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
