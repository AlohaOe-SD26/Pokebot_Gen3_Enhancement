# S2-1b part 2 recon, ADVERSARIAL angle: what goes wrong with "snapshot 03 to 32, then rewrite (live in full, parked open as stubs, done only in the archive)"

Date 2026-10-22. HEAD 39a6a5ee. Read-only. Tags: MEASURED (ran it), READ (read the source), INFERRED (reasoned), UNKNOWN.

## 0. Corrections to the task's premises
- MEASURED: 03 has THREE box states, not two: `grep -c '^- \[ \]'` = 230, `'^- \[x\]'` = 178, `'^- \[~\]'` = **37**, plus 8 indented boxes. 03:57-63 defines `[~]` as "partial", and 03:76-78 says *"Do not treat `[~]` as either finished or unstarted without reading the entry."* A two-way "open vs done" rule has no place for 37 items.
- MEASURED: 03 is CRLF in the worktree and LF in git (`git ls-files --eol`: `i/lf w/crlf`, `core.autocrlf=true`). It has 697,177 B and 4,400 CRLF. Every byte-for-byte claim must name which form it uses.
- MEASURED: by bytes (LF form, 692,778 B), the parts are: open-box items 47.7%, `[~]` items 16.9%, `[x]` items **22.0%**, headings 9.8%, other prose 3.5%. Moving ONLY the done items cannot get near a part-1-sized cut. The bulk is OPEN content, and stubbing it is what makes the file smaller.
- READ: lint_docs.py:95-101 records that 03's line budget was raised 3600->4200 and then 4400 ON A MEASUREMENT. 03 was "78.5% OPEN sections" and "only 6.8% closed-or-archived", and on 2026-09-16 "4.1% closed". The project's own finding is that 03 is a BACKLOG, not a forming archive.

## (1) Rulings in 06 that constrain 03, its sections, statuses or archiving
- `decomp_lookup.py ask "punch list"`: MEASURED, 5 rulings returned, none specific to slimming 03 (frames budget, organicteam, P5, installer, route facts).
- READ 06:3062-3066 (2026-08-22, PASS 5): *"RULING — reclaim budget by ARCHIVING VERBATIM, never by trimming live content ... each script-verified to contain ZERO open markers before the move and each leaving a stub carrying the rule later work leans on. ⛔ Rejected: deleting closed detail (it is the evidence trail) and raising the R3 limit."* The open-markers half bears directly on "parked OPEN items as stubs": that ruling archived only blocks with zero open markers. Part 1 reconciled it at 06:9650: *"every byte is in 28, and an adversarial completeness verify hunted the rewrite for any LIVE item it dropped."* INFERRED: a stub of an OPEN item is a stronger move than part 1 made, because part 1 kept every live item in full.
- READ 06:3068-3072 (2026-08-22): *"the three OPEN items filed under `## Done` were FLAGGED, not moved ... ⚠ The move is the better end state ... but a doc edit that could lose content is not worth doing at the end of a long session."* So moving them is endorsed, and is still owed (03:3748-3752).
- READ 06:3090-3101 (2026-08-23, P5): *"the work item's own status in `03-PUNCH-LIST.md` ↔ what the handoff claims about it ... A checklist protects exactly what it enumerates."* It is not a gate (*"Rejected: making it a GATE"*).
- READ 06:2189-2201 (2026-08-14): *"`#24-organicteam` is NOT deferred ... **A deferral and its reversal must never both read as live.**"*
- READ 06:3562-3584 (2026-08-28): no "part N of M"; *"The split is by KIND, not SIZE"*; history goes to the append-only partner file.
- READ 06:9651 + 9664 (2026-10-22, part 1): *"no new numbered file; history goes to 28, its established home"*, and **Rejected: "A new numbered snapshot file: it would make the asymmetric 04/28 pair a trio."**
  - CONFLICT TO FLAG: `archive_sweep.py:85` defaults 03 -> `32-PUNCH-LIST-ARCHIVE.md` ("32 is the next free number (R4); 28 already holds old 04 blocks"). That default comes from spec text (`2026-10-19-BUILD-SPECS-steps-1-2.md:279`), not from any 06 ruling: `grep -n 32-PUNCH 06-DECISIONS-LOG.md` returns 0 hits (MEASURED).
  - Meanwhile every earlier 03 retirement went to 28 (37 `###` stubs in 03 say "ARCHIVED", e.g. 03:974, 03:1168-1177, 03:3769), and 06 2026-08-22 used 28 too.
  - So putting the snapshot in 32 splits 03's history across two files: old blocks in 28, the snapshot in 32. The snapshot's own stubs would also point to 28. This is a design decision for the coordinator; this recon does not settle it.
- READ 06:5392-5395 (2026-09-16): *"If you are tempted to raise it again, run R7 first: if the closed fraction has grown ... trimming is the right answer."*
- READ 06:537-549 (2026-07-26, user directive): hard-won route facts live in decision code. *"The punch-list paragraph now points at the table as the authority."* A fact that only 03 prose holds is the failure that ruling describes.
- READ 06:887 (2026-07-29): *"`#doc-policy-05` → OPTION A"*. RULED, yet 03:2839 still reads `- [ ] #doc-policy-05 — **user ruling wanted**`, and 03:32 lists it as BLOCKED ON A USER DECISION. This is a stale open box.
- No 06 ruling names the user-set sections (MEASURED: grep for icebox, user-set, re-orders, culls and "Under discussion" returned no 03-related hits).

## (2) 08 prevention rules about punch-list edits going wrong
- READ 08:9634-9637 (2026-08-26): *"MULTI-SLICE EDITS GO BOTTOM-UP, AND EACH SLICE RE-ASSERTS ITS BOUNDARY BEFORE WRITING ... hunk count ≠ intended block count is a one-glance corruption tell."*
- READ 08:10326-10330 (2026-09-01): *"ANY SCRIPT THAT DELETES A RANGE MUST BOUND THE RANGE AND REFUSE WHEN THE BOUND IS HIT ... verify the INVARIANT after the write, not the operation's own report."*
- READ 08:11470-11477 (2026-09-03): *"NEVER RETIRE AN ITEM ON A STRUCTURAL TEST ALONE. READ IT. 'No open checkbox' is a proxy; open work also hides in prose, in `D<n>` sub-items, and in 'AWAITING A USER RULING'."* Before archiving, grep the slug in 04 and 05.
- READ 08:12558-12562 (2026-09-05): *"assert after writing that every non-blank removed line is present in the archive ... A falsifiable claim in a document is worth exactly as much as the check behind it."*
- READ 08:14543 (2026-09-07): *"A STATUS WORD IS NOT A STATUS. Never decide 'is this closed?' by substring."*
- READ 08:14666-14669: *"READ THE TOOL'S NUMBER, NOT ITS VERDICT ... a zero there means the operation did not occur."*
- READ 08:14792-14799: *"A FAILING GATE STATES A PREMISE. TEST IT BEFORE OBEYING IT ... an automated 'is this closed?' predicate cannot tell a work item from a reference section."* That session archived the file's own marker legend by mistake.
- READ 08:16026-16027 (2026-09-10): *"'Closed' describes the work, not every sentence in the block — before archiving an item, grep its body's nouns tree-wide and hoist anything it solely owns."* The case: a `[x]` item was the ONLY tracker of Dragon Claw TM02.
- READ 08:16858-16862 (2026-09-12, a two-anchor slice deleted 58 items): *"NEVER slice between two independently-located anchors ... EVERY bulk doc edit must PRINT its line delta and ASSERT a bound on it."* Also: *"lint_docs ... would have been HAPPIER with the file 1995 lines shorter."*
- READ 08:17826-17834: *"for any irreversible selection, print the FULL candidate list and READ IT ... a tool's invariants protect what the TOOL does, never what YOU SAY it did."*
- READ 08:8586-8674 (P5): the third copy of a status fact is the one that goes stale.
- READ 08:24031-24033 (2026-10-22, part 1's lesson): *"a FAULT arm plants its fault in a synthetic input it owns. A fault arm that reads a real repo document is a bug, even while it passes."*
- READ 08:23988-23989 (2026-10-21): *"a spec that sets a size or count target ... first measures, on the real file, how much of it the tool's selection can reach."* That applies here: done items are only 22% of the bytes.

## (3) Live content inside DONE items and history sections
- MEASURED (`scan.py`): **97 of 179 `[x]` items carry live-looking words** (⛔ / DO NOT / REMAIN / OPEN / pending / UNPROVEN ...). Most are DO-NOT-REDO stubs, and those are live too: each one is a do-not. Concrete live content:
  - 03:880 (inside `[x] #24-drakeL75`): *"2 REVIVES REMAIN, and the bot does not use them in battle ... `allow_revive=False` (`battle_items.py:165`) pending a PID-grounded index probe"*. This is a live KI-100 caveat. The open item 03:1233 also says *"The REVIVE half stays OFF pending KI-100"*, so this one is not sole-owned (READ).
  - 03:146 (`[x] #24-pass2triage`): *"It SPAWNED `#26-victoryroadgap` and sharpened `#24-e4postbattlestall`; those are separate OPEN items"*. The same bullet also carries the do-not *"EVERYTHING FROM 'REMAINING ...' ONWARD IS SUPERSEDED HISTORY ... do NOT action it."*
  - 03:967 (`[x] #26-victoryroadgap`): *"⇒ what remains is `#24-ch23training`; close this once it ships."*
  - 03:3061 (`[x] #40`, a USER-REQUESTED section): *"(Live catch in a real battle still pending.)"*
  - 03:955 (`[x] #24-fixturelineage`): heading do-not *"⛔ DO NOT GRIND `post_grind_L60.ss1`, AND DO NOT 'REPAIR'"*.
  - 03:3131 (`[x] ~~#24-team~~`): *"SUPERSEDED by `#24-organicteam`, which is ✅ APPROVED — GATE LIFTED (user 2026-08-06, re-confirmed 2026-08-14). ⛔ Read `#24-organicteam`, not this."* MEASURED: the OPEN, user-approved `#24-organicteam` item itself already sits in 28 (28:7663 `- [ ] #24-organicteam — ✅ THE GATE IS LIFTED. APPROVED TO BUILD`, inside an archived "SESSION END 2026-08-05" block, 28:7649). In 03 it is named only at 03:33 (the triage table) and 03:3131 (a `[x]`). **If done items leave 03 and the triage index is rewritten, the user-approved open item leaves 03 entirely.** That is the 2026-08-14 failure.
  - 03:3758 `[x] #24-ch20rename` still reads *"NEW ... do it at the START of a session"* with a Do/Do NOT list. 07:12793 says DONE. Its do-not (*"Do NOT rewrite git history or the append-only logs"*) is live (READ).
- MEASURED: `## Done` (03:3747-4401) holds **51 open boxes, 0 partial and 30 done**, across 29 `###` items. At least 20 are open: `#24-partyindex-minus-one` 3777, `#24-errorpath-frequency` 3791, `#24-stalestatusclaims` 3807, `#24-ballrestock-ordering` 3863, `#24-punchlist-archive` 3874, `#24-tateliza-attrition` 3878, `#24-counterprobe-rotted` 3904, `#24-countermsg-repro` 3912, `#24-harness-faultgap` 3923, `#24-mossdeep-strandfixture` 3933, `#24-rotatelead-precondition` 3942, `#24-truckleak` 3957, `#24-pcpingpong` 3975, `#24-counterpids-never-retired` 3991, `#24-ch23preflight-gap` 4005, `#24-whiteoutloop` 4014, `#24-regimeb-noescalation` 4039, `#24-bosstrainingeconomics` 4079, `#24-ch23training` 4102, `#24-marillskew` 4211, `#24-cutscenestall` 4224, `#24-tier2audit-residue` 4229 and `#24-lowlevelmules` 4253. **A rule keyed on the SECTION ("history sections go") would carry about 50 open boxes away.**
- READ: open boxes are no more reliable than done ones. `#doc-policy-05` is open at 03:2839 but RULED (06:887). The triage table row 03:31 says KI-52 *"Needs a scope decision"*, while 05:1167 reads *"KI-52 — ✅ FIXED 2026-08-11"*. A rewrite that copies the open boxes as "live" carries stale commands forward.
- READ: open work held in prose rather than boxes. Examples: the triage index §2 table (03:25-33: the boss-healing response, KI-52, `#doc-policy-05`, `#24-organicteam`) and `D<n>` sub-items (the `#26-manualderails` D4 user decision, per 08:11452).

## (4) The USER-SET sections: which are the user's own lists
Evidence of user ownership is in the headings and bodies (READ). No 06 ruling covers them (MEASURED, see (1)).
- 03:2942 `## Under discussion (user 2026-07-26, NOT agreed scope — see 19-TEAM-BUILDING-DISCUSSION.md)`.
  - Body 03:2943: *"‼ Do NOT start these. Each has open questions that must be answered with the user first."*
  - 4 open items carry the user's recorded answers ("ANSWERED 2026-07-26"): `#24-gymtrainers`, `#24-partyvariety`, `#24-personality`, `#24-favourite`.
  - ⚠ Its do-not is stale for `#24-gymtrainers`, which says *"UNBLOCKED 2026-08-13"* (03:2955). A rewrite must neither drop the user's answers nor silently "fix" the heading.
- 03:3012 `## Next (user-set order 2026-07-19: #30 → #31 → #32, THEN the first wave below)`. **This is an explicit user ORDER.** Body 03:3013-3016: *"BUILT + ADVERSARIALLY VERIFIED in sandbox ... AWAITING USER OK to promote to custom. In-game confirms still pending."* It holds 3 open items.
- 03:3047 `## Adjustments (user-requested 2026-07-19)`: 6 `[x]` and 1 `[~]` (`#36b`, *"could go scrollable for a true 5× if the user wants"*). `#40` (`[x]`) still holds a pending live check.
- 03:3070 `## User rulings + new round (2026-07-19)` opens with `[x] RULINGS: Latias+Latios BOTH obtainable (218/386); Surskit unobtainable`, a user ruling written as a done box. It is also in `11-LIVINGDEX-DESIGN.md:746` (READ). The section holds 4 open, 4 partial and 12 done items, including user-gated conditions:
  - `#24-autosave`: *"APPLY ONLY AFTER the user green-lights the current story build"*;
  - `#24-ui`: *"WORK ON THIS ONLY AFTER the bot is finished and tested 100% (user directive)"*.
- 03:3196 `## Living-Dex deepening (user-requested 2026-07-19; DESIGN-FIRST, no cutting corners)`: 4 open, 4 done; `#41-research` has a REMAINING clause.
- 03:3230 `## Now-ish (user-added 2026-07-19, ahead of first wave)`: 3 open, in order #33, #34, #35.
- 03:3246 `## First wave (after #30-#32 + #33-#35 — agreed direction 2026-07-19)`: "agreed", so user-agreed; 7 open.
- 03:3281 `## Later / icebox (catalog in 09-FEATURE-BRAINSTORM.md; user re-orders/culls)`: **the heading reserves reordering and culling for the user.** 9 open, 1 done.
- 03:3302 `## Promoted to custom 2026-07-19 (built; awaiting user in-game confirmation)`: 8 `[~]` items, each waiting on a USER test.
- INFERRED: 3012, 3230, 3246 and 3281 encode an ORDER or a cull right that belongs to the user. 2942 and 3302 encode user-gated status. 3047, 3070 and 3196 are user-requested lists that mix done and open boxes. These sections total about 30 KB (MEASURED by section: 6,325 + 2,379 + 1,361 + 10,249 + 2,313 + 1,059 + 2,426 + 1,558 + 951 B), so keeping them verbatim costs little.

## (5) What a lossless move must prove, and whether part 1's checks carry over
- READ part-1 spec P-1 (BUILD-SPEC-S2-1b:164-169): (a) `28_after` starts with `28_before`; (b) the appended bytes equal the old file, working-tree bytes; (c) the same against `git show HEAD:` with line endings normalized; FAULT: one flipped byte is detected.
- INFERRED: against a NEW 32, check (a) is **vacuous**, because every file starts with the empty prefix. The prefix check must become "32 did not exist at HEAD" (`git cat-file -e HEAD:"PROJECT KNOWLEDGE/32-PUNCH-LIST-ARCHIVE.md"` fails) plus "the file holds exactly heading lines + old 03, with nothing after". If the snapshot goes to 28 instead, (a) carries over unchanged.
- MEASURED: CRLF in the worktree and LF in the index means (b) and (c) are different claims. A new file written by Python with `\n` stays LF in the worktree until the next checkout, so (b) "worktree bytes equal" fails or passes by accident depending on how the file is written. State the line-ending form explicitly.
- READ 08:24031: the flipped-byte fault arm must flip a byte in a SYNTHETIC copy the script owns, never rely on a quirk of the real 03.
- What part 1 did NOT need and part 2 does (INFERRED, from (3)): byte-losslessness of the snapshot says nothing about whether live items left 03. The missing proofs:
  - (i) a SLUG census: every `#NN-slug` and `KI-n` in old 03 still found in new 03, or explicitly listed as archive-only (MEASURED: about 409 distinct slugs, by a rough regex);
  - (ii) an open-box census: every old `- [ ]` and `- [~]` slug present in the new 03, or listed with the reason it left;
  - (iii) the sole-owner hoist from 08:16027: grep the nouns of each moved `[x]` body tree-wide;
  - (iv) the user-section headings and their item ORDER, unchanged.
- READ: lint gates after the rewrite.
  - R8(c), lint_docs.py:31-36: *"a waiver whose line is gone is STALE (a failure)"*. 03 has **56** long-line waivers (`grep -c 03-PUNCH long_line_waivers.json` = 56), so the rewrite must drop or re-hash them in the same commit.
  - The R8 ceiling (699,459, `doc_size_ceilings.json:22-26`) should be ratcheted down, or bytes can quietly return.
  - R1 bans a `# HISTORY` block in 03.
  - R5 only checks that listed files exist; no gate requires a new 32 to be listed in 00-README (INFERRED from the rule list, lint_docs.py:22-36). P4 is prose-only.
- READ 03:7-13: `audit_doc_consistency.py` *"matches the literal [drift] figure and cannot tell a quotation from a claim"*. A rewrite that restates any drift number turns it red.

## (6) What reads 03 at session start or in a hook, and could mislead a cold start
- READ `.claude/hooks/session-sync.ps1:79-83,97`: the SessionStart hook injects the **first 5 lines matching `^\s*-\s*\[ \]`** of 03, verbatim and whole, as "Open punch-list:".
  - MEASURED today: lines 84, 85, 87, 90, 91 (`#28-trainer-autonomy`, `#28-trainer-improvements` at 4,309 chars, `#28-seasoned-player`, `#27-dmgcalcfix`, `#27-obtaindata`).
  - INFERRED: the rewrite's ORDER decides what every cold start is told is open. A parked story stub or a user-set GUI item placed first becomes "the open punch list". Indented `- [ ]` lines count too.
- READ `.claude/commands/wrapup.md:8`: *"mark the item done in `03-PUNCH-LIST.md` (with date, moved to Done)"*. READ 03:3-4: *"check items off with `[x]` and move them to Done with the completion date"*. If the new rule is "done items live only in the archive", both instructions re-grow a Done section in 03 at the next wrap-up, and both must change.
- READ: enforcing gates that scan 03 and could go silently vacuous on a near-empty file (08:24031 shape).
  - `probe_closed_item_refs.py:52-55` builds its CLOSED set from 03 only. MEASURED today: `items: 112 closed items: 34 ... PASS`. INFERRED: with done items moved out, the closed set is about 0, and the gate can no longer catch an open item describing an archived (closed) slug as open. That is exactly P5's failure.
  - The same applies to `probe_item_header_body.py:47` (TARGETS = 03), `probe_punchlist_step_status.py:36` (needs `- [x] **N.` checklists, e.g. `#24-e4healing`), `probe_retraction_coverage.py:68`, `probe_stale_citations.py:47` and `audit_doc_citations.py:43`.
  - Their self-tests are synthetic (`probe_item_header_body.py:108-136`; READ), so they will stay green on an empty subject.
- MEASURED: line-number citations into 03 will all point at the wrong text after the rewrite. Code: `03-PUNCH-LIST.md:810` ×6 (provenance in `probe_bracket_viability.py:66`, `probe_party_l65_audit.py:17`), `:47` ×6, `:391`, `:2105`, `:1757` ×2 each. Docs: 74 citations across 05, 07, 08, 28 and research notes. INFERRED: the one in current-state 05 (05:2571, `03-PUNCH-LIST.md:47`) will mislead; the append-only ones are dated history.
- READ 00-README:11 row 5 *"`03-PUNCH-LIST.md` | The work queue"*. CLAUDE.md §1 says to skim 03 before proposing work. Neither mentions an archive for 03, so the README needs a 32 row (or a 28 note) in the same commit (P4).
- READ 03:3874-3876: the open item `#24-punchlist-archive` (*"Move CLOSED items VERBATIM to an append-only archive; never splice"*) and `#28-trainer-improvements` (03:85: *"03 is S2-1b part 2, OPEN, next in the queue"*) are the P5 halves this item must close. So is 04:48/57, item 1.
- Not checked: the full `#28-trainer-improvements` body, and whether `Ch21DiveMode` at `story_harness.py:9681` contradicts `#24-ch20rename`'s DONE (07:12793 says it was renamed to `Ch20DiveMode`; the class still exists, so this may be a later Ch21 dive mode). UNKNOWN; out of scope.
