# Evidence of earlier trees (kept, unchanged)

`ai_player/evidence/` holds, at its top level, the evidence of the CURRENT working tree only: every file there names the
tree's digest in its `code:` line, and `py -3.12 ai_player/gates/provenance.py --check-evidence` fails otherwise. The
step-3.1 verifier's second round (2026-10-08) found older files beside the current ones ("a literal reading of 'every
evidence file' would not hold"). They were MOVED here, byte for byte, file names unchanged, into one folder per digest
their code line names. Nothing was deleted or rewritten. A document that cites `evidence/<name>` for one of these files
finds it under `evidence/archive/<digest>/<name>`.

| folder | what it holds | files |
|---|---|---|
| `no-digest/` | runs before `gates/provenance.py` existed (their code line says only "HEAD ...; UNCOMMITTED changes"): build steps 0, 0.1, 1, 1.1 and 2 of 2026-10-07 (`step0-*`, `step01-*`, `step1-*`, `step1-at-step2*`, `step11-*`, `step2-*`, `step2-repro-XBC`, `step2-seed9-*`, `step21-WARPY`), the verifiers' re-runs of those days (`verify-*`, `verify21-*`, `verify3-step1/2-*` of 2026-10-07), and the intermediate seed-9 run of step 2.1 (`2026-10-08-step2-seed9-*`) | 327 |
| `2652e886e7844ce4/` | the step-3 verifier's re-run on the tree of the step-3 verifier's second round (`2026-10-08-verify3-*`) | 49 |
| `b4c70735d1599fa2/` | the step-3.1 verifier's re-run on the step-3.1 tree (`2026-10-08-verify31-*`) | 35 |
| `2b316cce90537f5e/` | the step-3.1 verifier's second re-run, on the tree of the step-3.1 verifier's round (`2026-10-08-verify31b-*`, `2026-10-08-step3-RATEverify31b.txt`) | 61 |

Files of the same NAME as a current one (`2026-10-08-step2-REVERT.txt`, `step11-REVERT`, `step2-seed9-at-step3-*`, every
`step01/1/2/3-*`) were not moved: each round's re-run rewrote them, and their earlier versions are in git history.

BUILD STEP 4 (2026-10-08): the final runs of build step 3.2 (its tree `sha256:3ea1b655920e8c61`, the tree the README's
"Step 3.2" section quotes) were never committed, so the step-4 re-runs would have overwritten the only copy. They were
MOVED, byte for byte, before the step-4 final runs:

| folder | what it holds | files |
|---|---|---|
| `3ea1b655920e8c61/` | build step 3.2's final runs: `step01-*` (4), `step1-*` (21), `step11-REVERT`, `step2-*` (18), `step2-seed9-at-step3-*` (16), `step3-*` (36) | 96 |

THE STEP-4 VERIFIER'S ROUND (2026-10-08): build step 4's final runs (its tree `sha256:83a4581da76e0739`, the tree the
step-4 verifier checked) were never committed either. They were MOVED, byte for byte, before this round's final runs:

| folder | what it holds | files |
|---|---|---|
| `83a4581da76e0739/` | build step 4's final runs: `step01-*` (4), `step1-*` (21), `step11-REVERT`, `step2-*` (18, with `step2-RATE` and `step2-REVERT`), `step2-seed9-at-step3-*` (16), `step3-*` (35), `step4-*` (13) | 108 |

‼ TWO FILES OF THAT TREE ARE LOST: `2026-10-08-step3-REVERT.txt` and `2026-10-08-step4-REVERT.txt`. This round's
development runs of `revert_step3.py` (a subset, W0, W70, W76-W78) and `revert_step4.py` (all 41) wrote over them BEFORE
the folder was archived (`revert_step3.py` writes its evidence file even for a subset). Their results are quoted in the
README's build-step-4 and step-3.2 sections ("30 of 30 CAUGHT"; "73 mutants caught and W13 redundant alone, of 74") and in
the step-4 verifier's report ("The revert evidence lists W62-W75 as CAUGHT"); the files themselves are gone.

THE STEP-4 VERIFIER'S SECOND ROUND (2026-10-09): the final runs of the step-4 verifier's round (its tree
`sha256:a14d81a107a65b76`, the tree the step-4 verifier's re-run checked, never committed) were MOVED, byte for byte, BEFORE
any run of this round (the hazard above is closed: `revert_step3.py` now writes a SUBSET's file beside the system's
temporary files, never into `evidence/`):

| folder | what it holds | files |
|---|---|---|
| `a14d81a107a65b76/` | the step-4 verifier's round's final runs: `step01-*` (4), `step1-*` (21), `step11-REVERT`, `step2-*` (19, with `step2-RATE` and `step2-REVERT`) and `step2-seed9-at-step3-*` (16), `step3-*` (36), `step4-*` (17) | 114 |

This round's own development passes (`*-step3dev-*`, `*-step3dev2-*`, `*-step3dev3-*`, `*-step3-RATEdev*`) were moved out
of the evidence folder before its graded runs: they are not evidence. So were the files of one interrupted final chain on
the tree `sha256:60308f3c190d6254` (its `revert_step3.py` failed on a mutant anchor the round's own grader edit had moved,
W50; fixed, and every suite run again on the final tree): not evidence either.

The final tree's folder also holds two HELD-OUT replications (`*-step3-RATE-SEEDS101-110.txt`, `*-step4-RATE-SEEDS101.txt`:
seeds no development run played, graded by the same pre-registered bounds). They are replications, not gates, and BOTH
SAY FAIL; the README's "Everything on ONE tree" of the step-4 verifier's second round says which predictions did not
replicate and why.
