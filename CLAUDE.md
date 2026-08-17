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
- **‼ MEASURED 2026-07-25 (two model generations, same 10 prompts, ~65 claims
  adjudicated against the decomp) — three rules that follow from the data:**
  1. **AGREEMENT IS NOT A CONFIDENCE SIGNAL.** Where BOTH generations agreed they
     were still wrong ~35% of the time (15 BOTH-WRONG rulings). Disagreement is a
     great *search* strategy for finding claims worth checking; agreement proves
     nothing, because both models share the same misconceptions.
  2. **The two generations fail in DIFFERENT PLACES.** 2.5-pro hallucinates
     *citations* (invented a map AND a script label, tagged VERIFIED). 3.1-pro's
     names are excellent (phantom flag names 35% → 11%; head-to-head 21–1) but it
     hallucinates in the **actionable** section — all three of its "your bot must
     hardcode an interrupt here" constraints rested on permanence that does not
     exist. **Grade Gemini's NAMES highly and its ARCHITECTURE ADVICE not at all.**
  3. Therefore: use Gemini to enumerate *what to look for* (symbols, flags, map
     names, mechanics to check) and NEVER to decide what the bot should DO.

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

### ‼ CLAUDE SUBAGENTS ARE APPROVED FOR RESEARCH AND ASSISTANCE (user directive, 2026-08-12)
**Standing approval — no need to ask, now or in future sessions.** Use Claude
subagents (the Agent tool) freely for research, recon, cross-checking and any
other assistance. They proved their worth immediately: five parallel agents
resolved **KI-58** (the Mossdeep Gym) after four of my own offline models had
each concluded something impossible, and they turned up **two latent bugs in our
own pathfinder** (KI-59, KI-60) as a side effect.

How to get value out of them, learned from that round:
- **Fan out on different ANGLES, not the same question.** The five that worked
  were: decomp/layout mechanics, how a human plays it, an audit of OUR code, a
  live tile dump, and one explicitly ADVERSARIAL ("refute this claim"). The
  adversarial one found the answer.
- **Send them in ONE message so they run concurrently**, and keep working while
  they do — do not idle.
- **Tell them what is already RULED OUT**, with citations, so they do not re-derive
  it — but invite them to say if a ruled-out item is wrong.
- **‼ THEIR OUTPUT IS A NOTE, NEVER TRUTH — the same rule Gemini has.** Verify the
  load-bearing claim in our own harness before building on it. KI-58's mechanic
  was only believed after stepping on the switch live and watching the statues
  move. Three agents agreeing is a strong signal and still not proof: agreement
  is not a confidence signal (see the measured Gemini rules above).
- **Prefer them for anything large or noisy** — big read-only sweeps, decomp
  spelunking, adversarial review — so the bulk stays out of the main thread.

### ‼‼ SESSION DISCIPLINE — the failure modes that RECURRED WITHIN ONE SESSION (2026-08-13)

Written as PROPERTIES, not stories. **Every rule below was violated by an agent who had already
written that rule down, on the same day.** That is the whole reason this block exists: a rule filed
as "the lesson from bug X" does not fire when you are building Y.

0. ⛔ **CONFLICT WITH THE MANAGED BLOCK — FLAGGED FOR THE USER, 2026-08-13, NOT silently resolved.**
   Definition of Done **step 5 (line ~86) says "`git add -A` and commit"**, and that command is now
   **BLOCKED** by the hook in rule 1. Step 5 is INSIDE the Project Kit managed block, so editing it
   would be reverted by the next `Bootstrap-Project` run — which is why it is overridden here
   instead. **Until the user rules: step 5 means "stage explicit paths".** `/wrapup` and
   `/checkpoint` have already been corrected (they are outside the managed block).
   ‼ Do NOT "fix" this by reaching for `POKEBOT_ALLOW_BLIND_ADD=1` — routinely using the escape
   hatch restores the exact failure the hook exists to prevent.
1. **Stage EXPLICIT PATHS. Never `git add -A` / `git add .`** — subagents write into the working
   tree while you work, so a wildcard stage sweeps in unreviewed files.
   ✅ **ENFORCED, not requested:** `.claude/hooks/block-blind-git-add.ps1` denies it (allows
   `-u`/`-p`/explicit paths; `POKEBOT_ALLOW_BLIND_ADD=1` is the deliberate escape hatch).
   **Name every added file in the commit message** — if you cannot say what a staged file is, it
   does not belong in that commit.
2. **THE HEADLINE CARRIES THE CAVEAT.** A title that claims more than the evidence makes the
   document wrong no matter how careful the body is — a future agent skims the title and acts on
   it. Before writing "X already does Y", **read X to its LAST statement** (a trailing
   `set_manual_mode()` means it hands off to a human — the opposite of automation).
3. **Assert IDENTITY, never position or count.** PIDs — never slot indices, never party counts. A
   count that nets to zero (one deposited, one caught) reads TRUE when nothing happened.
4. **A liveness/acceptance check must derive its target from the state the run ACTUALLY reached,
   and must assert something the run does not already satisfy.** Hardcode no coordinates. When a
   probe FAILS, read the failing line before touching the thing under test — three times in one
   day the subject was correct and the CHECK was wrong.
5. **A broken instrument does not invalidate its past readings.** Re-derive a number before
   discarding it, and ask what question it ANSWERED — a count can be exactly right and its
   conclusion still wrong (reachability was never part of the count).
6. **Anything enforceable belongs in a GATE, not in prose here.** A rule already broken twice is
   evidence that prose failed — write the gate instead. ‼ **And FAULT-TEST every gate**: prove it
   fails when the thing it guards is broken, and prove it does NOT fire on mere mentions in
   comments or docstrings. A gate with false positives teaches the reader to bypass it, which is
   strictly worse than no gate.
7. **INSTRUMENT THE ACTION, NOT THE INPUT TO THE ACTION** (added 2026-08-17). A candidate list, an
   eligible set, a flag — none of them prove behaviour. ⛔ **A CANDIDATE IS NOT AN ATTEMPT.** Log the
   value the code actually ACTS on; if it lives in a local, rebind the callee to capture it. *Cost of
   learning this: a driver reported "KI-66 IS REPRODUCED" on a candidate list while the bot had, in
   fact, chosen correctly every time — the headline was refuted only when the requested slot was
   logged.* ‼ And when a tool prints two verdicts, **say out loud which one your claim rests on**.
8. **IDENTICAL OUTPUT ACROSS RUNS IS A DETERMINISM CHECK, NEVER A REPLICATION** (added 2026-08-17).
   Say *"one trajectory, replayed"* — never *"measured twice"*. ‼ Corollary, earned the same day:
   **a claim of the form "without X the bug survives" is a CLAIM**, and the only currency this
   project accepts for it is *an arm with X removed*. A latch shipped as load-bearing was measured
   REDUNDANT and deleted; had it stayed, a maintainer trusting it could have removed the guard that
   actually works. If you will not run that arm, do not write the sentence.
9. **CHOOSE THE INSTRUMENT BY THE QUESTION** (added 2026-08-17, and it is in §0c of the playbook).
   **Drivers answer CORRECTNESS questions; batches answer FREQUENCY questions.** A 3-hour batch is
   ~30 runs and has resolved nothing four times running, so reaching for one to check whether a code
   path REGRESSED is slower *and* less conclusive than a targeted A/B. ‼ When a change touches a
   shared path (e.g. every battle), the cheap decisive test is an A/B on the *ordinary* case, not
   more samples of the exotic one.
10. ⛔ **WHEN A FIX IS A COORDINATE CONVERSION, MEASURE ITS DIRECTION FIRST** (added 2026-08-17).
   Run an OBSERVE-ONLY probe printing both coordinates beside a ground truth derived independently,
   *then* apply it. Never reason it out from a docstring: `handle_fainted_pokemon` has now had
   **three** index-space bugs (KI-18, KI-34, KI-66) and a fourth is filed
   (`#24-faintchooser-fourthspace`). A backwards conversion is worse than the bug it replaces.


### ‼‼ DOC CONSISTENCY LAYER — independent eyes on documentation (user directive, 2026-08-13)

WHY: on 2026-08-13 a handoff answered all seven quality-bar questions and still sent the next
session to REBUILD FINISHED WORK — the banner said "Room 3 driven and passing" while the queue
490 lines below said "build Room 3"; a KI header claimed "ARMED" while its own body refuted it;
the file `00-README.md` sends cold readers to FIRST was five chapters stale. Root cause: each
increment updated one half of a pair and not the other. **Completeness was checked; CONSISTENCY
was not.** Prose self-checks demonstrably fail here (see SESSION DISCIPLINE above), so this layer
is gates + INDEPENDENT agents — ⛔ **no agent certifies text it wrote, and a fork does not count
as independent** (a fork inherits your context, and therefore your blind spots).

**THE PAIRS THAT MOVE TOGETHER.** Editing one half means editing — or explicitly re-confirming —
the other, IN THE SAME COMMIT. These are the named cross-checks, not "review the docs":
  P1  `04-HANDOFF` banner / YOU-ARE-HERE  ↔  `NEXT ACTIONS` queue item 0. "X is done" above
      forbids "build X" below. The queue is what a cold agent ACTS from; the banner is only
      what it reads first.
  P2  every touched `05-KNOWN-ISSUES` KI HEADER (title + status words)  ↔  that KI's newest
      dated body line. The header is the half that gets skimmed — the headline carries the caveat.
      ‼‼ **AND EVERY SECTION HEADING (`##`) ↔ THE STATUS OF *EVERY* BULLET UNDER IT** — added
      2026-08-15 because P2 was pointed only at KI headers and missed the single most expensive doc
      bug in the tree: a section headed *"OPEN ISSUES … do not conclude they are fixed"* whose FIRST
      bullet read *"✅✅ KI-59 — FIXED, A/B PROVEN, GATED"*. An adversarial cold-start priced that at
      ~a day of re-doing finished, gated, promoted work. ⛔ **A heading is a claim about every bullet
      beneath it**; if their statuses differ the heading must say MIXED and each bullet must carry
      its own marker.
  P3  `04-HANDOFF` STATE table + HOW TO RUN / TEST  ↔  this session's newest `07-CHANGELOG`
      entries. What shipped must be startable from the handoff alone.
  P4  `00-README` reading-order descriptions  ↔  the current top of each file this session
      touched. A stale pointer misdirects EVERY future cold start, not just one.
  (Numeric counts — gates, drift, artifact existence — are `audit_doc_consistency.py`'s job.
  Never hand-check what a gate checks; never let a gate's PASS stand in for the semantic pairs.)

**TIER 0 — every commit touching PROJECT KNOWLEDGE (mechanical, seconds, no agent):**
  `lint_docs.py` AND `audit_doc_consistency.py` exit 0 before the commit. Both are in
  `run_gates.py`. Committing docs over a red doc gate is the same offense as `git add -A`.

**TIER 1 — per COMPLETED WORK ITEM (not per commit): ONE cheap independent agent.**
  After the item's doc edits, BEFORE its commit: spawn ONE fresh subagent (reviewer-shape, cheap
  model, NOT a fork) with exactly three inputs — the doc DIFF, a one-paragraph claim of what the
  item actually did, and the pair list P1–P4. Its only question: *"for each pair, QUOTE both
  halves — do they agree, and does the queue reflect the claim?"* ‼ A finding without both quotes
  is DISCARDED — a noisy reviewer gets bypassed exactly like a noisy gate. Fix findings, re-run
  Tier 0, then commit. Routine doc touches that complete no item (typo, date bump) = Tier 0 only.

**TIER 2 — SESSION END (inside /wrapup, after doc edits, before the wrap-up commit):**
  Spawn ONE fresh cold-start agent given ONLY `04-HANDOFF.md` + `00-README.md` — no chat context,
  no claim paragraph, nothing you believe. It reports: (1) the exact FIRST ACTION a next session
  should take and the line commanding it; (2) P1–P4 with both halves quoted; (3) any instruction
  to do a thing the same file marks done. Compare (1) against what YOU know is true — a mismatch
  is a DOC bug; fix and re-run Tier 0 before committing. ‼ Two clean audits in a row do NOT
  retire this tier — agreement is not a confidence signal (measured; see the Gemini rules).

  ‼‼ **(4) AND — ADDED 2026-08-15 BECAUSE (1)–(3) PASSED TWICE OVER A BROKEN HANDOFF — THE AGENT
  MUST TRY TO *BEGIN* THE NEXT ITEM AND REPORT WHERE IT GETS STUCK.** Not implement it: prepare it.
  It must state the plan, NAME the fixture/save/anchor it would use, list which values the docs GIVE
  it and which they WITHHOLD, and answer one blunt question — *"could I start right now with no
  human input, yes or no?"* ⛔ **If the item is an A/B or a repro, it must COMPUTE THE DISCRIMINATOR
  on the named fixture and show the arms actually differ.**
  **WHY (measured, this session, not theory):** a handed-off spec passed the consistency checks
  twice while naming a fixture that made its own A/B **vacuous** — `team_max 39` against a
  threshold of `wild_max + 8 = 35`, so the flag under test was identical in BOTH arms and the run
  would have shown "no difference", reading as a REFUTATION of a true finding. Consistency checks
  cannot see that: the document was perfectly self-consistent and perfectly unusable. The next pass
  then found the FIX had been applied to the history block while the QUEUE HEAD kept the stale
  text — so ⇒ **when a Tier 2 finding is fixed, re-run Tier 2 and check WHERE the fix landed, not
  merely THAT it landed.** ‼ *The strongest audit of a handoff is not "is it consistent?" but "can
  someone START from it?"*
  `/checkpoint` runs Tier 1 instead of Tier 2: the user is stopping NOW, and the pair check is
  the cheap half that catches a lying resume pointer — the half that strands the next machine.

⛔ **DoD COMPOSITION NOTE (managed block, Definition of Done steps 2–4 — an ADDITION, not a
conflict, 2026-08-13).** Those steps say "update docs" with no consistency check; they are inside
the managed block, so the requirement lives here: **steps 2–4 are not COMPLETE until Tier 0
passes and (for a completed item) Tier 1 returns PASS; step 5 (commit) may not begin before
that. The session's final step-6 push may not happen before Tier 2 returns clean.** `/wrapup`
and `/checkpoint` carry these steps explicitly (they are outside the managed block).
