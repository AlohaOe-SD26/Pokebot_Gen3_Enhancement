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

- `render.py` refuses an unresolved `{{placeholder}}`, an empty required value or field, an unranged READ-LIST file
  over 30 KB, and a prompt without the role's marker. Paste its `prompt` into the workflow script's `agent()` call
  (a JSON string is a valid JS string literal) and pass `model` when it is not null.
- Line 1 of every rendered prompt is `<!-- stage-template:<role>@<ver> -->`. `tools/usage_audit.py` counts a
  workflow agent whose first prompt lacks it as UNTEMPLATED, so compliance is measured, not assumed.
- A fix round runs only when `stage_helpers.py refix` says REFIX. UNKNOWN (a missing or malformed verdict) goes to a
  human, never to PASS.

## Model tiers (`models.json`)

Every stage ships at `top`. A stage moves to `mid` or `cheap` only with a `proof`: the JSON a plant run wrote
(3+ planted defects of 3+ kinds, all caught by the cheaper agent, one clean control with zero findings, for that
stage, tier and template version). `verify` is pinned to `top` in `lint_templates.PINNED_TOP`. When a template's
text changes, bump its `@<ver>`: a proof names `<role>@<ver>`, so the old proof then stops counting. Nothing
enforces the bump itself; an edit without one keeps a proof that tested other text.

## Tests

`tools/story-dev/selftest_workflows.py` (T-1 to T-8, FAULT + CONTROL each).
