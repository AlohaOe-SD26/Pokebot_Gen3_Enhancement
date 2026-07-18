# Custom Interface

## Native dashboard GUI (the program's own window — DEFAULT)
> ✅ User-confirmed hands-on 2026-07-18 ("worked!").

Since 2026-07-18 the bot's own window (the one the emulator embeds into)
uses the dashboard layout: `modules/gui/dashboard_gui.py`, launched by
default; `--classic-gui` restores upstream's original window (also the
place for OpenGL rendering and frame-stepping mode).

- **Layout:** resizable window; emulator video letterboxed left; tool
  column right with Controls (bot mode incl. custom modes, speed 1×–32×/∞,
  Video/Audio toggles), KPI tiles (total/shinies/phase/rate), Party (HP
  bars colored by fraction, status, shiny ✨, eggs), Status (game state,
  fps, bot message) and an Event log (shiny encounters highlighted).
- **Handheld mode (ROG Ally X):** the "Handheld mode" button, `F11`, or
  double-click on the video → true fullscreen video. A semi-transparent
  Pokéball button (top-right) or `H` opens the overlay tool drawer;
  "Hide"/`H`/`Esc` closes it; `Esc` (drawer closed) exits handheld mode.
  The mode persists per profile (`dashboard_ui.json`).
- **Stock features kept:** menu bar (save states, screenshots, reset,
  profile folder), keys.yml bindings, Manual-mode keyboard input; with
  `-d` the stock debug tabs open in a separate "Debug" window (map tab
  clicks on the video still work).
- **Verified 2026-07-18** on a real run (Emerald ROM, test-dashboard
  profile): desktop layout, F11 handheld, Pokéball → drawer, Esc-out, and
  return to desktop — all screenshot-confirmed. Not yet verified: party
  panel with a non-empty party, live encounter KPIs (needs a save with
  progress), debug window tabs.

## Web dashboard (v1 — remote viewing, opt-in)

> Part of the `custom-pokebot/` fork docs. The upstream HTTP API this builds
> on is fully documented in
> `../../40cakes repo/DOCUMENTATION/04-interfaces-gui-web-streaming.md`.

## What it is

A self-contained web dashboard served by the bot's own HTTP server —
**purely additive files** (`modules/web/static/custom-ui/`), zero upstream
code edits, no external CDNs (works fully offline).

- **Live video** (`/stream_video` multipart PNG) with a "video disabled"
  overlay + one-click re-enable (the stream silently sends nothing while
  emulator video is off — a verified upstream gotcha).
- **KPI tiles**: total encounters, shinies, phase encounters, encounters/hr.
- **Party panel**: name, level, HP bar (status-colored + numeric text),
  status-condition badge, shiny badge, egg handling.
- **Opponent card** during battles (level, nature, IV sum, shiny value).
- **Controls**: bot-mode dropdown (includes custom modes), speed
  (1×–32×/MAX), video/audio toggles.
- **Manual controller pad** (hold-to-press, pointer events) — active only
  in Manual mode, matching the API's behavior.
- **Live updates** via `/stream_events` SSE (Party, Opponent, GameState,
  BotMode, Message, WildEncounter, Map, EmulatorSettings, PerformanceData)
  with connection indicator; stats poll every 30 s as fallback.
- **Event log**: encounters (shiny highlighted), map changes, mode changes.

## How to use

1. Enable the HTTP server: in your profile (or global) `http.yml`:
   `enabled: true` (defaults to `127.0.0.1:8888`).
2. Start the bot, open **http://127.0.0.1:8888/static/custom-ui/index.html**

Dark theme by default (follows OS `prefers-color-scheme`); colors follow
the project's validated dataviz reference palette.

## Handheld mode (ROG Ally X)

Built for playing on a handheld: the emulator video goes fullscreen
(letterboxed, pixel-perfect scaling) and every tool collapses into a
slide-in drawer.

- **Enter**: the "Handheld mode" button in the video bar, double-click/tap
  the video, press `H`, or bookmark `…/index.html?handheld=1` on the
  device (boots straight into it; `&drawer=1` also opens the tools).
  Entering via button/tap also requests browser fullscreen.
- **Open tools**: tap the semi-transparent Pokéball button (custom inline
  SVG, top-right; brightens on hover/focus) or press `H`. The drawer is a
  translucent blurred panel with ALL tools (controls, pad, KPIs, party,
  opponent, event log).
- **Close tools**: the drawer's "Hide" button, `H`, or `Esc`.
- **Exit handheld mode**: double-click the video or `Esc` (with drawer
  closed). The mode persists across reloads (localStorage).

The layout is fully responsive in both modes (grid collapses to one column
under 900 px; handheld video scales to any window size).

## Files

- `modules/web/static/custom-ui/index.html` — structure
- `modules/web/static/custom-ui/style.css` — theme (light+dark, CSS vars)
- `modules/web/static/custom-ui/app.js` — API/SSE wiring (vanilla JS)

## Verification status

Tested against a mock of the bot's API (same aiohttp framework, canned
endpoint payloads shaped from the real source, live SSE + video stream) and
screenshot-verified in headless Edge: layout, KPIs, party rendering
(HP colors/status/shiny/egg), controls state, SSE indicator, video stream.
**Pending live verification** against the real bot (needs ROM + profile +
`http.yml` enabled) — POST actions (mode/speed/input) exercised only
against the mock.

## Known gaps (v2+ roadmap; upstream API limits documented in doc 04)

- No profile selection (upstream starts the HTTP server only after a
  profile loads) and no auth (upstream has none — keep it on 127.0.0.1).
- No savestate/screenshot/pause endpoints upstream — would need small
  divergence additions to `modules/web/http.py`.
- Manual pad is held-buttons only and not frame-accurate (API limitation).
- Encounter-rate trend chart, shiny log browser, PC box viewer are natural
  next panels.
