Run a project health check, repair what is SAFE to repair, and report PASS/WARN per item:

1. **Docs:** all nine files exist in `PROJECT KNOWLEDGE/` (00-README through 08-MISTAKES). Missing ones: recreate from `PROJECT KIT/templates/PROJECT KNOWLEDGE/` (replace `Pokebot_Gen3_Enhancement` with the project folder name and `2026-07-17` with today), then note the repair in the changelog.
2. **Directives:** `CLAUDE.md` contains exactly ONE `<!-- BEGIN PROJECT-KIT DIRECTIVES ... -->` / `<!-- END PROJECT-KIT DIRECTIVES -->` pair. Compare the `[kit vX.Y]` stamp on the BEGIN line against the contents of `PROJECT KIT/VERSION` — if older, recommend re-running `PROJECT KIT/Bootstrap-Project.bat` (do not edit the block by hand).
3. **Git:** report working-tree status, current branch, unpushed commits (`git log @{u}..HEAD --oneline`), and remote reachability (`git ls-remote origin HEAD`). If there are pushable commits and the tree is clean, push them.
4. **Mid-task state:** does `04-HANDOFF.md` → "If stopped mid-task" hold pending work? If yes, surface it prominently — that is the resume point.
5. **Large files:** any tracked file over 95MB (GitHub rejects >100MB)? Recommend gitignore/Git LFS.
6. **Environment:** if `claude` is available, run `claude doctor` and surface anything it flags (install health, updates); report but never auto-change it. Confirm `git` and `gh` are on PATH and `gh auth status` is logged in; if not, point the user to `Install-Environment.bat`.
7. **Doc staleness:** if the handoff's "Last updated" predates the most recent code commit, flag it and offer to refresh the handoff now.

Never do anything destructive without asking. Finish with a compact PASS/WARN summary list.
