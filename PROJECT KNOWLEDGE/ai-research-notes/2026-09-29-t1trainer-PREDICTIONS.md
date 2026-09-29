# 2026-09-29 — design v2 step 5 (TID/T1: trainer identity + money telemetry, log-only, ALWAYS ON): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code is committed and before any graded drive. Branch `wt/t1trainer`, cut from `main` `03244ae7`.
> Spec: `ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md` step 5 (a NOTE). Its decomp and ROM numbers were verified by
> an independent agent against pokeemerald and our ROM, and a second agent audited our code paths. The orchestrator
> re-read ROXANNE_1's row and the money table from the ROM file. Every spec number holds.

## THE CHANGE (planned), with the verification's corrections

- **New `sandbox-pokebot/modules/story/trainer_identity.py`.** It reads only through existing primitives: `read_symbol`,
  `unpack_uint16`, `context.emulator.read_bytes`, `decode_string` and `get_event_flag_by_number`.
  - `read_opponent_trainers(battle_type)`: A = `gTrainerBattleOpponent_A`; **B only when `BattleType.TwoOpponents` is
    set.** B's ID SURVIVES into later single battles (`battle_setup.c` writes B only from the B param tables and clears
    it only on a sighting reset). IDs must satisfy `0 < id < 855`.
  - `trainer_row(id)`: from `gTrainers` (stride 0x28): flags +0x00, class +0x01, party size +0x20, party pointer
    +0x24.
  - `last_mon_level(id)`: the ROM party, stride 16 if `flags & 1` else 8, level at +2, `party[partySize-1]`.
  - PURE `money_value_for_class(table_bytes, cls)`: 4-byte entries, up to the 0xFF terminator (unlisted ⇒ 5).
  - PURE `payout(value, last_level, double, two_opponents, multiplier=1)`: 4 × level × value; ×2 only for DOUBLE
    without TWO_OPPONENTS (`battle_script_commands.c:5624-5629`); × the money multiplier.
    - ⚠ The Amulet Coin's ×2 applies only when a player-side holder SWITCHES IN (`battle_util.c:3294-3296`). This
      badge-1 fixture has no Amulet Coin, so the live `mult` is predicted 1.
  - `first=`: `not get_event_flag_by_number(0x500 + id)` at battle START (the flag is set after the battle).
- **`story_mode.py`: two module-level helpers, `_t1_start(mode, encounter)` and `_t1_end(mode, outcome)`** (stand-in
  `self` safety, the step-4 lesson).
  - `_t1_start` is called once per battle. It snapshots only when `encounter is None and BattleType.Trainer in
    get_battle_type()`, which excludes Wally's tutorial (its battle type has no Trainer bit, and its stale opponent ID
    is in range).
  - `_t1_end` runs right after the `[MONEY]` line, before `_r20_catch_end` and the unguarded Lost block.
- **Lines** (category `TRAINER`, never under `[BATTLE]`):
  - `[TRAINER] start opp=<A>[+<B>] class=0x..(<NAME_NO_SPACES>) value= lvl_last= base= first= double= map= money=`
  - `[TRAINER] end … res=<Won|Lost|…> money=a->b delta= mult= heal_stock=<name:qty,…>`
  - **`res=`, never `outcome=`** (two batch parsers count `outcome=BattleOutcome`). **No spaces in values.** **No
    `key=`** (step 6's).
- **Flag: none**, by the 06:7902 precedent.
- **Fault arms:** `POKEBOT_T1_FAULT_FIRSTMON` (reads `party[0]`), `POKEBOT_T1_FAULT_STRIDE2` (2-byte money stride) and
  `POKEBOT_T1_FAULT_WILDTOO` (snapshots wild battles).
- **NEW gate `probe_trainer_identity_T1.py`:**
  - (a) static constants;
  - (b) ROM rows read from the `.gba`: 265 ROXANNE_1 class 0x20, levels 12/12/15, so `last_mon_level` = 15; 11 MARCEL
    0x05; 261 SIDNEY 0x1F; **116 (a Grunt, stride 8) levels 26/28/30, so 30**. The money table gives LEADER 25,
    YOUNGSTER 4, RICH_BOY 50, class 0 → 5;
  - (c) payout rows: 1,500, 80, 1,600, the double ×2, the two-opponent sum;
  - (d) a WallyTutorial battle type gives no snapshot;
  - (e) B is not read without TwoOpponents;
  - (f) with a raising logger and an open context, the defeat is still counted;
  - the fault arms, each with an exact red set.

## THE DISCRIMINATOR (measured: step 4's M0, `main` `9a4fbbeb`, seed 1)

`storyresume` on `r20_badge1_party1_gym.ss1` (`50af0f5c`), `POKEBOT_R20_OPENFENCE=1`, `--set-balls 60`,
`random.seed(1)`. Debug frames. Each positive wallet change between consecutive `[MONEY]` lines, with no purchase
between them, is a trainer payout:

| M0 `[MONEY]` frame | Map | Wallet Δ | Reading |
|---|---|---|---|
| f148516 | (0,31) Route 116 | +180 | a trainer |
| f152239 | (0,31) | +320 | a trainer |
| f156823 | (0,31) | +128 | a trainer |
| f160004 | (0,31) | +320 | a trainer |
| f163453 | (24,4) Rusturf Tunnel | +220 | the Grunt (4 × L11 × 5) |
| f188817 | (0,19) | −4,874 | a payout MASKED by a purchase since the previous line: not predictable from M0 |
| f199649 | (0,21) | +440 | a trainer |
| f238265 | (3,3) Dewford Gym | **+1,900** | **Brawly (LEADER, 25 × 4 × L19)** |
| f253550 | (0,24) | +468 | a trainer |

## THE ARMS AND THEIR PREDICTED READINGS

All arms use the same command, 120,000 frames (to debug f259500), and seed 1.

| Arm | Code | Predicted |
|---|---|---|
| **CONTROL** | `main` `03244ae7`, the PARENT commit, which has no T1 | M0 replayed (steps 4 and 5 default OFF): its tracked lines equal M0's through f259500 |
| **T1** | `wt/t1trainer` HEAD | **Every `[BATTLE] …` line (every one: started, ended, TURN, ITEM) is identical to CONTROL.** A `[TRAINER] start`/`end` pair for every trainer battle, and none for a wild battle. For each of the 8 unmasked payouts above, the end line reads `res=Won`, `delta` equal to the Δ in the table, **`delta == base`**, `mult=1` and `first=True`. Brawly reads `class=0x20(LEADER) value=25 lvl_last=19 base=1900`. The Rusturf Grunt reads `value=5 lvl_last=11 base=220` |
| **FIRSTMON** (fault) | T1 + `POKEBOT_T1_FAULT_FIRSTMON=1` | the same `[BATTLE]` lines. `base` ≠ `delta` for every Won trainer whose first and last mon levels differ (Brawly's first mon is predicted lower than L19). Red |
| **WILDTOO** (fault) | T1 + `POKEBOT_T1_FAULT_WILDTOO=1` | `[TRAINER]` pairs on WILD battles too, reading `delta=0` and `mult=0`. Red |

**STRIDE2 is VACUOUS live, stated in advance.** A 2-byte stride differs from the true one only for class 0 (verified
over all 255 classes), and no Hoenn trainer battle has class 0. Its proof is the gate's class-0 row.

## FALSIFIERS

- Any `[BATTLE]` line differs between T1 and CONTROL: the telemetry changed a battle.
- A `[TRAINER]` line on a wild battle, or none on a trainer battle.
- A Won line with `delta != base`, or `mult != 1`.
- `outcome=` or a space inside any `[TRAINER]` field value.
- A traceback, or a `[MODE]` change CONTROL does not have.

## WHAT THIS DOES NOT SHOW

- Which trainers a run skips (the T3 ledger).
- Rematch state. `first=` is True on the first fight at each rematch tier, which has its own flag.
- The B side of a two-opponent battle LIVE: no pinned fixture has one. The gate's rows cover the formula.
- Whether money-making pays.

## ADDENDUM (committed BEFORE the code, after observe-only smoke runs; no graded drive has run)

Three observe-only smoke runs of the uncommitted code (20,000 frames, seed 1) found one thing the plan did not predict:
- **A post-battle scene re-enters the battle hook.** After the School Kid (id 280) win that evolves Mudkip into
  Marshtomp, the listener calls `on_battle_started` AGAIN at f150064 and `on_battle_ended` again at f150066.
  - This is pre-existing behaviour. CONTROL also logs `[MONEY] after Won` twice for that battle (f148516 and f150066).
  - T1 logged a PHANTOM pair (`opp=280 … res=Won delta=0 mult=0`), which is exactly this note's falsifier "a Won line
    with `delta != base`".
- **The discriminator was MEASURED, not assumed.**
  - `gBattleOutcome` was the first hypothesis, and it was REFUTED: it read `Won` at all 6 starts, real and phantom.
  - The number of living enemy mons: 1 or 2 at every real start, **0 at the re-entry**.
- **Fix:** `_t1_start` logs `[TRAINER] skip reason=no_enemy_alive …` and opens no pair when 0 enemy mons are alive. An
  unreadable party still logs the battle. The start line gains `enemy_alive=`. Gate case W4, and the source mutant
  F7.

**Revised readings for the graded arms (everything else above stands):**
- T1: at f150064 one `[TRAINER] skip reason=no_enemy_alive` line and NO `[TRAINER] start`/`end` pair. Every
  `[TRAINER] start` line reads `enemy_alive` ≥ 1.
- The `[BATTLE]` lines stay identical to CONTROL, because the guard only chooses whether to LOG.

