# 2026-09-30 — design v2 step 12 (W, weaken-to-catch, RULING 25): the DESIGN, after a five-angle recon and a three-lens review

⚠ **A NOTE, not a source of truth.** It supersedes v2's §Step 12 (`2026-09-29-r23-27-DESIGN-v2.md` :595-666) where they
differ. Recon reports (each a NOTE): `2026-09-30-weaken12-recon/w12_recon_{decomp,ourcode,fixture,adversary,gemini}.md`.
Tags: [R:ADV-B2] = the adversary's finding B2; [R:DEC-H5] = the decomp report's H5; [R:OUR-3.6], [R:FIX], [R:GEM-7].

⛔ **THE HEADLINE CARRIES THE CAVEAT: STAGE 1 WILL ALMOST NEVER ACT IN A REAL RUN.**
- Across all 66 fixture rows, no party lead holds an exact-damage, sleep or paralysis move. The one stage-1 move
  anywhere is Sing, on a Skitty that sits in slot 3 and never leads [R:FIX].
- The story's leads are Sceptile, Mightyena, Swellow and Mudkip/Marshtomp, and none of them learns such a move
  before the League (INFERRED from their level-up lists).
- So what really weakens a target is STAGE 2: plain hits, bounded by the calculator. Stage 2 stays OFF, because step
  11 MEASURED the calculator and did NOT clear it (8 of 300 hits).
- Step 12 therefore builds the SAFE, GATED MACHINERY. Its live value arrives when stage 2 is cleared: by step 14's
  batch with `POKEBOT_R25_DMGAUDIT=1`, or by `#27-dmgcalcfix` plus the user's ACCEPT_MARGIN ruling.
- Proving stage 1 live takes a TEST lever (D8 below). Natural play will not exercise it.

## WHAT THE RECON CHANGED (each verified by the author at its line before it is used here)

- **✔ The game can run a move the module did NOT choose** [R:ADV-B2, DEC-M1, OUR-3.5]:
  - With an Encore on us, choosing Fight runs the encored move (`battle_main.c:4192-4196`).
  - Torment, Disable, Taunt, Imprison and a Choice item refuse a pick. Our KI-93 re-pick and NoPP override then take
    the first slot with PP (BAS:391-418, :555-572), and neither checks any weaken bound.
  - Also: our `encored_move` reader has the wrong offset (BS:730 reads 0x04; the decomp's `encoredMove` is 0x06,
    `include/battle.h:73-74`), and upstream has the same bug.
- **The hazards REPEAT on every throw turn,** not once [R:ADV-S2, DEC-M4]:
  - recoil, on every use;
  - Ghost Curse, once per our active mon;
  - weather chip, each end of turn;
  - Struggle's recoil ignores Rock Head (`battle_scripts_1.s:3939-3940`).
  - So a per-turn numeric floor protects one turn out of an unbounded number of throw turns.
- **Belly Drum cuts the target's HP by max/2 BEFORE our hit when it moves first** [R:GEM-1]. It needs hp > max/2, which
  is exactly the "damage above 50%" window.
- **Exact-damage moves run `typecalc`** [R:DEC-D2]:
  - Ghost is immune to Seismic Toss, Sonicboom and Super Fang (unless Foresight is on the target);
  - Normal is immune to Night Shade;
  - Wonder Guard blocks each of them unless the result is super-effective (Night Shade vs Shedinja
    passes; Shedinja's 1 max HP then fails hp − X ≥ 1).
  - Our calculator returns the fixed value anyway (U:204-228).
- **Status** [R:DEC-S2..S5]:
  - Sleep has no `typecalc`, so there is no Grass or Electric immunity in Gen 3.
  - Uproar (any battler) blocks sleep.
  - A target that already has any status cannot get another.
  - Synchronize reflects paralysis (never sleep) onto us.
- **A semi-invulnerable target or a Substitute does not block a BALL** (`battle_script_commands.c:9905-10050`, no test).
  So such a target is THROW-ONLY, never DEFER: a DEFER hands the turn to the parent's status chooser (CS:50-60), which
  checks neither [R:ADV-N1].
- **There are no wild double battles in Emerald** [R:DEC-H8, GEM-12]. The double check stays anyway, as a guard.
- **Our code** [R:OUR]:
  - No constructor takes a `weaken=` argument, and gates pin the three construction lines and `_r20_catch_start`'s
    position (`probe_dexcatch_bail.py:78-87`, `probe_r20_telemetry.py:257-290`).
  - `BattlePokemon.moves` compacts empty slots.
  - `.ability` is the SPECIES ability; the live byte is `ability_n` (Trace) [R:ADV-S8].
  - `[TURN]` is logged in category BATTLE.
  - `decide_turn` can run more than once per turn.
- **There are three catch-chance implementations, and the float one exceeds 1 above odds 254** [R:DEC, ADV-N8].
- **The author's own checks** (pret/pokeemerald master, 2026-09-30, and our code at `cdb49f83`):
  - `battle_main.c:4192-4198`: with an Encore, the encored move is forced.
  - `include/battle.h:70-80` puts `encoredMove` at 0x06; `battle_state.py:729-730` reads 0x04.
  - `battle_scripts_1.s:3939-3940`: Struggle jumps past the Rock Head check.
  - `battle_script_commands.c:8792-8796`: Belly Drum needs hp > max/2 and costs max/2.
  - `battle_scripts_1.s:814`, `:824`, `:1200`, `:1725`: `typecalc` in all four exact-damage scripts.
  - `battle_script_commands.c:9915-9926`: the ball throw blocks only trainer and Wally battles. Three agents agree
    that there is no later Substitute or semi-invulnerable test.
  - `story_mode.py:85-93`: the adapter site.
  - `battle_action_selection.py:405-418`: the KI-93 re-pick takes the first slot with PP.
  - The remaining recon claims are cited as the recon's, not the author's.

## THE DESIGN (D1-D15; revised after the design review; each also a `06` decision when built)

- **D1. Scope and flags.**
  - `POKEBOT_R25_WEAKEN` ∈ {unset, `observe`, `1`}.
  - `POKEBOT_R25_WEAKEN_CALC` ∈ {unset, `1`} (stage 2; meaningful only with WEAKEN set).
  - `POKEBOT_R25_WEAKEN_KINDS` defaults to `dex,team`.
  - All default OFF, each read once per run in `reset_per_run_state`, each with a `29` row.
  - Stage 2 is BUILT here, so its `observe` verdicts can be measured live. It stays OFF in every acting arm and batch
    until M1b's acceptance.
- **D2. The kind comes from the mode; the TARGET is identified by PID. No construction site changes.**
  - The adapter reads `context.bot_mode_instance._catch_ctx`, which `_r20_catch_start` fills on the line before each
    catch strategy is returned (SM:6446-6467).
  - It acts only if `ctx["kind"]` is in scope AND `ctx["sp"]` names the opponent's species at the battle's FIRST
    decision. At that decision the adapter stores the opponent's PERSONALITY (PID) on the strategy instance.
  - Later decisions:
    - a PID mismatch → DEFER;
    - the same PID with a different species (Transform) → THROW-ONLY [review safety F2, mechanics B2; rule 3:
      identity, never position].
  - Rejected: a `weaken=` constructor argument. It would rewrite three construction lines that four existing gates
    pin, and the harness and gates build instances without `__init__` [R:OUR-3.1-3.3].
  - Shiny never reaches the adapter (SM:251-275 calls `CatchStrategy.decide_turn` directly); a row pins that.
- **D3. The pure module `sandbox-pokebot/modules/story/weaken_catch.py`** (no emulator, no `random`).
  - Frozen snapshots: WTarget, WSelf, WParty, WEnv. They include:
    - the raw move slots with PP;
    - the LIVE ability bytes mapped to names;
    - the disable-struct fields (the Encore move at 0x06 and its timer, Disable, Taunt), our Torment, the target's
      Imprison-others;
    - both status2/status3, the side status and the Safeguard timer;
    - weather plus Cloud Nine/Air Lock, the battle-type flags, Uproar on any battler, and the target's held item;
    - EVERY party member able to battle (their live abilities, for the retaliation clause);
    - the turn counter, from a pure read of `gBattleResults` + 0x13, never from a cached `BattleState` (KI-108)
      [review F8, LP10].
  - `catch_p` is exactly `battle_script_commands.c:9987-10028`, with odds > 254 giving 1.0 and the full ball table
    ([R:DEC-C1, C3]; Net Ball uses the LIVE types).
  - `decide_weaken_turn(...)` returns one of {DAMAGE(slot), STATUS(slot), THROW, DEFER} plus a reason.
- **D4. The order of checks** (the first match wins; v2's order, damage BEFORE status [review mechanics N1: damage is
  lasting, sleep wears off]).
  - **DEFER:**
    - the flag is off, or the kind is out of scope, or the context or PID does not match;
    - the battle is not a single wild battle: trainer, safari, double, roamer, any legendary or Regi/Kyogre/Groudon/
      Rayquaza flag, Pyramid or Pike [R:ADV-S7];
    - any read failed;
    - our item is a Choice item.
  - **THROW** is always `TurnAction.use_item(self._get_best_poke_ball(battle_state))`: the parent's own choice,
    honouring its allowlist, so never the Master Ball. It is never the parent's `decide_turn`. A `None` ball → DEFER,
    which is unreachable after the out-of-balls flee [review safety F5].
  - **THROW-ONLY:**
    - our side is under Encore, Torment or Disable, or the target holds Imprison [R:ADV-B2];
    - the target is semi-invulnerable, behind a Substitute, confused or ticking (status1 poison/burn/toxic; status2
      wrap/curse/nightmare; status3 Leech Seed; our pending Future Sight or Doom Desire);
    - the target knows Explosion/Self-Destruct and no battler has Damp;
    - an ENDER is known: Teleport, Roar/Whirlwind, Perish Song, Memento;
    - a CALLING move is known: Metronome, Mirror Move, Assist, Sleep Talk;
    - the same PID now shows a different species;
    - the one-throw chance ≥ 0.5 (for THE ball THROW would use, at the current HP and status);
    - the per-battle caps are spent: 1 damage turn, 3 status tries (a berry cure counts as a try), 2 no-progress
      turns. They are keyed on the pure turn read.
  - **DAMAGE: NO-SELF-HARM is BINARY** (it replaces v2's numeric hazard floor). Damage is admissible only if the target
    can hurt ITSELF in NO way for the rest of this battle:
    - **Its moves:** none of recoil, crash, rampage, Belly Drum, Ghost Curse, Explosion/Self-Destruct or a calling
      move.
    - **Encore:** a target that knows Encore could force a second hit in a later turn [review safety F1 / mechanics
      S1: the execution-time override, `battle_util.c:111-117`].
    - **Acquired moves:** none of Transform, Mimic or Sketch [review mechanics B2].
    - **Weather moves:** none of Sandstorm or Hail, unless it is immune to them (RULING 25 names them) [review F7].
    - **Struggle:** its total PP must exceed the in-battle horizon H = 2 × (usable balls + 8). The 2 covers our
      Pressure. It is bounded by balls, because RULING 25's "never given up" spans encounters, not one battle [review
      F3, mechanics S2]. *(As built: the slack is 8. ⚠ Corrected by the build review (W12-S1): it bounds the THROW phase only. A
      trapped Run costs no turn (`battle_main.c:4339-4346`), and ordinary failed flees are UNBOUNDED
      (`battle_util.c:464-475`, the u8 speedVar wrap). So a Struggle-recoil KO stays reachable AFTER a catch is
      abandoned (out of balls, or the dex reserve/faint bail): a recorded residual, never during the catch.)*
    - **Weather:** no damaging weather it is not immune to (sand or hail, whether or not Cloud Nine or Air Lock is
      present, since the suppressor may leave).
    - **Our party's retaliation:** no member of our party able to battle (any faint-switch) has Rough Skin, Poison
      Point, Flame Body or Effect Spore against the target's contact moves, nor Liquid Ooze against its drain moves or
      Leech Seed, nor Synchronize [review F3, mechanics B1].
    - Then the only bound left is the hit itself: hp − X ≥ 1.
    - Rejected: v2's per-turn numeric floor. It protects one of many throw turns [R:ADV-S2].
    - Rejected: a floor summed over the horizon. It is sound but needs every hazard's per-turn cost, and binary is the
      conservative choice.
  - **Stage 1 damage** (effect-dispatched, never by name):
    - the effects: LEVEL_DAMAGE = our CURRENT level; SONICBOOM 20; DRAGON_RAGE 40; SUPER_FANG hp // 2 (hp ≥ 2);
    - admissible iff:
      - the chosen RAW slot has PP > 0 and is not the disabled move [review safety F4];
      - the target is not immune by type (the Foresight exception applies to Ghost);
      - the move gets through Wonder Guard, which blocks it unless super-effective (Night Shade vs Shedinja passes,
        but Shedinja's 1 max HP then fails hp − X ≥ 1) [review mechanics N4];
      - the target's hp is > 50% of max;
      - hp − X ≥ 1;
      - progress X ≥ 10% of max HP;
      - **E_gain ≥ 1.0 ball**, where `E_gain = E(hp) − E(hp − X)` and `E(h) = 1 / catch_p(ball, h, status)`: the
        expected BALLS saved. The ball is THROW's, and the status is the target's current one [review F5, mechanics
        S3, proof LP3].
        - *Revised before the predictions:* the first revision netted the damage turn: `E(hp) − (1 + E(hp − X))`.
          Computed on the arm's own target, that rejects Seismic Toss against a full-HP Taillow (max HP 22, 13
          damage): the net gain is 0.97. The resource RULING 25 constrains is BALLS (their cost, the reserve, "the
          best ball"), and the damage turn spends none. So the gain counts balls, which is v2's literal "E-gain ≥ 1.0
          throw". The turn itself costs the target's one attack on our lead, which the design accepts.
        - Under the fault that skips hp − X ≥ 1, E is evaluated at max(hp − X, 1).
  - **Stage 2 damage** (only with CALC=1; Tier A whitelist; W = 1, one hit):
    - ub = ceil(crit_max × 1.10) + `WEAKEN_MARGIN` (3, separate from ACCEPT_MARGIN);
    - admissible iff hp − ub ≥ 1, the target is > 50%, PP > 0, and the progress and E_gain at the non-crit MIN clear
      the same thresholds;
    - and NO step-11 persistent divergence holds (then no stage-2 damage): Guts with a burn; the foe's Marvel Scale
      with either side statused; our Flash Fire boost; Charge; badge-7 special; Hidden Power under Charge; the live
      ability differing from the species' [R:ADV-S9].
  - **STATUS** (sleep over paralysis, at most 3 tries). Skip on:
    - Substitute or Safeguard; any existing status;
    - Uproar on any battler (sleep);
    - the LIVE Insomnia/Vital Spirit (sleep) or Limber (paralysis);
    - Soundproof against a SOUND move (by the move's flag);
    - Thunder Wave against Ground, and Glare against Ghost without Foresight;
    - Taunt on us; the chosen slot's PP being 0 or its move disabled;
    - the target knows Magic Coat;
    - `banned_moves`.
    - Paralysis is also skipped against Synchronize (it reflects onto us), in favour of sleep.
    - A Chesto/Cheri/Lum berry is NOT a skip: the first try consumes it and counts as a try [review mechanics N2].
  - **No healing items, ever** (RULING 27).
- **D5. The adapter (W-b)** goes in `StoryCatchStrategy.decide_turn`, between the out-of-balls flee (SM:86-92) and
  `super()` (SM:93). `StoryDexCatchStrategy`'s bails run first by construction (SM:197-217).
  - It reuses the `battle_state` it is passed and makes NO `get_battle_state()` call (KI-108).
  - Its own `try`: any exception → DEFER plus one `[WEAKEN] ERR` line (flag on only).
  - `observe` logs the verdict and returns the parent's action unchanged. Each line carries its snapshot (for replay)
    and is marked `first=1` on the battle's first non-THROW verdict; later observe verdicts are counterfactual
    [R:ADV-N6].
- **D6. Logs and the instrument.**
  - `[WEAKEN]` and `[WEAKEN-OBS]` go in their OWN category `WEAKEN`. With the flag unset, NO line contains `WEAKEN`.
  - Every live arm runs with `POKEBOT_R25_DMGAUDIT=1`.
    - Its BEFORE records the move chosen at the selection EXIT. Its AFTER records Δ`gBideDmg[1]` and the HP, including
      at battle end, where a KO shows.
    - ⚠ The Encore execution override changes `gChosenMove`, not `gChosenMoveByBattler` [review safety F1]. So the
      grade checks the EFFECT: a STATUS turn must show Δbide = 0, and a DAMAGE turn exactly X.
  - The grade pairs each `[WEAKEN] act=` with the BEFORE of the SAME battle (the CTL segment) and the SAME turn counter
    [review LP9].
  - The primary safety readout: 0 `[CATCH] end … res=Won` in any acting arm without a fault.
- **D7. The docs that say a catch never damages** (SM:72-83, :96-109, :1773, :2073-2078; `probe_dexcatch_bail.py:4`;
  `probe_dex_open_fence.py:8`) are scoped to "with `POKEBOT_R25_WEAKEN` unset", in the code commit. The gates that pin
  those texts are checked and updated with them.
- **D8. The TEST lever:** `--set-lead-move <move-slot>=<move>` in `story_harness.py`, a state write for TESTS only.
  - It OVERWRITES move slot 1 of party slot 0: the fixture's Mudkip knows Tackle, Growl, Mud-Slap and Water Gun, so
    there is no empty slot; Growl is the one lost [review LP2].
  - It writes through the `game_cheats.py` `_rebuild_party` path, passing every field so nothing else resets. PP is set
    to the move's max.
  - It is read back on a LATER frame (the party read is frame-cached), and the read-back is logged like
    `--set-balls`'s.
  - It is applied in BOTH the ON and OFF arms of an experiment, so the lever-OFF run is the control.
  - Two values:
    - **Seismic Toss** (LEVEL_DAMAGE): the acting arm;
    - **Dragon Rage** (40 fixed): the bound's arm. Against every Route 116 target (max HP 20-28 at L6-8), 40 ≥ max HP,
      so hp − X ≥ 1 BINDS by construction [review LP1].
  - LEVEL_DAMAGE's X is the lead's level AT the catch turn, taken from the Step-0 reads [review LP4].
- **D9. A new KI for the Encore reader (BS:730, upstream too): filed as KI-114 and `#27-encorereader`, NOT fixed here.**
  - It is a shared battle path, and a fix would need its own A/B.
  - The weaken module reads the raw 0x06 itself.
- **D10. Fences and scope (recorded, not changed):**
  - The dex fence's full-HP expected-throws refusal still blocks ordinary hard catches before weaken acts; that is the
    intended scope [R:ADV-N11].
  - False Swipe is Q9, the user's question.
  - `hm` and `counter` follow after step 14.
  - The out-of-balls flee can fail against a trapping target [R:GEM-7]. That is the parent's path, and it goes to a
    lead for a KI after a check.
- **D11. The gate `tools/story-dev/probe_weaken_catch.py`** carries the W-row table (id, snapshot, expected verdict),
  filed in the PREDICTIONS BEFORE the code [R:ADV-B1].
  - Every fault is a production env with an exact red set written before its run.
  - A COVERAGE row fails if a row is in no mutant's set.
  - An adversarial mutant pass comes before registration.
  - Adapter rows run the REAL classes (`StoryDexCatchStrategy`/`StoryCatchStrategy` with a fake mode and state)
    [R:ADV-S11].
  - AST pins:
    - no `get_battle_state` in the adapter;
    - the adapter sits after the flee and before `super()`;
    - shiny does not reach it;
    - the construction lines are unchanged.
  - A stage-boundary row pair with a CALCLEAK fault [R:ADV-S1].
  - Every review finding becomes a row: Encore-knower, Transform-knower, a faint-switch retaliator, the PP horizon,
    0 PP, Master Ball + Poké Ball, the PID/species cases, the berry try.
- **D12. The catch-chance rows:**
  - `catch_p` against HAND-DERIVED decomp values at NON-full HP and with a status (a full-HP agreement alone cannot
    fail usefully [review LP11]);
  - the float `calculate_catch_success_chance` is NOT used [R:DEC, ADV-N8].
- **D13. Transform (Ditto) and Color Change (Kecleon):** handled by D2's PID/species rule and by "knows Transform →
  no damage". Color Change cannot raise an exact-damage move's damage.
- **D14. `run_with_base_modules.py` learns `plugins.custom_modes.*` modules** (it asserted `modules.*` only), so the
  BASE arms can load the base `story_mode.py` [review LP7]. It gets its own fault test, as its first version did.
- **D15. Step 11's decision rule is copied for every A/B here** (`2026-09-30-dmgcalc11-DESIGN.md` F7):
  - the two OFF runs of an experiment must match each other first (else a third);
  - an ON or observe run is graded against a REPRODUCING OFF run on every frame-stamped line without `WEAKEN`, up to
    its discriminator turn;
  - a lone divergent run is re-run, never graded;
  - the two OFF runs are separated in time (KI-112) [review LP5].

## THE ARMS (to pre-register after the Step-0 reads; every arm on the pinned `r20_pregym1_party4_r116.ss1`, TEAM6, `--set-balls 30`, seed 1, DMGAUDIT=1)

| Arm | What | Pass |
|---|---|---|
| G-W | `probe_weaken_catch.py` | every W-row; every fault exact; COVERAGE; AST pins; after an adversarial mutant pass; under 300 s |
| W-OFF ×2 | flags unset, the two runs separated in time | match each other; 0 lines contain `WEAKEN` |
| W-BASE ×2 | the BASE `story_mode.py` (D14), flags unset | = W-OFF on every frame-stamped line (the build changes nothing with flags unset) |
| W-OBS | WEAKEN=`observe` | = a reproducing W-OFF on every line without `WEAKEN`. One OBS line per in-scope decision, and none in shiny/hm/counter/trainer battles. Each OBS snapshot's target HP, status and moves equal DMGAUDIT's raw `mons` record at the same turn (an INDEPENDENT reader). The replay gives the same verdict (a determinism check only) [review LP6]. |
| W-OBSCALC | WEAKEN=`observe` + CALC=1 | as W-OBS; the stage-2 `would=` verdicts measured (a frequency only; nothing acts) |
| ST-OFF ×2 | the lever `1=Seismic Toss`, flags unset, separated in time | match each other; these ARE the Step-0 reads that name the discriminator (the first in-scope turn against a target where Seismic Toss is admissible) |
| ST-ON | the lever + WEAKEN=1 | = ST-OFF up to the discriminator turn. There, `[WEAKEN] act=DAMAGE`, DMGAUDIT's BEFORE shows Seismic Toss, Δbide = X exactly, and the target is not KO'd. 0 `res=Won`. |
| DR-OFF ×2 | the lever `1=Dragon Rage`, flags unset, separated in time | match each other; the discriminator: the first in-scope turn |
| DR-ON | the lever + WEAKEN=1 | = DR-OFF up to the discriminator turn. There, NOT Dragon Rage (THROW or STATUS); 0 `res=Won`. The bound BINDS. |
| DR-FAULT | the lever + WEAKEN=1 + a fault that skips hp − X ≥ 1 | at the discriminator turn Dragon Rage runs (BEFORE), the target faints (`[CATCH] end … res=Won`). No vacuity exit: if it does not happen, the arm FAILS. |

## OPEN, NOT DECIDED HERE (the user's)

- ACCEPT_MARGIN and stage 2's release (step 11's F8).
- False Swipe (Q9).
- Whether stage 1's near-zero live reach is worth a CATCHING-LEAD choice: a future item that would put a
  status/exact-damage holder in the lead for wanted catches. It is out of scope; `roster.py:122 reorder_party` exists.

## THE DESIGN REVIEW (three fresh lenses, 2026-09-30; every blocker/should-fix to a refuter; `…-recon/w12_design_review.md`, verbatim)

- **One BLOCKER, confirmed:** proof LP1. W-FAULT could never bind with Seismic Toss (targets always at full HP; X ≤ 17
  < max HP 20-28), and its pass column let it pass by declaration. → The Dragon Rage lever (40 ≥ every target's max
  HP) and DR-ON/DR-FAULT with no vacuity exit.
- **Should-fix, all confirmed by refuters and folded:**
  - safety F1 / mechanics S1: an Encore landing in the same turn forces a second hit at EXECUTION (`battle_util.c:111-117`)
    → no damage against an Encore-knower; the grade checks the EFFECT.
  - mechanics B1 / safety F3: the retaliation clause looked at the active mon only → the whole party.
  - mechanics B2: Transform acquires moves after the decision → knows Transform/Mimic/Sketch → no damage; the target
    identified by PID.
  - mechanics S2 / safety F3: the Struggle threshold contradicted the design's own premise → the ball-bounded horizon.
  - safety F4: no PP rule → PP > 0 on the raw slot.
  - safety F5 / mechanics S3 / proof LP3: THROW, the ball and E_gain were undefined → defined (THROW is the parent's
    ball; E_gain nets the damage turn).
  - proof LP2: the lever had no empty slot → it overwrites Growl, in BOTH arms.
  - proof LP4: LEVEL_DAMAGE was hard-coded to the load level → taken from Step-0.
  - proof LP5: KI-112 controls for the lever arms → ST-OFF ×2 and DR-OFF ×2, plus step 11's decision rule (D15).
  - proof LP7: nothing compared flags-unset against the BASE → W-BASE ×2, and the tool learns `plugins.*` (D14).
- **Refuted to nits:** safety F2 (its Transform half survives as mechanics B2); proof LP3 (folded anyway); proof LP6
  (the replay is a determinism check, so an independent-reader check was added).
- **Nits folded:** F7 (weather moves); F8/LP10 (the turn from a pure read); N1 (v2's order restored); N2 (a berry is a
  try); N4 (the Wonder Guard wording); LP9 (pairing by battle and turn); LP11 (non-full-HP catch rows).
- **Nits left as recorded scope:** N3 (one damage turn is conservative); LP8 (the exclusion clauses are exercised by
  the pure gate, not live).

## AS BUILT, AFTER THE GATE'S ADVERSARIAL MUTANT PASS (2026-09-30; `tools/story-dev/evidence/2026-09-30-weaken12-ADVERSARIAL.txt`)

- **The pass.** 139 mutants: the gate caught 37 and missed 102. The worst miss was the KO floor's off-by-one
  (`hp − X ≥ 0`), invisible to a gate whose only floor row sat 18 HP from the boundary.
  - 85 of the misses were caught by its 72 proposed rows. The 17 others were argued equivalent, only more
    conservative, or unreachable.
  - After the fold, the gate is 211 rows, 9 faults and 196 mutants. Every one of its 205 pre-written sets matched on
    the first run.
- **Five production defects it found, each FIXED with a row that failed on the old code and a reverting mutant:**
  - **PD1, a real KO path:** a NON-lead party member with Trace that faint-switches in copies the TARGET's ability (e.g.
    Rough Skin), which then chips the target every throw turn. ⇒ With Trace in the party, the target's own live ability
    counts among the retaliation subjects.
  - **PD2, latent:** Pain Split before our hit resets the target's HP. ⇒ Self-harm.
  - **PD3, no reach:** a confusion berry (Figy, Wiki, Mago, Aguav, Iapapa) fires at half HP, where our hit leaves the
    target. ⇒ No damage.
  - **PD4, no reach:** a Sand Stream party member would start a sandstorm on a faint-switch. ⇒ No damage unless the
    target is sand-immune.
  - **PD5, very low:** a stage-2 RECHARGE turn and failed flee turns throw no ball. ⇒ Stage 2 excludes RECHARGE moves,
    and the horizon slack is 8.
  - **A grading nit:** a THROW with no ball to name was logged DEFER but remembered as THROW. ⇒ The memo records what
    was done.
- **No filed verdict changed,** except W42b's snapshot, which moved to total PP 78 to stay just above H.
- **Every live arm's Step-0 decision is unchanged:** ST DAMAGE, DR THROW, NL THROW (the builder replayed each).
- **The arms are RE-RUN on the fixed commit** (`…-GRADED.md`).

