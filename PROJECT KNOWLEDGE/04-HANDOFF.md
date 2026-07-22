# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-07-22

> **NEW AGENT: read `14-AGENT-PLAYBOOK.md` right after this file.** It is the
> accumulated craft (harness, debugging method, story-mapping, faithfulness rules, bug
> patterns) — use it to build faster and prove every fix.

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

## Current state (what's WHERE)
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
1. DAILY upstream check at session start (CLAUDE.md ritual; last 2026-07-19).
2. On user "promote": merge sandbox→custom carefully + run the independent
   adversarial sweep (see debt below) + live-launch check.
3. Full #41 finish: wire `living_dex_mode` target selection to
   `obtainability.plan_for` (route gift/static/roamer to the reset modes,
   surface trade/event/unobtainable) + an auto-evolve helper.
4. Dex tabs #34/#35 once the 4 decisions land.
5. Remaining first wave: #27 battery-aware (Ally), #28 mobile remote;
   then #42-hard (HM-gated map reachability), #24 story auto-player (+#45).

## OPEN VERIFICATION DEBT
The big promotion's #8/#12/#18/#20 + the 2026-07-19 GUI polish went to custom
with builder self-verification; a partial independent sweep on custom fixed
4 bugs (`75e02cab`). The post-#f0b275f3 sandbox batch (above) is self/fact/
live-verified but wants an independent adversarial pass at promotion time.

## How to run / test
```powershell
cd custom-pokebot          # production; sandbox-pokebot = experimental
python pokebot.py                      # dashboard GUI (default)
python pokebot.py "Nick - Emerald"     # the user's real save (progressed)
python pokebot.py <profile> --classic-gui
python ..\install.py                   # setup/update/heal (custom)
python ..\install_sandbox.py           # same for sandbox
```

## Gotchas / unpushed work
- Tree clean, all pushed. NEVER edit `40cakes repo/pokebot-gen3/` (mirror).
- `profiles/` (incl. the user's real save) + `roms/` are gitignored — never
  commit them. The Emerald ROM IS tracked by user ruling (private repo).
- New `plugins/*.py` need `.gitignore` negations + `git ls-files` check (ML-2).
- Never `git commit` without a pathspec in automation (ML-3).
- Stock auto-updater is disabled for our root-`.git` layout (ML-4 fix).
- Known issues: KI-1 (stale pokebot.spec), KI-4/5 (cloud-sync minor),
  KI-6 fixed (two-row tab bar). Mistakes: ML-1..ML-7 in 08-MISTAKES
  (ML-6 = Canvas .lift/.tkraise both = tag_raise; ML-7 = global navigator
  can't cross a warp-split map like Route 104 through the Woods).
