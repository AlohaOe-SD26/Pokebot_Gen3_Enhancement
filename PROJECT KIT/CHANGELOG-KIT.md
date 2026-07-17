# Claude Code Project Kit — Version History

Newest first. The current kit version is in `PROJECT KIT/VERSION`; each
bootstrapped project stamps its directives block with the version that wrote
it (e.g. `[kit v1.6]`), so `/health` can flag when a project is behind.

## v1.10 - session-awareness heartbeat for the Remote Programs hub
- `KeepAwake.ps1` now writes a small `REMOTE START/logs/session.lock`
  heartbeat (JSON: pid, started, heartbeat, project) while a Claude session
  is live, refreshing it each ~30s poll and removing it on exit (via a
  `finally`, so the awake-hold release always runs too). The Remote Programs
  hub reads this lock to show a green "running" indicator per project, so you
  don't accidentally launch a second session. KeepAwake was chosen because it
  already runs for exactly the session's lifetime - the user's `Remote-Start`
  launcher stays byte-identical (untouched).
- Staleness is handled hub-side (a heartbeat older than ~2 min is treated as
  ended), so a hard-killed session's leftover lock stops showing as running.
- No behavior change for anyone not using the hub: the lock is written into
  the already-ignored `logs/` folder and never affects the launch flow.

## v1.9 — automation parameters for the Remote Programs hub
- `Bootstrap-Project.ps1` gained optional parameters so the Remote Programs
  hub can drive it without prompts: `-RepoName <name>` (create the private
  repo under that name), `-RepoUrl <url>` (use an existing repo as origin),
  `-NoRemote` (skip GitHub entirely), `-NonInteractive` (never prompt; take
  safe defaults - identity/login prompts skipped, large files auto-ignored,
  no "Press Enter" holds). Double-click behavior without parameters is
  unchanged.
- Verified end-to-end on real PowerShell 5.1: local-only mode, RepoUrl mode
  (bare-remote push), and LIVE `-RepoName` mode (real private GitHub repo
  created, kit committed and pushed) - all with zero prompts and clean
  UTF-8 docs.

## v1.8 — encoding correctness, verified on real Windows
- **Fixed: the bootstrap corrupted every non-ASCII character in the docs it
  installed** (em-dashes, smart quotes became mojibake). Root cause: Windows
  PowerShell 5.1's `Get-Content` reads UTF-8-no-BOM templates as ANSI when no
  `-Encoding` is given; the installer then re-encoded to UTF-8, double-encoding
  the text. All template/doc reads in `Bootstrap-Project.ps1` now force
  `-Encoding UTF8`, and its script body is pure ASCII.
- **Fixed: the SessionStart catch-up hook (`session-sync.ps1`) rendered
  non-ASCII doc content as mojibake** in a fresh session's context. Same
  encoding family: the hook now forces UTF-8 stdout (guarded so it never
  breaks always-exit-0), reads docs with `-Encoding UTF8`, and keeps its own
  script body ASCII-only.
- **New: bootstrapped projects protect the launcher from line-ending damage.**
  The generated `.gitattributes` marks `REMOTE START/Remote-Start.ps1` and
  `.bat` as `-text` (byte-verbatim across machines). Launcher-only — your own
  files keep normal git normalization.
- **Verified on real Windows (PowerShell 5.1):** a full end-to-end bootstrap
  into a scratch project produced byte-clean UTF-8 docs, a correct managed
  CLAUDE.md block, a private GitHub repo + first push, and a fully idempotent
  re-run (every existing file left untouched).

## v1.7 — non-coder setup, agent memory, cheaper catch-up
- **One-click environment installer** (`Install-Environment.bat`/`.ps1`):
  detects and installs Git, GitHub CLI, and Claude Code (native installer
  first, winget `Anthropic.ClaudeCode` as fallback) with plain-language
  prompts, then guides the two interactive sign-ins (GitHub device flow and
  Claude browser login) and ends with a verification gate. Node.js is no
  longer required — Claude Code's native installer replaces the old npm path.
- **`08-MISTAKES.md`** — a new append-only ledger (symptom, root cause, fix,
  one-line prevention rule). Read at session start so solved bugs and
  abandoned dead-ends are never re-walked. `/wrapup` appends to it when an
  item involved a fix; `/reconcile` retires prevention rules once a
  test/lint/refactor makes the mistake structurally impossible (a stale
  "don't do X" line wastes context).
- **Cheaper catch-up:** the SessionStart hook now emits a small structured
  brief (sync state, branch, mid-task resume point, open punch-list items,
  recent mistakes) via Claude Code's official `additionalContext` channel,
  with a `startup|resume|clear|compact` matcher — so a fresh session orients
  for a few tokens instead of re-reading every doc. The brief is also kept in
  `04-HANDOFF.md`, so it survives even if hook injection misbehaves.
- **Token-discipline directives** added to CLAUDE.md: write-it-down-then-start-
  fresh, compact at clean boundaries, open docs on demand, delegate verbose
  side-quests to subagents sparingly. CLAUDE.md stays under 200 lines.
- `/checkpoint` and `/wrapup` locked to user-invocation only
  (`disable-model-invocation`); `/health` now runs `claude doctor` and checks
  Git/gh/auth; `08-MISTAKES.md` added to the doc audit and `merge=union` set.

## v1.6 — navigation & onboarding
- Root `START-HERE.txt`: a plain-language decision guide (new project vs.
  continue-from-GitHub vs. daily work vs. offline backup) so a first-time
  user knows exactly which file to double-click.
- README rewritten task-first: Quick Start and First-time PC setup now lead;
  version history moved here.
- Guided first-run preflight in Bootstrap-Project: detects missing Git,
  GitHub CLI, gh auth, and git identity, and offers to run/sets up what it
  can (launching `gh auth login`, setting `user.name`/`user.email`) instead
  of failing partway through.

## v1.5 — offline portability
- `Make-Portable.bat`: writes a dated snapshot (verified `git bundle` of the
  whole repo + a kit copy + `PORTABLE-README.txt`) to a USB stick or drive,
  restorable with zero network. A snapshot, never a sync channel.

## v1.4 — resume semantics hardened
- Sync (launcher + SessionStart hook) fetches and compares first: BEHIND →
  pull (remote is truth after a clean wrap-up); AHEAD/DIVERGED → STOP and
  report, never auto-push/merge/discard — reconciling is the user's call.
- Command words mapped in the directives: "wrap up" and "pick up where you
  left off".

## v1.3 — protocol hardening
- `/checkpoint` gains never-red-on-main: park failing work on a `wip/`
  branch, restore main, record full debug state in the handoff.
- `/checkpoint` and `/wrapup` capture any new session directives as
  punch-list items with full specs.
- Trust-but-verify on resume: confirm the tree matches the handoff before
  resuming.
- `/reconcile`: agent-guided merge of a pre-existing project's own
  instructions with the kit directives — ask-first, nothing deleted without
  approval, contradictions surfaced for the user.

## v1.2 — robustness
- Keep-awake guard (holds the PC awake only while Claude Code runs).
- SessionStart hook runs the sync on every entry, even plain `claude`.
- Append-only logs marked `merge=union` so two machines' entries never
  conflict.
- Run transcripts written to `logs\` by every script; large-file (>95MB)
  pre-push guard; kit version stamp.

## v1.1 — first robustness pass
- Pre-launch sync added to Remote-Start; `/checkpoint`, `/wrapup`, `/health`
  slash commands; per-run logs.

## v1.0 — foundation
- Idempotent bootstrap: CLAUDE.md managed-directives block, PROJECT
  KNOWLEDGE doc skeleton (00-07), private GitHub repo creation via gh,
  bundled Remote-Start launcher, per-item definition of done.
