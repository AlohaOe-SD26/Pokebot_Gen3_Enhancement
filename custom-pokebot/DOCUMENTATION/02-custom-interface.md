# Custom Interface — web dashboard (v1)

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
