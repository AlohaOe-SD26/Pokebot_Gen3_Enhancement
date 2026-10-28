# E2 + O8 BUILD SPEC: per-game recording and torn-write resilience for the bot tuner (spec only, NOT built)

> **A note, not truth** (`00-READ-THIS-FIRST.md`). 2026-10-28, from four recon reports; every cited line re-read at
> `f9fffb68` (the clone's copies match, CRLF aside). Revised the same day after one adversarial critique round (22
> findings, 21 accepted in full, 1 in part: §7). Backlog E2 + O8, `#28-trainer-improvements` item 1. Paths are in
> `ai-agent/` unless given.

## 0. In plain English

- Today the tuner records a cycle's games only when the 12-hour cycle ends, so the 2026-10-17 shutdown lost 12
  finished games.
- **E2:** each finished game is saved within about 5 minutes of ending, and a restart scores finished games from disk.
  A crash then costs only the games still being played (about half a game per lane).
- **O8:** a half-written line goes to a `.bad` file instead of stopping the tuner. The state file keeps a backup, which
  is restored only when it is provably current; otherwise the tuner stops and asks. Files are forced onto the disk
  before they count as saved.
- **O8:** after 5 crashes in a row the tuner stops retrying and writes `ATTENTION.md`, and the watchdog toasts you.
  Today it retries every 10 minutes forever and tells no one. While crash-looping it still fetches pushed code, so a
  fix or a revert can reach it.
- **⚠ What changes for the ranking.** The ranking rules and the strategy-choice code do not change. But a cycle that
  crashes now adds the games that finished before the crash (today it adds none). Like any cycle with a scored game, it
  also uses up its tested inbox proposals and resets the failure count. That is item (1)'s stated aim ("record each
  game as it finishes"). ✅ The user confirmed it: USER RULING 48 (2026-10-28, U1 and U2 in §6).
- No stop is needed: it installs itself at the next cycle boundary.

## 1. The problem, measured

### 1a. A mid-cycle shutdown loses the whole cycle

- `run_cycle` blocks on one `subprocess.run` (`learner.py:739-740`). The batch runner copies lane logs into
  `batch/Lnn/debug-logs` only in its `finally`, after the lanes stop (`collect_logs`,
  `tools/story-dev/x4_headless.py:1134`, called at `:1849`). `finish_cycle` parses only those copies (`:752-754`,
  `scoring.py:142`) and appends once (`:759`).
- When the machine dies, that `finally` never runs. On restart, adopt (`:807-828`) finds no copied logs and records 0
  runs. `cmd_reparse` (`:1533`) and `cmd_ingest` (`:1512`) read only `batch/`, so they cannot recover it.
- **ai0031 (clone, read-only):** `learner.log:292` starts it at 02:30 AM; `:293-295` (04:00 PM) "adopt: scoring
  ai0031 … 0 runs logged, 0 scored"; `cycles.jsonl:31` `"runs": 0`. Its manifest lists 24 logs, all under
  `profiles/endless-ai0031-H*/debug-logs`, none under `batch/`. Per lane in ARMS lane order (H1-H12, from `raw.zip`'s
  `batch/ARMS.json`): 2,1,1,2,2,3,1,3,4,1,2,2. So **12 finished games** (not newest in their lane) were on disk and
  never scored. Since the 10-24 archive they exist only in `raw.zip`. Its inbox proposal 'ballstock-openfence-topup'
  (`learner.log:290`) stayed queued because the cycle scored nothing (`ok` False, `:771-776`).
- **A double count is also possible** (read from code, not reproduced). A death between the `runs.jsonl` append
  (`:759`) and `save_state` (`:777`) makes the next start adopt and append the same cycle again. This is the NORMAL
  path (copied logs). `finish_cycle` has no dedupe; `cmd_ingest` has one (`:1518`).

### 1b. A torn write stops the tuner, silently and forever

Read from code, not reproduced. Live data is clean today: all 3,366 `runs.jsonl` rows parse.

- **JSONL:** `load_jsonl` (`:168-171`) raises on the first bad line. `append_jsonl` (`:174-178`) never fsyncs, and a
  half line without `"\n"` glues onto the next row, losing a good row too. A torn `runs.jsonl` raises in `plan_cycle`
  (`:683`): no batch, 3 tries, then a misworded ATTENTION.
- **A torn `cycles.jsonl`** raises at `:779` (`report.write` reads it) after each batch. That is AFTER `save_state`
  (`:777`), so the cycle is already recorded, but consult, prune and the ops row are skipped. The raise reaches
  `loop()`'s `except` (`:1490`), so a scored cycle counts as `ok` False and `failures` rises (`:1497`). With the live
  `max_consecutive_failures` of 3, three such cycles write an ATTENTION saying "cycles in a row produced no scored
  runs" (`:1500`), which is false. On the adopt path (`:1439`, outside the per-cycle `try`) the same raise exits the
  process with 1 once; the next start finds the cycle recorded.
- **`state.json`:** `load_state` (`:187-190`) has no `try`; `save_state` (`:193-199`) never fsyncs and keeps no backup.
  A missing file silently returns a fresh state (51 cycles of history dropped). A torn one raises at `:1433`, outside
  the per-cycle `try` (`:1488-1495`); `loop()` is only `try/finally` (`:1432`, `:1507`), so Python exits 1 and
  `run_agent.ps1:17-18` restarts it every 600 s, forever. `failures` never moves; no traceback reaches `learner.log`.
- **`plan.json` (`:827`) and `ARMS.json` (`:761`)** are read with no `try`: the same crash loop through adopt.

## 2. Design

### 2a. E2: the game journal

**Format.** One line per finished game in `runs/<tag>/games.jsonl`: `{"journaled": "<TIME_FMT>", "rec": <record>}`.
`<record>` is exactly the `runs.jsonl` row today's `finish_cycle` would write for that log (`parse_batch` fields plus
`genome_id`).

**Writer and timing.** The learner (the batch runner and bot stay unchanged). `run_cycle` replaces `subprocess.run`
with `Popen` and a wait loop, `proc.wait(timeout=JOURNAL_POLL_S)` (300 s), calling `journal_games()` on each timeout.
Args, stdout, env and cwd stay as they are. Right after `Popen` returns, `_clear_crashes()` runs (§2c). The adopt wait
loop (`:821-825`) also calls `journal_games()` on each poll, so a restarted learner keeps journaling a still-running
batch.

**Nothing new may kill the batch.** Today nothing in the learner runs during the batch (`:739-740`). `subprocess.run`
kills its child and re-raises on any `BaseException`; the wait loop keeps that. But `journal_games` and
`_clear_crashes` are each wrapped in `try/except Exception`, and the `log()` call inside that handler sits in its own
`try`, because `log()` opens `learner.log` unguarded (`:144-146`; a full disk makes logging itself raise). So only
`KeyboardInterrupt`/`SystemExit`, or an exception from `proc.wait` itself, reaches the kill-and-reraise: the cases
where `subprocess.run` kills today. WHY: `proc.kill` stops only `x4_headless.py`, and its lanes keep running
(`run_agent.ps1:4-5`). The exception would land in `loop()`'s `except` (`:1490`), and the next cycle would start beside
orphaned lanes (`other_bots_running` does not count lanes).

**`journal_games(tag, batch, known)`:**
1. Read `batch/ARMS.json` behind a guard; unreadable → return 0.
2. Per lane, list `PROFILES/<lane.profile>/debug-logs/*.log` sorted by name. Keep logs with mtime ≥ ARMS `started` −
   6 s when it parses. This APPROXIMATES `collect_logs`, which keeps mtime ≥ `since` − 5 (`x4_headless.py:1150`;
   `since` = `time.time()` at `:1597`). `started` is that moment truncated to the second (`:1661`), so the journal's
   filter keeps a superset by up to about 2 s.
3. Candidates: every log except the newest (the logger closes the old log before opening the next,
   `sandbox-pokebot/modules/debug_logger.py:282-295`), not in `known`, unmodified for `JOURNAL_STABLE_S` = 120 s.
4. Build each record with `scoring.lane_record(..., last_in_lane=False)`, add `genome_id`, append one line (hardened
   append, §2b), add the key to `known`.

`known` is loaded from the journal after `repair_jsonl` in journal mode. That mode moves every bad line to `.bad`, with
no limit, and never writes ATTENTION or stops anything (§2b).

**`scoring.py` refactor (behavior-preserving).** Extract `:144-150` into `lane_record(meta, arms, i, lane, path,
last_in_lane, source, batch_dir)`; `parse_batch` loops over it and gains `lane_logs=None` (replacing the glob at
`:142`). `parse_log` and `PARSER_VERSION` are unchanged (a bump forces a full reparse at startup, `:1433`).

**`finish_cycle`:**
- **Normal case** (any `batch/L*/debug-logs/*.log` exists): today's block (`:752-756`) runs unchanged, then a
  read-only comparison logs `<tag>: game journal: N of N journaled games match the batch's records` (mismatches name
  the differing keys). Records are never altered.
- **Recovery case** (no copied logs; today: 0 runs): `recover_records()` runs `parse_batch(batch, tag,
  lane_logs=<profile logs, same filter>)`, so each lane's newest log is censored by today's rule (`scoring.py:146`).
  It then swaps in the journal's record for each matching `(lane, log)`, because the journal parsed the log while it
  was whole. It adds journal records whose log is gone (the journal alone if `ARMS.json` is unreadable).
  `batch_dir` stays `str(batch)`. The cycle row keeps `exit: "adopted"` and gains
  `"recovered": "<n> from lane profiles, <m> from the journal"`.
- **Unreadable `ARMS.json` (`:761`):** `meta` = `{}` and `created` = `[batch]` plus every `PROFILES/endless-<tag>-*`
  folder. The batch runner names lane profiles by `--profile-tag <tag>` (`:714`), and `_ours` still filters by exact
  name. Without the rebuild, `created` holds only `batch`, and archive and prune walk only `created` (`:849`,
  `:1111`), so the lane profiles would never be archived (a disk leak).
- **Both cases:** append only records whose `(source, batch, lane, log)` is not already in `runs.jsonl`; skip the
  `cycles.jsonl` row if this tag's exists (counts use all records). After `save_state`, delete `games.jsonl` (now
  redundant). `ok = usable > 0` is unchanged.

**INVARIANT (what changes and what does not).** Outside the O8 fault paths, the new code's records differ from today's
in exactly two cases:
- **(a) A batch with no copied logs.** Today it records nothing. The new code records the rows today's code would have
  recorded had the logs been copied at the crash, with the journal's whole parse used for any profile log cut by the
  crash. By today's own rules, those rows then enter the ranking (`plan_cycle`, `:683`, `:694`), `ok = usable > 0`
  moves the cycle's tested proposals to `done/` (`:771-776`), and `failures` resets (`:1497`). Under the new code
  ai0031 would have used 'ballstock-openfence-topup'. This is the ranking-data change in §0 (U1).
- **(b) A death between the append and the save.** The dedupe drops the second copy of the cycle's rows.

`brain.py`, `knowledge.py`, `plan_cycle`, `parse_log`, `PARSER_VERSION` and `report.py` are untouched. Proven by J3,
J4, J5, J5b, J7, J9 and RD2 (§4).

**Rejected.** Appending games to `runs.jsonl` mid-cycle (more torn-write exposure; half cycles visible to ranking).
Journaling in the batch runner or bot (outside `ai-agent/`). Profiles alone (a power cut can cut a log's tail; the
fsynced journal was parsed whole).

### 2b. O8: torn-write resilience

New helper `_atomic_write_text(path, text)`: write `path.tmp`, flush, `os.fsync`, `_replace_with_retry` (`:1002`).
(Windows cannot fsync a folder; NTFS journals the rename.)

**Writes:**
- `append_jsonl`: if the file is non-empty and its last byte is not `"\n"`, write `"\n"` first, so a torn fragment stays
  its own line. One write for all rows, then flush and `os.fsync`. Keep text mode, UTF-8 and `json.dumps(r,
  default=str)`, so healthy bytes are identical (CRLF on Windows, as today).
- `write_jsonl` (reparse), `save_state`, `plan.json`/`arms.json` (`:724-725`), `attention()` and the crash counter
  use `_atomic_write_text`.
- `save_state` writes `state.json` first, then the same text to `data/state.json.bak`, in its own `try`. A failed
  `.bak` write is logged (guarded) and never raised; the next save rewrites it. An example is the backup's open handle
  outlasting the retries (`tools/ops/backup_learner.py:21-25`). So `save_state` gains no new way to raise.
- **The `.bak` is NOT assumed current.** It is the newest state the NEW code saved. It is older when its last write
  failed, when the process died between the two writes, or after a rollback (old code writes `state.json`, never the
  `.bak`) followed by a redeploy. Hence the restore check in `load_state`.

**Loads:**
- `load_jsonl`: read bytes, split on `b"\n"`. A blank or whitespace-only piece is skipped and is NOT a bad line. That
  includes the trailing `b""` after the final newline: the live `runs.jsonl` ends with `"}\r\n"`, and today's loader
  skips blank lines (`if x.strip()`, `:171`). Each other piece is decoded and parsed strictly (JSON accepts the `"\r"`).
  A bad line is skipped and logged, never raised. Healthy files, CRLF included, give today's rows.
- `repair_jsonl(path, limit)`: bad lines go to `<file>.bad` (one JSON object each: found, file, line number, text;
  fsynced). The file is then rewritten without them, atomically, with the good lines copied byte for byte (CRLF kept).
  A replace blocked by an open handle is logged and retried next time. Two modes:
  - **`runs.jsonl` and `cycles.jsonl`:** run by the lock holder only, at start, after the top ATTENTION check (§2c),
    with `limit` = `MAX_BAD_LINES` = 3. Over the limit there is no rewrite: `repair_jsonl` returns "refused", and
    `loop()` writes `attention("…restore it from the nightly backup")` and returns 0. The backup does hold `data/`
    (`backup_learner.py:342-352`). No helper calls `sys.exit`.
  - **`games.jsonl`** (`journal_games`, `recover_records`): no limit. Every bad line is moved, and there is never an
    ATTENTION or a stop. The nightly backup does NOT hold `runs/<tag>/` (`backup_learner.py:342-352`), so "restore it"
    would be false there; the lane profiles are the fallback. On any failure, log it and use the good lines in
    memory.
- `load_state`: parse and check the shape (a dict, an int `cycle`, a list `cycles`). When `state.json` is unreadable or
  missing, the `.bak` is used ONLY if it parses with the right shape AND its `cycle` is at least the highest `NNNN`
  among `runs/aiNNNN` and `PROFILES/endless-aiNNNN-*`. Both survive archiving. `run_cycle` makes the folder before the
  save that sets `cycle` (`:721-730`), so a `.bak` behind any started cycle is stale. Then:
  - The lock holder (a `_LOCK_HELD` flag) renames the bad file to `state.json.bad.<k>` (never deleted), restores
    `state.json` and logs "restored from state.json.bak (cycle N; the newest cycle's archive flags and failure count
    may be one save old)". Other processes use the `.bak` in memory only.
  - Otherwise raise `StateUnreadable` and name the gap ("state.json.bak holds cycle 47 but runs/ai0053 exists"). Never
    return a fresh state.
  - Neither file exists → fresh state (first start, as today).
  - A crash in the milliseconds between `:721` and `:730` with a torn `state.json` also refuses. That is conservative,
    and the breaker sends it to a human.
  - **Rejected:** a save counter, because old code copies the key unchanged and so cannot reveal a rollback. Also an
    mtime rule ("`.bak` no older than the bad file"), because it refuses safe cases. A `.bak` one save behind can be
    hours older than `state.json` and still be safe when the runs check passes: a lost finish save is redone by adopt,
    and the dedupe stops it double counting.
- Adopt: unreadable `plan.json` → moved to `plan.json.bad`, `current` cleared, logged (as for a missing plan,
  `:816-820`). Unreadable `ARMS.json` at `:761` → `{}` plus the `created` rebuild (§2a).
- `config.json`: no fallback (a human's file; guessing is worse than stopping). Its failure goes to the breaker.

**Not changed:** `ops.jsonl`, `agent.lock`, `inbox/` (guarded), `LATEST.md` (self-heals), consult files (fail open).

### 2c. O8: the crash-loop breaker

- **Where:** in Python. The FIRST statement inside `loop()`'s `try` is now the ATTENTION check: if `ATTENTION.md`
  exists, log and return 0. The check at `:1446` stays. WHY: the crash path (`:1433-1439`) runs before `:1446`. The
  logon autostart (`README.md:54`; it runs `run_agent.ps1`) would otherwise restart a crash loop that the breaker
  stopped, 5 more crashes per logon. The startup repair of `runs.jsonl`/`cycles.jsonl` comes next. An
  `except Exception` before `loop()`'s `finally` (`:1507`) covers everything from there: `load_state` (`:1433`),
  adopt, the update/test step, and the crash handler's own `load_state` (`:1492`). STOP stays where it is, because
  `run_agent.ps1:11` checks it before every start, the autostart's included. `run_agent.ps1` is **not** changed: a
  `.ps1` edit reaches the live window only after a manual restart, and `code_signature` ignores `.ps1` (`:202-207`).
- **On a crash** (run mode; `once` returns 1 uncounted). Each step has its own `try`; when even logging fails, it
  prints to stderr.
  1. Log `learner CRASHED (n of 5 in a row)` and the traceback.
  2. `n = _note_crash()`: increment `data/crashes.json` `{count, first, last, last_error}`. It is kept outside
     `state.json`, which may be the broken file; unreadable counts as 0. If the write fails, print to stderr and
     return 1. That is today's 10-minute retry; a full disk is caught by the watchdog's disk and liveness checks.
  3. **Fetch a fix.** If `config.json` reads and `auto_update` is on, call `update_checkout()`, which never raises
     (`:223-238`). If `code_signature()` now differs from `started_sig`:
     - If `tests_pass()`, log "code changed during a crash loop and test_agent.py passes: restarting into it" and
       return 3. `run_agent.ps1` restarts at once, and the count is kept, so new code that crashes the same way still
       reaches 5.
     - If the tests fail, write `attention("The learner was crash-looping and the update it fetched FAILS
       test_agent.py; the next start would run that untested code. …")`, reset the count and return 0.
     WHY: today the fast-forward runs only at `:1449-1452`, after `:1433-1439`. Without this step, a crash there never
     reaches `update_checkout`, so a pushed fix or revert never arrives (§5 Rollback).
  4. n < 5 → return 1 (`run_agent.ps1` waits 10 minutes, as today). n = 5 → `attention("The learner crashed 5 times in
     a row and stopped retrying. Last error: <type: message>. Tracebacks: data/learner.log.")`, reset to 0, return 0,
     and `run_agent.ps1` stops.
- **Limit:** `CRASH_LIMIT` = 5, a module constant (config may be the broken file).
- **Reset to 0:**
  - When `run_cycle` has launched a batch (`Popen` succeeded; guarded, §2a). A `finish_cycle` crash after that is
    already counted by `failures`, `:1496-1502`, untouched.
  - When the breaker writes ATTENTION, so deleting it and restarting gives a fresh 5.
  - On any CLEAN exit of `loop()`, return 0 or 3 from the normal path (STOP, ATTENTION, the disk floor, a restart into
    new code), so crashes before a human STOP and restart do not count as "in a row". The crash handler's own return 3
    keeps the count.
- **Not counted:** `KeyboardInterrupt`. Lock acquisition (`:1424`) stays outside the `try` (known gap).
- **What the user sees:** a watchdog NEEDS YOU toast, "the learner paused itself: <reason>", within 30 minutes
  (`tools/ops/watchdog.py:557-560`, USER RULING 43); the `ATTENTION.md` flag in `tools/status.py`; "crashes in a row: n"
  in `learner.py status`. About 40 minutes from the first crash to ATTENTION.

## 3. Files

**Change:**
- `ai-agent/learner.py`: changed `append_jsonl`, `write_jsonl`, `load_jsonl`, `load_state`, `save_state`, `attention`,
  `acquire_lock`/`release_lock`, `run_cycle`, `finish_cycle`, `adopt_unfinished`, `loop`, `cmd_status`; new
  `repair_jsonl`, `_atomic_write_text`, `StateUnreadable`, `journal_games`, `recover_records`, `_note_crash`,
  `_clear_crashes`; constants `JOURNAL_POLL_S`, `JOURNAL_STABLE_S`, `MAX_BAD_LINES`, `CRASH_LIMIT`; paths `STATE_BAK`,
  `CRASH_FILE`.
- `ai-agent/scoring.py`: `lane_record`; `parse_batch(..., lane_logs=None)`.
- `ai-agent/test_agent.py`: four groups (§4). `LEARNER_PATHS` gains `STATE_BAK`, `CRASH_FILE` (`assert_isolated`
  fails without them, which is intended); `SANDBOX_ATTRS` gains every patched name (including `update_checkout`,
  `tests_pass`, `code_signature`, `JOURNAL_POLL_S`, `JOURNAL_STABLE_S`).
- `ai-agent/README.md`: the journal, the `.bak`/`.bad` files and when a `.bak` is refused, the breaker, what to do per
  ATTENTION, the manual rollback (§5).
- New `tools/ops/replay_learner_recovery.py`: off-gate real-data acceptance (RD1, RD2).
- Docs per the Definition of Done: `02`, `03`, `04`, `05`, `07`; `06` for §2a's recovery choice, §2b's `.bak` check
  and §2c's choices.

**Untouched:** `run_agent.ps1`, the scheduled tasks, `x4_headless.py`, `sandbox-pokebot/`, `brain.py`,
`knowledge.py`, `report.py`, `consult.py`, `config.json`, `tools/status.py`, the watchdog, `ai_player/`, the clone.

## 4. Proof plan

All tests go in `test_agent.py` (the deploy gate), temp-dir isolated. Target ≤ 15 s added (suite ~36 s, gate timeout
600 s); record the measured time. A FAULT arm patches the guard away or runs a verbatim copy of today's function
(`REF_*`) on the same file, and must fail its check. A CONTROL shows the healthy case unchanged.

**Names.** New groups are T, ST, BK and J; the off-gate checks are RD. They avoid the existing S1-S14 (scoring,
`test_agent.py:104-136`), B1-B13 (brain, `:139-189`) and R1-R21 (prune).

**Every check that drives `loop()`** runs inside `O3Sandbox`, whose `_cmdlines` is empty. It patches `load_config` to
`DEFAULTS` plus `auto_update=False`, `wait_if_other_bots_running=False`, `lanes=8`, and it patches
`sleep_unless_stopped`, as the existing loop tests do (`test_agent.py:1411`, `:2036`). It also spies or patches
`update_checkout`, `tests_pass` and `code_signature`. `tests_pass` is ALWAYS patched: the real one would run this
suite inside itself. WHY: the suite runs in the clone, whose `config.json` has `auto_update` true, so an unpatched loop
would run real git there and see this PC's other bots and its real RAM. A failure seen only there sets `refused_sig`
(`:1458`), which is never retested.

**`test_o8_torn`: torn JSONL line**

| Check | Setup | FAULT | Guarded result |
|---|---|---|---|
| T1 | 3 rows + half a row, no `"\n"` | `REF_load_jsonl` raises | Load returns 3; repair moves the fragment to `.bad`, rewrites the 3 rows byte for byte; a second repair moves nothing |
| T2 | T1's file + 1 appended row | `REF_append` glues: 3 readable | 4 readable |
| T3 | `runs.jsonl` with 5 bad lines | (none) | Repair returns "refused", file byte-unchanged; via `loop()`: ATTENTION written, returns 0 |
| T4 | torn `cycles.jsonl` tail; `drive_cycle` | `REF_load_jsonl`: RAISED (today: `ok` False, `failures` + 1) | `run_cycle` returns True; `scored()` passes; the new cycle row is readable |
| T5 | torn `runs.jsonl`, `STOP` planted; real `loop()` | startup repair call deleted: no `.bad` | Returns 0; `runs.jsonl.bad` holds the fragment; `runs.jsonl` = the good lines byte for byte |
| T6 | `games.jsonl` with 5 bad lines; `journal_games` | journal handled in runs mode: refused / ATTENTION | All 5 in `.bad`; no ATTENTION, no exit; `a-0`, `a-1` still journaled |
| T-C | healthy CRLF file ending `"\r\n"` | control | 0 bad lines; load = `REF_load`; repair a no-op (no `.bad`, same bytes and mtime); append bytes = `REF_append`'s; fsync called |

**`test_o8_state`: truncated or empty `state.json`**

| Check | Setup | FAULT | Guarded result |
|---|---|---|---|
| ST1-ST4 | 0 bytes / first half / 4 KB NUL / valid JSON list; good `.bak` | `REF_load_state` raises (ST1-ST3), returns a list (ST4) | `.bak` dict returned, `state.json` restored, bad kept as `state.json.bad.1` |
| ST5 | both unreadable | (none) | Raises `StateUnreadable`, never `{"cycle": 0}` |
| ST6 | `state.json` missing, `.bak` good | `REF` returns cycle 0 | Restored |
| ST7 | not the lock holder | (none) | Reads the `.bak`, moves nothing |
| ST8 | stale `.bak` (cycle 47), `runs/ai0053` exists, `state.json` torn | runs check removed: cycle 47 restored | Raises `StateUnreadable` naming "47" and "ai0053"; nothing renamed |
| ST9 | the `.bak` replace raises `PermissionError` on every try | unguarded `.bak` write: `save_state` raises | `save_state` returns; `state.json` holds the new state; a log line names the failure |
| ST-C | healthy; first start | control | Load = saved dict; `.bak` = `state.json`; fsync spy on both; no files → fresh state |

**`test_o8_breaker`: crash loop** (real `loop()` under the patches above, deployment marker in the temp dir)

| Check | Setup | FAULT | Guarded result |
|---|---|---|---|
| BK1 | `state.json` and `.bak` both bad | `CRASH_LIMIT` huge or `_note_crash` no-op: no ATTENTION after 5 | Returns 1,1,1,1,0; ATTENTION says "crashed 5 times" and names `StateUnreadable`; 5 tracebacks in `learner.log`; count reset to 0 |
| BK2 | `load_config` patched to raise | (none) | Counted the same way; no update attempted |
| BK3 | 3 crashes from `loop()` (bad state); state fixed; one cycle through `run_cycle` DIRECTLY (`drive_cycle`); bad state again; 4 crashes | reset patched out: ATTENTION at the 2nd of the 4 | No ATTENTION; count 4 |
| BK4 | a pushed fix: crash with `auto_update` on, `update_checkout` spied, `code_signature` changed after it, `tests_pass` → True | handler without step 3: returns 1 | Returns 3; the spy was called once; no ATTENTION; count 1 |
| BK4b | as BK4, `tests_pass` → False | (none) | Returns 0; ATTENTION says the fetched update fails `test_agent.py` |
| BK5 | `ATTENTION.md` planted + bad state | ATTENTION checked only at `:1446`: returns 1, count 1 | Returns 0 at once; count unchanged; no state file touched |
| BK6 | crash with the `crashes.json` write and `log()` both raising | unguarded handler: the exception escapes | Returns 1; stderr names the crash |
| BK7 | 3 crashes, a clean `STOP` run (returns 0), then 4 crashes | clean-exit clear patched out: ATTENTION | No ATTENTION |
| BK-C | healthy state + `STOP` | control | Returns 0, no crash, no ATTENTION, count 0; a crash in `once` returns 1 uncounted |

**`test_e2_journal`: per-game records** (`make_batch`'s logs copied into lane profile dirs)

| Check | Setup | FAULT | Guarded result |
|---|---|---|---|
| J1 | poll twice | (none) | Only `a-0`, `a-1` journaled (not newest `a-2`, `b-1`), no duplicates; adding `a-3` journals `a-2` next poll |
| J2 | candidate modified now | stable window 0: journaled | Not journaled |
| J3 | (none) | (none) | Each journal record = `REF_parse_batch`'s record of the copied logs, every field |
| J4 kill mid-cycle | `current` set, `plan.json`, `ARMS.json`, no copied logs, torn journal tail | `recover_records` patched out: 0 rows (ai0031) | Adopt's rows = `REF_parse_batch` over the profile logs as `collect_logs` would copy them, row for row; 3 usable; `recovered` set; proposals done; tail in `.bad`; its key set `(source, batch, lane, log)` recorded |
| J5 recovery re-adopt | after J4, restore pre-adopt `state.json` and `games.jsonl` (a death between append and save), adopt again | dedupe patched out: keys duplicated | `runs.jsonl`'s key set = J4's, each key once; one cycle row |
| J5b normal re-adopt | adopt with copied logs (as L1-L3), restore pre-adopt `state.json`, adopt again | dedupe patched out: each key twice | Key set = the first adopt's, each once; one cycle row |
| J6 | profile dirs deleted | (none) | Journal records only |
| J7 normal path | `drive_cycle` (real `run_cycle`), `JOURNAL_POLL_S` 0.05, `JOURNAL_STABLE_S` 0, logs in the lane profiles | one journal record altered before the compare: the line names its key | The journal-append spy saw ≥ 2 named keys (`a-0`, `a-1`) before the batch ended; rows = `REF_parse_batch` of the copied batch; the compare line says "2 of 2"; journal deleted; O6 `scored()` passes |
| J8 old files | adopt with copied logs, no `games.jsonl` | control | Existing L1-L3 pass unchanged |
| J9 swap | journal `a-0`, `a-1`; then cut `a-1.log`'s last lines in its profile; adopt with no copied logs | swap removed: `a-1`'s row = REF | `a-1`'s row = the journal record, and differs from `REF_parse_batch`'s row of the cut log |
| J10 adopt loop | `adopt_unfinished` with `batch_running` True for 2 polls, sleep patched, stable window 0 | adopt-loop journal call removed: no append before scoring | The append spy saw `a-0`, `a-1` during the polls |
| J11 never kills | `drive_cycle` with `journal_games` raising and `log()` raising inside its handler | guards removed: RAISED, fake batch killed | `run_cycle` returns True; `scored()` passes; the fake batch ran to its end (exit 0) |
| J12 start filter | ARMS with `started`; one profile log with mtime 1 h before it | filter removed: the stale log is journaled and recovered | Stale log neither journaled nor recovered; CONTROL: a fresh log is |
| J13 bad plan / ARMS | profiles named `endless-<tag>-*`; (a) `plan.json` half JSON; (b) `ARMS.json` half JSON at finish | REF: raises at `:827` / `:761`; no rebuild: `created` lacks the profiles | (a) `plan.json.bad` exists, `current` cleared, adopt returns None; (b) finish returns, `created` = batch + both profiles |

**Also:** every existing group passes unchanged (S1-S14 cover the refactor). **Mutants:** delete each guard call and
check that the suite fails for each. Record the count. The guards: newline guard, startup repair, journal-mode repair
without a limit, `.bak` write and its guard, `.bak` restore and its runs check, the top ATTENTION check, outer `except`,
counter, the handler's update step, reset (Popen, ATTENTION, clean exit), recovery, swap, dedupe, the `run_cycle`
journal call, the adopt-loop journal call, the journal and clear guards, the `plan.json` and `ARMS.json` guards, the
`created` rebuild.

**Off-gate real-data acceptance** (`tools/ops/replay_learner_recovery.py`; reads the clone read-only, writes only to
scratch; outcomes registered before the run). Off the gate because the gate runs in the clone and must not depend on
live data.
- **RD1, ai0031:** copy `runs/ai0031/raw.zip` and `plan.json` out, unzip, run `recover_records`. Expect 24 records:
  the 12 not-newest logs complete, plus any newest log already at Champion or derail #5 (report how many).
- **RD2, faithfulness, ai0049-52.** Their profiles, the copied batch and the ground-truth rows all exist (clone
  `runs.jsonl`: 55/59/52/52 rows). Point `RUNS` at scratch and `batch`/`PROFILES` at the clone. Compare by identity
  `(batch, lane, log)`, never by count. Any difference stops the deploy.
  - (a) `journal_games`, stable window 0: every journaled record equals the clone's row field for field.
  - (b) `recover_records` on the profiles, once with no journal and once with (a)'s. Its key set must equal the
    clone's rows for that batch, and every row, the censored newest logs included, must equal its clone row field for
    field.
  - **Timing:** `keep_raw_cycles` is 4 (clone `config.json`), so ai0049's raw logs are archived when ai0053 ends
    (about 4:28 PM 2026-10-28). Run RD2 before then, or use ai0050-53 after.

## 5. Deploy

- **No stop needed.** `run_agent.ps1` and the task are unchanged. Ship as usual: commit with explicit paths, push to
  `main`. U1 is answered (USER RULING 48: yes), so the push need not wait.
- **The cycle in flight is untouched.** The learner fast-forwards only between cycles (`:1449-1452`) and restarts into
  new code (exit 3) only if `test_agent.py` passes (`:1453-1457`). ai0053 (started 04:28 AM, ends about 4:28 PM today)
  finishes under the old code; no cycle runs half under each.
- **Backward compatibility:** schemas unchanged (the counter is a separate file); the first save writes the first
  `.bak`; no `PARSER_VERSION` bump, so no startup reparse; a cycle without `games.jsonl` recovers from profiles alone;
  an old `plan.json` is read through the guard; a missing `crashes.json` counts as 0.
- **Edge case:** if the tests FAIL in the clone, the old process runs on with new files on disk ("FAILS: keeping the
  running version"); a mid-cycle restart then has new code adopt an old-code cycle (covered by J8, and J4 without a
  journal).
- **Check after the boundary** (read-only): `learner.log` shows "test_agent.py passes: restarting into it";
  `state.json.bak` exists; `crashes.json` is absent or 0; `runs/<new tag>/games.jsonl` gains lines within ~3 hours;
  the cycle ends with the "game journal: N of N match" line and normal counts (lately 50-62 runs, 38-50 usable). A
  "FAILS" line → investigate in a scratch clone; the tuner keeps running.
- **Rollback:** revert and push. It arrives at the next cycle boundary like any change. If the new code crash-loops at
  startup, the breaker fetches it at the next crash (§2c step 3) and restarts into it once it passes its tests (a
  revert does). **Roll back BY HAND** when the learner has already stopped (`ATTENTION.md`) or the update step itself
  is what is broken:
  1. `git -C "C:/Remote Projects/pokebot-learner" fetch origin`
  2. `git -C "C:/Remote Projects/pokebot-learner" merge --ff-only origin/main`
  3. Delete `ai-agent/findings/ATTENTION.md`.
  4. Start `run_agent.ps1`.
  After a rollback, old code writes `state.json` but never the `.bak`. On a redeploy the `.bak` stays stale until the
  first save, and the runs check (§2b) refuses it in that window.

## 6. Risks, scope and questions

**Risks:**
- The `Popen` loop must match `subprocess.run` (kill on any `BaseException` that reaches it). J7 and J11 drive the real
  `run_cycle`. `proc.kill` stops only `x4_headless.py`, as today; the guards keep the new code from ever reaching it.
- The breaker stops the tuner on a fault lasting over ~40 minutes that today it might outlive (accepted; toasted).
- The breaker's update step runs real git, and on a code change the ~36 s test suite, inside a crash handler. In a
  crash loop, a fetched update that fails its tests stops the tuner (ATTENTION) instead of running untested.
- A `.bak` can miss the newest cycle's archive flags and failure count (one save). The restore logs this; a lost finish
  save is redone by adopt and deduped.
- A game that ended within ~7 minutes of a power cut comes from its profile log, which may lack its last lines.

**Out of scope:** E3; O12 (why the PC shut down); O2 (longer cycles); a crash during the batch runner's ~1-minute log
copy (a partial copy behaves as today); the batch runner's non-atomic `ARMS.json`; `cmd_reparse` re-reading recovered
cycles from profiles (their rows are kept by `:1550`); the "no scored runs" wording (`:1500`); the lock race
(`:276-280`); journal or crash count in `tools/status.py`.

**Questions only the user can answer** (✅ ANSWERED 2026-10-28, USER RULING 48 in `06`: U1 "Yes, count them", U2 "No, leave them out"):
- **U1 (before deploy).** When the PC dies mid-cycle, should the games that finished before the crash count toward the
  strategy ranking, the same as games from a cycle that ended normally? Counting them also uses up that cycle's tested
  proposals, as any cycle with a scored game does. The spec's default is yes, because item (1) asks for exactly that
  ("record each game as it finishes"). If the answer is no, the recovery case keeps the journal, appends nothing, and
  the proposals stay queued.
- **U2.** Should ai0031's 12 lost games be added back from its `raw.zip`? That adds old data to the ranking, so it is
  the user's decision.

## 7. Critique round (2026-10-28)

One adversarial round, 22 findings (safety and proof lenses). Each was checked against `ai-agent/` at `f9fffb68` (the
clone read-only) before the spec changed.

| # | Finding | Verdict | What changed, or why not |
|---|---|---|---|
| 1 | Rollback cannot arrive after a startup crash | ACCEPTED | Verified: the fast-forward is only at `:1449-1452`, after `:1433-1439`. §2c step 3 now fetches in the crash handler (with a test gate), §5 gives the manual rollback, and BK4/BK4b test it |
| 2 | Journal and reset run inside the batch's kill region; `log()` is unguarded | ACCEPTED | Verified `:144-146`, and the lanes outlive `proc.kill` (`run_agent.ps1:4-5`). §2a: both calls guarded, their log in its own `try`; only `KeyboardInterrupt`/`SystemExit` or `proc.wait` kills. J11 added |
| 3 | The `.bak` "mirrors the newest good state" is false after a rollback | ACCEPTED in substance | Restore now requires the `.bak`'s `cycle` ≥ the highest `aiNNNN` folder; otherwise `StateUnreadable` (ST8). REJECTED the save-sequence and mtime parts: old code copies a counter unchanged, and mtime refuses safe one-save-behind cases (§2b) |
| 4 | `repair_jsonl`'s exit on `games.jsonl` kills a batch or stops the learner | ACCEPTED | Journal mode: no limit, never ATTENTION or a stop; the refusal is returned to `loop()`, with no `sys.exit` in a helper (T6) |
| 5 | B3 through the real loop reaches git, process scans and RAM | ACCEPTED | Verified: the clone `config.json` has `auto_update` true, and `AI` is a code root. BK3 calls `run_cycle` directly; every `loop()` check uses the patch set in §4 |
| 6 | Logon autostart restarts a stopped crash loop; the counter ignores clean exits | ACCEPTED in part | ATTENTION is checked at the top of `loop()` (BK5); the counter clears on any clean 0/3 exit (BK7). REJECTED "and STOP": `run_agent.ps1:11` checks STOP before every start, the autostart's included (`README.md:54`) |
| 7 | The breaker's own write or log can raise uncounted | ACCEPTED | Each handler step guarded; stderr fallback; a failed count write returns 1 (BK6). It cannot count on a full disk; the watchdog's disk check covers that |
| 8 | A `b"\n"` split counts the trailing empty piece as bad | ACCEPTED | Verified: the live `runs.jsonl` ends `"}\r\n"`. Blank pieces are skipped and not bad; repair keeps good lines byte for byte (T-C) |
| 9 | A torn `cycles.jsonl` is understated | ACCEPTED | §1b now states `ok` False, `failures` + 1 and the false ATTENTION after 3 (`:1490`, `:1497`, `:1500`); T4 added |
| 10 | "Ranking … do not change" is false in the recovery case | ACCEPTED | §0 caveat, the INVARIANT reworded (rows, proposals, `failures`), U1 asks the user, and the push is held for the answer (then answered: USER RULING 48, see §5) |
| 11 | J7 passes on "0 of 0" | ACCEPTED | Verified: the fake batch lives ≤ 0.4 s against a 120 s stable window. J7 sets it to 0 and requires ≥ 2 named keys plus a "2 of 2" line, with a mismatch FAULT |
| 12 | The swap is never tested | ACCEPTED | J9 (a cut profile log must yield the journal's record); swap added to the mutants |
| 13 | `recover_records` is never checked against real rows | ACCEPTED | RD2(b): full-row identity compare on ai0049-52, with the 4:28 PM archive deadline noted (`keep_raw_cycles` 4 verified) |
| 14 | Dedupe on the normal path is untested; J5 checks a count | ACCEPTED | J5 asserts the key set; J5b re-adopts with copied logs |
| 15 | No check drives the startup repair through `loop()` | ACCEPTED | T5 |
| 16 | Bad `plan.json`/`ARMS.json` untested; `created` loses the profiles | ACCEPTED | Verified `:762`, `:849`, `:1111`. `created` is rebuilt from `endless-<tag>-*` (§2a); J13 |
| 17 | `games.jsonl` refusal contradicts "never fails a batch"; the backup lacks `runs/` | ACCEPTED | Verified `backup_learner.py:342-352` (`data/`, `findings/`, `inbox/`, `config.json`). Same fix as #4 |
| 18 | The start filter only approximates `collect_logs`, and no fixture has `started` | ACCEPTED | Worded "approximates" (a superset by up to ~2 s); J12 |
| 19 | The adopt-loop journal call is untested | ACCEPTED | J10; added to the mutants |
| 20 | Same as #9, proof lens | ACCEPTED | As #9 |
| 21 | Per-lane counts are in alphabetical order; S1-S7 collide | ACCEPTED | Verified from `raw.zip`'s `batch/ARMS.json`: 2,1,1,2,2,3,1,3,4,1,2,2. Renamed to ST/BK; also found B1-B3 colliding with brain B1-B13, and off-gate R1/R2 with prune R1/R2 (now RD1/RD2) |
| 22 | A failed `.bak` replace raises after `state.json` was replaced | ACCEPTED | `.bak` write guarded and logged (§2b); ST9 |
