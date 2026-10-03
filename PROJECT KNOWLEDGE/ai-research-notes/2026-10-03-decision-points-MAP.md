> NOTE — agent research output, NOT a source of truth. Every claim cites file:line; verify there before building on it.
>
> **Coordinator spot-check (2026-10-03, at HEAD `845029b3`).** Five citations were re-read in
> `sandbox-pokebot/plugins/custom_modes/story_mode.py`, and all five hold:
> - `:2230` `HARD_PLATEAU_LOSS_THRESHOLD = 12`;
> - `:2953` `_boss_plan_is_hopeless`;
> - `:3688` `_prepare_for_fight`;
> - `:3811` `grass_is_fodder = ... wild_max + 8 < team_max`;
> - `:3865` `target = team_max + 1  # light top-up — the boss battle is the trainer`.
>
> Every other claim, including the proposed knob names and their effects, is UNVERIFIED. A proposed env var does
> not exist until someone builds it, and each one is a story-bot change (registry `29`, a proof, a review).

Scope: `sandbox-pokebot/modules/story/`, `sandbox-pokebot/plugins/custom_modes/story_mode.py` (the `StoryMode` class actually
lives here, not in a `modules/story_mode.py`), `sandbox-pokebot/modules/battle_strategies/`. Built for `ai-agent/knowledge.py`'s
next knob round, against step 14's 78-run data (walls: Tate & Liza 16% / 11.2 losses avg / team avg level ~33 flat at both
first loss and win; E4 door: basket-short 13%, below-L65-floor 11%; Norman 11% (KI-118); Winona; Juan).

Existing learner knobs today (`ai-agent/knowledge.py` `GENES`, all catching/items): `POKEBOT_R24_CATCHHURT`,
`POKEBOT_R24_CATCHTRAIN`, `POKEBOT_R24_OVERSURVIVAL`, `POKEBOT_R24_NOFAINTBAIL`, `POKEBOT_R25_CAP`, `POKEBOT_R25_RARE`,
`POKEBOT_R23_BALLRESTOCK`, `POKEBOT_R27_KEYITEMS`, `POKEBOT_R26_KITTOPOFF`, `POKEBOT_R27_DOUBLEITEMS`, `POKEBOT_R20_OPENFENCE`.
Held FIXED (never varied): `POKEBOT_R20_TEAM6`, `POKEBOT_R20_HUNTFIRST` (both OFF; knowledge.py:23-26 says "a Claude
proposal may unlock them"). None of the walls below have a dedicated knob yet.

## 1. Catching / team building

| file:line | decides | inputs | current rule + constants | flag today | knob idea (risk) |
|---|---|---|---|---|---|
| `story_mode.py:2428` | pre-gym-1 team-catch target | `POKEBOT_R20_TEAM6` | `4` if unset, `6` if `=1` | `POKEBOT_R20_TEAM6` (FIXED=0; measured **-36 finish-rate points** in `#24-partycap` when raised, registry:165) | re-promote to a GENE now that PC-first make-room exists (registry:165 says the regression's cause may be fixed); values `4`/`5`/`6`; risk: repeats the -36pt regression if make-room still doesn't cover it |
| `story_mode.py:2518-2526` | the loop-target the catch fence reads (kept in sync w/ above) | `_catch_team_target` | returns it verbatim; `POKEBOT_R20_FAULT_TARGETLOOP=1` is a test-only desync arm | n/a (test arm, never set live) | none — this is plumbing, not a decision; tune the target above only |
| `story_mode.py` (reset_per_run_state, registry:167) | post-gym-1: catch a new species INTO the party instead of refusing as "runway" | `POKEBOT_R20_OPENFENCE`; party size | OFF by default; every other gate (hunt/training/reserve/attempt-cap) still applies when on | `POKEBOT_R20_OPENFENCE` (already a GENE) | already tunable; no new knob needed |
| `modules/story/team_policy.py:36,58-59` | which party mon is "dead weight" and how many get boxed per PC visit | level gap vs. lead, battles/KOs/survivals, HM-sole-carrier exemption | `DEAD_WEIGHT_LEVEL_GAP=8`; `MIN_PARTY_AFTER_ROTATION=3`; `MAX_DEPOSITS_PER_ROTATION=2`; `MIN_BATTLES_BEFORE_CONTRIBUTION_CALL=6` | none | `POKEBOT_DEADWEIGHT_GAP={6,8,10}`, `POKEBOT_ROTATION_DEPOSITS={1,2,3}`; risk: too aggressive deposits starters needed for rotation, too lax reproduces the 35%-dead-weight-party measurement this module was built to fix |
| `modules/story/counter_hunt.py` (box_counter_choice, ~line 331-397 per recon) | catch-attempt cap per species | `POKEBOT_R25_CAP` | `2` attempts default, `3` if `=1`; `POKEBOT_R25_RARE` exempts rare species from the cap | `POKEBOT_R25_CAP`, `POKEBOT_R25_RARE` (both GENES already) | already tunable |

## 2. Lead selection & switching

| file:line | decides | inputs | current rule + constants | flag today | knob idea (risk) |
|---|---|---|---|---|---|
| `modules/story/team_policy.py:262-297` (`lead_rank_key`) | sort key for the lead before a type-countered fight (lower=better) | `incoming` worst-case multiplier, `can_attack`, `glass_wonder_guard`, `is_hunted_counter`, `level` | tuple order: Wonder-Guard trap → can-attack → incoming → hunted-counter → level (desc); **order is the whole design**, pinned by `06-DECISIONS-LOG` 2026-08-02 | none | not a good knob target — reordering these terms was explicitly tried/rejected (option b, "weight level gap", DECLINED); leave alone |
| `story_mode.py:5119,5190,5295,5329,5460,5525,5579,5753,5900,6082` | which boss segments call `_lead_best_matchup(ace_types, hunted_pids=...)` before the fight | per-boss `ace_types`, `self._hunted_counter_pids` | called once per boss segment, re-evaluated on every retry (the chapter code re-enters `_prepare_for_fight`→lead-select→fight on each loss) | none | n/a — this already re-runs every attempt; the lead CAN change between losses if the party changed (e.g. a counter was just caught) |
| `story_mode.py` `_register_counter` / reset_per_run_state:2502 | when a hunted-counter PID starts/stops being preferred as lead | badge count at registration (`_hunted_counter_badges`) | **no per-boss expiry** — `_hunted_counter_pids` persists for the WHOLE run once set; only `pc_trip.owed_counter_pids` (PC-deposit protection) expires by badge count | none (this is KI-122's mechanism: a Norman counter can still be preferred as Tate & Liza's lead) | `POKEBOT_COUNTER_LEAD_SCOPE={whole_run, this_boss_only}`; risk: scoping it to one boss could un-lead a counter that's ALSO good for the next boss (e.g. a Fighting counter is often fine vs multiple gyms) — needs a type re-check, not a blind clear |

## 3. Training / grinding (when, where, to what level)

| file:line | decides | inputs | current rule + constants | flag today | knob idea (risk) |
|---|---|---|---|---|---|
| `story_mode.py:1876-1938` (`decide_maintenance`) | train the single weakest/laggard battler before it's excluded from the sweeper gate | battler levels, boss target, `catchup_gap`, frame estimate, heal-map availability | pick weakest below `target-TRAIN_CATCHUP_GAP`; refuse if cost unknown or `> MAINTAIN_MAX_FRAMES` | `POKEBOT_MAINTAIN` (FIXED=1, i.e. always on in every current arm) | `POKEBOT_MAINTAIN_CATCHUP_GAP={3,4,6,8,10}`; risk: too tight excludes battlers who need it, too loose reproduces the pre-#24-trainmap dead-weight problem |
| `story_mode.py:3420-3425` (`_maintain_lagging_battler`) | frame budget for that one maintenance errand | — | `MAINTAIN_MAX_FRAMES = 150_000` (measured to block a 285k-frame L40→L47 grind) | `POKEBOT_MAINTAIN_FAULT=nobudget` (test-only, raises to 10M) | `POKEBOT_MAINTAIN_MAX_FRAMES={100k,150k,200k}`; risk: too low silently skips real catch-up work, too high burns batch time |
| `story_mode.py:2191` | how close a battler must already be to the target to get readied pre-fight at all | — | `TRAIN_CATCHUP_GAP = 6` | none (used by `team_policy.DEAD_WEIGHT_LEVEL_GAP=8`, which sits one above it on purpose) | `POKEBOT_TRAIN_CATCHUP_GAP={4,6,8}`; risk: moving this without also moving `DEAD_WEIGHT_LEVEL_GAP` reopens the margin the two were tuned together to keep |
| `story_mode.py:2201` + `:3811` | is the boss's local grass "fodder" — relocate/skip training there | wild level vs. team max | **proactive** gap `FODDER_LEVEL_GAP = 12` (story_mode.py:2201); **reactive** (mid-loss-streak) gap is `8`, inline at `:3811` (`wild_max + 8 < team_max`) — two different thresholds for the same question | `POKEBOT_FODDER_RULE=xp_rate\|legacy` (`modules/story/training_areas.py:648`, default `xp_rate` since 2026-07-29) | `POKEBOT_FODDER_LEVEL_GAP={8,10,12,14}` and/or unify the two gaps; risk: Mossdeep (Tate & Liza) likely has no usable grass at all regardless of this gap — see §5 |
| `modules/story/training_areas.py` (`estimate_frames_to_level`) | frame-cost estimate gating any targeted grind | `FRAMES_PER_WILD_BATTLE=1433` (measured), `_CALIBRATED_AVG_WILD_BASE_EXP_YIELD=50.2` | `MAX_PREP_TRAINING_FRAMES = 250_000` (story_mode.py:2211) caps any single targeted grind | none | `POKEBOT_MAX_PREP_FRAMES={150k,250k,350k}`; risk: raising it lets one grind decision eat a large slice of a run's frame budget |
| `pokemon_league.py:1595,1622-1705` | **RULING 15** — League entry level floor & how many mons must clear it | party levels, `CH24_MIN_AT_FLOOR` | `CH24_LEVEL_FLOOR = 65`; need `min(CH24_MIN_AT_FLOOR, party_size)` members ≥ floor (reported `CH24_MIN_AT_FLOOR = 4`, pokemon_league.py ~1667) | none | see §8 — same knob, listed once there to avoid duplicating the entry-gate table |
| `pokemon_league.py:2032` (`train_for_league`) | pre-E4 training target | `floor=CH24_LEVEL_FLOOR` | trains toward the floor specifically, not the band logic in §5 | none | `POKEBOT_CH24_TRAIN_MARGIN={0,2,5}` (train to floor+N instead of exactly floor); risk: a thin floor margin means ONE bad matchup immediately drops a mon back under the floor at the door |

## 4. Boss preparation & counter hunts

| file:line | decides | inputs | current rule + constants | flag today | knob idea (risk) |
|---|---|---|---|---|---|
| `story_mode.py:2953-3083` (`_boss_plan_is_hopeless`) | is this boss plan unwinnable (type-chart "no answer" + loss-KO plateau) | `_defeat_counts`, `_loss_ko_history`, `ace_types` | fires only once `losses >= PLATEAU_LOSS_THRESHOLD(6)` AND the best KO count over the last 3 losses is NOT better than the 3 before; `HARD_PLATEAU_LOSS_THRESHOLD(12)` is a runaway backstop that forces hopeless regardless of the type-chart answer once 12 losses are flat over two 6-loss windows | none | see §5/top-5 — this pair of constants is the single biggest lever on every named wall |
| `story_mode.py:2264` | minimum EFFECTIVE power (power × type eff. × STAB) for a move to count as a "credible answer" | move base power, type chart, STAB | `CREDIBLE_ANSWER_POWER = 75` (raised 60→75 after a Combusken+Rock Smash STAB case still passed at 60) | none | `POKEBOT_CREDIBLE_ANSWER_POWER={60,75,90}`; risk: lowering it re-opens the exact Norman/Rock-Smash false-negative this constant was raised to close |
| `story_mode.py:3085-3345` (`_counter_ladder`) | act on a hopeless verdict: box-first withdraw, else hunt, bounded to **once per boss per run** | `needed` type names, PC box, `COUNTER_HUNT_MAX_DESTINATIONS` | box-first (next) tried first; else up to `COUNTER_HUNT_MAX_DESTINATIONS = 3` hunt destinations, each costing a `HUNT_SPIN_BUDGET_FRAMES` (120,000, in `counter_hunt.py`) | none | `POKEBOT_COUNTER_HUNT_DESTINATIONS={1,3,5}`, `POKEBOT_COUNTER_HOPS` (reachability bound, currently `COUNTER_MAX_HOPS=8`, story_mode.py ~1591, measured zero-margin for Norman's Fiery Path Machop); risk: raising hops risks walking to unreachable/far maps and burning the one hunt on nothing |
| `story_mode.py:3123-3151` — **KI-118, Norman's wall** | box-first: is a PC-boxed mon accepted as "the" counter without hunting | `counter_hunt.box_counter_choice(needed, exclude_pids, taught)` | accepts on **type match OR** a move clearing `CREDIBLE_ANSWER_POWER`; measured: an L6-10 box-caught Makuhita (type match, no credible move) gets accepted and spends the once-per-boss ladder, walling **7 of 14** arm-B Mudkip runs at Norman (`05-KNOWN-ISSUES.md:3297-3315`) | `POKEBOT_R20_FAULT_NOBOXCOUNTER` (test-only, disables the block entirely) | **top-ranked — see bottom of file** |
| `story_mode.py:2502` + registration at counter-ladder catch/box-first sites — **KI-122, Tate & Liza's wall** | how long a hunted counter stays preferred as lead | badge count at registration | **no mid-run expiry** of `_hunted_counter_pids`; a Norman-caught counter can still be `is_hunted_counter=True` (team_policy.py lead term) going into Tate & Liza | none | **top-ranked — see bottom of file** |
| `modules/story/counter_plan.py` (`find_counter_candidates`) | ranks catch targets: reachable → huntable → type coverage → verified tile → encounter rate/level fit | `needed` types, `allow` predicate | `max_results` default 10-12 depending on caller; same `CREDIBLE_ANSWER_POWER=75` gate on a move-based candidate | none | `POKEBOT_COUNTER_CANDIDATES={5,10,15}`; risk: low — breadth, not correctness; mainly a frame-cost/latency knob |

## 5. Boss RETRY policy — precise answer

**File:line: `plugins/custom_modes/story_mode.py:3688-3910` (`_prepare_for_fight`), re-entered by the per-chapter driver on every lost attempt.**

What happens after a loss, in order:
1. **The loss is auto-healed by the game itself**, not by bot code: Gen 3's whiteout (`DoWhiteOut`, decomp `src/overworld.c:358`, cited at story_mode.py:3770-3771) halves money and respawns the party, already fully healed, at the last-visited Poké Center. There is no separate "heal then retry" branch in `_prepare_for_fight` — the heal already happened before this function runs again.
2. **Losses are counted per boss key** at `story_mode.py:2576` (`self._defeat_counts[key] += 1`, inside `on_battle_ended`), with per-loss KO telemetry recorded at `:2591-2592` (`self._loss_ko_history`).
3. On re-entry, `_prepare_for_fight` recomputes `losses = max(self._defeat_counts.get(k, 0) for k in cfg["keys"])` (`:3699`).
   - **losses < 2**: proactive path — random target in the boss's level band, and a sweeper-sufficiency check that can skip training entirely if a party mon already answers the gym (`:3717-3759`).
   - **losses >= 2**: (a) try teaching an owned TM that answers the boss (`gym_tm_teach.maybe_teach_gym_tm`, `:3712-3715`); then (b) **boss-training mode** check (`:3788-3875`): if local grass is far below the team (`wild_max + 8 < team_max`, `:3811`) or no grass is mapped for this boss at all, and recent attempts have KO'd ≥1 of the boss's mons, re-attempting the boss itself is treated as the real training — **only a +1 level top-up** (`target = team_max + 1`, `:3865`), explicitly NOT the heavy escalation. This is why a wall like Tate & Liza (Mossdeep, an island with no useful local grass) shows a **flat team level across losses**: the bot is not training harder each time, it is deliberately re-attempting at ~the same level. (c) Otherwise (useful grass exists): heavy escalation, a RANDOM choice of `team_max+5`, `team_avg+5`, or `hi + 2*(losses-1)` (`:3876-3890`).
4. **Lead switching does happen every attempt** — the boss segment's own `_lead_best_matchup(ace_types, hunted_pids=...)` call (§2 table) re-runs before each fight, so the lead can change if the party changed (e.g. a new counter was just caught/withdrawn) — it is not frozen across retries, but if nothing in the party changed, the same mon is chosen again.
5. **Derail threshold**: once `losses >= PLATEAU_LOSS_THRESHOLD (6)` AND the KO trend has plateaued (`_boss_plan_is_hopeless`, `:2953`), the counter ladder (§4) gets ONE shot. If it fails: ONE "second wind" is granted — `self._loss_ko_history` for this boss is **cleared** (effectively resetting the loss-plateau clock, not the raw `_defeat_counts`) and the function returns to retry fresh (`:3827-3853`). If the SAME boss goes hopeless again after the second wind is spent, `_prepare_for_fight` raises `BotModeError` (`:3858`) — an honest stop, which the run-level recovery machinery counts as a "derail." **`HARD_PLATEAU_LOSS_THRESHOLD = 12`** (`:2230`) is a backstop that forces the hopeless verdict regardless of the type-chart answer once 12 losses show a flat best-KO count across two 6-loss windows — which lines up almost exactly with the measured **11.2 average losses per run** at Tate & Liza (6 to first hopeless check + up to 6 more after the second wind ≈ 12).

So: **it does not retry blindly at the same level as a static rule** — it retries at the same level specifically when it has judged (via the fodder test) that grinding would not help and the fight itself is the only available training, which appears to be the common case at Tate & Liza.

## 6. Items in battle

| file:line | decides | inputs | current rule + constants | flag today | knob idea (risk) |
|---|---|---|---|---|---|
| `modules/story/battle_items.py:59` (`choose_healing_item`) | use a healing item in battle, and which one | current/max HP, options, worst hit taken, uses so far | heal only below `HEAL_AT_FRACTION = 0.35` of max HP; cap `MAX_ITEM_USES_PER_BATTLE = 4`; refuses if best available heal < worst hit taken (losing-race guard) | none (an `POKEBOT_HEAL_AT_FRACTION` override is read at `double_items.py:160` but not wired as a GENE) | `POKEBOT_HEAL_AT_FRACTION={0.25,0.35,0.5}`; risk: too low wastes items on scratches, too high "donates" a turn mid-KO race |
| `story_mode.py:6424` (`_r27_key_gate`) | restrict item use to KEY trainers only | opponent trainer class via `trainer_identity.read_opponent_trainers()` | `KEY_TRAINER_CLASSES` = Leader/Elite Four/Champion/Rival/Magma-Aqua leader+admin (`trainer_identity.py:63-67`); fails OPEN (unreadable ⇒ items allowed) | `POKEBOT_R27_KEYITEMS` (already a GENE) | already tunable; a possible refinement is widening/narrowing `KEY_TRAINER_CLASSES` itself, but that is a set edit, not a clean env knob |
| `modules/story/double_items.py:113` (`guard_ok`) | is the double-battle item cursor actually on the intended mon (PID identity check) | intended PID, menu PID, slot, party count | fails CLOSED; this is a safety guard, not a tunable | `POKEBOT_R27_DOUBLEITEMS` gates the feature (already a GENE); `*_FAULT_DBL_WRONGSLOT/NOGUARD` are test-only | not a knob candidate — disabling the guard reproduces the exact wrong-slot bug it exists to stop |
| `modules/story/battle_items.py:161` (`choose_status_or_revive_item`) | cure Sleep/Freeze, or Revive as a last-mon measure | status name, non-fainted count | `TURN_COSTING_STATUSES = {Sleep, Freeze}` only (poison/burn/paralysis not cured); Revive only when `non_fainted_count <= 1`; `allow_revive=False` by default (unproven) | none | `POKEBOT_REVIVE_THRESHOLD={0,1,2}`; risk: reviving at slot-2-remaining still often loses, since the revived mon returns at 50% HP |
| `modules/story/amulet_coin.py:97,116` (`pick_holder`) | which mon holds the Amulet Coin for 2x prize money | party levels, held-item slot | highest level, empty-held-item-slot tiebreak | none | low priority — doesn't touch any named wall |

## 7. Shopping / restock / money

| file:line | decides | inputs | current rule + constants | flag today | knob idea (risk) |
|---|---|---|---|---|---|
| `modules/story/stock_topoff.py:20-21,153-176` | when to top off Poké Balls, and how many | spare balls, money, shop inventory | restock trigger `TRIGGER = 20` (= `DEX_CATCH_BALL_RESERVE(10) + DEX_CATCH_MAX_EXPECTED_THROWS(10)`); buys up to `TARGET = 30`/visit, budget capped at `min(₽6,000, (money-floor)/2)` | `POKEBOT_R23_BALLRESTOCK` (already a GENE) | `POKEBOT_R23_TRIGGER_BALLS={10,15,20,25}`; risk: below 10 risks running the dex-catch reserve dry mid-hunt |
| `stock_topoff.py:125-135` + `league_reserve.py:53` | the money floor the bot will never spend below | stage (pre/post basket-reserve era), missing basket cost | `CASH_FLOOR = ₽1,000`; once the League-basket era starts, `floor = 1,000 + 2 × missing_basket_cost` (≈ ₽109,600 before any basket items are owned) | `POKEBOT_R23_FAULT_FLOOR=<₽>` (test-only override) | `POKEBOT_R23_FLOOR_MULTIPLIER={1,2,3}` (the "×2" above); risk: below 1 leaves the League basket chronically unaffordable, directly feeding the 13% "basket short" E4 wall |
| `stock_topoff.py:219-283` (`kit_wants`/`visit_plan`) | which healing items to stock and to what per-battle target | held items minus reserve | HP ladder Potion<Super<Hyper (Max Potion excluded); target = `MAX_ITEM_USES_PER_BATTLE = 4` uses/battle; Full Heal to 2, else Awakening+Ice Heal to 1 each | `POKEBOT_R26_KITTOPOFF` (already a GENE; requires `POKEBOT_R27_KEYITEMS=1` or it's skipped, `:308-314`) | `POKEBOT_R26_HP_TARGET={2,4,6}` uses/battle; risk: below 4 risks running out mid-gauntlet |
| `victory_road.py:440-462` | the mandatory League basket contents + total cost, and the sell-to-cover-shortfall fallback | bag before, missing qty | Hyper Potion×30(₽36,000) + Full Restore×3(₽9,000) + Full Heal×8(₽4,800) + Revive×3(₽4,500) = **`LEAGUE_MIN_MONEY = ₽54,300`**; shortfall covered by selling Nuggets only (allow-list, never a deny-list) | `POKEBOT_CH23_FAULT_NOSELL` (test-only) | `POKEBOT_LEAGUE_BASKET_PROFILE={minimal,current,survival+}` (scale the quantities); risk: shrinking the basket trades a cheaper gate for a thinner in-gauntlet healing margin — this is the OTHER side of the 13% basket-short wall from the floor knob above |
| `pokemon_league.py` R1 restock path (~1699-1706, ~2880-2903) | one conditional restock attempt if the ONLY shortfall is the basket (not the level floor), only from Ever Grande/lobby | `reasons` list, location | single attempt; re-checks once; no second try | `POKEBOT_CH24_FAULT_NORESTOCK` (test-only) | `POKEBOT_CH24_RESTOCK_ATTEMPTS={1,2}`; risk: a second attempt costs an extra walk/frame budget if the first one already exposed a structural shortfall (not enough money at all) |

## 8. The Elite Four entry gate

**File:line: `pokemon_league.py:2736-2930` (`prepare_and_open_the_league`), the gate before the point of no return.**

Exact sequence: (1) level-floor check — `ch24_trainees_below_floor(CH24_LEVEL_FLOOR=65)` (`:1622`) must leave fewer than
`min(CH24_MIN_AT_FLOOR, party_size)` members short, **RULING 15** (`:1664-1705`); (2) League-basket stock check —
`ch24_readiness_shortfall` against the §7 basket; (3) if the ONLY shortfall is the basket (not the floor) and the bot is at
Ever Grande/the lobby, ONE restock attempt runs and the two checks re-run; (4) if reasons remain, it **raises `BotModeError`**
at `:2912-2927` — "§Ch24 R1: REFUSING to enter the Elite Four at ... —", quoting both shortfalls. It does not retry, does not
train, does not re-attempt restock a second time. **This is a hard stop, not a loop** — the run only gets back here if an
outer driver re-invokes the chapter.

Once inside, `run_the_gauntlet` (`:4541-4650`) uses **different** machinery than a gym leader: its own docstring says it
"does not catch, retry or recover" — a lost battle inside the gauntlet raises immediately (`beat_the_trainer_here` asserts
victory, `:3313-3326`), with no `_boss_plan_is_hopeless`/`_counter_ladder` escalation path at all. A whiteout mid-gauntlet is
additionally NOT a safe abort (KI-22 claim 1: `DoWhiteOut` clears all four `FLAG_DEFEATED_ELITE_4_*` and resets
`VAR_ELITE_4_STATE`), and stepping on `(9,1)` into `HALL5` is a one-way point of no return.

Knob candidates: `POKEBOT_CH24_MIN_AT_FLOOR={3,4,5}` (party-size-vs-floor strictness, directly targets the 11% below-floor
wall) and the §7 floor/basket knobs (directly target the 13% basket-short wall). Risk for the floor count: lowering it lets
weaker parties into a gauntlet with no retry machinery at all, which could convert a pre-entry refusal (recoverable) into an
in-gauntlet loss (NOT recoverable, per KI-22 claim 1).

## Ranked top 5 knobs for next week

1. **`POKEBOT_BOXFIRST_TIER` (`story_mode.py:3141`, `counter_hunt.box_counter_choice`)** — directly targets **Norman / KI-118**,
   the only wall here with a *measured* causal mechanism: box-first accepts a type-only match with no credible move and
   spends the once-per-boss counter ladder on it, walling 7 of 14 arm-B Mudkip runs (`05-KNOWN-ISSUES.md:3297-3315`). Values:
   `disable` (hunt instead of withdrawing) / `credible_only` (require `CREDIBLE_ANSWER_POWER`) / `any_move` (today's
   behaviour). Highest confidence of the five because the failure mode is already measured, not inferred.
2. **`POKEBOT_HARD_PLATEAU_LOSS` + `POKEBOT_PLATEAU_LOSS` (`story_mode.py:2223,2230`)** — these two constants gate the
   hopeless check / second-wind / derail cycle for **every** named wall (Tate & Liza, Norman, Winona, Juan). The measured
   **11.2 average losses at Tate & Liza** lines up almost exactly with `6 (first plateau check) + up to 6 more (post-second-
   wind) = 12 (HARD_PLATEAU)`, strongly suggesting this pair — not a type/counter problem — is what is actually bounding
   that wall. Risk: this is also the safety valve that stopped KI-23's 41-loss Winona runaway; loosening it carelessly could
   reopen that.
3. **`POKEBOT_BOSSMODE_TOPUP_LEVELS` (`story_mode.py:3865`, today hardcoded `target = team_max + 1`)** — directly explains
   the **flat team level** at Tate & Liza: once local grass is judged fodder (true for an island gym like Mossdeep) the bot
   deliberately trains only +1 level per loss instead of escalating, trusting the repeated boss attempt itself as the
   trainer. Testing a less conservative cap (e.g. +3) is a direct, cheap experiment against the flat-level evidence.
4. **A League-basket/floor pair — `POKEBOT_R23_FLOOR_MULTIPLIER` (`stock_topoff.py:134`) and/or
   `POKEBOT_LEAGUE_BASKET_PROFILE` (`victory_road.py:440-462`)** — targets the **13% "basket short" E4 door refusal**
   directly; the floor multiplier and the basket size are two sides of the same ₽54,300 requirement, so they should be
   screened together rather than separately.
5. **`POKEBOT_COUNTER_LEAD_SCOPE` (expire `_hunted_counter_pids` per boss, story_mode.py:2502 / registration sites)** —
   targets **KI-122** at Tate & Liza: a counter caught for an earlier boss has no mechanism to stop being preferred as lead
   later. Ranked last of the five specifically because, unlike #1, this mechanism is NOT yet measured as causal for Tate &
   Liza (the task brief names it as a known issue, not a graded finding) — a cheap A/B against #3 above would tell us which
   of the two actually explains the flat-level pattern before committing a knob to either.
