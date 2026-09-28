# 2026-09-28 — `#27-r101standstill` RECON (a 4-agent workflow: logs, code, map, adversarial) — a NOTE, not truth

> Synthesis below, verbatim. The load-bearing tile claim was then VERIFIED in our own harness (see the PREDICTIONS file).

**NOTE, not truth: #27-r101standstill synthesis of 4 recon reports (logs, code, map, refute)**

**(1) Mechanism**

1. **The Surf hunt picks its ground while the player is inside Wally's house.** CONFIRMED by two angles.
   - logs: 185/185 standstill episodes start at `PETALBURG CITY(8,0)`.
   - code: P1 log 12816 shows `pos=(2, 4)`.
   - refute: the choice point was correlated across all logs.
2. **From that interior every candidate fails the static path check.** CONFIRMED by two angles: code and map both ran `calculate_path` offline, and all 6 HM03 grounds returned "not on connected maps (note that warps don't count.)" (`map_path.py:768-773`). The refute report lists the mechanism as inferred.
3. **So the fallback returns `grounds[0]` = ROUTE101 (9,9).** CONFIRMED.
   - I read `early_game.py:5112`: `chosen if chosen is not None else grounds[0]`.
   - The comment at `:5109-5110` says this branch "fires only when no candidate paths — an abnormal state no driver reproduces yet". That is false: it fires on every Surf hunt that starts indoors.
   - The flip to `grounds[0]` came in `dabb8148` on 2026-08-26, and Route 101 hunts first appear that same day. This is a date correlation only.
4. **(9,9) is `MB_NORMAL`, so it never rolls an encounter.** CONFIRMED by three angles.
   - The decomp gives `map.bin` metatile 0x1d2, behavior 0x0.
   - Our ROM reader gives `has_encounters=False`.
   - `metatile_behavior.c:11` `[MB_NORMAL] = TILE_FLAG_UNUSED`, and `wild_encounter.c:595` rolls only when that flag is set.
   - The row `training_areas.py:78` is commented `# tile used by travel_to_route103()`, which contradicts that file's own docstring at `:12`, "verified tall-grass tile".
   - Across 204 episodes there were 0 battles.
5. **The bot is spinning, not frozen.** ONE-ANGLE inference, supported by logs and refute and CONTESTED by map.
   - `scripts=[]`, `controllable=True`.
   - `held_buttons=[]` proves nothing, because `press_button` is a one-frame press (`libmgba.py:476,589`).
   - In 5 episodes the facing goes Up→Left while the position stays (9,9), e.g. `H3 …20260826-140759.log:17559→17574`.
   - The dump stack is blind: before `384f5c51` it stopped at `_run_with_frame_budget` (KI-107).
6. **The spin's own bail loses to the 18k global watchdog.** Mechanism CONFIRMED (I read the code); the ratio is ONE-ANGLE.
   - The watchdog signature has no facing field (`story_mode.py:4162-4168`), so turning counts as no progress.
   - `_watchdog_stop` increments `_wd["stuck"]` once per call (`early_game.py:218`) against `_STORY_SPIN_NO_PROGRESS_FRAMES = 2400` (`:170`).
   - `spin()` calls the stop condition only when `tile_transition_state` and `running_state` are both `NOT_MOVING` (`higher_level_actions.py:381-386`), which is once per completed turn.
   - The 40,000 `deadline` at `:5127` also counts calls, but it is not the competitor that matters; the 2,400 bail is.
   - Measured lower bound: across 185 episodes the bail never fired inside 18k frames, so each check takes more than 7.5 frames. The "~10 frames per turn" figure is inferred from the decomp's 8-frame `WalkInPlaceFast` and has not been measured.
7. **P4r1/P4r7 ("still at (10, 29)") is a DIFFERENT bug.** CONFIRMED by 4 angles.
   - With ≤1 ball the hunt calls `provision_poke_balls()`, whose default is `RUSTBORO_MART` (`:2654`).
   - On the way back it bounces off the north door of Petalburg Woods: `f2550175 → f2550331`.
   - It is then stranded on Route 104, and none of the 6 candidate warps is a Woods door.
   - The recovery prints "already Petalburg-side — travel skipped" (ONE-ANGLE, logs). It shares only the target selection with the standstill.

**(2) Where the reports disagree**

- **Is the spin running at all?**
  - Map §8: "facing … never changes. The spin loop may not be running at all."
  - Logs §B3 and refute §3: 5 runs change Up→Left, and the 3,000-frame dump interval is a multiple of the ~40-frame turn cycle.
  - To settle: log `facing_direction` and the pressed direction at every stop-condition call.
- **Frames per stop check.** Estimates are 9–10 (logs), about 10 (refute) and "~8+" (code). The only measurement is ">7.5". To settle: log the emulator frame at each call.
- **Why ROUTE101 is re-picked after the P4 derail.** Code says "ground check or fallback, not reproducible offline". Map's static check found no path from Route 104 (10,29) to R101 or Petalburg, which points to the fallback. To settle: log the result of each candidate in the ground check from (10,29).
- **The ROUTE111 (25,55) `MB_DEEP_SAND` row.** Only map flags it. Desert sand may carry `HAS_ENCOUNTERS`, so check `metatile_behavior.c` before treating it as a defect. The three ocean rows (115/118/119) are CONFIRMED by two angles (code and map).
- The 2026-08-26 fallback flip is date-correlated by 3 reports, which is still correlation, not an A/B.

**(3) Driver design (a correctness question): `--driver r101standstill`**

*Fixture:* `norman_done.ss1`, the only one any report names. `FIXTURES.md5:90`: "Badges 1-5 … PETALBURG_CITY (7,6) … RECEIVED_HM_SURF=1 … ITEMS pocket empty; party 28% HP, 3 fainted".

*Vacuity preconditions.* Print and assert all of these on load, or the arms do not differ:
- `hm_learner_slot(HM03) is None`. If someone can already learn Surf, the hunt is never entered.
- Poké Balls ≥2, using `--set-balls` (fixed in #27-setballs). Otherwise the Rustboro provisioning path from P4 confounds the run.
- The loaded map and position, because (7,6) is ambiguous in the fixture row.

*Arms* (each calls `ensure_hm_learner(HM03)`, `early_game.py:5048`):
- **A, indoor.** Walk into Wally's house (map (8,0)) by ordinary navigation. Predicts ROUTE101 (9,9), 0 battles, and `stuck` below 2400 when 18,000 frames have passed since arrival.
- **B, outdoor.** Same fixture, started on outdoor Petalburg. Predicts ROUTE103 (5,7), per map §6 and the post-derail retargets.
- **C, the tile removed.** Arm A with the R101 row rebound in-harness to (11,10) or (13,10). Predicts a battle well before 18k frames.

*Readings.* Rule 7: log the value the code acts on, not the candidate list.
1. Every ground candidate with its `_cp` result or exception text, then the final `(map_enum, tile)` bound at `:5112`, and whether `chosen is None`.
2. On entry to `_story_spin`: the actual position and the metatile behavior under the player.
3. At every stop-condition call inside `spin()`: the emulator frame, `facing_direction`, `_wd["stuck"]`, and `_stop`'s `frames`. Rebind `context.emulator.press_button` so the direction and frame of every press are logged. That press is the action.
4. The frame at which `stuck` reaches 2400. Bound the run at 30k frames after arrival, since the driver may not include the global watchdog.
5. The battle-start count and the hunt's exit reason.

*Discriminators:* the chosen ground (A vs B), and battles>0 (A vs C). State which verdict a claim rests on.

*Falsifiers:*
- Median Δframe per check ≤7.5: the "wrong units" claim is refuted.
- No presses, or facing constant across consecutive checks: the spin is not running (map's hypothesis), and some other generator is holding the bot.
- Any battle at (9,9): the tile claim is refuted.
- Arm B also picks ROUTE101: the indoor-fallback claim is refuted.
- Arm C gets 0 battles in 18k frames: something beyond the tile suppresses encounters (the Repel or script path, code §6c/d).
- Arm A ends somewhere other than (9,9): the arrival assumption is wrong.

*Optional:* a batch that includes `384f5c51` shows the real generator stack. It answers a frequency question, not this one.

**(4) Fix candidates and their risks**

- **F1: Change the R101 spin tile to (11,10), (12,11) or (13,10).** Known from static reading only; it needs the table's two-way reachability sweep and a live encounter check. Risk: Zigzagoon is only 10% of Route 101's slots (map §5), so the hunt stays slow.
- **F2: Choose the ground from the outdoor exit, or step outside first.** This removes the hidden fallback. Risk: it changes the default Surf ground to ROUTE103, where "never caught one" already appears 23 times after 190k–330k frames (refute §4), a separate slowness. It also needs warp-aware exit logic.
- **F3: Assert arrival after `_navigate_riding_out` (`:5120`).** Check that the position equals the tile and that the tile is encounter land, and fail loudly with the tile named. Cheap. Risk: none beyond turning silent wedges into named derails.
- **F4: A gate over every `TRAINING_GRASS` row.** Require a land-encounter behavior and not water, since `has_encounters` alone passes the ocean rows. It must catch (9,9) and the 3 ocean tiles, and must not fire on legitimate desert sand. Fault-test it.
- **F5: Count real emulator frames in `_watchdog_stop` and `_stop`.** Risk: `_story_spin` runs every story spin (a shared path), so a real-frame 2,400 (40 s) may bail during honest low-rate grass hunts and cause re-navigation churn. It needs an A/B on the ordinary grass case (rule 9). Alone it only changes which derail fires: the bail returns, and then `:5146` raises "never caught one".
- **F6 (separate item, P4): the provisioning and Woods routing.** Pass a nearer mart; whether Petalburg Mart sells Poké Balls is UNVERIFIED. Also fix the Woods-door bounce and the "Petalburg-side" misclassification of Route 104. Risk: the navigation code is shared.

Sources: `C:\Remote Projects\Pokebot_Gen3_Enhancement\sandbox-pokebot\modules\story\early_game.py` (170, 204-223, 2654, 5048, 5084-5146), `...\modules\story\training_areas.py:78`, `...\modules\modes\util\higher_level_actions.py:377-391`, `C:\Remote Projects\Pokebot_Gen3_Enhancement\tools\story-dev\saves\FIXTURES.md5:90`.