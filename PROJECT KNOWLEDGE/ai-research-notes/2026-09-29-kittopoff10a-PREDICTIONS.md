# 2026-09-29 — USER RULING 26, design v2 step 10a (HK at Rustboro: the healing kit rides step 9a's heal errand): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code commit and before any live arm. Branch `wt/kittopoff` (from `main` `61c6759e`, whose top commit
> is the spec `ai-research-notes/2026-09-29-kittopoff-SPEC.md`).
> ⚠ **Not blind for the gate:** the new gate `probe_kit_topoff.py` was run three times before this file was committed,
> ALL PASS each time:
> - its coverage mutants M15-M20 were added after run 1;
> - an adversarial mutant pass then found 32 plausible mutants neither gate caught, and two code defects. Rows E9-E18,
>   K15-K19, W3-W5 and A2-A3 were added, with every mutant set written BEFORE run 3
>   (`tools/story-dev/evidence/2026-09-29-kittopoff10a-ADVERSARIAL.txt`);
> - the step-9 gates were re-proven against the edits.
>
> The Arm 8 gate bullets are therefore known outcomes. **Every LIVE arm below is blind.**
> Step 10 is split, as step 9 was: **10a** (this file) is consumer (a) at Rustboro; **10b** (the Sootopolis visit and
> the earlybasket driver's kit grade) follows with its own predictions.

The arms run the PRODUCTION mode (`--driver storyresume`), which writes no harness readings (no `R[...]` keys).
Like step 9a's, they are graded from PRODUCTION telemetry in the debug log: the `[BALLS-BUY]`/`[KIT-BUY]` lines
and the tracked lines. Each arm therefore names the exact line that grades it, and the headings name the arms,
not `P<n>` (`probe_predictions_gradeable.py`'s key convention names harness readings, and there are none here).

## WHAT IS BUILT (uncommitted at filing)

- `modules/story/stock_topoff.py`:
  - PURE `kit_wants` (spec D3-D4) and `visit_plan` (D5-D6: one budget; balls to the reserve + 1, the kit, the rest of
    the balls, bought as one line set);
  - `parse_kit_flag` (D1), `kit_log_line` (`[KIT-BUY]`, D8), `_kit_held` (the reserve view, D4; fault
    `POKEBOT_R26_FAULT_RAWBAG`), `_kit_skip_reason` (the key-item coupling, D2), `_static_kit_sold` (Rustboro: Potion,
    Super Potion);
  - `ball_topoff_errand(…, kit_mode)`: the kit branch, with separate memo keys (D9). With the kit OFF, skipped or in
    `observe`, every ball decision is step 9a's.
  - `_walk_buy_return(…, kit_lines, kit_reason)`: one `buy_in_shop` call, verified per item name (D7). It buys the
    lines the live list sells and VERIFIES against the planned ones, so a set the live list drops is a shortfall of
    that set, never a silent ok (the adversarial pass's second defect).
  - A planning failure logs a `[BALLS-BUY]` line only when the balls are on, and a `[KIT-BUY] kit-failed` line when
    the kit is (the pass's first defect: a kit-only planning failure logged a ball line and no kit line).
  - Neither fix is reachable in the live arms: Rustboro's live list is its static list, and no arm raises in planning.
- `modules/modes/util/higher_level_actions.py` (UPSTREAM-derived): the kit flag parsed before the first yield next to
  the ball flag; the guard widened to either flag; `kit_mode=` passed on.
- Gates:
  - NEW `probe_kit_topoff.py`, appended to `run_gates.py`;
  - the 9a gate's A2 row and the anchors of M2, M9, M10, M12 and M15 updated, with their red sets UNCHANGED (re-proven);
  - the 9b and RULING 18 gates pass unchanged.
- Registry rows: `POKEBOT_R26_KITTOPOFF`, `POKEBOT_R26_FAULT_RAWBAG`.

## THE ARMS

- **Common to every arm:** `saves/r20_badge1_party1_gym.ss1` (PINNED 50af0f5c), the seed-1 wrapper,
  `--driver storyresume --set-balls 5 --frames 60000`, sequential, profile repro-ml: 9a's command.
- **At the first Rustboro heal:** spare 7, ₽9,940, stage MID, floor ₽1,000, budget ₽4,470.
- **Items pocket: no healing items.** `heal_stock=-` on the first battle after the heal
  (`evidence/2026-09-29-t1trainer-T1.txt:62`).
- **Baselines:** 9a's raw debug logs `M0-5-r1` and `B-ON` (in the scratch `…/Temp/p2b/bb/logs/`, recorded by 9a).
- **Tracked lines:** `[MAP]`, `[BATTLE] started|ended`, WHITEOUT, `[KEYBATTLE]`, `[CATCH]`, `[DEXFENCE]`, `[DEXCATCH]`
  (9a's grader).
- ⚠ **`POKEBOT_R27_KEYITEMS=1` adds a `[KEYBATTLE]` line to every trainer battle,** so an arm with it compares with
  K-KEY, the matched control, not with 9a.

### Arm 1: K-OFF (no flags): the kit's code changes nothing when OFF
- Tracked lines identical to 9a's M0-5-r1, whole run (52 of 52).
- No `[BALLS-BUY]` and no `[KIT-BUY]` line.
- **FALSIFIER:** any tracked-line difference.

### Arm 2: K-BALL (`POKEBOT_R23_BALLRESTOCK=1`): 9a's ball top-off is unchanged
- Tracked lines identical to 9a's B-ON, whole run.
- Exactly one line, byte-identical to B-ON's apart from the frame stamp:
  `[BALLS-BUY] why=topoff mart=11,7 ball=Poké Ball bought=22 premier=2 spare=7->31 money=9940->5540 exit=16,39 back=16,39 facing=Down reason=top off 22 x Poké Ball (spare 7 <= trigger 20; budget 4470)`
- No `[KIT-BUY]` line.
- **FALSIFIER:** any difference.

### Arm 3: K-OBS (balls `1`, `POKEBOT_R26_KITTOPOFF=observe`, no key items): observe buys exactly 9a's balls
- Tracked lines identical to 9a's B-ON, whole run, with the same `[BALLS-BUY] why=topoff … bought=22 premier=2 …` line.
- Exactly one
  `[KIT-BUY] why=kit-observe mart=RustboroCity kit=[('Super Potion', 4)] bought=- money=9940->9940 wants=[('Super Potion', 4)] reason=kit [('Super Potion', 4)] and 8 x Poké Ball (4 to the reserve + 4 after the kit); budget 4470, 70 left`.
- **FALSIFIER:** a different ball purchase, a Super Potion bought, or a missing or different kit line.

### Arm 4: K-SKIP (balls `1`, kit `1`, NO key items): the coupling holds, loudly
- Tracked lines and the ball line identical to 9a's B-ON.
- Exactly one
  `[KIT-BUY] why=kit-skip mart=RustboroCity kit=- bought=- money=9940->9940 wants=- reason=POKEBOT_R27_KEYITEMS is not 1: ordinary trainers would drain the kit (spec D2)`.
- **FALSIFIER:** a Super Potion bought, or no skip line.

### Arm 5: K-KEY (balls `1`, `POKEBOT_R27_KEYITEMS=1`, kit unset): the matched control for Arms 6 and 7
- The same `[BALLS-BUY] why=topoff … bought=22 premier=2 spare=7->31 money=9940->5540 …` line as B-ON.
- `[KEYBATTLE]` lines at trainer battles.
- No `[KIT-BUY]` line.
- Frames are not predicted beyond this. The rival after the heal is a key battle, and no healing item is held, so the
  fight should match B-ON's, but that is only an expectation.

### Arm 6: K-ON (balls `1`, kit `1`, key items `1`): one visit, one budget, the split order
- Tracked lines identical to K-KEY up to the errand.
- Then exactly these two lines (frame stamps not predicted):
  - `[BALLS-BUY] why=topoff mart=11,7 ball=Poké Ball bought=8 premier=0 spare=7->15 money=9940->5540 exit=16,39 back=16,39 facing=Down reason=kit [('Super Potion', 4)] and 8 x Poké Ball (4 to the reserve + 4 after the kit); budget 4470, 70 left`
  - `[KIT-BUY] why=kit mart=11,7 kit=[('Super Potion', 4)] bought={'Super Potion': 4} money=9940->5540 exit=16,39 back=16,39 facing=Down reason=kit [('Super Potion', 4)] and 8 x Poké Ball (4 to the reserve + 4 after the kit); budget 4470, 70 left`
- ⚠ **The money equals B-ON's (₽5,540); only the ITEMS differ:** Poké +8, Premier +0, Super Potion +4, against B-ON's
  +22, +2, +0.
- The rival fight that follows may now use Super Potions. The trajectory after the purchase is not predicted.
- **FALSIFIER:**
  - B-ON's 22 balls;
  - no Super Potions;
  - a Premier;
  - a different money figure;
  - a `topoff-failed` or `kit-failed` line.

### Arm 7: K-ONLY (kit `1`, key items `1`, balls unset): a kit-only walk
- Tracked lines identical to K-KEY up to the errand.
- No `[BALLS-BUY]` line.
- Exactly one
  `[KIT-BUY] why=kit mart=11,7 kit=[('Super Potion', 4)] bought={'Super Potion': 4} money=9940->7140 exit=16,39 back=16,39 facing=Down reason=kit [('Super Potion', 4)] and 0 x Poké Ball (0 to the reserve + 0 after the kit); budget 4470, 1670 left`.
- **FALSIFIER:** a ball bought, a different money figure, or no walk.

### Arm 8: the gates (NOT blind: see the header)
- `probe_kit_topoff.py` ALL PASS, every mutant red on exactly its written set.
- `probe_stock_topoff.py` (9a, anchors updated), `probe_stock_topoff_sootopolis.py` (9b) and `probe_league_reserve.py`
  (R18) pass.
- The full suite passes.
- An adversarial mutant pass (the step 9b 08 prevention rule) ran before the gate was trusted. Of its 41 mutants, the
  kit gate caught 2, the 9a gate 6 more, and NEITHER caught 32. Each of the 32 now has a row and a mutant, with its
  set written before run 3. The six the 9a gate alone caught now redden this gate too. Run 3: ALL PASS, every set
  exact on its first run (`evidence/2026-09-29-kittopoff10a-ADVERSARIAL.txt`, `…-GATE.txt`).
- ⚠ A second adversarial pass on the EXPANDED gate has not run. The three-lens review is the next adversary.

## WHAT THIS DOES NOT SHOW

- The Sootopolis kit lines (10b).
- Whether the kit wins the rival fight or key battles (step 14).
- A kit before gym 1 (the named gap).
- A Mart selling a status cure: Rustboro sells none, so the status line is proven only by gate rows K4 and K5.
