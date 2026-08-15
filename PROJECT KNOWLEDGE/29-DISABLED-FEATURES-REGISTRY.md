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

## B. FAULT-INJECTION SWITCHES (restore a pre-fix behaviour for A/B)
These exist so a fixed bug can be **re-measured without reverting code** — the project's standard
idiom. **The fix is always the default; the switch restores the bug.**

| flag | default | restores |
|---|---|---|
| `POKEBOT_HMTEACH_POSTLEARN_A` | `0` | the `#24-hmteachloop` bug: keep A-mashing after the move is learned, which re-arms "teach it to another POKéMON?" |
| `POKEBOT_TEACHWINDOW_A` | `0` | the `#24-teachmsgstall` bug: the **one-frame** `Task_ReplaceMoveYesNo` detector, and the pre-fix ride ladder |
| `POKEBOT_LEADCANTBATTLE_A` | `0` | the KI-52 bug: raise (and wedge mid-battle) instead of fighting it out |
| `POKEBOT_BOXCOUNTER_TYPEONLY_A` | `0` | the user-observed **Slugma/Winona** bug: `box_counter_pid` skips its MOVE branch and matches on TYPE only, so a boxed counter hunted for its move is missed. Exists for (P4)'s ARM A. ‼ Exercised against the REAL function by `repro_box_counter_move_test.py`, so the hook cannot rot |

## C. TUNING KNOBS (not results)
| flag | default | what it tunes |
|---|---|---|
| `POKEBOT_FAINT_GIVEUP_LIMIT` | `20` | how many faints before a run gives up |
| `POKEBOT_FODDER_RULE` | `xp_rate` | which rule picks fodder |
| `POKEBOT_CONNECTION_STEP` | `0` | ‼ **rationale not yet transcribed.** Documented here only so the linter passes; read the code before assuming what it does |

---

## ‼ HONESTY NOTE ON THIS FILE
Rows in section A marked *"not transcribed here yet"* are **deliberately blank rather than
guessed**. This project's north star includes producing training material for a future agent, and
an invented measurement is worse than an absent one. Fill them from `07-CHANGELOG` /
`08-MISTAKES` when someone next touches the relevant area.
