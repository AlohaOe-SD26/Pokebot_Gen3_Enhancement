# Team policy — build-ready design (2026-07-26)

> Follows `19-TEAM-BUILDING-DISCUSSION.md` (§5 personality, §6 what exists). That file is the
> DISCUSSION; this one is the DECISION. Verified against our code and
> `modules/data/emerald_obtainability.json`. Still not built — but this is buildable as written.

## 0. One open question CLOSED

`19-…§7.1` asked whether `modules/obtainability.py` counts event-only species as obtainable.
**It does not.** Mew(151), Lugia(249), Ho-Oh(250), Celebi(251), Jirachi(385), Deoxys(386) all
carry `kind:"event"` **and** `emerald_reachable:false`. So **`emerald_reachable` alone is a
sufficient filter** for the favourite pool — no extra event filter needed. The legendary pool
is the `static`/`roamer` reachables (Regis, Kyogre, Groudon, Rayquaza, Latias/Latios); filter
by species, not by `kind`, because Sudowoodo(185) is `static` and not legendary.

## 1. Catch policy — replaces the two hard conditions

> ‼ **SUPERSEDED FOR NEW SPECIES by the user ruling of 2026-07-31** (`06-DECISIONS-LOG.md`).
> The ruling is **"always catch new, WHEN IT IS CHEAP"**: an unseen species is caught on
> sight unless doing so would block progress. **There is NO roll for a new species.** The
> scored roll below was explicitly considered and rejected, for two reasons: the dex fills
> too slowly, and — the decisive one — a roll adds run-to-run variance to *every batch
> measurement*, which is expensive in a project whose main instrument is comparing batches.
>
> **What survives from this section:** the hard floors (they become the definition of
> "cheap", and are already implemented in `counter_hunt.resource_blocker()` — spare balls
> with the last one reserved, party space, never mid boss-prep), raising the party target
> 4 → 6, and box overflow. **What does not:** the `p = 0.30 + 0.50*curiosity …` roll, as the
> gate for catching a species the bot has never caught.
>
> The roll may still be the right model for **duplicates** (a second Zigzagoon that fills a
> type gap) — that was not what the user was asked about and is not ruled on. Keep it here
> for that purpose, and do not re-apply it to new species.

Drop the `BADGE01_GET` gate. Raise `_catch_team_target` 4 → 6, allow overflow to the box
(the shiny path already proves party-full→box works). Then a **scored roll behind hard floors**:

```
p = 0.30 + 0.50*curiosity
  + 0.40  (is a favourite)
  + 0.20  (fills a type gap vs the next known boss)
  - 0.25  (party already full: costs a box slot and a ball)
catch if rng.random() < p     # rng = Random(run_seed ^ dex ^ encounter_ordinal)
```

**Hard floors, checked BEFORE the roll, never randomised:** Pokédex received; `poke_balls > 1`;
not already in the party; per-chapter budget of 8 catch *attempts*.

Species novelty becomes a **bonus, not a gate** — a duplicate that fills a type gap is allowed.
Below `curiosity < 0.25` the bot catches only named targets (favourite / HM / counter) and
type-gap fillers.

**Why competence survives:** the deterministic paths — `_sufficiency_verdict`,
`_boss_plan_is_hopeless`, counter targets — never consult the roll. Variance comes from the
roll and the favourite; competence comes from the same gates as today.

## 2. Dead-weight predicate — new pure module `modules/story/team_policy.py`

`dead_weight(party_view, i, ctx) -> str | None` (a reason, or None). Fails if ANY of:

| test | rule | why |
|---|---|---|
| **Level** | `level < lead_level - 8` | `TRAIN_CATCHUP_GAP = 6` is where `_prepare_for_fight` STOPS training a mon, so >8 behind is **unrecoverable by construction** — exactly the observed L5 Cascoon in an L24 party |
| **Uselessness** | no move with `base_power > 0` **and** no HM move | the complement of `_battler_slots()` |
| **Contribution** | ≥6 battles sent out, 0 KOs, 0 survivals | catches the mon that is technically able but never contributes |

**Not** type redundancy in v1 — weakest signal, hardest to falsify offline.
**Exempt:** the favourite; and any mon that is the party's ONLY carrier of a learned HM.
**‼ AMENDED 2026-07-29 AFTER MEASUREMENT — the predicate is a FACT, not a deposit rule.**
Replaying this predicate over all **363 real badge-moment parties** from the `20260729-062040`
bundle showed it flags 3+ mons in **41%** of parties and would cut **132 observed four-mon
parties to a single Pokémon** — the "lone starter can't rotate" condition behind the Roxanne
party-menu hang (KI-8). **59% of parties would drop below three mons.** The predicate is not
wrong (the starter takes most of the XP, so the bench really is 10-20 levels behind by
mid-game) — but *"will never be caught up"* does not imply *"box it this visit"*.
`modules/story/team_policy.py` therefore separates them: `dead_weight()` states the fact;
`rotation_plan()` caps the decision at `MAX_DEPOSITS_PER_ROTATION = 2` and never drops the
party below `MIN_PARTY_AFTER_ROTATION = 3`, worst-first, converging over successive heal
trips. Freeing one or two slots is all the purpose requires. Post-cap, across the same 363
parties: deposits 0/1/2 only, and **zero** parties left under three mons.

**Action: bench immediately, deposit at the next PC trip, NEVER release.** A wrong deposit
costs one PC visit; a wrong release is unrecoverable, and this is a heuristic.

## 3. Roles — three derived facts, not a taxonomy

1. `sweeper_for(fight)` — **already exists** as `_sweep_score ≥ SWEEP_SCORE_FLOOR`. Reuse it.
2. `hm_carrier` — the set of HM moves known.
3. `coverage_types` — distinct attacking types across the party.

No tank/wall roles: we have no switching AI that could exploit them, so they would be
decoration. Party health = ≥1 sweeper for the next boss, all needed HMs covered, ≥4 coverage
types.

**Falsification condition (required):** log `coverage_types`, `roles` and
`attempts_to_first_win` per boss into the run header, then A/B ≥8 runs with the rule off.
Metric: median attempts-to-first-win at Wattson/Winona, and whiteouts per hour. **If coverage
≥4 does not move it, delete the rule.**

## 4. Rotation policy — piggyback, do not detour

**Never route to a PC for its own sake in v1.** On arrival at a Centre (a heal trip that was
happening anyway), run `rotation_plan(party, box, next_boss)`; execute only if it deposits ≥1
dead-weight mon **or** withdraws a mon clearing `SWEEP_SCORE_FLOOR` when nothing in the party
does.

**One standalone detour is justified:** `_boss_plan_is_hopeless` fired AND the box already
holds a super-effective answer. Far cheaper than a catch-and-train expedition, and it is the
case where the run otherwise ends. Cap: one rotation per visit, cooldown of one boss attempt.

## 5. Counter-chain integration — the ladder at `story_mode.py:1309-1313`

Replace the bare `raise` with an ordered ladder, each rung bounded, falling through to the
SAME raise:

1. **Box answer** — `team_policy.box_counter(needed)`; set a pending rotation, `yield from`
   the heal/PC trip. Cheapest, zero RNG.
2. **`COUNTER_CATCH_TARGET_DEX`** — a module-level set mirroring `HM_CATCH_TARGET_DEX`
   exactly, consumed by a clone of the branch at `story_mode.py:1485-1511`.
   ‼ **Build this rung FIRST.** It works even though every `counter_plan` candidate currently
   has `tile: None`, because the bot walks through wild grass constantly anyway.
3. **Travel + train** to a planned tile — inert today (no tiles); must SKIP CLEANLY, not crash.
4. All failed → keep raising the existing `BotModeError`.
   ‼ **Never delete the terminal raise.** Silent non-progress is worse than an honest stop.

## 6. NEVER randomise — the safety list

- **The `poke_balls > 1` reserve** — randomising it reintroduces the catch-without-balls bug.
- **`SURVIVAL_WHITEOUT_THRESHOLD`, derail budgets, loop bounds, timeouts** — a randomised
  bound makes a hang non-reproducible, the one failure we cannot debug offline.
- **HM acquisition and HM carriers** — boxing the only Surf carrier soft-locks the run.
- **The favourite's influence on boss lead selection** — it biases catching and keeping only;
  `_sufficiency_verdict` stays deterministic.
- **Release. Ever.**
- **The starter, and scripted-cutscene branches.**
- **`run_seed`** — recorded once, never re-rolled; every stochastic decision derives from it.
- ‼ **Caution must never map to "grind longer"** (§5.3's trap) — it maps to heal threshold,
  flee decision, safer training area, smaller level margin.

## 7. Offline test plan — no emulator, all of it

- **Personality:** pure `(seed, events) → (curiosity, caution)`. Assert determinism, bounds
  `[0,1]`, direction per event class, and that every drift emits a cause string.
- **Catch policy:** `should_catch_pure(...)` over 1000 seeds — assert distinct-species count
  across simulated runs exceeds a floor (the variance claim), party reaches 6, `BADGE01_GET`
  no longer blocks, and named targets are caught 100% even at `curiosity = 0`.
- **Dead weight:** table-driven. L5 Cascoon in an L24 party → dead; L18 in L24 → alive;
  HM-only carrier at L5 → alive; no damaging move → dead. **This encodes the observed bug as
  a regression test.**
- **Roles:** `coverage_types` on hand-built parties; reuse existing Roxanne/Wattson fixtures.
- **Rotation:** pure `rotation_plan(...) → (deposit[], withdraw[])`; assert no detour unless
  hopeless-and-box-has-answer.
- **Counter ladder:** extract a pure `counter_action(needed, box, plan) → (enum, payload)` so
  the generator only EXECUTES it; then the whole ladder, including the terminal raise, is
  unit-testable.
- **Favourite pool:** assert every roll has `emerald_reachable=True`, and that
  151/249/250/251/385/386 can never be rolled.
