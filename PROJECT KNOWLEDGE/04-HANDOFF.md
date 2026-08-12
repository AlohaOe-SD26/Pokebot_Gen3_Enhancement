# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-08-12 — read "‼ YOU ARE HERE" immediately below.
Every banner further down is HISTORY, newest first.

---
# ‼ YOU ARE HERE — 2026-08-12 (end of a very long session). Read this, then `14-AGENT-PLAYBOOK.md`.

## WHAT THIS IS
`sandbox-pokebot/` is the working build of a Pokémon Emerald bot. Its **Story mode** plays the game
autonomously from Littleroot. `40cakes repo/` is a pristine upstream mirror (never edit);
`custom-pokebot/` is the promoted fork. **All work happens in `sandbox-pokebot/`.**

‼ **CLAUDE SUBAGENTS ARE STANDING-APPROVED** for research and assistance (user directive
2026-08-12, in `CLAUDE.md`). Use them freely — fan out on different ANGLES in ONE message, include
one explicitly ADVERSARIAL, tell them what is already ruled out, and keep working while they run.
**Their output is a NOTE, never truth**: verify the load-bearing claim in our own harness. That is
how KI-58 was cracked after four of my own models failed.

‼ **READ `01-VISION-AND-DESIGN.md`'s NORTH STAR FIRST if you have not.** The user restated the goal
on 2026-08-11: (1) a bot that plays Emerald **organically and faithfully, as a human would**, and
(2) **a documented substrate for a future self-training AI agent**. Goal 2 is why the documentation
burden here is so heavy, and why negative results are treated as the most valuable asset.

## STATE
| | |
|---|---|
| branch / HEAD | `main`, **clean, 0 unpushed** |
| box | **IDLE.** Nothing running. Last batch `20260811-130454` (VERDICT OK, 28 runs). |
| story content | ✅ **§Ch18 COMPLETE 2026-08-12 — the MIND BADGE is won and wired into the ladder. 19 of 24 beats.** Littleroot → 6 badges → Mt. Pyre → Magma Hideout (and out) → Slateport submarine theft → **the Lilycove AQUA HIDEOUT (with the MASTER BALL)**. (was 18 of 24 before Ch18.) |
| ‼ is code frozen? | **No.** Nothing is running. |
| upstream | checked **2026-08-12**, still `5dd898f8` — no change. Daily check DONE. |
| restore point | **`restore/2026-08-11-all-promoted`** (annotated, pushed, verified on the remote) |
| sandbox ↔ custom drift | ‼ **§Ch18 IS IN SANDBOX ONLY — NOT PROMOTED.** `modules/story/mossdeep_gym.py`, `modules/story/mossdeep_gym_puzzle.py`, Segment 18 in `plugins/custom_modes/story_mode.py`, and the three `mossdeep*` drivers exist only in `sandbox-pokebot/`. Promotion needs the user's approval AND a driven `--build custom` check, never a diff. Everything BEFORE Ch18 is drift-free: — §Ch15 exit + §Ch16 + §Ch17 + heal stops + the MASTER BALL all PROMOTED 2026-08-12 (user-approved); the first promotion was verified by driving `--build custom` to an identical frame count |
| **if stopped mid-task** | **NOTHING IS PARKED.** Everything is committed and pushed. Start at "NEXT ACTIONS". |

## ✅ WHAT SHIPPED THIS SESSION (2026-08-11 → 12)
The story ladder went **16 → 19 of 24 beats**.

‼ **§Ch18 (items 5, 6 and the block below) is COMMITTED AND PUSHED BUT *NOT* PROMOTED to
`custom-pokebot/`.** Items 1-4 below were promoted on 2026-08-12 with the user's approval, verified
by driving `--build custom` to a frame-identical PASS. **§Ch18 has had no such approval and no such
verification — the sandbox↔custom drift row above is stale the moment you read it.** Promotion is
the user's call, and it needs its own driven check in `custom-pokebot`, not a diff.

1. **KI-56 FIXED — §Ch15 now LEAVES the Magma Hideout.** It used to pass its own binary test on
   runs that ended permanently stranded. No walk-out exists (18 of 20 warp-graph nodes reachable,
   the exit not among them); fixed with the **Escape Rope the dungeon itself provides**. Driven
   PASS, landing on the exact tile predicted from `escapeWarp` beforehand.
2. **KI-57 FIXED — §Ch16 (Slateport) COMPLETE.** ‼ Beating Maxie *parks Capt. Stern on the only
   tile touching the harbor door*: Ch15's own success spawns Ch16's blocker. The answer was not a
   route but a conversation — talking to him `warp`s the player inside. Driven PASS x3.
3. **§Ch17 (Lilycove Aqua Hideout) BUILT + the MASTER BALL.** An 18-hop warp-panel maze solved from
   the ROM warp table. ‼ The Master Ball can't be taken directly — both free neighbours are
   unreachable — so the route takes the **Nugget** first and steps onto the tile it vacates. Driven
   PASS with `master_balls=1`.
4. **The Ch16 haul whiteout FIXED** (`whiteouts` 1 → 0, and faster). The anchor hands the chapter a
   party at **8.8% HP, 5 of 6 fainted**, and the chapter was passing only *because a whiteout
   heals*. Heal stops are now nearest-first.
5. **§Ch18 leg 1** — `--driver mossdeeptravel` Surfs Lilycove → Mossdeep and enters the gym
   (PASS, `whiteouts=0`), capturing `saves/in_mossdeep_gym.ss1`.
6. **KI-58 RESOLVED — the Mossdeep Gym is a ROTATING-TILE STATUE PUZZLE**, not a maze (see below).
7. **KI-59 + KI-60 filed** — two latent bugs in the SHARED pathfinder, code-verified, deliberately
   **not** fixed. `#24-impassabledirs`, `#24-pathsourcecheck`.
8. **`#24-grounditems` groundwork** — `collect_item_ball()` is now shared by three callers;
   `#24-npcgifts` and `#24-masterball` added on your direction.
9. **New tools:** `probe_warp_maze.py` (generalised, self-checks against a DRIVEN route),
   `probe_gym_bruteforce.py` (model-free walker), `probe_gym_components.py`, `probe_escape_warp.py`,
   `probe_hideout_warp_graph.py`, `probe_slateport_harbor_map.py`, `repro_hideout_exit.py`.
   `probe_anchor_inventory.py` now prints **party HP** — it immediately flagged three anchors as
   "cannot survive a journey".

## ✅ AND THEN, LATER ON 2026-08-12 — §Ch18 BUILT, DRIVEN, FIXED AND WIRED (ladder 18 → 19 of 24)
10. **The Mossdeep Gym puzzle is SIMULATABLE and the model is VALIDATED.**
    `modules/story/mossdeep_gym_puzzle.py` predicts every object's tile after a switch press;
    `probe_gym_simulate.py` made the GAME grade it — **11/11 loaded objects, identity-keyed on
    `local_id`** — and caught a completely wrong model on its first run. Method written up as
    playbook **§4b**.
11. **The route is SOLVED and DRIVEN.** BFS over `(player tile × every object position)` →
    **117 steps**, matching two independent agent routes switch-for-switch.
    `--driver mossdeepgym` → `at_leaders=True at=(23,8) whiteouts=0`, one plan, zero re-plans.
12. **§Ch18 COMPLETE.** `--driver mossdeepbadge` → `badge=True controllable=True whiteouts=0`,
    `BADGE07_GET` after 754 frames. **Segment 18 wired into the ladder.**
13. **‼ TWO REAL DEFECTS FOUND BY ADVERSARIAL AGENTS, NOT BY MY TESTS** — both invisible to a
    passing run: the whiteout path checked the map only at entry AND raised an error type the
    recovery could not catch (fixed, proven by fault injection, `repro_gym_whiteout_guard.py` 4/4);
    and **§Ch18 stranded the run on an eleven-tile island** while passing `badge + controllable`
    (fixed; **the acceptance now requires being out of the gym**).
14. **KI-61 FIXED** — the chapter registry had the Space Center BEFORE the gym, which made the
    progress detector skip two whole beats. A/B proven; the design doc's "order confirmed" was wrong.
15. **§Ch19 groundwork + measured hazards** (`space_center.py`, `probe_space_center_recon.py`,
    `probe_ch19_hazards.py`). **NOT built, NOT wired** — and it says so.
16. **KI-62, KI-63 filed.** KI-63 is a real blocker: **no party member can learn Dive and the party
    is full**, so `#24-pc` is a PREREQUISITE of §Ch21.

## ‼ THE TWO THINGS THAT MATTER MOST FROM THIS SESSION

**1. When N of your own instruments agree on something impossible, they share a missing primitive.**
Four instruments agreed the Mossdeep Gym had no route to its own leaders. All four modelled it as
*walk + warp*; the gym has a **third movement primitive** — floor switches that relocate 21 statues
and nine trainers. Even the model-free brute-force walker was wrong, because it *changed the map
while exploring it*. Five parallel Claude agents found it; the explicitly ADVERSARIAL one cracked it.

**2. ‼ EVERY DEFECT THAT MATTERED THIS SESSION WAS FOUND BY AN ADVERSARIAL AGENT, NOT BY A TEST.**
Three times: the statue model (caught by a validation gate I only built because the rule says to),
the whiteout path, and §Ch18 stranding the run. In each case my own runs were **green** — the
happy path cannot exercise an error path, and an acceptance test written by the same person who
wrote the code inherits the same blind spot. ⇒ *Spend the agents on REFUTING finished work, not
only on researching new work.* And: **write the predicted failure down BEFORE the run** — the
§Ch19 hazard checks did this and 3/3 held, which is how two traps got designed out instead of
debugged.

## ‼‼ THE BATCH RESULT — one thing resolved, one thing NOT
**RESOLVED — the status tax is real:** incapacitated turns lost **960/2,945 = 32.6%** vs a clean
control of **1,259/33,017 = 3.8%**. **8.5×, z = +62.2**, over 47,789 turns from 36 independent lane
logs. ‼ My earlier n=2 figure of 64.3% was **~2× too high** — one dungeon fight is not a rate.

**NOT RESOLVED — `#24-teachmsgstall` has no production effect and is REOPENED:**
teach success **38/47 (80.9%)** vs **38/42 (90.5%)** pre-fix, **z = −1.28**; `post_select=exhausted`
**8/85** vs **3/80**, **z = +1.46**; and the new `already-advanced` exit fired **ZERO** times in 85
teaches. The one-frame window was real but was **not the dominant production cause**. The fix stays
(it closes a real hole and costs nothing); **there is another path to `exhausted`.**

**NO EVIDENCE EITHER WAY:** KI-51 and KI-52 never fired in the batch (0 events). Still unmeasured.

## 🛡 THE HARDENING ROUND — advisory rules → code that refuses
Driven by the finding that **≥12 of 164 logged mistakes are self-admitted REPEATS**, several
committed while the author knew the rule. **Run `preflight.py` before touching anything.**
| tool | what it does |
|---|---|
| `preflight.py` | one gate: git sync + fixtures + docs + live-batch detection. **Exits 1.** |
| `lint_docs.py` | CLAUDE.md's doc rules enforced (R1-R6). Cut `04-HANDOFF` from 3,240 → 167 lines |
| `verify_fixtures.py` (+`--assert name=md5`) | PINNED saves byte-identical; put the assert **in** the measurement command |
| `repro_no_silent_except.py` | RATCHET at **140/203** silent handlers — may never rise |
| `29-DISABLED-FEATURES-REGISTRY.md` + lint R6 | every `POKEBOT_*` flag with its MEASUREMENT. **Check before proposing a feature** |
| `30-METRICS.md` | which instrument answers which question, at what n |
| `27-INJECTION-SURFACE.md` | how the bot observes/acts + the 8 timing traps (for goal #2) |
| `25-BACKUPS-AND-RESTORE.md` | restore points: naming, what a tag does/doesn't capture, recipes |
| `26-REVIEW-AND-HARDENING-PLAN-…md` | the full review: taxonomy, doc health, future path |

‼ **Three of these found real problems on their first run**: six competing START-HERE banners, an
**11th undocumented flag** (which turned out to be the roster blocker), and 140 silent handlers.

## ‼ WHAT THE USER DECIDED THIS SESSION
* **Promotions approved twice** (teach fix; then KI-51 + KI-52 + status telemetry).
* **"Roster hygiene before bosses"** approved as the boss-response direction — then found
  **BLOCKED** (KI-54): the box is empty, and the deposit path was already measured harmful.
  ‼ The real unlock is `POKEBOT_BOX_OVERFLOW_CATCH`, which is **one unhandled text box** away.
* **The boss-response design is still the user's call.** The status tax now has a resolved rate
  behind it, but a status response is a battle-policy change touching every mode — **do not build
  it unilaterally.**

## ✅ KI-56 (Magma Hideout strand) — resolved 2026-08-11, detail ARCHIVED

Full block moved to `28-HANDOFF-ARCHIVE.md`; the issue itself is in
`31-KNOWN-ISSUES-ARCHIVE.md`. ‼ Keep only this: its prevention rule — **a chapter's test must
include "and the bot can continue"** — was violated AGAIN by §Ch18 on 2026-08-12, which passed
`badge + controllable` while parked on an eleven-tile island. It is the most re-learned lesson
in this project. Read it before writing any chapter's acceptance test.

## ⏭ NEXT ACTIONS, IN ORDER

> **START HERE ON A FRESH CONTEXT.** Everything is committed and pushed; nothing is parked.
> 1. **Run `preflight.py`.** Then read this list and the **§Ch19 section below it**.
> 2. **The actual next build is §Ch19, the Mossdeep Space Center** — groundwork exists, hazards are
>    measured, and the one genuine unknown is the party-selection menu. Item 1 below is a *record*
>    that §Ch18 is finished, not a task.
> 3. Two things are the USER's call, not yours: **promoting §Ch18 to `custom-pokebot/`**, and the
>    **boss/status battle-policy** decision further down.
> 4. Before building anything, skim `08-MISTAKES.md`'s last ten entries — six were written today and
>    three of them are about tests that passed while the bot was broken.

1. **✅ §Ch18 IS DONE (2026-08-12) — the Mind Badge is won and Segment 18 is wired into the ladder.**
   The ladder now runs **19 of 24 beats**. Three drivers, all PASS:
   * `--driver mossdeeptravel` → Surf Lilycove → Mossdeep, enter the gym. Anchor
     `saves/in_mossdeep_gym.ss1`.
   * `--driver mossdeepgym` → solve the statue puzzle. `at_leaders=True at=(23,8) whiteouts=0`,
     117 steps in a single plan. Anchor `saves/at_mossdeep_leaders.ss1`.
   * `--driver mossdeepbadge` → the whole chapter. `badge=True at=(23,8) controllable=True
     whiteouts=0`, `BADGE07_GET` after 754 frames. Anchor **`saves/post_mossdeep_gym.ss1`**.

   ‼ **TWO PATHS REMAIN UNEXERCISED, and neither should be described as tested.** (a) The
   executor's own `_ride_out_interruption` branch logged **zero** times — the trainer battles that
   fired were handled by the standard `TrainerApproachListener` / `BattleListener`. (b) The **real
   whiteout path**: both runs had `whiteouts=0`, so the recovery is proven only by fault injection
   (`repro_gym_whiteout_guard.py`), never by a live loss.

   ‼ **WHAT ADVERSARIAL REVIEW CAUGHT THAT THE PASSING RUN COULD NOT.** `walk_to_the_leaders`
   checked the gym map only at entry and then reasoned in gym-local coordinates forever — a
   whiteout would have had it planning gym routes from Pokémon Center coordinates — and it raised
   `RuntimeError` where the chapter catches `BotModeError`, so the re-enter-and-re-solve recovery
   **could never have fired**. Both fixed. *A green happy-path run says nothing about error paths.*

   ‼ **AND §Ch18 WAS STRANDING THE RUN** — found later the same day, by the adversarial pass for
   §Ch19, *after* §Ch18 had been driven twice, committed and reported complete. It ended on
   `(23,8)`, part of an **eleven-tile island**; `calculate_path((23,8) → (7,35))` raises, and the
   only exit is the `(21,6)` **coord event** (invisible to any warp-graph solver). Fixed with
   `leave_the_gym()` — driven, now ends in `MOSSDEEP_CITY (38,10)` — and **the acceptance test now
   requires being out of the gym**, so the stranded version would fail. *This is KI-56's rule
   violated a second time in the session in which I re-read it.*

## ⏭ §Ch19 — the MOSSDEEP SPACE CENTER. GROUNDWORK DONE, NOT BUILT, NOT WIRED.

Start from **`saves/post_mossdeep_gym.ss1`** (re-captured: now standing in `MOSSDEEP_CITY (38,10)`,
7 badges, ‼ **66% HP with one Pokémon fainted** — heal FIRST).
`modules/story/space_center.py` holds the route and the first three legs and says plainly that it is
groundwork. `probe_space_center_recon.py` is the measured area atlas.

**Hazards were PREDICTED by an adversarial pass and then TESTED before building — 3/3 held**
(`probe_ch19_hazards.py`, keep it green):
* **The city is cut in two.** The five Team Magma NPCs the gym victory spawns occupy the ONLY land
  bridge (x=44, y=23-26). A single route gym → Space Center cannot exist. **Route to the cutscene
  trigger line first** — `(42,21) (41,22) (41,23) (41,24) (40,25) (40,26)` — ride the forced scene,
  **observe `VAR_MOSSDEEP_CITY_STATE == 2`**, then plan leg 2.
* **The 2F prompt must be answered with A.** It is a `MSGBOX_YESNO`; B answers NO, which warps you
  back to 1F **with the var unchanged** — an infinite re-entry livelock, healthy avatar, no error.
* **Completion is `VAR_MOSSDEEP_SPACE_CENTER_STATE == 3`.** ‼ NOT `FLAG_DEFEATED_MAGMA_SPACE_CENTER`,
  which the Rayquaza PokéNav call **clears again** ~250 steps later — a chapter graded on it would
  pass, then silently un-pass.
* **Steven must be talked to TWICE**, and leaving 2F resets that (his first talk is dialogue only —
  a bot waiting for a battle there will hang). The second talk opens a **party-selection menu**
  (`ChooseHalfPartyForBattle`, 1-3 mons) that **nothing in this codebase has ever driven**; blind
  A-mashing volunteers slots 0-2, i.e. Zigzagoon L15, into a fight with Maxie L42-44. **This is the
  one genuine unknown — instrument it on the first run rather than guessing.**
* **The multi battle puts Steven's Metang/Skarmory/Aggron into `gPlayerParty[3..5]`**, and our
  faint-replacer picks by party index — it can try to send out the ALLY's Pokémon. Losing calls
  `SetCB2WhiteOut` directly.

⛔ **§Ch21 (Seafloor Cavern) IS BLOCKED — KI-63.** **No party member can learn Dive and the party is
full** (measured: 0 learners, 6/6). Receiving HM08 is fine (a script gift needs no learner), so
§Ch19/§Ch20 are unaffected — but **`#24-pc` is a PREREQUISITE of §Ch21**, not a later nicety. The
natural single swap is a **Wailmer or Tentacool** (both learn Surf *and* Dive; Zigzagoon L15 is our
only Surf carrier).

⚠ **KI-59 is armed in the Seafloor Cavern** — 115 `Impassable *` tiles across Rooms 1-9, which
`map_path` over-blocks. That is the reproduce-map KI-59 asked for: fix it with an A/B on
`SEAFLOOR_CAVERN_ROOM1` **before** the cavern chapter exists.

   ✅ **`sandbox-pokebot/modules/story/mossdeep_gym_puzzle.py` simulates the puzzle offline**, and
   `probe_gym_simulate.py` **PASSES**: 11/11 loaded objects predicted on a live press, identity-keyed
   on `local_id`, plus a period-4 identity control on all five colours. Per-press object counts
   (Yellow 8, Blue 4, Green 3, Purple 10, Red 5) independently reproduce the decomp's pad occupancy
   table. **A route may now be planned on this model.**

   Encoding (derived from the ROM dump, not assumed): arrows are `0x250..0x27F`; band =
   `(mt-0x250)//8` → `0 Yellow 1 Blue 2 Green 3 Purple 4 Red`; code = `(mt-0x250)%8` →
   `0 Right 1 Down 2 Left 3 Up`; ‼ **codes 4/5 are that colour's SWITCH**. Movement is a **rigid
   simultaneous rotation with NO occupancy check**, so four presses of a colour is the identity.

   ‼ **THE THINGS THAT WILL BITE — all newly measured, all in KI-58:**
   * **Nine TRAINERS stand on arrow pads and rotate with the statues.** A statue-only model is wrong.
   * **Statues are `graphics_id == 224`** (21 of them), *not* `trainer_type == "None"`.
   * **"5 counters mod 4" is UNSAFE** — not every pad holds three objects. Use the object-position
     tuple (what the module does).
   * **Solving the puzzle AIMS THE TRAINERS AT YOU.** Pressing yellow at `(3,30)` slides Maura to
     `(4,30)`, adjacent and facing the player; the trainer intro fires before the bot can step off.
     **Expect gym battles as part of the mechanic**, and never write a wait loop that assumes no
     script will start.
   * **Three** switches are unavoidable transit tiles: `(23,24)`, `(23,21)`, `(8,10)`.
   * `(21,6)` ejects to `(7,30)` and is **not flag-gated**; treat as blocked. Leaving the gym RESETS
     the puzzle; internal warps preserve it (`SKIP_OBJECT_EVENT_LOAD`).
   * **No configuration is unsolvable** — 114,929 reachable states, 0 dead. The bot cannot strand
     itself here, which is a change from every dungeon so far.

   **HOW TO BUILD IT:** A\* over `(player tile, object-position tuple)` using
   `mossdeep_gym_puzzle.press` / `is_walkable`, with warps and forced switch tiles as edges. The
   116-step agent route in KI-58 is a **cross-check on the solver's answer, never the answer**. Then
   Tate & Liza at `(23,8)/(24,8)` facing NORTH: a **DOUBLE battle** needing **≥2 usable Pokémon**,
   and the party still carries Zigzagoon L11 / Skitty L17.

2. ✅ **DONE — the Slateport-haul whiteout is FIXED** (`whiteouts=0`, PASS, and 5,457 frames
   faster). Cause: the anchor hands Ch16 a party at **8.8% HP with 5 of 6 fainted**, and the
   chapter was passing only *because* a whiteout heals. Fix: `SLATEPORT_ROUTE_HEALS`,
   nearest-first (Lavaridge → Mauville → Slateport). ‼ **Three other anchors are in the same
   state** — `post_mtpyre` 11%/3 fainted, `post_winona` 29%/3 fainted — so any NEW chapter built
   on one inherits the same latent whiteout. `probe_anchor_inventory.py` now prints the HP line
   and says so. **Heal early in Ch17.**

3. **Optional hardening of the §Ch15 exit:** drive it from a run that walks back down to
   `1F (25,34)` rather than from 4F. The warp graph says 3F_3R is reachable from there, but only
   statically. `sandbox-pokebot/profiles/ch16a/current_state.ss1` is a free repro of that state.

3. **`#24-teachmsgstall` is REOPENED** — the fix has no production effect (z = −1.28) and
   `already-advanced` never fired. Start from `post_select=exhausted`, which still occurs 8/85.

4. **The boss-response decision is the USER's.** The status tax is now a resolved rate
   (32.6% vs 3.8%, z = +62.2), which is the evidence a status response needed — but it is a
   battle-policy change touching every mode using `DefaultBattleStrategy`. **Do not build it
   unilaterally.** ‼ And roster hygiene is blocked (KI-54) until
   `POKEBOT_BOX_OVERFLOW_CATCH` works — one unhandled text box.

5. **Remaining hardening (designed, not built):** H5 (make `n=` structural in every analysis probe)
   and H7 (a bounded-loop helper so an unbounded loop is a visible smell). See
   `26-REVIEW-AND-HARDENING-PLAN-2026-08-11.md`.

6. **Do NOT grade anything on the finish rate.** Eight batches, zero resolvable pairs. Use
   `30-METRICS.md` to pick an instrument before measuring.

## HOW TO RUN / TEST
```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 preflight.py          # ‼ RUN THIS FIRST. git + fixtures + docs + freeze
PYTHONUTF8=1 py -3.12 lint_docs.py          # doc rules (exit 1)
PYTHONUTF8=1 py -3.12 verify_fixtures.py    # PINNED saves byte-identical
PYTHONUTF8=1 py -3.12 probe_status_tax.py <batch-dir>   # the status tax, with its control
PYTHONUTF8=1 py -3.12 x4_headless.py --lanes 8 --minutes 180   # a batch (3h)

# --- §Ch18/§Ch19 (all exit 0 today; keep them green) ---
PYTHONUTF8=1 py -3.12 repro_gym_whiteout_guard.py   # 4/4, fault-injected  (~1 min)
PYTHONUTF8=1 py -3.12 probe_chapter_order.py        # KI-61 regression guard
PYTHONUTF8=1 py -3.12 probe_ch19_hazards.py         # 3/3; H1 is now a stranding guard
PYTHONUTF8=1 py -3.12 probe_space_center_recon.py   # §Ch19 area atlas (measured, not recalled)
PYTHONUTF8=1 py -3.12 probe_gym_solve.py            # re-derive the 117-step gym route

# --- drivers (these run under the REAL main loop, so they can fight) ---
PYTHONUTF8=1 py -3.12 story_harness.py post_aqua.ss1          --driver mossdeeptravel --frames 500000
PYTHONUTF8=1 py -3.12 story_harness.py in_mossdeep_gym.ss1    --driver mossdeepgym    --frames 400000
PYTHONUTF8=1 py -3.12 story_harness.py at_mossdeep_leaders.ss1 --driver mossdeepbadge --frames 300000
```
‼ **Never read an exit code through a pipe** — `| head` reports ITS status, not the script's. Write
to a file and echo `$?` (this nearly recorded a PASS that had never run).
‼ **A driver can fight; a hand-driven probe cannot.** Battle handling lives in the main loop's
listeners, not inside a bot mode's generator (`modules/battle_fault.py:5`).
**Regression gate — 15 of 15 green (2026-08-12):** plus `repro_gym_whiteout_guard.py` (4/4, fault-injected — ‼ it is a BOUNDED prefix test, because a hand-driven generator has no battle listeners and cannot win a gym fight; see 08-MISTAKES). Previously 14 of 14 (2026-08-11): the ten standing `repro_*` plus
`repro_teach_under_dialogue`, `repro_teach_prompt_window`, `repro_maxie_whiteout_guard`,
`repro_lead_cannot_battle`, and the `repro_no_silent_except` ratchet.
‼ `repro_counter_hunt` and `repro_area_item_gate` print `RESULT: ALL PASS` / `all checks pass.` —
grepping only for "ALL PASS" reports them as false failures.

## GOTCHAS (still true)
* **Never use the Grep TOOL on `tools/story-dev/x4-runs/`** — gitignored, ripgrep returns a silent
  zero. Use Bash `grep` and print the bytes searched as a control.
* **Event-var/flag names carry NO `VAR_`/`FLAG_` prefix**, and unknown names return `-1`/`False`
  **silently**. Membership-test first.
* **Report map identity as the `MapRSE` ENUM, never `map_name`** — that is a display label.
* **`.ss1` replays IDENTICALLY.** One fight repeated five times is still n = 1.
* **A save any driver re-captures is a CACHE, not a fixture** (`FIXTURES.md5` marks these VOLATILE).

# 📚 EARLIER HANDOFF SNAPSHOTS → `28-HANDOFF-ARCHIVE.md`

Every superseded "you are here" section now lives in **`28-HANDOFF-ARCHIVE.md`** (append-only).
This file is CURRENT STATE only — if something here is no longer true, fix it here rather than
adding another banner below it.
