# Hunting, Living Dex, Obtainability & Watchdog
> Custom-fork feature docs — intent first, then how it works. These were
> promoted 2026-07-19. Upstream (unmodified) mechanics they build on are in
> `../../40cakes repo/DOCUMENTATION/`.

## Why these exist
The stock bot hunts a single spot in a single mode. These features turn it
into a goal-driven, mostly-hands-off tool: tell it a target (or "complete
the dex") and it figures out *where* to hunt, *how* to get there, *what* is
even obtainable, catches opportunistically, and recovers itself if it gets
stuck on a 24/7 run.

---

## Hunt Planner (`Hunt` tab)
**Intent:** "I want species X" → the bot tells you the best place and mode,
and can go hunt it in one click.

- **`modules/encounter_index.py`** reads every map's wild-encounter tables
  straight from the ROM (headless, cached per-ROM in `cache/`) and inverts
  them into *species → [{map, method, rate%, level range}]*, ranked best
  first. `find_encounter_tile(map)` locates a real grass/water/fishing tile
  to stand on.
- **`plugins/custom_modes/hunt_mode.py`** ("Hunt (Custom)") sets the target,
  navigates there via the global pathfinder, and starts the right hunting
  behavior (spin for grass/surf, fish for rods).
- **GUI:** pick a target with the sprite picker → a ranked location list +
  recommended mode → "Hunt" travels and hunts.
- **Honest limit:** actually walking the route needs a real save; Rock Smash
  has no auto-tile finder (manual positioning).

## Living-Dex Orchestrator (`Living Dex` panel in the Hunt tab)
**Intent:** the "ultimate idle" — complete the Pokédex hands-off.

- Derives a target list of **uncaught + obtainable** species (from your live
  Pokédex flags × the obtainability model below).
- **Opportunistic (#43):** the target only *drives travel*; it catches ANY
  wanted-uncaught species it meets en route, so it fills the dex fast.
- **Shiny-safe (#47):** it also catches a **shiny even of an already-owned
  species** — never miss a shiny.
- Advances by reading the live dex (a failed/fled catch just stays wanted),
  and stops cleanly when the list is exhausted or boxes are full.

## Obtainability model — the honest Pokédex reality
**Intent:** never send the bot chasing something it can't catch, and be
honest about what a "living Emerald dex" actually is.

- **`modules/obtainability.py` + `modules/data/emerald_obtainability.json`**
  classify all 386 species: **wild 132 / evolution 149 / gift 7 / static 8 /
  roamer 2 (Latias+Latios, both obtainable) / event 6 / breeding 3 /
  special 1 / unobtainable 79** (sums to 386, fact-checked against the ROM's
  own wild tables + the bot's reset-mode seeds).
- **Two denominators, shown honestly:** `N / 386 National Dex` AND
  `218 / 386 obtainable in Emerald without trading`. ~79 Gen-3 species
  simply cannot be obtained in Emerald alone (they need a trade from
  FR/LG/RS) — the dex marks these rather than hunting them forever.
- Living-dex planning uses this: wild → hunt; evolution → hunt the base and
  evolve; gift/static/roamer → routed to the reset modes; trade/event/
  unobtainable → flagged "manual / trade required".

## Capability gating
**Intent:** don't target a place you can't get to yet.

- **`modules/capabilities.py`** reads the save for owned **HMs, fishing rods,
  and badges** and answers `can_use_method(...)` (Surfing needs Surf + the
  Balance Badge; each rod needs its key item; Rock Smash needs the move +
  Dynamo Badge; grass is always fine). Targets needing a capability you lack
  are **deferred with a reason** ("needs Super Rod").
- **Deferred to a future round:** full map reachability through Cut-trees /
  HM-gated tiles (`navigate_to_anywhere` currently models warps only).

## Analytics (`Stats` tab → ANALYTICS card)
**Intent:** shiny hunters want to see their luck and history.
- **`modules/analytics.py`**: a luck meter (actual shinies vs binomial
  expectation at 1/8192, with σ / z-score / verdict), an encounter-rate
  sparkline, and a sortable/filterable per-species stats browser with
  sprites — all live from `stats.db`.

## Catch-ball allowlist (`Hunt` tab → CATCH BALLS card)
**Intent:** don't let the bot burn your Master Ball.
- **`modules/catch_balls.py` + `catch_balls.yml`**: a checkbox per ball type;
  the catch logic (`battle_strategies/catch.py`) only throws allowed balls.
  Master Ball is excluded by default.

## Watchdog / auto-recovery
**Intent:** make 24/7 unattended hunting trustworthy.
- **`modules/watchdog.py` + `plugins/watchdog_plugin.py` + `watchdog.yml`**:
  detects encounter-stall, an unexpected drop-to-Manual (crash), and
  frame-freeze; runs a bounded recovery ladder (re-assert mode → reload a
  healthy savestate with a safety backup first, overworld-gated → give up to
  Manual + alert after max attempts). Never corrupts a save; never loops on
  a broken state. Status shows in the Stats tab.

## Move learning (behavior note)
Per #39, the bot **declines** new moves by default (`battle.yml new_move:
cancel`) so a level-up never interrupts a hunt. The decision point
(`DefaultBattleStrategy.which_move_should_be_replaced`) has a `learn_best`
seam for future intelligent move evaluation and for the planned story mode
(which will want good movesets).
