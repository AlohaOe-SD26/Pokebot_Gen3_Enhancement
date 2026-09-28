# 2026-09-28 — `#27-setballs` (the harness's `--set-balls` does nothing): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the fix. Branch `wt/setballs`, cut from `main` `a379751e`. The defect: `story_harness.py` looks up
> `"PokÃ© Ball"` (a mis-encoded "Poké Ball" from commit `4bd5bc4de`). The lookup raises `KeyError`, the `except` logs
> `[setup] set-balls err …`, and the run CONTINUES with the bag unchanged. The `martbuy` driver's ball count has the same
> literal.

## THE FIX (planned)

1. Both lookups use `"Poké Ball"`.
2. `--set-balls N` sets the Poké Ball STACK to N and KEEPS every other ball stack (Premier, Great, …). The old
   behaviour replaced the whole pocket with N Poké Balls. No committed evidence ever depended on either behaviour
   (0 `set-balls err` lines in `evidence/`).
3. A failure is LOUD: the `except` logs and RE-RAISES, so a run whose lever did not apply cannot continue as if it had.
4. The remaining mis-encoded literals in `story_harness.py` (help strings, comments, log text) are repaired by an
   exact cp1252→UTF-8 round trip, touching only the affected lines.
5. A gate, `probe_harness_item_names.py`:
   - every string literal passed to `get_item_by_name(...)` / `_ball_count(...)` in `story_harness.py` resolves
     offline;
   - the set-balls `except` re-raises;
   - no line holds mojibake.
   Fault arms: a mutant literal must FAIL; a mutant `except` without `raise` must FAIL; a comment that MENTIONS the
   bad name must NOT fire.

## DRIVE — `storyresume` on `post_mtpyre.ss1` (`80602159694b`; bag: 16 Poké + 1 Premier = 17), `--set-balls 30 --frames 4000`

| Arm | Code | Harness log | Profile debug log |
|---|---|---|---|
| A (unfixed) | `main` `a379751e` | `[setup] set-balls err 'PokÃ© Ball'` (and the run continues) | the first `[hb]` reads `balls=17` |
| B (fixed) | the fix commit | `[setup] set Poké Balls to 30`, with a READ-BACK of the bag the code wrote (rule 7): `Poké Ball x30`, `Premier Ball x1` | the first `[hb]` reads `balls=31` |
| C (fixed, `--set-balls 0`) | the fix commit | `[setup] set Poké Balls to 0`, read-back `Premier Ball x1` | the first `[hb]` reads `balls=1` |

`--frames 4000`, because the heartbeat fires every 3,600 frames (a 3,000-frame run would have none, which is VACUOUS). A
`[BALLS] a -> b` delta line is NOT predicted: the lever applies at harness step 1, possibly before the logger's first
sample, so no delta may be logged. The read-back and the heartbeat are the readings.

## FALSIFIERS

- Arm A applies the change: the diagnosis is wrong.
- Arm B's heartbeat reads 30 rather than 31: the other stacks were dropped (fix item 2 is wrong).
- Arm C reads 0: same.
- A FIXED arm continues after a `set-balls err`: the failure is not loud. (Unfixed arm A continuing IS the bug.)

## WHAT THIS DOES NOT SHOW

- Step B (the ball restock) itself, which is the next item.
- Any fixture premise besides the ball count.
