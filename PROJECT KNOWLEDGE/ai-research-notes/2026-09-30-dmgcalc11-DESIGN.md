# 2026-09-30 — design v2 step 11 (M1, damage-calculator fidelity): the DESIGN, after a five-angle recon and a three-lens review

> A NOTE refining `2026-09-29-r23-27-DESIGN-v2.md` §Step 11. It supersedes that section where they differ.
> - The recon was a workflow of five fresh Claude agents: our calculator, the decomp transcribed, an adversarial
>   deviation hunt, the records and rulings, and the live state readers (their reports are NOTES in
>   `2026-09-30-dmgcalc11-recon/`). A Gemini fan-out was used only for "what to look for", and the decomp agent
>   checked it claim by claim: names mostly right, placement and order mostly wrong. The author re-read every
>   load-bearing claim marked ✔ at the cited place. ⚙ marks a number computed by the recon or the review that the
>   gate must re-derive; ⚠ marks a claim not yet checked live.
> - Branch `wt/dmgcalc11`, cut from `main` `241929d7` (10b merged).
> - ✅ **The design's adversarial review has RUN** (three fresh Claude agents, 2026-09-30: the M1a gate, the M1b
>   audit, scope/records/arms; `## THE DESIGN REVIEW` at the end). It found 4 blockers and about 30 should-fix
>   findings. Every one is folded in below, marked **[R:<id>]**.
> - ✅ **The Step-0 live reads (F6) have RUN** and held on every question (`tools/story-dev/evidence/2026-09-30-dmgcalc11-STEP0.txt`).
> - ✅ **The PREDICTIONS are filed** (`2026-09-30-dmgcalc11-PREDICTIONS.md`, before any code).
> - ⛔ **Nothing here is built yet.** Next: the code, the gates' adversarial mutant passes, the gates, the arms, the review.

## WHY THE v2 STEP 11 BODY CANNOT BE BUILT AS WRITTEN

- **B1. The proposed acceptance CAN FAIL ON CORRECT PLAY (rarely), because the calculator applies the crit after
  STAB and type.** v2 says "0 over crit_max + 3 HP" (v2 §3's M1b acceptance row).
  - Ours: ✔ `_util.py:207-213` (STAB, then each type), then `:230-231` (crit ×2) and `:233-238` (Charge ×2).
  - The game: ✔ `battle_script_commands.c:1293-1301` (`Cmd_damagecalc`: base × `gCritMultiplier` × `dmgMultiplier`,
    then Charge ×2, then Helping Hand), before STAB (`:1369-1372`) and the type steps (`ModulateDmgByType`, ✔
    `:1321-1325`, a minimum of 1 per step), with the random factor last (✔ `:1639-1651`).
  - ⚙ The recon and the review, three times independently: crit_max reads up to **4 HP** low, and up to **8 HP** with
    Charge. By hand: a STAB 4× crit on an odd post-base value B, the game 12B, ours 12B−4.
  - **How often [R:SR-12]:** exceeding crit_max + 3 needs STAB, two 2× steps, a crit, an odd B and the top random
    roll: ⚙ about 1/512 per STAB-4× hit. A STAB 2× crit errs by 2 (inside +3); a non-STAB 4× by 0. So a failure
    is luck, not fidelity, and one is enough to fail the acceptance for good.
  - Story-path 4× cases: Makuhita vs the Aron line, Marshtomp's Mud-Slap vs Magnemite, Electrike vs
    Wingull/Pelipper, Grass vs Barboach and Geodude.
- **B2. "The whitelisted effects" are defined nowhere**, and `EFFECT_HIT` alone is not safe: Surf is `EFFECT_HIT`
  yet doubles against a diving target (`battle_scripts_1.s:236-240`, checked by the review).
- **B3. `[TURN]` does not name the executed move.** It is logged before the no-PP override (✔ emission
  `battle_action_selection.py:534-538`; the override at `:552-569`), and Encore can substitute the move. M1b
  predicts for `gChosenMoveByBattler[0]` (✔ `pokeemerald.sym:156`), read at the selection exit.
- **B4. Excluding faints discards the evidence step 12 exists for** (KO-safety). `gBideDmg[1]` (✔ `.sym:133`)
  records our hit's damage before the HP cap and is blind to heals, end-of-turn effects and weather chip (the recon;
  confirmed by two review lenses at `bsc.c:1912` vs `:1920-1929`). ⚠ Live unverified (F6). Its limits
  [R:M1A-8, M1b-6, M1b-9, SR-15]: it is recorded AFTER the hp−1 clamp (False Swipe, Endure, Focus Band), and it
  also records the foe's recoil, crash, confusion self-hit, Substitute cost, Belly Drum, Curse cost, Pain Split, our
  Rough Skin and our Liquid Ooze; the foe's Bide resets it to 0 mid-turn.
- **B5. The spec evaluates the foe's status only before the turn**, but our own move can burn, poison, confuse or trap
  the foe THIS turn.
- **B6. KI-110 cannot be pinned in the direction M1 audits.** It changes only damage aimed at US
  (`defender_is_player`); an our-attack row passes vacuously.
- **B7. A scope conflict in the record:** step 11 is "measurement only" (v2:23, v2:569; 03; 04), while KI-109, KI-110
  and KI-111 each named "v2 step 11" as their fix vehicle (05). 06 holds no user ruling on fixing the calculator and
  no "do not re-raise" (grepped by the recon and again by the review: CLAUDE.md rule 11).

## THE DESIGN (F1-F10; each also a `06` decision when built)

- **F1, scope: MEASUREMENT ONLY. `_util.py` is not changed in step 11.**
  - M1a pins every deviation as a KNOWN-DIVERGENCE row (F2).
  - The fixes are a NEW item, **`#27-dmgcalcfix`**, filed in `03` with this revision: KI-109/110/111, D1 (the crit
    and Charge order), D2 (type order), D3 (the per-step minimum), Marvel Scale on the wrong battler, Guts + burn,
    Psywave's minimum, fixed-damage immunity, Brick Break vs screens, Hidden Power (Electric) under Charge. Its own
    default-OFF flag, M1a as its gate, an A/B on the ORDINARY case (06:4555-4559, 06:4595-4598). KI-111's fix
    touches the user's profile and the schema, and every fix is an upstream divergence for `DIVERGENCE-LOG`
    [R:SR N5]. The KIs' "vehicle: v2 step 11" lines point to it (edited in this revision [R:SR-10]: the first
    version of this note CLAIMED that edit and had not made it).
  - Why not in step 11: a KI-109 fix changes move choice (a behaviour change, so a flag and an A/B), and M1b's
    inertness proof cannot hold in the same step as a behaviour change.
- **F2, M1a: `tools/story-dev/probe_damage_calc_decomp.py`, a pure gate.**
  - **The instrument cannot be controlled by itself [R:M1A-1, SR-7] (BLOCKER folded).** A port written in our order
    would enumerate 0 and pass. Therefore:
    - the predictions pre-register HAND-DERIVED anchor literals, each with its decomp lines, BEFORE the port exists.
      From the review ⚙: Fighting STAB vs Normal/Rock, B=3, crit: game 36, ours 32. Spark STAB vs Wingull, B=3,
      crit + Charge: game 72, ours 64. Mud-Slap vs Magnemite, B=5, crit: game 60, ours 56;
    - every anchor is checked against BOTH the port and the calculator;
    - every enumerated bound must be at least its bucket's largest anchor delta (a smaller bound means the port is
      wrong), and after the first run the bounds are asserted EXACTLY, each with a witness tuple pinned as a row;
    - the mutant "the port in our order" must turn the anchor assertions red.
  - **The enumeration drives PRODUCTION [R:M1A-5].** `_calculate_base_move_damage` is patched to return B, and the
    REAL `calculate_move_damage_range` runs the rest. Ordered defender type pairs in ROM order (never from
    `species.json`, which is alphabetical: 95 of 385 species differ [R:M1A N1]), a defender with a neutral ability,
    a whitelisted non-Struggle move. ⚙ 36 s for all 17 types × 289 ordered pairs × STAB × crit × Charge × B = 2-259.
  - **Four signed buckets, max end and min end separately [R:M1A-4].** ⚙ Pre-registered: non-crit under 1 / over 1;
    crit under 4; non-crit + Charge under 4; crit + Charge under 8; min ends ±1, 4, 4, 7.
  - **Rows run the REAL calculator on REAL objects [R:M1A-2, SR N7].** `BattlePokemon` built from 0x58-byte
    `gBattleMons` records inside a real `BattleState`; types only from `get_type_by_name`/`_index` (a fresh `Type`
    compares by identity and reads neutral); every row asserts `attacker in own_side` and `defender not in own_side`
    first (a stand-in's `__contains__` returns `NotImplemented`, which reads True).
  - **Badges per row [R:M1A-3].** `_util.get_event_flag` is patched per row with an explicit flag set (patching
    `modules.memory` does nothing: `_util` imported the name; offline, every flag reads False silently). KI-110 is
    pinned at {BADGE07 set, BADGE08 clear}, in the foe→us direction. A liveness row: Badge 1 on vs off must change
    ours' output.
  - **Every KNOWN-DIVERGENCE row asserts three literals [R:M1A-6]:** the game's value (from the port, or for a
    base-term row hand-derived from `pokemon.c`), ours, and the nonzero delta. Rows: the crit order; the type order
    (Bite vs Sableye, with an odd post-STAB value); the per-step minimum; Marvel Scale on each battler; Guts + burn;
    Sonicboom and Psywave (KI-109; Psywave's minimum is level/2); fixed damage vs an immune type, using a move whose
    name branch DOES match (Night Shade vs Normal; Seismic Toss or Super Fang vs Ghost) [R:M1A-7]; Brick Break vs
    Reflect; Struggle; Hidden Power's type and power; Hidden Power (Electric) under Charge [R:M1A N6]; KI-110; KI-111.
  - **The whitelist**, a constant keyed on `moves.json` `effect`, never on names, except Surf and Struggle, which
    need the move index [R:M1A N3]:
    - Tier A (plain: one hit, fixed power, no condition): HIT, HIGH_CRITICAL, ALWAYS_HIT, QUICK_ATTACK, VITAL_THROW,
      PAY_DAY, SECRET_POWER, SKY_UPPERCUT, THUNDER, KNOCK_OFF, THIEF, RAPID_SPIN, FLINCH_HIT, PARALYZE_HIT,
      FREEZE_HIT, the stat-down and stat-up *_HIT effects, SUPERPOWER, OVERHEAT, RECHARGE, DOUBLE_EDGE, RECOIL (not
      Struggle), RECOIL_IF_MISS, ABSORB, RAGE, HIDDEN_POWER.
    - Tier B (a secondary that can move the FOE's HP the same turn): BURN_HIT, BLAZE_KICK, THAW_HIT, TRI_ATTACK,
      POISON_HIT, POISON_TAIL, POISON_FANG, CONFUSE_HIT. Valid only when the AFTER read passes F4's status rules.
    - Tier C (conditional; valid only while the condition is observably false at BOTH reads): Surf vs Underwater;
      EARTHQUAKE vs Underground; GUST and TWISTER vs InTheAir; FLINCH_MINIMIZE_HIT vs Minimized; FACADE;
      SMELLINGSALT; WEATHER_BALL; BRICK_BREAK; PURSUIT; any Fire or Electric move while Mud Sport or Water Sport is on
      any battler [R:M1A-9]; FALSE_SWIPE only while the foe's HP before exceeds crit_max [R:M1A-8]; FAKE_OUT,
      FOCUS_PUNCH, SNORE and DREAM_EATER, whose failures still spend PP (they read as a 0; F4's "no damage" stratum)
      [R:M1A N2, M1b-2]. (Whirlpool is TRAP, which is out.)
    - Everything else is out: multi-hit, dynamic power, fixed damage, OHKO, Counter/Mirror Coat/Bide/Endeavor,
      two-turn, Future Sight, TRAP, EXPLOSION. It goes to a logged stratum, never to the acceptance set.
  - **Mutants**, with sets written before the first run and an ADVERSARIAL mutant pass before the gate is trusted
    [R:SR N6]: the port in our order; swapped type order; a `_util` edit that FIXES D1 (every D1 row must flip:
    `#27-dmgcalcfix` depends on exactly that); and the gate's usual row mutants. Timed against `run_gates`' 300 s.
    (The spec's "a synthetic row over crit_max + MARGIN must fail" belongs to F4's audit, which is where an
    acceptance is computed [R:M1A N5, SR-8].)
- **F3, M1b PRODUCTION: RAW reads only [R:SR-2].** Behind `POKEBOT_R25_DMGAUDIT=1`, in their OWN log category
  `DMGAUDIT` (never `BATTLE`, never appended to `[TURN]`: v2 [A-S10]).
  - Why raw: every verdict is then computed OFFLINE by F4, which is pure and gateable, and a classifier bug found
    after step 14 costs a re-audit, not a re-batch. The every-battle path gains reads and one log call, nothing else.
  - **BEFORE, at the selection exit** (the fall-through of ✔ `battle_action_selection.py:173`'s `while`; the review
    checked: choices are final there, and no frame passes, so HP cannot change). It logs, by PURE `read_symbol` reads:
    the turn counter (`gBattleResults` + 0x13, ✔ `battle.h:247` per two lenses), `gBattleOutcome`, both chosen
    actions and moves, both battlers' raw `gBattleMons` records (0x58 bytes), `gStatuses3`, `gDisableStructs`, the
    weather, both side statuses, both `gBideDmg` slots, and the Flash Fire flag (a `gBattleResources` double
    dereference [R:M1b-8]). And the LIVE prediction for `gChosenMoveByBattler[0]`: min, max, and crit_max with
    `is_critical_hit=True`, computed on the handler's EXISTING `battle_state` object (BAS:115), valid because nothing
    in `gBattleMons` changes during selection [R:M1b-11c, SR N7]. ⛔ It adds no `get_battle_state()` call (KI-108).
  - **AFTER, at the next selection entry** (reusing the BAS:115 object), and **at the battle's end** (the
    battle-handler loop's exit, with pure reads; ⚠ whether `gBattleMons` survives there is F6's question) [R:M1b-11d]:
    the same raw fields.
  - **Where BEFORE lives [R:M1b-12]:** at module level (the handler is re-entered within one selection, and a
    function local dies across re-entries: BAS:26-28); the latest exit overwrites it; it is cleared at battle start.
    There are other exits (BAS:193, :886, :981, raises, the KI-47 abandonment): only the `while` fall-through writes
    a BEFORE.
  - A `[DMGAUDIT] CTL` line at battle start. ⛔ With the flag unset, NO line contains `DMGAUDIT` [R:SR-3].
  - The flag is read per handler call, like BAS's census flags (BAS:150): a THIRD stated exception to v2:151's
    "read per run in `reset_per_run_state`", because BAS has no StoryMode and the harness drivers bypass it
    [R:SR-11].
- **F4, M1b CLASSIFIER and AUDIT: `tools/story-dev/audit_damage_calc.py` (pure; gated by `probe_dmgaudit.py`).**
  - **Pairing [R:M1b-1, SR-1] (BLOCKER folded):** a pair is BEFORE(T) with EITHER the entry read at T+1, OR the
    battle-end read with `gBattleOutcome != 0` and the counter still T (the game never increments it on the turn a
    battle ends: ✔ `battle_main.c:3988-3997`). A changed foe identity is kept when Δ`gBideDmg[1]` ≥ the foe's HP at
    BEFORE and the old mon's party HP is 0 (a trainer KO); `gBideDmg` is per slot and survives the switch. Not with
    Spikes on the foe's side (a switch-in's Spikes are recorded) [R:M1b-1b, SR N4].
  - **A sample:** singles only; our action USE_MOVE with a nonzero chosen move; our PID unchanged; the chosen MOVE's
    PP down by at least 1, matched by move id, never by slot [R:SR-2]. **A hit is Δ`gBideDmg[1]` > 0**; a 0 with PP
    spent is the "no damage" stratum (miss, Protect/Detect, a failed move) [R:M1b-2, SR-14]. A NEGATIVE Δ is an
    instrument fault (the foe's Bide resets it) [R:M1b-9].
  - **Strata, never silent discards**, each evaluated at BOTH reads:
    - the foe: status, confusion, trap, Leech Seed, Curse or Nightmare; a Tier C condition; its Def/SpD stage or its
      side's screens changed [R:M1b-10]; its chosen move hurts itself (recoil, crash, Substitute, Belly Drum, Ghost
      Curse, Pain Split, Explosion, Memento), or is Protect, Detect, Endure or Bide [R:M1b-6, M1b-9]; its chosen move
      reads 0 (Struggle) [R:M1b-9]; it holds a Focus Band; a Substitute; a held item or a bag item used
      (`gChosenActionByBattler[1]` = item) [R:M1b-5, SR-4];
    - our side: HP ≤ maxHP/3 at ANY point of the turn with a matching pinch ability (HP before − Δ`gBideDmg[0]`, which
      catches a dip and a drain back up [R:M1b-7]); an Atk/SpA stage change; a status change with Guts or Facade;
      Flash Fire set; our Rough Skin; our Liquid Ooze against a draining foe [R:SR-15];
    - PERSISTENT known-divergence states at BEFORE, from M1a's rows (Guts + burn, Marvel Scale, Cloud Nine/Air Lock,
      Flash Fire): their own stratum, never the acceptance set [R:M1b-8];
    - the weather changed; `max == 0` (predicted immune); outside the whitelist (by tier); wild vs trainer.
  - **Crit ambiguity:** a crit is not readable after the turn, so a reading in (max, crit_max] is tagged "crit or
    under-prediction, ambiguous".
  - **The self-check:** on clean turns (no KO, and no heal or tick from an enumerated list: a held item present at
    BEFORE, a foe item action, drain, Leech Seed on us, and the end-of-turn ticks), Δ`gBideDmg[1]` equals the foe's HP
    difference. Pre-registered as 0 disagreements on named turns [R:M1b-4, SR-9].
  - **Outputs:** the raw `[DMGAUDIT]` line count beside the parsed count (FAIL on a mismatch); FAIL on the logger's
    30 MB cap marker [R:SR N2]; per stratum and per effect: max(observed − crit_max), max(observed / crit_max), the
    counts over crit_max + ACCEPT_MARGIN and over crit_max + M1a's bound, the hits below the non-crit min (step 12's
    "progress" side), the self-check count; and an INDEPENDENT control: every clean BEFORE record replayed through
    M1a's port, with the observations outside the port's [min, crit_max] counted [R:SR-7].
  - **The acceptance verdict** (the data is step 14's): ≥ 300 clean whitelisted hits, 0 over crit_max +
    ACCEPT_MARGIN; fewer than 300 is "insufficient", never PASS.
  - **`probe_dmgaudit.py`, the pure gate [R:SR-2, SR-8]:** rows EXECUTE the classifier on synthetic BEFORE/AFTER
    records: one per stratum reason, the battle-end pair, the trainer-KO pair, a turn gap, a double BEFORE, a changed
    PID, unchanged PP, a chosen move ≠ the slot whose PP dropped, a negative Δ, a bide/HP disagreement; and the
    acceptance: one clean sample at crit_max + ACCEPT_MARGIN + 1 → FAIL, the same in an excluded stratum → PASS,
    exactly at the bound → PASS, 299 samples → "insufficient". AST rows pin production: the category, no new
    `get_battle_state()` call in BAS, the flag read site, and nothing in BAS emits `DMGAUDIT` with the flag unset.
    Mutants with sets written before the first run.
- **F5, the flag is kept, against the step-T precedent (06:7902-7917, applied again at 06:8248-8272) [R:SR-11].**
  - The difference: M1b reads memory inside the shared selection generator of EVERY battle (06:4555-4559), where a
    defect costs every fight; step T's reads sat per catch and per heartbeat. The flag gives a SAME-HEAD inertness A/B
    (v2 [A-S10]) and a switch-off without a revert.
  - "It is just a way to forget it" is met by step 14's runbook, which sets it in both arms by name.
  - Rejected: always on from the first commit. Deferred: always on after step 14 proves it inert at scale.
  - `29` rows for the flag and for any fault env, in the commit that first reads each (`lint_docs` R6 checks both
    directions, including `tools/story-dev`) [R:SR N1].
- **F6, the Step-0 live reads, BEFORE the predictions** (observe-only; a scratch driver, nothing in production). ⚠ All
  from the decomp:
  - `gBideDmg[1]`'s difference equals the foe's HP difference on a clean non-KO hit, and holds the uncapped roll on a
    KO;
  - `gChosenActionByBattler[0]`/`gChosenMoveByBattler[0]` are final at the selection exit;
  - the turn counter's VALUE at a battle-end read equals BEFORE's (F4's pairing) [R:SR-1];
  - `gBattleMons[0]` and `[1]` (our PP too) and `gBideDmg` are readable at the battle's end [R:SR-1];
  - the Flash Fire dereference reads a sane value.
  - If `gBideDmg` fails, F4 falls back to the HP difference and faints become a censored stratum.
  - ✅ **RESULTS (2026-09-30, `evidence/2026-09-30-dmgcalc11-STEP0.txt`; an observe-only probe at the base code,
    post_mtpyre, 90,000 frames, 101 reads, 0 failed).** Every question held:
    - Q1: Δ`gBideDmg[1]` = the foe's HP difference on 6 of 7 clean singles turns. The 7th is the MASKED HEAL (Marcel's
      Manectric reads 18 → 18 while our hit dealt 65, because the foe used its Hyper Potion first): `gBideDmg` records
      the hit, the HP difference cannot, and the foe's item action is READABLE at the selection exit
      (`gChosenActionByBattler[1] == 1`).
    - Q2: the uncapped roll on every KO: 7 of 7 battle-end KOs (a Linoone at 8 HP took 73) and 3 of 3 trainer KOs
      whose foe identity changed.
    - Q3: the chosen move is final at the exit: its PP drops by 1 when it ran, by 0 on our sleep turns; PP down with
      Δ`gBideDmg` 0 is a miss (Take Down vs Double Team).
    - Q4: the turn counter is EXIT + 1 at the next entry, and EQUAL to EXIT's at a battle's end (0 violations).
    - Q5: `gBattleMons` is readable at all 14 battle-end reads.
    - Q6: the Flash Fire flags read `[0, 0]` at every selection entry and exit, and `gBattleResources` is NULL at every
      battle-end read (freed). ⇒ **The battle-end AFTER read must not dereference it.**
  - ⚠ **FOUND BY THE FIRST LIVE AUDIT (a 50,000-frame smoke with the flag on, 2026-09-30): a faint RESETS the foe's
    `gBattleMons` record.** At a battle-end AFTER read after a KO, the foe's ability byte (0x20) reads 0, and on
    Vanessa's Pikachu the stat stages were reset to neutral and the held item (0x2E) was cleared. A classifier that
    compares the foe's record between the reads therefore excludes EVERY KO pair as "changed", which is exactly the
    evidence B4 keeps. ⇒ **When the foe fainted (its HP after is 0), F4 applies no per-mon foe comparison at the AFTER
    read**; like a trainer KO, it keys on the foe's chosen move ("foe-after-unobservable") and on our side's checks.
- **F7, inertness and correctness (M1b), on `post_mtpyre.ss1` (PINNED, md5 asserted), `storyresume --frames 90000`,
  seeded, at the SAME HEAD.** The runner writes `git rev-parse HEAD` and "clean tree" into each evidence file (a
  worktree log cannot) [R:SR N3].
  - **The decision rule, pre-registered [R:SR-5, M1b-11a]:** the two OFF runs must match each other first (else a
    third); each ON run must equal a reproducing OFF run on every frame-stamped line that does not contain
    `DMGAUDIT`, and the report names the first difference; a lone divergent run is re-run, never graded.
  - **The category rules [R:SR-3]:** OFF has 0 lines containing `DMGAUDIT`; in ON every such line matches
    `^f\d+ \[DMGAUDIT\] `, and no `[BATTLE]` line contains it.
  - **Non-vacuity, pre-registered from the OFF runs at the base [R:M1b-3, M1b-5, SR-4]:** a `CTL` line; at least one
    ACCEPTED whitelisted hit whose Δ`gBideDmg[1]` equals the foe's HP difference; at least one battle-end KO pair
    [R:SR-1]; at least one doubles stratum (Route 123); a held-item stratum (Vanessa's Pikachu holds an Oran Berry,
    deterministic at BEFORE); the named turns of the self-check. (The review found that two of the three item
    events the first version cited never fire in the committed runs: a one-hit KO, and an HP above the AI's quarter
    threshold.)
  - **A per-turn expected-verdict table [R:SR-2b]**, pre-registered with its FIELDS (foe species, HP before and
    after, verdict), derived from the OFF runs' `[TURN]`/`[TRAINER]` lines, graded line by line.
- **F8, the consequence for step 12, stated so it is not lost [R:SR-12, SR-13].** While D1 stands, "0 over crit_max +
  3" can fail on correct play (about 1/512 per STAB-4× hit). So:
  - MARGIN is split: **ACCEPT_MARGIN** (the acceptance's slack) and the weaken bound's own margin (v2:628's "+3").
    Re-setting one must not silently widen the other (the second is a behaviour change).
  - Step 12's stage 2 **stays OFF** (v2:630 already), and its L1/L2 wait, until EITHER `#27-dmgcalcfix` fixes D1
    with its flag ON in BOTH of step 14's arms (otherwise step 14 measures the unfixed calculator; else a second
    batch), OR the user re-sets ACCEPT_MARGIN from M1a's bound. v2 §3's numbers are "PROPOSALS for the user".
  - The exact absorption (⚙, W = 1; W is undefined in the tree): ceil(1.1·c) + 3 − c ≥ 4 for every c ≥ 1, equal to 4
    up to c = 10, so D1 alone uses the whole slack; D1 + Charge (8) needs c ≥ 41. The acceptance being STRICTER than
    step 12's bound is deliberate: do not "harmonise" it the wrong way.
- **F9, what step 11 owes step 12, beyond the verdict:** the whitelist (F2), the per-effect error distributions (F4)
  to re-derive CALC_ERR and the margins, and the lower tail (hits below the non-crit min).
- **F10, the docs this revision corrects [R:SR-10]:** the KI-109/110/111 vehicle lines (→ `#27-dmgcalcfix`); the new
  item in `03`; supersede markers at v2's §Step 11 and its §3 M1b row; `03` and `04` point to THIS note first.

## THE ARMS (to pre-register after the Step-0 reads)

| Arm | What | Pass |
|---|---|---|
| G-M1a | `probe_damage_calc_decomp.py` | the anchor literals hold on port AND calculator; bounds ≥ the anchors, then exact; every row's three literals; mutants red on their sets; under 300 s |
| G-AUDIT | `probe_dmgaudit.py` | every classifier and acceptance row; the AST pins; mutants red on their sets |
| M1b-OFF ×2 | post_mtpyre, DMGAUDIT unset, seeded, same HEAD | the two match each other; 0 lines containing `DMGAUDIT` |
| M1b-ON ×2 | the same, DMGAUDIT `1` | each equals a reproducing OFF run on every line without `DMGAUDIT`; the category rules; non-vacuity; the per-turn verdict table |
| M1b-FAULT | ON + a fault that reads `gBideDmg[0]` in place of `[1]` | the self-check count > ON's pre-registered 0, on the named turns |
| M1b-DIFF | the old BAS module (`git show 241929d7:`) vs the new, flag unset, both driving the real generator through `repro_ki46_action_selection_bound.py`'s fake readers | identical yields and lines; the same number of `get_battle_state()` calls with the flag on and off [R:SR-6] |
| M1b-EXEC | the new BAS code run with its `except` removed | it runs (08: a recorder that never ran inside a swallowing `try`) |
| M1b-AUDIT | `audit_damage_calc.py` on the ON arms | raw count = parsed count; strata printed; the independent port control reported |

## OPEN, NOT DECIDED HERE

- ACCEPT_MARGIN (F8): the user's, once M1a has measured the bound, shown with the ~1/512 rate.
- Whether `#27-dmgcalcfix` comes before step 14 (with its flag ON in both arms) or after (a second batch).
- A mid-turn read that would make the crit and the move order observable (UNVERIFIED feasibility; not needed).

## THE DESIGN REVIEW (three fresh Claude agents, 2026-09-30; their output is a NOTE, and the author checked each blocker at its cited line before folding it)

- **Blockers (4), all folded:**
  - M1A-1 / SR-7: the bound could not fail (a port in our order passes). → Hand-derived anchors; bounds asserted.
  - M1b-1 / SR-1: KO samples were zero by construction. The turn counter does not move on a battle's last turn (✔
    `battle_main.c:3988-3997`), and a trainer's replacement changes the identity. → F4's pairing.
  - SR-2: no arm checked that M1b was CORRECT, only that it was inert, present and parsed. → Raw production (F3), a
    pure classifier with its own gate (F4), a per-turn verdict table (F7).
- **Should-fix, all folded (marked in place):** M1A-2 to M1A-9 (real objects, badges per row, the fourth bucket, the
  enumeration drives production, three-literal rows, a non-vacuous immunity row, False Swipe/Endure/Focus Band, the
  sports); M1b-2 to M1b-12 (hits vs misses, a baseline for the fault arm, the item strata, the clamp, the pinch dip,
  persistent divergences, the other writers of `gBideDmg`, the foe's side, the KI-112 rule, where BEFORE lives); SR-3
  to SR-15 (the category rules, F3/F7 consistency, the decision rule, the differential and execution arms, the audit's
  fault rows, the claim that was not true, the flag's read site, the headline's caveat, the margin split and sequencing,
  misses, Liquid Ooze).
- **Checked and found TRUE by the review:** B1's two orders and the 1/4/8 bounds (reproduced three times); B3; the
  selection exit is final and frame-safe; the AFTER object is reusable; the symbols and the 0x13 offset; `gBideDmg`
  before the cap and blind to heals and ticks; `types.json` equals the ROM chart; the real calculator runs offline on
  synthetic records; the Tier C scripts; 06's precedents as cited; no user ruling contradicted.

## AS BUILT (2026-09-30, the build commit; the live arms are graded in a separate note)

⛔ **The build is gated, not graded.** Nothing below says the calculator is accurate enough for step 12: that is M1b's
acceptance, on the live arms, still to run.

- **Production (F3), `sandbox-pokebot/modules/dmgaudit.py`, OFF unless `POKEBOT_R25_DMGAUDIT=1`.** Four hooks, each
  reading the flag on every call and catching its own errors into ONE `ERR` line:
  - `on_battle_start` (the `CTL` line) and `on_battle_end` (`AFTER kind=end`) in `battle_handler.handle_battle`;
  - `on_selection_entry` (`AFTER kind=entry`) and `on_selection_exit` (`BEFORE`) in
    `battle_action_selection.handle_battle_action_selection`.
  - Only pure `read_symbol` reads, and no `get_battle_state()` (KI-108). The prediction reuses the handler's own
    object and is computed for the move the GAME records as chosen.
  - `base=` (the calculator's own base term, plain and crit) is logged beside `pred=`, so the audit can replay the
    decomp-ordered port from the live base: SR-7's independent control, live.
  - Three things were added while building:
    - an absent left battler (a fainted slot in a double) logs `pred=err:Absent`;
    - every early return logs `base=none` (the audit gate's PIN-b6 caught its omission);
    - the battle-end read never dereferences `gBattleResources` (F6 Q6).
  - The fault arm `POKEBOT_R25_FAULT_DMGAUDIT_BIDE0` copies slot 0's `gBideDmg` into slot 1.
  - Both envs have `29` rows.
  - The line format is `2026-09-30-dmgcalc11-recon/m1_line_format.md` (v=1).
- **M1a (F1): `tools/story-dev/dmgcalc_port.py` + `probe_damage_calc_decomp.py`.**
  - The port follows the decomp's order and embeds `gTypeEffectiveness` in TABLE order.
  - The gate has 45 rows and 38 mutant cases. Every pre-registered literal (`…-PREDICTIONS.md`) and all four bucket
    bounds reproduced EXACTLY.
  - It runs in ~71-73 s with a process pool. ⚠ **Its no-pool fallback measured ~295 s, at the suite's 300 s limit:**
    a known limit, recorded, not fixed.
- **M1b's audit (F4): `tools/story-dev/audit_damage_calc.py` + `probe_dmgaudit.py`.**
  - The audit is pure: a strict v=1 parser, F4's pairing, the classifier, F2's whitelist tiers, the port control
    through `base=`, and the acceptance.
  - `ACCEPT_MARGIN = 3` is printed as a PROPOSAL for the user (F8).
  - Its exits: 0 PASS, 1 FAIL, 2 INSUFFICIENT, 3 the instrument failed.
  - The gate has 177 rows and 193 mutants, and a COVERAGE row fails if a row is in no mutant's set. It runs in ~12 s
    with a pool, ~56 s in-process.
- **Two classifier rules the design did not have:**
  - the FAINT RULE (the ⚠ paragraph under F6; found by the first live smoke,
    `evidence/2026-09-30-dmgcalc11-SMOKE.txt`);
  - Hidden Power's ROLLED type drives the sport and pinch checks (found by the audit gate's adversarial pass).
- **One pre-registered verdict moves under the faint rule, inside what the table allowed.**
  - Marcel's Shiftry at f3193320 chose Harden and fainted.
  - The table said "ACCEPTED if our hit came first, else excluded: the foe's Def stage changed (either is correct; the
    read decides)". The faint reset erases that Def-stage read.
  - It is now EXCLUDED, with the reason keyed on the chosen move (`foe-after-unobservable`).
  - The expected accepted count on a reproducing run becomes 9, inside the predicted 7 to 10.
  - The graded note must state this reason change; it is not a new prediction.
- **Both adversarial mutant passes were folded into the gates**
  (`evidence/2026-09-30-dmgcalc11-ADVERSARIAL-{M1A,AUDIT}.txt`):
  - **M1a: 72 mutants.** The load-bearing finding for `#27-dmgcalcfix` was three planned fixes (Guts, Brick Break,
    KI-110) that each had a destructive twin with identical output on every row. The new rows B-BURN, B-REFL and
    B-KI110-SPA tell each pair apart.
  - **The audit: 107 mutants, of which the first gate MISSED 96.** 36 rows and 105 of the pass's mutants were added.
- **M1b-DIFF and M1b-EXEC** (`evidence/2026-09-30-dmgcalc11-DIFF.txt`) passed, in a form equal to or stronger than the
  arms table:
  - the new modules equal the base as ASTs once the hooks are removed;
  - with the flag unset, zero reads and zero logs;
  - with the flag set, zero `get_battle_state()` calls, and the exact CTL/BEFORE/AFTER sequence, which proves each hook
    body ran to its log call.
- **The full suite: ALL 134 ENFORCING GATES PASS in 469.3 s** (`evidence/2026-09-30-dmgcalc11-GATES.txt`).
