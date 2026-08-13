# ‼‼ `PuzzleSolverMode` ALREADY SHIPS §Ch21's DUNGEON *AND* THE WHOLE REGI ARC (2026-08-13)

> **Status: VERIFIED BY ME DIRECTLY**, not recalled and not taken from an agent — the file is
> byte-identical to the upstream mirror and the code below is quoted verbatim from our own tree.
> **What is NOT verified: that any of it RUNS here.** Nothing in this project has ever driven it.
> See "What this does NOT prove" at the bottom before planning on it.

## How this was found

While doing KI-68's step 1 (recon for a chapter-driven `dive()`), the search for an
`emerge()`/surface counterpart turned up `surface_from_dive()`
(`modules/modes/util/higher_level_actions.py:705`) — whose **only caller** is
`modules/modes/puzzle_solver.py:204`. Reading that call site revealed a complete, working dive
recipe, and then a great deal more.

## The measurement

```
git diff --no-index "40cakes repo/pokebot-gen3/modules/modes/puzzle_solver.py" \
                    "sandbox-pokebot/modules/modes/puzzle_solver.py"
→ no output: BYTE-IDENTICAL to the pristine upstream mirror.
```

Registered as a real bot mode at `modules/modes/__init__.py:29` and `:54`. 692 lines.
`is_selectable()` (`puzzle_solver.py:77-89`) returns True only while standing on one of:
`ROUTE113_GLASS_WORKSHOP`, `SKY_PILLAR_OUTSIDE`, **`ISLAND_CAVE`**, **`DESERT_RUINS`**,
**`ANCIENT_TOMB`**, `BIRTH_ISLAND_EXTERIOR`, `MIRAGE_TOWER_1F`, **`PACIFIDLOG_TOWN`**,
**`SEAFLOOR_CAVERN_ENTRANCE`**.

## 1. §Ch21's DUNGEON IS ALREADY ROUTED — hand-coded, Emerald-specific

`puzzle_solver.py:356-...`, `case MapRSE.SEAFLOOR_CAVERN_ENTRANCE`. Asserts **Strength, Rock
Smash, Surf**, sets `use_repel = True`, then walks rooms 1 → 2 → 6 → 3 → … with explicit
`use_rock_smash(...)`, `use_strength(...)` and `walk_one_tile(...)` calls, in an
`if context.rom.is_emerald:` branch distinct from the RS one. Excerpt:

```python
yield from navigate_to(MapRSE.SEAFLOOR_CAVERN_ROOM1, (4, 10))
yield from use_rock_smash("Right")
yield from navigate_to(MapRSE.SEAFLOOR_CAVERN_ROOM1, (5, 10))
yield from use_strength("Down")
...
if context.rom.is_emerald:
    yield from navigate_to(MapRSE.SEAFLOOR_CAVERN_ROOM2, (9, 7))
    yield from use_rock_smash("Left")
    yield from navigate_to(MapRSE.SEAFLOOR_CAVERN_ROOM2, (4, 6))
    yield from use_strength("Up")
```

‼ Because the hard parts use `walk_one_tile` / `use_strength` / `use_rock_smash` rather than the
planner, **KI-59 (the `Impassable *` over-blocking) may be largely sidestepped here** — but
`navigate_to` is still used, so KI-59 is not automatically harmless. Must be measured.

## 2. THE DIVE SEQUENCE IS ALREADY WRITTEN — and it is the template §Ch21 needs

`puzzle_solver.py:199-206` — the Sealed Chamber path, verbatim:

```python
def path():
    yield from navigate_to(MapRSE.ROUTE134, (61, 31))
    yield from dive()
    yield from navigate_to(MapRSE.UNDERWATER_ROUTE134, (8, 8), False)
    yield from navigate_to(MapRSE.UNDERWATER_SEALED_CHAMBER, (12, 44), False)
    yield from surface_from_dive()
    yield from navigate_to(MapRSE.SEALED_CHAMBER_OUTER_ROOM, (10, 3))
```

Note the third positional `False` = `run=False` (`walking.py:389-392`) — you do not run underwater.

⇒ **KI-68's leg breakdown is confirmed, with one correction.** KI-68 says *"Only (b) is missing,
and it is one call."* It is **two** calls: `dive()` **and** `surface_from_dive()`. Both already
exist (`higher_level_actions.py:682` and `:705`); neither has any caller in `modules/story/` or
`story_mode.py`. Entering underwater and never surfacing is precisely how this project strands a
run, so the second call is not a detail.

## 3. ALL THREE REGI PUZZLES ARE ALREADY IMPLEMENTED

`case MapRSE.DESERT_RUINS` (Regirock, ~:220), `ISLAND_CAVE` (Regice, ~:264),
`ANCIENT_TOMB` (Registeel, ~:312) — each with separate Emerald and RS branches, gated on
`SYS_REGIROCK_PUZZLE_COMPLETED` / `SYS_BRAILLE_REGICE_COMPLETED` /
`SYS_REGISTEEL_PUZZLE_COMPLETED`, and asserting the Emerald-specific moves:
**Regirock → Rock Smash** (`:232`), **Registeel → Flash** (`:324`) — RS uses Strength and Fly
(`:248`, `:340`).

‼ **This independently confirms KI-69's Emerald-vs-RS reversal**, from upstream bot code sitting in
our own tree rather than from the decomp:

```python
if context.rom.is_emerald:
    assert_pokemon_in_party_slot("Wailord", 0, "... requires Wailord in the first party slot.")
    assert_pokemon_in_party_slot("Relicanth", get_party_size() - 1,
                                 "... requires Relicanth in the last party slot.")
if context.rom.is_rs:
    assert_pokemon_in_party_slot("Relicanth", 0, ...)
    assert_pokemon_in_party_slot("Wailord", get_party_size() - 1, ...)
```
(`puzzle_solver.py:180-197`) — **Emerald: WAILORD slot 0, RELICANTH LAST.** Exactly KI-69.

## ⇒ WHAT THIS CHANGES

The Regi arc and §Ch21 were both framed as "build a chapter". Most of the content is already
written. What is genuinely missing is narrower and different in kind:

| piece | status |
|---|---|
| Seafloor Cavern interior route | ✅ upstream code exists |
| Sealed Chamber dive route + braille Dig | ✅ upstream code exists |
| Regirock / Regice / Registeel puzzles | ✅ upstream code exists |
| **Getting the player TO `SEAFLOOR_CAVERN_ENTRANCE`** | ❌ the dive leg — KI-68's real gap |
| **Party CONTENTS**: Wailord, Relicanth, and Dive/Dig/Flash carriers | ❌ `#24-roster`'s deposit/withdraw half |
| **Party ORDER**: Wailord slot 0, Relicanth last | ✅ **`roster.py`, DRIVEN AND PROVEN 2026-08-13** |
| Driving `PuzzleSolverMode` from the story ladder | ❌ it is a manual, map-gated mode |

‼ **Today's roster drive turns out to be the exact precondition this arc asserts.**
`assert_pokemon_in_party_slot("Wailord", 0)` is `plan_last_slot`'s reason for existing.

## ‼ WHAT THIS DOES **NOT** PROVE — read before building on it

1. **Nobody in this project has ever run `PuzzleSolverMode`.** "Upstream ships it" is not evidence
   it works here. This project's own rule: an external artefact is a NOTE, never truth, until it is
   verified in our own harness.
2. **It is a manual, map-gated mode**, not a story segment. `is_selectable` requires already
   standing at the destination — so the story bot still has to make every journey itself.
3. **Its battle handling is NOT ours.** `on_battle_started` returns
   `handle_encounter(encounter, enable_auto_battle=True)` (`:98-99`), not this project's
   `LevelUpTravelBattleStrategy` — which exists precisely because it *never flees a trainer battle*.
   The Seafloor Cavern is full of Aqua grunts. **Unverified and load-bearing.**
4. **⛔ The Regi battle is UNRECOVERABLE** (KI-69): `B_OUTCOME_WON` removes the encounter forever,
   and the fall-through **including `B_OUTCOME_LOST`** sets `FLAG_DEFEATED_*`. A KO *or* a whiteout
   deletes it permanently. Whether `handle_encounter(..., enable_auto_battle=True)` can KO a Regi
   is exactly the question to answer **before** ever pointing this mode at a tomb.
5. **`use_repel = True`** — what that needs in the bag, and what happens with none, is unverified.
6. **Our fork has diverged** from upstream in the helpers this mode calls. "Byte-identical file"
   does not mean "byte-identical behaviour" once `navigate_to` / `handle_encounter` differ.

⇒ **The next measurement is unchanged in kind but far better targeted:** drive the dive leg to
`SEAFLOOR_CAVERN_ENTRANCE`, then hand off to `PuzzleSolverMode` and see what actually happens.
Do NOT point it at a Regi tomb until item 4 is answered.
