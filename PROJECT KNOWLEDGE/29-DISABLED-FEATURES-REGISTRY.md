# 29 — DISABLED FEATURES & FLAG REGISTRY

> **Current-state file.** Every `POKEBOT_*` environment flag in the bot code must appear here.
> `lint_docs.py` **fails** if one does not — see R6.

---

## ‼‼ WHY THIS FILE EXISTS

The 2026-08-11 review's error taxonomy names **family C — "removing/altering something that was
WORKING"** as the family with the worst measured cost in the project's history:

* a heal-time party deposit cut the finish rate **47% → 5%** (2026-08-02);
* a **WINNING** lead was removed on the strength of one observed loss (2026-08-03);
* *"I removed a WINNING behaviour for **the second time in a week, having already written the rule
  against it**"* (2026-08-04);
* *"**THIRD** removal-shaped feature in a week that cost more than it saved"* (2026-08-05);
* a component was removed on a **7→8** reading and it was the best-performing config (2026-08-06).

`pc_trip.py`'s own comment states the shared cause exactly:

> *"All three were features that REMOVE something, justified by counting what they SAVED and never
> what they COST."*

‼ **AND IT HAPPENED AGAIN ON 2026-08-11.** Asked to improve boss performance, I recommended
"roster hygiene before bosses" — **a feature that had already been built, measured harmful, and
pinned off months of runs earlier.** Only a manual pre-build check caught it (KI-54). Nothing in the
repo would have stopped me: the measurement lived in a code comment inside `pc_trip.py`, where
nobody looks before proposing a feature.

⇒ **This registry is that measurement, moved somewhere it will be found.** A flag pinned at `0` is
not a leftover — it is usually a *result*, and the result is expensive to re-derive.

## HOW TO USE IT
* **Before proposing or building anything**, check whether a flag here already covers it.
* **Never flip a `HARMFUL` flag on in production** without a batch that measures the cost the
  original measurement recorded.
* When a new flag is added to bot code, add a row here **in the same commit** — the linter enforces it.

---

## A. FEATURES MEASURED HARMFUL AND PINNED OFF
‼ These are **results, not TODOs.** Re-enabling one is a decision that needs a batch, and it is the
user's call.

| flag | default | what it does when ON | the measurement that turned it off |
|---|---|---|---|
| `POKEBOT_PC_ROTATION` | `0` | deposits "dead weight" to the PC at heal stops (`pc_trip.deposit_dead_weight_if_worth_it`) | **Team size at Feather 5.65 / 5.72 / 5.81 (off) → 4.45 / 4.75 (on). Balance→Feather 83 / 75 / 70% → 52 / 57%.** It removes ~one whole team member permanently and the last funnel rung collapsed over that transition. ‼ It also deposited a **hunted counter** the chain had crossed Hoenn to fetch (2026-08-03) |
| `POKEBOT_AREA_ITEM_GATE` | `0` | refuses item-gated hunting areas (`#24-areaitemgate`, `#24-counterdesertgate`) | one of the **three removal-shaped features in one week** named in `pc_trip.py`'s comment. ‼ Its specific numbers are in `07-CHANGELOG` / `08-MISTAKES` around 2026-08-05 and are **not transcribed here yet** — do not quote a figure from this row |
| `POKEBOT_LEAD_DEMOTE_WONDER_GUARD` | `0` | demotes a Wonder Guard lead (`#24-leadpolicy` (c)) | the code's own comment says it is **"a HYPOTHESIS under test, not a settled fact — batch7 carried five changes"**, i.e. it was never cleanly attributed. Off because unproven, not because disproven |
| `POKEBOT_HUNT_ANYGROUND` | `0` | relaxes hunting-ground narrowing to any ground | **permissiveness measured 28 wasted treks and 15% conversion; the narrowing took conversion to ~50%.** ‼ "Do NOT relax the narrowing to manufacture a candidate" is a standing note |

## A2. BUILT BUT NEVER WORKED — off because it DELIVERED NOTHING, not because it was harmful
‼ This distinction matters and the code is careful about it: *"it is gated because it DELIVERED
NOTHING, not because it was proven harmful."*

| flag | default | what it does when ON | why it is off |
|---|---|---|---|
| `POKEBOT_BOX_OVERFLOW_CATCH` | ‼ **`1` — ON, NOT DISABLED** | lets a catch overflow into the **PC box** when the party is full (`#24-pcoverflow`) | ‼‼ **THIS ROW WAS STALE FROM 2026-08-11 TO 2026-08-12 AND BLOCKED REAL WORK.** It said `default 0` and named an "EXTRA TEXT BOX" blocker. Both were **already refuted on 2026-08-07** — four days before this row was written. The live code is `story_mode.py:2241-2243`, `_os.environ.get("POKEBOT_BOX_OVERFLOW_CATCH", "1")`, i.e. **default ON**, with the capability test recorded in the comment directly above it: `--driver boxcatch` on a full party + empty box gave `caught=True box_before=0 box_after=1 exited_clean=True exit_frames=120`, then `AFTER-CATCH usable=True second_catch=True frames=20 box_now=2`. **Zero forced presses — the existing battle handler rides the box-send message out.** The original batch verdict ("never fired in 26 runs") was true and meant only that the counter hunt never had a full party when it fired. **Set to `"0"` to disable.** |

⛔ **RETRACTED 2026-08-12 — the paragraph that used to sit here was the refuted claim, repeated
four lines under its own retraction.** It said this was *"THE MISSING PRECONDITION FOR ROSTER WORK
(KI-54) … what stands in its way is one unhandled text box"*. **Both halves are false.** The flag
has defaulted to **ON** since 2026-08-07, and the text box needs **no handling** (`--driver
boxcatch`: `exited_clean=True exit_frames=120`, zero forced presses). Nothing stands in the way of
box-overflow catching; it works today.

‼ **Kept as a warning rather than deleted, because the failure mode is the lesson:** a retraction is
worthless if the retracted sentence still reads as live advice elsewhere in the same file. The
root-cause comment in `story_mode.py:2202` — which is what produced the four wrong documents — is
now also explicitly marked HISTORY in both forks.

## A3. FIVE FLAGS THE GATE COULD NOT SEE (registered 2026-08-14)

> ⛔ **These five existed in code while `lint_docs.py` printed "11 flag(s) in code, 11 documented"
> and exited 0.** The R6 scan matched only `environ.get("POKEBOT_…")` literals — blind to
> `os.getenv`, to names held in constants, and to files outside its roots. The scan is now
> accessor-agnostic and the roots include `pokebot.py` + `tools/story-dev`. Found by a cold-start
> audit; the widened gate fired on exactly these five before this section existed (its A/B).

| flag | default | what it does when ON | notes |
|---|---|---|---|
| `POKEBOT_ENCOUNTER_BENCHMARK` | off | grows the encounter buffer 100 → 1000 for benchmarking (`modules/stats.py:632`, via `os.getenv`) | upstream-inherited tuning knob; no measurement attached |
| `POKEBOT_RNG_DECORRELATION_FRAMES` | on (nonzero) | frames of RNG decorrelation at story-mode start (`modules/story/intro.py:77`, name held in `_RNG_DECORRELATION_ENV`) | `=0` disables and restores fully deterministic replays — that is its A/B use |
| `POKEBOT_STORY_DEBUG_TURBO` | on | matches x4-lane turbo settings in interactive story runs (`plugins/custom_modes/story_mode.py:3706`, name in `_TURBO_ENV`) | `=0` opts out and leaves emulator settings untouched |
| `POKEBOT_UNTHEMED` | `0` | `=1` disables the GUI theme (`sandbox-pokebot/pokebot.py:272`, via `os.getenv`) | cosmetic; also reachable via settings |
| `POKEBOT_CH20_FAULT` | unset | `=room1` forces the §Ch20 Room 1 solve to FAIL so the drivers' failure branch is exercisable on demand (`tools/story-dev/story_harness.py`) | ‼ A PERMANENT fault hook, not a leftover — an `AttributeError` lived on that branch precisely because no green run could reach it. A fault-mode run MUST print `ACCEPTANCE: FAIL`; printing PASS is the defect |
| `POKEBOT_CH21PROBE_FAULT` | unset | `=warpcoord` makes `tools/story-dev/probe_ch21_topology.py` look for the Sootopolis dive warp at a coordinate it is NOT at, so the assertion MUST report FAIL and the probe MUST exit 1 | ‼ A PERMANENT self-test, not a leftover. It exists because the FIRST draft of that probe's `warps_of()` iterated TILES and read the MAP-level `.warps`, so all 6,400 tiles reported the same warp and the assertion "there is a warp at (45,65)" passed merely because the TILE (45,65) exists — it COULD NOT FAIL. Fault-tested both ways 2026-08-24: off → EXIT=0, on → 2 FAIL + EXIT=1 |
| `POKEBOT_SKYPILLAR_FAULT` | unset | `=nofall` makes `tools/story-dev/probe_skypillar_clean_layout.py` assert the OPPOSITE of its central finding (that `4F_Clean (11,1)` DOES reach `(3,1)`), which MUST fail | ‼ A PERMANENT self-test. The finding it guards — that the §Ch21 Sky Pillar ascent REQUIRES a deliberate fall through `4F (6,4)`/`(7,4)` — is what makes Ch21 buildable, and a Tier 1 review correctly refused it while it rested only on an uncommitted scratch script. Fault-tested both ways 2026-08-24: off → all PASS EXIT=0, on → 1 FAIL EXIT=1 |
| `POKEBOT_CH21NPC_FAULT` | unset | `=wrongtile` makes `tools/story-dev/probe_ch21_npcs.py` look for Steven at a tile he is not on, so the "LEG 2 IS POSSIBLE" assertion MUST fail | ‼ A PERMANENT self-test. The probe exists because a `calculate_path` to an NPC's OWN tile ALWAYS fails (it is occupied) — my first pass did exactly that for all 18 Sootopolis NPCs, read the universal "refuses" as geography, and wrongly concluded an earlier agent's "Steven at (20,36)" was unreachable. Measured ADJACENTLY, 15 of 18 are approachable and Steven is 27 waypoints away. Fault-tested both ways 2026-08-24 |
| `POKEBOT_POCKET_FAULT` | unset | `=rig` breaks `tools/story-dev/probe_ch21_pocket_exit.py`'s fault-injection rig on purpose (the synthetic “loaded” objects claim the wrong map, so `active_objects` can never match a tile's `dynamic_object_id`). CONTROL 3 — which requires the rig to reproduce the 98 wp that `--driver ch21leg2probe` measured LIVE — must go RED under it, and the probe then refuses to print a single measurement and exits 1. ‼ This is the probe's own fault test: a control that cannot fail is decoration. (2026-08-27) |
| `POKEBOT_CH21_POCKET_ARM` | `follow` | Selects which walk-out design `--driver ch21pocket` drives out of the Sootopolis pocket. `follow` = compute the path ONCE at the resting tile then `follow_waypoints` (never re-plans); `navigate` = a naive single `navigate_to`, whose outer loop restarts a FRESH plan on a waypoint timeout — and a fresh plan taken inside the 90-waypoint danger zone refuses. ⚠ MEASURED 2026-08-27: **both arms produced IDENTICAL output (1,781 frames)**, because with nothing forcing a re-plan they are the same code path. The arm exists to make the comparison runnable, NOT because it has been shown to discriminate. (2026-08-27) |

## B. FAULT-INJECTION SWITCHES (restore a pre-fix behaviour for A/B)
These exist so a fixed bug can be **re-measured without reverting code** — the project's standard
idiom. **The fix is always the default; the switch restores the bug.**

| flag | default | restores |
|---|---|---|
| `POKEBOT_HMTEACH_POSTLEARN_A` | `0` | the `#24-hmteachloop` bug: keep A-mashing after the move is learned, which re-arms "teach it to another POKéMON?" |
| `POKEBOT_TEACHWINDOW_A` | `0` | the `#24-teachmsgstall` bug: the **one-frame** `Task_ReplaceMoveYesNo` detector, and the pre-fix ride ladder |
| `POKEBOT_LEADCANTBATTLE_A` | `0` | the KI-52 bug: raise (and wedge mid-battle) instead of fighting it out |
| `POKEBOT_BOXCOUNTER_TYPEONLY_A` | `0` | the user-observed **Slugma/Winona** bug: `box_counter_pid` skips its MOVE branch and matches on TYPE only, so a boxed counter hunted for its move is missed. Exists for (P4)'s ARM A. ‼ Exercised against the REAL function by `repro_box_counter_move_test.py`, so the hook cannot rot |
| `POKEBOT_PCWITHDRAW_FAULT` | `0` | ⛔ **KI-79's fault hook — a PERMANENT, DOCUMENTED arm, not a leftover.** `=1` makes `withdraw_from_box` (`modules/story/pc_trip.py`) SKIP the PC interaction entirely, so the withdraw provably does not happen while everything around it still runs. ‼ **It exists because the code it guards is an ERROR PATH, and a green happy-path run cannot exercise an error path** — before the KI-79 fix, "the mon arrived" and "we never even tried" printed the SAME green `"{name} is in the party"` line, because that line read a COUNT (`len(get_party())`) and announced an IDENTITY. **MEASURED with this hook:** faulted → `‼ THE WITHDRAW DID NOT LAND. Slugma in_party=False still_boxed=True`, and `--driver boxcounter2` correctly reports `moved=False` / `ACCEPTANCE: FAIL`; unfaulted → green success and `ACCEPTANCE: PASS`. ⇒ it fault-tests the DRIVER as well as the fix |
| `POKEBOT_KI80_ARM4` | `0` | ⛔ **Selects a DIFFERENT EXPERIMENT, not a fault.** `=1` makes `--driver ki80ladder` run **arm 4 alone** — the MIRROR-REGRESSION arm — instead of arms 1-3. It needs a **HAS_ANSWER** save (`fortree_gym_wedge.ss1`), because arms 1-3's NO_ANSWER party makes `_prepare_for_fight` RETURN at `:1924` and never reach the `:1925 boss_mode` line arm 4 exists to watch. It carries its OWN two controls (A: `_boss_plan_is_hopeless` must return **not** hopeless; B: condition 9 INVERTED — `VICTORY_ROAD_1F` `wild_max` 40 must make `grass_is_fodder` False at `team_max` 39) and arms 1-3's anti-vacuity check is deliberately NOT graded under it. **MEASURED 2026-08-16:** PASS on `fortree_gym_wedge.ss1` (`PLAIN_ESCALATION`, no drift); FAIL on a NO_ANSWER save with *"this save is NO_ANSWER (hopeless=True), so it cannot exercise the `:1925 boss_mode` path at all"* — so the control is fault-tested, not merely present |
| `POKEBOT_KI80_DECOUPLED` | `0` | ⛔ **NOT a fault hook and NOT a bug — it flips an EXPECTATION, not behaviour.** `=1` tells `--driver ki80ladder` to require that ALL THREE arms reach `_counter_ladder`, which is what must be true AFTER KI-80's decoupling. Unset, it requires today's coupled matrix (`GRASS_STRONG` -> plain escalation). ‼ **It changes nothing in production — only what the driver GRADES**, which is exactly why the same driver can be both the BEFORE and the AFTER evidence KI-80's fix requires. **MEASURED 2026-08-15:** `=1` FAILS today with *"GRASS_STRONG: expected the counter-ladder branch, got 'PLAIN_ESCALATION'"*, and that FAIL is the proof the check discriminates rather than rubber-stamping |
| `POKEBOT_BOXCOUNTER2_GYM` | `0` | ⛔ **NOT a fault hook and NOT a bug — an OPT-IN for an UNGRADED observation.** `=1` makes `--driver boxcounter2` (P4 Stage 2) attempt the Fortree gym leg after its verdict is already printed. **Off by default ON PURPOSE:** an L15 Slugma will likely lose to Altaria L33, and a whiteout drops the run to Manual where **KI-71** abandons the generator and NOTHING prints — so an enabled gym leg can only ever add noise or a silent death, never evidence. The `ACCEPTANCE:` line is emitted BEFORE it and nothing in the leg can change that verdict (design note §5 step 8: *reported, never graded*) |

## C. TUNING KNOBS (not results)
| flag | default | what it tunes |
|---|---|---|
| `POKEBOT_FAINT_GIVEUP_LIMIT` | `20` | how many faints before a run gives up |
| `POKEBOT_FODDER_RULE` | `xp_rate` | which rule picks fodder |
| `POKEBOT_CONNECTION_STEP` | `0` | ‼ **rationale not yet transcribed.** Documented here only so the linter passes; read the code before assuming what it does |
| `POKEBOT_CH21_FAULT_MISS` | unset | FAULT INJECTION, driver-proof only (2026-08-27): `steven_escort()` faces AWAY on its first approach so the A-press misses — the arm that proves the missed-press bail fires and the approach loop recovers. ⛔ Never set in production; evidence `2026-08-27-ch21escort-missbail-armA-fault.txt` |
| `POKEBOT_CH21_FAULT_WRONGANSWER` | unset | FAULT INJECTION, driver-proof only (2026-08-27): `_answer_wallace_multichoice()` answers index 0 once — the spec §4.9 arm proving the WHERES_RAYQUAZA re-arm is DETECTED (attempt 2, same menu id, state still 2) and RECOVERED to state 3. ⛔ Never set in production; evidence `2026-08-27-ch21cave-wronganswer-armA-fault.txt` |

---

## ‼ HONESTY NOTE ON THIS FILE
Rows in section A marked *"not transcribed here yet"* are **deliberately blank rather than
guessed**. This project's north star includes producing training material for a future agent, and
an invented measurement is worse than an absent one. Fill them from `07-CHANGELOG` /
`08-MISTAKES` when someone next touches the relevant area.
