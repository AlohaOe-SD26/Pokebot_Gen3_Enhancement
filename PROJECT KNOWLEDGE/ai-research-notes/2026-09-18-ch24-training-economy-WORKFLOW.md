# §Ch24 TRAINING ECONOMY — 9-AGENT WORKFLOW SYNTHESIS (2026-09-18)

> ⛔⛔ **AGENT OUTPUT IS A NOTE, NEVER TRUTH.** 4 research angles, each adversarially verified, then
> synthesised. 9 agents, 0 errors, ~49 min, 1.6M subagent tokens. **The synthesis's own §7 records
> that nine of the four notes' headline claims were killed by their refutation passes** — read it.
> Commissioned by USER RULINGS 4-7 (`06-DECISIONS-LOG.md` 2026-09-18).

---

# ⭐⭐ WHAT **I** VERIFIED MYSELF BEFORE ACCEPTING ANY OF IT — AND ONE HEADLINE IS **REFUTED**

The synthesis's §1 says the picker defect *“is one expression, not a missing table row”* and that
⇒ *“the fix is **not** data-shaped … the open work is putting an absolute floor in the scorer, which
is a code change”*.

⛔ **THAT IS REFUTED BY DIRECT MEASUREMENT.** I ran the real function.

✅ **VERIFIED — the scorer, at source** (`modules/story/training_areas.py`, inside
`best_training_area`): `score = (abs(hi - team_level), -hi)`. It is a SYMMETRIC distance, with a
“too strong” guard (`if team_level < lo - 1: continue`) and **no “too weak” guard**. So far the
synthesis is right.

✅ **VERIFIED — it is a CONSTANT FUNCTION today, and both reported values are correct:**

| `allow` | L20 | L30 | L47 | L53 | L75 |
|---|---|---|---|---|---|
| **`None`** (the production default) | ROUTE117 (13-14) | ROUTE117 | ROUTE117 | **ROUTE117** | ROUTE117 |
| everything permitted | ROUTE111 (19-22) | ROUTE121 (25-28) | ROUTE121 | **ROUTE121** | ROUTE121 |

⇒ our recorded “ROUTE117 for a L53 party” and the synthesis's “ROUTE121” are **the same defect seen
through different `allow` predicates**. Neither is wrong.

⭐⭐ **BUT THE CAUSE IS THE TABLE, NOT THE SCORER — MEASURED.** `TRAINING_GRASS` has **10 rows and
tops out at ROUTE121 (25-28)**. Nothing above L28 is in it at all. I added ONE row in memory —
`(VICTORY_ROAD_1F, (15,39), (36,40))`, the tile our code already calls `TRAIN_SPOT_1F` — and
re-ran the UNMODIFIED scorer:

| team level | 30 | 34 | **35** | 40 | 47 | 53 | 75 | 90 |
|---|---|---|---|---|---|---|---|---|
| returns | ROUTE121 | ROUTE121 | **VICTORY_ROAD_1F** | VR_1F | VR_1F | VR_1F | VR_1F | VR_1F |

⇒ ✅ **THE EXISTING SCORER IS ADEQUATE ONCE THE DATA EXISTS.** It picks the ruled ground for every
level from ~35 up, still gives L30 a level-appropriate route, and the existing “too strong” guard
still protects low parties. ✅ And it works under the **production default `allow=None`**, because
`VICTORY_ROAD_1F` is in neither `AREA_PREREQ` nor `NO_RETURN_GROUNDS`.
⇒ ⛔ **so “the fix is not data-shaped” is WRONG.** The minimal fix is data.

⚠⚠ **AND THAT SAME FACT IS THE REAL RISK, WHICH NEITHER MY PUNCH-LIST ITEM NOR THE SYNTHESIS NAMED
CORRECTLY.** Because `VICTORY_ROAD_1F` has **no `AREA_PREREQ` entry**, adding the row would make the
picker propose Victory Road to **any L35+ party at ANY story point** — long before Badge 8 — and
`allow=None` would NOT filter it, since that branch only skips maps that HAVE a prereq. Real callers
include counter-hunts (`counter_hunt.py:647`) and maintenance training (`story_mode.py:2659, 3199`),
not just §Ch24.
⇒ ⭐ **THE MINIMAL FIX IS TWO DATA CHANGES, NOT ONE:**
1. add `(VICTORY_ROAD_1F, (15,39), (36,40))` to `TRAINING_GRASS`; **and**
2. add an `AREA_PREREQ` entry for `VICTORY_ROAD_1F` so the conservative `allow=None` path skips it
   until a caller proves reachability.
⛔ **NEITHER IS DONE. NOTHING WAS WRITTEN TO PRODUCTION** — the table edit above was in memory and
reverted in the same process.

⚠ **STILL UNVERIFIED BY ME** (do not treat as settled): every EXP/battle figure in the table below,
the Gen-3 EXP formula citation, the PokeNav verdict, the money figures, and the Sweet Scent claim.
Those are the synthesis's, not mine.

---

# NOTE — TRAINING GROUNDS, POKÉNAV, MONEY, AND THE PICKER DEFECT
*Synthesis of four researched + adversarially-verified angles, 2026-09-18. This is a NOTE, never truth. Every load-bearing claim carries VERIFIED (someone opened the file and quoted it) or INFERRED/RECALLED (reasoning or memory). Do not promote one to the other. Nine of the four notes' own headline claims were killed by their refutation passes — see §7 before building on anything here.*

---

## 1. THE ONE THING THAT MATTERS MOST

Gen-3 EXP depends **only on the defeated foe** — `calculatedExp = expYield * foe.level / 7` (VERIFIED, `src/battle_script_commands.c:3310`) — so "level-appropriate training" is not a matching problem at all, it collapses to a single ordering: **among grounds the party can reach, survive, and get BACK from to heal, take the one with the highest EXP/battle.** That ground, for the whole pre-Champion game, is Victory Road (1F = 775 EXP/battle, B1F = 950, against Route 121's 348 and Route 117's 155 — all VERIFIED, reproduced twice independently), and it sits adjacent to the exact milestone ruling 4 names. But our picker cannot get there, and the reason is one expression, not a missing table row: `score = (abs(hi - team_level), -hi)` (VERIFIED, `training_areas.py:509`) is a **symmetric** distance with a "too strong" guard and no "too weak" guard, so it becomes a constant function from L28 upward and hands a L47–L75 party Route 121's L25–28 band forever. ⛔ **And the fix is not data-shaped:** the ground has already been RULED by the user (`06-DECISIONS-LOG.md:6214-6227`, VERIFIED — Victory Road 1F, exit side, **"B1F IS OFF THE TABLE … Do not reopen B1F without a new ruling"**), so the open work is not *choosing* a ground but (a) putting an absolute floor in the scorer, which is a code change, and (b) threading a heal leg that today does not exist — `_CAVE_EXITS` is single-hop and Ever Grande is measurably **split** (VERIFIED, `evidence/2026-09-18-vr-heal-roundtrip.stdout.txt`).

---

## 2. LEVEL-BRACKET TRAINING GROUNDS

Every row below was independently recomputed from `src/data/wild_encounters.json` + `modules/data/species.json` by the refutation pass and reproduced to <0.1% — **VERIFIED**. Slot weights `(20,20,10,10,10,10,5,5,4,4,1,1)` VERIFIED at `modules/map.py:1893`. Rate→steps VERIFIED at `src/wild_encounter.c:27/:495/:504` (p = rate/180).

⛔ **PROVENANCE WARNING (VERIFIED):** the `rate` column is **single-sourced to the decomp**. Our `cache/encounter_index_BPEE0.json` *cannot* corroborate it — it is a species→locations index whose `rate` field is that species' **slot share**, not the map's encounter rate. Do not build a "compute the rate from the cache" step (see §7).

| Ground | Band | Rate | Steps/enc | EXP/battle | EXP/step | Gate |
|---|---|---|---|---|---|---|
| **VICTORY_ROAD_B1F** | 38–42 | 10 | 18.0 | **950** | 52.8 | Badge 8 · **behind Wally** · ⛔ off the table by ruling |
| METEOR_FALLS_1F_2R (=B1F_1R, STEVENS_CAVE) | 33–40 | 10 | 18.0 | 817 | 45.4 | Surf + Waterfall |
| VICTORY_ROAD_B2F | 40–44 | 10 | 18.0 | 803 | 44.6 | Badge 8, two warps deep |
| SKY_PILLAR_1F/3F (5F 33–39) | 33–38 | 10 | 18.0 | 782 | 43.4 | post-Rayquaza story |
| ⭐ **VICTORY_ROAD_1F** | 36–40 | 10 | 18.0 | **775** | 43.1 | Badge 8 — **the ruled ground**; tile `(15,39)` MEASURED `Cave` |
| METEOR_FALLS_B1F_2R (only Bagon ground) | 25–40 | 10 | 18.0 | 722 | 40.1 | Surf + Waterfall |
| **ARTISAN_CAVE 1F/B1F** | **40–50** | 10 | 18.0 | 653 | 36.3 | `FLAG_SYS_GAME_CLEAR` (post-Champion) |
| MAGMA_HIDEOUT ×8 | 27–33 | 10 | 18.0 | 477 | 26.5 | Magma Emblem · ⛔ sole exit → Jagged Pass (**NO_RETURN**) |
| DESERT_UNDERPASS | 35–45 | 10 | 18.0 | 406 | 22.5 | GAME_CLEAR (bricked wall) · 50% Ditto |
| MT_PYRE_SUMMIT | 24–30 | 10 | 18.0 | 386 | 21.5 | Surf |
| MT_PYRE_1F..6F | 22–29 | 10 | 18.0 | 365 | 20.3 | Surf |
| CAVE_OF_ORIGIN_1F (+3 UNUSED_RS maps) | 30–36 | 4 | 45.0 | 363 | **8.1** | story |
| ROUTE119 | 24–27 | 15 | 12.0 | 352 | 29.3 | Surf |
| **ROUTE121 / ROUTE123** | 25–28 | 20 | 9.0 | 348 | 38.6 | Surf — highest ROUTE band that is not Mirage Island |
| ROUTE120 | 25–27 | 20 | 9.0 | 342 | 38.1 | Surf |
| NEW_MAUVILLE_INSIDE | 22–26 | 10 | 18.0 | 334 | 18.6 | Basement Key |
| ROUTE118 | 24–27 | 20 | 9.0 | 332 | 36.9 | Surf |
| NEW_MAUVILLE_ENTRANCE *(omitted by the original note)* | 22–26 | 10 | 18.0 | 329 | 18.3 | Basement Key |
| MT_PYRE_EXTERIOR | 25–29 | 10 | 18.0 | 328 | 18.2 | Surf |
| SEAFLOOR_CAVERN ×8 | 28–36 | 4 | 45.0 | 299 | **6.6** | Dive — worst ground on the list |
| SHOAL_CAVE_LOW_TIDE ×5 | 26–32 | 10 | 18.0 | 288 | 16.0 | Surf + **wall clock** (low tide = hours 03–08, 15–20 only) |
| JAGGED_PASS | 20–22 | 10 | 18.0 | 263 | 29.2 | ⛔ **NO_RETURN_GROUNDS** in our own table |
| ROUTE115 | 23–26 | 20 | 9.0 | 261 | 29.0 | Surf |
| MIRAGE_TOWER 1F–4F | 20–24 | 10 | 18.0 | 248 | 13.8 | story window |
| ROUTE111 (north) | 19–22 | 20 | 9.0 | 224 | — | Fallarbor side only |
| ROUTE114 | 15–18 | 20 | 9.0 | 221 | — | — |
| **ROUTE130** | **5–50** | 20 | 9.0 | 188 | 20.9 | Mirage Island — **1/65536 per party slot per day** |
| ROUTE117 | 13–14 | 20 | 9.0 | **155** | — | — (what the picker returns for a L53 party) |
| SAFARI_ZONE ×6 | 25–40 | 25 | 7.2 | **ZERO** | 0 | ⛔ `BattleSetup_StartWildBattle` → `DoSafariBattle` |

### ⭐ HIGHEST-LEVEL NON-LEGENDARY WILD — IT IS A **TIE AT L50**, NOT A SOLE MAXIMUM (VERIFIED)
| Ground | Species | Level | Reachable when |
|---|---|---|---|
| **ARTISAN_CAVE_1F / B1F** | Smeargle (12 land slots, L40–50) | **50** | post-Champion only (Lilycove ferry → Battle Frontier) |
| **ROUTE130** | Wynaut (slot 8, min=max=50) | **50** | Mirage Island, ~1/10,923 per day with a full party |

⛔ Neither is usable for ruling 4's window, and **Artisan Cave is only 7th–8th on EXP/battle** despite the highest band — Smeargle's yield is 106 against Golbat 171 / Hariyama 184. ⇒ **any future scoring key must be EXP/battle, never band maximum.**

### Not worth adding (VERIFIED negatives, so two plausible expansions are closed)
- **Surf** — best is VICTORY_ROAD_B2F water at 769 EXP/battle, but 50 of 55 water tables run at rate 4 (45 steps/enc) ⇒ 17.1 EXP/step vs VR B1F land's 52.8. *(⚠ "every surf table is rate 4" was refuted — three Safari tables are rate 9, two town tables rate 1; the conclusion survives only because the rate-9 ones pay zero EXP.)*
- **Rock Smash** — VR B1F's L30–40 rate-20 table is 602 EXP/battle, but the check runs **per smash**, not per step (~9 smashes/encounter, each a walk + a party-menu move).

### Brackets — **INFERRED**, and read the caveats
| Team L | Ground | Battles/level* |
|---|---|---|
| 10 | ROUTE117 (13–14) | 2.1 |
| 20 | ROUTE111-N (19–22) / ROUTE114 (15–18) | 5.6 — *Jagged Pass scores higher but is NO_RETURN* |
| 30 | MT_PYRE_SUMMIT (24–30); ROUTE121/123 if Mt Pyre not open | 7.2 |
| 40 | VICTORY_ROAD_1F (36–40) | 6.3 — ⛔ **not** Magma Hideout (NO_RETURN; the picker refuses it) |
| 50 → 100 | **VICTORY_ROAD_1F stays optimal forever** — EXP/battle does not decay with trainee level, and nothing pre-Champion beats it that the story can return from | 8.1 → 15.7+ |

\* ⚠ Assumes Medium-Fast n³ **and `viaSentIn == 1`** (the trainee solos every battle). `*exp = SAFE_DIV(calculatedExp, viaSentIn)` and an Exp. Share halves it again (VERIFIED, `battle_script_commands.c:3312-3324`) ⇒ **real battles/level can be 2× these** on a swap-trained party. Use the repo's `get_experience_needed_for_level` API, not this arithmetic.

### Two levers the table does not show
- ⭐ **SWEET SCENT bypasses the encounter check entirely and needs NO badge** (VERIFIED, `wild_encounter.c:697-746` calls `TryGenerateWildMon(..., 0)` then `BattleSetup_StartWildBattle()` with no `WildEncounterCheck`; badge guard is `fieldMove <= FIELD_MOVE_WATERFALL` and Sweet Scent is index 13). Cave floors qualify. ⚠ **Not "~0 steps/level"** — 20 PP ≈ 2.5 levels at L50, and each refill is a full round trip to the nurse.
- ⚠ **Steps/encounter are NOT exact for an arbitrary lead** (VERIFIED): `ABILITY_ILLUMINATE` / `ARENA_TRAP` **double** the rate; `STENCH` / `WHITE_SMOKE` / `SAND_VEIL`-in-sandstorm halve it; bike ×0.8; flutes and Cleanse Tag apply. An Illuminate lead halves the entire EXP/step column.

---

## 3. IS POKÉNAV A TRAINING / MONEY SOURCE?

**VERDICT: a real, permanently repeatable MONEY source; a weak TRAINING source for ruling 4's window; and ⛔ it is NOT the targeting tool the research first claimed.**

### What is VERIFIED about the mechanism
| Fact | Evidence |
|---|---|
| 78 rematch rows: 0–63 ordinary, 64 Wally VR, 65–72 gym leaders, 73–77 E4+Wallace | `include/constants/rematches.h:5-87`; data `battle_setup.c:260-335` |
| Each trainer is a ladder of **5 static parties** — no level scaling, ever | `battle_setup.h:6-13`; `trainer_parties.h:9277` |
| ⭐ **The top team repeats FOREVER** once all four are beaten | `battle_setup.c:1588-1601` (loop runs to `i==5`), `:1691-1709` (`return trainerIds[REMATCHES_COUNT-1]`) |
| One arming = **one** battle; a win clears it to 0 | `trainer_battle.inc:50-60`; `battle_setup.c:1351-1368` → `:1852-1856` → `:1733-1739` |
| ⭐ **A LOSS does NOT burn the arming** — `CB2_WhiteOut` branches before `HandleRematchVarsOnBattleEnd` | `battle_setup.c:1351-1368` |
| Walking path: ≥5 badges + 255 steps + a map load + a **31%** roll per registered trainer on that map | `battle_setup.c:1792-1817`, `:1619-1620`; step hook `field_control_avatar.c:543` |
| ⭐ A **map-connection crossing** also triggers the roll, not just a warp | `overworld.c:801` sits inside `LoadMapFromCameraTransition` (`:784`) |
| A **failed** roll leaves the counter at 255 ⇒ leave and re-enter for a free re-roll | `battle_setup.c:1813-1816` (reset only when the roll returned TRUE) |
| ⚠ …but entering a map where someone is **already** armed returns TRUE and **burns** the counter | `battle_setup.c:1614-1618` (`// Trainer already wants a rematch.` still sets `ret = TRUE`) |
| ⭐⭐ **Registration is AUTOMATIC** on winning any trainer battle while `FLAG_HAS_MATCH_CALL` is set — no second conversation | `battle_setup.c:1341-1347` → `:1754-1761`. Our bot sets that flag in Rustboro (`early_game.py:2644`) ⇒ **every rematch-table trainer we have beaten since is already registered** |
| Trainer battles pay **×1.5 EXP** over an equivalent wild | `battle_script_commands.c:3378-3379` |
| One integer `i` indexes everything: `sMatchCallTrainers[i].trainerId == gRematchTable[i].trainerIds[0]` for all i∈0..63 (checked programmatically, zero misalignments) | `match_call.c:171+` vs `battle_setup.c:262-325` |
| Gym-leader rematches are `FLAG_SYS_GAME_CLEAR`-only; the E4 rows are hard-forbidden | `gym_leader_rematch.c:32-41`; `battle_setup.c:1576-1586`, `:1610` |
| Wally VR rematch is **post-Hall-of-Fame only** | `VictoryRoad_1F/scripts.inc:75-91` |

### ⛔ THE CLAIM THAT ANSWERS RULING 5 — AND IT IS THE OPPOSITE OF THE FIRST ANSWER
**The player CANNOT choose whom to arm.** `UpdateRematchIfDefeated` lives *only* inside `else if (ShouldTrainerRequestBattle(matchCallId))` (VERIFIED, `match_call.c:1524-1529`), and `ShouldTrainerRequestBattle` designates **at most one trainer in the entire table** for a given game state:

```c
// src/match_call.c:1882-1907  (VERIFIED verbatim)
if (GetNumOwnedBadges() < 5) return FALSE;
max  = (numRematchTrainersFought * 13) / 10;
rand = ((dayCount ^ dewfordRand) + (dewfordRand ^ GetGameStat(GAME_STAT_TRAINER_BATTLES))) ^ otId;
n = rand % max;
if (n < numRematchTrainersFought) { if (GetNthRematchTrainerFought(n) == matchCallId) return TRUE; }
```
⇒ a player-initiated call **COLLECTS** the already-designated trainer; calling anyone else arms nobody. It *is* deterministic and computable (~77% of states have a valid target; `GAME_STAT_TRAINER_BATTLES` is an input, so the target rotates after every trainer battle — **INFERRED** that rotation always yields a fresh *reachable* target; nobody ran it). The call is also gated on the player's map type being ROUTE/TOWN/CITY/OCEAN_ROUTE (VERIFIED, `pokenav_match_call_list.c:355-356`), which forbids calling from beside the two highest-level targets (both in Meteor Falls).

### As a TRAINING source — weak for ruling 4
Recomputed from `trainers.h` + `trainer_parties.h` (VERIFIED, 13 ladders reproduced exactly): **only 5 of 64** ordinary rows top out ≥L47 — JOHN_AND_JAY 52 & NICOLAS 49 (Meteor Falls 1F 2R, Surf+Waterfall cave), LILA_AND_ROY 51 (Route 124, Surf), ISAIAH & KATELYN 48 (Route 128, Surf). **51 of 64 top out below L45**, and the floor is L31 (LYDIA/ISAAC, Route 117). ⇒ a L47+ party farming an *arbitrary* armed rematch **reproduces ruling 1's defect at a different scale**. Any use must filter by ladder-top level.

### Our side (VERIFIED)
- **Zero rematch handling** anywhere in `sandbox-pokebot/modules/`.
- `PokenavListener` B-mashes every incoming call away (`_listeners.py:376-395`), but `SelectMatchCallMessage` already fired in `MatchCall_PrintIntro` — so armings do happen unread. ⚠ *Rate is a few percent per call, not "collecting constantly".*
- ⛔ `on_pokenav_call()` **takes no arguments and no caller identity flows through it** (`_interface.py:154`). Logging *who* called is **not** "one implementation" — it needs a RAM read accessor for `sMatchCallState` / `trainerRematches` that the tree does not have (the only toucher is `gui/debug_menu.py:217-221`, and it **writes**).
- ⛔⛔ **FLAG NUMBERING CONFLICT, UNRESOLVED.** Decomp: `TRAINER_REGISTERED_FLAGS_START = 0x15C = 348` ⇒ ROSE=348. Ours: `347 MET_FRONTIER_SWIMMER_MOVE_TUTOR` ✓, then `348 MATCH_CALL_REGISTERED` (inserted), `349 REMATCH_ROSE` (+1), … `420 REMATCH_TATE_AND_LIZA`, then **`REMATCH_JUAN` is ABSENT** and `421 REMATCH_SIDNEY` resumes, ending `425 REMATCH_WALLACE` ✓ (= decomp 348+77). Both anchors match, which is only possible with one inserted and one dropped name. ⇒ `get_event_flag_by_number(0x15C+i)` and `get_event_flag("REMATCH_ROSE")` **read different flags** for every ordinary trainer. Must be settled live before any code reads these.
- ⛔ **RTC TRAP:** `RtcGetLocalDayCount()` reads `sRtc` (BCD, `rtc.c:89-95/:343-346`); our `get_clock_time()` reads `gLocalTime` — a *different* clock. `sRtc` is in our symbol table (`pokeemerald.sym:759`).
- Two latent hazards worth knowing: `GetTrainerMatchCallId` is an unbounded `while(1)` with no terminator (`match_call.c:1545-1555`), and `ShouldTrainerRequestBattle`'s `rand % max` has no zero guard — only the badge early-return stands between it and a divide-by-zero.

---

## 4. MONEY

### Ranked (post-verification)
| # | Source | Value | Status |
|---|---|---|---|
| 1 | ⭐ **AMULET COIN** — ×2 on **every** trainer payout and Pay Day, free, from Mom in Littleroot | E4 gauntlet alone: ₽32,400 → ₽64,800 | VERIFIED effect (`battle_util.c:3294-3296`), source (`players_house.inc:307-319`, `FLAG_BADGE05_GET`). ⛔ **NOT REFERENCED ANYWHERE IN OUR CODE.** ⚠ Gate chain is longer than "one NPC": a `VAR_LITTLEROOT_HOUSES_STATE` short-circuit, `FLAG_HAS_MATCH_CALL`, and `FLAG_ENABLE_MOM_MATCH_CALL` ⇒ possibly **two** conversations. ⭐ `moneyMultiplier` is set once and never reset to 1, so **any** mon sent out during the battle locks the ×2 — it need not be the lead. |
| 2 | **One-time trainers** | ROM-wide ₽1,304,976; **first-battle-only = 563 trainers / ₽588,332** | Total VERIFIED (reproduced exactly). The split is the CORRECTED one — see §7. Skipping a trainer destroys that money permanently (our own measured ₽4,128). |
| 3 | **PICKUP** — machinery already ships and is ON by default | ~**₽101/battle** per Pickup mon at L51–60 at shipped defaults; ₽123 if `pickup_check_frequency=1` | Mechanic VERIFIED (`battle_script_commands.c:784-824`, `:9654-9727`); EV table reproduced to the ruble. ⚠ The ₽123 assumes harvesting **every** battle; default is every 5th and `Cmd_pickup` needs an **EMPTY** slot ⇒ ×0.819. ⇒ ~540 battles funds the whole ₽54,300 basket with **zero extra walking**. ⛔ Nugget from Pickup is reachable only at party level **≤20**. |
| 4 | **E4 gauntlet itself** | ₽32,400 (₽64,800 w/ Coin) | VERIFIED by independent recomputation; confirms `victory_road.py:447`. Only if you WIN. |
| 5 | **Nuggets** — 10 exist, we take **1** | ₽45,000 uncollected | VERIFIED: all 10 coordinates read from `map.json`. Routes 112/113/119/120/121 + Fallarbor are ones the bot already walks. Sell = price/2 = ₽5,000 (VERIFIED at 6 `item_menu.c` sites) ⇒ `victory_road.py:457` is correct. |
| 6 | **Other field treasure** | ₽101,950 total incl. the nuggets (Star Piece ×4 ₽19,600, Big Pearl ×7 ₽26,250, Stardust ×4 ₽4,000, Pearl ×3 ₽2,100) | All 18 coordinates VERIFIED. Most of the non-Nugget half is Dive/Safari/Shoal-gated. ⛔ **Big Mushroom has ZERO field locations** (Paras is unobtainable in Emerald). |
| 7 | **Vitamins** | ≈₽220,500 if all sold | **INFERRED** — a flag census, not a map census. ⚠ The itemisation is wrong (Iron is **5**, not 6 — the 6th grep hit is TM Iron Tail; PP Max ×1 omitted), and **≥14 of 45 are not on route pre-E4** (6 Artisan Cave post-game, 5 Dive, 3 Safari). |
| 8 | **Rematches** | Best repeatable in the game: **CINDY stage 6** and **WINSTON stage 5, both MAP_ROUTE104, ₽7,200 each** from a single L36 Linoone (₽14,400 each w/ Coin) | VERIFIED; I ranked all 64 finals — these two beat 3rd place (John&Jay ₽4,160) by 1.7×. Slow: ≥5 badges + 255 steps + ~3.2 map re-entries per grant. |
| 9 | **Wild held items** | Staryu ₽745/mon = **~₽112/encounter** (Lilycove Super Rod slot 7 = **15%**, now VERIFIED from `wild_encounters.json` `encounter_rates`) | Grimer is 2% of Fiery Path encounters ⇒ ₽5/encounter; Gulpin 15% ⇒ ₽28. Only Staryu is both renewable and level-appropriate. |
| 10 | **Pay Day** | level×5/hit | VERIFIED formula — and now VERIFIED as moot: only Meowth/Persian learn it and both are unobtainable in Emerald; not a Gen-3 TM. |

### ⛔ RULED OUT — do not spend a day on these
- **Slateport half-price PokéNews** — post-game (`tv.c:2540`), Energy-Guru-only, and **provably break-even for every item**: buy is `p >> 1`, sell is `p / 2`, identical integers ⇒ no price exists at which the loop profits (VERIFIED).
- **Gym-leader rematches** — `FLAG_SYS_GAME_CLEAR` (VERIFIED).
- **Lilycove lottery** — needs ≥2 matching *trailing* digits, and every self-caught mon shares one OT ID so a full PC is no better than one mon ⇒ ~₽49/day EV (VERIFIED).

### THE ONLY SINK — and it prices ruling 6's tension exactly
`DoWhiteOut` does `SetMoney(money / 2)` — **all** money, unconditionally (VERIFIED, `overworld.c:358-366`), and `EventScript_WhiteOut` also calls `ResetEliteFour` (VERIFIED, `event_scripts.s:585-586`). ⇒ **losses are acceptable at 50% of the wallet each**, items survive and cash does not (which validates the standing "spend down to items before the League" ruling), and a mid-gauntlet loss costs the run *and* half the money.

### What our code tracks today (VERIFIED)
- `HandledBattleResult.money_gained` is **computed and thrown away**: written at `battle_handler.py:445` (`get_player().money - before_cash`), and a clean repo-wide grep finds exactly **one** other hit — the field definition at `battle_state.py:968`. **Zero readers.** ⇒ `#24-bosstrainingeconomics`'s "money is not written to any log" is still true, and the instrument it asks for is half-built.
- The only place money is actually reasoned about is `victory_road.py:440-461`: `LEAGUE_MIN_MONEY = 54_300` vs a MEASURED ₽56,041 (margin **₽1,741**), `LEAGUE_SELLABLE = (("Nugget", 5_000),)` — the entire shortfall contingency is **one Nugget**, and a single skipped Cooltrainer pair (₽4,128) has already broken it once.

---

## 5. WHAT OUR CODE GETS WRONG TODAY

```python
# sandbox-pokebot/modules/story/training_areas.py:499-511   (VERIFIED — re-read this session)
        if hi <= min_wild_max:
            continue  # doesn't beat the floor the caller already has
        if team_level < lo - 1:
            continue  # wilds too strong — the trainee would lose here
        ...
        score = (abs(hi - team_level), -hi)  # closeness to team_level, then higher band
        if best_score is None or score < best_score:
            best, best_score = (map_enum, tile, (lo, hi)), score
    return best
```
`abs()` is symmetric; the winnability guard is **one-sided**. There is no notion of "too weak" anywhere in either picker (`best_training_grass`'s sibling at `:250-252` is identical). The sole floor is the caller-supplied `min_wild_max`, it defaults to 0, and **`best_training_grass` has no floor parameter at all**.

**Constancy, CORRECTED (VERIFIED by replay over the `ast`-extracted real tables):** the answer stops responding to its argument at **L13** (`allow=None` → ROUTE117 (31,16) L13–14) and at **L28** (any permissive predicate → ROUTE121 (44,14) L25–28). **Not L29.** ⛔ The discriminators are **12→13** and **27→28**; a test that "varies the level across 29" is **vacuous** — both arms return the same row today *and* would under a correct implementation.

**Which answer production actually gets (VERIFIED):** all three call sites pass an `allow` predicate, so `allow=None` is a dev-console default nobody takes. The production answer at L47/53/60/75 is **ROUTE121, L25–28** — still exactly ruling 1's defect, but a materially different severity from the L13–14 headline number.

| Caller | Floor? | Consequence |
|---|---|---|
| `counter_hunt.py:647` | none | A counter caught at L40 gets the same fodder ground as a fresh L15 one. |
| `story_mode.py:2659/:2688` (`best_training_grass`) | **impossible** — no parameter | Priced by the frame budget, never refused. |
| `story_mode.py:3168/:3199` (relocation) | yes — `relocation_floor(...)` | ✅ **Correct. Do not "fix" this one.** |

⛔ But callers 2 and 3 are **the same function in sequence**: `_maintain_lagging_battler` is invoked at the *top* of `_prepare_for_fight` (`:2926`), and the floored relocation probe runs later in the same body — so the floor does not protect the errand that runs first.

**The de-facto guard is the frame budget, not the picker** (`MAX_PREP_TRAINING_FRAMES = 250_000`, `MAINTAIN_MAX_FRAMES = 150_000`): it refuses the *grind* and never says the *ground* was wrong, and `affordable_training_target` degrades by buying fewer levels **on the bad ground** rather than declining. A cost gate wearing a correctness gate's hat.

**The estimator** (`training_areas.py:688-718`): `xp_per_battle = 50.2 * wild_level / 7`, calibrated to a **Route 102 L3–5 patch**; `FRAMES_PER_WILD_BATTLE = 1433`, measured on the same patch; **no heal term** despite this file measuring heals as dominant ("78 heal round trips in one run"). It also omits the **×2 EXP split** and the **×1.65 frames-per-WIN** term — together ~3.3× optimistic, and a **closed** punch-list item that keeps being re-discovered. ⚠ On VR ground the errors point *both* ways: at wild_level 40 the base-exp term gives 286.9 vs the measured **775.6**, i.e. pessimistic, while the split/frames terms are optimistic. Do not quote a net direction.

**Also true, and worth saying plainly:** §Ch23 — the only real training leg that exists — **bypasses the picker entirely** (`TRAIN_SPOT_1F` + `TRAIN_TARGET = 47` hardcoded), and **E4 prep does not exist**: `_prepare_for_fight` is invoked for ten fights ending at Juan, and `story_mode.py:5178-5179` says the next build is Chapter 24.

---

## 6. THE MINIMAL FIX, AND WHAT IT RISKS

### Already settled — start here, do not re-derive (VERIFIED, `06-DECISIONS-LOG.md:6214-6227`)
> **RULING 2 — GRIND AT THE VICTORY ROAD EXIT SIDE, AND HEAL AT A POKÉ CENTER (NOT ITEMS).** … ⇒ **THIS SETTLES THE GROUND QUESTION AND KILLS THE B1F BRANCH.** … ⇒ ⛔ **B1F IS OFF THE TABLE** … **Do not reopen B1F without a new ruling.**

and RULING 1 (same entry) ratifies an **L62–75** goal — so production's `TRAIN_TARGET = 47` is *not* the target any more, and "§Ch23 is already level-appropriate" stops being true against L75 on a L36–40 ground.

### Free, correct, and independent of everything else (data-only)
1. `training_areas.py:38` and `:157` say Mirage Island is "behind a 1/256 daily RNG gate". It is a **16-bit equality against a daily RNG, i.e. 1/65536 per party slot** (VERIFIED, `time_events.c:42-52`) — wrong by ~256×, in the file whose job is to stop the next agent re-surveying. Add the second trap while there: **Wynaut's only ability is Shadow Tag** *and* it learns **Destiny Bond at L15** (VERIFIED in our own `species.json` `learnset.level_up`) — a KO can take the trainee with it. ⚠ Shadow Tag is **escapable** with a Smoke Ball or a Run Away lead (see §7).
2. `training_areas.py:66` has `(MapRSE.ROUTE102, (9, 2), (3, 5))`; the ROM band is **3–4**. The only mismatch of eleven audited bands — and `hi` is the live scoring key.

### The Victory Road promotion (the real item) — **INFERRED sequencing**
| Step | Shape | Status |
|---|---|---|
| (a) Move **only** the `VICTORY_ROAD_1F` row (`:149`) into `TRAINING_GRASS` with tile `(15, 39)` | data | tile is production-proven and MEASURED `Cave` (`victory_road.py:474-477`) |
| (b) Give it an `AREA_PREREQ` | **code-adjacent** | ⛔ `"waterfall"` **fails closed** — the whitelist is `(None, "surf", "region", "rocksmash")` (`story_mode.py:1211-1212`) and `_party_can_waterfall()` **does not exist**. Either reuse `"surf"` (simulated safe) or extend the whitelist + write the predicate — a code change. |
| (c) Heal-map entry | **blocked** | The spelling is `PokemonCenter.EvergrandeCity` (VERIFIED, `map_data.py:1537`) — `EverGrandeCity` raises AttributeError *inside boss prep*. But the 2026-09-18 probe shows **Ever Grande is SPLIT** (Poké Center door: 23 wp from (18,42); **NO PATH** from (18,6)), and §Ch23 heals at the League **NURSE**, which `train_team`'s `heal_center` cannot express because it takes a `PokemonCenter`. ⇒ **(c) is not writable as-is.** |
| (d) An **absolute floor** in the scorer | **code** | The data fix cannot create one. Needs an N chosen from evidence, and every caller must handle a far-more-frequent `None`. |

⇒ **Honest order: heal-threading FIRST, table SECOND, floor THIRD.** Anything else makes the table claim something navigation cannot deliver.

### What a promotion risks (each VERIFIED)
- **Promoting all three VR rows inverts the tie-break against you:** `-hi` selects **B1F at L42 and B2F at L45–75** — the two floors that are deeper/behind Wally — making the picker's answer *strictly worse* than §Ch23's existing hardcode. **1F only.**
- With **no** prereq entry, the conservative `allow=None` default proposes VR to any **L35+** party (simulated) — the exact inversion the default exists to prevent. *(Mitigated in practice: no production caller uses that arm.)*
- **`TRAINING_GRASS` is not the picker's private table.** Four other consumers read it: `_hm_hunting_grounds`, `counter_plan.find_counter_candidates` (a tile bumps the Victory Road Hariyama's rank — the top Fighting answer for Norman), `hunt_ground_tile`, and the debug header. `POKEBOT_HUNT_ANYGROUND=1` becomes materially more dangerous after a promotion than it is today.
- **`_return_blocked` would NOT catch a VR row**, because nothing has measured VR's return leg into `NO_RETURN_GROUNDS` — and the probe says Ever Grande is split.
- **The heal miss is handled asymmetrically:** maintenance refuses honestly (`"no heal centre mapped … — refusing"`), relocation **silently falls back to the boss's Poké Center** (`story_mode.py:3210`) — i.e. walks to the wrong city. Invisible from `training_areas.py`.
- `_CAVE_EXITS` / `_CAVE_ENTRANCES` hold **two** maps (Granite Cave 1F, Fiery Path), neither of them Victory Road, and the global navigator cannot cross warp levels — two real-HW runs already dropped to Manual on exactly that.

---

## 7. REFUTED / WITHDRAWN

**This section is not empty.** Nine headline-level claims and ~25 supporting ones were killed. Anything here must NOT be carried forward.

### Brackets angle
| Killed claim | Why |
|---|---|
| ⛔ "**Our ROM cache is trustworthy as the build source** — I cross-checked all 87 land tables against it" | `cache/encounter_index_BPEE0.json` is a **species→locations** index; its `rate` is that *species' slot share* (Victory Road B1F appears as four rows, 35/35/25/5) and the file **contains no `encounter_rate` at all**. ⇒ the rate column was never cross-checked, and the proposed "compute `encounter_rate` from the cache at build time" step would read a slot share where a rate belongs. |
| "Altering Cave's divergence is harmless — 84 EXP/battle, weakest in its class" | The 84 belongs to `gAlteringCave1` (band 6–16); our cache holds **`gAlteringCave9`** (18–28, **347.9**), and the sibling `gAlteringCave8` is **541.6** — which would rank ~12th in the game, above Magma Hideout. The sentence swapped tables mid-claim. |
| ⛔ "**The heal loop is two warps** / the bot does not need to travel anywhere" | Its own quoted warp list is **three warps plus two full traverses** (Ever Grande plateau + the width of Victory Road 1F). |
| ⛔ "**Every Mirage Island encounter is UNFLEEABLE**" | A **Smoke Ball** (`HOLD_EFFECT_CAN_ALWAYS_RUN`) or a **Run Away** lead returns `BATTLE_RUN_SUCCESS` *before* the Shadow Tag check (`battle_main.c:4034`, `:4038` vs `:4042-4051`). A guard exists and it is cheap. |
| "Wynaut's learnset is unverifiable — `species.json`'s array is empty" | It is populated under `learnset.level_up`: Counter 15, Mirror Coat 15, **Destiny Bond 15**, Encore 1. The stated reason for not verifying was false, and it hid the worse hazard. |
| "**Artisan Cave is THE highest-level non-legendary ground**" / "11 Smeargle slots" | **Tie at L50** with Route 130 Wynaut (slot 8, min=max=50); Artisan Cave 1F has **12** land slots. |
| "Every surf table runs at rate 4" | Histogram is {4:50, **9:3**, 1:2}. The conclusion survives only because the rate-9 tables are Safari Zone (zero EXP). |
| "**MAGMA_HIDEOUT (477) pre-badge-8**" as a T=40 bracket answer | The same note's next-but-one finding says its **sole exit is into Jagged Pass, which our own probes call NO_RETURN** — and `best_training_area` refuses NO_RETURN grounds at `:497` before any other test. Same note, opposite advice, no caveat at the point of recommendation. |
| "**Complete** land table, L26+ tier" | Missing `NEW_MAUVILLE_ENTRANCE` (329), `CAVE_OF_ORIGIN_ENTRANCE`, three `CAVE_OF_ORIGIN_UNUSED_*` (363), and five Altering Cave alternates. |
| "steps/encounter are **exact**" | Ignores lead ability (Illuminate/Arena Trap ×2, Stench/White Smoke/Sand Veil ×0.5), bike ×0.8, flutes, Cleanse Tag. |
| "EXP depends **only** on the defeated wild" | Omits `SAFE_DIV(calculatedExp, viaSentIn)` and the Exp. Share halving ⇒ every battles/level figure assumes a solo trainee. |
| **Seven wrong repo citations** in a note whose brief required FILE:LINE | `:135-137`→47 and 145 (the "two independent derivations agree" finding — its repo half was never opened); `:71`→10; "8 TRAINING_GRASS rows at :73-91"→**10 rows at :65-89**; `:142`→150; AREA_PREREQ `:275-283`→270-285; Safari `:47-52`→49-54. |
| Trimmed, not killed | "Artisan Cave is 6th-best EXP" (7th by its own table, 8th recomputed) · "Route 121/123 is the highest ROUTE band **in the game**" (Route 130 is 5–50) · "Sweet Scent ⇒ ~0 steps/level" (20 PP ≈ 2.5 levels) · the badge→**map** consequence list is RECALLED, only badge→field-move is VERIFIED · Jagged Pass silently dropped from T=20 without stating the (correct) reason · Artisan Cave "only access is the Lilycove ferry" — the Slateport S.S. Tidal script was never opened. |
| ⭐ **A defect the note inherited rather than found** | `TRAINING_GRASS`'s ROUTE102 band is `(3, 5)`; the ROM says **3–4**. The only mismatch of eleven audited — in the file whose own header argues hand-typed bands are how myths become load-bearing. |

### PokéNav angle
| Killed claim | Why |
|---|---|
| ⛔⛔ "**Calling a registered trainer arms them on the spot** — the player CAN initiate a rematch" (the ⭐⭐ headline answer to ruling 5) | `UpdateRematchIfDefeated` sits **only** inside `else if (ShouldTrainerRequestBattle(...))`, which returns TRUE for **at most one** matchCallId per game state. Calling anyone else arms **nobody**. Findings 6 and 7 of that note contradict each other and **6 is the wrong half**. |
| ⛔ "Route 121 is the money route (₽8,768/cycle)" | **Omits the top two by 73%**: CINDY and WINSTON, both **MAP_ROUTE104**, **₽7,200 each** from a single L36 Linoone ⇒ ₽14,400 in two single-mon battles on a no-Surf route. Also omitted: MIGUEL ₽3,040, ISABEL ₽2,800, JEFFREY ₽2,280, ANDRES ₽2,220 — all above the list's own #7. |
| "Our `event_flags/emerald.txt` has **none** of the 78 registered flags" | All 78 are there as `REMATCH_*`. And verifying it exposed the **off-by-one both agents missed** (§3). |
| "The arming state can go live while the pre-HoF Wally NPC does not exist" | Arming also requires the **REGISTERED** flag, set only by defeating `TRAINER_WALLY_VR_2`, which exists only at the post-HoF NPC. The pre-E4 fight is `WALLY_VR_1`, not `trainerIds[0]` of any row. *(Headline — post-HoF only — survives.)* |
| "Indices 0–63 = ordinary **route** trainers" + "stand next to the target and call them" | **11 of 64 are not on routes** (Meteor Falls ×2, Abandoned Ship ×2, Jagged Pass ×2, Mt Pyre ×2, Mt Chimney ×2, Petalburg Woods), and the call gate forbids indoor/cave maps — including the **two highest-level rows in the pool**. |
| Wrong citations | `battle_setup.c:1461-1463` for `trainerRematches[...] > 0` → **wrong file** (`match_call.c:1461-1463`); `game_stats.py:11` → `:17`. |
| Trimmed, not killed | "the L30–50 bracket map" (only 5/64 ≥L47) · "the **only** non-dungeon L30–52 ground in Hoenn" (never weighed never-yet-fought one-time trainers) · "the bot has been silently collecting armed rematches for its entire existence" (~25× too strong) · "≥5 badges" cites two *different* functions (`HasAtLeastFiveBadges` counts; `GetNumOwnedBadges` counts **consecutive** from badge 1) · `RegisterTrainerInMatchCall` is **not** called unconditionally · the renderer-on claim is an inference about production config. |

### Money angle
| Killed claim | Why |
|---|---|
| ⛔ "Rematches need the trainer **registered by talking to them again**" — and its dependent open question "is `TRAINER_REGISTERED_FLAGS_START + i` ever set in our runs? If not, ₽755,740 is unreachable" | Registration is **automatic** in `CB2_EndTrainerBattle` → `RegisterTrainerInMatchCall` for every won battle once `FLAG_HAS_MATCH_CALL` is set. The `register_matchcall` script lines only play the fanfare; the talk-again path is the fallback for trainers beaten *before* the PokéNav. ⇒ **the open question is void and our saves are already armed.** |
| ⛔ "**₽549,236 first-battle-only (524 trainers)** / ₽755,740 rematch (330)" | A **name-suffix artifact** (`_2`..`_6`), reproduced exactly and therefore diagnosable: it misclassifies **45 one-time story trainers** worth ₽42,736 — every Aqua/Magma Hideout, Seafloor Cavern, Space Center and Weather Institute grunt — as rematch money. Correct: **563 / ₽588,332** first-battle, 291 / ₽716,644 rematch. The ₽1,304,976 **total** survives exactly. |
| "Iron 6" in the vitamin census | It is **5**; the 6th grep hit is `FLAG_ITEM_METEOR_FALLS_1F_1R_TM_IRON_TAIL`. PP Max (×1) was omitted, so ₽220,500 survives by coincidence while its itemisation is wrong. |
| "Vitamins are **already on route**" | ≥14 of 45 are not: **6 are Artisan Cave (post-game)**, 5 are Dive-gated, 3 are Safari Zone. |
| "`on_pokenav_call` has **ZERO** implementations anywhere in the tree" / "the only pickup overrides are `puzzle_solver` + base" | Both false — `tests/utility.py:165-169` and `:147`. (Useful direction: a settable hook already exists, so a logger can be exercised without a live drive.) |
| ⛔ "Capturing who called costs **one** `on_pokenav_call` implementation" | The callback takes **no arguments** and no caller identity flows through `_listeners.py`; the only thing in the tree that touches match-call state **writes** it (`gui/debug_menu.py`). The cost estimate is wrong on the single most actionable claim against ruling 5. |
| Wrong citations | `LEAGUE_HEAL_BUDGET` at `:164` → **`:414`**; `match_call.c:1166-1175` for the six trigger conditions → **`:1147-1155`**. |
| Trimmed, not killed | Pickup ₽123/battle is the `frequency=1` number (shipped default gives ~₽101) · "at L50+ the rare slots are White Herb…" starts one slot late (L41–50 = Ether/White Herb) · Amulet Coin's gate chain and its "must be the lead" claim · "~58 rematch entries" → **64** · "255 steps **per attempt**" → per *granted* rematch; a failed roll leaves the counter at 255 · Grimer/Gulpin per-**mon** EV ≠ per-encounter (₽5 and ₽28) · the lottery is ruled out for the wrong reason. |

### Our-code angle
| Killed claim | Why |
|---|---|
| ⛔ **A FABRICATED QUOTE** — "`:512 return best, ...` / `return None` path" | Line 512 is `    return best`. There is no tuple return and no `return None` anywhere in the function. (The *proposition* holds only because `best = None` at `:489` — a different fact.) |
| ⛔ "This is the path that would run during **E4 prep**" | **E4 prep does not exist.** `_maintain_lagging_battler` has one caller, `_prepare_for_fight`, invoked for ten fights ending at Juan; `story_mode.py:5178-5179` says Chapter 24 is unbuilt. This was the claim that made the defect sound load-bearing for the E4. |
| ⛔ "Has `probe_vr_heal_roundtrip.py` ever been RUN? I found no recorded result" | It was run **2026-09-18** with a saved stdout artifact and four doc records. Its answer is sharper than the question: from inside VR the cross-map ask is **refused as malformed**; the same-map walk to the grind tile is 44 wp OK; **Ever Grande is SPLIT** (door 23 wp from (18,42), **NO PATH** from (18,6)). |
| ⛔ "`PokemonCenter.EverGrandeCity`" | Does not exist — the member is **`EvergrandeCity`** (`map_data.py:1537`). Written as proposed it raises AttributeError inside boss prep. |
| ⛔ The whole "RECOMMENDED MINIMAL CHANGE" is presented as open | **Superseded by a user ruling** (`06-DECISIONS-LOG.md:6214-6227`, 2026-09-18) that settles the ground, adds a constraint the recommendation lacks (*"Do not reopen B1F without a new ruling"*), and points the grind at the exit side. This is exactly the grep CLAUDE.md session-discipline rule 11 requires before escalating. |
| "Callers 2 and 3 are independent call sites; the relocation floor means the gym-prep path is not the hole" | They are **the same function in sequence** — the unfloored errand runs *first* inside the very `_prepare_for_fight` the floor is said to protect. |
| "Constant above **L29**"; "any 'is it fixed?' check must vary the level **across 29**" | Constancy begins at **L13** and **L28**. ⛔ The prescribed A/B is **VACUOUS** — L28 vs L30 returns the identical row in both arms. Real discriminators: 12→13 and 27→28. |
| "`allow=None` → ROUTE117 L13–14" as *the* production answer | **Zero** production call sites pass `allow=None`. Production gets **ROUTE121 L25–28**. Still the defect; different severity. |
| Wrong citations | VR rows `:159-162` → **`:149-151`** (`:159` is a SEAFLOOR comment); `counter_hunt.py:748-763` → `:724-746`; `counter_plan.py:325` → `:321`, `:346` → `:345`; `story_mode.py:1211-1214` → `:1207-1212` (the load-bearing fail-closed quote); `:3208` → `:3210`; `:2551-2553` → `:2560`; `:2694` → `:2688`; `debug_logger` also reads `XP_RATE_RELOCATE_RATIO`; `_hm_hunting_grounds` def is `:4577`. |
| Trimmed, not killed | The estimator's omission list misses the **×2 EXP split** and **×1.65 frames-per-win** (~3.3× optimistic — already a **closed** punch-list item, third re-discovery) · `_return_blocked`/NO_RETURN_GROUNDS omitted from the "only refusals" inventory · "a band 40 levels **above** scores identically" is foreclosed one line earlier by the winnability guard · "§Ch23 is already level-appropriate" is false against the ratified L62–75 goal. |

---

## 8. STILL UNKNOWN — and the cheapest experiment for each

| Unknown | Cheapest decisive experiment |
|---|---|
| ⭐ **The heal leg from a Victory Road grind tile.** The 2026-09-18 probe proves Ever Grande is split and that a cross-map ask from inside VR is refused as malformed — it does **not** prove a working round trip. | A chain-aware two-hop `_CAVE_EXITS` probe, then `calculate_path` from the **actual grind tile (15,39)** to the League **NURSE** (not a `PokemonCenter`), plus a control tile that DOES path. ⛔ Until this is green, every promotion plan rests on an unmeasured heal leg. |
| **Frames per battle at L38–42.** `FRAMES_PER_WILD_BATTLE = 1433` was measured on Route 102 L3–5 wilds; direction of the error is known (optimistic on time), magnitude is not. | 30 battles on VR 1F with the existing XP-event counter, same harness as the 83-event Route 102 run. Ruling 2 makes wall-clock the thing the user watches; no "hours to L75" number is legitimate until this exists. |
| **Does the bot actually have a Pickup mon with an EMPTY slot during the grind?** Machinery ships and is on; value is zero without the mon. | Log `party_indices_with_picked_up_items` over one real grind leg, with `pickup_check_frequency = 1` in the arm. `#24-ch23wally` records a L19 Zigzagoon fed into fights as a *defect* — the same mon is the money engine. |
| ⛔ **The rematch flag off-by-one** (ours 349 vs decomp 348; `REMATCH_JUAN` absent). | **One observation settles both the offset and the naming:** beat one known route trainer on a live save and diff the flag bitfield. Do this before any code reads these flags. |
| **SaveBlock1 offsets 0x9C8 / 0x9CA / 0x2E66** (decomp comments, not our measurement; invalid for R/S). | Walk 255 steps and watch `0x9C8` climb; win a rematch and watch `0x9CA + i` go non-zero → 0. |
| **`ShouldTrainerRequestBattle` end-to-end.** Arithmetic VERIFIED; the prediction never run. | Read `sRtc` (BCD day count — **not** `gLocalTime`), `dewfordTrends[0].rand`, `GAME_STAT_TRAINER_BATTLES`, `trainer_id`; predict the index; place that exact call; check the byte. A failed prediction means the day-count source or `GetNthRematchTrainerFought`'s ordering is wrong. |
| **The PokéNav Match Call list ORDER** (special trainers interleaved; our driver only ever selects entry 0) and **NPC talk-tiles for all 64 rematch trainers** (they never re-approach — `CheckTrainer` bails on a set first-battle flag). | Read `pokenav_match_call_data.c` / `MatchCall_GetRematchTableIdx`, then a live cursor capture. Wrong cursor = calling the wrong person. Tiles need `calculate_path` from a real captured position plus a control tile. |
| **Victory Road B1F/B2F spin tiles** — none anywhere in the repo. | A metatile dump from a post-Wally save (how 1F's `(15,39)` was found, MEASURED `Cave`). ⛔ Only worth doing if the user reopens B1F — it is currently ruled off the table. |
| **Shoal Cave room access at high tide** (INFERRED — the encounter header is keyed to the MAP, only the LAYOUT swaps). | A layout decode, not a script read. |
| **Which of the 45 vitamin flags are real map objects** (flag census ≠ map census; `flags.h` contains at least one R/S leftover). | Read each `data/maps/<Map>/map.json` before routing to any of them. The Nugget calibration was perfect (10 flags → 10 objects), so the census is a good upper bound and a bad budget. |
| ⛔ **A DESIGN QUESTION NO RESEARCH PASS CAN SETTLE:** what should the picker DO when the best candidate is 30 levels below the trainee — return `None` (and let every caller's fallback fire), or return it with a mismatch reason the caller logs? And what is N? | Ask the user. Today it returns it silently and no caller can tell a good pick from a fodder pick. |
| ⛔ **And the prior question:** does the fix belong in the picker at all, or in a **new post-Victory-Road training leg** keyed to ruling 4's milestone (first heal at the E4 nurse) that bypasses the picker the way §Ch23 already does? **Nothing in the tree is keyed to that milestone** — `_prepare_for_fight` / `_maintain_lagging_battler` fire per boss throughout the game. | Also a user/architecture call. Per this project's own measured rule, research enumerates what to look for and never decides what the bot does. |
