"""RUN THE STANDING GATE SUITE — one command, one exit code.

WHY THIS EXISTS. The suite was defined ONLY as a comment in `04-HANDOFF.md` ("THE 16-GATE SUITE"),
so running it depended on a human copying names out of prose. That failed in the obvious ways:
the handoff advertised **15** gates for a whole session after a 16th was added, and an older
version of the same list said "the ten standing `repro_*`" without naming them — which is not
reproducible. A list that must be remembered is not a gate; it is a wish.

‼ THE LIST LIVES HERE NOW, IN CODE. `04-HANDOFF.md` should point AT this file rather than
re-listing the names, so the two can never disagree again.

Usage:
    cd tools/story-dev && PYTHONUTF8=1 py -3.12 run_gates.py
    PYTHONUTF8=1 py -3.12 run_gates.py --quick     # skip the slow ROM-loading probes

Exits 0 only if EVERY gate exits 0. Prints a one-line-per-gate summary and, for any failure, the
tail of that gate's output so the reason is on screen without hunting for a log.

‼ NEVER read an exit code through a pipe (`| head` reports ITS status, not the script's). This
runner captures each gate's output to a file and reads `returncode` directly — which is the same
mistake `04-HANDOFF.md` warns about, made impossible here.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")

import time
from pathlib import Path

# ⛔⛔ EVERY GATE RUNS IN A UTF-8 CHILD, ALWAYS. Three gates (`audit_doc_citations`,
# `probe_item_header_body`, `probe_closed_item_refs`) were measured FALSELY FAILING on a default
# Windows cp1252 console: they finished their checks and then died with UnicodeEncodeError while
# PRINTING a `‼`. A gate that reds for a reason unrelated to what it guards teaches the reader to
# bypass it — CLAUDE.md rule 6, and the reason this is fixed here as well as in each gate.
# ⭐ Belt AND braces on purpose: the per-gate guard makes a BARE invocation work (how a human runs
# it); this makes every FUTURE gate immune without having to remember.
_GATE_ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}

HERE = Path(__file__).resolve().parent

#: Per-gate wall-clock bounds. The slowest real gate measured 114.6s, so these carry ~8x margin.
#: ‼ These exist because there was NO bound at all until 2026-08-22 — see the note at the call.
TIMEOUT_FAST = 300
# ⛔ A 900->2400 RAISE WAS APPLIED HERE FOR ~2 HOURS ON 2026-08-26 AND REVERTED THE SAME DAY,
# because a Tier 1 review REFUTED its premise with a live observation: `repro_gym_whiteout_guard.py`
# hangs IN-SUITE reproducibly (frozen just AFTER printing phase [1]'s header, audio-host errors,
# on a QUIET machine, in this strictly SEQUENTIAL runner) while passing ALL 5 checks solo -- so the
# hang is an in-suite environmental interaction (`#26-gatestartupcontention`), and MORE TIME CANNOT
# FIX IT: at any bound it hangs and gets killed. Raising the bound only made a real hang cost 40
# minutes to surface instead of 15 -- the exact "bound raised without a caller that recovers" shape
# this project has been burned by. The bound stays 900; the item holds the evidence.
TIMEOUT_SLOW = 900

#: ‼ PROBES THAT RUN BUT DO NOT GATE — introduced 2026-08-22, deep sanity check PASS 4.
#: Deep sanity check PASS 4 measured THREE entries in this suite that contained **zero assertions
#: and no exit call**, so they could not fail: `probe_slot_free_plan.py`, `probe_regi_capabilities.py`
#: and `probe_dive_routing.py`. On the UNMODIFIED tree they printed 4, 23 and 6 alarm lines
#: respectively — `probe_regi_capabilities.py` prints "‼ MISSING (10) — each one stops the arc" —
#: and the suite reported ALL PASS over all three. Same defect class as `repro_whiteout_abort.py`
#: in pass 3, three at once.
#:
#: They were dispositioned INDIVIDUALLY, not swept:
#:   * `probe_slot_free_plan.py`  -> RESCUED into a real gate. It already computed the safety
#:     invariant (`spared_ok`); only the exit code was missing. Proven with the agent's own
#:     injection: the identical command went exit 0 -> exit 1.
#:   * `probe_regi_capabilities.py` -> ADVISORY. It reports a KNOWN-blocked arc (the Regi work is
#:     not started). Giving it an exit code would red the suite permanently for a documented,
#:     accepted state — a gate that cries wolf, which this project rates worse than no gate.
#:   * `probe_dive_routing.py`   -> ADVISORY. Its own closing line says it is STATIC and "does NOT
#:     prove the route works". It is documentation that happened to be wired into the suite.
#:
#: ⛔ THEY STAY IN `GATES` ON PURPOSE. Gate ordinals are append-only here — deleting entries would
#: renumber every citation after them, which is the exact mistake logged on 2026-08-17. They run,
#: their output is kept, and they are labelled ADVIS so no reader mistakes them for enforcement.
ADVISORY: frozenset[str] = frozenset({
    "probe_regi_capabilities.py",
    "probe_dive_routing.py",
    #: `#24-dexhunt`'s vacuity check. ADVISORY because it measures a CORPUS, not the code: a batch
    #: run with `--build custom` carries no `ids=`/`owned=` telemetry, so it correctly reports a
    #: zero window — a fact about the corpus, not a regression. Failing the suite over that would
    #: teach the reader to bypass it, which is strictly worse than no gate.
    "probe_dexfence_opportunity.py",
    #: `#24-retractioncoverage`. ⛔ DOWNGRADED TO ADVISORY THE SAME DAY IT SHIPPED, 2026-09-17.
    #: It was landed ENFORCING on the claim that it "fails safe — misses, never false-alarms". A
    #: Tier 1 reviewer refuted that in one pass and BOTH failures were then reproduced directly:
    #:   * a still-LIVE sentence can be harvested as retracted when a keyword and an unrelated
    #:     past-reference quotation share a window ⇒ a FALSE POSITIVE on healthy text, which is the
    #:     one failure mode CLAUDE.md §6 says is worse than having no gate at all;
    #:   * it is blind to the IN-PLACE marker idiom, which is how its OWN motivating defect #3 is
    #:     written ⇒ it does not catch the bug it was built for (verified: 2 occurrences, 0 harvested).
    #: ⇒ ADVISORY until both are fixed and fault-tested against the reviewer's repros.
    "probe_retraction_coverage.py",
})

#: The standing suite. `slow=True` means it boots a ROM/emulator and takes real time.
GATES: list[tuple[str, bool]] = [
    ("preflight.py", False),
    ("lint_docs.py", False),
    # Tier 0 of the DOC CONSISTENCY LAYER (CLAUDE.md directive, 2026-08-13): the docs may not
    # contradict themselves or the code. Exists because a handoff passed its own quality bar and
    # still sent the next session to REBUILD FINISHED WORK. Self-test: `--self-test` (10 checks).
    ("audit_doc_consistency.py", False),
    # The STRUCTURAL half of the same layer, added 2026-09-01. Tier 0 was GREEN over all four
    # defects that four cold-start audits found in one day, because every one of them was
    # structural rather than textual: a queue marker pointing at the wrong leg, the HOW TO RUN
    # section deleted wholesale by an unbounded archiving script, a claimed fault-arm count that
    # disagreed with the arms listed. CLAUDE.md: "anything enforceable belongs in a GATE, not in
    # prose". Self-test: `--self-test` (7 cases; ⛔ three of its five checks shipped with FALSE
    # POSITIVES that the self-test caught before it ever graded the real file).
    ("audit_handoff_invariants.py", False),
    ("verify_fixtures.py", False),
    ("audit_flag_names.py", False),
    ("repro_undefined_names.py", False),
    ("repro_no_silent_except.py", False),
    ("repro_roster_reorder.py", False),
    ("audit_encoding.py", False),
    ("repro_box_counter_move_test.py", False),
    ("repro_pid_identity_key.py", False),
    # ⛔ ADDED 2026-09-09 after a telemetry change put `_last_owned` in the WRONG function's
    # `global`, making every heartbeat raise UnboundLocalError INSIDE main.py's `except: pass`
    # ⇒ all telemetry silently dead. A stub suite passed 5 arms and never called `on_frame()`.
    ("repro_heartbeat_emits.py", False),
    # ‼ KI-80. A boss cfg may not gain a `"grass"` key while `grass_is_fodder` is still the sole
    # gate on `_boss_plan_is_hopeless`/`_counter_ladder` — doing so SKIPS the counter machinery
    # for teams above the patch's band + 8, silently, behind a healthy-looking log line. The
    # punch list's own (P6) item asked for exactly that edit; this gate is why it cannot land by
    # accident. AST-based (a mention in a comment cannot trigger it) and SELF-RETIRING (it stops
    # enforcing the moment the coupling is removed). `--self-test` proves all four directions.
    ("repro_boss_grass_gate.py", False),
    # PARTY ACCOUNTING STAGE 0 (`06-DECISIONS-LOG.md` RULING D). Drives the REAL `get_party()` over
    # fabricated `gPlayerParty` memory to prove the divergence observer SEES each class
    # (HOLE/OVERFLOW/STALE/INVALID) and — the part that actually matters — that it changes NOTHING:
    # a byte-identical A/B against the hooks stubbed out, silence on a healthy party, and a
    # fault-injected observer that must break the LOG and never the party read.
    ("repro_party_accounting.py", False),
    # The SECOND half of the user-observed Slugma/Winona derail — not the bug, but why it took a
    # day to find. The heal's three PC piggybacks swallowed every exception, so "nothing to do"
    # and "it threw" were the same silence. Proves the two outcomes are now distinguishable, that
    # the reporter survives a broken console AND a broken run log, and — structurally — that no
    # handler in the heal has quietly reverted to `pass`.
    ("repro_heal_piggyback_reporting.py", False),
    ("repro_hm_slot_wiring.py", False),
    ("repro_multi_battle_partner.py", False),
    ("repro_whiteout_abort.py", False),
    ("repro_gym_whiteout_guard.py", True),
    # ⛔ `#26-ch23money` F0 — the wallet reaches the debug log after every battle, EQUAL to memory on two saves with
    # different wallets, and the hook is a silent no-op with telemetry off. (Money was never logged; the first three
    # organic League arrivals had to be reconstructed.) Boots a ROM.
    ("probe_money_telemetry.py", True),
    ("probe_chapter_order.py", True),
    ("probe_dive_learner.py", True),
    ("probe_slot_free_plan.py", True),
    ("probe_regi_capabilities.py", True),
    ("probe_dive_routing.py", True),
    # KI-59 / `#24-impassabledirs`. Asserts the REAL production `PathTile` vectors match the decomp
    # on both halves (entry AND exit), on VICTORY_ROAD_1F (29 live tiles), with a NEGATIVE control
    # on SEAFLOOR_CAVERN_ROOM1 proving the branch is inert there. ‼ It reads production objects
    # rather than recomputing, because the probe that DID recompute (`probe_shoal_tide.py`)
    # reproduced the bug exactly and so could never have caught it.
    ("repro_impassable_dirs.py", True),
    # ‼ KI-65. `party_index` is assigned at ONE place inside a `try`; when the offer read fails the
    # name stays unbound and TWO later reads raise `UnboundLocalError` into swallowing `except`s —
    # so the HM veto (the "last line of defence") fails OPEN on the exact path it was written for,
    # and the CantForgetHM re-pick prints "Nothing else can be given up" while forgettable moves
    # exist. Two arms on an INJECTED fixture whose slot 0 is deliberately an HM (the only shape
    # that makes `:280` reachable — the two captured `movelearn_hmwedge_*.ss1` saves CANNOT test
    # this, measured, see the script docstring). ARM A must decline HONESTLY; ARM B is the control
    # the fix may not touch. Fault-tested 2026-08-16: reverted to HEAD, the gate FAILED on exactly
    # the lie + honest-message checks. It DRIVES the emulator, so a mention in a comment cannot
    # trigger it.
    ("repro_ki65_unbound_party_index.py", True),
    # `#24-orphans` (1), 2026-08-17. KI-79 made `withdraw_from_box` SAY the truth; every exit still
    # returned `None`, so the caller could not READ it and a failed withdraw was reported and then
    # silently tolerated. This asserts the verdict REACHES the caller — AST-structural, so a new
    # early `return` added later cannot quietly reintroduce the bug — plus the pure report mapping.
    # ⛔ It does NOT assert the withdraw works: that is the live two-armed `boxcounter2` A/B.
    # Fault-tested against REALITY, not only synthetics: `--build custom` (the unpromoted tree) FAILS
    # on exactly the bare returns and the discarded result. Self-test: `--self-test` (7 cases).
    ("repro_withdraw_verdict.py", False),
    # ⭐ The PC-first half of the 2026-09-25 HM directive: a carrier we ALREADY OWN must be
    # found in the BOX, by PID, without a PC trip. Fault-tested 2026-09-25 (slot-index and
    # no-learnset-filter breaks both caught; control green).
    ("repro_boxed_hm_learner.py", False),
    # ⛔ A CONVENIENCE MUST NEVER DISABLE A SAFETY. Written 2026-09-25 after a one-line
    # fixture-CAPTURE added inside the restore's own `try` raised a NameError and SKIPPED THE
    # RESTORE, nearly leaving a CLEARED-GAME state in what the real bot resumes from.
    # Fault-tested: a bare statement before a restore FAILS, and a blinded matcher FAILS too.
    ("repro_restore_guard.py", False),
    # ⛔ A PREDICATE THAT CAN BE TRUE BEFORE ITS CODE RUNS IS A CONSTANT. Written 2026-09-25
    # after the FIRST full-chapter drive won all five fights and still failed: the champion
    # leg asked `battle_ended_frame is not None`, and FOUR battles had already ended.
    # Fault-tested: reintroducing the absolute test FAILS; a blind matcher FAILS too.
    ("repro_latch_scope.py", False),
    # ⛔ ENDLESS-RESET RUN BUDGET (written 2026-07-27, REGISTERED 2026-09-26 — it had never been in
    # this suite). 2026-09-26 additions: the cap EXTENDS once §Ch24 owns the run (the league grind
    # is ~4.5M frames, so under a flat cap every run reaching the League was killed mid-grind and a
    # Hall of Fame was structurally impossible in this mode), and the outcome line reports the
    # enforced re-based count instead of `now - start_frame` (which, after the in-run hard reset,
    # was "this end minus the previous session's end"). Fault-tested against the HEAD code:
    # 8 named FAILs; a comment quoting the old expression does NOT fire it.
    ("repro_endless_frame_budget.py", False),
    # ⭐ `#24-ch23training` (USER RULING 14, 2026-09-26): §Ch23 trains an over-ceiling climb in bounded
    # CHUNKS instead of refusing (30 of 39 organic badge-8 deaths). Checks the planner on every refused
    # corpus species, that the ordinary party still plans ONE chunk, identity-by-PID across evolution,
    # the impossible-case refusal, and the NOCHUNK arm. Fault arms built in: a non-chunking planner and a
    # (pid, species) lookup each turn it red.
    ("probe_ch23_chunk_plan.py", False),
    # ⛔ `#26-ch24organic` R1 — the readiness refusal before the one-way Elite Four: its pure decision,
    # that it sits AFTER training and BEFORE the first door walk / guard press, that it adds no yield,
    # and that its NOTRAIN/NOREADY arms are read in production. Four built-in fault arms turn it red.
    ("probe_ch24_r1_refusal.py", False),
    # ⛔ `#26-ch24organic` gap 2 — the return bridge: after R1 and before the first door walk, a TILE
    # assertion after every walk/flight, both bounded, both arms read in production. Fault arms built in.
    ("probe_ch24_bridge.py", False),
    # ⛔ `#26-ch24organic` gap 3 — teach Fly in production: `_play` latches, teaches, THEN trains; the
    # hand-off driver mirrors that order; the learner rule skips four-HM mons. Fault arms built in.
    ("probe_ch24_flyteach.py", False),
    # ⛔ USER RULING 16 — §Ch23 leg 11 buys only the MISSING basket quantities (same end state; not a thinner
    # basket): the pure `basket_to_buy`, the prices, the leg's money check and purchase, the FULLBASKET arm.
    ("probe_ch23_basket_buy.py", False),
    # ⛔ USER RULING 17 — Mom's Amulet Coin (Segment 12d): `_play` runs `run_ch12d` between the Surf guard and
    # 13a, the driver drives that same function with `_play`'s Petalburg map set, `pick_holder`, the post-game
    # house-state refusal, and both fault arms read + registered. Six built-in fault arms turn it red.
    ("probe_amulet_coin.py", False),
    # ⛔ USER RULING 18 — the early League basket + its reserve: the reserve filters ONLY the battle strategy's
    # medicine list (before the policy, fail-unlocked), no bag reader sees it, arming is state-derived, the
    # purchase plan is pure, §Ch22 L1 heals → buys → re-heals → gym. Six built-in fault arms turn it red.
    ("probe_league_reserve.py", False),
    # ⛔ `#24-dexcatch-battlebail` / RULING 20 Phase 0 — a post-gym-1 Pokédex catch bails at the ball reserve and on
    # a faint (a dex-only subclass; the shiny, HM and counter catches untouched). Three built-in fault arms.
    ("probe_dexcatch_bail.py", False),
    # ⛔ USER RULING 19 `#26-gymtmteach` — the gym-TM teach (design 4): the wall by identity weighted by our faints from
    # the LEADER'S battles only; a recipient the ruled order actually fields; a duel estimate; the slot rule; a taught
    # move never switches off the counter ladder / honest stop. Six built-in fault arms.
    ("probe_gymtm_teach.py", False),
    # ⛔ USER RULING 20 Phase 0 — a post-gym-1 Pokédex catch is not STARTED above ~10 expected throws (Gen 3's own catch
    # arithmetic, from the decomp), and the fence logs each SPECIES' verdict once per reason. Four built-in fault arms.
    ("probe_dexcatch_rate.py", False),
    # ⛔ `#26-hmwrongitem` — the story's HM teach must PROVE the bag cursor is on the HM before pressing A (the game sorts
    # the TM/HM pocket when the bag opens; 9 of 87 live teaches used HM06). A/B-proven on `norman_done.ss1`.
    ("probe_hmteach_itemverify.py", False),
    # ⛔ KI-104 — the HM teach's slot picker is TOTAL (never None / 4 / an HM) and keeps what the mon was trained on
    # (the live shapes: Double Kick, Mud Shot, Low Kick). A/B-proven on `norman_done.ss1`. Three built-in fault arms.
    ("probe_hmslot_rule.py", False),
    # ⛔ `#26-destreachability` (Petalburg Woods) — the Ch12 leg aims at a REACHABLE tile (the old (26, 5) is a solid tree;
    # 67/67 live legs derailed there). ROM: the bot's own planner on the pinned `norman_done.ss1`, with a control.
    ("probe_woods_dest.py", True),
    # ⛔ KI-106 / `#27-evgpcwedge` — every Story recovery starts from NO held input (a leaked Up walked a whiteout
    # respawn into the Ever Grande Poké Center and wedged an 8-badge run). Static, with three fault arms built in.
    ("probe_recovery_heldrelease.py", False),
    # ⛔ KI-47 / `#27-ki47range` — the after-faint chooser decides by IDENTITY (PID + species), never by converting
    # indexes through `gBattlePartyCurrentOrder` (which holds the ENEMY's order after an enemy send-out: a stale map
    # froze the chooser at party 4). Pure plan table + AST wiring, five built-in fault arms.
    ("probe_faint_chooser_identity.py", False),
    # ⛔ USER RULING 20 Phase 2 step T — the per-catch telemetry is LOG-ONLY: `end=`/`dest=` classify honestly, and a
    # raising emit can never cancel a catch, skip defeat counting, or replace a whiteout's StoryAbort. Three fault arms.
    ("probe_r20_telemetry.py", False),
    # ⛔ `#27-setballs` — every item name the story harness looks up is REAL (a cp1252 round trip once turned "Poké
    # Ball" into mojibake and `--set-balls` silently did nothing for two months), and `--set-balls` fails LOUDLY.
    ("probe_harness_item_names.py", False),
    # ⛔ `#27-r101standstill` — every TRAINING_GRASS row and named spin tile can roll a LAND encounter (ROUTE101 (9, 9) was
    # the travel waypoint: 204 batch hunts spun on it with 0 battles). ROM gate: tile types come from the map data.
    ("probe_training_tiles.py", True),
    # ⛔ RULING 20 P2-a — the pre-gym-1 team target is ONE value, 4 unless POKEBOT_R20_TEAM6=1, read by BOTH the fence and
    # the team loop (`#24-partycap` measured 4 -> 6 costing 36 points once; it stays flag-gated). Two fault arms.
    ("probe_catch_team_target.py", False),
    ("probe_dex_open_fence.py", False),
    # `#27-enroutejoin` — every HM/counter hunt WALK runs under `hunt_walk`, and the fence refuses a party join then.
    ("probe_hunt_walk.py", False),
    # RULING 20 P2-c — before gym 1, an armed or walking hunt is checked before team building (flag, default OFF).
    ("probe_hunt_first.py", False),
    # USER RULING 24 step 2 — a hurt party no longer blocks a post-gym-1 dex catch; its loss is not a map defeat (flag).
    ("probe_dex_catch_anytime.py", False),
    # USER RULING 24 step 3 — a training grind no longer blocks a post-gym-1 dex catch, and the trainee keeps the lead.
    ("probe_dex_catch_training.py", False),
    # USER RULING 24 step 4 — a wanted species is caught before survival mode flees it (flag, default OFF).
    ("probe_dex_catch_oversurvival.py", False),
    # USER RULING 24 step 5 — no first-faint bail on a dex catch, BOTH paths (flag, default OFF).
    ("probe_dex_catch_nofaintbail.py", False),
    # design v2 step 5 (TID/T1) — trainer identity + prize money read as the game does; the lines never change a battle.
    ("probe_trainer_identity_T1.py", False),
    # USER RULING 27 (design v2 step 6, KB) — healing items only against key trainer classes (flag, default OFF).
    ("repro_key_battle_items.py", False),
    # design v2 step 7 (RP) — the rare-species predicate: inert data + a pure module. The generator reads our ROM
    # statically (no emulator), and `--check` proves the committed table is what it produces. 13 mutants.
    ("probe_rarity_predicate.py", False),
    # ⛔ `#26-healmap-lavaridge` — an unreachable training ground is remembered from where it was CHOSEN as well as
    # where the walk died (the old key never matched after an abandon: ROUTE111 (25,55) re-walked 19x in P1r7).
    ("probe_trainblock_origin.py", False),
    # ⛔ `#26-healmap-lavaridge` F4 — the Flannery heal takes the cable car + Jagged Pass from below Lavaridge (the
    # generic heal walk has no route there before Flannery: 54 of 54 derailed in the batch). Static + stubbed.
    ("probe_lavaheal.py", False),
    # ⛔ `#26-healmap-lavaridge` (Petalburg family) — the Norman heal falls back to the story's own road when the
    # generic walk bounces from the Rustboro side (53 of 53 derailed in the batch), releasing held input first.
    ("probe_petaheal.py", False),
    # ⛔ USER RULING 20 Phase 1 (A) — ONE deposit-victim rule for every LIVE make-room path: never box a counter still
    # owed to its boss, and for a REQUIRED errand always find a victim on a level-even team. Pure + wiring; 4 fault arms.
    ("probe_r20_makeroom.py", False),
    # ⛔ USER RULING 20 Phase 1 (B), Strength — a BOXED HM04 learner is collected at the Magma haul's heal stops (the
    # HM07-incapable one first); the in-hideout caller stays party-only. Behaviour with stubs + wiring; 4 fault arms.
    ("probe_r20_strengthbox.py", False),
    # ⛔ USER RULING 20 Phase 1 (B), Waterfall — box-first inside ensure_waterfall_learner (the generic gate never fires
    # on a SATURATED compatible learner), and _withdraw_hm_learner names the PID it was asked for. 3 fault arms.
    ("probe_r20_wfbox.py", False),
    # ⛔ `#27-gaterepo` — no live tool script may hardcode the MAIN checkout's path: 22 did, and from a worktree they
    # graded (and imported) `main` while printing PASS. AST scan; docstrings/comments exempt; 5 fault arms.
    ("probe_no_hardcoded_repo.py", False),
    # ⛔ USER RULING 20 Phase 1 (B), counters — box-first before the hunt (a stricter, ranked box pick), and the heal
    # withdraws only counters still OWED (an expired one could be re-collected, and by box order). 4 fault arms.
    ("probe_r20_counterbox.py", False),
    # ⛔ USER RULING 20 Phase 1 (B), Fly + RULING 21 — box-first Fly at the League lobby PC (stand tile (6,2)), the carrier
    # left out of training and R1, and the swap-back checked by (PID, species) before the guards. 5 fault arms.
    ("probe_r20_flybox.py", False),
    # ⛔ KI-107 F3+F4 — the whiteout recovery's waits are BOUNDED (a stale whiteout flag + a battle menu idled a run 6.27M
    # frames), the KI-47 park is logged, and dumps follow the `inner` generator. 3 fault arms.
    ("probe_ki107_bounded.py", False),
    # ⛔ `#24-restockleg` F1 (USER RULING 12) — a basket-ONLY R1 refusal restocks once at §Ch23 leg 11's shop, then R1 is
    # decided again, before the refusal can raise; a level shortfall never shops. 3 fault arms.
    ("probe_ch24_restock.py", False),
    # ⛔ §Ch23 leg 5 must NOT re-fire from the League plateau on a re-entry (it aimed at an unreachable apron), and
    # MUST still fire from the south, incl. the Wally-beaten south-PC respawn. The REENTRY arm restores the bug.
    ("probe_ch23_leg5_reentry.py", True),
    # ⛔ The citation REPAIRER must shift a range citation's BOTH ends (it shifted only the start, 2026-09-26 —
    # the 08 rule it existed to honour). Self-test; the old logic fails it.
    ("repro_fix_doc_citations.py", False),
    # ⛔ KI-102. The withdraw counted party room EXCLUDING eggs while the consumer that
    # refuses counts INCLUDING them, so 5 mon + 1 egg queued no deposit and then RAISED —
    # after the PC journey was already spent. Carries a HISTORICAL CONTROL that pins the old
    # predicate's disagreement, and a PARITY check that rejects "equivalent-looking" rewrites.
    ("repro_withdraw_room.py", False),
    # ⛔ The HM carrier must stay collectable AFTER a counter has been hunted.
    # `_hunted_counter_pids` is MONOTONIC (never cleared), so the intuitive `counter or hm`
    # silently disables the HM path for the rest of any run that ever hunted a counter — and
    # that failure is invisible to any test which does not hunt a counter FIRST.
    ("repro_withdraw_pid_source.py", False),
    # ⛔ Winning a roamer battle destroys Latias/Latios FOREVER. The retail ROM decides it
    # with `gBattleOutcome & B_OUTCOME_WON` (B_OUTCOME_WON == 1), i.e. ANY ODD outcome — so
    # DREW, PLAYER_TELEPORTED (Roar/Teleport!) and FORFEITED are all fatal, and RAN is the
    # only safe player-chosen exit. This gate pins the PARITY, and its anti-enumeration arm
    # fails any rewrite back into a list of names (which is how FORFEITED got missed once).
    ("repro_roamer_outcome.py", False),
    # `#24-abortswallow` round 3, 2026-08-17. A broad `except` around a `yield from` in the story
    # path can swallow a whiteout; 16 such sites have been fixed, 36 candidates remain.
    # ⛔ IT IS A RATCHET, NOT A ZERO-THRESHOLD, and that is what made it gateable at all: the triage
    # MEASURED that ~64% of the candidates are not this defect, so demanding zero would be red on
    # arrival over correct-as-written code. ⛔ The "obvious" alternative — prune by whether an abort
    # SOURCE is reachable — was REFUTED by an observed failure (`mossdeep_gym.py:465` fabricated
    # "could not get out of the gym" on a dead run, and its body wraps only navigation primitives).
    # Fault-tested both ways: injecting ONE unguarded site takes it 36 -> 37 and exits 1.
    ("probe_abort_swallowing.py", False),
    # ‼‼ APPEND NEW GATES, NEVER INSERT. Gates are cited BY ORDINAL across the docs
    # ("gate #25", "suite #24", "gate #27"). This entry was first INSERTED at position 4
    # on 2026-08-17 and silently renumbered SIX existing citations; an audit agent caught
    # it. ⛔ Adding a gate anywhere but the END rewrites history that prose already quotes.
    ("audit_doc_citations.py", False),   # #28 — citation drift: `ident` + file.py:LINE must resolve
    # #29 — the `git add -A` hook. `CLAUDE.md` calls it "ENFORCED, not requested" and /wrapup +
    # /checkpoint both cite it, but nothing had ever proven it fires. PASS 4 measured EIGHT
    # BYPASSES and ONE FALSE POSITIVE in it. 31 permanent cases, fault-tested both directions.
    # ‼ APPENDED AT THE END, never inserted — gate ordinals are append-only (2026-08-17: inserting
    # one at position 4 silently renumbered SIX doc citations).
    ("selftest_git_add_hook.py", False),
    # ⛔ Its sibling. Written 2026-09-25 after a `grep <gate log> && git commit` committed
    # over a RED suite — grep had SUCCEEDED at finding the word "FAIL", so the commit ran.
    # SECOND occurrence of that class; CLAUDE.md says committing over a red gate is the same
    # offence as `git add -A`, and that one has a hook. Now so does this.
    ("selftest_commit_over_gates_hook.py", False),
    # ⛔ The third hook (user-approved 2026-09-28): git commands that can silently DISCARD work
    # (`checkout -- <f>`, `restore`, `reset --hard`, `stash`, `clean -f`, branch deletion, force-push,
    # `worktree remove`, `rm -f`). A reviewer's `git checkout --` deleted an uncommitted fix on
    # 2026-09-27. Case table + two mutants (always-allow, always-block) + the settings registration.
    ("selftest_destructive_git_hook.py", False),
    # #30 — `#24-loopheadabort`. Nav retry loops must `_check_abort()` at the LOOP HEAD (outside the
    # try — `StoryAbort` subclasses `BotModeError`, so a check inside would be swallowed by the
    # ⛔ §1 gates the ORDERING that makes those checks safe: `StoryMode.run` must clear the
    # latch BEFORE calling any recovery routine. (An earlier draft claimed the recovery runs with
    # the latch SET and must contain NO checks — REFUTED 2026-08-23; see the gate's docstring.)
    ("repro_loop_head_abort.py", False),
    # #31 — §Ch20 CONSTANT PARITY. The production chapter's tiles and push tables must be
    # character-identical to the DRIVEN harness constants. ‼ Written because a FABRICATED
    # `ROOM8_PUSHES` was committed to `modules/story/seafloor_cavern.py` on 2026-08-24: invented
    # from a spec that CITED the source line range without quoting it, right shape, **8 of 9 rows
    # wrong**, and carrying a true-sounding "adjudicated against the decomp" provenance comment.
    # Those nine pushes run in a room where a boulder on (5,3) PERMANENTLY seals the exit, and a
    # wrong sequence fails ~25 minutes into a drive looking like a pathfinding bug.
    # ⇒ A FILE:LINE CITATION IS A POINTER, NOT THE CONTENT.
    # ‼ APPENDED AT THE END — gate ordinals are append-only.
    ("repro_ch20_constants.py", False),
    # #32 (2026-08-26): `#26-fleefreeze` — the trapped-flee DELEGATION. Emulator-free, 3 arms
    # (ordinary unchanged / trapped delegates / old-behaviour refuted by construction). Guards the
    # one-line fix for the freeze that killed 3 of 8 lanes in batch 20260826-063456.
    ("repro_flee_trap_delegate.py", False),
    # #34 — every §Ch23 fault arm is REGISTERED, CALLED and DOCUMENTED.
    # ‼ APPENDED AT THE END, never inserted — gate ordinals are append-only. ⛔ THIS ENTRY WAS FIRST
    # INSERTED MID-LIST ON 2026-09-04, directly under the two standing warnings above that forbid
    # exactly that, AND its comment said "#29" — colliding with `selftest_git_add_hook.py`'s real
    # #29 and giving one gate THREE different numbers (comment #29 / handoff #34 / true position).
    # A Tier 1 reviewer caught it. ⇒ the warning was not enough on its own; read it as a RULE, not
    # as background prose.
    # WHY THE GATE EXISTS (MEASURED 2026-09-04): SIX of §Ch23's seven fault arms were unregistered,
    # so `_fault(arm)` — which builds its env name with an f-string — read a variable nobody sets
    # and returned False FOREVER. Every one of them was DEAD FROM CREATION while the docs described
    # them as the arms that prove those legs' guards work. A runtime raise only fires if someone
    # happens to DRIVE that leg (this survived until a real Wally drive); this is the static half.
    # Fault-tested three ways (`POKEBOT_CH23ARMS_FAULT=unregistered|orphan|noregistry`).
    ("probe_ch23_fault_arms.py", False),
    # #35 — a CLOSED punch-list item must never be described as OPEN by another item.
    # ‼ APPENDED AT THE END, never inserted — see #34's note; that rule was broken hours before this.
    # WHY: P5 ("an item's status and the handoff's claim move TOGETHER") failed THREE times in
    # 2026-09, twice inside the SAME item, always as "closing a CHILD is not updating the PARENT".
    # Three rounds of prose did not fix it, so per SESSION DISCIPLINE #6 it became a gate.
    # ⛔ AND IT WAS ONLY TRUSTED AFTER IT CAUGHT A RECONSTRUCTION OF THE REAL BROKEN FILE: it passed
    # clean TWICE first (line-by-line, then bullet-wise but unflattened) while its own fault arm
    # "proved" it worked. A gate is not proven by its own fault arm.
    ("probe_closed_item_refs.py", False),
    # --- #36 — `#24-e4healing`: the OUT-OF-BATTLE healing policy (`modules/story/overworld_items.py`)
    # ‼ APPENDED AT THE END, never inserted — the same rule #34 and #35 carry.
    # WHY A GATE: the policy runs between Elite Four rooms, where there is no nurse, no shop and no
    # way back, so a wrong choice is unrecoverable rather than merely wasteful. The module is PURE,
    # so exhaustive checking costs milliseconds and there is no excuse not to.
    # ⛔ AND IT WAS ONLY TRUSTED AFTER A REAL FAULT TEST BROKE THE PRODUCTION MODULE FOUR WAYS.
    # The first version was BLIND to its single most important rule (revive by battle value, not
    # slot order): the fixture fainted Sceptile at slot 0 and Zigzagoon at slot 1, so "lowest slot"
    # and "highest level" both answered Sceptile and the two policies were INDISTINGUISHABLE.
    # ⇒ **a check whose arms give the same answer on the chosen fixture is vacuous**, and it passes
    # loudly. Both revive checks now put the high-level mon LATER in slot order than a decoy.
    ("repro_overworld_items.py", False),
    # --- #37 — a CLOSED punch-list header may not sit over its OWN still-open body
    # ‼ APPENDED AT THE END, never inserted — the same rule #34, #35 and #36 carry.
    # WHY A GATE: this exact defect cost FIVE Tier 1 rounds on 2026-09-05, and it was caught in BOTH
    # directions on the same item — a header commanding a rebuild of work shipped in the same commit,
    # then, after "fixing" it, a header claiming closure over a body still reading "still open".
    # ⛔ THE GAP WAS BETWEEN TWO EXISTING CHECKLISTS: `audit_doc_consistency.check_touched_ki_pairs`
    # checks KI headers, `probe_closed_item_refs` checks a closed item described as outstanding BY
    # ANOTHER item — and nobody checked a punch-list header against ITS OWN body. A checklist
    # protects exactly what it enumerates.
    # ⭐ Deliberately NARROW, and SILENT on marked history / 🔶 MIXED / 🔜 open items / fenced code,
    # because a gate with false positives teaches the reader to bypass it. 7 fault arms:
    # `probe_item_header_body.py --self-test`.
    ("probe_item_header_body.py", False),
    # --- #38 — `KI-90`: the bot aims at an ABSENT opponent slot in a DOUBLE battle and raises
    # ‼ APPENDED AT THE END, never inserted — the same rule #34-#37 carry.
    # WHY A GATE, AND WHY IT IS SAFE TO BE ONE: this repro asserts that an OPEN defect still
    # reproduces, which would normally be a BOOBY TRAP — the suite would go red the moment someone
    # FIXED the bug, punishing exactly the work the repro exists to enable. ⇒ it SELF-RETIRES:
    # if the raise is gone while its discriminator still passes, it prints SELF-RETIRED and exits 0.
    # ⛔ The retirement test keys on BEHAVIOUR, not on the exception's message: raised anything ->
    # the defect is LIVE whatever the wording; returned cleanly -> SELF-RETIRED; step cap -> the
    # repro is broken, fail loudly. ‼ It keyed on the MESSAGE TEXT first, and a Tier 1 reviewer broke
    # it by rewording the raise while leaving the defect untouched — it retired a live defect.
    # ⇒ A GUARD KEYED ON A HUMAN-READABLE STRING IS NOT A GUARD ON BEHAVIOUR.
    # ⭐ It also computes its DISCRIMINATOR before driving anything, because the FIRST repro spec
    # written for KI-90 was vacuous: "left slot absent" alone cannot raise (`story_mode.py:261-313`
    # already aims right), and that arm would have reported "does not reproduce".
    ("repro_ki90_absent_left_slot.py", False),
    # --- #39 — `KI-95`: the faint chooser's replacement ranking (`rank_replacement`)
    # ‼ APPENDED AT THE END, never inserted — the same rule #34-#38 carry.
    # WHY A GATE: `choose_new_lead_after_faint` has had THREE index-space bugs (`KI-18`, `KI-34`,
    # `KI-66`) and every one needed a ROM, a live battle and a staged faint to see — which is
    # precisely why they kept happening. `KI-95` (ranking on a bare type multiplier, so a 40 BP
    # super-effective move outscored a 100 BP neutral one) is the first found by READING the code.
    # ⭐ THE DURABLE FIX IS NOT THE METRIC, IT IS THE TESTABILITY: the ranking is now a PURE function
    # taking an injected damage estimator, so this runs offline in milliseconds with no ROM.
    # ⛔ FAULT-TESTED: `POKEBOT_KI95_PROBE_FAULT=legacy` feeds it the pre-KI-95 metric, and EXACTLY
    # C1 goes red — the other SIX cases (C2-C7) are deliberately independent of the offensive
    # metric's scale, so a fault that knocked them over too would prove the probe was coupled where
    # it claims not to be. A probe that passes in both arms measures nothing.
    # ‼ THIS COMMENT SAID "the other four" until 2026-09-06, hours after C6 and C7 were added — an
    # independent reviewer caught it. A count in prose beside a list that grows is a pair, and both
    # halves move together.
    ("probe_faint_chooser_rank.py", False),
    # --- #40 — `KI-93`: the drive GRADER's own five fault arms
    # ‼ APPENDED AT THE END, never inserted — the same rule #34-#39 carry.
    # WHY A GATE: `grade_ki93_drive.py` is the instrument that decides whether a `KI-93` drive is
    # believable, and it SHIPPED THREE BUGS IN ONE NIGHT — it flagged correct behaviour (its
    # invariant was keyed on slot, not Pokemon), then returned PASS on the known-bad log (it could
    # not read identity there), then returned PASS on a drive where the fix never engaged. Each was
    # caught by a human reviewer rather than by the tool. ⇒ the arms are now embedded.
    # ⛔ THE ARMS ARE SYNTHETIC ON PURPOSE: the real drive logs live under `profiles/`, which
    # `.gitignore` excludes, so pointing at them would make the fault matrix unreproducible on a
    # fresh clone — and `#24-reprosweepratchet` is blunt that what the suite does not run, rots.
    # Bare invocation runs `--self-test`: good drive -> 0; cross-mon veto leak, missing identity,
    # vacuous drive, and missing control line -> 1.
    ("grade_ki93_drive.py", False),
    # --- #41 — the x4 batch runner's own reporting + build selector
    # APPENDED AT THE END, never inserted — the same rule #34-#40 carry.
    # WHY A GATE, AND WHY NOW: this repro has covered `x4_headless.py`'s parsing since 2026-07-31 but
    # was NEVER REGISTERED, so nothing ran it — exactly the rot `#24-reprosweepratchet` describes
    # ("none of the 104 repros is in run_gates.py, and what the suite does not run, rots").
    # It got urgent on 2026-09-07 when `--build` and `--status` landed: `--build` decides WHICH FORK a
    # batch measures (a finish rate whose build is unknown is not a measurement), and `--status`
    # shipped WRONG once already — it counted the literal string "FINISHED" and reported 0% for a
    # batch whose own INDEX row records 36%.
    # Pure and fast: it parses fixtures and reads two source files. No ROM, no emulator.
    ("repro_x4_headless.py", False),
    # --- #42 — `KI-97`: the Fortree-gate drive GRADER's own six fault arms
    # APPENDED AT THE END, never inserted — the same rule #34-#41 carry.
    # WHY A GATE: `KI-97` killed 6 of 14 ended runs in the 2026-09-07 batch, and its acceptance
    # criterion is that a STRING DISAPPEARS — the weakest shape of evidence there is, because a run
    # that never reached Segment 13a satisfies it vacuously. This grader is what makes the
    # disappearance mean something, so the grader itself must be fault-tested.
    # ⛔ THE ARM THAT MATTERS MOST IS `_arm_benign_route119`, AND IT MUST PASS. The obvious grader —
    # "require zero `Route 119 already cleared` lines" — is WRONG: that line is also printed
    # legitimately before BADGE06, and the live batch contains 135+ benign occurrences against 23
    # real signature hits. Such a grader would have failed every healthy lane and taught the reader
    # to ignore it. The defect is the SEQUENCE (that line -> a Mauville (19,6) fail-fast), not
    # either line alone.
    # ⭐ VALIDATED ON REAL DATA, not only synthetics: against `x4-runs/20260907-073620` (the
    # PRE-FIX build) it exits 1, flagging the signature in the lanes that died of it.
    # ⛔ STATE THE INVARIANT, NOT THE SNAPSHOT — that batch was LIVE while this was written, and an
    # earlier comment here quoted "5 FAIL / 2 PASS / 1 INDETERMINATE" which a reviewer, running the
    # same command minutes later, could not reproduce (lanes had progressed). The durable claim is:
    # against a build WITHOUT the fix, PASS is **structurally 0** — `Ch13a skipped` cannot appear in
    # a build that lacks the line — while the FAIL count only rises as more runs end.
    # ‼ Three outcomes, not two: a lane that never reached Ch13a is INDETERMINATE, never FAIL, so the
    # gate does not fire on healthy early-game lanes — but INDETERMINATE can never stand in for PASS.
    # Bare invocation runs `--self-test`: good drive and benign-Route-119 -> 0; the signature,
    # a vacuous log, an over-gate, and an unattributed Mauville failure -> 1.
    ("grade_ki97_drive.py", False),
    # --- #43 — HM COVERAGE: anything the story REQUIRES someone to know must have a TEACH step
    # APPENDED AT THE END, never inserted — the same rule #34-#42 carry.
    # ⛔⛔ WHY: this is the most expensive gap in the project's history and it was STRUCTURAL. §Ch23's
    # preflight asserts a WATERFALL carrier; §Ch21 puts HM07 in the bag; **production never taught
    # it**. Across 37 stored batches the 8th badge was reached six times and ALL SIX died on that
    # assertion — nothing ever passed it.
    # ‼ NO BEHAVIOURAL TEST COULD HAVE SEEN IT. §Ch23 was built, driven and green — from FIXTURES
    # captured downstream of a HARNESS DRIVER that did the teach. The chapter passed its own tests
    # for days while the route reaching it was impassable. A fixture encodes everything the step
    # before it did, INCLUDING steps that exist only in the harness. Only a structural check sees it.
    # ⭐ VALIDATED ON REAL CODE IN BOTH DIRECTIONS, not only synthetics: `--build sandbox` (which has
    # the 2026-09-07 teach) exits 0, and `--build custom` (which does not yet) exits 1 naming
    # `assert_ch23_preflight` — i.e. it catches the ACTUAL historical bug on the fork that still has
    # it. A grader proven only on synthetic arms can still be blind to the real thing: an earlier
    # regex version of this gate PASSED the broken fork and FAILED the fixed one, because the real
    # preflight expresses its requirement as a loop over a tuple. It is AST + function-scoped now.
    # ‼ BARE = SELF-TEST **AND** AUDIT SANDBOX. A gate whose default mode only runs synthetic arms
    # proves the checker works and nothing about the code. Sandbox, not custom: custom fails today
    # for a KNOWN correct reason (unpromoted fix), and a gate red for a good reason gets ignored.
    # Pure and fast: parses Python, reads no ROM.
    ("probe_hm_coverage.py", False),
    # `#24-whiteoutloop` — the batch's #1 failure class (14 of 53 ended runs, 26%). The whiteout
    # counter had NO reset site while its message said "in a row", so it was a LIFETIME loss quota
    # that killed runs winning 86-96% of their battles, after whiteouts spread over a median of 13
    # different towns. Now keyed to CONSECUTIVE whiteouts at ONE location.
    # ‼ A GATE, NOT A DRIVE, AND DELIBERATELY: reproducing this needs 41 whiteouts — many hours of
    # emulation. The decision is PURE, so the gate replays the 14 REAL killed sequences (frozen in
    # `fixtures/whiteout-sequences-20260907.json`) instead. Rule 9: choose the instrument by the
    # question.
    # ⭐ ITS FAULT ARM 1 IS THE POINT — it replays the OLD counter and requires it to kill 14 of 14.
    # Without that control CHECK 1 was VACUOUS: the first fixture held 40 events, one short, so no
    # budget could trip a `> 40` cap and "0 of 14 killed" meant nothing. The arm caught it.
    # Pure and fast: replays a JSON fixture, reads no ROM.
    ("probe_whiteout_budget.py", False),
    # ⛔ A `NameError` only fires on the branch nobody drives, so it survives every green suite until
    # an emulator run finds it. That happened THREE times on 2026-09-08 in one session:
    #   `os`      — `story_harness.py` binds it as `_os`;      `grep -c "^import os"` said "fine".
    #   `console` — `victory_road.py` binds it FUNCTION-LOCALLY; `grep -c "console.print"` said "fine".
    # ⭐ A usage grep cannot see WHERE a name is BOUND. Only scope analysis can, so this gate walks
    # the real scope chain: builtins + MODULE-LEVEL bindings (⛔ not descending into other functions)
    # + the function's own + every enclosing function's (closures are legal).
    # ‼ Its self-test has 5 arms — 2 fault, 3 no-fire — and it was ALSO fault-tested against the real
    # `victory_road.py` with that one import line deleted, where it correctly reports ['console'].
    # ⭐ MEASURED CLEAN BEFORE SHIPPING (rule 6 — a noisy gate teaches bypass): 6,540 functions across
    # both forks, 0 findings. Three earlier drafts were discarded at 32 and 8 false positives, and a
    # fourth reported 0 for the WRONG REASON (its module scope swallowed function-local imports, so
    # it would have missed the very bug it was built for — its own arm caught that).
    # Pure and fast: parses Python, reads no ROM.
    ("probe_name_resolution.py", False),
    # ⛔⛔ THE DRIFT FIGURE IS THE MOST PERSISTENT DOC DEFECT IN THIS TREE — 13 instances, 12 of them
    # recurrences. `04-HANDOFF.md` self-documents #10 (*"the 10th STALE COPY … survived both a
    # nine-site sweep AND a green gate"*), and the edit that "fixed" it to 0 was wrong the next day.
    # ⭐ THE REMEDY IS TRANSPLANTED, NOT INVENTED: line budgets already solved this exact class with
    # *"NO COUNTS ARE QUOTED HERE — RUN `lint_docs.py`"*, because a count written into the file it
    # describes is stale the moment it is written. Drift never got that treatment; now it has one.
    # A drift digit is a violation unless it is (1) the STATE row, (2) inside a quotation, (3) inside
    # a `code span` (a FILENAME, not a measurement), or (4) preceded by a past-tense marker.
    # ‼ WHY IT IS A GATE AND NOT A SWEEP, with numbers: an audit listed 3 instances, a Tier 1 reviewer
    # found a 4th, a hand grep found a 5th — and this gate found SIX MORE, including a live, wrong
    # *"drift is 5"* in `03-PUNCH-LIST.md`. Every authored LIST was incomplete; only the pattern was.
    # ⭐ 7 arms (2 fault, 5 no-fire). Its first draft used `\W{0,12}` and could not cross `" is "`,
    # so it reported real findings while BOTH fault arms silently failed — inert against its own
    # purpose, exactly like `archive_doc_block.py`'s invariant C. Read the arms, never the count.
    # Pure and fast: reads Markdown, reads no ROM.
    ("probe_drift_restatement.py", False),
    # ⛔⛔ `#24-promotedpairgate` — SEVEN instances of one shape in a single day, every one caught
    # by COST (a diff advisory, a Tier 1 reviewer, a Tier 2 audit) and never by a check. A KI whose
    # 05 HEADER says PROMOTED/FIXED/CLOSED may not be called NOT PROMOTED / STILL OPEN in a LIVE
    # clause of the handoff. ⭐ CLAUSE-scoped, never line-scoped: the item RECORDS a dry run where
    # the line-scoped design produced 6 findings (all false) and then 6 -> 23 AFTER the document got
    # MORE accurate, because the metric tracked LINE LENGTH. ✅ Found an 8th instance on its first
    # live run (`KI-95` “sandbox-only, unpromoted” against a PROMOTED header) and ships at 0.
    ("probe_promoted_pair.py", False),
    # ⛔⛔ PAIR **P3** BROKE THREE TIMES IN THE SAME FILE, THE SECOND TIME INSIDE A COMMIT ABOUT
    # THE FIRST — so prose has demonstrably failed and this is the gate `CLAUDE.md` asks for. The
    # recipes block is what a COLD READER copies, so a stale line there does not cost a minute of
    # confusion, it costs HOURS of emulator time and returns an unusable party. ✅ On its FIRST run
    # it found a live break the Tier 1 reviewer had NOT flagged (a second `post_grind_L60.ss1`
    # recipe, whose own adjacent comment already said "NOT A REPRO ANY MORE" while the command
    # stayed executable for nine days). ‼ It scans RUNNABLE lines only — the fixed block names the
    # dead fixture in a WARNING, and a gate that fired on its own fix would teach people to bypass
    # it; `POKEBOT_RECIPEGATE_FAULT=1` scans comments too and MUST fail. ⚠ "Named but unpinned" is
    # REPORTED, not blocking — a different gap, pre-dating this gate.
    ("probe_runrecipe_fixtures.py", False),
    # ⭐⭐ #62 — `KI-74` IN BOTH DIRECTIONS, ON ONE MAP AT ONE INSTANT. The ENTRY tiles read
    # ROM=0/LIVE=3 (sealed at runtime) and the EXIT door reads ROM=1/LIVE=0 (opened at runtime),
    # with two ordinary tiles AGREEING in both grids so a divergence is about the door and not
    # the reader. ‼ Two divergences in OPPOSITE directions is the point: one could be dismissed
    # as "our ROM reader is wrong about this map", two cannot. What this gate actually protects
    # is `_live_collision_grid` — the only reader that can see runtime `setmetatile` writes, and
    # the thing standing between us and a bot that confidently plans a RETREAT the game refuses.
    # Its failure mode without this gate is a jam in the Elite Four, hours into a run.
    # ⚠ True = BOOTS A ROM, so `--quick` skips it. It loads a save state into libmgba to read
    # `gBackupMapLayout`; there is no offline way to ask what the GAME thinks a tile is.
    ("probe_e4_entry_seal.py", True),
    # ⭐⭐ #63 — THE POLICY THAT SPENT A ~700,000-FRAME ITEM. `which_move_should_be_replaced`
    # counted type coverage over the REPLACEABLE slots, which exclude HMs, so a Wailord holding
    # three Water HMs + Ice Beam read as "no Water" and traded Ice Beam for Hydro Pump at L59.
    # ‼ The three arms are the point: ARM 1 alone would be satisfied by a policy that declined
    # EVERYTHING, so CONTROL A proves a genuine new type is still accepted and CONTROL B proves a
    # same-type upgrade still lands. ⚠ True = boots a ROM: it runs the policy against the REAL
    # pinned party rather than fakes, because twice in one day a hand-built probe fixture was
    # wrong while its subject was right.
    ("probe_learn_hm_coverage.py", True),
    # ⛔⛔ `_derail_reason` grouped with a DECIMAL-only `\d[\d,]*` pass while a PID is HEX, so
    # `Marill#30AD95BD` -> `Marill#NADNBD` and EVERY PID BECAME ITS OWN KEY. `summary.json` is written
    # through `.most_common()`, so the biggest blocker scattered into count-1 rows at the BOTTOM.
    # ⭐ MEASURED on batch `20260907-203713` (49 real outcomes): Ch23 training went 16 keys -> 6, and
    # the displayed #1 changed from a 6-count cause to the true 9-count one. THE RANKING INVERTED —
    # every agent, gate and human reading the top of that file got the wrong blocker, low by ~3x.
    # ‼ THIS GATE EXISTS BECAUSE A TIER 1 REVIEWER ASKED WHERE THE EXECUTABLE ARM WAS: the fix had
    # been validated only by a one-off manual re-aggregation quoted in the changelog, and a number in
    # a changelog cannot fail when someone edits the regex back.
    # ⭐ Its own fault test is recorded: with the PID line deleted it exits 1; restored, 0.
    # Its load-bearing check is the GROUPING one — two outcomes differing ONLY by PID must produce
    # the SAME key, which a single-string arm cannot see.
    # Pure and fast: imports one function, reads no ROM.
    ("probe_derail_grouping.py", False),
    # ⛔⛔ `team_is_ready` builds its verdict by APPENDING to `reasons` while looping over
    # `battler_identities()`. An EMPTY dict means the loop never runs, `reasons` stays [], and it
    # returns **(True, [])** — a party with nothing that can fight the Elite Four is certified READY,
    # silently, and §Ch23 returns early having trained nobody.
    # ⭐ A CHECK THAT ANSWERS WITHOUT ASKING — the third of that shape in this one function (the
    # `POKEBOT_CH23_TRAIN_TARGET=53` flag that reached half the function; the Crunch test that
    # stopped asking at exactly L47). All three grade PASS by never evaluating.
    # ‼ GATED NOW, BEFORE IT IS NEEDED: the only untested fix direction left on `#24-lowlevelmules`
    # is benching by ROLE in `battler_identities`, and a predicate one clause too broad EMPTIES the
    # set — surfacing as a PASSING run, this project's most expensive failure mode.
    # ⭐ 4 arms (1 fault, 3 no-fire, incl. "a genuinely ready team still passes"), run against the
    # REAL function with `battler_identities`/`get_party` monkeypatched. Fault-tested: disable the
    # guard and it exits 1; restored (byte-identical) it exits 0.
    # Pure and fast: imports one bot module, reads no ROM.
    ("probe_empty_battler_guard.py", False),
    # `#24-dexhunt` — THE CATCHING FENCE, 2026-09-10. `decide_dex_catch` is PURE, so all 18
    # conditions are interrogated offline in milliseconds.
    # ⛔⛔ IT IS GATED BECAUSE THE DRAFT SPEC FOR THIS FEATURE CALLED A FUNCTION THAT DOES NOT EXIST
    # (`counter_hunt.hunt_active()`; the real name is `is_armed()`). `_should_catch` wraps its body
    # in `except Exception`, so the `AttributeError` would have been SWALLOWED: the fence would
    # never fire, and the 8-hour A/B would print "no difference" — reading as a REFUTATION of a
    # feature that never ran. A pure predicate plus this gate makes that class unshippable.
    # ⭐ The load-bearing cases are the ones a "just relax the badge gate" patch would fail: C3
    # (party 4/6 refuses — the runway `#24-partycap` measured at 36 points), C8 (the ball reserve is
    # a LEVEL, not a boolean, because `counter_hunt.hunt()` checks balls at :471 and only arms at
    # :510, leaving `is_armed()` False across its whole journey), and C15 (an EGG occupies a slot,
    # so 5 mons + 1 egg is FULL — the two party-count conventions are built to DISAGREE there).
    # ⛔ It proves CORRECTNESS, never EFFICACY — that needs a batch. `probe_dexfence_opportunity.py`
    # is the (measured) proof such a batch would not be vacuous.
    # Fault-tested: `POKEBOT_DEXFENCE_FAULT=nofence` restores pre-fence behaviour and C3/C5-C9/C14/
    # C16 all go RED, exit 1. Pure and fast: imports one bot module, reads no ROM.
    ("probe_dex_catch_fence.py", False),
    # `#24-dexhunt` — THE VACUITY CHECK for the batch that will grade the fence, 2026-09-10.
    # Answers OFFLINE, from the recorded corpus, whether the fence can EVER fire; a feature that
    # cannot fire makes its own A/B print "no difference".
    # ⚠ ADVISORY, DELIBERATELY: it measures a CORPUS, not the code. A batch run with `--build custom`
    # (no `ids=`/`owned=` telemetry) correctly reports zero, and that is a fact about the corpus, not
    # a regression — failing the suite over it would teach the reader to bypass the gate.
    # Fault-tested: `POKEBOT_DEXFENCE_PROBE_FAULT=1` raises FULL_PARTY to an impossible 7 and the
    # window collapses 4286 -> 0, exit 1.
    # ‼ `slow=False`: it boots no ROM. MEASURED at 10.8s (it walks ~1,400 corpus logs), which is
    # real but well inside the no-ROM tier — quoted here because an unmeasured "it's fast" is how
    # a suite acquires a time bound it cannot keep.
    ("probe_dexfence_opportunity.py", False),
    # §Ch23 leg 4 vs the League interior, 2026-09-10. `at_ever_grande_top()` required
    # `_on_map(EVER_GRANDE_CITY)`, but every League room is its OWN map and the League is not in
    # `VICTORY_ROAD_MAPS` — so from inside the building BOTH of leg 4's guards read False and the
    # chapter fired an OCEAN CROSSING from indoors, burning all three attempts and RAISING.
    # ⛔ A DERAIL AMPLIFIER: it turns one recoverable §Ch24 fault into a hard §Ch23 failure.
    # ⭐ Two arms, each attacking a different claim, and BOTH are load-bearing:
    #   `=nofix`  restores the pre-fix predicate -> C1+C2 red and NOTHING ELSE. That second half is
    #             the finding: the bug was ONLY the interior, so the report claiming it "returns
    #             False at the League door" had the mechanism wrong (6 <= 55 was already True).
    #   `=prefix` swaps the explicit map set for `startswith("EVER_GRANDE_CITY_")` -> C6 red,
    #             because that swallows the POKÉ CENTER, which shares the prefix and is not the
    #             League. Not a strawman: it is the simplification a maintainer would reach for.
    # Pure and fast: imports two bot modules, reads no ROM, drives no emulator.
    ("probe_league_leg4_guard.py", False),
    # `#24-regimeb-noescalation` — the FIRST loss adaptation after Winona, 2026-09-10.
    # `_prepare_for_fight` was last called at badge 6; from badge 7 on, N whiteouts was N
    # IDENTICAL losses. Two grass-less configs (Tate & Liza, Juan) wire the existing
    # machinery to badges 7-8.
    # ⛔ GRASS-LESS IS THE MEASURED DESIGN, NOT AN OVERSIGHT: `TRAINING_GRASS` tops out at
    # ROUTE121 L25-28 while the opposition is L41-46, so no tabled ground can train for
    # these fights. C2 asserts the omission so a later "helpful" addition must argue with it.
    # ⭐ C4 pins the bands to the DECOMP — Juan's ace (Kingdra L46) is FIVE levels above his
    # roster bulk, so a band read off the bulk misses the mon that wins the fight.
    # Two arms (`=grass`, `=band`), both real maintainer mistakes. Pure: AST + regex, no ROM.
    ("probe_late_boss_configs.py", False),
    # 54 — EVERY REGISTERED GATE THAT BOOTS AN EMULATOR MUST UNTHROTTLE IT.
    # ⛔ Written after a MEASURED 16-day outage, not as a precaution. `repro_gym_whiteout_guard.py`
    # set `context.audio`/`context.video` but not the third line of that triple,
    # `context.emulation_speed = 0` — and `audio = False` only silences the SAMPLES, while the
    # per-frame `_audio_stream.write()` that PACES the emulator to 60fps is guarded by
    # `if self._throttled:` alone (`libmgba.py:593` vs `:618-621`). So the gate walked a long gym
    # route at REAL TIME and was killed at this runner's 900s bound. Its own drive budgets total
    # 46,000 frames = 766.7s at 1× before ROM/save-state load, so it sat right ON the bound. It was
    # PACED, never stuck. Filed 2026-08-26 as `#26-gatestartupcontention`; red until 2026-09-11,
    # so no full suite run could be green in between.
    # ⭐ A/B: throttled → 900s kill (×3); unthrottled → 107s, EXIT=0, 5/5 — its documented runtime.
    # ‼ The gate exists because FIVE MORE registered gates had the same omission and were passing
    # purely because their routes are short. Proven against the REAL pre-fix file, not only its own
    # `=1` arm. Pure: reads the registry + source text, no ROM.
    ("probe_gate_unthrottled.py", False),
    # 55 — `#24-maintain`'s decision, every branch, plus the predictions filed before it was built.
    # ⛔ THE BOUNDARY IT DEFENDS: `06-DECISIONS-LOG.md` 2026-09-10 REJECTED training a lagging mon to
    # the BOSS's level (L40→L47 = 285,167 frames vs a 250,000 ceiling; and a L33-40 ground cannot be
    # won at — 69 battles, 0/43 HP, still L13). This item survives only by changing the two variables
    # that arithmetic is sensitive to: the target is `boss_target - TRAIN_CATCHUP_GAP`, and the
    # ground is keyed to the LAGGARD's level. C7/C8 assert exactly that, so a future "why not train
    # it to the boss level?" edit must argue with the measurement.
    # ⭐ C13 is the VACUITY conjunct and it earned its keep: the `=gap` arm (decide on a gap vs party
    # MAX) leaves every single-party case GREEN and is caught ONLY by C13, which holds the party
    # fixed and varies the boss target. Three arms, each reds exactly its own cases. Pure: no ROM.
    ("probe_maintenance_decision.py", False),
    # 56 — NO `yield` INSIDE A `finally` ON THE STORY SURFACE. It is a latent crash, not a style
    # rule: closing a generator that is suspended inside the matching `try` raises
    # **RuntimeError: generator ignored GeneratorExit**, and CPython closes abandoned generators at
    # GC time — so a mode switch or a discarded story run is enough. This gate REPRODUCES that at
    # runtime on every invocation rather than asserting it, so the day the semantics change it says
    # so instead of quietly guarding nothing.
    # ⛔ TWO REAL INSTANCES existed the day it was written: `#24-maintain`'s new step (caught before
    # it ever ran) and `victory_road.py:2099` — ALREADY-PROMOTED production code whose comment read
    # "⛔ IN A `finally` ON PURPOSE". The intent was right, the mechanism was a crash ⇒ a
    # deliberate-looking comment is not evidence of safety. Proven against that real pre-fix file,
    # not only its own arm. Pure: AST + a 6-line runtime demo, no ROM.
    ("probe_yield_in_finally.py", False),
    # #57 — `#24-maintain` must REFUSE training grounds it cannot walk to, and ABANDON the errand
    # rather than kill the run when it finds one anyway.
    # ⛔ THE ONLY GATE IN THIS SUITE WHOSE JUSTIFICATION IS A COMPLETED A/B THAT SAID "SHIP NOTHING".
    # The 2026-09-12 batch (32 lanes x 310 min per arm) measured the feature as net-HARMFUL: median
    # run length 99 KB with maintenance ON vs 537 KB OFF, badge-7 rate 0.9% vs 3.7%, and 406 runs
    # killed by a family of `Could not reach (X,Y) on ROUTE<N>` derails that the control arm never
    # suffered ONCE. All of it flowed from one picker that chose on level fit with no idea where the
    # player stood, plus a handler that re-raised a best-effort errand's failure into the run.
    # ‼ Gates the ADDITIVE guarantee too (`allow=None` filters nothing), because `best_training_grass`
    # is ALSO injected as `decide_maintenance`'s `ground_for` — narrowing its default would have
    # moved gate #55's answers as a silent side effect of a bug fix.
    # Pure: AST + the real picker, no ROM. Four fault arms, each measured to red only its own cases.
    ("probe_maintain_unreachable.py", False),
    # #58 — `#24-wallydecline`: the Mauville Wally masher must never be able to press B at a
    # yes/no box. ⛔ THIS GATE IS STATIC **BECAUSE A BEHAVIOURAL ONE CANNOT BE TRUSTED HERE.** The
    # defect is PHASE-LOCKED: with the guard removed, a fixture whose phase lands on A still passes.
    # It did — the pre-fix `mash` arm returns `ACCEPTANCE: PASS` on `mauville_prewattson.ss1`, and so
    # did the very first repro against unfixed code. ⇒ a test run is not a regression detector for
    # this; a text check is. Cost of the original: **124 of 143 ended runs** (= 60% of 207 started)
    # died frozen at MAUVILLE (8,7), because B is "NO" at a Gen-3 yes/no, declining sets a flag
    # nothing in the decomp clears, and Wally stands on the only tile the gym door opens from.
    # Also checks `_dialogue_button` still DELEGATES to `_yes_no_menu_is_open`, so the two yes/no
    # predicates cannot drift. Custom is ADVISORY until promoted, then enforced automatically.
    # Fault-tested 2026-09-13: guard removed -> RED (exit 1), restored MD5-identical.
    ("probe_yesno_guard.py", False),
    # #59 — `#24-e4healing` step 3: the in-battle policy for items whose `parameter` is 0.
    # ⛔ THIS FILE EXISTED AND WAS NOT IN THE SUITE. `repro_battle_items.py` has gated
    # `choose_healing_item` since it was written, and nothing ran it — so the HP policy was
    # effectively ungated and the new status/revive policy would have been too. Found while adding
    # step 3 on 2026-09-13. ⇒ *a repro that is not in `run_gates.py` is a test nobody runs.*
    # WHY THE POLICY MATTERS: `06-DECISIONS-LOG.md` 2026-09-04 measured that the in-battle filter
    # `param > 0` excludes Full Heal / Revive / Antidote (all `parameter == 0`), so **11 of the 44
    # items bought for the ₽54,300 Elite Four basket were unusable by any code path**.
    # The new checks include the CONFUSING NEIGHBOURS the real bag holds (Repel, whose parameter is
    # 100 = STEPS, and an X Attack) because `overworld_items.py` records a live drive where filtering
    # by `parameter > 0` selected a Repel — "the gate missed it because its item universe was CLEANER
    # THAN REALITY."
    # Pure: no ROM, no emulator, milliseconds. Fault-tested 2026-09-13 — widening
    # `TURN_COSTING_STATUSES` to include chip statuses reds exactly 3 of 46 checks and exits 1.
    ("repro_battle_items.py", False),
    # #60 — the STATE MACHINE around the item policy, which #59 structurally cannot see.
    # ⛔ A Tier 1 reviewer caught this BEFORE it shipped: the no-op detector judges an item by
    # whether OUR HP ROSE by the next decision, and a status cure NEVER raises HP. So every
    # SUCCESSFUL cure read as a failure — the first flipped the index space, the second set
    # `_items_ineffective = True`, disabling ALL item use (including HP emergencies) for the rest of
    # that battle. Two cures in one fight is not exotic: `pokemon_league.py`'s own driver stages a
    # FROZEN Sceptile precisely because freeze and sleep both occur.
    # ‼ #59's 72 checks could not see it — they are pure-function and static-source. This drives the
    # REAL `_maybe_use_item` with the emulator edges faked. ⇒ a policy can be perfect and its
    # integration still broken; gate the state machine separately.
    # Fault-tested 2026-09-13: reverting the kind-awareness reds 5 of 11 — including
    # "the HP-emergency path STILL WORKS after two cures", which returns None, i.e. the exact
    # regression the reviewer predicted. Pure: no ROM, no emulator, milliseconds.
    ("repro_item_noop_detector.py", False),
    # ---------------------------------------------------------------------------------------- #61
    # ⛔ APPENDED, NEVER INSERTED — gate ordinals are cited in prose across PROJECT KNOWLEDGE.
    # A punch-list item may not tick a numbered step `[x]` and ALSO say elsewhere in the same item
    # that the step "remains". ‼ WHY IT EXISTS: that exact contradiction shipped TWICE IN 24 HOURS
    # on `#24-e4healing` — 2026-09-13 (step 3: checklist ticked, STATUS line stale) and 2026-09-14
    # (step 4: checklist ticked, cell header AND STATUS line stale). Both were caught by Tier 1
    # reviewers, i.e. by luck and cost, not by a check. P5 is prose; CLAUDE.md says a rule broken
    # twice means the prose failed and the gate should be written instead.
    # Fault-tested 2026-09-14: restoring the old `"steps 2 and 4 remain"` STATUS line reds it with
    # `FAIL 03-PUNCH-LIST.md:391 says step 4 REMAINS, but the same item ticks it [x] at :483`, and
    # the file was restored byte-identically (sha256 verified). ⭐ It does NOT fire on the dated
    # RETRACTION that quotes the old wording — the live tree contains exactly such a quote and the
    # gate passes, which is the false-positive arm.
    ("probe_punchlist_step_status.py", False),
    # --- #62 — the FORK-DRIFT METER's own five fault arms (`promote.py --self-test`)
    # ‼ APPENDED AT THE END, never inserted — the same rule #34-#61 carry.
    # WHY A GATE: `promote.py --check` is called *the authority* on sandbox↔custom drift in four
    # places, and on 2026-09-15 it was measured WRONG — a permanent phantom `drift: 1` on a file git
    # stored as ONE blob (`core.autocrlf=true` had materialised one copy with CRLF, and the meter
    # hashed raw bytes). A phantom either invites the no-op promotion `promote.py`'s own docstring
    # says it refuses to make, or teaches the reader that the number is noise — and the next REAL
    # drift, a fix that never reached the fork that SHIPS, then goes unseen.
    # ⛔ THE FIX (ignore line endings) BUYS A FALSE-NEGATIVE RISK, WHICH IS THE ONE THAT COSTS.
    # So it is tested, not trusted. Arm A is the CONTROL THAT MUST FIRE: two files ONE CHARACTER
    # apart must still read as drift. Without it, a `_digest` returning a constant passes every
    # other arm perfectly. Arm E pairs a content change WITH an ending change, so "cosmetic" can
    # never become an excuse that swallows a real one.
    # ⭐ It drives the SHIPPED `measure()` over real files in a temp tree rather than re-deriving
    # the comparison — a self-test that re-implements its subject passes whenever the two
    # implementations agree, including when both are wrong.
    ("selftest_promote_drift.py", False),
    # --- #63 — RETRACTION COVERAGE (`probe_retraction_coverage.py`)
    # ‼ APPENDED AT THE END, never inserted — the same rule #34-#62 carry.
    # WHY A GATE: on 2026-09-17 I retracted three claims and, for each, left another copy of the SAME
    # sentence live elsewhere — a closed punch-list item still reading "all three prerequisites still
    # stand"; my own decisions-log entry still reading "not a re-plumbing job"; and "Grind past L62
    # toward ~L75 BEFORE building more legs" marked in ONE of its TWO verbatim occurrences in
    # `04-HANDOFF.md`. Two were caught by Tier 1 reviewers, i.e. by cost. `08-MISTAKES.md` ALREADY
    # carried the rule and I broke it anyway ⇒ CLAUDE.md §6: prose failed, write the gate.
    # ⭐ THE CATEGORY ERROR IT REMOVES: "is this copy historical?" is a JUDGEMENT about surrounding
    # prose; "does a marker sit next to THIS copy?" is a FACT about bytes. The gate only asks the
    # second. A marker 208,000 chars earlier in the same line does not cover a later copy.
    # ⛔ FAULT-TESTED, AND IT FAILED TWICE BEFORE IT PASSED — which is the only reason it is trusted:
    #   v1 matched the prose BETWEEN two quotations (1,004 bogus claims, 199 false positives);
    #   v2 let a claim CONTAINING a keyword excuse itself, so the injected-defect arm read ZERO.
    #   v3 (shipped) requires the past-reference idiom ("THIS clause READ …") AND an adjacent
    #   retraction keyword, and excludes the claim's own text from the marker window.
    # Arms: real tree clean / unmarked copy injected MUST fire / same copy WITH a marker must NOT /
    # sub-threshold fragments never harvested. `--self-test` runs all four.
    # ⛔⛔ THIS BLOCK ORIGINALLY READ "SAFE TO ENFORCE BECAUSE IT FAILS SAFE: an unrecognised
    # retraction idiom is simply not harvested, so the failure mode is a MISS, never a false alarm."
    # ‼ THAT CLAIM IS WITHDRAWN — IT WAS REFUTED THE SAME DAY, FROM BOTH DIRECTIONS, AND THE GATE IS
    # NOW ADVISORY (see the ADVISORY frozenset above for the two defects and their repros).
    # ⭐ THE DURABLE LESSON, worth more than the gate: **A FAULT TEST PROVES THE ARMS YOU THOUGHT OF;
    # IT DOES NOT PROVE THE PROPERTY YOU CLAIMED.** Four arms passed — real tree clean, injected
    # defect fires, marked copy silent, no sub-threshold matches — and the property those arms were
    # meant to establish ("fails safe") was false in two independent ways that no arm looked for.
    # ⇒ When a gate's ENFORCING status rests on a PROPERTY, write an arm that attacks the PROPERTY,
    # not just arms that exercise the mechanism.
    ("probe_retraction_coverage.py", False),
    # --- #64 — INVISIBLE CHARACTERS IN THE KNOWLEDGE DOCS (`probe_doc_control_chars.py`)
    # ‼ APPENDED AT THE END, never inserted — the same rule #34-#63 carry.
    # WHY A GATE: on 2026-09-17 a changelog entry written through a shell-quoted string turned `\b`
    # into a LITERAL 0x08 BACKSPACE inside the document. Every terminal rendered it as an empty pair
    # of backticks, so it read as "the shell deleted my text" — the wrong diagnosis. It was PRESENT
    # AND INVISIBLE, and was found only because an assertion string failed to match and the bytes
    # were inspected instead of the rendering.
    # ‼‼ A SWEEP THEN FOUND A SECOND, OLDER ONE in `28-HANDOFF-ARCHIVE.md`, inside a sentence
    # explaining that a literal control character in source is a hard failure "because `\b` compiled
    # to a BACKSPACE twice in one day and the gate still passed." ⇒ THREE independent sessions have
    # put a backspace byte into prose ABOUT the backspace bug, and nothing caught any of them.
    # ⭐ THE GAP: control characters in SOURCE are gated (`#24-p2headergate` (C)); the DOCS were not.
    # `lint_docs.py` and `audit_doc_consistency.py` both passed a file containing 0x08.
    # ⭐ ENFORCING, AND THE JUSTIFICATION IS ABOUT THE INPUT DOMAIN, NOT THE CHECKER — the distinction
    # `probe_retraction_coverage.py` got wrong the same day. Markdown has NO legitimate use for any C0
    # control character except TAB and NEWLINE, so there is nothing to judge and nothing to misjudge;
    # a hit is a defect by construction. Contrast: that gate had to DECIDE whether text was retracted.
    # ⛔ FAULT-TESTED, six arms, and ARM 3 failed first: it exercised `scan_text` directly while the
    # CRLF normalisation lived in `scan_docs`, so a legitimate CRLF was reported. The gate was right
    # and the CONTRACT was split — normalisation moved into `scan_text`. A lone CR still fires (ARM 4).
    ("probe_doc_control_chars.py", False),
    # --- #65 — A GATE STRING NOTHING RESOLVES (`probe_caps_resolve_every_gate.py`)
    # ‼ APPENDED AT THE END, never inserted — the same rule #34-#64 carry.
    # WHY A GATE: `region_reach.py` keeps one fact in three places — `KNOWN_GATES` (which edges
    # are gated, on which capability STRING), `_GATE_MOVE_NAMES` (string -> field-move name), and
    # `_resolve_caps` (which strings actually get RESOLVED). Nothing made them agree. On
    # 2026-07-26 commit `0c1d6686` added a `"waterfall"` edge plus its move name plus its badge —
    # THREE of the four pieces — while `_resolve_caps` kept a hardcoded four-key literal.
    # `_bfs_distances` drops any edge whose gate is missing from `caps`, so the result was not an
    # open gate or a closed one but **a gate that could never open for anyone, in either
    # direction** (`_gate_key` is symmetric). It survived ~7 weeks.
    # ⛔ IT FAILED BY BEING QUIET, which is why prose could never have caught it: `is_map_reachable`
    # is fail-safe, so a wrong refusal is indistinguishable from a right one. MEASURED before the
    # fix — a bot standing at the Victory Road grind tile believed the world was **3 maps**
    # (`evidence/2026-09-18-waterfall-capability.stdout.txt`); after, 309.
    # ⭐ ENFORCING, and the justification is about the INPUT DOMAIN, not a judgement call: a gate
    # string that `KNOWN_GATES` uses but `_resolve_caps` cannot resolve is a defect BY
    # CONSTRUCTION — there is nothing to weigh and nothing to misjudge. It reads the live dicts,
    # never text, so it cannot fire on a mention in a comment or docstring.
    # ⛔ FAULT-TESTED IN BOTH DIRECTIONS. (1) On UNFIXED code it goes red naming `waterfall` — it
    # was written and run BEFORE the fix precisely so it could be shown to detect the real bug
    # rather than pass vacuously. (2) `POKEBOT_CAPS_FAULT_DROPKEY=surf` drops a gate that DOES
    # resolve today, and it goes red naming `surf` — proving it fires on any broken pairing, not
    # only on the one known defect.
    ("probe_caps_resolve_every_gate.py", False),
    # --- #66 — A TRAINING PICKER ASKED WITHOUT A PREDICATE (`probe_picker_allow_required.py`)
    # ‼ APPENDED AT THE END, never inserted — the same rule #34-#65 carry.
    # WHY A GATE: `training_areas.py`'s two pickers behave DIFFERENTLY at `allow=None`, on purpose.
    # `best_training_area` refuses anything with an `AREA_PREREQ`; `best_training_grass` does NO
    # filtering, because it is injected as `decide_maintenance`'s `ground_for`. ✅ MEASURED
    # 2026-09-19: narrowing that default changes 83 of 99 levels and makes every one WORSE, so the
    # asymmetry is load-bearing and must NOT be "fixed".
    # ⇒ when VICTORY_ROAD_1F was promoted (2026-09-19) the `AREA_PREREQ` row kept
    # `best_training_area(allow=None)` conservative — measured, zero levels — but
    # `best_training_grass(allow=None)` now answers VICTORY_ROAD_1F from L35 up. That is harmless
    # ONLY because no production caller uses that shape. THIS GATE KEEPS IT TRUE.
    # ⛔ THE BEHAVIOURAL ALTERNATIVE WAS SELF-REFUTING: `assert best_training_grass(40) is not
    # VICTORY_ROAD_1F` is FALSE the day the row lands. A guard that cannot be satisfied is not one.
    # ⭐ AST, NOT GREP — it inspects real Call nodes only, so it cannot fire on a mention in a
    # comment or docstring (including its own prose). Scans modules/ + plugins/ only: tools/
    # probes legitimately call the pickers bare to MEASURE them, which is how the asymmetry above
    # was established.
    # ⚠ IT HAS NO PRE-EXISTING DEFECT TO CATCH — it is a RATCHET, not a repair, so its FAULT ARM
    # (`POKEBOT_PICKER_FAULT_INJECT=1`) is the ONLY proof it works. ✅ Fault-tested 2026-09-19:
    # passes clean on 206 production files; with the arm set it fails naming the injected call.
    ("probe_picker_allow_required.py", False),
    # --- #67 — AN INVERTED RANGE CITATION (`probe_citation_ranges.py`)
    # ‼ APPENDED AT THE END, never inserted — the same rule #34-#66 carry.
    # WHY A GATE, AND IT IS A GAP IN ANOTHER GATE: `audit_doc_citations.py` pairs an identifier
    # with `file.py:LINE` and checks that LINE sits inside the identifier's span — but its
    # `FILEREF` captures a single `(\d+)`, so for `file.py:100-220` it reads the START and is
    # STRUCTURALLY BLIND to the END.
    # ⛔ MEASURED CONSEQUENCE, 2026-09-19: a 37-line insertion staled 16 citations; a bulk
    # re-point shifted every START and left every END, producing NINE inverted ranges
    # (`early_game.py:4614-4605`, `:2106-2103`, …). The full 66-gate suite went green over all
    # of them and the commit claimed the gate had "caught every one". It had not; it could not.
    # A Tier 1 reviewer found them by reading. This gate is so that reading is not required.
    # ⭐ ONLY THE UNAMBIGUOUS CHECK IS FATAL: `start > end` is a defect by construction — nothing
    # legitimate looks like it, so there is nothing to judge and nothing to misjudge. A
    # "straddle" (end leaves the definition its start is in) is ADVISORY: 67 exist in this tree
    # and many are honestly imprecise, so failing on them would make a noisy gate — which this
    # project's own rule says is strictly worse than no gate.
    # ⭐ SPANS COME FROM `ast`, NOT A REGEX. v1 treated every nested `def` as a boundary and
    # reported a CLASS as straddling its own methods — a false positive on its first run.
    # ⛔⛔ APPEND-ONLY HISTORY (06/07/08/28-) IS EXEMPT, AND THAT IS A DESIGN REQUIREMENT:
    # `08-MISTAKES.md` QUOTES a malformed range as the evidence of a past defect. A gate that
    # forced that quote to be "fixed" would make a green build an argument for falsifying the
    # record. A gate over documentation must never be able to demand that history be edited.
    # ✅ FAULT-TESTED 2026-09-19: clean over 205 in-scope documents; with
    # `POKEBOT_CITERANGE_FAULT=1` it fails naming the injected inverted citation.
    ("probe_citation_ranges.py", False),
    # --- #68 - THE FLY DISJUNCT GOING VACUOUS (`probe_fly_disjunct.py`)
    # APPENDED AT THE END, never inserted - the same rule #34-#67 carry.
    # WHY A GATE: `_training_area_allowed` admits a training area if the WALKING oracle says yes
    # OR the party can Fly to its anchor town. The Fly clause is the whole of `#24-flyladder`
    # Piece 2b, and it is INVISIBLE when it stops working: if a refactor makes `can_fly_to_anchor`
    # always False, the predicate silently falls back to walking-only, the per-trainee ladder
    # quietly loses five of its six rungs, and NOTHING FAILS. The bot just trains in the one place
    # it can still walk to - which is precisely the shape of the ~2,000,000-frame fodder grind this
    # project has already paid for once.
    # MEASURED AT REGISTRATION (2026-09-23, evidence `2026-09-23-fly-disjunct.stdout.txt`):
    # on `post_ch24_atdoor_L75.ss1` FIVE of six rungs are admitted BY FLY ALONE - the walking
    # oracle refuses ROUTE117/111/115/118/121 at the 4-hop budget and only VICTORY_ROAD_1F passes
    # it. So the clause is load-bearing by measurement, not by argument.
    # THE NEGATIVE CONTROL IS HALF THE GATE, and it is why this is not just an assertion that
    # something returned True: `post_grind_L60.ss1` has NO Fly knower, and the gate FAILS if any
    # rung is admitted there beyond what walking already allowed. A disjunct that says yes on a
    # fixture that cannot fly is saying yes for some other reason, and the green tick would be
    # measuring nothing.
    # ANTI-VACUITY IS THE PASS CONDITION ITSELF: the gate fails when ZERO rungs flip NO->YES.
    # It cannot go green by the feature being unnecessary, which is the failure mode a plain
    # "does the predicate work" check would have.
    ("probe_fly_disjunct.py", False),
    # --- #69 - A DELIBERATE REFUSAL CAUGHT BY ITS OWN TRY BLOCK (`probe_flyanchor_refusal.py`)
    # APPENDED AT THE END, never inserted - the same rule #34-#68 carry.
    # WHY A GATE, AND IT IS THE SIBLING OF #68 RATHER THAN A DUPLICATE: #68 proves the Fly
    # PREDICATE is load-bearing; this proves the TRAVERSAL's refusal actually fires. Nothing
    # exercised the traversal, and that gap shipped a live defect into the sandbox.
    # THE DEFECT, MEASURED 2026-09-23: `_fly_to_training_anchor` ends with
    # `raise UnreachableDestinationError(...)` and that raise sat INSIDE the try whose own
    # `except Exception as error:` caught it. `reraise_if_aborting` re-raises ONLY when the story
    # abort latch is set (i.e. after a whiteout), so on every ordinary run the refusal was
    # swallowed, the generator returned, and `_goto_training_area` fell through to the walk.
    # WHAT THAT COSTS: the Fly disjunct is what makes 11-to-15-hop training areas selectable at
    # all. With the refusal inert the bot ADMITS such an area, cannot fly to it, and WALKS at it
    # under `train_team`'s 500-round guard with no frame cap - KI-28's 19.9M-frame shape.
    # TWO ARMS, AND ARM B IS NOT DECORATION: a "fix" that re-raises unconditionally passes arm A
    # and breaks every heal-return, because a Poke Center is `map_type=Indoor` so Fly is ALWAYS
    # illegal there while the grind tile is two hops away. Arm A alone would grade that a success.
    # FAULT-TESTED 2026-09-23 (`POKEBOT_FLYREFUSAL_FAULT=1` re-creates the swallow): happy path
    # exit 0 with both arms green; with the arm set, exit 1 failing arm A ONLY - a discriminating
    # result, not a blanket failure.
    # NO EMULATOR: the oracles are stubbed, so it is pure control flow and runs in under a second.
    ("probe_flyanchor_refusal.py", False),
    # --- #70 - THE PP HEAL TRIGGER THAT CANNOT FIRE FOR ONE TRAINEE (`probe_lead_pp_scope.py`)
    # APPENDED AT THE END, never inserted - the same rule #34-#69 carry.
    # WHY A GATE: `train_team`'s PP heal term is `_team_is_out_of_pp()`, which is ALL-QUANTIFIED -
    # False as soon as ANY party member has a damaging move with PP. With five L75s benched it is
    # PERMANENTLY False while one trainee grinds, so the PP heal can never fire for the one mon
    # actually swinging. `#24-ppscope` adds a narrow, trainee-scoped term beside it.
    # THE FAILURE IT GUARDS IS SILENT, WHICH IS WHY A WATCHDOG CANNOT REPLACE IT: a dry lead under
    # SwapTrainBattleStrategy SWAPS rather than FLEES, so the bot keeps winning and keeps levelling
    # while the exp splits 50/50 - decaying the ladder's measured 21.0 h toward 41.1 h. Every
    # no-progress check in the tree sees healthy progress.
    # FOUR ARMS, and arm C is the one a naive fix fails: status-only moves (Castform's real
    # Sunny Day / Hail shape) have base_power 0, so "has a move with PP" would call a lead healthy
    # while it cannot damage anything. Arms D1-D3 keep an egg / absent / empty lead from reading
    # DRY, which would send the bot on a heal trip that fixes nothing forever.
    # NO EMULATOR: the predicate is PURE (the party is an argument), so this runs in milliseconds.
    # A predicate that needs a ROM to test is a predicate that gets tested once.
    # FAULT-TESTED 2026-09-23 (`POKEBOT_PPSCOPE_FAULT=1`): happy path exit 0, all arms green; with
    # the arm set, exit 1 with BOTH True-expecting arms (A, C) red and every False-expecting arm
    # still green - which is what a blanket-False stub must do.
    ("probe_lead_pp_scope.py", False),
    # --- #71 - THE Ch24 RUN-LATCH (`probe_ch24_owns_run.py`)
    # APPENDED AT THE END, never inserted - the same rule #34-#70 carry.
    # WHY A GATE: `ch23_chapter_done()` is FLAG AND POSITION AND BAG (victory_road.py:3315-3322).
    # Ch24 breaks the POSITION conjunct BY DESIGN - its training leg flies to ROUTE117 within
    # seconds and later grinds INSIDE Victory Road, which trips the other half of the same line.
    # Without a latch every later run finds Ch23 "unfinished", re-runs do_victory_road_chapter(),
    # and `_guard` STOPS the bot with a diagnostic. victory_road.py:3308-3313 predicted exactly
    # this and called it a forward dependency of Ch24.
    # ARM B IS THE ONE WITH A BODY COUNT: the latch must clear in reset_per_run_state() and NOT in
    # __init__. StoryEndlessResetMode.run() loops on the SAME object, so __init__ runs once per
    # BATCH - a latch set there makes run 2 skip Ch23 entirely. That is the `_rival_attempts`
    # shape (story_mode.py:1849-1872) which killed 16 of 20 P1 runs, 6 of 9 P2, 5 of 8 P3.
    # ARM D READS THE SHIPPING SOURCE, which is what keeps the other arms honest: A-C exercise a
    # MODEL of the latch (the real `_ch23_settled` is a closure inside `_play`, unreachable from
    # outside), so D checks the model has not drifted into a comforting fiction - including that
    # the `_guard` half is gated too, since `_guard` is assert-not-skip and a bare predicate there
    # would merely move the failure one line down.
    # FAULT-TESTED 2026-09-23 (`POKEBOT_CH24OWNS_FAULT=init` = a latch that never clears): happy
    # path exit 0; with the arm set, exit 1 with every arm depending on "the latch can be unset"
    # red (B and C) and every SOURCE-reading arm green.
    ("probe_ch24_owns_run.py", False),
    # --- #72 - A PREDICTION IS ONLY PRE-REGISTERED IF THE READING THAT GRADES IT EXISTS
    # (`probe_predictions_gradeable.py`)
    # ⛔⛔ MEASURED 2026-09-24. `2026-09-24-ch24-multirung-PREDICTIONS.md` was committed BEFORE its
    # drive exactly as the story-drive skill requires, and TWO of its seven predictions came back
    # UNGRADEABLE: P3 (the one that closes `#24-ppscope`) and P4 both state their falsifiers in terms
    # of an exp split that `ch24train` NEVER RECORDED. The 2.2 % baseline P4 quotes came from a
    # DIFFERENT driver (`Ch24SwapTriggerMode`), and the instrument was assumed to travel with the
    # number. ⇒ the file was internally coherent, correctly pre-registered, and partly unfalsifiable
    # by the run it was written for — which is the exact failure pre-registration exists to prevent,
    # and it invited "5 of 7 confirmed" over seven predictions of which two were never tested.
    # ⭐ ENFORCING, and the justification is about the INPUT DOMAIN rather than a judgement call: the
    # gate asks only whether a named key is WRITTEN somewhere in `story_harness.py`. That is a
    # mechanical fact with no interpretation in it.
    # ‼ SCOPED BY DATE (`CONVENTION_START = 2026-09-24`): 29 older prediction files are exempt, so
    # the gate never reddens history — a gate with false positives teaches the reader to bypass it.
    # New files are covered automatically and cannot opt out, which a marker-based opt-in could not
    # promise (the agent who forgets the reading is the agent who forgets the marker).
    # ⛔ IT CHECKS EXISTENCE, NOT CORRECTNESS — that `exp_leak_pct` exists does not prove it measures
    # what P4 means by "leak". It closes the measured hole: a falsifier over a quantity NOTHING records.
    # FAULT-TESTED 2026-09-24, all four arms: `--fault missing-key` (a key no driver writes),
    # `--fault no-graded-by` (a prediction naming no reading) and `--fault no-driver` (no DRIVER line)
    # each exit 1; `--fault mention` — the FALSE-POSITIVE arm, proving a comment-only key neither
    # satisfies the gate nor trips it — exits 0.
    ("probe_predictions_gradeable.py", False),
    # --- #73 - EVERY ITEM NAME IN A POLICY TABLE RESOLVES (`probe_item_names_resolve.py`)
    # ⛔⛔ FOUND 2026-09-24 by a recon agent and VERIFIED against our own `modules/data/items.json`:
    # `overworld_items.py` named **"Paralyze Heal"** in TWO places (`STATUS_ONLY` and the
    # `healing_items` fallback allowlist). There is no such item — Gen-3 spells it "Parlyz Heal".
    # ⇒ `held.get("Paralyze Heal", 0)` could only ever return 0, so the entry was DEAD, and the
    # allowlist's own rule is "an item not named here is not used" — so the misspelling did not fail
    # loudly, it SILENTLY REMOVED a real item from the bot's options.
    # ⭐ AND THE GATE IMMEDIATELY FOUND A SECOND ONE NOBODY KNEW ABOUT: "Energy Powder" (the real
    # item is "Energypowder", one word). That is the whole argument for gating the CLASS rather
    # than fixing the instance.
    # ‼ WHY THIS SHAPE IS DANGEROUS RATHER THAN COSMETIC: a name that resolves to nothing produces a
    # MISSING ACTION, NEVER AN ERROR. `pokemon_league.py`'s own header already records two earlier
    # instances of the same class ("Repel selected because `parameter > 0`"; "an allowlist silently
    # empty because `field_use` is an enum"). The gauntlet is the one place where a missing heal
    # cannot be retried: five fights, no nurse past the lobby door, no way back.
    # ⛔ NO EXISTING GATE COVERED IT. `repro_item_noop_detector.py` gates the no-op detector's STATE
    # MACHINE; `repro_battle_items.py` runs pure-function/static checks over the battle policy.
    # Neither asks the flat question "is this string an item?".
    # ⭐ ENFORCING, and the justification is about the INPUT DOMAIN: it asks only whether a literal
    # appears in `items.json`. That is mechanical, with no interpretation in it.
    # ‼ SCOPED TO POLICY TABLES, not to every string literal — scanning everything would flag prose,
    # log text and map names, and a gate with false positives teaches the reader to bypass it.
    # The trade is deliberate and stated in the docstring: it cannot see a name built at runtime.
    # FAULT-TESTED 2026-09-24 on a GREEN baseline (the arms are meaningless against a red one, which
    # is how they were first run): `--fault phantom` (inject a non-item) exits 1; `--fault prose`
    # (Title-Case text OUTSIDE a policy table) exits 0, proving no false positive.
    ("probe_item_names_resolve.py", False),
    # --- #74 - A WINNING RUN MUST NOT READ "CH23 NOT DONE" (`probe_ch23_done_winstate.py`)
    # ⛔⛔ THE ONE WHERE **SUCCESS IS THE FAILURE CASE**. `ch23_chapter_done()`'s only position
    # conjunct was `_on_map(EVER_GRANDE)`, but the Hall of Fame returns the player to
    # LITTLEROOT_TOWN_BRENDANS_HOUSE_2F (MEASURED by `--driver ch24tailprobe`). So after a WIN the
    # predicate read False => §Ch23 re-ran, legs 1-3 self-skipped, LEG 4 FIRED, and the bot
    # attempted AN OCEAN CROSSING FROM A BEDROOM — turning a completed game into a hard §Ch23
    # failure. Fixed by two disjuncts: `IS_CHAMPION` (monotone: one setter in the decomp, cleared
    # nowhere) and a `CH24_SEALED_MAPS` position term.
    # ⭐ ENFORCING, and the justification is about the INPUT DOMAIN: every check is a mechanical
    # property of the source — a tuple's membership, a name's presence in the flag table, the order
    # of two statements, and whether a called name resolves. No interpretation.
    # ‼ IT EXCLUDES THE LOBBY ON PURPOSE. `inside_league()` would have matched LEAGUE_1F/2F, where
    # §Ch23's OWN heal (leg 10) and shop (leg 11) legs stand — §Ch23 would then declare itself done
    # in the middle of its own work. The `lobby` arm proves that exclusion is enforced.
    # ⛔⛔ AND THE `noimport` ARM EXISTS BECAUSE THIS GATE ONCE PASSED OVER A BROKEN PREDICATE. The
    # first version of the fix called `get_event_flag(...)` in a module that does not import it; the
    # NameError was SWALLOWED by the function's own broad `except`, the disjunct silently never
    # fired, and the gate said PASS because the text was present and correctly ordered.
    # => TEXT ORDER IS NOT BEHAVIOUR. The gate now also checks that every name the function CALLS
    # actually resolves, and `--fault noimport` reproduces the shipped-broken state.
    # FAULT-TESTED 2026-09-24, all four arms exit 1: lobby, badflag, order, noimport.
    ("probe_ch23_done_winstate.py", False),

    # --- #75 - A GENUINE COMPLETION MUST NOT BE FILED AS A FAILURE
    #           (`repro_content_end_classifier.py`)
    # ⛔⛔ THE ONE WHERE **A WIN READS AS A DEFECT.** `story_mode.py` emits, on the ONLY path
    # that means the bot finished everything built, "... basket bought. **End** of built
    # content. NEXT (WIP): Ch24 ..." — with a CAPITAL E. All three log classifiers
    # (`compare_runs.py`, `endless_runs.py`, `story_harness.py`) looked for the LOWERCASE
    # needle with a CASE-SENSITIVE `in`, so the match was False and the first ever completed
    # run would have been filed as `HANG CONFIRMED` in every batch report.
    # ‼ AND THE OBVIOUS FIX WAS WORSE THAN THE BUG: lowercasing only the HAYSTACK repairs
    # this one needle and breaks TEN others in the same files (HANG CONFIRMED, FEATHER BADGE,
    # BADGE01_GET, Traceback ...). Both sides are casefolded, or neither.
    # ⭐ ENFORCING, and cheap: it is pure string logic with no emulator. It reads the literal
    # FROM `story_mode.py` rather than carrying a copy — a gate holding its own copy of the
    # thing under test passes forever after someone edits the real one, which is EXACTLY how
    # this defect survived (three classifiers and a docstring all carried a lowercase copy of
    # a capitalised fact).
    # THREE ARMS: C1 the real literal (RED->GREEN demonstrated), C2 every other needle still
    # matches, C3 a clean log matches nothing. `--self-test` fault-tests the gate itself.
    ("repro_content_end_classifier.py", False),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true", help="skip gates that boot a ROM")
    ap.add_argument("--list", action="store_true", help="print the suite and exit")
    args = ap.parse_args()

    if args.list:
        for name, slow in GATES:
            print(f"{'SLOW' if slow else 'fast'}  {name}")
        return 0

    selected = [(n, s) for n, s in GATES if not (args.quick and s)]
    total_in_suite = len(GATES)
    skipped = total_in_suite - len(selected)

    # ‼ CONTROL: a gate that does not EXIST must fail loudly, not be silently skipped. A suite that
    # quietly runs 14 of 16 and reports ALL PASS is exactly the "blind gate" shape this project has
    # been bitten by twice (audit_flag_names checking 2 files; the flag audit that exited 0 on a
    # phantom name).
    missing = [n for n, _ in selected if not (HERE / n).is_file()]
    if missing:
        print("‼ MISSING GATE SCRIPT(S) — refusing to report a pass over a suite that is not all here:")
        for n in missing:
            print(f"    {n}")
        return 1

    print("=" * 92)
    print(f"STANDING GATE SUITE — {len(selected)} gate(s)"
          f"{' (quick: ROM gates skipped)' if args.quick else ''}")
    print("=" * 92)

    results: list[tuple[str, int, float]] = []
    logs = HERE / ".gate-logs"
    logs.mkdir(exist_ok=True)

    for name, _slow in selected:
        started = time.monotonic()
        out = logs / f"{Path(name).stem}.txt"
        with out.open("w", encoding="utf-8", errors="replace") as handle:
            # ‼ BOUNDED — added 2026-08-22, deep sanity check PASS 4 (INFRASTRUCTURE).
            # This call had NO `timeout=` and the word appeared nowhere in the file, so a gate that
            # HUNG was not a failure: it blocked the entire suite forever, with no output and no
            # exit code. Eight of these gates boot a ROM/emulator — precisely the hang-prone shape —
            # and this project's prime directive #3 is "never hang, every loop needs a bound". The
            # runner that enforces every other rule was the one place without one.
            # Slowest real gate measured 114.6s, so the fast/slow bounds carry ~8x margin.
            try:
                rc = subprocess.run(
                    [sys.executable, name],
                    cwd=HERE, stdout=handle, stderr=subprocess.STDOUT,
                    timeout=TIMEOUT_SLOW if _slow else TIMEOUT_FAST,
                    env=_GATE_ENV,
                ).returncode
            except subprocess.TimeoutExpired:
                rc = 124   # the conventional timeout code; must land in `failed`, never in PASS
                handle.write(
                    f"\n\n‼ TIMEOUT — killed after "
                    f"{TIMEOUT_SLOW if _slow else TIMEOUT_FAST}s by run_gates.py.\n"
                    "  A hung gate is a FAILED gate. If this is legitimate work, raise the bound\n"
                    "  deliberately rather than removing it.\n"
                )
        elapsed = time.monotonic() - started
        results.append((name, rc, elapsed))
        if name in ADVISORY:
            label = "ADVIS"
        else:
            label = "PASS" if rc == 0 else "FAIL"
        print(f"  {label:<5} {name:<34} exit={rc}  {elapsed:6.1f}s")

    # ‼ An ADVISORY probe's exit code does not gate — see the ADVISORY note above.
    failed = [(n, rc) for n, rc, _ in results if rc != 0 and n not in ADVISORY]
    advisory_ran = [n for n, _, _ in results if n in ADVISORY]
    print("=" * 92)
    if not failed:
        total = sum(e for _, _, e in results)
        enforcing = len(results) - len(advisory_ran)
        line = f"ALL {enforcing} ENFORCING GATES PASS  ({total:.1f}s total)"
        if advisory_ran:
            line += f"   [+{len(advisory_ran)} ADVISORY probe(s) — run, NOT gated]"
        print(line)
        # ‼ THE HEADLINE CARRIES THE CAVEAT — added 2026-08-22, deep sanity check PASS 4.
        # `--quick` skips every ROM gate and the CLOSING line — the one people paste into a doc or
        # a commit message — used to read a flat "ALL n GATES PASS" with the caveat only in the
        # header, far above. This project's own P2 rule is that a title claiming more than the
        # evidence makes the document wrong no matter how careful the body is.
        if args.quick:
            print(f"‼ --quick RAN {len(results)} OF {total_in_suite} — {skipped} ROM GATE(S) WERE "
                  f"NOT RUN. THIS IS NOT A GREEN SUITE.")
            print("  Run without --quick before any commit; a red ROM gate is invisible here.")
        print("=" * 92)
        return 0

    print(f"FAILED: {len(failed)} of {len(results)}")
    for name, rc in failed:
        print(f"\n--- {name} (exit {rc}) — last 25 lines ---")
        tail = (logs / f"{Path(name).stem}.txt").read_text(encoding="utf-8", errors="replace")
        for line in tail.splitlines()[-25:]:
            print(f"    {line}")
    print("=" * 92)
    return 1


if __name__ == "__main__":
    sys.exit(main())
