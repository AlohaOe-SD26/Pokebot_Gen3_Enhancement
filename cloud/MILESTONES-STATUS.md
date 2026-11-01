# MILESTONES-CH5-CH8 status (cloud job; the truth, updated after every step)

Branch: claude/milestones-ch5-ch8-o0janq. Decomp: pret/pokeemerald@731ad5bfd6e6f265508d0efcca0ba42f9dcf5881 (git clone --depth 1 https://github.com/pret/pokeemerald /tmp/pokeemerald). Wall time so far: 11 min (session clock).

## Done
- Steps 1-4: all four chapters drafted (20 milestones: ch5 x8, ch6 x3, ch7 x5, ch8 x4), 16 trainers, 7 looks; generator run: 0 problems; in-memory Story load test passes for BOY and GIRL.
- Step 5: cloud/MILESTONES-REPORT.md written (per-chapter sources, hints, levels, not found, uncertain, SHA, wall time).

## In progress
- nothing

## Next
- NOTHING: the job is complete. For the owner: review the DRAFT, then decide whether to wire it into milestones.json via ai_player/gates/extract_milestones.py (not done here: new files only).

## How a later session resumes
1. git fetch origin claude/milestones-ch5-ch8-o0janq; check it out; read this file and `ai_player/knowledge/seasoned/milestones_ch5_ch8_DRAFT.json` (it is complete up to the last step listed under Done).
2. Re-clone the decomp (command above) and check `git -C /tmp/pokeemerald rev-parse HEAD` against the SHA; a different SHA means re-verify every cited line.
3. Do the step under "Next" only: add that chapter's milestones (same schema as milestones.json: id, chapter, title, done{flags,variables,trainers}, waypoint, optional, maps, steps, hint, fight, note, taught_by, decomp), commit and push, then update this file.
4. Rules: new files only (the DRAFT json, this status file, cloud/MILESTONES-REPORT.md); never edit milestones.json or any .py; stage explicit paths; no push to main.
