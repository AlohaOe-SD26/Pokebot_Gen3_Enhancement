# Backlog round 3, angle 2: DEPLOYING the finished AI agent (USER RULINGS 36, 37, 41)

Date 2026-10-19. A NOTE, not truth (ai-research-notes rule). Read-only research; nothing was run. Every "found" line below was
read from the file named; every "estimate" is marked. Grounds: design draft sections 2.4 and 11, `ai_player/host/*` docstrings,
`ai_player/gates/check_purity.py`, `sandbox-pokebot/{pokebot.py,modules/roms.py,modules/profiles.py}`,
`REFERENCE-INSTALLER-PATTERN.md`, `06` rulings 36, 36-addendum, 37, 41 and the 2026-07-18 / 2026-08-23 ROM rulings.

## 0. Bottom line

The seams for a standalone program already exist (launcher = the swap point, eyes and controller = the two adapters, one
verdict-file exit door). What is MISSING is everything around the AI that a friend's PC needs and this PC hides: where files
live, a ROM the user brings, a settings file, a place for the API key, and a build that cannot carry the ROM. Most of the
choices below cost a few dozen lines TODAY and are expensive to retrofit once saves, memory and settings exist in the wild.
Build the wizard, installer and crash reporter LAST; make the data-shape decisions (D1-D8) NOW.

## 1. Traps found (this PC's setup that a friend's PC would not have)

- **T1. The stock updater turns ON in a non-git install.** `pokebot.py:231-238` runs `run_updater()` unless the install is
  bundled or has a `.git` in an ancestor folder. This PC has one, so it never fired. A friend's copy has none, so upstream's
  updater would offer a 40Cakes release zip over our fork. (Read from the code, not run.) Fix without editing the framework:
  the installer creates an empty `.git` folder at the install root, which the fork's own check honours; proof = a clean-folder
  start with the network off that shows no updater prompt. Alternative: a one-line DIVERGENCE-LOG entry in `pokebot.py`.
- **T2. A profile cannot be created without a donor.** `launcher.py:89,145-165` copies `metadata.yml` from a donor profile
  (`PREFERRED_TEMPLATE = "endless-P1-torchic"`, else the first profile found, else error). A friend has none. The metadata is
  four fields (`file_name`, `game_code: BPE`, `revision: 0`, `language: E`), so generate it from the ROM's header instead.
- **T3. The repo is the wrong thing to hand a friend.** The Emerald ROM is tracked in the private repo (rulings 2026-07-18 and
  2026-08-23, "Do not re-raise for THIS file"; each says revisit if the repo ever goes public), 327 `.ss1` save states are tracked,
  and `ai_player/gates/fixtures/` holds 48 files (7.3 MB, many `.ss1`). Those rulings cover the REPO. They say nothing about a
  distributable, so the artifact needs its own rule (D9). Giving a friend repo access is, in effect, giving them the ROM.
- **T4. About 25 `AI_PLAYER_FAULT_*` / control switches are read from the environment by the production code path**
  (`options.py`; the fault arms need that). On a friend's PC a stray variable could switch on a fault arm mid-game. The deploy
  launcher must scrub them (D6).
- **T5. One-file base64 installer will not hold the program.** Measured `du`: `sandbox-pokebot/mgba` 30 MB, `modules` 79 MB
  (not broken down; I did not check how much is pycache or data), `ai_player` source about 2 MB without `gates/fixtures`.
  The pattern's reference installer had 48 text files. Source fits; the mGBA binaries probably do not (D10).
- **T6. The brain cannot reach the network, by design.** `check_purity.py` `LIBRARIES` is an allowlist and my grep for
  `socket|urllib|requests|http|anthropic` found no network module in it. Good: it means the production consult MUST be
  host-side, and the brain must only ever see validated plain data (D7).
- **T7. A cap held in memory resets on restart.** `ai-agent/consult.py` already avoids this (`_calls_today` reads its log). The
  production consult must do the same, and for dollars as well as calls (D7).

## 2. Decisions to make NOW (cheap now, costly after friends have data)

**D1. One `AppPaths` module; no path literal anywhere else.** Four classes of data with four owners: PROGRAM (installer-owned,
hash-checked, replaceable), KNOWLEDGE (ships with the program, read-only: `ai_player/knowledge/*`), USER DATA (never touched by
the installer: `settings.json`, `roms/`, `profiles/`, `memory/`, `runs/`, `consult_ledger.jsonl`, `crash-reports/`), and the KEY
(not in any folder, D7). Default layout: a portable folder `EmeraldAI/` with `program/` and `data/` side by side (delete the
folder = uninstall; back up = copy `data/`), with an `AI_PLAYER_HOME` override. The launcher's dev default
`<repo>/sandbox-pokebot` stays as the dev resolver only. Gate: no `sandbox-pokebot`, `C:/`, `Remote Projects` or
`endless-P1` outside the dev resolver. Cost: about 60 lines.

**D2. Version every user-data file; refuse a NEWER one, never rewrite it.** Each of `settings.json`, the memory files, the ledger
and the profile marker carries `schema_version`. An older program that meets a newer version stops with a plain message instead
of "fixing" it; a newer program migrates forward only, after copying the old file to `data/backup/<date>-<version>/`. This single
rule is what makes rollback safe, and it cannot be added after the first friend's memory file exists. Fault arm: hand-edit a
future version in, expect a refusal and a byte-identical file.

**D3. ROM intake: the user supplies it, we check the hash, we never ship, upload or log it.** `ai_player rom add <file>`:
SHA-1 must equal `f3ae088181bf583e55daf962a92bb46f4f1d07b7` (Emerald USA/Europe, the dump the 2026-08-23 ruling calls "the dump
the program is built to load"). `modules/roms.py` whitelists other Emerald dumps (German, French, Italian, Japanese, Spanish) plus
Ruby, Sapphire, FireRed and LeafGreen, but the AI's knowledge and address tables were built and tested on the English one, so
refuse the rest with a plain sentence ("this is a French Emerald; this version plays the English one"). Do not try to repair
headered or zipped ROMs: say what is wrong. Copy the file into `data/roms/`, record only its hash in settings, write the profile's
`metadata.yml` from the header (fixes T2). Fault arms: wrong hash, truncated file, a zip, a Ruby ROM.

**D4. Profile = one playthrough = one save.** The cartridge save (`current_save.sav`) is the durable truth; `.ss1` states are tied
to the exact emulator build and ROM, so they are a convenience, never the only copy. Keep a rotating `.sav` backup (say the newest
10, every in-game save and before every update). `--fresh` on an existing profile must not silently wipe it: in deploy mode "new
game" makes a NEW profile name, and "retire" archives rather than deletes. Keep the existing `.ai_player_profile` marker rule
(`seed_profile` refuses to change a profile it did not create). Resume after a crash comes from the `.sav`/state, via the
supervisor already listed as round-2 R15.

**D5. Personality: a setting with a cycle mode.** `personality: random | catcher | story | trainer | cycle`, plus `seed: auto | N`.
`cycle` takes the next archetype for each NEW playthrough (a counter in `data/`), matching "personas cycle" (ruling 40). Log both
in the run card. Be honest in the docs that a seed reproduces the AI's CHOICES, not the game's own RNG (KI-112 / backlog B6).

**D6. Two front doors: `play` (deploy) and `run` (dev, today's).** `play` reads only `settings.json`: a JSON file with `_help`
keys, the format the learner's `config.json` already uses and the user already knows. Defaults live in code; a missing or corrupt
file means defaults plus one warning line, a bad value names the file and key, unknown keys are warned about. The launcher turns
settings into the `AI_PLAYER_*` variables the brain reads (so `options.py` does not change), and in `play` mode it SCRUBS every
`AI_PLAYER_FAULT_*` and control switch from the child's environment (fixes T4; extends `UNTRUSTED_ENV`). Settings: ROM hash,
profile, personality, seed, speed (1x / 2x / unthrottled), display (window / headless), audio, session limits (hours, stop at
badge N or Champion), consult block (D7), retention (D8), log level. Sensible default for the art-piece use: visible window, 1x.

**D7. The optional consult: host-side, key-isolated, capped by a ledger.**
- *Boundary:* one `Coach.ask(request) -> plan | None` interface (design draft 2.4); transports `cli` and `mailbox` (dev, no key)
  and `api` (production). The API transport lives in a host-side process or thread, because the brain cannot import network
  code (T6) and must not hold a secret. The brain gets validated plain data, rejects invalid steps (the draft's rule), and never
  waits: timeout, 401, 429, no network and garbage JSON all mean "continue on the current goal".
- *Key:* never in `settings.json`, a run folder, a log, an exception text, a crash report or git. Read from the
  `ANTHROPIC_API_KEY` variable first, else the Windows Credential Manager (a `consult setup` step that asks once and stores it
  there), else ask each launch without saving. Strip it from the BRAIN child's environment (it lives in the launcher side only).
  A log writer that sees `sk-ant-` replaces it. Fault arm: plant a key, trigger an error in every log path, a crash report and a
  bundle build, and grep all output for it.
- *Toggle and consent:* OFF by default; ON needs a key present and a typed confirmation that calls spend the user's own money.
- *Cap:* `consult_ledger.jsonl` in user data, read back on start (T7). Limits: calls per day, dollars per call, dollars per
  month, dollars total. Reserve the worst-case cost BEFORE the call and settle from the response's reported token usage, so a
  failed or overlapping call cannot overshoot. At the cap the AI plays on and logs that it stopped asking. Keep model name and
  price table in a data file, not in code (model ids change).
- *Standing setup prompt:* a versioned file `consult_prompt.md` in KNOWLEDGE (the game, the AI's goals and personality, the state
  digest, the allowed intent vocabulary, the reply schema, "answer short, never give button presses"). Each request log records
  its hash. Text the AI reads in the game goes into a fenced block and is treated as data. Ruling 37 Q5 caps (about 20 calls a
  day, at most $0.50 each, Opus escalations capped and logged apart) become the shipped defaults, not constants.
- *Dev stays free of keys:* the mailbox / `claude` CLI path and `DEVELOPER-NOTES.md` flow are unchanged (ruling 36 addendum).

**D8. Resource and disk limits as settings with defaults, because a friend's PC is not this PC.** Run at below-normal priority;
a hard wall clock per session (exists: soft deadline, then the launcher's kill); a retention policy for run folders
(`disk_budget.py --profiles --keep-newest 12` is the test-side version; promote it to a runtime rule with a size cap of its own);
cap `actions.jsonl` (the full-observation records are the bulk; I did not measure a whole-game run, so measure one before
choosing numbers; the sweeps measured about 8 MB a run); refuse to start under N GB free (`disk_budget.py` already refuses at 30
for sweeps; a player needs a smaller number). Memory use is not measured here; the learner budgets about 1.5 GB per lane.

**D9. The artifact is built from an ALLOWLIST and a gate refuses to emit it if it carries a forbidden byte.** The build lists
files explicitly (the installer pattern's `FILES` dict is already that idea), never a folder copy. The gate fails on any `.gba`,
`.sav`, `.ss1`, `roms/`, `profiles/`, `tests/states/`, `gates/fixtures/`, anything containing the header string `POKEMON EMER`
with game code `BPEE`, anything matching `sk-ant-`, and any path outside the list. Fault arms: drop a ROM, a state and a fake key
into the tree and see each one stop the build. Note what must still ship because the launcher runs it: the purity gate
(`gates/check_purity.py`, run before every launch, exit 7 on FAIL) and the instrument; the other gates and fixtures stay home.

**D10. Packaging choice, made now, built later.** The user's installer pattern (one `install_*.py`, embedded files, SHA-256
drift check, `PROTECTED` set, `SCRIPT_VERSION` as `YYYY-MM-DD-DESCRIPTOR-VN`, "healing" re-runs) is the right model for SOURCE.
Because of T5, recommend: the installer embeds the Python source and a manifest, and takes the large binaries from a hash-pinned
release archive that sits beside it (or that the user chooses to host); it verifies every SHA-256 before writing. `PROTECTED` =
all of `data/`. A PyInstaller bundle is a possible later form (`pokebot.spec` and `is_bundled_app()` exist); keep it possible by
reading data through `AppPaths` and never from `__file__`-relative paths.

**D11. Updates and rollback with no phone-home.** The only network traffic the program ever makes is the opt-in consult. Updating
= running a newer installer the user sends (the pattern's healing run). Before replacing a changed program file the installer
copies it to `program_backup/<old SCRIPT_VERSION>/` (keep the newest 2); rollback = re-run the older installer, safe because of D2.
`ai_player doctor` prints: installed version, files whose hash drifted, Python version, ROM hash OK, free disk, key present
(yes/no only), network reachable (only if the consult is on). Verification pass: an interrupted install must heal on re-run.

**D12. Crash reports the user can send, built by a command, never uploaded.** `ai_player report` writes
`data/crash-reports/<date>-exit<N>.zip`: the last 2,000 lines of `ai_player.log`, the verdict file, the `[AI-EXIT]` line, the last
200 action records WITHOUT full observations, the heartbeat lines (map, position, party), version and drift list, OS and Python
versions, and settings with the key and the user's profile path redacted. Never the ROM, saves, states, key or the user name.
Map each exit code (0, 2, 3, 6, 7, 8, 9, 124, 130) to one plain sentence and a next step. Fault arm: plant a fake key and the
Windows user name everywhere, build the zip, grep it.

**D13. The host layer stays swappable: write the contract down and test it with a fake host.** Today the framework imports sit in
`host/` only (about 14 framework symbols: `context`, memory and symbol reads, `get_player`, party and species decoders, bag,
pokedex, map objects, battle state, `modules.main` for the listener rebuild). A different host (the mGBA Python bindings
directly, which `sandbox-pokebot/mgba/` already contains) would need: read memory and symbols, press buttons and advance a
frame, a frame counter, save/load state, ROM load, and a window or headless switch. It would NOT need `isolation.py`, the
listener rebind, the HTTP forcing, the profile marker or the stock updater, which exist only to contain the framework. So now:
(a) write the host contract as a short Protocol in one file and tag each `host/` file FRAMEWORK-ADAPTER or NEUTRAL; (b) add a
`FakeHost` conformance test that runs the brain through the contract with no framework import (the existing harnesses may
already be most of this: check before building). Do NOT rewrite the host now. Open question for later: a framework-free host
would drop the GPL surface and the HTTP server, but the party, bag and map decoders would have to be rebuilt, and the cost is
unmeasured.

## 3. Legal and safety (notes for the user, not legal advice)

- **ROM:** never distributed, never uploaded, never in a bundle or report (D3, D9, D12). Each friend supplies their own dump.
- **Saves and states** contain game memory: treat like the ROM (not in the artifact, not in reports).
- **GPL-3.0:** `sandbox-pokebot/LICENSE` is GPL-3.0 and `ai_player` imports the framework, so what friends receive is a combined
  work. Python source ships anyway, so the obligation is simple to meet: ship the source, keep `LICENSE` and a `NOTICE`
  (upstream 40Cakes credit; the mGBA library is MPL-2.0). Do not hand out a compiled-only build without the source.
- **Sprites and game data:** the framework carries game artwork. Upstream distributes it, but list it in `NOTICE` and keep the
  program's name neutral (not a Pokemon trademark).
- **Secrets:** no key in files, logs, git or the artifact; a scan gate on the repo and the artifact; `.gitignore` entries for the
  data folder; `consult forget-key` removes it from the Credential Manager.
- **Money:** the consult is the only thing that can spend a friend's money, so it is off by default, capped by a persistent
  ledger, and shows the running total.
- **Privacy:** no telemetry, no phone-home; the HTTP server stays forced off (it already is); reports leave only by the user's hand.
- **Control:** a clean stop (Ctrl+C is handled and ends with a verdict) plus a stop file or hotkey for a windowed art piece.
  Taking over the controller mid-game is out of scope.

## 4. Order, cost, and proof

- *Slot:* D1-D6 and D13(a) are host-side, need no emulator run beyond one smoke, and cost no Claude usage at runtime; do them
  when next in `launcher.py`. D7's INTERFACE and its fault arms (key leakage, cap ledger) belong with whenever the Coach is first
  built (the draft's `api` stub). D8-D12 are the last build, after the AI plays the whole game. Estimates (not measured): paths
  60 lines, settings schema 150, rom intake 80, ledger 120, doctor 100, report 80, artifact gate 80.
- *Proof bar kept:* each item above names its fault arm. Add one end-to-end check that cannot pass on this PC by accident: install
  into a folder OUTSIDE any git tree, on a second local Windows user with a fresh Python 3.12 venv, no donor profile, no
  `sandbox-pokebot`, network off, then `rom add`, `play` for a short run, `report`. (Windows 11 Home probably lacks Windows
  Sandbox; a second user account is the cheap substitute.) That one run would surface T1 and T2 immediately.
- *Cheapest first step:* a 30-line `AppPaths` plus the artifact allowlist gate (D1, D9): they stop the two mistakes that cannot be
  undone once shared (a ROM in a package, a path baked into saved data).

## 5. Not checked

Whole-game run size and memory; whether `modules` (79 MB) is mostly data or pycache; whether the existing play/hands harnesses
already work as a `FakeHost`; that T1 actually fires on a clean install (read, not run); how `gates/check_purity.py` is imported at
launch (what exactly the artifact must keep); Credential Manager access from a pure Python install (the `keyring` library is the
usual route; unverified here); the Anthropic API's current model ids and prices (keep them in data, look them up when building).
