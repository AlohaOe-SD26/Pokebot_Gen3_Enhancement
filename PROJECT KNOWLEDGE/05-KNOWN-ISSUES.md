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

## KI-6 — Tab bar overcrowds with 6 tabs — RESOLVED 2026-07-19 (sandbox)
- **Symptom:** Adding the Hunt tab (#9) made 6 tabs overflow the ~360px
  tool-column width — labels overlapped/truncated.
- **Fix (done):** tab bar wraps to two balanced rows when there are >4 tabs
  (3+3 for six), legible in both desktop and the handheld drawer
  (screenshots ki6_1/ki6_2). Gamepad focus-nav + tab persist unaffected.

## KI-7 — fly_to() checks the wrong badge for Emerald — ✅ FIXED 2026-07-24 (sandbox)
- **Fix:** RSE branch now gates on BADGE06_GET (Feather Badge) — the stock BADGE03 check
  was FR/LG's. Fixed ahead of Ch14's first Fly usage; DIVERGENCE-LOG entry due at
  promotion (upstream-file edit).

## (old text) KI-7 — fly_to() checks the wrong badge for Emerald (opened 2026-07-19, severity: low)
- **Symptom:** `modules/modes/util/higher_level_actions.py` fly_to() gates on
  BADGE03_GET (Dynamo) — correct for FR/LG but WRONG for Emerald, where Fly
  needs the Feather Badge (BADGE06). Inherited from upstream. Story-mode #24
  must not rely on fly_to as-is; fix when wiring Fly into story navigation.

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

## KI-9 — Training spin could silently stall (no encounters) — MITIGATED 2026-07-21
- **Symptom:** during pre-gym / pre-rival training, the grind `spin()` could end up where it
  can't trigger wild encounters (walked out of grass, trainer line-of-sight, bad respawn spot)
  and walk in place FOREVER — the level never reaches target, the stop-condition never fires, no
  whiteout, no derail → hard stall (harness-repro'd from `route116team.ss1`: stuck at Marshtomp
  L16 with no EXP for 20k+ frames). Position/RNG-dependent (a clean fresh run trains fine).
- **Mitigation (done):** `_story_spin` now has a **no-progress watchdog** — if the party gains
  no EXP for `_STORY_SPIN_NO_PROGRESS_FRAMES` (2400) consecutive OVERWORLD frames, it bails so
  the caller (`train_team`'s loop) **re-navigates to the grass and retries**, which un-sticks it.
  Overworld-only counting means a long single battle can't false-trigger it. VALIDATED: the same
  `route116team` run that hung before now trains past L16, beats Roxanne, and reaches the rival
  prep with all fixes. Bounded by `train_team`'s outer guard (500) → derail recovery if truly stuck.

## KI-10 — Post-sail whiteout can respawn the run on the MAINLAND (Dewford arc) — MITIGATED 2026-07-22
- **Scenario:** the Emerald whiteout respawn point is the last Poké Center USED. After the first
  Briney sail (Ch6), Mr. Briney leaves his cottage (FLAG_HIDE_BRINEYS_HOUSE_MR_BRINEY) and waits
  at his BOAT: vanilla re-sails happen by talking to him on the Route 104 beach (his Route104
  object is un-hidden by the sail script) or at the Dewford dock (12,9). If the bot whites out on
  the Dewford side BEFORE ever healing at the Dewford PC, it respawns at Rustboro's PC — and
  `sail_to_dewford`'s cottage leg (Leg 3-4) would knock on an EMPTY house.
- **Mitigation (done):** `deliver_stevens_letter` heals at the Dewford PC FIRST when starting
  from town, so from the moment the Dewford arc begins, whiteouts respawn IN Dewford (the
  Segment-6 whitelist also stops any Dewford-side resume from re-running the sail). Remaining
  edge: a whiteout in the sail leg itself (route trainers) before the first Dewford heal — rare
  (the leg heals before the rival and fights little), but if hit, the run derails to Manual at
  the cottage instead of re-sailing.
- **Proper fix (when Ch8 needs re-sailing anyway):** teach the sail leg to talk to BOAT-Briney —
  if `HIDE_BRINEYS_HOUSE_MR_BRINEY` is set, engage his Route 104 beach object (live local_id via
  `_talk_to_wandering_npc`-style lookup) instead of entering the house.

## KI-11 — Oceanic Museum entrance grunt-sealed at Devon-goods time — ✅ RESOLVED 2026-07-22
**RESOLUTION:** NOT a state bug — a missing STORY STEP. The museum grunts clear when you talk
to **Dock at Stern's Shipyard** (`SlateportCity_SternsShipyard_1F_EventScript_Dock` runs
`setflag FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA`). User-supplied + decomp-confirmed; built into
`deliver_devon_goods_to_stern` (Shipyard→Dock→museum). The doc was wrong (had the museum
freely enterable) — corrected in §Ch8b. This is the motivating case for the /validate-docs
process. Original write-up kept below for reference.

- **Symptom:** `deliver_devon_goods_to_stern` cannot reach the museum. The doors are city
  warps (30,26)/(31,26); the ONLY tiles below them, (30,27)/(31,27), are occupied by two
  Team Aqua grunts (obj id 18/5, `SlateportCity_EventScript_AquaGrunt2/1`). The whole
  y=27 row from x=22-31 is a grunt wall (gap at x=27, but (27,26) above it is collision).
  So the museum is physically SEALED — navigate_to (interior or door tile) plan-fails, and
  a walk-into-door bumps the grunt forever.
- **What's verified (probes 2026-07-22):** all 11 outside grunts share hide-flag
  `FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA` (882). It is UNSET by default (confirmed on an
  INDEPENDENT fresh game at Rustboro AND on slateport.ss1), `VAR_SLATEPORT_CITY_STATE=0`,
  and the SlateportCity map.json has NO coord-trigger near the museum to reposition them
  (its only coord_event is the Battle Tent Scott scene at (10,13)). The 2F Stern-fight
  grunts are SEPARATE 2F objects (id 2-4 spawned at the stairs), not this outside crowd.
- **The contradiction:** vanilla canon = the museum IS enterable on the first (Devon-goods)
  visit, yet structurally it's sealed with flag 882 unset. Something clears/repositions the
  crowd that our static read isn't capturing (a map ON_TRANSITION/ON_FRAME script setting a
  var, an event on the Slateport dock arrival, or the flag being set earlier than found).
- **DO NOT guess a state-write** (setting flag 882 hides the crowd, but proving that matches
  vanilla's exact state at this point needs the mechanism first — house rule).
- **Fastest ground truth = the USER:** on a real first Slateport visit, are Aqua grunts
  blocking the Oceanic Museum doors, or is the entrance clear? Then either build the faithful
  trigger or document the state-write. `deliver_devon_goods_to_stern` (interior logic sound)
  stays defined but UNWIRED; frontier honestly = Slateport arrival.

> 📦 **KI-14, KI-15 and KI-16 moved to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-13** — all three
> were ✅ FIXED same-day in July 2026. Moved verbatim, nothing deleted, because this file crossed
> its 3,000-line budget (lint rule R3) when KI-70/KI-71 were filed.

## KI-19 — Route 111 training band was paired with a heal 2.2× farther than necessary (2026-07-24) — FIXED-PENDING-WIRING

`ROUTE111_OLD_LADYS_REST_STOP` (map `(18,1)`, door at ROUTE111 `(26,18)`) contains ONE NPC —
`Route111_OldLadysRestStop_EventScript_OldLady`, `flag_id=0` so always present and ungated — that
gives a **full HP + status + PP heal, repeatable**. PROVEN live: all four party members damaged to
1 HP with four different status conditions and spent PP, verified in memory, then fully restored;
repeated a second time with no change in behaviour. Static dump confirms **zero `bg_events`** — no
bed exists in that building.

**Distances from the Route 111 training tile (25,55):** rest stop **96 steps**, Fallarbor Poké
Center **213 steps**.

`training_areas.py` / `_training_area_heal_map()` currently pairs ROUTE111 with
`PokemonCenter.FallarborTown` because that was the only heal verifiable at the time. Re-pairing
needs a heal-at-NPC helper (the existing path is `heal_in_pokemon_center(PokemonCenter.X)`, which
assumes a Poké Center layout) — punch-list `#24-npcheal`.

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
   one. Against Winona: any Electric (Route 110 Voltorb/Magnemite, Mauville area) or an Ice move.
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
   ‼ The note above says "any Electric (Route 110 Voltorb/Magnemite, Mauville area)". The
   planner's own answer from the real Winona-era save is **Electrike @ ROUTE118 (29,15),
   L24-26, 30%** — a verified spin tile. Trust the planner's measured output over this
   prose; it reads the ROM's encounter tables and prices the grind.
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

## KI-32 — the stall detector was STRUCTURALLY BLIND to any in-battle wedge — ✅ FIXED 2026-07-29
- **Symptom:** user log `20260729-122709`. A mid-battle rotation wedged the PARTY MENU in
  Fortree Gym; the run then held `state=3 controllable=False` at one fixed position for
  **~280,000 frames** and emitted **ZERO stuck dumps** — no generator call stack, the single
  most useful artefact the logger produces.
- **Cause:** `modules/debug_logger.py` stall detection did
  `if st.get("battle_active"): _stall_frames = 0` on EVERY in-battle frame. The intent was
  sound (a battle legitimately holds still mid-turn and during the EXP fill, so the 300-frame
  overworld threshold would false-trigger every turn) but the implementation meant **no
  in-battle wedge could ever be reported, however long it lasted.**
- **Same shape as KI-27** (Weather Institute): the guard could not fire on the thing it was
  guarding. A guard must not share its subject's failure mode.
- **Fix:** a battle now gets a much LARGER threshold, not an exemption —
  `_BATTLE_STALL_DUMP_AFTER = 18_000` (5 min at 60fps, ~60× the overworld threshold and
  ~2 orders of magnitude above the longest legitimate quiet stretch). Overworld sensitivity
  unchanged at 300.
- **Repro:** `tools/story-dev/repro_battle_stall_blindspot.py` — proves a frozen battle now
  dumps, a healthy/changing battle never does, 300/3,000/10,000-frame in-battle quiet is not
  disturbed, the overworld path is unchanged, and a long wedge re-dumps periodically.

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

## KI-38 — 3 residual after-faint give-ups remain; the text fallback has now EARNED its place (opened 2026-07-30, severity: MED)
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

## KI-39 — The bot has NO cross-map overworld route planning; long journeys are hand-coded (2026-07-30)

**This is the root cause behind every "unreachable counter destination", and it is much
bigger than `#24-counters`.** It is also the direct answer to the user's question *"is there
a way to get the bot to map to already traveled locations?"* — today, no.

### Measured, from `rocksmash_taught.ss1` (standing in MAUVILLE_CITY (32,15))
| destination | `calculate_path` |
|---|---|
| ROUTE117 (31,16) — directly connected | **OK, 72 waypoints** |
| ROUTE110 (12,60) — joined through a gate BUILDING (a warp) | FAIL |
| ROUTE116 (11,7) — several maps west | FAIL |
| ROUTE111 (25,55) — same map, other side of the Go-Goggles desert | FAIL |

### Why `navigate_to_anywhere` does not rescue it
It branches on REGION, and a region is the connected component over direct N/S/E/W map
connections. Measured: `region_of(MAUVILLE_CITY) == region_of(ROUTE111) ==
region_of(ROUTE116) == region_of(LAVARIDGE_TOWN) == region_of(FALLARBOR_TOWN) == **0**`.
**The whole Hoenn overworld is ONE region.** So for any overworld→overworld trip the
same-region branch is taken, the warp planner is never consulted, and the entire journey is
handed to `calculate_path` — which only spans directly-connected maps. The warp route often
EXISTS and is simply never asked for: `graph.plan(MAUVILLE → FIERY_PATH)` returns a valid
one-warp edge (ROUTE112 (11,36) → FIERY_PATH), yet the navigation fails at 255 frames because
leg 1 — *walk to that warp tile* — is itself a multi-map journey `calculate_path` cannot plan.

### Why nobody noticed
The story chapters hand-code their long journeys leg by leg (`_hold_walk_route` exists
precisely to "bridge the planner can't cross"). Every long trip the bot makes today was
written out by hand, so the generic capability was never exercised — and its absence looks
exactly like "that destination is unreachable".

### Consequences to hold in mind
* A counter hunt only reaches destinations a leg or two away. FIERY_PATH (18,19) arrives in
  2,922 frames from **Lavaridge**, but Norman is fought at **Petalburg** — so even the one
  rung measured "live" is probably inert at the moment it actually fires. Expect the counter
  chain to stop honestly far more often than it hunts.
* `#24-dexhunt`, `#24-pc` (box trips), `#24-catchcap` and the whole team/PC-reserve plan all
  assume the bot can travel to a known place on request. **They are gated on this.**

### What the fix looks like (NOT built)
A cross-map journey planner: BFS the map-connection graph **plus** warp edges to produce an
ordered leg list, then execute leg by leg with `navigate_to`, re-planning from the real
position after each leg (the shape `navigate_to_anywhere` already uses for cross-region
routes — it just never gets to use it). Needs: the desert/elevation splits expressed as
sub-map partitions (Route 111 north vs south are the same map but not mutually walkable),
capability gates (Surf/Fly/Go-Goggles), and a frame budget per leg.

‼ **Do not "fix" this by adding gateway waypoints.** Tried and refuted 2026-07-30: a gateway
in the same region is routed by the same broken same-region branch, so it fails identically.
Fallarbor PC, Lavaridge PC and Fiery Path were all tried as gateways from Mauville; every
leg failed at 255 frames (`probe_counter_gateway.py`).

## KI-40 — Runs stopped FINISHING and the global watchdog fires ~77x more often (2026-07-30, UNATTRIBUTED)

**Measured**, bundle `20260730-204036` (build `ffb062ce`, 4 lanes, ~3h11m) vs bundle
`20260730-062818` (build `21b587f1`, ~13h):

| metric | `21b587f1` | `ffb062ce` |
|---|---|---|
| runs reaching `finished` | 29 of 60 run-ends (48%) | **0 of 30** |
| `global watchdog — nothing progressed` | 5 (~0.4/h) | **94 (~29.5/h)** |
| dominant run-end reason | `boss: N losses…` (22) | **global watchdog (23 of 30)** |

**Not environmental:** RUN HEADERs are identical — Python 3.13.7, same ROM, `speed=0
video=True audio=False`, fodder rule `xp_rate`. **Not an instrument change:** the watchdog
message and its 18,000-frame bound are unchanged since `88a0e307`, present in both builds.

**Observed wedge sites:** `training N battler(s) to Lv 31 in ROUTE117` (stage 9, map (10,0)),
and the `Rock Smash teach skipped → Fallarbor travel not applicable → Meteor Falls scene
already done` sequence (stage 11, map (24,12)). In both, recovery re-enters the same step and
the watchdog fires again — derail #2, #3, #5 on the identical step.

**‼ ATTRIBUTION IS OPEN.** The bundles are 16 commits apart. Ten are prior-session work
(KI-34, KI-35, KI-36, KI-37 fixes); four are mine and touch production code (`5229e780`,
`f74fab6c`, `31647da3`, `06807942`). The `21b587f1` bundle is the already-reviewed
`20260730-062818` batch, i.e. it predates ALL of them. **Do not blame or clear either group
from this data.**

**Refuted already:** that `_counter_ladder`'s `_note_training_unreachable` calls poison the
training-area picker. Only 2 blacklist events came from the ladder; `ROUTE111 (25,55)`
dominates in both builds (14 new / 24 old) and is the training picker's own doing.

**THE EXPERIMENT THAT SETTLES IT (do this before any more long batches):** ~1 hour on
`d7d493d8` and ~1 hour on `ffb062ce`, same lanes and settings, comparing **watchdog fires per
hour** and **finish rate**. `d7d493d8` is the last build the handoff records as
live-validated — but note that validation was *"no unrecovered errors"* and never checked
finish rate, so it may not be a clean baseline either. If `d7d493d8` is clean, bisect my four
commits; if it is not, the cause is in the KI-34/35/36/37 work.

### KI-40 — ATTRIBUTED 2026-07-30 by controlled A/B. The 2026-07-30 counter-chain work is CLEARED.

Baseline arm run on the user's machine: bundle `20260730-214525`, build **`d7d493d8`**
(detached HEAD via tag `baseline/ki40`), launch `212123`, ~24 min, 4 lanes.

| build | window | watchdog fires | **per hour** | runs `finished` |
|---|---|---|---|---|
| `21b587f1` (pre-KI-34/35/36/37) | ~13 h | 5 | **0.4** | 29 of 60 |
| **`d7d493d8` (baseline arm)** | ~0.4 h | 8 | **~20** | **0 of 2** |
| `ffb062ce` (counter-chain work) | ~3.2 h | 94 | **~29.5** | 0 of 30 |

**`d7d493d8` already wedges at ~50× the old rate**, in the same order of magnitude as
`ffb062ce`. The discrimination required was "≈0 or ≈30 per hour"; it came back ≈20.
⇒ **The regression entered between `21b587f1` and `d7d493d8`** — i.e. in the
**KI-34 / KI-35 / KI-36 / KI-37** work (`00db4a81`, `4f1e02f9`, `d7d493d8`), NOT in the
2026-07-30 counter-chain or menu commits.

‼ **This also corrects the handoff.** `d7d493d8` was recorded as live-validated — but that
validation was *"no unrecovered errors"*, and it never checked **finish rate**. On the
finish-rate metric `d7d493d8` is badly broken, and that went unnoticed for a full day of work
built on top of it. **A "clean" verdict is only as good as the metric it was measured on.**

**The wedge is the TARGETED-TRAINING path, in both builds:**
* `d7d493d8`: `Taillow is the answer to this gym but needs Lv 18 — targeted top-up of just
  that mon` → wedge. Stage 7 (Brawly), map (3,3) = DEWFORD_TOWN_GYM.
* `ffb062ce`: `prepping — training 3 battler(s) to Lv 31 in ROUTE117` → wedge. Stage 9,
  map (10,0); also the Rock Smash→Fallarbor→Meteor Falls sequence at map (24,12).
In both, recovery re-enters the identical step and the watchdog fires again (derail #2, #3,
#5 on the same step), so the step itself never becomes completable.

**Leading hypothesis — the mode is being STARVED, not stuck.** The watchdog reports "nothing
progressed for 18,000 frames", which is what a listener sitting above the mode produces.
`04-HANDOFF` Rule 2 already warns: *"Every listener that can sit above the mode must honour
`battle_fault_pending()` and be bounded… `BattleListener` and `TrainerApproachListener` now
do; **others are UNAUDITED**."* The window's diff is +143 lines in `battle_handler.py` and
+21 in `_listeners.py`. **Audit every remaining listener next**; a training spin walks in
grass and is exactly where listener traffic is heaviest.

**Next step is DIAGNOSIS, not more batches** — the remaining suspect set is 3 commits and the
symptom is reproducible in-run. A further 1-hour arm on `00db4a81` or `4f1e02f9` would bisect
it if reading the diffs does not.

### KI-40 → ROOT-CAUSED 2026-07-30: it is **KI-38**, and KI-38 is not "residual" — it is the dominant run-killer

`05-KNOWN-ISSUES`/`04-HANDOFF` describe KI-38 as *"3 residual after-faint give-ups"*. That
figure came from one sample. Measured across both A/B arms it is the thing ending the runs.

**The STUCK dump (baseline `d7d493d8`, P2, f623813) is unambiguous:**
```
message='Story: entering Dewford Gym to challenge Brawly...'
game_state=3  controllable=False
battle: active=True  instr=BattleScript_FaintedMonTryChoose
tasks=['Task_HandleChooseMonInput']            <- the after-faint party menu is OPEN
party=['Taillow L19 0/48', 'Marshtomp L17 55/55', 'Nincada L10 0/28', 'Whismur L17 51/51']
controllers=['StoryEndlessResetMode.run']      <- ‼ NO battle handler on the stack
===== DUMP [STUCK — 111000 frames no progress] =====
```
Two healthy mons (Marshtomp 55/55, Whismur 51/51) were available to send in. Nothing was
driving the battle: the faint chooser had already given up and left the menu open.

**Rates (`GAVE UP` / hour), stable across builds:** baseline `d7d493d8` 9 in ~0.4 h ≈ **22/h**;
`ffb062ce` 75 in ~3.2 h ≈ **23/h**. Faults handed to the mode: 5 and 48 respectively.
‼ **`NO ELIGIBLE REPLACEMENT` = 0 in BOTH.** The chooser always had a valid, living target and
still failed to select it. This is not a "no legal move" case; it is a selection bug.

**Why KI-34's fix made the SYMPTOM worse while being correct in itself.** `4f1e02f9` added
`FAINT_CHOOSER_GIVEUP_LIMIT = 3` to bound an unbounded re-entry (previously ~35 re-entries /
210,000 frames per battle). The bound works — but on giving up it leaves **the battle still
active with the menu open**, hands a fault to the mode, and the mode's recovery (B-ride,
re-orient, resume) cannot answer an in-battle party menu. So recovery re-enters the same step
and wedges again — derail #2, #3, #5 on the identical step. Before the limit, the handler span
forever inside one battle (wasteful, but it stayed on the stack and could still succeed, which
is why `21b587f1` still finished 48% of its runs). **The limit converted a slow leak into a
hard stop.** Both the index-space fix and the bound are right; what is missing is a
give-up path that RESOLVES the battle instead of abandoning it.

**Therefore the fix must be one of:**
1. ‼ **Make the chooser actually select** — `#24-menutext`, already named in the handoff as
   the resolver: read the party-menu text so the bot knows what the cursor is on, instead of
   inferring from indices. **The string MUST come from the decomp.** KI-38's own evidence
   (`presses={'Down': 3, 'A': 273}`, `cursors_seen=[0,2,3,7]` in a 4-mon party, where 7 is
   probably CANCEL) says the cursor model is wrong, which no amount of retrying fixes.
2. **Make the give-up SAFE** — on give-up, drive the battle to a resolved state rather than
   returning with the menu open. A fault the mode cannot act on is worse than no fault.
3. **Interim mitigation only:** raise `FAINT_CHOOSER_GIVEUP_LIMIT`. This trades a hard wedge
   for the old slow leak; it keeps KI-34's index-space fix (which is correct and unrelated).
   Cheap to try, one constant, and it should restore something like the 48% finish rate —
   but it is a mitigation, not a fix, and it must not be mistaken for one.

## ‼ KI-39 — CORRECTED AND LARGELY RESOLVED 2026-07-31. Read this before the section above.

**The KI-39 entry above states the cause wrongly, and the handoff repeated it.** The claim
was *"`calculate_path` only spans directly-connected maps"* and *"the bot has NO cross-map
overworld route planning"*. Both are false. Measured live from `rocksmash_taught.ss1`
(Mauville 32,15) with the SAME `calculate_path` the production path uses
(`tools/story-dev/probe_journey_legs.py`, `probe_journey_why.py`, `probe_journey_walls.py`):

* `map_path.py` assigns **every** edge-connected map a global offset and a shared `level`,
  and its own docstring says it "supports paths across several maps, but only if they are
  connected". Mauville, Routes 110/111/112/116/117 and Verdanturf are **all level 459** — so
  `calculate_path` was trying, and failing at TILE level, not refusing to plan.
* Partial reachability proves it: **ROUTE110 17/125 tiles reachable, ROUTE111 11/173,
  ROUTE117 22/41, VERDANTURF 14/23.** A planner that could not cross maps would score 0.

### The four blocked trips had FOUR DIFFERENT causes. Only one was route planning.

| trip | measured cause | status |
|---|---|---|
| Mauville → **ROUTE116** | Verdanturf declares a North map CONNECTION to Route 116, so the union-find merges them into one region — but **0 of 40 sampled Route 116 tiles are walkable from Verdanturf**, while the RUSTURF_TUNNEL door at VERDANTURF (8,1) is. The real link is a **warp inside one region**, and `WarpGraph.plan()` returns `[]` for any same-region pair. **This is the genuine KI-39.** | **FIXED** (see below) |
| Mauville → **ROUTE110** (12,60) | reachable strip ends at y≈20 (column 12); the rest is behind the cycling-road gate structures — same warp-inside-a-region class | fixed in kind; specific tile still needs the gates |
| Mauville → **ROUTE112 / FIERY_PATH** | the **Rock Smash twin-rocks choke on ROUTE111 at (18,101)**. Column-by-column probe: reachable y≥102, blocked y≤101 across columns 17–20. Route 112 scores **0/76**, and Fiery Path's only two doors are both on Route 112. | **NOT a planner problem** — see KI-41 |
| Mauville → **ROUTE111** (25,55) | the Go-Goggles desert. Genuinely gated; the south strip is reachable, the north is not. | correct refusal |

### The fix that shipped
`WarpGraph.warp_candidates()` — warp planning at **MAP** granularity instead of REGION
granularity, so a warp route can be returned even when start and goal share a region. The
map-level adjacency is now kept (it was previously consumed by the union-find and discarded);
`CACHE_VERSION` 1→2 so stale caches rebuild rather than silently loading a degraded graph.
`navigate_to_anywhere` now (1) asks `calculate_path` whether a plain walk works — unchanged
fast path if yes — and only then (2) asks for warp candidates and **validates each one's
first leg with `calculate_path` before committing**, remembering warps it has taken so a
re-plan cannot ping-pong.

‼ Also fixed in the same change: `navigate_to_anywhere`'s "did the warp fire?" test compared
**regions**. A warp between two maps of the same region — exactly the class this makes
plannable — leaves the region unchanged, so a *working* warp would have been reported as
`"Warp at … did not trigger (locked or event-gated?)"`. It compares maps now.

### Proof
* `tools/story-dev/repro_journey_planner.py` — 27 checks, no emulator, pins the whole
  topology including the two traps below.
* `tools/story-dev/probe_journey_live.py` (+ `story_harness.py --driver journey`) — live
  fault-injected A/B in the faithful harness:
  **OLD arm `arrived=False map=MAUVILLE_CITY`** (never left the starting map) vs
  **NEW arm `arrived=True map=ROUTE116`, 33,725 frames**, walking Mauville → Route 117 →
  Verdanturf → Rusturf Tunnel → Route 116.

### Two traps found while building it, both pinned by the repro
1. **The progress filter must be NON-INCREASING, not strictly decreasing.** The phantom
   Verdanturf→Route116 connection puts the target 1 hop away, so *nothing* can be strictly
   closer and a strict filter drops the very warp that works.
2. **Banning the previous answer produces junk candidates.** Verdanturf→Route116 offered the
   BATTLE TENT LOBBY and the MART as candidates 5 and 6 — real routes (walk in, walk out,
   then take the tunnel) that make no progress. Harmless only while an earlier candidate
   validates, which is not a guarantee.

### ‼ What this does NOT fix — correct the handoff's expectations
The handoff said `#24-journey` *"unblocks the thing that is killing runs"*. **It does not.**
The counter the ladder names is Machop @ FIERY_PATH, and measured after the fix: a warp route
to FIERY_PATH **is** found (2 candidates, both ROUTE112 doors) and **neither first leg is
walkable**, because of the Rock Smash choke. The planner was never the blocker there — see
**KI-41**, which is now the thing standing between the counter chain and acting.

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

## KI-46 — Battle ACTION SELECTION spins for ever on an unrecognised controller callback (2026-08-03, FIXED same day)

**KI-45 was one instance of a pattern. This is another, at a different site.**

**Observed**, batch10 (`x4-runs/20260803-164713`): lanes **H2 and H8 both wedged for ~59
minutes**. **H8 completed 0 runs in the whole 180-minute batch**; H2 managed 2 against 4-5
elsewhere. Both stacks stopped at `battle_action_selection.py:55`, with **zero**
`_select_in_menu` dumps — so the KI-45 bound was not involved.

```
BattleListener.fight → handle_battle → handle_battle_action_selection  @ :55
```

**Cause.** `handle_battle_action_selection`'s loop conditions are sound (battle over, or the
main callback moves on). But if the battle stays ACTIVE in turn-action-selection while the
CONTROLLER callback matches none of the branches, control reaches a bare
`else: yield; continue` and spins there indefinitely.

**Fix.** `_MAX_UNRECOGNISED_FRAMES = 600` (~10 s) counting only frames where the state is NOT
recognised; the counter **resets the moment a real decision is made**, so a long multi-turn
battle never accumulates toward it. On exhaustion it reports via
`battle_fault.request_mode_recovery()` — one recoverable derail for an opted-in mode — and
raises `BotModeError` otherwise. The message carries **both observed callbacks**, because that
is the diagnosis: it names the unrecognised state so the branch can be added properly.

‼ **The fix contained the exact bug it was fixing a sibling of.** `BotModeError` is not
imported at that module's top, so the first version would have raised `NameError` *instead of*
the honest error — the same shape as the swallowed `get_party` NameError that made
`#24-leadcounter` silently dead for two batches. Caught only because
`repro_ki46_action_selection_bound.py` **drives the real generator** and asserts the exception
is not a `NameError`. A source-text assertion would have passed.

**Repro:** `repro_ki46_action_selection_bound.py` — drives the generator, and check 5 proves a
battle that ends normally is unaffected (no false positive).

‼ **THE STANDING LESSON (now twice measured): both project-level guards are structurally blind
to any loop on the battle path.** The global watchdog needs an UNCHANGED progress signature and
a battle keeps changing it; the per-run frame budget is KI-36's documented "cannot fire while a
battle handler is on the stack". **Any `while` loop under `BattleListener.fight` has no safety
net but its own bound.** Audit the remaining ones rather than waiting for the next lost lane.

---

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

## KI-51 — FIXED 2026-08-11: `do_magma_hideout` rode 60,000 frames at an empty overworld after a whiteout, then blamed the wrong thing

**Symptom (found by KI-50's run).** After the whiteout above, the Maxie challenge loop kept
mashing A/B for **18,300+ frames and counting** — 13 `STUCK` dumps — with the step message frozen
at `"at (15, 21), facing Right at Maxie (16, 21)"` while the avatar was standing in
**MAUVILLE CITY (22,6)**, two towns away.

**Root cause.** The loop's only exit condition was `while not _groudon_awakened()`. A whiteout
cannot make that true, so the loop was structurally incapable of noticing it. It *was* bounded
(60,000 frames), so this was never an infinite hang — but the bound's message names the wrong
cause entirely: *"the Maxie challenge never resolved in 60,000 frames"*, when what actually
happened is that the party fainted and the game teleported the player out.

‼ **Same class as the 2026-08-10 lesson, one week later**: *a failure message must report STATE,
not a HYPOTHESIS* — that one said "check the destination is walkable" across three runs where it
always was.

**The fix.** The loop now also watches the map: if the player is off `MAGMA_HIDEOUT_4F` for more
than **300 consecutive frames**, it raises immediately and reports the real state (map, tile,
`party_alive`, frames elapsed) instead of riding the bound out.
* **Debounced, deliberately.** An instant check would risk ending a HEALTHY Maxie fight on one
  odd frame across a battle screen transition — a far worse bug than the one being fixed. 300
  frames (~5s) is longer than any transition here and still ~200x cheaper than the full bound.
* **An unreadable map counts as "still on 4F"**, so a reader error can never end the fight.

✅ **CONFIRMED LIVE 2026-08-11** (`mh-try1`, the anchor retry loop) — the guard fired and printed
its own message, which is the evidence that was missing when this entry was first written:
```
[magmahideout] FAILED: BotModeError: Magma Hideout: left MAGMA_HIDEOUT_4F during the Maxie
challenge without Groudon awakening — almost certainly a WHITEOUT. map=(0, 2) tile=(22, 6)
party_alive=6/6 (was standing (15, 21) facing Right at Maxie (16, 21), 2209 frames in).
```
`map=(0,2)` is MAUVILLE_CITY and `(22,6)` is the whiteout respawn tile — exactly the state the
pre-fix loop rode straight past. **It stopped at 2,209 frames against a 60,000-frame bound**, so
this failure cost ~57,800 fewer frames than it used to. (An earlier run stopping at ~20,600 frames
was NOT counted as proof, because `_check_abort()` is an equally possible raise in the same loop
and that run's stdout was lost. This one prints the message, so it is decided.)

‼ **AND IT CORRECTS ONE OF MY OWN CHOICES: `party_alive=6/6` is NOT diagnostic here.** I put that
field in the message expecting it to be the corroborating fact for "whiteout" — but a whiteout
HEALS the party, so it reads full precisely BECAUSE the thing happened. The diagnosis rests
entirely on the **map**. The field is still worth printing (it rules out "the party is dying right
now"), but a future reader must not treat 6/6 as contradicting the whiteout call.
‼ And note WHY `_check_abort()` did not save the PRE-fix run: it raises on `_STORY_ABORT`, which
**StoryMode's** whiteout handling sets — a harness driver need not mirror that override
(`04-HANDOFF`: "a harness driver must mirror the OVERRIDES of the mode it stands in for"). **A
guard that only works in one of the two ways the code is run is not a guard**, which is the
argument for the map check existing at all.

**Structural proof:** `repro_maxie_whiteout_guard.py` (no emulator, 18 checks — the map read, the
debounce, the unreadable-map default, the STATE fields in the message, and the ordering against
the 60,000 bound). Fault-injected to **2 red**, restored to **ALL PASS**.

**Verified, both directions, on real committed saves** (`map_group_and_number` is a plain tuple;
`== MapRSE.X.value` is a valid identity test):
```
magma_door.ss1      (24,13)  == JAGGED_PASS       -> True    == MAGMA_HIDEOUT_4F -> False
magma_1f_fail.ss1   (24,91)  == MAGMA_HIDEOUT_4F  -> True
```
⇒ on 4F the guard never fires; off 4F it fires. ‼ Note the second control also shows
**`saves/magma_1f_fail.ss1` is misnamed — it stands on 4F, not 1F.**

**Prevention rule.** *A loop whose exit condition is a story flag must ALSO watch for the ways the
game can move the player out from under it. A whiteout satisfies no flag.*

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

## KI-54 — "Roster hygiene before bosses" is BLOCKED: the box is EMPTY, and the deposit path it would need was already measured harmful (2026-08-11, severity: informational — a plan-blocker, not a defect)

**Context.** The user approved "roster hygiene before bosses" on 2026-08-11 after the Magma Hideout
loss showed **two dead party slots** (Zigzagoon L6, Skitty L17) in a **L38-39** boss fight, one of
which (Skitty) cost the kill on Camerupt at 22/110 immediately before Maxie healed it to 67.
**Verification before building found two blockers.**

### ‼ BLOCKER 1 — there is nothing to swap TO. The box is EMPTY.
```
post_maxie.ss1         party 6, BOX 0
magma_door_losing.ss1  party 6, BOX 0
POSITIVE CONTROL boxwithdraw.ss1 -> 2 in box: ['Poochyena:L26', 'Shuppet:L26']
```
The control matters: an empty box and a broken box reader look identical. The reader works.

### ‼ BLOCKER 2 — the deposit path EXISTS and is pinned OFF with measured harm
`modules/story/pc_trip.py: deposit_dead_weight_if_worth_it()`, gated by `POKEBOT_PC_ROTATION`
(default **0**) since 2026-08-05:
| batch | PC deposits | avg team size at Feather | Balance→Feather |
|---|---|---|---|
| b3 / b4 / b5 (OFF) | 0 | 5.65 / 5.72 / 5.81 | 83 / 75 / 70% |
| b8 (ON) | 14 | **4.45** | **52%** |
| b13 (ON) | 18 | **4.75** | **57%** |
It removed ~**one whole team member permanently** and the last funnel rung collapsed over exactly
that transition.

⇒ **The SWAP version is impossible (empty box); the DEPOSIT-ONLY version is that disproven feature
in narrower clothing.** Do not rebuild it from the boss-fight evidence alone.

### ⛔⛔ THE "MISSING PIECE" BELOW IS WRONG — RETRACTED 2026-08-12. READ THIS FIRST.

**`POKEBOT_BOX_OVERFLOW_CATCH` IS NOT DISABLED. It has defaulted to ON since 2026-08-07** —
`plugins/custom_modes/story_mode.py:2241-2243` reads
`_os.environ.get("POKEBOT_BOX_OVERFLOW_CATCH", "1")`. **Verified in the live code**, not recalled.

And the "one unhandled text box" blocker was **refuted on 2026-08-07, four days before the section
below was written**. The capability test is recorded in the comment right above the flag read:
`--driver boxcatch` on a full party with an empty box gave `caught=True box_before=0 box_after=1
exited_clean=True exit_frames=120`, then `AFTER-CATCH usable=True second_catch=True frames=20
box_now=2` — **zero forced presses**; the existing battle handler rides the box-send message out.
(The message is real decomp — `Cmd_givecaughtmon` → `B_MSG_SENT_SOMEONES_PC` — it simply needs no
handling.) `03-PUNCH-LIST.md` says so plainly: *"I 'confirmed' that wedge twice and both were my
probe idling."*

‼ **HOW THIS HAPPENED, because it is the more valuable lesson.** Four documents were written on
2026-08-11 by reading a **stale comment block** (`story_mode.py:2202-2226`, which still said
"GATED OFF … default 0") instead of the **live default twenty lines below it**. That is precisely
the failure the flag registry was created to prevent, committed one level up — in the registry
itself. ⇒ **A registry row is a claim with an expiry date too. Read the code the row describes,
not the prose next to it.**

**Consequence:** BLOCKER 1 below is void as a blocker. The box being empty was never a gate; the
counter hunt simply never had a full party when it fired.

<details><summary>Superseded text, kept because the batch evidence in it is still real</summary>

`POKEBOT_BOX_OVERFLOW_CATCH` (default **0**, `#24-pcoverflow`) is the feature that lets a catch
overflow **into the PC box** when the party is full. **It is off, so nothing ever puts anything in
the box.** That is the direct cause of BLOCKER 1.

It was gated after batch `20260806-142418` graded it against its own **pre-registered** target and
it FAILED: `withdrawing` **0** (target ≥1) and `INTO THE PC BOX` **0** — the path **never fired in
26 runs**. ‼ The code is careful to add that it is off because it **delivered nothing**, not
because it was proven harmful (only 10 of 43 watchdog dumps had a full party; the wedges were
battle-handler shaped).

‼‼ **AND THE BLOCKER IS NAMED AND SMALL:** a box-send shows an **EXTRA TEXT BOX** that the
party-catch path never shows, and the bot has no handling for it (user-identified 2026-08-06, then
decomp-confirmed).

⇒ **This re-orders the roster options.** Option (a) "populate the box first" is not a large new
project — it is **one unhandled text box** away from firing. That is a far better first move than
(b) re-enabling the measured-harmful deposit path.

‼ **How this was found is the point:** the measurement lived in a code comment in
`story_mode.py`, where nobody looks before proposing a feature. `lint_docs.py`'s new R6 rule forced
every `POKEBOT_*` flag into `29-DISABLED-FEATURES-REGISTRY.md`, and this flag surfaced immediately —
an 11th flag that my own hand-written grep had missed.

</details>

### ✅ THE ACTUAL PLAN, 2026-08-12 — deposit-first, and it is SMALLER than the box round-trip

With BLOCKER 1 void, the remaining question is only how to free one party slot for a Dive learner.
**Measured against `modules/data`, not recalled:**
* **76 species learn Dive; NONE of ours does**, and there is no evolution escape — **Linoone NO,
  Delcatty NO**, Castform has no evolution, and Beldum is post-Champion. **A catch is mandatory.**
* **Spheal is the answer: ~50% of the `SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM` LAND table at L26-32,
  catch rate 255 (the maximum), and it learns BOTH Surf and Dive.** `MOSSDEEP_CITY` connects
  directly to `ROUTE125`, and Route 125 → the entrance room is **one warp** — no cave threading.
  ⚠ **TIDE IS THE RISK:** only the five LOW-tide maps have an encounter header in our ROM; the high
  tide maps have **none at all**. Which RTC hours give low tide is **UNVERIFIED**.
* **Fallback with no tide dependency: Marill on Route 120**, 15% at L25-27, learns both.
* ⛔ **Do NOT fetch the Super Rod first.** Sharpedo/Wailmer are real (40%/60% Super Rod off
  Mossdeep, both learn Surf+Dive) but need **three missing subsystems**: no rod-fetch chapter
  exists, the story bot has **no fishing capability at all**, and `_hm_hunting_grounds` reads
  `land_encounters` ONLY. One `TRAINING_GRASS` row versus three subsystems.

‼ **AND THE BOX ROUND-TRIP IS THE LONGER PATH, NOT THE SHORTER ONE** — the opposite of what I
assumed. `ensure_hm_learner`'s success test reads the **party** (`hm_learner_slot(item) is not
None`), so a catch that lands in the box never satisfies it: the spin burns its whole 40,000-frame
budget and raises "never caught one". Routing through the box would need the stop condition changed,
the new PID captured and registered, **and** a Poké Center trip anyway.

**Deposit-first is strictly smaller and reuses only PROVEN code:**
1. one `TRAINING_GRASS` row for the Shoal Cave entrance room (spin tile derived and two-way swept
   from a real anchor — never from recall);
2. replace the `raise` in `ensure_hm_learner` with a `free_one_party_slot()` factored out of
   **`withdraw_from_box:331-355`**, which already deposits **exactly one** mon, worst-first, and is
   live-proven by `--driver boxwithdraw` (three identical consecutive runs, `deposited=True
   withdrew=True party_after=6`, and the second heal produced exactly one withdraw line).
   ‼ **This is NOT the measured-harmful rotation.** That harm was `POKEBOT_PC_ROTATION`, which fires
   on **every heal** and deposits up to 2 mons down to a floor of 3. Freeing one slot once is a
   different act, and KI-54 says so itself.
3. **Verified offline against our exact party:** the real predicate picks **Skitty L17** — and
   correctly **spares Zigzagoon L15 despite it being the lowest level**, because `_only_hm_carrier`
   protects our sole Surf carrier. That is exactly the mon KI-54 named as "the real passenger".
⚠ Second-order: Spheal arrives at L26-32 against an L48 lead, so it is itself "dead weight" by the
L48−8 rule. Harmless while `POKEBOT_PC_ROTATION=0`; it becomes a **self-eviction loop** if anyone
turns that on.

### ‼ THE TIDE IS NOT A BLOCKER — measured 2026-08-12, and it removes the plan's only unknown

The tide worry was **real but misdirected**. Findings, decomp- and ROM-measured:
* `UpdateShoalTideFlag()` (`src/time_events.c:54-92`) is a **24-entry hour table**;
  `FLAG_SYS_SHOAL_TIDE` **set = HIGH**. LOW tide is hours **03-08 and 15-20**. It is sampled ONLY on
  `ON_TRANSITION` into the entrance room from an OUTDOOR map, and is then frozen for the visit.
* ‼‼ **BUT THE TIDE GATES THE DESCENT, NOT THE HUNT.** The high-tide "maps" (24,50)/(24,51) have
  **no encounter header and zero warp edges** — they exist only to own a layout that
  `setmaplayoutindex` borrows onto map (24,46). The player stays on **(24,46)** at both tides, and
  `GetCurrentMapWildMonHeaderId` keys off map group/number, **not layout**. Measured from our ROM:
  the entrance room still has **65 walkable `MB_CAVE` encounter tiles at high tide** (332 at low).
  ⇒ **The Spheal 50% table is live at BOTH tides. No tide handling is needed at all.**
* **Surf is the only gate**, and we have it: our planner routes `MOSSDEEP_CITY (49,35) → ROUTE125
  (22,19)` in **119 waypoints**, and Zigzagoon L15 knows Surf (measured on the live save). Route 125
  → the entrance room is a single warp, (22,19) ↔ (20,30).
* Spin-tile candidates, all `MB_CAVE` with two-way static `calculate_path` PASS: **(25,30)** (5 steps
  from the arrival warp), (14,30), (20,24). ⚠ **Static evidence only — NOT the live two-way sweep
  this project requires** (the Route 114 demotion). Never promote a spin tile on this alone.
* ⚠ **A REAL HAZARD FOR ANY IN-ROOM NAVIGATION:** `MapLocation` resolves the layout from the cached
  ROM map header, i.e. **always the LOW-tide floor plan** for (24,46). At high tide the planner is
  therefore planning against the wrong map. Fix or fence this before any code paths inside that room.
* ⚠ Never spin on or south-adjacent to **(20,30)** — it is `MB_SHOAL_CAVE_ENTRANCE`, which counts as
  a south-arrow warp.

**‼ AND THE REAL BLOCKER IS STILL THE FULL PARTY:** `ensure_hm_learner` raises at
`early_game.py:4342-4348` when the party is ≥6 **before it ever calls `_hm_hunting_grounds`**. So the
hunting ground is necessary but not sufficient — freeing the slot is the gate, exactly as the
deposit-first plan above says.

**Cheapest tide-free fallback, needing ZERO new data:** `_hm_hunting_grounds(HM08)` **already**
returns one ground today — **ROUTE117 (31,16), Marill, 10%**, already two-way swept. Route 120 is not
in `TRAINING_GRASS` and would itself need a swept row, so Route 117 is strictly cheaper if the Shoal
Cave sweep fails.

### ‼ THE LIKELY CAUSAL LOOP, stated as a hypothesis
With deposits OFF, **anything caught stays in the party for ever** — so the party fills with
passengers. The dead weight may be a *symptom* of deposits being off, and deposits are off because
they thinned the team. That is a genuine tension, not an oversight.
‼ One nuance worth keeping: the old rotation policy was bad at **choosing** — it deposited a
*hunted counter* and a Machop 25 levels behind the team's best. "That policy was harmful" is not
the same claim as "depositing is harmful", but neither has been measured separately.

### What is NOT blocked
* Zigzagoon is the **HM slave** (Surf / Rock Smash / Strength) — it has a job and should not be
  treated as dead weight. **Skitty L17 has no stated job**; it is the real passenger.
* Passengers only reach the field after the competent mons faint — but that is exactly when the
  fight is decided, and in the measured fight it cost the kill. The marginal value is real but it
  is second-order to whatever fainted the first four.

### DECISION REQUIRED (not taken)
Options: (a) populate the box first — `#24-roster`'s actual scope, catch-overflow, with its own
prerequisites; (b) re-enable deposits under a much tighter policy (never a hunted counter, never
an HM carrier, never below party 5, only >N levels behind) — ‼ re-opens a measured-harmful path and
must not ship without a batch; (c) a catch/keep policy so passengers never enter the party;
(d) park roster work and do the STATUS response instead, which needs no box and has a
deterministic fixture (`magma_door_losing.ss1`).

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

## KI-63 — NO party member can learn Dive, and the party is full: §Ch21 is BLOCKED (2026-08-12, MEASURED, OPEN)

Measured on `post_mossdeep_gym.ss1` by `tools/story-dev/probe_ch19_hazards.py`:
```
party 6/6: Sceptile L48, Zigzagoon L15, Swellow L40, Skitty L17, Mightyena L44, Castform L36
Dive learners in party: NONE
```
Only 76 species learn Dive and none of ours is among them.

**‼ WHAT THIS DOES AND DOES NOT BLOCK.** Receiving **HM08 is a scripted gift and needs no learner**,
so §Ch19 (Space Center) and the Dive hand-over in Steven's house are unaffected — `FLAG_RECEIVED_HM_DIVE`
will set normally, and it is that flag which removes the Seafloor Cavern entrance guard. What is
blocked is **USING** Dive, i.e. actually reaching the Seafloor Cavern (§Ch21).

**Why it is not a small fix.** The party is FULL, so a catch would go to the PC, and
`early_game.py:4294` already refuses exactly this case:
> `No party mon can learn {move} and the party is full — needs PC box management (#24-pc) or a
> manual swap.`
And `#24-roster`/`#24-pc` is itself gated by KI-54 (the box is empty and the deposit path was
measured harmful). ⇒ **`#24-pc` is a PREREQUISITE of the Seafloor Cavern, not a later nicety.**

**‼ The natural swap is not the obvious one.** Zigzagoon L15 is the party's ONLY Surf carrier, so it
cannot simply be dropped. A **Wailmer or Tentacool** — both on the water this arc already crosses
(Routes 124/126/127/128) — learns **Surf and Dive**, which makes it a single swap that covers both
duties. To settle before building: confirm the encounter tables in `modules/data` rather than
trusting this note.

‼ **NOW REPRODUCIBLE — `tools/story-dev/probe_dive_learner.py` (added 2026-08-12).** The correction
below was first committed as **docs only**, labelled "measured", with **no script and no artifact**.
An adversarial pass called that out: every number was independently re-derived and turned out to be
right, but it was *right by a good recall, not by anything anyone could re-run* — the exact failure
this project's rules exist to prevent, committed by the agent enforcing them. The probe reads
`species.json` + the encounter index and reproduces all of it:
```
species that learn Dive: 76      Dive learners in the party: NONE
evolution escape: NONE — a CATCH IS MANDATORY  (Zigzagoon->Linoone, Skitty->Delcatty, neither learns it)
 50%  Shoal Cave (Low Tide), Entrance Room   Spheal  L26-32  +SURF (covers BOTH duties)
 15%  Route 120                              Marill  L25-27  +SURF      <- tide-free fallback
```
‼ It carries a printed CONTROL on every id→name resolution, and they earned their place at once:
the first draft read `evolutions[].target_species` as a national dex number and produced
*"Zigzagoon -> Slaking"*. That wrong mapping would still have returned the RIGHT ANSWER to the
question being asked ("no evolution learns Dive") — a correct conclusion from garbage data.
**Sanity-check an id→name mapping against a pair you already know before trusting it on pairs you
do not.**

**‼ CORRECTION 2026-08-12 (measured, supersedes the swap suggestion above).** **Wailmer is ROD-ONLY
and the bag has no rod**, and Tentacool is a surf slot spanning L5-35. The better candidate from our
own species data is **Spheal** — ~50% of the Shoal Cave low-tide **land** table at L26-32, Ice/Water,
and it learns **both Surf and Dive** with no rod needed. Also: `RECEIVED_SUPER_ROD` is **False** and
the free Super Rod is in `MOSSDEEP_CITY_HOUSE3`, which would additionally make **Sharpedo** (40% of
casts, L30-35) available — it learns both too. ⚠ Shoal Cave HIGH-tide rooms returned **no encounter
header at all** in our ROM, so tide timing matters. Still blocked by the 6/6 party + KI-54.

## KI-64 — the multi-battle faint replacer would send out the ALLY's Pokémon (2026-08-12, code-verified, ✅ FIXED)

Found while building §Ch19 by an audit of our own code, and confirmed by reading both choosers.

`SPECIAL_BATTLE_STEVEN` (the Mossdeep Space Center) runs `ReducePlayerPartyToSelectedMons` and then
`FillPartnerParty`, which writes Steven's max-IV **Metang L42 / Skarmory L43 / Aggron L44 into
`gPlayerParty[3..5]`** and sets the party count to 6. So `get_party()` returns **six** Pokémon, only
the first three of which are ours.

Both replacement choosers excluded **only the two mons currently on the field**:
* `modules/battle_strategies/default.py` `choose_new_lead_after_faint` — ranks by highest current HP;
* the story override in `plugins/custom_modes/story_mode.py` — ranks by `(incoming, -outgoing,
  -hp_fraction, -level)`.

Under either rule **three fresh high-level mons beat our damaged party outright**, so the chooser
would return the ally's slot. The game then refuses ("Can't switch with ALLY!") and the party menu is
handed a target it can never accept.

‼ **The guard already existed and had ZERO callers in the entire tree:**
`BattleState.is_double_battle_with_partner` (`modules/battle_state.py:288`). Written, never wired up.
`BattleType.Multi` is likewise never referenced anywhere. **FIXED** by cutting the candidate list at
`MULTI_PARTY_SIZE = 3` in both choosers when that property is true.

‼ **Why it was latent, not harmless:** §Ch19 is the FIRST content in this project to reach a multi
battle. Nothing before it could ever have exercised this path — which is exactly why "no bug has
been observed" said nothing about whether one existed.

‼ **AND THE PASSING RUN PROVED NOTHING ABOUT THE FIX.** §Ch19's end-to-end PASS reported
`whiteouts=0` and **zero faints**, so `choose_new_lead_after_faint` was never called once — the fix
rode along entirely unexercised. Proven instead by **fault injection**,
`tools/story-dev/repro_multi_battle_partner.py` (no emulator, milliseconds), **3/3**:
```
ARM A  old rule      -> slot 5 (Aggron)     ALLY   [AS PREDICTED] the bug reproduces
ARM B  shipped code  -> slot 2 (Mightyena)  OURS   [AS PREDICTED] the fix holds
ARM C  plain double  -> slot 5                     unchanged (no over-correction)
```
ARM A is the **positive control** and is the reason ARM B means anything: a fixture where our own
mon happened to win the ranking would pass under both arms and prove nothing. ARM C exists because a
fix that also changed ordinary double battles would be a regression wearing a fix's clothes.

‼ **THE FIRST FIX WAS WRONG TWICE, AND THE FIRST A/B PASSED IT ANYWAY** (corrected 2026-08-12 by an
adversarial review; full write-up in `08-MISTAKES.md`):
1. **It was DEAD CODE on the story path.** The MRO is `StoryItemBattleStrategy` →
   `LevelUpTravelBattleStrategy` → **`LevelUpLeadBattleStrategy`** → `DefaultBattleStrategy`, and
   `level_up.py:41` has its own `choose_new_lead_after_faint`, so the base-class guard never ran.
2. **The `index >= 3` cut was in the WRONG INDEX SPACE.** Opening the battle party menu runs
   `UpdatePartyToBattleOrder`, which PHYSICALLY PERMUTES `gPlayerParty`. Measured in our own passing
   run (`ch19d.log` f37745): `[Sceptile|Mightyena|Swellow|Metang|…]` → `[Sceptile|**Metang**|Mightyena|**Swellow**|…]`.
   Index 1 becomes the ALLY's Metang and OUR Swellow moves to index 3 — so the cut **offers the ally
   and hides one of ours**, precisely when a replacement is needed.

**The correct fix:** `ally_party_indices(battle_state, party)` in `battle_strategies/default.py`,
keyed on **ORIGINAL TRAINER ID** — identity travels with the Pokémon, position does not. Wired at all
three call sites (`default.py`, `level_up.py`, the story override in `story_mode.py`). It FAILS
CLOSED: an unreadable player/OT excludes nobody rather than everybody, because excluding everybody
would return `None` and push the caller into its full-party fallback — the very bug this prevents.

**Now 5/5 in `repro_multi_battle_partner.py`**, including the two arms that matter:
```
D  permuted array  -> slot 3 (Swellow) OURS   ‼ a positional `<3` rule would have hidden this
                                                 and allowed slot 1 (Metang, the ALLY)
E  LevelUpLead...  -> slot 3 (Swellow) OURS   the class the story bot ACTUALLY calls
```
§Ch19 re-driven end-to-end afterwards: still `ACCEPTANCE: PASS`, `whiteouts=0`.

**RESOLVED, previously flagged unverified:** `BattleType.InGamePartner = 1 << 22` **is** correct —
`battle_tower.c:2122` sets `TRAINER|DOUBLE|TWO_OPPONENTS|MULTI|INGAME_PARTNER`, so
`is_double_battle_with_partner` genuinely reads True in this battle.

⚠ **STILL UNPROVEN LIVE.** Every driven run had `whiteouts=0` and **zero faints**, so no chooser has
ever run in a real multi battle. The repro pins the LOGIC; only a driven loss can pin the whole path.
See KI-66 for the other party scans this fix does NOT cover.

## ‼‼ KI-68 — §Ch21 IS NOT BLOCKED BY THE PARTY SLOT. **DIVE IS NOT ROUTABLE AT ALL.** (2026-08-12, code-verified, OPEN)

**This supersedes the framing in KI-63 and KI-54.** I was one edit away from building the wrong
thing, and an adversarial pass caught it before the code shipped.

**THE MEASUREMENT** (verified by me, not taken on trust):
* `modules/map_path.py:592-593` — `WaypointAction.Dive` and `WaypointAction.Emerge` are **declared
  and assigned NOWHERE in the tree.** A repo-wide search for `WaypointAction.Dive` /
  `WaypointAction.Emerge` returns **zero** assignments.
* `map_path.py:690` — `can_dive()` exists; its only references are its own definition and cache
  lines (`:678, :681, :690-696`). **Zero callers.**
* `modules/warp_graph.py:342` — `continue  # Dive/Emerge need HM08 — excluded on purpose`;
  `modules/story/region_reach.py:68-70` does the same; `modules/modes/util/global_navigation.py:12`
  documents Dive routes as unsupported.
* `modules/modes/util/higher_level_actions.py:682` `dive()` exists, but its only callers are
  `puzzle_solver.py` and a test — **nothing in `modules/story/` or `story_mode.py`.**

⇒ **The planner cannot emit a Dive waypoint.** So the whole "free a party slot → catch a Dive
learner → teach Dive" chain, even executed perfectly, ends at `UnreachableDestinationError` on the
first navigation into a dive spot. **It moves the failure one line down and costs a party member.**

### ‼ REFINED 2026-08-12 (`probe_dive_routing.py`) — "NOT ROUTABLE" ≠ "NOT POSSIBLE"

Do **not** read the above and conclude the Dive content is out of reach. Measured:
* `warp_graph.py:20` and `:342` say it explicitly — *"Dive/Emerge connections … excluded on
  purpose"*. **This is a DESIGN state, not a defect.** A dive is not a warp event at all: it is a
  MOVE used on a deep-water tile that lands you on a different map at the same coordinates, so no
  warp-graph solver could ever offer it and `calculate_path` was never going to.
* **`dive()` ALREADY EXISTS AND WORKS** — `modules/modes/util/higher_level_actions.py:682`, drives
  `Task_UseDive`, and refuses unless the tile really is Deep/Semi-Deep Water and the player is not
  already underwater. So a wrong tile fails LOUDLY.
⇒ **The fix is a CHAPTER that drives the transition, not a change to the planner** — exactly the
pattern already used three times here (§Ch18's `(21,6)` coord-event exit, Steven's bottom-row door
via `_walk_through_warp`, the Magma Hideout Escape Rope). The legs split cleanly:
```
a. surf to the deep-water tile          -> PLANNER   (Surf IS routable)
b. call dive() standing on it           -> CHAPTER   (one call; the missing piece)
c. navigate the UNDERWATER map          -> PLANNER   (ordinary same-map)
d. surface / take the warp in           -> CHAPTER or PLANNER (a real warp)
```

### ✅ THE TOPOLOGY IS FULLY MAPPED, and most of it needs no Dive at all
Read from our own ROM (`probe_dive_routing.py`):
```
UNDERWATER_ROUTE134      (8,8)  -> UNDERWATER_SEALED_CHAMBER
UNDERWATER_SEALED_CHAMBER (7,1) -> UNDERWATER_ROUTE134
SEALED_CHAMBER_OUTER_ROOM (10,2)-> SEALED_CHAMBER_INNER_ROOM
UNDERWATER_SEAFLOOR_CAVERN (6,7)-> UNDERWATER_ROUTE128        (§Ch21)
DESERT_RUINS  (8,29) -> ROUTE111     ISLAND_CAVE (8,29) -> ROUTE105
ANCIENT_TOMB  (8,29) -> ROUTE120
```
‼ **The three Regi tombs are ORDINARY MAP WARPS from routes the bot already reaches.** Only the
**Sealed Chamber unlock** is behind a dive. So the Regi arc is not gated on Dive end-to-end — it is
gated on ONE underwater errand, after which the tombs are ordinary navigation.
‼ Note `UNDERWATER_SEALED_CHAMBER` has **no warp to `SEALED_CHAMBER_OUTER_ROOM`** — that transition
is a SURFACE/emerge, i.e. a second chapter-driven action, not a warp.

‼ **`can_dive()` needs the move KNOWN, not learnable.** Measured on `post_dive.ss1`: `BADGE07_GET`
True, party members knowing Dive **NONE** → it would return False. HM08 being in the bag is not
enough, which is the same distinction KI-63 makes.

### ⇒ THE CORRECT ORDER (and why the obvious order is wrong)
1. **FIRST, prove what the planner needs.** `modules/debug_utilities.py:611` can inject
   `LearnedMove.create(get_move_by_name("Dive"))` onto an existing party mon. Do that and drive
   Route 128 → Seafloor Cavern. **This work is required no matter how the learner is acquired**, and
   it is near-zero risk — no deposit, no new data row, no party change.
2. `_hm_hunting_grounds(HM08)` — **already measured**: it returns `(ROUTE117, (31,16), ['Marill'])`
   TODAY (`probe_slot_free_plan.py`). Marill learns Surf and Dive. So no new hunting ground is
   *required*; Spheal is only a quality upgrade (50%/L26-32 vs 10%/L13).
3. **‼ IF a new ground is ever added, it must NOT go in `TRAINING_GRASS`.** Measured with the real
   function: a `SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM (25,30) (26,32)` row makes it the **highest band
   in the table**, and `best_training_area` then flips for every team from ~L30 up:
   ```
   BEFORE  team L30/34/36/40/44/48 -> (ROUTE121, (44,14), (25,28))
   AFTER   team L30/34/36/40/44/48 -> (SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM, (25,30), (26,32))
   ```
   `TRAINING_GRASS` is primarily the **training-relocation** table, not an HM registry — so the row
   would send every post-Winona boss-prep relocation into a cave across the ocean, with **no
   `_training_area_heal_map` entry** and **no `NO_RETURN_GROUNDS` entry**. `AREA_PREREQ = "surf"`
   does not save it (`_training_area_allowed` passes once any mon knows Surf), and
   `_hm_hunting_grounds` never reads `AREA_PREREQ` at all — the guard would protect every consumer
   except the one it was added for. Use `HUNTING_GROUNDS` (catch-and-leave) or a new `HM_GROUNDS`.
4. **Prefer the ALREADY-PROVEN route over a new deposit.** `#24-pcoverflow` solved this exact
   problem for counters 90 lines away: `POKEBOT_BOX_OVERFLOW_CATCH` defaults ON and is live-proven,
   `counter_hunt.hunt` already returns `{"slot": None, "pid": ...}` for a boxed catch, and
   `withdraw_from_box` collects it at the next heal — **net-zero on party size**. The HM branch
   (`story_mode.py:2158`) still carries the `len(party) < 6` gate the counter branch dropped.

### If a `free_one_party_slot()` is ever built anyway — four things it MUST do
Recorded because I wrote a draft and reverted it; these are the defects the review found in it:
* **Raise on a non-Poké-Centre map.** `pc_trip`'s contract is *"PIGGYBACK, DO NOT DETOUR"*; the
  extracted block does `navigate_to(here, PC_STAND_TILE)` on **whatever map it is on**.
* **Honour `_hunted_counter_pids`.** That protection lives in `plan_deposits`, NOT in the block
  being extracted — batch8 threw away 2 of 5 hunted counters exactly this way.
* **Recompute `party_count`.** `early_game.py:4395` reuses the pre-deposit count as `before`, so
  `_story_spin`'s `len(party) > before` stop condition could never fire.
* **Protect the freshly caught learner.** `_only_hm_carrier` keys on **known moves**, so a Spheal is
  unprotected in the window between the catch and the teach — and it is the lowest-level mon, i.e.
  first in `find_dead_weight`. That is a catch → deposit → catch oscillation.

‼ **What the victim chooser gets RIGHT, so nobody re-derives it:** Zigzagoon L15 IS correctly spared
(sole Surf carrier), Sceptile too (sole Rock Smash + Strength carrier), and the pick is Skitty L17.
Measured, `probe_slot_free_plan.py`.

## ‼ OPEN ISSUES THAT LIVE IN THE ARCHIVE — do not conclude they are fixed

Two **OPEN, code-verified, unfixed** bugs were moved to `31-KNOWN-ISSUES-ARCHIVE.md` for the R3
line budget, not because they were resolved. A cold read of that file's header says "issues that
are now resolved live here", so they are listed here to stay findable:

* **KI-59** — `map_path` **INVERTS `Impassable *` directions**, over-blocking every such tile.
  ‼ **ARMED IN THE SEAFLOOR CAVERN**: 115 `Impassable *` tiles across Rooms 1-9. Fix it with an A/B
  on `SEAFLOOR_CAVERN_ROOM1` **before** that chapter exists. (Archive line ~481.)
* **KI-60** — `calculate_path` **never validates its SOURCE tile**, so a result is evidence about
  the DESTINATION only. Every probe in this project asserts the avatar's real position because of
  this. (Archive line ~513.)

## ‼‼ KI-69 — THE REGI ARC: the party order everyone "knows" is the RUBY/SAPPHIRE one (2026-08-12, decomp-verified, OPEN)

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

## KI-66 — the multi-battle hazard is BROADER than the faint chooser (2026-08-12, code-verified, OPEN)

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

## KI-67 — the chapter retry loop swallows the WHITEOUT ABORT (2026-08-12, ✅ CLOSED — original filing, kept for the diagnosis)

`StoryMode.on_whiteout` sets `set_story_abort(True)`; only `StoryMode.run` clears it.
`do_space_center_chapter` catches `BotModeError` — **including the abort raised by `_check_abort()`**
— and retries in place with the latch still set. Attempts 2 and 3 therefore raise instantly at the
first `_check_abort()` inside `_navigate_riding_out`, so **one whiteout consumes the entire retry
budget in a handful of frames** and the chapter reports three failures, two of them fabricated.

‼ **And the harness cannot see it**: `set_story_abort` appears **zero** times in `story_harness.py`,
so every driver's `on_whiteout` only increments a counter and `_check_abort()` is effectively dead
code under test. `SpaceCenter1Mode`'s docstring claims it "MIRRORS StoryMode's own choice" — it
mirrors `on_battle_started` and **not** `on_whiteout`. So every retry-path claim in these docstrings
is untested prose.

## KI-67 — the earlier 'production half fixed' write-up is SUPERSEDED (ARCHIVED)

Superseded in full by the '✅✅ KI-67 FULLY CLOSED' section below, which carries the driven
evidence. The archived text is kept only for its harness DESIGN NOTES (the four parts a driver
must mirror, and why half a mirror is worse than none) — see `31-KNOWN-ISSUES-ARCHIVE.md`.

## ✅✅ KI-67 FULLY CLOSED 2026-08-12 — the FIRST DRIVEN WHITEOUT RECOVERY IN THIS PROJECT

`StoryWhiteoutRecoveryMixin` (`tools/story-dev/story_harness.py`) gives a driver all four parts of
production's behaviour, and `SpaceCenter2Mode` uses it. **Driven both ways:**

| run | result |
|---|---|
| healthy, `--driver spacecenter2` | `PASS`, `whiteouts=0 recoveries=0`, frame-identical to before |
| **deliberate loss, `--inject-weak`** | `whiteouts=3 recoveries=3`, ends controllable at `MOSSDEEP_CITY (28,17)` |

‼ **THE FRAME DELTAS ARE THE PROOF, not the counts** — the count alone cannot tell the fixed code
from the broken code:
```
WHITEOUT #1  frame 3532810
WHITEOUT #2  frame 3540599   (+7,789)
WHITEOUT #3  frame 3547686   (+7,087)
```
**Broken = three attempts in a handful of frames after ONE whiteout. Fixed = each attempt costs
~7,000 frames and produces ITS OWN whiteout** — i.e. the bot really did walk back from the Pokémon
Center to Steven and fight again, three times. And the error it finally reported was a
**`StoryAbort`**, not the fabricated *"cannot reach Steven at (1,8)"* the laundering used to produce.
The ACCEPTANCE **FAIL** is correct: a lone Lv3 Poochyena genuinely cannot win that battle.

**Five defects in the mixin were found by an adversarial review BEFORE it was driven**, all fixed:
* `except BotModeError` was too narrow — **`PathFindingError` is a `RuntimeError`**, so a laundered
  abort would have escaped the recovery loop and been graded a genuine failure;
* **MRO silent-revert**: ten other drivers still define their own `on_whiteout`, and mixing this in
  without deleting theirs would leave the driver *looking* converted while never setting the latch.
  `__init_subclass__` now REFUSES that at class-creation time (proved dynamically in the repro);
* `self.tag` was dereferenced on the *listener's* stack, where an `AttributeError` kills the run
  before any RESULT line — now `getattr`;
* the recovery budget compared a never-reset CLASS counter to a per-call limit — now a delta;
* falling out of the loop returned `None` = **success** — the silent-green pattern; now returns the
  last error.

‼ **AND A REAL BLOCKER THE REVIEW CAUGHT: an injected run could have overwritten a committed
anchor.** `--inject-weak` replaces the party with a lone Lv3 Poochyena; had such a run reached the
completion var it would have written `post_space_center.ss1` — a fixture `--driver spacecenter` and
`FIXTURES.md5` depend on — with a joke party, **silently**. Anchor capture now refuses whenever the
run injected a party. (Verified after the fact: the injected runs captured nothing; the anchor on
disk came from the healthy run.)

**Also fixed in PRODUCTION, not just the harness:** `StoryMode.run`'s `recoveries > 40` exit raised
**without clearing the process-global latch**, so whatever ran next would abort at its first
`_check_abort()` for no visible reason. The harness must not be stricter than the thing it mirrors.

**Superseded — the old "still open" text follows for its design notes:**

⛔ **STILL OPEN — THE DRIVEN HALF, AND DO NOT HALF-DO IT.** `set_story_abort` still appears **zero**
times in `story_harness.py`. ‼ **Both reviews independently warned that adding the latch to drivers
WITHOUT also mirroring `run()`'s clear-and-retry loop makes it a ONE-WAY DOOR** — the latch is
process-global and nothing else clears it, so every later `_check_abort()` would raise forever and
currently-passing drivers would go red over correct production code (`--driver spacecenter`,
`--driver mossdeeptravel`; anchors would stop refreshing). **So it is all four or nothing:**
`on_whiteout` sets the latch AND `_whiteout_pending`; the driver wraps the chapter in a
clear-and-retry loop; the whiteout branch clears the latch BEFORE navigating and calls
`exit_building_after_whiteout()`; and the RESULT line reports the recovery count. Cheapest safe
shape is ONE shared mixin the eleven drivers inherit, so it cannot drift again.
**Then prove it with `--driver spacecenter2 --inject-weak`** from the 2F anchor (past the grunts,
at Steven) — a 1-mon party is legal (`GetMinBattleEntries()` is 1) and loses fast, and
`Cmd_checkteamslost` sums HP over the player's picks only. ‼ Assert `_whiteout_pending` in the log:
the whole severity assessment rests on it being True when the error arrives, and that was traced
statically, never run.

**Also still open (pre-existing, adjacent):** the latch is process-global and `run()` does not clear
it in a `finally`, so an exit via `derails > 4` or `recoveries > 40` leaves it set for whatever runs
next. Harmless today only because nothing else sets it — it goes live the moment the harness mirror
lands. And ~48 further swallow sites remain in `early_game.py`; most self-heal because the next
abort-aware call re-raises, but they should get the same one-line guard, enforced by an AST check
rather than by prose.

## KI-65 — the HM-refusal re-pick has NEVER executed: `party_index` is unbound there (2026-08-12, code-verified, OPEN)

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
