# 2026-10-01 — design v2 step 14, T1 (`x4_headless.py --arms`): BUILD SPEC + PREDICTIONS (filed BEFORE any code)

⛔ **THE CAVEAT IS THE HEADLINE.** T1 is a TOOL change (`tools/story-dev/x4_headless.py`; no production code). It makes
a per-lane A/B possible and refuses to run one that is contaminated. It proves nothing about the bot. It blocks tonight's
batch (USER RULING 28); T2-T4 block only the grading.

**Parent:** `2026-10-01-batch14-DESIGN.md` §3 T1 (its definition), §4 (the stop rules T1 automates).

## Step 0: what the author read (FILE:LINE, 2026-10-01)

- `x4_headless.py` in full.
  - **The loop is NOT in a try/finally:** only `KeyboardInterrupt` is caught (:1050-1098).
  - **Lanes are stopped only after the loop** (:1100-1101), and **the logs are copied only after that** (:1112).
  - `check_headers` reads 8 KiB of each NEW log once its header is complete (:667-698).
  - `resummarise` carries forward a fixed key list (:906-909) and derives the slot from the tag (`int(tag.lstrip("H"))`,
    :891).
  - `ensure_lane_profile` rewrites `story.yml` with `character_name: {lane_tag(slot)}` (:548-556).
- `repro_x4_headless.py`: `check(label, cond)` rows. It drives the REAL `lane_summary` for wiring (:445-498), calls
  `x4.lane_env()` and `x4.lane_profile_name(i)` with today's signatures (:72, :106), and pins `BUILD_NAME == "custom"`
  (:385).
- **The run header's `build:` line** holds the first 12 hex digits of HEAD (`debug_logger.py:128-170`, e.g.
  `build:         21b420ce281c on branch main`), and `env-all:` is a Python dict repr (`:262-266`).
- **Non-`POKEBOT_` variables the sandbox reads** (a grep of `environ.get` / `environ[` / `getenv` with a literal name,
  plus the names read through constants): `TEACH_TRACE`, `TEACH_MISS_WINDOW`, `TEACH_CANCEL_FORGET`, `STORY_TALK_DEBUG`,
  `KI15_TRACE`, `FW_TRACE`, `CAPTURE_FORCE`, and `CH21_CAPTURE_*` (`sootopolis.py:2188`). `SAVE_POST_RIVAL` is already
  popped (:641). Every name read through a constant is `POKEBOT_*` (`_TURBO_ENV = "POKEBOT_STORY_DEBUG_TURBO"`,
  `story_mode.py:7025`, defaults ON when unset, as in the user's GUI batches).
- **The monitor's texts, traced:**
  - `dex catch #N (joins the party)` prints only with `open_fence` (`story_mode.py:2102-2103`, :2171-2174).
  - `consume the HM/counter runway` prints only without `open_fence` (:2104-2110).
  - `a training grind is in progress` prints only without `lift_training` (:2135-2141).
  - `party is not at full strength` prints only without `lift_health` (:2149-2158).
  - The ONE production caller of `decide_dex_catch` wires all three to the run's flags (:2730-2772).
  - The eight B-only markers were traced by the review (`b14_design_review.md`, angle `markers`).

## The build (exactly what T1 adds)

### 1. The arms file, `tools/story-dev/arms/batch14.json` (committed)

```
{"arms": {"A": {<18 vars>}, "B": {<18 vars>}},
 "monitor": {"A": {"forbid": [...], "expect": [...]},
             "B": {"forbid": [...], "require": {"<substr>": <seconds>}, "expect": [...]}}}
```
- The 18 variables are the DESIGN's §1 table, verbatim. A gate row pins the file to it.
- **Monitor entries:** a `forbid` entry is a string, or a list of strings that must ALL appear on ONE line. `require`
  aborts the batch if a lane has not shown the substring that many seconds after its first spawn. `expect` is only
  recorded (its first-seen time), never enforced: the smoke run's positive controls.
- **A:**
  - `forbid` = `[KEYBATTLE]`, `[KIT-BUY]`, `[DBLITEM]`, `why=topoff`, ` rare=`, `[DEXCATCH-NOBAIL]`,
    `[CATCH] trainee`, `[CATCH] loss-filed`, and `["dex catch #", "(joins the party)"]`;
  - `expect` = `consume the HM/counter runway`.
- **B:**
  - `forbid` = `consume the HM/counter runway`, `a training grind is in progress`, `party is not at full strength`;
  - `require` = ` rare=` and `[KEYBATTLE]` at 3600 s;
  - `expect` = ` rare=`, `[KEYBATTLE]`, `why=topoff`, `[KIT-BUY]`.

### 2. Validation (pure; refused at start, before any lane spawns)

**Refused:**
- fewer than 2 arms; an empty arm; a non-string value; arms with different key sets; two identical arms;
- a key that does not start with `POKEBOT_`;
- a key containing `FAULT`, matching `_ARM\d*$` or `_A$`, or `POKEBOT_RNG_DECORRELATION_FRAMES`;
- a key that does not appear literally in the build's source (`modules/` + `plugins/` `*.py`);
- N not divisible by the number of arms, or any within-arm position whose STARTER differs between arms;
- a malformed `monitor`;
- `--arms` without `--profile-tag`, or with `--build custom`;
- a tag that is empty, starts with `P`/`p`, or contains anything outside `[A-Za-z0-9_-]`;
- any lane profile that already exists under the tag.

### 3. Lanes

- **Arm assignment:** arm k takes slots [k·N/K, (k+1)·N/K).
- **In-game name** = `lane_tag(slot mod N/K)`, so slot i of every arm shares one name.
- **Profile** = `endless-<tag>-H{slot+1}-<starter>`, created fresh.
- **`lane_env(lane=None)`:** with no arm it is unchanged. With an arm, it is `os.environ` minus every `POKEBOT_*`
  variable and the D6 names (`TEACH_TRACE`, `TEACH_MISS_WINDOW`, `TEACH_CANCEL_FORGET`, `STORY_TALK_DEBUG`, `KI15_TRACE`,
  `FW_TRACE`, `CAPTURE_FORCE`, `SAVE_POST_RIVAL`, `CH21_CAPTURE_*`), plus today's three settings and the arm's dict. The
  names it stripped are recorded.

### 4. Live checks (each aborts the batch whatever `--on-bad-header` says)

- **(b) The header check.** Once a header is complete, `env-all` must `ast.literal_eval` to a dict EQUAL to the lane's
  arm, and `build:` must equal HEAD's first 12 digits at the start. Missing, unparseable, a non-dict or different ⇒
  abort, with `ARM HEADER` and the differing keys named.
- **(f) The freeze watch, every 60 s.** HEAD and `git status --porcelain --untracked-files=all -- <build root>
  tools/story-dev/x4_headless.py` must equal the start snapshot. Any change aborts with `FREEZE BROKEN`.
- **(g) The monitor, every tick.** Each lane's logs (mtime ≥ start) are read incrementally, whole lines only, matched by
  plain substring.
  - A `forbid` hit aborts with `ARM LEAK`, naming the lane, the log and the line.
  - A `require` miss at its deadline aborts with `VACUITY`.
  - First-seen times for `require` and `expect` go into the summary.

### 5. Records and robustness

- **`<stamp>/ARMS.json` is written BEFORE the first spawn.** It holds: the file verbatim and its sha256; per lane the
  arm, starter, name and profile; the stripped variables; sha256 of the build's `profiles/*.yml` and
  `customcatchfilters.py`; the full porcelain; the freeze snapshot; the bound; the start time.
- **The loop runs inside try/finally,** so the lanes are always stopped. Any exception becomes an abort reason.
- **The console is teed** to `<stamp>/x4h.txt`.
- **Each spawn records** its start time, end time, exit code and commit. At the deadline, each lane records
  `alive_at_deadline` and its open log (the CUT run).
- **The summary carries the arm** (`lane_summary`), and `resummarise` carries forward `arm`, `spawns`,
  `alive_at_deadline`, `cut_log` and `monitor`.
- The INDEX row shows `N (A/B)`, and `--status` prints each lane's arm.
- **The dirty check behind the "unattributable" warning** is scoped to the build root and the runner in an `--arms`
  batch. Without `--arms` it is unchanged.

### 6. Fault arm (runner-side; registered in `29`)

`X4H_FAULT_ENVLEAK=1` adds `POKEBOT_X4H_LEAK=1` to slot 0's environment AFTER `lane_env` builds it. It simulates an
inherited leak that the strip missed, so the live header check must abort.

## PREDICTIONS

| # | Run | Prediction | Falsified by |
|---|---|---|---|
| T1-1 | `repro_x4_headless.py` | every new row in section F passes, every old row still passes, and the full suite (`run_gates.py`) passes | any FAIL |
| T1-2 | an adversarial mutant pass on the new code | every mutant of a refusal, the header equality, fail-closed, the strip, block assignment, name pairing, the freeze compare, the monitor's forbid / require / multi-substring logic and the carry-forward reddens at least one row | a surviving mutant that is not equivalent (a row gets added) |
| T1-3 | the LIVE fault: `X4H_FAULT_ENVLEAK=1`, 8 lanes (4 A + 4 B), `--minutes 5`, tag `s14fault` (main checkout, `--build sandbox`) | ABORTS with `ARM HEADER`, naming H1 and `POKEBOT_X4H_LEAK`, before H1's FIRST run leaves its intro (within about 90 s of H1's spawn). Every lane is stopped, and `ARMS.json` exists | no abort; an abort for another reason; any lane process still running afterwards |
| T1-4 | the SMOKE (USER RULING 28): 16 lanes, `--minutes 15`, the real arms file, tag `s14smoke` | the time bound ends it (verdict OK) with 0 header violations, 0 `forbid` hits and a freeze unchanged. Every lane's every header equals its arm. All 8 B lanes show ` rare=` and `[KEYBATTLE]`. At least 6 of 8 A lanes show the runway text, and at least 6 of 8 B lanes show `why=topoff` and `[KIT-BUY]`. Median frames/s per lane is 550-700 | any violation or hit; a B lane missing ` rare=` or `[KEYBATTLE]`; fewer than 6 of 8 on either positive control; fps outside the band (a THROUGHPUT finding: the expected n is restated, and it does not stop the batch) |

The batch starts tonight (tag `s14`, 16 lanes, `--minutes 780`) only if T1-1, T1-3 and T1-4 hold, T1-2's survivors
are closed, and T1 is merged to `main` at the commit the batch runs (USER RULING 28).

## GRADED — the build phase (2026-10-01; the live arms T1-3 and T1-4 follow)

- **T1-1 HELD:** the gate passes (sections F-H, 246 rows), the existing rows unchanged, and the full suite passes
  (`run_gates.py`: all 137 enforcing gates).
- **T1-2 FAILED AS FILED:** the first independent mutant pass killed only 103 of 155 mutants. 44 real gaps survived,
  almost all WIRING: F14 checked `_run_batch` by its source SHAPE, and that passed with the arm abort gated on
  `--on-bad-header`, the monitor or the freeze off, and the lanes built without their arm. The gate's own typo row also
  caught a real bug on its first run: the "key appears in the source" test was a SUBSTRING test (`…KITTOPOF` passed
  inside `…KITTOPOFF`); it now matches whole tokens.
- **Folded:**
  - section G, which DRIVES the real `_run_batch` with a fake Popen (asserted in place), a fake clock, fake git and a
    bot-less `BUILD_ROOT`;
  - the runtime review's twelve findings R1-R12: lost lanes are DEGRADED, never VACUITY; cut runs are recorded on every
    exit; the do-not-commit banner; a kill-on-close job, measured on a real sleeper; a dirty start is refused; and more.
- **A SECOND independent pass** (236 mutants) re-applied every earlier mutant: the only survivors are the six the first
  pass called equivalent. It killed 48 of 81 mutants of the new fixes, and its section H closes the 31 real gaps (the
  job assignment, the tee and the provisional summary could each be deleted with the gate green). What remains is 8
  EQUIVALENT mutants, each argued in the evidence.
- **One launch decision measured:**
  - This session's processes sit in a kill-on-close job, so a background task would die with the session and take
    the batch with it.
  - A WMI-created `python.exe` is in no job and its parent is `WmiPrvSE`.
  - ⇒ the night run is launched through WMI (`tools/story-dev/launch_x4h_detached.ps1 -Tag <tag> -Minutes <m>`, run
    from the MAIN checkout; the recipe is in `04`).

## GRADED — the live arms (2026-10-01; evidence `tools/story-dev/evidence/2026-10-01-batch14-T1-LIVE.txt`)

- **T1-3 HELD (5 of 5):** `x4-runs/20261001-090513`, 8 lanes, tag `s14fault`.
  - The batch aborted in 0.8 min with `ARM HEADER` on H1, naming `POKEBOT_X4H_LEAK`.
  - In the same tick the other seven lanes' headers EQUALLED their arms.
  - Every lane stopped (`in_job` True, `stopped_by` x4h), and no lane process remained afterwards.
- **T1-4: 9 of 10 AS FILED:** `x4-runs/20261001-090649`, 16 lanes, 15.1 min. It was launched DETACHED through WMI, the
  exact night path.
  - Verdict OK, 0 violations; all 16 `env-all` headers equal their arms.
  - Every B lane showed ` rare=` (17-90 s) and `[KEYBATTLE]` (53-90 s).
  - 7 of 8 A lanes showed the runway text, the live proof that an explicit `"0"` is OFF.
  - 8 of 8 B lanes showed `why=topoff` and `[KIT-BUY]`.
  - The freeze watch answered every poll.
  - ⛔ **FAILED AS FILED: throughput.** The per-lane median was 862 frames/s, ABOVE the 550-700 band. This was the first
    15 minutes, which are early game. It is not a stop: the batch measures its own throughput, and the expected n is
    restated from that, never from this window. (The grader assumed sequential spawns for its offsets; about 10% on one
    lane, immaterial.)
- **⇒ T1 is DONE.** The batch is SCHEDULED (task `Pokebot-Batch14`, 9:00 PM LA tonight; `04` has the details and the
  freeze rules).
