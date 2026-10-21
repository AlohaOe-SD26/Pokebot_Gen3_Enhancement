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
| archive old raw logs now | `py -3.12 learner.py archive` is meant for when the learner is STOPPED. It refuses while the 24/7 learner holds its lock (the running learner archives at each boundary by itself). If the learner is started while a manual archive runs, it WAITS for it (up to 120 min, then exits 2) instead of refusing |
| check the code still works | `py -3.12 test_agent.py` (offline, about 10 seconds, must say ALL PASS) |

If it ever stops on its own, `findings\ATTENTION.md` says why. Fix the cause, delete that file, start it again.

If the learner process dies mid-cycle, the batch keeps playing. The next start ADOPTS it: it waits for the batch to
end, then scores it.

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
7. **Archive** (backlog O3, built 2026-10-21). The newest `keep_raw_cycles` cycles (20) keep their raw logs as
   files. Each older cycle's `runs/<tag>/batch/` (measured 1.3-1.7 GB) is zipped to `runs/<tag>/raw.zip`, with
   `raw.manifest.json` listing every file's name, size and CRC32.
   - Measured on a copy of ai0038: 73 files, 1,303 MB -> 68.6 MB (19:1) in 16 s.
   - The zip is VERIFIED (every member's CRC equals the CRC read from the original) before anything is deleted.
     Then `batch/` and the cycle's lane profiles are deleted. **An original is deleted only when its exact bytes
     (name, size, CRC32) are in a verified archive, and no archive file is ever overwritten or deleted.**
   - A cycle is archived only once it is QUIET: no batch runner or lane process (`endless-<tag>-`) names it and no
     original changed in the last 60 minutes (`QUIET_MINUTES`). Otherwise it is skipped until a later boundary. If an
     original changes while it is being archived, nothing is deleted.
   - At most `max_archives_per_prune` (3) cycles a boundary; a failure is logged, the raw logs stay, and the next
     boundary retries. A killed archive leaves only a `raw.zip.part`, removed next time. Links and junctions inside
     `batch/` are neither archived nor followed.
   - A `raw.zip` that cannot be trusted while every original is still on disk is SET ASIDE as `raw.zip.bad.<k>` (with
     `raw.manifest.json.bad.<k>`), and the originals are archived afresh. A set-aside file is never overwritten,
     renamed or deleted; delete them by hand only after checking them.
   - **HELD for review.** When the learner cannot prove a cycle safe, it touches NOTHING of that cycle and logs
     `HELD FOR REVIEW` once, then `held for review: <tags>` each boundary. It keeps running. The cases are: a delete
     that stopped part-way (so `raw.zip` is the only copy of some files) whose remaining originals changed or gained
     a file, or whose `raw.zip` no longer verifies; an unreadable `raw.manifest.json`; a `runs/<tag>/batch` that its cycle's `created` list does not name;
     and a `batch` that is a link. `learner.py archive-check` lists them (exit 1), `learner.py status` and
     `tools/status.py` count them. To release a cycle: stop the learner, inspect and fix that folder, remove the
     cycle's `"held"` entry from `data\state.json`, and start the learner again.
   - Archives are kept forever (`keep_archive_cycles: 0`; any other value is reserved and does nothing yet). They
     are the AI's experience input (backlog A6): `zipfile.ZipFile(path).open("batch/L01/debug-logs/<x>.log")`.
   - The run records in `data/runs.jsonl` are kept forever, as before.

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
- **Code changes, new knobs, relaunches:** these stay with an interactive Claude session, where you can see them.

## Safety rules (built in, not just written down)

- It never edits code. Its only git is fetch plus a fast-forward-only merge of its own clone, between cycles
  (test L5). It writes inside `ai-agent/`, plus the batch runner's lane profiles
  (`sandbox-pokebot/profiles/endless-ai####-*`), which it later deletes by exact name. A test (R2) proves it never
  deletes anything else.
- It allows one learner at a time (a lock file) and never runs two batches at once.
- It only uses knob values listed in `knowledge.GENES`, and anything else is refused (tests B7, B8).
  - The eleven step-14 knobs use only values that ran for 13 hours.
  - The one documented exception is the boss-mode knob's `4`, which drives training the bot already runs every
    game (`06`, 2026-10-03).
- It pauses itself, instead of retrying forever:
  - after 3 cycles in a row with no scored runs;
  - when the disk falls below 25 GB free. It first archives every cycle but the newest (it never deletes
    without a verified archive) and stops only if that is not enough.
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
| `consult.py` | the optional Claude call |
| `test_agent.py` | the offline gate (scoring, choice, regression, the batch runner's own preflight, prune and archive safety) |
| `config.json` | the settings, re-read every cycle |
| `run_agent.ps1` | the 24/7 wrapper (restarts after a crash or into updated code; stops on `STOP` or `ATTENTION.md`) |
