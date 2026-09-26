# 2026-09-26 — `#26-ch24organic` GAP 2 (THE RETURN BRIDGE) — GRADED: ALL SEVEN ARMS + THE REGRESSION ARM AS PREDICTED (re-run after the code review)

> Grades `2026-09-26-ch24-bridge-PREDICTIONS.md` (committed `7cb5a759` on branch `wt/ch24organic` BEFORE any
> drive). Evidence, committed: `tools/story-dev/evidence/2026-09-26-ch24bridge-{T1-FLY-SOUTH,T2-FLY-VR1F,
> V-ALREADY,F1-NOFLYER,F2-WRONGTILE,NB-NOBRIDGE,W-WALK,RG-CH24BRIDGE}.txt` (+ `.stdout.txt`) — ⚠ the files are the
> RE-RUN on the post-review code (the first run's readings were identical for all seven arms). Fixtures verified first
> (`post_ch24ready` `cf383b5b2567`, `post_e4ice_FINAL` `ebfafa71fa99`, `post_vr_exit` `0ad243164fd6`,
> `post_league_shop` `1564948368f6`, `post_ever_grande` `18203e997edc`). All drives `HARNESS_EXIT_ON_MANUAL=1`.

| arm | prediction | reading | verdict |
|---|---|---|---|
| **T1** FLY-FROM-SOUTH | PASS; walk refused; fly (27,49) → (18,6); entry completes | `ACCEPTANCE: PASS`, `missing=[]`; `BRIDGE mode='fly' positioned=True start=((0, 8), (27, 49)) end=((0, 8), (18, 6))` | ✅ |
| **T2** FLY-FROM-VICTORY-ROAD | PASS; step-out, then fly → (18,6) | `ACCEPTANCE: PASS`; `start=((24, 43), (15, 39))` (VR1F), `stepped_out=True`, `end=((0, 8), (18, 6))` | ✅ |
| **V** ALREADY-THERE | PASS; `mode='already'`, no flight | `ACCEPTANCE: PASS`; `mode='already'`, `fly=None` | ✅ (vacuity) |
| **F1** NO-FLYER | PASS; refusal names BOTH missing preconditions | `§Ch24 bridge: cannot return to the League door from EVER_GRANDE_CITY (18, 42) — (18, 6) is not reachable on foot from here (PathFindingError …), and flying back is impossible: no party member knows Fly; the Pokémon League was never visited (LANDMARK_POKEMON_LEAGUE is unset).` — all conjuncts True | ✅ |
| **F2** WRONG-TILE | PASS; the flight lands elsewhere and the TILE assert fires | fly `moved=True` (**`fly_to_destination` accepted the landing**), then `expected to stand on EVER_GRANDE_CITY (18, 6) … but we are at LILYCOVE_CITY (24, 15)` | ✅ **the assert is live, and it is the only thing that caught it** |
| **NB** SKIP-THE-FIX | FAIL at GET INSIDE | `ACCEPTANCE: FAIL`; `UnreachableDestinationError: Could not reach (18, 6) on MapRSE.EVER_GRANDE_CITY: … we are still at (27, 49)`; `E1-INSIDE` absent | ✅ **the bridge is load-bearing** |
| **W** WALK | walk, positioned; FAIL only for `E1-READY` | `mode='walk'`, `plan_wp=36`, `walk_finished=True`, no `walk_refused`, `end=((0, 8), (18, 6))`; `missing=['E1-READY']` only | ✅ |
| **RG** REGRESSION (`--driver ch24bridge`, `post_ch24_atdoor_L75`) | PASS unchanged; bridge `already`; R1 passes | `ACCEPTANCE: PASS` — door, (9,1), Sidney BEATEN; `bridge.mode='already'`; `readiness_refusal=[]` | ✅ |
| **G** `probe_ch24_bridge.py` | PASS; its fault arms red | PASS (B1-B5); door-walk-before-bridge, renamed assert, a duplicate `RETURN_BRIDGE_READINGS`, an unbounded flight — each caught | ✅ |

## CODE REVIEW (adversarial `reviewer`) — KICK-BACK, then fixed and re-run

1. ⛔ **The new `BRIDGE_READINGS` was DEAD ON ARRIVAL**: `enter_the_league`'s constant of the same name is assigned
   later in the module and silently SHADOWED it, and the harness hardcoded `"B-POSITIONED"` instead of importing
   it. Renamed `RETURN_BRIDGE_READINGS`, imported by both drivers; gate **B5** now refuses any `*_READINGS` name
   assigned twice (fault arm: a second assignment turns it red). The grades were unaffected (they read the leg's
   own report), which is why no drive could have shown it.
2. The PROVEN chain that also calls `prepare_and_open_the_league` was not re-driven ⇒ arm **RG** (pre-registered
   `86ce6cad`): `--driver ch24bridge` on `post_ch24_atdoor_L75` — `ACCEPTANCE: PASS` (door → (9,1) → Sidney BEATEN),
   bridge `mode='already'`, `readiness_refusal=[]`.
3. Risk noted, docstring corrected: indoors is NOT walked out of — it ends in the named "Fly is illegal on this
   map" refusal (bounded, undriven).

## WHAT THIS SETTLES
* ✅ A party that ends §Ch24 training anywhere Fly can reach — the south half, Victory Road 1F, a route —
  now gets back to the League door, and the landing is proven by TILE (F2: the flight helper alone accepts a
  wrong landing). Without it (NB) the entry dies at GET INSIDE from (27,49), exactly as the recon predicted.
* ✅ A party that cannot get back is refused BY NAME before anything is attempted (F1).
* ✅ A party already at (18,6) pays nothing (V).

## WHAT IT DOES NOT SETTLE
* ⚠ One trajectory per arm (rule 8). Indoor starts (a Poké Center, League 2F) are handled only by the named
  "Fly is illegal on this map" refusal — not driven.
* ⚠ Organic parties still mostly LACK a flyer (13 of 30) and none is taught Fly in production — gaps 3 and 5.
  For them the bridge will refuse by name (F1's shape) unless they happen to end on the north plateau (W).
