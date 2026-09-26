# 2026-09-26 — PRODUCTION FLY FOR §Ch24: teach, return-to-League bridge, flyer acquisition (RECON + ADVERSARIAL VERIFY)

> ⚠ **AI RESEARCH NOTE — NOT A SOURCE OF TRUTH.** A 6-agent Claude workflow (`production-fly-recon`): three
> read-only recon angles, each followed by an adversarial verifier told to REFUTE it. Nothing was driven.
> The verbatim reports follow; ‼ **READ EACH VERIFIER BEFORE ITS REPORT — they correct them.**

## THE NET (my synthesis of the six; each point tagged with who established it)

1. ✅ **Production never teaches Fly** (all six agree; code-cited). HM02 is in every organic bag after the Route 119 rival.
2. ✅ **The return bridge is the right shape:** after §Ch24 training, `fly_to_destination(PokemonLeague)` then ASSERT
   `_on_map(EG)` ∧ tile == (18,6). The landmark flag is set by League 1F `OnTransition`, which §Ch23 legs 10/11 always
   enter first (unless the party is healthy AND the basket already full). Fly lands at (18,6) — MEASURED twice.
   ⚠ `fly_to_destination` checks only that the bot MOVED (its docstring claiming it asserts the map is false).
   ✅ South↔north walking is NO PATH in BOTH directions — both MEASURED (KI-94 2026-09-06, vr-heal-roundtrip 2026-09-18).
3. ⛔ **There is NO readiness refusal before the one-way gauntlet** (confirmed three times). Proposed: R1 OUTSIDE on
   EG (18,6) after training AND the bridge (order: train → bridge → R1), R2 heal at the lobby nurse, R3 a backstop in
   `run_the_gauntlet` requiring `E1-READY`.
4. ⛔⛔ **NEW HAZARD (bridge verifier):** an organic party with NO Fly does not "stay on the plateau" — every battler
   L39-64 qualifies for VICTORY_ROAD_1F (1 region hop) and `train_team` WALKS in via (18,27), which leads to the EXIT
   half of VR1F; the grind tile (15,39) is by the ENTRANCE warp. A return ticket must refuse WALKING off the north
   plateau without a way back, not only flying.
5. ⚠ **Teach placement:** Segment 24, just before `train_for_league`, latch first — teaching earlier switches on the
   Fly shortcut for every mid-game training pick. The move picker must EXCLUDE HM SLOTS itself (`teach_hm_move` only
   protects them when `replace_slot is None` — an explicit HM slot loops forever). Fly is a banned battle move but
   has base power 70, so "keeps a damaging move" must exclude banned moves.
6. ⭐ **The League lobby has a PC** (metatile at (6,1), `MB_PC`) ⇒ a boxed flyer can be withdrawn from (18,6);
   `_withdraw_hm_learner` cannot be reused as-is (lobby nurse/PC tiles differ).
7. **Acquisition (13 of 30 parties have no flyer):** Taillow/Swellow, Wingull/Pelipper, Swablu, Tropius, Skarmory are
   catchable before the E4; the land-only HM hunt finds R103/R116/R115/R118/R119/R121 and its `reversed()` order would
   pick the SPARSEST ground (R119 Tropius); R115 is by far the densest. A Fly hunt MUST pass `heal_centers` or a
   6-mon party hard-derails (PC-first and make-room are both gated on it).
8. ⚠ The §Ch24 latch lives only in memory: a restart off the plateau re-enters §Ch23 before any bridge can run.

---

######## RESULT 0
# Fly carriers for the 13 parties that have no Fly user

## 1. Fly learners you can catch in Hoenn before the Elite Four
Two sources agree exactly. The decomp lists 38 `.FLY = TRUE` species [DECOMP src/data/pokemon/tmhm_learnsets.h], and so does `species.json` (tm_hm move 19) [CODE modules/data/species.json]. The decomp's wild tables also match our cached index [DECOMP src/data/wild_encounters.json] [CODE cache/encounter_index_BPEE0.json].

| Species | Where (method, share of that table, level; map rate) |
|---|---|
| Taillow | R104 grass 10% L4-5, Petalburg Woods 5% L5-6, **R116 20% L6-8**, **R115 40% L23-25** (all rate 20) |
| Swellow | R115 10% L25 |
| Wingull | **R103 20% L2-4**, R104 10%, R110 8% L12, **R115 10%**, **R118 19% L25-27**, **R121 9% L26-28**, R123 9%, Mt Pyre Exterior 10% (rate 10). **Surf: 35% L10-30 on about 30 waters, including Ever Grande City, Lilycove and R128 (rate 4). R104 water is 95%.** |
| Pelipper | Surf 5% L25-30, same waters |
| Swablu | R114 40% L15-17, **R115 30%** |
| Tropius | **R119 9% L25-27** (rate 15) |
| Skarmory | R113 5% L16 |

None of them come from fishing or Rock Smash.

Not usable:
- **Doduo, Dodrio, Xatu:** Safari Zone only. Nothing in `modules/story` handles Safari battles [CODE training_areas.py ceiling comment].
- **Hoothoot:** Safari NE/SE only. I did not verify when those areas open.
- **Altaria:** Sky Pillar 5F only, which has cracked floors and is excluded [CODE training_areas.PENDING_GRASS comment].
- **Vibrava:** you only get it by evolving Trapinch.

## 2. What the existing hunt would do if it were called with HM02
`_hm_hunting_grounds` only searches land encounters on `TRAINING_GRASS` rows that have a tile, and it skips Victory Road [CODE early_game.py:_hm_hunting_grounds]. For HM02 that leaves six grounds [INFERENCE, computed offline, not run against the ROM]:

| Ground | Target | Rough steps per target |
|---|---|---|
| R103 | Wingull | about 45 |
| R116 | Taillow | about 45 |
| R115 | Swablu, Swellow, Taillow, Wingull | about 10 |
| R118 | Wingull | about 47 |
| R119 | Tropius | about 133 |
| R121 | Wingull | about 100 |

- **How the steps figure is computed:** 1 ÷ (rate × 16 ÷ 2880 × target share) [DECOMP src/wild_encounter.c:WildEncounterCheck].
- **Intimidate or Keen Eye in the lead halves these encounters.** They skip half of wilds at 5+ levels below the lead [DECOMP wild_encounter.c]. That matters for parties led by Mightyena.
- **The order ignores density.** `ensure_hm_learner` tries grounds furthest-progressed first, taking the first one `calculate_path` can reach. So **R121 (9%) wins over R118 (19%)** [CODE early_game.py:ensure_hm_learner].
- **Grounds outside the search:** R104 and Petalburg Woods have no tile (PENDING), R114 was demoted, and R110, R113, R123, Mt Pyre and every surf table aren't in the list [CODE training_areas.TRAINING_GRASS/PENDING_GRASS].
- **Conditions for a catch:** party under 6 (`ensure_hm_learner_making_room` deposits one mon otherwise), at least 2 balls, and a 40,000-frame spin limit [CODE story_mode.py HM branch; early_game.ensure_hm_learner].

**Nothing in production calls it for HM02.** The only production calls are for HM06, HM03 and HM08 [CODE plugins/custom_modes/story_mode.py]. `TRAVEL_PLAN` hard-codes Swellow [CODE pokemon_league.py:TRAVEL_PLAN]. The generic catch-and-teach pieces already exist, so the Fly teach would copy those three call sites.

## 3. Story order
- **First catch:** R103 Wingull, right after the rival gives 5 Poké Balls in Birch's lab [DECOMP LittlerootTown_ProfessorBirchsLab/scripts.inc].
- **First teach:** HM02 comes in §Ch13c from the Route 119 rival [CODE early_game.fight_route119_rival_and_get_fly].
- **First use:** using Fly outside battle needs BADGE06 [DECOMP src/party_menu.c enum FIELD_MOVE_FLY → FLAG_BADGE06_GET].
- **Best window: §Ch13c to the Fortree Gym.** The bot is standing on R119 (Tropius), with R118 (Wingull 19%) one map south. R121 opens after §Ch13d, once the Devon Scope clears the Route 120 bridge Kecleon [CODE early_game.get_devon_scope] [DECOMP Route120/scripts.inc].
- **Missed chance on the way:** the trip to Ever Grande crosses Lilycove and R124-128 water, where 35% of surf encounters are Wingull. The current code can't hunt on water.

## 4. What each anchor can reach

| Anchor | Grounds |
|---|---|
| **Fortree** | R119 is next door (Tropius). R121 is 2 hops via R120. R118 is 2 hops via R119. [DECOMP data/maps/*/map.json connections] |
| **Lilycove** | R121 is next door (Wingull 9%). Its own water has Wingull and Pelipper, but only by surfing, which the hunt can't do. |
| **Ever Grande** | **North (League) side:** nothing wild can be walked to [CODE pokemon_league.py measured comment above TRAVEL_PLAN]. **South (Poké Center) side:** only water. The city's own water has Wingull 35% and Pelipper 5% at zero hops, but the hunt can't use it. The nearest land ground is R121, **6 hops** [DOC 03-PUNCH-LIST.md, the 4-hop budget entry]. |

So the bot has to catch the carrier **before Victory Road**, or the hunt needs a surf mode.

## 5. The 2026-09-25 directive and #24-hm-slaves
- **Punch list status is `[~]` MIXED.** The PC-first withdraw has shipped. The catch half is open ("widen the curated TABLE, never the INDEX"), and so is choosing a centre [DOC 03-PUNCH-LIST.md #24-hm-slaves].
- **The shiny question is closed:** it was refuted, so nothing needs building [DOC 03-PUNCH-LIST.md; 07-CHANGELOG.md].
- **Duplicate catches are only avoided when a centre is given.** The HM catch branch never checks whether a species is already owned [CODE story_mode.py HM-learner branch]. That is harmless only because the PC is checked first, and that check runs only when `heal_centers` is not empty [CODE early_game.ensure_hm_learner_making_room]. A Fly call with no centres could catch a second Wingull while one sits in a box.
- **A carrier takes a party slot while flying**, so one battle mon has to be boxed [INFERENCE]. That fits RULING 13.

**Could not determine:**
- Box contents of the 13 parties.
- Whether `calculate_path` can path from the south side of Ever Grande to R121.
- Whether turning in place triggers encounters at the per-step rate.
- Whether 40,000 frames is enough on R121.

**Side finding:** the comment above `pokemon_league.TRAVEL_PLAN` says the Fly badge is "BADGE03". That's stale; the code itself checks BADGE06.

## LOAD-BEARING CLAIMS
1. The only Fly carriers realistically catchable before the E4 are Taillow, Swellow, Wingull, Pelipper, Swablu, Tropius and Skarmory [DECOMP wild_encounters.json + tmhm_learnsets.h].
2. The existing hunt would find exactly six grounds (R103, R116, R115, R118, R119, R121), because it is land-only [CODE early_game._hm_hunting_grounds; INFERENCE offline].
3. It tries R121 first, even though R118 has twice the Wingull rate [CODE ensure_hm_learner `reversed(grounds)`].
4. No production code catches or teaches Fly [CODE story_mode.py call sites; pokemon_league.TRAVEL_PLAN].
5. Using Fly needs BADGE06 [DECOMP party_menu.c].
6. From the Ever Grande League side nothing can be reached. From the south side, the only nearby carriers are on water, and the current hunt can't search water [CODE pokemon_league.py measured comment; CODE _hm_hunting_grounds; DECOMP EverGrandeCity water table].
7. A Fly hunt must pass `heal_centers`, or the PC is never checked and "no duplicates" isn't enforced [CODE ensure_hm_learner_making_room; story_mode.py HM branch].

Scratch files: `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/01ddd963-7a1a-4b49-8ecd-33397f5304e2/scratchpad/flyrecon/` (`fly.py`, `wild_encounters.json`, `tmhm.h`, `party_menu.c`, `wild_encounter.c`).

######## RESULT 1
# Production "teach Fly" step: `ensure_fly_knower()` design

## 1. Placement
**Where:** in `story_mode._play`, Segment 24, inside the `else:` branch of `if ch24_chapter_done()`. It runs after `_guard("Victory Road (Ch23)", _ch23_settled)` and immediately before `train_for_league(_ch24_train_report)`. Call `self.mark_ch24_owns_run()` first, before the teach.

**Why not earlier (13c / 22c):**
- **The Fly shortcut is global.** `_training_area_allowed` treats a far ground as reachable if the bot can Fly there. That check is also used by boss-prep relocation (`_allow`) and by maintenance (`_maint_allow`). `train_team` then flies to the anchor via `_goto_training_area → _fly_to_training_anchor`. Today this path is idle only because no organic party member knows Fly. Teaching Fly earlier would switch on flying for every mid-game training pick without a test [CODE story_mode._training_area_allowed, early_game.train_team].
- **Fly is useless in battle.** It is in `banned_moves`, so the slot it takes stops contributing to battles from the moment it is taught [CODE profiles/battle.yml]. Pay that cost as late as possible.
- **§Ch23 would get worse.** Bringing in a low-level Fly mule before Victory Road adds a "worst battler" to §Ch23's training refusal. 18 of the 30 refusals were exactly that kind of mule [DOC ch23training-DESIGN].
- **The HM07 funnel no longer applies.** Waterfall is already taught at 22b, and no HM is acquired after §Ch24 starts [CODE story_mode 22b].

**Why the latch comes first:** the fallback in §5 can walk into the Ever Grande Poké Center. `ch23_chapter_done()` requires standing on the Ever Grande map. Without the latch, a derail inside that building would re-run §Ch23, including the ocean crossing [CODE train_for_league docstring].

## 2. Choosing the learner
- **Candidates:** non-egg party members where `can_learn_tm_hm(HM02)` is true, that have at least one empty or non-HM slot, and that keep at least one usable damaging move after the teach. This is `ensure_waterfall_learner`'s "compatible and has a slot to spend" rule. `hm_learner_slot` is not enough because it returns saturated mons [CODE victory_road.ensure_waterfall_learner].
- **Ranking:** least battle value lost (from §3), then highest level.
- **Fly-capable species in the data:** Swellow/Taillow, Pelipper (also Surf), Wingull, Altaria/Swablu, Tropius, Skarmory, Xatu, Crobat, Flygon/Vibrava, Salamence [CODE modules/data/species.json].
- **Do not reuse `TRAVEL_PLAN`:**
  - It hardcodes Swellow and Wing Attack; `apply_moveset_plan` refuses if the species is missing or doesn't know Wing Attack.
  - Its order guard refuses whenever Swellow still knows Peck, and production never runs `MOVESET_PLAN`. So on a `post_league_shop`-shaped party it raises `BotModeError`, and a derail follows [CODE pokemon_league.apply_moveset_plan; INFERENCE].

## 3. Which move to overwrite
A new pure function, `pick_fly_replace_slot(mon, party)`, checks in this order:
1. An empty slot.
2. A banned or zero-power move (for example Endeavor or Double Team).
3. A move beaten by another move on the same mon: same type, at least equal power and priority, where `ALWAYS_HIT` beats `HIT`. This picks Peck on `post_league_shop` and Wing Attack on `post_moveset` [CODE moves.json: Aerial Ace `effect=ALWAYS_HIT`].
4. The weakest move whose type the mon already covers.

**Never overwrite** a move that is the party's only move of a type that is super-effective against an Elite Four or Champion Pokémon. Count every member's damaging moves, HMs included; the Hydro Pump/Ice Beam loss came from leaving HMs out of that count [CODE story_mode.which_move_should_be_replaced]. Read the rosters from `trainer_parties.h` [DECOMP]. If only protected slots remain, reject that learner.

`teach_hm_move`'s default (`replace_slot=None`) takes the lowest base power. On `post_moveset` that is Quick Attack, which would lose the priority move [CODE early_game.teach_hm_move]. That is why a dedicated picker is needed.

## 4. Fit with the other HM carriers and `team_policy`
- HM slots are never overwritten: `teach_hm_move` excludes them, and Gen 3 cannot forget HMs.
- Teach Fly to exactly one mon. As the only Fly carrier, `dead_weight` exempts it from being boxed (`_only_hm_carrier`; `HM_MOVES` includes Fly). That keeps it in the party through the training ladder's heal-and-deposit trips [CODE team_policy]. If two mons knew Fly, neither would be protected.
- After each heal, check that the Fly carrier is still in the party. On loss, degrade (re-teach if possible) rather than raise, following the `assert_carriers_survived` shape.
- Field moves ignore HP, so a fainted carrier can still Fly [DOC victory_road.field_move_carriers].

## 5. Failure handling
- **T0:** a party member already knows Fly (`first_pokemon_with_move("Fly")`). Skip, with no menu opened.
- **T1:** teach with `teach_hm_move(HM02, idx, replace_slot)`, then verify by PID:
  - the learner knows Fly;
  - it lost exactly the intended move;
  - the other five movesets are unchanged;
  - the game is back in the overworld.

  On `BotModeError`, call `reraise_if_aborting` first, retry once, then degrade to T3.
- **T2:** nobody in the party can learn Fly. Try the box first: take the top result of `boxed_hm_learner_pids(HM02)[:1]` and call `_withdraw_hm_learner` with the Ever Grande Poké Center. Only do this if `calculate_path` to that centre's apron succeeds. From (18,6) it does not [DOC FIXTURES post_fly].
  - **No catching trip:** from the League plateau, every grass area needs Fly to reach, and `_hm_hunting_grounds` excludes Victory Road [CODE].
- **T3:** log `fly_unavailable=<reason>` with `_log_story_event` and return without raising. `train_for_league` then runs without Fly: only Victory Road 1F, which admits trainees at L39 and above; lower trainees are recorded as `no_ground`. This still needs the separate readiness refusal before the Elite Four (RECON §4.3). This path covers the 13 of 30 organic parties with no Fly-capable member.

## 6. Proof: fault arms and the drive
**Fixtures:**

| Fixture | Position | Swellow moves / Fly | HM02 in bag | Role |
|---|---|---|---|---|
| `post_league_shop.ss1` | (18,6) | Peck, Wing Attack, Aerial Ace, Quick Attack [INFERENCE]; no Fly | yes [DOC] | **Primary**: same state production reaches at §Ch24 entry |
| `post_moveset.ss1` | (18,6) | Facade, Wing Attack, Aerial Ace, Quick Attack; no Fly | yes (the `ch24fly` drive passed from it) | Slot-choice arm |
| `post_ever_grande.ss1` | (18,42), south side | Swellow L42; no Fly [INFERENCE] | yes [INFERENCE] | Box-withdraw arm: only fixture with a walkable Poké Center (22 waypoints) |
| `post_fly`, `post_ch24ready`, `post_ch24_atdoor`, `post_ch24_atdoor_L75` | various | Swellow already knows Fly (last two measured) | — | Skip control |
| `post_grind_L60.ss1` | Victory Road 1F | no Fly | yes | Do not use: ruled a dead branch |

**Fault arms:**
- **A — skip the teach** (`POKEBOT_FLYTEACH_FAULT=skipfix`, read in production and registered in `29-DISABLED-FEATURES-REGISTRY.md`), on `post_league_shop`. Before driving, compute the difference between arms: `best_training_area(19, max_wild_max=20, allow=_training_area_allowed)` should return `None` without Fly and a ground with Fly. The treatment arm must log a real `fly_to_destination` landing; the fault arm must log `no_ground` for Zigzagoon.
- **B — wrong slot:** a pure gate using made-up parties (both real Swellow movesets, an Endeavor case, a unique Ice-move learner, a 4-HM Pelipper). Reverting the protection must turn exactly the protected case red.
- **C — no capable member:** stub HM02 compatibility to false. Expect no raise, `fly_unavailable` recorded, and the same tile, in the overworld.
- **D — already a Fly knower:** on `post_fly`, the bag is never opened.
- **E — latch:** `_ch24_owns_run` is true before the first button press.

**Drive:** `--driver ch24flyteach post_league_shop.ss1`. After teaching, fly to the first rung's anchor town and grade on arriving at a **different** map, so the continuation check can fail.

## Could not determine
- Fixture bags and movesets were not read directly (no emulator was run).
- Whether the League 1F lobby has a PC. The decomp lists a nurse, a clerk and two guards; a PC would be a tile, not a listed object.
- Whether Victory Road 1F (15,39) can be reached on foot from (18,6).

## LOAD-BEARING CLAIMS
1. The Fly shortcut in `_training_area_allowed` also drives boss-prep and maintenance training picks [CODE story_mode `_allow`/`_maint_allow`].
2. Fly is a banned battle move [CODE profiles/battle.yml].
3. `apply_moveset_plan(TRAVEL_PLAN)` refuses when Swellow still has Peck or lacks Wing Attack [CODE pokemon_league.apply_moveset_plan].
4. The only production caller of `apply_moveset_plan` is `fetch_ice_beam`, which itself has no production caller [CODE pokemon_league; DOC RECON].
5. From (18,6), no path reaches the Ever Grande Poké Center [DOC FIXTURES post_fly].
6. The only Fly carrier is exempt from being boxed [CODE team_policy.dead_weight].
7. `teach_hm_move`'s default would overwrite Quick Attack on `post_moveset` [CODE early_game.teach_hm_move; INFERENCE].
8. 27 of 30 badge-8 parties carry a low bench mon that needs Fly; 17 of 30 have a Fly-capable member [DOC ch23training-DESIGN].
9. Fly lands at the League only if `FLAG_LANDMARK_POKEMON_LEAGUE` is set [DOC RECON; DECOMP region_map.c].

######## RESULT 2
# §Ch24 bridge from training back to the League door (design)

## 1. When FLAG_LANDMARK_POKEMON_LEAGUE gets set
- It is set in only one place: League 1F `OnTransition` runs `setflag FLAG_LANDMARK_POKEMON_LEAGUE` and `setrespawn HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE` [DECOMP data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc].
- In an organic run, two §Ch23 legs walk into League 1F [CODE victory_road.py:do_victory_road_chapter, stock_for_the_elite_four]:
  - leg 10 `heal_at_league` goes in when `_on_map(EG) and not party_is_healthy()[0]`;
  - leg 11 goes in when the bag is short of `LEAGUE_BASKET`.
- `ch23_chapter_done` requires the basket [CODE victory_road.py:ch23_chapter_done]. §Ch24 training starts only after `_guard("Victory Road (Ch23)", _ch23_settled)` [CODE story_mode.py:_play].
- **So the flag is set before training starts** in every organic run. The one exception would be a bag that already held the full basket before leg 11 [INFERENCE: implausible]. Both legs leave the bot at EG (18,6).
- Every Poké Center 1F runs `setrespawn` [DECOMP EverGrandeCity_PokemonCenter_1F/scripts.inc]. After the first training heal, a whiteout therefore respawns at that rung's Poké Center, not the League.

## 2. Where training can end
| End | Position | Walk to (18,6)? |
|---|---|---|
| floor already met (self-skip) | where §Ch23 left it, (18,6) | yes |
| last rung on VR1F | step-out to EG (27,49) [CODE `_ch24_step_out_if_fly_illegal`] [LOG 2026-09-24c-ch24climb-DETERMINISM-REPEAT.stdout.txt] | no: (18,6)→(27,49) returned NO PATH [LOG 2026-09-18-vr-heal-roundtrip.stdout.txt]; the reverse direction was never measured |
| last rung on a route | the grind tile (train_team does not heal at the end [CODE early_game.py:train_team]), e.g. ROUTE117 (31,16) [LOG 2026-09-23-ch24train.stdout.txt] | no |
| rung or outer purse expires | wherever `gen.close()` lands: grind tile, mid-walk, or inside a Poké Center (Indoor, which the step-out does not handle) [CODE `_yield_bounded_by_frames`] | no |
| no_ground / no_anchor / no_progress | position unchanged | often yes |
| whiteout | the last `setrespawn` Poké Center | no |

Today `prepare_and_open_the_league` does this:
- It raises unless the bot is on EG.
- From (27,49) it calls `_navigate_riding_out(EG, LEAGUE_DOOR_APRON)` under a 200k-frame bound and ignores the return value. Then it holds Up. Directly north of (27,49) is the Poké Center door (27,48) [DECOMP EverGrandeCity/map.json].
- Its training call only runs `if VR._on_map(VR.EG)`.

**Could not determine:** whether `navigate_to_anywhere` can find a way to (18,6) through Victory Road.

## 3. The minimal production step
Add a new `return_to_league_door(report)` in pokemon_league.py. Call it inside `prepare_and_open_the_league` just before "GET INSIDE". That one call site covers both `train_for_league` calls, the self-skip path and the whiteout-resume path.
1. If on LEAGUE_1F, return. If on EG and `calculate_path((EG,here),(EG,(18,6)))` succeeds, walk there, reusing the (18,27) trap check from `heal_at_league`.
2. If the current map forbids Fly:
   - on VR1F, use the existing step-out;
   - inside a Poké Center (Indoor), navigate to `fly_landing_tile(heal_center)`. This part is new; `train_one_for_league` would need to record the rung's heal_center.
3. Call `fly_to_destination(FlyDestinationRSE.PokemonLeague)`. Its guards already check for a Fly knower, BADGE06, `LANDMARK_POKEMON_LEAGUE` (via get_flag_name) and the map type.
4. **Assert `_on_map(EG)` and tile == (18,6).** `fly_to_destination` only checks that the bot moved, not where it landed. The cursor (28,10) is the top cell of the Ever Grande map section (posWithinMapSec 0), so with the flag set the game sends the bot to the League heal location [DECOMP src/region_map.c:CB_ExitFlyMap, GetPositionOfCursorWithinMapSec; region_map_sections.json]. Measured: flights from (27,49) and from (18,42) both landed at (18,6) [LOG 2026-09-14-ch24flyto-POKEMONLEAGUE-UNBLOCKS-KI94.stdout.txt, 2026-09-17-ch24toleague-TREATMENT.txt].

Also add a **"return ticket" check** to `train_one_for_league`: never fly off the plateau unless a flight back to PokemonLeague is possible right now (a Fly knower in the party, BADGE06, the landmark flag). Re-check it after any boxing, because RULING 13 allows the Fly knower to be boxed.

## 4. If Fly is unavailable
- **No production code teaches Fly** [DOC 2026-09-26-organic-frontier-RECON.md §4.1]. So `can_fly_to_anchor` is always False today, and only walkable grounds are admitted. Trainees below L39 get no_ground. The bot should mostly stay on the plateau, so the bridge is a no-op, and the readiness gate below then refuses [INFERENCE].
- **Off the plateau with no Fly: refuse, and name the guard that failed.** Walking back means the whole of Victory Road again, which is §Ch23 legs 5–9. Those legs raise when their work is already done [CODE do_victory_road_chapter docstring]. Prevent this case with the return ticket rather than building a walk-back fallback.
- **Flag unset:** `fly_to` already refuses. The alternative, flying to EverGrandeCity, lands on the Poké Center side of the split city.
- **Hazard, undetermined:** a party with no Fly could walk into VR1F through (18,27). VR1F is not in `_CAVE_ENTRANCES`, and the step-out always heads for (27,49).
- The game allows Fly while surfing and from a fainted knower: `SetUpFieldMove_Fly` checks only the map type, and no HP check was found in the field-move menu code [DECOMP src/party_menu.c]. Our menu navigation while surfing has never been driven.

## 5. Readiness refusal
**The recon is right: there is none.**
- `prepare_and_open_the_league` records `below_floor_after`, and `E1-READY` is only a reading.
- `run_the_gauntlet` only takes `G-PREPARED`.
- `enter_the_league` says "NO READINESS CHECK HERE, ON PURPOSE" [CODE pokemon_league.py].
- The story_mode.py comment saying the readiness guard "IS step 1" is false.

Proposed gates:
- **R1, outside:** in `prepare`, after the bridge and a retry of training, before GET INSIDE. The bot is on EG (18,6), a City map, so Fly is legal and the problem can still be fixed. Raise if any party member is below the floor or the basket is short.
- **R2, in the lobby before the guard talk:** heal at the nurse, standing at (3,4) and talking across the counter as `heal_at_league` does (RULING 5). Then assert `party_is_healthy`.
- **R3, backstop in `run_the_gauntlet` before `enter_the_league`:** refuse unless `E1-READY` is present. The lobby has a nurse and an exit, so a refusal there stops the bot without stranding it.
- R1 will fire on organic parties until Fly teaching or RULING 13 roster selection exists. That is correct: a named stop outside the League is better than a one-way, under-levelled gauntlet.

## 6. The drive that would prove it
Build a new `ch24return` driver that imports the production function. Pre-register predictions before running.

| Arm | Fixture | Expected result |
|---|---|---|
| T1 | post_ch24ready.ss1, EG (27,49), Swellow knows Fly, flag already proven set | arrives at (18,6) |
| T2 | post_e4ice_FINAL.ss1, VR1F (15,39) | step-out, then Fly, arrives at (18,6) |
| Vacuity | post_ch24_atdoor_L75.ss1, already at (18,6) | no flight; `R-FLOWN` absent |
| F1 | post_grind_L60.ss1, no Fly knower [DOC tools/story-dev/saves/FIXTURES.md5] | a refusal that names the missing knower |
| F2 | T1 with `LANDMARK_POKEMON_LEAGUE` cleared in RAM | refusal |

- The discriminator is the flag and knower value, read at the start of each arm.
- **Integration A/B:** run `--driver ch24entry` from post_ch24ready.ss1 at a floor the party already meets.
  - Before the fix: it fails at GET INSIDE, before (9,1).
  - After the fix: it reaches `E1-AT-DOOR`.
- **Readiness arm:** set the floor above L19 and fault training off. R1 must raise while the bot is on EG, with `ENTERED_ELITE_FOUR` still False.

## LOAD-BEARING CLAIMS
1. The landmark flag is set only by League 1F OnTransition, and §Ch23 legs 10/11 walk into League 1F before §Ch24 starts [DECOMP scripts.inc; CODE do_victory_road_chapter, stock_for_the_elite_four, ch23_chapter_done].
2. After a VR1F rung, training ends at (27,49), and (18,6)→(27,49) has NO PATH [CODE `_ch24_step_out_if_fly_illegal`; LOG 2026-09-24c, 2026-09-18-vr-heal-roundtrip].
3. With the flag set, Fly to PokemonLeague lands at (18,6); this was measured from (27,49) and (18,42) [DECOMP CB_ExitFlyMap; LOG ch24flyto, ch24toleague-TREATMENT].
4. `fly_to_destination` checks that the bot moved, not where it arrived, so the bridge must assert the tile [CODE pokemon_league.py:fly_to_destination].
5. Nothing refuses an under-levelled party before (9,1) [CODE prepare_and_open_the_league, run_the_gauntlet, enter_the_league].
6. Organic parties never know Fly [DOC RECON §4.1], so R1 plus the return ticket decide what happens in organic runs.
7. Not determined: whether `navigate_to_anywhere` can path (27,49)→(18,6), whether VR1F's two halves connect, and whether Fly works while surfing in our menu code.

Scratch copies of the decomp files are in C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/01ddd963-7a1a-4b49-8ecd-33397f5304e2/scratchpad/flyrecon/.

######## RESULT 3
**Verdict:** the report holds up. Claims 1, 2, 4 and 5 are confirmed. Claims 3, 6 and 7 are partly right: two understate the problem and one overstates it.

## Claim by claim

**1. Fly carriers you can catch before the E4: CONFIRMED, with one omission.**
- I fetched `tmhm_learnsets.h` and `wild_encounters.json` myself. They are byte-identical to the scratch copies.
- There are 38 species with `.FLY = TRUE`, and `species.json` (tm_hm move 19) gives the same 38 [DECOMP] [CODE modules/data/species.json].
- Every rate I checked matches: R115 Taillow 40, Swablu 30, Swellow 10, Wingull 10; R118 Wingull 19; R121 Wingull 9; R119 Tropius 9 at map rate 15; R113 Skarmory 5.
- No carrier appears in any fishing or Rock Smash table.
- The omission: Rayquaza can learn Fly and is a static L70 battle once `VAR_SKY_PILLAR_STATE >= 2`, which is before the E4 [DECOMP data/maps/SkyPillar_Top/scripts.inc]. Leaving it out is reasonable, because `StoryCatchStrategy` only throws balls [CODE story_mode.py:StoryCatchStrategy]. But the report never lists it.

**2. Exactly six grounds: CONFIRMED.**
- The rows with a tile, minus Victory Road, are R101, R102, R103, R116, R117, R111, R115, R118, R119 and R121.
- R101, R102, R117 and R111 have no Fly learners, which leaves the six named [CODE training_areas.TRAINING_GRASS; early_game._hm_hunting_grounds].
- The steps-per-target numbers recompute correctly.

**3. R121 is tried before R118: CONFIRMED but UNDERSTATED.**
- `reversed(grounds)` gives the order R121, R119, R118, R115, … [CODE early_game.ensure_hm_learner]. So Tropius on R119 (about 133 steps per target, the sparsest of the six) also comes before R118.
- R115 is by far the densest ground (90% of its table, about 10 steps) and comes fourth.
- In the report's own recommended window (§Ch13c up to the Devon Scope), R121 should fail `calculate_path`. Object templates that have a hide flag block their tile until that flag is set [CODE map_path.py:dynamic_collision_flag]. So the hunt would pick **R119 Tropius**, the worst ground [INFERENCE: I did not confirm the flag on the Route 120 bridge Kecleon's template].

**4. No production code catches or teaches Fly: CONFIRMED.**
- `ensure_hm_learner_making_room` is called only for HM06, HM03 and HM08 [CODE story_mode.py].
- The other teach sites are for HM04 and HM07 [CODE early_game.py; victory_road.py].
- `fetch_ice_beam` and `apply_moveset_plan` have no production caller. The Fly disjunct and `_fly_to_training_anchor` use Fly but never teach it.

**5. Using Fly needs BADGE06: CONFIRMED.**
- The decomp enum has `FIELD_MOVE_FLY, // FLAG_BADGE06_GET`, and the menu checks `FlagGet(FLAG_BADGE01_GET + fieldMove)` [DECOMP src/party_menu.c:CursorCb_FieldMove].
- `can_fly_to_anchor` checks BADGE06 [CODE training_areas.can_fly_to_anchor].
- The comment in `TRAVEL_PLAN` still says "BADGE03". The report's side finding is right.

**6. Ever Grande: PARTLY right.**
- Ever Grande City and R128 have only water and fishing tables [DECOMP]. So the south-side part of the claim holds.
- "Nothing wild can be walked to" from the League side is overstated. The same measured comment shows the Victory Road exit landing (18,28) is reachable [CODE pokemon_league.py:TRAVEL_PLAN comment], and Victory Road 1F is recorded as 1 hop away [CODE training_areas.py VICTORY_ROAD_1F comment].
- The conclusion still stands for Fly, because Victory Road has no Fly learners (Golbat is not in the 38; Crobat is).

**7. `heal_centers` is required: CONFIRMED but UNDERSTATED.**
- The PC-first block really is gated on `if heal_centers and …` [CODE early_game.ensure_hm_learner_making_room].
- The full-party deposit is gated by the same parameter. With `()` the `for centre in heal_centers` loop never runs, so it raises the original "party is full" error. That means a Fly hunt with no centres derails any 6-mon party, not just risks a duplicate.
- The HM catch branch has no owned-species check [CODE story_mode.py HM-LEARNER HUNT branch]. Confirmed.
- Minor: "at least 2 balls" is not a precondition. `ensure_hm_learner` buys more through `provision_poke_balls()` when you have 1 or fewer.

## Missed

- **Hunt order, again.** The order puts R115 last among the late grounds. Any Fly hunt should rank by density (or name R115/R118) instead of taking whichever ground is furthest along and paths first. As written, the recommended window lands on the sparsest ground.
- **Carriers by evolution.** Crobat (Golbat by friendship), Vibrava/Flygon (Trapinch at L35) and Salamence can all learn Fly. Since `can_learn_tm_hm` works per species, none of them was in the 17 "always Swellow" parties. Whether any of the 13 parties has Golbat or Trapinch in a box: could not determine.
- **Frame budget on R119.** At rate 15 there are about 12 steps per encounter, so each Tropius costs roughly 11 unwanted battles, and Intimidate or Keen Eye halves the encounters again. I could not determine whether `_story_spin` counts battle frames against the 40,000 limit. R119 is the ground most at risk of timing out.
- **Surf rate.** Ever Grande water gives about 112 steps per carrier (Wingull 35% + Pelipper 5% at map rate 4). It exists, but it is not cheap.

## Net

The facts about the tables, the ROM data and where the code is called from are accurate. The two corrections that matter:
1. In the recommended §Ch13c window, the hunt order would pick Tropius on R119 (the sparsest ground), not a Wingull ground.
2. A missing `heal_centers` turns a full party into a hard derail, not just a duplicate-catch risk.

I edited nothing in the repo. My fetched decomp copies and check script are in `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/01ddd963-7a1a-4b49-8ecd-33397f5304e2/scratchpad/flyrecon/verify/`.

######## RESULT 4
**Verdict on the "teach" report: the placement and the TRAVEL_PLAN analysis hold up; the slot picker, T2 and the proof plan need changes before building.** Three things break it as written: the picker can choose moves the game won't forget, the League lobby has a PC the report missed, and nothing brings the bot back to the League after it flies away.

## Claims

1. **CONFIRMED.** The Fly disjunct in `_training_area_allowed` just returns `can_fly_to_anchor(...)`, with no chapter gate [CODE story_mode._training_area_allowed]. Its only guards are: a party member knows Fly, BADGE06, the map type allows Fly, and the town's visited flag [CODE training_areas.can_fly_to_anchor]. The boss-prep `_allow` and the maintenance `_maint_allow` both wrap it [CODE story_mode].
2. **CONFIRMED.** Fly is in `banned_moves`, and so is Dive [CODE profiles/battle.yml]. But `moves.json` gives Fly base power 70, so `team_policy.MonView.has_damaging_move` counts it as damaging. The "keeps a usable damaging move" filter has to exclude banned moves itself.
3. **CONFIRMED.** `apply_moveset_plan` raises `BotModeError` in three cases: the species is missing, Wing Attack is missing, or an outstanding Peck→Facade change exists (Peck known and Facade not) [CODE pokemon_league.apply_moveset_plan].
4. **CONFIRMED** in sandbox-pokebot. The only call is inside `fetch_ice_beam`, with an Ice Beam plan, not `TRAVEL_PLAN`. Nothing in `modules/` or `plugins/` calls `fetch_ice_beam` [CODE].
5. **PARTLY.** The fact is right, but the source is wrong: I could not find a "FIXTURES post_fly" doc. The real evidence is the `TRAVEL_PLAN` comment (PathFindingError to (27,48) from (18,6)) and the guard-3 comment in `early_game._fly_to_training_anchor`, which cites `2026-09-18-vr-heal-roundtrip` with a control tile [CODE]. The conclusion drawn from it, that the box can't be reached from the plateau, is wrong (MISSED B).
6. **PARTLY.** `dead_weight` does exempt the only carrier of an HM [CODE team_policy._only_hm_carrier]. But the ladder's heals don't deposit by default: `deposit_dead_weight_if_worth_it` does nothing unless `POKEBOT_PC_ROTATION=1`, and that flag is pinned to 0 [CODE pc_trip.plan_deposits]. Only `deposit_one_dead_weight` (when `_needs_party_slot` is set) and the make-room step in `withdraw_from_box` ever deposit.
7. **CONFIRMED, with a caveat.** The default picks a 0-power move first, otherwise the lowest base power [CODE early_game.teach_hm_move], so Quick Attack (40) goes on post_moveset. On the report's own primary fixture, post_league_shop, the default picks Peck (35), which is the correct slot. The default only fails on the harness-only post_moveset state.
8. **PARTLY.** The population is the 30 **refused** parties out of 39 badge-8 organic runs, not "30 badge-8 parties" [DOC ch23training-DESIGN]. Those runs die at §Ch23's refusal and never reach §Ch24 today.
9. **CONFIRMED, with one more condition.** Fly lands at the League only if `FlagGet(FLAG_LANDMARK_POKEMON_LEAGUE) && posWithinMapSec == 0`, meaning the cursor must also be on Ever Grande's top cell [DECOMP src/region_map.c]. The flag is set in `EverGrandeCity_PokemonLeague_1F_OnTransition` [DECOMP]. The bot maps `FlyDestinationRSE.PokemonLeague` = (28,10) to that flag [CODE region_map].

## MISSED

- **A. HM slots are not protected once the picker names a slot (this refutes §4's first bullet).** `teach_hm_move` only excludes HM slots when `replace_slot is None`. There is no HM check on an explicit slot [CODE early_game.teach_hm_move].
  - The picker's rule 2 ("banned or zero-power") would choose Flash (base power 0) or Dive (banned, HM08). Rule 4 could choose Rock Smash (20) or Cut (50).
  - The game refuses to forget an HM, so the teach loops. This is the exact bug recorded in `teach_hm_move`'s own comment.
  - Fix: `pick_fly_replace_slot` must drop HM slots itself.
- **B. The League lobby has a PC.** Metatile 0x004 sits at (6,1) in `EverGrandeCity_PokemonLeague_1F/map.bin`. Its attribute is 0x83, which is `MB_PC` [DECOMP layout and `metatile_behaviors.h`]. The standing tile is presumably (6,2) [INFERENCE: it mirrors the Poké Center's (10,2)].
  - So a box withdraw is possible from (18,6).
  - `_withdraw_hm_learner` can't be reused as-is: it goes through `heal_in_pokemon_center`, whose nurse tile (7,4) is wrong for the lobby (the handoff says the lobby nurse is at (3,2), talked to from (3,4)). The deposit path also hardcodes `PC_STAND_TILE=(10,2)` [CODE].
- **C. No way back to the League.** Teaching Fly switches production onto the ladder's flying path, which has only been driven in the harness.
  - `train_for_league` ends wherever the last rung left it. The one exception is a Victory Road finish, which steps out to `EG_PC_APRON` on the south side.
  - `prepare_and_open_the_league` raises when not on Ever Grande ("does not navigate across the region"). From the south side, its walk to `LEAGUE_DOOR_APRON` has no path [CODE; INFERENCE on the exact failure].
  - So the teach alone can turn today's "stopped short of the floor" outcome into a derail. The planned drive only checks the outbound flight.
- **D. The picker's tie-break is unspecified.** On post_league_shop both Peck and Wing Attack lose to Aerial Ace, so "picks Peck" needs an explicit rule such as lowest power first.
- **E. Agreeing with the report:** there really is no readiness refusal before the Elite Four. `prepare_and_open_the_league` only records `train_skipped_offmap`, and `run_the_gauntlet` and `enter_the_league` have no level-floor check [CODE].

## NET

**Still standing:**
- The placement and the reasons given for it.
- Not reusing `TRAVEL_PLAN`.
- The T0 and T3 structure.

**Must change before building:**
- **Picker (A).** Exclude HM slots.
- **T2 (B).** Redesign it around the lobby PC.
- **Return leg (C).** Add a fly-back-to-League step, or make it a precondition. The proof must include returning to (18,6).

Fixture movesets and bags are still unread, since no emulator was run. I couldn't determine whether Victory Road 1F (15,39) can be reached on foot from the north door.

Scratch files from this check are in `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/01ddd963-7a1a-4b49-8ecd-33397f5304e2/scratchpad/flyrecon/`.

######## RESULT 5
# Adversarial verification: the "bridge" report

**1. The landmark flag is set only in League 1F, and legs 10 and 11 set it before §Ch24.** CONFIRMED, with one nuance.
- A code search of pret/pokeemerald finds the flag only in `flags.h`, `region_map.c` and League 1F `OnTransition`. [DECOMP]
- The guards are as reported: leg 10 is `_on_map(EG) and not party_is_healthy()[0]`, and leg 11 runs when the basket is short. [CODE victory_road.py:do_victory_road_chapter]
- The flag is skipped only if the basket is already full **and** the party is healthy. The report's single condition (basket full) is not enough on its own, because leg 10 still goes in when the party is hurt.

**2. Training ends at (27,49), and there is no path back.** PARTLY.
- The end tile is confirmed: `T-CONTINUE at EVER_GRANDE_CITY(27, 49)` [LOG 2026-09-24c]. The step-out is also `train_for_league`'s last act, not only its first. [CODE]
- (18,6)→(27,49) returning NO PATH is confirmed. [LOG vr-heal-roundtrip, line C]
- **REFUTED: "the reverse direction was never measured."** `PathFindingError: Could not find a path from (27/49) to (18/5)` was measured on 2026-09-06 [DOC 31-KNOWN-ISSUES-ARCHIVE.md KI-94; FIXTURES.md5 post_ch24ready row]. The recon note repeats the same wrong claim.
- "Then it holds Up into the PC door" is overstated. `_navigate_riding_out`'s fail-fast raises `UnreachableDestinationError`, and `_yield_bounded_by_frames` does not catch it, so the Up-walk is probably never reached [INFERENCE]. Either way the run fails loudly before (9,1).

**3. With the flag set, Fly to PokemonLeague lands at (18,6).** CONFIRMED.
- `CB_ExitFlyMap` picks the League heal location when `posWithinMapSec == 0`. [DECOMP region_map.c]
- `MAPSEC_EVER_GRANDE_CITY` is x=27, y=8, h=2. Adding the cursor offsets (1,2) gives the cells (28,10) and (28,11), so (28,10) is the top cell. [DECOMP region_map_sections.json]
- Heal location League = (18,6), Poké Center = (27,49). [DECOMP heal_locations.json]
- Both measured flights landed at (18,6). [LOG]

**4. `fly_to_destination` does not check where it landed.** CONFIRMED, and worse than reported.
- It checks only `moved`, PID stability and `neighbours_reachable`.
- Its docstring says "the leg asserts the destination MAP". That is false. [CODE pokemon_league.py:fly_to_destination]

**5. Nothing refuses an under-levelled party.** CONFIRMED.
- `run_the_gauntlet` takes `G-PREPARED` unconditionally.
- Nothing in modules, plugins or the harness reads `below_floor_after`. [CODE]

**6. Organic parties never know Fly.** The Fly fact is CONFIRMED. The inference built on it is REFUTED (see Missed #1).
- Production `teach_hm_move` callers teach only HM03, HM04, HM06, HM07 and HM08. [CODE]

**7. The undetermined items.** PARTLY resolved.
- Walking (27,49)→(18,6) has now been measured both ways (see #2).
- Fly from a fainted knower is allowed: `SetPartyMonFieldSelectionActions` and `CursorCb_FieldMove` have no HP check. [DECOMP party_menu.c]
- Still undetermined: warp routing by `navigate_to_anywhere`, and whether VR1F's two halves connect.

**Other points**
- A whiteout does not land indoors. Every Center's heal location is on the outdoor map. [DECOMP heal_locations.json; CODE early_game.py:exit_building_after_whiteout docstring]
- Before the first training heal, the respawn point is (18,6) itself.

## Missed

**1. Organic parties with no Fly walk off the plateau. This is the normal case, not an edge hazard.**
- `_training_area_allowed` admits VICTORY_ROAD_1F through `region_reach.is_map_reachable(..., 4)`. Ever Grande to VR1F is **1 hop** at map level. [CODE training_areas.py: TRAINING_GRASS comment, `AREA_PREREQ[VICTORY_ROAD_1F]="region"`]
- In `_fly_to_training_anchor`, `can_fly_to_anchor` is False, the `region_reach` check is True, so it returns and `train_team` **walks**.
- VR1F's band is 36–40 and `max_wild_max=level+1`, so every trainee at L39–64 qualifies. That includes the battle team, which §Ch23 trained to 47.
- From (18,6) the only Victory Road door is (18,27). It leads to VR1F warp 1 at (39,5), the exit half. The grind tile (15,39) is beside the *entrance* warp at (15,40). [DECOMP EverGrandeCity and VictoryRoad_1F map.json]
- So "the bot mostly stays on the plateau and the bridge is a no-op" is wrong.
- A return ticket that only guards flying never fires here. It must also refuse walking off the north plateau when there is no way back.

**2. The §Ch24 latch lives only in memory.**
- `_ch24_owns_run` is cleared in `reset_per_run_state`, and a fresh bot instance starts without it.
- If the bot restarts while on a route, `ch23_chapter_done()` is False (the bot is not on EG). `do_victory_road_chapter` then runs `cross_to_ever_grande` before `prepare` is ever reached.
- The bridge placed in `prepare` does not cover this resume.

**3. R1's ordering is wrong.** A training retry after the bridge flies off again. The order must be train, then bridge, then R1.

**4. The proof plan has gaps.**
- The F1 fixture (`post_grind_L60.ss1`) is at VR1F, so that arm runs the step-out first. Its landmark flag is unverified; read it at the start of the arm.
- The readiness arm needs a "training off" fault that does not exist. `POKEBOT_CH24ENTRY_FAULT` only offers `nolatch` and `skiptalk`.

## Net

The core of the design holds: claims 1, 3, 4 and 5 check out. Flying to PokemonLeague and then asserting (18,6), plus a readiness gate outside the League, is the right shape.

Two corrections:
- The (27,49)→(18,6) NO PATH was already measured, which makes the split stronger.
- The organic no-Fly case is not "stays on the plateau". Battlers at L39–64 walk into Victory Road through (18,27). The return ticket must cover walking as well as flying, or VR1F must be refused from the north side when there is no Fly.

Also missing: a resume after restart off the plateau goes back into §Ch23 before the bridge can run.