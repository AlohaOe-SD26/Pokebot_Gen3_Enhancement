# Boss preparation, first slice BP-1: the build spec (USER RULING 58), 2026-11-08 (NOT built)

> A NOTE, not a source of truth (`00-READ-THIS-FIRST.md`). It folds the critique of
> `2026-11-07-BOSS-PREP-DESIGN.md` (MAJOR M1-M5) into a spec a builder can follow on branch `wip/ch6-ch7`; one designer
> wrote it read-only against `f299a1e7`, and no independent check has read it yet: the build round's verifier is the
> first. Its numbers came from the appendix script calling the worktree brain's own functions; they become test
> expectations only once the built code reproduces them.
> ⛔ **Seeds (section 5.3):** the spec proposes 6365 and 6337 for the live A/B, which ledgers #111 and #107 already spent.
> The project never re-runs a spent seed: the build round takes NEW seeds (6371 upward, checked free in every ledger)
> unless the user approves a replay arm. Paths under `s53/` are the session's scratch folder, which may be gone; the
> probe's durable record is `ai_player/evidence/2026-11-07-ch6-stops-development-probe-11.txt` on the branch.

## BP-1 "train the party's own counter for the next gym leader": the build spec (2026-11-08, NOT built)

> A NOTE, not a source of truth. It revises `PROJECT KNOWLEDGE/ai-research-notes/2026-11-07-BOSS-PREP-DESIGN.md` (Part 1,
> the design; Part 2, the adversarial critique) into the FIRST slice a builder can follow without design decisions. It
> folds in the critique's M1-M5, the minor items that touch this slice (m1, m3, m4, m5, m6, m7, m9, m10, m11, m12, n1-n4),
> and the critic's simpler slice (S1: score with `move_value` both ways; S2: train the party's own evolvers first).
> Rulings applied (`06`): USER RULING 58 and its 2026-11-07 correction, 44 (a boss Pokemon's held item is KNOWN; IVs and
> aiFlags are not), 40 (a seasoned player: static game knowledge allowed, live hidden state not), 33 (type advantages of
> both the Pokemon and its moves; recoil; varied sensible picks), 35 (the AI plays itself; the bot is teaching material
> only, `check_purity.py` stays CLEAN), 41 (time is acceptable). Code read: branch worktree
> `.claude/worktrees/wf_e7452923-f06-3` at `f299a1e7` (`wip/ch6-ch7`); paths below are relative to its `ai_player/`.
> Decomp paths are relative to the pinned `C:/Remote Projects/_decomp/pokeemerald`.
>
> **The numbers in §2 were computed by a scratch script that calls the worktree brain's OWN functions** (`move_value`,
> `rough_share`, `typical_stat`, `learn_choice`, `type_multiplier`): `s53/bossprep2/compute.py` (md5 prefix `f72c29446c9c`),
> output `s53/bossprep2/out_none.txt` (md5 prefix `ed0002657c39`), one file per fault arm `out_<fault>.txt`. Two cells
> were re-derived by hand (§2.4). **They become test oracles only when the BUILT code reproduces them** (the critique's M1
> was exactly a scratch script that carried the fault its own test forbade). Own Pokemon's stats are TYPICAL in these
> numbers (the logs do not show the summary's stats); the live verdict uses the summary's stats at the current level, so
> its numbers can move a little (the A/B's offline discriminator, §5.4, re-computes on the real start).

---

### 0. What BP-1 is, in one paragraph

Before the NEXT gym leader, the AI judges its party against that leader's known team (species, levels, moves, held items:
static, RULINGS 40/44/58) with a small deterministic duel built on the battle brain's own move valuation. When the verdict
is NOT READY and the personality is Story or Catcher, it picks ONE party member to raise (the plan with the least work to
READY, judged on each member's moves AND evolutions at the level it would reach), makes that member LEAD (a party-reorder
hand), and raises it in wild battles on grass whose static wild levels suit it, with experience kept on the trainee (M4)
and one bounded budget per boss (M5). Trainer only LOGS its verdict and plan (the in-run control). No PC, no catching, no
hunt, no ball economy (BP-2). For C1 against BRAWLY the plan is: **raise its own Wurmple (L3) to L18**, where either
evolution branch (Beautifly or Dustox, Bug/Flying or Bug/Poison: Fighting does x0.25) with Confusion or Gust reads READY.

**Scope guard (decided here, not a builder choice): the ACTION fires only for `ACT_ON = {"BRAWLY"}`.** The verdict is
computed and LOGGED for every gym leader; widening `ACT_ON` is BP-2, after T12a's calibration over chapters 1-5. This is
what makes "chapters 1-5 unchanged" (T12) true by construction rather than by luck.

---

### 1. The readiness verdict for the next boss

#### 1.1 Inputs (all static or shown on screen; nothing hidden)

| Input | Source | Classification |
|---|---|---|
| Which boss is next | the first milestone at or after the current one, in the story's order (`knowledge/story.py`, the list the goals already walk), with `fight_named`, whose `maps` hold a gym map that `knowledge/atlas.py` `gym_leaders()` names; the leader's NAME is the key | AI (`milestones[].maps`, `.fight`; `bosses[].name/role/battled_on`). No badge FLAG read (m4), no `order`/`entry`/`id` (DEVELOPER, n6) |
| The boss's party | `world/bosses.json` `bosses[name].party[]`: `species`, `level`, `moves`, `held_item` (new `atlas.boss_party(name)`) | AI (`check_fairness.py:287-293`); `held_item` is AI by RULING 44 (M2). `iv` and aiFlags are not in the file and stay withheld |
| Boss Pokemon types | `knowledge/facts.py` `species_fact(name).types` (the same SPECIES types `seen_types` uses); `bosses[].party[].types` is only a cross-check in T11 | AI |
| Move facts | `facts.move_fact` (type, power, accuracy, effect, priority, category, fixed damage) | AI |
| Own members | the party as the eyes read it: PID (identity, rule 3), species, level, HP, max HP, moves, and the summary's stats when read (`MonSummary.stats`) | screen |
| Evolutions, level-up moves | `knowledge/seasoned/species.json` `species[].evolutions[]` (method, `parameter.value`, `into`) and `learnsets.json` `species[].level_up[]` (level, move), via a new loader `knowledge/seasoned.py` | AI (classified in T11) |
| Wild levels per map | `knowledge/seasoned/encounters.json` `maps[].map`, `availability`, `methods.land.slots[].min_level/max_level` (same loader) | AI |
| Typical stats | `brain/battle.py` `TYPICAL_BASE` / `typical_stat` (step 4.1 round 3: a person knows a Pokemon by its level) | rule 4.1 |

NOT read: foe base stats, catch rate, exp yield, growth rate (all HIDDEN, `CARRIES`); wild held items (HIDDEN);
`look.storage` (box PIDs reach the brain every look, `brain/navigator.py:595-597`; m5: `bossprep.py` must not read it,
T11 plants it); the trainer's bag (not extracted; BRAWLY's 2 Super Potions are covered by the caution margin only); any
Pokemon's PID-derived trait (Wurmple's branch, abilities: scored by the WORSE branch).

#### 1.2 Projection of a member to a level (M3)

`project(member, level) -> list[Member]` (one per hidden branch):
1. Walk levels `member.level+1 .. level`. At each level `lv`, for every evolution of the current species with method
   starting `EVO_LEVEL` and `parameter.value <= lv`, the member becomes `into` (two `EVO_LEVEL_SILCOON/CASCOON` entries
   both apply: TWO branches; the PID that decides it is hidden). Other methods (item, friendship, trade) do not apply.
2. Moves learned at `lv`: the level-up moves of the (possibly new) species at exactly `lv` (on evolution the new species'
   moves at that level, as the game offers them). Kept moves carry over. With fewer than 4 moves the move is added; with
   4, `brain/battle.py` `learn_choice` decides (the AI's own rule; it never forgets an HM).
3. A projected member uses TYPICAL max HP and stats at its level (`typical_stat`); the current level uses the summary's.
4. A branch-split candidate is scored by its WORSE branch (the lower class, then the lower party-left share).

#### 1.3 The two halves (S1, m7): `move_value` both ways

Per member M and boss Pokemon B:
- **Attack half** `A(M,B)`: `max(move_value(slot, move, M.types, M.level, hp_share, B.types).value)` over M's damaging moves.
  This is the battle brain's own valuation: type multiplier x STAB x power x hit chance, minus recoil (RULING 33), fixed
  damage at x1 unless immune (`battle.py:415-416`). The verdict's own move each turn is this argmax; on a TIE in value,
  the lower `priority`, then the lower slot (the pessimistic tie: Grovyle's Pound and Quick Attack tie at 40).
- **Threat half** `T(M,B)`: `max(move_value(slot, verdict_slot(move), B.types, B.level, 1.0, M.types).value)` over B's
  damaging moves, with the VERDICT POWERS of §1.4 (m6).
- The pair `(A, T)` and the solo duel (§1.5) are LOGGED per boss Pokemon as the explanation (the design's classes,
  "typing only" / "moves only" / "full", become log words, not rules: S1). Ranking uses the duel, never the classes.

#### 1.4 The verdict's rules for the FOE's moves (M1, m1, m6) — exact

| Rule | Value | Source |
|---|---|---|
| Fixed damage `LEVEL_DAMAGE` (Seismic Toss, Night Shade) | the user's LEVEL in HP points, ignoring resistance and super-effectiveness; 0 if `type_multiplier(move.type, M.types) == 0` (a Ghost vs Seismic Toss) | `data/battle_scripts_1.s:1195-1203` (`typecalc`, then `bicbyte` clears the effectiveness flags, then `dmgtolevel`); `battle.py:415-416` |
| Low Kick (`LOW_KICK`, power 1 in moves.json) | power 60 (species weight is not in the knowledge; 60 over-rates it against light Pokemon, which biases toward NOT READY) | weight table `src/battle_script_commands.c:774-782` |
| Flail / Reversal (`FLAIL`) | power by the USER's HP share each turn: `scale = int(48 * hp/max)`; first row with `scale <= cut`: 1->200, 4->150, 9->100, 16->80, 32->40, 48->20 | `src/battle_script_commands.c:749-757` |
| Multi-hit (`MULTI_HIT`: Arm Thrust) | power x 3.0 (2 and 3 hits 37.5 % each, 4 and 5 12.5 %: mean 3.0) | `src/battle_script_commands.c:7147-7151` |
| Focus Punch (`FOCUS_PUNCH`, priority -3) | 0 damage on a turn the member uses a DAMAGING move (it is hit first and loses focus); full power when the member uses a status move | `data/battle_scripts_1.s:2260-2266` (`jumpifnodamage`), `src/battle_script_commands.c:9150` |
| Status moves (Bulk Up, Reflect, Light Screen) | 0 (not modelled; the caution margin carries them) | — |
| Held item Sitrus Berry | once, when the holder's HP is at or under half its max after a hit: +30 HP points (capped at max) | `src/data/items.h` ITEM_SITRUS_BERRY `holdEffectParam = 30`; `src/battle_util.c:3322-3326` (`hp <= maxHP / 2`) |
| Held item Oran Berry | the same with +10 | `holdEffectParam = 10` (builder: confirm in `items.h` in T11) |
| Any other held item | not modelled; logged "held item X not modelled" | — |

Implementation of the variable powers: add a keyword `power: float | None = None` to `brain/battle.py` `move_value`,
`_formula_share` and `rough_share` (used instead of `_power(...)` when given). Default `None` keeps every existing caller
byte-identical (T1's CONTROL checks it over every move in `moves.json`). `move_value` itself is NOT otherwise changed:
its STAB on fixed damage (`Seismic Toss 30` in the threat half) is a known small mis-rating in the LOG only; the duel uses
the flat level.

#### 1.5 The duel (`brain/bossprep.py` `verdict`) — exact, integer HP points

1. **Lead.** The plan's trainee if a plan is being judged, else the game's slot-0 member (by PID).
2. **HP.** Members: current HP points (summary) or typical max HP at a projected level. Boss Pokemon: `typical_stat("hp",
   level)` points (BRAWLY: MACHOP 48, MEDITITE 48, MAKUHITA 55).
3. **Damage of one hit, in points.** Own -> boss: `round(rough_share(move, member_summary_or_None, member_battler,
   boss_battler) * boss_max_hp)` (the person's rough sense, to an eighth; `None` from a status move or Bide = 0). Boss ->
   own: the §1.4 rules; otherwise `round(rough_share(verdict_slot(move), None, boss_battler, member_battler) *
   typical_stat("hp", member.level))` (the boss's attack is TYPICAL for its level, rule 4.1). Hits always land (accuracy
   is already in the move choice and in the caution margin). No critical hits.
4. **The foe's move each turn:** the one that does the most points to the member now (a person's worst case; no aiFlags).
5. **Order each turn:** the foe first, UNLESS the foe's move has lower priority than the member's (Vital Throw -1, Focus
   Punch -3 move after; Quick Attack +1 moves first). Equal priority: foe first. Speed is not modelled (TYPICAL_BASE has
   no speed), which biases toward NOT READY (n2).
6. **Faint and replacement.** At 0 points or less the member faints; the next is the healthy member with the highest
   `A/max(T,1) x (0.5 + 0.5 x hp/max)` against the boss Pokemon standing (the shape of `replacement`, `battle.py:1376-1385`).
   HP carries over to the next boss Pokemon.
7. **Cap:** 80 turns per boss Pokemon (no result = NOT READY).

**Classes:**
- **READY**: every boss Pokemon falls and the party's HP points left / its total max HP >= the caution: Story 0.25,
  Catcher 0.30, Trainer 0.40 (taste, the design's values; `CAUTION` in `bossprep.py`).
- **CLOSE**: every boss Pokemon falls with less than the caution left, OR only the LAST boss Pokemon stands and it has at
  most half its HP left. (BP-1 does nothing on CLOSE: it is BP-2's fight-smarter case.)
- **NOT READY**: anything else.

**When it runs:** on every goal decision where the party's signature `(pid, species, level, max_hp, moves)` or the next
boss changed since the last run (cached; no RNG drawn; one `[AI-BOSSPREP]` log line per run).

#### 1.6 The options and the plan (only for a boss in `ACT_ON`, a Story or Catcher personality, a NOT READY verdict)

- **Eligible trainee:** a party member (by PID) with at least one damaging move NOW (it must win wild battles alone; a
  Harden-only cocoon needs switch training: BP-2).
- **Its option:** the lowest target level `L` from `level+1` to `max(boss levels) + 11` (BRAWLY: 30) at which the verdict,
  with that member projected to `L` (worst branch), the rest as they are and the trainee LEADING, is READY.
- **Cost:** `L^2 - level^2` (about how many wild battles: the experience curve of a TYPICAL Pokemon is cubic and the wilds
  it meets grow with it; species growth rates are HIDDEN).
- **Choice:** a draw from a NEW seeded stream `random.Random(f"{seed}:bossprep")` (so no other stream shifts) among the
  options with `cost <= min_cost / temper.near_best` (RULING 33's "varied among sensible picks"; Story 0.85, Catcher 0.80).
- **Commit (m10):** the plan (trainee PID, target level, the verdict line) is stored once and not re-chosen on later maps.
  It is re-judged only (a) when the trainee reaches the target (READY -> done; CLOSE -> done; still NOT READY -> target +1,
  within the budget), (b) after a loss to that boss (§3.3).
- **Trainer:** the verdict and the plan it WOULD choose are logged; no goal; `bp.state = "logged"`.

---

### 2. C1 against BRAWLY: the numbers and the plan

#### 2.1 BRAWLY_1 (trainer 266, `include/constants/opponents.h:270`), from the pinned decomp

`src/data/trainer_parties.h:3391-3413`; `src/data/trainers.h:3196-3206` (a single battle, `doubleBattle = FALSE`; the
trainer's items: 2 Super Potions, not extracted and not modelled). `world/bosses.json` matches it exactly (checked: same species, levels, moves, held items).

| # | Species L | Types | Moves | Held item |
|---|---|---|---|---|
| 1 | MACHOP 16 | Fighting | Karate Chop, Low Kick, Seismic Toss, Bulk Up | none |
| 2 | MEDITITE 16 | Fighting/Psychic | Focus Punch, Light Screen, Reflect, Bulk Up | none |
| 3 | MAKUHITA 19 | Fighting | Arm Thrust, Vital Throw, Reversal, Bulk Up | SITRUS BERRY |

#### 2.2 C1's party at the start (probe-C1, RUSTBORO (19,53), md5 e909e537)

From `s53/ch6probe11/out/probe11/probe11-B-C1-6365/ai_player.log` L30 (levels, HP) and L1211-1240 (moves as the fights
show them): Grovyle L21 57/57 [Pound, Pursuit, Absorb, Quick Attack]; Poochyena L6 21 [Tackle, Howl]; Wurmple L3 16
[Tackle, String Shot]; Seedot L3 16 [Bide, Harden]; Shroomish L5 21 [Absorb, Tackle]; Cascoon L5 20 [Harden].

#### 2.3 Both halves per boss Pokemon, and the solo duel at full HP (`out_none.txt`)

Cell = attack half (best move, its `move_value`, its type multiplier) / threat half (the boss's best move by `move_value`
with verdict powers) / the solo duel (WIN with the member's HP share left, or LOSE).

| Candidate (moves at that level) | vs MACHOP L16 | vs MEDITITE L16 | vs MAKUHITA L19 |
|---|---|---|---|
| Grovyle L21 [Pound, Pursuit, Absorb, Quick Attack] | Pound 40 (x1) / Low Kick 90 / LOSE | Pound 40 (x1) / Focus Punch 225 / WIN 1.00 | Pound 40 (x1) / Vital Throw 105 / LOSE |
| Wurmple L3 [Tackle, String Shot] | Tackle 33 (x1) / Low Kick 45 / LOSE | Tackle 33 / FP 112 / WIN 1.00 | Tackle 33 / Vital Throw 52 / LOSE |
| Cascoon L5 [Harden] | none 0 / Low Kick 45 / LOSE | none / FP 112 / LOSE | none / Vital Throw 52 / LOSE |
| Shroomish L5, Poochyena L6, Seedot L3 | x1 Normal moves / LOSE | WIN except Seedot (Bide: no damage modelled) | LOSE |
| Dustox L13 [Harden, Confusion, Gust] (from Cascoon) | Confusion 100 (x2) / Seismic Toss 30 / LOSE | Gust 80 (x2) / FP 56 / WIN 1.00 | Confusion 100 (x2) / Vital Throw 26 / WIN 0.15 |
| Dustox L16 (same moves) | Confusion 100 (x2) / Seismic Toss 30 / **LOSE** (three Seismic Tosses = 48 = its HP) | WIN 1.00 | WIN 0.38 |
| Dustox L18 [Harden, Confusion, Gust, Protect] | Confusion 100 (x2) / Seismic Toss 30 / **WIN 0.40** | Gust 80 (x2) / WIN 1.00 | Confusion 100 (x2) / WIN 0.23 |
| Beautifly L16 [Tackle, Absorb, Poison Sting, Gust] (from Wurmple, Silcoon L7) | Gust 120 (x2, STAB) / Seismic Toss 30 / WIN 0.33 | WIN 1.00 | WIN 0.12 |
| Dustox L16 [Tackle, Confusion, Poison Sting, Gust] (from Wurmple, Cascoon L7) | LOSE | WIN 1.00 | WIN 0.38 |
| Grovyle L26 | Pound / WIN 0.33 | WIN 1.00 | LOSE |
| Grovyle L29 [Pound, Pursuit, Leaf Blade, Quick Attack] | Leaf Blade 105 / WIN 0.80 | WIN 1.00 | WIN 0.11 |

What the table shows: the typing half is decisive against Makuhita (Vital Throw 105 against Grass, 26 against
Bug/Poison), and Seismic Toss is what keeps a resistant counter from walling Machop (M1): 16 points a hit whatever the
typing, so a Dustox needs about L18 (53 HP) to survive the two turns it needs.

#### 2.4 Hand checks (not from the script)

- **Dustox L18 vs MACHOP L16, WIN 21/53.** Dustox typical HP `(2*63+15)*18//100+18+10 = 53`. Machop's best: Seismic Toss
  16 (Low Kick 60 x1.5 x0.25 rounds to 7, Karate Chop to 3). Confusion: `((2*18//5+2)*50*30/27)/50+2 = 12`, x2 = 24,
  x0.925 = 22.2 of 48 = 0.4625 -> rough 0.5 -> 24 points: 2 hits. Foe first: 53-16=37, 48-24=24; 37-16=21, 24-24=0. WIN
  with 21/53 = 0.40. Matches.
- **C1 at its fight, Grovyle L22 60/60 vs MACHOP: NOT READY, Machop 12/48 left.** Machop's best is 16 (Low Kick 60 STAB:
  9.2 x1.5 x0.925 = 12.8 of a typical 63 -> 0.25 -> 16; Seismic Toss 16). Pound: `((10)*40*36/27)/50+2 = 12.67` x0.925 of
  48 -> 0.25 -> 12 points: 4 hits; Grovyle survives 3 (48 < 60, 64 >= 60): it faints before its fourth with Machop at 12
  (0.25); the five L3-6 members fall one hit each. The real game: Grovyle "fell from 100% to 7% in three turns" and C1
  never got past Machop (design §1.7). The verdict agrees with all three recorded losses.

#### 2.5 The verdicts that calibrate it (T3's fixtures: parties at their fights, TYPICAL stats)

| Run (personality) | Party at BRAWLY | Real outcome | Verdict |
|---|---|---|---|
| C1 (Story) | Grovyle L22 60 + five L3-6 | lost 3 of 3 | **NOT READY** (all fainted vs MACHOP, its HP 0.25) |
| C2 (Catcher) | Combusken L23 69 [Scratch, Ember, Double Kick, Peck] + five L3-4 | lost | **CLOSE** (MACHOP and MEDITITE fall to Peck; MAKUHITA stands at 0.35) |
| C2 (Catcher) | Combusken L24 71 (the same) | won | **CLOSE** (MAKUHITA at 0.35) |
| C3 (Trainer) | Marshtomp L25 77 [Tackle, Bide, Mud Shot, Water Gun] + five L3-8 | won first try | **READY** (0.58 >= 0.40) |
| today's rule (`strongest_level >= max level + margin`) | C1 | — | READY (22 >= 20): the rule that sent C1 in |

Caveat (the design's T3 caveat stands): calibrated on three trajectories, not validated. It is deliberately pessimistic
(foe first, worst move, no speed, Low Kick 60) and still calls the two real wins READY/CLOSE.

#### 2.6 C1's options and the plan (Story)

| Trainee (leads; rest as they are) | First READY level (worst branch) | Party left | Cost `L^2 - l^2` | Eligible in BP-1 |
|---|---|---|---|---|
| **Wurmple L3** | **L18 (Dustox branch; the Beautifly branch is better)**: Machop and Meditite fall to Dustox, Makuhita to Grovyle after Dustox faints | 0.44 | **315** | yes (Tackle) |
| Cascoon L5 | L19 (Dustox) | 0.34 | 336 | **no** (Harden only: switch training, BP-2) |
| Grovyle L21 | L30 (Leaf Blade at L29) | 0.62 | 459 | yes |
| Shroomish L5 | L24 (Breloom, Mach Punch at L23) | 0.36 | 551 | yes |
| Poochyena L6 | L30 (Mightyena; Dark: weak to Fighting) | 0.33 | 864 | yes |
| Seedot L3 | never by L30 (Nuzleaf is Grass/Dark: x2) | — | — | yes |

**The plan: raise Wurmple (by its PID) to L18.** Near-best set for Story: `cost <= 315 / 0.85 = 370.6` -> {Wurmple} only,
so every seed picks it (Catcher: `<= 393.75`, also {Wurmple}).

**Why this and not the design's catch-a-Sableye:** it needs no PC, no ball, no hunt; it uses the party's OWN future
counter (M3, S2), which the design would have deposited; its two evolution branches both resist Fighting x0.25 and
reach Confusion or Gust (x2 against all three) by L13; and the duel shows that Seismic Toss, not typing, sets the level
it needs (L18, not the "full counter" L14 the design's class rule would have set: m11). Training Grovyle instead (the
only plan today's code can express) costs about half again as much (459) and leans on a single Pokemon.

**Where it trains (map rule, §3.1):** Route 104 (land L3-5) while L3-4, Petalburg Woods (L5-6) from L4, Route 116 (L6-8)
from L6 (`encounters.json`; all three visited and reachable from RUSTBORO before the boat). Pre-registered estimate (mine,
not measured): about 110 wild battles, about 300,000 frames (150,000-450,000).

---

### 3. The trainee rule (M4) and the one per-boss budget (M5)

#### 3.1 The raise goal

- **Goal:** `Goal("raise", why, boss_milestone_id, steps=errands.train_session, key="raise")` chosen in
  `GoalManager.next_goal` at the place of step 5 (TRAIN), when a plan is active for the next boss (`bp.state == "active"`),
  the party is not hurt, `_allowed("raise")`, and a raise map is reachable. It is NOT conditioned on `fight_next` (the
  plan is made at the start, RUSTBORO, where the grass is; at DEWFORD there is none).
- **One budget (m11):** while a plan is active for a milestone, step 5's `train` goal for that milestone is not chosen.
- **Map:** among maps the AI has visited with grass (`inside_grass`) and a known way (`world_distance < UNREACHABLE`),
  whose `encounters.json` entry has `availability == "normal"` and land slots: the one with the highest land `max_level`
  that is `<= trainee level + 2`; ties: nearer. None qualifies: the reachable one with the lowest `max_level`. None
  reachable: `bp.state = "spent"` ("no grass within reach for the raise").
- **Lead:** before every raise roam, if the game's slot-0 PID is not the trainee's, the new hand
  `hands/party_order.py` `lead_with(hands, pid, why)` puts it first (START -> POKéMON -> the trainee -> SWITCH -> slot 0;
  the `start_menu`, field `party` and `party_action` UI kinds; `PARTY_MENU_ACTIONS` has SWITCH, `eyes/screens.py:352`).
  Success = the game's party slot 0 PID equals the trainee's and the PID multiset is unchanged. A failure counts
  `reorder_fails`. Also on entering the boss's gym map: re-lead if slot 0 is not the trainee (Gen 3 battles can leave
  the order changed).

#### 3.2 Experience stays on the trainee (M4)

1. `GoalRunner` sets `mind.purpose = "raise"` and `mind.trainee = pid` for a raise goal (next to `goals.py:2390`), and
   clears `trainee` after it.
2. In purpose `raise`: `BattleMind._switch` returns None (no switch to a stronger member: a switch splits the experience);
   no catch or ball decision (a person training a Pokemon fights); `_run_or_not` treats `raise` exactly as `train`
   (`battle.py:1267`: run when low, or from a foe 6+ levels above).
3. Rest: `roam_hooks` for a raise sets `nav.battle_rest = trainee_rest(look, pid, heal_below, active)`:
   **the trainee (by PID) fainted, or under a third of its max HP** -> stop and heal; otherwise today's `training_rest`.
   (Today's `needs_rest` is keyed on the STRONGEST, `battle.py:601-608`, so a fainted L3 trainee leaves the party at
   135/151 = 89 % and Grovyle would fight every later battle: the critique's M4.)
4. At every raise battle's first look, the own battler's PID is logged; one whose lead is not the trainee ends the roam
   ("the trainee is not leading") and counts a `reorder_fails`.
5. The one leak kept: when the trainee faints mid-battle, the game's replacement (today's rule) finishes that battle and
   earns its experience. The roam then ends (rule 3). Each such battle counts `leak_battles`; the A/B reports it.
6. Experience is MEASURED: at each raise roam's start and end the summary EXP of the trainee and of the strongest other
   member are logged (`[AI-BOSSPREP] raise exp: trainee +X, others +Y`).

#### 3.3 The per-boss budget (M5), exact

One record, `GoalManager.memory.fight_prep[<boss milestone id>]["bp"]` (game memory, persisted: `game_memory.py:144`,
so a continue keeps it: m9):

```
{"plan": "raise:<pid hex>:<target>", "trainee": <pid>, "target": <int>, "state": "active|done|spent|logged|none",
 "battles": 0, "frames": 0, "sessions": 0, "stalls": 0, "reorder_fails": 0, "leak_battles": 0,
 "failed": [], "losses": 0, "hunt_encounters": 0, "balls_thrown": 0}
```

| Bound (per boss) | Story | Catcher | Trainer |
|---|---|---|---|
| `battles`: wild battles begun inside raise roams | 160 | 200 | — (logs only) |
| `frames`: frames from each raise goal's start to its end (travel, roam, the heal it ends in) | 450,000 | 550,000 | — |
| `stalls`: consecutive raise sessions with no trainee level gained | 12 | 12 | — |
| `reorder_fails` | 3 | 3 | — |
| `hunt_encounters`, `balls_thrown` | 0 (BP-2's half of the same budget) | 0 | — |

The first bound reached sets `state = "spent"` and logs "budget spent: no endless grind"; the boss is then fought as
today. A raise battle WON and a trainee level gained count as progress for `STORY_PATIENCE` exactly as training does
(`mode.py:114-117`; include `raise` wherever `train` is counted there).

**After a loss to that boss** (a lost battle on the boss's gym map while the plan exists): `losses += 1`. If `state ==
"done"`: append the plan to `failed`, re-judge, and choose again among options NOT in `failed` (the same trainee at a
higher target is a different plan) within the remaining budget and only if a raise map is reachable; else fight as
today. `MAX_LOSSES` (`mode.py:113`, run-wide 3) stays the run's stop (m9: the ladder therefore has at most 2 steps for
the whole run; not changed in BP-1).

---

### 4. The changed files and functions

| File | Change |
|---|---|
| `knowledge/seasoned.py` (NEW loader) | `evolutions(species) -> tuple[(method, level|None, into)]`, `level_up(species) -> tuple[(level, move)]`, `land_levels(map_const) -> (min, max) | None`. Reads ONLY: `species[].symbol/name/evolutions[].method/parameter.value/into`; `learnsets species[].symbol/level_up[].level/move`; `encounters maps[].map/availability/methods.land.slots[].min_level/max_level`. Symbols map to facts names through the entries' `name` / `move_named` (T11 checks every one maps). |
| `knowledge/atlas.py` | `boss_party(name) -> tuple[BossMon, ...]` (species, level, moves, held_item; reads only `bosses`, `name`, `party`, `species`, `level`, `moves`, `held_item`). |
| `brain/bossprep.py` (NEW) | `BossMon`, `Member`, `Verdict(cls, party_left, log, kos)`; `next_boss(milestones, current)`; `project`; `attack_half`, `threat_half`; `verdict_slot`; `hit_points`; `verdict`; `options`; `choose_plan(rng, temper)`; `trainee_rest`; constants `CAUTION`, `ACT_ON = frozenset({"BRAWLY"})`, `BUDGET`, `FLAIL_TABLE`, `BERRY_HP`, `LOW_KICK_POWER = 60`, `MULTI_HIT_FACTOR = 3.0`, `RAISE_LEVEL_SPAN = 11`; `BossprepFaults` (the fault switches of §5.2, test side only). No `look.storage`, no hidden key. |
| `brain/battle.py` | `power` keyword on `move_value`, `_formula_share`, `rough_share` (default None: unchanged); `BattleMind.trainee: int | None = None`; purpose `raise` in `_switch` (None), the catch decision (off) and `_run_or_not` (as `train`). |
| `brain/goals.py` | the verdict run per decision (cached), the plan, the `raise` goal (§3.1), skipping step 5's `train` for a milestone with an active plan, the runner branch (`goal.kind in ("train", "catch", "raise")` at :2606, the raise map, `lead_with`, `roam_hooks(trainee=pid)`, `mind.purpose`/`trainee`, the `bp` accounting and budget, the after-loss rule). |
| `hands/party_order.py` (NEW) | `lead_with(hands, pid, why) -> Generator[..., bool]` on the existing `menus.wait_for_ui` / `move_cursor` / `choose`. |
| `mode.py` | the `f"{seed}:bossprep"` stream (built beside `:battle`, `:story`); `raise` counted as progress for `STORY_PATIENCE`; the end note's `fight_prep` already carries `bp`. |
| `gates/check_fairness.py` | `LOADERS["knowledge/seasoned.py"] = ("seasoned/species.json", "seasoned/learnsets.json", "seasoned/encounters.json")`; `world_files` also returns `seasoned/` names; every key path of the three files classified in `KNOWLEDGE_FIELDS` (a Pokedex or guide shows it -> AI: types, abilities, evolutions, level-up/TM/tutor/egg moves, where a species lives and its levels and shares; HIDDEN: `base_stats`, `catch_rate`, `base_exp`, `growth_rate`, `wild_held_items`; `_*` META; decomp refs and `*_source` DEVELOPER); `bosses[].party` description updated ("read by atlas.boss_party"). |
| `gates/test_bossprep.py` (NEW), `gates/test_kb2.py` | §5.1 tests; pinned-keys tests for `boss_party` and `seasoned.py` (the `test_k_f3c` pattern). |
| `gates/revert_bossprep.py` (NEW), `gates/run_regression.py` | §5.2 mutants, registered as a revert driver. |
| `gates/probe_bossprep.py` (NEW, test side) | prints the verdict, options and plan from a start state's eyes (the A/B discriminator, §5.4). |

---

### 5. Tests, mutants, live A/B

Every FAULT arm must change the named value on its fixture; every CONTROL must not. Fixtures for T1-T9 are built in
code from §2's parties (TYPICAL stats: `stats=()`), plus the real BRAWLY entry from the knowledge.

#### 5.1 Offline tests (`gates/test_bossprep.py` unless named)

| Test | Expected (from the built code) | FAULT -> what changes | CONTROL (unchanged) |
|---|---|---|---|
| **T1 two halves** | §2.3's cells, e.g. Dustox L18 vs MACHOP: Confusion 100 (x2) / Seismic Toss 30 / WIN 21/53; vs MEDITITE: Gust 80 (x2) | `types_only` (attack half with `BattleFaults(ignore_types=True)`): Dustox L18 vs MEDITITE becomes Confusion 50 (x1); C2 L23 CLOSE -> NOT READY (MAKUHITA 1.00 left, Combusken picks Scratch). `moves_only` (threat half 0): C2 L23 CLOSE -> READY 0.79; C1's plan Grovyle L23. `fp_always` (Focus Punch never fails): Grovyle L21 vs MEDITITE WIN 1.00 -> LOSE | Grovyle L21's row under `types_only` (Normal moves, no STAB either way); `power=None` gives byte-identical `move_value`/`rough_share` for every move in `moves.json` against every type pair (today's callers) |
| **T2 fixed damage** | Seismic Toss from MACHOP L16 = 16 points on Dustox (x0.25) and on Grovyle; 0 on a Ghost (a Shuppet fixture) | `fixed_resisted` (scaled by the chart): Wurmple's target 18 -> 13 (Beautifly worst), Cascoon's 19 -> 13. `no_immunity`: the Ghost takes 16 | Grovyle's option (L30) and C3's READY 0.58 under `fixed_resisted` |
| **T3 verdict classes** | §2.5: C1 NOT READY (MACHOP 12/48), C2 L23 CLOSE, C2 L24 CLOSE, C3 READY 0.58 | `strongest_level` (today's rule): C1 READY. `no_sitrus`: C2 L24 CLOSE -> READY 0.56, Wurmple's target 18 -> 17. `flail_flat` (Reversal power 1): Dustox L18 vs MAKUHITA 0.23 -> 0.47 | C1 NOT READY under `no_sitrus` (MACHOP is first; the berry never fires) |
| **T4 projection (M3)** | Wurmple L3 -> L18: two branches; worst = Dustox [Tackle, Confusion, Poison Sting, Gust]; Cascoon L5 -> L13 = Dustox [Harden, Confusion, Gust]; Cascoon -> L20 = [Moonlight, Confusion, Gust, Protect] (`learn_choice` forgot Harden) | `no_projection` (current species and moves): Wurmple's first READY 18 -> 28; Cascoon and Grovyle never READY by L30 | projecting a member to its own level returns it unchanged |
| **T5 plan** | C1 Story at the start: options exactly §2.6 (costs 315, 459, 551, 864; Seedot none; Cascoon ineligible); plan = Wurmple L18 on each of 20 seeds | `eligible_cocoon`: Cascoon (336) joins the near-best set; some of the 20 seeds pick it. `cost_by_level_gap` (`L - l`): Grovyle (9) beats Wurmple (15). `rechoose` (no commit): a plan stored, then Grovyle +1 level, a re-choice happens | Trainer on the same fixture: no `raise` goal; its goals list equals the parent's |
| **T6 trainee rule (M4)** | `trainee_rest` on C1's party with Wurmple fainted, the rest full: a reason | `rest_by_strongest` (today's `training_rest`): None (135/151 = 0.89 >= 0.6, Grovyle healthy). `switch_in_raise`: trainee Wurmple vs a wild Taillow (threat x2), Grovyle in the party -> a switch Decision. `catch_in_raise`: balls in the bag and a yes draw -> a ball Decision | trainee and party healthy: both rules None; purpose `train` still switches and catches exactly as the parent (same fixtures) |
| **T7 budget (M5)** | Story: spent at 160 battles, at 450,000 frames, at 12 stalls, at 3 reorder fails (whichever first); `train` not chosen for the milestone while `active` | `no_bound`: never spent. `two_budgets`: `train` sessions also run and `TRAIN_SESSIONS` is consumed | 159 battles / 449,999 frames / 11 stalls: still active |
| **T8 persistence and after-loss** | a save/continue round trip keeps `bp`; a loss with `state == "done"` adds the plan to `failed` and the next plan differs | `not_persisted`: `bp` empty after the continue. `same_plan`: the same plan string again | a loss with `state == "spent"`: no new plan |
| **T9 next boss** | from `ch6_briney_house` and from `ch7_brawly`: BRAWLY; from the first milestone after `ch7_brawly`: the next gym's leader | `current_only` (today's `fight_next`): None at `ch6_briney_house`. `act_on_all`: a NOT READY ROXANNE fixture (the builder builds one from a Torchic party; it must read NOT READY before it is used) gets a `raise` goal | at `ch7_brawly` both rules name BRAWLY; with `ACT_ON` as shipped the ROXANNE fixture gets no goal |
| **T10 reorder (driven, live fixture)** | from the probe-C1 start: `lead_with(Wurmple's PID)`; the game's party slot 0 PID == Wurmple's; the PID multiset unchanged | `reorder_by_slot` (the hand given slot 1 shifted by one): slot 0 PID != Wurmple's | `lead_with(the current lead's PID)`: no press, party unchanged |
| **T11 loaders, fairness, purity** | `check_fairness` PASS with the seasoned files classified; `check_purity` CLEAN (n3); every learnset move and evolution target maps to a facts name; `boss_party("BRAWLY")` equals §2.1 (held item included: RULING 44); Oran Berry's 10 confirmed in `items.h` | planted `entry["catch_rate"]` or `["base_stats"]` in `seasoned.py` -> B2/B3 FAIL; planted `look.storage` in `bossprep.py` -> the pinned AST test FAILS (m5); mapping without the `_`->space step -> unmapped count > 0 | the existing loaders' pinned-keys tests (`test_k_f3c`) unchanged |
| **T12 chapters 1-5 unchanged** | (a) offline: the verdict over every recorded chapters 1-5 named-fight start (the probe records' parties) is REPORTED, class per fight (calibration for BP-2; no assertion, since `ACT_ON` blocks action). (b) LIVE replay: the newest ledger run of chapters 1-5 from the New Game start (`gates/ledger.py`), its Story seed, same start and frames, arm A = BP-1's parent, arm B = BP-1: identical goal sequence, battle decisions and end-state md5, the `[AI-BOSSPREP]` lines filtered | FAULT arm on the same seed: B with a planted extra draw from the `:story` stream in each verdict run -> the replay DIVERGES (proves the check is not vacuous); if T12a found a NOT READY ROXANNE start, `act_on_all` on that start is the fault arm instead | `run_regression.py --full` PASS |

#### 5.2 Mutants (`gates/revert_bossprep.py`, the `revert_step*` pattern; each must be killed by the test named)

`types_only` (T1), `moves_only` (T1/T3), `fp_always` (T1), `fixed_resisted` (T2), `no_immunity` (T2), `strongest_level`
(T3), `no_sitrus` (T3), `flail_flat` (T3), `no_projection` (T4), `eligible_cocoon` (T5), `cost_by_level_gap` (T5),
`rechoose` (T5), `rest_by_strongest` (T6), `switch_in_raise` (T6), `catch_in_raise` (T6), `no_bound` (T7), `two_budgets`
(T7), `not_persisted` (T8), `same_plan` (T8), `current_only` (T9), `act_on_all` (T9/T12), `reorder_by_slot` (T10),
`storage_read` (T11). Dropped from the design's list: "`held_item` read" (RULING 44 makes it the correct behaviour, M2).
The scratch fault arms already show each of `types_only`, `moves_only`, `fp_always`, `fixed_resisted`, `no_sitrus`,
`flail_flat`, `strongest_level` and `no_projection` changing §2's numbers (`out_<fault>.txt`; `no_projection` is the
script's `no_evolution`); the builder's mutants must
reproduce those changes from the built code.

#### 5.3 The live A/B (development, never graded)

- **Start:** `probe-C1` (`s53/ch5stops/out/probe/probe-C1`, RUSTBORO (19,53), md5 e909e537), target `ch7_brawly`,
  1,200,000 frames, wall 9,000 s, 3 at once, the #111 harness copied (`s53/ch6probe11/arms11.py` -> a BP-1 copy).
- **Arms:** A = BP-1's parent commit on `wip/ch6-ch7`; B = BP-1. Same seeds in both arms (paired).
- **Seeds:** 6365 (#111's; arm A there is #111's trajectory REPLAYED if the parent's play-code digest equals #111's
  `03f82b7d06832ad1`: say "one trajectory, replayed", n4), 6337 (#107's), and 6371 (new; if the ledger shows it used on
  this start, the next unused integer above). Three trajectories per arm, not a rate.
- **Pre-registered prediction (hashed, sha256, before launch):** A: no BADGE02 on all three (C1's base lost 3/3 on 6365
  and 6337). B: the plan is Wurmple -> L18 on all three; the raise takes 150,000-450,000 frames (estimate 300,000);
  B reaches BRAWLY on all three; B sets BADGE02 on at least 2 of 3; in each B win the trainee's PID is on the field when
  MACHOP and MEDITITE faint; B's Grovyle level at BRAWLY's first turn <= A's + 1.

#### 5.4 The discriminator, computed offline BEFORE any run

`gates/probe_bossprep.py --start probe-C1` (the built code, the eyes on the start state, the real summary stats):
- arm A's rule: `strongest_level 21 >= training_target 20` -> no training for BRAWLY (and DEWFORD's grass is out of
  reach); no plan.
- arm B: next boss BRAWLY; verdict NOT READY; options with Wurmple's PID first; plan = Wurmple, target in [16, 20].
- **If B's class is not NOT READY, or its plan is not Wurmple, or the target is outside [16, 20]: STOP.** The spec and
  the built code disagree; reconcile before spending a run (it is not a result).

#### 5.5 The claim, read from the GAME (the AI's log only quoted beside it)

Per run: (1) `FLAG_BADGE02_GET`; (2) the battle with `gTrainerBattleOpponent_A == 266` (TRAINER_BRAWLY_1) and its
`gBattleOutcome` (1 = won); (3) for each of BRAWLY's three Pokemon, on the record where its HP reaches 0, the player
battler's PID (`gBattleMons[0].personality`) mapped to species and level through the game's party data: WHO took each
knockout; (4) at BRAWLY's first turn: slot-0 PID, the trainee's species and level, Grovyle's level (both arms: M4's
confound check); (5) frames: the raise's total (from `bp.frames` and the records' goal spans), frames to BADGE02,
`bp.battles`, `bp.leak_battles`, the trainee's and the others' EXP gained in raise roams.

**How the result reads:** B wins and the trainee took >= 1 knockout and Grovyle is not above A's + 1 -> the plan
changed the outcome on these trajectories (not a rate). B wins with every knockout Grovyle's, or Grovyle well above A's
-> confounded (M4's leak): a finding, not a success. B loses with the trainee at target -> the verdict was optimistic:
BP-2 calibration. B's raise spent its budget -> the budget or the map rule: a finding. **A run that ends on its frame
budget before BRAWLY is INCONCLUSIVE, never "B did not earn BADGE02" (m12).** Before trusting a B win, confirm the
trainee evolved in the game (its species at BRAWLY is Beautifly or Dustox): an evolution has been seen completing under
the AI's hands before (probe #104, `skills/battle.py:162-166`), but not for this trainee.

---

### 6. What stays OUT of BP-1

- **BP-2:** the PC (deposit and withdraw, box eyes), the catching HUNT (a named species, the hunt's catch rule that
  weakens before throwing at a hard catch, `MAX_THROWS`/`MAX_WEAKEN_TURNS`, M5's `hunt_encounters`/`balls_thrown`
  bounds), ball supply and stocking up before a boss, Sableye/Taillow/Wingull/Ralts as counters; switch training for a
  cocoon (Cascoon); more than one trainee; train-the-whole-team as its own plan.
- **BP-2:** fight smarter (a boss-fight switch rule past `OUTLEVELS` and `switched_against`, m3; the boss's known move
  types in `matchup`; the earlier heal; never switching a wall out against a boosted foe, m2); CLOSE as a plan of its own.
- **BP-2:** `ACT_ON` widened to every gym leader after T12a's calibration; the rival and team bosses (a classified join,
  n6); Levitate and other type-changing abilities (m8: single-ability species only); Pokedex weight for Low Kick; the
  trainer's bag (not extracted; grep `06` before relying on it); Struggle and Foresight caveats (m1).
- **Never:** reading IVs, aiFlags, base stats, catch rates, exp yields, growth rates, wild held items, box contents not
  seen, or a PID-derived trait; any change to the bot's default behaviour; `MAX_LOSSES` per boss (a user question: m9,
  grep `06` first).

## Appendix. The script that computed section 2's numbers (`compute.py`, scratch, as it ran)

```python
"""BP-1 spec numbers (scratch, read only): the per-foe duel and the readiness verdict for C1/C2/C3 against BRAWLY_1, with
the spec's rules, built on the worktree brain's OWN functions (move_value, rough_share, type_multiplier, stab, learn_choice).

Arg 1: the worktree root (the folder holding ai_player). Arg 2 (optional): a FAULT name to run the whole report under:
  fixed_resisted  Seismic Toss scaled by the type chart (M1's fault)
  no_evolution    projections keep the current species and moves (M3's fault)
  moves_only      the threat half ignored (every foe move does 0)
  types_only      the attack half ignored (own moves valued neutral, no STAB)
  no_sitrus       the held item ignored (M2's fault)
  strongest_level today's rule: ready when the strongest member >= max boss level + margin
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

ROOT = Path(sys.argv[1])
FAULT = sys.argv[2] if len(sys.argv) > 2 else ""
sys.path.insert(0, str(ROOT))

from ai_player.brain.battle import (BattleFaults, learn_choice, move_value, rough_share,  # noqa: E402
                                    typical_stat)
from ai_player.eyes.observation import BattleMon, MonSummary, MoveSlot  # noqa: E402
from ai_player.knowledge.facts import move_fact, move_named, species_named, type_multiplier  # noqa: E402

K = ROOT / "ai_player" / "knowledge"
SEASONED_SPECIES = {e["symbol"]: e for e in json.loads((K / "seasoned/species.json").read_text("utf-8"))["species"]}
LEARNSETS = {e["symbol"]: e for e in json.loads((K / "seasoned/learnsets.json").read_text("utf-8"))["species"]}
BOSSES = json.loads((K / "world/bosses.json").read_text("utf-8"))["bosses"]

CAUTION = {"Story": 0.25, "Catcher": 0.30, "Trainer": 0.40}
MARGIN = {"Story": 1, "Catcher": 2, "Trainer": 3}
FLAIL = ((1, 200), (4, 150), (9, 100), (16, 80), (32, 40), (48, 20))  # battle_script_commands.c:749
VERDICT_POWER = {"LOW_KICK": 60, "MULTI_HIT_FACTOR": 3.0}  # weight unknown -> 60; 2-5 hits, mean 3.0 (:7147)
SITRUS_HP = 30  # items.h ITEM_SITRUS_BERRY holdEffectParam 30; battle_util.c:3323 hp <= maxHP/2


def tname(t: str) -> str:
    return t.capitalize()


def sp_name(symbol: str) -> str:
    return species_named(symbol.removeprefix("SPECIES_").replace("_", " ")) or symbol


def mv_name(symbol: str) -> str:
    return move_named(symbol.removeprefix("MOVE_").replace("_", " ")) or symbol


def slot(name: str) -> MoveSlot:
    f = move_fact(name)
    return MoveSlot(name, f.type, f.power, f.pp, f.pp)


def types_of(species: str) -> tuple[str, ...]:
    sym = "SPECIES_" + species.upper()
    return tuple(dict.fromkeys(tname(t) for t in SEASONED_SPECIES[sym]["types"]))


@dataclass
class Mon:
    species: str
    level: int
    moves: tuple[str, ...]
    max_hp: int
    hp_share: float = 1.0
    note: str = ""

    @property
    def types(self) -> tuple[str, ...]:
        return types_of(self.species)


@dataclass
class Boss:
    species: str
    level: int
    types: tuple[str, ...]
    moves: tuple[str, ...]
    held: str | None


def brawly() -> list[Boss]:
    b = next(x for x in BOSSES if x["name"] == "BRAWLY")
    return [Boss(sp_name(p["species"]), p["level"], tuple(tname(t) for t in p["types"]), tuple(mv_name(m) for m in p["moves"]),
                 p["held_item"]) for p in b["party"]]


# ---------------------------------------------------------------- projection (M3): moves and evolutions by level
def project(mon: Mon, level: int, branch_pick=min) -> list[Mon]:
    """Every way `mon` can be at `level` (a hidden-branch evolution gives two); typical max HP at a projected level."""
    if FAULT == "no_evolution" or level <= mon.level:
        if level <= mon.level:
            return [mon]
        return [Mon(mon.species, level, mon.moves, typical_stat("hp", level), 1.0, mon.note + " (no evolution: FAULT)")]
    outs = [(mon.species, list(mon.moves), [])]
    for lv in range(mon.level + 1, level + 1):
        nxt = []
        for species, moves, path in outs:
            sym = "SPECIES_" + species.upper()
            evos = [e for e in SEASONED_SPECIES[sym]["evolutions"] if e["method"].startswith("EVO_LEVEL")
                    and e["parameter"].get("value", 99) <= lv]
            targets = [(sp_name(e["into"]), path + [f"{sp_name(e['into'])} L{lv}"]) for e in evos] or [(species, path)]
            for into, p2 in targets:
                ms = list(moves)
                learned = [mv_name(m["move"]) for m in LEARNSETS["SPECIES_" + into.upper()]["level_up"] if m["level"] == lv]
                if into != species:
                    learned = [mv_name(m["move"]) for m in LEARNSETS["SPECIES_" + into.upper()]["level_up"]
                               if m["level"] == lv] + learned[:0]
                for new in learned:
                    if new in ms or move_fact(new) is None:
                        continue
                    if len(ms) < 4:
                        ms.append(new)
                        continue
                    summ = MonSummary(0, into, 0, lv, 1, 1, "", types_of(into),
                                      tuple(slot(m) for m in ms), 0, 0, False)
                    choice = learn_choice(summ, new)
                    if choice.learn:
                        ms[ms.index(choice.forget)] = new
                nxt.append((into, ms, p2))
        outs = nxt
    return [Mon(s, level, tuple(m), typical_stat("hp", level), 1.0, ", ".join(p)) for s, m, p in outs]


# ---------------------------------------------------------------- the two halves (move_value both ways)
def own_best(mon: Mon, foe: Boss, hp_share: float = 1.0):
    faults = BattleFaults(ignore_types=True) if FAULT == "types_only" else BattleFaults()
    best = None
    for i, name in enumerate(mon.moves):
        v = move_value(i, slot(name), mon.types, mon.level, hp_share, foe.types, faults)
        if v is None or v.status:
            continue
        if best is None or v.value > best.value:
            best = v
    return best


def foe_slot(name: str, foe_share: float) -> MoveSlot:
    """A boss move as the verdict values it: a variable-power move gets its verdict power (m6)."""
    f = move_fact(name)
    if f.effect == "LOW_KICK":
        return MoveSlot(name + "*", f.type, VERDICT_POWER["LOW_KICK"], None, None)
    if f.effect == "FLAIL" and FAULT != "flail_flat":
        scale = int(48 * max(0.0, foe_share))
        return MoveSlot(name + "*", f.type, next(p for cut, p in FLAIL if scale <= cut), None, None)
    if f.effect == "MULTI_HIT":
        return MoveSlot(name + "*", f.type, int(f.power * VERDICT_POWER["MULTI_HIT_FACTOR"]), None, None)
    return slot(name)


def foe_threat(foe: Boss, mon: Mon):
    """The threat half: the boss Pokemon's strongest known damaging move against the candidate's TYPING (move_value)."""
    best = None
    for i, name in enumerate(foe.moves):
        v = move_value(i, foe_slot(name, 1.0), foe.types, foe.level, 1.0, mon.types)
        if v is None or v.status:
            continue
        if best is None or v.value > best.value:
            best = v
    return best


def battler(species: str, level: int, types) -> BattleMon:
    return BattleMon(species, 0, level, None, None, 48, "", tuple(types), ())


def out_share(mon: Mon, foe: Boss, move: str) -> float:
    s = rough_share(slot(move), None, battler(mon.species, mon.level, mon.types), battler(foe.species, foe.level, foe.types))
    return s or 0.0


def in_share(foe: Boss, mon: Mon, name: str, foe_share: float, member_damaging: bool) -> float:
    """One hit of the boss move on the member, as a share of the member's max HP (fixed damage: its level, x0 if immune;
    Focus Punch fails when the member deals damage first)."""
    f = move_fact(name)
    if f.category == "status":
        return 0.0
    mult = type_multiplier(f.type, mon.types)
    if f.effect == "FOCUS_PUNCH" and member_damaging and FAULT != "fp_always":
        return 0.0
    if f.fixed_damage:
        if mult == 0:
            return 0.0
        flat = foe.level if f.effect == "LEVEL_DAMAGE" else 0
        if FAULT == "fixed_resisted":
            flat = int(flat * mult)
        return flat  # HP POINTS
    if FAULT == "moves_only":
        return 0
    s = rough_share(foe_slot(name, foe_share), None, battler(foe.species, foe.level, foe.types),
                    battler(mon.species, mon.level, mon.types))
    s = s or 0.0
    return round(s * typical_stat("hp", mon.level))  # HP POINTS (its share of a typical Pokemon of the member's level)


@dataclass
class Fight:
    won: bool
    log: list = field(default_factory=list)
    party_left: float = 0.0


def verdict(party: list[Mon], lead: int, team: list[Boss], personality: str) -> Fight:
    hp = [round(m.hp_share * m.max_hp) for m in party]  # HP POINTS
    order_used = []
    field_i = lead
    log = []
    for foe in team:
        foe_max = typical_stat("hp", foe.level)
        fp = foe_max
        sitrus = foe.held == "ITEM_SITRUS_BERRY" and FAULT != "no_sitrus"
        for _turn in range(80):
            f = fp / foe_max
            if hp[field_i] <= 0:
                alive = [i for i in range(len(party)) if hp[i] > 0]
                if not alive:
                    return Fight(False, log + [f"all fainted vs {foe.species} (its HP {f:.2f})"], 0.0)

                def rank(i):
                    a = own_best(party[i], foe)
                    t = foe_threat(foe, party[i])
                    return ((a.value if a else 0.0) / max(t.value if t else 1.0, 1.0)) * (0.5 + 0.5 * hp[i] / party[i].max_hp)
                field_i = max(alive, key=rank)
            me = party[field_i]
            mine = own_best(me, foe, hp[field_i] / me.max_hp)
            dmg_out = round(out_share(me, foe, mine.name) * foe_max) if mine else 0  # a hit lands
            options = [(in_share(foe, me, n, f, mine is not None), n) for n in foe.moves]
            dmg_in, used = max(options)
            p_me = move_fact(mine.name).priority if mine else 0
            p_foe = move_fact(used).priority
            foe_first = p_foe >= p_me
            seq = ["foe", "me"] if foe_first else ["me", "foe"]
            for who in seq:
                if who == "foe" and fp > 0 and hp[field_i] > 0:
                    hp[field_i] -= dmg_in
                elif who == "me" and hp[field_i] > 0 and fp > 0:
                    fp -= dmg_out
                    if sitrus and 0 < fp <= foe_max // 2:
                        fp = min(foe_max, fp + SITRUS_HP)
                        sitrus = False
            f = fp / foe_max
            if fp <= 0:
                log.append(f"{foe.species} KO'd by {me.species} L{me.level} ({mine.name})")
                order_used.append(me.species)
                break
        else:
            return Fight(False, log + [f"{foe.species}: no result in 80 turns"], 0.0)
    left = sum(max(0, h) for h in hp) / sum(m.max_hp for m in party)
    ready = left >= CAUTION[personality]
    return Fight(ready, log, left)


def c1_party() -> list[Mon]:
    # C1's party at the start (probe11 C1 log L30: levels, HP) and its moves as the battles show them (L1211-1240)
    return [Mon("Grovyle", 21, ("Pound", "Pursuit", "Absorb", "Quick Attack"), 57),
            Mon("Poochyena", 6, ("Tackle", "Howl"), 21), Mon("Wurmple", 3, ("Tackle", "String Shot"), 16),
            Mon("Seedot", 3, ("Bide", "Harden"), 16), Mon("Shroomish", 5, ("Absorb", "Tackle"), 21),
            Mon("Cascoon", 5, ("Harden",), 20)]


def table_halves(team: list[Boss], mons: list[Mon]) -> None:
    print("| candidate | " + " | ".join(f"vs {b.species} L{b.level}: attack half / threat half / duel" for b in team) + " |")
    for m in mons:
        cells = []
        for b in team:
            a = own_best(m, b)
            t = foe_threat(b, m)
            duel = verdict([m], 0, [b], "Story")
            cells.append(f"{a.name if a else '-'} {a.value if a else 0:.0f} (x{a.effectiveness if a else 0:g}) / "
                         f"{t.name.rstrip('*') if t else '-'} {t.value if t else 0:.0f} / "
                         f"{'WIN ' + format(duel.party_left, '.2f') if duel.log and 'KO' in duel.log[-1] else 'LOSE'}")
        print(f"| {m.species} L{m.level} [{', '.join(m.moves)}] {m.note} | " + " | ".join(cells) + " |")


def main() -> None:
    team = brawly()
    print("FAULT:", FAULT or "none")
    print("BRAWLY:", [(b.species, b.level, b.types, b.moves, b.held) for b in team])
    party = c1_party()
    print("\n## C1 members now and projected (both halves, per boss Pokemon, solo duel at full HP)")
    rows = list(party)
    for idx, lv in ((5, 10), (5, 13), (5, 16), (5, 18), (5, 20), (2, 13), (2, 16), (4, 16), (0, 24), (0, 26), (0, 29)):
        for p in project(party[idx], lv):
            rows.append(p)
    table_halves(team, rows)

    print("\n## C1 verdict, Story, as it stands (lead Grovyle L21)")
    v = verdict(party, 0, team, "Story")
    print(v.won, f"{v.party_left:.2f}", v.log)
    if FAULT == "strongest_level":
        print("strongest_level rule: READY" if max(m.level for m in party) >= 19 + MARGIN["Story"] else "not ready")

    print("\n## C1 options: train ONE member to L (the rest as they are); the trainee LEADS")
    for idx in (0, 5, 2, 4, 1, 3):
        start = party[idx].level
        for lv in range(start, 31):
            worst = None
            for proj in project(party[idx], lv):
                trial = list(party)
                trial[idx] = proj
                r = verdict(trial, idx, team, "Story")
                if worst is None or (r.won, r.party_left) < (worst[0].won, worst[0].party_left):
                    worst = (r, proj)
            r, proj = worst
            if r.won:
                cost = lv ** 3 - start ** 3
                print(f"  {party[idx].species} L{start} -> {proj.species} L{lv} [{', '.join(proj.moves)}]: READY, "
                      f"party left {r.party_left:.2f}; typical exp {cost}; {r.log}")
                break
        else:
            print(f"  {party[idx].species}: never READY by L30")

    print("\n## C2/C3 verdicts at their fights (T3 calibration)")
    c2 = [Mon("Combusken", 23, ("Scratch", "Ember", "Double Kick", "Peck"), 69), Mon("Wurmple", 4, ("Tackle", "String Shot"), 18),
          Mon("Poochyena", 3, ("Tackle",), 15), Mon("Lotad", 4, ("Astonish", "Growl"), 18),
          Mon("Zigzagoon", 4, ("Tackle", "Growl"), 17), Mon("Seedot", 3, ("Bide", "Harden"), 15)]
    c3 = [Mon("Marshtomp", 25, ("Tackle", "Bide", "Mud Shot", "Water Gun"), 77), Mon("Poochyena", 8, ("Tackle", "Howl"), 24),
          Mon("Ralts", 4, ("Growl",), 17), Mon("Wurmple", 3, ("Tackle", "String Shot"), 15),
          Mon("Zigzagoon", 3, ("Tackle", "Growl"), 15), Mon("Seedot", 3, ("Bide", "Harden"), 15)]
    for name, pers, p in (("C2 Catcher L23", "Catcher", c2), ("C3 Trainer L25", "Trainer", c3)):
        for m in p:
            for mv in m.moves:
                if move_fact(mv) is None:
                    print("   unknown move", mv)
        p = [m for m in p if all(move_fact(mv) is not None for mv in m.moves)]
        r = verdict(p, 0, team, pers)
        print(name, r.won, f"{r.party_left:.2f}", r.log)
    c2b = list(c2)
    c2b[0] = Mon("Combusken", 24, c2[0].moves, 71)
    r = verdict([m for m in c2b if all(move_fact(mv) is not None for mv in m.moves)], 0, team, "Catcher")
    print("C2 Catcher L24", r.won, f"{r.party_left:.2f}", r.log)
    c1f = list(party)
    c1f[0] = Mon("Grovyle", 22, party[0].moves, 60)
    r = verdict(c1f, 0, team, "Story")
    print("C1 Story at its fight (Grovyle L22 60/60)", r.won, f"{r.party_left:.2f}", r.log)


main()
```
