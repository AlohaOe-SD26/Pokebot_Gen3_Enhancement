# §Ch24 `#24-levelgap` — RECON BEFORE THE BUILD (2026-09-18)

> ⛔ **AGENT OUTPUT IS A NOTE, NEVER TRUTH.** Four agents on different angles (our training code paths,
> chapter wiring, the B1F ground, and one explicitly ADVERSARIAL). ✅ marks what **I** re-verified at
> FILE:LINE in this round. ⛔⛔ **NO PRODUCTION CODE WAS WRITTEN.** This scopes the build.

---

## ⭐⭐ THE HEADLINE: THE BLOCKER IS NOT THE FRAME CEILING. IT IS THE HEAL.

`#24-levelgap` is framed around `MAX_TRAINING_FRAMES = 250_000` refusing every configuration. That
framing is **inverted by a fact I verified myself**:

✅ **`MAX_TRAINING_FRAMES` IS NOT ENFORCED INSIDE `train_team`.** It is defined at
`victory_road.py:508` and enforced at **exactly one site**, `victory_road.py:2021`, inside
`train_for_victory_road`. The symbol does not appear in `early_game.py` at all.
⇒ **a new §Ch24 leg calling `train_team` directly inherits NO frame ceiling whatsoever** — only
`train_team`'s own 500-ROUND guard (`early_game.py:2102-2103`).
⇒ ⛔ **That is a hazard, not a licence.** `victory_road.py:505-507` says so in terms: *"`train_team`
itself has NO frame budget — only a 500-ROUND guard — and KI-28 burned 19.9M frames on a target the
local grass could not deliver."* **The new leg must impose its own budget, because nothing else will.**

⇒ The real blocker is the one already filed as **`#24-cavehealblind`**: *can a grind inside Victory
Road heal at all?* Everything else recon touched is either solved or favourable.

---

## ⛔⛔ A DOCUMENTED, "VERIFIED" CLAIM IS FALSE — AND IT IS LOAD-BEARING FOR THE BUILD

Both `29-DISABLED-FEATURES-REGISTRY.md` (the `POKEBOT_CH24_FAULT_NOWALK` row) and
`story_harness.py:15583-15585` state, marked *(verified 2026-09-17)*:

> *"⛔⛔ `train_team` **DOES NOT TRAVEL**. It grinds the grass it is STANDING IN and heals at
> `heal_center`; its body references neither `TRAINING_GRASS` nor `best_training_area`."*

✅ **THE FIRST HALF IS FALSE. I READ IT MYSELF.** `train_team`'s loop body calls
`_goto_training_area(grass_map, grass_tile)` **every round** — the CALL at `early_game.py:2125`, the function at `:2049-2068` — and
`_goto_training_area` (`:2049-2066`) threads a cave door when the map is in `_CAVE_ENTRANCES` and then
ends in `_navigate_riding_out(grass_map, grass_tile, avoid_encounters=False)`.
✅ **THE SECOND HALF IS TRUE** — neither `TRAINING_GRASS` nor `best_training_area` appears in its body.

‼ **WHY THIS MATTERS MORE THAN A DOC TYPO:** the whole `#24-levelgap` design question *"the ground is
not a parameter"* is about `train_for_victory_road`'s hardcoded `grass=TRAIN_SPOT_1F` (`:2088`) and
its local `WILD_MAX = 40` (`:1988`) — **not** about `train_team`, which takes `grass` and walks to it.
✅ Production already proves the shape: `story_mode.py:4183-4184` calls
`train_team(level_floor, scope="whole", grass=RUSTBORO_TRAINING_GRASS, heal_center=PokemonCenter.RustboroCity)`.

⇒ ⚠ **AND THE `NOWALK` FAULT ARM DOES NOT TEST WHAT ITS ROW CLAIMS.** Parked off-grass, `train_team`
does not "quietly train nothing because it never moves" — it **tries to navigate to
`TRAIN_SPOT_1F` anyway**. Whether that navigation SUCCEEDS from a Poké Center is a different and
**unmeasured** question. ⛔ I found **no committed evidence file** for that arm (the
`2026-09-16-e4exit-CONTROL-NOWALK.*` files belong to `--driver e4exit`, a different driver).
⇒ **The arm's stated rationale is retracted; its observed behaviour is unverified here.**
⭐ Correctly understood, that arm is **the `#24-cavehealblind` experiment in disguise**: it measures
whether `train_team` can navigate from OUTSIDE into Victory Road grass.

---

## ✅ WHAT I MEASURED MYSELF THIS ROUND (`probe_vr_heal_roundtrip.py`, planning only)

Evidence: `tools/story-dev/evidence/2026-09-18-vr-heal-roundtrip.stdout.txt`

| from | ask | result |
|---|---|---|
| `post_wally.ss1` — `VICTORY_ROAD_1F (9,15)` | **same-map** → the grind tile `(15,39)` | ✅ **OK, 44 wp** |
| `post_wally.ss1` | cross-map → the Ever Grande Poké Center | ⚠ REFUSED-AS-MALFORMED (*"not on connected maps … warps don't count"*) — **not** a reachability answer |
| `post_ever_grande.ss1` — `EVER_GRANDE_CITY (18,42)` | → Poké Center door `(27,48)` | ✅ **OK, 23 wp, 1 warp** |
| `post_ch24_atdoor_L75.ss1` — `EVER_GRANDE_CITY (18,6)` | → Poké Center door `(27,48)` | ⛔⛔ **NO PATH** — and this is a **SAME-MAP** ask, so it IS a real reachability answer |

⭐ **EVER GRANDE IS SPLIT — ⚠ AND THIS REPRODUCES A DOCUMENTED MEASUREMENT RATHER THAN DISCOVERING ONE.** ‼ I wrote “nobody had connected this” and that was an over-claim, caught before publication: `story_harness.py:15422-15423` already says *“from the League door (18,6) `calculate_path` reaches neither grass nor a Poké Center”*, and `:15601-15603` records `(27,49) -> VR_APRON (18,42)` as *“OK, 22 waypoints, under a two-sided control (PC door OK; League door FAIL, reproducing `FIXTURES.md5`)”*. ⇒ **my probe is a CONTROL on my own instrument, and it agrees with the record.** What is still mine to add is the CONSEQUENCE: From the
League-door apron `(18,6)` the Poké Center is **unreachable on foot**; from `(18,42)` it is 23 wp.
⇒ **that is almost certainly why §Ch23's leg 10 heals at the LEAGUE NURSE** (`heal_at_league`,
`victory_road.py:2962`, navigating to `LEAGUE_NURSE_STAND (3,4)`) **rather than at the Poké Center.**
⇒ ⛔ A §Ch24 grind that heals at `PokemonCenter.EvergrandeCity` inherits this split. `train_team`'s
`heal_center` parameter takes a `PokemonCenter`, and **the League nurse is not one** — so a
League-side grind cannot reuse `train_team`'s heal path as-is.

⚠ **THE HONEST LIMIT OF ALL FOUR ROWS:** `calculate_path` **plans**; it does not walk. And
`_navigate_riding_out` wraps `navigate_to_anywhere`, which ✅ `early_game.py:1988-1997` records as
*"a multi-hop, self-replanning, live-validated warp navigator"* that crossed 3 warps in each direction
in a real drive — **so a `calculate_path` refusal does NOT bound what the navigator can do.**
⇒ **Only a drive settles the heal.** That is `#24-cavehealblind`, and it is now the gating item.

---

## ⛔⛔ THE ADVERSARIAL PASS REFUTED THE ITEM'S CENTRAL FEASIBILITY CLAIM — AND I RE-DERIVED IT MYSELF

`#24-levelgap` states: *“every 2-level step fits the ceiling — worst step **136,135 f against
250,000**, 1.8× headroom.”* ⛔ **BOTH HALVES ARE WRONG, AND THE SECOND IS WORSE THAN THE FIRST.**

**(a) THE CITED “WORST STEP” IS AN INTERIOR STEP.** ✅ Wailord is `Fluctuating`
(`modules/data/species.json`), whose EXP curve past L36 is `((level // 2) + 32) * level**3 // 50`
(`modules/pokemon.py:615-621`). Cost therefore RISES monotonically with level, so the worst step is
the **LAST** one. Computed by me from those exact formulas and the estimator's own constants
(`CAL 50.2`, `FRAMES_PER_WILD_BATTLE 1433`):

| step | @ wild 40 (1F) | @ wild 42 (B1F) |
|---|---|---|
| 47→49 | 88,846 | 84,547 |
| 57→59 ← **the item's cited “worst”** | 141,867 | **136,135** |
| 71→73 | 247,909 | 236,445 |
| **73→75 — THE ACTUAL WORST** | ⛔ **266,538** | ⛔ **253,641** |

⇒ **the real worst step is OVER the 250,000 ceiling on BOTH grounds**, on the item's own
uncorrected model. The quoted 136,135 is the 57→59 step at wild 42 — real, but not the worst.

**(b) AND THE MODEL IS KNOWN-WRONG BY ~3.3×, IN A FILE DATED ONE DAY EARLIER.** ✅ VERIFIED at
`story_harness.py:15416-15420`: the wall-clock figures there are *“already **doubled** for the
measured **0.501 participant divisor the estimator does not model**”*, and *“⚠ Expect **~1.65× on
top**: the measured A/B runs **~2,368 frames per WIN** against the estimator's **1,433 frames per
BATTLE**”*. Combined: **(1/0.501) × (2368/1433) = 3.30×**.
⇒ applied to my table, **EVERY step exceeds the ceiling, including the first**:
`47→49 = 88,846 × 3.30 = **293,046**`; `73→75 = **879,138**`.

⇒ ⛔ **“2-level steps” IS NOT A VIABLE DESIGN AS SPECIFIED.** The design consequence is concrete:
**step size must SHRINK as level rises**, and the budget must be derived from the MEASURED cost, not
from `estimate_frames_to_level`. ‼ Note this interacts with the headline finding: a leg calling
`train_team` directly is not refused by the ceiling at all — it would simply **run for 879,138 frames
without complaining**, which is KI-28's shape exactly.

**(c) THE ITEM NAMES A GROUND THAT HAS NO VERIFIED TILE.** The item says *“on Victory Road B1F
ground”*; ✅ the driver it proposes promoting trains on **1F** — `story_harness.py:15603`
`GRIND_TILE = VR.TRAIN_SPOT_1F[1]` — and B1F's `PENDING_GRASS` row carries `None` for its spin tile.
⇒ building to the item's literal wording requires **inventing and two-way sweeping a new B1F spin
tile**, which is unscoped work, not “promote 33 lines”.

⚠ **WHAT THE ADVERSARIAL PASS did NOT overturn:** resumability is genuinely free (levels bank to the
ROM save; `SetMoney(money/2)` threatens only §Ch23's pre-purchase basket margin, and Poké Center
healing is free); the per-call ceiling really is per-call; and the roster/fainted-mon risk is
inherited from existing code, not introduced here.

## ✅ WHAT RECON SETTLED IN THE BUILD'S FAVOUR

| question | answer | strength |
|---|---|---|
| Usable wild ground on B1F? | **8 walkable `Cave` tiles, `has_encounters=True`, 2-3 wp from the `(8,3)` arrival ladder.** Best candidates `(9,4) (7,4) (9,5) (10,4) (6,4)`; ⛔ **not** `(9,3)/(7,3)` — cardinally adjacent to the ladder WARP | agent, from a **STATIC ROM read** — ⛔ never confirmed live (KI-74: a layout-swapped map lies to static readers) |
| Encounter band | L38-42; Golbat 35% / **Hariyama 35% (base EXP 184)** / Lairon 25% / Mawile 5%; max **42** | agent, ROM cache + 2 in-tree corroborations |
| Does the B1F "isolation" block a grind? | ⭐ **NO — it is a GUARANTEE.** 3/3 spin candidates route from the ladder; **0/5 trainers and the B2F warp do NOT** ⇒ nothing can ambush a parked spin and it cannot wander onto a ladder. 1F is *worse* on this axis (five trainers plus Wally) | in-tree, corroborated by a LIVE drive (`2026-09-04-ch23-b1f-recon-LIVE.txt`) |
| Launch fixture | `post_wally.ss1` — `VICTORY_ROAD_1F (9,15)` = `B1F_LADDER_APRON`, **one warp from the pocket**, already pinned | ⚠ inferred by the agent, not a project ruling |
| `team_is_ready` raises? | ⛔ **NO — it NEVER raises**; it returns `(bool, list)`. The raises live in the CALLER | agent ✅ at `victory_road.py:1847-1912` — ⚠ **this contradicts `#24-levelgap`'s line *"`team_is_ready(target)` raises terminally"*, which should be corrected |
| Crunch clause | gated on the MOVE, never the level; does not consult `target` ⇒ unaffected by stepping upward. But if Mightyena lacks Crunch it fails at EVERY level ⇒ **check once, up front** | agent + already in the item |
| Swap-train doubling the cost? | ⚠ **probably NOT at this level.** The turn-1 swap fires only when `active.level + 2 <= foe.level`; at L47+ against L40-42 wilds the trainee out-levels the foe, so it solos for full XP | ⚠ agent INFERRED — **unmeasured, and it cuts against the item's "double all of it again" caveat** |

---

## ✅ THE CHAPTER CONTRACT §Ch24 MUST SATISFY (mapped, not guessed)

⭐ **`modules/story/pokemon_league.py` ALREADY EXISTS — 1,544 lines of §Ch24 leg helpers** and is
**already inside every `modules/story/` gate's scope**. There is **no** `do_pokemon_league_chapter`
and **no** `ch24_chapter_done` anywhere in the tree.

The reference skeleton is `do_victory_road_chapter` (`victory_road.py:3327-3484`): resume-safe early
return → `for attempt in range(1, 4)` → `_check_abort()` as the FIRST statement OUTSIDE the `try` →
position-dispatched guarded legs → `except StoryAbort: raise` + `except BotModeError: reraise_if_aborting(error)`
→ post-loop re-check → terminal raise. Wiring is a four-line contract in `story_mode.py:5170-5176`.

⛔ **GATES THAT WILL GRADE NEW `modules/story/` CODE ON DAY ONE:** #7 undefined-names (hard zero),
#8 silent-except (**per-root ratchet: `modules/story` = 123**), #27 abort-swallow (**ratchet 27**),
#43 HM coverage, #56 yield-in-finally (hard zero), name-resolution, encoding, flag-names.
⇒ the `except StoryAbort: raise` + `reraise_if_aborting` pair is **required by gate #27**, not a style
choice.

⭐ **AND A FORWARD OBLIGATION ALREADY WRITTEN AGAINST §Ch24** (`victory_road.py:3310-3311`): it *"MUST
set its own progress marker so §Ch23 is not re-entered"* once it spends the basket — which is exactly
`#24-markerwinstate`, and `#24-ch23lobbyresume` measured what happens without it.

---

## ⛔ WHAT THIS RECON DOES **NOT** ESTABLISH

* **Whether a Victory Road grind can heal.** Every path above is a PLAN. `#24-cavehealblind` needs a
  DRIVE: park on a B1F pocket tile, force a heal, observe. **Nothing should be built before it.**
* **Whether the B1F tiles are really `Cave` LIVE.** The 8-tile table is a STATIC ROM read and KI-74 is
  precisely the case where that lies. A live grid read is owed.
* ✅ **The frame arithmetic IS now settled — and it REFUTES the item** (see the section above).
  What is NOT settled is the REPLACEMENT: a viable step schedule must be derived from the
  **measured** cost (≈3.3× the model), and **no such schedule has been computed or driven.**
* **Any production code.** Nothing was written, and the ground/`WILD_MAX` plumbing inside
  `train_for_victory_road` remains exactly as `#24-levelgap` describes it.
