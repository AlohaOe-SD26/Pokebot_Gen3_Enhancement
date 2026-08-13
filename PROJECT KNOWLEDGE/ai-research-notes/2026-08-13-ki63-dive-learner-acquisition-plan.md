# KI-63 — ACQUIRING A REAL DIVE LEARNER: measured plan, and a correction to our own handoff

> **2026-08-13.** Everything numbered below was MEASURED by `probe_dive_learner_plan.py` (new,
> read-only, four positive controls, all PASS) or verified by me directly in the code. This is the
> spec for the next build; nothing here has been driven yet.

## Why this matters

`--driver ch21dive` proved the whole Mossdeep → Seafloor Cavern dive route the same day — but it
**injected Dive with a debug write**. KI-63 (nobody can learn Dive, party 6/6) is the one thing
still standing between the bot and §Ch21, and it is also step 3 of the Regi arc.

---

## ‼ CORRECTION 1 — OUR OWN HANDOFF NAMES A DEPOSIT PATH THAT CANNOT DO THE JOB

`04-HANDOFF.md` / KI-54 say:

> *"Freeing one slot reuses `withdraw_from_box:331-355`, which is live-proven and deposits exactly
> ONE mon."*

**That is wrong for freeing a slot BEFORE a catch**, and I verified it directly:

```python
# modules/story/pc_trip.py:314-315   (the FIRST thing withdraw_from_box does)
target = find_in_box(pids)
if target is None:
    return
```

At step (a) nothing has been caught, so there is no PID in the box, `find_in_box` returns `None`,
and **the function returns having done nothing.** The deposit block at :331-355 is only reachable
as a *side effect* of withdrawing an already-boxed, already-known Pokémon. The logic pattern is
proven; the function is not callable for this purpose.

**And the obvious alternative is gated OFF.** `deposit_dead_weight_if_worth_it`
(`pc_trip.py:153-208`) *is* a standalone one-deposit primitive with the right mechanics — but it
routes through `plan_deposits`, whose first act is:

```python
# modules/story/pc_trip.py:83
if _os.environ.get("POKEBOT_PC_ROTATION", "0").strip() not in ("1", "true", "yes"):
    return {"deposit": [], "withdraw": [], "reasons": {}, "worth_it": False}
```

`POKEBOT_PC_ROTATION` is pinned at **0** and is **measured harmful** (~1 team member/run, a 5.4%
VOID batch). So calling it today prints nothing, deposits nothing, and returns cleanly — **a silent
no-op.**

⇒ **Neither existing function frees a slot pre-catch. A new one must be written.** Narrow, ungated,
capped at exactly one deposit, built from `team_policy.find_dead_weight` +
`interact_with_pc([PCAction.deposit_pokemon_to_box(mon)])` — mirroring what `withdraw_from_box`
already does internally, which is the proven mechanism.

‼ **How this would have failed:** the driver calls the obvious-looking function, nothing happens,
party stays 6, and the next `ensure_hm_learner` raises *"the party is full"* — sending the reader
after `ensure_hm_learner` when the bug is two calls upstream.

## ‼ CORRECTION 2 — DEPOSIT-FIRST IS THE WRONG ORDER

`ensure_hm_learner` checks `hm_learner_slot(item)` at `early_game.py:4338-4340`, **before** the
party-full check at `:4342-4348`. So an unconditional deposit at step (a) pays a PC trip and costs
a team member even in the case where no catch was ever needed.

**Correct order: try first, deposit only on the specific failure.**

---

## THE MEASURED FACTS

| question | measured answer |
|---|---|
| Poké Balls at `post_dive.ss1` | **19** (Poké 16 / Premier 1 / Great 1 / Master 1) |
| Money | **$54,334**, `affordable_poke_balls()` = 269 |
| `_hm_hunting_grounds(HM08)` | **`[(ROUTE117, (31,16), ['Marill'])]`** — the doc was right |
| control: same call for HM03 (Surf) | 6 grounds ⇒ a 1-ground answer for Dive is a real fact, not a broken lookup |
| Marill | learns **Dive AND Surf**, catch rate 190, but **10% of Route 117's land table, L13 flat** |
| Spheal (`SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM`) | **50%**, **L26-32**, catch rate **255**, Dive AND Surf |
| `find_dead_weight` victim | **slot 3, Skitty L17** |
| ‼ sole-HM-carrier exemption | **Zigzagoon (Surf) and Sceptile (Rock Smash/Strength) are EXEMPT** — the Surf carrier is spared |
| Mossdeep → ROUTE117 | paths, **1,055 waypoints** (8 map hops) |
| Mossdeep → Shoal Cave | ✗ different warp region (233 vs 0) — but its **door at ROUTE125 (22,19) paths in 103** |

**⇒ `#24-ballstarve`'s premise does not hold at this anchor.** It was filed from a mid-game,
Surf-era batch; ball starvation may still be real THERE. It is recorded in the punch list as
*not closed on this evidence*.

## ‼ THE STRATEGIC CHOICE THIS FORCES — do not make it silently

The chain works today, but only toward **Route 117: 1,055 waypoints for a 10%, L13 Marill.**
Shoal Cave's Spheal is better on *every* axis — 5× the slot rate, catch rate 255 vs 190, L26-32 vs
L13, and 103 waypoints + one door instead of 1,055.

⛔ **But it must NOT simply be added to `TRAINING_GRASS`.** Measured previously with the real
function: a Shoal Cave row becomes the **highest band in the table** and flips `best_training_area`
for every team from ~L30 up. `_hm_hunting_grounds` iterates `TRAINING_GRASS` — so the two uses are
coupled, and a "small data addition" silently changes where the whole bot trains.

⇒ The clean answer is a **separate HM-hunting-ground table** that `_hm_hunting_grounds` also
consults, leaving `TRAINING_GRASS` (and therefore `best_training_area`) untouched.
**This is a design decision with a measured blast radius — worth surfacing, not assuming.**

⚠ Also unmeasured: **no Shoal Cave tile has been two-way swept**, so the ground is not promotable
yet. This project demotes statically-derived grounds (the Route 114 lesson).

---

## THE BUILD ORDER (adversarially reviewed before writing any code)

1. `ensure_hm_learner(HM08)` **first** — it may return a slot with no catch needed.
2. On the specific *"the party is full"* `BotModeError`: run a **new** `deposit_one_dead_weight()`
   — ungated, capped at one, `find_dead_weight` + `interact_with_pc`, inheriting the sole-HM-carrier
   exemption for free. **Not** `withdraw_from_box`, **not** `deposit_dead_weight_if_worth_it`.
3. Retry `ensure_hm_learner(HM08)` — this performs the bounded hunt (40,000-frame deadline, raises
   loudly on timeout) and the catch.
4. Before teaching: check whether the returned slot **already knows Dive** (skip if so — otherwise
   `items.py:196-197` raises a confusing *"already knows it"* on the happy path), and compute
   `move_index_to_replace` yourself. ‼ `teach_hm_or_tm`'s default is **slot index 3**, with no
   expendability logic; `early_game.teach_hm_move` has the smart picker (`_is_hm_slot` → prefer
   0-power → else weakest) and should be preferred.
5. ‼ **Assert by re-reading the party, never by a clean return.** `teach_hm_or_tm` is a generator
   with **no return value and no post-teach verification**. The only trustworthy gate is the
   mon's actual moveset.
   ⛔ **CORRECTION 2026-08-13 — `can_dive()` IS NOT IMPORTABLE, so do not assert with it.** It is
   a **nested closure inside `calculate_path`** (`map_path.py:690`, `nonlocal _can_dive`), not a
   module-level function. KI-68's *"`can_dive()` exists; zero callers"* therefore describes a
   private helper, not an API — and an earlier draft of this very note told the builder to call
   it. Caught by the import-symbol check **before** the run, not by a failed one. Compute the
   same predicate instead, verbatim:
   ```python
   context.rom.is_rse and get_event_flag("BADGE07_GET") and get_party().has_pokemon_with_move("Dive")
   ```

### Predicted failure modes worth pre-registering
* the deposit no-op above (**most likely first-run failure**);
* the hunt silently degrading if balls run out mid-hunt — `story_mode.py:2154-2168` re-checks
  `balls > 1` *every encounter* and just stops catching, then fights for up to 11 minutes before
  the timeout raises. **Log the ball count at hunt start and end** or this is indistinguishable
  from bad luck;
* a caught L13 Marill is **36 levels below the team** — it is an HM slave, and `find_dead_weight`
  will want to deposit it on the next trip unless the sole-carrier exemption covers it.

## ✅ WHAT IS ALREADY SAFE — verified, not assumed

**Teaching Dive cannot overwrite Surf.** `early_game.py:4473-4480` filters out any move whose
`tm_hm.name` starts with `"HM"`, and `:4485-4495` raises loudly if *every* slot is an HM rather
than starting a teach it cannot finish. `teach_hm_or_tm` (`items.py:188-205`) raises on the same
condition. The self-inflicted "strand the bot mid-ocean by forgetting Surf" scenario is
structurally prevented at both layers.
