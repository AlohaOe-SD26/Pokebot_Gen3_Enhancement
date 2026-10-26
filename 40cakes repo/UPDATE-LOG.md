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
>    ⛔⛔ **ASK THE USER BEFORE RUNNING THIS STEP.** It fetches *and MERGES*, writing a merge
>    commit onto `main`; force-push and history rewriting are BANNED in this project, so it is
>    **not trivially undoable once pushed** (CLAUDE.md: ask before any destructive git
>    operation). And the WORKING TREE MUST BE CLEAN — `git subtree pull` runs `ensure_clean()`
>    and dies `fatal: working tree has modifications`. *(Added 2026-09-26: a cold-start audit
>    found this step carried NO approval note, while three separate pointers told a fresh agent
>    to "just run the 5 steps" — a safety caveat is worthless in 1 of 4 places.)*
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
- ⏸ **Daily check 2026-10-26 — UPSTREAM MOVED A SEVENTH TIME; STILL PARKED BY USER RULING.** `upstream-pokebot/main` = **`f14ab79d`** *“Merge pull request #846 from hanzi/windows-python315-fix”* (committed 2026-10-27 03:50 +0700), 2 new commits since `7f3d6be8`: Python 3.15 support (`fb484279`) and a fix for installing on Windows with Python 3.15 (`f1717a26`). No check was recorded for 10-25 beyond the re-check line on the 10-24 entry. ‼ **NOTHING WAS PULLED AND NO DOCS WERE TOUCHED** (the sync is parked). Pending review for `custom-pokebot/` when the user unparks it: these 2 plus the 17 of 10-24, none applied.
- ⏸ **Daily check 2026-10-24 — UPSTREAM MOVED A SIXTH TIME; STILL PARKED BY USER RULING.** `upstream-pokebot/main` = **`7f3d6be8`** *“Merge pull request #843 from hanzi/safari-mode-clones”* (committed 2026-10-24 04:10 +0700), i.e. **29** commits ahead of the mirrored `5dd898f8`, 17 of them new since `3bd0b70c` (PRs #835-#843): Tk 9 variable traces (#835); Python 3.14 support, a fixed requirements script and an explicit `requests` dependency (#837); window scaling on Wayland (#838); a debug-tab crash and HTTP 500s on uninitialised cache items (#839); a segfault when the HTTP server reads stats while the bot writes them (#840); duplicate Rock Smash encounters after soft resets in Emerald (#841); more distinct RNG seeds from FR/LG soft resets (#842); and Safari mode / Roamer Reset duplicate encounters and running out of Repel in Safari mode (#843). No check was recorded for 10-23. ‼ **NOTHING WAS PULLED AND NO DOCS WERE TOUCHED** (the sync is parked). Pending review for `custom-pokebot/` when the user unparks it: all 17, none applied. Re-checked **2026-10-25**: unchanged (`7f3d6be8`), still parked.
- ⏸ **Daily check 2026-09-30 — UPSTREAM MOVED A FIFTH TIME; STILL PARKED BY USER RULING.** `upstream-pokebot/main` = **`3bd0b70c`** *“Merge pull request #831 from hanzi/docker-improvements”*, i.e. **12** commits ahead of the mirrored `5dd898f8` (new since 2026-09-29: `6739e9ba` *“Make WebRTC optional and allow configuring TURN servers”* (#830), `81c82632` *“Remove bundling code and improve handling in Docker images”* (#831) and their two merge commits; 9 files, +641/−339: `modules/web/http.py`, a NEW `modules/web/webrtc.py`, `modules/web/static/index.html`, `modules/config/schemas_v1.py`, `modules/config/templates/http.yml`, `modules/runtime.py`, `pokebot.py`, `requirements.py`, and `pokebot.spec` DELETED). Nothing pulled, no docs touched; the mirror is still correctly `5dd898f8`. Pending review for custom when the sync is taken up: the web-server/WebRTC changes, and #831's removal of `pokebot.spec` (KI-1 documents that file as stale upstream). Re-checked **2026-10-01**: unchanged (`3bd0b70c`), still parked. Re-checked **2026-10-02**: unchanged (`3bd0b70c`), still parked. Re-checked **2026-10-03**: unchanged (`3bd0b70c`), still parked. Re-checked **2026-10-07**: unchanged (`3bd0b70c`), still parked (no sessions 10-04..10-06). Re-checked **2026-10-14**: unchanged (`3bd0b70c`), still parked (no check recorded for 10-08..10-13). Re-checked **2026-10-22**: unchanged (`3bd0b70c`), still parked (no check recorded for 10-15..10-21).
- ⏸ **Daily check 2026-09-29 — UPSTREAM MOVED A FOURTH TIME; STILL PARKED BY USER RULING.** `upstream-pokebot/main` = **`fe68b4f4`** *“Merge pull request #829 from hanzi/control-flow”*, i.e. **8** commits ahead of the mirrored `5dd898f8` (new since 2026-09-28: `ec80d586` *“Fix race conditions in HTTP server”* (#828), `aa95f019` *“Change control flow to flatten call stack”* (#829) and their two merge commits; 12 files, +230/−135, the largest `modules/web/http.py`, `modules/gui/__init__.py`, `modules/main.py` and `pokebot.py`). Nothing pulled, no docs touched; the mirror is still correctly `5dd898f8`. Pending review for custom when the sync is taken up: #829 changes the bot's main loop. Re-offer the sync to the user.
- ⏸ **Daily check 2026-09-28 — UPSTREAM MOVED A THIRD TIME; STILL PARKED BY USER RULING.** `upstream-pokebot/main` = **`1ca1736d`** *“Improvements to the WebRTC implementation (#827)”*, i.e. **4** commits ahead of the mirrored `5dd898f8` (on top of `f0a14cad` #826, `84c6064c` #824, `7ee780d4`). Nothing pulled, no docs touched; the mirror is still correctly `5dd898f8`. Re-offer the sync to the user (the 2026-09-26 ruling is “not now”, not “never”).
- ⏸ **2026-09-26 (later) — UPSTREAM MOVED AGAIN, AND THE USER RULED “NOT NOW, KEEP IT PARKED”.** Re-fetched: `upstream-pokebot/main` = **`f0a14cad`**, i.e. **3** commits ahead of the mirrored `5dd898f8` — the two below plus `f0a14cad` *“Reduce usage of global state (#826)”*, which makes the diff **28 files** (`modules/game.py` +266 the largest), no longer the one Tk file. Asked with those facts; answer recorded in `PROJECT KNOWLEDGE/06-DECISIONS-LOG.md` 2026-09-26. ⇒ **still nothing pulled, no docs touched; the mirror is still correctly `5dd898f8`.** Keep doing the daily check; do NOT run step 2 without asking again (“not now” is not “never” — re-offer it).
- ⛔⛔ **UPSTREAM HAS MOVED — FIRST TIME SINCE THE MIRROR WAS CREATED. THE SYNC IS *NOT* DONE; IT IS PARKED.** Daily check **2026-09-26**: `git fetch upstream-pokebot` ⇒ `upstream-pokebot/main` = **`84c6064c`**, i.e. **2 commits ahead** of the mirrored `5dd898f8`:
  * `7ee780d4` — *"Don't require Tk to run in headless mode"*
  * `84c6064c` — merge of upstream PR **#824** (`iqno/headless-without-tkinter`)
  ‼ **NOTHING WAS PULLED AND NO DOCS WERE TOUCHED.** The 5-step procedure at the top of this file includes a `git subtree pull --squash` (a MERGE INTO `main`) and a documentation pass; the session was ending, so it was parked rather than half-done. ✅ The mirror is therefore still *correctly described* by the entry below — it really is at `5dd898f8`. ⇒ **NEXT SESSION: run the 5 steps from the top of this file**, and remember step 5 — do NOT auto-apply anything to `custom-pokebot/`; list it for the user. ⚠ The change looks small and low-risk for us (headless Tk import), but "looks small" is not a reason to skip the docs step.
- Prior daily check: **2026-09-17** (`git fetch upstream-pokebot` → `upstream-pokebot/main` still
  `5dd898f8`, unchanged; tree hash RE-DERIVED both sides this date and equal at
  `fa3504a285eb62fa` — mirror `HEAD:40cakes repo/pokebot-gen3` vs `upstream-pokebot/main^{tree}`;
  nothing to pull, nothing appended per the standing directive).
- Prior daily check: **2026-09-16** (`git fetch upstream-pokebot` → `upstream-pokebot/main` still
  `5dd898f8`, unchanged; tree hash RE-DERIVED both sides this date and equal at
  `fa3504a285eb62fa` — mirror `HEAD:40cakes repo/pokebot-gen3` vs `upstream-pokebot/main^{tree}`;
  nothing to pull, nothing appended per the standing directive).
  ⚠ **2026-09-15 WAS MISSED** — recorded, not quietly backfilled, for the same reason as every gap
  below: the directive is once per CALENDAR DAY, so a gap is a fact about our process. Nothing was
  lost — the commit and the tree hash are unchanged across it.
- Prior daily check: **2026-09-14** (`git fetch upstream-pokebot` → `upstream-pokebot/main` still
  `5dd898f8`, unchanged; tree hash RE-DERIVED both sides this date and equal at
  `fa3504a285eb62fa` — mirror `HEAD:40cakes repo/pokebot-gen3` vs `upstream-pokebot/main^{tree}`;
  nothing to pull, nothing appended per the standing directive).
  ⚠ **2026-09-11, 2026-09-12 AND 2026-09-13 WERE MISSED** — those sessions ran long on the `#24-e4healing` step-3 build, its live drive, and five rounds of doc review. Recorded, not quietly backfilled, for the same reason as every gap below. Nothing was lost: the commit is STILL `5dd898f8` and the tree hash was RE-DERIVED both sides on 2026-09-14 and is still `fa3504a285eb62fa`, i.e. upstream did not move across the gap.
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
