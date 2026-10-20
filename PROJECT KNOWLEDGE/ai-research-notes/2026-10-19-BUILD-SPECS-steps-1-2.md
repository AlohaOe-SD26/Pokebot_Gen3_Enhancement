# BUILD SPECS for order steps 1 and 2 (critiqued 2026-10-19)

- **What this is:** build-ready specs for steps 1 and 2 of "The order" in `2026-10-18-improvement-backlog.md`, taken from the
  round-3 note `2026-10-19-backlog-round3/01-build-specs.md` after a critic pass. A spec was kept only if its tests hold a FAULT
  arm AND a CONTROL, its deploy keeps the learner safe (`test_agent.py` passes before the commit and before any restart; the
  deployment clone is never edited; a learner setting changes by commit + push to main), and it lowers no rigor.
- **A SPEC, NOT A DECISION.** Nothing here is approved or built. Each item becomes a `06` decision and a punch-list status when it
  is built, and every line-number claim is a NOTE until the builder re-reads those lines (`00-READ-THIS-FIRST.md`).
- **The order it follows:** the backlog's step 1 (O3 -> O4 -> O6+O7 -> O1 -> A1 -> P3), then step 2 (N3+A4+P9 as a ratchet; O5;
  the stage templates last, because P3 measures their compliance). Learner-code items (O3, O6+O7, O5) ship as one reviewed train.
- **Critic's changes are marked `[CRITIC]` in place** and listed in "Critic's ledger" at the end.

## 0. Facts from the code that shape every spec

1. **What restarts the learner.** `learner.py:150-156` `code_signature()` hashes `ai-agent/*.py` ONLY (top level). A change to
   `tools/`, `config.json`, docs or `run_agent.ps1` reaches the clone by the `update_checkout` fast-forward (`:171-186`) but
   never restarts it. A change to any `ai-agent/*.py` restarts it ONLY if `test_agent.py` passes (`:189-195, :478-484`);
   a red suite logs "keeping the running version" and **silently does not deploy**. `test_agent.py` is not in
   `run_gates.py` (grep), so nothing runs it before a commit. **Rule for every learner-code spec: run
   `py -3.12 ai-agent/test_agent.py` before the commit, and confirm the deploy by the clone's `learner.log`
   ("restarting into it") or by A1's status line "running code X vs clone code Y".**
2. **A tracked change in the clone blocks auto-update** (`update_checkout`, `:174-176` "has tracked changes"; untracked files
   do not). `ai-agent/published/` is neither ignored (`ai-agent/.gitignore`) nor tracked today, but the moment a snapshot is
   committed there, running `learner.py publish` FROM the clone would modify tracked files and silently stop auto-update. So the
   weekly snapshot (O4) copies clone data INTO the main checkout instead, and nothing writes a tracked path in the clone.
3. **`consult_log.jsonl` rows consume the daily cap.** `consult.py:42-46` counts any line starting `{"day": "<today>"`. A
   "skipped" row written there would starve real calls (O5 must log skips elsewhere).
4. **A latent data-loss path in `cmd_reparse`** (`learner.py:549-572` with `scoring.py:138-143`): a cycle whose `batch/ARMS.json`
   exists but whose logs are gone yields ZERO fresh records, yet `covered.add(stamp)` still runs (`:566`), so `kept` (`:568`)
   DROPS that batch's old records. Today safe only because `rmtree` removes the whole `batch/`. Any archive design must
   remove `batch/` entirely OR guard `if recs:` (the spec does both).
5. **Machine facts (read-only probes today):** C: = Disk 1 (Samsung 990 PRO), 79 GB free of 1.86 TB. **E: = Disk 2 (Samsung
   970 EVO), a different physical disk, 46.9 GB free.** Z: = Disk 0 (WD HDD 4 TB), 181 GB free. The Desktop is
   **OneDrive-redirected** (`C:\Users\Ripto\OneDrive\Desktop`). The autostart task `Pokebot-AI-Learner-Autostart`: logon
   trigger with a 2-minute delay, `powershell -NoExit ... run_agent.ps1`, `RestartCount 0`.
6. **Transcript layout (for P3):** `~/.claude/projects/C--Remote-Projects-Pokebot-Gen3-Enhancement/<session>.jsonl` (4 main),
   `<session>/subagents/agent-*.jsonl` (300), `<session>/subagents/workflows/wf_*/agent-*.jsonl` (684) with `agent-*.meta.json`
   (`agentType`, `description` such as `recon:decomp`, `workflowPhase`), `.../wf_*/journal.jsonl` (agentId to label to phase),
   and `<session>/workflows/wf_*.json` holding `runId`, `timestamp` and the full workflow `script` source (so the real workflow
   prompts DO exist, only outside the repo). Assistant lines carry `message.model` and `message.usage`
   (`input_tokens`, `cache_creation_input_tokens` with a 5m/1h split, `cache_read_input_tokens`, `output_tokens`). 1,088 `.jsonl`
   files in that one project folder today (the "980" of angle 2 was a count at another time).
7. **Existing tools to REUSE, not rewrite:** `tools/story-dev/archive_doc_block.py` (moves one block under four invariants A-D,
   has `--self-test`); `ai_player/gates/prune_evidence.py:47` `CITING`; `ai_player/gates/disk_budget.py:130` citing patterns;
   `ai_player/gates/check_lessons.py:38-45` `DOCUMENTS`; `lint_docs.py:122-160` `_blank_fenced` (fence-blanking that keeps the
   line count, the "mention is not a violation" machinery). `provenance.py:56-60` digests `ai_player/` and excludes `**/*.md`
   and `evidence/`, so **docs-only and `tools/`/`ai-agent/` changes never stale an AI-player evidence file**.
8. **Test conventions to follow:** `test_agent.py` uses `check("ID name", ok, detail)` (`:26`), FAULT/CONTROL names (`R2`, `C3`/`C4`
   use a sentinel on `shutil.which` to prove Claude was or was not reached) and registers tests in the tuple at `:323-324`
   (about 10 s total; `tests_pass` has a 600 s cap). Repo-level checks are `tools/story-dev/selftest_*.py` registered in
   `run_gates.py` `GATES` (`("selftest_x.py", False)`, cwd `tools/story-dev`).

**Build order (dependencies):** O3 -> O4 -> O6+O7 (learner side) -> O1 -> A1 -> P3. Step 2: N3 (R8 as a RATCHET) -> A4 sweep + P9
split -> ratchet down; O5 independent; templates after P3 (P3 measures their compliance). After adding gates run
`audit_doc_consistency.py` (it checks gate counts).

---

## STEP 1

### S1-1. O3: compress each cycle's raw logs instead of deleting them

**Files:** CHANGE `ai-agent/learner.py` (`prune` `:418-432`, callers `finish_cycle :390` and the disk guard `:487`; new
`archive_cycle`, `verify_archive`, `cmd_archive`; guard in `cmd_reparse :566`); CHANGE `ai-agent/config.json` (new keys, below);
CHANGE `ai-agent/test_agent.py` (R4-R11 and R5b); doc fix `ai-agent/README.md` ("about 4 GB a cycle" is 1.4 GB, measured 1.3 G for ai0034).

**Behaviour.**
- `keep_raw_cycles` keeps its meaning: the newest N cycles stay RAW (interactive grep). Cycles older than that are ARCHIVED, then
  their raw removed. New keys: `max_archives_per_prune: 3` (bounds boundary latency: about 15-30 s per 1.3 GB cycle), `keep_archive_cycles: 0`
  (0 = forever; the archives ARE A6's input).
- `archive_cycle(c)` for a cycle with a `batch/` that holds files: write `runs/<tag>/raw.zip.part` (stdlib `zipfile`, `ZIP_DEFLATED`
  level 6, member names relative to `runs/<tag>/` so `batch/L01/debug-logs/x.log`; zip not tar.gz so A6 reads ONE log by name
  with `ZipFile.open`). Compute each source file's CRC32 while streaming. Then verify: `testzip() is None`, member count and sizes
  equal the source list, each member CRC equals the source CRC. Only then `os.replace` to `raw.zip` (retry 5x, 2 s apart, for an
  antivirus lock), write `raw.manifest.json` (`tag, n_files, bytes_raw, bytes_zip, members[{name,size,crc32}]`), and only then
  delete the originals (`batch/` whole, plus the lane profiles by the SAME `ours` predicate as today; extract it as `_ours(c, p)`).
- Idempotent after a crash: `.part` leftovers are removed at the next prune; `raw.zip` present AND originals present is re-verified
  against the originals, then the originals are deleted; a `raw.zip` that fails verification is renamed `raw.zip.bad` and
  re-archived while the originals still exist. `c["archived"]=True` and `c["pruned"]=True` are set only after the originals are gone.
- **Never delete without a verified archive, with NO exception.** [CRITIC: the source spec deleted the oldest raw under 2 GB
  free; the round-2 critic REJECTED pruning A6's input under disk pressure, and a delete cannot be undone.] Under 2 GB free (no
  archive can be written): do NOT start the next batch, log loudly, write `ATTENTION.md`, delete nothing. The watchdog's 40 GB
  alarm (S1-4) and O7's early archive fire long before this floor.
- `prune` can never raise into the loop: each cycle is wrapped, a failure is logged and retried next boundary.
- Disk guard `:487` (`keep_raw_cycles: 1`) now ARCHIVES (frees about 97 %) instead of deleting.
- `cmd_reparse`: `if recs:` before `covered.add(...)` (fact 4); optional follow-up (not in this item): re-read archived cycles by
  extracting ONE at a time to `runs/_reparse_tmp/` and deleting it, so a parser upgrade covers all history, not 20 cycles.
- `learner.py archive-check`: re-verify every `raw.zip` against its manifest (read-only, about 1 s per 50 MB); A1 prints its last result.
- [CRITIC] `learner.py archive` (the manual `cmd_archive`) refuses while the learner holds its lock (`data/agent.lock`, the name S1-2
  uses; the builder confirms it), so a second writer never races `prune`. `archive-check` stays read-only and may run any time.
- UNVERIFIED: whether lane profiles (`sandbox-pokebot/profiles/endless-<tag>-*`, 6.9 GB) hold anything A6 wants. This spec keeps today's
  behaviour (delete with the raw); A6's spec must open one before it relies on that.

**Tests (`test_agent.py`; synthetic batch with 3 logs, one 5 MB repetitive).**
- R4 round trip: prune with keep 1 over two cycles -> `raw.zip` exists, `batch/` gone, every member's bytes read back from the zip
  equal the pre-prune sha256, manifest matches. (R1/R2 stay green: an EMPTY `batch/` needs no archive; a path not created by name is
  never touched.)
- R5 FAULT, in-process: make the stream copy raise `OSError` after the first member -> originals byte-identical, no `raw.zip`, `c["pruned"]` False,
  the loop-facing `prune` returned normally; CONTROL: the next prune with no fault archives it.
- R5b FAULT, a REAL kill: a TEST-SIDE wrapper script imports the learner, monkeypatches the copy loop to sleep per member and runs
  `archive_cycle` [CRITIC: no delay switch in learner code; a stray environment variable must never change the live learner]; `Popen.kill()` while `raw.zip.part` exists; assert
  originals intact and the next prune completes. (The backlog's "kill mid-gzip" taken literally.)
- R6 FAULT corrupt archive never trusted: patch verification to see a flipped byte -> originals kept, `.part` removed. CONTROL: untouched -> deleted.
- R7 crash between replace and delete: `raw.zip` + originals present -> re-verified, originals deleted; with a CORRUPT `raw.zip` + originals -> originals kept, zip quarantined as `.bad`.
- R8 `os.replace` raising `PermissionError` twice then succeeding -> archived; always raising -> originals intact, no exception escapes.
- R9 reparse safety: batch with `ARMS.json` and no logs -> old records kept (FAULT: remove the `if recs:` guard and this must fail); CONTROL: logs present -> re-read.
- R10 emergency branch [CRITIC, rewritten]: free 1 GB and a failing archive -> nothing deleted, the next batch NOT started, `ATTENTION.md`
  written; a FAULT mutant that deletes the oldest raw must fail this test. CONTROL: free 50 GB and a failing archive -> nothing deleted,
  the batch starts, the archive is retried at the next boundary.
- R11 [CRITIC] lock: FAULT the lock is held -> `learner.py archive` refuses and the tree is byte-identical; CONTROL lock free -> it archives.
- Real-data proof (not in the suite): the CANARY below, with measured ratio and elapsed seconds recorded in `07`.

**Deploy.** Commit and push `ai-agent/*.py` and the config with `keep_raw_cycles` STILL 20 (no behaviour change on first restart).
Canary: set `keep_raw_cycles` to 13 once (the learner re-reads config each cycle) [CRITIC: by a commit + push to main that the clone
fast-forwards, the usual way; NEVER by editing the clone's `config.json`, whose tracked change would silently stop auto-update (fact 2);
a code deploy is confirmed only by the clone's `learner.log` "restarting into it" line (fact 1)], so exactly ONE real cycle leaves the window at the next boundary [COLD-START CHECK 2026-10-19: the value "13" and "ai0023" are STALE, because ai0023 was pruned at 4:04:30 PM on 2026-10-19 and the oldest raw cycle is now ai0024. COMPUTE it at build time: N = (the number of cycles in the clone's `state.json` that still hold a `batch/` dir) - 1, read just before the change. A config change reaches `finish_cycle` ONE CYCLE LATE (its `cfg` is loaded at cycle start), so expect the canary archive at the second boundary after the push, not the first];
check zip, ratio, `batch/` gone, `runs.jsonl` row count unchanged, and `status`. Then set 4 (same route), only after `archive-check` passes on the canary's zip. Expected: 16 GB of raw becomes about 0.6 GB; steady state 40-60 MB/cycle (ESTIMATE from one measured `stdout.txt` ratio; `.log` ratio unmeasured, so the canary is the measurement).
**Implementation facts the cold-start check had to guess (2026-10-19, now given):**
- The raw logs live at `<clone>/ai-agent/runs/<tag>/batch/L01/debug-logs/*.log`, not in `data/`.
- The disk guard is INLINE in `loop()` (about `learner.py:487`). Extract it into a helper first, so R-tests can drive it.
- `cmd_archive` takes the learner's lock through `acquire_lock()` and `release_lock()`. `acquire_lock` replaces a STALE lock; it never waits on a live one.
- Register `archive` and `archive-check` in the argparse choices (about `:619`) and the dispatch dict (about `:639`).
- `archive-check` prints one line per zip, `OK <tag> <members> <bytes>` or `BAD <tag> <reason>`, and exits 1 on any BAD.

**Risks:** a wrong delete is the only dangerous failure; contained by verify-then-delete, the idempotent recovery tests and "ours" predicate. Boundary latency bounded by `max_archives_per_prune`.
**Size:** about 85 lines code + 95 lines tests: small-medium.

### S1-2. O4: back up the learner's data off C:

**Files:** ADD `tools/ops/backup_learner.py` (stdlib only; imports nothing from the learner), `tools/ops/ops_config.json` (tracked:
`clone`, `backup_dir`, `keep`, `min_dest_free_gb`, `status_file`), `tools/ops/install_ops_tasks.ps1` (shared with S1-4);
ADD `tools/story-dev/selftest_ops.py` (registered in `run_gates.py`).

**Behaviour.**
- Nightly (1:00 AM, clear of the 4 AM/4 PM cycle boundaries; `StartWhenAvailable`): zip `data/` (minus `agent.lock`, `*.tmp`), `findings/`, `inbox/`
  (with `done/`, `rejected/`), `config.json` and `%LOCALAPPDATA%\pokebot-ops\` to `E:\pokebot-backups\learner\learner-data-YYYYMMDD-HHMM.zip`
  (estimate 2-3 MB). The default target is E:; **refuse** a destination on the same volume as the source (`os.stat().st_dev`), under
  `min_dest_free_gb` (10), or not writable. Z: (HDD, 181 GB free) is the alternative if E: ever fills: a user choice.
- Consistent copy: `.jsonl` read in binary to the size seen at the start and trimmed to the last newline (the learner appends
  without fsync); `state.json` read and parsed, 3 retries. Write `.part`, verify, rename, THEN apply retention.
- Verify: zip tests clean; every `.jsonl` member parses line by line; `state.json` parses; `runs.jsonl` line count not below the previous
  backup's (a shrink -> the report says `WARN runs.jsonl shrank A -> B`, because `reparse` may legitimately rewrite it, so a warning, not a failure).
- Retention: keep the newest 14 files matching `^learner-data-\d{8}-\d{4}\.zip$` ONLY; never delete anything else; **never prune after a failed
  backup**. Writes `backup_status.json` (time, bytes, ok, warnings) that the watchdog and A1 read [CRITIC: in `%LOCALAPPDATA%\pokebot-ops\`,
  never in the clone; the tasks run `py -3.12 -B`, so no `__pycache__` is written into the clone either].
- `--restore-check <zip> --into <dir>`: extract and parse; refuses a non-empty target and never writes under the clone. Run the drill once after install and record it.
- Weekly repo snapshot: `backup_learner.py --publish-to "<main checkout>/ai-agent/published"` copies `LATEST.md, latest.json, DEVELOPER-NOTES.md, runs.jsonl, cycles.jsonl,
  learner.log` from the clone into the MAIN checkout; an interactive session commits with explicit paths (A1 prints "snapshot N days old"). The 24/7 process never commits. [CRITIC: measure the snapshot
  before its first commit; `learner.log`'s size is unmeasured, so a file over 5 MB is published as its last 5,000 lines.]

**Tests (`selftest_ops.py`, fake clone tree).**
- B1 round trip: every file's sha256 equals; counts match the manifest.
- B2 FAULT torn append: a writer appends a half line during the copy -> backup holds only complete, parsing lines. CONTROL: untouched file is byte-identical.
- B3 FAULT same volume (inject the `st_dev` probe) -> refuse, nothing written. CONTROL: different volume -> ok.
- B4 FAULT free space 5 GB -> refuse, no partial file; CONTROL 50 GB -> ok.
- B5 retention: 20 old fakes -> exactly 14 newest remain; a file `notes.txt` and `learner-data-notadate.zip` are untouched. FAULT: backup fails verification -> NO old backup deleted.
- B6 FAULT a corrupt new zip is deleted and reported, old ones kept.
- B7 restore-check: parses a good zip; refuses a non-empty target (CONTROL: empty target ok).

**Deploy.** `tools/` reaches the clone on the next fast-forward, no learner restart. The scheduled tasks run the CLONE's copy (the main checkout's work-in-progress
cannot break the nightly). Task registration is a system change: `install_ops_tasks.ps1` defaults to `-WhatIf` (prints what it would register), `-Apply` only
with the user's yes, `-Uninstall` removes them; idempotent. **Risks:** a backup into the wrong disk (B3), a half file (B5/B6), a silent stop (the watchdog flags "no backup in 36 h").
**Size:** about 120 lines + 90 tests: small-medium.

### S1-3. O6 + O7 (learner side): an ops ledger row per cycle and an early-prune margin

**Files:** CHANGE `ai-agent/learner.py` (`run_cycle :333-354`, `finish_cycle :357-391`, `loop :486-490`); CHANGE `ai-agent/test_agent.py`.

**Behaviour.**
- A separate `data/ops.jsonl` (NOT `cycles.jsonl`: its readers `report.write`/`published` stay untouched), one row per finished cycle:
  `tag, started, finished, minutes, free_gb_start, free_gb_end, learner_gb, cpu_avg, consult_seconds, boot_time, gap_minutes` (gap = this start minus the previous finish, idle waits included),
  `archive_seconds, archive_bytes`. `cpu_avg` from a daemon thread sampling `psutil.cpu_percent(None)` every 60 s while `subprocess.run` blocks [CRITIC: `psutil` is imported
  INSIDE the sampler's `try`, so a missing module gives null fields, never a learner that cannot start];
  `learner_gb` from a size walk of `runs/` and the profiles (cap 20 s, else null). `frames_per_lane_sec` is DEFERRED (needs a field from `x4_headless` output; UNVERIFIED).
- **The ledger can never fail a cycle:** all sampling is inside one `try/except` that stores nulls plus `ops_error`.
- O7: in `loop`, if `free_gb() < min_free_gb + early_prune_margin_gb` (new key, default 15 -> acts under 40 GB) run the archive prune at `keep_raw_cycles 2` BEFORE the 25 GB floor path.
  [CRITIC] O7 ships in O3's train or after it, never before: without O3 a prune at keep 2 DELETES A6's input, the round-2 rejection.
  (Self-contained; no cross-process file with the watchdog.)

**Tests.** O6-1 a finished fake cycle appends a row with every key and sane types. O6-2 FAULT psutil patched to raise (and [CRITIC] its import made to fail) -> the cycle is still scored and a null row with
`ops_error` is written. O6-3 CONTROL `report.write` output is byte-identical with and without `ops.jsonl`. O7-1 free 38 GB (min 25, margin 15) -> early prune called with keep 2 and it ARCHIVES ([CRITIC] FAULT: archiving made to fail -> the early prune deletes nothing);
CONTROL free 60 -> not called; FAULT margin 0 -> not called (proves the margin is what fires it).
**Deploy:** learner code, restart after `test_agent.py` passes. **Risks:** the size walk on a 23 GB tree (capped, null on timeout). **Size:** about 55 lines + 60 tests: small.

### S1-4. O1: a session-free watchdog and a Windows notification

**Files:** ADD `tools/ops/watchdog.py` (stdlib + `psutil` for the cmdline check, which the learner already needs; imports NOTHING from the learner), `tools/ops/watchdog.ps1`
(runs the python, and on ANY python failure writes `NEEDS YOU: watchdog could not run` and toasts itself), extend `tools/ops/install_ops_tasks.ps1`; tests in `selftest_ops.py`.

**Behaviour.** Task `Pokebot-Ops-Watchdog` every 30 min, user session only, hidden window, `MultipleInstances IgnoreNew`, 5-minute limit. Read-only on the clone. Each run:
- resolve the Desktop with `[Environment]::GetFolderPath('Desktop')` (OneDrive-redirected, fact 5); write via tmp + replace inside `try`, fallback copy in `%LOCALAPPDATA%\pokebot-ops\LEARNER-STATUS.txt`.
- append a sample `{t, free_gb_c, free_gb_e, alive, boot}` to `%LOCALAPPDATA%\pokebot-ops\samples.jsonl` (trimmed to 14 days atomically); this lives OUTSIDE the clone so it survives a wiped clone and is in O4's zip.
- State heads: `OK`, `NOTE: <why>` (the user's own `STOP`; a pending Windows restart; the PC just booted), `NEEDS YOU: <why>`. Second line: `checked 12:30 PM PT, next 1:00 PM` (12-hour LA time, `zoneinfo`).
- Checks (thresholds READ FROM the clone's `config.json`, never hard-coded): (1) learner process: a process scan for `learner.py` with `run`/`once`, re-checked once after 90 s (an exit-code-3 restart is a blink) -> `NEEDS YOU: learner is not running` unless `STOP` exists (NOTE) or the boot was under 15 minutes ago (NOTE: autostart delay); (2) `findings/ATTENTION.md` -> NEEDS YOU with its reason line; (3) stuck: `learner.log` age above `cycle_minutes + 60` min while alive (the log is silent during a batch, so this must track O2's longer cycles); (4) disk: free under 40 GB, or a fall over 10 GB in 6 h -> NEEDS YOU, else the forecast line "79 GB free; falling 6.0 GB/day; 25 GB in 9 days" (least squares over up to 72 h, at least 12 samples; "no downward trend" otherwise);
  (5) Windows restart pending (`winreg`: `RebootRequired`, `PendingFileRenameOperations`) -> NOTE; (6) unexpected shutdown: boot time moved since the last sample -> NOTE with downtime minutes (best-effort `wevtutil` for event 41); (7) `backup_status.json` older than 36 h or `ok:false` -> NEEDS YOU.
- Notify ONLY on a change of state code (state held in `watchdog_state.json`); one reminder per 24 h while NEEDS YOU persists; one "recovered" toast. Toast = `Windows.UI.Notifications.ToastNotificationManager` from Windows PowerShell 5.1 (Win11 Home has no `msg.exe`); falls back to the file alone.
  The file also prints how to restart: `run C:\Remote Projects\pokebot-learner\ai-agent\run_agent.ps1`. **Auto-restart is NOT built** (a policy choice for the user; it would make the watchdog a writer).

**Tests (`selftest_ops.py`).**
- W1 healthy fake tree -> first line `OK`, no toast.
- W2 FAULT lock/process dead -> after the re-check `NEEDS YOU: learner is not running`; REAL process control: `Popen([py, -c, sleep, "learner.py", "run"])` alive -> OK, then `.kill()` -> NEEDS YOU. CONTROL: `STOP` file -> NOTE and no toast.
- W3 FAULT `ATTENTION.md` -> NEEDS YOU carries its reason; CONTROL: a log line that merely CONTAINS the words "NEEDS YOU" changes nothing.
- W4 stuck: `learner.log` 14 h old with `cycle_minutes 720` -> NEEDS YOU; 11 h -> OK; 14 h with `cycle_minutes 1440` -> OK (kills a hard-coded 13 h mutant).
- W5 disk: synthetic samples at exactly -6 GB/day -> the text `falling 6.0 GB/day; 25 GB in 9 days` at 79 GB; a 12 GB drop in 6 h -> NEEDS YOU; flat -> no "falling".
- W6 notify-on-change: 3 runs in the same NEEDS YOU state -> the toast function is called once; recovery -> once more; 24 h later -> one reminder. FAULT mutant (notify every run) must fail.
- W7 boot grace: boot 5 min ago + no learner -> NOTE; 20 min -> NEEDS YOU.
- W8 `watchdog.ps1` with a nonexistent python -> status file says `NEEDS YOU: watchdog could not run`.
- W9 read-only: (path, mtime, size) of the whole fake clone identical before and after.
- Human step (cannot be automated, recorded in `07`): the user sees ONE real toast from `watchdog.ps1 -TestToast`, and says whether the hidden-window flash every 30 min is acceptable.

**Deploy:** no learner restart; the user approves `install_ops_tasks.ps1 -Apply`. **Risks:** alert fatigue (change-only + reminder), OneDrive sync churn from a 30-min file write (tiny; the fallback copy exists), false NEEDS YOU in the boot window (W7). **Size:** about 190 + 35 + 60 lines and 150 tests: medium.

### S1-5. A1: `tools/status.py`, a one-call check-in

**Files:** ADD `tools/status.py` (stdlib; reads the clone through `ops_config.json`); tests in `selftest_ops.py`.

**Behaviour.** One screen, at most 40 lines and 2.5 KB, `--json` for scripts, `--fetch` only when asked (default uses the LAST fetched refs and prints their age):
- CLOCK: `now 3:41 PM PT | started 1:10 PM | elapsed 2 h 31 m | ETA 5:10 PM` (`--started`, `--eta-minutes` optional), 12-hour LA time (N14).
- LEARNER: process and the watchdog's first line; `state.json` current tag, lanes, cycle end time and time left; failures; the last 3 cycles (`runs/usable`); `latest.json` (`runs, scored`, top 3 `ranked` with `n` and `mean`, top 3 `walls`, Champion count);
  inbox count and oldest age; the last consult outcome from `learner.log` (`consult: skipped ... queue`) and the last 3 `consult_log` exits (reachable or "failed, exit X"; it never calls Claude).
- OPS: disk and the forecast line, raw cycles vs archived and archive GB, last `archive-check`, last backup age and snapshot age, last `ops.jsonl` row.
- CODE: `running code <sig from the last 'learner started' line> vs clone <sig>` (fact 1; the signature function is COPIED (6 lines) and a test asserts it equals `learner.code_signature` on a temp dir, so drift fails) and `main checkout: N uncommitted, ahead A / behind B (fetched 3 h ago)`.
- WORK: newest 3 `PROJECT KNOWLEDGE/in-flight/*.md` (E1; absent today) with age; newest 3 `ai_player/evidence/*.txt` (name, last line; the verdict format is UNVERIFIED so it prints the raw last line); the AI frontier line from a one-line `PROJECT KNOWLEDGE/ai-frontier.txt` if D3 has made it; the last `cost-ledger.jsonl` row if P3 exists.
- Each section is wrapped: a failing section prints `unavailable: <reason>` and the rest still prints; exit code 0.

**Tests.** A-1 full fake tree -> every labelled field present, output under 2.5 KB with 20 cycles. A-2 FAULT zero-byte `state.json` and a truncated `runs.jsonl` -> other sections print, no traceback, exit 0, those sections say `unavailable`. CONTROL: a good tree prints no `unavailable`. A-3 pinned `--now`/`--started` gives the exact elapsed string. A-4 signature-drift test (above). A-5 read-only snapshot test.
**Deploy:** `tools/`, no restart. **Risks:** it reads a live learner's files mid-write (A-2). **Size:** about 170 lines + 90 tests: medium.

### S1-6. P3: `tools/usage_audit.py` and `PROJECT KNOWLEDGE/cost-ledger.jsonl`

**Files:** ADD `tools/usage_audit.py`, `PROJECT KNOWLEDGE/cost-ledger.jsonl` (append-only), `tools/story-dev/selftest_usage_audit.py` with a hand-written fixture transcript.

**Behaviour.**
- Discovery: `rglob("*.jsonl")` under every project folder named in `ops_config.json` (default the two Pokebot ones; fact 6), grouped by session, then by workflow (`wf_*` folder; name from the `meta.name` in `workflows/wf_*.json` `script`), stage = `workflowPhase`/`description` label from `meta.json`/`journal.jsonl`.
- **Count each API response once.** One response may span several transcript lines with the same `message.id`; key on it and take the max `output_tokens`. (A test builds exactly this.)
- Per agent: calls (assistant responses), tokens (input, cache write 5m/1h, cache read, output), `model` mix, tool calls by name. **Input-equivalent** = a constants block (cache read 0.1x, write 1.25x/2x, output weighted per the `06` 2026-10-15 definition; UNVERIFIED which weights that entry used, so the block cites it and the first report states the weights printed).
- Context-weight proxy by category, from each tool result's characters times the number of LATER responses in that agent: Read of `.py` / `.md` docs / evidence+logs, Bash `cat|sed|head|tail` / `grep|rg` / suite runs (`test|probe|selftest|gates`) / other. A Bash command is categorised by its FIRST real command token (after `cd x &&`), never by a substring.
- Cold re-writes: a response with `cache_creation` above half of the previous context after a gap over 300 s. Flags: agents over 150 and 200 calls, the 10 heaviest Reads, unranged Reads over 30 k characters, and **untemplated agents** (first prompt lacking the `<!-- stage-template:<role>@<ver> -->` marker, S2-3).
- Output: a 25-line report and ONE ledger line per workflow: `{key, rev, ts, session, workflow, stage_rows, agents, calls, ie_mtok, model_mix, categories, cold_rewrites, over150, untemplated}`. A re-run for the same key appends `rev+1`; readers take the newest. `--calibrate <ie_mtok> <percent>` appends a (meter reading, estimate) pair so "% of a week" becomes a fit over several readings, not the single 143M = 36 % point.
- Read-only on transcripts; stores numbers and a description capped at 80 characters, never prompt text. Malformed lines (a live transcript ends mid-line) are skipped and counted.

**Tests (fixture of about 14 lines: 2 responses, one split over 3 lines; a Read of `.py`; a `cat`; a `grep`; a suite; one malformed line).**
- U1 golden: exact calls, tokens, categories, `bad_lines 1`. U2 FAULT dedupe removed (monkeypatched key) -> tokens triple, golden fails. CONTROL: dedupe on.
- U3 categorisation: `git commit -m "cat the log"` is NOT `cat`; `cat file.log` is (FAULT and CONTROL in one).
- U4 cold re-write: gap 6 min + big write counts; gap 2 min with the same size does not (CONTROL).
- U5 append-only: two runs give rev 1 and rev 2 and the first line is byte-identical.
- U6 read-only snapshot of the transcript folder.
- U7 smoke on the REAL folder (not a gate): shares sum to 100 +/- 0.5 and the report prints the angle-2 reference numbers (.py Reads 33.4 %, Bash cat/grep 36.5 %, suites 7.6 %, evidence 2.2 %) beside its own, so the discrepancy that contradicts A2's premise is settled by a number.

**Deploy:** `tools/` only. **Risks:** a wrong proxy ranks the wrong lever; mitigated by U7 and by printing the weights. **Size:** about 230 lines + 130 tests: medium.

---

## STEP 2

### S2-1. N3 + A4 + P9: slim docs with byte budgets, built as a RATCHET

**Why a ratchet:** `04-HANDOFF.md` is 390,563 B and `03-PUNCH-LIST.md` 693,665 B; a hard 60 KB budget fails the gate today. So R8 ships GREEN at today's sizes and tightens as the sweep removes bytes.

**Files.** CHANGE `tools/story-dev/lint_docs.py` (add R8 beside R3, `:184-216`); ADD `tools/story-dev/doc_size_ceilings.json` (file -> ceiling bytes) and `long_line_waivers.json`
(file, sha1 of the line's first 60 characters, chars); ADD `tools/story-dev/archive_sweep.py` (driver over `archive_doc_block.py`); ADD `tools/story-dev/split_readme.py` (one-off, reuses invariant A);
CHANGE `ai_player/gates/prune_evidence.py:47`, `disk_budget.py:130`, `check_lessons.py:38-45`; ADD `32-PUNCH-LIST-ARCHIVE.md` (next free NN, R4); ADD `tools/story-dev/selftest_lint_docs.py`
(needs a `POKEBOT_DOCS_DIR` override in `lint_docs.py` so the test runs on a synthetic tree). Update `00-README.md`'s reading order (P4 pair).

**R8 behaviour (N3).** On the CURRENT-STATE files 01-05 plus `00-README.md` (and `ai_player/README.md`'s current part after the split): (a) `bytes <= ceiling` from the JSON; (b) every line is at most 1,200 characters, outside
fenced blocks (`_blank_fenced`) and table rows (a leading `|`), unless waived by hash; a waived line may only SHRINK; (c) a waiver whose line no longer exists is reported stale; (d) **the ceilings and waivers may only shrink versus `git show HEAD:`**
(a worktree value above the committed one fails). `lint_docs.py --ratchet` lowers each ceiling and never raises one. [CRITIC: it lowers to max(target, current size + headroom), headroom 8 KB a
file in the JSON, never to the exact current size: at exactly-current every next doc edit fails, and the cheapest way to pass is to trim a
caveat (CLAUDE.md rule 2). A ceiling may RISE only with a `raised` entry (date, bytes, why) in the JSON; the lint prints every raise, so
Tier 1 sees it in the diff.] Targets (handoff about 60 KB, README current part about 90 KB; `03`/`05` decided after the first sweep measures) are printed as "over target by X", non-fatal until the ceiling reaches them.

**Sweep behaviour (A4).** `archive_sweep.py --source <file> [--apply]`: lists blocks that R7 already defines as closed (a `###` section whose heading says done and which holds no `- [ ]`/`- [~]` and is not `MIXED`/`STILL OPEN`), the byte saving each, then (with `--apply`) calls `archive_doc_block`'s move function
(invariants A-D) for each with an auto pointer that **keeps every slug** (`` `#slug` `` and every `KI-n` named in the block) so `grep '#slug'` still lands on a pointer. Dry run is the default. It never splits a table row; a prose mega-line is split only at the last `. `/`; `/` - ` before 1,200 characters into indented continuation lines, and only if the whitespace-normalised join equals the original.
Archive targets: closed `03` items to `32-PUNCH-LIST-ARCHIVE.md`; old `04` blocks to the existing `28-HANDOFF-ARCHIVE.md`. The `CLAUDE.md` half of A4 is NOT part of this spec (angle 2 demoted it; <2 % of a 600k context).

**Split behaviour (P9).** `split_readme.py` reads an explicit allowlist of `##` headings that stay (Run it, Layout, Purity contract, Known limits, ...: the list is written from the real README by the builder, UNVERIFIED here), moves every other section verbatim, in order, to `ai_player/readme/NN-<slug>.md`, and leaves one line per moved section:
`> moved: <heading> -> readme/NN-<slug>.md`. Invariant A (no non-blank line lost) is checked before writing. The three consumers above gain `ai_player/readme/**/*.md`; `check_lessons.DOCUMENTS["README"]` becomes the concatenation of README plus `readme/*.md` so a lesson's quoted text still resolves wherever it moved. Until the split lands, `tools/bgrep.py` (hit plus 120 characters, capped, `--line N` to expand) keeps greps off the long lines.

**Tests.**
- R8-1 FAULT: a 1,300-char line appended to a synthetic `04` -> exit 1, message names file and line. CONTROL: the same text inside a fenced block, and as a table row -> exit 0 (the mention rule).
- R8-2 FAULT: file 1 KB over its ceiling -> fail; at the ceiling -> pass. R8-3 FAULT: a waived line grows by one character -> fail; shrinks -> pass. R8-4 FAULT: a ceiling raised against `HEAD` with no `raised` entry -> fail; CONTROL [CRITIC]: the same raise WITH a `raised` entry -> pass, printed. R8-5 `--ratchet` lowers and never raises (run twice, second is a no-op).
- S-1 dry run leaves the tree byte-identical (hash). S-2 a closed block moves and every slug it held is still found in the source by grep (FAULT: a pointer written without the slug fails the sweep's own post-check). S-3 an `✅`-headed section that still holds `- [ ]` is NEVER selected; a `MIXED` heading is never selected (CONTROL: the same text with the open item removed IS selected). S-4 `lint_docs.py` and `audit_doc_consistency.py` pass on the synthetic tree after `--apply`. S-5 split-line join equals the original.
- P9-1 evidence citation: a synthetic evidence file cited ONLY from `readme/step-x.md` -> `prune_evidence.py` dry run lists it KEEP (cited). FAULT mutant: `CITING` without the new glob -> it is listed INDEX AND DELETE (proves the test can fail, and names the data-loss path). P9-2 `check_lessons` still finds a quote that lives in a history file; mutant `DOCUMENTS` without the folder -> fails. P9-3 `disk_budget.citing_text()` includes history text. P9-4 concatenated sections before == after (ordered, no loss).
- Final acceptance (measured): handoff <= 60 KB by cold `wc -c`, `lint_docs` and `audit_doc_consistency` exit 0, and a cold-start agent (Tier 2) can still answer the seven quality-bar questions from the shorter file.

**Deploy:** docs and tools, no restart; one sweep per commit with explicit paths (CLAUDE.md rule 1). **Risks:** a moved item missed (slug-preserving pointers, S-2/S-3), the citation scan (P9-1), waiver sprawl (shrink-only, R8-3/4), `audit_doc_consistency` counts. **Size:** R8 about 70 lines, sweep about 120, split about 100, consumer edits about 25, tests about 260: medium-large in total, splittable into three commits.

### S2-2. O5: a novelty gate on the consult and a rolling `DEVELOPER-NOTES.md`

**Files:** CHANGE `ai-agent/consult.py` (`maybe_consult :62-111`), `ai-agent/learner.py` (`read_inbox :277-294`, call `consult.roll_notes` from `finish_cycle`), `ai-agent/config.json`, `ai-agent/test_agent.py`.

**Behaviour.** Order stays: enabled -> daily cap -> waiting-proposals cap -> NEW novelty -> claude.
- Digest from `findings/latest.json` (fresh: `report.write` runs before the consult, `learner.py:388-389`): `top3 = ranked[:3].genome`, `walls` shares (count over total), `scored`. State in `data/consult_state.json`.
- Consult when: no previous digest, OR top 3 differs, OR any wall share moved `>= wall_move_points` (3.0, raw difference, not rounded buckets, which flap at edges), OR `scored` grew `>= new_runs` (**150, not the backlog's 40**: a 12-lane cycle yields about 38-41 usable games, so "40 new runs" fires nearly every cycle and the gate would do nothing), OR `forced_days` (7) passed. **Any error reading or parsing the digest FAILS OPEN** (consult proceeds) with a logged reason.
- A skip logs to `learner.log` only, and writes `data/consult_skips.jsonl`, **never `consult_log.jsonl`** (fact 3).
- Repeat collapse: key terms = `KI-\d+`, wall names from `latest.json`, `POKEBOT_\w+`. If the new note's term set has Jaccard >= 0.6 with each of the last 2 notes, append ONE line `- <date>, after <tag>: unchanged since <date of last distinct note> (N consults)`; the full reply is already kept in `findings/claude-<tag>.md` (`:89`), so nothing is lost.
- `roll_notes`: keep the newest 5 full entries in `DEVELOPER-NOTES.md`, move the rest verbatim to `DEVELOPER-NOTES-ARCHIVE.md`, run at every cycle end regardless of whether a consult happened (so the current 35 KB file shrinks at once, not at the next consult).
- Proposals: in `read_inbox`, move a proposal older than `proposal_ttl_days` (3) or whose `genome_id` equals another waiting one into `inbox/expired/` with a `.why.txt` (not deleted). Note `cmd_plan` calls `read_inbox` too, so `plan` gains this side effect, as it already has for invalid files.
- Dev probe (one-time, about 2 cheap calls): does `claude -p ... --setting-sources user` still load the repo `CLAUDE.md`? `consult.py --probe-context` runs `claude -p "Reply OK" --output-format json` from the repo and from an empty temp dir with `--add-dir <repo>`, and prints the difference in total input tokens (cache read + write + input). The flag behaviour is UNVERIFIED until the probe runs; record the number in `06`. [CRITIC: the follow-up NEEDS DESIGN. The source spec switched the consult's `cwd` to a temp dir when the repo run is about 10k tokens larger (CLAUDE.md is 38.9 KB); that also removes the project's rules (e.g. "agreement is not a confidence signal") from the consult's context and may change proposal quality. The switch is a separate `06` decision after an A/B on proposal quality: the probe ships in this item, the switch does not.]

**Tests (existing sentinel technique on `shutil.which`).**
- N1 digest unchanged -> `consult: skipped, nothing new since ...` and Claude NOT reached. N2 FAULT/CONTROL top 3 changed -> proceeds (reaches the `not on PATH` line, like C4).
- N3 wall share moved 2.9 points -> skip; 3.1 -> go (boundary both ways). N4 `forced_days`: 8 days -> go; 6 days -> skip.
- N5 FAULT a skip must not consume the cap: after 5 skips `_calls_today` is still 0. N6 corrupt `latest.json` and corrupt `consult_state.json` -> proceeds (fail open).
- N7 7 notes -> 5 in the file and 2 in the archive, and file + archive text equals the original (no loss). N8 same-terms note -> one line under 200 characters; a note with a NEW `KI-` id -> full paragraph (CONTROL).
- I3 proposal aged 4 days -> `expired/`, aged 2.9 days stays; I4 duplicate genome -> `expired/` (CONTROL: distinct genome stays).
- Replay (measured, in `07`): run the gate over `runs.jsonl` for the consults since 2026-10-11; expect it to skip most of the repeats and fire where the top 3 changed (the share is UNVERIFIED until run; `latest.json` is not stored per cycle, so the digest is recomputed from `runs.jsonl` with `brain.summarize`).

**Deploy:** learner code, restart after the suite passes. **Risks:** a missed real change, bounded by the weekly force, the 150-run and top-3 rules and fail-open. **Size:** about 90 lines + 110 tests: small-medium.

### S2-3. Stage templates: P11 + P1 + N6 + P10

**Files.** ADD `tools/workflows/templates/{recon,build,sweep-analysis,verify,doc-check}.md`, `tools/workflows/models.json`, `tools/workflows/render.py`, `tools/workflows/lint_templates.py`, `tools/workflows/stage_helpers.py` (N6), `tools/workflows/regression_due.py` and `tools/workflows/suite_map.json` (PR-2); ADD `tools/story-dev/selftest_workflows.py`. Source material: the existing workflow scripts are recoverable from `<session>/workflows/wf_*.json` `script` (fact 6), so the templates start from prompts that ran, not from imagination.

**Behaviour.**
- A template carries required fields: `GOAL, READ-LIST (path[:start-end]), DO-NOT-READ, STOP, RETURN-CAP (under 200 words plus a file path), MODEL, WAIT-RULE, MAP-FIRST, LOOKUP-FIRST` and a header marker `<!-- stage-template:<role>@<ver> -->`. The standing DO-NOT-READ: `ai_player/evidence/`, `**/INDEX.md`, whole `07`/`08`, `ai_player/README.md` whole. WAIT-RULE (P1): never wait inside a big context; start the run as a background script, write the note (`PROJECT KNOWLEDGE/in-flight/<run>.md`, E1) and finish; past 150 calls write the note and hand back.
- `render.py` fills `{{placeholders}}` and **refuses** an unresolved one or an empty required field.
- `lint_templates.py`: all fields present; every READ-LIST entry that points at a file over 30 KB carries a range (size read from disk); DO-NOT-READ holds the standing entries; RETURN-CAP parses and is at most 200 words; `MODEL` is `top|mid|cheap` and agrees with `models.json`; **a stage below `top` must name a `proof` that passes the plant check** (P10). [CRITIC: the source spec accepted any file containing the marker `PLANT-CAUGHT`, which anyone can type: a vacuous gate. The proof is the JSON the plant run writes: at least 3 planted defects of different kinds, each with an id, the cheaper agent's findings, and one CLEAN control input; the lint passes it only if every planted id is in the findings AND the control has zero findings. One caught plant is N = 1, and agreement is not a confidence signal.] `models.json` ships with every stage at `top`, so nothing changes until a plant test earns a move. Plant tests (a doc with a planted P1 inconsistency, a diff with a planted bug) are run as a small workflow by Claude, one cheaper-tier agent per stage; this is the only part with a token cost, and the adversarial verify stays top tier by rule.
- N6 `stage_helpers.refix_decision(verifier_json_path)` returns one of `PASS` (no refix), `REFIX` (the JSON parses, `all_pass` is the boolean `False`, `FAILURES` is a non-empty list) or `UNKNOWN` (missing file, bad JSON, `all_pass` absent or the string `"false"`, empty `FAILURES` with `all_pass: false`): **UNKNOWN means ask a human, never PASS**.
- `regression_due.py`: for each suite in `suite_map.json` (suite -> globs), read the newest evidence file's tree digest with `provenance.code_digest` (`provenance.py:126`) and list the suite when the digest differs from the current tree AND `git diff --name-only <evidence commit>..HEAD` intersects its globs; "never run" is listed too. (UNVERIFIED which provenance function yields the CURRENT tree digest; the builder reads `FrozenTree`/`snapshot_tree` first.)
- **Compliance is measured, not assumed:** nothing can force a future ad-hoc workflow script to use the templates, so P3 reports "untemplated agents" per workflow (S1-6) and `.claude/commands/orchestrate.md` is edited to name `tools/workflows/` as the only prompt source.

**Tests.** T-1 FAULT each required field removed in turn -> lint fails naming it (10 cases); CONTROL: the full template passes. T-2 FAULT an unranged READ-LIST entry for a 600 KB file -> fail; a ranged one or a small file -> pass. T-3 FAULT `MODEL: mid` with no proof -> fail; [CRITIC] a proof missing one planted id, a proof whose control has a finding, or only 2 plants -> fail; CONTROL: 3 plants all found and a clean control -> pass. T-4 mention control: the words "DO-NOT-READ" or "MODEL" inside a code fence or in a template's prose must not satisfy or break a field check. T-5 `render.py` refuses an unresolved placeholder. T-6 `refix_decision`: the six JSON shapes above (including the string `"false"` and a missing file) map to the stated verdicts. T-7 `regression_due`: changing a covered file lists its suite; changing only a doc does not (CONTROL); an unknown glob in `suite_map.json` is an error, not silence.

**Deploy:** `tools/`, no restart. **Risks:** ossified templates (P3 shows it), a weaker tier missing a defect (the proof gate), a verifier that forgets the JSON (UNKNOWN). **Size:** templates about 5 x 40 lines of text, code about 60 + 80 + 50 + 90 lines, tests about 140: medium-large; split into P11+P10, N6, and regression_due.

---

## Summary

| Spec | Touches learner code (restart after tests) | New code, lines | Tests, lines | Size |
|---|---|---|---|---|
| O3 compress | yes | 85 | 95 | small-medium |
| O4 backup | no | 120 | 90 | small-medium |
| O6+O7 ledger and margin | yes | 55 | 60 | small |
| O1 watchdog and toast | no (needs the user's OK for tasks) | 285 | 150 | medium |
| A1 status | no | 170 | 90 | medium |
| P3 usage audit | no | 230 | 130 | medium |
| N3+A4+P9 slim docs | no | 315 | 260 | medium-large |
| O5 novelty gate | yes | 90 | 110 | small-medium |
| Templates P11+P1+N6+P10 | no | 280 plus 200 text | 140 | medium-large |

Total about 1,600 lines of code and 1,100 of tests. Learner-code items (O3, O6+O7, O5) should ship as ONE reviewed commit train with a single restart each, not interleaved.

## Needs the user (plain-English calls only)

1. Registering two Windows scheduled tasks (a nightly backup, a 30-minute status check) on the user's PC.
2. Backup target: E: (a different physical disk, 47 GB free) is the default; Z: (181 GB, a spinning disk) is the alternative.
3. Keep the compressed raw logs forever (about 1-2 GB a month)? Recommended yes: they are the bot's game history the AI will learn from.
4. Should the watchdog ever restart a dead learner by itself? Not built; the status file will say how to restart it.

## What I did not verify

The `.log` compression ratio (only `stdout.txt` was measured); whether lane profiles hold anything A6 needs; the `06` input-equivalent weights; the verdict format of `ai_player/evidence` files; whether `claude -p` loads `CLAUDE.md`; the `wf_*.json` fields other than `runId`, `timestamp` and `script`; the exact current-tree digest function in `provenance.py`; and that Windows PowerShell 5.1 toasts show for a scheduled task on this PC (a human check).

## Critic's ledger (2026-10-19)

| Spec | Verdict | What changed |
|---|---|---|
| S1-1 O3 compress | KEPT, fixed | no delete without a verified archive, even under 2 GB (pause instead); the kill test needs no env switch in learner code; the manual `archive` takes the lock (R11); canary settings by commit, never in the clone |
| S1-2 O4 backup | KEPT, fixed | status file outside the clone, `-B`; snapshot size measured before its first commit |
| S1-3 O6+O7 | KEPT, fixed | O7 never ships before O3, and its test asserts ARCHIVE, not delete; `psutil` imported lazily |
| S1-4 O1 watchdog | KEPT | auto-restart stays unbuilt (the user's call); the toast is a human check |
| S1-5 A1 status | KEPT | none |
| S1-6 P3 usage audit | KEPT | none |
| S2-1 N3+A4+P9 | KEPT, fixed | ratchet with headroom and recorded raises, so no gate rewards trimming a caveat |
| S2-2 O5 | KEPT; one part NEEDS DESIGN | the probe ships; the consult `cwd` switch is a separate decision after an A/B |
| S2-3 templates | KEPT, fixed | a model move needs a plant-run JSON (3+ plants and a clean control), not a typed marker |

Spot checks (grep, 2026-10-19), all CONFIRMED: `ai-agent/learner.py:150-153` `code_signature` globs top-level `*.py` only;
`tools/story-dev/run_gates.py` holds no `test_agent` (0 hits), so the suite must be run by hand before a learner commit;
`ai-agent/consult.py:46` counts every line starting `{"day": "<today>"` (why O5's skips must not be logged there).
