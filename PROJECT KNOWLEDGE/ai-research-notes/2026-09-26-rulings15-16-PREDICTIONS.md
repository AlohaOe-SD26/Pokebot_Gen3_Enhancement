# 2026-09-26 — USER RULINGS 15 + 16 — PRE-REGISTERED PREDICTIONS (written BEFORE any drive)

> **RULING 15** (R1): refuse the Elite Four only if FEWER THAN `min(4, party size)` members are at the floor
> (`ch24_readiness_shortfall(..., party_size=)`, `CH24_MIN_AT_FLOOR = 4`). **RULING 16** (§Ch23 leg 11): buy only the
> MISSING basket quantities (`basket_to_buy`, `basket_cost`; arm `POKEBOT_CH23_FAULT_FULLBASKET` restores the old
> full-basket purchase). Branch `wt/ch24organic`; every drive `HARNESS_EXIT_ON_MANUAL=1`. Gates (static, already PASS):
> `probe_ch24_r1_refusal.py` (G1 with the strict all-six rule as a fault arm), `probe_ch23_basket_buy.py`.

## DISCRIMINATORS (measured before the drive, `probe_ch24_readiness_inputs.py`)
* `post_ch24_atdoor_L75.ss1` (`8b8cd907db09`), EG (18,6): below L65 = Zigzagoon L19, Castform L36 ⇒ **4 of 6 at the
  floor**; basket 37/3/18/3.
* `post_league_shop.ss1` (`1564948368f6`), EG (18,6): levels 19/36/47/48/48/53 ⇒ **floor 48: 3 below (19, 36, 47) —
  only 3 at it; floor 47: 2 below (19, 36) — 4 at it**; basket EXACTLY 30/3/8/3; ₽1,741.
* `post_league_heal.ss1`, EG (18,6): basket 0/0/0/0; ₽56,041.

| arm | driver · fixture · env | prediction | falsifier |
|---|---|---|---|
| **R15-ENTER** | ch24entry · `post_ch24_atdoor_L75` · floor **65** · `NOTRAIN=1` | `ACCEPTANCE: PASS` — R1 passes at the PRODUCTION floor with Zigzagoon L19 + Castform L36 below (`readiness_refusal=[]`, `E1-READY`), door open | any R1 refusal |
| **R15-B48** | ch24entry · `post_league_shop` · floor 48 · `NOTRAIN=1` · `EXPECT=refuse:floor` | `ACCEPTANCE: PASS` (refuse): `3 mōn below the L48 floor — only 3 of 6 at it, RULING 15 needs 4` naming Zigzagoon, Castform, Wailord; door shut | no refusal; a basket reason |
| **R15-B47** | ch24entry · `post_league_shop` · floor 47 · `NOTRAIN=1` | `ACCEPTANCE: PASS` (enter) — 2 below, 4 at the floor ⇒ R1 passes; door open | a refusal ⇒ the boundary is off by one |
| **R15-A** (regression) | ch24entry · `post_league_shop` · floor 65 · `NOTRAIN=1` · `EXPECT=refuse:floor` | `ACCEPTANCE: PASS` (refuse): `6 mōn below … only 0 of 6 at it, RULING 15 needs 4` | any entry |
| **S1 FULL** | ch23shop · `post_league_heal` | `ACCEPTANCE: PASS`; `to_buy` = the whole basket, `need_money=54300`; ₽56,041 → **₽1,741** (as the 2026-09-04 capture) | any other spend; a shortfall |
| **S2 NOTHING** | ch23shop · `post_league_shop` | `ACCEPTANCE: FAIL` **solely** on `premise_ok=False` (the driver refuses to count a run that started stocked); `failure=None`, `nothing_to_buy=True`, `to_buy=[]`, `need_money=0`, `money_before == money_after == 1741`, readings complete, back on EG | any refusal or spend; any other failed conjunct |
| **S3 FULLBASKET** (skip-the-fix) | ch23shop · `post_league_shop` · `POKEBOT_CH23_FAULT_FULLBASKET=1` | FAILURE: `Ch23 leg 11: the missing basket lines [...all four...] cost ₽54,300 … but we hold ₽1,741` — the OLD behaviour refuses a party that already carries the whole basket; money unchanged | no refusal (then the arm tests nothing) |
