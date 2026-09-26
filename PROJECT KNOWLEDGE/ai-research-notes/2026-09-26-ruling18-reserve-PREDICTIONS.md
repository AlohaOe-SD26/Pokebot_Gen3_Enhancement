# 2026-09-26 — USER RULING 18 (buy the League basket early + reserve it) — PREDICTIONS, filed BEFORE any drive

> Build: `sandbox-pokebot/modules/story/league_reserve.py` — the purchase `stock_basket_early` (called from §Ch22 L1 via
> the new `sootopolis_gym.heal_and_stock_before_the_gym`: heal → buy → re-heal if the trip walked → gym) and the
> reserve `filter_medicine_for_reserve` (one guarded call in `StoryItemBattleStrategy._maybe_use_item`, before
> `options`). Recon (3 agents, NOTES): decomp mart facts; an audit of our spend/use points; an adversarial
> "how this backfires" pass whose 12 scenarios shaped the design (reserve ONLY in the battle strategy; state-derived
> release; fail unlocked; fail-open purchase verified by bag delta; buy before the gym, re-heal after).
> ⚠ SCOPE READING (mine, flagged to the user): the ruling said "locked so gym battles cannot spend it"; the reserve
> holds for every trainer battle until the Elite Four — the recon found 0 items spent on Juan in every log, so a
> gym-only lock would protect nothing. Today's bot carries no Hyper Potions past Sootopolis, so the reserve
> reproduces today's fights exactly.

## FIXTURE FACTS (observe-only, `probe_reserve_inputs.py`)
`post_hm07` (`bc3686118ac7`): SOOTOPOLIS_CITY (31,34), ₽67,466, badges 1-7, `SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` set, basket
lines 0/0/0 ⇒ reserve ON, plan `[Revive 3, Full Heal 8, Hyper Potion 30]` = ₽45,300 → leaves ₽22,166.
`post_badge8`: in Sootopolis, badge 8 ⇒ purchase OUT OF ERA, reserve ON. `post_phoebe_L75`: PHOEBES_ROOM, ENTERED set,
sealed ⇒ reserve OFF, bag Hyper 36 / FR 3 / FH 18 / Revive 3. `post_mtpyre`: pre-era ⇒ OFF. `post_league_shop`: ON.
`post_hof_cleared`: champion ⇒ OFF.

## PURCHASE ARMS — `--driver earlybasket` (§Ch22 L1 exactly)

| arm | how | predicted reading | falsifier |
|---|---|---|---|
| **E1 BUY** | `post_hm07`, `EB_SAVE_AFTER=<scratch>` | PASS: `EB-PLANNED, EB-MART, EB-BOUGHT`; bag delta = {Revive 3, Full Heal 8, Hyper Potion 30}; ₽67,466 → **₽22,166**; walked; re-healed (party full); ends on SOOTOPOLIS_CITY_GYM_1F | the Mart stand (3,3)/Left is wrong for Sootopolis (`shop_menu_open False` — it is `LAYOUT_MART`, unverified live here); the crater crossing fails to plan (layout pin); a delta ≠ plan |
| **E2 VACUITY (own output)** | E1's after-purchase state, `EB_EXPECT=buy` | `PREMISE FAILED` (plan empty) ⇒ FAIL | a PASS |
| **E2b** | same state, `EB_EXPECT=nothing` | PASS: "nothing missing", no walk, money unchanged, gym 1F | it walks to the Mart again |
| **E3 ERA** | `post_badge8`, `EB_EXPECT=skip` | PASS: "out of era", no move, no spend | it shops after badge 8 |
| **E4 PARTIAL** | `post_hm07`, `POKEBOT_RESERVE_FAULT_FLOOR=60000`, `EB_EXPECT=partial` | PASS: plan `[Revive 3, Full Heal 4]` (budget ₽7,466: 4,500 + 2,400), ₽67,466 → ₽60,566 ≥ floor, cheapest-to-leak prefix, gym 1F | Hyper Potion bought before the cheaper lines, or the floor broken |
| **E5 NOBUY** | `post_hm07`, `POKEBOT_RESERVE_FAULT_NOBUY=1`, `EB_EXPECT=nobuy` | PASS: "fault NOBUY", no walk, money unchanged, party full, gym 1F — L1 behaves exactly as before the ruling | L1 fails without the purchase |

## RESERVE ARMS — `--driver ch24glacia` on `post_phoebe_L75` (a real trainer battle that spends a Hyper Potion)
In-battle spend = `heal_bag_after` (after the pre-fight between-room heal, which the reserve does NOT touch) −
`bag_after_glacia`. The 2026-09-17 TREATMENT spent **1 Hyper Potion** in the fight (36 → 35).

| arm | env | predicted | falsifier |
|---|---|---|---|
| **V1 BASELINE** | — (sealed map ⇒ reserve OFF) | in-battle spend ≥ 1 Hyper Potion (items used as today) | spend 0 ⇒ the release on a sealed map is broken (the Elite Four would fight without items) |
| **V2 NOLOCK** | `POKEBOT_RESERVE_FAULT_NOLOCK=1` | IDENTICAL to V1 (bag lines, outcome, frames) — one trajectory, replayed: on a sealed map the reserve contributes nothing | any difference |
| **V3 FORCEON** | `POKEBOT_RESERVE_FAULT_FORCEON=1` | in-battle spend of EVERY basket line = **0** (the filter sits on the real battle path); a "reserve holding back" RESERVE event; the fight's outcome is NOT graded | any basket item spent in the fight |
| **V4 RAISE** | `POKEBOT_RESERVE_FAULT_RAISE=1` | IDENTICAL item use to V1 — fail UNLOCKED | spend 0 (a broken reserve disabled item use — the exact historical shape) |

**G** `probe_league_reserve.py` — PASS with its six built-in fault arms red (already run while building; re-run with
the suite).

## WHAT THESE DRIVES CANNOT SETTLE
* Whether buying early leaves enough money for leg 11's Full Restores after Victory Road — the next organic batch's
  `[MONEY]` / `EARLY_BASKET` lines will say.
* The reserve's effect in its REAL scope (Juan, Victory Road trainers) — those fights have never spent a Hyper Potion
  because none was carried; the Glacia arms prove the mechanism, not its value.
* A bag with too few free ITEMS slots (the shop's "no more room" branch) — no fixture; the bag-delta check reports it
  as `partial` rather than claiming success.

## ADDENDUM 1 — E1 FAILED as its pre-registered falsifier said; fix filed BEFORE the re-drive

**E1 (as first built): `ACCEPTANCE: FAIL`** — `failed open: UnreachableDestinationError: Could not reach (3, 3) on
SOOTOPOLIS_CITY_MART … still at (43, 32) … Could not find a path from (43/32 @ SOOTOPOLIS_CITY)`. Nothing bought,
nothing lost: re-healed, entered the gym, `no_failure True` — the fail-open design held. The falsifier "the crater
crossing fails to plan" fired, but NOT for the layout reason I named: the pin reported the same blockdata before and
after.
**Diagnosis (observe-only probe, fresh process, `post_hm07`):** `(31,34)→(17,29)` OK 23, `(43,32)→(17,30)` OK 40 —
because the probe starts at (31,34), where only objects 7 and 18 are live. `calculate_path` (`map_path.py:806-852`)
blocks the TEMPLATE tile of any object it cannot currently see; `get_map_objects()` is a camera window. Object 7's
template is **(20,36), on the path's land bridge west**, but a script moved it to (29,33). From (31,34) it is in view
(template ignored); from (43,32) it is not (bridge "blocked") ⇒ no path.
**Fix:** walk to `SOOTOPOLIS_MART_WAYPOINT = (31,34)` first (the fixture's own start tile; proven reachable from the PC
in the same run), then to the Mart.

| arm | predicted | falsifier |
|---|---|---|
| **E1' BUY (re-drive)** | as E1 was predicted: PASS, delta {Revive 3, Full Heal 8, Hyper Potion 30}, ₽67,466 → ₽22,166, `waypoint_reached` ((0,7),(31,34)), re-healed, gym 1F | still no path from (31,34) (then object visibility is not the cause) |

## ADDENDUM 2 — E1' half-worked; the second half of the same defect; fix filed BEFORE the next drive

**E1' (waypoint only): `ACCEPTANCE: FAIL`, but the PURCHASE LANDED exactly as predicted** — bag delta {Revive 3,
Full Heal 8, Hyper Potion 30}, ₽67,466 → **₽22,166**. It then failed on the way BACK: the re-heal raised
`HealWalkFailedError: … the walk to SootopolisCity is BLOCKED` from the Mart. The same camera-window blocker, in
reverse: from the Mart side object 7 is out of view, so the planner blocks the bridge and finds no path east.
⚠ **This is the dangerous half:** a bot on the Mart side with no plannable way back fails every attempt's pre-gym heal
— a stranded run. My first fix covered one direction of a symmetric problem.
**Fix:** at the waypoint (where the planner sees the object) plan BOTH legs before crossing — if either fails, do not
cross; after shopping, walk back along the path PLANNED FROM THE PC SIDE (`return_across_from_the_mart`: resumes from
wherever on the stored path we stand, bounded; the planner only as an off-path last resort); the walk back runs
OUTSIDE the shop's try (a shop error or a partial purchase still returns), and an expired budget triggers one more
bounded walk back. Gate `probe_league_reserve.py` R7 pins all of it (two new fault arms).

| arm | predicted | falsifier |
|---|---|---|
| **E1'' BUY** | PASS: `EB-PLANNED, EB-MART, EB-BOUGHT`; delta {Revive 3, Full Heal 8, Hyper Potion 30}; ₽67,466 → ₽22,166; `returned True` via the stored path (no `return_errors`); re-healed; gym 1F | the stored path times out and cannot resume, or the re-heal still reports BLOCKED from (31,34) |
