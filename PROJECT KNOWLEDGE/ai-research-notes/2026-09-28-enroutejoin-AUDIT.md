# 2026-09-28 — AUDIT (a NOTE, not truth): where a dex catch that joins the party DURING A WALK is misread (`POKEBOT_R20_OPENFENCE=1`)

> A read-only Claude subagent audit, at worktree HEAD `64973527`. Nothing was edited or driven. Every claim quotes a line;
> verify before building on it. Site A's three load-bearing lines were re-read by me (`early_game.py:5106`, `:5163`,
> `:5185`). Filed for `#27-enroutejoin`.

## WHY THE FLAG MAKES THESE REACHABLE

The fence refuses a catch while:
- `hunt_armed = is_armed() or HM_CATCH_TARGET_DEX` (`story_mode.py:2467`) holds;
- training is on;
- or the party is hurt.

**Both hunts arm only AFTER walking, so the fence is open for the whole walk.** Before P2-b, a post-gym-1 dex catch
happened only at a full party and went to the box, so the party never changed during such a walk. Shinies were the one
exception.

## A. `ensure_hm_learner` (rank 1). Flag ON, after gym 1, party below 6

1. **The snapshot is taken at entry.** `early_game.py:5106` `party_count = len([...])`.
2. **Two walks follow, with the fence open for both:**
   - `:5159` `provision_poke_balls()` (only when balls ≤ 1);
   - `:5163` `_navigate_riding_out(map_enum, tile)`, which ends on encounter tiles.
3. **Arming and the stale comparison:**
   - `:5183` `HM_CATCH_TARGET_DEX = {...}`;
   - `:5185` `before = party_count`;
   - `:5197` stop when `len(party) > before`.
4. **The spin ends on its first frame.** Unless the new member can learn the HM, `:5205` raises "Hunted for a {move}
   learner but never caught one (timeout/balls)". Nothing was hunted.
5. **Nothing handles that error:**
   - `ensure_hm_learner_making_room` re-raises anything without "party is full" (`:5347`);
   - the retry `:5392` and the three call sites have no handler;
   - so the result is a DERAIL.
6. **The worst case is the make-room retry.** The party has just been healed at the centre and has exactly five
   members. The retry walk therefore has the fence open, and the first unowned wild takes the freed slot. This can
   repeat, and the derail cap (`_derails > 4`) usually resets because `_progress_sig` includes party size.
7. **An identity stop alone does not fix 5 → 6.** At 6, the HM catch branch refuses the target (`story_mode.py:3830`,
   `len(party) < 6`), so the hunt would spin to its 40,000-frame deadline instead.

## B. `counter_hunt.hunt` (rank 2)

The order is WALK → SNAPSHOT → ARM, not the build spec's "arm, walk, snapshot":
- `:542` provision;
- `:558` `_navigate_riding_out(…, tries=24)`;
- `:560` `before = _party_count()`;
- `:577` the PID snapshot;
- `:580` `arm([...])`.

The success test is right, because the identities are taken after the walk. The PLAN made before the walk goes stale:
- **B1. A party of 5 becomes 6 during the walk.** The counter is then caught into the BOX (`box_counter_pid`), and the
  ladder prints "the counter is in the PC box — skipping training". Rung 3 is skipped silently.
- **B2. The target species itself is caught on the approach.** That copy is inside the after-walk snapshot, so it is
  excluded. The hunt then spins up to 120,000 frames for a second copy, and the first copy can push the real counter into
  the box.
- **B3. The ladder's "no party answer" verdict is never re-checked** after a counter-typed species joins on the walk.

## C. Box-first withdraw re-picks (rank 3; practically unreachable)

The sites:
- `early_game.py:8955-8964` (Strength);
- `victory_road.py:1083-1090` (Waterfall);
- `pokemon_league.py:2496-2520` (Fly).

Each withdraws a mon, re-picks the learner, and raises if the pick is not the withdrawn PID. A learner that joined on the
walk could trip a false alarm. None of these walks crosses land-encounter tiles: they go to the centre just used, to
Sootopolis, or to the League lobby.

## CHECKED AND SAFE (the auditor's list, condensed)

- **`early_game.py:5355` heal:** the party is full then, so a catch goes to the box.
- **`pc_trip.py`:** live reads inside the centre.
- **The heal piggybacks in `higher_level_actions`.**
- **`_withdraw_hm_learner`:** asserts by PID.
- **`train_team` and its callers:** `set_swap_train(True)` closes the fence for the whole grind, including its walks.
- **`train_counter(slot)`:** no walk before the read.
- **The HM teach sites; the `sootopolis`, `sootopolis_gym` and `victory_road` iterations over `before`.**
- **`pokemon_league.py:1315`:** covers `fly_to` only.
- **Also safe:** `gym_tm_teach`, `amulet_coin`, `space_center`, `overworld_items`, `obstacle_clearing` and
  `region_reach`.
- **The party's last slot:** nothing assumes what it holds.
- **The AST scan:** snapshot → walk or spin → use, over `modules/story/*`, `story_mode.py` and `higher_level_actions.py`.
  It found only A, B and C.

## NEARBY, OUTSIDE THE QUESTION (not verified in depth)

- **Composition, not staleness.** Readers that treat every battler as a trainee take a fresh, far-below catch as a new
  trainee:
  - `victory_road.team_is_ready`;
  - the Rustboro rival's `train_team(level_floor, "whole")`;
  - `_maintain_lagging_battler`;
  - `plus5_avg`.

  That is a Phase 3 frequency question.
- **A pre-gym-1 hunt's spin can be cut short by a team catch, independent of this flag.** The `pre_badge1` branch returns
  before `hunt_armed` in `decide_dex_catch`. That is exactly P2-c (hunt-armed first), which the build spec already has.
