# §Ch24 EGRESS PROOF (`C-CANCONTINUE`) — GRADED

**Date:** 2026-09-25. Graded against `2026-09-25-ch24-egress-PREDICTIONS.md`, which was filed
**before** any of these four drives. **ALL FIVE PREDICTIONS HELD.**

## THE FOUR ARMS

| Arm | Command | Result |
|---|---|---|
| HAPPY v1 (hardcoded `(7,1)`) | `CH24_CHAMP_FROM=drake --driver ch24champion` | `ACCEPTANCE: PASS`, 15 readings, `egress_waypoints: 4` |
| FAULT v1 | `+ POKEBOT_CH24_FAULT_NOEGRESS=1` | `ACCEPTANCE: FAIL`, `missing=['C-CANCONTINUE']` |
| HAPPY v2 (**derived** target) | same as v1 | `ACCEPTANCE: PASS`, `egress_exits: [(7, 1)]`, `egress_reached: (7, 1)`, `egress_waypoints: 4`, `egress_refusals: []` |
| FAULT v2 | `+ POKEBOT_CH24_FAULT_NOEGRESS=1` | `ACCEPTANCE: FAIL`, `egress_fault_armed: True`, `egress_reached: None`, `missing=['C-CANCONTINUE']` |

## GRADE

| # | Prediction | Verdict |
|---|---|---|
| P1 | all ELEVEN champion readings, `C-CANCONTINUE` included | ✅ HELD (both happy arms) |
| P2 | `egress_waypoints` a small positive integer (3–8) | ✅ HELD — **4** |
| P3 | the fault arm FAILS with `C-CANCONTINUE` missing | ✅ HELD (both fault arms) |
| P4 | it fails **at the egress check specifically** — `C-USABLE` still taken | ✅ HELD — `C-USABLE` is in `readings` on both fault arms; only `C-CANCONTINUE` is missing |
| P5 | the positive map assert does not break `C-HOME` | ✅ HELD |

## ⭐⭐ THE RESULT WORTH KEEPING: THREE INDEPENDENT METHODS AGREE ON `(7,1)` AND ON `4`

1. **Our own repo** — `early_game.py:75  HOUSE_2F_STAIRS_DOWN = (7, 1)`, walked by the intro every run.
2. **The decomp** — `LittlerootTown_BrendansHouse_2F/map.json` declares exactly ONE warp event at
   `(7,1)`, and decoding the map binary gives `(4,2)→E→E→E→(7,2)→N→(7,1)` = **4 steps**.
3. **The live ROM at runtime** — `egress_exits: [(7, 1)]` (read off the map's warp table) and
   `egress_waypoints: 4` from `calculate_path`.

‼ Agreement between agents is NOT a confidence signal (measured, and it is a standing rule here) —
but agreement between a STATIC decode, a LIVE read and an EXISTING CONSTANT is three different
*instruments*, not three guesses. That is the kind of agreement worth recording.

## ⛔ A BUG CAUGHT BEFORE IT SHIPPED — AND THE RULE THAT CAUGHT IT

The first implementation hardcoded `HOME_MAP = BRENDANS_HOUSE_2F` and `HOME_STAIRS = (7,1)`.
**Gender is CONFIGURABLE** (`profiles/*/story.yml` documents `gender: "boy" or "girl"`;
`story_mode.py:4059` passes it to `run_intro`), and a GIRL save resumes in `MAYS_HOUSE_2F`
(`MapRSE...MAYS_HOUSE_2F.value == (1, 3)`, confirmed in our own `map_data.py`). On a girl profile the
positive map assert would have made `_settled()` **never return True**, timing out a run that had
just cleared the game. Every profile in the repo is `boy`, so it was LATENT — which is the kind that
ships. ⇒ the target is now **derived from the live map's warp table**, which is the project's own
standing rule: *"a liveness check must derive its target from the state the run ACTUALLY reached,
and must hardcode no coordinates."* The decomp-derived `(7,1)` is kept only as telemetry
(`egress_expected_male_stairs`), never as the target.

✅ **THE (4,2) CAVEAT IS NOW CLOSED — VERIFIED AGAINST THE DECOMP, TWICE, INDEPENDENTLY.** I first filed `HOME_TILE = (4,2)` as UNVERIFIED for May's bedroom (this repo carries no heal-location data). A TIER 1 reviewer then fetched the decomp itself, and I repeated the fetch: `gh api repos/pret/pokeemerald/contents/src/data/heal_locations.json` returns `HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F` **and** `..._MAYS_HOUSE_2F` BOTH at `x:4, y:2`. ⇒ the settle conjunct is correct on either gender.

⚠ **WHAT REMAINS IS A DRIVE, NOT A DOUBT.** No `gender: girl` profile exists, so the girl path rests on derived + decomp reasoning and has never been RUN. Cheap to close whenever a girl profile is added: `--driver ch24champion` from a girl fixture, checking `C-CANCONTINUE` still passes and `egress_exits` resolves against MAY'S own warp table. ‼ Note that May's STAIRS were never verified and never needed to be — the egress target is read from the live map, which is exactly why deriving beat naming.

## ⛔⛔ STILL OPEN — AND MORE EXPENSIVE THAN IT LOOKS

**The training leg at production `floor=65` has never been driven as part of this chain.** The
gauntlet PASS ran at `CH24_ENTRY_FLOOR=1`, which no-ops `train_for_league` (`latch_calls=2` rather
than 3 is the fingerprint).
‼ **AND THE CHEAP FIX DOES NOT EXIST — MEASURED, not assumed.** Re-running the gauntlet at 65 from
`post_ch24_atdoor_L75.ss1` will NOT be a fast no-op: that fixture's party is
`Mightyena L75 | Zigzagoon L19 | Sceptile L75 | Swellow L75 | Wailord L75 | Castform L36`, so
`ch24_trainees_below_floor(65)` returns **Zigzagoon AND Castform** — and its docstring names exactly
those two as the trainees. A floor-65 chain run would grind L19 and L36 up to L65: **hours**.
⇒ **THE CHEAP SEAM TEST IS `CH24_ENTRY_FLOOR=20`**: only Zigzagoon (L19) falls below it, so
`train_for_league` executes and does REAL work (L19→L20) inside the chain, proving the readiness
branch RUNS AND HANDS OFF. That proves the SEAM, not the MAGNITUDE — say it that way, and do not
let a floor-20 pass be written up as "the chain works at production settings".

## ⚠ WHAT THIS STILL DOES NOT PROVE

It proves a PATH EXISTS, not that the bot walks it. Actually leaving (stairs → 1F → front door →
Littleroot) belongs to the dex-hunt chapter — and `2026-09-25-post-hof-littleroot-MEASURED.md`
records the trap waiting there: **1F has an `OnFrame` script that fires on arrival**, `lockall`s,
MOVES the player and hands over the SS Ticket. Budget for it; do not navigate during it.
