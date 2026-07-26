# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-07-26 (survival mode; `#24-movelearn-recovery` closed — see "YOU ARE HERE")

### ⭐⭐⭐ 2026-07-24 — KI-15 FIXED (3 proven fixes) + OVERNIGHT CHAPTER LOOP RUNNING
**KI-15 is fixed** (see 05-KNOWN-ISSUES KI-15 + changelog for the full story): (1)
`navigate_to` no-progress bail (`NavigationStuckError`), (2) the cutscene rider's
450-frame B→single-A escalation for the stale post-battle battle-text wedge, (3) the
StoryMode run-loop 240-frame persistence nudge. Each proven on a captured state
(`saves/ki15_gotaway_wedge.ss1`, `saves/ki15_nurse_wedge.ss1`); museum-greeter
regression probe green; faithful goods_recovered runs self-recover where they used to
hang terminally. ‼ TWO intermediate designs FAILED and taught lessons (08-MISTAKES
2026-07-24): the wedge is reader-indistinguishable from a dialogue tail (discriminate
by RESPONSE TO INPUT + persistence, never by readers), and any auto-unstick press must
be sustained-signature + single-press + cooldown, or it A-mashes NPC dialogues.
New probe tools: probe_stuck_state.py / probe_press_variants.py / probe_ride_fixed.py.

**OVERNIGHT DIRECTIVE (user, 2026-07-24, verbatim intent):** work through ALL remaining
chapters until the story bot is complete; harden + fill in the chapter skeleton; fix
errors along the way, but after a bunch of failed fix retries MOVE ON to the next
chapter; use Gemini assistants (gemini_relay.py) for research gaps.

**OVERNIGHT PROGRESS (as of ~02:30):**
- **Ch12 BUILT + WIRED + committed (`f5aba6d8`)** — Segments 12a/b/c: direct
  Lavaridge→Petalburg route (Fiery-Path note was WRONG — see changelog), Rusturf
  Wanda-wall smashes, Petalburg gym SIGN-script doors (never walk into them!),
  Norman challenge, fully-automatic Surf handoff, teach Surf. Mechanically validated
  live to Norman's room (run9: 500k frames, 0 hang / 0 Manual; one whiteout →
  recovery + boss-training kicked in correctly). The Norman WIN is level-bound on
  the thin flannery_done team — a 2M-frame run is grinding it out in the background
  (ch12_run10_long.log). When it lands, capture `norman_done.ss1`/`surf_taught`
  checkpoint + validate 12c, then update END_MARKERS batches.
- **Fresh batch (3M frames, 5 lanes): 3/5 reached HEAT BADGE organically, 0 Manual**
  (KI-15 fix class held); 2 lanes → the NEW **KI-17** (after-faint reshow DMA race —
  the original "Shedinja chooser" bug, real all along; 2 states captured, Gemini
  decomp analysis archived, sweep hardened; validate on the next batch).
- **Ch13a-e SKELETON built + wired + committed (`4b626c91`)** — Surf arc: travel to
  Fortree (Surf crossing planner-native), Weather Institute (Shelly), Route 119
  rival → HM02 Fly, Devon Scope (Steven (13,15)/Kecleon (12,16) on R120; city
  Kecleon (25,8)), Fortree Gym (turnstile push-solve) → Winona. Flags audited
  (phantoms dodged: use HIDE_ROUTE_119_RIVAL / RECEIVED_HM_FLY). ⚠ ALL of Ch13 is
  first-run-validate — expect a Ch12-style iteration burst when a post-Surf save
  exists.
- **§Ch14 SPEC drafted** (Route 121 → Mt. Pyre exterior → Magma Emblem [KEY ITEM,
  no flag — gate on the BAG] → Jagged Pass hideout door → Maxie; flags audited).
- **Norman balance:** the flannery_done team (no Fighting answer) didn't break
  Slaking in 2M frames (6 attempts, boss-training cycled correctly, 0 hangs) —
  fresh teams carry Combusken; the win is expected organically in the big batch.
- **★ NORMAN BEATEN ORGANICALLY (batch 20260724-070630 lane 1, Blaziken team)** —
  Ch12 validated end-to-end; **`saves/norman_done.ss1`** captured+verified (BADGE05 +
  RECEIVED_HM_SURF, controllable). The lane's one failure (the 12c Surf-teach hunt
  picking warp-locked Route 117 grounds) is FIXED (reachable-grounds picker + Route
  102 (9,2) promoted into TRAINING_GRASS). Batch: 1× Norman+Surf, 2× healthy
  budget-INCOMPLETE, 2× pre-jolt-fix wedges (fixes landed mid-batch, 54f9537e).
- **Ch13a-c VALIDATED (11 iterations from norman_done, commit e043cbaf):** teach
  Surf → Surf-cross Route 118 → Weather Institute (Shelly) → **HM02 Fly** → reaches
  Fortree/Route 120. Six general engine fixes fell out (all in the playbook table):
  phantom-escape in `_ride_out_all_scenes`, choice-aware scene rides, `_hold_walk_route`
  (bridges the planner can't cross), coord-trigger targeting, `_clear_stale_battle_message`,
  Fortree-side travel `order` ranking.
- **Ch13d Devon Scope WORKS end-to-end** (real path, run 13, commit 2bdd526e): the
  Route 120 north-bridge strand is solved (`_leave_route120_north_bridge`: Steven's
  scene isolates the avatar at (13,16) — held Up→(13,15), Left→(5,15) escapes; called
  from 3 resume paths). The run crossed Route 120, flushed the city Kecleon, healed,
  and reached the Fortree gym door. Checkpoint `saves/devon_scope_got.ss1`.
- **✅ Ch13e "tree-bridge blocker" was NEVER REAL — note REFUTED and retired (2026-07-24.)**
  The old claim here said the gym door (22,11) is reachable only from (21,11)/(22,12) and
  blamed planner-blind elevation walkways (the Route-119/120 class). Probed live
  (`tools/story-dev/probe_route120_to_fortree.py` §6/7): (22,11) is a correctly-typed
  `Door Warp` → FORTREE_CITY_GYM, landing (15,24), matching the code's own docstring. Its
  ONLY blocker is the transient story flag **969 HIDE_FORTREE_CITY_KECLEON** — the Kecleon
  sits in the single chokepoint tile (25,8) between the walkway and the door cluster. With
  flag 969 forced True (reader-level fault injection), (22,11) plans from (25,7) in 9
  waypoints, from the plaza (5,6) in 38, and from ROUTE120 (5,15) in 115 — i.e. reachable
  from essentially anywhere, no held-walk route needed. `get_devon_scope` already flushes
  that exact Kecleon before `do_fortree_gym` runs, so the real playthrough sets the flag
  first. Control: (22,12) is fully walkable both before and after injection, proving the
  pre-flush FAIL came from the one gated chokepoint and not a second broken tile.
  ‼ The stale note was written from observing the PRE-FLUSH blocked state and mistaking a
  story-sequenced flag for a map/planner limitation. **Residual debt:** this is a strong
  fault-injection proof, not a live post-flush save — capture a checkpoint keyed on flag
  969 and re-run §6/7 without injection to close it (punch-list `#24-fortreelive`).
  NEXT: 13e Winona (turnstile gym, built, untested) → BADGE06. Then Ch14 (§Ch14 spec
  ready). Milestones:
  `norman_done.ss1` (clean, BADGE05+Surf), `devon_scope_got.ss1` (Scope, on Route 120).
- **KNOWN OPEN:** KI-17 (after-faint reshow DMA freeze — sweep hardened per Gemini's
  decomp analysis, validate next batch); the fresh 5M batch was 0/5-frontier but all
  failures were the freeze family / pre-jolt-fix wedges (fixes landed), not new breakage.

> **NEW AGENT: read `14-AGENT-PLAYBOOK.md` right after this file.** It is the
> accumulated craft (harness, debugging method, story-mapping, faithfulness rules, bug
> patterns) — use it to build faster and prove every fix.

### ⭐⭐⭐⭐⭐ 2026-07-23 — **CH11d COMPLETE: HEAT BADGE WON** (frontier = Ch12)
The Lavaridge trapdoor maze is SOLVED and Segment 11d is WIRED. `do_lavaridge_gym` no
longer guesses: it scans both floors for holes (1F behaviour 104), geysers (B1F
behaviour 41) and **jump-south ledges (behaviour 59)**, builds the chamber graph and
BFSes it from wherever the player actually is. The ledges were the whole bug — under
plain collision the floors look like sealed chambers with no exits, which is why five
prior runs oscillated on inert tiles. Canonical chain = 4 falls: (8,9), (0,10), (2,3),
(10,6). **Validated (ch11d_run11): 0 derails, Flannery beaten, BADGE04_GET, clean
content-end; the run whited out mid-way, self-recovered and re-solved the maze move for
move — an unplanned determinism proof.** Checkpoint `saves/flannery_done.ss1`.
Also fixed: a failed leg used to B-ride a nonexistent cutscene (18k-frame wedge, run 10)
— recovery is now script-aware and stall-budgeted. Details: changelog + 08-MISTAKES
(two entries) + 06-DECISIONS + design §Ch11d (full mechanics table).
⚠ Segment 11d does NOT pre-grind: a two-way sweep proved NO training grass is reachable
from Lavaridge (Jagged Pass one-way; Route 112 lower has no return). L29-31 wins but is
marginal → #24-trainmap.

**✅ FIXED (user's real-HW log 2026-07-23, `Story_DEBUG__RESET...062055.log`) — both
reported bugs, reproduced in-harness then proven:**
1. **Slateport museum greeter loop.** Root cause: "A" is not "advance text" — beside an
   NPC it STARTS a conversation, so A-riding a plain message re-opened it forever (the
   fee was already paid; the text was "Please enjoy yourself."). New `_dialogue_button()`
   presses A only while a Yes/No/multichoice is on screen, B otherwise; ride-outs also no
   longer mash during a dialogue's non-controllable tail. Closes the whole class.
2. **Dewford detour to the dock.** Briney is STATIC at (12,9), but the code used the
   wandering-NPC helper whose known-spot path is a GREEDY stepper — it dead-ended on the
   y=10 wall band and wandered into the south-east pocket. Now walks straight to (11,9)
   with the pathfinder and talks; the helper also tries the pathfinder before greedy
   stepping. Dock leg is now a direct 10-tile walk.
Proof: `museumprobe2.py` (repro → clean pass) + a 250k-frame `brawly_done.ss1` run
through Dewford gym → sail → Slateport → museum delivered → Route 110 rival → Mauville
prep, still in Story mode at the budget end, 1 self-recovered derail.
New tool: `tools/story-dev/mapfacts.py` (warps + objects + passability grid for any map).
⚠ Sandbox only — not promoted to custom (standing rule: promote on the user's explicit OK).

**ALSO LANDED 2026-07-23 (user directives, built during their fresh-start test run):**
- **"Show Coords" toggle** — Play tab → CONTROLS → "Debug" row. Live tile + area name +
  map group/number + facing, for reporting pathing coordinates during development.
  Off by default, display-only, fully guarded. ⚠ **Compile-verified but NOT clicked live**
  (the user's test was running) — confirm on screen.
- **`sandbox-pokebot/profiles/GEMINI-FULLGAME-RESEARCH.md`** — a Deep Research commission
  for a whole-game bot-grade walkthrough, to be re-run periodically so mapping detail lands
  ahead of the build frontier. Grade the result with the procedure in that file (including
  a known-answer control from an already-built chapter) and record it in its run log.

**2026-07-23 (day, cont.) — user's fresh-start test graded + HM-learner fix + Gemini full-game:**
- User's fresh run reached Mauville/Rock Smash cleanly; their report exposed the Ch10b
  design flaw: the HM mule was picked by LEVEL, not compatibility (party menu loops on
  NOT ABLE when the top mon can't learn it — e.g. any Swellow-led party). FIXED +
  A/B-PROVEN: `hm_learner_slot` (compatible pick) + `ensure_hm_learner` (derives hunting
  grounds from ROM encounter tables × learnsets, provisions balls, catches a learner via
  the new HM_CATCH_TARGET_DEX on-sight catch branch) + `teach_hm_move` truthful
  compat guard. Proof: repro_hm_learner.py + `--driver hmtest` (fault-injected party →
  hunted Rt 117 → caught Poochyena → taught Rock Smash, PASS). Watch out for the
  function-local-import shadowing lesson in 08-MISTAKES.
- **Gemini full-game Deep Research response GRADED B+** (run log + detail in
  profiles/GEMINI-FULLGAME-RESEARCH.md): step order/rosters/puzzle-rules HIGH (Sky
  Pillar first-visit-solid-floors trap, Fortree turnstile persistence, Aqua warp graph,
  Seafloor Sokoban reset, Sootopolis Hamiltonian ice); identifiers MEDIUM — several
  phantom flags, audit_flag_names.py is mandatory before wiring any of them. Leads
  folded into design §Ch12+ (⚠ unverified-external). PROMPT 2 (early-game check =
  the known-answer control) not yet relayed.
- New punch-list futures from the user: #24-provisions (potions/strategic healing),
  #24-tms, #24-pokeprofiles (per-species battle profiles via batched overnight research
  + Gemini cross-referencing), #24-economy. All noted for later — not next work.

**PENDING (2026-07-23):** (1) the user's fresh-start test run — log incoming, grade it
when it arrives; (2) the full-game PROMPT 2 early-game pass is still unrelayed.
**DONE 2026-07-23 (afternoon):** the #24-pokeprofiles Batch-1 response is GRADED (B:
TM-compat 98%, levels 42% — never trust research levels; grading + raw archive in
profiles/GEMINI-POKEPROFILES-*.md, machine check = tools/story-dev/grade_pokeprofiles.py)
and the **Gemini API relay is BUILT + verified** (tools/story-dev/gemini_relay.py; key
GITIGNORED at sandbox-pokebot/profiles/gemini.key — never commit it; usage + day-one
rules in 15-ESCALATION-RESEARCH.md).

**BUILT 2026-07-23 (evening, user approved "proceed"):** the whole boss-training
discussion landed, each piece proven (changelog has the details + proofs):
KI-14 fixed (menu-free close + menu-aware cutscene rider; teach-to-Route-113 clean,
museum repro still clean) - matchup-aware after-faint chooser (A/B: no more
Thunderbolt-food replacements) - BOSS-TRAINING MODE (KO telemetry from
gBattleResults; light top-up + boss re-attempts when grass is fodder; 0-KO fallback;
grass-less bosses skip the grind). Punch list: +#24-trainersweep (one-time trainer
sweep before grinding; Match Call rematches later - NOT built yet).
NEXT VALIDATION: a fresh batch (or the user's next real-HW run) through Wattson to
watch boss-training fire organically; then Ch12.

**BUILT 2026-07-23 (night, user approved + defensive backup):** the SWEEPER-SUFFICIENCY
GATE (see changelog for full detail + proofs). Revert point if anything goes wrong:
tag `backup-pre-sufficiency-2026-07-23` (pushed) —
`git checkout backup-pre-sufficiency-2026-07-23 -- sandbox-pokebot/plugins/custom_modes/story_mode.py`.
Gate: sufficient sweeper (ace-pair score + stat-fit + defensive veto) → skip team prep;
near-miss / imminent-evolution (Torchic→Combusken) → targeted top-up of ONE mon;
no sweeper → band prep unchanged; losses ≥2 → reactive layer owns it. Proven by
repro_sufficiency.py (6 scenarios) + a live rustboro.ss1 run (targeted top-up →
ROXANNE BEATEN → into Ch5). gemini_relay default is now gemini-3.1-pro-preview.
DEFERRED (my call, user offered now-or-later): the "company-style" multi-agent Gemini
orchestration refinement — better done overnight/later; noted on the punch list.

**FIXED 2026-07-23 (late night, user's paired logs):** the Route 111 first-rock hang
(the batch-8 morning-queue wedge, now closed): `_smash_rock` is idempotent and judged
by the rock OBJECT disappearing (Rock Smash spawns wild battles — the script context
can read active forever afterward), plus a phantom-script escape in the cutscene rider
(10s of playable+quiet+script-active = parked context, scene over). Proofs:
repro_phantom_script.py A/B + live rocksmash_taught run through both rocks to Route
113. Log identification for the user: 56c1baf9 (12:24) = mid-Wattson training;
478c2506 (13:41) = the fresh run with the hang. Punch list: +#24-hm-multi.

**BUILT 2026-07-23 (late night, user directive): milestone-state sharing.** The repo's
checkpoint library is now a GUI feature: "Load Milestone State" (dashboard GAME MENU
card + both Emulator menus) lists the story-ordered, chapter-tagged checkpoints from
tools/story-dev/saves and loads them like save states (registry:
modules/story_milestones.py — curated table + auto-labeled fallback; safety copy about
the NICK test playthrough + use-a-test-profile + pair with resume-anywhere Story modes,
never DEBUG-RESET). saves/user-reports/ added for the user's bug-capture states.
⚠ Compile/import-verified, NOT yet clicked live (user's test was running) — confirm
the popup renders next GUI session.

**FIXED 2026-07-23 (user's DEBUG run from a personal save):** the Mt. Chimney cable
car wedge + a structural stranding, both proven end-to-end (changelog for detail):
(1) boarding approached the wrong tile (attendant is (6,6), approach (6,7) — was (6,8));
now `ride_cable_car_to_summit()` with a retry; (2) a whiteout on a Jagged Pass trainer
respawns below the one-way descent and the cable-car segment was Magma-gated →
permanent stranding + a guard that falsely passed. Now `do_jagged_descent` re-rides the
cable car when stranded below, and the 11c guard checks arrival-in-Lavaridge. One run
meteorfalls_done → cable car → Maxie → whiteout → cable-car RE-RIDE → Lavaridge →
Flannery → HEAT BADGE, 0 derails. Also validated this session: the rock-smash fix
(taught to Mightyena, no hang) and the sufficiency gate, both from the user's earlier logs.

**BUILT 2026-07-23 (user's milestone-testing feedback):** three fixes, all proven
(changelog for detail); revert point tag `backup-pre-resume-robustness-2026-07-23`.
(1) Rock Smash field use 6x faster (was gating the YES-answer A on "script inactive",
but the prompt IS a script) — ~20s for both Route 111 rocks now.
(2) RESUME-FROM-ANYWHERE: `normalize_to_overworld()` at `_play` start B-presses any
entry state (menu/dialogue/battle/cutscene) to a clean controllable overworld before
segments navigate; proven to heal the actual menu-saved milestone (BAG_MENU -> OVERWORLD
in 204 frames) + a 5-state fault-injected A/B.
(3) `rocksmash_taught.ss1` milestone regenerated in a clean overworld (was saved in the
bag menu); other Ch10 checkpoints audited clean. `regen_rocksmash_taught.py` is the
template for re-capturing any checkpoint safely.
NOTE for the future: the user asked to keep extending resume robustness "for all
situations" — the normalizer covers the common ones; deepen as new edge states appear.

**KI-16 FIXED + VALIDATED 2026-07-23:** the wattson_done deterministic wedge was
`_smash_rock` returning before `EventScript_SmashRock`'s WaitForMovementFinish completed —
the next navigation cancelled the crumble movement and stranded the script. Fix: wait for
the field script to clear before returning. The wattson_done batch that was 5/5 hangs is
now **5/5 HEAT BADGE, 0 hangs/derails/whiteouts.** wattson_done is a good milestone again.
**KI-15 RE-DIAGNOSED 2026-07-23 (still open, ~1/5):** ‼ it is NOT an after-faint party-menu
hang — that was a MISDIAGNOSIS never supported by any log (`grep -r "SHEDINJA fainted"` = 0
hits; the after-faint sweep is proven ROBUST). The REAL bug (3 confirmed 20k hangs) is a
**post-battle STORY-RESUME hang**: an inline battle interrupts story navigation/a scripted
scene and the flow can't resume (stale `cb=ReturnFromBattleToOverworld` +
`BattleScript_PayDayMoneyAndPickUpItems`). Two forms: `_wait_until_cutscene_over` loops
(RUSTBORO), and `navigate_to` bounces `(5,6)↔(5,7)` (ROUTE 104). Env-gated `KI15_TRACE`
instrumentation is in `_wait_until_cutscene_over`; faithful `--driver story` runs ride the
scene cleanly (hang needs the rare battle-interrupt race). Full diagnosis + next steps in
05-KNOWN-ISSUES KI-15. Do NOT patch the battle handler for this.

**VALIDATION SWEEP DONE 2026-07-23 (user-requested 5 fresh + 5 milestone):**
Pass 1 (5 fresh→HEAT BADGE): 4/5 clean (3 frontier + 1 budget-INCOMPLETE), 1 real hang
(after-faint chooser, KI-15). Pass 2 (5 from rocksmash_taught): **5/5 HEAT BADGE, 0
hangs/derails/whiteouts** — the recent frontier work is validated solid. Two intermittent
bugs logged with repros: KI-15 (after-faint chooser + 1-HP Shedinja) and KI-16
(wattson_done deterministic navigator wedge — use rocksmash_taught for milestone tests,
not wattson_done). Neither guess-patched (critical code, need validated repros first).

**IN PROGRESS — Ch12 BUILD STARTED 2026-07-23 (route leg, WIP/unwired):**
`travel_lavaridge_to_petalburg` exists in early_game.py but is **NOT wired into _play**
(frontier = Flannery/HEAT BADGE, untouched). Progress: the Route 112 ledge crossing works
(Lavaridge→Route111(13,90) reaches the desert edge). **BLOCKER FOUND + documented:** Route
111's middle is the Go-Goggles DESERT — it blocks N↔S, so the Lavaridge→Mauville leg must
go via the FIERY PATH (reverse Ch10 `travel_to_fallarbor`: Route112 → Fiery Path → Route112
→ Route111-south past the smashed rocks → Mauville). RESUME HERE: finish that leg by
mirroring travel_to_fallarbor's Fiery-Path+rock legs, then validate the Mauville→Petalburg
tiles (currently guesses), then build do_petalburg_gym + the Surf handoff (tasks #5/#6),
then wire Segment 12 + livetest END_MARKERS. Backup tag `backup-pre-ch12-2026-07-23`.
Recon tools: route_probe_ch12.py, route_chain_ch12.py, petalburg_gym_probe.py.

**(reference) Ch12 DEEP-MAP + build plan** — §Ch12 build spec in 12-STORYMODE-DESIGN
(now corrected for the Fiery-Path routing). 
**NEXT: BUILD Ch12 — DEEP-MAPPED 2026-07-23, ready.** Spec in 12-STORYMODE-DESIGN §Ch12
(archived research tools/story-dev/research-gemini-ch12-2026-07-23.md). Key findings,
verified this session: **Go-Goggles/Route 111 desert are OPTIONAL — SKIP them** (Route 111
connections probed: the desert is never on the Lavaridge→Mauville→Petalburg path). Route =
long overland backtrack (Lavaridge → Rt112 ledges → Rt111 S → Mauville → Rt117 → Verdanturf
→ Rusturf Tunnel → Rt116 → Rustboro → Rt104 → Petalburg Woods → Petalburg). Gym = the tall
9×112 PETALBURG_CITY_GYM, VAR_PETALBURG_GYM_STATE-gated doors (runtime-modified, Mauville
class → LIVE-SOLVE), Norman at top (4,2), 8 trainer tiers. Beat Norman (Spinda27/Vigoroth27/
Linoone29/Slaking31 ⚠, TRUANT ace) → BADGE05 + TM42 → **step DOWN** → Wally's dad → warp to
Wally's house → HM03 Surf (RECEIVED_HM_SURF) → teach it. Build as progress-gated legs +
a do_petalburg_gym live-solver; validate connections + the door path + Norman team at build.
Start from `flannery_done.ss1`. Update livetest END_MARKERS when the frontier moves.

### (superseded) OVERNIGHT LOOP INSTRUCTIONS — kept for the resume ritual
The user commissioned an unattended overnight loop: (1) 5-run fresh batches until ALL
FIVE reach the Dynamo Badge content-end clean (no Manual/hang/crash; self-recovered
derails OK) — fix what fails, rerun; (2) then deep-map the next chunk (Ch10 first),
sanity-check (audit_flag_names + two-way pathability sweeps + decomp validation),
build it, test along the way; (3) any question needing Gemini goes to
`sandbox-pokebot/profiles/GEMINI-PROMPTS.md` (append-only, never blocks — build with
the decomp-verified best answer + a marked assumption); (4) repeat chapter by chapter,
building the skeleton as deep into the game as possible. Batches ~25-40 min each;
mapping/doc work interleaves during runs (no code edits mid-batch). If this session
ends mid-loop, resume the loop from this note + the newest livetest-runs batch.
Current: batch 20260722-204645 running (5 lanes, fresh→badge, with the cave-heal +
mapped-index fixes 55e27eab). Watch item: Rustboro rival staging non-engagement (1/5
in the prior batch).

### ⭐⭐⭐⭐⭐ Session 2026-07-22 (Fable 5, afternoon→evening) — **CHAPTER 9 COMPLETE: DYNAMO BADGE WON**
**Story frontier = Ch10.** Run 14 played stern_done.ss1 → rival → Wally → prep-training
(Route 117 (31,16), band 20-24, two evolutions: Swellow + Mightyena) → live-grid maze
solve → **Wattson BEATEN** → `wattson_done.ss1` (verified: BADGE03_GET +
DEFEATED_MAUVILLE_GYM + DEFEATED_WALLY_MAUVILLE) → clean content-end. KI-13 closed by:
the 0-power move-learn guard (Mud-slap preserved), Segment 9c prep, the two-way-swept
training tile, and `_ride_out_all_scenes` (aftermath chains). Interrupt hardening from
the user's real-HW log: `ensure_facing_direction` rides out field scripts (85k-frame
wedge fixed, regression-proven) + a GLOBAL StoryMode no-progress watchdog (18k frames of
stasis → self-derail into recovery). **NEXT: Ch10 (Rock Smash from Mauville SE house →
Route 111/112 → Fiery Path → Fallarbor)** — run /validate-docs + audit_flag_names.py
first; note the Route 110/117 pathability prevention rule (two-way sweep FROM THE REAL
ENTRY TILE) before picking any grind tile.
**Five proven fixes this session** (each with repro + proof; changelog has details):
1. Phantom post-evolution script suppressed wild encounters → training spin starved
   (batch run05) → `_story_spin` B-rides leftover scenes on its no-progress bail.
2. After-faint party menu deadlock (blind A-spam lockstep; slots 0+1 both fainted) →
   STATE-AWARE sweep in `handle_fainted_pokemon` + dispatch recognizes
   `BattleScript_FaintedMonTryChoose`. Proven live on the wedge state (~128 frames).
3. Ch9a guard keyed on a PHANTOM flag ("DEFEATED_RIVAL_ROUTE_110" doesn't exist!) →
   decomp-true `route110_rival_beaten()` (VAR_ROUTE110_STATE ≥ 1, tear-resistant);
   `_done()` now raises on unknown names; NEW `tools/story-dev/audit_flag_names.py`.
4. **THE BIG ONE:** Mauville's barriers exist only in the LIVE grid (gBackupMapLayout);
   `get_map_data`/`calculate_path` read the ROM's STATIC layout — blind to setmetatile.
   `do_mauville_gym` now reads the live grid, learns both barrier configs, BFS-plans
   across toggles, walks legs judged by ARRIVAL. (Applies to every runtime-modified map
   ahead: Trick House, ice floors, Sky Pillar.)
5. Harness: NO-PROGRESS milestones dump the generator call stack; player position is in
   the progress signature (an exploring solver is not a hang).
**Assets:** `saves/mauville_wedge.ss1` (mid-maze repro), ch9_run*.log series,
livetest batch REPORT.md (runs 01-04 clean/budget-bound; run05 = fix #1's repro).
**Batch verdict (20260722-134735):** 4× zero-error budget-bound INCOMPLETE + 1 organic
stall (fixed). Report in `tools/story-dev/livetest-runs/20260722-134735/REPORT.md`.

### ⭐⭐ Session 2026-07-22 (late night) — KI-12 battle-chain fixed + Gemini PoC GRADED + Ch9 validated
- **KI-12 (user's gym party-menu hang + "double battle bug") FIXED as a 3-bug chain** via a
  purpose-built repro (`--inject-faintbench`): bounded after-faint party menu; chooser-None
  fallback (any living mon beats crashing); the double-battle `reason` TypeError fixed +
  story strategy now ATTACK-THROUGHS trainer doubles. Key insight: Emerald fires TRUE
  double battles when two trainers sight you at once (why these clustered at gyms). Proof:
  the repro plays the double to a natural whiteout → story recovery. Details: changelog +
  08-MISTAKES (one-repro-three-bugs lesson).
- **Gemini external-research PoC: GRADE = HIGH.** Its Ch9 research was precise + cited,
  matched every decomp spot-check (Route 110 rival triggers, Wally flags/Scott sequence),
  and CORRECTED our own doc (Gabby&Ty's first battle is Route 111, not Slateport).
  VERDICT: promote to the REGULAR pre-build validation step (/validate-docs source 3 via
  the primer); deep mid-build escalation stays rare. Gemini-via-API documented in
  15-ESCALATION-RESEARCH as the future automation path (needs the user's key, gitignored).
- **§Ch9 written into the design doc** (validated sequencing, ✓-tagged by source):
  Route 110 rival choke-point (⚠ probe VAR_ROUTE110_STATE in stern_done first) → Mauville
  Wally-gates-the-gym → switch-puzzle gym → Wattson (Voltorb20/Electrike20/Magneton22/
  Manectric24) → BADGE03. **NEXT: build Ch9 from §Ch9** (probe the ⚠ items first).

### ⭐ CH8b DONE — Devon Goods → Capt. Stern (KI-11 resolved) — 2026-07-22
`deliver_devon_goods_to_stern` BUILT + WIRED + VALIDATED: full run slateport.ss1 → Stern's
Shipyard → **talk to Dock** (the missing story step — sets FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA,
clearing the grunt-sealed museum; user-supplied + decomp-confirmed) → museum → ¥50 fee → 2F
→ Stern (13,6) → two grunt battles WON → Archie → `DELIVERED_DEVON_GOODS` (+ scene heals) →
clean content-end. Checkpoint `stern_done.ss1` (verified: DELIVERED + Aqua-cleared). KI-11 was
a DOC/sequencing gap → the new **/validate-docs** process exists to catch this class going
forward. **Frontier now = Ch9 (Route 110 → Mauville → Wattson); run /validate-docs on §Ch9
before building.** Also open from the batch sweep: #24-evo-trainstall (evolve-mid-training
hang, repro `saves/evostall.ss1`) + #24-freshbatch-rustboro. Minor: an 8000-frame cutscene-
wait derail recovers during the museum approach (non-fatal; tighten later).

### ⭐⭐⭐⭐ Session 2026-07-22 (Fable 5, night) — SHINY ALWAYS-CATCH ✅ + dock-stall fix ✅ + DEBUG modes ✅ (SANDBOX, pushed)
- **SHINY = ALWAYS CATCH implemented + proven** (the user's directive, done first): shiny
  branch now FIRST in `on_battle_started` → `StoryShinyCatchStrategy` (catches with any
  usable ball — owned species/full party/any stage; out-of-balls mid-battle → fights
  through; zero balls / tutorial → fight-through). Proofs: `repro_shiny_noballs.py` A/B
  (parent flees / shiny fights on the same input) + `--driver shinytest` fault-injection
  (forced-shiny wild: 3 balls thrown → CAUGHT, with team-catch gating forced off).
- **Real-HW dock stall FIXED** (user's log: derail-loop at Dewford (11,9) on the open
  post-sail Letter-reminder msgbox): both sail legs + the derail recovery now B-ride any
  active script before waiting for control.
- **New Run-tab modes**: "Story (DEBUG)" (debug logger on, resume-anywhere) and "Story
  (DEBUG - RESET)" (debug logger + hard reset + forced NEW GAME; ⚠ the save-present menu
  branch still wants one real-profile validation — the harness profile has no in-game save).
- **FULL-ARC REGRESSION GREEN:** one story run post_rival.ss1 → sail → Letter → Brawly →
  sail → Slateport PC, ~75k frames, 0 derails/whiteouts — proves the dock fix end-to-end
  and that the shiny reorder didn't disturb normal battle routing.
- Punch list: +#24-interrupt (interruption intelligence), +#24-movelock (Disable/Encore/
  Taunt-aware move choice) — user's slate-for-later items.
- **REAL-HW TRIPLE-LOG REVIEW (user's 2nd-PC session):** DEBUG-RESET's forced-NEW-GAME-
  over-existing-save branch VALIDATED on a real profile (fresh run then played clean
  through Roxanne→PokéNav; abrupt log end = the user's SYSTEM crash mid Match-Call
  tutorial, no bot stall dumps). A second run validated the ENTIRE Ch5c→8a arc on real
  HW (rival→Briney ambush→sail→letter→Brawly→Slateport, 0 derails). Finding fixed:
  watchdog's `_SELF_RECOVERING_MODES` exact-name check missed the DEBUG variants
  (spurious restart after the intentional content-end Manual + save-state reloads
  silently re-armed) → `_is_self_recovering` prefix matcher, A/B-proven.
- **NEW: "Conduct Live Tests" capability** (`/livetest`, `tools/story-dev/livetest.py`):
  N-run batch sweeps (fresh→frontier or scoped from any checkpoint) in isolated
  parallel lane profiles + auto summaries → a LIVE TEST REPORT (frequency + context
  signature + universal-bug vs nuanced-situation triage) reviewed WITH the user before
  fixes. ‼ Keep `END_MARKERS` in livetest.py in sync with the story's content-end
  message whenever the frontier moves. Never run lanes while the user live-tests.

### ⭐⭐⭐ Session 2026-07-22 (Fable 5, latest) — CHAPTER 8a DONE: the bot reaches SLATEPORT (SANDBOX, pushed)
- **`sail_to_slateport()` BUILT + VALIDATED (0 derails)**: `brawly_done.ss1` → gym exit →
  Dewford heal → dock Briney (Up×1→A on his Cancel-defaulted multichoice — the stock helper
  would wrap onto Petalburg) → sail → Route 109 → Slateport → PC heal → clean stop.
  Checkpoint **`tools/story-dev/saves/slateport.ss1`** (Slateport (19,20), healed,
  `DELIVERED_DEVON_GOODS=False` = the Ch8b anchor). Two new engine rules learned + logged
  (playbook §7): object events are CAMERA-LOADED (use `approach_hint` on town-sized maps),
  and `multichoicedefault` menus need explicit cursor moves.
- **NEXT: Ch8b — Devon Goods → Capt. Stern.** Read the SlateportCity + OceanicMuseum decomp
  first (beat chain: Stern hunt → museum entry (fee?) → 2 Aqua grunt fights → Archie scene →
  `DELIVERED_DEVON_GOODS`). ‼ Gabby&Ty DOUBLE battle at (28,14)/(29,13) right next to Stern's
  pre-museum spot — the live testbed for the double-battle fix + the open framework rotation
  stall. Then Route 110 N → Mauville → Gym 3 (Wattson). Start from `slateport.ss1`.

### ⭐⭐ Session 2026-07-22 (Fable 5, later) — CHAPTER 7 DONE: Steven's Letter + KNUCKLE BADGE (SANDBOX, pushed)
- **`deliver_stevens_letter()` + `do_dewford_gym()` BUILT + VALIDATED**: full `--driver story`
  run `dewford.ss1` → Dewford PC heal → Route 106 → Granite Cave **five-warp ladder chain**
  (every floor is split; route dips through B2F — full pathfinder-verified graph in design
  §Ch7) → Steven (7,8), Letter delivered (TM47) → reverse chain (1F one-way-ledge shortcut)
  → PC heal → dark gym → **Brawly beaten, BADGE02** — **0 derails / 0 whiteouts** (ch7_run7).
  Checkpoint **`tools/story-dev/saves/brawly_done.ss1`** (Dewford Gym (4,4), flags verified).
- **NEW primitive `_walk_warp_chain`** (furthest-along pathable step — first-match loops on
  one-way ledges) + `_enter_warp_by_navigation` (warp-entry with map-change detection +
  last-error reporting). Segment-6 sail gate now a pre-sail map WHITELIST. Checkpoint capture
  rides out leftover dialogue first (dewford.ss1 v1 loaded non-controllable; repaired).
- Brawly prep is FLOOR-ONLY (band 14-16): **no training grass exists around Dewford pre-Surf**
  (Route 106/107/Dewford = surf-only tables; Granite Cave wilds L6-10) — `training_areas.py`
  updated; loss-escalation falls back to the (slow) cave spot. KI-10 logged (post-sail
  mainland respawn edge; mitigated by the early Dewford heal).
- **NEXT: Ch8** — Briney at the Dewford dock (12,9) → sail to Slateport (read the DewfordTown
  decomp for gating: likely needs the Letter delivered — we have it), Route 109 → Slateport
  (Stern/Museum; ‼ Gabby&Ty DOUBLE battle — also the live testbed for the open framework
  rotation stall) → Route 110 → Mauville → Gym 3 (Wattson). Start from `brawly_done.ss1`.

### ⭐ Session 2026-07-22 (Fable 5) — CHAPTER 6 DONE: the bot sails to Dewford (SANDBOX, pushed)
- **`sail_to_dewford()` BUILT + VALIDATED end-to-end** (post_rival.ss1 → Dewford dock (12,3)):
  Rustboro → Route104 north → back through Petalburg Woods (river-split, doorprobe-verified
  warp table in design §Ch6) → south beach → Briney's cottage (17,50) → first-sail **YES/NO**
  (decomp correction: the multichoice is only for later sails) → sail → DEWFORD_TOWN.
  Proven BOTH via `--driver saildewford` AND the real `StoryMode._play` (Segment 6 wired,
  guard map==DEWFORD, clean content-end stop). Checkpoint **`tools/story-dev/saves/dewford.ss1`**.
- **NEW primitive `_talk_to_wandering_npc`** — Briney PATROLS his cottage (as does Peeko);
  4 approaches failed provably before the winner: observe a patrol lap → park BESIDE his
  route → face-tap+A as he transits. Full saga + prevention rules in 08-MISTAKES (2026-07-22)
  + playbook §7 (incl. the `calculate_path`-blocks-walkers gotcha and the three-body
  route-tile deadlock). `STORY_TALK_DEBUG=1` traces the helper.
- Daily upstream check done (main still `5dd898f8`).
- **NEXT: Ch7** — Dewford → Route 106 → Granite Cave 1F→B1F→Steven's Room (7,8): deliver the
  Letter (A-through, no choices; sets `DELIVERED_STEVEN_LETTER`, gives TM47) → back → Gym 2
  **Brawly** (dark gym; type-aware lead — Taillow/Flying resists Fighting; level-floor;
  attempt-cap) → `BADGE02_GET`. Start from `dewford.ss1`; §Ch6–8 has the map facts
  (⚠ validate the cave floor-warp chain + Dewford door warps live).

### ⭐ Session 2026-07-21 (late) — battle-robustness + provisioning fixes (SANDBOX, pushed)
All from real-hardware debug logs; each reproduced + fixed + committed:
- **Faithful PokéNav Match-Call tutorial** now works (bot calls Mr. Stone; renderer-gated,
  state-write fallback). Confirmed on real HW.
- **Rustboro rival** wired (§5c): type-aware lead (Taillow beats grass Grovyle) + whole-team
  **level floor ≥10** + safe heal + attempt-cap. **Failed-rival stuck-at-(16,53) bug FIXED**
  (re-engage keyed off the live battle, not the persistent MET flag). A full fresh run BEAT
  the rival → `post_rival.ss1` captured (Rustboro (16,53), STATE=8).
- **Double-battle after-faint hang FIXED** (`level_up.py` chooser dropped the on-field-partner
  exclusion → returned the partner's slot). A/B proven.
- **Gym/trainer fight-through FIXED** (Roxanne hung switching Torchic into a weak bench):
  trainer/gym/E4 battles now attack-through, never rotate/flee into a stall. A/B proven.
- **Premier Ball batching**: buy Poké Balls in tens → 1 free Premier Ball each (validated +2).
- **OPEN (framework):** the mid-battle **rotation-execution** stall
  (`battle_action_selection.py`) still exists for any rotating strategy — needs a live repro to
  pin `map_battle_party_index` / the party-menu submenu. Story bot sidesteps it in trainers.
  (The sail leg that was queued here is DONE — see the 2026-07-22 session block above.)

## What this project is
Documents and enhances 40Cakes/pokebot-gen3 (Python shiny-hunting bot for
Gen-3 Pokémon via libmgba). Layout (details in CLAUDE.md "Project rules"):
- `40cakes repo/pokebot-gen3/` — PRISTINE upstream mirror (git subtree,
  remote `upstream-pokebot`, commit `5dd898f8`). Daily upstream check;
  record in `40cakes repo/UPDATE-LOG.md` (last check 2026-07-19, unchanged).
- `40cakes repo/DOCUMENTATION/` — verified dev docs of the ORIGINAL program.
- `custom-pokebot/` — OUR PRODUCTION fork; divergences in `DIVERGENCE-LOG.md`.
- `sandbox-pokebot/` — experimental copy; new work is built + verified here,
  then PROMOTED into custom on the user's explicit OK.
- `install.py` (repo root) = custom installer; `install_sandbox.py` = sandbox.
- `Pokemon_Emerald_AI_Notes.md` — transfer notes for the sibling AI project.

## HISTORICAL — what was WHERE as of 2026-07-21 (‼ NOT current state)

> **‼ Read `## ‼ YOU ARE HERE — 2026-07-25 (late), the COUNTER system` below for the
> CURRENT state.** Everything in this section is a snapshot from **2026-07-21** and is
> now roughly eight chapters stale — it ends at "Frontier: PokéNav + tutorial done",
> whereas the bot now reaches **Badge 6 (Winona), the end of built content**. It is kept
> because the per-feature promotion history and the Rustboro-era atlas notes are still
> useful; do not read any sentence in it as describing today.

### ⭐ PROMOTED to custom (production) 2026-07-21 — commit `a9553ee4`
This session's Story-mode work is now in `custom-pokebot`: matured defeat/whiteout
recovery (no Manual / no save reloads; resumable Segment 1), the Oldale heal-loop fix,
StoryCatchStrategy (flee-not-Manual when out of balls), SwapTrainBattleStrategy
(swap-training + finish-don't-flee), whiteout-aware `_story_spin`, `training_areas.py`
groundwork, and the opt-in Debug Logging toggle (`modules/debug_logger.py`). 10 code
files copied sandbox→custom (verified clean superset); DIVERGENCE-LOG updated for the
upstream-file edits (heal exit, main.py debug hook, GUI toggle). Sandbox now matches
custom on these files (test harness / profiles / SANDBOX-NOTES stay sandbox-only).
**Real-hardware validated through:** fresh save → Oldale → rival → Pokédex → Petalburg
→ Wally → Woods → Rustboro → pre-gym catching + swap-training.
**SOLIDIFY-RUSTBORO pass DONE (2026-07-21, promoted `395c392d`/`f04e2c01`):**
(1) Resume edge fixed — Segment 3 recognizes the whole Rustboro area (Route 116 mid-
training resume no longer backtracks). (2) `_lead_strongest_battler()` leads the gym with
our best mon. (3) Training-grind fixed — `_prepare_for_fight` readies only the primary +
near-band battlers (`train_team(slots=)`), leaving fresh low catches to level organically
(#24-team). **Full flow VALIDATED end-to-end in-harness: route116 save → minimal prep →
BEAT ROXANNE (Stone Badge, Mudkip→Marshtomp) → Devon Goods (Rusturf) → clean content-end
stop, 0 whiteouts.**
**NEXT-CHUNK PASS started (2026-07-21, SANDBOX checkpoint, NOT promoted):**
Rustboro mapped statically (Devon Corp floors + Mr. Stone 3F (15,5), rival NPC city (16,50),
PC/Mart/Gym entrances) → §Ch5b Atlas + Hardening Checklist in 12-STORYMODE-DESIGN.
`return_devon_goods_and_get_pokenav()` BUILT + VALIDATED (gets the PokéNav).
**✅ PokéNav Match-Call tutorial SOLVED (2026-07-21, SANDBOX, NOT promoted).** Root-caused
(WebFetch pokeemerald + harness obs): after the PokéNav the game auto-walks you into the
city; the map ON_FRAME (`VAR_RUSTBORO_CITY_STATE==6`) fires the Scientist tutorial → intro
msgboxes → start-menu multichoice (case 3 = POKéNAV) → PokéNav app in
`POKENAV_MODE_FORCE_CALL_READY` (must place a Match Call). **The app does NOT advance in
our headless harness** (proven: 150 A-presses/1500f = 0 progress). Fix (user chose FAITHFUL):
`handle_pokenav_match_call_tutorial()` **actually plays the tutorial** — opens the PokéNav,
Down,Down→MATCH CALL→A→list→A→CALL→A (calls **Mr. Stone**)→advance→B out→
`RUSTBORO_CITY_STATE=7`. This works because the PokéNav app only advances with the **renderer
ON** (`context.video=True`, which the real bot has); harness needs `--video`. **Proven
end-to-end via `_play` (video on): app opens, call placed, clean stop, NO fallback used.**
FALLBACK: headless/stall → `skip_pokenav_match_call_tutorial()` (state-write to vanilla's
exact end-state) — never hangs. **Wired into `_play` §5b → clean stop.**
**REAL-HW RUN (2026-07-21 debug log) confirmed: faithful PokéNav tutorial WORKS (called Mr.
Stone). Losing the rival stranded the bot at (16,52) → Manual — FIXED + validated** (the Down-step
loop keyed off the persistent MET flag; now keys off actual engagement → retries re-engage).
Added (user directive): whole-team **LEVEL FLOOR ≥10** (escalating) + **safe PC heal** right
before the rival, and raised the training heal margin so the swap-train finisher heals earlier.
**✅ FULL FRESH RUN BEAT THE RIVAL + post_rival.ss1 CAPTURED (2026-07-21).** A from-scratch
headless run (new game → … → Rustboro rival) with the fixes won the rival with a NATURAL team
(led Taillow L17 = Flying, resists Grass + hits Grovyle 2×; team Dustox L16 / Marshtomp L18 /
Taillow L17 / Poochyena L16, all ≥10). **No faint-hang recurred** (heal-margin mitigation +
a real team). **`post_rival.ss1`** (scratchpad, regenerate via the fresh run if needed) is
validated: `DEFEATED_RIVAL_RUSTBORO=True`, `RUSTBORO_CITY_STATE=8`, controllable at **Rustboro
(16,53)** — i.e. the rival cutscene leaves you at (16,53) in Rustboro; walk SOUTH from there off
the map edge onto Route 104. The choose-after-faint framework hang is now a rare latent edge
(mitigated, didn't trigger) — still worth a proper fix but not blocking. **NEXT: build the sail
leg from post_rival.ss1 — walk south (16,53)→Route 104→Mr. Briney's house→talk Briney→Dewford
(§Ch6 atlas).**
**Rustboro rival: WIRED (§5c) with type-aware lead + attempt-cap (user-chosen).** Trigger =
coord row y=53 x12-19 (gated VAR==7). §5c: `_prepare_for_fight(band 16-19)` →
`_lead_best_matchup(["Grass"])` (avoids the 4×-weak Marshtomp; validated vs the type chart —
picks a 1× mon) → `fight_rustboro_rival` (stage (16,52), Down across y=53). `RIVAL_MAX_ATTEMPTS=3`
bounds the whiteout→retrain retry (thin team stops cleanly, no loop). Verified: wiring runs
error-free (enters training). ⚠️ **NOT yet validated: an actual rival WIN** — the `devon_done`
test save has a pathological team (Marshtomp + L7-8 filler) that loses regardless of lead. **To
prove the win we need a NATURAL post-gym team save** (ask user for one, or build via a fuller
harness playthrough). **Frontier: PokéNav + tutorial done, rival wired-but-win-unvalidated.** NEXT-AREA MAPPED
(design §Ch6 atlas: Route 104 S → Mr. Briney (sail) → Dewford → Granite Cave (Steven's Letter)
→ Gym 2 Brawly — all warps/NPCs/coords). **Sail-leg build is GATED (see §Ch6 SAIL-LEG RECON
NOTE):** (a) need a real post-rival save (rival cutscene deposit position unknown; a synthetic
rival-flag state stalls at Rustboro (16,53) — the Rustboro-south↔Route104-north corridor needs
recon), and (b) the Briney sail mechanic is understood (talk (5,3) → multichoice → Dewford=idx0).
**NEXT: confirm rival win on real hardware → capture a real post-rival save → build the sail leg
from §Ch6.** Open: #24-team organic-team leveling; #24-trainmap area-training groundwork.
### In custom-pokebot (PROMOTED, production) — big promotion `f0b275f3` (2026-07-19)
Native dashboard GUI (default; `--classic-gui` = stock), handheld mode,
backup/restore + cloud + cloud-save-sync (off by default), macros, Patrol
v3 (multi-map/global-nav), gamepad in-game input, shiny alerts, update
notice, game cheats, tabbed GUI, full-dex sprite picker. Stock auto-updater
footgun fixed (ML-4). Installer V2 done. Requirements install-only-missing.
User confirmed the native GUI + installer hands-on ("worked!").

### In sandbox-pokebot ONLY (BUILT + self/fact-verified, NOT yet promoted)
All 2026-07-19, awaiting user review/promotion:
- #33 GUI fixes (left party always visible; Pokéball-open/Hide both modes)
- #22 Watchdog/auto-recovery · #9 Hunt Planner v1+v2 (encounter index +
  travel-and-hunt) · #23 Living-Dex Orchestrator · #11 Analytics (stats
  browser/trend/luck meter)
- #30 handheld menu→Play-tab + Left Party Section + hover · #31 money cheat
  + Lock · #32 gamepad GUI-nav (adversarially verified clean)
- Adjustments #36–#40: bigger party balls (140px), themed hover tooltip,
  gamepad-nav gated to drawer, auto-decline move learning (`new_move:
  cancel`), catch-ball allowlist (protects Master Ball)
- Living-Dex deepening: #43 opportunistic catching · #44 party ball moved
  to hover (strip now clean) · #41-evo obtainability(evolution) + #42-easy
  capability gating · #41-research Emerald obtainability lists.
  **Census (sums to 386): wild 132/evolution 149/gift 7/static 8/roamer 1/
  event 6/breeding 3/special 1/unobtainable 79 → 217/386 obtainable in
  Emerald without trading.** `modules/data/emerald_obtainability.json`.

### Live-verified on the USER'S REAL SAVE (`Nick - Emerald`, placed in both
bots' gitignored profiles/): real shiny party renders (Celebi/Sceptile
Lv100…), money cheat read real 7,908, analytics read real 57,436
encounters/10 shinies ("lucky"), capability gate read real Old/Good/Super
Rod. Save left md5-identical after every test.

### Dex data (#34/#35 tabs not built yet)
`modules/data/generated/pokedex_data.json` = 386 species COMPLETE except
`dex_artwork` (stats/learnsets/evolutions/sprites/category/height/weight/
flavor all done, Phases 1/2/3a). `itemdex_data.json` = core (309 items);
gaps = map_locations/mart/pickup/historical.

## ‼ YOU ARE HERE — 2026-07-25 (late), the COUNTER system

**Everything committed and pushed. Tree clean.** The session that produced this was very long;
prefer these files over any transcript.

### The headline: Badge 6 from a COLD START
A fresh title-screen run reached the **end of built content** (f2.48M, 38 maps, **0 derails**).
The Fortree rotating-gate puzzle is solved live (`modules/story/fortree_gates.py`, a port of the
decomp's `src/rotating_gate.c`, validated **4/4** against the emulator). Next unbuilt chapters:
**Mt. Pyre, the Magma hideout.**

### The problem now being solved — `#24-counters` (KI-23)
The user's overnight logs: **198 Winona attempts, 41 losses, 41 whiteouts, never won**, with a
party FAR ABOVE her levels (Sceptile L42 vs her L29-33). It lost on TYPES, not levels — Sceptile
is resisted by Flying, Ninjask is itself part Flying, nothing was Electric/Rock/Ice.
**Boss-as-training-vehicle cannot converge without a type answer, and levelling does not help.**

Four pieces, each independently PROVEN, being connected in this order:
| piece | file | state |
|---|---|---|
| detect non-convergence | `story_mode._boss_plan_is_hopeless` | done; Winona now goes through `_prepare_for_fight` (she never did before — the guard could not fire on the one boss that motivated it) |
| identify needed types | same | done; computed from the real type chart, not a table |
| find catch candidates | `modules/story/counter_plan.py` | done; over the whole-game encounter index |
| region reachability | `modules/story/region_reach.py` | done; **KI-24 fixed for BOTH consumers** as of 2026-07-25 — counter selection AND the training gate |
| wire them together | — | IN PROGRESS at session end |
| execute (travel/catch/train) | — | NOT STARTED |

### Four traps a future session must not re-walk
1. **`calculate_path` is unsound at REGION scale** (KI-24). It reads the Route 118/119/120
   dual-elevation bridges as walls, so it reported Route 118 — the real Winona answer — as
   unreachable, and it fails even on a same-map Route 119 walk. **Both consumers now use
   `region_reach`** — `_counter_area_allowed` and, as of 2026-07-25, `_training_area_allowed`.
   Never reach for `calculate_path` to answer "can I get to that map"; it is correct only for the
   final tile-level leg once already ON the map. Measured effect of the training-gate switch: the
   Winona candidate list went from `[False × 10]` to `[True × 5, False × 5]`.
   **The whole story-bot repro suite is GREEN (5/5):** `repro_fodder_grass`, `repro_counter_plan`,
   `repro_counter_wiring`, `repro_region_reach`, `repro_boss_plateau`.
2. **Hop count is a FILTER, not a RANK** (KI-24b). Measured from ROUTE120: Fortree 1, Route119 2,
   **Lilycove 2**, Route118 3, Mossdeep 4, Pacifidlog 10 — Lilycove is *closer* than the answer,
   because one connection can span a whole sea route. Use `max_hops=4` as a sanity bound and let
   `counter_plan`'s own criteria rank.
3. **Event flags are not all monotonic** (KI-21) and **whiteout wipes the Elite Four flags**
   (KI-22). `_done()`-style resume gating assumes flags stick; for Ch16 that is false.
4. **‼ Expect a fix in a well-tested area to turn something RED for the WRONG reason.** Much of
   this suite was written to CHARACTERISE defects, so some assertions require a FAILURE to occur
   ("at least one unreachable", "raises", "returns empty") and invert the moment that failure is
   repaired. **Two were found this way on 2026-07-25 alone**, and neither would ever have been
   noticed while green. When a fix reddens a test, the first question is not "what did I break"
   but "was this assertion depending on the thing I just fixed?" — see the 08-MISTAKES pattern
   entry (2026-07-25).

### Research: five `CLAUDE-VALIDATED-*` files, ~175 claims grounded in the real decomp
Indexed in `ai-research-notes/00-READ-THIS-FIRST.md`. **Gemini notes are LEADS ONLY** — a Claude
subagent with tool access is the final word (`CLAUDE.md`). Best grounding method found: a local
sparse clone of pokeemerald (~44 MB) — it makes ABSENCE claims checkable, which per-file API
fetches cannot do.

### Top open items
1. **`#24-counters` phase 2** — now the #1 item. The bot DIAGNOSES a hopeless boss plan and names a
   concrete reachable counter, then stops. Travelling to it, catching it and training it is unbuilt.
   `#24-whiteout` collapsed into this (below), so they are one problem from two ends.
2. **`#24-npcheal`** — re-pair Route 111 training to `ROUTE111_OLD_LADYS_REST_STOP` (decomp-cited
   full ungated repeatable heal, 96 steps vs 213 to Fallarbor). Needs a heal-at-NPC helper.
3. `#24-counters` phase 2 (the chain NAMES a counter; acting on it isn't built).
4. `#24-edgecost`, `#24-regionreach` gate table, KI-18 live confirmation.

### ✅ 2026-07-26 — SURVIVAL MODE closes the travel-attrition half of `#24-whiteout`
The batch's largest loss cluster is fixed: **25 whiteouts on ROUTE110 in one run** (31 of 66
batch-wide). It was NOT training attrition — with no `train_team` session running,
`on_battle_started` falls through to `LevelUpTravelBattleStrategy`, which fights every wild to
level the lead and "flees only at low HP, which the training loop covers by healing". On a TRAVEL
leg there is no training loop, so nothing heals and HP only falls until the party wipes.
Now: after **3** defeats on a map, wild battles there are FLED (`SURVIVAL_WHITEOUT_THRESHOLD`).
Wild only (trainers are un-fleeable; the boss/gym path is untouched), never during `train_team`,
per-map. `repro_survival_mode.py` (7 cases) asserts each limit and flees on the real run01 state.
‼ **Read the 08-MISTAKES entry before editing `on_battle_started`:** the first version silently
did nothing because several branches of that method import `console` locally, which makes the name
function-local for the WHOLE method — so a module-level `console.print` is an `UnboundLocalError`
that a surrounding `except Exception: pass` reports as "condition False". The warning was
commented 16 lines above where I wrote it, and I still hit it.
**Suite is now 7/7** (`repro_survival_mode` and `repro_training_unreachable` joined the five).

### 🧪 2026-07-25 — LIVE BATCH `20260725-194810`: the day's fixes hold; 2 new issues fixed
5 fresh cold-start lanes, 3M frames, commit `26613bcb`. **1/5 reached the frontier (baseline 0/5)**,
**0/5 move-learn deaths (baseline 2/5)**, 66 losses (baseline 128). Batch dir has `REVIEWED.md`.
* **All three of the day's fixes confirmed live.** The `CantForgetHM` branch fired **44 times** —
  the wedge situation kept arising and kept being handled, which is stronger than "it didn't occur".
  The plateau guard fired on Norman at **exactly 6 losses** (was 27). The counter chain ran
  end-to-end for the first time and named `Makuhita (Fighting), Granite Cave 1F, L6-10, 50%`.
  The battle-fault channel never triggered — still repro-only evidence.
* **Fixed: a wrong YES from `region_reach` cost the RUN, not a walk** (killed 2/5). ROUTE111's
  training tile is FALLARBOR-SIDE ONLY but the map is reachable from Mauville, so the gate passed
  and the walk died at the desert — then every derail re-picked the SAME tile. New
  `UnreachableDestinationError` + a `(standing map, target map, tile)` memory. ‼ Read the
  08-MISTAKES entry: "recoverable" describes the LOOP, not the failure.
* **Fixed: `livetest.py`'s whiteout metric always read 0** — it counted a debug-log-only string.
  ‼ **Ignore the `whiteouts` field in every archived batch summary.** Now also emits `losses` and
  `losses_by_map`, automating the census that redirected `#24-whiteout`.
* **Found, NOT fixed — training-loop attrition has no give-up guard.** run01 lost **25 times on
  Route 110** swap-training a lopsided team, KOs flat at 1. Same plateau shape as Norman; the guard
  covers configured BOSSES only. Now the largest single loss cluster (31 of 66). See `#24-whiteout`.

### 📊 2026-07-25 (later) — `#24-whiteout` MEASURED: it is gyms, not attrition
Do not redesign healing/travel for this. Census of all 5 night5 runs (~128 losses; **losses and
whiteouts are 1:1** — there is no potion/revive layer, so losing always means whiting out):
**~83% of losses are GYM LEADERS** — Norman 38, Wattson 24, Winona 20, Flannery 18, Route110 10,
Dewford+Rustboro 6. The cost is the **boss-as-training-vehicle** strategy, and it is a PLATEAU, not
slow progress: run3 made **27 Norman attempts over 508,000 frames** (~19k each) for **+2-4 levels**,
with **KOs flat at 1-2 of 4 across all 27** and a **L15 Shroomish** carried untrained throughout.
* **Fixed:** `_boss_plan_is_hopeless` was **power-blind** — it accepted **Rock Smash (20 power)** as
  a super-effective "answer" to Norman (Fighting is 2.0x vs Normal, and that HM is one the bot is
  REQUIRED to carry), so the guard could never fire on the boss that needed it most. Now needs
  `base_power x effectiveness x STAB >= CREDIBLE_ANSWER_POWER` (60). A/B on the real logged party:
  `(False, []) -> (True, ['Fighting'])`. Its `except Exception` also used to return the SAME value
  as success — a silent self-disable — and now warns.
* ‼ Reading the night5 logs: they launched at **07:36**, and the entire counter chain landed
  **after** (09:47 → 13:27). Anything those logs show about non-convergence pre-dates the guard.
* **Still open** (now `#24-counters` phase 2): the bot stops with a named counter instead of going
  and getting it. Also unbuilt: a provisions/healing layer so a loss isn't automatically a whiteout,
  and benching dead weight (a L15 in a L30+ team is a free loss).
* Tests: `repro_boss_plateau.py` CASE 5 = the REAL run3 party + its real KO trace; CASE 6 guards
  against over-correcting the threshold (STAB Double Kick, the organic Norman win, must still count).

### ✅ 2026-07-25 (later) — `#24-movelearn-recovery` CLOSED (was the #1 open item)
The move-learn wedge that killed 2 of 5 night5 cold-start runs (~f1.55M each) is fixed and
A/B-proven from the real captures. **Read the changelog entry before touching move-learn code** —
the filed diagnosis was only the last of FOUR links, and three of them are still worth knowing:
* The game says **`Task_HandleInputCantForgetHMsMoves`** ("HM moves can't be forgotten") and until
  now nothing in the codebase referenced that symbol — `get_learn_move_state()` reported it as the
  Yes/No prompt, because the script pointer stays parked at `BattleScript_AskToLearnMove+0x11`.
* The actual hang was an **unbounded "screen is still opening, just wait" branch**: zero inputs for
  6,000 straight frames. Found by instrumenting BUTTON PRESSES, not states — the before-arm read
  `{'B': 4050, 'A': 1350}` with **no `Down` at all**, which is exactly 3×1800 escape-valve presses
  and proved the main handler pressed nothing.
* The cursor in `sMonSummaryScreen` is **not trustworthy until the move-select input task is
  active**; a stale read is how an HM got confirmed while the decision was DECLINE.
* New: **`modules/battle_fault.py`** — battle handling is a SIBLING generator on
  `context.controller_stack`, not nested in the mode, so a `BotModeError` from battle code can
  never reach `StoryMode.run()`'s `except`. Faults now travel by an **opt-in channel**
  (`handles_battle_faults`) and cost one derail. Stock modes are provably unchanged.
Assets: `saves/movelearn_hmwedge_{quickattack,slash}.ss1` (real wedge states, rescued from the run
profiles before the next batch could overwrite them), `repro_movelearn_hm_wedge.py`,
`repro_movelearn_fault_recovery.py` (stock / optin / story arms). Suite 5/5 green.
⚠ `repro_hm_replace_valve_forced.py`'s default budget was raised 25,000 → 35,000: bounding the wait
costs more emulator frames per iteration, so the third strike moved to f27,583 and the repro
*looked* like a regression when nothing had changed.

## Earlier — 2026-07-25, overnight autonomous research stretch

**State: everything committed and pushed. Working tree clean apart from gitignored run output.**
The user is running `Story (ENDLESS RESET)` overnight on their own machine and will bring the logs
in the morning. I was told to proceed autonomously on RESEARCH/DOCUMENTATION until then.

### Headline results from 2026-07-24/25 (all pushed)
* **BADGE 6 WON.** Fortree's rotating-gate puzzle is solved live — the decomp rule
  (`src/rotating_gate.c`) was ported into `modules/story/fortree_gates.py`, validated **4/4**
  against the live emulator at the tile a real run died on, and a full run reached Winona's
  challenge tile and beat her in 182k frames with **0 derails**. Story bot now reaches the
  **end of built content** (next unbuilt: Mt. Pyre, Magma hideout).
* **First run ever to survive its whole 3,000,000-frame budget** without hanging.
* ~19 fixes shipped, ~15 A/B-proven. Story-bot bundle PROMOTED to `custom-pokebot`
  (`6202a257`), verified there behaviourally, not just by import.
* `Story (ENDLESS RESET)` bot mode + a CLI batch runner (`tools/story-dev/endless_runs.py`).

### Research state — the important nuance
`PROJECT KNOWLEDGE/ai-research-notes/` holds ~57 Gemini notes. **Read
`ai-research-notes/00-READ-THIS-FIRST.md` before using ANY of it.** Findings that matter:
* Notes are LEADS. A Gemini pass may never be the final word on a fact code depends on.
* Only `CLAUDE-VALIDATED-*.md` files are grounded in the real decomp. **FIVE exist**
  (~175 claims total): `items-round1` (9 claims), `concepts-round1`
  (**51 claims: 30 confirmed, 15 refuted, 6 unresolved**), `concepts-round2`,
  `concepts-round3`, `story-round1`.
* ‼ **SUPERSEDED grounding method.** Round 1 used per-file API fetches
  (`gh api repos/pret/pokeemerald/contents/<path>`). **Use a local sparse clone of
  pokeemerald (~44 MB) instead** — it is the default now because it makes ABSENCE
  claims checkable (you can grep the whole tree for "this symbol does not exist"),
  which a per-file fetch fundamentally cannot do. The `gh api` route still works for
  a single known path, but do not start a validation round with it.
* **Stacking same-model passes does NOT converge on truth.** The adversarial critique invented a
  correction to a claim that was already right; the adjudicator then claimed ~100% confidence
  while describing recall as decomp verification.
* ‼ **~35 notes are tainted**: I overrode the relay's correct default with a two-generation-old
  model (see 08-MISTAKES 2026-07-25). Now impossible — `gemini_relay.py` refuses anything below
  Pro 3.1 in code. Story angles have been re-run as `story-notes-s*-v2.md`.

### The four highest-value validated facts (safe to build on)
1. **Mid-battle EXP survives a whiteout** → boss-training mode is VALID. But EXP goes only to mons
   ALIVE when the opponent faints, and the trainer ×1.5 is per-recipient after the split.
2. **A catch cannot be lost** with full party + full boxes (guarded before the ball is consumed).
   Real risk is an infinite bag→"BOX is full"→bag loop.
3. **The roamer sets NO flag** and is destroyed by every ODD battle outcome (incl. a mutual KO and
   teleport). `FLAG_DEFEATED_*` on statics means "encounter resolved", not "destroyed".
   **Whiteout is the safe abort for every scripted static.**
4. **`IsMonValidForMoveDeleter` does not exist** — the game guards only SURF
   (`IsLastMonThatKnowsSurf`). Fly/Dive/Waterfall/Strength/Rock Smash/Cut/Flash are UNGUARDED, so
   the bot must own HM coverage or it can strand a run permanently.

### Next steps, in priority order
1. **Cross-reference the user's overnight ENDLESS-RESET logs** against
   `tools/story-dev/batch3/*.log`. Where runs die tells us which research topic actually blocks
   progress — that beats more research.
2. `#24-movelearn-recovery` — the move-learn `BotModeError` is raised inside the battle handler,
   OUTSIDE StoryMode's derail-recovery scope, so a stall kills a run instead of costing one
   battle. **This killed 2 of 3 cold-start runs.** Gated on `#24-harness-savepath` (concurrent
   runs all overwrite one shared save path, so it still has no clean repro).
3. `#24-npcheal` — re-pair Route 111's training band to `ROUTE111_OLD_LADYS_REST_STOP` (PROVEN
   full ungated repeatable heal, 96 steps vs 213 to Fallarbor). Needs a heal-at-NPC helper;
   the existing path assumes a Poké Center layout.
4. KI-18 remains open/downgraded: both fixes are proven, but no live `.ss1` confirms the real
   cursor lands on the partner's slot.
5. `#24-whiteout` — attrition is the largest silent cost (58/85 whiteouts in single runs).

## MOST RECENT — 2026-07-24 (story bot: 3-starter validation batch)

**What just happened.** Ran three starter-locked fresh runs to hunt starter-specific
bugs (`profiles/starter-{treecko,torchic,mudkip}`, each `story.yml` pinning `starter:`).
All three are FINISHED. Headline: **no starter-specific logic bug exists** — every failure
was on shared navigation/attrition code, so the chapter code is starter-agnostic.

| starter | frames | maps | stopped at | party head |
|---|---|---|---|---|
| treecko | 2,195,761 | 38 | `get_devon_scope` → `_ride_out_scripted_scene` (Route 120, Ch13d) | Sceptile L39 + **Castform L25** |
| torchic | 1,650,182 | 27 | `ensure_facing_direction` @ Route 111 (18,99) | Combusken L29 |
| mudkip  | 2,113,515 | 34 | "too many whiteout recoveries" guard → Manual | Marshtomp L38 |

Treecko is the DEEPEST organic run to date — the Castform proves it cleared the Weather
Institute (Ch13b) and got as far as the Devon Scope errand. Logs live in
`tools/story-dev/starter-runs/{treecko,torchic,mudkip}.log`.

**Fixed this session:** `ensure_facing_direction` unbounded press loop (branch-local guards
could not fire — see 08-MISTAKES 2026-07-24). Now bounded at 1800 frames → `BotModeError`,
which StoryMode can recover from instead of hanging.

**Open from this batch (not yet fixed):**
- **Whiteout attrition is the top cost.** treecko 58, mudkip 85, torchic 11 whiteouts.
  Clusters: mudkip Petalburg ×24 / Slateport ×18; treecko Mauville ×16 / Slateport ×14 —
  i.e. the Norman and Wattson gyms plus the Slateport corridor. The "boss re-attempt IS the
  training" strategy is functioning but expensive; mudkip's run ended because it tripped the
  consecutive-whiteout bound. Needs a prep/attrition rethink, punch-list #24-whiteout.
- treecko's Route 120 `_ride_out_scripted_scene` wedge (Ch13d) — new, uncaptured.

**Docs:** `17-PORTABLE-ORCHESTRATION-GUIDE.md` added — the project-agnostic version of the
multi-agent structure, written to be lifted into any other Claude Code repo (16 stays the
Pokébot-specific one).

## Most recent work (2026-07-20)
- **PLANNING & RESILIENCE METHODOLOGY (doc 13) + out-of-balls safety floor (sandbox).**
  User directive: pause new story/feature code, plan the situations up front
  (provision-or-fall-back, never break, no cheats), retrofit existing scripts with
  preconditions/fallbacks, resume story ONLY when the user says so. Delivered:
  **`13-PLANNING-AND-RESILIENCE.md`** — goal-oriented task model (preconditions →
  provision/fallback → execute → verify → recover), Resource Ledger spec, an
  enumerated Contingency Catalog, the **Mart Atlas** (Oldale (2,4)/Petalburg (8,6)/
  Rustboro (11,7); badge-gated basic/expanded stock; Poké Ball 200), the Emerald
  money reality (no Vs Seeker → sell/Pickup/economy), a retrofit plan, and the future
  decision-brain seam. Referenced from 00-README. **First retrofit done: catching is
  now resource-aware** — `_should_catch` returns False when poke_balls ≤ 1 so it
  never attempts a catch it can't complete (fallback = skip). **BUY-AT-MART
  PROVISIONING now COMPLETE + verified**: `buy_poke_balls`/`provision_poke_balls`
  (early_game.py) drive the Emerald shop (talk from Rustboro-mart (3,3) facing Left;
  Poké Ball index 0; `wait_until_task_is_not_active(task,"A")` for list confirms;
  advance the "How many?"/"OK?" messages). Wired into catch_starter_team: out of
  balls → buy min(30, affordable) keeping a ¥500 reserve → resume; broke → skip.
  Verified end-to-end (balls forced to 2 → caught → bought 30 → resumed → team of 4).
  Commits: doc 13, `_should_catch` safety floor, `1a3df6ad` buy provisioning.
  **Retrofit largely complete** (catching/healing/training/nav/defeat/derail all
  have preconditions+fallbacks). Buy made SHOP-AGNOSTIC (`_mart_item_row` reads stock
  live → works at any mart). **DO NOT resume story chapters until the user says so.**
- **⭐ LATEST (2026-07-21) — "stuck at Oldale PC" investigation (sandbox).** User
  reported the bot getting stuck at the first Poké Center in Oldale "after respawn."
  Two DISTINCT bugs found:
  - **Bug 1 FIXED + verified — Segment 1 intro re-run.** `_play` Segment 1 was
    monolithic (gated only by RECEIVED_POKEDEX), so ANY pre-Pokédex recovery/resume
    (whiteout, derail, loaded save) re-ran the scripted intro FROM THE TRUCK →
    `go_upstairs` navigated to the house from Route 103/Oldale → impossible → derail
    loop, frozen in place. Reproduced from a pre-Pokédex Route 103 save. Fix: split
    Segment 1 — scripted intro (truck→lab) runs only while `_has_starter()` is False;
    train→rival→Pokédex is resumable + gated by DEFEATED_RIVAL_ROUTE103. Verified it
    now resumes at training. Also hardened the derail budget: `_progress_sig` is now a
    monotonic PARTY fingerprint (flags flicker during battle transitions and faked
    progress → infinite loops); recovery `wait_until_truly_controllable` (waits for a
    STABLE controllable overworld, presses nothing).
  - **Bug 2 OPEN — post-battle transition freeze (likely the ACTUAL "Oldale PC
    stuck").** During training, after a battle (flee / level-up / move-learn e.g.
    Mudkip Water Gun @L10) the return-to-overworld transition leaves the overworld
    non-controllable while the bot acts (navigate / walk to the Oldale nurse) → can
    hard-freeze (nurse heal dialogue never starts). Confirmed REAL (harness runs the
    identical `main_loop`), timing/starter-sensitive (default starter = "random";
    Treecko's overnight run got through, Mudkip reliably hits it). Offline repro is
    hampered by save-state reload artifacts. **USER DECISION: validate on the real PC
    first** (force Mudkip via `<profile>/story.yml` `starter: mudkip`, fresh game) and
    report back before a deeper fix. See 08-MISTAKES 2026-07-21 (3 entries).
  Committed to sandbox; battle_handler mis-fire change reverted (keyed on
  gDisplayedStringBattle which goes STALE after battle).
- **⭐ DEBUG LOGGER (2026-07-21, sandbox) — Bug 2 CONFIRMED on real PC.** Built an
  opt-in "Debug Logging (diagnostic file)" toggle in the Run (bot-mode) menu of BOTH
  GUIs (native `dashboard_gui.py` + classic `emulator_controls.py`), default OFF.
  `modules/debug_logger.py` writes an extensive structured log to
  `<profile>/debug-logs/<mode>-debug-<ts>.log` (gitignored): EVENT stream
  (story steps / battles+outcomes / map / party level-ups / mode changes / Story
  DERAIL+WHITEOUT) + auto STUCK DUMPS carrying the running GENERATOR CALL STACK
  (function+line, via gi_yieldfrom walk — pinpoints where the bot is waiting) plus
  held buttons / tasks / scripts / battle text; battles excluded from stall
  detection. Hooked once in `main_loop` (guarded); StoryMode logs derail/recovery
  events. Validated on the freeze scenario (self-healing ~1078-frame stalls →
  DERAIL #1..#5 → Manual).
- **⭐⭐ Bug 2 FIXED (2026-07-21) via the user's real-bot debug log.** The generator
  call stack pinpointed it (a TREECKO run — NOT Mudkip-specific): heal → derail →
  RE-heal loop. `heal_in_pokemon_center` returned while the overworld was transiently
  non-controllable, so `fight_route103_rival`'s next navigate choked → derail →
  recovery re-ran `_play` → re-healed → endless heal/leave-PC/re-enter-PC → Manual.
  FIX: heal waits for a STABLE controllable overworld after the exit warp
  (`higher_level_actions.py`, 34bfc47a). Downstream blocker also fixed:
  `StoryCatchStrategy` flees instead of Manual when out of balls (opportunistic
  pre-gym catching could burn the 5 starter balls on bad RNG; 3b069d47). VALIDATED
  in-harness end-to-end (route103 pre-Pokédex → **Rustboro → Route 116 catching**,
  team Mudkip L13 + Poochyena L4, **0 derails / 0 Manual**).
- **⭐ SWAP-TRAINING (2026-07-21) — fixes the training loop the user then saw.** With a
  very under-levelled catch (Lv2 Poochyena) the pre-gym `train_team` ground it against
  too-high Route 116 wilds → fight/faint/heal/repeat churn. NEW `SwapTrainBattleStrategy`
  switches a trainee that's ≥2 levels below the wild to the strongest team-mate turn 1
  (shares XP, no fainting/heal-churn); gated by `_SWAP_TRAIN` around `train_team`, which
  heals off the team's lowest HP. Validated (route116team save): Poochyena L4→L7,
  **0 heals / 0 faints**, flee rate 25%. Commit ef812c0e. User chose "BOTH": also landed
  area-training groundwork `modules/story/training_areas.py` (#24-trainmap, commit
  d405674d) — level-spectrum of early grass + `best_training_grass()`, to later route a
  low mon to a full-XP area (swap-train stays the fallback). **NEXT: user re-tests on
  the real PC — should now reach Rustboro/Roxanne with smoother training.**
  Documented strategy (planning doc §4/§4b): map shops/PCs AS REACHED, not all now;
  new punch-list #24-shops (incl. Lilycove multi-floor, E4 PC shop+mart) and #24-pc
  (PC/box team management). Remaining planning items future/noted (money-making
  engine, PP-aware heal, HM-gated routing, decision brain).
- **STORY TEAM-BUILDING: pre-fight training + retrain + pre-gym catching (sandbox,
  user directives #1/#2).** (a) `train_team(target, scope)` grinds wilds on Route 116
  (11,7) — scope 'whole' rotates the lowest battler to lead, 'lead' trains the lead.
  (b) `_prepare_for_fight(cfg)` before Gym 1: proactive target in the band (Roxanne
  13-17, random) + reactive escalation if lost here ≥2× (the +levels strategy AND
  team scope both randomized for organic feel). (c) `catch_starter_team(4)` +
  `on_battle_started` catch branch: catch NEW species (no dups, by dex #) until the
  party fills to 4. Verified: rustboro.ss1 → train Mudkip→Marshtomp L20 → beat Roxanne
  → Chapter 5a; and caught Abra/Whismur/Taillow (party 1→4). Committed b2fd5875
  (train/retrain) + c6433bf6 (catching). Tuning notes: Route 116 trainers over-train
  a bit; a full caught team is a slow grind (the 'lead' scope keeps some runs fast).
  **NEXT: Chapter 5b (return goods → Devon Corp 3F president → PokéNav → Rustboro rival).**
- **STORY DEFEAT/WHITEOUT RECOVERY built + verified (sandbox, user directive #1).**
  No more save-state reloads on defeat. (1) Watchdog neutered for Story
  (`_SELF_RECOVERING_MODES={"Story"}`, watchdog.py) — never reloads/rewinds. (2)
  StoryMode: `on_whiteout()`→abort+True (never Manual); `run()` wraps `_play` in a
  restart loop that steps out of the Poké Center (respawn lands ON warp (7,8) → walk
  above + step down), waits for a stable started+overworld state (post-warp flickers
  "not started", which had misfired the intro), and resumes; `on_battle_ended(Lost)`
  counts losses per location. Verified from rustboro.ss1 + injected Lv3 Poochyena:
  lost to Roxanne 7×, recovered every time, stayed in Story, no reloads. Committed
  `301fdea9`. **NEXT (in progress): retrain-on-2nd-loss (Route 116 grass, randomized
  scope/target per user), pre-fight level thresholds (~L17 for Roxanne), pre-gym
  catching (new species only), then Chapter 5b.** Repro harness gained `--inject-weak`.
- **STORY CHAPTER 5a BUILT + VERIFIED (sandbox only): recover the Devon Goods.**
  `recover_devon_goods()` (early_game.py) wired as StoryMode Segment 5a (gated by
  RECOVERED_DEVON_GOODS). After Gym 1: walk Rustboro → theft (DEVON_GOODS_STOLEN) →
  chase east onto Route 116 → across to the Rusturf Tunnel west door (47,8) →
  approach the grunt at (13,5) from the west and engage WITH A → grunt battle →
  goods recovered + Peeko freed. Verified via the real StoryMode.run() from
  gym1_done.ss1: RECOVERED_DEVON_GOODS=True at ~f31858, clean finish (Mudkip→Marshtomp
  evolved mid-chase, handled cleanly). Checkpoint `goods_recovered.ss1`. Key geometry
  fixes (mapdump): Devon Corp warps (11,15)/(12,15); Route 116 far tiles have no path
  (ledges — target the west edge, let the global navigator cross); the tunnel grunt
  BLOCKS the corridor (don't pathfind past it — engage with A, not B). **NOT promoted
  to custom** (sandbox-only, like legs 3-4 + Gym 1). **NEXT: Chapter 5b —
  `return_goods_get_pokenav()` (back to Devon Corp, president on 3F → PokéNav) + the
  Rustboro rival (211).** Full plan + verified coords in design §Ch5.
- **★ Lv16 MOVE-LEARN HANG — ROOT CAUSE FOUND & FIX VALIDATED (both builds, ML-13).**
  Overnight autonomous debugging session (user-authorised). REPRODUCED the exact hang
  with a faithful main.py-loop headless harness (`scratchpad/repro_movelearn.py`):
  inject a Treecko at `exp_for_L16-1`, walk into the Route 103 rival (single-Pokémon
  trainer, encounters avoided) so it crosses Lv16 on the KO that ENDS the battle.
  ROOT CAUSE: the Emerald BATTLE "Delete a move to make room for X?" Yes/No has NO
  backing task, so `get_learn_move_state()` could only detect it by a fragile
  script-offset (`+0x11`); when that never matched, the state stayed `Unknown` and the
  fallback pressed A only when `is_waiting_for_input()` (the FIELD printer, unreliable
  in battle) → it pressed NOTHING → froze on the Yes/No. FIX: rewrote
  `handle_move_replacement_dialogue` to be fully TEXT/TASK-driven (§DA) — Yes/No
  detected from on-screen text, move-select from the reliable input task, all other
  text advanced with A directly (no is_waiting_for_input gate); hardened
  `handle_evolution_scene`'s hand-off likewise. PROVEN by fault-injection A/B (force
  the state Unknown + is_waiting_for_input False = the user's env): OLD stalls ~10,600
  frames & fails to learn the move; FIXED resolves in 394 frames, learns Pursuit,
  evolves to Grovyle, sensible moveset — on BOTH builds. The earlier ML-12 dispatch
  reorder was a RED HERRING (A/B byte-identical) but is kept as harmless defence.
  Backup before the session: git tag `backup-pre-overnight-2026-07-20` (pushed) +
  local copy `C:/Remote Projects/_pokebot_backup_2026-07-20_overnight/`.
  Committed: `7af57428` (fix, both builds) + `71732daf` (design §DA doc).
  **END-TO-END from-scratch proof:** ran a FRESH Treecko game via the real Story
  mode (no injection); Treecko trained naturally to Lv16 in a real story battle and
  hit the EXACT fragile condition (`ml=Unknown, tasks=[]`, "trying to learn PURSUIT")
  — the fix RESOLVED it cleanly (learned Pursuit, mode=Story continued). This is the
  user's precise scenario working on a fresh save. (Separately, that run then
  WHITED OUT: a lone Lv16 Treecko can lose to Roxanne — the KNOWN #24-team weakness,
  NOT the move-learn bug; `do_rustboro_gym` assumes a stronger team. Flagged for
  #24-team/#24-defeat.) Recommend the user still do one real 32× confirmation.
- **MOVE-LEARN HANG — dispatch-order fix + live stall diagnostic (BOTH builds).**
  User: the Lv16 move-learn STILL froze on the "Delete a move?" prompt despite
  every prior fix passing my offline harness (the unexplained harness-vs-real
  gap). Found a concrete cause in `handle_battle`'s dispatch chain (ML-12): the
  action-selection check (`get_main_battle_callback() ==
  "HandleTurnActionSelectionState"`) ran BEFORE the move-learn check, so if that
  callback lingered while the post-battle move-learn prompt was up, the frame was
  swallowed by action-selection and the prompt was NEVER handled → the exact hang.
  FIX: move-learn + evolution-animating now dispatch FIRST, before action
  selection. Also added `_dump_battle_stall_diagnostic()`: when the in-battle
  no-progress watchdog fires (~100s), it now logs the EXACT on-screen battle/field
  text + script instruction + callback + move-learn state + active menu tasks to
  the console AND `<profile>/battle_stall.log` — so if it still hangs, the user's
  log pins the precise frame (closes the harness-vs-real gap with real data, §DA).
  The move-learn text-detection is already universal (matches generic phrases
  like "make room for", reads the offered move dynamically). Both builds compile.
  NOT yet user-verified on the real 32× run — **ask the user to re-test; if it
  still freezes, send `battle_stall.log`.** Design §DA; ML-12.
- **AUTONOMOUS RUN (2026-07-20): a fresh game now auto-plays through GYM 1
  (Stone Badge).** User granted full autonomy to build story chunks until a wall.
  Done this run: (a) documented the Story bot's PURPOSE — it's the deterministic
  REFERENCE/scaffold for the SEPARATE Pokémon Emerald AI project (design §P,
  01-VISION); (b) built the reusable recon tool `sandbox-pokebot/tools/mapdump.py`
  + a RECON PLAYBOOK (design §R); (c) PROMOTED Petalburg→Woods (legs 1-2) to
  custom (`8686a8d8`); (d) built + verified (all deterministic, ×2, via the
  listener harness with per-frame state refresh):
  **leg 3** `cross_petalburg_woods()` (Woods maze + Aqua/Devon scene → Route 104
  north), **leg 4** `travel_route104_north_to_rustboro()` (→ Rustboro), and
  **GYM 1** `do_rustboro_gym()` (heal → gym → beat Roxanne → BADGE01_GET). All
  wired into StoryMode. Checkpoints: route104_north / rustboro / gym1_done .ss1.
  **NOT yet promoted** (legs 3-4 + Gym 1 await user test→promote).
  NEXT: Chapter 4 (deliver Devon Goods → Rusturf Tunnel → Dewford / Gym 2).
- **FIX (2026-07-20, user-reported): Petalburg Woods STALL** — the real bot got
  "stuck" in the Woods (all my tests passed). Root cause ML-9: door entry
  hand-stepped onto the warp tile (flaky → BotModeError → main.py Manual mode =
  "stuck"), AND my harness masked it by reading player/map every frame. FIX: warp
  via `navigate_to(map, door_tile)` (`_pass_through_door`, like
  heal_in_pokemon_center). Re-verified with a MAIN.PY-FAITHFUL harness
  (scratch `faithful.py`): wally_done → Woods → Rustboro → Gym 1 → BADGE01_GET
  True, no error. Fixed in BOTH builds (sandbox + custom — leg 2 was promoted).
  **Test harness rule CORRECTED (design §16 / ML-9): match main.py — do NOT read
  player/map every frame (it hides timing bugs); catch BotModeError→manual.**
- **CHAPTER 5 (Devon errand) FULLY RECONNOITERED, not built** — mapped live from
  gym1_done: theft scene (StolenGoodsScene @ ~23,20 → DEVON_GOODS_STOLEN) needs a
  FLAG-ANCHORED ride-out (mid-scene controllable windows thrash the generic one);
  Devon employee (EmployeeAskToGetGoods @ 30,9); chase Rustboro E → Route 116 →
  Rusturf Tunnel WEST door Route116 (47,8)→tunnel(4,10) [navigate_to_anywhere
  picks the wrong (Verdanturf) warp — use _pass_through_door leg-by-leg]; grunt
  battle → RECOVERED_DEVON_GOODS + Peeko; return → Devon Corp (11,0) →
  RECEIVED_POKENAV. Rival battle (DEFEATED_RIVAL_RUSTBORO) trigger still to find.
  Full plan design §Ch5; checkpoint post_theft.ss1. NEXT: build recover_devon_goods()
  + return_goods_get_pokenav() using the flag-anchored ride-out + _pass_through_door.
- **RESUME-FROM-ANYWHERE v1 + Wally-detection fix (sandbox)** — user-reported a
  resumed save (in Petalburg Woods) mis-detected as "still needs Wally".
  StoryMode.run() rebuilt as a SEGMENTED flag-gated resume (fresh game runs all;
  resumed/hand-played save skips finished segments; Woods segment enters by
  current map). Fixed chapters.py Ch2 flag → HIDE_PETALBURG_CITY_WALLYS_MOM (the
  never-set THANKED_FOR_PLAYING_WITH_WALLY was the bug). Verified across
  checkpoints. Design §RS; refinements (per-step, fly/teleport, title-Continue,
  evolution) = punch-list #24-resume/#24-evo. Sandbox-only (needs legs 3-4+gym
  promoted first).
- **MOVE-LEARNING re-checked** — user reported "still has issues (Pursuit/Treecko)".
  The decision logic is verified correct (Mudkip + Treecko/Pursuit, never throws,
  declines status moves) and on the real path (_listeners→handle_battle→
  handle_move_replacement_dialogue); most likely their test predated the
  move-learning commit. NOTE evolution is OFF (stop_evolution default True) →
  #24-evo. Ask user to re-test with latest.
- **Smart MOVE-LEARNING implemented (both builds)** — user-reported the "learn a
  new move / delete an old one?" prompt. Added `LevelUpTravelBattleStrategy.
  which_move_should_be_replaced()`: never trades a damaging move for a status move
  (a Pokémon can't end up with only non-combat moves), preserves type coverage,
  skips no-gain moves; overrides the stock `new_move: cancel` decline-all.
  Unit-verified with real game objects (both status-slot and all-damaging kits).
  Remaining refinement (status-move utility ranking) folded into #24-team.
- **NEW punch-list items** (both user-requested, future): **#24-team** organic
  team-building / helper acquisition (design §TB), and **#24-ui** a Story-bot
  pre-run settings popup (name / starter / nickname). #24-ui is explicitly
  "after the bot is finished + tested 100%".
- OPEN: Torchic-vs-Roxanne needs the #24-team helper model (do_rustboro_gym
  assumes a favourable starter; verified with Mudkip).
- **Story travel Petalburg → Petalburg Woods BUILT + verified (sandbox, not
  promoted).** `travel_to_petalburg_woods()` (early_game.py) + new
  `LevelUpTravelBattleStrategy` (story_mode.py), wired into StoryMode. Chain:
  heal at Petalburg PC → cross WEST onto Route 104 riding out the one-time
  `PetalburgCity_EventScript_Scott` cutscene at (4,12) → fight the Route 104
  trainer (no-flee strategy) → enter the Woods south door (10-11,38) via
  discrete up-steps. Deterministic via the listener harness (fresh gym save →
  Woods, 6251 frames, ×2). KEY FIXES: single-mon party can't flee/rotate a
  trainer → crash (ML-8, fixed with heal + no-flee strategy); Scott script runs
  while state stays OVERWORLD (advance on `script.is_active`); navigate walks
  OVER door warps without triggering (step up into it discretely). Full map
  facts in design §16. Checkpoint `woods_entered.ss1` (in Woods at (17,38)).
  **NEXT: leg 3 — cross the Woods past the mandatory Aqua-grunt/researcher scene
  → north warp → Route 104 north → Rustboro (leg 4) → HM01 Cut → Gym 1.**
- **Dashboard GUI bug fixed (BOTH builds, committed `27189794`):** clicking
  "Hide" threw `_tkinter.TclError: wrong # args … raise tagOrId` from
  `_pokeball_button.lift()`. `_pokeball_button` is a **Canvas**, and Tkinter's
  Canvas aliases BOTH `.lift()` AND `.tkraise()` to `tag_raise` (raise a canvas
  ITEM, needs a tag). Fix = `tkinter.Misc.tkraise(self._pokeball_button)` (base
  widget-stacking raise). Non-fatal but noisy; fixed in sandbox+custom. The
  other `.lift()` calls in the file are on Toplevel/Frame (safe). See ML-6.
- **Petalburg→Rustboro travel — DIAGNOSED, NOT yet built.** Read the ROM
  connection graph: **Route 104 is one map ID split by the Petalburg Woods
  warp barrier**, so `navigate_to_anywhere` structurally CANNOT do
  Petalburg→Rustboro (it routes the connection graph, then fails the local path
  across the split Route 104). Must build LEG-BY-LEG through the Woods warps.
  Full verified geometry + 5-leg plan in design §16; root cause in ML-7. This
  is the immediate next build.
- **Story mode now runs a fresh game → through Professor Birch's lab** (sandbox,
  awaiting user test → promote). Full chain (verified with real battle
  listeners, ~17.5k frames): title → intro → house → clock → rival → Birch
  rescue on Route 101 → **random starter** → **first battle won** → **finish
  lab conversation** → hands to manual in the lab. `early_game.py` functions +
  StoryMode wiring. Config: `starter` (random/specific) live; `starter_nickname`
  GATED OFF (types but doesn't persist — TODO, user-deprioritised).
- **Sandbox audio off at startup** (sandbox `pokebot.py` forces `no_audio`;
  reliable regardless of launch; GUI-toggleable). Custom unaffected.
- **CHAPTER 1 COMPLETE through the rival battle (sandbox, awaiting user test →
  promote).** A fresh game now plays: intro → house → clock → rival intro →
  Birch rescue → starter → first battle → lab → **north to Route 103 (training
  en route) → grind to a random Lv 8-10 (healing at Oldale's Poké Center) →
  heal to full → beat the rival.** `travel_to_route103` + `train_lead_to_level`
  + `fight_route103_rival` in early_game.py, wired into StoryMode.
  on_battle_started returns `LevelUpLeadBattleStrategy` (fight-to-win).
  Key fixes: default strategy fled wilds (no XP); `find_closest_pokemon_center`
  is broken (hard-target `PokemonCenter.OldaleTown`); heal-to-full before the
  un-fleeable rival trainer battle. VERIFIED piecewise (fresh→lab 18.9k frames;
  route103→rival-beaten 31.1k frames). Earlier Chapter-1 parts (→lab) already
  in custom; the travel/train/rival is NOT yet promoted.
- **Pokédex sequence DONE + wired + committed** (`return_to_lab_and_get_pokedex`
  + `_navigate_through_scripts` helper): after the rival, back to Birch's lab
  (riding out the Oldale rival intercept), receive the Pokédex + Poké Balls.
  Verified (SYS_POKEDEX_GET True). StoryMode now ends cleanly at the Pokédex.
  NOT yet promoted (test then promote).
- **Pokédex sequence PROMOTED to custom** (user-tested "runs perfectly to the
  PokeDex").
- **Petalburg travel DONE + wired (sandbox)**: `travel_to_petalburg` reaches
  Petalburg — `_navigate_leg` to Oldale (past the Route 101 loop) then
  `navigate_to_anywhere(PETALBURG)`. Verified with listeners (22.1k frames).
  StoryMode now ends "reached Petalburg." NOT yet promoted (test then promote).
- **Petalburg travel PROMOTED to custom** (user-tested).
- **Chapter 2 DONE + wired (sandbox): Petalburg Gym (Dad/Norman) + Wally
  catching tutorial.** `do_petalburg_gym_and_wally_tutorial()`: enter gym → fire
  the Norman scene at (4,108) → ride out the fully-auto tutorial (Route 102
  Ralts catch + back). Completion = back in the gym + controllable after
  visiting Route 102 (NOT a flag). Verified via the listener harness. NOT yet
  promoted (test then promote).
- **CRITICAL TESTING LESSON:** test story steps ONLY via the listener-driven
  harness (build FrameInfo + call get_bot_listeners each frame, like main.py) —
  a bare `next(gen)+run_single_frame()` loop reads STALE state (no state-cache
  update) and gives WRONG results for scripted scenes. This cost hours.
- **DETECTOR BUG (low priority):** `chapters.py` Ch2 flag
  `THANKED_FOR_PLAYING_WITH_WALLY` is NOT set by the Wally tutorial — find the
  real flag (badge-anchored detection makes this low-impact).
- **Chapter 2 PROMOTED to custom** (user-tested "it worked").
- **NEXT SESSION — build Route 104 → Woods → Rustboro travel (leg-based).**
  Full verified geometry + 5-leg plan is in **design §16**; root cause of why
  `navigate_to_anywhere` fails is **ML-7**. Verified connection graph:
  Petalburg(30×30) West→Route104(offset-50); Route104(40×80) North→Rustboro,
  East→Petalburg, South→Route105; Petalburg Woods(24,11 / 48×44) has NO map
  connections (WARP-entered only); Rustboro(0,3 / 40×60) South→Route104.
  **Route 104 is warp-split by the Woods** — so travel MUST go leg-by-leg:
  (1) Petalburg west-edge exit → Route104 south [find the exact west-exit y at
  x=0; a script/wall triggers near (4,13)], (2) → Woods south warp, (3) cross
  Woods riding out the mandatory Aqua-grunt/researcher scene → north warp,
  (4) Route104 north → Rustboro south connection, (5) into Rustboro. Keep the
  battle listener attached through grass. Warps: `MapWarp` has
  `.local_coordinates` + `.destination_warp_id` (NOT `.destination_map`).
  GYM 1: Roxanne = Geodude Lv12/12 + Nosepass Lv15; starter is only Lv8-10 →
  TRAIN first; Torchic (Fire) weak vs Rock. Also need HM01 Cut. Checkpoints:
  petalburg.ss1, wally_done.ss1 (post-tutorial, in the gym at (8,1)/(4,108)).
- Iteration save-states in scratchpad: truck/house1f/house2f/clockset/
  outside_town/rival_*/birch_rescue/birch_free/first_battle/birch_lab/lab_done.

- **Story chunk B COMPLETE (sandbox, awaiting user test → promote):** a new game
  now auto-plays intro → into house → set clock → downstairs (rides Mom + the
  Petalburg-Gym TV scene) → outside → rival's house (auto mom greeting → upstairs
  → touch Poké Ball → meet the rival) → back outside. `early_game.py`
  (`walk_off_truck_and_into_house`, `go_upstairs_and_set_clock`,
  `descend_and_leave_players_house`, `visit_rivals_house`) wired into StoryMode.
  Full fresh-run verified (~11,800 frames → Littleroot (14,9), NICK/male). Map
  facts in design §14/§14.1/§14.2. Iteration uses scratchpad save-states
  (truck/house1f/house2f/clockset/outside_town/rival_* .ss1). **NEXT CHUNK:
  Route 101 → help Birch → choose starter → first battle.** Then a config pass
  (starter choice + nickname; character name already lives in `<profile>/
  story.yml`). Clock+earlier parts already promoted to custom; THIS chunk (the
  downstairs+rival additions) is sandbox-only pending the user's test.

- **PROMOTED Story Mode (chunks 1-2) to custom** after the user tested the
  intro live ("worked perfectly"). custom now has modules/story/, the StoryMode
  plugin, the title-screen selection fix (BotMode.is_selectable_from_title_
  screen + both pickers), and story tests. Verified in custom (compile, 12/12
  tests, intro smoke test → NICK/male in truck). DIVERGENCE-LOG (j) + docs
  updated. Sandbox == custom for all story files. **Next work (chunk B) starts
  in SANDBOX again** per the sandbox→promote workflow.
- **Story-mode chunk 2 BUILT: Chapter 0 New Game intro AUTOMATED.**
  `modules/story/intro.py` (`run_intro`) + `config.py` (story.yml name/gender)
  + `plugins/custom_modes/story_mode.py` (`StoryMode` bot). Drives title → New
  Game → Birch speech → gender → name → **controllable INSIDE the truck**.
  Verified on fresh throwaway profiles (boy/NICK, girl/MAY, config/ASH),
  deterministic ~4600 frames, real save untouched. Live facts → design §13.
  **NEXT CHUNK:** step off truck → room + set clock → Route 101 rescue →
  choose starter → first battle (design §6.3 step 4 / user's "chunk B").
  Intro TODO: the "existing save → Continue from title" path (intro currently
  assumes a save-less boot).
- **Story-mode chunk 1 (sandbox):** `modules/story/` read-only progress
  detector + 30-chapter registry + `tests/test_story_progress.py` (12/12).
  Badge-anchored (design §12 + ML-5). On the real save → **ch5, 1 badge**,
  flags the stray Magma Emblem anomaly.
- Story build is sandbox-only, NOT promoted. How to run: set bot mode to
  "Story" (fresh profile → intro; loaded save → detects chapter). Test harness
  pattern: `create_profile` + `LibmgbaEmulator` + drive the generator with
  `run_single_frame()` (see this session's scratch harnesses).
- Story-mode design Pass 4 → CONVERGED (see 12-STORYMODE-DESIGN §10).
- Fixed KI-8 (party strip 140→84px, no longer overlaps video) and KI-9
  (controller stuck in menu: `toggle_handheld` leaked `_gui_nav_active`; now
  cleared + gamepad uses a DERIVED gate `gamepad_gui_nav_engaged()`; added a
  "Controller GUI Control" master toggle — View menu + F10). Both PROMOTED to
  custom, live-verified on the real save (md5 identical). See 07-CHANGELOG.

## AWAITING THE USER (nothing blocked on me)
1. **PROMOTE** the sandbox batch → custom (with a promotion-time independent
   adversarial sweep; also fold in the OPEN VERIFICATION DEBT below).
2. **Ball size** — keep 140px (~2.7×) or make the left strip scrollable for a
   true 5×? (Note: #44 moved the ball to the hover, so the strip is clean now
   anyway — may be moot; confirm.)
3. **4 dex-tab decisions** (build #34/#35): (a) Pokémon dex artwork — source
   Sugimori art or reuse battle sprites? (b) item historical totals — track
   going forward/current-only/omit? (c) item map-location scope? (proceeding
   default: flavor/dims already done from ROM.)
4. **#41 honesty policy** — proceeding "show BOTH denominators" (386 National
   + 217 Emerald-obtainable) unless told to exclude. Two flagged
   uncertainties for the user: Latias-vs-Latios roamer/static (flips with the
   in-game TV answer), and Surskit (Emerald-alone unobtainable but
   record-mix swarm with a 2nd cart) — filed unobtainable; confirm.

## Next steps (in order)

**`#24` (the story auto-player) is the ONLY active work.** Everything else below is
parked and should not be started without the user asking for it.

1. DAILY upstream check at session start (CLAUDE.md ritual; last 2026-07-19).
2. **`#24-movelearn-recovery`** — the move-learn `BotModeError` is raised inside the
   battle handler, OUTSIDE StoryMode's derail-recovery scope, so a stall kills the
   run. **Killed 2 of 5 cold-start runs** — the highest-value open item. Reproducible:
   per-run stall snapshots land in `tools/story-dev/saves/stalls/`.
3. **`#24-whiteout`** — whiteout attrition is the dominant cost of the current
   strategy (the run that SUCCEEDED still took 80 whiteouts).
4. **`#24-counters` phase 2** — the chain now NAMES a reachable counter (Electrike,
   Route 118); travelling to it, catching it and training it is not built (KI-23).
5. **`#24-regionreach` gate table** — `region_reach.KNOWN_GATES` has one hand-verified
   entry, and the training-gate switch is blocked on a repro mock leak (KI-24b).
6. `#24-npcheal`, `#24-edgecost`, `#24-trainmap` `PENDING_GRASS` tiles; KI-18 live
   confirmation.
7. Next unbuilt chapters: **Mt. Pyre**, then the **Magma hideout**.

**Parked (not active):** on user "promote", merge sandbox→custom + independent
adversarial sweep + live-launch check; `#41` living-dex obtainability wiring +
auto-evolve helper; dex tabs `#34`/`#35` (blocked on the 4 decisions above);
`#27` battery-aware, `#28` mobile remote, `#42-hard` HM-gated map reachability, `#45`.

## OPEN VERIFICATION DEBT
The big promotion's #8/#12/#18/#20 + the 2026-07-19 GUI polish went to custom
with builder self-verification; a partial independent sweep on custom fixed
4 bugs (`75e02cab`). The post-#f0b275f3 sandbox batch (above) is self/fact/
live-verified but wants an independent adversarial pass at promotion time.

## How to run / test

### The bot itself
```powershell
cd custom-pokebot          # production; sandbox-pokebot = experimental
python pokebot.py                      # dashboard GUI (default)
python pokebot.py "Nick - Emerald"     # the user's real save (progressed)
python pokebot.py <profile> --classic-gui
python ..\install.py                   # setup/update/heal (custom)
python ..\install_sandbox.py           # same for sandbox
```
Story modes in the dropdown: `Story`, `Story (DEBUG)`, `Story (DEBUG - RESET)` (hard
reset → forced NEW GAME), `Story (ENDLESS RESET)` (chained reset runs in-process; set
the count from the GUI's "Endless Debug-Reset Runs…" item, 0 = forever).

### The story-bot test harness — `tools/story-dev/` (read its `README.md` first)
**Always `py -3.12` (the repo `python` is 3.9 and fails on match statements) and
`PYTHONUTF8=1`.** Full method: `PROJECT KNOWLEDGE/14-AGENT-PLAYBOOK.md`.

```powershell
# story_harness.py — the FAITHFUL main-loop harness (== the real bot's loop).
#   <state> = a .ss1 basename in tools/story-dev/saves/, a full path, or `fresh`.
$env:PYTHONUTF8=1
py -3.12 tools/story-dev/story_harness.py fresh --driver story --frames 2500000
py -3.12 tools/story-dev/story_harness.py norman_done.ss1 --driver story --build sandbox
py -3.12 tools/story-dev/story_harness.py fresh --driver storydebugreset --video
#   --video is REQUIRED to drive app UIs (PokéNav etc.) — they stall headless.

# endless_runs.py — the CLI batch runner (fresh profile per run, wall-clock +
#   log-growth stall failsafes; the GUI mode is the in-process equivalent).
py -3.12 tools/story-dev/endless_runs.py                 # 10 runs, treecko
py -3.12 tools/story-dev/endless_runs.py --count 0       # infinite (Ctrl-C)
py -3.12 tools/story-dev/endless_runs.py --count 25 --starter mudkip
py -3.12 tools/story-dev/endless_runs.py --starters all  # rotate all three

# compare_runs.py — cluster failures by signature ACROSS runs. This is the single
#   most productive debugging move in the project; a cluster of >=2 across different
#   machines/starters is the strongest evidence we act on. Reads both the harness
#   format and the in-game debug-logger format.
py -3.12 tools/story-dev/compare_runs.py tools/story-dev/night5/*.log
py -3.12 tools/story-dev/compare_runs.py --label mine tools/story-dev/night5/*.log `
                                         --label user ~/Downloads/Story_DEBUG*.log

# repro_*.py — the regression suite; run the relevant ones after any story change.
py -3.12 tools/story-dev/repro_fodder_grass.py     # prep/training decision table
py -3.12 tools/story-dev/repro_counter_plan.py     # counter-candidate ranking
py -3.12 tools/story-dev/repro_counter_wiring.py   # counter chain, all 3 outcomes
py -3.12 tools/story-dev/repro_region_reach.py     # region reachability oracle
py -3.12 tools/story-dev/repro_boss_plateau.py     # boss non-convergence detection
```

## Gotchas / unpushed work
- Tree clean, all pushed. NEVER edit `40cakes repo/pokebot-gen3/` (mirror).
- `profiles/` (incl. the user's real save) + `roms/` are gitignored — never
  commit them. The Emerald ROM IS tracked by user ruling (private repo).
- New `plugins/*.py` need `.gitignore` negations + `git ls-files` check (ML-2).
- Never `git commit` without a pathspec in automation (ML-3).
- Stock auto-updater is disabled for our root-`.git` layout (ML-4 fix).
- **Known issues: `05-KNOWN-ISSUES.md` holds 24 entries (KI-1 … KI-24b), not 6.**
  The ones that are LIVE and can cost a run:
  - **KI-17** — after-faint party-menu RESHOW freeze (HIGH; hit 2 of 5 fresh lanes).
  - **KI-18** — DOUBLE-battle replacement swap loops forever (HIGH; user-reported).
  - **KI-23** — Winona/boss-as-training-vehicle cannot converge without a TYPE
    answer; the counter chain diagnoses it but does not yet act (`#24-counters`
    phase 2).
  - **KI-24 / KI-24b** — `calculate_path` is unsound at region scale. **Partially
    fixed:** `region_reach` is wired into counter-candidate selection only;
    `_training_area_allowed` still uses `calculate_path`, so the false negatives
    are still live for training-area selection.
  Older low-severity ones still open: KI-1 (stale upstream `pokebot.spec`), KI-4/5
  (cloud-sync minor), KI-8 (mid-battle rotation party-menu stall). KI-6/7/11/14/15/16
  are fixed; KI-9/10 mitigated; KI-19 fixed-pending-wiring; KI-20/21/22 are
  decomp-verified fact dumps to read before building, not defects.
- **Mistakes: `08-MISTAKES.md` holds ~70 entries, not 7.** ML-1..ML-7 are the
  earliest (ML-6 = Canvas `.lift`/`.tkraise` both map to `tag_raise`; ML-7 = the
  global navigator can't cross a warp-split map like Route 104 through the Woods) —
  everything after them is story-bot era and is where the current traps live. Read
  the tail of the file, not just the head.
