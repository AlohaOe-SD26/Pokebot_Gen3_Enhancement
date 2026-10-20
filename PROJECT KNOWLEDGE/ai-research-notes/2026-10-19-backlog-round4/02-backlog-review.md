# Backlog round 4, angle 2: EDITORIAL REVIEW of `2026-10-18-improvement-backlog.md` (2026-10-19)

A NOTE, not a decision and not a source of truth (`00-READ-THIS-FIRST.md`). Read-only: the backlog (414 lines) was read whole;
its build specs (`2026-10-19-BUILD-SPECS-steps-1-2.md`) were read for the summary, ledger and header only. Spot checks were by
grep and `ls` on this checkout and, read-only, on the learner clone `C:/Remote Projects/pokebot-learner`. Nothing was edited
except this file. Claims marked UNVERIFIED were not opened.

**Checks I made that the backlog does not contain**
- `tools/status.py`, `usage_audit.py`, `run_regression.py`, `codemap.py`, `lookup.py` and `RULINGS.md` do not exist yet: no
  A1/P3/P7/P2/N2 work has started, so every size below is a spec figure, not a measurement.
- `ai-agent/config.json` (repo and clone) holds `keep_raw_cycles` 20, and the clone's HEAD is `5a3694ab` (the push of 1:03 PM).
  BUT the clone's `data/learner.log` line 333 reads `[2026-10-19 04:04:30 PM] pruned the raw logs of ai0023`. That prune ran
  AFTER the push, with the old setting (12), because the running cycle (ai0035, `code_commit` `babad02e`) had loaded its config
  before the clone fast-forwarded. Under 20 the first deletion is ai0024, when ai0044 finishes: about 108 hours after ai0035,
  so about 2026-10-24 in the early morning (an ESTIMATE at 12 hours a cycle). On disk now: `runs/ai0024` to `runs/ai0035` hold
  a `batch` folder; ai0023 and everything older do not.
- The consult backlog cap is real: `ai-agent/consult.py:74-76` (`max_waiting_proposals`, default 6), config line 32.
- `ai-agent/learner.py:99` `load_config()` is called again at 464, 474, 485 and 388 (read, not run).

---

## 1. Executive summary: the top 15 in build order

Sizes are the spec's "new code + tests" lines where a spec exists (`BUILD-SPECS`); `est.` marks my own guess. The order is the
backlog's order with four corrections (section 3: D3 pulled into step 1, R5 before R1 + R2, A3 absorbed by the templates, A2's
agent-free half first). All savings are estimates until P3 exists.

| # | ID | Title | Why it is here | Size |
|---|---|---|---|---|
| 1 | O3 | Compress each cycle's raw logs, never delete | A6's input is deleted every 12 h; DEADLINE before ai0044 ends (about 10-24) | 85 + 95 |
| 2 | O4 | Nightly off-C: backup of `data/` and `findings/` | 2,371 games exist once, on a 96 %-full drive | 120 + 90 |
| 3 | O6 + O7 | Ops-ledger row per cycle, early-prune margin | feeds A1, O1 and the daily summary; ships in the learner train with O3 | 55 + 60 |
| 4 | P3 | `usage_audit.py` and `cost-ledger.jsonl` | every saving in the file is an estimate; one claim is already contradicted | 230 + 130 |
| 5 | A1 + D3 | One-call `status.py` with the AI frontier line | a check-in in one call (convenience; main chat is about 3 % of usage) | 170 + 90 |
| 6 | O1 | Session-free watchdog and a notification | alerts are files nobody sees; NEEDS THE USER'S OK for scheduled tasks | 285 + 150 |
| 7 | N3 + P9 (+A4 docs) | Byte and line budgets; split the 514 KB `ai_player/README.md` | cold start about 100k to 15k tokens; handoff is 390,563 bytes | 315 + 260 |
| 8 | P11 + P1 + N6 + P10 (+A3, E1) | Stage templates with READ LIST, STOP, WAIT RULE, model per stage | agents past 200 calls hold 53 % of context weight | 280 + 140 |
| 9 | N2 + P5 | Prior-art lookup: `RULINGS.md` and `facts-ledger.jsonl` | about 10 `08` entries re-asked a ruled question | est. 250 + 120 |
| 10 | A6 | Experience records from the bot's finished games (a script) | the "seasoned player" memory; needs O3 so the input survives | est. 300 + 150 |
| 11 | A5 + L1 + L2 | ONE generator: chapter packs, campaign manifest, boss book | chapter 3-4 recon cost about 16M with 9 agents; most is derivable | est. 600 + 300 |
| 12 | B1 (+R13) | Goodhart gate: grader thresholds unreachable by the AI | the AI already used the grader's own yield thresholds; gate before 5.3 | est. 80 + 80 |
| 13 | A2 (agent-free half) + P7 | `run_regression.py`, summary files, `--quick` lane | stops agents re-reading logs and waiting on suites | est. 250 + 150 |
| 14 | E2 + O8 | Per-game recording; torn-write resilience and crash-loop breaker | one lost cycle (ai0031) and about 25 % of games cut off | est. 150 + 150 |
| 15 | R5 -> R1 + R2 (+DP1, DP2, L3 a-b) | Free-screen precondition, then save/CONTINUE and a memory that survives a kill | DECIDE-EARLY: the first memory file fixes paths and schema | est. 300 + 200 |

Not in the 15 but time-critical: C1 as a one-line checklist now (section 6, edit 8). Waits on the user: O1's scheduled tasks,
O4's target disk (the specs say `E:` is a different physical disk, 47 GB free), and O3's "keep compressed logs forever".

---

## 2. Duplicates and near-duplicates to merge

| Cluster | IDs | Merge into | Note |
|---|---|---|---|
| Check-in surface | A1, O1, O6, O7, `#28-trainer-improvements` item 9 (daily summary), item 6 (heartbeat), D3, N14 | ONE ops ledger (O6) with three renderers: `status.py`, `LEARNER-STATUS.txt`, a line at the top of `LATEST.md` | item 9 is not in the backlog's order at all; without this note it gets built a second time |
| Stage agents | A3, P11, P1, N6, P10, E1 | the stage templates (order step 2) | A3 sits in step 4 although step 2 delivers it |
| Doc slimming | A4, N3, P9 | N3 + P9 | A4's `CLAUDE.md` half is dropped (edit 5) |
| Knowledge generator | A5, L1, L2, the KB1 slices, L10 | one generator | already stated in step 3 but three headers remain; build once |
| Experience records | A6, `#28-trainer-improvements` item 7, L10, C2 | A6 | item 7 IS A6; C2 is its lane policy, not a separate build |
| Cut-off games | O2, `#28-trainer-improvements` item 2, E2 (item 1), O10 | E2 first, then O2 (a config line); carry-over only if O2's cut share stays high; O10 is the bias check for either | both fix the same 23.7 % |
| AI settings as data | D2, DP5, R12, R13 | R12's registry first, D2's weight files and DP5's `personality`/`seed` on the same schema | else the files hold unregistered constants |
| Seed and clock | B6, O13's probe, DP5 `seed`, R4's `seed` field | one probe (can `x4_headless` pin the seed despite KI-112?) | one answer settles four items |
| Gate effectiveness | B2, N5, N9, N7 | B2 as the rule, N5 as its mutant generator, N9 as its reach counter | N7 (`[ev:]` markers) stays separate, medium |
| Static-gate extension | N10, B1's AST rule, R3's AST gate | one pass over the lint/`check_purity` module | three edits to the same module |
| Free screen | R5, R6, R1's "saving only on a free screen" | R5 inside R6 as one "screen state" ladder | R1 and R6 both depend on R5 |
| Disk | B4, O1's "81 to 58 GB in a day", O7 | one story | 81 - 58 = 23 GB, close to the 24.3 GB of AI temp folders of B4: PROBABLY the same event (UNVERIFIED) |
| Hooks | B5, `#27-hookhatch`, P12 | B5 | already stated |
| Claim hygiene | N1, N4, N7, LESSONS PR-1 | keep N1 + N4 first; N7 later | all four are "a prose rule broken twice" |
| Two spec copies | `backlog-round3/01-build-specs.md`, `2026-10-19-BUILD-SPECS-steps-1-2.md` | the critiqued copy | the older file differs by about 690 lines and lacks the critic's fixes (for example "no delete without a verified archive"); edit 23 marks it SUPERSEDED |

---

## 3. Contradictions (between items, with the order, or with the facts)

1. **Intro vs order.** "What gets built first: priority A items" is false by the order: A2 and A3 are step 4, A5 and A6 step 3, and
   R1, R2, R8, R9 (all labelled A) wait for 5.3 in step 6. Section heading "A. Highest value per token (build first)" repeats it.
2. **A2's premise is contradicted by the file's own Round 2** (evidence and log reads 2.2 %, suite output 7.6 %, against `.py`
   source reads 33.4 % and Bash cat/grep 36.5 %) yet the top section still states "32-50 %" as measured and keeps A2 under
   "Highest value per token". A section heading is a claim about every bullet under it (the project's own P2 rule).
3. **A4's `CLAUDE.md` half** is DEMOTED in Round 2 (38.9 KB, under 2 % of a context) but A4's body still gives "every turn of
   every agent pays" as the reason and still lists the move. There is also a real risk: a rule moved out of the auto-loaded file
   stops firing, and the SESSION DISCIPLINE block exists because rules not in front of the agent were broken.
4. **R5 vs the order.** Step 6 reads "R6, R1 + R2, R5", but R1 + R2 "save only on a free screen (R5)". R5 must come first.
5. **A1 vs D3.** A1 (step 1) prints "the AI player's frontier", which D3 (step 6) defines. Pull D3's one line into step 1.
6. **A3 vs the templates.** A3 is listed in step 4; the stage templates (step 2) "sharpen A3" and deliver it.
7. **Order step 0 "DONE" vs the learner log.** It is DONE as a push, not as an effect: ai0023 was pruned at 04:04:30 PM, after the
   push. The text "ai0001-ai0022 gone" is stale by one. Step 0 also says O3 is "the one TIME-LIMITED item" without a date.
8. **"Stop starting games that cannot finish" is REJECTED** here, but `#28-trainer-improvements` item 2 still offers it as an
   option. Strike it there.
9. **E2 / E3 say "power cut"; the folded O12 note says the cause is UNKNOWN** (an unexpected shutdown at 6:50 AM, events 41 and
   6008). E3's BIOS advice helps only if the cause is power. E3 also has no build left (autostart already worked).
10. **C1 as written invites editing the clone.** The rules say a learner setting changes by commit + push to main and reaches
    the learner only at its between-cycle fast-forward. ("Re-read every cycle" is true only after that.)
11. **B6: "Part of this exists"** with no file named, while Round 2 says "no run record holds a seed today". A reader cannot tell
    what is built.
12. **Items with no place in the order** (a cold reader cannot tell if they are dropped): C1, C2, B6, E1, E3, N5, N7, N9, P4 + P6,
    and L12's sequencing (which says L1, L2, L10 and L3 a-b are "now, with chapters 3-4", while the backlog puts L1 + L2 in step 3).
    L12 itself has no entry in the backlog; only its range "L1-L12" appears.

---

## 4. Items lacking evidence, or with stale evidence

- **Header caveat missing:** every percentage comes from an audit script that is not in the repo (P3 says so; the intro does not).
- **A1:** "3-8 tool calls ... 300k-token chat context" is one session's anecdote; the file's own "main chat about 3 %" caps the
  token benefit. Value is real but it is convenience and safety, not tokens.
- **A2 (-20-35 %), A3 (-20-40 %), P11's model saving:** estimates with no measurement behind them.
- **A4:** line counts dated 10-18; the bytes (390,563 for the handoff, a 56,940-character line, 38.9 KB `CLAUDE.md`) are in Round 2.
- **A5:** "about 16M (9 agents)" cannot be reproduced until P3.
- **B6:** see contradiction 11. **C2:** "flat at 13-17 % for four weeks" has no source or date (cite `findings/LATEST.md`).
- **O3:** "ai0001-ai0022 gone" stale (now ai0023); "about 11 GB of 79 free" vs config "+10 GB of 78 GB free" vs the older config
  comment "about 4 GB a cycle" vs "about 1.3 GB" in the newer one. Pick one measured number.
- **O4:** "confirm `E:` is one" is resolved by the build specs. **O1:** "81 to 58 GB" is undated and probably B4's temp folders.
- **Undated counts that disagree:** 2,371 games (O4), 2,293 runs (O2), 1,852 scored bot runs (round 3), 544 cut games (O10). They
  may be different dates or different filters; none is labelled.
- **O10:** "Treecko 27 % vs Torchic 21 %, about 2.7 se" predates three more cycles; recompute before it is cited.
- **P2:** the evidence is bot-era (`story_mode.py` read 549 times); the build target is `ai_player/`. Re-measure on P3's first report.
- **O5:** the saving is stated honestly ("~1 call a day, 7k tokens") and is the smallest of the "A" items.
- **Missing legend:** R10, R13, L12 and KB1 are defined only in other files.

---

## 5. Items that no longer apply, or are done

| Item | State | Action |
|---|---|---|
| Order step 0 (`keep_raw_cycles` 20) | pushed 2026-10-19 1:03 PM; effective from the cycle after ai0035 | keep as DONE with the caveat; the O3 deadline is the real item |
| O3's "interim, no code" clause | done (same) | mark done inside O3 |
| `#28-trainer-improvements` item 3, the consult backlog cap | DONE 2026-10-18 (`c787dc0e`), verified in `consult.py:74-76` | C1 already says so; remaining parts (priority, expiry, de-duplication) belong to O5 |
| A3 | delivered by the templates | no separate build |
| A4's `CLAUDE.md` half | dropped (contradiction 3) | move to "Rejected or deferred" |
| E3 | informational only, autostart worked | label "no build" |
| C1 | now a one-line checklist; the cap and `max_calls_per_day` 2 already bound the cost | keep as a checklist line, not an item |
| O4's "confirm `E:`" | answered in the build specs | edit 16 |
| Backlog item "O13" | deferred; its probe moved to B6 | no change |

---

## 6. Proposed exact edits (old text -> new text), all in `2026-10-18-improvement-backlog.md` unless stated

Apply in this order; each old string is quoted from the file (line numbers in brackets).

**1. Intro [line 10]**
- OLD: `- **What gets built first:** priority A items, in the lean phase right after the weekly reset.`
- NEW: `- **What gets built first:** the steps in "The order" below, not the A label (A2 and A3 come later, and A-labelled R1, R2, R8, R9 wait for step 5.3). Every percentage comes from an audit script that is not in the repo until P3, so each is an estimate.`

**2. ID legend, a new line after the intro bullets [after line 10]**
- NEW: `- **IDs:** A-E are in this file. O, N, P, R come from round 2 (2026-10-19-backlog-round2/01..04; R10 and R13 are defined in 03-ai-player.md). L and DP come from round 3; S1-S2 are in the build specs. KB1 is the seasoned knowledge base, slice 1 (branch claude/kb1-seasoned-knowledge, merge pending).`

**3. Usage section [line 16]**
- OLD: `  - reading raw logs and evidence: 32-50 % of its cost;`
- NEW: `  - reading raw logs and evidence: 32-50 % of its cost (the 5.1 and 5.2 builders only; over all 980 transcripts it is 2.2 %, see Round 2);`

**4. A2 evidence and benefit [lines 35, 42]**
- OLD: `- **Evidence:** agents reading raw logs cost 32-50 % of a builder.`
- NEW: `- **Evidence:** the 5.1 and 5.2 builders spent 32-50 % reading raw logs, but over 980 transcripts evidence and log reads are 2.2 % and suite output 7.6 % (Round 2, angle 2). UNPROVEN until P3; build the agent-free run_regression.py half first.`
- OLD: `- **Benefit:** an estimated -20-35 % per step. **Risk:** low, because the raw logs stay on disk.`
- NEW: `- **Benefit:** UNMEASURED (an earlier estimate said -20-35 % per step); P3 decides. **Risk:** low, because the raw logs stay on disk.`

**5. A3 and A4 [lines 44, 51-58]**
- OLD: `**A3. SHORT-LIVED staged agents instead of one long builder.**`
- NEW: `**A3. SHORT-LIVED staged agents instead of one long builder.** (DELIVERED by the stage templates P11 + P1 + N6 + P10 in order step 2; no separate build.)`
- OLD: `` `CLAUDE.md` (about\n  500 lines) is injected into EVERY agent, so every turn of every agent pays for it. `` (two lines)
- NEW: `` The handoff is 390,563 bytes and is the cold-start cost (N3 + P9). ``
- OLD: `  - Move the bot-era rules of CLAUDE.md (outside the managed block) into a linked BOT-RULES.md. Every rule is KEPT` / `    and only MOVED, and the move is recorded in 06.` (two lines)
- NEW: `  - ~~Move the bot-era rules of CLAUDE.md~~ DROPPED (review 2026-10-19): it is 38.9 KB, under 2 % of a 600k context, and a rule moved out of the auto-loaded file stops firing. Revisit only if P3 shows otherwise.`

**6. A1 benefit [line 32]**
- OLD: `- **Benefit:** a check-in becomes one call. **Cost:** small. **Risk:** none (read-only).`
- NEW: `- **Benefit:** a check-in becomes one call. This is convenience, not tokens (the main chat is about 3 % of usage; P3 will say). It prints the AI frontier, so build D3's one line with it in step 1. **Cost:** small. **Risk:** none (read-only).`

**7. A6 identity [line 71]**
- OLD: `**A6. EXPERIENCE RECORDS from the bot's finished games** (#28-trainer-improvements item 7; USER RULING 41).`
- NEW: same, plus ` This IS item 7 and L10; C2 is only its lane policy.`

**8. C1 [lines 123-124]**
- OLD: `- config.json is re-read every cycle, so near the weekly limit a session sets consult.max_calls_per_day 0 and` / `  back after the reset.`
- NEW: `- config.json is read each cycle, but only after the learner fast-forwards its clone to origin/main, so near the weekly limit a session sets consult.max_calls_per_day 0 by commit + push (never by editing the clone), and back after the reset.`

**9. B6 [line 118]**
- OLD: `Part of this exists; make it universal and gated.`
- NEW: `Part of this exists (UNVERIFIED which part: name the file before building; round 2 found no run record holding a seed); make it universal and gated. One probe (O13: can x4_headless pin the seed despite KI-112?) also settles D2/DP5's seed and R4's card field.`

**10. D2 [line 142]**
- append: ` Build R12's knob registry first, or the weight files hold unregistered constants; DP5's personality and seed flags use the same schema.`

**11. E2 and E3 [lines 154-158]**
- OLD: `a power cut loses only the games in` / `progress (on 2026-10-17 it lost the whole of cycle ai0031).`
- NEW: `an unexpected shutdown (cause of 2026-10-17 unknown, O12) loses only the games in progress (it lost the whole of cycle ai0031).`
- OLD: `**E3. Power-cut recovery:** the BIOS "restore on AC power loss" and Windows auto-login are the user's choice.`
- NEW: `**E3. Unexpected-shutdown recovery (informational, no build):** the BIOS "restore on AC power loss" helps only if the cause was power (unknown, O12); Windows auto-login is the user's choice.`

**12. Order step 0 [lines 162-163]**
- append after `set the usual way learner settings change.`: ` In effect only from the cycle after ai0035: ai0023 was still pruned at 04:04 PM 2026-10-19 (the clone's data/learner.log line 333). The first deletion under 20 is ai0024, when ai0044 finishes, about 2026-10-24 (an estimate): O3 must ship before then.`

**13. Order step 1 [line 165]**
- OLD: `then **A1 with O1 + O6 + O7** and **P3**`
- NEW: `then **A1 (with D3's frontier line) with O1 + O6 + O7** and **P3** (O1 needs the user's OK for scheduled tasks)`

**14. Order step 4 and step 6 [lines 171, 173]**
- OLD: `**A2 with R3 + N8 + R4, A3, P7, P2,**` -> NEW: `**A2 (agent-free half first) with R3 + N8 + R4, P7, P2,**`
- OLD: `**D1-D3** and **R6, R1 + R2, R5, R8 + R9, R12**` -> NEW: `**D1, D2** and **R6, R5, R1 + R2, R8 + R9, R12**`

**15. A line after the order [after line 176]**
- NEW: `Unplaced above: C1 (a checklist line, now); C2 (with A6, step 3); B6 and its seed probe, N5, N7, N9, P4 + P6 (step 4, after B2); E1 (with the templates, step 2); E3 (informational); L4, L5, L12 (per chapter, see 03-long-horizon.md); DP3, DP6, DP7, DP8, DP9, DP10-DP13 (after the AI plays the whole game).`

**16. O3 [lines 207-210]**
- OLD: `(ai0001-ai0022 gone, ai0022 at 04:03 AM 2026-10-19)` -> NEW: `(ai0001-ai0023 gone; ai0023 at 04:04 PM 2026-10-19, after the push of the interim)`
- OLD: `interim, no code: keep_raw_cycles 12 to 20 (about 11 GB of 79 free).` -> NEW: `interim DONE, no code: keep_raw_cycles 20 from the next cycle (about 10 GB of 78 free); deadline for O3 is before ai0044 ends (about 2026-10-24, an estimate).`

**17. O4 [line 213]**
- OLD: `(confirm E: is one)` -> NEW: `(E: is a different physical disk with 47 GB free per the build specs; Z: is the alternative)`

**18. O1 evidence [line 216]**
- OLD: `disk fell 81 to 58 GB in a day from outside the learner` -> NEW: `disk fell 81 to 58 GB in a day from outside the learner (23 GB, probably B4's 24.3 GB of temp folders; UNVERIFIED)`

**19. O5 label [line 220]**
- OLD: `(A; sharpens C1)` -> NEW: `(B, small saving; bundled in the learner train with O3 and O6 + O7 for one restart; sharpens C1)`

**20. Rejected list [line 328]**
- OLD: `- **"Stop starting games that cannot finish": REJECTED**` -> NEW: `- **"Stop starting games that cannot finish": REJECTED** (strike it as an option in #28-trainer-improvements item 2)`

**21. Section heading [lines 23, 205]**
- OLD: `## A. Highest value per token (build first)` -> NEW: `## A. Highest value per token (the order below sets the sequence; A2 and A3 are not first)`
- OLD: `### A. Highest value per token` (Round 2) -> NEW: `### A. Highest value per token (the order sets when)`

**22. Round 3 line [line 335]**
- append: ` Do not build from 2026-10-19-backlog-round3/01-build-specs.md; it is the uncritiqued copy.`

**23. In a DIFFERENT file (not done here, read-only rule): top of `2026-10-19-backlog-round3/01-build-specs.md`**
- NEW first line: `SUPERSEDED 2026-10-19 by ../2026-10-19-BUILD-SPECS-steps-1-2.md (critiqued). Do not build from this copy.`

**24. `#28-trainer-improvements` in `03-PUNCH-LIST.md` (a different file)**
- item 1: reword "power cut" to "unexpected shutdown (cause unknown)"; item 2: strike "or do not start a game that cannot finish"; item 7: add "= backlog A6".

---

## 7. What this review did not do

It did not re-derive any usage figure (the audit script is absent), did not read the round 2 and round 3 notes beyond the L12,
R10 and R13 definitions, and did not re-check line citations such as `mode.py:104-105` (the backlog marks those CONFIRMED). The
ai0044 date assumes 12 hours a cycle with no overhead and an unchanged `keep_raw_cycles`. Tier 1 of the doc-consistency layer
(P1-P5) still applies when these edits are made: the punch-list entry and the handoff queue must change in the same commit.
