# 2026-09-30 — design v2 step 11 (M1, damage-calculator fidelity): PRE-REGISTERED PREDICTIONS, filed before the code

> Filed BEFORE any step-11 code exists (the branch `wt/dmgcalc11` holds docs only at this commit). The design is
> `2026-09-30-dmgcalc11-DESIGN.md` (F1-F10, after a recon, a three-lens review and the Step-0 live reads).
> DRIVER: storyresume (the M1b live arms; M1a and the audit are pure gates).
> **How each prediction is graded.** Step 11 is graded by NAMED GATE ROWS (`probe_damage_calc_decomp.py`,
> `probe_dmgaudit.py`) and by the NAMED OUTPUTS of `audit_damage_calc.py` on the live arms' debug logs, not by
> `story_harness.py` R keys, so the predictions carry no `### P<n>` headings (the convention `probe_predictions_gradeable`
> enforces for harness-graded drives; steps 7 and 8, also gate-graded, did the same). Each item below names its grader.
> **Where the literals come from.** Every GAME value was derived by hand from the decomp TWICE, independently: by the
> author (Group D) and by a fresh agent that was forbidden to read the calculator (all rows; its derivation is
> `2026-09-30-dmgcalc11-recon/m1_rows_game.md`, committed with this note). Every OURS value pins current behaviour and
> was measured by running the real calculator offline on real `BattlePokemon`/`BattleState` objects built from
> 0x58-byte records, with the side membership asserted per row (`m1_rows_ours.md`). ⛔ A game value is never taken
> from the step's own port: the port is checked AGAINST these literals.

## M1a — `probe_damage_calc_decomp.py`

**The anchors and the known-divergence rows.** Each row asserts three literals: the game (port, or hand for a base-term
row), ours, and the delta. Group D starts from a GIVEN base B (the calculator's `_calculate_base_move_damage` patched to
return B); Group B runs the full calculator. Ranges are [min, max] at the random factor's 85% and 100% ends.

| Row | What it pins | Game | Ours (current) | Delta on max |
|---|---|---|---|---|
| D-A1 | the crit applied after STAB/type (Fighting STAB vs Normal/Rock, B=3, crit) | [30, 36] | (27, 32) | −4 |
| D-A2 | the same with Charge (Spark STAB vs Water/Flying, B=3, crit + Charge) | [61, 72] | (54, 64) | −8 |
| D-A3 | Mud-Slap STAB vs Electric/Steel, B=5, crit | [51, 60] | (47, 56) | −4 |
| D-N1 | the type order, under (Bite STAB vs Sableye Dark/Ghost, B=5) | [5, 7] | (5, 6) | −1 |
| D-N2 | the per-step minimum of 1 (Signal Beam vs Steel/Flying, B=2) | [1, 1] | (1, 0) | −1 |
| D-O1 | the type order, over (a Fighting move vs Rock/Flying, B=3) | [1, 2] | (2, 3) | +1 |
| B-MS1 | Marvel Scale on the (burned) DEFENDER | [10, 12] | (14, 17) | +5 |
| B-MS2 | Marvel Scale wrongly on our (poisoned) attacker | [14, 17] | (10, 12) | −5 |
| B-GUTS | Guts + burn (no halving in the game) | [35, 42] | (18, 22) | −20 |
| B-BB | Brick Break removes Reflect first | [88, 104] | (45, 54) | −50 |
| B-KI110 (B7 set) | our Sp. Def boost on badge 7 (foe → us) | [22, 27] | (23, 28) | +1 |
| B-KI110 (B8 set) | the same, badge 8 only | [23, 28] | (22, 27) | −1 |
| B-KI111 | Solarbeam in rain | [71, 84] | (137, 162) | +78 |
| B-STR | Struggle is typeless (vs Ghost) | [20, 24] | (1, 0) | −24 |
| B-HP | Hidden Power (all IVs 31: Dark, 70) | [27, 32] | (27, 32) | 0 (a FIDELITY row, not a divergence) |
| B-HPC | Hidden Power rolled Electric under Charge (IVs 31/31/31/31/30/31) | [54, 64] | (108, 128) | +64 |
| B-SONIC | Sonicboom (KI-109; ours with every stat 100) | 20, no random | (3, 4) | −16 |
| B-PSY | Psywave at L30 (KI-109; the minimum is level/2) | [15, 45] | (2, 3) | −42 |
| B-NS | Night Shade vs Normal (immune in the game) | 0 | (30, 30) | +30 |
| B-ST | Seismic Toss vs Ghost | 0 | (30, 30) | +30 |
| B-SF | Super Fang vs Ghost | 0 | (100, 100) | +100 |

The inputs of every row are in `2026-09-30-dmgcalc11-recon/m1_rowspec.md` (committed with this note).

**The enumerated bounds** (the real calculator after the base term vs the port, every move type × every ordered defender
type pair from the ROM chart × STAB × crit × Charge × B = 2..259; ⚙ the design review measured this sweep at 36 s):

| Bucket | Ours UNDER the game, max (HP) | Ours OVER the game, max (HP) | Min end, max \|Δ\| |
|---|---|---|---|
| non-crit | 1 | 1 | 1 |
| crit | 4 | 0 | 4 |
| non-crit + Charge | 4 | 0 | 4 |
| crit + Charge | 8 | 0 | 7 |

- Each bound is AT LEAST its bucket's largest anchor delta above (4 ≥ D-A1/D-A3's 4; 8 ≥ D-A2's 8; 1 ≥ D-N1/D-N2's 1;
  D-O1's +1 for "over"). After the first run the bounds are asserted exactly, each with its witness tuple pinned.
- **Falsifier:** a bound below its anchor means the PORT is wrong (not the calculator); a bound above the pre-registered
  value is a RESULT to report, not a failure to explain away.

**The mutants (sets written in the gate before its first run), the predictions for three named ones:**
- "the port in OUR order" (crit and Charge after STAB/type): the Group D anchor rows turn red.
- "the calculator with D1 FIXED" (crit and Charge moved before STAB/type in `_util.py`): D-A1, D-A2 and D-A3 flip (ours
  equals the game), so their three-literal rows turn red; every Group B row stays green.
- "swapped type order in the port": D-N1 and D-O1 turn red.
- The gate runs under 300 s.

## G-AUDIT — `probe_dmgaudit.py` (the pure classifier and acceptance gate)

- Every classifier row and every acceptance row the design names (F4) passes: the battle-end pair, the trainer-KO pair,
  a turn gap, a double BEFORE, a changed PID, unchanged PP, a chosen move ≠ the slot whose PP dropped, a negative Δ,
  a bide/HP disagreement, one row per stratum reason; and the acceptance: crit_max + ACCEPT_MARGIN + 1 → FAIL, the
  same in an excluded stratum → PASS, exactly at the bound → PASS, 299 samples → "insufficient".
- Its mutant sets are written in the gate before its first run, after an adversarial mutant pass.

## M1b — the live arms (post_mtpyre, `storyresume --frames 90000`, seed 1, the SAME build commit)

The Step-0 probe ran this exact trajectory at the base code (`evidence/2026-09-30-dmgcalc11-STEP0.txt`), and the
build changes nothing with the flag unset, so its frames are the prediction. (KI-112: if a run diverges, the design's
decision rule applies, and the per-turn table is graded only on a reproducing trajectory.)

- **OFF ×2:** the two runs match each other on every frame-stamped line; 0 lines contain `DMGAUDIT`.
- **ON ×2:** each equals a reproducing OFF run on every frame-stamped line that does not contain `DMGAUDIT` (the report
  names the first difference, if any); every `DMGAUDIT` line matches `^f\d+ \[DMGAUDIT\] `, and no `[BATTLE]` line
  contains `DMGAUDIT`.
- **Non-vacuity (graded by `audit_damage_calc.py`'s outputs on the ON runs):** a `CTL` line at each of the 15 battle
  starts; ≥ 1 ACCEPTED whitelisted non-KO hit with Δ`gBideDmg[1]` = the foe's HP difference (three are predicted:
  Manectric 83 → 18 = 65 at f3190263, Vigoroth 88 → 24 = 64 at f3198642, Linoone 82 → 8 = 74 at f3216950); ≥ 1 accepted
  battle-end KO pair; the doubles stratum on the three Route 123 doubles; the foe-item-action stratum at f3191078
  (Marcel's Hyper Potion); the held-item stratum on Vanessa's Pikachu (Oran Berry, the decomp's `sParty_Vanessa`).
- **The per-turn verdict table (the 17 singles USE_MOVE exits of the Step-0 trajectory; graded line by line):**

| Exit frame | Foe (trainer / wild) | What happened | Predicted verdict |
|---|---|---|---|
| f3173282 | Hideo's Koffing #1 | KO'd, replaced (Δbide 90 ≥ 55); it had chosen Self-Destruct | excluded: the foe's chosen move hurts itself |
| f3174185 | Hideo's Koffing #2 | battle-end KO (55, Δbide 87); it chose Poison Gas | ACCEPTED, KO |
| f3185457 | Vanessa's Pikachu | our Mightyena asleep, PP unchanged | not a sample (our move did not run) |
| f3186160 | Vanessa's Pikachu | asleep again | not a sample |
| f3186810 | Vanessa's Pikachu | PP down, Δbide 0 (a miss) | excluded: no damage (and the held-item stratum) |
| f3187609 | Vanessa's Pikachu | battle-end KO (61, Δbide 128) | excluded: the foe holds an item (Oran Berry) |
| f3190263 | Marcel's Manectric | 83 → 18 = 65; it chose Howl | ACCEPTED, clean hit |
| f3191078 | Marcel's Manectric | 18 → 18, Δbide 65; its action was an item | excluded: the foe used an item |
| f3191967 | Marcel's Manectric | KO'd, replaced by Shiftry (Δbide 69 ≥ 18) | ACCEPTED, trainer KO |
| f3193320 | Marcel's Shiftry | battle-end KO (94, Δbide 142); it chose Harden | ACCEPTED if our hit came first, else excluded: the foe's Def stage changed (either is correct; the read decides) |
| f3197066 | Cristin's Loudred | KO'd, replaced (Δbide 97 ≥ 91) | ACCEPTED, trainer KO |
| f3198642 | Cristin's Vigoroth | 88 → 24 = 64; it chose Uproar | ACCEPTED, clean hit |
| f3199547 | Cristin's Vigoroth | battle-end KO (24, Δbide 61); its chosen move reads 0 (the Uproar lock) | excluded: the foe's chosen move is 0 |
| f3208167 | wild Poochyena | battle-end KO (60, Δbide 107) | ACCEPTED, KO (wild) |
| f3210218 | wild Shuppet | battle-end KO (68, Δbide 198; Bite vs Ghost ×2) | ACCEPTED, KO (wild) |
| f3216950 | wild Linoone | 82 → 8 = 74 | ACCEPTED, clean hit (wild) |
| f3217980 | wild Linoone | battle-end KO (8, Δbide 73) | ACCEPTED, KO (wild) |

  (17 rows: the Step-0 table's f3173282 through f3217980, singles only; the five doubles exits go to the doubles
  stratum.) ⚠ Whether each ACCEPTED sample lies within [min, crit_max] depends on the live prediction, which is not
  pre-registered here. The only prediction on that is F8's: with 7 to 10 accepted samples, 0 over crit_max + 3 is
  EXPECTED (a D1 failure needs a STAB 4× crit, about 1/512 per such hit), and any over is reported, not explained away.
- **FAULT (gBideDmg[0] read in place of [1]):** the self-check's disagreement count is 0 in ON on the named clean turns
  (f3190263, f3198642, f3216950), and > 0 in FAULT on those same turns.
- **DIFF (the base module vs the new, flag unset, through `repro_ki46_action_selection_bound.py`'s fake readers):**
  identical yields and lines; the same number of `get_battle_state()` calls with the flag on and off.
- **EXEC:** the new code in the battle-action module runs to its end with its `except` removed.
- **AUDIT:** the raw `[DMGAUDIT]` line count equals the parsed count in both ON runs; no 30 MB cap marker.

**Falsifiers:** an ON run that differs from a reproducing OFF run on any line without `DMGAUDIT`; a `DMGAUDIT` line in
an OFF run or under `[BATTLE]`; an accepted sample the table calls excluded (or the reverse) on a reproducing run;
FAULT not above ON; a Group B or D literal that the gate's port or calculator does not reproduce.

## ADDENDUM (2026-09-30, ~8:05 AM LA): the BASE-vs-build divergence A/B, filed AFTER the five arms ran and BEFORE this A/B

⚠ **This section is NOT part of the pre-registration above.** It was written after the arms had run. It predicts only
the A/B below, and it changes no row above.

- **What the arms showed (build `c44b1def`):**
  - OFF-r1 = OFF-r2 on all 371 frame-stamped lines.
  - ON-r1 and ON-r2 each equal them on every line without `DMGAUDIT`.
  - All four follow the Step-0 trajectory EXACTLY to f3215340 (Route 119, the `[hb]` at (35, 90)).
  - At that point the Step-0 run met a wild Linoone at (22, 127) (f3215905); the four build runs walked on to Route 118
    at f3215976.
  - So the per-turn table's two Linoone rows (f3216950, f3217980) are on a branch the build's runs never reach.
- **The A/B:** the BASE code (`241929d7`'s two production modules, loaded in place of the build's by scratch
  `run_base_off.py`, in the SAME worktree, profile and caches), run twice exactly like the OFF arms.
- **H1 (predicted): the build is not the cause.** BASE-r1 = BASE-r2 = OFF-r1 on every frame-stamped line (no Linoone).
  Then the Step-0 run is the odd trajectory: either its wrapper probe's own overhead or KI-112's wall-clock input. Its
  cause is NOT decided by this A/B.
- **H2 (the falsifier of "the build is inert"):** a BASE run follows the Step-0 lines past f3215340 (the Linoone).
- **H3:** the BASE runs differ from each other. Then this point is KI-112-unstable, and neither trajectory is "the"
  prediction.
- **The grading rule for the per-turn table, already filed above ("graded only on a reproducing trajectory"), applied:**
  - the 15 rows f3173282 … f3210218 are graded as filed;
  - the two Linoone rows are NOT REACHED, never counted as PASS;
  - singles exits past the divergence were never pre-registered, and are reported, not graded.
- **What this changes, and what it does not:**
  - Non-vacuity's "the three named clean hits" loses f3216950. The two others stand.
  - "A CTL line at each of the 15 battle starts" becomes 14 on the build's trajectory (the Linoone battle is absent).
  - The FAULT arm's named turns are the two reached (f3190263, f3198642).
  - The accepted count is 8, inside the predicted 7 to 10. The "9 or 10 on this trajectory" count in the design's AS
    BUILT section assumed the Linoone rows.
