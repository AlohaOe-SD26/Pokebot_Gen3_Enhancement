# Acceptance evidence — 2026-09-07

Raw logs are `*.log` in this directory and are **gitignored**; these are the lines they turn on.
Reproduce: see the commands in each section.

## KI-96 — the round-3 root cause, MEASURED FALSE
```
$ POKEBOT_KI96_CENSUS=1 py -3.12 story_harness.py saves/post_grind_L60.ss1 --driver ch23chapter --frames 400000
f5864245 [BATTLE] [KI96-REREAD] party_slot=2 pre(raw=201345 decoded=[2, 0, 1, 3, 4, 5] aims_at_menu_slot=0 active_was=0) post(raw=201345 decoded=[2, 0, 1, 3, 4, 5] aims_at_menu_slot=0 active_now=0) VERDICT=AGREE
```
pre == post, byte-identical, on a run that DID reproduce the wedge => the array is NOT a stale
leftover refilled at menu-open. The one-line 'fix' would have changed nothing.

## KI-96 — the BOUND, driven-proven
```
KI-96: the in-battle party menu would not accept party slot 2 (menu slot 0) after 241 A-presses. Backed out with B and refused rather than spinning until the KI-47 net 
```
The unbounded `while PARTY_MENU: press A` is now a bounded, named, diagnosable stop.
NOTE the run then went Story -> Manual. That is CORRECT: no harness driver declares
`handles_battle_faults`, so `request_mode_recovery` returns False by contract (#24-harness-faultgap).

## KI-97 — driven GREEN
```
$ py -3.12 story_harness.py saves/post_sootopolis_arrival.ss1 --driver storyresume --frames 25000
C1 'Could not reach (19, 6) on MapRSE.MAUVILLE_CITY' : 0  (want 0)
C2 'Fortree arc already complete (BADGE06)'          : 1  (want >=1, POSITIVE CONTROL)
```

## gate #42 — validated in BOTH directions
```
$ py -3.12 grade_ki97_drive.py acceptance-2026-09-07/ki97-accept.log   -> exit 0, PASS
$ py -3.12 grade_ki97_drive.py x4-runs/20260907-073620                 -> exit 1, 0 PASS / 5 FAIL / 3 INDETERMINATE
```
A grader proven only on the failing side can still be a grader that always fails.

## #24-mossdeepstrand — SAFE half driven, RESCUE half NOT
```
Story: Mossdeep Gym already done — skipping.
```
Segment 18's else ran and `leave_the_gym()` no-oped off the gym map with no error.
The RESCUE half needs a save at MOSSDEEP_CITY_GYM (23,8) with BADGE07 SET — see #24-mossdeep-strandfixture.

---

## `KI-96` — ✅ SOLVED AND DRIVEN (2026-09-07 19:40–19:52)

Same fixture (`saves/post_grind_L60.ss1`), same driver (`--driver ch23chapter`), same build
(`sandbox`), 26 minutes apart. Each arm made **exactly one** `RotateLead` attempt, so the two are
directly comparable on a single event.

```
                       WEDGED  Story-debug-20260907-194020   FIXED  Story-debug-20260907-194608
RotateLead attempts          1                                     1
[KI96-FIX] fired             0                                     1
the 240-press bound       ONCE, at 241 presses                  NEVER
outcome                   Bot STOPPED -> Manual,                switch ACCEPTED after 27 presses
                          VICTORY ROAD (34,12)
battles fought               6                                    12
frames run              46,333                                82,292
ledger entry            19:46:32                              19:52:42
```

**The measurement that identified the root cause** (from the FIXED run, and from the corrected probe
in the WEDGED run):
```
[KI96-INDEX] requested party index=2 -> mapped menu in_battle_index=0
[KI96-FIX]   menu open after 50 frame(s): re-mapped party slot 2 from menu slot 0
             (pre-menu, STALE) to 2 (in-menu). Aiming at 2.
[KI96-REREAD] pre (raw=201345 decoded=[2,0,1,3,4,5] aims_at_menu_slot=0)
              post(raw=012345 decoded=[0,1,2,3,4,5] aims_at_menu_slot=2)   VERDICT=DIFFER
[KI96-WHY]   action=0  cursor_slotId=0  order_in_menu='012345'
             msg='DIVER is already in battle!'
[KI96-DONE]  the party menu closed after 27 press(es) — the switch was ACCEPTED
```
`action=0` is an ORDINARY menu (not `CANT_SWITCH`=2, not `ABILITY_PREVENTS`=4) ⇒ the mon was never
trapped and the refusal was PER-SLOT. `gBattlePartyCurrentOrder` is refilled by
`PlayerHandleChoosePokemon` at menu-open; `in_battle_index` was computed ~140 lines earlier from the
previous turn's leftovers.

⚠ **HOW TO READ THE LOG COUNTS.** `grep -c 'would not accept party slot'` returns **9** on the wedged
run and that is **ONE firing**, not nine: the stop message is echoed by the mode switch, two STEP
lines, the "Bot stopped" line and five subsequent `[hb]` heartbeats. Count the EVENT, not the lines
mentioning it.

‼ **AND READ THE FILE AFTER THE RUN ENDS.** These markers were first read at 19:47 while the FIXED
run was still writing; it did not finish until 19:52:14. The verdict was unchanged, but a mid-run
read is not a result — the stronger fact (the bound never fired across the FULL 82,292 frames, 1.8x
the wedged run) is only visible on the completed file.

---

## §Ch23 REGRESSION CHECK on the fully-fixed sandbox (2026-09-07 20:28)

`story_harness.py post_grind_L60.ss1 --driver ch23chapter --build sandbox --frames 600000`

```
ACCEPTANCE: PASS    done=True   battles=12   whiteouts=0   failure=None
neighbours_reachable=4
leg5_entry    ((24,43), (15,39))
ladder_apron  {'tile': (21,21), 'step': 'Left'}
b2f_arrival   ((24,45), (30,25))
heal_before   602/1000, fainted [Wailord], hurt [Mightyena, Swellow]
```

**⚠ WHAT THIS PROVES, AND WHAT IT DOES NOT.** The run never took the `RotateLead` path
(`KI96-FIX` 0, `KI96-DONE` 0, bound firings 0) and never whited out (`WHITEOUT recovery` 0). ⇒ **it
is NOT an acceptance of either the `KI-96` re-map or the location-keyed whiteout budget.** Neither
code path executed.

**⭐ IT IS A REGRESSION CHECK ON THE ORDINARY CASE, AND THAT IS EXACTLY THE RIGHT INSTRUMENT HERE.**
Both changes sit on paths that EVERY battle and EVERY whiteout traverses, and session-discipline
rule 9 says: *"when a change touches a shared path, the cheap decisive test is an A/B on the ORDINARY
case, not more samples of the exotic one."* §Ch23 passed before these changes and still passes after,
with the same shape of result. That is the claim, and it is the whole claim.

The exotic cases are covered separately and deliberately: `KI-96` by its own driven A/B above, and
the whiteout budget by gate #44 replaying the 14 real killed sequences (a drive would need 41
whiteouts — hours of emulation — for a decision that is pure).

‼ **AND THIS RUN'S FIRST ATTEMPT SILENTLY DID NOT HAPPEN.** It was launched without the harness's
POSITIONAL `state` argument, died in under a second on a usage error, and the task runner reported
**"completed (exit code 0)"** because the invocation ended `; echo "EXIT=$?"`. Nine lines of usage
text sat in this log while the drive was believed to be running. See `08-MISTAKES.md` 2026-09-07 —
never put a command after the one whose status you care about, and confirm a long run STARTED by
reading its log rather than trusting the launch.
