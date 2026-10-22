# S2-1b recon: what a cold start needs from 04-HANDOFF.md (content angle)

Recon only. Nothing in the repo was changed. HEAD `f9353aec`, `## main...origin/main` (MEASURED: `git status -sb`; one untracked file not mine: `tools/scripts_census.py`).
Byte figures are UTF-8 content bytes per line, measured by a scratch script (`len(line.encode())+1`). The file is CRLF: `wc -c` = 403,243, my per-line sum = 402,344, a difference of 899 = one CR per line (MEASURED). Tags: MEASURED / READ / INFERRED / UNKNOWN.

LOOKUP-FIRST: `py -3.12 tools/decomp_lookup.py ask "handoff slim-down S2-1b"` -> `NO PRIOR RULING OR FACT FOUND`, exit 3 (MEASURED). `grep -n S2-1b 06` -> 06:9573 "The handoff's 60 KB target is a SEPARATE design item, S2-1b ... splitting 04's mega-lines alone is refused by R3 (883 -> 1,069 lines)" (READ). I found nothing contradicting the ALREADY ESTABLISHED list.

## (1) Line-range table (classification + bytes)

Mega-lines over 3,000 chars (MEASURED, chars / bytes): 6: 23,670 / 24,098; 17: 31,416 / 32,304; 305: 3,120 / 3,192; 307: 14,097 / 14,480; 312: 24,531 / 24,962; 313: 16,110 / 16,293; 381: 4,252 / 4,329; 384: 63,230 / 64,034; 389: 3,511 / 3,579; 402: 5,076 / 5,201; 480: 46,505 / 47,608; 568: 3,828 / 3,923; 624: 10,850 / 11,002; 891: 9,186 / 9,335. These 14 lines total ~258 KB, 64 % of the file (MEASURED sum).

| Lines / part | Bytes | Class | Evidence (quoted) |
|---|---|---|---|
| 1-5 title, sync note, repo URL | 245 | LIVE-NOW | 04:5 "**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git" |
| 6 chars 0-1389 (2026-10-22 + 2026-10-21) | 1,409 | LIVE-NOW | "**Last updated:** 2026-10-22 (S3-4 slice 1, KB2, ✅ BUILT and verified; ... C: was cleared of 60 GB ..." |
| 6 chars 1389-2114 (2026-10-19) | 754 | HISTORY | "and 2026-10-19 (⏸ **PARKED until the weekly reset ..." |
| 6 chars 2114-23670 (2026-10-16 back to 2026-09-28) | 21,934 | HISTORY | "and 2026-10-03 (⭐ **HYBRID CHOSEN (USER RULING 31) ..." through §Ch24 "*(Previous: §Ch24 S2 — `fight_one_room()` ..." |
| 7-16 Fly-ladder corrections 2026-09-23 | 2,851 | HISTORY (story bot) | 04:8 "THE 2026-09-23 FLY-LADDER NUMBERS PUBLISHED EARLIER THAT DAY WERE WRONG" |
| 17 (PIECE 2a + "§Ch24 IS BEATEN END TO END") | 32,304 | HISTORY | "*(Previous entry: 2026-09-19 — PIECE 2a shipped ..." / "§Ch24 IS BEATEN END TO END" |
| 18-20 | 57 | structural | 04:18 "Every banner further down is HISTORY, newest first." |
| 21-123 overnight run 09-06/07, 09-09/10 telemetry, dexhunt fence | 15,532 | HISTORY (story bot) | 04:22 "OVERNIGHT RUN, 2026-09-06/07"; 04:100 "`#24-dexhunt`'s CATCHING FENCE IS BUILT" |
| 124-125 retired-banner heading | 494 | HISTORY pointer | 04:125 "THE OLD “YOU ARE HERE” BANNER — **RETIRED HISTORY, ARCHIVED 2026-09-24" |
| 126-141 reading order + single-marker rule | 1,255 | LIVE-RULE (gate H1 enforces the marker; 00-README row 1 repeats the grep) | 04:130 "EXACTLY ONE LINE IN THIS FILE *BEGINS* WITH `>    ➡➡➡`" |
| 142-161 line budgets, ARCHIVE FIRST | 2,244 | LIVE-RULE (partly DUPLICATE of lint_docs output) | 04:149 "ARCHIVE FIRST, WRITE SECOND — AN INSTRUCTION, NOT A CAUTION" |
| 162-174 STEP 0 sync + daily upstream fetch | 838 | LIVE-NOW (DUPLICATE of CLAUDE.md §1 and the daily-upstream rule) | 04:166-167 "git status --short && git fetch && git status -sb" / "git fetch upstream-pokebot && git rev-parse --short upstream-pokebot/main" |
| 175-180 preflight + run_gates + gate-count history | 4,090 | LIVE-NOW for ~150 B; the rest HISTORY (count trail) | 04:175 "`PYTHONUTF8=1 py -3.12 preflight.py` and `PYTHONUTF8=1 py -3.12 run_gates.py` ⭐ **NEW 2026-09-14:** gate **#61**" |
| 181-213 suite green again 2026-09-11, old reds | 3,895 | HISTORY | 04:182 "THE SUITE IS GREEN AGAIN — `repro_gym_whiteout_guard.py` WAS FIXED 2026-09-11" |
| 214 "State: main ..." | 1,830 | HISTORY; its KI-82 do-not is DUPLICATE of 06 | 04:214 "⛔ Do not re-raise it; the only condition that reopens it is the repo being made PUBLIC." |
| 215-220 disk 87 % (2026-08-18) | 661 | HISTORY | 04:215 "DISK: 87% used, 247 GB free (RE-MEASURED 2026-08-18 ..." |
| 221-223 do not copy a whole fork to scratch | 217 | LIVE-RULE | 04:221 "do NOT copy a whole fork to scratch" |
| 224-235 `#24-sanitycheck` | 1,304 | HISTORY | 04:224 "THE DEEP SANITY CHECK ... IS COMPLETE — 5 of 5" |
| 236-242 expected dirt (party_accounting_ledger) | 712 | LIVE-RULE (DUPLICATE: `preflight.py` annotates it, `grep -c party_accounting_ledger preflight.py` = 2) | 04:239 "Do NOT `git checkout --` it — COMMIT it with the work that produced it" |
| 243-272 drift history, promotion method rules, §Ch20 rooms | 4,228 | HISTORY + ~400 B LIVE-RULE (258-261) | 04:259 "a comment-only promotion is proved behaviour-neutral by **AST equality**" |
| 273-281 §Ch20 shipped, §Ch21 naming, 60-second pointer | 1,026 | HISTORY | 04:274 "§Ch20 — SHIPPED AS A CHAPTER 2026-08-24 — ⛔ DO NOT REBUILD" |
| 282-297 WHAT THIS IS | 1,131 | LIVE-NOW but STALE: describes only the story bot | 04:283-285 "`sandbox-pokebot/` is the working build ... Its **Story mode** plays the game ... **All work happens in `sandbox-pokebot/`.**" (no AI player, no tuner) |
| 298-301 STATE head + branch row | 245 | LIVE-NOW | 04:301 "**⛔ TRUST `git status`, NOT THIS CELL.**" |
| 302 box: chars 0-309 | ~330 | LIVE-NOW | "the BOT TUNER (`ai-agent/`, 24/7 learner) RUNS 12 headless lanes from its own clone" |
| 302 rest | ~1,730 | HISTORY | "*(Older, story bot:)* ▶ **Step 14's batch `20261001-210001` RAN**" |
| 303-307 story chapter rows §Ch19-§Ch24 | 21,833 | HISTORY (story bot; DUPLICATE of 12-STORYMODE/07) | 04:307 "**§Ch23 VICTORY ROAD / §Ch24 THE LEAGUE** ..." |
| 308 is code frozen? | 314 | LIVE-NOW | "**No (2026-10-21).** ... The bot tuner runs 24/7 from its OWN clone, so commits here are safe" |
| 309 party ORDER | 352 | HISTORY | "**PROVEN 2026-08-13.** `--driver roster`" |
| 310 upstream: chars 0-458 | ~470 | LIVE-RULE (parked by ruling); date STALE | "USER RULING 2026-09-26: “NOT NOW, KEEP IT PARKED.” ⭐ Daily check **2026-10-02**" while `40cakes repo/UPDATE-LOG.md:30` reads "Re-checked **2026-10-14**: unchanged (`3bd0b70c`)" |
| 310 rest | ~2,115 | HISTORY (DUPLICATE of UPDATE-LOG) | "*(Previous:)* Daily check **2026-09-29** ..." |
| 311 restore point: chars 0-240 | ~245 | LIVE-RULE | "**NEWEST: `restore/2026-08-17-pre-promotion-all5`**" (matches `git tag -l "restore/*" --sort=-creatordate` top line, MEASURED) |
| 311 rest | ~2,140 | HISTORY | "Previous: **`restore/2026-08-17-pre-promotion-ki66-onfield`** ..." |
| 312 drift: chars 0-151 | ~160 | LIVE-RULE; the one place `probe_drift_restatement.py:21` allows a dated drift digit | "**31 as of 2026-10-07 (LATEST): +`plugins/custom_modes/ai_player_mode.py`" |
| 312 rest | ~24,800 | HISTORY (DUPLICATE of `custom-pokebot/DIVERGENCE-LOG.md`) | " 30 as of 2026-10-03: +`modules/story/bossmode_topup.py` ..." |
| 313 mid-task: chars 0-2168 | ~2,190 | LIVE-NOW (in progress, unpushed rule) | "(if `git status` says AHEAD, that push did not happen: push first) ... never lower `keep_raw_cycles` below 17 before `archive-check` prints OK ai0024." |
| 313 chars 2168-4485 | 2,323 | HISTORY | "*(History:)* ✅ **2026-10-16: step 5.2 is COMMITTED" |
| 313 chars 4485-12481 | 8,082 | HISTORY + the parked-branch sentence (LIVE-RULE, DUPLICATE of 384 and 03:103-104) | "TWO STORY-BOT BRANCHES ARE PARKED MID-TASK ... `wt/gradeidentity` ... `wt/boxfirst`" |
| 313 chars 12481-16110 | 3,701 | HISTORY / meta-rules | "THE DATE IS THE PART THAT ROTS, NOT THE CLAIM." |
| 314 git stash KEPT | 1,047 | LIVE-RULE (06 holds the ruling, `grep -c "stash@{0}" 06` = 1) | "⛔ **Standing rule: never `git stash drop` / `clear` / `pop` in this repo.**" |
| 316-328 archived-session lessons (10 stubs merged) | ~5,700 | LIVE-RULE (method lessons; only partly DUPLICATE: the playbook has "can continue" 1 hit, "missing primitive" 1 hit, "adversarial agent" 0 hits) | 04:318 "A CHAPTER'S ACCEPTANCE TEST MUST INCLUDE "AND THE BOT CAN CONTINUE"" |
| 330-335 §Ch19-era issues | ~2,800 | HISTORY (DUPLICATE of 05/31) | 04:335 "Moved for the R3 budget; all four are in `05-KNOWN-ISSUES.md` or its archive" |
| 337-345 NEXT ACTIONS heading + preamble | 998 | LIVE-NOW (preamble partly stale) | 04:341 "**Two story-bot branches ARE parked mid-task (`wt/gradeidentity`, `wt/boxfirst` ...). The AI learner `ai-agent/` runs 24/7.**" |
| 346-383 item 0 August work, §Ch21, sanitycheck, 03 headroom | 8,720 | HISTORY | 04:351 "QUEUE ITEM 0'S AUGUST WORK IS ALL DONE — ⛔ DO NOT RE-RUN ANY OF IT." |
| 384 (the ➡➡➡ line) | 64,034 | see (3) | |
| 385-479 §Ch24 build history, safety batch, wallydecline, older blocks | 31,649 | HISTORY (story bot) | 04:389 "⛔ **SUPERSEDED HISTORY (done since: `enter_the_league` ...)" |
| 477-479 never edit the tree while a batch runs | ~235 | LIVE-RULE for story batches only | 04:477 "NEVER COMMIT OR EDIT THE TREE WHILE A BATCH RUNS" |
| 480 (14 §Ch23 blocks) | 47,608 | HISTORY (story bot) | 480 parts all start "✅✅✅ ... DO NOT REBUILD" or "⛔⛔⛔ THE MOST DANGEROUS CLAIM IN THIS CHAPTER" (§Ch23) |
| 481-621 parallel build list, older standing items, orphans, P5/P6, §Ch20 | 18,414 | HISTORY; ~1 KB LIVE-RULE in 587-596 | 04:589-590 "THREE RULES SURVIVE AND ARE STILL LIVE: (1) ⛔ **do NOT add a row to `TRAINING_GRASS`**" (05 has 2 TRAINING_GRASS hits, 31 has 7) |
| 622-623 queue item 1 (preflight + gate-count trail) | 751 | DUPLICATE of 175 / HOW TO RUN; count trail is HISTORY | 04:622 "1. **Run `preflight.py`**, then the gate suite" |
| 624 drift EXPECT trail | 11,002 | HISTORY (DUPLICATE of 312 and DIVERGENCE-LOG) | "⚠ **EXPECT 31 differing as of 2026-10-07 (LATEST; ..." |
| 625-652 drift notes, queue 3b, archived pointers | 2,679 | HISTORY | 04:637 "THE SURVIVING QUEUE ITEMS ARE ONLY `0`, `1` AND `3b`." |
| 653-685 HOW TO RUN: ops, usage audit, lookup, regression, KB2, chapter packs | 3,638 | LIVE-NOW | 04:655 "### The bot tuner's ops tools, the usage audit and the lookup — added 2026-10-21" |
| 686-709 story v2 steps 8-14 recipes + archived pointers | 3,728 | HISTORY (story bot, PARKED) | 04:686 "### Design v2 steps 8-9b (story bot, PARKED)" |
| 710-720 preflight / run_gates / --quick / --list | 1,153 | LIVE-NOW | 04:714 "PYTHONUTF8=1 py -3.12 preflight.py        # ‼ RUN THIS FIRST." |
| 721-744 grade_ki93, chapter order, stale citations, ki76, abort ratchet | 2,250 | story-bot recipes (734-739 `probe_stale_citations.py` is a generic LIVE-RULE) | 04:734 "RUN THIS BEFORE TRUSTING ANY `file.py:NNN`" |
| 745-770 §Ch20 / P4 / KI-66 / KI-80 / party accounting | 2,330 | story-bot recipes / pointers | 04:754 "KI-66 — the faint chooser inside the Steven MULTI battle" |
| 771-786 doc gates (Tier 0) | 1,311 | LIVE-NOW | 04:771 "THE DOC GATES — MANDATORY before ANY commit touching PROJECT KNOWLEDGE (Tier 0)" |
| 787-850 §Ch24 grind / gauntlet / bridge / rooms / tail / KI-93 | 8,410 | story-bot recipes | 04:798 "§Ch24 THE WHOLE CHAPTER AS ONE CHAIN (`run_the_gauntlet`)" |
| 851-852 promote --check | 184 | LIVE-RULE (bot fork ops) | 04:852 "promote.py --check            # measures drift BOTH ways, changes nothing" |
| 853-878 drift-check notes, promote procedure, custom-fork gates | 2,690 | story-bot ops; 867-870 LIVE-RULE ("To PROMOTE (the USER's call, never assume it)") | 04:867 |
| 879-883 suite safe to run bare | 669 | LIVE-RULE | 04:881 "`env -u PYTHONUTF8 PYTHONIOENCODING=cp1252 py -3.12 run_gates.py --quick` (must exit 0)" |
| 884-890 driver keeps running after ACCEPTANCE | 503 | story-bot recipe rule | 04:886 "**Read the `ACCEPTANCE:` line, not the last line.**" |
| 891 drift verify | 9,335 | HISTORY, and it CONTRADICTS 312 | 04:891 "✅ **Expect 0 as of 2026-09-16 (later)" vs 04:312 "**31 as of 2026-10-07 (LATEST)" |
| 892-899 footer | 292 | structural | 04:898 "This file is CURRENT STATE only" |

## (2) Quality bar: where 04 answers it today, and the bytes a slim answer needs

| Question | Where 04 answers it now (quoted) | Slim size (INFERRED) |
|---|---|---|
| What is this project | 04:282-296 "WHAT THIS IS", which is STALE (story mode only, "All work happens in `sandbox-pokebot/`"). The real answer is spread across 384:9-1608 ("The user chose the HYBRID (USER RULING 31)", "USER RULING 35: the AI PLAYS THE GAME ITSELF") and CLAUDE.md FOCUS | ~800 B, rewritten (not verbatim) to name the AI player, the bot tuner and the parked story bot |
| State right now | 04:6 chars 0-1389; STATE rows 301, 302 (first 309 chars), 308, 313 (chars 28-2168) | ~3.5 KB |
| What was just done | 04:6 "2026-10-22 (S3-4 slice 1, KB2, ✅ BUILT and verified; its chapter-pack tool ✅ BUILT ... C: was cleared of 60 GB" | ~1 KB (inside the banner head) |
| In progress | 04:313 "IN FLIGHT ON THE LIVE SYSTEM: O3 runs in the bot tuner since 4:08 PM 2026-10-21 with the canary K=17, and O6+O7 since 4:09:58 AM 2026-10-22; O5 restarts at the end of ai0041"; parked branches 384 chars 13600-15329 | ~2.2 KB + ~1.7 KB |
| Next | 384 chars 3517-11632: "(0a2) ... STILL TO DO: CONFIRM O5's restart", "(0b) THE CANARY ... THEN run `py -3.12 learner.py archive-check`", "Then the backlog's TOP-15 ORDER ... AUTHORITATIVE", "(3) STEP 5.3: first B1 + N8's grader half" | ~8 KB verbatim; ~3 KB if it pointed to `ai-research-notes/2026-10-18-improvement-backlog.md` lines 3-19, which duplicate the order (that file says "the top 15 in build order") |
| How to run/build/test | 04:653-685 (ops, regression, KB2, packs), 710-720 (preflight, run_gates), 771-786 (doc gates), 162-174 (sync ritual) | ~7 KB |
| Gotchas / unpushed work | 04:313 "if `git status` says AHEAD, that push did not happen: push first"; 04:314 stash rule; 04:236-242 expected dirt; 04:142-161 archive first; 04:221-223 scratch; 313 "never lower `keep_raw_cycles` below 17" | ~4.5 KB |
| Remote URL | 04:5 | 76 B |

MEASURED gap: the Project Kit session-start hook reads a `## If stopped mid-task` SECTION (`.claude/hooks/session-sync.ps1:70`, regex `'(?ms)^##\s*If stopped mid-task\s*(.+?)(?:^##\s|\Z)'`). 04 has no such heading (`grep -n "^##\s*If stopped" 04-HANDOFF.md` -> exit 1); the mid-task answer is a table row (04:313 "| **if stopped mid-task** |"). So the hook's RESUME POINT line never fires today. A slim 04 could add the heading.

## (3) The ➡➡➡ line (04:384, 64,034 B) split into parts

| Chars | Bytes | Part | Class |
|---|---|---|---|
| 0-9 | 15 | the marker `>    ➡➡➡` | LIVE (gate H1, `audit_handoff_invariants.py` MARKER_RE `^>\s{2,}➡➡➡`) |
| 9-1608 | 1,613 | 2026-10-03 hybrid ruling, learner session-start steps, R35, v1 design draft | LIVE-NOW orientation, largely DUPLICATE of CLAUDE.md (FOCUS / AI learner sections) |
| 1608-3517 | ~1,920 | STEP 0 ... STEP 5.2 done list (2026-10-07 to 2026-10-16) | HISTORY, but a compact AI-frontier summary a cold start uses (INFERRED) |
| 3517-3717 | 202 | (0a) DONE: O3 deployed | HISTORY (done) |
| 3717-4588 | 873 | (0a2): O6+O7 restart confirmed; STILL TO DO: confirm O5's restart at the end of ai0041 | LIVE-NOW |
| 4588-5073 | 485 | (0b) the canary K=17, then archive-check, then K=4 | LIVE-NOW |
| 5073-5719 | 650 | (0c) DONE: backup + watchdog registered; "-Apply registers EVERY task" | HISTORY + one LIVE-RULE sentence |
| 5719-~7000 | ~1,300 | (0d) DONE: evidence identity, lane re-runs, the retire | HISTORY except the recipe "Re-run the lane (`py -3.12 ai_player/gates/run_regression.py --full --evidence`, about 72 min, detached, no commit while it runs)" (LIVE-RULE; DUPLICATE of 04:677) |
| ~7000-11161 | ~4,200 | the ordered work list: backlog TOP-15 order, steps 1-2 status, step 3 (KB1, KB2, chapter packs, W7), (1) KB1, (1b) A6, (2) the lean setup incl. S2-1b | LIVE-NOW (much of it is "✅ BUILT" status, DUPLICATE of the backlog summary) |
| 11161-11632 | 471 | (3) STEP 5.3: B1 + N8, then chapters 3-4, then self-tuning; cloud jobs paused | LIVE-NOW |
| 11632-13600 | ~1,970 | *(Previous:)* step 5.1 done, 5.2 plan, RULINGS 33/36 notes, BOSSMODE_TOPUP | HISTORY (rulings DUPLICATE of 06) |
| 13600-15329 | ~1,750 | parked story-bot branches + "Story-bot next, when the user resumes it, in order" | LIVE-RULE (DUPLICATE of 03:103-104 `#27-boxfirsttype` / `#27-gradeidentity`) |
| 15329-48885 | ~33,900 | "THE OLDER TEXT OF THIS LINE FOLLOWS. **⏩ CURRENT AS OF 2026-10-02 (~11 AM): STEP 14 IS GRADED**" and older (2026-09-29, 09-28 START HEREs, §Ch24) | HISTORY |
| 48885-~50400 | ~1,500 | upstream-merge procedure: "THREE THINGS BEFORE YOU RUN STEP 2 ... (a) IT IS A MERGE ONTO `main` ... ASK THE USER" | LIVE-RULE (parked by ruling; partly DUPLICATE of CLAUDE.md daily-upstream rule and `40cakes repo/UPDATE-LOG.md`) |
| ~50400-63230 | ~12,800 | "*(Everything below this sentence is COMPLETE work, not instructions:)*" PC-first HM path, §Ch24 champion leg | HISTORY |

Live share of 384 (MEASURED offsets, INFERRED split): ~11.7 KB in chars 0-11632, plus ~1.75 KB of parked branches and ~1.5 KB of the upstream-merge rule. About 49 KB is history.

Defect found while reading (MEASURED): 384 char ~9026 says "(see the (P3b) line below)", but the only (P3b) line is 04:237, above it.

## (4) HOW TO RUN (04:653 on): live versus story-bot

LIVE work (keep, ~7.3 KB):
- 655-684 (3,638 B): status.py, usage_audit, decomp_lookup, build_rulings_index, learner archive-check, test_agent.py, backup_learner, install_ops_tasks, selftest_ops/usage_audit/seasoned_crosscheck, extract_experience + its selftest, workflows render/stage_helpers/regression_due/selftest, lint_docs --rewaive, archive_sweep, run_regression --quick/--full, extract_world/verify_world/test_kb2, make_chapter_pack, selftest_chapter_pack, selftest_lint_docs. Covers: AI player gates and regression lane, the learner, ops, doc gates, chapter packs.
- 710-720 (1,153 B): preflight, run_gates (all / --quick / --list).
- 771-786 (1,311 B): the doc gates (lint_docs, audit_handoff_invariants + --self-test, audit_doc_consistency, audit_encoding), plus the PowerShell-corruption rule.
- 879-883 (669 B): the suite is safe bare; the cp1252 check.
- 851-852 + 867-870 (~540 B): promote --check and "To PROMOTE (the USER's call, never assume it)": a bot-fork rule, still live as a do-not.
- MISSING from HOW TO RUN, present only in prose: the learner status command `py -3.12 "C:/Remote Projects/pokebot-learner/ai-agent/learner.py" status` (04:384 chars 9-1608 and CLAUDE.md), and the sync ritual (04:166-167). The AI player's live drivers (`live_step5.py`, `rate_step5.py`) are named only in 384 prose; `ai_player/README.md` "## Run it" (line 284) holds them (READ: grep only).

Story-bot recipes (PARKED; candidates to move, ~20 KB): 686-709 (3,728 B; v2 steps 8-14 incl. `x4_headless.py ... --arms arms/batch14.json`); 721-744 (2,250 B; grade_ki93, chapter order, ki76warp, abort ratchet; except 734-739 `probe_stale_citations.py`, a generic rule); 745-770 (2,330 B); 787-850 (8,410 B; §Ch24 grind/gauntlet/bridge/rooms/tail/KI-93); 853-866 + 871-876 (~2.1 KB drift-check notes, custom-fork gates); 884-890 (503 B, ACCEPTANCE vs HANG CONFIRMED); 891 (9,335 B).
Gate note (READ, `audit_handoff_invariants.py:13-20`): H2 needs the HOW TO RUN section to exist with a non-trivial body; H3/H4 check only the drivers and fixtures that ARE named, so removing story recipes cannot turn them red (INFERRED). `probe_runrecipe_fixtures.py` scans 04's runnable recipes for DEAD fixtures (READ, line 2).

## (5) Estimate of a minimal 04 (verbatim keep-set; INFERRED from the MEASURED sizes above)

| Kept part | Bytes |
|---|---|
| 1-5 header + URL | 245 |
| 6 banner head (chars 0-1389) | 1,409 |
| 126-161 marker rule + budgets/archive-first | 3,499 |
| 162-174 sync ritual | 838 |
| 175 preflight/run_gates line | 836 |
| 221-223 scratch rule + 236-242 expected dirt | 929 |
| 282-296 WHAT THIS IS (needs a rewrite to be true) | 1,131 |
| STATE: 298-301, 302 head, 308, 310 head, 311 head, 312 head, 313 head (0-2168), 314 | ~5,000 |
| 337-345 NEXT ACTIONS heading + preamble | 998 |
| 384 chars 0-11632 + parked branches (13600-15329) | ~13,480 |
| HOW TO RUN 653-685, 710-720, 771-786, 851-852, 879-883, 893-899 | ~7,250 |
| headings / blanks | ~300 |
| **Core total** | **~35.9 KB** |
| Optional LIVE-RULE extras: 316-328 lessons (~5.7 KB), 587-596 TRAINING_GRASS rules (~1 KB), 258-261 AST-equality rule (~0.4 KB), upstream-merge "three things" (~1.5 KB), 734-739 stale-citations probe (~0.6 KB) | +~9.2 KB |
| **With extras** | **~45 KB**, under the 60 KB target (`lint_docs.py:226` SEED_TARGETS `{"04-HANDOFF.md": 60 * 1024}` = 61,440 B) |

Lines: header 5 + banner 2 + 126-175 50 + 221-242 ~10 + WHAT THIS IS 15 + STATE 11 + NEXT 9 + 384 split under `MAX_LINE_CHARS = 1200` (`lint_docs.py:218`), ~13.5 KB, so about 13 lines + HOW TO RUN ~74 + headings/blanks ~25: **about 215 lines (~245 with the extras)**, far below the 900-line R3 budget (`lint_docs.py:126` `"04-": 900`). The banner head (1,389 chars) and the 313 head (2,140 chars) still exceed 1,200, so they need a split or a kept waiver; `long_line_waivers.json` holds 28 waivers for 04 keyed on the first 60 chars (`WAIVER_KEY_CHARS = 60`, MEASURED count). Bytes moved out: ~402 KB minus ~36-45 KB = **~357-366 KB** into the archive (1.25 MB, which R8 does not police: `lint_docs.py:31` "on 00-README + 01-05").

Constraints the move must keep (READ): `audit_doc_consistency.py:1193-1204` needs a "Last updated:" line; `probe_drift_restatement.py:21` makes the STATE drift row the only place a dated drift digit may appear; gate H1 needs exactly one `>    ➡➡➡` line. P4: `00-README.md:9` says "the file's opening lines are a stack of dated banners, most of them history", which a slim 04 makes false, so it must change in the same commit.

UNKNOWN: which other gates parse 04's moved text. 28 `tools/story-dev/*.py` files mention "04-HANDOFF" (MEASURED `grep -ln`), among them `probe_promoted_pair.py`, `probe_retraction_coverage.py`, `selftest_promote_drift.py` and `audit_doc_citations.py`. I did not test any of them against a slimmed copy.
