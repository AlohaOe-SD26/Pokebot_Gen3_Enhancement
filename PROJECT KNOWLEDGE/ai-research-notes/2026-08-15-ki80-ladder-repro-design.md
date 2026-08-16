# KI-80 repro driver — DESIGN v2, after an adversarial refutation pass (2026-08-15)

> ⛔ **v1 OF THIS NOTE WAS REFUTED ON ITS CENTRAL SAFETY CLAIM.** v2 is a full rewrite rather than a
> correction bolted onto v1, because "correct text sitting beside stale text" is this project's most
> frequently-logged doc failure. What the refutation killed is recorded in §9, not left implicit.
> Every number is **measured live**, and the driver **re-measures all of them at run start**.

## 1. What is under test

`story_mode.py:1899` computes one boolean carrying two unrelated meanings:

```python
grass_is_fodder = ("grass" not in cfg) or (wild_max is not None and wild_max + 8 < team_max)
```

and `:1901` makes it the **sole** gate on `_boss_plan_is_hopeless` (`:1907`) and `_counter_ladder`
(`:1914`). ⇒ **giving a boss a training patch silently removes its KI-23 counter machinery.**

**The subject is the GATE — which branch production takes — and nothing else.**

## 2. Why it is cheap to drive

`_prepare_for_fight` gates its expensive proactive half behind `if losses < 2:` (`:1823`). The repro
seeds **8** losses, so control runs from `:1817` to the branch at `:1877` with **no yield, no travel,
no button press** (verified line-by-line by the refutation pass, §9 item 1).

⛔ **But the path does NOT end at the discriminating print.** See §5 — that error is what v1 got
wrong, and it is the whole reason this note has a v2.

## 3. THREE arms

Two arms would only show *"a `grass` key removes the ladder"* — true but weak, and blind to whether
the key's PRESENCE or the level ARITHMETIC did it. The defect is the conflation, so the experiment
must separate the two halves of the disjunction.

| arm | `cfg["grass"]` | `wild_max` | `grass_is_fodder` | expected branch |
|---|---|---|---|---|
| `NOGRASS` | absent | n/a | **True** (1st disjunct) | `_counter_ladder` |
| `GRASS_FODDER` | Route 102 | **4** | **True** (2nd disjunct) | `_counter_ladder` |
| `GRASS_STRONG` | Route 119 (Winona's real patch) | **27** | **False** | plain escalation `:1948` |

`NOGRASS` vs `GRASS_STRONG` is the regression. `GRASS_FODDER` is the control that gives it meaning:
a patch that IS fodder KEEPS the machinery, so the discriminator is the arithmetic, not the key.

‼ **Arms 1 and 2 are observationally IDENTICAL by design** — same branch, same `hopeless/needed`,
same error. That sameness is the finding, not a defect. But it means the driver cannot *observe*
that arm 2 really carried a `grass` key; it must ASSERT the cfg it passed and say so plainly.

## 4. Fixture, and why the two previously-named saves are both unusable

`saves/batch2_run04_wedge.ss1` — measured 2026-08-15 (`probe_credible_answer.py`): `NO_ANSWER`,
party **Marshtomp L28 / Swellow L28 / Mightyena L28 / Nincada L10**, so `team_max = 28`.

* ⛔ NOT `fortree_gym_wedge.ss1` — Castform scores 160 ≥ 75, **condition 7 fails**, never hopeless.
* ⛔ NOT `ch13_fortree_door.ss1` — Blaziken L39 makes `27 + 8 = 35 < 39` **True**, so
  `grass_is_fodder` is True in *both* arms: **condition 9 fails and the A/B is vacuous.**
* ⚠ NOT `batch3_run03_wedge.ss1` — NO_ANSWER but `team_max = 35`, exactly on the boundary
  (`35 < 35` false by one level). One level-up silently flips the experiment.

`batch2_run04_wedge` clears condition 9 with **7 levels of margin**.

‼ **Not Winona-era** (badges 123). Fine for a DECISION-level A/B, but ⛔ **do not report it as a
faithful Winona scenario** — and note the refutation's correction: `_counter_catch_message` →
`_counter_area_allowed` → `is_map_reachable` → `_live_capability` **does read badge flags and HM
moves** (`region_reach.py:200-222`), so W3's *candidate list* is badge-dependent. The claim
"nothing on the path reads a badge" was **false**; the branch decision still does not.

## 5. ⛔⛔ TERMINATION — the thing v1 got wrong, and the fix

A generator's first `next()` runs **to the first `yield`**, and `:1949`'s print is **not** the end of
the arm. On `GRASS_STRONG`, control continues: `:1961` → `:1976` (`"grass" in cfg`, so not skipped) →
`:2024 local_patch_is_fodder(27, 28, 12)` = **False** (`training_areas.py:519`: `27+12=39 < 28`), so
the `need = []` escape at `:2080` never fires → `:2087 yield from train_team(...)`. Inside
`train_team`, **before its first yield**: `early_game.py:2003 set_swap_train(True)` (a module global,
undone only by a `finally` that has not run) and, via `_rotate_lead_safely` →
`higher_level_actions.py:403` → `menuing.py:308`, **`context.emulator.press_button("Start")`**.

⇒ v1's three headline claims — *"one `next()` per arm"*, *"nothing mutates game state"*, *"no arm
presses a button"* — were **all false on the one arm that carries the regression**, and v1's
invariance snapshot (map, position, pids, `team_max`) was structurally incapable of seeing any of it.

**THE FIX: terminate each arm AT its discriminator, from inside the console proxy.**
The recorder raises a private sentinel the instant it sees a terminal signature, which unwinds
`_prepare_for_fight` at `:1948` — **before** `:1961`, and therefore before `train_team` exists.

Terminal signatures (each a distinct, NAMED outcome — never a catch-all):
| signature substring | line | means |
|---|---|---|
| `training harder before` | `:1949` | plain escalation — **the regression** |
| `boss-training mode` | `:1927` | `hopeless` came back False — see §9 item 4 |
| `boss attempts KO'd nothing` | `:1932` | `boss_teaches` False — the seed is wrong |

The ladder arms need no tripwire: the spy returns False, so production raises `BotModeError` at
`:1920` and the arm ends there on its own.

⛔ **Belt and braces regardless:** every arm runs under `try: … finally: gen.close()`, so if a
signature is ever missed, `train_team`'s own `finally: set_swap_train(False)` still runs.
⛔ **And `GRASS_STRONG` runs LAST**, so any leak it does spring cannot contaminate the others.

**Stated scope limit:** the arm is deliberately cut off at the decision. Nothing downstream of the
branch is exercised, and this driver claims nothing about it.

## 6. Seeded state, against KI-80's 9 conditions

`key = MapRSE.FORTREE_CITY_GYM.value` (= `(12, 1)`); `LOSSES = 8`; history `[(1,1) … (8,1)]`.

| # | condition | satisfied by |
|---|---|---|
| 1 | `losses >= 2` (`:1877`) | 8 |
| 2 | `grass_is_fodder` (`:1899`) | the arm variable — the thing under test |
| 3 | `boss_teaches` — `any(kos >= 1)` of the last two (`:1900`) | flat 1s ‼ `any`, not `all` |
| 4 | `losses >= 6` `PLATEAU_LOSS_THRESHOLD` (`:1046`) | 8 |
| 5 | `len(history) >= 6` (`:1512`) | 8 |
| 6 | `max(last 3) <= max(prev 3)` (`:1514-1517`) | flat 1s ⇒ `1 > 1` is False |
| 7 | no credible answer (`eff >= 2.0` **and** `bp*eff*stab >= 75`) | measured NO_ANSWER |
| 8 | `"ace_types" in cfg` (`:1557`) | `("Dragon","Flying")` |
| 9 | `team_max <= wild_max + 8` | **28 <= 35**, 7 levels of margin |

Verified independently: `sorted()` on `(seq, kos)` tuples orders by `seq`, and `_loss_seq` is a
single global counter, so `[-2:]` really is "the two most recent". Seeding ONE of `cfg["keys"]` is
sufficient — `:1817` and `:1894` both union over the whole list.

⛔ **The 12 ceiling.** At `losses >= 12` **and** `len(history) >= 12`, `hard_plateau` goes True and
the answer loop iterates an **empty tuple** (`:1573`), so `hopeless` is True *regardless of the
party* — right answer, wrong reason, and the A/B would go green proving nothing. **8 is inside 6–11.**

## 7. Observability — witnesses that must AGREE

* **W1 — console proxy.** Records and forwards every `print` **reached through the module global**
  (`story_mode.py:21`), and raises the §5 sentinel on a terminal signature. ⚠ **Not "every print":**
  `_counter_area_allowed:902` and `_log_story_event:3742` re-import `console` function-locally and
  bypass the proxy. Harmless here; stated because the headline must carry the caveat.
* **W2 — `_counter_ladder` spy.** Records entry with the `losses`/`needed` it was handed, returns
  `False` without hunting. ⛔ **It MUST be a generator function** (`:1914` is `yield from`); a plain
  `def … return False` makes `yield from False` raise `TypeError`, which would read as "the run
  errored" rather than "the ladder was reached".
* **W3 — the `BotModeError`.** Its message embeds the `losses` **production actually used**, so the
  seed is checked against production's arithmetic instead of the driver's belief.
* **W4 — a DELEGATING observer on `_boss_plan_is_hopeless`.** Calls the real method and records
  `(hopeless, needed)`. ⛔ Must capture the original **bound** method before rebinding, or it
  recurses for ever. It never substitutes a verdict.

⛔ **Disagreement between witnesses is a FAIL, not a tie-break.**

## 8. Anti-vacuity and hygiene, enforced at run start

Before grading, the driver measures from the running game and refuses on any failure:

1. `team_max` from `get_party()` — reported, never assumed.
2. `wild_max` for Route 119 and Route 102 via production's own `get_wild_encounters_for_map`.
   ⛔ **Assert both are `not None` explicitly** — `:1891` swallows the failure with a bare
   `except: pass`, leaving `wild_max = None`, which makes `grass_is_fodder` **False** and would turn
   `GRASS_FODDER` silently into a second `GRASS_STRONG`.
3. `wild119 + 8 >= team_max` **and** `wild102 + 8 < team_max` — the arms really do differ.
4. `random.seed(...)` fixed and logged: `:1819`/`:1941` are unseeded in production and change how
   far an arm would run.
5. The cfg replica is cross-checked against the **real `winona_fight` literal parsed from the source
   AST** (`story_mode.py:3532`) — key set, `band`, `ace_types`, `ace_level` — because it is
   method-local and cannot be imported. ⛔ Include `"heal"`: `:1993` reads it.
6. Invariance per arm, widened past v1's: map, position, **ordered** party `(pid, species)`,
   `team_max`, `swap_train_active()`, `context.message`, and `_training_unreachable`.

If any check fails the driver prints **`ACCEPTANCE: FAIL — the fixture no longer discriminates`**
and stops. ‼ It must never print a quiet PASS over arms that cannot differ — that is the mistake
logged twice on 2026-08-15.

## 9. What the refutation pass changed (v1 → v2)

1. **SURVIVED** — no yield between `:1806` and `:1949` at `losses = 8`; `:1823` really is skipped.
   Refined: only `GRASS_STRONG` reaches `:1949`; the ladder arms delegate at `:1914`.
2. **SURVIVED** — `StoryMode()` constructs cleanly; every `self.*` on the path is initialised by
   `reset_per_run_state()`. Caveat: a booted emulator + loaded save IS required (`get_party()`).
3. ⛔ **REFUTED — the killer.** See §5. v1's cheapness claim and v1's safety net were the same
   claim, and both failed on the regression arm.
4. **SURVIVED** — the seeding satisfies conditions 1, 3, 4, 5, 6. Added: `_boss_plan_is_hopeless`'s
   blanket `except` (`:1608`) returns `(False, [])`, i.e. *not hopeless*, which sends the ladder arms
   to the **boss-training-mode** print — a THIRD signature v1 never named. Now named, in §5.
5. **PARTLY REFUTED** — the proxy is safe (no non-`print` uses of `console`), but "records every
   print" was false. Corrected in §7.
6. **SURVIVED, independently corroborated.** Route 119 land max = **27** and Route 102 = **4**,
   read from `pret/pokeemerald`'s `wild_encounters.json` — matching `training_areas.py:50`'s
   `(ROUTE119, (21,109), (24,27))`. The arms genuinely differ.
7. Also fixed: W2 must be a generator; W4 must capture the bound method; seed `random`; assert
   `wild_max is not None`; include `"heal"` in the replica; run `GRASS_STRONG` last.

## 10. Expected matrix, and what the fix must do to it

**Today (coupled):** `NOGRASS` → ladder · `GRASS_FODDER` → ladder · `GRASS_STRONG` → plain escalation.
**After decoupling:** all three → ladder.

`POKEBOT_KI80_DECOUPLED=1` flips the expectation, so the *same* driver is the before-and-after
evidence KI-80 requires. ⛔ The "before" run is unrepeatable once the fix lands — **run and commit it
first** (the rule KI-79's three-point A/B established).

## 11. What this driver deliberately does NOT do

* It does not edit `story_mode.py`; the arms are cfg dicts built in the driver, so
  `repro_boss_grass_gate.py` (suite #24) stays green and the structural gate and the behavioural
  repro do not fight each other.
* It does not hunt, travel, train, or battle — §5 cuts every arm off at its decision.
* It proves the gate behaves as KI-80 describes. It proves **nothing** about KI-80's *fix*.
