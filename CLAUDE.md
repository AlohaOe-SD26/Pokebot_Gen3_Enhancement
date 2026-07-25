# Pokebot_Gen3_Enhancement — Claude Code Project Instructions

Anything you write OUTSIDE the marked block below is yours and will never be
touched. The Project Kit bootstrap only manages the text BETWEEN the
BEGIN/END markers (re-running Bootstrap-Project updates that block in place).

<!-- BEGIN PROJECT-KIT DIRECTIVES [kit v1.10] (managed block — re-run Bootstrap-Project to update; do not hand-edit inside) -->
## Standing Directives (Project Kit)

These rules apply automatically to EVERY session in this project, with no
prompting needed. They exist so that any AI agent — in any future chat — can
pick up exactly where the last one left off.

### 1. Session start — orient before acting
- **Sync first** (this project is worked on from multiple computers): run
  `git status` and `git fetch`, then compare local to remote BEFORE reading
  docs or touching code:
  - BEHIND the remote → pull first. The remote is the truth, because a
    completed wrap-up always ends with a confirmed push.
  - AHEAD or DIVERGED → STOP and report to the user before touching
    anything: it means a previous session ended without completing its
    wrap-up, and reconciling unpushed work is the USER's call. Never
    auto-push it, build on it, or discard it.
  - Uncommitted local changes (or an "Unpushed work" handoff note) → same
    rule: review with the user before pulling; never discard local work to
    make a pull succeed; conflicts are resolved with the user, never
    destructively.
- A `[kit sync]` status line may appear in context at session start (from
  the SessionStart hook, which already attempted this sync) — trust it and
  act on any WARNING it carries before doing anything else.
- Read `PROJECT KNOWLEDGE/00-README.md` (reading order), then
  `PROJECT KNOWLEDGE/04-HANDOFF.md` for current state, in-progress work, and
  next steps. Treat the handoff as the authoritative "you are here" marker.
- If the handoff's "If stopped mid-task" section holds pending work, that is
  the exact stopping point of an interrupted session — resume THERE first.
- Trust but verify: before resuming, confirm the working tree actually
  matches the handoff's claimed state (git status/log vs. what the handoff
  says; run the project's verification checks if in doubt). If reality and
  the handoff disagree, reconcile and CORRECT the handoff before new work.
- Skim `03-PUNCH-LIST.md`, `05-KNOWN-ISSUES.md`, and `08-MISTAKES.md` before
  proposing or starting work, so effort goes to agreed priorities and so past
  bugs and abandoned dead-ends are NOT repeated. A short catch-up brief may
  already be injected at session start (sync state, resume point, open items,
  recent mistakes) — use it to orient cheaply instead of re-reading every doc.
- Never re-derive project intent from code alone. `01-VISION-AND-DESIGN.md`
  is the source of truth for what this program (and each part of it) is FOR.
  If code and vision conflict, flag it — don't silently pick one.

### 2. Documentation duties (continuous, not optional)
- **Project status** — keep `04-HANDOFF.md` continuously current: what state
  the project is in, what just changed, what is mid-flight, what comes next.
- **Changes & fixes log** — every meaningful change, fix, or addition gets an
  entry appended to `07-CHANGELOG.md`.
- **Intent & goals** — keep `01-VISION-AND-DESIGN.md` accurate for both the
  whole program and each individual component. When a new component is built,
  add its purpose/intent there before or with the code.
- **Architecture** — keep `02-ARCHITECTURE.md` true to how the code is
  actually built today (stack, module map, data flow, run/build/test
  commands), updating it whenever structure changes.
- **Decisions** — any significant choice (architecture, library, tradeoff,
  scope) gets appended to `06-DECISIONS-LOG.md` with rationale and the
  alternatives that were rejected.
- **Mistakes** — whenever a bug took real effort to fix, an approach was tried
  and abandoned, or an assumption proved wrong, append an entry to
  `08-MISTAKES.md` (symptom, root cause, the fix that worked, a one-line
  prevention rule). This is how future sessions avoid re-walking solved
  problems — it is not optional bookkeeping, it is cost control.
- **Punch list** — keep `03-PUNCH-LIST.md` statuses true at all times.

File-handling rules:
- `01`, `02`, `03`, `04`, `05` are CURRENT-STATE files: edit them in place so
  they always describe present reality. Remove stale content.
- `06`, `07`, and `08` are APPEND-ONLY history: add new entries at the end
  with a date. Never rewrite, reorder, or delete past entries.

### 3. Definition of Done — every completed work item
A work item (feature, fix, refactor, asset) is NOT done until all of these
are complete, in order:
1. The change works and has been verified (run it / test it as applicable).
2. Current-state docs updated: `01`/`02`/`05` as applicable; the item's entry
   in `03-PUNCH-LIST.md` marked done.
3. `07-CHANGELOG.md` entry appended; `06-DECISIONS-LOG.md` appended if any
   significant decision was made; `08-MISTAKES.md` appended if this item
   involved fixing a bug or abandoning a tried approach.
4. `04-HANDOFF.md` updated (current state, next steps).
5. `git add -A` and commit, message format:
   `<type>: <short summary> (punch-list #N)` — types: feat/fix/refactor/docs/chore.
6. `git push`. If the push is REJECTED because the remote has new commits
   (worked on from another computer), run `git pull` to merge, verify
   nothing broke, and push again — ask the user before resolving any
   merge conflict. If the push fails for other reasons (offline, no
   remote yet), record the fact under an "Unpushed work" note in
   `04-HANDOFF.md` so the next session pushes first.

Do steps 2–6 per completed item, not batched at the end of a long session.

Project slash commands (in `.claude/commands/`): `/wrapup` runs this
definition of done for the item just finished; `/checkpoint` safely parks
unfinished work when a session must stop mid-task — use it EVERY time work
stops early, so no computer strands changes; `/health` audits docs, git
state, and kit version, and repairs what it safely can; `/reconcile` merges
a pre-existing project's own instructions with these directives — ask-first,
nothing removed without approval — and also retires prevention rules whose
underlying mistake has been structurally fixed (a stale "don't do X" line
keeps that idea active and wastes context, so once a test/lint/refactor makes
it impossible, drop the rule and note it in `08-MISTAKES.md`).

Command words (natural-language equivalents the user may say): **"wrap up"**
= end the session safely — run `/wrapup` if the current item can be finished
AND verified green quickly, otherwise `/checkpoint` (park it honestly); in
both cases capture new session directives, update handoff + punch list, and
end with a confirmed push (commit hash + branch) — nothing may exist only on
this machine. **"pick up where you left off"** = the session-start ritual
above, explicitly re-run (sync check first, then handoff, then trust-but-
verify, then resume next steps in order).

### 7. Working efficiently (keep sessions cheap)
Long, noisy sessions cost tokens and degrade quality. Favor durable files
over a swollen context window:
- **Write it down, then start fresh.** The PROJECT KNOWLEDGE docs — not the
  chat history — are the project's memory. Before a context gets large, make
  sure the handoff + logs capture the state, so a NEW session can resume from
  files cheaply rather than from a long transcript.
- **Compact at clean boundaries.** When a phase/item is finished and docs are
  current, that is the moment to compact or clear — not mid-task. If
  compacting, state what to preserve (modified files, test/run commands, open
  decisions) first.
- **Don't re-read what the brief already gave you.** Open a specific doc when
  you need its detail, not all of them by reflex.
- **Delegate verbose side-quests.** Large read-only exploration or research
  can go to a subagent so its bulk stays out of the main thread — but use this
  judiciously; isolated agents cost materially more tokens, so reserve them
  for genuinely large or noisy tasks, not routine edits.

### 4. Handoff quality bar
Another agent with ZERO prior context must be able to resume from
`04-HANDOFF.md` alone. It must always answer: What is this project? What
state is it in right now? What was just done? What is in progress (and how
far along)? What is next? How do I run/build/test it? Any gotchas or
unpushed work?

### 5. Git conduct
- The remote repository URL is recorded in `04-HANDOFF.md`.
- Commit per completed work item; keep commits scoped and messages honest.
- Never force-push; never rewrite published history; never commit secrets
  (.env files, API keys, tokens).
- Ask before any destructive git operation (reset --hard, clean -f, branch
  deletion).

### 6. Precedence & reconciliation
- Instructions OUTSIDE this managed block are the project's own rules: they
  compose with these directives and are always honored alongside them.
- If something outside the block DIRECTLY CONTRADICTS these directives, do
  not silently follow either side — flag the conflict to the user and ask
  which wins (`/reconcile` exists for exactly this). Record the ruling in
  the decisions log so it never has to be asked twice.
<!-- END PROJECT-KIT DIRECTIVES -->

## Project rules (outside the managed block — this project's own directives)

### Two-folder fork layout (user directive, 2026-07-17)
- `40cakes repo/pokebot-gen3/` is a PRISTINE mirror of upstream
  40Cakes/pokebot-gen3 (git subtree, remote `upstream-pokebot`). NEVER
  edit files inside it; it only changes via upstream pulls.
- `40cakes repo/DOCUMENTATION/` documents the ORIGINAL program only.
  `40cakes repo/UPDATE-LOG.md` is the append-only record of upstream syncs.
- `custom-pokebot/` is OUR enhanced fork — all enhancements happen there,
  documented in `custom-pokebot/DOCUMENTATION/`, with every intentional
  difference from upstream logged in `custom-pokebot/DIVERGENCE-LOG.md`.

### Daily upstream update check (user directive, 2026-07-17)
Once per calendar day, at session start (after the kit sync ritual): run
`git fetch upstream-pokebot` and compare `upstream-pokebot/main` against
the newest commit recorded in `40cakes repo/UPDATE-LOG.md`.
- If unchanged: append nothing; update the "Last daily check" date on the
  newest UPDATE-LOG entry.
- If upstream moved: (1) snapshot current `40cakes repo/DOCUMENTATION/*.md`
  into `DOCUMENTATION/_history/<YYYY-MM-DD>-<old-commit>/`; (2)
  `git subtree pull --prefix="40cakes repo/pokebot-gen3" upstream-pokebot main --squash`;
  (3) read the upstream diff and update the DOCUMENTATION files to match;
  (4) append an UPDATE-LOG entry (old -> new commit, summary, docs touched,
  changes pending review for custom-pokebot); (5) NEVER auto-apply
  upstream changes to `custom-pokebot/` — list them for the user to decide.

### Sandbox area (user directive, 2026-07-18)
- `sandbox-pokebot/` is the EXPERIMENTAL copy of custom-pokebot where new
  enhancement rounds are built and tested (`install_sandbox.py` sets it up
  and runs it). During a sandbox round, do NOT modify `custom-pokebot/` or
  the mirror. Sandbox features are promoted into custom-pokebot ONLY after
  explicit user approval, together with their DIVERGENCE-LOG entries and
  docs; after promotion the sandbox is re-based on the new custom.

### Gemini model floor — PRO 3.1+ ONLY (user directive, 2026-07-25)
- Research calls MUST use Gemini **Pro 3.1 or newer**. This is ENFORCED IN CODE:
  `gemini_relay.py` refuses anything else and exits with an explanation. A doc
  rule was not enough — the default was already correct and an agent still
  overrode it to a two-generation-old model on ~35 calls by copying a stale
  docstring example, then spent a day concluding "Gemini is inaccurate".
- **The usual correct invocation passes NO `--model` at all.** Only pass one to
  select a NEWER Pro. `--allow-weak-model` exists for cheap one-liners that
  genuinely do not need Pro; using it for research is a mistake.
- Flash / Flash-Lite / Gemma are refused regardless of version: the failures that
  motivated this were factual-recall errors, which is where small models are
  weakest.

### Gemini research notes — standing directive (user directive, 2026-07-24)
- **Use Gemini research agents (`tools/story-dev/gemini_relay.py`) whenever fixing
  or building anything story/mechanic/game related** — for extra context, for
  cross-referencing, for verifying, and for making the documentation more
  accurate. Multiple agents on different ANGLES beats one broad question.
- **Their output is always a NOTE, never a source of truth, and never replaces
  existing documentation.** It lands in `PROJECT KNOWLEDGE/ai-research-notes/`
  and the authoritative doc gets a STUB MARKER pointing to it. On any
  contradiction the authoritative doc WINS until the note is verified. See
  `ai-research-notes/00-READ-THIS-FIRST.md` for the rule and the per-claim
  verification gates (flags → `audit_flag_names.py`; coords → live probe;
  learnsets/encounters → `modules/data`; reachability → `calculate_path` from a
  real captured position PLUS a control tile that does path).
- **Verification passes must be ADVERSARIAL:** hand a later agent the earlier
  note and ask it to FIND ERRORS in it. Asking a second agent the same question
  just produces a second guess; asking it to refute produces information.
- **‼ CLAUDE VALIDATES GEMINI (user directive, 2026-07-25).** Gemini is the
  research FAN-OUT (cheap, many angles); the VALIDATION pass is a Claude
  subagent, because only Claude agents here have real tool access — they can
  `gh api repos/pret/pokeemerald/contents/<path>` to read the ACTUAL decomp,
  read `sandbox-pokebot/modules/data/*`, run `audit_flag_names.py`, and drive a
  live emulator probe. Gemini can only recall, and describing recall as
  verification is precisely how the 2026-07-24 item round produced ~100%
  confidence over content that contained a hallucinated item. The user has
  accepted the extra token cost for this. Never let a Gemini pass be the final
  word on a fact that code will depend on.
- Why the caution is not theoretical: in the first batch an agent confidently
  denied the existence of `ROUTE111_OLD_LADYS_REST_STOP`, which is in our own
  `map_data.py`, on the single most load-bearing question it was asked.

### Story-bot craft & documentation excellence (user directive, 2026-07-21)
- **Read `PROJECT KNOWLEDGE/14-AGENT-PLAYBOOK.md` every session** (right after the
  handoff). It is the accumulated method for building the Story bot: the faithful
  test harness, the debugging method (reproduce → fault-inject A/B → fix → prove),
  static ROM recon + Area Atlases, the renderer-gated faithful-vs-fallback pattern,
  and the recurring bug patterns + prevention rules. Follow it; keep it current.
- **Prove every fix** (reproduce first; A/B where possible) — no guessing. **Faithful
  to natural gameplay** — a state-write is a documented last-resort fallback that must
  reproduce vanilla's exact end-state. **Never hang / never silently derail** — bound
  every loop; un-fleeable battles must fight through; guard every "did it work?".
- **Document with INTENT + WHY**, not just what. Per completed item: changelog +
  (decision if a real choice) + (mistake + one-line prevention rule if a bug was fixed)
  + handoff. When you learn a new trick, add it to the playbook. Retire stale rules.
  Aim to leave the docs so the next agent builds/debugs/documents *better* than the last.
