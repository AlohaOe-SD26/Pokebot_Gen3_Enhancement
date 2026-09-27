# 2026-09-26 — `#26-hmwrongitem` (KI-105): GRADED

> Predictions: `2026-09-26-hmwrongitem-PREDICTIONS.md` (`a93fe66e`, re-registered for HM04 at `75b41241` — both BEFORE
> the drives they predict). Evidence: `tools/story-dev/evidence/2026-09-26-hmwrongitem-*`.

| # | Result | vs prediction |
|---|---|---|
| H1 / H2 (HM03) | both ABORTED before teaching: no party mon on `norman_done.ss1` can learn Surf | a failed PREMISE, not a result — re-registered |
| **H1b** (HM04, the old scroll) | `RESULT learned=False`, moveset unchanged — the cursor sat on HM03, which Blaziken cannot learn | **as predicted** (the shape of the batch's unexplained "exhausted" hard caps) |
| **H2b** (HM04, the fix) | `[TEACH-CURSOR] ⛔ upstream left the cursor on slot 6 (HM03); correcting to slot 7 (HM04)` → `verified` → `RESULT learned=True` (Strength) | **as predicted, the correction line verbatim** |

**The mechanism, shown by the fixture itself:** the stored pocket `[TM08, TM34, TM39, TM47, HM06, TM50, HM04, TM42, HM03]`
sorts to `[TM08, TM34, TM39, TM42, TM47, TM50, HM03, HM04, HM06]` when the bag opens; the upstream helper's index for HM04
(6) then holds HM03 — as the live batch's HM03 index (8) held HM06.

**Not shown:** the live frequency after the fix (the post-merge batch: `does not know Surf/Waterfall` derails from a wrong
HM should be 0). ⚠ H2b also shows KI-104 (the slot rule) live: Strength replaced Double Kick — separate and OPEN.
