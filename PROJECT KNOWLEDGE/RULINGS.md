> **06 wins. This file is a finding aid; quote the section, never this table.**

# RULINGS index (generated from `06-DECISIONS-LOG.md`; never edit by hand)

- Regenerate: `py -3.12 tools/story-dev/build_rulings_index.py` | gate: `py -3.12 tools/story-dev/build_rulings_index.py --check`
- Look up a question first: `py -3.12 tools/decomp_lookup.py ask "<words>"` (it quotes 06 itself).
- Judgments (marker vs mention, supersession, which heading defines a repeated number) live in `rulings-overlay.json`; a section not in it is ACTIVE with no flag.
- Line numbers are HINTS; the id `<date>-<sha1(heading)[:6]>` is the key.

## Do not reopen

| id | 06 line | do not reopen |
|---|---|---|
| `2026-07-18-2d9552` | 86 | Keeping the user's Emerald ROM tracked in the private repo (revisit only if the repo is ever made public). |
| `2026-08-23-43fd61` | 3119 | The tracked Emerald ROM, now BOTH tree entries (custom-pokebot/roms/ and sandbox-pokebot/roms/): keep as is, fix the docs. |
| `2026-09-05-cc4d7b` | 4392 | NOT BINDING: this section is SUPERSEDED by 2026-09-05-079ffd ("THIS SUPERSEDES BOTH OF TODAY'S EARLIER LEG-9 DECISIONS"), so its two 'do not re-propose' lines (a Poke Center heal before leg 9; the (33,17) bypass) do not stand on their own, and 06:4479 calls the bypass claim an artifact of the probe. Read 079ffd. |
| `2026-09-12-125f6e` | 5109 | "Why not just train the laggard to the boss's level?" (ruled 2026-09-10 with arithmetic: L40->L47 = 285,167 frames against a 250,000 ceiling). The flag-OFF decision of this section is superseded; this question is not. |
| `2026-09-12-f83fd9` | 5167 | The VALUE question of POKEBOT_MAINTAIN (top-up): the user ruled it ON after being shown it measures neutral (32x310 and 32x120 per arm). |
| `2026-09-16-42f48d` | 5331 | The three rejected post-whiteout money options (adaptive re-stock, attempt cap, re-earning trip): the user chose SPEND DOWN BEFORE ENTERING. |
| `2026-09-17-5edc72` | 5581 | post_grind_L60.ss1 is a dead branch: not grinded from, not repaired, not cited as "13 levels we already paid for"; the L75 grind starts from post_ch24ready.ss1. |
| `2026-09-17-11cd93` | 5638 | Fetching another TM13, buying one, or tutoring an Ice move onto Wailord (06:5661). |
| `2026-09-17-c1970f` | 5808 | #24-trainestimatorcal (the item filed against the train estimator's cost model): withdrawn the same day; the estimator is ~18% pessimistic on frames (07 2026-09-08 :24637-24641). |
| `2026-09-18-7c5632` | 6196 | Victory Road B1F as the grind ground: off the table (user RULING 2 of 2026-09-18 picked the room before the Victory Road exit, for round-trip speed) unless a new ruling says otherwise. |
| `2026-09-18-9c3dff` | 6457 | Settled because measured: the TRAINING_GRASS row never lands without its AREA_PREREQ row; adding it does not make Victory Road huntable; _MAX_TRAINING_TRAVEL_LEGS = 4 is not binding. NOT settled (reopen freely): the ranking-level change from inside Victory Road, a companion narrowing of _counter_area_allowed. |
| `2026-09-18-dcfea7` | 6587 | Promoting Victory Road into TRAINING_GRASS (#24-trainingbrackets closed without a code change). Reopen freely: the heal-map fallback (#24-healmapfallback) and B1F's Rock Smash table if USER RULING 2's B1F exclusion is ever revisited. |
| `2026-09-23-5c88b3` | 6816 | Boxing Zigzagoon or Castform to make the L65-75 floor easier: the user ruled (a), train all six on the Fly ladder. Read with 13@2026-09-25 (the battle team is L65-75, the roster is free), which moved the team boundary but not the floor. |
| `2026-09-25-bd0d61` | 6967 | What the bot does on LOSING the Elite Four: restock, then retry (authorised and unbuilt is not undecided). |
| `2026-09-27-e47f76` | 7636 | What the user meant by the desert fossil request (#27-desertfossil): get the desert fossil, choosing one at random each run; the mechanics are UNVERIFIED (recon the decomp first). |
| `2026-09-28-f65547` | 8022 | The three RULING 20 §8 policy questions: money for Poke Balls (23), catching while hurt or training (24), the attempt cap (25). |
| `2026-09-29-33b616` | 8057 | The five questions of 2026-09-28-r23-25-DESIGN.md §5: Q1 the ball budget (no per-run ceiling, bounded batches), Q2 stocks (kept all game, RULING 26), Q3 what "rare" means (already answered: check the notes), Q4 hard catches (keep trying), Q5 giving up (never on a wanted rare); and RULING 27 (healing items in KEY battles only). |
| `2026-10-21-58fe1b` | 9512 | The four step-1 operations questions: backups go to Z:, the TWO ops scheduled tasks (the nightly backup and the watchdog) approved at Claude's judgement (not scheduled tasks in general), compressed raw logs kept forever, the 3 % weekly-meter calibration. |
| `2026-10-21-d1e589` | 9575 | Whether the watchdog's toast reaches the user and whether its 30-minute window flash is acceptable (both yes, 2026-10-21; the monitor stays off). |
| `2026-10-21-3b21a7` | 9582 | Whether the AI may know bosses' held items (yes) and their exact stats / IVs and AI flags (no), for S3-4's trainers.json (2026-10-21). Not the spec's other two items (species shares, sight ranges). |
| `2026-10-21-bd628b` | 9593 | Whether the AI sees which species the scripted bot chose (no) and whether it knows trainers' positions and sight ranges (yes), for S3-4 (2026-10-21). |
| `2026-10-28-7d117a` | 9792 | Whether cloud jobs can be paid from the user's $250 credit (no: the weekly plan pays, measured and documented 2026-10-28); the cloud phase stays shelved unless the user re-opens it. |
| `2026-10-28-abc2b6` | 9807 | Whether games recovered from a crashed tuner cycle count toward the strategy ranking (yes) and whether ai0031's 12 games lost on 2026-10-17 are backfilled (no), for E2 + O8 (2026-10-28). |
| `2026-10-28-35b2cb` | 9814 | While the project is paused: do not delete the tuner's ai-agent/STOP, re-enable its three Windows tasks (Pokebot-AI-Learner-Autostart, Pokebot-Ops-Watchdog, Pokebot-Ops-Backup) or start it until the user says to resume; do not re-ask when or how to pause (2026-10-28). |
| `2026-10-28-77ea25` | 9832 | Do not park or pause the bot tuner or the project (no ai-agent/STOP file, no disabled Pokebot-* task) unless the user asks; do not re-ask whether to pause (2026-10-28). |
| `2026-10-29-2afa57` | 9904 | Do not re-ask U1 (the AI's big-moment save list: as built), U2 (a session ended by its time or frame limit may be continued from its last save: YES) or the reset question (a refused reset combination ends that game for good) (2026-10-29). |
| `2026-10-30-c2a92b` | 9942 | Do not re-ask whether the 24/7 trainer (ai-agent/ learner) should train the AI player itself, nonstop, chapter by chapter: it should (2026-10-30). |
| `2026-10-31-911bb5` | 9958 | Do not re-ask whether the AI trainer's practice runs from the AI's own saves are allowed (yes, with a New Game test after a few), or which limit ends a session (the frame budget; the clock is a backstop) (2026-10-31). |
| `2026-11-05-577173` | 10020 | Do not reopen merging a development pass as a graded claim, or replacing the general instructed choice with a scene-specific (POKéNAV-only) menu script (2026-11-05). |
| `2026-11-06-dc449a` | 10029 | Do not reopen an in-process defense in live_chain.py against code written to disable the grader (the purity gate's and R9's job), or grade DIR trusting results.json over the ledger (2026-11-06). |
| `2026-11-07-08dac8` | 10039 | Do not re-ask what a seasoned player does against a boss the party loses to: all three (train the whole team; a counter judged by its resistances AND its moves' type advantages; smarter fights) are viable for every gym leader, boss and the Elite Four (2026-11-07). |

## Repeated USER RULING numbers (a number is not a key)

| number | id | date | 06 line | relation |
|---|---|---|---|---|
| 12 | `2026-09-23-5c88b3` | 2026-09-23 | 6816 | defines 12@2026-09-23 |
| 12 | `2026-09-25-bd0d61` | 2026-09-25 | 6967 | defines 12@2026-09-25 |
| 12 | `2026-09-26-38271b` | 2026-09-26 | 7300 | applies `2026-09-23-5c88b3` |
| 12 | `2026-09-27-57614f` | 2026-09-27 | 7799 | applies `2026-09-25-bd0d61` |
| 13 | `2026-09-23-8c1057` | 2026-09-23 | 6860 | defines 13@2026-09-23 |
| 13 | `2026-09-25-40ef56` | 2026-09-25 | 7101 | defines 13@2026-09-25; amends `2026-09-18-e97c57` |
| 21 | `2026-09-26-6d6b8c` | 2026-09-26 | 7421 | defines 19@2026-09-26, 20@2026-09-26, 21@2026-09-26 |
| 21 | `2026-09-27-360ecb` | 2026-09-27 | 7765 | amends `2026-09-26-6d6b8c` |
| 23 | `2026-09-28-f65547` | 2026-09-28 | 8022 | defines 23@2026-09-28, 24@2026-09-28, 25@2026-09-28 |
| 23 | `2026-09-29-33b616` | 2026-09-29 | 8057 | defines 26@2026-09-29, 27@2026-09-29; amends `2026-09-28-f65547` |
| 25 | `2026-09-28-f65547` | 2026-09-28 | 8022 | defines 23@2026-09-28, 24@2026-09-28, 25@2026-09-28 |
| 25 | `2026-09-29-33b616` | 2026-09-29 | 8057 | defines 26@2026-09-29, 27@2026-09-29; amends `2026-09-28-f65547` |
| 39 | `2026-10-15-17dd10` | 2026-10-15 | 9386 | defines 39@2026-10-15 |
| 39 | `2026-10-16-aaa49a` | 2026-10-16 | 9482 | applies `2026-10-15-17dd10` |
| 47 | `2026-10-27-5b5b7d` | 2026-10-27 | 9785 | - |
| 47 | `2026-10-28-7d117a` | 2026-10-28 | 9792 | applies `2026-10-27-5b5b7d` |
| 53 | `2026-10-29-2afa57` | 2026-10-29 | 9904 | defines 53@2026-10-29 |
| 53 | `2026-10-30-cc5521` | 2026-10-30 | 9927 | applies `2026-10-29-2afa57` |

## Superseded or withdrawn

| id | 06 line | status | by | title |
|---|---|---|---|---|
| `2026-07-17-fb3c6f` | 27 | SUPERSEDED | `2026-07-17-c7d216` | 2026-07-17 — Installer enhancement will ADAPT, not literally apply, the base64 pattern |
| `2026-08-23-908a3b` | 3156 | WITHDRAWN | `2026-08-23-576b9b` | 2026-08-23 — RULING: the whiteout-RECOVERY path is permanently exempt from `_check_abort()` |
| `2026-09-05-11b4ba` | 4352 | SUPERSEDED | `2026-09-05-079ffd` | 2026-09-05 — the leg-9 attrition fix will be a POKÉ CENTER heal, not bag items, and not grinding |
| `2026-09-05-cc4d7b` | 4392 | SUPERSEDED | `2026-09-05-079ffd` | 2026-09-05 (evening) — REVERSAL: the leg-9 fix is TWO SINGLE BATTLES. The heal AND the bypass are measured dead. |
| `2026-09-12-125f6e` | 5109 | SUPERSEDED | `2026-09-12-f83fd9` | 2026-09-12 — `#24-maintain` stays DEFAULT-OFF after its A/B, and the A/B is kept rather than re-run |
| `2026-09-12-e757a6` | 5138 | SUPERSEDED | `2026-09-12-f83fd9` | 2026-09-12 (09:03) — `#24-maintain`: the benefit question is ANSWERED (no), and the flag stays OFF |
| `2026-09-17-5bafb0` | 5866 | SUPERSEDED | `2026-09-17-b69c79` | 2026-09-17 (late) — THE RETRACTION-COVERAGE CHECK IS **ENFORCING**, NOT ADVISORY |
| `2026-09-26-38271b` | 7300 | SUPERSEDED | `2026-09-26-cc050f` | 2026-09-26 — `#26-ch24organic` R1 REFUSES AT THE PRODUCTION FLOOR (USER RULING 12 APPLIED LITERALLY) — ⚠ RELAXATION IS THE USER'S CALL, FLAG |
| `2026-10-28-35b2cb` | 9814 | SUPERSEDED | `2026-10-28-77ea25` | 2026-10-28 — USER RULING 49: PAUSE the project at the end of the bot tuner's round ai0053 (about 4:28 PM 2026-10-28): park the tuner, switch |

## All 367 sections (newest first)

| id | 06 line | user rulings | flags | title |
|---|---|---|---|---|
| `2026-11-07-08dac8` | 10039 | 58 | DO-NOT-REOPEN | 2026-11-07 — USER RULING 58: against a boss the party loses to, all three plans are viable (train the whole team, bring a counter, fight smarter) for BRAWLY and |
| `2026-11-06-dc449a` | 10029 |  | DO-NOT-REOPEN | 2026-11-06 — The graded chain driver `live_chain.py`: a WRITTEN threat model, "grade DIR is never better than the ledger", its refusals and exit codes, and a st |
| `2026-11-05-577173` | 10020 |  | DO-NOT-REOPEN | 2026-11-05 — Chapter 5's stops: a GENERAL instructed choice for forced menus; the grunt as data; the next graded test is a New Game to the end of chapter 5 (pun |
| `2026-11-01-6cfa03` | 10007 |  |  | 2026-11-01 — Chapter 5's eight milestones wired into the AI from the cloud note, after two independent checks; six choices, and what the first development probe |
| `2026-11-01-bab294` | 9998 | 57 |  | 2026-11-01 — USER RULING 57: keep progressing on the extra credit, with the cloud kept set up; the measurement: at a full weekly meter a cloud job bills the EXT |
| `2026-10-31-2d2d7e` | 9991 |  |  | 2026-10-31 — The KI-128/KI-129 held-out: K8.EDGE_WINDOW is REPORTED, not graded; the graded bars stay what the fix claims |
| `2026-10-31-76810c` | 9983 |  |  | 2026-10-31 — KI-129 Part B: an edge ping-pong is a ping-pong (a sliding "nothing new" window for edges, routes exempt); an explore goal that ends in one is now  |
| `2026-10-31-8a3e66` | 9975 |  |  | 2026-10-31 — KI-128's fix reads the game's MAP TYPES through a declared loader (`ai_player/knowledge/atlas.py`), the AI player's first static-knowledge loader;  |
| `2026-10-31-979d5c` | 9967 | 56 |  | 2026-10-31 — USER RULING 56: the $50 extra credit may be spent now, to start the AI work before the weekly reset; the user re-opens the cloud-credit question (m |
| `2026-10-31-911bb5` | 9958 | 55 | DO-NOT-REOPEN | 2026-10-31 — USER RULING 55: practice runs from the AI's own saves are allowed, but a NEW GAME test must follow a few of them; the session limit is Claude's cal |
| `2026-10-30-ef2a3b` | 9950 |  |  | 2026-10-30 — The AI trainer's design: MEASURE FIRST (A0, A1), then the top blocker's skill build, then the trainer inside the learner; R12 comes after U2b |
| `2026-10-30-c2a92b` | 9942 | 54 | DO-NOT-REOPEN | 2026-10-30 — USER RULING 54: the 24/7 trainer is to TRAIN THE AI PLAYER ITSELF, nonstop, chapter by chapter (or as Claude designs it), because the AI has been s |
| `2026-10-30-297528` | 9935 |  |  | 2026-10-30 — U2a's verification findings V1-V3 fixed; an old launch line with no instrument record fails closed |
| `2026-10-30-cc5521` | 9927 | 53 |  | 2026-10-30 — U2a BUILT: a session ended by its time or frame limit may be continued (USER RULING 53), judged by the host's own record, and every continue tells  |
| `2026-10-30-b8f22e` | 9916 |  |  | 2026-10-30 — R1 + R2's FOLLOW-UP BUILT: the build's decisions (two STOPs ruled on, the CHAIN kill rule, what was deferred to U2's build) |
| `2026-10-29-2afa57` | 9904 | 53 | DO-NOT-REOPEN | 2026-10-29 — USER RULING 53: the user approved the open asks and left the three open design questions to Claude's recommendations (U1 the list as built; U2 YES, |
| `2026-10-29-47a9a5` | 9893 |  |  | 2026-10-29 — R1 + R2 BUILT: the AI saves like a person, CONTINUEs after a kill, and its memory survives it (the build's decisions) |
| `2026-10-29-eb1c46` | 9884 | 51, 52 |  | 2026-10-29 — USER RULINGS 51 and 52: the AI saves like a person, and never reloads to undo a loss (one later exception, deferred: a stationary legendary's faile |
| `2026-10-29-753e92` | 9878 |  |  | 2026-10-29 — R1 + R2's save/kill probe: a TEST-SIDE tool in no lane, and what it hands R1's design (WHEN the AI saves is not decided here) |
| `2026-10-29-92e464` | 9871 |  |  | 2026-10-29 — KB2's input hashes ignore line ends: folded in the hash, not fixed by an `eol` attribute |
| `2026-10-29-d6802c` | 9855 |  |  | 2026-10-29 — R5 (a free screen before "done"): what the settle chose, the rulings on the build's open questions, and where the build departs from its spec |
| `2026-10-28-f8ae9d` | 9841 | 50 |  | 2026-10-28 — The park tool (USER RULING 50): how `tools/ops/park_tuner.py` parks and resumes the bot tuner, and where it departs from its spec |
| `2026-10-28-77ea25` | 9832 | 50 | DO-NOT-REOPEN | 2026-10-28 — USER RULING 50: the PARK is CANCELLED; the user continues this project, and the safe park/pause stays available for when the user asks |
| `2026-10-28-495011` | 9821 |  |  | 2026-10-28 — E2 + O8 built: what the journal, the recovery case, the `.bak` check and the crash-loop breaker chose, and where the build departs from its spec |
| `2026-10-28-35b2cb` | 9814 | 49 | DO-NOT-REOPEN SUPERSEDED | 2026-10-28 — USER RULING 49: PAUSE the project at the end of the bot tuner's round ai0053 (about 4:28 PM 2026-10-28): park the tuner, switch off its Windows aut |
| `2026-10-28-abc2b6` | 9807 | 48 | DO-NOT-REOPEN | 2026-10-28 — USER RULING 48: games that finish before a crash COUNT toward the tuner's ranking; the 12 games lost on 2026-10-17 (ai0031) are NOT added back |
| `2026-10-28-452f91` | 9799 |  |  | 2026-10-28 — L5.SHOPPED, built for ruling 46: a told purchase of ANY item, and one counted purchase per told purchase |
| `2026-10-28-7d117a` | 9792 | 47 | DO-NOT-REOPEN | 2026-10-28 — USER RULING 47's measurement: the $250 credit did not move, and the official docs say the weekly plan pays for cloud jobs, so the cloud phase is SH |
| `2026-10-27-5b5b7d` | 9785 | 47 |  | 2026-10-27 — USER RULING 47: use the $250 cloud credit before it expires (2026-11-04) if a cloud job is billed to it; measure that first, and shelve it if the w |
| `2026-10-27-94e439` | 9778 | 46 |  | 2026-10-27 — USER RULING 46: the launcher's "it shopped" means ANY purchase, not only POKé BALLs |
| `2026-10-27-ec688e` | 9773 |  |  | 2026-10-27 — Step 5.3's graded result is FAIL on 3 of 38 counted checks: accepted as information, not retuned; step 5.3 is done |
| `2026-10-27-0ab496` | 9767 |  |  | 2026-10-27 — Step 5.3 stage B step 3: the final bounds are the re-sourcing build's candidates, all 20 kept |
| `2026-10-27-0bc932` | 9760 |  |  | 2026-10-27 — Step 5.3 stage B step 1: phase 2's STOP and STOPDEAD also replay LOSE3's runs; a re-grade judges phase 2 by the rule its sweep was played under |
| `2026-10-25-11c24a` | 9754 |  |  | 2026-10-25 — Step 5.3's grader: a MISSING game read is left out of a check and named, never counted as a value |
| `2026-10-25-467d45` | 9740 |  |  | 2026-10-25 — Step 5.3's re-sourcing plan: the addendum's open items decided |
| `2026-10-24-eba575` | 9715 |  |  | 2026-10-24 — Step 5.3 A2's decision addendum: the 39 B1-debt rows decided |
| `2026-10-23-633c48` | 9705 |  |  | 2026-10-23 — Technical decisions of step 5.3 stage A1 (Claude's calls) |
| `2026-10-22-60ce7d` | 9687 |  |  | 2026-10-22 — KB2 extraction asserts only what an independent exhaustive scan re-checks; `unknown` accepted over fix-spec-2's Beldum answer |
| `2026-10-22-8000d8` | 9668 |  |  | 2026-10-22 — S2-1b part 2 (the `03-PUNCH-LIST.md` slim-down) DEFERRED after its recon; the queue reorders to KB2 slice 2 first |
| `2026-10-22-23d549` | 9643 |  |  | 2026-10-22 — S2-1b (the handoff slim-down): SNAPSHOT, THEN REWRITE; and the queue order after it |
| `2026-10-22-d95db5` | 9636 |  |  | 2026-10-22 — Technical decisions of O5, the consult novelty gate (Claude's calls) |
| `2026-10-22-bce135` | 9629 |  |  | 2026-10-22 — Technical decisions of the chapter-pack tool, A5 (Claude's calls) |
| `2026-10-22-74ca34` | 9621 |  |  | 2026-10-22 — Technical decisions of S3-4 slice 1, KB2 (Claude's calls) |
| `2026-10-21-20a928` | 9612 |  |  | 2026-10-21 — Evidence identity = the code under test (#28-evidence-identity; Claude's call) |
| `2026-10-21-1eff0e` | 9602 |  |  | 2026-10-21 — Technical decisions of S4-1, the regression runner (Claude's calls) |
| `2026-10-21-bd628b` | 9593 | 45 | DO-NOT-REOPEN | 2026-10-21 — USER RULING 45 (S3-4's two other user items): the AI does NOT see which species the bot chose; it DOES know trainers' positions and sight ranges |
| `2026-10-21-3b21a7` | 9582 | 44 | DO-NOT-REOPEN | 2026-10-21 — USER RULING 44 (the S3-4 boss-knowledge question): the AI KNOWS each boss Pokémon's held item; it does NOT know their exact stats (IVs, hidden stat |
| `2026-10-21-d1e589` | 9575 | 43 | DO-NOT-REOPEN | 2026-10-21 — USER RULING 43 (the watchdog's human check): the test toast arrived; a brief window flash every 30 minutes is fine; the monitor stays off |
| `2026-10-21-07367b` | 9566 |  |  | 2026-10-21 — Technical decisions of S2-1, the doc-size ratchet (Claude's calls) |
| `2026-10-21-a23037` | 9554 |  |  | 2026-10-21 — Technical decisions of the A6 and stage-template review rounds (Claude's calls) |
| `2026-10-21-7e2320` | 9544 |  |  | 2026-10-21 — Technical decisions of the O6 + O7 / O1 / KB1 step-5 round (Claude's calls) |
| `2026-10-21-1bd257` | 9531 | 42 |  | 2026-10-21 — Technical decisions of the O3 / O4 / P3 / KB1 / S3-2 round (Claude's calls; USER RULING 42 is the user's) |
| `2026-10-21-58fe1b` | 9512 | 42 | DO-NOT-REOPEN | 2026-10-21 — USER RULING 42 (the step-1 operations questions): backups go to Z:, the scheduled tasks are approved, compressed raw logs are kept forever, and a w |
| `2026-10-16-32da14` | 9496 | 41 |  | 2026-10-16 — USER RULING 41 (confirmation of the overall goal): a deployable AI agent that plays the WHOLE game on its own through the emulator, like a person,  |
| `2026-10-16-aaa49a` | 9482 | 39 |  | 2026-10-16 — "P2" decided by Claude (USER RULING 39: technical): the shares of TIME stay REPORTED, never graded; human-likeness is graded by what curiosity YIEL |
| `2026-10-15-040755` | 9457 |  |  | 2026-10-15 — The CLOUD PHASE: the user's $250 promotional cloud credit buys THINKING work that needs no emulator. Nothing may get stuck there, and the setup rev |
| `2026-10-15-994eef` | 9420 | 40 |  | 2026-10-15 — USER RULING 40: the AI is a SEASONED PLAYER (it knows Pokemon and Emerald and remembers past games) who still plays every new game like a person, w |
| `2026-10-15-17dd10` | 9386 | 39 |  | 2026-10-15 — USER RULING 39: the trainer runs and IMPROVES on its own when Claude or the internet is unavailable, QUEUES its questions and reconnects by itself; |
| `2026-10-15-1ae414` | 9367 | 38 | cue | 2026-10-15 — USER RULING 38 follow-up: consult KEPT ON (it CORRECTS this day's "consult OFF" entry); the learner at 12 lanes; the lean process to start after st |
| `2026-10-15-f882fc` | 9333 |  |  | 2026-10-15 — Usage-safe operation: the learner needs no Claude (consult OFF), restarts itself at logon, and the AI player's rounds go LEAN from step 5.3 |
| `2026-10-15-815b9c` | 9316 |  |  | 2026-10-15 — The AI player's order of work: step 5.2 = safety gates + PRODUCTIVE curiosity (on chapters 1-2), then 5.3 = chapter 3, then 5.4 = chapter 4 with th |
| `2026-10-15-f4f400` | 9301 |  |  | 2026-10-15 — The AI player's development rounds: a fix round only for a FAILURE; the full regression of every step at a CHAPTER boundary |
| `2026-10-15-a2b22c` | 9293 | 38 |  | 2026-10-15 — USER RULING 38: the learner drops to 8 lanes, and goes back to 16 when the AI player gives it something new to test |
| `2026-10-14-969c77` | 9277 |  |  | 2026-10-14 — AI player step 5 is COMMITTED with the verifier's pacing failure OPEN; step 5.1 fixes it and the review's findings BEFORE chapters 3-4 are attempte |
| `2026-10-07-862657` | 9266 |  |  | 2026-10-07 — The AI player's purity hardening STOPS at step 0.1; the remaining residuals are documented limits, and work moves to the AI itself (step 1, EYES) |
| `2026-10-07-389c41` | 9248 | 37 |  | 2026-10-07 — USER RULING 37: the AI player v1 decisions (answers to the design draft's §9) |
| `2026-10-03-0bc438` | 9240 | 36 |  | 2026-10-03 — USER RULING 36, addendum: only the PRODUCTION version needs an API key; dev/prototype/test versions consult Claude through the chat (reports and lo |
| `2026-10-03-bd23a6` | 9230 | 36 |  | 2026-10-03 — USER RULING 36: the AI player's eyes and its Claude coach. Perception by memory injection (as the bot does); the first version asks Claude; later v |
| `2026-10-03-c60e81` | 9220 | 35 | cue | 2026-10-03 — USER RULING 35: the AI PLAYS THE GAME ITSELF; the bot is only its TEACHER (supersedes ruling 34's "AI-only flags in the bot's code" and ruling 31's |
| `2026-10-03-852e91` | 9211 | 34 |  | 2026-10-03 — USER RULING 34: the focus is the AI version; the bot is parked, not abandoned; AI concepts reach the bot only when the user says so |
| `2026-10-03-b6d7bf` | 9194 | 33 |  | 2026-10-03 — USER RULING 33, addendum: PC team swapping for situations (hunting, legendaries, gym and Elite Four counters), VARIED across playthroughs; Game Cor |
| `2026-10-03-eaffe3` | 9135 | 33 |  | 2026-10-03 — USER RULING 33: the human-play design. Personalities, catching, training with type and recoil awareness, no speedrunning, roaming (not spinning), a |
| `2026-10-03-b3e98e` | 9112 | 32 |  | 2026-10-03 — USER RULING 32: the AI's ultimate goal is HUMAN-LIKE, organic play, never a speedrun; the learner's progress-only score is a partial proxy |
| `2026-10-03-2484db` | 9079 |  |  | 2026-10-03 — The first WALL knob: `POKEBOT_BOSSMODE_TOPUP` (boss mode's +1 top-up becomes learnable); the screen grows to Hadamard-16; genome ids hash only chan |
| `2026-10-03-febc24` | 9040 |  | cue | 2026-10-03 — The AI learner runs from its OWN deployment clone and updates itself between cycles (supersedes "never runs git" in the RULING 31 entry); its knobs |
| `2026-10-03-23ae4e` | 8998 | 31 |  | 2026-10-03 — USER RULING 31: the HYBRID direction. The story bot is parked; the Emerald AI strategy learner (`ai-agent/`) is built on top of it |
| `2026-10-02-dfea15` | 8978 |  |  | 2026-10-02 — design v2 step 14 graded: the registered verdict is REPORTED but not RELIED ON; the corrected re-grade is EXPLORATORY; promotion is blocked |
| `2026-10-01-bee57d` | 8954 |  |  | 2026-10-01 — `#27-battleeq` (KI-108): fix `BattleState.__eq__` as the DEFAULT, with a fault switch; the evidence is a forced second caller, not an ordinary-batt |
| `2026-10-01-c8854b` | 8926 |  |  | 2026-10-01 — design v2 step 14 T4: STOP-3 counts only ACTING package tags; E4 is a hand read, not a simulation (after its adversarial pass) |
| `2026-10-01-1ebcca` | 8910 |  |  | 2026-10-01 — design v2 step 14 T2/T3: how the comparator handles what the DESIGN left to the tool (after its adversarial pass) |
| `2026-10-01-48ecb7` | 8897 | 29 |  | 2026-10-01 — `#27-shellhook`: the hook's scope after its adversarial pass (USER RULING 29) |
| `2026-10-01-2c582c` | 8885 | 29 |  | 2026-10-01 — USER RULING 29: the heredoc / shell-text hook is APPROVED (`#27-shellhook`) |
| `2026-10-01-94f74d` | 8865 |  |  | 2026-10-01 — design v2 step 14 T1: how the A/B runner refuses a contaminated batch (`#26-organiccatch`, v2 step 14) |
| `2026-10-01-99acef` | 8850 | 28 |  | 2026-10-01 — USER RULING 28: step 14's batch — 16 lanes, two arms; start TONIGHT if the smoke run passes; Q1 and Q3 run AS BUILT (`#26-organiccatch`, v2 step 14 |
| `2026-10-01-fc47a9` | 8810 |  |  | 2026-10-01 — design v2 step 14 (the Phase 3 batch): how the A/B is run and graded (`#26-organiccatch`, v2 step 14) |
| `2026-10-01-500697` | 8793 |  |  | 2026-10-01 — `#27-itemprobes`: how step 14 will be measured, and the open question it leaves for the user (`#27-itemprobes`) |
| `2026-09-30-318d5b` | 8773 |  |  | 2026-09-30 — Design v2 step 13's BUILD REVIEW: its rulings, and step 14's arm B (`#26-organiccatch`) |
| `2026-09-30-cb30b1` | 8745 |  |  | 2026-09-30 — Design v2 step 13 BUILT and FOLDED: the builder's gap rulings, and the adversarial pass's (`#26-organiccatch`) |
| `2026-09-30-0edd97` | 8718 |  |  | 2026-09-30 — Design v2 step 13 (KB-2, items in DOUBLE battles): the design's rulings, and their rejected alternatives (`#26-organiccatch`) |
| `2026-09-30-49d8a0` | 8691 |  | cue | 2026-09-30 — Design v2 step 12's BUILD REVIEW: its rulings, and a correction to the entry above (`#26-organiccatch`) |
| `2026-09-30-3a5ec4` | 8649 |  |  | 2026-09-30 — Design v2 step 12 (W, weaken-to-catch, RULING 25) as built: a BINARY no-self-harm rule, gain counted in BALLS, the kind read from the mode, a test  |
| `2026-09-30-e235c5` | 8619 |  |  | 2026-09-30 — Design v2 step 11's review: which classifier exclusions to tighten, and which to RELAX (`#26-organiccatch`) |
| `2026-09-30-6cffed` | 8581 |  |  | 2026-09-30 — Design v2 step 11 (M1, damage-calculator fidelity) as built and graded: raw reads in production, every verdict offline, the faint rule, and how a d |
| `2026-09-30-27d7da` | 8530 |  |  | 2026-09-30 — Design v2 step 10b (HK at Sootopolis) as built, and its review: the kit separated from the basket by TIME, the driver's lever rule completed, each  |
| `2026-09-29-ba0289` | 8494 |  |  | 2026-09-29 — Design v2 step 10a (HK at Rustboro) as built, and its review: how each set is logged, and where the kit is planned (`#26-organiccatch`) |
| `2026-09-29-557b8f` | 8451 |  |  | 2026-09-29 — Design v2 step 10 (HK, the healing-kit top-off): the spec as it will be built (`#26-organiccatch`) |
| `2026-09-29-033776` | 8437 |  |  | 2026-09-29 — Design v2 step 9b review: where the driver's ball grade lives (`#26-organiccatch`) |
| `2026-09-29-aa8144` | 8406 |  |  | 2026-09-29 — Design v2 step 9b (BB consumer b, Sootopolis): how the ball top-off rides RULING 18's visit (`#26-organiccatch`) |
| `2026-09-29-7d7a2c` | 8376 |  |  | 2026-09-29 — RULINGS 23 + 26 / design v2 step 9a (BB): the ball top-off rides the heal, Rustboro first, with bounded defaults (`#26-organiccatch`) |
| `2026-09-29-2a62c0` | 8360 |  |  | 2026-09-29 — RULING 25 / design v2 step 8 (RC), after the review: the accepted consequences are WIDER than first recorded (`#26-organiccatch`) |
| `2026-09-29-2da544` | 8330 |  |  | 2026-09-29 — RULING 25 / design v2 step 8 (RC): the cap of 3 and the rare exemption, through two pure helpers, asking about `encounter.pokemon` (`#26-organiccat |
| `2026-09-29-2fb9cc` | 8299 |  |  | 2026-09-29 — design v2 step 7 (RP): what "rare" is, pinned in data (`#26-organiccatch`) |
| `2026-09-29-01fad8` | 8274 |  |  | 2026-09-29 — RULING 27 / design v2 step 6 (KB): healing items only against KEY trainer classes, gated INSIDE `_maybe_use_item`, failing OPEN |
| `2026-09-29-2b24be` | 8248 |  |  | 2026-09-29 — design v2 step 5 (TID/T1): trainer telemetry is ALWAYS ON and log-only; B is read only in TwoOpponents; a post-battle re-entry is skipped by a MEAS |
| `2026-09-29-3567e5` | 8229 |  |  | 2026-09-29 — `#24-rarepredicate`: the 2026-08-07 "the dataset does not reproduce" verdict is RETRACTED (two script defects) |
| `2026-09-29-19e818` | 8200 |  |  | 2026-09-29 — READINGS OF THE RECORD that design v2 builds on (recorded so they are not re-derived or re-asked) |
| `2026-09-29-0695b5` | 8176 |  |  | 2026-09-29 — RULING 24 step 5: no faint bail on a dex catch, on BOTH paths; the flag is read from the running mode; BAILWIDE became a gate mutant |
| `2026-09-29-aa4777` | 8151 |  |  | 2026-09-29 — RULING 24 step 4: a wanted species outranks SURVIVAL MODE; the dex commit is ONE helper called from two places, through the class |
| `2026-09-29-5c03e2` | 8132 |  |  | 2026-09-29 — RULING 24 step 3: the training lift removes ONE refusal; a training dex catch keeps the trainee as lead; the flag is read from the RUNNING mode |
| `2026-09-29-191151` | 8123 |  |  | 2026-09-29 — RULING 24 C4 knowingly changes what a SHARED map key sees; `_catch_defeat_counts` is telemetry only |
| `2026-09-29-e4472b` | 8105 |  |  | 2026-09-29 — RULING 24 step 2: the health lift removes ONE refusal, and a lost DEX catch is filed apart from map defeats (team losses are not) |
| `2026-09-29-33b616` | 8057 | 23, 25, 26, 27 | DO-NOT-REOPEN | 2026-09-29 — USER RULINGS 23 and 25 CLARIFIED, and USER RULINGS 26 and 27: stocks kept all game, the best ball, never give up on a wanted rare, weaken-to-catch  |
| `2026-09-28-f65547` | 8022 | 23, 24, 25 | DO-NOT-REOPEN | 2026-09-28 — USER RULINGS 23, 24 and 25: the answers to RULING 20's §8 questions (money for balls, catching while hurt or training, the attempt cap) |
| `2026-09-28-92a86a` | 8003 |  |  | 2026-09-28 — RULING 20 P2-c ships OFF, covers a WALKING hunt as well as an armed one, and has no production fault env |
| `2026-09-28-12a491` | 7984 |  |  | 2026-09-28 — `#27-enroutejoin`: refuse a PARTY JOIN while a hunt walks, rather than re-reading the party on arrival or arming before the walk |
| `2026-09-28-d6562e` | 7964 |  |  | 2026-09-28 — RULING 20 P2-b lifts ONE refusal, behind a flag that ships OFF; its fault arm is "the open branch returns early" |
| `2026-09-28-c3d6b1` | 7951 |  |  | 2026-09-28 — RULING 20 P2-a ships OFF, with its `none_left` exit active only under the flag |
| `2026-09-28-77cc5e` | 7931 |  |  | 2026-09-28 — A hunt's spin tile is filtered and ASSERTED by tile type; the filter fails OPEN; no automatic retarget |
| `2026-09-28-9c79ab` | 7918 |  |  | 2026-09-28 — `--set-balls N` sets the Poké Ball STACK only, and a failure aborts the run |
| `2026-09-28-9f12c0` | 7902 |  |  | 2026-09-28 — RULING 20's catch telemetry is ALWAYS ON (no flag), and it ships ahead of every behaviour change |
| `2026-09-28-f98703` | 7885 |  | cue | 2026-09-28 — The `#24-faintchooser-fourthspace` closure (2026-08-17) is SUPERSEDED by measured evidence |
| `2026-09-28-6eddd7` | 7856 |  |  | 2026-09-28 — The after-faint chooser decides by IDENTITY (PID + species); every index conversion is confined to a fault arm (`#27-ki47range`, KI-47) |
| `2026-09-28-7858e3` | 7830 |  |  | 2026-09-28 — The destructive-git hook: Python with a shell-aware pre-scan; a hatch read from the COMMAND; every hook located via $CLAUDE_PROJECT_DIR |
| `2026-09-27-71fbf2` | 7819 |  |  | 2026-09-27 — RULING 21's identity check accepts an EVOLUTION on the same PID (not PID-only, not a re-record) |
| `2026-09-27-57614f` | 7799 | 12 |  | 2026-09-27 — `#24-restockleg` F1 (USER RULING 12): R1 restocks ONCE, inside itself, only when the basket is its ONLY reason |
| `2026-09-27-6c5555` | 7788 |  |  | 2026-09-27 — KI-107: bound the whiteout recovery's waits NOW; leave the root cause (F1) for a driven fix |
| `2026-09-27-360ecb` | 7765 | 21 |  | 2026-09-27 — RULING 20 Phase 1, increment B (Fly) + USER RULING 21: the lobby PC; the lowest fighter sits out; the swap-back happens in the lobby, before the gu |
| `2026-09-27-83e6c0` | 7741 |  |  | 2026-09-27 — RULING 20 Phase 1, increment B (counters): box-first before the hunt with a NEW strict picker; the heal withdraws only OWED counters |
| `2026-09-27-c6a75e` | 7724 |  |  | 2026-09-27 — RULING 20 Phase 1, increment B (Waterfall): box-first INSIDE `ensure_waterfall_learner`, at Sootopolis only |
| `2026-09-27-7b0088` | 7706 |  |  | 2026-09-27 — RULING 20 Phase 1, increment B (Strength): box-first only where a centre trip can come back; the boxed pick prefers a learner that cannot carry HM0 |
| `2026-09-27-69bc11` | 7688 |  |  | 2026-09-27 — RULING 20 Phase 1, increment A: the REQUIRED-errand victim is the lowest-level unprotected member; counters expire at their badge |
| `2026-09-27-230438` | 7655 | 22 |  | 2026-09-27 — ⭐ USER RULING 22: A DEDICATED SHEDINJA SEQUENCE — THE ONLY DUPLICATE-CATCH EXCEPTION BESIDES RARE/SHINY; and two RULING 20 design points settled fr |
| `2026-09-27-e47f76` | 7636 |  | DO-NOT-REOPEN | 2026-09-27 — USER OBSERVATIONS during batch `#27-batch0927`: catching still stops at 4 (re-affirms RULING 20), and a FUTURE fossil request |
| `2026-09-27-81d5ef` | 7617 |  |  | 2026-09-27 — the Norman heal TRIES the generic walk first and falls back only on failure (unlike Lavaridge's pre-check) |
| `2026-09-27-8a6372` | 7594 |  |  | 2026-09-27 — the Lavaridge heal is fixed AT THE SEGMENT (F4), not in the navigator |
| `2026-09-27-da5804` | 7574 |  |  | 2026-09-27 — an unreachable training ground is remembered from BOTH the map where the walk died and the map it was chosen from |
| `2026-09-27-864d48` | 7546 |  |  | 2026-09-27 — RULING 20 Phase 0: the pre-gym-1 attempt cap is DEFERRED to Phase 2, and the full-HP pre-gym-1 health check is REJECTED |
| `2026-09-27-6929a2` | 7523 |  |  | 2026-09-27 — KI-106: RELEASE LEAKED HELD INPUT AT THE STORY'S RECOVERY SEAM, not in `_sampling` or `isolate_inputs` |
| `2026-09-26-4f81b7` | 7506 |  |  | 2026-09-26 — KI-104: THE HM TEACH'S SLOT PICKER IS TOTAL, AND TYPE PROTECTION IS A PREFERENCE, NEVER A REFUSAL |
| `2026-09-26-c73225` | 7489 |  |  | 2026-09-26 — RULING 20 PHASE 0: DO NOT START A POKÉDEX CATCH EXPECTED TO COST MORE THAN 10 BALLS |
| `2026-09-26-9ff66b` | 7467 |  |  | 2026-09-26 — RULING 19 BUILT AS "TEACH ONLY WHERE THE TM CAN REACH AND WIN SOMETHING" (design 4) |
| `2026-09-26-86b525` | 7454 |  |  | 2026-09-26 — THE DEX-CATCH BAIL: STOP AT THE RESERVE; WHEN TRAPPED, THROW; TRAPPED AND EMPTY, FIGHT |
| `2026-09-26-6d6b8c` | 7421 | 19, 20, 21 |  | 2026-09-26 — ⭐⭐ USER RULINGS 19-21: GYM ANSWERS FROM OWNED TMs; ORGANIC CATCHING INSTEAD OF CHAPTER FIXES; THE FLY SWAP |
| `2026-09-26-f56b48` | 7407 |  |  | 2026-09-26 — §Ch23 LEG-5 RE-ENTRY: A PATH CHECK, NOT A y-THRESHOLD; FAIL TOWARD THE OLD GUARD |
| `2026-09-26-682edf` | 7387 |  |  | 2026-09-26 — RULING 18 IMPLEMENTATION CHOICES: SOOTOPOLIS IN §Ch22 L1, RESERVE UNTIL THE ELITE FOUR, STATE-DERIVED |
| `2026-09-26-931cb0` | 7372 |  |  | 2026-09-26 — RULING 17 IMPLEMENTATION CHOICES: SEGMENT 12d, FAIL SOFT, TOP-LEVEL HOLDER (v1) |
| `2026-09-26-cc050f` | 7350 | 15, 16, 17, 18 |  | 2026-09-26 — ⭐⭐ USER RULINGS 15-18: §Ch24 READINESS AND THE LEAGUE-BASKET MONEY (asked with evidence; `06` grepped first — none was ruled) |
| `2026-09-26-346986` | 7339 |  |  | 2026-09-26 — `ensure_fly_learner` REPORTS A MISSING LEARNER, IT NEVER RAISES; THE WALK-OFF GUARD RUNS ONLY WITHOUT FLY |
| `2026-09-26-667eb2` | 7328 |  |  | 2026-09-26 — THE RETURN BRIDGE RUNS AFTER R1, AND ONLY ONCE (`#26-ch24organic` gap 2) |
| `2026-09-26-5fbdbd` | 7317 |  |  | 2026-09-26 — `#26-ch24organic` IS BUILT ON A WORKTREE BRANCH WHILE THE USER'S BATCH RUNS |
| `2026-09-26-38271b` | 7300 | 12 | SUPERSEDED | 2026-09-26 — `#26-ch24organic` R1 REFUSES AT THE PRODUCTION FLOOR (USER RULING 12 APPLIED LITERALLY) — ⚠ RELAXATION IS THE USER'S CALL, FLAGGED |
| `2026-09-26-20079f` | 7287 |  |  | 2026-09-26 — §Ch23's CHUNKED TRAINING GRANTS ITS PURSE TO THE BATCH RUN CAP (`_ch23_training_allowance`) |
| `2026-09-26-41e337` | 7273 |  | cue | 2026-09-26 — ⛔ CORRECTION TO RULING 14's MONEY CLAUSE (same day, caught BEFORE any code used it) |
| `2026-09-26-18ee11` | 7252 | 14 |  | 2026-09-26 — ⭐ USER RULING 14: LOW-LEVEL HM CARRIERS MAY BE SWAP-TRAINED ON VICTORY ROAD 1F INSIDE §Ch23, IN BOUNDED CHUNKS |
| `2026-09-26-60c04c` | 7236 |  |  | 2026-09-26 — THE ENDLESS ANALYZER KEYS END-GAME MILESTONES ON NAME ∧ (GROUP, NUMBER) ∧ ≥2 SIGHTINGS, AND READS `debug-logs/` + `Old/` |
| `2026-09-26-1d4bda` | 7214 |  |  | 2026-09-26 — HOLD THE USER'S OFFERED 12-HOUR x4 BATCH UNTIL THE TWO §Ch23 KILLERS ARE FIXED (`#26-batch0926`) |
| `2026-09-26-3a4b03` | 7204 |  |  | 2026-09-26 — USER RULING: THE UPSTREAM SYNC STAYS PARKED ("Not now, keep it parked") |
| `2026-09-26-61c53c` | 7183 |  |  | 2026-09-26 — ENDLESS-RESET CAP: RAISE THE BASE TO 7M, AND EXTEND IT ONLY ONCE §Ch24 OWNS THE RUN (`#26-endlesscap`) |
| `2026-09-25-9652b1` | 7168 |  |  | 2026-09-25 (later still) — test the HM path with WATERFALL, never SURF |
| `2026-09-25-70d879` | 7142 |  |  | 2026-09-25 (later still) — prove the PC-first HM block LOAD-BEARING from PRODUCTION, not from the driver |
| `2026-09-25-40ef56` | 7101 | 13 |  | 2026-09-25 — ⭐⭐ USER RULING 13: **THE BATTLE TEAM IS L65-75; THE ROSTER IS FREE** |
| `2026-09-25-52b1fb` | 7022 |  |  | 2026-09-25 — ⭐ USER DIRECTION: THE HM-LEARNER SEARCH MUST USE THE **PC** AND THE **WHOLE MAP** |
| `2026-09-25-bd0d61` | 6967 | 12 | DO-NOT-REOPEN | 2026-09-25 — ⭐⭐ USER RULING 12: ON LOSING THE ELITE FOUR, THE BOT **RESTOCKS AND RETRIES** |
| `2026-09-24-e59b96` | 6927 |  |  | 2026-09-24 — ⭐ USER GOAL: **THE TEAM LINEUP SHOULD VARY BETWEEN RUNS** (organic play) |
| `2026-09-24-38cb13` | 6899 |  |  | 2026-09-24 — ⭐ DESIGN RULING: §Ch24 LEG 1 STOPS **AT** THE LEAGUE DOOR; THE COMMITMENT BELONGS TO THE GAUNTLET LEG |
| `2026-09-24-1b9a57` | 6878 |  |  | 2026-09-24 — ⭐ USER RULING: THE ORDER IS ELITE FOUR → POKÉDEX → ORGANIC PLAY |
| `2026-09-23-8c1057` | 6860 | 13 |  | 2026-09-23 — USER RULING 13: IF A MŌN IS EVER REMOVED, IT IS A PC DEPOSIT — AND THE ROUND TRIP IS PROVEN FIRST |
| `2026-09-23-5c88b3` | 6816 | 12 | DO-NOT-REOPEN | 2026-09-23 — ⭐⭐ USER RULING 12: TRAIN ALL SIX ON THE FLY LADDER. THE PARTY IS NOT REDUCED. |
| `2026-09-23-15754a` | 6776 |  |  | 2026-09-23 — THE FLY-AWARE PREDICATE IS A **DISJUNCT** OVER `region_reach`, NOT A `calculate_path` LAST-MILE CHECK |
| `2026-09-23-35005f` | 6738 |  |  | 2026-09-23 — USER DIRECTIVE: FISHING AS AN HM-CARRIER SOURCE, A SIX-MŌN TEAM, AND WORKING PC SWAPS — SCOPED AFTER §Ch24 |
| `2026-09-19-0fdf1f` | 6710 |  |  | 2026-09-19 — `max_wild_max` TAKES A NUMBER, NOT A MARGIN, BECAUSE `modules/` MAY NOT IMPORT `plugins/` |
| `2026-09-19-7dd76c` | 6667 |  |  | 2026-09-19 — ⭐⭐ USER RULING: TRAIN EACH MŌN AT A LEVEL-APPROPRIATE GROUND, AND FLY TO REACH IT |
| `2026-09-18-e97c57` | 6622 |  |  | 2026-09-18 — ⭐ USER RULING: EVERY TEAM MEMBER MUST BE L65-75, AND THEY NEED NOT MATCH |
| `2026-09-18-dcfea7` | 6587 |  | DO-NOT-REOPEN | 2026-09-18 — VICTORY ROAD IS NOT PROMOTED INTO `TRAINING_GRASS`, AND `#24-trainingbrackets` CLOSES WITHOUT A CODE CHANGE |
| `2026-09-18-fa9ec4` | 6537 |  |  | 2026-09-18 — A PRE-REGISTERED ABORT CONDITION FIRED AND I PROCEEDED ANYWAY — HERE IS THE REASONING, ON THE RECORD |
| `2026-09-18-9c3dff` | 6457 |  | DO-NOT-REOPEN | 2026-09-18 — THE VICTORY ROAD TRAINING ROW IS NOT ADDED UNTIL `#24-waterfallcap` IS FIXED; THE CAP FIX ITSELF MAY LAND ALONE, AND FIRST |
| `2026-09-18-5c6096` | 6420 | 11 |  | 2026-09-18 — ⭐⭐ USER RULING 11: THE §Ch24 ACCEPTANCE BAR, AND IT IS BIGGER THAN THE ITEM THAT PROMPTED IT |
| `2026-09-18-d4732f` | 6386 | 9, 10 |  | 2026-09-18 — ⭐ USER RULINGS 9 & 10: THE LEDGER IS TWO ARTIFACTS; OVERWORLD ITEMS ARE USER-GATED |
| `2026-09-18-dc6cd5` | 6355 |  |  | 2026-09-18 — ⭐ USER DIRECTIVE: A REMATCH LEDGER, AND A PER-CHAPTER MAP KNOWLEDGE BASE THAT IS *PRODUCT* |
| `2026-09-18-1ad42c` | 6322 | 8 |  | 2026-09-18 — ⭐ USER RULING 8: “REGULAR SPEED” MEANS ×1 IN PRODUCTION; FAST-FORWARD IS FOR DATA |
| `2026-09-18-58a393` | 6260 |  |  | 2026-09-18 (second round) — ⭐ USER RULINGS: TIME IS NOT THE CONSTRAINT, LEVEL-APPROPRIATENESS IS |
| `2026-09-18-7c5632` | 6196 |  | DO-NOT-REOPEN | 2026-09-18 — ⭐ USER RULINGS: THE LEVEL TARGET, THE GRIND LOCATION, AND WHERE §Ch24 HEALS |
| `2026-09-18-d88ad7` | 6179 |  |  | 2026-09-18 — A GUARD TRANSCRIPTION MUST NAME THE *CALL*, NOT THE ENCLOSING `if` |
| `2026-09-18-b5e69d` | 6156 |  |  | 2026-09-18 — MINT THE LOBBY FIXTURE ON THE *REVERSIBLE* SIDE OF THE IRREVERSIBLE STEP |
| `2026-09-18-983f5f` | 6125 |  |  | 2026-09-18 (later) — THE LOBBY FIXTURE IS MINTED **WITHOUT** THE GUARD TALK |
| `2026-09-18-0ce2d2` | 6086 |  |  | 2026-09-18 (later) — THE §Ch24 MARKER IS AN **EXPLICIT TUPLE**, NEVER A GROUP TEST — AND ALL THREE CAVEATS ARE CLOSED |
| `2026-09-18-6186dd` | 6028 |  | cue | 2026-09-18 (later) — ⛔ REVERSAL: §Ch23 IS THE WRONG HOST FOR THE GRIND. THE DECISION ABOVE NAMED THE GROUND AND ASSUMED THE HOST |
| `2026-09-18-4d4aa9` | 5989 |  |  | 2026-09-18 — BUILD THE STEPPED GRIND ON **1F** FIRST; CHOOSE THE GROUND **LAST** |
| `2026-09-17-f37484` | 5948 |  |  | 2026-09-17 (late) — ⛔ A THIRD CAVEAT ON THE §Ch24 MARKER RULING: IT DOES NOT COVER **WINNING** |
| `2026-09-17-8f6cba` | 5922 |  |  | 2026-09-17 (late) — ENFORCING IS JUSTIFIED BY THE **INPUT DOMAIN**, NOT BY THE CHECKER |
| `2026-09-17-b69c79` | 5891 |  | cue | 2026-09-17 (late) — ⛔ REVERSAL OF THE ENTRY ABOVE: THE RETRACTION-COVERAGE CHECK IS **ADVISORY**, NOT ENFORCING |
| `2026-09-17-5bafb0` | 5866 |  | SUPERSEDED | 2026-09-17 (late) — THE RETRACTION-COVERAGE CHECK IS **ENFORCING**, NOT ADVISORY |
| `2026-09-17-c1970f` | 5808 |  | DO-NOT-REOPEN | 2026-09-17 (late) — ⛔ THE LEVEL FIX IS **NOT** “A CAPABILITY WE ALREADY SHIPPED”: IT IS SHIPPED IN THE HARNESS ONLY |
| `2026-09-17-f27980` | 5772 |  |  | 2026-09-17 (late) — the §Ch24 tail probe does NOT defeat the 20,000-frame no-progress detector, on purpose |
| `2026-09-17-3a4ad8` | 5733 |  |  | 2026-09-17 (late) — Mint room 3's start fixture by adding a POST-FIGHT capture to the proven Phoebe driver, not by building a two-room driver |
| `2026-09-17-f8f2d5` | 5696 |  |  | 2026-09-17 (third) — USER RULING: §Ch24 HEALS FROM THE BAG BETWEEN ROOMS. IT IS NOT OPTIONAL. |
| `2026-09-17-11cd93` | 5638 |  | DO-NOT-REOPEN | 2026-09-17 (second) — THREE USER RULINGS ON §Ch24, PLUS A NEW STANDING CHANNEL |
| `2026-09-17-5edc72` | 5581 |  | DO-NOT-REOPEN | 2026-09-17 — ⛔ THE L75 GRIND RUNS ON `post_ch24ready.ss1`. `post_grind_L60.ss1` IS A DEAD BRANCH. |
| `2026-09-16-322cd3` | 5543 |  | cue | 2026-09-16 (later still) — ⛔ CORRECTION TO MY OWN WINNABILITY VERDICT: "WALLACE IS OUT OF REACH" IS AN **L53** RESULT, AND LEVELLING CONVERTS IT |
| `2026-09-16-d32268` | 5496 |  |  | 2026-09-16 (later) — THE §Ch24 PROGRESS MARKER MUST BE A **POSITION ON THE SEALED SIDE**, and that is safe by EXHAUSTION |
| `2026-09-16-cb324e` | 5426 |  |  | 2026-09-16 — ⛔ DO **NOT** WIRE SEGMENT 24 YET, EVEN THOUGH LEG 1'S MECHANICS ARE FULLY DRIVEN |
| `2026-09-16-cd940d` | 5381 |  |  | 2026-09-16 — USER RULING: 05-KNOWN-ISSUES gets ARCHIVE + RAISE + GUARD (not a bigger file, not "Part 2") |
| `2026-09-16-42f48d` | 5331 |  | DO-NOT-REOPEN | 2026-09-16 — USER RULING: the post-whiteout money policy is **SPEND DOWN BEFORE ENTERING** |
| `2026-09-15-500206` | 5293 |  |  | 2026-09-15 — Fix the DRIFT METER, not the file's line endings (`#24-driftreduction`) |
| `2026-09-13-0e7479` | 5268 |  |  | 2026-09-13 — `#24-e4healing` step 3, the WIRING: three more choices |
| `2026-09-13-bf098b` | 5236 |  |  | 2026-09-13 — `#24-e4healing` step 3: four design choices in the in-battle item policy |
| `2026-09-12-d713d6` | 5201 |  |  | 2026-09-12 — `#24-maintain-staletarget`: leave the ordering alone (measured zero cost; reordering has a CERTAIN harm) |
| `2026-09-12-f83fd9` | 5167 |  | DO-NOT-REOPEN cue | 2026-09-12 (user ruling) — ‼ `POKEBOT_MAINTAIN` WILL BE TURNED **ON**. This SUPERSEDES the two “stays OFF” entries above. |
| `2026-09-12-e757a6` | 5138 |  | SUPERSEDED | 2026-09-12 (09:03) — `#24-maintain`: the benefit question is ANSWERED (no), and the flag stays OFF |
| `2026-09-12-125f6e` | 5109 |  | DO-NOT-REOPEN SUPERSEDED | 2026-09-12 — `#24-maintain` stays DEFAULT-OFF after its A/B, and the A/B is kept rather than re-run |
| `2026-09-11-79f56f` | 5064 |  |  | 2026-09-11 — `#24-maintain` is TWO items in one slug; the early half is buildable and the late half stays dead |
| `2026-09-10-3b0bfa` | 5031 |  |  | 2026-09-10 — Post-Winona loss adaptation: grass-less configs, and why `#24-maintain` cannot be built yet |
| `2026-09-10-7e05ef` | 4996 |  | cue | 2026-09-10 (later) — CORRECTION to the §Ch24 entry-marker entry above: its leg-4 mechanism was wrong |
| `2026-09-10-c0342b` | 4931 |  |  | 2026-09-10 — §Ch24's entry marker: THREE DESIGNS KILLED, and the question was the wrong one |
| `2026-09-10-c60cf4` | 4879 |  |  | 2026-09-10 — `#24-dexhunt`: four design rulings on the catching fence |
| `2026-09-08-4698bb` | 4849 |  |  | 2026-09-08 — Where the "run it bare" guarantee stops: the runner and its REGISTERED gates |
| `2026-09-08-a3b3ab` | 4814 |  |  | 2026-09-08 — Two Gen-3 facts settled FROM THE DECOMP, and what we did NOT do with them |
| `2026-09-08-79bf73` | 4771 |  |  | 2026-09-08 — An accumulate-reasons predicate must handle the EMPTY input EXPLICITLY (`team_is_ready`) |
| `2026-09-07-05d943` | 4733 |  |  | 2026-09-07 — `#24-hm07teach`: TEACH the move (not relax the preflight), and place it at Segment 22b |
| `2026-09-07-48241e` | 4691 |  |  | 2026-09-07 — the grind: STEP the proven trainer, never re-implement it, and never raise its ceiling |
| `2026-09-07-a26209` | 4664 |  |  | 2026-09-07 — `KI-93`: the refusal memory is keyed on the POKÉMON and expires when a turn executes |
| `2026-09-06-6d95ae` | 4636 |  |  | 2026-09-06 — `KI-93`: gate the dismiss on the PRINTER STATE, and hold the refusal memory at MODULE level |
| `2026-09-06-ba281b` | 4606 |  |  | 2026-09-06 — reuse the shipped damage formula, and make the faint ranking a PURE function |
| `2026-09-06-96e383` | 4545 |  |  | 2026-09-06 — KI-93 (Torment): the fix is DESIGNED AND VERIFIED, and deliberately NOT IMPLEMENTED YET |
| `2026-09-05-7ea9a8` | 4506 |  |  | 2026-09-05 (late) — leg 11 may SELL to close a basket shortfall, from an ALLOW-LIST, never a deny-list |
| `2026-09-05-079ffd` | 4456 |  | cue | 2026-09-05 (late) — REVERSAL #2: leg 9 ROUTES AROUND the pair via (33,16). The split is shelved. |
| `2026-09-05-cc4d7b` | 4392 |  | DO-NOT-REOPEN SUPERSEDED cue | 2026-09-05 (evening) — REVERSAL: the leg-9 fix is TWO SINGLE BATTLES. The heal AND the bypass are measured dead. |
| `2026-09-05-11b4ba` | 4352 |  | SUPERSEDED | 2026-09-05 — the leg-9 attrition fix will be a POKÉ CENTER heal, not bag items, and not grinding |
| `2026-09-05-810262` | 4312 |  |  | 2026-09-05 — REJECTED: a gate for "two different next steps on one line" |
| `2026-09-05-04819e` | 4275 |  | cue | 2026-09-05 — REVERSAL: `ch23_chapter_done()` DOES require the Elite Four basket |
| `2026-09-05-db3496` | 4229 |  |  | 2026-09-05 — `KI-90` is fixed AT THE CHECKPOINT: aim at the RIGHT opponent when the LEFT is absent |
| `2026-09-05-fb7a4d` | 4191 |  |  | 2026-09-05 — modifying `modules/battle_*`: what is ACTUALLY decided (and the phantom ruling this replaces) |
| `2026-09-05-55b4ca` | 4152 |  |  | 2026-09-05 — a repro for an OPEN bug may be a gate ONLY if it SELF-RETIRES |
| `2026-09-05-6620a9` | 4123 |  |  | 2026-09-05 — §Ch23's completion gate is FLAG **AND** POSITION, not the chapter table's milestone |
| `2026-09-05-327083` | 4097 |  |  | 2026-09-05 — The 2026-09-04 catching directive is served BY `#24-dexhunt`, not by a new item |
| `2026-09-04-14103b` | 4055 |  |  | 2026-09-04 — USER DIRECTIVE: the bot CATCHES and TRAINS, and fills the Pokédex |
| `2026-09-04-8cafcd` | 3992 |  |  | 2026-09-04 — USER DIRECTIVE: the Elite Four is an ITEM-ONLY gauntlet |
| `2026-09-04-6f8621` | 3962 |  |  | 2026-09-04 — §Ch23: generalise leg 6's ladder helpers rather than copy them into leg 7 |
| `2026-09-03-78d5f8` | 3923 |  |  | 2026-09-03 — VICTORY ROAD B1F: A FIXED PUSH SEQUENCE WITH A REFUSAL GUARD, NOT A RUNTIME SOLVER |
| `2026-09-03-0416fa` | 3896 |  |  | 2026-09-03 — §Ch22's LEG ORDER, AND WHAT A CHAPTER DRIVER'S GRADE IS ALLOWED TO DEMAND |
| `2026-09-02-a7c936` | 3871 |  |  | 2026-09-02 (later still) — §Ch21 DISPATCH grades STRICTER than `chapters.py` does, on purpose |
| `2026-09-02-622828` | 3845 |  | cue | 2026-09-02 (later) — CORRECTION to the entry above: `chapters.py` ALREADY consumes `RECEIVED_HM_WATERFALL` |
| `2026-09-02-cb308e` | 3806 |  |  | 2026-09-02 — §Ch21 LEG 5: THE FOUR CHOICES THAT SHAPED IT |
| `2026-09-01-3d0017` | 3762 |  |  | 2026-09-01 (later) — §Ch21 LEG 4: THE FALL IS ITS OWN PRIMITIVE, AND THE GRADE IS POSITION+PATH, NOT VARS |
| `2026-09-01-d04f21` | 3724 |  |  | 2026-09-01 (later) — LEG 4's END BOUNDARY: **THE DESCENT IS IN SCOPE.** Not a judgement call — forced by a standing rule plus a measurement |
| `2026-09-01-0ce209` | 3691 |  |  | 2026-09-01 (later) — READ THE SKY PILLAR'S CLEAN LAYOUTS FROM **OUR OWN ROM**, NOT BY EXTENDING THE NETWORK PROBE |
| `2026-09-01-2c95ed` | 3596 |  |  | 2026-09-01 — §Ch21 LEG 3: FIVE DECISIONS THE BUILD SPEC LEFT TO THE BUILDER |
| `2026-08-28-1b2e58` | 3562 |  |  | 2026-08-28 — USER QUESTION, ANSWERED AND SETTLED: WHY `04-HANDOFF.md` IS NOT SPLIT INTO "PART 1 OF N" |
| `2026-08-28-db0019` | 3530 |  |  | 2026-08-28 — USER RULING: THE PREVENTION RULES ARE LIVING, AND I MAY UPDATE THEM — NOT ONLY APPEND |
| `2026-08-27-bc9868` | 3486 |  |  | 2026-08-27 — THE POCKET-EXIT QUESTION IS ANSWERED STATIC-FIRST, WITH PRODUCTION'S PLANNER AS THE ORACLE AND THE DRIVE RESERVED FOR WHAT STATIC CANNOT SEE |
| `2026-08-26-f9bebb` | 3471 |  |  | 2026-08-26 — `#24-driftheadlineshape`: position-scoped exemption, not vocabulary |
| `2026-08-26-ad07f9` | 3448 |  |  | 2026-08-26 — `#24-difftriggeredrules`: advisory-only, diff-indexed, and NO permissionDecision in the hook |
| `2026-08-26-2557d6` | 3423 |  |  | 2026-08-26 — The Winona SECOND WIND: one derail-retry may do what the manual flip does |
| `2026-08-24-6ae55e` | 3393 |  |  | 2026-08-24 — §Ch21 leg 1's acceptance was RE-POINTED from the Cave of Origin to the Poké Center |
| `2026-08-23-e58d12` | 3350 |  |  | 2026-08-23 (logged 2026-08-24) — RULING: `#24-abortrecoveryresiduals` (a) — do NOT patch the whiteout-recovery path; close it on an ASSESSMENT |
| `2026-08-23-fdae9a` | 3322 |  |  | 2026-08-23 — RULING: delete `check_ratchet_baseline_claims` rather than fix its 7 blockers |
| `2026-08-23-e6e84a` | 3288 |  |  | 2026-08-23 — RULING: three design choices in `#24-p2headergate`, and why each alternative was rejected |
| `2026-08-23-395bcf` | 3274 |  |  | 2026-08-23 — RULING: fix the debt you CREATED; file the debt you INHERITED |
| `2026-08-23-a9efcf` | 3263 |  |  | 2026-08-23 — RULING: the abort-swallow ratchet now carries DIFFERENT baselines per fork |
| `2026-08-23-fc657d` | 3230 |  |  | 2026-08-23 — RULINGS from `#24-p4residuals`: two obvious fixes refuted, and why a DENYLIST beat an allowlist |
| `2026-08-23-576b9b` | 3200 |  | cue | 2026-08-23 — ⛔ REVERSED, SAME DAY: the "recovery path is exempt from `_check_abort()`" ruling above is WITHDRAWN |
| `2026-08-23-55fdc8` | 3192 |  |  | 2026-08-23 — RULING: this fix is NOT promoted. Drift is 1 and the decision is the user's. |
| `2026-08-23-908a3b` | 3156 |  | WITHDRAWN | 2026-08-23 — RULING: the whiteout-RECOVERY path is permanently exempt from `_check_abort()` |
| `2026-08-23-43fd61` | 3119 |  | DO-NOT-REOPEN cue | 2026-08-23 — RE-AFFIRMED (not a new decision): the Emerald ROM stays tracked. ⛔ THIS IS THE SECOND RULING ON IT. |
| `2026-08-23-a4429c` | 3090 |  |  | 2026-08-23 — RULING: the pair list gains **P5**, and a dead agent means an UNCOVERED ANGLE |
| `2026-08-22-c4a4a7` | 3046 |  |  | 2026-08-22 — PASS 5 rulings: a scope that did not exist, and what NOT to fix |
| `2026-08-22-37699d` | 3001 |  |  | 2026-08-22 — PASS 4 rulings: an ADVISORY gate tier, and three things deliberately NOT done |
| `2026-08-17-1201e6` | 2974 |  |  | 2026-08-17 — promote all five in ONE round, but prove them in THREE groups |
| `2026-08-17-2e9e98` | 2937 |  |  | 2026-08-17 — `#24-ki76correctness`: MEASURE the arming before touching shared pathfinding, and let PRODUCTION be the oracle |
| `2026-08-17-d5629d` | 2904 |  |  | 2026-08-17 — `#24-orphans` (5): fix the AXIS, do not build the WRAPPER |
| `2026-08-17-22c043` | 2847 |  |  | 2026-08-17 — Drift claims are PARSED AS CLAIMS (polarity + currency marker), not pattern-matched as tokens (`#24-driftassertions`) |
| `2026-08-17-a6b313` | 2819 |  |  | 2026-08-17 — MEASURE an index-space conversion's DIRECTION before applying it (KI-66) |
| `2026-08-16-5bf4bb` | 2790 |  |  | 2026-08-16 — A SAFETY VETO THAT CANNOT EVALUATE MUST FAIL **CLOSED** (KI-65) |
| `2026-08-16-600493` | 2774 |  |  | 2026-08-16 — the abort probe stays a PROBE, and `--build` is what makes a promotion measurable |
| `2026-08-16-17ac23` | 2745 |  |  | 2026-08-16 — `withdraw_from_box`'s "Never raises" contract is narrowed, not abandoned (KI-81) |
| `2026-08-16-f2c554` | 2658 |  |  | 2026-08-16 — DESIGN for the failed-PC-withdraw reaction: FOUR PREREQUISITES BEFORE ANY RETRY |
| `2026-08-16-640a16` | 2621 |  |  | 2026-08-16 — USER RULING: how production reacts to a failed PC withdraw |
| `2026-08-16-6ea351` | 2590 |  |  | 2026-08-16 — unique harness log names: unbounded (gitignored) growth accepted over ANY retention cap |
| `2026-08-16-0f5bc3` | 2565 |  |  | 2026-08-16 — a SELF-RETIRED gate is LEFT retired, not deleted |
| `2026-08-16-802eff` | 2500 |  |  | 2026-08-16 — KI-80's decoupling: the MINIMAL split, and the two things deliberately NOT done |
| `2026-08-15-687b92` | 2458 |  |  | 2026-08-15 — KI-80's repro is THREE arms terminated by a tripwire, not a two-arm A/B run to completion |
| `2026-08-15-357d25` | 2420 |  |  | 2026-08-15 — USER APPROVED TWO PROMOTIONS, and the second established the evidence bar for a BEHAVIOUR promotion |
| `2026-08-15-440deb` | 2390 |  |  | 2026-08-15 — `party_accounting_ledger.jsonl` IS COMMITTED, not gitignored (and harness logs stay ignored) |
| `2026-08-14-62859d` | 2345 |  |  | 2026-08-14 — Party accounting Stage 0: observe from INSIDE the reader, ship no consumer, and say which classes are sampled |
| `2026-08-14-b14e4f` | 2291 |  |  | 2026-08-14 — KI-78 Stage 1: identity is `(personality, species)`, and an evolved-since-capture mon is RE-RESOLVED rather than raising — except when it is ambigu |
| `2026-08-14-10aa4b` | 2220 |  |  | 2026-08-14 — USER RULINGS: the LIVING-DEX goal, resumable runs, and a sanctioned trade-evolution deviation |
| `2026-08-14-8594d0` | 2189 |  |  | 2026-08-14 — USER RULING: the `#24-organicteam` gate is LIFTED (re-confirmed), and the punch list was contradicting the ruling record |
| `2026-08-14-212d1a` | 2165 |  |  | 2026-08-14 — §Ch20: losing to Archie is a VALID BRANCH the chapter must handle, not a defect a driver should prevent |
| `2026-08-14-41b89b` | 2142 |  |  | 2026-08-14 — §Ch20 Room 9: release is gated on VAR_ROUTE128_STATE == 2, never on "looks controllable"; scene-riding presses are gated, never mashed |
| `2026-08-14-a6e059` | 2116 |  |  | 2026-08-14 — §Ch20 Room 8: the jam response is EXIT-AND-RE-ENTER with ONE retry, wired and fault-tested — never improvised pushes, never unbounded retries |
| `2026-08-13-0117b1` | 2074 |  |  | 2026-08-13 — an acceptance test asserts the OUTCOME, not the position you expected to see it from |
| `2026-08-13-1ea1a9` | 2032 |  |  | 2026-08-13 — §Ch20 Room 1: DRIVE UPSTREAM'S SEQUENCE, not our own build spec's — and treat that spec's "exhaustive" claims as unaudited |
| `2026-08-13-9d3b6c` | 2007 |  |  | 2026-08-13 — USER RULING: `stash@{0}` is KEPT PERMANENTLY as a record. Do not drop it. |
| `2026-08-13-b9e4ed` | 1951 |  |  | 2026-08-13 — the next BUILD is §Ch20 (Seafloor Cavern), NOT the Regi arc — and KI-59 was never the arc's blocker |
| `2026-08-13-9e8ace` | 1902 |  |  | 2026-08-13 — KI-59: land the MEASUREMENT as its own item; the fix is FIX-A + a new exit-blocking concept, A/B'd on a LIVE map |
| `2026-08-13-fee98f` | 1749 |  |  | 2026-08-13 — RULING: **Shoal Cave is NOT adopted as a hunting ground.** Route 117 stays. |
| `2026-08-12-72809f` | 1726 |  |  | 2026-08-12 — §Ch18's chapter function lives in `mossdeep_gym.py`, not `early_game.py` |
| `2026-08-12-a65240` | 1702 |  |  | 2026-08-12 — Claude subagents are STANDING-APPROVED for research and assistance |
| `2026-08-12-9e70db` | 1675 |  |  | 2026-08-12 — the warp-maze solver is now a TOOL, and its control is a route we already drove |
| `2026-08-11-7dc88a` | 1639 |  |  | 2026-08-11 — §Ch17's route is SOLVED BY THE WARP GRAPH, and each hop is graded on the TILE |
| `2026-08-11-4a9bf7` | 1611 |  |  | 2026-08-11 — KI-56 is fixed with the Escape Rope the DUNGEON provides, not a shopping detour |
| `2026-08-11-b5f5e5` | 1597 |  |  | 2026-08-11 — every button in the teach flow goes through a recording `_press()` wrapper |
| `2026-08-11-1dd71e` | 1585 |  |  | 2026-08-11 — a fault injection that models a TIMING miss must fire exactly once |
| `2026-08-11-504bee` | 1565 |  |  | 2026-08-11 — menu detectors watch the INPUT HANDLER, not just the display task |
| `2026-08-10-956ff4` | 1547 |  |  | 2026-08-10 — the en-route heals are best-effort; the chapter does not die on a nice-to-have |
| `2026-08-10-48295f` | 1527 |  |  | 2026-08-10 — grade Jagged Pass reachability by VAR_JAGGED_PASS_STATE, never by calculate_path |
| `2026-08-10-80c3c4` | 1507 |  |  | 2026-08-10 — Ch15 is built as THREE separately-graded increments, not one chapter function |
| `2026-08-10-3706c8` | 1491 |  |  | 2026-08-10 — KEEP the self-correcting index space rather than hard-coding one rule |
| `2026-08-10-f85760` | 1473 |  |  | 2026-08-10 — SPEND ON CONTENT (coverage), not on optimising the first six badges |
| `2026-08-10-eb76fe` | 1455 |  |  | 2026-08-10 — PROMOTE `#24-battleitems` with NO resolved outcome metric |
| `2026-08-10-8ad582` | 1437 |  |  | 2026-08-10 — RETIRE the finish rate as a grading metric; grade content BINARY |
| `2026-08-12-2e3274` | 1400 |  |  | 2026-08-12 — gates must REFUSE, and their scope is chosen so they stay believed |
| `2026-08-12-c9b1f7` | 1382 |  |  | 2026-08-12 — the party-selection menu is DRIVEN AND VERIFIED, not mashed |
| `2026-08-12-15152d` | 1361 |  |  | 2026-08-12 — §Ch19 is ONE segment covering TWO beats, graded on `RECEIVED_HM_DIVE` |
| `2026-08-06-e37aa0` | 1325 |  |  | 2026-08-06 — `#24-roster`: USER RULINGS on the PC roster / duplicate-catch exemption |
| `2026-08-05-26c51a` | 1286 |  |  | 2026-08-05 — `#24-hmslots`: RESERVE SLOTS. Deeper teams are deferred to an organic-play pass. |
| `2026-08-05-548af8` | 1256 |  |  | 2026-08-05 — USER DIRECTIVE: stop bisecting after this batch; get back to STORY CONTENT |
| `2026-08-02-b1072f` | 1215 |  |  | 2026-08-02 — Lead policy: super-effectiveness outranks level ONLY for a hunted counter |
| `2026-07-31-cf6a0e` | 1175 |  |  | 2026-07-31 — USER RULING: `#24-dexhunt` is "always catch new, WHEN IT IS CHEAP" |
| `2026-07-31-609d87` | 1157 |  |  | 2026-07-31 — The candidate progress filter rejects only moves AWAY, never "not strictly closer" |
| `2026-07-31-c846f7` | 1108 |  |  | 2026-07-31 — Warp planning becomes MAP-granular, but the walk decision stays with `calculate_path` |
| `2026-07-31-7e8b7a` | 1093 |  |  | 2026-07-31 — Headless lanes keep the RENDERER on (`-hl`, never `-nv`) |
| `2026-07-31-40bea4` | 1067 |  |  | 2026-07-31 — The headless batch runner ASSERTS the emulation config; it does not set it |
| `2026-07-30-c8fc9d` | 1035 |  |  | 2026-07-30 — Menu entries keep a FIXED position; a disabled entry beats a missing one |
| `2026-07-30-441578` | 998 |  |  | 2026-07-30 — The counter hunt is bounded by PER-RUN STATE, not by retries or frames |
| `2026-07-30-e695a0` | 958 |  |  | 2026-07-30 — Counter hunting grounds are a WHITELIST, and huntability is separate from reachability |
| `2026-07-29-9b440e` | 916 |  | cue | 2026-07-29 — Debug Story modes force unthrottled + video ON; this SUPERSEDES the 2026-07-26 "never touch video" rule |
| `2026-07-29-575205` | 859 |  |  | 2026-07-29 — USER RULINGS on the six open questions |
| `2026-07-27-aed0cc` | 839 |  |  | 2026-07-27 — Fixed-in-sandbox issues stay in 05-KNOWN-ISSUES until promotion (PROVISIONAL) |
| `2026-07-27-a5d154` | 813 |  |  | 2026-07-27 — Documentation audits use read-only agents; only the main thread writes |
| `2026-07-27-ce41e5` | 784 |  |  | 2026-07-27 — The per-run frame budget is enforced by stepping the generator, not by a timer |
| `2026-07-26-6ecd41` | 769 |  |  | 2026-07-26 — Lead policy and the Route 110 rival cap are NOT fixed autonomously |
| `2026-07-26-b2fb26` | 749 |  |  | 2026-07-26 — `run_index` dedupe by ownership, not by adjacency |
| `2026-07-26-2e8395` | 729 |  |  | 2026-07-26 — Per-run state gets an explicit reset method, not a fresh object |
| `2026-07-26-db1f0f` | 695 |  |  | 2026-07-26 — Cold-start runs decorrelate via a random pause on the NAMING SCREEN |
| `2026-07-26-a0aed2` | 681 |  |  | 2026-07-26 — The parent→child command channel is a SEPARATE shared-memory region |
| `2026-07-26-a91740` | 660 |  |  | 2026-07-26 — Log collection is park → copy → VERIFY → archive, and never reorders |
| `2026-07-26-27c12c` | 645 |  |  | 2026-07-26 — The badge recorder ships BEFORE the trainer-card UI that motivated it |
| `2026-07-26-4581ad` | 624 |  |  | 2026-07-26 — A lane's party travels as JSON and is rebuilt as stand-ins, rather than forking the party renderer |
| `2026-07-26-f3d7de` | 612 |  |  | 2026-07-26 — Separate profiles per lane, not one shared profile with tagged logs |
| `2026-07-26-d4cbc7` | 598 |  |  | 2026-07-26 — Lane profiles are BOT-MANAGED: `story.yml` is rewritten on every batch launch |
| `2026-07-26-940959` | 570 |  |  | 2026-07-26 — ENDLESS LOOP ×4 runs as four CHILD PROCESSES, not four emulators in one process |
| `2026-07-26-a96c47` | 556 |  |  | 2026-07-26 — Validation runs are BATCHED across fixes, not run per fix (user directive) |
| `2026-07-26-8e9970` | 537 |  |  | 2026-07-26 — Hard-won map/route facts live in the DECISION CODE, not in prose (user directive) |
| `2026-07-26-42f4fa` | 515 |  |  | 2026-07-26 — ENDLESS RESET restores SPEED but never touches VIDEO (user directive) |
| `2026-07-25-3dee16` | 484 |  |  | 2026-07-25 — Battle-handler faults reach the mode by an OPT-IN channel, not by an exception |
| `2026-07-25-0e1f48` | 423 |  |  | 2026-07-25 — The TRAINING gate switches to `region_reach` too (KI-24 closed on both consumers) |
| `2026-07-25-23544a` | 392 |  | cue | 2026-07-25 — "Endless reset runs" ships as an IN-PROCESS bot mode, reversing the shipped launcher |
| `2026-07-25-7e01c4` | 368 |  |  | 2026-07-25 — The Gemini Pro-3.1+ requirement is enforced in CODE, not by a doc rule |
| `2026-07-25-ce6123` | 335 |  |  | 2026-07-25 — Hop count is a FILTER (`max_hops=4`), never a RANK |
| `2026-07-25-88df32` | 306 |  |  | 2026-07-25 — `region_reach` is a NEW predicate, not a repair of `calculate_path` |
| `2026-07-25-4fa5ea` | 280 |  |  | 2026-07-25 — Ground decomp research in a LOCAL SPARSE CLONE, not per-file `gh api` fetches |
| `2026-07-24-a43bab` | 246 |  |  | 2026-07-24 — Budget training in FRAMES, not levels (punch-list #24) |
| `2026-07-24-a43da8` | 221 |  |  | 2026-07-24 — Fodder grass: SKIP the grind rather than travel, and keep the trigger conservative |
| `2026-07-24-f32198` | 193 |  |  | 2026-07-24 — Orchestration: premium orchestrator + cheap workers, gated by the HARNESS (not by model opinion) |
| `2026-07-24-d62320` | 177 |  |  | 2026-07-24 — KI-15: clear the post-battle input wedge at the RUN-LOOP seam, not in the rider |
| `2026-07-23-22885f` | 165 |  |  | 2026-07-23 — Proactive prep is a hint; reactive escalation is the guarantee |
| `2026-07-23-71564b` | 152 |  |  | 2026-07-23 — Research answers never supply numbers the ROM already knows |
| `2026-07-23-463b22` | 137 |  |  | 2026-07-23 — Derive the Lavaridge maze from ROM data; don't explore it or hardcode it |
| `2026-07-21-3d5d1d` | 121 |  |  | 2026-07-21 (revised) — PokéNav Match-Call tutorial: FAITHFUL primary, state-write fallback |
| `2026-07-21-b2a107` | 99 |  |  | 2026-07-21 — Skip the forced PokéNav Match-Call tutorial via a targeted state-write |
| `2026-07-18-2d9552` | 86 |  | DO-NOT-REOPEN | 2026-07-18 — Emerald ROM stays tracked in the repo (user ruling) |
| `2026-07-17-c7d216` | 63 |  | cue | 2026-07-17 — Installer implemented as git-driven one-script (supersedes provisional entry) |
| `2026-07-17-61ace6` | 40 |  |  | 2026-07-17 — Two-folder fork layout + daily upstream sync (user directive) |
| `2026-07-17-fb3c6f` | 27 |  | SUPERSEDED | 2026-07-17 — Installer enhancement will ADAPT, not literally apply, the base64 pattern |
| `2026-07-17-ba32a6` | 14 |  |  | 2026-07-17 — Vendor upstream via git subtree (squashed), not clone/submodule |
| `2026-07-17-31ec7b` | 7 |  |  | 2026-07-17 — Adopted the Claude Code Project Kit |
