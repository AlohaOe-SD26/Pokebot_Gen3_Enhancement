# 2026-09-26 — `#26-hmwrongitem`: the HM teach uses the WRONG HM — PRE-REGISTERED PREDICTIONS

> Filed BEFORE the drives. Recon (3 Claude agents, a NOTE): 9 of 87 HM teaches in the day's batch taught HM06 Rock Smash
> to a Surf/Waterfall target (`Teach flow finished but Marshtomp does not know Surf`, 7 runs). Hypothesis (mine, from the
> fixture's own pocket): upstream `scroll_to_item_in_bag` computes the slot from the TM/HM pocket as stored, but the game
> SORTS that pocket when the bag opens; right after an HM is received it is unsorted.
> Fix (branch `wt/ch24organic`, `early_game.teach_hm_move`): `pokemon_league.scroll_to_tm_verified` (read the cursor + the
> live pocket, correct closed-loop, refuse rather than press A on anything else); arm `POKEBOT_HMTEACH_FAULT_UNVERIFIED`.

**Fixture:** `norman_done.ss1` (PINNED `e6fb7d5f`), PETALBURG_CITY, badges 1-5. Its TM/HM pocket AS STORED:
`[TM08, TM34, TM39, TM47, HM06, TM50, HM04, TM42, HM03]` — HM03 at index 8. Sorted (the game's order after the bag
opens): `[TM08, TM34, TM39, TM42, TM47, TM50, HM03, HM04, HM06]` — index 8 is **HM06**.
**Driver:** `--driver teachfull`, `TEACH_ITEM=HM03` (it teaches to a compatible party mon that already has 4 moves).

| # | Arm | Prediction | Falsifier |
|---|---|---|---|
| H1 | `POKEBOT_HMTEACH_FAULT_UNVERIFIED=1` (the old scroll) | the WRONG item is used: the target ends WITHOUT Surf, and if it can learn Rock Smash it GAINS Rock Smash; `RESULT learned=False`; a `TEACH EXIT … hard-cap` or an equivalent failure exit | Surf learned with the old scroll (the hypothesis is wrong — the bug has another cause) |
| H2 | the fix | `[TEACH-CURSOR] ⛔ upstream left the cursor on slot 8 (HM06); correcting to slot 6 (HM03)` then `verified`; the target learns **Surf**; no Rock Smash gained; `RESULT learned=True` | no correction line (the scroll was right: H1's failure has another cause), or Surf not learned |

## ADDENDUM (filed BEFORE the re-drive) — PREMISE FAILED for HM03; re-registered for HM04

Both HM03 arms ran and ABORTED before teaching: `teachfull` found no party mon on `norman_done.ss1` that can learn Surf
(`compat=False` for all five — evidence `2026-09-26-hmwrongitem-H1-unverified.*` / `-H2-fix.*`). A premise failure,
not a result. Re-registered on **HM04 Strength**: stored index 6; in the SORTED pocket index 6 is **HM03 Surf**.

| # | Arm | Prediction | Falsifier |
|---|---|---|---|
| H1b | `TEACH_ITEM=HM04`, `POKEBOT_HMTEACH_FAULT_UNVERIFIED=1` | the old scroll lands on **HM03**; the Strength target (a 4-move Strength learner, e.g. Blaziken) CANNOT learn Surf, so no replace prompt ever comes: a failure exit of the `exhausted` / never-appeared kind, `RESULT learned=False`, the moveset UNCHANGED — the shape of the batch's 13 unexplained "exhausted" hard caps | Strength learned (the scroll was right after all) |
| H2b | `TEACH_ITEM=HM04`, the fix | `[TEACH-CURSOR] ⛔ upstream left the cursor on slot 6 (HM03); correcting to slot 7 (HM04)` then `verified`; the target learns **Strength**; `RESULT learned=True` | no correction line, or Strength not learned |
