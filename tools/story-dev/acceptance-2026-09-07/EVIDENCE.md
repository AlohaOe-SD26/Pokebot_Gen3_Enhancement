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
