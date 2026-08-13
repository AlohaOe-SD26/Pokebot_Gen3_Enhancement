# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-08-13 — read "‼ YOU ARE HERE" immediately below.
Every banner further down is HISTORY, newest first.

---
# ‼ YOU ARE HERE — end of the ROSTER-DRIVE session (2026-08-13). Read this, then `14-AGENT-PLAYBOOK.md`.

## ⏱ THE 60-SECOND VERSION (if you read nothing else)
* **`reorder_party()` IS NOW DRIVEN AND PROVEN.** `--driver roster` (NEW) ran **six swaps, all
  verified by PID**, including **`RotatePokemon(i, j != 0)` — a path nothing in this project had
  ever driven.** The party-ORDER capability the Regi arc needs is real, not just planned.
* **The drive found a real defect and it is FIXED, A/B proven:** `reorder_party()` returned `True`
  with the avatar **unable to walk**. ‼ Every cheap check said it was fine — not Manual, state
  already `OVERWORLD`, start menu already closed. Only asking it to MOVE revealed it.
* **‼ 0 of 6 pre-registered predictions fired, and neither prediction pass found the real bug.**
  Both hunted the KI-38 hang family because that is where the docs point. See
  `ai-research-notes/2026-08-13-roster-drive-predictions.md` — it holds the full raw transcripts.
* **Two issues filed, both deliberately NOT fixed: KI-70** (`_rotate_lead_safely` has the same
  shape, on the hottest path in the bot — **measured, margin held, but n = 1**) and **KI-71**
  (roster.py's "dropped to MANUAL" guard is **unreachable**; `main.py:145-147` abandons the
  generator first).
* **`puzzle_solver.py` IS A RECIPE BOOK, NOT A SHORTCUT — COPY FROM IT, DO NOT DRIVE IT.**
  It is byte-identical to the upstream mirror and holds the Seafloor Cavern + Sealed Chamber +
  Regi routes. ‼ **I first wrote this up as "it already ships §Ch21 and the Regi arc" and that was
  OVERSTATED** — an adversarial pass refuted it and I verified the refutation myself:
  the Seafloor branch ends `navigate_to(ROOM9, (16,42))` → `set_manual_mode()` (it parks the bot on
  **Archie's own cutscene tile** and hands control to a human — no battle, no progression, no exit),
  and the Regi branches **open the door only**, ending at the tomb's EXIT warp, never at the statue.
  **What survives is still valuable**: the `dive() → navigate → surface_from_dive()` template (which
  `--driver ch21dive` copied to a 6/6 PASS), free hand-derived room coordinates, and independent
  corroboration of **KI-69**'s Emerald party order (`("Wailord", 0)` / `("Relicanth", size-1)`).
  Read `ai-research-notes/2026-08-13-puzzle-solver-already-ships-ch21-and-the-regi-arc.md` —
  **the correction is at the top.** ⛔ Never point it at a Regi tomb: its battle handling is
  `handle_encounter(auto_battle=True)` and KO'ing a Regi destroys the encounter.
* **✅ THE FIRST DRIVEN DIVE IN THIS PROJECT — KI-68 step 1 IS DONE.** `--driver ch21dive` (NEW)
  → `ACCEPTANCE: PASS legs=6/6 at_entrance=True got_out=True can_continue=True`. Mossdeep →
  `SEAFLOOR_CAVERN_ENTRANCE (10,17)` **and back out to the open ocean**.
  ‼ **THE STATIC WARP DATA IS MISLEADING AT BOTH ENDS OF THIS CAVERN** — the way in *and* the way
  out are RUNTIME `setdivewarp`s that no warp-graph or path scan can see. **Drive it; do not read
  it.** The way out is three hops, not the one the table implies.
  ‼ **This does NOT make §Ch21 unblocked** — the run INJECTED Dive with a debug write. Acquiring a
  real Dive learner (KI-63) is still open.
* **KI-72 filed (NEW, code-verified):** `calculate_path` has never heard of
  `"Underwater Blocked Above"` / `"Seaweed No Surfacing"` — the two tile types you cannot surface
  from — so it will route a dive to a dead end. ⇒ **NEVER let the planner choose where you
  surface**; pick the tile explicitly, as upstream already does.
* **Nothing is parked. Nothing is running.** All 15 gates exit 0 after the change.
* **§Ch19 is DONE and the ladder runs 20 of 24 beats.** §Ch18 + §Ch19 are **PROMOTED** to
  `custom-pokebot/` and verified by driving `--build custom`, including the real ladder.
* **The next content beat (§Ch21, Seafloor Cavern) is BLOCKED, and the reason changed twice** —
  read **KI-68** before touching it. It is *not* the party slot, and Dive is *not* impossible:
  the planner cannot AUTO-route a dive, so **a chapter must drive `dive()` explicitly.**
* **The REGI arc is the user's ask** — read **KI-69**. ‼ **Emerald reversed the party order:
  WAILORD first, RELICANTH last**, and the wrong order fails **silently**. ‼ **The Regi battle is
  UNRECOVERABLE** — a KO *or* a whiteout deletes the encounter permanently.
* **Run `preflight.py` first.** Then the gate list in "HOW TO RUN / TEST".

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
| story content | ✅ **§Ch19 COMPLETE 2026-08-12 — the MOSSDEEP SPACE CENTER is defended and HM08 DIVE is in the bag. 20 of 24 beats.** Littleroot → 6 badges → Mt. Pyre → Magma Hideout (and out) → Slateport submarine theft → the Lilycove AQUA HIDEOUT (with the MASTER BALL) → the MIND BADGE → **the Space Center multi battle + Dive**. (was 19 of 24 before Ch19.) |
| ‼ is code frozen? | **No.** Nothing is running. |
| party ORDER | ✅ **PROVEN 2026-08-13.** `--driver roster` from `saves/post_dive.ss1` → `phases=4/4 saw_j_nonzero=True idempotent=True restored=True can_continue=True ACCEPTANCE: PASS`. Raw transcripts (both A/B arms) in `ai-research-notes/2026-08-13-roster-drive-predictions.md`. ‼ The **deposit/withdraw** half of `#24-roster` is still open. |
| upstream | checked **2026-08-13**, still `5dd898f8` — no change. ‼ This row goes stale on a CALENDAR DAY, not on an event: if today's date is later than the one shown, **the daily check is DUE** (`git fetch upstream-pokebot`, compare against `40cakes repo/UPDATE-LOG.md`). Do not read it as satisfied. |
| restore point | **`restore/2026-08-12-pre-ch1819-promotion`** (annotated, pushed) — taken immediately BEFORE the §Ch18/§Ch19 promotion. Older: `restore/2026-08-11-all-promoted`. |
| sandbox ↔ custom drift | ✅ **§Ch18 + §Ch19 ARE PROMOTED** (2026-08-12, user-approved). 8 files; at promotion time the trees were **byte-identical across all 255 code/config files**, verified by DRIVING `--build custom` three ways — §Ch18 `badge=True out_of_gym=True whiteouts=0`; §Ch19 `dive=True hm08=True CAN-CONTINUE OK` at `frames=3558869` **identical to sandbox**; and the real `StoryMode` ladder end-to-end. ‼ **TWO FILES HAVE DRIFTED SINCE, ON PURPOSE — both are sandbox-only and must NOT be promoted yet:** `modules/story/roster.py` (**NEW**, the party-reorder module — its *driver* is unproven) and `modules/menuing.py` (the `PartyMenuExit` freeze fix, which only matters to that unproven driver). **Verify with the loop in "HOW TO RUN / TEST" before assuming either number.** |
| **if stopped mid-task** | **NOTHING IS PARKED.** Everything is committed and pushed. Start at "NEXT ACTIONS". |

## ✅ WHAT SHIPPED IN THE LATEST SESSION (§Ch19 + promotion + roster)
1. **§Ch19 built and driven end-to-end** — Space Center multi battle **and** HM08 Dive, wired as
   Segment 19. Ladder **19 → 20 of 24**. Acceptance includes "and the bot can continue".
2. **§Ch18 + §Ch19 PROMOTED** to `custom-pokebot/`, verified by driving `--build custom` three ways.
3. **KI-64 fixed** (the multi-battle faint replacer would have sent out STEVEN's Pokémon) — ‼ and my
   first fix was **wrong twice**: dead code on the story path, and a positional cut that inverted
   itself once the party menu permutes `gPlayerParty`. Now keyed on **original trainer ID**.
4. **KI-67 CLOSED, both halves** — the whiteout abort no longer burns a chapter's retry budget or
   launders itself into a fabricated diagnosis, and the harness finally mirrors production.
   **First driven whiteout recovery in this project** (frame deltas +7,789 / +7,087).
5. **Two blind gates fixed:** the flag audit was checking **2 files** and could not see names behind
   a module constant (i.e. blindest at the completion markers); and **pyflakes had never been run** —
   it found a `NameError` on the Magma Hideout's *success* path.
6. **New: `modules/story/roster.py`** (party reorder) + the `PartyMenuExit` freeze fix.
7. **Regi arc researched and Phase A measured** (KI-69) at the user's request.

### 📌 THE OLDER SESSION'S SUMMARY (§Ch16-§Ch18) FOLLOWS BELOW — it is HISTORY, not current state.
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
  ⛔ **RETRACTED 2026-08-12:** the line below said the unlock was `POKEBOT_BOX_OVERFLOW_CATCH`,
  "one unhandled text box away". **Both halves are false.** That flag has defaulted to **ON** since
  2026-08-07 (`story_mode.py:2241-2243`, verified in the live code), and the text-box blocker was
  refuted the same day (`exit_frames=120`, zero forced presses). Four docs repeated it because they
  were written from a **stale code comment** instead of the default twenty lines below it. See
  KI-54's retraction block.
* **The boss-response design is still the user's call.** The status tax now has a resolved rate
  behind it, but a status response is a battle-policy change touching every mode — **do not build
  it unilaterally.**

## ✅ KI-56 (Magma Hideout strand) — resolved 2026-08-11, detail ARCHIVED

Full block moved to `28-HANDOFF-ARCHIVE.md`; the issue itself is in
`31-KNOWN-ISSUES-ARCHIVE.md`. ‼ Keep only this: its prevention rule — **a chapter's test must
include "and the bot can continue"** — was violated AGAIN by §Ch18 on 2026-08-12, which passed
`badge + controllable` while parked on an eleven-tile island. It is the most re-learned lesson
in this project. Read it before writing any chapter's acceptance test.

## ✅✅ §Ch19 IS DONE (2026-08-12, later session) — the Space Center AND Dive, ladder 19 → 20 of 24

**Driven end to end from `post_mossdeep_gym.ss1`, zero whiteouts:**
```
[ch19c] RESULT dive=True hm08=True MOSSDEEP_SPACE_CENTER_STATE=3
        map=MOSSDEEP_CITY at=(19, 11) controllable=True whiteouts=0
[ch19c] CAN-CONTINUE OK(15wp to the Pokemon Center)
[ch19c] ACCEPTANCE: PASS
```
`modules/story/space_center.py` is the chapter; **Segment 19 is wired into `story_mode.py`**, graded
on `RECEIVED_HM_DIVE` (‼ NOT on the Space Center var — `chapters.py` grades chapter 19 on the Dive
flag, and the two are set in DIFFERENT BUILDINGS; a segment stopping at the battle would pass its own
guard while `current_chapter()` returned 19 for ever, and on the re-run the 2F Steven has been
`removeobject`'d so there would be nobody left to talk to).

**New anchors:** `at_steven_2f.ss1`, `post_space_center.ss1`, `post_dive.ss1`.
**New drivers:** `spacecenter1` (legs 1-3), `spacecenter2` (the menu + multi battle), `spacecenter`
(whole chapter — ‼ run it from `post_space_center.ss1` as well; skipping to leg 6 is what PROVES the
resume guards).

### ‼ THE FOUR THINGS WORTH KNOWING BEFORE TOUCHING THIS CHAPTER
1. **Mossdeep is CUT IN TWO until the forced cutscene runs.** The gym victory SPAWNS five Team Magma
   NPCs onto the only land bridge (x=44, y=23-26) and our planner blocks loaded-object tiles, so no
   route to the Space Center door exists yet. Leg 1 is therefore TWO legs: trigger line → **assert
   `VAR_MOSSDEEP_CITY_STATE == 2`** → then the door. ‼ I first blamed KI-59 (our planner
   over-blocking) because my flood fill modelled collision only and could not see NPCs — the planner
   was right. `probe_ch19_route.py` now models live objects so it cannot tell that lie twice.
2. **The stair grunt must be TALKED to.** `sight_radius = 0`, and it stands ON (13,2), the only tile
   the stairs are reachable from — so navigating there can never succeed, and waiting cannot help.
3. **‼ THE PARTY-SELECTION MENU IS SOLVED AND VERIFIED LIVE** (this was the chapter's one genuine
   unknown). Cursor slots 0-5 are mons, **6 = CONFIRM, 7 = CANCEL**; each pick is `A` (submenu) then
   `A` (ENTER), and **the cursor does NOT advance between picks**. A on an already-picked mon
   DESELECTS it, so blind A-mash toggles one slot for ever with a healthy screen and no error. Every
   pick is verified against **`gSelectedOrderFromParty`** (stored as `slot + 1`): measured `[1,5,3,0]`
   against `INTENDED-PICKS [0,4,2]` — an exact match. **Always bring three**: `Cmd_checkteamslost`
   sums HP over the PLAYER's picks only, so bringing fewer is strictly worse, not "letting the ally
   carry it".
4. **Losing is a RETRY, not an error.** The script inspects the outcome itself and calls
   `SetCB2WhiteOut` on anything but a win — money halved, warp to the last heal location — but the
   var stays at 2 and no trainer flag is set. ‼ Leg 1's heal matters twice over: the anchor's
   respawn was measured to be **LILYCOVE**, across the sea with no Fly user.

### ‼ AND IT NEARLY SHIPPED STRANDED — FOR THE THIRD TIME
The first full run finished `dive=True hm08=True controllable=True` and **FAILED**, because it ended
inside `MOSSDEEP_CITY_STEVENS_HOUSE (3,7)`. The Dive gift is an ON_FRAME script that fires on the
doorstep, so the beat ends where it begins with every completion signal already true. **The
acceptance caught it only because it asks for a real `calculate_path` off the end tile** rather than
asking whether the avatar is "controllable" — which it was, indoors, the whole time. §Ch15 ended four
floors underground, §Ch18 on an eleven-tile island, §Ch19 in a living room. *Keep that assertion in
every chapter's acceptance.* (Second bug inside the fix: both navigate-based door helpers free the
tile by stepping SOUTH, and (3,7) is the bottom row — an exit door needs `_walk_through_warp("Down")`.)

## 🛠 TWO GATES WERE BLIND, AND FIXING THEM FOUND A REAL BUG
* **`audit_flag_names.py` was checking TWO files** — written before the chapters moved into
  `modules/story/*.py` — and, worse, could only see names written as literals AT the call site, while
  the house idiom is a module constant. So it was blindest exactly at the **completion markers**.
  Now globs 19 files, resolves `CONST = "LITERAL"`, prints per-file counts, and **exits 1** on a
  phantom (it used to print findings and exit 0). Coverage 2 files/117 names → 19/144. A/B proven by
  fault injection.
* **`pyflakes` was installed and had never been run.** New gate `repro_undefined_names.py`
  (ZERO tolerance over `modules/story` + `plugins/custom_modes`). It found my own missing import
  *after* a five-minute drive had already paid to reach it — **and KI-65**, below.

## ‼‼ THE ADVERSARIAL REVIEW OF THE FINISHED CHAPTER FOUND MY OWN FIX WAS WRONG TWICE
Run AFTER §Ch19 was committed and reported proven — which is exactly why it is worth doing.
* **KI-64's fix was DEAD CODE on the story path.** The MRO is `StoryItemBattleStrategy` →
  `LevelUpTravelBattleStrategy` → **`LevelUpLeadBattleStrategy`** → `DefaultBattleStrategy`, and
  `level_up.py:41` has its own `choose_new_lead_after_faint`. I had guarded the base class.
* **‼ And the `index >= 3` cut was in the WRONG INDEX SPACE.** Opening the battle party menu runs
  `UpdatePartyToBattleOrder`, which PHYSICALLY PERMUTES `gPlayerParty` — visible in my own passing
  log (`ch19d.log` f37745): index 1 becomes the ALLY's Metang and OUR Swellow moves to index 3. The
  cut **offered the ally and hid one of ours**, precisely when a replacement is needed.
* **My fault-injected A/B passed it anyway**, because the fixture modelled only the un-permuted
  order and asserted the base class directly. A control arm does not save you if all three arms
  measure the wrong thing.
* **Now fixed properly**: `ally_party_indices()` keyed on **ORIGINAL TRAINER ID** (identity travels
  with the Pokémon; position does not), wired at all three call sites. Repro is **5/5** with the
  permuted-array and story-class arms added; §Ch19 re-driven to a PASS afterwards.
⇒ **Two new prevention rules in `08-MISTAKES.md`:** print the MRO before "fixing" a strategy method,
and never identify a Pokémon by party index across a battle-menu boundary.

## ‼ FOUR NEW ISSUES FILED
* **KI-64 (FIXED)** — the multi-battle faint replacer would have sent out **STEVEN's** Pokémon.
  `FillPartnerParty` writes his Metang/Skarmory/Aggron into `gPlayerParty[3..5]`; both choosers
  excluded only the on-field mons and rank by condition, so three fresh L42-44 mons win outright.
  ‼ The guard needed already existed with **zero callers**: `is_double_battle_with_partner`.
* **KI-65 (OPEN, unfixed — ‼ and I CORRECTED MY OWN OVERSTATEMENT of it)** —
  `battle_move_replacing.py:280` uses `party_index`, which is assigned lower down. I first wrote
  that the HM-refusal re-pick "may never have executed"; **that was too strong.** Tracing the flow:
  the name is bound in the `AskWhetherToLearn` branch, which normally runs first, so on an ordinary
  teach the re-pick works. The real bug is narrower — line 371 is inside a `try:` whose `except`
  silently defaults, and on THAT path the name is never bound, so a later `CantForgetHM` raises
  `UnboundLocalError` into a SECOND silent `except` that declines. **Two invisible failures that
  compound.** Still worth fixing, still needs its own repro first.
* **KI-66 (OPEN)** — the multi-battle hazard is BROADER than the faint chooser: **four more**
  full-party scans on the same paths (two in `battle_handler.py`, `alive_slots`, and the rotation
  targets feeding an **unbounded** `while PARTY_MENU: press A`). The right fix is ONE choke point —
  `ally_party_indices()` now exists — not a guard per call site. ⚠ Also unverified and worth checking
  FIRST, because it would fire on turn 1 rather than on a faint: a claimed `IndexError` in
  `decide_turn_in_double_battle` from `gPlayerPartyCount` still being 3.
* **✅ KI-67 (CLOSED 2026-08-12)** — both halves. The chapter retry loops no longer swallow the
  abort (`StoryAbort` + the latch-keyed `reraise_if_aborting`, because a type-only guard cannot see
  an abort an inner loop already replaced with a fresh error), AND the harness now mirrors
  production via `StoryWhiteoutRecoveryMixin`. **First driven whiteout recovery in this project:**
  `--driver spacecenter2 --inject-weak` gave `whiteouts=3 recoveries=3`, ending controllable at
  `MOSSDEEP_CITY (28,17)`. ‼ **The proof is the FRAME DELTA, not the count** — +7,789 and +7,087
  between whiteouts, i.e. each attempt really walked back to Steven and fought again. Broken code
  would have burned three attempts in a handful of frames after ONE whiteout.
  ‼ Five defects in the mixin were caught by an adversarial review **before** it was driven
  (`PathFindingError` is a `RuntimeError` and escaped the recovery; MRO silent-revert; a `tag`
  dereference on the listener's stack; a class-counter budget; a `None`-is-success exit), plus a
  real blocker: an injected run could have silently overwritten a committed anchor.

## 🆕 THE REGI ARC — researched and measured 2026-08-12 (user-requested). See **KI-69**.

**‼ THE PARTY ORDER EVERYONE REMEMBERS IS THE RUBY/SAPPHIRE ONE.** Emerald reversed it:
**WAILORD first (slot 0), RELICANTH last** (`braille_puzzles.c:92-104`, comment and all). The wrong
order **fails silently** — no message, no error. Emerald also swapped **Regirock to ROCK SMASH**
(was Strength) and **Registeel to FLASH** (was Fly). Pinned in `repro_roster_reorder.py`.

**⛔ THE REGI BATTLE IS UNRECOVERABLE — read this before writing any battle policy.** Level 40,
catch rate 3. `B_OUTCOME_WON` removes it forever, and the fall-through case **including
`B_OUTCOME_LOST`** sets `FLAG_DEFEATED_*`. ⇒ **KO'ing it OR whiting out deletes the encounter
permanently.** The only safe non-catch exit is fleeing.

**✅ NEW CAPABILITY: `modules/story/roster.py`** — `plan_reorder` / `plan_last_slot` (PURE, proven
exhaustively: 720 permutations replayed, `repro_roster_reorder.py` 15/15) and `reorder_party()`
which drives `RotatePokemon` inside the `_rotate_lead_safely` harness. ‼ **The DRIVER is UNPROVEN** —
`RotatePokemon(i, j)` with `j != 0` has never been driven here, and it sits on the unfixed side of
KI-38 (four unbounded loops + a `set_manual_mode()` trapdoor). **Drive it before anything depends on
party order.**

**MEASURED capability status** (`probe_regi_capabilities.py`): ✅ Go-Goggles, HM08 in bag, Surf
(Zigzagoon), Rock Smash (Sceptile). ⛔ **no rod at all**, no TM28 Dig, and nobody knows Dive, Dig or
Flash. So the arc needs an acquisition phase first — Super Rod (Route 118), TM28 (Route 114), and
teaching Dive/Dig/Flash. ‼ **Relicanth is underwater-only, so Dive is upstream of everything.**

## ⏭ NEXT ACTIONS, IN ORDER

> **START HERE ON A FRESH CONTEXT.** Everything is committed and pushed; nothing is parked.
> 1. **Run `preflight.py`**, then the 15-gate suite in "HOW TO RUN / TEST" (all exit 0 today), and
>    the sandbox↔custom drift loop (expect **exactly 2** differences — `roster.py`, `menuing.py`).
>
> 2. ✅ **DONE 2026-08-13 — `reorder_party()` IS DRIVEN.** `--driver roster` exists and passes.
>    Six swaps, all verified by PID, including the never-driven `RotatePokemon(i, j != 0)`.
>    **Both unknowns this item asked about are now SETTLED by the trace:**
>    * *the exit-menu timing gap* — **REAL, and it was a bug.** The party menu's last act is
>      re-showing the Start menu (`Task_ShowStartMenu` still live at f660 of a 662-frame call), so
>      `reorder_party` used to return `True` while the avatar could not walk. **Fixed** with a
>      `swapped`-gated `_settle()`; A/B proven (`moved=False`→`True`, FAIL→PASS, and phase 3 costs
>      0 frames in BOTH arms — the control arm proving the gate does not over-fire).
>    * *the stale-cursor read* — **the mechanism is real but did NOT fire.** `gPartyMenu.slot_id`
>      is **not reset between menu sessions**: the tracer read a stale `slot_id=2` on the overworld
>      before the menu had opened, and `navigate_to_mon:520-524` computes its scroll direction from
>      exactly that global. It happened to be re-read live in time. **This is luck, not safety** —
>      re-check it first if a future roster drive ever mis-swaps.
>    ‼ **What is NOT done:** the **deposit/withdraw** half of `#24-roster`. Ordering answers "in
>    what order", not "which Pokémon". And **promotion of `roster.py` + `menuing.py` to
>    `custom-pokebot/` has NOT been asked for — that is the USER's call.**
>
> 2c. **‼ READ `ai-research-notes/2026-08-13-puzzle-solver-already-ships-ch21-and-the-regi-arc.md`
>    BEFORE ITEMS 3 AND 4 BELOW.** Both were written believing §Ch21 and the Regi arc had to be
>    built as chapters. **Most of that content already exists in upstream code we already have.**
>    Items 3 and 4 are still correct about the DIVE LEG — which is the real gap — but wrong about
>    the scale of what remains. **KI-72** also lands here: never let the planner choose a surfacing
>    tile.
>
> 3. **‼‼ READ KI-68 BEFORE TOUCHING §Ch21 — AND DO NOT READ "NOT ROUTABLE" AS "NOT POSSIBLE".**
>    The party slot is **not** the blocker. `WaypointAction.Dive`/`Emerge` are declared and assigned
>    **nowhere**, and `warp_graph.py:342` says the exclusion is **on purpose** — a dive is not a warp
>    event, so `calculate_path` was never going to emit one. **But `dive()` already exists and
>    works.** ⇒ **The fix is a CHAPTER that drives the transition**, exactly like §Ch18's coord-event
>    exit and Steven's bottom-row door — *not* a planner rewrite.
>    **DO THIS FIRST, near-zero risk and required either way:** inject Dive via
>    `debug_utilities.py:611` and drive Route 128 → Seafloor Cavern to see what the legs really need.
>    ‼ If a hunting ground is ever added, **NOT to `TRAINING_GRASS`** — measured, a Shoal Cave row
>    becomes the highest band and flips `best_training_area` for every team from ~L30 up.
>
> 4. **The REGI arc (user-requested) — read KI-69.** ‼ **WAILORD first, RELICANTH last** (Emerald
>    reversed it; the wrong order fails silently). ‼ **The Regi battle is UNRECOVERABLE** — a KO *or*
>    a whiteout deletes the encounter; only fleeing is safe. Phase A is measured: we have Go-Goggles,
>    HM08, Surf and Rock Smash; we have **no rod at all**, no TM28 Dig, and nobody knows Dive, Dig or
>    Flash. **Relicanth is underwater-only, so Dive (item 3) is upstream of the whole arc.**
>
> 5. Older framing below, kept for its measurements — its CONCLUSION is superseded by items 3-4:

> 2b. **‼ THE NEXT BUILD IS NO LONGER BLOCKED THE WAY THE DOCS SAID.** §Ch20/§Ch21 need **Dive
>    USED**, and KI-63 is real (no party member learns it, party 6/6). But the thing four documents
>    called the gate — `POKEBOT_BOX_OVERFLOW_CATCH` being off and "one unhandled text box" away —
>    **is false and has been since 2026-08-07.** It defaults to ON; the text box needs no handling.
>    **Verify it yourself at `story_mode.py:2241-2243` before believing either version.**
>    **THE PLAN (measured against `modules/data`, detail in KI-54's new section):**
>    * **Spheal**, ~50% of the `SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM` LAND table at L26-32, catch rate
>      255, learns **Surf AND Dive**. Mossdeep → Route 125 → the entrance room is **one warp**.
>      ⚠ TIDE is the one risk: the high-tide maps have **no encounter header at all**, and which RTC
>      hours give low tide is **UNVERIFIED**. Tide-free fallback: **Marill on Route 120** (15%, L25-27).
>    * ‼ **Deposit-first, NOT box-first** — the opposite of the obvious guess. `ensure_hm_learner`
>      tests the **party**, so a catch into the box never satisfies it and the spin burns its whole
>      budget. Freeing one slot reuses `withdraw_from_box:331-355`, which is live-proven and deposits
>      exactly ONE mon — it is **not** the measured-harmful `POKEBOT_PC_ROTATION` (which fires every
>      heal, down to a floor of 3). Verified offline: it picks **Skitty L17** and correctly spares
>      Zigzagoon L15, our only Surf carrier.
>    * ⛔ **Do NOT fetch the Super Rod first** — Sharpedo/Wailmer are real, but it needs three missing
>      subsystems (no rod chapter, no fishing capability at all, and `_hm_hunting_grounds` reads
>      land encounters only) against one `TRAINING_GRASS` row.
>    * ✅ **THE TIDE IS NOT A BLOCKER (measured 2026-08-12).** The high-tide "maps" have no encounter
>      header and no warps — they only own a LAYOUT that gets borrowed onto map (24,46), and the
>      encounter table keys off map number, not layout. **The Spheal 50% table is live at BOTH
>      tides** (65 walkable encounter tiles at high, 332 at low). No tide handling needed.
>      **Surf is the only gate** and we have it: `MOSSDEEP_CITY → ROUTE125` routes in 119 waypoints,
>      Zigzagoon L15 knows Surf, and Route 125 → the entrance room is one warp.
>    * ‼ **BUT THE REAL GATE IS STILL THE FULL PARTY** — `ensure_hm_learner` raises when the party is
>      ≥6 **before** it ever looks for a hunting ground. Free the slot first; the ground is
>      necessary, not sufficient.
>    * ⚠ Two hazards recorded in KI-54 before anyone codes in that room: `MapLocation` always
>      resolves the **low-tide** layout for (24,46), so in-room planning at high tide plans against
>      the wrong map; and (20,30) counts as a south-arrow warp, so never spin on or below it.
> 3. **Fix KI-59 before the cavern exists** — it is armed there (115 `Impassable *` tiles across
>    Rooms 1-9). A/B on `SEAFLOOR_CAVERN_ROOM1`.
> 4. ✅ **THE PROMOTION ALREADY HAPPENED** (2026-08-12, user-approved, driven on `--build custom`).
>    Do NOT ask for it again. The line below is superseded; only the battle-policy half is still
>    the user's call. Superseded text: Two things remain the USER's call: **promoting §Ch18 + §Ch19 to `custom-pokebot/`**, and the
>    **boss/status battle-policy** decision further down.
> 5. Before building anything, skim `08-MISTAKES.md`'s last entries — five were written today and
>    three of them are about tests or gates that were green while something was broken.

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

## 📌 HISTORY — §Ch19 planning notes, written BEFORE it was built. ‼ §Ch19 IS DONE AND WIRED.
> Everything from here to the next `##` heading is the pre-build research. It is kept because the
> measured hazards in it are still true and still useful, but its status line is **obsolete** —
> §Ch19 shipped, was promoted, and runs in the ladder. Do not read this as a to-do.

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
   `POKEBOT_BOX_OVERFLOW_CATCH` — ⛔ **RETRACTED 2026-08-12: it is already ON and already works.**

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
PYTHONUTF8=1 py -3.12 repro_gym_whiteout_guard.py   # 5/5, fault-injected  (~1 min)
PYTHONUTF8=1 py -3.12 probe_chapter_order.py        # KI-61 regression guard
PYTHONUTF8=1 py -3.12 probe_ch19_hazards.py         # 3/3; H1 is now a stranding guard
PYTHONUTF8=1 py -3.12 probe_space_center_recon.py   # §Ch19 area atlas (measured, not recalled)
PYTHONUTF8=1 py -3.12 probe_gym_solve.py            # re-derive the 117-step gym route

# ‼ THE 15-GATE SUITE — ALL EXIT 0 as of the last session. Run it before and after any change.
#   preflight, lint_docs, verify_fixtures, audit_flag_names, repro_undefined_names,
#   repro_no_silent_except, repro_roster_reorder, repro_multi_battle_partner,
#   repro_whiteout_abort, repro_gym_whiteout_guard, probe_chapter_order, probe_dive_learner,
#   probe_slot_free_plan, probe_regi_capabilities, probe_dive_routing
PYTHONUTF8=1 py -3.12 probe_chapter_order.py --build custom   # ‼ also check the OTHER fork

# ‼ VERIFY THE SANDBOX<->CUSTOM DRIFT ROW RATHER THAN TRUSTING IT (PowerShell, from the repo root):
#   Get-ChildItem "sandbox-pokebot\modules","sandbox-pokebot\plugins" -Recurse -Filter *.py |
#     ForEach-Object { $rel=$_.FullName.Substring((Resolve-Path "sandbox-pokebot").Path.Length+1)
#                      $c="custom-pokebot\$rel"
#                      if (Test-Path -LiteralPath $c) { git diff --no-index --quiet -- $c $_.FullName
#                                                       if ($LASTEXITCODE -ne 0) { "differs: $rel" } }
#                      else { "MISSING in custom: $rel" } }
#   EXPECTED TODAY: exactly 2 — `modules/story/roster.py` (new, sandbox-only) and
#   `modules/menuing.py` (the PartyMenuExit freeze fix). Anything else is unexplained drift.

# --- §Ch19 gates + drivers (all exit 0 / PASS today; keep them green) ---
PYTHONUTF8=1 py -3.12 repro_roster_reorder.py       # party-reorder PLANNER, 16/16
# ‼ THE PARTY-ORDER DRIVE (added 2026-08-13). ~4 min. Expect ACCEPTANCE: PASS.
#   phases=4/4 saw_j_nonzero=True idempotent=True restored=True can_continue=True
#   ‼ `saw_j_nonzero` is the one that matters — False means the run re-proved the OLD shape only.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver roster --frames 400000
# ‼ THE FIRST DRIVEN DIVE (added 2026-08-13). ~3 min. Expect ACCEPTANCE: PASS, legs=6/6.
#   Mossdeep -> ROUTE128 (38,27) -> dive -> cavern -> surface (10,17) -> and back OUT.
#   ‼ `got_out` is the one that matters: an underwater cavern is the best place yet to strand a run.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch21dive --frames 900000
PYTHONUTF8=1 py -3.12 probe_ch21_topology.py         # the measured route (read-only, 2 controls)
PYTHONUTF8=1 py -3.12 probe_regi_capabilities.py    # what the Regi arc still needs (KI-69 Phase A)
PYTHONUTF8=1 py -3.12 probe_dive_routing.py         # why a chapter must drive dive() (KI-68)
PYTHONUTF8=1 py -3.12 repro_undefined_names.py      # ZERO undefined names in the story surface
PYTHONUTF8=1 py -3.12 audit_flag_names.py           # 19 files / 144 names; exits 1 on a phantom
PYTHONUTF8=1 py -3.12 probe_ch19_route.py           # why Mossdeep is cut in two (models live NPCs)
PYTHONUTF8=1 py -3.12 story_harness.py post_mossdeep_gym.ss1 --driver spacecenter1 --frames 900000
PYTHONUTF8=1 py -3.12 story_harness.py at_steven_2f.ss1      --driver spacecenter2 --frames 600000
PYTHONUTF8=1 py -3.12 story_harness.py post_mossdeep_gym.ss1 --driver spacecenter  --frames 1500000
PYTHONUTF8=1 py -3.12 story_harness.py post_space_center.ss1 --driver spacecenter  --frames 400000  # resume-safety

# --- drivers (these run under the REAL main loop, so they can fight) ---
PYTHONUTF8=1 py -3.12 story_harness.py post_aqua.ss1          --driver mossdeeptravel --frames 500000
PYTHONUTF8=1 py -3.12 story_harness.py in_mossdeep_gym.ss1    --driver mossdeepgym    --frames 400000
PYTHONUTF8=1 py -3.12 story_harness.py at_mossdeep_leaders.ss1 --driver mossdeepbadge --frames 300000
```
‼ **Never read an exit code through a pipe** — `| head` reports ITS status, not the script's. Write
to a file and echo `$?` (this nearly recorded a PASS that had never run).
‼ **A driver can fight; a hand-driven probe cannot.** Battle handling lives in the main loop's
listeners, not inside a bot mode's generator (`modules/battle_fault.py:5`).
**‼ THE AUTHORITATIVE GATE LIST IS THE 15 NAMED IN "HOW TO RUN / TEST" ABOVE — all exit 0.** Do not
reconstruct it from the prose below; there are 94 `repro_*.py` files and the older text says "the
ten standing repro_*" without naming them, which is not reproducible. Current pass counts, measured:
`repro_gym_whiteout_guard.py` **5/5**, `repro_roster_reorder.py` **16/16**,
`repro_whiteout_abort.py` **13/13**, `repro_multi_battle_partner.py` **5/5**.

**Older text (2026-08-12, counts now stale):** plus `repro_gym_whiteout_guard.py` (4/4, fault-injected — ‼ it is a BOUNDED prefix test, because a hand-driven generator has no battle listeners and cannot win a gym fight; see 08-MISTAKES). Previously 14 of 14 (2026-08-11): the ten standing `repro_*` plus
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
