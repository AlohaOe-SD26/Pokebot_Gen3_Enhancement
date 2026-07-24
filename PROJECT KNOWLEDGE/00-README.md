# PROJECT KNOWLEDGE — Pokebot_Gen3_Enhancement

This folder is the project's brain. Any agent (or human) starting a session
reads here FIRST. Created by the Claude Code Project Kit on 2026-07-17.

## Reading order
| # | File | What it tells you | Type |
|---|------|-------------------|------|
| 1 | `04-HANDOFF.md` | Where we are RIGHT NOW + what's next | current-state |
| 2 | `14-AGENT-PLAYBOOK.md` | **HOW to work on this excellently** — tools, debugging method, story-mapping method, faithfulness rules, bug patterns | reference |
| 3 | `01-VISION-AND-DESIGN.md` | What this program is for; intent of each part | current-state |
| 3 | `02-ARCHITECTURE.md` | How it's built; how to run it | current-state |
| 4 | `03-PUNCH-LIST.md` | The work queue | current-state |
| 5 | `05-KNOWN-ISSUES.md` | Open bugs and traps | current-state |
| 6 | `08-MISTAKES.md` | Bugs/dead-ends already solved — don't repeat them | append-only |
| 7 | `06-DECISIONS-LOG.md` | Why things are the way they are | append-only |
| 8 | `07-CHANGELOG.md` | Everything that has ever changed | append-only |
| 9 | `12-STORYMODE-DESIGN.md` | Story bot design: chapters, Area Atlas (§AA), resume/defeat/self-correct | reference |
| 10 | `13-PLANNING-AND-RESILIENCE.md` | HOW the bot decides & stays robust: task model, resource ledger, contingency catalog, marts | reference |
| 11 | `15-ESCALATION-RESEARCH.md` | Last-resort: hand a STUCK story sequence to an external research agent (Gemini) — the reusable primer + `/escalate-sequence` | reference |
| 12 | `16-ORCHESTRATION-PLAYBOOK.md` | **HOW to run a session cheaply**: premium orchestrator + cheap sub-model workers + Gemini; tier table, delegation rule, review gate, metrics — `/orchestrate` | reference |

## Story-mode working process (commands)
- `/validate-docs` — before building a chunk (or when a build hits a wall), cross-check
  the doc section against decomp + live recon + walkthroughs; correct + re-verify.
- `/escalate-sequence` — LAST rung: if a sequence still can't be resolved, generate the
  two research prompts (primer + question) for an external agent; verify the answer
  before building. See `15-ESCALATION-RESEARCH.md`.
- `/livetest` — batch fresh-run sweeps → a Live Test report (see `04-HANDOFF.md`).

## File rules
- **Current-state files (01–05):** edit in place. They must always describe
  present reality — stale content gets removed, not preserved.
- **Append-only files (06, 07, 08):** new dated entries go at the END. Past
  entries are never rewritten, reordered, or deleted. `08-MISTAKES.md` is read
  at session start so past errors aren't repeated.

## Definition of Done (summary)
Verified change → current-state docs updated → changelog/decisions appended
→ handoff updated → commit → push. Full version: see the managed block in
the project root's `CLAUDE.md`.
