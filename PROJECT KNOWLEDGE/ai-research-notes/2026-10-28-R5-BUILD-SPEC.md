> ✅ **BUILT 2026-10-29** (`07`; decisions `06` 2026-10-29). VERBATIM below this box: the spec the orchestrating session wrote for the build workflow (session scratch `s53/r5/R5-BUILD-SPEC.md`, sha256 `b5662366bc02131d`). Where the build departs from it, the CODE and `06` win: D4 and U1 CONTROL were AMENDED (the decision's pause and a second look before every "done": one free look is not a free screen), D6 was REWRITTEN (the settle never lets the frame budget cut a reached target), D5's `settled` is now `played_out` with `passed`, and a D9 was added (a MAX_LOSSES-th loss inside the settle ends it). The build, the sweep, the review and the fix round: `2026-10-28-R5-BUILD-REPORT.md`.

# R5: A FREE SCREEN BEFORE "DONE" (build spec, 2026-10-28)

> Status: SPEC, written by the orchestrating session for the build workflow. Backlog item R5
> (`ai-research-notes/2026-10-18-improvement-backlog.md:325-326`; top-15 item 15's first half; `04` queue item 4).
> Its recon (three angles, read-only, 2026-10-28) is in the session scratch `s53/r5recon/` and will be committed as
> `ai-research-notes/2026-10-28-R5-recon-{code,record,game}.md`: 01-code-map.md (OUR code), 02-record.md (what the
> project already decided), 03-game-facts.md (the pinned decomp). Read their section 0 first; cite them by section.

## 1. What and why

- The play loop ends a run "done" at `ai_player/mode.py:457-458` on the pass's look (`:433`), BEFORE it plays what is on
  screen (`:475`). No frame passes between, and `_play_end` (`:647`) presses nothing. So a run can end with a text box,
  a fade, a battle or a menu up whenever the target's proof flipped before the screen freed (01-code-map §0, §3).
- Today's NATURAL routes mostly end free: `ch1_pokedex` and `ch2_wally` set their proof a few commands before
  `releaseall` (03-game-facts §2), and `ch4_roxanne`'s badge flips before TM39's text but is fought inside a `talk` goal
  that plays out to free (`2026-10-15-ch34-recon/08-verify-gaps.md:24`, re-read on today's code, 01-code-map §3.4).
- The RESIDUAL routes to "done" mid-screen (01-code-map §3.3): `play_out` giving up (`mode.py:476-481`); `talk_to`'s
  `"talked; then {stop}"`; `Navigator.run` checking `intent.done` before `nav_free` (`navigator.py:1253-1255`);
  `handle` returning right after a battle or a map change. And intermediate milestones flip mid-scene: `ch1_clock`
  (`FLAG_SET_WALL_CLOCK` before MOM's upstairs text), `ch1_birch`, `ch1_starter`, `ch2_dad` (03-game-facts §6).
- R5 makes "done" wait for a free screen (the precondition R1's save needs: a save is possible only on a free screen),
  and records whether every end's screen was free (a guard, never evidence: RC/08:263).

## 2. Decisions (the orchestrator's technical calls; they go to `06` with the build)

- **D1. R5 alone, not inside R6's screen ladder.** R5 writes no persisted file, so it fixes no DECIDE-EARLY shape; a free
  screen is the ladder's END condition, and R6 can later give `play_out`/`handle` a default for unknown screens.
  Rejected: building R6 first or with it (R6 is not in the top 15; its `screen_wishlist.jsonl` would be a user-data
  file ahead of DP1 + DP2).
- **D2. The shape: a settle block BEFORE the done check, the done check's two lines byte-identical.** Mutant G226 anchors
  on the exact text of `mode.py:457-458` (`revert_step5.py:1010-1015`; a missing anchor raises at `:1536-1537`), and 36
  mutants anchor on `mode.py` text. Sketch (the builder owns the details):
  ```python
              if (milestone is None or index > target) and not nav_free(look):
                  # (R5) ... the target's proof can flip with a box still up: play the screen out first
                  stop = yield from play_out(hands, nav, f"{options.target} reached: what is on screen first")
                  ...record the settle (below)...
              if milestone is None or index > target:
                  return self._play_end(hands, story, manager, runner, report, "done", f"{options.target} reached")
  ```
  Rejected: moving the done check below `:475` (01-code-map §11 shape ii): it reorders G226's and G228's anchors and
  lets patience end a reached target "stuck".
- **D3. When the screen will not free within `play_out`'s bound** (`SCENE_ROUNDS` = 12 `handle` calls), the run STILL
  ends `done: <target> reached`: the game's proof holds, `live_step5.py:350` compares that exact string, and the honesty
  rule says a proof under a stop reason is a lie (`live_step5.py:354-359`). The unsettled end is SAID instead (PL-3): a
  `hands.tell` line, a `hands.note("end_screen", ...)` and the report field of D5. Rejected: ending "stuck" (contradicts
  the honesty rule); retrying past the bound (PL-4).
- **D4. Press, never idle (PL-1).** The settle is `play_out` (it presses through waiting text via `handle`/`advance`).
  No new `busy`/`idle` wait.
- **D5. Every end records its screen.** `_play_end` adds `report["end_screen"]` from a fresh `hands.look()` (a read; no
  frame passes): free or not (`nav_free`), what holds it (`busy_reason`) and the frame; for a "done" end also whether
  the settle ran, its frames and its stop. It goes into the `end` note too. No new COUNTED grader check (it would change
  step 5.3's graded check set); `live_step5.py`/`rate_step5.py` may PRINT it.
- **D6. The frame budget:** settle frames count against `settings.frames` (`mode.py:806-813`). Accepted: a budget end
  during a settle reads `stopped: not finished within N frames`, reported, not hidden.
- **D7. R5's second call site** (before a goal switch after a milestone) already holds: the loop plays out a non-free
  screen at `:475` before `next_goal` (`:494`). No change; a CONTROL asserts it.
- **D8. R5's third call site** (before a save) is R1's: R5 adds no save.
- ⛔ Never change the BOT's default behaviour; nothing under `sandbox-pokebot/`, `custom-pokebot/`, `40cakes repo/`.

## 3. Unit tests (`ai_player/gates/test_goals.py`, PlayLoopTests; a FAULT and a CONTROL for every guard)

Use the existing seams (`run_loop` with a screen function and a patched `play_out`, `test_goals.py:838-900`; the text-box
look `:1006-1007`; `ch1_through("ch2_oldale")` for a look past `ch1_pokedex`, `:3708`).
- U1 FAULT: target reached on a look with a text box up: `play_out` IS called before the end, the end look is free, the
  reason is EXACTLY `done: <target> reached`, `end_screen.free` True, `settled` True.
- U1 CONTROL: target reached on a free look: "done" at once, `play_out` NOT called, NO frame passes (the pad's frames
  equal), the same exact reason, `end_screen.free` True, `settled` False.
- U2 FAULT: `play_out` returns a stop with the screen still up: the reason is STILL exactly `done: <target> reached`
  (never "stuck"), the tell line and the `end_screen` note say not free and carry the stop.
- U3 CONTROL: target NOT reached with a box up: the old path (`:475`): `play_out`, then the loop goes on (no end).
- U4: every existing done/stuck test stays green; U5: a "stuck" end records `end_screen` too.
- Purity (`gates/check_purity.py`) and fairness (`gates/check_fairness.py`) stay green: the new code reads the screen
  (`nav_free`, `busy_reason`) and the already-computed `milestone`/`index`, never `.marks` (no new door).
- PF-2: each new call gets a CALL-DELETING revert mutant in `revert_step5.py` (the settle; the `end_screen` record), each
  CAUGHT by its FAULT arm; the call census (`gates/call_census.py`) covers the new sites or a reasoned waiver is added.
  Re-anchor any mutant whose anchor text moved, and show it still mutates the same thing.

## 4. The live proof (PF-12: a unit-tested rule is not a chapter proof)

- **Compute the discriminator FIRST (CLAUDE.md Tier 2 (4)).** Candidate fixture: `AI_PLAYER_TARGET=ch1_clock` from a
  REAL New Game (`ch1_clock` is a required milestone, `milestones.json:383`, proof `SET_WALL_CLOCK` 81). It is
  UNVERIFIED whether the clock path already plays out to free before the loop reads the mark. Measure it on the
  PRE-R5 code (`HEAD` before the build) on 1-2 development seeds: does the run end "done" with the screen NOT free
  (MOM's text)? Read "free" with a HARNESS-side, game-side test that does not reuse the AI's `nav_free` (PF-19;
  03-game-facts §4: `callback2 == CB2_Overworld`, the script lock clear, the message box shut, held over >1 frame).
  - If YES: that is a natural A/B. If NO (vacuous): try `ch2_dad`, `ch1_birch`, `ch1_starter` the same way; if all are
    vacuous, PLANT the residual route in the HARNESS only (never in the AI's code): the first `play_out`/`talk_to`
    return after the target's mark flips is cut short while the box is up, and the plant must be shown to REACH that
    state (PF-4: a reach floor, graded only on runs that reached it).
- **The A/B:** arm OLD = R5 reverted (the settle-deleting mutant, applied the way `revert_step5.py` applies mutants, in a
  temp tree), arm NEW = R5. The same fixture, the same seeds, the host clock pinned (`04`: the game reads the HOST
  CLOCK). Discriminator: the harness's game-side free test at the end. Expected: OLD ends `done` NOT free on every seed
  that reached the state; NEW ends `done` free. And the NEW arm's reason is the exact string.
- **Seeds:** at least 3 HELD-OUT seeds never played by any arm or sweep (check the seed ledger; write the range in the
  ledger BEFORE playing; `ai_player/README.md` explains it). Development seeds are separate and listed.
- **PF-17 CONTROL:** the normal chapter-1 end (`ch1_pokedex`, no plant) on 1 held-out seed: "done" free, the settle did
  not run (`settled` False).

## 5. Regression and the rules while it runs

- Before the commit: `tools/workflows/regression_due.py`, and every DUE revert driver under about 20 minutes (`08`
  2026-10-23). After the build is final: the full lane `py -3.12 ai_player/gates/run_regression.py --full --evidence`
  (72-100 min, detached, run by the orchestrator; first check none is running). While it runs: NO edit under
  `ai_player/`, `06`, `07`, `08`, `CLAUDE.md` (a change mid-run FAILS it, `08` 2026-10-28).
- ⛔ No `git add -A`, no destructive git, no commit by the workflow: the orchestrator commits.

## 6. Docs (the orchestrator writes them; listed for completeness)

`ai_player/README.md` (the play loop's end), `ai_player/LESSONS.md` only if a lesson is added (with its gate), `04`
queue item 4, the backlog's line 18 and R5's entry, `06` (D1-D8), `07`, `08` if a bug or a dead end, and the recon
notes into `ai-research-notes/`.

## 7. Out of scope

R1 + R2 (the save, CONTINUE, the memory file), R6 (unknown screens), promoting the end-screen record to a counted grader
check, chapter 3-4 play.
