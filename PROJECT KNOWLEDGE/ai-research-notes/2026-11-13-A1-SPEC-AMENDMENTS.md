# A1 spec: amendments v4 (the final copy), after the adversarial review and its three re-checks (2026-11-13)

> **A NOTE for the lead. NOT APPLIED.** v4 was revised read-only by the AMV4 reviser on 2026-11-13, from about 10:04 PM
> PST, from v3 (`AMENDMENTS-v3.md`, 144,729 bytes, md5 `a77a0fe5...`, kept unchanged). v4 answers v3's delta re-check
> (`result.a1.check` in `wf_result_wug76nq4r.json`: READY_WITH_FIXES; 2 MINOR, 6 NIT, no MAJOR) with the lead's calls
> D1-D8 on it (section 1.0b). Two calls are applied in an adapted form, with the reason: D7's "a few frames" and D8's
> cause of the disk's fall. Two add a little beyond the call, also with the reason: D3 (the new block 15-g and the
> copies of the lab files the NEW blocks rely on) and D4 (07-j's profile-folder kill) (1.0b). Earlier rounds: v2
> (`AMENDMENTS-v2.md`) answered the review (`result.review` in `wf_result_w3j046n6y.json`: READY_WITH_FIXES; 14
> findings: 2 MAJOR, 11 MINOR, 1 NIT; 14 missing items; 6 user-question judgments); v3 answered v2's re-check
> (`result.a1.check` in `wf_result_wtuk5qef9.json`: READY_WITH_FIXES; 9 MINOR, 5 NIT) with the lead's calls 1-9
> (section 1.0).
>
> **v4 is the final copy, and it becomes the repo note**
> `PROJECT KNOWLEDGE/ai-research-notes/2026-11-13-A1-SPEC-AMENDMENTS.md` (the merge's docs addendum,
> `mergeplan/DOCS-ADDENDUM.md` section 3, names `AMENDMENTS-v4.md` as the note's source). Its NEW blocks enter the
> spec. v1 (`AMENDMENTS.md`), v2 and v3 are earlier drafts kept in the lab; none of them is the note.
>
> **Lab paths (the lead's ruling, D3):** every folder under `C:/Remote Projects/_ai_lab/s53/` is lab that the merge's
> cleanup may delete (the cleanup list goes to the user). Only `C:/Remote Projects/_ai_lab/keep/` is kept (this PC
> only, not git). This note's own tables and prose name lab paths as they are. The NEW blocks cite a git source
> (ledger entries and their evidence files, commits, `07`'s merge entry, the repo notes
> `2026-11-13-CH5-SEARCH-LOOP-FIX.md` and this one), or a kept copy in
> `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/` (its README.txt names each file with its sha256), or mark a
> lab path "(lab, deleted after the merge)". `C:/Remote Projects/_livechain/` (the G starts, #101's graded record) is
> outside `_ai_lab/s53/`.
>
> **Writes:** this file; `STATE.md` (lines tagged AMV2, AMV3, then AMV4); read-only scripts in `a1prep/tools_v2/`,
> `a1prep/tools_v3/` and `a1prep/tools_v4/`; and (v4, D3) 17 copied files plus an appended README section in
> `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/`. Nothing in R, WT, the learner clone or another lab folder
> changed. No emulator, no seed, no detached job, no git write.
>
> **Read:** the spec `PROJECT KNOWLEDGE/ai-research-notes/2026-11-11-A1-FRONTIER-PROBE-SPEC.md` (R's copy: 60,366
> bytes, md5 `0d5e04fc...`, CRLF line ends; WT's copy is the same file, `git diff --quiet 934ddb7f` exit 0). WT
> (`.claude/worktrees/ch67-merge`) is now at `fa9f073d` (`<S3t2>`, the lead's second timing-rows commit), on
> `19e9700c` (E0-2's evidence file and ledger entry #148), on the test-only fix-up `3caf9c47`, on the fix `9d2f3fc5`,
> on `a90c8e8f` (E0's record, ledger #147). Code lines below are read at `3caf9c47` unless named otherwise. The lab:
> `bp1r4/out/`, `fix5/` (runs, `STATE.md` through line 106 after the lead's fix, `verify1/`), `mergeplan/` (`STATE.md` through line 262,
> `DOCS-ADDENDUM.md`, `e0/runs/E0-6481`, `e0/runs/E0-6484`, `out/merge/E0-2_6_judge.txt`), `e0diag/` (`DIAGNOSIS.md`,
> `REFUTE.md`, `shadow/SHADOW.md`), `_livechain/graded-ch5`, `notes/2026-11-13-CH5-SEARCH-LOOP-FIX.md`, the keep
> folder's `README.txt`. R's `06`. v4 also read, in git at WT `fa9f073d`: BP-1 round 2's and round 4's evidence files.

## 0. Short version (the headline carries the caveat)

- **These are amendments to a spec, not a build.** Every measured number is development data: one trajectory per run,
  never a rate. Cost and time are estimates. The full lane's two longest rows are PROVISIONAL upper bounds.
- **E0-2 read GO:** "E0 VERDICT: REACHED 3 of 3; legs ran 15, purity-clean 15; wall 31 min (cap 120); problems 0 ->
  GO" (the message of commit `19e9700c`; ledger #148; `mergeplan/STATE.md` lines 248 and 256). It is a hard-break
  check, one trajectory per seed, on `3caf9c47`'s play code. Part 0 changes play code, so it does not cover A1's.
- **MAJOR 1 accepted. L6 rises to 1,000,000 frames with a 7,200 s wall (AM-16, now MUST).** The boss-prep raise runs
  INSIDE L6: 0 raise goals after `ch6_dewford` in 8 of 8 measured runs. L6 used 82.5-86.7 % of 600,000 frames in 5 of 8
  runs from C1. A Catcher's raise budget is 550,000 frames, so a Catcher L6 would not fit 600,000.
- **MAJOR 2 accepted as the lead ruled. A1's legs carry the goal memory (part 0, GM, AM-01).** Errand fields are
  restored. `last_save` and `saved_for` reset at a `--state` start. The loss count is carried. I found no concrete harm
  that outweighs "one game, one loss count"; its measured consequence is recorded. MC stays E0's harness exactly, with
  no goal memory and live_chain's 1.5 GB world cut (v3).
- **Part 0 moves the play digest (v3).** It is play code, so E0-2's GO does not cover A1's code. MC's FIRST run, on
  the A1 commit's stage, MUST read PASS before WP1. On later merges MC stays a SHOULD (AM-05).
- **No departure (v3).** The LOOP key applies only when the loop runs into the leg's end, read as: its last crossing
  at most 120,000 frames (`STORY_PATIENCE`) before the end. That keys both E0 loop legs as one LOOP key (last
  crossings 92,013 and 20 frames before their ends). v2's window-share clause is dropped: no measured leg needed it
  (AM-03).
- **New amendments:** K1's leads in the record (AM-20); the chapter 1-5 miss rate out of A1 v1's scope and filed as its
  own item (AM-21); the `06` entries A1's docs pass writes, citing the merge's correction of USER RULING 55 (2)'s
  reason, or writing one only if it is absent (AM-22, v4); the leg record's new fields in one edit (AM-23); the new
  tests and mutants in one edit (AM-24); the spec's title, header and Review log record the amendment (AM-25). 25
  amendments, 87 edit blocks in all (v3 added 07-h and 25-c; v4 adds 07-i, 07-j and 15-g).
- **v3's fixes** (section 1.0): GOALS-OFF's stale measure defined; definition-of-done item 0 split; T31's boundary
  rows; MC's world cut; "about 4.4 h"; P2's carried-loss path; the play digest; WP1b's per-job SKIP; three line ranges;
  part 0's two contradictions; lab paths out of the NEW blocks.
- **v4's fixes** (section 1.0b): T31's share row made possible (0.75, not 0.95) and `window_share` defined; the lab
  paths in NEW blocks moved to git sources or the kept copies; MC's 1.5 GB cut in 2.7's per-leg line and 3.5's
  CUT-WORLD row (new blocks 07-i, 07-j); AM-22 (vi) cites the merge's `06` correction; AM-18's PASS time; 2.4's STRICT
  rule; the disk's newest readings.
- **Cost about 57-98 Mtok (central 76). Machine time about 11-13.5 h, about 22.5 h worst:** mostly WP1 (4-5 h at P =
  8) and one full regression lane (about 4.4 h, budgeted from upper-bound rows; the merge's own full lane gives the
  measured hours). Agent time about 13-20 h. Calendar about 3-4 days after the merge. **The disk kept falling (v4):**
  47.95 GB free at 10:00 PM and 46.21 GB at 10:50 PM (53.2 GB at 8:10 PM; unevenly; cause not found), where 2.7's
  P_fit gives 2 for A1, not 8, and 1 for MC, under its P = 3 (section 2.8). WP1 then takes at least about 14 h at P = 2
  (about 9.3 h at P = 3), not 4-5 h. Under 45 GB A1 (and MC) refuses to start. Build step 0a re-measures the disk.
- **Kept outside the lab (D3).** The lead kept, at about 10:02 PM, in
  `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/` with sha256 (its README.txt; this PC only, not git): T31's
  fixture sources (E0's three L5 `world_last.jsonl`, `row.json` and `ai_player.log`, in `e0-L5/`), T35's real K1
  tells (`c-fix/C_FIX_actions.jsonl`) and four scripts (`scripts/`: `stage_merge.py`, `stage_diag.py`,
  `replay_leg.py`, `compare_moves.py`). T31 and T35 name that folder (24-a). v4 added there (cp -p, each cmp-equal to
  its source; the README's appended section): the spec's 1.2 Lab kit (`ch6probe11/`: `build_stage11.py`,
  `make_arm11.py`, `arms11.py`; `bp1r2/seeds_free.py`), `mergeplan/find_junctions.py` and the C1-C3 starts
  (`ch5stops/out/probe/`, md5-equal to 2.1's table). The G starts stay in `C:/Remote Projects/_livechain/graded-ch5`,
  outside `_ai_lab/s53/`. A1's build still cuts T31's fixture and copies T35's into git, with their sha256.
- **Every old text is a fenced block that occurs exactly once in the spec** (section 1.4; counts also in `STATE.md`).
- **No question for the user.** Every call here is technical (section 1.3).

## 1. How each review item is answered

### 1.0 v3: the re-check's findings (`result.a1.check.findings[0..13]`, in its order) and the lead's calls

| C | Sev | The re-check found (short) | Lead's call | Answer in v3 (edit ids) |
|---|---|---|---|---|
| C1 | MINOR | GM's GOALS-OFF arm has no measure: `item_errands` is `unknown` for a leg that carries no snapshot | 1 | **Changed.** `measures.stale` is measured against the start's kept `goals_last.jsonl`, carried or not (`snapshot`: carried, kept or none); `unknown` only when the start has no snapshot at all (23-b); 3.15 items 5 and 7 (01-k); T35's GOALS-OFF cases (24-a) |
| C2 | MINOR | Definition-of-done item 0 (items 6-7 before any snapshot) blocks GM's own chain and P1 | 2 | **Changed.** "item 6 before any leg carries a snapshot; item 7 before WP1" (01-n) |
| C3 | MINOR | T31 has no case at the LOOP boundaries that its mutants name | 3, adapted | **Changed.** T31's CONTROL "at each boundary": 40 crossings, LOOP; a last crossing exactly 120,000 frames before the end, LOOP; 120,001, its own key, flagged (24-a). **Adapted:** call 3's share row ("a share of exactly 0.50 with the last crossing 120,001 frames before the end gives LOOP") is not written as LOOP, because call 4 drops the share clause: under the amended rule that leg keeps its own key. T31 asserts that instead (v4, D1: a window share of 0.75, above v2's dropped 0.5 and at most 0.80 on a 600,000-frame leg with its last crossing 120,001 frames before the end; v3's 0.95 could not occur there; 120,001 frames: its own key), and the 0.5 mutant becomes `<=` → `<` at 120,000 (24-b) |
| C4 | MINOR | v2's LOOP "departure" was unforced: E0 T's 92,013 frames are inside v2's own 120,000-frame clause | 4 | **Changed.** Clause (4a) dropped; (4) is now the end rule only (03-b). Section 0, 1.1 R6, 2.4, AM-03 and section 4 item 1 corrected; 22-a (i), 18-d, section 5 step 1, section 6 |
| C5 | MINOR | MC is not "exactly" E0's harness while A1's 1 GB cut and 1.25 GB profile budget apply to it | 5 | **Changed.** An MC job's world cut is `live_chain.GUARD_WORLD_BYTES` (1.5 GB), its profile budget 1.75 GB, above it (05-b, 07-b, 07-c, 07-d, 07-e); T14 (07-f) and T33 (24-a) test it |
| C6 | MINOR | "at least 4.4 h" is drawn from upper-bound rows | 6 | **Changed.** "about 4.4 h (budgeted from upper-bound rows)" in section 0, 1.1 R13, 18-a, 18-c, 18-e, AM-18 and section 5; the merge's own full lane (`07`'s merge entry) gives the measured hours, which A1's build plan reads at step 0a (18-c, section 5) |
| C7 | MINOR | P2's CONTROL ignores the carried loss count | 7 | **Changed.** `stuck: N battles lost` ends with `losses_carried` > 0 are reported apart; the path and its measured 0 of 8 are in the discriminator (12-d) |
| C8 | MINOR | Part 0 moves the play digest, unstated; MC's first run need not read PASS | 8 | **Changed.** 3.1 (01-f) and a new 3.15 item 8 (01-k) say so; MC's first run, on the A1 commit's stage, MUST read PASS before WP1 (05-a, 05-b, 05-d, 13-a, section 5 step 6); MC stays a SHOULD on later merges (AM-05) |
| C9 | MINOR | A WP1b dependency WAIT holds the whole queue, and `--max-wait` can DROP it first | 9 | **Changed.** A per-job SKIP: later ready jobs launch, the job keeps its place, no `--max-wait` clock; the fallback start when the source chain ENDS without a reached L5 (07-e; 01-c, 01-e); "GO, WAIT, SKIP or DROP" (new 07-h); T26 and T34 (07-g, 24-a); mutants (24-b) |
| C10 | NIT | Three line ranges | - | **Changed.** `learn_slide` :824-840 (04-a, AM-04); `REFUTE.md` :256-258 (19-a); `DIAGNOSIS.md` :267-269 (05-b, AM-21) |
| C11 | NIT | 2.1's "1,643 frames lower" holds for 3 of the review's 5 runs | - | **Changed.** "from each log's first frame (f748040-f748082), so 1,643-1,685 frames lower" (2.1) |
| C12 | NIT | Two contradictions inside part 0 | - | **Changed.** (a) `starter_from: job_file` for a G start, `truth_party` for a C start (01-c); (b) "a leg after a hard kill" dropped from 3.15 item 5 (01-k) |
| C13 | NIT | AM-21 files its `03` item on a frozen `main` | - | **Changed.** "in the merge's docs pass (`06` 2026-11-12 merge item 1) or after the merge commit" (AM-21) |
| C14 | NIT | Presentation gaps (a)-(e) | - | **Changed.** (a) R14 "estimates"; (b) the size in CRLF bytes: "about 107 KB" for v3 (AM-25, 25-b; the asked "about 98 KB" was v2's 98,332-byte applied file); (c) new block 25-c puts "amended parts read at `3caf9c47`" in the header; (d) 3.8's precedence: LOOP condition (5), the raise reason first (03-b, 08-a, T36); (e) 1.4 re-dated, with v3's counts |

**Also (the lead; reworded in v4 under D3):** every lab path a NEW block names now cites a git source, names a kept
copy in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/`, or carries "(lab, deleted after the merge)". By the
lead's ruling every folder under `_ai_lab/s53/` is lab that the merge's cleanup may delete, and only `_ai_lab/keep/`
is kept; v3's "not on the deletion list" for `bp1r2/`, `bp1r4/`, `ch5stops/` and `ch6probe11/` no longer holds.
`a1prep/tools_v4/lab_scan4.py` lists 26 NEW-block lines with a lab token (in 01-c, 01-k, 02-a, 02-b, 03-b, 05-b,
13-a, 14-a, 15-g, 16-d, 17-b, 19-a, 22-a, 24-a). Each one's sentence names a git source (ledger entries and their
evidence files, the repo notes), a kept copy, or "(lab, deleted after the merge)"; BP-1's run names stand beside their
ledger entries; `C:/Remote Projects/_livechain/` is named as outside the lab. No NEW block marks a path only "(lab)",
and none cites a lab STATE.md line number. The facts new since v2 are in section 2.8.

### 1.0b v4: the delta re-check's findings (`result.a1.check.findings[0..7]`, in its order) and the calls D1-D8

The delta re-check is `result.a1.check` in `wf_result_wug76nq4r.json`; D1-D8 are its findings[0..7], in that order.

| D | Sev | The delta re-check found (short) | The lead's call | Answer in v4 (edit ids; the v4 text) |
|---|---|---|---|---|
| D1 | MINOR | T31's CONTROL "a window share of 0.95" with the last crossing 120,001 frames before the end cannot occur (at most 0.80 on 600,000 frames, 0.90 on 1,200,000); v3 dropped `window_share`'s only definition | "even with a window share of 0.75 (above v2's dropped 0.5; at most 0.80 on a 600,000-frame leg with its last crossing 120,001 frames before the end)" in 24-a, 1.0 C3 and section 4 item 8; define `window_share` in 23-b | **Changed.** 24-a, T31 CONTROL: "120,001 frames: its own key, flagged, even with a window share of 0.75 (above v2's dropped 0.5; at most 0.80 on a 600,000-frame leg with its last crossing 120,001 frames before the end; there is no share rule)". 23-b: "window_share ((the pair's last crossing - its first) / the leg's frames; reported, never a rule)". 1.0 C3 and section 4 item 8 say the same; AM-23 and AM-24 carry v4 lines. The arithmetic: (600,000 - 120,001) / 600,000 = 0.799998; a share of 0.75 puts the first crossing at frame 29,999 of the leg and the last at 479,999 |
| D2 | MINOR, for the lead | DOCS-ADDENDUM section 3 named v1 (`AMENDMENTS.md`) as the repo note's source | done by the lead; v4's header says v4 is the final copy | **Stated.** The header: "v4 is the final copy, and it becomes the repo note ... v1 (`AMENDMENTS.md`), v2 and v3 are earlier drafts kept in the lab; none of them is the note." `mergeplan/DOCS-ADDENDUM.md` section 3 now reads "Its source: `s53/a1prep/AMENDMENTS-v4.md` (the final copy; v1 `AMENDMENTS.md`, v2 and v3 are earlier drafts kept in the lab, NOT the note)" |
| D3 | NIT | 4 NEW-block citations of `bp1r2/` and `bp1r4/` marked only "lab" (02-b, 05-b, 16-d, 17-a) | every folder under `_ai_lab/s53/` is lab the cleanup may delete; only `_ai_lab/keep/` is kept. Cite a git source (A1's own seed check; BP-1's evidence or ledger), the kept copy, or "(lab, deleted after the merge)"; section 0 states what the lead kept; T31 and T35 name the folder; copy any other lab file a NEW block relies on; reword 1.0's "Also" | **Changed.** 02-b: "BP-1 round 2 saw both (`ai_player/evidence/2026-11-11-bossprep-bp1r2-live-ab.txt` :61-67): ledger #125's C and B decision streams were IDENTICAL in 3 of 3 pairs, and #127's C2L4 pair split at a map change at frame 617,525 (11 frames against 10)" (merged ids since the lead's fix after the v4 check; the branch's #119 and #121). 05-b: "checked FREE by A1's own seed check before the first launch (2.5; 3.10's `--ledger development`; T13). The range read FREE in 308 ledgers at 7:46 PM 2026-11-13 (the repo note `2026-11-13-A1-SPEC-AMENDMENTS.md`, section 2.6)" (v3's "at `plan` time" corrected: 3.10 checks the seeds before `ledger.begin`, before the first launch). 16-d: "(ledger #131-#133; their raises ended at frames 457,706, 460,630 and 450,262 of 450,000 in #131 and at battles 164, 164 and 163 of 160 in #132-#133: `ai_player/evidence/2026-11-11-bossprep-bp1r4-live.txt`, P-W5 and P-G6)", "each L6 read from its run's own log (lab, deleted after the merge)". 17-a: "A1's own seed check (this section and 3.10's `--ledger development`, T13) checks every seed again before the first launch". T31 and T35 name `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/` (`e0-L5/`, `c-fix/C_FIX_actions.jsonl`, 24-a). 14-a and the new block 15-g (1.2's Lab kit row, :64) name the kept kit; 01-c names the kept C1-C3; 01-k and 03-b add ledger entries #133 and #132 and this note's sections. Section 0's item is now a statement; the header, 1.0's "Also", 2.8 and section 6 follow. **Copied** (cp -p; cmp 17 of 17 equal; sha256 in the keep README's appended section): the spec's 1.2 Lab kit (`ch6probe11/build_stage11.py`, `make_arm11.py`, `arms11.py`; `bp1r2/seeds_free.py`), `mergeplan/find_junctions.py` (14-a's junction scan), and C1-C3 (`ch5stops/out/probe/`, 12 files, md5-equal to 2.1's table). **Declined:** copying `_livechain/graded-ch5` (outside `_ai_lab/s53/`; section 4 item 9) |
| D4 | NIT | MC's 1.5 GB cut is missing from the spec's :179 and :273, so an MC leg would carry the reason "over 1 GB" | two new blocks, each adding "(an MC job: over 1,500,000,000 bytes, live_chain's guard, 2.4b)"; ids in the scheme; every count line updated | **New blocks 07-i and 07-j.** 07-i (2.7, :179): "a newest `world.jsonl` over 1,000,000,000 bytes (an MC job: over 1,500,000,000 bytes, live_chain's guard, 2.4b) is killed (CUT-WORLD)". 07-j (3.5, :273): "the probe's guard killed the launch (its kill marker) for `world.jsonl` over 1 GB (an MC job: over 1,500,000,000 bytes, live_chain's guard, 2.4b), or for the job's profile folder over its budget (3.12)", its blocker text: "for an MC job "over 1.5 GB"; for the profile cut "profile folder over budget"". **Added beyond the call:** the profile-folder kill, which 07-d sends to "CUT-WORLD's rule" but 3.5's first-match table did not list. Each new old text occurs once and overlaps no other block's; section 0 and 1.4 count 87 blocks (15-g, D3, is the third new one) |
| D5 | NIT | AM-22 (vi) duplicates the correction the merge's docs pass writes (DOCS-ADDENDUM G4) | (vi): cite the merge's `06` correction; write one only if it is absent; step 0a reads `06` first | **Changed.** 22-a (vi): "cite the merge's `06` correction of USER RULING 55 (2)'s reason (the merge docs pass's entry "E0's STOP and the fix-forward", DOCS-ADDENDUM G4: lab, deleted after the merge); write one only if it is absent". Section 5 step 0a: "Read `06` first (v4: the merge's entry "E0's STOP and the fix-forward" carries USER RULING 55 (2)'s corrected reason, AM-22 (vi))". 1.3, section 0 and AM-22's v4 line follow |
| D6 | NIT | AM-18 calls all four raised rows kill times; `revert_safety_gates`' 3456 was a PASS | "(three of them the side lanes' kill times, lower bounds there; revert_safety_gates' 3456 a PASS time, 3455.6 s, 96 % of its 3600 s floor)" | **Changed.** AM-18's evidence: "(three of them the side lanes' kill times, lower bounds there; revert_safety_gates' 3456 a PASS time, 3455.6 s, 96 % of its 3600 s floor; all four "upper bounds under load until measured alone", the `_doc`)", checked against `fa9f073d`'s `_doc` ("ran revert_safety_gates 3455.6 s (96 % of its 3600 s floor)") |
| D7 | NIT | 2.4's STRICT-rule sentence contradicts itself: E0 C's last crossing came 20 frames before its end | "A STRICT rule (a tolerance of a few frames: E0 C's last crossing came 20 frames before its end) would key T by its own key and C by LOOP" | **Changed, adapted.** 2.4: "A STRICT rule (a tolerance of a few dozen frames: E0 C's last crossing came 20 frames before its end) would key T by its own key and C by LOOP". **Adapted:** a tolerance of "a few frames" (under 20) would key C by its own key too, the same contradiction; "a few dozen" covers C's 20 frames and stays far under T's 92,013 |
| D8 | NIT | the disk kept falling: 48.22 GB at 9:53 PM gives MC a P_fit of 2 | quote the newest disk reading and PRELANE line; the disk falls about 3 GB an hour while the tuner runs (two dated readings); MC's P_fit 2 below about 48.25 GB; step 0a re-measures; section 0 follows | **Changed, adapted in part.** 2.8: the newest readings, "C: 47.71 GB free" (`fix5/STATE.md` line 102, 10:13 PM) and the lead's line ("47.95 GB free at 10:00 PM ... falling about 3 GB an hour while the tuner runs (53.2 at 8:10 PM)"), and v4's own `df` (46,895,435,776 bytes at 10:35 PM); the two dated readings, "53.2 GB at 8:10 PM ... and 47.95 GB at 10:00 PM, so 5.25 GB in 110 minutes, about 2.9 GB an hour on average"; "MC's P_fit is 2 below about 48.25 GB"; A1's P_fit is 3 at 47.95 and 46.90 GB (below 48.0); "A1 refuses to start under 45 GB ... 46.90 GB is under an hour above it". PRELANE's newest line (`fix5/STATE.md` line 103, 10:21 PM): `revert_step5` "OVERALL: PASS" ("exit 0 in 7783 s"); `revert_step3` and `revert_r1` still RUNNING at the last re-read. **Adapted:** the fall was uneven (about 5.1 GB an hour from 8:53 to 9:13 PM, 0.8 from 9:13 to 9:53 PM), and PRELANE ran over the same span, so v4 says "the tuner and PRELANE both ran throughout; the cause was not checked". Section 0, section 5 and section 6 follow |

### 1.0c The lead's fixes after the third re-check (of v4)

v4's own check (`result.a1.check` in `a1prep/wf_result_wkvt2hxc1.json`, lab: READY_WITH_FIXES, 1 MINOR, 7 NIT, no
MAJOR; "every fix touches new text only") was answered by the lead in this file, about 11:00-11:20 PM 2026-11-13, with
the Edit tool, on a copy (`AMENDMENTS-v4.pre-lead.md` keeps v4 as the fixer left it, md5 `221af4a8`). No old block
changed: all three old-text scripts exit 0 afterwards (1.4).

| # | Sev | The check found (short) | Where the fix landed |
|---|---|---|---|
| L1 | MINOR | BP-1's ledger ids were `wip/ch6-bp1`'s, not the merged ledger's (+6) | merged ids everywhere (#125, #127, #131-#133), the branch ids beside them where an evidence file is cited (02-b, 16-d); a "Ledger ids" bullet in 2.8 gives the map; 01-k, 03-b, AM-01/02/03/16's v4 lines and 1.0b's D3 row follow |
| L2 | NIT | PRELANE finished, v4 said two drivers were running | 2.8 and section 6 quote all three results; the header reads `fix5/STATE.md` through line 106 |
| L3 | NIT | P_fit stops one step early | 2.8, section 0, 2.4b's v4 line and section 5's total: A1 2 from 45.5 GB, MC 2 from 46.5 GB and 1 below; the newest sample (46.21 GB, 10:50 PM) |
| L4 | NIT | DOCS-ADDENDUM line numbers went stale | cited by section (section 3; G4) in 1.0b's D2 row and AM-22's v4 line |
| L5 | NIT | "its README.txt" inside a subfolder | "the keep folder's root `README.txt`" in 01-c, T31 and T35 |
| L6 | NIT | 1,055 lines | 1.4: 1,056 line ends after these fixes (the fixer's v4: 1,054) |
| L7 | NIT | 16-d pointed to 2.1 for the derivation | "(section 2.1 and AM-16)" |
| L8 | NIT | "two re-checks" | "three re-checks" in the title and 25-b |

### 1.1 The findings (`findings[0..13]`, in the review's order)

| R | Sev | Review named | The finding (short) | Answer in v2 (v3 changes: 1.0; v4 changes: 1.0b) |
|---|---|---|---|---|
| R1 | MAJOR | AM-16, AM-08 | AM-16 closed the 80 % check the wrong way; the BRAWLY raise runs in L6, which used 82-86 % | **Changed.** AM-16 reversed and made MUST: L6 1,000,000 frames, 7,200 s wall, derived from the measured L6 frames (section 2.1); set before WP1's prediction is hashed; 3.4's `legs_of` dict; 2.3; section 5. AM-08 corrected: the raise runs in L6 (8 of 8 runs). P2's CONTROL re-derived under the raise (AM-12, edit 12-d). 2.8 and 6.2 in AM-18 |
| R2 | MAJOR | AM-01, AM-05, AM-13 | GM's restore of "exactly what a continue restores" has unexamined effects (losses, save fields, MC and #101 harness, no WP1b fallback) | **Changed.** AM-01 lists the restore field by field: errand fields restored; `last_save`, `saved_for` reset; losses carried (no concrete harm found; consequence measured and recorded). Chain and practice legs carry; MC does not (AM-05). Comparisons with #101, E0, E0-2 name the difference (AM-13). WP1b fallback start (edit 01-c). Goal custody joins 3.6 and T27 (01-h, 01-i, 01-m) |
| R3 | MINOR | AM-01 | 3.11, T9, 3.1, section 0 still contradict GM; 2.1, 2.4, 2.8, 6.2 have no text | **Changed.** Edits 01-a (section 0), 01-b (1.3), 01-c (2.1), 01-d and 01-e (2.4 table and order), 01-f (3.1), 01-g (3.4), 01-h and 01-i (3.6), 01-j (3.11, eighth key), 01-k (3.15), 01-l (T9, 8 keys), 01-m (T27), 01-n and 01-o (4.4); 2.8 and 6.2 in AM-18. GM and `check_purity.py`: 3.15 item 4 states the re-registration |
| R4 | MINOR | AM-01, AM-09 | Fix E makes "no item ball where it lay ... any more" fire for a ball only out of reach | **Changed.** `measures.stale` counts only tiles in the snapshot's `tried_items` (v3: the start's kept snapshot, carried or not, 1.0 C1), per tile, and reports the rest apart (AM-09, AM-23). GM's live discriminator is that per-tile count, computed before the A/B on a chain's chapter-5 end made by part 0's code (3.15 item 7). P11's B1F starts are not used (a P11 follow-up ordered after A1) |
| R5 | MINOR | AM-12, AM-03, AM-04 | K1 cannot fire at P1's or P2's walls; K1's tells are not recorded | **Changed + new.** AM-12 drops K1 as a reason and cites `k1_blast.out.txt`. New AM-20: `measures.k1_leads`; T16 CONTROL that a K1 tell is never a foe; WP1's prediction expects few chapter-5 LOOP keys after E and K1 (AM-13). **Declined in part:** `ch5loop_tcap.world.jsonl` as a T31 CONTROL (it holds 0 transitions); it becomes a T16 CONTROL instead |
| R6 | MINOR | AM-03, AM-12 | The LOOP key conflicts with T6, 1.3's D7 "Hold" and the CONTROLs; can hide a later end; 1-run filter; ping-pong ends; `crossings_raise` | **Changed** (v3: no departure, 1.0 C4). T6 scoped (03-c); 1.3 D7 "Changed" (01-b); P1(b), P2's CONTROL, T8 read LOOP records (12-c, 12-d, 03-d); LOOP keys filed at 1 run (AM-22); `pingpong_ends` counted; `crossings_raise` by the ACTIVE raise goal. The "only when the loop runs into the leg's end" rule is kept, read with a 120,000-frame tolerance (`STORY_PATIENCE`): E0 T's last crossing came 92,013 frames before its end and E0 C's 20, so both get the LOOP key (section 2.4). v2's window-share clause is dropped |
| R7 | MINOR | AM-13 | Cite E0-2, not the fix's per-leg A/B, as the control's prior | **Changed.** 13-a cites E0-2's verdict line (v2: `mergeplan/STATE.md` line 248, STAGE FX line 256; v3: the message of commit `19e9700c` and ledger #148, which survive in git); the fix's A/B is mechanism evidence only |
| R8 | MINOR | AM-02 | `06`'s reason for USER RULING 55 (2), "so runs replay", is refuted by E0 | **New.** AM-22 item (vi): a new `06` entry corrects the REASON; the decision (the frame budget) stands, DO-NOT-REOPEN respected (section 1.3) |
| R9 | MINOR | many | Old texts fail an exact match (line wraps, a duplicate, JSON forms) | **Changed.** Every old text is a fenced `~~~old` block with its exact characters, newlines and indents included; AM-15's `:1368` is anchored to 1.2's row only; AM-18 uses the literal Total row. All occur exactly once (section 1.4) |
| R10 | MINOR | AM-18 | Section 0's cost, WP1 shape and machine time are stale | **Changed.** Edits 18-a and 18-b (section 0's WP1 and Cost bullets), 01-a (part 0), 21-a (what A1 v1 does not answer) |
| R11 | MINOR | AM-05 | MC is labelled MUST; no seeds; false-STOP rate unstated | **Changed.** AM-05 is SHOULD; seed rule 6701-6799, 3 a merge; 1 - p^3 stated, p UNKNOWN (E0-2's 3 of 3 bounds it only below 0.37); one STOP's cost measured once (about 11 h); MC carries no goal memory |
| R12 | MINOR | AM-13 or new | The open chapter 1-5 miss-rate question is not given to A1 | **New, as the lead ruled.** AM-21: out of A1 v1's scope, stated in section 0, filed as its own item (a seeded batch, pre-merge `main` against the merged tree). **Declined:** the review's first option, a main-tree arm inside A1 |
| R13 | MINOR | AM-18 | The full regression lane's hours are not budgeted | **Changed.** 18-c (2.8), 18-e (6.2), 18-a (section 0) and the build plan (section 5): about 4.4 h, budgeted from upper-bound rows (`revert_bossprep` 15,931 s and `revert_p11` 12,879 s, PROVISIONAL), about 9-10 h if it times out once; the merge's own full lane gives the measured hours (v3, 1.0 C6) |
| R14 | NIT | AM-02, AM-04, AM-07, AM-15 | Small inaccuracies; memory.py lines moved +35 at `9d2f3fc5` | **Changed.** "may move it (suggestive)" (02-a, 19-a); memory.py cited by symbol with lines at `3caf9c47`, re-read at build step 0a (04-a, 15-e); AM-07 estimates the job's profile folder from its parts (no profile folder was measured) and raises the out estimate (07-b); unknown ride and bump keys dropped AND listed, with T16 cases (04-a, 04-b) |

### 1.2 The missing amendments (`missing_amendments[0..13]`, in order)

| M | Item (short) | Answer |
|---|---|---|
| M1 | The L6 budget, P2's CONTROL under the raise | AM-16 (16-a to 16-f), AM-12 (12-d), AM-18 |
| M2 | GM's restore scope at a `--state` start; who carries; MC, the WP1 control, 3.6/T27 | AM-01 (3.15 items 2 and 5; 01-h, 01-i, 01-m), AM-05, AM-13 |
| M3 | A WP1b rule for a pair whose WP1a chain misses | AM-01 (01-c, 01-d, 01-e), AM-07 (07-e, 07-g, 07-h: the per-job SKIP, v3, and the fallback), AM-24 (T34) |
| M4 | AM-01 carried through 3.11, T9, 3.1, section 0, 2.1, 2.4, 2.8, 6.2; the re-registration | AM-01 (01-a to 01-o), AM-18 (2.8, 6.2), 3.15 item 4 |
| M5 | A per-tile stale measure and GM discriminator | AM-09, AM-23 (`measures.stale`), 3.15 item 7 |
| M6 | `measures.k1_leads`; a T16 control; AM-12 without K1 | AM-20, AM-23, AM-04 (04-b), AM-12 |
| M7 | A `06` correction of USER RULING 55 (2)'s reason | AM-22 item (vi) |
| M8 | AM-03 made consistent (7 parts) | AM-03, AM-01 (01-b), AM-12, AM-22, AM-23, AM-24; v3 keeps the review's end rule, with a tolerance (1.0 C4) |
| M9 | AM-13 cites E0-2 | AM-13 |
| M10 | Section 0's headline | AM-18 (18-a, 18-b), AM-01 (01-a), AM-21 |
| M11 | MC: seed rule, false-STOP rate, SHOULD | AM-05 |
| M12 | A1's role on the chapter 1-5 frequency question | AM-21 (out of scope, own item) |
| M13 | The full lane's machine time | AM-18, section 5 |
| M14 | 4.4 item 8's list of `06` entries | AM-22 |

### 1.3 Questions for the user

None. I agree with the review's six judgments. Rule-11 lookups v2's revision ran (`py -3.12 -B tools/decomp_lookup.py
ask`, read-only, in R, about 8:05 PM):
- "loss count MAX_LOSSES carried across legs goal memory test start": NO PRIOR RULING OR FACT FOUND.
- "frontier probe leg budget L6 chapter 6 frames raise": NO PRIOR RULING OR FACT FOUND.
- "merge check seeds false stop rate chapter 1-5": NO PRIOR RULING OR FACT FOUND.
- "frame budget runs replay checked determinism": USER RULING 55's DO-NOT-REOPEN, `06` :9965 ("Do not re-ask ...
  which limit ends a session (the frame budget; the clock is a backstop)"). AM-22 (vi) keeps that decision; it cites
  the merge's correction of the stated reason, or writes one only if it is absent (v4, D5), so the ruling is not
  reopened.

v3 asks the user nothing either: its changes are the lead's calls on the re-check. It read R's `06` :10104 ("a play
change now would need a new live round"), :10106 ("Evidence is found by the TREE DIGEST it records"), :10124 (the
merge's docs pass happens in the merge worktree) and :10125 (`main` is frozen until it takes the merge). None is
contradicted.

v4 asks the user nothing either: D1-D8 are the lead's calls on the delta re-check. The copies into `_ai_lab/keep/`
follow the lead's D3 ruling, and the cleanup list itself goes to the user (the lead's line, D3).

### 1.4 How to apply the edit blocks, and the check

- Each edit is a pair of fenced blocks with one id: `~~~old <id>` holds the spec's text exactly (its newlines and
  continuation indents included), `~~~new <id>` the replacement. Read the spec as UTF-8 text with CRLF turned to LF;
  each old block occurs there exactly once; replace it; keep the file's CRLF line ends.
- No two old blocks overlap, and no new block contains another block's old text, so they may be applied in any order;
  applied one by one in id order the result equals applying all by span. Apply each block ONCE: 17 of them insert
  text and keep their own old text inside the new (01-a, 01-c, 01-k, 03-b, 05-b, 07-b, 09-a, 11-a, 14-a, 15-f, 16-f,
  17-b, 19-a, 21-a, 24-a, 25-b, 25-c). `<the merge commit>` in 15-d is filled at apply time.
- Checked by three independent read-only scripts (lab, deleted after the merge; their output is quoted here):
  `a1prep/tools_v2/check_v2_oldtext.py SPEC AMENDMENTS-v4.md` (each old block counted in the text form and, with
  `\r\n` line ends, in the raw bytes, both 1; every id paired; no spans overlap; no new block holds another's old text;
  the id-order apply equals the span apply); the first re-checker's `a1prep/recheck/count_oldtext.py SPEC
  AMENDMENTS-v4.md` (overlap-inclusive counts T in the LF text, B in the raw CRLF bytes, W with whitespace collapsed;
  overlap and adjacency; stray fences); and the second re-checker's `a1prep/recheck3/count3.py SPEC AMENDMENTS-v4.md`
  (T, B and W all 1; overlaps; new-contains-old; the span apply equal to the sorted-id and the note-order applies;
  this table's spec lines). `a1prep/tools_v3/applied_check.py` applies all in memory and checks the applied tables;
  `tools_v3/counts_table.py` printed the table below.

**v4's counts, printed at about 10:37 PM PST on 2026-11-13** against the spec as it is now (60,366 bytes, md5
`0d5e04fc...`): **87 old blocks and 87 new, ids paired; every old block 1 in the text form and 1 in the raw CRLF
bytes (`check_v2_oldtext.py`: "ALL OLD TEXTS EXACTLY ONCE, NO OVERLAP", exit 0); T 1, B 1, W 1 in
`count_oldtext.py` ("NOT EXACTLY ONCE: none", exit 0) and in `count3.py` ("NOT EXACTLY ONCE: none", "OVERLAPS:
none", "NEW contains ANOTHER id's OLD: none", "1.4 table rows: 87; mismatches: none", "RESULT: ALL CHECKS PASS",
exit 0); no overlap (02-a ends where 01-e begins, offset 15655, which touches without overlapping, as in v2 and v3);
"sequential apply in id order equals the span apply: True"; the applied text is 108,917 bytes as LF text (UTF-8),
109,973 bytes with CRLF, 1,056 lines (line ends, as `wc -l` counts them), every table row with its header's cell
count.** (Re-run by the lead after the lead's fixes of 1.0c, all three scripts exit 0; v4 as the fixer left it read
108,730 / 109,784 bytes and 1,054 line ends.) v3's 84 blocks keep their counts; v4 adds 07-i, 07-j and 15-g. "spec
line" is where the block begins in the current spec.

| id | text | bytes | spec line | id | text | bytes | spec line | id | text | bytes | spec line |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01-a | 1 | 1 | 23 | 01-b | 1 | 1 | 72 | 01-c | 1 | 1 | 106 |
| 01-d | 1 | 1 | 144 | 01-e | 1 | 1 | 149 | 01-f | 1 | 1 | 204 |
| 01-g | 1 | 1 | 262 | 01-h | 1 | 1 | 295 | 01-i | 1 | 1 | 298 |
| 01-j | 1 | 1 | 392 | 01-k | 1 | 1 | 433 | 01-l | 1 | 1 | 452 |
| 01-m | 1 | 1 | 470 | 01-n | 1 | 1 | 523 | 01-o | 1 | 1 | 525 |
| 02-a | 1 | 1 | 148 | 02-b | 1 | 1 | 500 | 02-c | 1 | 1 | 585 |
| 02-d | 1 | 1 | 37 | 03-a | 1 | 1 | 322 | 03-b | 1 | 1 | 326 |
| 03-c | 1 | 1 | 449 | 03-d | 1 | 1 | 451 | 04-a | 1 | 1 | 335 |
| 04-b | 1 | 1 | 459 | 05-a | 1 | 1 | 143 | 05-b | 1 | 1 | 151 |
| 05-c | 1 | 1 | 212 | 05-d | 1 | 1 | 524 | 06-a | 1 | 1 | 199 |
| 06-b | 1 | 1 | 485 | 07-a | 1 | 1 | 176 | 07-b | 1 | 1 | 185 |
| 07-c | 1 | 1 | 398 | 07-d | 1 | 1 | 401 | 07-e | 1 | 1 | 414 |
| 07-f | 1 | 1 | 457 | 07-g | 1 | 1 | 469 | 07-h | 1 | 1 | 411 |
| 07-i | 1 | 1 | 179 | 07-j | 1 | 1 | 273 | 08-a | 1 | 1 | 324 |
| 08-b | 1 | 1 | 328 | 09-a | 1 | 1 | 300 | 09-b | 1 | 1 | 329 |
| 10-a | 1 | 1 | 403 | 10-b | 1 | 1 | 182 | 10-c | 1 | 1 | 458 |
| 11-a | 1 | 1 | 215 | 12-a | 1 | 1 | 489 | 12-b | 1 | 1 | 495 |
| 12-c | 1 | 1 | 499 | 12-d | 1 | 1 | 510 | 13-a | 1 | 1 | 517 |
| 14-a | 1 | 1 | 405 | 15-a | 1 | 1 | 60 | 15-b | 1 | 1 | 71 |
| 15-c | 1 | 1 | 320 | 15-d | 1 | 1 | 16 | 15-e | 1 | 1 | 582 |
| 15-f | 1 | 1 | 438 | 15-g | 1 | 1 | 64 | 16-a | 1 | 1 | 127 |
| 16-b | 1 | 1 | 128 | 16-c | 1 | 1 | 133 | 16-d | 1 | 1 | 135 |
| 16-e | 1 | 1 | 260 | 16-f | 1 | 1 | 531 | 17-a | 1 | 1 | 155 |
| 17-c | 1 | 1 | 158 | 17-b | 1 | 1 | 160 | 18-a | 1 | 1 | 24 |
| 18-b | 1 | 1 | 29 | 18-c | 1 | 1 | 189 | 18-d | 1 | 1 | 561 |
| 18-e | 1 | 1 | 568 | 19-a | 1 | 1 | 172 | 20-a | 1 | 1 | 349 |
| 21-a | 1 | 1 | 32 | 22-a | 1 | 1 | 526 | 23-a | 1 | 1 | 311 |
| 23-b | 1 | 1 | 312 | 24-a | 1 | 1 | 473 | 24-b | 1 | 1 | 479 |
| 25-a | 1 | 1 | 1 | 25-b | 1 | 1 | 638 | 25-c | 1 | 1 | 8 |

## 2. Evidence new since v1 (each run is one trajectory)

### 2.1 L6's frames, measured from C1 (`a1prep/tools_v2/l6_frames.py`)

L6 = the start record's frame (f746397, C1's truth) to the log's `MILESTONE ch6_dewford done at f<N>`. Every run is one
leg of 1,200,000 frames from C1 (`ch5stops/out/probe/probe-C1`), Story, target `ch7_brawly`.

| Run | Code | L6 frames | % of 600,000 | Raise ended | Walk and sail after the raise | Outcome |
|---|---|---|---|---|---|---|
| `bp1r4/out/ab4w/ab4w-B4-C1-6414` | BP-1 round 4 | 500,515 | 83.4 | frames 457,706 of 450,000 | 23,841 | ch7_brawly reached |
| `ab4w-B4-C1-6415` | same | 496,341 | 82.7 | frames 460,630 of 450,000 | 17,094 | ch7_brawly reached |
| `ab4w-B4-C1-6416` | same | 495,188 | 82.5 | frames 450,262 of 450,000 | 26,184 | ch7_brawly reached |
| `ab4g/ab4g-B4-C1-6426` | same | 395,755 | 66.0 | battles 164 of 160 | 28,011 | stuck: 3 battles lost |
| `ab4g/ab4g-B4-C1-6427` | same | 382,058 | 63.7 | battles 164 of 160 | 14,864 | stuck: 3 battles lost |
| `ab4g2/ab4g2-B4-C1-6429` | same | 377,952 | 63.0 | battles 163 of 160 | 19,900 | ch7_brawly reached |
| `fix5/runs/CH6_FIXED` | `9d2f3fc5` | 520,366 | 86.7 | frames 475,016 of 450,000 | 24,521 | ch7_brawly reached |
| `fix5/runs/CH6_UNFIXED` | `a90c8e8f` | 520,216 | 86.7 | frames 458,101 of 450,000 | 42,640 | ch7_brawly reached |

- 5 of 8 over 80 %. They are exactly the 5 whose raise ended on its FRAME bound (`[AI-BOSSPREP] ... the raise ends,
  budget spent (frames N of at most 450000)` in each `ai_player.log`).
- The raise runs in L6: in all 8 runs, 0 `raise` goal records come after `ch6_dewford`, and the raise's goal records
  name `ch6_briney_house` as their milestone (`"extra":{"milestone":"ch6_briney_house",...}` in `actions.jsonl`).
- The review measured from each log's first frame (f748040-f748082), a lower bound, so its numbers are 1,643-1,685
  frames lower (v3; the re-check's `recheck/l6_recheck.py`: 748,040 for 6414, CH6_FIXED and CH6_UNFIXED, 748,045 for
  6415, 748,082 for 6416).
- The largest L6 over Story's raise budget: 520,366 / 450,000 = 1.156. A Catcher's budget is 550,000 frames
  (`brain/bossprep.py` :160); 550,000 × 1.156 is about 636,000 frames, over 600,000. No Catcher L6 was measured.

### 2.2 Battles lost per chain (`a1prep/tools_v2/losses_per_chain.py`, "a battle was LOST" lines per leg)

| Chains | Lost per chain | Carried into chapter 6 (if carried) |
|---|---|---|
| #101 (`_livechain/graded-ch5`, `dc0a4e69`) | LC-C-6203 0, LC-C-6204 0, LC-S-6201 0, LC-S-6202 2 (L3, L4), LC-T-6205 1 (L5), LC-T-6206 1 (L5) | 0, 0, 0, 2, 1, 1 |
| E0 (`mergeplan/e0/runs/E0-6481`, `c25d2c40`) | LC-C-6482 0, LC-S-6481 0, LC-T-6483 2 (L3, L5) | 0, 0, 2 |

- With the count carried, no chapter 1-5 leg of these 9 chains would have ended early (none reached 3).
- BRAWLY in BP-1 round 4 from C1 (0 carried): `ab4g-6426` and `-6427` lost 3 (stopped); `ab4g2-6429` lost 2, then won;
  `ab4w-6414/6415/6416` lost 0.

### 2.3 E0-2 (FX4 on seeds 6484-6486)

- `mergeplan/out/merge/E0-2_6_judge.txt`: LC-S-6484, LC-C-6485, LC-T-6486 each "REACHED ch5_rival_meet"; 19.5, 21.3
  and 29.8 min of legs; "batch: purpose development, verdict by its registered rules PASS, ledger entry #148".
- Its verdict line: "E0 VERDICT: REACHED 3 of 3; legs ran 15, purity-clean 15; wall 31 min (cap 120); problems 0 ->
  GO" (`mergeplan/STATE.md` line 248; the STAGE FX line, 256, repeats it). In git: the message of commit `19e9700c`
  carries the same line; ledger #148's evidence file `ai_player/evidence/2026-11-13-chain-heldout-dev-ch5_rival_meet-6484.txt`
  line 3 reads "code: HEAD 3caf9c47" and line 49 "LC.REACH ... 3 of 3 (bound: at least 2 of 3)".
- Largest world in E0 and E0-2 legs: 275,942,646 bytes (E0 T L5), then 119,208,232 (E0 C L5), 92,892,223 (E0-2 T L3)
  (`row.json` `world_file.bytes`). None reached 300 MB.

### 2.4 Loop windows (`a1prep/tools_v2/loop_window.py`, `ai_player.log` "MAP A -> B" lines)

| Leg | Reached | Top pair | Crossings (during an ACTIVE raise) | Window share of the leg | Last crossing to the leg's end | `stuck: ping-pong` goal ends | End |
|---|---|---|---|---|---|---|---|
| E0 LC-T-6483 L5 | no | PETALBURG_WOODS-ROUTE104 | 118 (0) | 0.60 | 92,013 | 25 | stopped: not finished within 600000 frames |
| E0 LC-C-6482 L5 | no | PETALBURG_WOODS-ROUTE104 | 74 (0) | 0.82 | 20 | 8 | stuck: no progress for 120153 frames |
| E0 LC-T-6483 L3 | yes | PETALBURG_WOODS-ROUTE104 | 14 (0) | 0.83 | 18,340 | 1 | done |
| E0-2 LC-T-6486 L3 | yes | PETALBURG_WOODS-ROUTE104 | 92 (0) | 0.78 | 25,296 | 13 | done |
| E0-2 LC-S-6484 L5 | yes | ROUTE116-RUSTBORO_CITY | 20 (0) | 0.59 | 40,827 | 0 | done |
| fix5 T_FIX_1 (T's L4 start) | yes | ROUTE116-RUSTBORO_CITY | 6 (0) | 0.78 | 38,299 | 0 | done |
| bp1r4 ab4w-6414 (L6+L7) | yes | ROUTE116-RUSTBORO_CITY | 16 (8) | 0.74 | 165,738 | 0 | done |
| fix5 CH6_FIXED (L6+L7) | yes | ROUTE116-RUSTBORO_CITY | 20 (10) | 0.77 | 152,858 | 0 | done |
| bp1r4 ab4g-6426 (L6+L7) | no | DEWFORD_TOWN-DEWFORD_TOWN_GYM | 5 (0) | 0.10 | 28,471 | 0 | stuck: 3 battles lost |

- E0 T escaped its loop and beat the grunt at f1257345 (DIAGNOSIS :145), then ran out on `ch5_return_goods`. A STRICT
  rule (a tolerance of a few dozen frames: E0 C's last crossing came 20 frames before its end) would key T by its own
  key and C by LOOP: two 1-run keys again (v4, D7; v3 wrote "the last crossing at the leg's end itself", which would
  key C by its own key too). v3's rule reads "runs into the leg's end" with a 120,000-frame tolerance
  (`STORY_PATIENCE`, `mode.py` :112): T's last crossing came 92,013 frames before its end and C's 20, so both get the
  one LOOP key. No measured leg needs the window share, which v2 added and v3 drops (1.0 C4). Of the not-reached legs
  in this table, only those two reach 40 crossings.
- v1's calibration "reached legs at most 14" is superseded: E0-2's T L3 REACHED with 92 crossings. A reached leg is
  never ranked (churn table), so the 40 bar still separates E0's two loop legs (118, 74) from the other not-reached
  legs measured (5 and 6 crossings: `ab4g-6426` and `-6427`). BP-1's reached raise runs crossed their top pair at most
  20 times, 10 of them during an active raise.
- The fix's arms from E0's starts crossed the woods pair 1 (T), 0 (C) and 0 (S) times (`fix5/STATE.md`, "X").
- `gates/fixtures/ch5loop_tcap.world.jsonl` (in `3caf9c47`) keeps 4 maps, warps and connections and 0 transitions.

### 2.5 K1 and E at `3caf9c47`

- K1: `brain/goals.py` `WAY_IN = "a seasoned player's knowledge"` :875; `entry_lead` :878-906 sets `lead.why =
  f"{WAY_IN}: {lead} has a way into it"`; `_travel_on` tells `"[AI-GOALS] {target_map} is somewhere it has not been:
  first to {lead}, {because}"` (:3699). `hands/pad.py` `tell` :232-235 writes it to `actions.jsonl` as a `tell`/`say`
  record. `fix5/runs/C_FIX/actions.jsonl` holds 2: "[AI-GOALS] RUSTURF_TUNNEL is somewhere it has not been: first to
  ROUTE116, a seasoned player's knowledge: ROUTE116 has a way into it".
- K1 cannot fire at the planted walls: `fix5/verify1/k1_blast.out.txt` gives K1-eligible False for `ch1_rival_route103`
  (go ROUTE103) and `ch6_briney_house` (go ROUTE104_MR_BRINEYS_HOUSE); `fix5/STATE.md` (4:15 PM): "K1's only
  live-reachable change in chapters 1-7 is RUSTURF_TUNNEL -> ROUTE116".
- E: `Navigator.walls` (`brain/navigator.py` :816-820) returns `objects_now` (which E fills with the things seen standing
  this session) plus `scene_walls`. `_back_to_ball` (`goals.py` :3367-3391) gives "not picked up: no item ball where it
  lay at {goal.tile} any more" whenever the ball is not in view after the walk; `fix5/STATE.md` 3:18 PM shows it for a
  ball only out of reach at (34, 7) on ROUTE116 ("a pre-existing message that over-claims 'gone' for 'out of reach'").
  Picking a ball up adds its key to `tried_items` (`goals.py` :3304), so "in `tried_items`" covers picked-up and
  given-up balls alike.

### 2.6 Seeds and disk

- `bp1r2/seeds_free.py 6601-6603 6604-6606 6611-6646 6484-6486 6701-6760 6761-6799 2000000-2999999` at 7:46 PM: "308
  ledgers: main 1, worktrees 11, others 296"; FREE for every range but 6484-6486, which WT's ledger entry #148 (E0-2)
  names. The one unreadable file, as before: `mergeplan/review/exports/s2/ai_player/gates/ledger.json` ("Expecting
  value: line 115 column 1").
- `df -B1 /c` at 8:00 PM: 53,218,197,504 bytes free.
- v3: no ledger entry was added on WT after that check (`fa9f073d` changed only `run_regression_times.json`), and
  PRELANE uses no seeds. Other ledgers were not re-read.
- v4: the scan script is kept, cmp-equal, at `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/bp1r2/seeds_free.py`
  (D3). It also reads the lab's own ledger copies (`_ai_lab/s53/**/ledger.json`), so after the cleanup it scans fewer
  ledgers. WT's HEAD was still `fa9f073d` at 10:17 PM.

### 2.7 Lines that moved at `3caf9c47` (the fix changed 14 files)

`world/memory.py` (45 lines in the fix's diff stat; the later symbols moved +35): `MapMemory.to_dict` :413
(`tile_fields` :417, `bumped` :420, `edges` :426), the warp graph's doc :484, the rides doc :531-537, `record_ride`
:588, `close_ride` :614, `learn_slide` :824 (`slid` :838), `WorldMemory.to_dict` :911 (rides :927), `from_dict` :935
(rides :954). `brain/goals.py` (57 lines in the diff stat): the boss-prep
tells :2200-2590, "the raise ends, budget spent" :2476, "a battle lost on the gym map" :2581, the next-named-fight rule
:2177-2181. Unchanged by the fix: `mode.py` (:460, :1401), `game_memory.py`, `options.py`, `__main__.py`,
`host/launcher.py`, `live_chain.py`, `live_step5.py`, `check_anchors.py`, `test_check_anchors.py`, `test_live_chain.py`.

### 2.8 New since v2 (v3, with v4's updates; each run is one trajectory)

- **`<S3t2>` = `fa9f073d`**, the lead's amendment II-A1 (parent `19e9700c`; `git diff --stat` shows only
  `ai_player/gates/run_regression_times.json`): `revert_step5` 3460 -> 12110, `revert_r1` 1167 -> 4085, `revert_step3`
  2014 -> 7049, `revert_safety_gates` 326 -> 3456 s, because the side branches' own full lanes ran those drivers at or
  over their old caps (`mergeplan/STATE.md` line 260). Its `_doc` calls the side lane's kill times "lower bounds" and
  the rows "upper bounds under load until measured alone". The rows sum to 36,334 s at `19e9700c` and 56,067 s at
  `fa9f073d` (`git show`, read-only); the longest row is `revert_bossprep` 15,931 s at both, so the lane's planned wall,
  4.43 h (the same STATE line), does not move. The merge's full lane runs on `fa9f073d`.
- **PRELANE** (the three mutant drivers that name the fix's files, `revert_step5`, `revert_step3` and `revert_r1`, in
  full on the fix's code `3caf9c47`), DONE (`fix5/STATE.md` lines 103-106, lab; the lead's `mergeplan/STATE.md` line
  of 10:45 PM): all three exit 0 and "OVERALL: PASS", no verdict changed. `revert_step5` "698 mutants CAUGHT as
  predicted, 5 REDUNDANT ALONE as predicted, of 703" (7,783 s, `--workers 3`); `revert_step3` "93 mutants CAUGHT as
  predicted, 1 REDUNDANT ALONE as predicted (each with its reason), of 94" (8,922 s, 1 worker); `revert_r1` "637
  mutants CAUGHT as predicted, 4 REDUNDANT ALONE as predicted, of 642 run (642 defined)" (8,631 s, `--workers 2`). The
  three ran at once, under the tuner's load, so these are not alone-times. No amendment depends on them. They and the
  merge's full lane's seconds are the measured hours A1's build plan reads (section 5, step 0a).
- **Disk (v4: it kept falling).** The newest readings: "C: 47.71 GB free" (`fix5/STATE.md` line 102, 10:13 PM) and
  "Disk: C: 47.95 GB free at 10:00 PM (shutil, decimal; 44.66 GiB), falling about 3 GB an hour while the tuner runs
  (53.2 at 8:10 PM)" (`mergeplan/STATE.md` line 262, the lead's line); `df -B1 /c` (this revision) read
  47,948,328,960 bytes at 10:06 PM and 46,895,435,776 at 10:35 PM (0.16 GB of that drop is v4's own copies into the
  keep folder, 163,444,160 bytes). Two dated readings give the rate: 53.2 GB at 8:10 PM (`fix5/STATE.md` line 96,
  PRELANE's launch: "C: free 53.2 GB") and 47.95 GB at 10:00 PM, so 5.25 GB in 110 minutes, about 2.9 GB an hour on
  average. The fall was uneven: 50.48 GB at 8:53 PM, 48.77 at 9:13 PM, 48.49 at 9:33 PM and 48.22 at 9:53 PM
  (`fix5/STATE.md` lines 98-101), about 5.1 GB an hour from 8:53 to 9:13 PM and about 0.8 from 9:13 to 9:53 PM. The
  tuner and PRELANE both ran throughout; the cause was not checked. 2.7's formula is P_fit = floor((free - 40 - 0.6 -
  0.4 - 2.0) / budget). For A1 (1.25 GB a job) it gives 4 from 48.0 GB, 3 from 46.75 GB and 2 from 45.5 GB. For MC
  (1.75 GB) it gives 3 from 48.25 GB, 2 from 46.5 GB and 1 below that; its 3 chains run min(P, P_fit) at a time (2.7).
  At 47.95 GB: 3 for A1 and 2 for MC. The lead's newest sample, 46.21 GB at 10:50 PM (`mergeplan/out/disk_samples.txt`,
  lab), gives 2 for A1 and 1 for MC. So WP1's "4-5 h at P = 8" holds only if the disk is back near 53 GB; its about 28
  job-hours take at least about 9.3 h at P = 3 and about 14 h at P = 2. **And A1 refuses to start under 45 GB** (2.7,
  D11's floor; MC too): 46.21 GB is 1.21 GB above it. The merge's lab cleanup frees space (its size was not measured).
  Build step 0a re-measures the disk.
- **Battles lost before `ch6_dewford`:** 0 in 8 of 8 runs from C1; their 8 losses (`ab4g-6426` 3, `ab4g-6427` 3,
  `ab4g2-6429` 2) all come after it, and every one is a BRAWLY gym-map loss (`a1prep/tools_v3/loss_order.py`, by log
  line order: the LOST lines carry no frame). The re-check's P2 finding (1.0 C7) says the same.
- **E0 and E0-2 in git:** E0 is ledger #147 (`ai_player/evidence/2026-11-13-chain-heldout-dev-ch5_rival_meet-6481.txt`;
  commit `a90c8e8f` at 8:19 AM, its message "E0 VERDICT: NOT REACHED (1 of 3 reached ch5_rival_meet); legs ran 15,
  purity-clean 15; wall 41 min (cap 120); problems 5 -> STOP"). E0-2 is ledger #148 (section 2.3; commit `19e9700c` at
  7:42 PM). So one STOP cost about 11.4 hours from record to record.
- **The chapter 5 repo note** (`notes/2026-11-13-CH5-SEARCH-LOOP-FIX.md`, fixed in place twice since v2; v4 read its
  10:12 PM version, 26,814 bytes, 12 sections, while its third check ran; it becomes
  `PROJECT KNOWLEDGE/ai-research-notes/2026-11-13-CH5-SEARCH-LOOP-FIX.md`): its section 3 holds the one-frame
  splits and "Cause NOT proven"; section 4 "missed 2 of 3 against 0 of 9 ... (p about 0.045, confounded)"; section 8
  the fix's arms (T L4 fixed "X 1", C L4 fixed "X 0") and CH6 probe-C1's whole-leg frames (609,121 unfixed, 657,908
  fixed); section 10 "long loops in 3 of about 9 merged-code paths against 0 of about 11 main paths: suggestive only".
  The NEW blocks cite those sections in place of lab files.
- **Kept outside the lab.** The lead's ruling (D3): every folder under `_ai_lab/s53/` is lab that the merge's cleanup
  may delete; only `_ai_lab/keep/` is kept (this PC only, not git). The note's fixer kept T's L4 start
  (`end_state.ss1` and `world_last.jsonl`) in `C:/Remote Projects/_ai_lab/keep/2026-11-13-ch5loop-T-L4/`
  (`notes/STATE.md`, 9:06 PM). (v4) `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/` holds, with each file's
  source and sha256 in its README.txt: the lead's copies of about 10:02 PM (E0's three L5 `world_last.jsonl`,
  `row.json` and `ai_player.log`; C_FIX's `actions.jsonl`; `stage_merge.py`, `stage_diag.py`, `replay_leg.py`,
  `compare_moves.py`) and this revision's of about 10:17 PM (the 1.2 Lab kit's four files, `find_junctions.py`, and
  C1-C3's 12 start files, 163,444,160 bytes in all with the kit), each cmp-equal to its source.
- **BP-1's facts in git (v4).** BP-1 round 2's evidence file `ai_player/evidence/2026-11-11-bossprep-bp1r2-live-ab.txt`
  :61-67: ledger #125's C and B decision streams IDENTICAL in 3 of 3 pairs; #127's C2L4 pair split at a map change at
  frame 617,525 ("the game took 11 frames to change maps in B2 and 10 in C"). BP-1 round 4's
  `ai_player/evidence/2026-11-11-bossprep-bp1r4-live.txt`: #131 ab4w, seeds 6414-6416, "the raise SPENT before BRAWLY
  in 3 of 3 (frames 457706, 460630, 450262 of 450000)"; #132 ab4g (6426, 6427) and #133 ab4g2 (6429), "battles 164,
  164, 163 of 160", with 6426 and 6427 ending "stuck: 3 battles lost (MAX_LOSSES 3)". Both files are on
  `wip/ch6-bp1` and in WT at `fa9f073d`, so on `main` after the merge. The per-run L6 frames (2.1), losses (2.2) and
  crossings (2.4) are not in them: they were read from the runs' lab logs.
- **Ledger ids (the lead, after the v4 check).** Every ledger id in this note is the MERGED ledger's
  (`ai_player/gates/ledger.json` at `fa9f073d`, 148 entries). The two BP-1 evidence files above number the same entries
  as on `wip/ch6-bp1`, 6 lower: merged #125 = `wip/ch6-bp1#119`, #127 = #121, #131 = #125, #132 = #126, #133 = #127
  (each merged entry's `was` field names its branch id).

## 3. The amendments (v2, with v3's and v4's changes)

Kinds: **MUST** = the spec is wrong or breaks a ruling or its own rule; fix before the build. **SHOULD** = a gap the
build or its proofs will hit. **NOTE** = a citation or number. Each amendment says what changed from v1; a **v3**
line says what the re-check changed (1.0), and a **v4** line what the delta re-check changed (1.0b).

### AM-01 (MUST) Part 0 (GM): the goal memory a test start carries

**Changed from v1** (the lead's call 2 on R2, R3): the restore is listed field by field; who carries a snapshot is
stated (A1's chain and practice legs yes, MC no); comparisons with #101, E0 and E0-2 name the difference; WP1b gets a
fallback start; the change is carried through every section named; GM's live A/B moves to a chain's chapter-5 end made
by part 0's own code, with a per-tile discriminator (R4). v1's fallback (A1 test-side only, item 4 NOT MET) is
dropped: the lead chose GM. Record fields: AM-23. Tests and mutants: AM-24. `06`: AM-22.

**v3** (1.0 C1, C2, C8, C9, C12): the GOALS-OFF arm's stale measure is read against its start's kept snapshot (3.15
items 5 and 7; AM-23); definition-of-done item 0 asks item 6 before any snapshot and item 7 before WP1 (01-n); part 0
moves the play digest, so MC's first run on the A1 commit must read PASS before WP1 (3.1, new 3.15 item 8); WP1b's
dependency is a per-job SKIP (01-e; AM-07); `starter_from` follows the start's kind, and "a leg after a hard kill" is
no longer listed as a start (01-c, 3.15 item 5). The P11-x citation names the repo path, not WT (3.15 item 6).

**v4** (1.0b D3): 01-c says where C1-C3's files are kept
(`C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/ch5stops/out/probe/`, md5-equal to 2.1's table) and that the
C folders hold the state and `world.jsonl` only; 01-k cites ledger #133 and this note's section 2.2 for the BRAWLY
win on a third try.

**Why.** `06` :10114 (R): "4. The P11 follow-ups: a test start is the emulator state PLUS the AI's world memory PLUS
its goal memory (a requirement added to A1's harness)". No harness can meet it with today's AI code: `--state`
archives the profile's memory file (launcher :205); the launcher sets `AI_PLAYER_MEMORY` itself (`__main__.py` :190);
the play brain refuses an existing memory file outside a continue (`mode.py` :460).

**Evidence (at `3caf9c47`).**
- What a continue restores: `game_memory.py` `GOAL_KEEP` :137-162 (the errand fields `talked`, `tried_items`,
  `item_tries`, `fight_prep`, `pages`, `looked`, `scene_walls`, ...; and R1's `saved_for` :160, `last_save` :161);
  `GOAL_RESET` :164-180; `R1_NEW_FIELDS` :188; `restore_goals` :412; `restore_personality` :424 (another base raises);
  `restore_battle` :441; `build_payload` :447 (world, goals, personality, battle, mons, losses).
- The cartridge at a `--state` start: `__main__.py` :191, `env[ENV_CART] = "continued" if continuing else ("empty" if
  args.fresh or args.state else "kept")`.
- What the save fields do: `brain/saving.py` :150-155 (the gap rule: "its last save was at ..., N game minutes ago");
  :205-209 (`before_leader` takes a `saved_for` entry, or a `last_save` after the gym was entered, as the save before
  the leader). At a `--state` start they would describe a save the empty cartridge does not hold.
- The loss count: `mode.py` :113 `MAX_LOSSES = 3`; :796-797 "(R2, T5) the battles lost so far, as of the save:
  MAX_LOSSES counts across processes; new ones on top"; `_count_losses` :1030-1043. Measured per chain: section 2.2.
- The key reaches the child unchanged: `run_arm` sends `arm.env` (`live_step5.py` :468); `child_env` (launcher
  :775-784) copies the environment minus `UNTRUSTED_ENV` (:116: four `PYTHON*` keys only).
- The play side writes files only through `runlog.py` and the instrument (`check_purity.py` FILE_WRITERS :639-642);
  `memory.jsonl` is written "through `runlog.RecordFile`" (`paths.py` :11).
- `GRADER_GATES` (`live_chain.py` :292-295) holds `check_purity.py`. `revert_step5.py`, also in it, is blob `20c48244`
  at `934ddb7f` and `ad15e8f5` at `3caf9c47` (`git rev-parse`; the merge and the fix both changed it). So the merged
  `main`'s next graded live_chain run re-registers its grader files whether or not part 0 edits `check_purity.py`.
- P11-x's offline repro (WT `PROJECT KNOWLEDGE/ai-research-notes/2026-11-12-P11-X-DETOUR-DIAGNOSIS.md` :51-58):
  `_remembered_ball` returns (17, 7) with a new goal memory and None with `tried_items = {"24:7|17,7"}`.

**The loss count: carried, as the lead ruled.** I looked for a concrete harm and found a measured consequence, not a
harm. Of 9 chapter 1-5 chains, none would have ended a leg early, and 2 (#101's LC-S-6202, E0's LC-T-6483) would enter
chapter 6 with 2 losses, leaving one BRAWLY try; 1 of BP-1 round 4's 4 BRAWLY wins (`ab4g2-6429`) came on its third
try. So A1's "N battles lost" keys at chapter 7 will hold more ends than BP-1 measured from C1 with 0 carried. That is
what the AI does in a continued game (`mode.py` :796), so it is the faithful harness, not a fault. The record keeps
`losses_carried` and the report splits carried from in-leg losses (08-b, AM-23), so "BRAWLY three times" stays
distinguishable from "BRAWLY once after two whiteouts". Rejected: a fresh allowance of 3 per leg (a game that cannot
exist; it would differ from a continue, the very thing D12's leg rule approximates).

**Edit 01-a** (section 0, line 23):

~~~old 01-a
that writes no tracked file, disk caps (KI-129, KI-130).
~~~

~~~new 01-a
that writes no tracked file, disk caps (KI-129, KI-130). **Part 0 (GM, 3.15) is AI-side:** the play brain writes its
  goal memory at every end it controls and restores it at a `--state` start, so A1's test starts carry the emulator
  state, the world memory and the goal memory (`06` 2026-11-12 item 4).
~~~

**Edit 01-b** (1.3, line 72; it also carries AM-03's D7 change):

~~~old 01-b
| §6 Q1; D2, D3, D4, D7, D12, D16 | **Hold** (Q1 = USER RULING 55). D3 also excludes the harness-placed I1, D1, D2 (2.1); D7 takes the LEG's chapter; D12 is `run_chain`'s. |
~~~

~~~new 01-b
| §6 Q1; D2, D3, D4, D16 | **Hold** (Q1 = USER RULING 55). D3 also excludes the harness-placed I1, D1, D2 (2.1). |
| D7, D12 | **Changed** (for `06`, 4.4 item 8). D7 takes the LEG's chapter, and a leg that ends inside a long map-pair loop gets ONE LOOP key whatever its next milestone, class or end map (3.8). D12 stays `run_chain`'s leg rule, but every leg A1 starts from a kept state also carries the kept goal snapshot (part 0, GM, 3.15); the profile's `memory.jsonl` is still archived per leg. |
~~~

**Edit 01-c** (2.1, after the Excluded bullet, line 106):

~~~old 01-c
  `legs_of` refuses an optional target); C1L4 and C2L4 (chapter-4 ends the chains cover).
~~~

~~~new 01-c
  `legs_of` refuses an optional target); C1L4 and C2L4 (chapter-4 ends the chains cover).
- **Goal memory (part 0, GM, 3.15).** None of G1-G6 or C1-C3 holds a goal snapshot (G1-G6's folders keep the state,
  the world line and the logs; C1-C3's the state and `world.jsonl`), so a job started from one is labelled
  `goal_memory: none` and counted apart. WP1b's practice starts are WP1a's own `ch5_rival_meet` ends (2.4: the same
  tree, all 9 pairs, snapshots carried). A pair whose WP1a chain ENDS without a reached L5 (it stopped before L5, or its
  L5 missed `ch5_rival_meet`) uses its persona's next unused G start (Story G1, G2; Catcher G3, G4; Trainer G5, G6;
  then C1-C3), with that start's own starter (`starter_from: job_file` for a G start, `truth_party` for a C start, as
  above), labelled `goal_memory: none` and `fallback_for: <pair>`, and counted apart, so chapters 6-7 are never left
  unmeasured.
- **Where the C starts are kept.** `_ai_lab/s53/` is lab that the merge's cleanup may delete. C1-C3's files (the
  table's `end_state.ss1` and `world.jsonl`, with `probe-C*.job.json` and `probe-C*.json`) are kept, md5-equal to the
  table, in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/ch5stops/out/probe/` (sha256 in the keep folder's
  root `README.txt`; this PC only, not git). G1-G6 stay in `C:/Remote Projects/_livechain/graded-ch5`, outside the lab.
~~~

**Edit 01-d** (2.4's table, the WP1 row, line 144; AM-05's 05-a changes the P1 row above it):

~~~old 01-d
| **WP1**, the wide probe | after the merge | **J-N:** 9 chains, one per pair, L1-L7. **J-F:** 27 practice jobs, G1-G6 and C1-C3 × 3 seeds, L6-L7. **P2:** arm WALL-BRINEY on the first-seed J-F jobs of G1, G3, G5 (one per persona), L6 only | 39 jobs, at most 9×7 + 27×2 + 3 = 120 legs |
~~~

~~~new 01-d
| **GM**, part 0's live A/B (3.15 item 7) | after A1's runner exists, beside P1 | one diagonal New Game chain L1-L5 with GM (it makes the start), then arms GOALS-ON and GOALS-OFF from its L5 end on 2 seeds, L6 | 5 jobs, at most 9 legs |
| **WP1a**, the wide probe's chains | after the merge and GM | **J-N:** 9 chains, one per pair, L1-L7, each leg carrying the goal snapshot | 9 jobs, at most 9×7 = 63 legs |
| **WP1b**, practice and the cottage wall | as each WP1a chain's L5 ends | **J-F:** 27 practice jobs, WP1a's 9 `ch5_rival_meet` ends × 3 seeds, L6-L7, snapshots carried (a pair whose chain missed: the fallback start of 2.1, counted apart). **P2:** arm WALL-BRINEY on the first-seed J-F job of each diagonal pair (one per persona), L6 only | 30 jobs, at most 27×2 + 3 = 57 legs |
~~~

**Edit 01-e** (2.4, the Order sentence, line 149):

~~~old 01-e
 **Order:** J-N chains, then J-F interleaved by start, then P2.
~~~

~~~new 01-e

  **Order:** GM's chain and A/B (part 0's live proof), then WP1 as ONE batch (one ledger entry, seeds 6611-6646, one
  prediction file): WP1a's 9 chains first, then J-F interleaved by start, then P2. A WP1b job is SKIPPED (3.13: it keeps
  its place, and the ready jobs behind it launch) until its source chain's reached L5 record exists; when that chain
  ENDS without one, the job takes its fallback start at once (2.1). **Who carries a goal snapshot:** every A1 leg
  started from a kept state, except MC's (2.4b, E0's harness), GM's GOALS-OFF arm (3.15 item 7) and the labelled
  `goal_memory: none` starts. Any A1 number set beside #101, E0 or E0-2 (none of which carried one) names that
  difference or uses a labelled no-GM arm.
~~~

**Edit 01-f** (3.1, the NOT CHANGED line, line 204):

~~~old 01-f
`live_step5.py`, `launcher.py`, `ledger.py`, AI play code, `ai-agent/*`.
~~~

~~~new 01-f
`live_step5.py`, `launcher.py`, `ledger.py`, `ai-agent/*`. **AI play code changes
  ONLY in part 0 (GM, 3.15)**, AI-side and under its own proofs: `mode.py`, `game_memory.py`, `options.py` (the new
  `AI_PLAYER_GOALS`), the launcher side's `__main__.py` (its `--continue` refusal), their tests, and `check_purity.py`
  only if the build finds a pinned list that needs it (3.15 item 4). **So part 0 moves the play digest:** A1's live
  runs play code that E0-2 (ledger #148, on `3caf9c47`) never ran, and "a play change now would need a new live round"
  (`06` :10104). MC's first run, on the A1 commit's stage, is that round (3.15 item 8).
~~~

**Edit 01-g** (3.4 step 4, line 262):

~~~old 01-g
the `Arm` (fresh, the previous leg, or `"START"` in `carried`); `run_arm`;
~~~

~~~new 01-g
the `Arm` (fresh, the previous leg, or `"START"` in `carried`; its `env`
   carries `AI_PLAYER_GOALS` = the kept goal snapshot when the leg carries one, 3.15); `run_arm`;
~~~

**Edit 01-h** (3.6, C5, line 295):

~~~old 01-h
its `world_in` sha256 the kept line's, the env keys the allow-list);
~~~

~~~new 01-h
its `world_in` sha256 the kept line's, its goal snapshot's sha256 the kept
`goals_last.jsonl`'s when one is carried (part 0), the env keys the allow-list);
~~~

**Edit 01-i** (3.6, the T27 sentence, line 298):

~~~old 01-i
T27 asserts that cap is the only difference.
~~~

~~~new 01-i
T27 asserts the two differences: that cap, and the goal snapshot an
A1 leg carries (part 0). The one exception is MC: an MC job decides by `continue_after` itself (2.4b), its New Game
chains being the case that C5 assumes.
~~~

**Edit 01-j** (3.11, line 392):

~~~old 01-j
`AI_PLAYER_MEMORY` :245 and `AI_PLAYER_CONTINUE` :247 are unused: A1 never continues a game (D12).
~~~

~~~new 01-j
Part 0 adds an eighth key, `AI_PLAYER_GOALS` (its `options.py` line is new, beside `ENV_WORLD` :189): the
  kept goal snapshot, only on a leg that carries one (3.15), checked in custody by sha256 (C5); an MC job never sends
  it. `AI_PLAYER_CONTINUE` :247 is unused: A1 never continues a game (D12). `AI_PLAYER_MEMORY` :245 is never a job key:
  the launcher sets it itself (`__main__.py` :190), and `--state` archives the profile's memory file first (launcher
  :205), so without part 0 every `--state` leg begins a new goal memory. Every leg record states
  `start_memory.goal_memory`.
~~~

**Edit 01-k** (new 3.15, inserted before section 4, line 433):

~~~old 01-k
## 4. Tests and proof
~~~

~~~new 01-k
### 3.15 Part 0 (GM): the goal memory a test start carries

`06` 2026-11-12 item 4 makes a test start "the emulator state PLUS the AI's world memory PLUS its goal memory". No
harness can give the third today: `--state` archives the profile's memory file (launcher :205), the launcher sets
`AI_PLAYER_MEMORY` itself (`__main__.py` :190), and the play brain refuses an existing memory file outside a continue
(`mode.py` :460). So part 0 is AI-side code, built and proven BEFORE A1's runner relies on it. Lines are at `3caf9c47`.

1. **The end snapshot.** At every end the play brain controls (`done`, `stuck`, `stopped`, the soft deadline) it appends
   ONE line to `<run_dir>/goals.jsonl` through `runlog.RecordFile` (the play side writes files only through `runlog.py`
   and the instrument, `check_purity.py` FILE_WRITERS :639-642): the save payload without its world (`game_memory.py`
   `build_payload` :447: `goals_part`, the personality, the battle mind, the registry, the loss count). A hard kill, or
   the probe's CUT-WORLD kill, leaves none; such a leg never continues (3.6 C2). The leg's end keeps the line as
   `goals_last.jsonl` beside `world_last.jsonl`.
2. **The restore, at a `--state` start given `AI_PLAYER_GOALS`** (a new `options.py` key beside `ENV_WORLD` :189):
   - RESTORED, as a continue restores them: every `GOAL_KEEP` field (`game_memory.py` :137-162: `tried_items`,
     `talked`, `pages`, `looked`, `scene_walls`, `fight_prep`, ...) except the two below; the personality
     (`restore_personality` :424: base, favourite, history, draws; another base is refused); the battle mind
     (`restore_battle` :441); the Pokemon registry (`MonRegistry`).
   - RESET: `GOAL_RESET` (:164-180), as in a continue; and R1's save fields `last_save` and `saved_for` (:160-161,
     `R1_NEW_FIELDS` :188). A `--state` start empties the cartridge (`__main__.py` :191: cart `empty`), so there is no
     AI save to remember; kept, they would make the save policy skip a due save for a save that is not there
     (`brain/saving.py` :150-155, the gap rule; :205-209, `before_leader`).
   - CARRIED: the loss count. One game has one loss count, as a continue keeps it (`mode.py` :796-797: "MAX_LOSSES
     counts across processes; new ones on top"). Each leg records `losses_carried`, and the report splits carried from
     in-leg losses (3.7, 3.8). Measured (one trajectory per chain): of 9 chapter 1-5 chains none would have ended a leg
     early, 2 would enter chapter 6 with 2 losses (#101's LC-S-6202, E0's LC-T-6483), and 1 of BP-1 round 4's 4 BRAWLY
     wins (`ab4g2-B4-C1-6429`, ledger #133) came on its third try (counted in the repo note
     `2026-11-13-A1-SPEC-AMENDMENTS.md`, section 2.2). A1's BRAWLY numbers are therefore not BP-1's (0 carried, from
     C1): any comparison names this.
   - The world memory still comes only from `AI_PLAYER_WORLD`; the snapshot holds none.
   - REFUSED before play: `AI_PLAYER_GOALS` with `--continue` (D19's rule, as for `ENV_WORLD`: `options.py` :414-418,
     `__main__.py` :157-159), without `AI_PLAYER_WORLD`, or a file that is not one parseable line.
3. **Launcher side.** `child_env` (launcher :775-784) already passes every `AI_PLAYER_*` key (`UNTRUSTED_ENV` :116
   names only `PYTHON*` keys). Part 0 adds only the `--continue` refusal to `__main__.py`, a `LAUNCHER_FILES` file
   (`check_purity.py` :171).
4. **Purity and the graded driver.** If the build finds `check_purity.py` needs an edit (a pinned env name or writer
   list), that edit is part 0's, and live_chain's next graded run re-registers its grader files (`GRADER_GATES`
   :292-295 holds `check_purity.py`). The merge forces that re-registration anyway: `revert_step5.py`, also in
   `GRADER_GATES`, differs between `934ddb7f` and `3caf9c47` (blobs `20c48244` and `ad15e8f5`).
5. **Who carries a snapshot.** Every A1 leg started from a kept state carries the previous leg's (or the start's) kept
   snapshot (`start_memory.goal_memory: carried`). A start with none (G1-G6, C1-C3) runs with `goal_memory: none`,
   labelled and counted apart; a leg after a hard kill never runs (item 1). GM's GOALS-OFF arm (item 7) also runs with
   `goal_memory: none`, from a start that has one: that kept snapshot is still the yardstick of its stale errands
   (`measures.stale`, 3.7). MC never carries one (2.4b).
6. **Offline proofs, before any live run** (each with a mutant, 4.2): the P11-x repro as FAULT and CONTROL
   (`ai-research-notes/2026-11-12-P11-X-DETOUR-DIAGNOSIS.md` :51-58, beside this spec after the merge:
   `_remembered_ball` gives (17, 7) with a new goal memory and None with `tried_items = {"24:7|17,7"}`), so the restore
   switched off gives (17, 7) and on gives None; `last_save` and `saved_for` planted in a snapshot are absent after a
   `--state` restore and kept by a continue; a snapshot with 2 losses ends the run at its first new loss (MAX_LOSSES
   3); each refusal of item 2; the end line written at each end the brain controls and absent after a hard kill
   (stub). The purity gate, the quick gates and the DUE suites green.
7. **Live A/B** (after A1's runner exists, beside P1; plan `GM`, seeds 6604-6606). One diagonal New Game chain L1-L5 on
   seed 6604 makes the start. BEFORE any A/B launch the per-tile discriminator is computed offline on its L5 end: the
   tiles of the end snapshot's `tried_items` that are remembered item tiles (`MapMemory.items`) of a map the next leg
   starts on or crosses early (RUSTBORO_CITY, ROUTE116, ROUTE104), that is, tiles `_remembered_ball` offers with a new
   goal memory and not with the snapshot. With at least one, arms GOALS-ON and GOALS-OFF run L6 from that end on seeds
   6605 and 6606 (paired). The measure is `measures.stale.item_errands` (3.7), per tile, counted in BOTH arms against
   their common start's kept `goals_last.jsonl` (GOALS-ON carries it; GOALS-OFF keeps it but does not carry it):
   predicted 0 in every GOALS-ON leg and at least 1 in every GOALS-OFF leg. With none, the A/B is VACUOUS, is not run,
   and is reported so; the chain's earlier leg ends are tried the same way; with none anywhere, part 0 rests on item 6
   plus the live custody records, named as such.
8. **The play digest moves.** Part 0 is play code, so the A1 commit's play digest differs from that of the tree E0-2
   ran (ledger #148: `3caf9c47`), and "a play change now would need a new live round" (`06` :10104). That round is
   MC's first run (2.4b; build step 6): on the A1 commit's stage, it MUST read PASS before WP1. On every later merge MC
   runs as 2.4b says.

## 4. Tests and proof
~~~

**Edit 01-l** (T9, line 452):

~~~old 01-l
the 7 keys arrive; the command line byte-identical
~~~

~~~new 01-l
the 8 keys arrive (`AI_PLAYER_GOALS` only on a leg that carries a snapshot, never on an MC job); the command line byte-identical
~~~

**Edit 01-m** (T27, line 470):

~~~old 01-m
| T27 | graded-driver agreement | the known divergence, asserted: a reached, clean leg with a 500,000,000-byte world continues here, stops in `continue_after` (C3), record says why | worlds under 300 MB: `reached` and the decision equal `leg_reached` and `continue_after`, leg by leg |
~~~

~~~new 01-m
| T27 | graded-driver agreement | the known divergences, asserted: a reached, clean leg with a 500,000,000-byte world continues here, stops in `continue_after` (C3), record says why; a leg that carries a goal snapshot records `goal_memory: carried`, which `continue_after` never sends | worlds under 300 MB: `reached` and the decision equal `leg_reached` and `continue_after`, leg by leg; an MC job (2.4b) STOPS at the 500,000,000-byte leg exactly as `continue_after` does, and sends no `AI_PLAYER_GOALS` |
~~~

**Edit 01-n** (4.4, before item 1, line 523):

~~~old 01-n
1. The offline suite green; the mutants CAUGHT as predicted.
~~~

~~~new 01-n
0. Part 0 (GM): its offline proofs (3.15 item 6) pass before any A1 leg carries a snapshot, and its live
A/B (3.15 item 7) passes before WP1. 1. The offline suite green; the mutants CAUGHT as
predicted.
~~~

**Edit 01-o** (4.4 item 6, line 525):

~~~old 01-o
6. WP1 ran; its chapters 1-7 blocker report with examples is in the evidence.
~~~

~~~new 01-o
6. WP1 ran (WP1a, then WP1b, 2.4); its chapters 1-7 blocker report with examples is in the
evidence, reach split by start kind (3.8).
~~~

### AM-02 (MUST) 2.4, 4.3 P1(c), 6.3 risk 9, 1.1: one seed is not one trajectory

**Changed from v1:** the old texts are now exact (R9); "host load may move it (suggestive)" (R14); the `06` reason
correction the review asked for is AM-22 item (vi) (R8). The substance stands. **v4** (1.0b D3): 02-b cites BP-1
round 2's committed evidence (`ai_player/evidence/2026-11-11-bossprep-bp1r2-live-ab.txt` :61-67) instead of a lab
STATE.md line. That file shows both cases: #125's streams IDENTICAL in 3 of 3 pairs, and #127's C2L4 pair split by
one frame at a map change (frame 617,525). So 02-b now says a split need not happen, and it can.

**Why.** The spec rests a design choice and a reported prediction on "the clock is pinned". The cartridge reads the
host's time, and E0 measured one-frame splits on the merged code.

**Evidence.** `live_step5.py` :142 ("the cartridge's own clock reads the HOST's time in a launcher run"), :409 ("each a
NEW trajectory on the host's clock: a sample, not a replay"); design :354 (risk 9); `e0diag/DIAGNOSIS.md` :89-90 (E0
"557997 watch busy 18f" against the replay's "557998 watch busy 19f"), :102-104 ("a single run from a saved start is a
SAMPLE, not a verdict"), :307 (the RTC cause unproven); `REFUTE.md` :247-248; `shadow/SHADOW.md` :83 ("What this
suggests", 2 runs against 3); `mergeplan/STATE.md` line 198 ("THE GAME IS NOT DETERMINISTIC").

~~~old 02-a
**3 seeds per start:** the clock is pinned (`ENV_CLOCK` "10:00", `live_step5.py` :143), so one start on one seed is
  one trajectory replayed (CLAUDE.md rule 8).
~~~

~~~new 02-a
**3 seeds per start, all distinct:** `ENV_CLOCK` "10:00" (`live_step5.py` :143) is the wall clock the AI SETS
  in its room; the cartridge's own clock reads the host's time in a launcher run (:142; design risk 9). Measured on the
  merged code (E0; the repo note `2026-11-13-CH5-SEARCH-LOOP-FIX.md` section 3, beside this spec): the same code, saved
  start, seed and environment, with fresh profiles, replay move for move and then split by ONE frame at a warp onto an
  outdoor map, at a point no one can predict (the cause is suspected, not proven: "Cause NOT proven", that section);
  host load may move it (suggestive only: `e0diag/shadow/SHADOW.md` :83-84, 2 runs against 3; lab, deleted after the
  merge). So a rerun on one seed is a correlated near-replay, never an independent sample and never a replication
  (CLAUDE.md rule 8): identical results are a determinism check only, and a different result on the same seed is not
  evidence of a code difference. Seeds are spent per start and never repeated to sample it.
~~~

~~~old 02-b
- **(c) Reported:** with the pinned clock the paired arms replay identically until the wall bites (BP-1 round 2's C and
  B decision streams were IDENTICAL in 3 of 3 pairs, `bp1r2/STATE.md` 08:22); the first differing decision record
  should name an OLDALE plan or step.
~~~

~~~new 02-b
- **(c) Reported:** paired arms on one seed replay until the FIRST of: the wall biting, or the game's own one-frame
  split at a warp onto an outdoor map (E0). The report says which came first. A `[watch] busy Nf` record that differs
  by one frame at a warp is a game split; an AI decision record naming an OLDALE plan or step is the wall. BP-1 round 2
  saw both (`ai_player/evidence/2026-11-11-bossprep-bp1r2-live-ab.txt` :61-67, which numbers them #119 and #121 as on
  `wip/ch6-bp1`): ledger #125's C and B decision
  streams were IDENTICAL in 3 of 3 pairs, and #127's C2L4 pair split at a map change at frame 617,525 (11 frames
  against 10), its next AI decisions the same one frame later. So a split need not happen, and it can. (c) never
  decides (a) or (b).
~~~

~~~old 02-c
9. **Determinism:** paired arms on one seed replay;
   identical results are a determinism check, never a replication. 10. **Junctions:** a promotion or merge touching
~~~

~~~new 02-c
9. **Determinism (measured 2026-11-13):** the game is
   not fully deterministic under the launcher (a one-frame split at an outdoor warp; host-time RTC suspected, not
   proven). Identical results are a determinism check, never a replication. An example reproduces the REGION of a
   stop, not its path. A stop is diagnosed by an A/B on its own saved start (E0's method), never by re-rolling seeds.
   10. **Junctions:** a promotion or merge touching
~~~

~~~old 02-d
enough to
   replay the stop through the launcher). The next skill build takes the top entry. Seen in development (never a rate):
~~~

~~~new 02-d
enough to
   start the stop's region again through the launcher: one more trajectory, 2.4). The next skill build takes the top
   entry. Seen in development (never a rate):
~~~

### AM-03 (MUST) 3.8, 4.1 (T6, T8), 1.3 (D7): loop legs are one blocker, not noise

**Changed from v1** (the lead's call 3, R6, M8): T6 scoped to non-LOOP legs (03-c); 1.3's D7 row "Changed" (in 01-b);
P1(b), P2's CONTROL and T8 read records under LOOP keys (12-c, 12-d, 03-d); LOOP keys are filed at 1 run (AM-22); the
AI's own `stuck: ping-pong` goal ends are counted (AM-23); `crossings_raise` counts crossings during an ACTIVE raise
goal, between its `goal` and `goal_end` records. T31 is in AM-24; mutants in AM-24; `06` in AM-22.

**v3** (1.0 C4, C3, C14d; the lead's call 4): **no departure.** The review asked to apply the override "only when the
loop's window runs into the leg's end". v2 replaced that with a window-share rule (4a) beside an end-proximity rule
(4b), saying E0 forced it. It did not: E0 T L5's last crossing came 92,013 frames before its budget end (it escaped the
loop, beat the grunt at f1257345, DIAGNOSIS :145, and ran out on `ch5_return_goods`), which is inside (4b)'s 120,000
frames (`STORY_PATIENCE`, `mode.py` :112); E0 C's came 20 frames before its end. So the review's rule, read with that
tolerance, keys both E0 legs as one LOOP key, and v3 drops (4a): no measured leg needed it, and it alone could key a
loop that ended long before a later, different end (the review's concern). A battle-loss stop, a wedge or a crash
still keeps its own key, flagged. A raise still ACTIVE at the end now comes first, stated as condition (5) (T36's
"never LOOP" had no rule behind it in 3.8). T31 gets rows at both remaining boundaries (40 crossings; 120,000 frames).
**v4** (1.0b D3, D7): 03-b names `ab4g-6426` and `-6427`'s ledger entry (#132) and this note's section 2.4 for the
counts; 2.4's STRICT-rule sentence is corrected (a tolerance of a few dozen frames, not the leg's end itself).

**Why.** E0's two misses were one blocker (a ping-pong between PETALBURG_WOODS and ROUTE104 while the AI searched for
RUSTURF TUNNEL), but 3.8's key splits them by next milestone, end map and class, each with 1 run, below 4.4's "at least
2 runs". `live_ki128.edge_window` (:455-483) counts edges only; E0's loops went through warps.

**Evidence.** Section 2.4. E0's kept rows (v1, `a1prep/tools/next_unmet_e0.py`): LC-T-6483 L5 "next unmet
ch5_return_goods; end map [0, 31]", CLEAN-BUDGET; LC-C-6482 L5 "next unmet ch5_rusturf_grunt; end map [0, 19]",
CLEAN-CHOSEN "stuck: no progress". Spec :526: "a KI for each new blocker holding at least 2 runs".

~~~old 03-a
**The key:** `(leg chapter, next_unmet, reason_norm, end_map_const, class)`.
~~~

~~~new 03-a
**The key:** `(leg chapter, next_unmet, reason_norm, end_map_const, class)`, or the LOOP key
  (below).
~~~

~~~old 03-b
- **Ranking** per (`tree.play_digest`, chapter) on the exact key;
~~~

~~~new 03-b
- **The loop signature** (every leg; from the kept `world_last.jsonl`, read as JSON with no AI import): its
  `transitions` (`[frame, source, target, how, by, tile, arrival, direction]`, `WorldMemory.to_dict` :916-917 at
  `3caf9c47`) newer than the start truth's frame (a carried prefix is the previous kept line's list). Per unordered map
  pair, count the crossings either way, edges and warps alike, maps named by the snapshot's `maps[key].const`.
  `crossings_raise` counts the crossings made while a `raise` goal is ACTIVE (after its `goal` record in
  `actions.jsonl`, before its `goal_end`). `measures.loop` (3.7) keeps the top pair, its window and the AI's own
  `stuck: ping-pong` goal ends.
- **The LOOP key (D7 changed):** `(leg chapter, "-", "loop", "<A>|<B>", "LOOP")`, A and B the top pair's map
  constants, sorted. It replaces the key above when ALL hold: (1) not reached; (2) the crossings less
  `crossings_raise` reach `LOOP_MIN_CROSSINGS` (40, both directions); (3) an end where time or space ran out:
  CLEAN-BUDGET, CLEAN-CHOSEN whose `reason_norm` begins `play: stuck: no progress`, or CUT-WORLD; (4) the loop runs
  into the leg's end: its last crossing lies at most `LOOP_END_FRAMES` (120,000 = `STORY_PATIENCE`, `mode.py` :112)
  frames before the leg's end; (5) no `raise` goal is ACTIVE at the leg's end (the raise comes first: such a leg keeps
  its own key, on a CLEAN-BUDGET end with the reason `budget: a boss-prep raise still active`, above). A leg that meets
  (1) and (2) but fails (3), (4) or (5) keeps its own key, its record says `measures.loop.keyed: "flag"`, and the
  report lists it in a "loops seen" table beside that key, so a different, discrete end (a battle-loss stop, a wedge, a
  crash), or a loop that ended long before a later end, is never hidden. LOOP is a key label, never a D14 class: the
  stop logic is unchanged, and the record keeps all five raw key values. Calibrated on E0's two loop legs (118 and 74
  crossings; last crossings 92,013 and 20 frames before their ends; their window shares, 0.60 and 0.82, are reported,
  never a rule); the other not-reached legs measured had 5 and 6 (BP-1 round 4's `ab4g-6426` and `-6427`, ledger
  #132), and BP-1's reached raise runs at most 20, 10 of them during a raise (the counts: the repo note
  `2026-11-13-A1-SPEC-AMENDMENTS.md`, section 2.4). Both constants are pre-registered in the prediction file.
- **Churn:** a REACHED leg with `crossings - crossings_raise >= 40` goes in a "churn" table (count, frames in its
  window), never ranked (E0-2's T L3 reached with 92 crossings).
- **No live loop kill:** a leg runs to its own end (USER RULING 55; E0 T escaped its loop and beat the grunt).
- **Ranking** per (`tree.play_digest`, chapter) on the exact key;
~~~

~~~old 03-c
| T6 | clustering | one reason, other numbers: ONE key | other next milestone, class or end map: TWO |
~~~

~~~new 03-c
| T6 | clustering | one reason, other numbers: ONE key; two LOOP legs on one pair with other next milestones, classes (CLEAN-BUDGET, and CLEAN-CHOSEN `stuck: no progress`) and end maps: ONE LOOP key, count 2 | non-LOOP legs with another next milestone, class or end map: TWO |
~~~

~~~old 03-d
| T8 | ranking | two trees: the planted wall first on its own, absent on the other; INFRA, REFUSED, NOT CLEAN never in the denominator | no blocker: empty list, excluded counts shown |
~~~

~~~new 03-d
| T8 | ranking | two trees: the planted wall first on its own, absent on the other, its legs read by their records' `next_unmet` under their own key or a LOOP key alike; INFRA, REFUSED, NOT CLEAN never in the denominator | no blocker: empty list, excluded counts shown; a tree whose only LOOP key's records never name the wall's milestone shows no wall |
~~~

### AM-04 (MUST) 3.9, T16: the experience allow-list on the merged memory

**Changed from v1:** the old texts are exact and the whole static-facts paragraph is one edit (R9); memory.py is cited
by symbol with lines at `3caf9c47`, re-read at build step 0a (R14); an unknown ride or bump key is dropped AND listed,
with T16 cases (R14); T16 also gets the K1 CONTROL (AM-20) and a real merged-memory CONTROL (R5). **v3** (1.0 C10):
`learn_slide` is :824-840 (it ends at :840, "return info"), not :824-842.

**Why.** The merged snapshot carries `rides` with per-game counters and `bumped` entries with `slid`. As written,
`rides` passes whole (F20's uneven filtering again) and `slid` is unspecified; failing closed on `slid` would make WP1's
control "experience `unclassified` empty" miss on a known key. L7 crosses GRANITE CAVE's muddy slope.

**Evidence (at `3caf9c47`).** The rides doc (`world/memory.py` :531-537): "from", "to", "arrival", "who", "gfx",
"tile", "words", "place", "via", "first", "last", "uses", "closed". `record_ride` :588-598 (`kept["uses"] += 1`,
`kept["last"] = ride.get("frame")`, the ride's own `frame` not kept); `close_ride` :614-619; the ride record
`brain/rides.py` :176-178 (from, to, arrival, who, gfx, tile, words, place, via, frame). `learn_slide` :824-840
(`info["slid"] = True` :838). `WorldMemory.to_dict` :911 (rides :927).

~~~old 04-a
**Static facts by ALLOW-LIST**, from the leg's kept `world_last.jsonl` (the `WorldMemory.to_dict` snapshot,
`ai_player/world/memory.py` :801-816), read as JSON with no AI import:
- **World:** `warps` as `{key: {to, arrival, direction, inferred}}`, dropping `uses`, `first`, `last`, `by` (:666-676,
  :712-714); `connections` as `{source, target, direction, from, arrival, offset}`, dropping `by`, `frame` (:689-690),
  de-duplicated; `landmarks`; `rides` (on `wip/ch6-ch7` only, :892 there).
- **Per map** (`MapMemory.to_dict` :375-389): `key`, `name`, `const`, `tile_fields`; `tiles` with only the first 4 of
  the 7 compact fields (flags, ledge, elevation, behavior: `TileFact.compact` :214-217), never `seen_frame` or
  `seen_from`; the 7 names are hard-coded, and a map whose `tile_fields` (:379-380) differs is dropped and listed in
  `unclassified` (fail closed); `edges` (:859-861); `bumped` as `{tile|direction: {from, direction}}`, dropping `first`,
  `last`, `bumps` (:725-727).
~~~

~~~new 04-a
**Static facts by ALLOW-LIST**, from the leg's kept `world_last.jsonl` (the `WorldMemory.to_dict` snapshot,
`ai_player/world/memory.py`), read as JSON with no AI import. The symbols are the citation; lines are given at
`3caf9c47` (the merged tree with the chapter-5 fix) and re-read at the final head before the build:
- **World:** `warps` as `{key: {to, arrival, direction, inferred}}`, dropping `uses`, `first`, `last`, `by` (the warp
  graph's doc :484; written :745-746, :755, :792); `connections` as `{source, target, direction, from, arrival, offset}`,
  dropping `by`, `frame`, de-duplicated; `landmarks`; `rides` as
  `{name: {from, to, arrival, who, gfx, tile, words, place, via}}`, dropping the per-game `first`, `last`, `uses` and
  `closed` (`record_ride` :588-598, `close_ride` :614-619; `brain/rides.py` :176-178 records the ride, whose `frame`
  `record_ride` does not keep); any other ride key is dropped AND listed in `unclassified`.
- **Per map** (`MapMemory.to_dict` :413): `key`, `name`, `const`, `tile_fields`; `tiles` with only the first 4 of
  the 7 compact fields (flags, ledge, elevation, behavior: `TileFact.compact` :216), never `seen_frame` or
  `seen_from`; the 7 names are hard-coded, and a map whose `tile_fields` (:417) differs is dropped and listed in
  `unclassified` (fail closed); `edges` (:426); `bumped` as `{tile|direction: {from, direction, slid}}`, `slid` only
  when present (a muddy slope that slides the player back, a static map fact: `learn_slide` :824-840), dropping
  `first`, `last`, `bumps` (:257, :420); any other bump key is dropped AND listed.
~~~

~~~old 04-b
| T16 | experience filter | `visits`, `items`, `people`, `persons`, `met`, `closed`, `arrivals`, `transitions`, `news`, `heard`, `news_log`, `spoke`, warps' `uses/first/last/by`, connections' `by/frame`: absent; planted `rng_state`: dropped AND listed; other `tile_fields`: dropped, listed | allowed keys pass; tiles have 4 fields |
~~~

~~~new 04-b
| T16 | experience filter | `visits`, `items`, `people`, `persons`, `met`, `closed`, `arrivals`, `transitions`, `news`, `heard`, `news_log`, `spoke`, warps' `uses/first/last/by`, connections' `by/frame`, rides' `first/last/uses/closed`, bumped's `first/last/bumps`: absent; planted `rng_state`, a planted unknown ride key and a planted unknown bump key: dropped AND listed; other `tile_fields`: dropped, listed | allowed keys pass (rides' 9 static fields; `slid` kept); tiles have 4 fields; the merged tree's real fixture `gates/fixtures/ch5loop_tcap.world.jsonl` (4 maps of the AI's own memory) extracts with `unclassified` empty; a K1 tell ("... a seasoned player's knowledge: ...") before a battle record is never read as the fight's foe, and alone makes no fight |
~~~

### AM-05 (SHOULD; v1 said MUST) 2.4, new 2.4b, 3.2, 4.4: the merge check, so that E0 can retire

**Changed from v1** (the lead's call 4, R11, R2): SHOULD, because `06` :10135 is a condition for retiring E0, not a
requirement on A1, and the spec breaks no ruling; MC stays E0's harness exactly (no goal snapshot; live_chain's own
continue rule and world guard); a seed rule per merge; the false-STOP rate stated, with p UNKNOWN; one STOP's measured
cost.

**v3** (1.0 C5, C8; the lead's calls 5 and 8): "exactly" is made true: an MC job's world cut is live_chain's
`GUARD_WORLD_BYTES` (1.5 GB), never A1's 1 GB, and its profile budget, 1.75 GB, sits above that cut (3.12, 3.13, T14,
T33). MC's FIRST run is on the A1 commit's stage and MUST read PASS before WP1, because part 0 moves the play digest
(3.15 item 8); MC stays a SHOULD on later merges. The NEW block's lab citations are replaced by git sources.

**v4** (1.0b D3, D4): the seeds bullet cites A1's own seed check (2.5; 3.10, before the first launch, not v3's "at
`plan` time") and this note's section 2.6 for the 7:46 PM reading, not `bp1r2/seeds_free.py`. MC's 1.5 GB cut now
also reaches 2.7's per-leg line and 3.5's CUT-WORLD row (07-i, 07-j). At the disk's newest reading MC's P_fit is 1
(46.21 GB, 10:50 PM; 2 from 46.5 GB), under its P = 3 (2.8).

**Evidence.** `06` :10127 ("A CHAPTER 1-5 CHECK BEFORE THE LANE (step E0) ... a check for a hard break ... NEVER a rate:
one trajectory per seed. 3 of 3 with every purity check passing: go on. Any miss: stop"); :10135 ("Item 4 is a
one-time bridge: it stops being needed when A1's frontier probe covers chapters 1 to 5 on every merge"). E0: 1 of 3 on
`c25d2c40` (wall 41 min); E0-2: 3 of 3 on `3caf9c47` (wall 31 min), section 2.3. `live_chain.py` `JOB_ORDER_3` :159,
`GUARD_WORLD_BYTES` :178. E0's STOP and E0-2's GO: `mergeplan/STATE.md` lines 195 and 256.

~~~old 05-a
| **P1**, the planted-wall proof | can run on `main`'s code (5) | arms REAL and WALL-OLDALE (4.3), the 3 diagonal New Game chains each, the SAME 3 seeds in both arms | L1-L2, at most 12 legs |
~~~

~~~new 05-a
| **P1**, the planted-wall proof | on the merged `main`, after GM's offline proofs | arms REAL and WALL-OLDALE (4.3), the 3 diagonal New Game chains each, the SAME 3 seeds in both arms, the goal snapshot carried in both | L1-L2, at most 12 legs |
| **MC**, the merge check (2.4b) | first on the A1 commit, PASS before WP1; then on every merge, from the tree under test | the 3 diagonal New Game chains, NO goal snapshot (E0's harness), 3 never-used seeds | L1-L5 (to the newest graded target), at most 15 legs |
~~~

~~~old 05-b
### 2.5 Seeds
~~~

~~~new 05-b
### 2.4b The merge check (MC): the chapter 1-5 check on every merge (it replaces E0)

`plan MC --first-seed N [--to <target>]`: the three diagonal New Game chains (`live_chain` `JOB_ORDER_3` :159) from
`--fresh` to the newest GRADED target (`PROJECT KNOWLEDGE/ai-frontier.txt`; today `ch5_rival_meet`), legs by
`FRAMES_BY_CHAPTER` and `WALL`, P = 3, run with the `frontier_probe.py` of the tree under test (on a merge, the merge
worktree), so its ledger entry and evidence land on the branch under test as E0's did (`a90c8e8f`, `19e9700c`). One
development ledger entry; the prediction hashed before the first launch.
- **Its first run is on A1's own commit, and it MUST read PASS before WP1.** Part 0 moves the play digest (3.15 item
  8), so E0-2's GO (ledger #148, on `3caf9c47`) does not cover A1's play code. That run uses the stage of the A1 commit,
  and WP1 does not start before it reads PASS. On every later merge MC runs as this section says.
- **E0's harness, exactly.** No goal snapshot is carried (`AI_PLAYER_GOALS` is never sent); the next leg is decided by
  `live_chain.continue_after` itself (its 300 MB cap included); the world guard is live_chain's: an MC leg's
  `world.jsonl` is cut only over `live_chain.GUARD_WORLD_BYTES` (1,500,000,000 bytes, :178), never at A1's
  1,000,000,000, and an MC job's profile budget, 1,750,000,000 bytes, sits above that cut (2.7, 3.12). So every MC leg
  continues or stops where E0's would (T27, T33). A1's floors (45 GB to start, 40 GB to abort) still apply: they
  protect the tuner and never decide play. No E0 or E0-2 leg came near a world cap (largest 275,942,646 bytes).
- **Seeds:** each merge takes the next 3 never-used seeds of the MC range `6701-6799`, checked FREE by A1's own seed
  check before the first launch (2.5; 3.10's `--ledger development`; T13). The range read FREE in 308 ledgers at 7:46
  PM 2026-11-13 (the repo note `2026-11-13-A1-SPEC-AMENDMENTS.md`, section 2.6). Never a seed any entry names:
  6481-6483 (E0, ledger #147) and 6484-6486 (E0-2, ledger #148) are spent.
- **Reading (a hard-break check, NEVER a rate, `06` :10127).** PASS = every leg CLEAN-*, every `PURITY_IDS` check and
  L5.THIS_RUN passing, every chain reaching its target. Any HUNG, NOT CLEAN, REFUSED, freshness INFRA, CUT-WORLD or
  miss is a STOP. A miss's records (its key, or LOOP, 3.8) start the diagnosis, which is an A/B on the miss's own saved
  start (E0's method), never a reroll.
- **Its false-STOP rate is UNKNOWN.** With per-chain reach p on the tree under test, a 3-of-3 bar stops a good merge
  with probability 1 - p^3: 14 % at p = 0.95, 27 % at p = 0.9, 49 % at p = 0.8. p is not known: E0-2's 3 of 3 on
  `3caf9c47` (one trajectory per seed) bounds it only from below, at 0.37 (one-sided 95 %: 0.05^(1/3)); #101's 6 of 6
  ran main's `dc0a4e69`, and E0's 1 of 3 the unfixed merged `c25d2c40`: other trees, not pooled. One STOP's cost,
  measured once: from E0's STOP record (commit `a90c8e8f`, 8:19 AM, ledger #147) to E0-2's GO record (commit
  `19e9700c`, 7:42 PM, ledger #148) on 2026-11-13, about 11.4 hours, with a diagnosis, a shadow replay, a recon, a fix
  round and a fix-up (`07`'s merge entry; the repo note `2026-11-13-CH5-SEARCH-LOOP-FIX.md`; their Mtok are not yet in
  `cost-ledger.jsonl`). The lead may relax the bar in `06`, knowingly: for example, a miss whose key already holds on
  the base tree's newest A1 report is a known blocker, recorded, not a STOP. E0 would still have stopped under that
  rule: long loops appeared in 0 of about 11 main paths (that note's section 10, "suggestive only"; from
  `e0diag/DIAGNOSIS.md` :267-269, lab, deleted after the merge).
- About 30-45 minutes (E0 41 min, E0-2 31 min). The merge run book's step E0 becomes `frontier_probe.py run` on the MC
  job list, and `06` records "Item 4's bridge retires" (4.4 item 8).

### 2.5 Seeds
~~~

~~~old 05-c
plan P1|WP1 --first-seed N > jobs.json        (pure; validates the env keys)
~~~

~~~new 05-c
plan P1|GM|WP1|MC --first-seed N [--to T] > jobs.json   (pure; validates the env keys; MC sends no AI_PLAYER_GOALS)
~~~

~~~old 05-d
4. P1 PASSES.
~~~

~~~new 05-d
4. P1 PASSES; MC's first
run, on the A1 commit's stage (2.4b), read PASS before WP1, and its records parse.
~~~

### AM-06 (SHOULD) 3.1, 4.2: the files A1 changes

**Changed from v1:** the old text is exact (R9); `test_live_chain` :102 moves here from AM-15; 4.2's sentence on
`check_anchors` is edited here.

**Evidence.** `test_check_anchors.py` :61-63 pins `"^ANCHORS GATE: PASS \(9 of 9 runners, ..."`; `check_anchors.py`
`RUNNERS` :39-51; `run_units.py` `test_live_chain` :102 (`SUITES` :42); `suite_map.json` has 6 suites, `units`
covering `ai_player/**`; `run_regression.py` `REVERTS` :207-213; `run_regression_times.json` PROVISIONAL rows
`revert_bossprep` 15931 and `revert_p11` 12879. None of these files changed in the fix. (v3: `run_regression_times.json`
changed after it, at `<S3t2>` `fa9f073d`: four other rows raised, section 2.8; the two rows above did not move.)

~~~old 06-a
- **CHANGED, one entry each:** `G/run_units.py` `SUITES` (:42, like `test_live_chain` :94);
  `tools/workflows/suite_map.json`; `ai_player/README.md` ("Run it"); after the merge only, `G/ledger.json` (the band
  row, the batches' entries).
~~~

~~~new 06-a
- **CHANGED, one entry each:**
  - `G/run_units.py` `SUITES` (:42, like `test_live_chain` :102 on the merged tree);
  - `G/check_anchors.py` `RUNNERS` (:39-51: `"revert_frontier": ("MUTANTS", None)`), and `G/test_check_anchors.py`,
    whose CLI pin "9 of 9 runners" (:61-63) becomes 10 of 10;
  - `ai_player/README.md` ("Run it");
  - `G/ledger.json` (the band row, the batches' entries).
  `tools/workflows/suite_map.json` needs no entry: its `units` group covers `ai_player/**`. Whether `revert_frontier`
  also joins the full lane (`run_regression.py` `REVERTS` :207-213 plus a PROVISIONAL row in
  `run_regression_times.json`) is the lead's call; live_chain's mutants are not in the lane either. Part 0 (GM) lists
  its own AI-side files in 3.15.
~~~

~~~old 06-b
anchor must hit exactly once; after the merge, `check_anchors.py` (on `wip/ch6-ch7` only) reads this table too.
~~~

~~~new 06-b
anchor must hit exactly once; `check_anchors.py` (on the merged `main`, `RUNNERS` :39-51) reads this table too (3.1).
~~~

### AM-07 (SHOULD) 2.7, 3.5, 3.12, 3.13, T14, T26: a per-job disk budget, and P that fits the disk

**Changed from v1:** the budget measures the job's PROFILE folder, where the run folders live (R14); the out estimate
rises for AM-10's kept files; the free space is re-measured; the WAIT list also holds WP1b's dependency (AM-01), and
T26 tests it.

**v3** (1.0 C5, C9; the lead's calls 5 and 9): an MC job keeps live_chain's 1.5 GB world cut, with a 1.75 GB profile
budget above it (07-b, 07-c, 07-d; the disk reservation counts each job's own budget, 07-e; T14, 07-f). WP1b's
dependency is no longer a WAIT, which holds the whole queue ("nothing launches this pass"), but a per-job SKIP: the
job keeps its place, the ready jobs behind it launch, no `--max-wait` clock runs, and the fallback start is taken when
the source chain ENDS without a reached L5 (07-e; the start check's list, new 07-h; T26, 07-g).

**v4** (1.0b D4): two new blocks carry MC's 1.5 GB cut into the spec's two general lines that still stated only A1's
1 GB rule: 2.7's per-leg line (07-i, line 179) and 3.5's CUT-WORLD row (07-j, line 273). 07-j also names the
profile-folder kill, which 07-d sends to CUT-WORLD's rule but 3.5's row did not list, and an MC leg's blocker text
("over 1.5 GB"). The disk's newest readings are in 2.8 (D8); 07-a's 53.2 GB stays a dated reading, and the runner
computes P_fit at start.

**Why.** The free space is now 53.2 GB, not 66. At P = 8 the worst case could ABORT a batch on its own concurrency, and
a job's folder holds more than `world.jsonl`.

**Evidence.** `df -B1 /c` at 8:00 PM 2026-11-13: 53,218,197,504 bytes free. `paths.py` :8 ("dev default
<build_root>/profiles/<NAME>/ai_player/"); `__main__.py` :181 and `run_arm` (`live_step5.py` :448) put run folders in
`profiles/<NAME>/ai_player_runs/`. E0 T L5's `actions.jsonl`: 19,575,916 bytes for 600,000 frames (about 33 bytes a
frame). `memory.jsonl` up to 2,462,973 bytes in E0's diagnosis profiles (v1). `--state` renames the old memory file
into `retired/` each leg (launcher :205). The learner's floor: `min_free_gb` 25 (clone `config.json` :20-22, v1).

~~~old 07-a
**Free** 66 GB at 10:34 AM 2026-11-11.
~~~

~~~new 07-a
**Free** 53,218,197,504 bytes (53.2 GB) at 8:00 PM 2026-11-13 (`df -B1`; E0-2 began at
  53.6 GB).
~~~

~~~old 07-b
  Profiles are deleted per job; the main sandbox's 14 GB of old `profiles/` is not A1's.
~~~

~~~new 07-b
  Profiles are deleted per job; the main sandbox's 14 GB of old `profiles/` is not A1's.
- **Per-job budget.** A job's profile folder holds its legs' run folders (`profiles/<name>/ai_player_runs/`) and its
  memory files (`ai_player/memory.jsonl` and the `retired/` copies each `--state` leaves, launcher :205). It peaks at
  the leg in flight's `world.jsonl` (cut at 1,000,000,000 bytes) plus that leg's `actions.jsonl` (about 33 bytes a
  frame: 19,575,916 for E0 T L5's 600,000 frames, so about 40 MB for an L7), plus the finished legs' folders until the
  job's zip (about 164 MB of `actions.jsonl` for a 7-leg chain at full budgets, and about 0.6 MB of logs a leg), plus
  the memory files (up to 2,462,973 bytes each in E0's diagnosis profiles). `PROFILE_BUDGET_BYTES` = 1,250,000,000.
  An MC job (2.4b) keeps live_chain's world cut, 1,500,000,000 bytes, so its budget is `MC_PROFILE_BUDGET_BYTES` =
  1,750,000,000: the same 250 MB above its cut (an L1-L5 chain's `actions.jsonl` at full budgets is about 91 MB).
- **P fits the disk.** At start, P_fit = floor((free - `ABORT_FREE_GB` - out_estimate - stages - 2.0) / 1.25), with
  out_estimate 0.6 GB (the out store above, with the AI's own kept files) and stages 0.4 GB. The run uses min(P, P_fit),
  recorded, and refuses (exit 2) when P_fit < 1. At 53.2 GB: (53.2 - 40 - 0.6 - 0.4 - 2.0) / 1.25 = 8.2, so 8. An MC
  batch divides by 1.75 instead: 5 at 53.2 GB, above its P = 3.
~~~

~~~old 07-c
`OUT_CAP_BYTES = 5_000_000_000` (free space in
~~~

~~~new 07-c
`OUT_CAP_BYTES = 5_000_000_000`,
  `PROFILE_BUDGET_BYTES = 1_250_000_000`; for an MC job (2.4b) the world cut `live_chain.GUARD_WORLD_BYTES`
  (1_500_000_000, read from live_chain, never copied) and `MC_PROFILE_BUDGET_BYTES` = that + 250_000_000
  (1_750_000_000) (the free-space values in
~~~

~~~old 07-d
`--out` > 5,000,000,000 → DROP pending jobs.
~~~

~~~new 07-d
`--out` > 5,000,000,000 → DROP pending jobs;
  a running job's profile folder > 1,250,000,000 bytes → kill (CUT-WORLD's rule; reason "profile folder over budget").
  An MC job (2.4b) is cut by live_chain's world guard instead, newest `world.jsonl` > 1,500,000,000 bytes, and by its
  profile budget, > 1,750,000,000 bytes; never at 1,000,000,000 or 1,250,000,000.
~~~

~~~old 07-e
  singles cap; a running `run_regression.py`.
~~~

~~~new 07-e
  singles cap; a running `run_regression.py`; the disk reservation (free minus the sum, over running jobs, of the
  job's profile budget, 3.12, less its profile folder bytes, is under `ABORT_FREE_GB` + 2.0: so concurrency alone never
  ABORTs a batch). **SKIP** (per job, never global: the job keeps its place in line, the jobs behind it are checked in
  the same pass, so a ready one launches; re-checked next tick; no `--max-wait` clock runs while it waits on its
  dependency): a WP1b job whose source chain has no reached L5 record yet (2.4). When that chain ENDS without one (it
  stopped before L5, or its L5 missed `ch5_rival_meet`), the job takes its fallback start (2.1) at once. Only time in
  a WAIT counts toward `--max-wait`.
~~~

~~~old 07-f
| T14 | disk | 44.99 GB at start: no launch, no ledger write; 39.99 GB: ABORT; world 1,000,000,001 bytes: CUT-WORLD; `--out` 5,000,000,001: pending DROPPED | at each boundary: 45.0 GB starts; 40.0 GB no abort; 1,000,000,000 bytes kept; `--out` 5,000,000,000 launches; an older folder's world kills nothing |
~~~

~~~new 07-f
| T14 | disk | 44.99 GB at start: no launch, no ledger write; 39.99 GB: ABORT; world 1,000,000,001 bytes: CUT-WORLD; `--out` 5,000,000,001: pending DROPPED; a profile folder of 1,250,000,001 bytes: cut; P_fit 0: refused, exit 2; an MC job's world of 1,500,000,001 bytes or profile folder of 1,750,000,001: cut | at each boundary: 45.0 GB starts; 40.0 GB no abort; 1,000,000,000 bytes kept; `--out` 5,000,000,000 launches; a profile folder of 1,250,000,000 bytes kept; P_fit exactly 8 runs 8; an MC job's world of 1,000,000,001 and of 1,500,000,000 bytes kept, its profile folder of 1,750,000,000 kept; an older folder's world kills nothing |
~~~

~~~old 07-g
| T26 | scheduler | 10 other singles, P = 8: at most 6 own launches, rest WAIT; others fall to 0 mid-run: all 8 start, `not_started` empty; `run_regression.py` running: WAIT, then start; past `--max-wait`: DROPPED with the reason | 0 others: 8 at once |
~~~

~~~new 07-g
| T26 | scheduler | 10 other singles, P = 8: at most 6 own launches, rest WAIT; others fall to 0 mid-run: all 8 start, `not_started` empty; `run_regression.py` running: WAIT, then start; the disk reservation short: WAIT; a WP1b job before its source chain's reached L5 record: SKIPPED, then started from that end; its chain ENDED without one: started from its fallback start at once, labelled; a WAIT past `--max-wait`: DROPPED with the reason | 0 others: 8 at once; a SKIPPED WP1b job first in line with a ready job behind it: that job launches in the same pass, and the SKIPPED job keeps its place; a SKIP longer than `--max-wait` (7,200 s): not DROPPED |
~~~

**Edit 07-h** (3.13, the start check's results, line 411; new in v3):

~~~old 07-h
The start check returns GO, WAIT or DROP. **DROP** (to `not_started` with the
  reason, for good): the deadline; the `--out` cap; `STOP.txt`, `ABORT.txt`, the AI-only stop; a wait past `--max-wait`
~~~

~~~new 07-h
The start check returns GO, WAIT, SKIP or DROP. **DROP** (to `not_started` with the
  reason, for good): the deadline; the `--out` cap; `STOP.txt`, `ABORT.txt`, the AI-only stop; a WAIT past `--max-wait`
~~~

**Edit 07-i** (2.7, the per-leg line, line 179; new in v4):

~~~old 07-i
- **Per leg:** a newest `world.jsonl` over 1,000,000,000 bytes is killed (CUT-WORLD); every finished one is measured,
~~~

~~~new 07-i
- **Per leg:** a newest `world.jsonl` over 1,000,000,000 bytes (an MC job: over 1,500,000,000 bytes, live_chain's
  guard, 2.4b) is killed (CUT-WORLD); every finished one is measured,
~~~

**Edit 07-j** (3.5, the CUT-WORLD row, line 273; new in v4):

~~~old 07-j
| 1 | CUT-WORLD | the probe's guard killed the launch for `world.jsonl` over 1 GB (its kill marker) | resets | yes: "harness cut: world.jsonl over 1 GB (a churn, KI-129/KI-130)" | no |
~~~

~~~new 07-j
| 1 | CUT-WORLD | the probe's guard killed the launch (its kill marker) for `world.jsonl` over 1 GB (an MC job: over 1,500,000,000 bytes, live_chain's guard, 2.4b), or for the job's profile folder over its budget (3.12) | resets | yes: "harness cut: world.jsonl over 1 GB (a churn, KI-129/KI-130)"; for an MC job "over 1.5 GB"; for the profile cut "profile folder over budget" | no |
~~~

### AM-08 (SHOULD) 3.8, 3.7: boss preparation in the record; the raise runs in L6

**Changed from v1** (R1): v1 said the raise lies "inside L7's 1,200,000". It runs in L6 (section 2.1: 0 raise goals
after `ch6_dewford` in 8 of 8 runs; its goal records name `ch6_briney_house`). With L6 at 1,000,000 frames (AM-16), a
raise still ACTIVE at L6's end no longer names A1's own L6 budget: L6 clears every measured raise span (at most 495,767
frames, CH6_FIXED) and a Catcher's L6 at the measured ratio (about 636,000 frames, section 2.1). It names a raise that
does not end as its own budget says (BP-2's 3a, `06` :10108). The record fields move to AM-23. **v3** (1.0 C14d): such
a leg keeps its own key and is never LOOP; 3.8 now says so (the LOOP key's condition (5), 03-b), as T36 asserts.

**Why.** `06` :10116 orders BP-2's items by the probe's ranked blockers; under 3.8 every BRAWLY loss is one key
whatever the plan did.

**Evidence (at `3caf9c47`).** `brain/bossprep.py` `ACT_ON` :154, `ACTING` :156 ("Story", "Catcher"), `BUDGET` :158-162
(Story 160 battles or 450,000 frames; Catcher 200 or 550,000); `spent_reason` :802. `brain/goals.py`: the plan for the
NEXT NAMED FIGHT :2177-2181; "the raise ends, budget spent" :2476; "a battle lost on the gym map (N so far" :2581;
`[AI-BOSSPREP]` tells :2200-2590. BP-1 round 4: "stuck: 3 battles lost (MAX_LOSSES 3)" in `ab4g-6426` and `-6427`.

~~~old 08-a
→ `play: stuck: N battles lost (MAX_LOSSES N)`). `end_map_const` = the constant whose
~~~

~~~new 08-a
→ `play: stuck: N battles lost (MAX_LOSSES N)`). A not-reached CLEAN-BUDGET leg
  whose `raise` goal is still ACTIVE at its end (a `goal` record with no `goal_end` after it in `actions.jsonl`) gets
  `reason_norm` `budget: a boss-prep raise still active` (the raise runs in L6, 2.3) and keeps its own key, never the
  LOOP key (its condition (5), below).
  `end_map_const` = the constant whose
~~~

~~~old 08-b
starter, up to 3 examples newest first.
~~~

~~~new 08-b
starter, up to 3 examples newest first; for a chapter 6-7 key, the boss-prep breakdown (plan
  made, raise ended by its budget, trainee reached its target, a Trainer that only logged) and the battles lost carried
  in against lost in the leg (3.15).
~~~

### AM-09 (SHOULD) 3.6, 3.8: a leg boundary is a session boundary; the stale-memory cost, per tile

**Changed from v1** (the lead's call 7, R4): the stale measure counts only tiles in the carried snapshot's
`tried_items`, per tile, because the fix's E makes the "gone" message fire for a ball merely out of reach (section 2.5).
The field's definition is in AM-23; this amendment adds the session-boundary paragraph and the reach split. **v3**
(1.0 C1): the yardstick is the start's kept snapshot, carried or not, so GM's GOALS-OFF legs get a count too (AM-23).

**Evidence.** DIAGNOSIS :167-170 ("A new session drops the in-session marks: `WorldMemory.unreached`, `cut_off` and
`spent` are not in world.jsonl"); `fix5/STATE.md` 12:35 PM (E's standing walls, "Not saved in to_dict", v1);
`GOAL_RESET` :164-180; `mode.py` :796-797; BP-1 round 4's first goal from C1 was already a stale errand: "not picked up:
no item ball where it lay at (36, 51) any more" at f746397 (`ab4w-B4-C1-6414/actions.jsonl`).

~~~old 09-a
### 3.7 Records (schema_version 1; one JSON line each in `<out>/records.jsonl`)
~~~

~~~new 09-a
**A leg boundary is a session boundary.** The next leg starts with the end state, the kept world line and, with part 0,
the kept goal snapshot. Everything else restarts: the explorer's in-session marks (`WorldMemory.unreached`,
`cut_off`, `spent`, which are not in `world.jsonl`; and the fix round's session-only standing walls); `GOAL_RESET`;
and, without a snapshot (`goal_memory: none`), also `GOAL_KEEP`, the personality's draws, the battle mind and the loss
count. A chain is one game played in N sessions, not continuous play. `measures.stale` (3.7) measures the cost per
tile.

### 3.7 Records (schema_version 1; one JSON line each in `<out>/records.jsonl`)
~~~

~~~old 09-b
CLEAN-BUDGET apart from CLEAN-CHOSEN.
~~~

~~~new 09-b
CLEAN-BUDGET apart from CLEAN-CHOSEN, and reach split by start kind: new game; chain leg with a goal snapshot; chain
  leg without; practice with a snapshot; practice world-only (`goal_memory: none`).
~~~

### AM-10 (SHOULD) 3.12, 2.7, T15: keep the AI's own save, memory and goal snapshot in each example

**Changed from v1:** the old text is exact; the goal snapshot (`goals_last.jsonl`) joins the kept files; the out
store's size rises; T15 tests it.

**Evidence.** Spec :403-404; `paths.py` :1-16 (the memory lives "beside the profile's current_save.sav"); USER RULING
55's "practice runs that replay a chapter from the AI's own saves" (`06` :9962); `game_memory.py` :16 (the header is
"written with the FIRST save line (no save, no file)").

~~~old 10-a
each leg's `end_state.ss1` and `world_last.jsonl` (the example; Phase A's pool state).
~~~

~~~new 10-a
each leg's `end_state.ss1` and `world_last.jsonl` (the example; Phase A's pool state),
  and, copied into the leg's kept folder BEFORE the profile is deleted, each when present: `goals_last.jsonl` (part 0),
  the profile's `current_save.sav`, `ai_player/memory.jsonl` and `ai_player/launches.jsonl` (about 1-3 MB a leg; a
  memory file exists only once the AI has saved in that game, `game_memory.py` :16; an absent one is recorded).
~~~

~~~old 10-b
**Out store** about 2.5 MB a leg (1.5 raw, 1 zipped logs), 0.3 GB for 120 legs
~~~

~~~new 10-b
**Out store** about 5 MB a leg (1.5 raw, 1 zipped logs,
  up to 3 of the AI's own kept files, 3.12), about 0.6 GB for WP1's 120 legs
~~~

~~~old 10-c
| T15 | retention | a zip failing `testzip` keeps the raw folder | verified: raw deleted but `end_state`, `world_last`; profile deleted |
~~~

~~~new 10-c
| T15 | retention | a zip failing `testzip` keeps the raw folder; an AI file whose copy fails its size check is recorded, never silent | verified: raw deleted but `end_state`, `world_last`, `goals_last` and the AI's save and memory files when present (an absent one recorded); profile deleted |
~~~

### AM-11 (SHOULD) 3.2: `replay` and `compare`, from E0's kit

**Changed from v1:** the old text is exact; `replay` carries the kept goal snapshot. **v4** (1.0b D3): the lead kept
both port sources in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/scripts/` (`replay_leg.py`,
`compare_moves.py`; sha256 in its README.txt; this PC only, not git).

**Evidence.** `e0diag/replay_leg.py` :1-17; `e0diag/compare_moves.py` :1-7; SHADOW :62 ("IDENTICAL (frame, action) over
the first 29492").

~~~old 11-a
report DIR                                     (offline; from records.jsonl)
~~~

~~~new 11-a
report DIR                                     (offline; from records.jsonl)
replay EXAMPLE --stage DIR --profile NAME [--seed N] [--frames F] [--code-tree DIR]
                                               (one leg again from a kept example: state, world line, goal
                                                snapshot when kept; one new trajectory, never a replication)
compare A.jsonl B.jsonl [--context N]          (offline; the first differing (frame, action), skipping 'say' and
                                                'world' records)
~~~

### AM-12 (SHOULD) 4.3 P1, P2: forms, CONTROLs under LOOP keys, final-head anchors, P2 under the raise

**Changed from v1** (R5, R6, R1): K1 is no longer a reason (it cannot fire at either wall: section 2.5,
`k1_blast.out.txt`); the CONTROLs read records under LOOP keys; v1's `map_walls`/`standing_walls` names do not exist
at `3caf9c47` and are replaced by `Navigator.walls`; P2's CONTROL is re-derived under L6's 1,000,000 frames, with its
discriminator.

**v3** (1.0 C7; the lead's call 7): under the carried loss count a REAL job that enters chapter 6 with 2 losses ends
L6 at its first lost battle there, and a raise battle lost before the house leaves next unmet `ch6_briney_house`: the
FAULT's own form, with no wall. Such `stuck: N battles lost` ends with `losses_carried` > 0 are reported apart from
the CONTROL, and the discriminator names the path with its measured frequency: 0 battles lost before `ch6_dewford` in
8 of 8 runs from C1 (section 2.8).

**Evidence.** Section 2.1 (L6 frames, the raise's milestone), section 2.5 (K1, E). Decomp pin `731ad5b`
`Route104_MrBrineysHouse/scripts.inc` :25, :32 (the spec's own citation).

~~~old 12-a
**P1, the planted wall at OLDALE TOWN (FAULT and CONTROL, on `main`'s code).** Arms REAL (the stage at the commit) and
~~~

~~~new 12-a
**P1, the planted wall at OLDALE TOWN (FAULT and CONTROL, on the merged `main`, the goal snapshot carried in both
arms).** The anchor is picked, and its offline unit test run, on the final merged head: since the fix round's E,
`Navigator.walls` (`brain/navigator.py` :816-820 at `3caf9c47`) also holds the things seen standing this session
(`objects_now`), so the planted wall extends the wall set as that head builds it. P2's anchor follows the same rule.
Arms REAL (the stage at the commit) and
~~~

~~~old 12-b
Predicted form CLEAN-CHOSEN with a reason beginning `play: stuck:`; a
  CLEAN-BUDGET end still counts toward (a), reported as a miss of the form. Confirmed at decomp pin `731ad5b`:
~~~

~~~new 12-b
Predicted form CLEAN-CHOSEN with a reason beginning `play: stuck:`. A
  CLEAN-BUDGET end, or a LOOP key whose legs' records all have next unmet `ch1_rival_route103`, still counts toward
  (a), reported as a miss of the form; "the top chapter-1 key names it" reads a LOOP key's records. Confirmed at
  decomp pin `731ad5b`:
~~~

~~~old 12-c
- **(b) CONTROL:** on REAL no chapter-1 key names `ch1_rival_route103`, and at least 2 of 3 chains reach `ch2_wally`.
~~~

~~~new 12-c
- **(b) CONTROL:** on REAL no chapter-1 leg record ends not reached with next unmet `ch1_rival_route103`, under its own
  key or a LOOP key, and at least 2 of 3 chains reach `ch2_wally`.
~~~

~~~old 12-d
:25, :32). **CONTROL:** the 3 paired REAL J-F jobs never show it. This proves saved starts put a wall in the right
chapter.
~~~

~~~new 12-d
:25, :32); a LOOP key whose records all name `ch6_briney_house` counts as well. **CONTROL:** no leg record of the 3
paired REAL jobs (WP1b's first-seed J-F job of each diagonal pair, or its fallback, 2.1) ends not reached with next
unmet `ch6_briney_house`, under any key, except an end `play: stuck: N battles lost` whose leg carried losses in
(`losses_carried` > 0, 3.15 item 2): such an end is reported apart, beside the CONTROL, and never read as the wall or
as its absence. **The discriminator, computed before the prediction is hashed:** the next unmet milestone at L6's end.
On WALL-BRINEY it stays `ch6_briney_house` in every case (the flag is set only inside the house). On REAL, L6's
1,000,000 frames (2.3) hold a Story raise (the largest measured L6 from C1: 520,366 frames) and a Catcher raise (its
550,000-frame budget × 1.156, the largest measured L6 over Story's 450,000: about 636,000 frames) with room to spare,
so a REAL leg that nothing blocks reaches `ch6_dewford`. On the spec's 600,000 frames a Catcher L6 could not fit, and
its CLEAN-BUDGET end with next unmet `ch6_briney_house` (the raise's goal records name that milestone) would read as
the wall: the CONTROL would not have discriminated. One more path ends a REAL L6 in the FAULT's form: the carried loss
count. A game that enters chapter 6 with 2 losses (2 of the 9 chapter 1-5 chains measured, 3.15 item 2) stops at its
first lost battle there (MAX_LOSSES 3), and a raise battle lost before the house leaves next unmet
`ch6_briney_house`. Measured: 0 battles lost before `ch6_dewford` in 8 of 8 runs from C1 (0 carried; all 8 of their
losses came after it, at BRAWLY's gym), so the path is possible and was not seen. This proves saved starts put a wall
in the right chapter.
~~~

### AM-13 (SHOULD) 4.3 WP1 CONTROLS: the merged and fixed tree's own chapter 1-5 result

**Changed from v1** (R7, R2, R5): the prior is E0-2, not the fix's per-leg A/B; the harness difference (WP1a carries
the goal snapshot, E0-2 and #101 did not) is named, with MC as the like-for-like check; the prediction expects few
chapter-5 LOOP keys after E and K1, and possible chapter-3 churn. **v3** (1.0 C8, the lead's ALSO): E0-2 ran
`3caf9c47`'s play code, and part 0 moves A1's play digest, so the CONTROL names MC's first run on the A1 commit; the
lab citations become commit `19e9700c`, ledger #148 and the repo note `2026-11-13-CH5-SEARCH-LOOP-FIX.md`.

~~~old 13-a
the diagonal J-N chains reach `ch5_rival_meet` in at least 2 of 3 (#101 was 6
of 6 on `dc0a4e69`; D15's "chapters 1-5 did not regress", in development form)
~~~

~~~new 13-a
WP1a's diagonal J-N chains reach `ch5_rival_meet` in at least 2 of 3 (D15's
"chapters 1-5 did not regress", in development form). The prior is E0-2 on the merged and fixed head: "E0 VERDICT:
REACHED 3 of 3; legs ran 15, purity-clean 15; wall 31 min (cap 120); problems 0 -> GO" (the message of commit
`19e9700c`; ledger #148, `ai_player/evidence/2026-11-13-chain-heldout-dev-ch5_rival_meet-6484.txt`; one trajectory
per seed). It ran `3caf9c47`'s play code; part 0 moves A1's play digest (3.15 item 8), so MC's first run on the A1
commit must read PASS before WP1 starts. E0-2 and #101 (6 of 6 on `dc0a4e69`, main's code) carried no goal snapshot
and WP1a does: the report names that difference, and MC on the same tree (2.4b) is the like-for-like check. The fix
round's per-leg A/B (one trajectory per arm from saved starts) is mechanism evidence only. The prediction expects few
or no chapter-5 LOOP keys after E and K1 (the fix's arms from E0's starts crossed the woods pair once from T's start
and 0 times from C's: the repo note `2026-11-13-CH5-SEARCH-LOOP-FIX.md` section 8; 0 from S's, `fix5/STATE.md`, lab,
deleted after the merge), and chapter-3 churn rows are possible (E0-2's T L3
reached with 92 crossings)
~~~

### AM-14 (SHOULD) 3.12: teardown proofs from the kit that ran on the merged code

**Changed from v1:** the old text is exact (R9). Substance unchanged. Evidence: `mergeplan/stage_merge.py` :8-17,
`find_junctions.py` :1-6; DIAGNOSIS :318-324; SHADOW :171 (v1). **v3** (the lead's ALSO): those sources are lab,
deleted after the merge, so the NEW block marks them and states the rule in full; the port needs only
`build_stage11.py` (in `ch6probe11/`, not on the deletion list) and the text. **v4** (1.0b D3): v3's "not on the
deletion list" no longer holds: under the lead's ruling `ch6probe11/` is lab too. The kit's sources are kept in
`C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/` (the lead's `scripts/stage_merge.py` and `stage_diag.py`;
v4's `mergeplan/find_junctions.py` and `ch6probe11/`), and 14-a names them. `stage` also promotes `make_arm11.py`
(the spec's 3.3), so 14-a names it beside `build_stage11.py`.

~~~old 14-a
- **`teardown`** unlinks every junction FIRST (a recursive delete through one would delete the main sandbox's
  `modules/`), then deletes the stage.
~~~

~~~new 14-a
- **`teardown`** unlinks every junction FIRST (a recursive delete through one would delete the main sandbox's
  `modules/`), then deletes the stage. It prints the main sandbox's counts of `modules`, `plugins`, `mgba` and `roms`
  before and after (they must read unchanged). Before any delete, a junction scan of the stage folder must find none.
  This is the rule of the kit that staged the merged code (`stage_merge.py` :8-17 and `find_junctions.py` :1-6 from
  `_ai_lab/s53/mergeplan/`, `stage_diag.py` from `_ai_lab/s53/e0diag/`: lab; their copies are kept in
  `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/`, `scripts/` and `mergeplan/`, sha256 in its README.txt,
  this PC only, not git; E0's diagnosis and its shadow replay tore down every stage this way). It is stated here in
  full, so `stage` and `teardown` need only the 1.2 lab kit's `build_stage11.py` and `make_arm11.py` (3.3; kept copies,
  1.2) and this text.
~~~

### AM-15 (NOTE) citations and counts on the merged tree

**Changed from v1** (R9, R14): `:1368` is anchored to 1.2's Exits row only (the Review log keeps its history);
`test_live_chain :94` moved to AM-06 (06-a); risk 6's line is `:935` at `3caf9c47`, not `:919`; the planted-milestone
rule is placed in 4.1.

**v4** (1.0b D3; the lead's ruling that every folder under `_ai_lab/s53/` is lab the merge's cleanup may delete): new
block 15-g. 1.2's Lab kit row names four lab files A1's build reuses (`stage`, 3.3; the child, 3.4; the seed re-check,
2.5). They are copied, cmp-equal, into `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/` (`ch6probe11/`,
`bp1r2/`), and the row names that folder.

~~~old 15-a
`ai_player/mode.py` :1368 (`stopped: not finished within … frames`)
~~~

~~~new 15-a
`ai_player/mode.py` :1401 (`stopped: not finished within … frames`)
~~~

~~~old 15-b
28 milestones on `main`, 36 on `wip/ch6-ch7`.
~~~

~~~new 15-b
36 milestones on the merged `main` (28 before it).
~~~

~~~old 15-c
On `main` there are no chapter 6-7 marks
  (`play_harness.tracked()` reads `knowledge/milestones.json`, which ends at chapter 5 there); they come with the merge.
~~~

~~~new 15-c
The merged `milestones.json`
  holds chapters 6-7's marks (36 milestones; `play_harness.tracked()` reads `knowledge/milestones.json`).
~~~

~~~old 15-d
Chapters 6-7 (the sail to DEWFORD through BRAWLY) are on branches, merged next.
~~~

~~~new 15-d
Chapters 6-7 (the sail to DEWFORD through BRAWLY) are merged
  on `main` at <the merge commit>; the graded frontier is unchanged (a merge check is not a grade).
~~~

~~~old 15-e
(`WorldMemory.from_dict` uses `.get` defaults, :919 on the branch)
~~~

~~~new 15-e
(`WorldMemory.from_dict` uses `.get` defaults, :935 at `3caf9c47`)
~~~

~~~old 15-f
to FAIL on a copy with its guard removed (4.2).
~~~

~~~new 15-f
to FAIL on a copy with its guard removed (4.2). A test that plants a milestone puts it AFTER the real file's last
chapter (`test_live_chain.py` `case_no_budget` :487-493 on the merged tree: a chapter-6 milestone behind chapter 7 is
refused BACKWARDS).
~~~

**Edit 15-g** (1.2, the Lab kit row, line 64; new in v4):

~~~old 15-g
| Lab kit | `_ai_lab/s53/ch6probe11/build_stage11.py`, `make_arm11.py`, `arms11.py` `child` (`carried = {"START": (state, world, [])}`, `state_from="START"`); `s53/bp1r2/seeds_free.py` | `stage` (3.3); seeds (2.5) |
~~~

~~~new 15-g
| Lab kit | `_ai_lab/s53/ch6probe11/build_stage11.py`, `make_arm11.py`, `arms11.py` `child` (`carried = {"START": (state, world, [])}`, `state_from="START"`); `s53/bp1r2/seeds_free.py`. `_ai_lab/s53/` is lab, which the merge's cleanup may delete: the four files are kept, cmp-equal, in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/` (`ch6probe11/`, `bp1r2/`; sha256 in its README.txt; this PC only, not git) | `stage` (3.3); seeds (2.5) |
~~~

### AM-16 (MUST; v1 said NOTE and closed it the other way) 2.3, 3.4, section 5: L6's budget is raised

**Changed from v1** (the lead's call 1, R1, M1): v1 compared L6+L7 frames against L7 alone and said "no raise". The
raise runs in L6, and L6 used over 80 % of its 600,000 frames in 5 of 8 runs, so the spec's own rule (2.3: "used over
80% of a leg's frames, raise that budget before WP1's prediction is hashed") requires the raise. The number is derived
from the measured frames (section 2.1). **v4** (1.0b D3): 16-d cites BP-1 round 4's ledger entries (#131-#133) and
their committed evidence file for the raise ends, and this note's section 2.1 for the derivation; its per-run L6 frames
are marked as read from the runs' lab logs.

**The derivation.** (1) The largest measured L6 is 520,366 frames (CH6_FIXED, Story); under 80 % that needs at least
650,458. (2) The raise ended on its frame bound in exactly the 5 runs over 80 %, so where that bound ends the raise, L6
follows the raise's frame budget (an inference from 5 runs): the largest L6 is 1.156 times Story's 450,000. A Catcher's budget is 550,000 (`brain/bossprep.py` :160), so a
Catcher L6 needs about 636,000 frames, and under 80 % at least about 795,000. (3) Rounded up: **1,000,000 frames**. The
largest Story L6 then uses 52 %, a Catcher's about 64 %. (4) The wall: at 349 frames/s (2.6) 1,000,000 frames take
2,865 s, at 300 frames/s (where the lead lowers P) 3,333 s; the wall is **7,200 s**, as L7's, so a slow host never
turns a budget end into a hard kill. (5) It is set before WP1's prediction is hashed. Its basis is USER RULING 55 (2)
(`06` :9963: "In training the budget is set generously, so it never cuts off real progress"), which keeps the frame
budget as the session limit; raising one leg's budget keeps that decision.

~~~old 16-a
| Frames | 330,000 | 330,000 | 600,000 | 900,000 | 600,000 | 600,000 | 1,200,000 |
~~~

~~~new 16-a
| Frames | 330,000 | 330,000 | 600,000 | 900,000 | 600,000 | 1,000,000 | 1,200,000 |
~~~

~~~old 16-b
| Wall (s) | 3,600 | 3,600 | 3,600 | 3,600 | 3,600 | 3,600 | 7,200 |
~~~

~~~new 16-b
| Wall (s) | 3,600 | 3,600 | 3,600 | 3,600 | 3,600 | 7,200 | 7,200 |
~~~

~~~old 16-c
At 349 frames/s (2.6), 1,200,000
  frames take 3,440 s: the wall is 7,200 s.
~~~

~~~new 16-c
At 349 frames/s (2.6), 1,200,000
  frames take 3,440 s and 1,000,000 take 2,865 s (3,333 s at 300 frames/s, where the lead lowers P): both walls are
  7,200 s.
~~~

~~~old 16-d
- **At build time:** if a final BP-1 round 3 or P11-1 run that reached its target used over 80% of a leg's frames, raise
  that budget before WP1's prediction is hashed.
~~~

~~~new 16-d
- **The budget check, closed on 2026-11-13: L6 raised to 1,000,000 frames.** The boss-prep raise runs INSIDE L6: it
  plans for the next NAMED fight from the whole story (`brain/goals.py` :2177-2181 at `3caf9c47`; `load_story` loads
  every milestone, `knowledge/story.py` :152-153), and 8 of 8 measured runs from C1 made 0 raise goals after
  `ch6_dewford`. L6 (C1's start record, f746397, to `MILESTONE ch6_dewford`) took 500,515, 496,341 and 495,188 frames in
  BP-1 round 4's `ab4w-B4-C1-6414/6415/6416`, 395,755, 382,058 and 377,952 in `ab4g-6426/6427` and `ab4g2-6429`
  (ledger #131-#133, which that evidence file numbers #125-#127 as on `wip/ch6-bp1`; their raises ended at frames
  457,706, 460,630 and 450,262 of 450,000 in #131 and at battles 164, 164 and 163 of 160 in #132-#133:
  `ai_player/evidence/2026-11-11-bossprep-bp1r4-live.txt`, P-W5 and P-G6), and
  520,366 and 520,216 in the fix round's CH6_FIXED and CH6_UNFIXED (the repo note `2026-11-13-CH5-SEARCH-LOOP-FIX.md`
  section 8 keeps their whole L6+L7 frames, 657,908 and 609,121), one trajectory each, each L6 read from its run's own
  log (lab, deleted after the merge): 5 of 8 over 80 % of 600,000, exactly the 5 whose raise ended on its frame bound
  (450,262-475,016 of 450,000). The derivation is in the repo note `2026-11-13-A1-SPEC-AMENDMENTS.md` (section 2.1 and AM-16). A
  Catcher's budget is 550,000 frames (`brain/bossprep.py` :160): at the largest measured L6 over Story's 450,000
  (1.156) a Catcher L6 needs about 636,000 frames. 1,000,000 keeps both under 80 % (52 % and about 64 %). Set before
  WP1's prediction is hashed (USER RULING 55 (2), `06` :9963: "In training the budget is set generously, so it never
  cuts off real progress").
~~~

~~~old 16-e
{**FRAMES_BY_CHAPTER, 6: 600000, 7: 1200000}
~~~

~~~new 16-e
{**FRAMES_BY_CHAPTER, 6: 1000000, 7: 1200000}
~~~

~~~old 16-f
## 5. What needs the chapter 6-7 merge, and what could be built before it
~~~

~~~new 16-f
## 5. What needs the chapter 6-7 merge, and what could be built before it

**History once the merge lands:** every part is then built and run on the merged `main`. The order note below still
holds, and the L6/L7 budget check is closed (2.3).
~~~

### AM-17 (SHOULD) 2.5: seeds re-checked; GM's and MC's seeds; an unreadable ledger fails closed

**Changed from v1:** re-checked at 7:46 PM with 308 ledgers (section 2.6); GM's 6604-6606 and MC's 6701-6799 added;
6484-6486 are now E0-2's (WT #148), not a reserve. **v4** (1.0b D3): 17-a cites this note's section 2.6 for the 7:46 PM
reading and A1's own seed check (2.5, 3.10, T13) for every later check, not `bp1r2/seeds_free.py`. The script the
spec's 2.5 re-runs at build time is kept in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/bp1r2/`, and 1.2's
Lab kit row says so (15-g).

~~~old 17-a
- **Proposed:** P1 `6601-6603`, WP1 `6611-6646`. At 10:40 AM 2026-11-11, `py -3.12 -B "C:/Remote
~~~

~~~new 17-a
- **Proposed:** P1 `6601-6603`, GM's live A/B `6604-6606`, WP1 `6611-6646`, MC `6701-6799` (3 a merge,
  2.4b). Re-checked at 7:46 PM 2026-11-13: FREE for each of these ranges and for `2000000-2999999` in 308 ledgers
  (main 1, worktrees 11, others 296; the command and its output: the repo note `2026-11-13-A1-SPEC-AMENDMENTS.md`,
  section 2.6); 6481-6483 are E0's (ledger #147) and 6484-6486 E0-2's (ledger #148). A1's own seed check (this
  section and 3.10's `--ledger development`, T13) checks every seed again before the first launch.
  At 10:40 AM 2026-11-11, `py -3.12 -B "C:/Remote
~~~

~~~old 17-c
- **Not a reservation:** BP-1 round 3 (6403-6430) and P11-1 (6431-6460) have not committed.
~~~

~~~new 17-c
- **Not a reservation:** BP-1 rounds 3-4 and P11 have since committed their seeds (the merged `ledger.json`'s
  entries #128-#146 name seeds in 6403-6454).
~~~

~~~old 17-b
development included (live_chain R3).
~~~

~~~new 17-b
development included (live_chain R3). A1's own check lists every ledger it could not read and refuses
  unless each is a known non-ledger (on 2026-11-13 one truncated export,
  `_ai_lab/s53/mergeplan/review/exports/s2/ai_player/gates/ledger.json`, "Expecting value: line 115"; lab, deleted
  after the merge; `seeds_free.py` only skips it).
~~~

### AM-18 (NOTE) section 0, 2.8, 6.1, 6.2: cost and time with the amendments and the full lane

**Changed from v1** (the lead's call 8, R10, R13): section 0's headline is amended (cost, WP1a and WP1b, part 0,
machine time); the full regression lane's hours are in; L6's change is in the worst case; the 6.1 rows sum to the
total.

**v3** (1.0 C6; the lead's call 6): "at least 4.4 h" read the rows the wrong way. The lane's 4.4 h is a BUDGET from
its longest row, which the timing file calls an upper bound, so it is "about 4.4 h (budgeted from upper-bound rows)"
everywhere. The merge's own full lane (`07`'s merge entry) gives the measured hours, which A1's build plan reads when it
starts (section 5, step 0a). The rows moved at `<S3t2>` (section 2.8); the longest did not. MC's first run is named
as such (C8); the LOOP rule's name follows C4. **v4** (1.0b D6, D8): the evidence no longer calls all four raised rows
kill times: `revert_safety_gates`' 3456 is a PASS time (`fa9f073d`'s `_doc`: "ran revert_safety_gates 3455.6 s (96 % of
its 3600 s floor)"). WP1's hours at the disk's newest P_fit are in 2.8; the 18-a..18-e texts keep P = 8, which the
runner lowers to P_fit at start (2.7).

**Evidence.** `run_regression_times.json` at `19e9700c`: `revert_bossprep` 15931, `revert_p11` 12879 (PROVISIONAL,
"upper bounds until measured alone"), `revert_step5` 3460, `revert_step3` 2014, `revert_r1` 1167; the suites sum to
36,334 s. At `fa9f073d` (`<S3t2>`, section 2.8): `revert_step5` 12110, `revert_step3` 7049, `revert_r1` 4085,
`revert_safety_gates` 3456 (three of them the side lanes' kill times, lower bounds there; revert_safety_gates' 3456 a
PASS time, 3455.6 s, 96 % of its 3600 s floor; all four "upper bounds under load until measured alone", the `_doc`);
the suites sum to 56,067 s. With `--workers 4` the lane's planned wall is its longest row, 15,931 s
(4.43 h, `mergeplan/STATE.md` line 260, lab): a budget from an upper-bound row, not a bound below. `06` :10126 (a lane
that only times out runs again). E0-2's chains: 19.5-29.8 min of legs each (section 2.3).

~~~old 18-a
- **WP1 (after the merge), 39 jobs:** 9 New Game chains to `ch7_brawly`, one per personality × starter (6 pairs never
  played as a New Game chain: `live_chain.PAIRS` is the diagonal, though `rate_step5.plan_of` cycled all 9 in sweeps);
  27 practice jobs (9 chapter-5 ends × 3 seeds, chapters 6-7); 3 planted-wall jobs. About 3-3.5 h of machine time at 8
  at once beside the tuner's 12 lanes (6.5 h worst). First, P1 (20-30 min) plants a wall at OLDALE TOWN that must rank
  first on the walled code and never appear on the real code.
~~~

~~~new 18-a
- **WP1 (after the merge), 39 jobs in one batch:** **WP1a**, 9 New Game chains to `ch7_brawly`, one per personality ×
  starter (6 pairs never played as a New Game chain: `live_chain.PAIRS` is the diagonal, though `rate_step5.plan_of`
  cycled all 9 in sweeps), each leg carrying the goal snapshot; **WP1b**, 27 practice jobs (WP1a's 9 chapter-5 ends ×
  3 seeds, chapters 6-7; a pair whose chain missed uses its persona's G start, counted apart) and 3 planted-wall jobs
  (P2). About 4-5 h of machine time at 8 at once beside the tuner's 12 lanes (about 9 h if every L6 and L7 spends its
  whole budget; L6 is now 1,000,000 frames). Before it: part 0's live A/B (about 1-1.5 h), P1 (20-30 min: a wall at
  OLDALE TOWN that must rank first on the walled code and never appear on the real code), MC's first run (about 30-45
  min, on the A1 commit; it must read PASS) and one full regression lane (about 4.4 h, budgeted from upper-bound rows;
  the merge's own full lane gives the measured hours). About 11-13.5 h of machine time in all, about 22.5 h worst
  (6.2). Estimates.
~~~

~~~old 18-b
- **Cost:** 38-65 Mtok (central 50), above the design's 8-15; the graded chain driver it leans on cost 111.8 Mtok
  (`cost-ledger.jsonl`).
~~~

~~~new 18-b
- **Cost:** about 57-98 Mtok (central 76; estimates), above the design's 8-15 and the first draft's 38-65: part 0
  (GM), its verifier share, the amendments' rules and the extra live work add 19-33 (6.1). The graded chain driver it
  leans on cost 111.8 Mtok (`cost-ledger.jsonl`).
~~~

~~~old 18-c
P1: about 1 job-hour, 20-30 min at P = 6. WP1: about 19 job-hours (J-N 9 × 0.9 h, from #101's 17-28 min a chain for
chapters 1-5 at P = 3 plus 10-30 min for 6-7; J-F 27 × 0.4 h; P2 3 × 0.15 h), so 3-3.5 h at P = 8 with the tail, 6.5 h
if every L7 spends its whole budget.
~~~

~~~new 18-c
P1: about 1 job-hour, 20-30 min at P = 6. GM's live A/B: one chain L1-L5 and 4 L6 legs, about 1-1.5 h. MC: about
30-45 min at P = 3 (E0 41 min, E0-2 31 min). WP1: about 28 job-hours (WP1a 9 × 1.05 h: chapters 1-5 in 19.5-29.8 min a
chain in E0-2, then L6 and L7; WP1b 27 × 0.6 h; P2 3 × 0.65 h), so about 4-5 h at P = 8 with WP1b's wait for WP1a's
L5 ends and the tail, about 9 h if every L6 and L7 spends its whole budget (1,000,000 and 1,200,000 frames at 349
frames/s). The full regression lane (4.4 item 3): about 4.4 h, budgeted from upper-bound rows: its longest suite,
`revert_bossprep`, has a PROVISIONAL 15,931 s row, the next, `revert_p11`, 12,879 s (`run_regression_times.json`
calls both "upper bounds until measured alone"), and every other row is shorter (since `fa9f073d`, `revert_step5`
12,110 s, a side lane's kill time). A lane that only times out runs again (`06` 2026-11-12 item 3): about 9-10 h then.
The merge's own full lane (`07`'s merge entry) gives the measured hours, and A1's build plan reads them when it
starts.
~~~

~~~old 18-d
| **Total** | **38-65 (central 50)** | the sum of the parts |
~~~

~~~new 18-d
| Part 0, GM (AI-side code, offline FAULT and CONTROL, purity, gates) | 8-15 | the first amendments' estimate; R1 + R2's save and memory work is the nearest kind |
| The amendments' rules (LOOP and its end rule; boss-prep, rides, K1 and stale fields; MC's plan, seeds and world cut; the per-job disk budget; WP1b's SKIP; replay and compare; rides and `slid`; L6) | 5-9 | the first amendments' 4-8, plus this revision |
| GM's share of the verifier | 3-5 | the first amendments' estimate |
| The extra live work (GM's chain and A/B, MC's first run, WP1b's dependency, the full lane's watch) | 2-3 | ch6-probe11 1.6 for 3 runs |
| The extra `06` entries (4.4 item 8) and their Tier 1 | 1 | recent docs rows |
| **Total** | **57-98 (central 76)** | the sum of the parts: 38-65 above, plus 19-33 |
~~~

~~~old 18-e
Build 5-8 h of agent time; P1 about 30 min; trainer smoke about 15 min; WP1 3-3.5 h of machine time (6.5 h worst); the
report about 1 h. Calendar: about 1.5-2 days after the merge, less if the offline build ran before it.
~~~

~~~new 18-e
Agent time about 13-20 h. Machine time about 11-13.5 h: GM's live A/B 1-1.5 h; P1 about 30 min; MC's first run about
30-45 min; the mutant run about 30 min; the trainer smoke about 15 min; WP1 4-5 h (about 9 h worst); the full lane
about 4.4 h (budgeted from upper-bound rows; about 9-10 h if it times out once and runs again; the merge's own lane
gives the measured hours); about 22.5 h worst in all. The report about 1 h. Calendar: about 3-4 days after the merge,
less if the offline build ran before it. Estimates.
~~~

### AM-19 (NOTE) 2.6: load moves trajectories

**Changed from v1:** the old text is exact; the wording says "suggestive" (R14). **v3** (1.0 C10, the lead's ALSO):
`REFUTE.md` :256-258 (its sentence ends at :258); both lab sources are marked; the stepping claim also names its code,
`hands/pad.py` `_count` (`yield from self._count(...)` at :103, :104, :121, :135, :146 at `3caf9c47`).

~~~old 19-a
recorded. RAM 128 GB; per-run RAM UNMEASURED.
~~~

~~~new 19-a
recorded. RAM 128 GB; per-run RAM UNMEASURED. Load may move a trajectory (suggestive only: decision stalls of
  100-700 ms came before a game-side split in 2 runs against 3, `e0diag/shadow/SHADOW.md` :83-84; stepping is
  synchronous, `hands/pad.py` `_count`, so load changes frames only through an unproven host-time effect,
  `e0diag/REFUTE.md` :256-258; both files lab, deleted after the merge). So frames/s stays per leg, no claim compares
  two arms' paths, and a lower P makes a leg faster, never a replay.
~~~

### AM-20 (SHOULD, NEW) 3.7, 3.9, T16, 4.3: K1's leads in the record; a K1 tell is never a fight

**Why** (the lead's call 6, R5, M6). K1 (the fix's entry-map lead) writes a `tell` into `actions.jsonl`, but the
record says nothing of it, so a chapter-5 stop or LOOP cannot say whether K1 fired. K1 cannot fire at P1's or P2's
walls (section 2.5), so it is no reason in AM-12.

**What.** `measures.k1_leads` (defined in AM-23), read from the `tell` records "... is somewhere it has not been:
first to <lead>, a seasoned player's knowledge: <lead> has a way into it". K1's leads stay out of the experience
extract (they are static knowledge from `knowledge/world/maps.json`, never the AI's memory). T16's CONTROL (04-b) and
T35 (AM-24) prove the fights parser never reads a K1 tell as a foe. WP1's prediction expects few or no chapter-5 LOOP
keys (13-a). The edit below states the parser's rule in 3.9.

~~~old 20-a
(the newest earlier `tell` "battle: a trainer battle against", `tells` :702-705)
~~~

~~~new 20-a
(the newest earlier `tell` "battle: a trainer battle against", `tells` :702-705;
  no other tell is read, so a K1 lead's tell, "... a seasoned player's knowledge: ...", never names a foe)
~~~

### AM-21 (NOTE, NEW) section 0: the chapter 1-5 miss rate is out of A1 v1's scope

**Why** (the lead's call 5, R12, M12). E0's diagnosis left OPEN whether the merge raises the chapter 1-5 miss rate. It
is a frequency question for many seeds (CLAUDE.md rule 9). MC is a hard-break check and WP1a has 9 chains, so A1 v1
cannot answer it. **Declined:** the review's first option, a main-tree arm inside A1.

**Filed as its own item:** the lead files a `03` item in the merge's docs pass (`06` 2026-11-12 merge item 1, :10124:
the docs are written in the merge worktree before `main` is touched) or after the merge commit, never on the frozen
`main` (`06` :10125); it need not wait for A1. Proposed slug `#28-ch15-missrate`: a seeded development batch of New
Game chains to `ch5_rival_meet`, the pre-merge `main` (`934ddb7f`) against the merged tree, many seeds each, read as a
rate, its prediction hashed first. A1's docs pass checks the item exists (AM-22). **v3** (1.0 C13): v2 said "at the
next docs pass on `main`", which the freeze forbids.

**Evidence.** `mergeplan/STATE.md` line 198: "the frequency signal, 2 of 3 E0 L5 misses against 0 of 9 on main,
one-sided p about 0.045 and confounded by start states, leans against the merge). THE LEAD'S READING: whether the
merge raises the chapter 1-5 miss rate is OPEN". DIAGNOSIS :267-269 (v3; v2 said :266-268). In git: ledger #147, and
the repo note `2026-11-13-CH5-SEARCH-LOOP-FIX.md` sections 4 and 10. E0-2's 3 of 3 does not answer it either (one
trajectory per seed).

~~~old 21-a
## 1. What A1 is for, and what exists
~~~

~~~new 21-a
- **Not answered by A1 v1: whether the merge raises the chapter 1-5 miss RATE.** E0's diagnosis left it OPEN (2 of 3
  E0 L5 misses against 0 of 9 on main, p about 0.045 and confounded by start states: ledger #147 and the repo note
  `2026-11-13-CH5-SEARCH-LOOP-FIX.md` sections 4 and 10). It is a frequency question for many seeds (CLAUDE.md rule
  9); MC (2.4b) is a hard-break check and WP1a has 9 chains. It is filed as its own `03` item: a seeded batch of New
  Game chains to `ch5_rival_meet`, the pre-merge `main` (`934ddb7f`) against the merged tree, many seeds each, read as
  a rate.

## 1. What A1 is for, and what exists
~~~

### AM-22 (SHOULD, NEW) 4.4 item 8: the `06` entries A1's docs pass writes

**Why** (the lead's call 8, R8, M7, M14). 4.4 item 8 lists the `06` entries for the first draft only. The amendments
change D7 and D12, retire E0, add disk rules and raise L6. And E0 refuted the REASON `06` gives for USER RULING 55
(2), "so runs replay and can be checked" (`06` :9963), which the review found and v1's grep missed. The decision (the
frame budget is the session limit) stands and is DO-NOT-REOPEN (`06` :9965); only the reason is corrected, in a new
entry, because `06` is append-only. **v3:** (i) names the end rule (C4); (iii) adds live_chain's world cut and the
first run's PASS before WP1 (C5, C8); (iv) adds the per-job SKIP (C9). **v4** (1.0b D5): the merge's docs pass writes
that correction itself, in its `06` entry "E0's STOP and the fix-forward (2026-11-13)" (`mergeplan/DOCS-ADDENDUM.md`
G4: "AND a CORRECTION in the same entry ... 06 is append-only: the correction is a new paragraph"). So (vi)
cites it and writes one only if it is absent, and build step 0a reads `06` first (section 5).

~~~old 22-a
`03`; `05` (a KI for each new blocker holding at least 2 runs); `06`
for the 1 GB cut and CUT-WORLD, HUNG and the missing-verdict rule (D14 changed), the continue rule without the 300 MB
cap, the WAIT/DROP scheduler, the Phase A contract (D1 and D11 changed), and the persona of saved starts.
~~~

~~~new 22-a
`03` (with the chapter 1-5 miss-rate item of section 0);
`05` (a KI for each new blocker holding at least 2 runs, and for every LOOP key at 1 run: a loop that ends a leg is not
noise); `06` for the 1 GB cut and CUT-WORLD, HUNG and the missing-verdict rule (D14 changed), the continue
rule without the 300 MB cap, the WAIT/DROP scheduler, the Phase A contract (D1 and D11 changed), the persona of saved
starts, and six more: (i) D7 changed, the LOOP key and its end rule (3.8); (ii) D12 changed, part 0 (GM): A1's legs
carry the goal snapshot, `last_save` and `saved_for` reset at a `--state` start, the loss count carried, MC carries
none (3.15; rejected: A1 test-side only, with `06` 2026-11-12 item 4 NOT MET); (iii) MC replaces E0, "Item 4's bridge
retires", with its seed rule, its unknown false-STOP rate, live_chain's world cut, and its first run on A1's commit
read PASS before WP1 because part 0 moves the play digest (2.4b, 3.15 item 8); (iv) the disk rules: the per-job budget
and P_fit (2.7, 3.12, 3.13), and the per-job SKIP (3.13); (v) the L6 budget, 1,000,000 frames and 7,200 s (2.3);
(vi) cite the merge's `06` correction of USER RULING 55 (2)'s reason (the merge docs pass's entry "E0's STOP and
the fix-forward", DOCS-ADDENDUM G4: lab, deleted after the merge); write one only if it is absent (`06` :9963 gives "so
runs replay and can be checked"; E0 measured one-frame splits at outdoor warps, so a run replays only up to its first
such split); the decision (the frame budget is the session limit) stands and is not reopened.
~~~

### AM-23 (SHOULD, NEW) 3.7: the leg record's new fields, in one edit

**Why.** AM-01, AM-03, AM-08, AM-09, AM-10 and AM-20 each add fields to the leg record; one edit keeps 3.7 whole and
the edit blocks apart. Every field is read from the leg's own files; none is a D14 class. **v3** (1.0 C1; the lead's
call 1): `measures.stale` names its yardstick (`snapshot`: carried, kept or none) and is measured against the start's
kept `goals_last.jsonl` whether or not the leg carried it, so GM's GOALS-OFF arm has a number; `unknown` only when no
snapshot exists at all. `goals_sha256` follows. **v4** (1.0b D1): `window_share` is defined in the record ("(the pair's
last crossing - its first) / the leg's frames"), since v3 dropped the only clause that defined it (v2's (4a)).

~~~old 23-a
world_over_300mb, world_deleted, log}
~~~

~~~new 23-a
world_over_300mb, world_deleted, log, loop, k1_leads, stale}; `start_memory`; `bossprep`; `rides` (the next
  bullet)
~~~

~~~old 23-b
  raw: end_state.ss1 and world_last.jsonl}; `notes`.
~~~

~~~new 23-b
  raw: end_state.ss1, world_last.jsonl and, when present, goals_last.jsonl and the AI's save and memory files, 3.12};
  `notes`.
- **The fields the 2026-11-13 amendments add:**
  - `start_memory` {`goal_memory` carried or none, `goals_sha256` (of the start's kept snapshot, carried or not; null
    without one), `losses_carried` (the carried snapshot's loss count, else 0), `fallback_for` (a WP1b fallback's
    pair, else null)} (3.15, 2.1).
  - `measures.loop` {pair, crossings, crossings_raise, share of the leg's transitions, window [first, last frame],
    window_share ((the pair's last crossing - its first) / the leg's frames; reported, never a rule), last_to_end
    (the frames from the last crossing to the leg's end, which condition (4) reads), pingpong_ends (`goal_end` records
    whose reason begins `stuck: ping-pong`),
    transitions_in_leg, maps_entered, keyed LOOP or flag or none} (3.8).
  - `measures.k1_leads` {count; per lead: goal map, lead map, first frame}, read from the `tell` records of the form
    `[AI-GOALS] <map> is somewhere it has not been: first to <lead>, a seasoned player's knowledge: ...`
    (`brain/goals.py` `WAY_IN` :875, `entry_lead` :878-906, the tell :3699 at `3caf9c47`), so a chapter-5 stop or LOOP
    says whether K1 fired.
  - `measures.stale` {`snapshot`: the yardstick, the start's kept `goals_last.jsonl`: `carried`, `kept` (present at
    the start but not carried: GM's GOALS-OFF arm, 3.15 item 7) or `none`; `item_errands`: the DISTINCT tiles of that
    snapshot's `tried_items` for which the leg has a `not picked up: no item ball where it lay at (x, y) any more`
    outcome (read by the `goal_end`'s key `item:<map>|x,y`); `item_outcomes`: those outcomes, counted;
    `gone_or_unreachable`: the same message for any other tile (the fix's E makes it fire for a ball merely out of
    reach, `goals.py` `_back_to_ball` :3367-3391); `item_errands` and `item_outcomes` are `unknown` only when the start
    has no snapshot at all (`snapshot: none`: G1-G6, C1-C3), and `gone_or_unreachable` then counts every such outcome;
    `memory_line`: the AI's `[AI-WORLD] memory from ...` line}.
  - `bossprep` (AI-written lines, reported, never a class): `acting` (Story and Catcher act; a Trainer only logs,
    `brain/bossprep.py` :156); `plan` {boss, trainee species, from L, target L, the option drawn} or
    `no plan (<why>)`; `raise_goals` (`goal` records of action `raise`) and `raise_battles` (`raise battle:` lines);
    `raise_end` (budget spent, target reached, trainee left, or still active at the leg's end); `boss_losses`
    (`a battle lost on the gym map (N so far` lines) and `other_losses`; `frames_from_plan`.
  - `rides` (from the world tail): the rides used in the leg (a `uses` delta against the start's line) and the ones
    found `closed`.
~~~

### AM-24 (SHOULD, NEW) 4.1, 4.2: the new offline tests and mutants, in one edit each

**Why.** The amendments add six guards; their tests (T31-T36) and mutants go in one place each, beside the row edits
their owners make (T6 and T8 in AM-03, T9 and T27 in AM-01, T14 and T26 in AM-07, T15 in AM-10, T16 in AM-04). The
suite target stays under 60 s. T31's FAULT also runs on E0's real transitions, cut to a committed fixture by a script
(sha256 recorded); `ch5loop_tcap.world.jsonl` cannot serve there (0 transitions) and is T16's CONTROL instead.

**v3** (1.0 C1, C3, C4, C5, C9, C14d; the lead's ALSO): T31's CONTROL gets the boundary rows of the rule that remains
(40 crossings; 120,000 frames; 120,001 with a high share); T33 checks MC's world cut; T34 when a fallback may start;
T35 GOALS-OFF's cases; T36 the raise precedence with a real loop before it; the mutants follow (about 54). T31's and
T35's real fixtures come from lab folders deleted after the merge (`mergeplan/e0/runs/E0-6481`'s L5 world tails;
`fix5/runs/C_FIX/actions.jsonl`): each row says so, and what runs without them.

**v4** (1.0b D1, D3): T31's 120,001-frame row has a window share of 0.75, not 0.95: on a 600,000-frame leg whose last
crossing is 120,001 frames before its end the share is at most (600,000 - 120,001) / 600,000, just under 0.80, so 0.95
could not occur; 0.75 is above v2's dropped 0.5, so a mutant that brings a 0.5 share rule back fails that row. T31's
and T35's fixture sources are now kept by the lead in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/`
(`e0-L5/`, `c-fix/`; sha256 in its README.txt; this PC only, not git), and both rows name that folder. A1's build still
cuts T31's fixture and copies T35's tells into git, with sha256.

~~~old 24-a
| T30 | hard-coded copies | stub AI list with a 4th personality, or reordered tile fields: pin fails | 3 personalities equal `PERSONALITIES` as a set; 7 field names equal `to_dict()["tile_fields"]` (a test may import the AI) |
~~~

~~~new 24-a
| T30 | hard-coded copies | stub AI list with a 4th personality, or reordered tile fields: pin fails | 3 personalities equal `PERSONALITIES` as a set; 7 field names equal `to_dict()["tile_fields"]` (a test may import the AI) |
| T31 | LOOP key | two planted legs shaped like E0's merge into ONE LOOP key with count 2: 59 warp crossings each way, the last crossing 92,013 frames before a CLEAN-BUDGET end, next unmet `ch5_return_goods`, end ROUTE116; and 37 each way, the last crossing 20 frames before a CLEAN-CHOSEN `stuck: no progress` end, next unmet `ch5_rusturf_grunt`, end ROUTE104; a CUT-WORLD leg on the same pair joins it; the same counts cut from E0's kept L5 transitions give the same key (a committed fixture made by a script, sha256 recorded, from E0's L5 `world_last.jsonl` files, kept with their `row.json` and `ai_player.log` in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/e0-L5/`: sha256 in the keep folder's root `README.txt`, this PC only, not git; copied from `_ai_lab/s53/mergeplan/e0/runs/E0-6481`, lab, deleted after the merge; without them T31 runs on its planted legs only) | at each boundary (T14's form), on the first FAULT leg's shape: 40 crossings (20 each way): LOOP; a last crossing exactly 120,000 frames before the end: LOOP; 120,001 frames: its own key, flagged, even with a window share of 0.75 (above v2's dropped 0.5; at most 0.80 on a 600,000-frame leg with its last crossing 120,001 frames before the end; there is no share rule); 39 crossings: no LOOP; a reached leg with 118 crossings: churn table only; 60 crossings all during an ACTIVE raise: no LOOP; a `stuck: 3 battles lost` end after a loop: its own key, flagged; edge and warp crossings count alike; `pingpong_ends` counts only `goal_end` records beginning `stuck: ping-pong` |
| T32 | goal custody (part 0) | a next leg whose `AI_PLAYER_GOALS` file's sha256 differs from the kept `goals_last.jsonl`: REFUSED before launch; an MC job naming `AI_PLAYER_GOALS`: refused by `plan` | a carried snapshot arrives byte-identical, `goal_memory: carried`; a start with none runs, `goal_memory: none` |
| T33 | MC is E0's harness | an MC job whose next-leg decision differs from `continue_after`'s (a 500,000,000-byte world): fails; an MC leg cut by A1's 1,000,000,000-byte world rule: fails; an MC seed outside 6701-6799 or named by an entry: refused | an MC plan gives the 3 diagonal chains to the newest graded target, P = 3, no goal key; an MC job's world cut is `live_chain.GUARD_WORLD_BYTES` itself (read, never copied) and its profile budget lies above it |
| T34 | WP1b dependency and fallback | a WP1b job launched before its source chain's reached L5 record: fails; a fallback start taken while that chain still runs: fails; a missed chain's pair started from a G start without `fallback_for`: fails | a reached source: the job starts from that end with its snapshot; a source chain that ENDED without a reached L5: the persona's next unused G start at once, labelled, counted apart |
| T35 | stale and K1 measures | a "gone" outcome on a tile NOT in the snapshot's `tried_items` counted in `item_errands`: fails; a GOALS-OFF leg (its start's kept `goals_last.jsonl` present, not carried) whose `item_errands` reads `unknown`: fails; a K1 tell read as a fight's foe: fails | a tile in `tried_items` counted once however many outcomes; a GOALS-OFF leg with 2 "gone" outcomes on one tile of its start's kept `tried_items`: `item_errands` 1, `snapshot: kept`; a start with no snapshot (G1): `item_errands` `unknown`, `snapshot: none`; two K1 tells in the form `brain/goals.py` :3699 writes give `k1_leads.count` 2, lead ROUTE116 (the fixture: the 2 real tells of the fix round's C_FIX `actions.jsonl`, kept as `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/c-fix/C_FIX_actions.jsonl`: sha256 in the keep folder's root `README.txt`, this PC only, not git; copied from `_ai_lab/s53/fix5/runs/C_FIX/`, lab, deleted after the merge; without it, planted in that form) |
| T36 | boss-prep fields and the raise reason | a planted L6 leg ending CLEAN-BUDGET with a raise goal still ACTIVE, after 60 crossings made before the raise began, the last 100,000 frames before its end: reason `budget: a boss-prep raise still active`, its own key, never LOOP (3.8's condition (5)) | a raise that ended before the budget end: the leg's own reason; a Trainer leg: `acting` logged only, no raise counted |
~~~

~~~old 24-b
`revert_frontier.py`: about 28 single-edit mutants, one per guard above. For example:
~~~

~~~new 24-b
`revert_frontier.py`: about 54 single-edit mutants, one per guard above: about 28 for the first draft's guards and
about 26 for the 2026-11-13 amendments' (part 0's own mutants, 3.15 item 6, sit with its AI-side tests). The
amendments' mutants: the LOOP bar `>=` → `>` at 40 crossings, and `<=` → `<` at the 120,000-frame end rule; warps not
counted (KI-128's blind spot); the raise exclusion removed; the raise precedence removed (an ACTIVE raise keyed LOOP);
reached legs labelled LOOP; the LOOP key keeping `next_unmet`; LOOP applied to a discrete end; rides' counters kept,
or an unknown ride key passed; MC deciding by A1's continue rule, sending `AI_PLAYER_GOALS`, or cut at A1's 1 GB
world rule; the profile budget `>` → `>=`; P_fit off by one; a dependency SKIP made a WAIT, or DROPPED by
`--max-wait`; the raise reason dropped; every "gone" outcome counted as stale; a GOALS-OFF leg's `item_errands` left
`unknown`; a K1 tell read as a foe; goal custody unchecked; L6 back to 600,000; a fallback start unlabelled, or taken
before its source chain ends.
The first draft's, for example:
~~~

### AM-25 (NOTE, NEW) title and Review log: the spec records that it was amended

**Why.** A reader of the applied spec must see that it changed after its review, from what, and where the reasons are.
The spec grows from 60,366 bytes to about 110 KB; its own Review log says the first revision was cut under 60,000 for
size. No size ceiling covers `ai-research-notes` (`tools/story-dev/lint_docs.py` R8 covers `00-README` and 01-05 only),
so a tightening pass is the lead's call, not a gate's. **v3** (1.0 C14b, C14c; the lead's ALSO): the size is quoted in
the applied file's own CRLF bytes (section 1.4). The re-check asked for "about 98 KB", v2's applied size (98,332
bytes); v3's added text makes it about 107 KB. The header gets "amended parts read at `3caf9c47`" (new block 25-c);
the Review log names the repo note, not the lab file. **v4** (1.0b): v4's text makes the applied file about 110 KB
(section 1.4), and 25-b says the amendments were revised after "three re-checks of the revisions" (the third, of v4,
counted by the lead after it; 1.0c).

~~~old 25-a
# A1: the wide frontier probe and the trainer's runner core: BUILD SPEC (2026-11-11, revised after review)
~~~

~~~new 25-a
# A1: the wide frontier probe and the trainer's runner core: BUILD SPEC (2026-11-11, revised after review; amended 2026-11-13)
~~~

~~~old 25-b
The review's other notes (the order in `06`, seeds re-checked at build time, live work after the merge) were already in
2.5 and 5.
~~~

~~~new 25-b
The review's other notes (the order in `06`, seeds re-checked at build time, live work after the merge) were already in
2.5 and 5.

**2026-11-13: amended after the chapter 6-7 merge, E0 and E0-2** (the repo note
`2026-11-13-A1-SPEC-AMENDMENTS.md` beside this spec: 25 amendments, revised after an adversarial review of their first
draft and three re-checks of the revisions, every reason and its evidence there; the amended parts read at
`3caf9c47`). The main changes: part 0, GM (3.15), which moves the play digest; the LOOP key (3.8); L6 raised to
1,000,000 frames (2.3); MC replaces E0 as E0's harness exactly, its first run on A1's commit before WP1 (2.4b); WP1
split into WP1a and WP1b, with a per-job SKIP (2.4, 3.13); the per-job disk budget (2.7); the record's new fields
(3.7); T31-T36 (4.1). The file grew from 60,366 bytes to about 110 KB; a tightening pass is the lead's call.
~~~

**Edit 25-c** (the header's "Read at" lines, line 8; new in v3):

~~~old 25-c
the learner clone `da2fb96a`; the decomp pin `731ad5b`.
~~~

~~~new 25-c
the learner clone `da2fb96a`; the decomp pin `731ad5b`.
> **Amended parts read at** `3caf9c47` (2026-11-13: the merged tree with the chapter-5 fix; Review log).
~~~

## 4. Declined, and why

1. **(v3: no longer declined.) The LOOP override "only when the loop's window runs into the leg's end"** (R6, M8).
   v2 declined it and added a window-share rule, saying E0 forced that. It did not (1.0 C4): the
   review's rule, read with a 120,000-frame tolerance (`STORY_PATIENCE`), keys E0 T (last crossing 92,013 frames before
   its end) and E0 C (20) as one LOOP key (section 2.4). v3 applies it and drops the window share (03-b).
2. **`ch5loop_tcap.world.jsonl` as a T31 CONTROL** (R5): it holds 0 transitions. It is a T16 CONTROL instead.
3. **A main-tree arm inside A1 for the chapter 1-5 rate** (R12, option 1): out of scope by the lead's call 5; filed as
   its own item (AM-21).
4. **v1's fallback, A1 test-side only with item 4 NOT MET** (v1's AM-01): the lead chose GM (call 2); recorded as the
   rejected option in AM-22 (ii).
5. **A per-leg reset of the loss count** (R2's alternative): the lead's call is carried; no concrete harm found
   (AM-01); its consequence is measured and recorded.
6. **Pooling #101's 6 of 6 with E0-2's 3 of 3 to estimate p** (AM-05): different trees.
7. **P11's re-made B1F starts for GM's live A/B** (v1's AM-01 item 5): a P11 follow-up ordered after A1 (`06` :10114,
   :10116); the A/B uses a chain end made by part 0's own code.
8. **(v3) Call 3's share row as written** ("a share of exactly 0.50 with the last crossing 120,001 frames before the
   end gives LOOP"): call 4 drops the share clause, so under the amended rule that leg keeps its own key, flagged.
   Writing it as LOOP would contradict call 4. T31 asserts the amended behaviour at that boundary instead (v4, D1: a
   window share of 0.75, above v2's dropped 0.5 and at most 0.80 on a 600,000-frame leg with its last crossing 120,001
   frames before the end; v3's 0.95 could not occur there; the leg keeps its own key), and the other two rows of call 3
   are in T31 as asked.
9. **(v4) Copying `C:/Remote Projects/_livechain/graded-ch5` (the G1-G6 starts) into the keep folder** (D3 names
   `_livechain/` as an example): it is outside `_ai_lab/s53/`, so the lead's ruling does not put it on the cleanup
   list, and it is #101's graded record, which `live_chain.py grade` must keep re-grading unchanged (spec :84-85).
   Copying it would add 124 MiB (`du -sh`) beside a falling disk (2.8) and protect nothing the cleanup touches.

## 5. Build plan outline (on the merged `main`, after the merge commit)

| # | Part | Proof it needs | Agent h | Machine |
|---|---|---|---|---|
| 0a | Read `06` first (v4: the merge's entry "E0's STOP and the fix-forward" carries USER RULING 55 (2)'s corrected reason, AM-22 (vi)); re-read the citations at the final head; seeds (AM-17: A1's own seed check, or the kept `seeds_free.py`, 15-g); disk (AM-07; 2.8: re-measure, P_fit follows); the `06` entries of AM-22 written next; the full lane's measured hours (`07`'s merge entry; PRELANE's seconds) replace step 4's budget | quotes; the seeds FREE; `df`; the lane's hours | 0.5 | - |
| 0b | Part 0, GM (3.15): the end snapshot; the restore with its reset and carried fields; the refusals | offline FAULT and CONTROL (P11-x repro, save fields, loss count, refusals); purity gate; quick gates; the DUE suites; part 0's mutants | 3-5 | - |
| 1 | Offline core: v1's list, plus L6 at 1,000,000, the LOOP end rule and the raise precedence, `k1_leads`, the per-tile stale measure (GOALS-OFF included), WP1b's per-job SKIP and fallback, MC's `continue_after` and live_chain's world cut, the profile budgets and P_fit | T1-T36 under 60 s; each FAULT fails on a copy without its guard | 5-8 | - |
| 2 | `revert_frontier.py` (about 54 mutants, prediction hashed first); `check_anchors` `RUNNERS` and its pin 10 of 10; `run_units` `SUITES`; the lead's lane call | mutants CAUGHT as predicted; ANCHORS GATE 10 of 10 | 1-2 | about 30 min |
| 3 | Independent adversarial verifier (not a fork), then at most 2 fix rounds | its verdict | - | - |
| 4 | The full regression lane on the A1 commit (alone: 2.6's WAIT) | one lane PASS | 0.3 | about 4.4 h, budgeted from upper-bound rows (9-10 h with a rerun; step 0a puts the merge lane's measured hours here) |
| 5 | GM's live A/B (one chain L1-L5, the per-tile discriminator computed offline, then 2 seeds an arm), and P1 | 3.15 item 7; P1 PASS = (a) and (b) | 0.8 | 1.5-2 h |
| 6 | MC's first run, on the A1 commit's stage (part 0 moved the play digest; E0's replacement) | the 2.4b reading: PASS, a MUST before WP1 | 0.3 | 30-45 min |
| 7 | `reserve-band` and the trainer smoke | `ledger.py --check`; nothing tracked changed | 0.3 | about 15 min |
| 8 | WP1: WP1a, then WP1b as WP1a's L5 legs end (the per-job SKIP), then P2 | WP1 CONTROLS (13-a); P2 PASS (12-d) | 1 | 4-5 h at P = 8 (9 h worst) |
| 9 | Report and docs: 07, 04, 03, 05, 06 (AM-22); Tier 1; commits by explicit path | Tier 0 green; Tier 1 PASS | 1-1.5 | - |

Total: about 13-20 h of agent time; about 11-13.5 h of machine time at P = 8 (about 22.5 h worst). At 46.75-47.95 GB
free P_fit is 3 for A1 and 2 for MC (WP1 alone at least about 9.3 h); at 46.21 GB (10:50 PM 2026-11-13) it is 2 for
A1 and 1 for MC (WP1 alone at least about 14 h; section 2.8); under 45 GB nothing starts. About 3-4 days of calendar.
Estimates.

## 6. Not checked, not proven

- No emulator, test, gate or A1 code was run (A1 is not built). The `tools_v2/*.py`, `tools_v3/*.py` and
  `tools_v4/*.py` scripts only read files. The one write outside this folder (v4, D3) is the keep folder's 17 copies
  and its appended README section; none of the copied scripts was run.
- Part 0 is designed, not built: whether `check_purity.py` needs an edit, and whether `restore_goals` needs a session
  line at a `--state` start, are not checked. Which files the play digest covers was not read
  (`make_arm11 tree_digest(play_only=True)`); part 0 moves it because `mode.py` and `game_memory.py` are play code.
- No Catcher L6 was ever measured. Its 636,000 frames come from Story's ratio (1.156) times the Catcher budget.
- The LOOP rule rests on two loop legs (E0 T and C L5); the 40-crossing bar and the 120,000-frame end tolerance are a
  calibration on those two, not a measured separation over many legs. Chapters 6-7's own ping-pongs (KI-134) were not
  measured with it.
- The carried-loss path in P2's CONTROL (12-d) is unseen in 8 of 8 runs from C1, all with 0 carried; how often a
  WP1a chain enters chapter 6 with losses is a measured consequence on 9 chains (2 with 2 losses), not a rate.
- PRELANE finished with all three drivers "OVERALL: PASS" and no verdict changed (2.8), but on `3caf9c47`, one run per
  mutant, the three at once under load: its seconds are not alone-times. The merge's full lane started at 10:46 PM on
  `fa9f073d`; its hours are not in this note.
- The disk fell from 53.2 GB (8:10 PM) to 47.95 GB (10:00 PM) and 46.21 GB (10:50 PM), unevenly (2.8); the cause was
  not found (the lab's test leftovers in Temp are about 1.4 GB in all, and the tuner's newest run folder was 431 MB).
  A1's P, WP1's hours and A1's 45 GB start floor depend on it.
- T31's real-transition fixture and T35's real K1 tells are kept on this PC only (`_ai_lab/keep/2026-11-13-a1-sources/`,
  not git); the fixture is not cut yet. A1's build cuts it and commits both with their sha256 (24-a).
- The spec's own unamended lines still name lab paths (1.2's Lab kit row is amended by 15-g; 2.1's C rows, 2.5's
  seed-scan command, 3.3's "the lab's `build_stage11.py`" and :40's `_ai_lab/s53/bp1r2/out/control2/results.json`, a
  KI-130 citation the build does not need, are not). For the files the build needs, a NEW block in the same section,
  or 1.2, names the kept copy (01-c, 15-g, 14-a); no further old text was added for them.
- MC's false-STOP rate is unknown (AM-05). E0-2 is one trajectory per seed.
- The carried loss count's effect on BRAWLY is a measured consequence on 9 chains and 4 wins, not a rate.
- Whether a GM chain's chapter-5 end holds a discriminating tile is unknown until that chain exists (3.15 item 7 says
  what to do if it does not).
- The time and cost figures are estimates. The full lane's 15,931 s and 12,879 s rows are PROVISIONAL upper bounds;
  since `fa9f073d` three other rows hold a side lane's kill times (lower bounds there). "About 4.4 h" is a budget.
- The old texts were checked against the spec as it is now (md5 `0d5e04fc...`). If the merge's docs pass edits the
  spec first, re-run `check_v2_oldtext.py`, `recheck/count_oldtext.py` and `recheck3/count3.py` before applying.
  **2026-11-14 (the merge's docs pass):** it did edit the spec (two ledger-id bridges, G10, and an "AMENDMENTS
  PENDING" flag on its blank line 2, so no line moved; now 60,693 B, md5 `108df6e0...`). The three checkers are kept in `C:/Remote Projects/_ai_lab/keep/2026-11-13-a1-sources/checkers/`
  (this PC only; two byte-equal to the lab's; the kept `count3.py` now folds CRLF to LF when it reads this note,
  because the repo checks this note out with CRLF and the lab's original then parsed 0 blocks, "RESULT: SOME CHECK
  FAILED" over a correct note) and were re-run on the edited spec and this note, LF and CRLF (each as
  `py -3.12 -B -I <checker> <spec> <note>`): "ALL OLD TEXTS EXACTLY ONCE, NO OVERLAP", "NOT EXACTLY ONCE: none",
  "RESULT: ALL CHECKS PASS". Re-run them if the spec changes again before A1 applies this note.
- The applied spec was read only in memory (v3: `check_v2_oldtext.py --dump-applied`, printed; v4:
  `tools_v3/applied_check.py`, its tables and line widths), never written; `lint_docs.py` and
  `audit_doc_consistency.py` were not run on it, because nothing was applied.
- "MC is E0's harness exactly" is a design (`continue_after`, live_chain's world cut and a profile budget above it,
  inside A1's runner); no MC has run. T27, T33 and T14 are its proof. A1's 45/40 GB floors still apply to MC: they
  protect the tuner and never decide play. The 1.75 GB budget's 250 MB margin over the cut rests on estimated
  `actions.jsonl` and memory sizes (2.7), not a measured MC profile.
- WP1b's per-job SKIP is a new scheduler state; whether waiting on a slow WP1a chain stretches WP1's machine time
  beyond 4-5 h was not modelled beyond the job-hour sum. With the SKIP, other ready jobs fill the slots meanwhile.
