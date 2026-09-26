# 2026-09-26 — USER RULING 17 (Amulet Coin) — PREDICTIONS, filed BEFORE any drive

> Build: `sandbox-pokebot/modules/story/amulet_coin.py` (`run_ch12d` → `fetch_amulet_coin` → `give_item_to_party_member`),
> wired into `_play` as Segment 12d after `_guard("Teach Surf (Ch12c)")`. Driver: `--driver amuletcoin`
> (`AMULET_EXPECT=given|skip|onetalk|nogive`; it calls `run_ch12d` itself, the same function `_play` calls).
> Spec: the GO recon (a NOTE); every load-bearing mechanic re-read in the decomp by me today (cited in the module).

## FIXTURE FACTS (observe-only, `probe_amulet_inputs.py`, not assumed)

`norman_done.ss1` (`e6fb7d5f36db`, pinned today): PETALBURG_CITY (7,6), **male** ⇒ Brendan's house, door (5,8);
BADGE05=1 BADGE06=0 HAS_MATCH_CALL=1 **ENABLE_MOM_MATCH_CALL=0** RECEIVED_AMULET_COIN=0; houses state May/Brendan =
0/2 (the post-game S.S.-Ticket scene needs 3 — it cannot fire); ITEMS pocket EMPTY (room for the coin); party
Shedinja L29 (0 HP), **Blaziken#341D550A L36 (0 HP)**, Mightyena L33 15/100, Ninjask L29 (0 HP), Loudred L30 93/93;
`pick_holder` = slot 1 (Blaziken — the top level; fainted mons can hold items).
`post_mtpyre.ss1` (`80602159694b`): MT_PYRE_SUMMIT, BADGE06=1 ⇒ out of era. ⚠ `amulet_coin_pending()` reads **True**
there (badge 5, no coin) — ⇒ **only the era gate stops it**, which is exactly what the arm tests.

## ARMS AND PREDICTIONS

| arm | how | predicted reading | falsifier (what would mean the BUILD is wrong) |
|---|---|---|---|
| **A1 GIVEN** | `norman_done`, default, `AMULET_SAVE_END=<scratch>/amulet_end.ss1` | `ACCEPTANCE: PASS`; order `AC-HOUSE, AC-REGISTERED, AC-RECEIVED, AC-GIVEN, AC-BACK`; talks `[register, coin]` (≤ 4 — a spare means a missed A, recorded not failed); `give_context_task = Task_ItemContext_MultipleRows`; `give_party_menu = True`; no `give_switched` (Blaziken holds nothing); holder `Blaziken#341D550A`; bag coins 0; end in PETALBURG_CITY with `continue_path OK`; 5k–30k frames | the context task is SingleRow (the grid assumption is wrong); `give_party_menu False` (Right did not reach GIVE); talk 1 predicted `register` but RECEIVED set on talk 1 (the decomp reading is wrong); the coin lands on a different PID |
| **A2 VACUITY (own output)** | A1's end state, `AMULET_EXPECT=given` | `PREMISE FAILED` ⇒ **FAIL** (the grade cannot pass a no-op) | a PASS |
| **A2b** | A1's end state, `AMULET_EXPECT=skip` | PASS, reason `"nothing pending"` (the coin is held), no move, < 2,000 frames | it walks south again |
| **A3 ERA GATE** | `post_mtpyre`, `AMULET_EXPECT=skip` | PASS, reason `"out of era"`, no move | it leaves Mt. Pyre |
| **A4 ONETALK** (fault `POKEBOT_AMULET_FAULT_ONETALK=1`) | `norman_done`, `AMULET_EXPECT=onetalk` | PASS (a RECOVERY arm): talks `[register]`, registered, NOT received, soft reason `"Mom did not hand over…"`, `AC-BACK`; its order lacks RECEIVED/GIVEN ⇒ it would FAIL the `given` grade | received after one talk (then the register-first reading is wrong) |
| **A5 NOGIVE** (fault `POKEBOT_AMULET_FAULT_NOGIVE=1`) | `norman_done`, `AMULET_EXPECT=nogive` | PASS (recovery): received, NOT given, bag coins 1, soft reason `"the give did not land…"`, `AC-BACK` | `AC-GIVEN` taken (it would mean AC-GIVEN is assumed, not read from the party) |

**G gates** (`probe_amulet_coin.py`, static, each with its own fault arm): `_play` calls `run_ch12d` between the
Surf guard and Segment 13a and guards only when it ran; the driver's Petalburg map set equals `_play`'s
`_at_petalburg`; `pick_holder` (top level / empty-slot tie-break / never an egg / empty ⇒ None); the driver imports
`AMULET_COIN_READINGS` from the module; `_houses_state` refuses `-1`.

## WHAT THESE DRIVES CANNOT SETTLE (stated now, so the grade cannot over-claim)
* Whether the coin **pays enough** — that is the batch's `[MONEY]` lines (F0), measured over organic runs.
* Mom as the **female** player (May's house, door (14,8)) — no fixture; the door comes from the recon's map read.
* A holder that already carries an item (the switch yes/no) — Blaziken holds nothing, so that branch is unexercised.
