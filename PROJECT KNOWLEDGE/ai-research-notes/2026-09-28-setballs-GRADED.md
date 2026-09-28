# 2026-09-28 — `#27-setballs` GRADED: `--set-balls` works again, keeps the other balls, and cannot fail silently

> Predictions: `2026-09-28-setballs-PREDICTIONS.md` (`f257d58e`, before the fix). Fix: `964d38a5`. Drive:
> `storyresume` on `post_mtpyre.ss1` (bag: 16 Poké Balls + 1 Premier Ball), `--frames 4000`. Evidence:
> `tools/story-dev/evidence/2026-09-28-setballs-arm{A,B,C}.txt`.

| Arm | Code | Harness log (what the code did) | First `[hb]` | Verdict |
|---|---|---|---|---|
| A `--set-balls 30` | unfixed | `[setup] set-balls err 'PokÃ© Ball'`, and the run went on | `balls=17` (the lever never applied) | ✅ as predicted |
| B `--set-balls 30` | fixed | `set Poké Balls to 30 — read back from the save block: ball pocket = Poké Ball x30, Premier Ball x1` | `balls=31` | ✅ as predicted |
| C `--set-balls 0` | fixed | `set Poké Balls to 0 — read back from the save block: ball pocket = Premier Ball x1` | `balls=1` | ✅ as predicted |

No falsifier fired. B and C prove both halves of the fix:
- the lever APPLIES;
- it KEEPS the other stacks (31, not 30; 1, not 0).

The read-back comes from the save block, because `get_item_bag()` is cached per frame and a same-frame read would
report the bag from before the write.

**The loud-failure half is proven by the gate, not the drive.** In `probe_harness_item_names.py`, L1 checks that the
set-balls `except` re-raises, and fault arm F2 (an `except` that only logs) fails L1. N1 resolves all 12 literal item
lookups in the harness offline; F1 (the mojibake restored) fails N1 and N2; F3 (a comment mentioning it) does not fire.

## WHAT THIS DOES NOT SHOW

- That any past evidence was affected: 0 committed files contain `set-balls err`, so no earlier graded arm used the
  lever.
- Step B (the ball restock), which is now unblocked.
