# P11-x: the detour after the dark crossing - diagnosis (P11-2 builder, 2026-11-11)

> A NOTE, not a source of truth (`00-READ-THIS-FIRST.md`): on any contradiction the authoritative docs win. P11-2's
> first builder wrote this diagnosis on 2026-11-11 (its run book: 19:07) from P11-1's kept records, read-only
> (`s53/p11r2/P11X-DIAGNOSIS.md`);
> its third builder appended the correction at the end on 2026-11-12; P11-2's closing pass filed it here unchanged on
> 2026-11-12. THE VERIFIER RE-READ IT (`s53/p11r2/result/verify_report_section.md`, "P11-x, re-read"): its own flag reader,
> checked against two controls (the save's map, and the STEVEN flag against the harness's marks: both OK in 17 of 17
> states), reads FLAG_ITEM_GRANITE_CAVE_1F_ESCAPE_ROPE as 0 at the three ROUTE 106 starts and the three G1F starts and 1 at
> the three B1F starts; the B1F starts' world memories list 1F's ball at "17,7"; the arms pass AI_PLAYER_WORLD and no
> AI_PLAYER_MEMORY; the builder's offline repro reproduces on the P11-2 code; the errand ran in exactly ab2-B-C2,
> ab2-B-C3, ab2-F-C2, ab3-B-C1 and ab3-B-C2. One of the verifier's predictions MISSED AS WORDED: two FAULT runs
> (ab3-F-C2, ab3-F-C3) were on ROUTE 106 BEFORE their crossing; anchored, as the diagnosis anchors it, on the crossing's
> arrival at 1F (35, 3), only the 5 errand runs leave the cave afterwards, and THE DIAGNOSIS STANDS. WHAT FOLLOWS: the test
> kit must save and restore the AI's GOAL memory together with a start (not the world memory alone); the three B1F starts
> must be re-made (the start maker's run folders are gone); and P11-1's "FIX reached STEVEN sooner in only 3 of 6" is
> CONFOUNDED by the test starts (the three pairs where FIX was later are the three where only FIX ran the stale errand), so
> it is no evidence about the way-through fact either way. Development records only: one trajectory per seed, never a rate.

Read-only, from P11-1's kept records (`s53/p11r1/out/ab2`, `ab3`: #115, #116), its start files (`s53/p11r1/starts_p11`),
and the code at `f1069d9d` (worktree `ch6-p11`). Nothing was run live for this. Development records: one trajectory per
seed, never a rate.

## Verdict

**The errand for an item ball that is gone is an artifact of the live A/B's START, not a defect of the AI's code.** The
B1F starts restored the AI's WORLD memory (which still lists the ball at GRANITE CAVE 1F (17, 7)) but not its GOAL memory
(where the AI records that it picked the ball up). In the AI's own continuous play, and across a save and continue, both
memories travel together and the errand does not arise. **The walk out of the cave is a consequence of that errand**: it
takes the AI over 1F's one-way ledges to the entrance side, from which STEVEN's room is reachable only back through the
dark, and the goal-less look-around there prefers ROUTE 106 and DEWFORD.

So there is **no AI-code fix in P11-2** (the lead's condition "a clear defect with a small fix" is met only by a TEST-KIT
fix, which changes no AI code and is for the next live round: see "What to do"). One design question goes back to the
lead (new stop P11-x2, below).

## Evidence

1. **The ball was gone before every B1F run began (the GAME's record).** `p11r2/read_flags.py` reads the event flags
   straight from the save states (checked first against the harness's own GAME marks: FLAG_DELIVERED_STEVEN_LETTER reads
   0 at every start and 1 at the ends of `ab3-B-C1-6450` and `ab3-F-C1-6450`, as their `marks_before` / `marks_after`
   say). `FLAG_ITEM_GRANITE_CAVE_1F_ESCAPE_ROPE` (0x41A, the ball at 1F (17, 7), `data/maps/GraniteCave_1F/map.json`) is
   **0 at all three G1F starts and 1 at all three B1F starts**: the start maker's own play (the AI, `make_starts_p11.py`)
   picked it up on its way from 1F's mouth to the ladder (17, 11). It is also 1 at the kept end state of #116 C1
   (`ab3-B-C1-6450`), the run whose record says "not picked up: no item ball where it lay at (17, 7) any more" (V6).
2. **The start's world memory still lists it.** In each `B1F_C*_world.jsonl` (the world memory the A/B runs restored),
   map `24:7` (1F) has `items {"17,7": <frame>}` (seen at f768974 / f653385 / f845788, before the B1F arrival). The world
   memory never drops a ball once seen (`world/memory.py` `see_objects` only adds to `MapMemory.items`); what stops the
   AI going back for a ball it took is the goal memory's `tried_items` (`brain/goals.py` `_remembered_ball` skips every
   `"map|x,y"` in it; `pursue` adds the key when it picks a ball up).
3. **The runs began with a NEW goal memory.** The arms run `gates/play_harness.run` with `world_in` (that world file)
   and no memory file (`memory_options(None, False)` gives the brain no `memory_file`), so `tried_items` was empty. The
   start maker saved only the emulator state and the world file (its run folder, with everything else, was deleted).
   A real save and continue restores `tried_items` (`game_memory.py` GOAL_KEEP: "the item balls it tried and is done
   with").
4. **Reproduced offline on the real start memory and the real code** (`p11r2/p11x_repro.py`, read-only):
   `GoalManager._remembered_ball` on 1F at (35, 3), the arrival after the crossing, returns **(17, 7)** with a new goal
   memory and **None** with `tried_items = {"24:7|17,7"}`, for B1F_C1, C2 and C3 alike ("REPRODUCED").
5. **In continuous play it does not happen.** The six lit-control runs of #117 played on from ROUTE 106 through 1F and
   the dark to STEVEN with one memory throughout: each picked the ESCAPE ROPE up at (17, 7) with a `pick_up` goal ("an
   item ball on the ground at (17, 7)") and none of them went back for it after the crossing (`grep "back over to it"`:
   0 in 6). (Supporting, not proof: the counterfactual needs a run whose decision on 1F falls where the errand did.)
6. **The errand explains every detour, and nothing else does** (`p11r2/p11x_table.py`, `p11x_goal_at_1f.py`; frames
   from each run's first record):

   | Run | First on 1F (35,3) | Stale errand | Out to ROUTE 106 | STEVEN's room | Crossings |
   |---|---|---|---|---|---|
   | ab2-B-C1 | +20,008 | none | none | +22,946 | 1 |
   | ab2-B-C2 | +32,341 | +33,866 | +34,882 | +58,052 | 2 |
   | ab2-B-C3 | +23,224 | +28,581 | +34,550 | +97,778 | 2 |
   | ab2-F-C1 | +61,196 | none | none | +63,029 | 1 |
   | ab2-F-C2 | +63,067 | +68,637 | +72,123 | +181,203 | 2 |
   | ab2-F-C3 | +77,233 | none | none | +77,965 | 1 |
   | ab3-B-C1 | +21,264 | +21,760 | +27,723 | +86,781 | 2 |
   | ab3-B-C2 | +34,280 | +35,547 | +41,246 | +115,243 | 2 |
   | ab3-B-C3 | +30,325 | none | none | +37,548 | 1 |
   | ab3-F-C1 | +49,640 | none | none | +53,298 | 1 |
   | ab3-F-C2 | +81,724 | none | none | +83,656 | 1 |
   | ab3-F-C3 | +147,065 | none | none | +149,592 | 1 |

   - Every errand (5 of 5) ended "no item ball where it lay at (17, 7) any more", and every errand run then walked out to
     ROUTE 106 and crossed the dark a second time. No run without the errand left the cave after the crossing: those
     reached STEVEN's room 732 to 7,223 frames after first standing on 1F.
   - The errand came at the first new goal decision on 1F (+496 to +5,570 frames after arriving): a `look_around` (the go
     goal put aside after failing twice in the dark) or a `go` whose budget ran out on 1F was in force. In the seven runs
     without it, the `go` goal was in force and the next goal was the `talk` to STEVEN. FIX 4 of 6 and FAULT 1 of 6 is how
     often a new decision fell on 1F before STEVEN was in view; why it fell more often in FIX is a frequency question.
   - **P11-1's caveat "FIX reached STEVEN sooner in only 3 of 6" rests on this artifact**: the three pairs where FIX was
     later (ab2 C3, ab3 C1, ab3 C2) are exactly the three where only FIX had the stale errand. What FIX would have done
     with a consistent memory is not measured (a counterfactual; FIX reached lit 1F first in 6 of 6).
7. **Why the walk then leaves the cave.** `p11r2/draw_1f.py` (the extractor's own walk on 1F): from the north arrival
   (35, 3) the walk reaches both 1F's north part (STEVEN's door (5, 10)) and its entrance side, down the one-way ledges at
   (13, 10-12), (14, 9) and (15, 9-12); from the item ball's side (17, 8) it reaches the mouth (37, 12) and the ladder
   (17, 11) but neither (35, 3) nor STEVEN's door. In `ab3-B-C1-6450` the errand walked from (9, 5) to (17, 8), over a
   ledge; at (18, 7) the go goal ("by looking around: not told yet": no goal map) chose "the back at (37, 11) ... it leads
   back to ROUTE106, where 6 thing(s) are left to see (score -18.4)", then DEWFORD ("4 thing(s) are left to see") and its
   houses: the explorer's ordinary choice on a map seen all of, with no knowledge that STEVEN's room lies through the dark.

## What to do

- **Kit (no AI code; for the next live round that starts mid-chapter).** A start file must carry the AI's WHOLE memory:
  have the start makers run with a memory file (`play_harness.run(..., memory=...)`) and save it beside the world file,
  and have the arms pass it (`--memory`), or at least seed the goal memory's `tried_items`. Then re-measure the frames to
  STEVEN's room on consistent starts. P11-2's own live check stops at the first frame on 1F, before the errand, so it
  does not depend on this.
- **New stop P11-x2 (a design question for the lead, not a defect):** should an errand that crosses a one-way ledge away
  from the story's way be weighed (or should a seasoned player's "STEVEN is at the back of this cave" reach the lit 1F)?
  With a consistent memory it arises only when the AI really left a ball behind beyond a one-way ledge; today such an
  errand strands it on the entrance side and the goal-less look-around leaves the cave.
- **Minor, not the cause:** the world memory never forgets a ball it saw; a person standing where the ball lay, and seeing
  none, would. Here the ball's tile was 18 tiles off screen when the errand was chosen, so it does not apply.

## Files (all in `s53/p11r2/`)

`read_flags.py` (the flag reader), `p11x_repro.py` (the offline reproduction), `p11x_table.py` + `p11x_table.out`,
`p11x_goal_at_1f.py` + `p11x_goal_at_1f.out`, `draw_1f.py`.

## Correction (appended 2026-11-12 by P11-2's third builder; nothing above is rewritten)

Evidence item 7 cites `draw_1f.out` for "neither (35, 3) nor STEVEN's door". That probe asked about **(5, 11), which is a
WALL** (collision 1, MB_NORMAL), not a tile beside the door, so its two "False" lines about the door prove nothing. The
second builder re-asked it on 2026-11-12 at 08:57 (`draw_1f_check.py` -> `draw_1f_check.out`, the same walk rules), this
time about floor tiles a player stands on: (5, 9) above STEVEN's door (5, 10) and (6, 10) east of it (both collision 0,
MB_CAVE, elevation 3). From (35, 4), the tile below the north ladder (35, 3) where the AI arrives, the walk reaches 201
tiles, including (5, 9), (6, 10), the ball's side (17, 8), the south ladder's (17, 12) and the mouth's (37, 11). From the
ball's side (17, 8) it reaches 83 tiles, including (17, 12) and (37, 11), but NOT (5, 9), (6, 10) or (35, 4). **Item 7's
sentence stands, and `draw_1f_check.out` is now its proof.** The verdict and the rest of the evidence are unchanged.
