# 2026-09-26 — WHERE ORGANIC RUNS DIE, AND WHAT STANDS BETWEEN THEM AND THE HALL OF FAME

> ⚠ **AI RESEARCH NOTE — NOT A SOURCE OF TRUTH.** Produced by a 10-agent Claude workflow
> (`frontier-recon`: five read-only recon angles, each followed by an ADVERSARIAL verifier told to
> refute it). Every claim below carries its verifier's verdict. Claude subagents had tool access
> (logs, our tree, `gh api` on pret/pokeemerald) — but nothing here was DRIVEN in the emulator.
> ⛔ Verify any load-bearing claim in our own harness before code depends on it
> (`00-READ-THIS-FIRST.md`). Where this note and a current-state doc disagree, the doc wins.

**Corpus:** the 99-run ENDLESS corpus of 2026-09-15/16 (`sandbox-pokebot/profiles/endless-P*/debug-logs/`,
builds `e2b0f8af`/`2f8a6332`/`658d41fe` — the latter two docs-only, so ONE code build) and the x4 batch
`20260913-092254` (`f039bffc`, 42 runs, 76 % cut off by its 120-minute limit — a measure of the time
limit, not of failures). ⚠ The lane `stdout` file is present BOTH in `debug-logs/` and in `debug-logs/Old/`;
globbing both doubles every count.

## 1. THE FUNNEL (MEASURED; both verifiers CONFIRMED)

| milestone | endless (n=99) | x4 (n=42) |
|---|---|---|
| Badge 1 | 98 | 39 |
| Badge 5 (Norman) | 77 | 29 |
| Badge 6 (Winona) | 60 | 18 |
| Badge 7 (Tate & Liza) | 53 | 5 |
| **Badge 8 (Juan)** | **39** | 2 |
| Ever Grande City loaded (outdoor map) | 30 | 2 |
| **Victory Road loaded** | **0** | 0 |
| League interior / Hall of Fame | 0 | 0 |

Badges from `badge-log.json`; maps from `analyze_endless_batch.py`'s MEASURED column (its assumed roll-up
says 30 at Victory Road — false).

## 2. ⭐⭐ ALL 39 BADGE-8 RUNS DIED **INSIDE §Ch23** (CONFIRMED by two independent verifiers)

* **30 runs — the §Ch23 training refusal.** Every run that loaded Ever Grande healed at the Poké Center,
  reached `VR_APRON (18,42)` (i.e. ABOVE the waterfall), and then `train_for_victory_road` raised
  `Ch23 training: <mon> alone needs N frames, over the 250,000 per-call ceiling` — 3 attempts × 5 derails,
  identical every time, then the endless reset. 0 runs reached `enter_victory_road`.
  * Refused mon (worst per run): **Marill ×11** (always L13, always 406,972 frames — an IDENTICAL estimate
    means identical total EXP ⇒ MEASURED evidence it never gained EXP), Slugma ×5, Loudred ×3, Swellow ×2,
    Mightyena ×2, Ninjask ×2, five singletons. 18 of 30 were L≤19 mules; 12 were L26-37 team members
    (the *no-training-after-Winona* half of `#24-lowlevelmules`). P4-9's Swellow was only 2.6 % over.
  * ⛔ `#26-victoryroadgap`'s "bounces between (0,8) and (16,12) and never climbs" is REFUTED: (16,12) is
    the Ever Grande Poké Center (decomp `map_groups.json`), the bounce is the heal, and the bot WAS above
    the waterfall.
  * **This is the existing `#24-ch23training` / `#24-lowlevelmules` blocker.** Already-refuted fixes, do
    not re-try: Marill into `BENCH_SPECIES` (benching = not trained, still fielded — `04-HANDOFF`);
    training in steps (69 battles, no gain — `08-MISTAKES` 2026-09-08); raising the ceiling (it stands
    in for "can this mon survive that grass").
* ✅ **FIXED 2026-09-26 (`#26-carleestage`; reproduced and A/B-proven, see `2026-09-26-ch23-carleestage-GRADED.md`) — the mechanism below is now MEASURED, not plausible.** **9 runs — Route 128 `CHANNEL_STAGE (101,26)` unreachable.** `Could not reach (101, 26) on ROUTE128 …
  still at (101, 25)`, right after `Route128_EventScript_Carlee`. Decomp mechanism (verifier, PLAUSIBLE —
  Carlee's live position was NEVER READ): Carlee sits at (101,29) `WALK_UP_AND_DOWN` range_y 3, sight 4;
  a trainer that walks up to the player stops and is re-typed to face-direction (`trainer_see.c`
  `PlayerFaceApproachingTrainer`), so she stays on (101,26) — exactly our stage tile, which sits inside
  her patrol. The 2026-09-03 "free tile" measurement was taken while she was elsewhere.
  ⚠ 5 of these 9 carried Marill L13 ⇒ fixing this ALONE likely converts most into training refusals.
* ✅ **Ruled out:** the per-run frame cap (0 of the 39 hit it; the 6 cap kills were all BEFORE §Ch23 —
  Space Center, Tate & Liza ×2, Juan ×2, Sootopolis), and `#24-waterfallcap` (`victory_road.py` never
  imports `region_reach`; the refusal is a frame-cost estimate made before any navigation).
* ⚠ **"Unchanged at HEAD" is true of the MECHANISM, not proven of the INPUT** (verifier): the refusal code
  is AST-identical since `e2b0f8af`, but the party that arrives may differ (Fly disjunct, battle fixes
  `461b6104`/`96ed1ec7`, PC-first HM carrier `caee0b26`/`bf731d97`). Unmeasured, not "unchanged".

## 3. OTHER RUN-ENDING CAUSES (endless, 95 ended runs; CONFIRMED category-by-category)

| cause | runs | badges at end |
|---|---|---|
| §Ch23 training refusal | 30 | 8 |
| boss type-wall give-up (Winona 8, Juan 6, Tate & Liza 5, other 2) | 21 | 5 / 7 / 6 |
| Poké Center walk BLOCKED (Lavaridge 7 via ROUTE112→CABLE_CAR; Fallarbor 3 via MT_CHIMNEY) | 10 | 3 |
| §Ch23 ROUTE128 (101,26) | 9 | 8 |
| per-run frame cap (5M) | 6 | 6-7 |
| Surf-learner hunt: ROUTE101 (9,9) unreachable from ROUTE104 — the defect is `_hm_hunting_grounds`' fallback to `grounds[0]` when nothing paths (verifier correction) | 6 | 5 |
| watchdog 5 · no balls/money for an HM hunt 4 · cutscene 2 · other 2 | 13 | — |

⚠ "Never ended a run" ≠ "recovered" (verifier): this per-run tally is NOT the per-derail RECOVERED/FATAL
classifier `#26-destreachability` asks for.

## 4. PAST §Ch23 — THE ORGANIC §Ch24 HAND-OFF HAS UNDRIVEN GAPS (organic-path audit; verifier verdicts inline)

1. **Production never teaches Fly (HM02)** — CONFIRMED. `TRAVEL_PLAN` / `apply_moveset_plan` are reached
   only from harness drivers (`ch24fly`) and `fetch_ice_beam`, which has no production caller. ⇒ an
   organic party cannot use the Fly ladder; trainees below ~L39 get "no reachable ground" and stay low.
   (The claim "every §Ch24 fixture has a Fly user" is REFUTED — `post_grind_L60.ss1` has none.)
2. **After training, nothing gets the bot back to the League door** — code path CONFIRMED, outcome
   INFERENCE. `train_for_league` ends in `_ch24_step_out_if_fly_illegal` → `EG_PC_APRON (27,49)`;
   `prepare_and_open_the_league` then needs `LEAGUE_DOOR_APRON (18,6)`, and Ever Grande's north (League)
   and middle (Poké Center) areas connect only through Victory Road or by Fly (decomp layout; same-map
   NO-PATH measured both ways). The Fly-to-League step exists only in harness drivers (`ch24toleague`,
   `ch24flyto`). ⭐ **Named decisive test:** `navigate_to_anywhere(EG, (18,6))` from (27,49) in a harness
   driver. Likely fix: a production Fly-to-League step after training.
   ⭐ The routing verifier made this STRONGER: Ever Grande row y=37 has ZERO collision-0 tiles for
   x=0..39 (decomp) ⇒ the split holds in both directions. ⚠ But the punch list's "NO PATH IN BOTH
   DIRECTIONS, measured" overstates: only (18,6)→(27,48/49) was measured. ⚠ `train_for_league` has no
   "return to the League" postcondition at all (at floor 21 it ended on ROUTE117). ⛔ **And the §Ch24
   training driver's T-CONTINUE is VACUOUS**: it paths to `fly_landing_tile(PokemonCenter.EvergrandeCity)`,
   the tile the bot already stands on (0 wp), so the climb's PASS says nothing about reaching (18,6).
   ⚠ A Fly-to-League bridge lands at the League only if `FLAG_LANDMARK_POKEMON_LEAGUE` is set
   (decomp `region_map.c` `CB_ExitFlyMap`); `ch24toleague-TREATMENT.txt` is a measured arrival at (18,6).
3. **No readiness refusal before the one-way Elite Four** — CONFIRMED. `E1-READY` is a reading, not a
   gate; `run_the_gauntlet` never reads `below_floor_after`. The `story_mode.py` comment saying the
   readiness guard "IS step 1" is false.
4. **Money** — CONFIRMED: basket ₽54,300 vs a ₽1,741 measured margin (one chain drive); whiteouts halve
   money (`DoWhiteOut`). **22b** (`ensure_waterfall_learner`) has no PC-first fallback and no hunt.
5. Lower: `_ch24_owns_run` is in-memory only; the derail budget can be reset by EXP gains
   (`_progress_sig`), so "5 derails then Manual" is not guaranteed.

## 5. ROUTE MAP DISCREPANCIES (decomp vs our constants; model is the agent's own reimplementation ⇒ INFERENCE)

* **D1** `EG_EXIT_LANDING = (18,27)` is WRONG — the measured landing is **(18,28)**; (18,27) is the walk-on
  door BACK into Victory Road. The constant is currently unused; aiming at it would warp the bot back.
* **D2** Leg 7's comment says the planner "rides the DESCENT"; `map_path.py` emits `WaypointAction.Waterfall`
  only for `Direction.North` ⇒ the measured `{Surf:1, Waterfall:1}` is a CLIMB.
* **D3** Leg 5's comment says Edgar belongs to leg 7; he is on 1F, on leg 9's route.
* **D4** `12-STORYMODE-DESIGN.md` has no §Ch23 section although it says "see §Ch23 below".
* ⚠ Verifier: the "only path" trainer lists are NOT safe — a flood-fill finds a leg-6 route that avoids
  Samuel but forces Shannon (26,12-15) instead (INFERENCE). The ledge list omits (17,38) `MB_JUMP_SOUTHWEST`.
* **H2** Halle (B1F) can block the only corridor if she spots the bot at (16,20); routing via
  (15,19)→(15,20) avoids a forced second fight. Unhandled; one leg-8 drive saw 1 trainer battle.

## 6. TOOLING DEFECTS FOUND (CONFIRMED)

* `analyze_endless_batch.py`'s League-interior check **can never fire**: every League room and the Hall of
  Fame carry `MAPSEC_EVER_GRANDE_CITY`, so logs print `EVER GRANDE CITY(16,N)`; its self-test string
  never occurs in a log. Detect by map group/number (16, 0-11 and 14) or the `§Ch24 COMPLETE` line.
  Milestones stop at Ever Grande.
* `x4_headless.py`: `--build` defaults to **custom**; its badge regex is title-case and never matches
  the emitted `DYNAMO BADGE earned` strings.
* On the current sandbox, an endless outcome of `finished` means `ch24_chapter_done()` passed — the only
  cleared-game signal the batch tooling has. Finish rates are not comparable across 2026-09-25.
* The per-run frame counts on endless outcome lines were wrong from run 2 on — FIXED 2026-09-26
  (`#26-endlesscap`).
