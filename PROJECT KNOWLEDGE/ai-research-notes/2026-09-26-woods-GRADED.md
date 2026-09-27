# 2026-09-26 — `#26-destreachability` (Petalburg Woods member): GRADED

> Predictions: `2026-09-26-woods-PREDICTIONS.md` (`a754a99c`, BEFORE the drives). Evidence:
> `tools/story-dev/evidence/2026-09-26-woods-*`. Fixture `flannery_done.ss1` (unpinned; md5 `61e90c57…` at both drives).

| # | Result | vs prediction |
|---|---|---|
| W1 / W2 | both SUBJECTS as predicted; both GRADES failed on the driver's check (`_where()` returns numeric map ids; the check compared names) | a DRIVER bug, not a result — fixed and re-run |
| **W1b** (old tile) | `UnreachableDestinationError: Could not reach (26, 5) on MapRSE.PETALBURG_WOODS … still at (14, 5)`, inside the Woods, 37,609 frames | **as predicted** — the batch's 67/67 derail reproduced |
| **W2b** (the fix) | Lavaridge → Route 112 → 111 → Mauville → 117 → Verdanturf → Rusturf → 116 → Rustboro → Route 104 → PETALBURG_WOODS → Route 104 → **PETALBURG_CITY**, finished, no whiteout, 38,438 frames | **as predicted** |

**Not shown:** frequency in a batch (expected: 0 `Could not reach (26, 5)` derails after the merge, one derail slot saved
per run that takes this leg). The Route 111 member of `#26-destreachability` is separate and OPEN.
