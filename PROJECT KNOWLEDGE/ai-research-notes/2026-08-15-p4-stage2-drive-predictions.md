# (P4) STAGE 2 drive — PRE-REGISTERED predictions (2026-08-15)

> ‼ **THIS IS A NOTE, NOT TRUTH.** Read `00-READ-THIS-FIRST.md`. Written **BEFORE** the first
> `--driver boxcounter2` run, per `14-AGENT-PLAYBOOK.md` §4c rule 3.
> Sources: `2026-08-15-p4-boxcounter-repro-design.md` (the Stage 2 spec, §5 steps 5-8 and §9),
> the **live** measurement `probe_box_contents.py` (NEW, this session), and direct reads of
> `counter_hunt.py`, `pc_trip.py`, `higher_level_actions.py`, `story_mode.py`.

## The thing under test

`--driver boxcounter2` (NEW) = **acceptance steps 5-7** of the design note's §5 chain, run from
`saves/ch13_fortree_door.ss1` (ROUTE120, badges 12345, Winona unbeaten, party FULL at 6).
It **SUBCLASSES `BoxCounterMode`**, so every Stage 2 run RE-PROVES Stage 1 first
(playbook §4c rule 2: *copy a proven phase and it will rot; SUBCLASS it and it cannot*).

Chain: Stage 1 (inject Slugma → `box_counter_pid` under the arm) → publish the returned PID into
`_hunted_counter_pids` → **the real `heal_in_pokemon_center(PokemonCenter.FortreeCity)`** with its
three PC piggybacks → assert the Slugma MOVED box→party by IDENTITY → `_lead_best_matchup` →
a SECOND heal whose withdraw must NO-OP.

## ‼ FOUR THINGS MEASURED THIS SESSION THAT CHANGED THE DESIGN

1. ⛔⛔ **THE ANCHOR'S BOX IS NOT EMPTY, AND ITS OCCUPANT QUALIFIES.** Measured live
   (`probe_box_contents.py ch13_fortree_door.ss1`, exit 0):
   `box0.slot0 = Castform L25 pid=6ADF9056 types=['Normal']` — **type_match=False**, but
   `move[0] = Powder Snow type=Ice` (damaging) and `move[3] = Hail type=Ice`, so
   **move_match=TRUE against `NEEDED={Rock,Ice,Dragon,Electric}`**, and it sits at the **FIRST**
   box slot, ahead of anything injected. `box_counter_pid` returns the FIRST match in box order.
   ⇒ **Stage 1's `sole` control (`occupants == [pid]`) ABORTS on this anchor.** This is the
   design note §8 risk #4 (*bystander shadowing*) turning out to be LIVE, not hypothetical.
2. ✅ **PRODUCTION ALREADY NEUTRALISES THE SHADOW — the driver's own control was the only
   casualty.** The Castform is in the box BEFORE the run, so it is in `before = _box_pids()`,
   which is passed as `exclude_pids`, and `counter_hunt.py:288` skips it
   (`if pid is None or pid in exclude_pids: continue`). The mechanism the design note feared
   (§3, `exclude_pids` self-defeat) is here the mechanism that SAVES the test.
3. ✅ **`post_dive.ss1`'s 14 boxes are ALL EMPTY** (`boxed_count=0`) — which is precisely why
   Stage 1's `occupants == [pid]` passes there today, and why the defect above was invisible.
4. ⛔ **`needed` CANNOT be obtained by calling `_boss_plan_is_hopeless()` live.** It returns
   `(False, [])` unless losses have PLATEAUED (`story_mode.py:1507` needs
   `losses >= PLATEAU_LOSS_THRESHOLD`, `:1512` needs ≥6 KO-history entries). A fresh anchor has
   zero losses. ⇒ derive `needed` from the **type chart** seeded by Winona's real `ace_types`.

## ‼ THE `sole` CONTROL IS REPLACED BY ONE THAT USES PRODUCTION, NOT A RE-IMPLEMENTATION

⛔ The tempting fix — re-computing "does this bystander qualify?" in the driver — is the exact sin
the design note §4 flags (`repro_box_counter_move_test` re-implements type-only against fakes, so
the REAL hook could rot unnoticed). Instead, **ask production the question directly**, with the
fixture itself excluded:

```
sole = box_counter_pid(NEEDED, exclude_pids=before | {slugma_pid}) is None
```

*If nothing else in the box can be returned when the Slugma is taken away, then the Slugma is the
only thing that could have been returned.* Zero re-implementation, and it is the right control in
**both** arms: under ARM B it proves no bystander qualifies by type **or** move; under ARM A
(move branch skipped) it proves no bystander qualifies by **type** — which is exactly what ARM A's
expected `None` requires. Bystanders are still ENUMERATED and PRINTED for diagnosis, but the
enumeration is descriptive only — **the verdict never depends on driver-side logic.**

## ‼ WHERE THE PID COMES FROM — the difference between this test and the one that missed the bug

Design note §8 risk #7: `boxwithdraw` HAND-SETS `_hunted_counter_pids`
(`story_harness.py:4326-4327`), bypassing `box_counter_pid` entirely — **that is precisely why the
existing driver never caught this bug.** Stage 2 therefore publishes ONLY what production returned:

```
self._hunted_counter_pids = set() if got is None else {got}     # `got` = box_counter_pid(...)
```

⇒ **ARM A reproduces the user's derail END TO END and ORGANICALLY**: `got is None` → the set is
empty → `counter_withdraw_outcome()` returns `False` → `higher_level_actions.py:342` logs the SKIP
and `:343` never calls `withdraw_from_box` → the heal completes and the counter STAYS BOXED.
That is the user's bug, produced by production logic, not by the test.

## Pre-registered predictions

| # | prediction | if it FAILS, what that means | source |
|---|---|---|---|
| P1 | Stage 1 re-proves under the subclass on the NEW anchor: `fixture_ok=True disjoint=True not_excluded=True sole=True`, ARM B `pid_match=True`. | If `sole=False`, a SECOND qualifying non-excluded mon exists that the live probe did not see — re-measure the box before anything else. | Stage 1 PASSES today on `post_dive`; finding 2 above |
| P2 | `before_box_pids` contains **exactly one** PID, `6ADF9056` (the Castform), and `slugma_pid ∉ before`. | A different/extra PID means the anchor drifted or the injection ran before the snapshot (§3 self-defeat). | live probe |
| P3 | `needed` derived from the type chart with `ace_types=("Dragon","Flying")` equals **{Rock, Ice, Dragon, Electric}**. | A mismatch means the type chart or our type data changed — LOUD by design (§8 risk #11). | `story_mode.py:3535` `"ace_types": ("Dragon","Flying")`; `:1600-1606` |
| P4 | ARM B: after the FIRST real heal, `slugma_pid` is in the PARTY **by PID**, and `contains_pokemon(slugma)` is **False** — it MOVED, it was not copied. | If BOTH are true-ish but the box still holds it, the write path duplicated rather than moved. | design §5 step 5 |
| P5 | ARM B: the withdrawn Slugma still `knows_move("Rock Throw")` — the move that made it a counter survived the transfer. | A lost moveset means the box→party copy is lossy; that would invalidate the whole counter-hunt feature, not just this test. | design §5 step 6 |
| P6 | ARM B: the party is STILL 6 after the withdraw, because `pc_trip.py:438-462` deposits one dead weight to make room. ⛔ **REPORTED, NEVER GRADED** — a count cannot distinguish success from doing nothing (measured: `party_before=6 party_after=6 box_before=2 box_after=2` on a SUCCESSFUL withdraw). | n/a — reported only. | design §5 preamble; `harness_withdraw3.log:467` |
| P7 | ARM B: `_lead_best_matchup(["Flying"], hunted_pids={slugma_pid})` puts `slugma_pid` in **slot 0** (by PID, never index). | If slot 0 is someone else, `_is_hunted_counter` (`early_game.py:1759-1771`) is not reaching `lead_rank_key` — the `#24-leadcounter` surface that reported `hunted_pids=0` on 684 decisions. | design §5 step 7 |
| P8 | ARM B: a SECOND full heal NO-OPs the withdraw — `find_in_box()` returns `None` because the mon is in the party now (`pc_trip.py:420-422`), so party PIDs are UNCHANGED across heal 2. | ⛔ **A no-op has innocent causes** — box empty, party full with nothing safe to deposit (`:452-457`). The driver must therefore assert the *reason*: `find_in_box` is `None` AND the Slugma is in the party — never "nothing happened". | design §5 step 7 |
| P9 | ARM A: `_hunted_counter_pids == set()`; after the heal the Slugma is **still in the box** and **not in the party**; the `_piggyback_report` SKIP line names the empty set. | If ARM A's Slugma reaches the party anyway, something other than `_hunted_counter_pids` is driving withdrawals. | design §6; `higher_level_actions.py:336-344` |
| P10 | The whole chain is bounded: ROUTE120 → Fortree PC → heal ×2 fits well inside `--frames 400000` (closest measured: `boxwithdraw` did TWO full heals with PC round-trips in ~24,841 frames). | A frame blow-out means the navigation, not the PC, is the problem — read the last milestone printed. | design §7 |
| P11 | ⛔ **REPORTED, NOT GRADED:** the gym leg. It is **OFF by default** (`POKEBOT_BOXCOUNTER2_GYM=1` to enable) — an L15 Slugma will likely lose to Altaria L33, and a whiteout drops to Manual, where KI-71 abandons the generator and NOTHING prints. All grading and the `ACCEPTANCE:` line therefore complete **BEFORE** any gym attempt. | n/a — reported only. | design §5 step 8; KI-71 |

## Pre-registered failure modes

* ⛔ **A fixture defect reading as the bug.** `box_counter_pid` swallows every exception into
  `return None` (`counter_hunt.py:318-319`), so a Slugma that failed to decode is
  INDISTINGUISHABLE from ARM A's expected miss. Stage 1's read-back control through the PRODUCTION
  reader runs first and aborts with a message DISTINCT from a test failure.
* ⛔ **`withdraw_from_box` NEVER RAISES** (`pc_trip.py:475-478`, blanket `except`). "No exception"
  is not evidence. Every step-5/6/7 claim is a post-hoc IDENTITY assertion.
* ⛔⛔ **PRODUCTION PRINTS A SUCCESS IT DID NOT VERIFY** — `pc_trip.py:472-473` does
  `after = len(get_party())` and then prints *"{name} is in the party"*. That is a COUNT
  masquerading as an identity claim, and a driver that greps for that line would be fooled by a
  silent failure. ⇒ **never grade on that message.** (Filed this session; see `05-KNOWN-ISSUES.md`.)
* **A derail to Manual mid-heal (KI-71)** abandons the generator with no exception and no RESULT.
  Mitigated as §6 specifies: Stage 1's decisive verdict is emitted BEFORE the risky leg, and a
  PRE-RISK attribution line (arm, map, position, party HP, the PID) is printed immediately before
  the heal so a silent death is still attributable.
* **The anchor drifting.** `ch13_fortree_door.ss1` is a VOLATILE fixture. P2 asserts its box
  contents, so a changed anchor fails loud instead of quietly changing what the test means.

## What this does NOT prove

* Nothing about a real `hunt()` — the Slugma is INJECTED, not caught. The catch half is Stage 1's
  standing caveat and remains untested end-to-end.
* Nothing about Winona being BEATEN. P11 is an observation, off by default.
* Nothing about the `(P3) party-accounting` A-vs-B question. This run DOES mutate the party
  (a deposit + a withdraw), so it is the first population member that could — see the
  `(P3b)` caveat that no prior drive mutates the party.

---

# ✅ RESULTS (appended 2026-08-15, AFTER the drives — the predictions above are UNEDITED)

**Scorecard: 9 of 11 predictions held; 1 was REFUTED and cost the anchor; 1 (P3) was refuted in a
way that found a real defect in our documentation.** Matrix `{ARM A, ARM B} × {sandbox, custom}`:
**4/4 `ACCEPTANCE: PASS`**.

| # | verdict | evidence |
|---|---|---|
| P1 | ✅ HELD | Stage 1 re-proved under the subclass on every run: `fixture_ok=True disjoint=True not_excluded=True not_in_party=True needed_ok=True sole=True pid_match=True`. |
| P2 | ✅ HELD (on `ch13_fortree_door`) | `SNAPSHOT before_box_pids=1 entries (['6ADF9056'])`, fixture landed at `box(0, 1)` — i.e. BEHIND the Castform — and `BYSTANDERS: Castform:6ADF9056 EXCLUDED`, `sole=True`, ARM B still returned the fixture's PID. **The shadow was real and production excluded it, exactly as predicted.** |
| **P3** | ⛔ **REFUTED — and it found a documentation defect that had stood for a year** | First run of the new control printed `derived=['Dragon','Ice','Rock'] ; literal=['Dragon','Electric','Ice','Rock'] ; needed_ok=False` and **ABORTED the fixture rather than testing a set production would never pass.** Electric is **0.5x into Dragon** × 2.0x into Flying = **1.0 — NEUTRAL on Altaria**. See the dedicated section below. |
| P4 | ✅ HELD | ARM B: `AFTER-HEAL in_party=True still_boxed=False moved=True` — both halves, so it MOVED rather than being copied. |
| P5 | ✅ HELD | `MOVESET-SURVIVED knows_rock_throw=True`. |
| P6 | ✅ HELD (reported) | `PARTY-COUNT before=6 after=6`, with `DEPOSITED-TO-MAKE-ROOM ['Skitty L17']`. Confirms the design's warning: the count is **identical** on success, so it can never grade this. |
| P7 | ✅ HELD, **and the control proved the mechanism was decisive** | `LEAD control(hunted=None)=5C96EA9B (Mightyena L38) ; real(hunted={fixture})=…(Slugma L15) ; lead_is_counter=True`, `LEAD-MECHANISM-DECISIVE=True`. Without `hunted_pids` a different mon leads ⇒ this step **could** have failed and did not. |
| P8 | ✅ HELD, attributed | `SECOND-HEAL party_unchanged=True still_in_party=True find_in_box=None noop_attributed=True` — the no-op is because the mon is already in the party, not because the box was unreadable. |
| P9 | ✅ HELD | ARM A: `PUBLISHED _hunted_counter_pids=[]` → `AFTER-HEAL in_party=False still_boxed=True moved=False` → `ARM-A RESULT hunted_counter_pids_empty=True still_boxed=True not_in_party=True`. ⚠ Note ARM A also printed `DEPOSITED-TO-MAKE-ROOM []` — **production did not even deposit**, which is the cleanest possible contrast with ARM B's `['Skitty L17']`. |
| P10 | ✅ HELD | ~25,490 recomputes/frames-order for ARM B, well inside `--frames 400000`. |
| P11 | ✅ HELD | `STEP 8/8 — gym leg SKIPPED (set POKEBOT_BOXCOUNTER2_GYM=1 to run it).` ACCEPTANCE printed before it, as designed. |

## ⛔⛔ THE ANCHOR IN THE DESIGN NOTE IS REFUTED BY MEASUREMENT — USE `fortree_gym_wedge.ss1`

The design note's §7 "SUPERSEDED BY MEASUREMENT" correction told Stage 2 to use
`ch13_fortree_door.ss1` (ROUTE120) **instead of** `fortree_gym_wedge.ss1`, reasoning that starting
INSIDE the gym "adds a gym-exit leg that is pure risk". That reasoning was about POSITION and was
never tested against ROUTING. **It is wrong**, and the first Stage 2 drive proved it:

```
f32: *** BotModeError -> Manual: Cannot reach FORTREE_CITY: it is not walkable from ROUTE120,
     and none of the 6 candidate warp route(s) start at a tile that can be walked to from here
```

⇒ **This is KI-24, and it is DOCUMENTED IN OUR OWN CODE.** `modules/story/region_reach.py:7-11`:
*"Routes 118/119/120 are the dual-elevation-bridge maps `calculate_path` reads as WALLS"*. Every
Winona-era (`badges=12345`) anchor we own sits on ROUTE119/ROUTE120 **except** the gym wedge
(`probe_anchor_inventory.py`) — so the wedge is not merely acceptable, it is **the only Winona-era
anchor from which the production heal can route at all.** The feared gym-exit leg cost nothing:
`navigate_to_anywhere` walked out through the warp and reached the PC on the first attempt.
✅ `fortree_gym_wedge.ss1` is FULL at 6 (Mightyena L38, Sceptile L39, Swellow L33, Skitty L17,
Zigzagoon L3, Castform L25) with an **empty box** and no PID collisions.
⚠ **What is LOST by the swap** — and it is not nothing: the wedge has **no Shedinja/Ninjask twin
pair**, so Stage 2 no longer runs over a live KI-78 collision. `ch13_fortree_door.ss1` still holds
that pair and is still the right anchor for any test whose subject IS the collision.

## ⛔ THE `needed` SET WAS WRONG IN FOUR PLACES, AND ONLY A DERIVATION CAUGHT IT

`{Rock, Ice, Dragon, Electric}` appears in `counter_hunt.py:250`, in this project's design note, in
the handoff, and was hardcoded in the Stage 1 driver. **Production has never computed it.**
`_boss_plan_is_hopeless` derives `needed` from `cfg["ace_types"]` **alone** — and Winona's `cfg`
names the ACE, `("Dragon", "Flying")` (Altaria L33). Electric: 0.5 × 2.0 = **1.0**.
The old claim is mis-scoped rather than invented — Electric IS 2.0x on Swablu/Tropius/Pelipper/
Skarmory, all pure-ish Flying — but the bot's own rule looks only at the ace.
‼ **The lesson is about the INSTRUMENT, not the fact**: four documents agreed with each other for
a year because they were copies of one another. The moment a control asked the LIVE TYPE CHART
instead of asking another document, it fell over on the first run. *Agreement between documents is
not evidence; only a derivation from the source of truth is.*
⇒ Corrected in `counter_hunt.py` (sandbox — **this creates drift; promotion is the user's call**)
and in the driver, which now DERIVES the set and grades the derivation against the expectation.

## What these four runs do NOT prove (unchanged, and worth repeating)

* **Nothing upstream of registration.** The Slugma is INJECTED and the PID is published by the
  driver from `box_counter_pid`'s return. The real `hunt()` → `story_mode.py:1750` wiring is still
  untested end-to-end; `hunt()` snapshots its own `before_box_pids` AFTER travel, so an injected
  fixture would be excluded a second time. That is the honest remaining gap in (P4).
* **Nothing about beating Winona.** The gym leg is off by default and reported-not-graded.
* **Nothing about KI-79.** The unverified success print was found by READING, and every drive so
  far printed it truthfully.
