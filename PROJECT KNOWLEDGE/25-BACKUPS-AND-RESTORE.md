# 25 — BACKUPS & RESTORE POINTS

> **Current-state file, but an INDEX — NOT the record.** ⛔ **`git for-each-ref --sort=creatordate
> refs/tags/restore/` IS THE AUTHORITY** (ruling 2026-08-15, see §6); this file carries the WHY and
> will always lag the WHAT — it was **6 tags stale** when an audit caught it. Keep the inventory
> below complete anyway, **oldest first**, with what each captured and why it exists.

## 0. TL;DR — how to get back to a known-good version

```bash
git fetch --tags                                   # restore points live on the REMOTE
git tag -l 'restore/*' 'backup/*' 'baseline/*'     # what is available
git show restore/2026-08-11-all-promoted           # what a point IS, before touching anything
git switch -c inspect-0811 restore/2026-08-11-all-promoted   # look around SAFELY, on a branch
```
‼ **Reading a restore point never changes anything. Start there.** Only the recipes in §5 modify
the working tree, and the destructive one requires the user's say-so.

---

## 1. The mechanism, and why it is this one

A restore point is an **annotated git tag, pushed to `origin`**. Not a zip, not a folder copy.

| property | why it matters here |
|---|---|
| **immutable** | a tag names one exact commit; it cannot silently drift the way a *file* can — and this project lost three separate results in one day to "same filename, different bytes" (`08-MISTAKES` 2026-08-11) |
| **off-machine** | pushed to GitHub. This project is worked on from **multiple computers**; a local archive protects against nothing that matters |
| **zero bloat** | the objects already exist in history. A 63 MiB zip per checkpoint would not |
| **carries its reason** | an *annotated* tag holds a message. A restore point whose purpose nobody recorded is nearly useless a month later |

‼ **A LIGHTWEIGHT TAG IS NOT ENOUGH.** Three of the 2026-07-23 points are lightweight
(`objecttype=commit`), so their "subject" in any listing is just *the commit message that happened
to be at HEAD* — not why the point was taken. Always `git tag -a`.

### For true offline archival (optional, rarely needed)
A single self-contained file with the entire history — restores everything even with no GitHub:
```bash
git bundle create ../Pokebot-backup-$(date +%Y-%m-%d).bundle --all
# restore:  git clone Pokebot-backup-YYYY-MM-DD.bundle restored-repo
```
‼ Store it **outside** the repo. Committing a bundle *of* the repo *into* the repo is circular and
bloats every future clone.

---

## 2. Naming convention (canonical from 2026-08-11)

```
restore/<YYYY-MM-DD>-<short-slug>
```
ISO date first so tags sort chronologically; slug says what the point is *for*.

‼ **The history is inconsistent and that is deliberate not to rewrite.** Four shapes exist:
`backup-pre-X-DATE` (legacy, no slash), `backup/DATE-X`, `baseline/X`, `restore/X-DATE`. **Do not
rename or delete old tags** — they are published refs, and the project's git conduct rule forbids
rewriting published history. New points use the canonical form; old ones stay as they are.

**Prefix meanings as actually used:**
| prefix | meaning |
|---|---|
| `restore/` | "put the tree back here if the next thing goes wrong" — the default |
| `backup/` | same intent, older spelling |
| `baseline/` | a point captured to be the **A arm of a comparison**, not to revert to |
| `v*`, `2024*`, `2025*` | ‼ **UPSTREAM pokebot-gen3 release tags**, pulled in by the subtree. **Not ours.** 116 of them. Never treat these as project restore points |

---

## 3. ‼ What a restore point DOES and DOES NOT capture

Measured on 2026-08-11 against `restore/2026-08-11-all-promoted`:

**CAPTURED** (inside the tagged tree):
* all code — `sandbox-pokebot/`, `custom-pokebot/`, `40cakes repo/`, `tools/`
* all `PROJECT KNOWLEDGE/` docs and the divergence/update logs
* **the ROM** — tracked ON PURPOSE (user ruling 2026-07-18, re-affirmed 2026-08-23; see
  `06-DECISIONS-LOG.md` and KI-82). ⛔ **This is why a restore point is "a runnable program" —
  untracking it would silently break that promise on every existing tag.** Two tree entries
  (`sandbox-pokebot/roms/`, `custom-pokebot/roms/`) sharing ONE git blob, so the repo stores one
  copy, not two. ⚠ Revisit ONLY if this repository is ever made public
* **all save fixtures** — **78** tracked files under `tools/story-dev/saves/` (**76** of them
  `.ss1`), including the pinned anchors and `FIXTURES.md5`. *(Re-measured 2026-08-22; this read
  "69 / 67" and was stale — `git ls-files tools/story-dev/saves/` is the authority.)*
  ⚠ **77 `.ss1` exist on disk; the one extra is `midstuck.ss1`, DELIBERATELY gitignored** — it was
  a shared scratch path every concurrent run overwrote, so it was demoted on purpose. It is a
  restore-point HOLE only in the sense that it was never meant to be one.
  ⛔ **And only 11 of those have a `FIXTURES.md5` row at all** — see `#24-fixturecoverage`; the
  other 66 are neither PINNED nor declared VOLATILE, so `verify_fixtures.py` cannot see them drift.

**NOT CAPTURED** (git-ignored; a restore leaves these as they are on the machine):
| not captured | how to get it back |
|---|---|
| `*/mgba/` — the emulator binary (**0 files tracked**) | re-run `install.py` / `install_sandbox.py` |
| profile runtime state (`profiles/*/`) beyond 4 tracked files | regenerated on next run |
| `logs/`, `cache/`, `backups/`, `__pycache__/` | disposable |
| `tools/story-dev/x4-runs/` — batch output | **not recoverable.** Batch results live only in the docs that quote them, which is why every batch claim in `07-CHANGELOG` carries its numbers inline |

⇒ **A checkout of a restore point gives you a runnable program** once `mgba` is present. It does
**not** give you back a deleted batch log.

---

## 4. When to create one

* **Before any autonomous or long unattended round** (this is what the 2026-07-20/21 points were for).
* **Before a change with wide blast radius** — shared battle strategy, config defaults, anything
  touching every mode.
* **Before deliberately re-enabling a feature that was measured harmful** (e.g. `POKEBOT_PC_ROTATION`).
* **At the end of a round where everything is green and promoted** — so there is a known-good floor.
* **Before a bisect**, to name the far end (`restore/pre-bisect-20260804`).

Cost is ~zero. Under-tagging is the only real failure mode.

---

## 5. Restore recipes

### (a) Just look — never modifies anything
```bash
git show restore/2026-08-11-all-promoted --stat | head -40   # the message + what changed
git show restore/2026-08-11-all-promoted:sandbox-pokebot/modules/story/early_game.py | head -60
git diff restore/2026-08-11-all-promoted..HEAD --stat        # what has changed SINCE
```

### (b) Recover ONE file from a restore point (the common case)
```bash
git checkout restore/2026-08-11-all-promoted -- path/to/file.py
```
‼ Then run `tools/story-dev/verify_fixtures.py` if you restored anything under `saves/`.

### (c) Undo a bad change while KEEPING history — **preferred**
```bash
git revert <bad-commit>          # or: git revert <oldest>..<newest>
```
Safe, reviewable, pushes normally, and leaves the record of what happened. **Use this by default.**

### (d) Full rollback of the working tree — **ask the user first**
```bash
git switch -c rollback-from-0811 restore/2026-08-11-all-promoted
```
A **branch** at the restore point. Nothing is destroyed and it can be merged or abandoned.

‼ **`git reset --hard`, `git clean -f`, force-push and branch deletion are DESTRUCTIVE and the
project's git conduct rule requires asking the user before any of them.** Never force-push to move
`main` back — that rewrites published history for every other machine.

---

## 6. INVENTORY — every restore point, oldest first

| date | tag | annotated? | what it captures / why |
|---|---|---|---|
| 2026-07-20 | `backup-pre-overnight-2026-07-20` | ✅ | before autonomous overnight move-learn debugging. HEAD=`f24d8b99` |
| 2026-07-21 | `backup-pre-features-2026-07-21` | ✅ | before autonomous build: defeat-handling, thresholds, catching, Ch5b |
| 2026-07-23 | `backup-pre-sufficiency-2026-07-23` | ❌ lightweight | before the sweeper-sufficiency prep gate |
| 2026-07-23 | `backup-pre-resume-robustness-2026-07-23` | ❌ lightweight | before resume-robustness work |
| 2026-07-23 | `backup-pre-ch12-2026-07-23` | ❌ lightweight | before Ch12 |
| 2026-07-29 | `backup/pre-trainmap-2026-07-29` | ✅ | before `#24-trainmap+` training-area work |
| 2026-07-30 | `baseline/ki40` | ✅ | **comparison baseline, not a revert target** — isolates 4 production commits from 10 prior KI-34/35/36/37 ones |
| 2026-07-31 | `backup/2026-07-31-ki38-fixed` | ✅ | KI-38 after-faint chooser fixed and live-confirmed |
| 2026-08-04 | `restore/pre-bisect-20260804` | ✅ | before bisecting the batch8→11/12 decline (52.8%→37.0%). Suite 77/77 |
| 2026-08-05 | `restore/session-end-20260805` | ✅ | regression closed (52.0%), three harmful features flagged off, counter chain end-to-end. Suite 78/78 |
| **2026-08-11** | **`restore/2026-08-11-all-promoted`** | ✅ | **zero drift sandbox↔custom; `#24-teachmsgstall` + KI-51 + KI-52 + status telemetry all promoted; gate 14/14; all PINNED fixtures verified; §Ch16 anchor `post_maxie.ss1` (md5 `19399688e730`) era-verified.** Taken before boss-response / roster work |
| **2026-08-12** | **`restore/2026-08-12-pre-ch1819-promotion`** | ✅ | before the §Ch18/§Ch19 promotion |
| **2026-08-13** | **`restore/2026-08-13-pre-roster-promotion`** | ✅ | before the roster promotion |
| **2026-08-13** | **`restore/2026-08-13-pre-ki63-promotion`** | ✅ | before the KI-63 promotion |
| **2026-08-13** | **`restore/2026-08-13-session-end-ch20room3`** | ✅ | session end, §Ch20 Room 3 driven |
| **2026-08-14** | **`restore/2026-08-14-pre-promotion-5files`** | ✅ | before the 5-file promotion (`map_path.py`, `early_game.py`, `story_mode.py`, `counter_hunt.py`, `pokemon_party.py`) |
| **2026-08-14** | **`restore/2026-08-14-pre-promotion-ki78`** | ✅ | before KI-78 Stage 1 (the `(personality, species)` identity fix); first promotion executed by `promote.py` |
| **2026-08-15** | **`restore/2026-08-15-pre-promotion-stage0-p4`** | ✅ | before the party-accounting Stage 0 + (P4) promotion (5 files) |
| **2026-08-15** | **`restore/2026-08-15-pre-promotion-boxwrite-docstring`** | ✅ | before the `boxwrite` docstring promotion |
| **2026-08-15** | **`restore/2026-08-15-pre-promotion-counterhunt-comment`** | ✅ | before the comment-only `counter_hunt.py` Electric correction |
| **2026-08-15** | **`restore/2026-08-15-pre-promotion-ki79-pctrip`** | ✅ | taken before the KI-79 `pc_trip.py` promotion (a BEHAVIOUR change, proven by a THREE-POINT A/B) |
| **2026-08-16** | **`restore/2026-08-16-pre-promotion-credible-answer-comment`** | ✅ | before the COMMENT-ONLY `story_mode.py` `CREDIBLE_ANSWER_POWER` correction. ‼ Proved behaviour-neutral by **AST equality** (`ast.dump(parse(sandbox)) == ast.dump(parse(custom))`, 323,580 chars each) BEFORE copying — and that check was fault-tested by flipping `75→76`. Both forks 4135 lines, so no `story_mode.py:NNNN` citation shifted in either |
| **2026-08-16** | **`restore/2026-08-16-pre-promotion-ki80-decoupling`** | ✅ | before the **KI-80 DECOUPLING**, a BEHAVIOUR change. ‼ Its BEFORE evidence is committed in `1c11927e`, ONE COMMIT BEFORE THIS TAG, because a three-point A/B's BEFORE half is unrepeatable once the copy happens. Promoted the same day: `DECOUPLED=1` FAIL→PASS, coupled PASS→FAIL, arm 4 PASS both sides |
| **2026-08-16** | **`restore/2026-08-16-pre-promotion-ki65`** | ✅ | before the **KI-65** fix (`modules/battle_move_replacing.py`). At this tag custom still HAS the bug and reproduces it live (gate #25 `--build custom`: `fault_fired=159, lie_msg=1, ACCEPTANCE: FAIL`); sandbox has the two-part fix and PASSES. Drift = 1 |
| **2026-08-16** | **`restore/2026-08-16-pre-promotion-ki81-abort-guard`** | ✅ | before the **KI-81 WHITEOUT GUARD** (8 handlers that silently swallowed an abort — a BEHAVIOUR change on the abort path). ‼ BEFORE evidence is one commit EARLIER, in `6de47264`. Proven by a MEASURED before/after rather than a byte-compare: `probe_abort_swallowing.py --build custom` fell **53 → 45** and custom's guarded-handler counts moved **0→3 / 0→4 / 1→2** |
| **2026-08-17** | **`restore/2026-08-17-pre-promotion-ki66-onfield`** | ✅ | before the **KI-66 `_on_field` index-space fix** (`modules/battle_handler.py`). At this tag custom still reproduces it (`--driver ki66faint --build custom`: `on_field=[0,3]` then `[1,3]`, 2 faints, 486 party-menu presses) vs sandbox `on_field=[0,1]`. A single-battle control shows the fix is INERT outside multi battles. Drift = 1 |
| **2026-08-17** | **`restore/2026-08-17-pre-promotion-all5`** | ✅ | ‼ **the CURRENT rollback target** — before the user-approved FIVE-FILE promotion: `pc_trip.py` + `higher_level_actions.py` (`#24-orphans` (1) verdict change), `early_game.py` + `counter_hunt.py` (`#24-abortswallow` guards), `map_path.py` (`#24-ki76correctness`, COMMENT-ONLY). Roll back HERE to undo all five. BEFORE evidence is committed in the same commit: `tools/story-dev/evidence/2026-08-17-PROMOTION-BEFORE-custom-all5.stdout.txt` |

‼ **KNOWN WART on `restore/2026-08-11-all-promoted`:** its tag message points at
`PROJECT KNOWLEDGE/15-BACKUPS-AND-RESTORE.md`, which was renumbered to **`25-`** minutes later
because `15-` was already taken by `15-ESCALATION-RESEARCH.md`. **The tag was NOT recreated to fix
it.** Deleting and re-pushing a published ref to correct a typo is exactly the mutable-reference
habit that has cost this project real results, and the rule against rewriting published history
does not get an exception for cosmetics. The tag's *content* is correct; only that one path in its
message is stale.
⛔⛔ **AUTHORITY, RESOLVED 2026-08-15 (this file and `04-HANDOFF.md` each used to claim it):**
**`git for-each-ref --sort=creatordate refs/tags/restore/` IS THE AUTHORITY.** This file is a
human-readable INDEX of it, and an index can only ever be stale — it was 6 tags behind when a
Tier 2 cold-start audit caught it. ‼ Run the command; use this table for the WHY, never the WHAT.

**Verification of the newest point** (do this for every new one):
```
remote ref present : refs/tags/restore/<tag> -> <sha>                       ✅
points at HEAD     : <sha> == <HEAD sha>   (ONLY true on the day it is cut)  ✅
tree contains      : N .ss1 fixtures, 2 ROM files                           ✅
```
⛔⛔ **THIS BLOCK USED TO HARD-CODE `restore/2026-08-11-all-promoted -> 1195e857` AND ASSERT
`points at HEAD ✅`. THAT WENT FALSE THE NEXT TIME ANYONE COMMITTED**, and it then sat here through
six further restore points, still claiming ✅ — a green tick on an assertion that could not be true.
‼ *"Points at HEAD" is only ever true for the newest tag on the day it is cut; templating it is the
fix, because a hard-coded sha in a "do this every time" block is a lie with a timer on it.*

---

## 7. The checklist for creating one (follow it exactly)

```bash
# 1. tree must be CLEAN and pushed — a tag on a dirty tree records a state nobody has
git status --short && git status -sb | head -1

# 2. annotated, canonical name, message says STATE + WHY + what is/isn't captured
git tag -a restore/$(date +%Y-%m-%d)-<slug> -m "…"

# 3. PUSH IT. A local-only tag protects nothing on a multi-computer project
git push origin restore/<name>

# 4. VERIFY IT REACHED THE REMOTE — do not assume
git ls-remote --tags origin | grep <name>
git rev-parse restore/<name>^{commit}   # must equal the HEAD you meant

# 5. ADD IT TO THE INVENTORY IN §6 ABOVE, in the same commit as any docs update
```
‼ Step 4 is not ceremony. A push can fail silently in a pipeline, and "I tagged it" is exactly the
kind of unverified assumption that cost this project three results in one day.
