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

## ADVERSARIAL REVIEW

It returned KICK-BACK only for the owed `07`/`08` entries, which were written after it. It verified:
- the two functional repairs (the set-balls lookup and `martbuy`'s `_pb`); every other changed line is text;
- that the read-back mirrors `get_item_bag()`'s own construction;
- that the re-raise is unhandled up to the harness loop, so it ends the run with a traceback;
- that N2 has no live false positive.

Its main risk is CLOSED in `22ba1210`: `debug_write_item_bag` returns False WITHOUT raising when no save block is
mapped, so the read-back is now ASSERTED against the intended pocket (gate L2, fault arm F4). B and C were re-driven
there identically (`evidence/2026-09-28-setballs-final-22ba1210.txt`).

Its count correction stands: 38 mis-encoded lines were repaired, 2 by hand in the rewritten set-balls block and 36 by
the round-trip script.

Its other point, that no mojibake gate covers `tools/story-dev/*.py` as a whole, is recorded as a residual. A
measured tree-wide scan finds:
- the deliberate examples inside `audit_encoding.py`;
- a legitimate character table in `sandbox-pokebot/modules/game.py:142`, a false positive;
- cosmetic mojibake in `livetest.py`.
A tree-wide gate would therefore need an allowlist, which is how gates acquire false positives.

## WHAT THIS DOES NOT SHOW

- That any past evidence was affected: 0 committed files contain `set-balls err`, so no earlier graded arm used the
  lever.
- Step B (the ball restock), which is now unblocked.
