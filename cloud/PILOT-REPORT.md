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
