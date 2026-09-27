# 2026-09-26 — KI-104: the HM teach's slot rule — PRE-REGISTERED PREDICTIONS

> Filed BEFORE the drives. Code (branch `wt/ch24organic`, uncommitted at filing): `early_game.choose_hm_slot` — a TOTAL,
> type-aware picker (status > banned > strictly dominated by a kept move or the incoming HM > weakest non-STAB > STAB;
> HMs excluded first; multi-hit and power-1 moves valued sensibly); an explicit HM `replace_slot` refused before the bag.
> Arm `POKEBOT_HMTEACH_FAULT_OLDSLOT` restores the old rule (zero power, else the lowest RAW base power). Gate
> `probe_hmslot_rule.py` PASS at filing (the live shapes, totality incl. 500 seeded movesets, three fault arms).

**Fixture:** `norman_done.ss1` (PINNED `e6fb7d5f`), `--driver teachfull`, `TEACH_ITEM=HM04` (Strength) — the same A/B
setup as `#26-hmwrongitem` H2b/H2c, whose fixed-scroll runs taught Strength over **Double Kick** (the old slot rule).
Blaziken = [Scratch (Normal 40), Blaze Kick (Fire 85), Double Kick (Fighting 30 x2), Rock Smash (HM06)].

| # | Arm | Prediction | Falsifier |
|---|---|---|---|
| K1 | `POKEBOT_HMTEACH_FAULT_OLDSLOT=1` | `RESULT learned=True`, `replaced=['Double Kick']` (the old rule — as H2b/H2c) | anything else replaced |
| K2 | the new picker | `RESULT learned=True`, `replaced=['Scratch']` — Scratch is strictly dominated by the incoming Strength (Normal 80 ≥ 40); Double Kick and Blaze Kick (STAB) kept; the verified scroll still corrects HM03 → HM04 | Double Kick or Blaze Kick replaced; Rock Smash (HM) touched; not learned |
