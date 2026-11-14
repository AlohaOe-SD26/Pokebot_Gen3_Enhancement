# P-G6 diagnosis: why the Grovyle plan got BADGE02 in 1 of 3 round-4 runs (BP-1 round 4, third builder, 2026-11-12)

**THIS IS A NOTE, NEVER A SOURCE OF TRUTH** (the rule for this folder: `00-READ-THIS-FIRST.md`). WHO WROTE IT: BP-1
round 4's third builder (a Claude agent), on 2026-11-12, as `s53/bp1r4/PG6-DIAGNOSIS.md` in the lab, read-only on the
kept records of the round's live runs. It is filed here by round 4's closing pass (its second builder), unchanged except
where a line is marked CORRECTED: the round-4 verifier's V4-m1 (Leaf Blade is not a law) and, to agree with the evidence,
its V4-n2 (no counterfactual). WHAT TRIED TO REFUTE IT: the verifier's paired live A/B on three new Grovyle-plan seeds
(6421, 6424, 6430; ledger #129-#131), round 3 (975964c7) against round 4 on the same seed: round 4 won BADGE02 in 3 of
3, round 3 in 1 of 3, and the A/B's own refutation test of (S), V-7, held
(`ai_player/evidence/2026-11-12-bossprep-bp1r4-verify-ab.txt`). It did not refute (S). WHAT STAYS UNPROVEN: that the
seeds, and not round 4, caused P-G6's miss (three pairs, one trajectory per seed and arm, never a rate: the A/B points
the same way and does not prove it); whether E5's earlier Centre visit changed anything (section 5); whether a full-PP
first fight would have been won; and the Leaf Blade line is an association (5 of 5 fights won at or above it, 3 of 22
below it, over 27 fights), not a law.

**Added by the lead at the closing pass's commit (the closing verifier's VC-n2 and VC-n3).** Two edits carry no
CORRECTED marker: the verdict's "lose ... win" now reads "lost ... won", and the Files list at the end was extended with
the verifier's A/B and the closing pass's counts. And "every lost fight gained 613 EXP" is true of the builder's 15
fights (the table in section 1). It is not true of all 27: in the verifier's A/B, round 3's arm on seed 6424 lost its
first fight with a Grovyle at L24 and gained 0 EXP (10588 before fight 1 and before fight 2).

P-G6 (hashed 2026-11-11 20:00) predicted BADGE02 in each Grovyle-plan run of round 4 (B4: seeds 6426, 6427, 6429). It
MISSED: 1 of 3 (6426 and 6427 ended on 3 battles lost, all to BRAWLY; 6429 lost twice, then won). Round 3's B3 (975964c7,
seeds 6411-6413) had 3 of 3. Development runs, one trajectory per seed: nothing below is a rate.

## Verdict: (S), with one caveat

The evidence supports (S): the same decisions in the same kind of situation, in a fight that both rounds lost without
Leaf Blade (11 of 12 such fights lost, B3 3 of 4, B4 8 of 8) and won with it (3 of 3). Round 4's runs reached BRAWLY with
less experience than round 3's, and that shortfall arose after the raise had ended, where no round-4 change ran.

**[CORRECTED 2026-11-12, the round-4 verifier's V4-m1.]** It read "a fight that both rounds lose without Leaf Blade ...
and win with it", as a law. Those counts are the builder's 15 fights. Over all 27 BRAWLY fights of both kits (the
verifier's 12 paired-A/B fights added; `s53/bp1r4c/leaf_count.py`), a fight that began at 18798 EXP or more was won 5 of
5, and one that began below it 3 of 22. All three wins below the line came without Leaf Blade: B3 6411's second fight at
17433 EXP, and, in the verifier's A/B, round 4's 6421 first fight at 18422 and 6424 second fight at 17715. Leaf Blade is
strongly associated with the win; it is not a law. (S) does not rest on the law: it rests on the identical decisions
(section 4) and on where the shortfall arose (section 2).

The caveat: one round-4 change did alter the state the trainee arrived in. E5's PP rule moved the raise's one Centre
visit earlier, so 6426 and 6427 began their first BRAWLY fight without Pursuit (and, in 6426, without Quick Attack).
**[CORRECTED 2026-11-12, the round-4 verifier's V4-n2.]** It read "On these records that changed no fight's experience
and no outcome", which the records cannot show: they do not show what full PP would have done. There is no sign that it
changed an outcome: the first fight was lost in all six runs of both rounds, with or without those moves; every lost
fight gained the same 613 EXP; the moves missing were Quick Attack (Normal, power 40, as Pound, which it kept) and
Pursuit (Dark: resisted by MACHOP and MAKUHITA); and in the verifier's 6421 pair both arms began fight 1 without Pursuit.

No play code was changed for P-G6. What the fight needs is a design matter, listed at the end for the lead.

## 1. What a BRAWLY fight's outcome goes with here: the experience at its start (Leaf Blade at L29)

**[CORRECTED 2026-11-12, V4-m1: this heading read "What decides a BRAWLY fight here".]**

`exp_b3.py` (writes `exp_b3.json`) follows the trainee by PID 3495168255 from the run's first observation (its
`experience`) through the game's own "GROVYLE gained N EXP. Points!" messages. SELF-CHECK: the sum equals the last
observation's experience of the same pid in 6 of 6 runs (18400, 20281, 20019, 18874, 18819, 19782).

| run | fight | level, HP at start | EXP at start | gained in it | L29 / Leaf Blade | outcome |
|---|---|---|---|---|---|---|
| B3 6411 | 1 | L27 72/72 | 16820 | 613 | no | lost |
| B3 6411 | 2 | L28 75/75 | 17433 | 967 | no | WON |
| B3 6412 | 1 | L28 68/76 | 18701 | 613 | no | lost |
| B3 6412 | 2 | L28 76/76 | 19314 | 967 | yes | WON |
| B3 6413 | 1 | L28 76/76 | 18439 | 613 | no | lost |
| B3 6413 | 2 | L28 76/76 | 19052 | 967 | yes | WON |
| B4 6426 | 1 | L27 62/73 | 17035 | 613 | no | lost |
| B4 6426 | 2 | L28 75/75 | 17648 | 613 | no | lost |
| B4 6426 | 3 | L28 75/75 | 18261 | 613 | no | lost |
| B4 6427 | 1 | L27 70/73 | 16980 | 613 | no | lost |
| B4 6427 | 2 | L28 76/76 | 17593 | 613 | no | lost |
| B4 6427 | 3 | L28 76/76 | 18206 | 613 | no | lost |
| B4 6429 | 1 | L28 75/75 | 17589 | 613 | no | lost |
| B4 6429 | 2 | L28 75/75 | 18202 | 613 | no | lost |
| B4 6429 | 3 | L28 75/75 | 18815 | 967 | yes | WON |

Every lost fight gained exactly 613 EXP (MACHOP and MEDITITE knocked out, MAKUHITA not); every won fight 967. Grovyle
learns Leaf Blade at L29 (Medium Slow: 19411 EXP). A fight that starts at 18798 EXP or more (19411 - 613) reaches L29
before MAKUHITA: 3 of 3 won. Below it: 1 of 12 won (B3 6411's second fight, without Leaf Blade). Both rounds show the
same association. **[CORRECTED 2026-11-12, V4-m1: it read "Both rounds follow the same rule". With the verifier's 12
paired-A/B fights, 27 in all: 5 of 5 won at or above the line, 3 of 22 below it.]**

So with MAX_LOSSES 3 a run reaches the line by its third fight when it arrives at BRAWLY with at least 17572 EXP (two
losses add 1226). B3: 16820 (won its second fight below the line), 18701, 18439. B4: 17035, 16980, 17589 (6429 by 17
EXP). **[CORRECTED 2026-11-12, V4-m1: it read "a run gets BADGE02 (barring a lucky fight) when it reaches BRAWLY with at
least 17572 EXP" and "won its second fight by luck". The line is an association, not a law: 3 of the 27 fights were won
below it.]**

## 2. Where the shortfall arose: after the raise ended, not in it

| run | EXP at SPENT | EXP at the first fight | gained in between | frames in between |
|---|---|---|---|---|
| B3 6411 | 15796 | 16820 | 1024 | 108,632 |
| B3 6412 | 16200 | 18701 | 2501 | 187,294 |
| B3 6413 | 16361 | 18439 | 2078 | 168,035 |
| B4 6426 | 16405 | 17035 | 630 | 105,082 |
| B4 6427 | 16386 | 16980 | 594 | 87,656 |
| B4 6429 | 16283 | 17589 | 1306 | 143,160 |

The raise ended on its battle budget (160) at L27 in all six runs (`raise_reach_r4.py`: battles 160-164), and B4's raise
ended with as much EXP as B3's or more. The difference came in the stretch from SPENT to the gym (RUSTBORO's mart, MR.
BRINEY, DEWFORD, GRANITE CAVE): B3 6412 and 6413 took 168k-187k frames with Centre trips (6412's trainee fell to 12/76
after a long fight with an Aron; a member fainted in 6413, and 6413 topped up before the fight at 85%), and met more wild
Pokemon on the way; B4's stretches were 88k-143k frames.

## 3. Did a round-4 change run after SPENT or in the fights? No (counted, with a positive control)

`sig_b3.py` counts the lines each round-4 change writes when it acts, per run, in three segments: R (the raise: the first
raise goal to SPENT), S (SPENT to the first BRAWLY fight), F (the fights to the run's end).

| run | R: raise / guard / PP (fight_safe) / PP (rest) / last resort | S | F |
|---|---|---|---|
| B3 6411 | 324 / 3 / 0 / 0 / 0 | 0 | 0 |
| B3 6412 | 320 / 2 / 0 / 0 / 0 | 0 | 0 |
| B3 6413 | 324 / 3 / 0 / 0 / 3 | 0 | 0 |
| B4 6426 | 328 / 2 / 5 / 3 / 0 | 0 | 0 |
| B4 6427 | 328 / 3 / 9 / 4 / 3 | 0 | 0 |
| B4 6429 | 326 / 2 / 5 / 3 / 0 | 0 | 0 |

The counter finds the lines where they are (segment R, the POSITIVE CONTROL), and finds none after SPENT or in the fights.
(B3's "last resort" matches are round 3's own fallback words, which round 4's E2 kept.) The battles' purposes after SPENT
are "train" and "travel" only in both rounds, never "raise". The code says why:

- E2 (the guard's order) and E3 (the trainer-battle test) live in `BattleMind._guard_turn`, which returns at once when
  nobody is protected. The guard is None in the boss fight (`GoalRunner._guard_for`: the boss fight is left out, in both
  trees) and after SPENT (`_plan_trainee` needs the plan's status "active"). `_raise_turn` needs purpose "raise".
- E4 (the guard and purpose between goals) is silent. It would show as a battle with purpose "raise" outside a raise, or a
  guard after a goal. After SPENT both trees have no guard and no raise purpose.
- E5 (PP): its rest rule and fight_safe's PP count are plan rules (an active plan's trainee). They fired in the raise only:
  in each B4 run the raise's one Centre visit came for PP ("the raise's trainee Grovyle L25 is out of PP", f950553 -
  f956213), where B3's came later for low HP (f974100 - f992466, after fighting with Absorb alone). That is the caveat:
  6426 then fought 109 battles to BRAWLY without a PP restore, 6427 99; their first fights began without Pursuit (6426
  also without Quick Attack). B3 6411 had 89 battles since its visit and kept every move; 6412, 6413 and 6429 had Centre
  visits after SPENT.
- E1 does not apply to the Grovyle plan (no knock-out partner). Its other half, the budget checked before any rest, made
  no difference at SPENT: the trainee was at full HP in all six runs, so neither tree had a rest due.
- The pre-boss top-up (`goals.py` HEAL_BEFORE_FIGHT 0.9, the party's HP share) is unchanged by round 4.

## 4. The fights' decisions through both trees, offline, with a CONTROL

`extract_b3.py` writes `bossfights_b3.json`: every decision of the 15 BRAWLY fights with the situation the records hold
(the game's party read and foe from the digest; the member on the field; the moves the AI listed as usable; the potions
left). `replay_b3.py <tree> <out>` replays them through one tree's battle brain: a fresh BattleMind per fight as the live
one was made ("Story", purpose "train", no guard), the same seeded rng for every tree, and the live history told back so
every tree walks the same path; sends through `replacement`, questions through `answer` and `learn_choice`.
`compare_b3.py` compares.

Predictions hashed first: `prediction_replay_b3.txt` sha256 c8ee3c14...; after the first run showed that 58 "decide"
notes were sends and learning questions, `prediction_replay_b3_addendum.txt` sha256 df8f80d6... before the corrected run.

- P-R1' HOLDS: 975964c7 (lab copy `base/`, line-ending-blind equal to the commit) and the round-4 tree give the identical
  (kind, choice) and identical words on 323 of 323 events (235 decisions, 55 sends, 33 questions).
- P-R2' HOLDS, the CONTROL: a copy of the round-4 tree with `_heal`'s threshold doubled (`plant_b3/`) differs in 14 of 15
  fights (59 decisions); each fight's first difference is (item, Potion) in the plant where the round-4 tree fights.
- P-R3' HOLDS: no send differs before it.
- Fidelity to the live records: 235 of 235 decision kinds (15 Potions), 219 of 220 live moves inside the replay's own
  candidate set, the candidate sets equal in 217 of 220, sends 55 of 55, answers 33 of 33. The chosen moves agree in 130 of
  220: most choices are draws among about-as-good moves, and the live rng state is not in the records.

So in these situations round 4 decides exactly as round 3 does.

## 5. What the evidence does not settle

- Whether E5's earlier rest changed the stretch after SPENT through the trainee's PP (a long fight with fewer moves can
  cost HP and so a Centre trip, which in B3 6412 lengthened the stretch and ADDED experience). The records show no
  consistent direction, and three runs a round cannot.
- Whether a full-PP 6426 or 6427 would have won its first fight. Without Leaf Blade, full-PP fights were won 1 in 10.

## 6. What the fight needs (DESIGN, for the lead; no play code changed)

1. The raise's target and budget against the key move's level: the Grovyle plan targets L30, but its 160-battle budget
   ends it at L27 (15796-16405 EXP in all six runs), 3006-3615 EXP short of L29, where Leaf Blade is strongly associated
   with the win. **[CORRECTED 2026-11-12, V4-m1: it read "where Leaf Blade decides the fight".]** These raises gained
   54-58 EXP per counted battle on ROUTE116 (from the start's 6976), so L29 is about 52-66 more.
2. What a lost boss fight changes before the next try: today it walks straight back (whiteout, Centre, gym) with the same
   team and 613 more EXP. 6426 and 6427 used their three tries 537-592 EXP short of the line.
3. A heal before the boss that counts PP: the top-up is by party HP only (0.9). 6426 and 6427 began fight 1 without
   Pursuit (6426 also without Quick Attack) at 62/73 and 70/73, the party above 0.9. There is no sign that it changed an
   outcome. **[CORRECTED 2026-11-12, V4-n2: it read "On these records it changed no outcome".]**

## Files (s53/bp1r4)

exp_b3.py / exp_b3.json; arrival2_b3.py, arrival3_b3.py, ppheal_b3.py (the stretch and the PP); sig_b3.py (the
signatures); extract_b3.py / bossfights_b3.json; replay_b3.py; replay_base_b3.json, replay_wt_b3.json,
replay_plant_b3.json; compare_b3.py / compare_b3.json; make_plant_b3.py / plant_b3/ (the control tree); replay_run1/ (the
first, uncorrected run); prediction_replay_b3.txt, prediction_replay_b3_addendum.txt. The earlier builders' boss_cmp_r4.py,
raise_reach_r4.py, lead_peek_boss.py read the same records. The verifier's A/B: s53/bp1r4/verify (v_judge_vab.py,
v_judge_vab.json, out/vabg1-3). The closing pass's counts: s53/bp1r4c (leaf_count.py, e5_check.py, e2_count.py).
