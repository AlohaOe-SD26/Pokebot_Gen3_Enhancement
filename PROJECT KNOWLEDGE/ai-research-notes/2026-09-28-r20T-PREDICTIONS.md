# 2026-09-28 — USER RULING 20 Phase 2, STEP T (per-catch telemetry, LOG-ONLY): PRE-REGISTERED PREDICTIONS

> Filed BEFORE any T code is applied. Branch `wt/r20telemetry`, cut from `main` `4ea923a5`. Spec:
> `2026-09-27-ruling20-phase2-BUILDSPEC.md` §4 T and §7, corrected by a 4-agent re-verification (C1-C8: `--set-balls`
> is broken, so no arm uses it; `--frames 90000`, not 60000, or the run is VACUOUS; `res=` not `outcome=`; M4 is
> unreachable in the harness; M5 is a NEW `env-all:` line beside the existing `env:` line; M1's shiny site is `:3751`).

## THE DRIVE

`PYTHONUTF8=1 py -3.12 story_harness.py post_mtpyre.ss1 --driver storyresume --frames 90000 --profile <p>`,
`post_mtpyre.ss1` (`80602159694b`, PINNED; party 6 with 3 fainted, box 0, spare 17, badges 6, ₽14,804).

**CONTROL (already run, on `4ea923a5` with NO telemetry): `tools/story-dev/evidence/2026-09-28-r20T-CONTROL.txt`.**
- 12 battles in the window, whose `[BATTLE] started/ended` lines are the P4 reference.
- Shuppet at f3144418: `[DEXFENCE] … not at full strength`.
- The heals are at Lilycove and Mauville.
- Oddish #43: its catch starts at f3209102 and is `Caught` at f3211292 (`[BALLS] 17 -> 16`).
- Linoone #264: its catch starts at f3216729 and is `Caught` at f3224789 (`[BALLS] 16 -> 10`).
- `[DEX]` owned went 10 → 11 → 12.
- It REPRODUCES the spec's 2026-09-28 reference frame for frame, so today's KI-47 change did not move this trajectory.

## PREDICTIONS — T arm (the same command, T applied)

- **P1.** Exactly 2 `[CATCH] start` and 2 `[CATCH] end` lines in the window, each start followed by its end:
  - `start kind=dex sp=Oddish#43 lv=<n> attempt=1 badges=6 party=6/6 box=0 spare=17 … map=<g>,<n>` at f3209102, then
    `end kind=dex sp=Oddish#43 end=caught res=Caught thrown=1 … dest=box pid=<8 hex> party=6/6 box=1 spare=16
    badges=6 bail=-`;
  - `start kind=dex sp=Linoone#264 … attempt=1 … box=1 spare=16` at f3216729, then `end … end=caught res=Caught
    thrown=6 … dest=box pid=<8 hex> … box=2 spare=10 … bail=-`.
  - Each `pid` is 8 hex digits, and the two differ.
- **P2.** At least one `[DEXFENCE] … not at full strength` line before the first `[CATCH] start`.
- **P3.** Every `[hb]` line carries `box=` and `badges=6`. `box=` reads 0 before f3211292, then 1, and 2 after
  f3224789.
- **P4 (THE LOG-ONLY TEST).** Every `[BATTLE] started` / `ended` line (frame + outcome) is IDENTICAL to the control's.
  The path is deterministic, so this is one trajectory replayed, and ANY difference means T changed behaviour.
- **P5.** The run header has an `env-all:` line reading `(no POKEBOT_* env vars set)` (none are set in this arm), and
  the old `env:` line is still present.
- `[CATCHTEAM]` / `[BALLS-BUY]` / `[BADGE]` lines: none are expected in this window. There is no pre-gym-1 team loop,
  no mart restock, and `badge_log.on_frame` never runs in the harness. Their correctness is covered by the gates, not
  by this drive.

## FAULT ARM — `POKEBOT_R20_FAULT_NOCATCHEND=1`, same command

- 2 `start`, 0 `end`.
- `grade_r20_telemetry.py` exits 1 and reports "start without end" twice.
- P4 still holds (the arm suppresses a log line, never behaviour).
- The header's `env-all:` names `POKEBOT_R20_FAULT_NOCATCHEND`.

## FALSIFIERS

- Any P4 difference: T is not log-only. STOP; do not merge.
- `dest=?` on a catch: the box is not yet readable when `on_battle_ended` runs (UNVERIFIED today). Fix the read, not
  the grader.
- A `thrown` that disagrees with the `[BALLS]` deltas (1 and 6).
- 0 `[CATCH] start` lines: the arm is VACUOUS, not a pass.

## WHAT THIS DOES NOT SHOW

- The `team`, `hm`, `counter` and `shiny` start sites, `bail` / `out_of_balls` marks, M4, M6 and O3. The gate
  `probe_r20_telemetry.py` covers their never-raise and classification properties. Real-run coverage comes from the
  next batch.
- Any frequency.
