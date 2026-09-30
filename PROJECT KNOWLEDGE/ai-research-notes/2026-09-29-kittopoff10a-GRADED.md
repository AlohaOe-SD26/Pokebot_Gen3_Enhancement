# 2026-09-29 — USER RULING 26, design v2 step 10a (HK at Rustboro) GRADED: with the kit ON, the post-badge-1 Rustboro heal buys 8 Poké Balls AND 4 Super Potions on 9a's budget, in one walk; every other arm is exactly 9a's

> Predictions: `2026-09-29-kittopoff10a-PREDICTIONS.md` (`bdd07a4d`), committed BEFORE the code commit `b06cbc09`
> and before any live arm. ⚠ Arm 8 (the gates) was not blind, and the predictions say so. Every LIVE arm (1-7) ran
> on the committed code after the predictions.
>
> Evidence (frames are debug-log frames):
> - `tools/story-dev/evidence/2026-09-29-kittopoff10a-K-*.txt`: one file per arm, with its flags, its
>   `[BALLS-BUY]`/`[KIT-BUY]` lines, the rival's lines and its tracked lines;
> - `-GRADER.txt`: the grader's output (20/20). The grader was fault-tested first: 9a's M0 graded as K-BALL and 9a's
>   B-ON graded as K-OBS both FAIL, for the right reason;
> - `-ADVERSARIAL.txt` and `-GATE.txt`: the adversarial mutant pass and gate run 3.

## RESULTS — every prediction held (each bullet re-read against its own words)

| Arm | Flags | Reading | Verdict |
|---|---|---|---|
| **K-OFF** | none | 52 of 52 tracked lines identical to 9a's M0-5-r1, whole run; no `[BALLS-BUY]`, no `[KIT-BUY]` | ✅ OFF changes nothing |
| **K-BALL** | balls `1` | 48 of 48 identical to 9a's B-ON, whole run; the one ball line byte-identical to B-ON's (`f178239 … bought=22 premier=2 spare=7->31 money=9940->5540 …`); no kit line | ✅ 9a unchanged |
| **K-OBS** | balls `1`, kit `observe` | 48/48 identical to B-ON; B-ON's ball line; `f176384 [KIT-BUY] why=kit-observe mart=RustboroCity kit=[('Super Potion', 4)] bought=- money=9940->9940 wants=[('Super Potion', 4)] reason=kit [('Super Potion', 4)] and 8 x Poké Ball (4 to the reserve + 4 after the kit); budget 4470, 70 left`, byte for byte | ✅ observe buys 9a's balls, logs the plan |
| **K-SKIP** | balls `1`, kit `1`, no key items | 48/48 identical to B-ON; B-ON's ball line; `f176384 [KIT-BUY] why=kit-skip … reason=POKEBOT_R27_KEYITEMS is not 1: ordinary trainers would drain the kit (spec D2)` | ✅ the coupling holds, loudly |
| **K-KEY** | balls `1`, key items `1` | B-ON's ball line; 8 `[KEYBATTLE]` lines; no kit line | ✅ the matched control |
| **K-ON** | balls `1`, kit `1`, key items `1` | 40/40 identical to K-KEY up to AND including the Mart entry (`f176596`); then `f178117 [BALLS-BUY] why=topoff mart=11,7 ball=Poké Ball bought=8 premier=0 spare=7->15 money=9940->5540 exit=16,39 back=16,39 facing=Down reason=kit [('Super Potion', 4)] and 8 x Poké Ball (4 to the reserve + 4 after the kit); budget 4470, 70 left` and `f178117 [KIT-BUY] why=kit mart=11,7 kit=[('Super Potion', 4)] bought={'Super Potion': 4} money=9940->5540 …` (same reason) | ✅ one visit, one budget, the split order |
| **K-ONLY** | kit `1`, key items `1` | 40/40 identical to K-KEY up to the Mart entry; no ball line; `f177851 [KIT-BUY] why=kit mart=11,7 kit=[('Super Potion', 4)] bought={'Super Potion': 4} money=9940->7140 exit=16,39 back=16,39 facing=Down reason=kit [('Super Potion', 4)] and 0 x Poké Ball (0 to the reserve + 0 after the kit); budget 4470, 1670 left` | ✅ a kit-only walk |

- **K-ON spends exactly B-ON's money (₽4,400); only the ITEMS differ:** Poké +8, Premier +0, Super Potion +4, against
  B-ON's +22, +2, +0. None of Arm 6's falsifiers fired (no 22 balls, no Premier, no `failed` line).
- **Arm 8, the gates (not blind):**
  - `probe_kit_topoff.py` ALL PASS: 114 checks (47 rows + 67 mutant checks). Every one of its 64 mutants was red on
    EXACTLY its written set, and its 3 comment-only edits on none. That held on the first run after the adversarial
    pass. (The evidence file first said 116, a miscount; corrected there.)
  - The 9a, 9b and RULING 18 gates pass after the edits.
  - The adversarial pass ran BEFORE the gate was trusted: 41 mutants; this gate caught 2, the 9a gate 6 more, NEITHER
    caught 32. Each of the 32 now has a row. It also surfaced two code defects, fixed before the code commit (below).
  - The full suite, run after the review's fixes: **ALL 131 ENFORCING GATES PASS** (135 entries = 131 + 4
    advisory; 590 s). `probe_dexfence_opportunity.py` exits 1 as an ADVISORY probe, as it did in 9a's and 9b's
    suites (`evidence/2026-09-29-kittopoff10a-SUITE.txt`).

## SEEN, NOT GRADED

- **The kit was SPENT in the key battle, as designed, and the rival still won.**
  - K-ON started the rival (opp 600, `[KEYBATTLE] … key=True allow=True`) with `heal_stock=Super_Potion:4`. It used a
    Super Potion at 15/58, 17/58, 15/58 and 14/58 HP (uses 1-4: the per-battle cap) and ended with `heal_stock=-`.
  - Result: LOST at f192179, as in B-ON and K-KEY (f187576). The fight ran 12,134 frames against K-KEY's 7,409.
  - K-ONLY: the same four uses (at 5, 9, 16 and 12 of 58), LOST at f193192.
  - After the whiteout K-ON holds ₽2,770 and 15 balls, and K-ONLY ₽3,570 and 7 balls, against B-ON's ₽2,770 and 31.
  - ⇒ **On this seed, with a party of one L18 Marshtomp, 4 Super Potions do not flip the rival.** Whether the kit pays
    for itself is a step 14 (batch) question. It is exactly the kind of answer this single trajectory cannot give.
- **K-KEY differs from B-ON only by its `[KEYBATTLE]` lines** (the tracked lines minus those are identical, whole
  run): with no healing item held, key-item mode changes nothing here.
- **The kit lines are emitted where their decisions are made:** observe and skip at the heal's end (f176384); a
  purchase at the end of the walk (K-ON f178117, K-ONLY f177851, B-ON f178239).
- **The Mart visit is shorter with fewer lines:** f176596 → f178038 (B-ON, 1,442 frames); → f177916 (K-ON, 1,320);
  → f177650 (K-ONLY, 1,054).
- **`[KIT-BUY]` lines appear on the `[BALLS]` debug channel** (the errand's one `_emit`); a grep for `[KIT-BUY]`
  finds them either way.

## FOUND ALONG THE WAY (the adversarial pass, before the code commit)

- **A kit-only PLANNING failure logged `[BALLS-BUY] why=topoff-failed ball=-` and no `[KIT-BUY]` line.** That broke
  D8, which allows a ball line only when balls were planned and gives the kit `kit-failed`. Fixed: each flag logs its
  own tag, and with the kit OFF the line is byte-identical to 9a's. Gate row E12; mutants MSF1 and MSF2.
- **`_walk_buy_return` verified against the FILTERED lines.** When both sets were planned and the live list dropped
  one, that set's plan became empty and read as ok: a silent non-purchase. Fixed: it buys the filtered lines and
  VERIFIES against the planned ones, so a dropped set is a shortfall of its own set (D9). Gate rows W4 and W5;
  mutants MK, MVK and MVB.
- Neither path is reachable in these arms: Rustboro's live list is its static list, and no arm raised in planning.

## WHAT THIS DOES NOT SHOW

- Sootopolis (10b), whether the kit wins fights (step 14), a kit before gym 1 (the named gap), and a Mart selling a
  status cure (Rustboro sells none; the status line is proven only by gate rows K4, K5 and K17).
- A second seed. Every live arm is one trajectory, replayed. The pre-errand identity checks are determinism checks,
  not replications (KI-112: 1 of 3 identical runs once diverged by a frame; here none did).

## THE REVIEW (three lenses: spec, gate adversary, live integration; each finding put to a refuter)

- **Every live prediction held; the findings were code and gate gaps.** The live lens re-read the real collaborators:
  - `buy_in_shop` handles a mixed ball + medicine list, and a full Items pocket refuses after the confirm without
    charging;
  - the D2 premise holds: with key items on, a Super Potion is spent only in a key battle, and nothing outside battle
    uses one;
  - the memo resets per run;
  - the heal hunk cannot raise for a non-story mode.
- **R1, CONFIRMED by all three lenses (code):** a one-sided shortfall misreported the set that succeeded.
  - When the kit fell short and the walk came back, the balls (bought in full) were logged
    `topoff-failed … reason=the errand's frame bound expired`; the bound never fired, and the balls lost their success
    line. The mirror case gave the kit the balls' reason.
  - ⚠ Gate row E6 ASSERTED the defect, and W4/W5 asserted "no success line": the gate locked it in (`08`).
  - Fixed: each set is logged by its own verdict; the fallback reason separates "not back" from "bound expired".
    E6, W4 and W5 were rewritten; E19, E25 and W6 were added.
- **R2, PLAUSIBLE (code; the only live trigger is a fault arm):** under kit `observe`, a raise in a kit-only read
  cancelled step 9a's ball purchase and memoised the city, against D6.
  - Fixed: the kit is planned in its own try; a kit-only raise blocks only `<city>:kit`, and the balls stay 9a's. Row
    E24.
  - A planning raise now memoises the ball key only when the balls are on (always, with the kit OFF).
- **The proof that the kit OFF/skipped/observe is step 9a**, a differential the spec lens built. It exec's
  `61c6759e`'s module beside the fixed one over 16,128 (state, kit-mode) pairs: **0 differ** (the reviewed code had
  252, all R2). The walk: 432 states, 0 differ (`evidence/2026-09-29-kittopoff10a-REVIEW-DIFF.txt`).
- **The gate lens's STUB AUDIT** found two unfaithful fakes that had hidden R1's mirror and R2:
  - the `_kit_held` stub never raised: the harness now can (`kit_raise`, row E24);
  - the fake walk never produced "balls short, kit ok": a `ballshort` kind now does (row E19).
  - Its `ok` kind also reported `kit_got` of 0. That is fixed to the planned quantity; gate run 6 is ALL PASS with
    every red set identical to run 5.
- **The gate lens's second adversarial pass:** 34 new mutants. 12 were caught, 8 dropped as equivalent or contrived,
  and 14 reported (and the three defects above). Each reported one became a row or tightened one:
  - X3/X9, the key-item and RAWBAG flags read by truthiness: K14 and K13 pin "0";
  - X5, the kit flag defaulting ON: A4;
  - X4, parsed with 9a's `parse_flag`: A5;
  - Y1, the typo not on the console: A2;
  - X6, the kit loop starving the status line: K20;
  - X7, the ball reason not rebound: E22;
  - X8, a skipped kit still planned: E20;
  - Y14/Y47, the kit memo keyed on its mode: E21;
  - Y42-Y44, observe's failure branches: E23.
  - 23 new mutants in all.
  - Gate run 4 missed on two sets I had MIS-DERIVED (M7 omitted E21, M14 omitted A4). Both reds are legitimate; the
    sets were corrected with the reason in the gate. **Run 5: ALL PASS, 148 checks**
    (`evidence/2026-09-29-kittopoff10a-REVIEW-GATE.txt`).
- **Not taken:**
  - spec F3 (a kit-only "sells none" blocks the balls): its refuter showed it is unreachable at Rustboro and an
    explicit, commented D9 choice;
  - spec F4 (D8's `hp=`/`status=` form was not built): recorded as AS-BUILT in the spec and in `06`, because the built
    form was pre-registered and graded, and a 10b grader must use it.
- **The regression re-run**, its expected lines committed in `5e841f2c` BEFORE the run: all seven arms on the fix are
  identical to their graded runs on EVERY frame-stamped line (199-249 lines each, heartbeats included), and the grader
  gives 20/20 (`evidence/2026-09-29-kittopoff10a-REVIEW-RERUN.txt`). One trajectory per arm, replayed.
- **Seen along the way:** K-OFF's 199 frame-stamped lines equal 9a's M0-5-r1 byte for byte, and K-BALL's equal
  B-ON's. Step 10a is invisible to a kit-OFF run at the line level, not only at the tracked-line level.
