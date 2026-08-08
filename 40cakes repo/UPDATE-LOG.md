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
- Last daily check: 2026-08-08 (upstream main still `5dd898f8` — no
  changes). Prior 2026-08-07, 2026-08-06, 2026-08-05, 2026-08-02: no changes. Prior 2026-07-31: no changes. Prior 2026-07-30: no changes.
  Prior 2026-07-26: no changes. Prior 2026-07-18: fetched new upstream
  branch `update-symbols` + release tags, main unaffected.
