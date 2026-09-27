# 2026-09-27 — RULING 20 Phase 1, increment B: box-first recon for Strength, Waterfall, Fly and counters (a NOTE)

> ⛔ **A NOTE, NOT A SOURCE OF TRUTH.** Four read-only Claude agents (one per site), 2026-09-27, on branch
> `wt/r20phase1` at `8cac9095` (before any increment B code). Their line citations refer to THAT revision; the Strength
> build has since moved `early_game.py` lines. Each load-bearing claim is re-verified at build time, in the site's own
> PREDICTIONS / GRADED notes. Design: `2026-09-27-ruling20-phase1-DESIGN.md`.
>
> **Build order taken from this recon** (smallest and cleanest first):
> 1. Strength (the heal-stop caller only; the in-hideout caller stays party-only). BUILT first:
>    `2026-09-27-r20strengthbox-PREDICTIONS.md`.
> 2. Waterfall (inside `ensure_waterfall_learner`; the generic gate never fires on the saturated shape).
> 3. Counters (a new `box_counter_choice`, plus an owed-only withdraw source, hazard H1).
> 4. Fly (a lobby-PC trip plus a per-map PC stand tile, plus RULING 21's swap-back obligations).
>
> **Open design points** (not user rulings yet): counter H3 (a box-first counter arrives untrained), and which fighter
> RULING 21's swap boxes.



## SITE: strength
**STRENGTH site: findings for Increment B (read-only; scratch probes only)**

**Bottom line:** add box-first to `ensure_strength_learner` behind a new `heal_centers=()` parameter. Pass `(center,)` only at the heal-stop caller `early_game.py:8309`, and leave the in-hideout caller `:9010` party-only. No fixture has the "learner only in the box" premise on its own, so a driver has to create it. Two issues this turned up are flagged below.

**1. The function**

- `ensure_strength_learner` is `early_game.py:8719-8768`. It returns early if the party knows Strength (`_party_knows_strength`, `:8710-8716`).
- It raises if HM04 is not in the bag (`:8735-8740`).
- Then `slot = land_hm_learner_slot(hm04)` (`:8744`), which raises "no party member can learn HM04" when `slot` is None (`:8745-8749`). Otherwise it calls `teach_hm_move` (`:8754`) and asserts the result (`:8756-8768`).
- It never reads the box.
- `land_hm_learner_slot` (`:4869-4883`) calls `pick_land_hm_slot` (`:4817-4866`) with `hm_learner_slot` (`:4688-4703`, party only).
  - `pick_land_hm_slot` returns None exactly when `hm_learner_slot` does (`:4839-4840`), so the Rock Smash `_pref` equivalence (`story_mode.py:4940-4951`) holds here too.

**2. Callers, where the bot stands, and the nearest reachable centre**

**Site 1, `:8309`** (inside `travel_to_magma_hideout_door`, heal loop `:8285-8330`):
- It runs right after `heal_in_pokemon_center(center)` for each entry in `MAGMA_ROUTE_HEALS` (`:8078-8081`): Lilycove first, then Mauville.
- That heal walks out of the centre (`higher_level_actions.py:736-748`). So the bot is just outside the door it used: LILYCOVE_CITY around (24,15) or MAUVILLE_CITY around (22,6). The exact exit tile is UNVERIFIED; the volatile `magma_1f_fail.ss1` currently reads MAUVILLE_CITY (22,6).
- **Nearest reachable centre: the one it just left. No travel.**
- A `BotModeError` here is caught (`:8310-8319`) and printed as "SKIPPED". If Lilycove fails, the loop's Mauville stop tries again, which gives a natural second chance.
- It runs only when the chapter starts before the haul (`:8283`; `_MAGMA_PAST_HAUL` is `:8113`). A resume from ROUTE112 or the mountain never reaches it.

**Site 2, `:9010`** (inside `open_magma_hideout_1f`, called from `do_magma_hideout` `:8522-8523`):
- It runs only when the boulders are unpushed (`:9007-9008`).
- The bot is on MAGMA_HIDEOUT_1F at the arrival tile (10,34), a 44-tile pocket (docstring `:8496-8500`; not measured by me).
- **Nearest centre is Lavaridge, and you can walk there but not back.** Static checks on the pinned `magma_door_ki52.ss1`:
  - Jagged Pass (16,19)→(16,20): 1 waypoint. (16,20)→(14,39): 21 waypoints.
  - ROUTE112 (6,46)→LAVARIDGE (9,7): 24 waypoints.
  - Control, uphill: Jagged Pass (14,39)→(16,20) FAILS, which confirms the pass is one-way.
  - LAVARIDGE (9,7)→ROUTE112 (28,28): OK, 66 waypoints. Control: ROUTE112 (28,28)→LAVARIDGE FAILS.
  - The region graph says ROUTE112→LAVARIDGE is 1 hop and "reachable", so it does not see the ledges (matches the design's warning at `:73`).
- Getting back needs the cable car:
  - The very next step in the function, `strength_push`, only walks within the hideout map (`:9014` → `_navigate_riding_out(MAGMA_HIDEOUT_1F, …)`). It cannot take the cable car.
  - A chapter re-run from Lavaridge would walk to **Lilycove** first, because Lavaridge is not in `_MAGMA_PAST_HAUL` (`:8104-8113`, `:8283-8292`).
  - So a Poké Centre trip from site 2 strands or derails the run.
- The Lavaridge staging heal (`:8336-8354`) is also useless as an insertion point: it is measured to be refused from below (`:8338-8342`; `heal_at_lavaridge` docstring `:6435-6440`).

**3. Proposed insertion**

The guard is the same shape as the template at `early_game.py:5155-5163`:

```python
def ensure_strength_learner(heal_centers=()) -> Generator:
    if _party_knows_strength(): return
    hm04 = ...                                    # :8733-8740 unchanged (without HM04 a withdraw buys nothing)
    slot = land_hm_learner_slot(hm04)             # :8744
    if slot is None and heal_centers and not _hm_pcfirst_disarmed():
        boxed = boxed_hm_learner_pids(hm04)       # pure save-block read, no journey (:4715-4719)
        if boxed:
            yield from _withdraw_hm_learner(hm04, boxed, heal_centers)   # arms head PID only (:5073)
            if _party_knows_strength(): return    # a mon that already knows it ranks first (:4736, :4774)
            slot = land_hm_learner_slot(hm04)
    if slot is None: raise BotModeError(... + boxed PIDs from boxed_hm_learner_pids(hm04))  # :8745
```

- At `:8309`: `yield from ensure_strength_learner(heal_centers=(center,))`, where `center` is the loop variable.
- At `:9010`: leave it as `ensure_strength_learner()`. The empty tuple switches box-first off. The raise should name any boxed carrier, which costs nothing because it is a pure read.
- A full party is handled by `withdraw_from_box`'s own make-room step (`pc_trip.py:617-640`, `required=True`).

**Two design points:**
- `boxed_hm_learner_pids` ranks only by "already knows it" and level. It ignores the rule that keeps Strength off a mon that can also learn Waterfall (`#24-hm07funnel`, `:4817-4837`). A boxed Marshtomp (can learn both HM04 and HM07) would be withdrawn and taught. Consider sorting HM07-incapable carriers first before taking the head.
- The "only compatible learner of a still-required HM" protection (design `:100`) is **not** in Increment A. `deposit_protected_pids` protects counters only (`pc_trip.py:57-86`), and `_only_hm_carrier` only protects mons that already know an HM (`team_policy.py:119-128`, `:147-149`). So the only HM04 learner can already be boxed in a real run, which is exactly the premise under test.

**Residual gaps:**
- A run that resumes past the haul gets no box-first for Strength at all. From ROUTE112 (28,28), both Lavaridge and Mauville fail statically. Whether `heal_in_pokemon_center`'s `navigate_to_anywhere` can clear the ROUTE111 (18,101) rock is UNVERIFIED.
- Seafloor Cavern asserts Strength is in the party without box-first (`seafloor_cavern.py:297-300`).
- Victory Road calls `strength_push` without `ensure_strength_learner` (`victory_road.py:2749`, `:2772`, `:3001`, `:3003`).

**4. Fixtures (measured by loading each one)**

In every Ch15-era save, both Mightyena and Sceptile can learn HM04 (Swellow, Skitty, Zigzagoon and Castform cannot), and every box is empty.

| Fixture | Status | Where | Strength state |
|---|---|---|---|
| `post_mtpyre.ss1` | PINNED, md5 matches | MT_PYRE_SUMMIT (23,7), the start of the travel leg (before site 1) | Badges 1-6, HM04 in bag, full party of 6 (Mightyena L42 at 0 HP, Sceptile L42, Swellow, Skitty, Zigzagoon, Castform). Nobody knows Strength; `hm_learner_slot=0` |
| `magma_door.ss1` | VOLATILE; same md5 as the PINNED `magma_door_ki52.ss1` (273d19b3…) | JAGGED_PASS (16,20), entrance open | Sceptile already knows Strength, so site 2 returns at `:8730`. Useless for this test without a write |
| `magma_door_losing.ss1` | PINNED | JAGGED_PASS (16,20) | Mightyena already knows Strength; same problem |
| `magma_1f_fail.ss1` | VOLATILE; md5 now ba23ca04…, manifest says 275d332a… and "stands on 4F", so the manifest line is stale | MAUVILLE_CITY (22,6) — site 1's second heal stop exactly. Copy it and record its md5 before use | Mightyena L44 knows Strength; Sceptile L44 can learn it |
| `jagged_descent.ss1` | — | JAGGED_PASS (14,10) | Wrong era: badges 1-3, no HM04 in bag |

**5. Creating the premise, and the A/B arms**

**Debug write** (the `hmpcfirst` precedent):
- Move every HM04 learner into the box with `debug_write_box_slot`, keeping their real PIDs. Then `debug_write_party` the rest: 4 mons, or padded to 6 with Wingull (cannot learn HM04) for the full-party make-room path.
- ⚠ **Measured trap:** two `debug_write_box_slot` calls in the same frame left **one** mon in the box. The second write overwrote slot 0, and that mon was lost from both party and box. The cause is that `get_pokemon_storage` returns its cached copy within a frame (`pokemon_storage.py:146-147`), and the write helper's "slot occupied" refusal reads that stale copy. Yield a frame between writes or pass `slot_index` explicitly.
- Measured discriminator on the injected states:
  - `post_mtpyre.ss1`: `land_hm_learner_slot=None`, `boxed_hm_learner_pids=['863B0917']` (Sceptile).
  - `magma_1f_fail.ss1`: `boxed_hm_learner_pids=['5C96EA9B']` (Mightyena, which already knows Strength, so no teach).
  - With a full party, `make_room_victim(required=True)` picked Skitty L17 both times, not the Zigzagoon that is the only Surf carrier.

**Faithful alternative:** stand inside the Mauville Poké Center at (10,2) facing Up and call `interact_with_pc([PCAction.deposit_pokemon_to_box(m) …])`, the same call `withdraw_from_box` uses (`pc_trip.py:640-663`).

**Arms** (grade by PID plus species, never by count):
- **Fix on:** the head PID is in the party and gone from the box. On the Sceptile variant, Strength is known by 863B0917 after the teach. On the Mightyena variant, rebind `teach_hm_move` and assert it was **not** called.
- **Fault:** `POKEBOT_HMPCFIRST_FAULT=skipfix`, reusing the existing registered arm read in production (`:5113-5114`). Expect the `:8745` raise, the PID still boxed, and no Poké Centre trip.
- **Vacuity control:** only Sceptile boxed, Mightyena left in the party. Measured `hm_learner_slot=0`, so box-first must not fire; rebind `_withdraw_hm_learner` to count zero calls. Un-injected fixtures give identical arms.
- **Site-2 arm:** `ensure_strength_learner()` with no centres on the injected premise must raise with no trip, and the message must name the boxed PID.

**6. Closest existing driver**

`--driver magmadoor` is not relevant. It is a pre-Emblem door-reachability probe (`story_harness.py:2346-2410`) and never calls `ensure_strength_learner`.

- **`hmpcfirst`** (`story_harness.py:21158-21370`) is the template for the mechanics: premise assertion, injection, identity grading, the `skipfix` arm, and the bounded errand.
- **`magmatravel`** (`:2413-2557`, from `post_mtpyre.ss1`) is the only driver that reaches site 1. It needs `MAGMA_TRAVEL_CAPTURE=0`, or it overwrites `magma_door.ss1` (`:2551-2554`).
- **`magmahideout`** (`:4255-4369`) reaches site 2. It overwrites `magma_1f_fail.ss1` on failure (`:4358-4361`).

**Recommendation:** a new narrow driver built on `hmpcfirst` that calls `ensure_strength_learner(heal_centers=(PokemonCenter.MauvilleCity,))` from a pinned copy of `magma_1f_fail.ss1`. Then one `magmatravel` run on an injected `post_mtpyre.ss1` as the end-to-end check.

Scratch probes (they wrote only the `repro-ml` profile's own shutdown state):
- <session scratchpad>/probe_strength_fixtures.py
- <session scratchpad>/probe_strength_premise.py

## SITE: waterfall
### WATERFALL site: box-first recon (Increment B)

**Bottom line:** the Waterfall site can't reuse the Surf/Dive template as it stands. In the measured failure (a four-HM party member that can learn Waterfall), `hm_learner_slot` returns that saturated member, so the template's box-first gate never fires. The insertion has to live inside `ensure_waterfall_learner` and use that function's own "compatible and has a spendable slot" pick.

#### 1. What the function does, and where it is called

**The function** is `sandbox-pokebot/modules/story/victory_road.py:962-1078`. In order:
- It returns early if someone already knows Waterfall (`:992`).
- It raises if HM07 is not in the bag (`:996-1002`).
- It picks the highest-level party member that is Waterfall-compatible **and** has a non-HM slot to spend (`:1018-1031`). An unreadable move counts as not spendable.
- If nothing qualifies (`best is None`, `:1033`), it raises a named refusal (`:1051-1058`). That message always says "every compatible party member has four HM moves". It is wrong when *no* party member is compatible, which is exactly the `fortree_gym_wedge` shape.
- Otherwise it calls `teach_hm_move` (`:1063`) and checks the world afterwards (`:1068`).
- It never looks at the PC box.

**The only caller** is Segment 22b: `story_mode.py:5661` (import), `:5663` (call), `:5664-5665` (`_guard`). Line `:5654` is inside the comment block above it. No harness driver calls this function. `ch23teach` calls `teach_hm_move` directly (`story_harness.py:12936-12958`), so the production function has never been driven.

#### 2. Where the bot is, and which Poké Center to use

- Segment 22b runs right after `ch22_chapter_done()`: badge 8 held and off both gym floors (`sootopolis_gym.py:792-809`). The chapter ends with `leave_gym_to_city` (`:921`), so the bot is on SOOTOPOLIS_CITY. `post_badge8.ss1` sits at (31,33).
- **The only usable centre is Sootopolis.**
  - The planner refuses both alternatives from (31,33): Mossdeep and Ever Grande are "not on connected maps (warps don't count)" (measured). Leaving the crater needs Dive and is hand-sequenced (`victory_road.py:125-128`, `leave_the_crater`).
  - The Ever Grande centre door (27,48) is above the waterfall (`victory_road.py:129-131`, `:148`), so reaching it needs Waterfall. That is circular.
  - Whether `navigate_to_anywhere` could ever leave the crater by Dive: UNVERIFIED.
- **Measured on Sootopolis:**
  - 23 steps from `post_hm07`, 24 from `post_badge8`, 38 from `post_sootopolis_arrival`.
  - `SOOTOPOLIS_CITY_POKEMON_CENTER_1F` has its PC at (10,1) by `tile_type=="PC"`. The stand tile (10,2) is walkable, 8 steps from (7,7). So `PC_STAND_TILE` is valid here, as it is for Fortree, Ever Grande and Mossdeep 1F.
- It is also the centre the chapter itself uses: §Ch23 leg 2 heals there (`victory_road.py:1197`, `:1168`). `heal_in_pokemon_center` ends outside the door (`higher_level_actions.py:735-747`), which is on `_RESUMABLE_MAPS` (`victory_road.py:111`), so the §Ch23 preflight still passes.
- Whether a PC withdraw has ever been driven at Sootopolis: UNVERIFIED. `hmpcfirst` proved it at Fortree.

#### 3. Why the template doesn't transfer (computed live, `post_badge8` with the injection below)

- `wf_pick = None`, `hm_learner_slot(HM07) = 3` (the saturated Wailmer), `boxed = ['253062D9']`.
- **The gate:** the box-first gate in `ensure_hm_learner_making_room` is `hm_learner_slot(item) is None` (`early_game.py:5155`). It is False here, so the function goes straight to `ensure_hm_learner`, which returns slot 3. Box-first never fires.
- **The return value:** `_withdraw_hm_learner` computes its return and its "withdrew X (pid=…)" line from `hm_learner_slot(item)` (`early_game.py:5090-5096`). After a real withdraw of a L30 Marill it would still name Wailmer L40, the higher level, and print a false identity line.
- This is the measured shape: 5 of the 6 recorded Rain-badge parties had a Swampert holding [Strength, Rock Smash, Surf, Dive] (`07-CHANGELOG.md:24218-24226`).

#### 4. Proposed insertion (inside `ensure_waterfall_learner`, between `:1031` and `:1033`)

- Move the pick loop (`:1025-1031`) into a local `_pick()` and call it before and after the withdraw.
- If `_pick()` is None and a new production-read skip arm is not set (e.g. `POKEBOT_WFBOXFIRST_FAULT=skipfix`, same pattern as `_hm_pcfirst_disarmed` at `early_game.py:5113`, registered in `29-DISABLED-FEATURES-REGISTRY.md`):
  1. Take `boxed_hm_learner_pids(hm07)` (`early_game.py:4707`). Optionally filter it to box mons with a spendable slot, because its ranking (`:4774`) doesn't check that.
  2. Take only the head PID and call `_withdraw_hm_learner(hm07, [pid], (PokemonCenter.SootopolisCity,))`.
  3. **Ignore its return value.** Better: give it a `pick=` parameter so the Waterfall site can pass `_pick` and its log line names the right mon.
  4. Re-check `field_move_carriers()["Waterfall"]` first, since the withdrawn mon may already know it; if so, return.
  5. Otherwise `best = _pick()`, and assert the pick's PID equals the withdrawn PID.
- If still None, raise the existing refusal. Reword it to separate "no compatible member" from "all saturated", and to say what the box check found.
- Make-room needs no change. `withdraw_from_box` already calls `make_room_victim(..., required=True, protected=deposit_protected_pids())` (`pc_trip.py:617-640`), and sole HM carriers are excluded (`pc_trip.py:120`), so Wailmer's Dive is safe.
- ⚠ **Cross-site risk:** in a party with no dead weight, the required fallback can box the *only Fly learner*. §Ch24's `ensure_fly_learner` then fails unless Fly box-first ships too. Increment A's commit already records this gap. On `post_badge8` the victim is Zigzagoon (dead weight), so it doesn't bite there.

#### 5. Fixture status (measured with a scratch probe; profile `repro-ml`, no files written)

| fixture | where / badges | HM07 in bag | Waterfall learner in party | box |
|---|---|---|---|---|
| `post_badge8` | SOOTOPOLIS (31,33), 1-8 | yes | Wailmer FA51ECF3 L40 [Dive, Surf, Water Gun, Rollout], spendable, **0/160 HP** | 0 |
| `post_hm07` | SOOTOPOLIS (31,34), 1-7 | yes | same Wailmer, spendable | 0 |
| `post_sootopolis_arrival` | SOOTOPOLIS (29,53), 1-7 | **no** | Wailmer, spendable | 0 |
| `fortree_gym_wedge` | FORTREE_CITY_GYM (4,19), 1-5 | **no** | none compatible | 0 |
| `post_waterfall` / `post_depart_sootopolis` | Sootopolis / ROUTE126 | yes | Wailmer already knows Waterfall | 0 |

- On every Sootopolis fixture, Wailmer is the only Waterfall-compatible member. The make-room victim (`required=True`) is Zigzagoon 33CB74C3, L19, dead weight.
- Swellow 0B30A747 is the only Fly-compatible member everywhere.
- `fortree_gym_wedge` (design D5's alternative) is a poor fit:
  - `:998` raises "HM07 is not in the bag" before any box code runs;
  - Sootopolis is unreachable from there;
  - it tests the no-compatible shape, which the generic gate already covers, not the saturated shape that matters here.

#### 6. How a driver creates "learner only in the box" (verified in memory on `post_badge8`)

1. Snapshot box and party PIDs. The box is empty, which the driver should assert.
2. **Saturated shape:** rebuild Wailmer as `debug_create_pokemon(species=Wailmer, level=40, original_pokemon=wailmer, moves=[Dive, Surf, Cut, Flash])` and write it with `debug_write_party` (the other members copied as `SimpleNamespace(data=...)`, as `ch20dive` does at `story_harness.py:6624-6650`).
   - Measured: the PID stays FA51ECF3, `wf_pick` goes 3 → None, `hm_learner_slot` stays 3, and Surf and Dive carriers survive (Surf is also on Zigzagoon).
   - Cut and Flash are HMs nobody else holds, so no other member's sole-carrier status changes.
   - Using the literal measured moveset [Strength, Rock Smash, Surf, Dive] would give the same result by the predicate at `:1018-1031`, but that was not run live.
3. **Box it:** `debug_write_box_slot(debug_create_pokemon(Marill, 30))`. Measured: `can_learn HM07 = True`, and `boxed_hm_learner_pids` returns the new PID.
4. Drive production `ensure_waterfall_learner()`.

**Arms:**
- **FIX:**
  - Marill's PID is in the party, gone from the box, and knows Waterfall.
  - Wailmer FA51ECF3 is still in the party with Dive and Surf.
  - The deposited PID is Zigzagoon 33CB74C3 (pre-registered from `make_room_victim`).
  - All three field-move carriers are non-None.
  - The run ends on SOOTOPOLIS_CITY with an exit it can path to.
  - Party 6→6 and box 1→1 are printed, not graded.
- **skipfix:** the named refusal at `:1051`, no Poké Center trip (position unchanged), Marill still boxed, party PIDs unchanged.
- **nobox** (skip step 3): `boxed = []`, no trip, named refusal.
- **Ordinary** (skip steps 2 and 3, i.e. plain `post_badge8`): Wailmer is taught directly with no PC visit. Compare against `evidence/2026-09-03-ch23teach-WATERFALL-PASS.txt`, where Rollout was forgotten. This is the rule-9 test on the ordinary path.
- **Ordinary + boxed Marill** (skip step 2 only): the party Wailmer is taught and Marill stays boxed. This proves the party is tried before the box.
- **noegress:** a fault in the end-position check, as in `hmpcfirst`, so that check is seen to fail.

The discriminator is computed: the FIX and skipfix arms start from `wf_pick=None` / `boxed=[pid]`, so the outcomes must differ (a withdraw versus a raise).

#### 7. Closest existing drivers

- **`hmpcfirst`** (`story_harness.py:21158`) is closest in mechanism: it already uses HM07, injects a box Wailmer, grades by PID, and has the nobox / skipfix / noegress arms plus the end-position check. It has been driven, with evidence in `evidence/2026-09-25-hmpcfirst-*.txt`. The design note's "never RUN" repeats a stale driver docstring (`:21159`).
- **`ch23teach`** (`:12854`) is closest by site: same fixture, same position, and it grades that Dive and Surf survive.
- A new `wfboxfirst` driver would be `ch23teach`'s fixture and safety checks combined with `hmpcfirst`'s injection, grading and arms, calling the production function.

**Still UNVERIFIED:** how often an organic 8-badge run has a Waterfall-capable mon in the box; a live PC withdraw at Sootopolis; the Fly-learner deposit risk in parties with no dead weight.

Scratch probes are in `<session scratchpad>/`: `probe_wf_fixtures.py`, `probe_wf_funnel.py`, `probe_soot_pc.py`. Each run left an autosave in `sandbox-pokebot/profiles/repro-ml/states/` (untracked by git). No tracked files changed; the modified `party_accounting_ledger.jsonl` dates from 09:42, before these runs.

## SITE: fly
**FLY site: box-first recon for RULING 20 Phase 1, increment B (read-only)**

The Fly withdraw cannot reuse the existing HM machinery. From where `ensure_fly_learner` runs, the only PC the bot can walk to is the League 1F lobby PC. The existing path can't reach that PC, and `pc_trip`'s withdraw would stand on the wrong tile there. The fix is a small lobby-PC trip plus a stand tile chosen per map. The "learner only in the box" state is not in any fixture, but it can be built in memory from `post_moveset.ss1`; I did that in a scratch run and all the checks below come from it.

Scratch scripts (nothing in the repo was edited; `party_accounting_ledger.jsonl` was already modified at 09:42, before my runs at 10:03):
- `<session scratchpad>/probe_fly_site.py`
- `<session scratchpad>/probe_fly_premise.py`

### 1. Where the bot is when it is called
- **The call site** is `story_mode.py:5731`, not `:5722` as the design note says. Line 5722 is the "game is cleared" print.
  - Order: `ch24_chapter_done()` (`:5721`), then `self.mark_ch24_owns_run()` (`:5729`), then `ensure_fly_learner` (`:5731`), then the report check (`:5732-5735`), then `train_for_league` (`:5737`).
  - It sits behind `_guard("Victory Road (Ch23)", _ch23_settled)` (`:5693`).
- **First entry: EVER_GRANDE_CITY, the north plateau, normally at (18,6).**
  - `ch23_chapter_done` requires being on Ever Grande, outside Victory Road, with the full basket (`victory_road.py:3719-3726`).
  - §Ch23's last leg exits the lobby onto Ever Grande and asserts it (`victory_road.py:3596-3608`).
  - `post_moveset.ss1` (captured after that shop) reads EVER_GRANDE_CITY (18,6), measured.
- **Re-entry:** usually Fly is already known and the function returns at `pokemon_league.py:2226-2231`.
  - After a run with no Fly, training can end on the SOUTH half at (27,49) (`pokemon_league.py:2316-2318`).
  - A whiteout after the lobby respawns at Ever Grande (18,6): the lobby's OnTransition runs `setrespawn HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE`, and that heal location is Ever Grande (18,6) in the decomp's `heal_locations.json:118-121`. The JSON has no `respawn_map` entries; the claim that Emerald respawns outdoors rests on project measurements (`victory_road.py:3675-3678`). Partly UNVERIFIED.

### 2. Which PC it can use
- **Only the League 1F lobby PC.** From the plateau, the Ever Grande Poké Center at (27,48) is unreachable on foot, measured (`victory_road.py:355-363`; `FIXTURES.md5:69`). With no Fly knower, nothing else is reachable either.
- **`_withdraw_hm_learner` and `ensure_hm_learner_making_room` cannot be reused here:**
  - They go through `heal_in_pokemon_center(centre)` (`early_game.py:5077`, `:5186`).
  - `PokemonCenter` has no League member. `EvergrandeCity` is the south centre (`map_data.py:1537`), so the walk raises `HealWalkFailedError` "BLOCKED" (`higher_level_actions.py:586`). That error is caught per centre, and the function returns None.
  - Even if the walk worked, `heal_in_pokemon_center` hard-codes the standard interior: nurse at (7,4) (`:610`), exit at (7,7)/(7,8) (`:741-748`).
  - The lobby is different: the nurse is at (3,4) across a counter, and the exit is an arrow warp at (9,11) (`victory_road.py:386-398`).
  - Their fallback is a hunt (`early_game.py:5166`), and nothing on the plateau can be hunted.
  - `hm_learner_slot` (`:5090`) ignores saturated move slots. `_fly_teach_plan` is the right check (`pokemon_league.py:2140-2145`).

### 3. The League 1F PC tile (measured from the ROM's map data)
- The only PC tile on EVER_GRANDE_CITY_POKEMON_LEAGUE_1F is **(6,1)**. Its neighbours:
  - **(6,2): Normal tile, collision 0, elevation 3 → stand here, face Up.**
  - (6,0), (5,1), (7,1): collision 1.
- This is the same tile-type field `interact_with_pc` checks before it will open the PC (`pc_interaction.py:731-733`).
- **Decomp (`gh api` on `EverGrandeCity_PokemonLeague_1F`):**
  - `bg_events` is empty, so the PC is a metatile behaviour, not an event.
  - OnTransition places the guards at (9,2)/(10,2) while `FLAG_ENTERED_ELITE_FOUR` is unset.
  - Warps: (9,1)/(10,1) go to HALL5; (9,11)/(10,11) go to Ever Grande.
  - UNVERIFIED by me: `map.bin` itself (the flyer recon cites two decodes giving (6,1)).
- **Paths, with live objects from `post_league_lobby.ss1`:**
  - (3,4) → (6,2): OK, 5 waypoints.
  - (9,11) → (6,2): OK, 12 waypoints via (9,3), (8,3), (7,3), (6,3). It passes under the guard at (9,2), which is harmless with no A press (`victory_road.py:400-409`).
  - (3,4) or (9,11) → (10,2): **NO PATH**, because the guard object stands there.

### 4. `pc_trip` cannot take a stand tile per map
- `PC_STAND_TILE=(10,2)` and `PC_FACING="Up"` are module constants (`pc_trip.py:35-37`). They are hard-coded at all three navigate sites: `:279-281`, `:401-403` and `withdraw_from_box` `:645-647`. `withdraw_from_box(pids)` has no stand parameter.
- In the lobby, `navigate_to((10,2))` fails (guard). The blanket `except` then returns `(False, "error", …)` (`:709-723`), so nothing is withdrawn and the failure is only a console line.
- (10,2) is also directly under the (10,1) step-on door to HALL5, a hazard once the guards move.
- **Proposed fix:** a map-keyed lookup in `pc_trip`, e.g. `PC_STAND_BY_MAP = {LEAGUE_1F.value: ((6,2), "Up")}` with a `pc_stand_for(current_map)` that defaults to the constants.
  - Use it at all three sites.
  - Add a pure pre-check that the faced tile's type is `PC` before walking.
  - This touches every heal withdraw, so it needs a regression check on the ordinary case: the `hmpcfirst` default arm from `fortree_gym_wedge.ss1` should behave exactly as it does today (CLAUDE.md rule 9).

### 5. Box-first insertion
Insert in `ensure_fly_learner` at `pokemon_league.py:2253-2260`: after the HM02 and banned-move checks, and before `no_learner` is reported. The NOFLYTEACH arm at `:2235` still skips everything, and the rule of never raising for a missing learner is kept.

```python
plan = _fly_teach_plan(get_party(), hm02, banned)
if plan is None and os.environ.get("POKEBOT_R20_FAULT_NOFLYBOX") != "1":   # new arm, register in 29
    boxed = boxed_hm_learner_pids(hm02)            # pure save read; knows-Fly first, then level (early_game.py:4773)
    if boxed:
        landed, code, detail = yield from _withdraw_at_league_pc(boxed[0], report)   # ONE PID, never the list
        report["fly_box"] = code
        if landed:
            knower = get_party().first_pokemon_with_move("Fly")   # a boxed KNOWER needs no teach -> "already"
            if knower is not None: ...report fly_teach="already", fly_source="box"; return
            plan = _fly_teach_plan(get_party(), hm02, banned)      # assert planned learner PID == boxed[0]
```

**New `_withdraw_at_league_pc(pid)`**, following the door handling in `heal_at_league`:
1. If on Ever Grande, `_walk_through_warp("Up", EG.value)` (`victory_road.py:3272`) and assert `LEAGUE_1F`. If already in the lobby, skip this.
2. Call `withdraw_from_box([pid])`, which now stands on (6,2) facing Up and handles room itself with `required=True`.
3. Leave with `_navigate_riding_out(LEAGUE_1F, LEAGUE_EXIT_TILE)` and `_walk_through_warp("Down", …)` (`:3332-3334`), and assert Ever Grande.

Leaving the lobby is required: Fly is illegal on an Indoor map (`pokemon_league.py:1208`, `:1211-1225`), so a bot left in the lobby would have `train_for_league`'s Fly ladder refused.

Existing pieces this relies on: the caller treats `already`/`taught` as success (`story_mode.py:5732`); the `ch24handoff` driver's `fly_known` check expects the same. Gate `probe_ch24_flyteach.py` F4 (`:212-217`) must stay green.

### 6. RULING 21 obligations — these must ship with box-first
- **The make-room victim** in `withdraw_from_box` (`pc_trip.py:617-640`) is measured as **Zigzagoon 33CB74C3** (dead weight, L19, 34 below the best) on all three fixtures and in both injected arms.
- RULING 21 (`06-DECISIONS-LOG.md:7446`) allows one fighter in the PC while the Fly carrier trains. RULING 12 (`06:6833`) forbids boxing Zigzagoon or Castform to make the floor easier.
- So the swap is only legal if these are built with it:
  - Record FIGHTERS (PID and species) at the latch, before the teach.
  - Exclude non-fighters from the trainee list. Today `ch24_trainees_below_floor` counts every non-egg member (`pokemon_league.py:1622-1656`), so a withdrawn carrier would be ground to L65.
  - Before R1, swap the carrier back out for the boxed fighter at the lobby PC and assert party PIDs == FIGHTERS. R1 today counts only levels (`:1665-1692`), and RULING 15 needs only 4 of 6 at the floor.
- **One question the rulings do not settle: which fighter to box.**
  - Dead weight picks Zigzagoon, which trains first and would then miss training.
  - The flyer recon's O1 boxes the fighter trained last and swaps at an anchor PC (`ai-research-notes/2026-09-26-ch24-flyer-acquisition-RECON.md:42`).
  - No code for RULING 21 exists yet (grep found none).

### 7. The three fixtures (measured)
All three have HM02 ×1, BADGE06, LANDMARK_POKEMON_LEAGUE, ENTERED_ELITE_FOUR=False, **an empty box**, and a party of 6 in which only Swellow `0B30A747` can learn Fly. So **none of them meets the premise as captured.**

| Fixture | Position | Swellow | `_fly_teach_plan` |
|---|---|---|---|
| `post_moveset.ss1` | Ever Grande (18,6), plateau — the production first-entry position | L48, Fly not taught | (2,3) |
| `post_league_lobby.ss1` | LEAGUE_1F (3,4), guards live at (9,2)/(10,2) | L75, already knows Fly | (3,3); function returns F-KNOWN |
| `post_ch24ready.ss1` | Ever Grande (27,49), south half — the off-plateau case, where the standard centre is the right one | L48, already knows Fly | (2,3) |

### 8. Building "learner only in the box", and the arms
**Construction** (proven in memory on `post_moveset.ss1`): `debug_write_party(party minus Swellow)`, then `debug_write_box_slot(swellow)`, which lands at (0,0). Yield frames before reading back. Premise results:
- `_fly_teach_plan` = None.
- `boxed_hm_learner_pids` = [0B30A747].
- After the withdraw, the plan picks Swellow 0B30A747 at (5,3).

**Arms:**
- **ROOM (party 5):** no deposit. Grade: Swellow in the party AND gone from the box, by (PID, species). The lobby was visited; `F-TAUGHT` with `fly_learner` = Swellow#0B30A747. Ends on Ever Grande with Fly legal, plus a real `calculate_path` continue check.
- **FULL (party 6):** add a Machoke L50 filler (cannot learn Fly). Pre-registered: victim is Zigzagoon 33CB74C3; Swellow in; the other 5 PIDs are unchanged.
- **Skip-the-fix (`POKEBOT_R20_FAULT_NOFLYBOX=1`), same injection:** expect `fly_teach=no_learner`, Swellow still boxed, LEAGUE_1F never entered.
- **Wrong tile (force (10,2) in the lobby):** expect NO PATH, verdict `error`, `no_learner`. This proves the per-map stand tile is doing the work.
- **Skip the exit:** expect the Fly-legal check to FAIL.
- **Ordinary case:** untouched `post_moveset.ss1`. Taught from the party, the box is never consulted, and frames must match HEAD exactly (determinism).
- **Knower in the box:** `post_league_lobby.ss1` with Swellow (knows Fly) boxed; exercises the no-teach branch and the already-in-lobby entry.
- **RULING 21 restore:** its own arms — skip the swap-back, where the identity check must FAIL while the level check passes; and a carrier-as-trainee arm.

### 9. UNVERIFIED
- `map.bin` for the PC at (6,1): I used ROM map data only.
- That `navigate_to`'s failure at (10,2) matches `calculate_path`'s: I measured only the planner.
- Emerald's whiteout respawn semantics (only partly checked in the decomp).
- That the Ever Grande south Poké Center 1F uses (10,1)/(10,2).
- Whether a real organic §Ch24-entry save with a boxed flyer exists: none is pinned.

## SITE: counter
**Box-first counter site (RULING 20 Phase 1, Increment B): recon report**

**Bottom line.** Put the box check inside `_counter_ladder`, right after the once-per-boss "started" mark and before both the planner and the ball check. It registers the PID the same way a hunted counter is registered, and the story's own gym-segment heal then collects it. Two things block a naive version, and both were measured:
- `box_counter_pid` is too lenient, and it returns the first match in box order, not the best one.
- The heal's withdraw still uses the full, never-cleared `_hunted_counter_pids`, so an expired counter sitting earlier in the box gets withdrawn instead of the new one.

All three fixtures work with an injected counter, but `fortree_gym_wedge.ss1` can only be driven by calling `_counter_ladder` directly.

**1. Code read** (paths are under `sandbox-pokebot/`)
- **`_counter_ladder`, `story_mode.py:2736-2899`**
  - The once-per-boss bound is at `:2762-2772`.
  - Then the planner runs (`:2775`), then `resource_blocker` (`:2785`), then the shortlist (`:2801`), then `hunt` (`:2817`).
  - Registration is at `:2864-2876`: it adds the PID to `_hunted_counter_pids` and overwrites `_hunted_counter_badges[pid] = badge_count()`.
  - A catch that went to the box skips training (`:2881-2890`).
  - Only caller: `:3440`. It is reached only on a hopeless verdict (`:2604-2721`: at least 6 losses, a plateau, and no party move scoring 75 or more).
- **`counter_hunt.box_counter_pid`, `counter_hunt.py:235-326`**
  - It accepts a box mon whose own type matches, with no move check (`:296`).
  - It also accepts any damaging move of a needed type, whatever its power (`:318-323`).
  - It returns the first match in box order.
  - Its behaviour is pinned to `party_counter_slot` by `repro_box_counter_move_test.py` (`:263-266`). **Do not change it.**
- **`hunt`, `counter_hunt.py:426-575`.**
- **Heal withdraw, `higher_level_actions.py:677-724`**
  - The source is `withdraw_pid_source(_wanted_hm_learner_pids, _hunted_counter_pids)` (`:690-693`, `:53-76`). It passes the raw set.
  - `withdraw_precedence` (`:79-126`) defers the withdraw only when `_needs_party_slot` is set.
  - `withdraw_from_box` → `find_in_box` (`pc_trip.py:491-507`) takes the first box-order match among every registered PID.
  - The make-room step uses `make_room_victim(..., exclude_pids=pids, required=True, protected=deposit_protected_pids())` (`pc_trip.py:617-640`).
  - Increment A's badge expiry feeds only the deposit side (`pc_trip.py:57-86`).
- **Which heal follows each boss's prep:**

  | Boss | Lead pick | Heal | Heal function |
  |---|---|---|---|
  | Wattson | `:4881` | `:4882` | bare `heal_in_pokemon_center` |
  | Norman | `:5131` | `:5134` | `heal_at_petalburg`, which calls `heal_in_pokemon_center(PetalburgCity)` (`early_game.py:6974-7011`) |
  | Winona | `:5305` | `:5306` | bare `heal_in_pokemon_center` |
  | Tate & Liza | — | `:5461` | bare `heal_in_pokemon_center` |
  | Juan | — | inside `sootopolis_gym.py:872` | UNVERIFIED whether it goes through the PC piggyback |

**2. Where and how** (a proposal, not built)
Insert it after `self._counter_hunts[key] = "started"` (`story_mode.py:2772`), before `find_counter_candidates` (`:2775`):
```python
if not _boxfirst_counter_disarmed():   # new arm POKEBOT_R20_FAULT_NOBOXCOUNTER=1, read inside the function; register in 29
    party_pids = frozenset(m.personality_value for m in get_party() if m is not None)
    pick = counter_hunt.box_counter_choice(needed, exclude_pids=party_pids,
                                           taught=getattr(self, "_gym_tm_taught_moves", None) or {})
    if pick is not None:                       # (pid, species, level, why); unreadable box -> None -> hunt as today
        self._register_counter(pid, where="PC box (box-first)")   # extract :2864-2876 so both paths share it
        self._counter_hunts[key] = f"box-first {species} L{level} pid={pid:08X} ({why})"
        return True                            # _prepare_for_fight returns (:3474-3477); the segment heal withdraws it
```
- **Why before `resource_blocker`:** it refuses when there is one ball or none (`counter_hunt.py:407-409`), and a withdraw needs no ball.
- **Why before the planner:** a planner failure (`:2778-2781`) should not block the box check.
- **Why after the "started" mark:** the once-per-boss bound (`:2741-2752`) then covers box-first too, so the termination argument is unchanged.
- **Registration must overwrite** `_hunted_counter_badges[pid]`, never `setdefault`. That way a previously expired counter becomes owed to the current boss and `deposit_protected_pids` protects it again. The hunt path already overwrites (`:2869`).
- **Add a new function `box_counter_choice`; leave `box_counter_pid` alone.**
  - Read the box with `pc_trip.box_views()`. It reads the save blocks, so it works from anywhere (`early_game.py:4715-4719`).
  - Accept a mon if either:
    - its own type is a needed type, which is the planner's rule (`counter_plan.py:156`); or
    - it knows a damaging move of a needed type with base power × 2.0 × STAB ≥ `CREDIBLE_ANSWER_POWER` (75), which is the planner's move rule (`counter_plan.py:185-199`). Ignore gym-TM-taught (PID, move) pairs, following RULING 19 (`story_mode.py:2688-2697`).
  - Rank by: has a credible move, then that score, then type coverage, then level.
  - Return one PID only, following the one-PID rule (`early_game.py:4724-4734`).
- **Why own-type must stay accepted (measured):**
  - Magnitude and Low Kick have base power 1 in the move data.
  - So every realistic Ground counter for Wattson scores 0-3: Geodude L15, Numel L20, Barboach L20, Nincada L15.
  - The planner's own Wattson target is Numel at FIERY_PATH, which is also type-only.
- **Why the lenient move test must go (measured):** today a box mon whose only answer is Rock Smash (20 power, scores 40) or Mud-Slap (20) would qualify, and it would use up the ladder's one action for that boss.

**3. What to exclude**
- **All current party PIDs.** This covers counters already in the party, and it covers KI-78 twins. The Norman fixture has Shedinja and Ninjask both at PID `42207D6F` in the party (measured). Registering a twin's PID would also protect the party twin and make the lead picker promote it.
- **Eggs** (already skipped at `counter_hunt.py:291`).
- **Gym-TM-taught moves** as evidence of an answer (see §2).
- **`_wanted_hm_learner_pids`:** no exclusion needed. It is always empty outside `_withdraw_hm_learner` (`early_game.py:5072-5086`).
- **Deposit-side protection** is already handled by `make_room_victim`: owed counters, the PIDs being withdrawn, the only carrier of an HM, and the last living battler. Gym-TM recipients are deliberately not protected (`pc_trip.py:62-64`).

**4. Hazards (read or measured)**
- **H1 — the wrong counter can be withdrawn, and it still reads as success.**
  - The heal passes the full never-cleared set, and `find_in_box` takes the first box-order match.
  - Since Increment A, expired counters can be boxed by make-room. One sitting earlier in the box gets withdrawn instead of the box-first pick.
  - The verdict still reads `code=landed` (`higher_level_actions.py:226`).
  - This is the unbuilt withdraw half of design item 2. It is a precondition for box-first working correctly.
  - Fix: make the withdraw source the owed counters only. Factor `owed_counter_pids(mode)` out of `deposit_protected_pids` without its fault arms (otherwise `NOPROTECT` would also turn off withdraws) and use it at `:692`.
- **H2 — no lead on the first attempt.** The lead is picked before the segment heal (see the table in §1), so the withdrawn counter does not lead the attempt right after registration. It is the same for today's box-catch path.
- **H3 — the counter arrives untrained.**
  - Winona has no `grass` key, so `train_counter` declines anyway (`counter_hunt.py:689-694`).
  - Wattson and Norman lose the training rung. Once a credible counter is in the party the verdict becomes "not hopeless", so nothing trains it until the 12-loss hard plateau (`:2647-2651`). `counter_hunt.py:25-29` warns about exactly this.
  - Options: accept it (same as today's box-catch path), add a level floor, or train each registered PID once at the start of `_prepare_for_fight` after it lands. The last option also closes the existing gap at `:2881-2890`. **This needs your decision.**
- **H4 — first box-order match (measured).** After injecting Slugma, then Geodude, then Snorunt (Icy Wind, score 330), then Bagon (Dragon type, score 0), `box_counter_pid` still returned Slugma.

**5. Fixtures** (measured with a scratch probe on this branch; no box injection was saved)

| | `fortree_gym_wedge.ss1` | `mauville_prewattson.ss1` | `prenorman_fodder_grind.ss1` |
|---|---|---|---|
| Boss | Winona | Wattson | Norman |
| Needed types | Rock / Ice / Dragon | Ground | Fighting |
| Where it loads | Inside FORTREE_CITY_GYM (4,19) | MAUVILLE_CITY (19,15) | ROUTE102 (9,2), **inside a wild battle**: call `normalize_to_overworld` first (`probe_counter_tiles.py:211-219`) |
| Badges | 1-5 | 1-2 | 1-4 |
| Party | 6/6: Mightyena 38, Sceptile 39, Swellow 33, Skitty 17, Zigzagoon 3, Castform 25 | 4: Dustox 20 (fainted), Marshtomp 20 (Ground type, no Ground move), Taillow 18, Poochyena 16 | 5: Combusken 35 (Rock Smash scores 60), Shedinja 25 + Ninjask 27 (both `42207D6F`), Whismur 18, Mightyena 30 |
| Credible answer in party | Castform, Powder Snow scores 160, so **not hopeless** below 12 losses | none | none |
| Box / balls | empty / 17 | empty / 19 | empty / 31 |
| Withdraw make-room | needed; victim would be Skitty (dead weight) | not needed | not needed |
| Injection | Slugma L15 (Rock Throw, 100) → returned | Geodude L15 (type only) → returned | Machop L15 (Karate Chop, 150) → returned |
| Hunt shortlist | Slugma @ FIERY_PATH (18,19) | Numel @ FIERY_PATH | Machop @ FIERY_PATH |
| Heal to use | bare Fortree | bare Mauville | `heal_at_petalburg` |

Injection uses `debug_create_pokemon` + `debug_write_box_slot`, as in boxcounter's `_stage1` (`story_harness.py:5640-5687`). Reuse its read-back and `not_in_party` checks.

**6. A/B plan for D3**
Drive on `fortree_gym_wedge.ss1`, calling `_counter_ladder` directly with Winona's config, `losses=8`, and needed = {Rock, Ice, Dragon} derived as in `_derive_needed`.
- **Why a direct call:** a `_prepare_for_fight` drive is vacuous here. Castform makes the verdict "not hopeless" (as Ki80Ladder's docstring notes at `story_harness.py:6027-6029`), and the save is inside the gym, where the Winona segment skips prep (`:5303`).
- **Observers:**
  - W1: records entry to `counter_plan.find_counter_candidates`, calling the real function.
  - W2: a generator stand-in for `counter_hunt.hunt` that records entry and returns None without travelling.
  - W3: state checks on the registry, the badge map and `_counter_hunts`.
  - W4: record each deposit and withdraw by PID, using r20makeroom's recorder pattern.
- **Harness trap:** registration lands on the ladder's `self`, but the heal reads `context.bot_mode_instance`. If the driver creates its own `StoryMode()` (the secondwind pattern), it must copy production's registration onto the driver, as boxcounter2 does at `:5851`. Otherwise the heal leg fails for a harness reason.

| Arm | Setup | Expected |
|---|---|---|
| A1 | Fix on, Slugma injected | W1 and W2 not entered; ladder returns True; registry = {Slugma}; its badge count = 5; `_counter_hunts` says "box-first". After `heal_in_pokemon_center(FortreeCity)`: Slugma (PID + species) in the party and gone from the box; the one deposit is Skitty's PID. |
| A2 | `POKEBOT_R20_FAULT_NOBOXCOUNTER=1`, Slugma injected | W1 entered; W2 entered for Slugma @ FIERY_PATH; ladder returns False ("none found"); registry empty; the heal's withdraw is skipped and Slugma stays boxed. |
| A3 | Fix on, nothing injected (control) | W1 entered. Shows A1's skip came from the injected box mon, not from Castform in the party. |
| A4 | A1 plus an expired Machop registered with badge count 4, placed earlier in the box | Tests H1. With today's source, the heal withdraws Machop (the wrong mon); with an owed-only source, it withdraws Slugma. |

- **Why the arms differ (computed on this save):**
  - The box check returns None before injection and the Slugma PID after, so A1 and A3 differ.
  - There are 17 balls, so `resource_blocker` does not stop A2 before the hunt.
  - The shortlist is not empty, so A2's W2 actually fires.
- **Pure gates:**
  - A new test for `box_counter_choice`: Rock Smash-, Mud-Slap- and Rollout-only mons rejected; own-type accepted; ranking beats box order; a party-PID twin excluded; a gym-TM-taught move ignored.
  - `repro_box_counter_move_test.py` must stay green.
- **Replications:**
  - `mauville_prewattson.ss1`: Geodude L15, no make-room, bare Mauville heal.
  - `prenorman_fodder_grind.ss1`: normalize to the overworld first; Machop L15; heal through `heal_at_petalburg`; the KI-78 twin is present in the party.

**Side effect of the scratch runs.** On shutdown the emulator auto-saved states under `sandbox-pokebot/profiles/repro-ml/states/`, one of them `2026-09-27_10-05-31.ss1`, and updated `current_state.ss1`. Both paths are gitignored (`sandbox-pokebot/.gitignore:12`), so no tracked file changed. `party_accounting_ledger.jsonl` was already modified before these runs.

Files are in <session scratchpad>/:
- probe_boxfirst_counter_fixtures.py
- probe_boxfirst_shortlist.py