# 2026-09-30 — design v2 step 13 (KB-2): healing items in DOUBLE battles — DESIGN (reviewed; Step 0 read)

⛔ **THE CAVEAT IS THE HEADLINE.**
- This step makes the bot ABLE to use a healing item in a double. It does not claim that items change a fight's outcome.
- The story's one scripted key double is Tate & Liza. There the losses are lopsided (about 73% of 0927's losses KO'd at
  most 1 of the 4 foes) and the bag is thin, so items are unlikely to flip it. The outcome value is mostly post-game:
  all 32 gym-leader rematches are doubles.
- ⇒ The live proof is a **CORRECTNESS A/B** (did the item land on the intended Pokémon, judged by IDENTITY?). A win-rate
  question is step 14's, a FREQUENCY question (CLAUDE.md rule 9).
- **Everything new is behind `POKEBOT_R27_DOUBLEITEMS` (default OFF)**, except C1, the action-cursor fix. C1 is a latent
  upstream defect that any double-battle item makes fire; with the flag unset it is inert by construction, and the
  flag-unset A/B (arm P-OFF vs X-BASE) is a no-crash regression check of every flag-unset change on a shared path.
- **v1 is deliberately narrow:** non-multi doubles, each battler heals only ITSELF, HP items only (§2).

**Inputs:**
- The spec: `2026-09-29-r23-27-DESIGN-v2.md` §Step 13 (`:671-680`), a spec pointer. This design supersedes it where they
  differ.
- The recon, six angles, and the design review (three lenses, every blocker/should-fix put to a refuter), each a NOTE:
  `2026-09-30-doubleitems13-recon/d13_recon_{decomp,ourcode,fixture,history,adversary,gemini}.md` and
  `d13_design_review.md`. The Gemini pass was 48% wrong on 44 claims, clustered on exactly the timing and index-space
  questions below; nothing here rests on it.
- Step 0: `tools/story-dev/evidence/2026-09-30-doubleitems13-STEP0.txt` (every read below marked S0-n).

## 1. WHAT THE AUTHOR VERIFIED (read at FILE:LINE, or measured live in Step 0)

**Our code** (worktree at `f7ae9878`):
- **V1. The action cursor is read for battler 0 only.** `scroll_to_battle_action` calls `_select_in_menu(
  "gActionSelectionCursor", idx)` with no side (`sandbox-pokebot/modules/battle_menuing.py:89-91`); `_select_in_menu`
  compares byte 0 unless `use_third_byte` (`:57-64`). `scroll_to_move` passes the side (`:94-96`). The callers are
  `battle_action_use_move` (`battle_action_selection.py:1198`), `battle_action_use_item` (`:1034`), RotateLead (`:773`),
  and the run and Safari paths (`:962-998`, battler 0 only).
- **V2. Both battlers of a double go to `decide_turn_in_double_battle`.** Battler 0 as `(state, 0)`, battler 2 as
  `(state, 1)` (`battle_action_selection.py:198-212`). The strategy index ("side") is {0, 1}; the handler's
  `battler_index`, like the game's battler id `g`, is {0, 2}; `g = 2 * side`.
- **V3. The handler re-reads the battle state AFTER each decision** (`:577-579`), so battler 2 decides on the state read
  before battler 0's item flow ran.
- **V4. `StoryItemBattleStrategy` overrides only `decide_turn`** (`story_mode.py:796`). A double falls through to
  `LevelUpTravelBattleStrategy.decide_turn_in_double_battle` (`:563-618`), whose trainer branch attacks only. The spec's
  `:518` is stale. `_maybe_use_item` reads `own_side.left_battler` twice: for the decision (`:832`) and for the KI-101
  judge (`:908`).
- **V5. The executor carries no battler.** `battle_action_use_item(battle_state, item, target_index)` (`:1016`) remaps
  the menu slot after the bag opens (KI-101, `:1106-1121`), drives the cursor with `scroll_to_party_menu_index`, presses A,
  then B until `BATTLEMAINCB2` (`:1133-1140`).
- **V6. MEASURED: the action-cursor bug has never fired in the batch corpora.** 0 of the 4,520 debug-log files
  (4,492 `.log`, 28 `.txt`) under the main checkout's `sandbox-pokebot/profiles/` contain `cursor 'gActionSelectionCursor'`.
  The control search for `KI-45: cursor` does find files, so the search works (the hits read, in two of them, are on
  `gMoveSelectionCursor`). ⇒ C1 is latent today and fixes no measured derail.
- **V7. `BattleType.Multi` (bit 6) and `InGamePartner` (bit 22) exist** (`battle_state.py:49`, `:65`).
- **V8. The `[TURN]` line logs each deciding battler's level and HP** (`battle_action_selection.py:453-541`).
- **V9. The Struggle loop presses A into battler 2's menu** (review S13-P1, refuter upheld): in `battle_action_use_move`
  (`:1207-1215`) the loop presses A while the main callback is `HandleTurnActionSelectionState` and checks battler 0's
  controller only. When battler 0 has no usable move, its menu never opens and battler 2 is asked next, so the loop
  commits battler 2's action blind. Today that is FIGHT (byte 2 = 0). After battler 2 has used an item, byte 2 is 1 and
  the loop would open battler 2's BAG.
- **Found along the way, NOT in this step's scope** (filed as KI-115, `#27-battlestructptr`): `gBattleStruct` is a
  4-byte POINTER and `read_symbol` does not dereference, so `battle_move_replacing.py:147` reads `gActionSelectionCursor[0]`
  as the move learner's party index and `battle_strategies/_util.py:93` reads `sLearningMoveTableID` as the run-attempt
  count (whose true offset is +0x6C, not +0x4C).

**The decomp** (pret/pokeemerald copies in the session scratchpad `decomp/`):
- **G1. A player's medicine applies AT SELECTION.** `ItemUseCB_Medicine` takes `gPlayerParty[gPartyMenu.slotId]`, runs
  `ExecuteTableBasedItemEffect_` and then `RemoveBagItem(item, 1)` (`party_menu.c:4396-4434`). HP and the bag count are
  final before the menu closes. An HP item on a full-HP or 0-HP target is refused ("won't have any effect") and nothing
  is consumed.
- **G2. The in-battle party menu lists the party in BATTLE ORDER** (`ChooseMonForInBattleItem` →
  `UpdatePartyToBattleOrder`, `party_menu.c:5780-5785`), and the cursor opens on slot 0 (`:524-525`). In a non-multi
  double the order is built at battle start as [left active, right active, the rest ascending] (`:5970-5983`).
  ⚠ Only positions 0 and 1 are invariant: a switch SWAPS positions, so the tail carries switch history (reviews M2/S13-P7,
  and MEASURED in S0-4). The multi's order is fixed at battle start ([0,3,1,2,4,5], `:5942-5955`) and rewritten by player
  switches (review M8).
- **G3. B on battler 2's action menu is refused after battler 0 chose a non-ball item** (`battle_controller_player.c:
  306-318`); after a move or switch it cancels battler 0's choice.

**Step 0, measured on the base code** (evidence file above):
- **S0-3.** `storyresume` fights Tate & Liza from the pinned `d13_tateliza.ss1` with production's strategy and prints
  `[TRAINER] … class=0x20(LEADER) … double=True two=False`. On seed 1, Zigzagoon (party 1) faints on turn 0 and the faint
  chooser sends Mightyena (party 4, PID `5C96EA9B`) to the RIGHT. Battler 0 is decided twice per turn: in a double the
  Fight menu opens later than `battle_action_use_move`'s 6-frame wait, the call returns early, the handler backs out with
  B and re-decides (benign today; the item flow's bag-open wait is bounded).
- **S0-4.** `*gBattleStruct + 0x60` is `battlerPartyOrders` (the offset derived from `include/battle.h` and CONFIRMED
  live): at turn 0 all four arrays decode to [0,1,2,3,4,5]; after a replacement (party 2 for fainted party 1) the two
  PLAYER arrays read [0,2,1,3,4,5] and the two opponent arrays are unchanged. `+0x58` is NOT a copy of
  `gBattlerPartyIndexes` ([0,0,0,0], then [0,0,1,0]), so it is not a self-check (review M7).
- **S0-5.** The pure policy replayed over the base code's decisions:
  - Route 123's first two-trainer double (`post_mtpyre.ss1`, the X-BASE1 run): party slots 0, 3 and 5 are fainted, so
    the actives are Sceptile (party 1, menu 0) and Swellow (party 2, menu 1). BOTH battlers discriminate from the first
    decision. The first act, at the DEFAULT fraction and under both worst-hit semantics, is **f3149372, turn 0, side 0,
    Sceptile 21/117, Hyper Potion**; its partner Swellow is at 18/109 (hurt, so the wrong-slot arms bind).
  - Tate & Liza (the S0-RESUME run): no act at the default 0.35 (turn 4's Sceptile 46/133 is refused by rule 3: the
    Potion's 20 is below the 73-HP hit). At `POKEBOT_HEAL_AT_FRACTION=0.8` the first act is **f3456183, turn 1, side 1,
    Mightyena 99/127, Potion** (both semantics), its partner Sceptile at 116/130.
- **S0-6.** The flag-unset baseline on `post_mtpyre.ss1` (X-BASE, base code, twice apart).

## 2. DECISIONS

- **D1. SCOPE.** The new path acts only in a battle with `Trainer` and `Double`, and with neither `Multi` nor
  `InGamePartner`. That covers Tate & Liza, the 32 rematches and the emergent two-trainer doubles.
  - The Space Center multi is OUT (it returns `super()`): the bot controls battler 0 only there, Steven's three
    Pokémon sit in `gPlayerParty[3..5]`, and it is measured low-value (0 losses of 16, 2 of 24, 4 of 56 across three
    batches; `d13_recon_history.md` §5). A later item.
  - Wild battles already return early (`story_mode.py:823`).
- **D2. SELF-ONLY.** Each battler may use an item only on its OWN active Pokémon. Healing the partner is a later
  extension. Why:
  - a request, its target and its verdict are then one Pokémon, so identity stays simple (rule 3);
  - two heals on one Pokémon in one turn cannot happen, which closes V3's stale-HP hazard;
  - the singles meaning is kept: heal the Pokémon that is fighting.
- **D3. PER-POKÉMON STATE, KEYED BY (PID, species).** The singles fields that describe ONE Pokémon become a ledger per
  Pokémon in doubles: `_hp_seen`, `_worst_hit`, `_hp_when_item_requested`, `_status_when_item_requested`,
  `_item_qty_when_requested`.
  - So a partner's decision can no longer clear a pending request silently (`story_mode.py:974`, recon W8).
  - `_worst_hit` becomes the requester's own largest drop between its consecutive decisions (the damage it took in one
    turn from both foes). ⚠ On a turn where it healed, that drop is masked (the heal lands at selection, after
    `_hp_seen` recorded the pre-heal HP; review M9). The singles path has the same flaw; it is recorded, not fixed.
  - These stay PER BATTLE, shared by both battlers: `_item_uses` (the cap of 4), `_index_space_flipped` (the one retry),
    `_items_ineffective` (the disable), `_r27_verdict`.
  - Mechanism: `_maybe_use_item` gains `side=0`, and its two `left_battler` reads (`:832`, `:908`) select by `side`. A
    doubles wrapper swaps the requester's ledger into those five attributes around the call and back out in a `finally`.
    With `side=0` and no wrapper, the singles path is the same code, so every singles gate keeps its meaning.
- **D4. THE IDENTITY GUARD in the executor** (flag `1`, doubles only; rule 3 and rule 7):
  - before the bag opens: the intended PID, raw from `gPlayerParty[target_index]` (normal order); and the SELF binding,
    `target_index == u16 gBattlerPartyIndexes[g]` (review M5, kept as defence in depth);
  - at `PARTY_MENU`, after the KI-101 remap and the cursor scroll: `slot = gPartyMenu[9]`; the guard passes only if
    `0 <= slot < gPlayerPartyCount` (review M10: Cancel is 7, and 6-7 read past the party) and the PID at
    `gPlayerParty[slot]` (menu order while the menu is open, G2) equals the intended PID. It reads the cursor's ACTUAL
    slot, never `_menu_slot` (review F8);
  - on a mismatch, **no A press**: unwind with B (the existing loop), log `a_pressed=0`, use no item. The A press itself
    is logged either way (review S13-P4);
  - ⇒ **with the guard, "the bag count dropped" implies "the intended Pokémon took the item"**, which closes the
    adversary's F3 (a wrong slot in a double is often the LIVING partner, which consumes the item silently);
  - the bound after a refusal: HP items go through the existing retry-once / disable (`story_mode.py:976-987`). Status
    cures would be bounded only by the 4-use cap (review S13-P2), which is one reason for D10.
- **D5. THE FLAG is read per call** (`os.environ`), in the strategy and the executor (the design v2 A-N6 exception, like
  `POKEBOT_R27_KEYITEMS`: the Mossdeep harness drivers build the strategy directly and never run `reset_per_run_state`).
  - `unset` (or any other value): `decide_turn_in_double_battle` returns `super()` with no read and no log line.
  - `observe`: `super()` plus one `[DBLITEM-OBS]` line per decision (C5). **It never calls `_maybe_use_item` or
    `_r27_key_gate`** (they change state and log `[ITEM]` / `[KEYBATTLE]`; review S13-P3/F5). Its `would` comes from the
    pure policy (C6), fed by its own per-PID HP tracker, which is the ONE piece of state observe keeps: a separate object,
    `_dbl_obs`, excluded from the gate's no-state-change row. Its key-class field is computed by the pure
    `trainer_identity.key_battle_verdict`, with no cache and no log.
  - `1`: act (D1-D4, D10).
- **D6. COMPOSITION WITH `POKEBOT_R27_KEYITEMS`: ORTHOGONAL.** `DOUBLEITEMS` makes a double follow the singles item
  policy, including whatever `KEYITEMS` decides. With `KEYITEMS=1`, only key classes get items (Tate & Liza is LEADER;
  `_r27_key_gate` reads opponent B when `TwoOpponents`, `story_mode.py:6383-6388`). With it unset, every trainer double
  gets items, as every trainer single does today. Rejected: making `DOUBLEITEMS` require `KEYITEMS` (the kit's D2 rule);
  two flags that each mean one thing compose more safely. Step 14 runs BOTH ON. Arm P-KEY is the composition control.
- **D7. C1, THE BATTLER-AWARE ACTION CURSOR, IS UNCONDITIONAL.** `scroll_to_battle_action(action_index,
  is_right_side_pokemon=False)` passes the side to `_select_in_menu`. `battle_action_use_move`, `battle_action_use_item`
  and RotateLead pass `battler_index > 1`; run and Safari stay on battler 0.
  - With the flag unset both bytes are 0 at every call (a trainer double only ever FIGHTs), so C1 is inert by
    construction (reviews F4/S13-P5, refuted to nits: the flag-unset A/B stays, worded as a no-crash regression check).
  - It is exercised where it matters by P-ON (battler 2's FIGHT with byte 0 = 1) and T-ON (battler 2's BAG, then its
    next FIGHT with byte 2 = 1).
  - A fault proves it load-bearing: `POKEBOT_R27_FAULT_DBL_CURSOR0`, read inside `battle_menuing.py`, restores byte 0.
  - It touches an upstream-mirrored file ⇒ a `DIVERGENCE-LOG` entry when it is promoted.
- **D8. THE RULE-10 MEASUREMENT IS THE ON ARM'S MENU LINE.** The conversion production acts on is the executor's remap
  after the bag opens; its ground truth is the PID found at the cursor's actual menu slot beside the intended PID
  (`[DBLITEM] menu`), and the guard enforces it. `observe` adds an OFFSET self-check only (review F7): it reads
  `battlerPartyOrders[g]` raw at `u32(*gBattleStruct) + 0x60 + 3g` and reports `bpo_pos`, the requester's position in
  it, which must equal `side` (the active positions are invariant, G2). A row DISCRIMINATES only when the requester's
  party index differs from `side`; where they are equal, a wrong index space gives the same answer.
- **D9. FAIL OPEN.** Every new strategy step is wrapped like `decide_turn` (`story_mode.py:796-803`): an exception gives
  the parent's attack. Telemetry never raises. The guard's own read failing counts as a mismatch (it backs out; review
  S13-P6).
- **D10. HP ITEMS ONLY IN DOUBLES (v1).** The doubles path passes only items with `parameter > 0` to the policy; a status
  cure (Awakening, Full Heal, Ice Heal, parameter 0) is not requested in a double. Why: a guard refusal on a cure is not
  counted by the retry/disable logic (D4), and v1's proof is about identity, which an HP change shows directly. Cures in
  doubles are a later extension (with a refusal counter). Tate & Liza's Hypnosis makes a cure reachable there, so this
  is a real, recorded limit.
- **D11. THE STRUGGLE LOOP STOPS AT BATTLER 2'S MENU** (V9; flag `1`, doubles, `battler_index == 0`): the loop returns
  without pressing once `get_battle_controller_callback(2)` is `HandleInputChooseAction`, and the handler makes battler
  2's own decision. Behind the flag, so the flag-unset path keeps today's blind FIGHT byte for byte.

## 3. THE CODE, CHANGE BY CHANGE

- **C1** (`modules/battle_menuing.py`, `modules/battle_action_selection.py`): D7, including the fault read.
- **C2** (`story_mode.py`, `StoryItemBattleStrategy`): `decide_turn_in_double_battle(battle_state, battler_index)`.
  - Flag unset → `return super()...` as the first statement after the flag test. Out of D1's scope → `super()`.
  - `observe` → C5's line (D5), then `super()`.
  - `1` → the ledger swap (D3) and `_maybe_use_item(battle_state, side=battler_index, doubles=True)` inside `try`;
    `None` or an exception → `super()`. `doubles=True` applies D10's HP-only filter.
- **C3** (`story_mode.py`): `_maybe_use_item(self, battle_state, side=0, doubles=False)`. The two `left_battler` reads
  select by `side`; D10's filter applies only when `doubles`. Nothing else changes; the key gate stays where gate A1
  pins it.
- **C4** (`battle_action_selection.py`): `battle_action_use_item(battle_state, item, target_index=0, battler_index=0)`;
  the `UseItem` case passes the handler's `battler_index`; D4's guard and the `after` read run when the flag is `1` and
  the battle is a double. D11's exit in `battle_action_use_move`.
- **C5, telemetry, only with the flag set** (so the flag-unset run adds no line). Raw reads only (`read_symbol` /
  `read_bytes`), NEVER `get_battle_state()`: a second call in one frame can return a stale party order (KI-108) and
  would make the executor's own remap read the stale object; `probe_dmgaudit.py`'s NH-gbs-count row counts those calls
  (review F9). Strides (review M3): `gBattlerPartyIndexes` is u16[4], so battler g is at byte `2g`.
  - `[DBLITEM-OBS] side= g= turn= me=<species>#<pid8> P= hp=cur/max would=<item|-> why=<reason> key=<0|1|?> worst=
    uses= bpo=<3 bytes hex> bpo_pos= disc=<0|1> cur=<4 bytes>`;
  - `[DBLITEM] use side= g= item= target=<species>#<pid8> P= hp=cur/max self=<0|1>` when acting;
  - `[DBLITEM] menu g= battler_in_menu= layout= slot= menu_pid= intended_pid= ok=<0|1> a_pressed=<0|1>`;
  - `[DBLITEM] after g= target=<pid8> hp=<before>-><after> status1=<before>-><after> partner=<pid8>
    hp=<before>-><after> <item>=<before>-><after> healed=<gBattleResults[3] before>-><after>`, read at the executor's
    first `BATTLEMAINCB2` frame (the `returned-to-battle` stage, before any move runs), from raw `gPlayerParty` (field
    order again) and the save block (reviews M4/F2). **The arms grade HP and the bag on THIS line, never on the next
    `[TURN]`** (the turn's damage lands after the heal).
- **C6, the pure logic, in `modules/story/double_items.py`** (no emulator imports): `mode(env)`, `in_scope(type_bits)`,
  `active_positions(order)` (positions 0-1 only), `decode_bpo(3 bytes)`, `guard_ok(intended, menu, slot, count)`,
  `self_ok(target_index, g, battler_party_indexes)`, `ledger_key(pid, species)`, `hp_only(options)`, and
  `heal_options(bag_items, reserve_filter)` for observe, pinned to what `_maybe_use_item` passes by a PARITY row.
- **C7, faults, read inside production code** (named `POKEBOT_R27_FAULT_DBL_*`, each registered in `29`):
  - `CURSOR0`: C1 reads byte 0 for every battler;
  - `WRONGSLOT`: the executor drives the cursor to the PARTNER's menu slot (1 − side);
  - `NOGUARD`: skip D4's PID check (the A is pressed whatever the PID).

## 4. LEVERS

- **None are state writes.** `--set-party-hp` and `--set-bag-item`, proposed before Step 0, are DROPPED: the natural
  trajectories discriminate (S0-3, S0-5).
- `POKEBOT_HEAL_AT_FRACTION=0.8` (it exists, `story_mode.py:1079`) in EVERY Tate & Liza arm, OFF included. It is inert
  in the flag-unset arms (a double never reaches `_maybe_use_item` there, and the fixture meets no single before the
  fight).
- `POKEBOT_R27_KEYITEMS=1` in every Tate & Liza arm (Tate & Liza is key, so it permits); unset in every Route 123 arm
  except P-KEY.

## 5. STEP 0 (done; `evidence/2026-09-30-doubleitems13-STEP0.txt`)

S0-1 pin `d13_tateliza.ss1` (md5 `1d8f604694b9`); S0-2 its party and bag; S0-3 the driver (`storyresume`); S0-4 the
`battlerPartyOrders` offset; S0-5 the acting discriminators; S0-6 X-BASE on `post_mtpyre.ss1` (PINNED `80602159694b`),
twice apart. The frames below are run-relative to nothing: they are the logs' own frame counters, which the seeded
trajectories reproduce.

## 6. THE ARMS (seed 1, `storyresume`; values from Step 0; filed as predictions BEFORE any code)

**Family P — `post_mtpyre.ss1`, KEYITEMS unset (except P-KEY), the default fraction, no lever.** The first double starts
f3148510; its first decision is f3149372.

| Arm | Flags | Frames | What it must show |
|---|---|---|---|
| X-BASE ×2 | base code, unset | 90,000 | Equal to each other (D15: else a third). The baseline. |
| P-OFF ×2 | build, unset | 90,000 | Equal to each other and to X-BASE on every line: the flag-unset build changes nothing (a no-crash regression check of C1-C4). 0 `DBLITEM` lines. |
| P-OBS | `observe` | 30,000 | = P-OFF on every line without `DBLITEM`. One OBS line per double decision; `bpo_pos = side` on every row; `disc=1` on every row of the first double. Its first `would≠-` row: f3149372, side 0, Sceptile, Hyper Potion. |
| P-ON | `1` | 30,000 | = P-OFF up to f3149372. There: side 0 uses the Hyper Potion on Sceptile (`self=1`); `menu … ok=1 a_pressed=1`, slot 0, `menu_pid` = Sceptile's; `after`: Sceptile 21→117, Swellow unchanged, Hyper Potion 1→0, `healed` +1. Battler 2's same-turn FIGHT (byte 0 = 1 there) completes with no KI-45. No item reaches another PID in the run. |
| P-KEY | `1` + `KEYITEMS=1` | 30,000 | No item (a `[KEYBATTLE] … key=False` line; the classes are not key). Gameplay = P-OFF. |
| P-CUR | `1` + `FAULT_DBL_CURSOR0` | 30,000 | The item lands as in P-ON; battler 2's FIGHT scroll then raises KI-45: `cursor 'gActionSelectionCursor' never reached index 0 … (last read: 1)`. |
| P-SLOT | `1` + `FAULT_DBL_WRONGSLOT` | 30,000 | At f3149372: `menu … slot=1 … ok=0 a_pressed=0`; `after`: Swellow 18→18, Sceptile 21→21, Hyper Potion 1→1. Then the retry (a second refusal) and the disable; no item is used in the battle. |
| P-NOG | `1` + `WRONGSLOT` + `NOGUARD` | 30,000 | `a_pressed=1` on slot 1: `after`: Swellow 18→109, Sceptile 21→21, Hyper Potion 1→0. ⇒ the guard is load-bearing (and the old bag verdict logs `✔ CONSUMED`, blind to the wrong target). |

**Family T — `d13_tateliza.ss1`, KEYITEMS=1 and HEAL_AT_FRACTION=0.8 in every arm.** The battle starts f3452776.

| Arm | Flags | Frames | What it must show |
|---|---|---|---|
| T-OFF ×2 | unset | 20,000 | Equal to each other; equal to S0-RESUME on every line through the battle's end. |
| T-OBS | `observe` | 20,000 | = T-OFF on every line without `DBLITEM`; `bpo_pos = side` on every row; `disc=1` on side 1's rows from turn 1; first `would≠-`: f3456183, side 1, Mightyena, Potion; `key=1`. |
| T-ON | `1` | 20,000 | = T-OFF up to f3456183. There: side 1 uses the Potion on Mightyena (party 4, menu 1); `menu … slot=1 … ok=1 a_pressed=1`; `after`: Mightyena 99→119, Sceptile unchanged, Potion 1→0. Battler 2's BAG scroll converges (C1), and its next FIGHT (byte 2 = 1) completes with no KI-45 (graded if battler 2 is asked again; declared ABSENT, not passed, if it faints first). A `[KEYBATTLE] … key=True` line. |

- **Decision rule (D15):** the OFF runs of a family must match each other first, else a third run; a lone divergent run
  is re-run, never graded. KI-112 (`#27-determinism`) is live.
- A fault arm's run may derail after its graded event (P-CUR's KI-45 is a recoverable story derail under StoryMode); only
  the lines named are graded.

## 7. THE GATE (`tools/story-dev/probe_double_items.py`, appended to `run_gates.py` after an adversarial mutant pass)

- **Pure rows (C6):** mode parsing; scope (Trainer+Double; Multi, InGamePartner, wild and single each out);
  `active_positions` on orders with a swapped tail; the nibble decode; `guard_ok` (match, mismatch, slot 6, slot 7,
  count); `self_ok` with the u16 stride (a byte-stride read must fail); `ledger_key`; `hp_only`.
- **Production rows (fakes):**
  - flag unset → the `super()` result, the instance `__dict__` equal before and after, no log;
  - `observe` → the `super()` result, `__dict__` equal except `_dbl_obs`, exactly one OBS line, `_maybe_use_item` and
    `_r27_key_gate` never called;
  - the observe PARITY row: `heal_options` equals what `_maybe_use_item` passes to `choose_healing_item`;
  - `1`: side 0 heals the left Pokémon, side 1 the right, never the partner; a status-only bag gives no item (D10);
  - a partner's decision leaves the requester's pending verdict intact;
  - Multi → `super()`; `KEYITEMS=1` against a non-key double → no item;
  - `scroll_to_battle_action(1, True)` reads byte 2 (fake `read_symbol`); the executor passes the battler;
  - executor positive control: matching PIDs → the cursor is driven to the requester's slot and A is pressed
    (`WRONGSLOT` reddens it); a scroll that stops short → the guard refuses (it reads `slotId`); a PID mismatch → no A;
  - D11: controller 2 enters `HandleInputChooseAction` mid-loop → no A after that frame.
- **Existing gates that must stay green unchanged:** `repro_item_noop_detector.py` (#60), `repro_key_battle_items.py`
  (its A1 AST pin), `repro_battle_items.py`, `repro_ki46_action_selection_bound.py`, `probe_dmgaudit.py` (NH-gbs-count),
  `repro_no_silent_except.py` (review F9).
- **Faults and mutants:** every C7 fault, plus a mutant per rule, each reddening exactly its own rows.

## 8. RESIDUALS AND FOUND-ALONG-THE-WAY

- The multi (D1), partner heals (D2) and status cures in doubles (D10) are later items.
- D3's masked worst hit on a heal turn (review M9), shared with singles.
- **KI-115 / `#27-battlestructptr`**: the two `gBattleStruct` misreads (§1).
- **`#27-itemprobes`**: step 14's `probe_item_index_space.py` matches a line no current code prints; it must be fixed
  before step 14.
- `[KEYBATTLE]` is logged only inside `_maybe_use_item`, so today a LEADER double prints `[TRAINER]` but no
  `[KEYBATTLE]`. With `DOUBLEITEMS=1` it prints. Step 14's audit must expect that.
- The spec's stale cites (`story_mode.py:518` → `:563`; `battle_script_commands.c:5625-5626` → `:5626-5627`).

## 9. THE REVIEW, AND HOW EACH FINDING WAS FOLDED (`d13_design_review.md`, verbatim)

- **Upheld, folded:**
  - proof F1 (blocker) and mechanics M1, safety S13-P4: the wrong-slot arms need a hurt partner. Both families have one
    at the act (Swellow 18/109; Sceptile 116/130), pre-registered; the A press is now logged.
  - safety S13-P1 (blocker → should-fix): V9 and D11.
  - M3: strides and the battler space are written into C5/D4; S0-4's live reading separates the player's arrays from
    the opponent's.
  - M4/F2: the `after` line; every HP and bag grade reads it.
  - F3: the C1 criterion is split by side (P-ON: battler 2's FIGHT after battler 0's BAG; T-ON: battler 2's BAG, then
    its next FIGHT).
  - F5/S13-P3: observe's own tracker, the parity row, no `_maybe_use_item` / `_r27_key_gate` call.
  - F6: the item KIND is predicted (HP on both acts); D10.
  - F7: D8 reworded; `agree` became `bpo_pos = side`, an offset self-check.
  - F8: the executor rows.
- **Refuted to nits, folded anyway where cheap:** M2 and S13-P7 (G2 restated), M5 (the self binding added), S13-P2 (D4's
  bound corrected; D10), S13-P5 and F4 (the flag-unset A/B kept, worded as a no-crash check; F4's natural P family
  adopted).
- **Nits:** M6 (P-CUR predicted as KI-45), M7 (S0-4), M8 (G2), M9 (D3), M10 (D4), M11 (KI-115), S13-P6 (D9), F9 (§7).

## 10. OPEN QUESTIONS

None blocks this step. D1, D2, D6 and D10 are the author's calls, recorded in `06` with their rejected alternatives.
