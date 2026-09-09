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
