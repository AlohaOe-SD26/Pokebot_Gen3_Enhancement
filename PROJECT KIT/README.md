# Claude Code Project Kit

A portable, drop-in folder that makes any project — new or existing —
resumable by Claude Code from any computer. It installs standing directives,
a PROJECT KNOWLEDGE doc system, GitHub sync, a phone-access launcher, and
offline backup. New here? Read `START-HERE.txt` at the top of the zip first;
it points you at the right file to double-click.

## Quick start

**First time on a computer (once):** double-click
`PROJECT KIT\Install-Environment.bat`. It installs the three tools you need
(Git, GitHub CLI, Claude Code) and walks you through signing in to GitHub and
Claude. Safe to re-run. You do **not** need Node.js — Claude Code installs
itself now. (Details under "First-time PC setup" below.)

**New project (or an existing folder on this PC):** copy the `PROJECT KIT`
folder into the project's root, then double-click
`PROJECT KIT\Bootstrap-Project.bat`. It creates a private GitHub repo,
installs everything, and does the first commit + push. The only thing it
asks is the repo name.

**Continue a project from GitHub onto this PC:** keep the
`CONTINUE FROM GITHUB` folder wherever your projects live, double-click
`Continue-From-GitHub.bat`, pick the repo (or paste a URL). It clones and
offers to start working immediately.

**Daily work on a set-up project:** double-click
`<project>\REMOTE START\Remote-Start.bat` — syncs with GitHub, keeps the PC
awake, launches Claude Code with phone access.

**Offline backup:** double-click `<project>\PROJECT KIT\Make-Portable.bat`
to write a full snapshot to a USB stick, restorable with no network.

The bootstrap is **idempotent** — re-running it never overwrites your files;
it only adds missing pieces and refreshes the managed directives block in
CLAUDE.md (with a `.bak` backup whenever it touches an existing file). To
upgrade a project to a newer kit, drop in the new `PROJECT KIT` folder and
re-run the bootstrap.

## First-time PC setup (once per computer)

**The easy way:** double-click `PROJECT KIT\Install-Environment.bat`. It
detects and installs Git, GitHub CLI, and Claude Code (trying Claude Code's
own installer first, then winget), guides you through the GitHub and Claude
sign-ins, and finishes by checking everything is ready. It's safe to run more
than once — it skips whatever's already done — so if a step needs a fresh
window, just run it again.

`Bootstrap-Project.bat` also detects what's missing and offers to help. If you
prefer to do it by hand, here are the steps:

1. **Git:** `winget install Git.Git` (reopen PowerShell after).
2. **GitHub CLI + login:** `winget install GitHub.cli`, then `gh auth login`
   → GitHub.com → HTTPS → "authenticate Git: Yes" → "Login with a web
   browser" (copy the 8-char code, paste at github.com/login/device).
   Saying **Yes** to "authenticate Git" also wires up push credentials.
   Verify with `gh auth status` — it should show your account (AlohaOe-SD26).
3. **Git identity:** `git config --global user.name "Your Name"` and
   `git config --global user.email "you@example.com"`.
4. **Claude Code:** install with PowerShell `irm https://claude.ai/install.ps1 | iex`
   (or `winget install Anthropic.ClaudeCode`) — **no Node.js needed**. Run
   `claude`, sign in via claude.ai, confirm `/status` shows Pro/Max (clear
   `ANTHROPIC_API_KEY` if one is set).

You don't need your GitHub username anywhere — gh creates repos under
whatever account it's logged in as.

## What the bootstrap installs

1. **`CLAUDE.md`** — standing directives Claude Code auto-loads every
   session: sync first, read the handoff, keep docs current, document intent
   (whole program + each part), and a per-work-item Definition of Done
   ending in commit + push. The directives live between
   `<!-- BEGIN/END PROJECT-KIT DIRECTIVES -->` markers; anything you write
   outside the markers is yours and never touched.
2. **`PROJECT KNOWLEDGE\`** — `00-README` (reading order),
   `01-VISION-AND-DESIGN`, `02-ARCHITECTURE`, `03-PUNCH-LIST`, `04-HANDOFF`,
   `05-KNOWN-ISSUES` (current-state, edited in place) and `06-DECISIONS-LOG`,
   `07-CHANGELOG`, `08-MISTAKES` (append-only history). `08-MISTAKES` logs
   solved bugs and dead-ends so future sessions don't repeat them.
3. **Slash commands** in `.claude\commands\`: `/checkpoint` (stop mid-task
   safely), `/wrapup` (finish an item), `/health` (audit + repair),
   `/reconcile` (merge a pre-existing project's own instructions).
4. **SessionStart hook** (`.claude\settings.json` + `hooks\`) — runs the
   safe sync on every session start, even plain `claude`.
5. **`REMOTE START\`** — the phone launcher (KeepAwake → Git-Sync → your
   original Remote-Start.ps1, which ships byte-identical and is never
   overwritten).
6. **Git + GitHub** — `git init` (branch `main`), a starter `.gitignore`
   and `.gitattributes` (append-only logs set to `merge=union`); then a
   private repo via gh (name prompted) or a pasted URL. Repo URL recorded in
   `04-HANDOFF.md`; large files (>95MB) flagged before the first push.

## Existing projects — what's preserved

An existing `CLAUDE.md` keeps everything outside the markers; the directives
block is appended (backup `CLAUDE.md.bak`), and on later re-runs updated in
place. Existing PROJECT KNOWLEDGE files, `.gitignore`, your launcher, and an
already-set `origin` are all left as-is — only missing pieces are added. If
the project already had its own agent instructions or session protocol, run
`/reconcile` in your first session: the agent merges them with the kit
directives, asks before changing anything, deletes nothing without approval,
and surfaces any direct contradictions for you to rule on.

## Continuing across computers

Because the kit is committed into each repo, a clone brings down CLAUDE.md,
PROJECT KNOWLEDGE, REMOTE START, and PROJECT KIT all at once. Use
`CONTINUE FROM GITHUB\Continue-From-GitHub.bat` (lists your repos via gh,
clones into a sibling folder, offers to launch Remote-Start). The first
session reads `04-HANDOFF.md` and resumes where the other machine left off.

The sync rule that keeps two machines safe: **the remote is the truth after
a clean wrap-up.** On resume, BEHIND the remote → pull; AHEAD or DIVERGED →
stop and report, because that means a previous session never finished its
wrap-up, and reconciling unpushed work is your call (never auto-pushed or
discarded). So: finish work items cleanly before switching machines, and
each session starts current and ends pushed.

## Command words

Drive sessions in plain language: **"wrap up"** = finish-and-verify the
current item (`/wrapup`) or park it honestly (`/checkpoint`), then update
docs and end with a confirmed push — nothing left only on this machine.
**"pick up where you left off"** = re-run the start ritual: sync check →
read handoff → verify the tree matches it → resume the next steps in order.

## Knobs (top of Bootstrap-Project.ps1)

- `$LevelsUp` — 1 (default) when the kit sits in a subfolder of the project
  root; 0 if its files sit directly in the root.
- `$ManualProjectPath` — hard-override the project root.
- `$DefaultBranch` — branch name for new repos (default `main`).

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Push rejected ("fetch first" / non-fast-forward) | Another computer pushed first. Run `git pull`, verify, `git push` — or tell the agent "run the push-recovery flow". |
| `gh: not logged in` / auth expired | `gh auth login` again (device flow). Verify with `gh auth status`. |
| Session not visible on the phone's Code tab | Known bug: open the session URL from the terminal once in the phone's browser; it then appears in the list. |
| Session times out / PC slept anyway | Check the minimized "KeepAwake" window exists; its log is in `REMOTE START\logs\`. Laptops: closing the lid still sleeps unless lid action is "do nothing". |
| Merge conflict during pull | Don't resolve blindly. Tell the agent "resolve the merge per the sync directive" — it asks before anything destructive. |
| Push fails: file too large (>100MB) | Add it to `.gitignore` (the bootstrap's guard offers this) or use Git LFS. |
| A script window closed too fast to read an error | The full transcript of every run is in that script's `logs\` folder — paste the latest log to Claude. |
| Hook didn't run / no `[kit sync]` line | Hooks need a recent Claude Code (`claude update`); check `.claude\settings.json` has the SessionStart entry. Everything else works without the hook. |
| Project's directives feel outdated | Compare the `[kit vX.Y]` stamp in CLAUDE.md to `PROJECT KIT\VERSION` (or run `/health`); re-run `Bootstrap-Project.bat` with the newest kit. |
| No internet / GitHub unreachable, need the project elsewhere | Use `Make-Portable.bat` beforehand (keep a recent USB snapshot); restore per its PORTABLE-README.txt, work offline, reconcile + push when access returns. |

## Version history

See `CHANGELOG-KIT.md` for what changed in each version.
