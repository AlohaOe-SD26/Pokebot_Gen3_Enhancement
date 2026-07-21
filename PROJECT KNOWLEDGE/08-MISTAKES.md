# Mistakes & Dead-Ends — Pokebot_Gen3_Enhancement
> APPEND-ONLY. The point of this file: never solve the same problem twice and
> never re-walk a known dead-end. Future sessions read this BEFORE starting so
> past errors aren't repeated. New entries go at the END, with a date.
>
> Log a entry whenever: a bug took real effort to fix, an approach was tried
> and abandoned, an assumption turned out wrong, or a fix corrected a mistake.
> Entry format:
>
> ## YYYY-MM-DD — short title  (ML-N)
> - **Symptom:** what went wrong / what was observed
> - **Context:** file(s), feature, or area
> - **Root cause:** what was actually wrong (not just the symptom)
> - **Fix:** what resolved it (the approach that worked)
> - **Prevention:** one-line rule so it doesn't recur
> - **Retire when:** (optional) the structural change that makes the
>   prevention rule unnecessary (e.g. "a test now covers this") — once true,
>   the rule can be dropped from CLAUDE.md to save context.

---

## 2026-07-17 — Agent-written docs contained ~4% wrong claims  (ML-1)
- **Symptom:** The initial deep-documentation pass (written by 5 parallel
  agents) read convincingly but contained 39 factual errors across ~975
  verifiable claims (~4%): off-by-N line refs, an inverted behavior claim
  (LoseOnPurpose/Explosion), invented capabilities (navigate_to crossing
  warps; a repo-root sprites/ dir; OBS "hotkey" mechanism), wrong return
  types, and a wrong error-handling claim (work-queue errors exit the
  process, not drop to Manual).
- **Context:** `40cakes repo/DOCUMENTATION/00–05`, `Pokemon_Emerald_AI_Notes.md`.
- **Root cause:** First-pass documentation states plausible inferences with
  the same confidence as verified facts; some errors even originated from
  stale comments/docstrings in the upstream source itself (e.g. the
  obs.py header, the `disable_default_battle_handler` docstring).
- **Fix:** A second adversarial verification pass (6 agents, one per doc,
  instructed to open every cited file:line and re-derive every behavioral
  claim from code) fixed all 39 and flagged what remained unverifiable.
- **Prevention:** Never build on agent-written technical docs until they
  have survived an adversarial verify pass; and treat upstream
  comments/docstrings as claims to verify, not facts.

## 2026-07-17 — gitignore silently dropped the custom-modes framework from commits  (ML-2)
- **Symptom:** A fresh clone (installer test) was missing all of punch-list
  #3's plugin files; the "committed and pushed" framework existed only on
  this machine.
- **Context:** `custom-pokebot/plugins/` — upstream's `.gitignore` ignores
  `plugins/` wholesale (it treats plugins as user-private), so `git add -A`
  skipped the new files without any warning, and the drift/heal check
  (which only sees tracked files) was blind to them too.
- **Root cause:** Assumed `git add -A` + clean `git status` meant "all new
  files are in the commit"; ignored files never show in either.
- **Fix:** `.gitignore` negation block (`plugins/*` + `!` rules, logged in
  DIVERGENCE-LOG) + explicit `git add`; verified with `git ls-files`.
- **Prevention:** After adding files inside a vendored/upstream tree,
  verify they are actually tracked (`git ls-files <path>`) — a clean
  status is not proof. The installer's fresh-clone test now also catches
  this class of bug (critical-files smoke check includes the plugin files).

## 2026-07-18 — Agent-built features carried 16 bugs past their own tests  (ML-3)
- **Symptom:** The sandbox round (built by 3 fork agents, each with green
  self-written test batteries and live GUI runs) still contained 16 real
  defects on adversarial review — including 2 critical (backup backend
  committing unrelated staged files; macro "once" mode looping forever).
- **Context:** sandbox-pokebot round #7 (backup, macros, patrol, GUI).
- **Root cause:** Self-written tests validate the author's mental model;
  the criticals lived in INTEGRATION CONTRACTS the authors never tested:
  the main loop re-instantiating finished modes, and git's index being
  shared global state. One original test was a tautology that always
  passed.
- **Fix:** Independent adversarial verifiers per slice, instructed to
  re-derive contracts from upstream code and attack edge cases; 16 fixes,
  batteries extended (backup 12→31 checks; macros rewritten to drive the
  REAL mode under a simulated main loop).
- **Prevention:** Feature code from agents ships only after an independent
  adversarial pass that specifically tests INTEGRATION contracts (main
  loop, git index, Tk lifecycle) — green self-tests are not evidence;
  and never `git commit` without a pathspec in automation.

## 2026-07-19 — Stock auto-updater silently active in the fork  (ML-4)
- **Symptom:** Launching custom-pokebot could offer to download a 40Cakes
  upstream *release* zip and extract it over our fork, clobbering all
  divergences. Went unnoticed until upstream tagged a new release, making
  the prompt appear on launch.
- **Context:** `pokebot.py` run_updater() guard.
- **Root cause:** Upstream disables the updater when `.git` is INSIDE the
  bot folder; our git repo's `.git` is at the REPO ROOT (parent), so the
  guard never matched and the updater stayed on. A structural consequence
  of the two-folder fork layout that nobody checked at vendoring time.
- **Fix:** Guard now walks ancestor dirs for `.git` (custom + sandbox).
- **Prevention:** When vendoring an app that self-updates, audit its
  update/self-modify triggers against the actual repo layout — a nested
  `.git` assumption breaks in a monorepo/subtree layout.

## 2026-07-20 — Story detection: naive single-signal scans mis-place saves  (ML-5)
- **Symptom:** The read-only story progress detector, tested on the real
  `Nick - Emerald` save, gave two different WRONG chapters depending on
  strategy: "first-incomplete flag scan" said ch2 (an early flag was unset
  despite the Stone Badge proving it's past ch2); "furthest-proof" said
  ch16c/chapter 21 (a stray Magma Emblem key item in a hand-edited save
  dominated placement).
- **Context:** `modules/story/chapters.py`, `modules/story/progress.py`.
  The save turned out to be a hand-built TEST save (shiny Lv100 Celebi/Sceptile
  beside Lv6 mons; badge + key item set out of natural order).
- **Root cause:** Individual event flags / key items are NOT reliable
  monotonic proofs of story position on real saves. Only the 8 gym badges are
  earned strictly in order and unskippable.
- **Fix:** Badge-anchored detection — highest set badge → its chapter bracket →
  first unmet finer milestone WITHIN the bracket. Finer flags/items only refine
  within the bracket and can't move placement outside it; anything met ahead of
  the badge count is reported as an anomaly, not used for placement. Also
  replaced the unreliable `HIDE_MT_PYRE_SUMMIT_MAXIE` proxy with the Magma
  Emblem key-item check. 12/12 unit tests; correct result (ch5) on the save.
- **Prevention:** For "where am I in the story", anchor on badge level first;
  treat any single non-badge flag/item as a refinement or an anomaly, never as
  the primary position signal.
- **Retire when:** covered by `tests/test_story_progress.py`
  (`test_current_chapter_never_leaves_its_badge_bracket`,
  `test_hacked_save_stone_plus_stray_magma_emblem`).

## 2026-07-20 — Tkinter Canvas .lift()/.tkraise() both mean tag_raise  (ML-6)
- **Symptom:** Clicking "Hide" in the dashboard threw `_tkinter.TclError:
  wrong # args: should be ".!canvas2 raise tagOrId ?aboveThis?"` from
  `self._pokeball_button.lift()` (dashboard_gui.py ~line 1735). Non-fatal
  (Tk swallows it) but noisy in the console.
- **Context:** `_pokeball_button` is a **Canvas** (image button). GUI restack.
- **Root cause:** Tkinter's `Canvas` aliases **BOTH** `lift` AND `tkraise`
  to `tag_raise` (raise a canvas ITEM, which needs a tagOrId) — so calling
  either with no args on a Canvas errors. (On normal widgets `.lift()` is the
  widget-stacking raise.)
- **Fix:** Call the base method directly: `tkinter.Misc.tkraise(canvas_widget)`
  — raises the whole widget's stacking, no tag needed. Fixed in sandbox+custom.
- **Prevention:** To restack a **Canvas** widget, never `.lift()`/`.tkraise()`
  — use `tkinter.Misc.tkraise(widget)` (or `.lower` → `Misc.lower`).

## 2026-07-20 — Global navigator can't cross a warp-split map  (ML-7)
- **Symptom:** `navigate_to_anywhere(RUSTBORO/ROUTE104, …)` from Petalburg always
  failed — `Could not find a path from (…@PETALBURG_CITY) to (…@ROUTE104)`, or it
  picked an unreachable Route104 waypoint, or "too many scripted interruptions"
  after 25 retries. Hours of coord-guessing (41,20)/(16,38)/(10,65) all failed.
- **Root cause:** Route 104 is ONE map ID but is physically split into a south
  (Petalburg) half and a north (Rustboro) half, joined only by walking THROUGH
  Petalburg Woods via WARPS. The global navigator routes over the map-CONNECTION
  graph (which shows Petalburg→Route104→Rustboro as edge-connected) then fails the
  LOCAL path across Route104 because a warp barrier is invisible to connection
  routing. NO target coordinate can fix this — it's structural.
- **Fix (plan):** build the trip in LEGS with explicit warp traversal (Petalburg →
  Route104-south → Woods-south-warp → cross Woods → Woods-north-warp → Route104-north
  → Rustboro). See design §16.
- **Prevention:** Before trusting `navigate_to_anywhere` across regions, check the
  ROM connection graph AND whether any intermediate map is warp-split (a route that
  routes THROUGH a cave/woods/building). If so, drive it leg-by-leg through the
  warps — don't guess target coords. Read connections with get_map_data(M).connections
  (each has .direction/.offset/.destination_map); warps via .warps (`MapWarp` =
  `.local_coordinates` + `.destination_warp_id`).

## 2026-07-20 — Single-mon party can't flee a trainer → travel battle crash  (ML-8)
- **Symptom:** Story travel across Route 104 crashed with
  `RuntimeError: Tried to run away from a trainer battle` — the lead (Mudkip
  Lv11) dropped below the 20% HP flee threshold mid-fight and the strategy
  tried to escape.
- **Root cause:** At this point the party is a SINGLE Pokémon.
  `LevelUpLeadBattleStrategy` flees (or rotates) when the lead's HP is too low —
  but you cannot flee a TRAINER battle, and with one mon there is nothing to
  rotate to, so it calls `TurnAction.run_away()` which raises. The lead was also
  entering at 28% HP (unhealed).
- **Fix:** (1) `LevelUpTravelBattleStrategy` (subclass) — in a TRAINER battle it
  never escapes; it fights on with the strongest move (`is_trainer_battle`
  guard). Used for ALL story battles now (wild battles keep the flee-at-low-HP
  behaviour, which is fine — wilds CAN be fled and the training loop heals).
  (2) Travel HEALS at a Poké Center before the trainer zone so full HP carries
  the fight. Both in `travel_to_petalburg_woods()` / story_mode on_battle_started.
- **Prevention:** Any route travel with a single-/small-mon party must pre-heal
  AND use a no-flee strategy for trainers — a trainer battle can never be fled.

## 2026-07-20 — Hidden coord scripts + door-warp quirks block travel (companion to ML-7)
- **Scott gate:** Petalburg's ONLY west exit to Route 104 is row y=12/13; walking
  there fires a ONE-TIME cutscene `PetalburgCity_EventScript_Scott` at (4,12)
  that runs WHILE game_state stays OVERWORLD (so a "press B only when not
  overworld" ride-out never advances it). Advance dialogue whenever
  `get_global_script_context().is_active`, not just on a state change.
- **Door warps:** navigate_to_anywhere walks OVER a 'Non-Animated Door' warp
  tile WITHOUT triggering it (warp fires only on a genuine player step onto the
  door from below). And a held direction won't cleanly enter it. Fix: navigate
  to a tile BELOW the door, then step UP with DISCRETE steps (press, let the
  ~16-frame step complete); if navigate stopped ON the door, drop south first.
- **Finding hidden blockers:** dump the map collision grid (get_map_data per
  tile → `.collision`/`.tile_type`) to find the real opening, and read
  `get_global_script_context().stack` at the stall tile to name the script.

## 2026-07-20 — Petalburg Woods stall: fragile door-stepping + a TEST HARNESS that hid it (ML-9)
- **Symptom:** In the REAL bot (install_sandbox), Story mode got "stuck" inside
  Petalburg Woods and stopped progressing — but every one of my test runs passed.
- **Two root causes:**
  1. **Fragile door entry.** My Woods door/warp entry stopped SHORT of the door
     and hand-stepped onto it with single-frame button presses + a per-frame
     `_map_group_number()` check. Single-frame presses don't reliably complete a
     tile step, and the map read FLICKERS during the warp fade, so the warp often
     didn't fire → `BotModeError` → and main.py catches BotModeError and
     **switches to Manual mode** (main.py:121) = the player just stops = "stuck".
  2. **The harness masked it.** My verification harness read `get_player_avatar()`
     + `get_map_data_for_current_position()` EVERY frame (for logging/stall
     detection). main.py does NOT — it only reads game_state/script/tasks per
     frame. Those extra reads subtly shifted battle/warp timing so the flaky door
     happened to fire. So the bug reproduced ONLY without the extra reads.
- **Fix:** warp through a door by making the door tile a NAVIGATION TARGET —
  `navigate_to(map, door_tile)` — exactly how `heal_in_pokemon_center` enters the
  Poké Center. navigate_to completes the step and fires the warp reliably. New
  helper `_pass_through_door(door_tile, from_map)` (steps one tile off the door
  first if a prior navigate parked us on it). Verified with a MAIN.PY-FAITHFUL
  harness (below). Applies to both Woods doors; the south door is in custom too.
- **Prevention (supersedes the earlier §16 note):** test story steps with a
  harness that MATCHES main.py — per frame read ONLY game_state / script_context
  / tasks (to build FrameInfo), NOT player/avatar/map; and catch `BotModeError`
  the way main.py does (→ set_manual_mode) so a raise shows up as "stuck", not a
  crash. Reading extra state each frame HIDES timing-sensitive bugs. Never
  hand-step onto a warp tile — navigate_to it.

## 2026-07-20 — Move-learn "stuck (but bot not stopped)" at Treecko Lv16  (ML-10)
- **Symptom (user):** at Treecko Lv16 (learns Pursuit) the bot HANGS but does NOT
  drop to Manual — an infinite loop, not a BotModeError. Likely all starters at
  their evolution level.
- **Diagnosis (code trace; NOT yet reproduced in-harness):** Lv16 is BOTH
  Treecko's evolution level AND a move-learn (Pursuit). With the stock
  `stop_evolution` default the evolution is force-CANCELLED. Suspected loop:
  `battle_handler.handle_battle` checks `BattleScript_AskToLearnMove` BEFORE
  `Task_EvolutionScene`, and `handle_move_replacement_dialogue` BREAKS OUT if an
  evolution task is active but not at the move-learning sub-state — so if the
  move-learn prompt and the (cancelled) evolution overlap, control ping-pongs
  and never advances. The move-decision override (which_move_should_be_replaced)
  is verified correct and is NOT the cause.
- **Fix applied (both builds):** `LevelUpTravelBattleStrategy.should_allow_evolution`
  → always True, so the starter EVOLVES (the well-tested evolve→learn path) instead
  of the fragile cancel path — and the team is stronger for gyms (#24-evo).
- **VERIFICATION DEBT:** could NOT reproduce in the harness — every available
  checkpoint either isn't on a grass tile or the lead is too low to reach Lv16 in
  a test run, and post-story scripts block navigation to grass. NEEDS USER
  VERIFICATION on a real Treecko run. If it STILL hangs after evolving, the real
  culprit is the handle_battle precedence / move-dialogue guard above (fix there,
  carefully, once reproduced) — and knowing WHICH screen it's frozen on (evolve
  screen vs "delete which move?" vs move summary) pins it instantly.
- **Prevention:** keep a grass checkpoint with the lead near each evolution level
  for fast move-learn/evolution testing.

## 2026-07-20 — REAL cause of the Lv16 move-learn hang: battle handler exits early  (ML-11, supersedes ML-10)
- **Symptom (user):** starters hang while learning a move at Lv16, still in
  pre-evolved form; bot doesn't stop.
- **ML-10 was WRONG** (blamed the evolution-cancel path; enabling evolution did
  NOT fix it). REPRODUCED definitively with a debug_create_pokemon Treecko Lv15
  (exp just below 16) fought in a TRAINER battle: the freeze is a PURE MOVE-LEARN
  hang — the `BattleScript_AskToLearnMove` instruction repeats forever with
  **Task_EvolutionScene INACTIVE**. Wild battles never froze; only trainer
  battles, and FLAKY (~50%), because the level-up move-learn surfaces AS the
  trainer battle is ENDING.
- **Root cause:** `battle_handler.handle_battle`'s loop was `while
  battle_is_active()`. In a trainer battle the move-learn prompt can appear the
  frame the battle goes inactive → the loop EXITS → the "Delete which move?"
  prompt is left unhandled → the mode's run()/navigation spins → hang.
- **Fix (both builds):** loop while `battle_is_active() OR a move-learn/evolution
  dialogue is pending`, and dispatch to `handle_move_replacement_dialogue` when
  the learn-move dialogue is active even if the battle instruction has moved on.
  Verified: trainer-battle repro 4/4 clean (learns Pursuit + evolves to Grovyle);
  wild path unchanged.
- **Prevention:** end-of-battle prompts (move-learn, evolution, nickname) must be
  handled by a loop that outlives `battle_is_active()`. Reproduce battle edge
  cases with debug_create_pokemon + a real TRAINER battle, not just wild.
- NB: the earlier `should_allow_evolution → True` change is KEPT (user wants
  evolution ON by default; it's a real feature) but was NOT the freeze fix.

## 2026-07-20 — Move-learn hang, the ACTUAL harness-vs-real cause: dispatch order  (ML-12, refines ML-11)
- **Symptom (user):** even after ML-11's loop-outlives-battle fix, the Lv16
  move-learn STILL froze on the "Delete a move?" prompt on the real 32× run —
  while EVERY offline reproduction passed. An unexplained harness-vs-real gap.
- **Root cause:** `handle_battle`'s if/elif dispatch checked the action-selection
  callback FIRST: `if get_main_battle_callback() in ("HandleTurnActionSelectionState",
  "sub_8012324"): handle_battle_action_selection(...)`. The main battle callback
  can still read `HandleTurnActionSelectionState` on the frames the post-battle
  move-learn prompt is displayed. When it did, the move-learn `elif` (several
  branches lower) was never reached — the frame was spent in action-selection,
  which just waits for a turn menu that isn't there → the prompt sat unhandled →
  hang. Offline harnesses that stepped a clean move-learn (callback already past
  action-selection) never hit this ordering, which is why they passed.
- **Fix (both builds):** reordered the dispatch so `AskToLearnMove` /
  `_move_learn_dialogue_active()` and an in-progress evolution scene are dispatched
  FIRST, ahead of the action-selection / item-steal / pay-day checks. A move-learn
  or evolution now always wins the frame. Also added `_dump_battle_stall_diagnostic()`
  on the no-progress watchdog to log the exact on-screen text + state to
  `<profile>/battle_stall.log`, so any residual freeze produces a precise report.
- **Prevention:** in a frame-dispatch if/elif chain, END-OF-BATTLE / modal prompts
  (move-learn, evolution, nickname) must be matched BEFORE the general
  turn/action-selection branch — a lingering action-selection callback otherwise
  intercepts them. When an offline harness passes but the real bot hangs, suspect
  DISPATCH ORDER / state the harness doesn't reproduce, and instrument the real
  run (a stall-time diagnostic) rather than trusting the harness again.

## 2026-07-20 — Lv16 move-learn hang: ROOT CAUSE FOUND + fix VALIDATED by fault-injection (ML-13, supersedes the ML-12 hypothesis)
- **Symptom (user, many sessions):** a starter learning a move at Lv16 (Treecko →
  Pursuit) freezes on the "Delete an old move to learn Pursuit? YES/NO" prompt at
  32× and never recovers. Every prior offline test passed → an unexplained
  harness-vs-real gap. The `battle_stall.log` diagnostic (ML-12) never appeared
  because the freeze is inside the move handler, not the handle_battle watchdog.
- **How it was finally reproduced (the method that worked):** a FAITHFUL headless
  harness that replicates main.py's loop EXACTLY (FrameInfo + get_bot_listeners +
  controller-stack advance + run_single_frame) — `scratchpad/repro_movelearn.py`.
  Inject a Treecko at `exp_for_L16 - 1` as the party lead, walk it into the Route
  103 rival (a SINGLE-Pokémon trainer) with encounters avoided, so it crosses Lv16
  on the KO that ENDS the battle. Tracing every frame (state, tasks, on-screen
  battle text, `is_waiting_for_input()`) showed the real mechanism.
- **ROOT CAUSE:** the Emerald *battle* "Delete a move to make room for X?" Yes/No
  has **NO backing task** (`tasks=[]` the whole time). `get_learn_move_state()` can
  therefore only recognise it by a **fragile script-offset equality**
  (`gBattleScriptCurrInstr == BattleScript_AskToLearnMove + 0x11`). When that exact
  offset is never observed, the state stays **`Unknown`**. The old handler's
  `Unknown` branch pressed A **only when `is_waiting_for_input()`** — but that reads
  the FIELD text-printer (`sTextPrinters[0]`), which in battle lags ~140 frames and
  in the worst case is **always False**. Fragile-state + unreliable-gate ⇒ the
  handler pressed **nothing** ⇒ frozen on the Yes/No. (My env happened to resolve
  the offset at frame +496, so it limped through — the real env doesn't.)
- **The ML-12 dispatch-order hypothesis was WRONG (a red herring).** A pre-vs-post
  A/B of the ML-12 reorder on the repro was **byte-identical** — the action-selection
  callback never intercepted the move-learn. ML-12 (dispatch reorder + stall
  diagnostic) is harmless/defensive and kept, but it is NOT the fix.
- **THE FIX (validated):** rewrote `handle_move_replacement_dialogue` to be fully
  **TEXT/TASK-driven** (design §DA): detect the Yes/No from the on-screen text
  ("make room for" / "Delete a move") as well as the state, drive the move-select
  from the reliable `Task_HandleReplaceMoveInput`, and advance ALL other text with A
  **directly** (never gated on `is_waiting_for_input()`). Also hardened
  `handle_evolution_scene`'s hand-off (it waited only for `AskWhetherToLearn` before
  delegating — same fragility; now it breaks on state OR text OR the move-select
  task, with a guard).
- **PROOF (fault-injection A/B, both builds):** a `--break-state` switch forces
  `get_learn_move_state()` to never report AskWhetherToLearn (→ Unknown) and
  `is_waiting_for_input()` → False — i.e. the user's exact failing environment.
  * OLD code: **stalls ~10,600 frames** on the prompt and **fails to learn Pursuit**
    (only escapes via the safety-backout, which declines the move).
  * FIXED code: resolves in **394 frames**, learns Pursuit, evolves to Grovyle,
    final moveset sensible (Fury Cutter, Pursuit, Absorb, Quick Attack).
  Verified on BOTH sandbox and custom.
- **Prevention:** the Emerald battle Yes/No prompts are NOT task-backed and MUST NOT
  be detected by script-offset alone; read the on-screen text. NEVER gate a battle
  button-press on `is_waiting_for_input()` (it is the FIELD printer). When an offline
  test passes but the real bot hangs, build a FAITHFUL main.py-loop harness and, if
  the bug still won't reproduce, FAULT-INJECT the suspected fragile signal to prove
  the failure mode and the fix. Repro tooling: `scratchpad/repro_movelearn.py`.

## 2026-07-21 — ML-13 addendum: user-observed trigger (starter hits Lv16 MID-FIGHT vs Roxanne)
User reported the precise real-world trigger for the ML-13 move-learn hang: the STARTER
reaches Lv16 and learns a move MID-FIGHT during the Roxanne battle (before her Nosepass is
sent out) — i.e. a level-up move-learn in the MIDDLE of an ongoing TRAINER battle, with more
of the trainer's team still to come. Their intuition was that the bot seemed "confused about
whether it's supposed to evolve / keep fighting vs. learn the move." That matches the ML-13
root cause exactly: the mid-trainer-battle level-up lands on the task-less "Delete a move to
make room?" Yes/No, whose fragile offset-ONLY detection failed → the handler pressed nothing
→ froze. The overnight TEXT-DRIVEN fix handles this instance (confirmed in the from-scratch
run: the starter hit Lv16 in a real battle, "trying to learn PURSUIT" with ml=Unknown, and
the fix resolved it from the on-screen text). Coverage is universal across ALL move-learn
instances: (1) wild level-up, (2) TRAINER mid-fight level-up [this case], (3) end-of-battle
level-up, (4) move-learn DURING evolution, (5) multiple moves at one level, (6) level-up +
evolution at the same level (Treecko L16 → Pursuit + Grovyle). If it ever recurs, capture the
exact on-screen text + `battle_stall.log` — but it should not.

## 2026-07-21 — Monolithic Segment 1 re-ran the intro on any pre-Pokédex recovery
**Symptom:** Bot froze in place (Route 103 / Oldale) during early game; looked like
"stuck at the Oldale Poké Center after respawn." **Root cause:** `StoryMode._play`
Segment 1 was one block gated only by RECEIVED_POKEDEX; any recovery/resume before the
Pokédex re-entered it at `walk_off_truck_and_into_house()`, then `go_upstairs_and_set_clock`
called `navigate_to(PLAYERS_HOUSE_1F, …)` from a different map → BotModeError → derail
loop, player never moving. **Fix that worked:** gate the scripted intro on
`_has_starter()`; make train→rival→Pokédex resumable and flag-gated. **Prevention:** a
"segment" that runs a linear cutscene from a fixed start is NOT a resumable point — gate
it on a state that proves we're still at that start (no starter yet), never on a
downstream flag alone.

## 2026-07-21 — Reading gDisplayedStringBattle / gBattleMainFunc to detect "message on screen"
**Symptom:** A battle_handler change meant to advance a stranded "learned <move>!" message
instead looped handle_battle forever on the NEXT battle. **Root cause:** both
`gDisplayedStringBattle` and `gBattleMainFunc` retain their LAST values after a battle
ends (verified: the bot is controllable and progressing while the text still reads "grew
to LV. N!"). A check keyed on that stale text fired long after the battle. **Fix:** reverted;
use `player_avatar_is_controllable()` (require it STABLE for many consecutive frames — it
flickers during the return transition) as the "is the overworld actually usable" signal.
**Prevention:** treat gDisplayedStringBattle/gBattleMainFunc as STALE-after-battle; never
use them as a live "dialogue is up" gate.

## 2026-07-21 — Offline save-state repro is unreliable across a battle→overworld transition
**Symptom:** A state captured mid-transition (no_progress trap) deadlocked on reload —
unresponsive to A/B/movement for 6000+ frames — even though the LIVE run self-healed from
the same point. **Root cause:** a save state taken during the return transition captures an
inconsistent snapshot that can't resume. **Prevention:** don't trust a reloaded
mid-transition save state as evidence of a live hang; confirm hangs from the live run's
logs. Validate transition-timing fixes on the real bot, not just reloaded states.

## 2026-07-21 — A story grind spin() that doesn't consult the whiteout-abort flag
**Symptom:** bot spins in place at the respawn Poké Center after losing a wild battle
while training before the rival. **Root cause:** `train_lead_to_level`'s `spin()` stop
-condition was `level>=target or hp<=heal_at` — after a whiteout the game heals you
(hp=100%) and level is still < target, so the condition never fires, and the spin never
checked `story_should_abort()` (which `on_whiteout()` sets). **Fix:** `_story_spin()`
helper bakes the abort check + trailing `_check_abort()` into every story spin.
**Prevention:** ANY long-running story grind/wait MUST be abort-aware (go through
`_story_spin`, or call `_check_abort()` in its loop) so a mid-step whiteout unwinds it
into StoryMode.run's recovery — a stop-condition based only on level/HP is NOT enough
because a whiteout heals you.
