# Known Issues — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. Open problems only — when an issue is
> fixed, remove it here and record the fix in 07-CHANGELOG.md.
> Entry format below; KI numbers never get reused.

<!--
## KI-1 — <short title>   (opened YYYY-MM-DD, severity: high/med/low)
- **Symptom:** what goes wrong
- **Repro:** how to trigger it
- **Suspected cause:** best current theory
- **Workaround:** if any
-->

## ‼ HOW TO READ THIS FILE (re-audited against code 2026-07-27)

**Only KI-1 … KI-5 are upstream bugs.** They exist identically in
`40cakes repo/pokebot-gen3/` (pristine — do not fix there) and in our forks (fix
candidates; any fix goes in DIVERGENCE-LOG). *The paragraph that used to sit here
claimed ALL entries were upstream bugs — it was written when the file held five, and
was wrong for the other eighteen.*

**Everything from KI-6 onward is OUR OWN story-bot / fork code**, and the active copy
is **`sandbox-pokebot/`** (not `custom-pokebot/`). KI-23/KI-24 concern
`modules/story/region_reach.py` and `modules/story/counter_plan.py`, which are ours and
have no upstream equivalent.

**Numbering:** IDs are **not contiguous** — there is no KI-12 and no KI-13 in this file.
23 distinct IDs across 25 headings (KI-1 and KI-15 each appear twice).

**Status re-audit 2026-07-27.** Every entry was checked against `sandbox-pokebot/`.
Entries proven fixed are now marked `✅ FIXED` in their heading with the fixing
`file:line`, and their superseded diagnostic bodies are collapsed under a
`<details>`-style "superseded" marker rather than deleted, because several were
proposing work that is already shipped:

| entry | why it was dangerous | proof of fix |
|---|---|---|
| KI-18 | body said *"Do NOT patch on the hypothesis. Reproduce first"* — it WAS proven and patched | `modules/battle_handler.py:475-501` (`_on_field` exclusion, KI-18-labelled) |
| KI-17 | body said *"Workaround: none in-run yet"* + prescribed a decomp read that is done | `modules/battle_handler.py:508-528` (`post_gap=24`; never gamble an A) |
| KI-16 | heading said FIXED, body still said *"use this repro for a focused fix"* | `modules/story/early_game.py:4434-4470` (`_rock_present()` world-judged) |
| KI-24 | body read as an open architectural bug; KI-24b already declares it fixed | `story_mode.py:553` and `:606` both call `region_reach.is_map_reachable` |
| KI-11 | body said `deliver_devon_goods_to_stern` stays **UNWIRED** — it is wired | `modules/story/early_game.py:3397-3412` (Shipyard → Dock leg) |
| KI-7 | a duplicate "(old text)" block restated the fixed bug as live | `modules/modes/util/higher_level_actions.py:59` (`BADGE06_GET`) |

**✅ RESOLVED — USER RULING 2026-07-29 (`#doc-policy-05`, option A):** entries fixed in
`sandbox-pokebot/` but not yet promoted to `custom-pokebot/` are **RETAINED here and marked
`✅ FIXED` with the fixing `file:line`**, because they are still open *for the production
copy* and deletion would lose the only promotion-owed signal. They are removed only once
promoted. This overrides the "remove it here" instruction in the file header above for the
sandbox-fixed case.

## KI-1 — Upstream pokebot.spec (PyInstaller) is stale/broken   (opened 2026-07-17, severity: low)
- **Symptom:** `pokebot.spec` references `import.py` (file doesn't exist in
  the repo) and a repo-root `sprites/` dir (sprites actually live at
  `modules/web/static/sprites/`); a PyInstaller build would fail as-is.
- **Repro:** `pyinstaller pokebot.spec`.
- **Suspected cause:** spec never updated after upstream restructures;
  upstream releases are source ZIPs, so the spec is unexercised.
- **Workaround:** run from source (our normal path). Relevant to punch-list
  #4 only if we ever want packaged builds.

## KI-2 — Upstream `BattleStateSide.modified_stats()` raises TypeError   (opened 2026-07-17, severity: low)
- **Symptom:** `modules/battle_state.py:590` builds its stage-multiplier
  table from set literals (`{10, 40}`), which can't be indexed — calling
  `modified_stats()` raises `TypeError`. Zero callers in the repo (dead
  code), so nothing breaks today.
- **Workaround:** use `stats_modifiers` (battle_state.py:587) and apply
  multipliers yourself. Must be fixed in custom-pokebot before any custom
  battle brain relies on it.

## KI-3 — Upstream stale docstring names nonexistent battle opt-out   (opened 2026-07-17, severity: low)
- **Symptom:** `modules/modes/_interface.py:62` docstring tells mode
  authors to call `self.disable_default_battle_handler()` — that method
  doesn't exist anywhere. The real mechanism is returning
  `BattleAction.CustomAction` from `on_battle_started()`.
- **Workaround:** documented in `40cakes repo/DOCUMENTATION/03`; keep in
  mind when writing custom modes.

## KI-4 — Cloud-sync requires backups enabled (opened 2026-07-19, severity: low)
- **Symptom:** If `backups enabled: false` but `sync.enabled: true`, every
  clean exit logs "sync FAILED (backup could not be created)" — cloud-sync
  is built on the backup system. Honest failure, NOT data corruption.
- **Workaround:** enable backups when using cloud-sync. Fix candidate: a
  config-validation warning at load.

## KI-5 — Background git calls could wait on a credential prompt (opened 2026-07-19, severity: low)
- **Symptom:** cloud-sync/update-check git fetch/push could block up to its
  timeout if a remote interactively prompts for credentials.
- **Mitigation in place:** all such calls are timeout-bounded on daemon
  threads, so startup is never blocked. Fix candidate: set
  `GIT_TERMINAL_PROMPT=0` in the subprocess env.

> 📦 **KI-6 and KI-7 moved to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-13** — both resolved July
> 2026. Moved verbatim, nothing deleted, to keep this file inside its 3,000-line budget (rule R3).

## KI-8 — Mid-battle rotation execution can stall the party-menu switch (opened 2026-07-21, severity: med)
- **Symptom:** a mid-battle switch (`TurnAction.RotateLead`) into a weak/underlevelled bench
  hung the in-battle PARTY_MENU (Roxanne with Torchic vs Rock + an L6-7 bench → stuck, then
  Manual). `state=3` = PARTY_MENU.
- **Where:** `modules/battle_action_selection.py` `case TurnAction.RotateLead` →
  `scroll_to_party_menu_index(map_battle_party_index(index))` → `while get_game_state() ==
  PARTY_MENU: press A`. If the target is mis-mapped or the party-menu submenu default isn't
  "SHIFT", the scroll loop (`menuing.py`) or the A-press loop spins.
- **Mitigation (done):** the Story bot's trainer-battle strategy now ATTACKS through and never
  proactively rotates in a trainer/gym/E4 battle (`LevelUpTravelBattleStrategy.decide_turn`) —
  so it sidesteps this path. Faints are handled reactively by the after-faint chooser (which
  correctly excludes fainted/active/double-partner mons).
- **Proven fix pattern now exists (2026-07-22):** the after-faint SIBLING of this exact
  blind `while PARTY_MENU: press A` loop deadlocked deterministically in Ch9 and was fixed
  with a STATE-AWARE sweep (read cursor slot + party HP + active task — including
  `Task_HandleSelectionMenuInput`, the real Emerald popup task — and press the one button
  that advances, with press/release gaps; see `handle_fainted_pokemon` in
  `battle_handler.py`). When KI-8 is reproduced, port that same sweep to the RotateLead
  path in `battle_action_selection.py`.
- **Still open (for Fable):** any strategy that DOES rotate (e.g. SwapTrain in an unexpected
  double/trainer case) is exposed. Reproduce a live rotation into a specific slot and pin
  `map_battle_party_index` / the party-menu submenu handling. Good first target: the Slateport
  **Gabby & Ty DOUBLE battle** (§Ch8) — it also validates the after-faint double-battle fix.

> 📦 **KI-9 moved to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-13** — MITIGATED 2026-07-21.

> 📦 **KI-10 moved to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-13** — MITIGATED 2026-07-22.

> were ✅ FIXED same-day in July 2026. Moved verbatim, nothing deleted, because this file crossed
> its 3,000-line budget (lint rule R3) when KI-70/KI-71 were filed.

> 📦 **KI-19 moved to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-13** — FIXED-PENDING-WIRING 2026-07-24.

## KI-20 — TRAPS confirmed against the decomp (2026-07-25) — read before building these systems

From `ai-research-notes/CLAUDE-VALIDATED-concepts-round2.md`. Each was verified by reading the
decomp, not recalled.

**‼ NEVER put an HM holder in the DAYCARE.** `ApplyDaycareExperience` calls
`DeleteFirstMoveAndGiveMoveToMon` with **no HM check and no prompt** — **move slot 1 is deleted
silently**. This is worse than the research note claimed (the note framed it as a normal
move-learn prompt). Any future daycare/training feature must refuse a mon holding an HM in slot 1,
and ideally refuse HM holders entirely. This is the single most destructive automated action found
so far: it strands a run with no error and no dialogue.

**`get_map_objects()` is not a room inventory.** `TrySpawnObjectEvents` only spawns objects inside
a CAMERA WINDOW, so the list is systematically incomplete just after a warp. `do_fortree_gym`
survives this only because it re-plans every tile; a comment now says so at the call site. Never
precompute a route from one object snapshot, and never read an empty list as "clear".

**Self-caught Pokémon NEVER disobey.** `IsMonDisobedient` (in `battle_util.c:3923`, *not*
battle_main.c) returns obedient before any badge logic unless `IsOtherTrainer(...)`. So the
"army" strategy needs **no** level cap; only in-game TRADES are capped (10/30/50/70).

**Encounter-rate corrections** (any XP-per-frame table built on the old numbers is wrong):
running shoes do **not** affect encounter rate at all — only the bike does (×0.8) — and the grass
rate constant is **20**, not 21. `Sweet Scent` bypasses Repel *and* the rate roll entirely
(flags=0) ⇒ a **guaranteed** encounter, which makes it the correct grinding primitive.

**Verified-correct, no action:** the Fortree "leave and re-enter resets it" recovery is right on
BOTH halves — gate orientations live on `VAR_TEMP_0..3` and are cleared twice over
(`ClearTempFieldEventData` plus `RotatingGate_InitPuzzle`), and NPC positions are restored by
`LoadObjEventTemplatesFromHeader` → `ResetObjectEvents`/`TrySpawnObjectEvents`. The user's reported
NPC-reset mechanic is real. Returning from a BATTLE is not a map load, which is precisely why the
parked-trainer case exists. Also verified: our `get_current_repel_level()` already reads the right
thing (`VAR_REPEL_STEP_COUNT`, first non-fainted non-egg member).

**Refuted:** the trainer AI does **not** switch on AI flags (no `AI_FLAG` references in
`battle_ai_switch_items.c`); real triggers are Perish Song / Wonder Guard / ability-absorbers /
Natural Cure, and it never switches while holding a super-effective move — so AI-baiting is less
reliable than the notes implied. Whiteout money is plainly `money / 2`
(`GetWhiteoutMoneyPenalty` does not exist). Shedinja does **not** need a spare Poké Ball, only a
free party slot.

## KI-21 — Decomp-verified facts that will otherwise cost the NEXT build phase (2026-07-25)

From `ai-research-notes/CLAUDE-VALIDATED-story-round1.md` (~65 claims ruled, every one citing a
fetched decomp file). These are the ones that would have produced mystery hangs.

**‼ 1. EVENT FLAGS ARE NOT ALL MONOTONIC — our resume gating assumes they are.**
`StoryMode._play` gates every segment on `_done("FLAG_NAME")`, which silently assumes a set flag
stays set. **It does not always.** Verified non-monotonic: `FLAG_DEFEATED_MAGMA_SPACE_CENTER` (the
rival's PokéNav call `clearflag`s it), the four Elite-Four member flags (wiped at the Hall of
Fame), the event legendaries, Shoal Cave (daily), the fan-club TM (weekly).
**New prevention rule: passing `audit_flag_names.py` proves a name is READABLE, not MONOTONIC.**
Any segment gated on one of those can re-run or be skipped wrongly. Audit the Ch14+ gates against
this list before building them. (Reassuring: `audit_flag_names.py` currently reports clean, so no
phantom name has leaked into shipped code.)

**‼ 2. FOUR OF EIGHT HMs ARE GIVEN BY A MAP-ENTRY `ON_FRAME_TABLE` TRIGGER, NOT BY TALKING.**
Surf, Strength and Dive fire on entering the map; **Fly is a coord trigger at ROUTE119 (25,31)/
(26,31) that starts `trainerbattle_no_intro` instantly.** Both Gemini generations said "talk to
NPC X" — **a bot that walks up and presses A waits forever.** Our code already handles the Fly
coord trigger (found the hard way in an earlier session), which is a good consistency check on
this ruling.

**‼ 3. A MANDATORY `multichoice` MENU LOOPS FOREVER ON THE WRONG ANSWER.**
`CaveOfOrigin_B1F`: **only index 2 ("Sky Pillar") advances.** Indices 0/1/3, the switch default
AND a B-press all `goto` back to the same prompt — **no counter, no timeout, no escape.** Three of
the four mandatory critical-path multichoice menus default to the WRONG option. All 49
`multichoice` sites were swept and the critical four tabled with correct indices — read that table
before building Ch14+, because this is a guaranteed hang otherwise, and it would look exactly like
the phantom-script wedges we already chased for days.

**4. HM07 Waterfall needs BOTH Maxie AND Archie** talked to at
`VAR_SOOTOPOLIS_CITY_STATE == 5` — the same state unlocks the Gym and every house door. Neither
note mentioned it. `VAR_SOOTOPOLIS_CITY_STATE` has **seven** states, not five; the complete
machine with every setter is in the validated file.

**5. "Missable" was largely invented.** Master Ball, TM Thief, TM Earthquake, the Magma Hideout
items, the unchosen fossil and the S.S. Tidal are **NOT** missable — building interrupts for them
is wasted work. What genuinely vanishes: **Aqua Hideout grunts at Badge 7**, **Magma grunts at the
Groudon cutscene**, and **each Trick House puzzle the moment it is cleared**.

**6. `src/field_move.c` does not exist** and ten cited C functions have zero hits. The real HM gate
is `party_menu.c:3725`. Treat any note's file path as a claim, not a location.

## KI-22 — Round-3 findings, incl. one that AMENDS an earlier "safe" rule (2026-07-25)

From `ai-research-notes/CLAUDE-VALIDATED-concepts-round3.md` (~50 claims, decomp-cited).

**‼ 1. AMENDS KI-20/round-1: "whiteout is the safe abort" is FALSE during the Elite Four.**
`DoWhiteOut` runs `EventScript_WhiteOut`, which is **not** a no-op: it clears **all four**
`FLAG_DEFEATED_ELITE_4_*` and resets `VAR_ELITE_4_STATE`. So a whiteout mid-gauntlet silently
un-does progress. Whiteout remains the safe abort for scripted legendary statics; it is NOT safe
during the E4. This compounds KI-21's non-monotonic-flag warning — the E4 flags are the clearest
example, and any Ch16 gating must not assume they stick.

**‼ 2. Timer Ball has a u8 overflow.** `u8 ballMultiplier = battleTurnCounter + 10` wraps at turn
246 to **0**, which bypasses the `> 40` clamp and feeds `odds = 0` into `16711680 / odds`. Never
throw a Timer Ball past ~turn 240 — relevant to any long legendary-catch loop, which is exactly
where a bot would rack up turns.

**3. Healing is a TABLE, not an inference** — `sHealLocations` has 22 entries, and `setrespawn`
lives in each Poké Center's **ON_TRANSITION**, so merely ENTERING the building moves the respawn
point. There are exactly **five** `Common_EventScript_OutOfCenterPartyHeal` sites, one of which is
**Route 111 Old Lady's Rest Stop** — now decomp-cited, vindicating the user against the first
Gemini round. This is what `#24-npcheal` should be built from.

**4. Dive needs TWO mechanisms.** Round 2 advised settling dive routes from `CONNECTION_DIVE`;
connections give 7 routes (not 4), but **`setdivewarp` is a separate script-level mechanism with
16 sites**, including Route 134 → the Sealed Chamber. A connection-only navigator would declare
the Sealed Chamber unreachable — i.e. round 2's own suggested method was incomplete.

**5. The impossible-without-event-data list (do NOT build hunts for these):** Mew, Deoxys, Lugia,
Ho-Oh, the Southern-Island Latias/Latios and the Soul Dew are unreachable, and **Jirachi does not
exist in Emerald at all** (zero scripts, zero encounter entries). All four event islands are closed
clusters (`connections: null`) with **no warp to them anywhere outside `LilycoveCity_Harbor`**. The
ticket-granting scripts ARE in the ROM but have **zero callers**, and
`ShouldDistributeEonTicket()` is commented `// Always returns FALSE`.

**6. An INJECTED Mew/Deoxys would disobey forever** at any level with all badges — the badge-8 and
own-OT escape hatches sit *inside* the block that gets skipped for non-fateful mons. Scripted
island legendaries use `seteventmon`, so they are fateful and obedient. (`IsMonDisobedient`,
`battle_util.c:3913`; `CalculatePlayerMonObedience` does not exist.)

**7. Mart inventories in the notes were the weakest data in either round** — six rows wrong
(Potion is not sold at every Mart; Hyper Potion/Revive not in Fallarbor; Full Heal not in
Mauville/Lavaridge; **Moomoo Milk is not purchasable anywhere**). All 19 prices were right. The
break-even for "walk to a free heal vs carry potions" is **¥14.0/HP before Fortree and ¥6.0/HP
after** — a flat ¥/HP model is off by 2.3×.

## KI-23 — Winona: the boss-attempt strategy cannot converge without a TYPE ANSWER (2026-07-25)

**Evidence: the user's overnight ENDLESS RESET session (2 runs) + my 5 cold-start runs.**

**Run 1 — 198 Winona attempt-messages, 41 losses, 41 whiteouts, NEVER won.** The last ~567,000
frames were spent entirely inside the Fortree gym sequence (the message never changed across 159
consecutive 3,600-frame heartbeat dumps), cycling: challenge → lose → whiteout → recover →
re-enter. Party at the end: **Sceptile L42, Loudred L39, Mightyena L36, Shedinja L29, Ninjask L28,
Zigzagoon L11.**

**Run 2 — 37 attempts, 32 losses, then WON** (`FortreeCity_Gym_EventScript_WinonaDefeated` +
`Common_EventScript_PlayGymBadgeFanfare` in the final dump; the log ends mid-fanfare). Party:
**Swampert L41**, Swellow L39, Vigoroth L32, Mightyena L18, Castform L26.

**Root cause — not levels, TYPES.** Winona is Swablu/Tropius/Pelipper/Skarmory/Altaria
(L29-33). Run 1's party at L42/L39/L36 was *far* above her levels and still lost 41 times,
because it had **no super-effective answer**: Sceptile (Grass) is resisted by Flying and shredded
by it; Ninjask (Bug/**Flying**) and Shedinja (Bug/Ghost, 1 HP) are worse; Loudred and Mightyena are
neutral. Nothing Electric, Rock or Ice — and Altaria is **4× weak to Ice**. Run 2 won not by
matchup either, but by brute-forcing with a bulky Swampert.

**So the boss-as-training-vehicle strategy has a failure mode we had not seen: it does not
converge when the team has no type answer.** It is not "slow" there — it is a genuine infinite
loop bounded only by the whiteout cap, and levelling further does not help. This is the same
economics as Norman (KI: 35 whiteouts) but worse, because Flying resists the common early types.

**What the fix needs (this is `#24-counters`, and it is exactly the user's stated goal of
"counters after failure and learning"):**
1. **Detect non-convergence** — N consecutive losses to the same boss with no downward trend in
   the boss's surviving mons means the plan is wrong, not under-levelled. Cheap signal: KOs
   scored per attempt is flat/zero.
2. **Then change the PLAN, not the level** — identify a type the boss is weak to, and go CATCH
   one. Against Winona: an **Ice** move (4x into Altaria), or **Rock**/**Dragon**.
   ⛔⛔ **CORRECTED 2026-08-15 — this line said "any Electric (Route 110 Voltorb/Magnemite,
   Mauville area)", and that is the SIXTH copy of one error.** ‼ The nuance matters, so read it
   rather than just deleting the word: **Electric is 2x-or-better against THREE of her five** —
   **Swablu 2.0, Pelipper 4.0, Skarmory 2.0** — **but it is exactly NEUTRAL against the ACE,
   Altaria** (Dragon/Flying: `0.5x` Dragon `x 2.0x` Flying = **1.0**), *and* neutral against
   **Tropius** (Grass/Flying: `0.5x x 2.0x` = 1.0).
   ⚠ *These five numbers were COMPUTED from `modules/data/types.json`, not recalled — a first draft
   of this very correction said "FOUR of her five" and was wrong about Tropius. Seven copies deep
   into one error, do not trust the type chart in your head.*
   ‼ For contrast, the types production actually names: **Ice** is 4.0 into BOTH Altaria and Tropius;
   **Rock** is 2.0 into four of the five but only 1.0 into Skarmory (Steel resists it). ⇒ **the prose is reasonable about her TEAM and wrong about what the CODE
   DOES**, because `_boss_plan_is_hopeless` derives `needed` from the **ACE ALONE**
   (`cfg["ace_types"]`). MEASURED: production returns `needed = ['Rock', 'Ice', 'Dragon']`, with
   no Electric, on every arm of `--driver ki80ladder`. A planner asked for an Electric here would
   be answering a question production never asks.
   `training_areas.py` already knows where species live; the missing piece is
   "what type do I need and where do I get it".
3. Keep the existing escalation for the case where the team DOES have an answer and is merely
   under-levelled — that path demonstrably works (my run1 won Badge 6 cold-start).

**Cross-run confirmation:** my 5 runs show the same shape elsewhere — 2 of 5 died on the whiteout
cap (`#24-whiteout`), and my successful run took 80 whiteouts. Attrition is not a side-effect; it
IS the dominant cost of the current strategy.

### STATUS 2026-07-30 — all three parts of "what the fix needs" are now BUILT (live validation owed)
1. **Detect non-convergence** — `_boss_plan_is_hopeless` (phase 1, 2026-07-25). DONE.
2. **Change the PLAN, not the level** — `counter_plan` names the target (phase 1) and
   `counter_hunt` + `StoryMode._counter_ladder` now TRAVEL, CATCH and TRAIN it (phase 2,
   2026-07-30). `repro_counter_hunt.py`, 15 checks, ALL PASS.
   ⛔⛔ **SUPERSEDED 2026-08-15 — DO NOT ACT ON THE ELECTRIKE LINE.** This bullet used to say the
   planner's own answer was *"Electrike @ ROUTE118 (29,15), L24-26, 30%"*. That output predates the
   ace-only derivation of `needed`: **Electric is NEUTRAL into Altaria** (see the correction above),
   so the planner does **not** propose an Electric today. MEASURED 2026-08-15 on
   `batch2_run04_wedge.ss1`, `--driver ki80ladder`, production's own message: *"Need one of: Rock,
   Ice, Dragon … Nearest reachable counters: **Slugma (Fire) on Fiery Path** (tile (18,19), L15-15,
   10% rate) — reachable; **Geodude (Ground/Rock) on Magma Hideout (1F)**"*.
   ‼ **The standing rule survives and is the point:** trust the planner's MEASURED output over any
   prose in this file — including this sentence. Run it; do not quote it.
3. **Keep the existing escalation** where the team DOES have an answer — untouched; the
   ladder only runs once `_boss_plan_is_hopeless` is already True.

‼ **STILL OPEN — this KI is NOT closed.** Nothing yet proves a run actually catches a
counter and converts it into a win; that needs a live batch. And the regression to watch for
is the mirror of the original bug: with a counter in the party `_boss_plan_is_hopeless` stops
firing, so a boss that used to stop honestly could LOOP instead. The per-run bound
(`_counter_hunts`, one hunt per boss per run) is what prevents it.

## KI-24 — `calculate_path` cannot prove LONG-RANGE reachability; our gates under-report it (2026-07-25)

**Found while validating the counter-catch planner.** From the correct Winona-era save
(`devon_scope_got.ss1`, verified: ROUTE120 (13,16), BADGE05_GET, `_party_can_surf()==True`),
`_training_area_allowed` reports **zero** reachable counters for Winona's types — including
Route 118 Electrike, which is the real answer to her.

**It is not a Surf gate and not an in-game obstacle.** The ROM's `MapConnections` give a genuine,
warp-free, edge-connected chain `ROUTE120 ↔ FORTREE_CITY ↔ ROUTE119 ↔ ROUTE118` — exactly what
`calculate_path` documents itself as supporting. Yet it fails on every hop, **and it also fails on
a same-map walk inside ROUTE119 alone** (y=5 → y=135, no map crossing at all). A same-map failure
rules out map-crossing as the cause.

**Most likely cause — already documented in this project.** Routes 118/119/120 are the
**dual-elevation bridge** maps: `calculate_path` reads those bridges as WALLS. That is precisely
why `_hold_walk_route()` (held-input walking) exists and why `_leave_route120_north_bridge` is
hand-written. A long north-south Route 119 path must cross them, so the planner declares it
impossible. (KI-20's camera-window `get_map_objects()` limitation may compound it, but the bridge
class alone explains a same-map failure.)

**Consequence — this is a REAL limitation in shipped gating, not just in the new planner.**
`_training_area_allowed` and therefore `best_training_area` use tile-level `calculate_path` as
their reachability oracle. On exactly the maps with the best mid-game training bands (115/118/119/
121) that oracle says "unreachable" for reasons that are artefacts of the pathfinder. The
conservative `allow=None` fallback is no better — it proposed **Magma Hideout Geodude** and
**Shoal Cave Spheal** as answers to a Fortree gym, i.e. across the region.

**The fix is architectural, and it is `#24-regionreach`:** reachability at REGION scale should be
answered from the **map-connection graph plus HM/badge gates**, not from tile-level pathing.
"Can I get to Route 118 from Fortree?" is a connectivity question; tile pathing is only correct
for the final leg once we are on the map. The ROM connection data is available and was
hand-verified during this investigation. Doing this would also retire the `AREA_PREREQ`
`"region"` hack that Route 111 currently needs.

**Prevention rule:** a reachability oracle must be sound for the SCALE it is asked about. Using a
tile pathfinder to answer a cross-region question inherits every one of its blind spots as a false
"no", and false negatives are invisible — nothing errors, the option is simply never proposed.

## KI-24b — region reachability BUILT; hop count alone is too coarse to rank by (2026-07-25)

`modules/story/region_reach.py` now answers reachability from the ROM's own `MapConnections` +
warps (never a hand-written table), with capability gates and — the point of the module —
`why_unreachable()` reasons that distinguish **"no connection path"** from **"needs Surf at
A↔B"** from **"reachable but N hops away (limit M)"**. The oracle itself is proven: ROUTE118 is
reachable from ROUTE120 at the Winona moment, where tile-level `calculate_path` said it was not.

**✅ SCOPE — KI-24 is now fixed for BOTH consumers (2026-07-25).** `region_reach` is wired into
`_counter_area_allowed` (counter-candidate selection, `counter_plan.find_counter_candidates`) AND,
as of 2026-07-25, into `_training_area_allowed` (training-area selection, passed as `allow=` to
`best_training_area`). Tile-level `calculate_path` no longer answers any region-scale question in
the story bot.

**The measured effect on the training predicate** (`repro_counter_plan.py`, same Winona-era live
position, same candidate list, ONLY the predicate changed):

| `_training_area_allowed` | reachable flags over the 10 Winona candidates |
|---|---|
| before (`calculate_path`) | `[False × 10]` — every candidate rejected; KI-24 in the raw |
| after (`region_reach`) | `[True × 5, False × 5]` — incl. **Route 118 Electrike: reachable** |

**How it landed, and the test bug it exposed.** The first attempt FAILED
`tools/story-dev/repro_fodder_grass.py` case 5 (`L31 team in Fallarbor`: expected `SKIP GRIND`,
got `RELOCATE to ROUTE111 L19-22`) and was reverted rather than forced. Investigating the failure
showed the TEST was wrong, not the change — see 08-MISTAKES 2026-07-25 (partial mock). `_stand_at()`
patched only `modules.map.get_map_data_for_current_position`, while the predicate's `calculate_path`
branch read `modules.player.get_player_location`, which stayed live. So case 5 had been asserting a
verdict for a position it never simulated — it was really asking about `(PETALBURG_CITY, (7,6))`.

Proof the re-baseline was a TEST fix and not a behaviour change: with `_stand_at()` repaired and
`story_mode.py` **untouched**, the ORIGINAL `calculate_path` code also answers
`RELOCATE to ROUTE111`, and cases 1-4 are unchanged. Three independent sources agree Route 111 is
reachable from Fallarbor — `calculate_path` succeeds from `(14,7)`, `region_reach` measures 2 hops,
and `training_areas.py`'s own comment says so.

**✅ The sibling repro that went red is fixed — `tools/story-dev/repro_counter_plan.py`.** Its
primary assertions never failed; what failed was a non-vacuity scaffold asserting that a
deliberately WIDE type set contained at least one `False`. **That scaffold was relying on the
bug** — it existed only because the Winona set was vacuously all-`False` under the pre-KI-24
predicate, and it inverted the moment the false negatives went away (the wide set now returns
`[True × 25]`). Per user ruling 2026-07-25 the non-vacuity check MOVED to where non-vacuity now
genuinely lives: the Winona set itself, asserted to span BOTH branches, which is the property the
sort proof actually needs. The wide set is still sorted as a larger-sample check.

This was the SECOND test in one day found to be asserting something that depended on a defect
(case 5 was the first) — see the 08-MISTAKES pattern entry for the shape and the prevention rule.

**‼ But the cost model I assumed is wrong, and the measurement says so.** Measured hops from
ROUTE120 on the Winona-era save:

| target | hops |
|---|---|
| FORTREE_CITY | 1 |
| ROUTE119 | 2 |
| **LILYCOVE_CITY** | **2** |
| **ROUTE118** (the real Winona answer) | **3** |
| MOSSDEEP_CITY | 4 |
| PACIFIDLOG_TOWN | 10 |

I expected "the answer is a handful of hops, the far cities are many". **Lilycove is CLOSER than
Route 118 by this metric**, and Mossdeep is one hop further. Because a single ROM connection can
span an entire sea route, uniform 1-hop weighting compresses "same landmass cluster" (1-4) and
only separates the genuinely far-flung (Pacifidlog, 10).

**So hop count is a usable FILTER but not a usable RANK.** `max_hops=4` cuts Pacifidlog-class
targets while keeping the Fortree/119/118 cluster, and that is how it should be used — as a
sanity bound, with `counter_plan`'s existing criteria (type coverage → verified tile →
encounter rate → level fit) doing the actual ranking.

**Next, if finer granularity is ever needed (`#24-edgecost`):** weight each edge by the source
map's traversal length rather than a flat 1, or price travel in FRAMES so it composes with
`training_areas.estimate_frames_to_level`. Both are real work; neither is needed until hop
count demonstrably mis-ranks something.

**Also still open:** `KNOWN_GATES` holds only THREE hand-verified edges (`region_reach.py:81-91`) —
DEWFORD_TOWN↔ROUTE106 and DEWFORD_TOWN↔ROUTE107 (both `surf`), plus EVER_GRANDE_CITY↔VICTORY_ROAD_1F
(`waterfall`, added 2026-07-26 because Victory Road's L38-42 Hariyama otherwise ranked #1 as a
counter candidate). *(This line said "only one entry" until re-counted 2026-07-27.)* So
edges whose requirement cannot be derived from ROM data currently read as UNGATED — i.e. this
oracle now fails OPEN where the old one failed CLOSED. That is the safer direction for a
*planner* (a wrong "yes" costs a wasted walk that navigation will fail recoverably; a wrong "no"
is invisible) but it must be grown before this gates anything irreversible.

**Prevention rule:** when you introduce a cost metric, MEASURE it against known-good and
known-bad cases before trusting it to rank. "Reachable" was a boolean that hid a cost; "hops" is
a cost that hides map size. Each fix exposed the next assumption — check the numbers, don't
reason about them.

---

# Added 2026-07-27 — open issues found by a code audit, previously unlisted

## KI-25 — `_lead_best_matchup` is purely DEFENSIVE; it benches the only mon that can win (opened 2026-07-27, severity: HIGH)
- **Symptom:** before a type-countered fight the bot leads a mon that merely *survives* the
  foe's STAB, regardless of whether it can deal damage. Measured in bundle
  `20260726-231412`: P2 led **Whismur L15** into the Route 110 rival **13 times in one run**
  while **Marshtomp L24** sat in slot 2. P3 led Zigzagoon L16 with Grovyle L22 benched.
- **Cause (exact line):** `modules/story/early_game.py:1587`
  ```python
  best = min(slots, key=lambda i: (_incoming(party[i]), -party[i].level))
  ```
  `_incoming()` (`:1566-1583`) returns only the foe's worst-case STAB multiplier *against*
  the candidate. Nothing in the key considers the candidate's offence. The only capability
  filter, `_battler_slots()` (`:1651-1659`), requires merely *any* move with
  `base_power > 0` — not one that can hurt **this** foe.
- **‼ Live consequence — the Flannery segment does not do what its own comment says.**
  `plugins/custom_modes/story_mode.py:2519-2531`: the comment states the plan is *"a WATER
  lead (all four of her mons are 2x to Water)"*, but the call is
  `_lead_best_matchup(["Fire"])`, which ranks by *resisting* Fire. Water, Fire, Rock and
  Dragon all resist Fire equally (0.5×) and the tie-break is `-level` — so a higher-level
  Combusken/Numel leads instead of the Water mon the comment asks for.
- **Also:** a 1-HP Wonder Guard Shedinja scores `0.0` incoming vs Norman (Normal→Ghost) and
  is therefore *chosen*, then dies to Slaking's Faint Attack (Dark) — the model reads only
  the ace's STAB types, never movepools. Observed in P4, bundle `20260726-231412`.
- **NOT the old `train_team` lead-restore bug** (fixed 2026-07-26, repro still green): the
  matchup call runs *afterwards* and overrides the restore.
- **Workaround:** none. Design options and the tradeoffs are in `03-PUNCH-LIST.md`
  `#24-leadpolicy` — **needs a user ruling**, since benching a 4×-weak mon is sometimes
  exactly right.

## KI-26 — boss fights with no prep and no attempt cap (opened 2026-07-27; **MEASURED AND
## GENERALISED 2026-08-07** — severity: HIGH. This is `#24-whiteoutloop`.)

### ‼ 2026-08-07: this is the whiteout loop, and it is now quantified from stored logs
`#24-whiteoutloop` asked "show WHERE runs are when the loop starts, and do not attribute it
without that." Answer, from four stored batches (read-only, no emulator, `x4-runs/2026080*`):

**Every whiteout is preceded by `lost a battle at map (G,N) (defeat #K here; KO'd J of theirs
first)`. The whiteout machinery is not the bug — it fires and recovers every time. The bug is
that nothing stops the bot re-attempting a fight it keeps losing.**

| batch | defeats | at maps with NO `_prepare_for_fight` cfg | top 2 |
|---|---|---|---|
| `20260806-174746` | 554 | 283 (51%) | ROUTE110 111*, PETALBURG_GYM 103 |
| `20260806-142418` | 547 | 271 (50%) | PETALBURG_GYM 146, ROUTE110 108* |
| `20260806-103811` | 541 | 234 (43%) | PETALBURG_GYM 169, ROUTE110 91* |
| `20260806-055947` | 594 | 291 (49%) | ROUTE110 120*, PETALBURG_GYM 118 |
| **total** | **2,236** | **1,079 (48%)** | (* = no boss cfg) |

**Re-attempting mostly does not work.** Of 53 sequences with ≥3 defeats at the same map in one
batch, the best-KO trend is **FLAT in 37, improving in 15, worse in 1**. The premise that a lost
attempt is still training (Gen 3 keeps the XP) holds only ~28% of the time. Worst cases:

    L08 run1 LAVARIDGE_GYM  n=17  kos=[3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3]   <- perfectly flat
    L06 run1 ROUTE110       n=12  kos=[1,1,1,1,1,1,1,1,1,1,1,1]             <- perfectly flat
    L04 run2 PETALBURG_GYM  n=32  kos=[0,2,2,2,2,2,2,2,3,2,...,3,2]         <- 32 attempts

**‼ CORRECTION to this entry's own text below:** it says *"Route 110 and Wally are the only
combat segments without [prep]"*. **That is no longer true.** `_prepare_for_fight` is called at
exactly SIX sites — Roxanne `:2567`, Rustboro rival `:2658`, Brawly `:2724`, Wattson `:2837`,
Norman `:3026`, Winona `:3152`. **Gym 4 / Flannery (Segment 11d, `:2957`) has none**, and
LAVARIDGE_TOWN_GYM_1F is a top-4 defeat map in **4 of 4** batches (87/57/53/73). Mt. Chimney
(21) has none either. Line numbers in the original text below are also stale (`:744` → `:812`,
`:2335-2363` → `:2780-2808`).

**‼ AND THE PLATEAU DETECTOR CANNOT SAVE THE CONFIGURED FIGHTS EITHER.**
`_boss_plan_is_hopeless` (`:1250`) already implements exactly the right plateau test, but it
returns hopeless only when **BOTH** (1) the KO count has plateaued **AND** (2) no party mon has a
≥2.0-effective damaging move against `ace_types`. A party that HAS a super-effective answer and
is simply **underlevelled** fails test (2) for ever — which is Petalburg's 32-attempt run.

**FIX SHAPE (do not implement mid-batch; sandbox edits break running lanes):**
1. Give Flannery and the Route 110 rival real `_prepare_for_fight` cfgs. Biggest lever, reuses
   machinery that already exists and is already trusted for six other fights.
2. A cfg-independent cap keyed on **flat KOs, not raw attempt count** — so the maps nobody
   configured are still bounded.
   ‼ **This is what honours the warning already recorded below.** "P2 lost 13 times and then
   reached Fortree, so a cap at 6 would have killed a recovering run" is exactly right, and the
   KO series is the discriminator that entry lacked: a run whose KOs are CLIMBING is recovering
   (15 of 53) and must not be capped; a run flat at `[3]×17` is not, and never will be.

---

### Original entry (2026-07-27), retained
- **Symptom:** repeated identical losses at ROUTE 110 (34,56) with no adaptation. The code's
  own note records the worst case: `plugins/custom_modes/story_mode.py:744` — *"Measured
  worst case before this existed: 25 whiteouts on ROUTE110 in a single run."*
- **Cause:** Segment 9a (`story_mode.py:2335-2363`) is only
  `heal_in_pokemon_center` → `_lead_best_matchup([ace_type])` →
  `travel_route110_and_fight_rival()` → `_guard(...)`. **No `_prepare_for_fight`, no
  `train_team`, no attempt counter.** Every other combat segment has prep: Roxanne `:2122`,
  Brawly `:2279`, Wattson `:2377-2395`, Norman `:2581`, Winona `:2707`, and the Rustboro
  rival `:2177-2225` additionally has an escalating level floor and `RIVAL_MAX_ATTEMPTS = 3`.
  Route 110 and Wally (`:2366`) are the only combat segments without.
- **The only thing bounding it today** is `SURVIVAL_WHITEOUT_THRESHOLD = 3` (`:745`), which
  is a *wild-battle flee* heuristic, not a rival-attempt cap.
- **‼ Do NOT just add a cap.** In bundle `20260726-231412`, P2 lost there **13 times and
  then went on to reach Fortree** — a cap at 6 would have killed a recovering run. Adding
  prep needs a Route 110 training-grass tile, which is a game fact to probe or read from the
  decomp, never recall. See `03-PUNCH-LIST.md` `#24-route110cap`.

## KI-27 — hard hang at the Weather Institute, with the global watchdog itself wedged (opened 2026-07-27, severity: HIGH)
- **Symptom:** bundle `20260727-063751`, P3 run 1: `state=3 controllable=False`, position
  frozen at **ROUTE 119(32,1) (10,10)**, for **27 million frames / ~6.5 h** — and **not one
  STUCK dump fired in that entire stretch**, so the no-progress watchdog never saw it.
- **Last known stack:** `do_weather_institute` → `_ride_out_all_scenes`
  (`modules/story/early_game.py:5548`).
- **Partially mitigated 2026-07-27:** `_run_with_frame_budget()` now bounds the *run*
  (`story_mode.py:2866`), so the lane derails and the batch continues. **This truncates the
  symptom; it does not fix the hang, and it does not explain why the watchdog was silent.**
- **Next step:** wait for a post-fix batch to see whether it recurs and how often before
  spending time on it. Tracked as `#24-weatherinstitute-hang`.

## KI-28 — training LIVELOCKS that no progress detector can catch (opened 2026-07-27, severity: MED)
- **Symptom:** a run spins/heals indefinitely without reaching its level floor. Bundle
  `20260727-063751`: P1 run 7 = **19.9M frames** on Route 103 + Oldale heals; P2 run 35 =
  **13.4M frames** on Route 116.
- **Why KI-9's watchdog cannot help:** these produce real encounters, real battles and real
  healing trips — they are *busy*, just not progressing. A "nothing happened for N frames"
  detector is blind to them by construction. Only a resource budget catches them.
- **Contributing cause:** the training target is pursued regardless of whether local wilds
  can deliver it. Route 103's wilds are L2-3; Route 116's are L6-7.
- **Mitigated 2026-07-27** by the per-run frame budget (bounds the waste to one run).
  **Not fixed:** a target the local grass cannot deliver should be detected and abandoned.
  Tracked as `#24-grindconverge`.

## KI-29 — P4 broke the 1:1 losses:whiteouts canary twice (opened 2026-07-27, severity: LOW — watch item)
- **Symptom:** bundle `20260727-063751`, lane P4: run 1 logged **39 whiteouts vs 38 losses**,
  and run 8's sequence *opens* with a whiteout before any loss (`WLW`). Across three bundles
  the ratio had been exactly 1:1 in every other lane (no potion layer exists, so every loss
  becomes exactly one whiteout).
- **Most likely cause:** a whiteout event crossing a run boundary rather than poison damage —
  2 events out of 52. The per-run reset added 2026-07-27 (`reset_per_run_state`, which clears
  `_whiteout_pending`) may already cover it.
- **Action:** RE-CHECK on the first post-fix batch before investigating. Do not chase yet.

## KI-30 — a duplicate `Stone` badge is recorded on run 1 of every batch (opened 2026-07-29, severity: LOW)
- **Symptom:** in the newest bundle (`20260729-062040`), after correctly segmenting the
  cumulative badge log by batch, **run 1 of ALL FOUR lanes** shows `['Stone','Stone',
  'Knuckle', …]`. Every other run in every lane is clean — correct order, no duplicates, no
  gaps. It is exactly one extra `Stone`, only ever on run 1.
- **Cause: HYPOTHESISED, NOT PROVEN.** Most likely the batch-start boundary: at process
  start the emulator still holds the PREVIOUS session's save (Stone already earned) and the
  poll records it before the hard reset wipes the flags. `reset_for_new_run`'s adjacent-race
  branch (`badge_log.py`) makes the mode ADOPT main.py's boundary rather than count a second
  one, which is correct for the index but does not stop a pre-reset poll from recording.
- **‼ Do not fix on this hypothesis.** It has not been reproduced. The repro would be:
  start a batch from a profile whose save already holds BADGE01, and assert no badge is
  recorded before the first `[MAP]` of the new game.
- **Impact:** inflates run 1's badge count by one in every batch. It does not affect run
  grouping, gym order, or any other run. Harmless to the bot; misleading to an analyst.
- **Related:** the analysis-method trap that made this *look* far worse than it is —
  `run_index` restarts per process, so grouping a cumulative badge log by index across days
  merges batches. See `14-AGENT-PLAYBOOK.md` §2c.

## KI-31 — the fodder-grass gate compares the WRONG TWO QUANTITIES (opened 2026-07-29, severity: MED)
- **Symptom (user report 2026-07-29):** the bot trains in grass next to the objective even
  when those wilds are far below the team — "severely below level 5" — so XP per battle is
  near worthless. Norman is the 5th gym but sits in the STARTING region, which makes it the
  sharpest case.
- **Cause.** `_prepare_for_fight` relocates only when
  `local_max + FODDER_LEVEL_GAP < team_max_now` (`story_mode.py:1420`, `FODDER_LEVEL_GAP = 12`
  at `:715`). That compares the **wild** level to the **team** level — but the project's own
  measured model says XP per battle does not depend on the team at all:
  `xp_per_battle = 50.2 × wild_level / 7` (`training_areas.py`, calibrated against a real
  83-event probe). **XP is proportional to the WILD level, full stop.**
- **Measured cost** (real `TRAINING_GRASS` bands, team standing on Route 102 L3-5):

  | team level | relocates? | xp/battle here | best reachable band | speedup forgone |
  |---|---|---|---|---|
  | 10 | no | 35.9 | 8 | 1.6× |
  | 15 | **no** | 35.9 | 14 | **2.8×** |
  | 20 | yes | 35.9 | 22 | 4.4× |
  | 25+ | yes | 35.9 | 28 | 5.6× |

  The failure window is **teams at or below L17** — the gate needs `local_max + 12 <
  team_max`, so with L5 wilds it is False *at* 17 and first fires at **L18**. (Stated as
  "below 17" in the first draft; a repro assertion caught the off-by-one.) From L18 up it
  works correctly.
- **‼ DO NOT "just fix" THE CONSTANT.** The conservatism is DELIBERATE.
  `tools/story-dev/repro_fodder_grass.py` states it: *"WATTSON / ROXANNE / an early team ->
  UNCHANGED 'train locally' (the whole point of the conservative gap: proven-good prep must
  not move)"*. Teams at L10-17 are exactly Roxanne/Brawly/Wattson, so any fix moves prep that
  currently works.
- **‼ AND THE GOVERNING TEST CANNOT RUN ON THE DEV BOX.** `repro_fodder_grass.py` loads a real
  ROM + `saves/norman_done.ss1` and needs `mgba`. It is one of the 5 environmental failures
  here. **This change must be validated on the machine that runs the batches.**
- **‼ STATUS UPDATE 2026-07-29 (later): `xp_rate` IS NOW THE DEFAULT (user directive).**
  The user launches the bot by **double-clicking `install_sandbox.py`**, which cannot set an
  environment variable — so an env-var-only switch meant the intended rule never actually ran.
  Requiring a shell to get the intended behaviour is a broken interface, so the default was
  flipped. Every launch path (double-click, GUI, CLI, x4 lane) now agrees, and
  `POKEBOT_FODDER_RULE=legacy` is the documented way back for an A/B.
  ‼ **The governing test `repro_fodder_grass.py` STILL has not been run on any machine** — it
  needs a real ROM + save state. The arms provably differ only for teams at/below L17 and only
  at boss prep, and every run names its rule in the log header, so the blast radius is bounded
  and attributable — but this is a **user-directed default, not a validated one**. If early
  prep regresses, set `POKEBOT_FODDER_RULE=legacy`.
- **STATUS 2026-07-29 (earlier): the decision is a PURE, FLAGGED function.**
  `training_areas.local_patch_is_fodder()` holds both rules behind `FODDER_RULE`, which
  defaults to `"legacy"`. A repro proves the extracted legacy path reproduces the old inline
  expression across all 1,800 `(local_max, team_max)` combinations, and that the two rules
  disagree on **exactly L5-L17 and nowhere else** — so flipping the flag cannot disturb prep
  from L18 up. `tools/story-dev/repro_fodder_rule.py`.
  **To run the A/B — NO CODE EDIT NEEDED (2026-07-29):** set the env var
  `POKEBOT_FODDER_RULE=xp_rate` before launching. It normalises case/whitespace and REFUSES
  an unknown value loudly (a typo silently falling back to `legacy` would invalidate the
  experiment). Every run header prints `Story: training-relocation rule = …`, so a bundle is
  attributable after the fact.
  ‼ Do NOT hand-edit the constant on the batch machine: `install.py`'s self-healing runs
  `git checkout -- <drifted>` and can revert it.
  On the machine with `mgba`, also run `repro_fodder_grass.py` before and after and compare
  the WATTSON/ROXANNE rows — those are what the flag changes. Only then consider changing the
  default.
- **Proposed rule (implemented, OFF by default):** replace the gap test with a frame-saving
  test built from the existing pure model — relocate when
  `estimate_frames_to_level(mon, target, local_max) − estimate_frames_to_level(mon, target,
  better_hi)` is a large win (e.g. the better area at least HALVES the estimated grind, which
  by the model means `better_hi ≥ 2 × local_max`). This needs no new constant and no travel
  measurement.
  ‼ Travel cost remains **unmeasured** — `story_mode.py:576` says so explicitly — which is why
  the proposal is deliberately conservative and only fires on large wins.
- **Related:** `train_team` (`early_game.py:1738`) never consults `best_training_area` at all;
  its `grass` is a caller-supplied constant. Both belong to `#24-trainmap+`.

> 📦 **KI-32 moved to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-13** — ✅ FIXED 2026-07-29.

## KI-33 — a mid-battle rotation can still wedge the PARTY MENU (opened 2026-07-29, severity: HIGH)
- **Symptom:** the wedge KI-32 made visible. From `20260729-122709`, inside a Fortree Gym
  trainer battle:
  ```
  f1791402 [BATTLE] started
  f1793385 [PARTY] slot0 Marshtomp:L35 -> Castform:L25   <- rotation applied
  f1793407 [PARTY] slot0 Castform:L25 -> Marshtomp:L35   <- reverted 22 frames later
  f1799232 [PARTY] slot0 Marshtomp:L35 -> Castform:L25   <- applied again
  f1800001 [hb] state=3 (PARTY_MENU) controllable=False  <- wedged until stopped
  ```
  Apply → revert → apply, then a permanent `PARTY_MENU`. The run had already cleared five
  gyms and won 310 battles; this ended it.
- **This is the open half of KI-8.** KI-8 records the same
  `TurnAction.RotateLead → scroll_to_party_menu_index → while PARTY_MENU: press A` hazard and
  says the Story bot "sidesteps this path" because its trainer strategy never proactively
  rotates. **Something rotated anyway** — so either the strategy did rotate, or the after-faint
  chooser ran. Which one is NOT yet established.
- **Aggravating factor:** the mon rotated IN was **Castform L25**, against Winona's L29-33
  line-up, while **Marshtomp L35** was rotated out — the defensive-only lead selection of
  KI-25 choosing badly under pressure.
- **Next step (needs the emulator):** capture a save state at the wedge and drive
  `TurnAction.RotateLead` into a specific slot to establish whether the stall is in
  `map_battle_party_index`, the submenu default not being "SHIFT", or the after-faint chooser.
  KI-8's "Proven fix pattern now exists" note is the starting point.
- **Bounded, not fixed:** the per-run frame budget would have ended this run at 3.5M frames
  (it was at 2.78M when stopped), and KI-32 now makes it *diagnosable*. Neither prevents it.

## KI-34 — the after-faint chooser LIVELOCKS when its candidate filter and the game disagree (opened 2026-07-29, severity: HIGH)
- **User report:** *"noticed an error with I think p2 or p3 where they were training with a
  skitty and an Abra in the team in a double battle but had issues selecting the Abra."*
  Confirmed in P2 of bundle `20260729-172342`, and **this is the first production catch by the
  KI-32 in-battle stall fix** — without it the log would again have been silent.
- **Evidence (71 in-battle STUCK dumps, f652,238 → f862,238 = 210,000 frames):**
  ```
  game_state=3 (PARTY_MENU)  controllable=False
  battle: active=True  instr=BattleScript_FaintedMonTryChoose
  battle_text='MARSHTOMP fainted!'
  party=['Marshtomp L27 0/76', 'Skitty L15 41/41', 'Poochyena L12 0/32', 'Abra L7 21/21']
  -> handle_battle @ battle_handler.py:264
  -> handle_fainted_pokemon @ battle_handler.py:532 / :537
  ```
- **It is a LIVELOCK, not a hang.** Across all 71 dumps the **party never changes** — no
  replacement is ever sent out — but the menu state *cycles*:
  `Task_ReturnToChooseMonAfterText + Task_PrintAndWaitForText` ×57,
  `Task_HandleChooseMonInput` ×10, `Task_HandleSelectionMenuInput` ×3, and the stack alternates
  between the two `yield` sites at `:532`/`:537`. The bot is pressing buttons and the game is
  responding; the *outcome* never occurs.
- **‼ Its 6,000-frame bound does not bound anything.** `handle_fainted_pokemon` ends with
  `if frames > 6000: return` — but the dispatcher re-enters it with `frames = 0`.
  210,000 / 6,000 ≈ **35 re-entries**. This is verbatim the playbook rule
  *"bound the OUTCOME, not just the frames — a bounded loop re-entered by its dispatcher is
  still infinite."*
- **Two candidate mechanisms — NOT yet distinguished, and the dump cannot separate them:**
  1. **`alive_slots` is EMPTY.** If this is a DOUBLE battle whose actives are Skitty(1) and
     Abra(3), then `_on_field = {1,3}`; slots 0 and 2 are fainted, so the KI-18 exclusion
     leaves **no candidate at all**. Every branch then either dismisses text or walks the
     cursor, and A is never pressed — matching "issues selecting the Abra" exactly.
  2. **Text-branch starvation.** The `Task_PrintAndWaitForText` /
     `Task_ReturnToChooseMonAfterText` branch is checked FIRST and was active in 57 of 71
     samples, so it can starve the `cursor not in alive_slots → "Down"` branch: A dismisses
     the text, the cursor is still on a fainted slot, A re-selects it, the text returns.
     KI-17's `post_gap = 24` was meant to prevent this; 24 frames may be insufficient.
- **‼ INSTRUMENTED 2026-07-29 — the next occurrence will name its own cause.**
  `handle_fainted_pokemon` now emits, via `debug_logger.event(category="BATTLE")`:
  * on entry — `[FAINT-CHOOSER] alive_slots=… on_field=… party=[(slot, species, hp)…]`, with an
    explicit **`‼ NO ELIGIBLE REPLACEMENT — cannot succeed`** when `alive_slots` is empty. That
    one line separates mechanism (a) from (b).
  * on give-up — `[FAINT-CHOOSER] GAVE UP after N frames … presses={…} cursors_seen=[…]`.
    The press histogram is what distinguishes *pressing the wrong thing* from *pressing
    nothing* (playbook §7); the state trace alone cannot.
  Counted per iteration, emitted once, so it cannot flood a log.
- **‼ DIAGNOSED 2026-07-30 by that instrumentation — mechanism (b), and (a) is REFUTED.**
  Overnight batch `20260730-062818`, 7,539 chooser entries and 3,978 give-ups:
  * **`alive_slots` was NEVER empty — 0 of 7,539.** So the KI-18 on-field exclusion is NOT
    starving the candidate set. **Mechanism (a) is dead.**
  * **`presses={'A': 289}` — A and NOTHING ELSE**, every time. No `Down`, no `B`, no `(none)`.
  * **`cursors_seen=[1]` — a SINGLE position for the whole 6,002 frames**, and that position
    **is in `alive_slots`**. The cursor is parked on a living, eligible mon.
  So: the cursor is already correct, the bot presses A ~289 times, and the menu never advances.
  It is not choosing wrongly and not failing to find a candidate — **its A-presses are not
  being accepted**, and the printer-task branch (`Task_PrintAndWaitForText` /
  `Task_ReturnToChooseMonAfterText`) keeps re-arming, so it never reaches any other branch.
  KI-17's `post_gap = 24` is insufficient for this case.
- **Where:** `MAUVILLE CITY(10,0)` — the Mauville Gym — in **3,975 of 3,975** located give-ups,
  and `on_field` carries TWO slots, i.e. a **DOUBLE battle**. Exactly the user's original report.
- **‼ Scale, and why it matters more than it looks:** P3 alone burned **23,857,950 frames** in
  3,975 give-ups (**~7.8 complete runs' worth**) — and P3 completed only **5 badge-earning runs
  overnight against P2's 19.** The livelock, not difficulty, is what cost that lane its night.
  P1 1, P2 0, P4 2 — it is **99.9% concentrated in P3/Treecko**, because Treecko has no Ground
  answer to Wattson, loses repeatedly, and every loss is another after-faint chooser roll.
- **‼ ROOT CAUSE FOUND 2026-07-30 — USER OBSERVATION + CODE, and it invalidates my reading of
  my own instrumentation.** The user, watching the screen: *"the bot is selecting a live pokemon
  in the pokeparty, but its one that is already in the field (cannot select an already active
  pokemon to swap out)"*.
  That is impossible if `alive_slots` is correct — and it is correct, **in its own index space.
  The comparison is not.** There are TWO party index spaces:
  * **regular party order** — what `get_party()` returns;
  * **in-battle party-menu order** — what the party MENU uses, which diverges from the regular
    order once mons have been switched in and out. `BattleState.map_battle_party_index()`
    (`battle_state.py:332`) exists solely to convert between them, and its docstring says so:
    *"the order in the party menu might be different from what `get_party()` returns so we'd
    have to scroll to a different index."*

  `handle_fainted_pokemon` uses BOTH SPACES AND COMPARES THEM DIRECTLY:
  | line | value | space |
  |---|---|---|
  | `battle_handler.py:474` | `party_in_menu = get_party()` | **regular** |
  | `battle_handler.py:~504` | `alive_slots` built by enumerating that party | **regular** |
  | `battle_handler.py:530` | `cursor = get_party_menu_cursor_pos(...)["slot_id"]` (reads `gPartyMenu.slotId`) | **in-battle menu** |
  | `battle_handler.py:548-549` | `cursor in alive_slots` / `cursor not in alive_slots` | **‼ mixed** |

  ‼ **The same function already knows better**: its PRIMARY path maps correctly at
  `battle_handler.py:443-444` (`if index_needs_mapping: new_lead_index =
  battle_state.map_battle_party_index(new_lead_index)`). Only the RECOVERY SWEEP — the loop that
  actually wedges — skips the mapping.
- **Why this explains every observation at once:** once the orders diverge (i.e. after switches
  and faints — exactly a double battle late in a fight), menu-slot *n* is a different mon than
  party-slot *n*. The sweep concludes "cursor is on a living, eligible mon", presses A, and the
  game **refuses because that mon is on the field** — which re-arms
  `Task_PrintAndWaitForText`, so the loop takes the dismiss-text branch again. Hence exactly
  what was logged: `presses={'A': 289}`, **cursor static**, and a `cursor in alive_slots` test
  that was TRUE and meaningless. It is worst in P3 because that lane faints most, so its orders
  diverge most.
- **‼ LESSON (logged in 08-MISTAKES):** I instrumented the VALUES but not their UNITS. Two
  integers from different coordinate systems compared as if interchangeable — and the log I
  added made the wrong comparison look verified.
- **FIXED 2026-07-30.** Two changes in `modules/battle_handler.py`:
  1. **Convert before comparing.** `alive_slots_menu = {map_battle_party_index(i) ...}` and every
     cursor test now uses the MENU-order set — matching what the primary path and
     `battle_action_selection.py:124/199` already did. The entry log prints BOTH sets with their
     units and flags `[orders DIVERGE]`.
  2. **Bound the OUTCOME, not the frames.** `FAINT_CHOOSER_GIVEUP_LIMIT = 3` per battle
     (counter reset in `handle_battle`); on exceeding it the run gets a RECOVERABLE derail via
     `battle_fault.request_mode_recovery()`, which makes `handle_battle` and `BattleListener`
     short-circuit so `StoryMode` claims it and the endless loop starts the next run.
     It never RAISES from battle code — on this flat controller stack that would reach
     `main_loop` and force Manual.
- **Repro:** `tools/story-dev/repro_faint_chooser_index_space.py` — builds a diverged battle
  party order and proves the OLD test calls menu slot 1 selectable while the NEW test correctly
  rejects it as on-field: the user's observation, reproduced as arithmetic.

## KI-36 — the per-run frame budget CANNOT fire while a battle handler is on the stack (opened 2026-07-30, severity: HIGH)
- **Symptom:** in `20260730-062818`, P3 run `235303` ran for **25,632,106 frames** — five times
  the 5,000,000 cap — and the batch reported **`frame-cap=0`**. The budget never fired.
- **Cause, and it is a defect in the KI-27 fix itself.** `_run_with_frame_budget` is a
  **generator wrapper**: it can only check the budget when the story generator is stepped. But
  the controller stack is **FLAT** (`02-ARCHITECTURE.md`) — `main_loop` advances only the TOP
  generator. In that run the stack was
  `['StoryEndlessResetMode.run', 'TrainerApproachListener.handle_trainer_approach', 'BattleListener.fight']`
  in **8,022 of ~8,200 samples**, so `BattleListener.fight` was on top and the story generator —
  with my budget wrapper — **was never advanced at all.**
- **‼ So the budget is blind to precisely the failure class it was built for.** Every wedge we
  have (KI-17, KI-33, KI-34) is inside a battle handler.
- **Why KI-32's stall dumps still worked:** `modules/debug_logger.py` is driven by a **per-frame
  listener** from `modules/main.py`, not by a generator, so it keeps sampling regardless of what
  is on top of the stack. We therefore have **diagnosis without termination**.
- **PARTIALLY FIXED 2026-07-30 — a net, not the complete fix.** `modules/debug_logger.py`
  already ticks every frame as a per-frame LISTENER (exactly why its stall dumps fired when the
  budget did not), so the thing that NOTICES a wedge now also ENDS one: at
  `_BATTLE_STALL_FAULT_AFTER = 60_000` frames of byte-identical in-battle state (>3x the dump
  threshold, ~16 min at 60fps) it calls `battle_fault.request_mode_recovery()` once.
  LIMITATION, STATED: this only works while **debug logging is ON**. It is a net for batch runs
  (which always enable it), not a general watchdog. **A stack-independent budget in `main_loop`
  remains the complete fix and is still OPEN.**
- **Relationship to existing entries.** Same family as **KI-33** (Fortree, 2026-07-29) and
  **KI-17** — all three are `BattleScript_FaintedMonTryChoose` +
  `Task_ReturnToChooseMonAfterText`/`Task_PrintAndWaitForText`. KI-17 is currently marked
  ✅ FIXED; **it is not fixed for the multi-faint case.** KI-33's open question ("strategy or
  after-faint chooser?") is hereby **answered: the after-faint chooser.**
- **Not fixed.** Bounded only by the per-run frame budget, which would end the run at 3.5M.

## KI-35 — a SUCCESSFUL run now uses 87% of the per-run frame budget (opened 2026-07-29, severity: MED)
- **Symptom:** the single run in `20260729-151635` **completed** — six gym leaders beaten
  including Winona (`FortreeCity_Gym_EventScript_WinonaDefeated` + badge fanfare), 462 battles
  won — and consumed **3,058,007 frames**. `MAX_FRAMES_PER_RUN = 3_500_000`.
  That is **14% headroom**, not the "~1.5x" its own comment claims (written when the deepest
  run was ~2.24M).
- **Risk:** the in-run frame budget added 2026-07-27 (KI-27 fix) will start terminating
  **successful** runs and reporting them as wedged. A slightly unluckier run — a few more heal
  round trips, one extra failed gym attempt — trips it.
- **Why runs got longer, measured in the same log:** **78 heal round trips** in one run
  (Route 116↔Rustboro ×34, Dewford↔Granite Cave ×29, Route 117↔Mauville ×15). With no potion
  layer every HP dip is a full walk to a Poké Center and back. This is `#24-provisions`, and
  it is now the dominant cost of a run — more than any gym's difficulty.
- **✅ FIXED 2026-07-29: `MAX_FRAMES_PER_RUN` 3,500,000 → 5,000,000.** Restores ~1.6x over the
  deepest observed run (3,117,110), re-deriving the constant from measured data rather than
  guessing — the same "~1.5x the deepest completed run" rule the original comment used.
  ‼ Raising it is cheaper than it used to be: since KI-32 an in-battle wedge produces a STUCK
  dump after 18,000 frames, so the cap is no longer the only thing that NOTICES a hang, just
  the thing that ENDS one — a wedge is now diagnosed ~270x sooner than the cap fires.
  Expect to raise it again as content grows; re-derive from the deepest COMPLETED run.


## KI-37 — a listener above the mode can STARVE it, so a handed-over battle fault is never claimed (opened 2026-07-30, severity: HIGH — CAUSED BY THE KI-34 FIX)
- **Symptom:** user log `20260730-081347` (`Story (DEBUG - RESET)`, build `4f1e02f9`).
  `handle_fainted_pokemon` did its job — 3 give-ups, then a correct hand-over at f1,797,401:
  `[FAINT-CHOOSER] handing a recoverable derail to the mode`. **Nothing claimed it.** The run
  then sat at `state=3 controllable=False` on ROUTE 117 for **1,182,000 frames** until the user
  stopped it by hand. KI-36's 60,000-frame net ALSO fired and was ALSO unclaimed.
- **Contrast, same build, sibling log `20260730-074518` (`ENDLESS RESET`):** the identical
  hand-over was claimed **one frame later** — `f902223 [STORY] DERAIL #1: Story: battle handler
  gave up — after-faint chooser could not send a mon out after 3 attempts (KI-34)`. So the
  channel works; something specific starved the mode in the other run.
- **Cause.** `TrainerApproachListener.handle_trainer_approach` was:
  ```python
  while get_global_script_context().is_active:
      context.emulator.press_button("B")
      yield
  ```
  An **unbounded loop with no fault check**. When a battle wedges, the trainer script never
  clears, so this listener sits on TOP of the controller stack pressing B for ever — and the
  MODE, the only thing that can consume the fault and derail, is never advanced. The stack at
  the wedge was `['StoryDebugResetMode.run', 'TrainerApproachListener.handle_trainer_approach']`
  with **no battle handler at all**: the fault had already short-circuited it, exactly as
  designed.
- **‼ `BattleListener` ALREADY HAD THIS EXACT GUARD**, ~110 lines above in the same file, with a
  comment naming the identical hazard: *"this would press B forever while the MODE — the only
  thing that can recover — is starved of frames."* The sibling listener simply never mirrored
  it. Third instance of that shape (KI-18's driver, KI-34's recovery sweep, now this).
- **This is a deadlock the fix created**, and `battle_fault.py`'s own docstring predicted it:
  *"An unconsumed fault would be far worse than a Manual drop."*
- **✅ FIXED 2026-07-30:** `handle_trainer_approach` now returns when `battle_fault_pending()`,
  popping back to the mode. Asserted in `repro_faint_chooser_index_space.py`.
- **‼ FOLLOW-UP, STILL OPEN:** audit **every** listener that can sit above the mode for the same
  omission, and bound their loops. A per-frame, stack-independent recovery (KI-36's complete
  fix) would make this class impossible rather than requiring each listener to remember.

## KI-38 — 3 residual after-faint give-ups remain; the text fallback has now EARNED its place (opened 2026-07-30 — ⛔ SUPERSEDED: see the REOPENED KI-38 entry further down; it was MITIGATED, not fixed, and is the dominant battle hang)
- **The KI-34 index fix works and the diagnosis is CONFIRMED.** `[orders DIVERGE]` appears in
  both logs with concrete evidence — `alive_slots=[1, 2, 3](party-order) -> [0, 2, 3](menu-order)`
  — and give-ups fell from **3,975 in one lane to 3 per run.**
- **But 3 remain**, with a new press profile: `presses={'Down': 3, 'A': 273}` and
  `cursors_seen=[0, 2, 3, 7](menu-order)` against `alive_slots=[2](party) -> [0](menu)` in a
  FOUR-mon party. Two things are unexplained and the data cannot separate them:
  1. **cursor 7 in a 4-mon party** — almost certainly the party menu's CANCEL entry. If the
     cursor walks past the target onto CANCEL, `"Down"` may never bring it back.
  2. **273 A-presses with the cursor reportedly reaching 0**, the mapped target — so either the
     target is still wrong, or A on it is being refused for a reason we do not read.
- **‼ The user's proposed TEXT-DETECTION FALLBACK (`#24-menutext`) is now justified by
  evidence**, exactly as predicted when it was deferred: reading the game's own refusal message
  distinguishes "wrong target" from "right target, refused" and is strictly more general than
  any index reasoning. **The exact string must be read from the pokeemerald decomp, never
  recalled.**
- **Also worth instrumenting:** log the cursor AND the target on each press, not just the sets,
  so a press can be attributed to a position.

## KI-39 — ✅ CORRECTED AND LARGELY RESOLVED 2026-07-31 — the ORIGINAL (refuted) entry now ALSO moved to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-14)

⛔ **Until 2026-08-14 this file kept the 178-line ORIGINAL entry — whose stated cause the archive
explicitly refutes — while the CORRECTION lived in the archive.** A reader absorbed the wrong
analysis in full before reaching this stub. Backwards from the archive rule: the current-state
file keeps the truth, the archive keeps the history. Both halves are now in
`31-KNOWN-ISSUES-ARCHIVE.md`, refutation alongside original.


Archived 2026-08-13 to keep this current-state file inside its 3,000-line R3 budget. Nothing was
deleted — the full correction and its diagnosis are in the archive.

---

## KI-41 — The Mauville→Route 112 corridor is sealed by a ROCK SMASH rock the planner treats as permanent (2026-07-31)

**Measured** from `rocksmash_taught.ss1` (Mauville 32,15), `probe_journey_walls.py`:
ROUTE111 column-by-column reachability, y from 139 (south, next to Mauville) northward —

```
x=17  ##########.........######.....#####..#............   last reachable y=102
x=18  #########..........#######....#####..#............   last reachable y=102, y=101 BLOCKED
x=19  ##########......#..##..####...#########...........   last reachable y=101, y=100 BLOCKED
x=20  ...####.###.#..##.###..##.###.#########...........   last reachable y=101, y=100 BLOCKED
```

The intermittent bands further south are the corridor's **one-way ledges** (they only
descend, so northbound approach is fragmented); the hard floor at **y≈100–101** is the
twin-rocks choke. `modules/story/early_game.py`'s `travel_lavaridge_to_petalburg` docstring
already names it: *"smash the twin-rocks choke from the NORTH side … column 18 needs only the
(18,101) rock"*, and notes the rocks **RESPAWN on map reload**.

**Consequences**
* ROUTE112 is **0/76** sampled tiles reachable from Mauville. FIERY_PATH's only two doors are
  ROUTE112 (11,36) and (22,10), so **Fiery Path is unreachable from Mauville** until that
  rock is smashed — and Fiery Path's Machop is the counter `#24-counters` names for Norman.
* The story only gets past it because `travel_to_fallarbor` / `travel_lavaridge_to_petalburg`
  hand-code a `_smash_rock` at exactly that coordinate. **Nothing generic does.**

**Why the planner cannot see it.** `calculate_path` models a Rock-Smash rock via
`dynamic_collision_flag` / `dynamic_object_id`, i.e. as an obstacle that *is* impassable right
now. That is CORRECT — the bot genuinely cannot walk through it — but it means every generic
"can I get there?" answer is a NO that a single field-move would turn into a YES.

### ‼ KI-41 — FIXED 2026-07-31 (same day). `#24-smashroute`.
`modules/story/obstacle_clearing.py` reads the ROM's own object events, keeps the ones whose
script is a known field-move obstacle, and offers only those the bot can both REACH (an
adjacent tile pathable right now) and CLEAR (party move + badge). Hooked into
`early_game._navigate_riding_out` **before** its fail-fast guard — that guard is right that
"the field is idle and we have not moved, so retrying cannot change the result", but smashing
the rock CHANGES THE WORLD, which is the premise it tests.
**Live A/B** (`story_harness.py --driver smashroute`, `rocksmash_taught.ss1`): OLD arm
`arrived=False map=MAUVILLE_CITY`; **NEW arm `arrived=True map=FIERY_PATH`, 45,305 frames.**
Only Rock Smash is actionable; Cut is known-but-unvalidated and **Strength is excluded on
purpose** (a boulder is PUSHED, not removed, so the success test can never fire).
Repro: `repro_obstacle_clearing.py`. ‼ It shipped with a re-entrancy bug — `clear_obstacle`
→ `_smash_rock` → `_navigate_riding_out` runs through the hook itself — caught by
`repro_smashrock_battle_wedge.py` going from sub-90s to >500s. See `08-MISTAKES` 2026-07-31.

**Original shape of the fix (as written before it was built).** When a journey leg fails, ask whether a smashable rock
(or a cuttable tree) sits on the blocked corridor, and if the party has the move and badge,
clear it and re-plan. `_smash_rock` already exists and is idempotent. The rock coordinates
must come from map data or the decomp, never from memory. ‼ Bound it: a rock that respawns
must not become an infinite smash-and-retry loop.

## KI-42 — The Norman counter sits EXACTLY on the `COUNTER_MAX_HOPS` boundary (2026-07-31)

Measured with `region_reach.hops_to`, the oracle `_counter_area_allowed` actually calls:

| from | to FIERY_PATH | verdict at `COUNTER_MAX_HOPS = 8` |
|---|---|---|
| PETALBURG_CITY (where the Norman ladder fires) | **8 hops** | ALLOWED — with **zero margin** |
| ROUTE102 (`prenorman_fodder_grind.ss1`) | 7 | allowed |
| MAUVILLE_CITY (`rocksmash_taught.ss1`) | 3 | allowed |

So the entire `#24-counters` chain for Norman — the ~72%-of-derails item — depends on a
distance that is exactly at its own limit. **One extra hop anywhere in the map graph and the
candidate is filtered out silently**, with no error: `best_huntable()` simply returns nothing
and the ladder reports "no huntable counter candidate". That is the KI-24 failure shape (a
false negative that gives no reason at all), and nothing currently warns about it.

‼ **Do NOT just raise the constant.** It was already raised 4 → 8 on measurement, and the
bound is what keeps the cost model from ranking endgame maps first (Hariyama @
VICTORY_ROAD_B1F L38-42 prices at ~0 to train and ranks #1 the moment the map is called
reachable). Any change needs the same measurement that justified 8.

**Cheap mitigation worth doing:** have `_counter_area_allowed` LOG when it rejects a
candidate for distance and by how much (`why_unreachable` already returns
"reachable but N hops away (limit M)"). A silent filter at exactly the boundary is the
thing that will waste the next debugging session.

---

## KI-43 — `_navigate_when_ready`'s escape hatch is budgeted EXACTLY like the watchdog, so it is dead code (2026-07-31, severity: HIGH — ROOT CAUSE FOUND, FIX NOT YET APPLIED)

**This is the `global watchdog 9 → 143` caveat from the batch3 result, investigated.** The
handoff's own hypothesis — *"runs travel much further now and long journeys trip the
18k-frame no-progress watchdog"* — is **WRONG**. It is a hard regression introduced by
`fea2bb19` (`#24-journey` part 3), and it has nothing to do with journey length.

### The mechanism

`_navigate_when_ready` (`modules/modes/util/global_navigation.py`) wraps every `navigate_to`
call and waits for the overworld instead of letting `navigate_to` raise:

```python
while get_game_state() is not GameState.OVERWORLD or not player_avatar_is_controllable():
    waited += 1
    if waited > _MAX_NON_OVERWORLD_FRAMES:
        break      # "so a genuine softlock still surfaces rather than yielding for ever"
    yield
```

```
_MAX_NON_OVERWORLD_FRAMES = 60 * 60 * 5   = 18,000    (global_navigation.py:90)
StoryMode global watchdog: _stall_frames >= 18,000     (story_mode.py:2002)
```

**The same number.** The wrapper presses no buttons and changes no state, so map, coords,
game state, progress signature and `context.message` stay frozen while it waits — which is
exactly the watchdog's stall signature. The watchdog fires ON frame 18,000 (`>=`); the break
needs frame 18,001 (`>`). **The watchdog wins by one frame, every time.** The docstring's
promise that "a genuine softlock still surfaces" is unreachable code.

The constant is not new — but at `289d1710` it guarded only the outer `navigate_to_anywhere`
loop's `get_game_state() is not OVERWORLD` wait, which is rare. `fea2bb19` added the far
stickier `not player_avatar_is_controllable()` to it and put it on EVERY `navigate_to` call.
That is what made the collision reachable.

### The measurement (stored logs only — no emulation was re-run)

| | baseline `289d1710` | batch3 `3875843c` |
|---|---|---|
| `global watchdog` (stdout, deduped — see below) | **5** | **72** |
| RUSTBORO_CITY_MART purchases completing cleanly | **33 / 33** | **0 / 36** |

Where the 72 fire — **not** on long journeys:

| trips | map | stage | fires immediately after |
|---|---|---|---|
| 35 | `RUSTBORO_CITY_MART` | 3: Woods & Cut | `bought Poké Balls` |
| 31 | `LAVARIDGE_TOWN` | 13: Gym 5 — Norman | `BADGE: Heat Badge` |
| 3 | `ROUTE112` | 11 | — |
| 1 | `ROUTE116` | 3 | — |

Both clusters are **stationary wedges at a step boundary**, not travel.

### The Rustboro cluster, in full

`early_game.py:2171` restocks balls, then `:2174` navigates to the grass. The restock buys in
batches of ten to farm the free Premier Ball each purchase gives, and each batch re-enters
`buy_poke_balls`, which opens with `_navigate_riding_out(mart_map, approach)` while the avatar
is still settling out of the shop UI and is therefore **not controllable**. The wrapper sits
on that for the full 18,000 frames and the watchdog derails the run.

Proof it is the *second* purchase, from the ball-count transitions:

```
baseline  (0→10) ×17   (11→21) ×17   (22→32) ×16      three purchases, chained
batch3    (0→10) ×13   (1→11)  ×23   — and NOTHING ELSE, 36 of 36 are FIRST buys
```

**So the cost is not only the burned frames.** Every restock now buys 10 balls instead of 30,
loses 2 free Premier Balls, and spends a derail out of the budget that protects against
genuine stuck loops.

### ‼ Instrument note — `global_watchdog` in `summary.json` is DOUBLE-COUNTED

`summarize_lane` counts over `stdout + debug logs`, and a watchdog derail is written to
**both** (console line, and `[STORY] DERAIL #N:` in the debug log). So the headline
`9 → 143` is really **5 → 72**. This is specific to the watchdog: `GAVE UP` appears only in
debug logs and `BADGE:`/`losses` only in stdout, so those canaries are NOT inflated. Do not
"fix" this by halving — dedupe the source.

### Reproduce

`tools/story-dev/repro_watchdog_budget_collision.py` — no emulator, reads both constants from
source. **RED on purpose** until the cap is lowered.

### The fix, and why it is not applied yet

Lower `_MAX_NON_OVERWORLD_FRAMES` for the wrapper to something sized for the transient it was
built for (a battle transition clears in a few frames; ~600 frames / 10 s is generous), so
`navigate_to` gets to raise its own honest error and `_navigate_riding_out` spends a retry on
it — the pre-`fea2bb19` behaviour, but without the spurious failure `fea2bb19` fixed.

**NOT APPLIED 2026-07-31:** batch `20260731-201554` was mid-flight and the runner restarts
crashed lanes, so an edit to `sandbox-pokebot/` would have been imported by a restarted lane
and contaminated the batch. Apply after it lands, then prove with a live A/B (the Rustboro
restock is a cheap repro site: it fails 36/36 today).

Related: **KI-40** (a *different*, earlier watchdog spike, attributed to the KI-34/35/36/37
work). The `289d1710` baseline shows only 5 fires, so KI-40's regression is not what this is.

---

## KI-44 — Counter training cannot REACH its training grass: ROUTE102 is unwalkable from ROUTE103 (2026-07-31, severity: HIGH — this is now the counter chain's blocker)

**Measured**, batch4 `x4-runs/20260731-201554` (commit `92d220d5`), 7 of 7 attempts:

```
Story: training the counter — Machop L15 -> L21 (team is L35, est 222115 frames).
Story: counter training failed (UnreachableDestinationError('Could not reach (9, 2) on
  MapRSE.ROUTE102: the field is idle and we are still at (45, …), so retrying cannot change
  the result (Cannot reach PETALBURG_CITY: it is not walkable from ROUTE103, and none of the
  6 candidate warp route(s) start at a tile that can be walked to from here
  (tried: OLDALE_TOWN(…)×4, PETALBURG_CITY(…)×2).).')) — continuing untrained.
```

6 of 7 are this exact error; the 7th is a whiteout abort. **Zero counters were trained**, so
the Machop still fights Norman's L28-31 team at L15-16 — the same state as batch3, which is
why batch4's badge funnel is flat at every rung (Heat→Balance 77% → 83%, z = 0.52).

‼ **EXPOSED, NOT CAUSED, BY `affordable_training_target` (`1c4b183d`).** Before that fix the
gate refused to train at all, so the bot never attempted the journey and this failure could
not appear in any log. Do not "revert the training fix" — the fix is correct and is doing its
job (`training … rejected` went 4 → 0, the affordable target fires 7×). The blocker simply
MOVED from the budget to the travel, exactly one step further down the chain.

**What the error says.** The bot stands on **ROUTE103** and wants **ROUTE102 (9,2)**.
`_walk_is_possible` says no for the direct route, and all six warp candidates it was offered
(4× OLDALE_TOWN, 2× PETALBURG_CITY) are judged unwalkable from where it stands. Route 103
connects to Oldale Town by an ordinary map CONNECTION, so "no candidate is walkable" is the
suspicious part — this smells like KI-24's `calculate_path` unsoundness at region scale
rather than a genuinely sealed route.

**Do not fix by raising retries.** The message already contains the fail-fast reasoning —
*"the field is idle and we are still at (45, …), so retrying cannot change the result"* — so
retrying is known-useless here. Establish first whether ROUTE103 → OLDALE_TOWN → ROUTE102 is
genuinely walkable from that tile with a live probe from the ACTUAL captured position (the
2026-07-31 lesson: validating travel from an easy starting position and shipping it as done
is already in `08-MISTAKES.md`), plus a control tile that DOES path.

Related: **KI-24/24b** (`calculate_path` unsound at region scale; `_training_area_allowed`
still uses it), **KI-39 CORRECTED**, **KI-43** (fixed).

### KI-44 — ROOT CAUSE FOUND AND FIXED 2026-08-01 (live-probed; awaiting a batch for the outcome proof)

**It was never a routing bug.** `train_counter` used `cfg["grass"]` — the **BOSS's** patch —
so a Machop caught in FIERY_PATH was sent to Norman's `PETALBURG_TRAINING_GRASS =
(ROUTE102, (9, 2))`. Two independent faults; the log only ever showed the first.

| | |
|---|---|
| 1. it cannot get there | 6 of 7 stranded on ROUTE103 (45, 7) — eight maps from the catch |
| 2. it would not be worth going | **ROUTE102's land wilds are L3-4** |

Fault 2 was invisible in every log and is arguably the worse one. Probed 2026-08-01
(`tools/story-dev/probe_counter_grass.py`, reads the ROM's own encounter tables):

| map | land wild levels | |
|---|---|---|
| **ROUTE102** | **3-4** | what Norman's cfg used |
| FIERY_PATH | 14-16 | where the counter is caught |
| ROUTE112 | 14-16 | adjacent |
| JAGGED_PASS | 20-22 | adjacent |

`story_mode.py:739` already described this exact patch as *"Route 102 at L4 ... ~25 xp a
kill, i.e. never"* — the pathological case `FODDER_LEVEL_GAP` was invented for. So even a
perfect journey would have bought a near-worthless grind.

‼ **AND THE OBVIOUS REPAIR IS ALSO WRONG.** "Train where you caught it" picks FIERY_PATH,
which is in `NO_RETURN_GROUNDS`: reachable and exitable (fine for catch-and-leave hunting)
but **the heal leg back to Lavaridge FAILS**, and a training loop needs that third leg.
ROUTE112 is there for the same measured reason (Lavaridge→door OK at 60 waypoints,
door→Lavaridge FAILS) and JAGGED_PASS cannot even path within itself. There was simply **no
legal training ground** for a counter caught in Fiery Path — a structural hole in the chain,
not a wrong constant.

**THE FIX** — `counter_hunt.counter_training_ground()`. Ask `best_training_area`, the picker
the rest of the bot already uses: it refuses no-return grounds FIRST, applies the winnability
guard, honours the live reachability predicate, and prefers the band closest to the trainee.
Falls back to `cfg`'s pair when it has no answer, so a boss whose configured grass IS correct
keeps exactly today's behaviour, and a picker failure can never destroy a successful catch.

**Live probe from `lavaridge.ss1`** (one map from the catch site), with the real
`_counter_area_allowed` predicate:
```
best_training_area(L15) -> (ROUTE117, (31,16), (13,14))
best_training_area(L20) -> (ROUTE111, (25,55), (19,22))     # level-matching works
counter_training_ground(L15, Norman cfg)
    -> grass=(ROUTE117,(31,16))  heal=PokemonCenter.VerdanturfTown   => RELOCATED, fix fired
```
So the counter now trains on **L13-14 wilds with a working heal loop** instead of L3-4 on the
far side of Hoenn.

**Repro:** `tools/story-dev/repro_counter_training_ground.py` — asserts the PROPERTY (never a
no-return ground at any level L10-30 even with `allow=<always true>`, never an unwinnable
band, never ROUTE102 for a L15 counter, and safe degradation with no ROM) rather than one
hardcoded map, so a future table edit cannot quietly reintroduce the hole.

‼ **WHAT IS NOT YET PROVEN.** The probe stood on LAVARIDGE_TOWN, not on FIERY_PATH (18,19)
where the catch actually happens — one map short of the exact case. And the OUTCOME claim
(that a trained counter beats Norman) is unmeasured: that needs a batch, and batch4's own
lesson is that the mechanism firing is not the same as the funnel moving. Read
`Heat→Balance` against batch4's 24/29 (83%), and count `counter training failed` — it was
**7 of 7**.

---

## KI-45 — A battle MOVE-menu loop hangs a lane indefinitely, and neither guard can see it (2026-08-02, severity: HIGH)

**Observed live**, batch6 lane H4 (`x4-runs/20260802-160603`): the lane produced **no stdout
for 27 minutes** while the process stayed alive and burned CPU (8,874 s). Not a freeze — a
loop. It ended the batch with ~7.3 MB of output against ~15 MB on healthy lanes, i.e. it lost
roughly half its productive time.

```
generator call stack (where the bot is waiting):
  -> BattleListener.fight            @ _listeners.py:219
  -> handle_battle                   @ battle_handler.py:306
  -> handle_battle_action_selection  @ battle_action_selection.py:96
  -> battle_action_use_move          @ battle_action_selection.py:283
  -> scroll_to_move                  @ battle_menuing.py:52
  -> _select_in_menu                 @ battle_menuing.py:41
f3060001 state=4 controllable=False map=DEWFORD TOWN(3,3) pos=(4,4)
         party=['Nincada:L10','Marshtomp:L20','Whismur:L13']
         scripts=['EventScript_DoTrainerBattle']
```
**866 STUCK dumps** at that site; every heartbeat in the last 200 lines is the same message
(`entering Dewford Gym to challenge Brawly`).

**‼ WHY NOTHING STOPPED IT — both guards are structurally blind here.**
* The **global watchdog** requires an UNCHANGED progress signature for 18,000 frames. A menu
  loop keeps changing map/coords/state/message, so the signature never goes stale.
* The **per-run frame budget** is KI-36's documented hole: *"the per-run frame budget CANNOT
  fire while a battle handler is on the stack."* This is exactly that shape, in a new place.

**NOT caused by the 2026-08-02 changes.** `#24-pc` and `#24-areaitemgate` touch healing,
training-area choice and the PC; nothing on this stack. The party here (Nincada L10 /
Marshtomp L20 / Whismur L13) is a normal early-game team.

**What to do — do NOT just raise a timeout.** `_select_in_menu` is a cursor-scroll loop; if it
cannot reach the target slot the honest answer is to raise so the battle handler's existing
fault path can take over, not to spin. Establish first WHY the cursor never arrives (a
disabled/0-PP move? a move slot index off the end? the cursor already there and the
success test wrong?), reproducing from H4's own debug log, before bounding anything.

Related: **KI-36** (the frame budget cannot fire under a battle handler — the same blind
spot), **KI-8** (mid-battle rotation party-menu stall), **KI-17** (after-faint party-menu
freeze). This project has now seen three distinct battle-menu wedges; a shared bounded
menu-drive helper may be the real fix.

### KI-45 — FIXED 2026-08-03 (bounded + reported through the recoverable channel)

**Root cause: stock `battle_menuing._select_in_menu` is `while True:`.** It presses a direction
until the cursor read equals the target. If the menu is not actually open, or the read returns
anything outside 0..3, no press can change it — and the movement logic still picks a direction
every iteration: `current_index=5` with `target_index=0` matches
`current_index > 1 and target_index <= 1` and presses **"Up" forever**.

**Measured cost, twice:**
| | dumps | effect |
|---|---|---|
| batch6 lane H4 | 866 | 27 min silent, ~half the lane's output lost |
| batch9 lane H6 | 1,430 | **0 runs completed in a 180-minute batch** |

**Fix:** `_MAX_CURSOR_STEPS = 60` (~180 frames; a real selection needs ≤3 presses, so ~20×
headroom and ~1% of the watchdog window). On exhaustion it reports through
`battle_fault.request_mode_recovery()` — one recoverable derail for a mode that opted in —
and only raises `BotModeError` when no mode can handle it, preserving stock behaviour.

‼ **The message carries the last cursor value, because THAT is the diagnosis.** An
out-of-range value means the menu was never open; a stuck in-range value means the presses are
not landing. Without it the next reader is back to guessing, which is what cost two lanes.

**Repro:** `repro_ki45_cursor_bound.py` — **drives the real generator** against a stuck cursor
rather than asserting on source text, so a regression to `while True` hangs the test instead of
passing it. Also asserts a normal selection still completes in ≤4 presses.

‼ **Why nothing else caught it, worth keeping:** the global watchdog needs an UNCHANGED
progress signature and a menu loop keeps changing map/coords/state; the per-run frame budget
is KI-36's documented hole ("cannot fire while a battle handler is on the stack"). **Two
independent guards were both structurally blind to the same loop.** Any new `while True` on
the battle path has no safety net but its own bound.

---

> 📦 **KI-46 moved to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-13** — FIXED same day, 2026-08-03.

## KI-47 — The battle path has a CLASS of unbounded loops; the existing watchdog is STARVED by them (2026-08-04, NET ADDED)

**Audit result** (`ast` sweep of `battle_handler`, `battle_action_selection`, `battle_menuing`,
`battle_move_replacing`, `battle_evolution_scene`, `modes/_listeners`): **32 `while` loops with
no counter, no `break` and no `raise`.** Two have each already cost a whole lane:

| | site | cost |
|---|---|---|
| KI-45 | `battle_menuing._select_in_menu` | batch6 H4; batch9 H6 = **0 runs / 180 min** |
| KI-46 | `handle_battle_action_selection` | batch10 H2 **and** H8, ~59 min each |

‼ **WHY `handle_battle`'s OWN ML-11 WATCHDOG DID NOT CATCH EITHER.** It is correct, and it is
**starved**: it only runs between iterations of its own loop, and a sub-generator that yields
for ever consumes the frames on its behalf, so `_no_progress` never increments. Same
starvation shape as **KI-37** (a listener above the mode starving it).

**The fix is ONE NET, not 32 bounds.** `handle_battle._watch(subgen, label)` wraps every
sub-handler call and counts frames **where they are actually consumed** — inside the
sub-generator's yields — faulting after `_SUBHANDLER_STALL_FRAMES = 3000` (~50 s) with the
battle progress signature frozen. It therefore covers all 32 loops, **including ones not yet
written**. Reports via `battle_fault.request_mode_recovery()`; raises `BotModeError` otherwise.

‼ **ORDERING IS DELIBERATE — the net sits BEHIND the specific bounds** (KI-45's 60 cursor
steps ≈ 180 frames, KI-46's 600 frames). A tighter net would pre-empt them and destroy their
specific diagnoses, leaving only "the battle stopped progressing". `repro_ki47_subhandler_net.py`
check 2 asserts that ordering.

**Deliberately NOT done: bounding the other 30 individually.** Most legitimately wait for the
game to move on, and 30 hand-picked bounds are 30 chances to pick a wrong one. Add a specific
bound only where a real hang has been observed — the net makes that safe to wait for.

**Repro:** `repro_ki47_subhandler_net.py` — asserts no sub-handler is called unwrapped, that a
forever-yielding handler faults, that a long BUT PROGRESSING one does not (no false positive),
and that the error is not a `NameError`.


---

## KI-38 — REOPENED 2026-08-04. It was MITIGATED, not fixed, and it is the dominant battle hang

The handoff has recorded KI-38 as "FIXED 2026-07-31 AM" since the hang rate went 11/12 → 1/8.
Batch11's KI-47 net makes that reading untenable:

```
KI-47  7 of 8 hits   handle_fainted_pokemon, frozen at 'BattleScript_FaintedMonTryChoose'
KI-46  1 of 8 hits   controller0='CompleteOnInactiveTextPrinter2'
```

**Every one of the seven is the after-faint chooser.** It is still wedging ~7 times per
180-minute batch. What changed on 2026-07-31 is that it stopped being *fatal*; what changed
on 2026-08-04 is that the net converts each wedge into a bounded recoverable derail instead of
an infinite lane. Neither is a fix — the run still pays for every one.

‼ **WHY THE RATE DROP WAS MISREAD.** "Hangs 11/12 → 1/8" measured how often a wedge *killed a
run*, not how often it *happened*. Recovery improving is not the fault going away — the same
error as `d7d493d8` being called live-validated on "no unrecovered errors" while finishing 0%
of runs. **State the metric beside any "fixed" claim, and prefer a rate of OCCURRENCE over a
rate of SURVIVAL.**

**The real fix is still `#24-menutext`,** as KI-38's own entry already says: read the party-menu
TEXT instead of inferring from cursor indices. Its evidence — `cursors_seen=[0,2,3,7]` in a
4-mon party, `presses={'Down': 3, 'A': 273}` — says the cursor MODEL is wrong, and no retry
limit or bound can fix a wrong model. `FAINT_CHOOSER_GIVEUP_LIMIT` and the KI-47 net are both
mitigations layered over it.

**Measured drag:** ~7 derails per batch, each costing recovery time and one unit of the derail
budget that protects against genuine stuck loops.

---

## KI-48 — Direct navigation cannot walk ROUTE110 → MAUVILLE_CITY: it only considers Mauville's building DOORS, never the map connection (2026-08-09, severity: MED — measured, not yet root-caused)

- **Symptom.** `_navigate_riding_out(MapRSE.MAUVILLE_CITY, (22, 6))` from ROUTE110 fails
  **3 of 3** attempts, identically and deterministically, at tile (16, 89):
  ```
  Could not reach (22, 6) on MapRSE.MAUVILLE_CITY: the field is idle and we are still at
  (16, 89), so retrying cannot change the result (Cannot reach MAUVILLE_CITY: it is not
  walkable from ROUTE110, and none of the 6 candidate warp route(s) start at a tile that can
  be walked to from here (tried: MAUVILLE_CITY(8, 5), MAUVILLE_CITY(22, 5),
  MAUVILLE_CITY(35, 5), MAUVILLE_CITY(23, 14), MAUVILLE_CITY(32, 14), MAUVILLE_CITY(8, 13)).)
  ```
- **The tell.** All six candidates it enumerated are **building doors inside Mauville**. The
  plain ROUTE110 → MAUVILLE_CITY **map connection** is not in the candidate set at all, so the
  planner never tried the route a player would use.
- **Repro** (~1,400 frames, no batch needed):
  ```
  cd tools/story-dev
  PYTHONUTF8=1 CAPTURE_TARGET=MAUVILLE_CITY:22,6 CAPTURE_NAME=throwaway.ss1 \
      py -3.12 story_harness.py slateport.ss1 --driver anchorcapture --frames 600000 --profile ki48
  ```
- **‼ It is NOT a map fact, and that is what makes it a bug.** Story mode walks
  Slateport → Mauville every run; `--driver anchorstory` did it here in **13,666 frames** from
  the same save, producing `saves/mauville_prewattson.ss1`. Whatever story mode's travel path
  does, the direct entry point does not.
- **Ruled out — do not re-run these:** a door-warp transition race (`Task_DoDoorWarp` +
  `Task_AnimateDoor` were live while the error claimed *"the field is idle"*, which looked
  exactly like `#24-journey` part 3 for door warps). A retry-after-settle A/B produced **three
  identical failures at the identical tile**. Deterministic failure is not a race.
- **Why it may matter beyond this probe.** `could not reach` was **72 occurrences** in batch
  `20260808-095721` and is the largest unexplained travel-failure bucket in the counter chain.
  This is one concrete, cheap-to-reproduce instance of that class. It is NOT yet established
  that they share a cause — ‼ that claim needs a measurement that could discriminate, per the
  2026-07-31 prevention rule.
- **Suspected cause (UNVERIFIED, stated as a hypothesis only):** the candidate enumeration is
  warp-only, so a destination reachable purely by an edge connection has no candidate to plan
  toward. Check whether the connection path is skipped because (16, 89) sits on/next to
  Route 110's dual-elevation Cycling Road, which is the KI-24 failure shape.
- **Workaround:** capture anchors with `--driver anchorstory` (the bot's own route) rather than
  `--driver anchorcapture` for any Slateport → Mauville leg.

---

## KI-49 — Journey planning is MAP-granular, so it can arrive at an entrance from which the destination TILE is unreachable — and nothing tries another entrance (2026-08-09, severity: MED, MEASURED)

- **Symptom.** Asked to walk to `ROUTE116 (11, 7)` from Mauville, the bot **reaches ROUTE116**
  (~32,000 frames) and lands at **(65, 11)**, then fails the final intra-map leg:
  `Could not find a path from (65/11 @ ROUTE116) to (11/7 @ ROUTE116)`. It reports the
  destination as unreachable and stops. No other entrance to the same map is attempted.
- **Why it happens.** `#24-journey` deliberately plans at MAP granularity (`06-DECISIONS-LOG`
  2026-07-31 rejected the full leg-list planner). Once the map is reached, the tile leg is on
  its own. If the map has more than one entrance and the arrival one is in a disconnected
  region, the trip fails at the last step having done all the work.
- **Measured, `probe_r116_east_grass.py` (static, two positive controls, both PASS):**
  | from | walkable tiles reachable | GRASS tiles reachable |
  |---|---|---|
  | (65, 11) — the arrival, east | **17 of 151** (bbox x 64-78, y 6-14) | **0 of 138** |
  | (11, 7) — the west side | 104 of 151 | **136 of 138** |
  Route 116's grass is essentially all on the WEST side; the east arrival is a small isolated
  pocket. So the trip did not fail because the destination is unreachable in principle — it
  failed because of WHICH ENTRANCE the journey chose.
- **‼ How independent is that evidence?** Only partly, and it should not be oversold: the
  driven `_navigate_riding_out` leg and the static `calculate_path` region check share the
  tile-graph machinery, so their agreement is weaker than two genuinely separate instruments.
  What is strong is the CONTRAST between east and west, which is measured the same way on both
  sides and is a 0/138 vs 136/138 split.
- **‼ OPEN, and not guessed at here:** which map path the journey took to land on the EAST end
  (the harness log records the sweep's own lines, not map transitions), and therefore whether a
  west approach is even available pre-badge03. Answer that before designing a fix.
- **Possible shapes of a fix (none chosen):** rank candidate entrances by whether the
  destination tile is reachable from them; or fall back to another entrance when the tile leg
  fails; or let hunting grounds declare the entrance their tile belongs to.
- **Repro:** `PYTHONUTF8=1 py -3.12 probe_r116_east_grass.py` (seconds, no emulation loop), or
  the full driven version in the `#24-r116sweep` punch-list entry.

---

## KI-50 — ‼‼ CORRECTED SAME DAY. The chapter is NOT a coin-flip: the CURRENT `magma_door.ss1` loses to Maxie DETERMINISTICALLY (2026-08-11, severity: MED, MEASURED)

**What was measured.** A second driven run of `--driver magmahideout` from `saves/magma_door.ss1`
— the identical command that produced `groudon=True, whiteouts=0` on 2026-08-10 — **lost**:
```
whiteouts in the run: 7      (vs 0 on 2026-08-10)
battle_text='NICK whited out!'  instr=BattleScript_LocalBattleLostEnd
respawn: MAUVILLE_CITY (22,6)
floors reached: 1F -> 2F_1R -> 3F_1R -> 4F, standing at (15,21) facing Maxie (16,21)
```
It navigated the whole dungeon correctly and reached Maxie — the *content* works. It then lost
the fight.

‼‼ **THE "1 IN 3" READING WAS WRONG AND IS WITHDRAWN.** I recorded two losses against one win
and wrote it up as a RATE. It is not a rate. **All three losing runs are BYTE-IDENTICAL:**
```
mh-anchor   41 unique [TURN] lines  md5 07f99a10ac8b
mh-anchor2  41 unique [TURN] lines  md5 07f99a10ac8b
mh-try1     41 unique [TURN] lines  md5 07f99a10ac8b
diff: IDENTICAL, all pairs
```
Same HP, same PP, same 18 turns, same Camerupt heal on the same turn. A `.ss1` replays identical
frame timing, so **the current `magma_door.ss1` does not sometimes lose — it always loses.**

‼ **AND THE ONE WIN WAS ON A DIFFERENT SAVE.** `magma_door.ss1` is **re-captured by
`--driver magmatravel` on every success**. The winning run of 2026-08-10 used the save as it stood
BEFORE 22:05; a later `magmatravel` success overwrote it at 22:05 with a different party/RNG phase,
and every hideout run since has lost the identical fight. Reaching Maxie is 3/3 and always was —
the *content* is fine.

‼‼ **THIS IS THE SAME FIXTURE-OVERWRITE HAZARD THAT KILLED THE `#24-teachmsgstall` REPRO EARLIER
THE SAME DAY**, on a completely different question, and I walked into it again within hours of
writing the prevention rule. **`saves/magma_door.ss1` is a CACHE, not a fixture.** The
deterministic-loss state is now preserved as **`saves/magma_door_losing.ss1`** — nothing writes to
that name, and it is a genuinely valuable repro: a boss fight that loses the same way every time is
the ideal fixture for the boss-healing and frozen-PP questions below.

‼ **A RETRY LOOP IS THE WRONG RESPONSE** and I ran one before checking. Eight attempts would have
produced eight identical losses (~80 minutes). It was stopped after attempt 1 once the md5s matched.
**The fix is a DIFFERENT SAVE, not another roll:** re-run `--driver magmatravel` from
`saves/post_mtpyre.ss1` to mint a fresh `magma_door.ss1`, then drive the hideout from that.

‼ **THIS AMENDS AN "ALREADY PROVEN" ROW.** `04-HANDOFF.md` carried
"The Magma Hideout chapter completes — ✅ `groudon=True`, 0 whiteouts" with no sample size beside
it. **n was 1.** The chapter reaching Maxie is reliable; the chapter *completing* is not, because
it depends on winning a boss fight with a party that arrives worn down. Quote it as
"1 of 2 driven runs" until there are more.

**Why it matters beyond this chapter:** the post-Maxie era is the precondition for §Ch16 (the
Slateport Harbor beat), so anchor manufacture for the next chapter inherits this coin-flip.

### ✅ THE MAXIE FIGHT, READ TURN BY TURN (2026-08-11, from `mh-anchor2`'s own telemetry)
`#24-bosstelemetry` was already in the tree, so the losing fight is on record. Maxie's team is
**Mightyena L37 / Crobat L38 / Camerupt L39**; the party opened at full strength (Sceptile 122/122).

**✅ FINDING 1 — SOLID AND UNAMBIGUOUS: Maxie HEALED Camerupt out of the kill.**
```
[TURN 14] Skitty L17 45/45 -> UseMove:Tackle(pp35)  vs Camerupt L39  22/110
[TURN 15] Skitty L17 45/45 -> UseMove:Tackle(pp34)  vs Camerupt L39  67/110
```
Skitty's PP went 35 -> 34, so its Tackle DID execute — and Camerupt still went **22 -> 67, a heal
of at least +45**, one or two hits from death. This is the known boss-healing problem
(`probe_boss_healing.py`: 17.0% of boss-length battles show a >=50 HP heal) **deciding a
story-content chapter for the first time on record.** The party had Camerupt beaten and could not
close.

**⚠ FINDING 2 — REAL OBSERVATION, NOT DIAGNOSABLE WITH TODAY'S TELEMETRY.** The party's best
attacker did nothing for three consecutive selections while dying:
```
[TURN 3] Sceptile L44 122/122 -> UseMove:Slam(pp19)  vs Crobat L38 90/119
[TURN 4] Sceptile L44 110/122 -> UseMove:Slam(pp19)  vs Crobat L38 90/119
[TURN 5] Sceptile L44  30/122 -> UseItem              vs Crobat L38 90/119
[TURN 6] Sceptile L44   4/122 -> UseMove:Slam(pp19)  vs Crobat L38 90/119
```
**PP frozen at 19 across all three Slams, Crobat's HP frozen at 90/119, Sceptile 122 -> 4.**
(Its Leaf Blade had decremented normally on turns 0-2: pp12 -> 11 -> 10, killing Mightyena — so
the mon and the logger were both working moments earlier.)

‼ **A MISS CANNOT EXPLAIN FROZEN PP** — a missed move still consumes it. But **two causes remain
and this telemetry cannot separate them**:
1. the standing `#24-bosstelemetry` **lead 2**, "selected but not executed" on natural mons
   (2026-08-09, undiagnosed); or
2. **ordinary incapacitation** — sleep, freeze, flinch, full paralysis, or a confusion self-hit.
   None of those consume PP either, and Crobat learns **Confuse Ray** and **Bite** (flinch). The
   HP pattern (−12, then −80, then −26 while never acting) fits confusion self-damage well.

⇒ **RESOLVED THE SAME DAY — IT IS CONFUSION, NOT A BOT BUG.** The status field was added to the
turn logger and the deterministic fixture re-run. One run answered it:
```
[TURN 3] Sceptile L44 122/122            -> UseMove:Slam(pp19)  vs Crobat L38 90/119
[TURN 4] Sceptile L44 110/122 [Confused] -> UseMove:Slam(pp19)  vs Crobat L38 90/119
[TURN 5] Sceptile L44  30/122 [Confused] -> UseItem              vs Crobat L38 90/119
[TURN 6] Sceptile L44   4/122 [Confused] -> UseMove:Slam(pp19)  vs Crobat L38 90/119
```
Crobat used **Confuse Ray**; Sceptile hit itself 122 -> 110 -> 30 -> 4. Confusion self-hits do not
consume PP, which is the whole of the "frozen PP" mystery. **Castform was confused too**
(turns 8-9, 100 -> 46). ‼ **`#24-bosstelemetry` LEAD 2 is REFUTED for this instance** — the action
pipeline is fine; the bot simply has **no answer to confusion** (it neither switches out nor
carries a Persim Berry), which is a STRATEGY gap, not a bug.
‼ Scope it honestly: the 2026-08-09 sightings (Cross Chop at pp2, Ninjask's Scratch at pp30) were
recorded WITHOUT status and are not retro-explained by this — but confusion is now the leading
hypothesis for them, and the field to check them with exists.

**CONTROL: the telemetry change is behaviourally inert.** With the status suffix stripped, the new
run's 41 turn lines are md5-identical to the three earlier runs (`07f99a10ac8b`) — same fight, one
extra field.

### ✅ DONE: the turn logger now prints STATUS
`modules/battle_action_selection.py`'s `_describe(mon)` printed species / level / HP and no status,
which is why every boss-loss post-mortem here had to end in "either a bot bug or ordinary status".
It now appends `[Confused]` / `[Sleep]` / `[Paralysis]` / … from `status_permanent` +
`status_temporary`, and **only when there is something** — a healthy mon must not add noise to the
~800 battle-level samples a batch produces.

### ⇒ SO WHY THE CHAPTER LOSES, in one sentence
**Crobat confuses the two strongest attackers into killing themselves, and then Maxie heals
Camerupt out of the kill.** Neither is a bug: both are gaps in what the bot can DO about a boss.
That is a design decision (status response / burst damage / item policy) and belongs to the user —
see the boss-healing entry in `03-PUNCH-LIST` §2.

**Also not yet investigated:** whether the whiteouts are the same worn-party problem the travel leg
already has (Ch14 hands over 3-of-6 fainted, no Revives), or whether the interior's own trainer
chain grinds the party down.

**Repro:** `PYTHONUTF8=1 py -3.12 story_harness.py magma_door.ss1 --driver magmahideout
--frames 2500000 --profile mhN` and count `whited out` in the debug log.

---

## KI-51 — ✅ FIXED 2026-08-11 — a whiteout-blind loop rode 60,000 frames and blamed the wrong thing (ARCHIVED)

Full diagnosis, the two controls and its prevention rule moved to `31-KNOWN-ISSUES-ARCHIVE.md` on
2026-08-13 to keep this current-state file inside its 3,000-line budget (lint rule R3). Keep only
this: **a loop whose exit condition is a story flag must ALSO watch for the ways the game can move
the player out from under it — a whiteout satisfies no flag.** ‼ It also recorded that
`saves/magma_1f_fail.ss1` is MISNAMED: it stands on **4F**, not 1F.

---

## KI-52 — ✅ FIXED 2026-08-11 — a wild battle used to END THE RUN when the lead could not act (ARCHIVED)

The strategy raised from inside battle code, and battle handling is a SIBLING on a flat
controller stack — so `main_loop` caught it first and forced Manual. Fixed by rotate → flee →
**FIGHT ON**, and by never raising inside a battle (record the fault via `modules/battle_fault.py`
and let the mode claim it). Promoted to `custom-pokebot` 2026-08-11.

Full detail moved to **`31-KNOWN-ISSUES-ARCHIVE.md`** on 2026-08-12 for the R3 budget.

## KI-53 — `calculate_path` is DIRECTIONAL between ROUTE110 and SLATEPORT_CITY: southbound plans, northbound-to-city fails (2026-08-11, severity: MED, MEASURED, blocks §Ch16's travel leg)

**The measurement** (static `calculate_path`, `probe_ch16_travel.py`, all controls green):
```
SLATEPORT(28,13) -> ROUTE110(14,97) : OK, 30 waypoints
ROUTE110(14,97)  -> SLATEPORT(28,13): FAIL          <- the exact reverse of the line above
ROUTE110(14,5)   -> SLATEPORT(28,13): FAIL
ROUTE110(14,97)  -> SLATEPORT(14,4) : FAIL
ROUTE110(14,97)  -> ROUTE110(14,5)  : OK, 168 waypoints   (intra-map is healthy)
ROUTE110(14,97)  -> MAUVILLE(22,6)  : OK, 203 waypoints   (the other neighbour is fine)
MAUVILLE(22,6)   -> ROUTE110(14,97) : OK, 203 waypoints
```
‼ **Same two tiles, opposite directions, opposite answers.** Both maps plan internally, the
intra-ROUTE110 path plans, and ROUTE110's *other* neighbour (Mauville) plans in both directions.
The failure is specific to **arriving at SLATEPORT_CITY from ROUTE110**.

**CONTROLS.** Every map used here passed an intra-map hop first. ‼ And the control tiles are chosen
**empirically** — the first draft hard-coded `SLATEPORT_CITY (28,13) -> (28,14)`, which FAILED
because `(28,14)` is simply not walkable, making a healthy planner look dead. *A control that can
legitimately fail is not a control.*

**Why it matters:** §Ch16's travel leg is `post_maxie.ss1` (Magma Hideout) → Slateport Harbor. The
last mile is exactly this hop, so a single `navigate_to(SLATEPORT_CITY, …)` from the north is
expected to fail.

### ‼ WHAT THIS IS *NOT*
* **Not a contradiction of KI-48.** KI-48 is about the **driven navigator** failing ROUTE110 →
  MAUVILLE_CITY (3/3) and explicitly notes `calculate_path` disagrees with it. This entry is about
  the **static planner**. Static-plans-but-driven-fails is an established pattern here; do not
  merge the two entries.
* **Not proof the leg is impossible.** `calculate_path` has called reachable places unreachable
  before (KI-24), and `_navigate_riding_out` does strictly more than the static planner (it clears
  obstacles and retries) — which is exactly how §Ch15's Mauville → Route 112 leg succeeded while
  planning statically as FAIL. **A static FAIL is a strong signal to plan around, not a verdict.**

### NEXT STEP (not yet done)
Build §Ch16's travel leg as **explicit short legs** in the §Ch15 pattern, with **ROUTE110 →
SLATEPORT_CITY as its own leg**, so that if it breaks it names itself instead of arriving as
"the chapter does not work". Only if that driven leg also fails is this a planner bug worth
chasing — and then the discriminator is whether a *one-way ledge* on Route 110's south edge makes
the asymmetry legitimate terrain rather than a defect.

---

## KI-54 — "Roster hygiene before bosses" is BLOCKED (2026-08-11, informational) — FULL ENTRY MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-15)

Moved on the R3 line budget: 218 lines of a CURRENT-STATE file, severity *informational*, and its
subject was RETRACTED. ‼ **Keep only this:** the "one flag and one text box away" unlock was
**false on BOTH halves** — `POKEBOT_BOX_OVERFLOW_CATCH` had defaulted **ON** since 2026-08-07 and
the text-box blocker was refuted the same day. **Four documents repeated it because they were
written from a stale CODE COMMENT instead of the default twenty lines below it.** ⇒ *read the
value, not the comment describing the value.* And the deposit path it would have needed was
separately MEASURED HARMFUL (`#24-pc`: ~1 mon/run, ~19 points of the last funnel rung).

---

## KI-55 — ✅ RESOLVED 2026-08-11 — the STATUS TAX is real and MEASURED (ARCHIVED)

Incapacitated turns cost **960/2,945 = 32.6%** against a clean control of **1,259/33,017 = 3.8%**
— **8.5x, z = +62.2**, over 47,789 turns from 36 independent lane logs. ‼ An earlier n=2 figure of
64.3% was **~2x too high**: one dungeon fight is not a rate.

Full detail moved to **`31-KNOWN-ISSUES-ARCHIVE.md`** on 2026-08-12 for the R3 budget.
‼ Keep only this here: the rate is the EVIDENCE a status response needed, but building one is a
battle-policy change touching every mode and remains **the USER's call**.

## KI-56 / KI-57 — ✅ BOTH RESOLVED AND DRIVEN 2026-08-11 → archived

Full write-ups moved to **`31-KNOWN-ISSUES-ARCHIVE.md`** to keep this file inside its budget.
* **KI-56** — §Ch15 stranded the run inside the Magma Hideout; Strength boulders RESET on map
  reload. Fixed with the Escape Rope the dungeon itself provides. ‼ Its prevention rule — *a
  chapter's test must include "and the bot can continue"* — was violated again by §Ch18 on
  2026-08-12 (see `08-MISTAKES.md`). It is the single most re-learned lesson here.
* **KI-57** — beating Maxie parked Capt. Stern on the tile §Ch16 needed; he was not an obstacle
  but the door — talking to him warps the player in.

## KI-58 — the Mossdeep Gym statue puzzle (2026-08-12, ✅ RESOLVED — detail ARCHIVED)

The gym is a **ROTATING-TILE STATUE PUZZLE**, not a maze: nine floor switches call
`moverotatingtileobjects`, moving every object on a matching coloured arrow — **including nine
of the trainers**. Four independent instruments all concluded it had no route to its own leaders
because none of them modelled that third movement primitive.

Full detail (the encoding derived from the ROM dump, the validated simulator, the per-press
object counts, and the list of things that bite) moved to **`31-KNOWN-ISSUES-ARCHIVE.md`** on
2026-08-12 to keep this file inside its R3 budget. ‼ Keep only this here: the method that cracked
it is written up in `14-AGENT-PLAYBOOK.md §4b` — *simulate the mechanic, then make the GAME grade
your simulator* — and it is the reusable part.

## KI-61 — the chapter DETECTOR named the wrong beat after badge 7 (2026-08-12, ✅ FIXED — ARCHIVED)

`chapters.py` listed the Space Center BEFORE the Mossdeep gym, so `_compute_badges_before()`
put chapter 19 in the SIX-badge bracket and `current_chapter()` skipped two whole beats the
moment the seventh badge landed. A/B proven; the design doc's "order confirmed" was wrong.

Full detail moved to **`31-KNOWN-ISSUES-ARCHIVE.md`** on 2026-08-12 for the R3 budget.
‼ Keep only this here: it is guarded by `probe_chapter_order.py`, which now takes `--build` and
passes on BOTH forks — it used to hard-code the sandbox path and so could never test the build
the user runs. **ORDER in a list that more than one consumer reads is a silent logic bug, not
cosmetics.**

## KI-62 — the detector still names "To Lilycove" on a save long past Lilycove (2026-08-12, OPEN, LOW)

Noticed while measuring KI-61 and deliberately **not** fixed, because it is a different question.
On `post_aqua.ss1` — 6 badges, the Aqua Hideout already completed — `current_chapter()` returns
**ch16 "To Lilycove"**, whose milestone is `MET_RIVAL_LILYCOVE`. Either our runs reach Lilycove
without triggering that rival meeting, or the flag is the wrong completion proxy for that chapter.

‼ Consequence: the detector's report is a **lower bound** on progress, not a position. Anything that
reasons from `chapter_key` (the endless-run stage label, resume messages) may understate how far a
save has got. `probe_chapter_order.py` deliberately does not assert on this save, and says why.
**To settle it:** check `MET_RIVAL_LILYCOVE` across the anchors that have plainly passed Lilycove,
and if it is unset on all of them, the milestone is wrong rather than the run.

## ✅ KI-63 — RESOLVED 2026-08-13. The bot acquires DIVE BY PLAYING. (filed 2026-08-12)

> **`--driver divelearner` → `ACCEPTANCE: PASS` on the first drive.** Nothing injected: a slot was
> freed, a **Marill L13** was hunted and caught (balls 19→17), and **Dive was taught over Defense
> Curl** — the 0-power move, exactly what the expendability picker should pick.
> `knows_dive=True can_dive=True surf_intact=True can_continue=True`, and **Zigzagoon kept Surf**.
>
> **What had to be BUILT:** `pc_trip.deposit_one_dead_weight()` — because **neither** existing
> deposit path can free a slot *before* a catch (`withdraw_from_box` returns immediately with
> nothing boxed; `deposit_dead_weight_if_worth_it` is a silent no-op behind
> `POKEBOT_PC_ROTATION`). ‼ Our own handoff named the first of those as the path to use; that is
> retracted. Wired as an opt-in `_needs_party_slot` piggyback inside `heal_in_pokemon_center`.
>
> **‼ ORDER:** call `ensure_hm_learner` FIRST and deposit only on the specific *"party is full"*
> failure — `hm_learner_slot` is checked *before* the party-full check, so deposit-first would
> spend a PC trip and a team member even when no catch was needed.
>
> ## ✅ WIRED INTO PRODUCTION 2026-08-13 (later) — the caveat below is now RESOLVED **in sandbox**
> `early_game.ensure_hm_learner_making_room` sets the flag and retries once; both `story_mode.py`
> call sites (Rock Smash HM06, Surf HM03) now use it. Driven: `ACCEPTANCE: PASS`, with the deposit
> asserted **by PID** (`deposited_pids=[1556928702]` = Skitty). New gate
> **`repro_hm_slot_wiring.py` (22/22, fault-injected)** keeps the chain connected.
> **MEASURED WORTH:** 20 terminal run-kills in 1,129 runs (**0.91%** excluding a reverted
> party-cap bundle), **#1 of 14 derail causes by frames per event (1,717k avg)** — 7.2% of all
> derailed lane time from 3.4% of derails, every one of them five badges deep.
> ⛔ **`custom-pokebot` IS STILL INERT** — it reads the flag but nothing there sets it, and its
> `story_mode.py` still calls the bare function. **Promotion has NOT been asked for.**
>
> ### (the caveat as it stood before the wiring)
> **The CAPABILITY is proven; PRODUCTION IS NOT WIRED.** `_needs_party_slot` has **no setter
> anywhere in `modules/` or `plugins/`** — only `--driver divelearner` sets it (verified by grep).
> So in a real `StoryMode` run the piggyback **never fires**, `ensure_hm_learner(HM08)` still
> raises *"the party is full"*, and the chapter still ends there. **Wiring `story_mode.py` to
> catch that error and set the flag is the remaining work.** Flagged by adversarial review, which
> was right to insist it be stated rather than implied.
> ‼ §Ch21 also still has to be BUILT as a chapter; this removes its blocker. The learner is a **Marill L13, 36 levels below the team** — an HM slave that
> `find_dead_weight` would want to box on a later trip unless the sole-carrier exemption covers it.
> And the ground used is Route 117 (10%, L13, 1,055 waypoints); the better Shoal Cave ground was
> deliberately NOT adopted, because `_hm_hunting_grounds` reads `TRAINING_GRASS` and a Shoal row
> flips `best_training_area` for every team from ~L30 up. See
> `ai-research-notes/2026-08-13-ki63-dive-learner-acquisition-plan.md`.

### (original filing, kept for its measurements)
## KI-63 (original 2026-08-12 filing) — MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-13)

✅ **KI-63 is RESOLVED — see its entry above.** The original filing ("no party member can learn
Dive and the party is full") was moved to the archive on 2026-08-13 to keep this current-state file
inside its 3,000-line R3 budget. Nothing was deleted.

---

## KI-64 — ✅ FIXED 2026-08-12 — the multi-battle faint replacer would have sent out STEVEN's Pokémon — FULL DETAIL MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-13)

Fixed, driven and gated (`repro_multi_battle_partner.py`, in the standing suite). The body was still sitting in this CURRENT-STATE file long after it closed, and it pushed the file over its 900/3000-line R3 budget when KI-77 was filed — so it was moved verbatim, not deleted.

‼ **Keep only the two prevention rules, because both were re-learned the hard way:**
1. **Print the MRO before "fixing" a strategy method.** The first fix guarded the base class and was DEAD CODE on the story path (`LevelUpLeadBattleStrategy` has its own `choose_new_lead_after_faint`).
2. **Never identify a Pokémon by party INDEX across a battle-menu boundary.** Opening the battle party menu runs `UpdatePartyToBattleOrder`, which physically PERMUTES `gPlayerParty` — the second fix's `index >= 3` cut was in the wrong index space and offered the ALLY's Pokémon while hiding one of ours. Key on **original trainer ID** (`ally_party_indices()`); identity travels with the Pokémon, position does not.


## KI-74 — `setmetatile` tiles are INVISIBLE to the shared map model, and the KI-59 fix made that fail-DANGEROUS instead of fail-safe (2026-08-13, code-verified, OPEN)

- **The mechanism.** `modules/map.py:770` takes the layout pointer from `self._map_layout[12:16]` —
  the **compile-time ROM grid**. The engine's live grid is `gBackupMapLayout`, which is what
  `setmetatile` rewrites. `map.py` never reads it, so `get_map_data` / `get_map_all_tiles` /
  `calculate_path` are blind to **every runtime tile patch, on every map**.
- **This is not theoretical — it has already been paid for once.** The Mauville Gym barriers wedged
  runs 6-9 for exactly this reason; the fix was a LOCAL live-grid reader,
  `early_game.py:3971 _live_passable()` (`read_symbol("gBackupMapLayout")`), whose own comment says
  the static layout is "blind to every toggle — a 'pathable' static plan walks the player into a
  live beam and bumps forever". ⇒ **The solution pattern exists in-tree; it is just not shared.**
- **‼ WHERE IT IS ARMED NEXT — the REGI ARC, at the DOOR.** `Route111_OnLoad`, `Route105_OnLoad` and
  `Route120_OnLoad` each `call_if_unset FLAG_REGI_DOORS_OPENED` a script that does
  `setmetatile <x>, <y>, METATILE_General_RockWall_RockBase, TRUE` — **the three tomb entrances are
  bricked over until the Sealed Chamber is solved**, and the 4th argument `TRUE` sets the impassable
  bit in the live grid only. Our planner sees an open door and will route the bot into a wall.
  ⚠ Reported by an adversarial agent with decomp citations; **the OUR-SIDE half is verified here**
  (the grep above), the decomp half is NOT yet verified in our harness — do that before building.
- **‼ HOW KI-59'S FIX INTERACTS, and this is the part to keep.** Before 2026-08-13 an
  `Impassable *` tile came out mostly-`False` — the planner **over-blocked and detoured**, i.e.
  failed SAFE. After the fix it comes out mostly-`True`, so on a map whose real layout has been
  rewritten the planner will now **confidently route onto it and bump**. **242 of the 401 live tiles
  (144 Regi + 98 Shoal Cave) sit on maps that rewrite themselves**, and the A/B deliberately chose
  `VICTORY_ROAD_1F` *because* it does not — so every self-rewriting map was outside the proof.
  ⇒ **The fix is still correct** (it matches the decomp on a static layout) **but its blast radius
  on self-rewriting maps is unmeasured.** Measure before any content depends on those maps.
- **Relationship to KI-73.** KI-73 is the narrower cousin (the layout *cache* keyed on map number).
  This is the general case: even with a perfect cache we read the wrong grid.
- **What a fix looks like** (not attempted): promote `_live_passable()`'s `gBackupMapLayout` read
  into `modules/map.py` as an opt-in "live grid" mode for the CURRENTLY LOADED map only — it is
  valid nowhere else — and have chapters that touch self-rewriting maps ask for it explicitly.

---

## KI-75 — the forced-movement simulators do not know about the new exit rule (2026-08-13, code-verified, OPEN, LATENT)

- `map_path.py`'s current/ice slide simulators advance a slide using **collision and elevation only**.
  A* now honours `blocked_exit_directions`, but the slide model does not, so the two can disagree:
  the planner can emit a waypoint at a tile the sliding player never actually reaches.
- **Not observed.** No built content combines directional-impassable tiles with ice or currents.
  ‼ It is planted under **§Ch22 (Sootopolis Gym)**, which is an ice-puzzle gym — check it there
  before building that chapter rather than after.
- Filed by the adversarial review of the KI-59 fix, not by a failure.

---

## KI-76 — our CURRENT-SLIDE model ends the slide ONE TILE SHORT and in the WRONG MOVEMENT MODE, and it cannot see that a slide can END ON A WARP (2026-08-13 — ✅ SAFETY half FIXED and fault-tested; ⚠ CORRECTNESS half OPEN; the §Ch20 Room 6 route is driven and sprang no trap, so it is ARMED chiefly on Routes 132-134)

Found by an adversarial audit of the KI-59-era claim *"our planner models the currents"*, which I had
just committed off the back of a clean 4/4 prediction run. **The 4/4 stands; the conclusion drawn
from it was too strong.** Both defects below are corroborated by OUR OWN measurements, not only by
the agent that reported them.

### Defect 1 — the slide stops one tile early, and leaves the avatar notionally still surfing
`modules/map_path.py:283-288`:
```python
next_tile = get_map_data(current_map, (x, y))
if next_tile.elevation == 1 and not next_tile.collision:
    destination = next_tile; steps += 1
else:
    break
```
So our slide destination is **the last elevation-1 (water) tile**. The game does something else: if
the next tile is land at `ELEVATION_DEFAULT (3)` with no object, `CheckForObjectEventCollision`
returns `COLLISION_STOP_SURFING` and `CreateStopSurfingTask` runs — **the player is moved ONTO the
land tile and DISMOUNTS.**
⇒ **Wrong tile AND wrong movement mode.** Measured in `SEAFLOOR_CAVERN_ROOM7`: **44 of its 117
current chains** funnel into `(3,18)` and push south onto `(3,19)` (`MB_CAVE`, coll 0, elev 3). We
would plan a rest at `(3,18)`, still surfing; the game puts the avatar on foot at `(3,19)`. Every
subsequent planned step from there is wrong.

### ‼ Defect 2 — a slide can end ON A WARP, and the warp penalty is computed ONE BRANCH TOO EARLY
**The precise mechanism** (audited 2026-08-13): `map_path.py:915` applies the `cost = 1000000`
warp-avoidance penalty to the neighbour **before** `:957-966` substitutes the slide destination for
that neighbour. So the DESTINATION's `warps_to` is never inspected, never penalised, and never
marked `is_warp` on the emitted `Waypoint`.
⚠ **And A\* is actively BIASED TOWARD long slides.** Under `avoid_encounters=True` (the
`navigate_to` default) the `+1000` encounter penalty at `:971` is charged **once per waypoint,
after** substitution. A 9-tile slide therefore costs ~`1+9+1000`; nine hand-walked water steps cost
~`9x1001`. **Long slides are ~9x cheaper**, so the planner prefers exactly the moves that can spring
this. The guard that exists to prevent it cannot see them.
**9 of Room 6's 108 chains terminate on `(14,8)`** — which our own `probe_ch20_interior.py` already
recorded as `warp (14,8) elev=1 coll=0 'Non-Animated Door'` → `SEAFLOOR_CAVERN_ENTRANCE`. It is the
water-level door, `MetatileBehavior_IsNonAnimDoor` is in `IsWarpMetatileBehavior`'s accept list, and
`TryStartWarpEventScript` fires on the step. ⇒ **Surf anywhere into roughly `x=9..14, y=9..12` of
Room 6 and the current flushes you north and OUT OF THE MAP.** The planner sees traversable water.
The nine entry tiles all funnel through `(14,9)`, a northward current directly under the door.

### What is NOT wrong (so nobody re-derives it)
* ✅ **No cycles.** All 225 chains in both rooms terminate; the unbounded `while` cannot hang *on
  this data*. Longest chain: Room 6 = 29, Room 7 = 32 ⇒ **a cap of 64 is safe** and should be added
  anyway, because "cannot hang on this map" is not "cannot hang".
* ✅ **No elevation 0/15 tiles** anywhere in either room, so the wildcard-truncation hazard is absent.
* ✅ **Zero blocked-push pockets** — you cannot get permanently stuck sitting on a current here.

### ‼ A THIRD FINDING THAT IS NOT A BUG BUT WILL STALL A CHAPTER
The two `MB_SOUTH_ARROW_WARP` exits — `ROOM6 (11,21)` and `ROOM7 (3,23)` — are **direction-gated**.
They are not in `IsWarpMetatileBehavior`'s list; they go through `IsArrowWarpMetatileBehavior`, which
accepts only `DIR_SOUTH`. And the tile south of each is a **wall** (`ROOM6 (11,22)` / `ROOM7 (3,24)`,
both collision 1). ⇒ **The bot must stand on the tile and press SOUTH into the wall.** Merely
pathing onto it does nothing, and a chapter that "arrives and stops" **stalls forever**. (The two
`(4,1)`/`(5,1)` doors are NOT gated — they fire on any step, so they are transit tiles, never park
tiles.) This is the §Ch18 coord-event shape again: an exit invisible to a warp-graph solver.

### ✅ MEASURED 2026-08-13: the four routes we actually plan do NOT spring it
`probe_ch20_currents.py` section 3b now asserts that no waypoint lands on a warp tile before the
destination is reached. **Result: 0 offenders across all routes.** P1's route rides four currents and
its waypoints `(14,16) (19,11) (8,12) (4,8)` are exactly the documented Room 6 chain termini —
`(14,8)`, the trap, never appears. ‼ **That is NOT a general guarantee**: the defect is real, it is
simply not exercised by these source/destination pairs. **Any NEW route through Room 6 must be
re-checked with that same assertion**, which is why it lives in the probe rather than in prose.
‼ **AND THE CHECK WAS WRONG ON ITS FIRST RUN — the planner was right.** It flagged P4 as riding into
a warp; in fact `(3,23)` IS P4's destination, and when the destination is itself a warp tile the
planner emits it and THEN one more waypoint — the arrival on the far side. So the destination sits at
index `len-2`, and a naive "is it the last waypoint?" test reports the intended exit as a trap.
**Fourth time in this project that a failing probe was the instrument, not the subject.**

### Why the 4/4 prediction run did not catch this
It asked only *"is there a path?"*, and the two routes it exercised do not happen to pass through
Room 6's flush zone or Room 7's dismount funnel. **A reachability question cannot detect a
destination that is off by one tile.** ⇒ Any §Ch20 leg through Rooms 6/7 must be validated by
**driving it**, not by planning it — and the live drive must assert the avatar's FINAL TILE and its
SURF STATE, not merely that it arrived somewhere.

### ⚠ THREE MORE DIVERGENCES FOUND BY THE SAME AUDIT (none armed in this cavern, all real)
* **The entry mask is an INVENTED heuristic, not game truth.** We forbid entering a current head-on
  against its flow; the decomp imposes **no entry restriction on currents at all** (they appear in
  none of the directional-block tables). It is benign and reachability-equivalent here — entering
  against the flow is a no-op, you are pushed straight back — **but it is the actual mechanism
  behind our "Room 6 is ONE-WAY" result.** ⇒ The conclusion is right; describing it as "our planner
  independently reproduced the game's asymmetry" **overstates it**, and that wording is corrected in
  `07-CHANGELOG.md` and `04-HANDOFF.md`.
* ✅ **FIXED 2026-08-13 (both, and MEASURED first — see below): the unbounded loop now has a
  512-step cap that FAILS LOUD, and all four `None` unpacks are guarded.** Measured before fixing:
  **only 5 maps in the entire ROM contain currents** — `ROUTE133` 1552, `ROUTE132` 1345,
  `ROUTE134` 1262, `SEAFLOOR_CAVERN_ROOM7` 117, `ROOM6` 108 — and **0 tiles are ARMED** for the
  `None` unpack (an edge current pushing off-map with no connection that way).
  ‼ **No currently-driven map contains a single current tile**, so neither defect was ever live.
  ‼ **BUT Routes 132/133/134 carry ~10x the cavern's currents and are UNMEASURED for cycles** — and
  they are the route to the **Sealed Chamber (Regi arc)** and **Ever Grande (§Ch23)**. The cap is
  ~16x the longest real chain (32), cannot alter any terminating chain (**A/B: probe output
  byte-identical**), and was **fault-tested** by injecting `cap=3`, which raised with a diagnostic
  naming the tile and map. `probe_current_edges.py` is the measurement.
* *(original wording)* **`_get_connection_for_direction()` can return `None`** (`map_path.py:435-439`) and is unpacked
  unguarded at `:258/264/272/278` ⇒ **`TypeError` inside `PathMap.tiles`** if a current ever sits on
  a map edge with no connection that way. Not reachable in Rooms 6/7 (interior currents);
  **UNVERIFIED for Routes 129-134 / Pacifidlog**, which are full of currents.
* **`MB_SLIDE_*` (0x44-0x47) is not modelled as forced movement at all.** Measured: **zero** in the
  Seafloor Cavern, so not armed here. (‼ "108/117 forced-slide tiles" is loose wording in our docs —
  they are all `*WARD_CURRENT`.)

### Not fixed, and why
Fixing defect 1 means teaching `map_path` a "slide ends in a dismount" concept, and defect 2 a
"slide ends in a warp" concept — both are changes to shared pathfinding that every mode depends on,
i.e. the KI-59 shape, and both need their own A/B. **For §Ch20 the cheap answer is the KI-72 rule
one level up: do not let the planner choose where a slide ends — pick the tiles explicitly and
assert them.** ⚠ **UNVERIFIED LIVE:** the `(3,19)` dismount and the `(14,8)` flush are both static
analysis. Both are cheap to confirm on hardware (surf onto Room 7 `(5,8)`; surf onto Room 6
`(14,9)`) and should be, before code depends on either.

---


## ‼ OPEN ISSUES THAT LIVE IN THE ARCHIVE — do not conclude they are fixed

Two **OPEN, code-verified, unfixed** bugs were moved to `31-KNOWN-ISSUES-ARCHIVE.md` for the R3
line budget, not because they were resolved. A cold read of that file's header says "issues that
are now resolved live here", so they are listed here to stay findable:

* **✅✅ KI-59 — FIXED 2026-08-13, BOTH HALVES, A/B PROVEN, GATED.** Entry vector corrected (all-True,
  clear `[opposite(D)]`) **and** a new `PathTile.blocked_exit_directions` added for the decomp's exit
  rule, checked on the SOURCE tile in the A* loop. **A/B on `VICTORY_ROAD_1F`:**
  `repro_impassable_dirs.py` exit **1 → 0**, **29/29 → 0/29** mismatches, and `calculate_path` went
  from **NO-PATH from every direction** (all 29 tiles invisible to the planner) to `OK len=1` on the
  legal approaches; the `MOSSDEEP_CITY` collateral control is **byte-identical** across arms. Now
  **gate #17**. ‼ `probe_shoal_tide.py` corrected in lockstep; its numbers re-derived on the fixed
  model are **unchanged (LOW 278 / HIGH 0)**. ✅ **PROMOTED 2026-08-14 — that promotion took drift
  to ZERO** (it had reached 5; `counter_hunt.py` and `pokemon_party.py` joined that day and went
  over with the rest, verified by driving `--build custom`). ✅ **drift is ZERO again — KI-78 Stage 1 was PROMOTED later the same day** (superseded: *drift is now 3 again*) —
  KI-78 **Stage 1** (`pokemon.py`, `pokemon_party.py`, `pokemon_storage.py`) landed in sandbox
  AFTER that promotion and has NOT been promoted; promotion is the USER's call.
  Historical note, superseded: *"Sandbox only — promotion is the
  USER's call.** The original diagnosis and the retraction that reprioritised it are kept below.
* **KI-59 (original entry)** — `map_path` **INVERTS `Impassable *` directions**. ✅ **REAL** (decomp-verified).
  ⛔ **BUT ITS "ARMED IN THE SEAFLOOR CAVERN" HEADLINE IS RETRACTED, 2026-08-13, MEASURED.**
  The handler at `map_path.py:128` is the **`elif` of `if tile.collision != 0:`** (`:118`), so a
  collision≠0 tile never reaches it. **All 115 cavern tiles have `collision=1` ⇒ ZERO are live**, and
  the prescribed A/B on `SEAFLOOR_CAVERN_ROOM1` would have measured a **zero delta**. KI-59 does
  **not** gate §Ch20/§Ch21. Swept over all 518 maps by `tools/story-dev/probe_impassable_dirs.py`:
  **2,658 such tiles, 2,257 dormant, 401 (15.1%) live.** It is live chiefly on the **REGI TOMBS**
  (Desert Ruins / Island Cave / Ancient Tomb, 48 each = 144), **SHOAL CAVE** (98) and **VICTORY
  ROAD** (58). ⇒ **It is a prerequisite of the REGI ARC, not of the cavern.** Full detail, the
  decomp ground truth, the specified fix and its pre-checked hazards are in the punch list under
  **`#24-impassabledirs`**. (Archive line ~481 — ‼ that archived entry's headline is now wrong;
  a correction banner sits on it.)
  ‼ **Knock-on:** `tools/story-dev/probe_shoal_tide.py:364-367` **replicates the inversion**, and
  that probe produced the *"reachable spin tiles: LOW 278, HIGH 0"* figure behind the user-delegated
  **"Shoal Cave is NOT adopted"** ruling — on rooms carrying **89 live tiles**. The ruling is NOT
  being reopened here, but the number underneath it was computed with a model we now know is wrong,
  and it should be **re-derived after the fix** before anyone leans on it again.
* **KI-60** — `calculate_path` **never validates its SOURCE tile**, so a result is evidence about
  the DESTINATION only. Every probe in this project asserts the avatar's real position because of
  this. (Archive line ~513.)

## ‼‼ KI-69 — THE REGI ARC: the party order everyone "knows" is the RUBY/SAPPHIRE one (2026-08-12, decomp-verified, OPEN)
> 📎 **STUB MARKER — decomp recon 2026-08-13:**
> `ai-research-notes/2026-08-13-regi-arc-decomp-ground-truth.md`. **It is a NOTE, not truth**, but it
> contradicts this entry in four places, and two of its findings were reached INDEPENDENTLY by two
> agents with matching citations. Read it before acting on anything below.
> 1. ⛔ **REGICE IS NOT A TIMED WAIT.** R/S's wait function is an **empty stub**
>    (`braille_puzzles.c:258-261`). Emerald needs a **36-tile perimeter lap in ONE visit** ending on
>    exactly `(8,21)`; one wrong tile fails it and `OnTransition` resets it. Tiles are in the note.
> 2. ⛔ **`FLAG_REGI_DOORS_OPENED` is never read inside the tombs** — it `setmetatile`-BRICKS the
>    three OUTDOOR cave mouths (Route105/111/120 `OnLoad`). ⇒ the Sealed Chamber is a **hard serial
>    prefix**, and those patched tiles are invisible to our map model (**KI-74**).
> 3. ⛔ **`CheckRelicanthWailord` gates the SEALED CHAMBER ONLY** — no tomb calls it, so both fish
>    can be **boxed afterwards**. Minimum party for that step is 2.
> 4. ⛔ **Ancient Tomb needs NOTHING to reach** (foot-reachable, `requires_flash: false`); Flash is
>    the puzzle MOVE. Desert Ruins needs GO-GOGGLES (an item). Only Island Cave needs Surf.
> 5. ✅ **Wailmer evolves at L40 into Wailord** (`evolution.h:147`) and **Route 105 Super Rod is
>    100% Wailmer**, so the 1% wild-Wailord hunt this entry implies is unnecessary.
> ⚠ **This entry names the Route 118 Fisherman as the SUPER ROD source; a second agent says that is
> the GOOD ROD and the Super Rod is `MossdeepCity_House3`. UNRESOLVED — verify before building.**


Researched at the user's request, ahead of building Relicanth/Wailmer catch logic.

### ‼ THE ORDER IS **WAILORD FIRST, RELICANTH LAST** — and the wrong order FAILS SILENTLY
`src/braille_puzzles.c:92-104`, `CheckRelicanthWailord()`, verbatim, comment and all:
```c
// Emerald change: why did they flip it?
// First comes Wailord
if (GetMonData(&gPlayerParty[0], MON_DATA_SPECIES_OR_EGG, 0) == SPECIES_WAILORD) {
    CalculatePlayerPartyCount();
    // Last comes Relicanth
    if (GetMonData(&gPlayerParty[gPlayerPartyCount - 1], MON_DATA_SPECIES_OR_EGG, 0) == SPECIES_RELICANTH)
        return TRUE;
}
```
**Ruby/Sapphire is Relicanth-first; EMERALD REVERSED IT.** On a mismatch `VAR_RESULT` is FALSE, the
script falls to `_NoEffect`, and **nothing happens — no message, no error.** Pinned in a test
(`repro_roster_reorder.py` §3) rather than trusted to memory. Emerald flipped two more in the same
arc: **Regirock is ROCK SMASH (was Strength)** and **Registeel is FLASH (was Fly)**.

**Other conditions, exactly:** literal indices `gPlayerParty[0]` and `[gPlayerPartyCount - 1]`;
**the party need NOT be six** — a party of exactly **two** satisfies it; **species only** (no level,
nickname, OT or held item); **eggs FAIL** (`MON_DATA_SPECIES_OR_EGG`); fainted mons are fine.
‼ It is a **one-time, single-scene** requirement — once `FLAG_REGI_DOORS_OPENED` is set the two
Pokémon are never needed again and the party can be rebuilt.

### ⛔ THE HIGHEST-RISK ITEM IN THE WHOLE ARC: the Regi battle is UNRECOVERABLE
`DesertRuins/scripts.inc:57-84` and siblings: level **40**, catch rate **3**.
```
B_OUTCOME_WON  -> the Regi is REMOVED FOREVER
B_OUTCOME_RAN / PLAYER_TELEPORTED -> respawns next visit (SAFE)
fall-through (INCLUDES B_OUTCOME_LOST) -> setflag FLAG_DEFEATED_REGIROCK  -> gone FOREVER
```
⇒ **KO'ing it OR whiting out against it destroys the encounter permanently.** The only safe
non-catch exit is **fleeing**. Our battle policy must be provably incapable of KO'ing it and must
never white out there. This needs its own guard and its own test before the arc is attempted.

### ⚠ CHALLENGE TO THE WHITEOUT HALF — filed 2026-08-13, **UNVERIFIED, claim NOT yet edited**

An adversarial agent challenged the sentence above, reading `pret/pokeemerald`:
* `battle_setup.c:569-575` — `StartRegiBattle` sets `gMain.savedCallback = CB2_EndScriptedWildBattle`.
* `:618-633` — that callback branches on `IsPlayerDefeated(gBattleOutcome)`; on defeat it calls
  `SetMainCallback2(CB2_WhiteOut)` **instead of** `CB2_ReturnToFieldContinueScriptPlayMapMusic`.
* ⇒ because the defeat path **replaces the callback rather than resuming the script**, the
  fall-through `setflag FLAG_DEFEATED_REGIROCK` allegedly never runs, and
  `DesertRuins_OnTransition` re-shows the Regi on the next visit.
* ⇒ the agent's conclusion: **losing is recoverable; only KO'ing or catching is not.**

‼ **THE CLAIM ABOVE IS DELIBERATELY LEFT UNCHANGED, and here is why.** This project's own rule is
that a decomp read is a NOTE, never truth — and this is *exactly* the kind of control-flow
reasoning that has been wrong here before. It is also the **safe** direction to be wrong in: if the
challenge is right we lose nothing by being over-cautious, and if it is wrong and we relaxed the
rule, the encounter is gone forever.

**‼ THE OPERATIONAL RULE IS UNAFFECTED EITHER WAY** — never KO a Regi, never rely on losing.

**How to settle it, cheaply (~1 run):** lose to a Regi on a save state, re-enter the tomb, and check
whether the object is still there. **Only after that** may this section be edited — and the edit
should quote the observed result, not the decomp.

### The chain, and what we already have
✅ **Better than expected:** `modules/menuing.py:862` `use_field_move()` already dispatches
**DIG**, **FLASH** and **ROCK SMASH** from the party menu — all three puzzle moves are supported.
`dive()` / `surface_from_dive()` and `fish()` exist too.

| step | detail | status |
|---|---|---|
| Sealed Chamber | Route 134 → dive → Underwater R134 **(8,8)** warp → Underwater Sealed Chamber (7,1) → walk to **exactly (12,44)** → surface → Outer Room (10,19) | ‼ surfacing anywhere but (12,44) **silently dumps you back on Route 134 (60,31)** — assert the map after |
| open the inner room | stand on **(9/10/11, 3)** and use **DIG** (TM28, **no badge gate**) → `SYS_BRAILLE_DIG` | needs TM28 + a learner |
| open the tombs | Inner Room, interact with the back wall at **(9/10/11, 4)** → `CheckRelicanthWailord` → `REGI_DOORS_OPENED` | ‼ guard on the FLAG, not on "we interacted" |
| Registeel (cheapest) | Route 120 warp (7,55) → Ancient Tomb; stand on **exactly (8,25)**, use **FLASH** | recommended FIRST target |
| Regirock | Route 111 desert (needs **Go-Goggles**); stand on (5/6/7, 23), use **ROCK SMASH** | second |
| Regice | a **36-tile exact lap**; any deviation fails and needs a braille re-trigger — and the path crosses the map's own **exit warp at (8,29)** | ‼ LAST — needs a "walk this exact ordered tile list" primitive we do not have |

**Catching the two key Pokémon** (measured against our `encounter_index_BPEE0.json`):
* **RELICANTH — DIVE-ONLY, 2 entries in the whole game**: Underwater Route **124** and **126**, 5%,
  L30-35, catch rate 25. Both are next to Mossdeep. ‼ This is why Dive gates the arc.
* **WAILMER — ROD-ONLY** (39 Super Rod + 27 Good Rod entries, **zero** surf/grass). **Route 105 is
  100% on the Super Rod at L20-45** — and Route 105 is also where Island Cave (Regice) is.
* **WAILORD evolves from Wailmer at L40 by level-up.** ‼ Evolution fires on GAINING a level, so a
  caught L42 Wailmer is still a Wailmer — **catch at ≤39 and level once**. Direct Wailord exists
  (Route 129 Surfing) at **1%** — too rare to plan on.

**No badge/E4/story gate exists on the arc** — every real gate is traversal capability.

### ✅ PHASE A MEASURED 2026-08-12 — `probe_regi_capabilities.py` on `post_dive.ss1`
The four "cheap unknowns" are now answered, and the acquisition list is **longer** than hoped:

| | capability | note |
|---|---|---|
| ✅ | **Go-Goggles in bag** | Regirock's desert gate is already open |
| ✅ | **HM08 in bag** | the Dive HM itself |
| ✅ | **Surf known** — Zigzagoon (slot 1) | reaches Routes 105/120/124/126/134 |
| ✅ | **Rock Smash known** — Sceptile (slot 0) | Regirock's puzzle move |
| ⛔ | **NO ROD AT ALL** — `RECEIVED_SUPER_ROD` **and** `RECEIVED_GOOD_ROD` both unset | ‼ Wailmer is ROD-ONLY, so **Wailord is currently unobtainable**. The Super Rod is the Fisherman on **Route 118** (needs Surf — we have it) |
| ⛔ | **TM28 Dig** — flag unset AND not in bag | the Sealed Chamber inner room cannot be opened. Route 114, Fossil Maniac's house, unconditional gift |
| ⛔ | **Nobody knows DIVE** | HM08 is in the bag but unlearned — and KI-63 still blocks teaching it (no learner, party 6/6) |
| ⛔ | **Nobody knows DIG** | needed even once TM28 is obtained |
| ⛔ | **Nobody knows FLASH** | Registeel's puzzle move |
| ⛔ | **No Wailord / Relicanth / Wailmer** | the two key species are not aboard |

All eight arc progress flags are **unset**, as expected — nothing has been started or spoiled.

⇒ **The Regi arc needs an ACQUISITION PHASE before any of its puzzles are reachable**, and all of it
is ordinary story-bot work (walk there, take the item, teach the move) rather than new primitives:
1. **Super Rod** (Route 118) — without it there is no Wailmer, no Wailord, no tomb.
2. **TM28 Dig** (Route 114) and teach it.
3. **Teach Dive** — ‼ still gated by KI-63/KI-68: no party member can learn it, the party is full,
   and the planner cannot auto-route a dive anyway (a chapter must drive `dive()`).
4. **Teach Flash** (Registeel only).
‼ Note the ordering trap: **Relicanth lives ONLY underwater**, so Dive must work before the key
party can even be assembled — Dive is upstream of everything else in this arc.

⚠ Reachability of Route 118, Route 114, Route 105, the desert and the tomb islands is a **separate,
DRIVEN question**. This probe answers "do we have it", never "can we get there".
⚠ **Unverified claim worth probing:** the tomb scripts appear not to check `FLAG_REGI_DOORS_OPENED`
at all (only their own puzzle flags), which would mean the tombs are solvable without the Sealed
Chamber. That contradicts common knowledge — **sequence the Sealed Chamber first regardless.**

## KI-66 — the multi-battle hazard is BROADER than the faint chooser (2026-08-12, code-verified, OPEN — ✅ except the turn-1 IndexError sub-claim, REFUTED 2026-08-12; the other four scans are still unguarded)

Filed from the adversarial review of the finished §Ch19. KI-64 fixed the three *faint* choosers; the
review found **four more party scans** on the same battle's paths that still have no partner concept.
None is fixed, and none has ever run live (every §Ch19 drive had zero faints).

| site | what it does wrong |
|---|---|
| `battle_handler.py:541-545` | the `new_lead_index is None` fallback scans the FULL party — and KI-64's guard makes `None` *more* likely, so it feeds this |
| `battle_handler.py:588-598` | full-party revalidation that writes a **party-order** index into a variable used as a **menu-order** index at `:600` (the KI-34 shape) |
| `battle_handler.py:630-636` | `alive_slots` excludes only the on-field pair, so the ally's benched mons are A-press candidates; each refusal round-trips `Task_ReturnToChooseMonAfterText` — three of six slots are guaranteed-refused in this fight |
| `_util.py:522-587` `get_potential_rotation_targets` / `select_rotation_target` | full-party, called live here from `default.py`; the result reaches `battle_action_selection.py:288`, an **unbounded** `while get_game_state() == PARTY_MENU: press A` |

✅ **REFUTED 2026-08-12 — the `IndexError` on turn 1 does not happen.** The review flagged
`decide_turn_in_double_battle` (`default.py:240-241`) doing `get_party()[partner.party_index]` with
an index of 3-5 while `gPlayerPartyCount` might still be 3, which would have fired on the FIRST turn
rather than on a faint. Refuted by our own driven run: `ch19d.log` f23255 shows `battle_is_active ->
True` with a **six-entry** party (`Sceptile|Mightyena|Swellow|Metang|Skarmory|Aggron`), and the
multi battle was won. `FillPartnerParty` does update the count in practice, so the index is in range.
‼ Worth stating because it is the one item on this list that would have broken §Ch19 in production
rather than merely on an error path — and it is the reason to check a "would fire immediately" claim
against an existing log before scheduling work for it.

**The right shape of the fix** is one choke point — `ally_party_indices()` already exists — rather
than a guard per call site. That is a battle-layer refactor touching every mode, so it is filed
rather than done.

## KI-67 (original 2026-08-12 filing) — MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-13)

✅ **KI-67 is FULLY CLOSED** — the closing write-up (the first driven whiteout recovery in this
project) is below. The original filing was archived on 2026-08-13 for the R3 3,000-line budget.
Keep only this: **a type-only guard cannot see an abort that an inner loop already replaced with a
fresh error** — hence `StoryAbort` plus the latch-keyed `reraise_if_aborting`.

---

## KI-67 — ✅✅ FULLY CLOSED 2026-08-12 (the FIRST DRIVEN WHITEOUT RECOVERY here) — FULL ENTRY MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-15)

Moved on the R3 line budget when KI-79/KI-80 were filed; it is CLOSED and was 77 lines of a
CURRENT-STATE file. ‼ **Keep only what later work leans on:** the proof was the **FRAME DELTA**
(+7,789 / +7,087), **not** a count — a whiteout recovery that changes no count still moves the
clock; and the archived text's real value is its harness DESIGN NOTES (the four parts a driver
must mirror, and **why half a mirror is worse than none**). ⚠ Still open there: ~48 swallow sites
in `early_game.py` that should get the same one-line abort-aware guard, **enforced by an assert
rather than by prose**.

## KI-65 — the HM-refusal re-pick raises `UnboundLocalError` into a silent `except` **WHEN `_read_offered_move` HAS ALREADY FAILED**, so two invisible failures compound into a silent decline (2026-08-12, code-verified, OPEN)

> ⛔ **HEADER CORRECTED 2026-08-16 (P2).** It read *"the HM-refusal re-pick has NEVER executed"* —
> which **this entry's own CORRECTION section, written the same day it was filed, calls too strong**
> and refutes: on an ordinary teach, branch (2) binds `party_index` at `:371` BEFORE the game can
> refuse, so the re-pick DOES run. The header outlived its own retraction by four days and is the
> half a skimmer reads. ‼ *An entry that corrects itself in the body must correct its TITLE in the
> same edit.*

Found by running **pyflakes** over the build for the first time (see `14-AGENT-PLAYBOOK.md`).

`modules/battle_move_replacing.py:280`, inside `handle_move_replacement_dialogue`:
```python
if state == LearnMoveState.CantForgetHM:
    ...
    try:
        _mv = get_party()[party_index].moves      # <-- party_index
        ...  # re-pick a slot the game has NOT refused
    except Exception:
        move_to_forget = 4                        # decline
```
`party_index` is a **function-local assigned only at line 371** (`move_to_learn, party_index =
_read_offered_move(...)`), far below this branch. If `CantForgetHM` is reached before that
assignment has run in this generator's life, line 280 raises **`UnboundLocalError`** — which the
surrounding `except Exception` converts into `move_to_forget = 4`, i.e. **decline**.

**Why this is bad rather than merely untidy.** Declining is a *legal* outcome, so the failure is
invisible: the run looks like it made a decision. The whole point of that block — its own comment
says *"Without the second [learning from the refusal], dismissing just returns to the move list with
the same doomed pick and the loop is infinite"* — is the re-pick, and the re-pick is exactly what
never happens. This is the playbook's named pattern **"a fail-safe `except` that returns the SUCCESS
value"**, and the guard is not protecting anything.

‼ **Candidate cause for the REOPENED `#24-teachmsgstall`**, which is currently characterised as
*"there is another path to `post_select=exhausted`"*. This is a path to a silent decline in the
teach flow. **Not yet fixed and not yet proven to be that path** — it needs its own repro (force
`CantForgetHM` and assert the re-pick runs) and an A/B, which is the honest next step rather than
assuming the connection.

**Severity:** MEDIUM, order-dependent (on iterations where line 371 already ran, the name is bound
and the branch works), which is also why it has survived unnoticed.

## ‼ KI-65 CORRECTED 2026-08-12 (same day) — my first description OVERSTATED it

I originally wrote that the re-pick *"has quite possibly never executed"*. **That is too strong, and
an inaccurate issue is worse than none.** Reading the control flow properly:

`party_index` is assigned at line 371 inside branch **(2) `AskWhetherToLearn`** — the "Delete a move
to make room for X?" prompt — which in the normal sequence runs BEFORE a slot is confirmed and
therefore before the game can refuse with `CantForgetHM`. So on an ordinary teach the name IS bound
and the re-pick DOES run.

**The real, narrower bug:** line 371 sits inside a `try:` whose `except Exception:` (line 377-381)
silently defaults `move_to_forget` when `_read_offered_move` fails. On that path `party_index` is
**never bound**, so a later `CantForgetHM` raises `UnboundLocalError` into the *second* silent
`except`, which declines. ⇒ The two failures COMPOUND: the read failed invisibly, and then the
recovery from the refusal failed invisibly too. Both look like decisions.

**Why it still matters and is still filed:** it is a real latent `UnboundLocalError` on a real path,
it is exactly the "fail-safe `except` that returns the SUCCESS value" pattern, and it is the reason
the pyflakes gate cannot yet be widened past the story surface. **Fix deliberately deferred** to a
focused pass with its own repro (force `_read_offered_move` to fail, then force `CantForgetHM`, and
assert the re-pick either runs or says loudly that it cannot) — changing the teach flow without that
repro is how `#24-teachmsgstall` got its current "the fix had no production effect" verdict.

‼ **Method note for the next agent:** this correction came from reading the ENCLOSING control flow
rather than the flagged line. A linter tells you a name is not provably bound; it does not tell you
how often that happens. Do not convert a static warning into a severity claim without tracing who
assigns it first.

---

## KI-70 — `_rotate_lead_safely` returns an avatar that may not be controllable yet; its callers walk immediately (2026-08-13, MEASURED n=1, severity: LOW-but-hot-path, OPEN, deliberately NOT fixed)

- **Where.** `modules/story/early_game.py:1619-1638`. Note the asymmetry: the **failure** path
  settles (`:1637` `wait_until_truly_controllable()`), the **success** path (`:1629-1630`
  `if ok: return`) does not. The pre-drive settle at `:1622-1624` is conditional on a field script
  being active, so it does nothing here.
- **Why it matters.** `_rotate_lead_safely` runs **every training round** — the hottest path in the
  bot — and its callers navigate on the very next statement:
  `early_game.py:1835-1843` (`do_rustboro_gym` → `navigate_to_anywhere`), `early_game.py:2028`
  (`train_team`), and seven `_lead_best_matchup` sites in `story_mode.py` (2977/3153/3187/3286/
  3351/3402/3528). `walking.py:178-179` raises
  `BotModeError("The player avatar is currently not controllable. Cannot navigate.")`.
- **How it was found.** NOT by a failure. It was found by the adversarial review of the
  `reorder_party` fix (2026-08-13) — the same defect shape, one function over.
- **‼ MEASURED, AND THE MARGIN HELD: `controllable_on_return=True`.**
  `--driver roster` PHASE 6 calls `_rotate_lead_safely(2)` and reads
  `player_avatar_is_controllable()` **on the frame it returns**, which is exactly what its callers
  do. Transcript in `ai-research-notes/2026-08-13-roster-drive-predictions.md`.
- **⚠ n = 1. One observation on one save is not a rate.** This project has made precisely that
  error before (the 64.3% status-tax figure from n=2 that a real batch cut to 32.6%).
- **WHY IT IS NOT FIXED, and what would change that.** An unconditional settle costs ~30 frames
  (`wait_until_truly_controllable`'s `stable_frames` floor) per rotation on the hottest path, to
  fix something never observed failing. But the reason it survives is a **margin, not a
  guarantee**: `change_lead_party_pokemon` ends with `wait_for_task_to_start_and_finish(...)` +
  `wait_for_n_frames(10)` (`higher_level_actions.py:309-310`), whereas the `RotatePokemon` /
  `PartyMenuExit` path exits on the strictly weaker *"OVERWORLD and start menu closed"*
  (`menuing.py:807-808, 833`). ⇒ **Fix it if a batch ever logs "currently not controllable" right
  after a lead rotation**, or if `change_lead_party_pokemon`'s tail is ever shortened. Until then
  the honest status is *structurally present, measured once, margin held*.
- **Contrast with the fixed case.** `modules/story/roster.py`'s `reorder_party` had the identical
  shape and DID fail live, because `PartyMenuExit`'s weaker exit condition gives it no margin at
  all. Fixed 2026-08-13 with a `swapped`-gated `_settle()`; A/B proven.

---

## KI-71 — `roster.py`'s "we were dropped to MANUAL" guard is UNREACHABLE mid-swap: the frame loop abandons the generator first (2026-08-13, code-verified, OPEN)

- **The guard.** `modules/story/roster.py` raises `BotModeError("Roster: the party-menu navigator
  dropped the bot to MANUAL mid-swap ...")` after the bounded `RotatePokemon` drive, specifically
  so a run that is already dead fails honestly instead of continuing.
- **Why it cannot fire.** `modules/main.py:145-148`:
  ```
  if context.bot_mode == "Manual":
      context.controller_stack = []
  if len(context.controller_stack) > 0:
      next(context.controller_stack[-1])
  ```
  `set_manual_mode()` only sets a flag — it raises nothing and crosses no yield boundary. So the
  in-flight `next()` returns normally, and on the **next** frame the stack is cleared and the
  suspended `reorder_party` generator is **abandoned, never resumed**. The guard sits after a
  multi-frame `yield from`, so it is only reachable if the whole drive completes inside the single
  `next()` that flipped the flag — which it cannot. ‼ `tools/story-dev/story_harness.py` mirrors
  this (its run 1 log printed `gen -> <no controller on the stack (Manual mode / dropped out)>`).
- **The trapdoors that reach it.** `menu_parsers.py:164-166` (`slot_id == -1`), `menuing.py:365`
  (`wait_for_init`), `:381` (`get_index_from_option`), `:388` (`select_desired_option`). All four
  call `set_manual_mode()` and **return/continue without raising** — the KI-38 family.
- **What it looks like.** No exception, no non-zero exit, no crash. The process idles healthily in
  Manual until something else declares a hang. The `menuing.py` message is printed; roster.py's
  own diagnostic never is.
- **‼ NOT OBSERVED IN THE FIRST DRIVE.** Six swaps, zero Manual drops, `slot_id` never read `-1`.
  This is a structural finding from reading `main.py`, not a reproduction.
- **What a fix looks like** (not attempted): the guard has to be *inside* the frame loop's reach —
  e.g. a listener, or having the trapdoors raise instead of silently setting Manual. That is the
  real KI-38 fix (`#24-menutext`) and should not be bolted onto roster.py alone.

---

## KI-72 — `calculate_path` cannot see the two tile types you CANNOT SURFACE FROM, so it will happily route a dive to a dead end (2026-08-13, code-verified, OPEN, ARMED for §Ch20 — the SEAFLOOR CAVERN; older text in the body says "§Ch21" and means Chapter 20, per the naming correction — and the Regi arc)

- **The measurement** (verified directly, one grep):
  ```
  grep -rn "Underwater Blocked Above|Seaweed No Surfacing" modules/ --include=*.py
    modules/map.py:103                              -> "Underwater Blocked Above"
    modules/map.py:131                              -> "Seaweed No Surfacing"
    modules/modes/util/higher_level_actions.py:718  -> the ONLY consumer
  grep -n "Underwater Blocked Above|Seaweed No Surfacing" modules/map_path.py
    (nothing)
  ```
  The tile reader emits both names; **`surface_from_dive()` is the only code in the tree that
  looks at them**; and `map_path.py` — the pathfinder — has never heard of either.
- **Consequence.** `map_path.py:279-280`'s generic fallback marks any tile_type it does not
  special-case as `accessible_from_direction = [True, True, True, True]`, at ordinary cost. So an
  underwater tile you can never surface from is, to the planner, plain open water — a perfectly
  good place to end a route.
- **The failure.** A chapter navigates underwater to a planner-chosen destination, calls
  `surface_from_dive()`, and gets
  `BotModeError: This tile does not allow surfacing from a dive.` (`higher_level_actions.py:718-719`).
  ‼ It fails **loudly**, which is the good news. The bad news is the retry shape: re-running the
  same `navigate_to` re-derives the same destination, so a naive retry loop cannot converge — the
  KI-67 shape (signal something, retry without changing state).
- **‼ THE DESIGN RULE THAT FOLLOWS — NEVER LET THE PLANNER CHOOSE WHERE YOU SURFACE.**
  Upstream already does the right thing without saying why: `puzzle_solver.py:203-204` navigates to
  a **hand-picked** `UNDERWATER_SEALED_CHAMBER (12, 44)` and surfaces *there*. Copy that pattern —
  pick the surface tile explicitly, and assert its `tile_type` before calling
  `surface_from_dive()`, exactly as `dive()` already asserts deep water before diving.
- **How it was found.** An adversarial pre-build pass on the §Ch21 dive plan, before any code was
  written. Not by a failure. **This is a DIFFERENT bug from KI-59** (which over-blocks
  `Impassable *`); this one under-blocks a type the planner does not model at all.
- **Not fixed, and why.** Fixing it properly means teaching `map_path.py` a new blocked-destination
  concept ("you may cross this tile but may not END on it"), which is a real change to shared
  pathfinding that every mode depends on. The design rule above costs nothing and removes the
  hazard for the work actually in front of us. ⇒ Revisit if a chapter ever genuinely needs the
  planner to pick a surfacing point.

---

## KI-73 — the map-layout cache is keyed on MAP NUMBER, but Shoal Cave swaps its floor plan at runtime, so the planner can route against a layout that is not on screen (2026-08-13, code-verified, OPEN)

- **The mechanism**, `modules/map.py:735-755`:
  ```python
  _map_layout_cache: dict[str, dict[tuple[int, int], bytes]] = {}
  ...
  @cached_property
  def _map_layout(self) -> bytes:
      if self.map_group_and_number not in _map_layout_cache[context.rom.id]:
          map_layout_pointer = unpack_uint32(self._map_header[:4])
          _map_layout_cache[context.rom.id][self.map_group_and_number] = \
              context.emulator.read_bytes(map_layout_pointer, 24)
      return _map_layout_cache[context.rom.id][self.map_group_and_number]
  ```
  The cache key is **`(rom.id) → (map_group, map_number)`**. Nothing in the key represents *which
  layout is currently loaded*.
- **Why that is wrong for Shoal Cave.** The entrance room is always map **(24,46)** at both tides;
  the high-tide "maps" (24,50)/(24,51) exist only to **own a layout** that `setmaplayoutindex`
  borrows onto (24,46). So the map NUMBER is constant while the FLOOR PLAN changes — exactly the
  thing this cache assumes cannot happen.
- **The failure.** Visit at low tide → the low-tide plan is cached. Return at high tide → every
  `MapLocation` for (24,46) still returns the **low-tide** plan. `calculate_path` then routes
  across tiles that are now water or wall. Measured scale of the difference (from KI-54): the room
  has **332** walkable `MB_CAVE` encounter tiles at low tide and **65** at high.
### ‼‼ ESCALATION — IT IS NOT "WHICHEVER TIDE YOU SAW FIRST". IT IS **ALWAYS LOW TIDE, FOREVER.**

`get_map_data` (`map.py:1756-1785`) builds `_map_header_cache` **once, for every map in the game**,
by walking the **static compile-time `gMapGroups` ROM pointer table**:
```python
map_group_pointers = read_symbol("gMapGroups", size=4 * number_of_map_groups)
...
map_header_pointer = unpack_uint32(context.emulator.read_bytes(group_pointer + 4 * map_index, 4))
map_header = context.emulator.read_bytes(map_header_pointer, 0x1C)
```
That table can only ever yield the **compiled DEFAULT** header for (24,46) — whose layout pointer is
the **low-tide** floor. `setmaplayoutindex` patches the **live `gMapHeader` RAM struct**, which this
table never reads. And it is populated on the FIRST `get_map_data` call anywhere in the process —
`PathMap.tiles` (`map_path.py:85-94`) calls it — so it is warm long before Shoal Cave is visited.

⇒ **`get_map_data(SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM, …)` returns low-tide geometry at BOTH tides,
always.** There is no `.clear()` on `_map_layout_cache` or `_map_header_cache` anywhere in
`modules/`.

> ### ⚠ CORRECTION 2026-08-13 (same day) — I OVERSTATED THIS. The mechanism is CACHE POISONING.
> A live measurement (`probe_shoal_tide.py`) refuted the "always low tide, forever" framing:
> **`get_map_data_for_current_position()` (`map.py:1750`) reads the LIVE `gMapHeader` and therefore
> DOES follow `setmaplayoutindex`.** Only `get_map_data(map, coords)` (`:1756`) is locked to the
> static ROM header.
> ‼ **The real defect is that BOTH write the same `_map_layout_cache`, keyed only on
> `(group, number)` — so the FIRST WRITER WINS for the whole session, silently.** A static plan made
> before entering poisons the live read afterwards, and vice versa. That is still a real bug and
> still unfixed; it is just narrower and stranger than "always low".

⇒ ‼ **AND `calculate_path` WILL NOT RAISE.** It plans happily over the wrong grid and returns a
route that walks the bot onto tiles that are water or wall in the live room. **Invisible to a run
that reports success** — the failure surfaces as bumping, stalling, or a nonsensical stall dump.

⇒ ‼‼ **THEREFORE KI-54's OWN "65 walkable tiles at high tide" FIGURE IS SUSPECT.** It was almost
certainly measured through this same lens, i.e. it is very likely a second view of the **same
low-tide layout** rather than an independent measurement of the high-tide floor. **We do not
currently know the high-tide geometry of that room.** (Found by an adversarial pass that was asked
to refute "the tide is not a blocker"; the static-table half verified by me directly.)

- ‼ **It is a STALE-CACHE bug, not merely a static-data bug.** `05-KNOWN-ISSUES` previously
  described this as *"`MapLocation` resolves the layout from the cached ROM map header, i.e. always
  the LOW-tide floor plan"*. That understates it: the value is whatever was cached **first, in this
  process**, so the direction of the error depends on which tide the bot happened to visit first,
  and it persists for the rest of the run.
- **Scope.** Any map whose layout is swapped at runtime. Shoal Cave is the case in front of us;
  a sweep for other `setmaplayoutindex` users has NOT been done.
- ‼ **CODE-VERIFIED, NOT REPRODUCED.** No run has yet driven the bot into that room at both tides.
  Filed so the next reader does not re-derive it, and so the Shoal Cave decision has a reason with
  a citation rather than a worry.
- **What a fix looks like** (not attempted): include the live layout pointer in the cache key, or
  invalidate the entry on map-transition. Both touch shared pathfinding that every mode depends on,
  so it needs its own A/B — not a drive-by change.

## KI-78 — ⛔ **PERSONALITY VALUE IS NOT A UNIQUE IDENTITY IN GEN 3: a SHEDINJA carries the SAME PID as the NINJASK it came from** — and this codebase keyed "which mon do I act on" off exactly that (2026-08-14, DECOMP-VERIFIED — ✅ **FIXED IN BOTH FORKS (Stage 1, promoted 2026-08-14) — ⚠ RESIDUAL CASES REMAIN OPEN**)

> ✅ **STAGE 1 LANDED 2026-08-14 — the party/box identity lookups now key on `(personality,
> species)`** via the shared `modules/pokemon.same_pokemon` predicate. A/B proven by
> `tools/story-dev/repro_pid_identity_key.py` (gate #20), which builds a **real** twin pair with
> genuine Gen 3 substructure encryption: the OLD PID-only rule, asked for the SHEDINJA, returns
> the **NINJASK's** slot; the shipped rule returns the right one. Fault-tested both ways — revert
> the fix and the gate goes red on exactly that check.
> ✅ **PROMOTED TO `custom-pokebot` 2026-08-14** (user-approved; the FIRST promotion executed
> through `tools/story-dev/promote.py` rather than by hand). Verified IN THAT FORK by
> `repro_pid_identity_key.py --build custom` → exit 0, which **asserts which fork it imported**
> before testing anything, plus a live drive. Superseded: *"custom-pokebot has the detection
> warning but not the fix — the wrong-target release is still live there."*
> ⛔ **The residual cases below are NOT closed by Stage 1** — see "Residual collisions".

- **Why this is severe.** This project's standing rule — written into `CLAUDE.md`'s SESSION
  DISCIPLINE as rule 3 — is *"Assert IDENTITY, never position or count. PIDs — never slot
  indices."* **That remedy has a hole, and this is it.** PID is the identity key we reach for
  precisely when a count would lie, so a PID collision defeats the fix and the prevention rule at
  the same time.
- **The mechanism, verified against the decomp (not recalled).** `CreateShedinja`
  (`src/evolution_scene.c:548-583`) does `CopyMon(&gPlayerParty[gPlayerPartyCount], mon,
  sizeof(struct Pokemon))` — a plain `memcpy` (`src/pokemon.c:4420-4423`) — and then overwrites
  species, nickname, held item, markings, the encrypt separator, ribbons, status and mail.
  **`MON_DATA_PERSONALITY` is NOT among them.** OT ID is likewise inherited. ⇒ Ninjask and
  Shedinja are PID-identical and OT-identical for their whole lives.
- ‼ **AND THE TRIGGER IS MORE COMMON THAN OUR OWN CODE CLAIMS.** In Gen 3 the ONLY precondition
  is `gPlayerPartyCount < PARTY_SIZE` (`evolution_scene.c:551`) — **there is no spare-Poké-Ball
  requirement**; that rule is Gen 4+. Our `modules/obtainability.py:88` display string says
  *"level up (empty slot + spare Ball)"* and **is wrong for this ROM**. Any Nincada reaching L20
  with one free slot spawns a Shedinja.
- ⛔ *(SUPERSEDED 2026-08-15 — Stage 1 was PROMOTED on 2026-08-14, so nothing below is 'sandbox
  only' any more; the fix is in BOTH forks and drift is 0. The residual R2/R3/R5/R6 cases named in
  the header are what remain open.)* **Where it WAS armed — the first two are FIXED by Stage 1, was
  then still armed in
  `custom-pokebot`. The rest are untouched and remain PID-only ON PURPOSE:**
  * ✅ `modules/pokemon_party.py` `Party.get_index_for_pokemon` — **now matches via
    `same_pokemon` (personality AND species)**, with the R6 handling below. It used to match
    `data[:4]` alone and return the first hit, which is **the function that decides WHICH PARTY
    SLOT a PC action operates on** — the whole hazard.
  * ✅ `modules/pokemon_storage.py` `contains_pokemon` — was PID-only; now on `same_pokemon`.
    Its neighbour `get_slot_for_pokemon` was **already** composite and is refactored onto the
    shared predicate so the pair cannot drift apart again. ⚠ `contains_pokemon` has **zero callers
    today**, so its correctness is proven by routing, not by a behavioural A/B.
  * ⚠ `modules/modes/util/pc_interaction.py:464` (`_do_deposit_actions`) and **`:505` (RELEASE)**
    resolve their target through `get_index_for_pokemon`, so they inherit the fix in sandbox and
    **remain exposed in `custom-pokebot`.** ⛔ One branch of that lookup **releases a Pokémon
    permanently.**
  * ⛔ **DELIBERATELY LEFT PID-ONLY — do not "fix" these:** `modules/story/pc_trip.py:384-400`
    `find_in_box(pids)` and the protected-counter PID set at `:136`;
    `modules/story/early_game.py:1655-1656`'s `_hunted_counter_pids` matching. These mean *"do not
    touch anything in this family"*, and a twin SHOULD inherit its sibling's protection — widening
    is the safe direction, narrowing is not.
- ‼ **R6 — THE NEW FAILURE MODE STAGE 1 INTRODUCES, AND HOW IT IS HANDLED.** A mon that EVOLVES
  between the caller capturing its object and the lookup running no longer matches on species.
  Rather than abort a working flow, a **unique** PID hit whose species disagrees is **re-resolved
  from the live party and reported LOUD**; a species miss with two or more PID hits **RAISES**,
  because the caller may be about to release something. ⛔ It must NEVER fall back to "the first
  PID match" — that is the original bug. Both branches are asserted by the gate.
  ⚠ **Unexercised by any live caller today:** every current caller re-captures its target
  immediately before entering the PC menu, with no encounter-capable movement in between. It is
  defensive coding, and knowing it is untested by a real flow is part of the record.
- ✅ **One place it is NOT a problem, by luck rather than design:** `counter_hunt._stop()`'s new
  identity test (fixed 2026-08-14) *wants* the twins to share a PID — a Shedinja spawn then cannot
  look like a new catch, which is the correct answer. Do not "fix" the collision in a way that
  breaks that.
- **What a fix looks like:** key on **`(personality, species)`** wherever a PID selects a target
  for an ACTION. ⚠ Not a drive-by change — `get_index_for_pokemon` is shared by deposit, release
  and the party menu, and the release path is destructive. Needs its own fault-injected A/B with a
  fabricated twin pair.
- ✅ **THE COMPOSITE KEY IS NOT A NEW IDEA HERE — HALF THIS CODEBASE ALREADY USES IT.**
  `modules/pokemon_storage.py:128` (`get_slot_for_pokemon`) already matches
  `data[:4] == data[:4] AND species.index == species.index`. Its neighbour `:121`
  (`contains_pokemon`) and the party-side `get_index_for_pokemon` simply never got it. ⇒ frame the
  change as a **CONSISTENCY FIX**, which is the cheapest possible framing for review.

### ‼ RULED 2026-08-14 — key on **SPECIES**, never on the NAME. And the intuitive reason is WRONG.

The user proposed `(PID, name)`, reasoning that the bot never renames. An investigation fetched the
decomp live to settle it, and **refuted the objection that had been raised against the idea**
(mine: *"a default nickname is probably stale after evolution"*):

* ⛔ **THE NICKNAME IS NOT STALE. `EvolutionRenameMon` (`src/pokemon.c:5814-5821`) rewrites a
  DEFAULT nickname to the new species name on evolution**, and it runs at
  `src/evolution_scene.c:766` — **before** `CreateShedinja` at `:814`. Shedinja's own nickname is
  then set unconditionally (`:558`). So the Ninjask reads `"NINJASK"`, the Shedinja `"SHEDINJA"`,
  and **for this specific pair a name-based key WOULD have worked.** Cross-checked against
  `pret/pokefirered` — this is vanilla Gen 3, not a pret modernisation.
* ✅ **SPECIES still wins, for a stronger reason: NAME is species re-encoded as text.** Because
  `EvolutionRenameMon` keeps default-nickname and species-name in lockstep, the name carries
  **zero information species does not already carry** — it is not a second axis of discrimination,
  it is a lossy copy of the first, with its own failure modes:
  - **every EGG shares ONE nickname** — `sJapaneseEggNickname` (`src/daycare.c:838-841`), and our
    reader takes the RAW bytes (`modules/pokemon.py:1000`), so all eggs collapse to one string;
  - **the nickname CHANGES for the same physical mon at hatch** (`src/egg_hatch.c:372-373`) — the
    same PID and species, a different name before and after, so `(PID, name)` is unstable across
    an event `(PID, species)` sails through;
  - **in-game trades ship preset nicknames** (`"DOTS"`, `"PLUSES"`, `"SEASOR"`, `"MEOWOW"` —
    `src/data/trade.h`) which never match an old species name and so **never update on evolution**;
  - `language != GAME_LANGUAGE` **disables the rename entirely** (`pokemon.c:5819`).
* ⛔ **AND "the bot never renames" is true only by a hair.** Every gameplay path declines the
  naming screen (`battle_handler.py:876-881`, `_listeners.py:455-465`, `static_gift_resets.py:195-207`,
  `starters.py:62,182`, `early_game.py:1041`, `game_corner.py:125`) — but `starter_nickname` is
  **already wired end to end** (`modules/story/config.py:18,27-32`, a random pool at
  `early_game.py:998-1007`) and short-circuited by one hard-coded `"No"`, `on_should_nickname_pokemon`
  is a sanctioned plugin hook (`plugin_interface.py:196-205`), and the debug utilities/GUI set names
  like `"Hulk"`, `"Ability"` and **`"CHEAT"`** (`debug_utilities.py:551-616,653-666`,
  `gui/debug_menu.py:187-206`, `gui/debug_edit_party.py:199`).
  ⇒ **Keying a DESTRUCTIVE path on a field the project is one uncommented `if` away from making
  arbitrary is a design error regardless of the decomp.**

### ⛔ THE CALL SITES THAT MUST **NOT** GET THE SPECIES COMPONENT

**`counter_hunt.py`'s PID SETS DEPEND ON THE TWINS SHARING A PID** — `_party_pids_now` /
`_box_pids_now` and the set-difference in `catch_confirmed` (`counter_hunt.py:311-342`). That fix
(2026-08-14) works *because* a Shedinja carries its Ninjask's PID and therefore cannot look like a
NEW identity. **Adding species there would make a Shedinja spawn report a catch that never
happened — reintroducing the exact bug that code was written to fix.** Likewise leave the
protected/hunted PID *sets* alone (`pc_trip.py:136,446`, `early_game.py:1769`,
`higher_level_actions.py:245-247`): those mean "don't touch anything in this family", and a twin
SHOULD inherit its sibling's protection — widening is the safe direction, narrowing is not.

### Residual collisions after the fix (name them, do not claim uniqueness we lack)
* **R2 — debug paths** (`debug_utilities.py:314-410`, `gui/debug_edit_party.py:199`) can fabricate
  two identical-PID identical-species mons by hand ⇒ the key must **detect** ambiguity, not assume
  it away.
* **R3 — corrupt/Bad-Egg box slots** read PID 0 / species 0; the box reader filters only on
  `is_empty` (`pokemon_storage.py:101`) where the party reader also checks `is_valid`
  (`pokemon_party.py:120`).
* **R5 — Battle Frontier rentals** overwrite `gPlayerParty`; a pre-entry PID is then simply absent
  (a miss, not a mis-hit). No bot code enters the Frontier.
* **R6 — a NEW failure mode the change introduces:** if a mon evolves between object capture and
  key use, the composite key **misses** where PID-only would have hit — converting a silent
  wrong-target into a loud abort. Correct for RELEASE; a behaviour change everywhere else.
  ⇒ On a species mismatch with a unique PID hit, log LOUD and **re-resolve from the live party**;
  raise only on genuine ambiguity, and NEVER fall back to the first PID hit.
- **Cheap detection meanwhile:** a duplicate-PID check over the party would flag the condition in
  one line, and it is worth logging LOUD when it fires, because every PID-keyed decision taken
  while it holds is suspect.

## KI-77 — `get_map_objects()` is a CAMERA-RANGE WINDOW, so the planner's picture of a PUSHED BOULDER flips with the camera (2026-08-13, MEASURED LIVE, OPEN — ⛔ **NOT armed in Room 8; the LARGE rooms are the risk**)

> ‼ **THE HEADLINE USED TO SAY "ARMED for §Ch20 Room 8" AND THE BODY BELOW REFUTES IT.** Room 8 is
> 11x14 and the despawn window is 20x17 — the map is *smaller than the window*, so nothing can
> despawn there except on the arrival tile, before any push. Room 8 is the next thing to build, so a
> reader skimming issue headers would have built a guard that measurement already ruled out. Fixed
> in the header 2026-08-13; **the rule is that the headline carries the caveat.**

- ✅ **THE WINDOW MODEL IS CONFIRMED IN A SECOND ROOM, 2026-08-14 (`--driver ch20room8`, both
  runs, PRE-REGISTERED as prediction P3 before the drive):** standing on `ROOM8 (5,12)` the dump
  returned **exactly 8 of the room's 12 boulders** — the four `y=4` templates fall outside
  `y ∈ [12-7, 12+9]` — and from the staging tile `(5,8)` all 12 are visible. The derived window
  has now predicted live dumps in Rooms 1 and 8 without a miss. ‼ The physical-reset question
  below is STILL unanswered: the ch20room8 recovery handler exercised the *map re-entry* respawn
  (`FLAG_TEMP_*`, a different mechanism), not the despawn-window reset.
- ⛔ **CORRECTED 2026-08-13, SAME DAY IT WAS FILED — MY FIRST FRAMING WAS TOO STRONG, AND THE REAL
  DEFECT IS WORSE BUT DIFFERENT.** I wrote *"a route planned in that state is planned against a map
  that does not exist"*, implying the planner can be permissive. **It cannot.** A decomp pass
  established that `RemoveObjectEvent` (`src/event_object_movement.c:1383`) only sets
  `active = FALSE`, and **nothing on the push path ever writes the boulder's new position back to
  `gSaveBlock1Ptr->objectEventTemplates[]`** (`OverrideTemplateCoordsForObjectEvent` `:2478` is
  reached only from the `copyobjectxytoperm` macro and from `trainer_see.c`), while
  `TrySpawnObjectEvents` respawns from `template->x/y`. ⇒ **THE GAME ITSELF RESETS A PUSHED BOULDER
  TO ITS ORIGINAL TILE WHEN IT SCROLLS OUT OF RANGE.** So the planner's "despawned ⇒ block the
  template tile" rule is **fail-safe and CORRECT on respawn**; it over-blocks only during the
  despawn window itself, and never under-blocks.
  ‼ **The real hazard is the PHYSICAL reset:** any route that pushes a boulder and then travels far
  enough for it to despawn **loses the push in the game**, not merely in the model. Fix the planner
  for this and you would be fixing the wrong thing.
  ⚠ **DECOMP-DERIVED, NOT VERIFIED IN OUR HARNESS.** Cheap verification for whoever needs it: in
  `SEAFLOOR_CAVERN_ROOM1`, push boulder `local_id=1` to `(5,12)`, then dump objects while standing
  at `(6,2)` — the only reachable tile from which `(5,12)` falls outside the window. If it reads
  `(5,11)` again, the reset is real. (Our current Room 1 route warps out on that tile, which is why
  the existing drives cannot answer it.)
- **Symptom (as originally filed, and still true).** `modules/map_path.calculate_path` treats a
  boulder's **template** tile as blocked whenever that boulder is not currently spawned, and its
  **live** tile as blocked whenever it is.
- ✅ **THE WINDOW IS NOW DERIVED, NOT GUESSED — AND IT PREDICTS OUR LIVE DUMP EXACTLY.**
  `TrySpawnObjectEvents` / `RemoveObjectEventIfOutsideView` (`src/event_object_movement.c:1645`,
  `:1699`) use `pos ± {2, MAP_OFFSET_W+2, 0, MAP_OFFSET_H+2}` with `MAP_OFFSET_W 15` /
  `MAP_OFFSET_H 14` (`include/fieldmap.h:18-20`), which in LOCAL coordinates is
  **`x ∈ [px-9, px+10]`, `y ∈ [py-7, py+9]` — 20 wide by 17 tall.**
  Validated against the measurement below **5 of 5, including on the boundary**: player at
  `ROOM1 (5,18)` ⇒ `y ∈ [11,27]` ⇒ boulders `(5,11)` and `(12,11)` IN, rock `(5,10)` and grunts
  `(8,6)` / `(15,10)` OUT. That is precisely the dump that was observed.
- **The measurement that found it** (`--driver ch20room1`, 2026-08-13, first drive inside the
  Seafloor Cavern). Standing on `SEAFLOOR_CAVERN_ROOM1 (5,18)` immediately after the warp, a dump
  of every active object returned **2 of the map's 5**:

      BEFORE  * local_id=1 gfx=87  at=(5,11)   <- PUSHABLE_BOULDER
      BEFORE  * local_id=2 gfx=87  at=(12,11)  <- PUSHABLE_BOULDER
              (local_id=3 BREAKABLE_ROCK at (5,10), and grunts 4 @ (8,6) / 5 @ (15,10), ABSENT)

  The rock was demonstrably present — the very next action smashed it — and both grunts appeared in
  later dumps, one of them battling. ⇒ `gObjectEvents` holds only what the game has spawned within
  camera range, **not the map's object inventory**. This was a **pre-registered prediction that
  FAILED** (P3 of `ai-research-notes/2026-08-13-ch20-room1-drive-predictions.md`).
- **Code path, verified.** `modules/map_path.py:811-818` builds `active_objects` and
  `blocked_coordinates` from `get_map_objects()`; `:844-853` blocks a tile whose
  `dynamic_object_id` is **not** in `active_objects` (i.e. assumes the object sits on its template
  tile); `:861` blocks the `current`/`previous` coordinates of objects that **are** active.
- **Why it did not bite in Room 1.** After the two pushes the route runs up x=12 and west along
  row 7 — it never needs `(5,11)` again. A green run therefore proves nothing about this, which is
  exactly why it had to be measured rather than inferred.
- ⛔ **"ARMED IN ROOM 8" IS REFUTED (2026-08-13, same day).** I filed Room 8 as the dangerous case.
  With the window now derived (20x17) and Room 8 measured at **11 wide x 14 tall**, the map is
  *smaller than the window*: a sweep over every player row finds the only despawns at `y=12` (the
  four row-4 boulders), and `y=12` is the arrival tile — occupied exactly once, **before a single
  push**, when every boulder is still on its template tile and model == truth. After the first push
  the route never returns below `y=8`. **Room 8 is safe.** ✅ Room 2 was likewise measured safe on
  its live drive (`--driver ch20room2` PASS): the one planner-driven crossing of a removed object's
  tile is the smashed rock at `(8,7)`, and smashed rocks are immune because `removeobject` **sets**
  their `FLAG_TEMP_*`, which short-circuits the `map_path.py:843` guard.
- ‼ **Where it may still matter:** LARGE rooms — Room 1 is 20x21, bigger than the window in both
  axes — and any RETREAT or long-range re-plan through a room whose boulders have been moved. The
  general rule that follows is cheap and worth keeping regardless of the fix: **plan short routes
  inside boulder rooms, and never plan one from another room.**
- **Scope beyond §Ch20.** This is shared pathfinder behaviour, not cavern-specific. It affects any
  planning done while a relevant object is off-camera — which is *most* long-range planning.
- ‼ **NOT YET REPRODUCED AS A FAILURE.** What is measured is the window behaviour and the code
  path. No run has yet been shown to plan a wrong route because of it. **Do not fix this on
  reasoning alone** — build the repro first (push a boulder, walk out of range, then ask
  `calculate_path` about both tiles and compare against the truth) and A/B it. That repro is cheap
  and should come before any change.
- **What a fix might look like** (not attempted, and it is not obviously desirable): remember the
  last-known live position of an object that has despawned, keyed by `(map, local_id)`, and prefer
  it over the template. ‼ That cache would be wrong in the other direction after a map re-entry,
  because the cavern's boulders are `FLAG_TEMP_*` objects that **respawn at their template tiles on
  every map load** — so any such cache must be invalidated on map transition, and the safest
  version may simply be "plan short routes inside boulder rooms".

---

## KI-79 — `withdraw_from_box` PRINTED A SUCCESS IT NEVER VERIFIED: `len(get_party())` wearing an identity's clothes (2026-08-15, code-verified while driving (P4) Stage 2 — ✅✅ **FIXED, FAULT-PROVEN, AND PROMOTED TO BOTH FORKS 2026-08-15, user-approved — ⚠ CLOSED *FOR THE MESSAGE*, WITH ONE RESIDUAL: NO CALLER ACTS ON THE VERDICT.** `withdraw_from_box` still returns nothing and still never raises, so production can now TELL the truth about a failed withdraw and still cannot REACT to one — tracked as an open thread in `03-PUNCH-LIST.md`, because a residual filed under a header reading only "CLOSED" is a residual nobody finds)

- **The line.** `modules/story/pc_trip.py:472-474`, the tail of `withdraw_from_box()`:
  ```
  after = len(get_party())
  console.print(f"[green]Story: PC — {name} is in the party; party is now {after}.[/]")
  context.message = f"Story: withdrew {name} — party {after}."
  ```
  It reads a **COUNT** and announces an **IDENTITY**. Nothing between the `interact_with_pc(actions)`
  call and this print asks whether `name` actually arrived.
- **Why it can lie, concretely.** The whole body is wrapped in a blanket
  `except Exception: ... "could not withdraw {name} ... it stays in the box"` (`:475-478`), so the
  function **never raises**. But a PC interaction that silently completes the WRONG action — or
  completes the make-room deposit and then fails the withdraw — leaves the count **exactly the
  same** (the deposit cancels the withdraw), takes no exception path, and prints the green
  success line. ‼ **MEASURED, not theorised:** on a genuinely SUCCESSFUL withdraw this project
  records `party_before=6 party_after=6 box_before=2 box_after=2` — every count unchanged. A
  metric that is invariant across success is invariant across failure too.
- **Why it matters beyond cosmetics.** This is the project's #1 recurring bug shape
  (`CLAUDE.md` SESSION DISCIPLINE rule 3: *assert IDENTITY, never position or count*; the same
  shape produced `catch_confirmed()`'s party-COUNT delta that a Shedinja spawn could fake, fixed
  under (P1)). It is **live in production**, on the PC path, in the middle of the arc whose whole
  purpose is PC/party robustness. And a future driver or log-scraper that greps for
  `"is in the party"` would inherit the lie — `--driver boxcounter2` deliberately does NOT.
- **How it was found.** Not by a test — by reading `withdraw_from_box` end-to-end while building
  (P4) Stage 2's acceptance chain, precisely because the design note required every claim to be an
  identity. The happy path prints the same line whether or not it is true, so **no green run could
  ever have surfaced it.**
- **NOT OBSERVED FAILING.** Every (P4) Stage 2 drive so far shows the line printing truthfully
  (ARM B: `moved=True`, verified independently by PID+species and by `contains_pokemon`). This is
  a structural finding from reading the code, not a reproduction. ‼ Report it as *"cannot be
  trusted"*, never as *"is wrong"*.
- ✅ **FIXED 2026-08-15 (sandbox), exactly as scoped below.** After the PC interaction the
  function now yields two frames (party AND storage are cached per frame, so a same-frame read
  sees the PRE-withdraw state and the verification would become the new false negative), then
  resolves the target BY IDENTITY: a party member matching `(personality_value, species.name)`
  **and** `contains_pokemon(target)` now False. Both halves are required — in-party-only could be
  a copy, gone-from-box-only could be a release. On success it prints the same green line; on
  failure it prints a loud named `‼ THE WITHDRAW DID NOT LAND … in_party=… still_boxed=…` and
  ⛔ **still does not raise**, because the original contract stands: a PC hiccup must not destroy
  a heal that already succeeded. What changed is that the caller is no longer LIED TO.
  ⛔ It is NOT fixed by asserting the count changed: on the make-room path it correctly does not.
- ‼ **PROVEN BY FAULT INJECTION, because a green run cannot exercise an error path.** New
  permanent hook **`POKEBOT_PCWITHDRAW_FAULT=1`** (registered in `29-DISABLED-FEATURES-REGISTRY.md`)
  skips the PC interaction so the withdraw provably does not happen. Measured, both arms, live:
  * **FAULTED** → `Story: PC — ‼ THE WITHDRAW DID NOT LAND. Slugma in_party=False
    still_boxed=True`, and `--driver boxcounter2` reported `moved=False knows_rock_throw=False
    lead_is_counter=False noop_attributed=False` → **`ACCEPTANCE: FAIL`**. ‼ It ran to COMPLETION
    and reported — it did not throw, which is itself worth knowing.
  * **UNFAULTED** → `Story: PC — Slugma is in the party; party is now 6.` (now identity-verified)
    → **`ACCEPTANCE: PASS`**, no regression.
  ⇒ The old code printed the SAME green line in BOTH of those runs. That is the defect, shown.
  ⇒ Bonus: this also FAULT-TESTS the Stage 2 driver — all four of its graded claims flip to False
  when the thing they check is sabotaged, so it is not rubber-stamping.
- 📁 **THE RAW TRANSCRIPTS ARE COMMITTED, BY NAME** — `tools/story-dev/evidence/2026-08-15-ki79-armB-UNFAULTED.stdout.txt` and `…-FAULTED.stdout.txt` (plus their `.driver.txt` twins).
  ‼ **They exist because a Tier 1 reviewer could not verify this entry and said so.** The harness
  USED TO WRITE `harness_<build>.log` — **one fixed filename per build, overwritten by the very next
  run** — so the unfaulted PASS transcript had already been destroyed by the faulted run that
  followed it, and all that remained on disk was a FAIL. ✅ **That collision is FIXED as of
  2026-08-16** (`#24-orphans` (4)): default log names are unique per run. ‼ **Committing the raw
  transcripts is STILL right** — a gitignored log is not evidence, and stdout (production's
  `console.print`) is not in the harness log at all. The claim was true and *unverifiable*,
  which for this project's purposes is the same as unproven. ⇒ **A/B runs must be captured with
  distinct `--log` names, and stdout redirected too** (the driver's own log does NOT contain
  `console.print` output — the `‼ THE WITHDRAW DID NOT LAND` and green-success lines live in
  stdout). The faulted stdout also carries `POKEBOT_PCWITHDRAW_FAULT=1, SKIPPING the PC
  interaction`, which is what proves the fault was actually armed for that run.
- ✅✅ **PROMOTED TO BOTH FORKS 2026-08-15 (user-approved); this file is in both.** *(⚠ The
  repo-wide drift figure is no longer 0 — one UNRELATED comment-only `story_mode.py` fix awaits
  the user's promotion call. It does not touch this item.)* Restore point
  `restore/2026-08-15-pre-promotion-ki79-pctrip`.
  ‼‼ **VERIFIED BY A THREE-POINT A/B, NOT BY A BYTE-COMPARE — and the distinction is the whole
  point for a BEHAVIOUR change.** `promote.py` reporting "1/1 byte-identical" only proves the file
  was COPIED; it cannot prove the new branch is what EXECUTES. The fault hook can:
  | # | run (`--driver boxcounter2 --build custom`) | result | proves |
  |---|---|---|---|
  | 1 | **BEFORE** promotion, `POKEBOT_PCWITHDRAW_FAULT=1` | `Slugma is in the party` → **PASS** | the hook is ABSENT in custom — the variable is INERT |
  | 2 | **AFTER** promotion, same command | `‼ THE WITHDRAW DID NOT LAND` → **FAIL** | ⇒ **the new code is LIVE in custom** |
  | 3 | **AFTER** promotion, unfaulted | green line → **PASS** | no regression on the happy path |
  ‼ Run 1 is capturable ONLY before the copy and is therefore committed. ⛔ **Run 1 does NOT prove the variable was 'inert' — a run of code that never READS a variable cannot show anything about it, and its output is indistinguishable from an unfaulted run.** (A Tier 1 reviewer caught exactly that overclaim.) What run 1 DOES prove is that the identical command PASSED before the promotion. The *absence of the hook* is proven from git instead, which is stronger and re-runnable by anyone: `git show restore/2026-08-15-pre-promotion-ki79-pctrip:custom-pokebot/modules/story/pc_trip.py | grep -c POKEBOT_PCWITHDRAW_FAULT` → **0** (sandbox at the same tag → **3**; custom now → **3**).
  Transcripts:
  `tools/story-dev/evidence/2026-08-15-ki79-promotion-{BEFORE-custom-faultvar-set,AFTER-custom-FAULTED,AFTER-custom-UNFAULTED}.stdout.txt`.
  Also green on custom: `boxcounter2 --build custom` **ARM A** → `ACCEPTANCE: PASS` (transcript: `tools/story-dev/evidence/2026-08-15-ki79-promotion-AFTER-custom-ARMA.stdout.txt`, which logs `ARM=A (POKEBOT_BOXCOUNTER_TYPEONLY_A='1')` so the arm is self-evidencing), and four `--build custom` gates that each ASSERT which fork they imported.
- ⚠ **WHAT IS STILL TRUE AFTER THE FIX:** the message is now trustworthy, but **no CALLER acts on
  it.** `withdraw_from_box` still returns nothing and still never raises, so a caller that needs to
  KNOW whether the counter arrived must check identity itself — which `--driver boxcounter2` does
  and production does not. That is a deliberate scope line, not an oversight.
- **Related:** KI-78 (identity is `(personality, species)`, because a Shedinja shares its
  Ninjask's PID — so even a PID-only check is not enough here), and the (P4) Stage 2 driver, whose
  `party_map()` is keyed on that pair for exactly this reason after a PID-keyed first draft
  reported a full party of 6 as 5.

---

## KI-80 — `grass_is_fodder` CONFLATED "no training patch configured" with "the patch is too weak", and it CO-GATED the counter-ladder (with `boss_teaches`, inside `losses >= 2`) — so giving a boss a training area silently disabled its KI-23 machinery. ✅ DECOUPLED AND PROMOTED TO BOTH FORKS 2026-08-16 (2026-08-16, ✅ **REPRODUCED AND DRIVEN** — `--driver ki80ladder` is COMPLETE and PASSING: **4 arms**, both forks, mirror-regression guard fault-tested against the real naive edit. ✅ **AND THE DECOUPLING IS NOW BUILT, DRIVEN AND REVIEWED** — `:1901` is `if boss_teaches:`, `boss_mode` sits behind its own `if grass_is_fodder:`; `repro_boss_grass_gate.py` has SELF-RETIRED. ✅ **AND PROMOTED TO BOTH FORKS 2026-08-16 (user-approved), proven by a THREE-POINT A/B against `--build custom` — drift is 0.** ⛔ **THIS KI STAYS OPEN ONLY FOR ITS TRACKED RESIDUAL** `#24-zerokocounter`: should `boss_teaches` come off the gate too? Not shipped because no arm can discriminate it, and an audit derived that it would need TWO new arms plus a frequency measurement first)

- **The line.** `plugins/custom_modes/story_mode.py:1899`:
  ```
  grass_is_fodder = ("grass" not in cfg) or (wild_max is not None and wild_max + 8 < team_max)
  ```
  and `:1901`:
  ```
  if grass_is_fodder and boss_teaches:
      hopeless, needed = self._boss_plan_is_hopeless(cfg)     # the ONLY call site
      if hopeless:
          acted = yield from self._counter_ladder(cfg, losses, needed)   # ditto
  ```
- **The defect.** One boolean carries two unrelated meanings — *"this boss has no patch"* and
  *"this boss's patch is far below the team"* — and it gates **KI-23's** hopeless-detector and
  counter-catch ladder. The two facts justify boss-training mode for the same reason, but they say
  nothing in common about whether the party has a TYPE ANSWER, which is what the counter ladder is
  for. ⇒ **A boss cannot be given a training patch without losing its counter machinery.**
- **‼ DERIVED CONSEQUENCE — ARITHMETIC ON MEASURED BANDS, *NOT* A REPRODUCTION** (see "NOT OBSERVED FAILING" below; the 198/41/41 figures ARE measured, but they are KI-23's history, not this scenario). On the exact boss KI-23 was filed for: `wild_max` is read from the
  ROM's LAND table for `cfg["grass"][0]` (`:1886-1890`). Winona's band is **(29,33)**; the patch
  the adjacent code comment suggests is **Route 119, band 24-27**. For any team at **L30-35** —
  i.e. her own band — `27 + 8 = 35 < team_max` is **FALSE**, so `grass_is_fodder` flips to False
  and the counter ladder is SKIPPED. Control falls to the plain
  `plus5_max`/`plus5_avg`/`escalate_band` escalation at `:1937-1951` — **the path KI-23 measured
  failing 198 attempts / 41 losses / 41 whiteouts, never converging**, because it does not
  converge when the party has no super-effective answer.
- ⛔ **AND IT IS INVISIBLE.** The regression prints a healthy-looking
  `"Story: lost here N× — training harder before re-attempting (target Lv X, plus5_max)"`.
  Nothing errors, nothing derails. The only symptom is the ABSENCE of the counter-catch message —
  and this project has been caught by absence-as-signal repeatedly.
- **How it was found.** An adversarial pass over `03-PUNCH-LIST`'s **(P6)** item, which asked for
  *"TRAINING-AREA MAPS per gym AND per boss"* and cited as its hole: *"Winona has no patch
  configured at all, so the whole relocation machinery is skipped for her."* ‼ **Acting on that
  sentence would have caused this regression.** Both of (P6)'s stated examples turned out to be
  wrong — see the (P6) entry in `03-PUNCH-LIST.md`, now corrected.
- ✅ **GATED — `tools/story-dev/repro_boss_grass_gate.py` (suite #24).** It re-derives the coupling
  from the live AST and then forbids a `"grass"` key on `winona_fight`, `flannery_fight` and
  `rival110_fight` while it stands. **AST-based**, so a mention in a comment or docstring cannot
  trigger it, and **SELF-RETIRING**: decouple the ladder and the gate stops enforcing and says so.
  `--self-test` proves all four directions (fires when broken; quiet when healthy; quiet when
  decoupled; quiet on comment-only mentions).
- ✅✅ **SUPERSEDED 2026-08-15 — IT HAS NOW BEEN OBSERVED FAILING, ON DEMAND, IN BOTH FORKS.**
  ⛔ This bullet previously read *"NOT OBSERVED FAILING … report it as 'would fire', never 'has
  fired'."* That was correct when written and is **retracted now**: `--driver ki80ladder`
  (`story_harness.py`) DRIVES production's own `_prepare_for_fight` three times on
  `saves/batch2_run04_wedge.ss1` and watches which branch it takes. **Measured, `team_max = 28`:**

  | arm | `cfg["grass"]` | `wild_max` | outcome |
  |---|---|---|---|
  | `NOGRASS` | absent | n/a | **`_counter_ladder` reached** |
  | `GRASS_FODDER` | Route 102 | **4** | **`_counter_ladder` reached** |
  | `GRASS_STRONG` | Route 119 — the patch her OWN cfg comment names (`story_mode.py:3531`: *"Route 119 is the Fortree-side band"*) — ⛔ she has NO `grass` key today, which is the only reason her ladder still works | **27** | ⛔ **plain escalation; ladder SKIPPED** |

  Same party, same seeded losses (8), same boss — **the only difference is the `grass` key.**
  `ACCEPTANCE: PASS` on `--build sandbox` AND `--build custom`. Production itself derived
  `needed = ['Rock', 'Ice', 'Dragon']` and raised *"Winona: 8 losses with no super-effective
  answer…"* on the two ladder arms, and printed *"lost here 8× — training harder before
  re-attempting"* on the third. ⇒ **the regression is real, and it is exactly as silent as
  predicted.** Transcripts: `tools/story-dev/evidence/2026-08-15-ki80ladder-*.stdout.txt`.
  ‼ **The driver EXITS 0 even on FAIL** (it is a harness driver, not a gate) — **grade on the
  `ACCEPTANCE:` line, never on the exit code.**
- ✅ **AND THE DRIVER IS FAULT-TESTED, not merely green.** Two deliberate failure runs, both
  committed as evidence: (1) against `ch13_fortree_door.ss1` — the fixture THIS ENTRY ONCE
  PRESCRIBED — it prints `ACCEPTANCE: FAIL … THE A/B WOULD BE VACUOUS: ROUTE119 does not flip
  `grass_is_fodder` at team_max=39`, **and all three arms come back `LADDER`**, demonstrating live
  that the prescribed test would have shown NO DIFFERENCE and read as a REFUTATION of a true
  finding; (2) with `POKEBOT_KI80_DECOUPLED=1` it FAILS today, which is what proves the same driver
  can serve as the AFTER run once the fix lands.
- ⛔ **WHAT THE DRIVER DOES NOT PROVE.** Its `_counter_ladder` spy replaces the ladder's BODY, and a
  tripwire in a console proxy cuts every arm off AT its decision. It proves the gate is **REACHED**;
  it proves nothing about what the hunt then does. Deliberate — the hunt travels, and travel is risk
  this test does not need. Design and the refutation that reshaped it:
  `ai-research-notes/2026-08-15-ki80-ladder-repro-design.md`.
- **What a fix looks like** (NOT attempted — it changes boss prep for EVERY gym, and KI-23's own
  entry warns about the mirror regression): split the two meanings. The counter ladder should be
  gated on *"is this fight hopeless"* — which `_boss_plan_is_hopeless` already answers on its own —
  not on whether a patch happens to be configured. ⛔ **The change may not ship on reading alone:**
  it needs the KI-23 repro conditions DRIVEN, both before and after, confirming `_counter_ladder`
  still fires rather than falling through to the plain escalation.
  ✅✅✅ **BOTH HALVES ARE NOW MET — THE DECOUPLING SHIPPED (sandbox) 2026-08-16.**
  AFTER: `POKEBOT_KI80_DECOUPLED=1` **FAIL → PASS**; arm 4 **still PASS** (no mirror regression);
  the coupled expectation now **FAILS**, proving the behaviour changed; `repro_boss_grass_gate.py`
  **SELF-RETIRED** and still exits 0. An adversarial diff review attacked six angles and all six
  SURVIVED — including that the `:1932` elif's firing condition is algebraically unchanged, that
  `_boss_plan_is_hopeless` is read-only and fails safe, and that the new `BotModeError` is caught at
  `:4080-4081` (`outcome = "derailed"`) rather than crashing a batch.
  ⚠ **Blast radius: arithmetic MEASURED, behaviour INFERRED** — Brawly/Roxanne/Wattson gain the
  machinery; **no run against those three exists**, only Winona's fixtures were driven.
  ✅ **PROMOTED 2026-08-16, user-approved, by a THREE-POINT A/B against `--build custom`** (not a
  byte-compare): `POKEBOT_KI80_DECOUPLED=1` **FAIL → PASS**, the coupled expectation **PASS → FAIL**,
  and **arm 4 PASS on both sides** — the invariance proving the mirror regression did not land.
  *(Superseded: the line below said the decoupling was merely unblocked.)* The AFTER run is the same command with
  `POKEBOT_KI80_DECOUPLED=1`, which must go from FAIL (today, measured) to PASS.
  ⛔ **The BEFORE run is unrepeatable once the fix lands — it was run and committed FIRST**, the
  rule KI-79's three-point A/B established.
- ⛔⛔ **BEFORE YOU DECOUPLE — TWO THINGS THE REPRO DRIVER CANNOT SEE (found by a Tier 2 cold-start
  agent that tried to BEGIN this item, 2026-08-15).** The naive edit is "delete `grass_is_fodder and`
  from `:1901`". ‼ **That is not sufficient, and its damage is invisible to `--driver ki80ladder`.**
  1. **`grass_is_fodder` HAS A SECOND USE SITE:** `:1932`, `elif grass_is_fodder and recent_kos and
     not boss_teaches:`. Decoupling `:1901` without deciding `:1932` leaves one boolean half-split.
  2. ⛔ **`:1925 boss_mode = True` IS ON THE *NOT-HOPELESS* PATH, AND `:1937` READS IT**
     (`if losses >= 2 and not boss_mode:`). So moving the hopeless check out from behind
     `grass_is_fodder` hands `boss_mode = True` to every boss that has a **strong patch AND a
     credible answer** — silently disabling their grass escalation. **That is precisely KI-23's
     mirror regression**, arriving through the edit meant to fix KI-80.
  ‼‼ **AND ARMS 1-3 CANNOT SEE IT.** All three use a NO_ANSWER party, so `hopeless` is True, the
  ladder fires, and `_prepare_for_fight` RETURNS at `:1924` — **`:1925` is never reached in any arm.**
- ✅✅ **SO ARM 4 IS NOW BUILT AND MEASURED — `POKEBOT_KI80_ARM4=1` (2026-08-16).**
  `POKEBOT_KI80_ARM4=1 … story_harness.py fortree_gym_wedge.ss1 --driver ki80ladder --frames 2000`
  → **`ACCEPTANCE: PASS`**, `OUTCOME=PLAIN_ESCALATION`, `INVARIANCE drift=none`.
  ‼ **Its assertion is FIX-SHAPE-AGNOSTIC and identical before and after:** a boss with a strong
  patch AND a credible answer must keep its plain grass escalation.
  ✅✅ **AND THE DETECTOR ITSELF IS NOW FAULT-TESTED AGAINST THE REAL NAIVE EDIT (2026-08-16) —
  THIS WAS A PREDICTION UNTIL AN AUDIT POINTED OUT THAT NOTHING HAD EVER SEEN IT FIRE.**
  `:1901` was temporarily changed to `if boss_teaches:` (the naive fix), both suites were run, and
  the edit reverted. The result is the strongest single argument for arm 4's existence:
  | run, under the NAIVE edit | result |
  |---|---|
  | arms 1-3, `POKEBOT_KI80_DECOUPLED=1` | ⛔ **`ACCEPTANCE: PASS`** — all three reach the ladder |
  | **arm 4**, `POKEBOT_KI80_ARM4=1` | ✅ **`ACCEPTANCE: FAIL`**, `ARM4 OUTCOME=BOSS_TRAINING_MODE` |
  ⇒ **THE THREE-ARM TEST ALONE WOULD HAVE BLESSED THE REGRESSION.** Arm 4 is the only thing that
  catches it, and it names it: *"a boss with a STRONG patch AND a credible answer entered
  BOSS-TRAINING MODE, so `:1937`'s plain grass escalation is SUPPRESSED."*
  ⇒ ‼ **THE FIX MUST KEEP `boss_mode = True` (`:1925`) BEHIND `grass_is_fodder`.**
  Transcripts: `evidence/2026-08-16-ki80ladder-FAULT-naive-edit-*`. ⚠ *A gate that has never failed
  may simply not be looking — this one has now failed on purpose.*
  ⛔⛔ **AND THE FIXTURE THIS ENTRY FIRST PRESCRIBED FOR ARM 4 WAS VACUOUS — THE SAME TRAP, THE SAME
  NUMBER, THE THIRD TIME.** It said *"`fortree_gym_wedge.ss1` … is exactly right for it"* with a
  **Route 119** patch. `fortree_gym_wedge` IS correctly HAS_ANSWER (Castform's Powder Snow scores
  **160 >= 75**) — but its **`team_max` is 39**, and `27 + 8 = 35 < 39` is TRUE, so `grass_is_fodder`
  is **True anyway** and the "strong patch" arm is silently a FODDER arm. *The check verified the
  INVERSE of condition 7 and once again never verified condition 9 — exactly how
  `ch13_fortree_door.ss1` (also `team_max` 39) survived an earlier audit.*
  ✅ **THE FIX, MEASURED 2026-08-16 across every `TRAINING_GRASS` map plus 9 candidates:** arm 4 needs
  a map with land `wild_max >= team_max - 8 = 31`, and **the ONLY one that clears it is
  `VICTORY_ROAD_1F` at 40** (Routes 121/123 peak at 28; ROUTE119 and ROUTE118/120 at 27;
  MT_PYRE_EXTERIOR 29). So arm 4 pairs `fortree_gym_wedge.ss1` with a **VICTORY_ROAD_1F** grass key:
  `40 + 8 = 48 >= 39` ⇒ `grass_is_fodder` is genuinely **False**.
  ⚠ **Victory Road is NOT a plausible training area for Winona, and the arm does not pretend it is** —
  arm 4 is a DECISION-level test of the branch, exactly as arms 1-3 are not a faithful Winona run.
  ✅ **Both of arm 4's controls are MEASURED, and the first is FAULT-TESTED:** CONTROL-A calls the
  REAL `_boss_plan_is_hopeless` and requires **not** hopeless — run against a NO_ANSWER save it FAILS
  with *"this save is NO_ANSWER (hopeless=True), so it cannot exercise the `:1925 boss_mode` path at
  all"*; CONTROL-B re-derives condition 9 INVERTED from the live ROM. Transcripts:
  `evidence/2026-08-16-ki80ladder-ARM4-*`.
- ✅ **THE PROMOTION ENTANGLEMENT IS RESOLVED (2026-08-16).** This bullet used to warn that a KI-80
  fix could not be promoted separately from an unapproved comment-only edit sitting in the SAME
  file (`plugins/custom_modes/story_mode.py`). **The user ruled, the comment-only correction was
  promoted** — so the KI-80 fix, when approved, promotes cleanly on its own.
  ✅ The KI-80 decoupling was itself promoted 2026-08-16 on that same rule; drift is 0.
  *(⚠ The superseded wording is DESCRIBED rather than reprinted: `audit_doc_consistency` matches
  literal strings and cannot tell a quotation from a claim — it red-flagged the first draft of this
  very bullet for reciting the old figure.)*
  ‼ **Keep the general rule, which is what actually matters:** *`promote.py` moves whole FILES, so
  two unrelated edits to one file cannot be promoted separately.* Land an approved edit before
  starting an unapproved one in the same file, or they become a single decision. ⛔ And when the fix ships, `repro_boss_grass_gate.py`
  (suite #24) **SELF-RETIRES** — it stops enforcing and says so; that is designed, not a failure.
- ⛔⛔ **THE REPRO CONDITIONS, READ FROM THE SOURCE 2026-08-15 (a static code read, not a live
  measurement — every row carries its file:line so it is checkable) — AND THEY ARE NOT WHAT THIS
  ENTRY FIRST SAID.** An earlier draft here said *"losses >= 2, kos >= 1, no type answer"*. That is
  **INCOMPLETE, and a test built to it would be VACUOUS**: at `losses` 2-5 the ladder cannot fire
  *whatever* the grass key is, so the A/B would show NO DIFFERENCE and would look like a refutation
  of a true finding. All of these must hold together:
  | # | condition | where |
  |---|---|---|
  | 1 | `losses >= 2` — the outer boss-training block | `story_mode.py:1877` |
  | 2 | `grass_is_fodder` — TRUE today for Winona only because she has no `grass` key | `:1899` |
  | 3 | `boss_teaches` — at least one of the **LAST TWO** losses has `kos >= 1` | `:1893-1900` |
  | 4 | ‼ `losses >= PLATEAU_LOSS_THRESHOLD` = **6** | `:1507`, `:1046` |
  | 5 | ‼ `len(_loss_ko_history) >= 6` | `:1512` |
  | 6 | ‼ NOT improving: `max(kos of last 3) <= max(kos of previous 3)` | `:1514-1517` |
  | 7 | ‼ **no battler has a credible answer**: some move with `eff >= 2.0` **and** `base_power * eff * stab >= 75` | `:1573-1596`, `:1087` |
  | 8 | `"ace_types" in cfg` — absent short-circuits to `(False, [])` before the answer test | `:1557` |
  | **9** | ⛔⛔ **`team_max <= wild_max + 8` — THE ARMS MUST ACTUALLY DIFFER** | `:1899` |
  ⛔⛔ **CONDITION 9 WAS MISSING UNTIL A COLD-START AUDIT FOUND IT (2026-08-15), AND WITHOUT IT THIS
  ENTRY PRESCRIBED A VACUOUS TEST — the exact failure it was written to prevent, one condition
  over.** `grass_is_fodder` is `("grass" not in cfg) or (wild_max + 8 < team_max)`. The A/B only
  MEANS anything if adding the `grass` key FLIPS it to False, which needs
  `wild_max + 8 >= team_max`. For a **Route 119** patch `wild_max = 27`, so the fixture's
  **`team_max` must be <= 35**.
  ⇒ ⛔ **`ch13_fortree_door.ss1` — which THIS ENTRY PREVIOUSLY NAMED AS THE FIXTURE — FAILS IT.**
  Its **Blaziken L39** gives `team_max = 39`, and `27 + 8 = 35 < 39` is TRUE, so `grass_is_fodder`
  is True **in BOTH arms**, both take the same branch, and the run would show NO DIFFERENCE — which
  reads as a refutation of a true finding. It satisfies condition 7 (NO_ANSWER) and fails
  **condition 9** (which is condition 2's requirement stated as a checkable arithmetic test); the
  earlier check verified 7 and never the flip.
  ✅ **VERIFIED CANDIDATES that satisfy BOTH** (`probe_credible_answer.py`, run 2026-08-15 —
  all NO_ANSWER, `team_max` in brackets): `batch3_run03_wedge.ss1` [35, OVERWORLD, MAUVILLE_CITY],
  `batch2_run04_wedge.ss1` [28, OVERWORLD, ROUTE111], `batch3_run05_end.ss1` [34, ⚠ **in BATTLE**],
  `ch13_r119_wedge.ss1` [33, ⚠ **in BATTLE**, and ROUTE119 is a KI-24 wall map].
  ‼ **None is Winona-era** (badges 123/1234, not 12345) — which does NOT block a DECISION-level
  A/B (`_prepare_for_fight` reads party levels/moves, the grass map's `wild_max`, and the seeded
  loss history — never a badge), but it DOES mean the run is not a faithful Winona scenario and
  must not be reported as one. ⚠ `batch3_run03_wedge` sits exactly ON the boundary (`35 < 35` is
  false by one level), so a single level-up during the run would silently flip it — **prefer margin,
  and ASSERT the measured `team_max` and `wild_max` at run start rather than trusting this table.**
  ‼ A flat series of six losses each with `kos = 1` satisfies 3-6 at once.
  ⛔⛔ **AND A CEILING NOBODY WOULD GUESS: KEEP `losses` UNDER 12.** At
  `losses >= HARD_PLATEAU_LOSS_THRESHOLD` (**12**) with `len(history) >= 12` and a flat 12-series,
  `hard_plateau` becomes True (`:1541-1544`) and the answer loop runs as
  **`for i in (battlers if not hard_plateau else ()):`** (`:1573`) — i.e. over an **EMPTY tuple**.
  ⇒ `hopeless` comes back **True regardless of the party**, for a completely different reason than
  the one under test. An A/B that drifts past 12 losses would therefore go GREEN *without* proving
  anything about the no-answer path. **Seed 6-11 losses, never 12+**, and assert the count you
  seeded. *(Caught by a Tier 1 reviewer against an earlier draft of this table.)*
- ⛔ **AND THE OBVIOUS FIXTURE DOES NOT WORK — MEASURED LIVE.** `fortree_gym_wedge.ss1` (the
  anchor (P4) Stage 2 uses) **FAILS condition 7**: its **Castform L25 knows Powder Snow** (Ice,
  base_power 40), and vs Altaria (Dragon/Flying) that is `40 x (2.0 x 2.0) x 1.0 = **160** >= 75` —
  a credible answer, so `_boss_plan_is_hopeless` returns **not hopeless** and the ladder can never
  fire from that save. ✅ **9 of 10 Winona-era saves pass CONDITION 7 (NO_ANSWER)**, including
  **`ch13_fortree_door.ss1`** — ⛔ **but passing 7 is NOT "qualifying": that save FAILS condition 9
  and is unusable as the fixture (see above)** — verified live with `tools/story-dev/probe_credible_answer.py`
  (NEW), which drives production's own type chart and `_battler_slots()`.
  ‼ **The discriminator is the GATE ORDER, not the score:** those 9 saves hold moves scoring
  **97.5** (Loudred/Stomp) and **90.0** (Mightyena/Bite) — both above 75 — that never count,
  because `eff` is 1.0 and the `eff < 2.0` branch `continue`s first. A check written as
  "score >= 75" alone would call every one of them HAS_ANSWER and be confidently wrong.
- **Related:** **KI-23** (explicitly NOT closed; its own watch-item is the mirror of this),
  **KI-31** (the fodder rule as a pure function), and the `xp_rate`-vs-`legacy` `FODDER_RULE` flag,
  whose repro `repro_fodder_grass.py` *"still has not been run, on any machine"* — a separate,
  already-tracked axis that must not be conflated with this one.
