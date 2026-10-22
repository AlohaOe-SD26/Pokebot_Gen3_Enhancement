# RECON: S2-1b part 2, 03 slim-down. Angle: what a cold start needs from 03 versus history

All numbers come from scripts run on HEAD 39a6a5ee's `PROJECT KNOWLEDGE/03-PUNCH-LIST.md` (697,177 bytes, 4,400 lines).
The scripts were deleted afterwards. Tags: MEASURED (I ran it), READ (I read the source), INFERRED (I reasoned), UNKNOWN.

## 0. Lookup and baseline
- MEASURED: `decomp_lookup.py ask "punch-list slim archive S2-1b"` returns one ruling, 06:9643-9666 (part 1, "SNAPSHOT, THEN REWRITE"). It has no do-not line about 03.
- MEASURED: `wc -c -l` gives 4400 lines and 697177 bytes. Box counts by grep: `- [ ]` 230, `- [x]` 178, `- [~]` 37 (the brief did not count this third marker), plus 8 indented boxes.
- MEASURED, from `lint_docs.py`:
  - R3: `03-PUNCH-LIST.md 4400 4400 0 0`.
  - Size ratchet: `692,777 699,459 0 56 56`. These are chars against the ceiling, plus 56 long-line waivers.
  - I1: "178 completed `[x]` items are sitting in the punch list".
- READ: `tools/story-dev/doc_size_ceilings.json:22-26` puts 03 at ceiling 699459 and headroom 8192. The slim will need a ceiling ratchet-down. `long_line_waivers.json` holds many 03 entries, which go stale when the lines move.
- READ: `archive_sweep.py:85` reads `DEFAULT_ARCHIVES = {"03-PUNCH-LIST.md": "32-PUNCH-LIST-ARCHIVE.md", ...}`.

## Q1. The `## ` sections
Method, MEASURED: an item runs from its box line to the next box line or the next `#` heading. "Item bytes" means the bytes of those spans.

| lines | section | bytes | `[ ]` n / bytes | `[x]` n / bytes | `[~]` n / bytes | era (INFERRED from dates and slugs) |
|---|---|---|---|---|---|---|
| 1-14 | title + preamble | 1,209 | 0 | 0 | 0 | file rules (keep) |
| 15-80 | ‼ TRIAGE INDEX (2026-08-10) | 5,957 | 0 | 1 / 95 | 0 | HISTORY (story triage), except the "Marker states" legend at 57-80 (1,511 B), which a cold start needs |
| 81-2941 | Now (active focus) | 559,829 | 119 / 253,492 | 123 / 123,970 | 20 / 106,090 | Lines 82-88 are LIVE (#28, about 11 KB). Lines 89-2941 are PARKED story items plus done HISTORY. |
| 2942-3011 | Under discussion (2026-07-26) | 6,325 | 4 / 6,058 | 0 | 0 | PARKED story |
| 3012-3046 | Next (2026-07-19) | 2,379 | 3 / 1,994 | 0 | 0 | dormant GUI (#30-#32) |
| 3047-3069 | Adjustments (2026-07-19) | 1,361 | 0 | 6 / 1,054 | 1 / 263 | GUI HISTORY |
| 3070-3195 | User rulings + new round (2026-07-19) | 10,249 | 4 / 3,098 | 12 / 3,204 | 4 / 3,905 | early story, mixed |
| 3196-3229 | Living-Dex deepening | 2,313 | 4 / 977 | 4 / 1,249 | 0 | dormant dex |
| 3230-3245 | Now-ish | 1,059 | 3 / 1,002 | 0 | 0 | dormant GUI |
| 3246-3280 | First wave | 2,426 | 7 / 2,353 | 0 | 0 | dormant |
| 3281-3301 | Later / icebox | 1,558 | 9 / 1,097 | 1 / 382 | 0 | dormant |
| 3302-3315 | Promoted to custom 2026-07-19 | 951 | 0 | 0 | 8 / 873 | dormant, awaiting a user in-game check since 07-19 |
| 3316-3746 | Story bot (#24) open backlog | 36,810 | 26 / 23,919 | 1 / 232 | 4 / 12,193 | PARKED story |
| 3747-4401 | Done — MIXED | 64,752 | 51 / 36,035 | 30 / 22,504 | 0 | PARKED story, mostly OPEN (see Q4) |

MEASURED: most work items are NOT boxes. They are `### ` headings whose body holds child `- [ ]` bullets. Many of the 230 `- [ ]` lines are sub-steps without a slug: for example 03:1407-1431 has four under `#24-ki47rotatelead`, and 03:4033-4101 has about ten. Counting boxes therefore overstates the item count.

I re-segmented the file into logical items. An item starts at a box line that leads with a slug, or at a `### ` heading. Status comes from the box, or from the heading's emoji (✅ done, 🔶 mixed, anything else open). The result, MEASURED + INFERRED, is in the table below. Its era column uses these definitions:
- LIVE = the #28 items plus `#27-hookhatch`.
- DOCS = doc and gate tooling items.
- DORMANT = numeric GUI and dex ids.
- STORY = everything else.

| era | open | partial | mixed / done-with-open-kids | done |
|---|---|---|---|---|
| LIVE ai/ops | 4 (7,681 B) | 1 (2,981 B) | 0 | 2 (1,364 B) |
| DOCS process | 16 (26,152 B, 308 L) | 3 (6,969 B, 73 L) | 0 | 3 (1,012 B) |
| STORY (parked) | 141 (339,333 B, 2,266 L) | 22 (106,228 B, 539 L) | 8 + 2 (51,442 B, 410 L) | 118 (128,667 B, 456 L) |
| DORMANT gui/dex | 27 (7,972 B) | 8 (873 B) | 0 | 11 (2,468 B) |
| no-slug headings (triage, batch reviews, group headings) | 22 headings, 9,834 B | | | |

## Q2. LIVE `- [ ]` and `- [~]` items (READ, sizes MEASURED)
- `#28-aiagent-v2` `[~]` 03:83, 2,981 B in one line. A STATUS line: the AI player steps 0-5.2 are DONE, and NEXT is the O3, O5, O6 and O7 deploys plus the KB1 merge. It is dense, and dated deploy timestamps are accreting in it.
- `#28-trainer-autonomy` `[ ]` 03:84, 819 B in one line. A SPEC and status line ("USER RULING 39 ... NOT STARTED").
- `#28-trainer-improvements` `[ ]` 03:85, 4,308 B in one line. It is mostly a STATUS log (O3, O4, O6, O7, O1 and O5 built or deployed, with times), plus "(1)-(9) ... NOT STARTED except (3) and (7)". Part status, part history.
- `#28-seasoned-player` `[ ]` 03:87-88, 1,657 B in two lines. STATUS: KB1 merged, KB2 slice 1 built, slice 2 spec ready, census done.
- `#27-hookhatch` `[ ]` 03:96, 897 B. Ops (the git hooks). It is a short open spec with "PARTLY A USER DECISION".
- Done, and HISTORY: `#28-aiagent` `[x]` 03:82 (797 B) and `#28-evidence-identity` `[x]` 03:86 (567 B). 04 cites the latter.
- DOCS-process items: 19 open or partial, all filed 2026-07-27..09-08 in the story era, with their tools in `tools/story-dev/` (INFERRED). Each has a mostly long body. The items, with size and line count:
  - `#24-linebudgetchars` 2,101 B / 24 L
  - `#24-retiredclaimgate` 2,130 / 25
  - `#24-gatescopeharness` 1,102 / 14
  - `#24-advisorydocstring` 1,545 / 18
  - `#24-sanitycheck2` 981 / 11
  - `#24-reprosweepratchet` 1,893 / 23
  - `#24-codeorphans` 2,222 / 24
  - `#24-gateselftests` 1,124 / 11
  - `#24-flagnamedocscan` 1,914 / 21
  - `#24-prechecksentence` 2,265 / 33
  - `#24-barecitationblindspot` 1,065 / 15
  - `#24-retractioncoverage` [~] 4,452 / 43
  - `#doc-audit-2` [~] 1,037 / 12
  - `#doc-audit-3` 250 / 3
  - `#doc-audit-4` [~] 1,480 / 18
  - `#doc-policy-05` 379 / 5
  - `#24-stalestatusclaims` 4,735 / 53
  - `#24-punchlist-archive` 301 / 4 (this task: 03:3874 reads "03 is AT its 3600-line budget; the next item needs an archive pass first")
  - `#24-tier2audit-residue` 2,145 / 24

  04 cites only `#24-sanitycheck2` and `#24-reprosweepratchet` among these (MEASURED, grep of 04).
- No `- [ ]` item about workflows exists. MEASURED: no slug in 03 matches `workflow`, and the backlog lives in 04 and the specs.

## Q3. The story-bot open items, and stubs
MEASURED:
- Raw boxes owned by story items: `[ ]` 175, `[~]` 25, `[x]` 157.
- Logical open items (open, partial, mixed or done-with-open-kids): 173, totalling 497,003 B and about 3,215 lines.
- Generated one-line stubs: 173 stubs, 26,523 B, average 153 B. The format is ``- [ ] `#slug` — <title ≤70 chars> — PARKED (OPEN); full text: `32-PUNCH-LIST-ARCHIVE.md` ``.
  - Example: ``- [ ] `#27-determinism` — FOUND 2026-09-29 (design v2 step 5's controls; KI-112), NOT STARTED: 1 — PARKED (OPEN); full text: ...``
  - 168 of the 173 slugs are unique. About 3 of the stubs are group headings that only name a slug (03:89, 94, 112), not items.
- Dormant GUI and dex open or partial items: 35 stubs, 4,789 B.
- Findability, INFERRED: one stub per slug keeps every open slug greppable, with these caveats:
  - (a) Titles cut from headers are often dates ("FOUND 2026-09-30 ...") and need hand titles.
  - (b) About 60 open sub-step boxes have no slug of their own (03:1407-1431, 4033-4101, 2195-2204 and others). Under a stub they are findable only via the parent slug in the archive.
  - (c) MEASURED: 04 cites 10 slugs that are DONE in 03: `#24-abortrecoveryresiduals`, `#24-dexcatch-battlebail`, `#24-drakeL75`, `#24-glaciaL75`, `#24-phoebeL75`, `#24-rarepredicate`, `#24-sidneyL75`, `#24-tailprobe`, `#27-batch0927` and `#28-evidence-identity`. With "nothing for done items" they resolve only in the archive.
  - (d) MEASURED: 04 cites `#24-organicteam`, which is in 03 only as a triage-table row (03:33), and `#27-tatelizab`, which is nowhere in 03.

## Q4. Box versus status words (READ; line text re-read)
- The heading at 03:3747-3752 claims "THREE STILL-OPEN `[ ]` ITEMS ARE FILED UNDER THIS HEADING". MEASURED: at least 25 open or mixed slugs sit under it:
  - partyindex-minus-one, errorpath-frequency, stalestatusclaims
  - ballrestock-ordering, punchlist-archive, tateliza-attrition
  - counterprobe-rotted, countermsg-repro, harness-faultgap
  - mossdeep-strandfixture, rotatelead-precondition
  - truckleak 🔶, truckleak-accept, pcpingpong 🔶, pcpingpong-accept
  - counterpids-never-retired, ch23preflight-gap, whiteoutloop 🔶
  - regimeb-noescalation, bosstrainingeconomics, ch23training, marillskew
  - cutscenestall, tier2audit-residue, lowlevelmules

  They total about 47 KB. The heading undercounts by a factor of 8.
- `- [ ]` items whose title leads with done words. Each one has a "WHAT REMAINS" acceptance clause, so the box is defensible but the headline is ✅:
  - 03:113 `#27-evgpcwedge`: "✅ FIXED AND A/B-PROVEN 2026-09-27", with "REMAINS: the next batch should show 0 `could not face` derails"
  - 03:139 `#26-hmwrongitem`: "✅ FIXED, A/B-PROVEN ... ✅ MERGED"
  - 03:140 `#26-gymtmteach`: "✅ BUILT, DRIVEN AND REVIEWED ... ✅ MERGED"
  - 03:473 `#24-amuletcoin`: "✅ BUILT 2026-09-26 (✅ MERGED ..."
  - 03:145 `#26-healmap-lavaridge`: "✅ RECON DONE; ... FIXED 2026-09-27"
  - 03:152 `#24-restockleg`: "✅ F1 BUILT AND DRIVEN"
- Dormant `- [ ]` items with "BUILT IN SANDBOX 2026-07-19" and never closed: 03:3247 `#22`, 03:3254 `#9`, 03:3262 `#23` and 03:3270 `#11`. The triage note at 03:41-47 already flags this.
- `- [x]` with open words: 03:1941 `#24-teachmsgstall` reads "✅ FIX SHIPPED 2026-08-11 AND KEPT; ⚠ REOPENED THE SAME DAY". 03:1950-1951 says "The live status is the table row for `#24-teachmsgstall` near the top of this file". That table was RETIRED (03:23, "the old front-of-file index table is in `28-HANDOFF-ARCHIVE.md`"). INFERRED: it is a dangling pointer, and the item's live status is not in 03.
- A `### ✅` heading over open child boxes: 03:2180 `#26-healnavbare`, "✅ ... FIXED 2026-09-11", with three `- [ ]` at 2195, 2197 and 2199 (for example "A/B the helper on an ORDINARY heal ... BEFORE").
- Cleared as false positives: 03:144 `#24-norman-lead` (its "OPEN" refers to `#24-leadpolicy`) and 03:146 `#24-pass2triage`.

## Q5. Slim-03 estimate (INFERRED arithmetic over MEASURED parts)
| part | bytes | lines |
|---|---|---|
| preamble 1-14 + marker legend 57-80 | 2,720 | 38 |
| LIVE open/partial in full (#28 ×4 + #27-hookhatch) | 10,662 | 6 |
| DOCS process as stubs (or in full: 33,121 B / 381 L) | 2,963 | 19 |
| STORY open stubs | 26,523 | 173 |
| DORMANT GUI/dex stubs | 4,789 | 35 |
| about 8 section headings + archive pointer | ~800 | ~10 |
| **TOTAL (docs as stubs)** | **≈48.5 KB** | **≈281** |
| TOTAL (docs in full) | ≈78.6 KB | ≈643 |

Optional: a one-line index of the 10 done slugs that 04 cites adds about 1.2 KB. Against today's 697,177 B and 4,400 lines, the slim is about 7-11% of the size.

## Gate dependencies on 03's content (READ)
- `probe_closed_item_refs.py:144` and `:154` build their fault victim with `victim = sorted(closed)[0] if closed else "#24-phantom"`.
  - The inject arm still fires, because `closed.add(victim)` runs at :145.
  - The "history" arm's second half (:161-163, which appends to the victim's own body) is a no-op when 03 holds no closed `###` item. That is the 08 lesson's shape. INFERRED, not run.
- `probe_item_header_body.py` uses synthetic fixtures (:118, :121), so it is unaffected.
