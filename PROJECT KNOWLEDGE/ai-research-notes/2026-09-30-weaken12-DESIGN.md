# 2026-09-30 — design v2 step 12 (W, weaken-to-catch, RULING 25): the DESIGN, after a five-angle recon

⚠ **A NOTE, not a source of truth.** It supersedes v2's §Step 12 (`2026-09-29-r23-27-DESIGN-v2.md` :595-666) where they
differ. Recon reports (each a NOTE): `2026-09-30-weaken12-recon/w12_recon_{decomp,ourcode,fixture,adversary,gemini}.md`.
Tags: [R:ADV-B2] = the adversary's finding B2; [R:DEC-H5] = the decomp report's H5; [R:OUR-3.6], [R:FIX], [R:GEM-7].

⛔ **THE HEADLINE CARRIES THE CAVEAT: STAGE 1 WILL ALMOST NEVER ACT IN A REAL RUN.**
- Across all 66 fixture rows, no party lead holds an exact-damage, sleep or paralysis move. The one stage-1 move
  anywhere is Sing, on a Skitty that sits in slot 3 and never leads [R:FIX].
- The story's leads are Sceptile, Mightyena, Swellow and Mudkip/Marshtomp, and none of them learns such a move
  before the League.
- So what really weakens a target is STAGE 2: plain hits, bounded by the calculator. Stage 2 stays OFF, because step
  11 MEASURED the calculator and did NOT clear it (8 of 300 hits).
- Step 12 therefore builds the SAFE, GATED MACHINERY. Its live value arrives when stage 2 is cleared: by step 14's
  batch with `POKEBOT_R25_DMGAUDIT=1`, or by `#27-dmgcalcfix` plus the user's ACCEPT_MARGIN ruling.
- Proving stage 1 live takes a TEST lever (W8 below). Natural play will not exercise it.

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
  - Wonder Guard blocks all four (power 1).
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

## THE DESIGN (D1-D14; each also a `06` decision when built)

- **D1. Scope and flags.**
  - `POKEBOT_R25_WEAKEN` ∈ {unset, `observe`, `1`}.
  - `POKEBOT_R25_WEAKEN_CALC` ∈ {unset, `1`} (stage 2; meaningful only with WEAKEN set).
  - `POKEBOT_R25_WEAKEN_KINDS` defaults to `dex,team`.
  - All default OFF, each read once per run in `reset_per_run_state`, each with a `29` row.
  - Stage 2 is BUILT here, so its `observe` verdicts can be measured live, and it stays OFF in every acting arm and
    batch until M1b's acceptance.
- **D2. The kind comes from the mode, and no construction site changes.**
  - The adapter reads `context.bot_mode_instance._catch_ctx`. `_r20_catch_start` fills it on the line before each
    catch strategy is returned (SM:6446-6467).
  - The adapter acts only if `ctx["kind"]` is in scope AND `ctx["sp"]` names the battle's opponent species. That
    guards against a context left stale by a swallowed exception.
  - Otherwise it DEFERs.
  - Rejected: a `weaken=` constructor argument. It would rewrite three construction lines that four existing gates
    pin, and the harness and gates build instances without `__init__` [R:OUR-3.1-3.3].
  - Shiny never reaches the adapter (SM:251-275 calls `CatchStrategy.decide_turn` directly); a row pins that.
- **D3. The pure module `sandbox-pokebot/modules/story/weaken_catch.py`** (no emulator, no `random`).
  - Frozen snapshots: WTarget, WSelf, WEnv. They include the raw move slots, the LIVE ability bytes mapped to names,
    the disable-struct fields (Encore move 0x06 and its timer, Disable, Taunt), our Torment, the target's
    Imprison-others, both status2/status3, the side status and Safeguard timer, weather plus Cloud Nine/Air Lock, the
    battle-type flags, Uproar on any battler, and the target's held item.
  - `catch_p` is exactly `battle_script_commands.c:9987-10028`, with odds > 254 giving 1.0 and the full ball table
    ([R:DEC-C1, C3]; Net Ball uses the LIVE types).
  - `decide_weaken_turn(...)` returns one of {DAMAGE(slot), STATUS(slot), THROW, DEFER} plus a reason.
- **D4. The order of checks** (the first match wins).
  - **DEFER:**
    - the flag is off, or the kind is out of scope, or the context does not match;
    - the battle is not a single wild battle: trainer, safari, double, roamer, any legendary or Regi/Kyogre/Groudon/
      Rayquaza flag, Pyramid or Pike [R:ADV-S7];
    - any read failed;
    - our item is a Choice item.
  - **THROW-ONLY:**
    - our side is under Encore, Torment or Disable, or the target holds Imprison [R:ADV-B2];
    - the target is semi-invulnerable, behind a Substitute, confused or ticking (status1 poison/burn/toxic; status2
      wrap/curse/nightmare; status3 Leech Seed; our pending Future Sight or Doom Desire);
    - the target knows Explosion/Self-Destruct and no battler has Damp;
    - an ENDER is known: Teleport, Roar/Whirlwind, Perish Song, Memento;
    - a CALLING move is known: Metronome, Mirror Move, Assist, Sleep Talk (step 11's lesson);
    - the one-throw chance ≥ 0.5;
    - the per-battle caps are spent: 1 damage turn, 3 status tries, 2 no-progress turns. They are keyed on
      `battle_state.current_turn`, never on `decide_turn` calls [R:OUR-3.6].
  - **STATUS** (sleep over paralysis, at most 3 tries). Skip on:
    - Substitute or Safeguard; any existing status;
    - Uproar on any battler (sleep);
    - the LIVE Insomnia/Vital Spirit (sleep) or Limber (paralysis);
    - Soundproof against a SOUND move (by the move's flag, not its name);
    - Thunder Wave against Ground, and Glare against Ghost without Foresight;
    - Taunt on us;
    - the target knows Magic Coat;
    - the target holds Chesto/Lum (sleep) or Cheri/Lum (paralysis);
    - `banned_moves`.
    - Paralysis is also skipped against Synchronize (it reflects onto us), in favour of sleep.
  - **DAMAGE: NO-SELF-HARM is BINARY** (it replaces v2's numeric hazard floor). Damage is admissible only if the
    target can hurt ITSELF in NO way this battle:
    - it knows no recoil, crash, rampage, Belly Drum, Ghost Curse, Explosion/Self-Destruct, Struggle-risk (total PP
      ≤ 4) or calling move;
    - no damaging weather it is not immune to (sand/hail, not suppressed by Cloud Nine/Air Lock);
    - none of OUR retaliation abilities (live byte) against its contact moves: Rough Skin, Poison Point, Flame Body,
      Effect Spore; nor Liquid Ooze against its drain moves or Leech Seed; nor Synchronize.
    - Then the only bound left is the hit itself: hp − X ≥ 1.
    - Rejected: v2's per-turn numeric floor. It protects one of an unbounded number of throw turns [R:ADV-S2].
    - Rejected: a floor summed over k turns. k is unbounded, because a wanted rare is never given up on (RULING 25).
  - **Stage 1 damage** (effect-dispatched, never by name):
    - the effects: LEVEL_DAMAGE = our level; SONICBOOM 20; DRAGON_RAGE 40; SUPER_FANG hp // 2 (hp ≥ 2);
    - admissible iff the target is not immune by type (the Foresight exception applies to Ghost) and has no Wonder
      Guard;
    - its hp is > 50% of max;
    - hp − X ≥ 1;
    - progress X ≥ 10% of max HP, and E-gain ≥ 1.0 throw (both calculator-free for exact damage [R:ADV-S12]).
  - **Stage 2 damage** (only with CALC=1; Tier A whitelist; W = 1, one hit):
    - ub = ceil(crit_max × 1.10) + `WEAKEN_MARGIN` (3, separate from ACCEPT_MARGIN);
    - admissible iff hp − ub ≥ 1, the target is > 50%, the progress at the non-crit MIN is ≥ 10% of max, and the
      E-gain at the MIN is ≥ 1.0;
    - and NO step-11 persistent divergence holds (then no stage-2 damage): Guts with a burn; the foe's Marvel Scale
      with either side statused; our Flash Fire boost; Charge; badge-7 special; Hidden Power under Charge; the live
      ability differing from the species' [R:ADV-S9].
  - **No healing items, ever** (RULING 27).
- **D5. The adapter (W-b)** goes in `StoryCatchStrategy.decide_turn`, between the out-of-balls flee (SM:86-92) and
  `super()` (SM:93). `StoryDexCatchStrategy`'s bails run first by construction (SM:197-217).
  - It reuses the `battle_state` it is passed and makes NO `get_battle_state()` call (KI-108).
  - Its own `try`: any exception → DEFER plus one `[WEAKEN] ERR` line (flag on only).
  - `observe` logs the verdict and returns the parent's action unchanged. Each line carries its snapshot, so the pure
    module can replay it. The first non-THROW verdict of a battle is marked `first=1`; later observe verdicts are
    counterfactual [R:ADV-N6].
- **D6. Logs.** `[WEAKEN]` and `[WEAKEN-OBS]` go in their OWN category `WEAKEN`. With the flag unset, NO line contains
  `WEAKEN` [R:ADV-S4].
  - **The ACTION is instrumented by step 11's recorder:** every live arm runs with `POKEBOT_R25_DMGAUDIT=1`. Its BEFORE
    records the move the game ACTUALLY chose (`gChosenMoveByBattler`), and its AFTER records Δ`gBideDmg[1]` and the
    HP, including at battle end, which is where a KO would show [R:ADV-S3, rule 7].
  - The grade pairs each `[WEAKEN] act=` with the next `[DMGAUDIT] BEFORE` by frame.
  - The primary safety readout: 0 `[CATCH] end … res=Won` in any acting arm.
- **D7. The docs that say a catch never damages** (SM:72-83, :96-109, :1773, :2073-2078; `probe_dexcatch_bail.py:4`;
  `probe_dex_open_fence.py:8`) are scoped to "with `POKEBOT_R25_WEAKEN` unset", in the code commit.
- **D8. The TEST lever for a non-vacuous stage-1 arm:** `--set-lead-move <slot>=<move>` in `story_harness.py`, a
  state write for tests only, read back and logged like `--set-balls`.
  - It gives the fixture's lead Mudkip (L13) Seismic Toss in an EMPTY slot, so no existing move is lost. That is 13
    fixed damage, and Fighting is not immune against the Route 116 targets (Taillow, Skitty, Abra).
  - The live arm's ON/OFF discriminator is computed at the Step-0 reads, on the arm's own trajectory.
- **D9. A new KI for the Encore reader (BS:730, upstream too): filed, NOT fixed here.**
  - It is a shared battle path, and fixing it changes `can_use_move` for every battle. That needs its own A/B.
  - The weaken module reads the raw 0x06 itself.
- **D10. Fences and scope (recorded, not changed):**
  - The dex fence's full-HP expected-throws refusal still blocks ordinary hard catches before weaken acts; that is the
    intended scope [R:ADV-N11].
  - False Swipe is Q9, the user's question.
  - `hm` and `counter` follow after step 14.
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
  - A stage-boundary row pair with a CALCLEAK fault [R:ADV-S1]: the same snapshot, CALC unset → no plain hit, CALC=1
    → admitted.
- **D12. The catch-chance rows:**
  - `catch_p` against hand-derived decomp values;
  - `catch_p` agrees with `dex_catch_expected_throws` at full HP;
  - the float `calculate_catch_success_chance` is NOT used [R:DEC, ADV-N8].
- **D13. Transform (Ditto) and Color Change (Kecleon):** the snapshot is re-read each decision. A target whose live
  species differs from the context's `sp` → THROW-ONLY [R:GEM-4].
- **D14. The out-of-balls flee can fail against a trapping target** [R:GEM-7]. That is the parent's existing path and
  out of scope, recorded as a lead for a KI after a check.

## THE ARMS (to pre-register after the Step-0 reads)

| Arm | What | Pass |
|---|---|---|
| G-W | `probe_weaken_catch.py` | every W-row; every fault exact; COVERAGE; AST pins; after an adversarial mutant pass; under 300 s |
| W-OFF ×2 | `r20_pregym1_party4_r116.ss1`, TEAM6, `--set-balls 30`, seed 1, flags unset, DMGAUDIT=1, the two runs SEPARATED IN TIME | they match on every frame-stamped line; 0 lines contain `WEAKEN` |
| W-OBS | the same, WEAKEN=`observe` | = a reproducing OFF on every line without `WEAKEN`; one OBS line per in-scope decision (reconciled with `[TURN]` inside team/dex `[CATCH]` battles); none in shiny/hm/counter/trainer battles; every OBS line replays to the same verdict through the pure module |
| W-OBSCALC | the same, WEAKEN=`observe` + CALC=1 | as W-OBS; the stage-2 `would=` verdicts are measured (frequency only; nothing acts) |
| W-EXEC ON/OFF | the lever (D8) + WEAKEN=1 vs unset, DMGAUDIT=1 | ON: at the first in-scope turn the discriminator names, DMGAUDIT's BEFORE shows Seismic Toss, Δbide = 13, and the target is not KO'd; OFF throws there; 0 `res=Won` in either |
| W-FAULT | the EXEC arm plus a fault that skips hp − X ≥ 1 (chosen so that it binds on the arm's trajectory, by computation) | the named KO happens (`res=Won`), proving the bound is load-bearing; or the arm is declared vacuous with its reason |

## OPEN, NOT DECIDED HERE (the user's)

- ACCEPT_MARGIN and stage 2's release (step 11's F8).
- False Swipe (Q9).
- Whether stage 1's near-zero live reach is worth a catching-lead choice: a future item that would put a
  status/exact-damage holder in the lead for wanted catches. It is out of scope; `roster.py:122 reorder_party` exists.
