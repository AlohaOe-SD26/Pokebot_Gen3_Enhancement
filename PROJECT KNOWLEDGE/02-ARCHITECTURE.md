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
├── PROJECT KNOWLEDGE/             # ★ this documentation set (00–31 + playbooks + batch-evidence/)
│   ├── 00–08 kit docs             # vision, architecture, punch list, handoff, logs
│   ├── 09–31 design/recon docs    # storymode design, living dex, team policy, backups,
│   │                              #   injection surface, disabled-features registry, metrics, archives
│   ├── ai-research-notes/         # Gemini notes — RECALL ONLY, never authoritative
│   └── REFERENCE-INSTALLER-PATTERN.md  # Nick's installer-as-codebase spec
├── PROJECT KIT/                   # portable bootstrap that makes the repo resumable anywhere
├── REMOTE START/                  # portable Claude Code remote launcher (Remote-Start.ps1, Git-Sync.ps1)
├── cloud-backups/                 # profile backups pushed to this private repo ("your repo IS the cloud")
├── tools/story-dev/               # ★ the Story-bot test harness, drivers, recon scripts, repro suite
│   ├── story_harness.py           # replicates main.py's loop exactly (see 14-AGENT-PLAYBOOK §2)
│   ├── livetest.py                # headless batch runner
│   ├── repro_*.py                 # regression reproducers — ⛔ count lives in §Testing; `ls` is the
│   │                              #   authority. THE bar is `run_gates.py`, not this directory
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
│       ├── modules/               # top-level modules: mirror 59, sandbox 84, custom 84 (2026-08-17; ⛔ MEASURE, do not trust)
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
    ├── modules/story/             # 24 modules (`ls modules/story/*.py` minus `__init__` IS the
    │                              #   authority — this count read 19 until 2026-09-16, i.e. it had
    │                              #   missed FIVE, §Ch23's and §Ch24's among them):
    │                              #   early_game, chapters, region_reach,
    │                              #   counter_plan (plans) + counter_hunt (executes),
    │                              #   training_areas, fortree_gates, intro, progress,
    │                              #   config, team_policy (WIRED: early_game.py:1773,
    │                              #     pc_trip.py:61/278/352/490 — OFF BY DEFAULT, not unwired),
    │                              #   mossdeep_gym_puzzle (PURE model, consumed by
    │                              #     mossdeep_gym.py:39 — corrected 2026-08-23, was 'UNWIRED'),
    │                              #   mossdeep_gym (§Ch18 chapter + executor),
    │                              #   space_center (§Ch19 chapter — Space Center AND Dive),
    │                              #   roster (party REORDER by PID; planner + DRIVER proven,
    │                              #     PROMOTED 2026-08-13 — zero production callers yet),
    │                              #   obstacle_clearing, pc_trip, battle_items,
    │                              #   seafloor_cavern (§Ch20), sootopolis (§Ch21),
    │                              #   sootopolis_gym (§Ch22), victory_road (§Ch23),
    │                              #   pokemon_league (§Ch24 — 3 legs, NOT wired; see below),
    │                              #   counter_hunt, overworld_items
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
had "diverged", with `story_mode.py` at *"3,061 lines vs 2,636"*. **Measured 4,135 in BOTH (2026-08-17; it read "3,742" from an earlier measurement — ⛔ a line count is a DECAYING number, run `wc -l`).** After
the §Ch18/§Ch19 promotion the two trees were byte-identical across all 255 code/config files.

⛔ **DO NOT READ A DRIFT FIGURE OUT OF THIS FILE. Run `promote.py --check`** — it measures both
directions in seconds and is the only authority; `04-HANDOFF.md`'s STATE row names the currently
expected set. This paragraph has carried THREE different figures (zero, then "EXACTLY 3" —
`map_path.py`, `early_game.py`, `story_mode.py`, all of which have since been PROMOTED — and the
set is different again today after PARTY ACCOUNTING STAGE 0). Each was true for hours. That is
precisely why `audit_doc_consistency.py` MEASURES drift rather than trusting any sentence,
including this one.

⭐ **AND `tools/story-dev/archive_doc_block.py` (added 2026-09-05) IS THE SAME IDEA APPLIED TO DOC
MAINTENANCE.** `03-PUNCH-LIST.md` and `05-KNOWN-ISSUES.md` carry `lint_docs` R3 line budgets, so
closed content is periodically retired to `28-HANDOFF-ARCHIVE.md` / `31-KNOWN-ISSUES-ARCHIVE.md`.
Doing that by hand went wrong TWICE IN ONE SESSION, in OPPOSITE directions — once dropping the
block's tail ("ARCHIVED VERBATIM" over a truncation) and once keeping it in the wrong place (only
the header moved, leaving "STATUS: OPEN... this is the next build" under a CLOSED heading). ⇒ the
tool enforces **two** invariants before writing either file: **no loss** (every removed non-blank
line is in the archive) and **no orphan** (the pointer is followed by a real block boundary).
‼ `--self-test` fault-proves both, and its own arms caught a flaw in the checker: invariant B first
read the same boundary constant the block-finder uses, so the injected fault blinded the check.
⇒ ⭐ **a check that shares its input with the thing it checks is not a check** — the reason
`_BOUNDARY_FOR_CHECK` is a deliberate duplicate. ⛔ It is a TOOL, not a gate, and is deliberately NOT
in `run_gates.py`: it performs an operation, so it has nothing to assert on a clean tree. Superseded text: **DRIFT IS ZERO AGAIN AS OF 2026-08-13.** `modules/story/roster.py` and `modules/menuing.py`
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
imported by **124 files under `sandbox-pokebot/modules/`** (124 in `custom-pokebot` — the forks are byte-identical, so any asymmetry here is a STALE COUNT, not a fact; 98 in
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

### `modules/party_accounting.py` — OURS, new 2026-08-14 (PROMOTED 2026-08-15; in BOTH forks)
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
py -3.12 pokebot.py                    # dashboard GUI (default); first run self-installs deps
py -3.12 pokebot.py <profile> -m Spin    # straight into a mode
py -3.12 pokebot.py <profile> --classic-gui   # upstream's original window (OpenGL/stepping)
py -3.12 pokebot.py --headless --no-video
py -3.12 -m unittest discover tests      # needs specific ROM dumps in roms/
py -3.12 ..\install_sandbox.py           # repo root: install/update/heal the SANDBOX copy
py -3.12 ..\install.py                   # same, for custom-pokebot
```

### ‼ Testing — the repro suite is the project's real verification bar
⛔ **CORRECTED 2026-08-13 — READ THIS BEFORE THE PARAGRAPH BELOW.** The verification bar is no
longer "sweep the `repro_*.py` directory". It is **two commands**, and they are what every session
is told to run first:

```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 preflight.py     # git sync + fixtures + docs + live-batch detection. Exits 1 ON FAILURE.
PYTHONUTF8=1 py -3.12 run_gates.py     # THE STANDING SUITE — 94 entries = 90 ENFORCING + 4 ADVISORY
#   (`probe_regi_capabilities`, `probe_dive_routing` RUN and print ADVIS but do NOT gate),
#   non-zero on any ENFORCING failure. ⛔ `--quick` skips 9 ROM gates and is NOT a green suite.
#   ⏱ MEASURED 2026-09-11: the FULL suite is **~183s** and `repro_gym_whiteout_guard.py` is
#   **~108s** of it — still the single dominant gate, but no longer a timeout. ✅ `--quick` ~31-40s
#   *(that timing is from 2026-09-05; for the COUNT, line 244 above and `run_gates.py` are the
#   authority — never this line)*. ⭐ **Budget ~3 MINUTES for the full suite, not 15.**
#   ‼ *(This comment read "a KNOWN-RED ~900s timeout (`#26-gatestartupcontention`) … so budget
#   ~15 MINUTES, not seconds" from 2026-08-26 until 2026-09-11. That item is now CLOSED: the gate
#   was never hanging, it was PACED to 60fps by a per-frame audio write because it never set
#   `context.emulation_speed = 0`. Gate #54 `probe_gate_unthrottled.py` enforces the fix.)* *(This comment read "~150s" until 2026-09-05, which a Tier 1
#   reviewer read as the total runtime and under-estimated the wall clock by two orders of
#   magnitude. 150s is a TIMEOUT CAP discussed further down, not a duration — ⇒ never put a bare
#   number next to a command without saying what it MEASURES.)*
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

`tools/story-dev/repro_*.py` is **104 scripts** (measured 2026-08-23; it read 103 as of 2026-08-17) (plus **75** `probe_*.py`) — ⛔ these grow weekly, so `ls tools/story-dev/repro_*.py | wc -l` is the authority, not this line; most
needing **no emulator**. ‼ **COUNTED, not recalled** — these figures said 84 and 52 from 2026-08-10
until a 2026-08-15 audit measured the directory; the probe count went 71 → 72 → **73** on 2026-08-16
as `probe_abort_swallowing.py` and then `probe_stale_citations.py` were added. They are prose, not a gate: `ls` is the authority.
Run the whole
sweep after any change; a fix that satisfies its own new repro can still break an older
one's contract (this happened twice on 2026-07-27).

```bash
# from the repo root. NOTE: `py -3.12`, NOT `python`.
for f in tools/story-dev/repro_*.py; do
  PYTHONUTF8=1 timeout 150 py -3.12 "$f" >/dev/null 2>&1 && echo "PASS $f" || echo "CHECK $f"
done
```
- **Interpreter:** `py -3.12`. Plain `python` on this dev box is **3.9** — unsupported by the
  project (3.11–3.13) and missing the deps. Install for 3.12 if absent:
  `py -3.12 -m pip install "confz==2.0.1" "ruamel.yaml~=0.18.2" "rich~=13.5.2" "numpy~=2.1.0"`.
- ⛔ **THE PINNED EXPECTATION HERE WAS STALE AND HID FIVE REAL BREAKAGES** (removed 2026-08-23).
  It read *"47 pass, 0 fail, 5 environmental"* — arithmetically impossible against this section's own
  103 scripts AT THE TIME (104 as of 2026-08-23), and three of the five it named now PASS. ‼ **Two of its instructions were also wrong:**
  without `PYTHONUTF8=1` about 37 healthy scripts die on a `‼` and read as CHECK (measured A/B:
  59 PASS/43 CHECK → **96 PASS / 6 CHECK of 102**), and the 90s cap failed
  `repro_gym_whiteout_guard`, which needs ~122s and PASSES inside `run_gates.py`.
  ⇒ **grade on `run_gates.py`, never on a remembered tally.**
  ✅ **ALL SIX ARE FIXED (2026-08-23, `#24-brokenrepros`). MEASURED SWEEP: 103 PASS / 0 CHECK / 1 SKIP of 104** — the one
  SKIP is `repro_x4_lanes`, excluded deliberately because it spawns real lane processes.
  ‼ **THE SKIP IS CONSERVATISM, NOT A KNOWN FAILURE:** an independent reviewer ran it on 2026-08-23
  and it PASSED, cleaning up after itself via its own `finally: batch.stop()` (their sweep read
  104/104). ⇒ do not record it as broken; the exclusion is about SIDE EFFECTS, not correctness.
  ‼ The item was filed as FIVE; the sweep found a SIXTH (`repro_double_faint`) that was invisible
  precisely because THIS FILE said it needed a real mgba. ⛔ **"Environmental" is a CLAIM — run it
  before you believe it**, and note that a figure here tells readers what NOT to run, which is why
  a stale one is self-sealing. ⚠ These scripts are NOT in `run_gates.py`; see
  `#24-reprosweepratchet` for the structural fix. *(Superseded text: the 5 were said to need a real mgba or have harness issues —
  `repro_boss_training`, `repro_double_faint`,
  `repro_navigate_failfast`, `repro_sufficiency`), plus `repro_x4_lanes`, which **spawns real
  lane processes** — skip it unless you mean it.
- ⛔ **Use the 150s cap in the snippet above, NOT 90s.** *(This line read "~90s" until 2026-08-23 —
  TEN LINES BELOW the entry recording the 90s cap as one of the bugs it caused. It is exactly the
  half-updated pair P2 exists for: the correction landed in the new prose and the old instruction,
  which is the one a reader COPIES, was left alone.)* 25s misreports slow-but-healthy scripts.
- The faithful end-to-end harness is `tools/story-dev/story_harness.py` (needs a real mgba).
  Its `--driver` list is the project's main debugging surface. ⚠ **The enumeration below is
  WATERMARKED 2026-08-08 and is NOT exhaustive** — later drivers (e.g. `boxcounter`, `boxcounter2`,
  the `ch20room*` family, `boxwrite`, `partypids`) are documented in `03-PUNCH-LIST.md` and
  `04-HANDOFF.md`'s HOW TO RUN / TEST instead. ⛔ **For the live list, read `--driver`'s `choices=`
  in `story_harness.py`, never this paragraph.** The ones added by 2026-08-08 are **capability
  tests**, each answering one binary question in
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

- ⛔⛔ **THERE ARE THREE DIFFERENT ANSWERS TO "IS THIS TILE WALKABLE", AND THEY DISAGREE.** This is
  load-bearing architecture, not trivia — it cost §Ch21 leg 3 a drive on 2026-09-01.
  1. **`get_map_data(map, tile)`** builds a `MapLocation` from the **STATIC ROM header**
     (`gMapGroups`, map.py:1774-1789). This is what `calculate_path` plans on.
  2. **`get_map_data_for_current_position()`** builds one from the **LIVE `gMapHeader`**
     (map.py:1742-1751) — a different layout whenever a map ran `setmaplayoutindex`.
  3. **`gBackupMapLayout` → `sBackupMapData`** is the grid **the game itself walks on**. It is the
     only one of the three that reflects `setmetatile`, because (1) and (2) both dereference a
     layout blockdata pointer that lives in **ROM** while `setmetatile` writes **RAM**.
  ‼ **AND (1) AND (2) SHARE ONE CACHE.** `_map_layout_cache` (map.py:735-755) is keyed by
  **`(rom id, map)` ALONE** and does not record which header filled it, so **whichever reader
  touches a map first wins for the whole process** — and `calculate_path` silently inherits that
  choice. MEASURED: seeding SOOTOPOLIS_CITY statically gives `(43,32)->(29,53)` = 37 waypoints;
  seeding it live gives 35. *The seeding order changes production's own answers.*
  ⇒ **On any map that runs `setmaplayoutindex` or `setmetatile`, a planned route must be checked
  against reading (3) before it is followed.** The instruments are
  `tools/story-dev/probe_live_mapgrid.py` (offline, any save state, border offset CALIBRATED not
  assumed) and `modules/story/sootopolis.py`'s `_live_collision_grid()` / `_live_wall_tiles()` /
  `_pin_planner_to_live_layout()` in production. ⛔ Those production helpers currently live in a
  CHAPTER module; promoting them into `modules/map.py` is the open follow-up (see KI-74).
  ‼ **AND THAT CHAPTER MODULE IS NOW DISPATCHED** (2026-09-02): `modules/story/sootopolis.py`
  is wired as **Segment 21** in `plugins/custom_modes/story_mode.py`, immediately after
  Ch20's block, via `do_sootopolis_chapter()` / `ch21_chapter_done()` — so these helpers now
  run in a PRODUCTION story path, not only under a harness driver.
  ⛔⛔ **AND THERE IS A *FOURTH* READING, BECAUSE READING (3) IS BLIND ON SOME MAPS
  (MEASURED 2026-09-02, Sootopolis Gym 1F).** `_live_collision_grid()` keeps only the collision
  bits — `(block & 0x0C00) >> 10` — and `ScrCmd_setmetatile` ORs `MAPGRID_IMPASSABLE` **only when
  its 4th argument is TRUE**, which every `setmetatile` in that gym passes as FALSE. So the floor
  can change completely underneath a run while both `_live_collision_grid()` and
  `probe_live_mapgrid.py` report **zero** differences and PASS. ⇒ **a PASS from those two on a
  `setmetatile` map is a FALSE NEGATIVE BY CONSTRUCTION.** The reader that works is
  **`sootopolis._live_metatile_grid()`**, which keeps the metatile id — `block & 0x03FF` — and it
  is A/B PROVEN: one step on thin ice moved the metatile grid by 1 tile (`0x20d → 0x20e`) and the
  collision grid by 0. ‼ Pick the reader by WHAT THE MAP MUTATES, not by which one you have.

* **`modules/story/sootopolis_gym.py`** — §Ch22 (Gym 8, Juan). ✅ **A FULL CHAPTER, DISPATCHED AS
  SEGMENT 22** (2026-09-03) via `do_sootopolis_gym_chapter()` / `ch22_chapter_done()`. ⛔ Its
  completion predicate is the badge **AND a position**, because `BADGE08_GET` is set while the bot
  still stands on a 20-tile island it cannot walk off — proven by two fault arms that strand it in
  two different places and both FAIL.
  It is the tree's only map where **`calculate_path` must never be used**: the locked stairs are
  `MB_SLIDE_SOUTH` with collision **0**, so the planner happily routes straight through them, and
  the ice puzzle is an **exact cover**, not a shortest path. The route is therefore a
  **precomputed table** generated from the decomp by `tools/story-dev/solve_gym_ice.py` and
  re-verified against `_live_metatile_grid()` before and after every step.
  ⛔⛔ **AND READING (3) IS NOT OPTIONAL EVEN WHEN THE READER'S NAME SAYS "CURRENT POSITION"
  (MEASURED 2026-09-02).** `get_map_data_for_current_position()` builds its `MapLocation` from the
  LIVE `gMapHeader` but resolves `_map_layout` through the SAME shared cache, so once any reader has
  seeded a map statically it returns the STATIC layout's answer. Standing ON FOOT on live sand at
  ROUTE131 (36,7) it reported `tile_type='Deep Water'`. ⇒ **on a layout-swapped map, `tile_type` /
  `collision` / `elevation` guards are worthless until that map is pinned** — `_live_collision_grid`
  (`gBackupMapLayout`) is the only trustworthy live oracle. Proven end-to-end on ROUTE131: un-pinned,
  `calculate_path(ROUTE131 -> ROUTE126)` does not mis-plan, it RAISES, and the bot never moves.
  * ‼ **The state is the full tuple of object positions**, not "5 counters mod 4": pads do not all
    hold three objects, and nine TRAINERS rotate along with the 21 statues.
  * `tools/story-dev/probe_gym_arrows.py` dumps the arrow field and derives the encoding from data;
    `probe_gym_simulate.py` is the validation gate that presses a switch for real and requires the
    simulator to have predicted every loaded object, keyed on `local_id`. **PASS: 11/11.**

* **`modules/story/victory_road.py`** — §Ch23 (Victory Road, and the League-approach shop/heal).
  ✅ **A FULL CHAPTER, DISPATCHED AS SEGMENT 23** (2026-09-05) via `do_victory_road_chapter()` /
  `ch23_chapter_done()` at `plugins/custom_modes/story_mode.py:5130`. Eleven legs, each with a pinned
  fixture (`post_badge8` → … → `post_league_shop`). ⛔ DO NOT REBUILD.
  ⭐ **2026-09-26: its training leg (`train_for_victory_road`) no longer REFUSES an over-ceiling climb —
  it trains it in bounded CHUNKS** (`ch23_chunk_target`, each ≤250k estimated and inside a real-frame
  purse; trainees resolved by PID across evolution; a loud refusal only when no team-mate can finish for a
  swap-trainee). That refusal ended 30 of 39 organic badge-8 runs. USER RULING 14; skip-the-fix arm
  `POKEBOT_CH23_FAULT_NOCHUNK`; offline gate `probe_ch23_chunk_plan.py`.

* **`modules/story/pokemon_league.py`** — §Ch24 (the Elite Four). ✅⭐ **THE SEQUENCER EXISTS AND
  PASSES (corrected 2026-09-25): `run_the_gauntlet()` chains all five legs in ONE run** — lobby →
  Sidney → Phoebe/Glacia/Drake → HALL4 → Wallace → a cleared game (`ACCEPTANCE: PASS`, `battles=5`,
  all `Won`). ✅ **AND IT IS WIRED INTO `_play` AS SEGMENT 24 (2026-09-25 evening)** —
  `ch24_chapter_done()` + the dispatch + the retargeted end-of-content banner. *(This paragraph said
  "nothing here is wired into `_play` yet" until 2026-09-26 — stale for a day, found while documenting
  §Ch23.)* ⚠ The ORGANIC hand-off into it is undriven and has known gaps: `#26-ch24organic`. ⇒ the gap is the CALLER,
  not the legs — which was already true on 2026-09-24 and is the half that did NOT change.
  *(superseded: "NO SEQUENCER AND NO SEGMENT 24 DISPATCH — but no longer PREP ONLY".)*
  ✅ **THREE REAL LEGS NOW SHIP HERE, ALL DRIVEN AND PASSING, ALL HARNESS-ONLY ON PURPOSE**, plus the shared
  `beat_the_trainer_here()` that two of them call (extracted from `fight_one_room` 2026-09-25 and proven
  behaviour-preserving by re-driving all three room pairs BIT-IDENTICAL). ⭐ **`enter_the_league()`**
  (`--driver ch24bridge`) is THE BRIDGE: it latches, checks a three-conjunct premise, crosses `(9,1)` — the
  POINT OF NO RETURN — reaches HALL5, enters SIDNEY'S ROOM, settles on `VAR_ELITE_4_STATE` rather than a
  hardcoded tile, beats Sidney, and ends EXACTLY on `fight_one_room`'s premise for the first pair.
  ⛔ It is what makes a room loop possible at all: before it, nothing connected the lobby door to that premise.
  And:
  `prepare_and_open_the_league()` (`--driver ch24entry`) gets the party ready OUTSIDE, walks in,
  talks the guards aside, ASSERTS they vacated, and stops on `(9,3)` **without** stepping onto the
  point of no return. ⛔ **Its R1 READINESS REFUSAL (`#26-ch24organic`, 2026-09-26)** raises BEFORE the
  walk to the door when, after training, fewer than `min(4, party size)` members are at `floor` (USER RULING 15)
  or a `LEAGUE_BASKET` line is short
  (pure decision `ch24_readiness_shortfall`; gate `probe_ch24_r1_refusal.py`; arms
  `POKEBOT_CH24_FAULT_NOTRAIN` / `POKEBOT_CH24_FAULT_NOREADY`) — until then it only recorded the
  shortfall and walked in anyway. ⭐ **Then its RETURN BRIDGE (`return_to_league_door`, gap 2)** gets a ready
  party from wherever training ended back to EVER_GRANDE_CITY (18,6): no-op in the lobby / on (18,6); WALK
  when the plateau connects (avoiding the (18,27) return trap); else step out of Victory Road, check Fly's
  preconditions BY NAME, fly to the Pokémon League and ASSERT THE TILE (`fly_to_destination` accepts any
  landing that moved). Gate `probe_ch24_bridge.py`; arms `POKEBOT_CH24_FAULT_NOBRIDGE` / `…_BRIDGEDEST`.
  ⭐ **`ensure_fly_learner` (gap 3)** teaches HM02 in `_play` after the §Ch24 latch and before
  `train_for_league` (learner + slot = `_fly_teach_plan`: never strips the last USABLE attack; verified by PID;
  never raises for a missing learner); gate `probe_ch24_flyteach.py`, driver `--driver ch24handoff`. ⭐ **Gap 4:**
  `train_one_for_league`'s return ticket — no Fly + on the League plateau + a `VICTORY_ROAD_*` rung ⇒ a named
  `no_ground`, never a walk into Victory Road's exit half (pure `_plateau_walkoff_refused`, gate B6); and `fight_one_room(from_room, hall, to_room, victory_flag)`
  (`--driver ch24room`) — the gauntlet's **species-agnostic repeating unit**: dismiss the parked
  victory msgbox → bag heal → room → hall → next room → locate the trainer **LIVE** → engage → win
  (asserted on the defeat FLAG) → prove the exit door is open in the **live** collision grid.
  ‼ `fight_one_room` names no Pokémon, move or type — deliberately, because the user's goal is that
  the team lineup VARY between runs (`06-DECISIONS-LOG.md`, 2026-09-24).
  ⛔ Its engage loop must NOT poll `battle_is_active()`: a battle pushes a controller above the story
  generator, so that poll is only ever scheduled while it is false. It detects the SUSPENSION
  instead (a frame-count jump across one `yield`). See `08-MISTAKES.md` 2026-09-24.
  What this module also ships, built and driven: `heal_party_from_bag` (`#24-e4healing`,
  `--driver ch24heal`, the only healing the gauntlet can ever have), `use_item_on_party_member`,
  `teach_move_from_bag` / `scroll_to_tm_verified` (the Ice Beam trip for Drake), and the Ever Grande
  routing constants.
  ‼ **WHAT MAKES THIS CHAPTER UNLIKE EVERY CHAPTER BEFORE IT:** five consecutive fights, ~25
  opposing Pokémon, **no reachable nurse and no way back** — every backward warp in the League
  interior sits on an `MB_NORMAL` tile and all three warp paths in `src/field_control_avatar.c`
  reject `MB_NORMAL`, so they are destination-only and never fire. ⇒ the bag is the ONLY healing,
  and the gauntlet is ALL-OR-NOTHING (a white-out calls `ResetEliteFour` and forfeits the run).
  ⛔⛔ **WIDENED 2026-09-18, VERIFIED AT THE DECOMP:** it is not only a white-out *in the gauntlet*.
  `data/event_scripts.s:585-586` — `EventScript_WhiteOut::` calls
  `EverGrandeCity_HallOfFame_EventScript_ResetEliteFour` **unconditionally** ⇒ **a white-out
  ANYWHERE IN HOENN wipes `VAR_ELITE_4_STATE` and the four `DEFEATED_ELITE_4_*` flags.**
  ⇒ ⭐ this is why `IS_CHAMPION` is the marker's second term (`#24-markerwinstate`): it is set in
  exactly one place and cleared nowhere. ⛔ **Never treat the `DEFEATED_ELITE_4_*` flags as evidence
  the league was beaten** — a faint on Route 101 is enough to clear them.
  ⛔ **AND `calculate_path` CANNOT ROUTE THROUGH ITS OWN DOORS** — the victory script opens the exit
  with a runtime `setmetatile` into `gBackupMapLayout` while our planner reads a ROM pointer cached
  forever (`modules/map.py:748-755`). That is `KI-74`, **CONFIRMED LIVE at this door 2026-09-16**
  (ROM says (6,1)=(6,2)=BLOCKED, the live grid says OPEN). The working oracle is
  `sootopolis._live_collision_grid()` / `_live_metatile_grid()`, exactly as for the Sky Pillar.
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

### `fix_doc_citations.py` — citation-drift repairer (added 2026-09-14)

`audit_doc_citations.py` (Tier 0, in `run_gates.py`) fails when a documented `file.py:LINE` citation
no longer lands inside the symbol it names — which happens every time an edit shifts line numbers.
It fired **five times in two days**, always with the same mechanical fix.

    cd tools/story-dev && PYTHONUTF8=1 py -3.12 fix_doc_citations.py [--dry-run]

⛔ It is a REPAIRER, not a gate: the audit stays the authority and stays in `run_gates.py`; this only
applies corrections the audit has already computed, and it cannot invent a target (every new line
number comes from the audit's own "spans `file.py:A-B`" clause). It refuses ambiguous lines rather
than guessing, never changes a file's line count (the `03`/`04` R3 budgets sit AT their limit),
preserves each file's own line endings (this tree mixes LF and CRLF), and re-runs the audit
afterwards so a partial repair cannot be mistaken for a clean one.

### `probe_punchlist_step_status.py` — gate #61, ENFORCING (added 2026-09-14)

Fails if a `03-PUNCH-LIST.md` item ticks a numbered step `- [x] **N.` while ANY other line inside
that same item says step N still "remains".

    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_punchlist_step_status.py

‼ WHY IT EXISTS: `#24-e4healing` states each step's status in THREE places (a numbered checklist, the
item's cell header, a STATUS line). That contradiction shipped **twice in 24 hours** — 2026-09-13
(step 3) and 2026-09-14 (step 4) — both times caught by a Tier 1 reviewer rather than by a check.
P5 is prose; CLAUDE.md's own rule is that a rule broken twice means the prose failed.

⛔ Deliberately narrow: it does not judge whether the tick is CORRECT, does not read the handoff, and
does not diff. A gate with false positives teaches the reader to bypass it. It ignores a hit whose
own clause carries a dated retraction, because this tree marks corrections by QUOTING the old
wording — and it splits mega-lines into clauses first, so a retraction elsewhere on a 40,000-character
line cannot vouch for an unrelated claim. Fault-tested both ways (reds on the reintroduced bug,
passes on the live tree which contains exactly such a retracted quote).
