# PRE-REGISTERED PREDICTIONS — `#24-swaptrigger2`, the swap-trainer's SECOND trigger

**Written 2026-09-23, BEFORE the drive.** Committed first so that a reading which contradicts a
prediction is a **RESULT**, not a driver failure — the standing rule in `.claude/skills/story-drive`.

---

## THE QUESTION, AND WHY IT BLOCKS PIECE 3

USER RULING 12 keeps all six mōn and trains the two stragglers on the per-trainee Fly ladder. The
ladder's entire escape from the L89-L94 overshoot is that a **level-matched trainee solos**, so no
finisher splits its exp.

`max_wild_max` kills only **trigger 1**. `SwapTrainBattleStrategy.decide_turn` fires on
`(underleveled or cant_continue)`, and

```
cant_continue = not self._pokemon_has_enough_hp(active)          # HP  < battle.hp_threshold
             or not any(util.move_is_usable(m) for m in active.moves)   # PP  all zero
```

Neither half is touched by the out-level rule. When it fires, `_capable_finisher` picks the
**strongest** healthy mōn that out-levels the foe — and at a level-matched ground the foe is LOW, so
almost any L75 qualifies. The exp then splits exactly as before, and the ladder's benefit evaporates.

**✅ THE PP HALF IS ALREADY SETTLED BY ARITHMETIC** (`probe_ladder_economics.py`): Zigzagoon carries
**80 PP**, so at ~3 turns/battle it survives **~27 battles** before every move is empty.
**⛔ THE HP HALF IS NOT.** That is what this drive measures.

---

## THE DRIVE

* **Fixture:** `post_ch24_atdoor_L75.ss1` — party at Ever Grande, Zigzagoon **L19**, four L75s.
* **Route:** the REAL leg — `_fly_to_training_anchor` to Verdanturf, then `_goto_training_area` to
  the ROUTE117 spin tile `(31,16)`. Wilds there are **L15-20**, so Zigzagoon L19 out-levels the band
  under the out-level rule (`hi=20 <= 19+1`).
* **Then:** grind, with `SwapTrainBattleStrategy.decide_turn` WRAPPED to count which branch fired.
* ‼ **Instrument the value the code ACTS ON** — the branch taken and the chosen finisher INDEX —
  never a candidate list. *A candidate is not an attempt.*

---

## PREDICTIONS (each with the falsifier that would refute it)

### P1 — Trigger 1 (`underleveled`) fires **ZERO** times.
Zigzagoon L19 vs a L20 foe needs `19 + 2 <= 20`, which is false. The out-level rule is supposed to
make this structural.
**FALSIFIER:** any trigger-1 firing ⇒ either `max_wild_max` is not being applied on this path, or
the ground's real wild band exceeds the table's `hi=20`. Either would mean the ladder's headline
mechanism does not work as specified.

### P2 — Trigger 2's **PP** half fires ZERO times in the first ~27 battles, then begins firing.
80 PP ÷ ~3 turns/battle.
**FALSIFIER:** PP-half firings before ~20 battles ⇒ turns/battle is materially higher than the
conservative 3 assumed in the economics, and **every heal-cadence number in
`probe_ladder_economics.py` is too generous**. That would not kill the ladder but it would shorten
the cadence and raise the heal-trip count.

### P3 — ⭐ **THE ONE THAT MATTERS: trigger 2's HP half fires in FEWER THAN 10 % of battles.**
`hp_threshold` is 20 %, Zigzagoon has 48 HP (so the threshold is < ~9.6 HP), and it out-levels its
foes. Losing 80 % of its HP in a short wild battle it is winning should be uncommon.
**FALSIFIER — and this is the decision point:** ≥ 25 % of battles firing the HP half means a L75
finisher enters a quarter of all battles, the participant divisor applies to those, and the ladder's
22.3 h creeps toward the 2-way 43.0 h. ⇒ **Ruling 12 would need to go back to the user with real
numbers**, exactly as `06-DECISIONS-LOG.md` RULING 12 says.

### P4 — When a finisher IS chosen it is a **L75**, not Castform L36.
`_capable_finisher` takes `max(..., key=level)` among those that out-level the foe.
**FALSIFIER:** Castform being chosen ⇒ my reading of `_capable_finisher` is wrong, and the exp-split
arithmetic in the economics probe is built on a wrong model of who absorbs the share.

### P5 — Zigzagoon's `total_exp` rises by **≈ `xp_per_battle(20)` ≈ 143 per battle** while soloing.
The modelled figure from `training_areas.xp_per_battle`.
**FALSIFIER:** a materially lower per-battle gain while trigger counts show ZERO swaps ⇒ the
`_CALIBRATED_AVG_WILD_BASE_EXP_YIELD = 50.2` constant is wrong for this band, and every hour figure
in the economics inherits that error.

### P6 — The Fly leg reaches ROUTE117 at all.
`_fly_to_training_anchor` + `_goto_training_area` have never been exercised by a driver in EITHER
fork. `promote.py` says so explicitly: *"a copy is not evidence… verify by DRIVING."*
**FALSIFIER:** the leg fails to arrive ⇒ Pieces 2b/2c are wrong in a way three static gates could
not see, and the promotion needs revisiting rather than the ladder.

---

## ⛔ WHAT THIS DRIVE CANNOT SETTLE, STATED SO NO ONE OVER-READS IT

* **It is ONE trajectory.** A firing RATE from a single grind is an estimate with a wide interval at
  ~50 battles. It can refute P3 decisively (a high rate is a high rate); it can only weakly support
  it.
* **It measures Zigzagoon at ROUTE117 only.** The climb spends **822 of its ~1,055 battles on
  ROUTE121**, where the foe is L38 and the trainee is L37-65. HP pressure there is a different
  question, and a clean result here does **not** transfer.
* **It says nothing about trainer sight cones** on the approach; the planner is structurally blind
  to them and ROUTE117 has ten trainers.
