# §Ch24 WIRING RECON — 10 AGENTS, AND WHAT I RE-VERIFIED MYSELF (2026-09-17, late)

> ⛔ **AGENT OUTPUT IS A NOTE, NEVER TRUTH** (`00-READ-THIS-FIRST.md`). Everything marked ✅ below was
> re-checked BY ME at FILE:LINE, or by running the command shown. Everything under "LEADS" was NOT,
> and is labelled as an agent claim.
> ⛔⛔ **THIS NOTE DOES NOT REOPEN THE STANDING RULING.** `06-DECISIONS-LOG.md:5426` — *"DO NOT WIRE
> SEGMENT 24 YET"* — still stands. The prerequisite count is **FOUR** (`#24-levelgap`).

---

## ⭐⭐ THE FINDING THAT MATTERS: THE CHOSEN PROGRESS MARKER DOES NOT COVER **WINNING**

The 2026-09-16 ruling (`06-DECISIONS-LOG.md:5496`) decided: *"the marker is 'the bot is standing on a
SEALED League map'"*, safe **by exhaustion** because no whiteout can respawn on one.

✅ **THE EXHAUSTION ARGUMENT IS TRUE — I RE-MEASURED IT.** `gh api .../src/data/heal_locations.json`
parsed: **22 heal locations over 20 distinct maps, and NOT ONE is a League interior.** Both Ever
Grande entries are OUTDOORS on `MAP_EVER_GRANDE_CITY` — `(27,49)` and `(18,6)`; the only INDOOR heal
locations in the entire game are the two Littleroot bedrooms. And entering the lobby arms the outdoor
one: `EverGrandeCity_PokemonLeague_1F_OnTransition: setrespawn
HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE` (decomp, read by me).

⛔⛔ **BUT THE MARKER IS STILL INCOMPLETE, AND MY OWN TAIL PROBE HOLDS THE COUNTEREXAMPLE.**
A *winning* §Ch24 ends at **`LITTLEROOT_TOWN_BRENDANS_HOUSE_2F (4,2)`** (MEASURED —
`2026-09-17-ch24-legB-TAIL-MEASURED.md` Q8). **That is not a League map.** So after a win the marker
reads FALSE, `ch23_chapter_done()` is consulted, and — verified line by line:

| # | step | evidence |
|---|---|---|
| 1 | `ch23_chapter_done()` needs `_on_map(EG)`; Littleroot is not Ever Grande ⇒ **False** ⇒ §Ch23 runs again | `victory_road.py:3318` |
| 2 | legs 1–3 self-skip — `_PRE_DEPARTURE_MAPS = (CITY, PC_1F, PC_2F, UWS, UW126)`, no Littleroot | `:3275` |
| 3 | leg 4 fires: `if not inside_vr and not at_ever_grande_top()` — `inside_vr` False, and `at_ever_grande_top()` is `inside_league() or (_on_map(EG) and y <= EG_LANDING[1])`, **both False from Littleroot** | `:3384-3385`, `:1426-1427` |

⇒ ⭐ **THE BOT WOULD ATTEMPT AN OCEAN CROSSING FROM A BEDROOM**, burn the chapter's attempts, and
raise — turning a *completed game* into a hard §Ch23 failure.

✅ **THE FIX IS ALREADY IMPLIED BY THE RECON'S OWN DESIGN, AND IT IS ONE WORD: A DISJUNCT.** The marker
must be *"on a sealed League map **OR** the game is cleared"*. `IS_CHAMPION` (flag **2175**) is the
right second term because it is **MONOTONE**: set in exactly one decomp file
(`data/scripts/hall_of_fame.inc`) and **cleared nowhere** — unlike `ELITE_4_STATE` and the four
`DEFEATED_ELITE_4_*` flags, which `ResetEliteFour` wipes on BOTH the winning and losing paths.
⚠ `IS_CHAMPION` alone is reported ~13,000 frames early (agent claim, unverified) — it is a completion
term, not a "run is usable" term.

---

## ✅ SIX OTHER FACTS I RE-MEASURED MYSELF

| # | fact | how I checked it |
|---|---|---|
| 1 | **The derail limit is 5, not 4.** `self._derails += 1` then `if self._derails > 4: raise` ⇒ the FIFTH consecutive no-progress derail escalates | read `plugins/custom_modes/story_mode.py` |
| 2 | **No heal location is a League interior** — 22 locations / 20 maps; the only INDOOR ones are the two Littleroot bedrooms | `gh api .../heal_locations.json`, parsed. ⚠ **already ruled 2026-09-16** — confirmation, not news |
| 3 | **Entering the lobby arms an OUTDOOR respawn** at `MAP_EVER_GRANDE_CITY (18,6)` | `gh api .../EverGrandeCity_PokemonLeague_1F/scripts.inc` |
| 4 | **`set_manual_mode` is the harness/production discriminator** — 163 calls in `story_harness.py`, **0 real calls** in `modules/story/` (3 hits, all prose in `roster.py`) | `grep -rn` both trees |
| 5 | **Land maxima 1F 40 / B1F 42 / B2F 44** — corroborated IN-TREE, closing an evidence gap a reviewer had flagged as unverifiable | decomp `wild_encounters.json` **and** `training_areas.py:149-151` `(VICTORY_ROAD_B1F, None, (38, 42))` |
| 6 | **B1F already has a training-areas slot with `spin_tile = None`** — the hole is pre-cut | `training_areas.py:150` |

---

## ⛔⛔ TWO HAZARDS THE ADVERSARIAL PASS FOUND THAT I HAD NOT CONSIDERED — BOTH VERIFIED

**(a) THE HEAL PATH IS THE HIDDEN COST OF GRINDING ON B1F, AND IT IS ABSENT FROM EVERY FRAME MODEL.**
`train_team` heals at a Poké Center whenever HP or PP dips (`early_game.py:2153-2158`, which already
carries a `_exit_training_cave_if_inside()` step from the Granite Cave incident). But:
* `victory_road.py:2282-2284` — *"⛔ IT HEALS FROM **1F**, NOT FROM B1F … from B1F it would have to
  re-cross the puzzle — and the puzzle RESETS on every warp, so a round trip from below costs the
  entire solve twice."*
* `victory_road.py:229-234` — `B1F_PUZZLE_RESETS_ON_WARP = True`; *"EVERY WARP RESETS THE ENTIRE
  PUZZLE … ⛔ NEVER CACHE 'THE PUZZLE IS SOLVED' ACROSS A WARP."* (their note says CONFIRMED LIVE).
⇒ a multi-hundred-battle grind means **many heals, each costing a full puzzle re-solve.**

**(b) B1F CARRIES A TRAINER.** `victory_road.py:2345-2346` — *"Refusing to descend — B1F carries a
trainer and wild encounters, and this is how a run whites out underground."* A defeated trainer does
not respawn, so trainer EXP is one-shot and does not belong in a wild-encounter model; the sight-line
is also an ambush risk for a parked spin.
⛔⛔ **THIS BULLET ORIGINALLY ENDED “The trainer's tile is not located anywhere in our tree.” THAT IS SUPERSEDED — I LOCATED ALL FIVE THE SAME DAY**; see the MEASURED section at the foot of this note. There are **five** trainers, and **every one is ≥16 manhattan tiles from every usable candidate spin tile**, against sight radii of 2–4. ⇒ the trainer hazard is REAL for traversal and **effectively nil for a parked spin at the arrival corner.**

### ⭐ THE CONSEQUENCE, AND IT INVERTS THIS ITEM'S ASSUMPTION

`#24-levelgap` assumes the post-Wally grind happens on **B1F**, for +22.6% EXP/battle.

⛔⛔ **THIS SECTION ORIGINALLY ARGUED THAT B1F “costs a puzzle re-solve per heal, carries a trainer, and
has no `TRAIN_SPOT_B1F`” ⇒ “the cheaper post-Wally ground may be the one we already have.” TWO OF
THOSE THREE LEGS ARE NOW GONE, MEASURED BY ME THE SAME DAY:**
* **“Carries a trainer” — true but NOT A COST HERE.** All five B1F trainers are ≥16 manhattan tiles
  from every usable candidate, against sight radii 2–4. For a *parked spin* the hazard is nil.
  ‼ And 1F is **worse** on this axis, not better: it carries **five trainers plus Wally**.
* **“No `TRAIN_SPOT_B1F`” — true, and now trivial.** Eight walkable `Cave` tiles are measured and
  listed below; naming the constant is the remaining work, not finding the tile.
* ✅ **THE ONE LEG THAT SURVIVES IS THE HEAL COST**, and it is the whole question: from B1F a heal
  means re-crossing a puzzle that **resets on every warp**.

⇒ **THE CHOICE NOW RESTS ON A SINGLE UNMEASURED NUMBER: the frame cost of one B1F heal round-trip.**
If it is small relative to ~450k frames of grinding, B1F's +22.6% EXP wins outright; if a heal costs a
full puzzle re-solve every time HP or PP dips, 1F's one-warp exit may dominate. ⛔ **Nobody has priced
it. Price it before choosing** — and note that it is now the ONLY thing separating the two grounds,
which makes it a cheap and decisive measurement rather than a vague concern.

---

## LEADS — AGENT CLAIMS I HAVE *NOT* VERIFIED (do not build on these)

* ~~B1F candidate training tiles (agent claim)~~ → ✅ **PROMOTED TO MEASURED, BY ME, 2026-09-17
  (late).** See the dedicated section below — the agent's claim was correct on every point I checked.
* **Migration scope:** ~2,916 harness lines across seven `Ch24*` classes whose *production kernel is
  ~90 lines of action*; the three room drivers are ~77% byte-identical (one unit, three instances);
  `Ch24ToLeagueMode` is a pure FIXTURE BRIDGE contributing zero production code.
* **`ch24_chapter_done()` design:** `IS_CHAMPION` plus a **negative** position term, because the map
  memory reportedly still reads `HALL_OF_FAME (16,11)` through the Hall of Fame, the credits AND the
  main menu — so a negative term is False for the whole unusable window.
* **`at_ever_grande_top()` was widened 2026-09-10** to short-circuit True inside the League, and that
  one line is what makes all eleven legs self-skip in the sealed zone. ✅ I confirmed the line exists.

## ⛔ WHAT THIS RECON DOES **NOT** ESTABLISH

* Nothing here unblocks wiring. **FOUR** prerequisites remain open, and `#24-levelgap` is the one that
  decides whether wiring is USEFUL AT ALL.
* The adversarial angle's verdict on the wiring plan was **"KILL THE PLAN AS STATED"**, because its
  step (1) is verbatim one of the standing ruling's already-REJECTED alternatives. Recorded so it is
  not re-proposed.
* ‼ **One agent's top "refutation" quoted my own just-committed docs back at me.** That is
  circularity, not corroboration, and it is not counted as support anywhere above.


---

## ✅ MEASURED BY ME: THE B1F TRAINING GROUND (STATIC ROM READ, 2026-09-17 late)

Ran the `ch23route` R15 procedure (`story_harness.py:12792-12811`) against `VICTORY_ROAD_B1F`:
`get_map_data(MapRSE.VICTORY_ROAD_B1F, (x,y))` per candidate, reading `tile_type`, `elevation`,
`collision` and `has_encounters`.

| tile | type | elev | collision | encounters | verdict |
|---|---|---|---|---|---|
| `(9,3)` `(7,3)` `(8,4)` **`(9,4)`** `(7,4)` `(9,5)` `(10,4)` `(6,4)` | **Cave** | 3 | 0 | **True** | ✅ usable |
| `(8,5)` | Normal | 0 | **1** | False | ⛔ WALL — cannot be stood on |

⭐ **THE 1F TRAP DOES NOT EXIST HERE, AND THAT IS THE USEFUL RESULT.** On 1F, *"16 walkable tiles are
`MB_NORMAL`, and a spin parked on one of those generates ZERO battles while looking perfectly healthy"*
(`victory_road.py:474-476` — `#24-grindconverge`'s shape). Around B1F's arrival, **every walkable tile
measured is `Cave`**; the only `Normal` tile found is a WALL, so it cannot be parked on by accident.

⚠ **THE REAL B1F HAZARD IS THE WARP, NOT A DEAD TILE.** `(8,3)` is the ladder back to 1F
(`warp[4] (8,3) -> VICTORY_ROAD_1F (9,14)`, read from the ROM). A spin that steps onto it leaves the
floor. ⇒ prefer a candidate **not cardinally adjacent to `(8,3)`** — `(9,4)`, `(7,4)`, `(9,5)`,
`(10,4)` and `(6,4)` all qualify; `(9,3)` and `(7,3)` do not.

### ⭐ THE FIVE B1F TRAINERS, LOCATED — AND THE CANDIDATES ARE CLEAR OF ALL OF THEM

`victory_road.py:2345` warns *"B1F carries a trainer and wild encounters, and this is how a run whites
out underground."* ✅ **CONFIRMED AND MADE PRECISE — there are FIVE**, read from both
`mapfacts.py` and the decomp's `data/maps/VictoryRoad_B1F/map.json` (21 object events: 8 Strength
boulders, 6 Rock Smash rocks, 5 trainers, 2 items):

| trainer | tile | sight radius |
|---|---|---|
| Michelle | `(5,21)` | 2 |
| Mitchell | `(14,16)` | 4 |
| Halle | `(14,20)` | 3 |
| Shannon | `(26,16)` | 4 |
| Samuel | `(37,12)` | 3 |

⇒ **the nearest trainer to ANY usable candidate is 16 manhattan tiles away** (Mitchell, from `(9,5)`
or `(10,4)`), against sight radii of 2–4. **The grind corner is comfortably outside every sight line.**
⚠ Sight lines are directional and this is a manhattan bound, not a ray-cast — but a 4× margin over the
largest radius makes a sight-line trigger implausible rather than merely unlikely.

⛔ **CAVEATS ON ALL OF THE ABOVE.** (1) **STATIC ROM read** — on a layout-swapped map the static view
lies (KI-74); B1F is not known to be one, but **confirm live before code depends on it**. (2) The
boulders at `(4,7)` and `(9,10)` are near the arrival and the puzzle **resets on every warp**
(`B1F_PUZZLE_RESETS_ON_WARP = True`), so their positions on arrival are the ROM defaults — do not
assume a solved state. (3) None of this prices the **heal round-trip**, which remains the open
question for `#24-levelgap`.
