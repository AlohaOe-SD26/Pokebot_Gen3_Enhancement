# 2026-09-26 — `#26-carleestage` — PREDICTIONS GRADED (all six CONFIRMED)

> Grades `2026-09-26-ch23-carleestage-PREDICTIONS.md` (committed `71f68287`, BEFORE any drive).
> Evidence, committed: `tools/story-dev/evidence/2026-09-26-ch23stage-{NOFIX,FIX,FULL}.txt` and the
> matching `.stdout-excerpt.txt` files. Instrument: `--driver ch23stage` from
> `post_depart_sootopolis.ss1` (md5 `5e1652cbea94`, asserted with `verify_fixtures.py` first).

## The runs

| arm | offsets | env | result line |
|---|---|---|---|
| NOFIX (skip-the-fix) | 0-47, step 13 | `POKEBOT_CH23_FAULT_NOSTAGEFIX=1` | `signature_k=[10, 14, 18, 25, 28, 41] accepted_k=[] other_raise_k=[]` · 48/48 reached ROUTE128 |
| FIX | 0-47, step 13 | — | `signature_k=[] accepted_k=[10, 14, 18, 25, 28, 41] other_raise_k=[]` · 48/48 reached ROUTE128 |
| FULL (fix) | 0, 10, 14, 18, 25, 28, 41 | `CH23STAGE_FULL=1` | `full_leg_pass_k=[0, 10, 14, 18, 25, 28, 41]` · 0 whiteouts |

## Grades

| # | prediction | verdict | the reading it rests on |
|---|---|---|---|
| P1 | ≥1 offset reproduces the organic death under NOFIX | ✅ **CONFIRMED — 6 of 48 (12.5 %)** | NOFIX rows k=10,14,18,25,28,41: `raised UnreachableDestinationError: Could not reach (101, 26) …`, end `(101, 25)` |
| P2 | the occupant is Carlee; Harrison at (101,24) | ✅ **CONFIRMED, all six** | objects `{9: (101, 26), 10: (101, 24)}` on every reproducing row; FIX `occupied_by=[(9, (101, 26))]` |
| P3 | the fix stages every reproducing offset at (101,25) | ✅ **CONFIRMED, 6/6** | FIX rows: `staged`, end `(101, 25)`, `accepted_at=(101, 25)` |
| P4 | reproducing offsets complete leg 4 with the fix | ✅ **CONFIRMED, 6/6 + the control** | FULL rows: `leg-complete`, end `((0, 8), (18, 42))` = `VR_APRON`, `grade={ended_above, on_apron, armed4, can_continue}` all True; 12,844-20,427 frames |
| P5 | non-reproducing offsets are BIT-IDENTICAL across arms | ✅ **CONFIRMED, 42/42** | per-k comparison of outcome, end tile, frame count and object positions: 42 identical, 0 different |
| P6 | no new failure mode under the fix | ✅ **CONFIRMED** | FIX `other_raise_k=[]`, FULL 0 whiteouts |

## What this does and does not establish

* ✅ The MECHANISM is the one hypothesised: a Carlee+Harrison double spot at (101,25) parks Carlee on
  the stage tile; and the fix removes exactly that death while changing nothing else on this fixture.
* ⚠ **12.5 % is NOT an organic rate.** 48 offsets replayed from ONE fixture are different RNG
  trajectories of ONE party on ONE approach (CLAUDE.md rule 8: they are not independent samples of
  organic play). The organic figure stays 9 of 39 badge-8 runs, from a different party mix.
* ⚠ **Fixing this alone mostly converts those runs into `#24-ch23training` refusals** (5 of the 9
  organic cases carried Marill L13). The organic payoff arrives only with that fix too.
* The adjacency rule is deliberately narrow (distance exactly 1, an object ON the stage). A stage
  refused for any other reason still raises — the 42 ordinary offsets show it is never consulted
  when staging succeeds.
