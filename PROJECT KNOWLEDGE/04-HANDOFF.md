# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-07-18

## What this project is
Documents and enhances 40Cakes/pokebot-gen3 (Python shiny-hunting bot
driving Gen-3 Pokémon games via libmgba). Layout (user directive — details
in CLAUDE.md "Project rules"):
- `40cakes repo/pokebot-gen3/` — PRISTINE upstream mirror (git subtree,
  remote `upstream-pokebot`, upstream commit `5dd898f8`). Checked against
  upstream DAILY; sync record: `40cakes repo/UPDATE-LOG.md`.
- `40cakes repo/DOCUMENTATION/` — complete, adversarially verified dev docs
  of the ORIGINAL program (superseded versions go to `_history/`).
- `custom-pokebot/` — OUR fork; every divergence logged in
  `DIVERGENCE-LOG.md`, custom docs in its `DOCUMENTATION/`.
- `Pokemon_Emerald_AI_Notes.md` (root) — transfer notes for the sibling
  Pokémon Emerald AI project.

## Current state
- **#5 custom interface — the program's OWN WINDOW is now the dashboard**
  (user direction 2026-07-18): `custom-pokebot/modules/gui/dashboard_gui.py`
  (`PokebotDashboardGui`, default GUI; `--classic-gui` = upstream window,
  also home of OpenGL/frame-stepping). Resizable letterboxed video + tool
  column (mode/speed/AV, KPI tiles, party HP bars, status, event log);
  handheld mode for ROG Ally X (F11/H/double-click → fullscreen; canvas
  Pokéball opens overlay drawer; Hide/H/Esc closes; per-profile
  persistence in `dashboard_ui.json`). Stock menu bar kept; `-d` debug
  tabs open in a separate Toplevel. VERIFIED on a real run with the
  Emerald ROM (test-dashboard profile, title screen): desktop, handheld,
  drawer, Esc-out, and `--classic-gui` regression all screenshot-confirmed.
  **FLAGGED TO REVIEW (user, 2026-07-18): approved from screenshots only —
  hands-on visual test still pending; clear this flag (and the matching
  ones in 03-PUNCH-LIST and custom-pokebot/DOCUMENTATION/02) after it.**
  Not yet verified: party/KPI panels with a progressed save; debug
  Toplevel tabs; the user's on-device Ally test. Browser dashboard
  (`modules/web/static/custom-ui/`) remains as opt-in remote viewing
  (auto-open plugin defaults OFF).
- **#4 installer — DONE (V2, 2026-07-18)**: `install.py` = the CUSTOM
  bot's one-script setup/update/heal per user spec: 7 fault-isolated
  steps, ✓/⚠/✗ summary + exit codes, full trace to `install.log`
  (gitignored), full-repo self-heal (incl. quoted-path fix), ROM step
  (whitelist-verifies repo ROM / sideloads a .gba placed next to the
  script), incremental updates (never re-downloads the repo). All paths
  tested on this machine; user confirmation of a real-world run pending.
- **#3 custom automations — WIP**: framework + "Patrol (Custom)" built,
  real-import verified; awaiting the user's in-game play-test.
- requirements.py (fork) now installs only missing modules; cffi pin
  loosened to `>=1.17.1` (upstream conflict); http.yml template defaults
  enabled (127.0.0.1).

## What was just done (this session, 2026-07-18)
- Daily upstream check (unchanged at `5dd898f8`); pulled the user's ROM
  upload; user ruling logged to keep it tracked.
- Smart dependency bootstrap + dashboard discoverability fixes.
- Built the native dashboard GUI (fork agent; ~860 lines) and verified it
  on a live run; browser auto-open defaulted off per user preference.

## Latest (2026-07-19) — #41 obtainability RESEARCH HALF done (sandbox)
- Compiled + fact-checked the Emerald gift/static/roamer/in-game-trade/event/
  breeding/special/unobtainable lists against the BPEE0 ROM's own `gWildMonHeaders`
  (authoritative — the encounter-index cache is complete) + Bulbapedia, and folded
  them into `modules/obtainability.py` via `modules/data/emerald_obtainability.json`.
- CENSUS (sums to 386): wild 132 / evolution 149 / gift 7 / static 8 / roamer 1 /
  event 6 / breeding 3 / special 1 / unobtainable 79. Second honest denominator:
  **217/386 obtainable in Emerald without trading**. Both denominators exposed to
  the GUI. 16/16 units (`tests/test_obtainability.py`). Full lists + citations +
  validation report: 11-LIVINGDEX-DESIGN.md (Phase #41-research).
- NOT yet done for full #41: wire `living_dex_mode` target selection to plan_for's
  `wild_huntable` gate (route gift/static/roamer to the reset modes; surface
  trade/event/unobtainable instead of silently skipping); auto-evolve helper. This
  pass was pure-data, validated against the ROM header + cache (no emulator boot).

## Awaiting the USER (nothing blocked on me)
- **Promotion OK** for the sandbox batch #30/#31/#32 (verified clean) +
  #33 (GUI fixes) → promote to custom on the user's word.
- **4 dex decisions** (steer Phase 3, see 10-DEX-RESEARCH.md / punch #34-#35):
  (1) Pokémon dex artwork — source Sugimori art or reuse battle sprites?
  (2) flavor text + height/weight/category from the decomp — yes?
  (3) historical item totals — track going forward / current-only / omit?
  (4) item map-location scope — full Emerald or a subset?
- **Past-the-menu SAVE** from the user → unblocks live tests (filled-slot
  party composites, hover stats with real data, money cheat in-game,
  caught/shiny dex counts, controller feel on the Ally).

## In progress (and how far along)
- SANDBOX now holds a LARGE unpromoted, self-verified batch (2026-07-19),
  awaiting the user's review/promotion + a progressed save for live tests:
  #30/#31/#32/#33 (GUI + money cheat, adversarially verified clean), #22
  Watchdog, #9 Hunt Planner v1+v2, #23 Living-Dex Orchestrator, #11
  Analytics. Each has unit/fact-check/screenshot verification; live in-game
  behavior + a promotion-time independent adversarial pass are pending.
- DEX DATA (#34/#35): Phases 1, 2, 3a DONE. pokedex_data.json is complete
  EXCEPT dex_artwork (386 species w/ full stats/learnsets/flavor/dims).
  itemdex_data.json has core data; gaps = map_locations/mart/pickup/
  historical. Phase 3b + the two GUI tabs BLOCKED on the 4 user decisions.
- (older #34/#35 line retained below) Phase 1 (research/inventory) + Phase 2 (assemble +
  fact-check the static datasets: 386 species / 309 items, integrity PASS)
  DONE in sandbox (`d6211e32`; build_dex_data.py + modules/data/generated/).
  Phase 3 (fill gap fields: dex artwork, flavor/height/weight, item
  locations) BLOCKED on the 4 user decisions above. Phase 5 = build the
  two GUI tabs on the data.
- PROMOTION DONE 2026-07-19 (`f0b275f3`): the ENTIRE sandbox round is now in
  custom-pokebot (user approved "all updates"): backup/restore + cloud,
  macros, Patrol v3 (multi-map/global-nav), gamepad + handheld menu-hide,
  shiny alerts, update notice, cloud save-sync v2 (off by default), game
  cheats, tabbed GUI + XP bars + topmost dialogs + full-dex sprite picker.
  Verified: import/discovery/install-check/live-launch. Also fixed the
  stock-updater footgun (ML-4) in custom + sandbox. sandbox-pokebot retained
  (now == custom) for future rounds.
- OPEN VERIFICATION DEBT (punch-list "Now" item #V): #8/#12/#18/#20 + the
  2026-07-19 GUI polish were promoted with builder self-verification only —
  run an independent adversarial sweep on custom before relying on them
  (cloud-sync is off by default, so inert). Twice interrupted by credit limits.
- #30/#31/#32 BUILT + ADVERSARIALLY VERIFIED in sandbox (2026-07-19, clean:
  money byte-safe 56/56, GUI-nav 28/28, no code bugs): (#30) persistent
  Handheld button + handheld menu→Play-tab GAME MENU + Left Party Section
  (ball-behind composites) + hover-stats tooltip; (#31) adjustable money +
  Lock; (#32) gamepad-driven GUI navigation (drawer-open → controller
  drives the dashboard; focus ring; party-slot focus pops the tooltip).
  AWAITING USER OK to promote to custom (last commits 78715773 / 78bfef1a).
- FIRST-WAVE features agreed (punch-list "Next"): #22 watchdog → #9 hunt
  planner + #23 orchestrator → #25 detail/box viewer + #11 analytics →
  #27 battery-aware + #28 mobile remote. Full idea catalog: 09-FEATURE-BRAINSTORM.md.
- USER IN-GAME TESTS still pending on the promoted features (cheats on a
  real save, macro record→replay, multi-map patrol walk, shiny alert/backup,
  gamepad on the Ally, cloud-sync desktop↔Ally).
- (historical) #7 SANDBOX ROUND (A1-A4) — BUILT + ADVERSARIALLY VERIFIED
  (16 bugs found and fixed, 2 critical — see ML-3 and SANDBOX-NOTES).
- ROUND 2 (roadmap items, all in sandbox, all committed+pushed):
  - #10 gamepad + handheld menu-hide (293854d3) — self-verified, user
    testing gamepad now.
  - #8 warp-aware global pathfinding (58a044fd) — self-verified (real-ROM
    graph extract 518 maps/1268 warps, 23/23 checks).
  - #12 shiny alerts + #18 update notice (58803096) — self-verified,
    real toast fired.
  - #20 cloud save-sync v2 (791b8d62) — self-verified via two-machine sim
    (its own battery caught 2 data-safety bugs, fixed pre-commit).
  ⚠ NOT YET INDEPENDENTLY VERIFIED: the adversarial verification pass for
  #8 and for #12/#18/#20 was STARTED but both verifier agents died on an
  API usage-credit limit (2026-07-18) before finding/fixing anything.
  Per ML-3, treat these four features as UNVERIFIED (self-tests are not
  sufficient). NEXT SESSION FIRST TASK: re-run the two adversarial
  verifiers (warp slice: warp_graph.py/global_navigation.py/patrol.py;
  alerts/update/sync slice: shiny_alert_plugin/update_check/cloud_sync +
  dashboard_gui) before promoting anything to custom-pokebot.
  Punch-list icebox carries the remaining roadmap (#9,#11,#13-#17,#19).
  All four items (A1 backup/restore + local/GitHub/synced-folder cloud, A2
  macro record/replay, A3 multi-map Patrol, A4 GUI pack incl. scrollable
  tool column, party sprites, shiny log) are built, machine-verified, and
  pushed (commits 2e933129, 2124b20e/38a0e207, 8f605513, 02057b26).
  Status + honest caveats: `sandbox-pokebot/SANDBOX-PROPOSALS.md` (top
  block); per-item detail in `sandbox-pokebot/SANDBOX-NOTES.md`. USER
  REVIEW PATH: `python install_sandbox.py` → launch sandbox → test with a
  real save (macro record→replay, shiny backup trigger, multi-map patrol,
  party sprites with a real party). Then: approve items → promote into
  custom-pokebot (rule C in proposals); pick next items from proposals
  section B. Promotion needs explicit user OK per item.
- #5/#4 CONFIRMED WORKING by user hands-on 2026-07-18 ("worked!") — flags
  cleared. #3 Patrol still awaiting explicit user play-test.

## If stopped mid-task
- Nothing pending — last stop was clean.

## Next steps (in order)
1. DAILY (every new calendar day, session start): upstream update check —
   ritual in CLAUDE.md "Daily upstream update check" / UPDATE-LOG.md header.
2. User tests the native GUI (`cd custom-pokebot; python pokebot.py` →
   dashboard window; F11 for handheld on the Ally) with a real save, and
   play-tests Patrol (#3): grassy map + `patrol.yml` (2-3 waypoints) in the
   profile folder + select "Patrol (Custom)". Fix whatever they report.
3. After user sign-off: mark #3 done and #5's native-GUI milestone done;
   then #5 v2 backlog (trend charts, shiny log browser, API additions) and
   #6 icebox.

## How to run / build / test
```powershell
cd custom-pokebot                      # our fork ("40cakes repo/pokebot-gen3" = pristine upstream)
python pokebot.py                      # dashboard GUI (native); profile GUI on first run
python pokebot.py <profile> --classic-gui   # upstream's original window
python pokebot.py --headless --no-video
python -m unittest discover tests      # needs specific ROM dumps in roms/
python ..\install.py                   # from repo root: update + heal + deps
```

## Gotchas / unpushed work
- The user's Emerald ROM is TRACKED in the (private) repo by explicit user
  ruling (2026-07-18, see 06-DECISIONS-LOG) — do not remove it and do not
  re-raise; but never commit any additional ROMs/saves/profiles.
- NEVER edit files under `40cakes repo/pokebot-gen3/` — pristine mirror;
  all enhancement work happens in `custom-pokebot/`.
- New files under `custom-pokebot/plugins/` need .gitignore negations and
  a `git ls-files` check (ML-2).
- Upstream pull (daily ritual, mirror only):
  `git subtree pull --prefix="40cakes repo/pokebot-gen3" upstream-pokebot main --squash`
- Upstream's `pokebot.spec` (PyInstaller) is stale/broken (KI-1); the
  bot's auto-updater self-disables for git checkouts (good for us).
- A gitignored `test-dashboard` profile exists locally for GUI testing.
