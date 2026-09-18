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


## 📦 ARCHIVED 2026-08-26 from `03-PUNCH-LIST.md` (R3 budget)

> Moved VERBATIM, nothing deleted; one-line stubs remain. ‼ A FIRST attempt at this move
> CORRUPTED the file: it replaced slices in SIZE order, so the 2nd/3rd replacements used
> STALE indices and cut across wrong boundaries (5 diff hunks where 3 blocks were intended).
> Caught by reading the diff's hunk structure BEFORE committing; recovered by git checkout +
> re-apply. ⇒ CAPTURE ALL BLOCKS FROM THE PRISTINE LIST FIRST, REPLACE IN DESCENDING LINE
> ORDER, AND ASSERT EACH BOUNDARY STILL MATCHES BEFORE WRITING.

---

- [x] **✅✅ DONE 2026-08-23 — ALL 17 nav retry loops patched, and GATED as #30.**
      ⛔ **AN EARLIER DRAFT OF THIS ENTRY EXCLUDED 3 LOOPS AND WAS WRONG — the exclusion is
      WITHDRAWN.** It claimed `exit_building_after_whiteout()`, `_exit_training_cave_if_inside()` and
      `_enter_warp_by_navigation()` run "while the abort latch is still SET". **They do not.** An
      adversarial review refuted it and an AST resolution of `StoryMode.run`'s branch chain
      confirmed: BOTH the derail branch (`if not self._whiteout_pending`) and the whiteout branch
      call `set_story_abort(False)` BEFORE those routines. ‼ *The original error was reading a LINE
      RANGE instead of a control-flow path — there are two clear sites, one per branch, so "between
      them" proves nothing.* See `08-MISTAKES.md` and `06-DECISIONS-LOG.md` (both 2026-08-23).
      ⇒ **WHAT GATE #30 §1 ACTUALLY ENFORCES: `StoryMode.run` must clear the latch BEFORE calling
      any recovery routine.** The hazard is real but one REORDERING away, and that is what is now
      gated — with a fault test that injects the real hazard. ⛔ Do not hoist the recovery calls
      above the clear.
      ✅ **PROVEN, not asserted** — gate #30 drives the REAL `_navigate_through_scripts` two-armed:
      **ARM A (latch clear) `nav_attempts=25` + the FABRICATED `BotModeError: … too many scripted
      interruptions`; ARM B (latch set) `nav_attempts=0` + `StoryAbort` on iteration 1.** The arms
      differ on TWO axes. 5 fault tests pass, including *a check in a COMMENT does not satisfy it*
      and *a check INSIDE the try does not count* (it would be swallowed — `StoryAbort` subclasses
      `BotModeError`). ⚠ **THE ONLY RE-DERIVABLE FIGURE IS 28/28** — run `repro_loop_head_abort.py`. The 26/9/17
      breakdown quoted in the changelog is SUPERSEDED NARRATIVE (the old direct-match definition),
      kept for continuity and reprinted by nothing. Coverage **28/28** by the precise criterion — *a loop is exposed only if it can reach a nav
      primitive WITHOUT passing through a helper that already has a head check* (direct matching says
      26, naive transitive says 44; both are wrong). The fix is inert NOWHERE.
      ⚠ **drift is 3 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until the chapter is driven) — `modules/story/seafloor_cavern.py`, the §Ch20 chapter UNDER CONSTRUCTION, sandbox only. ⛔ NOT a promotion decision: it is incomplete (constants + predicates + preflight only, no legs yet) and must not be promoted until it is driven end to end.** *(the abort guards were promoted 2026-08-24 and that drift is 3 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven).)* custom went
      8 AST swallowers → 0 and probe 36 → 23; see `custom-pokebot/DIVERGENCE-LOG.md`.
      Original entry follows. `#24-loopheadabort` — **NEW 2026-08-17, found while triaging `#24-abortswallow`. A DIFFERENT
      DEFECT FROM THAT ITEM — do not conflate them.** 13 bounded retry loops in
      `sandbox-pokebot/modules/story/early_game.py` wrap navigation primitives and have **no
      loop-head `_check_abort()`**: `1259, 1305, 1518, 1567, 2404, 2420, 2433, 3112, 3135, 3241,
      3551, 3702, 3712` (line numbers as of 2026-08-17 — ⛔ RE-DERIVE, they drift).
      **Why it is not the same bug:** none of the guarded callees (`navigate_to`,
      `navigate_to_anywhere`, `_enter_warp_by_navigation`) contains `_check_abort()`, so no
      `StoryAbort` object ever arrives — a handler guard there is INERT. What happens instead is
      that after a whiteout the loop keeps re-navigating a DEAD TEAM from the respawn Pokémon
      Centre, burns its whole retry budget (`_navigate_through_scripts` up to `max_rounds=25`,
      `recover_devon_goods` up to 20) and then raises a FABRICATED cause — *"Could not reach X (too
      many scripted interruptions)"*. ⇒ **the fix is a `_check_abort()` at the LOOP HEAD**, outside
      the `try`, so the abort ends the loop instead of being retried through.
      ⛔ **CORRECTED 2026-08-22 (PASS 5) — "20 of the 44 already have a head check" WAS A BORROWED
      NUMBER AND RE-DERIVES UNDER NO DEFINITION.** The 44 came from the abort-SWALLOW probe's
      original count, which measures a different population. MEASURED by AST over `early_game.py`:
      **nav-primitive loops 26, of which 9 have a head check** (bounded loops 93/40; yield-from
      loops 79/46). ⇒ the pattern IS established — copy an existing one — but quote the 9-of-26.
      ⚠ **AND THE LIST OF 13 IS INCOMPLETE.** Five more nav loops have no head check and no
      reachable `_check_abort`: **376, 1930, 2607, 3310, 4257**.
      ‼ **WHAT THOSE NUMBERS POINT AT, precisely (checked 2026-08-23):** they are the `try:` lines,
      not the `for`/`while` heads — e.g. `:373` is `for above in ((7, 7), (6, 7)):` and `:376` is its
      `try:`; `:4254` is `for wx, wy in warps:` and `:4257` its `try:`. ⛔ **That is the RIGHT
      insertion point anyway** — immediately BEFORE the `try:` is inside the loop and outside the
      handler, which is exactly where the check must go. Do not "correct" them to the `for` line
      without re-reading: the point is to be inside the loop, outside the `try`. the site near `2603` is the item's exact shape —
      a `for _ in range(10)` loop head at `early_game.py:2603` whose body wraps `navigate_to_anywhere`
      in `except BotModeError: pass` (verified in code; ⚠ a cold-start audit corrected an earlier
      draft that said `range(20)` at `:2607` — `:2607` is the `try:`, not the loop head). Treat the 13 as a FIRST BATCH, not the population.
      ✅✅ **THE A/B IS NOT VACUOUS — the discriminator was COMPUTED 2026-08-22, so this is startable.**
      `grep -c _check_abort` is **0** in both `global_navigation.py` and `walking.py`, and
      `raise StoryAbort` occurs ONCE in `early_game.py:135` ⇒ **ARM A** (latch set, no head check):
      nothing inside the loop reads the latch, so it burns the full budget (8-25 rounds) and then
      raises a FABRICATED cause; **ARM B** (head check): raises on iteration 1. **The arms differ.**


---

- [x] **(5) ✅ DONE 2026-08-17 — and the item's own premise was REFUTED first. ⛔ DO NOT REBUILD IT.**
      **The premise was "never built".** `compare_runs.py` **exists** (12.3 KB, 2026-07-25) and its
      shipped CLI **already** accepts `--label <arm> <logs>` groups, so the requested "pairing"
      needed no new plumbing at all. ‼ **But running it is what mattered, not reading it.**
      ⛔⛔ **MEASURED REFUTATION — the pairing as specified would have LIED.** Fed the two committed
      withdraw-verdict arms (`evidence/2026-08-17-withdrawverdict-ARM{A,B}-*.harnesslog.txt`,
      which are `ACCEPTANCE: FAIL` and `ACCEPTANCE: PASS`), the shipped tool clustered them **2x on
      ALL FOUR axes, every one tagged `<<< SPANS LABELS`** — the strongest *"these runs are the
      same"* signal it can emit, over the exact pair that provably differs.
      **ROOT CAUSE, and it is structural, not a typo:** every axis was FAILURE-shaped, because the
      tool was built for cross-machine CRASH clustering where "did the arms differ?" never arises.
      A focused driver's log **always** ends `HANG CONFIRMED` (the harness's own end-of-run marker)
      and never reaches the `content-end`/`badge6` milestones that outrank it — so the failure axis
      is **CONSTANT ACROSS ARMS BY CONSTRUCTION**, and `ACCEPTANCE:` — the house verdict token,
      present in **53 of 65** committed evidence transcripts and only ever `PASS`/`FAIL` — was not
      parsed at all. ⇒ **Delivering the wrapper the note asked for would have produced a report
      reading "the arms agree" over a matrix whose entire purpose is to show they disagree.**
      ✅ **WHAT SHIPPED INSTEAD — an AXIS, not a wrapper** (`tools/story-dev/compare_runs.py`):
      `ACCEPTANCE:` is parsed (ALL verdicts, whole-file, so a multi-stage driver's Stage 1 is not
      dropped by the tail window), shown as a matrix column, added as a fifth cluster axis, and a
      new **`A/B DISCRIMINATION`** section states the arms-differ answer in words — **and NAMES the
      axes that are blind to it**, so a `<<< SPANS LABELS` cluster can never again be misread as
      agreement.
      ✅ **FAULT-TESTED FOUR WAYS** (`evidence/2026-08-17-compareruns-abaxis-FAULT-TESTS.stdout.txt`):
      (1) real A/B FAIL-vs-PASS → **SEPARATES**, and names `failure kind` / `dying function` /
      `location` as blind; (2) arms that genuinely agree (KI-80's arm-4 invariance, PASS/PASS) →
      **does NOT** claim separation; (3) neither transcript graded → **refuses to grade**;
      (4) one arm graded, one not → **refuses**. ‼ **Test (4) caught a REAL defect in the first
      draft of this very change**: `(no verdict)` beside `PASS` printed a green *"✅ THE ARMS
      SEPARATE"* — an **ABSENCE read as a value**, above the caveat a skimmer never reaches.
      Separation is now judged over **graded labels only**. ⇒ `08-MISTAKES.md` 2026-08-17.
      ✅ **DEMONSTRATED ON A REAL 4-TRANSCRIPT MATRIX** (the deliverable the item wanted): KI-80's
      promotion set, 2 builds x 2 expectations, where the new axis renders the three-point A/B's
      **mirror** structure at a glance — `PASS = {before-coupled, after-decoupled}`,
      `FAIL = {before-decoupled, after-coupled}` — while `location` and `failure+location` cluster
      all four together and see nothing.
      ⚠ **SCOPE — what this item did NOT cover.** The research note's line 166 names *two* unbuilt
      things; the punch-list item named only this one. **The "natural-vs-injected byte-equivalence
      control" is still unbuilt and still unspecified** — it is NOT closed by this entry. It is the
      one that would shut the *"is an injected mon really like a caught one"* gap.
      ⚠ **`tools/` is shared, not forked** — this change carries **no promotion twin** and does not
      move the sandbox↔custom drift figure.

---

- [x] **✅ DONE 2026-08-22/23 — brought current, and it was WORSE than filed: not a pure completeness gap, it carried FOUR WRONG CLAIMS** (a "Next:" for work done 2026-08-16, a warning that had been lifted, and "the next room" of a cavern driven end to end). ⛔ Kept number-free — the added section contains no digits. Original text follows.
      `#24-plainenglishstale` — **NEW 2026-08-17. `24-PLAIN-ENGLISH-STATUS.md` is the file
      `00-README` sends a HUMAN to FIRST, and it is two days behind (last updated 2026-08-15).**
      Missing: the `#24-orphans` (1) verdict instrumentation, the KI-66 `_on_field` fix, and both
      `#24-abortswallow` rounds. ‼ **It carries NO stale number** — a cold-start audit grepped it and
      it quotes no gate/drift/probe/budget figure — so this is a COMPLETENESS gap, not a wrong claim,
      which is why no gate catches it. ⇒ Bring it current in plain English; ⛔ keep it number-free,
      because that property is exactly why it has never gone stale in the way the other files do.
      *(Precedent: this file was FIVE chapters stale on 2026-08-13 and that is what motivated the
      whole DOC CONSISTENCY LAYER.)*



## 📦 ARCHIVED 2026-08-26 (2nd) from `04-HANDOFF.md` NEXT ACTIONS — R3 budget

> Guarded method: section-scoped, live-marker assertion, bottom-up, boundary re-asserted.

---

>    ✅ **(i) `#24-ch20rename` and (ii) the §Ch20 AREA ATLAS ARE BOTH DONE, and all nine rooms are
>    DRIVEN — do NOT re-measure or re-drive.** ‼ **Keep the two lessons:** §Ch20 is a
>    **STRENGTH-BOULDER dungeon, not a route** (Rooms 6/7 are open water needing SURF, not
>    Strength); and an atlas read REMOTELY is a **LOWER BOUND** — `is_tile_accessible` blocks every
>    tile whose object is not in `active_objects`, so a remote read's NO-PATHs are an ARTIFACT, not
>    a map fact (§Ch19 hit this too).
>    **(ii-continued) THE BUILD SPEC IS WRITTEN:**
>    📦 **The §Ch20 BUILD-SPEC DETAIL and the "older framing" retractions were ARCHIVED 2026-08-23
>    → `28-HANDOFF-ARCHIVE.md`** (83 lines, verbatim, R3 budget — the file was at 897/900).

---

>    ✅ **(a) (b) (a2) (a3) (a4) ARE ALL DONE, AND (c) IS OBSOLETE — every §Ch20 room is DRIVEN
>    AND PASSING. ⛔ DO NOT REBUILD ANY OF THEM.** `ch20room2/3/8/9` all reached
>    `ACCEPTANCE: PASS` (Room 3 ×2 with the DOUBLE-battle claim confirmed live; Room 8 ×2 incl. a
>    fault run proving jam recovery, `recovered=True attempts=2`; Room 9 ×2, the cavern END TO
>    END). (c) died because KI-77's despawn window is **20x17** and Room 8 is **11x14**, smaller
>    than it, so KI-77 cannot fire there — a repro is still worth having for the LARGE rooms but
>    blocks nothing. ⚠ Room 9 run 2 LOST the Archie fight (**2W/1L measured** — the party arrives
>    chipped and there is no heal in the cavern): that is CHAPTER-DESIGN input, not a driver
>    defect, and it is why the chapter needs a whiteout-retry policy.


## 📦 ARCHIVED 2026-08-26 (3rd) from `04-HANDOFF.md` NEXT ACTIONS — R3, session park

> Guarded method (section-scoped, live-marker assertion, bottom-up, boundary re-asserted).

---

>    ✅ **(i) `counter_hunt.py` and (ii) KI-79 `pc_trip.py` are BOTH CLOSED AND PROMOTED** —
>    evidence moved to `28-HANDOFF-ARCHIVE.md` (2026-08-15, line budget). ‼ **Keep only the rule:**
>    *a byte-compare is NOT proof for a BEHAVIOUR promotion — a three-point A/B is* (PASS before →
>    FAIL after faulted → PASS after unfaulted), and run 1 is unrepeatable once the copy happens,
>    so it runs and commits FIRST. Hook `POKEBOT_PCWITHDRAW_FAULT`; detail in KI-79 + `07`/`06`.
>
>    🆕 **(P4c) `#24-orphans` — SIX REAL RESIDUALS FILED 2026-08-15 — ⚠ MIXED STATUS NOW:


---
(from 04-HANDOFF NEXT ACTIONS, 2026-08-26 session park)

>    ✅✅ **PREVIOUS QUEUE ITEM 0 IS ANSWERED (2026-08-17): `#24-faintchooser-fourthspace` — the
>    observe-only probe was BUILT (in `--driver ki66faint`, ZERO production change) and DRIVEN.
>    **NO fourth index space is demonstrated**: on the one diverging faint, the last cursor the
>    sweep read before the menu closed (**3**) IS in `alive_slots_menu` (**[1,3,4,5]**). ⛔ DO NOT
>    "FIX" IT — real in the log, INERT in behaviour, same as the owner filter. Positive control on
>    the pre-fix build (`cursor_reads=66, A-presses=239`) is what makes that zero trustworthy.

---
(from 04-HANDOFF NEXT ACTIONS, 2026-08-26 session park)

>    ✅✅ **DONE 2026-08-16 — THE COUNTER-LADDER IS DECOUPLED FROM `grass_is_fodder`. ⛔ DO NOT
>    REBUILD IT.** `:1901` is now `if boss_teaches:` and `boss_mode = True` sits behind its own
>    `if grass_is_fodder:` — the one-line version would have shipped KI-23's mirror regression, and
>    arm 4 measured it doing exactly that. Blast radius (arithmetic measured, behaviour inferred):
>    **Brawly** gains the machinery across his band, **Roxanne** at `team_max` 13-16, **Wattson** at
>    20-22; Norman unchanged; the Rustboro rival unaffected (no `ace_types`).


---

## MOVED FROM `04-HANDOFF.md` 2026-08-27 — the §Ch20 rooms + pathfinder-scoping summaries

> ‼ **NOTHING WAS DELETED.** These two sections were already "keep only what later work
> leans on" summaries and every word is preserved below. They moved because §Ch20 SHIPPED as
> a chapter on 2026-08-24, so they are history, and `04-HANDOFF.md` had grown past its
> 900-line budget while leg 3's live findings needed room. `04` keeps a pointer plus the two
> rules later work still leans on.

## ✅ §Ch20 — ALL NINE ROOMS DRIVEN AND PASSING (2026-08-13/14) — DETAIL in `28-HANDOFF-ARCHIVE.md`

⛔ **DO NOT REBUILD ANY OF THEM.** ‼ **Keep only the rules later work leans on:** graded on
**`VAR_ROUTE128_STATE == 2`**, never the Kyogre flag (set BEFORE a forced warp); the atoll escape is
**south to `(38,23)` then Surf onto `(38,24)`** (the landing tile has ZERO surfable neighbours, so a
naive Surf reads as a HUNG LEG); the **Archie fight is the chain's one stochastic element (2W/1L)**
and a LOST run prints nothing, so the chapter needs a whiteout-retry policy; *assert the OUTCOME,
not the position you expected*; *the instrument was wrong, not the claim*; *copy upstream's ROUTE,
never its CONTROL FLOW*; **`FLAG_SYS_USE_STRENGTH` is cleared on EVERY WARP**; and press **A only
when a text printer is waiting, B otherwise** (A beside an NPC starts a conversation).
## PATHFINDER + §Ch20 SCOPING BACKGROUND — in `28-HANDOFF-ARCHIVE.md`

‼ **Keep only what later work leans on:** (1) **KI-59** (the pathfinder's inverted `Impassable *`
handling) is **FIXED, PROVEN and GATED** (`repro_impassable_dirs.py`) — its headline was wrong in
FOUR documents: it is **NOT** armed in the Seafloor Cavern (all 115 tiles are `collision=1`);
game-wide **401 of 2,658** such tiles are live, chiefly the Regi tombs (144), Shoal Cave (98) and
Victory Road (58). (2) §Ch20's spec corrected our own docs: **ROCK SMASH is mandatory**, the trigger
tile is **`(17,42)` not `(16,42)`**, and the chapter grades on **`VAR_ROUTE128_STATE == 2`**, never
the Kyogre flag (set BEFORE a forced warp). (3) **KI-74/75/76** were filed there; KI-76's safety
half is fixed and fault-tested, its **correctness half is OPEN**.
⇒ ✅ **ALL NINE ROOMS ARE DRIVEN — the cavern is END TO END (2026-08-14). ⛔ DO NOT REBUILD ANY.**


---

## MOVED FROM `04-HANDOFF.md` 2026-08-28 — the completed 2026-08-26 `#26-*` redirect

> ‼ NOTHING DELETED. Both batches were mined and all four work items shipped; this is history.
> It moved to make budget room for leg 3's runnable commands after a Tier 2 audit found the
> newest shipped probe was not startable from the handoff. The three RIPE USER DECISIONS that
> followed this block stayed in `04`, because they are still open.

>    ✅✅ *(RETIRED 2026-08-27 — the 2026-08-26 USER REDIRECT to the three `#26-*` production
>    defects is COMPLETE: all four work items shipped, and BOTH batches `20260826-130441` and
>    `20260826-185918` are MINED — ⛔ DO NOT RE-MINE EITHER.* Finish rate moved 12.0 → 25.8 →
>    37.5% in one day; the wedge fix VALIDATED (KI-47 family 2 → 0); the FIRST TREECKO FINISH;
>    the Treecko wall NAMED as the `#24-pc` run-ender. Numbers in `#26-manualderails`, narrative
>    in `07-CHANGELOG.md` (2026-08-26). The Winona SECOND WIND shipped the same day — ⚠ that is
>    DECISION-LAYER proof only; its end-to-end pass is still owed by a post-fix batch
>    (discriminator: no five-fold hopeless-gate repeats before Manual).

---

## §Ch21 — THE SUPERSEDED LEG-1/2/3 QUEUE TEXT (moved out of `04-HANDOFF.md` on 2026-09-01)

⛔ **MOVED, NOT DELETED, AND IT IS SUPERSEDED — DO NOT ACT ON IT.** Legs 1, 2a, 2b and 3 are all
BUILT AND DRIVEN. This block is the queue text that used to command building them; it is kept
because it carries the reasoning and the measured numbers behind the routes, and because this
project's rule is that hard-won detail is archived rather than removed. The LIVE instruction is
the last `➡➡➡` in `04-HANDOFF.md`'s NEXT ACTIONS (as of 2026-09-01: **build leg 4, the Sky
Pillar climb**).

>    ➡ *(then, and only then)* DESIGN LEG 3 PROPER. Order: (1) re-read the §Ch21
>    ATLAS Sky Pillar rows in `12-STORYMODE-DESIGN.md` — the climb **requires a DELIBERATE FALL**
>    through `4F (6,4)` or `(7,4)`, and `#24-crackedfloorpathfinder` says `calculate_path` to
>    `4F (3,1)` simply RAISES, so **the fall must be an EXPLICIT chapter step like `dive()`** —
>    ⛔ do NOT wait for the planner to grow the feature. (2) Sootopolis is a TRUE ISLAND: the only
>    way out is to DIVE at one of its 19 dive tiles and surf 126→131 — Fly is ruled out (both
>    VISITED flags False). ⛔ The dive out is a FIXED warp, not (x,y)-preserving. (3) The
>    leg-3 start tile is the MEASURED resting tile **(31,17)**, and its route to the dive tile
>    (29,53) is measured at **118 wp**.
>    ‼ **Carry the probe's one unbuilt RECOMMENDATION into the design:** plan the pocket crossing
>    ONCE at the resting tile and, on a waypoint timeout, walk back toward Steven (32,18) to
>    re-load him before re-planning. Neither `follow_waypoints` nor `navigate_to` recovers on its
>    own. ⛔ That recovery is UNBUILT AND UNPROVEN — it is a recommendation, not a result.
>    ✅✅ *(RETIRED 2026-08-27 — LEG 2 IS BUILT AND DRIVEN, both halves; ⛔ DO NOT REBUILD.)*
>    Leg 2a `--driver ch21escort` + leg 2b `--driver ch21cave`, both `ACCEPTANCE: PASS`, fixtures
>    `post_steven_escort.ss1` and `post_wallace.ss1` PINNED. The ~24 lines of build instructions
>    that stood here were commanding work that had already shipped. Detail lives in the
>    §Ch21 ATLAS (`12-STORYMODE-DESIGN.md`), `07-CHANGELOG.md` (2026-08-26/27) and the spec
>    `ai-research-notes/2026-08-26-ch21-leg2-BUILD-SPEC.md`. Two lessons kept, both also in
>    `08-MISTAKES.md`: ⛔ **a bot stands BESIDE an NPC, never ON one** — `calculate_path` to an
>    NPC's own tile ALWAYS refuses, and reading that as geography sent a session down a dead end;
>    and ⛔ **`get_map_objects()` is CAMERA-RANGE limited**, so "zero NPCs loaded" is never
>    evidence about the map.
>    ✅ **LEG 1 IS DRIVEN — `--driver ch21dive` DONE 2026-08-24, `ACCEPTANCE: PASS`. ⛔ DO NOT
>    REBUILD.** Its recipe (surf 128→127→126, dive tile `(45,66)`, the KI-72 tile_type assertion,
>    step off `(9,8)`/`(10,8)` before surfacing) lives in the §Ch21 ATLAS, which is its authority.
>    Fixture `post_ch20.ss1` is PINNED.

---

## §Ch21 LEG 3 — THE FOUR PRE-BUILD RESULT BLOCKS (moved out of `04-HANDOFF.md`, 2026-09-01)

⛔ **SPENT, NOT WRONG.** These are the measurements that leg 3 was built ON; leg 3 shipped
2026-09-01 and every number below now lives on a constant in `modules/story/sootopolis.py` with
its provenance attached. Kept for the reasoning. ‼ **One of them is still LIVE for leg 4:** the
Sky Pillar floors swap to `*_CLEAN` while `VAR_SKY_PILLAR_STATE < 2`, so our planner reads the
POST-GAME layouts on the climb.

>    ✅✅ **LEG 3 STEP 0 — THE POCKET EXIT — IS DONE 2026-08-27. ⛔ DO NOT RE-RUN IT.**
>    `probe_ch21_pocket_exit.py` + `--driver ch21pocket` (PASS, 4,009 frames, both arms
>    identical ⇒ that A/B is NOT discriminating). ⛔ §4.11's answer is the RESTING tile
>    **(31,17)**, not (31,16). Pocket 347 tiles; re-plan danger zone **89 of 121** wp; the
>    pocket RE-SEALS ⇒ ONE crossing per visit. §4.10: 2 encounters, both on 1F. §Ch21 ATLAS.
>    ✅✅ **THE SKY PILLAR LAYOUT QUESTION IS SETTLED 2026-08-27 (decomp) — ⛔ DO NOT RE-ASK IT.**
>    Six floors swap to `*_CLEAN` gated `call_if_lt VAR_SKY_PILLAR_STATE, 2` ⇒ the story climb runs
>    on CLEAN while our planner reads the post-game layout. ⛔ FIRST-CLIMB-ONLY; the Rayquaza
>    return trip is a different problem and the Mach Bike belongs to it, not here.
>    ✅✅ **THE ROUTE 131 PRE-BUILD GATE IS DONE 2026-08-28 — ⛔ DO NOT RE-RUN IT AS THE NEXT
>    ACTION.** `probe_ch21_route131_live.py` (offline, 2 controls, fault-tested) re-derived the
>    divergence from **our own ROM's `gMapLayouts`** and matched the decomp pass. SET B = layout
>    **#318**: **116** tiles open-in-A/WALL-in-B. ‼‼ **It overturned the atlas's own step-7 line:
>    the (40,20) start is NOT "35 wp and a detour" but a WALL COLLISION** (35 free vs 39
>    avoiding ⇒ every optimal path is FORCED through live rock). The real route from (40,19) is
>    16 either way = clean, and ✅ the swim's own 23 ROUTE131 waypoints are clean in BOTH sets
>    (audited 2026-08-28 after a Tier 2 audit found that leg unchecked). ⛔ `(28,15)->door` is
>    **no route in SET A, 17 in SET B** ⇒ **the final approach is HAND-WALKED.**
>

---

## QUEUE ITEM 0's ✅-DONE AUGUST HISTORY (moved out of `04-HANDOFF.md`, 2026-09-01)

⛔ **DONE, NOT PENDING.** Moved so that `04-HANDOFF.md` contains exactly ONE `➡➡➡` marker —
the LIVE next action. Previously there were two and the reading instruction had to warn that
*"the first is a ✅-DONE block"*, which is a hedge around a doc defect rather than a fix.

>    ASSEMBLY IS NO LONGER QUEUE ITEM 0 — IT IS PARKED, READY, AND WAITING.** The live queue is
>    the **PC / PARTY ROBUSTNESS ARC** below. This was triggered by a live user test: a Winona
>    counter-hunt caught Slugma, healed, **derailed to Manual**, and on continue re-fought Winona
>    without the counter. The user's words: *"I want to ensure that the bot can robustly,
>    intelligently and strategically use the pokemon pc"*, and *"we should shift focus onto this
>    first so future issues can be handled better."*
>
>    **THE LIVE QUEUE, IN ORDER:**
>    ✅ **(P1) the Slugma derail and (P2) KI-78 Stage 1 are BOTH DONE, A/B-PROVEN, GATED (#19,
>    #20) AND PROMOTED. ⛔ DO NOT REBUILD EITHER.** Detail ARCHIVED VERBATIM to
>    `28-HANDOFF-ARCHIVE.md` (2026-08-18, R3 budget). ‼ **The one caveat that must not be
>    lost: KI-78 is NOT fully closed** — debug-fabricated identical pairs, corrupt box slots,
>    Frontier rentals and the evolved-since-capture path all stay OPEN. See its entry.
>    ✅ **(P3) party-accounting STAGE 0 is BUILT, GATED (#22) and DRIVEN, and (P3b) IS ANSWERED —
>    a DIVERGENCE WAS OBSERVED (2026-08-15). ⛔ DO NOT RE-RUN EITHER.** Detail ARCHIVED VERBATIM
>    to `28-HANDOFF-ARCHIVE.md` (2026-08-18, R3 budget). ‼ **Two rules survive and still bite:**
>    STALE is SAMPLED 1-in-300, so ⛔ read the SCAN COUNT, never the bare zero; and
>    ⛔ index/menu-cursor call sites STAY on quantity B — if A > B an index from A is out of
>    range. Stage 1 (re-pointing the ~35 capacity-shaped call sites) is UNBLOCKED.
>    🔜 **(P4) The END-TO-END repro of the user's actual scenario — STILL OWED.** Nincada evolves
>    into a full party → counter hunt → heal. **The honest gap: P1 is proven by a fabricated
>    fixture, not by reality.** ✅ **Its OBSERVABILITY half shipped 2026-08-14** (gate #23): the
>    heal's three PC piggybacks swallowed everything, so *worked* / *nothing to do* / *threw* were
>    one silence — the user's run took the middle branch, said nothing. They report now.
>    ⛔ **That is NOT P4.** ‼ **DESIGNED IN FULL — read
>    `ai-research-notes/2026-08-15-p4-boxcounter-repro-design.md` BEFORE BUILDING**; it refuted
>    four of my own premises. ✅ **Steps 1-3 DONE:** `debug_write_box_slot()` (‼ **PROVEN LIVE**,
>    `--driver boxwrite` → PASS; the P4 driver must still open with its own read-back control),
>    the `POKEBOT_BOXCOUNTER_TYPEONLY_A` fault hook, and the gate exercising the REAL hook.
>    ✅✅ **(P4) STAGES 1 AND 2 ARE DRIVEN AND CLOSED — `--driver boxcounter` (both arms) and
>    `--driver boxcounter2` (matrix {ARM A, ARM B} × {sandbox, custom} = 4/4 `ACCEPTANCE: PASS`).
>    ⛔ DO NOT REBUILD EITHER. 📦 **The full evidence — the four controls, the `hunted_pids=None`
>    control that made the mechanism decisive, and ARM A reproducing the user's derail from
>    PRODUCTION rather than simulation — is ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md`
>    (moved 2026-08-24 on the R3 900-line budget; nothing deleted).**
>    ‼ The PID is published ONLY from `box_counter_pid`'s return; `boxwithdraw` HAND-SETS it,
>    which is exactly why that driver never caught this bug.
>    ⛔⛔ **ANCHOR IS `saves/fortree_gym_wedge.ss1` — the "use `ch13_fortree_door.ss1`" correction
>    is REVERSED BY A DRIVE.** `ch13_fortree_door` is on ROUTE120 and the run died on its first
>    leg: `Cannot reach FORTREE_CITY: it is not walkable from ROUTE120`. That is **KI-24**,
>    documented in our own `region_reach.py:7-11` — Routes 118/119/120 are dual-elevation-bridge
>    maps `calculate_path` reads as WALLS. Every Winona-era anchor we own is on ROUTE119/120
>    EXCEPT the wedge. The feared gym-exit leg cost nothing.
>    ⚠ **What the swap gives up:** the wedge has NO Shedinja/Ninjask twins, so Stage 2 no longer
>    runs over a live KI-78 collision; `ch13_fortree_door.ss1` (which DOES hold a real pair
>    sharing `pid=42207D6F`) stays the anchor for any test whose SUBJECT is that collision.
>    ⛔ **`needed` IS `{Rock, Ice, Dragon}` — NOT `{...Electric}`.** Corrected by the driver's new
>    `needed_ok` control on its FIRST run: production derives `needed` from the ACE alone, the ace
>    is Altaria (Dragon/Flying), and Electric is 0.5× into Dragon × 2.0× into Flying = **1.0,
>    NEUTRAL**. Four copies (`counter_hunt.py:250`, the design note, THIS file, the driver) were
>    corrected — ⛔ **and a FIFTH was found 2026-08-15**, prose on `CREDIBLE_ANSWER_POWER`
>    (`story_mode.py:1087`) that named no type list, so the grep for the type set walked past it.
>    ‼ **STILL NOT PROVEN BY STAGE 2 — the honest gap:** everything UPSTREAM of registration. The
>    Slugma is INJECTED and the PID is published by the driver, so the real `hunt()` →
>    `story_mode.py:1750` wiring remains untested end-to-end. ⚠ And `hunt()` snapshots its OWN
>    `before_box_pids` AFTER travel, so an injected fixture is excluded a second time — that leg
>    needs a REAL CATCH, not an injection.
>    ✅✅ **(P4b) IS CLOSED — BOTH of its things are DONE (2026-08-15, user-approved).**
>    ✅✅ **KI-80's REPRO DRIVER IS BUILT, DRIVEN AND FAULT-TESTED (2026-08-15). ⛔ DO NOT REBUILD.**
>    `story_harness.py --driver ki80ladder`, anchor `saves/batch2_run04_wedge.ss1`. **THREE arms on
>    one fixture — same party, same 8 seeded losses, same boss; only the cfg's `grass` key differs:**
>    `NOGRASS` → ladder · `GRASS_FODDER` (Route 102, `wild_max` 4) → ladder ·
>    ⛔ `GRASS_STRONG` (Route 119, `wild_max` 27 — **the patch her own cfg comment names**,
>    `story_mode.py:3532`; ⛔ she has NO `grass` key today, and that is the only reason her ladder works) → **plain escalation,
>    ladder SKIPPED**. `ACCEPTANCE: PASS` on `--build sandbox` AND `--build custom`.
>    ‼ **The driver EXITS 0 even on FAIL — grade the `ACCEPTANCE:` line, never the exit code.**
>    Fault-tested twice: against `ch13_fortree_door.ss1` it FAILS with *"THE A/B WOULD BE VACUOUS"*
>    and all three arms return `LADDER` — a live demonstration that the fixture this file once
>    prescribed would have read as a REFUTATION of a true finding; and `POKEBOT_KI80_DECOUPLED=1`
>    FAILS today, which is what makes it usable as the AFTER run.
>
>    ✅ **✅✅ DONE 2026-08-16 — THE COUNTER-LADDER IS DECOUPLED FROM …** 📦 `28-HANDOFF-ARCHIVE.md` (2026-08-26, R3).
>    ✅✅ **AND IT IS PROMOTED TO BOTH FORKS (2026-08-16, user-approved)** by a THREE-POINT A/B
>    against `--build custom`: `POKEBOT_KI80_DECOUPLED=1` **FAIL → PASS**, the coupled expectation
>    **PASS → FAIL**, and **arm 4 PASS on BOTH sides** — that invariance is what shows the mirror
>    regression did not travel with the fix. ⛔ **THE KI-80 ARC IS CLOSED; DO NOT REOPEN.**
>
>    ✅ **✅✅ PREVIOUS QUEUE ITEM 0 IS ANSWERED (2026-08-17): `#24-fa…** 📦 `28-HANDOFF-ARCHIVE.md` (2026-08-26, R3).
>    ⚠ Limits recorded in the item: refusal count APPROXIMATE, n=1 diverging faint.
>
>    ✅✅ **`#24-driftassertions` IS DONE (2026-08-17) — the drift sweep IS A GATE** (`check_drift`;
>    reduction half `#24-driftreduction` open). ‼ Earned its keep again 2026-08-24: `sootopolis.py`
>    moved the count and it found SEVEN stale claims — a Tier 1 review then found an EIGHTH, in this
>    file's STATE-table HEADLINE, a shape `check_drift` missed (`#24-driftheadlineshape` —
>    ✅ CLOSED 2026-08-26: PASS 3 reads the row's FIRST `N as of <date>`, D28a-e + a live
>    incident replay prove it both ways).
>    📦 Detail ARCHIVED in `28-HANDOFF-ARCHIVE.md` (2026-08-24, R3 budget).
>    ✅✅ **`(P4c) #24-orphans` (1) IS HALF DONE (2026-08-17): its INSTRUMENTATION half is BUILT,
>    GATED (#26) and A/B-PROVEN (`withdraw_from_box` returns `(landed, code, detail)`; ARM B
>    `landed=True` vs ARM A `landed=False`). ⛔ DO NOT REBUILD IT. Its REACTION half stays OPEN
>    and still needs the USER plus an unmeasured heap offset. 📦 Detail ARCHIVED VERBATIM in
>    `28-HANDOFF-ARCHIVE.md` (2026-08-24, R3 headroom).
>    ✅✅ **`#24-abortswallow` (2026-08-17): 8 MORE SITES FIXED** — part of the arc that ended in
>    gate #27 (ratchet, baseline 36). ⛔ DO NOT REDO IT. 📦 Detail ARCHIVED VERBATIM in
>    `28-HANDOFF-ARCHIVE.md` (2026-08-26, R3 budget).
>    ✅✅ **`#24-abortswallow` ROUND 3 IS DONE (2026-08-17)** — refinement (1) shipped (37→36),
>    refinement (2) REFUTED (it would blind the gate to five already-fixed sites, one an OBSERVED
>    failure). ⛔ DO NOT REBUILD IT. 📦 Detail ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md`.
>    ✅✅ **AND THE PROBE IS NOW GATE #27 — A RATCHET, baseline 36, fault-tested both ways** (inject one
>    unguarded site → 37 → exit 1). That closed this item's gating question without a zero-threshold.
>
>    ➡➡➡ **QUEUE ITEM 0 — ✅✅✅ ALL FIVE PASSES ARE DONE AND COMMITTED (2026-08-22).
>    ⛔ DO NOT RE-RUN ANY OF THEM. ✅✅ `#24-loopheadabort` IS ALSO DONE (2026-08-23) — **all 17**
>    nav retry loops patched, gate #30. ⛔ An earlier draft excluded 3 on a FALSE premise ("the
>    latch is still set"); an adversarial review refuted it and the exclusion is WITHDRAWN. #30 §1
>    now gates the real invariant: the latch is cleared BEFORE every recovery routine.
>    ✅✅ `#24-p4residuals` is 6 of 7 DONE (2026-08-23); only (f) remains (a real emulator drive).
>    ✅✅ `#24-abortrecoveryresiduals` **(b) is DONE** (2026-08-23) — my own abort-swallowing debt
>    cleared, 11 → 7, control-armed. **(a)** still needs a driven double-whiteout; **(c)** (7
>    PRE-EXISTING swallowers, newly filed) wants its own control arm.
>    ✅✅ *(RETIRED 2026-08-28 — the 2026-08-26 `#26-*` redirect is COMPLETE; detail in
>    `28-HANDOFF-ARCHIVE.md`, narrative in `07-CHANGELOG.md` 2026-08-26.)*

---

## CLOSED PUNCH-LIST ITEMS, ARCHIVED VERBATIM (moved out of `03-PUNCH-LIST.md`, 2026-09-01)

⛔ **ALL FOUR ARE `[x]` DONE — this is history, not work.** Moved because `03-PUNCH-LIST.md`
is a CURRENT-STATE file with a 3,600-line budget and `lint_docs.py`'s own I1 advisory has
been saying that 101 completed items were sitting in it. These are the four oldest
(2026-08-05/06). ‼ Their RULINGS are still binding — `#24-partycap` in particular says DO
NOT RAISE THE CAP AGAIN, and `#24-hmslots` ratifies reserving HM slots.

- [x] `#24-partycap` — **MEASURED AND REVERTED 2026-08-05. DO NOT RAISE THE CAP AGAIN.**
      Batch `20260805-122057` (`be104e9c`, VERDICT OK, 0 violations): **52.0% → 15.8%**.
      The badge funnel put the ENTIRE loss on one rung — **Balance→Feather 76% → 21% (z=3.06)**
      — with every earlier rung flat, so **a deeper team is FREE through five badges**.
      Cause is **HM coverage, not strength**: 10 of 16 non-finishes are `No party mon can learn
      Surf and the party is full` (**0 occurrences in all 14 prior batches**). The empty slots
      are the RUNWAY that HM/counter catches land on — at cap 4 the team still reaches a mean
      **5.85** by Feather. Both constants back to 4, each with a do-not-raise comment.
      Full detail: `07-CHANGELOG.md` + `08-MISTAKES.md` 2026-08-05.

- [x] `#24-hmslots` — **RULED 2026-08-05: RESERVE SLOTS. No code change; this ratifies current
      behaviour.** The party fills to 4 with early wilds and grows organically to a measured mean
      **5.85 by Feather** as HM learners and counters board. Logged as a ruling so nobody reads it
      as unfinished and re-raises the cap — that mistake cost 36 points once already.
      Rejected: cap 5 (unmeasured, cosmetic, costs a batch), deposit-to-make-room (the real fix,
      but it is `POKEBOT_PC_ROTATION`'s shape — disabled for costing ~19 points).
      Full rationale: `06-DECISIONS-LOG.md` 2026-08-05.

- [x] `#24-mtpyre-batch` — **DONE 2026-08-06. Segment 14 holds in production.**
      `20260806-055947` (`498eedd9`, VERDICT OK): MT. PYRE 274 / ROUTE 121 171 / ROUTE 122 89 in
      the debug logs; **9 finishes vs 10 runs reaching Feather (~90% conversion)**; 0
      BotModeError from either guard. Finish rate 52.0% → 37.5% is the new completion
      requirement, not damage — **no funnel rung moved significantly** (Balance→Feather z=1.49,
      whole funnel z=0.88). Whiteout uptick measured NOT attributable to Mt. Pyre.

- [x] `#24-mtpyre-log` — **DONE 2026-08-06.** Segment 14's five milestones now `console.print`
      (`_ch14_say`), so a mid-way failure leaves a trail in batch stdout. Frame count identical.

### `#24-r121topology` — closed item archived 2026-09-01 (03-PUNCH-LIST.md line budget)

- [x] `#24-r121topology` — **ANSWERED 2026-08-05: it is a STORY GATE, not topology.** See
      `#24-r121gate`. Superseded text below kept for the reasoning trail.

### `#24-pcwithdraw-proof` — closed item archived 2026-09-01 (line budget)

- [x] `#24-pcwithdraw-proof` — **PROVEN 2026-08-07. FULL ENTRY MOVED to
      `28-HANDOFF-ARCHIVE.md` (2026-08-17)** on the R3 3,600-line budget. Closed, and its
      successor work (KI-79's identity-verified withdraw, and `#24-orphans` (1)) is tracked
      separately. Nothing deleted.

### `#24-relocfloor` — closed item archived 2026-09-01 (line budget)

- [x] `#24-relocfloor` — ✅ **DONE 2026-08-01, CLOSED. Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-08-17** (the R3 relief valve: this file hit its 3,600-line limit). ⛔ Nothing here is outstanding; read the archive for the measured relocation-floor table and the "ONLY the floor is wrong — do not key it all to the trainee" rule, which later training work still leans on.

### ‼ BATCH 4 LANDED 2026-07-31 23:15 — the counter chain's blocker MOVED to KI-44

### `#24-mtpyre` — closed item archived 2026-09-01 (line budget)

- [x] `#24-mtpyre` — **BUILT AND LIVE-PROVEN 2026-08-06.** `open_route121_aqua_gate()` +
      `do_mt_pyre_summit()`, Segment 14. From `post_winona.ss1` in 76,368 frames: Magma Emblem
      obtained, `HIDE_JAGGED_PASS_MAGMA_GUARD` True (Magma Hideout open). End save:
      `saves/post_mtpyre.ss1`. 8 repros green. ‼ NOT batched — see `#24-mtpyre-batch`.

### `#24-pcoverflow` — closed item archived 2026-09-01 (line budget)

- [x] `#24-pcoverflow` — **BUILT 2026-08-05** (user ruling: build the real thing, not a raised
      constant). `resource_blocker` no longer refuses a full party (ball gate untouched);
      `pc_trip.box_views/find_in_box/withdraw_from_box` read the PC, find a mon **by PID**, and
      collect it at the next heal. Frees exactly ONE slot, never deposits its own target.
      `repro_pc_overflow.py`. **NOT live-proven.**

### `#24-progressiongate` — closed item archived 2026-09-01 (line budget)

- [x] `#24-progressiongate` — **SHIPPED 2026-08-08.** `AREA_PREREQ[FIERY_PATH] = "rocksmash"`,
      resolved by `_party_can_rock_smash()` (move AND `BADGE03_GET`, fails closed).
      **DECOMP-VERIFIED**: `src/party_menu.c:122` — `FIELD_MOVE_ROCK_SMASH, // FLAG_BADGE03_GET`.
      A/B: pre-Wattson **0 huntable** (was the circular Numel @ FIERY_PATH); post-Wattson 1.
      Norman control preserved. Suite 8/8.

### `#24-winonaground` — closed item archived 2026-09-01 (line budget)

- [x] `#24-winonaground` — **SOLVED 2026-08-07 by `#24-movepoolcounters`. The real cause was
      neither the whitelist nor reachability: across all 11 huntable grounds Winona's needed
      types appear ONCE (Geodude @ ROUTE111) and it is a **Rock Smash** encounter, which the
      `method == "Grass"` filter drops — leaving zero candidates.** She now has Slugma @
      FIERY_PATH via Rock Throw. ‼ My first two stated causes were both wrong; the history is
      kept below because the wrong turns are the lesson.

### `#24-pcoverflow-proof` — closed item archived 2026-09-01 (line budget)

- [x] `#24-pcoverflow-proof` — **CLOSED 2026-08-07. Both halves are now live-proven, each by its
      own capability test.** Catch half: `--driver boxcatch` (see `#24-pcoverflow` below).
      Withdraw half: `--driver boxwithdraw` (see `#24-pcwithdraw-proof` below).
      The original blocker stands as a lesson: batch `20260805-122057` logged `withdrawing` **0**
      times because the Surf guard derailed runs before any full-party catch reached the overflow
      path. Bundling the feature with the cap measured the BUNDLE, not the part — and a targeted
      probe answered in **~45,000 frames** what four 3-hour batches could not.

### `#24-postwinona-save` — closed item archived 2026-09-01 (line budget)

- [x] `#24-postwinona-save` — **THE PRACTICAL BLOCKER FOR ALL Ch14 WORK. Do this first.**
      No save exists past Winona, so nothing in Mt. Pyre can be validated. A 2026-08-05 attempt
      drove Story from `fortree_gym_wedge.ss1` and ground through 10 Winona attempts (KO'ing
      3-4 of her 5 each) without converging — that save's team has no super-effective answer to
      Flying. Options: drive a fresh run to completion and keep the end state; or build the save
      from a run that already beat her (52% of batch runs do). Once it exists, commit it to
      `tools/story-dev/saves/` as `post_winona.ss1` — every Ch14 probe will want it.

---

## §Ch20 'ASSEMBLE AS A CHAPTER' — the superseded build spec (moved out of `04-HANDOFF.md`, 2026-09-01)

⛔ **DO NOT DO THIS. §Ch20 SHIPPED AS A CHAPTER ON 2026-08-24.** This spec sat inside the LIVE
queue as an executable instruction for eight days after the work shipped; two Tier 2 cold-start
audits were needed to find it (the first retired two sibling clauses and missed this one, which
was the worst of the four because it was a full build order, not a passing mention).

>    wired as Segment 20 in `story_mode.py`, built from the driven ingredients (`_ingress`, the
>    room solves, the walk route, the var-gated scene ride, the atoll escape). Requirements,
>    all measured: **organic Dive acquisition** (drivers inject it; KI-63's
>    `ensure_hm_learner_making_room` is wired in sandbox), **whiteout-retry policy for Archie**
>    (one retry = full re-dive of Rooms 1-8, ~25 min; Mossdeep Gym's N-attempts precedent),
>    **pre-boss readiness** (potions/party order — run 3 entered with a fainted mon and
>    Sceptile at 96/135), **Blocker 3** (Repel policy — Rooms 6/7 have `water_mons`; Rock Smash
>    prompts YES/NO every smash), **Blocker 4** (pre-flight badge/move assertion incl.
>    Dive/BADGE07), and grade the SEGMENT on **`VAR_ROUTE128_STATE == 2` + the escape +
>    can-continue** (the ladder chapter in `chapters.py:233` grades on
>    `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`, which is set PRE-warp — too weak for the segment).

---

## Queue items 1b / 2 / 3 - DONE, moved out of `04-HANDOFF.md` 2026-09-01

### queue item 3 - DONE, archived 2026-09-01 (line budget)

> 3. ✅ **DONE — DO NOT RE-DO.** KI-68's dive leg is driven (`--driver ch20dive` →
>    `ACCEPTANCE: PASS legs=6/6`) and all nine cavern rooms with it. ‼ **Keep the RULE, not the
>    task:** `WaypointAction.Dive`/`Emerge` are assigned NOWHERE and `warp_graph.py:342` excludes
>    dives from `calculate_path` **on purpose** — so *"not routable" never meant "not possible"*;
>    the answer is a CHAPTER that drives the transition, never a planner rewrite.
>    ‼ **LIVE, not stale:** if a hunting ground is ever added, **NOT to `TRAINING_GRASS`** —
>    measured, a Shoal Cave row becomes the highest band and flips `best_training_area` for every
>    team ~L30 up. ⇒ see **KI-80**, the same table's second sharp edge.
>
### queue item 2 - DONE, archived 2026-09-01 (line budget)

> 2. ✅ **DONE 2026-08-13 — `reorder_party()` IS DRIVEN.** `--driver roster` passes: six swaps, all
>    verified by PID, including the never-driven `RotatePokemon(i, j != 0)`. Both unknowns this
>    item asked about are SETTLED; the trace detail moved to `28-HANDOFF-ARCHIVE.md` 2026-08-14 on
>    the line budget. ⚠ **Keep one thing from it:** `gPartyMenu.slot_id` is NOT reset between menu
>    sessions and `navigate_to_mon:520-524` reads it — it happened to be re-read live in time, so
>    that is LUCK, not safety. Re-check it first if a roster drive ever mis-swaps.
>    ‼ **What is NOT done:** the **deposit/withdraw** half of `#24-roster`. Ordering answers "in
>    what order", not "which Pokémon". And **promotion of `roster.py` + `menuing.py` to
>    `custom-pokebot/` — ✅ **DONE, promoted 2026-08-13/14; both files are in BOTH forks.**
>    ‼ That is a statement about THESE TWO FILES, not about the repo's drift figure today —
>    PARTY ACCOUNTING STAGE 0 has since moved it. See the STATE line at the top of this file.**
>
### queue item 1b - DONE, archived 2026-09-01 (line budget)

> 1b. ✅ **DONE — the KI-63 wiring was PROMOTED on 2026-08-14 and is in BOTH forks. There is no
>    decision left here** (‼ not a claim about today's drift figure — see item 1). Its superseded
>    "first decision for the user" text, and the measured worth behind it (20 terminal run-kills in
>    1,129 runs, #1 of 14 derail causes by frames), moved to `28-HANDOFF-ARCHIVE.md` 2026-08-14.
>

### queue item 2c - reference pointer, moved out of `04-HANDOFF.md` 2026-09-01

> 2c. **‼ READ `ai-research-notes/2026-08-13-puzzle-solver-already-ships-ch21-and-the-regi-arc.md`
>    BEFORE ITEMS 3 AND 4 BELOW.** Both were written believing §Ch21 and the Regi arc had to be
>    built as chapters. **Most of that content already exists in upstream code we already have.**
>    Items 3 and 4 are still correct about the DIVE LEG — which is the real gap — but wrong about
>    the scale of what remains. **KI-72** also lands here: never let the planner choose a surfacing
>    tile.
>

### queue item 0's August work - DONE, moved out of `04-HANDOFF.md` 2026-09-01

>    ✅✅✅ **QUEUE ITEM 0'S AUGUST WORK IS ALL DONE AND COMMITTED — ⛔ DO NOT RE-RUN ANY OF IT.**
>    The five-pass deep sanity check, `#24-loopheadabort` (all 17 nav retry loops, gate #30),
>    `#24-p4residuals` (6 of 7; only (f) remains, a real emulator drive), and
>    `#24-abortrecoveryresiduals` (b) are DONE. Detail in `28-HANDOFF-ARCHIVE.md`.
>    ‼ **Still open there:** `#24-abortrecoveryresiduals` **(a)** (needs a driven double-whiteout)
>    and **(c)** (7 pre-existing swallowers, wants its own control arm).
>    ⛔ **THREE USER DECISIONS REMAIN RIPE** (not mine, and still open): the drift promotion
>    (double-batch validated); the post-wind repeat burn (`#26-manualderails` D4); mixin
>    adoption (`#24-harnesswhiteoutdrop`).

### the leg-3 completion block — compressed out of `04-HANDOFF.md` 2026-09-01

>    ✅✅✅ **LEG 3 IS BUILT AND DRIVEN (2026-09-01) — ⛔ DO NOT REBUILD IT.** `--driver ch21approach`
>    from `post_wallace.ss1` → `ACCEPTANCE: PASS`, **all 14 readings, `missing=[]`**, `frames=34122`,
>    `encounters=9`, `whiteouts=0`, `pocket_attempts=1`, `method_ok=True`, `premise_ok=True`.
>    Fixture **`post_skypillar_door.ss1` PINNED** (probe-verified: SKY_PILLAR_ENTRANCE (6,16),
>    badges 1-7; ⚠ party at **91% HP**, not full — there is no Poke Center after Sootopolis).
>    **THREE** fault arms ran: `POCKETSTALL` → `pocket_attempts=2` and still PASS (the pocket
>    recovery was the leg's one designed-but-unproven part and is now a RESULT); `BLINDWALL` → fails
>    LOUDLY naming the step, bounded, **no hang**; and `POCKETWALKBACK` (added after an ADVERSARIAL
>    REVIEW found a BLOCKER) → the recovery's OWN walk-back stalling now raises a NAMED "stranded"
>    error instead of a raw exception that escaped the retry budget.
>

### the §Ch20 completion block — compressed out of `04-HANDOFF.md` 2026-09-01

>    ✅✅✅ **§Ch20 SHIPPED AS A CHAPTER 2026-08-24 — 5/5 drives PASS, both recovery paths
>    exercised. ⛔ DO NOT REBUILD IT.** ⚠ NOT proven: organic Dive in the same run (the driver
>    injects it) and a LOST Archie fight (stochastic, 2W/1L; all five runs won).
>    ⛔ Read `#24-divegroundroute120`, `#24-hmgroundwatertiles` and `#24-gatescopeharness`
>    first — all three are measured and none is started.
>    ⛔ **`#24-abortrecoveryresiduals` IS DONE — DO NOT RE-OPEN (a)/(b)/(c).** (a) closed by
>    ASSESSMENT (reachability VERY LOW, evidence in `07-CHANGELOG.md`); no code change to the
>    whiteout-recovery path, deliberately.

---

## §Ch21 LEG 4 — THE BUILD-ORDER BLOCK (spent; moved out of `04-HANDOFF.md` 2026-09-01)

⛔ **SPENT — leg 4 is BUILT AND DRIVEN.** This was the queue's leg-4 build order and its
hazard list. Every hazard it names was handled and is proven in `07-CHANGELOG.md` 2026-09-01.
Kept for the reasoning (the one-shots, the fall tiles, the layout-pin rule, the scope ruling).

>    ➡➡➡ **NEXT ACTION: BUILD LEG 4 = THE SKY PILLAR CLIMB.** It starts by RIDING the Wallace
>    cutscene: `SKY_PILLAR_ENTRANCE (14,4)` warps to `SKY_PILLAR_OUTSIDE`, whose ON_FRAME scene
>    fires at `SOOTOPOLIS_CITY_STATE == 3` with NO coordinate condition, drives the player ~12
>    tiles under `lockall` and sets the var to 4. ⛔ That is a TRUE ONE-SHOT — leg 3 deliberately
>    stops one tile short of it and asserts both story vars are UNCHANGED (3 and 0).
>    ⛔ **READ THE §Ch21 ATLAS FIRST** (`12-STORYMODE-DESIGN.md`): the climb REQUIRES a deliberate
>    fall through `4F (6,4)`/`(7,4)`, which `calculate_path` cannot propose, so the fall must be an
>    explicit chapter step. The bot is BIKELESS (`RECEIVED_BIKE` False, measured) — ⛔ never
>    `mount_bike` (`puzzle_solver.py:39-42` is an infinite hang for a bikeless bot).
>    ‼ **AND THE ONE THING LEG 4 MUST INHERIT FROM LEG 3, OR IT WILL REPEAT ITS FIRST FAILURE:**
>    the Sky Pillar floors SWAP LAYOUTS below `SKY_PILLAR_STATE` 2. Our planner reads the
>    POST-GAME layouts. ⇒ **verify every planned route against `sootopolis._live_wall_tiles()`
>    (the `gBackupMapLayout` grid the GAME walks on) before following it, and pin the planner with
>    `_pin_planner_to_live_layout()` where it disagrees.** Leg 3's first drive jammed in Sootopolis
>    for exactly this reason and the A/B is in `evidence/2026-09-01-ch21-leg3-LAYOUTPIN-ab.txt`.
>    ⛔⛔ **THE SIX THINGS THAT DECIDE WHETHER **LEG 4** SURVIVES ITS FIRST DRIVE.**
>    ‼ *(REWRITTEN 2026-09-01. Until then this block was **LEG 3's** hazard list: the `➡➡➡`
>    heading above it had been retargeted to leg 4 and the FIVE bullets under it were NOT. FOUR of
>    the five described work this same file marks DONE — the cave return, the pocket, the
>    hand-walked tail and the ROUTE131 layout reading. A Tier 2 cold-start audit caught it and
>    called it the file's most expensive defect, because it is what a cold agent ACTS from.
>    ⇒ P2 is not only about `##` headings: **a `➡➡➡` marker is a claim about every bullet
>    beneath it**, and retargeting the heading without rewriting the body is the same failure.)*
>    (1) ⛔⛔ **WALK TO `(14,3)` — **NEVER** `navigate_to((14,4))`.** *(REWRITTEN 2026-09-01: this
>        bullet used to say "must reach `(14,4)`", which is the tile LEG 3'S OWN SHIPPED CODE marks
>        `⛔ NEVER (14,4)` — `sootopolis.py:737`. A third Tier 2 round caught it.)*
>        `(14,4)` is a **South Arrow Warp to SKY_PILLAR_OUTSIDE**, so `calculate_path` to it returns
>        `is_warp=True` ending on OUTSIDE `(17,13)` — i.e. **`navigate_to` would cross the map seam
>        INSIDE the navigate and run the one-shot Wallace `lockall` cutscene**, which is the exact
>        opposite of the `➡➡➡` line's own instruction to RIDE it. MEASURED: the same call to
>        `(14,3)` returns 21 wp `is_warp=False` (`evidence/2026-09-01-ch21approach-CLEAN.txt`).
>        ⇒ **navigate to `(14,3)`, THEN press Down deliberately** to fire the warp, THEN ride the
>        scene on the far side. ‼ An arrow warp does **not** fire merely by stepping onto the tile —
>        the direction must be HELD (`evidence/2026-08-27-ch21-skypillar-probe.stdout.txt`).
>        ⛔ **AND THE 'NEVER PRESS DOWN' RULE IS SCOPED TO `(6,16)`, NOT TO THE WHOLE LEG** — an
>        earlier draft banned it outright, which would have banned the one input leg 4 must make.
>        `(6,16)` is a SOUTH arrow warp back to ROUTE131 where the Sootopolis pocket has ALREADY
>        RE-SEALED; while standing there, never press or hold 'Down' and ⛔ **never use a helper
>        that JOLTS the d-pad** — `walking.py`'s starve-jolt tries `"Down"` FIRST.
>        `wait_until_truly_controllable()` presses nothing and is safe.
>    (2) **RIDE THE WALLACE CUTSCENE** at `SKY_PILLAR_OUTSIDE` (fires on MAP LOAD at
>        `SOOTOPOLIS_CITY_STATE == 3`, no coordinate condition, moves the player ~12 tiles under
>        `lockall`, then sets the var to **4**). ⛔ It is a TRUE ONE-SHOT — leg 3 deliberately
>        stops one tile short of it and asserts both story vars are UNCHANGED (3 and 0).
>    (3) ⛔ **THE FALL IS AN EXPLICIT STEP, AND `(9,4)` IS A DECOY.** `calculate_path` cannot
>        propose a deliberate fall (it does not model `"Cracked Floor"` at all), so the chapter
>        adversarial recon pass caught the stale clauses. What (9,4) WOULD do if fallen through —
>        land in 3F's 118-tile MAIN region, not the pocket — still powers discriminator (6).)*
>    (4) ⛔ **THE DESCENT NEEDS A **SECOND** FALL, AND ITS FAILURE MODE IS A LIVELOCK, NOT A
>        REFUSAL.** Omit it and the bot summits, wakes Rayquaza and is STRANDED. ‼ The atlas says
>        the west pocket has "no walking exit"; that is **REFUTED** — it contains `4F (7,1)`, a
>        planner-VISIBLE staircase, so the planner will happily route into a livelock. ⇒ the
>        DESCENT post-fall check must be a `calculate_path` to **3F (3,1)** — ⛔ not to be confused
>        with the ASCENT-FALL DISCRIMINATOR in (6), which targets 3F `(7,1)`; they answer
>        different questions — and it is the target the wrong exit cannot
>        satisfy. ⛔ A "the planner refuses" check would never fire.
>    ‼ **AND READ `#24-crackedfloorpathfinder` IN `03-PUNCH-LIST.md` BEFORE THE CLIMB — but read
>    its 2026-09-01 UPDATE FIRST.** That item still contains the REFUTED "no crack-free route"
>    claim and a "⛔ DO NOT READ THAT AS A GREEN LIGHT TO BUILD THE CLIMB" line, both of which
>    are SUPERSEDED (they blocked the post-game crack set, not the CLEAN one the story runs on).
>    A Tier 2 audit found this handoff never NAMED that slug, so the correction was unfindable
>    from where a cold reader starts. What survives from it is bullet (5) below.
>    (5) ⛔ **`SKY_PILLAR_TOP` IS THE ONE MAP WHERE THE DIVERGENCE INVERTS, AND IT IS
>        UN-VALIDATED.** 31 tiles the static planner calls OPEN are WALLS on CLEAN — and
>        `probe_skypillar_clean_layout.py` fetches only `2F/3F/4F_Clean`, so **it cannot check
>        TOP, 1F or 5F at all**. The atlas's "TOP 13 wp" was computed blocking CLEAN *cracks*
>        only, never CLEAN *walls* — ⛔ do not quote it as a validated summit route. Extend that
>        probe (or use `probe_live_mapgrid.py` while STANDING on each floor) before driving TOP.
>    (6) ⛔⛔ **THE OBVIOUS A/B IS VACUOUS — USE THIS DISCRIMINATOR INSTEAD.** Banning the five
>        `4F_Clean` cracks costs NOTHING (29 wp either way, 6 wp either way — MEASURED), so an
>        A/B of that shape prints "no difference" and reads as a REFUTATION of a true finding.
>        The arms that DO differ are the fall tile:
>          ARM A `4F (6,4)`/`(7,4)` ⇒ post-fall `calculate_path(3F → (7,1))` = **4 wp, OK**
>          ARM B `4F (9,4)` (the decoy) ⇒ the same call **REFUSES** (lands in the 118-tile main)
>        ‼ NAME THE INSTRUMENT PER ARM: ARM A's 4 wp is production's own `calculate_path`
>        (`evidence/2026-08-27-ch21-skypillar-probe.stdout.txt`); ARM B's refusal is so far only
>        an OFFLINE BFS over the decomp's `*_Clean` blob (`probe_skypillar_clean_layout.py:147`).
>        Re-ask ARM B of `calculate_path` before quoting it as one.
>        Both arms are executable: all three tiles are in the same 111-tile component.
>    ⛔⛔ **AND THE THING NOBODY HAS SUPPLIED, WHICH IS LEG 4'S FIRST TASK — THE ACCEPTANCE
>    PREDICATE AND THE LEG'S END BOUNDARY.** ⚠ *(half-superseded the same day: the BOUNDARY is now
>    SETTLED — see (a) below — so what remains unsupplied is the PREDICATE alone. An adversarial
>    recon pass caught this preamble still saying "neither exists" one line above the answer.)*
>    Decide, and
>    write down: (a) ✅ **ANSWERED 2026-09-01 — THE DESCENT IS IN SCOPE, and it is FORCED, not
>    chosen.** MEASURED on the CLEAN layouts: descending, the only down-staircase reachable from
>    4F's arrival is `(7,1)`, and from `3F (7,1)` the bot **CANNOT** reach `3F (3,1)` — it is
>    TRAPPED on 3F without a SECOND deliberate fall (`4F (0,3)` from `(0,2)`, or `(1,3)` from
>    `(1,2)`; both approachable). A summit-only leg therefore cannot satisfy this project's own
>    "and the bot can CONTINUE" rule BY CONSTRUCTION. Ruling + the full chain in
>    `06-DECISIONS-LOG.md`. *(superseded question:)* does leg 4 stop at the summit trigger or include the DESCENT? (the atlas says
>    "build the descent fall into the leg from the start"; the queue says only "the climb" —
>    they are different legs); (b) the end-state var to grade on — ⛔⛔ **AND IT IS NOT
>    `SKY_PILLAR_STATE` **AT THE VALUES 4 OR 5**. ⚠ Scoped deliberately: `SKY_PILLAR_STATE` DOES
>    reach **1** at the summit cutscene, so if (a) resolves to "leg 4 ends at the summit" then
>    `SKY_PILLAR_STATE == 1` may well be the right predicate. An earlier draft of this bullet
>    said flatly "it is NOT SKY_PILLAR_STATE", which over-claimed and could have banned the
>    correct answer. What is definitely wrong is the VALUES: an earlier draft wrote
>    "`SKY_PILLAR_STATE`? 4 vs 5?"
>    and that is FLATLY WRONG: **4 and 5 are `SOOTOPOLIS_CITY_STATE` values** (4 = Wallace opens
>    the door, `SkyPillar_Outside/scripts.inc:82`; 5 = Rayquaza awakened,
>    `SkyPillar_Top/scripts.inc:126`), while **`SKY_PILLAR_STATE` is 0 for the ENTIRE ascent**
>    and reaches 1 only at the summit cutscene (`12-STORYMODE-DESIGN.md` §Ch21 state table).
>    ‼ An agent taking the old text literally would grade on `SKY_PILLAR_STATE == 4`, **a value
>    the story climb never reaches** — a leg that cannot pass its own test. *(Caught by a Tier 2
>    RE-audit, 2026-09-01: the defect was introduced BY the fix for the previous audit, and this
>    same block gets it RIGHT 38 lines above, at bullet (2).)*
>    (c) the "and the bot can CONTINUE" `calculate_path` target off the tile actually reached.
>    ‼ §Ch15, §Ch18 and §Ch19 each PASSED their own test while STRANDED, and a 2026-08-28 Tier 2
>    audit named this missing predicate the #1 reason it answered NO to "could I start now?".
>    ⚠ **Also unverified:** the Rayquaza trigger `SKY_PILLAR_TOP (14,9)` DISAGREES with the two
>    coordinates our own code holds (`static_soft_resets.py:55` `(14,6)`; `static_run_away.py:163`
>    `(16,14)`/`(14,7)`). Verify it live before it gates anything.
>    ✅ **What leg 4 INHERITS, already built and proven:** `_bounded_step` (bounded, releases held
>    buttons in a `finally`), `_live_wall_tiles()` / `_live_collision_grid()` (the grid the GAME
>    walks on), `_pin_planner_to_live_layout()`, and the `LEG3_READINGS`-style readings/`method_ok`
>    grading shape in `Ch21ApproachMode`. Start from `post_skypillar_door.ss1` (PINNED, md5
>    `f6f8ab116b1bc18644286f51c2f202c6`; ⚠ party at 91% HP — there is no Poke Center up there).
>    Full detail + evidence: `12-STORYMODE-DESIGN.md` §Ch21.


## 2026-09-03 — §Ch21 LEG-4 FAULT ARMS, moved verbatim out of `04-HANDOFF.md`

⛔ **MOVED, NOT DELETED.** §Ch21 shipped as a chapter on 2026-09-02 and §Ch22 on 2026-09-03; the
handoff needed the lines for §Ch23's recipes and its own rule is to retire finished detail by
SUMMARISING AND POINTING. Every command below still works and every one is still the right
regression arm if `climb_sky_pillar` is ever touched — each FAILS for its own named reason.
`--driver ch21chapter` covers legs 1→5 end to end and is what the handoff keeps.

```
# ‼ THE SEVEN FAULT ARMS ARE NOT OPTIONAL — each fails for its OWN reason (five from the mid-leg
#   fixtures; BADBLOCKDATA from the FULL fixture, premise valid, so it fails purely on its own guard).
POKEBOT_CH21_FAULT_SUMMITSTOP=1  story_harness.py post_wallace_scene.ss1 --driver ch21climb   # FAIL, missing every descent reading
POKEBOT_CH21_FAULT_NOFALL=1      story_harness.py post_wallace_scene.ss1 --driver ch21climb   # FAIL, 'map never changed', bounded, no hang
POKEBOT_CH21_FAULT_POCKETEXIT=1  story_harness.py post_skypillar_summit.ss1 --driver ch21climb # FAIL, 'LIVELOCK, not a refusal'
POKEBOT_CH21_FAULT_DROPREADING=1 story_harness.py post_skypillar_summit.ss1 --driver ch21climb # FAIL, R-FALL2 missing though the fall happened
POKEBOT_CH21_FAULT_CONTROLOPEN=1 story_harness.py post_skypillar_summit.ss1 --driver ch21climb # FAIL, control_refused=False + order_ok=False
POKEBOT_CH21_FAULT_BADBLOCKDATA=1 story_harness.py post_skypillar_door.ss1 --driver ch21climb # FAIL, blockdata mismatch NAMES SKY_PILLAR_1F, bounded (2244 frames), no hang
PYTHONUTF8=1 py -3.12 story_harness.py post_rayquaza_gone.ss1 --driver ch21climb  # the VACUITY arm: 'already DONE; nothing to resume'
```


## 2026-09-03 — §Ch21 LEG-3 FAULT ARMS, moved verbatim out of `04-HANDOFF.md`

⛔ **MOVED, NOT DELETED**, for the same reason as the leg-4 block above. ‼ POCKETWALKBACK is the
arm an adversarial review added BECAUSE IT CAUGHT A REAL BLOCKER, and POCKETSTALL must still
PASS (`pocket_attempts=2`) — it proves the pocket recovery works LIVE. Restore from here if
`approach_sky_pillar` is ever touched.

```
# ‼ THE THREE FAULT ARMS ARE NOT OPTIONAL — the happy path cannot reach any of them. (This line
#   said TWO while THREE commands followed, until a Tier 2 audit caught it; a reader trusting the
#   count would skip POCKETWALKBACK, the arm an adversarial review added because it caught a REAL
#   blocker.) POCKETSTALL must still PASS with pocket_attempts=2 — the recovery working, LIVE.
POKEBOT_CH21_FAULT_POCKETSTALL=1 PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1 --driver ch21approach --frames 40000
#   BLINDWALL must FAIL loudly naming the step index, bounded, and must NOT hang.
POKEBOT_CH21_FAULT_BLINDWALL=1   PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1 --driver ch21approach --frames 60000
#   POCKETWALKBACK stalls the RECOVERY'S OWN walk back; it only fires while a recovery is running,
#   so it MUST be set WITH POCKETSTALL. Expect a NAMED BotModeError ("...the walk BACK to (31,17)
#   then stalled too... the stranded case") + FAIL — a RAW TimedOut... is the defect it catches.
POKEBOT_CH21_FAULT_POCKETSTALL=1 POKEBOT_CH21_FAULT_POCKETWALKBACK=1 PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1 --driver ch21approach --frames 30000
```


## 2026-09-03 — §Ch21 LEG-5 RECIPES (PART C probe + the return leg + its six fault arms), moved verbatim out of `04-HANDOFF.md`

⛔ **MOVED, NOT DELETED.** Same reason as the leg-3 and leg-4 blocks: §Ch21 and §Ch22 have both
shipped and the handoff needed the lines for §Ch23. ‼ The PART C probe's two arms remain the
reference for how KI-73 is proven on any layout-swapped map, and NPCMISS must still PASS.
`--driver ch21chapter` is the end-to-end arm the handoff keeps.

```
# leg 5 PART C — read-mostly VALIDATION probe (post_rayquaza_gone.ss1) ~16,300 fr. SETTLED
#   2026-09-02; the reference for proving KI-73 on a layout-swapped map.
PYTHONUTF8=1 py -3.12 story_harness.py post_rayquaza_gone.ss1     --driver ch21leg5probe --frames 150000
CH21_PROBE_NOPIN131=1 ... same ...   # CONTROL: un-pinned, the swim RAISES and never moves

# leg 5 — THE RETURN + HM07 WATERFALL (post_rayquaza_gone.ss1) ~20,700 fr. Expect PASS, missing=[],
#   order_ok, at=SOOTOPOLIS_CITY(31,34), hm_flag, hm07_in_bag=1, wallace_state=1, gym_door_wp=2,
#   whiteouts=0, encounters=7
PYTHONUTF8=1 py -3.12 story_harness.py post_rayquaza_gone.ss1     --driver ch21return --frames 60000
PYTHONUTF8=1 py -3.12 story_harness.py post_legends_calmed.ss1    --driver ch21return --frames 30000
#   ^ NPC half only, ~4,600 fr (FAILs by PREMISE — correct for a resumed run). Six fault arms, each
#   FAIL for its own reason except NPCMISS which must still PASS: POKEBOT_CH21_FAULT_{NOPIN131,
#   SETTLESKIP,SCENESTOP,NPCMISS,DROPREADING,CONTROLOPEN}=1

```


## 📦 `#24-ch22juan` — ARCHIVED VERBATIM 2026-09-03 (03-PUNCH-LIST.md R3 line budget)

> CLOSED 2026-09-03. Moved here **unaltered**; nothing was deleted or reworded. It was
> retired because §Ch22 shipped as a chapter the same day and this ~70-line build log was
> crowding the live items while `03-PUNCH-LIST.md` sat 2 lines under its 3,600-line cap.
> The surviving one-line pointer is in `03-PUNCH-LIST.md`.

### ✅ `#24-ch22juan` — §Ch22, GYM 8 (JUAN): **DONE. ALL DRIVERS PASS, THE BADGE IS WON, AND THE CHAPTER IS ASSEMBLED AND WIRED** (closed 2026-09-03 — see `#24-ch22chapter`)

- [x] ✅✅✅ **ALL FOUR DRIVERS PASS — a recon PROBE (`ch22probe`) plus THREE STORY LEGS
      (`ch22ice`, `ch22juan`, `ch22exit`). ⛔ DO NOT REBUILD ANY OF THEM.** Production
      `modules/story/sootopolis_gym.py`. *(This read "THREE LEGS … ch22probe/ch22ice/ch22exit" —
      counting the probe as a leg and omitting JUAN, contradicting its own header two lines up.)* Notes: `ai-research-notes/2026-09-02-ch22-juan-BUILD-SPEC.md`,
      `…-ch22-PARTA-{PREDICTIONS,RESULTS}.md`, `2026-09-03-ch22-B1F-EXIT.md`.
      Full narrative: `07-CHANGELOG.md` 2026-09-02 and 2026-09-03.
      * **PART A** (`ch22probe`, PASS, 3,958 frames) — ⛔ proved BY MEASUREMENT that
        `_live_collision_grid` / `probe_live_mapgrid.py` are **BLIND in this gym** (one ice step moved
        the METATILE grid and the COLLISION grid by ZERO), so they would PASS on a broken model. The
        working oracle is `_live_metatile_grid` (added for this) or `ICE_STEP_COUNT`. Measured 64
        thin-ice tiles in sections 7/19/38, six locked stairs, the puzzle RESETS on every entry, and
        **money = 67,466** (so healing is affordable; the problem is levels/coverage).
      * **THE ICE WALK** (`ch22ice`, PASS, 64/64 steps, 2,232 frames) — route GENERATED by
        `tools/story-dev/solve_gym_ice.py` from the decomp and re-derived on every run; its tile set
        matches the live grid 64/64 both ways. Section end counts **9/29/68** (the predicted 8/28/67
        were the raw thresholds; each unlock's `addvar` lands in the crossing step's beat).
      * **THE EXIT** (`ch22exit`, PASS, 19,989 frames, `whiteouts=0`) — first entry into B1F ever.
        Ice → **FALL** to B1F (8,6) → 19-step walk → ladder → out to SOOTOPOLIS_CITY (31,33), with a
        real 23-wp continue path. ⛔ The fall is MANDATORY: post-walk, Juan's platform is a **20-TILE
        ISLAND** (live and offline agree exactly) and `calculate_path` wrongly claims the exit is
        reachable — a THIRD proof it must never be used in this gym.
      * ✅ **EXACTLY 3 FORCED BATTLES** at (8,8)(8,17)(8,19) = Andrea/Bethany/Connie, the predicted
        sight tiles, costing 629/694 → 332/694 (~48% HP) with ZERO faints. ⛔⛔ **PRE-BADGE ONLY —
        the assembled chapter sees ZERO here** (see the decomp finding below); this driver runs at
        `badge8=False`. Three is THIS DRIVER's PASS shape; zero would be its sight-line model
        failing. ⇒ the ROUTE transfers to the chapter, the BATTLE COUNT and the HP cost do NOT.
      * ✅✅✅ **JUAN — BUILT, DRIVEN, AND *WON* (2026-09-03)** — `--driver ch22juan`,
        `ACCEPTANCE: PASS`, `BADGE08_GET`=True, `SOOTOPOLIS_CITY_STATE=6`, `battles=1`,
        `outcomes=['BattleOutcome.Won']`, **5/6 survivors**, `frames=32891`, `whiteouts=0`.
        Evidence `tools/story-dev/evidence/2026-09-03-ch22juan-WIN.txt`.
        ⛔⛔ **THIS REFUTED MY OWN PUBLISHED CLAIM.** Six files said the party could not win, some
        with the word *MEASURED* attached; it was a 1v1 damage calculation (Sceptile vs Kingdra)
        applied to a **6-versus-5** battle. Every typing premise stands — Kingdra L46 is
        WATER/DRAGON so Grass, Electric AND Ice are all NEUTRAL, nothing has a Dragon move, and
        Juan restores it three times (Rest+Chesto + 2 Hyper Potions) — only the CONCLUSION is
        withdrawn. All 12 claims corrected; root cause + 3 prevention rules in `08-MISTAKES.md`.
      * ⚠⚠ **AND IT IS SAMPLED — 5 WINS AND 1 LOSS OVER SIX DISTINCT RNG DRAWS** (2026-09-03).
        The four `ch22juan` arms all WON (control + jitter 181/1013/47; frames
        **32891 / 25508 / 21386 / 24565**, each 5/6 survivors) — but the CHAPTER drive, which
        reaches Juan after a heal and a longer navigation, **LOST** its first fight and won the
        next one after recovering. ⛔ *(This read "4 WINS OUT OF 4" for the few hours between the
        jitter sample and the chapter drive.)* ⇒ "the party CAN win Juan" is measured;
        **"wins reliably" is measured FALSE**, and the chapter owns a loss branch because of it.
        ⛔ My first three re-runs were BYTE-IDENTICAL and were **not** a sample — this harness is
        deterministic for a fixed (save, driver, code) triple, so a repeat is a REPLAY. The jitter
        knob is MEASURED to perturb (`gRngValue` 0x008c33fa → 0xfbf1b389 at N=181) and prints both
        values so a no-op sampler is visible. ⚠ **Swellow faints in every arm** and Sceptile ends
        anywhere from 141/141 to 32/141 ⇒ the post-Juan party is chewed and UNPREDICTABLE.
      ⭐⭐ **AND A DECOMP READ DELETED A WHOLE PLANNED LEG.** ✅ Read and quoted by me:
        `..._EventScript_JuanDefeated` runs `setvar VAR_0x8008, 8` + `call
        Common_EventScript_SetGymTrainers` → `SootopolisCity_Gym_SetGymTrainers` (`set_gym_trainers.inc`), `settrainerflag`ing **all ten** B1F trainers.
        ⇒ **the post-badge descent costs ZERO battles: no XP run, ONE descent.**
        ⛔ So `--driver ch22exit`'s 3 battles and 629/694 → 332/694 were measured at
        `badge8=False` — a premise the chapter NEVER ENTERS. Real numbers, NOT transferable
        (`08-MISTAKES.md` 2026-09-03). ✅ The Mart's stock is read too (Ultra Ball, Hyper/Max
        Potion, Full Heal, Revive, Max Repel, X Attack, X Defend, Shadow Mail) — with 67,466 in
        hand a stocking leg is *insurance*, not *readiness*.
      ✅ **NOTHING REMAINS — the chapter shipped the same day; `#24-ch22chapter` carries the detail and is also DONE.**
      ‼ **THE GUARDS EARNED THEIR KEEP FIVE TIMES ON THIS ITEM** — each bounded, named, and caught
      before it cost a fall or a false PASS: the `+1`-per-step counter model (it is +2 on a threshold
      crossing); a climb that CONSUMED its own first ice tile; a vacuity grade that PASSED a
      zero-frame no-op; the fall direction (y increases southward — 'Up' walked away from the fall
      tile); and the ladder warping on contact, which `_bounded_step` cannot express (the
      §Ch21-leg-4 lesson recurring verbatim). ⇒ *a pre-step check that REFUSES is worth more than a
      post-hoc assertion that explains.*
      ⚠ Drift is 10 (2026-09-03: `chapters.py` joined for a §Ch23 correctness fix) — `sootopolis_gym.py` is a new sandbox-only chapter module, as §Ch20/§Ch21 each
      added one. ⛔ PROMOTION IS THE USER'S CALL and is not implied.


## 📦 `#24-ch22chapter` — ARCHIVED VERBATIM 2026-09-03 (03-PUNCH-LIST.md R3 line budget)

> CLOSED 2026-09-03, the same day it was filed. Moved here **unaltered**; nothing deleted or
> reworded. Retired together with `#24-ch22juan` because §Ch22 shipped and the §Ch23 findings
> needed the space. The surviving one-line pointer is in `03-PUNCH-LIST.md`.

### ✅✅ `#24-ch22chapter` — §Ch22 IS A CHAPTER: **BUILT, WIRED AS SEGMENT 22, DRIVEN TO `ACCEPTANCE: PASS`, BOTH FAULT ARMS EXERCISED. THE LADDER IS 23 OF 24. ⛔ DO NOT REBUILD.** (filed and closed 2026-09-03)

- [x] ✅ **THE BLOCKER IS FIXED — `_descend_to()` NOW EXISTS.** ⛔⛔ IT WAS FOUND BY AN ADVERSARIAL REVIEW BEFORE ANY COMPOSED RUN: `_climb_to`
      WALKS NORTH ONLY.** `sootopolis_gym._climb_to` computes `nxt = (here[0], here[1] - 1)`
      unconditionally. The chapter's order is `… → fight_juan → fall_to_b1f`, and `fall_to_b1f`
      calls `_climb_to(FALL_STAGING = (8,5))` from `JUAN_STAND (8,3)` — **two tiles SOUTH**. Its
      first step would be **(8,2), Juan's own tile**: plain floor, so neither the locked-stair nor
      the cracked-ice guard fires, and it would press "Up" into him for 3 × 900 frames before
      blaming its step budget. ✅ **MITIGATED 2026-09-03** — it now refuses instantly and names the
      real problem — and ✅ **`_descend_to()` NOW EXISTS**, written after `--driver ch22stairs`
      MEASURED that (8,4)/(8,5) really do go `0x20f → 0x207` once the puzzle completes.
      ‼ *(This block read "A DESCENT HELPER IS STILL OWED, and it is the first thing to build" and
      "NO DRIVER HAS EVER RUN `walk_the_ice → fight_juan → fall_to_b1f` COMPOSED" — both were true
      when written and both were false hours later, under a `- [x]` heading that already said the
      blocker was fixed.)* ✅ **THE COMPOSED SEAM IS NOW COVERED**: the chapter drive runs it, and
      it was the acceptance test, not a formality — it found three grade defects.
- [x] ✅ **ALL FOUR MOVEMENT LEGS ARE NOW IN PRODUCTION** (`enter_gym`, `climb_to_juan`, `_descend_to`, `leave_gym_to_city`, plus `_ladder_to_1f` and `_heal_before_the_gym`). They were:
      (1) city → gym warp (31,32) → `GYM_ENTRANCE (8,25)`; (2) the 3-step stair climb
      (8,6) → `JUAN_STAND (8,3)` — ⛔ **the ice walk ends on (8,6), NOT on Juan's tile**, and both
      `walk_the_ice`'s docstring and `fight_juan`'s refusal message said otherwise until
      2026-09-03; (3) the descent (8,3) → (8,5) — ✅ **now `_descend_to()`, written 2026-09-03** after
      `--driver ch22stairs` measured the stair column; it did not exist at all, because
      `_climb_to` walks NORTH only; (4) ladder → 1F →
      out to the city. ⛔ All four are movement inside a gym where `calculate_path` is BANNED and `_live_collision_grid` BLIND — the hardest place in the tree to write "glue".
- [x] ✅ **`ch22_chapter_done()` EXISTS and is the badge AND a position** — PROVEN by two fault arms that strand in different places (`NODESCEND` on the island at (8,3); `STRANDED` on GYM_1F at (11,22)); both FAIL, and a flag-only grade would have passed both. It was:
      True while the bot is **stranded on the island**. Grade on badge AND position AND a live
      `calculate_path` off the end tile — the §Ch15/18/19 lesson.
- [x] ✅ **THE ORDER SHIPPED AND IS DRIVEN:** heal → ice → Juan →
      fall → B1F (**0 battles** — the victory script flags all ten trainers) → ladder → out.
      ⛔ Two contradicting justifications lived inside `sootopolis_gym.py` (an XP-before-Juan
      comment whose premise a comment 130 lines below retracted); the loser is deleted.
- [x] ⚠ **HAZARDS — all handled or measured; kept because they are still true of the code.** ⭐ H1 (the heal shrinking the party) was rated the RISKIEST prediction and **held**: six PIDs in, six out. Sourced in `ai-research-notes/2026-09-03-ch22-CHAPTER-ASSEMBLY-SPEC.md`:
      the heal can DEPOSIT Swellow or Zigzagoon (`DEAD_WEIGHT_LEVEL_GAP = 8`, and Zigzagoon is not
      HM-exempt because Wailmer shares Surf) ⇒ assert party COUNT and HMs by PID after every heal;
      `FLAG_ENABLE_JUAN_MATCH_CALL` lets Juan interrupt overworld walking afterwards; `BADGE08_GET`
      is set with 4 msgboxes + 2 fanfares + 60 frames still to run, so the script-idle conjunct in
      `fight_juan`'s grade is load-bearing; a mid-gym retry misdiagnoses itself ("regenerate the
      table") because the ice is spent, not the table; `VAR_ICE_STEP_COUNT` is SHARED with the
      Sky Pillar and Granite Cave.
      ✅ Two worries are REFUTED and must not be re-spent: the TM03 bag-full branch is
      arithmetically unreachable (58 TMs+HMs, 64 slots), and the Juan double-battle rematch cannot
      fire because `fight_juan` early-returns on `juan_defeated()`.
- [x] ✅ **`assert_ch22_preflight()` NOW EXISTS** (party size + `RECEIVED_HM_WATERFALL`, because the gym door is one of the ten sealed until §Ch21's second Wallace talk). ⚠ Still missing, and worth porting from §Ch21 if this module is touched again: a readings ledger. It had:
      no readings set, no `_take()`, no ORDER trace — §Ch21 has all four. ⛔ And note
      `assert_ch21_preflight()` is never actually CALLED by `do_sootopolis_chapter()`; §Ch20's
      placement (`seafloor_cavern.py:975`) is the one §Ch22 copied.
      ⇒ **WHAT §Ch22 HANDS TO §Ch23, and neither is §Ch23's to fix:** (1) the Juan fight is
      **stochastic — 5W/1L over six draws** — and the chapter recovers by design, so a story run
      may spend an extra ~35k frames there; (2) ⛔ **KI-47 can freeze the shared battle path inside
      that fight** and drop the run to Manual with NO `ACCEPTANCE` line at all. KI-47 now carries a
      deterministic ~22,000-frame repro command, which is the first this project has had for it.


## 📦 `#24-difftriggeredrules` — ARCHIVED VERBATIM 2026-09-03 (03-PUNCH-LIST.md R3 budget)

> CLOSED 2026-08-26. Moved here **unaltered**. Retired because §Ch23's build findings needed
> the space and this item is fully shipped. ⭐ **THE SYSTEM IS LIVE AND EARNING ITS KEEP** —
> on 2026-09-03 its R-SCANBOUND rule fired on a new probe and caught a coordinate scan bounded
> by the WRONG shaft's floor, which had been producing a correct answer only by luck.
> The surviving one-line pointer is in `03-PUNCH-LIST.md`.

### ✅ `#24-difftriggeredrules` — DONE 2026-08-26: rules are now INDEXED BY THE DIFF (filed 2026-08-23)

- [x] **SHIPPED 2026-08-26 — ⛔ DO NOT REBUILD.** `tools/story-dev/advise_on_diff.py`: 9 diff-keyed
      rule families (regex-added, digit-matching-added, `except`-added, `while True`-added,
      ungated-A-press-added, `set_manual_mode`-added, pristine-mirror path, 05-KI-header line,
      04/03 doc-pair paths), each firing on the SHAPE as code and silent on a `#`-comment mention.
      ⛔ ADVISORY, NEVER BLOCKING, as specified: exit 0 with or without findings. Delivery =
      `.claude/hooks/advise-on-commit.ps1` (PreToolUse on `git commit`): fail-open on every path,
      injects `additionalContext` ONLY — ⛔ deliberately NO `permissionDecision`, because an
      "allow" would auto-approve the commit past the user's permission prompt (a researcher agent
      claimed "allow" was mandatory; refuted — see `06-DECISIONS-LOG.md` 2026-08-26).
      **Proof:** 32-check `--self-test` (each rule both ways) + a mutation test (gutted
      comment-stripper → FAIL, gutted parser → FAIL, restored → PASS; transcript at
      `evidence/2026-08-26-advise-on-diff-mutation-test.txt`). An adversarial review KICKED BACK
      v1 with two real majors, both fixed + regression-tested: the two-line
      `if is_waiting_for_input(): press` idiom false-fired (now a ±2-added-line `unless` window,
      boundary tested T11c) and PURE RENAMES / BINARY diffs were invisible to path rules (git
      emits no `---`/`+++` for either; paths now also harvested from `diff --git` +
      `rename from/to` headers, tested T26-T29 incl. the real trailing-tab shape).
      ‼ Residual, deliberate: NOT in `run_gates.py` (the runner buries advisory output in
      `.gate-logs/`, which defeats "unmissable"); the hook is the delivery. Rules are a table —
      adding one = one entry + its two self-test arms (T25 enforces the pairing).


## 📦 MOVED FROM `03-PUNCH-LIST.md` ON 2026-09-04 — "SESSION END 2026-08-05" (387 lines, VERBATIM)

> **Why it moved.** `03-PUNCH-LIST.md` sat at its 3,600-line cap for three consecutive commits, and
> `lint_docs` R3's own wording names the cause: *"an archive is forming inside a current-state
> file"*. This block is **387 lines that declare themselves HISTORICAL in their own heading**, so it
> was the archive R3 meant. ⛔ **Nothing is deleted** — it is reproduced below verbatim, and a stub
> pointing here remains in the punch list.
> ‼ Its own opening line records that this heading read *"THE CURRENT TOP OF THE LIST"* for a month
> over a stale figure — which is precisely the failure mode that keeping stale content in a
> current-state file produces. Slugs preserved: `#24-cavethread`, `#24-ch21climb-whiteoutarm`, `#24-driftassertions`, `#24-driftreduction`, `#24-gymwhiteoutgatehang`, `#24-handoffbudget`, `#24-hmteachloop`, `#24-ki59archiveheader`, `#24-livegridreader`, `#24-logcollision-siblings`, `#24-organicteam`, `#24-orphans`, `#24-partycap`, `#24-pcoverflow`, `#24-pcoverflow-proof`, `#24-probecountgate`, `#24-roster`, `#24-skypillarprobewrites`, `#24-stdoututf8gate`, `#24-zerokocounter`, `#26-gatestartupcontention`.

### 📚 SESSION END 2026-08-05 — **HISTORICAL. ⛔ NOT the current top of the list.**
‼ This heading read "THE CURRENT TOP OF THE LIST" for a month, over a "Suite 78/78" figure that the suite (now 33 checks) has not matched since. **The live queue is `04-HANDOFF.md` NEXT ACTIONS.** The items below are still real; only the "current" claim was stale.

- [ ] `#24-organicteam` — ✅ **THE GATE IS LIFTED. APPROVED TO BUILD (user, 2026-08-14:
      *"Yes lift the gate as I believe it will help with other progress with this bot!"*), which
      RE-CONFIRMS RULING 1 of 2026-08-06.**
      ⛔ **THIS ENTRY SAID "DEFERRED — do not start early" UNTIL 2026-08-14 AND WAS WRONG BY FOUR
      DAYS** — the 2026-08-05 deferral was reversed by the user on 2026-08-06 (`06-DECISIONS-LOG.md`
      RULING 1, *"reversed knowingly"*), but a 2026-08-10 triage re-recorded the deferral as "the
      live instruction", so a deferral and its reversal both read as live. **Measured cost: it
      misled an agent twice in one conversation.** Both quotes are in `06-DECISIONS-LOG.md`.
      The user's REVERSAL reason (2026-08-06, quoted in the decisions log): *"it will help the
      story in the long run (less chance for failure, less errors with incompatible pokemon for
      bosses/gym leaders or missing HMs to travel…) We need this."*
      The real design question is not a seat count — it is the bot CHOOSING a team on purpose
      (type coverage, HM duties, keeping a favourite) instead of taking whatever slot is free.
      **Needs PC deposit/withdraw to be trustworthy first** — and as of 2026-08-14 that is
      measurably NOT trustworthy: three cited defects (the PC-menu Manual trapdoor, the egg-blind
      `withdraw_from_box` fullness test, and the type-only `box_counter_pid`) are being fixed
      first. It subsumes `#24-pcoverflow-proof` and the retired `POKEBOT_PC_ROTATION`.
      ‼ The OLD gate (*"story mapping must be finished first"*) is retired: the story IS mapped
      through §Ch20, and the user has ruled the feature helps the remaining progress rather than
      competing with it.

- [x] `#24-cavethread` — ✅ **CLOSED 2026-08-05 — IT WAS NEVER A BLOCKER. Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-08-17** (the R3 relief valve: this file hit its 3,600-line limit). ⛔ Nothing here is outstanding; read the archive only for the multi-hop cave reasoning.

- [x] `#24-pcoverflow` — **CATCH HALF PROVEN AND ENABLED 2026-08-07.** Two independent breaks
      were found and fixed: (1) `pc_trip.box_views()` called `boxes`, a `@cached_property`
      returning a list → `TypeError` every call; (2) both catch branches required `party < 6`.
      Capability test (`--driver boxcatch`, `post_mtpyre.ss1`): `caught=True box 0→1
      exited_clean=True exit_frames=120`, then `second_catch=True box_now=2`.
      `POKEBOT_BOX_OVERFLOW_CATCH` defaults **1**.
      ‼ The box-transfer message does NOT need dismissing — the existing battle handler already
      rides it out. I "confirmed" that wedge twice and both were my probe idling (`08-MISTAKES`).

- [ ] `#24-roster` — **APPROVED 2026-08-06, gate LIFTED. The PC-roster feature.**
      Catch overflow into the box + withdraw on demand, so the bot can field type counters and HM
      carriers it could not otherwise hold. **Rulings + rationale: `06-DECISIONS-LOG.md` 2026-08-06.**
      Measured targets: `no super-effective answer` = **8 of 15 non-finishes**;
      `nobody can learn Surf — hunting…` = **~42/batch in 16 of 17 batches**.
      ‼ Round one changes NO catch policy, NO party cap, and adds NO deposit path
      (`POKEBOT_PC_ROTATION` stays pinned at 0 — it cost ~1 team member/run and a 5.4% VOID batch).
      ‼ **KEY INSIGHT: the roster is the missing PRECONDITION for `#24-partycap`, not a competitor.**
      At cap 4 the bot hunts a Surf carrier successfully (42×/batch, costly); at cap 6 the identical
      need became a hard derail (127×) and the batch collapsed 52.0% → 15.8%. A roster decouples
      "party is full" from "cannot obtain a carrier" — the exact mechanism that made the cap fatal.
      Prerequisites, in order: `#24-hmteachloop` → `#24-pcoverflow-proof` → re-baseline → slice.
      ✅ **PARTY ORDER IS DONE AND PROVEN (2026-08-13).** `modules/story/roster.py`'s
      `reorder_party()` is driven end-to-end by **`--driver roster`**: six swaps, all verified by
      PID, including `RotatePokemon(i, j != 0)` — a path nothing in this project had ever driven.
      The drive found and fixed a real defect (it returned `True` with the avatar unable to walk;
      A/B proven). This is the piece the **Regi arc** needs (KI-69: Wailord first, Relicanth last).
      ✅ **PROMOTED to `custom-pokebot/` 2026-08-13 (user-approved)** — verified by driving
      `--driver roster --build custom` to a **frame-identical PASS**, with `find_spec` confirming
      the custom tree was the one imported. Post-copy drift ZERO. Restore point
      `restore/2026-08-13-pre-roster-promotion`.
      ‼ **The DEPOSIT/WITHDRAW half of `#24-roster` is still the open work** — ordering answers
      *"in what order"*, not *"which Pokémon"*. `withdraw_from_box` remains proven only by
      `--driver boxwithdraw`. Two issues filed and deliberately NOT fixed: **KI-70**, **KI-71**.
      ‼ `reorder_party()` still has **ZERO production callers** — it is capability, not yet content.
      ✅ **THE DEPOSIT HALF SHIPPED 2026-08-13** — `pc_trip.deposit_one_dead_weight()` frees exactly
      one slot (postcondition-verified, sole-HM-carrier exempt), wired into production via
      `early_game.ensure_hm_learner_making_room` at both `story_mode.py` HM call sites, and gated by
      `repro_hm_slot_wiring.py` (22/22, fault-injected). Driven: `--driver divelearner`
      `ACCEPTANCE: PASS`, deposit asserted **by PID**.
      **Measured worth:** 20 terminal run-kills in 1,129 runs (**0.91%** excl. a reverted party-cap
      bundle) and **#1 of 14 derail causes by frames per event (1,717k ≈ 46 min)**, every one five
      badges deep — rare, but it kills the deepest runs.
      ✅ **PROMOTED 2026-08-14 — `custom-pokebot` is no longer inert.** ⛔ Corrected 2026-08-14:
      this line read *"NOT promoted — `custom-pokebot` is still inert (reads the flag, nothing
      sets it)"* for hours AFTER the promotion landed, contradicting `04-HANDOFF.md` item 1b and
      the changelog. Caught by MEASURING (`promote.py --check` lists only the two PARTY ACCOUNTING
      STAGE 0 files), not by reading. ‼ *A promotion updates the handoff AND every punch-list item
      that claims the file is unpromoted — that is a P-pair, and it was missed.*
      ‼ **STILL OPEN in this item:** withdraw-on-demand, catch-overflow policy, and any use of
      `reorder_party` by real content (the Regi arc is what will need it).

      ## PARTY ACCOUNTING — STAGE 0 SHIPPED 2026-08-14 (the ROOT beneath the P1/P2 fixes)
      ✅ **`modules/party_accounting.py` + gate `repro_party_accounting.py` (#22).** Splits the
      three quantities RULING D named: **A** `gPlayerPartyCount` (CAPACITY authority), **B**
      `len(get_party())` (ITERATION/INDEX authority, can be LESS than A), **C** the belief ledger
      — **not built, deliberately**. Divergence classes: HOLE / OVERFLOW / INVALID observed
      EXACTLY from `get_party()`'s own branches; STALE ⛔ **SAMPLED 1-in-300, never exhaustive.**
      ✅ **It wires NO call site, and the gate ASSERTS that** rather than trusting it — alongside
      a byte-identical observer-on/off A/B, silence on a healthy party, and a raising observer
      that must break the LOG and never the read. Three source injections each made it fail.
      ✅ **DRIVEN:** `--driver ch20dive` → `ACCEPTANCE: PASS` unchanged, and the run reported
      **25,523 recomputes / 86 scans / NO DIVERGENCE** — which also empirically confirms the
      once-per-frame bound (25,523 recomputes over 25,523 frames).
      🔜 **NEXT IS MORE MEASUREMENT, NOT STAGE 1.** ⛔ Do not re-point the ~35 capacity-shaped
      call sites at A until `collect_party_accounting.py` exits 0. ✅ PROMOTED 2026-08-15 (user-approved,
      verified by driving `--build custom` to an ACCEPTANCE: PASS); drift is back to nil.
      ‼ **(P3b) 2026-08-15 — the collector I shipped COULD NOT REACH ITS OWN CRITERION.** It
      demanded ≥5 drives and read them from `harness*.log`, which `story_harness.py:70` opens
      `"w"` — **every drive truncates the previous**. Fixed with a durable append-only
      `party_accounting_ledger.jsonl`; proven by ACCUMULATING, not by inspection. And its first
      fixed run **double-counted one drive as two** (`ch20dive` vs `Ch20Dive`), so fingerprints are
      normalised and log-scanning is OFF by default. ⇒ *for a tool that decides "is there enough
      evidence yet", over-counting is the dangerous direction.*
      ✅✅ **(P3b) ANSWERED 2026-08-15 — CRITERION (a) MET, the collector exits 0.
      7 clean drives / 7 distinct drivers / 280,707 recomputes / 940 scans / NO DIVERGENCE.**
      `ch20dive` 25,523 · `room1` 28,364 · `room9` 69,645 · `room2` 31,275 · `room8` 47,585 ·
      `room3` 46,118 · `room6` 32,197. ‼ `ch20room9` LOST its Archie fight (documented 2W/1L) and
      its row was written anyway — the measurement is independent of the driver's verdict.
      ⛔⛔ **READ THE POPULATION, NOT JUST THE ZERO.** All seven drives are §Ch20 DUNGEON content
      with a STATIC party — no catching, no evolving, no PC traffic. The scenarios most likely to
      make A differ from B (catch into a full party; a Shedinja spawning unbidden) were never
      exercised. The criterion was pre-registered and is honestly met, so P3b CLOSES — but the
      finding is *"the dungeon path is clean"*, **not** *"A cannot differ from B"*, and it is NOT
      licence to re-point the ~35 capacity call sites. ⇒ **(P4) is the better next step than
      Stage 1**: its fixture is exactly the party-mutating case this population lacks.

      ## (P4) THE END-TO-END REPRO — ✅ STAGE 1 **AND STAGE 2** DRIVEN, 4/4 ACROSS BOTH FORKS
      ✅✅ **STAGE 2 IS DRIVEN 2026-08-15 (`--driver boxcounter2`) — matrix {ARM A, ARM B} ×
      {sandbox, custom} = 4/4 `ACCEPTANCE: PASS`. ⛔ DO NOT REBUILD IT.** A SUBCLASS of
      `BoxCounterMode`, so every Stage 2 run re-proves Stage 1 first. ARM B: the real
      `heal_in_pokemon_center(FortreeCity)` collected the boxed Slugma — `moved=True` (in party
      AND gone from the box), `knows_rock_throw=True`, `lead_is_counter=True` with a
      `hunted_pids=None` CONTROL proving the mechanism was decisive (`control=Mightyena L38` →
      `real=Slugma L15`), and a second heal that NO-OPed for the ATTRIBUTED reason. ARM A: the
      derail reproduced organically — `_hunted_counter_pids` published EMPTY, counter left boxed,
      **no deposit at all**. ‼ The PID is published ONLY from `box_counter_pid`'s return value.
      ⛔⛔ **THE ANCHOR IS `fortree_gym_wedge.ss1` — the "use `ch13_fortree_door.ss1`" correction
      further down this entry is REVERSED BY A DRIVE.** `ch13_fortree_door` is on ROUTE120 and the
      run died on its first leg (`Cannot reach FORTREE_CITY: it is not walkable from ROUTE120`) —
      **KI-24**, documented in our own `region_reach.py:7-11`. ⚠ The wedge has NO Shedinja/Ninjask
      twins, so `ch13_fortree_door.ss1` stays the anchor for tests whose SUBJECT is that collision.
      ⛔ **`needed` IS `{Rock, Ice, Dragon}` — NOT `{…Electric}`** (the ace is Altaria,
      Dragon/Flying; Electric is 0.5×2.0 = 1.0, NEUTRAL). Caught by the new `needed_ok` control on
      its first run; the four-type set was in four documents that were copies of one another.
      🔜 **WHAT (P4) STILL DOES NOT COVER:** everything UPSTREAM of registration — a real `hunt()`
      catch feeding `story_mode.py:1750`. The Slugma is INJECTED and the PID published by the
      driver. Also still unbuilt: the natural-vs-injected byte-equivalence control.
      🆕 **RESIDUAL `#24-zerokocounter` (filed 2026-08-16, from the KI-80 decoupling):
      SHOULD `boss_teaches` ALSO COME OFF THE COUNTER-LADDER'S GATE?** The KI-80 fix removed
      `grass_is_fodder` from `story_mode.py:1901` and KEPT `boss_teaches`. KI-80's own wording
      ("gated on *is this fight hopeless*, which `_boss_plan_is_hopeless` already answers alone")
      can be read as removing BOTH conjuncts. ‼ **The argument for removing it is strong:** a party
      that KOs **nothing** and has no type answer is the MOST hopeless case, yet it currently gets
      the `:1932` "the boss can't teach us" message and plain grass escalation rather than a counter
      hunt. ⛔ **It was NOT shipped because NO TEST CAN SEE IT:** all four `ki80ladder` arms seed
      `kos = 1`, so `boss_teaches` is True in every arm we have. Shipping it would be changing
      behaviour we cannot observe — the thing this project keeps being burned by.
      ⇒ **To pick this up: add a FIFTH arm that seeds a flat `kos = 0` history** on
      `batch2_run04_wedge.ss1` with the NOGRASS cfg. ✅ **DISCRIMINATOR COMPUTED 2026-08-16 — the
      arms DO differ:** `recent_kos = [0,0]` ⇒ `boss_teaches` False ⇒ **today** `:1901` is skipped,
      `:1932` fires, `boss_mode` stays False, `OUTCOME = PLAIN_ESCALATION`; **after** removing the
      gate, `_boss_plan_is_hopeless` runs and every one of its own gates still passes on a flat zero
      seed (`losses 8 >= 6`; `len 8 >= 6`; `max(last 3)=0 > max(prev 3)=0` is False so it does NOT
      bail; `hard_plateau` needs 12) ⇒ `hopeless=True` ⇒ `OUTCOME = LADDER`. Non-vacuous.
      ⛔⛔ **BUT A FIFTH ARM IS NOT ENOUGH, AND THIS ENTRY UNDERSTATED THE HAZARD UNTIL 2026-08-16.**
      It described the `:1932` problem as a lost MESSAGE. It is worse, twice over:
      (a) removing `boss_teaches` makes `:1901` unconditional, so the `elif` at `:1932` is
      **structurally DEAD in every case**, not just the hopeless one — an `elif` on an always-true
      `if` never runs; and (b) the NOT-hopeless path below becomes reachable by a zero-KO party for
      the first time, so a boss with a **fodder patch AND a credible answer** whose party KOs
      nothing would hit `if grass_is_fodder: boss_mode = True`, print *"re-attempting the boss is
      the real training (KO'd [0, 0] of theirs)"* — absurd on its face — and **SUPPRESS `:1937`'s
      grass escalation.** ‼ **That is KI-23's mirror regression in a new guise, and arm 5 CANNOT SEE
      IT** (a NO_ANSWER save returns at `:1923` and never reaches `:1925`). ⇒ **an ARM 6 is required
      too: HAS_ANSWER save + `kos = 0` + a FODDER patch.** Same lesson as arms 1-3 vs arm 4.
      ⚠ **And measure first:** nobody has checked how often a flat zero-KO loss series actually
      occurs in production. `analyse_defeat_loops.py` measured *"53 sequences with >=3 defeats — flat
      in 37"* but never broke out zero-KO series. ⛔ Do not change behaviour of unknown frequency.
      *(Hazard (a)/(b) and the discriminator were derived by a Tier 2 cold-start agent, 2026-08-16.)*
      🆕 **RESIDUAL (filed 2026-08-15, found by a Tier 2 cold-start): `04-HANDOFF.md`'s
      `NEXT ACTIONS` numbering RESTARTS.** It runs 1, 2, 2c, 3, 3b, 4, 5 and then begins again at
      2b, 3, 4, 5, so a cross-reference to "NEXT ACTIONS item 3" resolves to TWO different items.
      Not misleading about STATE — item 0 is unambiguous and is what a cold start acts on — but any
      citation to items 1-5 is unresolvable. ⇒ when the "older framing" block is next touched,
      archive it wholesale rather than renumbering in place.
      ✅✅ **KI-80'S REPRO IS BUILT, DRIVEN AND FAULT-TESTED (2026-08-15) — `--driver ki80ladder`.**
      THREE arms on `saves/batch2_run04_wedge.ss1` (`team_max` 28, 8 seeded losses): `NOGRASS` →
      ladder · `GRASS_FODDER` (Route 102, `wild_max` 4) → ladder · ⛔ `GRASS_STRONG` (Route 119 —
      **the patch her own cfg comment names**, `story_mode.py:3531`; ⛔ she has NO `grass` key today, `wild_max` 27) → **plain escalation, ladder SKIPPED.** Only the
      `grass` key differs. `ACCEPTANCE: PASS` in BOTH forks. Fault-tested twice: the fixture KI-80
      itself once prescribed (`ch13_fortree_door`) FAILS with *"THE A/B WOULD BE VACUOUS"* and all
      three arms return `LADDER`. ‼ **Exits 0 even on FAIL — grade the `ACCEPTANCE:` line.**
      ✅✅ **DONE AND PROMOTED 2026-08-16 — ⛔ DO NOT REDO THIS.** *(This block used to end with
      ➡ "NEXT: decouple `_counter_ladder` from `grass_is_fodder`" and "`POKEBOT_KI80_DECOUPLED=1`
      FAILS today". BOTH became false on 2026-08-16 and stood until an adversarial audit caught
      them on 2026-08-17 — an arrow commanding work that had shipped to BOTH forks.)*
      **MEASURED NOW:** `story_mode.py:1901` is `if boss_teaches:` in sandbox AND custom, and the
      driver's expectations are inverted so `POKEBOT_KI80_DECOUPLED=1` **PASSES**.
      ⛔⛔ **BUT NOT THE NAIVE EDIT, AND `POKEBOT_KI80_DECOUPLED` ALONE WILL BLESS IT.** MEASURED
      2026-08-16: with `grass_is_fodder` simply deleted from the `:1901` gate, the three-arm run
      goes **`ACCEPTANCE: PASS`** — all three arms reach the ladder — while KI-23's **mirror
      regression has silently landed**. ⇒ **ALSO RUN ARM 4, BEFORE AND AFTER:**
      `POKEBOT_KI80_ARM4=1 … story_harness.py fortree_gym_wedge.ss1 --driver ki80ladder`.
      It PASSes today and, against that same naive edit, printed
      `ARM4 OUTCOME=BOSS_TRAINING_MODE` and `ACCEPTANCE: FAIL` — *"a boss with a STRONG patch AND a
      credible answer entered BOSS-TRAINING MODE, so `:1937`'s plain grass escalation is
      SUPPRESSED."* Keep `boss_mode = True` (`:1925`) behind `grass_is_fodder`.
      Transcripts: `evidence/2026-08-16-ki80ladder-FAULT-naive-edit-*`. The BEFORE run is committed FIRST because
      it is unrepeatable afterwards. `repro_boss_grass_gate.py` SELF-RETIRES on the fix — designed.
      ✅ **BOTH PROMOTIONS ARE DONE (user-approved 2026-08-15).** *(✅ The comment-only `story_mode.py` fix was PROMOTED 2026-08-16, user-approved. ✅ And the KI-80 DECOUPLING in the same file — a BEHAVIOUR change — was PROMOTED 2026-08-16 too, by a THREE-POINT A/B against `--build custom`. drift is 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until the chapter is driven) — `modules/story/seafloor_cavern.py`, the §Ch20 chapter UNDER CONSTRUCTION, sandbox only. ⛔ NOT a promotion decision: it is incomplete (constants + predicates + preflight only, no legs yet) and must not be promoted until it is driven end to end..)* The KI-79 fix `pc_trip.py` (a BEHAVIOUR change) was proven by a THREE-POINT A/B showing the new branch actually RUNS in custom, not merely that the file copied. And `counter_hunt.py`
      (comment-only, the Electric correction) promoted with restore point
      `restore/2026-08-15-pre-promotion-counterhunt-comment`: 1/1 byte-identical, and VERIFIED BY
      DRIVING — `--driver boxcounter2 --build custom` ARM A and ARM B both `ACCEPTANCE: PASS`,
      plus four `--build custom` gates. See `custom-pokebot/DIVERGENCE-LOG.md`.

      *(Everything below is the Stage-1-era text. It is kept for its build detail; where it
      predicts Stage 2 or names the anchor, the block above supersedes it.)*
      ## (P4) THE END-TO-END REPRO — ✅ STAGE 1 DRIVEN (both arms), ⛔ STAGE 2 NOT BUILT
      ‼ **Read `ai-research-notes/2026-08-15-p4-boxcounter-repro-design.md` before building.** It
      refuted FOUR of the premises it was briefed with, two fatally: the heal's withdraw is no
      longer gated `if _pids:`, and ⛔ **`post_dive.ss1` is POST-WINONA**, so the counter rung can
      never fire from it (use `saves/ch13_fortree_door.ss1` — the wedge sits INSIDE the gym).
      ✅ **BUILT:** `debug_write_box_slot()` (`debug_utilities.py`) — the missing half of the
      fixture, mirroring the storage reader; refuses on R/S, on an occupied slot, on a short
      record. `POKEBOT_BOXCOUNTER_TYPEONLY_A` — a permanent fault hook restoring the pre-fix
      TYPE-ONLY behaviour, read INSIDE the function. And `repro_box_counter_move_test.py` now
      exercises the **REAL** hook (4 checks, 2 of them controls) — every arm in that gate was
      previously a re-implementation, so the hook could have rotted unnoticed.
      ✅ **STAGE 1 IS DRIVEN 2026-08-15 (`--driver boxcounter`), BOTH ARMS PASS** — the first time
      `box_counter_pid` ran against REAL `gPokemonStorage` memory rather than `FakeStorage`.
      ARM B → the Slugma's PID (found by its MOVE); ARM A (`POKEBOT_BOXCOUNTER_TYPEONLY_A=1`) →
      `None`, the user's bug reproduced on demand. Four controls: `disjoint`, `fixture_ok`,
      `sole`, `not_excluded`. ⛔ Stage 1 CANNOT DERAIL, which is why the decisive claim lives
      there — under KI-71 a derailed arm prints nothing at all.
      ✅ **ANCHOR CORRECTED BY MEASUREMENT for Stage 2: `saves/ch13_fortree_door.ss1`**, not
      `fortree_gym_wedge.ss1` (that one sits INSIDE the gym). It holds a **REAL Shedinja+Ninjask
      sharing `pid=42207D6F`** — the first LIVE KI-78 twin pair here. ⚠ Its box holds a Castform.
      🔜 **SMALL OPEN ITEM (not blocking):** two docstrings still say the Shedinja twin is "the
      LATER slot" without the *at creation* caveat — `repro_pid_identity_key.py` (tools, free to
      edit) and `pokemon_party.get_index_for_pokemon` (PROMOTED, so editing it costs a promotion
      cycle). The live save has them REVERSED because `reorder_party()` runs. The fix does not
      depend on order, so this is wording, not behaviour.
      🔜 **STAGE 2 REMAINS:** the heal → withdraw → boss-fought-WITH-the-counter half,
      a one-time natural-vs-injected byte-equivalence control, and the
      {ARM A,B}×{sandbox,custom} matrix. ⛔ **The likeliest way it ships broken:** inject the
      Slugma BEFORE `counter_hunt.py:477`'s `before_box_pids` snapshot and `exclude_pids` filters
      it out — `None` in BOTH arms, so ARM A "reproduces" the bug for entirely the wrong reason.

      ## THE HEAL'S PC PIGGYBACKS NOW REPORT — the OTHER half of the Slugma/Winona derail (2026-08-14)
      ✅ **Gate #23 `repro_heal_piggyback_reporting.py` (20 checks, no emulator; ‼ it PRINTS its own count — believe that, not this).** The three PC
      actions riding on `heal_in_pokemon_center` (rotation deposit, KI-63 slot-freeing deposit,
      hunted-counter withdraw) each wrapped everything in `except Exception: pass`, collapsing
      *worked* / *nothing to do* / *threw* into one silence. **The user's run took the middle
      branch and said nothing** — that silence is most of why the bug cost a day. All three now
      report; the decision is a pure, testable `counter_withdraw_outcome()`; the empty-case message
      names `_hunted_counter_pids` AND the Slugma shape. ⛔ The empty case must NOT read as an
      error — it is the common case, and that is a gate check, because a diagnostic that cries
      wolf on every heal is worse than the silence it replaced.
      ‼ **Why no gate caught it:** `repro_no_silent_except` did not scan `modules/modes/util/`, and
      **its rule-3 escape hatch had already approved all three handlers** — a justification comment
      documents intent, it does not make a failure observable. Scope extended (baseline 140 → 149)
      and the ratchet is now **per scan root** (133/4/3/9, all measured), so the widened budget
      cannot fund new debt in the roots it already covered. Both halves fault-tested.
      ⛔ **THIS IS NOT (P4).** P4 — the END-TO-END live repro — is **still owed**. Recon is done and
      its three constraints are recorded in `04-HANDOFF.md`'s queue item P4 (no save holds a
      Nincada; KI-71 means a derailed arm prints NO RESULT; do not depend on a stochastic catch).

- [ ] `#24-logcollision-siblings` — **NEW 2026-08-16, found while fixing `#24-orphans` (4).** Four
      more repro scripts carry the SAME evidence-destroying pattern `story_harness.py` just shed —
      a fixed default log name opened `"w"`, so re-running the same arm silently eats the previous
      transcript: `repro_hm_move_replace_loop.py:82`, `repro_hm_replace_valve_forced.py:54`,
      `repro_movelearn_fault_recovery.py:73`, `repro_movelearn_hm_wedge.py:65`. ⚠ **Milder than the
      harness's was** — each varies by `build`/`mode`/`state`, so it only collides when the SAME
      arm is repeated (still exactly the before/after case). ⇒ apply the same one-line fix
      (`_<timestamp>_<pid>`, print the path first). **Filed rather than done** so the change can be
      run-verified per script instead of swept in unverified — the harness fix was proven by an
      actual A/B, and these deserve the same.

- [x] `#24-driftassertions` — ✅✅ **DONE 2026-08-17: the drift-statement sweep IS A GATE** (`check_drift`, A/B-measured 4→9 sites caught with none lost, 17 fault tests). **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-08-18** (R3 budget). ⛔ Nothing outstanding here. ‼ Its SEPARATE reduction half is `#24-driftreduction` and is still OPEN. ‼ Two rules the gate earned and later work leans on: **claim-bound, never neighbourhood-bound** exemptions (a proximity window exempted a live claim twice), and **a gate cannot tell a quotation from a claim** — describe a stale figure, never reprint it.

- [x] `#24-handoffbudget` — ✅ **DONE 2026-08-17. `04-HANDOFF.md` was 7 lines from its 900-line limit; 38 LINES WERE RECOVERED, NET, and NOTHING WAS DELETED.** *(The merge itself freed 43; six citations an independent check found missing were then RESTORED, costing five back. ‼ This headline said 43 until a Tier 1 reviewer recomputed it from `git show HEAD:` — the item about stale numbers published a stale number, in its own headline.)* **** ⛔ No current count is quoted here — `lint_docs.py` prints it and IS the authority; a quoted count goes stale on the next edit to the file it describes (this row's own predecessor did, three times in one day, once by a single line). Ten `##` stub sections (`:179-233`) whose detail has lived in `28-HANDOFF-ARCHIVE.md` since 2026-08-13 were merged into one. ‼ **The saving came mostly from DE-DUPLICATION, not from cutting:** *"a chapter's acceptance test must include AND THE BOT CAN CONTINUE"* was written out THREE times in separate sections and *"N instruments agreeing on something impossible share a missing primitive"* TWICE; each is now stated ONCE, loudly. ⛔ An independent agent enumerated every claim, lesson, number and citation in the BEFORE text and checked each against the AFTER — the merge was not trusted to my own reading of it. ⚠ **My FIRST attempt made the file LONGER (893 → 905, R3 RED)**: consolidating headings does not shrink a file if the replacement prose is more verbose than what it replaced. Reverted and rewritten tight. *(Original filing:)* **`04-HANDOFF.md` was at 893/900 lines (7 FREE), which BLOCKED the next item's Definition of Done.** A Tier 2 cold-start audit measured it: a few
      added lines turn `lint_docs.py` RED, and step 2 of the DoD (update the docs) then cannot be
      committed. ⛔ **MEASURE with `lint_docs.py`; do not quote this line** — the budget row in the
      handoff has itself gone stale twice in one day.
      ✅ **THE WORK IS CONSOLIDATION, NOT DELETION, and the candidates are already identified:**
      `04-HANDOFF.md:179-233` is ten `## … MOVED to 28-HANDOFF-ARCHIVE.md` stub sections. They are
      NOT empty pointers — each keeps a distilled LESSON — but several keep the SAME one. *"A
      chapter's acceptance test must include **and the bot can continue**"* is restated at `:196`,
      `:209-212` and `:224-225`; the §Ch18 *"N of your own instruments agreeing on something
      impossible share a missing primitive"* lesson is at both `:185-189` and `:192`.
      ⇒ Merge the duplicates into ONE block per lesson, keep every DISTINCT lesson verbatim, and
      leave the archive untouched (it already holds the detail). Expected saving ~15-25 lines.
      ⛔ **DO IT AT A QUIET MOMENT, NOT MID-ARC** — same reasoning as `#24-driftreduction`: it
      touches the lines every in-flight change touches, and it must not run while a Tier 2 audit is
      reading the file. ‼ Re-run Tier 0 AND a fresh cold-start read afterwards: these stubs are what
      a cold agent skims, so a bad merge costs more than the lines it saves.
      ⚠ Related but SEPARATE: lint's `I1` line reports the completed `[x]` items still sitting in
      `03-PUNCH-LIST.md` — ⛔ RUN IT rather than quoting it; that figure and the line budget beside
      it were BOTH stale within a day of being written. That is this file's relief valve, not the handoff's.

- [x] ✅✅ DONE 2026-08-23 — ALL 17 nav retry loops patched, and GATED — 📦 **ARCHIVED 2026-08-26 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [x] **✅ DONE 2026-08-23 — both halves fixed** (`00-README`'s row was corrected earlier; `31`'s own header was corrected 2026-08-23 to say KI-59 is FIXED, KI-60 is open, and that "armed in the Seafloor Cavern" is refuted by that file's own correction). Original text follows.
      `#24-ki59archiveheader` — **NEW 2026-08-17, from a cold-start audit. THREE FILES DISAGREE ABOUT
      WHETHER KI-59 IS OPEN, and the one a cold reader meets first is wrong.**
      `00-README.md` describes `31-KNOWN-ISSUES-ARCHIVE.md` as *"Resolved/superseded known issues …
      Not current state"*; that file's OWN header says two **OPEN, unfixed** pathfinder bugs live in
      it (KI-59, KI-60); and `05-KNOWN-ISSUES.md` — **the correct one** — says *"KI-59 ITSELF IS
      FIXED, A/B-PROVEN, GATED (#17) AND PROMOTED TO BOTH FORKS"*, with only a NARROWER residual plus
      KI-60 still open. `04-HANDOFF.md` agrees with `05`.
      ⇒ **Fix `31`'s header to name the residual rather than the whole KI, and make `00-README`'s row
      say the file may contain open residuals.** ⛔ Do not "fix" it by marking KI-59 open — that would
      re-open work that is fixed, gated and promoted, which is this project's most expensive mistake.
      ⚠ Cheap, but it misdirects EVERY cold start that follows the reading order.

- [x] ✅ DONE 2026-08-22/23 — brought current, and it was WORSE than — 📦 **ARCHIVED 2026-08-26 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [ ] `#24-gymwhiteoutgatehang` — **NEW 2026-09-01. `repro_gym_whiteout_guard.py` HANGS, and it
  is RED in `run_gates.py` right now.** Measured twice: killed at the suite's **900s** bound, then
  re-run STANDALONE, where it produced no further output for **~36 minutes** and never printed a
  verdict at all (a 1500s `timeout` was set on the wrapper; it did not appear to reach the child
  process, so the run simply went quiet rather than being cleanly killed). Both times it stops
  after printing
  `[1]+[2] FAULT INJECTION — force the player 'off the gym map' part-way through the route` and
  emits nothing further. ⇒ it is a genuine hang at the fault-injection step, **not** gate-startup
  contention (`#26-gatestartupcontention`), because the standalone run had the machine to itself
  for most of its window.
  ⛔ **NOT CAUSED BY §Ch21 LEG 3, and that is checkable rather than asserted:** the only
  production file this session changed is `modules/story/sootopolis.py` (see `git diff --stat`),
  and `repro_gym_whiteout_guard.py` imports `modules.story.mossdeep_gym` and
  `modules.story.early_game` only — it never imports `sootopolis` or `story_harness`.
  ‼ **It was NOT re-verified against an older commit**, so "pre-existing" is an INFERENCE from
  the import graph, not a measurement. The cheap decisive test is to run it on the previous
  commit; do that before assuming it broke today.
  ⇒ **the suite measured 30 of 32 PASS when it ran.** The OTHER failure,
  `repro_no_silent_except.py`, was RED for a real reason (leg 3 added 3 silent handlers,
  126 > the 123 budget for `modules/story`) and has been FIXED — the handlers are justified
  in place and it now reports `PASS — exactly at the baseline. No new debt.` ⇒ a re-run should
  read **31 of 32**, with THIS item the only red. ‼ That is an INFERENCE from re-running the
  one gate alone, not a re-run of the whole suite (which costs ~40 minutes).
- [ ] `#24-skypillarprobewrites` — **NEW 2026-09-01, found by a Tier 2 cold-start audit.**
  `probe_ch21_skypillar.py` is documented in `04-HANDOFF.md` as "Seconds, no network" recon, but
  running it **WRITES**: it emitted `Save state ...profiles/repro-ml/states/<ts>.ss1 created!` and
  `Updated current_state.ss1!`. The path is gitignored so the repo is safe, but it mutates the
  SHARED `repro-ml` profile — and an agent may run it many times while building leg 4.
  ‼ **This is the class PASS 4 claimed to close** (`04-HANDOFF.md` credits it with fixing "seven
  observe-only gates writing shared profile state, 2,820 files / 160 MB"); this probe was added
  2026-08-27, AFTER that sweep, and re-introduced it. ⇒ the sweep fixed the instances, not the
  cause — there is no gate that FAILS a probe for writing profile state.
  ⛔ Fix the probe, and consider the gate: a check that an "observe-only" tool leaves
  `profiles/` byte-identical would make the class impossible rather than merely rare.
- [ ] `#24-stdoututf8gate` — **NEW 2026-09-01.** `audit_handoff_invariants.py` AND `lint_docs.py`
  crashed with `UnicodeEncodeError` under bare `python` on cp1252 (they print `⛔`/`‼` without
  reconfiguring stdout; only green because `run_gates.py` sets `PYTHONUTF8=1`). Both fixed in place
  (module-scope `reconfigure("utf-8")`); see `08-MISTAKES.md`. ‼ Crash class has recurred 3×+
  (`verify_fixtures.py`, the repro sweep, now two gates) → a GATE is owed: fail any `tools/story-dev/*.py`
  that can emit non-ASCII yet neither reconfigures stdout nor uses a byte-safe writer; FAULT-TEST it
  (fires on a no-reconfigure emoji print; not on `verify_fixtures`'s `buffer.write` nor pure-ASCII).
- [ ] `#24-ch21climb-whiteoutarm` — **NEW 2026-09-01, code-review finding 4 (OPTIONAL).** No arm has
  DRIVEN a real whiteout, so the leg's grade-on-POSITION-not-vars claim (a post-summit whiteout reads the
  same 5/1/1 from Sootopolis) is argued, not measured. Add `POKEBOT_CH21_FAULT_WHITEOUT` (all-BURNED 1-HP
  party → first encounter whites out; assert `whiteouts=1`, `reached=False`, FAIL). Deferred: needs
  party-injection + a battle drive; a flaky arm is worse than none.
- [ ] `#24-livegridreader` — **NEW 2026-09-01, created by §Ch21 leg 3's first drive. PROMOTE THE
  LIVE-GRID READER OUT OF A CHAPTER MODULE AND INTO `modules/map.py`.** Three helpers currently
  live in `modules/story/sootopolis.py` because that is where the bug bit: `_live_collision_grid()`
  (reads `gBackupMapLayout` — the grid the GAME walks on, and the ONLY reader in this tree that
  can observe `setmetatile` or `setmaplayoutindex`), `_live_wall_tiles()`, and
  `_pin_planner_to_live_layout()`. ⛔ **They are general, and the hazard is general** — every map
  that swaps a layout at runtime has it, and KI-74's own "what a fix looks like" asked for exactly
  this promotion. Leaving them in a chapter means the NEXT chapter re-earns the bug.
  ‼ **WHAT MAKES THIS NON-TRIVIAL, so nobody starts it expecting a move-and-rename:**
  (a) `_live_collision_grid` is valid ONLY for the currently loaded map and must keep refusing
  otherwise; (b) `_pin_planner_to_live_layout` MUTATES two process globals — it must evict the
  WHOLE `map_path._maps` game key, never one map (a per-map `pop` raised `KeyError` on a real
  drive, because `_get_all_maps_metadata` only populates when the key is absent entirely);
  (c) the border offset is `MAP_OFFSET = 7` but the backup grid is `mapWidth + 15` by
  `mapHeight + 14` — **asymmetric**, so a "derive it from the dimensions" implementation is
  wrong in a way that looks principled. ⇒ port the guards and the comments, not just the code.
  Evidence: `evidence/2026-09-01-ch21-leg3-LAYOUTPIN-ab.txt`, `probe_live_mapgrid.py`, KI-74.
- [ ] `#24-probecountgate` — **NEW 2026-08-17. Teach `audit_doc_consistency.py` to grade PROBE
      COUNTS the way it already grades gate counts and the drift figure.**
      ‼ **FILED FROM EVIDENCE, NOT A HUNCH: this is the THIRD un-gated number class to go stale in a
      SINGLE SESSION.** Drift claim-shapes went first (`#24-driftassertions`), then gate counts
      — ⚠ DESCRIBED, NOT REPRINTED (this gate matches literal strings and fired on this bullet's first draft): one phrasing put a NOUN between subject and verb, another wrapped the digits in markdown BOLD. And now
      `probe_abort_swallowing.py`'s candidate count: after round 2 took it 45 → 37, **three** sites
      still said 45, including **KI-81's HEADER AND BODY** — a P2 pair that went stale together — and
      a runnable command's trailing comment. A Tier 1 reviewer found them by RUNNING the probe.
      ⇒ **The pattern is now unambiguous: any number a doc quotes and a tool can measure WILL go
      stale, and prose discipline has never once caught it here.**
      **THE DELIVERABLE:** a rule that finds claims of the shape `N candidates`, `N candidate sites`,
      `N remain`, `45 → 37` near `probe_abort_swallowing` and compares them against the MEASURED
      count. ⛔ **FAULT-TEST BOTH WAYS** — it must fire on a stale count AND stay quiet on a clearly
      HISTORICAL one (`03-PUNCH-LIST.md` deliberately preserves *"Original remaining count when this
      item was filed: 45"*, and `07-CHANGELOG.md` is append-only history that must never be graded).
      ‼ Reuse the machinery that already exists rather than inventing a fourth dialect: `_CURRENCY`
      marker attachment, the span-scoped retraction exemption, and the `[*_]{0,2}` markdown
      tolerance are all in that file and were each earned by a real miss.
      ⚠ **COST NOTE:** the probe is a static AST scan over ~20 files, so measuring is cheap — but
      confirm it before wiring it in, because `audit_doc_consistency.py` runs in every Tier 0 check.
      ⚠ **AND SCOPE IT:** grade only CURRENT-STATE files (00-05, 24). `07`/`08`/`28`/`31` are
      append-only history where a stale count is CORRECT.

---

## 2026-09-05 — three superseded HISTORY blocks retired from `03-PUNCH-LIST.md`

⛔ **ARCHIVED VERBATIM, NOT SUMMARISED — and this time the claim is CHECKED.** The script that
moved these blocks asserts that every non-blank line it removed from the punch list appears
below; the first attempt made the same claim with no such check and truncated two of the three.
⇒ ⭐ **a falsifiable claim in a document is worth exactly as much as the check behind it.**

All three belong to items that are **CLOSED**, and each is self-labelled HISTORY or *(original
finding)* — superseded narrative kept for its reasoning, never a live instruction. Their
punch-list entries now carry a one-line pointer here, matching how `#24-magmahideout` and
`#24-strength` were retired on 2026-08-17.

‼ **Why these three and not the two biggest sections:** `#24-codeorphans` and the 2026-07-27 doc
audit are **OPEN work with unfinished sub-items** — retiring live instructions into an archive is
how a project loses track of them.

- [x] `#24-huntreachproof` (original finding) — ‼‼ **TOP ITEM 2026-08-08. Only ONE counter rung has ever worked, and
      `#24-movepoolcounters` widened the set with destinations the bot CANNOT TRAVEL TO.**
      Batch `20260808-095721`, conversion by target:
      | species | hunts | caught |
      |---|---|---|
      | **Machop @ FIERY_PATH** | 5 | **5 (100%)** |
      | Wingull / Nincada / Numel / Oddish / Baltoy / Taillow | 28 | **0** |
      `could not reach` **72**, `Could not find a path` **45**, `hunt found nothing` **0** —
      **travel failures, not catch failures.** Hunts 18 → 33 while catches fell 7 → 5.
      **ROOT CAUSE:** `huntable = reachable AND hunt_tile is not None`, and **`reachable` is a
      PREDICTION** (`_counter_area_allowed`'s hop budget + region oracle) that is wrong for 28 of
      33. `hunt_ground_tile`'s whitelist is evidence-backed for STANDING AND SPINNING, but its
      `TRAINING_GRASS` entries were two-way swept **for training, from training anchors** — not
      for a hunt firing from a boss anchor. `HUNTING_GROUNDS` — the table that encodes *driven,
      reach-and-leave* evidence — still has **one** entry, FIERY_PATH, and that is the only rung
      that converts. Not a coincidence.
      ‼ **Plausibly WORSE than before:** Winona used to stop immediately; now she burns a
      cross-Hoenn trek and then stops, and the hunt is bounded to ONE attempt per boss per run —
      so a failed destination costs the boss, not a trek. `no super-effective answer` rose from
      10 of 14 (71%) to **19 of 23 (83%)** of non-finishes. (Finish 41.7% → 25.8% is z = −1.24,
      NOT resolvable — the concern rests on the conversion counters, not on the rate.)
      **FIX:** require DRIVEN evidence from the anchor the hunt fires from — the bar
      `HUNTING_GROUNDS` already sets and FIERY_PATH already meets. Either sweep candidate grounds
      from real boss anchors and add them, or have the ladder demote a destination that has
      already failed to travel. ‼ Do NOT simply widen `HUNTING_GROUNDS` on a guess — its whole
      value is that every entry is measured.

- [x] HISTORY — `#24-teachpathrace` (original report) — **found 2026-08-07 by the `#24-hmteachloop` telemetry.**
      2 failures in 24 teaches (~8%) in `20260807-102552`, both on **Surf**, both fatal
      (`not-learned-after-ride:hard-cap`, the full 9,000 frames, Surf never learned):
      ```
      TEACH EXIT reason=ride:hard-cap stall_peak=82 post_select=instant-learn move=Surf
        slot=4 replace_slot=1 frame=8999 tasks=['ListMenuDummyTask',
        'Task_BagMenu_HandleInput', 'Task_ScrollIndicatorArrowPair']
        moves=['Take Down', 'Mud Shot', 'Rock Smash', 'Muddy Water']
      ```
      ‼ **`post_select=instant-learn` on a mon with FOUR moves is a contradiction, and that is
      the smoking gun.** The post-select loop (`early_game.py`, `for _f in range(900)`) breaks on
      `"Task_PartyMenuReplaceMove" in t or "Task_HandleChooseMonInput" in t` and calls it the
      instant-learn path — but `Task_HandleChooseMonInput` is STILL UP for a while after the mon
      is chosen, so it wins the race before `Task_ReplaceMoveYesNo` appears. The guarded
      `if "Task_ReplaceMoveYesNo" in _tasks():` block is then skipped entirely, the replace
      prompt is never answered, and the flow rides out the cap stuck in the BAG
      (`Task_BagMenu_HandleInput`). `stall_peak=82` confirms it was churning, not frozen.
      **FIX SHAPE:** the instant-learn break must require positive evidence of a FREE SLOT (or of
      the move actually being known), not the mere presence of the party-menu task — a task that
      is present on BOTH paths cannot discriminate between them.
      ‼ **Pre-existing, not introduced:** that loop is untouched by the 2026-08-07 fix. It was
      invisible before because nothing logged which exit fired, and it was being absorbed into
      the "7/8/9/4 teach failures" that four budget rounds chased.

- [x] HISTORY — `#24-teachmsgstall` (original characterisation) — **NEW 2026-08-07, THIRD teach bug.**
      All **9** teach failures in batch `20260807-160545` share one signature:
      ```
      tasks=['ListMenuDummyTask', 'Task_ContinueTaskAfterMessagePrints']   9 of 9, identical
      move=Surf                                                            9 of 9
      post_select=exhausted (7)   |   post_select=replace-prompt (2)
      ```
      A message never completes with the bag list still up, so the teach rides out the full
      9,000-frame cap and Surf is never learned.
      ‼ **`post_select` DOES NOT MATTER** — the two that reached the replace prompt died in the
      same place. That rules out path selection as the cause, and rules out `#24-teachpathrace`
      (my 2026-08-07 fix) as the culprit: it changed the shape (`instant-learn` → `exhausted`)
      because it stopped the flow mislabelling the path, which **revealed** this stall rather
      than creating it.
      ‼ 4 → 9 failures is **z = +1.05, NOT resolvable** — do not call it a regression. Teach
      SUCCESSES rose 33 → 38 over the same window.
      **NEXT STEP:** reproduce with `--driver teachfull TEACH_ITEM=HM03` on a save whose party
      matches the failing shape (a 4-move Marshtomp-line mon that already knows Rock Smash), then
      instrument what `Task_ContinueTaskAfterMessagePrints` is waiting on. Every failure is Surf
      and every mon already carries an HM — worth checking whether the HM-slot exclusion in
      `replace_slot` picking leaves no legal choice and the game silently refuses.

---

## Archived from `03-PUNCH-LIST.md`

Closed history, retired to keep `03-PUNCH-LIST.md` inside its 3600-line R3 budget. `#24-whiteoutloop` shipped BOTH parts on 2026-08-07; this block is its part-2 narrative, kept for its reasoning and never a live instruction. ⭐ First real use of `archive_doc_block.py`, the tool written earlier the same day after two hand-rolled archivings went wrong in opposite directions.

- [x] HISTORY — `#24-whiteoutloop` (part 2) — **the hard plateau.**
      Confirmed as the **#1 end reason** of batch `20260807-102552`: *"too many whiteout
      recoveries in a row"* = **4 of 14 non-finishes (29%)**.
      **SHIPPED — the hard plateau.** `_boss_plan_is_hopeless` demanded BOTH a KO plateau AND
      "no credible super-effective answer", so an UNDERLEVELLED party holding a good move on
      paper never gave up (measured worst case: PETALBURG_CITY_GYM, **32 consecutive losses**,
      KOs stuck at 2-3 throughout). The type-chart answer test is a **prediction**; a long flat
      KO series is a **measurement**. Past `HARD_PLATEAU_LOSS_THRESHOLD = 12` the measurement now
      wins and the existing counter/training escalation runs instead of another identical attempt.
      ‼ **Keyed on FLAT KOs across two six-attempt windows, never on attempt count** — that is
      what honours KI-26's record of a run that lost **13 times** at ROUTE110 and then reached
      Fortree. `repro_boss_plateau.py` cases 8-10 pin all three behaviours (fires on flat;
      **does NOT fire on a climbing run**; leaves the original no-answer path untouched); 1-7
      still pass unchanged.
      **STILL TO DO (part 1):** real `_prepare_for_fight` cfgs for **Flannery / Gym 4** and the
      **Route 110 rival**. They have none, so none of this machinery runs there at all — and
      they are **48% of all defeats** (1,079 / 2,236 over four batches) and top-4 in 4 of 4.
      ‼ Needs verified game facts (training grass tile, heal centre, ace types/level) — probe or
      decomp, never recall. The Route 110 rival's ace depends on the player's starter.

---

## Archived from `03-PUNCH-LIST.md`

Closed history, retired to keep `03-PUNCH-LIST.md` inside its 3600-line R3 budget. It is the 2026-08-07 DIAGNOSIS narrative for `#24-whiteoutloop`, whose fix shipped the same day; kept for its reasoning, never a live instruction.

- [x] HISTORY — `#24-whiteoutloop` (diagnosis) — **DIAGNOSED 2026-08-07 from stored logs. It is KI-26, generalised:
      uncapped boss re-attempts. Fix is specified and NOT yet implemented.**
      ‼ Measured NOT to be Mt. Pyre's: a run with 0 `MT. PYRE` mentions logged 3 whiteouts while
      heavy-Mt.-Pyre runs logged none. **The "show WHERE" ask is now answered** — every whiteout is
      preceded by `lost a battle at map (G,N) (defeat #K here; KO'd J of theirs first)`, so the
      map, the attempt ordinal and the progress signal were in the logs all along.
      * **48% of all defeats (1,079 / 2,236 across four batches) are at maps with NO
        `_prepare_for_fight` cfg** — ROUTE110 and LAVARIDGE_GYM (Flannery) are top-4 in 4 of 4.
      * **Re-attempting usually does not work:** of 53 sequences with ≥3 defeats at one map,
        the KO trend is **FLAT in 37, improving in 15, worse in 1**. Worst: 17 straight losses at
        Lavaridge with a constant `kos=[3]*17`; 32 straight at Petalburg.
      * `_boss_plan_is_hopeless` already has the right plateau test but demands **plateau AND no
        super-effective answer**, so an underlevelled party that HAS one never gives up.
      **FIX (2 parts, both deferred until the batch lands — never edit `sandbox-pokebot/` mid-batch):**
      1. Real `_prepare_for_fight` cfgs for Flannery and the Route 110 rival.
      2. A cfg-independent cap keyed on **flat KOs, not attempt count** — which is precisely what
         lets it honour KI-26's warning that a run losing 13 times still went on to reach Fortree.
      Full measurement + method in `05-KNOWN-ISSUES.md` KI-26.

---

## Archived from `03-PUNCH-LIST.md`

Closed history, retired to keep `03-PUNCH-LIST.md` inside its 3600-line R3 budget. ⭐ Fittingly, this block is itself a record of a WRONG STATED CAUSE being corrected — the same shape as the KI-90 correction made on the day it was archived. Kept verbatim for its reasoning; never a live instruction.

- [x] HISTORY — `#24-winonaground` (wrong-cause history) — ‼‼ **MY STATED CAUSE WAS WRONG.**
      I wrote that the huntable whitelist was `{FIERY_PATH, ROUTE116, ROUTE117, ROUTE102}` and
      contained no Rock/Electric/Ice ground. **False.** I grepped for named `*_TRAINING_GRASS =`
      CONSTANTS instead of reading the `TRAINING_GRASS` TABLE, which has **10 entries**:
      ROUTE101/102/103/111/115/116/117/**118**/119/121, plus FIERY_PATH from `HUNTING_GROUNDS`
      = **11 huntable grounds**.
      * **ROUTE118 (29,15) — Electrike, the named Winona answer — is ALREADY whitelisted.**
      * **ROUTE111 hosts Geodude (Ground/Rock, rate 100%, Lmax 20)** — a by-TYPE Rock answer to
        Winona that is already huntable.
      So there IS a candidate and there IS a swept ground. **Do NOT sweep ROUTE118; it is done.**
      The failure message is `no huntable counter candidate (**nothing reachable** with a proven
      spin tile)` — the rejection is downstream of the whitelist, in reachability or in
      `best_huntable`'s cost/level gates. Prior evidence points the same way: 2026-07-30 measured
      `Electrike @ ROUTE118 (29,15) — navigation FAILED, 255 frames`.
      **NEXT PROBE:** call `counter_plan.huntable_candidates()` for Winona's needed types from a
      REAL pre-Winona anchor and log the rejection reason PER CANDIDATE. Do not guess which gate
      it is — four gates can produce this one message.
      ‼ **The lesson (3rd time this session): I read a proxy for the data instead of the data.**
      Same class as grepping a gitignored tree and as reading the profile dirs with a date glob.

---

## Archived from `03-PUNCH-LIST.md`

Closed history, retired to keep `03-PUNCH-LIST.md` inside its 3600-line R3 budget. Fixed the day it was found; kept verbatim for its reasoning, never a live instruction.

- [x] HISTORY — `#24-counterdesertgate` (original diagnosis) — **NEW 2026-08-07, ROOT-CAUSED.**
      Batch `20260807-200030`: **7 Baltoy hunts to ROUTE111 (25,55), 0 caught.**
      `AREA_ITEM_PREREQ = {ROUTE111: "Go-Goggles"}` gates the desert, and
      **`counter_plan.py` references `AREA_ITEM_PREREQ` ZERO times** — it consults only
      `AREA_PREREQ`. The planner offers the desert tile (which sits NORTH of the goggles gate),
      the bot walks cross-Hoenn, cannot enter, and spins wherever it stopped.
      ‼ **PRE-EXISTING.** The gate exists in `_counter_area_allowed` behind
      `POKEBOT_AREA_ITEM_GATE` and is **OFF BY DEFAULT since 2026-08-04** ("THIS GATE COST MORE
      THAN IT SAVED", measured). `#24-movepoolcounters` only made it load-bearing — before it,
      ROUTE111 never won Winona's ranking.
      ‼ **DO NOT just flip `POKEBOT_AREA_ITEM_GATE` on.** That was measured and rejected for
      TRAINING, where a bad pick costs one trek. A COUNTER HUNT gets **one attempt per boss per
      run**, so a bad pick costs the boss. **Fix `find_counter_candidates` to honour
      `AREA_ITEM_PREREQ` for its own destination choice only** — that demotes Baltoy@ROUTE111
      below Slugma@FIERY_PATH, a ground already proven by Norman's 6-of-7 catch rate.
      **Acceptance:** `counter hunt — … FIERY_PATH … Slugma` appears and `CAUGHT Slugma` > 0,
      with `CAUGHT Machop` (control) unchanged.

---

## Archived from `03-PUNCH-LIST.md`

Closed 2026-09-05. Archived the same day to keep 03-PUNCH-LIST.md under its lint_docs R3 budget while step 4 of #24-ch23chain was respecified.

### ✅ `#24-icebeamteach` — **CLOSED 2026-09-05: WAILORD KNOWS ICE BEAM.** ⛔ DO NOT REOPEN.

`--driver ch24teachice` on `post_icebeam.ss1`: `ACCEPTANCE: PASS`, `LANDED ['Wailord:Ice Beam']`,
`wrong=[]`, `missing=[]`, `back_in_overworld=True`, `whiteouts=0`. Wailord's moves went
`['Dive','Surf','Water Spout','Waterfall']` → `['Dive','Surf','Ice Beam','Waterfall']`.
⭐ **A CLEAN A/B: same driver, same fixture, ONE line changed** — before the fix the cursor sat on
HM08 and the game refused; after it, the teach lands. Nothing else was touched.

**STATUS: CLOSED (was: OPEN — ROOT-CAUSED 2026-09-05).**
Reproduce with `--driver ch24teachice --frames 6000` on `post_icebeam.ss1` (~20 seconds).
‼ Use a SMALL `--frames`: the driver reaches its verdict by ~f574 and then
idles to the cap in Manual mode, so `--frames 40000` wastes twelve minutes per attempt.

⛔⛔ **ROOT CAUSE — `scroll_to_item_in_bag` RETURNS SUCCESS WITH THE CURSOR ON THE WRONG ITEM.**
MEASURED in ONE run once the right instrument was fitted:
```
[TEACH-CURSOR] after scroll_to_item_in_bag(TM13): pocket=2 slot=13 -> HM08
[TEACH-ITEM]   TM/HM pocket order = ['TM03','TM04','TM08','TM13',...,'HM07','HM08']
[TEACH-SAID]   0: 'DIVER already knows DIVE.'
```
The bot was using **HM08 Dive** on Wailord (nickname DIVER) the whole time. The game refused, bounced
to the bag, consumed nothing. Upstream scrolls to a slot number from `first_slot_index_for()`, and
for TM13 that is not the slot the on-screen cursor counts.
⭐ **WHY IT NEVER BIT BEFORE:** five earlier teaches (Aerial Ace, Facade, Strength, Rock Smash, Fly)
used items whose two indices COINCIDE. TM13 is the first item acquired out of that order.
⇒ **A helper that has worked five times is not verified, only unmeasured.**

**THE FIX, SHIPPED (`pokemon_league.py::scroll_to_tm_verified`):** call upstream, then READ the cursor
back out of `gBagPosition`, correct it closed-loop and BOUNDED against `get_item_bag().tms_hms`, and
**RAISE rather than press A on an unverified cursor** (a Gen-3 TM is single-use).
⛔ Upstream `modules/menuing.py` is left ALONE — a CASE-BY-CASE call for THIS defect (shared hot path; the cheaper route existed), ⛔ **not a ruling**: *(this read "same ruling as `KI-88`" until 2026-09-05; no such ruling exists — see `06-DECISIONS-LOG.md` 2026-09-05)*.

**ALSO MEASURED, so do not re-derive:** the party cursor lands correctly
(`reads=[2,2,2,2,2,2,2,3,3,3]`, mon under cursor = Wailord); `can_learn_tm_hm(TM13)` is True;
⚠ Wailord's ONLY forgettable slot is **Water Spout** — Dive/Surf/Waterfall are HMs and the game
refuses to forget an HM ⇒ **the swap is a REAL trade**, not a free slot.

‼ **THE LESSON, AND IT COST SIX DRIVES:** every one of those six diagnoses was about the PARTY menu,
downstream of an item selection that was wrong from the first frame. The item side had been
"verified" by printing the pocket's CONTENTS — which is not the cursor. ⇒ ⭐ **A CANDIDATE IS NOT AN
ATTEMPT: read what A will actually act on.**

*(superseded 2026-09-05 — the block that stood here was this item's PRE-SHIPMENT plan, left behind
when the header above was replaced. It said "STATUS: OPEN... this is the next build" and gave a route
"decomp-traced, NOT walked". Both are done. Retired rather than kept, because a route plan under a
CLOSED header is an instruction to redo finished work; the route AS BUILT is in the entry above and
in `07-CHANGELOG.md` 2026-09-05. Two things from it are still TRUE and are kept here:)*

**WHY THIS ITEM EXISTED (the rationale, still the justification for the whole §Ch24 TM plan).** Drake
is 4/5 dragon-ish and carries **zero Ice moves**; Wailord takes only 22-56% from his whole team. With
Ice Beam, Wailord does **Flygon 88% · Salamence 73% · Altaria 71% · Shelgon 71%**. ⭐ **Flygon has
LEVITATE**, so Ice is the ONLY super-effective type that reaches it. Cost: **₽0**.
⚠ **STILL A PREDICTION — THE BOT HAS NEVER FOUGHT DRAKE.** Ice Beam is now TAUGHT; that changes the
inputs to the analysis, not its status as an analysis.

⚠⚠ **WHAT THIS DOES NOT FIX, AND IT IS THE NEXT TM QUESTION: WALLACE IS STILL A LOSS.** Milotic's
Recover heals 98/turn against our best hit of 74 — Ice Beam does not touch that. The candidate answer
is SolarBeam + Sunny Day (TM22 / TM11, both also FREE pickups). ⛔ NOT scheduled and NOT de-risked:
neither flag has been probed and neither route has been walked. See
`ai-research-notes/2026-09-04-ch24-MOVESET-AND-TM-PLAN.md` §6.
---

---

## Archived from `05-KNOWN-ISSUES.md`

Fixed 2026-07-30. Archived 2026-09-06 to keep 05-KNOWN-ISSUES.md under its lint_docs R3 budget after KI-91 and KI-92 were filed. Its diagnosis tables remain valuable - three later index-space bugs (KI-18, KI-66, and #24-faintchooser-fourthspace) share its shape.

## KI-34 — the after-faint chooser LIVELOCKS when its candidate filter and the game disagree (opened 2026-07-29, severity: HIGH — ✅ **FIXED 2026-07-30, and the index-space mapping is IN THE CODE TODAY**: `battle_handler.py:676-680` defines `_to_menu_order()` and `:683` builds `alive_slots_menu`. ⚠ **The diagnosis tables below are the PRE-FIX picture, kept for the reasoning** — read them as history, not as today's code)
- **User report:** *"noticed an error with I think p2 or p3 where they were training with a
  skitty and an Abra in the team in a double battle but had issues selecting the Abra."*
  Confirmed in P2 of bundle `20260729-172342`, and **this is the first production catch by the
  KI-32 in-battle stall fix** — without it the log would again have been silent.
- **Evidence (71 in-battle STUCK dumps, f652,238 → f862,238 = 210,000 frames):**
  ```
  game_state=3 (PARTY_MENU)  controllable=False
  battle: active=True  instr=BattleScript_FaintedMonTryChoose
  battle_text='MARSHTOMP fainted!'
  party=['Marshtomp L27 0/76', 'Skitty L15 41/41', 'Poochyena L12 0/32', 'Abra L7 21/21']
  -> handle_battle @ battle_handler.py:264
  -> handle_fainted_pokemon @ battle_handler.py:532 / :537
  ```
- **It is a LIVELOCK, not a hang.** Across all 71 dumps the **party never changes** — no
  replacement is ever sent out — but the menu state *cycles*:
  `Task_ReturnToChooseMonAfterText + Task_PrintAndWaitForText` ×57,
  `Task_HandleChooseMonInput` ×10, `Task_HandleSelectionMenuInput` ×3, and the stack alternates
  between the two `yield` sites at `:532`/`:537`. The bot is pressing buttons and the game is
  responding; the *outcome* never occurs.
- **‼ Its 6,000-frame bound does not bound anything.** `handle_fainted_pokemon` ends with
  `if frames > 6000: return` — but the dispatcher re-enters it with `frames = 0`.
  210,000 / 6,000 ≈ **35 re-entries**. This is verbatim the playbook rule
  *"bound the OUTCOME, not just the frames — a bounded loop re-entered by its dispatcher is
  still infinite."*
- **Two candidate mechanisms — NOT yet distinguished, and the dump cannot separate them:**
  1. **`alive_slots` is EMPTY.** If this is a DOUBLE battle whose actives are Skitty(1) and
     Abra(3), then `_on_field = {1,3}`; slots 0 and 2 are fainted, so the KI-18 exclusion
     leaves **no candidate at all**. Every branch then either dismisses text or walks the
     cursor, and A is never pressed — matching "issues selecting the Abra" exactly.
  2. **Text-branch starvation.** The `Task_PrintAndWaitForText` /
     `Task_ReturnToChooseMonAfterText` branch is checked FIRST and was active in 57 of 71
     samples, so it can starve the `cursor not in alive_slots → "Down"` branch: A dismisses
     the text, the cursor is still on a fainted slot, A re-selects it, the text returns.
     KI-17's `post_gap = 24` was meant to prevent this; 24 frames may be insufficient.
- **‼ INSTRUMENTED 2026-07-29 — the next occurrence will name its own cause.**
  `handle_fainted_pokemon` now emits, via `debug_logger.event(category="BATTLE")`:
  * on entry — `[FAINT-CHOOSER] alive_slots=… on_field=… party=[(slot, species, hp)…]`, with an
    explicit **`‼ NO ELIGIBLE REPLACEMENT — cannot succeed`** when `alive_slots` is empty. That
    one line separates mechanism (a) from (b).
  * on give-up — `[FAINT-CHOOSER] GAVE UP after N frames … presses={…} cursors_seen=[…]`.
    The press histogram is what distinguishes *pressing the wrong thing* from *pressing
    nothing* (playbook §7); the state trace alone cannot.
  Counted per iteration, emitted once, so it cannot flood a log.
- **‼ DIAGNOSED 2026-07-30 by that instrumentation — mechanism (b), and (a) is REFUTED.**
  Overnight batch `20260730-062818`, 7,539 chooser entries and 3,978 give-ups:
  * **`alive_slots` was NEVER empty — 0 of 7,539.** So the KI-18 on-field exclusion is NOT
    starving the candidate set. **Mechanism (a) is dead.**
  * **`presses={'A': 289}` — A and NOTHING ELSE**, every time. No `Down`, no `B`, no `(none)`.
  * **`cursors_seen=[1]` — a SINGLE position for the whole 6,002 frames**, and that position
    **is in `alive_slots`**. The cursor is parked on a living, eligible mon.
  So: the cursor is already correct, the bot presses A ~289 times, and the menu never advances.
  It is not choosing wrongly and not failing to find a candidate — **its A-presses are not
  being accepted**, and the printer-task branch (`Task_PrintAndWaitForText` /
  `Task_ReturnToChooseMonAfterText`) keeps re-arming, so it never reaches any other branch.
  KI-17's `post_gap = 24` is insufficient for this case.
- **Where:** `MAUVILLE CITY(10,0)` — the Mauville Gym — in **3,975 of 3,975** located give-ups,
  and `on_field` carries TWO slots, i.e. a **DOUBLE battle**. Exactly the user's original report.
- **‼ Scale, and why it matters more than it looks:** P3 alone burned **23,857,950 frames** in
  3,975 give-ups (**~7.8 complete runs' worth**) — and P3 completed only **5 badge-earning runs
  overnight against P2's 19.** The livelock, not difficulty, is what cost that lane its night.
  P1 1, P2 0, P4 2 — it is **99.9% concentrated in P3/Treecko**, because Treecko has no Ground
  answer to Wattson, loses repeatedly, and every loss is another after-faint chooser roll.
- **‼ ROOT CAUSE FOUND 2026-07-30 — USER OBSERVATION + CODE, and it invalidates my reading of
  my own instrumentation.** The user, watching the screen: *"the bot is selecting a live pokemon
  in the pokeparty, but its one that is already in the field (cannot select an already active
  pokemon to swap out)"*.
  That is impossible if `alive_slots` is correct — and it is correct, **in its own index space.
  The comparison is not.** There are TWO party index spaces:
  * **regular party order** — what `get_party()` returns;
  * **in-battle party-menu order** — what the party MENU uses, which diverges from the regular
    order once mons have been switched in and out. `BattleState.map_battle_party_index()`
    (`battle_state.py:332`) exists solely to convert between them, and its docstring says so:
    *"the order in the party menu might be different from what `get_party()` returns so we'd
    have to scroll to a different index."*

  ⛔ **PRE-FIX PICTURE (2026-07-29). `handle_fainted_pokemon` *USED* BOTH SPACES AND COMPARED THEM
  DIRECTLY.** ✅ It no longer does: `:676-680` `_to_menu_order()` and `:683` `alive_slots_menu`
  now convert party-order → menu-order before any comparison. Line numbers below are TODAY's
  homes for those values, re-derived 2026-08-16; the *mixed-space* row is what got fixed:
  | line | value | space |
  |---|---|---|
  | `battle_handler.py:610` | `party_in_menu = get_party()` | **regular** |
  | `battle_handler.py:633` | `alive_slots` built by enumerating that party | **regular** |
  | `battle_handler.py:724` | `cursor = get_party_menu_cursor_pos(...)["slot_id"]` (reads `gPartyMenu.slotId`) | **in-battle menu** |
  | `battle_handler.py:667` (comment) / `:683` (the fix) | *was* `cursor in alive_slots` raw; **now** `alive_slots_menu = {_to_menu_order(i) for i in alive_slots}` | ✅ **was ‼ mixed — now MAPPED** |

  ‼ **The same function already knows better**: its PRIMARY path maps correctly at
  `battle_handler.py:443-444` (`if index_needs_mapping: new_lead_index =
  battle_state.map_battle_party_index(new_lead_index)`). Only the RECOVERY SWEEP — the loop that
  actually wedges — skips the mapping.
- **Why this explains every observation at once:** once the orders diverge (i.e. after switches
  and faints — exactly a double battle late in a fight), menu-slot *n* is a different mon than
  party-slot *n*. The sweep concludes "cursor is on a living, eligible mon", presses A, and the
  game **refuses because that mon is on the field** — which re-arms
  `Task_PrintAndWaitForText`, so the loop takes the dismiss-text branch again. Hence exactly
  what was logged: `presses={'A': 289}`, **cursor static**, and a `cursor in alive_slots` test
  that was TRUE and meaningless. It is worst in P3 because that lane faints most, so its orders
  diverge most.
- **‼ LESSON (logged in 08-MISTAKES):** I instrumented the VALUES but not their UNITS. Two
  integers from different coordinate systems compared as if interchangeable — and the log I
  added made the wrong comparison look verified.
- **FIXED 2026-07-30.** Two changes in `modules/battle_handler.py`:
  1. **Convert before comparing.** `alive_slots_menu = {map_battle_party_index(i) ...}` and every
     cursor test now uses the MENU-order set — matching what the primary path and
     `battle_action_selection.py:124/199` already did. The entry log prints BOTH sets with their
     units and flags `[orders DIVERGE]`.
  2. **Bound the OUTCOME, not the frames.** `FAINT_CHOOSER_GIVEUP_LIMIT = 3` per battle
     (counter reset in `handle_battle`); on exceeding it the run gets a RECOVERABLE derail via
     `battle_fault.request_mode_recovery()`, which makes `handle_battle` and `BattleListener`
     short-circuit so `StoryMode` claims it and the endless loop starts the next run.
     It never RAISES from battle code — on this flat controller stack that would reach
     `main_loop` and force Manual.
- **Repro:** `tools/story-dev/repro_faint_chooser_index_space.py` — builds a diverged battle
  party order and proves the OLD test calls menu slot 1 selectable while the NEW test correctly
  rejects it as on-field: the user's observation, reproduced as arithmetic.

---

## Archived from `05-KNOWN-ISSUES.md`

Fixed 2026-07-31. Archived 2026-09-06 to keep 05-KNOWN-ISSUES.md under its lint_docs R3 budget after KI-91, KI-92 and KI-93 were filed.

## KI-41 — The Mauville→Route 112 corridor is sealed by a ROCK SMASH rock the planner treats as permanent (2026-07-31)  — ✅ **FIXED 2026-07-31, same day** (`#24-smashroute`; see this entry's own `### ‼ KI-41 — FIXED` block. Header marker added 2026-08-22, PASS 5).

**Measured** from `rocksmash_taught.ss1` (Mauville 32,15), `probe_journey_walls.py`:
ROUTE111 column-by-column reachability, y from 139 (south, next to Mauville) northward —

```
x=17  ##########.........######.....#####..#............   last reachable y=102
x=18  #########..........#######....#####..#............   last reachable y=102, y=101 BLOCKED
x=19  ##########......#..##..####...#########...........   last reachable y=101, y=100 BLOCKED
x=20  ...####.###.#..##.###..##.###.#########...........   last reachable y=101, y=100 BLOCKED
```

The intermittent bands further south are the corridor's **one-way ledges** (they only
descend, so northbound approach is fragmented); the hard floor at **y≈100–101** is the
twin-rocks choke. `modules/story/early_game.py`'s `travel_lavaridge_to_petalburg` docstring
already names it: *"smash the twin-rocks choke from the NORTH side … column 18 needs only the
(18,101) rock"*, and notes the rocks **RESPAWN on map reload**.

**Consequences**
* ROUTE112 is **0/76** sampled tiles reachable from Mauville. FIERY_PATH's only two doors are
  ROUTE112 (11,36) and (22,10), so **Fiery Path is unreachable from Mauville** until that
  rock is smashed — and Fiery Path's Machop is the counter `#24-counters` names for Norman.
* The story only gets past it because `travel_to_fallarbor` / `travel_lavaridge_to_petalburg`
  hand-code a `_smash_rock` at exactly that coordinate. **Nothing generic does.**

**Why the planner cannot see it.** `calculate_path` models a Rock-Smash rock via
`dynamic_collision_flag` / `dynamic_object_id`, i.e. as an obstacle that *is* impassable right
now. That is CORRECT — the bot genuinely cannot walk through it — but it means every generic
"can I get there?" answer is a NO that a single field-move would turn into a YES.

---

## Archived from `05-KNOWN-ISSUES.md`

Fixed 2026-09-05, promoted 2026-09-06. Archived the same day to keep 05-KNOWN-ISSUES.md under its lint_docs R3 budget after KI-91/92/93 were filed. Its both-absent branch note and the sibling-controller containment observation are preserved verbatim in the archive.

## `KI-90` — ⛔⛔ IN A **DOUBLE BATTLE** WITH ONE OPPONENT SLOT ABSENT, THE BOT AIMS AT THE EMPTY SLOT, RAISES, AND THE RUN HANGS (2026-09-05, MEASURED; ✅ REPRODUCED by gate #38; ‼ root cause CORRECTED the same day; ✅✅ **FIXED the same day at the checkpoint — gate #38 SELF-RETIRED**; ✅ PROMOTED to `custom-pokebot/` 2026-09-06, user-approved, and re-verified against `--build custom`)

**Severity: HIGH, and it is a HANG, not a crash.** The exception unwinds the whole controller stack,
the bot drops to Manual *inside a battle nothing is driving*, and the run sits until the watchdog
kills it. MEASURED: 20,000 frames of no progress, then `HANG CONFIRMED`.

**2026-09-05, first end-to-end §Ch23 chapter drive, frame 66693:**
```
RuntimeError: Cannot attack the left-side opponent Pokemon because there isn't one.
  modules/battle_action_selection.py:499 in battle_action_use_move
  <- battle_handler.py:294 _watch  <- _listeners.py:219 BattleListener.fight
f66695: CONTROLLER -> <none>   (state=BATTLE)      f87506: HANG CONFIRMED
```

⛔ **THE MECHANISM, VERIFIED — AND IT IS A PERSISTENT STATE, NOT A TIMING RACE.**
* `opponent.left_battler is None` **iff** bit 1 of `gAbsentBattlerFlags` is set
  (`modules/battle_state.py:396-402`) — there is no other path to `None`.
* That byte is a **FROZEN SNAPSHOT** (`battle_state.py:245`, read at `:821`), captured at
  `battle_action_selection.py:23`/`:247`, i.e. **before** the A-press loop. Nothing during the
  presses can change it.
* `HasNoMonsToSwitch` returns FALSE unconditionally when `BATTLE_TYPE_DOUBLE` is off
  (`src/battle_util.c:2271`), and gates every writer of that byte.
  ⇒ ⭐ **THE RAISE ITSELF PROVES THE BATTLE WAS A DOUBLE**, with the opponent's LEFT trainer out of
  switchable Pokémon — a state that persists for the rest of the fight.
* Our code hardcodes `target_index = 1` and raises; **the game handles this case**, defaulting the
  cursor to OPPONENT_RIGHT (`src/battle_controller_player.c:535-536`).
* ‼ Victory Road makes doubles from face-to-face `trainerbattle_single` pairs
  (`gNoOfApproachingTrainers == 2`) — no double-battle trainer flag required.

⛔⛔ **AND IT IS UNRECOVERABLE FOR A REASON THIS ENTRY FIRST GOT WRONG.** It is NOT that the raise is a
bare `RuntimeError` where recoveries catch `BotModeError`. `handle_battle` is only ever reached from
`BattleListener`, a **SIBLING** generator on the controller stack — so from that position **every**
exception, `BotModeError` INCLUDED, unwinds to `modules/main.py`, where BOTH `except BotModeError`
(`:151-153`) and the bare `except Exception` (`:158`) call `set_manual_mode()`.
⇒ ⭐ **A RECOVERY LOOP ONLY CATCHES WHAT REACHES ITS OWN STACK.** Changing the exception type would
NOT make this recoverable — which is exactly the fix the old wording invited.

⛔ **NOT OURS, AND NOT NEW.** The identical raise is in an archived live run of **2026-07-22**
(`tools/story-dev/livetest-runs/archive/20260722-204645/run01/run.log:18254`), three weeks before our
`_fight_on` KI-52 fork landed (`72e938d2`, 2026-08-11). Our fork may raise exposure; it did not create
this. ‼ **BUT NOT UNTOUCHED EITHER:** `story_mode.py:261`'s own comment cites *"batch runs 01+03, 2026-07-22, both at the same trainer pair once one opponent went down"* — that override was WRITTEN to fix this raise, and the 2026-09-05 run died anyway. ⇒ the guard exists; the surviving hole is its both-not-alive FALL-THROUGH. ⚠ Which producer fired on 2026-09-05 is **NOT established**.

⛔ **BLAST RADIUS: EVERY CHAPTER'S BATTLES**, and §Ch24 hardest — five consecutive fights, no nurse.
⚠ **NOT MEASURED: how OFTEN it fires.** Two occurrences seven weeks apart is an existence proof, not
a rate. It is a CORRECTNESS question, so the instrument is a repro, never a batch.

✅✅ **FIXED 2026-09-05 (`06-DECISIONS-LOG.md` same day).** `battle_action_use_move` now sets `target_index = 3` — the RIGHT opponent — when the left slot is absent, matching the game (`src/battle_controller_player.c:535-536`) and this module's own `active_battler` rule (`battle_state.py:418-429`); it raises only if BOTH slots are absent. Gate #38 SELF-RETIRED, having verified the committed slot is **3** rather than merely that the raise stopped. ⚠ Sandbox only — promotion to `custom-pokebot/` is the USER's call. ⚠ The both-absent raise is unchanged and would still hang if reached (believed unreachable, NOT traced). *(superseded:)* **NOT FIXED YET — and NOT because of a ruling.** ⛔ This entry used to say "shared upstream; same ruling as `KI-83`/`KI-88`/`KI-89`". **That ruling does not exist** (`06-DECISIONS-LOG.md` 2026-09-05); we have modified this file 8 times, including a hang fix. *(that sentence read "It is unfixed because the fix is not yet DECIDED" — the fix WAS decided and written the same day; see the ✅✅ line above.)* Tracked as `#24-ch23chain`.
✅ **REPRODUCED 2026-09-05 — `tools/story-dev/repro_ki90_absent_left_slot.py` (gate #38).**
Three arms, in-process, milliseconds, against a REAL `BattleState` and the REAL
`battle_action_use_move` (what is real vs stubbed, and why, is in that file's own docstring):
```
ARM A  absent LEFT slot + UseMove         -> RuntimeError   (the defect)
ARM B  no absent flag  + UseMove          -> no raise       (⇒ the FLAG is the cause)
ARM C  absent LEFT slot + RIGHT-targeted  -> no raise       (⇒ the TARGET is the cause)
```
⭐ **IT SELF-RETIRES** (prints `SELF-RETIRED`, exits 0) if the raise disappears while its
discriminator still passes — so this gate cannot punish the fix. Both directions fault-proven.
📦 Rationale + rejected alternatives: `06-DECISIONS-LOG.md` 2026-09-05.

⛔ **Left-absent ALONE IS VACUOUS** — `story_mode.py:261-313` already aims RIGHT when the right opponent is alive, so that arm runs GREEN and reads as "does not reproduce". The raise is the FALL-THROUGH: left absent **AND** right also `hp == 0` in the same frozen snapshot. ‼ COMPUTE THE DISCRIMINATOR (print the `TurnAction` the strategy returns) BEFORE driving anything.
📌 **The full repro plan — the pinned fixture, the two trainer pairs, the KO count and the three left-hardcoded producers — lives in `03-PUNCH-LIST.md` `#24-ch23chain`**, which is where work is tracked; this entry describes the DEFECT, not the task.
Candidate fix (UNVERIFIED — gate #38 now exists to judge it): fall back to the RIGHT opponent when the left is
absent, as `HandleInputChooseMove` already does.

📦 Full evidence chain, the forensics, and a write-up of the refuted first diagnosis:
`ai-research-notes/2026-09-05-ki90-DOUBLE-BATTLE-ABSENT-SLOT.md`.

---

## Archived from `05-KNOWN-ISSUES.md`

Fixed 2026-07-30, follow-up still noted in the body. Archived 2026-09-06 to keep 05-KNOWN-ISSUES.md under its lint_docs R3 budget after KI-91/92/93 were filed and KI-93 grew with the retraction of its false elimination verdicts.

## KI-37 — a listener above the mode can STARVE it, so a handed-over battle fault is never claimed (opened 2026-07-30, severity: HIGH — CAUSED BY THE KI-34 FIX)  — ✅ **FIXED 2026-07-30** (see the ✅ bullet in this entry's body; header marker added 2026-08-22, PASS 5). ⚠ A follow-up remains open — read the body.
- **Symptom:** user log `20260730-081347` (`Story (DEBUG - RESET)`, build `4f1e02f9`).
  `handle_fainted_pokemon` did its job — 3 give-ups, then a correct hand-over at f1,797,401:
  `[FAINT-CHOOSER] handing a recoverable derail to the mode`. **Nothing claimed it.** The run
  then sat at `state=3 controllable=False` on ROUTE 117 for **1,182,000 frames** until the user
  stopped it by hand. KI-36's 60,000-frame net ALSO fired and was ALSO unclaimed.
- **Contrast, same build, sibling log `20260730-074518` (`ENDLESS RESET`):** the identical
  hand-over was claimed **one frame later** — `f902223 [STORY] DERAIL #1: Story: battle handler
  gave up — after-faint chooser could not send a mon out after 3 attempts (KI-34)`. So the
  channel works; something specific starved the mode in the other run.
- **Cause.** `TrainerApproachListener.handle_trainer_approach` was:
  ```python
  while get_global_script_context().is_active:
      context.emulator.press_button("B")
      yield
  ```
  An **unbounded loop with no fault check**. When a battle wedges, the trainer script never
  clears, so this listener sits on TOP of the controller stack pressing B for ever — and the
  MODE, the only thing that can consume the fault and derail, is never advanced. The stack at
  the wedge was `['StoryDebugResetMode.run', 'TrainerApproachListener.handle_trainer_approach']`
  with **no battle handler at all**: the fault had already short-circuited it, exactly as
  designed.
- **‼ `BattleListener` ALREADY HAD THIS EXACT GUARD**, ~110 lines above in the same file, with a
  comment naming the identical hazard: *"this would press B forever while the MODE — the only
  thing that can recover — is starved of frames."* The sibling listener simply never mirrored
  it. Third instance of that shape (KI-18's driver, KI-34's recovery sweep, now this).
- **This is a deadlock the fix created**, and `battle_fault.py`'s own docstring predicted it:
  *"An unconsumed fault would be far worse than a Manual drop."*
- **✅ FIXED 2026-07-30:** `handle_trainer_approach` now returns when `battle_fault_pending()`,
  popping back to the mode. Asserted in `repro_faint_chooser_index_space.py`.
- **‼ FOLLOW-UP, STILL OPEN:** audit **every** listener that can sit above the mode for the same
  omission, and bound their loops. A per-frame, stack-independent recovery (KI-36's complete
  fix) would make this class impossible rather than requiring each listener to remember.

## `KI-93` — the three RETRACTED fix attempts (archived 2026-09-06)

⛔ **THESE VERDICTS ARE VOID.** They came from a diagnostic calling `debug_logger.log(...)` — a function that does not exist — inside a `try/except: pass`, so nothing was ever written and "fired zero times" meant "my logger never ran". Moved out of `05-KNOWN-ISSUES.md` for its R3 budget; kept because the ATTEMPTS are real history even though their conclusions are not.

*(The untested table follows, kept for the record — ⛔ its verdicts are void:)*
**THREE FIX LOCATIONS TRIED (2026-09-06). ALL REVERTED. ⛔ Their "eliminated" verdicts are RETRACTED — see above.**
Each was implemented, driven, and disproved by instrumenting whether the code RAN — never by argument:
| # | where | why it is wrong |
|---|---|---|
| 1 | a one-shot fork AFTER the branch dispatch in `handle_battle_action_selection`, copying the shipped `BattleScript_SelectingMoveWithNoPP` precedent | fired **zero** times — that path is only reached when a decision COMMITS, and this loop never gets there |
| 2 | remember the refused slot at the caller's `HandleInputChooseMove` "press B" branch | fired **zero** times — instrumenting the outer `while` head showed it NEVER OBSERVES the refusal |
| 3 | bound the unbounded confirm loop in `battle_action_use_move` (`while ... press A`) and re-pick | the 90-press bound never fired: neither the re-pick nor its `BotModeError` appeared ⇒ execution is not in that loop either |
‼ All three PASSED the ordinary-case A/B byte-identically — which proves only that they were harmless.
⇒ ⭐ **A PASSING A/B PROVES HARMLESSNESS, NEVER EFFICACY.** Both questions must be asked separately.

**⭐⭐ THE ARTIFACT THAT SHOULD HAVE BEEN PULLED FIRST — THE GENERATOR STACK AT THE STALL:**
```
f18160 NO-PROGRESS x3000  sig=('BattleListener.fight','BATTLE','BattleScript_SelectingTormentedMove',…)
    gen -> isolate_inputs.<locals>.wrapper_function   @ _util_helper.py:10
    gen -> DebugUtil.track.<locals>.wrapper_function  @ debug.py:35
    gen -> BattleListener.fight                       @ _listeners.py:219
    gen -> DebugUtil.track.<locals>.wrapper_function  @ debug.py:35
    gen -> handle_battle                              @ battle_handler.py:373
    gen -> handle_battle.<locals>._watch              @ battle_handler.py:314
f18161 *** BotModeError -> Manual: KI-47 … 'handle_battle_action_selection' ran 3001 frames …
```
⇒ ⛔ **`handle_battle_action_selection` IS NOT ON THE STACK.** The deepest frame is `KI-47`'s own
`_watch` wrapper (`battle_handler.py:314`), which DRIVES the sub-handler rather than `yield from`-ing
it — so the sub-handler's own frame never appears, and every location I guessed at was downstream of a
frame the stack does not show.
⇒ ⭐ **START HERE NEXT TIME:** read `handle_battle.<locals>._watch` (`battle_handler.py:~314`) and
`handle_battle` (`:373`) and establish HOW the sub-handler is driven before choosing a fix site. The
stall signature and this stack are already captured in
`tools/story-dev/ki_ch24probe_ATTEMPT3.log`.

**⇒ THE METHOD LESSON, worth more than the three attempts:** the harness prints a full generator stack
on every no-progress event. **Pull it FIRST.** Three implement-drive-revert cycles cost real time and
each only excluded one candidate; the stack excludes all of them at once and names the frame to read.

**⛔ IMPLICATION FOR §Ch24 — THIS IS THE BLOCKER, NOT THE LEVEL GAP.** Planning so far has argued about
whether the party can WIN (the analysis says it dies at Glacia, fight 3). **This says the run cannot
finish fight 1 for reasons that have nothing to do with damage.** ⇒ ⭐ **fix the hang before spending
anything on levels or TMs** — a stronger party hangs in exactly the same place.

---

## Archived from `05-KNOWN-ISSUES.md`

MIXED status preserved. Archived 2026-09-06 for the R3 budget after KI-91/92/93/94 were filed. The CORRECTNESS half remains open under #24-ki76correctness.

## KI-76 — our CURRENT-SLIDE model ends the slide ONE TILE SHORT and in the WRONG MOVEMENT MODE, and it cannot see that a slide can END ON A WARP (2026-08-13 — ✅ SAFETY half FIXED, fault-tested, cap PROVEN; ⚠ CORRECTNESS half still UNFIXED and TRACKED as `#24-ki76correctness`, but ✅✅ **its ENDS-ON-A-WARP defect is CONFIRMED LIVE 2026-08-17** while the DISMOUNT defect remains analysis; ‼ **MIXED ARMING — the two defects are armed in DIFFERENT PLACES, see the 2026-08-17 blocks**)

> ⛔⛔ **THIS HEADER USED TO END *"so it is ARMED chiefly on Routes 132-134"*, ONE claim covering
> TWO defects. MEASURED 2026-08-17 (`probe_slide_endpoints.py`), that is half right and half
> BACKWARDS:** the **dismount** defect is armed **1,852** times ROM-wide and overwhelmingly on those
> routes (765/542/501) — but the **ends-on-a-warp** defect is armed **9** times and **ALL NINE ARE
> IN SEAFLOOR_CAVERN_ROOM6, ZERO on the routes.** A reader acting on the old header would have hunted
> the warp defect on the routes, where it does not exist. ‼ **A header covering two defects must
> state each one's status separately** — the P2 rule, applied to defects rather than to bullets.
> ✅ **The 512-step cap is no longer taken on faith:** production followed every cross-map chain on
> ONE shared budget, the cap NEVER fired, nothing cycles, and the longest chain is **77** steps
> (margin **6.6x**). ⛔ The *"longest real chain is 32 / ~16x / Routes 132-134 are unmeasured"* line
> below and in `map_path.py` was stale on all three counts and is corrected in both.
> ➡ **Full measurement, the priority ruling and the startable next action live in
> `03-PUNCH-LIST.md` under `#24-ki76correctness`. ⛔ The numbers are NOT repeated here — one copy.**

Found by an adversarial audit of the KI-59-era claim *"our planner models the currents"*, which I had
just committed off the back of a clean 4/4 prediction run. **The 4/4 stands; the conclusion drawn
from it was too strong.** Both defects below are corroborated by OUR OWN measurements, not only by
the agent that reported them.

---

## Archived from `05-KNOWN-ISSUES.md`

PARTLY FIXED status preserved. Archived 2026-09-06 for the R3 budget after KI-91/92/93/94 were filed. Its index-space diagnosis is worth re-reading before touching handle_fainted_pokemon - that shape has now recurred four times.

## KI-66 — the multi-battle hazard is BROADER than the faint chooser — **PARTLY FIXED 2026-08-17: DRIVEN (`--driver ki66faint`), and the `_on_field` INDEX-SPACE defect is FIXED AND PROMOTED TO BOTH FORKS. STILL OPEN: the OWNER filter (measured INERT on our one fixture), `:541-545`, `_util.py:522-587`.** ⛔ Its HEADLINE — "it sends out an ALLY's mon" — is **REFUTED**: the bot never ATTEMPTED an ally slot. (Filed 2026-08-12, code-verified; the turn-1 IndexError sub-claim was REFUTED 2026-08-12.)

Filed from the adversarial review of the finished §Ch19. KI-64 fixed the three *faint* choosers; the
review found **four more party scans** on the same battle's paths that still have no partner concept.
None is fixed, and none has ever run live (every §Ch19 drive had zero faints).

**THE FOUR SITES — TABLE MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-17).** ‼ Keep the list:
`battle_handler.py:541-545` (the `None` fallback — no owner AND no on-field filter),
`:588-598` (writes a party-order index into a menu-order variable — the KI-34 shape),
`:630-636` (`alive_slots`, excludes only the on-field pair — and see the DRIVEN block below: that
exclusion is itself in the WRONG INDEX SPACE), and `_util.py:522-587`
(`get_potential_rotation_targets` / `select_rotation_target`, feeding an UNBOUNDED
`while … press A` at `battle_action_selection.py:288`).

✅ **REFUTED 2026-08-12 — the `IndexError` on turn 1 does not happen.** The review flagged
`decide_turn_in_double_battle` (`default.py:240-241`) doing `get_party()[partner.party_index]` with
an index of 3-5 while `gPlayerPartyCount` might still be 3, which would have fired on the FIRST turn
rather than on a faint. Refuted by our own driven run: `ch19d.log` f23255 shows `battle_is_active ->
True` with a **six-entry** party (`Sceptile|Mightyena|Swellow|Metang|Skarmory|Aggron`), and the
multi battle was won. `FillPartnerParty` does update the count in practice, so the index is in range.
‼ Worth stating because it is the one item on this list that would have broken §Ch19 in production
rather than merely on an error path — and it is the reason to check a "would fire immediately" claim
against an existing log before scheduling work for it.

---

## Archived from `05-KNOWN-ISSUES.md`

Archived 2026-09-06 for the R3 budget after KI-91/92/93/94 were filed. Status unchanged - its correction and reasoning are preserved verbatim.

## KI-50 — ‼‼ CORRECTED SAME DAY. The chapter is NOT a coin-flip: the CURRENT `magma_door.ss1` loses to Maxie DETERMINISTICALLY (2026-08-11, severity: MED, MEASURED)

**What was measured.** A second driven run of `--driver magmahideout` from `saves/magma_door.ss1`
— the identical command that produced `groudon=True, whiteouts=0` on 2026-08-10 — **lost**:
```
whiteouts in the run: 7      (vs 0 on 2026-08-10)
battle_text='NICK whited out!'  instr=BattleScript_LocalBattleLostEnd
respawn: MAUVILLE_CITY (22,6)
floors reached: 1F -> 2F_1R -> 3F_1R -> 4F, standing at (15,21) facing Maxie (16,21)
```
It navigated the whole dungeon correctly and reached Maxie — the *content* works. It then lost
the fight.

‼‼ **THE "1 IN 3" READING WAS WRONG AND IS WITHDRAWN.** I recorded two losses against one win
and wrote it up as a RATE. It is not a rate. **All three losing runs are BYTE-IDENTICAL:**
```
mh-anchor   41 unique [TURN] lines  md5 07f99a10ac8b
mh-anchor2  41 unique [TURN] lines  md5 07f99a10ac8b
mh-try1     41 unique [TURN] lines  md5 07f99a10ac8b
diff: IDENTICAL, all pairs
```
Same HP, same PP, same 18 turns, same Camerupt heal on the same turn. A `.ss1` replays identical
frame timing, so **the current `magma_door.ss1` does not sometimes lose — it always loses.**

‼ **AND THE ONE WIN WAS ON A DIFFERENT SAVE.** `magma_door.ss1` is **re-captured by
`--driver magmatravel` on every success**. The winning run of 2026-08-10 used the save as it stood
BEFORE 22:05; a later `magmatravel` success overwrote it at 22:05 with a different party/RNG phase,
and every hideout run since has lost the identical fight. Reaching Maxie is 3/3 and always was —
the *content* is fine.

‼‼ **THIS IS THE SAME FIXTURE-OVERWRITE HAZARD THAT KILLED THE `#24-teachmsgstall` REPRO EARLIER
THE SAME DAY**, on a completely different question, and I walked into it again within hours of
writing the prevention rule. **`saves/magma_door.ss1` is a CACHE, not a fixture.** The
deterministic-loss state is now preserved as **`saves/magma_door_losing.ss1`** — nothing writes to
that name, and it is a genuinely valuable repro: a boss fight that loses the same way every time is
the ideal fixture for the boss-healing and frozen-PP questions below.

‼ **A RETRY LOOP IS THE WRONG RESPONSE** and I ran one before checking. Eight attempts would have
produced eight identical losses (~80 minutes). It was stopped after attempt 1 once the md5s matched.
**The fix is a DIFFERENT SAVE, not another roll:** re-run `--driver magmatravel` from
`saves/post_mtpyre.ss1` to mint a fresh `magma_door.ss1`, then drive the hideout from that.

‼ **THIS AMENDS AN "ALREADY PROVEN" ROW.** `04-HANDOFF.md` carried
"The Magma Hideout chapter completes — ✅ `groudon=True`, 0 whiteouts" with no sample size beside
it. **n was 1.** The chapter reaching Maxie is reliable; the chapter *completing* is not, because
it depends on winning a boss fight with a party that arrives worn down. Quote it as
"1 of 2 driven runs" until there are more.

**Why it matters beyond this chapter:** the post-Maxie era is the precondition for §Ch16 (the
Slateport Harbor beat), so anchor manufacture for the next chapter inherits this coin-flip.

---

## Archived from `05-KNOWN-ISSUES.md`

Archived 2026-09-06 for the R3 budget after KI-91..KI-95 were filed. Status unchanged.

## KI-24b — region reachability BUILT; hop count alone is too coarse to rank by (2026-07-25)

`modules/story/region_reach.py` now answers reachability from the ROM's own `MapConnections` +
warps (never a hand-written table), with capability gates and — the point of the module —
`why_unreachable()` reasons that distinguish **"no connection path"** from **"needs Surf at
A↔B"** from **"reachable but N hops away (limit M)"**. The oracle itself is proven: ROUTE118 is
reachable from ROUTE120 at the Winona moment, where tile-level `calculate_path` said it was not.

**✅ SCOPE — KI-24 is now fixed for BOTH consumers (2026-07-25).** `region_reach` is wired into
`_counter_area_allowed` (counter-candidate selection, `counter_plan.find_counter_candidates`) AND,
as of 2026-07-25, into `_training_area_allowed` (training-area selection, passed as `allow=` to
`best_training_area`). Tile-level `calculate_path` no longer answers any region-scale question in
the story bot.

**The measured effect on the training predicate** (`repro_counter_plan.py`, same Winona-era live
position, same candidate list, ONLY the predicate changed):

| `_training_area_allowed` | reachable flags over the 10 Winona candidates |
|---|---|
| before (`calculate_path`) | `[False × 10]` — every candidate rejected; KI-24 in the raw |
| after (`region_reach`) | `[True × 5, False × 5]` — incl. **Route 118 Electrike: reachable** |

**How it landed, and the test bug it exposed.** The first attempt FAILED
`tools/story-dev/repro_fodder_grass.py` case 5 (`L31 team in Fallarbor`: expected `SKIP GRIND`,
got `RELOCATE to ROUTE111 L19-22`) and was reverted rather than forced. Investigating the failure
showed the TEST was wrong, not the change — see 08-MISTAKES 2026-07-25 (partial mock). `_stand_at()`
patched only `modules.map.get_map_data_for_current_position`, while the predicate's `calculate_path`
branch read `modules.player.get_player_location`, which stayed live. So case 5 had been asserting a
verdict for a position it never simulated — it was really asking about `(PETALBURG_CITY, (7,6))`.

Proof the re-baseline was a TEST fix and not a behaviour change: with `_stand_at()` repaired and
`story_mode.py` **untouched**, the ORIGINAL `calculate_path` code also answers
`RELOCATE to ROUTE111`, and cases 1-4 are unchanged. Three independent sources agree Route 111 is
reachable from Fallarbor — `calculate_path` succeeds from `(14,7)`, `region_reach` measures 2 hops,
and `training_areas.py`'s own comment says so.

**✅ The sibling repro that went red is fixed — `tools/story-dev/repro_counter_plan.py`.** Its
primary assertions never failed; what failed was a non-vacuity scaffold asserting that a
deliberately WIDE type set contained at least one `False`. **That scaffold was relying on the
bug** — it existed only because the Winona set was vacuously all-`False` under the pre-KI-24
predicate, and it inverted the moment the false negatives went away (the wide set now returns
`[True × 25]`). Per user ruling 2026-07-25 the non-vacuity check MOVED to where non-vacuity now
genuinely lives: the Winona set itself, asserted to span BOTH branches, which is the property the
sort proof actually needs. The wide set is still sorted as a larger-sample check.

This was the SECOND test in one day found to be asserting something that depended on a defect
(case 5 was the first) — see the 08-MISTAKES pattern entry for the shape and the prevention rule.

**‼ But the cost model I assumed is wrong, and the measurement says so.** Measured hops from
ROUTE120 on the Winona-era save:

| target | hops |
|---|---|
| FORTREE_CITY | 1 |
| ROUTE119 | 2 |
| **LILYCOVE_CITY** | **2** |
| **ROUTE118** (the real Winona answer) | **3** |
| MOSSDEEP_CITY | 4 |
| PACIFIDLOG_TOWN | 10 |

I expected "the answer is a handful of hops, the far cities are many". **Lilycove is CLOSER than
Route 118 by this metric**, and Mossdeep is one hop further. Because a single ROM connection can
span an entire sea route, uniform 1-hop weighting compresses "same landmass cluster" (1-4) and
only separates the genuinely far-flung (Pacifidlog, 10).

**So hop count is a usable FILTER but not a usable RANK.** `max_hops=4` cuts Pacifidlog-class
targets while keeping the Fortree/119/118 cluster, and that is how it should be used — as a
sanity bound, with `counter_plan`'s existing criteria (type coverage → verified tile →
encounter rate → level fit) doing the actual ranking.

**Next, if finer granularity is ever needed (`#24-edgecost`):** weight each edge by the source
map's traversal length rather than a flat 1, or price travel in FRAMES so it composes with
`training_areas.estimate_frames_to_level`. Both are real work; neither is needed until hop
count demonstrably mis-ranks something.

**Also still open:** `KNOWN_GATES` holds only THREE hand-verified edges (`region_reach.py:81-91`) —
DEWFORD_TOWN↔ROUTE106 and DEWFORD_TOWN↔ROUTE107 (both `surf`), plus EVER_GRANDE_CITY↔VICTORY_ROAD_1F
(`waterfall`, added 2026-07-26 because Victory Road's L38-42 Hariyama otherwise ranked #1 as a
counter candidate). *(This line said "only one entry" until re-counted 2026-07-27.)* So
edges whose requirement cannot be derived from ROM data currently read as UNGATED — i.e. this
oracle now fails OPEN where the old one failed CLOSED. That is the safer direction for a
*planner* (a wrong "yes" costs a wasted walk that navigation will fail recoverably; a wrong "no"
is invisible) but it must be grown before this gates anything irreversible.

**Prevention rule:** when you introduce a cost metric, MEASURE it against known-good and
known-bad cases before trusting it to rank. "Reachable" was a boolean that hid a cost; "hops" is
a cost that hides map size. Each fix exposed the next assumption — check the numbers, don't
reason about them.

---

# ⚠ MIXED — entries added 2026-07-27 onward. ⛔ **READ EACH ENTRY'S OWN MARKER.**
> Re-titled 2026-08-22 (PASS 5). This H1 read *"open issues found by a code audit"* and is
> the LAST H1 in the file, so it scoped ~82% of it — while many entries beneath it carry their
> own ✅ markers. ⛔ **A heading is a claim about every entry beneath it**;
> that exact shape once cost about a day of re-doing finished, gated, promoted work.

---

## §Ch20 — the seven live drives (archived 2026-09-06 from `04-HANDOFF.md`)

Moved verbatim: §Ch20 shipped 2026-08-14 and its per-room recipes are a FINISHED chapter's
record, not current state. They are kept in full because each `Expect:` block names which
field of the verdict is load-bearing — knowledge that cost seven live drives to earn.
⚠ Status when archived: **all PASS except `ch20room9`, which is 2W/1L** (the Archie fight is
the chain's one stochastic element — see its own note below).

```
# --- §Ch20, the live drives (SEVEN of them; each ~4-25 min). All PASS as of 2026-08-14,
#     EXCEPT ch20room9, which is 2W/1L — the Archie fight is stochastic, see its note. ---
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20dive  --frames 900000
#   Expect: legs=6/6 at_entrance=True got_out=True can_continue=True ACCEPTANCE: PASS
#   ‼ `got_out` is the one that matters — an underwater cavern is the best place to strand a run.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room1 --frames 1500000
#   Expect: in_room1=True ab_before=False ab_after=True smashed=True pushed1=True pushed2=True
#           in_room2=True can_continue=True   ACCEPTANCE: PASS
#   ‼ `ab_before=False` is an ASSERTED part of the verdict: if the corridor was already reachable
#     the run proved nothing about the puzzle. A one-armed pass here would be meaningless.
# ⛔ THE THREE Expect: BLOCKS BELOW WERE ATTACHED TO THE WRONG COMMANDS until 2026-08-13 (the
#   fault note even carried ch20room2's PASS line). Each now sits DIRECTLY under its own command.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room2 --frames 2000000
#   Expect: room1_ok=True m1=False m2=False m3=True pushes=3/3 in_room6=True can_continue=True
#   ‼ It RE-SOLVES ROOM 1 from scratch first (FLAG_TEMP_* objects respawn on every map load), so
#     a ch20room2 PASS is also a Room 1 PASS. `m2=False` is the arm that matters: it attributes
#     the opening to the PUSHES rather than to the Rock Smash.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room6 --frames 2500000
#   Expect: room2_ok=True crossed=True in_room3=True room3_walk=True can_continue=True
#   ‼ `crossed` is THE FIRST EXECUTED CURRENT CROSSING here. `room3_walk` re-confirms LIVE that
#     Room 3 is crossable PUSH-FREE and that the line enters the trainer sight tile (6,5).
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room3 --frames 3000000
#   Expect: crossed=True usable=6 battles=1 saw_double=True in_room8=True can_continue=True
#   ‼ `saw_double` is REPORTED, NOT GRADED — grading a decomp claim would turn "we learned the
#     claim was wrong" into "the run failed". ‼ `battles` counts ROOM 3 only: counting run-wide
#     once printed a false REFUTED over data that CONFIRMED it (the Room 1 grunt fights every run).
# ‼ FAULT INJECTION: POKEBOT_CH20_FAULT=room1 forces the Room 1 solve to fail, so the drivers'
#   FAILURE branch can be exercised on demand.
#   Expect: RESULT … in_room2=False can_continue=False and a clean `ACCEPTANCE: FAIL` — ‼ a run
#   in fault mode that prints ACCEPTANCE: PASS, or no ACCEPTANCE at all, is the DEFECT.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room8 --frames 4000000
#   Expect: room3_ok=True pushes=9/9 attempts=1 recovered=False exit_path=True in_room9=True
#           can_continue=True   ACCEPTANCE: PASS
#   ‼ Step 9 faces LEFT. A boulder pushed north from (5,4) lands on (5,3) and PERMANENTLY
#     seals the only route to the (5,2) exit.
#   FAULT: POKEBOT_CH20_FAULT=room8 abandons attempt 1 before push 5 to EXERCISE the
#     jam-recovery handler. Expect: attempts=2 recovered=True and still ACCEPTANCE: PASS.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room9 --frames 6000000
#   Expect: rooms_ok=True triggered=True battles_r9=1 kyogre_flag=True var2=True landed=True
#           escaped=True ocean_path=True can_continue=True   ACCEPTANCE: PASS
#   ‼ 2W/1L: the ARCHIE fight is the chain's one stochastic element. A LOST run prints NO
#     RESULT AND CANNOT — the whiteout drops to Manual and the generator is abandoned. The
#     `PRE-ARCHIE PARTY` HP line is the loss's attribution record; grade a silent transcript
#     by its presence.
PYTHONUTF8=1 py -3.12 probe_route128_landing.py     # §Ch20's EXIT: 9/9, the atoll is real
#   ‼ The landing tile has ZERO surfable neighbours, so a naive "Surf from where you land" reads
#     as a HUNG LEG, not a failure. (§Ch20's exit leg is built; this stays as the trap it names.)
```

---

## `KI-95` — the original defect (archived 2026-09-06 from `05-KNOWN-ISSUES.md`)

Moved when the bug was fixed: `05-KNOWN-ISSUES.md` is for OPEN problems, and what remained open
about `KI-95` was only that the fix is unpromoted and rests on deprecated behaviour. The defect
record itself is kept in full here — it is the evidence that the fix was needed.

**VERIFIED BY READING IT** — as it stood on 2026-09-06, before the fix extracted the ranking into `rank_replacement` (`plugins/custom_modes/story_mode.py:118-191`); the chooser itself is `choose_new_lead_after_faint` (`story_mode.py:215-320`):
```python
outgoing = 0.0
for learned in mon.moves:
    if learned is None or learned.pp == 0 or learned.move.base_power == 0:
        continue                                   # ⬅ base_power used ONLY to skip status moves
    for pair in foe_pairs:
        m = 1.0
        for t in pair:
            m *= learned.move.type.get_effectiveness_against(t)   # ⬅ PURE TYPE MULTIPLIER
        outgoing = max(outgoing, m)
key = (incoming, -outgoing, -hp_fraction, -mon.level)
```
⇒ **`outgoing` is effectiveness only — never weighted by base power or level**, and `level` is merely
the last tiebreak, applied AFTER it.

**CONSEQUENCE.** Against Glacia's Glalie (pure Ice), our **L19 Zigzagoon's Rock Smash** (Fighting, 2×,
**20 BP on a level-19 mon**) scores `outgoing = 2.0` and **outranks a full-HP L48 Mightyena** whose best
is 1.0. The mule is sent in to die. Observed in a simulated Glacia run at T19.

**⚠ SCOPE — this runs in EVERY battle**, so the bar is this project's shared-path bar: a repro that
fails first, an argument that the change is ADDITIVE, and the full suite.

⛔⛔ **CORRECTED 2026-09-06 — THE INSTRUMENT NAMED HERE WAS THE WRONG ONE.** This entry said the bar
included *"the ordinary-case A/B"* via `POKEBOT_RECORD_TURNS` /
`evidence/ki93_ordinary_BASELINE.turns`. **That A/B cannot see this change at all.** The turn recorder
records what `decide_turn` RETURNS, and `choose_new_lead_after_faint` is not called unless something
FAINTS — so in an ordinary battle the recording is byte-identical whether the fix is present, absent,
or actively broken. ⇒ it would have passed trivially and been reported as evidence.
‼ **A passing A/B over a code path the run never executes is not weak evidence, it is NO evidence** —
and it is worse than none, because it reads as proof. **Choose the instrument by the QUESTION** (the
playbook §0c rule) means asking *"does this run reach the changed line?"* BEFORE quoting a green arm.

**⛔ NOT A BUG, RECORDED SO IT IS NOT "FIXED" LATER:** `Fly` and `Dive` sit in `banned_moves`
(`profiles/battle.yml:23-27`) under an explicit **`# 2-turn`** comment, beside `Bounce`. That is a
DELIBERATE exclusion — two-turn moves waste a turn and can desync the handler. It has a real cost
(Swellow's Fly is its best move vs Grass and is never used, so it effectively fields three moves), but
it is a trade-off with a reason, **not an oversight**. Analysis that calls it a defect is wrong.

---

---

## `KI-93` — the REFUTED "corrected design for attempt 2" (archived 2026-09-06)

Archived when the census measured its central premise false. Its error is instructive: the design
was carefully argued, internally consistent, and named the right code — and it could never have
worked, because the memory it proposed would be destroyed between every pick. **Nothing in the
text signalled that; only a control-line drive did.**

**⇒ CORRECTED DESIGN FOR ATTEMPT 2 (not yet built).** The fix needs MEMORY ACROSS LOOP ITERATIONS,
which the one-shot fork does not have: record that the last submitted `(battler_index, index)` was
REFUSED, and make the next selection in that turn choose a different usable slot. The natural home is
the `HandleInputChooseMove` branch (which is where the refusal is observed) plus a small
`refused_this_turn` set consulted after `decide_turn` returns.
⛔ That is a bigger change to the most safety-critical loop in the codebase than attempt 1 was, so it
keeps the same bar: the ordinary-case A/B above must stay byte-identical, plus the full suite.
✅ Everything needed is already in place — the baseline, the recorder (`POKEBOT_RECORD_TURNS`), and
the repro (`--driver ch24probe`).

---

## `KI-93` — fix attempt 1, verbatim (archived 2026-09-06)

Superseded: its central verdict was measured with a diagnostic that called a
non-existent function inside a bare `except`, so "fired zero times" meant "my logger
never ran". Kept in full — the attempt itself was reasonable and the way it failed is
the lesson.

**⛔⛔ FIX ATTEMPT 1 — TRIED, MEASURED DEAD, AND REVERTED (2026-09-06).** Do not repeat it.
The attempt copied the SHIPPED precedent 12 lines above it in the same function: the
`BattleScript_SelectingMoveWithNoPP` fork (`battle_action_selection.py`, added 2026-07-23), which
overrides the strategy's pick when the game bounces it. Extending that to
`BattleScript_SelectingTormentedMove` looked ideal — same shape, same file, observed-refusal, inert
unless the refusal is on screen.
✅ **It passed the ordinary-case A/B** (`ki93_ordinary_BASELINE.turns`, byte-identical) — so it was
provably harmless.
⛔ **And it did NOT fix the freeze.** Rather than guess why, I instrumented the fork itself with a
one-line log and re-drove: **it fired ZERO times.**
⇒ ⭐ **THE FORK IS NEVER REACHED.** It sits AFTER the branch dispatch, so it only runs once a branch
has assigned `battler_index` — i.e. once a decision is being COMMITTED. The Torment loop never gets
there: it alternates `HandleInputChooseAction` → select → refusal → `HandleInputChooseMove` → the
"press B" branch → `continue`, which short-circuits before the fork. The PP fork works only because
its refusal leaves the game in a state that DOES reach the commit path.
‼ **"The fix is wrong" and "the fix is never reached" are different answers needing different work** —
one log line separated them in a single drive.

---

## `KI-93` — the full pre-fix investigation (archived 2026-09-06)

Archived on the day it was fixed. Kept in full because the way this bug resisted FOUR
implement-drive-revert cycles is more instructive than the fix: three of those verdicts
were VOID (a diagnostic calling a function that does not exist, inside a bare `except`),
and the design that replaced them was refuted by a single control-lined census drive.

**MEASURED** by the new `--driver ch24probe` on `post_league_shop.ss1`. The bot walks into the League,
reaches Sidney, starts the fight, **fights several turns successfully**, and then the controller
vanishes while the battle is still live:
```
f6569 … f11393   PARTY CHANGE ×6   ⇐ EXP gained and lead rotations: the fight WAS progressing
f19363  !!! NO-PROGRESS x1200
        sig=('<none>', 'BATTLE', 'BattleScript_SelectingTormentedMove', 'DialogueNotActive', …)
f19363      gen -> <no controller on the stack (Manual mode / dropped out)>
f38163  HANG CONFIRMED (20000 frames no progress)
```
⇒ **Sceptile gained EXP (145272 → 146533) and mons fainted and were replaced before the drop**, so
this is not a failure to engage — it is a mid-battle collapse.

**WHAT IS MEASURED, AND WHAT IS NOT — read this before acting.**
* ✅ MEASURED: the controller is GONE at f19363 (`no controller on the stack`), the mode is Manual, the
  battle is still live, and the game sits in `BattleScript_SelectingTormentedMove`.
* ✅ MEASURED: it is **not** the probe's timeout. The probe's battle wait is **90,000 frames** and the
  drop happens at ~19k. ‼ An EARLIER version of this probe waited only 4,000 frames and produced a
  *superficially identical* signature by abandoning the battle itself — **that run's evidence is void
  and must not be cited.** The fix to the instrument came first, and only then was this recorded.
* ⛔ NOT MEASURED: **the identity of the exception.** "Torment makes our move-chooser raise" is a
  HYPOTHESIS, not a finding. `BattleScript_SelectingTormentedMove` is where the game was standing when
  everything stopped; that is a correlation.

**WHY IT IS PLAUSIBLE ANYWAY** (still a hypothesis): Sidney's team carries **Torment**, which forbids
repeating the last move. Our story strategy picks the strongest usable move each turn and would keep
re-selecting the same one; if the selection path raises rather than falling back, the exception escapes
`BattleListener` — and this project has ALREADY established that **any** exception from that sibling
controller reaches `modules/main.py:151-158` and sets Manual, which is precisely the
sibling-controller containment problem left open by `KI-90`.

**⇒ NEXT STEP, AND IT IS CHEAP: CATCH THE EXCEPTION'S IDENTITY.** Do not guess it. Re-run the probe
with the exception surfaced (log it from the listener, or wrap `decide_turn`), and read the type and
the message. Everything after that depends on which it is.
**Reproduce:** `PYTHONUTF8=1 py -3.12 story_harness.py post_league_shop.ss1 --driver ch24probe --frames 200000`

**⭐⭐ ROOT-CAUSED 2026-09-06, SAME DAY — AND MY OWN HYPOTHESIS WAS WRONG IN MECHANISM.**
This entry first said the controller "drops out", and offered "Torment makes our chooser raise" as a
hypothesis. **There is no exception at all.** The bot's own debug log records a DELIBERATE guard:
```
f4334908 [MODE] Story -> Manual
  message="KI-47: battle sub-handler 'handle_battle_action_selection' ran 3001 frames with no
           battle progress (frozen at ('BattleScript_SelectingTormentedMove', 'Handle…"
```
⇒ ✅ **`KI-47`'s net fired exactly as designed.** The chooser does not raise — it **loops**, making no
progress, and the watchdog stopped the bot with a diagnostic. ‼ The "no controller on the stack" line
I read as a drop-out is the CONSEQUENCE of that deliberate stop, not its cause.

**⇒ THE ACTUAL DEFECT, LOCATED:**
* `TemporaryStatus.Torment` is real and readable — `battle_state.py:97` defines it and `:159` sets it
  from `(status2 >> 31) & 0b1`.
* ⛔ **NO move chooser consults it.** `grep -rn "Torment"` over `modules/battle_strategies/`,
  `modules/battle_action_selection.py` and `plugins/custom_modes/story_mode.py` returns **nothing**.
* ‼ And this is a GAP IN AN ESTABLISHED PATTERN, not an unknown mechanic: `_util.py:67-69,124` and
  `item_stealing.py:55` already consult `Rooted`, `Wrapped`, `EscapePrevention` and `Substitute`.
⇒ under Torment the chooser re-selects the strongest move — the one it just used — the game refuses
it, and the sub-handler spins until `KI-47` stops the run.

**⚠ THE FIX HAS A PREREQUISITE, AND IT IS WHY THIS IS NOT A ONE-LINE FILTER.** Excluding the forbidden
move requires knowing the LAST MOVE USED, and **our `battle_state` does not expose one** — no
`last_used_move` / `last_move` / `previous_move` anywhere in `modules/battle_state.py`. ⇒ any fix must
first surface that (Emerald tracks it in `gLastMoves`), which makes this a state-model addition plus a
chooser change, in a SHARED battle-path file. ⛔ The bar for that is this project's standard one: a
repro that fails first, an argument for why the change is ADDITIVE, and the full gate suite.
✅ **The repro already exists** — `--driver ch24probe` reproduces it in ~19k frames.

**✅ FIX DESIGNED AND VERIFIED 2026-09-06 — DELIBERATELY NOT YET IMPLEMENTED.** Full reasoning in
`06-DECISIONS-LOG.md` that date. The short version, so nobody re-derives it:
* ✅ `STATUS2_TORMENT = (1 << 31)` (`include/constants/battle.h:155`) — our decode at
  `battle_state.py:159` is CORRECT, so a Torment-keyed filter cannot misfire in ordinary battles.
* ✅ The forbidden thing is `gLastMoves[battler]`, a MOVE ID, tested at SELECTION time
  (`src/battle_util.c:999`); the refusal is a **pure re-prompt that never consumes the turn** — which
  is precisely why re-picking spins.
* ✅ `gLastMoves` is readable in house style (`pokeemerald.sym:150`, `02024248`, 8 bytes).
* ⭐⭐ **THE BUG'S TOTAL BLAST RADIUS IS ONE POKÉMON IN THE WHOLE GAME:**
  `grep -c MOVE_TORMENT src/data/trainer_parties.h` = **1**, Sidney's SHIFTRY. A WRONG fix would
  affect EVERY battle. ⇒ that asymmetry is why this is designed carefully rather than patched quickly.
* ⛔ **THE OBVIOUS FIX IS THE DANGEROUS ONE.** `get_strongest_move_against` (`_util.py:244-269`)
  compacts its move list and returns an index INTO THE COMPACTED LIST; the existing exclusions are
  safe only because they append `-1` and preserve position. A filter that SKIPS would shift indices
  and mis-select in ordinary battles — the same index-space shape as `KI-18`/`KI-34`/`KI-66`. It also
  would not fix the bug alone (a four-layer fallback re-picks the slot) and misses double battles.
* ⇒ **CHOSEN: the OBSERVED-REFUSAL variant** — detect that the game refused a selection and pick
  differently, rather than predicting the forbidden move. Vacuously safe on the shared path, needs no
  `gLastMoves` read, and closes **Taunt and Imprison** too.
⛔ **BEFORE IMPLEMENTING:** the bar for a shared battle file is a failing repro (`--driver ch24probe`,
have it), an ADDITIVE argument, the full suite, **and an A/B on the ORDINARY case** — a normal battle
that must be unchanged. Specify that A/B first.

**⛔ FIX ATTEMPT 1 (the `SelectingMoveWithNoPP`-style one-shot fork) — ARCHIVED** →
`28-HANDOFF-ARCHIVE.md` (2026-09-06). It passed the ordinary-case A/B, did NOT fix the freeze,
and its *"fired zero times"* verdict is one of the three RETRACTED below as measured with a
broken logger. ⇒ **do not re-run it to "check"; re-derive it if it is ever proposed again.**

**⇒ ⛔ THE "CORRECTED DESIGN FOR ATTEMPT 2" IS REFUTED AND ARCHIVED** → `28-HANDOFF-ARCHIVE.md`
(2026-09-06). It rested on *"this function runs for ONE selection phase, so a plain local set
lives exactly one turn"* — **measured FALSE** by the census below (the handler is re-entered
five times per refusal episode). Kept verbatim in the archive because the REASON it is wrong is
the most useful thing anyone has learned about this bug.

**⛔⛔⛔ RETRACTED 2026-09-06 — THE "THREE ELIMINATED LOCATIONS" BELOW WERE MEASURED WITH A BROKEN
INSTRUMENT AND ARE **NOT** ELIMINATED.** Every one of those verdicts rested on a diagnostic that
called **`debug_logger.log(...)` — A FUNCTION THAT DOES NOT EXIST** (`modules/debug_logger.py` has
`event()`, not `log()`) — inside my own `try/except: pass`. So the `AttributeError` was swallowed and
**nothing was ever written**; "fired zero times" meant "my logger never ran", not "the code never ran".
⇒ ⭐ **THE LESSON THIS FILE ALREADY CARRIED, COMMITTED AGAIN HOURS LATER: an instrument that fails silently substitutes the subject.** Treat the table below as UNTESTED, not excluded.

**✅ WHAT IS ACTUALLY MEASURED, WITH A VERIFIED-WORKING LOGGER (`debug_logger.event`, plus an
unconditional CONTROL line proving the logger writes):**
* The confirm loop in `battle_action_use_move` **is entered and exits normally** — CONTROL fired **13
  times**, the spin-detector **0**. ⇒ not the freeze site.
* The commit path runs **20 times** with `instr='BattleScript_MoveEnd'` / `'FaintedMonEnd'` —
  **never** `'SelectingTormentedMove'`. ⇒ conditioning a fix on the refusal script AT THE COMMIT POINT
  can never fire, which is the real reason attempt 1 did nothing.
* ⭐⭐ **A BRANCH CENSUS FOUND THE SPIN SITE IN ONE DRIVE:**
```
controller0='CompleteOnInactiveTextPrinter2' count=1     instr='BattleScript_SelectingTormentedMove'
controller0='CompleteOnInactiveTextPrinter2' count=500   instr='BattleScript_SelectingTormentedMove'
controller0='CompleteOnInactiveTextPrinter2' count=2000  instr='BattleScript_SelectingTormentedMove'
```
⇒ **the loop sits in the "KNOWN WAIT STATES" branch** of `handle_battle_action_selection` with the
Torment message on screen. That branch does `yield; continue` for ever and is **deliberately exempt
from `KI-46`'s counter** ("recognised, so they must NOT count"), which is why only `KI-47`'s
last-resort net ever fired. Its own comment predicted this: *"safe to wait … because the KI-47 net
still backstops this."*
‼ **A first fix there — bound the wait and press B to dismiss — did NOT clear the hang** and was
reverted. Whether the press is wrong, the bound too long, or the message needs a different input is
**not yet measured**; instrument that the new branch RUNS before theorising.

**⭐⭐⭐ ROOT CAUSE ESTABLISHED FROM THE DECOMP, 2026-09-06 — AND IT IS A LIVELOCK, NOT A HANG.**
TWO things are true at once, and every fix attempt addressed only one:
1. **A BUTTON PRESS IS REQUIRED.** `sText_PkmnCantUseMoveTorment` (`src/battle_message.c:260`) ends in
   `\p` = `CHAR_PROMPT_CLEAR`, which parks the printer in `RENDER_STATE_CLEAR`
   (`src/text.c:1102-1105`) until `TextPrinterWaitWithDownArrow` sees an **edge-triggered**
   `JOY_NEW(A_BUTTON | B_BUTTON)` (`src/text.c:865-882`). `gTextFlags.autoScroll` is set ONLY for
   link/recorded battles (`src/battle_message.c:3002-3005`) ⇒ in an ordinary battle **there is no
   timeout and no auto-advance: it waits for ever.** That is why our "recognised wait" branch spins.
2. ⛔⛔ **AND DISMISSING IT DOES NOT HELP.** `Cmd_endselectionscript` sends the engine to
   `STATE_WAIT_ACTION_CHOSEN`, which **re-emits `CONTROLLER_CHOOSEMOVE`** (`src/battle_main.c:4217`)
   — the move menu reopens and the bot picks the SAME slot again.

**⇒ ⭐ THE ASYMMETRY THAT IS THE WHOLE BUG — and it explains why our no-PP handling works:**
the `ChooseMoveStruct` handed to the controller carries only `species`, `monTypes`, `moves[4]`,
`currentPP[4]`, `maxPP[4]` (`src/battle_main.c:4201-4217`).
* **no-PP** is VISIBLE (`currentPP[i]`) ⇒ a PP-aware chooser never re-picks ⇒ **at most one refusal**.
* **Torment** depends on `gLastMoves[]` + `STATUS2_TORMENT` (`src/battle_util.c:999`), **neither
  transmitted** ⇒ the chooser is structurally blind ⇒ **it re-picks for ever.**
⇒ **no-PP's refusal is SELF-CORRECTING; Torment's is STABLE UNDER RE-SELECTION.**
✅ **INDEPENDENTLY PROVEN BY OUR OWN DATA:** the commit-path instrumentation logged
`slot=2 battler=0` **20 times**. The decomp predicted exactly that, and we measured it before knowing
why.
‼ **The same blindness covers Disable, Taunt, Imprison and Choice-lock** (all set in
`TrySetCantSelectMoveBattleScript`, `src/battle_util.c:976-1080`) — a fix should cover the class.

**⇒ THE FIX NEEDS BOTH HALVES. Either alone is why four attempts failed:**
(a) **DISMISS** — ONE edge-triggered A or B, delivered only once the glyphs have finished (the
    down-arrow is up). ⚠ Three timing traps, all decomp-cited: a press DURING printing is eaten as a
    speed-up and does not count (`src/text.c:950-954`); a HELD button is invisible because `JOY_NEW`
    is edge-only (`include/global.h:128`); and a press ONE FRAME LATE lands in
    `HandleInputChooseMove` where B means CANCEL → the action menu, where B is inert in a single
    battle (`src/battle_controller_player.c:306-311`) — **a second, different-looking freeze.**
(b) **DO NOT RE-PICK THE REFUSED SLOT** — the half every attempt missed. Either mirror
    `CheckMoveLimitations` bot-side (`src/battle_util.c:1082-1123` is the algorithm) by reading
    `gLastMoves[]`, `STATUS2_TORMENT` and `gDisableStructs[]`, or — symbol-free — **blacklist for the
    turn any slot that produced a selection-refusal message.**

**⇒ ✅ THE CENSUS WAS RE-ADDED AND DRIVEN, 2026-09-06 — AND IT REFUTED THE FIX DESIGN BELOW.**
`POKEBOT_KI93_CENSUS=1`, `--driver ch24probe` on `post_league_shop.ss1`. ⭐ **The `[KI93-CTL]` control
line fired 13 times**, so unlike the three VOID verdicts above, this instrument provably wrote.

```
f4328601 [KI93-CTL]    handle_battle_action_selection entered — census armed
f4328608 [KI93-COMMIT] battler=0 action=UseMove slot=2 census={'decide@0': 1}
f4329276 [KI93-CTL]    handle_battle_action_selection entered — census armed
f4329283 [KI93-COMMIT] battler=0 action=UseMove slot=2 census={'decide@0': 1}
f4330143 [KI93-CTL] … f4330149 [KI93-COMMIT] slot=2 census={'decide@0': 1}
f4331061 [KI93-CTL] … f4331068 [KI93-COMMIT] slot=2 census={'decide@0': 1}
f4331887 [KI93-CTL] … f4331894 [KI93-COMMIT] slot=2 census={'decide@0': 1}
f4331906 [KI93-WAIT] frames=1    cb0='CompleteOnInactiveTextPrinter2' instr='BattleScript_SelectingTormentedMove' last_committed_slot=2
f4333705 [KI93-WAIT] frames=1800 cb0='CompleteOnInactiveTextPrinter2' instr='BattleScript_SelectingTormentedMove' last_committed_slot=2
         (no `[KI93-WAIT] ENDED` line ever — then KI-47 stops the run at 3001 frames)
```

**⛔⛔ FINDING 1 — THE HANDLER IS RE-ENTERED, SO A FUNCTION-LOCAL MEMORY CANNOT WORK. THIS KILLS THE
"CORRECTED DESIGN FOR ATTEMPT 2" WRITTEN ABOVE.** That design says: *"this function runs for ONE
selection phase — so a plain local `set` lives exactly one turn and needs NO clearing logic, which is
the part that would otherwise be easy to get wrong."* **MEASURED FALSE.** The census counter resets to
`{'decide@0': 1}` at **five separate calls** (f4328601, f4329276, f4330143, f4331061, f4331887), each
~700-900 frames apart, each re-picking **slot 2**. ⇒ a `refused_slots` local is DESTROYED between every
pick, so attempt 2 would have been wiped clean before it was ever consulted. **The memory must outlive
the call.** ‼ This is why a fifth attempt built on that paragraph would have failed too — and it was
invisible without the control line, because the design *reads* correct.

**✅ FINDING 2 — THE TERMINAL STATE IS ONE UNBROKEN WAIT, NOT AN ALTERNATION.** Once the run parks at
f4331906 it stays in the `CompleteOnInactiveTextPrinter2` branch monotonically to KI-47's cut. The
`[KI93-CANCEL]` hits in this drive all carry ORDINARY scripts (`BattleScript_MoveEnd`,
`FaintedMonEnd`, `ItemHealHP_RemoveItem`) — normal turn traffic, **not** part of the livelock. ⇒ the
earlier "it alternates ChooseAction ↔ ChooseMove" picture describes the RE-PROMPT PHASE, not the
freeze; the freeze is a single branch that never yields control back.

**✅ FINDING 3 — THE DATA THE FIX NEEDS IS PRESENT AT THE FREEZE SITE.** `last_committed_slot=2` is
known inside the wait branch, alongside `instr='BattleScript_SelectingTormentedMove'`. So the
"do-not-re-pick" half needs no `gLastMoves` read and no `CheckMoveLimitations` mirror — the refused
slot is simply the one we last committed when a refusal script is on screen.

**⇒ NEXT STEP: implement BOTH halves, with the memory held OUTSIDE the function call** (module-level,
scoped to the refusal episode and cleared once an ordinary battle script is seen), plus a bounded
edge-triggered dismiss inside the wait branch. ⛔ Bar unchanged: additive argument, full suite, and —
**unlike `KI-95`** — the ordinary-case A/B IS the right instrument here, because this change touches
the wait branch and the committed-slot path that EVERY battle executes.

*(⛔ The three attempts and their VOID verdicts are archived verbatim in `28-HANDOFF-ARCHIVE.md` (2026-09-06), moved out of this current-state file per the R3 budget rule. They are history, not evidence — treat those locations as UNTESTED.)*



---

---

## `KI-93` — the full resolution evidence (archived 2026-09-07)

Archived once the fix shipped and was graded clean. Kept in full because it is the
template `KI-96` should copy: gate on the game's own state rather than a frame count,
key the memory on the Pokémon rather than the slot, and grade the drive by its
SEQUENCE rather than its totals.

### ✅ 2026-09-06 — FIXED, RE-DRIVEN, AND GRADED CLEAN BY A FAULT-PROVEN INSTRUMENT. ⛔ NOT PROMOTED.

**The bot now fights Sidney to a conclusion.** Same repro, same fixture
(`post_league_shop.ss1 --driver ch24probe --frames 200000`):

⛔⛔ **EVERY NUMBER BELOW IS LABELLED WITH THE DRIVE THAT PRODUCED IT.** An earlier version of this
table mixed two runs — it printed the SUPERSEDED drive's loss under the FINAL drive's heading, and a
Tier 1 reviewer caught it. *(SESSION DISCIPLINE #7/#8: say which run a number came from.)*

| | before the fix | `234031` — first fix, DEFECTIVE | ✅ `235815` — FINAL, the graded drive |
|---|---|---|---|
| `KI-47` battle sub-handler stops | 3-6 per run | 0 | **0** |
| `SelectingTormentedMove` in the run log | the run ends on it | 0 | **0** |
| unjustified re-picks (grader C2) | n/a | **RED** — a fainted mon's vetoes reached its replacement | ✅ **0** |
| battle outcome | never reached — Manual at ~f18k | `BattleOutcome.Lost` at f38534, then a whiteout | ⭐ **`BattleOutcome.Won` at f35237** |

⭐⭐ **THE BOT NOW BEATS SIDNEY.** `f35237: outcome=BattleOutcome.Won`, `bt='NICK got $4900 for
winning!'`, and the game runs `EverGrandeCity_SidneysRoom_EventScript_Defeated` +
`PokemonLeague_EliteFour_SetAdvanceToNextRoomMetatiles` — the door to Phoebe opens. **§Ch24 FIGHT 1 IS
WON.**
‼ **And the two drives are deterministic from the same save**, so the only variable is the code ⇒ the
stale vetoes were not merely cosmetic: they forced bad moves and plausibly cost that battle. That is a
strong inference from a matched pair, not a controlled experiment — labelled as such.

⛔⛔ **RETRACTED — THIS PARAGRAPH SAID "It LOST the fight" AND THAT WAS THE OTHER DRIVE.** The final
run **WON**. The loss belongs to `234031`, the defective first fix.

‼ **WHAT IS NOW UNPROVEN, AND MUST NOT BE ASSERTED EITHER WAY:** *"the bot loses the Elite Four on
levels"* has **never been driven on the current code**. The only drive of the current code won fight 1
and stopped there. The party is L48-53 and the simulation says ~L60 is needed for Glacia (fight 3), so
the level gap is still the expected wall — **but that is a SIMULATION result, not a drive**, and this
entry no longer claims otherwise.
‼ The run's remaining stall is `Ch24ProbeMode.run` **in Sidney's room at (6,6) AFTER THE WIN** —
`DUMP [STUCK — 18300 frames no progress]`, because the probe has no "advance to the next room"
behaviour. A driver limitation, not this bug: `grep -c 'battle sub-handler'` is **0**.

**All three mechanisms fired** (`POKEBOT_KI93_CENSUS=1`): `DISMISS 12`, `REPICK 26`, `RESET 3`, and the
refused set now ROTATES (`{2}`, `{0,2}`, `{1,3}`, `{0,1,3}` …) instead of filling:
```
[KI93-REPICK] battler=0 slot 2 was REFUSED -> 0
[KI93-REPICK] battler=0 slot 2 was REFUSED -> 1
[KI93-REPICK] battler=0 slot 2 was REFUSED -> 3
```

**THE FIX, BOTH HALVES** (`modules/battle_action_selection.py`):
* **(a) DISMISS, GATED ON THE PRINTER'S OWN STATE.** The `CompleteOnInactiveTextPrinter*` branch was a
  bare `yield; continue`. A message ending in `\p` parks the printer in `RENDER_STATE_CLEAR` awaiting
  an EDGE-TRIGGERED `JOY_NEW(A|B)`, and `gTextFlags.autoScroll` is FALSE outside link battles ⇒ **no
  timeout, ever.** It now presses **B** on one frame in twelve while
  `get_text_printer(0).state == TextPrinterState.WaitForButton`.
  ⛔ **Never gate this on a frame count** — a press delivered while glyphs are still printing is eaten
  as a text speed-up and is not the dismissal press. The printer state is the only honest signal, and
  `modules/modes/_listeners.py:168-170` already used exactly this test.
  ⭐ **B, not A:** `gMoveSelectionCursor` is NOT reset when the menu re-opens, so a stray A re-commits
  the very move that was refused; a stray B falls back to the action menu, where B is inert in a
  single battle.
* **(b) DO NOT RE-SUBMIT A REFUSED SLOT.** Dismissing alone only converts the hang into a livelock —
  the engine returns to `STATE_WAIT_ACTION_CHOSEN` and re-emits `CHOOSEMOVE`. `_ki93_refused_slots` is
  **MODULE-LEVEL**, because the census measured the handler being RE-ENTERED five times per refusal
  episode; a function-local (the design this entry carried for a day) is destroyed between every pick.

**⭐⭐ IT IS A CLASS FIX, NOT A TORMENT FIX.** 61 battle strings end in `\p`; every one of them would
have hung in that branch. The refusal vocabulary covers Torment, Disable, Taunt, Imprison,
Choice-lock and no-PP (`KI93_SELECTION_REFUSAL_SCRIPTS`).

**ORDINARY-CASE A/B (the correct instrument here, unlike `KI-95`):** this change touches the wait
branch and the committed-slot path that EVERY battle executes, so the decision sequence must be
unchanged.
✅ **BYTE-IDENTICAL** (first arm, before the identity fix): 9 decisions, md5 `fd23c131a39df57fde5130791772fa7a`.

**RE-RUN AFTER THE IDENTITY FIX** (the code changed, so the earlier arm no longer describes it): ✅ **BYTE-IDENTICAL.** `post_return.ss1 --driver ch23exit --frames 120000`, 9 decisions, every one `(TurnAction.UseMove, 1)`, md5 `fd23c131a39df57fde5130791772fa7a` on BOTH arms (baseline captured before the fix; after-arm captured 2026-09-06 with it). ‼ **That proves HARMLESSNESS, never efficacy** — efficacy is the drive above, and the two are separate claims.

**⭐ THE ADDITIVE ARGUMENT:** the press fires only when the printer reports `WaitForButton`. Ordinary
battle messages auto-advance and never enter that state, so in a normal battle the new code is inert.

---

## (P4) STAGE 1 + STAGE 2 — the Slugma/Winona box-counter drives (archived 2026-09-07)

Moved out of `04-HANDOFF.md` for its line budget. The work CLOSED 2026-08-15 with all
four cells passing on both forks. Kept verbatim because each arm records WHICH
expectation it is graded against — `pid_match` means "matched THIS ARM's expectation",
so both arms PASS when the code is correct.

```
# --- (P4) STAGE 1 — the Slugma/Winona bug, live, BOTH ARMS. Needs a ROM; ~3 min each. ---
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver boxcounter --frames 200000
#   ARM B (this command, hook unset): expect `-> <pid>` and ACCEPTANCE: PASS.
POKEBOT_BOXCOUNTER_TYPEONLY_A=1 PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver boxcounter --frames 200000
#   ARM A (pre-fix): expect `-> None` and ACCEPTANCE: PASS — its expectation IS None.
#   ‼ BOTH ARMS PASS when the code is correct; `pid_match` means "matched THIS ARM's expectation".
#   ‼ Grade by `grep "boxcounter]"` — a driver that throws at f0 still produces a clean [done] line.

# --- (P4) STAGE 2 — the REAL heal collects the counter. ~4 min each. ⛔ ANCHOR IS THE GYM WEDGE:
#     `ch13_fortree_door.ss1` is on ROUTE120, which `calculate_path` reads as a WALL (KI-24), and
#     the run dies on its first leg with "Cannot reach FORTREE_CITY". This is measured, not feared.
PYTHONUTF8=1 py -3.12 story_harness.py fortree_gym_wedge.ss1 --driver boxcounter2 --frames 400000
#   ARM B: expect moved=True knows_rock_throw=True lead_is_counter=True noop_attributed=True,
#          ACCEPTANCE: PASS. Production prints `depositing Skitty L17` to make room — that deposit
#          is REPORTED, never graded.
POKEBOT_BOXCOUNTER_TYPEONLY_A=1 PYTHONUTF8=1 py -3.12 story_harness.py fortree_gym_wedge.ss1 --driver boxcounter2 --frames 400000
#   ARM A (the user's derail, reproduced): expect _hunted_counter_pids=[] and
#          still_boxed=True not_in_party=True, ACCEPTANCE: PASS — and NO deposit at all.
#   Add `--build custom` to either for the other fork (all four cells pass as of 2026-08-15).
#   ‼ Stage 2 SUBCLASSES Stage 1, so each run re-proves Stage 1 first — read the STAGE-1 GATE line.
#   ⛔ The gym leg is OFF by default and REPORTED-NOT-GRADED: POKEBOT_BOXCOUNTER2_GYM=1 enables it.
```

---

## KI-80 — the counter-ladder gate recipe (archived 2026-09-07)

Moved out of `04-HANDOFF.md` for its line budget. The check itself is **gate #13**
(`repro_boss_grass_gate.py`) and runs on every suite, so this hand recipe is history.
Kept verbatim because it records the THREE ARMS and the exact anchor they need.

```
# --- KI-80 — the counter-ladder gate, THREE arms in ONE run. ~40s. ⛔ ANCHOR MUST BE THIS SAVE:
#     it is NO_ANSWER (condition 7) AND team_max 28 <= wild_max 27 + 8 (condition 9). Both named
#     alternatives FAIL one of those: `fortree_gym_wedge` has a credible answer (Castform scores
#     160 >= 75), and `ch13_fortree_door` has team_max 39, which makes the A/B VACUOUS.
PYTHONUTF8=1 py -3.12 story_harness.py batch2_run04_wedge.ss1 --driver ki80ladder --frames 2000
#   ⛔ EXPECT `ACCEPTANCE: FAIL` — AND THAT IS THE HEALTHY ANSWER SINCE THE FIX SHIPPED.
#     This command grades the OLD, COUPLED expectation, so GRASS_STRONG now correctly reads
#     `-> LADDER expected PLAIN_ESCALATION`. Its FAIL is what PROVES the decoupling changed
#     behaviour. ‼ It said "Expect ... ACCEPTANCE: PASS" until 2026-08-16 and was inverted by the
#     fix — a cold-start audit caught it grading a healthy tree as broken.
#   ‼ THE DRIVER EXITS 0 EVEN ON FAIL — it is a harness driver, not a gate. GRADE THE
#     `ACCEPTANCE:` LINE, never `$?`. Grep with `grep "ki80ladder]"`.
POKEBOT_KI80_ARM4=1 PYTHONUTF8=1 py -3.12 story_harness.py fortree_gym_wedge.ss1 --driver ki80ladder --frames 2000
#   ⛔ ARM 4 — THE MIRROR-REGRESSION GUARD. Run BEFORE and AFTER the decoupling; must PASS both
#     times (OUTCOME=PLAIN_ESCALATION). Needs THIS save (HAS_ANSWER); the driver FAILS by name
#     on the wrong one, because arms 1-3's save cannot reach the `:1925` line it watches.
POKEBOT_KI80_DECOUPLED=1 PYTHONUTF8=1 py -3.12 story_harness.py batch2_run04_wedge.ss1 --driver ki80ladder --frames 2000
#   ✅ THE AFTER RUN, AND IT NOW PASSES — the ladder IS decoupled (2026-08-16). All three arms
#     reach LADDER. ‼ It said "Expect FAIL TODAY" until the fix shipped; seeing PASS is correct and
#     is NOT a sign the discriminator stopped discriminating. The proof that it still discriminates
#     is the command ABOVE, which correctly FAILS against the old expectation.
#   Fault-test kept for reference — the VACUOUS fixture this file once prescribed:
#     PYTHONUTF8=1 py -3.12 story_harness.py ch13_fortree_door.ss1 --driver ki80ladder --frames 2000
#     -> `ACCEPTANCE: FAIL … THE A/B WOULD BE VACUOUS`, and ALL THREE arms come back LADDER.
#   Transcripts: tools/story-dev/evidence/2026-08-15-ki80ladder-*.stdout.txt

PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver boxwrite --frames 200000
PYTHONUTF8=1 py -3.12 probe_box_contents.py ch13_fortree_door.ss1
#   READ-ONLY dump of EVERY box + party slot: species, level, PID, types, full moves, and per mon
#   `type_match`/`move_match` against NEEDED. Takes any save name (defaults to ch13_fortree_door).
#   ‼ This is what turned "the anchor's box might matter" into a measurement: it found the boxed
#   Castform whose Powder Snow (Ice) qualifies it as a counter, sitting AHEAD of any injected mon.
PYTHONUTF8=1 py -3.12 story_harness.py ch13_fortree_door.ss1 --driver partypids --frames 200000
#   READ-ONLY identity dump (party + box: species, level, PID) — flags shared PIDs. On this save
#   it prints the REAL KI-78 twin pair: Shedinja L30 and Ninjask L29 both pid=42207D6F.
#   Proves `debug_write_box_slot` writes a box slot the PRODUCTION reader can read. ACCEPTANCE: PASS.
```

---

## `KI-95` — the full resolution (archived 2026-09-07)

Archived once the fix shipped and gate #39 was green. Kept because it records WHY the
ranking was extracted into a pure function: this chooser had three index-space bugs and
was untestable without a ROM, a live battle and a staged faint.

### ✅ 2026-09-06 — FIXED IN THE SANDBOX, GATED, AND FAULT-TESTED. ⛔ NOT PROMOTED.

**What changed** (`sandbox-pokebot/plugins/custom_modes/story_mode.py`): the ranking is extracted into
a module-level **pure function `rank_replacement(candidates, foe_types, foes, damage_of)`**, and the
offensive term is now **expected damage** from the SHIPPED formula
`BattleStrategyUtil.calculate_move_damage_range` — which already accepts a party `Pokemon` as the
attacker, and which `decide_turn` a few lines below already trusts. No second damage model was written.

**Three things the fix corrects that the report above did not name:**
* **Immunity abilities.** A Ground move against a **Levitate** foe used to score `1.0`; the shipped
  formula returns 0 damage, so it now scores 0.
* **`banned_moves`.** The chooser ranked a mon on moves `decide_turn` would then REFUSE to use —
  `battle.yml:23-27` bans Fly/Dive as 2-turn moves. ⇒ *a move's value is only real if the policy can
  deliver it* (`08-MISTAKES.md`).
* **Ties.** Two mons holding the same-typed move used to tie regardless of power and fall through to
  HP fraction.

**Evidence — `tools/story-dev/probe_faint_chooser_rank.py`, GATE #39, offline, no ROM, 0.6 s.**
7 cases, and the fault arm is the reason it can be believed:
```
clean                             -> 7/7 PASS, exit 0
POKEBOT_KI95_PROBE_FAULT=legacy   -> EXACTLY C1 red, C2-C7 green, exit 0 ("the probe detects the defect")
```
The fault arm feeds the ranker the **pre-KI-95 metric** as its damage function, and C1 then picks
`A/Ember-40` — the wrong answer this KI describes. ⇒ **the probe was RED before the fix and is GREEN
after**, which is what makes it a measurement rather than a demonstration.

⛔ **WHAT THE PROBE DOES NOT PROVE.** It injects its OWN damage function, so it tests the RANKING, not
the integration with `calculate_move_damage_range`. The integration is argued from the fact that
`decide_turn` already calls that method with the same argument shapes — that is an ARGUMENT, not a
measurement, and the live confirmation is the `metric=damage estimates_ok=<n>` field now printed in the
`[FAINT-CHOOSER]` telemetry on every real faint. ‼ **If a live log ever shows `metric=legacy`, this fix
is NOT running** and the entry above is again true at runtime.

---

## `KI-63` — the full entry (archived 2026-09-07)

Resolved 2026-08-13; archived for `05-KNOWN-ISSUES.md`'s line budget. Kept verbatim
because it records how a BLOCKER was dissolved by checking rather than by building.

## ✅ KI-63 — RESOLVED 2026-08-13. The bot acquires DIVE BY PLAYING. (filed 2026-08-12)

> **`--driver divelearner` → `ACCEPTANCE: PASS` on the first drive.** Nothing injected: a slot was
> freed, a **Marill L13** was hunted and caught (balls 19→17), and **Dive was taught over Defense
> Curl** — the 0-power move, exactly what the expendability picker should pick.
> `knows_dive=True can_dive=True surf_intact=True can_continue=True`, and **Zigzagoon kept Surf**.
>
> **What had to be BUILT:** `pc_trip.deposit_one_dead_weight()` — because **neither** existing
> deposit path can free a slot *before* a catch (`withdraw_from_box` returns immediately with
> nothing boxed; `deposit_dead_weight_if_worth_it` is a silent no-op behind
> `POKEBOT_PC_ROTATION`). ‼ Our own handoff named the first of those as the path to use; that is
> retracted. Wired as an opt-in `_needs_party_slot` piggyback inside `heal_in_pokemon_center`.
>
> **‼ ORDER:** call `ensure_hm_learner` FIRST and deposit only on the specific *"party is full"*
> failure — `hm_learner_slot` is checked *before* the party-full check, so deposit-first would
> spend a PC trip and a team member even when no catch was needed.
>
> ## ✅ WIRED INTO PRODUCTION 2026-08-13 (later) — the caveat below is now RESOLVED **in sandbox**
> `early_game.ensure_hm_learner_making_room` sets the flag and retries once; both `story_mode.py`
> call sites (Rock Smash HM06, Surf HM03) now use it. Driven: `ACCEPTANCE: PASS`, with the deposit
> asserted **by PID** (`deposited_pids=[1556928702]` = Skitty). New gate
> **`repro_hm_slot_wiring.py` (22/22, fault-injected)** keeps the chain connected.
> **MEASURED WORTH:** 20 terminal run-kills in 1,129 runs (**0.91%** excluding a reverted
> party-cap bundle), **#1 of 14 derail causes by frames per event (1,717k avg)** — 7.2% of all
> derailed lane time from 3.4% of derails, every one of them five badges deep.
> ⛔ **`custom-pokebot` IS STILL INERT** — it reads the flag but nothing there sets it, and its
> `story_mode.py` still calls the bare function. **Promotion has NOT been asked for.**
>
> ### (the caveat as it stood before the wiring)
> **The CAPABILITY is proven; PRODUCTION IS NOT WIRED.** `_needs_party_slot` has **no setter
> anywhere in `modules/` or `plugins/`** — only `--driver divelearner` sets it (verified by grep).
> So in a real `StoryMode` run the piggyback **never fires**, `ensure_hm_learner(HM08)` still
> raises *"the party is full"*, and the chapter still ends there. **Wiring `story_mode.py` to
> catch that error and set the flag is the remaining work.** Flagged by adversarial review, which
> was right to insist it be stated rather than implied.
> ‼ §Ch21 also still has to be BUILT as a chapter; this removes its blocker. The learner is a **Marill L13, 36 levels below the team** — an HM slave that
> `find_dead_weight` would want to box on a later trip unless the sole-carrier exemption covers it.
> And the ground used is Route 117 (10%, L13, 1,055 waypoints); the better Shoal Cave ground was
> deliberately NOT adopted, because `_hm_hunting_grounds` reads `TRAINING_GRASS` and a Shoal row
> flips `best_training_area` for every team from ~L30 up. See
> `ai-research-notes/2026-08-13-ki63-dive-learner-acquisition-plan.md`.

### (original filing, kept for its measurements)

---

## `KI-45` — the original battle move-menu hang (archived 2026-09-07)

Fixed 2026-08-02; archived for the line budget. Kept verbatim because it is the first
member of the unbounded-battle-loop family that later produced `KI-47`, `KI-93` and
`KI-96`.

## KI-45 — ✅ **FIXED 2026-08-02.** A battle MOVE-menu loop hung a lane indefinitely and neither guard could see it. **FULL ENTRY ARCHIVED VERBATIM to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-09-05** (no loss, no orphan — both invariants asserted before writing). ⛔ Retired only to keep this current-state file inside its 3000-line budget. ‼ **PRECISELY WHAT MOVED:** the ORIGINAL 2026-08-02 diagnosis block. **The `### KI-45 — FIXED 2026-08-03` write-up below did NOT move and is still in THIS file** — the archiver stops at a `###` sub-heading, so a `##` entry containing one is split there. *(superseded: this read "the diagnosis and the fix are intact in the archive", which a Tier 1 reviewer refuted by opening both files.)*

**2026-09-05 — body retired, status re-confirmed unchanged.** KI-45 is CLOSED and stays closed. ⭐ Read it before touching `KI-90`: it is the same SHAPE — a battle-path loop that hung a lane while every guard reported healthy.
### KI-45 — FIXED 2026-08-03 (bounded + reported through the recoverable channel)

**Root cause: stock `battle_menuing._select_in_menu` is `while True:`.** It presses a direction
until the cursor read equals the target. If the menu is not actually open, or the read returns
anything outside 0..3, no press can change it — and the movement logic still picks a direction
every iteration: `current_index=5` with `target_index=0` matches
`current_index > 1 and target_index <= 1` and presses **"Up" forever**.

**Measured cost, twice:**
| | dumps | effect |
|---|---|---|
| batch6 lane H4 | 866 | 27 min silent, ~half the lane's output lost |
| batch9 lane H6 | 1,430 | **0 runs completed in a 180-minute batch** |

**Fix:** `_MAX_CURSOR_STEPS = 60` (~180 frames; a real selection needs ≤3 presses, so ~20×
headroom and ~1% of the watchdog window). On exhaustion it reports through
`battle_fault.request_mode_recovery()` — one recoverable derail for a mode that opted in —
and only raises `BotModeError` when no mode can handle it, preserving stock behaviour.

‼ **The message carries the last cursor value, because THAT is the diagnosis.** An
out-of-range value means the menu was never open; a stuck in-range value means the presses are
not landing. Without it the next reader is back to guessing, which is what cost two lanes.

**Repro:** `repro_ki45_cursor_bound.py` — **drives the real generator** against a stuck cursor
rather than asserting on source text, so a regression to `while True` hangs the test instead of
passing it. Also asserts a normal selection still completes in ≤4 presses.

‼ **Why nothing else caught it, worth keeping:** the global watchdog needs an UNCHANGED
progress signature and a menu loop keeps changing map/coords/state; the per-run frame budget
is KI-36's documented hole ("cannot fire while a battle handler is on the stack"). **Two
independent guards were both structurally blind to the same loop.** Any new `while True` on
the battle path has no safety net but its own bound.

---

> 📦 **KI-46 moved to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-13** — FIXED same day, 2026-08-03.

---

## `KI-96` — the three census drives and two refuted hypotheses (archived 2026-09-07)

Archived once the stale-array INVARIANT superseded them. Kept in full because the way two
confident root causes were measured false — each within an hour of being published — is
more instructive than either. Both were caught by re-checking a fresh claim against new
data, not by re-reading the argument.

**🔶 2026-09-07 — TWO CENSUS DRIVES. THE FIRST LOOKED LIKE A ROOT CAUSE; THE SECOND REFUTED IT.**
`[KI96-CTL]` fired in both, so both are valid measurements.

**DRIVE 1 — the refusal, and the target's identity:**
```
f5862188 [KI96-INDEX] requested party index=2 -> mapped menu in_battle_index=0
                      | slot2=Mightyena#5C96EA9B L60 184/184 | party_size=6
f5862270 [KI96-SPIN] n=1     instr='BattleScript_DoTurnDmgEnd' bt='What will DIVER do?'
f5864069 [KI96-SPIN] n=1800  instr='BattleScript_DoTurnDmgEnd' bt='What will DIVER do?'   (unchanged)
```
⛔ **THE TARGET IS NOT THE PROBLEM.** Mightyena is **L60, 184/184, not fainted, not the active mon**.
Every "is the switch legal?" theory is dead — the game refuses a perfectly legal Pokémon.
⇒ From `index=2 -> 0` I concluded the mapping was aiming at the ACTIVE battler (party 0). **That
conclusion was published and it is WRONG.**

**DRIVE 2 — the array dump that refuted it:**
```
f5862188 [KI96-ORDER] raw=201345  decoded_battleorder=[2, 0, 1, 3, 4, 5]  (battle_pos -> party_index)
                      active_battler_party_index=0   => menu slot 0 holds party 2
```
⇒ **Battle position 0 holds PARTY INDEX 2 — Mightyena, the intended target.** So
`map_battle_party_index(2) -> 0` is **CORRECT**, and the ACTIVE battler sits at position **1**, not 0.
⭐ **The conversion is NOT the bug.** The cursor is aimed at the right entry and the game still refuses.

**‼ THIS IS WHAT `08-MISTAKES.md` RULE 10 IS FOR, AND IT JUST PAID FOR ITSELF** — *when a fix is a
coordinate conversion, MEASURE ITS DIRECTION FIRST; a backwards conversion is worse than the bug it
replaces.* An index-space story that merely FITS the symptom is worth nothing until the array is read.
⛔ **AND A DOC HAZARD TO NOTE:** the wrong conclusion reached `04-HANDOFF.md` and commit `eb5abec3`'s
message before the refutation existed. Worse, a line-budget compression then DELETED it from this file
while those claims stood — *deleting text never breaks a gate's count*, so nothing flagged the
divergence. ⇒ **when trimming for a budget, re-read what the replaced span actually contained.**

**DRIVE 3 — the stage trace. EVERY STEP BEFORE THE LOOP IS CORRECT:**
```
f5862188 [KI96-STAGE] 0 before scroll_to_battle_action(2): state=BATTLE      actioncursor=0
f5862194 [KI96-STAGE] 1 after  scroll_to_battle_action(2): state=BATTLE      actioncursor=2
f5862199 [KI96-STAGE] 2 at the A press (same frame):       state=BATTLE      actioncursor=2
f5862270 [KI96-STAGE] 3 after scroll_to_party_menu_index(0): state=PARTY_MENU actioncursor=2
```
⇒ the action cursor reaches **2 (POKéMON)**, the A press is issued there, and **the PARTY MENU GENUINELY
OPENS** (`state=PARTY_MENU`). Combined with `[KI96-ORDER]` (menu slot 0 really is the target), **every
step up to the loop is correct.**

**⇒ ⭐ THE FAULT IS INSIDE THE PARTY-MENU INTERACTION, AFTER A IS PRESSED ON THE RIGHT ENTRY.** Not the
aim, not the mapping, not the target's legality, not the menu failing to open. That is a much smaller
box than this KI started with.

**⛔ AND `bt='What will DIVER do?'` IS A RED HERRING — RETRACTED.** `gDisplayedStringBattle` retains the
LAST battle string written; it is not proof of what is on screen. The earlier note that "the state and
the screen disagree" rested on reading it as live. `state=PARTY_MENU` is the reliable signal, and it
says the menu is open.

**⚠ ONE LABELLED HYPOTHESIS FOR THE NEXT MEASUREMENT — IT IS A GUESS AND IS MARKED AS ONE.** In Gen 3,
choosing a Pokémon in the battle party menu opens a small submenu (SHIFT / SUMMARY / CANCEL). The loop
presses A blindly every other frame; if the cursor sits on SUMMARY it opens a screen, and if on CANCEL
it backs out — either way `state` stays `PARTY_MENU` and the switch never completes. ⛔ **DO NOT ACT ON
THIS PARAGRAPH.** Tonight a root cause that merely FIT the symptom was published and then measured
false; log the submenu's existence and cursor before believing it.

**✅✅ 2026-09-07 — THE CONTROL ARM ARRIVED FROM THE LIVE x8 BATCH, AND IT SHARPENS THE CONDITION.**
Three census drives had produced three refusals and ZERO acceptances, so there was nothing to compare
against. The 8-lane batch (`20260907-073620`, `--build custom`, census armed) produced **250 rotation
attempts across all 8 lanes, and ALL 250 WERE ACCEPTED** (`[KI96-DONE]` = 250, each spinning ~1 frame).

| | `_battler_party_order` | mapping observed | outcome |
|---|---|---|---|
| **250 accepted** (batch) | `[0, 1, 2, 3, 4, 5]` — IDENTITY | `2→2`, `1→1`, `3→3`, `4→4` | ✅ accepted, **0 mis-aims** |
| **1 wedged** (`ch23chapter`) | `[2, 0, 1, 3, 4, 5]` — **PERMUTED** | `2→0` | ⛔ hangs |

⇒ ⭐⭐ **THE CONDITION IS NOW MEASURED: `KI-96` FIRES ONLY WHEN THE BATTLE ORDER HAS BEEN PERMUTED —
i.e. only after a PRIOR SWITCH in the same battle.** In all 250 accepted cases the order is untouched
and the mapping is the identity, so it is trivially correct; **the wedge is the only observed case where
`map_battle_party_index` did any real work.**

‼ **HONEST WEIGHTS: the accepted side is n=250 across 8 independent lanes; the wedged side is n=1.**
The CONDITION (permuted ⇒ wedge) is a strong lead, not an established law — one observation cannot
establish a rate, and a second permuted case must be captured before anyone builds on it.

⭐ **AND IT EXPLAINS THE STRATEGY SPLIT.** `LevelUpTravelBattleStrategy.decide_turn` never returns
`RotateLead` in a TRAINER battle, so every one of the 250 is a WILD-battle rotation — where a prior
switch is rare and the order stays identity. The chapter drivers bypass that mitigation and reach
`DefaultBattleStrategy`, which rotates in long trainer fights where a prior switch is normal.

⭐ **THE NEXT MEASUREMENT IS NOW CHEAP AND EXACT:** find a PERMUTED-order rotation. Either grep the
batch for any `[KI96-ORDER]` whose decoded order is not `[0,1,2,3,4,5]`, or force a second switch in
one battle. ⛔ Do NOT change `map_battle_party_index` until a permuted case is observed twice — this
KI has already had one confidently-published root cause measured false.

---

## 📦 ARCHIVED 2026-09-07 FROM `03-PUNCH-LIST.md` — `#24-ch23chain` (VERBATIM, nothing edited)

Moved only to keep 03 inside its 3600-line budget (`lint_docs.py` R3). The item is CLOSED;
its stub in 03 keeps the slug, the status and the do-not-redo warning.

### ✅ `#24-ch23chain` — **CLOSED 2026-09-05: §Ch23 COMPLETES END TO END.** `ACCEPTANCE: PASS`, `done=True`, `battles=16`, `whiteouts=0`, `failure=None`. ⛔ DO NOT REOPEN OR RE-DRIVE TO CHECK. The five steps: repro → `KI-90` fix → chain drive (found attrition) → the (33,16) bypass (A/B-proven) → the chain re-drive, which exposed and fixed a ₽2,387 shortfall the bypass caused. (opened and closed 2026-09-05)

✅ **BUILT AND WIRED (⛔ do not rebuild):** `victory_road.ch23_chapter_done()` +
`do_victory_road_chapter()`, and the Segment 23 dispatch in
`plugins/custom_modes/story_mode.py:3779-3795`. Driver `--driver ch23chapter`.

✅ **TWO ARMS PASS, AND THE SECOND IS THE ONE THAT MATTERS:**
* **resume-safety** — from `post_league_shop.ss1` (the chapter's END state): `ACCEPTANCE: PASS`,
  self-skips, `neighbours_reachable=4`.
* ⭐ **PREDICATE DISCRIMINATION** (`POKEBOT_CH23_PREDICATE_ONLY=1` on `post_wally.ss1`):
  `inside_victory_road=True  flag_only(DEFEATED_WALLY_VICTORY_ROAD)=True  gate(ch23_chapter_done)=False`.
  ⇒ a flag-only predicate would have declared the chapter DONE with the bot standing on
  VICTORY_ROAD_1F and six legs to go — the §Ch15/§Ch18/§Ch19 stranding shape, **falsified by
  measurement rather than argued away.**
  ‼ **THE CHEAP ARM ALONE PROVES NOTHING HERE:** on the end fixture the flag and the gate AGREE, so
  a flag-only predicate passes it identically. Keep both arms.

⛔⛔ **WHAT IS *NOT* PROVEN: THE CHAIN.** The end-to-end drive from `post_wally.ss1` ran ~66k frames,
fought its way through Victory Road, and then died on **`KI-90`** — an uncaught `RuntimeError`
("Cannot attack the left-side opponent Pokémon because there isn't one") from the SHARED battle path
that empties the controller stack and hangs the run. ‼ **NOT a defect in the orchestrator, and not
catchable by it:** the raise happens inside `BattleListener.fight`, a **SIBLING** controller — and
that is the operative fact, not the exception type. From that stack position **every** exception,
`BotModeError` INCLUDED, unwinds to `modules/main.py`, where BOTH `except BotModeError` (`:151-153`)
and the bare `except Exception` (`:158`) call `set_manual_mode()`.
⇒ ⭐ **A RECOVERY LOOP ONLY CATCHES WHAT REACHES ITS OWN STACK.**
*(superseded 2026-09-05: this read "it is a `RuntimeError` where every story recovery catches
`BotModeError`" — which invited exactly the wrong fix, changing the exception type. See `KI-90`.)*

⭐ **A REPRO SEED ALREADY EXISTS — BUT ONLY ON THE MACHINE THAT RAN THE DRIVE.** The harness
auto-saved stall states inside the failing battle: `saves/stalls/repro-ml-f63425.ss1` (bt=`CASTFORM
fainted!`, ~3.3k frames BEFORE the raise — **the useful one**, since a repro must fail FIRST) and
`repro-ml-f68406.ss1` (1.7k frames AFTER, i.e. the already-hung state, which proves nothing).
⛔⛔ **`tools/story-dev/saves/stalls/` IS GITIGNORED (`.gitignore:39`) — THESE FILES DO NOT TRAVEL.**
This project is worked from multiple computers, so a session elsewhere will NOT have them and must
REGENERATE them by re-running `--driver ch23chapter post_wally.ss1 --frames 600000` and reading the
`SAVED stall state` lines. ‼ Do not treat the paths above as a fixture pin.

✅✅ **STEP (2) IS DONE 2026-09-05 — THE FIX IS WRITTEN AND GATE #38 SELF-RETIRED.** `battle_action_use_move` aims at the RIGHT opponent when the left is absent; the decision and its rejected alternatives are in `06-DECISIONS-LOG.md` 2026-09-05. ⚠ **SANDBOX ONLY — promotion to `custom-pokebot/` is the USER's call.** ✅ **STEP (3) WAS RUN 2026-09-05 — AND FAILED AT THE TIME** (steps 4 and 5 then fixed it; the chain now PASSES). *(this read "RE-DRIVEN 2026-09-05 AND IT FAILS FOR A KNOWN REASON: the party LOSES the leg-9 Katelynn+Quincy DOUBLE battle on VICTORY_ROAD_1F and whites out" — **SUPERSEDED THE SAME DAY: the chain now PASSES**, `done=True`, `whiteouts=0`)* (`ACCEPTANCE: FAIL`, `battles=16`, `whiteouts=1`, `outcome=BattleOutcome.Lost` at f67819). ✅ KI-90's fix HELD — same fight, same start frame (f56544) as the previous drive, but no raise and no hang: the bot could act, and lost. ⇒ ⛔ **RETRACTED 2026-09-05 — this read "the wall moved from a BOT DEFECT to a GAME PROBLEM (levelling/strategy)" AND IT IS REFUTED BY THE DRIVE LOG.** It is still a BOT defect: the bot entered the fight with **two mons already at 0 HP** after eight battles with no heal, and **no heal ever runs on this floor**. The opposition is **L43** against our L52/L48/L47/L47. ⇒ the wall moved from ONE bot defect (a hang) to ANOTHER (unwired healing). See `06-DECISIONS-LOG.md` / `08-MISTAKES.md` 2026-09-05. ⇒ ⛔ *(This read "STEP (4) IS NOW THE LIVE ONE: make the party survive that double — level up, avoid the pair, or use items in-battle". **SUPERSEDED 2026-09-05:** "level up" is refuted — the opposition is L43 to our L52/L48/L47/L47 — and "use items in-battle" is impossible here, because in-battle items are unreachable in DOUBLE battles by MRO.)* **See STEP (4) below — ⛔ and note its option (a) (a Poké Center heal before leg 9) was BUILT, DRIVEN AND REFUTED on 2026-09-05: there is no reachable heal between leg 8 and leg 10.** ‼ Two forced 1F trainer fights previously took the party from 35% to 4% with five fainted, so this is the known-hardest stretch of the chapter.

✅ **STEP (1) IS DONE 2026-09-05 — `repro_ki90_absent_left_slot.py`, GATE #38, REPRODUCES IT** (ARM A raises; ARM B proves the FLAG is the cause; ARM C proves the TARGET is). It SELF-RETIRES when the bug is fixed, and both directions of that are fault-proven, so it will not punish the fix. ⇒ ✅ **STEP (2) IS ALSO DONE** — the fix is decided (`06-DECISIONS-LOG.md` 2026-09-05) and written. **STEP (3) IS DONE — the chain was re-driven and FAILED on a lost battle (see above).**

⇒ ✅✅ **STEP (4) IS DONE 2026-09-05 — THE (33,16) BYPASS IS BUILT AND A/B-PROVEN. ⛔ DO NOT REBUILD IT.** `exit_victory_road` crosses at `F1_BYPASS_WAYPOINT = (33,16)` with a guard and fault arm `POKEBOT_CH23_FAULT_NOBYPASS`. **A/B on `post_return.ss1`: bypass `battles=1` (Edgar only, the MANDATORY sight battle at (33,22) — I had wrongly predicted ZERO battles and failed to carry Edgar into the forecast); `NOBYPASS=1` `battles=2`, the extra firing at exactly `(31,17)`.** ⛔⛔ **BOTH ARMS PASSED — THIS PROVES THE BYPASS REMOVES THE ENCOUNTER, NOT THAT IT CONVERTS THE CHAIN'S LOSS INTO A WIN.** `post_return.ss1` enters that fight with Mightyena at **141/141**; the chain arrives at **23/143**. ⇒ ✅✅✅ **STEP (5) IS DONE — THE CHAIN COMPLETES.** `ACCEPTANCE: PASS`, `done=True`, `battles=16`, `whiteouts=0` (was 1), `failure=None`, ending at EVER_GRANDE (18,6). ⭐ `done=True` requires the whole basket in the bag, so the purchase is proven too. ‼ Step 5 also exposed and fixed a **₽2,387 shortfall the bypass itself caused** (two skipped Cooltrainer payouts, ₽4,128); leg 11 now sells the Nugget from an ALLOW-LIST. ⇒ **THIS ITEM IS CLOSED.** 44 wp to (33,16) + 18 wp on to the exit = **62, identical to the direct route**, and cone-free throughout. ⛔ *(This heading read "SPLIT THE PAIR INTO TWO SINGLE BATTLES … both MEASURED reachable" — superseded: the standpoints are reachable and cone-free, but the ROUTES to them both enter (31,17), so the split as specified starts the double it exists to avoid.)* ⛔ **THREE THINGS ARE MEASURED DEAD — DO NOT RE-PROPOSE:** "level up" (the opposition is L43 to our L52/L48/L47/L47), "make the party survive" (too vague, published in error), and **a HEAL before leg 9** (built, driven, REVERTED — `calculate_path` refuses it). ‼ *(This list said FOUR and included "the (33,17) bypass" — **that entry is RETRACTED**: its refusal was an instrument artifact, and the bypass via (33,16) is now the SELECTED fix.)* The root cause is MEASURED and it is ATTRITION — which this step does NOT fix, only stops worsening.** ‼ *(This heading first read "WIRE THE HEALING THAT IS ALREADY BUILT" and pointed at `heal_party_from_bag()`; corrected before commit — the bag is empty by this point and this chapter already heals at Poké Centers. See option (a).)*
**THE MEASUREMENT** (`sandbox-pokebot/profiles/repro-ml/debug-logs/Story-debug-20260905-172610.log:318`): the bot entered the fatal fight with
`[("Swellow",112,136), ("Zigzagoon",48,48), ("Mightyena",23,143), ("Wailord",0,226), ("Sceptile",0,145), ("Castform",103,103)]` —
**Sceptile (L52, our best) and Wailord BOTH already at 0 HP**, after EIGHT battles with no heal. ‼ The line above this one already recorded
*"two forced 1F trainer fights took the party from 35% to 4% with five fainted"* — **attrition was visible in our own notes and was read as difficulty.**
⛔ **AND THE OPPOSITION IS LEVEL 43** against our L52/L48/L47/L47 (decomp, see the note below). **WE WERE NEVER UNDERLEVELLED. GRINDING WOULD NOT HAVE FIXED THIS** —
a stronger party still walks in with its two best mons dead.

**⛔ IT IS A BOT DEFECT: TWO HEALING PATHS EXIST AND NEITHER RUNS HERE** (both verified directly in our tree, not taken from an agent):
1. **Out-of-battle healing is BUILT AND UNWIRED.** `heal_party_from_bag()` — `modules/story/pokemon_league.py:221`, documented live-validated,
   handles Revive and status cures. Its **only** call site in the repo is `tools/story-dev/story_harness.py:14936` (the harness). **No chapter calls it.**
2. **In-battle items are UNREACHABLE IN DOUBLES BY INHERITANCE.** `StoryItemBattleStrategy` (`story_mode.py:520`) overrides `decide_turn`
   (`:464` → `_maybe_use_item` `:466`) but defines **no** `decide_turn_in_double_battle`; doubles resolve up the MRO to `story_mode.py:364`,
   which never calls it. ‼ **Silent by design — no error, the method simply is not there.**

**⭐ AND THE FIGHT IS ONLY A DOUBLE BECAUSE OF HOW WE APPROACH IT.** Decomp: both trainers are `trainerbattle_single` with `.doubleBattle = FALSE`
(`src/data/trainers.h:3899`, `:3911`); it becomes a double solely because BOTH spot us on the same step (`gNoOfApproachingTrainers == 2`,
`src/battle_setup.c:1274-1275`). ⇒ **the battle type — the very thing that disables our item policy — is a consequence of our ROUTE, not of trainer data.**

**THREE OPTIONS, all decomp-verified, ⚠ none yet walked in our harness** — see `ai-research-notes/2026-09-05-ch23-LEG9-KATELYNN-QUINCY-DECOMP.md`:
* **(a) ⛔⛔ REFUTED 2026-09-05 — MEASURED IMPOSSIBLE, DO NOT RE-PROPOSE.** `heal_before_exit()` was written (106 lines + fault arm + registry row), driven, and reverted: `UnreachableDestinationError: Could not find a path from (21/32 @ VICTORY_ROAD_1F) to (15/39 @ VICTORY_ROAD_1F)` — `ACCEPTANCE: FAIL`, `battles=0`, `whiteouts=0`. ⇒ **from the leg-8 landing the entrance arrow warp is UNREACHABLE, so NO heal exists between leg 8 and leg 10.** `#24-ch23attrition`'s *"there is NOWHERE to heal inside Victory Road"* was right and was under-read as being only about B1F/B2F. ‼ A BFS I ran over the cached layout claimed the opposite (*"one 652-tile component"*) and was WRONG — see `08-MISTAKES.md` 2026-09-05: **a flood-fill over cached data is a hint, not reachability; `calculate_path` from a real captured position is.** ⇒ **(b) AND (c) BELOW ARE NOW THE ONLY LEVERS.** *(This option formerly read: "HEAL AT A POKÉ CENTER BEFORE LEG 9 — REUSE THE MECHANISM THIS CHAPTER HAS ALREADY PROVEN TWICE".)* ⛔ **NOT `heal_party_from_bag()`** — that was this item's first prescription and it is WRONG here: `#24-ch23attrition` records the wallet **spent down to ₽1,741 with ONE Potion in the bag**, so bag-healing has almost nothing to spend, and `#24-ch23attrition` also establishes that **there is NOWHERE to heal INSIDE Victory Road**.
  ⇒ ⭐ **THE FIGHT IS ON 1F AT (31,17) — THE SAME ARCHITECTURAL POSITION LEG 6 HEALS FROM.** `heal_before_descent()` (`victory_road.py`, `#24-ch23healdescent`, CLOSED 2026-09-04) goes 1F → south arrow-warp (15,40) → EG (18,41) → `heal_in_pokemon_center(EvergrandeCity)` → back in, and its A/B is **un-healed 32% / 3 fainted vs healed 87% / 0**. Leg 6's heal works *only* because it runs from 1F one warp from the door — **and so does leg 9.** ⇒ build the leg-9 heal as a second call of that same proven shape, not as new machinery.
  ‼ **AND CHECK `#24-ch23wally` OPTION (b) IN THE SAME BREATH:** it records that the faint-replacement ranking *"keeps feeding the L19 Zigzagoon into fights it cannot survive, which is a real slice of the damage taken"* — and **our losing party carried Zigzagoon:L19**. That is a second, independent contributor to the same attrition, already filed.
* **(b) ✅✅ SELECTED 2026-09-05 (late) — AND ITS EARLIER "REFUTED" VERDICT WAS MY OWN INSTRUMENT ERROR.** Re-measured from **(33,16)** (elevation 3, one tile north of the bridge): **44 wp there, cone-free; 18 wp on to the exit, cone-free; 62 total — exactly the direct route's cost.** ⇒ **the pair can be skipped for free.** ⛔ The earlier refusal came from seeding `calculate_path` at **(33,17)**, an elevation-**15** bridge tile: `map_path.py:916` seeds the search with the source tile's elevation and `:859` then forbids stepping onto any normal elevation-3 tile, so the query was malformed, not the map impassable. A real player never carries elevation 15. The probe now keeps that call as a labelled CONTROL. *(The superseded verdict read:)* ⛔⛔ **REFUTED 2026-09-05 — MEASURED DEAD, DO NOT RE-PROPOSE.** *(This read: "SKIP the pair — route via (33,17), which is outside both sight cones. BFS says 61 steps either way: +0 cost.")* `--driver ch23leg9probe` asked our planner from the real leg-8 landing: **(33,17) is reachable (43 wp) but the exit apron is NOT reachable from it** (`PathFindingError`). ⇒ **(33,17) is a dead end.** Both the decomp BFS and my own flood-fill got this wrong the same way.
* **(c) ⚠ AVAILABLE BUT NOT CHOSEN — AND ⛔ ITS APPROACH AS ORIGINALLY SPECIFIED IS REFUTED.** MEASURED: the routes to BOTH standpoints enter the cone at **(31,17)** (`(32,16) 45 wp enters_cones [(31,17)] safe=False`, `(29,16) 46 wp … safe=False`) ⇒ **walking there starts the double the split exists to avoid.** It is rescuable by approaching via (33,16) (hop (32,16)→(29,16) is 3 wp cone-free; exit from (29,16) is 20 wp cone-free), but it then buys two L43 fights with **no heal available**, where option (b) buys none for the same 62 waypoints. ⇒ **revisit only if §Ch24 needs the EXP** — that is `#24-e4healing`/the E4 level gap, not this item. *(The superseded verdict read:)* ✅✅ **SELECTED — THE ONLY SURVIVING LEVER.** Interact from **(32,16)** (45 wp, directly north of Quincy) and **(29,16)** (46 wp, directly north of Katelynn) — both MEASURED reachable by `--driver ch23leg9probe`, neither in a sight cone. Facing South and interacting runs `trainerbattle_single` (decomp: both trainers ARE single; the double is emergent from simultaneous spotting). ⭐⭐ **AND IT IS BETTER THAN AVOIDANCE WOULD HAVE BEEN:** our in-battle item policy is unreachable in DOUBLES only, so fighting them one at a time **turns our healing items back on** — which matters because option (a), the heal, is measured impossible. Afterwards the row is safe: a defeated trainer returns 0 from `CheckTrainer` (`src/trainer_see.c:275-277`).
  ⭐ **AND THE MECHANISM IS NOW PROVEN, NOT INFERRED:** the planner's own 62-waypoint route to the exit steps on **(31,17)** — the exact tile our fatal battle began on, and one of only two tiles both cones cover. ‼ `calculate_path` cannot see trainer sight lines at all (`avoid_scripted_events` consults only `on_enter_event_triggers`; spotting is a per-frame scan in `trainer_see.c`), so this will keep happening wherever a route grazes a cone.
  📦 **HISTORY — NOT OPEN WORK.** *(This read "NOT A FREE WIN … still owed live are …" while option (c) was the selected plan. **Option (c) was SHELVED**: option (b), the (33,16) bypass, shipped instead and the full chain now passes `ACCEPTANCE: PASS` / `done=True` / `whiteouts=0`. ⇒ the items below are owed ONLY IF someone revives the split, and are recorded here so that reviver does not have to re-derive them:)* (i) that interacting from those tiles really starts a SINGLE, and (ii) that the party survives two singles from whatever state leg 8 leaves it in — **there is no heal available to guarantee (ii).**
⇒ ✅✅ **(b) IS SELECTED: ROUTE AROUND VIA (33,16), AT ZERO COST** (44 + 18 = 62 wp, cone-free, identical to the direct route). **(a) is measured impossible** (no reachable heal between legs 8 and 10); **(c) is available but not chosen** — its approach routes enter the cone, and even rescued via (33,16) it buys two L43 fights with no heal for the same 62 waypoints. ‼ *(This line read "(a) AND (b) ARE BOTH REFUTED (measured). (c) IS THE WHOLE OPTION SET" — superseded the same day when (b)'s refutation turned out to be my own instrument artifact; and note it had ALREADY been rewritten once from "(a) is the fix; (b)/(c) are cheap force-multipliers". ⇒ **this one line has now been wrong three times — it is the summary of the option list, and a summary drifts every time an option changes.**)* ‼ *(This line read "(a) is the fix; (b)/(c) are cheap force-multipliers — DO (a) FIRST".)* ⭐ **DO THE PROBE BEFORE THE BUILD:** ask `calculate_path` from a real `post_return.ss1` position whether it will route to the exit apron while (30,17)/(31,17) are avoided, and whether (29,16)/(32,16) are reachable standpoints. **That single probe is what would have saved the heal**, and it is cheap. ⚠ Note attrition is NOT thereby fixed — it is merely un-fixable *here*; the party still arrives at leg 9 in whatever state leg 8 leaves it, so avoiding the fight is the only way to stop it getting worse. ⚠ **(a) does NOT make §Ch24 safe by itself:** §Ch24's gauntlet has no nurse, so the League basket (`#24-e4healing`) remains its own problem — do not let this item's success be read as closing that one.
⛔ **PROBE (b)/(c) LIVE BEFORE BUILDING THEM.** They are decomp BFS results in decomp map-local coordinates; a live walk is cheap and decisive.

*(superseded step list, kept for its reasoning:)* **NEXT STEP, IN ORDER:** (1) build a targeted repro for `KI-90` — ⭐ **A DOUBLE battle whose opponent LEFT slot is ABSENT *AND* whose RIGHT battler also reads
`hp == 0` in the SAME frozen snapshot** — ⛔ **left-absent ALONE IS VACUOUS**: `story_mode.py:261-313`
(`decide_turn_in_double_battle`) already returns `use_move_against_right_side_opponent` when the right
is alive, so that arm runs GREEN and would be misread as "does not reproduce". The raise is the
FALL-THROUGH. ‼ **COMPUTE THE DISCRIMINATOR BEFORE DRIVING:** call the strategy and PRINT the
returned `TurnAction`; if it is `UseMoveAgainstRightSideOpponent`, the arm proves nothing.
⚠ **THREE left-hardcoded producers exist — exercise both of the first two:**
`story_mode.py`'s `_default_target` fall-through; `DefaultBattleStrategy._fight_on`
(`modules/battle_strategies/default.py:345-374`, reached via `_handle_lead_cannot_battle` at
`:243-249` when the actor is below `hp_threshold` with no healthy partner); and `catch.py:60/65`.
⭐⭐ **AND THEIR DISCRIMINATORS DIFFER — DO NOT REPRODUCE #2 UNDER #1's CONDITION.** `_fight_on`'s only `return` is an UNCONDITIONAL `TurnAction.use_move(move)` with no left/right check at all, so **producer #2 raises on LEFT-ABSENT ALONE** — a strictly WEAKER (and cheaper) precondition than producer #1's fall-through, which additionally needs the right battler at `hp == 0`. ‼ Verified by reading `default.py:345-374`.
⭐ **FIXTURE, ALREADY PINNED AND TRACKED:** `saves/ki90_double_absent_seed.ss1`
(md5 `38673954cf2d0da197ccbc4e2acf5499`) — the harness's own auto-saved stall state from ~3.3k frames
BEFORE the raise, copied off the reused `stalls/repro-ml-*.ss1` name that every driver run overwrites.
Fallbacks, both same-map walks: `post_b1f_healed.ss1` → VICTORY_ROAD_B2F, stand on **(25,19)/(25,20)**
between **Dianne (25,18)** and **Felix (25,21)**; or `post_wally.ss1` → VICTORY_ROAD_1F **(30,17)/(31,17)**
between **Katelynn (29,17)** and **Quincy (32,17)**. Both trainers in every pair carry **2** Pokémon,
so **exactly 2 KOs** empty one side (`battle_util.c:2331-2347` scans `gEnemyParty[0..2]` for battler 1).
⚠ **UNVERIFIED — READ IT LIVE FIRST:** whether those pairs are already defeated in those fixtures; a
beaten trainer never approaches (`trainer_see.c:255-273`), so the run would silently prove nothing.
⇒ make it FAIL FIRST. ⛔ **DO NOT hunt a faint-during-move-selection window: that mechanism is REFUTED** (the
`battle_state` byte is a FROZEN snapshot taken before the A-presses), and chasing it would burn a day on a
state that cannot occur. The raise is DETERMINISTIC given an absent left slot, not stochastic; (2) only then decide the fix, and remember the file
is shared upstream ⚠ *(and note: the "`KI-83`/`KI-88`/`KI-89` ruling: route around" this line used to cite **DOES NOT EXIST** — see `06-DECISIONS-LOG.md` 2026-09-05. The real bar is EVIDENCE, not the filename; we have modified that file 8 times, including a hang fix)*;
(3) ✅✅✅ **DONE — the chain COMPLETES.** `--driver ch23chapter post_wally.ss1 --frames 600000` returns `ACCEPTANCE: PASS`, `done=True`, `battles=16`, `whiteouts=0`, `failure=None` (2026-09-05). *(This step read "re-run … and expect the chain to complete".)*
⚠ Do NOT reach for a batch: this is a CORRECTNESS question, so the instrument is a repro.

---

---

## 📦 ARCHIVED 2026-09-07 FROM `03-PUNCH-LIST.md` — `#24-ch23attrition` (VERBATIM, nothing edited)

Moved only to keep 03 inside its 3600-line budget (`lint_docs.py` R3). The item is CLOSED; its stub keeps the slug, the status and the do-not-redo warning.

### ✅ `#24-ch23attrition` — **CLOSED 2026-09-04: the party is back to 807/807 with zero fainted. The fix was a 36-STEP WALK to the League's Poké Center, not the ~5 hours of training I had priced.** ⚠ The Elite Four LEVEL gap is a SEPARATE, still-open question. (filed, dependency-corrected and closed 2026-09-04)

> ⛔⛔ **I HAD THIS BACKWARDS FOR ONE COMMIT, AND THE MEASUREMENT INVERTED IT.** I wrote that the party's condition blocked leg 8. It is the reverse: from the B2F landing **B1F (17,16)** the bot is **TRAPPED ON ITS ISLAND** — MEASURED `--driver ch23retprobe`: `(8,3)` (leg 6's ladder to 1F) **UNREACHABLE**, `(30,25)` (back to B2F) **UNREACHABLE**, `(20,21)` (the 1F ladder) **UNREACHABLE behind the plug**. ⇒ **the ONLY exit is through the plug, so the bot cannot leave Victory Road to heal until LEG 8 is solved.** Training or shopping first is not merely lower-priority, it is *impossible* from here.
> ⇒ **BUILD LEG 8 FIRST.** ⭐ And it is safer than it looks: the pushes and smashes do not fight, the standpoints are 15-18 wp away, and a whiteout on B1F respawns at **EVER_GRANDE — outside Victory Road, healed**, which is an escape rather than a loss.
> ‼ *The lesson: I priced an expensive option (hours of training) and put it to the user before checking whether the bot could even REACH the thing that option required. **Measure the dependency before pricing the remedy.***

- [ ] **THE CURVE, measured not predicted:** `post_training` **95% / 0 fainted** → `post_wally`
      **67% / 2** → *(leg 6 heals)* → `post_b1f_healed` **87% / 0** → `post_b2f` **38% / 3**.
      ⇒ **leg 7 alone costs ~49 points of HP and three Pokémon**, on only `battles=3`.
- [ ] ⛔ **AND THERE IS NOWHERE TO HEAL INSIDE VICTORY ROAD.** The nearest Poké Center is Ever
      Grande's, outside the 1F entrance; the League's own Center is *past* the exit. Leg 6's heal
      works only because it runs from 1F, one warp from the door. ‼ From B1F/B2F the round trip
      costs the **whole boulder solve twice**, because every warp resets the puzzle.
- [ ] **OPTIONS — none of which I should pick unilaterally:**
      (a) **train more on B1F now that it is reachable** (950.8 EXP/battle vs 1F's 775.6 — this was
      always the plan for closing the Elite Four gap, and it would fix attrition as a side effect);
      (b) **buy healing items before entering** — ✅ **DONE 2026-09-04 (leg 11)** *(this line said ₽38,893; the LIVE reading was **₽56,041**, spent down to **₽1,741**)* and the bag holds ONE Potion;
      ⚠ the League 1F Mart (Full Restore / Revive / Max Potion) is PAST Victory Road, so this needs
      an earlier shop;
      (c) ✅ **DONE 2026-09-06 — `#24-ch23wally` option (b) is fixed** (`KI-95`, gate #39, sandbox-only). It had been the faint-replacement ranking feeding the L19
      Zigzagoon into fights it cannot survive, which is a real slice of the damage taken;
      (d) accept it and let leg 8 run on a 38% party — ⛔ leg 8 has its own trainers (Samuel, Halle)
      and its own boulder puzzle.
- [x] ✅✅✅ **ANSWERED 2026-09-04 — AND THE ANSWER NEEDS NO TRAINING AT ALL.** The bot is now OUT
      of Victory Road (`post_vr_exit.ss1`, EVER_GRANDE_CITY (18,28)), and the leg that took it there
      MEASURED where healing is possible:
      **Ever Grande Poké Center (27,49) → UNREACHABLE · Victory Road apron (18,42) → UNREACHABLE ·
      LEAGUE DOOR (18,5) → REACHABLE in 37 wp.**
      ⇒ the exit lands on a **closed plateau**, so *"exit and heal at Ever Grande" is WRONG*; the
      only heal is the **League's own Poké Center**, which also carries a Mart (Full Restore /
      Revive / Max Potion) against the **₽56,041** in hand *(⚠ **₽38,893** as first written here — KNOWN-STALE, the pre-Victory-Road figure; ✅ spent down to **₽1,741** by leg 11).* ⭐ **That fixes attrition AND the empty
      bag in one 37-waypoint walk** — the training options below are no longer the answer to THIS
      problem (they remain the answer to the Elite Four LEVEL gap, which is a different question).
      ‼ This confirms live a claim a research pass had only DERIVED from its own flood-fill, and had
      explicitly flagged as needing a probe.
- [x] ✅✅✅ **DONE 2026-09-04 — `heal_at_league` ships and the party is WHOLE.** `--driver
      ch23heal` `ACCEPTANCE: PASS`, `battles=0`, `whiteouts=0`; **36/807 with five fainted →
      807/807 with none**, fixture `post_league_heal.ss1` (`1a8a0269…`) at EVER_GRANDE_CITY (18,6).
      ⭐ **AND IT FOUND A HIDDEN KILLER:** the party's only conscious member, Mightyena, was
      **badly poisoned** — that is what drained 36 → 24 HP across the walk with ZERO battles, and a
      whiteout on the last standing Pokémon was one or two steps away. An HP-only reading could not
      have explained it; `party_is_healthy()` now reports STATUS too.
      ‼ **The first attempt FAILED and the consequence guard caught it**: the bot reached the nurse
      tile (3,4) facing north and healed NOTHING, because I mashed A at a nurse who asks a YES/NO
      question. `heal_in_pokemon_center` has always done it properly (ONE A, then
      `wait_for_yes_no_question("Yes")`, then ride the script out). ⇒ **when a proven helper exists
      for an interaction, copy its SHAPE, not just its intent — the shape is where the timing
      knowledge lives.**
- [ ] ⛔ **URGENT: THE PARTY IS AT 4% WITH FIVE FAINTED** — only Mightyena is conscious. The two 1F
      trainer fights on the way out nearly wiped it. ⇒ the 37-wp walk to the League door is the very
      next action and must not be delayed. ‼ **Our `PokemonCenter` enum has NO League entry** (only
      `EvergrandeCity`), so `heal_in_pokemon_center` cannot target it as written — that gap is the
      first thing the heal leg must solve.
- [ ] ⭐ **OPTION (a) IS NOW PRICED — measured 2026-09-04 from the CURRENT (post-B2F) party,
      estimate-only, zero frames spent, on 1F at 775.6 EXP/battle:**
      **L50 → 315,260 frames** (~88 min) · **L53 → 705,036** (~196 min) · **L55 → 1,073,317**
      (**~5 hours**). ⛔ **Wallace is L58, so even L55 leaves a gap** — this buys survivability and
      the Elite Four's first three members, not the Champion.
      ‼ B1F is ~18% better ground (950.8 vs 775.6) but every heal round-trip from B1F re-crosses the
      boulder puzzle, so the 1F figures above are the realistic ones. **This is a real cost and the
      USER's call, not mine.**
      ‼ **AND THE ESTIMATE ONLY WORKS BECAUSE OF A FIX MADE WHILE MEASURING IT:** `team_is_ready()`
      read the module constant `TRAIN_TARGET` instead of the caller's target, so
      `POKEBOT_CH23_TRAIN_TARGET=53` printed `PRE reasons=[]` / `train_estimate_total = None` — the
      flag silently did nothing past the readiness gate. ⇒ **a parameter that reaches only half a
      function is not a parameter**, and it is the same defect shape as the six dead fault arms.
- [ ] ⚠ **NOT A TRAVERSAL BLOCKER — a BATTLE one.** VERIFIED: a fainted carrier still works for field
      moves (`ScrCmd_checkpartymove`, `src/scrcmd.c:1713`, skips only eggs and never reads HP), so
      Wailord fainting does not strand the run. ⇒ **do NOT "fix" `assert_carriers_survived` to reject
      fainted carriers** — it is correct as written, and that check would fire on a healthy run.

---

## 📦 ARCHIVED 2026-09-07 FROM `03-PUNCH-LIST.md` — `#24-waterfalltimeout` (VERBATIM)

Moved only to keep 03 inside its 3600-line budget (`lint_docs.py` R3). CLOSED item; its stub keeps the slug and the do-not-redo warning.

### ✅ `#24-waterfalltimeout` — **FIXED 2026-09-04 in sandbox: `[0][1]` → `[1][1]`, direction MEASURED before the edit.** ⚠ Sandbox only — promotion to `custom-pokebot` is the USER's call. (filed and fixed 2026-09-04)

- [ ] ⛔ **THE DEFECT, `modules/modes/util/walking.py:227`:**
      `frames_remaining_until_timeout += 195 + (get_player_location()[0][1] - waypoint.coordinates[1]) * 42`
      `get_player_location()` returns **`(map_enum, (x, y))`** (`modules/player.py:291`), so `[0][1]`
      is the **MAP NUMBER**, not the player's `y`. It must be **`[1][1]`**.
- [ ] **WHY IT IS BOTH TOO SHORT AND TOO LONG, depending on the map:**
      Ever Grande is map num **8**; a climb to `y=59` gives `195 + (8 − 59) × 42 = **−1947**` — a
      **negative** allowance. VICTORY_ROAD_B2F is map num **45** against a waypoint `y` of 14, giving
      `195 + (45 − 14) × 42 = **+1497**` where the right answer is **+69**. ⇒ the same line under- and
      over-shoots on different maps, which is why it never produced a clean, repeatable symptom.
      ‼ *(This bullet first said `−2142` / `+1428` — the un-based terms, one computed from the wrong
      waypoint `y`. Corrected against the committed evidence file; the same wrong figure had been
      copied into `walking.py`'s comment and is fixed there too.)*
- [x] ⚠ **IT WAS LATENT, NOT DORMANT — and the prediction was CONFIRMED.** It had not bitten because
      our legs **hand-drive** waterfall climbs instead of letting the planner emit a `Waterfall`
      waypoint (§Ch23 leg 4 does exactly that; its `NOCLIMB` fault arm exists for it). ✅ **And
      `ch23b2fprobe` then measured `calculate_path` emitting `{Surf: 1, Waterfall: 1}` on the route to
      B2F's exit — so leg 7 really would have been the first planner-emitted waterfall waypoint we
      ever rode.** Fixed before leg 7 was built, as intended.
- [x] ✅✅ **FIXED 2026-09-04, AND THE DIRECTION WAS MEASURED FIRST — not reasoned out.**
      Observe-only reading from `--driver ch23b1fprobe`, standing on VICTORY_ROAD_B1F (8,3):
      `get_player_location()[0][1]` = **44** (the MAP NUMBER — VICTORY_ROAD_B1F is `(24,44)`),
      `[1][1]` = **3** (the player's `y`), ground truth coords **(8,3)**. ⇒ `[1][1]` is correct.
      **THE A/B, computed from those measured values** (base 195, 42 frames per tile of climb):
      Ever Grande climb to y=59 → **old `-1947` frames (NEGATIVE — the timeout expires instantly)**,
      new **`+573`**. VICTORY_ROAD_B2F descent → old **`+1497`**, new **`+69`** (1,428 frames of
      false slack). ⇒ the one line was wrong in BOTH directions depending on the map, which is why
      it never produced a clean repeatable symptom.
      ⚠ **DRIFT 11 → 12** — `walking.py` is now divergent between sandbox and custom. Promotion is
      the USER's call; nothing is owed until they rule.
      ‼ Two gates caught the side effects of this one-line fix that I did not: `audit_doc_citations`
      (my 13-line comment moved `run_in_circle` from :706 to :719) and `audit_doc_consistency` (the
      drift count, in **nine** places across two files, found in four successive rounds).
      ⇒ **grep the tree for the FACT, not for the line the last error named.**
- [ ] **HOW TO PROVE IT (do not fix on inspection alone — this project has shipped three backwards
      index/coordinate "fixes"):** ⛔ **MEASURE THE DIRECTION FIRST** with an observe-only probe that
      logs BOTH `get_player_location()[0][1]` and `[1][1]` beside a ground truth, exactly as the
      2026-08-17 rule requires. Then A/B the timeout value on a real waterfall waypoint.
      ‼ Found by a recon agent auditing our Surf/Waterfall support, and confirmed by reading
      `player.py:291` — an agent's note that turned out to be about OUR code, not the decomp.

---

## 📦 ARCHIVED 2026-09-07 FROM `03-PUNCH-LIST.md` (VERBATIM)

Moved only to keep 03 inside its 3600-line budget (`lint_docs.py` R3). CLOSED item; a stub
in 03 keeps the slug and its do-not-redo warning.

### ✅ `#24-abortrecoveryresiduals` — ALL THREE RESOLVED 2026-08-23 (RETIRED to a summary; full detail in `07-CHANGELOG.md`)

- [x] **(b) and (c): the abort-swallow class is CLOSED in sandbox.** A whiteout raises `StoryAbort`,
      a `BotModeError`, so any broad `except BotModeError:` in story code can absorb the unwind and
      let the bot grind on. (b) guarded the 5 sites `#24-loopheadabort` newly exposed; (c) the 8
      that predate it. An AST pass now finds **ZERO** swallowers; guarded handlers 14 → 22; the
      ratchet went 36 → 31 → 23, **control-armed at each step** (strip the guards and it reads back
      up). Two-arm behavioural proof: latch CLEAR → swallowed, unchanged; latch SET → re-raised.
      ✅ **DONE 2026-08-24: PROMOTED (user-approved) and the custom baseline WAS lowered 36 → 23 in
      the same commit. Drift is **0 — everything is promoted** (2026-09-06, user-approved, driven against `--build custom`). *(This line previously carried the pre-promotion count; that history is in `custom-pokebot/DIVERGENCE-LOG.md` 2026-09-06 — it is NOT repeated here, because `audit_doc_consistency` measures drift and cannot tell a quoted old number from a live claim.)* Pre-promotion detail: `modules/story/pokemon_league.py` joined 2026-09-04 — the §Ch24 out-of-battle party heal; before that ⬆ from 12: `modules/story/overworld_items.py` joined 2026-09-04 — the NEW pure out-of-battle healing policy for `#24-e4healing`, gate #36; before that ⬆ from 11: `modules/modes/util/walking.py`, the `#24-waterfalltimeout` fix; previously ⬆ from 10 on 2026-09-03: `modules/story/victory_road.py`, §Ch23 legs 2-3; previously ⬆ from 8 on 2026-09-02: the NEW `modules/story/sootopolis_gym.py`, §Ch22's chapter module — a new sandbox-only chapter file, exactly as §Ch20 and §Ch21 each did. ⚠ PROMOTION IS THE USER'S CALL and is NOT implied here; run `promote.py --check`, which outranks this text) as of 2026-08-27 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven); both forks now read ZERO AST abort-swallowers.**
- [x] **(a): ASSESSED and CLOSED as VERY LOW — and the finding is that the code was NOT changed.**
      A second whiteout during recovery would be fatal, but it cannot realistically occur: the whole
      window is spent on maps whose land-encounter rate is **0** (all 17 towns + all 32 Poké Center
      maps, with routes as positive controls), `on_whiteout()` cannot fire
      twice on Emerald, and across **16,688 recorded recoveries** it has never once happened.
      ‼ The window is entered 23-36 times per run — this is closed on IMPOSSIBILITY, not rarity.
      ⚠ **RE-OPEN for FireRed/LeafGreen** (a live duplicate-callback path exists there) or if
      respawn moves to a map with a non-zero encounter rate. The proposed fix is recorded in the
      changelog as correct-in-shape and UNPROVEN — **do not ship it without a driven double whiteout.**

---

## 📦 ARCHIVED 2026-09-07 FROM `03-PUNCH-LIST.md` — `#24-brokenrepros` (VERBATIM)

Moved only to keep 03 inside its 3600-line budget (`lint_docs.py` R3). CLOSED item;
its stub in 03 keeps the slug, the status and the do-not-redo warning.

### ✅ `#24-brokenrepros` — DONE 2026-08-23 (RETIRED to a summary; full detail in `07-CHANGELOG.md`)

- [x] **Six `repro_*.py` scripts fixed — the item was filed as FIVE.** A stale line in
      `02-ARCHITECTURE.md` (*"47 pass, 0 fail, 5 environmental"*) named the wrong five and hid them.
      Sweep after: **103 PASS / 0 CHECK / 1 SKIP of 104** (`repro_x4_lanes` skipped — real processes).
      Root causes, one per script: a check asserting a LEAF CLASS NAME where the code had grown a
      subclass; THREE stale `SimpleNamespace` stubs missing `is_double_battle_with_partner`; one
      CWD-dependent repo path; and one that was never broken (122s under a 90s cap).
      ⛔ **The sixth was invisible because a doc said not to run it** — and that same script had been
      written off as "environmental" once before (2026-07-30), also for a stale stub.
      ⇒ spawned **`#24-reprosweepratchet`** (below): none of the 104 is in `run_gates.py`.
      ‼ RETIRED 2026-08-23 from ~56 lines to this summary because `03` hit its R3 line budget. The
      narrative, the per-script measurements and the two refuted "obvious fixes" are preserved in
      `07-CHANGELOG.md` and `08-MISTAKES.md`. ⛔ **Retire by SUMMARISING with a pointer, never by
      deleting** — code and other docs cite these slugs (`audit_doc_citations.py` checks that).

---

## 📦 ARCHIVED 2026-09-07 FROM `03-PUNCH-LIST.md` — `#24-p2headergate` (VERBATIM)

Moved only to keep 03 inside its 3600-line budget (`lint_docs.py` R3). CLOSED item;
its stub in 03 keeps the slug, the status and the do-not-redo warning.

### ✅ `#24-p2headergate` — DONE 2026-08-23 (RETIRED to a summary; full detail in `07-CHANGELOG.md`)

- [x] **TWO checks shipped, a THIRD deliberately DELETED.** (A) editing a `## KI-N` header with no
      line added inside that KI's own section is now a finding — its fault test is the real bug, a
      body line anchored on the header STRING landing ABOVE it. (C) a literal control character in
      `.py` source is a hard failure, because `\b` compiled to a BACKSPACE twice in one day and the
      gate still printed PASS both times; its own test then shipped VACUOUS and mutation testing
      caught that. ⛔ **(B) ratchet-baseline claims was DELETED after a six-angle review returned 7
      blockers — 289 lines removed.** Its exemption was written and broken THREE times; the fix that
      mattered was asking *what does it protect* (a stale figure in a doc that says to run the probe).
      ‼ **Two standing rules came out of it: review depth scales with BLAST RADIUS, and when a
      predicate needs a THIRD exemption the predicate is wrong.** Suite unchanged at 30.

---

## 📦 ARCHIVED 2026-09-07 FROM `03-PUNCH-LIST.md` — `#26-battleitemwedge` (VERBATIM)

Moved only to keep 03 inside its 3600-line budget (`lint_docs.py` R3). CLOSED item;
its stub in 03 keeps the slug, the status and the do-not-redo warning.

### ✅ `#26-battleitemwedge` — HANG closed 2026-08-26 AND LIVE-VALIDATED 2026-08-27 (batch `20260826-185918`: its KI-47 family 2 → 0 over 572 item flows)

**Shipped:** `battle_action_use_item` no longer fires ONE blind A into `scroll_to_item_in_bag`'s
unbounded, press-nothing first wait. It now presses, VERIFIES `GameState.BAG_MENU`, re-presses —
3 bounded attempts (≤ ~90 frames) — and on failure logs the stage and RETURNS, letting the strategy
re-decide: a re-decided turn beats a 3,001-frame KI-47 wedge + derail cascade. Every loop constant-
bounded (verifiable by reading); `[ITEM-FLOW]` stages narrate each attempt.
⚠ HONEST LIMITS: (1) no deterministic repro exists for the eaten-A itself (timing-stochastic) — the
proof is structural boundedness + the instrumented stages, and **the live arm LANDED in batch `20260826-185918` (KI-47 family 2 → 0 over 572 item flows)**
(the `20260826-130441` validation batch ran `dce95b4a`, BEFORE this fix — and its 3 KI-47 nets are
all this family's action-selection signatures, so the next batch has something to measure);
(2) items still failing to be CONSUMED is `#24-battleitems`' open work — this closes only the HANG.
📦 Original filing (the opened-bag freeze anatomy): `07-CHANGELOG.md` 2026-08-26 + git history.

---

## 📦 ARCHIVED 2026-09-07 FROM `03-PUNCH-LIST.md` — `#24-ch23wally` (VERBATIM)

Moved only to keep 03 inside its 3600-line budget (`lint_docs.py` R3). CLOSED item;
its stub in 03 keeps the slug, the status and the do-not-redo warning.

### ✅ `#24-ch23wally` — **CLOSED 2026-09-04: WALLY IS BEATEN.** ✅ Option (b) (the faint-replacement ranking) is **DONE 2026-09-06** — `KI-95`, gate #39, sandbox-only and unpromoted. It had been OBSERVED firing inside the winning run — see the open bullet. (filed, ruled, trained and closed 2026-09-04)

- [x] 📦 **SUMMARISED 2026-09-04 — full narrative in `07-CHANGELOG.md` (three entries, same date).**
      The leg's CODE was never at fault; the PARTY was. The user ruled TRAIN; the target L47 was
      PRICED not chosen (L50 needed 793,882 frames — Wailmer alone 359,683, over the 250,000
      per-call ceiling); the grind only ran at all after **KI-84**. Fixtures: `post_training.ss1`
      (`2f517f1f…`) → `post_wally.ss1` (`76000aa5…`, VICTORY_ROAD_1F (9,15) = the B1F ladder apron).
      ⭐ **THE A/B THAT CLOSES IT, same leg and same code:** untrained → `battles=5`,
      **`whiteouts=2`**, `wally_flag=False`; trained → `battles=6`, **`whiteouts=0`**,
      `wally_flag=True`. ⛔ The win cost 2 faints and left 67% HP.
- [ ] ⚠ **OPTION (b) IS STILL UNTAKEN, and it is no longer theoretical — it was OBSERVED.** The
      faint-replacement ranking (`story_mode.py:210`) weighs `hp_fraction` above LEVEL, and in the
      winning run it fed the **L19 Zigzagoon** into a fight against L40s, where it fainted. It cost
      nothing there because the battlers carried the fight. ⛔ Against the Elite Four — five fights,
      one party, no heal, no escape — the same cascade is a run-ender. ‼ And leg 6 has now shown the
      same drift: the party reached B2F at **32% with THREE fainted**. Tracked here so closing the
      Wally half does not bury it.

---

## 📦 ARCHIVED 2026-09-07 FROM `03-PUNCH-LIST.md` — `#24-ch23healdescent` (VERBATIM)

Moved only to keep 03 inside its 3600-line budget (`lint_docs.py` R3). CLOSED item;
its stub in 03 keeps the slug, the status and the do-not-redo warning.

### ✅ `#24-ch23healdescent` — **CLOSED 2026-09-04: leg 6 now heals before descending, and an A/B proves it (un-healed 32% / 3 fainted vs healed 87% / 0).** (filed and closed 2026-09-04)

- [ ] **MEASURED, NOT PREDICTED — the party gets worse at every stage:**
      `post_training.ss1` 95%/0 fainted → `post_wally.ss1` **67%/2** → `post_b1f.ss1` **32%/3**
      (Sceptile, Zigzagoon, Swellow) — the last two flagged "CANNOT SURVIVE A JOURNEY", and **leg 7
      would start from the worst.**
      ⚠ Leg 6 was driven UN-HEALED **on purpose** (isolate the variable under test); this item is
      the other half of that decision, not a defect report.
- [ ] **THE FIX: heal BEFORE the descent, while the bot is still on 1F one warp from the exit.**
      1F → arrow-warp out (15,40) → EG (18,41) → `heal_in_pokemon_center(EvergrandeCity)` →
      (18,42) → warp in → (9,15) → B1F. ‼ `assert_carriers_survived` after it (deposits ride along).
      ⛔ **PROBE THE ARROW-WARP FIRST.** 1F (15,40) is `MB_SOUTH_ARROW_WARP` — fires only on
      standing + facing South + holding Down, never a step; we have only crossed it INWARD.
- [x] ✅✅ **DONE 2026-09-04 — `heal_before_descent()` ships in `victory_road.py`.** Measured, same
      start fixture and same code: **un-healed → 32% HP with THREE fainted; healed → 87% with
      ZERO.** The heal itself read `538/799 (67.3%), 2 fainted` → **`799/799 (100%), 0 fainted`**.
      `--driver ch23descend` `ACCEPTANCE: PASS`, all 7 readings, `battles=6`, `whiteouts=0`; fixture
      **`post_b1f_healed.ss1`** (`b2eeb15c…`) is now the leg-7 start point.
      ⭐ **AND IT PROVED THE ARROW-WARP OUTWARD** — the untested navigation this item flagged. 1F
      (15,40) is `MB_SOUTH_ARROW_WARP` and we had only ever crossed it inward; it works.
      ‼ It heals from **1F, not B1F**: from below the round trip would cost the whole boulder solve
      twice, because every warp resets the puzzle. Fault arm `POKEBOT_CH23_FAULT_NOHEAL6` keeps the
      un-healed descent reproducible.
- [ ] ⚠ **RELATED, NOT THE SAME:** `#24-ch23wally` option (b) (the faint ranking feeding the L19
      into fights) is the CAUSE; healing treats the symptom. Both open.

---

## 📦 ARCHIVED 2026-09-07 FROM `05-KNOWN-ISSUES.md` — `31-KNOWN-ISSUES-ARCHIVE.md` (VERBATIM)

Moved only to keep 05 inside its 3000-line budget (`lint_docs.py` R3). CLOSED issue; its
stub in 05 keeps the id, the status and the do-not-redo warning. Nothing edited.

## KI-39 — ✅ CORRECTED AND LARGELY RESOLVED 2026-07-31 — the ORIGINAL (refuted) entry now ALSO moved to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-14)

⛔ **Until 2026-08-14 this file kept the 178-line ORIGINAL entry — whose stated cause the archive
explicitly refutes — while the CORRECTION lived in the archive.** A reader absorbed the wrong
analysis in full before reaching this stub. Backwards from the archive rule: the current-state
file keeps the truth, the archive keeps the history. Both halves are now in
`31-KNOWN-ISSUES-ARCHIVE.md`, refutation alongside original.


Archived 2026-08-13 to keep this current-state file inside its 3,000-line R3 budget. Nothing was
deleted — the full correction and its diagnosis are in the archive.

---

---

## 📦 ARCHIVED 2026-09-07 FROM `05-KNOWN-ISSUES.md` — `withdraw_from_box` (VERBATIM)

Moved only to keep 05 inside its 3000-line budget (`lint_docs.py` R3). CLOSED issue; its
stub in 05 keeps the id, the status and the do-not-redo warning. Nothing edited.

## KI-79 — `withdraw_from_box` PRINTED A SUCCESS IT NEVER VERIFIED (2026-08-15, ✅ FIXED, FAULT-PROVEN and PROMOTED TO BOTH FORKS — ✅ ITS RESIDUAL'S INSTRUMENTATION HALF IS DONE **AND PROMOTED TO BOTH FORKS 2026-08-17**; ⚠ THE REACTION HALF IS STILL OPEN, see below) — FULL ENTRY in `31-KNOWN-ISSUES-ARCHIVE.md`

Moved 2026-08-16 on the 3000-line budget. ‼ **Keep only what later work leans on:**
- **The defect:** `pc_trip.py:472-473` printed *"{name} is in the party"* after reading only
  `len(get_party())` — **a COUNT wearing an IDENTITY's clothes.** It now verifies
  `(personality_value, species)` **and** `contains_pokemon`, after a 2-frame yield, and prints a
  loud named failure instead of a green lie. Permanent fault hook `POKEBOT_PCWITHDRAW_FAULT`.
- ‼ **The method rule, which is the reusable part:** a byte-compare was NOT accepted as proof for a
  BEHAVIOUR promotion — a **THREE-POINT A/B** was (PASS before → FAIL after faulted → PASS after
  unfaulted), and run 1 is unrepeatable once the copy happens, so it runs and commits FIRST.
- ⚠ **THE RESIDUAL — HALF CLOSED 2026-08-17.** ✅ **The verdict now REACHES the caller:** all five
  exits return `(landed, code, detail)`, the ONE caller BINDS it, and a pure `withdraw_verdict_report`
  reports it — proven by a live two-armed A/B (`landed=True code=landed` unfaulted vs
  `landed=False code=did_not_land` faulted) and by gate #26 `repro_withdraw_verdict.py`, which
  **FAILED against the then-unpromoted `custom` tree (exit 1, six named sites) and now PASSES it
  (exit 0)** — that flip IS the promotion's proof.
  ✅ **PROMOTED TO BOTH FORKS 2026-08-17, USER-APPROVED**, in the five-file round; restore point
  `restore/2026-08-17-pre-promotion-all5`, drift 0, and verified by DRIVING custom
  (`--driver boxcounter2 --build custom` printed `verdict landed=True code=landed`).
  ⛔ **PROMOTION DID NOT CLOSE THE RESIDUAL:** production can now READ the verdict in BOTH forks and
  still cannot REACT to it. That half needs the unmeasured `sStorage->messageText` heap offset AND
  a USER ruling. *(This bullet read "⚠ SANDBOX-ONLY; a promotion is the USER's call" for one commit
  after the promotion — a Tier 1 reviewer caught it; the drift gate cannot see PROSE about
  promotion state, only figures.)*
  ⛔ **STILL OPEN: production READS the verdict but does not ACT on it** — what it should DO is the
  USER's ruling and is blocked on an unmeasured `sStorage->messageText` offset. `withdraw_from_box`
  still never raises for a PC problem, which is deliberate and unchanged. Its ONE caller is the
  `yield from` at `higher_level_actions.py:420` (inside the `try:` that opens at `:403`), which
  discards the value. **Tracked as `#24-orphans` item (1)**;
  its instrumentation half is specified, but *how* production should react needs the USER's ruling.

---

## 📦 ARCHIVED 2026-09-07 FROM `05-KNOWN-ISSUES.md` — `early_game.py` (VERBATIM)

Moved only to keep 05 inside its 3000-line budget (`lint_docs.py` R3). CLOSED issue; its
stub in 05 keeps the id, the status and the do-not-redo warning. Nothing edited.

## KI-81 — KI-67's fix was applied to TWO chapters and the CLASS was never swept (2026-08-16, MEASURED by probe). ✅ **8 SITES FIXED AND PROMOTED TO BOTH FORKS** — the PC/heal path and the site that proved the sweep was incomplete. ⛔ **STILL OPEN: candidates remain (ALL in `early_game.py`)**, and ✅ **THE PROBE IS NOW GATE #27 — a RATCHET whose baselines ARE EQUAL AGAIN SINCE 2026-08-24: `{sandbox: 23, custom: 23}`** (`probe_abort_swallowing.py:218` is the authority; they DIFFERED `{31, 36}` between 2026-08-23 and the promotion, and were 36/36 before that — history, not today)**; ‼ ~64% of the original 45 were MEASURED not to be this defect, which is WHY it is a ratchet and not a zero-threshold

**2026-08-27 (deep sanity check, PASS 2):** the header above claimed the ratchet baselines
still `DIFFER PER FORK: {sandbox: 31, custom: 36}` — REFUTED by the shipped gate itself
(`probe_abort_swallowing.py:218` reads `{"sandbox": 23, "custom": 23}` since the 2026-08-24
promotion). Header corrected; the 31/36 and 36/36 figures are kept above as history.

**2026-08-23 — the baselines SPLIT (this entry's newest dated line; it is the body half of
the per-fork clause in the header above).** `#24-abortrecoveryresiduals` (b) guarded the 5
sandbox sites that `#24-loopheadabort` had newly exposed, so sandbox measures **31** and custom
was **36** until the fix was PROMOTED on 2026-08-24 (user-approved), when it became **23** — the
forks are EQUAL again and both read ZERO AST abort-swallowers. *(Superseded instruction: ON PROMOTION, LOWER custom
36 -> 31 IN THE SAME COMMIT** — otherwise the ratchet silently re-permits 5 sites of debt in
the fork that ships. ‼ Control-armed, not assumed: stripping exactly those 5 guards restores 36.
⛔ **A TIER 1 REVIEWER CAUGHT THIS PARAGRAPH FILED UNDER KI-79** — it had been inserted directly
ABOVE the `## KI-81` header, so by this file's own `##` convention it read as KI-79's trailing
text and a reader opening KI-81 would never have seen it. ⇒ **Anchoring an insert on a header
string puts it BEFORE that header. Verify WHERE a fix landed, not merely THAT it landed.**

`StoryAbort` is a `BotModeError`, which is an `Exception` (`_interface.py:229`) ⇒ **every**
`except Exception:` and `except BotModeError:` catches a whiteout. KI-67 found this and fixed the
two CHAPTER retry loops that had been *observed* failing (`space_center.py:962-977`,
`mossdeep_gym.py:540-556`, re-derived 2026-08-16 — it was cited as `:534-551`) with two guards — `except StoryAbort: raise` **plus**
`reraise_if_aborting(error)`. ⛔ **The class was never swept.**

**MEASURED:** `tools/story-dev/probe_abort_swallowing.py` (NEW, `--self-test` proves it fires when
the guard is missing and stays quiet both when guarded and when the `try` drives no generator) —
**53 candidate sites**: `early_game.py` 44, `higher_level_actions.py` 4, `pc_trip.py` 3,
`counter_hunt.py` 1, `mossdeep_gym.py` 1.
⚠ **CANDIDATE means "could swallow", not "does".** The probe cannot prove a `_check_abort()` is
reachable through a given `yield from`; it narrows 500+ handlers to a triageable list.

**THREE HAND-VERIFIED, and they are the bad shape, not false positives:**
- `early_game.py:1625` — `except Exception: ok = False` around `yield from _yield_bounded(...)`,
  then **presses B twelve times and RETRIES**. An abort here is swallowed into a retry on a dead run.
- `early_game.py:267` and `:3241` — `except BotModeError as e:` inside retry loops. ‼ This is
  **KI-67's failure verbatim**: *"a chapter that caught the abort and retried IN PLACE ran straight
  into the next `_check_abort()`"* — burning the budget in a few frames and reporting invented
  failures.
- ‼ **All three of `heal_in_pokemon_center`'s piggybacks** (`:297`, `:316`, `:345`) catch `Exception`
  with no guard, so a whiteout during a heal **was** swallowed and the bot walked on. ✅ **FIXED.**

✅✅ **RESOLVED FOR 8 SITES, AND PROMOTED TO BOTH FORKS (2026-08-16, user-approved).** The triage
question this entry posed — *"`mossdeep_gym.py` still shows 1 even though KI-67 fixed it; triage
starts there, because it tells you which the probe is"* — **IS ANSWERED: the `try` at `:465`
(handler `:471`) is a TRUE POSITIVE, and it is a DIFFERENT `try` from KI-67's, at `:540` (handlers
`:543`/`:554`)** — the gym-exit door loop. ‼ *Both numbers re-derived from source, and note the
units: `:465`/`:540` are TRY lines, the `Guarded:` list below gives HANDLER lines.* After a whiteout it tried the
second door **on a dead run** and raised a FABRICATED *"could not get out of the gym"* naming doors.
⇒ **the probe does not over-flag; KI-67's sweep was incomplete.**
**Guarded — ‼ these nine lines were RE-DERIVED FROM SOURCE 2026-08-16, not hand-copied** (six of the
eight I first wrote here were wrong; a Tier 1 reviewer caught it, and hand-transcribed citations are
how this project keeps burning a day). ⇒ **Re-derive, never re-type**, with:
`ast.walk` for every `ExceptHandler` containing a `reraise_if_aborting` call —
  `higher_level_actions.py` `:297` / `:322` / `:357` (the three heal piggybacks, each `except
  Exception`) and `:781` (`except BotModeError`, `talk_to_npc`'s surviving arm after the split);
  `pc_trip.py` `:202` / `:313` / `:550` (all `except Exception`);
  `mossdeep_gym.py` `:471` (the gym-exit door loop — **this KI's own find**) and `:554`
  (**KI-67's pre-existing guard**, which is why the fork totals 9 guarded handlers for 8 added).
`reraise_if_aborting(error)` is the FIRST statement of each — LATCH-keyed, so it also catches an
abort already laundered into a plain `BotModeError`. ⚠ **Line numbers drift on every edit above
them; the SHAPE is the durable claim** — *"guard first, latch-keyed, `PathFindingError` split out"*.
⛔ **AN ADVERSARIAL REVIEW CAUGHT A REAL DEFECT IN THE FIRST CUT:** `talk_to_npc`
(`modules/modes/util/higher_level_actions.py:718`, split at `:767` — ‼ it is NOT in `pc_trip.py`,
which is where a later doc pass first misfiled it) also catches
`PathFindingError`, a **`RuntimeError`, NOT a `BotModeError`**; re-raising one would have ESCAPED
`StoryMode.run`'s `except BotModeError` and left the global latch **stuck TRUE**, leaking into
`ev_train.py`/`pokecenter_loop.py`. Fixed by SPLITTING the handler. *A guard that can leak a global
is worse than the silence it replaced.*
✅ **Promotion proven by a MEASURED before/after, not a byte-compare:** `--build custom` fell
**53 → 45**, guarded counts moved **0→3 / 0→4 / 1→2**, and the split survived the copy.

⛔ **STILL OPEN — 36 CANDIDATES REMAIN** (ALL `early_game.py`; `counter_hunt.py`'s single
candidate was fixed 2026-08-17, when 8 sites were swept and the probe fell 45 → 37, MEASURED).
⛔⛔ **SUPERSEDED 2026-08-17 — REFINEMENT (2) IS REFUTED AND (1) IS SHIPPED. DO NOT BUILD EITHER FROM THIS PARAGRAPH.** It survived unmarked eight lines below its own refutation, and a cold-start audit called it the most expensive thing in the tree: acting on it rebuilds a day of refuted work and can ship a gate that HIDES real defects. *(superseded text:)* ‼‼ **AND THE TRIAGE MEASURED THAT THE PROBE OVER-FLAGS: ~64% of the original 45 are NOT this
defect** — 25 wrap navigation primitives containing no `_check_abort()`, so no `StoryAbort`
can arrive; `:376` IS the whiteout-recovery path; `:2305` already guards by hand in a shape
the probe cannot see. ⛔ **DO NOT PROMOTE THE PROBE TO A GATE AS-IS** — it would be red on
arrival for reasons that are correct as written. Two refinements cut 45 → ~16. *(A separate
family — retry loops needing a LOOP-HEAD check, not a handler guard — was `#24-loopheadabort`,
✅ DONE 2026-08-23: all 17 patched, gate #30. ⛔ An earlier 3-loop exclusion rested on a FALSE
claim that the recovery path runs with the abort latch set; it is withdrawn.)* 44 sites in the largest and most timing-sensitive file here is not a
tail-of-session sweep, and **CANDIDATE ≠ DOES** — the probe cannot prove a `_check_abort()` is
reachable through a given `yield from`. ⇒ ⛔⛔ **SUPERSEDED 2026-08-17 — THIS IS DONE AND ITS ADVICE IS REFUTED. The probe IS gate #27, a RATCHET; refinement (2) would blind it to five already-fixed sites and must NOT be built.** *(superseded:)* triage, fix, THEN promote the probe to a gate — The
triage MEASURED that ~64% of the candidates are not this defect, so the probe must be REFINED first;
see the paragraph above and `#24-abortswallow` round 3. *(This line was the last thing in the KI, so
a skimmer read it as the instruction — a cold-start audit caught exactly that.)*; it is a
PROBE precisely because a gate red on arrival on pre-existing debt teaches everyone to ignore gates
(`repro_no_silent_except.py` took this exact path). Tracked as `#24-abortswallow`.

---

## Archived from `04-HANDOFF.md`

Per-leg driver invocations for two COMPLETED chapters. Moved only for 04's 900-line budget; a cold start needs the generic run commands (kept in 04), not these.

### §Ch21 + §Ch22 STORY LEGS — the runnable drivers
*(‼ added 2026-08-27 because a Tier 1 review found every leg existed only as PROSE, so a cold agent
could not START the shipped work from this file.)*
```
cd tools/story-dev
# legs 1 / 2a / 2b — each from its own PINNED fixture. ‼ Also covered end-to-end by `ch21chapter`
# below; these stay for isolating ONE leg, not for regression sweeps.
PYTHONUTF8=1 py -3.12 story_harness.py post_ch20.ss1              --driver ch21dive
PYTHONUTF8=1 py -3.12 story_harness.py post_sootopolis_arrival.ss1 --driver ch21escort
PYTHONUTF8=1 py -3.12 story_harness.py post_steven_escort.ss1     --driver ch21cave
# leg 3 step 0 — POCKET-EXIT probe, LIVE half (post_wallace.ss1) ~4,200 fr. ⚠ The `navigate` arm
# is the naive one and is MEASURED IDENTICAL to `follow`.
PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1           --driver ch21pocket --frames 60000
POKEBOT_CH21_POCKET_ARM=navigate  ... same ...

# leg 4 — THE SKY PILLAR climb + descent            (fixture: post_skypillar_door.ss1) ~10,100 frames
PYTHONUTF8=1 py -3.12 story_harness.py post_skypillar_door.ss1    --driver ch21climb --frames 60000

# ‼ leg 5's recipes (the PART C validation probe + its CONTROL arm, the return leg, the mid-leg
#   NPC half, and its SIX fault arms) are ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md` 2026-09-03.
#   The PART C arms are still the reference for proving KI-73 on a layout-swapped map.
# §Ch21 AS A CHAPTER — the PRODUCTION entry point, legs 1->5   (fixture: post_ch20.ss1)
#   MEASURED 2026-09-02: frames=95823, encounters=26, whiteouts=0, ACCEPTANCE: PASS.
#   Expect: ROUTE128(38,24) vars (1,0) -> SOOTOPOLIS_CITY(31,34) vars (5,3), hm07_in_bag=1,
#           wallace_state=1, gym_door(31,32)=2 wp, poke_center(43,32)=22 wp, premise_ok=True.
PYTHONUTF8=1 py -3.12 story_harness.py post_ch20.ss1              --driver ch21chapter --frames 250000
#   the VACUITY arm (must FAIL — it proves the grade is not satisfied by a no-op):
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch21chapter --frames 400

# §Ch22 PART A — the read-mostly gym probe (post_hm07.ss1) ~3,958 fr. PASSED 2026-09-02; kept
#   startable as the reference A/B for proving an instrument BLIND. Expect PASS, P0-P5, 64 thin ice
#   in sections 7/19/38, six locked stairs, metatile_diff=1 after one ice step and collision_diff=0
#   (the blindness proof), ICE_STEP_COUNT 1->2, re-entry resets to 1, money=67466, whiteouts=0.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22probe --frames 60000
#   its fault arm (must FAIL — proves the grade requires the MEASUREMENT, not just the code path):
POKEBOT_CH22_FAULT_NOSTEP=1 ... same ...

# §Ch22 THE ICE PUZZLE — the 64-step route table, walked   (fixture: post_hm07.ss1) ~2,232 frames
#   ⛔ DRIVEN 2026-09-02, and now also covered by the CHAPTER below. Production `walk_the_ice()`;
#   the table is re-derived from the DECOMP by `solve_gym_ice.py` and re-checked LIVE every step.
#   Expect: PASS, steps=64, sections (1,7,(8,17),9) (2,19,(8,12),29) (3,38,(8,6),68), frames=2232,
#           `end_tile=(8,6)` BUT `at=(8,3)` — DIFFERENT FIELDS, both right: production ENDS on
#           (8,6) and the 3-step climb to (8,3) is `climb_to_juan()`, which the CHAPTER owns.
#   ‼ End counts are 9/29/68, NOT 8/28/67 (each unlock's `addvar` lands in the crossing step's
#     beat). The guard tolerates +1 AND +2 — asserting +1 exactly was a real bug.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22ice   --frames 60000

# §Ch22 THE STAIR COLUMN — READ-ONLY, ~2,232 fr. ⛔ RUN BEFORE TOUCHING THE DESCENT. Walks the ice,
#   then dumps live column x=8 before AND after — an A/B in one run. Expect (8,4) and (8,5) both
#   0x20f -> 0x207 (LOCKED -> OPEN), (8,6) -> 0x20e cracked, (8,2)=0x22b (JUAN'S OWN TILE, plain
#   floor), VERDICT: WALK, PASS. ‼ PASS means THE READING HAPPENED — read the VERDICT line.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22stairs --frames 60000

# §Ch22 THE EXIT — the ice, then the DELIBERATE FALL to B1F and out, ~19,989 frames (MEASURED)
#   ⛔ DRIVEN 2026-09-03, the first entry into B1F ever. ‼ It re-walks the ice; the CHAPTER does not.
#   Expect PASS: ice_steps=64, fall to B1F (8,6) in ~140 fr, b1f_steps=19, battles=3 at (8,8)
#   (8,17) (8,19), end SOOTOPOLIS_CITY (31,33), continue=23 wp, whiteouts=0, frames=19989,
#   PARTY 629/694 -> 332/694 with ZERO faints.
#   ⛔⛔ 3 BATTLES IS *THIS DRIVER'S* PASS SHAPE — it runs at `badge8=False`. THE ASSEMBLED CHAPTER
#     SEES **ZERO** (the victory script settrainerflags all ten; MEASURED live). ⇒ this leg's battle count and HP cost are NOT transferable; the FALL and the ROUTE are.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22exit  --frames 120000

# §Ch22 JUAN — GYM 8, ~32,891 fr (MEASURED; the first gym-LEADER fight ever timed here). DRIVEN
#   2026-09-03 AND WON. Expect PASS, badge8=True won=True at=GYM_1F(8, 3), city_state=6, battles=1,
#   outcomes=['BattleOutcome.Won'], whiteouts=0, SURVIVORS 5/6, frames=32891.
#   ⛔ RE-RUNNING THIS UNJITTERED IS A REPLAY, NOT A SAMPLE (3 identical runs proved it). New draw:
POKEBOT_CH22JUAN_JITTER=181 PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1 --driver ch22juan --frames 120000
#     Expect a DIFFERENT frame count (25508 at N=181) and two DIFFERENT RNG values across the
#     idle — equal means the jitter moved nothing. ⇒ a LOSS is a RESULT: 6 draws, 5 WINS, 1 LOSS.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22juan  --frames 120000

# §Ch22 AS A CHAPTER — the PRODUCTION entry point (Segment 22). (fixture: post_hm07.ss1) ~64,563 fr
#   ✅ DRIVEN TO PASS 2026-09-03, INCLUDING A LOST GYM FIGHT IT RECOVERED FROM. ⛔ DO NOT REBUILD.
#   Expect PASS: badge8=True, at=SOOTOPOLIS_CITY(31,33), city_state=6, ice_steps=64 (ice_ok=True),
#   b1f_steps=19, battles_on_B1F=0 WITH b1f_entered=True, CONTINUE=23, RECOVERIES 1,
#   outcomes=['BattleOutcome.Lost','BattleOutcome.Won'].
#   ⭐ `battles_on_B1F=0` IS MEANINGLESS WITHOUT `b1f_entered=True` — drive 1 printed the same 0
#     having never set foot on B1F.
#   ⚠ A LOSS IS A RESULT (stochastic, 5W/1L over six draws) and the chapter RECOVERS. ⛔ A
#     transcript with NO `ACCEPTANCE` line + `BotModeError -> Manual` is **KI-47** (which has a
#     deterministic repro command there), not a hang and not a §Ch22 defect.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22chapter --frames 300000
#   two fault arms, each FAILing for a DIFFERENT half of the completion predicate:
#   POKEBOT_CH22_FAULT_{NODESCEND -> stranded on the ISLAND | STRANDED -> still on GYM_1F}=1
#   ⭐ CH22_CAPTURE=post_badge8.ss1 ... same ...  captures §Ch23's fixture on a FULL PASS only.

# §Ch23 LEG-9 ROUTING PROBE (OBSERVE-ONLY — walks nowhere, fights nothing; ~1 min):
#   PYTHONUTF8=1 py -3.12 story_harness.py post_return.ss1 --driver ch23leg9probe --frames 3000
#   Expect `ACCEPTANCE: PASS`, `battles=0`, readings R9P-HERE/DIRECT/CONE/BYPASS/SPLIT. It grades on
#   HAVING ASKED, not on the answers. Measured 2026-09-05 (late): direct = 62 wp ENTERS the cone at
#   (31,17); (33,16) bypass = 44+18 = 62 wp BOTH CONE-FREE (=> FREE); split routes enter (31,17), safe=False;
#   CONTROL_..._33_17 = PathFindingError EXPECTED (elevation-15 seed, kept visible). Full: 07-CHANGELOG.
# §Ch23 — VICTORY ROAD. ✅ ELEVEN LEGS BUILT AND DRIVEN (2026-09-04) **AND THE CHAPTER IS WIRED (2026-09-05)**. ⛔ DO NOT REBUILD THE LEGS OR THE ORCHESTRATOR. THE CHAPTER: `PYTHONUTF8=1 py -3.12 story_harness.py post_league_shop.ss1 --driver ch23chapter --frames 3000` — the CHEAP resume arm, expect `ACCEPTANCE: PASS`, `done=True`, `inside_victory_road=False`, `neighbours_reachable=4`. ⭐ THEN THE ARM THAT ACTUALLY PROVES THE DESIGN: `POKEBOT_CH23_PREDICATE_ONLY=1 ... post_wally.ss1 --driver ch23chapter --frames 2000` — expect `flag_only=True gate=False inside_victory_road=True`, i.e. a flag-only completion predicate would call the chapter DONE with six legs to go. ‼ The cheap arm CANNOT prove that: on the end fixture the flag and the gate agree, so a flag-only predicate passes it identically. ✅✅✅ THE FULL CHAIN (`post_wally.ss1 --driver ch23chapter --frames 600000`) **PASSES** as of 2026-09-05: `ACCEPTANCE: PASS`, `done=True`, `battles=16`, `whiteouts=0`, `failure=None`, ending at EVER_GRANDE (18,6). ⭐ `done=True` requires the whole Elite Four basket in the bag, so a pass also proves the purchase. ⛔ **DO NOT RE-DRIVE IT TO "CHECK".** *(This line read "It now LOSES the leg-9 Katelynn+Quincy double and whites out" — fixed the same day by routing leg 9 around the pair via (33,16) and, when that skipped their ₽4,128 of payouts, by selling the Nugget at leg 11.)* Fault arms for this leg: **`POKEBOT_CH23_FAULT_NOBYPASS=1`** (route direct through the sight cone — expect the pair to fire at (31,17)) and **`POKEBOT_CH23_FAULT_NOSELL=1`** (skip the top-up — expect a loud ₽2,387 shortfall). Also `POKEBOT_CH23_FAULT_STRANDED=1`, `POKEBOT_CH23_FAULT_NOLEAGUEHEAL=1`. *(This line read "THE CHAPTER IS UNBUILT" for eleven legs — a Tier 1 reviewer found the section had NO run command for any leg past leg 1.)*
# ✅ START FIXTURE: saves/post_badge8.ss1 (md5 723d94cc899f3ad2c75fbf49f9192984), all EIGHT badges, SOOTOPOLIS_CITY (31,33). ⚠ 428/701 (61%) with ONE MEMBER FAINTED, so §Ch23 opens with a heal. Verify a fixture from the FILE: probe_anchor_inventory.py.
# ⭐ EVERY LEG IS `PYTHONUTF8=1 py -3.12 story_harness.py <fixture>.ss1 --driver <name> --frames <N>`, run from tools/story-dev. Each fixture's md5, its state, and that leg's expected readings live in `saves/FIXTURES.md5` — THE AUTHORITY, never this line. Legs 2-11, in order:
#   ch23depart post_waterfall 40k · ch23cross post_depart_sootopolis 60k · ch23road post_training 60k · ch23descend post_wally 120k · ch23cross2 post_b1f_healed 120k · ch23return post_b2f 120k · ch23exit post_return 120k · ch23heal post_vr_exit 120k · ch23shop post_league_heal 120k (leg 11, buys the Elite Four basket; fault arm POKEBOT_CH23_FAULT_NOBUY=1 must FAIL) ‼ AND §Ch24 TRAVEL: `ch24fly post_moveset 40k` teaches Swellow Fly (expect `LANDED ['Swellow:Fly']`), then `ch24flyto post_fly 40k` FLIES to Slateport (expect `moved=True`, `party_pids_stable=True`, `neighbours_reachable=4`; `CH24_FLY_DEST=` overrides the target; fault `POKEBOT_CH24_FAULT_NOFLY=1` must FAIL). ‼ AND §Ch24: `ch24moves post_league_shop 40k` — `#24-e4moveset`, the FOUR FREE move changes (Sceptile Slam→Aerial Ace · Swellow Peck→Facade · Mightyena Tackle→Strength · Zigzagoon Growl→Rock Smash). Expect `ACCEPTANCE: PASS`, `LANDED` 4/4, `WRONG []`; captures `post_moveset.ss1` with `CH24_CAPTURE=`. Fault arm `POKEBOT_CH24_FAULT_BADMOVE=1` must FAIL by REFUSING (a single-use TM must never be spent on a guess). ⭐ Plan + rationale: `ai-research-notes/2026-09-04-ch24-MOVESET-AND-TM-PLAN.md`. ‼ AND §Ch24: `ch24heal post_league_shop 60k` — `#24-e4healing` step 1, the OUT-OF-BATTLE party heal. It STAGES its own damage (2 fainted, 1 FROZEN, 2 hurt) because no fixture has both a hurt party and the basket, then heals to full. Expect ACCEPTANCE: PASS, heal_actions=7, heal_ready=True, REVIVE ORDER [(4,Revive),(1,Revive)] (battle value, NOT slot order), Castform untouched. Fault arm POKEBOT_CH24_FAULT_NOHEAL=1 must FAIL. ‼ AND §Ch24 ICE BEAM, BOTH HALVES DONE 2026-09-05 — ⛔ these are REPRODUCTIONS, not work to do: `ch24icebeam post_slateport 700k` sails to the Abandoned Ship, takes the Storage Key, INSERTS it (the Storage Room door is a `MB_NORMAL` WALL until it is), takes **TM13** and returns outside; expect `ACCEPTANCE: PASS`, `have_key=True`, `have_tm13=True`, `battles=2`, `whiteouts=0`, capturing `post_icebeam.ss1`. Fault arm `POKEBOT_CH24_FAULT_NOKEY=1` must refuse at the Captain's Office, BEFORE the long walk back. ‼ Boarding is a NORTH ARROW warp — stand ON (29,6) and hold Up. THEN `ch24teachice post_icebeam 6k` teaches it: expect `ACCEPTANCE: PASS`, `LANDED ['Wailord:Ice Beam']`, `wrong=[]`. ⭐ Use a SMALL frame budget — it reaches its verdict by ~f574 and then idles to the cap in Manual, so 40k wastes twelve minutes. ⚠ Its trace should print `upstream left the cursor on slot 13 (HM08); correcting to slot 3 (TM13)` — that correction IS the fix for `KI-89`; if it stops printing, upstream changed.
# leg 1 — TEACH WATERFALL TO WAILMER. ~1,896 frames. ✅ DRIVEN 2026-09-03, ACCEPTANCE: PASS.
#   Expect: production picks slot 3 unaided, GAINED ['Waterfall'], LOST ['Rollout'],
#           keeps_dive=True keeps_surf=True, party intact 6->6, whiteouts=0.
#   ⭐⭐ `keeps_dive` IS THE GRADE, not a nicety: Wailmer is the party's SOLE Dive carrier and Dive
#     is the only exit from the Sootopolis crater (no land connections, allow_escaping false).
#   ⚠ It is the deepest forget-menu scroll this bot has driven (slot 3; both precedents were 1).
#     `#26-surfteachchain` D3 did NOT fire — that is NOT the same as D3 being fixed; its hazard is
#     RE-ENTRY and this run never re-entered. D3 stays OPEN.
PYTHONUTF8=1 py -3.12 story_harness.py post_badge8.ss1            --driver ch23teach --frames 40000
# Victory Road's route, OFFLINE from the decomp (no emulator, seconds). ⛔ RUN --self-test FIRST:
#   its negative/fault controls are what make the numbers mean anything.
PYTHONUTF8=1 py -3.12 solve_victory_road.py --self-test
PYTHONUTF8=1 py -3.12 solve_victory_road.py
#   Expect: Q1 says the exit is **UNREACHABLE on 1F alone** (477 tiles), and prints the same query
#           with elevation IGNORED (71 steps, 646 tiles) right beneath it — ‼ THE TWO DISAGREEING
#           IS THE POINT: elevation is what separates the regions, and 71 was v1's artifact.
#           Q2: on B1F only [both] opens the floor — 23 tiles with neither, 66 Strength-only,
#           23 Rock-Smash-only, 298 + the B2F warp with both. ⇒ **STRENGTH AND ROCK SMASH ARE BOTH
#           REQUIRED and §Ch23 DOES need a boulder solver.** Flash stays optional, but B1F/B2F are
#           on the critical path and get walked dark. Q3: Wally's detour costs **0 steps**.
#   ⛔ --self-test carries ONE CONTROL PER MODEL (collision leak + fault, ELEVATION leak + fault,
#     off-grid raise). v1 had only the collision pair, it PASSED, and the bug was in elevation.

# leg 3 — THE APPROACH, the PRODUCTION entry point. ~34,000 frames (MEASURED). Expect PASS,
#   reached=True at=SKY_PILLAR_ENTRANCE(6,16) pocket_attempts=1 rest=(6,16) encounters=9
#   whiteouts=0 frames=34122 rest_matches_prediction=True; METHOD planner_calls_on_route131=2
#   blind_steps_taken=1 tail_tiles_confirmed=16/16 method_ok premise_ok; CONTROL control_refused
PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1 --driver ch21approach --frames 120000

# leg 4 — THE SKY PILLAR CLIMB + DESCENT. ~10,000 frames (MEASURED). Both one-shots, both falls.
#   Expect: reached=True at=SKY_PILLAR_ENTRANCE(14,3) phase=full order_ok=True falls=[ascent,descent]
#           floors_pinned=7 VARS end=(5,1,1)  METHOD premise_ok=True method_ok=True  ACCEPTANCE: PASS
PYTHONUTF8=1 py -3.12 story_harness.py post_skypillar_door.ss1 --driver ch21climb --frames 60000
# ‼ leg 4's SEVEN FAULT ARMS (each FAILS for its own reason) are ARCHIVED VERBATIM in
#   `28-HANDOFF-ARCHIVE.md` 2026-09-03 — moved, not deleted, to make room for §Ch23. Restore them
#   from there if `climb_sky_pillar` is ever touched; `--driver ch21chapter` is the end-to-end arm.
# the Sky Pillar CLEAN layouts for all six floors, from our ROM (no network). Offline, seconds.
PYTHONUTF8=1 py -3.12 probe_skypillar_rom_layouts.py
POKEBOT_SPROM_FAULT=stride|noagree   ... same ...   # self-tests (both RED); anycand PASSES on purpose
# ‼ leg 3's THREE fault arms (POCKETSTALL must still PASS with pocket_attempts=2; BLINDWALL and
#   POCKETWALKBACK must FAIL by name) are ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md` 2026-09-03.
# ⛔⛔ NONE OF THE §Ch21 PROBES IN THIS BLOCK IS READ-ONLY, WHATEVER ITS 'Offline' LABEL SAYS —
#   ABOVE this line as well as below (a Tier 2 audit found it anchored below five of its subjects,
#   one under 'RUN THIS FIRST'). All SEVEN boot LibmgbaEmulator on the SHARED `repro-ml` profile
#   and write a save state + update current_state.ss1 EVERY RUN: probe_ch21_{skypillar,
#   route131_tail,route131_live,leg3_constants,pocket_exit}, probe_live_mapgrid,
#   ab_ch21_leg3_layoutpin. Gitignored, but it mutates shared state. `#24-skypillarprobewrites`.
# ⛔ keep BOTH sky-pillar
# probes: this one reads the layout WE plan on, `probe_skypillar_clean_layout.py` reads CLEAN.
# leg 3 — the TAIL adjudication + the CONSTANTS re-check. Seconds. ⛔ NOT read-only — see above.
PYTHONUTF8=1 py -3.12 probe_ch21_route131_tail.py
POKEBOT_R131TAIL_FAULT=stride|swapsets|bendtail  ... same ...    # self-tests; all three must fire
PYTHONUTF8=1 py -3.12 probe_ch21_leg3_constants.py
# ⛔ THE INSTRUMENT FOR "the planner and the game disagree about a tile" — use it on ANY map that
#   runs setmaplayoutindex or setmetatile. It reads gBackupMapLayout (RAM), which is the ONLY
#   reader in this tree that can see either. Pass any save state.
PYTHONUTF8=1 py -3.12 probe_live_mapgrid.py saves/post_skypillar_door.ss1
# leg 3's layout-pin A/B, against drive 1's own stall state (reproduces the failure, then fixes it):
PYTHONUTF8=1 py -3.12 ab_ch21_leg3_layoutpin.py

# leg 3 step 0 — the STATIC half. Seconds. ⛔ NOT read-only (see above). RUN THIS FIRST.
PYTHONUTF8=1 py -3.12 probe_ch21_pocket_exit.py
POKEBOT_POCKET_FAULT=rig PYTHONUTF8=1 py -3.12 probe_ch21_pocket_exit.py   # self-test: C3 RED, exit 1

# leg 3/4 — the SKY PILLAR, asked of PRODUCTION. Seconds, no network.
PYTHONUTF8=1 py -3.12 probe_ch21_skypillar.py
POKEBOT_SKYPILLAR_PROBE_FAULT=rig PYTHONUTF8=1 py -3.12 probe_ch21_skypillar.py  # self-test: C2 RED

# leg 3 PRE-BUILD GATE — ROUTE131 SET A vs SET B, from OUR ROM. Offline, seconds. ⛔ RUN BEFORE BUILDING.
PYTHONUTF8=1 py -3.12 probe_ch21_route131_live.py
POKEBOT_R131_FAULT=stride PYTHONUTF8=1 py -3.12 probe_ch21_route131_live.py   # self-test: C2 RED, exit 1
```
⛔ **Quote `ch21pocket`'s `RESULT` line, never its `ACCEPTANCE` line**: ACCEPTANCE grades *"did every
reading happen"*; whether the walk worked is the separate `walked_out=` field. ⚠ Any driver dirties
`party_accounting_ledger.jsonl` — expected, not damage (playbook §2b).

---

## 📦 ARCHIVED 2026-09-08 FROM `03-PUNCH-LIST.md` — `#24-dexhunt` (the ORIGINAL 2026-07-29 proposal, VERBATIM)

Moved only to keep 03 inside its 3600-line budget (`lint_docs.py` R3). ⛔ Nothing deleted and
nothing edited — it was kept in 03 for its RATIONALE, and that rationale is preserved here in
full. The LIVE `#24-dexhunt` item (re-affirmed and widened) remains in 03, above where this
sat, and is the one to act from.

### `#24-dexhunt` (original 2026-07-29 proposal, kept for its rationale) — catch EVERY new species, and hunt between gyms
⛔⛔ **SUPERSEDED — DO NOT ACT ON THE STATUS BELOW.** This is the ORIGINAL 2026-07-29 proposal, kept ONLY for its rationale; the LIVE entry is the `#24-dexhunt` heading ~50 lines ABOVE, which reads **"STATUS: OPEN, unblocked"**. The deferral quoted here was overtaken by the user's 2026-07-31 RULING and again by the 2026-09-04 catching directive. ‼ A Tier 1 reviewer found two headings under the SAME SLUG saying "OPEN, unblocked" and "NOT SCHEDULED" — ⇒ **retitling a superseded block is not stamping it; the STATUS LINE is the half a reader acts on.** *(historical:)* **NOT SCHEDULED — proposed, understood, and deliberately deferred by the user** ("we don't have
to implement it now… after I send these logs we should be at a good point to continue the
story").

**The proposal.** Catch every new species the bot meets, and deliberately hunt for unseen ones
between gyms. Rationale: (a) it is what a human player does, so runs look realistic; (b) the
encounters generated *while* hunting are XP, so hunting doubles as training and the dex fills
for free; (c) more encounters = more shiny chances.

**‼ Why (b) is the strongest argument, with measured backing.** Training is currently a
PURE-COST activity: bundle `20260729-151635` shows **78 heal round trips in one run** and
training is the single largest consumer of run frames. Hunting in level-matched areas converts
that same spend into XP **plus** dex progress **plus** shiny lottery tickets. It does not add a
cost so much as add yield to a cost already being paid.

**Most of the machinery already exists — this is assembly, not invention:**
| piece | what it already does |
|---|---|
| `modules/encounter_index.py` | whole-game reverse index: species → [{map, method, rate%, level range}] |
| `plugins/custom_modes/hunt_mode.py` | "travel to a target species' best wild spot, then hunt it" |
| `plugins/custom_modes/living_dex_mode.py` | "work through a list of target species autonomously" (#23) |
| `StoryShinyCatchStrategy` (`story_mode.py:78`) | already always-catches shinies, **even with a full party** (goes to the PC) |
| `21-TEAM-POLICY-DESIGN.md` §1 | already specifies *"Drop the `BADGE01_GET` gate. Raise `_catch_team_target` 4 → 6, allow overflow to the box."* |

**Exactly two gates block it today**, both in `_should_catch` (`story_mode.py`):
1. `if get_event_flag("BADGE01_GET"): return False` — catching stops after Gym 1.
2. `if len(party) >= self._catch_team_target: return False` — the cap of 4.
The other gates are sound and should stay: needs the Pokédex, needs >1 ball, never a duplicate,
never a shiny (the shiny branch pre-empts).

**‼ HARD DEPENDENCIES — do NOT build this first, it will starve:**
- **Ball + money economy.** Already failing at the current catch rate: this run logged *"out of
  Poké Balls — fleeing this catch and moving on"* and a derail *"Cannot hunt a Surf learner: no
  Poké Balls and no money to buy any."* Trainer battles are the ONLY income in Hoenn (no
  scripted cash gifts). Catching everything multiplies ball spend. → `#24-provisions` first.
- **PC / party management.** Catching everything guarantees a full party and constant box
  traffic. `team_policy.py` is built but **unwired**, and dead weight is already at 35% of badge
  moments. → `#24-trainmap+` item (3) first.
- **Menu-wedge exposure.** Every catch is more party-menu and nickname-prompt interaction, and
  **KI-34 (after-faint chooser livelock) is OPEN**. Multiplying menu traffic while a menu
  livelock is unfixed raises the derail rate. → settle KI-34 first.
- **Run length vs the frame budget.** A completed run is already ~3.06M frames against a
  (just-raised) 5M cap. Hunting between gyms will add substantially. Decide deliberately
  whether to accept fewer, richer runs per night or to cap hunting per chapter.

**‼ ONE GENUINE DESIGN CHOICE FOR THE USER — this proposal and doc 21 disagree.**
`21-TEAM-POLICY-DESIGN.md` §1 specifies a **scored, randomised** catch roll
(`p = 0.30 + 0.50*curiosity + …`) *specifically so runs differ from one another*. The user now
asks for **always-catch-new**, which is deterministic. Both are defensible: always-catch is more
human and gets variety from WHICH species the RNG offers; the scored roll makes two runs on the
same route diverge. **They cannot both be the rule — ask before building.**

---

## 📦 ARCHIVED 2026-09-08 FROM `03-PUNCH-LIST.md` — the 2026-08-10 ID CONSOLIDATION (VERBATIM)

Moved only to keep 03 inside its 3600-line budget (`lint_docs.py` R3). CLOSED and user-approved bookkeeping: the record of which duplicate/overlapping punch-list IDs were
merged. ⛔ Nothing deleted, nothing edited. Its stub in 03 keeps the pointer.

### 5. ✅ DUPLICATE / OVERLAPPING IDS — CONSOLIDATED 2026-08-10 (user-approved)
Each group now has ONE canonical entry; the duplicates were converted into **pointers** with all
their original text kept underneath, because IDs are never reused here and the reasoning trail is
worth more than the tidiness.
| group | canonical (still open) | why it wins |
|---|---|---|
| the `#24` umbrella (was 3 entries) | **"STORY AUTO-PLAYER"** | the umbrella header; ⛔ its "cold start reaches Badge 6" body went FIVE CHAPTERS stale and was corrected 2026-08-13 — **the live head is `#24-remainingarc` at the TOP of this file**, not this entry |
| PC / box team management | **`#24-roster`** | the user APPROVED it 2026-08-06 and lifted its gate, which outranks the older `#24-pc` design entry |
| organic team building | **`#24-organicteam`** | ⛔ **CORRECTED 2026-08-14** — this cell used to read *"it carries the user's 2026-08-05 DEFERRAL, i.e. the live instruction"*, which was **already false when written on 2026-08-10**: the user reversed that deferral on 2026-08-06 (`06-DECISIONS-LOG.md` RULING 1) and re-confirmed the lift on 2026-08-14. The entry is canonical because it is the concept's home, NOT because it carries a deferral. **The gate is LIFTED.** |
‼ **`#24-pc` (Surf resource walls) REMAINS OPEN and was not touched** — it is a derail class, a
different thing from the PC/box *feature* that shares its id.
Counts: ⛔ **DELIBERATELY NOT QUOTED — run `lint_docs.py`; its `I1`/`I2` lines ARE the authority.**
*(This line used to carry three figures and a cold-start audit measured TWO of them wrong within
a day — and the caveat it ALREADY carried, "this prose goes stale every session", did not stop anyone
believing the digits. ⇒ the only fix that works is to remove the number, not to warn about it.)*

HISTORY — originally flagged as: duplicate / overlapping ids, not merged
* **`#24` appears three times** as the umbrella (L≈1828 "STORY AUTO-PLAYER", L≈2040 "STORY-MODE
  BOT", L≈2292 "Story auto-player"). Two are roadmap-era restatements of the third.
* **`#24-pc` appears twice** (the resource-wall entry and the PC/box team-management entry) and
  **overlaps `#24-roster`**, which is the approved PC-roster feature.
* **`#24-organicteam` and `#24-team`** are the same concept under two IDs.
⇒ Recommend consolidating each group under its newest ID with the older ones pointing at it.
**Not done unilaterally — it rewrites history in a current-state file.**


---

## 2026-09-10 — THREE CLOSED PUNCH-LIST ITEMS RETIRED VERBATIM (R3 budget: 03 was at 4200/4200)

Moved out of `03-PUNCH-LIST.md` to reclaim headroom before new work was written into it, per the
handoff’s standing “ARCHIVE FIRST, WRITE SECOND” instruction. **Nothing was edited and nothing was
deleted** — the three blocks below are byte-identical to what stood in `03`, and each left a
one-line stub behind pointing here.

‼ **ONE LIVE RESIDUAL WAS *NOT* ARCHIVED.** `#24-e4moveset`’s closing paragraph was the only place
in the tree tracking the still-un-fetched **Dragon Claw (TM02) for Sceptile**. That sentence was
hoisted into the stub in `03` rather than retired with the block — **a closed item can still be the
sole owner of an open fact; check for residuals before retiring one.**

### ✅ `#24-icebeamtrip` — **CLOSED 2026-09-05: TM13 ICE BEAM IS IN THE BAG.** ⛔ DO NOT REDO THE TRIP.

`--driver ch24icebeam` `ACCEPTANCE: PASS` from `post_slateport.ss1` → fixture **`post_icebeam.ss1`**
(md5 `5515f893a2aa1a1e7e60d6741a3d8497`): `have_key=True`, `have_tm13=True`, `missing=[]`,
`battles=2`, `whiteouts=0`. Fault arm `POKEBOT_CH24_FAULT_NOKEY=1` refuses at the Captain's Office.

⛔⛔ **FOUR BLOCKERS, AND NOT ONE WAS VISIBLE IN THE WARP TABLES I TRUSTED:**
1. **Boarding is a NORTH ARROW WARP** (`MB_STAIRS_OUTSIDE_ABANDONED_SHIP`). Stand ON (29,6), hold Up.
   ⭐ Proven before the decomp arrived: a hand-step WEST walked straight *through* the tile to (28,6)
   without firing it — which no step-on warp can do.
2. **The DECK is split in two.** The Captain's Office is UNREACHABLE from the boarding tile — the
   decomp found it by collision BFS and **our own planner confirmed it independently** by refusing
   `(13,15) → (12,5)`.
3. **`CORRIDORS_B1F` ROW 5 is the ONLY crossover in the entire ship.** Reaching the key requires
   board → down → cross → up the WEST stair → deck west half.
4. **The Storage Room door is METATILE-GATED**, not warp-gated: `OnLoad` stamps (11,4) as
   `MB_NORMAL` — a WALL — until `FLAG_USED_STORAGE_KEY` is set. **Holding the key does nothing; it
   must be INSERTED with A.**

📦 Full evidence: `ai-research-notes/2026-09-05-ch24-ABANDONED-SHIP-ROUTE.md`.

---

### ✅ `#24-icebeamteach` — **CLOSED 2026-09-05: WAILORD KNOWS ICE BEAM.** ⛔ DO NOT REOPEN. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-05, to keep 03 under its R3 line budget).
### ✅ `#24-flyunlock` — **CLOSED 2026-09-05: FLY IS TAUGHT AND FLOWN. THE EVER GRANDE PLATEAU IS SOLVED.** ⛔ DO NOT REDO.

⛔⛔ **THE PROBLEM WAS GEOGRAPHY, NOT POLICY:** from EVER_GRANDE (18,6) only the League door and the
Victory Road exit landing were reachable — the Poké Center, the VR apron, the shore and every water
tile returned `PathFindingError`, so **the bot could not walk to a single wild encounter.**
✅ `ch24fly` → `post_fly.ss1` (`a45283a669e7ee36776b43acec3a8580`) teaches Swellow **Fly** over Wing
Attack (dominated by its own Aerial Ace); ✅ `ch24flyto` → `post_slateport.ss1`
(`171460626f5f6fead942aa88a85b2050`) FLIES to SLATEPORT (19,20), graded on ARRIVAL with
`party_pids_stable=True`. 16/17 destinations unlocked. 📦 `07-CHANGELOG.md` 2026-09-05.

---

### ✅ `#24-e4moveset` — **CLOSED 2026-09-05: the four FREE move changes are applied and driven.** ⛔ DO NOT REDO THEM.

`--driver ch24moves` `ACCEPTANCE: PASS`, fixture `post_moveset.ss1` (md5 `36e4510ecccf06957a7c3cb38ce2a967`),
fault arm `POKEBOT_CH24_FAULT_BADMOVE=1` correctly FAILS by refusing.

**Sceptile** Slam→**Aerial Ace** (four opponents run Double Team; Grass resists Grass) ·
**Swellow** Peck(35 BP)→**Facade** (Toxic makes Guts ×1.5 *and* Facade stack) · **Mightyena**
Tackle→**Strength** (35→80 BP; HMs reusable) · **Zigzagoon** Growl→**Rock Smash**.
⭐ All four were already in the bag — zero travel, zero money; compatibility read from
`tmhm_learnsets.h` at two revisions and diffed (Gen-3 TMs are SINGLE-USE).
‼ **I had this wrong first:** Rock Smash + Strength were NOT "two dead slots" — **Slam** (80/75%) is
worse than **Strength** (80/100%). 📦 Full detail: `07-CHANGELOG.md` 2026-09-05.

**WHAT REMAINS (not this item):** the two free PICKUPS that win Drake — **Ice Beam (TM13)** for
Wailord and **Dragon Claw (TM02)** for Sceptile, both confirmed still available by
`probe_ch24_readiness.py`. And **Wallace is still a loss** — see the note.

---

---

## 2026-09-10 (second pass) — TWO MORE CLOSED ITEMS RETIRED (R3 budget: `03` hit 4223/4200 while `#24-dexhunt` was being written up)

Same rule as the first pass this date, and the residual check was RUN, not assumed: every noun in
both blocks (`#24-movepoolcounters`, `answer_via`, `build_commits`, "never promote while a batch")
was grepped tree-wide and found in at least one other file, so neither block SOLELY owns a live
fact. `#24-lane-respawn-build`’s operational rule is additionally restated in its stub.

### ✅ `#24-lane-respawn-build` — a respawned lane loads the ON-DISK build (filed + fixed 2026-09-07)
- [x] ✅ **FIXED AND GATED — after shipping DEAD once.** `Lane.build_commits` records
  `git_commit()` at EVERY spawn, and `lane_summary()` (extracted for exactly this reason)
  carries it into the report. ⛔ The FIRST version recorded it on the Lane and never copied
  it into the summary dict — a mixed batch would have printed `(not recorded)` — and SEVEN
  green checks missed it because each called the reporting function on a HAND-TYPED dict.
  The gate now drives the REAL path (a real `Lane` through the real assembly), separates
  UNVERIFIED (a git hiccup) from MIXED, and is **fault-tested against the actual defect**:
  deleting the wiring line turns 11 checks red and exits 1; restoring it returns ALL PASS.
  ⭐ Detection does NOT replace the rule — it makes it auditable.
- [x] ⚠ `x4_headless.py` respawns a dead lane, and the new process imports whatever is on disk **at
  that moment**. ⇒ promoting mid-batch can put **two builds inside one batch**, not merely stale the
  MANIFEST — a finish rate whose build is ambiguous is not a measurement. This is the concrete
  mechanism behind the "never promote while a batch runs" rule. **Options:** snapshot the build per
  batch, or record each lane's load-time commit in the MANIFEST so a mixed batch is at least
  DETECTABLE. ⛔ Prefer detectable over forbidden — a rule nobody can verify is prose.

---

## 2026-09-10 (second pass) — TWO MORE CLOSED ITEMS RETIRED (R3 budget: `03` hit 4223/4200 while `#24-dexhunt` was being written up)

Same rule as the first pass this date, and the residual check was RUN, not assumed: every noun in
both blocks (`#24-movepoolcounters`, `answer_via`, `build_commits`, "never promote while a batch")
was grepped tree-wide and found in at least one other file, so neither block SOLELY owns a live
fact. `#24-lane-respawn-build`’s operational rule is additionally restated in its stub.

### ✅ `#24-countermsg` — the counter guard's CORRECT diagnosis read as WRONG (filed + fixed 2026-09-07, sandbox, display-only)
- [x] ⭐ **This cost a false defect report, which is the justification.** From a live batch log I read
  *"Winona: Need one of: Rock, Ice, Dragon. Nearest reachable counters: Slugma (Fire)..."* and
  reported the recommender as violating its own constraint. **It was not.**
  `counter_plan.py:156,185-205` admits a species by TYPES **or** by a level-up move of a needed type
  (`#24-movepoolcounters`, user directive) — Slugma learns **Rock Throw at L15** and Fiery Path
  Slugma is L15. ⇒ the list was right and the LINE was unreadable. ‼ **A message that makes correct
  behaviour look broken costs what a bug costs: someone investigates it.**
- [x] The explanation was already computed and discarded: `counter_plan.py:331-335` builds
  `answer_via` (`"type"` vs `"move:Rock Throw@L15"`) under a comment demanding the log say which rule
  fired — with ZERO production consumers. Now rendered, verified by direct call:
  `Slugma (Fire) via move:Rock Throw@L15 on Fiery Path (tile (18, 19), L15-15, 10% rate) — reachable`
- [x] The printed top-5 is now deduped **BY SPECIES** (5 of up to 12). Live, four of Winona's five
  rows were the same Geodude across four Magma Hideout floors. ⛔ The ladder's `huntable_candidates()`
  dedupes by `(map, tile)` and does NOT collapse those — the floors are distinct maps. A reader wants
  SPECIES; the executor wants DESTINATION. Different questions, different keys, deliberately not
  shared. ⛔ **DISPLAY ONLY** — `_counter_catch_message` builds a `BotModeError` string
  (`story_mode.py:2053`) and feeds nothing the ladder chooses.

---

## 2026-09-10 (third pass) — `#24-mossdeepstrand` retired, residual hoisted

Retired for R3 line budget while `#24-dexhunt` was written up. ‼ **This block is the clearest
example yet of the rule filed earlier the same day:** every one of its checkboxes is `[x]`, and it
still owned a LIVE to-do — *“Acceptance still owed: a drive from a save standing on (23,8) with
BADGE07 set”*. The fix is real but **UNDRIVEN**. That sentence was hoisted into the stub in `03`
rather than retired with the block.

### `#24-mossdeepstrand` — winning BADGE07 LOCKS THE BOT INSIDE the Mossdeep gym (filed 2026-09-07, ✅ FIXED IN THE SANDBOX same day — ⚠ UNDRIVEN, NOT PROMOTED)
- [x] ✅ **FIXED 2026-09-07 (sandbox, UNDRIVEN).** Two halves, each a no-op off the gym map:
  Segment 18's `else` now calls `leave_the_gym()` before printing (`story_mode.py:3774`), and
  the chapter's own badge early-return leaves first (`mossdeep_gym.py:549`). ⛔ The IDENTICAL
  early-return in `fight_the_leaders()` (`:382`) was deliberately LEFT ALONE — that one is a
  SUB-STEP and is correct: leaving is the chapter's job, and the fight is retried 3x.
  ⚠ Acceptance still owed: a drive from a save standing on (23,8) with BADGE07 set.
- [x] `(23,8)` is an 11-tile collision island whose only exit is a **coord_event** at `(21,6)` no warp
  solver can offer (`mossdeep_gym.py:460-461`). Its sole stepper, `leave_the_gym()`, is called only at
  `:596` — **after** the badge early-return (`:548-549`, `:556-557`) — and Segment 18 skips the
  chapter once BADGE07 is set (`story_mode.py:3772`). ⇒ **double bypass: with BADGE07 set and the
  avatar on (23,8), nothing in the tree can move it.** The chapter's own `:590-593` comment warns of
  exactly this; a later early-return re-opened it. `KI-97` moves this derail from Segment 13a to 19,
  not away. ✅ **That is exactly what was done** (bullet above): `leave_the_gym()` is resume-safe
  (`:471-474`), so calling it at Segment 18 and before the chapter's early-return costs nothing
  anywhere else. Detail: `ai-research-notes/2026-09-07-batch-blockers-RECON.md`.

---

## 2026-09-10 (fourth pass) — `#24-driftheadlineshape` retired (R3 budget)

Fully DONE, no open boxes, no owed drive. Residual check RUN, not assumed: `driftheadlineshape`,
`check_drift` and `D28a` each appear in at least two other files, so the block solely owns
nothing. Retired to make room for `#24-barecitationblindspot`, filed the same day.

### ✅ `#24-driftheadlineshape` — DONE 2026-08-26: `check_drift` PASS 3 reads the drift-row HEADLINE (filed 2026-08-24)

- [x] **SHIPPED 2026-08-26 — ⛔ do not rebuild.** `check_drift` PASS 3: the FIRST `N as of <date>`
      in any drift-labelled table row is compared to `real_drift()`; history deeper in the cell is
      exempt **BY POSITION** (the cell's own documented "today's number is at the TOP" convention —
      a declared exemption, not vocabulary). Fault-tested BOTH ways (D28a-e: fires on a wrong
      headline incl. word-form; quiet on right-headline-wrong-history — the inverted incident —
      non-drift rows, and fenced quotes) **plus a live INCIDENT REPLAY**: the real cell's `7`
      flipped to `2` turned the gate red at `04-HANDOFF.md:209` naming both figures, file restored
      byte-identical. Narrative: `07-CHANGELOG.md` 2026-08-26.

---

## 2026-09-10 (fifth pass) — `#24-hm07funnel` retired (R3 budget)

Fully CLOSED and driven at scale; its narrative already lives in `07-CHANGELOG.md`. Residual check
RUN: `hm07funnel` appears in `04-HANDOFF.md`, `06-DECISIONS-LOG.md` and `07-CHANGELOG.md`, so the
block solely owns nothing. Retired to make room for gate #52's entry.

### ✅ `#24-hm07funnel` — **CLOSED 2026-09-08, DRIVEN AT SCALE.** ⛔ DO NOT REDO.
- [x] Every HM funnelled onto one mon because Waterfall's and Dive's species pools are strict
  SUBSETS of Surf's (74 and 76 of 101, ZERO Surf-incapable) — forced by the learnset DATA, not by
  ranking. `pick_land_hm_slot()` (PURE) + `land_hm_learner_slot()` prefer a non-carrier at the two
  LAND-HM sites only; `hm_learner_slot` untouched so Surf and Dive keep the water mon.
  **MEASURED: Surf + Dive party-full went 7 of 53 → 0 of 49**, with 18 runs reaching Victory Road,
  so both teach points were passed — elimination, not avoidance. Detail: `07-CHANGELOG.md`.

---

## 2026-09-10 (sixth pass) — the stale front-of-file INDEX table retired

`03-PUNCH-LIST.md` opened with a table that its OWN heading called *“⛔ NOT AN ACTIVE LIST”* and whose
own body recorded that it *“has now gone stale TWICE the same way — it names whatever was live when
it was last edited”*, ending with *“`04-HANDOFF.md`’s NEXT ACTIONS queue is the thing to act from,
not this table.”* A cold reader who used it as the index worked from a 12-day-old picture.
⇒ Retired rather than repaired: **an index that must warn you not to use it is not an index.** The
handoff’s `➡➡➡` marker is the single live instruction, and that invariant is already gated.
Residual check RUN — all four slugs it names (`#24-loopheadabort`, `#24-p4residuals`,
`#24-ki76correctness`, `#24-sanitycheck`) appear in 5+ other files each, so it solely owns nothing.

### 1. ⚠ MIXED — ⛔ NOT AN ACTIVE LIST. Re-titled 2026-08-22 (PASS 5): **12 of its 16 rows are CLOSED**
> ⛔ **A HEADING IS A CLAIM ABOUT EVERY ROW BENEATH IT.** This table said "the only things being
> worked on now" while most rows carried ✅ DONE, and it named NEITHER live item. A cold reader
> using it as the index would have worked from a 12-day-old picture.
> ➡ **`#24-loopheadabort` IS DONE (2026-08-23, gate #30).** ⚠ **THE LIVE THING IS A PROMOTION
> DECISION — the USER's call** (drift: see the STATE row / `promote.py --check`). Then `#24-p4residuals`.
> ‼ *This row has now gone stale TWICE the same way — it names whatever was live when it was
> last edited. ⛔ `04-HANDOFF.md`'s NEXT ACTIONS queue is the thing to act from, not this table.*
> ⛔ **NOT `#24-ki76correctness`** — its only fixture is VACUOUS for its only live defect; and
> `#24-sanitycheck` is COMPLETE. *(This line named both of those as live until 2026-08-23 — it
> was written during pass 5 and went stale the moment pass 5 finished.)* — and
> `04-HANDOFF.md`'s NEXT ACTIONS queue, not this table, is what a session should act from.
> ‼ Rows below are kept for their evidence; read each row's OWN marker.
| item | state |
|---|---|
| `#24-battleitems` | ✅ **DONE & PROMOTED 2026-08-10.** Built, unit-proven (27 checks), live, self-correcting; validation batch `20260810-082509` passed (flips 20 → 2, both-failed 10 → 0). ‼ Outcome unproven — grade any follow-up on BATTLE-level metrics. |
| `#24-teachmsgstall` | ‼‼ **REOPENED 2026-08-11 by batch `20260811-130454`. The fix has NO production effect**: success 38/47 (80.9%) vs 38/42 (90.5%) pre-fix, **z = −1.28 NOT resolvable**; `post_select=exhausted` 8/85 vs 3/80, **z = +1.46 NOT resolvable**; and the new `already-advanced` exit fired **ZERO** times in 85 teaches. The one-frame window was real and decomp-confirmed, but it was **not the dominant production cause** — there is another path to `exhausted`. The fix stays (it closes a real hole and costs nothing). Original entry: **ROOT-CAUSED, FIXED, A/B-PROVEN.** The replace-prompt detector had a **ONE-FRAME window**: `Task_ReplaceMoveYesNo` swaps itself out for `Task_HandleReplaceMoveYesNoInput` on the frame it becomes answerable (decomp `src/party_menu.c`; measured f3232735 → f3232736). Missing it left a blind A-mash that reaches `Task_HandleStopLearningMoveYesNoInput`, where **A = give up**. Fixed by watching both spellings, an `already-advanced` exit, and B at the stop prompt. **A/B (same save, one env var): OLD `learned=False` / NEW `learned=True`.** ✅ **PROMOTED 2026-08-11 (user-approved), verified DRIVEN in `custom-pokebot` as the same A/B, frame-for-frame identical. Source drift: ZERO.** |
| `#24-grounditems` | 🟡 **PARTLY DONE 2026-08-12.** The shared helper **`collect_item_ball(map, ball_tile, approach, facing, flag, item_name)` is BUILT** and has two callers (the Magma Hideout Escape Rope, refactored onto it, and the Aqua Hideout Master Ball + Nugget) — the duplication this item existed to prevent never happened. `repro_hideout_exit.py` now checks the escape-rope path DELEGATES to it, so a future edit cannot quietly fork a second copy. ‼ Lessons baked in: grade on a **bag delta** (a FULL pocket makes `finditem` set no flag AND give no item, so a flag test hangs forever); an item ball is an OBJECT you stand beside, and not every neighbour is reachable; **the ball VANISHES when taken, freeing its tile** (that is how the Master Ball is reached at all). **WHAT REMAINS:** per-area sweep LISTS so chapters collect the balls they walk past. Known uncollected in already-built content: Aqua Hideout **Max Elixir** `B1F (29,12)` (all four approaches reachable from node `(27,12)`) and **Nest Ball** `B2F (3,13)`; Magma Hideout **Rare Candy** `1F (3,20)`. |
| `#24-npcgifts` | ‼ **NEW 2026-08-12 (user directive).** **Collect GIFT ITEMS from NPCs** — items a person hands you, which the bot currently walks straight past. Decomp-anchored starters: **EXP SHARE** — `RustboroCity_DevonCorp_3F_EventScript_MrStone`, gated on `FLAG_DELIVERED_STEVEN_LETTER`, sets `FLAG_RECEIVED_EXP_SHARE` (272); **QUICK CLAW** — `RustboroCity_PokemonSchool_EventScript_Teacher`, sets `FLAG_RECEIVED_QUICK_CLAW` (275). Both flag names verified present in `modules/data/event_flags/emerald.txt`. Shape: navigate to the NPC, face, A-ride the dialogue, grade on **the bag** (both scripts branch to `Common_EventScript_ShowBagIsFull`, which gives nothing and sets no flag). ‼ These are ORDINARY-PLAY value, not story-critical: an Exp Share collected in Rustboro compounds over every later chapter, which is exactly the organic-play goal. **Enumerate the full gift list from the decomp before building** — `giveitem` in `data/maps/*/scripts.inc` — rather than adding them one at a time. |
| `#24-masterball` | ✅ **DONE 2026-08-12 — the MASTER BALL is collected, driven PASS.** `master_balls=1 nuggets=1 escaped=True whiteouts=0`, and the driver's acceptance now REQUIRES it (read from the BAG, since a full pocket makes `finditem` set no flag and give no item). ‼ It cannot be taken directly: both of its free neighbours are unreachable, so the route takes the **Nugget** at `(15,10)` first and steps onto the tile the vanished ball frees. No Electrode is ever faced. ‼ The return leg had to be re-derived after a driven failure — the first one walked across a warp panel; `can_walk` in `probe_aqua_hideout_graph.py` is now panel-aware. |
| `#24-impassabledirs` | ✅ **DONE 2026-08-13 — FIXED, BOTH HALVES, A/B PROVEN, AND GATED.** `modules/map_path.py`: the entry vector now starts all-True and CLEARS `[opposite(D)]`, and a NEW `PathTile.blocked_exit_directions` carries the decomp's *exit* rule, checked on the SOURCE tile in the A* expansion loop (`is_tile_accessible` is handed the NEIGHBOUR and structurally cannot express it). **THE A/B, on `VICTORY_ROAD_1F`:** before → `repro_impassable_dirs.py` exits **1** with **29/29** live tiles reading `[--S-]` against a correct `[NE-W]`, and `calculate_path` returns **NO-PATH from every single direction** — all 29 walkable tiles were **completely invisible to the planner**; after → exits **0**, 0/29 mismatches, and the legal approaches return `OK len=1`. **COLLATERAL CONTROL:** the `MOSSDEEP_CITY` block of `probe_ki59_routing_ab.py` (a map with zero such tiles) is **byte-identical across both arms** — the two arms were produced with real production code via `git stash`, not by re-implementation. **NEGATIVE CONTROL:** `SEAFLOOR_CAVERN_ROOM1` reports **0 live tiles and 0 mismatches in both arms**, confirming from production objects that the branch is inert there. **New gate `repro_impassable_dirs.py` is in `run_gates.py` (suite reached 17 with it — 18 since `audit_doc_consistency.py`, 2026-08-14 — all PASS, 124.3s).** ‼ **`probe_shoal_tide.py` corrected IN LOCKSTEP** (it replicated the inversion, so it agreed with production while both were wrong) — and its headline numbers **re-derived on the fixed model are UNCHANGED: LOW 278 / HIGH 0, all controls PASS**, so the user-delegated **"Shoal Cave is NOT adopted"** ruling stands and now rests on a correct model. ✅ **PROMOTED 2026-08-14, user-approved — sandbox↔custom drift is back to ZERO** (it had reached 5: `map_path.py`, `early_game.py`, `story_mode.py`, plus `counter_hunt.py` and `pokemon_party.py` on 2026-08-14). Verified by DRIVING, not diffing: `--driver ch20dive --build custom` → `ACCEPTANCE: PASS`, `repro_box_counter_move_test.py --build custom` exit 0, drift was re-measured 0 both directions *(history: at that promotion)*. Restore point `restore/2026-08-14-pre-promotion-5files`. History and the measurement that reprioritised this item follow. ‼ **MEASURED 2026-08-13 — the INVERSION IS REAL but the TARGET MAP IN THE OLD TEXT WAS WRONG.** `tools/story-dev/probe_impassable_dirs.py` (NEW) swept **all 518 maps**. **The bug is REAL:** `map_path.py:128-132` starts `accessible_from_direction` all-False and **sets** `[opposite]` True, where ground truth is start all-True and **clear** `[opposite]`. For `Impassable North` the shipped model is `[--S-]` — the *exact complement* of correct `[NE-W]` — so it refuses the three legal entries **and permits the one illegal one**. ⛔ **BUT: `map_path.py:118` is `if tile.collision != 0:` and the `Impassable` handler is its `elif`, so a collision≠0 tile NEVER REACHES IT.** Measured: **2,658 such tiles game-wide, 2,257 DORMANT (collision≠0), only 401 (15.1%) LIVE.** ‼‼ **ZERO of the Seafloor Cavern's 115 are live** (all `collision=1`) — so the old instruction "A/B on `SEAFLOOR_CAVERN_ROOM1` before the cavern chapter exists" **would have measured nothing**, and this is **NOT a §Ch20 prerequisite**. **Where it IS live:** SHOAL_CAVE inner 77 + entrance 12 + high-tide 9; **DESERT_RUINS 48 / ISLAND_CAVE 48 / ANCIENT_TOMB 48 (the REGI arc — the user's ask, 144 tiles)**; LILYCOVE contest hall 40 + lobby 8; ARTISAN_CAVE_B1F 34; VICTORY_ROAD 1F/B2F/B1F 58; MIRAGE_TOWER_4F 5; GRANITE_CAVE_B2F 4; a tail of 1-3. Live strings: `North` 347, `East` 27, `West` 24, `North and South` 3. ✅ **THE FIX IS SPECIFIED AND DE-RISKED** (decomp-verified `gOppositeDirectionBlockedMetatileFuncs` / `gDirectionBlockedMetatileFuncs`, `event_object_movement.c:893-905, 4715-4722`): `MB_IMPASSABLE_<D>` means **"the tile's `<D>` EDGE is a wall"**, blocking entry *and* exit across it. ⇒ (a) `accessible_from_direction = [True]*4` then clear `[opposite(D)]`; (b) **a NEW exit-blocking concept is required** — `PathTile` cannot express "may not LEAVE in direction D" at all, and without it the fix still lets the planner walk north off a wall (22 of Island Cave's 48 live tiles have open floor to their north). ✅ **Hazards pre-checked, all clear:** the four `_is_optional_blocker` salt tiles are plain `Cave`, not Impassable (so the fix cannot defeat the salt gates); `Secret Base Breakable Door` (0xBE, a directional impassable the code misses) and `Secret Base Impassable` (0xB9, a false friend that must stay OUT) both occur **0 times** in this ROM. ‼ **`tools/story-dev/probe_shoal_tide.py:364-367` REPLICATES the inversion** and must change in lockstep — see the note under `#24-shoalcave`/KI-54. **Per-string split (live/total), which BOUNDS the fix:** `North` **347**/2601 · `East` **27**/27 (all live) · `West` **24**/24 (all live) · `North and South` **3**/3 (all live) · `South` **0**/3 (all dormant). **Five of the ten producible strings never occur in this ROM at all.** ⚠ **THESE ARE STATIC ROM LAYOUTS, NOT RUNTIME TRUTH.** Three of the four biggest live maps rewrite themselves: `setmetatile` appears in `DesertRuins`, `IslandCave`, `AncientTomb` (those ARE the braille walls opening), `ShoalCave_LowTideInnerRoom` and `LilycoveCity_ContestLobby`; `setmaplayoutindex` in both Shoal Cave low-tide rooms. So 77/48/48/48 describe the **compiled** layout, not what is on screen. ‼ **The Seafloor conclusion is UNAFFECTED — no `SEAFLOOR_CAVERN_ROOM*` script uses either command** (checked across the full result set). **REMAINS: the fix itself + an A/B.** ⇒ **RUN IT ON `VICTORY_ROAD_1F` (29 live tiles)** — it is the cleanest target because it does NOT rewrite itself, unlike Island Cave / Shoal Cave. **With a NEGATIVE control on a Seafloor room proving the branch is inert there**, and the A/B must assert **both** directions (entry AND exit), never on the Seafloor Cavern alone. |
| `#24-pathsourcecheck` | ‼ **NEW 2026-08-12 (KI-60), code-verified.** `calculate_path` never runs its SOURCE tile through `is_tile_accessible` — it seeds the queue unconditionally. So a path requested *out of solid rock* returns OK (this produced the wrong "different components" story in KI-57's first write-up), and an invalid source reports a bare "could not find a path" instead of naming itself. Low-risk fix = raise a distinct error on an inaccessible source, but it is shared code and needs its own A/B. |
| `#24-mossdeepgym` | ✅ **DONE 2026-08-12 — §Ch18 runs END TO END and is WIRED into the ladder (Segment 18).** `--driver mossdeepbadge` gives `badge=True map=MOSSDEEP_CITY_GYM at=(23,8) controllable=True whiteouts=0`; `BADGE07_GET` set after 754 frames; anchor `saves/post_mossdeep_gym.ss1`. The ladder reached **19/24** with this item (current: **20 of 24 beats**, since §Ch19). ‼ An adversarial review then found a defect the PASS could not have caught (the whiteout path checked the map only at entry, and raised `RuntimeError` where the chapter catches `BotModeError`, so the recovery could never fire) — fixed and proven by `repro_gym_whiteout_guard.py`, which INJECTS the fault. History below. ✅ Leg 1 driven PASS (`--driver mossdeeptravel`, `whiteouts=0`, anchor `in_mossdeep_gym.ss1`). ✅ **KI-58 resolved:** the gym is a **ROTATING-TILE STATUE PUZZLE** — nine floor switches call `moverotatingtileobjects`, shifting every object on a matching coloured arrow one tile. ✅ **NEW 2026-08-12: `modules/story/mossdeep_gym_puzzle.py` simulates it, and `probe_gym_simulate.py` PASSES** — 11/11 loaded objects predicted on a live press, identity-keyed on `local_id`, plus a period-4 identity control on all five colours. Encoding derived from the ROM dump: band = `(mt-0x250)//8` (`0 Yellow 1 Blue 2 Green 3 Purple 4 Red`), code = `(mt-0x250)%8` (`0 Right 1 Down 2 Left 3 Up`), **codes 4/5 = that colour's switch**. ‼ Movement is a **rigid simultaneous rotation with NO occupancy check**; **nine TRAINERS rotate too**; statues are `graphics_id == 224`. ‼ **"5 counters mod 4" is unsafe** — use the full object-position tuple. ‼ `(23,7)/(24,7)` are collision-1 — target `(23,8)/(24,8)` facing NORTH, press A; they need **≥2 usable Pokémon**. ‼ `(21,6)` ejects to `(7,30)` and is **not flag-gated**. ‼ **Leaving the gym RESETS the puzzle**; internal warps preserve it. ‼ **Solving the puzzle AIMS THE TRAINERS AT YOU** — pressing yellow at `(3,30)` puts Maura adjacent and facing you; gym battles are a consequence of the mechanic, not a derail. ✅ **SOLVER + EXECUTOR BUILT AND DRIVEN 2026-08-12:** `--driver mossdeepgym` gives `at_leaders=True map=MOSSDEEP_CITY_GYM at=(23,8) controllable=True whiteouts=0`, the 117-step route walked in a single plan with zero re-plans; anchor `saves/at_mossdeep_leaders.ss1`. The BFS route matches both agent-derived routes switch-for-switch. ✅ **The Tate & Liza DOUBLE battle is built and driven** (`fight_the_leaders`): the ≥2-usable-Pokémon gate is checked up front rather than discovered, and the chapter allows three attempts because a whiteout leaves the gym and leaving RESETS the puzzle. ‼ Still UNEXERCISED: the executor’s own interruption branch (the trainer battles that fired were handled by the standard listeners) and the real whiteout path (both driven runs had `whiteouts=0`; the guard is proven by fault injection, not by a live loss). ✅ **AND the chapter now LEAVES the gym** (it was stranding the run on an eleven-tile island; the acceptance test now requires being outside). **NEXT: §Ch19, the Mossdeep Space Center** — groundwork + measured hazards in `modules/story/space_center.py` and `tools/story-dev/probe_ch19_hazards.py`; ‼ §Ch21 is BLOCKED by KI-63 (no Dive learner, party full) — beating the leaders already sets `VAR_MOSSDEEP_SPACE_CENTER_STATE=1` and unhides Team Magma + Steven. |
| `#24-spacecenter` | ✅ **DONE 2026-08-12 — §Ch19 runs END TO END and is WIRED into the ladder (Segment 19).** One chapter covers BOTH the Space Center defence and the Dive hand-over, because `chapters.py` grades chapter 19 on `RECEIVED_HM_DIVE`. Driven from `post_mossdeep_gym.ss1`: `dive=True hm08=True MOSSDEEP_SPACE_CENTER_STATE=3 map=MOSSDEEP_CITY at=(19,11) controllable=True whiteouts=0`, **CAN-CONTINUE OK(15wp)**. The ladder now runs **20 of 24 beats**. Anchors captured: `at_steven_2f.ss1`, `post_space_center.ss1`, `post_dive.ss1`. Drivers: `--driver spacecenter1` (legs 1-3), `spacecenter2` (the menu + multi battle), `spacecenter` (whole chapter; run it from `post_space_center.ss1` too — that PROVES the resume guards by skipping to leg 6). ‼ **THE CITY IS CUT IN TWO** until the forced cutscene runs: the gym victory SPAWNS five Team Magma NPCs onto the only land bridge (x=44, y=23-26) and our planner blocks loaded-object tiles, so leg 1 is TWO legs — trigger line, assert `VAR_MOSSDEEP_CITY_STATE == 2`, then the door. I first mis-blamed KI-59 for this; see `08-MISTAKES.md`. ‼ **THE STAIR GRUNT MUST BE TALKED TO** (`sight_radius = 0`, stands ON the only tile the stairs are reachable from) — navigating there can never succeed. ‼ **THE PARTY-SELECT MENU IS NOW SOLVED AND VERIFIED LIVE:** cursor slots 0-5 are mons, **6 = CONFIRM**, each pick is `A` (submenu) then `A` (ENTER) and **the cursor does not advance**; A on an already-picked mon DESELECTS it, so blind A-mash toggles for ever. Every pick is verified against `gSelectedOrderFromParty` — measured `[1,5,3,0]` against `INTENDED-PICKS [0,4,2]`, an exact match (Sceptile L48 / Mightyena L44 / Swellow L40). **Always bring 3**: the loss condition sums HP over the player's picks ONLY, so bringing fewer is strictly worse. ‼ **Losing is a RETRY, not an error** — the script calls `SetCB2WhiteOut` itself, halves the money and warps to the last heal location, but leaves the var at 2; leg 1's heal matters twice over because the anchor's respawn was measured to be **LILYCOVE**, across the sea. ‼ **§Ch19 nearly ended INSIDE Steven's house** — caught by the acceptance's `calculate_path` off the end tile, KI-56's rule for the third time. |
| `#24-remainingarc` | 🔜 ✅✅ **2026-09-07 — `KI-95`, `KI-93` AND THE L60 GRIND ALL SHIPPED OVERNIGHT; THE LIVE BLOCKER IS NOW `KI-96`. ⛔ **SUPERSEDED 2026-09-07 (evening): `KI-96` IS SOLVED AND DRIVEN — the live blocker is now `#24-regimeb-noescalation`.**** The party is at **L60** (`post_grind_L60.ss1`, PINNED — 623 battles, 0 whiteouts, `--driver ch24grind`), the Torment livelock is FIXED and the bot **beats Sidney** (⚠ on its last Pokémon, 5 of 6 fainted), and the faint chooser now ranks on expected damage (gate #39). ⛔⛔ **BUT LEVELLING ALONE DOES NOT UNBLOCK §Ch24:** §Ch23's chain now wedges in the in-battle PARTY MENU (`KI-96`, an unbounded `while PARTY_MENU: press A`, A/B'd as PRE-EXISTING and present in BOTH forks) before the League door. ⇒ **✅✅ **SUPERSEDED 2026-09-07 (evening) — `KI-96` IS SOLVED AND DRIVEN; ⛔ IT IS NOT THE NEXT JOB.** Read it for the ANSWER, not for work; the live queue is the `➡➡➡` marker in `04-HANDOFF.md`. *(was: read `KI-96` in `05-KNOWN-ISSUES.md` — it is the next job.** ⛔ All of it is SANDBOX-ONLY; for the live drift run `promote.py --check` (the authority; never restated here) — the arc-2 four were PROMOTED 2026-09-07 (user-authorised, verified by driving); the KI-96 probe fix, #24-truckleak, #24-pcpingpong and #24-hm07teach are sandbox-only — ⛔ **the batch that blocked promotion FINISHED 2026-09-08 (`x4-runs/20260907-203713`), so nothing is waiting on it; PROMOTING IS THE USER'S CALL**. *(This cell's own rule says its FIRST WORDS are what a skimmer acts on, and it advanced four times on 2026-09-06/07; a Tier 2 cold-start audit caught it still routing readers to the CLOSED `#24-ch23chain`.)* Older text follows. 🔜 **§Ch23 (VICTORY ROAD) IS A CHAPTER AS OF 2026-09-05 — ALL ELEVEN LEGS **AND** THE ORCHESTRATOR + SEGMENT 23 WIRING ARE SHIPPED AND DRIVEN. ⛔ DO NOT REBUILD ANY OF IT. ‼ **§Ch24 (THE ELITE FOUR) IS THE ONLY CHAPTER WITH NO DISPATCH AT ALL**, and §Ch23's CHAIN **PASSES** (`ACCEPTANCE: PASS`, `done=True`, `battles=16`, `whiteouts=0`, 2026-09-05) — *(this read "RE-DRIVEN 2026-09-05 AND IT FAILS FOR A KNOWN REASON: the party LOSES the leg-9 Katelynn+Quincy DOUBLE battle on VICTORY_ROAD_1F and whites out" — **SUPERSEDED THE SAME DAY: the chain now PASSES**, `done=True`, `whiteouts=0`)* (`ACCEPTANCE: FAIL`, `battles=16`, `whiteouts=1`, `outcome=BattleOutcome.Lost` at f67819). ✅ KI-90's fix HELD — same fight, same start frame (f56544) as the previous drive, but no raise and no hang: the bot could act, and lost. ⇒ ⛔ **RETRACTED 2026-09-05 — this read "the wall moved from a BOT DEFECT to a GAME PROBLEM (levelling/strategy)" AND IT IS REFUTED BY THE DRIVE LOG.** It is still a BOT defect: the bot entered the fight with **two mons already at 0 HP** after eight battles with no heal, and **no heal ever runs on this floor**. The opposition is **L43** against our L52/L48/L47/L47. ⇒ the wall moved from ONE bot defect (a hang) to ANOTHER (unwired healing). See `06-DECISIONS-LOG.md` / `08-MISTAKES.md` 2026-09-05. ⭐ MEASURED, not counted from memory: the last `_guard(...)` in `story_mode.py` is `"Victory Road (Ch23)"` and there is no Ch24 guard — `grep -oE '_guard\("[^"]+"' plugins/custom_modes/story_mode.py | tail -1`. *(An earlier draft of this clause said "THE LADDER IS 24 OF 24 BUILT". ⛔ I could not derive that denominator from the code — the older cells say "23 of 24" while ALSO listing TWO chapters as remaining, which cannot both be true. A number you cannot re-measure does not belong in a current-state file; the grep above can be re-run.)* ⛔ Its live item is `#24-ch23chain`; read THAT, not this cell.** *(superseded: this opened "IS UNDERWAY … LEG 1 IS SHIPPED" and pointed at `#24-ch23victoryroad`, whose own header then commanded rebuilding the orchestrator. This cell's own note demands its FIRST WORDS change when the item advances — this is the third time that was needed.)* ‼ The route legs and the Victory Road boulder puzzle remain; the ladder is **23 of 24** and only §Ch23 and §Ch24 (Elite Four) are left. ⛔⛔ **AND THE ONE THING A SKIMMER MUST NOT MISS: TWO BOULDER PUSHES SEAL VICTORY ROAD B1F FOR THAT VISIT — never push (4,7) or (9,10) SOUTH.** ✅✅✅ **§Ch22 IS A CHAPTER AS OF 2026-09-03 — GYM 8, JUAN, THE RAIN BADGE, WIRED AS SEGMENT 22 AND DRIVEN TO `ACCEPTANCE: PASS`. THE LADDER IS 23 of 24, AND ONLY VICTORY ROAD (§Ch23) AND THE ELITE FOUR (§Ch24) REMAIN.** ⛔ Read `#24-ch22chapter` for its detail, not this cell. ‼ *(This cell's FIRST WORDS are what a skimmer acts on — it opened with "§Ch20 IS A CHAPTER" through two whole chapters of work, and with "§Ch21 IS A CHAPTER" through one more. ⇒ when this item advances, change the FIRST WORDS.)* ✅✅✅ **§Ch21 IS A CHAPTER AS OF 2026-09-02 — ALL FIVE LEGS **AND** THE `_play()` WIRING ARE SHIPPED AND DRIVEN. ⛔ DO NOT REBUILD ANY OF IT.** `--driver ch21chapter` from `post_ch20.ss1` → `ACCEPTANCE: PASS`, `frames=95823` (MEASURED), `encounters=26`, `whiteouts=0`, ending SOOTOPOLIS_CITY (31,34) with the GYM WARP (31,32) reachable in 2 wp and HM07 in the bag. ‼ **IT ALSO MEASURED THE PARTY HANDOVER: §Ch21 has two heals and NONE after leg 3, so **MEASURED: `post_hm07.ss1` is SIX ALIVE at 629/694 (91%), lead 52/115 — NOTHING is fainted.** ⛔ *(A claim that it "ENDS chipped, one member fainted, lead 25/115" stood here on 2026-09-02 and was WRONG: that is the CHAPTER DRIVE's end party from a DIFFERENT run (`post_ch20.ss1` → legs 1-5), which was never captured to a fixture. An adversarial refuter caught it and my own re-measurement confirmed it — see `08-MISTAKES.md`.)* ‼ **BOTH states are real, and §Ch22 must handle the WORSE one:** a live §Ch21 handover arrives chipped HARDER than the pinned fixture suggests. ⇒ **§Ch22 inherits a chipped party and its first act is almost certainly the Poke Center (43,32), 22 wp away and MEASURED reachable.** ⇒ **§Ch23 — VICTORY ROAD IS NOW WIRED** (`chapters.py:280-286`, graded on `DEFEATED_WALLY_VICTORY_ROAD` for the READOUT — the DISPATCH gates on `ch23_chapter_done()`, which is that flag **AND** a position, because the flag fires at leg 5 of 11). *(superseded: cited `chapters.py:259-262`, which is Segment 21's neighbourhood — verified against the code 2026-09-05.)* ⛔ *(This read "NEXT IS §Ch22 — GYM 8, JUAN" until §Ch22 shipped on 2026-09-03; §Ch22's own items are `#24-ch22juan` and `#24-ch22chapter`, both CLOSED.)* Detail: `07-CHANGELOG.md` 2026-09-03. *(⛔ THIS CELL OPENED WITH "§Ch20 IS A CHAPTER AS OF 2026-08-24" THROUGH TWO WHOLE CHAPTERS OF WORK — a Tier 2 cold-start audit caught it, calling it "the exact P5 shape the rule was written for": the live status was buried ~3,000 words into a single cell. ⇒ when this item advances, THE FIRST WORDS OF THIS CELL are what to change.)* ✅✅✅ **§Ch20 IS A CHAPTER AS OF 2026-08-24 — ASSEMBLED, WIRED AND DRIVEN. ⛔ DO NOT REBUILD IT.** `modules/story/seafloor_cavern.py` (971 lines, nine legs + orchestrator) is wired as **Segment 19b (organic Dive) + Segment 20**, graded on `_done_var("ROUTE128_STATE", 2)` — never the pre-warp Kyogre flag. `--driver ch20chapter` drives the PRODUCTION entry point (not a copy) and returned **5/5 ACCEPTANCE: PASS**: clean (`done=True var2=2 surfing=True at=(38,24) ocean_path=True`), plus ALL THREE recovery paths exercised by fault injection — `room8_recoveries=1` for an in-room jam, and `route128_resumes=1` **with `room8_recoveries=0`** proving attempt 2 never re-dived into the permanently-disarmed trigger. ‼ Acceptance includes *and the bot can continue*: a real `calculate_path` to the open-ocean probe, not the 41-tile lagoon. ⚠ **NOT proven:** organic Dive in the same run (the driver injects it, so these are ASSEMBLY tests) and a LOST Archie fight (stochastic, 2W/1L measured; all five runs won). ‼ An adversarial review found **4 blockers, all in the orchestration glue** — the dropped per-push `try/except` (a jam skipped the fault-proven recovery), a once-only resume check, an unguarded `PathFindingError`, and a missing loop-head abort; fixing them exposed 3 undefined names on exactly those branches. ➡ **§Ch21 IS UNDERWAY, NOT UN-STARTED** (updated 2026-09-01): legs 1 + 2a + 2b + 3 + 4 **and 5** are BUILT AND DRIVEN (leg 5 shipped 2026-09-02) — **ALL FIVE LEGS EXIST, AND SO DOES THE `_play()` WIRING**: §Ch21 became a CHAPTER on 2026-09-02 (Segment 21, driven end to end — see later in this cell). *(This clause read "what remains is the `_play()` WIRING, which does NOT exist yet" for a few hours between the leg-5 commit and the wiring commit; a Tier 1 reviewer caught it contradicting the SAME CELL's own later text.)* ✅✅✅ **LEG 3 (THE APPROACH) SHIPPED 2026-09-01 — ⛔ DO NOT REBUILD IT.** `--driver ch21approach` from `post_wallace.ss1` → `ACCEPTANCE: PASS`, **all 14 readings, `missing=[]`**, `frames=34122` (MEASURED, replacing the spec's ~55,000 estimate), `encounters=9`, `whiteouts=0`, `pocket_attempts=1`, `method_ok=True`, `premise_ok=True`; fixture **`post_skypillar_door.ss1` PINNED** (⚠ party at 91% HP — no Poke Center after Sootopolis). THREE fault arms ran (the third added after an ADVERSARIAL REVIEW found a BLOCKER — the pocket recovery's OWN walk-back was not guarded against the exception it recovers from, so a second stall escaped the retry budget as a raw exception; it now raises a NAMED "stranded" error, proven by `POKEBOT_CH21_FAULT_POCKETWALKBACK=1`): `POCKETSTALL` → `pocket_attempts=2` and still PASS (**the pocket recovery was the leg's one designed-but-UNPROVEN component and is now a RESULT** — a second arrival DOES re-open the pocket, and the retry loop terminates); `BLINDWALL` → fails LOUDLY naming the step index, bounded, **no hang**. ‼ Three things were measured for the FIRST time: the ROUTE131 layout divergence read **live in-drive** (`planner=0x08417FE4 live=0x0845C1B0 agree=False`, and 0 of the 18 tiles the leg walks are live walls); a **blind step executed onto a tile our own planner calls a WALL** ((40,19) — no such step had ever been taken in this project); and the resting-tile rule's **first arrow-warp case**, which CONFIRMS it ((6,16), matching prediction) — while the SAME leg produced its first REFUTATION, `UNDERWATER_ROUTE126`'s rest being **(45,66)**, not the warp target (45,65) that BOTH build-spec critics hard-asserted. ⛔⛔ **AND THE FIRST DRIVE FOUND A DEFECT CLASS THE WHOLE TREE WAS BLIND TO:** `_map_layout_cache` (map.py:735-755) is keyed by **MAP ALONE**, so the LIVE and STATIC layout readers share one entry and whichever reads first wins FOR THE PROCESS — `calculate_path` silently inherits it. The bot walked into a 9x3 block of solid rock in Sootopolis; A/B proven (37 wp with 3 live walls → 35 wp with none, `evidence/2026-09-01-ch21-leg3-LAYOUTPIN-ab.txt`). New instrument **`tools/story-dev/probe_live_mapgrid.py`** reads `gBackupMapLayout` — the grid the GAME walks on — and is the FIRST reader in this tree that can observe `setmetatile`/`setmaplayoutindex` at all (KI-74 had been unobservable in principle). ✅✅✅ **LEG 4 (THE SKY PILLAR CLIMB + DESCENT) SHIPPED 2026-09-01 — ⛔ DO NOT REBUILD.** `--driver ch21climb` from `post_skypillar_door.ss1` → `ACCEPTANCE: PASS`, all 15 readings, `order_ok`, `frames=10079`, both DELIBERATE FALLS, RAYQUAZA awakened (5/1/1), all 7 floors pinned to CLEAN, SEVEN fault arms all FAIL for their own reason (evidence `2026-09-01-ch21climb-CLEAN.txt` + `-FAULTARMS.txt`). Fixtures PINNED: `post_wallace_scene`, `post_skypillar_summit`, `post_rayquaza_gone`. ‼ Its recon KILLED TWO PLANS before a drive: `_bounded_step` cannot express a fall (asserts SAME-map), and `_live_wall_tiles` is crack-BLIND. ✅✅✅ **LEG 5 (THE RETURN + HM07 WATERFALL) SHIPPED 2026-09-02 — ⛔ DO NOT REBUILD.** PART C ran FIRST as the queue demanded (`--driver ch21leg5probe`, `ACCEPTANCE: PASS`, P0-P6, `frames=16297`, predictions filed before the drive in `ai-research-notes/2026-09-02-ch21-leg5-PARTC-PREDICTIONS.md` and graded in `…-RESULTS.md`), then PART D (`--driver ch21return`, `ACCEPTANCE: PASS`, **all 13 readings, `missing=[]`, `order_ok`**, `frames=20705`, `whiteouts=0`, `hm07_in_bag=1`, `wallace_state=1`, `gym_door_wp=2`). Fixtures PINNED: `post_legends_calmed.ss1` (mid-leg, so the NPC half iterates in ~4,600 frames instead of re-swimming) and `post_hm07.ss1` (the chapter's end state). ‼ **GATE 1 SETTLED BY AN ARM WITH THE PIN REMOVED:** un-pinned, ROUTE131 -> ROUTE126 raises `PathFindingError` and the bot never moves — the pin is not an optimisation, it is the only reason a plan exists. ‼ **GATE 2 SETTLED:** the state-5 Sootopolis layout is SAFE — the pin is a NO-OP and 0 of 3600 tiles are open-to-planner/wall-live (the 10 diffs are all locked DOOR warps). ⛔⛔ **AND DRIVE 1 PASSED WHILE SEALING §Ch22:** `_ride_talk` returned mid-script, so Wallace never stepped off the (31,33) tile that blocks the (31,32) GYM warp, and the 'can continue' check had been aimed at the Poke Center, which is reachable either way. FIXED (ride now requires `not script.is_active`; new `R-GYMDOOR` reading) — see `08-MISTAKES.md` 2026-09-02 for that and for the held-button msgbox hang the fix then exposed. ⇒ **NEXT IS THE CHAPTER WIRING** — ✅✅✅ **§Ch21 IS A CHAPTER AS OF 2026-09-02 — WIRED INTO `_play()` (Segment 21) AND DRIVEN END TO END: `--driver ch21chapter`, `ACCEPTANCE: PASS`, `frames=95823` (MEASURED), `encounters=26`, `whiteouts=0`, ending SOOTOPOLIS_CITY (31,34) with the GYM WARP reachable in 2 wp. ⛔ DO NOT REBUILD IT.** The chapter ladder moves 20 → 21 of 24. ‼ It also measured what nothing had: the party STARTS chipped (one fainted at 80%) and **MEASURED: `post_hm07.ss1` is SIX ALIVE at 629/694 (91%), lead 52/115 — NOTHING is fainted.** ⛔ *(A claim that it "ENDS chipped, one member fainted, lead 25/115" stood here on 2026-09-02 and was WRONG: that is the CHAPTER DRIVE's end party from a DIFFERENT run (`post_ch20.ss1` → legs 1-5), which was never captured to a fixture. An adversarial refuter caught it and my own re-measurement confirmed it — see `08-MISTAKES.md`.)* ‼ **BOTH states are real, and §Ch22 must handle the WORSE one:** a live §Ch21 handover arrives chipped HARDER than the pinned fixture suggests., because §Ch21 has two heals and none after leg 3 ⇒ **§Ch22 inherits a chipped party**. ⇒ NEXT IS §Ch22 (Gym 8, Juan). ⛔ **A CLAUSE HERE CLAIMED `chapters.py` "does not yet consume `RECEIVED_HM_WATERFALL`" — THAT WAS FALSE and is corrected 2026-09-02:** `chapters.py:250` already grades §Ch21 on that flag and `progress.py:40` maps it, so the wiring needs NO `chapters.py` edit. ‼ What it DOES need: a gate on leg 1, which has no resume guard of its own (`sootopolis.py:194` swims to ROUTE126 unconditionally, impossible from zero-connection Sootopolis), and `sootopolis_reached()` (`:99`) is DEAD CODE so no shipped predicate exists for it. ⇒ the live status is in THIS item's headline above and in `04-HANDOFF.md`'s queue. Older text follows. 🔄 **THE SEAFLOOR CAVERN IS DRIVEN END TO END (2026-08-14, latest) — KYOGRE AWAKENED, THE ATOLL ESCAPE EXECUTED; what remains of §Ch20 is the CHAPTER ASSEMBLY.** `--driver ch20room9` (NEW) → `ACCEPTANCE: PASS` ×2 (runs 1 & 3): Rooms 1→8 re-proven, the `(17,42)` trigger (gate `VAR_SEAFLOOR_CAVERN_STATE == 0` verified live), the Archie SINGLE battle, the Kyogre chain ridden with three bounded milestones, release gated on **`VAR_ROUTE128_STATE == 2`** (‼ the first `releaseall` is a decomp-proven trap — Room 9's script tail releases on Route 128 BEFORE the Steven scene re-locks), landing `(38,22)` with all mid-warp invariants exact, **facing on release MEASURED `'Up'` ×2** (previously decomp-only), and the measured escape `(38,23)` → Surf `(38,24)` → `OCEAN-PATH OK len=5` to the dive tile. **10/10 pre-registered predictions held** (`ai-research-notes/2026-08-14-ch20-room9-drive-predictions.md`). ⚠ **Run 2 LOST the Archie fight — 2W/1L measured, the chain's ONE stochastic element** — the party arrives chipped (no heal in the cavern; run 3 telemetry: one mon fainted, lead 96/135, usable=5), and a lost run prints NO RESULT (whiteout → Manual → generator dropped; the `PRE-ARCHIE PARTY` line is the attribution record). Ruled in `06-DECISIONS-LOG.md`: a loss is a VALID BRANCH — the chapter carries a bounded whiteout-retry (each retry = full re-dive, ~25 min) + pre-boss readiness. ‼ Pre-run adversarial review caught the museum-greeter bug being re-written into the new ride loop (A mashed across the release seam) — fixed BEFORE run 1 with the gated `A`-if-`is_waiting_for_input()`-else-`B` press (`08-MISTAKES.md`). Counts: **R1 n=13, R2 n=10, R6 n=9, R3 n=8, R8 n=5, R9 full-chain n=2.** ⇒ **NEXT: ASSEMBLE §Ch20 AS A CHAPTER** (Segment 20; organic Dive via KI-63's wiring; Repel policy — Blocker 3; badge/move pre-flight — Blocker 4; whiteout-retry; grade the segment on `VAR_ROUTE128_STATE == 2` + escape + can-continue, NOT on the pre-warp Kyogre flag). ⛔ Still NOT a chapter; ladder remains 20 of 24. Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH ROOM 8 — THE BOT STANDS IN ROOM 9 (2026-08-14). `--driver ch20room8` (NEW) → `ACCEPTANCE: PASS` twice: once CLEAN (first attempt — 9/9 pushes, `attempts=1`) and once FAULT-INJECTED (`POKEBOT_CH20_FAULT=room8`: the jam-recovery handler was EXERCISED, not just written — exit to Room 3 via the `(5,12)` arrow warp, re-enter, all twelve boulders respawn, retry clean; `recovered=True attempts=2`).** OUR adjudicated 9-push sequence (⛔ step 9 faces **LEFT**) executed exactly as tabled; an independent offline refutation pass (our ROM reader + the pret decomp agreeing on all 12 boulder templates, simulation checker itself fault-tested) returned **SURVIVES** before the drive. Exit path `(5,4)→(5,2)` `OK len=2`, **no boulder on `(5,3)`**, `ROOM9 (5,4)` arrival, real step taken. **9/9 pre-registered predictions held** (`ai-research-notes/2026-08-14-ch20-room8-drive-predictions.md`) — including KI-77's window predicting **exactly 8 of 12** boulders visible at arrival. The Room-3 walk was extracted VERBATIM into `_cross_room3` so ch20room8 inherits it; neutrality proven by re-running `--driver ch20room3` → PASS. Re-proof counts now: **R1 n=10, R2 n=7, R6 n=6, R3 n=5, R8 n=2.** ‼ Adversarial review of the diff found one real defect BEFORE it ran: the recovery hardcoded `"Down"` instead of deriving the hold direction from the live tile (the `_cross_room6` rule) — fixed, and the fault run then showed the arrow warp fires during the navigate itself, which the hardcode would have handled blindly. ⇒ **NEXT: ROOM 9** — the 62-step walk to the trigger `(17,42)` (⛔ NOT `(16,42)`, which is plain floor), Archie, Kyogre, grade on `VAR_ROUTE128_STATE == 2` (never the Kyogre flag), and the atoll exit: step SOUTH to `(38,23)`, face Down, Surf onto `(38,24)`. ⛔ Still NOT a chapter — no module in `modules/story/`, drivers inject Dive; the ladder remains 20 of 24. Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH ROOM 3 — THE BOT STANDS IN ROOM 8 (2026-08-13). `--driver ch20room3` → `ACCEPTANCE: PASS`, reproduced twice.** The WALK route: 18 steps, **zero pushes**, ending `SEAFLOOR_CAVERN_ROOM8 (5,12)` with a real step. It re-proves every room beneath it → **Room 1 n=7, Room 2 n=4, Room 6 n=3**. ✅ **THE DOUBLE-BATTLE CLAIM IS CONFIRMED LIVE:** one trainer battle in Room 3, `is_double=True`, at exactly `(6,5)`, with `usable=6` asserted BEFORE the walk so the result is attributable. ⛔ **My own discriminator printed a false "REFUTED"** — it counted trainer battles run-wide and swept in the Room 1 grunt; **the instrument was wrong, not the claim**, and it was caught because `saw_double` was reported rather than graded and the raw log printed the map next to the judgement. ✅ Two wild encounters fired, one **between two Strength pushes** — closing a gap the Room 2 note flagged as untested. ✅ An adversarial review of increment 3 found a real BLOCKER (a design decision that lived only in a commit message, never in `06-DECISIONS-LOG.md`) — closed. ⇒ **NEXT: BUILD `--driver ch20room8`** (‼ it does **not exist yet** — it is the thing to write, not a command to run), **using OUR 9-push sequence** — ⛔ **step 9 faces LEFT, never UP** (`(5,3)` permanently seals the exit); a jam is recoverable by exiting to Room 3 and re-entering. **Then Room 9** (62-step walk to the trigger `(17,42)`, Archie, and the atoll exit). Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH THE ROOM 6 CURRENT MAZE AND THE BOT STANDS IN ROOM 3 (2026-08-13, latest). `--driver ch20room6` → `ACCEPTANCE: PASS`, first drive, 8/8 pre-registered predictions.** ‼ **THE FIRST EXECUTED CURRENT CROSSING IN THIS PROJECT** — Rooms 6/7 were planner-level only until now, and *a plan is not a walk*. ⇒ **"Rooms 6/7 need no solver" now rests on a WALK.** ⚠ The **endpoint** is proven, not the intermediate slide behaviour. ✅ **And Room 3's arbitration was confirmed LIVE in the same run:** `calculate_path((4,15)→(8,1))` = `OK len=18` **containing `(6,5)`** ⇒ **Room 3 is crossable PUSH-FREE, so its 7-boulder puzzle is OPTIONAL**, and the walk **must** take the trainer battle (decomp: a single **DOUBLE** battle, still unobserved live). ⛔ **An earlier agent pass called our build spec "REFUTED" on Room 3 and was ITSELF WRONG** — I propagated it into the docs before a deeper pass corrected it; *an agent's REFUTED needs the same two independent authorities as a CONFIRMED*. ‼ **The drivers also DERAILED instead of failing** on the one branch three green runs never took (`AttributeError` on `self.moved`) — found by adversarial review, reproduced via the new permanent hook **`POKEBOT_CH20_FAULT=room1`**, fixed, A/B proven. **Room 1 is now n=5, Room 2 n=2.** ⇒ **NEXT: `--driver ch20room3`** (the WALK: `navigate_to(ROOM3,(8,1))`, 18 steps, zero pushes, precondition ≥2 usable Pokémon, graded on both trainer flags SET), **then Room 8** with OUR 9-push sequence — ⛔ step 9 faces **LEFT, never UP**. Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH ROOM 2 (2026-08-13). `--driver ch20room2` → `ACCEPTANCE: PASS`, first drive, 10/10 pre-registered predictions.** It re-solves Room 1 from scratch every run (`FLAG_TEMP_*` objects respawn on map load), so **Room 1 is now n=3**. Route: smash `(8,7)` → **exactly three** north pushes of boulder `id 4` → `(6,1)` → `SEAFLOOR_CAVERN_ROOM6 (11,21)`, then a real `calculate_path` to the room's exit `(4,1)` = `OK len=13` **measured from inside** — matching what `probe_ch20_currents.py` predicted from outside. ‼ **THE HEADLINE IS A CORRECTION TO OUR OWN SHIPPED SOURCE:** `FLAG_SYS_USE_STRENGTH` read **False** right after the ROOM1→ROOM2 warp, so `early_game.py`'s *"NEVER CLEARED … once per SAVE"* was wrong — it is cleared on EVERY warp (`ClearTempFieldEventData` → `LoadMapFromWarp`). The old claim rested on a search for the SCRIPT MACRO `clearflag`; the clear is the C function `FlagClear`. The CODE was always safe (`strength_push` re-checks per call) — this was load-bearing documentation on top of correct code. Both comments fixed; **for the live drift run `promote.py --check` (the authority; never restated here)** — as of that entry the drifting files were (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) — the guard was PROMOTED 2026-08-16** (`early_game.py` was already one of them). ‼ **KI-77 CORRECTED TWICE the day it was filed:** the despawn window is derived (20x17, predicts our live dump 5/5) so **"armed in Room 8" is REFUTED** (Room 8 is 11x14, smaller than the window — the LARGE rooms are the risk), and the game **physically resets a pushed boulder to its template tile on despawn**, so the planner is fail-safe and never under-blocks. ⚠ **THE UNTESTED DANGER IS THE EXIT:** the chapter lands on `ROUTE128 (38,22)` **facing north**, and north is a **41-tile closed lagoon** with `allow_escaping: false` ⇒ **step SOUTH to `(38,23)` and Surf**. ⇒ **NEXT: ROOM 3 — arbitrate first; it is NOT the walk the spec calls it (7-boulder puzzle omitted, trainers unavoidable on the push-free line, and a boulder can block the `(9,13)` retreat warp).** Room 8 is already adjudicated — use OUR 9-push sequence, and ‼ **step 9 faces LEFT, never UP** (`(5,3)` permanently seals the exit). Older text follows. 🔄 **§Ch20 INCREMENT 1 IS DRIVEN AND PASSING (2026-08-13): the bot is INSIDE the cavern and through ROOM 1.** `--driver ch20room1` → `ACCEPTANCE: PASS` first drive — ingress `legs 5/5`, `ROOM1 (5,18)`, Rock Smash + **two `strength_push`es verified by `local_id`** (boulder 1 → `(5,12)`, boulder 2 → `(13,11)`), ending `ROOM2 (10,7)` controllable with a real step taken. ‼ **The A/B is the result, not the arrival:** `calculate_path(→ (11,11))` went `PathFindingError` → `OK len=6` with live objects on both arms, which turns `probe_ch20_interior.py`'s Room 1 NO-PATH from a **lower bound** into a **measured fact**. 6 of 7 pre-registered predictions held (`ai-research-notes/2026-08-13-ch20-room1-drive-predictions.md`). ⛔ **AND THE ROUTE HAD TO BE ARBITRATED FIRST — our own build spec was WRONG about Room 1.** It claimed an *exhaustive* search proves the `(5,11)` boulder must be pushed **north**; the decomp and our own ROM both say `(5,10)` and `(5,12)` are `collision=0 elevation=3 'Cave'`, so **either** direction is legal and the uniqueness claim is false. Upstream's **south** push ships and was confirmed live. ⇒ ‼ **The spec's Room 2 and Room 8 "exhaustive" sequences are UNAUDITED — arbitrate each against the decomp AND `puzzle_solver.py:395-454` before driving it.** ‼ **NEW: KI-77** — `get_map_objects()` is a **camera-range window**, so a pushed boulder's vacated tile is re-blocked once it scrolls off screen; benign in Room 1, **armed in Room 8's nine pushes**. ⇒ **NEXT: arbitrate Room 2, then drive `--driver ch20room2` the same way (measure → A/B → solve → can-continue).** Older text follows. 🔄 **§Ch20 IS FULLY SCOPED AND UNBLOCKED, NOT YET BUILT (2026-08-13).** ✅ Its blockers are gone: **KI-63 resolved** (the bot acquires Dive by playing), the **dive leg is driven 6/6**, and **KI-59 never gated it** (retracted — 0 of the cavern's 115 tiles reach the buggy branch). **Artefacts to build from:** the 11-leg spec `ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md`, the Area Atlas `probe_ch20_interior.py`, and `probe_ch20_currents.py`. **Shape:** Rooms 1/2/3/5/8 are **STRENGTH-BOULDER** puzzles, Rooms 6/7 are **current mazes** (‼ routable by our planner — 4/4 predictions, no solver needed), Rooms 4/9 split by terrain. ‼ **ROCK SMASH IS MANDATORY** — Strength alone is physically stuck in Room 1. ‼ **Trigger tile is `ROOM9 (17,42)`, NOT `(16,42)`.** ‼ **Grade on `VAR_ROUTE128_STATE == 2`, not the Kyogre flag** — the flag is set before a forced warp into a SECOND cutscene that lands on a **sandbar the bot must Surf off**. ‼ **Losing to Archie resets the whole dungeon**; **puzzle state resets on every map re-entry**. ⇒ **NEXT: DRIVE IT, leg by leg** — the interior was measured from OUTSIDE, so its per-room routing is a LOWER BOUND. Older text follows. 🔄 **§Ch18 + §Ch19 DONE; §Ch20/§Ch21 remain.** The path to the end of the Aqua/Magma story, decomp-gated: ✅ **§Ch18** Mossdeep Gym → `BADGE07`; ✅ **§Ch19** Mossdeep Space Center **and** Steven's **HM08 Dive** → `FLAG_RECEIVED_HM_DIVE` (both in Segment 19 — they are one chapter in `chapters.py`), which also unhides the Seafloor Cavern entrance guard; ⛔ **§Ch21** Seafloor Cavern (Kyogre) — **BLOCKED BY KI-63**: HM08 is in the bag but **no party member can learn Dive and the party is full**, so `#24-pc` is a PREREQUISITE, not a later nicety. ‼ My handoff had said the Seafloor Cavern was next — it was three beats away, and Dive was the real gate. Checking beat the assumption. ⛔ **RETRACTED 2026-08-13 — "KI-59 is armed in the Seafloor Cavern" is FALSE and was never a §Ch20/§Ch21 prerequisite.** The 115 `Impassable *` tiles are real, but **every one has `collision=1`**, and `map_path.py:128` is the `elif` of `if tile.collision != 0:` — so **none of them reach the buggy branch**. Measured over all 518 maps by `probe_impassable_dirs.py`; re-measured in a fresh process in reverse order as a cache-poisoning control (KI-73), both agree. The prescribed A/B on `SEAFLOOR_CAVERN_ROOM1` would have shown a zero delta and invited the wrong conclusion. KI-59 is still REAL — it is live on 401 other tiles, chiefly the **Regi tombs** — but it does **not** gate the cavern. See `#24-impassabledirs`. Superseded text: KI-59 is armed in the Seafloor Cavern (115 `Impassable *` tiles across Rooms 1-9) — fix it with an A/B on `SEAFLOOR_CAVERN_ROOM1` BEFORE the cavern chapter exists. | ⛔⛔ **[SUPERSEDED 2026-09-01 — LEG 3 SHIPPED. THE CELL BELOW IS 2026-08-28 HISTORY AND ITS "LEG 3 ITSELF IS NOT BUILT" IS FALSE.** It survived BOTH Tier 2 audit rounds because the leg-3 commit rewrote the FIRST cell of this row and left the THIRD — the P5 shape exactly: a fact in three places, two updated. See this row's opening cell for the live status.]** ✅✅ **§Ch21 LEGS 1 + 2a + 2b ARE BUILT AND DRIVEN; LEG 3 IS FULLY SPEC'D AND GATED (2026-08-28)** — `modules/story/sootopolis.py` + `--driver ch21dive`/`ch21escort`/`ch21cave`, all `ACCEPTANCE: PASS`; fixtures `post_sootopolis_arrival.ss1`, `post_steven_escort.ss1`, `post_wallace.ss1` PINNED. Leg 3 step 0 MEASURED (§4.11's answer is the RESTING tile **(31,17)**, not (31,16)); the Sky Pillar atlas pass and the **ROUTE131 pre-build gate** are DONE (`probe_ch21_route131_live.py`, offline, fault-tested — SET B = layout #318, 116 tiles open-in-A/WALL-in-B). ⛔ *(superseded — see the marker opening this cell)* **LEG 3 ITSELF IS NOT BUILT**; leg 5 (the return, HM07) did not exist WHEN THIS CELL WAS WRITTEN — ⛔ it SHIPPED 2026-09-02, and so did the `_play()` WIRING (Segment 21) — see this row's opening cell. *(the trailing "STILL NOT wired into `_play()`" that stood here is SUPERSEDED.)* ➡ **§Ch21 RECON IS DONE 2026-08-24 (the chapter is NOT built): the routing is closed on paper, the Mach Bike question is SETTLED (not needed), and the §Ch21 ATLAS in `12-STORYMODE-DESIGN.md` carries the measured staircase + the FOUR hang/strand hazards. ⛔ READ THE ATLAS BEFORE WRITING ANY Ch21 CODE — the ascent REQUIRES a deliberate fall through `4F (6,4)`/`(7,4)`, which no pathfinder here can propose.**
| `#24-aquahideout` | ✅ **DONE 2026-08-11 — §Ch17 BUILT and driven PASS.** `escaped=True controllable=True map=AQUA_HIDEOUT_B2F at=(24,19) whiteouts=0`, all **8 maze hops** in order. B1F is a warp-panel maze (‼ 21 of its 25 warps return to B1F) so the route was BFS-solved from the ROM warp table by `probe_aqua_hideout_graph.py` and every hop is graded on **(map AND tile)** — Ch15's "did the map change?" is useless when most hops are B1F→B1F. Wired as Segment 17; anchor `saves/post_aqua.ss1` captured on PASS. **Out of scope:** the Master Ball at `B1F (15,9)` behind two Electrode. |
| `#24-slateportsub` | ✅ **DONE 2026-08-11 — §Ch16 runs end to end, driven PASS (x3, frame-identical).** `harbor_state=2 controllable=True map=SLATEPORT_CITY_HARBOR at=(8,13)`. **Legs 2-4 had never been exercised before.** The blocker (KI-57) was resolved by reading the game rather than routing around it: ‼ the harbor door is set in a solid wall whose ONLY neighbour is Capt. Stern's tile, and `SlateportCity_EventScript_CaptStern` — **talking to him** — ends in `warp MAP_SLATEPORT_CITY_HARBOR, 11, 14`. The script carries the player in. Anchor `saves/post_harbor.ss1` now captured on every PASS. |
| **KI-56 — stranded in the Magma Hideout** | ✅ **RESOLVED 2026-08-11 — BUILT AND DRIVEN.** Cause confirmed against the WHOLE eight-map warp graph (18 of 20 nodes reachable from the stranded tile; the only two misses are the exit warp and Jagged Pass), so there is no walk-out and options 2 and 3 are dead. Fixed with the **Escape Rope the dungeon itself provides** at `3F_3R (9,19)` — no detour, no shopping. `--driver magmaexit` VERDICT **PASS**: `out=True map=JAGGED_PASS at=(16,19) controllable=True`, the exact tile predicted from `escapeWarp` beforehand. Guarded by `repro_hideout_exit.py` (fault-injected both ways). |
| **KI-57 — Capt. Stern blocks Ch16's harbor approach** | ✅ **RESOLVED 2026-08-11.** He was never an obstacle — **he is the door.** `SlateportCity_EventScript_CaptStern` ends with `removeobject` + `setvar VAR_SLATEPORT_CITY_STATE, 2` + `warp MAP_SLATEPORT_CITY_HARBOR, 11, 14`, landing on the same tile the door warp uses. Ch16 legs 1+2 now walk to `(27,13)`, face Right and ride the scene; the door path survives as the resume branch. ‼ Two instrument lessons recorded: `calculate_path` does NOT validate its source tile (a 'path' out of solid rock reports OK), and a story NPC in a doorway is usually the trigger. |
| `#24-r110mauville` / KI-48 / KI-49 | travel bugs, measured, unstarted. `could not reach` was 72 events in one batch. |
| `#24-magmahideout` + `#24-strength` | ✅ **DONE 2026-08-10 night** — `GROUDON_AWAKENED_MAGMA_HIDEOUT` set, wired as Segment 15. Listed here only so the next reader sees they closed; details in the entries below. |


---

## 📦 ARCHIVED 2026-09-11 from `03-PUNCH-LIST.md` — `#24-orphans` (R3 line budget)

⛔ **VERBATIM. Nothing deleted, nothing edited.** Archived because 03 exceeded its R3 cap after
`#24-counterhmgate` was filed. **4 of its 6 sub-items were closed; the 2 LIVE halves were HOISTED
into the stub that replaced it** — they are NOT only here. Slug preserved and findable:
`#24-orphans` (it also names `#24-ki76correctness`, `KI-65`, `KI-66`, `KI-76`).

### ‼‼ `#24-orphans` — SIX REAL RESIDUALS THAT WERE WRITTEN DOWN BUT NEVER TRACKED — **MIXED STATUS (2026-08-17, LATEST): 4 DONE `[x]` ((2) KI-65, (4) log collision, (5) compare_runs A/B axis, (6) the KI-76 shelving), 2 PARTLY DONE `[~]` ((1) — instrumentation SHIPPED, REACTION half open; (3) KI-66 — `_on_field` half FIXED+PROMOTED, OWNER-filter half open), and ⛔ NOTHING plain OPEN `[ ]`** (filed 2026-08-15; last updated 2026-08-17)
> ⛔ **(6) CLOSED THE ORPHANING, NOT THE DEFECTS** — KI-76's two defects are OPEN and live in
> `#24-ki76correctness`. ‼ This heading said *"1 OPEN `[ ]` ((6) …)"* for one commit after (6)'s own
> box became `[x]`; a Tier 2 cold-start audit counted the boxes and caught it. **Count the boxes,
> do not re-type the tally.**
> ⛔ **THE CHECKBOX AND THE HEADER MUST SAY THE SAME THING — corrected 2026-08-17 by a Tier 1
> reviewer.** This header called (1) *OPEN* while its box was `[~]` and its body opened
> *"✅ INSTRUMENTATION HALF DONE"*, and called (3) *PARTLY DONE* while its box was `[ ]`. Both are
> now `[~]`, which is what a half-done item is. ‼ It is the P2 header-vs-body pair in miniature:
> the marker is what gets skimmed, so a marker that disagrees with the prose IS the bug.

> ⛔ **THE HEADING IS A CLAIM ABOUT EVERY BULLET BENEATH IT (P2).** These six do NOT share a status —
> read each bullet's own marker. Three are closed; three are live.

> ⛔ **WHY THIS ITEM EXISTS.** An audit asked a question nobody had asked: *for every "still open /
> still owed / not built" sentence written this session, would a future session ever FIND it?* Six
> would not. ‼ **Four of the six share one shape — a live residual recorded inside a document half
> that is marked DONE or ARCHIVED** (a CLOSED KI's body, an "older framing" queue block, an
> archived handoff section, a research note). That is the P2 header-vs-body failure applied to
> TRACKING rather than to STATUS, and prose alone did not catch it — the question did.

- [~] **(1) `withdraw_from_box`'s VERDICT — ✅ INSTRUMENTATION HALF DONE 2026-08-17 (returned,
      BOUND, reported, gated, two-armed A/B). ⛔ REMAINING: the REACTION POLICY — still blocked on
      an UNMEASURED heap offset, and it needs the USER.**
      ⛔ **STATUS IN ONE LINE: production can now READ the verdict; it still does not ACT on it.**
      That split is deliberate and is the whole shape of this item.
      ✅✅ **WHAT SHIPPED (⚠ was sandbox-only; ✅ PROMOTED 2026-08-17, user-approved — drift was 0 then; ⚠ it is 1 as of 2026-08-23, see the STATE row):**
      all five exits of `withdraw_from_box` return `(landed, code, detail)` — the shape the recorded
      design asked for — its ONE caller (`modules/modes/util/higher_level_actions.py:420`) BINDS the
      result, and a new PURE function `withdraw_verdict_report` turns it into a reported line.
      ‼ **The codes distinguish ATTEMPTED-AND-FAILED from NEVER-ATTEMPTED** (`landed`, `not_in_box`,
      `party_full_no_deposit`, `did_not_land`, `error`). ⛔ Collapsing the no-attempt cases into a
      failure would manufacture one out of the commonest case — the same shape as the count-based
      lie KI-79 removed. ⛔ An UNRECOGNISED code and a MISSING verdict both read as FAILED.
      ✅ **PROVEN TWO WAYS, both MEASURED:**
      (a) **LIVE TWO-ARMED A/B**, `--driver boxcounter2` on `fortree_gym_wedge.ss1`:
          ARM B unfaulted → `verdict landed=True code=landed`, `ACCEPTANCE: PASS`, 0 fault lines;
          ARM A `POKEBOT_PCWITHDRAW_FAULT=1` → `verdict landed=False code=did_not_land` (×2), fault
          provably armed (2 `SKIPPING the PC interaction` lines), `ACCEPTANCE: FAIL` — which is the
          REGISTRY'S DOCUMENTED EXPECTATION for the faulted arm, not a regression.
          Transcripts: `evidence/2026-08-17-withdrawverdict-ARM{A,B}-*.stdout.txt`.
      (b) **THE GATE FIRES ON THE REAL BEFORE-CODE, not a synthetic one:**
          `repro_withdraw_verdict.py --build custom` (the unpromoted tree) FAILS on exactly the bare
          returns and the discarded result; the same gate passes on sandbox. Gate #26, 7 self-tests.
      ⛔ **DO NOT REBUILD ANY OF THAT.**
      🔜 **WHAT REMAINS — the REACTION half, and every constraint below still applies to it.**
      ⛔ **Do not open THAT half expecting to write mode code.** Its next action is a live probe for
      one heap offset. ‼ Header and body disagreeing on that was itself a P2 finding (2026-08-16).
      ✅ **DESIGN RULED 2026-08-16 — THE USER RULED** (`06-DECISIONS-LOG.md`): *"reattempt but after
      intelligently processing the data (text boxes it reads to determine why it failed)"*.
      ‼ **That is TWO requirements and the second is load-bearing:** reattempt, but **NOT blindly** —
      the retry must be informed by a DIAGNOSIS read from the on-screen TEXT. ⛔ A retry that repeats
      the same failing action without knowing why is the PING-PONG this project has been burned by
      twice (`#24-movelearn-recovery`; KI-65's recon). ⛔ **Bound it**, ⛔ **an UNKNOWN reason must
      NOT retry** (stop loudly instead), and ⛔ **the reason must be READ, not inferred from internal
      state** — inferring it is the same class of error as the original bug, which announced an
      identity derived from a COUNT. Taxonomy, bound and retryability follow from MEASUREMENT.
      ✅✅ **RECON DONE 2026-08-16 — READ `06-DECISIONS-LOG.md`'s DESIGN ENTRY BEFORE CODING.**
      It found a BLOCKER and FOUR PREREQUISITES, each of which a naive retry would AMPLIFY:
      ⛔ **BLOCKER — the text the ruling depends on is not where any existing reader looks.** PC
      messages go to `sStorage->messageText` (heap-allocated); every text reader in this repo reads
      `gStringVar4` or `gDisplayedStringBattle`. **The struct offset is unknown here and MUST BE
      MEASURED** (the technique is established — `pc_interaction.py:135-182` reads that same struct
      at `+0xC74`/`+0x6FA`/`+0x20A0` — but ⛔ do NOT guess the number). Until then every failure is
      `UNKNOWN`, and UNKNOWN must not retry ⇒ **the feature would ship INERT.** Measure first.
      ✅ The refusal STRINGS are already verified against our own symbol table's byte sizes
      (`gText_YourPartysFull` 0x13, `gText_BoxIsFull2` 0x11, `gText_ThatsYourLastPkmn` 0x1a …) ⇒
      compare **ROM bytes vs the live buffer** like `menu_parsers.py:357`; ⛔ never hardcode English.
      **PREREQUISITES (each is its own defect, and each is now tracked here rather than orphaned):**
      **P1 ⛔ `withdraw_from_box` (`pc_trip.py:481-482` (the gate is `:489`)) counts `alive` EXCLUDING EGGS — a live latent bug.** Its
      own sibling `deposit_one_dead_weight._occupied` (`pc_trip.py:248-263`) documents that exact
      exclusion as *"a REAL bug (found by adversarial review 2026-08-13)"* and was fixed; this
      function never got the fix. On **5 mons + 1 egg** the make-room block is SKIPPED and
      `pc_interaction.py:418` then raises. ‼ **A retry over this ping-pongs forever.**
      **P2 ⛔ `interact_with_pc` has UNBOUNDED `while … press A` loops** (`pc_interaction.py:424-433`
      plus `:466-492`, `:332-344`, `:363-376`). Per decomp, `Task_WithdrawMon` on a full party sets
      `state = 1` and **never reaches the state 4 that loop waits for**. Wrapping a retry around an
      unbounded wait MULTIPLIES a hang. *(Loop behaviour under repeated A is decomp INFERENCE, not
      observed — but "no bound + a state that may never arrive" is enough to bound it first.)*
      **P3 ⛔ the capacity guard uses the WRONG QUANTITY** — `pc_interaction.py:418` tests
      `get_party_size()` (**B**) while the game uses **A**; `pokemon_party.py:184-193` says capacity
      questions must use A. With a **HOLE** (A=6,B=5 — already OBSERVED 30x in `boxcounter2`) the
      bot proceeds and the GAME refuses. ‼ This is the case proving the ruling's second clause: the
      diagnosis must change the **ACTION** (deposit), not repeat it.
      **P4 ✅ FIXED AND PROMOTED 2026-08-16 (KI-81) — was: the blanket `except` had no `StoryAbort`
      guard, so a WHITEOUT during a PC visit was laundered.** `reraise_if_aborting(error)` is now the
      FIRST statement of all 8 handlers in `pc_trip.py` / `mossdeep_gym.py` / `higher_level_actions.py`
      in **both** forks; probe reads **53 → 45** on custom. ⚠ **This removes a hazard, it does not
      supply the retry** — a retry loop still must not re-enter a dead run, so keep the guard the
      first statement of any new handler this item adds. Precedents (TRY lines, re-derived from source
      2026-08-16 — ⛔ re-derive, never re-type; six of eight hand-copied citations in the KI-81 entry
      were wrong): `space_center.py:955` (handlers `:962`/`:971`), `mossdeep_gym.py:540` (handlers
      `:543`/`:554`).
      ‼ **P1 and P4 are worth fixing on their own merits even if the retry never ships.**
      KI-79 made the *message* honest (identity-verified, loud on failure) but production still
      cannot REACT:
      the function returns nothing and never raises, so a failed withdraw is now *reported* and
      still silently tolerated. ⛔ It was filed in the body of a KI whose header read only
      "CLOSED" — any session scanning for open issues skips it. (KI-79's header now carries the
      caveat.) The next Slugma-class derail is still invisible to callers.
- [x] **(2) ✅✅ DONE 2026-08-16 — KI-65 REPRODUCED, FIXED, A/B-PROVEN AND GATED (#25).**
      ⛔ DO NOT REOPEN. Retired to a summary 2026-09-03 (line budget) — the reproduction, the A/B
      and the gate are all in `07-CHANGELOG.md` 2026-08-16 and `31-KNOWN-ISSUES-ARCHIVE.md` KI-65.

- [~] **(3) KI-66 — PARTLY DONE: `_on_field`'s index space is FIXED AND PROMOTED; what REMAINS is
      the OWNER filter (measured INERT on our one fixture) plus `:541-545` and `_util.py:522-587`.**
      The multi-battle hazard is BROADER than the faint chooser: four more
      full-party scans are unguarded, one feeding an UNBOUNDED `while … press A`. OPEN,
      code-verified, never live-run, and untracked until now.
      ✅✅ **DRIVEN 2026-08-17 — `--driver ki66faint` IS BUILT AND WORKS. ⛔ DO NOT REBUILD IT.** It subclasses `SpaceCenter2Mode`, stages one of our own picks at 1 HP (two bytes, `data[86:88]`) so it faints in real combat, and carries a PROVEN guard against overwriting the unpinned fixture `post_space_center.ss1`. ⛔⛔ **AND THE HEADLINE IS REFUTED: the bot NEVER ATTEMPTED an ally slot.** Ally slots sat in `alive_slots` on both faints, but the chooser ASKED FOR slots 2 then 3 — both ours — because `choose_new_lead_after_faint` already filters allies. ‼ **A CANDIDATE IS NOT AN ATTEMPT**, so an A/B fixing only the owner filter shows NO DIFFERENCE here and could make it WORSE (it empties `alive_slots` and trips a FALSE 'no eligible replacement'). ‼‼ **THE REAL DEFECT IS `_on_field`'S INDEX SPACE** — field-order `gBattlerPartyIndexes` compared against a party `UpdatePartyToBattleOrder` has already permuted; it excluded Swellow while Swellow was on the BENCH (proven by its send-out at `f21009`), costing **1263 frames vs 59** on a clean faint. ⇒ **✅✅ **`_on_field`'s INDEX SPACE IS FIXED AND PROMOTED TO BOTH FORKS (2026-08-17, user-approved). ⛔ DO NOT REDO IT.** Direction MEASURED first by an observe-only probe, then applied; all gates PASSED when that landed (**25** at the time — ⛔ the CURRENT count is deliberately not repeated here; `run_gates.py` prints it and IS the authority. This sentence has now been stale at 25 AND at 26 — `run_gates.py` IS the authority) (measured). ➡ **NEXT: the OWNER filter is still unfixed and proved INERT on this fixture — it needs its OWN discriminator, not this one. `:541-545` and `_util.py:522-587` are also untouched.** Read KI-66's DRIVEN block first.
      ✅✅ *(superseded: "BUILD-READY" — the driver now EXISTS.)* Earlier: both blockers CLOSED by recon (a cold-start agent first found them
      by TRYING to begin it, then a follow-up recon closed them).
      ✅✅ **BUILD-READY AS OF 2026-08-16 — the two blockers are CLOSED by recon; read KI-66's `RECON 2026-08-16` block FIRST.** The FIXTURE existed all along and was merely undocumented: **`--driver spacecenter2`, anchor `saves/at_steven_2f.ss1`**, drives the real six-mon multi battle. The FAINT needs no new capability and no `gBattleMons` writer: **pre-stage one selected mon at 1 HP before the battle** (1, not 0 — a 0-HP mon is never SELECTED) and it faints in real combat. ⛔⛔ **REFUTED 2026-08-17 BY THE LIVE RUN — this block used to claim the ally case "needs all three of ours down = the LOSS condition". BOTH HALVES ARE FALSE:** only TWO of ours were down (Swellow was alive on the BENCH, sent out at `f21009`), and in a multi battle the side is `gPlayerParty[0..5]` — ours AND Steven's — so that is not the loss condition at all. The run WON, `whiteouts=0`. See KI-66's DRIVEN block. ✅ **Grade instead on the ATTEMPTED SLOT INDICES + refusal count on a SINGLE faint**, which `:630-636` reaches while two of ours are still alive. ⚠ ARM B's behaviour when only ally mons remain is a USER POLICY call.
      *(Superseded: "RECON IS STARTABLE; THE BUILD IS NOT".)* Same correction item (1) already carries. What it confirmed by
      reading: all four sites are live (`battle_handler.py:541-545`, `:588-598`, `:630-636`,
      `_util.py:522-587`), and the choke point `ally_party_indices()` EXISTS
      (`battle_strategies/default.py:12`), called from `default.py:189` / `level_up.py:53` /
      `story_mode.py:171` — and from **none** of the four. What BLOCKS the build:
      **(i) no anchor save is named anywhere that reaches a partner double battle, and
      (ii) no fault hook forces the PLAYER FAINT that is the sole trigger for all four sites.**
      ‼ **Without both, the obvious before/after A/B IS VACUOUS** — the entry's own words are
      *"none has ever run live (every §Ch19 drive had zero faints)"*, so both arms are
      byte-identical and read as *"the fix is unnecessary"*. ⇒ **first deliverable is a FIXTURE +
      a faint hook, not a patch.** *(Undocumented candidates a future session may evaluate — found
      by listing directories, NOT cited by any doc, so verify before trusting:
      `saves/at_steven_2f.ss1`, `saves/post_space_center.ss1`, drivers `spacecenter1/2`,
      `faintrepro`.)*
      ⛔ **AND ONE POLICY QUESTION FOR THE USER, not for an agent:** when only ALLY mons are
      alive, ARM B's correct behaviour is *"ride out the loss"* — but that contradicts
      `ally_party_indices`'s own documented fail-closed rationale (`default.py:31-34`, which
      fails closed to an empty set precisely to avoid pushing the caller into the full-party
      fallback). Deliberately losing a battle is a behaviour choice.
      ‼ **The `IndexError`-on-turn-1 sub-claim is REFUTED (2026-08-12), not pending.** Do not
      re-check it; `05-KNOWN-ISSUES.md` cites the driven run (`ch19d.log` f23255, six-entry party,
      multi battle WON).
- [x] **(4) ✅ DONE 2026-08-16 — `story_harness.py` no longer overwrites its log.** — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [x] (5) ✅ DONE 2026-08-17 — and the item's own premise was REFUTED — 📦 **ARCHIVED 2026-08-26 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [x] **(6) ✅ DONE 2026-08-17 — SHELVED (it now has its own item, `#24-ki76correctness`) AND
      MEASURED. ⛔ The DEFECTS remain open; what closed is the ORPHANING, which is what this bullet
      was about.** *(Was: "KI-76's CORRECTNESS half is OPEN and MIS-SHELVED. Its only queue mention
      sits inside a block the handoff brackets as 'older framing … ⛔ also NOT next'.")*
      ‼ **Verified before acting:** KI-76 had **no punch-list entry of any kind** — its sole
      appearance in this file was this bullet saying it was mis-shelved, and its sole handoff
      appearance was buried at `04-HANDOFF.md:610` inside a §Ch20-era block. It is now a first-class
      item with the measurement attached; the numbers live THERE, not here, so they cannot drift
      into a second copy.

‼ **PREVENTION, and it is a question rather than a rule:** at wrap-up, for every *"still open /
owed / not built / residual"* sentence written that session, ask **"where would a future session
FIND this?"** If the only answer is an append-only log, a CLOSED KI's body, or a research note, it
is ORPHANED — put it here. ⇒ `08-MISTAKES.md`, 2026-08-15.


---

## 📦 ARCHIVED 2026-09-11 (second pass) from `03-PUNCH-LIST.md` — R3 line budget

⛔ **VERBATIM. Nothing deleted, nothing edited.** Both were fully CLOSED with zero open boxes,
so nothing needed hoisting. Slugs preserved and findable: `#24-ch21anchor`, `#26-fleefreeze`.

### ✅ `#24-ch21anchor` — DONE 2026-08-24 (RETIRED to a summary; full detail in `07-CHANGELOG.md`)

⛔ **`saves/post_ch20.ss1` EXISTS — DO NOT RE-CAPTURE IT.** Captured by `--driver ch20chapter`
with `CH20_CAPTURE=`, which writes ONLY on `ACCEPTANCE: PASS`, so the file's existence IS the
acceptance record. Probe-verified `OVERWORLD ROUTE128 (38,24)`, badges 1-7, `ROUTE128_STATE=2`,
`SOOTOPOLIS_CITY_STATE=1` — §Ch21's entry condition, measured live.
⚠ It carries **1 FAINTED party member at 80% HP** — faithful, but a §Ch21 leg started from it
can whiteout; heal first and do NOT read an early whiteout as a Ch21 bug.
‼ The lesson that outlived the item: **verify an anchor with `probe_anchor_inventory.py`, never
from the driver's log** — the probe caught the fainted member the driver's log did not report.

### ✅ `#26-fleefreeze` — FIXED 2026-08-26, GATED as #32 — and the LIVE arm LANDED: confirmed in batch `20260826-130441`

`_escape` delegates to the inherited KI-52 `_handle_flee` on the escape-impossible branch instead
of blindly returning `run_away()`. Gate #32 `repro_flee_trap_delegate.py` proves it 3 ways (⚠ its
ARM A sentinel was strengthened 2026-08-27 — it had been value-equal to `run_away()`). LIVE ARM
LANDED in BOTH post-fix batches: zero CantEscape freezes corpus-wide (baseline 3 of 8 lanes).
**ARC CLOSED.** 📦 Diagnosis + evidence: `07-CHANGELOG.md` 2026-08-26/27 + git history.



---

## 📦 ARCHIVED 2026-09-11 (third pass) from `03-PUNCH-LIST.md` — R3 line budget

⛔ **VERBATIM. Nothing deleted, nothing edited.** Each was fully CLOSED with zero open boxes,
so nothing needed hoisting. Slugs preserved: `#24-hm07teach`, `#26-mossdeeppuzzlespeed`.

### ✅ USER RULINGS 2026-07-29 — all six open questions answered
Full text + rationale: `06-DECISIONS-LOG.md` 2026-07-29. Summary:
`#24-counters` phase 2 → **A+C** (price both, then catch-and-train a Fighting type)
**plus new scope: area/species/level mapping + party>4 + PC rotation** (see `#24-trainmap+`
below); `#24-leadpolicy` → **A+C**; `#24-route110cap` → **A** (prep, NO cap);
KI-24b → **A** (fix the mock, re-baseline, show the diff); `#doc-policy-05` → **A**
(keep-and-mark until promotion); repo size → **leave it**.

### ✅ ALL FOUR HARNESS FIXES VALIDATED LIVE — 2026-07-29 (five bundles)
`#24-x4-staleslate`, `#24-x4-honestoutcome`, `#24-x4-runindex`, `#24-x4-framebudget` are
confirmed working in production. `couldn't beat the Rustboro rival` went **31 → 0**; max
single-run frames now 1.9M–3.1M (all under the 3.5M cap, the 27M/30M hangs are gone);
`run_index` stride 1 in all four lanes. **16 runs reached the Feather Badge in one batch**
(P1×5, P2×5, P4×4, P3×2) — previously a once-per-batch event. Detail: `07-CHANGELOG.md`
2026-07-29.

### ✅ `#24-hm07teach` — **CLOSED 2026-09-08, DRIVEN AT SCALE.** ⛔ DO NOT REDO.
- [x] Production never taught Waterfall, so §Ch23's preflight killed every 8-badge run in project
  history (six across 37 batches, all six there). `ensure_waterfall_learner()` + Segment 22b fixed
  it. **MEASURED: the §Ch23 Waterfall preflight went 11 of 53 → 0 of 49** (batch `20260907-203713`
  vs `20260907-113851`, equal wall time). Runs now die 16x deeper, in the TRAINING leg — see
  `#24-ch23training`. Full detail: `07-CHANGELOG.md` 2026-09-07 and 2026-09-08.

### ✅ `#26-mossdeeppuzzlespeed` — FIXED 2026-08-26, A/B-PROVEN ~2.9x: ~62k → ~21k frames (~17.2 → ~5.8 min)

Bounded PRE-TURN (`TURN_TIMEOUT_FRAMES=32`) removed the 58% sink; all five safety checks kept and
silent on both arms. Evidence `evidence/2026-08-26-mossdeep-speed-AB.txt`; narrative + original
filing in `07-CHANGELOG.md` 2026-08-26. ⛔ Fixes B/C deliberately NOT taken.



---

## 📦 ARCHIVED 2026-09-11 (fourth pass) from `03-PUNCH-LIST.md` — R3 budget

⛔ **VERBATIM.** Fully CLOSED, zero open boxes, nothing hoisted. Slug: `#26-battleitemwedge`.

### ✅ `#26-battleitemwedge` — HANG closed 2026-08-26 AND LIVE-VALIDATED 2026-08-27 (batch `20260826-185918`: its KI-47 family 2 → 0 over 572 item flows)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ DO NOT REDO. Full detail is in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.


---

## 📦 ARCHIVED 2026-09-11 (fifth pass) from `03-PUNCH-LIST.md` — R3 budget

⛔ **VERBATIM.** CLOSED the same day, zero open boxes. Full narrative also in
`07-CHANGELOG.md` 2026-09-11. Slug: `#26-gatestartupcontention`.

### ✅ `#26-gatestartupcontention` — **CLOSED 2026-09-11: it was never contention and never a hang — the gate was PACED TO 60fps.** ⛔ DO NOT REOPEN. (filed 2026-08-26, closed 2026-09-11)
⭐ **ROOT CAUSE, in one line:** the gate set `context.audio`/`context.video` but not
`context.emulation_speed = 0`, so the emulator stayed THROTTLED and paced itself by BLOCKING on
an audio write every frame. `audio = False` only silences the samples (`libmgba.py:593`); the
write is guarded by `if self._throttled:` alone (`:618-621`). The suite's 900s bound is ~54,000
frames at 1×, and this gate walks a long gym route. ⭐ **A/B: 900s kill (×3) → 107s, EXIT=0,
5/5 pass** — its own documented 114s runtime.
- [x] Fixed in `repro_gym_whiteout_guard.py` **and in the five other registered gates that had
      the same omission** (`probe_chapter_order`, `probe_dive_routing`, `probe_regi_capabilities`,
      `probe_slot_free_plan`, `repro_impassable_dirs`) — they passed only because their routes
      are short.
- [x] **GATED as #54 `probe_gate_unthrottled.py`** (rule 6: a rule already broken belongs in a
      gate). Proven against the REAL pre-fix file via `git show HEAD:…`, not only its own
      `POKEBOT_UNTHROTTLED_FAULT=1` arm.
⚠ **The three earlier diagnoses were each partly right and none was the cause.** Not gate
parallelism (`run_gates.py` is sequential — correctly refuted 2026-08-26). Not machine load
(reproduced on a quiet machine — correctly refuted). The `PaErrorCode -9999 / no driver`
errors are REAL but a SYMPTOM: this machine's output device is an HDMI TV, and failing writes
added a `_reset_audio()` per frame ON TOP of the pacing. ⇒ **the empty log was the tell — a
process producing nothing for 900s can be stuck OR merely slow, and nobody had measured which.**
⛔⛔ **"PASSES SOLO" IS REFUTED — DO NOT PLAN AROUND IT.** Measured 2026-09-11: three suite runs in one session each killed `repro_gym_whiteout_guard.py` at the 900s bound, **and a SOLO re-run produced nothing for 600s** before I stopped it. That agrees with `04-HANDOFF.md`'s record of a ~36-minute standalone hang and disagrees with this item's own former title. ‼ *(The title read "passes solo" from 2026-08-26 until 2026-09-11 — P2 in miniature: the half that gets skimmed said the opposite of the body's newest evidence.)*
⭐ **AND THE MECHANISM IS PROBABLY NOT A HANG AT ALL — it is a per-frame exception storm.** `libmgba.py:617-623`: when throttled, every frame calls `self._audio_stream.write(...)`; with no audio driver that raises `PortAudioError`, which is caught and answered with `self._reset_audio()` — **and then the next frame does it again**. The file's own comment describes the intended escape (*"in case audio could not be initialised, we fall back to a sleep-based throttling mechanism"*), but that branch is only reached when `_audio_stream` is falsy, and the error path never permanently clears it. ⇒ the emulator does not stop, it CRAWLS. That fits an empty log, a 36-minute solo run, and the repeated `PaErrorCode -9999 ... no driver installed` lines seen in all three of this session's runs.
- [x] ⛔ **OBSOLETE, NOT DONE — the premise was disproved.** Candidate fix was: make the fallback STICK** — after N consecutive `PortAudioError`s, set `_audio_stream = None` permanently so throttling uses the documented sleep path. ⚠ `libmgba.py` is UPSTREAM code, so this is a DIVERGENCE and needs a `DIVERGENCE-LOG.md` entry; prefer running gates UNTHROTTLED if that is sufficient, since a headless gate has no reason to pace itself to 60fps.
- [x] ⛔ Still true as GUIDANCE, no longer an action: do NOT "fix" it by raising the 900s bound. A bound that is raised to accommodate a defect stops being a bound.

`repro_gym_whiteout_guard.py` hangs IN-SUITE and passes solo. ⛔ **THE FIRST FILING OF THIS ITEM GOT
THREE DETAILS WRONG, AND A TIER 1 REVIEW CORRECTED ALL THREE WITH A LIVE OBSERVATION** (it caught the
gate mid-hang in a running suite): (1) the freeze is just AFTER phase [1]'s header prints, not
before it; (2) `run_gates.py` is strictly SEQUENTIAL — "~30 parallel gates" was wrong, so
gate-parallelism is not the mechanism; (3) it reproduces on a QUIET machine, so batch load is
refuted too. What stands: in-suite hang (≥3 occurrences: two 900s timeouts + one live-observed),
solo PASS the same hour, audio-host errors (`PaErrorCode -9999, no driver installed`) present at the
freeze point. ⛔ **A 900→2400 bound raise was tried and REVERTED — more time cannot fix a hang.**
➡➡ **DIAGNOSED 2026-08-26 — THE HANG SITE IS CAPTURED; THE PLANNED BISECT IS MOOT.** Stack dump
(`evidence/2026-08-26-gatecontention-stackdump.txt`): **`sounddevice.write` ← `libmgba.py:621
run_single_frame`** — the FPS limiter is a blocking audio write with NO BOUND; a wedged PortAudio
host blocks it forever. Reproduced **SOLO, twice, deterministically, 0 bytes out** (buffered
stdout — "after the header" and "empty log" are the SAME hang); host-state-dependent, batch lanes
immune (`audio=False speed=0` enforced). ⚠ The "sibling passes solo" control was WEAK
(`probe_chapter_order` never drives frames). **FIX CANDIDATES (one drive each): (a) run the gate
stream-free/unthrottled at EMULATOR level like the lanes; (b) bound the write in `libmgba.py`
(production internals — careful).** Narrative: `07-CHANGELOG.md` 2026-08-26.
‼ **RECURRED 2026-09-10 — 4th in-suite, 3rd solo, both at the documented freeze point.** In-suite
`exit=124` at exactly `900.0s` ⇒ the suite ran **50 of 51**. Solo, same hour and tree: printed the
`[1]+[2] FAULT INJECTION` header, then nothing. ⛔ **A TIMEOUT, never an assertion failure** — no
check went red; the process never reached one.
⭐ **EXONERATED STRUCTURALLY, not by "it passes solo" — which is FALSE, it hangs solo too.** The
concurrent `#24-dexhunt` fence lives in `_should_catch`, reachable ONLY via `on_battle_started`, a
LISTENER hook; this gate drives a mode generator **BY HAND with no listeners** (its own docstring
says so) and greps **0 code references** to that path. ⇒ structurally unreachable.
⇒ **LESSON: beside your own change, "it is the known issue" is an EXPLANATION, not an ALIBI** —
only a reachability argument or an arm with the change removed tells them apart.


---

## 📦 ARCHIVED 2026-09-11 (sixth pass) from `03-PUNCH-LIST.md` — R3 budget

⛔ **VERBATIM.** Filed AND fixed the same day, zero open boxes. Its shared-helper residual is
tracked separately as `#26-healnavbare` and is NOT in here. Slug: `#26-slateportpcderail`.

### ✅ `#26-slateportpcderail` — **SLATEPORT** Poké Center (19,19): a scripted-event derail to MANUAL, **22-26x PER BATCH** — **FIXED 2026-09-11** (filed and fixed same day)
⛔⛔ **THE SLUG AND TITLE SAID "MAUVILLE" FOR ONE COMMIT AND THAT WAS WRONG.** The derail line
reads `… (19, 19) @ (0, 1) … | stage: 9: Mauville & the Bike`, and I read the STAGE label as the
location. **`(0, 1)` is SLATEPORT_CITY** (resolved from `MapRSE`, not recalled) and `(19,19)` is
`PokemonCenter.SlateportCity` (`map_data.py:1529`). The stage text is the CHAPTER the run is in,
not where it broke. ⇒ **a map id is a fact to resolve, never to infer from a nearby label.**

**THE LINE, identical in every occurrence:**
> `Story localization — derail #1: We unexpectedly triggered a scripted event while trying to reach`
> `(19, 19) @ (0, 1).` / `Switching to manual mode. | stage: 9: Mauville & the Bike | map (0, 1)`

**MEASURED FREQUENCY — four batches, all on disk:**
| batch | occurrences |
|---|---|
| `20260909-160339` | 22 |
| `20260910-203458` | 26 |
| `20260910-234959` | 22 |
| `20260911-145915` (4 lanes, 25 min) | 3 |
⇒ this is not a rare edge; it is a **routine** outcome of the Mauville leg.

⛔ **IT IS PRE-EXISTING AND NOT CAUSED BY THE 2026-09-11 ROUTING FIXES.** That was checked before
claiming it: the same string appears 22-26 times in every batch that predates those fixes. ‼ Filed
BECAUSE it will be visible in the user's overnight batch, and a reader who sees it there must not
attribute it to the detour work.

**WHAT IT IS.** `walking.py:499-505` raises when a navigation walks onto a live scripted event and
the caller did not say `expecting_script=True`:
```
if get_global_script_context().is_active:
    if expecting_script: return
    else: raise BotModeError("We unexpectedly triggered a scripted event ... Switching to manual mode.")
```
⇒ same CLASS as the Littleroot running-shoes detour, but the opposite symptom: Littleroot PAID
+10000 to route around its trigger (cosmetic), while this one walks into a Mauville trigger and
derails (costly — `#26-manualderails` measured the user's manual flip-back usually just working).

- [x] **ROOT CAUSE + FIX.** `heal_in_pokemon_center` ends in a bare `navigate_to_anywhere`
      (`higher_level_actions.py:377`) with no `avoid_scripted_events=False` and no retry. Leg 4 of
      `sail_to_slateport` calls it while Slateport's coord events are still armed — **three lines
      after Leg 3 took exactly that precaution for a tile two squares away at (19,21)**. Leg 4 now
      carries the same bounded ride-out retry.
- [x] ⛔ Did NOT use `expecting_script=True` — it suppresses the error without riding the scene
      out, converting a visible derail into a silent wedge.
↪ The shared-helper half of this is tracked separately as `#26-healnavbare` — it is a different
defect (one helper, every heal site) from the one fixed here (one call site, one leg).

---


## 2026-09-12 — retired from `04-HANDOFF.md`: the 2026-09-07 batch block (`x4-runs/20260907-203713`)

Superseded by three later batches (2026-09-11 overnight, 2026-09-12 confirmatory, 2026-09-12 safety). Moved to keep `04-HANDOFF.md` inside its 900-line budget.
⚠ **ONE LINE FROM THIS BLOCK WAS DELIBERATELY LEFT BEHIND** — *“THE RULE, FOR THE NEXT BATCH: while one RUNS, do not edit `sandbox-pokebot/` and do not promote”* — because it is a LIVE rule, not history, and it was relied on again on 2026-09-12.

>    ✅✅ **THE BATCH IS FINISHED — `x4-runs/20260907-203713`, 49 ended runs, VERDICT OK, 480.1 wall minutes, `--build sandbox`, `code=8a8ae2d9`. THE SANDBOX IS UNLOCKED; edit and promote freely.**
>    ⭐⭐ **THE WALL IS BROKEN. §Ch23's Waterfall PREFLIGHT went 11 of 53 → 0 of 49.** Across 37 stored batches the 8th badge was reached six times and ALL SIX died on that preflight; nothing had ever passed it. Runs now die **16x deeper**, in the TRAINING leg. ⇒ `#24-hm07teach` and `#24-hm07funnel` are **CLOSED, driven at scale** — ⛔ DO NOT REDO EITHER, and their owed acceptance drives are ANSWERED; do not run them.
>    ⭐ **Surf + Dive party-full: 7 of 53 → 0 of 49.** ⭐ **Whiteout quota: 14 (26.4%) → 4 (8.2%)**, firing with its new location-keyed message — ‼ it did NOT go to zero, and that is CORRECT: four runs were genuinely stuck and the guard caught them.
>    ⛔ **STILL 0 FINISHED OF 49.** The new top blocker is **`#24-ch23training`** (16 of 49, 32.7%) — §Ch23's training leg REFUSES because one mon's grind alone exceeds the per-call frame ceiling (⚠ "alone" means *that one mon by itself*, NOT that it is alone in the party — all 16 failures have 2+ members). Marill in 9 of 16. Also NEW: `#24-cutscenestall` (4) and a per-run frame-budget class (2), neither present in the BEFORE batch.
>    ⚠ **HONEST LIMIT:** BEFORE is `--build custom`, AFTER `--build sandbox`, so the aggregate is not a single-variable A/B. The load-bearing per-class deltas (preflight 11→0, Surf/Dive 7→0) are each tied to a specific change with its own mechanism.
>    ⭐ **THIS IS THE FIRST BATCH WITH VERIFIABLE BUILD PROVENANCE.** `code=8a8ae2d9` is recorded AND the sandbox tree was clean at launch (checked), so the commit named is genuinely what ran. All three of today's fixes are ancestors of it (verified with `git merge-base --is-ancestor`).
>    ⭐ **WHAT IT IS MEASURING:** whether `#24-whiteoutloop` (was 14 of 53 = 26%) and §Ch23 (11 of 53 = 21%) actually shrink. ⚠ **EXPECT THE FAILURE TO MOVE, NOT VANISH** — see the next line. The previous batch for comparison is `x4-runs/20260907-113851` (53 ended runs, 0 finished).


## §Ch21 recon instruments + the §Ch21 start-fixture note — ARCHIVED 2026-09-17 (R3 budget)
⛔ Moved VERBATIM out of `04-HANDOFF.md`, not deleted. §Ch21 and §Ch22 are FINISHED CHAPTERS, so their recon recipes are reference rather than the critical path, and the handoff crossed its 900-line budget when §Ch24 room 3 shipped. ⭐ The lesson in the last line is why this is archived rather than dropped.

### §Ch21 recon instruments (both NEW 2026-08-24, both fault-tested)
```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 probe_ch21_topology.py            # warps/sizes/dive+surface tiles from ROM headers
POKEBOT_CH21PROBE_FAULT=warpcoord   ... same ...        # its self-test: MUST print 2 FAIL and exit 1

PYTHONUTF8=1 py -3.12 probe_skypillar_clean_layout.py   # the CLEAN-layout staircase + the deliberate fall
POKEBOT_SKYPILLAR_FAULT=nofall      ... same ...        # its self-test: MUST print 1 FAIL and exit 1
```
⛔ `probe_skypillar_clean_layout.py` is NOT in `run_gates.py` — it fetches decomp layout binaries over
the network and a standing gate must not need the net. ‼ It exists because a Tier 1 review REFUSED the
atlas's central finding while it rested on an uncommitted script: right numbers, un-re-runnable = NOT PROVEN.

### Capture the §Ch21 start fixture — ⛔ ALREADY DONE, do NOT redo
`saves/post_ch20.ss1` exists (`--driver ch20chapter` + `CH20_CAPTURE=`, written only on
`ACCEPTANCE: PASS`, so the file's existence IS the acceptance record). Verify a fixture with
`probe_anchor_inventory.py --filter <name>` — the FILE, never the driver's log (playbook §2b).


## The DISARMED `KI-96` repro note — ARCHIVED 2026-09-17 (R3 budget)
⛔ Already disarmed to a comment on 2026-09-17; moved out of the current-state file here. `KI-96` was SOLVED and DRIVEN 2026-09-07.


#  ⛔ DISARMED 2026-09-17 — WAS RUNNABLE, NOW A COMMENT. The note below already said “NOT A REPRO ANY MORE”, but the COMMAND stayed executable for nine days, so a cold reader pasting this block still ran it — on `post_grind_L60.ss1`, which is now a DEAD BRANCH too. Kept for the record: PYTHONUTF8=1 py -3.12 story_harness.py post_grind_L60.ss1 --driver ch23chapter --frames 400000
#   ⛔⛔ NOT A REPRO ANY MORE — `KI-96` WAS SOLVED AND DRIVEN 2026-09-07 (evening) and this file's
#   own banner says so, yet this block kept COMMANDING its repro for nine days. *(It read: “THE
#   `KI-96` REPRO. Wedges by ~f27k (~6 min) in the in-battle PARTY MENU … LEVELLING ALONE DOES NOT
#   UNBLOCK §Ch24.”)* The COMMAND stays: it is a valid §Ch23 chapter drive from the L60 party.


## PARTY ACCOUNTING STAGE 0 — the hand recipes, ARCHIVED 2026-09-17 (late, R3 budget)

⛔ Moved VERBATIM out of `04-HANDOFF.md`, not deleted. `repro_party_accounting.py` is **gate #22**
and `run_gates.py` runs it on every suite, so the hand recipe is reference rather than a daily
command — the same criterion this file used when it archived gate #13's recipe. The handoff hit
its 900-line R3 cap while §Ch24 room 3 shipped, and room 4 needs the headroom.
⭐ `collect_party_accounting.py` (the P3b aggregator) is the half worth remembering: it MEASURES
ONLY, and it fails LOUD when no log matches — *“I could not look” is not “clean”*.

# --- PARTY ACCOUNTING STAGE 0 — the readers, the divergence log, and its gate ---
PYTHONUTF8=1 py -3.12 repro_party_accounting.py     # PARTY ACCOUNTING STAGE 0 (gate #22)
#   Expect: `ALL 33 CHECKS PASS`, exit 0. No emulator, ~1s. ‼ It PRINTS its own check count —
#     believe that line, not this one. Takes `--build custom` and
#     ASSERTS which fork it imported. It drives the REAL get_party() over FABRICATED gPlayerParty
#     memory, so it tests the shipped reader, not a copy. ‼ The CONTROLS are the point: a healthy
#     party must record NOTHING, and get_party() must be byte-identical with the observer stubbed.
#   ‼ THE MEASUREMENT IT EXISTS FOR IS NOT IN THE GATE — it is the `[PARTY-ACCT] STAGE 0 SUMMARY`
#     that every `story_harness.py` drive now prints at the end. Collect those from LONG runs:
PYTHONUTF8=1 py -3.12 collect_party_accounting.py   # (P3b) aggregate every drive's summary
#   Exits 1 until the criterion is met (>=5 drives / >=3 drivers / >=250k recomputes, OR the first
#   divergence), so P3b cannot be eyeballed. ✅ AS OF 2026-08-15 IT EXITS 0: 7 drives, 7 drivers,
#   ⛔ SUPERSEDED 2026-08-15: it now reports ✅ CRITERION (b) MET — A DIVERGENCE WAS OBSERVED.
#   967,970 recomputes · 39 drives · 12 drivers, with HOLE x30 in `boxcounter2` in BOTH forks
#   (slot 5 of gPlayerPartyCount=6, counted by the game but near-all zero). The old line said
#   "7 drives, 280,707, NO DIVERGENCE … all DUNGEON content with a STATIC party" — true of that
#   population, false now that a party-MUTATING driver exists. ‼ RUN IT; do not quote it.
#   ‼ It MEASURES ONLY — it cannot drive the emulator, and it says so rather than implying a log
#     read is a reading. It also fails LOUD when no log matches ("I could not look" != "clean").


## ⛔ "WIRING THE PICKER IS KILLED" — the full item, ARCHIVED 2026-09-17 (late, R3 budget)

⛔ Moved **VERBATIM** out of `03-PUNCH-LIST.md`, nothing edited and nothing deleted. The item is a
CLOSED `[x]` decision (a design that was KILLED, kept for its rationale), and the punch list had
reached 4395/4400 against `lint_docs.py` R3 while §Ch24 leg B was being measured.
‼ **THE BOUNDARY WAS CHECKED BEFORE CUTTING**, per the rule added the same day: the item runs to
the line before a genuine SIBLING `- [x]`, its body contains no nested `- [` steps and no
`**THE WORK:**`-style header. (§Ch23's entry was tried first and rejected for exactly that reason.)

- [x] ⛔⛔ **WIRING THE PICKER IS KILLED 2026-09-09 — AND THE PREMISE OF THE 2026-07-21 DIRECTIVE IS

  NOT GENERALLY TRUE.** Six-agent adversarial pass. ⇒ **do NOT wire `best_training_grass` into
  training as a maintenance pass.** Three independent reasons:
  1. ✅⛔ **MEASURED 2026-09-09 — THE PROPORTION HOLDS, THE INFERENCE IS REFUTED.** *(Was
     `[AGENT, UNVERIFIED]`: "of 1,496 mons that ever reached 15+ behind, 88.8% were ALREADY more
     than 6 behind the FIRST time they were observed (median 11)", concluding **"THE MONS ARE BORN
     DEAD WEIGHT, so there is no early small-gap window to maintain."*)*
     **[MEASURED BY ME — `tools/story-dev/probe_laggard_origin.py`, batch `20260909-160339`,
     24 logs / 17,302 heartbeats / 78,113 id elements / 0 dropped]**
     ```
       population (ever >= 15 behind) : 63          first-seen gap > 6 : 53/63 = 84.1%  [claimed 88.8%]
       median first-seen gap          : 10          [claimed 11]
     ```
     ⇒ ✅ **THE PROPORTION IS ESSENTIALLY RIGHT** — most laggards DO arrive already past the
     threshold. A 5-angle adversarial pass put 88.8% inside the measurement's own 95% CI
     (74.3%-92.0%), and a **sampling-independent** arrival-anchored angle agreed (median 8 behind,
     ~80% > 6 at the instant of entry), which also proves heartbeat lag hides nothing here
     (median delta 0; identical for ~94% of paired mons).
     ⛔⛔ **BUT THE CONCLUSION DRAWN FROM IT IS FALSE, AND THAT IS THE HALF THAT ROUTED THE
     DECISION:**
     ```
       A arrived already INSIDE the <=6 window : 10        C never inside it at all : 38
       B arrived outside, LATER got inside it  : 15        => HAD a window (A+B) : 25/63 = 39.7%
           of which the LAGGARD LEVELLED UP    : 11  <= actionable
           of which the PARTY MAX FELL         :  4  (a deposit/swap — the bot did not earn it)
       median time inside the window : 163 heartbeats = 163 MINUTES (~2.7 HOURS emulated)
     ```
     ⇒ **"no early small-gap window to maintain" is refuted for 40% of the population**, and the
     window is not a sliver: the median mon spends **~2.7 HOURS of emulated time inside it**.
     ⛔ **BUT USE 33.3%, NOT 39.7%, WHEN PRICING A FIX.** A gap closes from either end, and only one
     end is actionable: 4 of the 15 recoveries happened because the party MAX FELL (the leader was
     deposited or swapped out — level never drops on a faint), not because the laggard improved.
     ⇒ **TRAINING-REACHABLE = A + B/level-rose = 21/63 = 33.3%.** *(Found by an adversarial review
     that was asked to attack exactly this claim; the tool now prints both numbers so the
     distinction cannot be lost again.)*
     ⇒ the problem is not only that they arrive behind — **a long window existed and was not used**,
     which is a different defect with a different fix, reachable at TRAINING time.
     ⛔⛔ **CORRECTED — THE 33.3% USED A WINDOW ONE LEVEL WIDER THAN THE CODE'S (found 2026-09-09,
     hours after publishing it).** My tool called a mon "inside the window" at `gap <= 6`, but the
     predicate is `level >= target - 6` with `target = team_max + 1` in boss-fodder mode ⇒ the real
     condition is **`gap <= 5`**. Re-measured on the same population:
     ```
       threshold                A inside   B rose   B topfell   TRAINING-REACHABLE
       gap <= 6  (my tool)            10       11           4      21/63 = 33.3%   <- overstated
       gap <= 5  (the CODE)            1       12           7      13/63 = 20.6%   <- USE THIS
     ```
     ‼ `A inside` collapses **10 -> 1**: nine of the ten mons that "arrived inside the window"
     arrived at **exactly gap 6**, the single value the predicate excludes.
     ⚠ **AND 20.6% IS ITSELF AN UPPER BOUND.** Outside boss-fodder mode `target` is the BOSS BAND,
     not `team_max + 1`, so "gap from team max" is not the code's coordinate there at all — this
     window only maps onto the predicate in the fodder branch.
     ⭐⭐ **THE FINDING THIS EXPOSED, AND IT IS BIGGER THAN THE CORRECTION.** First-seen gap over all
     184 mons in the batch:
     ```
       gap 0: 48   gaps 1-5: 12 TOTAL   gap 6: 23   gap 7: 36   gap 8: 26   gaps 9-15: 16   16+: 23
     ```
     **46% of arrivals land in gaps 6-8 while gaps 1-5 are nearly empty, and the window is gap <= 5.**
     ⇒ mons arrive SYSTEMATICALLY JUST OUTSIDE the training window.
     ⛔⛔ **AND THAT LEAD IS DEAD — KILLED 2026-09-09. DO NOT RE-PROPOSE WIDENING
     `TRAIN_CATCHUP_GAP`.** Four reasons, in one line each; **the full record with all raw output is
     in `07-CHANGELOG.md`, "I killed my own most promising lead, with evidence"**:
     1. **The histogram was contaminated** — 95 of 184 "arrivals" are not catches (starters, the
        Wally tutorial, **27 of Steven's allies merged by the §Ch19 multi-battle**, gifts, PC
        withdrawals, Shedinja spawns). All 48 gap-0 arrivals were non-catches. Genuine catches
        (n=89): `0-5: 2 | 6-8: 69 | 9-15: 2 | 16+: 16`.
     2. **The mechanism is refuted** — [MEASURED BY ME] 79/89 = **89%** of caught mons gain exp
        (median **+20 levels**); 59/89 = **66%** reach gap <= 5. They are not stuck outside it.
     3. **The fix does nothing** — `tools/story-dev/probe_catchup_threshold_sweep.py`: G=6 → G=∞
        admits **+2 mons** overall and **+1** of the 69 gap-6-8 catches; 65 of those 69 are already
        admitted at the shipped value. Flat from 5 to ∞ ⇒ the threshold binds nothing.
     4. **The gap is geography** — ⚠ [AGENT-MEASURED, NOT RE-DERIVED BY ME] all 90 catches fall
        inside the wild-band prediction (90/90, residual +0.20 ± 0.54); the bot already catches at
        its floor (only 40 of 8,401 catch-capable minutes offered a lower-gap catch).
     ⭐ **AND THE SAME REASONING WAS APPLIED TO A NEIGHBOURING CONSTANT ON 2026-07-24** —
     `06-DECISIONS-LOG.md:267-269`, rejecting an alternative:
     > *"3. Raise/lower the level window. Any level-denominated threshold is wrong for the same
     > reason the current one is: it cannot see the XP rate. Tuning it just moves which map it is
     > wrong on."*
     ⚠ **THAT ENTRY IS ABOUT `mon.level + 3`** (the evo-lookahead sufficiency gate, `story_mode.py:1563`,
     commit `e8d133be`), **NOT about `TRAIN_CATCHUP_GAP`** (`:1136`, commit `395c392d`, three days
     earlier). ⇒ it is an **ANALOGY whose reasoning transfers**, *not* a prior ruling on this
     constant. *(Recorded this way after a Tier 1 reviewer caught the overreach — the kill above
     rests on the measurements, not on borrowed authority.)*
     ⭐⭐ **AND THE FLAT SWEEP POINTS AT THE REAL CONSTRAINT.** If admission is unchanged from G=5
     to G=∞, then *what decides who trains is not the gap threshold*. A Tier 1 reviewer proposed
     bench membership — `_battler_slots()` (`modules/story/early_game.py:1894`) admits only a
     non-egg mon **holding a damaging move**. ⛔ **THAT IS UNTESTED AND CURRENTLY UNTESTABLE:
     `ids=` records no moves.** Reading the predicate suggests it is permissive, but that is a READ,
     not a measurement — and this project has a logged habit of those diverging.
     ⭐⭐⭐ **2026-09-10 — THE REFUSAL'S DRIVERS ARE NOW NAMED, AND THE OBVIOUS FIX IS DEAD.**
     **[MEASURED BY ME, reproduced by 10 agents]** the §Ch23 refusal message
     (`<Species>#<PID> alone needs <N> frames`) is dominated by ONE species:
     ```
       occurrences (all of x4-runs, stdout.txt): 414 = 198 Marill · 72 Slugma · 36 Mightyena ·
                                                  36 Nincada · 18 each Shedinja/Ninjask/Poochyena/Kadabra
       ⚠ BUT THE DECISION UNIT IS **23 DISTINCT REFUSAL EVENTS**, not 414 lines: each event renders
         18x in stdout and 15x in debug-logs (both counts correct, same events).
       Marill is named in **11 of 23 events = 47.8%** — the proportion HOLDS at event level.
     ```
     ⭐ **AND THE BENCH MECHANISM DEMONSTRABLY WORKS — THE LIST IS MERELY INCOMPLETE:**
     **[MEASURED BY ME, batch `20260909-160339`, n=13 Castform / 34 Zigzagoon]** `Castform` has a **92.3%** laggard rate and **0** refusals *because it is benched*; `Zigzagoon`
     20.6% and 0 refusals, benched. `Marill` (100% laggard, peak **L14 across 15 runs**, never once
     above L15 in 33 runs corpus-wide; `Azumarill` NEVER OBSERVED) and `Slugma` are the same shape
     and are NOT on the list.
     ⛔⛔ **BUT DO NOT ADD THEM — THE CANDIDATE IS DEAD.** Two reasons; **full record in
     `07-CHANGELOG.md`, "The §Ch23 refusal is diagnosed (HM carriers), and the obvious fix is dead"**:
     1. **Benching is "do not train", NOT "do not field"** (`07-CHANGELOG.md` F6, verified by me in
        code): the faint-replacement chooser (`story_mode.py:273-274`) filters on
        `None / is_egg / current_hp <= 0 / _excluded`, and `_excluded` (`:262-270`) is
        ally-and-already-battling only; `BENCH_SPECIES` has exactly two consumers, both in
        `victory_road.py`. ⇒ it deletes the only gate refusing to enter the E4 with a L13 Marill
        **and still fields it there**. ‼ A no-op on the estimate is not a no-op on the run.
     2. **The refusal is an ARGMAX** (`worst = max(estimates)` vs 250,000), so removing the named mon
        promotes the next: **6-10 of 23 events clear** *(four agents re-priced every event independently; conservative count 6)*, and the top residual is **Mightyena, the
        CRUNCH carrier that can never be benched**.
     ⭐ **THE DIAGNOSIS THAT SURVIVES, AND IT IS WORTH KEEPING:** the bot acquires **HM carriers it
     can neither train to the bar nor safely field** — Marill is caught purely as a Dive/Waterfall/
     Surf carrier and sits at **L13 in 100% of 521 sightings in the one exp-bearing batch** ⚠ **(corpus-wide it DOES level: 1,492 readings above L13 across 33 logs — see the correction below)**. The refusal is the MESSENGER, not the
     defect. ⇒ any real fix is UPSTREAM of both benching and training, and must answer *"what should
     happen to a mon that is carried for a field move and can never reach the battle bar?"*
     ⛔⛔ **THE SOLUTION SPACE, NARROWED BY MEASUREMENT — THREE DIRECTIONS ARE DEAD:**
     | direction | why it is dead | evidence |
     |---|---|---|
     | widen `TRAIN_CATCHUP_GAP` | admits **+2 mons** from G=6 to G=∞ | `probe_catchup_threshold_sweep.py` |
     | add the mule to `BENCH_SPECIES` | benching is *do not train*, **not do not field** — deletes the only gate and still fields it | `story_mode.py:273-274`; `07-CHANGELOG.md` F6 |
     | acquire the carrier at a better ground | **L27 still refuses** (336,755 vs a 250,000 ceiling) | `probe_dive_carrier_level.py` |
     ⭐ **WHAT THE MEASUREMENTS AGREE ON:** the carrier is **INERT IN THAT BATCH** — 521/521 sightings at
     `L13:exp1757` ⚠ **(NOT corpus-wide: 1,492 readings above L13 across 33 logs, and "never" was also CENSORING — 25 of 28 non-gainers were observed for less time than the slowest gainer needed)** — and the gate counts it as a battler. ⇒ any surviving fix
     must change **whether it is in the party at the gate**, or **whether the gate counts it**, not
     how much it is trained.
     ⛔⛔ **AND A PC DEPOSIT IS THE FOURTH DEAD DIRECTION — found by `precheck_prior_art.py` in two
     minutes, before any design.** `06-DECISIONS-LOG.md:1313-1316`: *"**Deposit to make room** — the
     real fix… Rejected FOR NOW because it is the shape of `POKEBOT_PC_ROTATION`, **which is disabled
     for costing ~19 points by depositing team members**."* ⇒ it was TRIED and it LOST 19 points.
     ‼ And the machinery carries **four documented live defects** (`06-DECISIONS-LOG.md:2694-2716`):
     `withdraw_from_box` counts `alive` EXCLUDING EGGS (its own sibling fixed exactly that bug);
     `interact_with_pc` has **unbounded `while … press A` loops** (`:424-433` plus four more), and per
     the decomp `Task_WithdrawMon` on a full party never reaches the state they wait for; the capacity
     guard tests `get_party_size()` when the game uses `CalculatePlayerPartyCount()`; and its blanket
     `except Exception` has no `StoryAbort` guard, so **a whiteout during a PC visit is being
     LAUNDERED today**. ⇒ depositing the carrier is not a quick win, it is four prerequisites deep.
     ⛔⛔ **AND THE FIFTH DIRECTION IS DEAD TOO — "bench a mon that has never gained exp since
     capture". KILLED 2026-09-10 BEFORE ANY CODE, BY A PROOF.** **Four CATCH-OBSERVATIONS across THREE distinct `Abra`** (one PID recurs in two separate reset-runs of the same lane — deterministic RNG, not two mons) were caught
     byte-identical at `L7:exp236` (the exact MediumSlow curve minimum); **three trained on to
     Kadabra L17-L20 and one never gained a point** — *verified by me*:
     ```
       A5FC8AAC  L7:exp236 -> Kadabra L20      BCE77DD9  L7:exp236 -> L7:exp236  (inert)
       A5FC8AAC  L7:exp236 -> Kadabra L17      51A86B58  L7:exp236 -> Kadabra L17
     ```
     ⇒ **at capture every mon satisfies the predicate**, and minutes-to-first-exp-gain across 89
     genuine catches is **continuous, not bimodal** (1,1,1,1,2,2,2,3…44,47,128,256,397,420,459 — no
     gap). Misclassification never falls below **65%** at any threshold. **No predicate reading
     current state can separate a tool from a future battler.**
     ⛔ **AND IT WOULD MAKE THINGS WORSE.** The predicate is MONOTONE (false→true only) and
     `team_is_ready` re-runs `battler_identities()` AFTER the grind (`victory_road.py:2055`): a mule
     excluded at the estimate that later gains one point **re-enters at L13 and raises after the
     budget is spent** — moving the refusal from before the cost to after it.
     ⛔⛔ **AND MY OWN LOAD-BEARING CLAIM WAS WRONG AT CORPUS SCOPE — CORRECTED HERE.** I published
     *"all 521 Marill sightings read `L13:exp1757`; the carrier NEVER gains a point"*. That is true
     of **one batch** and false of the corpus: across all **33** Marill-carrying logs the levels are
     `L13: 5,951 | L14: 926 | L15: 566` ⇒ **1,492 readings above L13**, and 5 of 33 runs show it
     levelling. ‼ It is also **CENSORING**: the slowest observed gainer needed 157 minutes, and
     **25 of 28 non-gainers were observed for less time than that**. ⇒ "inert" was an artifact of the
     observation window as much as a property of the mon.
     ⭐⭐ **AND THE PROCESS LESSON — THE MANDATORY FIXTURE TEST WAS VACUOUS.** Every member of the
     known-good fixture sits far above its capture level, so this predicate benches NOBODY there and
     "passes" while discriminating nothing. **Passing the test that killed the 2026-09-08 design was
     NOT evidence for this one.** A mandatory check that a candidate satisfies trivially proves
     nothing — the check must be one the candidate could FAIL.
     ⇒ **FIVE DIRECTIONS ARE NOW DEAD AND THERE IS NO SURVIVING CANDIDATE.** That is the honest
     state. The next attempt should start from the ROUTING question (is the carrier needed at
     §Ch23 at all?) rather than from another predicate over party state.
     ⛔ Run `tools/story-dev/precheck_prior_art.py` first: it has now killed four directions.
     ⛔ **DO NOT BUILD A FOURTH DESIGN WITHOUT RUNNING `tools/story-dev/precheck_prior_art.py` FIRST**
     — three have died here in two days, and two of the three were killed by arguments already in
     this repo.
     ⚠ **SIDE FINDING, load-bearing if anything here is ever promoted:**
     `custom-pokebot/modules/story/victory_road.py:1806` has **NO empty-battler guard**; it exists
     only in sandbox (`:1817-1827`). `06-DECISIONS-LOG.md` shipped that guard as a hard prerequisite
     for touching this predicate ⇒ promote the guard WITH any change, or the prerequisite is
     silently unmet.
     ⭐⭐ **THE QUESTION THAT REOPENS, AND IT IS THE REAL ONE:** if caught mons DO train and DO reach
     the window, **why is `#24-lowlevelmules` still ~a third of run-ends?** The cause is NOT "they
     cannot get into training". That is now ruled out with evidence, and the next investigation
     should start from what happens AFTER they are admitted.
     ⚠ **DENOMINATOR: 1,496 IS NOT REPRODUCIBLE.** An adversarial sweep of 17 unit definitions x 39
     batches found no population of 1,496 anywhere, and none within +-5% of it at +-3pp of 88.8%.
     ⭐ The likeliest explanation is benign and was found by the same pass: keying `party=` by
     **species + re-entry generation** (the natural pre-PID method) yields **81.9% / median 11 on
     story runs alone — the claimed median exactly**. ⇒ treat 1,496 as an artifact of a pre-`ids=`
     instrument, not as evidence of bad faith; and note the direction — species keying
     **UNDERSTATES** born-behind (72.9% vs 84.1%), so the instrument cannot explain a too-HIGH
     number.
     ⛔⛔ **AND THE MECHANISM SENTENCE WAS WRONG — VERIFIED IN THE CODE, NOT REPORTED.** This bullet
     used to say *"`TRAIN_CATCHUP_GAP = 6` excludes them from `to_train`"* keyed on the TEAM MAX.
     `story_mode.py:2135-2137` actually reads:
     ```python
     catchup  = target - self.TRAIN_CATCHUP_GAP        # target - 6, NOT team_max - 6
     to_train = {i for i in battlers if party[i].level >= catchup}
     to_train.add(strongest)                            # <- the strongest is ALWAYS included
     ```
     with `need = [i for i in to_train if party[i].level < target]` at `:2142`. ⇒ the window is
     **`target - 6 <= level < target`**, and `target` is **`team_max + 1`** in boss-fodder mode
     (`:2095`) but the **BOSS BAND** otherwise. So the exclusion is REAL and the framing was
     imprecise: in the team-keyed branch it is ">5 behind team max", near enough that the original
     conclusion survives — but a reader planning against "6 behind the team max" is planning
     against the wrong quantity in the branch that does not use it.
     ‼ `to_train.add(strongest)` and the `losses >= 2` top-up mean the set is **not purely
     gap-based** — another reason a plan keyed on a single gap number can miss.
  2. ⛔ **[AGENT, UNVERIFIED] THE ECONOMICS ARE SOMETIMES NEGATIVE.** `xp/battle = 50.2 * wild_level
     / 7` depends ONLY on the DEFEATED wild's level, so a level-matched (lower) band pays LESS per
     battle and can only win via the full-vs-half share — capped at 2.0x. Reported example: a L12 mon
     soloing its matched ROUTE117 earns **71.7 xp/battle** against **78.9** swap-training on
     ROUTE111 — **0.91x, i.e. WORSE**. ⇒ *"a matched area beats swap-training"* is not a general
     truth under this codebase's own XP model.
  3. ⛔ **[AGENT, UNVERIFIED] IT DOES NOT EVEN DELIVER "FULL XP".** The picker's winnability boundary
     (`mon_level >= lo - 1`) OVERLAPS the swap trigger (`level + 2 <= foe.level`): at L18 its own
     pick still swap-trains on **75%** of the band.
  ⭐ **WHAT THE ROUND DID ESTABLISH, AND IT IS NOT NOTHING:** early maintenance would be far cheaper
  than late payoff (**[AGENT, UNVERIFIED]** ~1.2% of a lane budget at Stone vs ~33% at Feather), so the distinction
  from the killed §Ch23 relocation is REAL — the idea fails on its own mechanism, not by being that
  fix again.
