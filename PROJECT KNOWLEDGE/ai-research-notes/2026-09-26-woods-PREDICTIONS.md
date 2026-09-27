# 2026-09-26 — `#26-destreachability` (Petalburg Woods member): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the drives. Forensics (a NOTE, `2026-09-26-batch0926-FORENSICS.md`): `travel_lavaridge_to_petalburg`
> aimed at PETALBURG_WOODS (26, 5), a SOLID TREE — 67 of 67 legs derailed and recovered only via a re-run from inside the
> Woods. Fix (branch `wt/ch24organic`): aim at (14, 6), the first tile inside the north door (planner-probed reachable);
> the existing south-east exit block does the rest. Arm `POKEBOT_WOODS_FAULT_OLDTILE`.
> Fixture: `flannery_done.ss1` (Lavaridge, the leg's start; NOT pinned — md5 `61e90c57fedf2a9e41349e3be23ff29c` at filing).
> Driver: `--driver woodsleg` (production's whole `travel_lavaridge_to_petalburg()`).

| # | Arm | Prediction | Falsifier |
|---|---|---|---|
| W1 | `POKEBOT_WOODS_FAULT_OLDTILE=1`, `WOODS_EXPECT=derail` | the leg raises `UnreachableDestinationError` naming (26, 5) while inside PETALBURG_WOODS (the batch's derail, reproduced) | the leg reaches Petalburg with the old tile (the forensics are wrong) |
| W2 | the fix, `WOODS_EXPECT=arrive` | the leg returns without raising, its map trace includes PETALBURG_WOODS, it ends in PETALBURG_CITY, no whiteout | any exception, a whiteout, or an end outside Petalburg City |
