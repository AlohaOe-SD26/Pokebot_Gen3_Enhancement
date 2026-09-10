# 14 — AGENT PLAYBOOK (how to work on this program excellently)

> **Read this SECOND, right after `04-HANDOFF.md`.** It is the accumulated craft for
> building the Story bot fast, correctly, and faithfully — the tools, the debugging
> method, the story-mapping method, the faithfulness rules, and the recurring bug
> patterns. Written 2026-07-21 for the next agent (Fable 5) to pick up and *exceed*
> what we've done so far. Keep it current: when you learn a new trick, add it here.

---

## 0. The prime directives (internalize these)

1. **Prove every fix. No guessing.** Reproduce the bug first (ideally a fault-injected
   A/B: show the OLD code fails and the NEW code passes on the SAME input). A fix you
   can't demonstrate is a hypothesis, not a fix. This is the #1 house rule.
2. **Faithful to natural gameplay.** The Story bot is a *deterministic reference* for a
   real playthrough. Prefer doing what a player does (walk there, press the buttons,
   fight the fight). A state-write (setting a var/flag) is a **last-resort fallback**,
   only when the faithful path is impossible/un-provable, and it must reproduce the
   EXACT vanilla end-state. Always gate faithful-first, fallback-second (see §5).
3. **Never hang, never silently derail.** Every loop needs a bound. Every un-fleeable
   battle must resolve to attack/switch → win-or-whiteout. Every "did it work?" gets a
   guard. When stuck, stop cleanly with a diagnostic — don't march on.
4. **Leave it better for the next agent.** Update the handoff, log the change, record
   the mistake + prevention rule, note the intent + *why*. Documentation is cost
   control: it's how the next session avoids re-walking solved problems.

---

## 0a. ‼ HOW TO RUN A MULTI-AGENT ROUND (hoisted here 2026-09-10 — it was stranded in a punch-list stub)

**This is the method that produced the 5-pass deep audit and every good recon round since.** It lived
only inside `#24-sanitycheck`'s closed entry in `03-PUNCH-LIST.md`, where no agent looking for *method*
would ever find it. ⇒ **a closed item is not where a reusable technique should live.**

1. **N agents, ONE ANGLE EACH, sent in ONE message** so they run concurrently. Different ANGLES, never
   the same question asked N times — asking twice buys a second guess, not a second opinion.
2. ⭐ **REQUIRE EVERY AGENT TO FAULT-INJECT OR RE-DERIVE, NEVER TO REASON.** That single instruction is
   what found *a gate that could not fail* and *a control that could not fail*. Make it a hard rule in
   the prompt, and give them an `unverified` field so an honest "I could not check this" has somewhere
   to go other than being dressed up as a finding.
3. ⭐⭐ **PAIR EVERY ANGLE WITH A REFUTER** that is handed the first agent's claims and told to FIND
   ERRORS, defaulting to REFUTED/UNPROVEN when a citation does not establish its claim. Measured
   repeatedly: the refuter is the only reviewer that catches **a true conclusion resting on a false
   mechanism** — a second measurer reproduces the conclusion and stops.
4. **TELL THEM WHAT IS ALREADY RULED OUT**, with citations, so they do not re-derive it — and invite
   them to say if a ruled-out item is wrong.
5. ⛔ **VERIFY EVERY LOAD-BEARING FINDING YOURSELF** before building on it. Across the five passes,
   agent claims failed that check three times and one arrived already STALE.
6. **Output contract:** `SEVERITY | what | what you RAN | result | smallest fix`, terse, anything
   unexecuted labelled CANNOT-REPRODUCE.

⚠ **AND THE COST IS REAL.** A four-angle round with refuters is ~8 agents and ~900k tokens. Use it for
a genuine design fork or a blocked diagnosis — not for a lookup you could grep in ten seconds.
‼ **Freeze the tree while an auditor reads it.** A reviewer handed a diff that shifts underneath it
will (correctly) return KICK-BACK on staleness, and you pay for the whole round twice.

---

## 0b. ‼ BEFORE YOU BELIEVE A RESULT — the eight-question pre-flight (added 2026-08-10)

**Read this before writing a conclusion into any file, and before starting work on any item.**
It is distilled from **eleven wrong conclusions in nine days**, four of them on 2026-08-10 alone.
Every single one had the same shape: **an instrument was trusted without checking it could see
what it was pointed at.** None was carelessness; all were plausible readings of a broken view.

### Before you START on an item
1. **Does the punch list claim it is unbuilt? VERIFY IN CODE FIRST.**
   ‼ **THREE** items marked *"ready to build"* / *"awaiting live validation"* had already shipped
   (`#24-leadcounter`, `#24-counters` phase 2, `#24-r121gate`). One was 8 days stale under a
   heading gating it on a batch that had already landed. **Treat the punch list as a HYPOTHESIS
   about what exists**, and `grep` the code before writing a line.
2. **Is the reason for a deferral still true?** `#24-magmahideout` sat deferred for three weeks on
   *"unreachable — one-way ledges"*. It was an NPC standing on the entry tile. **A deferral is a
   claim with an expiry date, especially if the tooling has improved since.**

### Before you TRUST a measurement
3. **Is my anchor the right ERA, not just the right MAP?** Seven probes ran from badges-1-3 saves
   to answer a post-Mt-Pyre question. **Name the flag/var that gates the content and assert it on
   the anchor** — one `get_event_flag()` would have saved all seven.
4. **Could my detector have returned POSITIVE at all?** A "no" is only evidence if "yes" was
   reachable. One detector polled `battle_is_active()` from inside a generator that is **frozen
   during battles** — it ran 2,466 times, every one on a frame with no battle possible.
   **Print how many times the check ran, beside its answer** (`pumps=7/40000` is readable; a bare
   `False` is not).
5. **Is my before/after comparing the SAME SUBJECT?** An item guard compared HP recorded for one
   Pokémon against whichever mon was active at the next decision — a *replacement* after a faint —
   and blamed the item for a death. **Key such state by identity (`party_index`), and record the
   frame of reference alongside the value.**
6. **Does my fixture actually CREATE its condition?** Assert it and print the assertion.
   A catch fixture spun through **125 battles catching nothing** because the save held zero Poké
   Balls. An injected Pokémon was checked for full HP, party membership and being sent out — none
   of which asked whether **its moves worked**; they did not, and six experiments measured a mon
   that could not attack. **For an injected combatant, assert an EFFECT ON THE WORLD** ("did the
   opponent's HP change"), not a property of the object.
7. **Am I summing populations I cannot both explain?** "62% of boss fights involve healing" mixed
   real potion use with an unexplained small class; the honest figure was **17%**. **Quarantine
   what you cannot explain; never fold it into a headline.**
8. **Is n big enough to say anything?** Finish rate is ~30 runs per 3-hour batch and has resolved
   **nothing in four batches** (25.0 → 33.3 → 16.1 → 28.6%). Battle-level metrics are ~800 per
   batch. **See §0c.**

### Two more that keep earning their place
* **A uniform FAIL is a SYMPTOM, not a cause.** If every case fails, suspect the instrument or a
  shared confound before believing a shared cause.
* **A known bug in a tool is a SEDUCTIVE explanation for anything that tool reports.** KI-24
  (the tile planner mis-reads terrain) was reached for when the planner was correctly modelling an
  NPC. Check the boring explanation — an object, a flag, an era — before the famous one.

---

## 0c. ‼ WHICH METRIC ANSWERS WHICH QUESTION (added 2026-08-10)

Choosing the wrong instrument has cost more time here than any bug.

| question | metric | sample per 3-h batch | can it resolve? |
|---|---|---|---|
| did a whole-run outcome change? | finish rate | **~30 runs** | **NO** — needs ~300 runs (~30 h) for a 10-point move |
| did a battle-level behaviour change? | boss-length win rate, heal events, item landings | **~800** | yes |
| did the counter chain convert? | hunts started vs **REAL** catches (`analyse_conversion.py`) | ~20-30 hunts | only for large moves |
| does a new CHAPTER work? | **the story flag it sets** | **1 run** | **yes — binary, no statistics** |

⇒ **Grade mechanism work on BATTLE-level metrics. Grade content on its completion FLAG.** Quote
the finish rate only as a lagging indicator, and never as evidence for a single change.
‼ And **split reported vs REAL** on any success count: one batch reported 13 counter catches of
which **3 were real** — the rest were Pokémon already in the party.

---

## 0d. ‼ THE INSTRUMENTS — what already exists, so you do not rebuild it (added 2026-08-10)

Every one carries a **positive control** and prints what it searched. ‼ `x4-runs/` is gitignored,
so the **Grep TOOL silently reports 0 on it** — always read batch logs from Bash/Python and print
the byte count.

| tool | answers | note |
|---|---|---|
| `advise_on_diff.py` | which PREVENTION RULES match my current diff | ADVISORY, exit 0 either way; fires at `git commit` via a PreToolUse hook; `--self-test` fault-tests every rule BOTH ways |
| `probe_anchor_inventory.py` | what era/map/party is in every save | reports the map as a **`MapRSE` enum** — `map_name` is a label and interiors carry their city's |
| `--driver anchorcapture` | make an anchor by navigating there | refuses to overwrite, refuses non-controllable states |
| `--driver anchorstory` | make an anchor by letting the REAL bot play to it | `CAPTURE_FORBID_FLAG` guards the ERA — **use it** |
| `analyse_conversion.py` | counter chain: hunts vs **REAL** catches, with a z | splits reported vs real; `--compare <stamp>` |
| `probe_boss_healing.py` | do opponents heal, and how much | **two classes**: ≥50 HP is understood (items); the small class is quarantined and unexplained |
| `probe_fainted_ace.py` | does the bot start battles with mons already down | reads the `hp=` field; older batches correctly report NO DATA |
| `probe_item_index_space.py` | which party-menu index space item use needs | reports NO LANDING RECORDS for pre-telemetry batches rather than "it never works" |
| `probe_r116_east_grass.py` | intra-map reachability with an east/west contrast | the pattern for "is this pocket reachable" questions |
| `--driver groundsweep` | DRIVEN reach-**and-leave** proof for a hunting ground | the only evidence that counts for `HUNTING_GROUNDS` |
| `--driver normancounter` | does a counter at level L beat Norman | ‼ has a CONTROL arm (`NORMAN_MACHOP_LEVEL=0`); natural moveset is the default because the explicit one is **known-broken** |
| `--driver magmadoor` | can the bot reach/enter the Magma Hideout door | scripted movement; see §Ch15 |
| `repro_battle_items.py` | the healing-item policy, exhaustively | 27 checks, **no emulator**, seconds |
| `probe_slide_endpoints.py` | where every current slide in the ROM really ends, and how much of KI-76 is ARMED | ‼ **the pattern worth copying: PRODUCTION IS THE ORACLE.** It classifies on `PathTile.forced_movement_to` — the value `map_path.py` itself computes — and keeps its own replica only for the break REASON, reporting the AGREEMENT RATE (3,763/4,384). v1 replicated production instead and was blind past a map boundary; an adversarial review caught it. ⛔ **Before re-implementing production logic in a probe, check whether production already PUBLISHES the value** |
| `compare_runs.py --label A a.log --label B b.log` | **did my A/B arms actually come out DIFFERENT?** | ⛔ read the **`A/B DISCRIMINATION`** section, NOT the clusters — a cluster tagged `<<< SPANS LABELS` means *the runs AGREE*, the wrong-signed answer to an A/B. It grades on `ACCEPTANCE:` and **names the axes blind to your difference** (added 2026-08-17 after it was measured calling a `FAIL`/`PASS` pair identical on all four original axes) |

**Telemetry now in the bot itself:** `[TURN n]` (one line per battle decision — actor, HP, move,
PP, opponent), `[BATTLE] started hp=[...]` (party HP at battle open), `[ITEM] using/✔ landed/‼ no
effect`, `[ITEM-FLOW]` (per-stage menu trace), `[FAINT-CHOOSER]`, `TEACH EXIT`.

---

## 1. Orientation — get up to speed cheaply

- `04-HANDOFF.md` = you-are-here (current state, next steps, open blockers).
- `12-STORYMODE-DESIGN.md` = the Story chapters, the **Area Atlases** (reconned
  warps/NPCs/coords per area), and the build/validate notes per chapter.
- `08-MISTAKES.md` = every bug/dead-end already solved — skim so you don't repeat them.
- `06-DECISIONS-LOG.md` = *why* things are the way they are (esp. faithfulness calls).
- The bot fork lives in `sandbox-pokebot/` (experimental — build/test here) and
  `custom-pokebot/` (production — promote to here after the user OKs). Story-bot code:
  `modules/story/early_game.py` (segments) + `plugins/custom_modes/story_mode.py`
  (the `StoryMode` bot mode, `_play` resume loop, battle strategies).

Don't re-derive intent from code alone — `01-VISION-AND-DESIGN.md` is the source of truth.

---

## 2. The faithful test harness (`tools/story-dev/story_harness.py`)

**Everything lives in `tools/story-dev/` (committed) — harness, drivers, recon scripts,
and a `saves/` progression sampler; see its README.** It replicates
`modules/main.py`'s main loop EXACTLY (FrameInfo build → listeners → controller-stack
advance → `run_single_frame`), so harness behaviour matches the real bot.

**Run it** (Python **3.12** via `py`; `python` is 3.9 and fails on match statements):
```
PYTHONUTF8=1 py story_harness.py <state.ss1|fresh> --driver <name> [--frames N] [--video] [--profile P] [--log F]
```
- `state`: a `.ss1` basename in `tools/story-dev/saves/`, a full path, or `fresh` (boot a
  new game from the title screen — the intro is handled by StoryMode).
- `--driver story` runs the REAL `StoryMode._play`. Other drivers are focused harnesses
  (see the `choices=[...]` list at the top of the file and the `if args.driver == ...`
  dispatch): `spin`, `gymtest`, `traintest`, `martbuy`, `pokenavtut/clear/skip/faith`,
  `sailrecon`, `rivalretry`, etc. **Add your own driver** for whatever you're isolating.
- `--video` enables the BG/OBJ renderer. **You need this to drive graphics-heavy app
  UIs** (the PokéNav, etc.) — their looped tasks don't advance with the renderer off.
  Emulation is slower with video on; only use it when required.
- The harness logs battle/level/controller transitions + a no-progress dump when it
  stalls. Read the `--log` file for the generator call stack at a hang.

**Save states are raw `get_save_state()` bytes.** Snapshot mid-run with
`pathlib.Path("name.ss1").write_bytes(context.emulator.get_save_state())`. Load with
`context.emulator.load_save_state(path.read_bytes())`.
**The GUI/real bot's `current_state.ss1` is PNG-wrapped** — extract the raw state from
its `gbAs` PNG chunk (`zlib.decompress`) to resume a fresh-run in the harness (see
the fresh-run recipe in `tools/story-dev/README.md`; committed checkpoints are in
`tools/story-dev/saves/`).

**Capture a checkpoint save on a condition** by adding a hook in the main loop (e.g. save
`post_rival.ss1` once `DEFEATED_RIVAL_RUSTBORO` is stable for 120 frames + controllable).
NOTE: event flags have a **1-frame read flicker** during memory updates — require a flag
to be True for *many consecutive* frames before trusting it (a single-frame True is noise).

### 2b. ANCHORS: look one up, and MAKE one when it does not exist (added 2026-08-09)

Most measurements here start from a save anchor, and for a long time anchors were only ever
*scavenged* from crash sites. `#24-r116sweep` then burned two runs on anchors chosen by NAME.
Three tools close that loop — use them in this order:

1. **`probe_anchor_inventory.py` — look it up first.** Loads every save in `saves/` and prints
   map, tile, game state, controllability, badges, party+levels, money. Seconds, no emulation
   loop. `--filter <substring>` for one save.
   ‼ **It reports the map as a `MapRSE` ENUM, and you must too.** `map_name` is a display
   LABEL and interiors carry their city's: `MAUVILLE_CITY_GYM` reads as `"MAUVILLE CITY"`. That
   single ambiguity produced two *different* wrong readings in two sessions (08-MISTAKES
   2026-08-09). **Report identity as the key (enum / id / `(group, number)`), never the label.**
2. **`--driver anchorcapture`** — navigate from an existing anchor to a named map/tile and
   snapshot. `CAPTURE_TARGET=MAP:x,y CAPTURE_NAME=foo.ss1`. Refuses to overwrite an existing
   anchor without `CAPTURE_FORCE=1`, and refuses to write anything that is not an **arrived,
   controllable overworld** (an anchor captured mid-scene makes every later leg fail for one
   harness reason instead of a map reason).
3. **`--driver anchorstory`** — when direct navigation cannot get there but the BOT
   demonstrably can, let the real story bot play until it stands on the wanted map, then
   snapshot. `CAPTURE_FORBID_FLAG=BADGE03_GET` aborts, with a stated reason, if the era window
   closes first. This is what produced `mauville_prewattson.ss1` in 13,666 frames after
   `anchorcapture` failed the same trip 3/3 (KI-48).

‼ **Verify the file with the INVENTORY, not with the driver's own log.** The driver reports
what it believes; the probe reports what the file contains.
‼ **Cross-map fixture travel is unreliable right now** — it failed four separate times on
2026-08-09 (KI-48, KI-49). Prefer an anchor that already stands on the map you need.

### 2b. ‼ THE STANDING GATE SUITE — `run_gates.py` IS the verification bar

⛔ **CORRECTED 2026-08-22 (deep sanity check PASS 5). This section titled a hand-rolled `for f in
repro_*.py` loop "the project's actual verification bar", and the whole playbook — the file every
session is told to read second — did not mention `run_gates.py` ONCE.** The bar is:

```bash
cd tools/story-dev
PYTHONUTF8=1 py -3.12 run_gates.py            # THE bar. Exits non-zero if any ENFORCING gate fails
PYTHONUTF8=1 py -3.12 run_gates.py --list     # the names, and which are slow
PYTHONUTF8=1 py -3.12 run_gates.py --quick    # skips every ROM gate — ⛔ NOT a green suite; never before a commit
```
‼ **`run_gates.py` prints its own gate count and IS the authority — never a number in prose.**
⚠ **TWO ENTRIES ARE `ADVISORY`, NOT GATES** (`probe_regi_capabilities.py`, `probe_dive_routing.py`):
they RUN and print `ADVIS`, and their exit code does not fail the suite, because they report a
KNOWN-blocked arc and a self-declared static probe respectively. ⛔ **Do not "fix" them by giving
them exit codes** — that reds the suite permanently over an accepted state. The reasoning and the
control that keeps the exemption honest are in `06-DECISIONS-LOG.md` (2026-08-22).
‼ Each gate is bounded (`TIMEOUT_FAST`/`TIMEOUT_SLOW`); a HUNG gate now FAILS with `exit=124`
rather than blocking the suite forever — it had no bound at all until 2026-08-22.

#### The wider `repro_*` sweep (still useful, but it is NOT the bar)

`tools/story-dev/repro_*.py` is **103** scripts and `probe_*.py` is **75** (measured 2026-08-17 — ⛔ these decay; run `ls tools/story-dev/repro_*.py | wc -l` rather than trusting this; it was recorded as ~52 for weeks while the suite nearly doubled) and **most need no emulator**. Run the whole
sweep before claiming any fix is clean:

```bash
for f in tools/story-dev/repro_*.py; do
  PYTHONUTF8=1 timeout 150 py -3.12 "$f" >/dev/null 2>&1 && echo "PASS $f" || echo "CHECK $f"
done
```
- **Use `py -3.12`.** Plain `python` on the dev box is 3.9 (unsupported, and the deps are
  not installed for it). Deps needed for the emulator-free ones: `confz==2.0.1`,
  `ruamel.yaml`, `rich`, `numpy`.
- ⛔ **A PINNED EXPECTATION USED TO SIT HERE AND IT WAS ARITHMETICALLY IMPOSSIBLE** — *"47 pass,
  0 fail, 5 environmental"* over a suite that measured 103 scripts then and **104 as of 2026-08-23**
  (47+5=52). Removed 2026-08-22; **grade on `run_gates.py`, never on a remembered tally.** The
  ⛔⛔ **THE "ENVIRONMENTAL" LIST THAT USED TO FOLLOW IS DELETED (2026-08-23).** It named
  `repro_boss_training`, `repro_double_faint`, `repro_navigate_failfast`, `repro_sufficiency` —
  **all four now PASS**, and `repro_double_faint` was broken by a STALE STUB, not by a missing
  emulator. ‼ **"Environmental" is a CLAIM, and it is self-sealing:** it tells the next reader not to
  run the very thing that would refute it. `repro_double_faint` was written off this way TWICE
  (2026-07-30 and 2026-08-23) before a full sweep caught it. ⇒ **run it before you believe it.**
  ⚠ `repro_x4_lanes` remains the ONE genuine exclusion — it **SPAWNS REAL LANE PROCESSES**; skip it
  unless you mean it.
- ⛔⛔ **THIS BLOCK IS A COPY. THE SINGLE SOURCE IS `02-ARCHITECTURE.md`'s sweep section — read it
  there.** *(2026-08-23: this copy went stale while the original was corrected, and a Tier 1 reviewer
  found it. It still said 90s — the cap that misreports `repro_gym_whiteout_guard` — and still listed
  `repro_double_faint` as needing a real mgba, which is EXACTLY the self-sealing misfiling that let
  six broken repros survive, twice. A mandatory-read file teaching the bug the item just fixed is the
  worst possible place for a stale copy.)*
- ✅ **MEASURED 2026-08-23 after `#24-brokenrepros`: `103 PASS / 0 CHECK / 1 SKIP of 104`.** The SKIP
  is `repro_x4_lanes` (spawns real lane processes). ⛔ **`PYTHONUTF8=1` is not optional** — without it
  ~37 healthy scripts die on a `‼`.
- Use a **per-script timeout of 150s, not 90s and not 25s** — a shorter one reports slow-but-healthy
  scripts as errors (this cost a confusing "6 errors vs 5" diff on 2026-07-27).
- ‼ **A fix that satisfies its own new repro can still break the contract an older one
  encodes.** Two separate 2026-07-27 changes did exactly that. Sweep, don't spot-check.

---

## 2b. ‼ RUNNING ANY DRIVER DIRTIES A TRACKED FILE — expected, not damage (added 2026-08-16)

Every `story_harness.py` run appends to **`tools/story-dev/party_accounting_ledger.jsonl`**, which is
**TRACKED, not gitignored** (it is the (P3b) observer ledger — the thing that finally produced
`CRITERION (b) MET`). So after any drive:

* `git status` shows `M tools/story-dev/party_accounting_ledger.jsonl`, and
* `preflight.py` reports **`WARN 1 uncommitted file(s). Review with the user before pulling`**.

⇒ **That WARN is EXPECTED after a drive and is not a broken tree.** ⛔ But do not reflexively
`git checkout --` it either: those rows are a real measurement record. **Commit it with the work
that produced it** (name it in the commit message, as with any staged file).
‼ This is a genuine trap for a cold start: `04-HANDOFF.md`'s STATE row promises a clean tree, and
the session-start ritual runs `preflight.py` — so an agent that drives *before* reading this
concludes the tree is dirty and stops. Flagged by a cold-start agent that hit exactly that.

## 2c. Reviewing an x4 log bundle (this is now a recurring job — reuse this, don't reinvent)

The user runs `ENDLESS LOOP ×4` batches and hands over `P1 - P4 x4 LOGs <date>-<time>.zip`.
Three have been reviewed (`20260726-201838`, `20260726-231412`, `20260727-063751`). The
method below found four harness bugs; the traps below each cost real time when first hit.

**Extract, then read `MANIFEST.txt` first** (lanes, starters, per-lane badge tallies).

**Where the facts live:**
- `*-stdout-*.txt` — `starting run N`, `-> derailed:`/`finished`, `lost a battle at map (g,n)`,
  `recovered from the whiteout`, `derail #N`. **No battle outcomes.**
- `*-debug-*.log` — `BattleOutcome.<X>`, `[MAP]`, `[PARTY]`, `[BATTLE]`, `[STEP]`, `[hb]`
  heartbeats, and `===== DUMP [STUCK …]` with the generator call stack. **One file per run.**
- `badge-log.json` — CUMULATIVE and never archived. Split by `earned_at` against the batch
  start, or you will read months-old records as new.
  ‼ **`run_index` RESTARTS AT 1 FOR EVERY PROCESS.** It is per-batch, not globally unique, so
  grouping a multi-day cumulative file by `run_index` MERGES separate batches and manufactures
  fake duplicate and out-of-order badges. On 2026-07-29 this briefly read as a badge-recorder
  regression across all four lanes; it was an artefact of my own grouping. **Segment first:**
  sort by `earned_at`, then start a new batch wherever `run_index` does NOT increase.
  ```python
  batches, cur, last = [], None, None
  for r in sorted(recs, key=lambda r: r["earned_at"]):
      ri = r.get("run_index")
      if ri is None: continue
      if last is None or ri < last: cur = {}; batches.append(cur)
      cur.setdefault(ri, []).append(r["badge"]); last = ri
  ```
  After segmenting, expect ONE known artefact: a duplicate `Stone` on run 1 of each batch
  (KI-30). Anything else is real.

**The five checks, in order:**
1. **Is this even the current code?** See the pre-fix tells in `28-HANDOFF-ARCHIVE.md` §0a (archived 2026-08-26 — NOT in 04 any more). Two
   bundles were reviewed against code that was never running — the largest single waste in
   this project. Check FIRST, report it FIRST.
2. **Do runs 4+ still play?** Count runs per lane, then read the **last non-`Encounter`
   `[STEP]` line of each debug log**. If late runs cluster on one step, per-run state is
   leaking. This one line exposed a bug that per-run outcome tallies showed nothing of.
3. **Are outcomes honest?** Cross-check each `finished` against that last `[STEP]`.
4. **Badge sanity** — gym order, no duplicates, no gaps, `run_index` stride exactly 1.
5. **The 1:1 canary** — losses:whiteouts has been exactly 1:1 across batches (no potion
   layer exists). Above 1.0 = whiteouts with no battle logged.

**Traps, every one of them paid for:**
- **A bundle can span SEVERAL app launches.** Segment by launch before concluding anything;
  old stdout survives because only debug logs get archived.
- **`MapRSE` and `MapFRLG` share `(group, number)` keys.** Parsing `map_data.py` unscoped
  yields KANTO names — `(8,1)` reads as Lavender Town PC instead of `PETALBURG_CITY_GYM`.
  Scope the regex to the `MapRSE` class body.
- **Look for RUN-INDEX-shaped patterns, not just lane-shaped ones.** "Every lane dies from
  run 4" is invisible in any per-lane aggregate.
- **A wedge shows as one debug log that never closes** — check frames, not file count. A
  lane can burn 30M frames in a single run and look "quiet" in a file listing.
- **`[STEP] 'Encounter…'` lines dominate**; filter them out or they bury the story steps.

---

## 3. The debugging method (reproduce → fault-inject A/B → fix → prove)

1. **Read the user's debug log first.** The opt-in Debug Logging (`modules/debug_logger.py`,
   toggle in the Run menu) writes an event stream + auto STUCK DUMPS with the **generator
   call stack** (where the bot is waiting) — this pinpoints the exact function+line of a
   hang. Battles are excluded from stall detection, so a hang *inside* a battle shows as a
   `[BATTLE] started` with no `ended` and heartbeats stuck at `state=BATTLE/PARTY_MENU`.
   (`GameState`: 1=BAG, 2=CHOOSE_STARTER, **3=PARTY_MENU**, **4=BATTLE**, 7=OVERWORLD…)
2. **Reproduce in the harness.** Load the closest save + a focused driver. If you can't
   reach the state, synthesize it (state-writes to set flags/vars, inject a party) — but
   remember synthetic state can diverge from real (e.g. a rival cutscene repositions you).
3. **Fault-inject A/B when possible.** The gold standard: a tiny script that calls the
   suspect function with a constructed input, shows the OLD code produces the bug, then
   (after the fix) the NEW code doesn't. Examples this session:
   `tools/story-dev/repro_double_faint.py` (double-battle chooser returns the on-field partner)
   and the trainer-battle `decide_turn` mock. These need **no emulator** and prove the
   logic directly — prefer them for battle-strategy / pure-logic bugs.
4. **Read RAM + scripts to understand the game.** `read_symbol("sym")`, `get_event_flag`,
   `get_event_var`, `get_tasks`, `get_global_script_context().stack`, `get_party()`,
   `get_player_avatar()`. Decode on-screen text with
   `decode_string(read_symbol("gStringVar4"))` / `gDisplayedStringBattle`.
5. **Static ROM recon** (no navigation): `get_map_data((group, num), (0,0))` gives any
   map's `.warps` / `.objects` (script_symbol) / `.connections` / `.map_size`. This is how
   we build Area Atlases (see `tools/story-dev/maprecon.py`).
6. **Screenshots** (video on): `context.emulator.get_screenshot().save(path)` — then read
   the PNG. This is how we scripted the PokéNav Match-Call navigation (we literally looked
   at each menu screen). Invaluable for app UIs.
7. **Authoritative game logic** = the pokeemerald decompilation. Fetch scripts with
   WebFetch, e.g.
   `https://raw.githubusercontent.com/pret/pokeemerald/master/data/maps/<Map>/scripts.inc`
   and `.../src/*.c`. This tells you the EXACT flags/vars/multichoice a scene needs
   (how we found `VAR_RUSTBORO_CITY_STATE`, the Match-Call tutorial flow, Briney's sail).

### 3b. ‼‼ RUN BOTH ARMS **BEFORE** YOU WRITE THE FIX (added 2026-08-16, KI-65)

**The rule:** the first thing you build is not the fix and not even the assertion — it is the two
arms, run back to back, **showing they already differ**. If fault-ON and fault-OFF behave
identically, you have a FIXTURE BUG, not a result, and every assertion you layer on top is
measuring nothing.

**Why this is now a step and not advice.** KI-65's spec was corrected TWICE and was still
unusable both times. Its prescribed fixture could not exercise the bug for **three independent**
reasons, none visible from reading the entry: the target line was unreachable on that party's slot
order; the save entered the dialogue at a point where an earlier branch decided the outcome **25
frames before the code under test ran**; and the "most plausible real cause" fault was silently
rescued by a second code path inside the same function. Measured proof it was vacuous: both arms
pressed **the same buttons on the same frames** (`f0 A, f2 Down x5, f12 A x224`).

**Three habits that catch this cheaply:**
* **Trace from the fixture's ENTRY STATE, not from the function's top.** A save parked mid-dialogue
  can have the answer already decided. Ask *"which branch runs FIRST from here?"* before *"which
  branch has the bug?"*
* **Instrument the DECISION, not only the outcome.** Log what policy returned and on which frame.
  `which_move_should_be_replaced(...) -> 1 @f37` versus a cursor confirmed `@f12` is what exposed
  the ordering; a bare pass/fail never would.
* **Prefer an INJECTED fixture to a captured one when the bug needs a specific shape.**
  `debug_write_party` / `debug_create_pokemon` let you put the HM in **slot 0** on purpose. A
  capture gives you whatever the run happened to have — and a capture that *looks* topical is the
  most expensive kind of wrong, because it is trusted. ⛔ Always read the injected fixture BACK
  through the production reader and assert the shape (playbook 0b Q6).

⇒ **`ACCEPTANCE: FAIL` on the unfixed code is a DELIVERABLE.** Record it. A gate that was never
seen red is a gate nobody has tested.

---

## 4. Story-mapping method (how to build a new chapter)

**MAP FIRST, then build, then validate.** (Hard-won: Rustboro cost us dearly by building
before mapping.)

1. **Static recon** the area(s): run `maprecon.py`-style `get_map_data` over the maps to
   get warps/NPCs/connections/sizes. Write it into `12-STORYMODE-DESIGN.md` as an **Area
   Atlas** with a **Hardening Checklist**.
2. **Read the decomp scripts** (WebFetch) for every scripted beat: what flag/var gates it,
   what multichoice/yes-no it shows, where the trigger tile is, what the completion signal
   is. Anchor each segment on a **completion flag** (e.g. `DEFEATED_RIVAL_RUSTBORO`).
   ⛔ **TRANSLATE THE NAME BEFORE YOU USE IT: our accessors take the BARE name — `ROUTE128_STATE`,
   NOT the decomp's `VAR_ROUTE128_STATE`.** The decomp spelling is what you just read and what every
   research note quotes, so this is the default mistake, not an exotic one. `get_event_var` returns
   **−1** for an unknown name, so the prefixed spelling FAILS SILENTLY and reads as "not done yet";
   `_done_var` is the safer door — it RAISES on a name it does not know. Bitten on §Ch20 (2026-08-24)
   and previously on `#24-r121gate`.
3. **Build a segment** in `early_game.py` as a generator. Reuse the helpers:
   `_navigate_through_scripts(map, tile)` (reach a MAP, riding out inter-map scenes) vs
   `_navigate_riding_out(map, tile)` (reach a TILE) — pick by intent, they differ.
   `_ride_out_scripted_scene`, `_wait_until_cutscene_over`, `wait_until_truly_controllable`
   (waits for a STABLE controllable window — the flag flickers), `wait_for_multiple_choice_question(idx)`
   (advances intro msgs, moves the cursor down `idx`, confirms).
4. **Wire it into `_play`** (`plugins/custom_modes/story_mode.py`) as a segment gated by
   its completion flag + an area check, and **guard** it (`_guard(label, done_check)` stops
   with a diagnostic if the segment didn't reach its signal). The resume model re-runs
   `_play` from wherever the player actually is (flags + position), so segments are
   idempotent — never assume you start fresh.
5. **Validate** end-to-end in the harness (`--driver story`), ideally from a fresh run or a
   real checkpoint. Watch for hangs, derails, whiteouts. Fix, re-run, prove.
6. ⛔ **Navigation is LEG-BY-LEG BY RULE, not by luck: `calculate_path` spans only DIRECTLY
   CONNECTED maps.** This is mechanical, not a "sometimes it struggles" heuristic — a generic
   journey call across non-adjacent maps does not path, full stop. Navigate to a staging tile,
   cross the connection, then navigate on the next map. *(Stated as a soft gotcha here for weeks
   — "can't always one-shot" — which invites trying it and hoping; the hard form was buried in a
   CLOSED punch-list item, `#24-r121gate`, where no chapter author would ever look. §Ch20's dive
   leg obeys it — one `navigate_to` per map — but by IMITATION of the chapter before it, not
   because the rule was written down. Examples: Rustboro→Route104, Route116 ledges.)*

### Area research template (fill one out per new area, into `12-STORYMODE-DESIGN.md`)
Keep it accurate and honest — tag anything not yet run `⚠ VALIDATE LIVE`; tag decomp-read
logic `✓ script-verified`. Don't fabricate a stand-here/press-this sequence you haven't run.
```
### <AREA> ATLAS
- MAP <NAME> (group,num) size=(W,H)
- CONNECTIONS: <dir → dest map (offset)>            # map graph — how you walk between areas
- WARPS: <(x,y) → dest map #id>                      # doors/stairs; note which is PC/Mart/Gym
- KEY NPCs / triggers: <(x,y) script_symbol>         # boss, gift-giver, story trigger, items
- SCRIPTED BEATS (✓ script-verified from decomp):
    <beat> — trigger: <coord/flag/var>; interaction: <msgbox/multichoice idx/yes-no>;
             completion flag: <FLAG_...>; gives: <item/HM>; gotchas: <...>
- BUILD PLAN: <numbered steps, each anchored on a completion flag; ⚠ VALIDATE LIVE the coords>
- HARDENING: heal points, type matchups for any boss, leg-by-leg nav notes, expected hazards
```
Sources: `get_map_data` (coords — reliable), pokeemerald decomp via WebFetch (scripted logic —
authoritative), the harness (the ground truth — validate and correct the doc).

---

## 4b. When a map has a MECHANIC: simulate it, then make the game grade your simulator

Some rooms are not walk-and-warp. The Mossdeep Gym has a third movement primitive — floor switches
that relocate 21 statues AND nine of the trainers — and four independent instruments all concluded
it had no route to its own gym leaders, because none of them modelled it. The method that worked,
and that generalises to any puzzle room:

1. **Find the mechanic's DATA, not its behaviour.** The arrows are map layout: baked into ROM,
   never moving. Dump them once (`probe_gym_arrows.py`) and the whole puzzle becomes simulatable
   offline. ‼ DERIVE the encoding from the dump rather than assuming it — print the distinct values
   and let the data name the scheme. Ours produced a free cross-check: the "direction 4/5" tiles
   turned out to be the nine floor SWITCHES, independently reproducing a list obtained another way.
2. **Write the simulator as a PURE module** (`mossdeep_gym_puzzle.py`): state in, state out, no
   emulator. It is then testable in milliseconds and the search can run 10^5 states.
3. **‼ MAKE THE GAME GRADE IT BEFORE YOU PLAN ANYTHING** (`probe_gym_simulate.py`). Walk to a
   switch over the SIMULATED map, press it for real, and require the simulator to have predicted
   every loaded object's new tile — **keyed on `local_id`**. This gate caught a completely wrong
   movement model on its first run, before a single route was planned on it.
   * compare only LOADED objects (`get_map_objects()` is a subset of the templates) and PRINT how
     many were compared, or a comparison over zero objects passes silently;
   * the walk itself is a second test: if the simulator misplaces a statue, the avatar fails to
     arrive and the probe names the step that disagreed.
4. **Search over `(position, world-state)`.** A `(map, position)` key merges genuinely different
   worlds — that is exactly how a model-free brute-force walker found 35 tiles and "proved" the gym
   unsolvable, because it was *changing the map while exploring it*.
5. **Execute by RE-SOLVING, not replaying.** A 117-step plan desynchronises the moment a trainer
   interrupts. Walk until something unexpected happens, then solve again from where you actually
   are; a BFS costs a fraction of a second.
6. **Cross-check the answer against independent derivations, and say which one you believe.** Ours
   matched two offline agent routes switch-for-switch. That is reassuring and is still not proof —
   the driven run is.

‼ **Static ROM facts, live facts, and identity are three different things.** `MapLocation.objects`
reads the map header in ROM and always returns ORIGINAL template positions; `get_map_objects()`
returns live, mutated positions but only for LOADED objects; and neither tells you an object's
identity as an NPC. Say which one you are using, every time — most of this room's wrong conclusions
came from mixing them up.

## 4c. ‼ THE §Ch20 CAVERN METHOD — incremental drivers that INHERIT, and predictions filed FIRST (added 2026-08-14)

The Seafloor Cavern (Rooms 1 → 2 → 6 → 3 driven in one day, every first drive a PASS) distilled
the chapter-building method into a repeatable shape. Reuse it for any multi-room dungeon:

1. **ARBITRATE the route before driving it.** Two sources per room — upstream's shipped
   `puzzle_solver.py` route AND our decomp/ROM reading — checked against each other by an agent
   told to find the disagreement. Room 1's "exhaustive search" uniqueness claim was refuted this
   way before it could ship a wrong route; Room 3's "REFUTED" verdict was itself refuted by the
   deeper pass. ‼ An agent's REFUTED needs the same two independent authorities as a CONFIRMED.
2. **One DRIVER per increment, and each driver INHERITS the previous one** (`Ch20Room3Mode →
   Ch20Room6Mode → Ch20Room2Mode → Ch20Room1Mode → Ch20DiveMode`). The cavern's rocks and
   boulders are `FLAG_TEMP_*` objects that respawn on every map load, so every deeper drive
   RE-SOLVES and RE-PROVES every room beneath it — replication for free (Room 1 reached n=7).
   ⛔ Copy a proven phase into a new driver and it will rot; SUBCLASS it and it cannot.
3. **Predictions are PRE-REGISTERED in an `ai-research-notes/` file BEFORE the run**, each with
   "if it FAILS, what that means". Scorecard so far: 6/7, 10/10, 8/8, 6/6-ish — and the single
   most valuable output of the whole campaign (KI-77) came from the one prediction that FAILED.
4. **The A/B is the result, not the arrival.** Measure the blocked route (NO-PATH) before the
   solve and the open route (OK) after, with live objects both times — a one-armed "it worked"
   cannot rule out "it was open all along". Use a THREE-point A/B when two obstacles could each
   explain the opening (Room 2's M1/M2/M3 attributed it to the pushes, not the smash).
5. **Failure branches get a PERMANENT env-gated fault hook, never a temporary edit** —
   `POKEBOT_CH20_FAULT=room1` forces the Room 1 solve to fail so the drivers' failure branch is
   exercisable on demand (registry §A3). It exists because an `AttributeError` lived on exactly
   the branch three green runs never took, and a fault-mode run MUST print `ACCEPTANCE: FAIL`.
6. **Measurements are REPORTED, not graded, when they test a claim rather than the run** —
   Room 3's `saw_double` measured a decomp claim; grading on it would have turned "we learned the
   claim was wrong" into "the run failed". And ‼ scope every count out loud: the discriminator
   once printed a false REFUTED by counting trainer battles RUN-WIDE instead of in-room.

Driver chain + expected outputs: `04-HANDOFF.md` → HOW TO RUN / TEST. Room adjudications:
`ai-research-notes/2026-08-13-ch20-*.md` (spec corrections, Room 8's 9-push sequence — ⛔ step 9
faces LEFT, never UP — and the Route 128 atoll exit).

## 5. Faithfulness rules (natural-first, state-write fallback)

- **Do it the player way when you can.** We proved the "impossible" faithful path more than
  once (e.g. the PokéNav Match-Call tutorial — the app just needed the renderer on; we then
  scripted HOENN MAP →Down,Down→ MATCH CALL → call Mr. Stone → B out).
- **Renderer-gated fallback pattern:** `handle_pokenav_match_call_tutorial()` does the
  faithful play-through when `context.emulator.get_video_enabled()`, and falls back to a
  state-write (`skip_pokenav_match_call_tutorial`) when headless or if the nav stalls. This
  is the template: *faithful when possible, deterministic fallback always, never hang.*
- **A state-write must reproduce the EXACT vanilla end-state** (every var/flag the scripted
  completion sets), so the resulting save is indistinguishable from having played it. Log it
  in `06-DECISIONS-LOG.md` and (on promotion of an upstream-file edit) in the
  `custom-pokebot/DIVERGENCE-LOG.md`.
- **Ask the user** when a faithfulness tradeoff is genuinely theirs to make (we did for the
  tutorial skip; they chose faithful-with-fallback).

---

## 6. Battle robustness principles (from real bugs)

- **Un-fleeable battles (trainer/gym/E4) MUST fight through.** Every turn resolves to an
  ATTACK or a VALID switch — never a flee (raises "can't run from a trainer") and never a
  switch that can't complete. When in doubt, ATTACK (the game Struggles if all PP is 0), so
  the fight plays through to win-or-whiteout (→ recovery). The Story bot's
  `LevelUpTravelBattleStrategy` now does exactly this and does NOT proactively rotate in a
  trainer battle (rotating into a weak bench stalled the party-menu switch — the Roxanne hang).
- **Switch targets must be benched, non-fainted, non-active, selectable.** In a DOUBLE
  battle you must exclude the on-field partner (we fixed `choose_new_lead_after_faint`
  dropping that check — it returned the partner's slot and stranded the party menu). The
  fainted/active/HP checks live in `get_potential_rotation_targets` / `_can_battle`
  (HP% > `hp_threshold` + a usable damaging move) / `choose_new_lead_after_faint`.
- **Prep before a boss:** type-aware lead (never lead a 4×-weak mon — e.g. Marshtomp is 4×
  weak to the rival's Grass), a whole-team **level floor** (all ≥ N, escalating on losses),
  a **safe PC heal** right before, and an **attempt-cap** so a loss retrains + retries a
  bounded number of times, then stops cleanly (see the Rustboro rival §5c).
- **Heal EARLY in swap-training** (big margin above the flee threshold) so the finisher
  doesn't faint mid-battle and strand the choose-next-mon menu.
- **OPEN framework issue (for you to pin):** the mid-battle rotation *execution*
  (`modules/battle_action_selection.py` `TurnAction.RotateLead` →
  `scroll_to_party_menu_index` → `while PARTY_MENU: press A`) can stall if the target is
  mis-mapped (`map_battle_party_index`) or the party-menu submenu default isn't "SHIFT".
  The Story bot sidesteps it (attack-only in trainers), but any rotating strategy is exposed.
  Reproduce a live rotation into a specific slot and confirm the selection completes.

---

## 7. Recurring bug patterns → prevention rules (memorize)

| Pattern | Prevention |
|---|---|
| Keying off a **persistent progress flag** to detect a re-triggerable event | Detect the LIVE event (battle active / the coord-script on the stack), not a one-shot "met/done" flag (the MET_RIVAL retry bug). |
| **Fainted/on-field mon selected** as a switch target | Every switch chooser excludes fainted + already-active (double-battle partner!) + eggs; falls back to any alive benched mon. |
| **Un-fleeable battle** flees/rotates into a dead end | Attack-through; never flee a trainer; never rotate into a target that can't complete. |
| **Headless renderer** off → app UI never advances | Graphics-heavy apps (PokéNav, …) need `--video`; gate faithful-vs-fallback on `get_video_enabled()`. |
| **Cross-map navigation** fails as one shot | Go leg-by-leg (stage tile → step across the connection → navigate next map). |
| Returning from a scene while **not controllable** | `wait_until_truly_controllable` (STABLE for N frames — the flag flickers). |
| **Event-flag read flicker** (1-frame True) drives a wrong decision | Require the flag stable for many consecutive frames before acting on it. |
| `_navigate_through_scripts` used to reach a **tile** | It reaches a MAP; use `_navigate_riding_out` for a TILE. |
| Building a chapter **before mapping** it | Static-recon → Atlas → build → validate. Always. |
| A flag-gated combat segment with **unbounded** whiteout re-entry | Attempt-cap + clean fallback to manual; never loop forever. |
| Talking to a **PATROLLING NPC** via its spawn tile, a navigate-chase, or blocking its route | `_talk_to_wandering_npc`: OBSERVE a lap (record both walkers' routes) → park BESIDE the route (on NOBODY's route, not a warp) → face-tap+A when he transits the adjacent tile. A tail-chase never catches a same-speed walker on a ring; blocking a shared ring queues the WRONG walker against you (Briney/Peeko, 2026-07-22). |
| A chapter's test says **"controllable"** and calls that done | *"Controllable" is not "able to continue."* Assert the bot is somewhere the NEXT chapter can start from — cheapest form is a real `calculate_path` to where it must go next. §Ch18 passed `badge + controllable` twice while parked on an 11-tile island (2026-08-12); §Ch15 did the same four floors underground (KI-56). **This is the most re-learned rule in the project.** |
| A world-model advanced from **the PLAN** rather than the observation | Update state from what actually happened — the tile the avatar LANDED on, not the step the route intended. The whole reason to re-plan is that the plan sometimes doesn't happen (Mossdeep gym warp, 2026-08-12). |
| A movement rule inferred from a **set of positions** | A set says which tiles changed occupancy; it cannot say WHO moved where. Key any "what moved" measurement on `local_id`, or it will confirm whichever hypothesis you brought (statue puzzle, 2026-08-12: rigid rotation 6/6 vs ordered slide 2/6 on the same data). |
| **"The avatar refuses to walk"** → theorising about input/timing | Print `get_global_script_context().stack` FIRST. Four runs were lost to input theories; the stack said `EventScript_ShowTrainerIntroMsg` in one line — a trainer had line of sight (2026-08-12). |
| A **readiness check** used to decide that nothing will start | A readiness check tells you the game is ready NOW, never that nothing is about to start. Landing on a coord_event/warp tile has a window where the avatar reads idle before the script takes hold. Confirm a warp by its DESTINATION TILE; hold switch waits open with a frame floor. |
| An **error type** that the recovery cannot catch | An error type is part of an interface. When you write a recovery, assert the failure it recovers from can actually REACH it — `walk_to_the_leaders` raised `RuntimeError` where its chapter caught `BotModeError`, silently disabling the whole retry (2026-08-12). |
| A **hand-driven generator** used to test anything that must survive a battle | Battle handling does NOT run inside a bot mode's generator; it lives in the main loop's listeners (`modules/battle_fault.py:5`). A probe driving a generator by hand cannot win a fight — it will sit until its budget expires. Use a real `--driver` for that; use probes for logic and guards. |
| Changing a **drift / gate / ladder COUNT** in the docs | ⛔ It is a MULTI-FILE, MULTI-SPELLING fact. Grep the WORD forms too — `ONE`, `zero`, "everything is promoted", "that one file" — not just the numeral, and never edit it only where you happen to be looking. One drift line went stale **three times in a single day** because it spelled the count as an English word naming a file, so every numeral sweep missed it. ‼ Do the edit as a SCRIPT that asserts each expected string is present AND unique and **applies nothing on any miss** — a partial sweep is the hazard; an atomic one fails loud. ⚠ **`audit_doc_consistency.py` enforces this, but it is a FLOOR, not a sweep — and on 2026-08-16 it MISSED one.** It has known word-numbers since the spelled-out "THREE" incident, but its patterns matched only phrasings an AUTHOR picks (`drift is N`, `EXPECT EXACTLY N`) and **not `N differing` — the format `promote.py --check` itself PRINTS**, which is what the docs quote most. A stale one survived a 13-site hand sweep AND the gate; an adversarial review found it, and adding that one pattern immediately surfaced THREE MORE. ✅ **Fixed 2026-08-16** (scoped to an EXPECTATION so historical measurements stay quiet; D6/D7/D8 fault-test it). ⇒ *when a gate polices a number a TOOL emits, the tool's own output string is the FIRST pattern it needs.* ⇒ the sweep is not where your effort goes: change the figure, then **run the gate and fix exactly what it names until it is silent**. The gate is the enumeration; grep is not. ⚠ Its two limits: it cannot tell a QUOTATION or a NEGATION from a claim. ⚠ `audit_doc_consistency` matches literals and cannot tell a QUOTATION from a claim, so DESCRIBE superseded wording, never reproduce it. |
| **PROMOTING a behaviour change** (as opposed to a comment) | ⛔ `1/1 byte-identical` proves the file was COPIED, never that its new branch is what RUNS. Prove execution with the feature's own **fault hook**, and capture the BEFORE arm *first* — it is unrepeatable once the copy happens. The shape: same command, `POKEBOT_*_FAULT=1 --build custom`, **PASS before (hook absent, inert) → FAIL after (hook fires) → PASS after unfaulted**. Three points, so the promotion is isolated as the cause. ‼‼ **AND WHEN THERE IS NO FAULT HOOK — a GUARD, or any structural change — MEASURE THE PROPERTY WITH A `--build`-AWARE INSTRUMENT INSTEAD (added 2026-08-16, KI-81).** A guard has no branch to flip, so the fault-hook shape does not apply; the question is whether the FORK'S OWN code now has the property. `probe_abort_swallowing.py --build custom` answered it: **53 → 45** candidate sites, with the per-file guarded-handler counts moving **0→3 / 0→4 / 1→2**. ⇒ *if the change has no hook, give the probe a `--build` flag — the number must MOVE across the copy.* Same rule as ever: the BEFORE reading is unrepeatable, so run and COMMIT it first. ‼ And expect `promote.py` to REFUSE a dirty tree — that is the tool working; commit the baseline, do not route around it. |
| An **A/B seen in the terminal** and then written up from memory | ✅ **FIXED 2026-08-16 (`#24-orphans` (4)): the default log name is now unique per run** (`harness_<build>_<driver>_<timestamp>_<pid>.log`), and the run PRINTS its path as the first line. It used to be one fixed name per build opened `"w"`, so the second arm of an A/B silently DESTROYED the first arm's transcript — that cost a Tier 1 kick-back on 2026-08-15. ‼ Still capture stdout separately for anything graded on `console.print` output: production's rich output is NOT in the harness log. ⚠ Four sibling repro scripts still have the old pattern — see `#24-logcollision-siblings` in `03-PUNCH-LIST.md`. |
| A **test that RE-IMPLEMENTS the predicate it is testing** | Ask PRODUCTION the question instead. To prove "only X could have been returned", call the real function again with X ALSO excluded and require `None` — zero re-implementation, and it stays correct when the function changes. `repro_box_counter_move_test` fault-injected by RE-CODING type-only against fakes, so the REAL hook could have rotted unnoticed; the `sole` control repeated the sin until 2026-08-15. |
| A **constant copied between documents** (a type set, a coordinate, a threshold) | DERIVE it from the source of truth at runtime and GRADE the derivation against the written expectation, so a change is loud. *Agreement between documents is not evidence — they may all be copies of one another.* `Winona needs Rock/Ice/Dragon/Electric` stood in FOUR files for a year; the first derivation from the live type chart killed it in one run (Electric is 0.5x into Dragon, so 1.0 on Altaria). |
| An assertion that **cannot fail** | Before grading a step, ask: *would this still pass if the feature were entirely absent?* If yes, add a CONTROL arm that removes the feature and show the outcome CHANGES. "`hunted_pids` puts the counter in slot 0" passes trivially whenever the counter already had the best matchup — the `hunted_pids=None` control (`control=Mightyena L38` -> `real=Slugma L15`) is the only thing that made it evidence (2026-08-15). |
| An **anchor save** accepted on era / map / position / party | ⛔ **An anchor is not verified until something has ROUTED from it.** Add "and `navigate_to`/`calculate_path` reaches the first destination the test needs". A Stage 2 anchor was 'corrected by measurement' onto ROUTE120 — correct on era, map, position AND party, and unable to reach its own Pokemon Center, because Routes 118/119/120 are the dual-elevation-bridge maps `calculate_path` reads as WALLS (KI-24, documented in our OWN `region_reach.py:7-11`). ‼ The word MEASURED never says WHICH question was measured. |
| A dict/set/`in` test keyed on a **bare PID** | In Gen 3 the PID is NOT unique — a Shedinja carries its Ninjask's PID (KI-78). The identity is `(personality_value, species)`. This bites test instruments too: a PID-keyed party map reported a FULL PARTY OF 6 AS 5, on the very save chosen because it contains that collision (2026-08-15). |
| A **subclass** reusing a driver phase that ends in `set_manual_mode()` | Split the phase into a body that returns a verdict and a thin `run()` that terminates. Inheriting a terminator drops the bot to Manual before the subclass's first line — and under KI-71 that is SILENT: no exception, no crash, a healthy-looking idle. |
| A **green happy-path run** treated as coverage of the error paths | A branch exists because something can go wrong — so make it go wrong. Fault-inject (patch the predicate, force the loss) rather than asserting the fix. |
| **ORDER** of a list that more than one consumer reads as meaning | A wrong order is a silent logic bug, not cosmetics. `chapters.py` ordering drove BOTH `badges_before` and the bracket in `current_chapter()`; one swapped pair made the detector skip two whole beats (KI-61, 2026-08-12). Order claims in docs need the same evidence bar as code — "order confirmed" was written there and was wrong. |
| Markdown edited through a **double-quoted shell string** | Backticks become command substitution: your citations are deleted and the script still exits 0. Use the Edit tool or a quoted heredoc (`<<'EOF'`). Corrupted three doc edits in one session (2026-08-12). |
| **Face-tap toward an empty tile STEPS** (if already facing that way) | Only face-tap toward a tile the NPC currently OCCUPIES (a bump can't step), and re-verify it's still there before pressing A. |
| **Standing on a walk-sequence NPC's route tile** freezes the room | Walk-sequence NPCs wait forever for their exact next route tile (no re-routing) — a blocked queue can deadlock every actor incl. the player (three-body gridlock). Park OFF-route; if walkers freeze, step off the route to unfreeze. |
| `navigate_to` reports **"no path" in a small room with walking NPCs** | `calculate_path` blocks every object's current AND previous tile — two walkers seal a tiny map at plan time. Use greedy manual steps (with perpendicular fallbacks + warp-tile avoidance) for indoor approach work. |
| Building a **multi-floor/warp route** from atlas prose or memory | Compute the pairwise within-floor warp pathability graph FIRST (`calculate_path((map,a),(map,b))` statically — no walking, no emulation of the route) and derive the chain from that. Granite Cave: every floor is split; the real route dips through B2F (2026-07-22). |
| **Chain walker loops** between floors (a step "reachable" leads backward) | Within-floor reachability is DIRECTIONAL (one-way ledges!). Pick the FURTHEST-ALONG pathable chain step, never the first match (`_walk_warp_chain`). |
| **Checkpoint saved mid-dialogue** loads permanently non-controllable | Never snapshot until the avatar is STABLY controllable (~120 frames) with no active script — B-ride any leftover dialogue out first. |
| A segment gated on **"not at the destination map"** re-runs on a mid-arc resume | Gate travel segments on a WHITELIST of their origin-side maps (a Granite-Cave derail re-entered the Dewford sail and marched to Manual, 2026-07-22). |
| Live NPC lookup returns **"not present" on a big map** | The engine only materializes object events NEAR THE CAMERA — from across a town the object isn't in RAM at all. Walk toward its spawn first (`_talk_to_wandering_npc(..., approach_hint=(x,y))`), then locate it live. |
| A **multichoice with a non-zero default cursor** answered with the stock helper | `wait_for_multiple_choice_question(i)` presses Down i× from WHEREVER the cursor is; `multichoicedefault` menus (Briney's dock menu defaults to Cancel) need explicit cursor moves (Up ×1 → A for Slateport). Read the decomp's multichoice line before answering. |
| **Open arrival msgbox** + a press-nothing wait-for-control = permanent stall | Scripted arrivals (the post-sail Letter reminder) leave a dialogue open; `wait_until_truly_controllable` never presses. B-ride the script (`_ride_out_scripted_scene`) before ANY wait that can follow a scripted arrival — and the derail recovery must always B-ride active scripts too (real-HW dock stall, 2026-07-22). |
| **Stock menu navigator driven raw** wedges when a field script fires (trainer sight-line, leftover evolution scene) | Menus can't open under a script lock and the navigators wait UNBOUNDED (the 110k-frame Joey stall). Wrap in `_yield_bounded`; check no script is active before opening a menu; on interrupt: close (B), ride out, retry (`_rotate_lead_safely`). First slice of #24-interrupt. |
| A **leftover script context after an evolution** silently kills wild encounters | An active script suppresses encounter generation — the training spin starves with zero visible error (batch run05). `_story_spin` B-rides any active script when its no-progress bail fires. If a spin gets no encounters, check `get_global_script_context().is_active` FIRST. |
| A stall's **signature can't localize the wedge** (in-battle, sig constant) | Dump the GENERATOR CALL STACK (`debug_logger._generator_stack`) — the harness now prints it at every NO-PROGRESS milestone. Two wrong hypotheses died in one day to a single stack line each; get the stack before theorizing. |
| A repro state **extracted after idle frames** "proves" a fix the organic run refutes | Savestate load/reload can DEFUSE volatile wedge state (the phantom script). Capture at the MOMENT the wedge forms; treat reload-based passes as weaker evidence than an organic end-to-end pass. |
| Probing whether a place is **reachable/usable** before grepping the DECISION code | The fact is usually already known and in the wrong place. Route 112's "no return path to Lavaridge" was recorded 2026-07-23 in prose, then re-derived by a 30-minute probe cycle on 2026-07-26 — by a session that had quoted half of it that morning. Grep `training_areas.py` (`NO_RETURN_GROUNDS`, `AREA_PREREQ`), `region_reach.KNOWN_GATES`, `_CAVE_EXITS` for the map name FIRST. If a hard-won fact isn't represented where the decision is made, it will be re-derived — move it there + add an assertion in the same change. |
| A recovery gated on **one resource** when several can block the action | The heal fired on low HP; the battle strategy flees on no usable MOVE (a PP condition). A starter that wins without being hit drains PP at full HP → flees every battle → fleeing takes no damage → the HP gate never fires → **3,011 consecutive flees, ~2.9M frames, no level gained**. Enumerate every resource whose exhaustion produces the same symptom (HP, PP, balls, money) and gate on all of them. |
| Taking the **reporter's stated cause** as the thing to fix | It is a hypothesis about a correlated event. A shiny "crashed the run"; the shiny path was the one part working correctly (it fought through and WON, 1.86M frames before the run died). Reproduce the reported cause and CHECK IT WORKS first — one grep redirected the whole investigation. |
| A run that is dead but shows **no error, no hang, and full HP** | Read the OUTCOME TALLY, not the state dumps. `3,011 RanAway vs 5 Won` was the only signal that a busily-"training" bot had gained nothing in 2.9M frames. `grep -o "outcome=BattleOutcome\.[A-Za-z]*" log \| sort \| uniq -c` is the cheapest health check on any long run. |
| Routing an existing class down a **NEW code path** | Read what that path does with it, not just what you return. `RunAwayStrategy.choose_new_lead_after_battle()` returns `False` (annotated `int | None`) — harmless while its only caller was `run_away_from_battle()`, which never rotates; returning it from `on_battle_started` sent it through `fight()`, which rotates whenever the value `is not None` → `Cannot rotate Pokémon #False with itself`, run dead. A strategy repro asserting WHICH strategy is chosen cannot catch what the framework then does with it. Check the whole protocol the new caller invokes. |
| A **numeric threshold justified by one worked example** | It is a guess with arithmetic attached. `CREDIBLE_ANSWER_POWER=60` excluded Rock Smash on a Water/Ground carrier (40) but not on a **Fighting-type** carrier, where STAB makes it exactly 60 — 21 more Norman losses. Enumerate everything that feeds the formula (STAB can multiply the case you are excluding by 1.5) and find a REAL data point on both sides before picking the number. |
| Using a **module-level name inside a long method that imports locally** | Python makes a name function-local for the WHOLE method if ANY branch imports it. `on_battle_started` imports `console` in several branches, so a new branch's `console.print` is an `UnboundLocalError` — and a surrounding `except Exception: pass` reports it as "condition False". Bitten twice (HM-learner 2026-07-23, survival mode 2026-07-26, the second time with the warning commented 16 lines above). Grep the method for `import` before using any module-level name in it. |
| **"That failure is recoverable"** used to justify a risky choice | Recoverability is a property of the LOOP, not the failure. If what re-runs after recovery re-derives the SAME choice from the SAME inputs, the failure is deterministic and "recovery" is just a countdown to Manual — a wrong YES from `region_reach` killed 2/5 live runs exactly this way, re-picking one unreachable Route 111 tile every derail. Anything a deterministic picker chose must be REMEMBERED as failed, or it gets re-chosen. |
| A metric moves to a **PERFECT value** after your change | Treat it as broken until proven. `livetest.py` reported `whiteouts: 0` for 5 runs that whited out 36/5/9/6/10 times — it counted a `debug_logger.event()` string that only reaches the debug-log FILE, not the stdout/run.log the summarizer parses. Ask whether your change could plausibly produce that number; verify against a raw count from the same stream. When adding a counter, grep the STREAM you parse, not the codebase. |
| A capability test asks **"do we have X?"** instead of **"do we have ENOUGH X?"** | It will accept the cheapest token instance. `_boss_plan_is_hopeless` counted any move with effectiveness ≥2.0 as an answer, so **Rock Smash (20 power)** — the HM the bot is FORCED to carry — vetoed the whole diagnosis on Norman, whose only counter-type is Fighting. 27 losing attempts / 508k frames followed. Weight by magnitude (`base_power × effectiveness × STAB ≥ 60`) and keep a test proving a weak-but-REAL answer still qualifies, so the threshold can't creep. |
| A **fail-safe `except` that returns the SUCCESS value** | Invisible when it fires: `except Exception: return False, []` returns exactly what a healthy plan returns, so a crash inside the guard reads as "all fine" while the run bleeds ~19k frames per attempt. Make guards fail LOUDLY — log that the guard is no longer protecting anything. (Caught by a repro stand-in missing a class constant: the `AttributeError` was silently eaten.) |
| Deciding a strategy is "slow" when it is **plateaued** | Trace the OUTCOME per attempt, not just the level counter. Norman: KOs flat at 1–2 of 4 across 27 attempts while levels crept +2 — levels rising made it look like progress; the KO trace showed a hard plateau. Log a per-attempt outcome metric for anything that retries. |
| An **unbounded "the screen is still opening, just wait"** branch | It is a hang with good manners. Written for a 1–2 frame window, it swallows every frame forever the moment an UNRECOGNISED screen is up — the move-learn handler pressed **nothing for 6,000 frames** with the "HM moves can't be forgotten" window on screen (2026-07-25). Bound every wait that presses nothing, and back out when it expires. |
| Diagnosing a wedge from **states alone** | Instrument the BUTTON PRESSES too. "Which buttons, how many, in what ratio" separates *pressing the wrong thing* from *pressing nothing* — opposite fixes. `{'B': 4050, 'A': 1350}` with no `Down` was exactly 3×1800 escape-valve presses, which proved the main handler never acted; the state trace looked busy the whole time. |
| The **game refuses an action** and the bot never hears it | The refusal is usually a NAMED task (`Task_HandleInputCantForgetHMsMoves`). Grep the .sym for the refusal before assuming the prompt is the one you expect: the battle-script pointer can stay parked at the ORIGINAL prompt's offset, so offset-derived state misreports the refusal as that prompt. Dismissing is not enough — strike the refused choice off and re-pick, or you re-offer it forever. |
| Acting on a **UI cursor read while the screen is still animating in** | `sMonSummaryScreen`'s cursor is meaningless until the screen's input task is active — a stale read of 4 while the real cursor sat on slot 1 confirmed an HM the bot had decided to decline. Gate any confirm press on the input task being live. |
| A **BotModeError raised from battle code** kills the run | Battle handling is a SIBLING generator on `context.controller_stack`, not nested in the mode, so `main_loop` catches it first and sets Manual — the mode's `except BotModeError` is structurally unreachable. Record the fault via `modules/battle_fault.py` and let the mode claim it (opt-in `handles_battle_faults`); it then costs one derail. |
| **Blind button-spam** menu recovery lockstep-deadlocks | With the cursor on a dead mon (and neighbors dead too) A-spam cycles the same popup forever; rare corrective presses land in message states and are swallowed. Recovery loops must be STATE-AWARE: read cursor/tasks/HP, press the one button that state needs, with press/release gaps. Bound the OUTCOME, not just the frames — a bounded loop re-entered by its dispatcher is still infinite. |
| A completion check on a **phantom flag/var name** can never pass | `get_event_flag()` returns silent False for names not in the table ("DEFEATED_RIVAL_ROUTE_110" doesn't exist — vanilla only sets `VAR_ROUTE110_STATE=1`). Run `tools/story-dev/audit_flag_names.py` with every chapter build; `_done()` now raises on unknown names; a probe printing False proves nothing until the NAME is proven real. |
| A **one-shot flag/var read polled thousands of times** eventually misfires | Save-block reads resolve a moving pointer and can TEAR around battle/map transitions (observed single-frame flag flickers). Completion predicates in tight loops need majority-of-N reads plus a consecutive-frame streak. |
| Navigating a **runtime-toggled maze** (Mauville barriers) on static collision | The planner can't see live setmetatile state — a "pathable" leg can dead-end into a closed barrier and `follow_waypoints` walks in place forever. Drive every leg `_yield_bounded` and judge by ARRIVAL (`pos == target`), never by the planner's opinion; a stalled leg marks its target blocked until the maze re-shapes. |
| Two states share **every reader signature** but need opposite handling (KI-15 battle-text wedge vs a dialogue's parked WaitForAorBPress tail) | Probe the captured .ss1s side by side (`probe_stuck_state.py`) AND test their response to each input (`probe_press_variants.py`) BEFORE keying a fix on readers. When readers tie, discriminate by a FUNCTIONAL property (the wedge blocks all movement; a tail doesn't) at a seam that can see it (the run-loop's position-frozen persistence nudge), and re-run the class's regression probe (museumprobe2) before committing — it caught three wrong designs in one night. |
| An **autonomous "unstick" press** fired per-frame or on a stale signal | `cb`/`gDisplayedStringBattle` stay stale until the NEXT battle; a live dialogue's script context flickers inactive between boxes. Any auto-press must require the stuck signature to PERSIST (seconds), include a can't-be-mid-flow guard (player position frozen), press ONCE, and cool down long — else it A-mashes an NPC dialogue into a brand-new wedge (`ki15_nurse_wedge.ss1`). |
| `navigate_to` **re-paths forever** when a post-battle transition wedges the avatar | The re-path loop had no no-progress bail — it now raises `NavigationStuckError` after ~8 re-paths that only revisit recently-seen tiles (with a bounded settle-wait between timeouts). Callers get a fast, recoverable derail instead of an 18k watchdog stall. Genuinely-advancing navs (NPC-blocked but reaching new tiles) never trip it. |
| A **battle interrupts a scripted scene** → the field script reads active FOREVER while the game is fully playable (parked post-battle trainer/wild script) | Any B-riding scene loop needs the PHANTOM-SCRIPT ESCAPE: while `gsc.is_active` but `controllable && !waiting_input && !menu` for ~600 straight frames, treat the scene as over and return. Ported from `_wait_until_cutscene_over` into `_ride_out_all_scenes` (Route 120 trainer, ch13_run10). A real scene locks the avatar / prints text / ends; 10s of "playable but script-active" = parked. |
| A **story scene contains a YES/NO** (Steven's "battle the Kecleon?") ridden with raw B | B DECLINES the choice forever (the museum-greeter lesson inverted). Ride scenes that contain a real choice with `_wait_until_cutscene_over("A")` (or the choice-aware `_dialogue_button`), which presses A only when a Yes/No/multichoice is actually on screen. |
| A **BRIDGE / dual-elevation span** reads as walls to `calculate_path` (NO PATH) | The static planner can't cross elevation-transition tiles (Route 119 spans; the Lavaridge-gym idling family). HELD-INPUT walk them with `_hold_walk_route([(dir,(x,y)),...])`, which releases the prior leg's direction each step (two held dirs → the game keeps the first → bump loop) and stops on a coord-trigger firing. |
| A **coord-trigger encounter** (Route 119 rival) aimed at the NPC's object tile | The object may be a PROP (the on-bike rival at x17); the battle fires from a COORD EVENT at a different tile (25,31). Read map.json coord_events for the trigger x,y + gating var; step ONTO that tile, don't talk to the object. |
| **Raising from BATTLE code** to signal a failure | Battle handling is a SIBLING of the mode on a FLAT controller stack, so `main_loop` catches a `BotModeError` first and forces Manual. Record it with `modules/battle_fault.py` `request_mode_recovery()`; the mode claims it via `take_pending_fault()`. (This is already in §7 for KI-19 — restated because it is now the standard way battle wedges end.) |
| A **listener that can sit ABOVE the mode** without a `battle_fault_pending()` check, or without a bound | It will press its button for ever while the MODE — the only thing that can consume a fault and recover — is starved of frames. KI-37: a correct hand-over went unclaimed and the run froze **1,182,000 frames**. `BattleListener` had the guard; `TrainerApproachListener` never mirrored it. **Both now do; the rest are UNAUDITED.** |
| Comparing two integers from **different coordinate systems** | Party-menu indices and `get_party()` indices DIVERGE after switches; `BattleState.map_battle_party_index()` converts. KI-34 compared them raw, judged an ON-FIELD mon selectable, and burned 23.9M frames. **The existence of a mapping helper is the tell that two spaces exist — grep for one before comparing.** And log the UNIT, not just the value: `cursor=1(menu-order)`, `alive_slots=[1,3](party-order)`. |
| A **user's direct observation of the screen** contradicted by your telemetry | Believe the user. They are watching the system; the telemetry is watching your MODEL of it. KI-34's root cause came from thirty seconds of the user looking at the party menu, after my instrumentation had "confirmed" the opposite. |
| A **travel `order` list** missing a corridor/interior map | Unranked map = rank −1 = "run every leg" = a backwards march + NO-PATH Manual (Woods, then Route 120). Rank EVERY map the arc can stand on — routes, city interiors (PC/gym), side spurs — at/after its position. |
| **Reviewing logs against code that was never deployed** | The bot runs from the user's OTHER machine (`…\Pokebot_Gen3_Enhancement_old\sandbox-pokebot`), not this checkout. TWO consecutive bundles (2026-07-26, 2026-07-27) were analysed in depth against fixes that had never been pulled there — the largest single waste in this project. Establish which build produced a log BEFORE analysing it; `04-HANDOFF.md §0a` lists four tells that take seconds. |
| A **comment asserting an object's lifetime** in place of code that enforces it | Per-run counters sat in `__init__` under *"Instance state … so ENDLESS RESET's next run starts with a clean slate."* The endless loop reuses ONE mode object, so `__init__` ran once per BATCH: `_rival_attempts` hit its cap of 3 and **runs 4+ quit at the rival without fighting** (27 of 37 runs across three lanes). Put per-run state in an explicitly named `reset_per_run_state()` that the boundary calls. If you write "so X starts clean", go find the line that makes it clean. |
| A **default outcome that is the SUCCESS value** | `outcome = "finished"` before a `try`, changed only by a raised `BotModeError` — so every unmodelled exit (here `set_manual_mode(); return`) reported success. 16 dead runs read as wins and a batch summary said ~80% success against a true ~20%. Start pessimistic; let only a proven completion set it. |
| Making a **success signal stricter** without enumerating the legitimate successes | The fix for the above nearly relabelled REAL completions as failures: the genuine end-of-content path also calls `set_manual_mode()` and returns normally. Before tightening a success test, list every path that legitimately produces the success. A fix that converts false positives into false negatives is not a fix. |
| A **limit checked only after the work completes** | It is a report, not a limit. `MAX_FRAMES_PER_RUN` was evaluated after `super().run()` returned, so a run that never returns never reached it — P3 hung **27M frames / ~6.5 h** with ZERO STUCK dumps. Evaluate any runaway bound from INSIDE the thing it bounds (`_run_with_frame_budget`). |
| A **progress detector used as the only runaway guard** | It cannot see a LIVELOCK (P1/P2 ground 13–20M frames producing real encounters, battles and heals — busy, just not progressing), and it cannot see a hang if the detector is what hung. Always pair "no progress for N" with a blunt resource budget that shares none of its assumptions. |
| A **dedupe guard tested against a plausible call order** instead of the real one | The `run_index` double-count "fix" deduped on adjacency ("no poll between the two calls") — impossible, because the mode signals BEFORE `super().run()` while the hard reset happens INSIDE it. It shipped with a confident comment and two rejected alternatives listed. Write the interleaving down — who calls, in what order, with what in between — before choosing the predicate. |
| **Tuning an assertion until it matches an observed number you cannot derive** | A repro was about to assert the old strategy yields exactly the observed `37`; it yields 38 under any interleaving that can be justified, and the true ordering is not observable from the logs. That is a fake proof wearing rigorous clothes. Assert the property you can defend (shape: ~2 per run vs exactly 1) and write down what you could not determine. |
| A **matching failure signature** treated as a diagnosis | Losses clustered at ROUTE 110 (34,56) with a weak lead and a strong mon benched — pixel-identical to a bug fixed the day before, and reported as "the fix did not hold". It wasn't: `_lead_best_matchup` reproduces every observed lead from its own defensive-only rule and runs AFTER `train_team`, overriding it. A signature is a hypothesis; read the code that produces it before naming a cause. |
| **Anchoring a repro on exact call syntax** rather than the property | `repro_endless_per_run_state.py` asserted the literal string `yield from super().run()` and broke when the story was correctly routed through a budget wrapper. Scope to the enclosing function body and assert the ORDERING property. Beware bare `.index()` over a whole class — it will happily match text inside a docstring. |
| **Navigating to a tile an NPC is standing on** | `calculate_path` blocks every LOADED object's current AND previous tile, so an occupied tile can never be a destination — the retry budget is spent proving it. If the atlas says an NPC "must be talked to", walk to a free ADJACENT tile, face it, press A, and grade on **the NPC MOVING** (a lost battle also produces "a battle happened"). §Ch19's stair grunt has `sight_radius = 0` and a `lock`/`faceplayer` script: it never starts its own battle, so waiting could not help either (2026-08-12). |
| Blaming the **planner** for a wall the STORY puts there | List every actor the planner sees that your model does not, BEFORE reaching for KI-59. A collision-only flood fill said Mossdeep's Space Center door was reachable and the planner refused — because the gym victory SPAWNS five NPCs onto the only land bridge. The planner was right. ‼ And a reachability probe run against a map the avatar is NOT standing on sees **no** live objects at all, so it silently measures a different world (2026-08-12). |
| **Running the linter you already have** — after the emulator run, or never | `pyflakes` was installed for months and never run. Its first run caught a missing import that had already cost a five-minute drive to discover, **and KI-65** — a branch whose `except` returns a legal-looking "decline", so its re-pick logic may never once have executed. Local-import style makes undefined names invisible to `py_compile` and fatal only on the branch that uses them. Gate: `repro_undefined_names.py`. ‼ When a cheap tool finds one bug on its first run, **read the rest of its output**. |
| A **gate** that reports instead of refusing, or whose scope has gone stale | `audit_flag_names.py` printed "all names valid (checked **2 files**)" while thirteen story modules went unchecked — and, after that was fixed, still could not see names reached through a module constant, i.e. it was blindest at the **completion markers**. A gate must **print what it searched**, print how much it found, and **exit non-zero**. Prefer a glob to a list (a list goes stale as code moves) and resolve one level of `CONST = "LITERAL"` (2026-08-12). |
| A menu driven by **counting presses** rather than reading the game's own record | `ChooseHalfPartyForBattle` cannot be mashed: A on an already-picked mon DESELECTS it, so A-mash toggles one slot for ever with a healthy screen and no error. Drive it by reading the cursor each step and verifying every pick against **`gSelectedOrderFromParty`** (`slot + 1`, 0 = empty). Cursor slots 0-5 are mons, **6 = CONFIRM, 7 = CANCEL** — and the cursor does NOT advance after a pick (2026-08-12). |
| A probe where **every case FAILS**, read as one common cause | It is a common SYMPTOM. KI-39 fitted "the bot has no cross-map route planning" to four failing `calculate_path` calls and put it in the handoff as *the* highest-value item; the four had four unrelated causes (a phantom map connection hiding a warp, a Rock Smash rock, the Go-Goggles desert, a gate structure) and only one was route planning. Make one measurement that could DISCRIMINATE: sample MANY target tiles per map, not one (partial reachability — ROUTE110 17/125, ROUTE111 11/173 — refutes "cannot plan" outright), and ask the tool what it BELIEVES (`map_path` tags all of them `level=459`, i.e. it was trying), not merely whether it succeeded. |
| A **single arbitrarily-chosen probe tile** standing in for a whole map | It cannot separate "this map is unreachable" from "this tile is unreachable". KI-39's ROUTE110 (12,60) is past a cycling-road gate; 17 other tiles on that map path fine. Sweep a grid + every warp tile, and report the reachable EXTENT (a column-by-column run-length map localises the wall to a coordinate — it put the Route 111 choke at exactly the (18,101) that `early_game.py` already documented in prose). |
| Widening what a **planner may return** without re-reading its validators | A check written against a narrower input set encodes that narrowness and then declares the new, correct cases broken. `navigate_to_anywhere` decided "did the warp fire?" by comparing REGIONS — fine while every plannable warp was cross-region by construction, but the moment same-region warps became plannable a perfectly-fired warp would report `"Warp at … did not trigger (locked or event-gated?)"`, i.e. the new feature would look like a locked door. |
| Trusting the **ROM's map headers** as ground truth for what is walkable | They lie. VERDANTURF declares a North map CONNECTION to ROUTE116; **0 of 40 sampled Route 116 tiles are walkable from Verdanturf** and the only link is the Rusturf Tunnel warp. Any planner built on headers alone will confidently produce routes that do not exist. Let the graph SUGGEST and let `calculate_path` RULE — validate every leg against the live world before committing to it. |
| A probe that prints **raw data and a derived summary**, and you read the summary | The summariser encodes an assumption about the answer's shape and is wrong precisely when the answer is interesting. A reachability column printed "first blocked y=130" while the load-bearing fact was the LAST reachable y (102) — the prediction looked refuted and was actually confirmed to the tile. |
| A **CLI flag applied inside ONE frontend branch** | It becomes a bug the day a second frontend can reach the same mode: `--endless-target` was parsed by every frontend and honoured only by the tile lane, so a headless "run forever" lane would have quietly stopped after 10 runs — indistinguishable from a lane that died. Apply startup settings BEFORE the dispatch that picks a frontend; if a flag must be branch-scoped, make the other branches reject it loudly. |
| Parsing a subprocess's stdout without pinning **`COLUMNS`** — *and then trusting the width alone* | `rich` wraps when stdout is a file, physically splitting long lines mid-word. `COLUMNS=400` was set for exactly this and was STILL not enough: a counter-chain derail message is ~1,000 chars, so it wrapped anyway, the `(N frames) ===` tail landed on the next line, and a batch reported **69% finish rate against a true 23.7%** with the dominant end reason missing entirely. Pin `COLUMNS` wide AND make the parser wrap-tolerant (`re.DOTALL` with a **bounded** gap so a truncated record can't swallow the next). Any width can be exceeded. |
| A repro that pins the **WORKAROUND** rather than the property | `repro_x4_headless.py` asserted "a rich-wrapped outcome line is genuinely unparseable (hence COLUMNS=400)" — so when the width mitigation failed, the suite was actively *defending* the bug. Assert what must be TRUE (wrapped records parse), never the limitation you happen to be living with. |
| Aggregating per-item dicts with a **dict comprehension** | `Counter({k: v for lane in lanes for k, v in lane.items()})` silently keeps only the LAST lane's count for any shared key. It reported 9 end reasons for 29 non-finishing runs; every number looked plausible and only the arithmetic failing to add up exposed it. Use `Counter.update()` in a loop, and check totals against an independent count. |
| Validating a travel/navigation fix from **whichever save was already loaded** | It tests the easy case by construction. `#24-journey` and `#24-smashroute` were both proven from Mauville — one map from the obstacle — and both shipped as done; the Norman ladder actually fires at **Petalburg**, where `PETALBURG_WOODS` (a warp-entered map that splits Route 104) makes 0/132 of the Woods, 0/150 of Rustboro and 0/125 of Route 116 unreachable, and neither feature could start. Find the position the feature ACTUALLY runs from by reading the code that invokes it, and test from there. |
| Separating **the data** from **a reading of the data** | Store raw logs per batch and give the summariser a `--resummarise` mode. When a parser bug is found (it will be), re-read the stored logs — re-running hours of emulation to fix a regex also produces a DIFFERENT sample, which destroys the comparison you were making. |
| ‼ **USE THE BADGE FUNNEL, not the finish rate** | Finish rate is ~38 binary outcomes per batch; badge records are ~200 and say WHERE runs are lost. Segment `badge-log.json` by batch window (sort by `earned_at`, split where `run_index` stops increasing) and compute conversion per rung. Measured 2026-07-31: the funnel showed early rungs FLAT (98%/97% both arms) with the whole change concentrated at Balance→Feather (45% → 83%, z=2.67) — which is what made the result credible rather than a lucky sample. A finish rate could never have shown that. |
| ‼ Quoting a **finish rate** from one batch as evidence a fix worked | A 3h / 8-lane batch yields ~38 runs, which can only resolve a change of roughly **+30 percentage points**. Measured 2026-07-31: 23.7% → 30.8% looks like a 7-point win and is **z = 0.70** — pure noise; resolving it would need ~776 runs per arm (~60 h). Trustworthy batch signals are NEAR-BINARY (the counter hunt firing 0 → 9 times is real); rates are not. Use batches to DISCOVER failure modes, not to grade improvements — and grade improvements with a direct capability test in the harness, which is binary and costs minutes. |
| A **latch or cache justified with the word "cannot"** | Re-read what it is actually protecting. `obstacle_search_exhausted` was justified with *"riding out a scene cannot create new rocks, so one empty answer is final for this trip"* — true for scenes, false for JOURNEYS, which cross many maps. It searched once in Petalburg (correctly empty), latched, then walked seven maps and stopped ON the map whose rock sealed the corridor with the feature switched off. Key such state to the thing that actually changes (here, the MAP), not to a boolean. |
| ‼ Using a signal that appears on **both branches** to choose between them | It cannot discriminate — it only says "somewhere in the middle" — and it fails as a RACE, so it looks fine until a slow frame. `Task_HandleChooseMonInput` (the party menu) was read as "instant-learn path", but it is up on the replace path too and merely lingers after the mon is chosen; 4 of 37 teaches then skipped the replace prompt entirely and burned the 9,000-frame cap. **Before using a task/flag/state as a path selector, ask what it looks like on the OTHER path.** Select on positive evidence unique to the branch (here: a genuinely free move slot). |
| Proving a fix that **TIGHTENS** a condition by testing only the branch you kept | A gate one notch too tight fails silently in the opposite direction, and the test you ran cannot see it. Pair every gating fix with a positive control on the branch you gated: the `#24-teachpathrace` fix needed a three-move mon (`instant-learn`, 252f, learned) alongside the four-move one (`replace-prompt`, 479f, learned). |
| ‼ Tuning a constant in a component where **only the success path is instrumented** | If a flow has N exits and 1 emits telemetry, no batch can discriminate between hypotheses, so the only visible knob gets turned — repeatedly. `#24-hmteachloop` cost **four** 3-hour batches (7/8/9/4 failures, all noise) tuning a budget, then fell in ONE ~5-minute run once every exit logged `reason / frame / tasks / learn_state`. **Before changing a constant a second time, make every exit say which it was.** The instrumentation is a function-local helper. |
| ‼ **Reusing a `for` variable name across two loops** in one function | Python leaks the loop variable, so a later loop silently rebinds it and any read afterwards reports the WRONG loop. `TEACH OK … in {_f} frames` measured the menus-closed loop, not the ride — producing "every successful teach exits in 35-86 frames", the figure that justified all four budget rounds. The ride's real cost was **8,999**. Capture it where the loop ends (`_ride_frames = _f`) and report both counts by name. Nothing warns you; the number just becomes a different number. |
| A test/driver that only exercises the **easy branch** | `--driver hmtest` teaches a freshly caught mon — free move slot, no replace dialogue, no post-learn prompt — and was 12/12 clean while every real failure was on a FOUR-move mon. A green test over a branch the bug does not live in reads as coverage. When a feature has a branch the driver never takes, build the driver that forces it (`--driver teachfull`). |
| A **bare `except` around a guard**, so a broken guard reports a clean negative | `get_item_bag().tm_hm_case` (the pocket is `tms_hms`) raised `AttributeError`, the `except` swallowed it, and the probe announced "HM06 is not in the bag" on a save that had it. Same shape as `box_views` returning `[]` on a `TypeError`. **A guard that cannot distinguish "no" from "I broke" is worse than no guard** — use the intended API and let the error be loud. |
| ‼ A liveness check whose success condition **the driven action cannot produce** | Not a flaky test — a *timer wearing a test's clothes*, and it always reports the alarming answer. The withdraw probe's "did the bot keep playing?" check spun until `local_coordinates` changed; `spin` **turns on the spot** (facing, not position) and we had just exited into a TOWN, so there was no encounter either. 20,000 frames of `HANG CONFIRMED` over a completely healthy bot. **Before trusting any "still working?" check, name the action that would make it PASS** — if nothing you are driving can produce that state, rewrite it. Prefer a check that is a real assertion too: the fix here was a SECOND `heal_in_pokemon_center` (navigates a building + scripted dialogue — unfakeable) which also proved the withdraw correctly no-ops the second time. |
| Testing a piggybacked feature by **calling the piggybacked function directly** | It proves the function works and says nothing about the hook, which is usually the half that is dead. `withdraw_from_box` had been correct for two days while `withdrawing` logged **0** in every batch, because the caller never reached it. Drive the HOST operation (`heal_in_pokemon_center`) and set up the state it reads (`_hunted_counter_pids`) — the harness makes your driver the `bot_mode_instance`, so a probe can supply exactly what production supplies. |
| Grading a probe with **no positive control on the read path** | `box_views()` failed with `TypeError` for two days and `find_in_box` swallowed it, so "the mon isn't there" and "we cannot see the box" printed identically. Assert the read works and the key re-resolves BEFORE spending a journey on it, or a null result at the end is unattributable. |
| Reading back **live game state in the same frame you wrote it** | Party/state reads are cached per frame. The heal-fixture logged `Mightyena 0/124` immediately after healing it — on a run that then won four battles — because the probe had not yielded. Log the BEFORE→AFTER you wrote, never a same-frame read-back. |
| Having just **warped into a map**, choosing the "nearest reachable" exit | You are STANDING ON the door back out, so any walkability check on it succeeds in zero steps and it wins every ranking. Result: `A -> B -> A -> B` for ever, which `used_warps` cannot stop when the map has several doors (Rusturf Tunnel has three, so the return trip is a different EDGE each time). Track visited MAPS and prefer a door leading somewhere new; allow a revisit only when nothing else validates. |
| ‼‼ A chapter's acceptance test that does not include **"and the bot can CONTINUE"** | A completion FLAG proves the CONTENT ran, not that the run survived it. Ch15 is graded binary on `GROUDON_AWAKENED_MAGMA_HIDEOUT`, which is set the moment Maxie falls **four floors deep** — so it passed its own test on a run that ends **permanently stranded** (KI-56: Strength boulders reset on map reload and re-seal 1F behind you; 248 tiles, no reachable exit warp). **Every chapter's test must assert the bot can still leave and act**, not just that the flag flipped. |
| ‼‼ Treating **"the item was consumed"** (or "the flag flipped") as **"the script finished"** | Same shape as `EventScript_ActivateStrength`, now confirmed for ITEMS, and it cost a driven run. The Escape Rope exit consumed the rope and then sat on the same tile for 1800 frames, `controllable=False`. `ItemUseOnFieldCB_EscapeRope` (`src/item_use.c:903`) calls `DisplayItemMessageOnField(..., Task_UseDigEscapeRopeOnField)`, and the warp only runs from that **callback** — which fires when the message is DISMISSED. A wait loop that merely `yield`s waits for ever on a text box. **If a wait loop can be satisfied only by a script advancing, it must PRESS something** — B, so it dismisses without interacting. The no-progress dump named it outright (`Task_ContinueTaskAfterMessagePrints`), which is why the dump is worth reading before theorising. |
| ‼‼ A run reports **PASS and a recovered failure** in the same breath | Treat the PASS as unproven until you know the failure was not what CAUSED it. §Ch16 passed three times with `whiteouts=1` — and a whiteout **fully heals the party**, which is exactly what a run that started at 8.8% HP needed. The chapter was green *because* it failed, and the post-chapter anchor read 100% HP for the same reason. Same shape for any recovery path: retries, fallbacks, `except`-and-continue. **Grade on `whiteouts==0` / `retries==0`, not just the goal flag.** |
| A heal / resupply stop the party **cannot reach alive** | Not a fix — a wish. Ch16's first heal was Mauville, and the run came out **frame-identical to the unhealed one up to `f14345`**, the exact frame of the original whiteout, because the route to Mauville is a strict PREFIX of the route to Slateport. The heals ran, after the whiteout had already healed for free. **Order stops nearest-first**, and treat *an unchanged failure frame* as proof the change came too late to matter — a `.ss1` diverges the instant behaviour does. |
| Inheriting **"X is unreachable"** from another chapter without checking WHERE it was measured | §Ch15 recorded Lavaridge as unreachable — *"not walkable from ROUTE112"*, three live failures — so Ch16 initially skipped it. But Ch15 measured from `ROUTE112 (28,28)`, the **cable-car station on Route 112 NORTH**, while Ch16 comes down Jagged Pass to the *south* end, which is the side Lavaridge connects to. **Same map name, different component.** Re-testing it is what turned `whiteouts=1` into `whiteouts=0`. A negative reachability result is bound to the tile it was taken from, not to the map. |
| Choosing a build anchor without reading its **party HP** | `probe_anchor_inventory.py` now prints HP and fainted count, and flagged **three** anchors on its first run: `post_maxie` 9% / 5 fainted, `post_mtpyre` 11% / 3 fainted, `post_winona` 29% / 3 fainted. Anchors get captured right after boss fights, so a wiped party is the NORM here, not an accident — every chapter built on one inherits a latent whiteout on its first haul. **Read the HP line before building on an anchor, and heal early in any chapter that starts from one.** |
| In a **warp-panel maze**, treating a planner path as a walkable route | `calculate_path` treats a panel as ordinary ground, so it will plot a walk straight ACROSS one and the bot teleports mid-leg. Measured: the Aqua Hideout leg `(42,13) -> (48,13)` crosses `(45,13)`, itself a panel — the bot landed at `(45,9)` and the next hop failed. **A walk edge is only real if the path's intermediate waypoints avoid warp tiles**; check their COORDINATES against the ROM warp table. ‼ Do NOT filter on `Waypoint.is_warp`: `map_path.unroll_path` guards that branch with `len(result) == 0`, so it is set **only on the final waypoint** and intermediate panels read as ordinary ground. (The hop's own tile-level assertion is what catches this at runtime — see the row above on grading hops.) |
| ‼‼ Static recon of an **object-dense map**, from an anchor standing elsewhere | It is **PESSIMISTIC**, not optimistic — the opposite of the caveat we had been writing everywhere. `map_path.is_tile_accessible` blocks any tile whose object template is not in `active_objects`, and `active_objects` comes from the **currently loaded** map. So reconning the 36-object Mossdeep Gym from a save inside the Aqua Hideout turned every object-template tile into a wall and made a real route look impossible (KI-58). **Both failure directions are now known:** static can call a `setmetatile`-walled tile WALKABLE (§Ch15's Jagged Pass door) *and* an open tile BLOCKED. Recon a busy map from a save standing ON it. |
| Inferring a mechanism from a **metatile / flag NAME** | A distinctive name feels like an explanation and stops the search. `MB_MOSSDEEP_GYM_WARP` read like "a special gym teleport with its own destination logic", and KI-58 was written on that guess; the decomp shows `DoMossdeepGymWarp()` is an ordinary warp with a different fade plus `SKIP_OBJECT_EVENT_LOAD`, destination still from the warp event. **Read the function the behaviour dispatches to** before writing a cause down. |
| Stuck deciding which of two readings of a map is right | **Build the second model and let them disagree.** A collision flood fill (`probe_gym_components.py`) cross-checked against `calculate_path` located KI-58's real cause in one run: they differed on exactly the two failing links, and the difference pointed straight at the statue templates. Re-reading one model would not have found it — a disagreement between two is a far sharper instrument than confidence in either. |
| Asserting a **warp table's coordinates as the LANDING tile** | A warp entry gives the destination WARP's tile, not where the player ends up. For **door-type** warps Gen 3 places you on the tile in FRONT of it; ladders and stairs land exactly on it. §Ch17's first run reported *"Could not enter the warp at (22,1)"* while standing happily on the far side, because the expected tile was `B1F (29,1)` and the bot was at `(29,2)` — so a warp that worked was retried until the tries ran out. **Allow one tile of slack when asserting an arrival, and check the slack cannot merge two nearby warps** (here B1F's panels are ≥3 tiles apart, so it cannot). |
| ‼‼ **N of your own instruments agree on something impossible** | Stop adding instruments of the same KIND — they probably share a missing primitive. Four models (warp-graph BFS, collision flood, `calculate_path` spot-checks, a statue-aware re-run) all said the Mossdeep Gym had no route to its own gym leaders. Every one modelled the gym as *walk + warp*; the gym has a **third movement primitive** — step on a floor switch to relocate 21 statues (`moverotatingtileobjects`, `src/rotating_tile_puzzle.c:108`). **Ask what the game can DO that none of your models represents, and get an explicitly ADVERSARIAL second opinion** ("refute this claim"). This is the project's own Gemini rule — *agreement is not a confidence signal* — turned on your own tools. |
| A **model-free** empirical probe that still gets it wrong | "I only pressed buttons, so I cannot be wrong about the map" protects you from bad map models, **not from a state key that is too small.** The gym brute-forcer stepped on floor switches while exploring, so the map mutated underneath it; with a key of only `(map, position)` two different worlds collapsed into one node and the search truncated at 35 tiles. **When the world changes in response to what you do, the world is part of the search state** — here, the live object positions from `get_map_objects()`. |
| A puzzle whose progress survives some transitions but not others | Check which, explicitly, before designing around it. Mossdeep Gym's own warp function exists FOR this: `DoMossdeepGymWarp` calls `SaveObjectEvents()` + `SetObjectEventLoadFlag(SKIP_OBJECT_EVENT_LOAD)` so **internal warps preserve statue positions**, while the flag is cleared on gym exit so **leaving resets the whole puzzle**. A bot that re-enters to "retry" starts from scratch and must know it. |
| ‼‼ An NPC blocks a required path, and you go looking for a **route around it** | A story NPC standing in a doorway is usually the intended TRIGGER, not terrain. §Ch16 lost a run and produced a whole known-issue arguing the Slateport Harbor door was *sealed* — the door is set in a solid wall whose only neighbour is Capt. Stern's tile, and Ch15's own Maxie script is what parks him there. But `SlateportCity_EventScript_CaptStern` ends `removeobject` / `setvar VAR_SLATEPORT_CITY_STATE, 2` / **`warp MAP_SLATEPORT_CITY_HARBOR, 11, 14`** — *talking to him carries the player in*, to the same tile the door warp uses. **`grep` the map's own `scripts.inc` for the blocker's `LOCALID_` BEFORE designing any route.** One grep produced the entire answer. Corollary: when a measurement implies the game soft-locks its own next beat in an era the game itself creates, the measurement is the suspect. |
| Trusting a `calculate_path` result about the **SOURCE** tile | It validates the destination side, not the source: asked for a route *out of solid rock* it returns `OK, 1 wp`. Three "walkable tiles adjacent to the door" in KI-57's first write-up were walls, and that artifact is what made the geometry look like disconnected components instead of one occupied tile. **A path result is evidence about the DESTINATION only — read `collision` yourself before using a tile as a source**, and when the geometry matters, DRAW the map (`probe_slateport_harbor_map.py`) instead of sampling it. |
| A driver crashes and the log looks like a **hung bot** | `map_name` is a LOCAL helper redefined inside every driver in `story_harness.py`, not a module-level one. A new driver that omitted it died at frame 30 with `NameError`; the harness dropped to **Manual mode** and the log then filled with 900k frames of heartbeats and `NO-PROGRESS` dumps — which reads exactly like a bot that will not move. **`grep EXCEPTION` in `harness_sandbox.log` before diagnosing any stall**, and note that the flushed harness log holds the traceback even when redirected stdout is still buffered and shows nothing. |
| ‼‼ Keying a detector on a **Gen 3 `Task_XxxYesNo` display task** | It exists for **ONE FRAME**. The decomp pattern is `Task_XxxYesNo: if (!IsPartyMenuTextPrinterActive()) { PartyMenuDisplayYesNoMenu(); func = Task_HandleXxxYesNoInput; }` — the task **retires itself on the frame the menu becomes answerable**, which is the same frame your "is the prompt up?" condition first becomes true. Measured: `f3232735 ['Task_ReplaceMoveYesNo']` → `f3232736 ['Task_HandleReplaceMoveYesNoInput']`, gone for ever. **Always match the DISPLAY task and the INPUT HANDLER together** (`_PROMPT_TASKS`, `_STOP_TASKS`), and add an "already advanced past it" exit. `#24-teachmsgstall` cost four rounds and three refuted causes on exactly this. |
| ‼‼ **Blind-mashing A at a live yes/no** to "keep things moving" | Somewhere in Gen 3 there is a prompt where **A means give up**, and a 900-frame mash will find it: `Task_HandleStopLearningMoveYesNoInput` case 0 = "stop learning" → "<mon> did not learn <MOVE>". Our own buttons walked the teach into abandoning itself, then re-armed it from the bag — a ping-pong that looked like a freeze. **Mash only to advance TEXT; every yes/no gets a named branch, placed BEFORE the fallback in the ladder** (an `elif` after `_f % 3 == 0` parses fine and never fires). |
| A bug that is **deterministic from a save AND intermittent in production** | That combination is the signature of a **frame-timing race**, not two bugs. A `.ss1` replays identical timing, so a save that loses the race loses it on every replay (0/3); live runs land on a random phase (38/42 ≈ 90%). Stop trying to reconcile the two readings and go looking for a window measured in frames. |
| ‼‼ Reading **repeated failures as a RATE** without checking the runs DIFFER | Identical telemetry means **n=1 no matter how many times you ran it**. The Magma Hideout looked like "wins 1 in 3"; all three losing runs were byte-identical (41 `[TURN]` lines, md5 `07f99a10ac8b` — same HP, same PP, same heal on the same turn), because a `.ss1` replays identical frame timing. **md5 the telemetry across runs before writing a fraction**, and never launch a retry loop against a deterministic failure — 8 attempts here would have been ~80 minutes for eight identical losses. |
| A result changes and the **save FILENAME did not** | Check the bytes/mtime before theorising about the code. Twice in one day the same filename held different content (`magma_door.ss1` overwritten by a `magmatravel` success; the teach repro's fixture likewise). **Same name ≠ same fixture.** |
| Putting a field in a **failure message** without predicting what it will READ there | KI-51's guard prints `party_alive` to corroborate "whiteout" — and it printed **6/6**, because a whiteout HEALS the party. The field reads healthy precisely BECAUSE the failure happened. Ask "what will this hold at the moment the message prints?", not "what would make the failure obvious?" A field that always reads healthy at the point of failure is decoration, and misleading if it looks like evidence. |
| Spending another EXPERIMENT where a missing **telemetry FIELD** would decide it | `#24-bosstelemetry` lead 2 ("selected but not executed") sat open from 2026-08-09 because the turn line printed species/level/HP and **no status**. Frozen PP had two explanations — a broken action pipeline, or ordinary confusion/sleep/flinch, none of which consume PP. **One line added to `_describe(mon)` settled it in a single run** (`[Confused]` — Crobat's Confuse Ray, the mon killing itself 122→4). Before designing an arm to discriminate two causes, check whether the log could simply SAY which. |
| A repro whose evidence rests on **a save some driver re-captures** | `saves/magma_door.ss1` is rewritten by `--driver magmatravel` on every success; a later chapter run silently replaced the exact save two failures had been measured on, and the committed "cheap repro" stopped reproducing. **A save any driver writes is a cache, not a fixture** — copy it to a name nothing writes to, and record its mtime beside the measurement. |
| ‼ A **fault injection that re-fires on every retry**, when the fix's mechanism IS retry | The fault becomes unsatisfiable by construction, so the arm that recovers correctly loops for ever and looks *worse* than the broken one. My first `TEACH_CANCEL_FORGET` did this and reported "both arms fail, the fix is worse". **Latch a timing-miss injection to ONE shot**, then OLD fails and NEW succeeds. |
| A structural repro that pins a call's **spelling** rather than its meaning | Routing every button through a recording `_press()` wrapper turned three green checks red without changing one behaviour. If a check exists to defend an invariant ("this branch cannot fire once the move is known"), match the branch by either spelling and then assert the invariant. |

---

## 8. Documentation discipline (do this every item — it is not optional)

Per the managed block in root `CLAUDE.md` (Definition of Done): verified change → update
current-state docs (`01/02/05`, `03` punch-list) → append `07-CHANGELOG.md` (+ `06` if a
real decision, + `08` if a bug was fixed/approach abandoned) → update `04-HANDOFF.md` →
commit (`<type>: <summary> (punch-list #N)`) → push. **Do these PER item, not batched.**

Write for an agent with ZERO prior context:
- **Intent + why**, not just what. Future-you needs the reasoning to change it safely.
- In `08-MISTAKES.md`, always include a one-line **prevention rule** (they become §7 above).
- When you learn a new technique or tool trick, **add it to THIS playbook**.
- Convert relative dates to absolute. Link related docs.
- **Retire stale rules:** when a test/refactor makes a past mistake impossible, drop the
  "don't do X" rule and note it — a stale rule wastes every future agent's attention.

The goal: the next agent reads `04` + this playbook and can immediately build, debug, and
document at full speed — better than we did.

## §N. ‼ `gh api ... | base64 -d` SILENTLY CORRUPTS BINARY DECOMP FILES (2026-08-13)

Fetching decomp **binaries** (`data/layouts/*/map.bin`, `metatile_attributes.bin`) with
`gh api repos/pret/pokeemerald/contents/<path> --jq .content | base64 -d` **re-encodes the bytes as
UTF-8**. Measured: an 800-byte `map.bin` came back as **1176 bytes**. Every tile you then decode is
garbage, and it fails *silently* — you get plausible-looking numbers, not an error.

**Do instead:** fetch binaries from `raw.githubusercontent.com` with `curl`, and **assert the size**
against `width * height * 2` before parsing a single tile. `gh api` remains fine for TEXT
(`.inc`, `.c`, `.h`, `.json`).

⇒ **Any earlier agent conclusion drawn from `gh api`-decoded `map.bin` is suspect** and should be
re-derived. This is also a general instance of the project's standing rule: an instrument that fails
silently is worse than one that crashes, so give it a control — here, the size check.
