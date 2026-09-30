# 2026-09-30 — design v2 step 11 (M1, damage-calculator fidelity): the DESIGN, after a five-angle recon

> A NOTE refining `2026-09-29-r23-27-DESIGN-v2.md` §Step 11. It supersedes that section where they differ.
> - The recon was a workflow of five fresh Claude agents: our calculator, the decomp transcribed, an adversarial
>   deviation hunt, the records and rulings, and the live state readers. A Gemini fan-out was used only for "what to
>   look for", and the decomp agent checked it against the decomp: names mostly right, placement and order mostly
>   wrong. Their reports are NOTES. The author re-read every load-bearing claim marked ✔ at the cited place. ⚙ marks
>   a number the recon computed that M1a must re-derive; ⚠ marks a claim not yet checked live.
> - Branch `wt/dmgcalc11`, cut from `main` `241929d7` (10b merged).
> - ⛔ **Nothing here is built yet.** The order is: this design, an adversarial review of it, the Step-0 live reads
>   (F6), predictions, code, gate, arms, review.

## WHY THE v2 STEP 11 BODY CANNOT BE BUILT AS WRITTEN

- **B1. The proposed acceptance fails by construction on CORRECT play.** v2 says "0 over crit_max + 3 HP" (v2 §3,
  M1b acceptance). Our calculator doubles for a crit AFTER STAB and type effectiveness:
  - ours: ✔ `_util.py:207-213` (STAB, then each type), then `:230-231` (crit ×2) and `:233-238` (Charge ×2);
  - the game: ✔ `battle_script_commands.c:1293-1301` (`Cmd_damagecalc`: base × `gCritMultiplier` ×
    `dmgMultiplier`, then Charge ×2, then Helping Hand), before `Cmd_typecalc`'s STAB (`:1369-1372`) and type steps
    (`ModulateDmgByType`, ✔ `:1321-1325`, a minimum of 1 per step), with the random factor last (✔ `:1639-1651`).
  - ⚙ Two recon agents, independently: crit_max reads up to **4 HP** low (a STAB crit against a 4× target with an
    odd post-base value), and up to **8 HP** with Charge; the non-crit max up to **1 HP** low.
  - Realistic 4× cases on the story path: Makuhita vs the Aron line, Marshtomp's Mud-Slap vs Magnemite, Electrike vs
    Wingull/Pelipper, Grass vs Barboach and Geodude. One such crit fails M1b "for good".
- **B2. "The whitelisted effects" are defined nowhere**, and `EFFECT_HIT` alone is not safe: Surf is `EFFECT_HIT` yet
  doubles against a diving target (recon: `battle_scripts_1.s:236-240`).
- **B3. `[TURN]` does not name the executed move.** It is logged before the no-PP override (✔ the emission at
  `battle_action_selection.py:534-538`; recon: the override at `:552-569`), and Encore can substitute the move. So
  M1b must predict for the move the GAME records as chosen, `gChosenMoveByBattler[0]` (✔ `pokeemerald.sym:156`,
  `02024274`), read at the selection exit.
- **B4. Excluding faints discards the evidence step 12 exists for** (KO-safety). ⚠ `gBideDmg[1]` (✔ `.sym:133`,
  `020241f8`) records our hit's damage BEFORE the HP cap and ignores heals, items, end-of-turn effects and weather
  chip (recon: `battle_script_commands.c:1912` vs `:1920-1929`). If it holds live, KO samples become valid.
- **B5. The spec evaluates the foe's status only before the turn**, but our own move can burn, poison, confuse or trap
  the foe THIS turn, and the end-of-turn tick lands in the same turn.
- **B6. KI-110 cannot be pinned in the direction M1 audits.** It changes only damage aimed at US
  (`defender_is_player`), so an our-attack row passes vacuously (KI-110's own "Reach today: none").
- **B7. A scope conflict in the record:** step 11 is "measurement only" (v2:23, v2:569; 03; 04), while KI-109, KI-110
  and KI-111 each name "v2 step 11" as their fix vehicle (05). 06 holds no user ruling on fixing the calculator and
  no "do not re-raise" (the records agent grepped it; CLAUDE.md rule 11).

## THE DESIGN (F1-F9; each also a `06` decision when built)

- **F1, scope: MEASUREMENT ONLY. `_util.py` is not changed in step 11.**
  - M1a pins every deviation as a KNOWN-DIVERGENCE row: the game's value from the decomp port beside ours, each with
    a decomp citation.
  - The fixes become a NEW item, `#27-dmgcalcfix`: KI-109/110/111, D1 (crit and Charge order), D2 (type order), D3
    (the per-step minimum), Marvel Scale on the wrong battler, Guts + burn, Psywave's minimum, fixed-damage immunity,
    Brick Break vs screens. It is behind its own default-OFF flag, with M1a as its gate and an A/B on the ORDINARY
    case, because `_util.py` is the every-battle path (06:4555-4559, 06:4595-4598). The KIs' "vehicle: v2 step 11"
    lines are corrected in the commit that files this design.
  - Why not fix in step 11: a KI-109 fix changes move choice (a behaviour change needs a flag and an A/B), and M1b's
    inertness proof is "every battle line identical", which cannot hold in the same step as a behaviour change.
- **F2, M1a: `tools/story-dev/probe_damage_calc_decomp.py`, a pure gate.**
  - A decomp-ORDERED port: base (the calculator's own base term, see below), × crit × `dmgMultiplier`, × Charge,
    STAB ×15/10, each type step in `gTypeEffectiveness` TABLE order with a minimum of 1, then the random factor
    `100 - r%16` for r in 0..15. It is a TEST ORACLE in `tools/` and never a production dependency (06:4606-4617
    rejected a second damage model in production).
  - **Enumeration, not sampling.** Past the base term, the error depends only on the post-base value B, STAB and the
    multiplier multiset. The probe sweeps B, STAB, crit, Charge and every (move type, defender type pair) from the
    ROM's type chart, and reports the maximum under- and over-prediction for the non-crit range, crit_max and crit
    with Charge. **Pre-registered:** non-crit 1 HP, crit 4 HP, crit + Charge 8 HP. ⛔ The defender's types come in
    ROM order (`gBattleMons` 0x21/0x22); `species.json` stores some in a different order (Aron, Lotad, Skarmory).
  - **Exact rows** executing the REAL `calculate_move_damage_range` (the playbook: execute production to pin wiring)
    on stand-ins that keep `BattlePokemon`'s contract. ⛔ A stubbed defender must NOT count as the player (recon:
    `battle_state.py:370-377` returns `NotImplemented`, which reads True, and would switch on KI-110's boost). Rows:
    the crit order (a worked 4× case); the type order (Bite vs Sableye, 1 HP); the per-step minimum (`max=0`, `min=1`
    on an immune or 0.25× tiny case); Marvel Scale on each battler; Guts + burn; Sonicboom and Psywave (KI-109; Psywave's
    minimum is level/2); fixed damage vs an immune type; Brick Break vs Reflect; Struggle; Hidden Power's type and
    power; KI-110 in the foe→us direction; KI-111 (Solarbeam's weather halving). Each expected value comes from the
    port and a decomp line, never from `_util`'s output.
  - **The whitelist, as a constant keyed on `moves.json` `effect`** (never on names: "Sonicboom", "Psywave",
    "Solarbeam", "Selfdestruct", "Doubleslap" and "Smellingsalt" are spelled that way in the data):
    - Tier A (plain, one hit, fixed power): HIT, HIGH_CRITICAL, ALWAYS_HIT, QUICK_ATTACK, VITAL_THROW, PAY_DAY,
      SECRET_POWER, SKY_UPPERCUT, THUNDER, KNOCK_OFF, THIEF, RAPID_SPIN, FLINCH_HIT, PARALYZE_HIT, FREEZE_HIT, the
      stat-down and stat-up *_HIT effects, SUPERPOWER, OVERHEAT, RECHARGE, DOUBLE_EDGE, RECOIL (not Struggle),
      RECOIL_IF_MISS, ABSORB, DREAM_EATER, FALSE_SWIPE, FAKE_OUT, FOCUS_PUNCH, SNORE, RAGE, HIDDEN_POWER.
    - Tier B (a secondary that can move the FOE's HP the same turn): BURN_HIT, BLAZE_KICK, THAW_HIT, TRI_ATTACK,
      POISON_HIT, POISON_TAIL, POISON_FANG, CONFUSE_HIT. In the whitelist only when the AFTER read passes F3's status
      exclusions.
    - Tier C (a conditional ×2 or a screen skip): Surf/Whirlpool vs Underwater, EARTHQUAKE vs Underground, GUST and
      TWISTER vs InTheAir, FLINCH_MINIMIZE_HIT vs Minimized, FACADE, SMELLINGSALT, WEATHER_BALL, BRICK_BREAK, PURSUIT.
      In the whitelist only while the condition is observably false at BOTH reads.
    - Everything else is out: multi-hit, dynamic power, fixed damage, OHKO, Counter/Mirror Coat/Bide/Endeavor,
      two-turn, Future Sight, trapping, EXPLOSION. They go to a logged stratum, never to the acceptance set.
  - Fault (the spec's): a synthetic row over crit_max + MARGIN must fail the probe. Plus the gate's own mutants, with
    sets written before the run, and a timing check against `run_gates`' 300 s limit (08, 2026-09-30).
- **F3, M1b: `[DMGAUDIT]` lines, observe-only, behind `POKEBOT_R25_DMGAUDIT=1`, in their OWN log category** (never
  `BATTLE`, never appended to `[TURN]`: v2 [A-S10]).
  - **BEFORE, at the selection exit** (the fall-through of ✔ `battle_action_selection.py:173`'s `while`), in the same
    frame, with PURE reads only (`read_symbol`; never `get_battle_state()`, KI-108): the turn counter, our and the
    foe's chosen action and move, a snapshot of `gBattleMons` for both battlers, `gStatuses3`, the weather, the side
    statuses and `gBideDmg[1]`. The prediction is the REAL calculator for `gChosenMoveByBattler[0]`: min and max, and
    crit_max with `is_critical_hit=True`.
  - **AFTER, at the next selection entry**, reusing the handler's existing `get_battle_state()` object (no new cached
    call), plus direct reads of the turn counter and `gBideDmg`; or at the battle's end if it ended that turn.
  - **A sample** is a pair with after-turn == before-turn + 1, singles only, our action USE_MOVE with a nonzero chosen
    move, our PID unchanged, the foe's (PID, species) unchanged, and the chosen move's PP down by at least 1 (it ran).
  - **The observed damage** is `gBideDmg[1]` after − before (primary: uncapped, blind to heals and ticks) and the foe's
    HP before − after (secondary). A self-check counts the turns where they disagree with no KO, heal or tick.
  - **Strata, never silent discards.** Every pair is logged with its verdict: in the whitelist or not (by tier),
    wild or trainer, and each exclusion reason, evaluated at BOTH reads: the foe's status, confusion, trap, Leech
    Seed, Curse or Nightmare; a Tier C condition; OUR side changed (HP crossed 1/3 with a matching pinch ability, an
    Atk/SpA stage rise, a status change with Guts or Facade, Flash Fire); the weather changed; the foe's chosen move
    hurts itself (recoil, crash, Substitute, Belly Drum, Ghost Curse, Pain Split, Explosion, Memento); our Rough Skin;
    a Substitute on the foe; `max == 0` (predicted immune).
  - **A crit is not readable after the turn** (recon: `gCritMultiplier` is overwritten by the next selection's AI
    scoring). A reading in (max, crit_max] is tagged "crit or under-prediction, ambiguous".
  - A `[DMGAUDIT] CTL` line at battle start proves the audit ran.
- **F4, `tools/story-dev/audit_damage_calc.py`.** It prints the raw `[DMGAUDIT]` line count beside the parsed count
  and fails on a mismatch (08: a `[TURN]` parser once dropped 13.5% of rows). Per stratum and per effect it reports:
  the maximum of observed − crit_max and observed / crit_max; the counts over crit_max + 3 and over crit_max + M1a's
  enumerated bound; the executed hits below the non-crit min (the "progress" side step 12 also needs); and the
  bide-vs-HP disagreement count. It computes the acceptance verdict, but the acceptance DATA is step 14's (v2).
- **F5, the flag is kept, against the step-T precedent (06:7902-7917), for reasons that differ from step T's.**
  - M1b adds per-turn memory reads to the battle-action path of EVERY battle; step T's telemetry sat off the
    per-frame path. The flag gives a SAME-HEAD inertness A/B (v2 [A-S10]) and a switch-off without a revert.
  - The worry "it is just a way to forget it" is met by step 14's runbook, which sets it in both arms by name.
  - Rejected: always on from the first commit. Deferred, not rejected: always on after step 14's batch proves it
    inert at scale.
  - The flag gets its `29` row in the commit that first reads it (`lint_docs` R6, both directions).
- **F6, the Step-0 live reads, BEFORE the predictions** (observe-only; an ad-hoc driver or a probe, nothing
  committed to production). ⚠ All from the recon's decomp reading, none checked live:
  - `gBideDmg[1]`'s difference equals the foe's HP difference on a clean non-KO hit, and holds the uncapped roll on a
    KO;
  - `gChosenActionByBattler[0]` and `gChosenMoveByBattler[0]` are final at the selection exit;
  - the turn counter (`gBattleResults` + 0x13) and `gBattleMons[1]` are readable where F3 reads them, including at a
    battle's end.
  - If `gBideDmg` fails, F3 falls back to the HP difference with the spec's original exclusions, and faints become a
    censored stratum.
- **F7, inertness (M1b): a same-HEAD pair on `post_mtpyre.ss1` (PINNED, md5 asserted), `storyresume --frames
  90000`, seeded, DMGAUDIT unset vs `1`, at least TWO runs per arm (KI-112).** Every frame-stamped line except
  `[DMGAUDIT]` must be identical, and the report names the first difference.
  - Non-vacuity: the ON arm must hold a `CTL` line, at least one prediction line, at least one doubles exclusion and
    at least one item or AI-item stratum. The recon tabulated the fixture's battles: three doubles on Route 123;
    Vanessa's Oran Berry; Marcel's and Cristin's Hyper Potions; our Mightyena asleep for three turns; Hideo's Koffing
    that knows Self-Destruct.
  - Also: an offline differential of the battle-action module with the flag unset, and a G1c-style execution of the
    new code with its `except` removed (08: a recorder that never ran inside a swallowing `try`).
- **F8, the consequence for step 12, stated so it is not lost.** While D1 stands, "0 over crit_max + 3" cannot hold
  on correct play. Step 12's stage 2 is therefore blocked until EITHER `#27-dmgcalcfix` fixes D1, OR MARGIN is re-set
  from M1a's enumerated bound. MARGIN is one of v2 §3's numbers, all "PROPOSALS for the user", so the choice goes to
  the user. Step 12's own bound (`ceil(W·crit_max·1.10) + 3`) already absorbs D1 whenever crit_max ≥ 10 (⚙). The
  acceptance being STRICTER than step 12's bound is deliberate: do not "harmonise" it the wrong way.
- **F9, what step 11 owes step 12, beyond the verdict:** the whitelist (F2), the per-effect error distributions
  (F4) to re-derive CALC_ERR and MARGIN, and the lower tail (hits below the non-crit min).

## THE ARMS (to pre-register after the Step-0 reads)

| Arm | What | Pass |
|---|---|---|
| G-M1a | `probe_damage_calc_decomp.py` | every row as pre-registered; its enumerated bounds equal the predictions (1 / 4 / 8) or the difference is REPORTED as a result; its mutants red on their sets; under 300 s |
| M1b-OFF ×2 | post_mtpyre, DMGAUDIT unset, seeded | the control, run twice |
| M1b-ON ×2 | the same, DMGAUDIT `1` | every non-`[DMGAUDIT]` frame-stamped line = OFF's; non-vacuity (F7) |
| M1b-FAULT | ON + a fault that reads `gBideDmg[0]` in place of `[1]` | the self-check's disagreement count rises above 0 on clean turns (the reader is proven pointed at the foe) |
| M1b-AUDIT | `audit_damage_calc.py` on the ON arms | raw count = parsed count; strata printed; a fault arm (a dropped line) fails it |

## OPEN, NOT DECIDED HERE

- MARGIN (F8): the user's, once M1a has measured the bound.
- Whether `#27-dmgcalcfix` comes before step 12 (it unblocks F8's first option) or after.
- A mid-turn read that would make the crit and the move order observable (recon: UNVERIFIED feasibility). Not needed
  for F3.
