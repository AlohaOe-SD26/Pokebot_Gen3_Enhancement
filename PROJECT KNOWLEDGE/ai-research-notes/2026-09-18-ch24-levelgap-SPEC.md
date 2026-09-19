# §Ch24 STEPPED TRAINING LEG — DESIGN SPEC + MY VERIFICATION (2026-09-18)

> ⛔⛔ **AGENT OUTPUT IS A NOTE, NEVER TRUTH.** An 11-agent workflow (5 subsystem reads, each
> adversarially verified, then synthesised) produced the spec below. ✅ marks what **I** verified or
> computed myself. **Read this header before the spec — I refuted one of its key claims.**

---

# ⭐⭐ THE HEADLINE, VERIFIED BY ME: THE RULING IS INTERNALLY UNSATISFIABLE BY TRAINING THE MULES

USER RULING 2026-09-18: *"all pokemon in the team need to be a level between 65-75."* That is a
floor **and a ceiling**. The pinned party carries Zigzagoon L19 and Castform L36.

✅ **VERIFIED AT SOURCE.** `SwapTrainBattleStrategy` (`story_mode.py:1038-1096`) switches the
trainee out on turn 1 when *"the trainee is >= UNDERLEVEL_MARGIN levels below the foe"*, and its own
docstring says *"switch so the team-mate finishes and **the trainee keeps its XP share**."*
⇒ **two participants**, so Gen-3 splits the exp and **the finisher gains as well.**
`_capable_finisher` picks `max(safe, key=(level, current_hp))` — **always the strongest**, so one
mōn monopolises the share and stays the one monopolising it.

✅ **COMPUTED BY ME** against each mōn's REAL growth curve and its REAL `total_exp` read from
`post_ch24_atdoor_L75.ss1` (not modelled start-exp):

| | |
|---|---|
| Zigzagoon L19 → L65 | **266,953** exp |
| Castform L36 → L65 | **224,497** exp |
| **total the mules must absorb** | **491,450** exp |
| finisher `_capable_finisher` selects | **Wailord L75**, `total_exp` 583,024, Fluctuating |
| finisher after a 1:1 share | 1,074,474 exp = **L89** ⛔ |
| finisher with the ×1.5 traded-mōn boost | 1,320,199 exp = **L94** ⛔ |

⇒ **TRAINING THE MULES TO THE RULING'S FLOOR BREAKS THE RULING'S CEILING, BY 14-19 LEVELS.**

⛔ **AND I REFUTED THE SPEC'S PROPOSED ESCAPE.** §1.3 below argues the overshoot is order-dependent
and that running the mule leg first from `post_ch24ready` (battlers L47-53) keeps the finisher in
band — it estimates Sceptile lands *"~L71, still under the cap."* ✅ **My computation, same method,
both mules: Sceptile L53 absorbing 491,450 → L85.** Still far over. **The escape does not exist**,
and the spec's §1.3 should be read with that correction in front of it.
*(The spec priced Castform alone and used modelled start-exp; I used both mules and the saves' real
values. That is the whole discrepancy.)*

---

# ✅ WHAT I ALSO VERIFIED, AND IT HOLDS

* **The bot CAN deposit.** `deposit_one_dead_weight()` (`pc_trip.py:219`) is standalone and is NOT
  behind `POKEBOT_PC_ROTATION` — its own docstring contrasts itself with
  `deposit_dead_weight_if_worth_it`, which is behind that pinned-0 flag.
* ⚠ **TWO GOTCHAS THAT BREAK THE NAIVE PLAN**, both read at source: `pc_trip.py:274-276` returns
  **True having deposited nothing** when the party is already under six (so you cannot box two by
  calling it twice), and victim choice delegates to `find_dead_weight`, which sorts **ascending by
  level** (`team_policy.py:169-172`) — **the caller cannot name Castform.** Boxing two NAMED mōn
  needs a PID-addressed deposit built on the same `interact_with_pc` primitive.
* **The code's own HM rule agrees with my party audit.** `dead_weight` returns None for
  `_only_hm_carrier` (`team_policy.py:147-148`) ⇒ Wailord and Swellow are protected by the code
  itself; Zigzagoon and Castform are not, because their field moves are duplicated.

# ⭐⭐ AND THE PRACTICAL CONSEQUENCE THAT DECIDES IT

On `post_ch24_atdoor_L75.ss1`, boxing the two mules leaves **Mightyena L75, Sceptile L75,
Swellow L75, Wailord L75** — every survivor inside 65-75. ⇒ **the ruling is satisfied with ZERO
further grinding on that fixture.** The grind only returns if §Ch24 starts from the earlier
`post_ch24ready` state, and that work is required under either reading.

⇒ **THE CHOICE IS THEREFORE NOT "(a) expensive vs (b) cheap". IT IS "(a) impossible vs (b) free".**
⚠ What remains genuinely open, and is the USER's alone: whether removing two Pokémon from the
party is acceptable for an art piece whose point is watching this team play.

---

# ─── THE WORKFLOW'S SPEC, VERBATIM ───

> ‼ A NOTE, never truth. Its §1.3 escape is REFUTED above. Its labels ([READ]/[COMPUTED]/[INFERRED])
> are the synthesising agent's own, not mine.

# §Ch24 STEPPED TRAINING LEG — DESIGN SPEC

**Item:** `#24-levelgap` · **Ruling:** every team member L65–75, per‑mon targets may differ (`06-DECISIONS-LOG.md:6622`) · **Ground:** `TRAIN_SPOT_1F = (VICTORY_ROAD_1F, (15,39))` (RULING 2) · **Placement:** after §Ch23 leg 10 `heal_at_league` (RULING 5) · **Cost is not an objection; an unbounded loop still is** (RULING 4).

Labels used below: **[READ]** = I opened the file this session. **[COMPUTED]** = arithmetic I ran this session over the repo's own formulas/constants. **[INFERRED]** = reasoning from read code, not observed.

---

## 1. THE PARTY-COMPOSITION DECISION, PRICED

### 1.1 What the party actually is
From `tools/story-dev/evidence/2026-09-18-party-l65-audit.stdout.txt` **[READ]** — on `post_ch24_atdoor_L75.ss1`, `post_league_lobby.ss1`: Mightyena/Sceptile/Swellow/Wailord **L75**, **Zigzagoon L19**, **Castform L36**. On `post_ch24ready.ss1` (the ruled grind start): Sceptile L53, Swellow L48, Wailord L47, Mightyena L48 + the same two.

Sole field-move carriers: **Waterfall ← Wailord, Dive ← Wailord, Fly ← Swellow.** Zigzagoon's Rock Smash + Surf are both duplicated; Castform holds no field move. **Both stragglers are navigationally free to remove; neither battler is.**

### 1.2 The price, three models, computed this session
`estimate_frames_to_level` constants: `50.2 × 40 / 7 = 286.857` exp/battle, `1433` frames/battle (`training_areas.py:681,692,721-725` **[READ]**). Start exp taken as `exp(level)` (conservative — a partly-levelled mon needs less). Measured rate = `grind_after_fix.log:11` + `:304` **[READ]**: Wailord L60→62, 32,478 exp in 82,415 frames ⇒ **2.538 f/exp traded, 3.806 f/exp de-boosted**.

| mon | exp to L65 | raw est. | ×3.30 "corrected" | measured‑rate |
|---|---|---|---|---|
| Zigzagoon L19 | 267,766 | 1,338,422 f | **4,416,793 f = 20.4 h @×1** | 1,019,117 f ⚠ invalid, see 1.4 |
| Castform L36 | 227,969 | 1,139,235 f | **3,759,476 f = 17.4 h @×1** | 867,650 f ⚠ invalid |
| Sceptile L53 | 130,858 | 654,881 f | 2,161,107 f = 10.0 h | 498,046 f = 2.3 h |
| Swellow L48 | 169,725 | 848,336 f | 2,799,509 f = 13.0 h | 645,973 f = 3.0 h |
| Mightyena L48 | 164,033 | 819,676 f | 2,704,931 f = 12.5 h | 624,310 f = 2.9 h |
| Wailord L47 | 237,315 | 1,186,524 f | 3,915,529 f = 18.1 h | 903,221 f = 4.2 h |

**[COMPUTED]**. My ×3.30 Zigzagoon figure reproduces the audit's 20.4 h exactly, which confirms the audit's hours are ×3.30-corrected at 60 fps.

**Reading (a) "train everyone", from `post_ch24_atdoor_L75`:** only the mules ⇒ **8.18M f = 37.9 h @×1** (×3.30) / 2.48M f = 11.5 h (raw).
**Reading (b) "box the stragglers", from `post_ch24ready`:** four battlers ⇒ **11.58M f = 53.6 h @×1** (×3.30) / 2.67M f = 12.4 h (measured) — but this work is required under BOTH readings. (b) is exactly (a) minus 37.9 h.

**Units, settled:** RULING 8 pins production to ×1, so **60 fps is the user's clock** and the hours above are the honest production figure. The harness runs ~1032 f/s, so the same work is a **dev drive of ~0.5–1.3 h**. Always print both, labelled. `probe_party_l65_audit.py:182` currently calls emulator hours "wall-clock" — that label is wrong and should not be copied.

### 1.3 ⭐ THE ARGUMENT NOBODY IN THE RESEARCH MADE: swap-training puts the finishers OVER 75

`SwapTrainBattleStrategy` (`story_mode.py:1038-1096` **[READ]**) switches the trainee out on turn 1 when `active.level + 2 <= foe.level`, and its own docstring says the trainee *"was sent out first"* and *"banks its Gen-3 shared-EXP"*. Two participants ⇒ **the finisher gains the same total exp the trainee does**. The finisher is `max(safe, key=(level, current_hp))` — always the strongest, so one mon monopolises the share.

**[COMPUTED]** From `post_ch24_atdoor_L75`, training Castform L36→65 (227,969 exp) with a L75 Wailord finishing: Wailord goes 582,187 → 810,156 exp = **L82**. Adding Zigzagoon's 267,766 takes it to **L83, or L86 if the finisher's ×1.5 trade boost applies** (every exp line in `grind_after_fix.log` reads *"gained a boosted"*, so it does for Wailord). Fluctuating curve `((L//2)+32)·L³//50`, `pokemon.py:615-621`.

⇒ **Reading (a), executed on the L75 fixture, violates the ruling's own upper bound.** And it is a dilemma with no good branch:

* **swap-train fires** → the trainee levels, and the finisher blows past 75.
* **swap-train does not fire** → the L19 trainee solos a L40 wild. That is the regime `story_mode.py:2574-2575` records as **measured-unwinnable** (*"69 battles, 0/43 HP, still L13"*), and `train_team`'s only escape is the PP trigger — i.e. `#24-grindppstall`'s shape. Zigzagoon's gap is **+21**; the corpus has **never observed swap firing above +6** (`victory_road.py:3410-3416`).

Castform is different and this matters: at **+4** it sits *inside* the observed firing envelope, so Castform is plausibly trainable at `TRAIN_SPOT_1F` while Zigzagoon is not.

**[COMPUTED] The order-dependent escape.** The overshoot exists only because the finisher is already at 75. Run the mule leg **from `post_ch24ready` (battlers L47–53), before the battler grind**, and the finisher's share is not waste but progress: Sceptile L53 absorbing Castform's 227,969 exp lands at **~L71**, still under the cap. ⇒ **if reading (a) is chosen, the leg must be ordered mules-first.**

### 1.4 Why the measured rate does not price the mules
3.806 f/exp was measured on a **L60–62 lead one-shotting L36–40 wilds, 38 Won / 0 lost**. A L19 trainee on that ground is the opposite condition; frames/battle and win-rate both collapse. The mule rows above are marked invalid deliberately. **Treat the mules as unpriced under the measured model; only the ×3.30 and raw figures apply, and both are model, not measurement.**

### 1.5 Can the bot deposit? **Yes — live-proven.**
* `deposit_one_dead_weight()` (`pc_trip.py:219` **[READ]**) is a standalone generator, **not** behind `POKEBOT_PC_ROTATION`, whose contract is a postcondition re-read from the party.
* It has fired end-to-end in **real batch runs**, outside `withdraw_from_box` and outside the rotation: `tools/story-dev/x4-runs/20260826-130441/L01/stdout.txt:127918` — *"PC — depositing ONE mon to free a slot: Shedinja L24"* → *"party is now 5"*. That deposit happened at **Mossdeep**, which `probe_pc_tile.py` never scanned — so `PC_TILE=(10,1)` is already proven on an unprobed centre sharing `LAYOUT_POKEMON_CENTER_1F`, the same layout Ever Grande uses.
* **Two properties that break the naive plan [READ]:** (i) `pc_trip.py:274-276` returns **True having deposited nothing** when the party is already below six — so you cannot box both by calling it twice; (ii) it delegates victim choice to `find_dead_weight`, which sorts **ascending by level** (`team_policy.py:170-174`) — the caller cannot ask for Castform. A §Ch24 leg that boxes two named mons needs its own PID-addressed deposit built on the same `interact_with_pc` primitive.
* The `team_policy` HM exemption (`:147-148`) independently protects Wailord and Swellow and does **not** protect Zigzagoon or Castform — the code's own rule agrees with the audit.

### 1.6 ⭐ RECOMMENDATION — **a question for the USER, not a decision taken**

**Recommend (b): box Zigzagoon and Castform; train the four battlers to a per-mon floor of L65 with headroom to 75.** Confidence: **high on the mechanics, medium on the aesthetics** — the aesthetic half is the user's alone.

Why, in one line each:
1. Reading (a) cannot be executed on the L75 fixtures without pushing a finisher to **L83–86**, violating the same ruling it serves.
2. Zigzagoon at +21 is in the regime this project has already measured as unwinnable; nothing in the tree says it can be ground at `TRAIN_SPOT_1F`.
3. Boxing makes the code **correct by construction**: with the bench empty, `battler_identities()` and `_battler_slots()` finally agree, `team_is_ready(65)` grades the whole party, and `scope="whole"` stops being a trap.
4. Neither straggler is a sole HM carrier, so `assert_carriers_survived` cannot trip and the navigator loses nothing.
5. It is reversible — `withdraw_from_box` is proven. **Deposit only; never `release_pokemon_from_box`.**

**Both rulings must be quoted to the user, because two exist and they pull opposite ways** (CLAUDE.md §11 — I grepped the log first):
* `06-DECISIONS-LOG.md:6645-6647` (2026-09-18): *"⛔ **DO NOT SILENTLY PICK (b).** … this project has no user ruling permitting it."*
* `06-DECISIONS-LOG.md:4058-4060` (2026-09-04), the user **verbatim**: *"I am fine with the bot catching and training pokemon, it should be doing this as well as collecting pokemon…"* — it names neither mon nor the PC. The log author's *"It is now sanctioned"* at `:4069-4071` is **the author's inference, not the user's words**, and must be presented as such.

**Third option to put on the table:** (c) box Zigzagoon only, and train Castform in the mules-first order from `post_ch24ready`. Costs 17.4 h (×3.30) instead of 37.9 h, keeps five of six visible mons, and puts no mon over 75.

---

## 2. WHERE THE LEG LIVES

**There is no §Ch24 host.** `grep -rn "def do_pokemon_league_chapter\|def ch24_chapter_done\|CH24_SEALED_MAPS" --include=*.py .` returns **nothing**, and there are **zero production imports of `pokemon_league`** **[READ, re-run unscoped this session]**. So this is two pieces of work.

**Module.** New generator `train_for_the_league(report=None, *, targets: dict)` in `sandbox-pokebot/modules/story/pokemon_league.py`. Six cross-chapter imports from `victory_road`: `TRAIN_SPOT_1F`, `battler_identities`, `team_is_ready`, `assert_carriers_survived`, `party_identities`, `_walk_through_warp`/`_navigate_riding_out`. **Not** in `victory_road.py` — a §Ch23 function that walks the party back into Victory Road keeps `ch23_chapter_done()` False forever (`victory_road.py:3318`: `if not _on_map(EG) or any(_on_map(m) for m in VICTORY_ROAD_MAPS): return False`), and `story_mode.py:5172-5173` would then re-dispatch §Ch23 on every pass.

**Dispatcher.** Build `do_pokemon_league_chapter()` in the same file, copying `do_victory_road_chapter`'s two defining properties (`victory_road.py:3327-3345`, `:3342-3345`, `:3468-3470` **[READ]**):
* dispatch on **position**, each leg behind a guard mirroring its own precondition;
* a 3-attempt loop for `BotModeError` **only** — `except StoryAbort: raise`, never retried (KI-67).

**Wiring.** In `story_mode.py`, immediately after the §Ch23 block at `:5170-5176`. ⛔ The §Ch24 marker must be consulted **before** `ch23_chapter_done()` is asked, not after: in the League lobby all ten §Ch23 guards read False, no leg runs, and the dispatch raises after three attempts. The marker must be an **explicit map tuple**, never a group/range test — map group 16 mixes `POKEMON_LEAGUE_1F`, the Ever Grande Poké Center and League 2F.

**Leg order inside §Ch24.** `[0] marker check → [1] TRAINING (this leg) → [2] go-to-the-door (promoted `Ch24ToLeagueMode`) → [3] gauntlet`. Placing it first means no inbound Fly: §Ch23 hands off at the League door apron (18,6), from which the Poké Center is **NO PATH same-map**, so leg 1 opens with `fly_to_destination(EverGrandeCity)` → lands (27,49) → walks 22 wp to the VR apron (18,42) → `_walk_through_warp("Up")` → grind tile. That entire route is already code and already driven (`Ch24GrindMode`'s preamble, `story_harness.py:15610-15639` **[READ]**).

**How it decides it is done.** `team_is_ready(target)` is already the right shape — it appends a reason **per battler** below the floor and **returns `(bool, list)` without raising** (`victory_road.py:1889-1891` **[READ]**), so the leg can consult and decide. Three additions:
1. **Roster.** Under reading (b) no change is needed once the bench is boxed. Under (a) the roster predicate must be parameterised — and note `team_is_ready` already carries a hard guard that an **empty battler set must never grade READY** (`:1867-1884`), which is the prerequisite for touching that predicate at all.
2. **Upper bound.** Nothing anywhere reads ≤75. Add `level > 75` as a reason.
3. **Per-member conjunct + liveness.** `training_continue_reading(report)` before the readiness raise (`victory_road.py:2131-2134`), aimed at what leg 2 starts from — the **VR apron (18,42)**, not the League door.

---

## 3. THE TRAINING SHAPE

### 3.1 What `train_team` supports
```
train_team(target_level, scope="whole", grass=..., heal_center=..., slots=None)
```
`early_game.py:2069-2075` **[READ]**. **One target for the whole call.** No per-mon knob. Three paths, `slots` taking precedence over `scope` silently, and `scope` never validated (`:2106-2113`).

### 3.2 What NOT to do
* ⛔ **`scope="whole"`** — `need` comes from `_battler_slots()` (`:1965-1974`), which filters on *not-an-egg + has a damaging move* and knows **nothing** about `BENCH_SPECIES`. It would grind Zigzagoon and Castform. It also picks **strictly lowest-first** (`:2120`), so it pins on Zigzagoon for ~139 consecutive battles before touching anything else **[COMPUTED: 19→36 is 39,797 exp ÷ 286.86]**. *(It becomes correct under reading (b), once there is no bench.)*
* ⛔ **`slots={i}` with `i != 0`** — KI-84. The index set is computed before `_rotate_lead_safely` **swaps**, so the next round reads the displaced old lead and `need` empties. Measured: 900k frames → 8 battles, Swellow +0.
* ⛔ **`train_for_victory_road(target=t)` once per mon** — `target` is the **function parameter**, consumed at seven sites (`victory_road.py:1973, 1991, 1993, 2049, 2087, 2096, 2136` **[READ]**). Per-mon targets there would make the pre-flight refusal, both skip tests and the final readiness assert measure the wrong number. It is not a one-line change.

### 3.3 What to do — the pattern that already ships twice
`victory_road.py:2065-2104` and `counter_hunt.py:752-781`. Per mon, per call:

```python
TARGETS = {pid: 65 for (pid, _species) in battler_identities()}   # per-mon, may differ; 65 <= t <= 75

for (pid, species), (slot, level) in sorted(battler_identities().items(), key=lambda kv: kv[1][1]):
    t = TARGETS[(pid, species)]
    here = battler_identities().get((pid, species))      # (a) RE-RESOLVE BY PID — the index is stale
    if here is None or here[1] >= t:
        continue
    slot_now, level_now = here
    if slot_now != 0:
        yield from _rotate_lead_safely(slot_now)         # (b) rotate OURSELVES
        lead = get_party()[0]                            # (c) ASSERT BY PID — the rotator gives up
        if lead is None or lead.personality_value != pid: #     silently after 3 attempts
            raise BotModeError(...)
    finished = yield from _yield_bounded(                 # (d) LIVE frame cap — §4
        train_team(t, slots={0}, grass=TRAIN_SPOT_1F,
                   heal_center=PokemonCenter.EvergrandeCity),
        budget_for(pid),
    )
    assert_carriers_survived(f"training {species}#{pid:08X}")   # (e) after every heal window
    after = battler_identities().get((pid, species))     # (f) RE-VERIFY BY PID — "returned" != "trained"
    if after is not None and after[1] <= level_now and after[1] < t:
        raise BotModeError("... refusing to loop — a call that trains nothing spins the budget away")
```

**Stagger: derive, do not hardcode.** The ruling permits differing targets; it does not ask for a pattern. Set every floor to 65 and let the natural overshoot of the last battle, plus the swap-train finisher subsidy, produce the spread. A literal `75/73/71/69/67/65` ladder is a constant standing in for a quantity that varies with growth curve and level — the same mistake as the fixed `STEP=2`.

**Stepping.** Keep the outer stepping loop, but derive the step: at each round pick the **largest `T` with `estimate_frames_to_level(mon, T, 40) <= per_call_budget`**. **[COMPUTED]** against the raw model and a 250k budget that yields: Sceptile `[58,62,65]` (3 calls), Swellow/Mightyena `[54,59,63,65]` (4), Wailord `[52,56,59,62,64,65]` (6), Castform `[45,52,57,61,65]` (5), Zigzagoon `[38,47,53,58,62,65]` (6). Monotone, uses only shipped code, and automatically shrinks as cost rises with level.

---

## 4. THE BUDGET

### 4.1 The failure mode it must prevent
KI-28 — **19.9M frames**. `05-KNOWN-ISSUES.md:535-537`: *"these produce real encounters, real battles and real healing trips — they are busy, just not progressing. A 'nothing happened for N frames' detector is blind to them by construction. Only a resource budget catches them."*

Two amplifiers specific to this leg **[READ]**:
* `train_team` has **no frame budget** — only `guard > 500` **rounds** (`early_game.py:2101-2103`). `MAX_TRAINING_FRAMES` is enforced at exactly one site, `victory_road.py:2021`, inside `train_for_victory_road`. A leg calling `train_team` directly inherits **nothing**.
* `_story_spin`'s no-progress watchdog measures **total party exp** (`early_game.py:195-199`). Under swap-training the finisher banks every battle, so party total keeps moving and **the watchdog cannot fire even if the trainee gains literally zero**.

### 4.2 The ×3.30, honestly
Provenance is real (`03-PUNCH-LIST.md:782-786`: `(1/0.501) × (2368/1433)`), and it is applied in `probe_bracket_viability.py:66`. But it is **contested at this exact ground**: `grind_after_fix.log` measures the identical step (Wailord L60→62) at **82,415 f** against a raw estimate of 160,496 (**1.95× pessimistic**) and a ×3.30 estimate of 529,637 (**6.43× pessimistic**). De-boosting the traded mon leaves 1.31× / 4.33×. And `ai-research-notes/2026-09-18-ch24-training-economy-WORKFLOW.md:253` forbids quoting a net direction on VR ground because the exp term errs the *other* way.

**[COMPUTED] The decisive consequence of believing ×3.30:** step the schedule in corrected units against the 250k ceiling and **Wailord gets STUCK at L57** — a single +1 level costs 264,818 f, over the ceiling, and one level is the atomic unit. Zigzagoon needs 24 calls. **No step size of any granularity reaches L65.** A budget that refuses a run which would in fact succeed is the mirror-image failure of KI-28, and RULING 4 explicitly forbids refusing on cost.

### 4.3 The design answer: asymmetric, and split admission from termination
**A pre-flight estimate is not a budget.** `_maintain_lagging_battler` already states the principle and ships the mechanism (`story_mode.py:2726-2732`, `:2795-2801`; `_yield_bounded` at `early_game.py:1668-1687` **[READ]**).

* **ADMISSION (pre-flight, tight, RAW units).** Per mon, `estimate_frames_to_level(mon, T, 40)`. `None` ⇒ **EXPENSIVE, raise** — never cheap. Refuse only the genuinely impossible: `CH24_ADMIT_MAX = 250_000` per **call** (not per mon, not per leg), which is what produces the derived step schedule in §3.3 and keeps every call inside a shape this project has already run.
* **TERMINATION (live, generous, ×3.30 units).** `budget_for(call) = min(3.30 × raw_estimate_for_this_step, CH24_CALL_HARD_CAP)` driven through `_yield_bounded`, with `CH24_CALL_HARD_CAP = 1_000_000` (≈4.6 h @×1 — larger than any single measured step by ~12×, so it never truncates a healthy call). Generous on purpose: a live cap's job is to stop a livelock, not to grade a plan.
* **LEG TOTAL.** `CH24_LEG_MAX_FRAMES` — set from the pre-flight sum ×3.30 with ~1.5× slack, **reported not refused** (RULING 4: the total is the user's time, a decision for them, not a safety property — `victory_road.py:2016-2019` says the same). Exceeding it **halts and reports partial progress**; it never continues silently and never raises the cap.
* **ESTIMATE-ONLY.** `POKEBOT_CH24_ESTIMATE_ONLY=1` stops after the numbers with zero frames spent, mirroring `POKEBOT_CH23_ESTIMATE_ONLY` (`victory_road.py:2004-2011`). **Run this before any frames are ever spent on this leg.**

### 4.4 The numbers this produces
From `post_ch24ready`, reading (b), four battlers → L65: **admission 17 calls**, pre-flight raw **3,509,417 f**, ×3.30 termination envelope **11,581,076 f**, measured-model expectation **2,671,550 f = 12.4 h @×1 / 0.72 h dev**. **[COMPUTED]** The gap between the last two is the whole reason termination must be separate from admission.

⛔ **Do not "fix" `MAX_TRAINING_FRAMES`'s docstring to say it has no other caller.** It does — the concept ships as `MAX_PREP_TRAINING_FRAMES = 250_000` at `story_mode.py:1727`, gating three other `train_team` callers (`:2213`, `:2957`, `counter_hunt.py:720`) **[READ]**. Only the line number `story_mode.py:1034` has drifted.

---

## 5. THE GUARDS AND THEIR FAULT ARMS

One arm per guard; each must fail **for its own reason**, and each must be shown to fail before the guard is believed.

| # | GUARD | FAULT ARM | MUST FAIL BY |
|---|---|---|---|
| G1 | Pre-flight per-call admission; `None` ⇒ raise | `POKEBOT_CH24_FAULT_NOESTIMATE=1` — skip the estimate | a call admitted whose own raw estimate exceeds `CH24_ADMIT_MAX`; proves the refusal is live code |
| G2 | Live `_yield_bounded` cap + leg total | `POKEBOT_CH24_FAULT_NOBUDGET=1` — remove both caps | running past the leg total without halting (KI-28's shape). **Inverse arm:** set the budget absurdly low ⇒ must **PASS-with-stop**, halting and reporting partial progress |
| G3 | Rotate‑by‑PID, then **assert by PID** slot 0 holds it | `POKEBOT_CH24_FAULT_NOPIDASSERT=1` — drop the assert | training the wrong mon after a forced rotation failure, while level readouts still look plausible (KI-84) |
| G4 | Post-call PID re-verify: refuse to loop on a call that moved nothing | `POKEBOT_CH24_FAULT_NOREVERIFY=1` | looping on a no-op call; pair with an injected no-op `train_team` |
| G5 | `assert_carriers_survived` after every call | cannot be made to fail live (both deposit paths inert by default). ⇒ **two-directional in-process self-test on a synthetic party** every run: refuses a party missing Waterfall, accepts an intact one | *a guard whose only evidence is that it never fired has never been shown to work.* Precedent: `ch24caveheal`'s `GUARD SELF-TEST OK` |
| G6 | Swap-train installed in `on_battle_started` | `POKEBOT_CH24_FAULT_NOSWAPTRAIN=1` | reproducing `#24-grindppstall` — ~15 wins then flee-forever at zero exp. **Cheapest arm in the set**: it has a pre-captured failing fixture, `grind_stall_ppzero.ss1` |
| G7 | Whiteout latch `set_story_abort(True)` | `POKEBOT_CH24_FAULT_NOLATCH=1` — count but do not latch | the generator continuing against a party now at the Poké Center rather than in the grass |
| G8 | Lead restored on **every** exit path (`GeneratorExit` re-raised untouched; `BaseException` restores then re-raises) | `POKEBOT_CH24_FAULT_NORESTORE=1` | exiting an aborted grind with the **weakest** mon in slot 0 — measured cost of not doing this: 19 losses / 44 whiteouts at one tile |
| G9 | **Per-member** completion conjunct incl. the ≤75 bound | `POKEBOT_CH24_FAULT_BATTLERSONLY=1` — restore the `BENCH_SPECIES` exclusion | ⭐ **the arm that proves the ruling is ENFORCED, not asserted.** Without it the grade is indistinguishable from today's passing grade |
| G10 | Vacuity / premise | `POKEBOT_CH24_FAULT_NOTRAIN=1` — walk and read, train nothing. **Plus the mechanical test: point the driver at its own OUTPUT fixture** | ‼ subtle here — `post_e4ice_FINAL.ss1` already satisfies the ≥65 half for four mons, so **the vacuity conjunct must be the per-member one, not the aggregate** |
| G11 | Continuation: real `calculate_path` off the END tile aimed at **the VR apron (18,42)**, what leg 2 starts from | `POKEBOT_CH24_FAULT_NOCONTINUE=1` | grading PASS from a position with no route out. ⛔ Not the League door — Fly is refused on `map_type=Underground` and the door has no walking path |

⛔ **Fault-test every arm both ways** (CLAUDE.md §6): prove it fails when the guarded thing is broken, **and** prove it does not fire on mere mentions in comments. And retire `POKEBOT_CH24_FAULT_NOWALK` rather than copying it — its stated rationale (*"`train_team` does not travel"*) was retracted in place on 2026-09-18 (`story_harness.py:15583-15588`); it now measures something else.

---

## 6. HOW IT GETS DRIVEN

**Adapt `Ch24GrindMode` (`story_harness.py:15393`); do not write a driver from scratch.** It already does ~90% of this leg **[READ]**.

**Keep:** the walk EG(27,49) → apron(18,42) → `_walk_through_warp("Up")` → `TRAIN_SPOT_1F`, with its `_budgeted` wrappers and its refusal to guess a route from anywhere else (`:15610-15639`); `on_whiteout` → `set_story_abort(True)` (`:15442-15451`); `on_battle_started` → `SwapTrainBattleStrategy()` (`:15487-15491`); the stepping loop; per-step `_checkpoint` captures that never overwrite; the `_basket()` reading logged at PRE / every step / RESULT.

**⛔ Do not copy:** the retry wrapper at `:15655-15659` — `set_story_abort(False)` then `except Exception`, and `StoryAbort` subclasses `BotModeError`, so it **swallows whiteouts** (KI-67's shape; gate #27 `probe_abort_swallowing.py` scans `modules/story` and would catch it on promotion, but only there). Also leave behind `context.set_manual_mode()` and the ACCEPTANCE printing — harness furniture, not production.

**Four concrete deltas:**
* **(a) Roster.** Under (b), box first and the roster is correct. Under (a), the roster predicate must widen — and `team_is_ready`'s empty-set guard must stay in front of it.
* **(b) `MAX_STEPS`.** `MAX_STEPS, MAX_RETRIES = 24, 2` at `:15513`. At `STEP=1` (the setting the only proven L75 run used) 24 steps closes 24 levels; Zigzagoon needs 46. The loop would simply **end silently short of target**. Replace the step *count* with the frames-based budget of §4.3 — a step count is the wrong unit once steps have unequal size.
* **(c) Upper bound.** Nothing reads ≤75 anywhere in `15505-15700`.
* **(d) The grade.** ⛔ Today the grade is **`ok = bool(moved)`** (`:15690`) — *"needs at least one BATTLER to have gained a level"*. `at_or_above_L{target}` at `:15692` is a logged **reading**, not the grade. ⇒ it prints PASS when one of four battlers gains one level. Replace with a conjunction: **every member ≥ its floor AND ≤75 AND the continuation path exists AND the premise held.**

**Fixture.** `post_ch24ready.ss1` (md5 `cf383b5b2567…`, PINNED, verified byte-intact this session) is the ruled grind start and is the right start under reading (b) **and** under the mules-first ordering of reading (a). `post_ch24_atdoor_L75.ss1` is the right start only for a mules-only leg — and that is exactly the configuration §1.3 shows overshoots. `grind_stall_ppzero.ss1` is the **failing arm**, not a start point (it is saved `game_state=BATTLE`, `controllable=False` — a fact recorded in `probe_p7_reach_calls_in_cave.py:62-66` and the punch list, but **not in `FIXTURES.md5`**, which is why it got stepped on twice).

**Engine.** Must be the harness driver, never a bare `while: next(gen)` loop. The loop lacks all six of: per-frame `context.bot_listeners` ticking + controller-stack advance (so battles are actually fought), `on_battle_started` strategy injection, `on_whiteout`, the position-aware no-progress detector with its 900-frame stall save and 20,000-frame `HANG CONFIRMED` stop, the outer `--frames` cap, and the end-of-run `[moveset]`/party dumps. A probe that used one sat in an unfought battle for **5,575 of 6,000 frames** and would have printed a comfortable false confirmation had its vacuity gate not refused.

---

## 7. ⛔ WHAT I HAVE NOT ESTABLISHED

Blunt. Each is load-bearing; each has a cheap settling experiment.

1. **⭐ THE ONE PROBE THAT SETTLES THREE THINGS AT ONCE — RUN IT FIRST.** Does `SwapTrainBattleStrategy` fire at +4 (Castform) and +21 (Zigzagoon), and **does the finisher bank an equal share?** My §1.3 overshoot argument is **[COMPUTED]** from read code plus Gen-3 split rules — not observed. The corpus has never seen the strategy fire above +6 (0 of 510 at +7; 0 of 4,950 at ≥+8), and *a zero at a gap means NOT OBSERVED, not REFUSED.*
 ⇒ **A ~40,000-frame bounded drive from `post_ch24_atdoor_L75.ss1`, rotating Castform to slot 0, logging `total_exp` for EVERY party member per battle plus the turn-0 decision.** Then repeat with Zigzagoon. Instruments already exist: `tools/story-dev/probe_swaptrain_envelope.py`. **Nothing in §1 or §4 should be built on before this runs.**
2. **The mules' cost is unpriced.** 3.806 f/exp was measured in the opposite regime (a L60 lead one-shotting). The 20.4 h / 17.1 h figures are **model output**, not measurement. ⇒ the same probe as (1), extended to 200,000 frames, gives a real frames-per-exp for a mule and a real win/flee ratio.
3. **`PC_TILE=(10,1)` at Ever Grande is inferred, not probed.** `probe_pc_tile.py:60-67` scans six centres and Ever Grande is not among them. The decomp says it shares `LAYOUT_POKEMON_CENTER_1F`, and Mossdeep (also unprobed, same layout) is live-proven — strong, not proof. ⇒ **add `EVER_GRANDE_CITY_POKEMON_CENTER_1F` to that probe's map list; it reads map headers, no emulation loop.** Seconds.
4. **Nobody has walked from the Ever Grande Poké Center door to the PC stand tile.** `(27,49) → VR apron (18,42)` is proven at 22 wp; the in-centre leg to `(10,2)` is not, and `navigate_to` is what any deposit calls. ⇒ one short bounded drive from `post_ch24ready.ss1`.
5. **No PID-addressed two-mon deposit exists.** `deposit_one_dead_weight` is a **no-op success below six** and cannot choose its victim. Whether a §Ch24-local `deposit_named(pids)` on the same `interact_with_pc` primitive behaves is unbuilt and undriven. ⇒ build it with `POKEBOT_CH24_FAULT_NODEPOSIT=1` already in it, and drive it once on `post_ch24ready.ss1` asserting **by PID, never by count** (a count that nets to zero reads TRUE when nothing happened).
6. **Where a mid-grind whiteout respawns is measured only from INSIDE the League** — `EVER_GRANDE (18,6)`, the plateau with no walking path to the grind tile *or* the Poké Center. Every Poké Center's `ON_TRANSITION` calls `setrespawn` (`victory_road.py:694-697`), so the grind's first heal at `PokemonCenter.EvergrandeCity` **plausibly** re-arms it to (27,49) — which **is** 22 wp from the apron. If so the hazard is confined to a whiteout before the first heal; if not, **every** whiteout strands the leg. ⇒ an observe-only `respawn_reading()` at the grind tile, before and after one heal. This decides whether the leg needs a Fly-based recovery path at all.
7. **`_battler_slots()` has no HP filter**, so a **fainted** mon counts as a battler and can be selected and rotated into the lead. `_min_battler_hp_pct() == 0` *should* force a heal the same round — I did not trace it. ⇒ a targeted unit-level check before relying on any whole-scope path.
8. **A 4-mon §Ch24 party is unaudited beyond `pokemon_league.py`.** I found no party-count assertion there (only the by-PID stability check at `:1300-1308`), but I did not audit `story_mode.py`, the battle strategies, or the faint-replacement chooser for size assumptions. ⇒ `grep` for `len(get_party())` / `party[5]` across `modules/story` + `plugins`; then one gauntlet drive on a deliberately 4-mon fixture.
9. **frames/battle at `VICTORY_ROAD_1F` is still unadjudicated** — 2,138 / 2,228 / 2,384–2,648 / 3,192 all live in the tree. ⇒ adjudicate **before** any constant is hardcoded; until then every budget must be derived at runtime from `estimate_frames_to_level`, not from a literal.
10. **My refutation of the ×3.30 rests on ONE trajectory** (`grind_after_fix.log`, 37 battles, one mon, one curve, at L60–62, and that mon is **traded**). Per rule 8 that is a single measurement, not a replication. ⇒ **one short arm with a NON-traded battler as lead at `TRAIN_SPOT_1F`**, re-deriving f/exp. ⛔ Do not re-adopt ×3.30 "to be safe" — §4.2 shows it makes L65 unreachable at any step size, which would refuse a run that succeeds.
11. **Does `train_team`'s heal round trip execute from `TRAIN_SPOT_1F` when the leg STARTS at (18,6)?** Filed as `#24-cavehealblind`. The proven `ch24caveheal` run started on the apron side. ⇒ covered for free by the first long drive, provided the leg's own Fly-in runs first.
12. **Two of the four fixtures in §6 have no recorded game state.** `FIXTURES.md5` records `OVERWORLD`/`controllable` on only 22 of 57 rows, and **none** of the four §Ch24 grind rows. Two of this project's recent failures were both "loaded a non-overworld state into an overworld entry point". ⇒ add a mandatory **GAME-STATE** field to `FIXTURES.md5` and have `verify_fixtures.py` require it. Cheap, mechanical, and it closes a class rather than an instance.

**Not established and not settleable by me: §1.6.** Which reading the user wants is a question, not a finding. Put it to them with the hours, the L83–86 overshoot, the two competing decisions-log entries quoted verbatim and correctly attributed — and record the ruling **at the place the next auditor looks**, so it never has to be asked twice.
