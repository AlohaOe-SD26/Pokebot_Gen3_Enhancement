# Mistakes & Dead-Ends — Pokebot_Gen3_Enhancement
> APPEND-ONLY. The point of this file: never solve the same problem twice and
> never re-walk a known dead-end. Future sessions read this BEFORE starting so
> past errors aren't repeated. New entries go at the END, with a date.
>
> Log a entry whenever: a bug took real effort to fix, an approach was tried
> and abandoned, an assumption turned out wrong, or a fix corrected a mistake.
> Entry format:
>
> ## YYYY-MM-DD — short title  (ML-N)
> - **Symptom:** what went wrong / what was observed
> - **Context:** file(s), feature, or area
> - **Root cause:** what was actually wrong (not just the symptom)
> - **Fix:** what resolved it (the approach that worked)
> - **Prevention:** one-line rule so it doesn't recur
> - **Retire when:** (optional) the structural change that makes the
>   prevention rule unnecessary (e.g. "a test now covers this") — once true,
>   the rule can be dropped from CLAUDE.md to save context.

---

## 2026-07-17 — Agent-written docs contained ~4% wrong claims  (ML-1)
- **Symptom:** The initial deep-documentation pass (written by 5 parallel
  agents) read convincingly but contained 39 factual errors across ~975
  verifiable claims (~4%): off-by-N line refs, an inverted behavior claim
  (LoseOnPurpose/Explosion), invented capabilities (navigate_to crossing
  warps; a repo-root sprites/ dir; OBS "hotkey" mechanism), wrong return
  types, and a wrong error-handling claim (work-queue errors exit the
  process, not drop to Manual).
- **Context:** `40cakes repo/DOCUMENTATION/00–05`, `Pokemon_Emerald_AI_Notes.md`.
- **Root cause:** First-pass documentation states plausible inferences with
  the same confidence as verified facts; some errors even originated from
  stale comments/docstrings in the upstream source itself (e.g. the
  obs.py header, the `disable_default_battle_handler` docstring).
- **Fix:** A second adversarial verification pass (6 agents, one per doc,
  instructed to open every cited file:line and re-derive every behavioral
  claim from code) fixed all 39 and flagged what remained unverifiable.
- **Prevention:** Never build on agent-written technical docs until they
  have survived an adversarial verify pass; and treat upstream
  comments/docstrings as claims to verify, not facts.
