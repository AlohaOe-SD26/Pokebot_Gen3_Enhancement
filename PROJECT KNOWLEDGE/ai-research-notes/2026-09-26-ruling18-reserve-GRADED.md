# 2026-09-26 — USER RULING 18 (early League basket + reserve) — GRADED: PASS AFTER TWO PRE-REGISTERED FAILURES AND A REVIEW KICK-BACK

> Grades `2026-09-26-ruling18-reserve-PREDICTIONS.md` (committed `d9287d39` BEFORE any drive; addendum 1 `f871f5a6` and
> addendum 2 `fde2c439` each committed after a failed drive and BEFORE the next one; addendum 3 `e0ae8baa`, the review's
> kick-back, BEFORE B1/B2). Evidence, committed: `tools/story-dev/evidence/2026-09-26-earlybasket-{E1-FAILED-NOPATH,
> E1b-STRANDED,E1c-BUY,E2-VACUITY-OWN-OUTPUT,E2b-OWN-OUTPUT-NOTHING,E3-ERA-BADGE8,E4-PARTIAL,E5-NOBUY,B1-BUDGET-BEFORE,
> B2-BUDGET-SHOP}.txt` and `2026-09-26-reserve-glacia-{V1-BASELINE,V2-NOLOCK,
> V3-FORCEON,V4-RAISE}.txt` (+ `.stdout.txt`). Fixtures asserted: `post_hm07` `bc3686118ac7`, `post_badge8`
> `723d94cc899f`, `post_phoebe_L75` `87d2fe61774a`. All drives `HARNESS_EXIT_ON_MANUAL=1`. Every passing arm was re-driven
> on the FINAL code for the committed evidence; frame counts below are from those runs (they differ run to run by a
> few thousand — a code change shifts frame timing and with it the random encounters; every conjunct was unchanged).

## THE PURCHASE — `--driver earlybasket` (§Ch22 L1 exactly)

| arm | prediction | reading | verdict |
|---|---|---|---|
| **E1** (as first built) | PASS | ❌ `failed open: … Could not find a path from (43/32 @ SOOTOPOLIS_CITY)` — nothing bought, nothing lost, still healed and entered the gym | ❌ its pre-registered falsifier fired (a planner failure) — **a RESULT**; cause below |
| **E1'** (waypoint (31,34) first) | PASS | ❌ **bought everything** (delta 3/8/30, ₽67,466 → ₽22,166), then the re-heal from the Mart raised `the walk to SootopolisCity is BLOCKED` — **a stranded run** | ❌ the same cause, reversed |
| **E1'' BUY** (round trip planned at the waypoint) | PASS: EB-PLANNED → EB-MART → EB-BOUGHT; delta {Revive 3, Full Heal 8, Hyper Potion 30}; ₽67,466 → ₽22,166; returned; re-healed; gym 1F | exactly that: `returned True` via the stored path in ONE attempt (`return_attempts [{from (17,30), …}]`); on the final code the walk back first pressed B ×8 to close the Mart menu and the clerk's goodbye (`close_presses 8`); crossing at 535 frames, shop open at 1,390, 10,329 frames in all (12,663 on the pre-review code), every conjunct True | ✅ |
| **E2 VACUITY (own output)** | FAIL on the premise | `PREMISE FAILED … plan=[]` ⇒ FAIL, 0 frames | ✅ |
| **E2b** | "nothing missing", no walk, no spend, gym 1F | exactly; 2,462 frames (the heal + the gym entry only) | ✅ |
| **E3 ERA** (`post_badge8`) | "out of era", no move | exactly, 0 frames | ✅ |
| **E4 PARTIAL** (`FLOOR=60000`) | `[Revive 3, Full Heal 4]`, ₽60,566 | exactly: delta 3/4/0, ₽67,466 → ₽60,566, cheapest-to-leak prefix, walked back, gym 1F (10,041 frames) | ✅ |
| **E5 NOBUY** | L1 unchanged without the purchase | "fault NOBUY", no walk, ₽67,466 kept, party full, gym 1F | ✅ |
| **B1 BUDGET-BEFORE** (`=300`) | expires before crossing; nothing to walk back; L1 completes | `finished False`, never crossed, ₽67,466 kept, re-healed, gym 1F (6,624 frames) | ✅ |
| **B2 BUDGET-SHOP** (`=1470`) | expires inside the Mart; the retry closes the menu and walks back | `finished False`, `crossed True`, cut after `frames_at_shop_open 1390` (the purchase did NOT complete — ₽67,466 kept), `close_presses 41`, `retry_return True` → `returned True`, `stranded False`, re-healed, gym 1F (7,902 frames) | ✅ the review's scenario, driven |

### WHY E1 AND E1' FAILED — A PLANNER TRAIT, MEASURED (filed as `KI-103`)
`calculate_path` blocks the ROM TEMPLATE tile of any object it cannot currently see (`map_path.py:806-852`), and
`get_map_objects()` is a camera window (KI-77). In Sootopolis after the crisis, `SootopolisCity/scripts.inc:116`
does `setobjectxyperm LOCALID_SOOTOPOLIS_STEVEN, 29, 33` — a PERMANENT move — while the ROM template still says
**(20,36), a tile on the only land bridge west**. From (31,34) he is in view and the bridge is open (probe: → Mart OK,
23 steps); from the PC front (43,32) or from the Mart side he is not, and the bridge reads as a wall ⇒ no path either
way. ⚠ KI-77 calls the template rule "fail-safe" because a pushed boulder respawns on its template; a
`setobjectxyperm` object never does, so here the over-block is permanent.
**The fix shipped** plans BOTH legs from (31,34) and refuses to cross if either fails; the walk back follows the
stored path (resuming mid-path; the planner only as an off-path last resort), runs outside the shop's try, and is
retried once if the budget expires on the far side. Gate R7 pins it.

## THE RESERVE — `--driver ch24glacia` on `post_phoebe_L75` (a real trainer battle that spends Hyper Potions)
In-battle spend = `heal_bag_after` − `bag_after_glacia` (the between-room heal is outside the reserve's scope).

| arm | prediction | reading | verdict |
|---|---|---|---|
| **V1 BASELINE** (sealed map ⇒ OFF) | spend ≥ 1 | **4 Hyper Potions** (36 → 32); Glacia beaten | ✅ the Elite Four keeps its items |
| **V2 NOLOCK** | identical to V1 | identical R lines, outcome and conjuncts (one trajectory, replayed) | ✅ on a sealed map the reserve contributes nothing |
| **V3 FORCEON** | spend 0 | **0** (36 → 36); Glacia still beaten, Wailord 99/396 instead of 272/396 | ✅ the filter sits on the path a real battle uses |
| **V4 RAISE** | identical item use to V1 | identical to V1 (4 spent) | ✅ fails UNLOCKED |

⚠ **NOT OBSERVED:** the predicted "reserve holding back" / "fail unlocked" RESERVE events — they go to the debug
logger, which harness runs do not enable. The bag readings above are the load-bearing evidence; the log lines will
appear in organic runs.

## CODE REVIEW (adversarial `reviewer`) — KICK-BACK, FIXED AND DRIVEN

* BLOCKER: "never strand the bot" was proven only statically. An expired budget `.close()`s the leg with
  `GeneratorExit` (not an `Exception`), skipping the in-function walk back; the outer retry had never run, would have
  waited for control with the Mart menu open, and fell back to the planner call that fails from the far side.
  FIXED: `POKEBOT_RESERVE_FAULT_BUDGET`; the walk back closes menus/dialogs first; off the stored path it tries the
  waypoint, then the Mart front (a west-side plan) so the stored path applies; still stranded ⇒ a NAMED error after
  the telemetry line. DRIVEN: B1 and B2 above. Gate R7 +2 checks.
* Risk (Full Restore reservation untested in the gate): R2 now asserts it.
* Risks noted, not changed: the "0 items on Juan" basis is 3 organic runs (the recon's sample); the planner's root
  cause is untouched (filed as `KI-103`).
* Ruled sound by the reviewer (its own traces): the filter's placement before both policies, fail-unlocked wiring,
  and a genuine whiteout (it teleports the player; `StoryAbort` handles it, not this module's retry).

## GATE — `probe_league_reserve.py`: PASS, eight built-in fault arms red
R1 (only in the battle strategy, before the policy, fail-unlocked; no bag reader sees it), R2 `apply_reserve`,
R3 state-derived arming + fail-unlocked, R4 `early_basket_plan`, R5 L1 wiring, R6 the six arms registered, R7 never
strand the bot on the Mart side (plan both legs first; walk back outside the shop's try; close menus first; retry
after an expired budget; a named error if still stranded). No false positive on a commented-out call.

## WHAT IT DOES NOT SETTLE
* Whether buying early leaves enough for leg 11's Full Restores after Victory Road — the next organic batch's
  `[MONEY]` / `EARLY_BASKET` lines will say.
* The reserve's value in its real scope (Juan, Victory Road trainers): those fights never had Hyper Potions to spend;
  V1-V4 prove the mechanism, not its value.
* A bag with no free ITEMS slot (the shop's "no more room") — no fixture; the bag-delta check reports it as `partial`.
* An organic arrival at Juan from training elsewhere, with the §Ch21 layout pinned in the same process — the leg
  re-pins from the live header before planning, but that combination has not been driven.
