# §Ch24 — THE POKÉMON LEAGUE: STRUCTURE, GATES AND TEAMS (2026-09-04)

> ⛔ **THIS IS A NOTE, NOT TRUTH.** Read `00-READ-THIS-FIRST.md`. On any contradiction with an
> authoritative doc, the authoritative doc WINS until verified. **READ** = the agent read the decomp
> file; **DERIVED** = the agent computed it itself; **OURS** = measured in our harness.

**Provenance.** One Claude agent, decomp-cited throughout (`pret/pokeemerald`). It was given our
existing beliefs and asked to confirm or refute each — it did both.

---

## 1. ⭐⭐ THE ONE THAT CHANGES OUR PLAN: **LEAGUE 1F HAS A POKÉ CENTER *AND* A MART**

⛔ **REFUTED, one of our beliefs.** We assumed no healing between the Victory Road exit and Sidney.
`data/maps/EverGrandeCity_PokemonLeague_1F/map.json` + `scripts.inc` (READ):
- `OBJ_EVENT_GFX_NURSE` at **(3,2)** → `Common_EventScript_PkmnCenterNurse` — a standard free heal.
- `OBJ_EVENT_GFX_MART_EMPLOYEE` at **(16,2)** → a `pokemart` stocking **Ultra Ball, Hyper Potion,
  Max Potion, Full Restore, Full Heal, Revive, Max Repel.**

⇒ **THE EMPTY-BAG PROBLEM IS SOLVABLE.** We go into this arc with **one Potion** and **₽38,893**.
There is a full restock one map before Sidney. ‼ This must happen BEFORE the commitment point in §3.

✅ **CONFIRMED, the half that was right:** there is **NO healing of any kind between Sidney and
Wallace.** Halls 1–5 have **zero** `object_events` and **zero** `bg_events`; each E4 room contains
exactly one object (the trainer).

⚠ **NOT YET VERIFIED IN OUR OWN MAP DATA.** Our `PokemonCenter` enum has **no League entry** (only
`EvergrandeCity`), so nothing in our code can currently heal there. Verify before building on it.

## 2. THE MAP CHAIN (READ) — ‼ **`HALL5` IS THE *FIRST* HALL**

⛔ **A NAMING TRAP.** Halls 1–4 come *after* Sidney/Phoebe/Glacia/Drake. A bot that assumes Hall1 is
first walks backwards.

```
VictoryRoad_1F (39,5) → EVER_GRANDE_CITY (18,27)          [the Victory Road EXIT]
EverGrandeCity (18,5) → LEAGUE_1F (9,11)                   [the League door]
LEAGUE_1F (9,1)/(10,1) → HALL5 (5,12)                      ⛔ COMMITMENT POINT is the next step
HALL5   (5,2) → SIDNEYS_ROOM  (6,13)
SIDNEY  (6,2) → HALL1 (5,12) → PHOEBES_ROOM (6,13)
PHOEBE  (6,2) → HALL2 (5,12) → GLACIAS_ROOM (6,13)
GLACIA  (6,2) → HALL3 (5,12) → DRAKES_ROOM  (6,13)
DRAKE   (6,2) → HALL4 (5,33) → CHAMPIONS_ROOM (6,12)       ⚠ HALL4 IS 33 TILES LONG (~5x the others)
CHAMPION(6,2) → HALL_OF_FAME (7,11)
```
Map groups: `EVER_GRANDE_CITY` = (0,8); `VICTORY_ROAD_1F` = (24,43); every League room is group 16.
The trainer object in every E4 room and the Champion's room is at **(6,5)**.

✅✅ **VERIFIED IN OUR OWN DATA 2026-09-04 (`modules/map_data.MapRSE`) — the map chain is REAL, not
recalled.** Every group/num the agent gave matches ours exactly: `EVER_GRANDE_CITY_POKEMON_LEAGUE_1F`
**(16,10)**, `HALL5` **(16,9)**, `SIDNEYS_ROOM` **(16,0)**, `HALL1`–`HALL4` **(16,5)–(16,8)**,
`CHAMPIONS_ROOM` **(16,4)**, `HALL_OF_FAME` **(16,11)**. ⇒ this is the one part of the note that has
cleared the project's "verify in our own harness" bar; the rest has not.
⭐ **AND OUR DATA HAS ONE THE NOTE MISSED: `EVER_GRANDE_CITY_POKEMON_LEAGUE_2F = (16,14)`.** The
agent's chain never mentions a 2F. Not on the critical path as described, but ⛔ **do not assume the
chain is complete** — find out what 2F is before wiring the walk.

⚠ **`HALL4` IS 33 TILES LONG.** Any hardcoded "walk N tiles up the hall" hangs there.

**Progress read:** `VAR_ELITE_4_STATE` (`0x409C`) steps 0→1→2→3→4 as each room is entered. Usable.

**Forced cutscenes (READ):** on warp in, `..._OnWarp` turns the player north; `..._OnFrame` runs
`Common_Movement_WalkUp6` — a **forced 6-step walk** — then seals the door. The Champion's room
force-walks and **goes straight into Wallace's battle with no player input.** ⇒ input during these is
swallowed; the bot must not fight the cutscene.

## 3. ⛔⛔ THE COMMITMENT POINT — EVERY E4 ROOM SEALS ITS OWN EXIT

`data/scripts/elite_four.inc`, `PokemonLeague_EliteFour_EventScript_WalkInCloseDoor` (READ):
```
setmetatile 5, 12, METATILE_EliteFour_EntryDoor_ClosedTop,    TRUE
... (5,13) (6,12) (6,13) (7,12) (7,13) ...
```
The final `TRUE` is `impassable`. The room's own south warp is at **(6,13)** — so **the exit warp
tile is made physically unreachable.** Each room's `OnLoad` re-applies the seal when
`VAR_ELITE_4_STATE` matches, so **it survives a save + reset.** The decomp's own comment notes
re-entering a beaten room "isnt normally possible".

⇒ **ONCE THE BOT STEPS HALL5 (5,2) → SIDNEY IT IS COMMITTED TO ALL FIVE BATTLES ON ONE PARTY, WITH
NO HEAL, NO SHOP AND NO ESCAPE.** Everything before that tile is reversible; nothing after it is.
**Heal and buy at League 1F before that step.** Bag items still work — our inventory is the only
healing for ~25 enemy Pokémon.

## 4. THE ENTRY GATE (READ) — ONE FLAG, BUT YOU MUST TALK TO A GUARD

The decomp's own comment: *"The door guards only check for FLAG_BADGE06_GET because Winonas badge is
the only one that can be skipped."*
- `..._OnTransition` runs `setrespawn HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE`, sets
  `FLAG_LANDMARK_POKEMON_LEAGUE`, and — **only while `FLAG_ENTERED_ELITE_FOUR` is unset** — parks the
  two guards at **(9,2)/(10,2)**, physically covering the tiles under the door warps at (9,1)/(10,1).
- ⇒ ⛔ **PATHING STRAIGHT TO (9,1)/(10,1) FAILS UNTIL THE GUARD SCRIPT HAS RUN.** The bot must talk
  to a guard; on success they step aside permanently and `FLAG_ENTERED_ELITE_FOUR` is set.

| flag | value |
|---|---|
| `FLAG_ENTERED_ELITE_FOUR` | `0x107` |
| `FLAG_BADGE06_GET` | `0x86C` |
| `FLAG_LANDMARK_POKEMON_LEAGUE` | `0x8B4` |
| `FLAG_IS_CHAMPION` | `0x87F` |
| `FLAG_DEFEATED_ELITE_4_SIDNEY/PHOEBE/GLACIA/DRAKE` | `0x4FB`–`0x4FE` |
| `VAR_ELITE_4_STATE` | `0x409C` |

## 5. LOSS BEHAVIOUR — ✅ OUR BELIEF CONFIRMED, PLUS TWO THINGS WE DID NOT KNOW

`DoWhiteOut` (`src/overworld.c:358`) runs `EventScript_WhiteOut` → `ResetEliteFour`, then halves
money, heals the party, and warps to the last heal location. `ResetEliteFour` (READ) clears all four
`FLAG_DEFEATED_ELITE_4_*` and does `setvar VAR_ELITE_4_STATE, 0`.

⭐ **NEW (1) — A WHITEOUT *ANYWHERE IN HOENN* WIPES E4 PROGRESS.** `ResetEliteFour` is called from
`EventScript_WhiteOut` **globally**, not scoped to the League. A wild Zigzagoon on Route 101 during an
unrelated errand undoes the run. `FLAG_IS_CHAMPION` is **not** cleared.

⭐⭐ **NEW (2) — THE RETRY LOOP IS CHEAP.** League 1F's `OnTransition` already set the respawn, and
`heal_locations.json` puts `HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE` at **EVER_GRANDE_CITY
(18,6)** — the tile **directly below the League door (18,5)**. ⇒ **a losing bot lands healed, one
step from the door. No Victory Road re-run.** *(Compare `HEAL_LOCATION_EVER_GRANDE_CITY` = (27,49),
the ordinary Poké Center.)*

Bonus (`src/region_map.c:2007`): once `FLAG_LANDMARK_POKEMON_LEAGUE` is set, Ever Grande becomes a
**two-name Fly destination** and the bot can Fly directly to the League front at (18,6).

## 6. THE TEAMS (READ — `src/data/trainer_parties.h`, `src/data/trainers.h`)

All four E4 members carry **2 AI Full Restores**; **Wallace carries 4**. Every ace holds a **Sitrus
Berry**. ✅ Every level below CONFIRMS our existing belief.

**SIDNEY** (max 49) — the only member with `SETUP_FIRST_TURN`:
Mightyena 46 · Shiftry 48 · Cacturne 46 · Crawdaunt 48 · **Absol 49**

**PHOEBE** (max 51): Dusclops 48 · Banette 49 · Sableye 50 · Banette 49 · **Dusclops 51**
⚠ **OUR "all-Ghost" BELIEF NEEDS A CAVEAT: `Sableye` is `{TYPE_DARK, TYPE_GHOST}`.** ⇒ **Mightyena's
Crunch is NOT super-effective on it** (Dark→Ghost ×2 but Dark→Dark ×0.5 = neutral), and Sableye is
immune to Normal, Fighting *and* Psychic. Crunch still hits Dusclops/Banette for ×2.

**GLACIA** (max 53): Sealeo 50 · Glalie 50 · Sealeo 52 · **Glalie 52 knows EXPLOSION** ·
**Walrein 53 knows SHEER COLD** (OHKO move — a real run-ender).

**DRAKE** (max 55): Shelgon 52 · Altaria 54 · Kingdra 53 · Flygon 53 · **Salamence 55**

**WALLACE** (max 58, **SIX** Pokémon): Wailord 57 (**Water Spout**) · Tentacruel 55 · Ludicolo 56 ·
Whiscash 56 · Gyarados 56 · **Milotic 58 (RECOVER + Sitrus Berry)**

## 7. WHAT THIS MEANS FOR OUR PARTY

Our trained party is **Sceptile L51 / Swellow L47 / Wailord L47 / Mightyena L47** (+ Zigzagoon L19
and Castform L36 as untrained bench). Against Sidney's 46–49 that is roughly even; against Wallace's
55–58 it is **8–11 levels short**, and Wallace has four Full Restores plus a Recover/Sitrus Milotic.

⇒ **DO NOT READ "TRAINED TO 47" AS "READY FOR THE CHAMPION".** L47 was chosen because it is the
highest target affordable on 1F *and* Mightyena's Crunch level — it clears **Wally (ace 45)**, not
Wallace. The remaining gap is meant to be closed on **B1F after Wally** (950.8 EXP/battle vs 1F's
775.6), which is the better ground and is gated behind exactly the fight the training was for.

⚠ And the bench is a live liability: the faint-replacement ranking weighs **HP fraction above
level**, so a cascade can send the L19 Zigzagoon into a L58 Milotic.

## 8. WHAT TO VERIFY BEFORE BUILDING

1. ⛔ **The League 1F Poké Center + Mart in OUR map data** — the whole restock plan rests on it, and
   our `PokemonCenter` enum has no League entry today.
2. The guard-blocking claim: confirm `calculate_path` to (9,1)/(10,1) actually **fails** before the
   guard script runs, and succeeds after. *(A cheap A/B, and it is the one that decides whether the
   bot can enter at all.)*
3. **DERIVED, NOT READ — treat with care:** the agent's own flood-fill claims the Victory Road exit
   at EGC (18,27) sits on a **closed 231-tile plateau** containing the League door but **not** the
   Ever Grande Poké Center, so after exiting Victory Road the League nurse is the only heal without
   re-traversing. The agent flagged its elevation/behaviour model as a reimplementation and asked for
   a live probe. ‼ The conclusion that *matters* (League 1F has a nurse) does **not** depend on it.
