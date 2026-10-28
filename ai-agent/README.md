# Emerald AI: the strategy learner (v1)

> ⛔ **What this is, and what it is NOT (USER RULING 35, 2026-10-03).** This learner tunes the STORY BOT's strategy
> settings while the bot plays. It is TEACHER-side: knowledge of which strategies work, plus a corpus of games. It
> is NOT the AI player.
>
> The AI version must play the game ITSELF (navigation, battles, menus, decisions) with no bot code and no bot-like
> behaviour. The bot's logic, scripts and docs only teach it. The AI player is still to be designed
> (`#28-aiagent-v2`; `HUMAN-PLAY-DESIGN.md`).

> ⭐ **THE ULTIMATE GOAL (the user, 2026-10-03): play Pokémon Emerald the way a PERSON does.** That means the story,
> catching Pokémon along the way, picking up items, exploring, training sensibly and the Pokédex, looking and acting
> as human as possible, and **never a robotic speedrun**. The progress score below is only part of that. `LATEST.md`
> shows human-like signals beside it and flags strategies that play less like a person. Never optimise progress at
> their expense.

**What it is.** The first stage of the AI version of this project. It runs 24/7 on this PC with no AI credits. It
plays real Pokemon Emerald games through the story bot's own engine, measures which STRATEGIES get furthest, keeps
the winners and tries new combinations. What it learns is written down for Claude to read and act on.

**What v1 learns, honestly.** The story bot already knows how to play: walking, battles, menus, the story. v1 does
not relearn that. It learns the strategic choices the story bot exposes as settings ("knobs"): when to catch new
species, when to restock, how to use healing items, and so on. These choices are where runs currently fail. A
whole-game AI that decides moment to moment is the later stage. This stage builds the data, the loop and the
measuring stick that stage needs.

**Where it stands at the start.** It begins from the 78 runs of step 14's 13-hour batch (2026-10-01). Of the 62
runs that finished, 11 became Champion. Most others ended at Tate & Liza, Norman, or the Elite Four door, refused
for a short basket of healing items or a team below the level floor.

## Where it runs: its own copy of the project

The learner runs from a **separate full clone**, `C:\Remote Projects\pokebot-learner`, never from the development
checkout. The reason: the batch runner abandons a cycle when the checkout's commit (HEAD) moves mid-batch, so results
can never mix two versions of the bot. On 2026-10-03 a docs-only commit in the development checkout killed a 12-hour
cycle 10 minutes in. In its own clone, HEAD moves only when the learner itself updates, between cycles.

- **Deploying a change:** commit and push to `main` as usual. Between cycles, the learner fast-forwards its clone
  to `origin/main` (`auto_update`; the only git it ever runs). If its own code changed, it re-runs `test_agent.py`
  and restarts into the new code only if that passes.
- The clone holds a git-ignored `DEPLOYMENT` marker. `run` and `once` refuse to start anywhere else, so two
  learners can never run from two checkouts (`--dev` overrides, for smoke tests only).
- The clone needs two untracked things the repo does not carry: the emulator library `sandbox-pokebot/mgba/` and
  one lane-profile template, `sandbox-pokebot/profiles/endless-P1-torchic/metadata.yml` (the ROM binding). Both were
  copied in when it was set up.

## Start, stop, check

Run these in `C:\Remote Projects\pokebot-learner\ai-agent`, the deployment clone:

| to... | do this (PowerShell, in that folder) |
|---|---|
| start it 24/7 | `.\run_agent.ps1` (keep the window open; the PC must not sleep) |
| after a reboot or power cut | it starts ITSELF 2 minutes after the user logs on: Task Scheduler task `Pokebot-AI-Learner-Autostart` (added 2026-10-15). A second start is harmless: the learner holds a lock, and the wrapper stops on exit code 2 (tested live). It returns by itself after a power cut only if the PC powers back on (BIOS "restore on AC power loss") and logs in (Windows auto-login), which is the user's choice. When training ends, DISABLE it, never delete it: `Disable-ScheduledTask -TaskName Pokebot-AI-Learner-Autostart`; re-enable it with `Enable-ScheduledTask -TaskName Pokebot-AI-Learner-Autostart` |
| stop it cleanly | create a file named `STOP` here: `New-Item STOP`. The running cycle finishes first, up to 12 hours |
| see where it is | `py -3.12 learner.py status` |
| see what it learned | open `findings\LATEST.md` (rewritten after every cycle) |
| preview the next cycle | `py -3.12 learner.py plan` (runs nothing) |
| check the raw-log archives | `py -3.12 learner.py archive-check` (read-only, any time: one `OK`/`BAD` line per `raw.zip`, then one `HELD <tag> <reason>` line per cycle held for review; exit 1 on any BAD or HELD; the result goes to `data\archive_check.json` for `tools/status.py`) |
| archive old raw logs now | `py -3.12 learner.py archive` is meant for when the learner is STOPPED. It refuses while the 24/7 learner holds its lock (the running learner archives at each boundary by itself). If the learner is started while a manual archive runs, it WAITS for it instead of refusing. After 120 min it gives up: it writes `findings\ATTENTION.md` with that reason and exits 2, which `run_agent.ps1` reports as "Another learner is already running" (it is not) and does not retry |
| check the code still works | `py -3.12 test_agent.py` (offline, about 1 minute, must say ALL PASS) |

If it ever stops on its own, `findings\ATTENTION.md` says why. Fix the cause, delete that file, start it again
(what to do for each reason: "When it stops itself" below).

If the learner process dies mid-cycle, the batch keeps playing. The next start ADOPTS it: it waits for the batch to
end, then scores it.

## Crashes, power cuts and half-written files (backlog E2 + O8, 2026-10-28)

**The game journal (E2).** While a batch runs, the learner records every game that has FINISHED in
`runs\<tag>\games.jsonl`, about every 5 minutes (`JOURNAL_POLL_S`). One line per game: `{"journaled": <time>, "rec":
<the exact runs.jsonl row that game will get>}`. A game counts as finished when its log is not the newest one of its
lane and has not changed for 2 minutes (`JOURNAL_STABLE_S`). A restarted learner that is waiting for a still-running
batch keeps journaling it.
- At a NORMAL cycle end nothing about the scoring changes: the batch's own log copies are scored exactly as before,
  and `learner.log` says `<tag>: game journal: N of N journaled games match the batch's records` (a mismatch names
  the games that differ; the records are never altered). The journal is then deleted (everything is in runs.jsonl).
  If it holds a game that runs.jsonl does not (the cycle's parse or recovery failed), it is KEPT as
  `games.jsonl.kept` and `learner.log` says so: it may be the only whole record of those games.
- If the MACHINE dies mid-cycle (a power cut, a shutdown), the batch runner never copies the lanes' logs into
  `batch\`. Before 2026-10-28 the next start then recorded 0 runs for that cycle (ai0031 lost 12 finished games on
  2026-10-17). Now it scores the games from the lane profiles (`sandbox-pokebot\profiles\endless-<tag>-*`), by
  today's rules: each lane's newest game was cut off, so it is kept but not scored. For each game the journal holds,
  the journal's record is used, because the journal read that log while it was whole. The cycle row says
  `"recovered": "<n> from lane profiles, <m> from the journal"`. Like any cycle with a scored game, it counts in the
  ranking, uses up the inbox proposals it tested and resets the failure count (USER RULING 48, U1). Old cycles are
  NOT backfilled (U2).
- A learner that died between writing runs.jsonl and saving state.json re-scores the same cycle at the next start;
  rows already in runs.jsonl (same source, batch, lane and log) and an existing cycles.jsonl row are not written twice.

**Half-written files (O8).** Every file the learner rewrites is written to a `.tmp`, forced onto the disk, then put
in place; appended lines are forced onto the disk too.
- A broken line in a `.jsonl` file is skipped (and logged) instead of stopping the learner. At each start the
  learner moves broken lines of `data\runs.jsonl` and `data\cycles.jsonl` into `<file>.bad` (one JSON object per
  line: when found, the file, the line number and the text) and rewrites the file without them, the good lines byte
  for byte. More than 3 broken lines (`MAX_BAD_LINES`) is not a torn write: it repairs nothing and stops with
  ATTENTION (restore that file from the nightly backup). A broken line in a journal goes to `games.jsonl.bad`, with no
  limit and never a stop.
- `data\state.json.bak` is a copy of state.json, rewritten right after every save. If state.json is unreadable or
  missing, the backup is used ONLY when it is provably current: it must read cleanly AND its `cycle` must be at least
  the newest cycle ever started (the highest `runs\aiNNNN` or `endless-aiNNNN-*` folder). Then the bad file is kept as
  `state.json.bad.<k>` and state.json is restored from the backup (the newest cycle's archive flags and failure count
  may be one save old; a lost cycle end is redone by adopt and not double counted). Otherwise the learner REFUSES
  (`StateUnreadable`: "state.json.bak holds cycle 47 but runs\ai0053 exists") and, after 5 such starts, stops with
  ATTENTION. A backup is stale after a rollback to code older than 2026-10-28 (that code never writes it) until the
  first save of the new code.
- `config.json` has no fallback: it is a human's file, and guessing is worse than stopping.

**The crash-loop breaker (O8).** A crash in the learner's loop, from the moment it holds its lock and has logged
`learner started`, is counted in `data\crashes.json` (`{count, first, last, last_error}`; kept outside state.json,
which may be the broken file). NOT counted, and so never stopped by the breaker or reached by its update step: a
crash before that point (an import error in the learner's own code, a failure taking the lock, reading the code
signature or writing that first log line, e.g. a full disk). `run_agent.ps1` retries those every 10 minutes, as
before O8; a full disk is the watchdog's to report.
- Crashes 1-4 in a row: the learner exits 1 and `run_agent.ps1` retries 10 minutes later, as before.
- Crash 5 (`CRASH_LIMIT`): it writes ATTENTION ("The learner crashed 5 times in a row and stopped retrying. Last
  error: ..."), resets the count and exits 0, so the wrapper stops. The watchdog toasts "the learner paused itself"
  within 30 minutes. About 40 minutes from the first crash.
- While crash-looping it still fetches pushed code: if `auto_update` is on and the fetch brings new learner code, it
  restarts into it when `test_agent.py` passes (the count is kept); if the tests fail it stops with ATTENTION instead
  of running untested code.
- The count resets when a batch is launched, when the breaker writes ATTENTION, and on any clean exit (STOP,
  ATTENTION, a restart into new code). `learner.py once` crashes are never counted.
- ATTENTION.md is checked FIRST at every start, so the logon autostart cannot restart a stopped crash loop.
- `learner.py status` shows `crashes in a row: n`.

### When it stops itself (ATTENTION.md): what to do

| ATTENTION says | do this |
|---|---|
| "crashed 5 times in a row" | read the tracebacks in `data\learner.log`. A code change: revert it and push (it arrives at the next start, or roll back by hand below). A broken `data\state.json`: restore it from the nightly backup. Then delete ATTENTION.md and start `run_agent.ps1` |
| "data/runs.jsonl (or cycles.jsonl) has more than 3 unreadable lines" | restore that file from the nightly backup (`tools/ops/backup_learner.py` keeps `data\`), or move the bad lines out by hand; then delete ATTENTION.md and start |
| "the update it fetched FAILS test_agent.py" | fix or revert the code on `origin/main`, then delete ATTENTION.md and start |
| "cycles in a row produced no scored runs" | read `data\learner.log` and the newest `runs\<tag>\x4.out.txt` |
| a disk message | free disk space |

**Manual rollback** (when the learner has already stopped, or its update step is what is broken). A normal revert
and push arrives by itself at the next cycle boundary, or at the next crash. By hand:
1. `git -C "C:/Remote Projects/pokebot-learner" fetch origin`
2. `git -C "C:/Remote Projects/pokebot-learner" merge --ff-only origin/main`
3. Delete `ai-agent\findings\ATTENTION.md`.
4. Start `run_agent.ps1`.
After a rollback to code older than 2026-10-28, `state.json.bak` stops being written; on a redeploy it stays stale
until the first save, and the check above refuses it in that window.

## One cycle (12 hours by default)

1. **Size itself to the PC.** Lanes are parallel games, in fours: one per starter (Torchic, Mudkip, Treecko,
   random) for each strategy. Default: as many as the CPU and memory allow, at most 24 (six strategies), keeping 4
   threads and 8 GB free. An open bot window costs one thread. If another batch or harness drive is running, the
   learner waits instead of competing.
2. **Pick strategies** (`brain.py`):
   - the current best (the control);
   - a proposal from `inbox/`, if one is waiting;
   - the next rows of a **screening design** (`design: pb12`).
     - This is a 12-strategy Plackett–Burman pattern. Every knob is ON in exactly 6 of the 12, and every pair of
       knobs is ON together in exactly 3, so each knob's own effect is measurable.
     - Step 14 changed all 11 knobs at once, which made them inseparable.
   - With any other `design` value, the old way: a Thompson draw (an underrated strategy with few runs), then
     mutants of the best.
3. **Play.** Real games, through `tools/story-dev/x4_headless.py --arms`. That runner refuses a misspelt knob, a
   duplicate strategy or a bad lane split before any game starts.
4. **Score** (`scoring.py`): each run becomes a small record.
   - Score = progress out of 13 (8 badges, 4 Elite Four, the Champion).
   - Per boss: losses, whether it was beaten, and the team just before the first loss and before the win.
   - The order and timing of each first win; every derail; money after the last battle.
   - A run the time limit cut off is kept but not scored.
   - `learner.py reparse` re-reads every batch whose raw logs still exist after a parser upgrade (not yet the
     archived ones; a batch whose logs are missing keeps its old records, test R9).
5. **Learn and report** (`report.py`): `findings/LATEST.md` holds:
   - the strategy ranking;
   - what each knob seems worth (a regression);
   - where runs end, with hints from `05-KNOWN-ISSUES.md`;
   - questions for Claude.
6. **Ask Claude** (`consult.py`; ON since 2026-10-03, at most 2 calls a day; see below).
7. **Archive** (backlog O3, built 2026-10-21). The newest `keep_raw_cycles` cycles (4 since 2026-10-22; `config.json`) keep their raw logs as
   files. Each older cycle is zipped to `runs/<tag>/raw.zip`, with `raw.manifest.json` listing every file's name,
   size and CRC32. The zip holds BOTH halves of the cycle:
   - `batch/...`: the cycle's `runs/<tag>/batch/` (measured 1.3-1.7 GB);
   - `profiles/<profile>/...`: every file of each of its lane profiles (`sandbox-pokebot/profiles/endless-<tag>-*`,
     about 46 MB each, one per lane: 12-16 a cycle). Most of a profile is its debug logs, byte-identical to the copies in `batch/`;
     the rest is found nowhere else: `badge-log.json` (the team and levels at every badge, the AI's experience
     data, backlog A6), `stats.db`, the saves, the screenshots and the profile's settings.
   - A profile file whose file name, size and CRC32 equal a `batch/` file's is not stored twice: its manifest entry
     says `"dup_of": "<that batch member>"`, and verification checks that member is in the zip with that size and
     CRC32. Every other file is stored.
   - Measured 2026-10-21 on a scratch copy of ai0024 (its batch and 16 profiles): 306 files (96 batch, 210 profile),
     2,469 MB -> 96.7 MB (25:1) in 24 s. Of the 210 profile files 134 were stored and 76 (every debug log) were
     `dup_of`; an independent sha256 read-back of all 306 originals (the `dup_of` ones through their targets) matched.
     The batch alone, before profiles were archived: ai0038, 73 files, 1,303 MB -> 68.6 MB in 16 s.
   - The zip is VERIFIED (every member's CRC equals the CRC read from the original, every `dup_of` target matches)
     before anything is deleted. Then `batch/` and the cycle's lane profiles are deleted. **No original, batch or
     profile, is deleted unless its exact bytes (name, size, CRC32) are in a verified archive, stored or through
     `dup_of`; no archive file is ever overwritten or deleted.** Before 2026-10-21 (re-verify F6) the profiles were
     deleted unarchived; cycles pruned before then have no profile files in any archive.
   - A cycle is archived only once it is QUIET: no batch runner or lane process (`endless-<tag>-`) names it and no
     original, in `batch/` or in a profile, changed in the last 60 minutes (`QUIET_MINUTES`). Otherwise it is skipped
     until a later boundary. If an original changes while it is being archived, nothing is deleted.
   - **Accepted residual risk.** The last check that nothing changed and the delete are two steps. A write that lands
     between them is deleted with its file. Measured on a batch shaped like a real one (96 files, 1.6 GB): 0.16 ms
     from that check to the start of the delete, 118 ms to its end (measured before profiles were archived; the delete
     now also removes the cycle's profiles, so it ends later). It needs a writer that was silent for 60 minutes,
     holds no open handle on the file, and has no command line naming the cycle. The fix (rename the folder away,
     re-check the renamed tree, then delete) is not built.
   - A cycle with no file in `batch/` but files in its profiles archives those files; only a cycle with no file
     anywhere has its empty folders deleted without an archive.
   - At most `max_archives_per_prune` (3) cycles a boundary; a failure is logged, the raw logs stay, and the next
     boundary retries. A killed archive leaves only a `raw.zip.part`, removed next time. Links and junctions inside
     `batch/` or a profile are neither archived nor followed.
   - A `raw.zip` that cannot be trusted while every original is still on disk is SET ASIDE as `raw.zip.bad.<k>` (with
     `raw.manifest.json.bad.<k>`), and the originals are archived afresh. A set-aside file is never overwritten,
     renamed or deleted; delete them by hand only after checking them.
   - **HELD for review.** When the learner cannot prove a cycle safe, it touches NOTHING of that cycle and logs
     `HELD FOR REVIEW` once, then `held for review: <tags>` each boundary. It keeps running. The cases are: a delete
     that stopped part-way (so `raw.zip` is the only copy of some files) whose remaining originals changed or gained
     a file, or whose `raw.zip` no longer verifies; an unreadable `raw.manifest.json`; a `runs/<tag>/batch` that its cycle's `created` list does not name;
     and a `batch` or a lane profile that is a link, a junction or a file. `learner.py archive-check` lists them (exit 1), `learner.py status` and
     `tools/status.py` count them. To release a cycle: stop the learner, inspect and fix that folder, remove the
     cycle's `"held"` entry from `data\state.json`, and start the learner again.
   - Archives are kept forever (`keep_archive_cycles: 0`; any other value is reserved and does nothing yet). They
     are the AI's experience input (backlog A6): `zipfile.ZipFile(path).open("batch/L01/debug-logs/<x>.log")`, or
     `.open("profiles/<profile>/badge-log.json")`. A reader that wants a `dup_of` file opens its `dup_of` member.
   - The run records in `data/runs.jsonl` are kept forever, as before.
   - **Early archive** (backlog O7, 2026-10-21). Before each cycle, if free disk is under `min_free_gb` +
     `early_prune_margin_gb` (25 + 15 = 40 GB), the same archive runs with only the newest 2 cycles kept raw, at
     most `max_archives_per_prune` a pass (it runs again at the next pass, idle waits included). It IS the archive
     above, so it never deletes without a verified zip and skips held and still-busy cycles. Why: it archives while
     there is still room to write zips, long before the 25 GB stop below. An unusable `early_prune_margin_gb` (null,
     a word, a list, NaN, infinity, a negative number or true/false) is logged once and the default 15 is used. If
     the early archive fails, `learner.log` says so and the disk check and the batch go ahead: only the disk check
     itself can hold a batch back (tests O7).
8. **Ops ledger** (backlog O6, 2026-10-21). After the archive, one row per cycle goes to `data/ops.jsonl` (not
   `cycles.jsonl`, so the report and `publish` see nothing new):
   - `tag`, `started`, `finished` (the moment the batch was scored, as in `cycles.jsonl`), `finished_epoch` (the
     same moment in Unix seconds), `minutes` between them;
   - `gap_minutes`: from the previous cycle's finish to this `started` (the boundary's consult, archive and
     update, plus any idle wait), so consecutive rows tile the clock. It is computed from the previous row's
     `finished_epoch` when that row is the previous cycle's (the same tag). Only otherwise (the first row, or after a
     row that could not be written) does it use the `finished` text, which is local time and can be 60 min off in
     the repeated hour when the clocks go back;
   - `free_gb_start`, `free_gb_end` (after the archive), `learner_gb` (`runs/` plus the learner's `endless-ai*`
     profiles; the size walk gives up after 20 s, checked between folders and every 1,000 entries), `cpu_avg` (the
     whole machine's CPU % over the batch, sampled every 60 s), `consult_seconds`, `boot_time` (when Windows last
     started);
   - `archive_seconds` and `archive_bytes`: how long this boundary's archive took and the size of the zips it wrote
     (the early archive logs its own numbers to `learner.log` instead).
   - A field that could not be measured is null and `ops_error` says why. **The ledger never fails a cycle**: the
     cycle is scored and saved first, and every failure (psutil missing or failing, the row builder failing, the file
     unwritable) becomes a null or a log line (tests O6-1 to O6-6). An adopted cycle's row has null start fields.

## Talking to Claude

- **The learner to Claude:** `findings/LATEST.md` and `latest.json` (the summary), `data/runs.jsonl` (every run),
  `data/learner.log` (everything it did). A Claude session on this PC reads them directly.
  - For a CLOUD session (claude.ai/code), run `py -3.12 learner.py publish` first. It copies those files into
    `published/`.
  - Then commit that folder with explicit paths; the live folders are git-ignored.
- **Claude to the learner:** a JSON file in `inbox/` (format in `inbox/README.md`) becomes a strategy in the next
  cycle.
  - It is checked against the allowed knobs first.
  - `config.json` is re-read every cycle, so lane counts, cycle length and so on can change without a restart.
- **Automatic consults** (`config.json` -> `consult.enabled: true`):
  - after each cycle the learner runs the `claude` command with READ-ONLY tools, on `model` (default sonnet), with
    a hard per-call cap (`max_usd_per_call`);
  - it skips the project's settings (`--setting-sources user`), and with them the session-start hook, whose
    `git pull` could move HEAD;
  - it saves the reply as `findings/claude-<cycle>.md` and queues up to 2 checked proposals;
  - it appends Claude's "for the developer" note to `findings/DEVELOPER-NOTES.md`, the first thing an
    interactive session should read;
  - capped at `max_calls_per_day`, and every call is logged in `data/consult_log.jsonl`.
  - **Reserve before the call** (O5 round 4): a paid call can only happen once the cap already counts it. Each
    consult writes two rows to `data/consult_log.jsonl`, joined by `id`:
    - BEFORE `claude` runs, a reservation, `{"day": "<date>", "kind": "reserved", "id", "tag", "started", "why"}`.
      Only these rows count toward the daily cap (lines that start with `{"day": "<today>"`; rows written before
      round 4 have the same start, so they count too). If it cannot be written (the file is read-only, or another
      program holds it open for reading only), NO call is made that cycle and `learner.log` says
      `consult: not asked, could not reserve the call in <path> ...`. A learner killed during the call keeps its
      reservation, so that call is still counted.
    - AFTER the call, the outcome, `{"kind": "outcome", "id", "day", "tag", "started", "seconds", "exit",
      "proposals_accepted", "note", "failed"?}`, which is never counted. `note` is `full`, `repeat`, `none` or
      `failed`; the optional `failed` key names each side effect (reply file, proposal, note) that could not be
      written. If the outcome row itself cannot be written, the line says so and the reservation still counts it.
  - **Only when there is something new** (backlog O5, 2026-10-21; checked after the two caps): the top 3
    strategies changed (in order), one wall's share of scored runs moved at least `wall_move_points` (3.0, raw
    percentage points), at least `new_runs` (150) more scored runs arrived, or `forced_days` (7) passed since the
    last consult that went ahead. The baseline is `data/consult_state.json`, saved only after a call that exited 0.
    A skip goes to `learner.log` and `data/consult_skips.jsonl`, never to `consult_log.jsonl` (whose reservation
    rows ARE the daily cap). If `findings/latest.json` or the state cannot be read, the consult goes ahead and says why.
  - A note that repeats the last two notes (Jaccard >= 0.6 of their key terms: `KI-n` ids, `POKEBOT_` knobs, the
    wall names; a `KI-n` id neither of them names always counts as new) becomes ONE line, `- <date>, after <cycle>:
    unchanged since <date> (N consults)`; the full reply is still in `findings/claude-<cycle>.md`.
  - At every cycle end, consult or not, `DEVELOPER-NOTES.md` keeps its newest 5 entries; older ones are moved, byte
    for byte, to `findings/DEVELOPER-NOTES-ARCHIVE.md` (archive written and read back first, so a crash can leave an
    entry in both files but never in neither). A failure there is logged and never fails the cycle.
  - A waiting `inbox/` proposal older than `proposal_ttl_days` (3, by file date), or naming the same genome as an
    older waiting one, is moved to `inbox/expired/` with a `.why.txt` when a cycle is planned (`plan` does it too).
    To run one after all, copy it back AND refresh its file time (`inbox/README.md`): a Windows copy keeps the old
    date, so a plain copy expires again at once.
  - `py -3.12 consult.py --probe-context` is a ONE-TIME developer probe (two cheap calls of the user's usage):
    does `claude -p --setting-sources user` still load the repo's CLAUDE.md? It prints the input-token
    difference between a run from the repo and one from an empty folder with `--add-dir`. It changes nothing.
- **Code changes, new knobs, relaunches:** these stay with an interactive Claude session, where you can see them.

## Safety rules (built in, not just written down)

- It never edits code. Its only git is fetch plus a fast-forward-only merge of its own clone, between cycles
  (test L5). It writes inside `ai-agent/`, plus the batch runner's lane profiles
  (`sandbox-pokebot/profiles/endless-ai####-*`), which it later archives and deletes by exact name. Tests R2 and R22
  prove it never archives or deletes anything else.
- It allows one learner at a time (a lock file) and never runs two batches at once. Known limit: taking the lock is a
  check followed by a write, not one atomic step, so two starts within milliseconds of each other both take it
  (measured 12 of 12; 0.5 s apart, the second is refused). Real starts are seconds apart.
- It only uses knob values listed in `knowledge.GENES`, and anything else is refused (tests B7, B8).
  - The eleven step-14 knobs use only values that ran for 13 hours.
  - The one documented exception is the boss-mode knob's `4`, which drives training the bot already runs every
    game (`06`, 2026-10-03).
- It pauses itself, instead of retrying forever:
  - after 5 crashes in a row (the crash-loop breaker, tests BK1-BK9 and BK-C);
  - after 3 cycles in a row with no scored runs;
  - when the disk falls below 25 GB free. It first archives every cycle but the newest (it never deletes
    without a verified archive) and stops only if that is not enough. Under 40 GB it has already been archiving
    early (step 7, tests O7).
  - Under 2 GB free no archive can be written: it archives nothing, deletes nothing, starts no batch and writes
    `findings/ATTENTION.md` (test R10).
- **It plays the code its clone holds.** Commits and pulls in the development checkout cannot touch a running
  cycle. New bot code reaches the learner at the next cycle boundary, through `auto_update`.

## Changing the knobs

The allowed knobs and values live in `knowledge.py` (`GENES`, and `FIXED` for the ones held constant). Adding one
takes three things:
- the story bot must read it (`tools/story-dev/x4_headless.py` refuses a knob missing from the source);
- it must be registered in `PROJECT KNOWLEDGE/29-DISABLED-FEATURES-REGISTRY.md`;
- `test_agent.py` must pass.

That is an interactive-session job.
- **The first wall knob shipped on 2026-10-03:** `POKEBOT_BOSSMODE_TOPUP` (1 vs 4), how many levels boss mode
  trains before re-fighting a boss it keeps losing to. Its default 1 is the old behaviour.
  - With 12 knobs, the screen is now Hadamard-16.
- **Next candidates**, in `PROJECT KNOWLEDGE/ai-research-notes/2026-10-03-decision-points-MAP.md`:
  - the plateau-loss thresholds;
  - the League basket;
  - the box-first tier (KI-118);
  - counter-lead scope (KI-122).

## Files

| file | job |
|---|---|
| `learner.py` | the loop and its commands (`run`, `once`, `plan`, `ingest`, `reparse`, `report`, `status`, `publish`, `archive`, `archive-check`) |
| `knowledge.py` | what it knows up front: knobs, bosses, named failure shapes, with sources |
| `scoring.py` | logs -> run records (the run-identity rules learned from KI-119) |
| `brain.py` | strategy choice and knob-effect estimates |
| `report.py` | `findings/LATEST.md` |
| `consult.py` | the optional Claude call, its novelty gate, the DEVELOPER-NOTES collapse and roll, and the one-time `--probe-context` |
| `test_agent.py` | the offline gate (scoring, choice, regression, the batch runner's own preflight, prune and archive safety, the ops ledger and the early archive, the consult's novelty gate, notes roll and inbox expiry, torn writes, the state backup, the crash-loop breaker and the game journal) |
| `../tools/ops/replay_learner_recovery.py` | off-gate real-data check of the journal and crash recovery against the clone, read-only (RD1, RD2) |
| `config.json` | the settings, re-read every cycle |
| `run_agent.ps1` | the 24/7 wrapper (restarts after a crash or into updated code; stops on `STOP` or `ATTENTION.md`) |
