# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-08-11 — read "‼ YOU ARE HERE" immediately below.
Every banner further down is HISTORY, newest first.

---
# ‼ YOU ARE HERE — 2026-08-11 (end of a long session). Read this, then `14-AGENT-PLAYBOOK.md`.

## WHAT THIS IS
`sandbox-pokebot/` is the working build of a Pokémon Emerald bot. Its **Story mode** plays the game
autonomously from Littleroot. `40cakes repo/` is a pristine upstream mirror (never edit);
`custom-pokebot/` is the promoted fork. **All work happens in `sandbox-pokebot/`.**

‼ **READ `01-VISION-AND-DESIGN.md`'s NORTH STAR FIRST if you have not.** The user restated the goal
on 2026-08-11: (1) a bot that plays Emerald **organically and faithfully, as a human would**, and
(2) **a documented substrate for a future self-training AI agent**. Goal 2 is why the documentation
burden here is so heavy, and why negative results are treated as the most valuable asset.

## STATE
| | |
|---|---|
| branch / HEAD | `main`, **clean, 0 unpushed** |
| box | **IDLE.** Batch `20260811-130454` finished 4:05 PM (VERDICT OK, 28 runs, 0 violations). |
| story content | Littleroot → 6 badges → Mt. Pyre → Magma Hideout. **16 of 24 ladder beats.** |
| ‼ is code frozen? | **No.** Nothing is running. |
| upstream | checked 2026-08-11, `5dd898f8`, unchanged |
| restore point | **`restore/2026-08-11-all-promoted`** (annotated, pushed, verified on the remote) |
| sandbox ↔ custom drift | **§Ch16 only** (`early_game.py`, `story_mode.py`) — deliberately NOT promoted; it is blocked and unproven |
| **if stopped mid-task** | **NOTHING IS PARKED.** Everything is committed and pushed. Start at "NEXT ACTIONS". |

## ✅ WHAT SHIPPED THIS SESSION
1. **`#24-teachmsgstall` root-caused and fixed** — the replace prompt was detectable for **one
   frame** (decomp-confirmed). Promoted. ‼ **But see the batch result below: it has NO production
   effect and the item is REOPENED.**
2. **KI-51** — the Maxie loop now notices a whiteout instead of riding 60,000 frames (confirmed
   live at 2,209 frames). Promoted.
3. **KI-52** — the bot **fights it out** instead of freezing mid-battle with a healthy bench
   (your directive). Promoted. ‼ Structurally proven only; no live A/B.
4. **Battle STATUS telemetry** — the turn log prints `[Confused]` etc. Promoted. It refuted
   `#24-bosstelemetry` lead 2 and made the status tax measurable for the first time.
5. **§Ch16 (Slateport Harbor) BUILT** — function, driver, Segment 16. **Blocked by KI-56.**
6. **A whole hardening round** (see below).

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

## ‼‼ KI-56 — THE BOT IS STRANDED IN THE MAGMA HIDEOUT. READ THIS BEFORE ANY STORY WORK.
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

### ✅ CAUSE CONFIRMED AND FIX CHOSEN (2026-08-11, later) — but NOT BUILT
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

All of it is **STATIC**. The bot has **no Escape Rope support at all** — that is the build.
## ⏭ NEXT ACTIONS, IN ORDER

1. **KI-56 — BUILD the escape.** Cause confirmed, fix chosen and fully specified (table above);
   nothing is built. This blocks ALL further story content. Three pieces:
   (a) a **`use_escape_rope()`** action — the bot has none; every future dungeon wants it;
   (b) **pick up the ball** at `3F_3R (9,19)` from `(9,20)` facing Up, gated on flag 1059 so a
   resumed run does not re-try a taken ball;
   (c) **wire it into §Ch15's exit** so the chapter ENDS outside, and extend the chapter's
   acceptance test to "and the bot can continue" (the rule this bug created).
   ‼ Do (a) and (b) against the stranded save `sandbox-pokebot/profiles/ch16a/current_state.ss1`,
   which is a free repro of the exact failure. Re-run both probes to re-derive any constant.

2. **§Ch16 is BUILT and waiting on KI-56.** Code, driver (`--driver slateporttheft`) and Segment 16
   are committed. Its first run got the era gate right and failed in leg 1 (leaving the hideout).
   **Legs 2-4 are unexercised — not implicated, not proven.** To re-run once KI-56 is fixed:
   ```
   cd tools/story-dev
   PYTHONUTF8=1 py -3.12 verify_fixtures.py --assert post_maxie.ss1=19399688e730 &&    PYTHONUTF8=1 COLUMNS=400 py -3.12 story_harness.py post_maxie.ss1        --driver slateporttheft --frames 2500000 --profile ch16b
   ```
   Acceptance is BOTH halves: `SLATEPORT_HARBOR_STATE == 2` **AND** controllable.
   ‼ Still-unmeasured risk on the later legs: **KI-53** (`ROUTE110 → SLATEPORT_CITY` fails
   statically while the exact reverse plans in 30 wp). A static FAIL is not a verdict.

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
