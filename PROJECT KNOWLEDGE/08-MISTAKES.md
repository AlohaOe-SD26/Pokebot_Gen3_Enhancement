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
