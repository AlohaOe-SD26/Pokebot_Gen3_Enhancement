# PROJECT KNOWLEDGE — Pokebot_Gen3_Enhancement

This folder is the project's brain. Any agent (or human) starting a session
reads here FIRST. Created by the Claude Code Project Kit on 2026-07-17.

## Reading order
| # | File | What it tells you | Type |
|---|------|-------------------|------|
| 1 | `04-HANDOFF.md` | Where we are RIGHT NOW + what's next — ⚠ **start at the single `➡➡➡ START HERE` marker** (`grep -n '^>    ➡➡➡' 04-HANDOFF.md`). Since 2026-10-22 (S2-1b) it holds CURRENT STATE only, about 60 KB: a one-sentence `**Last updated:**` on line 6, WHAT THIS IS, `## If stopped mid-task` (the resume point the session-start hook injects), STATE, NEXT ACTIONS, the rules that bind every session, the parked story bot's live rules, HOW TO RUN / TEST. Its history, and the full pre-slim file, are in `28` | current-state |
| 2 | `14-AGENT-PLAYBOOK.md` | **HOW to work on this excellently** — tools, debugging method, story-mapping method, faithfulness rules, bug patterns | reference |
| 3 | `01-VISION-AND-DESIGN.md` | What this program is for; intent of each part | current-state |
| 4 | `02-ARCHITECTURE.md` | How it's built; how to run it | current-state |
| 5 | `03-PUNCH-LIST.md` | The work queue | current-state |
| 6 | `05-KNOWN-ISSUES.md` | Open bugs and traps (a few CLOSED entries stay, each marked CLOSED or FIXED in its header, where an auditor would otherwise re-flag them) | current-state |
| 7 | `08-MISTAKES.md` | Bugs/dead-ends already solved — don't repeat them | append-only |
| 8 | `06-DECISIONS-LOG.md` | Why things are the way they are. ⭐ Since 2026-10-21 it has a finding aid: `RULINGS.md` (generated, with the hand-curated `rulings-overlay.json`), searched by `py -3.12 tools/decomp_lookup.py ask "<topic>"` together with `facts-ledger.jsonl` (verified facts, append-only) and the pinned decomp; `06` always wins. `cost-ledger.jsonl` is the usage audit's per-workflow cost ledger (`tools/usage_audit.py`) | append-only |
| 9 | `07-CHANGELOG.md` | Everything that has ever changed | append-only |
| 10 | `12-STORYMODE-DESIGN.md` | Story bot design: chapters, Area Atlas (§AA), resume/defeat/self-correct | reference |
| 11 | `13-PLANNING-AND-RESILIENCE.md` | HOW the bot decides & stays robust: task model, resource ledger, contingency catalog, marts | reference |
| 12 | `30-METRICS.md` | **Which instrument answers which question, and at what n.** Read BEFORE measuring anything. Includes why the finish rate can never resolve a change | current-state |
| 13 | `27-INJECTION-SURFACE.md` | **How the bot OBSERVES and ACTS on the game** — the sensorimotor contract, every reader's silent failure mode, and the 8 timing traps. Written for the future self-training agent | reference |
| 14 | `29-DISABLED-FEATURES-REGISTRY.md` | Every `POKEBOT_*` flag with the MEASUREMENT behind it. **Check before proposing a feature** — enforced by lint R6 | current-state |
| 15 | `28-HANDOFF-ARCHIVE.md` | Superseded "you are here" snapshots, archived punch-list entries and completed build how-tos — **APPEND-ONLY, so OLDEST FIRST: the newest material is at the BOTTOM.** ⛔ *This row said "newest first" until 2026-08-16; it was backwards, so a reader taking it at its word read the OLDEST content believing it was the newest.* **Not current state** — read `04-HANDOFF.md` for the present. Its LAST section (2026-10-22, "HANDOFF SNAPSHOT") is the full pre-slim `04-HANDOFF.md`, verbatim: the story bot's complete handoff and driver recipes | append-only |
| 16 | `31-KNOWN-ISSUES-ARCHIVE.md` | ⛔ **NOT ALL RESOLVED — CHECK EACH HEADING** (that file's own top says so; a cold-start audit found this row describing it as resolved-only, which is a fourth place disagreeing about KI-59 — `05-KNOWN-ISSUES.md` is the correct one). Mostly resolved/superseded known issues, moved verbatim from `05-KNOWN-ISSUES.md` — including KI-39's REFUTED original beside its correction, and resolved KI-68, and KI-65 (archived 2026-08-18 — its named residual is kept in `05`'s stub). **Not current state**; `04`/`05`/`07`/`08` point into it | append-only |
| 17 | `26-REVIEW-AND-HARDENING-PLAN-2026-08-11.md` | **Point-in-time review**: progress, the 164-mistake taxonomy, why advisory rules do not prevent repeats, the hardening plan, doc-health findings and the future path | reference |
| 18 | `25-BACKUPS-AND-RESTORE.md` | **Restore points: how to revert to a known-good version.** Naming, what a tag does/doesn't capture, restore recipes, and the full inventory | current-state |
| 19 | `15-ESCALATION-RESEARCH.md` | Last-resort: hand a STUCK story sequence to an external research agent (Gemini) — the reusable primer + `/escalate-sequence` | reference |
| 20 | `16-ORCHESTRATION-PLAYBOOK.md` | **HOW to run a session cheaply**: premium orchestrator + cheap sub-model workers + Gemini; tier table, delegation rule, review gate, metrics — `/orchestrate` | reference |

### Read WHEN RELEVANT (not part of the start-of-session ritual)
*Added to this index 2026-07-27 — docs 09–11 and 17–23 existed but were invisible to anyone
following the reading order above, which stopped at 16.*

| File | What it tells you | Type |
|---|---|---|
| `24-PLAIN-ENGLISH-STATUS.md` | **START HERE FOR A HUMAN ANSWER** — what the bot does, what we fixed, what is stuck, in GAME terms with no jargon. Written for reading cold. ⚠ **Last brought current 2026-09-03** (its banner says what it misses); `04-HANDOFF.md` is current. | current-state |
| `09-FEATURE-BRAINSTORM.md` | the full future-idea catalog the punch list draws from | reference |
| `10-DEX-RESEARCH.md` / `11-LIVINGDEX-DESIGN.md` | Living-Dex feature research + design (#23) | reference |
| `17-PORTABLE-ORCHESTRATION-GUIDE.md` | running this orchestration setup on another machine/project | reference |
| `18-RESEARCH-HEALPOINTS-AND-LEGENDARIES.md` | heal-point + legendary encounter research notes | reference |
| `19-TEAM-BUILDING-DISCUSSION.md` | the user's three team requests + the two-axis personality design | reference |
| `20-POST-FORTREE-RECON.md` | Mt. Pyre, Aqua Hideout, gyms 7–8 recon + second-pass corrections | reference |
| `21-TEAM-POLICY-DESIGN.md` | **BUILD-READY**: catch policy, dead-weight predicate, rotation, counter ladder | reference |
| `22-CAPABILITY-RECON.md` | healing items, the PC, ground/hidden items, shops, money | reference |
| `23-MEANDER-PATHING-DESIGN.md` | the travel-meandering verdict + algorithm (currently net-negative — read before building it) | reference |
| `FABLE-5-KICKOFF.md` | onboarding brief written for a specific agent handover | reference |
| `REFERENCE-INSTALLER-PATTERN.md` | Nick's installer-as-codebase spec | reference |
| `batch-evidence/` | ⛔ **WAS INVISIBLE UNTIL 2026-08-22** — in neither table, and referenced from nowhere in the repo, while its own README says *"Every conclusion in `07-CHANGELOG.md` and `05-KNOWN-ISSUES.md` rests on it. Losing that directory would make the entire measured history unre-derivable."* The git-tracked analysis subset of the 2.2 GB gitignored batch runs | reference |
| `tools/story-dev/evidence/` | committed run transcripts and fault-injection drivers that named claims rest on — including `2026-08-22-pass4-fault-drivers/`, the injections that proved which gates can fail | reference |
| `ai-research-notes/` | **AI research output — NEVER AUTHORITATIVE; the decomp/code wins on any conflict.** ‼ **Two kinds live here and they are NOT weighted the same** *(corrected 2026-09-15 — this row said “Gemini output — RECALL ONLY”, which is stale since the 2026-08-12 Claude-subagent directive, and would make a reader discount a decomp-CITED note as mere recall)*: **Gemini** notes are RECALL ONLY (no tool access — grade their NAMES, never their architecture advice); **Claude subagent** notes can cite the decomp and our own tree, and the good ones tag each claim with how it was established. Either way a claim is a LEAD until verified in our harness. Read `ai-research-notes/00-READ-THIS-FIRST.md` before trusting a single line of it. | reference |

## Story-mode working process (commands)
- `/validate-docs` — before building a chunk (or when a build hits a wall), cross-check
  the doc section against decomp + live recon + walkthroughs; correct + re-verify.
- `/escalate-sequence` — LAST rung: if a sequence still can't be resolved, generate the
  two research prompts (primer + question) for an external agent; verify the answer
  before building. See `15-ESCALATION-RESEARCH.md`.
- `/livetest` — batch fresh-run sweeps → a Live Test report. ⛔ *(The pointer here used to say “see `04-HANDOFF.md`”; a Tier 2 audit found the handoff contains no Live Test section at all — one unrelated prose hit. Read the skill itself, `.claude/skills/`, and the batch entries in `07-CHANGELOG.md`.)*

## File rules
- **Current-state files — `01`-`05`, plus `24`, `25`, `29`, `30`:** edit in place. They must always
  describe present reality — stale content gets removed, not preserved.
- **Append-only files — `06`, `07`, `08`, plus the archives `28` and `31`:** new dated entries go at
  the END. Past entries are never rewritten, reordered, or deleted. `08-MISTAKES.md` is read at
  session start so past errors aren't repeated.
  ⛔ *Corrected 2026-08-22 (PASS 5): these two bullets listed only `01`-`05` and `06`-`08` while the
  tables above type SIX more files, and each of those files' own header agrees with the table. A
  reader following the bullets alone would have edited an append-only archive in place.*

## Definition of Done (summary)
Verified change → current-state docs updated → changelog/decisions appended
→ handoff updated → **Tier 0 doc gates** → **Tier 1 review** → commit → push.
Full version: see the managed block in the project root's `CLAUDE.md`.

‼ **The two gate steps are NOT optional and were missing from this summary until
2026-08-14** — a session orienting from this file alone would have committed over
an unrun gate. From `tools/story-dev/`, these must exit 0 before ANY commit
touching `PROJECT KNOWLEDGE/`. ‼ **IT SAID "ALL THREE" OVER *FOUR* COMMANDS AND NAMED NO SUBSET** (fixed 2026-09-26, found by a Tier 2 cold start) — so: a **DOC-ONLY** commit needs the last three (CLAUDE.md's Tier 0 is `lint_docs` + `audit_doc_consistency`; `audit_encoding` is cheap and catches mojibake). `run_gates.py` is required before any commit touching **CODE** — it takes ~130 s to 15 min, which is why the distinction matters:

```
PYTHONUTF8=1 py -3.12 run_gates.py              # THE STANDING SUITE — required before any CODE commit
PYTHONUTF8=1 py -3.12 lint_docs.py              # line budgets, banners, flag registry, R8 byte ratchet (new text on its own line)
PYTHONUTF8=1 py -3.12 audit_doc_consistency.py  # docs vs code vs each other
PYTHONUTF8=1 py -3.12 audit_encoding.py         # mojibake + BOM (--repair fixes in place)
```

**Tier 1** = one INDEPENDENT agent reviews the doc diff of a completed item (never a
fork of yourself — it inherits your blind spots). **Tier 2** = at session end, a
cold-start agent given ONLY this file and `04-HANDOFF.md`. Both are defined in
`CLAUDE.md`'s DOC CONSISTENCY LAYER. ‼ They exist because prose self-checks
demonstrably fail here: a Tier 2 audit on 2026-08-14 found five defects that would
have misdirected a fresh session, on a tree where every mechanical gate was green.
