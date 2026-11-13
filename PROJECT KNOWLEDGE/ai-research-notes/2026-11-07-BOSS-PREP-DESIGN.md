# Boss preparation for the AI player (USER RULING 58): design and its adversarial critique, 2026-11-07 (NOT built)

> A NOTE, not a source of truth (`00-READ-THIS-FIRST.md`). USER RULING 58 (`06` 2026-11-07) is the authority: against a
> gym leader, boss or the Elite Four the party loses to, training the whole team, bringing a counter (judged by its
> typing's RESISTANCES and its MOVES' type advantages) and fighting smarter are all viable. Part 1 is one designer's
> design, written read-only against branch `wip/ch6-ch7` (`f299a1e7`); Part 2 is an independent adversarial critique
> of it. ⛔ **Fold the critique's MAJOR M1-M5 into the design before building** (M1: fixed-damage moves such as Seismic
> Toss ignore resistances; M2: USER RULING 44 lets the AI know bosses' held items; M3: evolution and future moves, for
> example C1's own Cascoon/Dustox; M4: raising a counter must not train the lead instead; M5: one bounded budget per
> boss for hunting, raising and training). The critic's simpler first slice (score each candidate against each boss
> Pokemon with the existing `move_value` both ways; first train the party's own evolvers) is the recommended start.
> Damage figures and catch odds in both parts are hand estimates, not measurements. The scratch helper scripts the
> designer used (`counters.py`, `levels.py`) are not kept.

## Part 1. The design (the designer, 2026-11-07)

### Boss preparation for the AI player: design (not built)

This is a design for USER RULING 58 (2026-11-07), which answers P4-1. It was read from the chapter 6-7 worktree
`.claude/worktrees/wf_e7452923-f06-3` at f299a1e7. Paths below are relative to its `ai_player/`, unless they start with
`s53/`, which is this session's scratchpad. Nothing here is built.

Every number is either cited to a file or marked as an estimate. Three things are NOT verified and are load-bearing:
- the Gen 3 type immunity of fixed-damage moves (§3, V1);
- my rough damage arithmetic (§1.7);
- my catch-odds arithmetic (§4).

#### 0. The headline, with its caveat

The base did not lose to BRAWLY because of the battle brain. It lost because nothing prepared the party for this boss:
- The training rule judged C1 "ready" by its strongest Pokemon's level alone.
- The AI knows nothing of BRAWLY's team before the fight.
- Two Pokemon it caught in the cave went to a PC box that it cannot use.

The smallest slice that could let C1 win is "a counter for the next boss". It has five parts:
- the static knowledge;
- a two-half counter score and a readiness verdict;
- a PC deposit;
- a hunt;
- the counter led and raised.

That is a prediction about one trajectory per seed, to be tested by the A/B in §4. It is not a measured result.

#### 1. What exists today

**1.1 How it picks a move.** `brain/battle.py:393` `move_value` gives each move a value. The value is:
- the move type's multiplier against the foe's types, times STAB, times power, times hit chance;
- minus a recoil penalty (`recoil_penalty`:364, `recoil_risk`:527; this is RULING 33's recoil).

It then makes a seeded draw among the moves within `near_best` of the best one (`choose_move`:1031, `TEMPERAMENTS`:208-215).

So it DOES use the type effectiveness of its MOVES. It does NOT use its own typing to choose a move.

**1.2 Its own typing.** Its own typing counts in only two places:
- STAB;
- `matchup`:554. This takes the foe's species types, plus moves the foe has USED, against the member's types, and scales the result by level.

`matchup` decides two things:
- switching (`better_member`:1302). It switches only when the Pokemon out is "badly matched": threat x2 or more, or its best move is worth less than half a neutral one;
- who goes in after a faint (`replacement`:1356).

In C1's fights Grovyle was never "badly matched" against Fighting types, which hit it for x1. And no member was "much better". So the switch rule could not fire.

**1.3 Switching and items in battle.**
- Switches: at most `MAX_SWITCHES` 2 a battle (:146).
- Heals: in a trainer battle only, below the personality's `heal_below`, at most `MAX_HEALS` 2 a battle (`_heal`:1340-1353). Story's `heal_below` is 0.30 (:211).
- There are no stat items (X Attack and the like), and no "lead with X" rule.

**1.4 How it trains.** The rule is in `brain/goals.py:1517-1539`.
- Before a NAMED fight (`fight_levels`:1767; for BRAWLY that is milestones.json `fight.levels [16, 19]`), it trains when `strongest_level(look)` (:545) is under `training_target` (:1782).
- `training_target` is the boss's max level plus `train_margin`: Story +1, Catcher +2, Trainer +3 (personality.py:153-162).
- Training is also bounded by `train_min_steps` and `TRAIN_SESSIONS` 8 (:259).
- Training roams TALL GRASS only (`grass_target`:758, `inside_grass`:753, `world/memory.py:317` `grass`).
- Only the LEAD fights, so only the lead gains levels.
- Two hands do not exist at all: a party reorder (`hands/menus.py` has none) and a PC (no eyes for the storage screen).

**1.5 When it gives up.** `mode.py:113` sets `MAX_LOSSES = 3`, counted across processes from the save (:793-830). At 3 losses the run stops (:1030-1040). Between losses nothing changes: it heals and talks to the leader again.

**1.6 What it knows of a boss's team.**
- `knowledge/atlas.py:83` `gym_leaders`: the leader's name and gym map. It reads only `role`, `name` and `battled_on`.
- The milestone's fight levels.
- In battle, the foe's species types (`seen_types`) and the moves it has used.

`world/bosses.json:705-760` already holds BRAWLY's party: MACHOP 16, MEDITITE 16, MAKUHITA 19, with their custom moves and types. `gates/check_fairness.py:274-305` classifies those keys `AI`. But no loader reads them.

The seasoned files `knowledge/seasoned/encounters.json` and `learnsets.json` are extracted and verified (`gates/verify_seasoned.py`). They are NOT in `LOADERS` (:79-90) or `KNOWLEDGE_FIELDS`.

**1.7 The evidence: C1's own log** (`s53/ch6probe11/out/probe11/probe11-B-C1-6365/ai_player.log`).

Fight 1 (L1211-1240):
- Grovyle L22 (moves Pound, Pursuit, Absorb, Quick Attack: worths 40/20/30/40) faced Machop L16 alone.
- It fell from 100% to 7% in three turns (L1213-1217), used a Potion (L1217), and fainted.
- Wurmple L3, Seedot L3, Shroomish L5, Poochyena L6 and Cascoon L5 each fell in one turn. Cascoon could only Harden (L1235).
- It never got past BRAWLY's FIRST Pokemon. Fights 2 and 3 repeat this (L1268-1298, L1329-1355).

Before the fights, in the cave:
- It met a Sableye five times (L611, L793, L804, L819, L961).
- It threw four Poke Balls at the first one, all missed (L614-621), and had no ball for the other four.
- It caught a Zubat L10 (L372-375) and a Makuhita L8 (L276-283). The party stayed the same six, so both went to a PC box.
- DEWFORD has no Mart (maps.json lists the gym, the hall, two houses and the centre).

A rough estimate (mine, not measured): with `TYPICAL_BASE` for Machop, Karate Chop does about 16 to Grovyle and Pound about 12 to Machop. That is about four hits each way, and the foe is assumed to move first. A rough verdict would therefore have said "not ready". Today's rule said "ready": L21-22 is at least 19+1.

#### 2. The three plans, as the AI would use them

All three are legitimate (RULING 58). The trigger, the score and the bounds are shared.

**2.0 The trigger and the verdict.**
- **Which boss is next.** The next boss is the leader of the lowest badge the AI does not hold. That comes from `bosses[].badge.id`, which is `AI`, and `Progress.badges`, which the trainer card shows. It does NOT come from `order` or `entry`, which are `DEVELOPER`.
- **The rival or a team boss.** For these, the boss is the current milestone's named fight.
- **When it judges.** At each milestone, and on arriving at a new map, it judges the party against that boss: the verdict (`brain/bossprep.py`, new).
- **What the verdict does.** For each boss Pokemon in order (species, level and moves from the static party; its stats are `TYPICAL_BASE` at its level, the step 4.1 rule), it finds the healthy member that wins that fight. It compares turns to knock the foe out (`rough_share`) against turns the member survives the boss Pokemon's best KNOWN move. The foe is assumed to move first, and stat boosts are ignored. HP carries over to the next boss Pokemon.
- **Ready.** The whole boss team falls with at least the personality's caution of party HP left (taste values, e.g. Story 0.25, Catcher 0.30, Trainer 0.40).
- **Not ready.** A plan is chosen.
- **After a LOSS** to that boss, the plan that was used is marked failed for that boss, and the next plan must differ: another counter, or another plan. The run never fights the same boss twice with the same plan and nothing changed. `MAX_LOSSES` stays the run's stop.

**2.1 (a) Train the team.**
- **Who trains.** One to three trainees: the members the verdict needs (the best counter score first, then the next-strongest), not only the lead.
- **To what level.** Each trainee is raised to its FIGHT LEVEL:
  - a full counter (both halves good): the boss's min level - 3;
  - otherwise: the boss's max level;
  - plus the personality margin.
- **Where.**
  - A map it knows and can reach whose static wild levels (encounters `min_level`/`max_level`) are near the trainee's.
  - Cave floor counts as roaming ground. Today only tall grass does, so the island had "no grass" (report NS4).
  - The trainee LEADS. That needs a reorder hand, because only the participant gains experience.
- **When it is ready.**
  - The verdict says ready, or every trainee reached its fight level.
  - The bound: a per-boss session cap, e.g. Story 8, Catcher 10, Trainer 14. Then it fights anyway, and the after-loss ladder takes over. It never grinds forever.

**2.2 (b) A counter.** Both halves (RULING 58) are scored against the boss's known team.
- **Resistance half.** The worst multiplier of the boss's damaging MOVE types on the candidate's TYPING. Fixed-damage moves (Seismic Toss, Night Shade) count x1 unless the typing is immune (x0); see V1. Example: Zubat resists Fighting x0.25, but Seismic Toss still does 16.
- **Move half.** For each boss Pokemon, the best multiplier x STAB of a damaging move the candidate WILL KNOW at its fight level. For a party member these are its real moves (the summary). For a wild species they come from its level-up learnset.
- **Classes.**
  - A full counter is strong on both halves.
  - Typing only is "half a counter". Abra at L8 resists Fighting x0.5 but knows only Teleport, so its move half is 0. It is not a counter until Kadabra's Confusion at L16.
  - Moves only is also half: Taillow, x1 typing and Peck x3.
  - A candidate weak to the boss (Aron, Geodude: x4, x2) is refused.
- **Work.** A candidate is also ranked by its cost:
  - the levels from now to its fight level;
  - for a wild species, also its encounter share on a map the AI has been to with a known way (static encounters, normal availability, land in the first slice).
- **Candidates.** Party members; PC box members it KNOWS (ones it saw go in, or saw on the box screen); and catchable species.
- **Choice.** A seeded draw among the picks within `near_best` of the top: RULING 33's "varied among sensible picks".
- **Raising it.** The counter is raised as in (a), with the counter leading.

Measured on the repo's files for BRAWLY (`s53/bossprep/counters.py`, `levels.py`; the encounter levels and shares are from encounters.json):

| Candidate | Where (level, share) | Resistance half | Move half | Class |
|---|---|---|---|---|
| Sableye | GRANITE B1F L9-11 10%, B2F L10-12 20% | immune x0 | Night Shade (level damage), Astonish L13 x3 vs MEDITITE | strong typing, fair moves |
| Zubat | the cave, 30% | x0.25, but Seismic Toss is unresisted | weak until Wing Attack at L21 | half |
| Taillow | ROUTE 104 L4-5 10%, ROUTE 116 L6-8 20% | x1 | Peck/Wing Attack x3 | moves only; needs about 10 levels |
| Wingull | ROUTE 104 land L3-5 10% | x0.5 | Wing Attack at L13, x3 | full from L13 |
| Ralts | ROUTE 102 L4 4% | x0.5 | Confusion L6, x3 vs MACHOP/MAKUHITA | full |

C1's own Grovyle scores x1 on both halves, and so do Shroomish and Seedot.

**2.3 (c) Fight smarter.** This is always on in a boss fight. In a later slice it is also a plan alone, when the verdict is CLOSE rather than hopeless.
- **Lead.** The plan's fighter leads: reordered before the fight, or switched to on turn 1.
- **Switch-in.** The threat in `matchup` adds the boss's KNOWN move types (static), so a member that resists is sent in.
- **Earlier heal.** In a boss fight, `heal_below` is raised, e.g. x1.6, with `MAX_HEALS` kept. C1 healed at 7% (L1217), and one Potion could not save it.
- **Recoil** stays as it is (RULING 33).
- **Stocking up.** Before the boss it buys Potions and balls up to the plan's need at a Mart it knows. DEWFORD has none.

**2.4 Which plan, by personality** (the lead's reading, not the user's words).
- **Catcher:** a counter, the best score; it likes a new species.
- **Story:** the least work to "ready": a counter on the way, or one more member trained.
- **Trainer:** train the team.

Each personality has a seeded lean, not a rule. After a loss, the next plan is drawn excluding the one that failed.

#### 3. The knowledge (static only, RULING 40)

**What it uses:**
- the type chart (`types.json`, loaded by `knowledge/facts.py`);
- moves (`moves.json`: type, power, fixed damage);
- species types;
- the boss's party, read from `world/bosses.json`: species, level, types, moves. This is the pinned-decomp extract by `gates/extract_world.py` from `src/data/trainers.h` and `src/data/trainer_parties.h`, e.g. BRAWLY at `trainer_parties.h:3391`;
- level-up learnsets and normal-play land encounters (`seasoned/*.json`, `gates/extract_seasoned.py`).

**Loaders:**
- A new `knowledge/bosses.py` reads ONLY `bosses[].name`, `role`, `double`, `badge.id`, and `party[].species/level/types/moves`. It gets its own pinned-keys test, like `test_k_f3c`.
- A new `knowledge/wild.py` reads ONLY `maps[].map`, `maps[].availability`, `methods.land.slots[].species/min_level/max_level/chance_pct`, and `learnsets species[].symbol/level_up[]`.
- Both are added to `LOADERS`. Every key path of the two seasoned files is classified in `KNOWLEDGE_FIELDS`:
  - `AI`: where a species lives, its levels and shares, and its learnset, as a guide lists them;
  - `META`/`DEVELOPER`: the decomp refs, the notes and the `*_source` lines.

**Checks:**
- **Extract/verify.** Re-run `verify_seasoned.py --selftest` and `verify_world.py` against the pinned decomp. The builder confirms that `verify_world` re-derives each boss's custom moves from `trainer_parties.h` independently. If it does not, add that check together with a planted error.
- **V1 (verify before relying).** In `data/battle_scripts_1.s`, `BattleScript_EffectLevelDamage` runs `typecalc` before `dmgtolevel`, so a Ghost is immune to Seismic Toss and resistances do not reduce it. Read it in the pinned decomp; do not trust my recall.

**Deliberately NOT read:**
- `held_item`. It is classified `AI` at `check_fairness.py:293`, but RULINGS 40 and 58 say held items that are not shown are hidden. Grep 06 before ever raising it.
- `catch_rate` and base stats. `CARRIES`:92-95 keeps them hidden from the brain.
- The trainer's bag, which is not extracted (`trainers.json` `_notes.bag_items`).
- The eyes' every-look box PIDs (`host/eyes.py:468`). The AI knows box members only from what it saw.

#### 4. The smallest first slice that could let C1 beat BRAWLY: BP-1 "a counter for the next boss"

**Why this slice.**
- At the start of the #107 and #111 probes (`probe-C1`, RUSTBORO (19,53), md5 e909e537), C1's party is already full: Grovyle L21 and five L3-6 (log L30). A catch therefore goes to the PC. So BP-1 needs a PC DEPOSIT first, which is simpler than a withdraw, because there is no box grid.
- Training alone cannot do it: Grovyle has no Leaf Blade until L29 (learnsets), and its other moves are 20-40 power.
- Fight smarter alone cannot do it either: no member scores above x1 on either half.

**What is built:**
1. `knowledge/bosses.py` and `knowledge/wild.py`, with their classification (§3).
2. `brain/bossprep.py`:
   - the two-half score;
   - the verdict;
   - the plan. In BP-1, Story and Catcher take the counter plan when the verdict says not ready. Trainer only LOGS its plan and keeps today's behaviour: that is the in-run control.
   - the after-loss exclusion.
3. `hands/pc.py`: deposit one member BY PID. It is the least useful against this boss, and never the counter or the last healthy member. It needs eyes for the storage screen's party panel.
4. A party-reorder hand on the existing party-menu eyes (`SWITCH` is in `PARTY_MENU_ACTIONS`, `eyes/screens.py:352`).
5. Goals:
   - `hunt` (species, maps). It roams grass OR cave floor (the tile's `encounter == "land"`). The battle mind wants THAT species whatever `catch_new` says. Story runs from the others. It is bounded by about 3 / share encounters with no sighting.
   - Stock up on balls before a hunt.
   - `raise` (the counter leads; `train` with a named trainee). Bounded per boss.
6. The plan's fighter leads in the boss fight. The reorder makes this happen, so no new battle rule is needed.

**Offline tests (each FAULT arm must change the result on its fixture; the CONTROL must not):**
- **T1 score, on BRAWLY.**
  - Expected: Sableye is "strong typing"; Abra L8 is "typing only" (move half 0) and ranks below any candidate with a move half; Aron is refused; Taillow is "moves only"; Wingull L13 is full.
  - FAULT `types_only`: Abra moves up. FAULT `moves_only`: Taillow and Ralts move up and Sableye drops.
  - CONTROL: ROXANNE's ranking (Rock) is unchanged by an arm that touches only fixed damage.
- **T2 fixed damage.** Seismic Toss counts x1 against Zubat and x0 against Sableye. FAULT `fixed_resisted`: Zubat jumps above Sableye.
- **T3 verdict.**
  - Fixtures: the #111 parties at their fights' starts.
  - Expected: C1 is NOT READY; C3 (Marshtomp L25) is READY; C2 (Combusken L23-24, lost one, won one) is CLOSE.
  - FAULT `strongest_level` (today's rule): C1 is READY.
  - Caveat: this is calibrated on three trajectories, not validated.
- **T4 plan.**
  - After a loss with plan P, the next plan is not P. FAULT `same_plan`.
  - The session and hunt caps hold. FAULT `no_bound`.
  - Trainer's behaviour is byte-identical to the base on a driven fixture: the CONTROL.
- **T5 hunt.** It wants the named species against a `catch_new` draw that says no. FAULT: the generic draw.
- **T6 cave floor.** GRANITE B1F is "here" for a hunt. FAULT: grass only gives "none". CONTROL: on a route with grass, the same tiles are chosen as on the base.
- **T7 deposit, driven on a fixture.** After it, the game's party PIDs lack the member and the box holds it (by identity, rule 3). FAULT: a deposit by slot.
- **T8 reorder.** The game's slot-0 PID equals the counter's PID.
- **T9 fairness.** `check_fairness` passes. A planted read of `held_item`, `catch_rate` or base stats in `bossprep.py` fails B2.
- **T10 chapters 1-5.**
  - Run the verdict over every recorded boss-fight start of chapters 1-5 (the probe records' party at the fight).
  - Report each one that flips to not ready. Each flip gets a live A/B control on its start.
  - `run_regression.py` stays green.

**Mutants** (a `gates/revert_bossprep.py`, in the `revert_step*` pattern). Each must be caught by a test above:
- types only;
- moves only;
- fixed damage resisted;
- the same plan after a loss;
- no bound;
- the hunt by `catch_new`;
- the deposit by slot;
- the counter not led;
- `held_item` read;
- the verdict by strongest level.

**Live A/B.**
- **Start:** `probe-C1` (as #107 and #111), target `ch7_brawly`, 1,200,000 frames, the #111 harness.
- **Seeds:** 6365 and 6337 (the base lost 3/3 on both, in #111 and #107; different code and seeds, so two trajectories, not a rate), plus one new seed.
- **Arms:** A = BP-1's parent; B = BP-1.
- **Discriminator, computed offline on the start BEFORE the run:**
  - A's prep says ready (L21 is at least 20), so nothing is done for BRAWLY.
  - B's verdict says NOT READY and names a ranked counter list from the maps C1 knows at RUSTBORO (Taillow, Wingull, Ralts...; the cave's Sableye and Zubat join once it has been there).
  - Show the two plans differ before spending a run.
- **The claim, read from the game:**
  - `FLAG_BADGE02_GET` is set in B and not in A.
  - BRAWLY's battle (trainer 266) ends with gBattleOutcome 1.
  - At that battle's first turn, the battle data's own PID equals the PID of the counter the plan named, and its species and level come from the game's party data.
- **Secondary readings:** frames to BADGE02, and the frames spent hunting and raising. Time is acceptable (RULING 41), but it is measured.
- **The prediction is hashed before the run.**
  - Unverified risks: catching Sableye with Poke Balls is rough. My estimate is about 15-25% a ball at low HP, and C1 missed four of four. A Taillow or Wingull needs about 10 levels.
- **The Dewford start.** #111 C1's end (DEWFORD, 0 balls, 3 losses) is for BP-2's after-loss path and its PC withdraw (the Zubat in the box). First confirm how the restored losses carry over (`mode.py:793-830`). If they would end the run at once, make a test-side start from it with the AI's own hands and no memory write (the D2 pattern).
- **D2 (round 6).** D2 also reproduces P4-1 (2 of 2 lost), but its party and box were never read. Compute its discriminator before using it.

**BP-2, after BP-1:** train-the-team as a full plan; fight-smarter (switching by the boss's known moves, the earlier heal, stocking up, a plan alone when CLOSE); the PC withdraw; the full personality draw; the after-loss ladder over all three plans; other bosses.

#### 5. Risks, and what it must not do

- **No bot code in its play (RULING 35).** The bot's battle and PC code is teaching material only. `check_purity.py` must stay CLEAN.
- **No hidden state (RULING 40).**
  - No foe base stats, IVs, catch rate or held items. Foe HP is read from the bar only.
  - Box contents only as SEEN.
  - "Next boss" from badge names, never from the developer keys `order` and `entry`.
- **Never grind forever.**
  - The hunt, raise and train caps are per boss.
  - A failed plan is never repeated unchanged.
  - `MAX_LOSSES` stays the stop.
  - Hunting must not starve the story: the hunt goal only runs while the boss is the next fight.
- **Not a machine (RULING 32).**
  - The counter is a seeded pick among sensible ones, and the lean is per personality.
  - A plan, once begun (a catch made), sticks unless it fails, or unless a new candidate is clearly better with no catch yet. No flip-flopping between counters.
- **Chapters 1-5.** No behaviour change without the T10 control. The verdict fires before every known boss, so it can change the ROXANNE and rival fights. Measure it, do not assume it.
- **The verdict is rough.** It ignores Bulk Up, Reflect, Focus Punch, crits and Sitrus, and the foe is assumed to move first. It can say "ready" wrongly, so the after-loss path must still work.
- **Load-bearing claims to verify first:**
  - V1: fixed damage and immunity;
  - that BRAWLY's AI cannot touch a Sableye (all of its damaging moves are Fighting: bosses.json:705-760);
  - Night Shade's 15 PP against three foes. This is an estimate: it may run out against MAKUHITA's HP plus Sitrus. In that case Scratch is left, and Grovyle can finish.
- **Never change the bot's default behaviour to serve the AI.**

## Part 2. The adversarial critique (the critic, 2026-11-07)

### Adversarial critique: boss preparation design (DESIGN.md), 2026-11-07

Read-only review. Code paths are relative to `.claude/worktrees/wf_e7452923-f06-3/ai_player/` (f299a1e7). Decomp paths are
relative to `C:/Remote Projects/_decomp/pokeemerald/`. The damage numbers below are MY hand estimates (Gen 3 formula,
assumed mid IVs). They are not measured and are marked "est.".

BRAWLY_1 (trainer 266, `include/constants/opponents.h:270`), from `src/data/trainer_parties.h:3391-3413`:
- MACHOP L16 (iv 100): Karate Chop, Low Kick, Seismic Toss, Bulk Up.
- MEDITITE L16 (iv 100): Focus Punch, Light Screen, Reflect, Bulk Up.
- MAKUHITA L19 (iv 200): Arm Thrust, Vital Throw, Reversal, Bulk Up. It holds a SITRUS BERRY.
- The trainer: 2 Super Potions; aiFlags CHECK_BAD_MOVE | TRY_TO_FAINT | CHECK_VIABILITY (`src/data/trainers.h:3202-3204`).

`world/bosses.json:705-760` matches the decomp exactly.

---

#### MAJOR

##### M1. The design's measured table and T1 were computed with the very fault that T2 forbids
- **Evidence.** `counters.py` computes `resist = max(mult(t, st) for t in btypes)`, where `btypes` is the SET of boss
  move TYPES. Seismic Toss therefore dissolves into "Fighting" and is resisted, which is FAULT `fixed_resisted`.
- MACHOP carries Seismic Toss (`trainer_parties.h:3397`). Under the design's own V1 rule, every non-Ghost candidate's
  resistance half against MACHOP is x1, not x0.5 or x0.25. That covers Wingull, Ralts, Zubat and Abra.
- So the table's "Wingull ... x0.5 ... full from L13" and "Ralts x0.5 ... full", and T1's expected "Wingull L13 is
  full", contradict T2's expected "Seismic Toss counts x1 against Zubat". Only Zubat's prose was hand-patched.
- The same script's move half multiplies a fixed-damage move by type effectiveness (`e * (1 if fx else s)`). That
  scores Sableye's Night Shade x2 against MEDITITE, but level damage ignores super-effectiveness
  (`data/battle_scripts_1.s:1200-1202`).
- **Why it matters.** Seismic Toss does a flat 16 a hit. Against a counter at L10-14 (about 33-45 HP, est.), it is what
  removes the counter. It erases the "resists Fighting" advantage that the classes rank on.
- **Fix.**
  - Compute the resistance half PER BOSS POKEMON and OVER MOVES, not over a type set: fixed damage counts x1, or x0
    when the typing is immune.
  - Weight each boss move by what it does: power x STAB x multiplier, or the level for fixed damage.
  - Then re-derive the table and T1's expected values before any of them become test oracles.

##### M2. The design withholds `held_item`, contradicting USER RULING 44, a settled do-not-re-ask ruling
- **Evidence.** DESIGN §3, under "Deliberately NOT read", says: "held_item ... RULINGS 40 and 58 say held items that
  are not shown are hidden. Grep 06 before ever raising it."
- The grep says the opposite. `PROJECT KNOWLEDGE/06-DECISIONS-LOG.md:9582-9591`, USER RULING 44 (2026-10-21), says:
  "the AI KNOWS each boss Pokémon's held item ... `heldItem` moves from WITHHELD to ALLOWED ... ⛔ Do not re-ask".
- `check_fairness.py:293` already classifies `bosses[].party[].held_item` as `AI`.
- MAKUHITA's Sitrus Berry adds 30 HP (est.) to the last foe, the one that decides the fight. DESIGN §5 itself names
  Sitrus as the reason Night Shade's PP may run out.
- **Fix.**
  - `knowledge/bosses.py` reads `party[].held_item`, and the verdict models HP berries.
  - Drop "`held_item` read" from the mutant list and from T9's planted-read fault. As written, that test would enforce
    a rule the user reversed.
  - Keep IVs and aiFlags withheld (also RULING 44).

##### M3. The score is asymmetric and ignores evolution, so it misses C1's in-party counters, and BP-1 would deposit one
- **Evidence.**
  - DESIGN §2.2 judges a party member by "its real moves (the summary)", but a wild species by "its level-up
    learnset" at its fight level.
  - C1's party at the start is Grovyle L21, Poochyena L6, Wurmple L3, Seedot L3, Shroomish L5 and Cascoon L5 (C1 log
    line ~30, and the L1240 result line).
  - The seasoned data (`levels.py` on the worktree's knowledge files):
    - CASCOON L5 evolves into DUSTOX at L10. DUSTOX is Bug/Poison, so Fighting does x0.25 to it. It learns Confusion at
      L10, which hits x2 against MACHOP and MAKUHITA, and Gust at L13, which hits x2 against all three.
    - WURMPLE L3 evolves at L7 into Silcoon or Cascoon. Which one is decided by its PID, which is hidden, but both
      branches reach a Fighting-resistant L10 form with Gust at L13.
    - BEAUTIFLY is Bug/Flying, so its Gust is STAB: x3 against all three.
  - `counters.py`'s PARTY/REF list checks Grovyle, Shroomish, Poochyena and Seedot, and never Wurmple or Cascoon.
- **Failure scenario.** BP-1 step 3 deposits "the least useful against this boss". Cascoon knows only Harden, so its
  move half is 0. It goes to the PC: the cheapest counter C1 owns, which needs no hunt, no ball and no PC.
- §4's "no member scores above x1 on either half" is true only for CURRENT moves.
- Plan (a), which the user ruled viable, is ruled out by construction here.
- **Fix.**
  - Score party and box members by the same rule as wild species: the moves and types at the fight level, following
    level evolutions in `species.json` `evolutions` (static data, RULING 40; classify the key).
  - Where the evolution branch is hidden (Wurmple), score the worse branch.
  - Exclude from deposit any member whose future score is a counter.
  - Note: a cocoon (Harden only) cannot earn experience alone. Raising it needs switch training (it leads, then
    switches out on turn 1, and Gen 3 splits the experience) or a Wurmple trained from L3 on L2-5 routes.

##### M4. "Raise the counter" would quietly train Grovyle instead, which also confounds the A/B
- **Evidence.** The rest rules are keyed on the STRONGEST member and the party's share:
  - `brain/battle.py:601-608` `needs_rest`: the strongest fainted or under 1/3, or the party under 1/3;
  - `brain/goals.py` `training_rest` (the party under the personality's `heal_below`).
- A trainee at L5-8 that faints leaves the party near 87% HP (est.: 137 of 157). So the roam goes on, and Gen 3 sends
  the first healthy member, Grovyle, into every later battle until the next heal. The experience goes to Grovyle.
- DESIGN §2.1 and BP-1 step 5 ("the counter leads") never say what happens after the trainee's first faint.
- **A/B confound.** Arm B can win BRAWLY because Grovyle gained levels during "raise". The planned claim (the counter's
  PID on the field at turn 1) does not rule that out.
- **Fix.**
  - A raise roam ends, and the AI goes to heal, when the TRAINEE faints or falls under its heal share.
  - At each battle start, assert that the lead PID is the trainee.
  - Add a fault arm: rest keyed on the strongest member.
  - The A/B records, in BOTH arms, Grovyle's level at BRAWLY's first turn and the PID on the field when each of
    BRAWLY's three Pokemon fainted. The claim then rests on who took the knockouts.

##### M5. The hunt's bound resets on every sighting, and the catch behaviour that burned C1's balls is untouched
- **Evidence.** The hunt is bounded by "about 3 / share encounters with no sighting" (BP-1 step 5).
- C1 SAW Sableye 5 times and caught none (DESIGN §1.7). C1's log lines 40-48 show 1 Great Ball and 4 Poké Balls thrown
  at a FULL-HP Marill: "every move could knock it out (its bar 100%): throw now".
- Sableye's catch rate is 45. Grovyle's Pound and Quick Attack are Normal, so they do x0 to a Ghost. Weakening it needs
  Absorb or Pursuit, which can knock it out.
- The resulting loop: a sighting, no catch, no balls, "stock up", travel, another sighting. Nothing bounds it, because
  each sighting resets the only counter.
- **Fix.**
  - One per-boss budget shared by hunt, raise and train: target encounters, balls thrown and frames.
  - When it is spent, drop to the next-ranked candidate, then to another plan.
  - The hunt's catch rule must weaken before throwing at a hard catch. Reuse `MAX_THROWS` and `MAX_WEAKEN_TURNS`
    (`battle.py:144-145`).
  - T5 needs a "sighted 5 times, 0 caught, 0 balls" fixture, with a FAULT arm that resets on sighting.

---

#### MINOR

##### m1. V1 is verified and already built
- `data/battle_scripts_1.s:1195-1203` runs `typecalc`, then `bicbyte` clears the super- and not-very-effective flags,
  then `dmgtolevel`.
- `brain/battle.py:415-416` already does "fixed damage ignores the matchup (an immunity still holds)".
- Two caveats:
  - A Ghost's immunity to Fighting lifts under Foresight or Odor Sleuth. BRAWLY knows neither.
  - Struggle skips `typecalc` (`src/battle_script_commands.c:1360`), so "immune to everything BRAWLY has" holds only
    until his PP runs out.
- Update the V1 list.

##### m2. The Sableye wall: its PP economics and the foe's stat boosts
- While MACHOP cannot hurt Sableye, BRAWLY's AI (CHECK_BAD_MOVE) uses Bulk Up, Reflect and Light Screen.
- Night Shade has 15 PP (`src/data/battle_moves.h`, `[MOVE_NIGHT_SHADE]` .pp = 15). At L12-14 that is about 180-210
  damage (est.).
- The boss team has about 50 + 37 + 60 HP, plus 30 from Sitrus, plus 100 from 2 Super Potions: about 277 (est.).
- §5's "Scratch is left, and Grovyle can finish" is wrong: Grovyle would come in against a foe at +N Attack from Bulk
  Up. Sableye must finish with its own Astonish, Scratch and Fury Swipes.
- **Fix.**
  - The verdict counts damage over PP for the whole team.
  - Never switch the wall out against a boosted foe.
  - Trainer items are static, but they are not extracted. Grep 06 before relying on them, and otherwise add a margin.

##### m3. Plan (c)'s switch-in cannot fire for C1, and §1.2 omits the guard that blocks it
- `OUTLEVELS = 5` (`battle.py:150`) is applied at `battle.py:1312-1313`. A Pokemon at foe level + 5 or more is never
  switched out, and Grovyle L22 against Machop L16 is 6 levels above.
- Adding the boss's known move types to `matchup` also leaves Grovyle at threat x1, so it is not "badly matched".
- §1.2 also omits `switched_against`, which allows one switch per foe species (:1290), and the need for 50% HP (:1319).
- **Fix.** Plan (c) needs a boss-fight rule, not the wild-tuned guard. Document all three conditions.

##### m4. `Progress.badges` is a flag read, not the trainer card
- `host/eyes.py:1360`: `badges=tuple(flag for flag in BADGE_FLAGS if get_event_flag(flag))`. No brain code reads it
  today.
- The badges are visible in substance, so this is not a leak, but it is a NEW flag read in the brain.
- **Fix.** Add a RULE A allowlist entry with its purpose and a fault test, or take the next boss from the AI's own
  record of which leaders it has beaten.

##### m5. The box PIDs already reach the brain
- `brain/navigator.py:595-597` `_pids` reads `look.storage` on every look.
- "Box members only as SEEN" therefore needs a gate: T9 plants a `look.storage` read in `bossprep.py`, and it must fail.

##### m6. Variable-power and conditional boss moves are valued wrongly
- Low Kick and Reversal have `power: 1` and are not fixed damage (`moves.json`). `_power` returns 1 for them
  (`battle.py:334-345`; `FIXED_POWER` at :156 has no LOW_KICK and no FLAIL entry).
- So the verdict never sees MAKUHITA's Reversal, which reaches 200 power at low HP and is STAB.
- Focus Punch (150) would be the "best known move", but it fails when its user is hit first.
- **Fix.** Give LOW_KICK and FLAIL worths, and model Focus Punch failing when hit, in the verdict's foe side.

##### m7. The move half is a bare multiplier
- A x3 Peck (35 power) scores the same as a x3 Wing Attack (60).
- Accuracy, PP and recoil are ignored. RULING 33 names recoil.
- **Fix (simpler, see S1).** Use the existing `move_value` (`battle.py:393`: type x STAB x power x hit, minus
  `recoil_penalty`) in BOTH directions, per boss Pokemon. One tested function then covers dual types, immunities, STAB,
  fixed damage and recoil.

##### m8. Abilities that change a type matchup
- The ruling covers "all gym leaders, bosses and elite 4". Levitate (TATE&LIZA's Solrock and Lunatone, PHOEBE's
  ghosts) makes a "Ground x2" score wrong.
- The seasoned base lists abilities (`06:9446`). Use single-ability species only; a two-ability species' ability is
  decided by its PID, which is hidden.
- This does not affect BP-1. Add the data hook to the knowledge now.

##### m9. The failed-plan memory must survive a continue, and the ladder is shorter than it looks
- `MAX_LOSSES` is restored from the save (`mode.py:793-794`). The failed-plan record must persist the same way, or a
  continue repeats the plan.
- `MAX_LOSSES = 3` (`mode.py:113`) is run-wide and counts every battle lost (`mode.py:1032-1040`). The after-loss
  ladder therefore gets at most 2 changes across ALL bosses.
- State this, and decide with the user whether it should be per boss. Grep 06 first.

##### m10. The counter can flip before any catch
- The verdict re-runs "on arriving at a new map", and a "clearly better" candidate wins when nothing is caught yet. So
  the counter can flip between Taillow, Wingull and Sableye as the maps change.
- **Fix.** Commit when the HUNT starts, with a margin and a flip count. Add a test.

##### m11. One cap or several?
- `TRAIN_SESSIONS` 8 per fight (`goals.py:259`) sits beside the new per-boss caps (Story 8, Catcher 10, Trainer 14) and
  the hunt bound. Say whether they share one budget.
- Also, the "full counter" fight level (min - 3 + margin = 14) ignores Seismic Toss's flat 16. Stop raising when the
  VERDICT says ready, not at a level that depends on the class.

##### m12. A budget end must not read as a refutation
- B adds a hunt, a PC visit and raising inside 1,200,000 frames, and #111's runs were 2.6-11x slower in the cave.
- Pre-register a frame estimate from #111's measured rates.
- A run that ends on its budget is INCONCLUSIVE, not "B did not earn BADGE02".

---

#### NIT
- n1. §1.4 says training is "bounded by `train_min_steps`". It is a floor: `goals.py:1523` makes the party "short" while
  the steps are under it.
- n2. "The foe is assumed to move first." Grovyle is much faster than Machop in static data. Because base stats stay
  hidden (`CARRIES`, `check_fairness.py:92-95`), say instead that the assumption biases T10 toward "not ready".
- n3. T9 lists `check_fairness`, but `check_purity.py` (RULING 35, §5) is in no offline test. Add it.
- n4. Arm A on seed 6365 is #111's trajectory replayed: "one trajectory, replayed" (CLAUDE.md rule 8). It is not a new
  measurement.
- n5. Wingull is also on ROUTE 103 (land L2-4, 20%, from `levels.py`). That is a better source than ROUTE 104's 10%.
- n6. The rival has 30 MAY/BRENDAN entries. Joining a milestone's `fight.trainers` to a bosses.json entry uses `id`,
  which is DEVELOPER. A classified join is needed (name, `battled_on`, its own starter). This is not BP-1.

---

#### Does BP-1 change C1's BRAWLY fight? Does the A/B discriminate?
- **Reachable: yes.** From probe-C1 the next milestone is `ch6_briney_house` on ROUTE 104, and BRAWLY is the next NAMED
  fight (`milestones.json`: ch6_briney_house, then ch6_dewford, ch7_steven, ch7_gym_trainers, ch7_brawly). So B can
  hunt Taillow or Wingull on ROUTE 104 before it sails.
- **Likely outcome as written: no.** Two problems combine:
  - Through M4, the raise mostly trains Grovyle.
  - Through M1, the chosen counter's real resistance against MACHOP is x1, because of Seismic Toss.
- The probable B fight is a counter at L8-12 that MACHOP removes in 1-2 hits (est.), plus a Grovyle a level or two
  higher.
- With M3 and M4 fixed, an in-party Dustox or Beautifly, or a Taillow at about L16 (est.), is a plausible winner.
- **The A/B.** The offline check that the two arms plan differently is good. The live claim needs knockout attribution
  by PID and Grovyle's level in both arms (M4) to separate "the counter won" from "Grovyle outlevelled it".

#### Anything simpler that meets the ruling
- **S1.** Drop the class taxonomy. Score each candidate by a per-foe duel built from the existing `move_value` in both
  directions (the candidate's moves at fight level against each boss Pokemon, and each boss Pokemon's KNOWN moves
  against the candidate's typing), plus `rough_share` for the turns.
  - That is both halves of RULING 58 and RULING 33's recoil in one tested function.
  - The classes become explanations in the log, not rules.
- **S2.** For C1 the smallest slice is plan (a) on IN-PARTY evolvers (M3). It needs:
  - the knowledge (bosses, learnsets, evolutions);
  - the verdict;
  - the reorder hand;
  - a trainee-aware raise (M4), with switch training for a cocoon.

  It needs no PC eyes or hand, no hunt and no ball economy. Those are the three largest new surfaces, so leave them,
  with the hunt bound (M5), for BP-2. The design's personality leans still hold: Catcher may prefer catching once BP-2
  exists.
