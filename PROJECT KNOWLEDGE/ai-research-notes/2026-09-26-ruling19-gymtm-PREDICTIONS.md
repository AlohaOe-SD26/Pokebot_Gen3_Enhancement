# 2026-09-26 — USER RULING 19 (teach an owned TM when a gym keeps winning): PRE-REGISTERED PREDICTIONS

> Filed BEFORE any `--driver gymtm` drive. A reading that contradicts a prediction is a RESULT, never a driver failure.
> Code (branch `wt/ch24organic`, uncommitted at filing time): `modules/story/gym_tm_teach.py`, the hook in
> `StoryMode._prepare_for_fight`, the foe recorder (`battle_action_selection.TURN_FOE` → `_loss_foe_history`), gate
> `probe_gymtm_teach.py` (PASS at filing), driver `--driver gymtm`.

## What changed in the design before any drive (so the predictions below are about design 3)

* **Design 1 named the wall by KO COUNT** (`roster[kos]`). A decomp read (Claude agent, `battle_ai_switch_items.c`
  `GetMostSuitableMonToSwitchInto`) refuted the premise: only the lead is party order. **MEASURED** from the live batch's
  own `[TURN]` lines (the foe faced last before each `ended (outcome=BattleOutcome.Lost)`), 145 Winona losses:
  **Skarmory 71, Altaria 64**, Pelipper 5, Tropius 4, Swablu 1; Juan 45: Kingdra 40, Crawdaunt 5. ⇒ the wall is
  recorded by IDENTITY now.
* **Design 1 excluded HM carriers** — the first observe-only run showed it excluded Sceptile (it knows Rock Smash).
* **Design 1's slot rule** refused Sceptile (four types, no status) and would have cost Blaziken Double Kick. Design 3:
  empty > status > strictly dominated > weakest non-STAB (`choose_slot`).
* Tate & Liza removed from scope (double battle — the turn record sees one foe).

## Fixtures (md5, verified at filing)

* `devon_scope_got.ss1` `2775e624d4c0f6a066b739ab8509f1a9` — ROUTE120 (13,16), badges 1-5, Torchic run: Ninjask,
  Blaziken#341D550A L39 [Scratch, Blaze Kick, Double Kick, Rock Smash], Mightyena, **Loudred#B2768B68 L31 [Pound, Uproar,
  Astonish, Stomp]**, Zigzagoon L3. Bag: TM34, TM39, TM50 ×1 each.
* `fortree_gym_wedge.ss1` `87d390d744741511ea6c6aee483f2214` (PINNED) — FORTREE_CITY_GYM (4,19), Treecko run: Mightyena,
  **Sceptile L39 [Rock Smash, Pursuit, Leaf Blade, Quick Attack]**, Swellow, Skitty L17, Zigzagoon L3, Castform L25.

## Predictions

| # | Drive | Prediction | Falsifier (the build is wrong if…) |
|---|---|---|---|
| P1 | `taught`, devon_scope_got, walls `Skarmory,Skarmory` | plan **TM34 Shock Wave → Loudred (pid b2768b68) replacing Pound**, coverage 3, drawback-free; outcome `taught`; Loudred = [Shock Wave, Uproar, Astonish, Stomp]; TM34 1→0, TM50/TM39 unchanged; every other mon unchanged; tripwire `BOSS_TRAINING_MODE`; OVERWORLD, no menu; a path to the Fortree gym door's front; < 12,000 frames | any other mon changes; a move other than Pound is lost; a TM other than TM34 is spent; a menu left open; the tripwire does not fire (the hook would be ending the preparation) |
| P2 | `taught`, fortree_gym_wedge, walls `Altaria,Altaria` | plan **TM39 Rock Tomb → Sceptile replacing Pursuit**, coverage 4, not drawback-free; Sceptile = [Rock Smash, Rock Tomb, Leaf Blade, Quick Attack]; TM39 1→0; the gates solve from the end tile to (15,3) | Rock Smash (HM) or Leaf Blade (STAB) lost; Quick Attack lost instead of Pursuit |
| P3 | `noteach` (`POKEBOT_GYMTM_FAULT_NOTEACH=1`), devon_scope_got, Skarmory×2 | planned TM34 → Loudred; `('Winona','TM34')` latched; outcome `planned, act skipped…`; NOTHING changes | anything taught, or no latch |
| P4 | `budget` (`POKEBOT_GYMTM_FAULT_BUDGET=600`), devon_scope_got, Skarmory×2 | `finished` False; most likely NOT taught (TM34 still 1, no move change) — if the 600 frames happen to cover the whole teach, `taught` with TM34 0 is also honest; either way OVERWORLD, no menu, a path to the gym | a menu left open; taught without a TM spent or a TM spent without the move |
| P5 | `noplan`, fortree_gym_wedge, Skarmory×2 (vacuity arm) | outcome `no plan`; reasons name "TM39 (Rock Tomb) is not super-effective on Skarmory"; nothing changes; < 2,000 frames | any teach on a fixture where no owned TM is 2x on the wall |
| P6 | `taught` pointed at P1's OWN END STATE (the grade's vacuity test) | **FAIL** — Loudred already has Shock Wave (2x on Skarmory) and Blaziken has Blaze Kick ⇒ `no plan`; `outcome_taught` False | a PASS (the grade would be measuring nothing) |

## Not measured here (stated so nobody reads the drives as more than they are)

* **Whether the taught move is USED against the wall** (the plan's acceptance). The driver stops before any battle.
  Live evidence = the next batch after the merge: a `[GYM_TM]` event with `outcome='taught'` followed, in the same run,
  by a `[TURN]` line `UseMove:<taught move>` against the wall species. Pre-registered metric: in runs with ≥1 taught
  event, the fraction whose later Winona battles contain such a line; and Winona conversion in runs that taught vs the
  4-lane baseline — ⚠ the batch cannot detect a small effect (the recon's expectation is ~1 of 4 Winona deaths).
* **The foe recorder filing a LOSS live.** The recorded value is the same `_foe` the `[TURN]` line prints (proven by the
  145 measured losses); the filing is gated (`probe_gymtm_teach.py` G1b). Live evidence = the batch's loss lines, which
  now end `last foe <species>`.
