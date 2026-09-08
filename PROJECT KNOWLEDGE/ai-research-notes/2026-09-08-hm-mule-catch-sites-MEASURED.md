# HM MULE CATCH SITES — MEASURED OVER 822 PRODUCTION LOGS (2026-09-08)

⛔ **AGENT OUTPUT — A NOTE, NOT TRUTH.** Read `00-READ-THIS-FIRST.md`. Where I verified something
myself it says **[I VERIFIED]**; everything else is the agent's measurement and is unconfirmed by our
harness. On any contradiction the authoritative doc wins.

⭐ WHY IT MATTERS: it prices `#24-lowlevelmules` and it KILLS "train the mule at catch time" for
Surf **by geography, not by cost**.

## THE THREE CATCH SITES (there are three, not five)
`ensure_hm_learner` has exactly three production call sites: **HM06 Rock Smash** (§Ch10b, post-Gym 3,
from Mauville), **HM03 Surf** (§Ch12c, post-Gym 5, from Petalburg), **HM08 Dive** (§Ch19b, post Space
Center, from Mossdeep). ⛔ Strength and Waterfall never catch — `ensure_strength_learner` and
`ensure_waterfall_learner` RAISE instead.

## THE MEASURED TABLE (team levels parsed from 822 real logs, not assumed)
```
catch site   HM          local wild band        team level (measured)   GAP   battles to close
ROUTE103     Surf        L2-4                   L31-43, median 36       ~33   1,850
ROUTE101     Surf        L2-3                   L32-40, median 35       ~34   2,430
ROUTE119     Surf        L24-27  ⛔ MIRAGE       median 36               ~11   87
ROUTE117     Dive        L13 (Marill 10%)       L43-54, median 49       ~36   588
ROUTE117     Rock Smash  L13-14                 L22-24                  ~11   74
```

## ⛔⛔ THE ROUTE119 ROW IS A MIRAGE, AND IT COST 615 HUNTS
`#24-hmgroundwatertiles` records that `ROUTE119 (21,109)` and `ROUTE118 (29,15)` are **Ocean Water
tiles** where only the SURF table fires — but `_hm_hunting_grounds` priced them off the **land**
table. ⇒ **615 of the 822 logs spun their full 40,000-frame hunt budget meeting Tentacool/Wingull.**
The EFFECTIVE Surf catch band is therefore **L2-4**, not L24-27.

## ⭐ THE CIRCULAR DEPENDENCY THAT SETTLES THE SURF CASE
Pre-Surf, every grass hosting a higher-band Surf learner is gated: Routes 115/118/119/121 are
`AREA_PREREQ = "surf"`, Route 112 is in `NO_RETURN_GROUNDS`, Route 111 needs Go-Goggles, Route 114 is
unreachable. The best reachable is **Route 117 Marill L13** — 23 levels under a L36 team.
⇒ **The bot cannot reach a level-appropriate Surf-learner ground without the move it is trying to
acquire.** Catch-time training for Surf is impossible by GEOGRAPHY, not by budget.

## AND "PICK A PARTY MEMBER INSTEAD" IS ALSO UNAVAILABLE AT §Ch12c
Measured over the observed hunt parties: **zero Surf learners**. Of the three starter lines only
Marshtomp/Swampert learns Surf. That is why this hunt is named the top non-finish cause in
`story_mode.py`.

## CORROBORATION — mules never level, at scale
Max level an HM mule EVER reached across ~400k heartbeat mentions: **Marill L15, Lotad L14,
Zigzagoon L23.** `FIXTURES.md5` shows the endpoint verbatim — *"Zigzagoon L19 … DELIBERATELY
untrained bench"*, with the harm recorded as observed: *"a cascade fed the L19 mule into a L40s
fight."*

## ⭐⭐ THE PROPOSED REAL FIX — UPSTREAM, AT CHAPTER 3 (HYPOTHESIS, flagged as architecture)
**Route 104 hosts Marill at 20%, L4-5, ON THE MANDATORY STORY PATH.** Measured team top level on
first arrival there: **L10-16, median L11** ⇒ a **6-7 level gap**, the smallest available anywhere in
the game for a water-HM carrier.
**[I VERIFIED] Marill's HM coverage from `modules/data/species.json`: Dive, Rock Smash, Strength,
Surf, Waterfall — ALL FIVE.** (Zigzagoon: Cut/Rock Smash/Surf. Lotad: Flash/Surf.)
⇒ acquiring a Marill at §Ch3, at team level, makes it a TEAM MEMBER rather than a mule — and the
§Ch12c Surf hunt and §Ch19b Dive hunt never fire at all.
⚠ UNVERIFIED BY ME: the Route 104 encounter rate/level and the arrival-level measurement. Check both
against `cache/encounter_index_BPEE0.json` before building.

## THE SECOND-BEST LEVER, ALREADY FILED
`#24-divegroundroute120` — Route 120 Marill 15% at **L25-27**, 379 waypoints, vs Route 117's 10% at
L13, 1,055 waypoints. **236 battles instead of 588.** ⚠ Blocked on one live sweep: all 436 Route 120
tiles are Long Grass and `spin()`'s behaviour there is undetermined.

## ⚠ CAVEAT THE AGENT RAISED ITSELF
`encounter_index.py` aggregates multiple slots of one species into a single min/max, so a wide band
like "Tentacool L5-35" is a UNION across slots, not a uniform range. Land tables are largely
unaffected; treat surf/rod figures as unions.
