# MILESTONES-CH5-CH8 status (cloud job; the truth, updated after every step)

Branch: claude/milestones-ch5-ch8-o0janq. Decomp: pret/pokeemerald@731ad5bfd6e6f265508d0efcca0ba42f9dcf5881 (git clone --depth 1 https://github.com/pret/pokeemerald /tmp/pokeemerald). Wall time so far: 8 min (session clock).

## Done
- Step 1 (chapter 5): 8 milestones (ch5_stolen_goods, ch5_goods_employee [optional], ch5_rusturf_grunt, ch5_return_goods, ch5_devon_corp, ch5_pokenav_tutorial, ch5_rival_meet, ch5_rival_battle [optional]).
- Step 2 (chapter 6): 3 milestones (ch6_briney_house, ch6_dewford, ch6_old_rod [optional]).
- Step 3 (chapter 7): 5 milestones (ch7_steven, ch7_flash [optional], ch7_gym_trainers [optional], ch7_brawly, ch7_exp_share [optional]); looks added: steven, mr_stone, brawly.

## In progress
- nothing

## Next
- Step 4: chapter 8 (ch8_sail_slateport, ch8_dock, ch8_stern, ch8_scott), then Step 5: cloud/MILESTONES-REPORT.md.

## How a later session resumes
1. git fetch origin claude/milestones-ch5-ch8-o0janq; check it out; read this file and `ai_player/knowledge/seasoned/milestones_ch5_ch8_DRAFT.json` (it is complete up to the last step listed under Done).
2. Re-clone the decomp (command above) and check `git -C /tmp/pokeemerald rev-parse HEAD` against the SHA; a different SHA means re-verify every cited line.
3. Do the step under "Next" only: add that chapter's milestones (same schema as milestones.json: id, chapter, title, done{flags,variables,trainers}, waypoint, optional, maps, steps, hint, fight, note, taught_by, decomp), commit and push, then update this file.
4. Rules: new files only (the DRAFT json, this status file, cloud/MILESTONES-REPORT.md); never edit milestones.json or any .py; stage explicit paths; no push to main.
