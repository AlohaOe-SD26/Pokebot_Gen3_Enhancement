# (P4) THE END-TO-END SLUGMA/WINONA REPRO — DESIGN, with the premises it REFUTED

> **Status: DESIGN ONLY, not built.** Produced 2026-08-15 by a Claude planning agent given the
> failure chain, the KI-71 constraint and the "no stochastic catch" rule. ‼ **This is a NOTE, not
> truth** (`00-READ-THIS-FIRST.md`). Every claim below carries a `file:line`; verify the
> load-bearing ones before building on them. Its corrections to MY OWN brief are the reason it is
> worth keeping — see §1.

## 1. ⛔ FOUR OF MY SEVEN PREMISES WERE WRONG. Two would have made the test meaningless.

| my premise | verdict |
|---|---|
| the heal's withdraw is gated `if _pids:` at `higher_level_actions.py:336` | ❌ **STALE — I changed it MYSELF the day before.** The decision moved to `counter_withdraw_outcome(_pids)` (`:337`), gated `if _should_withdraw:` (`:343`). A plan grepping `if _pids:` finds nothing. *I briefed an agent from memory of code I had already rewritten.* |
| `post_dive.ss1` party slot 3 is Wailmer L40 | ❌ **Wrong twice.** Slot 3 natively holds **Skitty L17**; the Wailmer is the `ch20dive` FIXTURE (`story_harness.py:4820-4834`). ⛔ **And `post_dive.ss1` is POST-WINONA (Sceptile L49) — the Winona rung can never fire from it**, so the whole repro would have been vacuous. |
| snapshot at `counter_hunt.py:470-489` | ⚠ off by one at the boundary: the pair is `:476-477`; `arm()` is `:490`. Matters for §3. |
| `box_counter_pid` has one caller, `counter_hunt.py:542` | ✅ confirmed. Also: `_hunted_counter_pids` is READ at `story_mode.py:3153/3187/3357/3408/3541` via `_lead_best_matchup(hunted_pids=…)` — an unused assertion surface. |
| KI-71 clears the stack | ✅ confirmed, precisely `modules/main.py:146`. |
| no box-write debug utility; box=80 bytes | ✅ confirmed — **but the gap is ~6 lines, not a project.** See §2. |

## 2. HOW TO GET A SLUGMA INTO A LIVE BOX — recommended: a new `debug_write_box_slot()`

The read path is entirely in `modules/pokemon_storage.py` and a writer just mirrors it:
* **Base address** `:145-149` — non-RS: `offset = unpack_uint32(read_symbol("gPokemonStoragePtr"))`.
  ⛔ RS differs (uses `get_symbol("gPokemonStorage")` directly) — refuse on RS.
* **Layout** `:83-101` — mons at `0x4 + (box * 30 * 80) + (slot * 80)`, 80 bytes each.
* ✅ **No count field to keep in sync**: occupancy is DERIVED (`slots` appends only when
  `not pokemon.is_empty`, `:97-99`; `pokemon_count` sums that, `:103-105`).
* ✅ **No encryption to re-implement**: `debug_create_pokemon` already emits a valid record
  (checksum `debug_utilities.py:364`, substruct reorder + XOR `:379-388`), and `Pokemon` holds
  "the 100-byte (party) or 80-byte (box)" record (`pokemon.py:911-912`).
* **Write primitive**: `context.emulator.write_bytes` (`libmgba.py:432-451`). ⛔ `write_symbol` is
  NOT usable — storage sits behind a pointer.
⇒ `write_bytes(base + 0x4 + box*2400 + slot*80, pokemon.data[:80])`. Write to the ACTIVE box's
`first_empty_slot_index` (`:44-52`) to mirror `CopyMonToPC`.

**Rejected: inject into the party then drive the real deposit.** It is MORE fabrication, not less —
the bug needs *party full AND Slugma boxed simultaneously*, so you must inject 7 mons' worth,
deposit, then inject a 6th. The resulting bytes are identical, and the deposit path is already
live-proven (`deposited=True` in four logs). **Rejected: catch a real Slugma** — the handoff forbids
depending on a stochastic catch, and the Fortree→Fiery-Path leg is a measured pathing failure
(`03-PUNCH-LIST.md:642-645`).

## 3. ‼‼ THE SINGLE MOST LIKELY WAY THIS SHIPS BROKEN — `exclude_pids` self-defeat

`counter_hunt.py:476-477` snapshots `before_box_pids = _box_pids()`, and `:542` passes it as
`exclude_pids`; `:284-285` skips any PID in that set. **A Slugma injected BEFORE line 477 is
filtered out and `box_counter_pid` returns `None` in BOTH arms** — ARM A "reproduces" the bug for
entirely the wrong reason and ARM B fails. The tempting fix (pass an empty exclude set) deletes the
production guard from the test.
⇒ **Inject strictly AFTER the snapshot**, and **assert `slugma_pid not in before_box_pids`**,
printing both. If the driver replicates the tail rather than driving `hunt()`: snapshot
`_box_pids()` first, THEN inject, THEN call `box_counter_pid(needed, exclude_pids=<snapshot>)`.

## 4. THE A/B — a PERMANENT env hook, read INSIDE the function

Precedent inside production modules: `POKEBOT_LEADCANTBATTLE_A` (`battle_strategies/default.py:328-333`),
`POKEBOT_HMTEACH_POSTLEARN_A` (`early_game.py:4982-4989`) — *"'the error stopped' is not proof a fix
worked; an arm that reproduces the bug on request is."*
* **ARM B** (unset): the move loop `counter_hunt.py:288-300` runs → returns the Slugma's PID.
* **ARM A** (`POKEBOT_BOXCOUNTER_TYPEONLY_A=1`): skip the move loop, leaving the type test
  `:286-287` → returns `None`.
⛔ Read the var **inside** the function (`default.py:333`), never at import — `training_areas.py:432`
is the anti-pattern: an import-time read is unresettable and ignores a driver that sets it later.
✅ **Gate the hook itself** in `repro_box_counter_move_test.py`, which today fault-injects by
RE-IMPLEMENTING type-only against fakes — so the real hook could rot unnoticed.

## 5. ACCEPTANCE — identity only, and ⛔ counts CANNOT work here

**Measured**: on a SUCCESSFUL withdraw every count is unchanged —
`party_before=6 party_after=6 box_before=2 box_after=2` (`harness_withdraw3.log:467`), because the
make-room deposit (`pc_trip.py:437`) cancels the withdraw (`:441`). *A count assertion cannot pass
even when the bot is right.* Grade the ordered chain, every step an identity:
1. fixture honesty via production readers: species/level/`knows_move("Rock Throw")`/PID, and
   ‼ **types ∩ needed == ∅** (Slugma is pure Fire) or the move branch is never measured;
2. `slugma_pid not in before_box_pids`;
3. `box_counter_pid(...) == slugma_pid` — equality, never `is not None`;
4. `_hunted_counter_pids == {slugma_pid}`, populated by production (`story_mode.py:1748-1750`);
5. after the real heal: PID in party **and** `contains_pokemon` now False — proving it MOVED;
6. the withdrawn mon still knows Rock Throw;
7. two POSITIVE outcomes: `_lead_best_matchup(["Flying"], hunted_pids=…)` puts the PID in slot 0
   (the `#24-leadcounter` surface that reported `hunted_pids=0` on 684 decisions), and a SECOND
   full heal in which the withdraw must NO-OP;
8. REPORTED-NOT-GRADED: the gym leg (an L15 Slugma likely loses to Altaria L33).
⛔ **Never `_story_spin` for liveness in Fortree** — grass-free town, a documented false
`HANG CONFIRMED` (`story_harness.py:4363-4367`).

## 6. ARM A UNDER KI-71 — two stages, externally graded

Stage 1 (graded, cannot derail): call `box_counter_pid` directly under the fault and print the
verdict — so ARM A *does* emit a RESULT for its decisive claim. Stage 2 (ungraded, may derail):
print a PRE-RISK attribution line in the shape of `ch20room9`'s (`story_harness.py:6640-6654`) then
drive the real heal. ✅ **The `_piggyback_report` SKIP text is ARM A's positive evidence**, not an
absence — it names `_hunted_counter_pids` and the Slugma shape (`higher_level_actions.py:85-89`).

## 7. ANCHOR AND COST

⛔ **SUPERSEDED BY MEASUREMENT (2026-08-15, same day) — USE `ch13_fortree_door.ss1`, NOT
`fortree_gym_wedge.ss1`.** Both were probed: same era (badges 12345, Winona unbeaten), both a FULL
party of 6 — but the wedge save sits **INSIDE** `FORTREE_CITY_GYM (4,19)` while `ch13_fortree_door`
is on `ROUTE120 (13,16)`, outside. Stage 2 drives a Pokémon Center heal; starting inside the gym
adds a gym-exit leg that is pure risk for a test about the PC.
✅✅ **And `ch13_fortree_door.ss1` carries the bug's own fixture for free: a REAL
`Shedinja L30` and `Ninjask L29` BOTH with `pid=42207D6F`** (`--driver partypids`). Stage 2 can
assert against the genuine twins instead of injecting them.
⛔ **It also refutes a detail this note repeats from KI-78:** the twin is NOT always the later slot
— here Shedinja is slot 2 and Ninjask slot 3. The decomp claim is about the moment of CREATION;
party order changes afterwards (`reorder_party()` ships and is driven). No test may rely on order.
⚠ Its box already holds one Castform, so a "sole candidate" control must account for that.

The original recommendation follows, kept for its cost estimate, which still stands:


**`saves/fortree_gym_wedge.ss1`** — the FORTREE anchor (`03-PUNCH-LIST.md:630`), and its team was
measured driving *"10 Winona attempts without converging … no super-effective answer to Flying"*
(`:1414-1418`), i.e. exactly the `_boss_plan_is_hopeless` precondition. `PokemonCenter.FortreeCity`
is in town (`map_data.py:1534`). Closest measured cost: `boxwithdraw` did TWO full heals with PC
round-trips in ~24,841 driven frames. Budget `--frames 400000`. Matrix: {ARM A, ARM B} ×
{sandbox, custom}.

## 8. THE OTHER RISKS (condensed — the full dozen are in the agent's report)

2. **A broken fixture reads as the bug** — `box_counter_pid`'s blanket `except: return None`
   (`:302-303`) makes a decode failure indistinguishable from ARM A's expected `None`.
   ⇒ mandatory read-back control BEFORE either arm.
3. **Wrong species ⇒ vacuous** — Numel is Fire/**Ground**, would return at the TYPE branch in both
   arms and never touch the move branch.
4. **Bystander shadowing** — `box_counter_pid` returns the FIRST match in box order; any other
   qualifying mon makes ARM B green without the move branch. Hence `== slugma_pid`.
5. **Stale `state_cache`** — `get_pokemon_storage()` is cached per frame (`:142-143`); a same-frame
   read-back sees the PRE-write box. ⇒ **yield a frame after writing** (`story_harness.py:4851`).
7. ‼ **Hand-setting `_hunted_counter_pids`** — this is what `boxwithdraw` does
   (`story_harness.py:4326-4327`), and it bypasses `box_counter_pid` entirely. **That is precisely
   why the existing driver never caught this bug.** The PID must arrive only from production.
8. **ARM B failing for a `find_dead_weight` reason** (`pc_trip.py:437-455`) is a FIXTURE defect —
   abort with a distinct message, do not grade FAIL.
10. **Grading the wrong fork** — the harness defaults `--build sandbox` (`:34`).
11. **Hardcoding Winona's `needed` set** — derive it live and assert it equals
    `{"Rock","Ice","Dragon","Electric"}`, so a chart change is loud.

## 9. BUILD ORDER (the driver is steps 4-8 and is NOT started)

1. `debug_write_box_slot()` in `debug_utilities.py` — **BUILT 2026-08-15**, see the changelog.
2. `POKEBOT_BOXCOUNTER_TYPEONLY_A` hook in `box_counter_pid` — **BUILT 2026-08-15**.
3. extend `repro_box_counter_move_test.py` to flip the REAL hook — **BUILT 2026-08-15**.
4-8. the `boxcounter` driver, `--driver` registration, `compare_runs.py` pairing, the one-time
   natural-vs-injected byte-equivalence control, and the 4-run matrix — **NOT BUILT.**
