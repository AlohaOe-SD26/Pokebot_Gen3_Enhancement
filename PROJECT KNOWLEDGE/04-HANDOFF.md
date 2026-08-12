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
| story content | ‼ §Ch18 leg 2 (the gym PUZZLE) driven PASS 2026-08-12; Tate & Liza not yet fought. Littleroot → 6 badges → Mt. Pyre → Magma Hideout (and out) → Slateport submarine theft → **the Lilycove AQUA HIDEOUT (with the MASTER BALL)**. **18 of 24 ladder beats.** |
| ‼ is code frozen? | **No.** Nothing is running. |
| upstream | checked **2026-08-12**, still `5dd898f8` — no change. Daily check DONE. |
| restore point | **`restore/2026-08-11-all-promoted`** (annotated, pushed, verified on the remote) |
| sandbox ↔ custom drift | **NONE** — §Ch15 exit + §Ch16 + §Ch17 + heal stops + the MASTER BALL all PROMOTED 2026-08-12 (user-approved); the first promotion was verified by driving `--build custom` to an identical frame count |
| **if stopped mid-task** | **NOTHING IS PARKED.** Everything is committed and pushed. Start at "NEXT ACTIONS". |

## ✅ WHAT SHIPPED THIS SESSION (2026-08-11 → 12)
The story ladder went **16 → 18 of 24 beats**, and everything below is committed, pushed and
**promoted to `custom-pokebot/`** (user-approved 2026-08-12; the promotion was verified by driving
`--build custom` to a frame-identical PASS, not merely diffed).

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

## ‼ THE ONE THING THAT MATTERS MOST FROM THIS SESSION
**Four of my own instruments agreed that the Mossdeep Gym had no route to its own gym leaders.**
All four were wrong, and all four shared one blind spot: they modelled the gym as *walk + warp*.
The gym has a **third movement primitive** — floor switches that relocate 21 statues. Five parallel
Claude agents (one explicitly ADVERSARIAL) found it; the adversarial one cracked it. Even the
model-free brute-force walker was wrong, because it *changed the map while exploring it*.
⇒ *When N of your own instruments agree on something impossible, they probably share a missing
primitive.* Three new playbook rows.

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

## ✅ KI-56 — WAS: stranded in the Magma Hideout. **FIXED AND DRIVEN 2026-08-11.**
Driving §Ch16 exposed it: **Ch15 completes its binary flag test and leaves the run permanently
stuck four floors deep.** Measured from `profiles/ch16a/current_state.ss1`:
* component containing the bot at `MAGMA_HIDEOUT_1F (25,34)`: **248 tiles, NO reachable exit warp**
* the INBOUND route `(10,34) → (25,34)` now **also fails** — the way it walked in is gone
* the push-from tiles are **unreachable**, so it cannot even re-push
* boulders measured at `(5,22) (7,22) (6,23)` = the **ORIGINAL** positions ⇒ **Strength boulders
  RESET on map reload**, exactly like Rock-Smash rocks

‼ **The acceptance test never asked whether the bot could LEAVE** — `GROUDON_AWAKENED` is set the
moment Maxie falls. New playbook rule added: *a chapter's test must include "and the bot can
continue"*.

### ✅ CAUSE CONFIRMED, FIX BUILT, DRIVEN **PASS** (2026-08-11, later)
`probe_hideout_warp_graph.py` re-tested the strand against the **whole eight-map warp graph**
(KI-56's own evidence was a *same-map* path failure, and `calculate_path` "is not able to use
warps", so a routing gap would have looked identical). It is not a routing gap: from the stranded
tile the search reaches **18 of 20 nodes**, missing only the exit warp `1F (10,34)` and
`JAGGED_PASS`. **Option 2 (return-route) is formally DEAD**; option 3 was already dead.

**THE FIX — the dungeon supplies its own escape, so there is no detour:**
| | |
|---|---|
| Escape Rope item ball | `MAGMA_HIDEOUT_3F_3R (9,19)` — a room §Ch15 already walks through |
| flag | `ITEM_MAGMA_HIDEOUT_3F_3R_ECAPE_ROPE` (1059), **unset** ‼ the decomp misspells "ESCAPE"; the correct spelling reads `False` silently forever |
| approach | **`(9,20)` only**, face Up. The other three sides are unreachable |
| reachable from | both 3F_3R warp nodes — including from the STRANDED tile |
| rope lands at | **`JAGGED_PASS (16,19)`**, collision 0 (`probe_escape_warp.py`, 3 controls) |
| bag today | **0 Escape Ropes** on every save ‼ and Lavaridge Mart does not stock them |

**BUILT AND PROVEN.** `collect_hideout_escape_rope()` + `use_escape_rope_to_leave_hideout()` +
`leave_magma_hideout()`, and the chapter now ENDS with the exit — **outside** the
`_groudon_awakened()` guard, so a resumed run still finishes it. Driver `--driver magmaexit`:
```
[mhexit] RESULT out=True map=JAGGED_PASS at=(16, 19) controllable=True landed_on_jagged_pass=True
[mhexit] VERDICT PASS
```
‼ `(16,19)` is the exact tile predicted from `escapeWarp` before any code was written.
Guarded by `repro_hideout_exit.py` (24 checks, fault-injected both ways). Gate: **15 of 15 green**.

‼ **The one thing that did not work first time**, because it will bite the next dungeon too: the
first run **consumed the rope and went nowhere**. `StartEscapeRopeFieldEffect()` runs from
`DisplayItemMessageOnField`'s **callback**, which fires only when the message is DISMISSED — the
wait loop has to press **B**, not just yield. *A consumed item is not the end of the script that
consumed it.*

**Not yet proven:** driven from `post_maxie.ss1` (on 4F). The exit has **not** been driven from a
run that walked all the way back down to `1F (25,34)`; the warp graph says 3F_3R is reachable from
there, but that is static.
## ⏭ NEXT ACTIONS, IN ORDER

1. **‼ §Ch18 — FIGHT TATE & LIZA. The PUZZLE IS SOLVED AND DRIVEN (2026-08-12); the gym battle is
   all that remains of the chapter.**
   ✅ Leg 1: `--driver mossdeeptravel` heals, Surfs Lilycove → Mossdeep, enters the gym
   (PASS, `whiteouts=0`), anchor **`saves/in_mossdeep_gym.ss1`**.
   ✅ **Leg 2: `--driver mossdeepgym` SOLVES AND WALKS THE STATUE PUZZLE — driven PASS.**
   `at_leaders=True map=MOSSDEEP_CITY_GYM at=(23,8) controllable=True whiteouts=0`, the 117-step
   route walked **in a single plan with zero re-plans**. New anchor
   **`saves/at_mossdeep_leaders.ss1`**, standing on the tile that faces Tate.

   ⏭ **WHAT IS LEFT:** face NORTH from `(23,8)` and press A. It is a **DOUBLE battle** requiring
   **≥2 usable Pokémon** (`GetMonsStateToDoubles`: a party count of 1 short-circuits; otherwise it
   needs ≥2 non-egg party members at HP > 0). The party carries Sceptile L47 / Swellow L40 /
   Mightyena L43 / Castform L36 plus Zigzagoon L15 and Skitty L17, so the gate is satisfied — but
   check HP at the anchor before assuming. Beating them sets `BADGE07`.
   ‼ **Grade the chapter on the badge AND controllable**, not the badge alone — `BADGE07` is set
   mid-script, so a flag-only test would call a `lockall`ed avatar a success (the
   `EventScript_ActivateStrength` trap that KI-56 was built on).

   ‼ **THE EXECUTOR'S INTERRUPTION BRANCH IS UNEXERCISED.** Two gym trainer battles DID fire during
   the PASS (frames 49670, 50040) and were won by the bot's standard `TrainerApproachListener` /
   `BattleListener` machinery — `modules/story/mossdeep_gym.py`'s own `_ride_out_interruption` path
   logged **zero** times. It is a safety net that has never been needed, not a proven path. Do not
   describe it as tested.

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
```
**Regression gate — 14 of 14 green (2026-08-11):** the ten standing `repro_*` plus
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
