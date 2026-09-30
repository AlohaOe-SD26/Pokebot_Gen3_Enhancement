# 2026-09-30 — design v2 step 12 (weaken-to-catch): PRE-REGISTERED PREDICTIONS, filed BEFORE any production code

⚠ Filed against `2026-09-30-weaken12-DESIGN.md` (revised after its three-lens review). **The W-row table below is
filed BEFORE the pure module exists** [review ADV-B1]. The builder must implement these rows with these verdicts. Any row
whose verdict the builder believes is wrong is REPORTED and argued; it is never silently changed. The live-arm section is
filed after the Step-0 reads, and before the production code.

## THE W-ROW TABLE (the pure gate `probe_weaken_catch.py`; module `modules/story/weaken_catch.py`)

**Default snapshot S0** (every row changes only what it names):
- **Battle:** a wild single battle (no battle-type flag); kind `team`; the context's `sp` matches, and the PID is fixed;
  `POKEBOT_R25_WEAKEN=1`, CALC unset; the turn read = 0; no caps spent; bag: Poké Ball ×30.
- **Target:** Taillow, L6, catch rate 200, max HP 22, hp 22, no status/status2/status3. Moves: Peck (contact), Growl,
  Focus Energy, Quick Attack (contact). Live ability Guts (= the species'), types Normal/Flying, no item. No Safeguard,
  no Uproar, no weather.
- **Our lead:** Mudkip L13, ability Torrent, no item. Raw slots: Tackle 31, Seismic Toss 20, Mud-slap 10, Water Gun 7.
  No Encore, Torment, Disable or Taunt.
- **Our other party members,** all able to battle: Poochyena (Run Away), Nincada (Compound Eyes), Whismur (Soundproof).

**Hand-derived anchors**
- `catch_p(200, Poké, 22/22, none)`. odds = 200·(66−44)//66 = 66; 16711680//66 = 253207; isqrt = 503; isqrt = 22; b =
  1048560//22 = 47661; p = (47661/65536)^4 ≈ 0.2797, so E ≈ 3.575.
- At hp 9: odds = 200·48//66 = 145; 16711680//145 = 115253; isqrt 339 → 18; b = 58253; p ≈ 0.6243, so E ≈ 1.602.
- ⇒ Seismic Toss (X = 13): hp − X = 9; progress 13 ≥ 2.2; E_gain ≈ 1.97 ≥ 1.0 ⇒ **DAMAGE**. The builder re-derives each
  anchor by hand in the gate, with integer arithmetic exactly as `battle_script_commands.c:9987-10028`.

| Row | Change from S0 | Expected verdict (reason) |
|---|---|---|
| W01 | none | DAMAGE(slot 1, Seismic Toss) (stage1-exact) |
| W02 | the flag unset | DEFER (off) |
| W03 | kind `hm` | DEFER (kind) |
| W04 | the context's `sp` ≠ the opponent's species at the first decision | DEFER (context) |
| W05 | a later decision with a different PID | DEFER (pid) |
| W06 | a later decision, same PID, different species (Transform) | THROW (transformed) |
| W07 / W08 / W09 / W10a / W10b | the TRAINER / DOUBLE / LEGENDARY / ROAMER / SAFARI flag | DEFER (battle-type) |
| W11 | our item a Choice Band | DEFER (choice) |
| W12 | our disable struct: Encore move at 0x06 set | THROW (encore-on-us) |
| W12b | 0x04 (disabledMove) set with a timer, and 0x06 = 0 | THROW (disabled), NOT "encore": this pins the offset |
| W14 / W15 | our Torment / the target's Imprison | THROW |
| W16 / W17 / W18 | the target semi-invulnerable / behind a Substitute / confused | THROW |
| W19 / W20 / W21 | the target poisoned / Leech Seeded / our Future Sight pending on its side | THROW (ticking) |
| W22 | the target knows Self-Destruct, no Damp | THROW (explosion) |
| W23 | the same, with our lead's Damp | THROW (no-damage self-harm, and no status move) |
| W24 / W25 / W26 / W27 | the target knows Teleport / Roar / Perish Song / Memento | THROW (ender) |
| W28 / W29 / W30 / W31 | the target knows Metronome / Mirror Move / Assist / Sleep Talk | THROW (calling) |
| W32 | the one-throw chance ≥ 0.5 (a Great Ball and the target at 30%) | THROW (odds) |
| W33 | a DAMAGE verdict at turn 0; now turn 1 | THROW (damage cap) |
| W33b | decide twice in the SAME turn after a DAMAGE verdict at that turn | DAMAGE again (same verdict, no second cap spent) |
| W34 / W35 / W36 / W37 | the target knows Take Down / Belly Drum / Thrash / Jump Kick | THROW (self-harm) |
| W38 / W38b | a GHOST target knows Curse / a non-Ghost target knows Curse | THROW / DAMAGE |
| W39 | the target knows Encore | THROW (encore-knower) |
| W40 / W40b / W40c | the target knows Transform / Mimic / Sketch | THROW (acquires) |
| W41 / W41b | the target knows Sandstorm (Normal/Flying) / the same target Ground-type | THROW / DAMAGE |
| W42 / W42b | the target's total PP 60 / 70 (H = 2·(30+4) = 68) | THROW (struggle) / DAMAGE |
| W43 / W43b / W43c | sandstorm on / on with a Ground target / on with our Cloud Nine | THROW / DAMAGE / THROW |
| W44 / W44b | a party member (not the lead) with Rough Skin; the target knows a contact move / it knows none | THROW / DAMAGE |
| W45 | a party member with Liquid Ooze; the target knows Absorb | THROW |
| W46 | a party member with Synchronize | THROW |
| W47 | Seismic Toss at PP 0 | THROW (no usable damage move) |
| W49 / W49b | a Ghost target / the same with Foresight on it | THROW (immune) / DAMAGE |
| W50 | Night Shade in slot 1, a Normal target | THROW (immune) |
| W51 | a Wonder Guard target with max HP 1 | THROW |
| W52 | the target at hp 11/22 (not > 50%) | THROW (half) |
| W53 | Dragon Rage in slot 1 (40 ≥ 22) | THROW (floor) |
| W54 | Sonicboom, a target with max HP 250 at hp 250 (20 < 25) | THROW (progress) |
| W55 | Sonicboom, a rate-255 target, max 100, hp 100 (E_gain ≈ 0.98) | THROW (egain) |
| W56 | Super Fang (X = 11 at hp 22) | DAMAGE |
| W57 | our lead has Sing in slot 2 and no damage move usable (Seismic Toss at PP 0) | STATUS(Sing) |
| W57b / c / d / e / f / g | as W57, with: the target's live Soundproof / Uproar on any battler / live Insomnia / the target already paralysed / Safeguard on its side / Taunt on us | THROW |
| W57h | as W57, 3 status tries spent | THROW (status cap) |
| W57i | as W57, the target holds a Chesto Berry | STATUS(Sing) (a berry is a try) |
| W57j | as W57, the target knows Magic Coat | THROW |
| W58 / W58b | Thunder Wave only; a Ground target / an Electric target | THROW / STATUS |
| W58c / W58d | Glare only; a Ghost target / the same with Foresight | THROW / STATUS |
| W58e / W58f | Thunder Wave only vs Synchronize (no ender) / Thunder Wave AND Sing vs Synchronize | THROW / STATUS(Sing) |
| W59 | Seismic Toss AND Sing, target at full HP | DAMAGE (damage before status) |
| W60 | as W57, Sing in `banned_moves` | THROW |
| W61 | bag: Master Ball ×1 + Poké ×30; the target at 30% (THROW) | THROW uses the Poké Ball |
| W62 | WEAKEN=`observe` | the parent's action, unchanged; one `[WEAKEN-OBS] would=DAMAGE … first=1` line |
| W63 / W63b | CALC unset / CALC=1; Seismic Toss at PP 0, Tackle admissible by the calculator's bound | THROW / DAMAGE(Tackle) |
| W64 | CALC=1, as W63b, our lead burned with Guts | THROW (divergence) |
| W65a-e | the ADAPTER on the REAL classes: (a) the dex reserve bail fires first; (b) the out-of-balls flee fires first; (c) an exception in the module → DEFER plus exactly one `[WEAKEN] ERR` line; (d) the flag unset → 0 lines containing `WEAKEN` and the parent's action; (e) the shiny strategy never reaches the adapter | as stated |
| W66 | AST pins: no `get_battle_state` in the adapter; the adapter after the flee and before `super()`; the three construction lines unchanged from `cdb49f83` | as stated |
| W67 | `catch_p` anchors: the two above; sleep ×2; paralysis ×15//10; odds > 254 → 1.0; the Nest Ball at L6 (bonus 34); the Net Ball vs a LIVE Bug type; the Timer Ball at turn 5 (bonus 15) | hand-derived values |
| W68 | any snapshot | the module never returns an item other than a ball (RULING 27) |

**Faults** (production envs; each builder writes its EXACT red set before its first run; a COVERAGE row):
- `POKEBOT_R25_FAULT_WEAKEN_NOFLOOR` (skip hp − X ≥ 1): must redden W53.
- `…_NOENCORE`: W39.
- `…_CALCLEAK`: W63.
- `…_ACTIVEONLY` (retaliation read off the lead only): W44, W45, W46.
- `…_NOPP`: W47 and W57's premise.
- `…_MASTERBALL` (the best ball by `catch_p`): W61.
- `…_SPECIESID` (identity by species): W05, W06.
- `…_NETGAIN` (the netted E_gain): W01 and every DAMAGE row whose net gain < 1 ≤ its gross gain.
- `…_NAMEDISPATCH` (exact damage by NAME): must redden at least the Sonicboom rows. `moves.json` spells it "Sonicboom",
  the calculator "Sonic Boom" [review ADV-S10].
- Plus the adversarial mutant pass's own.

## THE LIVE ARMS (filed after the Step-0 reads, before any production code)

**The Step-0 reads** (`tools/story-dev/evidence/2026-09-30-weaken12-STEP0.txt`; commit `da6437b5`, the BASE code):
- The command: `r20_pregym1_party4_r116.ss1` (md5 asserted), TEAM6=1, DMGAUDIT=1, `--set-balls 30`, 240,000 frames,
  seed 1.
- The six runs were interleaved NL1, ST1, DR1, NL2, ST2, DR2, so each pair was SEPARATED IN TIME by two other runs.
- **Every pair is IDENTICAL on its non-DMGAUDIT frame-stamped lines.** That is a determinism check: one trajectory per
  lever, replayed.
  - NL: 1432 lines, sha `e444a33991bd7720`.
  - ST: 1434 lines, sha `cbfc30a354dc1722`.
  - DR: 1620 lines, sha `414d58ba95536d55`.
- ⇒ They ARE the design's ST-OFF ×2 and DR-OFF ×2.
- ⇒ **NL ×2 stands in for W-BASE ×2**: it IS the base code, run before any production change. That substitution is
  stated here, before the code. `run_with_base_modules.py` remains the tool if a later divergence needs attributing.

**The in-scope decisions on the three trajectories** (every catch battle is kind `team`; no shiny, hm or counter battle;
8 trainer battles in each):
- **NL:**
  - Taillow L6 22/22, turns 0-6 (7 decisions), lead Mudkip L15 [Tackle, Growl, Mud-slap, Water Gun]. Caught at f165755.
  - Abra L7, 1 decision (Teleports).
  - Skitty L7 25/25, 3 decisions, lead Marshtomp L17 [Tackle, Mud Shot, Mud-slap, Water Gun].
  - ⇒ **11 in-scope decisions.**
- **ST** (the lever: Growl → Seismic Toss in slot 1): the FIRST in-scope decision is **f165971** (the `[TURN 0]` line).
  - The lead is Mudkip **L15** at 21/44, with Seismic Toss at **PP 2** (the fight strategy spent the rest in trainer
    battles) and Water Gun at PP 0.
  - The target is Taillow L6 **21/21**, rate 200, live ability Guts, moves Peck, Growl, Focus Energy (total PP 105),
    no item, no status.
- **DR** (the lever: Growl → Dragon Rage): the FIRST in-scope decision is **f140685**. The lead is Mudkip L14 at 39/42
  with Dragon Rage at PP 8; the target is the same Taillow, 21/21.
  - Then 11 Abra battles (f147598 … f233063), each 1 decision.

**The discriminators, computed** (the design's rules, integer `catch_p`, the Poké Ball):
- **ST at f165971:** X = 15.
  - hp − X = 6 ≥ 1; 21 > 10.5; progress 15 ≥ 2.1; PP 2 > 0.
  - No immunity: Fighting against Normal/Flying.
  - No self-harm: Peck, Growl and Focus Energy; total PP 105 > H = 2·(31 + 4) = 70.
  - No retaliation in our party (Torrent, Run Away, Compound Eyes, Soundproof); no weather.
  - `catch_p(21/21)`: odds 66 → p ≈ 0.2797, E ≈ 3.575. `catch_p(6/21)`: odds 200·51//63 = 161; 16711680//161 = 103799;
    isqrt 322 → 17; b = 61680 → p ≈ 0.7846, E ≈ 1.275.
  - E_gain ≈ 2.30 ≥ 1. One-throw 0.28 < 0.5.
  - ⇒ **DAMAGE(slot 1, Seismic Toss).** ST-OFF throws there (UseItem).
- **DR at f140685:** 40 ≥ 21, so hp − X < 1 and the floor BINDS. The lead has no status move ⇒ **THROW**, the same
  action as DR-OFF.
  - Every Abra decision: THROW (ender).
  - ⇒ **ON takes the OFF action at EVERY in-scope decision of the DR trajectory.**
- **DR-FAULT at f140685:** the floor is skipped; E at max(hp − 40, 1) = 1 gives E ≈ 1.275, so E_gain ≈ 2.30 ⇒ DAMAGE
  (Dragon Rage). 40 ≥ 21 ⇒ **the Taillow faints.**

**Per-arm predictions** (all on the BUILD; every arm DMGAUDIT=1; every comparison over frame-stamped lines without
`WEAKEN` or `DMGAUDIT`; step 11's decision rule, D15):

| Arm | Predicted |
|---|---|
| G-W | every W-row and fault as filed above; COVERAGE; under 300 s |
| W-OFF ×2 (flags unset, separated in time) | each = NL Step-0 on every line (sha `e444a33991bd7720`), so the build with flags unset changes NOTHING against the base; 0 lines contain `WEAKEN` |
| W-OBS | = W-OFF on every line without `WEAKEN`. **Exactly 11 `[WEAKEN-OBS]` lines**, one per in-scope decision, each `would=THROW`: Taillow and Skitty have no stage-1 move, and Abra is an ender. 0 `first=1`. 0 OBS lines outside the three catch battles (8 trainer battles). Each OBS line's target HP/max, status and moves equal DMGAUDIT's raw record at that turn. |
| W-OBSCALC | the same 11 lines, each `would=THROW`. Every plain hit's ub ≥ the target's HP at L15-17 vs L6-7; Mud-slap is 0 against the Flying Taillow. ⚠ A `would=DAMAGE` here would be a RESULT (a stage-2 decision), reported, not explained away. |
| ST-ON | = ST-OFF up to f165971. There: `[WEAKEN] act=DAMAGE` (Seismic Toss); DMGAUDIT's BEFORE shows `mv[0]` = 69; the AFTER shows Δbide[1] = **15** and the Taillow at **6**/21; not KO'd. Every later decision in that battle: THROW (the damage cap). Anywhere later (the trajectory diverges after the hit): every DAMAGE verdict is Seismic Toss with Δbide = the lead's level exactly and no KO. **0 `res=Won` in any catch battle.** |
| DR-ON | **= DR-OFF on EVERY line without `WEAKEN`, for the whole run** (ON takes OFF's action at every decision). At f140685: `act=THROW` with the floor as its reason. 0 `res=Won`. |
| DR-FAULT (`POKEBOT_R25_FAULT_WEAKEN_NOFLOOR=1`) | = DR-OFF up to f140685. There: DAMAGE (Dragon Rage), BEFORE `mv[0]` = 82, Δbide[1] = 40, and `[CATCH] end kind=team sp=Taillow#276 … res=Won`. If this does not happen, the arm FAILS (no vacuity exit). |

**Falsifiers:**
- a W-OFF line differs from NL Step-0;
- a `WEAKEN` line appears with the flags unset;
- an OBS line appears outside a team or dex catch battle, or the count ≠ 11;
- ST-ON does not act at f165971, or acts with Δbide ≠ 15, or a catch ends `res=Won`;
- DR-ON differs from DR-OFF anywhere;
- DR-FAULT does not KO.
- A fault or W-row whose red set differs from the one written before its run.
