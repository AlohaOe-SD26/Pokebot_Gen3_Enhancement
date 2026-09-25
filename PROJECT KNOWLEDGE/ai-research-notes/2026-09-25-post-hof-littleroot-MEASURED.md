# WHERE THE BOT LANDS AFTER THE HALL OF FAME — and how it gets out

**Date:** 2026-09-25. **Source:** a Claude decomp agent reading `pret/pokeemerald`, **plus my own
verification of every load-bearing claim** (marked ✅ below). **Status:** this is a NOTE. The
authoritative docs win on any contradiction until a claim is verified here.

⭐ **WHY THIS NOTE EXISTS.** §Ch24 ends in the player's BEDROOM. The next chapter (dex hunting)
begins by walking out of it. Getting this wrong costs live emulator drives, so it was researched
BEFORE anything was built.

---

## ✅ VERIFIED BY ME, IN THIS REPO OR ON A LIVE RUN

| Claim | How I verified it |
|---|---|
| The landing is `LITTLEROOT_TOWN_BRENDANS_HOUSE_2F` map `(1,1)`, tile **`(4,2)`** | MEASURED live: `usable_at`/`end_at` in `evidence/2026-09-25-ch24gauntlet-PASS.txt` AND `-ch24egress-HAPPY.log`. |
| Brendan's stairs are **`(7,1)`** | Matches our own `early_game.py:75 HOUSE_2F_STAIRS_DOWN = (7, 1)` (used by the intro every run) **and** the decomp's `map.json` warp_events. |
| The route is **4 steps** | ⭐ TWO INDEPENDENT METHODS AGREE: the decomp decoded the map binary to `(4,2)→E→E→E→(7,2)→N→(7,1)` = 4; the LIVE pathfinder returned `egress_waypoints: 4`. |
| A girl save lands in a DIFFERENT map, `MAYS_HOUSE_2F` = **`(1,3)`** | `MapRSE.LITTLEROOT_TOWN_MAYS_HOUSE_2F.value == (1, 3)` in our own `modules/map_data.py`. |
| Gender is CONFIGURABLE | `profiles/*/story.yml` documents `gender: "boy" or "girl"`; `story_mode.py:4059` passes `cfg.gender` to `run_intro`. All current profiles are `boy`. |
| `calculate_path` reaches a warp tile as a DESTINATION | The live probe pathed to `(7,1)`, a warp, and returned 4 waypoints — it stopped AT the door rather than following it through to 1F. |

## ⚠ FROM THE DECOMP, NOT INDEPENDENTLY VERIFIED BY ME — treat as leads

* `(4,2)` is plain floor (`MB_NORMAL`), **not the bed**; the bed is the furniture at x=0..2, y=3..5.
* Row `y=2` is walkable end to end; `(6,1)` and `(8,1)` are solid, so `(7,1)` is enterable **only
  from `(7,2)` heading north**. ⇒ for TRAVERSAL: route to `(7,2)`, then one NORTH step; treat
  `(7,1)` as terminal and never route *through* it.
* `(7,1)` is `MB_NON_ANIMATED_DOOR` — a **step-on** warp. **Not** an arrow warp (no held direction
  needed) and **not** an animated door warp.
* `LittlerootTown_BrendansHouse_2F` has **no `MAP_SCRIPT_ON_FRAME_TABLE`**, so nothing on 2F can
  `lockall` or move the player on the first post-credits frame.
* Mom and the rival both have object templates AT `(7,1)`, and **both are hidden**: the rival's
  hide-flag is `setflag`-ed by the Hall-of-Fame script itself, and Mom's is set in `new_game.inc`
  and *never cleared anywhere in the repo*. ⇒ no NPC can block those stairs.

## ⛔⛔ TWO FORWARD TRAPS FOR THE DEX-HUNT CHAPTER — DO NOT LEARN THESE BY DRIVING

1. **THE BIG POST-GAME CUTSCENE IS DOWNSTAIRS, NOT IN THE BEDROOM.**
   `LittlerootTown_BrendansHouse_1F_OnFrame` carries
   `PlayersHouse_1F_EventScript_GetSSTicketAndSeeLatiTV`, armed because the Hall-of-Fame script sets
   `VAR_LITTLEROOT_HOUSES_STATE_*` to 3 and clears `FLAG_HIDE_PLAYERS_HOUSE_DAD`. On the frame the
   bot arrives on 1F it hits `lockall`, **the script MOVES the player**, hands over `ITEM_SS_TICKET`
   and sets `FLAG_RECEIVED_SS_TICKET`. ⇒ **budget for a scripted scene on 1F, not on 2F**, and do
   NOT navigate during it (a moving player fights the pathfinder — the documented §Ch-intro trap).

2. **`continueGameWarp` IS CONSUMED EXACTLY ONCE.**
   `CB2_ContinueSavedGame` calls `ClearContinueGameWarpStatus()`. A SECOND CONTINUE resumes from
   the saved `location`/`pos` — **wherever the Hall-of-Fame save was taken, NOT the bedroom.**
   ⇒ ‼ If we ever capture a post-game FIXTURE, capture it AFTER the reboot has landed in the
   bedroom. A fixture taken at the HoF save point will land somewhere else on its second load, and
   would silently invalidate every drive that used it.

3. ⚠ The credits end in a **genuine `SoftReset(RESET_ALL)`** to the title screen — the bot must
   drive the CONTINUE menu. Our leg already survives this (`C-REBOOTED` observes the empty party
   during the EWRAM wipe), but anything that assumes in-memory continuity across the credits is
   wrong.

## ⚠ UNVERIFIED AND DELIBERATELY NOT RELIED ON

* May's bedroom layout. The decomp says it shares the 9×8 dimensions but **did not decode its
  map binary**, so `(7,1)` is NOT confirmed there. ⇒ this is exactly why `fight_the_champion` now
  **derives** its egress target from the live map's warp table instead of naming a tile.
* Whether a player-placed decoration can be solid. Moot for this route — every decoration-capable
  tile is at `y >= 3`, and the corridor is `y == 2`.
