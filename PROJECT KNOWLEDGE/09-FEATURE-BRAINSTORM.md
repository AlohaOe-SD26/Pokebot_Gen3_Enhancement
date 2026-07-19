# Feature Brainstorm — 2026-07-19
> A curated menu of enhancement ideas to review together, then promote the
> agreed ones into `03-PUNCH-LIST.md`. Grounded in what the bot can already
> do (memory read/write, frame control, the BotMode framework, the HTTP
> API, cheats/backups/macros/global-nav we just built). "PL#" = already on
> the punch list. ★ = my top recommendations.

## A. Smarter bots & automation
- ★ **A1. Living-Dex / hunt-queue orchestrator** — give it a target list; it
  auto-picks the right mode + location per species (uses Hunt Planner PL#9
  + global pathfinding PL#8) and moves between hunts autonomously. The
  "ultimate idle game" — set 50 targets, walk away. (L)
- ★ **A2. Story auto-player (trainer/gym battler)** — a mode that actually
  progresses the game: beat trainers/gyms with the existing battle engine,
  navigate routes via global nav. Turns "get a save to a hunt spot" into a
  one-click bootstrap. (L)
- **A3. Box manager / auto-release** — during long hunts, auto-release or
  auto-sort PC boxes by IV/nature/shiny filters so a full box never stalls
  a hunt. Directly prevents a common 24/7 failure. (M)
- **A4. Egg-hatch optimizer** — daycare + bike loop with auto-keep/release
  by IV/nature filter and auto-box management (extends the daycare mode). (M)
- **A5. Catch profiles** — named, per-hunt catch strategies (ball logic,
  false-swipe, status, HP thresholds) selectable in the GUI. (M)
- **A6. Nuzlocke assistant** — enforce/track nuzlocke rules (first-encounter
  per route, faint=release). Niche but fun. (M)

## B. GUI / UX
- ★ **B1. Pokémon detail + PC box viewer** — click a party/box mon → full
  panel (IVs, nature, ability, moves, ribbons); browse all PC boxes with
  sprites. High-value, uses data we already read. (M)
- ★ **B2. Theme system** — selectable color themes (dark variants, light,
  custom accent) from the GUI; the palette is already centralized. (S-M)
- **B3. Goals / session-target panel** — set a goal (N encounters, catch X,
  reach a phase) with progress bars + ETA. (S-M)
- **B4. Customizable layout** — reorder/hide tabs & cards; save per profile. (M)
- **B5. In-GUI log viewer** — read logs/*.log (bot/backup/cheats) in the GUI
  for troubleshooting without hunting through files. (S)
- **B6. First-run setup wizard** — guided ROM pick + profile create + basic
  config; lowers the barrier for a fresh install. (M)
- **B7. Keybinding + gamepad-mapping editor** — remap in the GUI (keys.yml
  and the new gamepad map are yaml/code-only today). (M)
- PL#14 Profile manager UI · PL#15 Config editor GUI · PL#19 Overlay themes.

## C. Data & analytics
- ★ **C1. Analytics suite (PL#11, expand)** — stats browser (sortable
  per-species table), encounter-rate trend sparkline, phase history, plus a
  **luck meter** (actual vs binomial-expected shiny odds) and per-method
  odds. (M)
- **C2. Shiny gallery** — a visual wall of every shiny caught (sprite, IVs,
  date, phase length), exportable. (S-M)
- **C3. Hunt summary cards** — auto-generate a shareable image on each shiny
  (like the Discord embed, but savable/local). (S-M)
- **C4. Cross-session history** — long-term charts from stats.db; cloud-sync
  stats too (extends PL#20 to stats.db). (M)
- **C5. CSV/JSON export & reporting** — export any stats view. (S)

## D. Integrations / connectivity
- ★ **D1. Polished mobile remote** — a phone-optimized view of the web
  dashboard (already responsive) to monitor 24/7 hunts from anywhere. Pure
  win on the existing HTTP API. (M)
- **D2. Stream chat integration (Twitch/YouTube)** — !stats / !shiny chat
  commands + shiny shout-outs; the bot is built for 24/7 streams. (M-L)
- **D3. Generic outbound webhooks** — fire on any event (beyond Discord) for
  user automations / IFTTT-style hooks. (S-M)
- PL#16 PKHeX quick-export.

## E. Robustness / 24-7 ops (high value for unattended hunting)
- ★ **E1. Watchdog / auto-recovery** — detect "stuck" (no encounters in N
  min, softlock, crash) and auto-recover: reload savestate / restart / drop
  to a safe state + alert. The single biggest reliability win for 24/7. (M)
- **E2. Crash-safe savestate ring** — periodic rolling savestates + auto-
  resume after a crash (complements backups). (S-M)
- **E3. Health monitor** — fps/memory/enc-rate anomaly detection with
  alerts ("idle 10 min", "fps dropped"). (S-M)
- **E4. Scheduled hunts** — time-boxed plans ("hunt X until 6pm, then Y"). (M)

## F. Handheld / ROG Ally specific
- ★ **F1. Battery-aware mode** — on the Ally, throttle speed/fps on low
  battery, pause on critical, resume on charge. Practical for real handheld
  use. (S-M)
- **F2. Gamepad-driven GUI** — navigate tabs/cheats/menus with the
  controller, not just the game (couch-friendly). (M)
- **F3. Handheld UI scale** — larger touch targets / a dedicated handheld
  scale toggle for the 7" screen. (S)

## G. Advanced / power-user
- **G1. RNG manipulation mode (opt-in)** — deterministic shiny/IV via seed
  manipulation. Upstream deliberately avoids this; ship as an explicit,
  clearly-labeled cheat-adjacent opt-in. (L)
- **G2. Cheat presets & scheduling** — save/name cheat combos; time-based
  cheat toggles. Extends the cheat menu. (S)
- **G3. Plugin marketplace/loader UI** — enable/disable community plugins &
  custom modes from the GUI (we already have the drop-in framework). (M)

---
## My recommended first wave (for discussion)
If it were my call, I'd sequence: **E1 watchdog/auto-recovery** (makes 24/7
trustworthy) → **PL#9 hunt planner + A1 orchestrator + PL#8 nav** (the idle-
game payoff, and #8 is already built) → **B1 detail/box viewer** + **C1
analytics** (make the data shine) → **F1 battery-aware** + **D1 mobile
remote** (Ally quality-of-life). A2 story auto-player is the most ambitious
but the most transformative.
