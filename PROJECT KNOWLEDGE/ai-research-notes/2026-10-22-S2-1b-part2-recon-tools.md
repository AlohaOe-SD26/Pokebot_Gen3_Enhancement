# S2-1b part 2 recon: tools, gates and hooks that READ 03 or cite into it (2026-10-22)

## Access limits (read this first)
- The permission classifier REFUSED four of my Bash calls (reason given: "Irreversible Local Destruction").
  They were: an archive_sweep.py DRY RUN on 03; a `sed` read of audit_doc_consistency.py:80-100/289-300/831-975;
  a grep of 03's open boxes / `^#|^##` map; and a tree-wide `03-PUNCH-LIST.md:N` grep from `.`. I did NOT work
  around them. As a result I never read 03 itself (the READ-LIST's 03:1-80 included), and the per-check detail
  of audit_doc_consistency on 03 is UNKNOWN. The coordinator should run those itself.

## (1) Readers of 03

| reader | what it extracts/asserts | run_gates | if content leaves 03 |
|---|---|---|---|
| lint_docs.py | R3 `LINE_BUDGET ... "03-": 4400` (:126); R7 `CLOSED_FRACTION_BUDGET = {"03-": 0.25, ...}` (:144), the `###` sections via `r7_section_is_closed` (:183-193); R8 bytes plus long lines (:238 `p.name in R8_FIXED or p.name[:3] in CURRENT_STATE`); INFO I1/I2 count `^- \[x\]` and `^- \[~\]` (:1069-1076, never fails) | `("lint_docs.py", False)` :116 | R8 **FAILS** with "STALE waiver" for each of 03's **56** waived long lines that the rewrite removes (:560-565). Fix: `--rewaive 03-PUNCH-LIST.md` (drops them, a shrink), then `--ratchet` (ceiling 699,459 -> size+8,192). Part 1 did exactly this (spec 2026-10-22 :157-158). |
| audit_doc_consistency.py | 03 is in its file set (:87 `"03-PUNCH-LIST.md", "04-HANDOFF.md", "05-KNOWN-ISSUES.md",`); :524 is a drift-copy comment; the `check_queue_vs_headline` def is at :831 | :120 | UNKNOWN (read refused). Run today: "all consistency checks PASS across 7 current-state files". |
| probe_closed_item_refs.py | `###` items with a `` `#NN-slug` `` in their header; a CLOSED item (✅/CLOSED/DONE 20, not 🔜⬜🔶) must not be called OPEN by another item (:54-55, :91-106, :136-140) | :435 | **Silent pass with a smaller scope**: archived closed slugs leave `closed`, so a live item that calls one OPEN is no longer caught. Its fault arm survives: `victim = sorted(closed)[0] if closed else "#24-phantom"` plus `closed.add(victim)` (:144-145). A missing 03 makes `read_text` raise, so a crash, so FAIL. |
| probe_item_header_body.py | `### ✅` headers over open-work body text (:47, :51, :71-80) | :460 | If no closed headers remain: silent PASS. The self-test is synthetic (:118-134), so it is not vacuous. A missing file crashes, so FAIL. |
| probe_punchlist_step_status.py | Items that contain `- [x] **N.`; another line in the same item must not say step N "remains" (:36-40, :79-111) | :833 | PASS when 0 items are checked (it prints the count but does not fail on 0, :116-118). A missing file gives a loud FAIL (:73-75). |
| probe_drift_restatement.py | `K.glob("0[1-5]-*.md")` (:169) | :604 | Arms are synthetic (:124-150). Unaffected. |
| audit_doc_citations.py | `ident` + `file.py:LINE` in CURRENT_STATE, which includes 03 (:42-44, :202-203) | :376 | Drifted citations that move to 32 leave scope (no fail). |
| probe_retraction_coverage.py | SCAN includes 03 (:68) | :879 | It is ADVISORY (:91-100). |
| archive_sweep.py | 03 mode: `DEFAULT_ARCHIVES = {"03-PUNCH-LIST.md": "32-PUNCH-LIST-ARCHIVE.md", ...}` (:85); its docstring says "then add it to 00-README's reading order, pair P4" (:52-53); `--apply` rehearses and lints first; sweep plus split crosses R3, "4,399 -> 4,525" (:49-51) | not a standalone gate (it is exercised by selftest_lint_docs :1325) | n/a (an operation). Its selftest uses a SYNTHETIC 03 (`PUNCH = ("# Punch List — synthetic...` selftest_lint_docs:151), so the fault does not borrow from the real 03. |
| .claude/hooks/session-sync.ps1 | `Where-Object { $_ -match '^\s*-\s*\[ \]' } \| Select-Object -First 5` (:82) | hook | The first 5 open boxes of the NEW 03 (indented ones count) become the session brief. With zero, the "Open punch-list:" block is silently omitted (:97). |
| /wrapup | "mark the item done in `03-PUNCH-LIST.md` (with date, moved to Done)" (wrapup.md:8) | — | It needs a Done place in 03. Whether one exists today: UNKNOWN. |
| /checkpoint | "punch-list items with their FULL specifications in `03-PUNCH-LIST.md`" (checkpoint.md:10) | — | — |
| /health | only that the 9 files exist (health.md:3) | — | — |
| tools/status.py | does NOT read 03 (Grep `PUNCH\|punch\|03-`: 0 matches) | — | — |
| precheck_prior_art.py (advisory) | `FILES = (05, 06, 07, 08, "03-PUNCH-LIST.md")` (:36-37), plus notes | no | **Silent miss**: content moved to 32 (or 28) becomes invisible to the prior-art search unless 32 is added to FILES. |
| fix_citation_drift.py | DOCS includes 03 (:71) | no | out of scope |
| advise_on_diff.py R-PUNCH | path trigger on 03 (:277-280) | hook | — |
| doc-check.md template | P5 says "grep the slug" in 03 (:15, :34) | — | — |
| staleness-sweep SKILL | 03 cell opening (:20, :66) | — | — |

Other 03 mentions are prose in comments or docstrings only (no read): advise-on-commit.ps1:11, repro_boss_grass_gate, story_harness, probe_bracket_viability, probe_party_l65_audit, and others (READ via grep).

## (2) Citations into 03 (MEASURED, `grep -o '#2[0-9]-[a-z0-9+-]*'`)
| file | slug hits / unique | other mentions of 03 |
|---|---|---|
| 00-README | 0 / 0 | row `| 5 | 03-PUNCH-LIST.md | The work queue | current-state |` (:13) |
| 01-VISION-AND-DESIGN | 5 / 4 | none |
| 02-ARCHITECTURE | 14 / 12 | :122 (closed content "retired to `28-HANDOF...`"), :365, :680 |
| 04-HANDOFF | 30 / 29 | :57 (queue item 1, S2-1b part 2), :138 (quoted old rule: "filed at the top of `03-PUNCH-LIST.md`: `#24-e4healing`", a positional claim) |
| 05-KNOWN-ISSUES | 77 / 46 | 7 mentions, one line citation `03-PUNCH-LIST.md:47` (05:2571) |
| 14-AGENT-PLAYBOOK | 22 / 19 | :33 (`#24-sanitycheck`'s closed entry), :797 (`#24-logcollision-siblings`) |
| 29-REGISTRY | 62 / 40 | none |
| CLAUDE.md | 5 / 5 | 4 mentions |

- **Line citations in .py files** (MEASURED): audit_doc_citations:54 (`:2105`), fix_doc_citations:36 (`:1757`), probe_bracket_viability:17,66 (`:810`), probe_party_l65_audit:17 (`:810`), probe_drift_restatement:38,83,131 (`:47`), run_gates:829 (`:391`). All are in comments or docstrings, and no gate checks `.md:LINE` citations. INFERRED: they are already stale history and none breaks a gate.
- **The TRIAGE INDEX**: referenced by no tool or doc (MEASURED: 0 hits in 00/01/02/04/05/14/CLAUDE.md, and 0 files under tools, .claude, ai-agent or ai_player).
- **Does a slug-to-03 resolver exist?** No. The only slug regex in a 03 reader is probe_closed_item_refs:88 (MEASURED by grep). INFERRED: if an item's TEXT moves and its slug line stays (the archive_sweep pointer keeps every slug, "S-2", :22-26), nothing breaks mechanically. The grep-the-slug convention (P5, doc-check.md, the R-HANDOFF advice :269-271) lands on the pointer. Whether the 04/05/14 slugs all resolve in 03 today is UNKNOWN (03 could not be read).

## (3) A new 32-PUNCH-LIST-ARCHIVE.md
- **README row and R5**: R5 is one-directional. It checks that each `NN-*.md` named in 00-README exists (lint_docs R5 block: `for name in sorted(named - existing): fail("R5", ...)`). A missing row does NOT fail. The row is required only by the archive_sweep docstring (:52-53) and pair P4. The README is 11,431 B against a 19,182 ceiling (MEASURED), so a row fits.
- **What 28 already holds**: README row 15 says 28 holds "archived punch-list entries" (00:23), and 28 has 28 "from 03-PUNCH-LIST"-type hits (MEASURED). So old 03 blocks already live in 28. The 32 target was set by spec 2026-10-19 (BUILD-SPECS-steps-1-2.md:267, :279: "closed `03` items to `32-PUNCH-LIST-ARCHIVE.md`").
- **The 2026-08-28 ruling** ("split by KIND, not SIZE", 06:3580) is about a current-state part N of M. An append-only 32 is a split by kind, so it does not conflict (INFERRED). 06:9651 said "no new numbered file" for 04 only because 28 existed.
- **Does any gate refuse a ~700 KB 32?** No. R3/R7 apply only to the prefixes 01-05 (`CURRENT_STATE = ("01-", ... "05-")` :92). R8 applies only to 00 and 01-05 (:238). R4 needs number 32 to be unused, and `ls` shows that 20 through 31 exist and 32 does not (MEASURED).
- **Gates that WILL scan 32** (inferred to pass, since the bytes are identical to today's passing 03):
  - audit_encoding: `DOCS.glob("*.md")`, :282. It also catches a BOM, so do not write 32 with PowerShell `Out-File`.
  - probe_doc_control_chars: `DOCS.rglob`, :107.
  - probe_citation_ranges: `EXEMPT_PREFIXES = ("06-", "07-", "08-", "28-")`, :63, which does NOT exempt 31 or 32. Its fatal check is inverted ranges only.

## Not run
archive_sweep dry run on 03 (refused). The coordinator should run `py -3.12 tools/story-dev/archive_sweep.py --source "PROJECT KNOWLEDGE/03-PUNCH-LIST.md"` (dry by default).
