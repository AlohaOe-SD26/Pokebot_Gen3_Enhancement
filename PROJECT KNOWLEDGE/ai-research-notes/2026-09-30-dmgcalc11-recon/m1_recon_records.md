> ⚠ **A NOTE, NOT A SOURCE OF TRUTH.** Output of one agent of the design v2 step 11 recon (2026-09-30, a workflow of five fresh Claude agents; decomp read at pret/pokeemerald f90719c4). The design that uses it is `../2026-09-30-dmgcalc11-DESIGN.md`, whose author re-read every load-bearing claim it relies on (marked ✔ there). Line numbers are as of branch `wt/dmgcalc11` at `241929d7`. Scratch scripts it mentions were not committed.

# M1 recon: RECORDS, RULINGS AND INSTRUMENTS (design v2 step 11)

Worktree read: `C:/Remote Projects/pokebot-wt-ch24` (branch `wt/dmgcalc11`), read-only. Decomp read with `gh api`
(pret/pokeemerald `master`, 2026-09-30). This is a NOTE for the step 11 design, not a source of truth. Everything I
did not read myself is marked UNVERIFIED. "PK/" = `PROJECT KNOWLEDGE/`; "v2" =
`PK/ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md`; "BAS" = `sandbox-pokebot/modules/battle_action_selection.py`.

---

## 0. The findings that matter most (ranked)

1. **Step 11 is MEASUREMENT ONLY, but the three KIs name it as their fix "vehicle". Nothing in 06 rules either way.**
   v2:569 ("measurement only"), PK/04-HANDOFF.md:384 and PK/03-PUNCH-LIST.md:123 ("MEASUREMENT only") vs
   PK/05-KNOWN-ISSUES.md:3107 (KI-109 "vehicle: design v2 step 11"), :3124 (KI-110 "Vehicle: v2 step 11"),
   :3137-3138 (KI-111 "Vehicle: v2 step 11, or a standalone item"). v2:573 asks M1a only to **pin** the Sonicboom/
   Psywave and BADGE07 findings. `grep` of 06 for KI-109/110/111, Sonicboom, Psywave, Solarbeam, BADGE07/08: **no user
   ruling, no "do not re-raise"**. Step 12 is deliberately built NOT to need the fix: stage 1 dispatches exact damage
   "on EFFECT and never on the calculator's names" (v2:624), with a NAMEDISPATCH fault (v2:646). ⇒ Recommend: keep 11
   measurement-only, pin the three as KNOWN-DIVERGENCE rows tagged by KI (so a later fix flips them), file the fix as
   its own item, and correct the three "vehicle" lines in the same commit (a P5-type pair otherwise).
2. **What step 12 stage 2 needs from M1 is more than a pass/fail.** v2:627-630 (stage 2 OFF "until M1b's
   acceptance"; `ub = ceil(W · crit_max · 1.10) + 3`), v2:723 (CALC_ERR 10 % and MARGIN 3 HP are "Judgements,
   re-derived from M1 and the batch"), v2:725 (acceptance: ≥300 clean samples, 0 over crit_max + 3 HP), v2:587 and
   v2:677 (the samples come from step 14, DMGAUDIT=1 in BOTH arms). ⇒ Step 11 ships the instrument; the acceptance
   verdict is a step-14 output. M1 must emit the per-effect distribution of (observed − crit_max) and
   observed / crit_max, so CALC_ERR and MARGIN can be re-derived. **`W` and "the whitelisted plain-hit family" are
   never defined in the tree** (grep of all `.md`: `ceil(W` appears once, v2:628); step 11 must define the whitelist
   by `move.effect`.
3. **"The foe faints → excluded" throws away the one observation weaken exists to prevent.** A faint is a CENSORED
   sample: damage ≥ hp_before. If hp_before > crit_max + MARGIN (after the other exclusions) it is a definite
   under-prediction. v2:577 excludes all faints. Recommend: log faints as censored and FAIL acceptance on
   `hp_before > crit_max + MARGIN`. This needs the foe's self-KO moves excluded (Explosion/Self-Destruct, Memento,
   Perish Song), which the list at v2:577-583 omits. **The fixture meets one:** Hideo's first Koffing knows
   Self-Destruct (decomp `src/data/trainer_parties.h:8670-8675`).
4. **The HP-rise rule does not catch an AI heal that the hit exceeds. The pinned fixture has one.** Marcel carries
   one Hyper Potion (`src/data/trainers.h:136+6`). The AI heals when `hp < maxHP/4` (`src/battle_ai_switch_items.c:870`),
   and items resolve before moves. In the e1ddc4e7 OFF run on post_mtpyre, Manectric reads **18/83 at TURN 1 and
   18/83 at TURN 2, with Take Down's PP 17→16** (executed): `tools/story-dev/evidence/2026-09-29-r27keyitems-A-OFF-r1.txt`
   lines f3191065 / f3191935. That is a heal to 83 then a ~65 HP hit, recorded as delta 0 (INFERRED from the decomp
   rule plus both runs' numbers). In the 4ea923a5 run the same fight reads 11 → 17 (a rise, so it would be caught):
   `evidence/2026-09-28-r20T-CONTROL.txt` f3189632 / f3190508. ⇒ the trainer stratum needs a real item-use read (or
   "the trainer still holds an item" as an exclusion); the rise rule alone is not enough.
5. **KI-108 makes `battle_state.current_turn` untrustworthy as a pairing key, and bans new `get_battle_state()`
   calls.** `BattleState.__eq__` omits `_current_turn` and the party order (`sandbox-pokebot/modules/battle_state.py:249-262`);
   the cache keeps the OLD object when old == new (`modules/state_cache.py:293-298`); PK/05-KNOWN-ISSUES.md:3066-3080.
   HP is inside the compared bytes, so HP reads are fresh; the turn number can be stale. And a new `get_battle_state()`
   call earlier in a frame makes later same-frame readers stale (KI-108 names BAS ~:803 and ~:1107 as correct only
   because each is the first caller in its frame). ⇒ DMGAUDIT reuses the handler's `battle_state` local and reads the
   turn counter raw (`gBattleResults+0x13`, decomp `include/battle.h:247`), or pairs on identity + PP.
6. **The [TURN] line is logged BEFORE the no-PP override and is not one line per turn.** [TURN] is emitted at
   BAS:534-538; the no-PP override that can change `index` runs after it (BAS:552-569). Decisions repeat within a
   turn (two `[TURN 0]` lines 19 frames apart at f3185424/f3185443 in the A-OFF-r1 evidence); the foe is always
   `opponent.left_battler` (BAS:455), so doubles print `vs ?`. ⇒ Emit the prediction after BAS:569 (instrument the
   action, CLAUDE.md rule 7), keep the LAST prediction per turn, and exclude doubles.
7. **Our own mon's state yields executed-looking zero samples.** `[Sleep] -> UseMove:Take Down(pp20)` repeats for 3
   turns with PP frozen (A-OFF-r1, f3185424-f3186797). The PP printed in `[TURN]` already discriminates "executed"
   (PP dropped) from "never ran" (sleep, freeze, full paralysis, flinch, confusion). Without it, zero samples pad the
   300 without testing anything (vacuity).
8. **Gates that will bite the implementation.** `probe_gymtm_teach.py` G1c EXECUTES the real `[TURN]` try body with
   SimpleNamespace stubs (:138-199); `repro_no_silent_except.py` holds BAS at 3 silent handlers (:293);
   `run_gates.py:45` passes the parent environment to every gate. ⇒ Put DMGAUDIT in its OWN try, give every `except`
   a `# noqa: BLE001 - <why>`, and never leave `POKEBOT_R25_DMGAUDIT` exported in a gate shell.
9. **The M1a stub trap.** `BattleStateSide.__contains__` returns `NotImplemented` for anything that is not a
   `BattlePokemon` (battle_state.py:370-377), and `bool(NotImplemented)` is True (PK/05:2746-2753). A stubbed
   DEFENDER is then "the player": it gets BADGE05 Def and **BADGE08 Sp.Def** boosts, which is KI-110's own branch
   (`_util.py:338-343`). M1a must build real `BattlePokemon` objects from 0x58-byte `gBattleMons` records. It must
   patch `modules.battle_strategies._util.get_event_flag` (imported by name at `_util.py:8`), and remember that
   `get_event_flag` returns False silently for an unknown name (`modules/memory.py:337-338`).
10. **A flag for DMGAUDIT contradicts an agent precedent. That is not a user ruling, but the step should say why.**
    06:7902-7917 rejected a flag for telemetry the batch needs ON in both arms ("just a way to forget it"). Step 14
    needs DMGAUDIT ON in both arms (v2:677), yet v2 flags it (v2:575). Also, reading the flag per call in BAS would be a
    THIRD exception to "read per run in `reset_per_run_state`". v2:151 lists exactly two and tells reviewers not to
    flag those. ⇒ State the third exception (the KI-93 census precedent, BAS:148-150), and add a `[DMGAUDIT] CTL` line
    so "flag forgotten" cannot read as "no samples" (the `[KI93-CTL]` precedent, BAS:168-171).

---

## 1. RECORDS AND RULINGS

### 1.1 What the spec says (v2 §Step 11, read in full)
- v2:569: "Step 11: M1, damage-calculator fidelity (measurement only). Parallel. It gates step 12's stage 2."
- v2:570-574 (M1a, pure): `tools/story-dev/probe_damage_calc_decomp.py`; port `CalculateBaseDamage`
  (`pokemon.c:3106-3372`), `Cmd_damagecalc`, `Cmd_typecalc`, `ApplyRandomDmgMultiplier`; report the MAXIMUM
  UNDER-prediction of `calculate_move_damage_range` (crit and non-crit) "for the whitelisted effects"; rows PIN the
  Sonicboom/Psywave name bug and the BADGE07 Sp. Def finding; fault: a synthetic row over crit_max + MARGIN must fail.
- v2:575-587 (M1b, live, observe-only): `POKEBOT_R25_DMGAUDIT=1`; its own `[DMGAUDIT]` line in its own category, never
  appended to `[TURN]`, never category `BATTLE` [A-S10]; per selected UseMove: predicted [min,max], crit_max, foe
  (PID, species), HP before, then (PID, species) and HP after at the next `[TURN]`; the exclusion list (below); an
  excluded sample is logged with its reason; `tools/story-dev/audit_damage_calc.py` summarises; acceptance ≥300
  clean samples with 0 over crit_max + MARGIN; inertness proof = a same-HEAD pair on `post_mtpyre.ss1`,
  `storyresume --frames 90000`, seeded, DMGAUDIT unset vs =1, every `[BATTLE]` line identical; `r20T-CONTROL` is NOT
  the control (recorded on `main 4ea923a5`, `evidence/2026-09-28-r20T-CONTROL.txt:2`); "The samples come from step
  14, with DMGAUDIT on in both arms."
- v2:588 "Does NOT show: fidelity for excluded effects or unmodelled abilities."
- Exclusions as listed (v2:577-583): foe faints; weather chip; foe poisoned/burned/toxic; foe knows a recoil, crash,
  drain, heal or Substitute move; a held item; Rough Skin; foe (PID, species) differs between reads; foe used a bag
  item that turn; end-of-turn effects on the foe (Leech Seed, Nightmare, Curse, the trapping moves); Wish and
  Ingrain; the foe is confused; any turn where the foe's HP ROSE; trainer samples as a separate stratum.
- Common rules that apply (v2:150-162): flag default OFF, read per run in `reset_per_run_state` with TWO stated
  exceptions [A-N6] (v2:151); a row in `29-DISABLED-FEATURES-REGISTRY.md` (v2:152); OFF byte-identical in every
  `[BATTLE]`/`[CATCH]`/`[ITEM]` line (v2:153); new log fields only with the flag ON (v2:154); predictions before any
  drive (v2:155); a named PINNED fixture with a computed discriminator, a skip-the-fix arm, a fault-tested gate
  (v2:156-159); adversarial review plus Tier 1 (v2:160); explicit-path commits (v2:161).
- The handoff adds the process (PK/04-HANDOFF.md:384): "a recon on different angles, predictions filed BEFORE the
  code, the code, the gate and its adversarial pass (timed against its suite timeout), the arms, the three-lens review."
- The v1 origin (PK/ai-research-notes/2026-09-28-r23-25-DESIGN.md:519-521): "Our damage calculator is not safe for a
  'cannot KO' test. It is wrong for whole move families: OHKO moves, multi-hit, Magnitude, Return, Flail and Counter
  (`_util.py:172`, `:230-242`). It has never been compared with observed in-game HP loss. Measurement M1 (logging
  predicted vs observed damage for every move our side uses) must come before any weakening."

### 1.2 Scope: is fixing KI-109/110/111 inside step 11? (the question asked)
**Record, verbatim positions:**
- Step 11 = "measurement only": v2:569; v2:23 ("measurement only; it gates step 12's stage 2"); PK/04-HANDOFF.md:384
  ("MEASUREMENT only"); PK/03-PUNCH-LIST.md:123 ("MEASUREMENT only").
- M1a "Rows pin" the bugs (v2:573): pin, not fix.
- The KIs say the opposite direction: KI-109 "**Fix direction** (vehicle: design v2 step 11, M1 damage-calculator
  fidelity)" (PK/05:3107); KI-110 "**Fix:** `BADGE08_GET` → `BADGE07_GET` at `:342`; optionally mirror the
  exceptions. Vehicle: v2 step 11." (PK/05:3124); KI-111 "Vehicle: v2 step 11, or a standalone item if it is wanted
  sooner." (PK/05:3137-3138).
- Step 0's verify note (PK/ai-research-notes/2026-09-29-v2step0-VERIFY.md:34-50) files them and says "A fix must match
  on `move.effect` AND return 0 on a 0 type product" (:39-40), but names no vehicle.
- **06 check (CLAUDE.md rule 11, done):** `grep -n -i` over 06 for weaken, damage calc, calculator,
  calculate_move_damage, `_util.py`, KI-109/110/111, sonic boom, psywave, solar beam, BADGE07, BADGE08, false swipe.
  Hits only at 06:4570-4612 (Torment; the 2026-09-06 "reuse the shipped formula" decision), 06:6517 (unrelated
  Waterfall badge), 06:8051-8053 and 06:8091-8097 (RULING 25 weaken). **No ruling on fixing the calculator, and no
  "do not re-raise"** attached to KI-109..111.

**Constraints that bear on a fix, whichever step does it:**
- It is an UPSTREAM divergence: "The upstream mirror and `custom-pokebot` carry the same code; a fix is a divergence to
  log." (PK/05:3112); PK/05:16-21 (UPSTREAM KIs live identically in the pristine mirror, "do not fix there").
- KI-111's fix edits `profiles/battle.yml`, "the user's file, so a divergence to log" (PK/05:3136-3137).
- `_util.py` is the every-battle hot path: 06:4555-4559 ("A defect that costs one fight does not justify a hurried
  change to the code path every battle depends on"); 06:4595-4598 ("the decisive test for a shared path is an A/B on
  the ORDINARY case"); CLAUDE.md SESSION DISCIPLINE rule 9.
- A KI-109 fix changes move choice (a live effect, PK/05:3093-3106) → a behaviour change → under v2's common rules
  it needs its own default-OFF flag and A/B. That cannot coexist with a "measurement only" step whose inertness proof
  is "every [BATTLE] line identical".
- KI-110 is dormant: "No caller computes damage aimed at our Pokémon (`defender_is_player` is never True)"
  (PK/05:3122). ⇒ **M1b (our attacks on the foe) can never observe KI-110**; only M1a can pin it.
- The post_mtpyre party (Mightyena, Sceptile, Swellow, Skitty, Zigzagoon, Castform; evidence
  `2026-09-28-r20T-CONTROL.txt` DUMP) uses no Sonicboom/Psywave/Solarbeam in the recorded runs, so the fixture could
  not discriminate a KI-109 fix anyway.
- Step 12 does not depend on the fix: stage 1 = exact-damage effects "dispatched on EFFECT and never on the
  calculator's names" (v2:624-626), NAMEDISPATCH fault (v2:646). Stage 2 uses crit_max from the calculator (v2:628)
  but only for the "whitelisted plain-hit family", which excludes the fixed-damage effects.

**Reading (mine):** step 11 is measurement; the KI fixes are a separate, flagged item with the M1a probe as their
gate. The three "Vehicle: v2 step 11" lines should be corrected in the same commit that files the plan. This is an
agent-level scoping choice with no user ruling behind it, so it does not need escalating (rule 11 checked).

### 1.3 USER RULINGS that constrain steps 11-12
- **RULING 25 (2026-09-28), 06:8045-8053:** cap 3 per species per run; "FUTURE DESIGN, to be DISCUSSED … weakening
  the target before catching it, done carefully. The design must account for indirect and self damage: weather,
  Spikes, and a target that knows Self-Destruct / Explosion, Double-Edge (recoil), Curse, or a weather move."
- **RULING 25 clarified (2026-09-29), 06:8090-8097:** user: "…we should implement that weaken to catch pokemon logic
  so it increases its catch rate…" ⇒ "WEAKEN-TO-CATCH IS TO BE BUILT, not only discussed. It carries the safety
  concerns RULING 25 named: weather, Spikes, Self-Destruct/Explosion, recoil, Curse, weather moves."
- **"⛔ Do not re-ask any of them"** (06:8025; 06:8059-8060): the three RULING 20 §8 questions and v1 §5's five.
  None of them is about the calculator; none restricts step 11. The note repeats this at v2:33.
- **RULING 27 (06:8100-8104):** no healing items in wild battles → step 12's "No healing items, ever" (v2:623).
  Irrelevant to M1.
- **Standing directive (CLAUDE.md, Gemini rules):** Gemini output is a note; the Claude validator reads the decomp.
  M1a's port must be decomp-cited, not recalled.
- **No user ruling found** on: fixing KI-109..111; the value of MARGIN/CALC_ERR; the 300-sample threshold; whether
  DMGAUDIT is flagged or always on. All are agent proposals (v2 §3 header: "all PROPOSALS for the user", v2:704).

### 1.4 Agent DECISIONS in 06 that constrain step 11
- **06:4606-4617 (2026-09-06): "score with `BattleStrategyUtil.calculate_move_damage_range`, not a hand-rolled …
  Rejected … a SECOND damage model in a codebase that already has one, guaranteed to drift from it."** ⇒ M1a's decomp
  port is a TEST ORACLE in `tools/`, never a production dependency. Step 12 must keep consuming the shipped
  calculator (v2:628 does). Promoting the port into production would need a new decision entry.
- **06:4631-4634:** promotion to `custom-pokebot/` is the user's call (applies if M1b's line is ever promoted).
- **06:4573-4604:** `get_strongest_move_against` returns an index into the COMPACTED list; "genuine index-space hazard".
  Relevant to DMGAUDIT: `BattlePokemon.moves` compacts empty slots (battle_state.py:519-533), and the move menu selects
  slot `index`. So for a moveset with a gap, `_me.moves[index]` (what [TURN] names, BAS:467) is not the slot the menu
  presses. v2:836 and v2:600 (weaken DEFERs on non-contiguous slots). ⇒ DMGAUDIT logs `contiguous=` or excludes.
- **06:7902-7917 (2026-09-28): step T telemetry ALWAYS ON; "Rejected: A flag, default off: the batch A/B would need it
  on in both arms anyway, so it is just a way to forget it."** Tension with v2:575, which flags DMGAUDIT although
  v2:677 needs it ON in both batch arms. Also "They were proven not to change a battle: 24 of 24 `[BATTLE]` lines are
  identical to a no-telemetry control" is the inertness-proof precedent.
- **06:8248-8272 (step 5):** "Graded A/Bs run their control more than once (KI-112)"; "Rejected … One control run".
- **06:8200-8227:** the readings v2 builds on; none concerns M1.

### 1.5 Mistakes / playbook rules that apply directly
- **08:10903-10945 "A DAMAGE CALCULATION BECAME A PUBLISHED CLAIM IN SIX FILES":** "⛔ NEVER WRITE 'MEASURED' OVER
  SOMETHING THAT WAS COMPUTED." ⇒ M1a numbers are CALCULATED (port vs calculator); only M1b's are MEASURED. The
  graded note must keep the two words apart.
- **08:22255-22267 "I SHIPPED A RECORDER THAT NEVER RAN, INSIDE A TRY THAT SWALLOWED THE PROOF":** "⛔ Code added
  inside a broad `try` must be proven to RUN — execute it once with the `except` removed." ⇒ DMGAUDIT needs a
  G1c-style execution row of its own.
- **08:15660-15680 (the `[TURN]` regex that dropped 13.5 % of rows, 7,620 of 56,339):** "WHEN YOU CORRECT A PARSER,
  RE-MEASURE ITS DENOMINATOR AGAINST THE RAW LINE COUNT." ⇒ `audit_damage_calc.py` must print raw `[DMGAUDIT]` line
  count vs parsed count and fail on a mismatch. Statused battlers print `[Sleep]`/`[Paralysis/Confused]` between HP
  and `->` (BAS:531).
- **14-AGENT-PLAYBOOK.md:160-165:** find the FIRST DIFFERENT LINE; compare every frame-stamped debug line.
- **14:166-172:** prove "OFF changes nothing" with a differential against the previous commit's module over a grid of
  states (16,128 states found R2 where every row and all seven live arms saw nothing).
- **14:173:** derive a row's expected line from the SPEC, never from the code's output ⇒ M1a expectations come from
  the decomp port, never from `_util`'s output.
- **14:175:** tabulate the input dimensions before writing rows.
- **CLAUDE.md SESSION DISCIPLINE rule 7:** instrument the ACTION. ⇒ predict for the index actually submitted.
- **Rule 3:** identity, not position ⇒ the foe by (PID, species), our mon by PID.
- **Rule 8:** identical output across runs is a determinism check, not a replication.

### 1.6 Exactly what step 12 stage 2 needs from M1
From v2 step 12 and §3:
1. **An acceptance verdict** on step 14's data: ≥300 clean samples, 0 over crit_max + 3 HP (v2:585, v2:725; "Before
   any stage-2 batch"). "⛔ It stays OFF in every batch until M1b's acceptance" (v2:630). Live L1/L2 "only after M1b"
   (v2:653).
2. **The numbers to re-derive CALC_ERR (10 %) and MARGIN (3 HP)** (v2:723, "Judgements, re-derived from M1 and the
   batch"): the per-effect max of (observed − crit_max) and max of observed / crit_max, per stratum (wild vs
   trainer). A pass/fail alone cannot re-derive them.
3. **The whitelist itself**, by `move.effect`: stage 2 admits "the whitelisted plain-hit family" (v2:627) and M1a
   reports "for the whitelisted effects" (v2:572); neither place enumerates it. `moves.json` carries decomp-style
   effect names (measured: HIT 24, HIGH_CRITICAL 8, *_HIT secondaries, QUICK_ATTACK, ALWAYS_HIT, RECOIL, PURSUIT,
   MULTI_HIT 12, …; 355 moves).
4. **M1a's maximum under-prediction per whitelisted effect** (crit and non-crit) (v2:572), which bounds crit_max's
   error independently of live sampling.
5. **The lower tail too** (my addition): stage 2's "Guaranteed progress must be ≥ 10 % of max HP" (v2:629) uses the
   calculator's MIN. M1 should report how often an EXECUTED hit lands below the non-crit min (the progress side),
   not only the safety side.
6. **A definition of W** (v2:628). Undefined in the tree; the only hint is the W-row list "the Swagger/Rain/Air Lock
   multipliers" (v2:638). Step 11's recon or the step 12 design must pin it.
7. **Deferred to after M1:** "whether to weaken shinies" (v2:700, v2:789).
8. The v1 "KO-safety" framing: step 12 "Does NOT show: KO-safety beyond M1b's sample" (v2:655). So M1b's sample IS
   the KO-safety evidence, which is why faint-censored samples (finding 3) matter.

### 1.7 Spec gaps found (for the step 11 design)
- **M1b's acceptance is not scoped to the whitelist.** v2:576 says "For the selected UseMove"; v1:521 said "every
  move our side uses". Multi-hit (MULTI_HIT, DOUBLE_HIT), fixed-damage (KI-109's Sonicboom scores ~1),
  power-varying (FLAIL, ERUPTION, Magnitude, Return, Rollout/Fury Cutter), two-turn and Pursuit-on-switch moves would
  exceed crit_max BY CONSTRUCTION and fail acceptance "for good". ⇒ Out-of-whitelist moves go to a logged stratum,
  not the acceptance set.
- **Missing exclusions** (each with a mechanism):
  - Foe self-KO or self-HP moves: Explosion/Self-Destruct (effect `EXPLOSION`), Memento, Perish Song, Pain Split
    (can RAISE or lower its HP), Belly Drum, Ghost-type Curse (user loses 1/2).
  - Damage suppression: Protect/Detect, Endure (floors at 1).
  - Mid-turn boosts to OUR attack before we move, if the foe is faster: Swagger (+2 Atk), Flatter (+2 SpAtk). These
    push damage past crit_max by construction.
  - Our own mon can't act: sleep, freeze, full paralysis, flinch, confusion, Truant, recharge. Detect by PP delta.
  - A turn GAP: our battler is locked (Rollout, Thrash/Outrage/Petal Dance, Uproar, Bide, two-turn charge, recharge),
    so selection is skipped and the next decision covers two turns. Require after_turn == pred_turn + 1 (read raw;
    see KI-108).
  - Status applied DURING the turn: our Poison Point/Flame Body/Static, or a BURN_HIT/POISON_HIT secondary, causes
    end-of-turn damage the same turn. Check poison/burn/confusion/Leech Seed/trap at the AFTER read, not only before.
    Likewise weather at both reads, since the foe may set sandstorm or hail that turn.
  - Our Liquid Ooze (the foe's drain hurts it) and Rough Skin (listed). Our Flash Fire boost, Mud Sport, Water Sport,
    Helping Hand and Cloud Nine/Air Lock are `todo`s in the calculator (`_util.py:240`, `:402-406`, `:497`, `:518`).
  - Doubles: the foe on `[TURN]` is `opponent.left_battler` (BAS:455), and a partner may hit the same target. The
    fixture meets three doubles (see 2.5).
- **Faints as censored samples** (finding 3).
- **The CALC_ERR asymmetry:** stage 2 applies ×1.10 **and** +3 (v2:628), but M1b accepts at crit_max + 3 without the
  1.10 (v2:725). The acceptance is stricter than what stage 2 assumes, which is conservative. Say so, so no one
  "harmonises" it the wrong way.

### 1.8 Doc staleness noticed (outside the step, flagged only)
- PK/03-PUNCH-LIST.md:123 still says (in its RULING 25 recap) "weakening before catching is for a later discussion".
  06:8096 (2026-09-29) supersedes that. It may read as dated history; a staleness sweep should decide.
- The three KI "vehicle" lines (1.2) disagree with "measurement only".

---

## 2. INSTRUMENTS

### 2.1 The `[TURN]` battle line (BAS:436-540)
- Built inside ONE `try` (BAS:447-540), whose `except` swallows everything (BAS:539-540, `# noqa: BLE001 -
  instrumentation must never affect the battle`).
- `_me` = `own_side.left_battler` (battler 0) or `right_battler` (BAS:450-454). **`_foe` = `opponent.left_battler`
  ALWAYS** (BAS:455): in doubles, `UseMoveAgainstRightSideOpponent` still prints the LEFT foe, or `vs ?` when it is
  absent. Evidence: `vs ?` on every right-side decision in `evidence/2026-09-28-r20T-CONTROL.txt` (f3154071 ff).
- `_what` = action name plus `:<move>(pp<n>)` from `_me.moves[index]` (BAS:456-470), a COMPACTED list
  (battle_state.py:519-533).
- USER RULING 19's recorder writes `TURN_FOE["species"]` and appends `(our_pid, our_species, _what, foe_species)` to a
  bounded, module-level log (BAS:57-61, :480-487). It must stay below `_what` (BAS:476-479, the 2026-09-26 bug).
- `_describe(mon)` = `Species L<lv> <hp>/<max>` plus ` [status]` only when non-empty (BAS:521-532);
  `_status_of` = permanent + temporary status (BAS:489-519).
- Emitted as `debug_logger.event(f"[TURN {battle_state.current_turn}] {me} -> {what}  vs {foe}",
  category="BATTLE")` (BAS:534-538). **Two spaces before `vs`.** On disk: `f<frame> [BATTLE] [TURN n] …`.
- `current_turn` = `gBattleResults` offset 0x13 (battle_state.py:822), which is `battleTurnCounter` (decomp
  `include/battle.h:247`).
- What it does NOT carry: the foe's PID; the foe's held item, ability or moves; weather; whether our move executed;
  the target in doubles. **What it does carry, usefully: our slot's PP at decision time.** A PP drop by the next
  decision means the move executed (a miss still spends PP; sleep, full paralysis, flinch and confusion do not).
  Seen live: A-OFF-r1 f3185424-f3186797, `[Sleep]`, pp20 three turns running, then pp19 at f3187577.
- **Ordering hazards:**
  - (a) `[TURN]` is logged BEFORE the no-PP override, which may rewrite `index` (BAS:552-569). A prediction taken at
    `[TURN]` can name a move that is not submitted.
  - (b) The Manual-mode `yield; continue` sits between them (BAS:542-544).
  - (c) The handler is re-entered within one selection episode, measured 5 times in a Torment episode (BAS:26-30).
    `[TURN n]` lines repeat with the same n (A-OFF-r1 f3185424/f3185443; r20T-CONTROL f3149591/f3149618).
  - (d) `battle_state` is read once at entry (BAS:115) and refreshed only when the battler index changes
    (BAS:574-576).
- ⇒ **Placement for DMGAUDIT:** after BAS:569, before `match action` (BAS:578). Use `index` and `battle_state` as
  they will be ACTED on. It gets its own `try`, not the `[TURN]` try: G1c (2.7) runs that body with stubs, and an
  exception there would kill `[TURN]` (08:22255). Keep pending state module-level, like `_ki93_*` (BAS:23-42), because
  function locals die on re-entry. Key it by our PID and the foe's (PID, species) plus a raw turn read, not by
  "the next line".

### 2.2 KI-108 and the battle-state cache (why DMGAUDIT must add no cached reads)
- `get_battle_state()` returns the cached object if `age_in_frames == 0`; otherwise it builds, assigns to the cache,
  and returns the NEW object (battle_state.py:808-827). The setter keeps the OLD object when `old == new`
  (state_cache.py:293-298), and `__eq__` omits `_battler_party_order` and `_current_turn` (battle_state.py:249-262).
  PK/05:3066-3080 (KI-108, OPEN).
- Consequences for M1b:
  - (i) HP, PP, status, stat stages, held item and moves live in `_battler` (the 0x58-byte `gBattleMons` records),
    which `__eq__` compares, so those reads are FRESH.
  - (ii) `current_turn` can be STALE. Do not pair on it alone; read `gBattleResults+0x13` raw via `read_symbol` (a
    raw read bypasses the cache).
  - (iii) Do not add a `get_battle_state()` call: a new earlier caller in a frame makes later same-frame callers
    stale. KI-108 lists BAS ~:803 (KI-96 re-map) and ~:1107 (KI-101 item target) as correct "ONLY because each happens
    to be the first caller in its frame".
  - (iv) No per-frame hook: v2:835, "Observe must stay byte-identical (no `random`, no extra reads)".
- `calculate_move_damage_range` itself takes the state it is given (`BattleStrategyUtil(battle_state)`,
  `_util.py:41-42`). Its only other reads are `get_event_flag` (`_util.py:336-342`, a save-block read,
  memory.py:336-343). No `random`, no cache writes (read in full: `_util.py:165-242`, `:296-520`).

### 2.3 debug_logger categories (for a new `[DMGAUDIT]` category)
- `debug_logger.event(message, *, category="STORY")` writes `f<frame> [<category>] <message>`; it is a no-op when
  logging is off (`sandbox-pokebot/modules/debug_logger.py:332-338`). A category is a free string with no registry.
  ⇒ `category="DMGAUDIT"` gives `f<fc> [DMGAUDIT] <msg>`. Do NOT also start the message with `[DMGAUDIT]` (it would
  print twice). `[TURN …]` is the message prefix inside category BATTLE, which is why `[BATTLE] [TURN n]` appears.
- ‼ `.event`, never `.log` (`.log` does not exist; three KI-93 verdicts were void, BAS:157-158).
- Byte cap: `_MAX_BYTES = 30 MB` per log, shared by all categories. Past it, events are dropped with one marker line
  (debug_logger.py:44, :463-470). A 90k-frame pair is far below it. For step 14's long runs, DMGAUDIT adds bytes to
  BOTH arms. **UNVERIFIED whether any batch log approaches 30 MB** (no "size cap reached" hit anywhere in the tree).
  The auditor should fail if the marker is present.
- The header: `env-all:` lists every `POKEBOT_*` by prefix (debug_logger.py:260-268), so the arm's flag is
  self-recorded. `_BEHAVIOUR_ENV_VARS` (:172) is only for behaviour flags; DMGAUDIT does not belong there.
- ⚠ **In a worktree the header cannot name the build.** `_git_facts` requires `.git` to be a DIRECTORY
  (debug_logger.py:141-146), and a worktree's `.git` is a file (`gitdir: …/worktrees/pokebot-wt-ch24`), so every
  worktree log reads `build: not a git checkout` (e.g. `evidence/2026-09-28-r20T-CONTROL.txt` header). ⇒ The
  "same-HEAD" claim must be written into the evidence header by the runner ("code = commit X (runner verified HEAD,
  clean tree)", as `evidence/2026-09-28-r20T-T-ARM.txt:2` does).

### 2.4 The harness: `storyresume` and the seeded-run convention
- `--driver storyresume` = the PRODUCTION `StoryMode()` on the loaded save (tools/story-dev/story_harness.py:29114-29132).
  It inherits `handles_battle_faults`; bound it with `--frames`. Optional presets: `STORYRESUME_PRESET_DEFEATS`,
  `STORYRESUME_PRESET_ATTEMPTS` (:29133-29179), not needed here.
- Seeding: the wrapper `W="import random,runpy,sys; random.seed(1); sys.argv=['story_harness.py']+sys.argv[1:];
  runpy.run_path('story_harness.py', run_name='__main__')"`, run as `PYTHONUTF8=1 py -3.12 -c "$W" <save> --driver
  storyresume --frames N --profile <p> --log <x>` from `tools/story-dev` (PK/04-HANDOFF.md:672-675).
- **Where the lines land:** `[BATTLE]`/`[TURN]`/category lines go to `profiles/<profile>/debug-logs/Story-debug-<ts>.log`
  (the harness enables it at story_harness.py:28316-28324). The harness's `--log` file carries only `log()` output
  (story_harness.py:29347-29350: "the harness `--log` file is written by `log()` alone"). Use distinct `--profile`
  per arm. The default `--log` name is unique per run (story_harness.py:55-71).
- **A driver cannot see mid-battle state from its own generator.** It resumes only after the battle ends
  (`tools/story-dev/probe_ghost_damage_real.py` docstring). ⇒ M1b must live in battle code (BAS), never in a driver.
- **KI-112:** the harness is NOT frame-deterministic. 1 of 3 identical seeded `storyresume` runs arrived one frame late
  at a warp and diverged (PK/05:3140-3154). ⇒ run each arm at least twice (06:8260).

### 2.5 The pinned fixture `saves/post_mtpyre.ss1` and what a 90,000-frame storyresume meets
- Pin: `tools/story-dev/saves/FIXTURES.md5:27` `80602159694bf6e95ca0e698481a4cc9 post_mtpyre.ss1 PINNED Ch15 build
  anchor. Badges 1-6, Magma Emblem held, MT_PYRE_STATE=1.` The worktree file's md5 matches (measured,
  `md5sum` = `80602159…4cc9`).
- Start state (DUMP in `evidence/2026-09-28-r20T-CONTROL.txt`): Mt. Pyre, f3143340; party Mightyena L42 0/124,
  Sceptile L42 21/117, Swellow L39 18/109, Skitty L17 0/45, Zigzagoon L3, Castform L35 0/100.
- Prior runs from this fixture (all `storyresume --frames 90000`, seed 1 unless noted):
  `2026-09-28-r20T-CONTROL.txt` (main 4ea923a5), `2026-09-28-r20T-T-ARM.txt` (174e8335),
  `2026-09-29-r27keyitems-A-OFF-r1/-r2.txt`, `-A-ON-r1/-r2.txt` (e1ddc4e7), `2026-09-29-r27keyitems-M0-liveA.txt`
  (7dcd69fd; two identical runs over 205 tracked lines), `2026-09-29-r24catchhurt-M0.txt` (120k frames,
  `--set-balls 30`). **The trajectory differs by HEAD** (4ea923a5 vs e1ddc4e7 differ from Route 119 on), so predictions
  must re-measure at the step's own base (v2:853).
- **Battles met (e1ddc4e7 OFF run, tabulated by me from A-OFF-r1; 59 raw `[TURN]` lines, 59 parsed):**

| start | opponent (decomp id) | type | our UseMove turns | notes for M1b |
|---|---|---|---|---|
| f3144418, f3146795 | wild Shuppet | single | 0 | RunAway |
| f3148510 | Kindra 106 + Ed 13 (HEX_MANIAC+COLLECTOR) | **DOUBLE** | 4 | Pursuit, Wing Attack, right-side `vs ?` |
| f3156846 | Fernando_1 195 + Alberto 12 | **DOUBLE** | 4 | Slam, Quick Attack, Tackle, Wing Attack |
| f3168023 | Jacki_1 249 + Fredrick 29 | **DOUBLE** | 2 | LOST; Surf (spread move) |
| f3172378 | Hideo 651 (NINJA_BOY) | single | 2 | Bite vs Koffing. **Koffing #1 knows SELF_DESTRUCT** (`trainer_parties.h:8670-8675`); `.items = {}` (`trainers.h:7816+6`) |
| f3184504 | Vanessa 300 (POKéFAN) | single | 4 | Take Down vs Pikachu; **Pikachu holds an Oran Berry** (`trainer_parties.h:3983-3989`); **our Mightyena [Sleep] 3 turns, PP frozen** |
| f3189301 | Marcel 11 (COOLTRAINER) | single | 4 | Manectric/Shiftry; **1 Hyper Potion** (`trainers.h:136+6`); the 18→18 masked heal (finding 4) |
| f3195397 | Cristin_1 767 (COOLTRAINER) | single | 3 | Loudred/Vigoroth; **1 Hyper Potion** (`trainers.h:9208+6`); Vigoroth `[Uproar/MultipleTurns]` |
| f3207367 | wild Poochyena | single | 1 | KO |
| f3209384 | wild Shuppet | single | 1 | Bite (Dark vs Ghost) |
| f3215934 | wild Linoone | single | 2 | 82→8 then KO |
| f3228351 | wild Geodude | single | 0 | caught (UseItem) |
| f3231535 | Grunt Magma Hideout 2 717 | single | 1 | `.items = {}` (`trainers.h:8608+6`) |

  ⇒ About 18 singles UseMove turns and 10 doubles turns. Most singles are excluded (held item, AI item, sleep,
  faints, identity change). The fixture is a good **inertness and non-vacuity** fixture: it exercises doubles, held
  items, AI items, sleep, faint and switch-in paths, and it must emit `[DMGAUDIT]` lines in the ON arm. It is **not**
  an acceptance source (v2:587 already says the samples come from step 14).
- Trainer ids from decomp `include/constants/opponents.h`: MARCEL 11 (:15), CRISTIN_1 767 (:771), VANESSA 300 (:304),
  HIDEO 651 (:655), GRUNT_MAGMA_HIDEOUT_2 717 (:721), KINDRA 106, ED 13, FERNANDO_1 195, ALBERTO 12, JACKI_1 249,
  FREDRICK 29.

### 2.6 Registering the flag (29 + lint_docs R6)
- `PK/29-DISABLED-FEATURES-REGISTRY.md:3-4`: "Every `POKEBOT_*` environment flag in the bot code must appear here.
  `lint_docs.py` fails if one does not". Add the row "in the same commit" (the HOW TO USE section).
- **R6, forward** (`tools/story-dev/lint_docs.py:255-320`): ANY quoted `POKEBOT_*` literal (`flag_re`, :274) in
  `sandbox-pokebot/{modules,plugins}`, `custom-pokebot/{modules,plugins}`, `tools/story-dev` (not `evidence/`,
  :300) and both `pokebot.py` must appear (substring) in 29. ⇒ Every fault env in `probe_damage_calc_decomp.py` or
  `audit_damage_calc.py` needs a row too.
- **R6, reverse** (:322-334): every BACKTICKED `POKEBOT_*` in 29 must be read by code, or R6 fails as an orphan. ⇒
  Never add a 29 row before the code lands. Predictions notes in `ai-research-notes/` are fine, since R6 reads only
  29 for the reverse check. Today 29 has no `R25_DMGAUDIT` or `WEAKEN` row (grep).
- Row precedent for an observe-only census in BAS: `POKEBOT_KI93_CENSUS` / `POKEBOT_KI96_CENSUS`, "OBSERVE-ONLY …
  **Changes no behaviour.**" (29:238-239).

### 2.7 Existing gates that touch `_util.py` or battle logging
- **`probe_gymtm_teach.py` (run_gates.py:243):**
  - G1b (:119-125) finds, by AST, the `ast.Try` whose source contains `TURN_FOE["species"] = `,
    `TURN_FOE["log"].append(`, `[TURN ` and `TURN_FOE_LOG_MAX`.
  - G1c (:138-199) EXTRACTS that try body, execs it as `_turn_body(battle_state, action, index, battler_index)` with
    SimpleNamespace stubs (no stats, ability or types), and checks it does not raise, appends one decision, and still
    emits `[TURN 3] … Shock Wave … Skarmory`.
  - ⇒ DMGAUDIT code inside that try, run with `POKEBOT_R25_DMGAUDIT=1` in the gate's environment, would reach
    `calculate_move_damage_range` on stubs and could redden G1c. `run_gates.py:45`,
    `_GATE_ENV = {**os.environ, …}`, passes the parent shell's env to every gate.
- **`repro_no_silent_except.py` (run_gates.py:122):** scans `modules/battle_strategies`, `modules/battle_action_selection.py`, …
  (:65-); per-root ratchet `"modules/battle_strategies": 4`, `"modules/battle_action_selection.py": 3` (:290-293).
  Every new `except` must re-raise, log, or carry `# noqa: BLE001` with prose. A bare `pass` without it is a red suite.
- **`probe_faint_chooser_rank.py` (run_gates.py:481):** the ranker is pure, with an INJECTED damage function, so it
  never touches `_util` (06:4618-4629, "the probe therefore does NOT test the integration with the real formula").
  The live `[FAINT-CHOOSER] … metric=damage estimates_ok=N estimates_failed=0` lines are the only runtime check that
  `calculate_move_damage_range` runs on live objects. The fixture run shows `estimates_ok=4`/`=13`, `failed=0`
  (r20T-CONTROL f3170516, f3197298).
- `probe_dex_catch_nofaintbail.py:163`, `probe_dexcatch_bail.py:146`: stub `get_strongest_move_against`. Unaffected by
  a measurement-only step.
- `repro_flee_trap_delegate.py:46` imports `_util`; `repro_ki90_absent_left_slot.py` drives the real
  `battle_action_use_move` (:17, :112, :185, :291). A change to BAS placement must keep it green.
- `probe_ghost_damage_real.py`: calls the REAL calculator on a live in-battle save (`in_phoebe_battle_L75.ss1`). It
  is **not in run_gates**, and that save is **not in FIXTURES.md5** (grep: only `ki90_double_absent_seed.ss1` and
  `grind_stall_ppzero.ss1` are pinned in-battle-ish saves). A precedent for an M1a row set built from real
  `gBattleMons` bytes.
- **run_gates mechanics:** `GATES: list[tuple[str, bool]]` (run_gates.py:104), `(name, slow)`, ordinals
  APPEND-ONLY (:80-82). `TIMEOUT_FAST = 300` s, `TIMEOUT_SLOW = 900` s (:51, :60); a timeout is exit 124 = FAIL.
  Today: 136 gates, 122 fast (parsed via AST). Adding `("probe_damage_calc_decomp.py", False)` changes the count;
  `audit_doc_consistency.py` C1 (:16-17, :146-153) fails any current-state doc quoting a stale gate count. No doc in
  04/02 quotes one today (grep).

### 2.8 A stronger inertness recipe (derived from the records above)
1. Same HEAD, both arms from the SAME commit; the runner writes `git rev-parse HEAD` and "clean tree" into each
   evidence header (the log cannot, 2.3).
2. `post_mtpyre.ss1` (md5 asserted, e.g. `verify_fixtures.py --assert post_mtpyre.ss1=80602159694b`, the usage at
   story_harness.py:4710), W wrapper, `--frames 90000`, distinct `--profile`, **no** `--set-balls`.
3. **At least 2 runs per arm** (KI-112; 06:8260).
4. Compare **every frame-stamped line except `[DMGAUDIT]`** and report the first difference (14:160-165), not only
   `[BATTLE]`.
5. Non-vacuity: the ON arm must contain a `[DMGAUDIT] CTL` line and ≥1 prediction line, ≥1 doubles-exclusion line
   (Route 123) and ≥1 held-item or AI-item exclusion (Vanessa/Marcel/Cristin). Otherwise the pair proves only that
   code which never ran changed nothing.
6. An offline differential: old vs new BAS module with DMGAUDIT unset, over a grid of fake states (14:166-172).
7. G1c-style execution of the new try body with the `except` removed (08:22255-22267).

### 2.9 Decomp symbols available but unread by our code (options, all UNVERIFIED live)
- `sandbox-pokebot/modules/data/symbols/pokeemerald.sym`: `gBattleMoveDamage` (:131), `gHpDealt` (:132),
  `gCritMultiplier` (:142), `gChosenActionByBattler` (:146), `gLastLandedMoves` (:151), `gMoveResultFlags` (:157),
  `gProtectStructs` (:171), `gSpecialStatuses` (:172), `gBattleResources` (:184), `gBattleResults` (:951,
  0x03005d10). A grep of `sandbox-pokebot` `*.py` finds NO reader of any of the first nine.
- `gBattleResults.lastUsedMovePlayer` (+0x22) / `.lastUsedMoveOpponent` (+0x24) (`include/battle.h`, the struct at
  ~:234-258) are written in `HandleAction_UseMove` whenever a living battler starts a move
  (`src/battle_util.c:140-146`), before the attack canceler. So an after-read of +0x24 names the foe's attempted move
  that turn (a heal, a self-KO, Swagger). It stays stale if the foe used an item or switched, so it cannot detect
  item use alone.
- AI item use clears the slot: `gBattleResources->battleHistory->trainerItems[i] = ITEM_NONE`
  (`src/battle_ai_switch_items.c:938`). A before/after read of that array (pointer deref, UNVERIFIED offsets) would
  detect finding 4's masked heal deterministically.
- The transient per-move values (`gCritMultiplier`, `gMoveResultFlags`, `gHpDealt`) are overwritten by the next move
  in the same turn; reading them needs a per-frame hook, which conflicts with v2:835. Not recommended for step 11.

---

## 3. UNVERIFIED / not read
- `ShouldSwitch` / `AI_TrySwitchOrUseItem` line numbers cited by v2:578-579 (`:429`, `:528`, `:541`, `:866`):
  `AI_TrySwitchOrUseItem` is at `battle_ai_switch_items.c:528` (confirmed), and the HEAL_HP rule is at `:870` (v2
  says `:866`, 4 lines off). `:429`/`:541` not checked.
- The timing of `gChosenActionByBattler[1]` relative to our decision; the offsets of
  `gBattleResources->battleHistory`.
- Whether a pure M1a can load `modules.pokemon` data (types, species, moves) without a ROM. `probe_ghost_damage_real.py`
  boots a profile, ROM and emulator.
- Batch log sizes vs the 30 MB cap.
- The masked heal in finding 4 is inferred (decomp rule + two runs' numbers). No battle message was logged.
- The damage-formula port itself (other recon angles).
