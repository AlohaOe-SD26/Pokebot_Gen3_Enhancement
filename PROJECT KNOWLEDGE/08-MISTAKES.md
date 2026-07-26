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

## 2026-07-21 — _navigate_through_scripts navigates to the MAP, not the coordinates
**Symptom:** `fight_rustboro_rival` never walked to the rival tile; it "returned" instantly
because we were already on the Rustboro map. **Root cause:** `_navigate_through_scripts`
loops `while _map_group_number() != dest_map` — it's for CROSS-map travel; on the same
map its loop body never runs, so the coordinates are ignored. **Fix:** use
`_navigate_riding_out(map, tile)` for a within-map walk that rides out scenes.
**Prevention:** `_navigate_through_scripts` = reach a MAP (rides out inter-map scenes);
`_navigate_riding_out` = reach a TILE. Pick by intent.

## 2026-07-21 — Emerald's forced PokéNav tutorial is a multichoice, not a msgbox
**Symptom:** after the PokéNav, walking out of Devon Corp hung 8000+ frames on
`RustboroCity_EventScript_PleaseSelectPokenav` → cutscene-timeout derail. **Root cause:**
it's a FORCED tutorial driven by `Task_HandleMultichoiceInput` (loops PleaseSelectPokenav
↔ MatchCallTutorial); A/B just re-picks the default and cursor-nav+A didn't clear it — it
requires the PokéNav APP to be opened + navigated. **Status:** not yet solved; story
stops cleanly before it. **Prevention:** when a scene won't ride out with A/B, inspect the
active TASKS (a `…MultichoiceInput`/menu task means a selection is required, not a
message) before assuming a dialogue-advance will clear it.

## 2026-07-21 — "Lead strongest" is wrong vs a type-countered rival (Rustboro grass rival)
**Symptom:** the Rustboro rival whited out our team even with the starter trained to Lv19.
**Root cause:** picking Mudkip makes the rival lead a grass **Grovyle**; Marshtomp
(Water/Ground) is **4× weak to Grass**, so leading our "strongest" (Marshtomp) feeds it to a
super-effective sweep, and the thin L7-8 filler can't finish. It's a TYPE-MATCHUP loss, not
a level problem. **Fix (design):** the rival is left NOT wired; wiring needs type-aware lead
selection (never lead a mon 4× weak to the foe's ace) + a capable second mon. **Prevention:**
`_lead_strongest_battler` is a level heuristic ONLY — for scripted trainer aces with a known
type, pick the lead by matchup, not raw level.

## 2026-07-21 — Never wire an unreliably-winnable battle into a flag-gated resume loop
**Symptom:** wiring `fight_rustboro_rival` into `_play` (gated on `DEFEATED_RIVAL_RUSTBORO`)
turned a losable battle into an infinite loop: whiteout → StoryMode recovery → re-enter the
same segment → train → fight → whiteout … forever (200k-frame run never progressed).
**Root cause:** a segment gated on "did we win?" with whiteout-recovery re-entry has no exit
when the battle isn't winnable with the current team. **Fix:** don't wire a battle until it's
reliably winnable; when wired, add an attempt-cap that stops cleanly (hand to manual) after N
losses instead of re-looping. **Prevention:** any flag-gated combat segment needs a
bounded-retry / clean-fallback path, never unbounded re-entry.

## 2026-07-21 — Emerald's PokéNav tutorial app can't be driven headless (video-off)
**Symptom:** after selecting POKéNAV in the Scientist's tutorial menu, the PokéNav app opened
(`gs=UNKNOWN`, `Task_Pokenav`/`Task_RunLoopedTask`) and neither A-spam (150 presses/1500
frames) nor B-spam advanced or closed it. **Root cause:** the tutorial opens the app in
`POKENAV_MODE_FORCE_CALL_READY` (you must actually place a Match Call), and the PokéNav's
graphics-driven looped-task UI does not progress in our `video=False` faithful harness.
**Fix:** skip the tutorial with a state-write to vanilla's post-tutorial end-state
(`skip_pokenav_match_call_tutorial`), proven in-harness. **Prevention:** graphics-heavy app
UIs (PokéNav, and likely similar) may be un-drivable headless — prefer a state-anchored
approach over UI-nav for them, and verify any UI-nav plan advances headless BEFORE building it.

## 2026-07-21 — Rival re-trigger broke on a persistent MET flag (stuck below the rival after a loss)
**Symptom (real HW):** losing the Rustboro rival → whiteout recovery → bot stood at (16,52)
below the rival and dropped to Manual instead of retrying. **Root cause:** `fight_rustboro_rival`'s
Down-step loop broke on `MET_RIVAL_RUSTBORO`, which stays set after a loss — so on the retry it
"thought" it had engaged while still on the staging tile and never stepped onto the y=53 trigger.
**Fix:** break on the ACTUAL engagement (battle active OR a rival coord-script running), never on
a persistent "met" flag; raise a derail if the trigger won't fire. **Prevention:** to detect a
scripted battle re-engaging, key off battle-active / the live script, NOT a one-shot progress flag.

## 2026-07-21 — Swap-train finisher can faint → bot strands on the choose-next-mon menu
**Symptom:** a long training run hung at `BattleScript_FaintedMonTryChoose` (PARTY_MENU) after
`MARSHTOMP fainted!` — the strategy didn't send a replacement. **Root cause (partial):** the
swap-train finisher heals only between battles at a narrow ~28% margin, so an unlucky hit faints
it; the after-faint replacement path then stalls. **Mitigation:** raised the training heal margin
to ~42% so the finisher heals earlier. **Still open:** the choose-after-faint handling itself must
robustly send a replacement (framework-level) — next task; a mon fainting must never strand the bot.

## 2026-07-21 — Double-battle faint hang: chooser returned the on-field partner
**Symptom (user):** in a double battle, when one active mon faints, the bot hangs on the party
menu trying to pick the OTHER on-field mon (slot 2) instead of a benched one. **Root cause:**
`LevelUpLeadBattleStrategy.choose_new_lead_after_faint` overrode the base chooser but dropped the
double-battle exclusion of the already-active battlers, so it returns the partner's party index —
which can't be selected. **Fix:** re-add the `is_double_battle` left/right-battler skip (mirror
`DefaultBattleStrategy`). **Prevention:** any `choose_new_lead_after_faint` override MUST skip
the currently-active battler(s) in double battles; the replacement can only be a benched mon.

## 2026-07-21 — Gym/trainer battle hung on an in-battle switch into a weak bench
**Symptom (user):** Roxanne with Torchic (Fire vs Rock) + L6-7 bench — bot stuck at the
in-battle PARTY_MENU (state=3), then Manual. **Root cause:** the trainer-battle strategy fell
through to the parent's rotate/flee logic when it had no "strongest move"; rotating into the
weak bench stalled the party-menu switch (`while PARTY_MENU: press A`) and fleeing a trainer
raises. **Fix:** trainer battles now ATTACK-only (never proactively rotate/flee); faints are
handled reactively by the after-faint path. **Prevention:** an un-fleeable battle (trainer /
gym / E4) must resolve every turn to an ATTACK or a valid switch — never a flee (raises) and
never a switch that can't complete; when in doubt, attack (the game Struggles) so the fight
plays through to win-or-whiteout. Any switch target must be a benched, non-fainted, non-active
mon that can actually be selected.

## 2026-07-21 — Training spin walked in place forever (no encounters, no derail)
**Symptom:** pre-gym training hung at Marshtomp L16 — stuck in the overworld grind spin with no
EXP gain for 20k+ frames, no exception → no whiteout/derail recovery. **Root cause:** `spin()`
can be somewhere it can't trigger encounters; the stop-condition (level ≥ target) never fires and
nothing raises. **Fix:** `_story_spin` no-progress watchdog (no party-EXP for 2400 overworld
frames → bail → caller re-navigates + retries). **Prevention:** any open-ended grind/wait loop
needs a no-progress escape that RE-TRIES (re-navigate), not just a hard timeout — a silent stall
with no exception bypasses the whiteout/derail recovery entirely.

## 2026-07-22 — Talking to Mr. Briney: four proven-wrong approaches before the right one
- **Symptom:** `sail_to_dewford` reached the cottage but could not start the sail; several
  distinct failure modes across runs (A-pressing at an empty tile; chasing him in circles;
  the whole room frozen solid with everyone stuck; "no path" errors to walkable tiles).
- **Root causes (each proven live in the harness):**
  1. Briney is NOT at his spawn tile (5,3) — he and Peeko PATROL a fixed ring around the
     cottage table (walk-sequence NPCs). A static approach-tile + face-press talks to air —
     and a face-tap toward an EMPTY tile STEPS onto it when already facing that way.
  2. navigate_to-ing to a tile adjacent to his CURRENT position: he has always moved on by
     the time the navigate lands (circled 30× without engaging).
  3. Greedy tail-chase: never catches a same-speed walker on a ring; worse, standing on the
     NPCs' route tiles while bumping created a THREE-BODY DEADLOCK (walk-sequence NPCs wait
     forever for their exact next route tile — they never re-route — so Peeko, Briney AND
     the player all froze permanently). Screenshot-diagnosed.
  4. Parking ON his route tile to force him to stop next to us: with TWO walkers lapping the
     SAME ring in the same direction (Peeko leads), the WRONG one always queues against us
     first; Briney freezes two tiles back, out of reach. Debug-trace-diagnosed.
  Bonus root cause: `calculate_path` marks every object's current AND previous tile as
  blocked, so in the tiny cottage the two walkers "seal" the room and navigate_to reports
  NO PATH to tiles the player can plainly walk to — indoor approach work needs manual steps.
- **Fix that worked:** `_talk_to_wandering_npc`: OBSERVE ~one patrol lap (record both
  walkers' route tiles; talk instantly if he passes adjacent; if the walkers freeze, WE are
  blocking — step off), then park on a walkable non-route non-warp tile ADJACENT to his
  route and face-tap+A when he transits past. Engaged on round 0-1 in every validation run.
- **Prevention rules:** (a) never assume an indoor NPC is at its map-JSON spawn tile — read
  the LIVE object (local_id) and treat "Walk Sequence" movement types as patrols; (b) only
  face-tap toward an OCCUPIED tile, and re-verify before pressing A; (c) never stand on a
  walk-sequence NPC's route tile longer than a moment; (d) don't trust navigate_to inside
  small rooms with walking NPCs. All four added to playbook §7.

## 2026-07-22 — Granite Cave: built the route from an unverified mental model (three fixes to converge)
- **Symptom:** the letter leg failed three different ways before the clean run: (1) "no path"
  to the B1F ladder I chose; (2) after correcting, B1F itself was split and the crossing was
  impossible; (3) after deriving the real chain, the walker PING-PONGED between floors for 9
  hops and gave up.
- **Root causes (all proven with static pathfinder probes):**
  1. I coded the chain from the atlas note "Steven's Room via B1F (12,3)" without verifying —
     (12,3) is actually the B1F↔B2F ladder pair, and Steven's door hangs off 1F (5,10).
  2. EVERY Granite Cave floor is split into disconnected walk-sections; the true route dips
     through B2F (five warps each way). A pairwise within-floor pathability probe of all
     warps gave the real graph in one shot — I should have run it BEFORE building.
  3. 1F has a ONE-WAY LEDGE (north section → entrance section), so "is the warp pathable from
     here" is DIRECTIONAL: from the north section the pathfinder truthfully reports the early
     ladder reachable (down the ledge), and a first-pathable-match chain scan rides it back
     down forever. Fix: pick the FURTHEST-ALONG pathable step.
- **Also:** a checkpoint save captured the instant a segment returned (dewford.ss1 v1) held a
  still-open arrival dialogue → loaded permanently non-controllable and every navigate raised.
- **Prevention rules:** (a) before building any multi-floor/warp route, compute the pairwise
  within-floor warp pathability graph (calculate_path statically — no walking needed) and
  derive the chain from THAT, not from atlas prose; (b) treat within-floor reachability as
  DIRECTIONAL (one-way ledges) — chain walkers pick the furthest-along reachable step;
  (c) never snapshot a checkpoint until the avatar has been STABLY controllable (~120 frames)
  with no active script — ride leftover dialogue out with B first.

## 2026-07-22 — Dock Briney "not present on map" (object events are camera-loaded)
- **Symptom:** `sail_to_slateport` derailed 5× with "NPC local_id=2 is not present on map
  DEWFORD_TOWN" — but Briney IS at the dock (12,9), and the same lookup worked fine in his
  cottage and for every indoor NPC before.
- **Root cause:** the GBA engine only materializes object events within camera range.
  After healing at the Dewford PC (west side), the dock (12,9) was ~10 tiles away — the
  object didn't exist in RAM, so the live `get_map_objects()` lookup legitimately found
  nothing. Small interiors never exposed this because everything is always in range.
- **Fix:** `_talk_to_wandering_npc(..., approach_hint=(x,y))` — when the target is absent,
  navigate to a walkable tile near its spawn first, then re-locate live. Validated (clean
  Ch8a run).
- **Prevention:** on town-sized maps, never conclude an NPC is absent/hidden from a live
  object lookup until you are standing near its spawn tile. (Playbook §7.)

## 2026-07-22 — Dewford dock stall: open arrival msgbox vs press-nothing waits (real-HW)
- **Symptom (user's debug log):** after the first sail the real bot froze at the Dewford
  dock (11,9): derails #1-4 of "player avatar is not controllable", then Manual. The
  harness had never hit it.
- **Root cause:** the post-sail arrival script leaves Briney's "deliver the LETTER"
  reminder msgbox OPEN. `wait_until_truly_controllable` (and the derail recovery's wait)
  presses NOTHING by design — correct for battle-transition flickers, but an open
  dialogue needs a button press to close, so every wait timed out and every navigate
  raised, forever. The harness missed it because the committed dewford.ss1 checkpoint
  had the dialogue already ridden out (and the earlier content ENDED at arrival, so
  nothing ever navigated afterward).
- **Fix:** both sail legs ride out the arrival script (B) before waiting; the derail
  recovery now ALSO B-rides any active script before its stable-controllable wait.
  PROVEN by the full-arc run (post_rival → Slateport, 0 derails through both arrivals).
- **Prevention:** any "wait to become controllable" that can follow a SCRIPTED ARRIVAL
  must be preceded by a bounded script ride-out; recovery paths must always be able to
  close a dialogue. (Playbook §7.)

## 2026-07-22 — Watchdog treated "Story (DEBUG)" as a huntable mode (exact-name set)
- **Symptom (real-HW log 3):** after Story (DEBUG) finished the built content and
  INTENTIONALLY handed to Manual at Slateport, the #22 watchdog "auto-recovered" it
  ("fault drop-to-Manual") — restarting the story mode, which re-handed to Manual.
  One-off restart in practice, but the latent risk was worse: the encounter-stall
  recovery (which may RELOAD SAVE STATES — forbidden for story runs since it rewinds
  the playthrough) was silently re-armed for both DEBUG modes.
- **Root cause:** `_SELF_RECOVERING_MODES = {"Story"}` used EXACT string membership;
  the new modes are named "Story (DEBUG)" / "Story (DEBUG - RESET)" and fell outside
  every story-mode exemption.
- **Fix:** `_is_self_recovering(mode)` — exact match OR "<name> " prefix — used at both
  gate sites. A/B (pure logic): all three story names now exempt; Spin/Manual and the
  hypothetical "Storyteller" remain non-exempt.
- **Prevention:** when adding a VARIANT of a mode (new name, same bot), grep every
  mode-NAME comparison in the codebase (`context.bot_mode ==`, name sets) — behavior
  keyed off mode names silently excludes new variants.

## 2026-07-22 — Doc sequencing gap (KI-11) + NPC approach tiles on walls (Ch8b)
- **KI-11 root cause = documentation, not code.** The §Ch8b doc (built from static recon +
  decomp scripts) had the museum as freely enterable and Stern at the harbor (28,13). REALITY
  (user walkthrough + decomp): the museum is grunt-SEALED until you talk to Dock at Stern''s
  Shipyard (setflag FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA), and Stern is on museum 2F (13,6).
  Static recon + decomp-script-reading CANNOT see cross-location STORY SEQUENCING; a
  walkthrough can. → the /validate-docs process (cross-check decomp + recon + walkthrough
  before building) exists to catch exactly this. Prevention: validate a chunk''s doc against
  all three sources FIRST; never assume "enterable" from geometry alone.
- **NPC approach tiles must come from the collision grid.** Both Dock and Stern were first
  coded with the approach tile directly BELOW them ((5,6)/(13,7)) — both collision walls, so
  navigation failed and the wandering-pursuit bounced. Interiors wall NPCs on arbitrary
  sides. Prevention: probe the collision grid and pick a walkable adjacent tile + the facing
  toward the NPC; key the talk on the completion FLAG, not a fixed facing.

## 2026-07-22 — Unbounded menu navigation vs field scripts (the 110k-frame Joey stall)
- **Symptom:** real-HW: training on Route 116 froze 110k frames at (11,7) next to
  Youngster Joey; batch run02 froze 20k frames after a mid-training evolution. No derail,
  no Manual — a silent wedge.
- **Root cause:** `change_lead_party_pokemon` → `StartMenuNavigator.open_start_menu`
  waits UNBOUNDED for the Start menu — but a field script (trainer sight-line, leftover
  evolution scene) LOCKS input, so the menu can never open. Story code called it raw at
  three sites.
- **Fix:** `_yield_bounded` (hard frame cap on any sub-generator) + `_rotate_lead_safely`
  (script-active pre-check; bounded drive; on interrupt: close menu, ride out scene,
  retry ×3, else skip the rotation). Proven by repro A/B on evostall.ss1.
- **Prevention rules:** (a) NEVER drive a stock menu navigator unbounded from story code —
  wrap in `_yield_bounded`; (b) any action that OPENS A MENU must check no field script is
  active first, and treat "script fired mid-menu" as an expected interruption (close, ride
  out, retry) — this is the first concrete slice of #24-interrupt.

## 2026-07-22 — One repro, three latent battle bugs (the KI-12 chain)
- **Lesson:** the 130k-frame party-menu wedge, the chooser-None crash, and the double-
  battle TypeError were ALL sitting on the same code path, each hidden behind the one
  before it. A single fault-injected repro (weak lead + weak bench vs a gym) peeled them
  one per run. Fix→rerun→next-bug is dramatically cheaper than three separate user
  reports.
- **Prevention rules:** (a) when fixing a crash on a path, RE-RUN the repro after the fix —
  assume more bugs hide behind it; (b) treat Emerald's two-sightline TRUE DOUBLE battles
  as a first-class case everywhere (any paired trainers — gyms especially — can produce
  one); every battle strategy MUST implement a non-fleeing decide_turn_in_double_battle
  for trainer battles; (c) never let a battle handler raise/crash mid-battle — a listener
  exception drops to Manual with the battle still on screen (an unrecoverable wedge);
  degrade to "send anything alive / attack with anything usable" instead.

## 2026-07-22 — A fix "proven" on an extracted savestate missed the organic bug (phantom-script stall)
- **Symptom:** batch run05 organically hung exactly like the archived evolution stall —
  AFTER the `_rotate_lead_safely` fix had "passed" its A/B on evostall.ss1.
- **Root cause (two layers):** (1) the real wedge was never the rotation — it was a
  phantom script context left active after an evolution, which suppresses wild
  encounters, starving the training spin of progress; (2) the A/B state had been
  extracted 20k idle frames after the stall began, and LOADING a savestate defuses the
  phantom — so the repro validated a state the organic run never passes through.
- **Fix that worked:** clear-leftover-scene guard at `_story_spin`'s no-progress bail
  (B-ride bounded), localized via generator-stack dump of the organic run.
- **Prevention rules:** (a) capture repro states AT THE MOMENT the wedge forms, not after
  idle frames — and remember savestate load/reload can itself defuse volatile wedge state;
  (b) when a "proven" fix fails organically, get the generator stack from the ORGANIC run
  before iterating — the sig alone localizes nothing.

## 2026-07-22 — Blind button-spam menu sweep deadlocked in lockstep (Ch9 after-faint wedge)
- **Symptom:** Ch9 validation hung 20k frames in the in-battle party menu
  (`BattleScript_FaintedMonTryChoose`, "MARSHTOMP fainted!") — with the KI-12 "bounded
  sweep" fix present and my widened dispatch confirmed running.
- **Root cause:** the bounded sweep still pressed A blindly every frame. With the cursor
  on a fainted mon AND slot 1 also fainted, A-spam cycled popup → "no energy left" →
  list → popup on the same slot forever; its rare corrective Down always landed during
  message/popup states where Down is swallowed. Bounded-but-blind just retried the same
  deadlock every 6600 frames via outer re-dispatch. (Also: the real popup task is
  `Task_HandleSelectionMenuInput` — the harness's tasks=[] read hid it; a live probe of
  the wedge state exposed it.)
- **Fix that worked:** state-aware sweep — each step reads cursor slot + party HP + which
  task is up, presses the ONE button that advances (A to dismiss text; A on popup only if
  the mon is alive, else B; Down to reach a living slot), with press/release gaps. Proven
  on the live wedge state (un-wedged in ~128 frames), then end-to-end.
- **Prevention rules:** (a) menu recovery loops must be STATE-AWARE (read cursor/tasks/HP
  and press the button that state needs) — blind spam can lockstep-deadlock with message
  timing; (b) "bounded" is not "safe": a bounded loop re-entered by its dispatcher is
  still an infinite loop — bound the OUTCOME (did the menu close?), not just the frames;
  (c) when tasks read as empty in a wedge, probe the live state — the task list from a
  harness snapshot can lie.

## 2026-07-22 — A phantom flag name silently gated a segment (Ch9a derail loop)
- **Symptom:** Segment 9a printed its success message yet its guard derail-looped to
  Manual — "completion signal" never true.
- **Root cause:** the guard checked flag "DEFEATED_RIVAL_ROUTE_110", which DOES NOT
  EXIST in Emerald (vanilla sets only `VAR_ROUTE110_STATE = 1` for this battle);
  `get_event_flag()` returns a silent False for any unknown name, so the mistake looked
  exactly like "not done yet". I had even probed the flag earlier and read its False as
  game state instead of questioning the name.
- **Fix that worked:** decomp-validated var predicate shared by segment AND guard;
  `_done()` now raises on unknown names; `audit_flag_names.py` catches phantoms
  statically (found exactly one — this one).
- **Prevention rules:** (a) before building on ANY flag/var name, verify it exists in
  the data table (run audit_flag_names.py with every chapter build); (b) a probe that
  prints False for a flag proves nothing until the NAME is proven real; (c) segment
  completion predicates and their guards must be the SAME function — two spellings of
  "done" will eventually disagree and derail-loop.

## 2026-07-22 — Trusted the map API over the game's own screen (Mauville maze, 4 wasted runs)
- **Symptom:** every plan said "path open"; the player bumped an invisible wall for 20k
  frames. Probes "confirmed" open tiles. Four validation runs and many probes died on
  contradictory evidence.
- **Root cause:** `get_map_data`/`calculate_path` read the ROM's STATIC map layout. Maps
  that setmetatile at runtime (Mauville Gym beams; also e.g. trick-house/ice puzzles
  later) exist only in the LIVE grid (`gBackupMapLayout`). The API is silently wrong for
  exactly the maps where it matters. A SCREENSHOT immediately showed the beam the data
  denied — taken hours into the investigation instead of first.
- **Fix that worked:** read the live grid directly inside the maze; plan on it; judge
  every leg by arrival, not by the planner's opinion.
- **Prevention rules:** (a) on any runtime-modified map, treat static map data as WRONG
  by default — read gBackupMapLayout; (b) when memory reads and observed behavior
  disagree, SCREENSHOT FIRST — one image killed a four-run mystery; (c) probe states
  must have clean provenance — every probe re-saves current_state.ss1 at shutdown, so
  chained probes drift; snapshot the repro to its own file (mauville_wedge.ss1 pattern)
  and always load THAT.

## 2026-07-22 — Training tile picked without a two-way pathability sweep (runs 11-13) + a lying bail message
- **Symptom:** three straight Wattson-prep runs died with "Could not reach <grass> (too
  many scene interruptions)" — at three different tiles.
- **Root causes:** (1) I picked training tiles from a has_encounters/collision probe
  WITHOUT pathability — Route 110's NE grass is Cycling-Road-walled, its south grass is
  ledge-one-way, and Route 117's north strip sits on a shelf the road can't return
  from; only Route 117's south-central field is two-way reachable (found by sweeping
  ALL 162 grass tiles from the REAL entry tile (55,6)). (2) `_navigate_riding_out`'s
  bail message blamed "scene interruptions" for what were instant PLAN failures — two
  runs were misdiagnosed off it before a probe of the actual call told the truth.
- **Fix that worked:** ROUTE117_TRAINING_GRASS = (31,16) (swept two-way); the bail
  message now includes the real last error.
- **Prevention rules:** (a) a training/grind tile is only valid after a TWO-WAY
  calculate_path sweep FROM THE REAL ENTRY TILE of the approach (not from an assumed
  edge tile — shelves/ledges make edges lie); (b) every retry-loop bail message must
  carry the LAST underlying error verbatim — a summary that guesses the cause sends
  the next debugging session down the wrong road.

## 2026-07-23 — A wall that wasn't: ledges read as collision, so the maze looked unsolvable
**Symptom.** The Lavaridge gym solver spent runs 5-9 flailing: it fell through holes,
walked to warp tiles that never fired, blacklisted them, re-fell, and finally bailed
with "could not solve the trapdoor maze". Successive sessions layered heuristics on it
(tried-hole memory, dead-vent blacklists, 900-frame settle waits, a hardcoded "trap
hole" list) and each one moved the failure without fixing it.
**Root cause.** Both floors were decomposed into chambers using `collision` alone.
Behaviour 59 (`MB_JUMP_SOUTH`) ledges have collision=1 but are hoppable downward two
tiles — and in this gym the ledges ARE the connections between chambers. Treating them
as walls made several chambers look exit-less, which is a shape that cannot occur in a
shipped game. When I finally built the graph statically it proved there was NO path to
Flannery — and that contradiction is what located the bug in one step.
**The fix that worked.** Model the hop as a one-way edge, derive the room graph from the
ROM, BFS it. The maze collapsed to a deterministic 4-fall chain and worked first try.
**Prevention rule.** `collision` is not passability — check the metatile BEHAVIOUR too
(ledges, and anything else that moves the player without being walkable). And when a
derived map model says a shipped game is unwinnable, the model is wrong: stop tuning the
heuristics and go prove the model instead.

## 2026-07-23 — "Ride out the cutscene" as an unconditional failure path is a hang
**Symptom.** After the gym walk was blocked by an NPC, `do_lavaridge_gym` sat at (13,16)
for 18,000 frames until the global watchdog derailed it — five times, then Manual.
**Root cause.** The failed-leg path called `_ride_out_scripted_scene("B")` unconditionally.
There was no scene; the helper waited out its engage timeout and then B-mashed against a
stale non-controllable battle-return state until it timed out. A blocked walk was being
"recovered" as if it were a cutscene.
**The fix that worked.** Ride out only when `get_global_script_context().is_active` is
actually true; otherwise settle briefly and re-plan, with a consecutive-stall budget that
raises a truthful error.
**Prevention rule.** A generic recovery must first CHECK that the thing it recovers from
is happening. An unconditional "wait for X to finish" on a path where X may never start is
a hang with extra steps.

## 2026-07-23 — "A" to advance dialogue re-opens it (the museum greeter loop)
**Symptom.** On real hardware the bot entered Slateport's Oceanic Museum and looped at
the greeter until it dropped to Manual. In-harness the same state cycled `Std_MsgboxNPC`
for 8000 frames and then threw "Cutscene did not end".
**Root cause.** Scene ride-outs press "A" so a Yes/No (the ¥50 fee) can't be declined.
But A next to an NPC is not "advance text" — it STARTS a conversation. Each press
dismissed the attendant's message and instantly re-opened it. Tracing the on-screen text
settled it in one look: `'Please enjoy yourself.'` — the fee was already paid, so there
was no choice to answer, only a message we kept re-requesting. A second, subtler window
did the same thing: the helper also pressed during the non-controllable TAIL after a
script ended, which re-triggers whoever we happen to be facing.
**The fix that worked.** Resolve the button per frame: A only while a Yes/No or
multichoice menu is actually on screen, B otherwise (B advances dialogue identically but
can never initiate it). And press only when a script is running or a text printer is
waiting on input — never during the tail.
**Prevention rule.** Never mash A to get through dialogue. A is for answering a choice
that is on screen NOW; use B to advance or dismiss. If a "wait for the scene to end"
helper presses a button, it must first confirm there is something on screen to press it at.

## 2026-07-23 — A greedy stepper is not a pathfinder (Dewford dock detour)
**Symptom.** User watched the bot leave the Dewford Poké Center and take a scenic route
east of the gym, loitering by the townsfolk for thousands of frames before finally
talking to Briney. It eventually worked, which is why it survived earlier reviews.
**Root cause.** Briney is STATIC at the dock, but the code used the wandering-NPC helper,
whose known-spot fast path is `_step_to` — single greedy steps toward the target with
perpendicular fallbacks and no route planning. Dewford has a wall band at y=10 (x=10-13)
between the y=11 corridor and the dock, so "keep heading east then north" dead-ends and
the fallbacks walk it into the south-east pocket. `_step_to` exists for a real reason
(in tiny rooms, patrolling walkers make `calculate_path` report "no path"), but it was
being used on a whole town.
**The fix that worked.** Walk straight to the dock tile with the real pathfinder, face
Briney, talk; keep the wandering procedure as a fallback. And in the helper itself, try
the pathfinder before falling back to greedy stepping.
**Prevention rule.** Match the walker to the space: pathfinder for anything room-sized or
bigger, greedy stepping only inside a small room where the pathfinder is provably blocked
by walkers. And when an NPC is static, don't reach for the wandering-NPC machinery at all.

## 2026-07-23 — The HM mule was picked by level, not by compatibility
**Symptom.** User report from a fresh-start real-HW run: the Rock Smash teach can loop
forever in the party menu. In our own logs the teach always worked — because Marshtomp
(compatible) happened to be the highest-level mon in every test party.
**Root cause.** Segment 10b taught `max(levels)` with no compatibility check. The party
menu shows an incompatible mon as NOT ABLE and refuses the selection — an A-mash
experiences that as an endless loop. Swellow (a routine catch that often outlevels the
starter mid-game) cannot learn Rock Smash: the trigger was party-composition luck.
**The fix that worked.** Pick by compatibility (`hm_learner_slot`), hunt+catch a learner
when the party has none (`ensure_hm_learner`, grounds derived live from encounter tables
× learnsets), and make `teach_hm_move` refuse an incompatible target truthfully.
**Prevention rule.** Any selection that feeds a game menu must validate against the
menu's own acceptance rule first — "best by our metric" is not "accepted by the game".

## 2026-07-23 — A silent except turned a scope bug into 252 wasted encounters
**Symptom.** The new HM-learner catch branch never fired: the hunt fought 252 wilds for
120k frames and caught nothing. No error anywhere.
**Root cause.** The branch read the module-level `console`, but LATER branches in the
same method do `from modules.console import console` locally — Python therefore treats
`console` as function-local for the WHOLE method, so the early reference raised
UnboundLocalError… which the branch's own defensive `except Exception: pass` swallowed
on every single encounter.
**The fix that worked.** Import `console` locally in the branch; found in minutes once
the except was temporarily instrumented to print the exception.
**Prevention rule.** Two rules. (1) A function-local import shadows the name for the
entire function — check the whole method before referencing a module-level name that is
also imported locally anywhere in it. (2) A `try/except: pass` around a DECISION means
failure = silently wrong behaviour, not a crash — when a decision branch mysteriously
never fires, instrument the except FIRST; don't re-derive the conditions by eye.

## 2026-07-23 — "game_state == OVERWORLD" does not mean the menus are closed (KI-14)
**Symptom.** After teaching Rock Smash, travel wedged for 12k+ frames and dropped to
Manual at Mauville — on the user's machine, twice, while every harness validation of
the teach flow passed.
**Root cause.** The teach's "B out until the overworld is back" loop exited on
`game_state == OVERWORLD` — but the START MENU (which the bag closes back into) is
itself an overworld state, so the loop declared success with the menu open and the
avatar frozen. The hardened cutscene rider then (correctly) refused to press at a menu
that is neither a script nor waiting text. Masked in harness runs because past
validations either stopped at the teach or B-mashed forever afterward (hmtest driver).
**The fix that worked.** A `_menu_task_active()` probe: menu-free = OVERWORLD state AND
no start-menu/list/party-menu task AND avatar controllable; and the cutscene rider now
presses B specifically when a menu task is up (B can close a menu but never open a
conversation, so the museum-greeter fix stays intact — re-proven).
**Prevention rule.** Never use `game_state == OVERWORLD` as "the UI is closed" — menus
live inside the overworld state. Ask the task list. And when a "recover by pressing"
helper gets a new guard, enumerate what the guard now EXCLUDES (here: menus) and decide
deliberately who handles that class instead.

## 2026-07-23 — A field script the game abandoned still "reads active" (Route 111 rock hang)
**Symptom.** The bot smashed the first Route 111 rock, a wild Geodude popped out of the
smash, and after the battle the run wedged at (18,101) forever — script context active,
avatar controllable, nothing on screen — until the user killed it. Same signature the
batch-8 sweep had already queued (bail→re-enter→re-wedge).
**Root cause.** Two layers. (1) `_smash_rock` judged success by "the smash script
ended" — but Rock Smash's wild-encounter roll can interrupt the field script with a
battle, after which the script context can stay marked active forever even though the
game has fully returned control. (2) Every script-gated wait downstream (the rider, the
recovery's rider) trusted that same flag, so the whole stack spun on a phantom.
**The fix that worked.** Judge by the WORLD, not the script: the rock OBJECT vanishing
is the success signal (and its absence on re-entry makes the step idempotent). Plus a
generic escape: sustained "playable + quiet + script-active" (600 frames) = a parked
context — treat the scene as over.
**Prevention rule.** A script-context flag is a HINT, not ground truth — after any
battle can interrupt a field script, verify completion by observable world state
(object gone, tile passable, flag set). And never let two layers (step + recovery)
both block on the same unverified signal: the second layer just doubles the hang.

## 2026-07-23 — Approach tile off by one at the cable car; a guard that passed on failure
**Symptom.** The bot reached the Mt. Chimney cable car station and sat frozen at (6,8)
for thousands of frames, never boarding, until the user killed the run.
**Root cause (two).** (1) It approached (6,8) and faced Up to talk to the attendant —
but the attendant is at (6,6) (the code AND its docstring both said (6,7)); facing Up
from (6,8) looks at the empty (6,7), so A did nothing. Nobody had probed the station
map; the coord was assumed. (2) Downstream, Segment 11c's guard was `_cur_map() not in
descent_origin` — which is TRUE at the Fallarbor whiteout-respawn, so a FAILED descent
reported success and the next segment ran from the wrong place.
**The fix that worked.** Probe the map (attendant (6,6) → approach (6,7)); guard on the
actual goal state (in Lavaridge / badge earned), not on "left the origin"; and give the
one-way descent a real recovery (re-ride the cable car when stranded below).
**Prevention rule.** Two. Probe interaction coordinates from the ROM before trusting a
remembered tile — an NPC one tile off is a silent no-op. And a completion guard must
assert the GOAL was reached, never merely that we left the starting area — "not at the
start" is not "arrived", and the difference is exactly a failed/interrupted segment.

## 2026-07-23 — Gating an input on "script inactive" when the prompt IS the script (slow Rock Smash)
**Symptom.** Rock Smash field use crawled — ~30s per rock, ~127s for the two Route 111
rocks — though it eventually worked.
**Root cause.** `_smash_rock` pressed A to answer the "Use ROCK SMASH? YES/NO" prompt
only `if not get_global_script_context().is_active`. But that prompt is served by an
ACTIVE field script, so the guard was always true-negative: A never answered it, and the
rock only broke when the outer 3-attempt loop re-pressed A after a 1800-frame idle.
**The fix that worked.** Press A on a fast fixed cadence (every 10 frames), unconditional.
In this context extra A presses are harmless (the tile is empty after the smash).
**Prevention rule.** Do not gate "advance/answer the prompt" inputs on "no script
running" — the prompt you are answering is itself a running script. Gate on whether an
input could do HARM (start a conversation, pick a destructive option), not on script
activity.

## 2026-07-23 — A milestone save captured inside a menu (rocksmash_taught)
**Symptom.** Loading the rocksmash_taught milestone in the GUI dropped the player into
the bag menu; the resuming Story mode then drove a navigator under the open menu.
**Root cause.** The checkpoint was captured mid-teach while the bag was still open
(state = BAG_MENU, not controllable). Save states must be taken from a stable
controllable overworld to be safe resume points.
**The fix that worked.** Regenerate the checkpoint from a clean overworld (teach ->
normalize -> verify -> round-trip). AND, structurally, a `normalize_to_overworld()` step
at Story resume so ANY awkward entry state (menu/dialogue/battle/cutscene) self-heals.
**Prevention rule.** Capture checkpoints only from a stable, controllable overworld
(assert it before writing). And make resume tolerant of arbitrary entry states rather
than assuming a clean overworld — users load states from anywhere.

## 2026-07-23 — "the object is gone" is not "the script is done" (KI-16 Rock Smash wedge)
**Symptom.** Deterministic hang resuming from wattson_done: after smashing the Route 111 rocks,
the next navigation wedged forever at (18,99) — avatar controllable, but a field script stuck.
**Root cause.** `_smash_rock` judged success by the rock OBJECT disappearing (a good idempotency
signal) and returned immediately. But `EventScript_SmashRock` continues past the object removal
into `WaitForMovementFinish` (the crumble/step animation). Returning early let the caller's
navigation start a player movement that CANCELLED the one the script was waiting on, so the
script never finished and every subsequent step wedged. It only surfaced from wattson_done
because that save's RNG fired a wild battle at the trigger spot; other paths dodged it.
**The fix that worked.** After the object is gone, wait for `get_global_script_context()` to go
inactive (pressing nothing, so the movement isn't interrupted) before handing control back.
**Prevention rule.** When a scripted interaction removes an object, "object gone" is a valid
COMPLETION-of-effect signal but NOT a completion-of-SCRIPT signal — the field script can outlive
the object (WaitForMovementFinish, cleanup). Before navigating away, wait for the field script
itself to clear, and don't press movement inputs while it's finishing.

## 2026-07-23 — A documented bug diagnosis that no log actually supported (KI-15 phantom party-menu)
**Symptom.** ~A full session was spent building fault-injection repros (poison, then burn, a
`faintrepro` no-flee driver) to reproduce an "after-faint PARTY_MENU chooser hang with a 1-HP
Wonder Guard Shedinja." Every approach failed to reproduce it — because the bug as described did
not exist.
**Root cause.** The KI-15 write-up (and a compaction summary built on it) asserted a specific
party (Marshtomp/Shedinja/Swellow/Poochyena/Ninjask), coords (7,9), and stack
(`BattleScript_FaintedMonTryChoose`, `bt='SHEDINJA fainted!'`) that were never in any captured
log. `grep -r "SHEDINJA fainted" livetest-runs/**/run.log` = 0 hits. The real confirmed hangs
(same batch, run05) had a totally different signature (post-battle story-resume: OVERWORLD +
`cb=ReturnFromBattleToOverworld` + `BattleScript_PayDayMoneyAndPickUpItems`, in
`_wait_until_cutscene_over` / `navigate_to`). The diagnosis had been written from memory/inference,
not from the log, and every later session inherited it.
**The fix that worked.** Go back to the PRIMARY EVIDENCE: read the actual `run.log` of the
confirmed hang (`summary.json: hang_confirmed=true`) before writing or trusting any diagnosis.
The real signature was obvious in 40 lines of the log tail.
**Prevention rule.** A known-issue entry MUST cite the exact log line/file it came from; if you
can't `grep` the cited symptom (e.g. the hang `bt=` string) out of a real run.log, treat the
diagnosis as UNVERIFIED and re-derive it from the log before spending any repro effort. Trust logs
over summaries — including this project's own prior write-ups.

## 2026-07-24 — A reader-level "signature" for a wedge state that another state shares exactly
- **Symptom:** Two KI-15 fix attempts in a row regressed or missed: (1) escalating B→A after
  40 frames whenever `is_waiting_for_input()` persisted re-opened the Slateport museum
  greeter every 40 frames (its tail matches the same broad signal); (2) a "narrow" signal
  built from `sTextPrinters` + `WaitForAorBPress` read FALSE on the actual captured wedge —
  the stale post-battle message ALSO waits via the stale `WaitForAorBPress` native, and the
  raw printers say not-waiting on BOTH states.
- **Root cause:** assuming two behaviorally-different states must differ in some memory
  reader. They don't have to: the wedge and the parked dialogue tail are byte-identical
  on every reader we have — and BOTH ignore B indefinitely (a third design, a 450-frame
  B→A rider escalation, also looped at the museum because the tail never expires either).
  The ONLY divergent property is functional: the wedge BLOCKS ALL MOVEMENT; the tail
  doesn't (the story can just walk away from it).
- **Fix that worked:** revert the rider to its old behavior entirely (parked waits =
  free) and clear the wedge at the ONE seam that can see "nothing has moved for
  seconds": StoryMode.run's nudge — waiting + no scripts + POSITION FROZEN for 240
  frames → a single A → long cooldown.
- **Prevention rule:** before keying a fix on a reader signature, probe the OTHER states
  that signature could match (load the captured .ss1s, print the readers side by side);
  when readers tie, discriminate by a FUNCTIONAL property (does movement work? does the
  state survive being left alone?), and re-run the regression probe of the class you're
  touching (museumprobe2 here) BEFORE committing — all three failed designs were caught
  that way, none reached a commit.

## 2026-07-24 — An every-frame "helpful nudge" is an A-mash: it created the wedge it was meant to fix
- **Symptom:** a run-loop nudge that pressed A whenever `waiting-for-input + no scripts +
  cb=ReturnFromBattle` held DID clear the (14,5) wedge — and then A-mashed the Rustboro
  nurse's dialogue into an endless re-open loop (a brand-new 15k-frame hang, captured as
  `ki15_nurse_wedge.ss1`).
- **Root cause:** `gBattleMainFunc` (cb) is STALE after every battle — it stays
  "ReturnFromBattleToOverworld" until the NEXT battle — so the guard was effectively just
  "a message is waiting", and a live dialogue's script context flickers inactive between
  message boxes, letting the every-frame A through. A beside an NPC = "talk", so each A
  re-opened the conversation (the museum-greeter lesson in a new coat).
- **Fix that worked:** persistence + position-freeze + single-press + cooldown (240 stable
  frames with the PLAYER POSITION unchanged → one A → 1200-frame cooldown). A live dialogue
  or tail cannot survive 4s of frozen-in-place play; the wedge (which blocks all movement)
  trivially does.
- **Prevention rule:** any autonomous "unstick" press must (a) require the stuck signature
  to persist for seconds, (b) include a can't-be-mid-flow guard (position frozen), (c) press
  ONCE, (d) cool down long enough for the world to react — never per-frame; and never trust
  `cb`/`gDisplayedStringBattle` alone (stale liars).

## 2026-07-24 — "Same-map two-way path" does NOT prove the story can reach a tile
- **Symptom:** a new training-area table shipped tiles verified by a two-way `calculate_path`
  between two tiles ~8 apart on the SAME map. Two were unusable: Route 111 (25,55) sits NORTH
  of the Go-Goggles desert (reachable from Fallarbor, never from Mauville/Petalburg — and no
  Mauville-side Route 111 grass exists at all), and Route 114 (18,29) is unreachable from
  EVERY real story anchor (Mauville/Fallarbor/Rustboro/Petalburg).
- **Root cause:** same-map connectivity only proves the tile is in *a* walkable region; a
  single map can hold several disconnected regions (deserts, rivers, ledges). The verification
  never asked "can the story get there FROM WHERE IT STANDS?"
- **Fix that worked:** verify every candidate tile from the REAL anchors the story occupies
  (the town PCs), and make the runtime picker position-aware — same region → a real
  `calculate_path` to the exact tile; cross-region → warp-graph `plan()` with a leg cap.
- **Prevention rule:** a map-data tile is not "validated" until a path is proven from an
  anchor the bot actually stands on; record WHICH anchor in the table comment.

## 2026-07-24 — A level-fit picker with no story-stage gate proposes places the bot can't go
- **Symptom:** `best_training_area(31)` returned Route 121 (past Lilycove, across water) for a
  pre-Surf team standing in Petalburg. The function matched its spec exactly — the SPEC was
  wrong (level fit only, no reachability, no HM gate, no travel cost).
- **Root cause:** delegating with an under-specified acceptance contract. The worker cannot
  invent constraints the spec omits, and its output looked correct in isolation.
- **Fix that worked:** three gates on top of level fit — HM prerequisite (Surf actually KNOWN,
  not just the badge), reachability from the current position, and a travel-distance cap
  (a training detour must be local; the warp graph will happily route across Hoenn).
- **Prevention rule:** when specifying a chooser, enumerate the DISQUALIFIERS, not just the
  ranking metric — and make the acceptance command assert a case that must return NOTHING.

## 2026-07-24 — A helper that returns on a state flag can hand back a dirty screen
- **Symptom:** HM teaching wedged in BAG_MENU. `ensure_hm_learner` returned the instant the
  caught-mon check passed, while the catch aftermath ("Give a nickname...?") was still up;
  `teach_hm_move` then opened the bag on top of it. Hit Surf (user-reported) and exposed every
  HM path including Rock Smash.
- **Root cause:** the spin's stop-condition ("party grew") is true well BEFORE the screen is
  clean, and `wait_until_truly_controllable` presses nothing by design, so nothing dismissed
  the prompt. A menu cannot open under a pending dialogue (the KI-14 class).
- **Fix that worked:** `normalize_to_overworld()` at BOTH ends — before returning from the
  catch helper, and again before the teach flow touches a menu (defence in depth; B answers
  the nickname prompt "no" and can never start an NPC conversation).
- **Prevention rule:** any helper that hands control to a caller which will open a MENU must
  return a normalized overworld, not merely a satisfied flag — and the menu-opening side
  should normalize again rather than trust its caller.

## 2026-07-24 — A branch-local loop guard cannot bound a multi-branch loop

**Symptom.** The torchic starter run hung forever at Route 111 (18,99) inside
`ensure_facing_direction` — the same tile that hung batch2 run04. The night before I had
added an input-starvation guard to that exact function and re-verified it, so I believed the
loop was bounded.

**Root cause.** `ensure_facing_direction` is a `while True` with several branches, and BOTH
existing guards were incremented inside a branch. The failing post-battle state reads
perfectly settled (OVERWORLD + NOT_MOVING + NOT_MOVING), so control always took the
"press the direction" branch — which RESETS `starved_frames = 0` on every iteration. The
press never lands, `facing_direction` never changes, and no counter in the function is ever
allowed to grow. The guard was live, correct, and structurally unable to fire.

**The fix that worked.** A branch-INDEPENDENT `total_frames` counter incremented at the top
of the loop body, raising `BotModeError` at 1800 frames. Turns a silent forever-hang into a
derail StoryMode can recover from. Both walking repros re-verified.

**Prevention rule:** every `while True` gets ONE counter incremented unconditionally at the
top of the body — per-branch counters are diagnostics, never the bound.

## 2026-07-24 — "tasks=[]" in my own dumps never meant what I read it to mean

**Symptom.** Across several investigations (KI-15's "transient tasks=[]", the torchic
starter-run wedge) the harness's NO-PROGRESS dump printed `tasks=[]`, and I repeatedly read
that as "the game has no tasks running — the wedge is not task-driven." I built theories on
top of that reading for days.

**Root cause.** That field printed `active_ml_tasks()`, which filters the live task list down
to FIVE hard-coded move-learn task names. It can therefore print `[]` while the game is running
a full, busy task list. Every wedge caused by a task OUTSIDE that allow-list was invisible —
and the one that mattered, `ExecuteMatchCall` (a PokéNav match call), is exactly such a task.
Worse, a match call is a TASK and not a field script, so it is also invisible to every
script-context guard in the codebase.

**The fix that worked.** Print `tasks=` from the FULL task list (`_all_task_names()`) and keep
the filtered one as a separate `ml_tasks=` field. Also added `scripts=` (the active field-script
stack), which the harness never printed at all — that omission is why three long runs that all
died on Route 111 (18,99) could not be diagnosed from harness logs, while the user's in-game
DEBUG dump cracked it in one line.

**Prevention rule:** a debug dump may never print a FILTERED collection under an unqualified
name — call it `ml_tasks=`, or print all of it; an empty filtered list reads as absence of the
whole category and will be believed.

## 2026-07-24 — A story FLAG was recorded as a MAP limitation, and blocked a chapter for days

**Symptom.** `04-HANDOFF.md` carried a "RESUME HERE — Ch13e BLOCKED on the Fortree
tree-bridge" note claiming the gym door (22,11) was reachable only from (21,11)/(22,12) and
not from the plaza, blamed on planner-blind elevation walkways (the Route-119/120 class). The
prescribed fix was to probe and add a `_hold_walk_route` held-input route — real work, on a
problem that did not exist.

**Root cause.** The observation was made while standing in the PRE-FLUSH world state. The
Fortree gym-path Kecleon occupies (25,8), the single chokepoint tile between the walkway and
the door cluster, and is hidden/removed by story flag **969 HIDE_FORTREE_CITY_KECLEON**. With
the Kecleon still there, everything past it fails to plan — which looks exactly like a map
limitation and is actually a story-sequencing state. `get_devon_scope` already flushes that
Kecleon before `do_fortree_gym` runs, so the real playthrough never hits it.

**The measurement that settled it.** Forcing flag 969 True at the reader level made (22,11)
plan from (25,7) in 9 waypoints, from the plaza (5,6) in 38, and from ROUTE120 (5,15) in 115.
Control: (22,12) is fully walkable both before and after, so the pre-flush failure came from
the one gated tile, not a second broken one.

**Contrast worth keeping.** The neighbouring real bug, (24,8), looked *identical* on the
surface — collision=1, all four directions inaccessible — but had NO `warps_to`, so it was
permanently unreachable under every game state. Same surface reading, opposite verdict. The
discriminator is the tile's TYPE and warp data, not its collision flags.

**Prevention rule:** a reachability claim is only valid together with the world state it was
measured in — record the story flags in force, and before calling a tile unreachable, check
whether a story flag gates the route to it.

## 2026-07-24 — A recovery helper's guard matched half the map, including its own destination

**Symptom.** Ch13d validation runs derailed repeatedly with
`held walk: never reached (13, 15) heading Up.` It looked like the avatar could not leave
the Route 120 bridge — so the first two hypotheses were an NPC standing on (13,15) (Steven,
mid-departure) or a terrain/elevation wall like the (24,8) bug found the same day.

**Both hypotheses were wrong.** Probed: (13,15) is `collision=0`, unoccupied at load and
across 2000 zero-input frames (Steven's template flag 972 already flushed), and holding Up
from (13,16) reaches it in well under 120 frames.

**Root cause.** `_leave_route120_north_bridge()` guarded on
`map == ROUTE120 and y <= 16`. That is true of the entire WESTERN half of Route 120 —
including **(5,15), the helper's own destination**. The first crossing succeeded; then a
mid-route battle and StoryMode restart re-entered the helper from (5,15), where its
hard-coded "hold Up until (13,15)" is geometrically impossible (holding Up only changes y,
and x=5 ≠ 13). It burned the 900-frame per-leg bound and raised, every time.

**A/B proof** (`tools/story-dev/repro_route120_bridge_guard_fault.py`): from (13,16) the
identical generator returns in 359 frames; from (5,15) it raised after 1101. After narrowing
the guard to the strand column (`y <= 16 and x >= 12`): (13,16) still returns in 359 frames
(unchanged), (5,15) returns in 0.

**Why it hid so long.** The helper is idempotent-looking and "no-op unless stranded" per its
own docstring — but the no-op test did not actually test for STRANDED, it tested for a broad
coordinate box. A guard that is wrong only on re-entry is invisible until something causes
re-entry, and here that was an unrelated wild battle.

**Prevention rule:** a "no-op unless X" guard must test X itself. If the helper's own
destination satisfies its entry condition, the condition is wrong — check that explicitly
when writing any recovery/idempotent helper.

## 2026-07-24 — Route 111 (18,99) SOLVED: a STALE READER, and my own bound had shrunk a real one

**The bug.** Four long runs across two machines died on Route 111 (18,99). Rock Smash rolls a
wild encounter; the battle interrupts `EventScript_SmashRock`; afterwards
`get_global_script_context().is_active` reads **True for the rest of the run**. Measured on a
captured save: never clears in 25,000 frames of zero input, while
`player_avatar_is_controllable()` reads True and pressing a direction turns AND walks the
avatar instantly ((18,99) → (18,97) in 60 frames). **It is a stale reader, not a lock.**
`ensure_facing_direction` deferred to that gate and B-mashed a parked context forever.

**Fix.** Phantom-script escape matching `_ride_out_all_scenes` / `_wait_until_cutscene_over`:
after 600 consecutive frames of script-active AND controllable AND not waiting-for-input, stop
trusting the gate for the rest of that call. Requires BOTH liveness signals, and resets the
counter the moment the avatar is genuinely locked, so a real scene never accumulates.
A/B: before — `travel_to_fallarbor` never returns in 12,000 frames, permanently parked at
(18,99); after — crosses off Route 111 by frame 5,000.

**‼ THE SECOND BUG, IN MY OWN EARLIER FIX (found by reviewing the diff, not by a test).**
This morning I added an absolute `total_frames > 1800` bound at the TOP of the loop. It
therefore counted frames spent *legitimately riding out a field script* in the branch below,
silently shrinking that branch's own 4800-frame tolerance to 1800 and making its bound dead
code. A genuine cutscene lasting 30–80 seconds would have begun raising instead of being
ridden out — a regression that would have shown up as random unexplained derails during long
scenes, nowhere near the code that caused it. The counter now increments only on the PRESSING
path, which is the loop it was written to bound. Verified: the locked-scene control raises at
4800 again, not 1800.

**Prevention rules.**
1. Before concluding "the game is stuck", press a direction and check whether the avatar
   actually moves. A reader that says "busy" while the game plays normally is stale — this is
   the third reader in this project with that property (`gBattleMainFunc`,
   `gDisplayedStringBattle`, now the field script context).
2. A loop-wide counter added to a loop with per-branch counters will silently override the
   smaller ones. When adding an absolute bound, check every existing bound it now preempts.

## 2026-07-25 — I overrode a correct model default with a two-generation-old model, ~35 times

**Symptom.** A day of Gemini research produced a high hallucination rate: an invented item with
invented coordinates and flag, HM07 placed in the wrong cave (twice — the critique "corrected" it
to a different wrong cave), a fabricated bike prerequisite, a wrong outbreak species, a wrong held
item, and a fabricated correction to a claim that was already right. I concluded "Gemini is
inaccurate" and the user agreed, directing that Claude validate Gemini from now on.

**Root cause — mine, not the model's.** `gemini_relay.py` already had
`DEFAULT_MODEL = "gemini-3.1-pro-preview"`, set by a user directive on 2026-07-23 precisely
because it gives better results. I passed `--model gemini-2.5-pro` on **every single call** —
because the module docstring's usage example showed `--model gemini-2.5-pro`, and I copied the
example instead of reading `DEFAULT_MODEL` twelve lines below it.

**The calibration that proved it.** Asked `gemini-3.1-pro-preview` the two claims 2.5-pro had got
wrong twice each — where HM07 Waterfall comes from, and whether the bike has a prerequisite. It
answered BOTH correctly on the first attempt, and volunteered the Ruby/Sapphire difference that
explains why the older model kept confusing them ("unlike Ruby/Sapphire, where it's found in the
Cave of Origin").

**Consequences.** ~35 research calls, one adversarial critique round and one adjudication round
were all run on the wrong model. The notes are still notes, so nothing was corrupted downstream —
but the effort spent diagnosing "Gemini's accuracy" was substantially spent diagnosing my own
flag. Fixed the misleading docstring example so the next agent cannot repeat it.

**Prevention rules.**
1. A tool's DOCSTRING EXAMPLE is not its default. Read the actual default constant before passing
   an override — and never pass an override you did not consciously choose.
2. When a tool starts producing bad output, check YOUR invocation before concluding the tool is
   bad. "The model is inaccurate" and "I selected a worse model" look identical from the outside.

## 2026-07-25 — Added a GUI feature to the GUI the user does not run (twice, before checking)

**Symptom.** The user asked for an "Endless Debug-Reset Runs" item in the Play section, tested,
and reported "still cannot see the option". I had added it to `modules/gui/emulator_controls.py`.

**Root cause.** This fork has TWO GUIs. `pokebot.py` builds the **dashboard** GUI
(`modules/gui/dashboard_gui.py`) by DEFAULT; `emulator_controls.py` is the **classic/upstream**
GUI, reachable only via the opt-in `-cg / --classic-gui` flag (`pokebot.py:94,181`). I found a
"Bot Mode" dropdown with a "Debug Logging" checkbutton in `emulator_controls.py`, recognised it as
the right-looking place, and never checked whether it was the DEFAULT surface. Both files contain a
near-identical menu, which is exactly why grepping for the pattern finds the wrong one first.

**Compounding it:** I then "verified" the work with syntax checks, a static name-resolution check,
and path arithmetic — all of which passed, none of which could detect that the code was in an
unreachable file. Green checks on the wrong file look identical to green checks on the right one.

**The fix.** Item added to `dashboard_gui.py`'s Play-tab mode menu (and kept in the classic GUI so
both surfaces have it), in both builds.

**Prevention rules.**
1. Before adding anything user-visible, confirm WHICH surface the user actually launches — read
   the entry point (`pokebot.py`) and find the DEFAULT branch, don't pattern-match on a file that
   merely looks right. `--classic-gui` being opt-in was the deciding fact and took one grep.
2. When two files contain near-identical UI code, assume a grep will land on the wrong one and
   check the entry point before editing either.
3. A feature I cannot exercise myself (a GUI dialog) is not verified by static checks. Say so
   plainly, and name the surface it was added to so the user can catch a mismatch immediately.

## 2026-07-25 — I built a subprocess launcher when the user asked for a chained BOT MODE

**Symptom.** The user asked for "endless debug reset runs back to back" in the Play menu. I built
a CLI batch runner and a menu item that spawned it as a detached process. The user reported: "I
get all the messages but it doesnt seem to actually run the instances, like debug reset does
(effectively chained debug reset bots)."

**Root cause.** I solved a different problem. "Endless debug-reset runs" means the EXISTING
`Story (DEBUG - RESET)` mode — hard reset → NEW GAME → play the story — repeated back to back
**in the running emulator**. I built an external headless harness that runs its own emulator
instances, so from the GUI nothing visibly happened: the dialog confirmed, a console spawned
elsewhere, and the bot the user was watching sat idle. The phrase "like debug reset does" was in
the original request and I did not weight it.

**The fix.** `StoryEndlessResetMode` ("Story (ENDLESS RESET)") — a real bot mode subclassing
`StoryDebugResetMode` whose `run()` loops the parent, swallowing `BotModeError` so one bad run
never ends the batch, forcing the bot mode back after each run (a deep derail can call
`set_manual_mode()` and would otherwise stop the batch silently), and bounding each run by frames.
The menu item now sets `ENDLESS_RESET_TARGET` and selects that mode instead of shelling out.

**Prevention rules.**
1. When a request names an EXISTING feature as the unit of repetition ("like debug reset does"),
   the implementation is a loop around that feature — not a new mechanism that achieves something
   similar. Re-read the request for the noun the user reused.
2. "The dialogs work but nothing happens" is the signature of work happening somewhere the user
   cannot see. Ask where they expected to see it before debugging the mechanism.
3. Plugin bot modes register automatically (any `BotMode` subclass defined in
   `plugins/custom_modes/*.py`) — but `get_bot_modes()` returns nothing for them unless plugins
   are loaded, so verify registration through `CustomModesPlugin().get_additional_bot_modes()`.

## 2026-07-25 — Verification effort spent on the wrong axis: "agreement" is not evidence

**What I did.** After finding that ~35 research notes ran on a two-generation-old model, I re-ran
10 story angles on the correct one and had a Claude agent ground the **disagreements** — reasoning
that a disagreement means at least one side is definitely wrong, so it is an efficient search
target. That part worked well.

**What I got wrong implicitly.** I treated the diffing as the whole safety story, which quietly
implies that where the two agreed, things were probably fine. The adjudication measured it:
**where both generations AGREED they were still wrong ~35% of the time** (15 BOTH-WRONG rulings).
Both models share the same misconceptions about this game, so consensus carries almost no
information. "Two independent sources agree" is only evidence when the sources are actually
independent — two runs of the same model family are not.

**Second, sharper finding.** The two generations fail in DIFFERENT PLACES, so "3.1 is better" is
too coarse to act on. 2.5-pro hallucinates *citations* (it invented both a map constant and a
script label and tagged the claim VERIFIED). 3.1-pro's names are far better (phantom flag names
35% → 11%, head-to-head 21–1) but it hallucinates in the **actionable** layer: all three of its
"your bot must hardcode an interrupt here" constraints rested on permanence that does not exist —
so acting on them would have meant building interrupts for items that cannot be missed.

**Prevention rules.**
1. Consensus between models of the same family is not corroboration. Only an EXTERNAL oracle
   counts — the decomp, `modules/data`, `audit_flag_names.py`, or a live probe.
2. Grade a model per SECTION, not per model. Gemini's symbol/flag/map NAMES are worth reading;
   its architectural recommendations are not, and it is confident in both.
3. When a research pass tells you to build a guard, ask what would happen if the guard were
   absent. Three of these guards would have protected against nothing at all.

## 2026-07-25 — A repro's "verdict" was a mock leak: `_stand_at()` patched only half the position

**Symptom.** `tools/story-dev/repro_fodder_grass.py` case 5 asserts that a L31 team standing in
FALLARBOR_TOWN produces `SKIP GRIND`. That looked like a deliberate statement about Fallarbor. It
was not — it was a partially-applied mock, and it blocked a correct change.

**Root cause.** The helper `_stand_at(town)` patches `modules.map.get_map_data_for_current_position`
and nothing else. But the code under test, `_training_area_allowed`, takes a second reading of
"where am I" from `modules.player.get_player_location()` before calling `calculate_path`. That call
is unpatched, so it returned the save's real position — `(PETALBURG_CITY, (7,6))` on
`norman_done.ss1` — and `calculate_path(PETALBURG_CITY(7,6) → ROUTE111(25,55))` raises
`PathFindingError`. The test recorded that refusal as if it were the Fallarbor answer.

**Proof it was a leak, not a judgement.** `calculate_path(FALLARBOR_TOWN(14,8) → ROUTE111(25,55))`
SUCCEEDS, and `region_reach` puts Route 111 two hops from Fallarbor. `training_areas.py`'s own
comment on that entry says "reachable from Fallarbor, NOT from Mauville/Rustboro/Petalburg". Every
independent source says reachable; only the half-mocked test said otherwise.

**Cost.** It silently vetoed the `#24-regionreach` training-gate switch — the change looked like a
regression when it was the fix. Nothing was shipped; the attempt was reverted pending a user ruling
(KI-24b).

**Fix that works (not yet applied — needs the user's call, since re-baselining an acceptance test
is not a thing to do unilaterally):** have `_stand_at()` patch `get_player_location` too, so the
mocked position is total.

**Prevention rule.** When you mock "where the player is", patch EVERY reader of that fact — grep
the function under test for all position sources before trusting its verdict. A half-mocked
precondition does not fail loudly; it silently answers a different question and calls it a pass.

## 2026-07-25 — RETIREMENT NOTICE: four prevention rules whose mistake is now structurally impossible

Per `CLAUDE.md`'s `/reconcile` guidance: a prevention rule whose underlying mistake has been made
impossible by a test, a guard, or a refactor should be RETIRED, because a stale "don't do X" keeps
that idea alive in every future agent's context forever and costs tokens for no protection.

**Nothing above is deleted or edited — this file is append-only.** The entries stand; this notice
records that their PREVENTION RULES no longer need to be carried forward. If a structural guard
named below is ever removed, the corresponding rule becomes live again.

### R1 — RETIRED: ML-5's "anchor story position on badge level, never on a single flag/item"
*(entry: 2026-07-20 — "Story detection: naive single-signal scans mis-place saves")*

The entry carries its own retirement condition, and it is now met. `tests/test_story_progress.py`
(present in BOTH builds, 12 tests) asserts exactly the two properties the rule describes:
* `test_current_chapter_never_leaves_its_badge_bracket` — loops every badge level 0-8 and asserts
  placement never escapes its bracket, which is the badge-anchoring rule as an executable claim;
* `test_hacked_save_stone_plus_stray_magma_emblem` — the specific hand-edited-save shape (Stone
  Badge + a stray Magma Emblem) that produced the ch16c mis-placement.

A regression cannot ship silently now, so the rule does not need to be read to be obeyed.

### R2 — PARTIALLY RETIRED: the phantom-flag rule (a) only
*(entry: 2026-07-22 — "A phantom flag name silently gated a segment (Ch9a derail loop)")*

**Rule (a)** ("before building on ANY flag/var name, verify it exists in the data table") is
retired: `_done()` in `plugins/custom_modes/story_mode.py` now raises a `BotModeError` on any name
absent from `modules.memory._event_flags`, so a phantom name is a loud build error at first use
rather than a silent False that reads as "not done yet". A typo cannot reach a derail loop.
`audit_flag_names.py` remains as the static complement.

**KEPT — rules (b) and (c), which have NO structural guard:**
* **(b)** a probe that prints `False` for a flag proves nothing until the NAME is proven real.
  The guard protects `_done()`; it does not protect an agent reading a one-off probe's output.
* **(c)** a segment's completion predicate and its guard must be the SAME function — two spellings
  of "done" will eventually disagree and derail-loop. Nothing enforces that structurally.

### R3 — RETIRED: ML-4's "audit a vendored app's self-update triggers for a nested-`.git` assumption"
*(entry: 2026-07-19 — "Stock auto-updater silently active in the fork")*

`pokebot.py` now walks EVERY ancestor directory for a `.git`
(`any((parent / ".git").exists() for parent in [_base, *_base.parents])`) before it will consider
running the stock updater — in both builds. The specific layout assumption that broke (upstream
expected `.git` inside the bot folder; ours is at the repo root) can no longer re-break, and the
guard is layout-agnostic rather than patched for our particular depth.

*Scope note:* this retires the rule as stated, which was specifically about the nested-`.git`
assumption. The broader habit — audit what a vendored app does on its own initiative — is general
engineering judgement, not a rule this file needs to carry.

### R4 — PARTIALLY RETIRED: the Gemini docstring-example rule (rule 1 only)
*(entry: 2026-07-25 — the ~35 research calls run on `gemini-2.5-pro`)*

**Rule 1** ("a tool's DOCSTRING EXAMPLE is not its default") is retired *for this tool*:
`gemini_relay.py` now REFUSES any model that is not Pro 3.1+ (`_is_pro_31_or_newer`, fail-closed on
anything unparseable, Flash/Flash-Lite/Gemma rejected regardless of version), with an explicit
`--allow-weak-model` escape hatch. Copying a stale docstring example can no longer silently
downgrade a research round — it exits with a message naming the directive and the fix.

**KEPT — rule 2: "when a tool starts producing bad output, check YOUR INVOCATION before concluding
the tool is bad."** This is the rule that actually cost the day, it generalises to every tool in
the project, and there is no structural guard for it anywhere. It stays.

## 2026-07-25 — A PARTIAL MOCK: the regression guard for all training logic tested the wrong world

- **Symptom.** `tools/story-dev/repro_fodder_grass.py` case 5 asserted that a L31 team standing in
  FALLARBOR_TOWN produces `SKIP GRIND`. It read as a deliberate statement about Fallarbor. It was
  not: the test had never put the player in Fallarbor. The case vetoed a CORRECT change — the
  `#24-regionreach` training-gate switch — by making the fix look like a regression.

- **Root cause: one reader stubbed, another left live.** `_stand_at(town)` patched
  `modules.map.get_map_data_for_current_position` and nothing else. But the code under test,
  `_training_area_allowed`, takes a SECOND reading of "where am I" from
  `modules.player.get_player_location()` before calling `calculate_path`. That call was never
  patched, so it returned the save's real position — `(PETALBURG_CITY, (7,6))` on
  `norman_done.ss1` — and `calculate_path(PETALBURG_CITY(7,6) -> ROUTE111(25,55))` raises
  `PathFindingError`. The test recorded that refusal as a Fallarbor verdict.

- **Why it survived so long.** A partial mock does not fail loudly. It silently answers a different
  question and returns a plausible-looking result, so it reads as a pass forever. And the verdict it
  produced (`SKIP GRIND`) was *reasonable* for the scenario as written, which is what made it
  invisible. **This file is the regression guard for every training-logic change of the preceding
  two days** — the frames-based budget gate and the fodder-skip itself both shipped green against it
  — so one of its five cases had been certifying nothing while the header printed "proven-good prep
  unchanged".

- **Proof it was a mock artefact and not a judgement.** Three independent sources agree Route 111 IS
  reachable from Fallarbor: `calculate_path(FALLARBOR_TOWN(14,7) -> ROUTE111(25,55))` succeeds;
  `region_reach` measures it at 2 hops; and `training_areas.py`'s own comment on that entry says
  "reachable from Fallarbor, NOT from Mauville/Rustboro/Petalburg". The decisive A/B: with
  `_stand_at()` repaired and `story_mode.py` **untouched**, the ORIGINAL `calculate_path` code also
  answers `RELOCATE to ROUTE111` — and cases 1-4 are unchanged. So the re-baseline is a test fix,
  provably not a behaviour change.

- **Fix that worked.** `_stand_at()` now derives both mocks from ONE source (the town's Poké Center
  door tile, a real walkable story-relevant position), patches `get_player_location` as well as
  `get_map_data_for_current_position`, and asserts the two describe the same map so it cannot drift
  apart again. `_stand_down()` restores both. Case 5 re-baselined to `RELOCATE to ROUTE111` with the
  evidence in a comment, so a future reader can tell "we fixed the test" from "we broke the feature".

- **Process note — what actually caught it.** The instruction was "the acceptance test MUST pass; if
  it fails, STOP and report; do not adjust the test." Following that literally is what surfaced the
  bug. Adjusting the expectation to make the feature land would have shipped the right feature and
  left the mock leak in place, silently certifying every future training change.

- **Prevention rule.** A mock that simulates a state must patch EVERY reader of that state — patch
  one of two and the test silently exercises the real world. Before trusting a repro's verdict, grep
  the function under test for all sources of the thing you stubbed.

## 2026-07-25 — PATTERN (not an incident): two tests in one day were asserting things that depended on a BUG

- **Symptom.** Fixing KI-24 turned the suite RED in two separate places, both of which looked at
  first glance like the fix had broken something. Neither had. Both tests were encoding the
  defect as if it were the specification:
  1. **`repro_fodder_grass.py` case 5** asserted `SKIP GRIND` for a L31 team in Fallarbor. That
     verdict was only reachable because `_stand_at()` leaked (one of two position readers left
     live), so the case was really asking about `(PETALBURG_CITY, (7,6))`. **The assertion needed
     the mock leak to hold.**
  2. **`repro_counter_plan.py:200`** asserted `False in [c["reachable"] for c in wide_cands]` —
     "at least one candidate must be UNREACHABLE" — as a non-vacuity guard for the
     reachable-first sort proof. **The assertion needed `calculate_path`'s false negatives to
     hold.** Fix the predicate and the wide set becomes all-`True`, so the required failure has
     nothing to find.

- **Root cause (the shared shape).** Much of this suite was written to CHARACTERISE defects — to
  pin down and hold still behaviour we had just diagnosed. That is a legitimate way to write a
  test, but it produces assertions phrased as *"a failure occurs here"* rather than *"this
  property holds"*. Those two phrasings are indistinguishable while the bug is live and diverge
  completely the moment it is fixed: the property-shaped one keeps passing, the symptom-shaped one
  inverts and reports the repair as a regression.

- **Why this is worth an entry rather than two footnotes.** It is a systematic risk for this
  project specifically. The suite is largely defect-characterisation, so **every future fix in
  a well-tested area should be expected to turn something red for this reason**, and the first
  instinct — "my change broke a test, back it out" — is exactly wrong. It cost real time twice in
  one day, and the second instance was very nearly written off as collateral damage from the first.

- **‼ Both were found ONLY because a change forced them to fail.** Neither would ever have been
  noticed while green. A partial mock and a bug-dependent guard both report success indefinitely;
  there is no passive signal. That is the uncomfortable part — the number of *remaining* assertions
  of this shape in the suite is unknown, and the only thing that surfaces them is fixing the bug
  they lean on.

- **Fixes that worked.** (1) `_stand_at()` patches every reader of the state it simulates, from one
  source, with an assert that they agree. (2) The non-vacuity check MOVED from the wide set to the
  Winona set — the list this planner exists to produce — and now asserts the property it actually
  needs: that the list spans BOTH branches, so "sorted reachable-first" has content. Both changes
  are commented with what they replaced and why, so the next reader can tell a repaired test from
  a weakened one.

- **Prevention rule.** A test that asserts a FAILURE occurs — "at least one unreachable", "raises",
  "returns empty", "is refused" — inverts the moment that failure is fixed. Assert the PROPERTY you
  need (both branches exercised; the ordering holds; the guard is reachable) rather than a symptom
  of the current bug, or the suite punishes progress.

- **Corollary for reviewers.** When a fix turns a test red, the first question is not "what did I
  break" but **"was this assertion depending on the thing I just fixed?"** Check whether the
  expectation could ever have been satisfied by CORRECT behaviour. If not, the test was
  characterising the defect and should be re-shaped — but re-shape it in its own commit, and prove
  the re-shaped test green against the UNCHANGED code where that is possible.

## 2026-07-25 — I fixed a Unicode-console crash in one tool and reintroduced it in the next

**Symptom.** `compare_runs.py` died mid-report with `UnicodeEncodeError` while analysing the
user's logs — an em dash in `"Lavaridge maze — riding the geyser"`. The report was lost.

**Root cause.** Hours earlier I fixed *the identical bug* in `gemini_relay.py`, where a bare
`print()` of an answer containing `→`/`↓` crashed on the cp1252 Windows console and destroyed two
complete, already-paid-for API responses. I fixed that INSTANCE and never generalised it, then
wrote a brand-new analysis tool with the same bare `print()` of log-derived text — text which is
*guaranteed* to contain the em dashes the bot itself writes into `context.message`.

**Fix.** A shared `_safe_print()` that falls back to a UTF-8 byte write. Applied to every print
in the report path.

**Why it matters more than it looks.** Both crashes destroyed OUTPUT, not input: an API response
already paid for, and an analysis of logs the user had waited on. A tool that loses its result to
the terminal it is printing to fails at the only thing it exists to do.

**Prevention rule:** when a bug is caused by the ENVIRONMENT (console encoding, path separators,
line endings, locale), fix the CLASS not the instance — every sibling tool has the same
environment. Ask "what else prints/writes text here?" before closing it out.

## 2026-07-25 — The bug report named the last link in the chain, and I nearly fixed only that

**Symptom.** `#24-movelearn-recovery`, the #1 open item, killed 2 of 5 night5 cold-start runs at
~f1.55M each. Filed as: "the `BotModeError` is raised inside the BATTLE HANDLER, which sits OUTSIDE
`StoryMode`'s derail-recovery try/except — so the whole run dies instead of losing one battle. **The
recovery scope is the bug, not the move-learn logic.**"

**That framing was true and still nearly cost the fix.** The recovery scope really was broken, and
fixing it really was necessary. But it is the LAST link: it decides how expensively the run dies,
not why it wedges. Had I implemented only what the item asked for, the runs would still have died —
just with a nicer log line — and the item would have been ticked off.

**Root cause (found by reading the frames, not the item).** Four defects in series. Combusken
carries Rock Smash, which is both an HM and its weakest move. A stray A from the
"any unrecognised text → press A" branch answered YES to a prompt the bot had decided to DECLINE; a
cursor read from `sMonSummaryScreen` while the screen was still animating in was stale, so A landed
on the HM slot; the game replied with `Task_HandleInputCantForgetHMsMoves`, **a symbol nothing in
the codebase referenced**, which `get_learn_move_state()` misreported as the Yes/No prompt; and the
handler then fell into an UNBOUNDED "screen is still opening, just wait" branch and **pressed
nothing for 6,000 consecutive frames.** Only then did the valve fire and hit the recovery-scope bug.

**The measurement that broke it open.** The repro recorded every button press. The before-arm read
`{'B': 4050, 'A': 1350}` and **no `Down` at all** — exactly 3×1800 presses in the escape valve's own
3:1 ratio. That single line proved the main handler had pressed *nothing whatsoever*, which pointed
straight at the silent wait branch. A state trace alone would never have shown it: the states were
changing busily the whole time.

**Fix.** Recognise the refusal window and strike the refused slot off; never act on an untrusted
cursor; bound the wait; and route the valve's fault to the mode via `modules/battle_fault.py`
instead of raising across the controller stack. Before: WEDGED at f23,400. After: RESOLVED at f258
on one capture and f224 on the other, both with the moveset correctly unchanged.

**Prevention rule:** a bug report describes the symptom the reporter could SEE — treat its stated
root cause as the newest link in a chain, and walk backwards until you can explain the FIRST
abnormal frame. Before accepting "component X mishandles this", ask what the GAME was showing at
that moment and whether any code reads it: here the game was saying "HM moves can't be forgotten"
in a named task, and nothing in the bot had ever heard of it.

**Second prevention rule:** instrument INPUTS, not just states, when diagnosing a wedge. "Which
buttons, how many, in what ratio" distinguishes *pressing the wrong thing* from *pressing nothing*,
and those have opposite fixes. Every `while True` that can press nothing on a frame needs a bound —
an unbounded "just wait for the state to settle" branch is a hang with good manners.

## 2026-07-25 — "Super-effective" was treated as "sufficient", and it disabled the guard on the one boss that needed it

**Symptom.** `#24-whiteout` was filed as generic attrition. Measuring it instead showed **83% of
all losses are gym leaders** (Norman 38, Wattson 24, Winona 20, Flannery 18), and one run made
**27 losing Norman attempts over 508,000 frames** with KOs flat at 1–2 of 4 the whole way — a
plateau, not slow progress.

**Root cause.** `_boss_plan_is_hopeless` decides whether to give up on levelling by asking "does
any battler have a super-effective damaging move?" — `base_power == 0` was excluded, but nothing
else. Norman's team is entirely NORMAL; the only type super-effective against Normal is FIGHTING;
and the party's only Fighting move was **Rock Smash, the 20-power HM the bot is required to carry
to progress**. Effective power 40. The veto fired every time, so the detector could never flag the
boss it was most needed for.

**Why it slipped through.** The Winona case that motivated the detector had *no* super-effective
move at all, so a pure type test looked sufficient. Norman is the opposite shape: an answer that
exists on paper and is worthless in practice. One example does not pin a predicate — and the
counter-example was already sitting in a log.

**Fix.** Weight by real power: `base_power × effectiveness × STAB >= 60`. Verified both ways
against the REAL logged party — before `(False, [])`, after `(True, ['Fighting'])` — and guarded
with a second case proving a weak-but-real answer (STAB Double Kick, 30 × 2.0 × 1.5 = 90, the move
that beat Norman organically) still counts, so the threshold cannot be quietly raised until nothing
qualifies.

**Prevention rule:** when a predicate asks "do we have X?", make it ask "do we have ENOUGH X?".
A capability test that ignores magnitude will accept the cheapest token instance — and the bot's
mandatory HM moves are exactly such tokens (Rock Smash/Cut/Strength are all low-power attacking
moves it is forced to carry). Check any type-matchup logic for the same blindness.

**Second prevention rule — a fail-safe `except` that returns the SUCCESS value is invisible.**
This detector's `except Exception: return False, []` returns precisely what a healthy boss plan
returns, so any crash inside it reads as "everything is fine" while costing ~19,000 frames per
losing attempt forever. It bit immediately: the new test case returned `False` because the repro's
stand-in `self` was missing the new class constant, and the `except` ate the `AttributeError` —
the test failed for a reason that had nothing to do with the logic under test. When a guard fails
safe, make it fail LOUDLY: log that the guard is no longer protecting anything, or the difference
between "working" and "broken" is unobservable.

## 2026-07-25 — A metric that read 0, and a cost model that was wrong in the docstring's own words

Two failures from one live batch, both about BELIEVING A STATED CLAIM instead of checking it.

**(a) The metric that always read 0.** `livetest.py`'s batch summary reported `whiteouts: 0` for
all five runs — right after I had changed whiteout-adjacent code. It counted `"WHITEOUT recovery"`,
which is a `debug_logger.event()` payload written to the profile's debug-log FILE, while the
summarizer only ever reads stdout and run.log. The real counts were 36/5/9/6/10. **Every whiteout
number in every archived batch summary is meaningless**, and none of them was ever questioned.

*Why it nearly landed as a result:* "0 whiteouts, down from 128" is exactly the headline I wanted,
and it appeared in the same report as three genuine wins, so it read as consistent. It was only
caught by asking why a number I had no mechanism to improve had improved so much — I changed no
battle, healing, or attrition logic.

**Prevention rule:** a metric that moves to a PERFECT value (0 errors, 100% pass) after a change
that could not plausibly produce it is a broken metric until proven otherwise. Verify it against a
raw count from the same logs before reporting it. And when adding a counter, grep the stream you
are actually parsing for the marker — not the codebase for the string.

**(b) The cost model that was wrong in its own docstring.** `_training_area_allowed` was switched
to `region_reach` that morning on an explicit, well-argued cost asymmetry: a wrong NO is
"INVISIBLE and costs a whole run", a wrong YES "costs ONE wasted walk, which navigation then fails
RECOVERABLY and loudly". The reasoning is sound and the direction was right. **But a wrong YES cost
the whole run, in 2 of 5 lanes**, because the picker is DETERMINISTIC: the derail recovery re-ran
`_play`, which re-picked the identical unreachable Route 111 tile and failed identically, until the
derail budget hit Manual. "Recoverable" was true of the single failure and false of the loop.

*Fix shape that generalises:* rather than special-casing Route 111, make the claim TRUE — record
the failed `(standing map, target map, tile)` and stop proposing it. That also covers every future
gap in `KNOWN_GATES`, which the same docstring already flags as the standing residual risk.

**Prevention rule:** "this failure is recoverable" is a claim about the LOOP, not the failure. Before
relying on it, ask what re-runs after recovery — if the retry re-derives the same choice from the
same inputs, the failure is deterministic and recovery is a countdown to Manual, not a recovery.
Anything chosen by a deterministic picker must be REMEMBERED as failed, or it will be re-chosen.
