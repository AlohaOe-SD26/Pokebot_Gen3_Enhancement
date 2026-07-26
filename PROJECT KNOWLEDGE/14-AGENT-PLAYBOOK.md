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
| Talking to a **PATROLLING NPC** via its spawn tile, a navigate-chase, or blocking its route | `_talk_to_wandering_npc`: OBSERVE a lap (record both walkers' routes) → park BESIDE the route (on NOBODY's route, not a warp) → face-tap+A when he transits the adjacent tile. A tail-chase never catches a same-speed walker on a ring; blocking a shared ring queues the WRONG walker against you (Briney/Peeko, 2026-07-22). |
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
| A **travel `order` list** missing a corridor/interior map | Unranked map = rank −1 = "run every leg" = a backwards march + NO-PATH Manual (Woods, then Route 120). Rank EVERY map the arc can stand on — routes, city interiors (PC/gym), side spurs — at/after its position. |

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
