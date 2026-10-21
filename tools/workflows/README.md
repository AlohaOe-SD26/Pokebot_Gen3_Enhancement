# tools/workflows: stage templates for workflow agents (spec S2-3)

**What this is.** The repo's ONE source of workflow-agent prompts. Each stage of a workflow (recon, build,
sweep-analysis, verify, doc-check) has a template in `templates/` with the same required fields: GOAL, READ-LIST
(paths with `:START-END` ranges), DO-NOT-READ, STOP, RETURN-CAP, MODEL, WAIT-RULE, MAP-FIRST, LOOKUP-FIRST.

**Why.** Before this, every workflow script was typed fresh, and the measured costs followed: agents opened with one
1.18 MB note, agents past 200 calls held 53 % of context weight, Opus-class agents were about 90 % of
input-equivalent (backlog P11, `PROJECT KNOWLEDGE/ai-research-notes/2026-10-18-improvement-backlog.md`). The templates
started from prompts that ran well on 2026-10-21 (the O3 build, adversarial review, fix and paperwork workflows).

## Use

```
py -3.12 tools/workflows/render.py build --values my-values.json --format json   # prompt + tier + agent() model
py -3.12 tools/workflows/lint_templates.py                                        # after editing a template
py -3.12 tools/workflows/stage_helpers.py refix <verdict.json>                    # PASS 0 / REFIX 1 / UNKNOWN 2
py -3.12 tools/workflows/regression_due.py                                         # which AI-player suites are stale
```

- `render.py` refuses (exit 2, nothing written): a template that does not pass the lint (so a MODEL line that
  disagrees with `models.json`, a tier below top without a valid proof, or `agent_model.top` set to a model never
  reaches `agent()`); a value that is not a JSON string, is over 20,000 characters, or holds a `## ` heading line, a
  second marker or an unclosed fence; an unresolved `{{placeholder}}`; an empty required value or field; and a
  READ-LIST entry that reads over 30 KB (a whole file, or a RANGE's own bytes), does not exist (unless tagged
  `[later]`), or sits unranged under DO-NOT-READ. Paste its `prompt` into the workflow script's `agent()` call (a JSON
  string is a valid JS string literal) and pass `model` when it is not null.
- A READ-LIST entry may be ANCHORED: `path:@<line prefix>+N` reads the N lines from the first line that starts with
  the prefix (what `grep -n '^<prefix>'` finds). `render.py` writes the concrete `path:START-END` into the prompt, and
  the lint measures the anchored range on every run, so a moved heading or a grown range is caught.
- Line 1 of every rendered prompt is `<!-- stage-template:<role>@<ver> -->`, and no other line may be a marker.
  `tools/usage_audit.py` counts a workflow agent as TEMPLATED only when the FIRST LINE of its first prompt (after the
  harness's user-request relay and computed-task framing) is exactly that marker for a role that has a template.
- A fix round runs only when `stage_helpers.py refix` says REFIX. UNKNOWN (a missing, malformed, contradictory or
  incomplete verdict: rule violations beside `all_pass: true`, a `failures` key spelled another way, duplicated keys,
  `complete` missing or false) goes to a human, never to PASS. A UTF-8 BOM is fine.

## Model tiers (`models.json`)

Every stage ships at `top`. `agent_model.top` must stay null (the coordinator's own model). A stage moves to `mid` or
`cheap` only with a `proof`: the JSON a plant run wrote, COMMITTED in this repo, of this shape:

```
{"stage": "<role>", "tier": "mid", "template": "<role>@<ver>", "template_sha256": "<lint_templates.template_digest>",
 "run": {"id": "<run id>", "transcript": "<an existing file>"},
 "plants": [{"id": "P1", "kind": "<kind>", "input": "<file>", "input_sha256": "<sha256 of its bytes, LF ends>"}, ...],
 "findings": [{"plant_id": "P1", "quote": "<text the agent quoted from that plant's input>"}, ...],
 "control": {"input": "<another file>", "input_sha256": "...", "findings": []}}
```

At least 3 plants of 3 different kinds, every one caught by a finding that quotes its input, and a clean control with
zero findings. `template_sha256` covers the whole template text except the MODEL line, so editing a template (even
without bumping `@<ver>`) retires its proof. `verify` is pinned to `top` in `lint_templates.PINNED_TOP`. Keep the run's
transcript in the repo next to the proof: a path that exists only on one computer fails the lint on the others.

## regression_due.py

`DUE` lines name what changed, or why the evidence cannot clear the suite: never run, no provenance, an unknown
commit, uncommitted evidence without a kept tree, or `unproven`: the evidence's code line records only `ai_player/`
(or `ai_player/ + hook`) while the suite also covers files outside that scope, or covers files git ignores. "ok"
means not stale; it says nothing about whether that run passed. `suite_map.json` must cover every module ai_player/
imports from this repo (the tool checks it with an import scan and exits 2 otherwise); what git ignores but a run
uses (the emulator binding, the bot's profiles) is listed under `environment` and printed as a NOTE.

## Tests

`tools/story-dev/selftest_workflows.py` (T-1 to T-8 and the fix round's T-2b, T-4b, T-5b, T-6b, T-7s/p/i/l; FAULT +
CONTROL each) and `tools/story-dev/selftest_usage_audit.py` U12 (the templated count).
