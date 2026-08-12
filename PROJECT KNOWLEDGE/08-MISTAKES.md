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

## 2026-07-26 — I walked into a documented trap that was commented three lines above my own code

**Symptom.** A new SURVIVAL MODE branch in `StoryMode.on_battle_started` did nothing. Its repro
reported the strategy unchanged for the exact state it was written to catch, and **nothing was
logged** — it looked exactly like "the condition is False".

**Root cause.** Several branches of that method do `from modules.console import console`. That
makes `console` a **function-local name for the WHOLE method**, so my block's `console.print(...)`
raised `UnboundLocalError` before it could `return RunAwayStrategy()` — and my own
`except Exception: pass` swallowed it.

**What makes this worth recording is not the Python rule, it is that the project already knew.**
The identical bug is in 08-MISTAKES (the 2026-07-23 HM-learner entry, "the function-local-import
shadowing lesson"), AND there is a comment about it *sixteen lines above where I typed*:

    # ‼ local import required: later branches in this method import
    # `console` locally, which makes the name function-local EVERYWHERE
    # in the method — referencing the module-level one here raises
    # UnboundLocalError (and the except silently ate the catch).

I read that comment while placing the block — I used the lines around it to choose the insertion
point — and still wrote `console.print` without the local import, because the module-level import
at line 21 made it *look* available.

**Why it was cheap this time.** The repro asserted the DECISION for the real run01 state, so the
failure surfaced in seconds instead of in a 40-minute live batch. The same silent-except that hid
the cause is also what the earlier fix-of-the-day made me suspicious of, so I went looking for a
swallowed exception rather than re-reading my condition.

**Prevention rule:** in a long method that imports anything locally, ANY name it imports is
function-local everywhere in that method — import it locally in your branch too, or hoist it. When
adding to an unfamiliar method, grep it for `import` before using a module-level name.

**Second prevention rule (a repeat, now escalated):** `except Exception: pass` around a decision
turns "your code crashed" into "your condition was False", which are debugged in completely
different directions. This is the SECOND time in two days it hid a live defect (the boss-plateau
detector's stand-in `self`, then this). Any silent guard around a branch that RETURNS a decision
should log the exception, not just pass — and a new branch should be proven by a repro that
asserts the decision, never by inspection.

## 2026-07-26 — A latent upstream bug that only a NEW CALLER could expose, and a threshold calibrated on one example

Both found by the validation batch, hours after both fixes had "passed" their repros.

**(a) The crash I shipped.** SURVIVAL MODE returns a flee strategy from `on_battle_started`.
Stock `RunAwayStrategy.choose_new_lead_after_battle()` returns **`False`** — annotated
`int | None` — and `BattleListener.fight()` rotates the lead whenever that value `is not None`.
So it rotated to party index `False` and `RotatePokemon` raised
`RuntimeError: Cannot rotate Pokémon #False with itself` right after "Got away safely!", dropping
the run to Manual with an empty controller stack.

The bug had been sitting in the framework the whole time. It was harmless because the ONLY caller
was `run_away_from_battle()`, which does not rotate leads. My change introduced a second caller on
a path that does. **My repro could not have caught it**: it asserted which strategy was CHOSEN,
and the crash happens in what the framework does with that strategy afterwards.

**Prevention rule:** when you route an existing class down a NEW code path, read what that path
does with it — not just what your code returns. Check the full protocol the new caller invokes
(here `choose_new_lead_after_battle`), not the one method you care about. A class that is correct
for its current caller is not thereby correct in general, and a value like `False` where `None` is
meant survives only until someone tests it with `is not None`.

**(b) The threshold calibrated on one example.** Yesterday I set `CREDIBLE_ANSWER_POWER = 60` so
Rock Smash (20 × 2.0 × 1.0 = 40) would not count as an answer to Norman. I checked it against the
run3 party — Marshtomp, a Water/Ground carrier. I did not check a **Fighting-type** carrier:
Combusken is Fire/Fighting, so its Rock Smash gets STAB and scores **exactly 60**, landing on the
boundary and passing. run05 then lost to Norman **21 times** with the guard silent — the precise
failure the threshold exists to prevent, arriving by a route I had not enumerated.

**Prevention rule:** a numeric threshold justified by ONE worked example is a guess with arithmetic
attached. Before fixing the number, enumerate what else feeds the formula (here STAB, which can
multiply the very case you are excluding by 1.5) and find a real data point on BOTH sides. The
threshold is now bracketed by two measured runs — 60 loses 21 times, 90 wins — instead of by one
example and taste.

## 2026-07-26 — The reported cause was the one thing that worked; and a heal gate that watched the wrong resource

**Reported:** a shiny appeared pre-Pokédex, "crashed the game — it tried to catch them", with a
suggested fix of disabling shiny logic until the Pokédex flag.

**What the log actually showed.** The shiny path was the ONE part behaving correctly: it detected
no usable Poké Balls, printed *"no catch possible here, fighting through"*, and **won** the battle.
The run continued **1.86 million frames** past it. The proposed fix would have suppressed working
code and left the real defect untouched.

**The real defect** was in the same log the whole time, and only one signal exposed it: the outcome
tally, **3,011 `RanAway` vs 5 `Won`**, with the party at **full HP**. `train_team` heals on
`_min_battler_hp_pct() <= heal_at`; the stock battle strategy flees when no move is USABLE — a PP
condition, not an HP one. A starter winning without being hit drains PP while HP stays at 100%, and
once PP is gone every battle is a flee, fleeing takes no damage, so the HP gate can never fire.
Permanent livelock at full health.

**Prevention rule — a guard must watch the resource that actually blocks the action.** The heal
existed to answer "the team can no longer fight", but it only measured HP. Whenever a recovery is
triggered by a threshold, enumerate EVERY resource whose exhaustion produces the same symptom (HP,
PP, balls, money, held items) and gate on all of them. A gate on a proxy resource is a gate that
fails in exactly the cases the proxy misses.

**Prevention rule — a user's stated cause is a HYPOTHESIS about a correlated event.** They saw a
rare thing (a shiny) next to a bad outcome and connected them; the shiny was simply the most
memorable moment in a run that was already dead. Reproduce the reported cause and CHECK IT WORKS
before fixing it: here, confirming the shiny path was healthy took one grep and redirected the
entire investigation. Never let the report choose the fix.

**Also (a repeat, and cheap):** the new repro printed `‼` and crashed on the cp1252 console —
destroying the output of a test that had already passed. `sys.stdout.reconfigure(...)` was in the
other repros and not this one. The 2026-07-25 rule said fix the CLASS not the instance; the class
here is "every tools/story-dev script that prints non-ASCII", and this one was missed.

## 2026-07-26 — My validation harness could not have caught the bug I was validating against

**Symptom.** Having found the out-of-PP livelock in the user's log via the outcome tally
(3,011 RanAway vs 5 Won), I ran the same tally over my own five-run batch `20260726-052205` to see
whether it had been silently paying that cost too. Every run returned **zero** battle outcomes.

**Not because the runs were clean.** `story_harness.py` never logged an outcome — only
`battle_is_active -> False`. The `[BATTLE] ended (outcome=...)` lines live in the GUI's
`debug_logger`, which batch runs don't use. Five full cold starts, ~2.5M frames each, and the
single metric that exposes "the bot flees everything and gains nothing" was not being recorded.

**Why that is worse than a missed bug.** I had reviewed that batch and declared the fixes
validated. That review could not have detected this failure class at all, and I did not know it —
the batch report looked complete. An unmeasured dimension reads exactly like a healthy one.

**Prevention rule:** when a real incident is diagnosed by some signal, immediately check whether
your OWN test harness records that signal — and if not, add it before moving on. The diagnostic
that caught a bug in production is, by definition, one your validation was missing. Cheap test:
run the new diagnostic over old artifacts; if it returns nothing, ask whether that means "clean" or
"never recorded" before believing it.

**This is the second measurement blind spot in two days** (the whiteout metric read 0 for every
batch ever run, 2026-07-25). Same shape both times: a number never cross-checked against a raw
count from the same logs. Any metric that has never been validated against ground truth should be
assumed broken until it is.

## 2026-07-26 — I re-derived a documented fact by probe, hours after quoting half of it myself

**Symptom.** Spent a full two-way probe cycle (three harness runs, a new driver, ~30 minutes of
emulation) discovering that Route 112's lower section cannot path back to Lavaridge, and that
Jagged Pass is internally one-way. **Both were already recorded on 2026-07-23**, in
03-PUNCH-LIST and 04-HANDOFF:

> "LAVARIDGE HAS NO REACHABLE TRAINING GRASS (two-way sweep 2026-07-23,
>  `jaggedgrass_probe.py`): Jagged Pass cannot be re-entered from the town (one-way ledges)
>  and **Route 112's lower grass has no return path**."

**The damning part.** Earlier the SAME session wrote, into the punch list, *"FIERY_PATH is the
better target (on the Ch10 route, traversable both ways, **unlike Jagged Pass's one-way ledges**)"*
— i.e. I quoted half the finding while contradicting the other half, then spent the afternoon
proving the half I had contradicted. Reading a fact, and even restating it, did not make me apply
it.

**Root cause — the knowledge was in the wrong PLACE, not missing.** It lived in prose, in
narrative documents, while the decision it constrains ("is this a usable training ground?") is made
in `modules/story/training_areas.py`. Nobody reads the handoff while picking a tile; they read the
table. Prose adjacent to a decision is not the same as prose *in* the decision.

**Fix — make it enforceable, not just recorded (user directive).** `NO_RETURN_GROUNDS` now lives in
`training_areas.py` with the measured evidence and date per entry, and BOTH pickers
(`best_training_grass`, `best_training_area`) refuse those maps *before* the reachability
predicate runs — because these grounds ARE reachable, which is exactly what makes them dangerous;
`allow=`/`region_reach` answer "can I get there", and the failure is the RETURN leg.
`repro_no_return_grounds.py` pins it, including that every entry cites evidence and a date (that
assertion immediately caught an entry of mine that cited neither).

**Prevention rule:** before probing whether somewhere is reachable/usable, grep the CODE that makes
that decision — `training_areas.py`, `region_reach.KNOWN_GATES`, `_CAVE_EXITS` — for the map name,
not just the docs. If a hard-won fact is not represented where the decision happens, it WILL be
re-derived; move it there and add the assertion, in the same change that discovers it.

**Second prevention rule:** the same knowledge is worth carrying in code as data + a test even when
it feels like "just a note". Cost of this lesson: ~30 minutes of emulation to relearn one sentence
written three days earlier.

## 2026-07-26 — An assertion that also passes when the process dies early proves nothing

**Symptom.** My lane-spawn test reported `ok  P1: argparse accepted the tile flags` for all four
lanes. It had not. The lanes died at `pokebot.py:166` in `load_plugins()` — **before**
`parse_arguments()` was ever called — because `plugins/gamepad_plugin.py` imports
`modules.gamepad`, which imports `modules.libmgba`, which imports the absent `mgba`.

**Root cause.** The assertion was written as the ABSENCE of a failure string:
`check("unrecognized arguments" not in text, ...)`. That string is missing from a process that
crashed during import, from a process that never started, and from an empty file. A negative
assertion over a log passes for every reason including "the code under test never ran".

**The fix that worked.** Assert on POSITIVE evidence the code path actually executed, and test the
seam directly instead of through a process that cannot boot: `test_tile_child.py` drives
`PokebotTileChild._on_frame` against a fake `context.emulator` with `mgba` stubbed into
`sys.modules`, and checks the frame ARRIVED in shared memory with the right pixels, sequence and
status. The spawn test now only claims what it can see (profiles, `story.yml`, stdout filenames,
bounded restart, clean teardown) and prints how far each lane actually got.

**Why this is the same shape as 2026-07-26's "my validation harness could not have caught the bug
I was validating against".** Both are a harness reporting green over a path it never exercised.
That is worse than a failing test, because it converts "untested" into "verified" in the record.

**Prevention rule.** An assertion must fail if the code under test never runs. Never assert that a
log LACKS an error string — assert that it CONTAINS the positive evidence of the thing you claim
happened, and if the environment cannot run that path, say so instead of asserting around it.

## 2026-07-26 — I built a truncation fallback that would have discarded data silently

**Symptom.** None yet — caught by a test before it ever ran. Worth recording because the
shape is one this project keeps paying for.

**Root cause.** `TileBridge.publish()` guards against an oversized status blob by falling
back to a minimal one:

    if len(blob) > STATUS_BYTES - 1:
        blob = json.dumps({"message": ...})   # drop everything else

I sized `STATUS_BYTES` at 1 KiB when the blob held a message and a counter. When the party
strip started following the focused lane, the blob grew to carry six Pokémon with moves and
IVs — **2,385 bytes measured**. Every party would have silently become the fallback: no
exception, no warning, just an empty party strip that looks like "the lane has no Pokémon
yet". The identical failure mode as the whiteout counter that read 0 for every run of every
batch, and as the endless-mode video pin.

**The fix that worked.** Raise the cap to 8 KiB with headroom, and — more importantly — a
test that asserts a REALISTIC worst case fits (`repro_x4_party.py`: a full six-mon
end-game team with moves, IVs, a long message and a log path, printed with its measured
size so the margin is visible rather than assumed).

**Prevention rule.** A fallback that discards data must either be observable (log it, or
surface it in the UI) or be provably unreachable by a test that measures the real worst
case. A silent `if too_big: send_less` is a data-loss bug waiting for the payload to grow.

## 2026-07-26 — A "did we produce anything?" check that passed on the wrong kind of content

**Symptom.** Caught by a test during development. `x4_logs.collect()` guarded against an
empty bundle with `if not plan: fail`. But `plan` also contains `badge-log.json`, which is
deliberately never archived and is therefore present on EVERY collection. So a second
collection with no new runs produced a perfectly valid zip containing four badge files and
zero logs — a bundle that looks exactly like run data, that you would attach and send off
believing it held four lanes' worth of runs.

**Root cause.** The completeness check tested for NON-EMPTINESS when the requirement was
about a specific KIND of content. Those coincide only while every item in the collection is
of the same kind; the moment a "keep this one" exception was added, the check silently
stopped meaning what it was written to mean — and nothing failed.

**The fix that worked.** Require at least one item of the kind that matters
(`any(archivable for ...)`) and fail with a message that says what to do about it: "no new
per-run logs were found — every lane's logs are already archived in its debug-logs/Old/
folder." Test asserts the failure, not just the success path.

**Prevention rule.** When a collection gains an exception ("all of these, except that one
is handled differently"), re-read every count, length and emptiness check over it — each
one is now potentially measuring a different set than it was written for. Same family as
the 1 KiB status blob: the guard did not change, the data did.

## 2026-07-26 — I built a four-lane sampler without ever checking that the lanes were independent

**Symptom.** ENDLESS LOOP x4 was designed, built, tested and shipped on one premise: four
lanes = four independent runs = four times the failure data. The user then noticed "P4 is a
copy of P3". P4's config was fine — but the question behind the report had never been asked
by me, and the answer was that **no two lanes were independent**. Emerald's `gRngValue` is
0 at every hard reset and is not RTC-seeded (Ruby is; Emerald inherited FireRed's
`main.c`), so instances fed the same frame-aligned script produce a bit-identical game.
Four lanes were closer to one sample than four. Worse, since the endless mode hard-resets
between runs, every RUN of a lane replayed the same early game too.

**Root cause.** "Independent" was doing enormous load-bearing work in the design — it was
the entire justification for the feature — and I never verified it. I checked the things
that were easy to check from our own code (config, profiles, process isolation, that
`random.choice` re-rolls) and mistook that for having checked independence. Process
isolation is not statistical independence: four isolated processes running the same
deterministic program on the same deterministic emulator produce the same answer.

**The fix that worked.** Read the decomp (`src/random.c`, `src/main.c`,
`src/naming_screen.c`, `include/config.h`) instead of reasoning about it, which located the
single controllable input to the seed — the cycles between naming-screen open and
name-confirm — and a 0-120 frame random pause there decorrelates lanes AND runs. Cost: up
to two seconds per run.

**Second-order lesson from the same hour.** The test I first wrote for it asserted that the
reachable seeds were "at least 1000 apart" — a threshold I invented rather than derived.
Seed DISTANCE is not the property that matters for an LCG; distinctness and stream
divergence are. The assertion failed (the real minimum is 192, a multiple of the 64-step
lattice) and the honest fix was to test the streams, not the seeds.

**Prevention rules.**
1. When a feature's value rests on a property like independence, randomness or freshness,
   VERIFY THAT PROPERTY FIRST — before building the thing that multiplies it. A fan-out
   built on an unchecked premise multiplies the cost, not the information.
2. Do not generalise a Gen-3 behaviour across Gen-3. Emerald, Ruby and FireRed differ here
   in exactly the way that would have made a from-memory answer wrong.
3. An assertion threshold must be derived from the mechanism, not chosen because it sounds
   demanding.

## 2026-07-26 — I named the wrong 8th gym leader, in a table I wrote from memory an hour after writing a rule against exactly that

**Symptom.** `modules/badge_log.py`'s badge table shipped with **Wallace** as the Sootopolis
Gym Leader. In Emerald the leader is **JUAN**; Wallace is the Champion
(`src/data/trainers.h:3268-3278` vs `:4024-4034`;
`data/maps/CaveOfOrigin_B1F/scripts.inc:65-69` has Wallace say it himself). Wallace IS the
Sootopolis leader — in Ruby/Sapphire. Any `badge-log.json` record written before the fix
carries the wrong `leader` string for BADGE08.

**Root cause.** I treated the leader roster as "flavour text for a tooltip" rather than as a
game fact, and typed it out while focused on the recorder's logic. The project's standing
rule — never write game facts from memory, verify against the decomp — was in my head for
the RNG question thirty minutes earlier and simply did not fire for a list of names that
felt like common knowledge.

**Why it is the SAME mistake as the RNG one.** Both are Gen-3 facts that differ BETWEEN
Gen-3 games (Emerald is RTC-unseeded where Ruby is; Emerald's 8th leader is Juan where
Ruby's is Wallace). Confidence about "Gen 3" is worth nothing at the exact points where the
games diverge, and those points are where a from-memory answer is most likely to be wrong
AND least likely to feel uncertain.

**The fix that worked.** One canonical decomp-verified table in `modules/badge_case.py`,
with `badge_log` deriving from it; every field carries its evidence. The table was left
EMPTY while verification was in flight, so `repro_badge_case.py`'s integrity assertions
failed loudly instead of the UI shipping invented data — the empty-table-plus-failing-test
is what made "unverified" impossible to forget.

**Prevention rule.** A game fact is a game fact whether it drives pathfinding or a tooltip;
tooltips get the same verification gate as flags and coordinates. When a table of such facts
is needed before it can be verified, ship it EMPTY with a failing test rather than filled
with a plausible guess — the difference between those two states must be visible in a test
run, not only in an intention.

## 2026-07-26 — My badge recorder trusted a single memory read, and invented 20 badges that were never earned

**Symptom.** The user's first x4 bundle: P1 started exactly one run and its `badge-log.json`
claimed **Stone ×10, Knuckle ×5, and a Balance badge** — the 5th badge, in a run that
reached the 2nd. Across four lanes roughly two thirds of all badge records were fictional.

**Root cause.** Badge flags live in the save block, and during a map warp save-block reads
return garbage for a frame or two. My poll sampled a flag ONCE and treated any 0→1
transition as a win. The evidence was sitting in the same log the whole time — the MAP
readout flips to a nonsense group and back in the identical window:

    f1190097 [MAP] MAUVILLE CITY(0,2) -> MAUVILLE CITY(10,5)
    f1190101 [MAP] MAUVILLE CITY(10,5) -> MAUVILLE CITY(0,2)

**What I actually got wrong.** Not the polling — the epistemics. I wrote a recorder whose
entire job is to assert "this happened", and gave it no way to distinguish a fact from a
glitch. Worse, I had already written the invariant that would have caught it: I put the gym
order in the badge table an hour earlier and never used it to sanity-check a reading. A
Balance badge with no Dynamo or Heat is impossible, and the data said so on the first run.

**The fix that worked.** Three independent filters, any one of which would have killed most
of these: debounce over two consecutive polls; once-per-run de-duplication; and a gym-order
check. Plus an authoritative run boundary from the mode itself, because the frame-counter
heuristic I relied on for run grouping had silently never fired.

**A fourth bug fell out of testing the fix:** a badge rejected by the order filter was
absorbed into the "already seen" set and could never be recorded afterwards, even when its
predecessors legitimately arrived. Rejecting a reading and remembering it are different
things and must not share a set.

**Prevention rules.**
1. A single memory read is a sample, not a fact. Anything that WRITES A PERMANENT RECORD
   from emulator memory must debounce, and must be idempotent over the event it claims.
2. If the domain has an invariant that makes a reading impossible, ENCODE IT AS A FILTER at
   the point of capture — not merely as a comment in a table. I had the invariant and
   still shipped the data.
3. When a "seen" set gates writes, check whether every path that adds to it actually means
   "handled". A rejection is not a handling.

## 2026-07-26 — I predicted this exact crash, reasoned it away, and shipped it anyway

**Symptom.** The first launch after the first successful x4 log collection died before the
profile screen: `Could not load ...\profiles\x4 LOGS\metadata.yml, file does not exist.`

**Root cause.** `list_available_profiles()` guards with `except RuntimeError`, but the
missing-metadata path raises `CriticalFileMissing`, a PrettyException. Any non-profile
directory under `profiles/` is therefore fatal at startup.

**What makes this worth recording is not the bug — it is that I SAW IT COMING.** When
choosing where to write the bundles I wrote, in `modules/x4_logs.py`:

    Inside `profiles/` because that is where the user asked for it; it has no
    `metadata.yml`, so `list_available_profiles()` skips it rather than listing a
    broken profile.

I had the right question, went looking, found the `except RuntimeError`, and concluded it
was handled — **without checking what `load_profile` actually raises.** I read the handler
and inferred the exception rather than reading the exception. Then I wrote the conclusion
into a docstring, where it became a load-bearing claim that no test ever touched.

**The fix that worked.** Skip non-directories and directories without `metadata.yml` before
loading, so enumeration is tolerant while by-name loading keeps its helpful error. Plus
`repro_profiles_stray_dir.py`, which asserts against the real failure rather than the
reasoning about it.

**Prevention rules.**
1. When you write "X is safe because Y handles it", the claim needs the same verification
   as a game fact — go and read what actually gets raised/returned, do not infer it from
   the handler. A confident comment is the most durable way to hide a bug.
2. If a design note in a docstring can be expressed as a test, write the test. This one was
   one `mkdir` away from being caught before it shipped.

## 2026-07-26 — Swap-training left the WEAKEST mon leading, and it cost one lane 44 whiteouts

**Symptom.** Batch `20260726-201838`, lane P2: **19 losses and 44 whiteouts**, every single
one at the same tile — ROUTE 110 (34,56) — with an identical party each time:

    party=['Dustox:L13', 'Nincada:L12', 'Marshtomp:L21', 'Poochyena:L11']
    [BATTLE] ended (outcome=BattleOutcome.Lost)
    [MAP] ROUTE 110(0,25) -> SLATEPORT CITY(0,1)     <- whiteout, respawn, walk back, repeat

**Root cause.** `train_team` rotates the LOWEST-level trainee into slot 0 on purpose, so it
shares XP (swap-training). Nothing ever put the good mon back. The bot therefore left every
grind with its weakest battler leading and opened the next trainer ambush with it — a L13
Dustox in front of a L21 Marshtomp.

**Why nothing caught it.** Three separate safety nets all had a reason not to apply:
- `_lead_strongest_battler()` existed and its docstring described this exact hazard — but it
  was only ever called before GYMS, never before travel.
- Survival mode (`#24-whiteout`) is deliberately scoped to WILD battles, because a trainer
  battle cannot be fled. P2's killer was a trainer.
- `_defeat_counts` escalation is boss-scoped; a route trainer is not a boss.

So the failure sat exactly in the gap between three mechanisms that each correctly declined
to handle it.

**The fix that worked.** Call `_lead_strongest_battler()` at the end of `train_team`, after
the loop and before the `finally` (a `yield` inside `finally` raises if the generator is
being closed, and on the exception path the run derails and resets anyway).

**Prevention rule.** When a routine deliberately puts the system into a WORSE state as part
of doing its job — a weak lead, a disabled guard, a raised limit — the restore belongs in
the same function, not in whichever caller happens to remember. And when you write a helper
whose docstring names a hazard, grep for every path that hazard can reach, not just the one
you were looking at.

---

## 2026-07-26 — A comment asserted a lifetime the code never enforced, and it silently killed 27 of 37 runs

**Symptom.** The user's x4 bundle `20260726-231412` looked, on its face, like the best batch
yet: P1 reported 16 of 20 runs "finished". Every one of those 16 was dead. In all three lanes
that got that far, **runs 1-3 played normally and every run from #4 onward died at the same
story beat** — the Rustboro rival — having earned only the Stone Badge. P1 run 8's debug log
is the tell: **zero `BattleOutcome.Lost` in the entire run**, yet it ends

    Story: couldn't beat the Rustboro rival in 3 tries ... handing to manual

It never fought. It couldn't.

**Root cause.** `StoryEndlessResetMode.run()` loops `yield from super().run()` **on the same
mode object**, so `StoryMode.__init__` runs once per BATCH, not once per run. Every per-run
counter lived in `__init__` — under a comment that stated the opposite in as many words:

    # Instance state, not module state, so ENDLESS RESET's next run starts with a clean slate.

`_rival_attempts` (cap `RIVAL_MAX_ATTEMPTS = 3`) therefore accumulated across the batch, and
because it increments on *entry* rather than per loss, three completed runs exhausted it
forever. `_defeat_counts` leaked the same way, so boss give-up thresholds fired on borrowed
losses — measured across run boundaries: MT_CHIMNEY `#7`→`#8`, FORTREE_GYM `#8`→`#9`, and P4
run 2 derailing as "6 losses" to Wattson after **three** real losses.

**The second bug, which is why nobody noticed the first.** `outcome` defaulted to
`"finished"` and only a raised `BotModeError` changed it — but a derail can instead call
`context.set_manual_mode()` and return normally. Every such exit was reported as a SUCCESS,
some as `finished (0 frames)`. The instrument built to *measure* failure was reporting the
failures as wins, which is worse than no instrument.

**What I got wrong on the way.** I first reported this as "the lead-restore fix did not hold",
because the loss tiles matched the previous batch's signature exactly — ROUTE 110 (34,56),
weak lead, strong mon benched. That was pattern-matching, not diagnosis. Reading
`_lead_best_matchup` showed it reproduces every observed lead exactly from its own rules
(purely defensive: `min(incoming_multiplier, -level)`), and that it runs *after* `train_team`
and overrides it. The old fix was intact; a different mechanism produced a similar-looking
symptom. **A matching signature is a hypothesis, not a diagnosis.**

**The fix that worked.** Extract `StoryMode.reset_per_run_state()` holding every per-run
counter, and call it from the endless loop at the top of each run. Add a `try/except/else`
so a run that handed itself to Manual reports `stopped:` instead of `finished`. Proven by
`repro_endless_per_run_state.py`: FAILs on HEAD, PASSes on the fix, and simulates the batch
lifecycle to reproduce the exact observed boundary (rival fought on runs `[1,2,3]` under the
old lifetime, `[1..8]` under the new).

**A trap I nearly shipped inside the fix.** Making `outcome` honest by asking "did we end
up in Manual?" would have relabelled GENUINE completions as failures: the end-of-built-content
return calls `set_manual_mode()` and returns normally too, exactly like a give-up. P2 run 1 of
this very bundle reached the Feather Badge that way and was a true `finished`. Caught by
checking every `set_manual_mode()` call site before committing, not by a test. `StoryMode` now
sets an explicit `_reached_end_of_content` flag, cleared per run.
**Corollary rule:** when you make a success signal stricter, enumerate every path that legitimately
produces the success FIRST — a fix that turns false positives into false negatives is not a fix.

**Prevention rules.**
1. **A comment claiming an object's lifetime is not a mechanism that enforces it.** Per-run
   state goes in an explicitly named `reset_per_run_state()` that the run boundary calls —
   never in `__init__` with a note hoping `__init__` is the boundary. If you write "so X
   starts clean", go find the line that makes it clean.
2. **A default outcome must be the FAILURE, not the success.** `outcome = "finished"` before
   a `try` means every unmodelled exit path silently reports success. Start pessimistic and
   let only a proven completion set it.
3. When a counter is a per-attempt BUDGET, increment it where the attempt is *spent*, and
   reset it where the budget is *renewed* — both, in the same review.

---

## 2026-07-26 — I "fixed" a double-count with a test that could never fire, and shipped it

**Symptom.** `run_index` in `badge-log.json` still advanced by two per run (P1: 1, 3, 5 … 37
across 19 runs) *after* a fix specifically for that, which had shipped with a long comment
explaining why it worked and listing two rejected alternatives.

**Root cause.** The fix deduped on ADJACENCY — "if a reset already happened and no poll has
occurred since, it's the same boundary" (`_run_index and _last_poll_frame < 0`). But the two
callers are never adjacent. The mode signals at the top of its loop, *before*
`super().run()`, and the emulator hard reset that triggers `main.py`'s detection happens
*inside* that call. Thousands of polls separate them, so `_last_poll_frame` is always a real
frame by the time the second call lands and the guard can never fire.

**The fix that worked.** Dedupe by OWNERSHIP instead: `reset_for_new_run(..., authoritative=
True)` lets a mode that knows its own run boundaries switch off main.py's heuristic for the
rest of the process. The adjacency guard was KEPT for the non-authoritative path, where it
is genuinely correct — dropping it broke `repro_badge_transient.py`, which had encoded that
contract. The regression sweep caught it; a targeted re-run of only the new repro would not
have.

**A second thing I got wrong.** My first version of the new repro asserted the old strategy
reproduced the literal observed value 37. It yields 38 under any interleaving I could
justify, and the exact ordering that produced 37 is not observable from the logs. Asserting
a number reverse-engineered until it matched would have been a fake proof dressed as a
rigorous one; the repro now asserts the *shape* (~2 per run vs exactly 1) and says why.

**Prevention rules.**
1. **A dedupe guard must be tested against the real call ORDER, not a plausible one.** Write
   the interleaving down explicitly — who calls, in what order, with what in between — before
   choosing the predicate. "No poll between" was a guess about ordering, never checked.
2. **Never tune an assertion until it matches an observed number you cannot derive.** Assert
   the property you can defend, and write down what you could not determine.
3. Always run the FULL repro sweep before claiming a fix is clean — a fix that satisfies its
   own new repro can still break the contract an older one encodes.

---

## 2026-07-27 — The failsafe against runaway runs was checked only AFTER the run returned, so it could describe a hang but never stop one

**Symptom.** In the user's bundle `20260727-063751`, three of four lanes each spent most of
the night inside a SINGLE run, and the batch lost roughly 16 of its 29 lane-hours:

    P3 run 1   30.4M frames, ~7.3 h   HARD HUNG at the Weather Institute
    P1 run 7   19.9M frames, ~5.5 h   spinning Route 103 / healing at Oldale, forever
    P2 run 35  13.4M frames, ~3.8 h   the same on Route 116

P3 is the clearest: from f3.2M to f30.4M the log contains nothing but identical heartbeats —
`state=3 controllable=False`, position frozen at ROUTE 119(32,1) (10, 10) — and **not one
STUCK dump in 27 million frames**.

**Root cause.** `MAX_FRAMES_PER_RUN` was evaluated after `yield from super().run()` returned.
A run that never returns never reaches the check. The constant's own docstring promised
exactly the protection it did not provide — *"so a run that neither finishes nor raises
cannot hold the batch forever — StoryMode's global watchdog normally catches that, but not
if the watchdog itself is what wedged"* — and the second clause is precisely what happened:
no STUCK dumps means the watchdog was the thing that wedged. P4 run 12 shows the other half
of the same flaw: it DID report `frame-cap (7,545,828 > 3,500,000)`, after burning more than
twice the cap.

**Why the progress detectors could not help.** P1 and P2 were LIVELOCKS, not hangs — real
encounters, real battles, real healing trips, just no story progress. Any "nothing has
happened for N frames" detector is blind to them by construction. Only a budget catches a
loop that is genuinely busy.

**The fix that worked.** `_run_with_frame_budget()` drives the story generator by hand and
checks the elapsed frame count every 2048 yields, raising `BotModeError` when the budget is
exhausted — which lands in the existing `except BotModeError` and is recorded as a normal
derail. Two details that matter: the framework advances bot modes with a bare `next()`, so
stepping by hand loses no `send()` values; and the check re-bases when the counter goes
BACKWARDS, because the hard reset happens inside the run and `get_frame_count()` restarts
with the emulator — measuring `now - start_frame` would go negative and silently disable the
budget, which is the same trap that made the old post-hoc check unenforceable.

**Prevention rules.**
1. **A limit that is only checked after the work completes is not a limit, it is a report.**
   Any bound meant to stop a runaway must be evaluated from INSIDE the thing it bounds.
2. **Watchdogs need a watchdog that cannot share their failure mode.** A "no progress"
   detector cannot catch a busy livelock, and cannot catch a hang if the detector is what
   hung. Pair every progress-based guard with a blunt resource budget.
3. When a docstring promises a guarantee, test the guarantee, not the code path you
   happened to write. This one had been asserted in prose through at least two reviews.

---

## 2026-07-27 — The docs described a two-folder project; the code has been three folders for ten days

**Symptom.** `02-ARCHITECTURE.md`'s folder map ended at `custom-pokebot/` and its run
instructions said `cd custom-pokebot`. `01-VISION-AND-DESIGN.md` said the project "**Enhances**
the bot in `custom-pokebot/`" and gave that copy the only fork intent-section. Meanwhile every
line of work since 2026-07-18 has happened in **`sandbox-pokebot/`**, which appeared in neither
document — and `02`'s own prose referenced `modules/battle_fault.py` and `modules/endless_x4.py`
as live features, both of which exist ONLY in the sandbox. The architecture doc contradicted
itself on the same page.

**Consequence.** An agent following the documented instructions `cd`s into a tree where
`endless_x4`, `tile_bridge`, `badge_log` and `battle_fault` do not exist, and where
`story_mode.py` is ~400 lines behind. `01` is designated by `CLAUDE.md` as "the source of truth
for what this program is FOR", so the wrong location sat in the highest-trust document.

**Root cause.** The sandbox was introduced by a user directive on 2026-07-18 and correctly
recorded in `CLAUDE.md` §"Sandbox area" — but the Definition of Done's "update 01/02" step was
satisfied for each FEATURE built in the sandbox without anyone re-reading whether 01/02 still
described the project's SHAPE. Per-item doc updates do not catch structural drift, because no
single item is about the structure.

**The fix that worked.** Rewrote `02`'s map to show all three copies plus `tools/`,
`PROJECT KIT/`, `REMOTE START/` and `cloud-backups/`; added a "Which copy am I in?" table;
gave `sandbox-pokebot/` a full intent section in `01`; and put copy prefixes on every
component heading that named a bare path.

**Prevention rules.**
1. **A per-item docs checklist never catches structural drift.** When a directive changes the
   project's SHAPE (a new copy, a new top-level dir, a moved entry point), that is its own work
   item with its own 01/02 update — not a side effect of the next feature.
2. **Never write a bare path in a multi-copy repo.** `modules/story/early_game.py` is ambiguous
   across three trees that all contain it and have diverged. Always prefix the copy.
3. If a doc's prose references something its own structural map omits, the map is stale —
   that self-contradiction is the cheapest possible detector, and it sat unread for days.

---

## 2026-07-27 — Two of four verification agents returned confidently wrong grep counts

**Symptom.** During a read-only documentation audit, one agent reported that `CLAUDE.md` has
"**zero** occurrences of sandbox" and that `02-ARCHITECTURE.md` also had zero, including in its
folder map. Both were used to argue that `sandbox-pokebot/` was undocumented everywhere.

**What was actually true.** `CLAUDE.md` contains an entire §"Sandbox area" user directive at
line 185, and `02-ARCHITECTURE.md` contained two occurrences. The *structural* finding the
agent was arguing for — that the folder MAP omits sandbox — was correct and worth acting on.
The supporting counts were not.

**Why it mattered.** Those counts were about to be written into `01`/`02` as justification
prose ("mentioned nowhere, including CLAUDE.md"). That would have put a checkable falsehood
into the source-of-truth documents, in a pass whose entire purpose was removing falsehoods.

**How it was caught.** The claim contradicted something already visible in context — the
session had `CLAUDE.md` loaded and it plainly contains the directive. One `grep -in sandbox
CLAUDE.md` settled it in seconds.

**The calibration to keep.** Across the four agents, **file-existence and line-reference
findings were reliable** (`custom-pokebot/modules/endless_x4.py` really is absent;
`requirements.py:7` really does say 3.13; `story_mode.py:553` really does call
`region_reach.is_map_reachable`). **Occurrence-COUNT claims were not.**

**Prevention rule.** Re-run any agent claim of the form "X appears zero/N times" before
depending on it — it is one command. Treat "does X exist at line N" as trustworthy. And never
let an audit meant to remove wrong facts introduce one: verify the load-bearing claims of the
verification itself.

---

## 2026-07-29 — I grouped a per-process counter across days and manufactured a badge-recorder regression

**Symptom.** Reviewing five bundles, the badge sanity check came back catastrophic: **every
lane, nearly every run** showed duplicated and out-of-order badges —
`['Stone','Knuckle','Stone','Knuckle','Dynamo','Heat','Balance','Feather','Stone',…]`. It read
as a total regression of the badge recorder, in the very batch that was supposed to validate
four fixes.

**It was my analysis, not the bot.** `run_index` **restarts at 1 for every process**. It is a
per-batch counter, not a globally unique id. I grouped a CUMULATIVE `badge-log.json` by
`run_index` over a two-day window, which merged 3–5 separate batches into one index space —
so batch A's run 3 and batch B's run 3 became a single "run 3" holding two playthroughs of
badges. The duplicates were entirely my own construction.

**How it was caught.** The pattern was too clean to be a bug: the LOW indices were all corrupt
and the HIGH indices were all pristine. A real recorder fault would not respect that boundary.
That is the shape of two sequences overlaid, not of a failure.

**The correct method** (now in `14-AGENT-PLAYBOOK.md` §2c): sort by `earned_at`, then start a
new batch wherever `run_index` does not increase. After segmenting, the same data showed one
genuine artefact — a duplicate `Stone` on run 1 of each batch (KI-30) — and nothing else.

**A second, related error in the same review.** My own "pre-fix tells" checklist in
`04-HANDOFF.md` listed `finished (0 frames)` as evidence the honest-outcome fix was absent. It
is not: that string comes from the negative-frame CLAMP, which I never removed. `start_frame`
is captured before the run and the hard reset restarts the counter mid-run, so
`now - start_frame` is negative for essentially every run after the first. It is EXPECTED
post-fix. I wrote that checklist myself, four days earlier, and it still misled me.

**Prevention rules.**
1. **Before grouping by an id, establish its SCOPE.** Per-process, per-run, per-batch and
   global ids look identical in a JSON dump. `run_index` restarting at 1 is invisible until
   you plot it. Check for non-monotonicity before using any counter as a grouping key.
2. **Corruption that respects a boundary is an artefact of your own method.** Real faults do
   not politely confine themselves to the first N records. When bad data has a clean edge,
   suspect the join before the source.
3. **A diagnostic checklist you wrote is not self-validating.** Re-derive each tell from the
   code path that emits it before trusting it — especially one you authored under time
   pressure. Two of four tells in mine were wrong or ambiguous.

---

## 2026-07-29 — A build-ready spec's threshold would have gutted 59% of real parties

**Symptom.** `21-TEAM-POLICY-DESIGN.md` §2 specifies the dead-weight test as
`level < lead_level - 8`, justified in the doc by `TRAIN_CATCHUP_GAP = 6` — the point at
which `_prepare_for_fight` stops catching a mon up, so anything further behind is
"unrecoverable by construction". The reasoning is sound and the doc was marked build-ready.

Implemented literally and replayed over the **363 real badge-moment parties** in the user's
`20260729-062040` bundle, it would have:

    boxed 3+ mons in 148 parties (41%)
    left 59% of all parties with FEWER THAN 3 mons
    cut 132 observed four-mon parties down to a SINGLE Pokémon

A one-mon party is exactly the "lone starter can't rotate" state that produced the Roxanne
party-menu hang (KI-8). Shipping this would have traded a dead-weight problem for a
strictly worse one.

**Root cause.** The threshold answers *"will this mon ever be caught up?"* — and its answer
is correct. It was then used to answer a different question: *"should this mon be boxed
now?"* In real runs the starter takes most of the XP, so by mid-game the entire bench is
10-20 levels behind. A predicate that flags "unrecoverable" therefore flags most of the team,
which is true and useless as a deposit rule.

**The fix that worked.** Split fact from decision. `dead_weight()` keeps the spec's
predicate unchanged. `rotation_plan()` caps the ACTION: `MAX_DEPOSITS_PER_ROTATION = 2`,
never below `MIN_PARTY_AFTER_ROTATION = 3`, worst-first, converging over successive heal
trips. Freeing one or two slots is all the purpose (room for an HM carrier or a counter)
actually requires. Post-cap over the same 363 parties: deposits of 0/1/2 only, and **zero**
parties left under three mons. `21-TEAM-POLICY-DESIGN.md` §2 amended with the measurement.

**Prevention rules.**
1. **"Build-ready" is not "validated".** A spec written before the data existed can be
   internally coherent and still wrong in the world. Replay any numeric rule against real
   captured state BEFORE wiring it to an action — 363 parties were sitting in the bundles
   the whole time and the check cost one script.
2. **Never let a predicate that states a FACT double as the rule that takes an ACTION.**
   "Is unrecoverable" and "box it now" are different questions; the second needs a budget,
   a floor, and an ordering. Keep them in separate functions so the action can be capped
   without weakening the diagnosis.
3. This is the third instance of the playbook's *"a numeric threshold justified by one
   worked example is a guess with arithmetic attached"* rule (after `CREDIBLE_ANSWER_POWER`
   60→75 and `FODDER_LEVEL_GAP = 12`). The pattern is now: **every constant that gates an
   action gets replayed against captured data in the same change that introduces it.**

---

## 2026-07-29 — I built an experiment whose only interface was hand-editing a source file the installer would revert

**Symptom.** To unblock the KI-31 A/B I put the new training-relocation rule behind
`FODDER_RULE`, defaulted it to the proven `"legacy"`, and told the user to run the
experiment by editing `modules/story/training_areas.py` on the batch machine. The user
pushed back: *"do I need to modify fodder_rule to perform this test? if so why did you not
do this?"*

**Three things were wrong with that handoff.**
1. **The interface was a source edit on a remote machine.** The whole reason the flag exists
   is to make the experiment cheap to run; requiring a code change on the box that runs the
   batches is the opposite of cheap.
2. **`install.py` would have REVERTED it.** Its self-healing step does
   `git checkout -- <drifted>` on tracked files that differ from HEAD — and I had just told
   the user to run `install_sandbox.py` first. The installer I recommended could silently
   undo the edit I asked for, and the batch would have run `legacy` while everyone believed
   otherwise.
3. **Nothing named the active rule in the output.** No log line recorded which rule
   produced a bundle, so even a successful flip could not have been *attributed* afterwards.
   An experiment whose independent variable is invisible in the results is not an experiment.

**What was right, and stays right:** defaulting to `"legacy"`. The governing test
(`repro_fodder_grass.py`) needs a real `mgba` and cannot run on this box, and the code
documents the early-game conservatism as deliberate. Shipping an unvalidated behaviour change
as the default would have been the worse error. The mistake was never the default — it was
making the alternative reachable only by editing source.

**The fix that worked.** `POKEBOT_FODDER_RULE=xp_rate` — an env var, immune to
`git checkout --`, needing no code change on a remote machine, and gone when the shell
closes. It normalises case/whitespace, **refuses an unknown value loudly** (a typo'd
`xprate` silently falling back to `legacy` is the single worst outcome for an A/B), and
`active_fodder_rule_banner()` prints the active rule — and how it was set — into every run
header.

**Prevention rules.**
1. **A feature flag whose only interface is editing tracked source is not a flag.** If a
   remote operator must run the experiment, the switch has to survive that machine's update
   tooling — env var, config file, or CLI argument. Check what the project's own installer
   does to working-tree drift before choosing.
2. **An experiment must name its variable in its output.** Add the banner in the same change
   that adds the flag, or the resulting data cannot be attributed to a condition.
3. **A flag that accepts an unrecognised value must fail loudly, never fall back.** A silent
   default turns a typo into a confident conclusion drawn from the wrong arm of the test.

---

## 2026-07-29 — Three times in one session I anchored a source assertion on text that also appears elsewhere

**Symptom.** Three separate repro assertions failed on their first run, all for the same
reason — a `src.index("...")` or `"x" in slice` test matched a *different* occurrence of the
same text than intended:

1. `repro_endless_per_run_state.py` anchored on `yield from super().run()`. Correct change
   routed the story through a wrapper, so the literal vanished. **Fixed** by anchoring on
   `super().run()` — which then matched the wrapper's own DOCSTRING, one line further out.
2. `repro_debug_log_header.py` asserted `"subprocess" not in body` for a function whose
   docstring EXPLAINS why subprocess is avoided; and resolved `_write_run_header()` to the
   `def` line rather than the call site, because the definition sits earlier in the file.
3. `repro_debug_emulation_config.py` sliced `class StoryMode` → `class StoryDebugMode` to
   prove StoryMode does NOT call a helper — but the helper's own *definition* sits between
   those two classes, so the slice contained its name.

None was a product bug. All three were the test lying about the product, in both directions:
(1) failed on a correct change, (3) would have passed for the wrong reason had the helper been
placed elsewhere.

**Root cause.** A source-text assertion is a proxy for a structural property. The proxy is
only valid while the text appears exactly once, in the place you mean. Docstrings, function
definitions and module-level helpers all duplicate the identifiers a test anchors on — and
this project writes long explanatory docstrings *by policy*, which makes the collision far
more likely here than in a codebase with terse comments.

**What worked.** Three rules, applied together:
- **Scope the slice to the syntactic unit** you mean (a class body ends at the next
  module-level statement, not at the next class).
- **Search from a known landmark**: `src.index(needle, i_start)` where `i_start` is the
  START line of the function under test, so a definition earlier in the file cannot match.
- **Strip docstrings** before asserting on code content (`body.split('"""')[-1]`).

**Prevention rule.** Prefer asserting the BEHAVIOUR over the source text — drive the function
and check the result, as `repro_debug_emulation_config.py` does for the config itself. Where a
structural assertion is genuinely needed (ordering, "is this wired at all"), anchor it from a
landmark inside the unit under test and strip docstrings first. And treat a source assertion
that fails on a change you believe is correct as a suspect *test*, not a suspect change —
twice out of three times here, it was.

---

## 2026-07-30 — I instrumented the VALUES but not their UNITS, and my own log made a wrong comparison look verified

**Symptom.** After adding `[FAINT-CHOOSER]` instrumentation to diagnose the KI-34 party-menu
livelock, the overnight batch produced 7,539 samples and I concluded, with confidence:

> `alive_slots` was NEVER empty (0 of 7,539) … `cursors_seen=[1]`, and that position **is in
> `alive_slots`**. The cursor is parked on a living, eligible mon.

From that I declared one hypothesis refuted and the other confirmed. **The conclusion was
unfounded.** The user, watching the screen, reported the bot was selecting *a Pokémon already on
the field* — which my data said was impossible.

**Root cause.** There are two party index spaces in a Gen-3 battle: the **regular** order from
`get_party()`, and the **in-battle party-menu** order, which diverges once mons have been
switched in and out. `BattleState.map_battle_party_index()` exists purely to convert between
them. `handle_fainted_pokemon` builds `alive_slots` from `get_party()` (regular) and reads
`cursor` from `gPartyMenu.slotId` (menu order), then compares them **directly** — while the
same function's primary path maps correctly 60 lines earlier. So "cursor ∈ alive_slots" was
comparing two different coordinate systems and was TRUE for the wrong reason.

**Why my instrumentation didn't catch it — and made it worse.** I logged both numbers, so the
data *looked* complete and self-consistent. Logging a value without its unit does not make it
verifiable; it makes a category error look like evidence. The log I added to settle the
question is precisely what convinced me of the wrong answer.

**What actually found it.** A human watching the screen for thirty seconds. No amount of the
telemetry I had chosen would have produced it, because every number in it agreed with itself.

**Prevention rules.**
1. **When two integers are compared, prove they share a coordinate system.** In this codebase
   that means: if a value came from a MENU (`gPartyMenu`, cursor positions, scroll indices) and
   another came from `get_party()`, one of them needs `map_battle_party_index()` before they
   touch. Grep for an existing mapping helper — its existence is the tell that two spaces exist.
2. **Log the UNIT, not just the value.** `cursor=1` and `alive_slots=[1,3]` should have been
   `cursor=1(menu-order)` and `alive_slots=[1,3](party-order)`; written that way, the bug is
   visible on the first line of output.
3. **A function that maps indices in one branch and not another is a bug, not a style
   inconsistency.** When adding a code path beside an existing one, check every conversion the
   original performs — the primary path here called `map_battle_party_index`; the recovery sweep
   simply never mirrored it. (Same shape as the KI-18 note: *"`choose_new_lead_after_faint`
   already performs this exclusion — the driver simply never mirrored it."* The identical
   mistake, in the identical function, one layer down.)
4. **Take a user's direct observation of the screen as primary evidence over your own
   telemetry.** They are watching the system; the telemetry is watching your model of it.

---

## 2026-07-30 — A cost model that rewards being over-levelled ranked Victory Road as the cheapest answer

**Symptom.** `counter_plan.find_counter_candidates(["Fighting"])` for a L30 team returns, in
order: Hariyama @ VICTORY_ROAD_B1F, Hariyama @ VICTORY_ROAD_1F, Makuhita @ VICTORY_ROAD_1F,
Heracross @ SAFARI_ZONE_NORTH — and only then the two Machop the bot could actually reach.
Every one of the top four is an endgame or gated interior.

**Root cause.** Cost = *frames to find* + *frames to train it to the team's level*, and the
second term is **~0 when the wild is already above the team**. So the model does not merely
tolerate deep-game encounters, it actively PREFERS them: the further into the game a wild
lives, the less training it appears to need. The ranking was introduced (2026-07-26) to fix a
real inversion — rate-ranking preferred a L6-10 Makuhita over a L20-22 Machop — and it fixed
that one while opening this one.

**Why it stayed invisible.** Phase 1 only PRINTED the ranked list. A wrong #1 in a log line
costs nothing, so nothing ever contradicted it, and the punch list recorded the opposite
belief — *"every candidate has `tile: None`; there is nothing to path to"* — which is false:
Wattson's ROUTE111 and Winona's ROUTE118 answers both carry swept tiles. **The list was never
wrong in a way anyone could see until something proposed to ACT on it.**

**The near miss.** The natural phase-2 implementation is `target = candidates[0]`. That walks
a mid-game team toward Victory Road. Reachability would not have stopped it: run live from the
Winona-era save, `_counter_area_allowed` calls Magma Hideout, Shoal Cave and the Safari Zone
**reachable**, 10/10.

**The fix that worked.** A separate `huntable` fact from an evidence whitelist
(`training_areas.hunt_ground_tile` over `TRAINING_GRASS` + the new `HUNTING_GROUNDS`), plus
`counter_plan.best_huntable()` as the only selector an executor may call. Proven offline
against the real ROM tables by `repro_counter_huntable.py`, including the sharp case: Jagged
Pass ranks ABOVE Fiery Path and is still refused.

**Prevention rule.** *A ranking answers "which is cheapest", never "may I go there". Any
planner output that gains an executor needs a separate, fail-closed permission predicate —
and check what the ranking actually returns on real data before building on it, because a list
that is only ever logged is never contradicted.*

---

## 2026-07-30 — Two sessions' worth of work was deferred to another machine over an mgba claim that was false

**Symptom.** `04-HANDOFF.md` stated, in the environment section a new agent is told to trust:
*"**No mgba here.** Anything needing a live emulator must be validated on the user's machine"*,
and elsewhere *"This dev box has no `mgba` installed … the bot has never been run here"*. Five
repros were classified "environmental" on that basis and live validation was routed to the
user's other computer.

**Root cause.** mgba is **vendored inside the repo** at `sandbox-pokebot/mgba/`, not installed
into the interpreter. The check behind the claim was almost certainly a bare `import mgba` (or
looking for `.last-requirements-check`), which fails from the repo root and succeeds the moment
`sandbox-pokebot` is on `sys.path` — which every repro does as its first action. Verified
2026-07-30: `repro_counter_wiring.py` loaded a real save state, ran frames, and read live party
and flag data on this box.

**Cost.** Every "must be validated on the user's machine" deferral written under this belief
was avoidable, and the handoff propagated it into each new session as established fact.

**Prevention rule.** *A capability claim in the handoff must record HOW it was tested, and a
negative result must be re-tested the way the code under test would do it — from the same
working directory and `sys.path` — before it is written down as an environment fact.*

---

## 2026-07-30 — "5 environmental, needs a real mgba" hid four rotted tests, one guarding live work

**Symptom.** The suite's standing expectation was *"53 pass, 0 fail, 5 environmental"*, with
four repros attributed to *"need a real mgba"*. Re-run on 2026-07-30 with
`PYTHONIOENCODING=utf-8`: **54 pass, 4 fail, 1 skip** — and every one of the four failures had
already printed `Running mGBA 0.10.2` before it died. **None of them needed an emulator it did
not have.** Confirmed pre-existing by re-running them with this session's changes stashed.

**Root cause.** Three of the four are stale scaffolding that drifted from the code under test:
`repro_boss_training`'s `SimpleNamespace` stand-in `self` never gained `_boss_plan_is_hopeless`
when the KI-23 work added that call to `_prepare_for_fight`; `repro_double_faint`'s stub mon
never gained `.level` when `level_up.py:73` started scoring on it; `repro_navigate_failfast`
asserts on the *string* `"raised BotModeError"` and now receives `UnreachableDestinationError`,
**which is a subclass of `BotModeError`** — the behaviour is correct and the assertion is not.
(The fourth, `repro_sufficiency`, may be a genuine behaviour change and is undiagnosed.)

**Why the label stuck.** "Environmental" is an explanation that predicts no observation. Once a
failure carries it, nobody reads the traceback again — and the count kept being copied forward
into the handoff as an expectation, so a green-except-the-usual-5 sweep looked healthy for
weeks while `repro_boss_training` — the guard on `_prepare_for_fight`, the exact function
`#24-counters` step 2 modifies — was dead.

**Prevention rule.** *A failing test may be excused only with the reason from its CURRENT
traceback, re-read at the time of excusing. "Environmental" is never a category — name the
missing thing, and if the run got far enough to start the emulator, it was not the emulator.*

---

## 2026-07-30 — A test stub missing a constant disabled the logic under test, SILENTLY — the second time

**Symptom.** `repro_sufficiency` case B (Torchic L14 vs Roxanne → top up to L16) returned
`None` instead of `('topup', 0, 16)`. No crash, no traceback, no warning — just a wrong
verdict, filed for weeks as "environmental, needs a real mgba".

**Root cause.** `_sufficiency_verdict`'s evolution-lookahead branch is wrapped in
`except Exception: pass`. The repro's stand-in `self` lacked `MAX_PREP_TRAINING_FRAMES` and
its stub mon lacked `total_exp`, so the frame-cost gate raised `AttributeError` **into that
swallow**, and the branch silently produced no entry. Every step of the lookahead is correct
on real data (sweep score 90 ≥ floor 80; estimate 24,361 ≤ budget 250,000). Two further
fixture faults hid behind it: the `ROXANNE` cfg had no `grass` key (the gate prices against
it), and the script created no emulator, so `get_wild_encounters_for_map` could not populate
its cache and `_wild_land_max` returned None.

**‼ This is a RECURRENCE.** `_boss_plan_is_hopeless`' own `except` block carries the comment
*"Caught once already: a stand-in `self` missing a class constant swallowed an AttributeError
and disabled the whole diagnosis. Never let it be silent again."* The production function was
hardened; **the test harness that shares the same stub pattern was not**, so the identical bug
recurred one level up — and there it was worse, because a test that silently stops testing
looks exactly like a test that passes.

**The fix that worked.** `_StoryModeStub`: harvest **every** UPPERCASE constant off
`StoryMode` (`**{k: getattr(sm.StoryMode, k) for k in dir(sm.StoryMode) if k.isupper()}`)
rather than hand-listing, and override `__getattr__` to raise an error that NAMES the missing
member and says how to supply it. Methods are bound to the real implementation
(`self.X = lambda *a: sm.StoryMode.X(self, *a)`), never re-stubbed.

**Prevention rule.** *A stand-in `self` must HARVEST the real object's constants, never
list them — and any code path wrapped in a broad `except` must be exercised by a fixture that
would fail LOUDLY if the stub drifted. When you harden a swallow in production, harden every
stub that feeds it in the same commit.*

---

## 2026-07-30 — I probed reachability with a tool that cannot cross warps, and nearly believed it

**Symptom.** `probe_counter_reachability.py`'s first run reported all five counter
destinations as unreachable, which would have meant the whole of `#24-counters` phase 2 was
inert. Three of the five errors read *"…are not on connected maps (**note that warps don't
count**)"*.

**Root cause.** I used `calculate_path`, which plans only across DIRECTLY CONNECTED maps.
FIERY_PATH is entered through a cave-door **warp**, and two of my anchors were inside
buildings (`LAVARIDGE_TOWN_GYM_1F`, `MAUVILLE_CITY_GYM`) — also warps. The tool cannot answer
"can the bot get there" **in principle**, and the executor does not use it: `counter_hunt.hunt`
calls `_navigate_riding_out` → `navigate_to_anywhere`, which crosses warps and rides out
scenes. Re-run with the real thing, Norman's Fiery Path leg **ARRIVED in 2,922 frames**.

**What saved it** was that the error message named its own limitation, and two of the five
failures had a *different* message ("Could not find a path") — the same verdict arriving by
two different routes is a signal to check the instrument, not to accept the verdict.

**What it cost, and what it bought.** Nothing was shipped wrong, and the corrected probe
paid for itself immediately: it showed the top destination is genuinely unreachable for
Wattson and Winona, which is why the destination-fallback exists at all. A probe that had
"confirmed" everything reachable would have been worse than the wrong one.

**Prevention rule.** *Probe with the SAME call the production path uses, not a lower-level
cousin — and if a negative result would kill a feature, re-derive it with the real call
before believing it. A planner that cannot cross warps cannot answer a question about a
destination behind a warp, and it says so in the error text: read it.*

---

## 2026-07-30 — I asserted a Hoenn route from memory, told the user it "plainly exists", and it does not

**Symptom.** Asked what "unreachable" meant for the counter destinations, I diagnosed the
same-region branch correctly and then wrote, to the user: *"The route plainly exists (Mauville
→ Route 112 → Fiery Path → Lavaridge → Route 113 → Fallarbor → Route 114 → Route 111 north).
Every leg is somewhere the bot has already walked."* I proposed an APPROACH GATEWAY feature
on that basis and started building it.

**It is refuted.** `probe_counter_gateway.py`, driving the real navigation from
`rocksmash_taught.ss1`: Mauville → Fallarbor PC FAIL, → Lavaridge PC FAIL, → Fiery Path
(18,19) FAIL — every one at 255 frames. The gateway idea is also structurally wrong: those
towns are all region 0, the same region as Mauville, so a gateway hop is routed by the very
branch that was failing.

**Root cause of my error.** I reasoned about Hoenn geography from recall and presented it as
established fact, in the one project whose standing directive is *"Never write a game fact
from memory — decomp or live probe only."* The measurement I already had said only
"`calculate_path` found no path"; I inflated that into a specific seven-leg route.

**What it cost, and what it bought.** No bad code shipped — the probe ran before the feature
was wired, which is the only reason. It cost the user a delay on their test and one wrong
recommendation. It bought KI-39: chasing the refutation found that the entire overworld is a
single region, so warp routing never engages for overworld→overworld travel and the bot has
**no cross-map journey planning at all** — a far more valuable finding than the gateway would
have been, and the actual blocker under `#24-dexhunt`, `#24-pc` and the team/PC-reserve plan.

**Prevention rule.** *A route, a map layout, or an "X connects to Y" claim is a GAME FACT.
Probe it before saying it — and never let a plausible route sketch turn a measurement's
"no path found" into "the path exists but the planner is dumb". Those are different claims
and only one of them was measured.*

---

## 2026-07-30 — A "clean" verdict measured on the wrong metric hid a total collapse in finish rate for a day

**Symptom.** `04-HANDOFF` recorded `d7d493d8` as live-validated: *"The last two logs … show no
unrecovered errors."* A full day of work (the whole `#24-counters` phase 2 build) was done on
top of that verdict. A controlled A/B then measured `d7d493d8` finishing **0 of 2 runs** with
**~20 global-watchdog fires per hour**, against `21b587f1`'s **48% finish rate** and **0.4
fires per hour**. The build called clean was the build where runs stopped finishing.

**Root cause of the wrong verdict.** *"No unrecovered errors"* is a statement about the
RECOVERY machinery — and the recovery machinery was working perfectly: every wedge was caught,
derailed and recovered. What it never asked was whether the run made PROGRESS. A run that
wedges, recovers, wedges again and never reaches the end of content is 100% "recovered" and 0%
useful. The handoff even carried the warning *"'No unrecovered errors' is not 'clean'"* — and
the metric still went unchallenged, because no one had written down what the alternative
metric was.

**Cost.** A day of feature work built on a broken baseline, plus a wasted A/B arm chasing my
own commits, which the same data then cleared.

**What actually found it.** Not the error counts — the **finish rate** and the
**watchdog-fires-per-hour**, both of which required normalising per hour because the two
bundles were 13 h and 3 h long.

**Prevention rule.** *State the METRIC beside every "validated" claim in the handoff, and make
at least one of them an outcome metric (runs finished per hour), never only a failure metric
(errors seen). A failure metric can be driven to zero by better recovery while the bot makes
no progress at all — and "recovered" reads exactly like "fine".*

---

## 2026-07-31 — A CLI flag that parses and then does nothing (`--endless-target` outside the tile lane)

**Symptom.** None, yet — caught while building the headless batch runner. A lane launched with
`--endless-target 0` ("run forever") would have stopped after 10 runs, and from the outside a
lane that stops is indistinguishable from a lane that died. An overnight 8-lane batch would
have silently produced ~1/3 of the sample it reported bounds for.

**Root cause.** `pokebot.py` applied `story_mode.ENDLESS_RESET_TARGET` *inside* the
`if startup_settings.tile_shm:` frontend branch. `argparse` accepted the flag for every
frontend; only one of four acted on it. The flag was added at the same time as the tile lane,
for the tile lane, and its scope was never revisited when `-hl` became a way to run the mode.

**The fix that worked.** Hoist the application out of the branch into a module-level
`apply_endless_target()` called once before the frontend dispatch — which also makes it
callable from a repro without booting an emulator.

**How it was proven.** An AST checker asking one question ("is every application of this name
nested inside a conditional on `tile_shm`?"), run against BOTH the pre-fix source (recovered
with `git show HEAD:…`) and the working tree. Same checker, verdict flips. That is a real A/B
for a structural change, and it costs no emulator.

**Prevention rule.** *When a startup flag is applied inside ONE frontend/branch, it is a bug
the day a second frontend can reach the same mode. Apply startup settings BEFORE the dispatch
that chooses a frontend — and if a flag must be branch-scoped, make the other branches reject
it loudly rather than ignore it.*

## 2026-07-31 — rich wraps a lane's stdout at 78 columns, and a summarizer over it silently reads zero

**Symptom.** Long console lines in a lane's `stdout.txt` are physically split mid-word:
`Story (DEBUG - RESET): debug logging ON -> C:\Remote \nProjects\...`. Verified in the user's
own bundle `P1-stdout-20260726-233837.txt`. Any regex spanning more than ~78 characters —
including `=== ENDLESS RESET: run N/M -> <outcome> (F frames) ===`, the line that carries
EVERY run outcome — matches nothing, and the summary reports 0 runs on a healthy batch.

**Root cause.** `rich.Console` sizes itself from the terminal; with stdout redirected to a
file there is no terminal, so it falls back to 80 columns and hard-wraps.

**The fix that worked.** Launch lanes with `COLUMNS=400` in the environment — rich reads it
(verified: `Console().width == 399`). The repro asserts a deliberately wrapped sample stays
unparseable, so if the parser is ever loosened to "fix" this the wrong way, that check fails.

**Prevention rule.** *Any subprocess whose stdout you will PARSE must be launched with
`COLUMNS` pinned wide, not just `PYTHONUNBUFFERED`. A wrapped line does not error — it reads
as an absent event, which is the failure mode hardest to notice.*

---

## 2026-07-31 — A root cause was written into the handoff as fact, and it was wrong in the direction that costs the most work

**Symptom.** KI-39 and the handoff's "WHERE WE ARE" both stated that the bot *"has NO
cross-map overworld route planning"* because *"`calculate_path` only spans directly-connected
maps"*, and concluded that building a generic BFS journey planner was **"the highest-value
item in the project"**. A session picking that up would have built one and found the
run-killer unmoved.

**Root cause of the wrong claim.** The original measurement was a table of four
`calculate_path` calls that all returned failures, and a single explanation was fitted to all
four. It never asked *why each one* failed. Two minutes of extra probing splits them into four
unrelated causes: a phantom map connection hiding a warp (the real bug), a Rock Smash rock, a
Go-Goggles gate, and an elevation/gate structure. Three of the four are not route planning.

**What actually exposed it.** Two cheap questions the original probe never asked:
1. *Are these maps even in the same connection component?* `map_path` tags every one of them
   `level=459`, and its own docstring says it "supports paths across several maps". A planner
   that could not cross maps was refuted by the source in one grep.
2. *How MANY tiles of the map are reachable, not just the one I picked?* ROUTE110 scored
   **17/125**, ROUTE111 **11/173**. Partial reachability is impossible under the stated cause,
   and it immediately localises the wall — a column-by-column sweep then put the Route 111
   choke at exactly the coordinate `early_game.py` already documents in prose, (18,101).

**Prevention rule.** *A probe that returns FAIL for every case has not found a common cause —
it has found a common symptom. Before writing one explanation into a handoff, make at least
one measurement that could DISCRIMINATE between causes (sample many targets, not one; ask the
tool what it believes, not just whether it succeeded). And a single arbitrarily-chosen probe
tile can never distinguish "this map is unreachable" from "this tile is unreachable".*

## 2026-07-31 — I predicted a hard boundary, the data showed a patchwork, and I nearly read it as a refutation

**Symptom.** The Rock-Smash-choke prediction was "reachable stops dead at ROUTE111 y=102".
The measured column came back as bands of reachable and blocked, and my probe printed the
FIRST gap (y=130), which looked nothing like the prediction.

**Root cause.** Two things were being measured at once: the choke (a hard floor) and the
corridor's **one-way ledges**, which only descend, so a northbound reachability probe is
legitimately fragmented above it. And the summary line reported the wrong boundary — the
interesting number was the LAST reachable y (102, with 101 blocked, exactly as predicted),
not the first gap.

**The fix that worked.** Read the run-length map itself instead of the summary. The prediction
was confirmed to the tile.

**Prevention rule.** *When a probe prints both raw data and a derived summary, check the raw
data before believing the summary — a summariser encodes an assumption about the shape of the
answer, and it is wrong precisely when the answer is more interesting than expected.*

## 2026-07-31 — A "did it work?" check that keyed on the wrong granularity would have made the fix look like a locked door

**Symptom.** None shipped — caught while making same-region warps plannable.
`navigate_to_anywhere` decided whether a warp had fired by comparing
`graph.region_of(arrived_map)` to `graph.region_of(leg.from_map)`.

**Root cause.** That test was only ever correct by accident: every warp the old planner could
return was cross-region by construction, because `plan()` refused same-region pairs. The
moment same-region warps became plannable, a warp that fired perfectly would leave the region
unchanged and be reported as `"Warp at ... did not trigger (locked or event-gated?)"` — the
new feature would have looked like a locked door, and the misleading error would have sent the
next investigation after event flags.

**The fix that worked.** Compare MAPS, with a coordinate fallback for in-map stairs (a warp
whose two ends share a map cannot use map identity).

**Prevention rule.** *When you widen what a planner may return, re-read every check that
validates its output. A verification written against a narrower input set encodes that
narrowness as an assumption, and it fails by declaring the new, correct cases broken.*

---

## 2026-07-31 — I hooked a recovery into the function that recovery itself calls, and made it infinite

**Symptom.** `repro_smashrock_battle_wedge.py` went from passing in under 90s to still running
at 500s, the moment `#24-smashroute`'s obstacle clearing landed. Nothing else in the sweep
moved, and the feature's own live test passed — so the only signal was one script's RUNTIME.

**Root cause.** Obstacle clearing was hooked into `early_game._navigate_riding_out`'s error
handler. But `clear_obstacle` calls `_smash_rock`, and `_smash_rock` calls
`_navigate_riding_out` to walk to the approach tile. So a clearance runs THROUGH the function
that starts clearances. If that short walk failed for any reason — an NPC in the way, a scene,
a bumped trainer — the handler searched again, found the SAME rock (its approach tile is still
reachable, that is why it was chosen), and called `clear_obstacle` one level deeper. The
`cleared_obstacles` set that bounds the outer loop is per-CALL, so every nested level started
with an empty one and nothing ever converged.

This is the project's oldest bug shape, and I walked straight into it after quoting it: *a
bounded loop re-entered by its dispatcher is still infinite* (KI-34, 23.9M frames). I had even
written a `cleared_obstacles` set specifically to bound the loop — and put it at the wrong
scope, which is worse than no bound, because it looks like one.

**The fix that worked.** A module-level `_clearing_in_progress` re-entrancy guard, set by
`clear_obstacle` and released in a `finally` (a guard stuck ON would silently disable the
feature for the rest of the run — as bad as one stuck off). `find_obstacle_on_route` returns
None while it is set. `repro_obstacle_clearing.py` §4 pins both the guard and its release
after an exception.

**Prevention rule.** *Before hooking a recovery into a function, list what the recovery calls
— transitively. If the recovery reaches the hooked function again, per-call state cannot bound
it and you need a re-entrancy guard, not a bigger counter. And when a change makes one repro
SLOWER without failing it, treat the runtime as the failure: it is what an infinite loop looks
like from outside.*

---

## 2026-07-31 — I validated a travel fix from the EASY starting position, and shipped it as done

**Symptom.** `#24-journey` and `#24-smashroute` both passed live A/B tests and both were
recorded as done. The very next batch showed the counter chain still failing to reach Fiery
Path — with a *different* error than before, from a place I had never tested.

**Root cause.** Every measurement behind both features was taken from `rocksmash_taught.ss1`,
i.e. standing in **MAUVILLE_CITY** — one map from the blocking rock, and inside the same
walkable component as most of the route. The Norman counter ladder does not fire there. It
fires at **PETALBURG_CITY**, and from Petalburg the world looks completely different:

| from Petalburg | walkable |
|---|---|
| ROUTE104 | 31/200 tiles |
| PETALBURG_WOODS | **0/132** |
| RUSTBORO_CITY | **0/150** |
| ROUTE116 | **0/125** |

`PETALBURG_WOODS` is a separate map entered by a warp, and it splits Route 104 in two — a
fact the ROM's map headers do not encode, since they describe ROUTE104 as one connected map.
So the planner believed the whole journey needed exactly ONE warp (`ROUTE112 -> FIERY_PATH`),
both candidates for it were behind that split, neither validated, and the executor stopped
with nothing to do. From Mauville that case cannot arise, so no amount of testing there would
ever have found it.

**Why the test suite did not catch it either.** The repro and the harness driver both used the
same save. A second save was the entire difference between "proven" and "unproven", and I
never asked which position the feature would actually run from.

**The fix that worked.** `_staged_progress_warp`: when nothing on a route to the goal is
reachable, take any reachable warp that does not INCREASE the map-graph distance to the
target, and re-plan. Ranked by distance, tie-broken by onward exit count — both thresholds
measured, not guessed (from Petalburg every house/gym/mart door is 9 hops against the current
8, so the distance rule alone excludes them; the Woods entrance and Mr Briney's front door are
BOTH 8, so exit count is what separates the way onward from a one-room house).

**Prevention rule.** *Validate a feature from the position it will ACTUALLY run from, and find
that position in the code (which segment/ladder invokes it) rather than reusing whichever save
was already loaded. A save chosen for convenience tests the easy case by construction — and if
one save is all the evidence there is, the claim is "it works from there", not "it works".*

## 2026-07-31 — A recovery guard budgeted EXACTLY like the watchdog is dead code, and it read as "the feature works"

**Symptom.** `global watchdog` fires rose from 5 to 72 between two batches. The handoff
explained it away as a side-effect of success — *"runs travel much further now, and long
journeys trip the no-progress watchdog, which then recovers"* — and flagged it as
uninvestigated. It was actually a hard regression that also silently cut every Poké Ball
restock from 30 balls to 10.

**Root cause.** `_navigate_when_ready` waits out a transient with
`if waited > _MAX_NON_OVERWORLD_FRAMES: break`, where that constant is 18,000 — the *same*
number as the story watchdog's stall threshold. The wrapper presses nothing and changes
nothing while it waits, so it *is* a stall by the watchdog's definition. `>=` beats `>`; the
derail always pre-empts the break. The escape hatch never executed once.

**What made it hard to see.** Recovery worked. Every one of these ended in a clean
`derail #1 → re-localise → continue`, so no run FAILED because of it — the only visible trace
was a counter going up, next to a plausible story about why success would raise it.

**How it was found.** Not by re-running anything — by asking the stored logs *where* the
fires landed. 35 of 72 were inside `RUSTBORO_CITY_MART` immediately after `bought Poké Balls`,
which is nowhere near a long journey. The A/B that settled it was already on disk: 33/33
purchases completed at baseline, 0/36 in the new build.

**Prevention rules.**
1. **A bounded wait that changes nothing while it waits must expire comfortably INSIDE the
   watchdog's stall window.** Equal budgets are not "generous", they are unreachable — the
   watchdog is guaranteed to fire first. Pinned by
   `tools/story-dev/repro_watchdog_budget_collision.py`.
2. **A rising counter next to a plausible success story is still an unexplained counter.**
   "We do more of X now, so more X-ish things happen" predicts a *proportional* rise spread
   across the work; before accepting it, check that the events actually land where X happens.
   Asking WHERE cost minutes and refuted it outright.
3. **When a metric moves, confirm the instrument reads one event once.** This canary was
   counted in both stdout and the debug log, so every headline figure was ~2× — but only for
   that canary, which is worse than a uniform error because it survives a spot check.

## 2026-08-01 — A flat funnel would have read as "the fix did nothing"; the MECHANISM counters said the opposite

**Symptom.** Batch4 was run to measure `affordable_training_target`. Every badge rung came
back flat (Heat→Balance 77% → 83%, z = 0.52; whole funnel z = 0.19). On the outcome metric
alone the honest conclusion is "the training fix bought us nothing — try something else."

**What was actually true.** The fix works perfectly. Counting the mechanism, not the outcome:
`training … rejected` went **4 → 0**, the affordable target fired **7×**, training **started
7×** — and then failed **7 of 7** because the bot could not walk from ROUTE103 to the ROUTE102
training grass (KI-44). Zero counters were ever trained, so the counter met Norman at L15-16
exactly as it had in batch3. The funnel *had* to be flat; nothing downstream had changed.

**The trap.** The blocker MOVED one step down the chain — budget → travel — and an
outcome-only reading cannot distinguish "the fix does not help" from "the fix works and the
next thing is broken". Those two conclusions lead to opposite next actions: abandon the fix,
or go fix the travel.

**Prevention rules.**
1. **Instrument the MECHANISM alongside the outcome.** For any fix, log the chain it is
   supposed to unblock — attempted / succeeded / failed — so a flat outcome can be attributed
   rather than guessed at. Three greps distinguished "didn't help" from "worked, next thing
   broke"; the funnel alone never could.
2. **A fix that removes a refusal will expose whatever the refusal was hiding.** When a gate
   stops declining work, the work starts running for the first time and its own failures
   become visible. Budget the follow-up before calling such a fix done, and do not read the
   newly-visible failure as a regression the fix caused — check whether the code path could
   even execute before.

## 2026-08-01 — "Import every module to verify the promotion" GUTTED `map_data.py` in BOTH builds

**Symptom.** After promoting sandbox → custom I wanted a stronger check than spot-importing 18
modules, so I imported every `.py` under `modules/` and `plugins/`. It reported
`imported 189, FAILED 4` — which looked like a clean result. `git status` then showed
`modules/map_data.py` **modified in both `custom-pokebot/` and `sandbox-pokebot/`**, cut from
**1,591 lines to 7**: the entire `MapRSE`/`MapFRLG` enums (518 maps) gone. Plus 19 untracked
artifacts (`*.sym`, `flags.c`, `vars.c`) downloaded/generated into both trees.

**Root cause.** Three of those modules are dev-only code generators that run at IMPORT time,
not under `if __name__ == "__main__"`: `modules/data/get_pret_maps.py` REWRITES
`modules/map_data.py` from a pret decomp checkout. The decomp is not present, so it wrote a
stub header, then died with `FileNotFoundError` — which my harness dutifully recorded as one
of "4 expected failures". **The traceback was the evidence of destruction and I read it as a
tidy skip.**

**Why it was nearly invisible.** Every real check still passed afterwards: the 18 promoted
modules imported fine, because nothing in that list imports `map_data` at module level. Had I
not run `git status`, a gutted map table would have been committed as part of a
"verified" promotion.

**The fix.** `git checkout --` on exactly those two files (they were committed seconds earlier
at `581b7bb4`, so the restore was exact), then `rm` of exactly the 19 enumerated artifacts —
targeted, not `git reset --hard` or `git clean -f`. Confirmed recovered: 1,591 lines and
`MapRSE` resolving 518 maps in **both** builds.

**Prevention rules.**
1. **Never bulk-import a package as a verification step.** Import is not a read-only
   operation — module-level code runs, and in this repo some of it writes source files. Verify
   a promotion by *parsing* (`ast.parse`, which cannot execute) plus importing the SPECIFIC
   modules the change touched.
2. **`git status` is part of every verification, not just before committing.** The check that
   caught this was not the 189/4 result; it was noticing the tree had changed. A verification
   that mutates the thing it verifies has proved nothing.
3. **An "expected failure" in a sweep still deserves its traceback read.** `FileNotFoundError`
   from a module named `get_pret_maps` was announcing that it had tried to regenerate a map
   table. I classified it as environmental noise without reading what it had already done.

## 2026-08-01 — The visible failure ("can't get there") was hiding a worse invisible one ("not worth going")

**Symptom.** KI-44: counter training failed 7 of 7 with `Could not reach (9, 2) on ROUTE102 …
not walkable from ROUTE103`. Every instinct — and the KI I had just written — said *routing
bug*, and the obvious next step was to probe the ROUTE103→OLDALE→ROUTE102 path.

**What was actually true.** The destination was wrong in the first place. `train_counter`
used `cfg["grass"]` — the **boss's** patch — so a counter caught in FIERY_PATH was sent to
Norman's Route 102. Reading the ROM's own encounter tables: **Route 102's land wilds are
L3-4**, against a L15 counter. Even a perfect journey would have bought a worthless grind.
The codebase already said so at `story_mode.py:739` ("~25 xp a kill, i.e. never") — in a
comment about a different feature, so nothing connected it to the counter chain.

**And the obvious repair was also wrong.** "Train where you caught it" picks FIERY_PATH, which
is in `NO_RETURN_GROUNDS` — reachable and exitable, but the heal leg back to Lavaridge fails.
Same for ROUTE112 and JAGGED_PASS. Had I "fixed" it that way the training loop would have
stranded the bot with no way to heal, and it would have looked like a NEW navigation bug.

**Prevention rules.**
1. **When a step fails to REACH somewhere, ask whether it should be going there at all
   before debugging the route.** A navigation error names a destination; it never says the
   destination was chosen correctly. Here the destination was chosen by boss identity when it
   should have been chosen by the trainee's level and position — one question upstream of the
   error.
2. **Before adding a new picker, check whether a vetted one already exists.** The repair was
   `best_training_area`, which already refused every no-return ground, applied a winnability
   guard and honoured reachability. Hand-rolling "train where you caught it" would have
   re-derived — badly — rules the project had already measured and written down.
3. **Assert the PROPERTY, not the answer.** `repro_counter_training_ground.py` asserts "never
   a no-return ground, at any level, even with allow=<always true>" rather than "picks
   ROUTE117", so a future edit to the training tables cannot quietly reintroduce the hole.

## 2026-08-01 — The fix worked perfectly and changed nothing, because the thing it produced was never used

**Symptom.** Batch5 was run to prove KI-44. The mechanism came back perfect: `counter
training failed` **7/7 → 2/9**, `Machop L15 -> L29` eight times, evolving to Machoke. And the
badge funnel did not move at all — Heat→Balance 83% → 79%, z = −0.33.

**What was actually happening.** The trained Machoke was **never led into the fight**. Leads
chosen for Norman in batch5: SHEDINJA ×9, MARSHTOMP ×4, SWAMPERT ×4 … MACHOKE **zero**.
`_lead_best_matchup(["Normal"])` scores `min(incoming_multiplier, -level)`, so Shedinja
(Bug/Ghost, Normal → 0×) always wins the score. The whole catch-travel-train chain ran, and
its product sat in the bag.

**‼ It was already written down.** `#24-leadpolicy` had diagnosed this and had a user ruling
(A+C) — and its entry literally predicted the run: *"P4 led Shedinja L20 vs Norman … and lost
to Slaking's Faint Attack (Dark)."* Two sessions were spent unblocking a chain whose output
a known, unbuilt item was discarding.

**Prevention rules.**
1. **When a fix produces an ARTEFACT, instrument its CONSUMPTION, not just its production.**
   "Was the counter trained?" and "did the counter fight?" are different questions, and only
   the second one can move an outcome. One grep for the chosen lead would have found this
   before the batch, not after.
2. **Before building a fix, grep the punch list for the thing it feeds.** The blocker chain
   here went budget → training ground → lead selection, and the third link was already an
   open item with a ruling. Reading the punch list forward from the fix — "what happens to
   the output?" — is cheaper than a 3-hour batch.
3. **Do not use a within-batch split as evidence of harm.** Counter-hunt runs beat Norman
   71% vs 89% for runs that never hunted — but the chain only fires on runs already losing,
   so that gap is selection bias. The honest comparison is the same subpopulation across
   batches (5/9 → 6/10, z = 0.20), which resolves nothing at n≈10. Say "cannot resolve"
   rather than reporting a direction.

## 2026-08-02 — I shipped a fix that stripped the party on every heal and cut the finish rate from 47% to 5%

**Symptom.** Batch6 (`x4-runs/20260802-160603`) finished **2 of 37 runs (5.4%)**, down from
16 of 34 (47.1%). `global watchdog` went **1 → 67**, most of them inside MAUVILLE_CITY_GYM,
and `Cutscene did not end` went 5 → 35.

**Cause — mine.** `#24-pc` piggybacked the PC rotation on **every** heal. With
`MIN_PARTY_AFTER_ROTATION = 3` the plan deposits until three mons remain, so the log reads
**`PC rotation done — party is now 3` 73 times out of 75**. The bot spent the entire batch in
a catch → deposit → catch cycle on a permanent three-mon party, then wedged in gyms it could
not win. It even deposited a **Shedinja L21** — a real battler.

**‼ `team_policy` was not wrong.** Its rule is "more than 8 levels behind the best is
unrecoverable", and an early-game party genuinely IS four low catches that far behind. The
DECISION was right every time; the **wiring** was wrong. Design §4 says "piggyback on a heal
that was happening anyway", and I read that as *every* heal — but it assumed rotation is
occasional, and every-heal makes it continuous.

**The fix.** `ROTATE_ONLY_WHEN_PARTY_AT_LEAST = 6`. The blocker this feature exists for is
exactly one condition — `resource_blocker()` refuses a counter hunt only when
`_party_count() >= 6` — so that is the only moment a slot must be freed. A four-mon party has
room already and rotating it buys nothing.

**Why the repros did not catch it.** Every check I wrote was about a SINGLE rotation in
isolation — does it pick the right mon, does it respect the floor, does it degrade safely.
All still pass. None asked *how often it would run*, and the damage was entirely in the
frequency. **A correct decision invoked at the wrong cadence is a bug the unit tests cannot
see.**

**Prevention rules.**
1. **When wiring a decision to a trigger, state the expected RATE and test it.** "Runs on
   every heal" vs "runs when the party is full" differ by ~30× here. `repro_pc_trip.py` now
   asserts that 3-, 4- and 5-mon parties are NOT rotated — a rate test, not a decision test.
2. **A feature that CONSUMES a resource must be gated on the condition that motivated it,
   not on a convenient hook.** The motivating log line said "the party is full"; the gate
   should have said `>= 6` from the start. I chose the hook (a heal) because it was
   convenient, and never re-derived the trigger from the requirement.
3. **Suspect your own newest change first when a batch collapses.** The regression was two
   commits old and the end_reasons named gyms, not the PC — it would have been easy to chase
   the gym wedges. `PC rotation done — party is now 3` × 73 was the tell, and it was one grep
   away because the feature logs what it does.

## 2026-08-03 — I removed a lead that was WINNING, on the strength of one observed loss

**Symptom.** Finish rate 47.1% (batch5) → 26.9% (batch7), and the three healthy batches before
that were 57%/60%/47% — mutually indistinguishable, so 26.9% is a real drop, not noise.

**What I did.** `#24-leadpolicy` option **(c)** demotes a 1-HP Wonder Guard mon (Shedinja) so
it never leads a boss. My entire justification was ONE observed loss recorded in the punch
list: *"P4 led Shedinja L20 vs Norman … and lost to Slaking's Faint Attack (Dark)."*

**What the logs said all along.** `BADGE:` lines only print on a **win**:

| | batch5 (no (c)) | batch7 (with (c)) |
|---|---|---|
| Shedinja appearances | 12 | 6 |
| …as a WINNING lead | **12** | **0** |
| Norman victories it led | **9 of 23 (39%)** | 0 |
| Balance Badges | 23 | 18 |

Wonder Guard makes Shedinja immune to Norman's ENTIRE Normal STAB. Faint Attack is the
exception; I generalised from it and deleted the rule.

**‼ The failure was asymmetric attention.** The loss was vivid, narrated in a punch-list entry
and easy to find. The nine wins were silent — they looked like ordinary successes. I searched
for evidence of the failure mode and found it, and never ran the one-line grep that would have
counted the successes.

**Prevention rules.**
1. **Before removing a behaviour, count how often it WINS, not just that it can lose.** One
   grep (`lead SHEDINJA` in `BADGE:` lines) was the whole answer and took seconds. A behaviour
   that appears in the logs only when it loses is not a behaviour that only loses.
2. **A punch-list entry describing a failure is a SAMPLE, not a base rate.** These entries are
   written when something goes wrong, so they are a biased sample by construction. Treat one
   as "here is a case to measure", never as "here is what usually happens".
3. **Ship a behaviour REMOVAL behind a flag.** `POKEBOT_LEAD_DEMOTE_WONDER_GUARD` now defaults
   OFF. Additions can be judged by whether they fire; removals can only be judged against what
   they replaced, so they need an A/B, not an argument.

## 2026-08-03 — A bare `except Exception` around "bookkeeping" hid a NameError for two batches

**Symptom.** `#24-leadcounter` never fired: batch7 6 of 6, batch8 `hunted_pids=0` on **all 684**
logged lead decisions.

**Cause.** The registry write was `_caught = get_party()[slot]` inside
`try/except Exception: pass` — and **`get_party` is not in `_counter_ladder`'s scope.** Every
other user in that file imports it locally. So every catch raised `NameError`, the bare except
swallowed it, and the set stayed empty. A plain typo, invisible for two batches, because I
wrapped bookkeeping in a catch-all "so it can never break the chain".

**Fix.** Import it locally, and make the except **log** rather than `pass`. Also added a
success line (`counter registered (pid=…)`), so both outcomes are visible.

**Prevention rule.** **A bare `except: pass` around code that WRITES state is a silent-failure
generator.** Guard the caller if you must, but the handler has to say something — this project
has now lost time three separate ways to failures that produced no output (KI-24's invisible
NO, the KI-31 relocation that was `console.print`-only, and this). If it is worth protecting,
it is worth logging.

## 2026-08-03 — The PC rotation deposited the counter the chain had just crossed Hoenn to fetch

**Symptom.** Batch8: 5 Machops caught, and the Norman lead candidate sets contained no counter
at all (`from SwampertL38 BeautiflyL23 RaltsL6 PoochyenaL10`).

**Cause, verbatim from one run:**
```
Story: counter hunt CAUGHT Machop (slot 5).
Story: training the counter — Machop L15 -> L29 (team is L39…).
Story: PC rotation — depositing Cascoon L5 …, Machop L17 (25 behind the team's best (L42))
```
A freshly-caught counter is ~25 levels behind the team **by construction**, so it is textbook
dead weight by `team_policy`'s level rule. `#24-pc` therefore threw it away — 2 of 5 that
batch. It also deposited **Shedinja ×2**, which the same batch showed winning 39% of Norman
fights.

**‼ Two of my own features actively fighting each other**, each correct in isolation:
`counter_hunt` fetches a low-level answer; `pc_trip` deletes low-level mons.

**Fix.** `plan_deposits` reads `_hunted_counter_pids` from the LIVE mode instance and refuses
to deposit those PIDs, logging the refusal. `team_policy` already protects the only HM
carrier for exactly this reason — a mon can be dead weight *by level* and still have a ROLE.

**Prevention rules.**
1. **When adding a feature that DELETES something, enumerate what else in the system CREATES
   that kind of thing.** A counter hunt and a dead-weight deposit are obviously in tension the
   moment they are named side by side; nothing but haste stopped me seeing it.
2. **"Dead weight" must be a judgement about ROLE, not only about level.** The level rule is a
   heuristic for role, and the exceptions (HM carrier, hunted counter, proven boss lead) are
   where the value is.

## 2026-08-04 — I removed a WINNING behaviour for the second time in a week, having already written the rule against it

**Symptom.** The badge funnel's last rung, Balance→Feather, fell from **83% / 75% / 70%**
(batch3/4/5) to **52-59%** (batch8-12), and the finish rate from a 52.8% plateau to 37.0%
(pooled z = −1.94).

**Cause.** `#24-areaitemgate`. I built it to stop **28 wasted treks per batch** — the
`ROUTE111 (25,55) is not reachable … dropping it as a training option` events — by refusing
the area unless Go-Goggles are held.

| batch | relocations to ROUTE111 | Balance→Feather |
|---|---|---|
| b3 / b4 / b5 (gate off) | 19 / 12 / **24** | 83% / 75% / 70% |
| b8…b12 (gate ON) | **0** | 52-59% |

**ROUTE111 (L19-22) is the ONLY training relocation this bot ever performs.** Its real success
rate was ~43% (24 successes against 32 failures in batch5). My gate took it to **zero**, the
team stopped being levelled for the post-Norman band, and the last rung collapsed.

‼ **THE FAILURES WERE LOGGED; THE SUCCESSES WERE SILENT.** `dropping it as a training option`
prints on failure. A successful relocation prints `relocating to ROUTE111` — and I never
grepped for it, because nothing was going wrong to make me look.

‼ **THIS IS THE SECOND TIME IN A WEEK.** The first was `#24-leadpolicy` (c), which deleted a
Shedinja lead that was winning 39% of Norman fights. After that one I wrote, in this very
file: *"Before removing a behaviour, count how often it WINS, not just that it can lose."*
I then applied that rule to the lead policy and **not** to the training gate, four days later.

**Prevention rules.**
1. **A rule written in 08-MISTAKES is not applied until it is applied to the CURRENT change.**
   Re-read the file's own prevention rules when the change under review is a REMOVAL. Both of
   these were removals dressed as fixes.
2. **Grep the positive counterpart of every failure line you are about to eliminate.** For
   `dropping it as a training option` the counterpart is `relocating to` — it was one grep
   away, in logs I already had, both times.
3. **A "wasted work" metric is not a cost metric.** 28 wasted treks looked like pure loss
   because I never priced what the same code path bought when it succeeded.

## 2026-08-05 — THIRD removal-shaped feature in a week that cost more than it saved (`#24-pc`)

**Measured.**
| batch | PC deposits | avg team size at Feather | Balance→Feather |
|---|---|---|---|
| b3 / b4 / b5 (off) | 0 | **5.65 / 5.72 / 5.81** | 83 / 75 / 70% |
| b8 (on) | 14 | **4.45** | 52% |
| b13 (on) | 18 | **4.75** | 57% |

`#24-pc` removes **about one whole team member permanently**, and the last funnel rung fell
over exactly that transition. Less depth post-Norman is less depth for Winona.

**What it bought:** the counter chain was blocked by a full party **5 times in batch5**. So the
trade was ~1 mon of depth on EVERY run to unblock 5 hunts per batch.

**The pattern, three for three this week:**
| feature | counted | never counted |
|---|---|---|
| `#24-leadpolicy` (c) | 1 Shedinja loss to Faint Attack | 12 Shedinja WINS (9 of 23 Norman victories) |
| `#24-areaitemgate` | 28 wasted treks/batch | 24 successful relocations/batch |
| `#24-pc` | 5 blocked hunts/batch | ~1 team member on every run |

All three are features that REMOVE or RESTRICT something. All three were justified by a
visible failure count with no corresponding success count. All three had the counter-evidence
sitting in logs I already had.

**Prevention rules.**
1. **A feature that removes something needs a PRICE, not a justification.** Write both numbers
   before building: what it saves per batch, and what it costs per run. `#24-pc` was "5 blocked
   hunts" vs "1 mon on every run" — a bad trade that was computable in advance.
2. **`08-MISTAKES` is not a diary, it is a checklist.** Rules 1 and 2 of the two previous
   entries would each have caught this one. Read this file's REMOVAL rules before writing a
   removal, not after measuring the damage.
3. **Team/party composition is a shared resource with no owner.** `counter_hunt` wants a free
   slot, `team_policy` wants dead weight gone, the boss prep wants depth. Three features have
   now fought over it. Any future change touching party membership must state its effect on
   the others.

## 2026-08-05 — A workaround's justifying comment outlived the limitation it named, and nearly bought a chain-threading system we already own

**Symptom.** `#24-cavethread` — the project's stated blocker for ALL story content past Winona —
was scoped as "build a multi-hop cave chain table", and was one session away from being built.

**Root cause.** `_CAVE_EXITS`/`_CAVE_ENTRANCES` (`early_game.py`, 2026-07-26) carry a long,
confident, CORRECT-WHEN-WRITTEN comment: *"The global navigator cannot cross warp levels, so ANY
target outside a cave plan-fails from within it."* **`#24-journey` fixed exactly that on
2026-07-31** — five days later, in a different file — and nobody went back to re-read the
comment that the fix invalidated. The workaround kept working (single-hop caves still thread
fine), so nothing failed loudly, and the stale justification sat there reading like a current
constraint. The punch list then inherited the stale premise and turned it into a build plan.

**What actually found it.** Not a probe — reading the call chain and noticing a DATE. The
comment said the navigator cannot cross warps; the handoff said `#24-journey` shipped warp
planning. Both could not be true. Cost to check: one offline BFS replay against the committed
ROM cache, no emulator, ~10 minutes. It showed the graph already knows all four routes, in both
directions, 3-4 hops deep.

**The fix that worked.** Re-scoped the item to MEASURE before building, and wrote the probe
(`--driver cavethread`) that drives the production call through Granite Cave — chosen because it
is the same depth as Mt. Pyre and carries the hardest hazard (a one-way ledge that makes
within-floor reachability directional).

‼ **Prevention rule: when a comment JUSTIFIES a workaround by naming a limitation, that comment
is a claim with an expiry date — check the limitation still exists before building on it.** A
workaround does not fail when its reason disappears; it just quietly becomes cost. Grep the
limitation, not the workaround. (Cheap habit: when a fix removes a limitation, grep the codebase
for comments naming it and retire them in the same commit.)

‼ **Second rule, from the same session — do not let this recon overshoot.** The BFS result
refutes "the route data is missing"; it does NOT prove the route is WALKABLE, because
`map_route`'s own docstring warns its connection edges can be phantoms. Stating both halves is
the whole discipline: KI-39 cost a day precisely by letting one measurement answer two questions.

## 2026-08-05 — I read a party's empty slots as waste. They were the runway the HM catches land on.

**Symptom.** Raising the pre-Gym-1 party fill 4 → 6 (`#24-partycap`) dropped the finish rate
from **52.0% to 15.8%** in one batch. 10 of 16 non-finishes were a failure that had never
appeared in any of the 14 preceding batches: `No party mon can learn Surf and the party is full`.

**Root cause.** Not team strength — **HM coverage**. A party pre-filled with early-route wilds
has no Surf learner and no room to catch one, and Surf is mandatory to pass the Balance→Feather
rung. The badge funnel showed every earlier rung FLAT and the entire loss on that one rung
(76% → 21%, z=3.06), which is what identified the mechanism.

**The wrong model I was operating on.** I treated `target_size = 4` as an arbitrary cap holding
teams smaller than the user wanted, and "empty slots" as unused capacity. They are neither. At
cap 4 the team still reaches a mean of **5.85** by the Feather Badge — it fills up on its own,
with the mons the run actually needs (a Surf learner, a Fighting counter). The free slots are
**scheduled capacity for catches that must happen later**. Filling them early with whatever
walks out of the grass spends a resource whose whole value is being available at a specific
future moment.

‼ **Prevention rule: before raising a limit, ask what the headroom is currently SPENT ON.** A
limit that looks arbitrary is often a reservation. Grep for what else catches, joins, or
allocates into the same pool, and check whether it happens LATER than the change — a resource
conflict that is invisible at the moment of the edit shows up several hours downstream.

‼ **Second lesson — the pre-registered rule did its job, and the funnel is why.** The handoff
had recorded, before any data existed: *"if team size rises but the finish rate falls, revert
the CAP, not the overflow."* That is exactly what happened, and having the rule written in
advance meant the revert took no argument. But note the finish rate alone would have supported
the WRONG diagnosis ("a deeper team costs more to heal and train" — plausible, pre-registered,
and false). Only the per-rung funnel showed strength was never the issue. **Keep pre-registering
the decision rule; keep reading the funnel for the CAUSE.**

‼ **Third: a coupled change can leave its partner unproven.** This batch was also meant to be
the first live proof of `#24-pcoverflow`. It logged `withdrawing` **0** times — the Surf guard
killed runs before any full-party catch reached the overflow path. **Bundling two changes into
one batch measures the bundle, not each part**; when the first one derails runs early, the
second gets no exposure at all. `#24-pcoverflow` remains unproven and needs its own probe.

## 2026-08-05 — Twice I read "the trip failed" off a final position, when the trip had SUCCEEDED and walked one map further

**Symptom.** The `#24-cavethread` probe reported `arrived=False map=GRANITE_CAVE_B1F` and I was
one edit away from writing "multi-hop threading stops one hop short" into the handoff as the
project's top blocker. The return-leg probe then reported `arrived=False map=DEWFORD_TOWN_HOUSE1`.
**Both trips had actually succeeded.**

**Root cause — mine, in the probe.** I derived destination tiles from the warp graph's
`to_coords`, reasoning that "where the ROM says you land" is walkable by construction. It is —
but it is also, always, **a warp tile**. Walking onto a warp FIRES it, so the bot reached the
target and was immediately carried one map beyond it: a B2F ladder bounced it back up to B1F, a
Dewford door put it inside a house. `navigate_to_anywhere` returned SUCCESS both times, correctly
by its own lights, and my final-position check turned that into "failed".

**The fix that worked.** Record the set of maps VISITED during the leg (`tracked()`), not the
position at the end. That answers "did it ever get there" and needs no non-warp tile to exist —
which mattered, because **every** B2F tile the warp graph knows is a ladder.

‼ **Prevention rule: NEVER pass a warp tile (door, ladder, stairs, cave mouth) as a navigation
destination — target a plain walkable tile.** The trip will overshoot by exactly one map and
report success. And when writing a probe, **assert on the strongest available evidence, not the
most convenient**: a final position is a snapshot, and a snapshot cannot distinguish "never got
there" from "got there and moved on". 14.8% of this ROM's warp edges have identical from/to
coordinates, so even the coordinates agree with the wrong answer.

‼ **Second lesson — the near-miss is the point.** The first run's wrong reading was *plausible,
specific and actionable* ("it halts on the ladder tile"), which is exactly what makes that class
of error expensive: it would have sent the next session hunting a bug in the ladder code that
does not exist. What caught it was refusing to accept a negative result whose mechanism I could
not explain — the no-exception return did not fit "the warp failed", and chasing that mismatch is
what produced the real answer. **An unexplained detail in a result you already believe is the
cheapest bug you will ever find.**

## 2026-08-05 — Three wrong readings of one failure, each cured by printing more of the error

**Symptom.** The Mt. Pyre traversal died on ROUTE120 (7,56). I diagnosed it three times:
1. *"Multi-hop threading stops one hop short"* — **wrong**, it was my probe targeting a warp tile.
2. *"Stranded in a sealed pocket whose only exit is the Ancient Tomb"* — **wrong**, read off a
   17-row slice of a 100-row map; the tomb's adjacency was pure coincidence.
3. **Right, and only after raising the driver's error truncation from 160 → 800 characters**,
   which revealed `Could not find a path from (7/56 @ ROUTE120) to (22/29 @ ROUTE122).`

**Root cause (measured, not inferred).** The navigator can WALK to a target, or WARP toward one,
but it cannot **walk across a map CONNECTION as an intermediate step**. `_staged_progress_warp`
scans `graph.warps_from()` only, and ROUTE120→ROUTE121 is a connection, not a warp — so it had
no move to offer, and control fell through to an **unvalidated** `region_route[0]` leg pointing
at a tile two connections away that `calculate_path` can never reach. **Route 121 was reachable
in 79 waypoints the entire time.**

‼ **Prevention rule 1: when a probe reports a failure you cannot explain, print the WHOLE error
before theorising.** Two full wrong diagnoses, several map dumps and a retraction commit were
bought by 160 characters of truncation. The nested `calculate_path` message named the failing leg
outright. **Budget error text generously in any probe — it is the cheapest diagnostic there is.**

‼ **Prevention rule 2: a claim read off a PARTIAL map dump is a guess.** Print the whole map or
write "unknown".

‼ **Prevention rule 3 — the recurring shape, now seen a fourth time.** The dead code path was
justified by *"this can never make a journey that works now start failing"*. Like the
`obstacle_search_exhausted` latch (*"riding out a scene cannot create new rocks"*) and the
`_CAVE_EXITS` comment (*"the navigator cannot cross warp levels"*), it was true when written and
became a trap. **A justification containing "can never" or "cannot" is a claim with an expiry
date — re-read it whenever the surrounding capability changes.**

## 2026-08-05 — I wrote the caveat, then shipped past it. A caveat you can state is a test you can run.

**Symptom.** `#24-connstep` (letting the navigator walk across a map connection) passed a clean
live A/B — old arm dies on ROUTE120, new arm reaches ROUTE121 — and I committed it enabled, with
a changelog note that the coarse tile choice "can land somewhere with less onward reachability
than an ideal tile". **That sentence was the bug report.** Four minutes of measurement, using a
stall save the failing run had already written, turned it from a caveat into a defect: from the
tile the step chose, ROUTE121 (21,5), the bot cannot reach ROUTE121's OWN south edge — the
onward route was sealed the moment it stepped.

**Root cause of the bad choice.** The candidate lattice iterates `for y in range(1, height, …)`
— from the TOP of the map. The target was SOUTH. "First walkable tile" is a coin flip with a
systematic bias, and it lost.

**The fix that worked (for now).** Gated behind `POKEBOT_CONNECTION_STEP`, default `0`, verified
to reproduce pre-change behaviour exactly. Kept rather than reverted because the diagnosis and
the A/B harness are worth having; the tile choice needs `map_path`'s global offsets to be aimed.

‼ **Prevention rule: when you can STATE a limitation precisely, you can usually MEASURE it —
do that before shipping, not in the changelog.** A named caveat is a hypothesis with a known
experiment attached. Writing it down instead of running it converts a four-minute check into a
defect that ships.

‼ **Second rule — "it cannot be worse, that journey fails anyway" is scoped to THAT journey.**
`_connection_step` runs BEFORE the unvalidated `region_route[0]` fallback, so it can divert trips
that succeed today, across every chapter. A new branch placed ahead of an existing one is never
purely additive, however dead the path it replaces looks on the case you are debugging.

## 2026-08-05 — I debugged the pathfinder for hours. The destination was blocked by three NPCs.

**Symptom.** The Fortree → Mt. Pyre journey failed. I root-caused it to a genuine navigator gap
(staged progress cannot cross a map CONNECTION), wrote a fix, A/B'd it, watched it strand the
bot, wrote a second variant, watched that fail differently, and ruled out surf. **All of it was
downstream of the real cause: three Team Aqua grunts standing in Route 121's only corridor
south, `FLAG_HIDE_ROUTE_121_TEAM_AQUA_GRUNTS` measured `False` — an UNFIRED STORY TRIGGER.**
The trigger that clears them, `ROUTE121 (25,5)`, was **6 waypoints** from where the bot stranded.

**Root cause of my error, and it is a measurement habit, not a reasoning slip.** Every Route 121
map dump I took covered **x=0-46 of an 80-wide map** — I never printed the full width, so I never
saw the x=30-31 corridor or the objects sealing it. I reasoned about traversability from 58% of
the map, repeatedly, while writing code against the conclusions.

‼ **Prevention rule: when the pathfinder says "no path", ask WHAT IS STANDING THERE before
asking what is wrong with the pathfinder.** A blocked corridor and a broken planner emit the
identical error string. The distinguishing check is cheap and specific:
1. `PROBE_MAPS=<map> mapfacts.py` — **at full width**, and read the `-- objects --` list.
2. Look up each blocker's hide flag in `modules/data/event_flags/<game>.txt`.
3. **Read that flag LIVE** — `mapfacts.py` shows the map as AUTHORED, so a listed object may be
   hidden at runtime. Only the live flag decides.
4. If it is present, find its coord trigger in the decomp's `map.json` (`coord_events`).

‼ **Second rule: an OBJECT with `script: 0x0` and a hide flag is a BLOCKER, not scenery.** It
cannot be talked to and it will never appear in any script you grep for by interaction — it just
occupies a tile until a scene removes it.

‼ **Third — the cost was not the wrong hypothesis, it was building on it.** The navigator gap I
found is REAL and the fix may still be worth having; it is committed, gated off. But I shipped
code against an untested assumption ("Route 121 is traversable from where we enter") three times
before testing it once. **A fix that does not resolve the symptom is evidence about the
diagnosis — treat the second failed variant as a signal to re-measure, not to iterate.**

## 2026-08-06 — Two different error strings, one wrong conclusion: "not connected" vs "no path"

**Symptom.** Across 2026-08-05 I concluded repeatedly that `calculate_path` "spans only DIRECTLY
CONNECTED maps", and built on it: it was the stated rationale for `#24-connstep`, for preferring
explicit legs, and it went into three docs and a chapter docstring.

**It is false**, and the Mt. Pyre chapter disproved it the moment it worked: leg 1 runs
**FORTREE → ROUTE120 → ROUTE121 in a single `calculate_path` call** — two connections.

**Root cause — I treated two different errors as one.** `map_path` emits:
* `"Source (…) and destination (…) are not on connected maps (note that warps don't count.)"`
  → genuinely unreachable; a warp is needed.
* `"Could not find a path from (…) to (…)."`
  → the maps ARE connected; **something is standing in the way.**

The ROUTE120 → ROUTE122 failure was always the SECOND kind — the Route 121 Team Aqua grunts
blocking the corridor. I read it as the first kind and went looking for a planner limitation.
Both strings appeared in my own logs, side by side, for hours.

‼ **Prevention rule: when a library reports failure, read WHICH failure. Two error strings from
the same call are two different facts.** Skimming them as "it failed" throws away the most
specific diagnostic the code is offering — here it was the difference between "the navigator is
missing a capability" (days of work, a gated-off feature) and "an NPC is standing there" (one
coord trigger, six waypoints away).

**What survives:** short explicit legs are still the right build pattern, but for a different
reason than I gave — each leg **fails where it broke**, naming the blocked map, instead of
producing one opaque error for a seven-map journey. The rationale in the chapter docstring has
been corrected to say so.

## 2026-08-06 — ‼ THE GREP TOOL RETURNS A SILENT ZERO ON `x4-runs/`. I accused an agent of fabricating data because of it.

**Symptom.** A research agent reported the counter `Story: nobody can learn <HM> — hunting …` at
35-53 hits per batch. I "verified" it, got **0 in all 17 batches**, and told the user the agent had
invented its central measurement. **The agent was right and I was wrong.**

**Two independent causes, both of which produce a confident zero:**

1. **I searched the wrong SURFACE.** I ran `grep -r … */stdout.txt`. That counter is emitted to
   `*/debug-logs/*.log`. Measured now:
   | batch | `nobody can learn` in **debug-logs** | in **stdout** |
   |---|---|---|
   | `20260806-055947` | **42** | 0 |
   | `20260805-075638` | **36** | 0 |
   | `20260804-174700` | **53** | 0 |
   Per playbook §2c the two surfaces carry **different facts by design** — stdout has no battle
   outcomes. Searching one and concluding "absent" is a category error.

2. **‼ THE GREP TOOL CANNOT SEE `x4-runs/` AT ALL.** `tools/story-dev/.gitignore:10` ignores
   `x4-runs/`, and the Grep tool wraps ripgrep, which **skips ignored files by default and reports
   `No matches found. Found 0 total occurrences across 0 files.`** Not an error. Not a warning.
   Confirmed directly: Grep on `x4-runs/20260806-055947` for `nobody can learn` → 0; Bash
   `grep -r` on the same path → 42.

**‼ STANDING RULE — SEARCHING BATCH LOGS:**
* **Never use the Grep tool on `tools/story-dev/x4-runs/`.** Use Bash `grep -r` (or
  `rg --no-ignore`). The whole batch evidence base is gitignored and reads as empty.
* **Name the SURFACE in any log claim** — `stdout.txt` vs `debug-logs/*.log` vs `badge-log.json`.
  A count without a surface is not a measurement.
* **A NULL RESULT REQUIRES A POSITIVE CONTROL.** Before reporting `count = 0`, run the SAME
  command over the SAME files for a string known to be present. One extra grep. It would have
  caught this instantly — in both directions.

‼ **Why this is the most dangerous shape in the project: a zero is byte-identical whether the
thing is absent or the search was blind.** This is the same failure as a phantom flag name reading
`False` forever, and as KI-39's "every case FAILS". **When two sources disagree on a count, do not
argue — find the command that reproduces BOTH numbers.** That is what resolved this in one call.

**What it nearly cost:** I had already told the user, on this false zero, that the HM-gate demand
"measures zero" and that a roster targeting it would be unmeasurable. The real figure is ~42
Surf-carrier hunt expeditions per batch, present in 16 of 17 stored batches.

## 2026-08-06 — I added a second knob to make a fix "safer". The extra knob became the new bug.

**Symptom.** `#24-hmteachloop` Fix A was graded against its own pre-registered target on batch
`20260806-103811` and **FAILED**: `Teach flow finished but` went **7 → 8**, not to 0.

**Root cause — my addition, not the original bug.** The diagnosis was correct and explicit: the
flat `range(3000)` ride budget expired while the teach was still progressing, and *"the ride budget
is the only correct knob."* I implemented the budget raise (9,000) **and also added a 900-frame
stall detector** on a progress signature (task set ∪ learn-state ∪ the target's moves), reasoning
that a genuinely wedged menu should still die fast.

**The signature sits UNCHANGED through the long post-teach text scroll**, so the stall counter fired
at 900 frames — **earlier than the 3,000 it replaced.** The hard cap was never reached (9,000 well
exceeds the ~4,870 a Norman-tail teach needs), so the stall break was the only possible early exit.

**Corroborating evidence from the same batch**, which also confirms the diagnosis was right:
* every SUCCESSFUL teach completes in **35-86 frames** (n=40) — nowhere near any cap;
* all 8 failures are Surf to an in-party 4-move mon — **Swampert ×5, Marshtomp ×2, Linoone ×1** —
  exactly the case the diagnosis isolated, entirely untouched by my change.

**The fix that followed:** delete the stall detector, keep the absolute 9,000 cap. Minimal, and
exactly what the diagnosis prescribed in the first place.

‼ **Prevention rule: a guard added to make a fix "safer" is itself a behaviour change and needs its
own evidence.** I had a measured diagnosis naming ONE knob, and I shipped two. The second had no
supporting measurement — I could not have said what a real stall looks like, because no stall had
ever been observed. **Ship the knob the evidence names; add the safety knob only when something has
actually failed unsafely.**

‼ **Second rule — this is why the target is pre-registered BEFORE the batch.** `TEACH OK` = 40 and
`Teach flow finished but` = 8 read, at a glance, like a mostly-working feature. Only the number
written down in advance (**0**) made it unambiguously a failure rather than something to rationalise.
The pre-registration did its job; I would otherwise have been tempted to call 8-vs-7 noise.

## 2026-08-06 — I removed a component on a 7→8 reading, and it was the best-performing config

**Symptom.** `#24-hmteachloop` has now been batched in three configurations. The failure counter
barely moves; the FINISH RATE moves a lot:

| teach ride config | `Teach flow finished but` | finish rate | watchdog |
|---|---|---|---|
| flat 3,000, no stall | 7 | 37.5% | — |
| **9,000 cap + 900-frame stall (v1)** | 8 | **52.0%** | 20 |
| 9,000 cap, stall REMOVED (v2) | 9 | **30.8%** | **68** |

**My error.** I read v1's `7 → 8` as "the stall detector made it worse" and removed it. **7/8/9 is
noise.** What the stall detector actually did was make each FAILURE CHEAP — and this batch's own
data shows why that is the only thing that matters: every SUCCESSFUL teach exits in **35-86
frames** (n=42), so the ride budget is irrelevant to successes and governs failures alone.
Without the stall break, a failure burns the full **9,000** frames instead of ~900 — ~8,100 wasted
frames each, which is exactly what feeds the 18,000-frame global watchdog.

‼ **Prevention rule: before removing a component, check what it costs on the metric it was
protecting — not on the metric you happened to be watching.** I graded a FRAME-COST guard on a
CORRECTNESS counter it was never meant to move. The number that mattered (finish rate, watchdog)
was in the same summary the whole time.

‼ **Second rule, and this is the fourth removal-shaped regression in a fortnight: a difference of
one on a single-digit counter is not a signal.** The project already knows a batch resolves ~±30
points and that near-binary counters are the only trustworthy batch signal. 7 vs 8 is neither.
**Require the counter to move by a factor, or to zero, before attributing anything to it.**

**Also recorded:** the underlying teach bug is STILL unfixed across all three configs (7/8/9).
The budget was never the knob — the failing teaches do not finish within ANY budget tried, and
then learn the move ~1,872 frames after the raise. **Do not tune it a fourth time.** Instrument
which `break` fires, at what frame, with what task set, and diagnose from that.

## 2026-08-06 — ‼ FOUR BATCHES, ZERO RESOLVABLE FINISH-RATE DIFFERENCES. I narrated all of them.

**Symptom.** Across four batches in one day I attributed finish-rate movements to specific code
changes — a "36-point regression", a "recovery", a "collapse". **None of the differences are
statistically resolvable.** Two-proportion z on the actual counts:

| batches | rates | z | verdict |
|---|---|---|---|
| `103811` vs `174746` | 52.0% vs 26.9% | **1.83** | NOT RESOLVED |
| `103811` vs `142418` | 52.0% vs 30.8% | **1.54** | NOT RESOLVED |
| `055947` vs `103811` | 37.5% vs 52.0% | **−1.02** | NOT RESOLVED |
| `142418` vs `174746` | 30.8% vs 26.9% | **0.31** | NOT RESOLVED |

Every one needs |z| > 1.96. **The project's own docs already say this** — *"a batch is ~38 runs
and can only resolve roughly ±30 percentage points… batches are for discovering failure modes,
not grading improvements"* — and I violated it in both directions repeatedly, including to justify
REMOVING a component and then to justify putting it back.

‼ **Prevention rule: never state a finish-rate comparison without its z. Compute it BEFORE
writing the sentence.** It is four lines of arithmetic against numbers already in `summary.json`.
Had I run it on the first comparison, three hours of attribution would not have happened.

‼ **What IS trustworthy is exactly what the project already said: near-binary counters and
factor-of-N moves.** From the same four batches, these ARE readable:
* `global watchdog` **68 → 33** — halved by restoring the stall detector. A factor, not a nudge.
* `Teach flow finished but` **9 → 4** — best of all four configs.
* `INTO THE PC BOX` / `withdrawing` **0** — a true zero, confirming the gate is off.

**So the stall-detector restoration is SUPPORTED — by the counters, not by the finish rate I
originally used to argue for it.** Right conclusion, wrong evidence, and the wrong evidence would
have flipped the decision if the noise had landed the other way.

‼ **Consequence for how this project measures.** The finish rate cannot grade a change at this
sample size, and the batches are already 3 hours. **Stop using it as a verdict.** Grade with:
(1) a direct capability test in the harness — binary, minutes; (2) near-binary counters; (3) the
badge funnel, which has ~200 records per batch instead of ~26 outcomes.

## 2026-08-07 — I "confirmed" a wedge TWICE. Both times it was my probe stopping, not the bot.

**Symptom.** Building a capability test for the full-party box catch, I twice reported the
box-transfer message as a confirmed production wedge:

    RESULT caught=True box_before=0 box_after=1 ... frames=30
    f8194: stall (bt='POOCHYENA was transferred to SOMEONE'S PC. It was placed in BOX "BOX1."')
    f27294: HANG CONFIRMED (20000 frames no progress)

It reads like proof. **It is not.** My `_stop()` fired the instant `pokemon_count` rose, the probe
logged its RESULT and called `context.set_manual_mode()`, and then **nothing was driving the
game.** The harness dutifully reported the idle as a hang. The `bt=` string is the STALE battle
text buffer — this project already recorded that trap ("the whiteout screen was just what was
left on screen").

**What the bot actually does**, once the probe drives the exit and then keeps playing:

    RESULT      caught=True box_before=0 box_after=1 exited_clean=True exit_frames=120 box_var=0
    AFTER-CATCH usable=True second_catch=True frames=20 box_now=2

`exit_frames=120` is the MINIMUM the settle loop can report — the exit was already clean before a
single forced `B`. Then it caught a SECOND mon into the box 20 frames later. **The full-party
overflow catch works end to end and was never broken.**

‼ **Prevention rule: a harness "HANG CONFIRMED" after a probe finishes is the PROBE idling, not
the bot wedging.** Any probe that hands to Manual and then gets graded on progress will always
look like a hang. **Grade a capability by DRIVING it to a positive outcome — "it kept playing and
did the thing again" — never by the absence of a hang.**

‼ **Second rule: a stop condition that fires on the FIRST observable sign of success stops too
early.** `pokemon_count > before` is true the moment the mon is stored, which is *mid*-sequence.
The interesting behaviour is everything after it. **Stop on the END of the operation, not its
first symptom.**

‼ **Third — I flip-flopped three times on this one question** (works / wedges / works). Each flip
came from a probe artifact, never from the bot. The cost was hours. **When a result contradicts
the previous one, suspect the instrument first — this session had already caught the same class
of error twice (`Grep` on a gitignored tree, `box_views` calling a property).**

---

## 2026-08-07 — A liveness check whose success condition the driven action CANNOT produce

**Symptom.** The withdraw capability test succeeded — `withdrew=True`, the mon entered the party —
and then the harness printed `HANG CONFIRMED (20000 frames no progress)` with the avatar frozen at
LILYCOVE_CITY (24,15) and `bot_mode=Story`. It read exactly like the bot wedging immediately after
a PC interaction, which is a plausible and alarming bug.

**Root cause — mine, in the probe.** The post-PC liveness check was `_story_spin` until
`local_coordinates` changes. **`spin` turns on the spot: it changes FACING, not position.** The
only other thing that could have broken the loop was a wild encounter, and we had just walked out
of a Poké Centre into a TOWN, which has no grass. So the stop condition was unreachable by
construction — the loop could only ever run to its bound, on a perfectly healthy bot.

**The fix that worked.** Replace it with an action that produces observable, un-fakeable progress:
a SECOND full `heal_in_pokemon_center`. It navigates into a building, works a scripted nurse
dialogue and walks back out — no in-place spin can imitate that — and it doubles as a real
assertion (the withdraw must now no-op, exactly one `withdrawing` line in total).

‼ **Prevention rule: before trusting a "did it keep working?" check, name the action that would
make it PASS.** If the thing you are driving cannot produce the state you are waiting for, you
have written a timer, not a test. This is the *third* variant of the same family in two days —
after "a HANG CONFIRMED post-probe is the probe idling" and "stop on the END of the operation, not
its first symptom" — and all three come from grading a capability by watching rather than by
driving it to a named positive outcome.

### Two smaller instrument errors in the same session, both of which printed a convincing lie

* **A read-back of `get_party()` in the same frame as a party write returns the PRE-write values.**
  The heal-fixture logged `Mightyena 0/124` right after healing it, on a run that then won four
  battles and levelled two mons. The party is cached per frame and the probe had not yielded.
  **Log the BEFORE→AFTER you wrote, never a same-frame read-back.**
* **`grep -c "withdrawing" harness_*.log` returned 0 while the line was plainly in the output.**
  `console.print` goes to stdout; the harness log file holds the harness's own `log()` lines only.
  This is the "NAME THE SURFACE" trap again, and the positive control is what caught it — the
  string was visible in the captured stdout of the very same run.

---

## 2026-08-07 — I tuned a budget FOUR times against a number that was measuring a different loop

**Symptom.** `#24-hmteachloop` survived four batched configurations (7 / 8 / 9 / 4 failures). Each
round changed `_TEACH_RIDE_HARD_CAP` and/or the stall threshold; the failure count never moved.

**Root cause — two instrument faults, compounding.**

1. **`TEACH OK … in {_f} frames` was reporting the wrong loop.** `teach_hm_move` has a ride loop
   `for _f in range(_TEACH_RIDE_HARD_CAP)` and then a menus-closed loop `for _f in range(1200)`.
   Python leaks a `for` variable into the enclosing scope, so by the time the success event ran,
   `_f` was the SECOND loop's count. That is where "every successful teach exits in **35-86
   frames**, so the budget governs only failures" came from. Measured properly, the ride was
   taking **8,999 frames — the entire cap — on teaches that had already succeeded.** The one
   sentence everyone reasoned from was false, and it read as hard data.
2. **Only the success path emitted telemetry at all.** Five distinct failure exits (two
   `never-appeared` raises, a silent 900-frame fall-through, a stall break, and cap exhaustion)
   were indistinguishable in every log. So no batch could ever discriminate between hypotheses,
   and the budget was the only visible knob — which is why it kept getting turned.

**The actual bug, found in one ~5-minute run once the exits were instrumented:** after the move is
learned the ladder's replace branches disable themselves (`and not _knows()`) and the flow falls
through to a blind `A`-every-third-frame — on a prompt that asks *"teach it to another POKéMON?"*,
where A means yes. The bot was re-arming its own teach cycle. Fix: press only `B` once `_knows()`.
A/B: **8,999 → 479 frames**, same outcome. `repro_hmteach_postlearn.py`.

‼ **Prevention rule: never reuse a loop variable name across two loops in one function, and never
read one after a later loop could have rebound it.** Capture it (`_ride_frames = _f`) at the moment
the loop ends. Python will not warn you; the number will just quietly become a different number.

‼ **Second rule — the one that actually cost the four rounds: if a component has N failure exits
and 1 of them is instrumented, you cannot diagnose it, and any fix you ship is a guess.** Before
changing a constant a second time, make every exit say WHICH it was. Cost of the instrumentation:
one function-local helper. Cost of not having it: four 3-hour batches and four wrong conclusions.

‼ **Third: a repro that only exercises the easy path will stay green through the bug.**
`--driver hmtest` teaches a freshly caught mon, which has a FREE move slot — no replace dialogue,
no post-learn prompt, 12/12 clean. Every real failure was on a four-move mon. **When a feature has
a branch the test never takes, the test is not covering the feature** — build the driver that
forces the hard branch (`--driver teachfull`).

### And my own probe repeated the session's other lesson, twice
* `get_item_bag().tm_hm_case` does not exist (the pocket is `tms_hms`), and a bare `except` around
  it turned the `AttributeError` into a confident "HM06 is not in the bag" on a save that had it.
  **A guard that reports a clean negative when the guard itself is broken is worse than no guard.**
  Use the intended API (`quantity_of`) and let errors be loud.
* The first draft of `repro_hmteach_postlearn.py` matched the button ladder at the wrong indent and
  anchored on "the first `if` in the loop" — which is the loop's own `break` test, not the ladder.
  It passed every assertion for the wrong reason. **A structural test must anchor on the thing it
  is testing (here: the branch that presses buttons), not on position.**

---

## 2026-08-07 — A task that is present on BOTH branches was used to choose between them

**Symptom.** 4 of 37 HM teaches in batch `20260807-102552` burned the full 9,000-frame cap and
never learned the move — all on Surf, all reported `post_select=instant-learn` on a mon with
**four** moves.

**Root cause.** The post-select loop decided which path it was on like this:

    if "Task_PartyMenuReplaceMove" in t or "Task_HandleChooseMonInput" in t:
        break   # instant learn path

`Task_HandleChooseMonInput` is the party menu — which is up on the *replace* path too, because it
does not disappear the instant the mon is chosen. On a slow frame it won the race before
`Task_ReplaceMoveYesNo` appeared, so the flow declared "instant learn", skipped the guarded
`if "Task_ReplaceMoveYesNo" in _tasks():` block entirely, and never answered the prompt.

**Fix.** Require positive evidence of the branch you are claiming: a genuinely free move slot, or
the move already known. With four moves there IS no instant-learn path, so the party-menu task
must not be allowed to signal one.

‼ **Prevention rule: a signal that appears on both branches cannot discriminate between them —
it can only tell you that you are somewhere in the middle.** Before using a task/flag/state as a
path selector, ask what it looks like on the OTHER path. If the answer is "the same", it is a
progress indicator, not a discriminator.

‼ **Second rule, about proving a gate: when a fix TIGHTENS a condition, testing the branch you
kept is only half the proof.** The other half is that the branch you gated is still reachable — a
gate one notch too tight fails silently and in the opposite direction. Here that meant a second
live run against a three-move mon (`instant-learn`, 252 frames, learned) alongside the four-move
one (`replace-prompt`, 479 frames, learned).

**The meta-point, and the reason this entry is worth the space:** this bug was found *by the
telemetry added earlier the same day for a different bug*, on its first batch, from one
self-contradicting field. It had been invisible for weeks, absorbed into the "7/8/9/4 teach
failures" that four 3-hour budget rounds chased. **Instrumenting every exit did not just fix the
bug it was built for — it made the next one fall out for free.**

---

## 2026-08-07 — A load-bearing dataset existed only as prose, and it does not reproduce

**What happened.** `#24-rarepredicate`'s "rare species" set — `best_slot_rate <= 4% OR
warp_depth >= 3`, with a published histogram (`d0=59 d1=21 d2=39 d3=7 d4+=3 d99=3`), "13 species
at depth>=3", "26 of 132 rare" — was recorded in `03-PUNCH-LIST.md` on 2026-08-06 and described
as "independently reproduced". `#24-roster` was then approved to build on it.

**There was no script.** Checked 2026-08-07: nothing in the repo produces those numbers.
`tools/story-dev/rare_species_dataset.py` is the first. Re-deriving from the same two committed
caches gives a materially different histogram (`d0=62 d1=36 d2=22 d3=11 d99=1`), 12 species at
depth>=3, and 23 rare.

**And the disagreement lands exactly where it hurts.** Skitty reproduces perfectly (rate 2%,
depth 0 — selected by the rate rule). **Bagon computes to depth 2**, one short of the `>=3`
threshold *that exists for Bagon's sake* — the user's ruling named it specifically ("gated to a
specific location"). As computed, the rule fails its own motivating example.

‼ **Prevention rule: a number that no committed script can regenerate is not a verified number,
however confidently it was recorded — and "independently reproduced" by a second pass of the same
kind of work is not reproduction, it is a second opinion.** Before a feature is approved to build
on a derived dataset, the derivation must exist as a runnable artifact. This is the same lesson as
"the logs are the data; the summary is only a reading of them", one level up.

‼ **Second rule — the one I had to actively resist: DO NOT tune the method until the answer comes
out right.** The obvious move was to adjust the BFS until Bagon landed on 3. That is fitting the
method to the desired conclusion, and it would have produced a dataset that looks validated and
is not. The punch list had already flagged this exact fragility in advance ("`>=3` earns some of
its precision by luck of Bagon's room being one warp deeper"); the honest outcome is to report
that the luck does not hold and stop.

**Also worth keeping — how sensitive this is.** Making warp edges bidirectional (a door works
both ways; the cache stores them directed) moved "unreachable" species from **34 to 1**. One
modelling choice dominates the entire answer, which is why the definition has to be pinned and
written down rather than re-derived from memory each time.

### And a smaller one in the same script
The encounter index is keyed by **internal ROM species index, not national dex**. I looked up
Skitty as 300 (its national dex) and got a different species, so the script reported "Skitty is
not in the index" for a species that is plainly in it. Resolve through the same call production
uses — `get_species_by_name(name).index` (Skitty is internal **315**, Bagon **395**).

---

## 2026-08-07 — I grepped for CONSTANTS and concluded the TABLE was almost empty

**Symptom.** I diagnosed `#24-winonaground` as "Winona's counter can never be hunted — the
huntable whitelist has only four grounds and none hosts a Rock/Electric/Ice wild", wrote it into
the punch list, changelog and handoff, told the user, and recommended a live ROUTE118 sweep as
the fix. All of it committed.

**It was wrong.** I ran `grep -n "_TRAINING_GRASS = "` and found three named constants
(ROUTE116/ROUTE117/ROUTE102), then treated those three as the whole table. The actual
`TRAINING_GRASS` table has **10 entries** — ROUTE101/102/103/111/115/116/117/**118**/119/121 —
and with `HUNTING_GROUNDS`' FIERY_PATH the bot has **11** huntable grounds. **ROUTE118 (29,15),
Electrike, the exact Winona answer I was proposing to go sweep, was already in it**, and ROUTE111
hosts Geodude (Ground/Rock, 100% rate) as a by-TYPE answer.

**How it was caught:** only because a probe for a *different* question (movepool counters) printed
`huntable grounds (11)` as a side effect. Nothing in the diagnosis itself would ever have failed.

‼ **Prevention rule: never infer a table's contents from a grep for its named constants.**
Named constants are a convenience for a few call sites; the table is the data. Print `len(TABLE)`
and its keys. The one-line version: **if the claim is about a data structure, evaluate the data
structure.**

‼ **Second, sharper rule: a diagnosis whose fix is "go and produce evidence X" must first check
whether X already exists.** I recommended sweeping a ground that had already been swept and
committed. The check costs one line.

**This is the THIRD instance of the same class in one session** — `Grep` on a gitignored tree
reporting 0 matches; the hard-plateau count read from profile dirs through a date glob that
excluded the files; and now this. All three: I queried a *proxy* for the data and reported the
proxy's answer as the data's. The common fix is not more care, it is **a positive control** —
print the size of what you searched, and confirm the search can find a thing you know is there.

---

## 2026-08-08 — I widened a candidate set on a PREDICTED reachability and never checked conversion

**What I shipped.** `#24-movepoolcounters` made the counter planner accept species that can LEARN
a counter-type move, not just species of that type. It was correct in principle, offline-proven
with a positive control, and it eliminated the "no huntable counter candidate" stop (25 → 0).

**What the batch said.** Hunts nearly doubled (18 → 33) and catches FELL (7 → 5). Conversion by
target: **Machop @ FIERY_PATH 5 of 5 (100%); every other destination 0 of 28.**
`could not reach` 72, `Could not find a path` 45, `hunt found nothing` 0 — **travel failures.**

**Root cause.** `huntable = reachable AND hunt_tile is not None`, and `reachable` is a
**prediction** (a hop budget plus a region oracle), not a driven fact. `hunt_ground_tile`'s
whitelist is evidence-backed for *standing and spinning*, but most of its entries come from
`TRAINING_GRASS`, which was two-way swept **for training, from training anchors** — not for a hunt
firing from a boss anchor. `HUNTING_GROUNDS`, the table that actually encodes driven
reach-and-leave evidence, has exactly one entry: FIERY_PATH. **It is the only rung that converts.**

‼ **Prevention rule: when you widen a candidate set, the acceptance metric is CONVERSION, not
population.** I measured "candidates exist" (25 → 0 stops) and "the planner picks them" (7 Baltoy
hunts) and reported both as confirmation. Neither is the outcome. The question was always *how
many hunts CATCH*, and that number moved the wrong way.

‼ **Second rule: a whitelist's evidence is only valid for the QUESTION IT WAS SWEPT FOR.** Both
tables answer "can we stand here and spin?", which is true. The counter hunt asks a different
question — "can we get here from where the boss is fought, and leave?" — and only FIERY_PATH was
ever measured for that. Reusing a table across two questions is how a fails-closed whitelist
quietly became fails-open.

‼ **Third: it may be worse than what it replaced, and that is the shape to fear.** Before, Winona
stopped instantly. Now she spends a cross-Hoenn trek and then stops — and the hunt is bounded to
one attempt per boss per run, so a bad destination costs the boss, not a trek. The handoff has
warned about exactly that bound since 2026-07-30; I widened what feeds it without re-reading it.

**Not claimed:** the finish rate fell 41.7% → 25.8% at z = −1.24, which does NOT resolve. The
concern above rests on the conversion counters (33 → 5), which are near-binary and do.

---

## 2026-08-08 — I inferred a structural cause from ONE confound and scoped a campaign around it

**The inference.** `Numel @ FIERY_PATH` was 5 hunts / 0 caught (Wattson, from Mauville) while
`Machop @ FIERY_PATH` was 5/5 (Norman, from Petalburg). Same ground, opposite outcomes — so I
concluded reachability is a property of the **(boss anchor → ground) PAIR**, wrote it into three
docs, and scoped `#24-huntreachproof` part 2 as a per-anchor driven-sweep campaign across six
anchors × five grounds.

**It was wrong.** After the narrowing shipped, the very next batch gave
`Numel @ FIERY_PATH` **7 hunts / 3 caught**. FIERY_PATH is reachable from Mauville and always was.

**The real cause was DESTINATION ORDERING.** The ladder tries up to three destinations but the
hunt is bounded to **one attempt per boss per run**, so ROUTE111/ROUTE116 consumed the bound
before FIERY_PATH was ever reached. Removing the bad destinations let the good one convert.

‼ **Prevention rule: two outcomes that differ do not identify the variable that differs.** I had
exactly one Numel/Machop contrast and read the anchor as the cause, when the ladder's ORDER — a
thing I already knew was bounded, and had written about twice — explained it at least as well.
**Before scoping work around a structural claim, list the alternatives that fit the same data
and find the measurement that separates them.** This is the same shape as the 2026-07-31 entry
("a probe that returns FAIL for every case has found a common SYMPTOM, not a common cause").

‼ **What saved it: shipping the narrowing FIRST and measuring before building on it.** I nearly
did part 2 first. The batch that validated the small change also demolished the premise of the
large one — six anchors × five grounds of emulator sweeps that would have fixed nothing.
**When a cheap change and an expensive one rest on the same hypothesis, ship the cheap one and
let it test the hypothesis.**

**The good news, recorded so the method is not lost:** the acceptance metric was CONVERSION
(hunts started vs caught), adopted after the 2026-08-08 population-vs-conversion mistake, and it
returned **15% → 50%, z = +2.73 — the project's first resolvable counter-chain result.**
The metric change is what made the win legible.

---

## 2026-08-09 — I read `map_name` and wrote down a GYM save as a CITY save

**Symptom.** `probe_anchor_inventory.py`'s first run reported `mauville_wedge.ss1` as
`MAUVILLE CITY (4, 12), badges=12, controllable=True` and flagged it **USABLE** as the anchor
`#24-r116sweep` needs. The handoff said the opposite — that this save starts *inside the gym*.
I had a fresh measurement disagreeing with a written record, which is the moment a wrong fact
gets committed.

**Root cause.** I printed `get_map_data_for_current_position().map_name`, which is the human
LABEL, and interiors carry their city's label: `MAUVILLE_CITY_GYM` reads as `"MAUVILLE CITY"`.
The (group, number) tuple was unambiguous the whole time — `MAUVILLE_CITY = (0, 2)`,
`MAUVILLE_CITY_GYM = (10, 0)` — and I had simply not printed it. Worse, the handoff's own
phrase *"starts INSIDE the gym at (10,0)"* was a previous agent reading that same tuple as a
TILE. So the identical ambiguity produced two different wrong readings, in opposite directions,
in two different sessions.

**The fix that worked.** Resolve `MapRSE((group, number)).name` and report THAT; never report
`map_name` as identity. The probe now says `MAUVILLE_CITY_GYM (4, 12)` and correctly answers
"no save satisfies the requirement", which is what sent the work to building a capture driver
instead of burning a third run on a bad anchor.

‼ **Prevention rule: report IDENTITY as the enum, never as the display label.** A label is
chosen for humans and is deliberately non-unique; a label that matches is not an identity that
matches. Where a fact has a canonical key (an enum, an ID, a `(group, number)` tuple), print
the key — and if a label is printed too, never let it be the field a decision reads.

‼ **Second, general one, because this is the SEVENTH proxy-reading error in eight days:** the
positive control worked exactly as intended here — it proved the badge reader could separate a
known-early save from a known-late one — and it still did not save me, because **the control
covered a different column than the one I got wrong.** A control proves the instrument can see
*the thing it tests*. When a probe reports several fields, the field a DECISION reads is the one
that needs the control.

---

## 2026-08-09 — A blind DETECTOR was written down as a broken FIXTURE, and it cost a hypothesis

**Symptom.** `#24-teachmsgstall` attempt 6 (`TEACH_AFTER_BATTLE=1`) reported
`battle_seen=False frames=2466`. That was recorded in the handoff and punch list as *"the spin
produced no encounter, so the probe is broken, NOT evidence"*, and the item's next step became
"fix the spin (verified grass tile + real budget)".

**Root cause — the spin was fine; the instrument reading it was not.** The log shows **197
`CONTROLLER -> BattleListener.fight` transitions** and the target's EXP climbing 21760 -> 24240.
The stop-condition polled `battle_is_active()` from inside `_story_spin`, but the mode's
generator is **not pumped while `BattleListener` owns the controller stack** — only the top of
the stack is advanced. So the callback ran on ~2,466 of ~44,000 frames, and *every one of those
frames was, by construction, a frame with no battle active*. The check could never have
returned True; `battle_seen=False` was a tautology, not a measurement.

**The fix that worked.** Count the battle in `on_battle_started`, which the framework calls on
the MODE INSTANCE while its generator is suspended. A/B on the identical fixture:
**old `battle_seen=False` after 2,466 pumps -> new `battles=1` after 7 pumps.**

**And the cost, which is the real lesson.** Attempt 6 had actually reached the teach with a
battle tail resident (`cb=ReturnFromBattleToOverworld`, `bt='Got away safely'`) and **taught
successfully**. It was a *negative result for the battle-tail hypothesis* — filed as "no
evidence" for a day, while the hypothesis it refuted stayed live and the next step pointed at
fixing a spin that was never broken.

‼ **Prevention rule: a NEGATIVE from a detector is only evidence if the detector could have
returned POSITIVE.** Before recording "X did not happen", show the check ran on frames where X
*could* have been observed — print how many times it ran alongside the answer (`pumps=7/40000`
is readable; a bare `False` is not). ‼ Corollary specific to this codebase: **anything sampled
from inside a generator on the controller stack is blind to whatever preempts that stack.**
Sample those from `on_battle_started` / a listener instead — the same shape as KI-37, where a
listener starving the mode produced a symptom that looked like the mode's own bug.

---

## 2026-08-09 — "a battle tail cannot be loaded from a save" sent three attempts down a road that wedged

**Symptom.** `#24-teachmsgstall` attempts 3-5 tried to WIN NORMAN'S GYM inside a probe so that a
battle tail would be resident when the teach ran. All three wedged in the gym (f61848, f56868)
without ever reaching the teach, and the item acquired a standing warning: *"do not return to
the gym route"*.

**Root cause of the detour.** The item recorded, as a fact, that *"a tail is RUNTIME state and
cannot be loaded from a save"*. That is true of a `.sav` (the game's own save file) and **false
of a `.ss1`**, which is a full emulator snapshot — the harness's own save format, and the thing
every fixture here already loads. Measured: all **six** stall states in `saves/stalls/` reload
with `cb=ReturnFromBattleToOverworld` and `instr=BattleScript_PayDayMoneyAndPickUpItems` still
set. The condition three probes tried to manufacture by playing the game was sitting on disk,
loadable in seconds.

**Prevention rule: when a note says a state "cannot" be reached, check the cheapest thing that
would disprove it before designing around it.** ‼ The specific confusion worth naming, because
it will recur: **`.sav` and `.ss1` are not the same kind of save.** A `.sav` holds what the game
persists; a `.ss1` holds the whole machine — RAM, callbacks, task list, mid-script state. Any
claim of the form "X is runtime state so a save can't hold it" is about `.sav` only.

‼ This is the same shape as the 2026-07-31 entry ("an optimisation whose justification contains
the word *cannot* deserves a second look") — that one cost a latched obstacle search, this one
cost three wedged probe runs and a day.

---

## 2026-08-09 — (not a mistake — the method that worked, recorded so it is repeated)

`#24-teachmsgstall` was reproduced by a fixture built to test a **different** hypothesis, and the
thing that made the result usable was a guard that declared the run invalid for its own stated
purpose. `TEACH_AFTER_TRAINER` patrolled for a trainer, found none (`trainers=0`), printed
*"NO TRAINER ENGAGED — this run is NOT evidence"* — and the teach stalled anyway, on the nine
**won wild** battles the patrol had produced as a side effect.

Without that guard the obvious write-up would have been "reproduced after a trainer battle",
which is false and would have sent the fix at trainer handling. With it, the actual variable was
visible in one line.

‼ **Prevention rule (generalising the three guards added today): a fixture must ASSERT that it
created its condition, and print the assertion beside the result.** The three that paid for
themselves within an hour: a ball-supply check (a run spun through 125 battles catching nothing
because the save had zero balls), a `caught=False` guard, and this `trainers=0` guard. ‼ The
corollary is the valuable half: **when the condition was NOT created and the bug happens anyway,
that is a finding — read what the fixture did instead.**

---

## 2026-08-09 — I nearly shipped an INERT fix, and a 10-minute measurement stopped it

**What almost happened.** `#24-teachmsgstall` was root-caused to `_MENU_TASK_MARKERS` not
containing `Task_ContinueTaskAfterMessagePrints`: `normalize_to_overworld` settles while a
message is printing, the teach opens the BAG on top of it, and the two tasks that result are
*exactly* the failing signature `['ListMenuDummyTask','Task_ContinueTaskAfterMessagePrints']`.
The reasoning was clean, it explained the signature perfectly, I had written the proposed fix
into the punch list and committed a deliberately-RED structural repro asserting the gate.

**Why it was wrong.** The signature is what the failure looks like *afterwards*. Printing the
state at the moment the teach actually takes over (a `HANDOFF-STATE` line in the driver) shows
**`message_task_active=False`** and a plain overworld task list — the message task does not exist
yet; it appears only once the bag is open. A gate on it would have settled anyway and changed
nothing. The A/B against a PASSING fixture then showed the two hand-offs are identical in every
field but one: `instr=BattleScript_PayDayMoneyAndPickUpItems` (fails) vs
`BattleScript_SuccessBallThrowEnd` (passes).

**Cost of catching it:** two ~10-minute fixture runs. **Cost of not catching it:** a shipped
no-op, a green repro asserting it, and a bug still live behind both.

‼ **Prevention rule: a signature captured at the STALL describes the wreck, not the moment of
failure. Instrument the HAND-OFF — the last instant the code still had a choice — and compare a
failing run against a passing one.** Two runs of the same fixture with one variable flipped
answered in twenty minutes what a day of reasoning from the crash signature got backwards.
‼ **Corollary, and the reason the repro was DELETED rather than left red:** a committed test for
a refuted design is worse than no test — it hands the next agent a wrong target with an
authoritative-looking assertion attached.

---

## 2026-08-09 — the acceptance bar was set from a number computed a different way than the check

**Symptom.** The batch confirming the `party_counter_slot` fence was graded against a written bar
of *"REAL conversion back to ≥50%"*. It came in at 39.1% and looked like a miss, next to two
results (Machop 0/7 → 6/7 at z = +3.24, false catches 10 → 0) that were unambiguous successes.

**Root cause.** The 50% came from the week's headline *"conversion 15% → 50% (z = +2.73)"*, which
was computed on **REPORTED** catches. The check was specified on **REAL** catches — the stricter
definition adopted afterwards, precisely because reported catches were found to include
pre-existing party mons. Recomputed consistently, the earlier pair is **15.2% → 45.0%
(z = +2.39)**. Nothing about the earlier conclusion changes; the *target* was inflated by ~5
points, and a genuine restoration was set up to read as a shortfall.

‼ **Prevention rule: when a metric's DEFINITION is tightened, restate every historical number in
the new definition before any of them is used as a threshold.** An acceptance bar inherited from
the looser definition silently compares two different quantities — the same reported-vs-real error
this project already documents, one level up, at the level of the metric rather than the data.
‼ Practical version: this is why `analyse_conversion.py` now exists and prints hunts / reported /
REAL together. A number that cannot say which definition produced it should never become a bar.

---

## 2026-08-09 — ‼ I RETRACT "an obtainable counter does not beat Norman". Six arms measured a BROKEN INJECTED MON.

**What I claimed, hours earlier.** Six `--driver normancounter` arms (a Fighting counter injected
at L18/22/26/40/55 plus a no-counter control) all lost to Norman's L28-31 team, and I concluded —
in the changelog, the handoff and to the user — that this "cannot be a type-coverage or level
problem" and "points at how the fight is conducted". I even cleared two confounds (full HP;
production's own battle strategy) before writing it, which made it feel well-checked.

**What the new telemetry showed on its FIRST run.** `#24-bosstelemetry` logs one line per turn
decision. The injected Machop:
```
[TURN  8] Machop L55 83/150 -> UseMove:Karate Chop(pp22)  vs Slaking L31 143/143
[TURN  9] Machop L55 83/150 -> UseMove:Karate Chop(pp22)  vs Slaking L31 143/143
[TURN 12] Machop L55 32/150 -> UseMove:Karate Chop(pp22)  vs Slaking L31 143/143
```
**Five consecutive turns: PP frozen at 22, Slaking untouched at 143/143.** The move was selected
and never executed. Meanwhile a natural party member in the same battle behaved normally
(`Mightyena -> Bite(pp24)`, Slaking 143 → 125 → 108 → 88). The A/B confirms it: with
`NORMAN_MACHOP_NATURAL=1` (omit `moves=`, let the species learnset stand) the same L55 Machop uses
**Cross Chop with PP decrementing 5 → 4 → 3 → 2** and knocks opponents down.

**Root cause of the bad experiment.** `debug_create_pokemon(moves=[LearnedMove.create(...)])`
produced move slots the battle engine will select but not execute. **Every one of the six arms was
measuring a mon that could not attack.** The control arm was real, but it was the only real one.

‼ **Prevention rule: an injected fixture mon must be proven to ACT, not merely to exist.** I
checked that it was created at full HP, that it was in the party, and that it was sent out — three
checks, all passing, none of which asked whether its moves worked. **The assertion that mattered
was "did the opponent's HP change".** For any injected combatant, assert an effect on the world,
not a property of the object.
‼ **Second: the conclusion was seductive because it was surprising.** "A L55 counter loses" is
exactly the kind of counter-intuitive result that feels like insight, and I promoted it to a
strategic recommendation within the hour. **A result that overturns a week of assumptions deserves
MORE instrument-checking than a boring one, not less.**

---

## 2026-08-10 — my "item didn't work" detector compared HP ACROSS a Pokémon switch

**Symptom.** `#24-battleitems`'s no-op guard reported **10 cases where "both index spaces failed"**
in batch `20260810-035733`, and 32 guard fires in the batch before — figures I used to describe
the feature as landing only ~2/3 of the time.

**What the logs actually say.** Of those 10, **9 are followed immediately by a `[FAINT-CHOOSER]`**
— the target fainted. And the detector works like this:

```python
mon = battle_state.own_side.left_battler          # whoever is active AT THIS DECISION
...
if mon.current_hp <= self._hp_when_item_requested: # HP recorded for a DIFFERENT mon
```

When the target faints, the next decision's `left_battler` is its **replacement**, so the guard
compares one Pokémon's HP against another's, concludes "no effect", and blames the item. The
genuine item-failure rate is therefore much lower than reported, and "both index spaces failed"
was mostly a mislabelled death.

**What is NOT affected, and why the index rule still stands:** the rule was derived from the 29
**landings** — positive detections where HP demonstrably rose on the same mon — not from the
failure counts. Those are reliable.

‼ **Prevention rule: a before/after comparison must prove it is comparing the SAME SUBJECT.** I
recorded `hp_when_item_requested` without recording WHOSE hp it was, and in a battle the active
Pokémon changes underneath you. Key such state by identity (`party_index`), and skip the check
when the subject has changed. ‼ This is the same family as KI-34 (party-menu vs `get_party()`
indices) and as the 2026-08-09 detector that could never observe the thing it tested: **state
sampled from a moving frame of reference needs its frame recorded alongside it.**

**Fix (queued, not yet applied — a batch is mid-flight and lanes re-import `sandbox-pokebot/`):**
key `_hp_when_item_requested` by `mon.party_index` and treat "subject changed" or `current_hp == 0`
as *no verdict* rather than as a failure.

---

## 2026-08-10 — I answered a post-Mt-Pyre question from a badges-1-3 anchor, seven probes running

**Symptom.** `#24-magmahideout` was deferred three weeks ago as "the door is unreachable; one-way
ledges". I re-tested with four static probes and three DRIVEN ones, each with a passing control,
and concluded — in the changelog, the punch list and to the user — that "the blocker is REAL" and
the chapter needed **explicit scripted movement**. Then one look at the decomp's object list
dissolved it: a **Team Magma guard stands on the single entry tile (16,19)** until flag 847
`HIDE_JAGGED_PASS_MAGMA_GUARD` is set. In the correct era the door is **2 waypoints** from a tile
the bot already reaches.

**Root cause.** Every probe ran from `jagged_descent.ss1` / `lavaridge.ss1` — **badges 1-3**, long
before the Magma Emblem — to answer a question about content that happens **after Mt. Pyre**. The
anchors were chosen to be geographically right and I never asked whether they were
chronologically right.

‼ **This is the SAME mistake as `#24-r116sweep`**, whose entry reads *"wrong ERA entirely"*, and
it is why `--driver anchorstory` has a `CAPTURE_FORBID_FLAG` guard **that I wrote earlier the same
day**. I built the era guard and then picked an anchor by geography anyway.

‼ **Prevention rule: an anchor must be verified against the STORY CLOCK, not just the map.**
Before probing, name the flag/var that gates the content under test and assert it on the anchor —
here, one `get_event_flag("HIDE_JAGGED_PASS_MAGMA_GUARD")` would have ended it in seconds.
‼ **Second, sharper rule: when a tile is walkable in collision data but the avatar cannot enter
it, suspect an OBJECT before suspecting the terrain model.** I reached for "KI-24 planner blind
spot" — a real, documented failure of that instrument — when the planner was correctly modelling
an NPC. A known bug in a tool is a seductive explanation for anything that tool reports.

---

## 2026-08-10 — the THIRD wrong answer about the same door: a static PASS on a runtime WALL

**Symptom.** The entry above closed `#24-magmahideout` with "in the correct era the door is **2
waypoints** from a tile the bot already reaches", measured post-Emblem with a passing control. I
built the travel leg against that number. It is **an artifact**: the door at `JAGGED_PASS (16,18)`
is covered by `METATILE_Lavaridge_RockWall` at runtime and cannot be walked onto at all until a
**step trigger** opens it.

**Root cause.** `JaggedPass_OnLoad` calls `JaggedPass_EventScript_ConcealHideoutEntrance`, which
`setmetatile`s (16,17) and (16,18) to rock wall while `VAR_JAGGED_PASS_STATE <= 1`. A coord_event
on one of five tiles — `(21,15) (22,20) (21,20) (14,15) (13,15)`, gated on the var being 1, which
`JaggedPass_OnResume` sets by itself once the Magma Emblem is in the bag — runs
`JaggedPass_EventScript_OpenMagmaHideout`, which `setmetatile`s the entrance open and sets the var
to **2**. ‼ `calculate_path` reads the ROM's **layout**, where (16,18) is already a cave entrance.
So the static planner cheerfully returned "OK, 2 waypoints" for a tile the running game had
walled off.

‼ **Three separate conclusions about this one door were all the same wall, misread:** "one-way
ledges make it unreachable" (2026-07-26); "ledge-isolated, needs SCRIPTED MOVEMENT" (2026-08-10
AM); and `--driver magmadoor`'s "pressing Up from (16,20) twelve times did not move the avatar, so
there is a real south-facing LEDGE". Each was a real measurement fitted to the wrong cause.

‼ **Prevention rule: a static PASS is not evidence on a map whose scripts rewrite metatiles.**
This is KI-24 INVERTED, and the inverted form is the more dangerous one — KI-24 is a static FAIL
on reachable terrain, which prompts a re-test, while this is a static **PASS** on unreachable
terrain, which reads as confirmation and gets built on. Before trusting `calculate_path` on a
story map, check whether the decomp's `OnLoad`/`OnResume`/`OnTransition` calls `setmetatile`; if
it does, grade reachability by the VAR the script sets, never by the planner.

---

## 2026-08-10 — my driver inherited a framework DEFAULT and I nearly reported it as a route failure

**Symptom.** Two driven runs of the new `--driver magmatravel` (the `#24-magmahideout` travel leg)
ended at the **identical frame f23674**, whiting out on ROUTE123 and dropping to Manual. I was one
step from writing down "the post-Mt-Pyre party cannot cross Hoenn; the travel leg is blocked".

**Root cause.** `BotMode.on_whiteout()` returns **False** by default, and False means *"switch the
bot to Manual so the user can handle it"*. **StoryMode overrides it to True and recovers**
(`story_mode.py:1221` — "We handle the whiteout ourselves — do NOT drop to Manual"). My driver
overrode `on_battle_started` and nothing else, so it measured the *default framework policy*, not
the production behaviour. In the real bot a whiteout is a survivable event that respawns a FULL
party at the last Pokémon Center.

‼ The tell was there and I nearly walked past it: **two independent runs failing at the exact same
frame is not a fact about the world, it is a fact about a deterministic code path** — and a
deterministic stop right after a state transition points at a handler, not at terrain.

‼ **Prevention rule: a driver that stands in for a production mode must mirror that mode's
OVERRIDES, not just call its functions.** "Probe with the SAME call the production path uses"
(2026-07-30) is not enough — the same call under different *policy* is a different experiment.
When writing a harness driver, diff its overridden methods against the mode it is standing in for
(`on_whiteout`, `on_battle_started`, `on_battle_ended`, …) and justify every difference.
‼ Corollary, and the reason this is worth the words: the surrounding facts were all TRUE — the
party really is 3/6 fainted with no Revives, the nearest Pokémon Center really is 276+ waypoints
away, and it really did die on Route 123. A correct-sounding story assembled from true facts is
exactly what a wrong instrument produces.

---

## 2026-08-10 — a flag set by a script is NOT the end of that script (two runs lost to a locked avatar)

**Symptom.** The new Strength push refused to work on Magma Hideout 1F. Eight pushes, boulder
unmoved, twice in a row, and **every diagnostic looked healthy**: `strength_active=True`, the
boulder present at the expected tile with the right graphics id, the destination tile collision 0
and elevation 3 (same as the source), the player standing adjacent and facing it. I twice
suspected the destination and twice re-measured it as fine.

**Root cause.** `EventScript_ActivateStrength` does `setflag FLAG_SYS_USE_STRENGTH` **and then
keeps going** — field-move animation, "STRENGTH made it possible to move boulders around",
`releaseall`. My activation loop exited the instant the flag flipped, which is while the player
is still held by the script's `lockall`. Every subsequent push pressed a direction at a **locked
avatar**, which does nothing and reports nothing.

**The fix that worked.** After the flag is set, `_ride_out_scripted_scene("B")` then
`wait_until_truly_controllable()` before touching the D-pad.

‼ **Prevention rule: a flag is an EVENT INSIDE a script, not the script's end.** When you wait on
a flag to know a scripted action happened, you have learned that it *started*, not that control
came back. Ride the scene out and wait for control before acting on it.

‼ **Second rule, and it is what actually broke the deadlock: a failure message must report STATE,
not a HYPOTHESIS.** Mine said *"check that the destination is walkable and empty"* — which sent me
to re-measure the destination twice. When I replaced it with a dump of the world
(`strength_active`, the tracked object id, every object with coords and graphics id), the cause
fell out of a single run. The message had encoded my best guess and I kept re-testing the guess.

**Two more bugs in the same code, both found only by driving it, both worth the line:**
* **A one-frame `press_button` is not a walk.** Movement needs the direction held until the tile
  changes (`walk_one_tile`); a single press just turns.
* **`walk_one_tile` leaves the direction and B HELD if you abandon it early** — it releases only
  after the position changes. Abandoning it in a retry loop jams the D-pad for every later
  attempt. Release in a `finally`.

---

## 2026-08-10 — I tested "is anything on that tile" for an object I had just displaced myself onto

**Symptom.** `strength_push`'s success test was *"the boulder is no longer on its tile AND
something is on the destination"*. That reads **False on a push that worked perfectly** — because
pushing a boulder moves the PLAYER onto the tile the boulder just left. The object dump shows it
plainly: `id=255@(7,23)` is the player, standing exactly where the test was looking.

**Root cause.** I tested a POSITION for an identity question. The subject moved, and my frame of
reference moved with it.

‼ **Prevention rule (this is the THIRD instance in this project — promote it):** state sampled
from a moving frame of reference needs its subject pinned by IDENTITY, not by location. Track the
object by `local_id`. The prior two: `#24-battleitems`' HP comparison that spanned a Pokémon
switch (2026-08-10), and KI-34's party-menu vs `get_party()` index confusion.

---

## 2026-08-11 — four rounds lost to a detector keyed on a task that RETIRES ITSELF on the frame it becomes useful

**Symptom.** `#24-teachmsgstall`: HM teaches wedged, "the replace prompt never appears", and the
failure point MOVED between runs (`Task_BagMenu_HandleInput` / `Task_ClosePartyMenuAfterText` /
`Task_ClosePartyMenuAndSetCB2`). It read as deterministic from a save (0 of 3) and as intermittent
in production (38 of 42) at the same time. Four rounds of budget tuning and three refuted causes.

**Root cause.** The detector was
`if "Task_ReplaceMoveYesNo" in t and "Task_PrintAndWaitForText" not in t`. Per
`pret/pokeemerald src/party_menu.c`, `Task_ReplaceMoveYesNo` displays the yes/no menu and
**sets its own task function to `Task_HandleReplaceMoveYesNoInput` in the same frame** — so the
condition is true for exactly one frame, measured. Miss that frame and the prompt is unobservable
for ever, and the loop's blind `A` every 12 frames then walks the flow into
`Task_HandleStopLearningMoveYesNoInput`, where **A means YES, ABANDON THE TEACH**.

**The fix that worked.** Watch the task that READS INPUT as well as the one that DISPLAYS
(`_PROMPT_TASKS`, `_STOP_TASKS`); add an `already-advanced` exit for "someone already answered
it"; press **B** at the stop-learning prompt, before the blind-A fallback in the ladder.

**Prevention rule.** *A Gen 3 `Task_XxxYesNo` hands off to `Task_HandleXxxYesNoInput` on the frame
the menu becomes answerable — so never key a detector on the DISPLAY task alone. Watch the input
handler too, or accept a one-frame lottery.*

**Second prevention rule (this one is general).** *Never blind-mash the ACCEPT button at a live
yes/no. Somewhere in Gen 3 there is a prompt where A means "give up", and a 900-frame mash will
find it. Mash only to advance TEXT; every yes/no needs a named branch.*

---

## 2026-08-11 — my fault injection re-fired on every retry, so the FIXED arm looked broken

**Symptom.** The A/B for the above: `TEACH_CANCEL_FORGET=1` cancelled the forget-move screen to
land the flow on "Stop trying to teach?". **Both arms failed**, and the NEW arm failed *worse*
(`menus-never-closed` after `stall_peak=250`). Read naively, the fix made things worse.

**Root cause.** The injection had no latch. The whole point of the fix is "say NO to giving up and
come back for another attempt" — so on the fixed arm the flow came back to the forget screen, the
injection cancelled it *again*, and it looped until the cap. **The injection was unsatisfiable, and
it punished precisely the recovery behaviour under test.**

**The fix that worked.** A one-shot latch: the fault models a SINGLE mistimed press. OLD then
fails (`learned=False`), NEW then succeeds (`learned=True`, 896 frames).

**Prevention rule.** *If a fix's mechanism is RETRY, the injected fault must fire ONCE. A fault
that re-fires on every attempt cannot be recovered from by design, so the arm that recovers
correctly looks identical to the arm that never tries.*

---

## 2026-08-11 — the committed "cheap repro" had been silently invalidated by a later successful run

**Symptom.** Both documented `#24-teachmsgstall` repro commands (`magma_door.ss1` + `--driver
teachfull`, HM04 and HM02) — recorded in `04-HANDOFF.md` and `03-PUNCH-LIST.md` as failing 3/3 —
**passed on the first attempt**, with identical parameters (`slot=2 replace_slot=0`).

**Root cause.** `saves/magma_door.ss1` is **re-captured by `--driver magmatravel` on every
success**. A chapter run at 22:05 on 2026-08-10 overwrote the exact save the 21:27/21:34 failures
were measured on. Different frame phase, so the race lands the other way. Nothing was wrong with
the finding; the fixture underneath it moved.

**The fix that worked.** Stop depending on it: the fault is now injected
(`TEACH_MISS_WINDOW` / `TEACH_CANCEL_FORGET`), which is reproducible regardless of the save.

**Prevention rule.** *A save that any driver RE-CAPTURES is not a fixture — it is a cache. If a
repro's evidence depends on an exact save, copy it to a name nothing writes to, and record the
mtime beside the measurement.*

---

## 2026-08-11 — an "ALREADY PROVEN" row with no sample size beside it, and n was 1

**Symptom.** `04-HANDOFF.md` carried, in a table headed *"‼‼ ALREADY PROVEN — DO NOT RE-RUN THESE"*:
"The Magma Hideout chapter completes — ✅ `groudon=True`, floors `[1F,2F_1R,3F_1R,4F]`, **0
whiteouts**". The second driven run of the identical command **lost to Maxie**: 7 whiteouts,
respawn at MAUVILLE_CITY. The row was true and also, as written, unfalsifiable-looking.

**Root cause.** The row recorded an OUTCOME without its **n**, on a step that contains a boss
fight — i.e. a stochastic step — and the table's own heading actively discourages re-measuring it.
The evidence index was built to stop wasteful re-derivation, which is right; but "do not re-run"
plus a missing sample size turns one lucky run into settled fact.

**The fix that worked.** KI-50 records the second result and re-states the claim as "reaches Maxie
reliably; *completes* 1 of 2". The chapter's navigation really is proven — the fight is not.

**Prevention rule.** *Every row in an "already proven" table needs its n. A claim about a step
containing a battle is a RATE, never a fact — write it as k/n or do not write it.*

---

## 2026-08-11 — I put a field in a failure message that reads the OPPOSITE of what I expected

**Symptom.** KI-51's new guard reports `party_alive` so a reader can see *why* "whiteout" is the
diagnosis. Its first live firing printed **`party_alive=6/6`** — a full, healthy party — beside the
words "almost certainly a WHITEOUT".

**Root cause.** A whiteout **heals the party**. The field reads full precisely BECAUSE the thing
happened, so it corroborates nothing; the diagnosis rests entirely on the map having changed. I
chose the field by asking "what would show the party lost?" instead of "what will this field
actually read at the moment the message prints?".

**The fix that worked.** Kept the field (it still rules out "the party is dying right now") and
documented that 6/6 does not contradict the whiteout call, so the next reader does not spend time
reconciling them.

**Prevention rule.** *Before putting a field in a failure message, predict the value it will hold
AT THAT MOMENT — not the value that would have made the failure obvious. A field that always reads
healthy at the point of failure is decoration, and a misleading one if it looks like evidence.*

---

## 2026-08-11 — I read two losses as a RATE, wrote "wins 1 in 3", and launched a retry loop against a deterministic failure

**Symptom.** The Magma Hideout chapter won once (2026-08-10) and then lost twice. I recorded that
as KI-50 "reaches Maxie 3/3, **wins 1/3**" — a rate — and started an 8-attempt retry loop to roll
the dice until it won.

**Root cause.** It is not a rate. **All three losing runs are byte-identical** — 41 unique `[TURN]`
lines, md5 `07f99a10ac8b`, same HP, same PP, same Camerupt heal on the same turn. A `.ss1` replays
identical frame timing, so the current `magma_door.ss1` does not *sometimes* lose, it **always**
loses. The single win was on the same filename holding **different bytes**: `magma_door.ss1` is
re-captured by `--driver magmatravel` on every success, and a run at 22:05 on 2026-08-10 overwrote
the winning-era save.

‼ **This is the SAME fixture-overwrite hazard that had killed the `#24-teachmsgstall` repro earlier
the same day**, on a completely different question — and I walked into it again within hours of
writing the prevention rule for it. Writing a rule down is not the same as applying it.

**The fix that worked.** md5 the telemetry across runs before believing a rate. Preserve the losing
state as `saves/magma_door_losing.ss1` (nothing writes to that name) — a boss fight that loses
identically every time is an excellent fixture, not just a nuisance. Re-mint `magma_door.ss1` via
`--driver magmatravel` rather than retrying the dice.

**Prevention rules.**
1. *Before treating repeated failures as a RATE, prove the runs DIFFER. Identical telemetry means
   n=1 no matter how many times you ran it — and a retry loop against a deterministic failure is
   pure waste (8 attempts here would have been ~80 minutes for eight identical losses).*
2. *When a result changes and the save filename did not, check the save's BYTES/mtime before
   theorising about the code. Same name ≠ same fixture.*

---

## 2026-08-11 — I "pinned" a repro fixture AFTER a background job had already overwritten it, and voided my own A/B

**Symptom.** The KI-52 live A/B (pre-fix vs fixed, on the save that wedged twice byte-identically)
came back with **both arms winning the chapter**. No wedge, no `[KI-52]` line — nothing to compare.

**Root cause.** The wedging save was `magma_door.ss1` = **`8171734228f3`** (round 2's mint). I
stopped the mint loop after round 2 — but **round 3's `magmatravel` had already started and
completed its capture**, overwriting `magma_door.ss1` with `273d19b34d96` at 10:00. At 11:01 I
copied that file to `magma_door_ki52.ss1` believing it was the wedging save, and **md5'd the copy
without ever comparing it to the md5 of the run that failed.** The A/B therefore ran on a save that
does not reproduce the bug.

‼ **This is the THIRD time in one day** the same fixture-overwrite hazard has bitten (the
`#24-teachmsgstall` repro; KI-50's "1 in 3"; now this) — and this time **I had already written the
prevention rule and even pinned the file.** Pinning was not the missing step. Verifying *which
bytes* I pinned was.

**The fix that worked.** Compare the pinned copy's md5 against the md5 recorded for the failing
run, and refuse to run the A/B if they differ.

**Prevention rule.** *Pinning a fixture is not "copy the file now" — it is "copy the file and
assert its md5 equals the one the failure was measured on". Any background job still running can
have replaced it, and `cp` will happily preserve the wrong bytes. Record the md5 IN the A/B
command, not just beside it.*

‼ **Corollary, learned the hard way:** stopping a monitor/loop does not stop the work already in
flight. Round 3's capture landed **after** I called TaskStop.

---

## 2026-08-11 — RETIREMENT NOTICE #2: what the new gates actually retire, and what they do NOT

Following the 2026-07-25 precedent (R1-R4). Same bar: a rule is **RETIRED** only when a structural
guard makes its mistake genuinely unreachable — not when a tool merely makes it *easier to notice*.

‼‼ **THE HONEST HEADLINE, STATED FIRST BECAUSE IT IS THE MOST IMPORTANT PART.** The 2026-07-25
retirements were earned by guards that made an error **unreachable** (`_done()` raises on a phantom
name; `gemini_relay.py` refuses a weak model). **Most of today's tools do not do that — they
DETECT, loudly, and only if someone runs them.** Detection is a large improvement over an advisory
sentence, but it is a weaker claim, and inflating it would be exactly the "confident wrong
statement" this project's north star forbids. Classified accordingly.

### R5 — RETIRED (scoped): "do not add a bare `except` that swallows the error"
*(entries: 2026-07-23 "a silent except turned a scope bug into 252 wasted encounters"; 2026-08-03
"a bare `except Exception` hid a NameError for two batches"; 2026-07-30 "a test stub disabled the
logic under test, SILENTLY — the second time")*

`repro_no_silent_except.py` AST-scans `modules/story/`, the battle strategies and
`battle_action_selection.py`, and **fails if the count of silent handlers RISES**. A NEW silent
`except` in that scope now breaks the gate. The rule does not need to be remembered to be obeyed
there.

‼ **SCOPE IS THE WHOLE CAVEAT, AND IT IS NARROW.** This is a **ratchet at 140 of 203 (69%)**, not a
clean slate — the existing 140 are still silent, 99 of them in `early_game.py`. And the scan does
**not** cover `tools/story-dev/` probes, repros or `plugins/` beyond the listed file — where two of
the three cited incidents actually happened. **KEPT for everything outside the scanned scope:** *a
guard that cannot distinguish "no" from "I broke" is worse than no guard.*

### R6 — PARTIALLY RETIRED: "check whether this was already built and disproven before proposing it"
*(entry: 2026-08-11 KI-54 — I recommended "roster hygiene before bosses", a feature already built,
measured harmful and pinned off; only a manual pre-build check caught it)*

**Retired: the discovery half.** The measurements used to live in code comments
(`pc_trip.py`, `story_mode.py`) where nobody looks before *proposing* a feature. They are now in
`29-DISABLED-FEATURES-REGISTRY.md`, and `lint_docs.py`'s R6 **fails** if any `POKEBOT_*` flag in bot
code is missing from it — so the registry cannot silently go stale. It found an 11th flag on its
first run that a hand grep had missed.

**KEPT: the looking half.** Nothing forces an agent to *read* the registry before proposing work.
The rule stands as: **before proposing a feature, check `29-DISABLED-FEATURES-REGISTRY.md`** — now
with the guarantee that it is complete.

### R7 — NOT RETIRED, DOWNGRADED TO A TOOL POINTER: the fixture rules
*(entries: 2026-08-11 ×3 — the invalidated "cheap repro"; "wins 1 in 3" read off byte-identical
runs; a fixture pinned AFTER a background job overwrote it)*

`verify_fixtures.py` + `FIXTURES.md5` make PINNED drift **exit 1**, `preflight.py` runs it at
session start, and `--assert name=md5` puts the check inside the measurement command.

‼ **But none of that is unreachable-by-construction.** A measurement run without `--assert`, or a
session that skips preflight, fails exactly as before. So the rules are **kept**, restated as
mechanics instead of vigilance:
* run `preflight.py` before touching anything;
* put `verify_fixtures.py --assert <name>=<md5> && …` in front of any measurement that depends on
  specific bytes;
* **prove runs DIFFER before calling repeated failures a RATE** — md5 the telemetry. *Nothing
  enforces this one at all;* it remains pure advisory and it cost a published wrong result today.

### R8 — NOT RETIRED: "the docs described a two-folder project; the code has been three for ten days"
*(entry: 2026-07-27)*

`lint_docs.py` R1-R3 catch **archive formation inside a current-state file** — a different failure
from **doc-versus-CODE drift**, which nothing checks. A doc can be perfectly structured and
completely wrong. **Rule kept in full.**

---

### ‼ WHAT THIS NOTICE CHANGES IN PRACTICE
Two rules get shorter (R5 within its scope, R6's discovery half). Everything else becomes *a
pointer to a command* rather than a habit to hold in mind — which is the real reduction, since a
command can be run by anyone and a habit cannot be inherited.

**If any guard named here is removed, its rule becomes live again.**

---

## 2026-08-11 — I built a control out of a journey the instrument was structurally unable to reproduce

**Symptom.** `probe_hideout_warp_graph.py`'s POSITIVE CONTROL was "the inbound journey §Ch15
actually drove must be findable in the graph". It failed on the first run, so the probe withheld
its verdict — correctly, but for the wrong reason. Nothing was wrong with the graph.

**Root cause.** The first leg of that journey, `1F (10,34) -> (25,34)`, is opened by two **Strength
pushes**. The graph's walk edges come from `calculate_path`, which models no pushes at all. I had
picked a control the instrument could never pass no matter how correct it was, so its failure
carried no information about the thing under test.

**The fix that worked.** Move the control to the **ascent** `1F (25,34) -> 4F` — the part of the
same driven journey that is plain walking and warps. It passed in 5 hops and matched §Ch15's route
exactly, and the real verdict followed immediately.

**Prevention rule.** *A control must be something the instrument could pass if the thing under test
is healthy — never a case that depends on a capability the instrument does not have.*

---

## 2026-08-11 — I called KI-56's cause wrong out loud, then the measurement refuted me (and that was the point)

**Symptom.** Reading that KI-56's evidence was a *same-map* path failure, and that
`calculate_path`'s docstring says *"It is not able to use warps"*, I concluded mid-session that the
strand was probably a **routing gap** on a warp-joined map rather than the Strength-boulder reset
KI-56 blamed. It was not. The warp graph reaches 18 of 20 nodes from the stranded tile; the boulder
reset is the cause, exactly as written.

**Root cause.** A true premise (the planner cannot use warps, so a same-map failure is ambiguous)
carried me to an unmeasured conclusion. Ambiguous evidence means *the question is open*, not *the
other answer is right*.

**The fix that worked.** Building the instrument that could tell the two apart, with a control that
would expose it if it were lying. The refutation is worth more than the guess would have been: the
old entry could only say "this same-map path fails", the new one says "no walk-out exists anywhere
in the eight-map graph", which is what let option 2 be closed for good and the fix be committed to.

**Prevention rule.** *When an existing finding rests on an inference, the move is to build the
instrument that separates the alternatives — never to re-label the finding from the armchair.*

---

## 2026-08-11 — `audit_flag_names.py` told me a deliberately misspelled flag name was valid

**Symptom.** To check the Magma Hideout item-ball flag I ran
`audit_flag_names.py ITEM_MAGMA_HIDEOUT_3F_3R_ECAPE_ROPE ITEM_MAGMA_HIDEOUT_3F_3R_ESCAPE_ROPE`.
It printed **"all names valid"** — for two names, one of which does not exist.

**Root cause.** The tool takes **no arguments**. It audits two hardcoded source files and silently
ignored my argv; "all names valid" was a true statement about `early_game.py` and `story_mode.py`,
and nothing at all about what I asked. A tool that ignores input looks identical to a tool that
approves it.

**The fix that worked.** Check a single name against the table directly:
`grep <NAME> sandbox-pokebot/modules/data/event_flags/emerald.txt`. That showed flag **1059** is
`ITEM_MAGMA_HIDEOUT_3F_3R_ECAPE_ROPE` — ‼ **the decomp misspells "ESCAPE" as "ECAPE" and our table
carries the typo through.** The correctly-spelled name does not exist, and unknown names read
`False` **silently** — so the sensible spelling would have been a permanent, invisible lie meaning
"the item ball is still there".

**Prevention rule.** *Before trusting a tool's PASS, confirm it actually consumed your input —
`audit_flag_names.py` audits fixed files and ignores argv; single names go to the table by grep.*

---

## 2026-08-11 — a consumed item is NOT the end of the script that consumed it (the Strength lesson, again, for items)

**Symptom.** The new Escape Rope exit ran, the rope count went 1 -> 0, and the bot then sat on the
same tile for 1800 frames with `controllable=False`. It looked like the game had refused the item —
except a refused item is not consumed.

**Root cause.** `ItemUseOnFieldCB_EscapeRope` (decomp `src/item_use.c:903`) calls
`DisplayItemMessageOnField(taskId, gStringVar4, Task_UseDigEscapeRopeOnField)`, and
`StartEscapeRopeFieldEffect()` runs only from that **callback** — which fires when the message is
DISMISSED. My wait loop only `yield`ed, so it waited for ever on a text box. This is the *same
shape* as the `EventScript_ActivateStrength` bug already recorded above ("a flag set by a script is
not the end of that script"), which I had read, quoted in a comment in the very same file, and
still walked into from the item side.

**The fix that worked.** Press **B** every 4th frame while waiting for the map to change. B
dismisses a message and interacts with nothing; A would have talked to whoever is standing on the
far side of the warp.

**What made it cheap.** The harness's no-progress dump printed the active task list, and
`Task_ContinueTaskAfterMessagePrints` was sitting in it. Reading the dump cost seconds; guessing
would have cost runs.

**Prevention rule.** *If a wait loop can only be satisfied by a script ADVANCING, it must press
something — waiting harder never dismisses a text box.*

---

## 2026-08-11 — my driver crashed at frame 30 and the log looked exactly like a hung bot

**Symptom.** The first `--driver magmaexit` run produced no `[mhexit]` output for ten minutes.
Redirected stdout held two setup lines; the process was alive but using ~11 CPU-seconds. It read as
a bot stuck somewhere early.

**Root cause.** Two things stacked. (1) `map_name` is a **local helper redefined inside each
driver** in `story_harness.py`, not a module-level function; my new driver used it without defining
it and died at frame 30 with `NameError`. (2) The harness caught that, dropped to **Manual mode**,
and went on emulating — filling the log with heartbeats and `NO-PROGRESS` dumps, which is precisely
what a genuinely wedged bot looks like. Meanwhile the redirected stdout was still buffered and
showed nothing at all.

**The fix that worked.** Reading `tools/story-dev/harness_sandbox.log`, which `log()` **flushes on
every line** — the traceback was sitting at line 6 the whole time.

**Prevention rule.** *Diagnose a stalled run from the flushed `harness_sandbox.log` and grep
`EXCEPTION` FIRST — redirected stdout can be minutes behind, and a crashed driver in Manual mode is
indistinguishable from a hung bot.*

---

## 2026-08-11 — I derived a route constant from `map.json` in the WRONG ERA, and the previous chapter is what invalidates it

**Symptom.** §Ch16 leg 1 targets `SLATEPORT_HARBOR_DOOR_APPROACH = (28,13)`, described in its own
comment as "the plain walkable tile below the door — and the harbor's own `setescapewarp` return
tile, **so it is guaranteed to exist and be standable**". Driven, it was neither: Capt. Stern was
standing on it, and the leg died with `UnreachableDestinationError`.

**Root cause.** The tile is standable *in the era `map.json` describes*. `SlateportCity_OnTransition`
calls `MovePeopleForSternInterview` whenever `VAR_SLATEPORT_CITY_STATE == 1`, whose first line is
`setobjectxyperm LOCALID_SLATEPORT_CAPT_STERN, 28, 13`. ‼ **And the previous chapter sets that var** —
`MagmaHideout_4F_EventScript_Maxie` sets `SLATEPORT_CITY_STATE` and un-hides Stern and Gabby & Ty.
**Completing Ch15 spawns the thing that blocks Ch16.**

The bitter part: the Ch16 constants block already carried the warning, four lines further down —
*"`OnTransition` REWRITES THIS MAP ... so `map.json`'s object list is NOT what will be standing
there. Do not derive walkability around objects from the static file."* It was written about the
HARBOR map and not applied to the CITY map in the same chapter.

**The fix that worked.** None yet — it is recorded as KI-57 with the measurement, because the
obvious fix does not work either: `(28,13)` is a one-tile neck, so every reachable tile near the
door is in a different component from the door's neighbours. Picking another staging tile cannot
help. A second, unused harbor entrance (warp 9 at `(40,7)`) is a LEAD, and wiring it in on today's
evidence would be the same mistake again.

**Prevention rule.** *A route constant on a map the PREVIOUS chapter's completion touches must be
derived in the era the bot will actually stand there — check every `setobjectxyperm` reachable from
that map's `OnTransition` before trusting a tile is empty.*

---

## 2026-08-11 — I hunted for a route around a blocked tile when the game's answer was "talk to him"

**Symptom.** §Ch16 leg 1 could not reach the Slateport Harbor door. I measured the geometry, found
Capt. Stern parked on the only tile touching the door, confirmed no alternative staging tile
existed, and wrote KI-57 concluding the door was **sealed** — with a "lead" about a second harbor
warp at `(40,7)` that turned out to be a boat dock surrounded by water.

**Root cause.** I treated a story NPC as terrain. `SlateportCity_EventScript_CaptStern` — *talking
to him* — plays the interview scene and ends with `removeobject`, `setvar VAR_SLATEPORT_CITY_STATE,
2` and `warp MAP_SLATEPORT_CITY_HARBOR, 11, 14`. The script **carries the player inside**, to the
same tile the door warp uses. The blocked door was not a bug to route around; it was the game
telling me which way in it wanted.

**What should have tipped me off sooner, and did eventually.** The measurement implied the game
soft-locks its own next beat, in the exact era the game itself creates. When a measurement says
that, the measurement is the suspect — and the missing piece is almost always a SCRIPT.

**The fix that worked.** `grep` the map's own `scripts.inc` for the blocking object's `LOCALID_`
before designing any route. One grep produced the whole answer.

**Prevention rule.** *When an NPC blocks a required path, read that map's scripts for its
`LOCALID_` FIRST — a story NPC standing in a doorway is usually the intended trigger, not an
obstacle.*

---

## 2026-08-11 — `calculate_path` does not validate its SOURCE tile, and I published the artifact

**Symptom.** KI-57's first write-up reported that `(27,12)`, `(29,12)` and `(28,11)` were "walkable
tiles adjacent to the harbor door" that could "reach it in 1 wp" but lived in a different
component. All three are **walls**.

**Root cause.** `calculate_path(get_map_data(map, blocked_tile), destination)` returns a path
happily — it validates the destination side, not the source. Every "OK, 1 wp" in that table was
produced by asking for a route out of solid rock. Drawing the collision map showed it instantly.

**The fix that worked.** `probe_slateport_harbor_map.py` reads `collision` per tile and draws it,
with a control that the drawing must not contradict the planner.

**Prevention rule.** *A `calculate_path` result is evidence about the DESTINATION only — before
using a tile as a source, check its `collision` yourself.*

---

## 2026-08-11 — a chapter's test was GREEN because the run FAILED: the whiteout was healing it

**Symptom.** §Ch16 reported `ACCEPTANCE: PASS` on three consecutive runs, each also reporting
`whiteouts=1`. I logged the whiteout as "unmeasured" and moved on, because the chapter passed.

**Root cause.** The anchor `post_maxie.ss1` hands the chapter a party at **8.8% HP with five of six
members fainted** (Ch15 ends four floors underground right after Maxie). Leg 1 then walks a long
cross-region haul, loses a fight, and whites out — **and a whiteout fully heals the party**, so the
run recovered and completed. The PASS was not despite the failure, it was *because of* it, and the
post-chapter anchor read 100% HP for the same reason.

**The fix that worked.** Heal stops before the haul — but see the next entry for the part I got
wrong first. Result: `whiteouts=0`, still PASS, and 5,457 frames faster.

**Prevention rule.** *When a run reports both PASS and a recovered failure (whiteout, retry,
fallback), treat the PASS as unproven until you know the failure was not what made it pass — a
whiteout heals, and healing is exactly what a struggling run needs.*

---

## 2026-08-11 — I put the heal stop somewhere the party could not reach alive

**Symptom.** Having found the party arrives at 8.8% HP, I added heal stops at Mauville then
Slateport. The run still reported `whiteouts=1`, and both heals appeared in the log as having
executed successfully.

**Root cause.** The route to Mauville is a strict **prefix** of the route to Slateport, so nothing
about the journey changed before the fight: the run was **frame-identical to the unhealed one up to
f14345**, the exact frame of the original whiteout. The heals ran, but only after the whiteout had
already healed the party for free. I had fixed the symptom's location, not its distance.

**What made this cheap to diagnose.** The identical frame number. Two runs of a `.ss1` diverge as
soon as behaviour does, so *"the whiteout is at f14345 again"* proves the change had no effect
before that point — far stronger evidence than re-reading the code.

**The fix that worked.** Reorder nearest-first and put **Lavaridge** at the front — including
re-testing a route §Ch15 had recorded as impossible, because Ch15's measurement was taken from a
different component of the same map (`ROUTE112` north, at the cable-car station, versus the south
end where Jagged Pass exits).

**Prevention rule.** *A heal/resupply stop only counts if the party can REACH it in its current
state — order them nearest-first, and treat an unchanged failure frame as proof the change came
too late to matter.*

---

## 2026-08-11 — I asserted the warp table's coordinates as the LANDING tile, and every door failed

**Symptom.** §Ch17's first driven run reported
`Could not enter the warp at (22, 1) on AQUA_HIDEOUT_1F ... Last navigation error: None`, ending at
`AQUA_HIDEOUT_B1F (29, 2)`. The message says the warp could not be entered. The warp had worked
perfectly — the bot was standing on the other side of it.

**Root cause.** §Ch17 grades each maze hop on the exact arrival tile (correct, and necessary: most
hops are `B1F -> B1F`, so a map-level test cannot tell them apart). I took the expected tile
straight from the ROM warp table — `B1F (29,1)` — but **a warp table entry gives the coordinates of
the destination WARP, not where the player ends up.** For door-type warps Gen 3 places the player
on the tile in FRONT of the door; only ladders and stairs land exactly on it. So the assertion was
off by one on every door, and `_enter_warp_by_navigation` dutifully retried a warp that had already
succeeded until it ran out of tries.

**The fix that worked.** `_aqua_at()` allows one tile of slack around the predicted arrival. Still
unambiguous for this maze because B1F's panels are three or more tiles apart — the tolerance was
checked against the geometry rather than just assumed safe.

**Prevention rule.** *A warp table gives the destination WARP's tile, not the landing tile — allow
one tile of slack when asserting an arrival, and check that slack cannot merge two nearby warps.*

---

## 2026-08-12 — my warp-maze route told the bot to walk over a warp panel

**Symptom.** The first Master Ball run collected the ball and then failed on the return leg:
`Could not enter the warp at (48,13) ... Could not find a path from (45/9)`. The bot was at
`(45,9)`; the route expected it at `(42,13)`.

**Root cause.** Leg B walked `(42,13) -> (48,13)`, and `(45,13)` sits between them — **itself a warp
panel**. `calculate_path` treats panels as ordinary walkable ground, so it happily plotted a route
across one; the bot stepped on it and was teleported. The chapter code was right and its
tile-level assertion caught the problem immediately. **The GRAPH was wrong**: it had been building
walk edges from paths it never inspected.

**The first fix that did NOT work.** I filtered on `Waypoint.is_warp`, which reads like exactly the
right field. It changed nothing, because `map_path.unroll_path` guards the warp branch with
`len(result) == 0` — **`is_warp` is set only on the FINAL waypoint of a path**, so an intermediate
panel is reported as ordinary ground by that flag too.

**The fix that worked.** Compare each intermediate waypoint's COORDINATES against the map's own
warp table (already read from ROM for the graph), and reject the edge if any of them is a panel.
The destination is exempt — firing it is the point of the hop. Re-derived, leg B changed from
`(48,17)/(48,13)` to `(45,17)/(48,9)/(45,3)` and the run passed.

**Prevention rule.** *In a warp-panel maze, a "walk edge" is only real if the PATH avoids panels —
check the waypoints' coordinates against the warp table, and do not trust `Waypoint.is_warp`, which
is set only on the last waypoint.*

---

## 2026-08-12 — I wrote a confident wrong cause into a known-issue, from a metatile name

**Symptom.** `probe_warp_maze.py` could not route the Mossdeep Gym. I read the tile behaviour,
saw `'Mossdeep Gym Warp'` (`MB_MOSSDEEP_GYM_WARP`), and wrote KI-58 saying the gym "is not a
warp-event maze" because those tiles "choose a destination from gym-specific logic". I even added a
warning not to extend the tool until that was resolved.

**Root cause.** I inferred a mechanism from a NAME. The decomp says the opposite: that behaviour
sits in the same `IsWarpMetatileBehavior` list as `MetatileBehavior_IsAquaHideoutWarp` — the panels
my graph already handled — and `DoMossdeepGymWarp()` is an ordinary warp with a different fade and
`SKIP_OBJECT_EVENT_LOAD`. The destination is still the warp event's. **The warp model was never
wrong.** A distinctive name felt like an explanation, and I stopped looking.

**The real cause, found by disagreeing with myself.** `probe_gym_components.py` flood-fills the
collision map and cross-checks the planner. The two models disagreed on *exactly* the two failing
links (flood: connected, planner: no), which located it in one run: an
`OBJ_EVENT_GFX_TRICK_HOUSE_STATUE` template sits on each — `(11,5)` and `(12,34)`. The gym has 21
statue tiles and they are the puzzle's barrier walls, so the planner was right all along.

**And the lesson that generalises past this bug.** `map_path.is_tile_accessible` blocks any tile
whose object template is not in `active_objects`, and `active_objects` comes from the **currently
loaded** map. So static recon from a foreign anchor treats every object-template tile as a wall —
**static recon of an object-dense map is PESSIMISTIC**, the opposite of the caveat we had written on
every probe ("static may call a walled tile walkable"). Both directions happen.

**Prevention rule.** *Never infer a mechanism from a metatile/flag NAME — read the function it
dispatches to. And when two models of the same map disagree, that disagreement is the fastest
diagnostic you have; build the second model rather than re-reading the first.*

---

## 2026-08-12 — my model-free brute force was ALSO wrong, because it changed the map while measuring it

**Symptom.** After four offline models each said "no route through the Mossdeep Gym", I built
`probe_gym_bruteforce.py` — press a button, read where the avatar went, no map model at all — on the
reasoning that it *cannot* be wrong about the map. It found 35 tiles and **zero** warp panels, and
failed its own known-good control. I fixed a real bug in its stepper (two blind presses move two
tiles) and got the identical result, which should have told me the stepper was never the problem.

**Root cause.** The gym is a rotating-tile statue puzzle: nine floor switches move the statues. The
walker was **stepping on switches while exploring**, so the map mutated underneath it — and because
its state key was only `(map, position)`, two genuinely different worlds collapsed into the same
node and the search truncated. An empirical instrument is only immune to *modelling* error; it is
not immune to having the wrong notion of STATE.

**The fix that worked.** Widen the state key to include the live object positions
(`get_map_objects()`), so `(position, statue configuration)` is the node. No arrow-band model needed
— the game moves the statues, we just read where they went.

**Prevention rule.** *When the world can change in response to what you do, the search state must
include the world — "I only pressed buttons, so I cannot be wrong" protects you from bad map models,
not from a state key that is too small.*

---

## 2026-08-12 — four models agreed and all four were wrong, because they shared a blind spot

**Symptom.** Warp-graph BFS, a collision flood fill, `calculate_path` spot-checks, and a
statue-aware re-run all concluded the Mossdeep Gym has no route to Tate & Liza. I had written KI-58
twice with two different wrong causes before this.

**Root cause.** Every one of them modelled the gym as *walk + warp*. The gym has a **third movement
primitive** — step on a floor switch to relocate the statues — and no amount of agreement between
models that lack it could ever surface it. This is the project's own measured rule about Gemini
("agreement is not a confidence signal; both models share the same misconceptions") applying to my
own instruments, which I had not thought to apply to myself.

**The fix that worked.** Fan out to five INDEPENDENT researchers with different angles, one of them
explicitly adversarial ("refute this claim"). The adversarial one found it, and two others
converged on it separately from the decomp. Then verify in our own harness before believing it.

**Prevention rule.** *When N of your own instruments agree on something impossible, stop adding
instruments of the same kind — they likely share a missing primitive. Ask what the game can DO that
none of them models, and get an adversarial second opinion.*
