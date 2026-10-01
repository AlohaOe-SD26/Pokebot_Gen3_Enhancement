# 2026-10-01 — design v2 step 14 (the Phase 3 batch A/B): recon angle `machinery`, verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (a subagent's return, read-only recon; workflow `step14-batch-recon`). Every load-bearing claim is verified by the author before the design relies on it.

# Step 14 batch machinery: per-lane flags or two batches

This is a note, not a source of truth. I did not write any files, run any git commands that change state, or start an emulator or batch.

## Bottom line

- **A 4-lane concurrent A/B cannot avoid confounding arm with starter.** Any fixed 2+2 split of P1 torchic, P2 mudkip, P3 treecko and P4 random puts each pinned starter in only one arm. The step 14 metric is key-battle win rate, including leaders. A Treecko lane stalls at Wattson in 11 of 14 runs (`x4_headless.py:116-118`), so a fixed split would move one arm's leader win rate whatever the flags do.
- **My choice is option 1a (the user decides; the full list is in the comparison section):**
  - 8 lanes on the existing headless runner `tools/story-dev/x4_headless.py`.
  - Arm A takes one lane of each starter type and arm B takes the other.
  - A per-lane arms file is passed explicitly as `--arms <file>`. Without it, the runner behaves as it does today.
- **If the user wants to watch the tile view,** the fallback is option 1b: the GUI's 4 lanes with a crossover (the two lane pairs swap arms at the midpoint).
- **Two sequential batches is the zero-code option.** It is starter-balanced, but time-of-day, machine load and code changes between the batches are all confounded with the arm.
- **The "twice the machine time" framing in the handoff is misleading.** At 4 lanes, each arm gets 2 lane-hours per wall-clock hour in both designs:
  - concurrent 4 lanes for 14 h gives about 28 lane-hours per arm;
  - two sequential batches of 14 h give about 56 lane-hours per arm in 28 h.
  
  The difference is sample size, not efficiency. Concurrency only saves wall time if it adds lanes.

## Verified (file:line)

**Lane spawn (GUI)**
- Every lane copies the dashboard's environment with `env = dict(os.environ)`, adds only `PYTHONUTF8` and `PYTHONUNBUFFERED`, and passes it to `Popen(env=env)` (`sandbox-pokebot/modules/endless_x4.py:173-196`).
- `poll()` respawns a dead lane through the same `_spawn` (`:203-227`), up to `max_restarts=20` (`:125`). A parked batch is never respawned (`:208-209`).
- **Lane table:** `LANE_STARTERS = ("torchic","mudkip","treecko","random")` (`:53`). The profile name is `endless-P{n}-{starter}` (`:58-67`). `story.yml` is rewritten on every launch, with `character_name` set to the lane tag (`:70-95`; rationale at 06:600-607).
- **The random lane re-rolls its starter every run** with `random.choice`, and prints `STARTER: config=… -> playing …` (`modules/story/early_game.py:1035-1044`).

**How the dashboard starts a batch**
- Entry point is `start_endless_x4` (`modules/gui/dashboard_gui.py:3141-3211`, menu action `ACTION_X4_TOGGLE` at `:4100`).
- The lane count is hard-coded: `lanes = 4` at `:3161`, the painter uses `batch.lanes[:4]` at `:3060`, and the mosaic is fixed at 2×2 (`modules/tile_mosaic.py:107`). **Eight GUI lanes would therefore not be a small change.**
- The confirmation dialog's lane roster is built at `:3162-3179`.

**Where the environment comes from**
- `install_sandbox.py` wraps `install.main`, which launches `pokebot.py` with `subprocess.run` and no `env=` (`install.py:506`). So today a GUI batch's flags can only come from the shell that launched the installer.
- No sandbox code writes to `os.environ`. I grepped for assignment, `pop`, `update`, `setdefault` and `clear`, and found nothing.

**How the step-14 flags are read**
- All of them are read from the environment inside the child process:
  - per run: `story_mode.py:2432-2459`;
  - per call: `:825`, `:880`, `higher_level_actions.py:526,533`, `stock_topoff.py:312,780` and `dmgaudit.py:31`.
- So an environment set at spawn time stays fixed for the life of the process, and every run of a lane belongs to one arm.
- `"0"` reads as OFF for every flag, either through `== "1"` or through `VALID_FLAG_VALUES = ("", "0", "observe", "1")` (`stock_topoff.py:75,92-95`).

**Each run declares its own arm**
- `debug_logger.py:260-266` writes an `env-all:` line in every run header listing every `POKEBOT_*` variable.
- `POKEBOT_ARM` does not appear anywhere in the code (grep found nothing), so it is free to use as a label.
- batch0927's logs predate this line (their headers show only `env:` at line 12).

**The headless runner already supports N lanes**
- Its lane profiles are `endless-H{n}`, kept separate on purpose so that a GUI batch and a headless batch can run on the same machine at once (`x4_headless.py:135-142`).
- Starters cycle through the same 4-entry table (`:111-128`).
- `--minutes` stops the batch automatically.
- It records the commit each lane loaded at every spawn and flags a batch that ran more than one build (`:360-410`, `:588-591`).
- It checks every new run header (`check_headers` at `:667`).
- Its own comment says 8 lanes are comfortable: "four lanes measured ~4 cores of a 16C/32T machine" (`:954-956`). `nproc` on this machine returns 32.
- **Its default is `--build custom` (`:957`), and custom-pokebot contains no `POKEBOT_R23`–`R27` code and no `env-all` line.** Running with the default would make both arms identical and leave no trace of it. `--build sandbox` must be forced.
- `--max-restarts` defaults to 3 (`:972`).

**Past A/B batches**
- **#24-maintain** was run as two sequential headless batches through `Run-Maintain-AB-Batch.bat`:
  - 32 lanes × 310 min, then 32 × 120 min per arm (07:27288-27290, :27424, :27631-27634);
  - the script uses SETLOCAL and an explicit `=0` (bat :38, :123, :137-145);
  - a default flip had nearly made its control arm a second ON arm (08:16867-16883);
  - the arms were "verified separated" from behaviour counts before anything was read;
  - 08:17141 records "never pool two batches without checking their arm/flag declarations".
- **xp_rate vs legacy** was a sequential comparison of GUI overnights (07:4975-5007).
- **Phase 3 itself was planned as "a concurrent A/B"** (03:128).

**The analysis tools**
- `battle_log.scan_logs` only globs `endless-P*` (`battle_log.py:741`).
- Its date window is a whole day (`:748-750`), and its docstring warns about "two arms sharing a day" (`:736-737`).
- `--lanes` requires `--since`/`--until` (`:810-811`).
- `--logs` can be repeated and accepts absolute globs (`:802`, `:813-815`).
- ⇒ The claim at 06:8807 that `--lanes` "serves either" holds only for GUI lanes. For headless lanes, use the batch stamp or one `--logs` glob per lane directory.

**Load drift within one batch**
- In batch0927, runs before about 10:00 ran at roughly 1,030-1,100 fps; later runs ran at 635-700 fps (`2026-09-27-batch0927-FINAL.md:478`).
- The cause was not established.

**Wall-clock reads exist**
- `watchdog.py:216-217` and `:423`, and `state_cache.py:25-41`. These are KI-112's unmeasured cause candidates (05:3157-3160).
- One KI-112 event fits a time-of-day input (05:3182-3185).

## The confound and how to split lanes

- **Four lanes, fixed 2+2: invalid.**
- **Four lanes, crossover:**
  - First half: A = {P1, P3}, B = {P2, P4}. Second half: A = {P2, P4}, B = {P1, P3}.
  - Every starter runs in each arm, and both arms always run at the same time.
  - The cost is one user action at about 7 h: Park & Collect, flip the phase, restart.
  - The roughly 4 runs in progress at the swap are cut short. That costs run-level metrics only; battle-level metrics keep those battles.
  - The analysis must select logs by the `POKEBOT_ARM` in each header, because a lane changes arm halfway (rule 3: select by identity, not by lane position).
- **Eight headless lanes, which is what I would choose:**
  - A = H1-H4 and B = H5-H8, or any split that gives each arm exactly one torchic, one mudkip, one treecko and one random lane.
  - ⛔ **Trap: an odd/even slot split is fully confounded.** Because the starter table repeats every 4 slots, it gives {torchic, treecko} against {mudkip, random}. The loader should refuse any split whose arms have different starter multisets.
- **Rejected:**
  - All-random starters: this needs a per-lane starter override and gives up the rule that P1 is always Torchic.
  - Switching arms every run inside a lane process: `StoryMode` is reused across runs (`story_mode.py:2464-2467`), and proving no state carries over would need byte-identical replay, which KI-112 rules out.
  - A zero-code hybrid (the GUI's 4 lanes as one arm and a 4-lane headless run as the other, each with its own shell environment): this confounds the runner with the arm.

## The smallest per-lane mechanism

**What the file looks like**
```json
{"label":"v2-step14",
 "arms":{"A":{...every key, explicit "0"...},"B":{...the same keys...}},
 "lanes":{"H1":"A",...,"H8":"B"}}
```
- Both arms include `POKEBOT_R25_DMGAUDIT="1"`, `POKEBOT_R25_WEAKEN="observe"` and `POKEBOT_R25_WEAKEN_CALC="0"`.
- OPENFENCE, TEAM6 and HUNTFIRST must be stated explicitly in both arms once "per the Phase 3 plan" is resolved. It is still unresolved in the spec (v2:695).

**Load it once, before any lane is prepared, and refuse to start on any error:**
- Every lane in the batch is assigned an arm, and every assigned arm is defined.
- **Every arm lists the same set of keys.** A control has to state its condition outright rather than rely on a default (08:16867-16883).
- Keys match `^POKEBOT_[A-Z0-9_]+$`. No key may contain `_FAULT_`, and `POKEBOT_ARM` is reserved.
- Every value is a string.
- Every arm has the same multiset of starters.

**How the environment is built**
- `lane_env(lane)` builds today's environment, then applies `update(overrides)` and sets `POKEBOT_ARM=<arm>`.
- The overrides are stored on the `Lane` object, so a respawn (`x4_headless.py:1088`) uses them as loaded and never re-reads the file.
- The parent's own `os.environ` is never modified.

**How the arms are recorded**
- The MANIFEST gets an arm per lane, the file's sha256, and any inherited `POKEBOT_*` variables (shared by both arms). An inherited `_FAULT_` variable refuses the batch.
- Each lane's stdout gets a first line naming its arm.
- `check_headers` also asserts `POKEBOT_ARM=<lane's arm>` in every run's `env-all:` line and aborts loudly on a mismatch.

**The GUI version (option 1b) uses the same loader, with these differences:**
- A menu click has no command-line argument, so the file sits at a fixed path, `profiles/endless-x4-arms.json`.
- The file carries an `expires` date, so a forgotten file does not silently turn half of next week's ordinary batch into arm B.
- It carries a `phase` field for the crossover.
- The arms are shown in the roster dialog (`dashboard_gui.py:3162`).
- `x4_logs.py:210` gets an `arm=` field.
- This one is a sandbox change, so it needs SANDBOX-NOTES and DIVERGENCE-LOG entries. Option 1a stays in `tools/`, and the GUI batch path is untouched.

**Failure modes**

| Failure | How it is handled |
|---|---|
| A stale arms file leaks into a later batch | Option 1a passes the file only by explicit argument; option 1b has the expiry date and shows the arms in the dialog |
| A typo in a flag name leaves that flag OFF in B with no error | Check the step-14 file against the registry in the gate, and run the post-batch behavioural separation check |
| A wrong value (`"true"` instead of `"1"`) reads as OFF | Same two checks |
| Shell variables leak into the lanes | Explicit keys override them; others are recorded in the MANIFEST |
| An implementation bug modifies the parent environment | Gate row |
| A respawn re-reads an edited file | Gate row |
| `--build custom` runs instead of sandbox | MANIFEST assertion |
| A merge to `main` mid-batch | Affects both arms equally, and x4_headless detects a mixed build; the GUI cannot detect it |
| Lanes in one arm crash more often | Report lane-hours, restarts and fps per arm; raise `--max-restarts` to 20 for a 14 h batch |

**How to prove it**

*1. Gate:* extend `repro_x4_headless.py`, which is already in `run_gates.py:505`. Rows:
- No file produces an environment dictionary exactly equal to today's.
- A/B values reach the right lanes.
- An inherited `CATCHHURT=1` becomes `"0"` in arm A.
- The parent environment is unchanged.
- An edit followed by a respawn leaves the lane's environment unchanged.
- One refusal row for each validation rule, including the odd/even split.

Each of these deliberately broken versions must turn its named row red:
- skip the update;
- re-read the file on respawn;
- modify `os.environ`;
- drop the key-set check;
- drop the starter check;
- set `POKEBOT_ARM` when no file is given.

*2. Live smoke run, about 8 minutes:* `--build sandbox --lanes 8 --minutes 8 --arms <file>`. It must show:
- each lane's first `env-all:` matches its arm exactly;
- MANIFEST shows `build sandbox` and SINGLE BUILD;
- per-lane fps at 8 lanes, compared with a 4-lane run;
- a run with no file whose `env-all:` equals the launching shell's.

*3. After the batch:* confirm the arms actually differed by behaviour before reading any result:
- `[KEYBATTLE]`, `[KIT-BUY]`, `[BALLS-BUY] why=topoff` and `[DBLITEM]` lines appear only in B;
- `[DMGAUDIT]` and `[WEAKEN]` lines appear in both.

I found where these tags are emitted, but **I have not confirmed that each one only appears when its flag is ON.** Check that first.

## Comparison

| Option | Lane-hours per arm | Wall time | Starters | Time, load and code changes | User actions | Code |
|---|---|---|---|---|---|---|
| 1a: headless, 8 lanes, concurrent | about 56, if per-lane fps holds | 14 h | balanced by construction | shared by both arms | one double-click (a SETLOCAL .bat like the Maintain one); stops itself | `tools/` only |
| 1b: GUI, 4 lanes, crossover | about 28 | 14 h | balanced over the batch | shared | start, midpoint swap, park | sandbox, plus header-based arm selection |
| 2: sequential, 4 lanes, 2 × 14 h | about 56 | 28 h | balanced within each arm | **confounded** | about 4 for the GUI, or 1 with a .bat around x4_headless | none |

- Option 2 also has to split arms by time, because the GUI's day window cannot separate two arms on the same day.

**Why 1a:**
- It removes the confounds option 2 cannot control.
- It gives the same per-arm sample as option 2 in half the wall time.
- It needs no user action partway through, and it leaves the user's GUI batch path unchanged.

**Its only real cost is the lost tile view.** Whether that is acceptable is the user's call; the headless runner was itself the user's request (2026-07-31) and has been used for two-arm runs before.

## Inferred or not yet measured

- **Per-lane throughput at 8 lanes.** At 32 headless lanes, lane H1 ran at about 478 fps (3,452,401 frames in 120.2 min; batch 20260912-104105). GUI batches averaged 722 fps (0927) and about 798 fps (0926: 180.5M frames over 62.8 lane-hours). The "about 2× in the same wall time" figure depends on this until the smoke run measures it.
- **Whether machine load changes bot behaviour.** This only matters through KI-112's wall-clock candidates, which have not been measured. Runs are already randomised per run (06:695-720), so KI-112 adds noise rather than bias, except through that load path.
- **Runs per arm.** At batch0927's rate of 1.6 lane-hours per run, about 17 runs per arm at 28 lane-hours and about 35 at 56. Arm B may differ. 06:5144-5160 says that at around 100 runs per arm a modest effect cannot be seen, so the per-arm sample is the binding constraint.
- **batch0927 is not a valid control for arm B.** It ran build `d21c0c3c`, before the KI-47 fix and the restock (FINAL:59). Arm A on the same commit as arm B is the valid baseline in either design.
