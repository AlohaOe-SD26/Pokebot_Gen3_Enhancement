# 2026-09-29 — USER RULING 25, design v2 step 8 (RC: the cap of 3 + the rare exemption): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code is committed and before any graded arm. Branch `wt/r25cap`, cut from `main` `0f6991c1`.
> Spec: `ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md` §2 step 8 (a NOTE). Ruling: `06`, USER RULING 25 (the cap
> of 3; no cap for rare, shiny and legendary). A three-angle recon (code audit, adversarial, live discriminator) came
> first; its output is a NOTE, and each load-bearing claim below was re-read at file:line. The M0 below was measured
> on the current code before this file was written.

## WHAT THE RECON CHANGED IN THE SPEC

- **Every `story_mode.py` line the spec cites is stale.** Two of them now point at OTHER gates: `:1982` is the armed
  hunt and `:1990` is the walking hunt. A builder following the numbers would delete those gates. Current lines:
  - `decide_dex_catch` `:1858`; its attempts gate `:2028`; the throws gate `:2036`; the reserve `:2013`;
  - `_should_catch` `:2530`, whose fence call is at `:2567`;
  - the attempts increment `:3897`.
- **The silent-failure trap (the recon RAN it).** `_should_catch` holds an `EncounterInfo`, not a `Pokemon`.
  `rarity.encounter_rarity(EncounterInfo)` returns rare=False with the note `adapter_error:AttributeError` and never
  raises. So the spec's `rarity_fn(enc)` would ship the exemption SILENTLY INERT, and its stub-based K rows cannot see
  it. ⇒ The adapter passes `getattr(encounter, "pokemon", None)`, pinned by an AST row and by a row with the REAL
  `encounter_rarity`. The live A/B has a fault arm that passes the wrapper.
- **K6 "walking still refuses" is wrong on the fence's full-party base.** The walking gate fires only with
  `open_fence` and a party below 6. The row uses party 5 with `open_fence`.
- **K3 must pin CAP off.** With CAP on, attempts 2 admits whatever `rare` says, and the RAREUNGATED arm would be
  vacuous.
- **The OFF cap is the constant `DEX_CATCH_MAX_ATTEMPTS`,** not a literal 2.
- **"Pure-only" was a choice, not a necessity.** A ~15-line harness-only lever (`STORYRESUME_PRESET_ATTEMPTS`,
  shaped like `STORYRESUME_PRESET_DEFEATS`) presets the attempts count, so the cap and the exemption can be A/B'd on a
  live encounter. The throws half has no live discriminator: the only rare species above 10 expected throws have
  been met only as 3 Wailords in 4,896 logs. That half stays pure.
- **"In battle: unchanged" understates the change, and this is stated, not fixed.** The in-battle reserve bail needs
  an escape. A TRAPPED dex catch throws into the reserve. Wailord (rare, always knows Whirlpool) and Magneton (Magnet
  Pull against a Steel lead) are rare trappers.
  - Today the cap of 2 bounds how often a run can enter that path for one species. With `POKEBOT_R25_RARE` it is
    bounded only by the fence's spare > 10 at entry, the ball supply and the whiteout budget.
  - This is recorded like RULING 25's accepted whiteouts: diagnosed, not re-litigated. Step 14 counts it.

## THE CHANGE (planned)

- **Constant:** `R25_MAX_ATTEMPTS = 3`.
- **Two module-level PURE helpers,** a deliberate split of the spec's single `r25_catch_inputs`, so that the verdict
  is computed ONCE and can be logged without a second call site:
  - `r25_rarity_verdict(rare_on, rarity_fn, pokemon)` returns None when RARE is off (no read at all). Otherwise it
    returns the verdict, and a raising `rarity_fn` gives a not-rare verdict with a `helper_error` note.
  - `r25_catch_inputs(cap_on, verdict)` returns `{"max_attempts": 3 if cap_on else DEX_CATCH_MAX_ATTEMPTS, "rare": verdict.rare}`.
- **`decide_dex_catch`:**
  - gains `max_attempts=DEX_CATCH_MAX_ATTEMPTS` and `rare=False`;
  - the attempts gate becomes `if not rare and attempts >= max_attempts`;
  - the throws gate gains `and not rare`, keeping the NORATE substring contiguous;
  - the reserve (`:2013`) is NOT touched (Q8 open).
- **`_should_catch`:**
  - reads the verdict for `getattr(encounter, "pokemon", None)` and stashes it on `self._r25_last_verdict`;
  - appends `**r25_catch_inputs(...)` after the `lift_training` line (that line is unedited; gate anchors).
  - Fault arm `POKEBOT_R25_FAULT_RAREWRAPPER` passes the wrapper instead.
- **Flags `POKEBOT_R25_CAP` and `POKEBOT_R25_RARE`,** read per run in `reset_per_run_state`, default OFF.
- **Flag-ON logging only:** ` rare=<reasons> tier=<tier> note=<note>` is appended to `[DEXFENCE]`, `[DEXCATCH] attempt`
  and `[CATCH] start` (dex/team kinds). Every OFF line stays byte-identical. The `_r20_catch_start` call site and
  signature are untouched (gate W and the oversurvival stub).
- **The harness lever `STORYRESUME_PRESET_ATTEMPTS`** (harness only; re-applied after every reset; prints an
  `applied:` line).
- **NEW gate `probe_r25_catch_cap.py`:**
  - K1-K10 through the REAL helpers into the REAL `decide_dex_catch`;
  - A-rows: the AST wiring pin on `.pokemon`, OFF gives the old inputs, the default `max_attempts`, and the log suffix;
  - source mutants RAREEARLY, RAREALL, RAREUNGATED, CAP2, NOATTEMPTS, NOTHROWS and WRAPPER, each red on its named
    rows, plus a negative arm.
- **Rows in `29-DISABLED-FEATURES-REGISTRY.md`:** `POKEBOT_R25_CAP`, `POKEBOT_R25_RARE`,
  `POKEBOT_R25_FAULT_RAREWRAPPER`.

## THE M0 (measured before this file; `tools/story-dev/evidence/2026-09-29-r25cap-M0.txt`)

- **The trajectory is the graded RULING 24 step 4 P-ON arm on current code:**
  - `storyresume` on `r20_badge1_party1_gym.ss1` (50af0f5c), `--set-balls 60 --frames 76000`, `random.seed(1)`;
  - `POKEBOT_R20_OPENFENCE=1`, `POKEBOT_R24_OVERSURVIVAL=1`, `STORYRESUME_PRESET_DEFEATS='24,7=3'`.
- **Run twice; the two runs are IDENTICAL on 90 of 90 tracked lines** (after filtering one-frame `(0,0)`/`(255,255)`
  warp map reads; run 1 alone logged a `(255,255)` read at f213839, after the discriminator).
- **The two discriminating encounters** (debug-log frames):
  - **Zubat (#41, ordinary):** `f200242 [DEXFENCE] CATCH #41 Zubat`, then `[DEXCATCH] attempt #1`, at party 1/6.
  - **Abra (#63), FEMALE** (stdout: "Abra♀ encountered at Granite Cave Steven's Room"): `f212439 [DEXFENCE] CATCH
    #63 Abra`, then `[DEXCATCH] attempt #1`, `[CATCH] start ... attempt=1 ... party=4/6`.
- **The female Abra is variant-rare:** 10% × 63/256 = 2.46% (the step 7 table), tier ULTRA.

## PREDICTIONS (graded on the debug-log lines named; every arm is the M0 command plus the listed env)

Each arm is ONE run, except the controls, which run TWICE (KI-112). A single-run arm is attributed only if it matches
M0 up to the named frame and diverges AT the gate's own line there.

- **R25-OFF ×2 (new code, no R25 env, no preset):** identical to M0 on all 90 tracked lines. No ` rare=` suffix
  anywhere. *Falsifier:* any difference that reproduces in both runs.
- **R25-A (`STORYRESUME_PRESET_ATTEMPTS='63=2'`, flags OFF):**
  - an `[HARNESS] STORYRESUME_PRESET_ATTEMPTS applied` line in stdout;
  - M0 until f212439, where `[DEXFENCE] skip #63 Abra — already attempted #63 2x this run`;
  - no `[DEXCATCH]` for #63 at that frame.
- **R25-LEVERTYPO (`STORYRESUME_PRESET_ATTEMPT='63=2'`, misspelled, flags OFF):** no `applied` line; the Abra is
  admitted as `attempt #1` exactly as in M0. It proves the lever, not something else, makes R25-A refuse.
- **R25-B (preset 63=2, `POKEBOT_R25_CAP=1`):** admitted, `[DEXCATCH] attempt #3 on Abra (#63) -> party`. No
  ` rare=` suffix (RARE off).
- **R25-C (preset 63=3, CAP):** `skip #63 Abra — already attempted #63 3x this run`.
- **R25-D (preset 63=3, CAP + `POKEBOT_R25_RARE=1`):**
  - admitted, `[DEXCATCH] attempt #4 on Abra (#63) -> party rare=variant tier=ULTRA note=-`;
  - `[CATCH] start ... attempt=4 ... rare=variant tier=ULTRA note=-`;
  - the `[DEXFENCE] CATCH #63 Abra` line carries the same suffix.
- **R25-E (preset 63=2, RARE only):** admitted as `attempt #3`, with `rare=variant tier=ULTRA`. R25-A against R25-E
  isolates the exemption from the cap.
- **R25-F, the fault arm (R25-D + `POKEBOT_R25_FAULT_RAREWRAPPER=1`):**
  - refused like R25-C: `skip #63 Abra — already attempted #63 3x this run`;
  - its `[DEXFENCE]` suffix reads `rare=- tier=- note=adapter_error:AttributeError`.
  - This is the silent-failure bug, visible live.
- **The ordinary controls (preset `41=2`; the arms diverge at the Zubat, f200242, so `--frames 62000`):**
  - **R25-ZOFF (flags OFF):** `skip #41 Zubat — already attempted #41 2x this run`.
  - **R25-ZCAP (CAP):** admitted as `attempt #3`.
  - **R25-ZRARE (RARE only):** refused `already attempted #41 2x`, with the suffix `rare=- tier=- note=-`. This is K7,
    live: an ordinary species gets no exemption.
- **The pure gate `probe_r25_catch_cap.py`:**
  - every K row holds;
  - every mutant turns its named rows red;
  - the WRAPPER mutant turns the AST row and the real-rarity row red.
- **The full suite stays green.** The existing fence rows that assert "already attempted" at
  `DEX_CATCH_MAX_ATTEMPTS` (`probe_dex_catch_fence.py` C13, `probe_dex_catch_anytime.py` A6,
  `probe_dex_open_fence.py` O8) still hold, because the defaults are unchanged.

## WHAT THIS WILL NOT SHOW

- How often the cap or the exemption matters in a real run (step 14's batch). The preset stands for attempts that did
  not happen on this trajectory: this is ONE trajectory, replayed, testing the wiring on a live encounter.
- The throws half live (pure only; see above).
- Anything about a rare species other than a female Abra, or about Q8 (the reserve).
