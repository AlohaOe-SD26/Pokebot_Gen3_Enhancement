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

**Numbering:** IDs are **not contiguous** — many early ones were archived to
`31-KNOWN-ISSUES-ARCHIVE.md`. ⛔ **RE-DERIVE, DO NOT TRUST A QUOTED FIGURE HERE:**
`grep -cE "^## KI-[0-9]+" 05-KNOWN-ISSUES.md` — **65 headings, 61 distinct IDs** as of
2026-08-22. ‼ This line read *"23 distinct IDs across 25 headings … no KI-12 and no KI-13"* for a
month while the file nearly tripled, and it named KI-15 as appearing twice when KI-15 has no entry
at all — **the file's only navigation aid was wrong three ways at once**, which is worse than
having none (PASS 5, 2026-08-22).

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
| KI-11 | body said `deliver_devon_goods_to_stern` stays **UNWIRED** — it is wired | `modules/story/early_game.py:3617-3804` (Shipyard → Dock leg) |
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

## KI-84 — `train_team(slots={i})` with i≠0 runs ONE spin-batch then returns as if finished (opened 2026-09-04, severity: HIGH — ⚠ **OPEN.** Worked around in §Ch23 only; every other `slots=` caller is still exposed)
- **Measured:** a 900k-frame §Ch23 run produced **8 battles** against an estimate of 306 — Wailmer 40→41, Mightyena 44→45, **Swellow +0** — then reported "finished the grind" (`tools/story-dev/ch23train_real.log`, 2026-09-04).
- **Root cause:** `early_game.py:2021` builds `need` from `party[i]` **by index**; `:2034` then calls `_rotate_lead_safely(target_slot)`, which drives the party menu's SWITCH option (`higher_level_actions.py:500`) — a **SWAP**. Next iteration `party[i]` holds the OLD LEAD (level ≥ target), `need` is empty, and the loop breaks. ⇒ this project's own SESSION DISCIPLINE rule #3 — *assert IDENTITY, never position* — violated inside shared code.
- **Workaround in §Ch23 (`victory_road.train_for_victory_road`):** rotate the mon to slot 0 ourselves, then call `train_team(slots={0})` — with the mon already lead, `target_slot == 0`, no swap happens and the loop converges. It asserts by **PID** that the rotation landed (`_rotate_lead_safely` gives up silently after 3 attempts) and raises if a call fails to move the level at all.
- ⛔ **Deliberately NOT fixed in `train_team` itself:** it is also the gym-prep path, so a change moves every gym's levels at once and needs its own A/B. A deferral with a reason, not an oversight.

## KI-82 — ✅ **CLOSED, NOT A DEFECT. ⛔⛔ DO NOT RE-RAISE — RULED TWICE.** (opened 2026-08-22, closed 2026-08-23)

**The tracked Emerald ROM is a DELIBERATE, USER-RULED choice.** Ruled 2026-07-18
(`06-DECISIONS-LOG.md`, *"Emerald ROM stays tracked in the repo (user ruling)"*, ending **"Do not
re-raise this for THIS file."**) and re-affirmed 2026-08-23: *"leave as-is, fix the docs."*
⚠ Two facts an auditor usually gets wrong: the "33 MB" figure was **wrong** — both paths resolve to
the SAME git blob `21bfd6e0`, so git stores **one** copy; and `.gitignore:17`'s `roms/*` is **not** a
contradiction (it blocks accidental *local* commits; the tracked file is unaffected).
‼ **THE REAL DEFECT WAS THE PROCESS:** this was filed without first checking
`06-DECISIONS-LOG.md`, where the answer had sat for five weeks. ⇒ **`grep -i` the decisions log
BEFORE escalating anything.**
📦 Full original entry archived verbatim in `31-KNOWN-ISSUES-ARCHIVE.md` (2026-09-05).
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

## KI-24b — region reachability BUILT; hop count alone is too coarse to rank by (2026-07-25) — 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-06, R3 line budget; nothing deleted, status unchanged).

**2026-09-06 — ARCHIVED, STATUS UNCHANGED.** Full entry verbatim in `28-HANDOFF-ARCHIVE.md`. ⛔ Archived for the R3 budget only — NOT a closure.
## KI-25 — `_lead_best_matchup` is purely DEFENSIVE; it benches the only mon that can win (opened 2026-07-27, severity: HIGH)
- **Symptom:** before a type-countered fight the bot leads a mon that merely *survives* the
  foe's STAB, regardless of whether it can deal damage. Measured in bundle
  `20260726-231412`: P2 led **Whismur L15** into the Route 110 rival **13 times in one run**
  while **Marshtomp L24** sat in slot 2. P3 led Zigzagoon L16 with Grovyle L22 benched.
- **Cause (exact line):** `modules/story/early_game.py:1659`
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
- **Last known stack:** `do_weather_institute` (`early_game.py:6361`) → its TWO calls to
  `_ride_out_all_scenes` (`early_game.py:437`), which sit at `do_weather_institute`
  `early_game.py:6364` and `early_game.py:6387`.
  ‼ *Re-derived from source 2026-08-16 — it read `:5548`, which is unrelated prose in another
  function. ⛔ NOTE THE UNIT: a stack line wants the CALL SITE, not the def.*
  ⛔⛔ **AND ON 2026-08-23 A TIER 1 REVIEWER CAUGHT THIS LINE BREAKING ITS OWN RULE, ONE SENTENCE
  LATER.** Three of its four numbers were wrong: `:6302` is the `def` line offered as a stack frame;
  `:6309` is DOCSTRING PROSE; `:6327` is an unrelated `_enter_warp_by_navigation(...)`; and the def
  was cited as `:436` when it is `:437`. Cause: the citation was "re-pointed" by bumping the outer
  number for line drift **without re-deriving the inner ones** — which is not re-derivation, it is
  a guess wearing its clothes. ⇒ **Re-point a citation by RE-PARSING for the symbol (AST), never by
  offsetting the old number.** All four numbers above are now AST-derived.
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
- **Related:** `train_team` (`early_game.py:1979`) never consults `best_training_area` at all;
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

## KI-34 — the after-faint chooser LIVELOCKS when its candidate filter and the game disagree — ✅ **FIXED 2026-07-30; the index-space mapping is IN THE CODE TODAY** (`battle_handler.py:676-680` `_to_menu_order()`, `:683` `alive_slots_menu`). 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-06, to keep 05 under its R3 line budget; nothing deleted).

**2026-09-06 — ARCHIVED, NOT REOPENED.** The full entry (113 lines: the livelock trace, the
index-space diagnosis tables, and the A/B that proved the fix) moved VERBATIM to
`28-HANDOFF-ARCHIVE.md` to keep this file under its `lint_docs` R3 budget after `KI-91` and
`KI-92` were filed. ⛔ **Nothing was deleted and nothing changed status** — KI-34 remains FIXED
(2026-07-30), and `battle_handler.py:676-680` / `:683` still carry the mapping.
⭐ **WHY IT IS WORTH RE-READING RATHER THAN FORGETTING:** its shape — a candidate filter and the
game disagreeing about which INDEX SPACE they are in — has recurred three more times since
(`KI-18`, `KI-66`, and `#24-faintchooser-fourthspace`). ⇒ read the archived tables before
touching `handle_fainted_pokemon` again.
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


## KI-37 — a listener above the mode can STARVE it, so a handed-over battle fault is never claimed — ✅ **FIXED 2026-07-30.** ⚠ A follow-up remains; see the archived body. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-06, R3 line budget; nothing deleted).

**2026-09-06 — ARCHIVED, NOT REOPENED.** Full entry verbatim in `28-HANDOFF-ARCHIVE.md`; status unchanged (FIXED 2026-07-30, with its follow-up still recorded there). ⚠ Its STARVATION shape is live again in `KI-93`: a recognised wait branch that is exempt from the specific counter, so only the last-resort net fires.
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

## KI-41 — the Mauville→Route 112 corridor is sealed by a ROCK SMASH rock the planner treats as permanent — ✅ **FIXED 2026-07-31.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-06, to keep 05 under its R3 line budget; nothing deleted).

**2026-09-06 — ARCHIVED, NOT REOPENED.** The full entry moved VERBATIM to `28-HANDOFF-ARCHIVE.md` to keep this file under its R3 budget after `KI-91`, `KI-92` and `KI-93` were filed. ⛔ Status unchanged: FIXED 2026-07-31.
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

## KI-43 — `_navigate_when_ready`'s escape hatch was budgeted EXACTLY like the watchdog, so it was dead code (2026-07-31) — ✅ **FIXED, PROVEN AND GATED.** ⛔ DO NOT REOPEN.

**The fix, and the oracle for it:** `global_navigation.py:244` defines `_TRANSIENT_WAIT_FRAMES = 600` and `_navigate_when_ready` uses THAT, not the 18,000-frame watchdog cap — so the escape hatch can actually fire. Gate: `repro_watchdog_budget_collision.py`.
‼ **The header said "FIX NOT YET APPLIED" for three weeks after it shipped** (corrected 2026-08-22, PASS 5) — the standing lesson that PRODUCTION IS THE ORACLE, not a KI header.
⛔ **RETIRED TO A SUMMARY 2026-09-03 (line budget) — SUMMARISED AND POINTED AT, NEVER DELETED.** The full investigation (the batch3 `9 → 143` caveat, the refuted journey-length hypothesis, and the `fea2bb19` regression it actually was) is in `07-CHANGELOG.md` 2026-07-31 and `31-KNOWN-ISSUES-ARCHIVE.md`.

## KI-44 — ✅ **FIXED 2026-08-01 (root cause found the day after it was opened). FULL ENTRY ARCHIVED VERBATIM to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-09-05** — Counter training could not REACH its training grass because ROUTE102 is unwalkable from ROUTE103. ⛔ Retired here only to keep this current-state file inside its 3000-line budget; the diagnosis, the fix and its A/B are intact in the archive.

**2026-09-05 — body retired, status re-confirmed unchanged.** KI-44 is CLOSED and stays closed:
the fix is `ROUTE102` reachability from `ROUTE103`, shipped 2026-08-01 and unchanged since. No
new evidence, no reopening — this line exists because a header edit and its body must move
together (pair P2), and retiring a body is still editing it.

## ✅ KI-45 — a battle MOVE-menu loop hung a lane indefinitely. **FIXED 2026-08-02.** 📦 ARCHIVED 2026-09-07

Full entry in `28-HANDOFF-ARCHIVE.md`. Closed over a month; moved for the R3 line budget. ‼ Kept as a pointer because it is the ANCESTOR of `KI-47`, `KI-93` and `KI-96` — the same class of unbounded battle-menu loop, and the first one this project paid for.

## KI-47 — The battle path has a CLASS of unbounded loops; the existing watchdog is STARVED by them (2026-08-04, NET ADDED)

> ⭐⭐ **2026-09-03 — THIS CLASS NOW HAS A DETERMINISTIC, ~22,000-FRAME REPRODUCTION.** It has only
> ever been seen opportunistically, in batches, at a cost of *"a whole lane"* per hit. One command:
> ```
> cd tools/story-dev && POKEBOT_CH22JUAN_JITTER=181 PYTHONUTF8=1 py -3.12 story_harness.py >     post_hm07.ss1 --driver ch22chapter --frames 300000
> ```
> **MEASURED:** at `f21520` the KI-47 net fires exactly as designed —
> `BotModeError -> Manual: KI-47: battle sub-handler 'handle_battle_action_selection' ran 3001
> frames with no battle progress (frozen at ('BattleScript_MoveEnd',
> 'HandleTurnActionSelectionState', 'LearnMoveState.DialogueNotActive', 398269))`, in the JUAN
> fight, stuck in `PARTY_MENU` on `bt='What will SCEPTILE do?'`. Stall state saved to
> `stalls/repro-ml-f19485.ss1`; full transcript
> `evidence/2026-09-03-ch22chapter-DRIVE3-KI47-FREEZE.txt`.
> ✅ **THE NET WORKS** — bounded, named, no hang. ⛔ **AND THE RUN STILL DIES**: the drop to Manual
> happens in the main loop's battle listener, OUTSIDE the story generator, so the driver's own
> try/except never sees it and **no `ACCEPTANCE` line is printed at all**. ⇒ grade a §Ch22 chapter
> transcript that ends with no ACCEPTANCE and a `BotModeError -> Manual` as *this*, not as a hang
> and not as a §Ch22 defect. (Same convention as §Ch20's `ch20room9`, whose lost runs also print
> nothing and cannot.)
> ⚠ **HYPOTHESIS, NOT A FINDING — do not build on it without a probe:** the frozen state name is
> `LearnMoveState.DialogueNotActive`, and Sceptile levels **50 → 51** during this fight in every
> winning run. A mid-battle level-up move-learn prompt landing inside action selection is the
> obvious suspect, and it is exactly the kind of thing this project has been wrong about before.
> ⚠ **The repro is deterministic for a fixed (save, driver, code) triple** — measured. Any change
> to the battle path re-rolls it, so re-verify the command still reproduces before using it as an
> A/B baseline.

> ---
>
> ⭐⭐ **AND AS OF 2026-09-03 THE MECHANISM IS *PROVEN*, NOT INFERRED — decoded out of the saved
> stall state's EWRAM, read-only.** ✅ I re-read both load-bearing lines myself.
>
> **WHAT THE BOT DID:** `battle_action_selection.py:269-291`, the `TurnAction.RotateLead` branch,
> drove the in-battle party menu onto **the Pokémon that was already on the field**. The game
> refused. From `tools/story-dev/saves/stalls/repro-ml-f19485.ss1`:
> ```
> gStringVar4  = 'SCEPTILE is already\nin battle!{CTRL09}'      ({CTRL09} = FC 09 = PAUSE_UNTIL_PRESS)
> gPartyMenu.slotId = 0   menuType = 1 (PARTY_MENU_TYPE_IN_BATTLE)
> gChosenActionByBattler = [2,...]  (2 = B_ACTION_SWITCH)   gActionSelectionCursor = [2,0,0,0]
> gPlayerParty[0] = SCEPTILE 26/138  (the mon on the field)
> ```
> `TrySwitchInPokemon` (`src/party_menu.c:5824`) refuses, `CursorCb_SendMon`'s failure arm
> (`:3505-3520`) calls `DisplayPartyMenuMessage(gStringVar4, TRUE)` and hands off to
> `Task_ReturnToChooseMonAfterText` — which is exactly the task pair the stall log shows.
>
> ⛔ **AND THE HANG SITE IS AN UNBOUNDED LOOP — one of KI-47's own 32.** ✅ Read by me at
> `modules/battle_action_selection.py:288-291`:
> ```python
> while get_game_state() == GameState.PARTY_MENU:
>     context.emulator.press_button("A")
>     yield
> ```
> No counter, no `break`, no `raise`. Its ONLY exit is the game leaving `PARTY_MENU`, which the game
> will not do while it sits on a refusal message that returns to the chooser.
> ‼ **AND THE EXISTING KI-46 BOUND CANNOT SAVE IT:** `unrecognised` is only incremented in the
> "no branch matched" paths (`:96`, `:117`), so once control is inside the `match action:` block the
> counter is frozen at 0 forever. Only `handle_battle._watch`'s 3,000-frame net fired.
>
> ⚠ **WHY THE CURSOR WAS ON SLOT 0 IS *NOT* EXPLAINED, AND THAT IS THE LOAD-BEARING GAP.** Three
> index spaces are conflated on this path and all three are MEASURED divergent in this state —
> `battling_pokemon[i].party_index` is a **battle** party id (`gBattlerPartyIndexes`),
> `map_battle_party_index` inverts *menu slot → battle party id*, and `scroll_to_party_menu_index`
> drives `gPartyMenu.slotId`, which the game uses as a **live `gPlayerParty` index**. But a
> reconstruction of `select_rotation_target` predicts slot 4, not 0, under every ordering tried.
> ⛔ **DO NOT BUILD A FIX ON THAT GUESS.** This is the `handle_fainted_pokemon` shape a fourth time
> (KI-18, KI-34, KI-66, `#24-faintchooser-fourthspace`), and the standing rule is that a coordinate
> or index conversion gets its DIRECTION MEASURED before it is applied.
> ⇒ **THE NEXT STEP IS AN OBSERVE-ONLY PROBE, filed as `#24-ki47rotatelead`:** log `index`,
> `in_battle_index`, `gBattlePartyCurrentOrder`, `gBattlerPartyIndexes` and the live cursor
> **immediately before** the A-spam, and again right after `scroll_to_party_menu_index` returns
> (the party order is observed to change 35 frames after the decision, so a stale conversion is a
> live candidate). ‼ Instrument the value the code ACTS on, not the candidate list.
>
> ✅ **REFUTED, so nobody re-opens it:** the mid-battle level-up hypothesis this entry carried.
> `LearnMoveState` is OUR enum (`modules/battle_move_replacing.py:18`), its value in the frozen
> tuple is `DialogueNotActive`, `ml_tasks=[]` in every sample, and Sceptile is still **L50** in the
> run's final moveset dump — the 50→51 level-up never happened in this run at all.
>
> ⚠ **SECOND FINDING, and it is about the INSTRUMENT:** `_progress_sig`
> (`battle_handler.py:257-269`) is built from the script instruction, the main callback, the
> learn-move state and total exp — **none of which a party-menu ping-pong changes.** So the 3,001
> "no progress" frames may have been furious menu activity that the signature cannot see. ⇒ a
> KI-47 stall report means *"this signature stopped moving"*, NOT *"the game stopped moving"*.

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

## KI-50 — the Magma chapter is NOT a coin-flip: the `magma_door.ss1` fixture loses to Maxie for a measured reason — ‼ CORRECTED SAME DAY it was filed. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-06, R3 line budget; nothing deleted, status unchanged).

**2026-09-06 — ARCHIVED, STATUS UNCHANGED.** Full entry verbatim in `28-HANDOFF-ARCHIVE.md`. ⛔ Archived for the R3 budget only — NOT a closure, and its same-day correction is preserved there.
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

## KI-58 — ✅ RESOLVED/FIXED; FULL ENTRY in `31-KNOWN-ISSUES-ARCHIVE.md` (stub compacted 2026-08-16 on the 3000-line budget)

## KI-61 — ✅ RESOLVED/FIXED; FULL ENTRY in `31-KNOWN-ISSUES-ARCHIVE.md` (stub compacted 2026-08-16 on the 3000-line budget)

## KI-62 — the detector still names "To Lilycove" on a save long past Lilycove (2026-08-12, OPEN, LOW — ✅ header RE-CONFIRMED 2026-09-07: still open, still low, and its "to settle it" check has not been run)

Noticed while measuring KI-61 and deliberately **not** fixed, because it is a different question.
On `post_aqua.ss1` — 6 badges, the Aqua Hideout already completed — `current_chapter()` returns
**ch16 "To Lilycove"**, whose milestone is `MET_RIVAL_LILYCOVE`. Either our runs reach Lilycove
without triggering that rival meeting, or the flag is the wrong completion proxy for that chapter.

‼ Consequence: the detector's report is a **lower bound** on progress, not a position. Anything that
reasons from `chapter_key` (the endless-run stage label, resume messages) may understate how far a
save has got. `probe_chapter_order.py` deliberately does not assert on this save, and says why.
**To settle it:** check `MET_RIVAL_LILYCOVE` across the anchors that have plainly passed Lilycove,
and if it is unset on all of them, the milestone is wrong rather than the run.

## ✅ KI-63 — RESOLVED 2026-08-13: the bot acquires DIVE BY PLAYING. 📦 ARCHIVED 2026-09-07

Full entry in `28-HANDOFF-ARCHIVE.md`. Closed for over three weeks and nothing in it is a live
constraint; moved for the R3 line budget. **In one line:** the fear was that HM08 would sit in
the bag with no party member able to learn Dive and no free slot — it does not, because the
bot reaches Dive through ordinary play.

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


## KI-74 — `setmetatile` tiles are INVISIBLE to the shared map model, and the KI-59 fix made that fail-DANGEROUS instead of fail-safe (2026-08-13, code-verified, **STILL OPEN — but as of 2026-09-01 it is OBSERVABLE, and it has now COST A DRIVE**)

- ‼‼ **UPDATE 2026-09-01 — THIS STOPPED BEING THEORETICAL.** §Ch21 leg 3's first drive walked out of
  the Sootopolis Poke Center and jammed at `SOOTOPOLIS_CITY (31,42)`:
  `UnreachableDestinationError: the field is idle and we are still at (31,42), so retrying cannot
  change the result`. Our planner had returned a confident route whose FIRST waypoint `(31,43)` sits
  inside a **9x3 block (x=27..35, y=43..45) that is collision-0 to us and collision-1 to the game**.
- ✅ **AND THE FIX THIS ENTRY ASKED FOR IS NOW BUILT.** This KI's own "what a fix looks like" said:
  *promote `gBackupMapLayout` into a "live grid" mode for the CURRENTLY LOADED map only.* That now
  exists twice over: **`tools/story-dev/probe_live_mapgrid.py`** (offline, any save state, with a
  CALIBRATED border offset — it scores 7 at 99.6% while every other candidate lands between 46% and
  74%, so a wrong offset reports as a broken control rather than as a divergence) and
  **`sootopolis._live_collision_grid()` / `_live_wall_tiles()`** in production, which refuse to run
  unless the avatar is standing on the map being asked about.
  ⛔ **It is NOT yet promoted into `modules/map.py`, so it is still opt-in per chapter** — which is
  why this KI stays OPEN rather than closing.
- ⛔ **THE PRECISE MECHANISM, now pinned to a line** (and it is the SHARED root of this KI and
  KI-73): `map.py:735-755` caches each map's 24-byte layout struct in `_map_layout_cache` keyed by
  **`(rom id, map)` ALONE**. It does not record whether the bytes came from the LIVE `gMapHeader`
  (`get_map_data_for_current_position`) or the STATIC ROM `gMapGroups` table (`get_map_data`).
  **Both writers populate the same entry, so whichever reader touches a map FIRST wins for the whole
  process — and `calculate_path` silently inherits that choice.** MEASURED two-armed: static-seeded,
  SOOTOPOLIS `(43,32)->(29,53)` is 37 waypoints; live-seeded it is 35. *The seeding order changes
  production's own answers.*
- ⇒ **A CONSEQUENCE WORTH KNOWING BEFORE YOU WRITE A PROBE:** any instrument that compares
  `get_map_data_for_current_position()` against `get_map_data(...)` **cannot report a difference**,
  because both return the same cache entry. `CH21_LAYOUT_PROBE` was exactly that shape and its
  2026-08-27 "no swap visible" reading has been **retracted** (see `29-DISABLED-FEATURES-REGISTRY.md`).
  A working comparison must dereference `gMapHeader` itself, as `sootopolis._route131_layout_reading()`
  does — it read `planner=0x08417FE4 live=0x0845C1B0 agree=False` live on ROUTE131.


- **The mechanism.** `modules/map.py:770` takes the layout pointer from `self._map_layout[12:16]` —
  the **compile-time ROM grid**. The engine's live grid is `gBackupMapLayout`, which is what
  `setmetatile` rewrites. `map.py` never reads it, so `get_map_data` / `get_map_all_tiles` /
  `calculate_path` are blind to **every runtime tile patch, on every map**.
- **This is not theoretical — it has already been paid for once.** The Mauville Gym barriers wedged
  runs 6-9 for exactly this reason; the fix was a LOCAL live-grid reader,
  `early_game.py:3972 _live_passable()` (`read_symbol("gBackupMapLayout")`), whose own comment says
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

## KI-76 — our CURRENT-SLIDE model ends the slide ONE TILE SHORT and in the WRONG MOVEMENT MODE — 🔶 **MIXED: ✅ SAFETY half FIXED and fault-tested; ⚠ CORRECTNESS half UNFIXED, tracked as `#24-ki76correctness`.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-06, R3 line budget; nothing deleted, status unchanged).

**2026-09-06 — ARCHIVED, STATUS UNCHANGED.** Full entry verbatim in `28-HANDOFF-ARCHIVE.md`. 🔶 Still MIXED: the SAFETY half is fixed and fault-tested; the CORRECTNESS half is still open under `#24-ki76correctness`. ⛔ Archived for the R3 budget only — this is NOT a closure.
### Defect 1 — the slide stops one tile early, and leaves the avatar notionally still surfing
`modules/map_path.py:340-353`:
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
**The precise mechanism** (audited 2026-08-13): `map_path.py:972` applies the `cost = 1000000`
warp-avoidance penalty to the neighbour **before** `:1013-1022` substitutes the slide destination for
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
  ⛔ **SUPERSEDED 2026-08-17 — this paragraph asserted three things that are now MEASURED FALSE OR
  DISCHARGED.** It read: *"Routes 132/133/134 carry ~10x the cavern's currents and are UNMEASURED
  for cycles … The cap is ~16x the longest real chain (32)"*. **They are measured now**
  (`probe_slide_endpoints.py`): **0 cycles** across all 4,384 chains with production following every
  cross-map chain on ONE shared budget, longest chain **77** (not 32 — that 32 was the CAVERN's
  longest, generalised), margin **6.6x** (not ~16x). ‼ And the *"route to … Ever Grande"* half is an
  OVERSTATEMENT: Ever Grande is a **Fly destination** (`modules/region_map.py:54`, verified in our own
  fork), so §Ch23 can bypass the currents entirely. ⚠ The Sealed Chamber / Regi arc *looks* like the
  real forcing function, but ⛔ **that half is UNVERIFIED** — the ROUTE134 `(60,31)` dive entry comes
  from a research NOTE that says so itself. Confirm it before calling anything unavoidable;
  `#24-ki76correctness` carries the exact check.
  ✅ What still stands: the cap **fails loud**, was **fault-tested** at `cap=3` (raised, naming the
  tile and map), and cannot alter any terminating chain (**A/B: probe output byte-identical**).
  `probe_current_edges.py` measured the `None`-unpack arming; `probe_slide_endpoints.py` measures
  the endpoints. ➡ Counts and priority: `03-PUNCH-LIST.md` → `#24-ki76correctness`.
* *(original wording)* **`_get_connection_for_direction()` can return `None`** (`map_path.py:435-439`) and is unpacked
  unguarded at `:258/264/272/278` ⇒ **`TypeError` inside `PathMap.tiles`** if a current ever sits on
  a map edge with no connection that way. Not reachable in Rooms 6/7 (interior currents);
  **UNVERIFIED for Routes 129-134 / Pacifidlog**, which are full of currents.
* **`MB_SLIDE_*` (0x44-0x47) is not modelled as forced movement at all.** Measured: **zero** in the
  Seafloor Cavern, so not armed here. (‼ "108/117 forced-slide tiles" is loose wording in our docs —
  they are all `*WARD_CURRENT`.)

### ✅✅ CONFIRMED LIVE 2026-08-17 — THE ENDS-ON-A-WARP DEFECT IS NO LONGER STATIC ANALYSIS

`--driver ki76warp` (NEW) staged the avatar on ROOM6 `(8,12)`, pressed EAST once onto `(9,12)`, and
recorded every tile of the slide. ⛔ **Nothing is fixed — this makes the fix's A/B possible.**

* **Our chain model is right — and here is the precise version of that claim.** Production
  predicted a COUNT and an ENDPOINT (`steps=9`, terminus `(14,8)`); the live slide took **exactly
  nine steps and ended exactly there**. ⚠ The intermediate tiles
  `(9,12)→(10,12)→(10,11)→(10,10)→(11,10)→(12,10)→(13,10)→(14,10)→(14,9)→(14,8)` were **NOT
  separately predicted** in the evidence — they are what the recorded tile TYPES imply, and the
  live trail matches that derivation exactly. *(An earlier draft of this bullet said "EXACTLY
  right, tile for tile", which credited the prediction with more than it made.)*
  ⇒ **the slide SIMULATION is not what is broken.**
* **The warp FIRES.** The avatar ends on `SEAFLOOR_CAVERN_ENTRANCE` — warp-arrival tile `(10,1)` at f+142, then the game's own auto-step to `(10,2)`, which is the FINAL settled tile the driver graded on — a different MAP. Our
  planner would have emitted `(14,8)` in ROOM6 as an ordinary resting waypoint — unpenalised and
  not marked `is_warp`.
* ‼ **AND A THIRD THING NOBODY ASKED FOR: `surfing=True` throughout the slide, `surfing=False` on
  arrival — THE AVATAR DISMOUNTS.** ⇒ a planner believing it is on `(14,8)` in ROOM6 and still
  surfing is wrong on **all three** of map, tile and movement mode.
* ✅✅ **AND THE OBVIOUS OBJECTION IS ANSWERED BY AN ARM, NOT BY AN ARGUMENT.** The default run
  HOLDS the direction button through the ride, so "the warp fired" could have meant "a held button
  kept pressing once we arrived". `KI76_RELEASE_EARLY=1` releases it the instant the avatar first
  moves: **released at f+9, and the ride is byte-for-byte identical** — same ten tiles, same frames,
  same warp, `ARM R`, `ACCEPTANCE: PASS`. Nine of the ten tiles and the entire warp happen with NO
  input held. ⇒ the button is exonerated by MEASUREMENT.
  📁 `evidence/2026-08-17-ki76warp-CONTROL-release-early.stdout.txt`.
* ⚠ **One thing left UNATTRIBUTED rather than explained away:** the avatar auto-steps from the
  warp-arrival tile `(10,1)` to the settled `(10,2)` ~29 frames after release. It is NOT the driver
  (no button is held by then, in either arm); it is most plausibly vanilla's own "step off the warp".
  ⛔ Not asserted — flagged.
⚠ **HONEST LIMITS:** this confirms the ENDS-ON-A-WARP defect. It does **NOT** confirm the DISMOUNT
defect in its own right — that one is about a slide ending beside walkable LAND, and what was seen
here is a dismount caused by a WARP transition. Related, suggestive, **not the same measurement**.
📁 `evidence/2026-08-17-ki76warp-RUN3-CONFIRMED.stdout.txt`.

### Not fixed, and why — ✅ NOW TRACKED as `#24-ki76correctness` (it had NO item until 2026-08-17)
Fixing defect 1 means teaching `map_path` a "slide ends in a dismount" concept, and defect 2 a
"slide ends in a warp" concept — both are changes to shared pathfinding that every mode depends on,
i.e. the KI-59 shape, and both need their own A/B. **For §Ch20 the cheap answer is the KI-72 rule
one level up: do not let the planner choose where a slide ends — pick the tiles explicitly and
assert them.** ⛔⛔ **SUPERSEDED 2026-08-17 — DO NOT ACT ON THE PARAGRAPH THIS REPLACES.** It said *"Confirm
`(14,8)` FIRST: its fixture already exists (`--driver ch20room6`, anchor `saves/post_dive.ss1`) —
surf onto Room 6 `(14,9)`"*. **Every operative noun in that sentence is now refuted:** `(14,9)` is
UNSTAGEABLE (Room 6 is one-way; 14 of 15 candidate staging tiles have NO PATH), `ch20room6`'s route
provably never visits `(14,8)`, and `post_dive.ss1` is VOLATILE. ✅ **The `(14,8)` flush was
CONFIRMED LIVE anyway**, by `--driver ki76warp` from `(8,12)` on the PINNED `post_dive_ki76.ss1`.
⚠ **What genuinely remains unverified is the `(3,19)` DISMOUNT** — Room 7 has no driver and no
anchor, so that needs a NEW fixture first; that is a deliverable, not a patch.
*(A Tier 2 cold-start audit found this block still commanding the finished work from the refuted
spec — the exact "rebuild finished work" trap this layer exists to stop.)*

---


## ‼ ARCHIVED ISSUES WORTH RE-READING — ⛔ MIXED STATUS: SOME ARE FIXED, SOME ARE NOT

⛔⛔ **READ EACH BULLET'S OWN MARKER. DO NOT ACT ON THIS HEADING.** These entries were moved to
`31-KNOWN-ISSUES-ARCHIVE.md` for the R3 line budget, **not** because they were all resolved — and
that file's header says *"issues that are now resolved live here"*, which is why they are re-listed
here to stay findable. ‼ **KI-59 ITSELF IS FIXED, A/B-PROVEN, GATED (#17) AND PROMOTED TO BOTH
FORKS** — what remains open is a NARROWER residual under it, plus KI-60.

‼‼ **THIS HEADING PREVIOUSLY READ *"OPEN ISSUES … do not conclude they are fixed"* AND OPENED WITH
*"Two OPEN, code-verified, unfixed bugs"* — directly above a bullet reading *"✅✅ KI-59 — FIXED …
GATED."*** An adversarial cold-start audit (2026-08-16) named it **the single most dangerous
inaccuracy in the docs**: a session that skimmed the heading would have re-run the full-ROM 518-map
sweep, rebuilt the entry-vector correction, re-added `PathTile.blocked_exit_directions` and re-proven
it on `VICTORY_ROAD_1F` — ~a day, for a bug that no longer exists. *(P2, the header-vs-body pair,
applied to a SECTION heading rather than a KI heading — the pair check had never been pointed at
section headings.)*

* **✅✅ KI-59 — FIXED 2026-08-13, BOTH HALVES, A/B PROVEN, GATED.** Entry vector corrected (all-True,
  clear `[opposite(D)]`) **and** a new `PathTile.blocked_exit_directions` added for the decomp's exit
  rule, checked on the SOURCE tile in the A* loop. **A/B on `VICTORY_ROAD_1F`:**
  `repro_impassable_dirs.py` exit **1 → 0**, **29/29 → 0/29** mismatches, and `calculate_path` went
  from **NO-PATH from every direction** (all 29 tiles invisible to the planner) to `OK len=1` on the
  legal approaches; the `MOSSDEEP_CITY` collateral control is **byte-identical** across arms. Now
  **gate #17**. ‼ `probe_shoal_tide.py` corrected in lockstep; its numbers re-derived on the fixed
  model are **unchanged (LOW 278 / HIGH 0)**. ✅ **PROMOTED 2026-08-14 — that promotion took drift
  to ZERO** (it had reached 5; `counter_hunt.py` and `pokemon_party.py` joined that day and went
  over with the rest, verified by driving `--build custom`). ✅ **drift was ZERO again as of 2026-08-14 — KI-78 Stage 1 was PROMOTED later the same day** (superseded: *drift is now 3 again*) —
  *(⚠ 2026-08-17: re-dated from "drift **is** ZERO again". It was a statement about 2026-08-14 written
  in the PRESENT tense inside a current-state file, so it read as a claim about today and the new
  claim-shape rule in `audit_doc_consistency.py` correctly asked about it. ⛔ The number was not
  changed — only the tense, to say what it always meant. MEASURE with `promote.py --check`.)* —
  KI-78 **Stage 1** (`pokemon.py`, `pokemon_party.py`, `pokemon_storage.py`) landed in sandbox
  AFTER that promotion and was NOT promoted AT THAT TIME. ✅ **It IS promoted now** (drift 0
  since 2026-08-17); this line read "has NOT been promoted" until a pass-2 gate caught it.
  Historical note, superseded: *"Sandbox only — promotion is the
  USER's call.** The original diagnosis and the retraction that reprioritised it are kept below.
* **KI-59 (original entry)** — `map_path` **INVERTS `Impassable *` directions**. ✅ **REAL** (decomp-verified).
  ⛔ **BUT ITS "ARMED IN THE SEAFLOOR CAVERN" HEADLINE IS RETRACTED, 2026-08-13, MEASURED.**
  The handler at `map_path.py:147` is the **`elif` of `if tile.collision != 0:`** (`:137`), so a
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

## KI-66 — the multi-battle hazard is BROADER than the faint chooser — 🔶 **PARTLY FIXED 2026-08-17 (DRIVEN); the residual is tracked as `#24-faintchooser-fourthspace`.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-06, R3 line budget; nothing deleted, status unchanged).

**2026-09-06 — ARCHIVED, STATUS UNCHANGED.** Full entry verbatim in `28-HANDOFF-ARCHIVE.md`. 🔶 Still PARTLY FIXED; the residual is `#24-faintchooser-fourthspace`. ⛔ Archived for the R3 budget only — NOT a closure. ⭐ Re-read its index-space diagnosis before touching `handle_fainted_pokemon`: that shape has now recurred four times.
### ✅✅ RECON 2026-08-16 — THE ITEM IS NOW BUILD-READY, AND ONE OF ITS SUB-CLAIMS IS NARROWED

⛔ **Read this before writing a line.** A Tier 2 cold-start agent tried to BEGIN this item and
could not: the handoff called it *"fully startable with zero input"* while naming no fixture and no
way to trigger the code. Both gaps are now closed by recon, and a third finding NARROWS the item.

**(1) AND (2) — THE FIXTURE AND THE FAINT MECHANISM: MOVED to `31-KNOWN-ISSUES-ARCHIVE.md`
(2026-08-17), because both are now EMBODIED IN THE DRIVER and its docstring documents them.**
‼ **Keep only the two facts:** the fixture is `--driver ki66faint` / `saves/at_steven_2f.ss1`; and
the faint is produced by staging ONE of our picks at **1 HP** before the battle (1, not 0 — a 0-HP
mon is never SELECTED), which needs no `gBattleMons` writer and stays faithful gameplay.

**(3) ⛔⛔ SUPERSEDED BY MEASUREMENT 2026-08-17 — THIS BLOCK'S "NARROWING" WAS WRONG.** It argued that
an "only ally candidates" state requires all three of our picks to be down, and that this equals the
game's LOSS condition. **Both halves are false, and the live run refutes them:**
* At faint #2 the candidate set WAS ally-only (`alive_slots=[4,5]`, allies `[1,4,5]`) while
  **Swellow was alive on the BENCH** — proven by its send-out at `f21009`. TWO of ours were down,
  not three. So the precondition is a BOT defect, not a game state.
* In a multi battle the player's side is `gPlayerParty[0..5]` — our three AND Steven's — so "all
  three of ours down" is not the loss condition at all. The run **WON**, `whiteouts=0`.
‼ *Derived by reading; refuted on first contact with the emulator. Left visible rather than deleted,
because it is the exact shape this project keeps paying for.*

### ✅✅ DRIVEN 2026-08-17 — `--driver ki66faint` — AND THE HEADLINE IS **NOT** WHAT FIRES

‼ **THE INSTRUMENT EXISTS AND WORKS. ⛔ DO NOT REBUILD IT.** `Ki66FaintMode` SUBCLASSES
`SpaceCenter2Mode` (so every run re-proves the party-selection + multi battle first), stages ONE of
our own picks at 1 HP before the battle — exactly two bytes, `data[86:88]` — and lets it faint in
real combat. Anchor `saves/at_steven_2f.ss1`. Transcripts:
`tools/story-dev/evidence/2026-08-17-ki66faint-RUN{1,2,3-instrumented}.stdout.txt`.
⛔ **SAFETY, AND IT MATTERS:** `SpaceCenter2Mode` CAPTURES `saves/post_space_center.ss1` on a PASS,
and that fixture is **not pinned** in `preflight.py` or `FIXTURES.md5` — an injected run overwriting
it would be SILENT and permanent. The driver disables capture AND re-hashes the file afterwards;
the hash was also recorded out-of-band before the first run. Verified intact every run.

**MEASURED (one deterministic trajectory; RUN1 and RUN2 are BYTE-IDENTICAL, so that is a replay
confirming determinism, NOT independent confirmation — n=1 trajectory, 2 faints):**

| | faint 1 | faint 2 |
|---|---|---|
| `alive_slots` | `[1,2,4,5]` | `[4,5]` |
| `ally_party_indices()` | `[1,4,5]` | `[1,4,5]` |
| ally slots present as CANDIDATES | yes (3) | yes (2 — **ALL** of them) |
| slot the chooser ACTUALLY ASKED FOR | **2 (ours)** | **3 (ours)** |
| menu-open → send-out | **59 frames** | **1263 frames** |

✅ **OBSERVER CONTROL:** RUN3 added the instrumentation (the requested-slot capture and the
press counter) and reproduced the SAME trajectory — identical milestone frames `f7908 / f7967 /
f19746 / f21009`. So the instrumentation does not perturb what it measures, which is what licenses
quoting RUN1's frame deltas beside RUN3's press count.

✅ **WHAT IS CONFIRMED:** `alive_slots` (`:633-636`) is built from the merged party with NO owner
filter, and it does drive A-vs-Down (`:739`, `:758-765`). Offering slots 1/4/5 is objectively wrong —
the decomp's `TrySwitchInPokemon` refuses them **unconditionally** in any multi battle.

⛔⛔ **WHAT IS REFUTED — AND THIS IS THE FINDING THAT MATTERS:** **the bot never ATTEMPTED an ally
slot.** It asked for slot 2, then slot 3 — both ours, `IS_ALLY=False` — because
`choose_new_lead_after_faint` DOES filter allies (`default.py:189-193`) and its pick is what
`:600 scroll_to_party_menu_index` receives. ‼ **A CANDIDATE IS NOT AN ATTEMPT.** Faint 1 is the
control: three ally slots in `alive_slots`, resolved in 59 frames, zero cost.
⇒ **AN A/B THAT FIXES ONLY THE ALLY FILTER WILL SHOW NO DIFFERENCE ON THIS FIXTURE**, and could
make things WORSE: removing 1/4/5 at faint 2 leaves `alive_slots` **EMPTY**, tripping the
`‼ NO ELIGIBLE REPLACEMENT — cannot succeed` branch (`:654`) as a FALSE alarm while Swellow sat on
the bench. ⛔ **Do not "fix" the ally filter on the strength of this run.**

‼‼ **THE REAL DEFECT THIS EXPOSED — `_on_field` IS IN THE WRONG INDEX SPACE (a THIRD instance in
this one function, after KI-18 and KI-34).** `_on_field` is built from `battler.party_index`
(`gBattlerPartyIndexes`, FIELD order) and compared against `get_party()`, which
`UpdatePartyToBattleOrder` has already permuted into BATTLE-SLOT order. At faint 2 it logged
`on_field=[1,3]` and thereby excluded **Swellow (slot 3), which was on the BENCH** — proven by its
send-out at `f21009` — while failing to exclude the ally that WAS active. That is what manufactured
the ally-only candidate set, and it is what cost **1263 frames vs 59** (21×), tripping the harness's
own `NO-PROGRESS x1200` alarm at `f20970` with `Task_ReturnToChooseMonAfterText` — the refusal
signature the code keys on at `:731`. ⚠ **486 party-menu presses** across the run.
⚠ **HONEST LIMITS:** no press/refusal counter existed per-faint until RUN3, and the give-up dump
only fires after 6000 frames, so *which* layer absorbed the cost (KI-38's refusal learning vs
`scroll_to_party_menu_index`'s own bounded walk) is **NOT determined**. No hang, no whiteout, chapter
PASSED — true for THIS configuration and under-measured as a general property (1263 frames is 21% of
the 6000-frame per-invocation bound, with only two refusable slots to burn through).

### ✅✅✅ FIXED AND PROMOTED TO BOTH FORKS 2026-08-17 (user-approved)

✅ **PROMOTED TO BOTH FORKS 2026-08-17, USER-APPROVED — drift was 0 at that point.** *(⚠ It is **1** as of 2026-08-23 — `early_game.py`, `#24-loopheadabort`, sandbox-only. Formerly **0** — the five sandbox-only files were promoted 2026-08-17; this KI was already promoted. MEASURE with `promote.py --check`.)* Proven by a THREE-POINT A/B against `--build custom`: BEFORE `on_field=[0,3]`/`[1,3]`, 2 faints, 486 presses → AFTER `on_field=[0,1]`, 1 faint, 361 presses → sandbox control IDENTICAL to AFTER. Restore point `restore/2026-08-17-pre-promotion-ki66-onfield`.

`_on_field` now maps through `BattleState.map_battle_party_index` before being compared against
`party_in_menu`, mirroring what `alive_slots` three blocks below has done since KI-34.

‼ **THE DIRECTION WAS MEASURED, NOT GUESSED.** Getting it backwards would have degraded EVERY
battle, so an OBSERVE-ONLY probe ran first (`--driver ki66faint`, RUN4) logging raw AND mapped side
by side, and the party dump independently established the truth:

| faint | raw (used then) | mapped | truth from the party dump |
|---|---|---|---|
| 1 | `[0,3]` | `[0,1]` | Sceptile(0) fainted + Metang(1) ally active ⇒ **{0,1}** |
| 2 | `[1,3]` | `[0,1]` | Mightyena(0) fainted + Metang(1) ally active ⇒ **{0,1}** |

⇒ `mapped` is right on BOTH faints and `raw` wrongly grabbed Swellow(3) on both.

**AFTER (RUN5):** `on_field=[0,1]` — correct — and `alive_slots=[2,3,4,5]`, which now CONTAINS our
bench mons instead of excluding them. Battle **Won**, `whiteouts=0`, chapter `ACCEPTANCE: PASS`.
⚠⚠ **HONEST LIMIT — THE AFTER RUN IS A DIFFERENT TRAJECTORY, SO DO NOT QUOTE A SPEEDUP.** Press
timing feeds battle RNG, so the run diverged: **one** faint instead of two, 361 party-menu presses
instead of 486. Those are NOT apples-to-apples and neither is a controlled measurement.
✅ **What IS controlled** is the correctness claim: `_on_field` now equals the truth the party dump
establishes, on every faint observed, before and after. The 1263-frame pathology did not recur.
⚠ The remaining faint resolved in ~89 frames (f7908→f7997).

✅✅ **SINGLE-BATTLE REGRESSION CONTROL — THE ONE THE GATES DID NOT COVER (2026-08-17).**
This filter runs in EVERY battle, and `map_battle_party_index` does **NOT** return its input
unchanged in a single battle (`battle_state.py:332-354` searches `_battler_party_order` and can
permute or raise). No gate drives a real faint in an ordinary battle, so a targeted A/B was run:
`--driver faintrepro --inject-shedinja-faint` on `route116team.ss1`, 120k frames, BEFORE vs AFTER.
**RESULT: IDENTICAL through the whiteout** — `STUCK-OW f6482`, `SAVED stall f7409`,
`NO-PROGRESS x1200 f7709`, `x3000 f9509` in BOTH arms; the sole diff is one extra idle-watchdog
line afterwards while both sit in Manual. ⇒ **the change is INERT in single battles**, which is the
regression that mattered. Transcripts: `evidence/2026-08-17-singlebattle-faint-{BEFORE-baseline,
AFTER-onfield-fix}.stdout.txt`.
⚠ A batch would NOT have answered this well: §0c records ~30 runs per 3-hour batch and that four
batches resolved nothing about run-level outcomes. This took minutes and is decisive.

⚠⚠ **OPEN QUESTION RAISED BY THE FIX — A POSSIBLE *FOURTH* INDEX SPACE, NOT ACTED ON.** With
`_on_field` corrected, the restored diagnostic reads
`alive_slots=[2,3,4,5](party-order) -> [1,3,4,5](menu-order)  [orders DIVERGE]` — so
`_to_menu_order` maps slot 2 to 1, and the sweep's candidate set no longer contains slot **2**,
which is the slot the strategy actually chose (`CHOSEN new_lead_index=2`). That mapping is
PRE-EXISTING KI-34 machinery, not introduced here, and the run still resolved (~89 frames, battle
WON). ⛔ **Deliberately NOT changed** — it needed its own probe and its own discriminator, exactly
as the owner filter does. Tracked so it does not orphan, as `#24-faintchooser-fourthspace`.
✅✅ **AND THAT PROBE RAN — ANSWERED 2026-08-17, `#24-faintchooser-fourthspace` IS CLOSED.
NO FOURTH INDEX SPACE IS DEMONSTRATED: the last cursor the sweep read before the menu closed
(**3**) IS in `alive_slots_menu` (**[1,3,4,5]**). The anomaly is REAL IN THE LOG and INERT IN
BEHAVIOUR. ⛔ DO NOT "FIX" IT, and ⛔ do not re-commission the probe — it exists and it ran
(commit `684d83a7`; the positive control on the pre-fix build, `cursor_reads=66, A-presses=239`,
is what makes that zero trustworthy). ⚠ Limits: refusal count APPROXIMATE, n=1 diverging faint.**
*(‖ This block read "it needs its own probe" for a day AFTER that probe had run and been
committed — a cold-start audit found `05` still commissioning finished work that `03` and `04`
both marked `[x]`. Corrected 2026-08-17.)*

✅ **SAFETY:** all gates PASSED when that landed (**25** at the time — ⛔ the CURRENT count is deliberately not repeated here; `run_gates.py` prints it and IS the authority. This sentence has now been stale at 25 AND at 26 — `run_gates.py` IS the authority) (measured), including `repro_multi_battle_partner.py`,
`repro_whiteout_abort.py` and the 114s `repro_gym_whiteout_guard.py` — this filter runs in EVERY
battle, not only multi battles, so those were the ones that mattered.
⛔ **STILL OPEN:** the owner filter itself (`alive_slots` has no OT check) is UNFIXED and remains
inert on this fixture — it needs its OWN discriminator, not this one. Sites `:541-545` (the `None`
fallback, no owner AND no on-field filter) and `_util.py:522-587` are also untouched.
Transcripts: `evidence/2026-08-17-ki66faint-RUN4-onfield-probe.stdout.txt` (before, with the probe)
and `...-RUN5-AFTER-onfield-fix.stdout.txt` (after).

✅ **NEXT, IN ORDER:** (a) ✅ DONE — fix `_on_field`'s index space — map through
`BattleState.map_battle_party_index` before comparing, exactly as `:659-680` already does for
`alive_slots`; (b) ⛔ **RETIRED 2026-08-17 AS UNRUNNABLE — it has no referent.** It asked to
"require faint 2's frame cost to collapse toward faint 1's", but the AFTER run the fix produced
has **1 faint, not 2** (`on_field=[0,1]`, 361 presses), so there is no faint 2 to measure. The
acceptance it was reaching for was already met by the THREE-POINT A/B recorded above;
(c) only then consider the owner filter, and **give it its own discriminator**, because this fixture
proves it is inert on its own.

⛔ *(SUPERSEDED 2026-08-17 — this line read "**NOT YET BUILT** — no driver was written and nothing here has been driven live". It was true when the recon above was written and is FALSE now: `--driver ki66faint` is BUILT, DRIVEN five times, and the `_on_field` defect it found is FIXED AND PROMOTED. ‼ It sat 64 lines under a heading saying FIXED AND PROMOTED — the exact "rebuild finished work" trap this layer exists to stop, and a third audit is what caught it.)*

**The right shape of the fix** is one choke point — `ally_party_indices()` already exists — rather
than a guard per call site. That is a battle-layer refactor touching every mode, so it is filed
rather than done.

## KI-67 (original 2026-08-12 filing) — MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-13)

✅ **KI-67 is FULLY CLOSED** — the closing write-up (the first driven whiteout recovery in this
project) is below. The original filing was archived on 2026-08-13 for the R3 3,000-line budget.
Keep only this: **a type-only guard cannot see an abort that an inner loop already replaced with a
fresh error** — hence `StoryAbort` plus the latch-keyed `reraise_if_aborting`.

---

## KI-67 — ✅✅ FULLY CLOSED 2026-08-12 (the FIRST DRIVEN WHITEOUT RECOVERY here) — FULL ENTRY MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-15). ⚠ **KI-67 ITSELF IS CLOSED; the swallow-site residual its body mentions is NOT KI-67's — it is tracked under KI-81 / `#24-abortswallow`.**

Moved on the R3 line budget when KI-79/KI-80 were filed; it is CLOSED and was 77 lines of a
CURRENT-STATE file. ‼ **Keep only what later work leans on:** the proof was the **FRAME DELTA**
(+7,789 / +7,087), **not** a count — a whiteout recovery that changes no count still moves the
clock; and the archived text's real value is its harness DESIGN NOTES (the four parts a driver
must mirror, and **why half a mirror is worse than none**). ⚠ Still open there: swallow sites
in `early_game.py` that should get the same one-line abort-aware guard, **enforced by an assert
rather than by prose**. ‼ **The count was `44` on custom / `36` on sandbox when MEASURED 2026-08-16 (`probe_abort_swallowing.py`, KI-81); ⛔ THE LIVE BASELINES ARE KI-81's TO STATE — see KI-81 (equal again at 23/23 since 2026-08-24; the per-fork split is history). This entry must not carry a live figure at all: its own header says the swallow residual `is NOT KI-67's`.** — ⛔ do not quote a figure from here, run the probe — ⛔ *this line read "~48", an ESTIMATE from before the probe existed, and it sat
beside the measured 44 with nothing saying which was which.* **Re-run the probe; do not trust either
number in prose** — it is the only thing that counts them.

## KI-65 — ✅✅✅ CLOSED 2026-08-16 (reproduced, fixed, A/B-proven, GATED #25, PROMOTED to both forks) — FULL ENTRY ARCHIVED VERBATIM to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-18

⛔ **DO NOT REOPEN OR REBUILD IT.** Archived under the R3 line budget, not because anything is
unresolved. ‼ **ONE RESIDUAL IS DELIBERATELY LEFT OPEN AND IS KEPT HERE SO IT CANNOT ORPHAN:**
the guards test `party_index is None`, which covers UNBOUND. They do **NOT** cover a
*legitimately bound but WRONG* index — `get_party_menu_cursor_pos` does not raise on a bad
cursor, it calls `set_manual_mode()` and returns **`slot_id = -1`**, and `get_party()[-1]` is
the LAST party member. That is a **wrong-mon, not an exception**, so it flows straight past
both guards. ⛔ This fix never claimed to address it. Read the archive for the full repro,
the three refuted recon claims, and the fixture that CANNOT test this bug
(`movelearn_hmwedge_*.ss1` — do not retry it).

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

- ⛔⛔ **2026-09-02 — A CLAIM THIS KI'S §Ch21 RESTATEMENT CARRIED IS MEASURED FALSE, AND THE
  CORRECTION MATTERS FOR ANY FUTURE EMERGE.** `sootopolis.py`'s trap list used to say *"`Emerge`
  preserves (x,y), so the underwater tile IS the city tile."* Measured by `--driver ch21leg5probe`
  and reproduced by `--driver ch21return`: surfacing from `UNDERWATER_SOOTOPOLIS_CITY (9,7)` lands
  at `SOOTOPOLIS_CITY (29,53)`. `Underwater_SootopolisCity_OnResume` runs
  `setdivewarp MAP_SOOTOPOLIS_CITY, 29, 53` — a **FIXED** destination that ignores where you
  surfaced from. ⇒ the KI's core danger is UNCHANGED and still real (the guard checks only the
  underwater tile type, and this map has none of the two blocking types), and the hard-coded (9,7)
  is still right — but **the city tile must be READ, never derived from the underwater one.**
  Anyone routing a different emerge point on a map with a `setdivewarp` would have been misled.
  Corrected in place at `sandbox-pokebot/modules/story/sootopolis.py:25-40`.

- **The measurement** (verified directly, one grep):
  ```
  grep -rn "Underwater Blocked Above|Seaweed No Surfacing" modules/ --include=*.py
    modules/map.py:103                              -> "Underwater Blocked Above"
    modules/map.py:131                              -> "Seaweed No Surfacing"
    modules/modes/util/higher_level_actions.py:858  -> the ONLY consumer (surface_from_dive)
  grep -n "Underwater Blocked Above|Seaweed No Surfacing" modules/map_path.py
    (nothing)
  ```
  The tile reader emits both names; **`surface_from_dive()` is the only code in the tree that
  looks at them**; and `map_path.py` — the pathfinder — has never heard of either.
- **Consequence.** `map_path.py:352`'s generic fallback marks any tile_type it does not
  special-case as `accessible_from_direction = [True, True, True, True]`, at ordinary cost. So an
  underwater tile you can never surface from is, to the planner, plain open water — a perfectly
  good place to end a route.
- **The failure.** A chapter navigates underwater to a planner-chosen destination, calls
  `surface_from_dive()`, and gets
  `BotModeError: This tile does not allow surfacing from a dive.` (`higher_level_actions.py:947`, inside `surface_from_dive`, which spans `:933-953`).
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

## KI-73 — the map-layout cache is keyed on MAP NUMBER, but Shoal Cave swaps its floor plan at runtime, so the planner can route against a layout that is not on screen (2026-08-13, code-verified, OPEN — blast radius WIDENED 2026-09-02)

- ⛔⛔ **2026-09-02 — THE BLAST RADIUS INCLUDES `get_map_data_for_current_position()`, THE FUNCTION
  WHOSE NAME PROMISES THE OPPOSITE.** MEASURED by `--driver ch21leg5probe`: standing ON FOOT on
  ROUTE131 (36,7), a live sand tile, that function returned `tile_type='Deep Water'`. It builds its
  `MapLocation` from the LIVE `gMapHeader`, but `MapLocation._map_layout` resolves through the
  **shared** `_map_layout_cache` (map.py:745-755), which the run's own first `calculate_path` had
  already seeded STATIC for ROUTE131. ⇒ **on a layout-swapped map, a `tile_type` / `collision` /
  `elevation` guard is worthless until that map is pinned** — including the leg-1-style
  "refuse to dive unless the tile is Deep Water" assertions, which can read the wrong map's answer.
  The only trustworthy live oracle remains `_live_collision_grid` (`gBackupMapLayout`).
- ✅ **2026-09-02 — AND THE PIN IS PROVEN LOAD-BEARING BY AN ARM WITH IT REMOVED** (house rule 8),
  on ROUTE131 (which unconditionally runs `setmaplayoutindex LAYOUT_ROUTE131_SKY_PILLAR`):
  un-pinned, `calculate_path(ROUTE131 (36,7) -> ROUTE126 (45,66))` raises `PathFindingError` and the
  bot never moves — a PLANNING failure, not a walking one. Pinned: 356 wp with 3 Surf mounts. The
  source tile's elevation reads **1 static / 3 live**, which is exactly what `map_path.py:916` seeds
  the start node from. Evidence `tools/story-dev/evidence/2026-09-02-ch21leg5probe-NOPIN131.txt`
  and `…-ch21return-fault-NOPIN131`.
- ⛔⛔ **2026-09-02 — AND THE LIVE-GRID INSTRUMENT ITSELF IS COLLISION-ONLY, SO IT IS A FALSE
  NEGATIVE BY CONSTRUCTION ON A MAP THAT REWRITES *PASSABLE* TILES.** Verified at three links:
  `sootopolis.py:934` keeps `(block & 0x0C00) >> 10` (collision bits only);
  `src/scrcmd.c:2044-2047` ORs `MAPGRID_IMPASSABLE` only when `setmetatile`'s 4th arg is TRUE;
  and `SootopolisCity_Gym_1F/scripts.inc` passes **FALSE** on every one. ⇒ in that gym the ice
  cracking under the bot is INVISIBLE to `_live_collision_grid` and `probe_live_mapgrid.py`,
  which will report **0 differences and PASS** over a catastrophically wrong model.
  ‼ The instrument did not become wrong — **it was always collision-only**, and §Ch21's hazard
  merely happened to be a collision change. ⇒ **success on one map is not validation for the
  class of problem.** The reader that works there is the METATILE ID (`block & 0x03FF`), or
  `get_event_var("ICE_STEP_COUNT")`. Detail: `ai-research-notes/2026-09-02-ch22-juan-BUILD-SPEC.md`.
- ⚠ **A pin can also be a NO-OP, and reporting one as a fix is its own defect.** SOOTOPOLIS_CITY at
  `SOOTOPOLIS_CITY_STATE=5` / `SKY_PILLAR_STATE=3` pins `0x083E6A04 -> 0x083E6A04` and a whole-map
  live-vs-static collision diff finds 10 differing tiles of which **0** are open-to-planner/wall-live
  (all ten are `static=1 -> live=3` door warps locked by `SootopolisCity_OnLoad`). ⇒ always log what
  the pin CHANGED, and grade on the direction of the difference, never on the count.

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

## KI-78 — ⛔ PERSONALITY VALUE IS NOT A UNIQUE IDENTITY IN GEN 3: a SHEDINJA carries the SAME PID as the NINJASK it evolved from (2026-08-14, ✅ STAGE 1 FIXED, GATED and PROMOTED TO BOTH FORKS — ⚠ RESIDUALS OPEN) — FULL ENTRY in `31-KNOWN-ISSUES-ARCHIVE.md`

Moved 2026-08-16 on the 3000-line budget. ‼ **Keep only what later work leans on:**
- **The defect:** a PID-keyed lookup can RELEASE THE WRONG POKéMON — permanent, unrecoverable.
  The identity is `(personality_value, species)`, never the PID alone. Gate:
  `repro_pid_identity_key.py` (also runs `--build custom`).
- **Measured on our own fixture:** `ch13_fortree_door.ss1` holds a real Shedinja+Ninjask pair BOTH
  with `pid=42207D6F`, and a PID-keyed map reported a FULL PARTY OF 6 AS 5.
- ⛔ **NOT fully closed — residual cases stay OPEN:** debug-fabricated identical pairs, corrupt box
  slots, Frontier rentals, and the evolved-since-capture path (handled but **unexercised by any
  live caller**).

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

## KI-79 — `withdraw_from_box` PRINTED A SUCCESS IT NEVER VERIFIED (2026-08-15, ✅ FIXED, FAULT-PROVEN and PROMOTED TO BOTH FORKS — ✅ ITS RESIDUAL'S INSTRUMENTATION HALF IS DONE **AND PROMOTED TO BOTH FORKS 2026-08-17**; ⚠ THE REACTION HALF IS STILL OPEN, see below) — FULL ENTRY in `31-KNOWN-ISSUES-ARCHIVE.md`

Moved 2026-08-16 on the 3000-line budget. ‼ **Keep only what later work leans on:**
- **The defect:** `pc_trip.py:472-473` printed *"{name} is in the party"* after reading only
  `len(get_party())` — **a COUNT wearing an IDENTITY's clothes.** It now verifies
  `(personality_value, species)` **and** `contains_pokemon`, after a 2-frame yield, and prints a
  loud named failure instead of a green lie. Permanent fault hook `POKEBOT_PCWITHDRAW_FAULT`.
- ‼ **The method rule, which is the reusable part:** a byte-compare was NOT accepted as proof for a
  BEHAVIOUR promotion — a **THREE-POINT A/B** was (PASS before → FAIL after faulted → PASS after
  unfaulted), and run 1 is unrepeatable once the copy happens, so it runs and commits FIRST.
- ⚠ **THE RESIDUAL — HALF CLOSED 2026-08-17.** ✅ **The verdict now REACHES the caller:** all five
  exits return `(landed, code, detail)`, the ONE caller BINDS it, and a pure `withdraw_verdict_report`
  reports it — proven by a live two-armed A/B (`landed=True code=landed` unfaulted vs
  `landed=False code=did_not_land` faulted) and by gate #26 `repro_withdraw_verdict.py`, which
  **FAILED against the then-unpromoted `custom` tree (exit 1, six named sites) and now PASSES it
  (exit 0)** — that flip IS the promotion's proof.
  ✅ **PROMOTED TO BOTH FORKS 2026-08-17, USER-APPROVED**, in the five-file round; restore point
  `restore/2026-08-17-pre-promotion-all5`, drift 0, and verified by DRIVING custom
  (`--driver boxcounter2 --build custom` printed `verdict landed=True code=landed`).
  ⛔ **PROMOTION DID NOT CLOSE THE RESIDUAL:** production can now READ the verdict in BOTH forks and
  still cannot REACT to it. That half needs the unmeasured `sStorage->messageText` heap offset AND
  a USER ruling. *(This bullet read "⚠ SANDBOX-ONLY; a promotion is the USER's call" for one commit
  after the promotion — a Tier 1 reviewer caught it; the drift gate cannot see PROSE about
  promotion state, only figures.)*
  ⛔ **STILL OPEN: production READS the verdict but does not ACT on it** — what it should DO is the
  USER's ruling and is blocked on an unmeasured `sStorage->messageText` offset. `withdraw_from_box`
  still never raises for a PC problem, which is deliberate and unchanged. Its ONE caller is the
  `yield from` at `higher_level_actions.py:420` (inside the `try:` that opens at `:403`), which
  discards the value. **Tracked as `#24-orphans` item (1)**;
  its instrumentation half is specified, but *how* production should react needs the USER's ruling.

## KI-81 — KI-67's fix was applied to TWO chapters and the CLASS was never swept (2026-08-16, MEASURED by probe). ✅ **8 SITES FIXED AND PROMOTED TO BOTH FORKS** — the PC/heal path and the site that proved the sweep was incomplete. ⛔ **STILL OPEN: candidates remain (ALL in `early_game.py`)**, and ✅ **THE PROBE IS NOW GATE #27 — a RATCHET whose baselines ARE EQUAL AGAIN SINCE 2026-08-24: `{sandbox: 23, custom: 23}`** (`probe_abort_swallowing.py:218` is the authority; they DIFFERED `{31, 36}` between 2026-08-23 and the promotion, and were 36/36 before that — history, not today)**; ‼ ~64% of the original 45 were MEASURED not to be this defect, which is WHY it is a ratchet and not a zero-threshold

**2026-08-27 (deep sanity check, PASS 2):** the header above claimed the ratchet baselines
still `DIFFER PER FORK: {sandbox: 31, custom: 36}` — REFUTED by the shipped gate itself
(`probe_abort_swallowing.py:218` reads `{"sandbox": 23, "custom": 23}` since the 2026-08-24
promotion). Header corrected; the 31/36 and 36/36 figures are kept above as history.

**2026-08-23 — the baselines SPLIT (this entry's newest dated line; it is the body half of
the per-fork clause in the header above).** `#24-abortrecoveryresiduals` (b) guarded the 5
sandbox sites that `#24-loopheadabort` had newly exposed, so sandbox measures **31** and custom
was **36** until the fix was PROMOTED on 2026-08-24 (user-approved), when it became **23** — the
forks are EQUAL again and both read ZERO AST abort-swallowers. *(Superseded instruction: ON PROMOTION, LOWER custom
36 -> 31 IN THE SAME COMMIT** — otherwise the ratchet silently re-permits 5 sites of debt in
the fork that ships. ‼ Control-armed, not assumed: stripping exactly those 5 guards restores 36.
⛔ **A TIER 1 REVIEWER CAUGHT THIS PARAGRAPH FILED UNDER KI-79** — it had been inserted directly
ABOVE the `## KI-81` header, so by this file's own `##` convention it read as KI-79's trailing
text and a reader opening KI-81 would never have seen it. ⇒ **Anchoring an insert on a header
string puts it BEFORE that header. Verify WHERE a fix landed, not merely THAT it landed.**

`StoryAbort` is a `BotModeError`, which is an `Exception` (`_interface.py:229`) ⇒ **every**
`except Exception:` and `except BotModeError:` catches a whiteout. KI-67 found this and fixed the
two CHAPTER retry loops that had been *observed* failing (`space_center.py:962-977`,
`mossdeep_gym.py:540-556`, re-derived 2026-08-16 — it was cited as `:534-551`) with two guards — `except StoryAbort: raise` **plus**
`reraise_if_aborting(error)`. ⛔ **The class was never swept.**

**MEASURED:** `tools/story-dev/probe_abort_swallowing.py` (NEW, `--self-test` proves it fires when
the guard is missing and stays quiet both when guarded and when the `try` drives no generator) —
**53 candidate sites**: `early_game.py` 44, `higher_level_actions.py` 4, `pc_trip.py` 3,
`counter_hunt.py` 1, `mossdeep_gym.py` 1.
⚠ **CANDIDATE means "could swallow", not "does".** The probe cannot prove a `_check_abort()` is
reachable through a given `yield from`; it narrows 500+ handlers to a triageable list.

**THREE HAND-VERIFIED, and they are the bad shape, not false positives:**
- `early_game.py:1625` — `except Exception: ok = False` around `yield from _yield_bounded(...)`,
  then **presses B twelve times and RETRIES**. An abort here is swallowed into a retry on a dead run.
- `early_game.py:267` and `:3241` — `except BotModeError as e:` inside retry loops. ‼ This is
  **KI-67's failure verbatim**: *"a chapter that caught the abort and retried IN PLACE ran straight
  into the next `_check_abort()`"* — burning the budget in a few frames and reporting invented
  failures.
- ‼ **All three of `heal_in_pokemon_center`'s piggybacks** (`:297`, `:316`, `:345`) catch `Exception`
  with no guard, so a whiteout during a heal **was** swallowed and the bot walked on. ✅ **FIXED.**

✅✅ **RESOLVED FOR 8 SITES, AND PROMOTED TO BOTH FORKS (2026-08-16, user-approved).** The triage
question this entry posed — *"`mossdeep_gym.py` still shows 1 even though KI-67 fixed it; triage
starts there, because it tells you which the probe is"* — **IS ANSWERED: the `try` at `:465`
(handler `:471`) is a TRUE POSITIVE, and it is a DIFFERENT `try` from KI-67's, at `:540` (handlers
`:543`/`:554`)** — the gym-exit door loop. ‼ *Both numbers re-derived from source, and note the
units: `:465`/`:540` are TRY lines, the `Guarded:` list below gives HANDLER lines.* After a whiteout it tried the
second door **on a dead run** and raised a FABRICATED *"could not get out of the gym"* naming doors.
⇒ **the probe does not over-flag; KI-67's sweep was incomplete.**
**Guarded — ‼ these nine lines were RE-DERIVED FROM SOURCE 2026-08-16, not hand-copied** (six of the
eight I first wrote here were wrong; a Tier 1 reviewer caught it, and hand-transcribed citations are
how this project keeps burning a day). ⇒ **Re-derive, never re-type**, with:
`ast.walk` for every `ExceptHandler` containing a `reraise_if_aborting` call —
  `higher_level_actions.py` `:297` / `:322` / `:357` (the three heal piggybacks, each `except
  Exception`) and `:781` (`except BotModeError`, `talk_to_npc`'s surviving arm after the split);
  `pc_trip.py` `:202` / `:313` / `:550` (all `except Exception`);
  `mossdeep_gym.py` `:471` (the gym-exit door loop — **this KI's own find**) and `:554`
  (**KI-67's pre-existing guard**, which is why the fork totals 9 guarded handlers for 8 added).
`reraise_if_aborting(error)` is the FIRST statement of each — LATCH-keyed, so it also catches an
abort already laundered into a plain `BotModeError`. ⚠ **Line numbers drift on every edit above
them; the SHAPE is the durable claim** — *"guard first, latch-keyed, `PathFindingError` split out"*.
⛔ **AN ADVERSARIAL REVIEW CAUGHT A REAL DEFECT IN THE FIRST CUT:** `talk_to_npc`
(`modules/modes/util/higher_level_actions.py:718`, split at `:767` — ‼ it is NOT in `pc_trip.py`,
which is where a later doc pass first misfiled it) also catches
`PathFindingError`, a **`RuntimeError`, NOT a `BotModeError`**; re-raising one would have ESCAPED
`StoryMode.run`'s `except BotModeError` and left the global latch **stuck TRUE**, leaking into
`ev_train.py`/`pokecenter_loop.py`. Fixed by SPLITTING the handler. *A guard that can leak a global
is worse than the silence it replaced.*
✅ **Promotion proven by a MEASURED before/after, not a byte-compare:** `--build custom` fell
**53 → 45**, guarded counts moved **0→3 / 0→4 / 1→2**, and the split survived the copy.

⛔ **STILL OPEN — 36 CANDIDATES REMAIN** (ALL `early_game.py`; `counter_hunt.py`'s single
candidate was fixed 2026-08-17, when 8 sites were swept and the probe fell 45 → 37, MEASURED).
⛔⛔ **SUPERSEDED 2026-08-17 — REFINEMENT (2) IS REFUTED AND (1) IS SHIPPED. DO NOT BUILD EITHER FROM THIS PARAGRAPH.** It survived unmarked eight lines below its own refutation, and a cold-start audit called it the most expensive thing in the tree: acting on it rebuilds a day of refuted work and can ship a gate that HIDES real defects. *(superseded text:)* ‼‼ **AND THE TRIAGE MEASURED THAT THE PROBE OVER-FLAGS: ~64% of the original 45 are NOT this
defect** — 25 wrap navigation primitives containing no `_check_abort()`, so no `StoryAbort`
can arrive; `:376` IS the whiteout-recovery path; `:2305` already guards by hand in a shape
the probe cannot see. ⛔ **DO NOT PROMOTE THE PROBE TO A GATE AS-IS** — it would be red on
arrival for reasons that are correct as written. Two refinements cut 45 → ~16. *(A separate
family — retry loops needing a LOOP-HEAD check, not a handler guard — was `#24-loopheadabort`,
✅ DONE 2026-08-23: all 17 patched, gate #30. ⛔ An earlier 3-loop exclusion rested on a FALSE
claim that the recovery path runs with the abort latch set; it is withdrawn.)* 44 sites in the largest and most timing-sensitive file here is not a
tail-of-session sweep, and **CANDIDATE ≠ DOES** — the probe cannot prove a `_check_abort()` is
reachable through a given `yield from`. ⇒ ⛔⛔ **SUPERSEDED 2026-08-17 — THIS IS DONE AND ITS ADVICE IS REFUTED. The probe IS gate #27, a RATCHET; refinement (2) would blind it to five already-fixed sites and must NOT be built.** *(superseded:)* triage, fix, THEN promote the probe to a gate — The
triage MEASURED that ~64% of the candidates are not this defect, so the probe must be REFINED first;
see the paragraph above and `#24-abortswallow` round 3. *(This line was the last thing in the KI, so
a skimmer read it as the instruction — a cold-start audit caught exactly that.)*; it is a
PROBE precisely because a gate red on arrival on pre-existing debt teaches everyone to ignore gates
(`repro_no_silent_except.py` took this exact path). Tracked as `#24-abortswallow`.

## KI-80 — `grass_is_fodder` CONFLATED "no training patch configured" with "the patch is too weak", and it CO-GATED the counter-ladder (with `boss_teaches`, inside `losses >= 2`) — so giving a boss a training area silently disabled its KI-23 machinery. ✅ DECOUPLED AND PROMOTED TO BOTH FORKS 2026-08-16 (this KI's own file is in both forks) (2026-08-16, ✅ **REPRODUCED AND DRIVEN** — `--driver ki80ladder` is COMPLETE and PASSING: **4 arms**, both forks, mirror-regression guard fault-tested against the real naive edit. ✅ **AND THE DECOUPLING IS NOW BUILT, DRIVEN AND REVIEWED** — `:1901` is `if boss_teaches:`, `boss_mode` sits behind its own `if grass_is_fodder:`; `repro_boss_grass_gate.py` has SELF-RETIRED. ✅ **AND PROMOTED TO BOTH FORKS 2026-08-16 (user-approved), proven by a THREE-POINT A/B against `--build custom`; that file is in BOTH forks.** ⛔ **THIS KI STAYS OPEN ONLY FOR ITS TRACKED RESIDUAL** `#24-zerokocounter`: should `boss_teaches` come off the gate too? Not shipped because no arm can discriminate it, and an audit derived that it would need TWO new arms plus a frequency measurement first)

⛔ **FULL ENTRY MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-17)** on the R3 3,000-line budget.
The arc is CLOSED, FIXED and PROMOTED TO BOTH FORKS, so its 200+ lines of build history are no
longer current state. ⛔ **DO NOT REOPEN OR REBUILD IT.**

‼ **KEEP ONLY WHAT LATER WORK LEANS ON:**
* The coupling is GONE from both forks: `story_mode.py:1901` is `if boss_teaches:`, and
  `boss_mode = True` now sits behind its own `if grass_is_fodder:`. `repro_boss_grass_gate.py`
  SELF-RETIRED when the coupling was removed.
* ⛔ **The one-line version of this fix ships KI-23's MIRROR REGRESSION** — arm 4 of
  `--driver ki80ladder` measured it doing exactly that, and the 3-arm suite alone would have
  BLESSED the naive edit. If you ever touch this branch again, run arm 4.
* ⛔ **DO NOT add a row to `TRAINING_GRASS`** — `best_training_area` ranks ONE GLOBAL table, so a
  new row changes the pick for every other caller (the measured Shoal Cave incident).
* **Norman's L3-5 patch against a L27-31 band is DELIBERATE** — it is the fodder trigger for the
  only training relocation this bot performs (70-83% measured).
* ⛔ **THE RESIDUAL IS STILL OPEN:** `#24-zerokocounter` — should `boss_teaches` come off the gate
  too? NOT shipped, because no arm can discriminate it; an audit derived that it needs TWO new
  arms plus a frequency measurement first. Tracked in `03-PUNCH-LIST.md`.
* Reasoning also survives in `06-DECISIONS-LOG.md` and `28-HANDOFF-ARCHIVE.md`.

## KI-83 — ⚠ **`tasks_scripts.py` IS 8 UNBOUNDED, ABORT-BLIND WAIT LOOPS THAT EVERY CHAPTER CALLS.** ⛔ **NOT OURS AND DELIBERATELY NOT FIXED — bound it AT THE CALL SITE.** (opened 2026-09-03, MEASURED)

**What.** `sandbox-pokebot/modules/modes/util/tasks_scripts.py` is 162 lines containing **8 loops with no frame cap and no `_check_abort()`**, and the file contains **ZERO** of either (counted, not estimated): `wait_until_task_is_active` (:18), `wait_until_task_is_not_active` (:33), **`wait_for_yes_no_question` (:80, a bare `while True:`)**, `wait_for_multiple_choice_question` (:112), `wait_until_script_is_active` (:130), `wait_until_script_is_no_longer_active` (:138), `wait_for_no_script_to_run` (:152), `wait_for_fade_to_finish` (:160). The only bounded loop is a cursor-movement `for` at :121.
**Why it matters.** These sit under the most-used helpers in the tree. `heal_in_pokemon_center` (`higher_level_actions.py:340-341`) calls `wait_for_yes_no_question` then `wait_for_no_script_to_run` — **so every heal, in every chapter, runs two unbounded abort-blind waits.** If the expected task never starts, the generator spins silently forever and **`StoryAbort` cannot unwind it**, because nothing checks the latch.
**The reachable trigger is already documented in our own tree:** the KI-81 comments at `higher_level_actions.py:359-366`/`:387-392` exist because **a whiteout can happen INSIDE the heal call** (field poison ticks on the walk in). After a whiteout the menus are gone, so the awaited task never starts.
⚠ **This is the same SHAPE as KI-47** (an unbounded `while … PARTY_MENU: press A` that wedges the battle path), which is also deliberately unfixed.
✅⛔ **IT IS UPSTREAM CODE, BYTE-IDENTICAL TO THE PRISTINE MIRROR — we have never modified it** (`diff` against `40cakes repo/pokebot-gen3/…` is empty). ⇒ patching it is a **DIVERGENCE decision**, needs a `DIVERGENCE-LOG` entry, and has the widest blast radius in the codebase (every chapter, every menu). **That is why it is filed rather than fixed.**
⇒ ⭐ **THE MITIGATION IS LOCAL AND COSTS NOTHING: wrap the CALL in a frame budget** (§Ch23's `_budgeted(gen, budget, label)` closing the generator in a `finally`). Bound at the call site, upstream untouched.
‼ **How it was found, which is the reusable part:** an adversarial review of a *design* (before any code existed) audited the "never-hang" claim and noticed it had cleared `heal_in_pokemon_center` by checking the **exit** loops (`:443-472`) while the **nurse interaction three lines earlier** was unbounded. ⇒ *a never-hang audit must enumerate the loops the call REACHES, not the loops nearby.* I then verified every claim myself before filing.
⛔ **NOT A HANG WE HAVE OBSERVED** — no drive has wedged here. It is a latent hazard with a documented trigger, and it is recorded so the next hang in a heal is diagnosed in minutes rather than days.


---

## `KI-88` — ⛔ `teach_hm_or_tm` CAN REPLACE THE WRONG MOVE (upstream helper; NOT fixed, ROUTED AROUND)

**Status: OPEN, deliberately. Filed 2026-09-05 with a full measurement; upstream left untouched.**

**The defect.** `modules/modes/util/items.py::teach_hm_or_tm` A-mashes toward the move-learn
screen, looping while `not task_is_active("Task_DuckBGMForPokemonCry")` and pressing A every frame.
**The move-selection screen can appear BEFORE that task is observed** — and the next blind `press A`
CONFIRMS WHATEVER THE CURSOR IS ON, the default **index 0**. Its own navigation
(`for _ in range(move_index_to_replace): press Down`) never runs at all.

**⭐ TWO FAILURES, ONE BUG — AND THE DOCS FIRST TOLD THEM AS ONE** (a Tier 1 reviewer caught it;
the trace below is from drive 2, where Sceptile is CORRECT, so quoting it beside the Leaf Blade
incident was incoherent). **Drive 1, unmodified upstream:** asked for Sceptile's **Slam** (index 3),
replaced **index 2, Leaf Blade** — its STAB move — spending a single-use TM on the wrong move.
**Drive 2, after a closed-loop cursor:** Sceptile then steered correctly, but the A-mash still blew
past for two others and **Zigzagoon lost Tackle instead of Growl**. Both real; different runs.

**⭐ THE MEASUREMENT, because this is the interesting part.** Teaching four Pokémon with a
per-iteration cursor trace produced only **TWO** traces:
```
target=3 cursor reads=[0,0,0,1,1,2,2,3,3,3]   Sceptile  — navigation ran, CORRECT
target=0 cursor reads=[0,0,0]                 Swellow   — CORRECT
(Mightyena, Zigzagoon: NO TRACE — the block never executed)
```
⇒ Mightyena wanted index 0 and got index 0, so it **looked** correct. **It was luck.** Zigzagoon
wanted index 1, got 0, and lost **Tackle** instead of Growl.
‼ **A passing result from a code path that never ran is the most convincing kind of wrong.**

**Blast radius.** Only bites when the move to replace is **not index 0**. §Ch23 leg 1 (teach
Waterfall) uses this helper and passes, so it is a race, not a certainty.

**⛔ WHY IT WAS NOT FIXED.** Shared file, every chapter depends on it, and it holds several unbounded
loops; a partial fix **hung a drive** and was reverted (`git checkout`, byte-identical). ⇒ **routed
around**: `modules/story/pokemon_league.py::teach_move_from_bag` owns the whole flow, gates its
A-presses on the screen not being up, and refuses on an unknown cursor. **If ever fixed:** the
A-mash must stop the instant a move-selection task is active, and the cursor must be READ, not
counted — the closed-loop reader already exists at `battle_move_replacing.py:564`.

⚠ **A TRAP FOR WHOEVER TRIES:** the screen runs under **TWO** tasks at different phases —
`Task_HandleInputCantForgetHMsMoves` transiently, then `Task_HandleReplaceMoveInput`. Sampling the
task list ONCE catches the transient. ⇒ **a one-frame sample is not a contract.**


## `KI-89` — ⛔⛔ `scroll_to_item_in_bag` RETURNS SUCCESS WITH THE CURSOR ON THE WRONG ITEM (upstream helper; MEASURED 2026-09-05, NOT fixed, ROUTED AROUND)

**Severity: HIGH and SILENT.** It does not raise, does not warn, and does not look wrong from the
outside. The caller then presses A on whatever the cursor happens to be sitting on.

**MEASURED, one run, `--driver ch24teachice` on `post_icebeam.ss1`:**
```
[TEACH-CURSOR] after scroll_to_item_in_bag(TM13): pocket=2 slot=13 -> HM08
[TEACH-ITEM]   TM/HM pocket order = ['TM03','TM04','TM08','TM13','TM34','TM39','TM47','TM50',
                                     'HM02','HM03','HM04','HM06','HM07','HM08']
[TEACH-SAID]   0: 'DIVER already knows DIVE.'
```
Asked for **TM13 (Ice Beam)** it left the cursor on **HM08 (Dive)** — slot 13, not 3 — so the bot used
Dive on Wailord (nicknamed DIVER) and the game refused. `modules/menuing.py::scroll_to_item_slot`
scrolls the on-screen cursor to the slot number `first_slot_index_for()` returns, and for TM13 those
two numbers are not the same index space.

⛔ **WHY IT HAD NEVER BITTEN:** five earlier teaches — Aerial Ace, Facade, Strength, Rock Smash, Fly —
used items whose two indices COINCIDE. TM13 is the first item this save acquired out of that order.
⇒ ⭐ **A HELPER THAT HAS WORKED FIVE TIMES IS NOT A VERIFIED HELPER, ONLY AN UNMEASURED ONE.**

⛔ **BLAST RADIUS — this is NOT teach-only.** Every caller of `scroll_to_item_in_bag` /
`use_item_from_bag` inherits it: healing, Repels, Escape Ropes, evolution stones. The visible symptom
differs per caller and can be a NO-OP rather than an error (using the wrong potion still "works").
⚠ **NOT yet measured for those callers** — this KI records what one run proved, not a sweep.

**NOT FIXED UPSTREAM — A CASE-BY-CASE CALL, NOT A RULING.** ⛔ *(This read "same ruling as `KI-88`" until 2026-09-05. **There is no such ruling** — `KI-88` in turn cited `KI-83`, and nothing at the bottom of that chain was ever decided; see `06-DECISIONS-LOG.md` 2026-09-05. This is a ROOT LINK of the chain that entry retracts, and it was left standing for one revision after the entries citing it were fixed.)* The reason below is this defect's OWN reason and stands on its own: `modules/menuing.py` is a shared file
every chapter depends on, and a partial fix to its sibling hung a drive on 2026-09-05. Routed around
in `modules/story/pokemon_league.py::scroll_to_tm_verified`, which calls upstream, READS THE CURSOR
BACK out of `gBagPosition`, corrects it closed-loop and BOUNDED against `get_item_bag().tms_hms`, and
**RAISES rather than press A on an unverified cursor** (a Gen-3 TM is single-use).

‼ **THE DIAGNOSTIC LESSON IS BIGGER THAN THE BUG.** SIX diagnoses were spent downstream of this, every
one about the PARTY menu, because the item side had been "verified" by printing the pocket's CONTENTS
— which is not the cursor. ⇒ ⭐ **A CANDIDATE IS NOT AN ATTEMPT: instrument what A acts on.**

📌 The exit the game actually took is path **E** of
`ai-research-notes/2026-09-05-ch24-TMHM-TEACH-CHAIN.md` (`gText_PkmnAlreadyKnows`), confirmed
independently by a decomp read.


## `KI-90` — in a DOUBLE battle with one opponent slot absent, the bot aimed at the empty slot and the run hung — ✅✅ **FIXED 2026-09-05** (`battle_action_use_move` aims at the RIGHT opponent; gate #38 SELF-RETIRED) and ✅ **PROMOTED to `custom-pokebot/` 2026-09-06.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-06, R3 line budget; nothing deleted).

**2026-09-06 — ARCHIVED, NOT REOPENED.** Full entry verbatim in `28-HANDOFF-ARCHIVE.md`; status unchanged (FIXED 2026-09-05, PROMOTED 2026-09-06). ⚠ Two observations from it are still LIVE and are why it is worth re-reading: the **both-absent branch still raises** (believed unreachable, never traced), and **any exception from `BattleListener` sets Manual** — the sibling-controller containment problem, which `KI-93` brushed against.
## `KI-91` — a 1,200-frame NO-PROGRESS stall inside §Ch23 leg 11, self-recovered (2026-09-05, MEASURED; ⚠ OPEN, not diagnosed)

**Symptom.** The §Ch23 chapter chain logged
`f65015: !!! NO-PROGRESS x1200 sig=(... (16, 4)) instr=BattleScript_GotAwaySafely
cb=ReturnFromBattleToOverworld bt='Got away safely!'` with the generator stack
`Ch23ChapterMode.run -> do_victory_road_chapter -> stock_for_the_elite_four -> wait_until_truly_controllable`.
It **recovered on its own** by ~f66446 and the run went on to `ACCEPTANCE: PASS`.

**What is known.** The bot was standing on `LEAGUE_MART_STAND (16,4)`, i.e. leg 11 had arrived at the
clerk. The overworld callback was still `ReturnFromBattleToOverworld` with a stale
`BattleScript_GotAwaySafely` instruction and a text printer cycling — the same "STUCK-OW" shape logged
repeatedly earlier in the run after wild-battle escapes. ⇒ the likely story is that
`wait_until_truly_controllable` waits out a battle-return tail that takes >1,200 frames when a
`Got away safely!` message is still draining.

**⚠ WHY IT IS FILED RATHER THAN FIXED.** It did not affect the outcome and I have not reproduced it in
isolation, so any fix would be speculative. ⛔ But a 1,200-frame stall at the LAST leg of the chapter is
worth a name: if the chapter ever hangs at the shop, this is the first thing to read.
‼ It is filed because the changelog said *"file rather than forget"* and a Tier 1 reviewer checked
whether that promise had been kept — **it had not.** ⇒ ⭐ **A PROMISE TO FILE IS NOT A FILING.**

**Next step if it recurs:** capture the stall save (`stalls/repro-ml-f65015.ss1` was written by the
harness, but that directory is gitignored and its names are REUSED — copy it out first, the trap
`ki90_double_absent_seed.ss1` already records), then drive `post_league_heal.ss1 --driver ch23shop`
and watch for the same `ReturnFromBattleToOverworld` tail.


## `KI-92` — `audit_doc_consistency` is BLIND to drift claims buried in `04-HANDOFF.md`'s banner line (2026-09-06, ⛔ FAULT-PROVEN, OPEN)

**Symptom.** The §Ch19→§Ch23 promotion took drift 14 → 0. A sweep corrected nine sites and the gate
returned **PASS** — yet a **10th** live claim survived, ~17,400 characters into `04-HANDOFF.md`'s
YOU-ARE-HERE banner (a **single line of 39,825 characters**):
> `⚠ **DRIFT IS <the pre-promotion figure> as of 2026-09-04 (⬆ from …) … ⚠ PROMOTION IS THE USER'S CALL and is NOT implied here`
> ‼ *(the figure itself is deliberately NOT reproduced here — see the rule below)*

A Tier 1 reviewer found it by reading. **The gate did not.**

**⛔ FAULT-PROVEN, NOT INFERRED.** I injected a literal stale claim back into the same region and re-ran
the gate:
```
inject at offset 17400 of the 39,866-char banner a literal stale drift claim of the form
  ' ⚠ **DRIFT IS <pre-promotion figure> as of 2026-09-04.** '
audit_doc_consistency.py  ->  "all consistency checks PASS across 7 current-state files"   exit 0
```
⇒ **the gate cannot see a drift claim at that position.** (The injection was reverted from a backup
and the revert verified: the corrections present, the injection absent, all gates green.)

**Why it matters.** This gate is the project's strongest doc instrument — it MEASURES drift by running
the comparison and checks claims against the measurement, and it found nine sites in one pass. Its
blind spot is therefore expensive: **a green PASS here reads as "no stale drift claim exists"**, and
that is exactly the false confidence `promote.py`'s own scope note warns about for a different check.

**⚠ NOT YET DIAGNOSED.** Candidate causes, none confirmed: the banner's "unit" may be exempted by a
`_QUOTED` / supersede span elsewhere in the same 39k-char line; `_SUBJECT_WINDOW = 90` proximity may
resolve differently at that offset; or the unit-splitting may cap. ⛔ Do not "fix" it by widening a
regex until the mechanism is known — this gate's own comments record two previous false-positive
rounds caused by exactly that.

**Reproduce:** copy `04-HANDOFF.md`, splice a stale drift claim (`⚠ **DRIFT IS <old figure> as of
<old date>.**`) into line 10 at offset ~17400, run `audit_doc_consistency.py`, observe PASS. ⛔ **Restore from the copy afterwards.**

**⇒ THE STRUCTURAL POINT, worth more than the bug:** a 39,825-character single line defeats every
instrument that reasons per line or per unit — mine and the gate's alike. Splitting that banner is
probably the real fix, and is a bigger change than this entry.

‼ **AND THIS ENTRY ITSELF TRIPPED THE GATE ON ITS FIRST DRAFT** — it quoted the stale figure verbatim, twice, in the very entry whose lesson is *retract measured numbers by DELETING and POINTING, never by quoting*. ⇒ ⭐ **the gate caught its own documentation**, which is the strongest evidence that the rule is real and that the habit, not the gate, is the problem.


## `KI-93` — the move chooser ignored **TORMENT**, spun for ever, and `KI-47`'s net stopped the bot — ✅ **FIXED IN THE SANDBOX 2026-09-06, DRIVEN CLEAN** (✅ **PROMOTED 2026-09-07 with USER AUTHORISATION and VERIFIED BY DRIVING** (`--build custom`: `BattleOutcome.Won`, `KI-47` stops 0, `grade_ki93_drive.py` C0-C3 PASS; rollback tag `pre-promote-2026-09-07`)). ‼ It was a CLASS bug: any battle message ending in `\p` hung identically.

📦 **The entire pre-fix investigation is ARCHIVED VERBATIM** → `28-HANDOFF-ARCHIVE.md`
(2026-09-06): the original measurement, the four failed fix attempts, the three VOID verdicts
produced by a broken logger, the REFUTED function-local design, and the census drive that
refuted it. Nothing is deleted — this file holds OPEN problems, and what remains open about
`KI-93` is only that the fix is **unpromoted**.

**One-line restatement:** a battle message ending in `\p` parks the text printer waiting for an
EDGE-TRIGGERED button press with no timeout, and the bot's wait branch pressed nothing — so it
yielded for ever while the game waited for it. Torment is simply the refusal the Elite Four
guarantees; **61 battle strings end in `\p`** and every one hung identically.

⭐ **The one fact worth carrying out of the investigation:** the census measured
`handle_battle_action_selection` being **RE-ENTERED ~5 times per refusal episode**, which is why
the refusal memory must be MODULE-LEVEL. The design this entry carried for a day put it in a
function-local and could never have worked — and nothing in the text signalled that.

### ✅ 2026-09-06/07 — FIXED, RE-DRIVEN, GRADED CLEAN BY A FAULT-PROVEN INSTRUMENT. ✅ **PROMOTED 2026-09-07 with USER AUTHORISATION and VERIFIED BY DRIVING** (`--build custom`: `BattleOutcome.Won`, `KI-47` stops 0, `grade_ki93_drive.py` C0-C3 PASS; rollback tag `pre-promote-2026-09-07`).

📦 **The full evidence block is ARCHIVED** → `28-HANDOFF-ARCHIVE.md` (2026-09-07): the
before/after table labelled per drive, the mechanism, the class-fix argument, the additive
argument and the A/B. It is also in `07-CHANGELOG.md` 2026-09-06/07. Kept here, because these
are the only parts still LIVE:

**The result in one line:** `KI-47` battle-handler stops **3-6 → 0**, `SelectingTormentedMove`
**→ 0**, and ⭐⭐ **the bot BEATS SIDNEY** — `outcome=BattleOutcome.Won`. **§Ch24 FIGHT 1 IS WON.**

⚠⚠ **AND IT WON ON ITS LAST POKÉMON — FIVE OF SIX FAINTED.** At the win the party read `Sceptile 0/147, Zigzagoon 0/48, Swellow 0/139, Mightyena 0/144, Castform 0/103` with only **`Wailord L47 226/226`** standing, after **20 faint-chooser events**. ⇒ *"the bot beats Sidney"* is true and **materially weaker than it sounds**: it is a survival-by-one-mon win on the UNDER-PREPARED `post_league_shop` party that `KI-94` says invalidates §Ch24 measurements. A Tier 2 cold-start audit caught this stated without its survivor count. ‼ It also CONFIRMS the level story: at L47-53 fight 1 is barely survivable, which is exactly why the L60 grind was worth doing.

‼ **CITE THE LOG WITH THE FRAME.** The win is `f35237` in the HARNESS log (`ki93_fix5_drive.log`, relative frames) and `f4351983` in the DEBUG log (`Story-debug-20260906-235815.log`, absolute frames). A Tier 2 auditor grepped `f35237` in the debug log, found nothing, and reasonably suspected a fabricated citation. **A frame number without its log is not a citation.**

⚠ **AND THE "DOOR TO PHOEBE OPENS" CLAIM IS AN INFERENCE, NOT A WALK.** `PokemonLeague_EliteFour_SetAdvanceToNextRoomMetatiles` appears ONCE in the harness log's script list — the game queued the metatile change. **The bot never walked through**: the probe has no "advance to the next room" behaviour and parked in the defeat dialogue. Fights 2-5 remain UNDRIVEN.
Graded by `grade_ki93_drive.py` (C0-C3 PASS, exit 0); ordinary-case A/B byte-identical.

**The fix, in one line:** a dismiss gated on `get_text_printer(0).state == WaitForButton`
(never a frame count — a press during glyph printing is eaten as a speed-up), plus a refusal
memory keyed on `personality_value` that expires when a turn executes. **It is a CLASS fix:
61 battle strings end in `\p`.**

‼ **`KI-96` IS THE SAME CLASS, STILL OPEN** — the in-battle PARTY-MENU switch is another of
`KI-47`'s unbounded loops, and it now blocks the L60 party from reaching the League.

### ⛔⛔ 2026-09-06, SAME NIGHT — AN INDEPENDENT REVIEWER FOUND A REAL DEFECT IN THIS FIX. ✅ FIXED AND RE-DRIVEN CLEAN (see the grade below).

**The headline above ("driven clean") was too strong and is corrected here.** The livelock result
stands — `KI-47` battle-handler stops went 3-6 → **0** and the fight reaches a real outcome. But the
first version of the fix keyed `_ki93_refused_slots` by **`battler_index` alone**, so the memory
outlived the Pokémon that earned it. Proven in MY OWN drive log, which I had already read and passed
over:

```
f4348916  Swellow (battler 0) is Tormented; refused={0: {0,1,3}}
f4349501  Swellow FAINTS; the faint chooser sends in CASTFORM to battler 0
f4349924  [KI93-REPICK] battler=0 slot 0 was REFUSED -> 2      ⬅ NO preceding [KI93-WAIT]
f4351213  ...again — Castform forced into Sunny Day TWICE, having been refused NOTHING
f4373734  battle_text='NICK whited out!'
```
⇒ **Castform inherited Swellow's vetoes by slot number.** My own code comment claimed *"a stale entry
costs at most one turn of second-best move choice"*; measured, it cost two forced turns on a mon the
game never refused, in the battle that then whited out. ‼ **The `[KI93-REPICK]` with no preceding
`[KI93-WAIT]` is the tell** — an override with no refusal behind it — and it was sitting in the log I
declared clean.

**⭐⭐ IT IS A RULE THIS PROJECT HAD ALREADY WRITTEN DOWN.** `CLAUDE.md` SESSION DISCIPLINE #3:
*"Assert IDENTITY, never position or count. PIDs — never slot indices."* A battler index is a
POSITION; the thing that earns a refusal is a POKÉMON.

**⭐ AND A SECOND DEFECT THE REVIEW LED ME TO, WHICH IT DID NOT NAME:** Torment forbids the **LAST MOVE
USED** (`src/battle_util.c:999`), which changes every time a turn executes. So a refusal is true only
for the selection episode that produced it — keeping it after a turn runs is wrong **even for the same
Pokémon**, and would have leaked across battles.

**THE FIX — two guards:**
1. **IDENTITY** — `_ki93_owner[battler_index]` records the `personality_value` that owns the memory;
   `_ki93_check_owner()` drops it the moment a different PID occupies that slot, and is called before
   the memory is read AND before it is written. (`item_stealing.py:23` already keys on PID — house style.)
2. **LIFETIME** — an ordinary (non-refusal) battle script seen in the cancel branch means the turn
   executed, so every banked veto is dropped. Previously the only clearing rule lived in the
   parked-printer branch, which almost never coincides with an ordinary prompt.

**🔶 MIXED — TWO OF THESE ARE DONE AND TWO ARE GENUINELY OPEN. Each bullet carries its own marker,**
**because a heading is a claim about every bullet beneath it** (`CLAUDE.md` P2, the `KI-59` shape):
* ✅ **THE RE-DRIVE IS DONE AND IT PASSES ALL FOUR CONDITIONS** (`Story-debug-20260906-235815.log`,
  real exit 0 — read without a pipe):
  ```
  C0 CONTROL     PASS  [KI93-CTL] fired 32x
  C1 LIVELOCK    PASS  `KI-47 battle sub-handler` stops = 0      (was 3-6)
  C2 JUSTIFIED   PASS  0 REPICK(s) with no refusal behind them   ⬅ the blocker, now clean
  C3 ENGAGED     PASS  DISMISS=8 and REPICK=12 — both halves live
  ACCEPTANCE: PASS
  ```
  ⭐ **C2 is the one that matters**: every override now has a real refusal behind it, keyed on the
  Pokémon's `personality_value`, so a fainted mon's vetoes can no longer reach its replacement. ⭐ **C3
  is the one that could have been faked**: `DISMISS>0` with `REPICK==0` would mean the new LIFETIME
  guard had silently disabled the fix, and it does not.
* ⭐ **Acceptance is MECHANICAL, not a human re-reading a log** —
  `tools/story-dev/grade_ki93_drive.py <debug-log> <harness-log>` grades a drive by its SEQUENCE:
  ```
  C0 CONTROL    [KI93-CTL] fired, or nothing else in the log is evidence
  C1 LIVELOCK   `KI-47 battle sub-handler` stops == 0
  C2 JUSTIFIED  every [KI93-REPICK] preceded by a [KI93-WAIT]…ENDED / [KI93-DISMISS] since the last
                COMMIT  ⬅ the check that catches an override the game never asked for
  C3 ENGAGED    DISMISS>0 with REPICK==0 means the LIFETIME guard cleared the memory too eagerly
  ```
  ⛔ **FAULT-PROVEN IN THREE DIRECTIONS, re-derived 2026-09-07 after a Tier 1 reviewer could not
  reproduce an earlier claim:**
  ```
  Story-debug-20260906-234031.log  (defective fix, no `owner=`)  -> C2 INDETERMINATE, exit 1
  Story-debug-20260906-232310.log  (no refusal occurred at all)  -> C3 VACUOUS,       exit 1
  Story-debug-20260906-235815.log  (the final fix)               -> C0-C3 PASS,       exit 0
  ```
  ‼ **A superseded claim is retracted here rather than quietly edited:** this bullet used to say the
  grader returned *"C2 RED with 17 unjustified re-picks"* on `234031`. It no longer does — that log
  predates the `owner=` field, so the current grader correctly refuses to judge C2 on it and returns
  INDETERMINATE. The "17" described a version of the tool that does not ship. *(`08-MISTAKES.md`:
  retract measured numbers by deleting and pointing, never by rewording.)*
* ⛔ **STILL OPEN — Doubles are UNEXERCISED.** The `battler_index == 2 → right_battler` mapping is asserted, not
  proven; this project has a 3-for-3 record of index-space bugs in the sibling faint chooser.
* ⛔ **STILL OPEN — an ordinary parked `\p` prompt has never been observed** in a drive, so the claim that a B press
  is harmless there is reasoned, not measured.

**Status:** ✅ **PROMOTED 2026-09-07 with USER AUTHORISATION and VERIFIED BY DRIVING** (`--build custom`: `BattleOutcome.Won`, `KI-47` stops 0, `grade_ki93_drive.py` C0-C3 PASS; rollback tag `pre-promote-2026-09-07`). `custom-pokebot/` still hangs on Torment. **Promotion is the user's call.**
## `KI-96` — ⛔ THE IN-BATTLE PARTY-MENU SWITCH IS AN UNBOUNDED `while PARTY_MENU: press A`, AND IT WEDGES §Ch23'S CHAIN AT L60 (2026-09-07, MEASURED, A/B'd AS PRE-EXISTING, OPEN)

**⭐⭐ WHY IT MATTERS RIGHT NOW: LEVELLING ALONE DOES NOT UNBLOCK §Ch24.** The L60 party
(`post_grind_L60.ss1`) cannot complete §Ch23's chain — it wedges here long before the League door, so
the §Ch24 measurement this fixture was built for is BLOCKED on this, not on levels.

**⛔ CITATION DRIFT, CORRECTED 2026-09-07 — AND NO GATE COULD HAVE CAUGHT IT.** This entry cited
`battle_action_selection.py:590-592`. That was true when `KI-96` was filed; the `KI-93` fix and this
KI's own census then grew the file and moved the loop to **line 672** (verified in BOTH forks). An
adversarial recon agent caught it, not `audit_doc_citations.py` — because that gate resolves
`symbol` + `file.py:LINE` PAIRS, and a **bare line number has no symbol to resolve against**.
⭐ **RULE: cite the SYMBOL.** The `TurnAction.RotateLead` arm is stable across edits; line 590 was not.

**THE CODE** — `modules/`battle_action_selection.py`'s `TurnAction.RotateLead` arm (line 672 as of 2026-09-07 — ⛔ cite the SYMBOL, not the line: this citation already drifted once from 590)`, the `TurnAction.RotateLead` arm:
```python
yield from scroll_to_party_menu_index(in_battle_index)
while get_game_state() == GameState.PARTY_MENU:
    context.emulator.press_button("A")
    yield
```
No bound, no escape, no check that the switch was ACCEPTED. If the game refuses the chosen mon it
returns to the party menu, the state stays `PARTY_MENU`, and this presses A for ever.

**MEASURED** — `--driver ch23chapter` from `post_grind_L60.ss1`:
```
f26951 *** BotModeError -> Manual: KI-47: battle sub-handler 'handle_battle_action_selection' ran
       3001 frames with no battle progress (frozen at ('BattleScript_DoTurnDmgEnd',
       'HandleTurnActionSelectionState', ...))
f28153 !!! NO-PROGRESS x1200  state=PARTY_MENU  bt='What will DIVER do?'
       tasks=['Task_ReturnToChooseMonAfterText', 'Task_PrintAndWaitForText']
       scripts=['EventScript_DoTrainerBattle']
f46953 HANG CONFIRMED (20000 frames no progress)
```
`Task_ReturnToChooseMonAfterText` is the game saying *"I printed a message and put you BACK in the
party menu"* — i.e. **the switch was REJECTED**, and we answered by pressing A again.

**✅ A/B — IT IS PRE-EXISTING, NOT A `KI-93` REGRESSION.** Same fixture, same driver, with the entire
`KI-93` change reverted to `a662f51a~1` (546 lines vs 848): the hang **reproduces identically** — one
`KI-47` battle sub-handler stop, same `state=PARTY_MENU` wedge. ⇒ *the arm with the change removed
still shows the bug*, which is the only currency this project accepts for "not mine".

**⛔ NOT AN EDGE-TRIGGER PROBLEM — CHECKED, SO NOBODY RE-DERIVES IT.** `press_button` auto-releases
(`libmgba.py:471`: *"if pressed on previous frame it will be released"*), so mashing A yields an edge
every other frame. The presses ARE landing; **the game is refusing the switch and we keep re-asking.**

**⇒ THIS IS ONE OF `KI-47`'s NAMED UNBOUNDED LOOPS, AND `KI-93` WAS ANOTHER — COPY ITS FIX,
WHICH IS DIRECTLY ABOVE IN THIS FILE.** In four words: *bound it, gate on the game's own state
(never a frame count), back out with **B** not A, and key any memory on `personality_value`
rather than a slot.* ‼ `KI-93` took four implement-drive-revert cycles, three of whose verdicts
were VOID, before one control-lined census named the site — which is why the census came first
here too, and answered it in ONE drive.

**📦 THE THREE-DRIVE INVESTIGATION AND ITS TWO REFUTED HYPOTHESES ARE ARCHIVED** →
`28-HANDOFF-ARCHIVE.md` (2026-09-07). What they established, and it still stands: the target is
HEALTHY (not fainted, not the active), the party menu genuinely OPENS, every stage before the
loop is correct, and `bt='What will X do?'` is a stale leftover string, not proof of the screen.
⛔ Two published root causes were measured FALSE there within an hour each — read the archive
before proposing a third.

**⛔⛔ RETRACTED WITHIN THE HOUR — "PERMUTED ⇒ WEDGE" IS FALSE.** The batch produced a PERMUTED-order
rotation that **succeeded**:
```
[KI96-ORDER] decoded_battleorder=[3, 1, 2, 0, 4, 5]  active_battler_party_index=3  => menu slot 2 holds party 2
[KI96-DONE]  the party menu closed after 27 press(es) — the switch was ACCEPTED
```
⇒ a permuted order is NOT sufficient for the wedge. That is the SECOND hypothesis on this KI to be
measured false, both within an hour of being written. ‼ Both were caught because the census keeps
producing comparable samples — **the habit of re-checking a fresh claim against new data is doing more
work here than any single insight.**

**✅✅ THE INVARIANT THAT ACTUALLY SEPARATES THEM — MEASURED, 262 SAMPLES, PERFECT SEPARATION:**
```
            decoded_battleorder[0] == active_battler_party_index
  HOLDS    : 261 / 261  -> ALL 261 ACCEPTED, and NONE aimed at menu slot 0
  VIOLATED :   1        -> the wedge: decoded[0]=2 while active=0, aimed at menu slot 0, hung
```
⭐ **THE ARRAY WAS STALE.** Gen 3's `UpdatePartyToBattleOrder` places the ACTIVE battler at battle
position 0, so `decoded[0]` must equal the active's party index — an invariant that held in every one
of 261 healthy rotations. In the wedge the array claimed position 0 held party **2** while the active
was party **0**, so `map_battle_party_index(2)` returned **0**, `scroll_to_party_menu_index(0)` parked
the cursor on the slot the ACTIVE really occupies, and the game refused — *you cannot switch in the
Pokémon that is already out.*

⭐ **THIS VINDICATES THE ORIGINAL ROOT CAUSE, FOR A DIFFERENT REASON.** The first published diagnosis
said "the mapping aims at the Pokémon already fighting". It was retracted because the array appeared to
say menu slot 0 held party 2. **The array was lying.** ⇒ the aim WAS at the active; the mechanism is a
STALE READ, not a wrong formula. `map_battle_party_index`'s arithmetic is correct — its INPUT is not.

‼ **HONEST WEIGHTS, UNCHANGED:** the healthy side is n=261 across 8 independent lanes; the violation
side is still **n=1**. What the 261 buy is not a rate but a RULE: the wedge is no longer "one odd case",
it is *the only case that broke an invariant confirmed 261 times*. A second violation should still be
captured before the fix is called proven.

**⇒ THE FIX THIS IMPLIES — TWO HALVES, AND THE SECOND IS REQUIRED REGARDLESS:**
1. ⭐ **ASSERT THE INVARIANT BEFORE TRUSTING THE MAPPING.** If `decoded[0] != active_battler_party_index`
   the order array is STALE: do not scroll to an index derived from it. Re-read it, or refuse the
   rotation this turn. ⛔ **Do NOT "fix" `map_battle_party_index`'s arithmetic — it is correct.** The
   defect is that a stale input is used without a validity check, which is why every attempt to correct
   the formula would have made things worse.
2. **BOUND THE LOOP ANYWAY.** A correct aim can still be refused (a mon that fainted between the
   decision and the menu). `:672` must stop pressing, back out with **B**, and raise a NAMED error into
   `KI-47`'s channel rather than spinning 3001 frames. **A correct aim is not a bound.**

**⛔ WHAT IS GENUINELY UNKNOWN NOW — DO NOT GUESS; THE LAST GUESS WAS WRONG:**
* Does `scroll_to_party_menu_index(0)` actually leave the cursor on entry 0? Unverified.
* Is the A press being consumed by something else on that frame? Unverified.
* ⭐⭐ **THE MOST INTERESTING THREAD, AND IT IS UNEXPLAINED:** `bt='What will DIVER do?'` is the
  **ACTION-SELECT** prompt (FIGHT / BAG / POKéMON / RUN), not a party-menu prompt — yet
  `get_game_state()` reports `PARTY_MENU`. **The state and the screen disagree.** If the game is really
  sitting on the action menu, then the party menu never opened, `scroll_to_party_menu_index` scrolled
  nothing, and every A press is landing on the action menu — which would explain the refusal completely
  and has nothing to do with indices.
⇒ *(SUPERSEDED — that telemetry SHIPPED on 2026-09-07; see the round 1-3 record immediately below.)*

**⭐ ROUNDS 1-3, 2026-09-07 — READ THIS BEFORE TOUCHING `KI-96`.**
* **Round 1** added (a) a refusal when `decoded_battleorder[0] != active_battler_party_index`, on the
  theory that the array was STALE, and (b) a 240-press bound on the menu loop. 262 samples separated
  perfectly (261 healthy hold it; the 1 wedge violates it).
* **Round 2 — an adversarial reviewer kicked it back, correctly.** Both new exits did a raw
  `raise BotModeError`, which crosses the mode/battle **sibling** boundary (`battle_fault.py:5-11`;
  `battle_handler.py:857` *"‼ NEVER `raise` here"*) and parks the run in **Manual**. Today's hang is
  caught by KI-47's watchdog, which DOES route through `request_mode_recovery` — so the "fix" would
  have traded a recoverable 3,001-frame stall for an unrecoverable lane death. Both exits now call
  `request_mode_recovery` first, keeping the raw raise as the documented fallback.
* **⛔⛔ Round 3 — THE REFUSAL WAS WITHDRAWN. DO NOT RE-ADD IT.** A decomp check
  (pret/pokeemerald @ `5eff7864`) showed `switchhandleorder` rewrites the order BEFORE
  `getswitchedmondata` advances `gBattlerPartyIndexes` (`data/battle_scripts_1.s:3110-3112`), so on a
  **healthy** switch the array is briefly *ahead*, not stale ⇒ the guard would refuse legitimate
  rotations. **A guard with false positives is worse than no guard.**
* **⭐ THE STRONGER ROOT CAUSE, NOT YET PROVEN:** `gBattlePartyCurrentOrder` is a 3-byte SCRATCH
  buffer that `PlayerHandleChoosePokemon` REFILLS at the instant the party menu is requested — and we
  compute the cursor slot at `:584` while the menu only opens at `:699`. ⇒ **we aim from a leftover.**
  It also explains 261-vs-1: the leftover is usually still correct, diverging only after a prior
  switch rewrote it.
* **WHAT SHIPPED:** observe-only **`[KI96-REREAD]`** telemetry (array + aimed slot, before AND after
  the menu opens, with an AGREE/DIFFER verdict) plus the bound. ⛔ The fix itself is NOT applied:
  rule 10 requires the measurement first, because `handle_fainted_pokemon` has had three index-space
  bugs. ⇒ **NEXT: run the drive with `POKEBOT_KI96_CENSUS=1` and read `[KI96-REREAD]`.**

**✅ WHAT WAS NOT MEASURED IS NOW PARTLY MEASURED** — *why* the switch is refused. Candidates: the
target is fainted, is already out, or is the mon the game just asked about. **Instrument it first** —
log the requested `index`, the mon's PID/HP at that moment, and the on-screen message — exactly the
census that made `KI-93` solvable after four blind attempts. ‼ `KI-93`'s history is the warning: four
implement-drive-revert cycles, three of them VOID, before one control-lined census named the site.

**Repro:** `PYTHONUTF8=1 py -3.12 story_harness.py post_grind_L60.ss1 --driver ch23chapter --frames 400000`
(wedges by ~f27k, ~6 min). Stall states are saved under `stalls/`.

## `KI-94` — ⛔⛔ THE §Ch24 PREP HAS NO COMBINED END-STATE, SO EVERY §Ch24 MEASUREMENT SO FAR USED AN UNDER-PREPARED PARTY (2026-09-06, MEASURED, OPEN — §Ch24 BLOCKER, BIGGER THAN `KI-93`)

**Symptom.** Every §Ch24 probe and all four `KI-93` fix attempts were driven from
`post_league_shop.ss1` — whose OWN fixture note opens with
**"⛔ THE BOT IS *NOT* READY TO ATTEMPT §Ch24 — SEE `#24-e4healing`."** I read past that line for a
whole session.

**MEASURED.** Wailord's moveset in every drive today:
```
[moveset] Wailord L47: Dive, Surf, Water Spout, Waterfall      ⇐ NO ICE BEAM
```
…while `#24-icebeamteach` is marked **CLOSED: "WAILORD KNOWS ICE BEAM" ⛔ DO NOT REOPEN**.

**⇒ THE CLOSED ITEM IS NOT WRONG — THE FIXTURE LINEAGE IS.** The §Ch24 prep runs
`post_league_shop → post_moveset → post_fly → post_slateport → post_icebeam`, and:
* each step was driven and PASSED in isolation;
* `post_icebeam.ss1` ends at **ROUTE108**, not the League;
* **`ch24teachice` captures NO fixture** — there is no `post_teachice.ss1` in `FIXTURES.md5`.
⇒ ⭐⭐ **THE PREP IS A CHAIN OF PROVEN STEPS WITH NO COMBINED END STATE.** Nothing carries the four
move changes, Fly, TM13 and the taught Ice Beam forward to the League door, and no save holds them
together.

**⛔ WHAT THIS INVALIDATES.**
* The winnability analysis must NOT be run against `post_league_shop.ss1` — it is the wrong party.
  Ice Beam was called *"the single change that turns Drake from a loss into a win"*, and the party we
  measured does not have it.
* `probe_ch24_readiness.py`'s stat dump is correct FOR THAT SAVE, but that save is pre-prep.
* ‼ `KI-93` is **NOT** invalidated: Torment blindness is structural (the chooser cannot see
  `gLastMoves`/`STATUS2_TORMENT` whatever the moveset), and the freeze would recur on any party.

**⇒ ⛔ SUPERSEDED 2026-09-07 — `KI-93` SHIPPED FIRST AND THE REORDER THIS DEMANDS IS CANCELLED (`04-HANDOFF.md`). Kept for its reasoning only. Its original text:** THE REAL NEXT STEP FOR §Ch24: chain the prep and **capture a
combined fixture** — the fully-prepared party standing at the League door — then re-measure
readiness and winnability against THAT. Until it exists, every §Ch24 number is about a party the
bot will never actually field.

**⭐⭐⭐ ROOT CAUSE FOUND 2026-09-06, AND IT IS AN ORDERING CONSTRAINT, NOT A MISSING CAPTURE.**
I built the combined fixture with existing tools and it FAILED at the last step — which is the useful
result. What was verified along the way:
* ✅ **The teach WORKS.** `--driver ch24teachice post_icebeam.ss1` → `ACCEPTANCE: PASS`,
  `Wailord L47: Dive, Surf, **Ice Beam**, Waterfall`. Captured as **`post_teachice.ss1`**
  (md5 `d1eb8736270b7486e464f23501432194`) and re-verified BY RELOADING the file.
  ⇒ `#24-icebeamteach` is correctly closed; only the fixture was missing.
* ✅ **Flying back works.** `CH24_FLY_DEST=EverGrandeCity --driver ch24flyto` → `ACCEPTANCE: PASS`,
  `moved=True`, `pids_stable=True`, `whiteouts=0`, Ice Beam intact. Captured as
  **`post_ch24ready.ss1`** (md5 `cf383b5b2567be00d7b3ba8fb3de26ac`).
* ⛔⛔ **BUT IT LANDS ON THE WRONG SIDE OF THE PLATEAU.** MEASURED:
```
PathFindingError: Could not find a path from (27/49 @ EVER_GRANDE_CITY) to (18/5 @ EVER_GRANDE_CITY)
```
Fly deposits the party at the **Poké Center (27,49)**; the **League door is (18,5)** and there is **no
walking route between them**. This is the same plateau split `post_vr_exit.ss1` already records from
the other direction (*"Ever Grande Poké Center → UNREACHABLE, League door → REACHABLE in 37 wp"*).

**⇒ ⭐⭐ THE CONSTRAINT: THE POKÉMON LEAGUE IS REACHABLE ONLY THROUGH VICTORY ROAD.** So the §Ch24 prep
— which REQUIRES flying away to Slateport for TM13 — **cannot be done after Victory Road and flown
back.** Either:
  (a) **do the prep BEFORE §Ch23's Victory Road traverse**, so the bot arrives already prepared — this
      is the cheap option and only reorders existing, individually-proven steps; or
  (b) re-traverse Victory Road after the prep — expensive, and it re-runs the trainer gauntlet.
⇒ **(a) is almost certainly right**, and it explains the fixture layout: the prep chain was built
FROM `post_league_shop.ss1` (already at the League), flew away, and never had a way back.

⚠ **PRECISION — DO NOT OVER-CLAIM THIS.** `calculate_path` "is not able to use warps or fly"
(`modules/map_path.py` docstring), so what is measured is **no WALKING path**. A warp route has NOT
been ruled out by measurement; the claim rests on that plus Emerald's design (the League sits beyond
Victory Road). ⇒ **if someone wants to keep option (b) alive, the thing to check is a warp route, and
it must be checked, not assumed.**

**✅ TWO FIXTURES BANKED REGARDLESS**, both verified by reloading: `post_teachice.ss1` (the taught
party) and `post_ch24ready.ss1` (prepared party, at Ever Grande PC). Neither is at the League, so
neither is the §Ch24 start — but they make the prep re-runnable without repeating the ~700k-frame ship
trip.

**⭐ THE LESSON — AND IT IS A CHEAP ONE TO REUSE:** a fixture's own note is a precondition, not
decoration. `post_league_shop.ss1` said "NOT READY" in its first sentence and I drove §Ch24 from it
anyway, repeatedly. **Read the fixture note before the drive, not after the anomaly.**


## `KI-95` — the faint chooser ranked replacements on a PURE TYPE MULTIPLIER, so a L19 mule outranked a healthy L48 (2026-09-06, ✅ FIXED IN THE SANDBOX + GATED as #39 — ✅ **PROMOTED 2026-09-07 with USER AUTHORISATION and VERIFIED BY DRIVING** (`--build custom`: `BattleOutcome.Won`, `KI-47` stops 0, `grade_ki93_drive.py` C0-C3 PASS; rollback tag `pre-promote-2026-09-07`))

📦 **The defect description, the code excerpt, the Glacia consequence and the retracted acceptance-bar
note are ARCHIVED VERBATIM** in `28-HANDOFF-ARCHIVE.md` → "KI-95 — the original defect". Nothing is
deleted; this file's own preamble says it holds OPEN problems, and the only parts of `KI-95` still open
are the two below: it is **NOT PROMOTED**, and it rests on a **deprecated CPython behaviour**.

**One-line restatement:** the offensive term in `choose_new_lead_after_faint` was a bare type
multiplier — `base_power` was used only to test `== 0` — so a L19 Zigzagoon's 20 BP Rock Smash (2× vs
Ice) scored `2.0` and outranked a full-HP L48 Mightyena scoring `1.0`. The mule was sent in to die.

### ✅ 2026-09-06 — FIXED IN THE SANDBOX, GATED AS #39, FAULT-TESTED. ✅ **PROMOTED 2026-09-07 with USER AUTHORISATION and VERIFIED BY DRIVING** (`--build custom`: `BattleOutcome.Won`, `KI-47` stops 0, `grade_ki93_drive.py` C0-C3 PASS; rollback tag `pre-promote-2026-09-07`).

📦 **The full resolution is ARCHIVED** → `28-HANDOFF-ARCHIVE.md` (2026-09-07), and it is also
in `07-CHANGELOG.md` 2026-09-06. **In one line:** the offensive term now scores EXPECTED DAMAGE
via the shipped `calculate_move_damage_range` instead of a bare type multiplier; the ranking is
the pure `rank_replacement`, gated offline by `probe_faint_chooser_rank.py` (**gate #39**, 7
cases, fault-tested — `POKEBOT_KI95_PROBE_FAULT=legacy` turns exactly C1 red). It also fixed two
things the report never named: a Ground move vs a **Levitate** foe scored 1.0 and now scores 0,
and the chooser no longer ranks mons on `banned_moves` that `decide_turn` would refuse to use.

**Still live below:** the fix rests on a DEPRECATED CPython behaviour, and it is unpromoted.

### ⚠ A LATENT FRAGILITY THIS FIX NOW DEPENDS ON — measured 2026-09-06, not reasoned about

An adversarial reviewer asked the right question: *does `calculate_move_damage_range` even work for a
**bench** `Pokemon`, or does it throw — leaving `estimates_ok=0` and the fix silently inert?* Chased to
the bottom rather than assumed:

* `_util.py:_calculate_base_move_damage` opens with `if attacker in self._battle_state.own_side:`.
* `BattleSide.__contains__` (`modules/battle_state.py:370`) returns **`NotImplemented`** for anything
  that is not a `BattlePokemon` — and a party `Pokemon` is a separate class (`pokemon.py:907` vs
  `battle_state.py:472`), not a subclass.
* Python's `in` coerces that with `bool()`. **MEASURED on this interpreter (3.12.4):
  `bool(NotImplemented)` is `True`, with a `DeprecationWarning` — it does NOT raise.**

⇒ **The fix works, and by luck lands on the RIGHT branch:** `attacker_is_player = True` is correct for
our own party mon, so the badge boosts apply and `partner_for` returns a live battler or `None`. Party
`Pokemon` also really does expose `.stats`, `.ability` and `.held_item` (`pokemon.py:1240/1158/1080`).

⛔ **BUT IT RESTS ON DEPRECATED BEHAVIOUR.** CPython has warned since 3.9 that `NotImplemented` in a
boolean context will become a **`TypeError`**. On the day that lands, `calculate_move_damage_range`
will raise for every bench mon, `estimates_ok` will be 0, and the ranker will silently fall back to the
legacy multiplier — i.e. **`KI-95` would quietly return without a single test going red**, because the
gate injects its own damage function and never touches this path.
⭐ **THAT IS EXACTLY WHAT THE `metric=` TELEMETRY IS FOR.** A live `[FAINT-CHOOSER]` line reading
`metric=legacy` means this has happened. It is the one signal that distinguishes "fixed" from "fixed on
paper", and it is why the field was added rather than leaving a reader to infer it from `estimates_ok`.

**Status:** ✅ **PROMOTED 2026-09-07 with USER AUTHORISATION and VERIFIED BY DRIVING** (`--build custom`: `BattleOutcome.Won`, `KI-47` stops 0, `grade_ki93_drive.py` C0-C3 PASS; rollback tag `pre-promote-2026-09-07`). `custom-pokebot/` still has the defect; drift is 4 (`KI-96` telemetry, the `KI-97` gate, `#24-mossdeepstrand` and `#24-countermsg`, all sandbox-only while the batch runs). **Promotion is the user's
call and has not been given.**

## `KI-97` — a `_play()` re-entry from a POST-Fortree position marched to MAUVILLE and fail-fast derailed (2026-09-07, MEASURED on the live batch, ✅ FIXED IN THE SANDBOX — ⚠ NOT DRIVEN, NOT PROMOTED)

**Symptom (4 of 9 ended runs — a running figure on a partial batch, not a rate):**
`Could not reach (19, 6) on MapRSE.MAUVILLE_CITY … Source (43/32 @ SOOTOPOLIS_CITY) … not on
connected maps`. Sootopolis has **no land route out** (Dive/Fly only).

**Root cause (✅ re-verified in-tree, not taken on report).** `_play()` re-enters from the TOP on
every whiteout and every derail. Segment 13a's `else` branch called `travel_to_fortree()` with no
completion gate; its `_rank()` (`early_game.py:6325-6326`) returns **-1** for maps absent from
`order` (`:6306-6313`) — Sootopolis and Mossdeep-gym both are — and `-1 > tgt` / `-1 == tgt` are both
False, so every leg runs from `LEGS[0] = MAUVILLE_CITY (19,6)` (`:6314`).

**⭐ THE CLASS, NOT THE INSTANCE:** the same function already carries a note (`:6303-6305`) recording
this exact failure for ROUTE120, fixed then by extending `order`. **An enumeration-based guard rots
whenever the story grows past it** — §Ch21-23 made these maps reachable long after that fix.
⇒ gate on the segment's own COMPLETION FLAG (`BADGE06_GET`), which cannot rot.

**Fix (sandbox only):** Segment 13a — imports, body and its trailing `_guard` — wrapped in
`if not _done("BADGE06_GET")`, with an `else` that prints a positive control.

**Acceptance, gradeable from any lane log:** `Story: Route 119 already cleared — heading to Fortree.`
and `Could not reach (19, 6) on MapRSE.MAUVILLE_CITY` → **zero** occurrences;
`Story: Fortree arc already complete (BADGE06) — Ch13a skipped.` → at least one; a pre-BADGE06 lane
must still print `Story: to Fortree — Mauville City...`.

**Status:** ✅ FIXED IN THE SANDBOX 2026-09-07. ⚠ **NOT DRIVEN** (the acceptance drive waits for the
batch to end — a drive now would contend with 8 live lanes) and ⛔ **NOT PROMOTED** (`custom-pokebot`
is frozen for the batch's duration). ⚠ It does **not** rescue the MOSSDEEP_CITY_GYM (23,8) variant —
see `#24-mossdeepstrand`. Detail: `ai-research-notes/2026-09-07-batch-blockers-RECON.md`.
