# 2026-09-27 — USER RULING 20, Phase 1 (the PC as the runway): DESIGN — a NOTE, not truth

> ⚠ **AI RESEARCH NOTE — NOT A SOURCE OF TRUTH.** A four-angle read-only recon took four angles: the existing PC code,
> the `#24-partycap` history, decomp mechanics, and an adversarial angle. A fifth agent synthesised them. Verify every
> load-bearing claim at file:line before building on it.
>
> **RESOLVED after this note was written (2026-09-27; see `06-DECISIONS-LOG.md`):**
> - **Its question 1 is ANSWERED BY RULING 20's own words:** "allowed a full team, catching along the way". Catches fill
>   the party up to 6, and the game boxes everything after that. That is arm A. Arm B, re-boxing catches, stays only as
>   a possible measured arm. RULING 13 (the battle team is L65-75, the roster is free) concerns the late-game battle
>   team and does not conflict.
> - **Its question 2 is ANSWERED BY RULING 19's recorded non-selection.** The user did NOT select "protect answers from
>   deposit", so gym-TM recipients get no special protection. Hunted counters stay protected until their badge, as a
>   design default.
> - **Its question 3 is ANSWERED BY USER RULING 22:** a dedicated Shedinja sequence (`#27-shedinjahunt`).

**RULING 20 Phase 1 design: the PC as the runway (a NOTE from four read-only recon reports, 2026-09-27)**

Line references are to `sandbox-pokebot/` unless another path is given, and come from the four reports. "(synth)" marks something I read myself for this synthesis: the `saves/` listing, `FIXTURES.md5`, the headers of `story_harness.py` drivers, and the entries in `06-DECISIONS-LOG.md`. Nothing was edited.

## Two facts the design rests on

1. **The game gives no choice at catch time.** A catch fills the first empty party slot. Only when all six slots are used does it go to the box, automatically and with no menu (`GiveMonToPlayer` → `CopyMonToPC`, `pokemon.c:4425-4479`). The bot's handler presses B at the nickname prompt, which prints one "transferred to SOMEONE'S PC" message (`battle_handler.py:893-898`). This was driven live once (`28-HANDOFF-ARCHIVE.md:4768-4772`).
   - The real limit is on our side. Field HMs and TM/HM teaching read only the party (`scrcmd.c:1713-1732`, `item_use.c:807-811`). Nothing moves a boxed mon into the party except a PC visit.
2. **The size of the party does not dilute EXP.** EXP is split only among alive participants (`battle_script_commands.c:3292-3350`). A passenger in the party costs nothing unless it is chosen to lead or to replace a fainted mon.
   - That choice ranks type before level: leads at `team_policy.py:293-299`, replacements at `story_mode.py:242-262`.
   - Both orders are ruled, so who is in the party is the only lever we have.

## (1) What Phase 1 must build, in order (MISSING or PARTIAL only)

Every item goes behind its own registered flag, separate from the fence flag. Constraint C23 says the PC paths must not be bundled with the fence change.

**1. One protected-deposit function, keyed by (PID, species). PARTIAL.**
- The species is part of the key because a Shedinja carries its Ninjask's PID (KI-78; `pc_trip.py:594-596`).
- It must be consulted at all three deposit sites:
  - `pc_trip.py:128`, the rotation deposit (off by default);
  - `pc_trip.py:286`, the make-room deposit's victim pick through `find_dead_weight` (`team_policy.py:170`);
  - `pc_trip.py:533-536`, the make-room step inside `withdraw_from_box`, which today skips only the PIDs being withdrawn.
- When it lands:
  - The false promises become true: the comment at `story_mode.py:2154` and the printed line at `:2862-2866`.
  - Gate G8 (`probe_gymtm_teach.py:463-465`) must change from a substring check to a behavioural check at each deposit site.

**2. Expire `_hunted_counter_pids` when that boss's badge is earned. MISSING.**
- The set is created at `story_mode.py:2224` and added to at `:2862`. It is never cleared (`03-PUNCH-LIST.md:3981`).
- Without expiry, a boxed counter is pulled back at every heal, which is churn.

**3. A make-room victim that always answers for a required errand. MISSING.**
- Change `deposit_one_dead_weight` (`pc_trip.py:224`, pick at `:286`) and the withdraw's make-room step (`:533`) to:
  1. try dead weight first, as today;
  2. if there is none and the errand is required (an HM or a counter), take the lowest-ranked unprotected member.
- The "party is full" raise in `ensure_hm_learner_making_room` (`early_game.py:5200-5210`) becomes the last resort, used only when every member is protected. It must log who was protected.
- The deposit stays one per errand (C7). It stays arbitrated with the withdraw through `withdraw_pid_source` and `withdraw_precedence` (`higher_level_actions.py:53`, `:79`; C4, the `#24-pcpingpong` fix).

**4. Route the full-party raise in `ensure_hm_learner` (`early_game.py:4958-4963`) through the making-room path for every caller. PARTIAL.**
It will fire more often once parties are full.

**5. Box-first for Strength, Waterfall and Fly. MISSING.**
Reuse `boxed_hm_learner_pids` (`early_game.py:4707`), `_withdraw_hm_learner` (`:5052`) and `ensure_hm_learner_making_room` (`:5117`).
- **Strength:** `ensure_strength_learner` (`early_game.py:8719`) raises at `:8744-8749`. Its callers are `early_game.py:8309` and `:9010`, in the Magma Hideout flow (synth).
- **Waterfall:** `ensure_waterfall_learner` (`victory_road.py:962`) raises at `:1052`. Caller: `story_mode.py:5654` (synth).
- **Fly:** `ensure_fly_learner` (`pokemon_league.py:2196`) returns `no_learner` at `:2256`. Caller: `story_mode.py:5722` (synth).
- ⚠ `PC_STAND_TILE` (10,2) (`pc_trip.py:36`) is valid for all 16 Poké Center 1F maps, whose PC is at (10,1) (decomp scan). The League 1F PC is at (6,1), so the Fly path needs a stand tile for each map. Which tile works is UNVERIFIED.

**6. Check the box for a counter before hunting one. MISSING.**
- In `_counter_ladder` (`story_mode.py:2733`), before `find_counter_candidates` (`:2772`) and `hunt` (`:2814`), call `box_counter_pid(needed, exclude_pids=…)` (`counter_hunt.py:235`). It exists; today it is called only after a hunt (`:562`).
- If a counter is boxed, register its PID and let the next heal withdraw it.

**7. Choose the centre by reachability. PARTIAL.**
- Rank each call site's centre tuple by `region_reach.hops_to` and `is_map_reachable` (`region_reach.py:469`, `:483`):
  - the tuples at `early_game.py:5074-5084` and `:5183-5194`;
  - the Surf tuple at `story_mode.py:5155-5158`;
  - the training-area map at `story_mode.py:1567`.
- Keep the existing try-and-fallback (`HealWalkFailedError`). The warp graph does not see scripted transport such as the Lavaridge cable car, so a "reachable" answer can still bounce.
- Send Lavaridge and Petalburg heals through their existing fallbacks, `heal_at_lavaridge` (`early_game.py:6432`) and `heal_at_petalburg` (`:6974`). Today the generic heal used by make-room and the HM withdraw still walks the old path (C20).

**8. Restock balls at the reserve, at the nearest reachable mart. PARTIAL.**
- Today `provision_poke_balls` (`early_game.py:2624`) always uses `RUSTBORO_MART` (`:2458`). It fires only at 1 ball or fewer, and only from inside a mandatory hunt: `:2676-2680`, `:5009-5011`, `counter_hunt.py:471-475`.
- Add a trigger at the dex reserve (the gate at `story_mode.py:1924`), piggybacked on a heal in a town that has a mart. Keep the ₽500 floor (`:2455`).
- Do not buy discretionary balls after badge 7 (the plan note). Model the League basket (`league_reserve.py:52`).
- ⚠ The counter stand tile is proven only at Rustboro (3,3) facing Left; `league_reserve.py:54` says Sootopolis shares that layout.

**9. Accept the Castform gift at a full party instead of declining it (`early_game.py:7253-7254`). PARTIAL.**
- The code declines with B. Whether the decomp sends Castform to the PC is UNVERIFIED (see the disagreements below).

**10. Per-catch telemetry at `[DEXCATCH] attempt` (`story_mode.py:3926`): balls, frames and outcome (C15). Status disputed** (see the disagreements below).

**Phase 2, not Phase 1** (listed so nobody builds them early):
- `_catch_team_target` (`story_mode.py:2195`);
- a "nothing admissible left" exit for `catch_starter_team` (`early_game.py:2671-2687`);
- the egg check at a target of 6 (`:1894-1900`);
- the pre-gym-1 attempt cap and first-faint bail (06, 2026-09-27);
- the fence gate order (C17).

## (2) The deposit and withdraw policy

**Protected on every path. The protected function returns these:**
- Game rules: the last living non-egg mon, and any mon holding Mail (`pokemon_storage_system.c:2645-2659`).
- The PIDs being withdrawn in this visit (existing, `pc_trip.py:536`).
- The sole carrier of each HM the party knows (existing, `team_policy.py:147`).
- The only compatible learner of an HM that is still required and not yet taught. This stays until box-first (item 5) covers that HM.
- A hunted counter, until its boss's badge (needs item 2).
- A gym-TM recipient, until its boss's badge (`gym_tm_teach.py:493`). **This depends on user question 2.**
- From §Ch24 readiness on, the six fighters.
  - RULING 12: never box one to dodge the L65 floor.
  - RULING 21: the Fly swap may box one briefly; the same six are restored and checked by PID before R1.

**When a deposit happens.** Only on demand, one per errand, and only when an errand needs a slot:
- (a) a required HM learner is in the box, or must be caught, and the party is full;
- (b) a counter must be withdrawn and the party is full.

Never on every heal and never down to a floor. Rotation stays off (`POKEBOT_PC_ROTATION=0`, `pc_trip.py:83`); it was measured harmful: "party is now 3" 73 of 75 times, and 2 of 37 finishes (C8).

**Who is deposited:**
1. Dead weight, lowest level first (today's rule).
2. If there is none and the errand is required: the lowest-ranked unprotected member.
3. If everyone is protected: raise with a named reason.

Only under arm B of question 1: a dex-catch "passenger" is deposited by identity at the next PC visit, unless an HM or counter need claims it.

**Withdraw:**
- Box-first for every HM consumer and every counter, before any hunt.
- One arbitrated plan per visit.
- Graded by identity: the (PID, species) is in the party and gone from the box. A whiteout must propagate (KI-79, KI-81).

**When a PC trip happens.** Only as a piggyback on a Poké Center heal (`higher_level_actions.py:492`, block at `:677-719`); there is no standalone PC trip. An errand triggers a heal at the centre chosen in item 7. A restock rides on a heal in a town with a mart.

## (3) Party or box, and how the six are chosen

The decomp answers the first half: there is no "send to box" option while a slot is free. So "box by default" means one of two things:

- **(A) Keep the party full.** Catches fill slots up to 6, then the game boxes everything automatically. This is the direction the ruling describes: "allowed a full team, catching along the way", with the PC paths replacing the runway (06:7431-7447). It is also the `#24-partycap` state, which is why Phase 1 must land first.
- **(B) Join, then re-box.** A catch joins while a slot is free and is deposited by identity at the next heal unless an HM or counter need claims it. This is the adversarial report's recommendation. It fits RULING 13's text: "dex catches … live in the PC" (06:7101).

**Recommendation:**
- Build the Phase 1 machinery so it serves both A and B, since neither needs different PC code.
- Make A the Phase 2 target, because RULING 20 is the later and more specific ruling. Keep B as a measured arm, and ask the user (question 1).

**How the six are chosen under A:**
- The first six owned are the team.
- After that, membership changes only at a PC visit, when a required errand swaps in a boxed HM carrier or counter. The victim follows the order in section 2.

**The residual risk under A** is C9: a fresh low-level catch can lead a boss or come in as a replacement, because type ranks before level. 13.9% of faint choices sent a mon 15 or more levels behind (NOTE only).

## (4) The partycap mechanisms, and how this design avoids each

These come from the history report, using the logs of batches `x4-runs/20260805-122057` and `20260805-075638`.

**1. No Surf learner and no free slot. 10 of 16 non-finishes; accounts for the whole 36 points.**
- Today: make-room plus box-first Surf.
- Replaying the 10 failing parties: 8 had a dead-weight victim; 2 level-even Treecko parties had none.
- Avoided by: item 3 (a victim always exists for a required errand), item 4 (every raise goes through make-room), and item 5 (the same fix for Strength, Waterfall and Fly).
  - The partycap batch only reached Winona, so those three HMs were never tested with a full early party.
- Still UNVERIFIED: how often the box holds a Surf carrier at badge 5.

**2. No free slot for a boss counter. 3 of 16.**
- Today: a counter caught at a full party goes to the box and is withdrawn at the next heal.
- Still seen at cap 4: "nothing is safe to deposit — leaving it boxed" 6 times, in `20260910-203458/L07` and `20260911-230219/L07`. Both runs later derailed at Winona.
- Avoided by: items 1, 2, 3 and 6.

**3. Shedinja is lost when no slot is free at Nincada's evolution. No measured rung cost, but a real loss.**
- Partycap had 21 Ninjask evolutions and 0 Shedinja. In the baseline, 5 of 17 Balance Badges were won with Shedinja leading.
- Not avoided by this design. See user question 3.

**4. Ruled out as causes:** EXP split, time or frame caps, balls, the Knuckle→Dynamo dip, and the logging error.

**5. New risks that opening the fence adds** (adversarial report, not partycap causes):
- the ball drain before gym 1 (C12; 18 of 38 runs, NOTE);
- catch whiteouts (C19);
- the Route 116 loop spinning with nothing admissible left (C18);
- catches ending a hunt early (C17);
- maintenance starvation (C10) and the §Ch23 training cost (C11).

These are handled by Phase 2's gates plus items 8 and 10.

## (5) A/B plan

All fixtures below were confirmed with `ls tools/story-dev/saves/`. Every driver grades by identity (PID plus species, never counts) and has a fault arm. Before running any of them, compute the discriminator on the fixture and show that the arms actually differ.

**Driver-level correctness proofs**

**D1. Required make-room at a level-even full party** (items 3 and 4)
- Fixture: `fortree_gym_wedge.ss1`, with the existing driver `--driver hmpcfirst`.
  - PINNED. Party: Mightyena, Sceptile, Swellow, Skitty, Zigzagoon, Castform, full at 6. None can learn Waterfall. Boxes empty (`FIXTURES.md5:88`; synth).
- Discriminator: first compute `find_dead_weight` on this party. If it already returns a victim, the level-even arm is vacuous. Then inject the history report's even L07 party (Swellow 34 / Ninjask 29 / Grovyle 30 / Loudred 27 / Dustox 27 / Mightyena 28) using `debug_write_party`.
- Arms:
  - flag off: expect the "party is full" raise;
  - flag on: expect the boxed Wailmer's PID in the party, and every protected PID still there.
- ⚠ The driver's docstring says "Built + gated 2026-09-25; never RUN" (`story_harness.py:21159`, synth). Whether it has been run since is UNVERIFIED.

**D2. The protected set is honoured on every deposit path** (items 1 and 2)
- Fixture: `fortree_gym_wedge.ss1`, with the existing `--driver boxcounter2` (story_harness docstring ~:5745), which publishes an injected counter's PID.
- Make a registered counter the only dead-weight member, then assert that make-room skips it.
- Fault arm: remove the protected-set consult; the counter must then be boxed.
- For the KI-78 PID collision, use `ch13_fortree_door.ss1`.

**D3. Box-first counter before a hunt** (item 6)
- Fixture: `fortree_gym_wedge.ss1`, with a counter injected into the box but NOT registered. Assert that no hunt starts and the PID lands in the party.
- Arm without the injection: the hunt must start.
- Other fixtures for other bosses: `mauville_prewattson.ss1` (Wattson) and `prenorman_fodder_grind.ss1` (Norman).

**D4. Strength box-first**
- Fixtures: `jagged_descent.ss1` (the `magmadoor` driver) or `magma_door.ss1` (`magmahideout`). `magma_door.ss1` is re-captured by other drivers, so copy it first.
- Premise, UNVERIFIED: that no party member can learn HM04. Check it with `--driver partypids`. If a learner is present, inject a party with none.

**D5. Waterfall box-first**
- Fixture: `post_badge8.ss1` (the `ch23teach` driver).
- ⚠ Wailmer is the sole carrier of Dive, Surf and Waterfall, and a single point of failure (`FIXTURES.md5:49-50`). The driver must assert it is still in the party by PID.
- Alternative: drive `ensure_waterfall_learner` from `fortree_gym_wedge.ss1`, whose premise is already proven.

**D6. Fly box-first and the League PC tile**
- Fixtures: `post_moveset.ss1` (the `ch24fly` driver) and `post_league_lobby.ss1` (sealed against the gauntlet).
- Swellow is the only Fly learner (`FIXTURES.md5:63`). Box it, then assert box-first withdraws it through the (6,1) PC.
- Assert the RULING 21 restore by PID.

**D7. Centre by reachability** (item 7)
- Fixtures: `lavaridge.ss1` and `norman_done.ss1` (the existing `lavaheal` and `petaheal` drivers). Run the generic make-room heal from those positions.
- `probe_heal_reachability.py` exists and can be reused.

**D8. Restock at the reserve** (item 8)
- Fixture: `rustboro.ss1`, where the stand tile is proven, with balls written down to 10 or fewer.
- Then `post_winona.ss1` or `post_mtpyre.ss1` (16 balls, `story_harness.py:2081`, synth) for a mart that is not Rustboro. Run `probe_mart_reachable.py` first.

**D9. Regression: a catch at a full party lands in the box**
- Fixtures: `post_mtpyre.ss1` (`--driver boxcatch`) and `boxwithdraw.ss1` (party 6, box 2).

**Fixtures for the Phase 2 fence arms:** `route116team.ss1` and `gym1_done.ss1`.

**Pure gates that must change** (keep every flag-off case as the regression arm):
- `probe_dex_catch_fence.py` (C2, C3, C20, and `FAULT_MUST_BREAK` at `:170`);
- `probe_dexcatch_rate.py` (R2);
- `probe_dexcatch_bail.py` (D2);
- `probe_dexfence_opportunity.py` (`FULL_PARTY=6`);
- G8 in `probe_gymtm_teach.py`;
- `repro_team_policy.py`, `probe_slot_free_plan.py`, `repro_withdraw_pid_source.py`, `repro_withdraw_room.py`, `repro_boxed_hm_learner.py` and `repro_pc_overflow.py`.

**Phase 3: the batch-level frequency question**

Run one concurrent batch with interleaved arms, on the same commit, stratified by starter. Partycap's losses were all Torchic and Treecko runs; Mudkip carries Surf itself.

Arms:
- **A0:** everything off.
- **A1:** Phase 1 on, fence closed. This isolates the PC paths, per C23.
- **A2:** Phase 1 on, fence open, using the user's answer to question 1.
- Optionally **A3:** the other choice from question 1.

Pre-register:
- **Primary:** finish rate, plus the per-rung funnel with Balance→Feather called out. The partycap cause was only visible per rung (76% → 21%, z=3.06).
- **Secondary:**
  - "party is full" HM derails (predicted 0 in A1 and A2);
  - "nothing is safe to deposit" (predicted 0);
  - make-room success rate;
  - box-first hits;
  - species owned per run;
  - balls at each badge; balls and frames per catch;
  - `[DEXCATCH-BAIL]` fires;
  - whiteouts in catch battles;
  - Shedinja and Castform presence.

State the power honestly. At about 20-30 runs per arm, this can only rule out a collapse the size of partycap's. It cannot certify a small regression. Compute the needed n from today's baseline finish rate before registering.

## Where the reports disagree, and the cheapest check for each

1. **Where a free-slot catch goes after gym 1.** The code report and the plan put it in the party; the adversarial report says re-box it (B). This is policy, not fact, so it goes to the user (question 1).
2. **Make-room success rate.** The history report counted 28 of 28 across 10 batches from 09-07 to 09-13; the adversarial report has 36 of 41 from a NOTE. Check: count the make-room success and failure lines in the `x4-runs` logs since 09-07, with the history agent's `runs.py` in the scratchpad.
3. **Castform at a full party.** The code declines it (`early_game.py:7253`); the plan says the decomp would send it to the PC. Check: read the `givemon` and `MON_GIVEN_TO_PC` handling in `data/maps/Route119_WeatherInstitute_2F/scripts.inc` with `gh api`.
4. **Per-catch logging.** Phase 0 is recorded as having built per-species logging; the adversarial report says balls, frames and outcome are logged nowhere. Check: read the fields printed at `story_mode.py:3926`.
5. **Ball stall.** This is derived from code only. The code report says dex catching stalls at 10 balls after gym 1; the history report found no out-of-balls derail at cap 6. Check: the `balls=` heartbeat in the current batch logs.
6. **Whether maintenance shrinks the dead-weight supply (C3).** Read from code, not measured. Check: count dead-weight candidates in the `party=` lines at the Surf gate, before and after 09-12.
7. **Date correction, agreed by all.** The make-room deposit was wired 2026-08-13 (KI-63) and the ping-pong fix landed 09-07. Only the box-first HM withdraw dates from 09-25 (06:7449, synth).

## (6) Questions only the user can answer

I grepped `06-DECISIONS-LOG.md` first. RULINGS 12, 13, 19, 20 and 21 and the 09-27 observations entry were read. The fossil request is already recorded, with "do not re-ask".

1. When the bot catches something new and a party slot is free, should that Pokémon stay on the team as a fighter (RULING 20, "a full team, catching along the way")? Or should it go to the PC at the next Pokémon Center unless it is needed for an HM or a gym counter (RULING 13, "dex catches … live in the PC")?
2. When the bot must free a party slot for a required HM Pokémon, may it put into the PC a Pokémon it hunted as a gym counter, or one it taught a gym TM, before that gym is beaten?
   - 06:7429 records that "protect answers from deposit" was not selected under RULING 19.
   - `protected_taught_pids` was nevertheless built, but it is read only by the rotation path, which is off.
3. Should the bot keep one party slot open around Nincada's evolution (about L20) so that it also gets Shedinja? With a full party it never appears. `story_mode.py:1355` records Shedinja winning 39% of Norman fights.
