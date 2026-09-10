# 40Cakes Upstream — Update Log
> APPEND-ONLY running record of upstream syncs. The newest entry's
> "Upstream commit" is the commit currently mirrored in `pokebot-gen3/`.
>
> **Daily ritual (standing directive in CLAUDE.md):** once per calendar
> day, at session start: `git fetch upstream-pokebot` and compare
> `upstream-pokebot/main` to the commit below. If upstream moved:
> 1. Snapshot the current docs: copy `DOCUMENTATION/*.md` into
>    `DOCUMENTATION/_history/<YYYY-MM-DD>-<old-commit>/`.
> 2. Pull: `git subtree pull --prefix="40cakes repo/pokebot-gen3" upstream-pokebot main --squash`
> 3. Read the upstream diff, update the DOCUMENTATION/ files to match.
> 4. Append an entry here (date, old → new commit, summary of upstream
>    changes, which docs changed).
> 5. Do NOT auto-apply upstream changes to `custom-pokebot/` — list them in
>    the entry as "pending review for custom" and let the user decide.

---

## 2026-07-17 — Initial mirror
- **Upstream commit:** `5dd898f8` (40Cakes/pokebot-gen3 `main`)
- Mirrored via `git subtree add --squash` at `40cakes repo/pokebot-gen3/`.
- DOCUMENTATION/ 00–05 written against this commit (docs v1).
- Last daily check: **2026-09-10** (`git fetch upstream-pokebot` → `upstream-pokebot/main` still
  `5dd898f8`, unchanged; tree hash RE-DERIVED both sides this date and equal at
  `fa3504a285eb62fa` — mirror `HEAD:40cakes repo/pokebot-gen3` vs `upstream-pokebot/main^{tree}`;
  nothing to pull, nothing appended per the standing directive).
  ⚠ **2026-09-08 AND 2026-09-09 WERE MISSED** — those sessions ran long on `#24-lowlevelmules`
  telemetry and the batch, and never performed the check. Recorded rather than quietly backfilled,
  for the same reason the 2026-09-03 gap below is: the directive is once per CALENDAR DAY, so a gap
  is a fact about our process. Nothing was lost (upstream did not move across the gap — the commit
  and the tree hash are unchanged from 2026-09-07), but a silently-skipped check would make the
  next real upstream move look like it landed overnight.
  Prior 2026-09-07 (no changes). Prior 2026-09-02, 2026-09-01 (no changes).
  ⚠ **2026-09-03 WAS MISSED** — that session ran long on §Ch23 and never performed the check.
  Recorded rather than quietly backfilled: the directive is once per CALENDAR DAY, and a gap is a
  fact about our process, not about upstream. Nothing was lost (upstream did not move), but a
  silently-skipped check would make the next real upstream move look like it landed overnight.
  ‼ Also RE-DERIVED on this date, not merely fetched: the mirror is byte-identical to upstream by
  TREE HASH — `git rev-parse 'HEAD:40cakes repo/pokebot-gen3'` and
  `git rev-parse 'upstream-pokebot/main^{tree}'` are both `fa3504a285eb62fa`, and
  `git log --full-history -- "40cakes repo/pokebot-gen3"` shows exactly ONE commit ever touched the
  prefix (`c5045771`, the subtree merge) ⇒ **no hand-edits, as the standing directive requires.**
  ⛔ Use the TREE-HASH comparison, not `git diff upstream-pokebot/main -- <prefix>`: with a
  `--squash` subtree the prefix has no shared history upstream, so that diff reports a meaningless
  `4290 files changed`. *(Gap note: 2026-08-19..21 had no session, so no check was recorded on
  those calendar days; the recorded commit was still correct, so nothing was missed.)*
  Prior 2026-08-28 (no changes). Prior 2026-08-27 (no changes). Prior 2026-08-22 (no changes; mirror tree re-derived identical). Prior 2026-08-18 (no changes). Prior 2026-08-16 (no changes). Prior 2026-08-15 (no changes). Prior 2026-08-14 (no changes). Prior 2026-08-13 (no changes). Prior 2026-08-12 (upstream main still `5dd898f8` — no changes). Prior 2026-08-11 (no
  changes), 2026-08-10 (no
  changes). Prior 2026-08-09 (no
  changes). Prior 2026-08-08, 2026-08-07, 2026-08-06, 2026-08-05, 2026-08-02: no changes. Prior 2026-07-31: no changes. Prior 2026-07-30: no changes.
  Prior 2026-07-26: no changes. Prior 2026-07-18: fetched new upstream
  branch `update-symbols` + release tags, main unaffected.
