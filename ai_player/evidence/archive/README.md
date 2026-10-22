# Evidence of earlier trees: the archive policy

`ai_player/evidence/` holds, at its top level, the evidence of the CURRENT working tree only: every file there names the
tree in its `code:` line, and `py -3.12 ai_player/gates/provenance.py --check-evidence` fails otherwise.

> **Since 2026-10-21 (`#28-evidence-identity`): a tree is identified by the CODE UNDER TEST, not by its digest alone.**
> The digest describes only the diff from a commit, so a clean tree's digest is the same at every commit. A file's
> identity is now (its label, its label's committed files at its HEAD, its digest), and a NEW archive folder is named
> `<digest>-<HEAD>` (`provenance.archive_key`), so two clean trees of different commits never share one. The folders
> below named by a bare digest were written before that and keep their names. Where the text below says "tree digest",
> read "tree identity" for any file archived from 2026-10-21 on.

## The policy (step 4.1, 2026-10-09: the step-4 review's item 9, "the archive is 54 MB")

* **This folder keeps only the files of earlier trees that are CITED BY NAME** by a document (`PROJECT KNOWLEDGE/**/*.md`,
  `ai_player/README.md`, `ai-agent/**/*.md`, the docstrings of `ai_player/gates/*.py`) or by a commit message. They sit in
  one folder per tree digest (the digest their `code:` line names), byte for byte, file names unchanged. A document that
  cites `evidence/<name>` for one of these finds it under `evidence/archive/<digest>/<name>`.
* **Every other file of an earlier tree is listed in `INDEX.md`**, one line each (its path, the size and sha256 OF THE BLOB
  git holds, the `git show` command that prints it, its first line), and is **deleted from the working tree**. Git keeps
  it: the commit named on its line holds it. (Step 4.1 round 2, the verifier: the size and sha256 were the Windows working
  copies', CRLF, so 25 of 29 sampled lines matched their own `git show` only after converting LF to CRLF; recomputed from
  the blobs by `prune_evidence.py --reindex`: 884 lines, 778 rewritten, every one now equal to what its `git show` prints.) Folder-level mentions ("everything on the tree X, archived in `archive/X/`") do not count as a citation of
  each file in the folder: they now point at the INDEX and git.
* **Applied by a tool, never by hand**: `py -3.12 ai_player/gates/prune_evidence.py` (a dry run), `--apply`; before a
  round's final runs rewrite the top level, `--retire <the previous tree's digest> --apply` moves that tree's CITED
  top-level files here and indexes the rest. The tool deletes a file only when git TRACKS it and it is UNCHANGED against
  HEAD (otherwise the file is kept and said), so nothing exists only in the working tree when it goes.
* **(Step 4.1 round 3) A tree git does not hold** (a working tree never committed: no `git show` can bring its files back):
  its CITED files stay here as files, and every UNCITED file is **packed** into one `uncited.zip` in its tree's folder
  (deflated; every member checked byte for byte against its file before the file is deleted), with one `INDEX.md` line
  each (its path, size and sha256, the pack that holds it, its first line). Nothing is lost and only what a document or a
  commit cites stays readable as a file. (The step-4.1 verifier's second round: "the archive is back to 9.8 MB ... The 115
  files (8.2 MB) of the never-committed tree 8b742931d35fa205 are kept wholesale, against the 'cited by name only'
  policy".) A file is CITED when its FULL name (or its name without `.txt`) appears in a citing document: a short form
  such as `step4-RATE.txt` names no one tree, so it does not keep a file out of the pack.
* **(Step 4.1 round 3) The order can no longer lose a file**: every evidence writer of the gates calls
  `provenance.keep_earlier(path)` just before it writes; a top-level file already there whose code line names ANOTHER tree is
  moved to `archive/<its digest>/` first (a taken name gets a `.N` suffix; an identical copy is not kept twice), so a graded
  run started before `--retire` archives what it would have written over instead of destroying it (the step-4.1 verifier:
  "`--retire` ran after round 2's graded chains had started, so 12 top-level evidence files ... were overwritten. They are
  unrecoverable"). `--retire` is still run first; the guard is what makes a slip harmless. (`gates/test_evidence.py`
  KeepEarlierTests, with the fault half: without the keep, the earlier bytes are gone.) The `code:` line may carry a tag
  (`[VERIFY] code: ...`, as `verify_knowledge.py` prints it): the tool reads it (round 2 moved two such files by hand).
* Development passes are not evidence: they never stay at the top level (each round removes them before its graded runs).

Applied for the first time on 2026-10-09 (HEAD `7a70a445`): 790 archive files (54 MB) and the 117 top-level files of the
tree `sha256:7b4322c9ac0df2e1` (the step-4 verifier's second round) were reviewed; 23 are cited and kept (18 in the archive,
5 moved here from the top level: 1.2 MB), 884 are indexed in `INDEX.md` (772 archive files, 112 top-level files) and
deleted. The folder is now 1.5 MB with its index.

## What is kept, by folder

| folder | the tree | kept (cited) |
|---|---|---|
| `no-digest/` | runs before `gates/provenance.py` existed (build steps 0 to 2, 2026-10-07) | `2026-10-07-step2-REVERT.txt`, `2026-10-07-step2-repro-XBC.txt`, `2026-10-07-step21-WARPY.txt` |
| `3ea1b655920e8c61/` | build step 3.2's final runs (2026-10-08) | `2026-10-08-step11-REVERT.txt`, `2026-10-08-step3-RATE.txt`, `2026-10-08-step3-REVERT.txt` |
| `83a4581da76e0739/` | build step 4's final runs (2026-10-08) | `2026-10-08-step11-REVERT.txt`, `2026-10-08-step3-RATE.txt`, `2026-10-08-step4-KNOWLEDGE.txt`, `2026-10-08-step4-RATE.txt`, `2026-10-08-step4-UNITS.txt` |
| `a14d81a107a65b76/` | the step-4 verifier's round (2026-10-08) | `2026-10-08-step11-REVERT.txt`, `2026-10-08-step3-RATE.txt`, `2026-10-08-step3-REVERT.txt`, `2026-10-08-step4-KNOWLEDGE.txt`, `2026-10-08-step4-RATE.txt`, `2026-10-08-step4-REVERT.txt`, `2026-10-08-step4-UNITS.txt` |
| `7b4322c9ac0df2e1/` | the step-4 verifier's second round (2026-10-09), retired before step 4.1's final runs | `2026-10-09-step3-RATE.txt`, `2026-10-09-step3-RATE-SEEDS101-110.txt`, `2026-10-09-step4-RATE.txt`, `2026-10-09-step4-RATE-SEEDS101.txt`, `2026-10-09-step4-UNITS.txt` |
| `8b742931d35fa205/` | step 4.1's final runs (2026-10-09), the tree the step-4.1 verifier FAILED; retired during step 4.1 round 2's graded runs | 5 cited files (`2026-10-09-step3-RATE.txt`, `2026-10-09-step3-RATE-SEEDS101-110.txt`, `2026-10-09-step4-RATE.txt`, `2026-10-09-step4-RATE-SEEDS101.txt`, `2026-10-09-step4-UNITS.txt`); the other 110 (7.9 MB; that tree was NEVER COMMITTED) PACKED in its `uncited.zip` (1.0 MB) in round 3, one INDEX line each. Its two held-out replications both say FAIL: the README's "Step 4.1" says which bounds were refuted |
| `d272da770b442dc4/` | step 4.1 round 2's final runs (2026-10-09), the tree the step-4.1 verifier's second round FAILED (held-out seeds 301-310 and the foe's base stats); retired by `--retire` BEFORE round 3's runs wrote anything at the top level | 4 cited files (`2026-10-09-step1-E1.txt`, `2026-10-09-step3-RATE.txt`, `2026-10-09-step4-RATE.txt`, `2026-10-09-step4-UNITS.txt`); the other 128 (9.8 MB, never committed) PACKED in its `uncited.zip` (1.2 MB), one INDEX line each (the README's round-2 section cites many of them by short names: they are in the pack) |
| `ce43362fc87b102e/` | step 4.1 round 3's FIRST graded pass (2026-10-09), stopped by its held-out failure (`rate_step4.py`'s grader bug, seed 422); archived file by file by `provenance.keep_earlier` as the next pass wrote over them | the cited files by name, among them `2026-10-09-step4-RATE-SEEDS401.txt` (the FAIL, 34 of 35); the other 32 PACKED in its `uncited.zip` |
| `6044f57f1cfdcb92/` | step 4.1 round 3's SECOND graded pass (2026-10-09), stopped by `rate_step3.py`'s held-out failure (the WALK A/B's 0.03 tolerance, seeds 401-410); archived the same way | the cited files by name, among them `2026-10-09-step3-RATE-SEEDS401-410.txt` (the FAIL) and `2026-10-09-step4-RATE-SEEDS501.txt` (rate_step4's held-out PASS, first played here); the other 61 PACKED in its `uncited.zip` |

The `7b4322c9ac0df2e1/` folder holds the two HELD-OUT replications of that round (`*-step3-RATE-SEEDS101-110.txt`,
`*-step4-RATE-SEEDS101.txt`: seeds no development run played, graded by the same pre-registered bounds). They are
replications, not gates, and BOTH SAY FAIL; the AI player's README, "Step 4, the verifier's second round", says which
predictions did not replicate and why.

## History kept as it was said (before the policy)

* The step-3.1 verifier's second round (2026-10-08) MOVED older files beside the current ones into one folder per digest,
  byte for byte; the trees `2652e886e7844ce4` (`2026-10-08-verify3-*`), `b4c70735d1599fa2` (`2026-10-08-verify31-*`) and
  `2b316cce90537f5e` (`2026-10-08-verify31b-*`) were the verifiers' re-runs: none of their files is cited, all are now in
  `INDEX.md`.
* ‼ TWO FILES OF THE TREE `83a4581da76e0739` WERE LOST BEFORE ANY ARCHIVE: `2026-10-08-step3-REVERT.txt` and
  `2026-10-08-step4-REVERT.txt`, written over by development runs of `revert_step3.py` and `revert_step4.py` before that
  folder was archived; their results are quoted in the README's build-step-4 and step-3.2 sections. `revert_step3.py` now
  writes a SUBSET's file beside the system's temporary files, never into `evidence/`.
* Development passes of the step-4 verifier's second round (`*-step3dev-*`, `*-step3-RATEdev*`) and one interrupted final
  chain on the tree `sha256:60308f3c190d6254` were moved out of the evidence folder before that round's graded runs: not
  evidence.
* ‼ (step 4.1 round 2) THE TREE `8b742931d35fa205` WAS RETIRED LATE: `--retire` ran a few minutes after round 2's graded
  chains had begun, so 12 of its top-level files had already been written over by the new tree's runs (`step01-A`, `-A2`,
  `-B`, `-C`, `step1-E1` to `-E7` and `-E2X`; their HEAD copies of the tree before stay in git). Two more,
  `2026-10-09-step4-KNOWLEDGE.txt` and `-KNOWLEDGEX.txt`, were moved here BY HAND: their code line is prefixed
  `[VERIFY] code:`, which the tool's `^code:` pattern does not match (a gap in `prune_evidence.py`, said; FIXED in round 3:
  the tool reads a tagged code line, `test_evidence.py` CodeLineTests). Round 2's development passes (`*-step3dev41b-*`,
  `*-step4dev41b-*`) were moved out before its graded runs: not evidence. The 12 files written over are NOT recoverable
  (that tree was never committed); round 3 made the slip harmless for the future (`provenance.keep_earlier`, above).
* (step 4.1 round 3) Applied on 2026-10-09 (HEAD `7a70a445`) with `--retire d272da770b442dc4 --apply` before round 3
  wrote anything at the top level: 4 cited files moved, 238 uncited files of the two never-committed trees packed (128 of
  `d272da770b442dc4`, 110 of `8b742931d35fa205`, 17.7 MB as files, 2.1 MB packed); the archive went from 9.8 MB to 4.5 MB
  with the round-2 tree's 9.8 MB inside it.
* (step 4.1 round 3) Two graded passes of round 3 were each stopped by a held-out failure and written over by the next pass:
  `keep_earlier` moved every one of their files here as it was about to be written over (the guard working as built: no
  file of either tree was lost), and `prune_evidence.py --apply` then packed the 93 uncited ones; the archive is 5.9 MB with
  four never-committed trees in it. Round 3's development passes (`*-step4dev41c-*`) were moved out before its graded runs.
