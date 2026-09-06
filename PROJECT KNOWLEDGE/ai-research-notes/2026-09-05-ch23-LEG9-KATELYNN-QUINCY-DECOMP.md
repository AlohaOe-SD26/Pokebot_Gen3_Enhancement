# §Ch23 leg 9 — KATELYNN + QUINCY: decomp ground truth and why the fight is a DOUBLE at all

> ⚠ **THIS IS AN AI RESEARCH NOTE, NOT TRUTH.** See `00-READ-THIS-FIRST.md`. The authoritative docs win
> on any contradiction until a claim here is verified in our own harness. Produced 2026-09-05 by a Claude
> subagent reading **pret/pokeemerald master `5eff78649e7170a877b961ef0b3da13b81a16038`**; the agent
> byte-diffed the five cached `src/*.c` files it used against upstream and reported them identical.
> ⛔ The single most actionable claim below — the **(33,17) bypass** — is **NOT yet walked in the harness**
> and must be treated as a hypothesis until it is.

## ‼ THE HEADLINE — the premise everyone (including this project's own docs) had wrong

**Katelynn and Quincy are NOT a scripted double pair.**

* `include/constants/opponents.h:328-329` — `TRAINER_QUINCY 324`, `TRAINER_KATELYNN 325`
* `data/maps/VictoryRoad_1F/scripts.inc:108-116` — **both use `trainerbattle_single`**, no partner field
* `src/data/trainers.h:3899`, `:3911` — **both `.doubleBattle = FALSE`**

The fight is a double **emergently**, because both trainers spot the player on the same step
(`src/battle_setup.c:1274-1275`, in `BattleSetup_StartTrainerBattle`):

```c
if (gNoOfApproachingTrainers == 2)
    gBattleTypeFlags = (BATTLE_TYPE_DOUBLE | BATTLE_TYPE_TWO_OPPONENTS | BATTLE_TYPE_TRAINER);
```

`src/trainer_see.c:214,228` accumulates the second spotter, then calls `SetUpTwoTrainersBattle()`.

⇒ ⭐⭐ **WHY THIS MATTERS MORE THAN THE STATS BELOW.** Our in-battle healing policy is unreachable in
DOUBLE battles by inheritance — `StoryItemBattleStrategy` (`story_mode.py:417`) overrides `decide_turn`
but not `decide_turn_in_double_battle`, so doubles resolve up the MRO to `story_mode.py:261`, which never
calls `_maybe_use_item` (verified directly in our tree, 2026-09-05). **So the battle type is the thing
that disables our items — and the battle type is a consequence of HOW WE APPROACH, not of trainer data.**
Engaging them one at a time is therefore not merely "easier"; it puts the fight back into the branch
where our item policy actually runs.

## The parties — all level 43, two mons each, NO held items

Macro `NO_ITEM_CUSTOM_MOVES` (`include/data.h:68`) ⇒ custom movesets, `partySize = 2`, and **held items
are not settable by this macro**. `src/data/trainer_parties.h:4272-4300`. `.iv = 100` ⇒ `fixedIV = 12`
in every stat (`src/battle_main.c:2013`), 0 EVs.

| Trainer | Slot | Species | Lv | Moves | Ability |
|---|---|---|---|---|---|
| **Quincy** | 1 | **SLAKING** | 43 | Attract, Ice Beam, Thunderbolt, Flamethrower | **Truant** |
| | 2 | DUSCLOPS | 43 | Skill Swap, Protect, Will-O-Wisp, Toxic | Pressure |
| **Katelynn** | 1 | **GARDEVOIR** | 43 | Skill Swap, Psychic, Thunderbolt, Calm Mind | **Synchronize** |
| | 2 | **SLAKING** | 43 | Earthquake, Shadow Ball, Aerial Ace, Brick Break | **Truant** |

Abilities from `src/data/pokemon/species_info.h:10313, 11153, 10193`. Ability slot is `personality & 1`
(`src/pokemon.c:2296-2299`); both personalities' low bytes are even ⇒ **slot 0**, so Gardevoir is
**Synchronize, not Trace**.

Computed stats (L43, IV 12, 0 EV, **neutral nature — natures NOT computed**):
Slaking ×2 — HP 187, **Atk 147**, Def 96, SpA 91, SpD 66, Spe 96 · Gardevoir — HP 116, **SpA 117,
SpD 109**, Def 66, Spe 78 · Dusclops — HP 92, **Def 121, SpD 121**, SpA 61, Spe 31.

⭐ **BOTH SLAKINGS HAVE TRUANT — they attack only every other turn.** That is the single biggest
exploitable weakness on the field.

**AI flags**, identical for both (`trainers.h:3900`, `:3912`):
`AI_SCRIPT_CHECK_BAD_MOVE | AI_SCRIPT_TRY_TO_FAINT | AI_SCRIPT_CHECK_VIABILITY` — competent, not top tier.

**⚠ ONE Full Restore total, not two.** Both declare `.items = {ITEM_FULL_RESTORE, ...}`
(`trainers.h:3898`, `:3910`), but only opponent A's items load —
`src/battle_ai_script_commands.c:303` reads `gTrainers[gTrainerBattleOpponent_A].items[i]` into a
**single shared** `BATTLE_HISTORY->trainerItems`. Used only below 1/4 max HP
(`src/battle_ai_switch_items.c:857-863`), and gated by battle type, **not** by aiFlags — it will happen.

**Field layout** (`src/battle_main.c:697-699`): opponent A → `gEnemyParty[0..2]`, B → `[3..5]`, so turn 1
is **Gardevoir + a Slaking**, with the second Slaking and Dusclops in reserve.

⇒ ⛔ **AND NOTE WHAT THIS TABLE SAYS ABOUT OUR PARTY: the opposition is L43 and our party was
L52/L48/L47/L47.** We were never underlevelled. This independently corroborates the measured root cause
(attrition — the bot arrived with Sceptile 0/145 and Wailord 0/226 already fainted). **Grinding was
never the fix.**

## The geometry, and the bypass that costs nothing

`data/maps/VictoryRoad_1F/map.json` — **Katelynn (29,17)** `MOVEMENT_TYPE_FACE_RIGHT`;
**Quincy (32,17)** `MOVEMENT_TYPE_FACE_LEFT`; both `trainer_sight_or_berry_tree_id: "2"`.
FACE_RIGHT = `DIR_EAST`, FACE_LEFT = `DIR_WEST` (`src/event_object_movement.c:361-362`); sight is a
straight ray of N tiles in the facing direction only (`GetTrainerApproachDistanceEast/West`,
`src/trainer_see.c:349-370`).

```
   x=  29    30    31    32    33
 y=17  [K]>>  ..    ..  <<[Q]   ..     <- (33,17) is east of Quincy, who faces WEST
```

* Katelynn (east, N=2) sees **(30,17), (31,17)**
* Quincy (west, N=2) sees **(31,17), (30,17)**

⛔ **The two cones are identical — there is no tile that trips only one of them.** Walking the row is
all-or-nothing, which is exactly why our drive got the double.
‼ **Our bot's fatal battle began at pos=(31,17)** (`Story-debug-20260905-172610.log:314-318`) — dead
centre of both cones. That is the independent confirmation that this pair is the one we lost to.

**The bypass:** the agent decoded `data/layouts/VictoryRoad_1F/map.bin` (46×45; collision = bits 10-11,
elevation = bits 12-15 per `include/global.fieldmap.h:7-12`) and ran BFS with Emerald's real elevation
rules (`IsElevationMismatchAt` :7707, `ObjectEventUpdateElevation` :7759, `AreElevationsCompatible`
:7789). **(33,17) is walkable**, and a route via `(32,19) (32,18) (33,18) (33,17) (33,16) (33,15)
(32,15) (32,14)` reaches the Ever Grande exit warp `(39,5)` with `(30,17)` and `(31,17)` FORBIDDEN —
**61 steps, identical to the natural route.** No coord trigger forces the fight (the map's only
`coord_events` are the two Wally triggers at `(2,23)`/`(3,23)`).

## THREE options, all decomp-verified reachable

1. **Skip entirely** — route through `(33,17)`. **+0 steps.**
2. **Split into two singles** — stand at `(29,16)` / `(32,16)` (or the `,18` equivalents) and interact;
   interaction runs `trainerbattle_single`. None of `(29,16)`, `(29,18)`, `(32,16)`, `(32,18)` lie in any
   sight cone. ⭐ **This is the option that also re-enables our in-battle item policy** (see the headline).
3. **Beat one, then walk the row** — a defeated trainer returns 0 from `CheckTrainer`
   (`src/trainer_see.c:275-277`), so the survivor spots you alone ⇒ single.

*Verified but NOT useful:* the `y=17/18, x=29..33` patch is map-elevation 15 (a crossing); a player on
the **elevation-4** corridor is invisible to these elevation-3 trainers
(`DoesObjectCollideWithObjectAt` requires `AreElevationsCompatible(3,4)` = FALSE). That corridor is in
the **entrance** component, not the exit component, so it does not help the exit route.

*Noted, not a strategy* (`src/trainer_see.c:217-218`): after the first spotter,
`if (GetMonsStateToDoubles_2() != PLAYER_HAS_TWO_USABLE_MONS) break;` — with fewer than two usable mons
you get a **single** instead. ‼ Which means a badly-attrited party silently changes the battle type —
worth knowing before reading any future log.

## ✅ WHAT I VERIFIED MYSELF, AGAINST OUR OWN CACHE (2026-09-05, not the agent's recall)

The agent's geometry was re-checked against **our own cached decomp copy** in
`tools/story-dev/.cache/victory_road/` — a source independent of what the agent remembered. Commands
are in the session log; the cache files are `data__maps__VictoryRoad_1F__map.json` and
`data__layouts__VictoryRoad_1F__map.bin`.

**Object data — every field matches the agent exactly:**
```
Katelynn  x=29 y=17  elev=3  MOVEMENT_TYPE_FACE_RIGHT  sight=2
Quincy    x=32 y=17  elev=3  MOVEMENT_TYPE_FACE_LEFT   sight=2
coord_events on this map: ONLY (2,23) and (3,23) — both Wally triggers
```
⇒ the sight cones are confirmed identical ((30,17) and (31,17)), **and no coord trigger forces the
fight**. ‼ Our bot's fatal battle began at **(31,17)** — inside both cones.

**Layout — decoded independently.** The cached `.bin` is **4140 bytes = 46 × 45 × 2**, matching the
agent's stated dimensions; collision = bits 10-11, elevation = bits 12-15:

| tile | collision | elevation | walkable |
|---|---|---|---|
| (29,17) Katelynn | 0 | 15 | yes |
| (30,17) cone | 0 | 15 | yes |
| (31,17) cone — **our fatal battle** | 0 | 15 | yes |
| (32,17) Quincy | 0 | 15 | yes |
| **(33,17) THE PROPOSED BYPASS** | **0** | **15** | **YES** |
| (33,18) / (33,16) bypass path | 0 | 15 / 3 | yes |
| (32,16) / (29,16) split-single tiles | 0 | 3 | yes |

⇒ ⭐ **THE BYPASS TILE IS GENUINELY WALKABLE, AND SO ARE THE SPLIT-SINGLE TILES** — confirmed from our
data, not from recall. The elevation-15 crossing patch is confirmed too.

⛔ **WHAT THIS DOES *NOT* ESTABLISH, AND THE DISTINCTION MATTERS.** Per-tile walkability is not a ROUTE.
I did **not** run a BFS, did **not** run our own `calculate_path`, and did **not** walk it live. The
agent's "61 steps either way" is still **its** number, unverified here. ⇒ **the bypass remains a
hypothesis with verified geometry** — a strictly stronger position than before, and still short of the
live probe the project's rules require before building on it.

## ⛔ GAPS — stated, not filled

* **NOT WALKED IN OUR HARNESS.** `(33,17)` and the `(29,16)`/`(32,16)` interaction tiles are decomp BFS
  results. Per project rule they are a note until a live probe confirms them. **That probe is cheap and
  decisive; do it before building either route.**
* **Coordinates are decomp map-local.** If our map frame uses a different origin, translate first.
* **Which trainer is opponent A vs B** was not traced (depends on object-event spawn order). It does not
  change the conclusion — both declare the identical single Full Restore, so the enemy side gets one
  either way.
* **Natures not computed** — the name-hash (`battle_main.c:2000-2012`) depends on species-name casing,
  which differs between decomp revisions. Stats above are neutral-nature.
* The agent read **vanilla US Emerald decomp, not our actual ROM**, and ran **no live emulator probe**.
