# 2026-09-30 — design v2 step 13 (KB-2, items in DOUBLE battles): PRE-REGISTERED PREDICTIONS, filed BEFORE any production code

⚠ Filed against `2026-09-30-doubleitems13-DESIGN.md` (reviewed and folded) and after its Step 0
(`tools/story-dev/evidence/2026-09-30-doubleitems13-STEP0.txt`). **Both tables are filed BEFORE the code exists.** The
builder implements these rows with these outcomes. Any row the builder believes is wrong is REPORTED and argued, never
silently changed. A live reading that contradicts a prediction is a RESULT, not a driver failure.

## THE GATE ROWS (`tools/story-dev/probe_double_items.py`)

**Pure rows** (`modules/story/double_items.py`):

| Row | Input | Expected |
|---|---|---|
| DP01 | `mode(env)`: unset / `observe` / `1` / `0` / `yes` / `ON` / ` 1` | off / observe / on / off / off / off / off |
| DP02 | `in_scope`: Trainer+Double; +Multi; +InGamePartner; Trainer alone; Double alone | True; False; False; False; False |
| DP03 | `decode_bpo(02 13 45)`; `decode_bpo(12 03 45)`; `active_positions([0,2,1,3,4,5])` | [0,2,1,3,4,5]; [1,2,0,3,4,5]; (0, 2) |
| DP04 | `guard_ok(A, A, slot 0, count 6)`; menu ≠ intended; slot 6; slot 7; slot = count; intended None | True; False ×5 |
| DP05 | `self_ok(4, g=2, raw 00 00 00 00 04 00 01 00)`; target 1 with the same raw | True; False (a byte-stride read, `raw[g]`, gives 0 and must redden the first) |
| DP06 | `ledger_key(pid, species)` | `(pid, species)`; two PIDs never share a ledger |
| DP07 | `hp_only([(Potion,1,20), (Full Heal,1,0)])` | `[(Potion,1,20)]` |

**Production rows** (fakes: a double with a left and a right battler whose PIDs, party indexes and HP differ; bag
Potion ×1 unless stated):

| Row | Setup | Expected |
|---|---|---|
| DQ01 | flag unset | the parent's action; the instance `__dict__` unchanged; no `DBLITEM` log line |
| DQ02 | `observe`, left 20/100 | the parent's action; `__dict__` unchanged except `_dbl_obs`; exactly one `[DBLITEM-OBS]` line with `would=Potion`; `_maybe_use_item` and `_r27_key_gate` never called |
| DQ03 | observe parity | `heal_options` equals the options `_maybe_use_item` passes to `choose_healing_item` on the same fake |
| DQ04 | `1`, side 0, left 20/100 | `UseItem(Potion, <left's party index>)` |
| DQ05 | `1`, side 1, right 20/100 | `UseItem(Potion, <right's party index>)` |
| DQ06 | `1`, side 0, left 100/100, right 20/100 | no item: the parent's action (self-only) |
| DQ07 | `1`, side 0, left asleep at 100/100, bag Full Heal only | no item (D10) |
| DQ08 | `1`: side 1 requests; then side 0 decides | side 1's pending request is still set afterwards |
| DQ09 | `1`, +Multi or +InGamePartner | the parent's action |
| DQ10 | `1` + `KEYITEMS=1`, a non-key class / class LEADER | no item / `UseItem` |
| DQ11 | `scroll_to_battle_action(1, True)` on a fake cursor [1, x, 0, x] | reads byte 2 and presses until byte 2 = 1; with `FAULT_DBL_CURSOR0` it reads byte 0 and presses nothing |
| DQ12 | `battle_action_use_item(…, battler_index=2)` | calls `scroll_to_battle_action(1, True)` |
| DQ13 | executor positive control, matching PIDs | cursor driven to the requester's slot, then A; `ok=1 a_pressed=1`. `FAULT_DBL_WRONGSLOT` reddens it |
| DQ14 | the scroll stops short (slotId ≠ `_menu_slot`) | refused: the guard reads slotId |
| DQ15 | PID mismatch at the slot | no A; the B unwind runs; `ok=0 a_pressed=0`. `FAULT_DBL_NOGUARD` reddens it |
| DQ16 | the Struggle loop; controller 2 enters `HandleInputChooseAction` mid-loop | flag `1`: no A after that frame. Flag unset: A keeps being pressed (today's behaviour, byte for byte) |
| DQ17 | flag unset, executor | no guard read and no `DBLITEM` line |

- **Faults:** `CURSOR0` reddens exactly DQ11 and DQ12's byte assertion; `WRONGSLOT` exactly DQ13; `NOGUARD` exactly DQ15
  (DQ14 stays green only if its refusal comes from the slot range check, so the builder states which).
- **Existing gates that must stay green:** `repro_item_noop_detector.py`, `repro_key_battle_items.py` (A1),
  `repro_battle_items.py`, `repro_ki46_action_selection_bound.py`, `probe_dmgaudit.py`, `repro_no_silent_except.py`.

## THE LIVE ARMS (seed 1, `storyresume`; every value from Step 0)

**Grading rules, fixed now:**
- Every HP and bag value is read from the `[DBLITEM] after` line, never from a later `[TURN]` line.
- "= X up to frame F" means: every frame-stamped line of the two copied debug logs with a frame < F is identical.
- PIDs are compared case-insensitively.
- D15: a family's two OFF runs must match each other first, else a third; a lone divergent run is re-run, never graded.

**Family P — `post_mtpyre.ss1` (PINNED `80602159694b`), KEYITEMS unset except P-KEY, the default fraction, no lever.**
Targets at the first double (f3148510): Sceptile, party 1, PID `863B0917`, 21/117, menu slot 0 (battler 0);
Swellow, party 2, PID `0B30A747`, 18/109, menu slot 1 (battler 2). Bag: Hyper Potion ×1.

| # | Arm | Prediction | Falsified by |
|---|---|---|---|
| P1 | X-BASE ×2, P-OFF ×2 (90,000 frames) | all four equal: `logsha` `928db5621b3d2f7c` over 371 frame-stamped lines, the value both X-BASE runs gave in `STEP0.txt` (frame numbers included); 0 `DBLITEM` lines in P-OFF | any difference between P-OFF and X-BASE; any `DBLITEM` line with the flag unset |
| P2 | P-OBS (30,000) | = P-OFF on every line without `DBLITEM`. The first `[DBLITEM-OBS]` row with `would≠-`: f3149372, side 0, Sceptile, `would=Hyper_Potion`. On every row of the first double `bpo_pos = side` and `disc=1` | a gameplay line that differs from P-OFF; a first `would` row elsewhere; `bpo_pos ≠ side` |
| P3 | P-ON (30,000) | = P-OFF before f3149372. At f3149372: `[DBLITEM] use side=0 g=0 item=Hyper Potion target=Sceptile#863B0917 P=1 hp=21/117 self=1`; `menu … slot=0 menu_pid=863B0917 ok=1 a_pressed=1`; `after … hp=21->117 … partner=… hp=18->18 … Hyper Potion=1->0 healed=+1`. Battler 2's same-turn FIGHT completes with no KI-45 | the item on any other PID; no act at f3149372; a KI-45 on `gActionSelectionCursor` |
| P4 | P-KEY (30,000; + KEYITEMS=1) | a `[KEYBATTLE]` line with `key=False` at the first double; no `[DBLITEM] use`; gameplay = P-OFF | an item used in a non-key double |
| P5 | P-CUR (30,000; + CURSOR0) | P3's `use`, `menu` and `after` lines as in P3; then `KI-45: cursor 'gActionSelectionCursor' never reached index 0 after 60 steps (last read: 1)` | no KI-45 on battler 2's FIGHT (the fix is not load-bearing) |
| P6 | P-SLOT (30,000; + WRONGSLOT) | at f3149372: `menu … slot=1 menu_pid=0B30A747 intended_pid=863B0917 ok=0 a_pressed=0`; `after … hp=21->21 … partner … hp=18->18 … Hyper Potion=1->1`. Then one retry, refused the same way, then `[ITEM] ‼ not consumed twice; disabling items`; no item is used in that battle | an A press on slot 1; any HP or bag change at the refusal |
| P7 | P-NOG (30,000; + WRONGSLOT + NOGUARD) | at f3149372: `menu … slot=1 … ok=0 a_pressed=1`; `after … hp=21->21 … partner=Swellow… hp=18->109 … Hyper Potion=1->0` | Swellow not healed (the arm is vacuous and the guard's load-bearing claim is unproven) |

**Family T — `d13_tateliza.ss1` (PINNED `1d8f604694b9`), `KEYITEMS=1` and `POKEBOT_HEAL_AT_FRACTION=0.8` in every
arm, 20,000 frames.** Targets from turn 1: Sceptile, party 0, PID `863B0917`, menu 0 (battler 0); Mightyena, party 4,
PID `5C96EA9B`, menu 1 (battler 2). Bag: Potion ×1, Full Heal ×1.

| # | Arm | Prediction | Falsified by |
|---|---|---|---|
| T1 | T-OFF ×2 | equal to each other, and to S0-RESUME on every line from the battle start (f3452776) to its end (f3464107) | a difference inside the battle |
| T2 | T-OBS | = T-OFF on every line without `DBLITEM`. `bpo_pos = side` on every row; `disc=1` on side 1's rows from turn 1 and `disc=0` on side 0's. First `would≠-`: f3456183, side 1, Mightyena, `would=Potion`, `key=1` | as P2 |
| T3 | T-ON | = T-OFF before f3456183. There: `use side=1 g=2 item=Potion target=Mightyena#5C96EA9B P=4 hp=99/127 self=1`; `menu … slot=1 menu_pid=5C96EA9B ok=1 a_pressed=1`; `after … hp=99->119 … partner=Sceptile#863B0917 hp=116->116 … Potion=1->0 healed=+1`. Battler 2's BAG scroll converges; its next FIGHT (byte 2 = 1) completes with no KI-45, graded only if battler 2 is asked again (declared ABSENT otherwise). A `[KEYBATTLE] … key=True` line | the item on Sceptile; no act at f3456183; a KI-45 on `gActionSelectionCursor` |

## WHAT WOULD MEAN THE BUILD IS WRONG (beyond each row's falsifier)

- Any flag-unset run that differs from the base code (P1, T1).
- Any `[DBLITEM] after` line where an HP rise lands on a PID other than the requester's in P3 or T3.
- A `menu` line with `ok=0` and `a_pressed=1` in any arm without `NOGUARD`.
- A hang or a Manual drop in any arm before its graded event.
