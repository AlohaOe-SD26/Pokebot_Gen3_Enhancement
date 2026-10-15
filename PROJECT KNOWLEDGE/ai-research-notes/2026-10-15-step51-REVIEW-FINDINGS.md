# Step 5.1 findings handed to step 5.2 (verbatim from the step-5.1 workflow, 2026-10-15)

## The final verifier (tree d3d34871df0ac077): all_pass True

### WEAK PROOFS
- LIVE ARMS ARE REPLAYS, now proven by a log diff (the builder only said 'most likely'). I compared each final arm's actions.jsonl with the matching d0c949e run, by (frame, decision, action):
- CH1T, CH1C and CH1M are identical, record for record (5636, 4937 and 7342 records).
- CH2 and CH2T match in every frame and action. CH2 differs only in one record's log label, at f227895. CH2T differs only in the balance number it prints: on d0c949e it read 'under the Story's 40%'.
- Only CH2M diverged (7199 vs 7228 records).
- The final arms do differ from a883634's runs (first difference at record 203-224).
So only the 801-820 sweep shows the final changes (G137, G138, the balance raise) in play. The live CH2T pass at 40.2% is the same trajectory as on the failed tree d0c949e.
- THE CH2 FLOOR IS PARTLY THE AI'S OWN TARGET. `GoalManager.owed()` (goals.py:652-672) computes errand frames over goal frames, nearly the quantity MIX_MIN grades, and overrides the dice when it is low. CH2T's log: 'draw 0.93, but 40% of this session's 46782 goal frames went to errands, under the Story's 45%: a break from the story'. The margin over the floor comes partly from a quota the AI aims at. What separates it from the beeline is graded elsewhere:
- CH2_OFF is under the floor in 19 of 20 runs (my recount: max 0.3005, seed 814).
- The curiosity the story did not need: 0.194-0.524 in the AI, 0.0 in the CH1 control.
- Chapter-2 time without the grass's battles: 1.403, the AI slower in 20 of 20 seeds.
The builder disclosed this.
- THE PACING MEASURE HAS TWO LIMITS:
- From the raw logs I can PROVE a wait of 150 frames at most (lower bound) in all 160 real runs.
- The original STALL1 and STALL2 stalls are hidden inside one 'busy 600f' record. Only an upper bound sees them: 619-644 and 1285-1372 frames, in exactly the 16 of 20 and 9 of 20 runs the AI's record flags.
- Outside the intro and battle openings, the long unobserved stretches in real runs match a text still printing (at most 6 frames per character). The upper bound itself is noisy: in clean runs it reaches 463, and every unobserved stretch it cannot attribute to printing falls in the intro or a battle opening.
- Live launcher arms have only the AI's own WaitWatch record. The game's second path runs only in the sweep (disclosed).
- CHAPTERS 3-4 HAVE NEVER BEEN PLAYED. These are unit-tested only:
- the optional gym trainers and ROXANNE by her badge alone (G74);
- the story-goal cooldown (G78);
- patience during a long training stint before an L18 fight (sweep A/B only before an L5 rival: PATIENCE 7/7 reached, PATIENCE_OLD 7/7 stopped);
- the RUSTBORO gym door (metatile 0x1CD, checked against pret's metatile_labels.h, never seen live).
- MAX_LOSSES 3 has been reached only in the LOSE3 copy: an altered decider, 5 of 6 runs. No unaltered run has reached it. Each live arm is one trajectory on the host clock.
- IN CHAPTER 1 THE FLOOR DOES NOT SEPARATE THE ARMS:
- The beeline control's errand share is 0.342-0.711, inside the floor. Chapter 1 rests on curiosity: 7.1-18.2 % vs 0.0 in 20 of 20.
- Path divergence barely differs: 0.445 vs 0.417 for the control. The goal-sequence divergence differs: 0.544 vs 0.376.
- 'The beeline 0.0' holds only for CH1. CH2_OFF keeps item pick-ups: up to 11.4 % unneeded curiosity in my recount, and 16 pick_up goals in all.
- SMALL RECOUNT DIFFERENCE. My no-speedrun ratio for CH1 outside the needs is 1.127 (slower in 16 of 20); the reported figure is 1.135 (16 of 20). The two methods clip the need spans differently. Without the battles my recount matches exactly: 1.141 (19 of 20), and CH2 1.403 (20 of 20).

## The adversarial review

**Step 5.1 adversarial check: six findings, most severe first**

**1. HIGH: it loafs, and every metric pays for it.** In CH1M at OLDALE, three errands in a row went nowhere:
- `explore` (forced by the time quota, "draw 0.91, but 9%… under the Catcher's 12%") ended "stuck: nothing new… for 3012 frames… 1 new tiles".
- "OLDALE_TOWN some more" ended "nothing new… for 3001 frames… none".
- `detour` ended "budget: 1500 frames ran out".

Across those three, "people in the way" went from 8 to 61. About 1,160 presses moved it 377 steps, all aimed at frontiers (-7, 10) and (-7, 15) past the blocked west exit. That is roughly 7,500 frames of walking into a blocker.

CH2M did the same in PETALBURG: two "some more" explores at "48%… under the Catcher's 50%", 8,400 frames, tiles 8025 → 8026 → 8026, re-triggering 'Hiya! Are you maybe… A rookie TRAINER?'.

Causes:
- The "some more" look-round (`goals.py:907-915`) never checks that anything is left to see.
- An explore whose budget ran out counts as done (`1381-1383`).
- `intent_mix` counts curiosity frames by goal kind, not by what the goal produced (`rate_step5.py:638`).

*Fix:* only look round again where `world.promise > 0` and a target is reachable. Keep person-blocked targets across goals (like `carried_scene_walls`). Count a curiosity goal's frames only when it yields something: new tiles, an item, a catch, words, a talk. Pre-register that yield check with an arm that loafs on purpose and must FAIL.

**2. HIGH: errands are filled by a quota, not interleaved.** When the time quota (`owed`) is short, the dice are skipped (`845, 888, 923, 1132`). After CH1M drifted to Catcher ("1%… under the Catcher's 12%"), it ran six curiosity goals in a row. In CH2T the PETALBURG look-round and the last chat were quota-forced (the catch by the first-balls rule). The quota (45-50 %) is set just above the grader's floor (`MIX_MIN` 30 %), so the floor now measures the AI's own target. *Fix:* let the shortfall raise the draw odds smoothly instead of bypassing them, cap curiosity goals in a row, and grade how errands are spaced and what they yield, not the share.

**3. MED: detours are cosmetic, and two pairs of runs picked the same place.** `goals.py:1775` prints "looked at the … at T" even when T was never reached:
- CH1C and CH1M both: "budget… ran out; looked at the frontier at (-7, 15)".
- CH2 and CH2M both: "stuck: nothing left to try on ROUTE102… looked at the grass at (18, 11)", a tile CH2M's own log calls "cannot be reached that way".

Nothing happens on arrival, not even a talk with the "people" it chose. In the sweep, 19 of 103 run rows with detours total 15-42 frames, under the 6-tile minimum walk. *Fix:* report "reached" or "not reached", and give a detour that was not reached no ok and no curiosity frames. Filter out frontiers past a map edge and tiles that cannot be reached. Talk to the chosen person. Grade the share of detours that arrive.

**4. MED: the beeline A/Bs cannot fail.** Turning errands off (`AI_PLAYER_FAULT_NO_ERRANDS`) removes the curiosity kinds in code (`624, 658, 880, 899, 918`). So "beeline 0.0 in 20 of 20" and "control 0" for the seed check are true by construction. *Fix:* the control that can actually fail is a loafing arm (see 1).

**5. LOW-MED: the stall check cannot see pushing against a blocker.** The 7,500-frame push in finding 1 passed "THE STALL PROPERTY 150". *Fix:* add a check for the longest free overworld stretch with presses but no new tile, measured both ways, with a blocked-frontier fault arm.

**6. LOW:**
- **A known town called "a new place".** CH1M said "a new place, OLDALE_TOWN" after healing there twice, because `known_before` is frozen at session start.
- **The `ask` step heads straight to the answer's house.** It still walks to the step's own house with "nothing was said" (CH1M did it twice).

**Clean:**
- **No screen-wait stall left.** The longest was AI 150, game 180, across 213 runs.
- **No hang.** Every new loop has a bound.
- **No new person-unfair read.** The gym is recognised by its door's look.

Files:
- `C:/Remote Projects/Pokebot_Gen3_Enhancement/ai_player/brain/goals.py`
- `C:/Remote Projects/Pokebot_Gen3_Enhancement/ai_player/gates/rate_step5.py`
- `C:/Remote Projects/Pokebot_Gen3_Enhancement/sandbox-pokebot/profiles/ai-step5-play/ai_player_runs/20261015-055241-CH1M/ai_player.log`
- `C:/Remote Projects/Pokebot_Gen3_Enhancement/sandbox-pokebot/profiles/ai-step5-play/ai_player_runs/20261015-061450-CH2M/ai_player.log`

## The full regression's open item

- `provenance.evidence_digests` reads only the first 12 lines of an evidence file, while `prune_evidence.digest_of` searches the first 4000 characters. Two step-0 files (G, M6) whose command is a multi-line `-c` script put their `code:` line on line 32, so the two checkers disagree. They were moved to `archive/no-digest/` for the 5.1 commit. Fix: one shared reader, with a test on a multi-line-command file.