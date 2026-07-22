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
6. **Navigation gotcha:** the global navigator can't always one-shot cross-map paths
   (Rustboro→Route104, Route116 ledges). Go **leg-by-leg**: navigate to a staging tile,
   then step across the map connection manually, then navigate on the next map.

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
