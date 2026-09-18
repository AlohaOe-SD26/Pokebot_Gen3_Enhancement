# §Ch24 PROGRESS MARKER — THE DESIGN, COMPLETE (2026-09-18)

> ⛔ **AGENT OUTPUT IS A NOTE, NEVER TRUTH.** A 6-agent trace (3 angles, each adversarially refuted)
> produced this. ✅ marks something re-verified BY ME at FILE:LINE or by running it **in this round**;
> everything else is attributed. ⚠ Two ✅ facts are CARRIED FORWARD from the 2026-09-17 ruling and were NOT
> re-checked today — *“22 heal locations over 20 maps”* and *“`IS_CHAMPION` is monotone”*. A reviewer flagged
> that the blanket preamble over-claimed them; they are not new claims, but they are not today's readings.
> ⛔⛔ **THIS DOES NOT WIRE SEGMENT 24.** It closes prerequisite (1)'s DESIGN. The ruling stands.

**The 2026-09-16 ruling chose "the bot is standing on a SEALED League map" and left THREE caveats.
All three now have answers.**

---

## ⭐⭐ THE DECISIVE CONSTRAINT, AND IT CAME FROM A REFUTER ATTACKING MY OWN SHORTHAND

I wrote, in the brief I handed the agents: *"sealed rooms are group 16 (SIDNEYS_ROOM (16,0) … HALL5
(16,9), HALL_OF_FAME (16,11), POKEMON_LEAGUE_2F (16,14))"*. A refuter pointed out that this describes a
**RANGE**, and asked what else lives in it. ✅ **I checked `map_data.py:1037-1051` myself:**

| map | value | in the marker? |
|---|---|---|
| SIDNEYS / PHOEBES / GLACIAS / DRAKES / CHAMPIONS_ROOM | (16,0)–(16,4) | ✅ yes |
| HALL1 … HALL5 | (16,5)–(16,9) | ✅ yes |
| **POKEMON_LEAGUE_1F** | **(16,10)** | ⛔ **NO** — §Ch23's heal (leg 10) and mart (leg 11) legs stand here |
| HALL_OF_FAME | (16,11) | ✅ yes |
| **EVER_GRANDE_CITY_POKEMON_CENTER_1F** | **(16,12)** | ⛔⛔ **NO** — the avatar STANDS here during any Poké-Centre heal (the door is `(EVER_GRANDE_CITY, (27,48))`) |
| **EVER_GRANDE_CITY_POKEMON_CENTER_2F** | **(16,13)** | ⛔ **NO** — same building, same group |
| **POKEMON_LEAGUE_2F** | **(16,14)** | ⛔ **NO** — the Cable Club |

⇒ ⛔⛔ **A GROUP-16 RANGE TEST WOULD GRADE §Ch23 DONE WHILE THE BOT STANDS ON `LEAGUE_1F (16,10)`
MID-HEAL — BEFORE THE BASKET IS BOUGHT.** ✅ `heal_at_league` asserts `_on_map(LEAGUE_1F)` (`victory_road.py:2962`) and heals at `LEAGUE_NURSE_STAND = (3,4)` on that map (`:2982`).
‼ **CORRECTED AFTER A TIER 1 BLOCK:** this first named the POKÉ CENTER maps as where leg 10 heals. It does not — leg 10 heals at the League NURSE on (16,10). ⛔⛔ BUT MY FIRST CORRECTION THEN OVER-REACHED, saying the Poké Center maps are “never visited by our code (2 refs repo-wide)”: that was a SYMBOL count, not an occupancy test — the avatar DOES stand on (16,12) during any Poké-Centre heal, and code detects such maps by SUBSTRING (`early_game.py:385`). ⇒ BOTH maps are occupied and the hazard is stronger than either earlier version. I had verified the map TABLE and then attached an agent's sentence about leg 10 to it. The hazard is unchanged and more direct; the Poké Center pair remains a second, independent reason a range test is wrong. That is the KI-90
class of hole, re-opened by a convenience.
⇒ ⭐ **THE MARKER MUST BE AN EXPLICIT TUPLE. A GROUP OR RANGE TEST IS FORBIDDEN.** This is the single
most important line in this note.
⚠ *(An earlier draft flagged `ROUTE4_POKEMON_CENTER_1F = (16, 0)` sharing SIDNEYS_ROOM's raw tuple. A reviewer correctly called this PADDING: it lives in `class MapFRLG`, a different Enum entirely, so no comparison in this codebase could confuse them. Kept only as a one-line caution: compare enum MEMBERS, not bare `(group, number)` pairs.)*

---

## THE DESIGN

```
#: The SEALED §Ch24 maps. ⛔ AN EXPLICIT TUPLE, NEVER A GROUP/RANGE TEST. Map group 16 also holds
#: POKEMON_LEAGUE_1F (16,10) — where §Ch23's leg 10 stands to heal (`heal_at_league` asserts
#: `_on_map(LEAGUE_1F)`) and leg 11 buys the basket — League 2F (16,14), and the Ever Grande POKÉ
#: CENTER (16,12)/(16,13). A range test would grade §Ch23 done MID-HEAL, before the basket. (2026-09-18)
CH24_SEALED_MAPS = (
    SIDNEYS_ROOM, PHOEBES_ROOM, GLACIAS_ROOM, DRAKES_ROOM, CHAMPIONS_ROOM,
    HALL1, HALL2, HALL3, HALL4, HALL5, HALL_OF_FAME,
)
```

**THE MARKER PREDICATE:** `on a CH24_SEALED_MAP` **OR** `IS_CHAMPION` (flag 2175).

* The **sealed-map** half is safe **by exhaustion** — ✅ re-measured: 22 heal locations over 20 maps,
  **none** a League interior; the lobby's `OnTransition` arms an **outdoor** respawn at
  `MAP_EVER_GRANDE_CITY (18,6)`. ⇒ a whiteout cannot forge a position there.
* The **`IS_CHAMPION`** half covers **winning**, which the original marker missed: a completed §Ch24
  ends in `LITTLEROOT_TOWN_BRENDANS_HOUSE_2F (4,2)`. `IS_CHAMPION` is **monotone** — set in exactly one
  decomp file, cleared nowhere.
⚠ `IS_CHAMPION` is a COMPLETION term, not a "the run is usable" term — it reads True through the Hall
of Fame and the credits while the run is unusable. Do not collapse the two roles (`#24-gameclearflag`).

---

## ✅ MEASURED BY ME — THE MARKER IS NECESSARY, NOT MERELY TIDY

Loading pinned fixtures and evaluating the **real production predicates**, with controls:

| fixture | map | marker | `inside_league` | `at_eg_top` | `ch23_chapter_done()` |
|---|---|---|---|---|---|
| `post_hall4_door` | **HALL4 (sealed)** | True | True | True | ⛔ **False** |
| `post_ch24_atdoor` | EVER_GRANDE (18,6) | False | False | True | True |
| `post_league_shop` | EVER_GRANDE (18,6) | False | False | True | True |
| `post_league_heal` | EVER_GRANDE (18,6) | False | False | True | False |

⇒ ⭐ **ONE TILE FROM THE CHAMPION'S DOOR, `ch23_chapter_done()` RETURNS FALSE** — so without a marker
§Ch23 *is* re-entered mid-gauntlet. That is the defect, measured rather than argued.
⇒ The controls separate (sealed True / outside False), so the readings mean something.
⇒ `post_league_heal` False → `post_league_shop` True is the **basket conjunct working as designed**.

---

## CAVEAT (2) — THE LOBBY WINDOW: SAFE POST-WALLY

**AGENT-MEASURED, and reproduced by an independent refuter that re-ran the probe** — ⚠ **not measured
by me: no fixture in this repo stands in the lobby** (`grep -c POKEMON_LEAGUE_1F saves/FIXTURES.md5`
→ 0), which is itself worth fixing.

* Post-Wally, standing at `POKEMON_LEAGUE_1F (9,11)`: **zero of §Ch23's eleven legs fire**, zero frames
  are yielded, nothing is bought, healed or moved. The chapter burns its three no-op attempts and
  raises `BotModeError`.
* ✅ **MY HYPOTHESIS CONFIRMED, AND THE TWO CAVEATS INTERACT:** leg 4 (the ocean crossing) skips because
  `at_ever_grande_top()` returns True in the lobby **via `inside_league()`, which includes 1F**. ⇒ the
  lobby is protected by the very wideness that makes `inside_league()` **wrong for the marker**. Keep
  `inside_league()` exactly as it is — ✅ it has exactly ONE caller (`victory_road.py:1424`).
* Legs 10 and 11 do **not** re-fire: their guards test `_on_map(EG)`, the **outdoor** map, not the
  lobby they stand in.

**⚠ TWO CORRECTIONS THE REFUTER MADE TO THE TRACE, both of which change the design:**
1. **The window is TWO maps, not one.** League **2F** (16,14) is reachable from the lobby, and ✅ our
   own code says how: *"`(1,7)` is `MB_UP_ESCALATOR`, collision 0 — an accidental step-on warp to
   League 2F (the Cable Club)"* (`victory_road.py:410-412`). Both 1F and 2F are non-marker maps the
   bot can occupy past the front door.
2. **"Zero legs fire" is true only POST-WALLY.** Pre-Wally the training leg fires in the lobby and on
   2F, because its guard (`:3393`) carries no position test. Not live today (the bot cannot be there
   pre-Wally), but the qualifier must travel with the claim.

---

## ⛔ WHAT THIS DOES NOT ESTABLISH

* **No code was written.** This is the design for prerequisite (1); implementing it is a separate item.
* **The lobby result is not mine.** It is an agent probe reproduced by a refuter. ⇒ **mint a lobby
  fixture** and re-measure — that converts caveat (2) from a trace into a reading, and the entry
  driver already walks that route.
* An agent reported that a spent basket at the **outdoor** whiteout respawn makes **leg 5** re-fire.
  ⚠ The refuter notes leg 4 firing from inside the Ever Grande Poké Center is **already a KNOWN GAP**
  (`probe_league_leg4_guard.py` case C6) and must **not** be re-filed as new. Named here only so the
  next reader does not rediscover it.
* Prerequisites (2), (3) and (4) are untouched and still open. **Segment 24 stays unwired.**
