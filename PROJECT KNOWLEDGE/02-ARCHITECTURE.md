# Architecture — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. Describes how it is built TODAY.

## Tech stack
*(counts and pins re-verified against code 2026-07-27)*
- **Python 3.11–3.13 (64-bit)**; the bot's own **recommended** version is **3.13**
  (`sandbox-pokebot/requirements.py:7-8`). `black` formatting per upstream style.
  ‼ **Tooling under `tools/story-dev/` is run with `py -3.12`** — see the test section.
- **libmgba-py 0.2.0-2** (CFFI bindings to mGBA) — the emulator core, auto-downloaded on
  first run into **`<copy>/mgba/`** (`get_base_path() / "mgba"`,
  `sandbox-pokebot/requirements.py:185`) — i.e. each copy has its own, and the pristine
  mirror has none until run.
- Key libraries: Tkinter (GUI), aiohttp (HTTP API/SSE), SQLite via stdlib (stats),
  confz/pydantic (YAML config schemas), Pillow, numpy. ‼ The declared YAML dep is
  **`ruamel.yaml`** (`requirements.py:18`); `import yaml` (PyYAML) is also used
  (`modules/game.py`, `modules/backup_manager.py`) but arrives transitively — it is NOT
  declared.
- Deps are declared in **`<copy>/requirements.py`** (a Python list, not requirements.txt)
  and self-installed at first launch.

## Folder / module map

**‼ THERE ARE THREE COPIES OF THE BOT, not two.** Getting this wrong is the most common
orientation error — see the "which copy" table below the tree.

```
Pokebot_Gen3_Enhancement/
├── CLAUDE.md                      # Kit directives + project rules (3-copy layout, daily upstream check, sandbox rule §"Sandbox area")
├── Pokemon_Emerald_AI_Notes.md    # Cross-project transfer notes (Emerald AI project)
├── install.py                     # installer/updater/healer for custom-pokebot
├── install_sandbox.py             # same, for sandbox-pokebot
├── PROJECT KNOWLEDGE/             # ★ this documentation set (00–24 + playbooks)
│   ├── 00–08 kit docs             # vision, architecture, punch list, handoff, logs
│   ├── 09–24 design/recon docs    # storymode design, living dex, team policy, …
│   ├── ai-research-notes/         # Gemini notes — RECALL ONLY, never authoritative
│   └── REFERENCE-INSTALLER-PATTERN.md  # Nick's installer-as-codebase spec
├── PROJECT KIT/                   # portable bootstrap that makes the repo resumable anywhere
├── REMOTE START/                  # portable Claude Code remote launcher (Remote-Start.ps1, Git-Sync.ps1)
├── cloud-backups/                 # profile backups pushed to this private repo ("your repo IS the cloud")
├── tools/story-dev/               # ★ the Story-bot test harness, drivers, recon scripts, repro suite
│   ├── story_harness.py           # replicates main.py's loop exactly (see 14-AGENT-PLAYBOOK §2)
│   ├── livetest.py                # headless batch runner
│   ├── repro_*.py                 # 84 regression reproducers — THE verification bar (§2b)
│   ├── audit_flag_names.py        # proves a flag/var NAME is real before code depends on it
│   └── saves/                     # committed checkpoint .ss1 progression sampler
├── 40cakes repo/                  # ★ everything about the ORIGINAL program
│   ├── UPDATE-LOG.md              # append-only upstream sync record + daily-check ritual
│   ├── DOCUMENTATION/             # deep developer docs of the original bot
│   │   ├── 00-CODEBASE-OVERVIEW.md         # start here
│   │   ├── 01-core-runtime-and-emulator.md
│   │   ├── 02-game-state-and-memory.md
│   │   ├── 03-bot-modes-and-battle.md
│   │   ├── 04-interfaces-gui-web-streaming.md
│   │   ├── 05-stats-config-data-tests.md
│   │   └── _history/              # versioned snapshots of superseded docs
│   └── pokebot-gen3/              # PRISTINE upstream mirror (git subtree, commit 5dd898f8)
│       ├── pokebot.py             # entry point + self-bootstrap
│       ├── modules/               # 59 top-level modules (sandbox 83, custom 74)
│       │   ├── modes/             # 23 bot automations + BotMode contract
│       │   ├── battle_strategies/ # battle decision engine
│       │   ├── gui/  web/  config/  data/  built_in_plugins/
│       ├── plugins/  tests/  wiki/
├── custom-pokebot/                # ★ PROMOTED fork (from upstream 5dd898f8) — the "production" copy
│   ├── DIVERGENCE-LOG.md          # append-only: every intentional diff vs upstream
│   ├── DOCUMENTATION/             # docs about the CUSTOM parts only
│   ├── modules/gui/dashboard_gui.py   # native dashboard GUI (default window)
│   ├── modules/web/static/custom-ui/  # browser dashboard (opt-in remote viewing)
│   ├── plugins/custom_modes/      # Patrol, Hunt, Living Dex, Macro, Story
│   └── (otherwise same program layout as the mirror)
└── sandbox-pokebot/               # ★★ THE ACTIVE COPY — all current work happens HERE
    ├── SANDBOX-NOTES.md  SANDBOX-PROPOSALS.md  CHEATS-DESIGN.md  DIVERGENCE-LOG.md
    ├── plugins/custom_modes/story_mode.py   # StoryMode + StoryDebug/DebugReset/EndlessReset
    ├── modules/story/             # 19 modules: early_game, chapters, region_reach,
    │                              #   counter_plan (plans) + counter_hunt (executes),
    │                              #   training_areas, fortree_gates, intro, progress,
    │                              #   config, team_policy (built, UNWIRED),
    │                              #   mossdeep_gym_puzzle (PURE model, UNWIRED),
    │                              #   mossdeep_gym (§Ch18 chapter + executor),
    │                              #   space_center (§Ch19 chapter — Space Center AND Dive),
    │                              #   roster (party REORDER by PID; planner + DRIVER proven,
    │                              #     PROMOTED 2026-08-13 — zero production callers yet),
    │                              #   obstacle_clearing, pc_trip, battle_items
```
‼ **CORRECTED 2026-08-12 — there is no "sandbox-only modules" list any more, and there was not one
for some time before that.** This file used to name ten modules (`endless_x4`, `tile_bridge`,
`tile_mosaic`, `x4_logs`, `remote_party`, `badge_log`, `badge_case`, `battle_fault`,
`story_milestones`, `gui/tile_child`) as *"absent from custom-pokebot"*. **Every one of them is
present in `custom-pokebot/modules/`** — measured file-by-file. `CLAUDE.md` repeats the same stale
claim. It mattered: that list was the premise of the main risk assessment before the §Ch18/§Ch19
promotion, and the risk turned out not to exist.

### Which copy am I in? (verified 2026-07-27)
| copy | role | edit it? |
|---|---|---|
| `40cakes repo/pokebot-gen3/` | pristine upstream mirror (git subtree) | **NEVER** — changes only via `git subtree pull` |
| `custom-pokebot/` | promoted/"production" fork | only when promoting an approved sandbox feature |
| `sandbox-pokebot/` | **experimental — where enhancements are built and tested** | **YES, this is the default** |

‼ **THE FORKS ARE ALMOST IDENTICAL TODAY — corrected 2026-08-12.** This paragraph used to say they
had "diverged", with `story_mode.py` at *"3,061 lines vs 2,636"*. **Measured: 3,742 in BOTH.** After
the §Ch18/§Ch19 promotion the two trees were byte-identical across all 255 code/config files.

⛔ **DO NOT READ A DRIFT FIGURE OUT OF THIS FILE. Run `promote.py --check`** — it measures both
directions in seconds and is the only authority; `04-HANDOFF.md`'s STATE row names the currently
expected set. This paragraph has carried THREE different figures (zero, then "EXACTLY 3" —
`map_path.py`, `early_game.py`, `story_mode.py`, all of which have since been PROMOTED — and the
set is different again today after PARTY ACCOUNTING STAGE 0). Each was true for hours. That is
precisely why `audit_doc_consistency.py` MEASURES drift rather than trusting any sentence,
including this one. Superseded text: **DRIFT IS ZERO AGAIN AS OF 2026-08-13.** `modules/story/roster.py` and `modules/menuing.py`
were **PROMOTED** (user-approved) after `--driver roster --build custom` returned
`ACCEPTANCE: PASS` **frame-identical to the sandbox run** — and after `find_spec` confirmed the
custom tree was the one actually imported, so a frame-identical result could not be a silent
fallback. Every `.py` under `modules/` and `plugins/` compared afterwards: 0 differing, 0 missing.
Restore point: `restore/2026-08-13-pre-roster-promotion`. Details + what remains unproven:
`custom-pokebot/DIVERGENCE-LOG.md`.

⇒ **Do not trust this paragraph either — MEASURE.** The drift loop is in `04-HANDOFF.md` under
"HOW TO RUN / TEST"; it takes seconds and prints the differing files. A path written without a copy
prefix is ambiguous — **always prefix**. Promotion rule and the "don't touch custom during a
sandbox round" directive: root `CLAUDE.md` §"Sandbox area".

‼ **The bot the USER runs is on a DIFFERENT MACHINE** (`…\Pokebot Gen 3 SECOND RUNNING
PROFILE\Pokebot_Gen3_Enhancement_old\sandbox-pokebot\`), not this checkout. Fixes committed
here do not reach it until that machine pulls. Two log bundles were analysed against
undeployed code before this was noticed — see `04-HANDOFF.md §0a`.

## How the pieces talk
Single-threaded frame-locked loop (`modules/main.py:36`): snapshot state →
run frame listeners → advance the top generator on
`context.controller_stack` (bot modes/battle handlers are generators; each
`yield` = one frame with given button state) → `run_single_frame()`. The
game is paused while Python decides. The `context` singleton
(`modules/context.py`) wires emulator, profile, config, mode, frontend.
Observers (GUI, HTTP API, Discord) consume frame-stamped state-cache
snapshots; the web thread never reads emulator memory directly.
Full walkthrough: `40cakes repo/DOCUMENTATION/00-CODEBASE-OVERVIEW.md`.

**‼ The controller stack is FLAT, not nested.** `main_loop` advances only the
TOP generator, so a bot mode and a battle handler pushed by `BattleListener` are
SIBLINGS — an exception raised by battle code propagates to `main_loop` (which
sets Manual), never through the mode's own `try`. A mode therefore cannot catch
or recover from a battle-handler failure by any arrangement of `except`. Faults
that a mode should survive travel by an explicit channel instead:
`modules/battle_fault.py` (sandbox) — the battle handler records the reason and
returns; a mode that declares `handles_battle_faults = True` claims it on its
next frame and re-raises inside its own recoverable scope. Opt-in on purpose;
see 06-DECISIONS-LOG 2026-07-25.

**Per-frame main-loop participants (fork additions).** Beyond the stock listeners, two
sandbox subsystems are wired directly into `modules/main.py` and run every frame:
`modules/debug_logger.py` (the opt-in event stream + STUCK dumps with generator call
stacks — `main.py:102-107`) and `modules/badge_log.py` (badge polling + run-boundary
detection — `main.py:114-117`, `:126-131`). Both are central to how failures get
diagnosed; see `14-AGENT-PLAYBOOK.md` §2c.

**One emulator per PROCESS — and that is load-bearing.** `context` is a module-level
singleton (`modules/context.py:188` — the file's last line, verified in all three copies)
imported by **118 files under `sandbox-pokebot/modules/`** (114 in `custom-pokebot`, 98 in
the mirror), with exactly one `context.emulator`; `modules/main.py` adds `work_queue:19`
and `inputs_each_frame:24` as further process-globals.
*(A "116 files" figure appears in an older comment in `modules/tile_bridge.py` and matched
no copy when re-counted on 2026-07-27 — the argument is unaffected, only the number.)* Anything wanting N emulators at once must therefore be
N processes. **Endless Loop ×4** (sandbox, `modules/endless_x4.py`) is the one feature
that does this: the dashboard spawns four `pokebot.py` lanes with `--tile-shm`, each
selecting the `PokebotTileChild` frontend (`modules/gui/tile_child.py`), which publishes
a 240×160 RGB frame plus a JSON status blob at 20 Hz into a single `SharedMemory` block
(`modules/tile_bridge.py`, lock-free: pixels → status → header, `sequence` written last
and re-checked by the reader). The dashboard reads all four slots and paints a 2×2 grid
via `modules/tile_mosaic.py` (pure PIL, no Tk) into its normal video canvas.
‼ The dashboard has **no Tk mainloop** — the event queue is pumped from the frame
callback — so during a batch this process's own emulator is parked in Manual at 1× purely
to keep pumping. Lane teardown happens in `_close_window()` **before** its `os._exit(0)`,
because no `atexit` handler will ever run on that path.

## Key modules
See the per-layer docs in `40cakes repo/DOCUMENTATION/` — the
authoritative module reference (intent + mechanics + file:line refs).
Custom-only behavior is documented in `custom-pokebot/DOCUMENTATION/`.

### `modules/party_accounting.py` — OURS, new 2026-08-14 (sandbox only; drift 2)
Splits the three quantities the bot used to conflate (`06-DECISIONS-LOG.md` RULING D):
**A** `gPlayerPartyCount` (what the game says is filled — the CAPACITY authority),
**B** `len(get_party())` (what the bot can READ — the ITERATION/INDEX authority, and it can be
LESS than A because `get_party()` skips near-empty slots), and **C** (what the bot believes it
has — deliberately not built yet).
‼ **It is STAGE 0: readers plus a divergence log, and it wires NO call site.** Three log-only
hooks inside `get_party()` record HOLE / OVERFLOW / INVALID exactly and STALE by sampling; the
run summary is printed by `story_harness.py` at the end of a drive. Nothing consumes the readers
— that is asserted by the gate, not just intended. Gate: `repro_party_accounting.py`.

## External dependencies & services
- **ROMs**: user-supplied in each copy's `roms/`, SHA-1 whitelisted,
  never committed.
- **Profiles** (`<copy>/profiles/<name>/`): save, savestates, per-profile
  config, `stats.db` — never committed.
- GitHub (upstream releases for the stock auto-updater; disabled for git
  checkouts like ours), Discord webhooks (optional), OBS websocket
  (optional).
- Upstream remote: `upstream-pokebot` → 40Cakes/pokebot-gen3. Daily check
  + pull ritual: see `40cakes repo/UPDATE-LOG.md` header. Pull command:
  `git subtree pull --prefix="40cakes repo/pokebot-gen3" upstream-pokebot main --squash`.

## How to run / build / test

### Running the bot
```powershell
cd sandbox-pokebot         # ★ the ACTIVE copy — use custom-pokebot for the promoted build,
                           #   or "40cakes repo/pokebot-gen3" for pristine upstream
python pokebot.py                      # dashboard GUI (default); first run self-installs deps
python pokebot.py <profile> -m Spin    # straight into a mode
python pokebot.py <profile> --classic-gui   # upstream's original window (OpenGL/stepping)
python pokebot.py --headless --no-video
python -m unittest discover tests      # needs specific ROM dumps in roms/
python ..\install_sandbox.py           # repo root: install/update/heal the SANDBOX copy
python ..\install.py                   # same, for custom-pokebot
```

### ‼ Testing — the repro suite is the project's real verification bar
⛔ **CORRECTED 2026-08-13 — READ THIS BEFORE THE PARAGRAPH BELOW.** The verification bar is no
longer "sweep the `repro_*.py` directory". It is **two commands**, and they are what every session
is told to run first:

```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 preflight.py     # git sync + fixtures + docs + live-batch detection. Exits 1.
PYTHONUTF8=1 py -3.12 run_gates.py     # THE STANDING SUITE — 23 gates, ~130s, non-zero on any failure
#  ‼ It PRINTS its own count. Believe that, not this comment: it has read 17, 18, 21 and 22, and a
#  stale count here is invisible to every gate — three separate copies of it existed on 2026-08-14.
```

‼ **`run_gates.py`'s `GATES` table is AUTHORITATIVE — prose is not.** The list lives in code
precisely because a comment here once advertised the wrong count for a whole session.
**Driving the story bot** is `tools/story-dev/story_harness.py <anchor> --driver <name>`; the
current §Ch20 chain is `ch20dive → ch20room1 → ch20room2 → ch20room6 → ch20room3`, and
`04-HANDOFF.md`'s "HOW TO RUN / TEST" holds the expected output line for each.
‼ A driver keeps running after it prints `ACCEPTANCE:` and the harness exits on its own idle
detector, logging **"HANG CONFIRMED" on a run that SUCCEEDED** — read the `ACCEPTANCE:` line, not
the last line.

*(the older sweep description follows, kept because the scripts still exist and still run)*

`tools/story-dev/repro_*.py` is **52 scripts**, most needing **no emulator**. Run the whole
sweep after any change; a fix that satisfies its own new repro can still break an older
one's contract (this happened twice on 2026-07-27).

```bash
# from the repo root. NOTE: `py -3.12`, NOT `python`.
for f in tools/story-dev/repro_*.py; do
  timeout 90 py -3.12 "$f" >/dev/null 2>&1 && echo "PASS $f" || echo "CHECK $f"
done
```
- **Interpreter:** `py -3.12`. Plain `python` on this dev box is **3.9** — unsupported by the
  project (3.11–3.13) and missing the deps. Install for 3.12 if absent:
  `py -3.12 -m pip install "confz==2.0.1" "ruamel.yaml~=0.18.2" "rich~=13.5.2" "numpy~=2.1.0"`.
- **Expected as of 2026-07-27: 47 pass, 0 fail, 5 environmental.** The 5 need a real mgba or
  have their own harness issues (`repro_boss_training`, `repro_double_faint`,
  `repro_navigate_failfast`, `repro_sufficiency`), plus `repro_x4_lanes`, which **spawns real
  lane processes** — skip it unless you mean it.
- Use a **~90s per-script timeout**; 25s misreports slow-but-healthy scripts as errors.
- The faithful end-to-end harness is `tools/story-dev/story_harness.py` (needs a real mgba).
  Its `--driver` list is the project's main debugging surface; the ones added since this file was
  last revised (2026-08-08) are **capability tests**, each answering one binary question in
  minutes rather than a 3-hour batch:
  `boxcatch` (full-party catch overflows to the PC box), `boxwithdraw` (the mon comes back out at
  a Poké Centre, driving the real heal-piggyback), `teachfull` (HM teach down the REPLACE path,
  which `hmtest` cannot reach because its freshly-caught mon has a free slot; `TEACH_INJECT` /
  `TEACH_AFTER_GYM` / `TEACH_AFTER_BATTLE` / `TEACH_AFTER_CATCH` build the failing fixtures),
  `cavethread`, `normancounter`, `groundsweep` (driven reach-AND-leave evidence for a candidate
  hunting ground), the two **Magma Hideout** drivers below, and the two
  **anchor-manufacturing** drivers below that.
- **`teach_hm_move` instrumentation and fault injection (added 2026-08-11, `#24-teachmsgstall`).**
  Every button in the teach flow goes through a recording `_press()` wrapper, so the trace can pair
  a state change with **the buttons we pressed to cause it** — the field that finally separated
  "the game is stuck" from "our own A-mash is driving a ping-pong". All four switches default OFF
  and change no control flow when unset:
  | env | what it does |
  |---|---|
  | `TEACH_TRACE=1` | one `TEACH TRACE` line per observable change: phase, game state, task set, learn state, knows, `pressed_since` |
  | `TEACH_MISS_WINDOW=1` | model a mistimed frame — ignore the 1-frame `Task_ReplaceMoveYesNo` sighting. ‼ Measured NOT sufficient on its own to wedge a teach |
  | `TEACH_CANCEL_FORGET=1` | **one-shot**: cancel the forget-move screen once, which the decomp routes to `StopLearningMovePrompt` — the prompt where A means give up. This is the discriminating arm |
  | `POKEBOT_TEACHWINDOW_A=1` | restore the pre-fix post-select loop AND ride ladder (the OLD arm) |
  ‼ The OLD arm must restore **both** loops (`_PROMPT_MATCH` / `_STOP_MATCH`), or it quietly enjoys
  half the fix and the A/B measures nothing.
- **`--driver magmatravel` / `--driver magmahideout` (added 2026-08-10, §Ch15)** — the chapter
  split into two separately-graded halves, which is what let a party problem, an instrument bug
  and a Strength gate each name themselves instead of arriving as one opaque failure:
  - `magmatravel` runs `travel_to_magma_hideout_door()` from `saves/post_mtpyre.ss1`. Acceptance
    is `VAR_JAGGED_PASS_STATE == 2` **and** standing on `JAGGED_PASS (16,20)` — ‼ the var, not
    the tile, because the door is walled by a `setmetatile` a path check cannot see. On success
    it **captures `saves/magma_door.ss1`**.
  - `magmahideout` runs `enter_magma_hideout()` + `do_magma_hideout()` from that anchor.
    Acceptance is `FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT`; it reports `floors=[...]` (how far it
    got) and captures `saves/magma_1f_fail.ss1` on failure.
  - ‼ Both override `on_whiteout()` to **True**, mirroring StoryMode. The framework default is
    False (= drop to Manual), and inheriting it made two runs stop at the identical frame and
    read as a route failure. **A driver standing in for a mode must mirror that mode's
    overrides, not merely call its functions.**
- **Anchors (save states) are now made, not only scavenged** — added 2026-08-09 because
  `#24-r116sweep` twice picked an anchor by NAME and both were the wrong map or era:
  - `probe_anchor_inventory.py` — loads every save in `saves/` and prints map (**as a `MapRSE`
    enum**, because `map_name` is a display label and interiors carry their city's), tile, game
    state, controllability, badges, party, money. Carries a positive control.
  - **`--driver spacecenter1 / spacecenter2 / spacecenter` (added 2026-08-12, §Ch19)** — legs 1-3,
    the party menu + multi battle, and the whole chapter. ‼ Run `spacecenter` from BOTH
    `post_mossdeep_gym.ss1` (plays it all) and `post_space_center.ss1` (must SKIP to leg 6) — the
    second is what proves the resume guards, and the ladder re-runs `_play` from wherever the player
    actually is.
  - **`--driver roster` (added 2026-08-13)** — the PARTY-ORDER capability, from `post_dive.ss1`.
    Five phases, all verified **by PID, never by slot**: (1) a spec pinning slots 0 AND 1, which is
    what forces `RotatePokemon(source, destination)` with `destination != 0` — the path nothing in
    this project had ever driven; (2) the REGI shape (`plan_last_slot`, first + last pinned);
    (3) idempotence, which must cost **0 frames**; (4) restore; (5) CAN-CONTINUE — a real
    `calculate_path` **and an actual position change**. A sixth block MEASURES `_rotate_lead_safely`
    (KI-70) without changing it.
    ‼ Its tracer re-implements the `gPartyMenu` parse (`_raw_party_menu`) on purpose:
    `get_party_menu_cursor_pos` calls `set_manual_mode()` on `slot_id == -1`
    (`menu_parsers.py:164-166`), so the stock reader can kill the run it is observing.
  - `--driver anchorcapture` — navigate to a named map/tile and snapshot; refuses to overwrite
    an existing anchor, and refuses to write a non-arrived or non-controllable state.
  - `--driver anchorstory` — drive the REAL story bot until it stands on the wanted map, then
    snapshot; `CAPTURE_FORBID_FLAG` fails loudly if the era window closes first. Needed because
    direct navigation cannot make some trips the bot itself makes (KI-48).
- **`saves/stalls/<profile>-f<frame>.ss1`** — the harness auto-snapshots at every stall. ‼ A
  `.ss1` is a full machine snapshot and **preserves battle callbacks / mid-script state**
  (measured 2026-08-09, 6 of 6), unlike a `.sav`. That makes a stall state a loadable fixture
  for bugs that need a runtime tail resident.
- **`#24-mossdeepgym` (2026-08-12, COMPLETE — Segment 18 in the ladder)** — the Mossdeep Gym
  rotating-tile statue puzzle:
  * `modules/story/mossdeep_gym.py` — the EXECUTOR and the chapter. ‼ It **re-solves rather than
    replays**: nine trainers stand on the rotating pads and every rotation re-aims them, so a blind
    117-step replay desynchronises the moment one fires. It walks until something unexpected
    happens, then solves again from where it actually is.
    ‼ **`do_mossdeep_gym_chapter()` lives here, not in `early_game.py`** — see `06-DECISIONS-LOG.md`.
    ‼ Every raise is a `BotModeError`, because the chapter's whiteout retry catches exactly that
    type; a `RuntimeError` here silently disables the recovery (and once did).
  * `modules/story/mossdeep_gym_puzzle.py` — a **PURE** simulator (`press(state, colour)`,
    `is_walkable(tile, state)`), so a 116-step route can be planned offline instead of pressed out
    on the emulator. `build_puzzle_from_emulator()` is the only impure part: it reads the arrow
    field, the nine switches, the 36 object templates and the collision layer from ROM.
    ‼ It re-reads the raw metatile id itself, because `modules/map.py` computes it (line 779) but
    returns only `(attributes, collision, elevation)` — widening a SHARED module for one puzzle was
    not worth the blast radius.
  * ‼ **The state is the full tuple of object positions**, not "5 counters mod 4": pads do not all
    hold three objects, and nine TRAINERS rotate along with the 21 statues.
  * `tools/story-dev/probe_gym_arrows.py` dumps the arrow field and derives the encoding from data;
    `probe_gym_simulate.py` is the validation gate that presses a switch for real and requires the
    simulator to have predicted every loaded object, keyed on `local_id`. **PASS: 11/11.**
- **`#24-spacecenter` (2026-08-12, COMPLETE — Segment 19 in the ladder)** — the Mossdeep Space
  Center **and** HM08 Dive, in ONE chapter because `chapters.py` grades chapter 19 on
  `RECEIVED_HM_DIVE`:
  * `modules/story/space_center.py` — six legs: heal → ride the forced Team Magma cutscene → cross
    1F → the 2F grunt gauntlet → Steven's two talks + the party menu + the multi battle → HM08 at
    Steven's house → **and back outside**.
  * ‼ **Leg 1 is TWO navigations, not one.** The gym victory SPAWNS five Magma NPCs onto the only
    land bridge (x=44, y=23-26) and `map_path` blocks loaded-object tiles, so no route to the door
    exists until the cutscene `removeobject`s them. The chapter routes to the trigger line and
    **asserts `VAR_MOSSDEEP_CITY_STATE == 2`** before planning leg 1b.
  * ‼ **`_talk_to_the_stair_grunt()`** — that grunt has `sight_radius = 0` and stands ON the only
    tile the stairs are reachable from, so it is an INTERACTION trainer and its tile can never be a
    navigation destination. Graded on the grunt MOVING, not on a battle happening.
  * ‼ **`choose_battle_party()` drives `ChooseHalfPartyForBattle`** — the first party menu of this
    kind this codebase has ever driven. Cursor 0-5 are mons, **6 = CONFIRM, 7 = CANCEL**; each pick
    is A (submenu) then A (ENTER) and **the cursor does not advance**; A on a picked mon DESELECTS
    it, so a blind mash toggles for ever. Every pick is verified against **`gSelectedOrderFromParty`**
    (`slot + 1`). It always brings THREE — the loss condition sums HP over the player's picks only.
  * `leave_stevens_house()` uses **`_walk_through_warp("Down")`**, because both navigate-based door
    helpers free the tile by stepping SOUTH and the interior door is on the bottom row. An exit door
    is not an entry door.
  * `tools/story-dev/probe_ch19_route.py` — the reachability probe. ‼ It models **live objects**,
    which the first version did not; without them it "found" a KI-59 planner defect that was really
    five NPCs standing on a bridge.
  * Drivers `--driver spacecenter1 / spacecenter2 / spacecenter`; anchors `at_steven_2f.ss1`,
    `post_space_center.ss1`, `post_dive.ss1`.
- **`#24-battleitems` (promoted 2026-08-10)** — the bot uses healing items in TRAINER battles:
  * `modules/story/battle_items.py` — a **PURE** policy (no emulator, no game state), so it is
    unit-testable in milliseconds by `tools/story-dev/repro_battle_items.py` (27 checks). Heal
    amounts are read from `modules/data/items.json` (`battle_use == "healing"`, `parameter` = HP,
    255 = full), never hard-coded.
  * `StoryItemBattleStrategy` in `plugins/custom_modes/story_mode.py` — supplies HP/bag/worst-hit
    to the policy and turns its answer into `TurnAction.use_item_on`. **Trainer battles only**, and
    it **fails open**, so wilds/training/catching are unchanged. It also self-corrects the
    party-menu index space and disables items for a battle if a use demonstrably does nothing.
  * `modules/battle_action_selection.py` — carries the fix for a real index-space bug (a
    BATTLE-order index was being fed to a PARTY-MENU scroll) plus `[TURN …]` per-decision and
    `[ITEM-FLOW]` per-stage telemetry.
- Offline planner probes need **no emulator**: `probe_counter_candidates_offline.py`,
  `probe_counter_item_gate.py`, `probe_movepool_counters.py`, `rare_species_dataset.py`,
  `analyse_defeat_loops.py`. ‼ They stub `get_map_enum`/`get_encounter_index`, and
  `find_counter_candidates` returns `[]` on ANY internal error — so each one carries a POSITIVE
  CONTROL (Norman must find Machop @ FIERY_PATH). Without it, a broken harness is indistinguishable
  from a real "no answer".
  Full usage: `14-AGENT-PLAYBOOK.md` §2.
