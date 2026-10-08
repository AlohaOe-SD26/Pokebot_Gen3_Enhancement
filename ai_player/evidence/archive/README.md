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
