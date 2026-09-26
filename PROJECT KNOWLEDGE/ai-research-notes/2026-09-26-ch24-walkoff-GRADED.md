# 2026-09-26 — `#26-ch24organic` GAP 4 (THE NO-FLY RETURN TICKET) — GRADED: BOTH ARMS AS PREDICTED (re-run on the rule narrowed by review)

> Grades `2026-09-26-ch24-walkoff-PREDICTIONS.md` (committed `adcae1fb` on branch `wt/ch24organic` BEFORE the drive).
> The defect was first OBSERVED with its prediction filed before the run (`evidence/2026-09-26-ch24gap4-OBSERVE-
> {PREDICTION,NOFLY-FLOOR50}.txt`, prediction confirmed). Evidence: `evidence/2026-09-26-ch24walkoff-{G4-FIXED,G4-SKIP}.txt`
> (+ `.stdout.txt`) — ⚠ RE-RUN on the narrowed rule (addendum `f8bbdb8e`). Fixture `post_league_shop.ss1` (`1564948368f6`),
> `--driver ch24handoff`, `NOFLYTEACH=1`, floor 50.

| arm | prediction | reading | verdict |
|---|---|---|---|
| **OBSERVE** (before the fix, `--driver ch24train`) | Wailord walks into VR1F's exit half and crashes on (15,39) | `UnreachableDestinationError: Could not reach (15, 39) on MapRSE.VICTORY_ROAD_1F … still at (39, 5)`; Zigzagoon/Castform `no_ground` | ✅ the defect is real |
| **G4** FIXED | no walk; `no_ground` ×5; R1 refuses at (18,6); door shut | `rungs=[]`, `no_ground` = all five, `end=((0, 8), (18, 6))`; `nobody can Fly and we stand on the League plateau — VICTORY_ROAD_1F (15, 39) is only reachable from here through Victory Road's EXIT half … Not walking {Wailord, Swellow, Mightyena} off the plateau`; `§Ch24 R1: REFUSING … 5 mōn below the L50 floor`; `ACCEPTANCE: PASS` | ✅ |
| **G4-SKIP** (`NOWALKCHECK=1`) | the old crash, inside the cave | `UnreachableDestinationError … (15, 39) … still at (39, 5)`; `final_at=((24, 43), (39, 5))` (VICTORY_ROAD_1F); `ACCEPTANCE: FAIL` | ✅ **the guard is load-bearing** |
| **G4-FLY** (= H1 of the gap-3 note) | unchanged with Fly | H1 PASS, bridge `mode='fly'` | ✅ |
| **G** `probe_ch24_bridge.py` B6 | the rule is exactly Victory Road + plateau + no Fly; controls NOT refused; no warp-blind check | PASS: VR1F on the plateau refused; GRANITE_CAVE_1F, FIERY_PATH, VR1F off-plateau, and anything with Fly NOT refused; fault arms (call removed; an over-eager rule) both red | ✅ |

## CODE REVIEW (adversarial `reviewer`) — KICK-BACK, then narrowed and re-run

The first guard asked `calculate_path(here → (ground, tile))`, which is **WARP-BLIND** (`map_path.py`: "not able to use
warps") — it refused VR1F for the wrong reason and would have refused every warp-gated ground (Granite Cave, Fiery
Path), the invisible-wrong-NO oracle the KI-24 user decision already rejected. The rule is now the measured case only
(`_plateau_walkoff_refused`); B6 unit-tests the grounds it must NOT refuse. Both arms re-run on it: identical outcomes.

## WHAT THIS SETTLES
* ✅ A party with no Fly no longer walks off the League plateau into a half of Victory Road it cannot train in: it
  stays at the door and R1 refuses BY NAME (who is below the floor), instead of an unnamed crash inside a cave that
  every derail re-entry repeats.

## WHAT IT DOES NOT SETTLE
* ⚠ Such a party still cannot train at all — gap 5 (flyer acquisition), or a grind tile in VR1F's EXIT half (not
  built: it needs a live tile dump), is what would let it climb.
* ⚠ "On the plateau" is a SAME-MAP `calculate_path` to (18,6) (reliable: no warps — §Ch23 leg 10's own check); in
  the lobby it is `_on_map(LEAGUE_1F)`. Other Victory Road floors are refused by name from the plateau too (conservative,
  undriven).
