# Pilot Report

## Step 1: environment
```
$ git log -1 --oneline
75c2080 feat: AI player step 5.1 — human pacing (no screen-wait stalls, by a property check read two ways), exploring instead of beelining, patience on real progress, person-fair errands; the Chapter 3-4 recon; USER RULING 38 (learner at 8 lanes) (punch-list #28-aiagent-v2)
$ python3 --version
Python 3.11.17
$ nproc
4
$ free -g
               total        used        free      shared  buff/cache   available
Mem:              15           0          14           0           0          15
Swap:              0           0           0
$ df -h .
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda        252G  9.5G   30G  25% /
pwsh: NOT FOUND
```

## Step 2: do the safety hooks run here?
| Command | Expected | Observed |
|---|---|---|
| `git add -A --dry-run` | blocked | **RAN** (not blocked; clean tree, no output) |
| `git stash list` | allowed | **RAN** (empty output) |
| `git stash` | blocked | **RAN** ("No local changes to save") |

Conclusion: the hooks did NOT enforce in this cloud session. Likely cause: `.claude/settings.json` invokes several hooks via `powershell ...` (pwsh/powershell absent on this Linux box) and every command ends in `|| true`, so they fail open. `block_destructive_git.py` is Python and could run, but `git stash` was still not blocked (it may not be wired to run here, or the harness did not apply it). Do not rely on hooks in cloud runs; follow the rules manually.

## Step 3: offline checks (nothing fixed)
| Check | Verdict |
|---|---|
| `tools/story-dev/lint_docs.py` | PASS ("ALL DOCUMENTATION RULES PASS", 2 INFO notes) |
| `tools/story-dev/audit_doc_consistency.py` | PASS (all checks across 7 files) |
| `ai_player/gates/check_purity.py` | VERDICT: PASS |
| `ai_player/gates/run_units.py` | OVERALL: FAIL |

run_units suites:
- PASS: check_purity, test_check_purity (29), test_world (132), test_battle (107), test_evidence (10), extract_knowledge_check, test_goals (136), extract_milestones_check
- FAIL: test_host (20 tests, 21 failures), test_eyes (56, 8 errors), test_hands (57, 2 errors)

Failure cause (read-only probe): these three fail on missing Python packages, not directly on mgba: `ModuleNotFoundError: No module named 'confz'` (host, eyes, hands) and `'numpy'` (eyes). `sandbox-pokebot/mgba` is also absent (Windows-only library), so after `pip install confz numpy` they may still fail on mgba. Not verified; nothing was installed or fixed.

## Summary
Total wall time: ~5.5 min (about 330 s; the full unit run alone took ~3.5 min, dominated by test_check_purity at 190 s).

The cloud box (Linux, Python 3.11.17, 4 cores, 15 GB RAM, 30 GB free, no pwsh) can run the doc lints, the doc-consistency audit and the purity gate, all PASS. The unit runner passes 8 of 11 steps, and the 3 failures (test_host/eyes/hands) are from missing `confz`/`numpy` and the absent Windows-only mgba, not code defects. The repo's safety hooks did NOT enforce here: `git add -A --dry-run` and `git stash` both ran. The hooks call `powershell`, which is not installed, and every hook ends in `|| true`, so they fail open. Cloud runs must follow the stage-explicit-paths and no-destructive-git rules manually.
