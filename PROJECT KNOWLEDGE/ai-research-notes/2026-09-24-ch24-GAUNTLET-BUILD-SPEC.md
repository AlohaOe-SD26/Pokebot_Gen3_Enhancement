# §Ch24 ELITE FOUR — PRODUCTION BUILD SPEC (AGENT OUTPUT, 2026-09-24)

⛔⛔ **THIS IS A NOTE, NOT TRUTH** — the standing rule for every agent product in this tree
(`ai-research-notes/00-READ-THIS-FIRST.md`). It came from a 13-agent workflow: six recon angles,
each put through an ADVERSARIAL verifier told to refute it, then one synthesis over only the claims
that survived. That is a good process and it is still **not** verification.
⇒ **Verify every load-bearing claim at FILE:LINE before building on it.**

✅ **ALREADY VERIFIED BY HAND FROM THIS SPEC (2026-09-24):** its hazard **H5** — that
`overworld_items.py` named items that DO NOT EXIST. Confirmed against `modules/data/items.json`
(`Paralyze Heal` → `Parlyz Heal`), and new gate **#73** then found a second nobody knew about
(`Energy Powder` → `Energypowder`). Both fixed. ‼ H5's other half was OVERSTATED: the planner does
read `mon.status` (to skip healthy mōn) — what it never does is MATCH the cure to the status, which
is harmless only while `Full Heal` is first in `STATUS_ONLY` and stocked.

⛔⛔ **AND ONE OF ITS "UNMEASURED" CLAIMS IS ALREADY MEASURED — DO NOT RE-DO IT.** The spec treats
the room seal as needing live confirmation. **It has one.** Gate `probe_e4_entry_seal.py`
(`#24-leg2spec` O5) is exactly that live run: it confirms the six entry tiles
`(5,12) (6,12) (7,12) (5,13) (6,13) (7,13)` are set impassable **TRUE** on walking in and
re-applied from `ON_LOAD` so the seal survives a save/load. ⇒ the spec's **H1 is not a discovery**
— it is `KI-74`'s mirror image, already known and already gated: the entry tiles read PASSABLE in
ROM and are SEALED live, so **the planner will confidently plan a retreat the game refuses.**
‼ Read that gate before writing anything that routes backward inside the League.

⚠ **STILL GENUINELY UNVERIFIED, AND LOAD-BEARING:** the COMMITMENT POINT specifically — whether
the bot is committed at **lobby tile `(9,1)`** (the spec's claim, resting on an `MB_NORMAL`
inference nobody has confirmed by reading tile bytes) or only once inside Sidney's room, which
the gate above does confirm. That one reading decides **where a readiness check can still act** —
a guard that runs after the commitment point can only report a problem it can no longer fix.
Also unverified: the unbounded waits inside the seal (H4). The spec's §5 names the probes.

✅ **UPDATE — M1 (PART 1) IS NOW MEASURED; SEE THE SECTION AT THE END OF THIS FILE.** The lobby's
north door IS `Non-Animated Door` at `(9,1)`/`(10,1)`, two tiles wide, and **ROM agrees with LIVE
there** (no `KI-74` divergence at the lobby). The lobby is confirmed as a place a readiness check
can still act from: the nurse is reachable and the way out is 14 waypoints. ⚠ The **Mart is NOT**
reachable from `post_league_lobby.ss1`, confirming hazard **H7**. ✅✅ **AND M1 PART 2 NOW SETTLES THE COMMITMENT QUESTION — see the second section at the end.**
**6 of 6 backward warp tiles in the League interior read `Normal`** (behaviour 0) while forward
warps read as DOORS, and every behaviour the warp paths accept is non-zero ⇒ **the interior is
ONE-WAY and `pokemon_league.py:5-8` is CONFIRMED.** Read from ROM with live-known controls, so
**nobody had to walk in** — the walk-through experiment was designed, reviewed and then ABANDONED
as the worse instrument.

---

# §Ch24 ELITE FOUR — PRODUCTION BUILD SPEC

Targets: `sandbox-pokebot/modules/story/pokemon_league.py` (legs) and `sandbox-pokebot/plugins/custom_modes/story_mode.py:5274-5294` (dispatch, immediately after `train_for_league`; the "END OF BUILT CONTENT" banner at `:5280` moves again — P4).

## 1. THE COMMITMENT POINT

**Tile `(9,1)` / `(10,1)` on `EVER_GRANDE_CITY_POKEMON_LEAGUE_1F` (16,10).** Both are `MB_NON_ANIMATED_DOOR`, collision 0, step-on warps to `HALL5` (16,9) `(5,12)` ([DECOMP] `EverGrandeCity_PokemonLeague_1F/map.json` warp_events[2],[3]; step-on path `src/field_control_avatar.c:702-706`, whitelist `:751-765`). Every backward warp in the interior — Sidney/Phoebe/Glacia/Drake `(6,13)`, Champion `(6,12)`, ShortHall `(4-6,12)`, Hall4 `(5,33)` — is `MB_NORMAL`, which all three warp paths reject, so they are **destination-only**. Fly/Teleport blocked (`src/overworld.c:1366-1375`, all 11 maps `MAP_TYPE_INDOOR`); Escape Rope/Dig blocked (`allow_escaping:false` + `src/item_use.c:911-921`). `WalkInCloseDoor` (`data/scripts/elite_four.inc:19-29`) is a *second, redundant* seal.

⛔ **UNMEASURED LIVE.** No fixture exists with `FLAG_ENTERED_ELITE_FOUR` set, and nothing in this tree has ever stepped through `(9,1)`. **The measurement that settles it (M1/M2 below):** from `post_league_lobby.ss1`, stand `(9,3)`, press A; assert flag 263 (`emerald.txt:211`) flips False→True *and* live guard objects local_id 3/4 move to `(8,2)`/`(11,2)` by identity; then step Up and assert map == (16,9). CONTROL: in HALL5 at `(5,12)` press Down 60 frames and assert still (16,9), paired against lobby `(9,11)` (arrow warp) which MUST fire.

⇒ **The readiness check runs in the lobby, standing at `(9,3)`, before the guard A-press.** Nothing after that tile may refuse to continue.

## 2. THE READINESS CHECK

Assert, from live reads (never the harness's memory of them):
- `party_is_gauntlet_ready(_party_snapshot())` — `overworld_items.py:240-249` (no faint, no status, all > 0.90) and `pokemon_league.py:137`.
- Level floor: every mon ≥ `CH24_LEVEL_FLOOR` (`pokemon_league.py:1916` signature).
- Bag basket present: `bag_healing_stock()` (`victory_road.py:3035-3039`) ≥ `LEAGUE_BASKET` (`victory_road.py:439-443`).

**On failure it must REMEDY, not halt** (we are still outside the seal):
1. status/HP → `heal_at_league` (`victory_road.py:2893`, stand `LEAGUE_NURSE_STAND=(3,4)` `:391`, consumed `:2982`) — free, in-lobby.
2. basket short → `stock_for_the_elite_four` (`victory_road.py:3071`), which already re-reads the bag and raises if the purchase did not land (`:3236-3247`).
3. level short → `train_for_league` (`pokemon_league.py:1916`); it self-skips when nobody is below the floor.
Re-check after each remediation; bound the cycle to 3 passes. Only if it still fails do we log a named diagnosis and `set_manual_mode()` — **and only while still in the lobby.**

⛔ `heal_party_from_bag` returning is NOT readiness: the empty-plan path returns at `pokemon_league.py:295-298` without `heal_after` and without `R-HEALED` (added only at `:336`). Gate on `report["heal_ready"] is True`.

## 3. THE ROOM LOOP

Rooms 1-4 are byte-identically shaped (13×14, one object at `(6,5)`, entry warp `(6,13)`, exit door `(6,2)`, hall landing `(5,12)`, hall door `(5,2)`). One parameterised generator `fight_one_room(room, hall, next_map, victory_flag)`:

- **S0 arrive.** `WalkInCloseDoor` auto-walks 6 north to `(6,7)` under `lockall`. Issue no input; `wait_until_truly_controllable()` (`early_game.py:1257`, flicker docstring `:1260-1266`).
- **S1 dismiss** — B every 6 frames, budget 3,000.
- **S2 heal** — `heal_party_from_bag(report)` wrapped in `try/except` that RECORDS and continues (never raise past the seal; rationale verbatim `story_harness.py:17737-17744`). Record `heal_ready`; it is advisory here, load-bearing only in the grade.
- **S3 locate** — live `get_map_objects()`, pick the nearest object north of us, stand `(6,6)`, face Up. Never the template.
- **S4 engage** — `"B" if frames % 3 else "A"`, ungated, budget 4,000. Gated presses measured to stall at the intro (`story_harness.py:16103-16105`).
- **S5 battle** — inherits `StoryItemBattleStrategy` (`story_mode.py:3604`); assert `swap_train_active()` is False first (`:3590-3591`).
- **S6 grade** — `victory_flag` set, AND door open from `_live_collision_grid(room)` (`sootopolis.py:870`) with `(6,1)`/`(6,2)` == 0. ROM says 0 either way (§4 H1). Vacuous on a reloaded fixture (`story_harness.py:18379-18383`).
- **S7 exit** — `_hop(room, (6,2), hall, …)` then `_hop(hall, (5,2), next_map, …)` — `pokemon_league.py:921`/`:941-947` already grades arrival.

**Champion differs, structurally:** entry is `(6,12)` not `(6,13)`; HALL4 is 11×34 with a 31-step walk from `(5,33)` — **the last heal point in the game**. There is no `ON_LOAD`, no defeated-flag guard, and `VAR_TEMP_1` is zeroed on every warp-in, so `EventScript_EnterRoom` `lockall`s on the first frame and runs `trainerbattle_no_intro TRAINER_WALLACE`. ⇒ S1-S4 do not exist: step onto HALL4 `(5,2)` and the next controllable frame is post-battle. Grade on `FLAG_IS_CHAMPION` (2175), **never** the four `FLAG_DEFEATED_ELITE_4_*` — `ResetEliteFour` (`data/event_scripts.s:628-634`) clears them ON A WIN. Everything after the win (scripted warp to Hall of Fame `(7,16)`, credits, `SoftReset(RESET_ALL)`) is **UNMEASURED — measure before building** (M6).

## 4. HAZARDS

- **H1 KI-74 planner blindness (survived, measured).** `calculate_path` reads ROM blockdata (`map.py:770-771`, cache `:735-755`); `setmetatile` writes EWRAM (`src/scrcmd.c:2035-2049`, `src/fieldmap.c:357-365`). A sealed `(6,13)` reads collision 0 in ROM, 3 live, and the planner returned a 7-waypoint route into it. ⇒ **whitelist destinations**; never `(6,13)`, `(5-7,12)`, `(5-7,13)` in a cleared room, no "step back to unstick".
- **H2 silent false success.** `navigate_to`'s warp override is lost on re-path (`walking.py:442-481`), so an inert-warp target can return *success* with the player on the near side. ⇒ every traversal goes through `_hop`/`_goto_warp` (`pokemon_league.py:921`, `:949`), which assert the arrival map.
- **H3** `_pass_through_door` has no post-condition (`early_game.py:422-439`). Wrap in `victory_road._budgeted` (`:619-654`: per-frame `_check_abort`, `gen.close()`, button reset) — **not** the harness's `_budgeted_local`, which has none. This is a behaviour change; drive it.
- **H4 unbounded waits inside the seal.** `pokemon_league.py:204` and `:330` call `wait_for_task_to_start_and_finish` (`modules/modes/util/tasks_scripts.py:40-48`) — no counter, no raise. Bound both before shipping.
- **H5 heal planner defects.** `overworld_items.py:188` picks the first held `STATUS_ONLY` item **without reading `mon.status`** → refused use → `heal_party_from_bag` raises at `:317-325` inside the seal. `"Paralyze Heal"` (`:62`, `:152`) is a phantom; the real name is `"Parlyz Heal"`. Fix or fence both before wiring.
- **H6** `_party_snapshot` indexes list positions (`pokemon_league.py:140,147`) driven into physical `gPartyMenu.slotId`; a party hole desynchronises them.
- **H7 lobby.** `navigate_to(LEAGUE_1F,(9,11))` means LEAVE (14th waypoint presses Down). The Mart clerk (local_id 2) was **not spawned** in `post_league_lobby.ss1` and paths to `(16,2)` refuse — understand that before writing a Mart leg.
- **H8** in-battle heal gate 0.35 (`battle_items.py:40,:78`) sits below measured E4 damage bands (`29-DISABLED-FEATURES-REGISTRY.md:202`).

## 5. MEASURE BEFORE WRITING CODE (ordered)

1. **M1 commitment probe** — §1 above, with the `(9,11)` control. New `--driver ch24commit`.
2. **M2 door-drive** — `_hop` lobby`(9,1)`→HALL5, HALL5`(5,2)`→SIDNEY. Settles whether our nav drives a step-on `MB_NON_ANIMATED_DOOR` at all.
3. **M3 seal fault arm** — from `post_sidney_door_open.ss1`, navigate to `(6,13)` and log outcome/frames. Converts H1's *failure mode* from inference to evidence.
4. **M4 room-1 heal** — never exercised (`Ch24ProbeMode` has no heal step). Add the heal, assert `heal_ready`.
5. **M5 bag dump** from `post_ch24ready.ss1`/`post_league_shop.ss1` — does H5's trigger (Antidote/Parlyz Heal) ever exist?
6. **M6 Champion tail** — extend `Ch24TailProbeMode` (`story_harness.py:19276`) through `(5,2)`, logging every state, frame counts to credits, and whether the harness survives `SoftReset`.
7. **M7 heal hang** — fault-inject a context menu that never opens; confirm H4's new bound raises.

## 6. FAULT ARMS (one per guard; each must FAIL the run when armed)

`POKEBOT_CH24_FAULT_NOREADY` (skip §2 check) · `..._NOREMEDY` (check fails, remediation disabled) · `..._NOROOMHEAL` (existing) · `..._HEALNOOP` (`max_actions=0`, existing) · `..._NOENGAGE` (existing) · `..._NOARRIVE` (bypass `_hop`'s arrival assert) · `..._RETREAT` (navigate to `(6,13)` in a cleared room — M3's instrument) · `..._NOCHAMPGRADE` (grade room 5 on the DEFEATED flags; must fail on a WIN) · `..._UNBOUNDHEAL` (restore the unbounded task wait). All scoped to gauntlet legs only.

---

# ⭐ M1 (PART 1) MEASURED, 2026-09-24 — LEAGUE LOBBY FACTS

`probe_league_lobby_facts.py`, **observe-only** (no button pressed, no step taken), from the pinned
fixture `post_league_lobby.ss1`. Evidence: `evidence/2026-09-24-league-lobby-facts.stdout.txt`.

**Standing: `EVER_GRANDE_CITY_POKEMON_LEAGUE_1F (3,4)` — which is `LEAGUE_NURSE_STAND` itself**
(`victory_road.py:391`). The fixture parks the bot on the nurse tile.

## WHAT IS NOW MEASURED RATHER THAN INFERRED

| tile | ROM | LIVE | agree | `tile_type` |
|---|---|---|---|---|
| **(9,1)** | 0 | 0 | SAME | **Non-Animated Door** |
| **(10,1)** | 0 | 0 | SAME | **Non-Animated Door** |
| (8,1) | 1 | 1 | SAME | Normal |
| (11,1) | 1 | 1 | SAME | Normal |
| (9,2) / (10,2) | 0 | 0 | SAME | Normal |

✅ **The build spec's claim that the lobby's north door is `MB_NON_ANIMATED_DOOR` at `(9,1)`/`(10,1)`
is CONFIRMED LIVE**, and the door is exactly **two tiles wide** — `(8,1)` and `(11,1)` are blocked.
✅ **AND ROM AGREES WITH LIVE HERE** — there is **no `KI-74` divergence at the lobby door**. That
matters: `KI-74` and `probe_e4_entry_seal.py` both found ROM/live disagreement *inside* the rooms, so
it was reasonable to expect it at the lobby too. It is not there.

## ⭐ THE DESIGN FACT THE GUARD DEPENDS ON

| destination | `calculate_path` from `(3,4)` |
|---|---|
| nurse stand `(3,4)` | **0 waypoints** — already standing on it |
| lobby south exit `(9,11)` (toward Ever Grande) | **14 waypoints** — reachable |
| mart clerk approach `(16,3)` | ⛔ **REFUSED — `PathFindingError`** |

⇒ **THE LOBBY IS A PLACE WHERE A READINESS CHECK CAN STILL ACT AND STILL RETREAT.** Its failure
branch can heal (the nurse is right there) and can leave (14 wp to the exit). That is the empirical
basis for putting the guard here rather than anywhere past the door.

⚠ **BUT THE MART IS NOT REACHABLE FROM THIS FIXTURE** — which CONFIRMS the build spec's hazard **H7**
(*"the Mart clerk was not spawned in `post_league_lobby.ss1` and paths to it refuse"*). ⇒ a readiness
branch that plans to **restock** cannot be written against this fixture, and must not be assumed to
work until a state with the clerk spawned is captured.

## ⛔ WHAT IS STILL NOT SETTLED — AND THE PROBE SAYS SO ITSELF

**Whether stepping onto `(9,1)` COMMITS the run.** `tile_type` says the tile is a door, i.e. the
**forward** warp is real. It says nothing about whether the **return** warp from `HALL5` fires — and
that is the whole commitment question. The spec's claim is that every backward warp sits on
`MB_NORMAL`, which the warp code rejects; **that half remains unread.**
⇒ It needs the walk-through arm: step through on a fixture, then try to walk back. That is
deliberately a **separate** probe, so that the observe-only one can never be the thing that seals a
run. ‼ Collision says what can be *walked on*, never what happens *after*.

---

# ⭐ M1 (PART 2), 2026-09-24 — **THE HALL RETURN WARPS ARE INERT** (⛔ AN EARLIER VERSION OF THIS
# SECTION CLAIMED MORE — SEE THE CORRECTION AT THE END OF IT BEFORE QUOTING ANYTHING BELOW)

`probe_league_return_warps.py`. Evidence: `evidence/2026-09-24-league-return-warps.stdout.txt`.
**No step is taken and no button is pressed** — it reads tile behaviour straight out of ROM for maps
the bot is *not* standing on, which is how `probe_e4_entry_seal.py`'s `rom_collision()` already works.

## THE RESULT

| what | map | tile | coll | `tile_type` |
|---|---|---|---|---|
| CONTROL lobby fwd door | `POKEMON_LEAGUE_1F` | (9,1) / (10,1) | 0 | **Non-Animated Door** |
| CONTROL lobby wall | `POKEMON_LEAGUE_1F` | (8,1) / (11,1) | 1 | Normal |
| **HALL5 back to lobby** | `HALL5` | (4,12) (5,12) (6,12) | 0 | **Normal** |
| HALL5 fwd to Sidney | `HALL5` | (5,2) | 0 | Non-Animated Door |
| **HALL1 back** | `HALL1` | (5,12) | 0 | **Normal** |
| **HALL4 back** | `HALL4` | (5,33) | 0 | **Normal** |
| ⛔ ~~SIDNEY back to Hall5~~ | `SIDNEYS_ROOM` | (6,13) | ~~0~~ | ⛔ **VOID — ROM IS STALE HERE. LIVE=3** |
| ⛔ ~~SIDNEY fwd to Hall1~~ | `SIDNEYS_ROOM` | (6,2) | ~~1~~ | ⛔ **VOID — ROM IS STALE HERE. LIVE=0** |

**5 of 5 HALL backward warp tiles read `Normal`; the HALL forward warps read as DOORS.**
⛔ *An earlier version said "6 of 6", counting a SIDNEY row that is void — see the correction.*

⇒ ✅ **`MB_NORMAL` is behaviour 0, and every behaviour the three warp paths accept is NON-ZERO**, so a
warp event on such a tile **can never fire**. ⇒ **THE HALL-TO-LOBBY RETURN WARPS ARE INERT.**
‼ **THAT IS NOT THE SAME CLAIM AS "the interior is one-way", AND AN EARLIER VERSION OF THIS
SECTION CONFLATED THEM.** The ROOMS are sealed by a RUNTIME rewrite this reader cannot see; that
half is live-confirmed separately by `probe_e4_entry_seal.py`. **The two together support
`pokemon_league.py:5-8`; neither alone does.**

## ⭐ WHY THIS IS BELIEVABLE — THE CONTROLS, AND AN ACCIDENT THAT CORROBORATED IT

* **The instrument proves itself in the same run.** The four lobby tiles have a LIVE measurement from
  2026-09-24 (`evidence/2026-09-24-league-lobby-facts.stdout.txt`). All four reproduce exactly. ⇒ the
  static reader is not being trusted on faith; it is being trusted **where it already agrees with a
  live reading on the same tileset**, and the probe VOIDS its own verdict if they diverge.
* **The vacuity check is what makes "everything is Normal" mean anything.** If forward warps also read
  `Normal`, the probe would be measuring nothing and says so. They do not: forward warps are doors.
* ⛔⛔ **WHAT I CALLED "AN UNPLANNED CORROBORATION" WAS ITSELF THE BUG.** I wrote that
  `SIDNEY (6,2)` reading `Normal`/collision **1** — *"blocked as shipped"* — showed the static data
  agreeing with the decomp's account of a runtime `setmetatile`. **It showed nothing of the kind.**
  `probe_e4_entry_seal.py` measures that tile LIVE as **ROM=1, LIVE=0**. ⇒ the reading I presented
  as *independent confirmation of the mechanism* was **an artifact produced by that very
  mechanism** — a stale pre-runtime snapshot. ‼ It is the most dangerous shape of wrong: a wrong
  row that was used to BUILD CONFIDENCE in the other rows.

## ⛔⛔ AND THE EXPERIMENT THIS REPLACED WAS THE WRONG ONE

The obvious test was to **walk through the lobby door on a fixture and try to walk back**. It was
designed, adversarially reviewed, and then **abandoned in favour of this**, because it is worse in
three specific ways:

1. **A false "COMMITTED" is cheap to produce and expensive to believe.** *"We are still in the hall"*
   reads identically whether the warp is inert, the bot never moved, the button cadence was wrong, a
   script was mid-flight, or a wait bound expired. ⇒ the failure mode of that probe is a **confident
   wrong answer that would be baked into the gauntlet design permanently.**
2. ⛔⛔ **IT WOULD HAVE POISONED THE REAL BOT'S RESUME POINT.** `libmgba.py:144` **loads**
   `current_state.ss1` at startup and `:226` **overwrites it** at shutdown. Probes are immune because
   they load a named fixture immediately — **the real bot is not.** ‼ And `is_test_run` guards only
   the LOAD, not the WRITE, so it is not a fix. A walk-through ending inside the gauntlet would have
   left the next unattended run resuming mid-commitment.
3. It answers for **one** tile. This reads **every backward warp in the interior** at once.

⇒ **THE RULE WORTH KEEPING:** *before running an irreversible experiment, ask what READS the same fact
non-destructively.* Here the answer was sitting in a helper the tree already used for something else.

## ⛔ WHAT IS STILL NOT SETTLED

* This is the ROM's **static** view — the tiles **as shipped**. The seal applied *inside a room* is a
  runtime `setmetatile`, invisible to this reader by construction. That half is already LIVE-confirmed
  separately by `probe_e4_entry_seal.py`, so the two together cover both halves.
* ⚠ **UNVERIFIED BY US:** the recon's claim that two guard objects at `(9,2)`/`(10,2)` physically block
  the approach until `FLAG_ENTERED_ELITE_FOUR` is set. Our static read shows those tiles as `Normal`
  collision 0 — **object occupancy is not collision**, so this probe *cannot* see it. It matters for
  the gauntlet's first leg (the bot must clear the guards to reach the door at all) and needs a live
  object read before anything depends on it.

---

# ⭐⭐ M2 MEASURED, 2026-09-24 — **THE GUARDS ARE REAL, AND THE LEG'S FIRST ACT IS NOT A NAVIGATE**

`probe_league_guards.py` on `post_league_lobby.ss1`. **Observe-only** — presses nothing, steps nowhere.
Evidence: `evidence/2026-09-24-league-guards.stdout.txt`.

| reading | value |
|---|---|
| `ENTERED_ELITE_FOUR` | **False** |
| guard 1 | `local_id=3`, gfx 33, Face Down, at **(9,2)** |
| guard 2 | `local_id=4`, gfx 33, Face Down, at **(10,2)** |
| nurse | `local_id=1`, gfx 58, at (3,2) |
| `calculate_path` → (9,1) and (10,1) | ⛔ **REFUSED — `PathFindingError`** |

⇒ ✅ **The decomp-derived claim is now LIVE-MEASURED:** while the flag is unset, the two guards
occupy **the only two approach tiles** to a door that is exactly two tiles wide. **A production leg
cannot simply navigate to the door.**

## ⭐⭐ THE PLANNER RESULT IS THE INTERESTING ONE, AND ITS MECHANISM IS NOW KNOWN

I predicted the `KI-48` silent-stall shape: the planner is NPC-blind, so it would route *through* the
guards and the navigator would wait forever against an object. **It did not. It refused.**
‼ A refusal is an exception a leg can catch; a silent wait is not. That is the better failure.

⛔⛔ **BUT THE HAZARD IS REAL — IT SIMPLY DID NOT FIRE AT THIS DISTANCE, AND THE REASON MATTERS:**
* `map_path.py:810-817` iterates **`get_map_objects()` — the LIVE list** — and blocks each object's
  `current_coords` **and** `previous_coords`. The guards were loaded, so the planner blocked
  `(9,2)`/`(10,2)`, and with the only approach gone `(9,1)` became unreachable. **That is why it
  refused.**
* `map_path.py:431-440` instead blocks the **TEMPLATE** tile (`map_data.objects` →
  `local_coordinates`) for an object that is **not loaded**. For these guards the template is
  **(8,2)/(11,2)** — the POST-flag positions — which leaves **(9,2)/(10,2) OPEN**.
⇒ **From far enough away that the guards are outside the object window, the planner will happily plan
a route straight through them.** The refusal measured here is a property of *standing close*, not a
property of the map. ‼ **Do not turn this reading into a safety assumption.**

## ✅ AND THE RECIPE ALREADY EXISTS, LIVE-VERIFIED ONCE

`Ch24ProbeMode` (`story_harness.py:15939-15952`) already implements the interaction: navigate to
**(9,3)**, `ensure_facing_direction("Up")`, then a **bounded** A-press loop (30 × 8 frames) with
`_check_abort()` and two break conditions. `post_sidney_L75.ss1` was captured from it on
`ACCEPTANCE: PASS` with the `P24-HALL5` reading — *"we reached HALL5, the guards let us through"*.
⇒ the leg does **not** need to invent this; it needs to **port and instrument** it.

‼ The guard checks **only `FLAG_BADGE06_GET`** (decomp) — no party, level, Pokédex or item check —
and our fixtures carry all eight badges. ⇒ **the readiness question is entirely ours to impose**; the
game will let an under-levelled party through without comment.

## ⛔ A CONTRADICTION INSIDE OUR OWN HARNESS, FOUND AND FIXED

`story_harness.py:15819` read *"talk the guards from (9,3) facing N; **they step onto (9,2)/(10,2)**"*
— **backwards**, and it contradicted the same file ~120 lines below (*"They stand ON (9,2)/(10,2)
until spoken to"*). The measurement settles it: they **start** there and **vacate** to (8,2)/(11,2),
which is what `map.json` lists because `copyobjectxytoperm` writes the post-flag positions back.
✅ Corrected, with the measurement cited as its warrant.

## ⚠ WHAT THE PROBE ITSELF GOT WRONG FIRST — BOTH CAUGHT BY ITS OWN SAFETY DESIGN

1. **Class confusion.** It read `ObjectEventTemplate`'s API (`local_coordinates`, `kind`) off the
   **live** `ObjectEvent` (`current_coords`) — two classes in `map.py` with overlapping names
   (`:1107` live, `:1588` template). Every row returned `AttributeError`.
   ⭐ **The camera-range guard is what stopped that becoming a false finding:** it reported
   **UNKNOWN**, not *"no guards visible ⇒ the way is clear"*. An unreadable object and an absent
   object produced **different verdicts**, which is exactly what that guard was built for.
2. **A verdict contradicted by its own log.** The first verdict asserted *"the planner will still
   return a route… WILL STALL"* while the same output printed `REFUSED`. ⇒ the probe now **reports
   which failure mode occurred** rather than asserting a predicted one, and prints the loud case and
   the silent case differently.
3. ✅ Added a **flag-name vacuity guard**: `get_event_flag` returns **False silently** for an unknown
   name (`memory.py:336-338`), and no row in `event_flags/emerald.txt` carries the `FLAG_` prefix —
   so `"FLAG_ENTERED_ELITE_FOUR"` would have printed a hardcoded False that looks like a reading.

## ⇒ THE LEG'S ORDERED STEPS, WITH STATUS

| # | step | status |
|---|---|---|
| 1 | assert premise: on `LEAGUE_1F`, controllable | ✅ fixture is exactly this |
| 2 | vacuity-guard the flag name, then read `ENTERED_ELITE_FOUR`; skip 4-6 if already True | ✅ pattern proven |
| 3 | heal at the nurse — **the last heal before the seal** | ✅ `heal_at_league` exists |
| 4 | navigate to **(9,3)** — never aim at (9,1)/(9,2) | ⚠ **path from (3,4) UNWALKED**, and exposed to the template-vs-live hazard above |
| 5 | face Up; bounded A-press loop | ✅ live-verified once |
| 6 | ⛔ **CONFIRM IT WORKED** — flag True **and** (9,2)/(10,2) empty by live object read | ⛔ **nothing in the tree asserts this today**; `ch24probe` checks only "are we on HALL5", i.e. the consequence two steps later |
| 7 | step onto (9,1) ⇒ arrive HALL5 — **the commitment point** | ✅ live-verified once |
