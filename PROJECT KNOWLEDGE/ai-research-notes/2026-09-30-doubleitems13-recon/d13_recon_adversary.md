# 2026-09-30 — design v2 step 13 (KB-2, healing items in DOUBLE battles): recon angle `adversary`, verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (a subagent's return, read-only recon; workflow `doubleitems13-recon`). Every load-bearing claim is verified by the author before the design relies on it.

# Step 13 (KB-2, items in DOUBLE battles): adversarial review of the spec

This is a note, not a source of truth. I did not modify any file, did not run the emulator, and ran no git command that changes state. I read the decomp copies with `gh api` at pret/pokeemerald master (fetched 2026-09-30). Code paths are relative to `C:/Remote Projects/pokebot-wt-ch24`.

**Headline: the spec's claims about the game hold, but the spec misses one certain blocker.** The menu driver reads battler 0's action cursor when battler 2 is choosing. So the first turn where battler 0 uses an item and battler 2 attacks will fault. That blocker is invisible at the Space Center, because the player controls only battler 0 there. It is certain to fire at Tate & Liza and in every leader rematch.

## A. The spec's claims, checked

| Spec claim | Verdict | Evidence |
|---|---|---|
| "attacks only (`story_mode.py:518`)" | **STALE CITE, the claim itself holds (nit)** | The only `decide_turn_in_double_battle` is now `sandbox-pokebot/plugins/custom_modes/story_mode.py:563`, on `LevelUpTravelBattleStrategy`. Its trainer branch attacks only (:573-613). `StoryItemBattleStrategy` (:739-1215) overrides only `decide_turn` (:796-803). Doubles are routed to `decide_turn_in_double_battle` at `modules/battle_action_selection.py:202-203` and :212. The 06:4427 record cites `story_mode.py:417`, which is also stale. |
| Items are usable at the Space Center multi (`battle_main.c:4222`) | **VERIFIED** | `src/battle_main.c:4221-4225` blocks items only for LINK, FRONTIER_NO_PYRAMID, EREADER_TRAINER and RECORDED_LINK. The Steven battle's flags are TRAINER, DOUBLE, TWO_OPPONENTS, MULTI and INGAME_PARTNER (`src/battle_tower.c:2123`), none of the blocked ones. ⚠ The player controls **only battler 0** there. Battler 2 is the partner AI (`src/battle_controllers.c:137-148`; `src/battle_controller_player_partner.c:1502-1506`), so this battle never runs the bot's battler-2 path (see F1 and F6). |
| All 32 rematches are doubles | **VERIFIED** | `src/data/trainers.h:9244-9616`: ROXANNE_2-5 through JUAN_2-5 all have `doubleBattle = TRUE`. `TATE_AND_LIZA_1` is at :3256 (TRUE, class LEADER, 4 Hyper Potions). The other `_1` leaders are FALSE (:3184-3268). `doubleBattle` sits at +0x18 (`include/data.h:88`). The OR into the battle flags is at `src/battle_main.c:2072`. Rematches use `trainerbattle_rematch_double` with a need-two-Pokémon text (`data/maps/RustboroCity_Gym/scripts.inc:37`). |
| "step 6's singles-only gate gives no items in a leader rematch" | **Conclusion right, cause misstated (nit, but it matters for step 14)** | The gate is not the cause. `_maybe_use_item` is never called in any double, whatever the flag says (routing cited above). So Tate & Liza gets no items **today, with `POKEBOT_R27_KEYITEMS` OFF**. Consequence for step 14: `[KEYBATTLE]` is logged only from `_r27_key_gate` inside `_maybe_use_item` (story_mode.py:6361-6400). A LEADER-class double will therefore have a `[TRAINER]` line but no `[KEYBATTLE]` line. Step 14's audit ("Arm B's `[KEYBATTLE]` lines must agree…") must expect those to be missing. |
| ×2 pay (`battle_script_commands.c:5625-5626`) | **VERIFIED, cite off by one (nit)** | The DOUBLE branch is at `src/battle_script_commands.c:5626-5627`. Line :5625 is the TWO_OPPONENTS formula. TWO_OPPONENTS is tested first (:5624), so the Space Center and two-trainer doubles are **summed** (:5638-5639), not doubled. Only single-ID doubles (Tate & Liza, rematches) pay ×2. |
| "A Space Center fixture is UNVERIFIED" | **STALE (should-fix)** | `tools/story-dev/saves/at_steven_2f.ss1` exists and is tracked. `--driver spacecenter2` and `--driver ki66faint` drive the real multi from it (story_harness.py:3771-3777, :3916-3935). It is **unlisted** in `FIXTURES.md5` and is re-captured on every spacecenter1 PASS (`CH19A_CAPTURE` defaults on, story_harness.py:3761-3765). It needs a pinned COPY, not discovery. |
| "Pin a Tate & Liza save first: `in_mossdeep_gym.ss1` is VOLATILE" | **VERIFIED, but it misses the better anchor** | `in_mossdeep_gym.ss1` is VOLATILE at `FIXTURES.md5:37`. `at_mossdeep_leaders.ss1` stands at the leaders with the puzzle already solved (story_harness.py:3378-3381). It is unlisted and is re-captured on every ch18b PASS (`CH18B_CAPTURE` defaults to "1", :3363-3366). Pin a copy of it; that skips the 117-step puzzle. |

## B. Traps in a naive "call the singles item logic from `decide_turn_in_double_battle`"

### F1 — BLOCKER: battler 2's action menu is driven with battler 0's cursor

**Verified.**
- `scroll_to_battle_action(i)` calls `_select_in_menu("gActionSelectionCursor", i)` without the third-byte flag (`modules/battle_menuing.py:90-91`). So it always compares against **byte 0** (:55-65).
- The game keeps one cursor per battler, indexed by the active battler:
  - A reads the active battler's cursor: `src/battle_controller_player.c:249`.
  - The D-pad changes it: :268-303.
  - Each battler's action menu reopens at its own saved position: :2586.
  - The cursor resets only when a Pokémon switches in (:2190) or at battle start (`src/battle_controllers.c:52`). The only reset message ever sent is `RESET_MOVE_SELECTION` (`src/battle_script_commands.c:7802`).
- Upstream already handles the per-battler MOVE cursor (`scroll_to_move(move_index, battler_index > 1)`, `battle_action_selection.py`, called from `battle_action_use_move` at :1190). It missed the ACTION cursor.
- `battle_action_use_item` has no battler parameter at all (:1016, called at :598, and it calls `scroll_to_battle_action(1)` at :1034). `battle_action_use_move` calls `scroll_to_battle_action(0)` at :1198.

**What goes wrong.** It works today only because both battlers always choose FIGHT, so byte 0 is 0.
- **Battler 0 uses an item, battler 2 attacks.** Byte 0 is 1, so the loop presses Left. That does nothing to battler 2's cursor, which is already at 0. After 60 steps it raises KI-45 (`battle_menuing.py:36-51`).
  - `MossdeepBadgeMode` (story_harness.py:3372) and `SpaceCenter2Mode` (:3771) do not declare `handles_battle_faults`. It appears only at story_harness.py:250 and :20419. So `request_mode_recovery` returns False (`modules/battle_fault.py:34-44`), the loop raises `BotModeError`, and the run drops to Manual and hangs (the KI-90 comment, `battle_action_selection.py:~1222-1226`).
  - Under StoryMode the same fault becomes a mid-leader-fight derail.
- **Battler 2 uses an item after battler 0 attacks.** Byte 0 is 0, so the loop presses Right forever and hits the same KI-45.
- **Inferred, not traced:** once battler 2 has used an item, its own cursor stays at 1. On the next turn a FIGHT request reads byte 0 (0), matches, and presses A on battler 2's real cursor, which opens the **bag**. `battle_action_use_move`'s no-move-menu loop then mashes A until the turn moves on. That can spend an item outside every policy and gate.
- **Inferred, not traced:** if the item flow's A lands on FIGHT instead, the three A presses in the bag-open retry (:1043-1056) commit a **move**, while `_item_uses`, `_hp_when_item_requested` and `_item_qty_when_requested` were already recorded (story_mode.py:1146-1159). The verdict then reads "not consumed" twice and sets `_items_ineffective`. **The ON arm silently reads as OFF**, which would look like a refutation of a true finding.

**Fix.** Pass the battler id (0 or 2) into `scroll_to_battle_action`, and use it in both `battle_action_use_move` and `battle_action_use_item`. The RotateLead path (:773, the KI-96 path) has the same bug class. These are upstream-mirrored files, so this needs a DIVERGENCE-LOG entry. It is a shared path, so it needs an A/B on the ordinary double (both battlers FIGHT, which should be byte-identical) per CLAUDE.md rule 9. **This must come before the flag.**

### F2 — BLOCKER: the wrong battler's HP and identity

**Verified.** `_maybe_use_item` hard-codes `mon = battle_state.own_side.left_battler` (story_mode.py:832). The KI-101 judge reads `own_side.left_battler` (:908). Called for strategy index 1, it heals the **left** mon on battler 2's turn. If the left battler is absent, it returns None and the right mon is never healed.

**Fix.** Pass the acting battler into the method. v1 rule: **each battler heals only its own mon.** That rule also neutralises F4 and F6. Judge by (PID, species), not by `party_index` (CLAUDE.md rule 3). Gate #60 (`repro_item_noop_detector.py`, run_gates.py:795-808) and `repro_key_battle_items.py` build a `FakeBattleState` with only `left_battler` (:159). They need a right-battler row with a mutant, or they stay vacuous for the new path.

### F3 — SHOULD-FIX (a blocker for grading): the bag-count verdict cannot see a wrong target in a double

**Verified mechanism.** The KI-101 verdict treats "bag count dropped" as success (story_mode.py:951-971). The heal and `RemoveBagItem` both happen at party-menu time (`src/party_menu.c:4416`, :4434; `src/pokemon.c:5082-5095`). A non-Revive item is refused on a 0-HP mon (`pokemon.c:5056-5060`). In singles a wrong slot was usually a fainted mon and was refused. In a double, the wrong slot is often the **living partner**, so the item is consumed and the verdict logs "✔ CONSUMED".

**Fix.** Grade the A/B by **which PID's HP rose** (party HP read before and after "target-chosen"), never by the bag count (CLAUDE.md rule 7).

### F4 — SHOULD-FIX: battler 2 decides on a snapshot taken before battler 0's item

**Verified.** `handle_battle_action_selection` refreshes `battle_state` only **after** the new battler's decision (:577-579, after the decide at :212). The snapshot battler 2 sees was taken during battler 0's iteration, before its item flow at :598. The item applies at menu time, so battler 2 sees pre-heal HP. The comment at :574-576 claims the refresh handles potions; it does, but only for the *action*, not the *decision*.

- With cross-targeting, battler 2 heals the same mon again. If that mon is now full, the item is refused, the verdict flips, and items end up disabled for the battle.
- Spending the **last item twice is NOT a hazard**. `get_item_bag()` re-reads in each new frame, and `ItemBag.__eq__` compares every byte (`modules/items.py:541-557`, :330-332; `state_cache.py:205-210`). Battler 2's decision is in a later frame, so its bag read is fresh.

**Fix.** Use the self-only rule (F2), or read HP fresh by PID inside the decision without `get_battle_state()` (see F9).

### F5 — SHOULD-FIX: where the flag is read

**Verified.** The A/B drivers build the strategy directly and are not StoryMode (story_harness.py:3408, :3660, :3816). §2 says flags are read in `reset_per_run_state` (story_mode.py:2265). Read there, `POKEBOT_R27_DOUBLEITEMS` would be invisible in those drivers, and ON would equal OFF.

**Fix.**
- Read it per strategy instance inside the method, as step 6 does, and list it as a third §2 exception (`[A-N6]`).
- Keep OFF byte-identical.
- State the interaction: with KEYITEMS OFF, items fire in every trainer double, including emergent two-trainer doubles (story_mode.py:564-567). That matches today's pre-RULING-27 singles behaviour, but must be said. The batch must run DOUBLEITEMS only together with KEYITEMS.

### F6 — SHOULD-FIX: the multi hides F1, and a wrong index there lands on Steven's Pokémon

- **Verified:** the multi's battle order is fixed at `[0,3,1,2,4,5]` (`src/party_menu.c:5942-5955`). This was measured in our own log `ch19d.log` f37745 (`modules/battle_strategies/default.py:17-22`).
- **Verified:** menu slots 1, 4 and 5 are the partner's (`party_menu.c:5806-5807`). The item-use selection checks only for eggs (:1309-1317).
- `own_side.right_battler` is Steven's Pokémon. `choose_status_or_revive_item`'s alive-count includes Steven's three (story_mode.py:1128); that is a nit, since Revive is off.
- The partner is AI-driven, so the bot's battler-2 path is never asked there.

**Fix.**
- Use a Space Center arm only as an *additional* arm. It can never be the arm that proves F1 is fixed.
- Exclude ally Pokémon by original trainer (`ally_party_indices`, default.py:12), never by position.

### F7 — SHOULD-FIX: per-battle state is shared between two Pokémon

**Verified.**
- `_worst_hit` is one number for the whole battle (story_mode.py:838-840). A frail Pokémon's big hit makes rule 3 (`battle_items.py:92-95`) refuse heals for its partner.
- `_hp_seen` is keyed by `party_index` (:841), not PID.
- The cure verdict is dropped when the next decision belongs to the other battler (:866).
- `MAX_ITEM_USES_PER_BATTLE = 4` (`battle_items.py:49`) is shared across both battlers. That is acceptable, but say so.

**Fix.** Key these by PID. State whether the bound is per battle or per Pokémon.

### F8 — NIT, but it is a CLAUDE.md rule 10 trap: two index spaces for "battler"

**Verified.** The strategy gets `battler_index` 0 or 1 (`_interface.py:80-87`). The driver uses battler ids 0 and 2 (:201, :211), which the game uses for the cursors and controllers. `get_battle_controller_callback(1)` is the **opponent**. The probe must log both.

### F9 — SHOULD-FIX: where KI-108 bites in doubles

**Verified mechanism** (the KI-108 write-up at `05-KNOWN-ISSUES.md:3066-3090`; `battle_state.py:249-262`, :808-826; `state_cache.py:293-298`).
- The driver's remap at :1115 is correct only while it is the first `get_battle_state()` call in its frame.
- Any probe line, or new code, that calls `get_battle_state()` in `battle_action_use_item` **before** :1115 in that frame makes the driver read a stale order. That changes the behaviour being observed.
- A probe that calls it **after** :1115 in that frame gets the old cached object. Its "ground truth" order is then wrong and shows a false mismatch.
- `current_turn` has the same staleness.

**Fix.** Probe reads must use plain `read_symbol` calls only, the step 11 dmgaudit precedent (story_mode.py:6584).
- ⚠ `gBattleStruct` is a 4-byte **pointer** (`pokeemerald.sym:181`; `src/battle_main.c:221`), and `read_symbol` does not dereference (`modules/memory.py:66`). Do not copy the house reads at `_util.py:93` or `battle_move_replacing.py:147`. **Inferred (not live-checked):** both read memory just past the pointer instead of the struct; they are the same upstream and not filed anywhere.

### F10 — SHOULD-FIX: the observe-only probe must not call `_maybe_use_item`

**Verified.** That method mutates state (:1146-1164) and logs `[ITEM] using` (:1166-1174) and `[KEYBATTLE]` (:6399). That breaks §2's "OFF byte-identical in every `[ITEM]` line".

**Fix.** Call only the pure `choose_healing_item` and `choose_status_or_revive_item` on copies. Use its own log category and its own flag.

### F11 — SHOULD-FIX: the grading tools are blind

**Verified.**
- `probe_item_index_space.py:44` looks for `landed using the (\w+)-order index`. The current log lines are `✔ landed (KI-101: …` (story_mode.py:1029) and `✔ CONSUMED` (:966), so it counts **0 landings**. Step 14 names it as an acceptance instrument.
- `probe_boss_healing.py:61`'s `[TURN]` pattern ends at `\s*$`, so it misses statused foes. The `[TURN]` foe is always `opponent.left_battler` (`battle_action_selection.py:458`).

### F12 — Refuted or safe, with evidence (do not spend time on these)

- **The game makes an item forfeit the partner's attack:** false. The item takes only the using battler's action (`battle_main.c:4221-4237`). The partner is then prompted (:4168).
- **B at battler 2's menu cancels battler 0's item:** false. It is inert for a non-ball item (`battle_controller_player.c:320-327`), so the bot's trailing B presses (:1137-1139) cannot undo it. After a *move*, B does cancel back to battler 0 (`battle_main.c:4282-4327`); that is harmless because the bot re-decides.
- **A refused item hangs:** no. The game returns to action choice (`battle_main.c:4406-4410`), and the two-attempt verdict bounds the retries.
- **Existing hang risk:** the unbounded B loop at :1137 is the one pre-existing one. It is not new in doubles.

## C. The probe's discriminator

### Where to log

- **At the decision** (inside the new override, still returning today's attack), using plain reads only:
  - frame, and turn (`gBattleResults`+0x13);
  - strategy index (0/1) **and** battler id (0/2);
  - controller callbacks for battlers 0 and 2;
  - raw `gActionSelectionCursor[0..3]` (this catches F1);
  - raw `gBattlerPartyIndexes`;
  - raw `gBattlePartyCurrentOrder`;
  - `battlerPartyOrders[battler]`, which is exactly what bag-open copies in (`battle_main.c:4236`; `battle_controller_player.c:2653-2663`).
    - Read it through the dereferenced pointer at `*gBattleStruct + 0x60 + 3*battler`. That offset is **inferred** from `include/battle.h:354-381`.
    - Self-check: `+0x58` must equal `gBattlerPartyIndexes`. If it does not, the row is void.
  - For the acting Pokémon and its partner: (PID, species, party index, HP/max) from `gBattleMons`, plus the snapshot's HP for the same PID (quantifies F4);
  - what the pure policy would choose for self and for partner.
- **Two coordinates per target:**
  - the predicted menu slot (the target's position in `battlerPartyOrders[battler]`);
  - the wrong-space slot (the party index used directly as a slot).
- **Premise conjuncts:** the order is not the identity AND the predicted slot differs from the party index. A row that fails either is **VACUOUS**. Precedent: the ki47oor "Swp" arm, story_harness.py:238-243.
- **Ground truth for the ON arm:** at the `PARTY_MENU` frame, the PID at `gPlayerParty[_menu_slot]` after `UpdatePartyToBattleOrder` (`party_menu.c:5781-5785`, :6078-6086), compared with the intended PID. Then which PID's HP rose.

### Where the two spaces actually differ

| Arm | Fixture | Order | What it discriminates |
|---|---|---|---|
| **D1** (strongest) | Pinned copy of `at_mossdeep_leaders.ss1`, with party slot 0 set to 0 HP **out of battle** (Ki66's 2-byte write precedent, story_harness.py:3935-3945) | The game sends slots 1 and 2 (`battle_controllers.c:589-630`). Order `12 03 45` = [1,2,0,…] (`party_menu.c:5957-5969`) | Battler 0 = party 1, menu 0. A wrong space on battler 0's self-heal lands on party 2, the **living partner**: consumed and invisible to the bag verdict (F3). Differs from turn 1. |
| **D2** (natural) | Same anchor, unstaged | Its docstring *predicts*, but has not measured, that Zigzagoon L15 in slot 1 faints early (story_harness.py:3384-3389). `SwitchPartyOrder` in a double (`battle_main.c:4086-4105`) then gives `02 13 45` | The replacement party 2 sits at menu 1. A wrong space hits the fainted slot 2 and is refused (visible to the bag verdict). |
| **D3** | Pinned copy of `at_steven_2f.ss1` with the ki66faint staging | `03 12 45`, measured. After a lead faint, **inferred** `13 02 45` | A wrong index lands on Steven's slot 1. That slot is likely full, so the item is refused. This arm cannot exercise F1. |

**Vacuous arms:**
- Tate & Liza turn 1 with healthy slots 0 and 1 (the order is the identity);
- any heal of the multi's lead (party 0 is at menu 0).

**Guard for D1:** the harness chapter might heal before the fight (**inferred risk**), so assert the order `120345` at battle start.

**For the A/B:** the policy may never fire at 35%. `POKEBOT_HEAL_AT_FRACTION` (story_mode.py:1079-1088) is the existing lever; predict with the pure policy before choosing an arm.
