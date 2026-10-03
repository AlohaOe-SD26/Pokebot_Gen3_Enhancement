# Emerald AI: the strategy learner (v1)

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

## Start, stop, check

| to... | do this (PowerShell, in this folder) |
|---|---|
| start it 24/7 | `.\run_agent.ps1` (keep the window open; the PC must not sleep) |
| stop it cleanly | create a file named `STOP` here: `New-Item STOP`. The running cycle finishes first, up to 12 hours |
| see where it is | `py -3.12 learner.py status` |
| see what it learned | open `findings\LATEST.md` (rewritten after every cycle) |
| preview the next cycle | `py -3.12 learner.py plan` (runs nothing) |
| check the code still works | `py -3.12 test_agent.py` (offline, about 10 seconds, must say ALL PASS) |

If it ever stops on its own, `findings\ATTENTION.md` says why. Fix the cause, delete that file, start it again.

## One cycle (12 hours by default)

1. **Size itself to the PC.** Lanes are parallel games, in fours: one per starter (Torchic, Mudkip, Treecko,
   random) for each strategy. Default: as many as the CPU and memory allow, at most 24 (six strategies), keeping 4
   threads and 8 GB free. An open bot window costs one thread. If another batch or harness drive is running, the
   learner waits instead of competing.
2. **Pick strategies** (`brain.py`):
   - the current best (the control);
   - a proposal from `inbox/`, if one is waiting;
   - a "Thompson draw": a strategy that may be underrated because it has few runs;
   - mutants of the best, changing one or two knobs, preferring combinations never run.
3. **Play.** Real games, through `tools/story-dev/x4_headless.py --arms`. That runner refuses a misspelt knob, a
   duplicate strategy or a bad lane split before any game starts.
4. **Score** (`scoring.py`): each run becomes a ~1 KB record.
   - Score = progress out of 13 (8 badges, 4 Elite Four, the Champion).
   - A run the time limit cut off is kept but not scored.
5. **Learn and report** (`report.py`): `findings/LATEST.md` holds:
   - the strategy ranking;
   - what each knob seems worth (a regression);
   - where runs end, with hints from `05-KNOWN-ISSUES.md`;
   - questions for Claude.
6. **Ask Claude** (`consult.py`, OFF until enabled; see below).
7. **Clean up.** It deletes its own raw logs (about 3 GB a cycle) except the newest 3 cycles. The run records are
   kept forever.

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
  - after each cycle the learner runs the `claude` command with READ-ONLY tools;
  - it saves the reply as `findings/claude-<cycle>.md` and queues up to 2 checked proposals;
  - capped at `max_calls_per_day`, and every call is logged in `data/consult_log.jsonl`.
  - It costs Claude usage, so it starts OFF.
- **Code changes, new knobs, relaunches:** these stay with an interactive Claude session, where you can see them.

## Safety rules (built in, not just written down)

- It never edits code and never runs git. It writes inside `ai-agent/`, plus the batch runner's lane profiles
  (`sandbox-pokebot/profiles/endless-ai####-*`), which it later deletes by exact name. A test (R2) proves it never
  deletes anything else.
- It allows one learner at a time (a lock file) and never runs two batches at once.
- It only uses knob values that have already run for 13 hours (step 14). Anything else is refused (tests B7, B8).
- It pauses itself, instead of retrying forever:
  - after 3 cycles in a row with no scored runs;
  - when the disk falls below 25 GB free.
- **It plays the code in `sandbox-pokebot/` as it is.** The batch runner aborts a cycle if that folder changes
  mid-batch, so a cycle never mixes two versions of the bot. While the learner runs:
  - do story-bot work in a git WORKTREE;
  - expect a `git pull` that changes `sandbox-pokebot/` to cut the current cycle short. Finished runs are still
    scored.

## Changing the knobs

The allowed knobs and values live in `knowledge.py` (`GENES`, and `FIXED` for the ones held constant). Adding one
takes three things:
- the story bot must read it (`tools/story-dev/x4_headless.py` refuses a knob missing from the source);
- it must be registered in `PROJECT KNOWLEDGE/29-DISABLED-FEATURES-REGISTRY.md`;
- `test_agent.py` must pass.

That is an interactive-session job. The obvious next knobs are the walls above:
- the Elite Four level floor and basket targets;
- the counter-catch rules behind Norman (KI-118) and Tate & Liza (KI-122).

## Files

| file | job |
|---|---|
| `learner.py` | the loop and its commands (`run`, `once`, `plan`, `ingest`, `report`, `status`, `publish`) |
| `knowledge.py` | what it knows up front: knobs, bosses, named failure shapes, with sources |
| `scoring.py` | logs -> run records (the run-identity rules learned from KI-119) |
| `brain.py` | strategy choice and knob-effect estimates |
| `report.py` | `findings/LATEST.md` |
| `consult.py` | the optional Claude call |
| `test_agent.py` | the offline gate (scoring, choice, regression, the batch runner's own preflight, prune safety) |
| `config.json` | the settings, re-read every cycle |
| `run_agent.ps1` | the 24/7 wrapper (restarts after a crash; stops on `STOP`, a pause or `ATTENTION.md`) |
