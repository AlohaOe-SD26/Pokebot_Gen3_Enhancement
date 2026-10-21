# BUILD SPECS for order step 3: the KB1 merge, N2 + P5, A6, and A5 with L1 + L2 (round 4, 2026-10-19, CRITIQUED)

## CRITIC'S VERDICT (2026-10-19, a second agent, not the author; source: `2026-10-19-backlog-round4/01-specs-step3.md`)

A spec is KEPT only if it has a fault arm AND a control, adds no runtime cloud or Claude dependency, copies no bot code or bot
behaviour (data only, RULING 35), and lowers no rigor. The adversarial Claude passes (S3-1 step 5, W7) are BUILD-time
verification, never runtime; every extractor reads the pinned LOCAL clone, never `gh api`. Bot logs and `runs.jsonl` enter only
as labelled numbers ("bot corpus", a prior on needs), never as code or a style.

| spec | verdict | critic fixes (marked "critic fix" in the text) |
|---|---|---|
| S3-1 KB1 merge | KEPT | the `.gitattributes` line is committed ON ITS OWN BEFORE the merge: a merge that writes the JSON as CRLF could only be re-checked-out with `git checkout -- <path>`, which the destructive-git hook blocks, and `git merge -F` does not carry a dirty `.gitattributes` into the merge commit; `git ls-files --eol` proves LF before V1 |
| S3-2 N2 + P5 | KEPT | N1's count is labelled a determinism check (one regex on both sides), N6 is the control; a decomp ref with no clone present is a loud SKIPPED count, never a pass (new F2); golden queries pin section ids, not line numbers; the stale `--check` prints its one regeneration command |
| S3-3 A6 | KEPT | `chapter_priors.json` is inside the digest scope (fact 3): regenerated only by an interactive session between graded rounds (new E10), never by O1's task; O1 is unbuilt and needs the user's OK, so a session runs `--incremental` until it exists |
| S3-4 A5 + L1 + L2 | slice 1 KEPT (trainers, bosses, maps, campaign); slice 2 (`items_gifts.json`, `events.json` and their pack sections) **NEEDS DESIGN** | slice 2 had a control (20 item records) but no fault arm and no command census; new W4b: the hand-authored campaign order had no test past the 20 milestones; events' flag NAMES are knowledge only (RULING 40) |

**Spot checks of the quoted log formats (grep, read-only, the clone's
`runs/ai0034/batch/L01/debug-logs/Story_(ENDLESS_RESET)-debug-20261018-231500.log`): CONFIRMED.** The `[TRAINER] start opp=265 ...`
and `[TRAINER] end opp=265 ... res=Won money=7368->8868 ...` lines match byte for byte, as do `[BADGE] n=1 party=4/6 box=0 owned=5
spare=0` and the counts 161 `res=Won` / 54 `res=Lost`. One difference, fixed below: the real `f59981 [BATTLE] ... UseItem` and
`f15036 [BATTLE] ended` lines have ONE space after the frame (the draft showed two). The parser splits on `\s+`; E1's fixture
uses the real spacing.

- **What this is:** build-ready specs for step 3 of "The order" in `2026-10-18-improvement-backlog.md`, in the style of
  `2026-10-19-BUILD-SPECS-steps-1-2.md`. Every spec has files, behaviour, acceptance tests with a FAULT arm AND a CONTROL, risks
  and size. **A SPEC, NOT A DECISION; a NOTE, not truth.** Line numbers are notes until the builder re-reads them.
- **How it was made:** read-only. Facts below were measured today by grep, `git show`, `git diff --name-only`, `ls-remote`,
  and two small census scripts run from the scratchpad over `06-DECISIONS-LOG.md` and the learner clone's `runs.jsonl` and logs.
  Nothing was written to the clone or changed in git. Claims I could not measure are tagged UNVERIFIED.
- **Rigor is not lowered:** every spec keeps game-read proofs where a game fact is involved, a fault arm for every gate, a
  control arm that proves the gate is not vacuous, and one adversarial pass by an agent that is not the author.

## 0. Facts measured today that shape the four specs

1. **The KB1 branch adds eight files and changes none.** `git diff --name-only <merge-base> origin/claude/kb1-seasoned-knowledge-cr1f5t`
   lists 8 paths, all status Added: `ai_player/knowledge/seasoned/{species,moves,learnsets,encounters}.json`,
   `ai_player/gates/{extract_seasoned,verify_seasoned}.py`, `cloud/KB1-REPORT.md`, `cloud/KB1-STATUS.md`. Merge base `75c2080a`;
   HEAD is 8 commits past it. **No path is touched by both sides** (`comm -12` of the two name lists is empty), so the merge cannot
   conflict. `cloud/` does not exist on HEAD, so the merge creates a new top-level folder.
2. **The fairness gate cannot see the new folder.** `check_fairness.py:211, 248, 405` use `knowledge.glob("*.json")`, which is
   not recursive. `ai_player/knowledge/seasoned/*.json` is therefore invisible to Rule B today. That is why the merge needs no gate
   edit, and also why the day a loader reads those files, every key must be classified in `KNOWLEDGE_FIELDS` (a separate, graded step).
3. **The digest scope includes the new files.** `provenance.py:51-60`: `PACKAGE_SCOPE = ("ai_player",)`, excluding only
   `ai_player/evidence`, `**/*.md` and the seed ledger. The new gates and JSON are inside the scope, so the merge changes the
   code-under-test tree. `FrozenTree` (G1) turns a mid-sweep change into FAIL "the tree changed mid-run". **Merge between graded
   rounds, never during one.**
4. **A predicted failure of KB1's own check on this machine (not yet run).** `extract_seasoned.py:122` writes with `newline="\n"`,
   and `--check` (`:533`) compares raw bytes of the on-disk file with the fresh output. `git config core.autocrlf` is `true` here
   and `.gitattributes` has no rule for the folder, so the working-tree JSON would be checked out as CRLF and `--check` would
   report "differs" for four identical files. The decomp clone must also be made with `core.autocrlf=false`: the extractor hashes
   raw bytes (`_files` sha256) and its regexes match `\n`.
5. **The decomp pin.** KB1 used `pret/pokeemerald@731ad5bfd6e6f265508d0efcca0ba42f9dcf5881`. `git ls-remote ... master` today
   returns that SHA. The only local clone, `C:/Remote Projects/POKEMON_EMERAL_AI/pokeemerald`, is at `83df84e4` (2026-06-27) and does
   NOT contain the pinned object (`git cat-file -t 731ad5bf` fails). It must not be used for `--check`.
6. **`06-DECISIONS-LOG.md` today:** 722,176 bytes, 314 sections, every one headed `## YYYY-MM-DD -- title`. 69 lines say
   "USER RULING". 28 distinct numbers appear in `USER RULING` headings. **Five numbers appear in headings on more than one date:** 12 (2026-09-23,
   09-25, 09-26, 09-27), 13 (09-23 and 09-25), 23 and 25 (09-28, then 09-29 "CLARIFIED"), 39 (10-15, then 10-16 "decided by Claude
   (USER RULING 39: technical)"). **Two of them (12, 13) are two DIFFERENT rulings sharing a number**, read in the headings: 12 is
   "train all six on the fly ladder" on 09-23 and "on losing the Elite Four, restock and retry" on 09-25; 13 is "if a mon is ever
   removed it is a PC deposit" on 09-23 and "the battle team is L65-75" on 09-25. The 09-26 and 09-27 hits for 12 are applications
   of the 09-25 one, 23/25's second heading is an amendment, 39's is an application. So **a ruling number is not a key**. 13 lines match a
   do-not-reopen phrase (lines 90, 3126, 5133, 5173, 5345, 5585, 6225, 6523, 6524, 6529, 6615, 6834, 7012), and at least one is
   only a quotation of a rule (3126).
7. **`runs.jsonl` today:** 2,424 rows. 2,392 carry `boss_log`, `milestones`, `derail_walls`, `money_last`, `catches`, `dex_owned`,
   `human_score`, `batch_dir`; 32 older rows do not. 1,852 are `usable` (= `complete`), 286 are champions. Only **592 rows (24 %)
   still have a raw log**: raw batches exist for cycles ai0024-ai0036 (13 cycles; ai0004-ai0023 hold none). Every one of the 592 rows
   resolves to `runs/<source>/batch/L<lane:02d>/debug-logs/<log>`.
8. **`boss_log` already exists per row:** per boss `{losses, won, party_first_loss, party_win}` where the parties are Python
   repr strings like `"['Combusken:L17', 'Silcoon:L7', ...]"`, taken by `scoring.py:84-99` from "the newest heartbeat before" the
   fight. So A6 has TWO tiers: tier A from `runs.jsonl` (2,392 rows, survives pruning) and tier B from raw logs (592 rows, richer,
   perishable).
9. **Only 592 of 2,424 rows keep their logs and the loss is continuing.** At 12-hour cycles and `keep_raw_cycles: 20`, the oldest
   raw cycle (ai0024) is deleted after about 8 more cycles, about 4 days from now (ESTIMATE from `ls runs`). O3 (gzip) removes the
   time limit; if it has not shipped by about 2026-10-23, S3-3 goes first.
10. **Decomp shape for the world slice (local clone, 83df84e):** 519 map folders in `data/maps/`, each with `map.json`
    (`connections`, `object_events` incl. `trainer_type` and `trainer_sight_or_berry_tree_id`, `warp_events`, `coord_events`,
    `bg_events`) and `scripts.inc` (`giveitem`, `finditem`, `trainerbattle`). 855 `#define TRAINER_*` ids in
    `include/constants/opponents.h`; `src/data/trainers.h` has 855 trainer blocks, **77 with `doubleBattle = TRUE`**;
    `trainer_parties.h` has FOUR party struct shapes (672 NoItemDefaultMoves, 87 NoItemCustomMoves, 31 ItemDefaultMoves, 64
    ItemCustomMoves). **Badge to field-move table:** `src/party_menu.c:120-127` (Cut = BADGE01 ... Fly = BADGE06), with Surf
    (BADGE05), Waterfall (BADGE08) and Dive (BADGE07) gated in `src/field_control_avatar.c:450-475`.
11. **KB1 did not extract trainers, items, gifts, map links or scripted events** (its report, "Could not extract / not done"). A5,
    L1 and L2 need those slices; they are S3-4's "KB2" below.

**Dependencies:** S3-1 first (it creates the pinned-clone convention); S3-2 and S3-4 reuse that clone and the pin file; S3-3 is
independent of all three and is the time-limited one. **Recommended order inside step 3:** S3-1, S3-2, S3-3, S3-4 (or S3-3 first
if O3 is late). Learner safety: none of these touches `ai-agent/*.py`, so none restarts the learner (`code_signature()` hashes
only `ai-agent/*.py`).

---

## S3-1. THE KB1 MERGE

**Files.**
- MERGE (8 added paths, no edit to any): the four `seasoned/*.json`, `extract_seasoned.py`, `verify_seasoned.py`,
  `cloud/KB1-REPORT.md`, `cloud/KB1-STATUS.md`.
- ADD one line to `.gitattributes`: `ai_player/knowledge/seasoned/*.json text eol=lf` (fact 4), COMMITTED ON ITS OWN BEFORE
  THE MERGE (critic fix), so the merge itself writes the four files as LF.
- ADD `tools/story-dev/selftest_seasoned_crosscheck.py` and register it in `run_gates.py` `GATES`
  (`("selftest_seasoned_crosscheck.py", False)`, cwd `tools/story-dev`). It lives outside `ai_player/` so it adds nothing to the digest.
- ADD `ai_player/evidence/<date>-kb1-merge.txt`, written through `provenance.keep_earlier` like every other evidence writer.
- FOLLOW-UP commit: `git mv cloud/KB1-REPORT.md` and `KB1-STATUS.md` into `PROJECT KNOWLEDGE/ai-research-notes/` with the stub
  marker (the report is an AI agent's claim document: a NOTE by `00-READ-THIS-FIRST.md`), so `lint_docs` and the marker rule apply.
- NOT TOUCHED: `check_fairness.py`, `facts.py`, any `brain/ eyes/ hands/ skills/ world/ host/` file, `mode.py`. KB1 is DATA only.
  A loader plus the `KNOWLEDGE_FIELDS` classification of `seasoned/` is a separate, graded step (`#28-aiagent-v2`).

**Behaviour (the plan).**
1. **Pre-checks (read-only):** `git fetch`; re-run the two `git diff --name-only` lists and require an empty intersection; no
   graded sweep or `run_units` in flight (fact 3); `py -3.12 ai_player/gates/provenance.py` prints a clean-at-HEAD line before.
2. **Pinned decomp clone, outside the repo, never committed:**
   `git clone -c core.autocrlf=false --depth 1 https://github.com/pret/pokeemerald <DECOMP>` then
   `git -C <DECOMP> fetch --depth 1 origin 731ad5bf...` and `checkout 731ad5bf...`. `<DECOMP>` is a sibling folder
   (`C:/Remote Projects/_decomp/pokeemerald`), passed as `--decomp` and later resolved by S3-2's `decomp_root()`. Write the SHA to
   `tools/decomp.pin` (one line) in the same commit as S3-2's tool, or now as a plain file.
3. **Merge:** `git merge --no-ff` with the message in a file (Write tool, then `-F`), naming all 8 paths in the message (session
   rule 1). After it, `git status` is clean, `git show --stat HEAD` lists exactly the 8 added paths (the attribute line is the
   commit before), and `git ls-files --eol ai_player/knowledge/seasoned/` shows `w/lf` for all four (critic fix). Undo, if ever
   needed, is `git revert -m 1 <merge>` (a new commit, no history rewrite).
4. **Verify, in this order, each recorded in the evidence file:**
   - **V1 reproduction:** `py -3.12 ai_player/gates/extract_seasoned.py --decomp <DECOMP> --check` expecting
     `CHECK OK: 4 files identical`. With `w/lf` already proven, a "differs" is a REAL disagreement between the extractor and the
     pinned decomp: a finding to adjudicate, never a reason to edit the extractor until it passes (critic fix; M3 settles fact 4).
   - **V2 independent verifier:** `verify_seasoned.py --decomp <DECOMP>` (default seed 20261015) expecting `221 checks, 221 passed`.
   - **V3 the verifier's own fault half:** `verify_seasoned.py --decomp <DECOMP> --selftest` expecting `6 of 6 plants caught`.
   - **V4 breadth:** three more seeds (`--seed 1`, `2`, `3`). The report says the verifier samples 12 species, 10 level-up, 8 TM,
     4 tutor, 3 egg, 4 held-item, 8 moves and 14 encounter slots with ONE fixed seed; three fresh seeds roughly quadruple coverage
     at seconds of cost. Any failure is a real finding (V2 passing once says nothing about unsampled rows).
   - **V5 offline cross-checks against sources that are not the extractor** (the new selftest; no decomp needed, so it can sit in
     `run_gates.py`):
     - **X1** every move present in BOTH `ai_player/knowledge/moves.json` and seasoned `moves.json`: type, power, accuracy, PP,
       priority equal (names normalized the way `verify_knowledge.key()` does it).
     - **X2** every species in both `ai_player/knowledge/species.json` and seasoned `species.json`: two types, six base stats,
       catch rate, experience yield equal.
     - **X3** `sandbox-pokebot/modules/data/species.json` (412 entries; fields `learnset`, `held_items_rse`, `base_stats`,
       `catch_rate`, `gender_ratio`, `egg_groups`, `abilities`, `evolutions`) against seasoned `species.json` + `learnsets.json`,
       **joined on national dex number, not on name** (names differ: "Nidoran" with a gender symbol). Compare types, abilities,
       stats, catch rate, gender, egg groups, wild held items, level-up (level, move) sets, TM/HM sets, tutor sets.
     - **X4 encounters, the one table with no other static source in-tree:** `sandbox-pokebot/modules/data/emerald_rarity.json`
       (153 species, generated by `rare_species_dataset.py` from the bot's ROM-read encounter index, with `best_rate` = the best
       per-map-and-method summed slot rate and `maps`) against seasoned `encounters.json`: for each species, the set of maps and
       `best_rate`. **KB1's `where_to_find` holds 143 species; the rarity file holds 153. The 10-species gap is the first thing to
       explain** (Safari Zone, Pyramid and Pike, a parse gap?); every unexplained species is a finding, and the check is not
       "equal" but "every difference carries a stated reason".
     - A **non-vacuity guard** on each: the compared count must be at least 90 % of the smaller side, so a join that matches
       nothing cannot pass.
   - Agreement is NOT a confidence signal (session rules): X1-X4 find disagreements to adjudicate against the decomp text by
     hand; they do not certify the rows that agree, because every source here descends from the same decomp.
5. **The one adversarial check (a fresh Claude subagent, not a fork, with tool access):** given `KB1-REPORT.md`, the pinned
   clone, the four JSON files and the instruction "find at least one wrong SEMANTIC claim", scoped to what the verifier CANNOT
   see because it re-reads the same text with the same reading:
   (i) the 50 TM + 8 HM slot-to-move mapping (the report says "58 slots"; check TM01-TM50 and HM01-HM08 against `ITEM_TM01..`
   order, known answers a player holds: TM26 is Earthquake, HM03 is Surf);
   (ii) `PERCENT_FEMALE()` rounding vs the stored byte; the Compound Eyes 20/60/20 held-item rule and the 45/50/5 rule against
   `SetWildMonHeldItem` in `src/pokemon.c`;
   (iii) the fishing sub-range indices (old 0-1, good 2-4, super 5-9) and the `encounter_rate * 16 / 2880` claim;
   (iv) the six Altering Cave headers sharing one map, and the Battle Pyramid/Pike entries with `map: null`;
   (v) egg moves for a species the verifier did not sample.
   It must pick rows by its own seed, not 20261015. **Pass bar:** a finding needs both quotes (the JSON line and the decomp line).
   Findings are adjudicated by me against the decomp; a confirmed error is fixed in the extractor, re-extracted, and added to the
   verifier's plants. **Zero findings is recorded as "no refutation found in N claims", never as "verified".**
6. **Docs (Definition of Done):** `07` entry; `06` entry (KB1 is static knowledge allowed by RULING 40; species `held_items` are
   a per-species static table, not a live hidden item, noted so the classification step can decide); punch-list status; handoff;
   `ai_player/README.md` index line. Tier 0 (`lint_docs`, `audit_doc_consistency`) and Tier 1 before the commit.

**Acceptance tests.**
- **M1 control:** V1 on a LF checkout prints `CHECK OK`; V2 221/221; V3 6/6.
- **M2 FAULT (the `--check` gate is not blind):** copy the four files to a scratch dir, change one byte of one value in
  `learnsets.json`; `--check` against the pinned clone must exit non-zero naming that file. CONTROL: the untouched copy passes.
- **M3 FAULT (CRLF):** convert one copy to CRLF; `--check` must report it. CONTROL: LF passes. (If the fact-4 prediction is wrong
  and CRLF passes, the extractor normalizes already and this test records that instead.)
- **M4 FAULT (X-checks have teeth):** plant a wrong type on one species in a scratch copy; X3 must fail naming it. CONTROL: real
  data passes with the explained-gap list for X4 written down.
- **M5 merge hygiene:** after the commit, `git diff --stat <before> HEAD -- ai_player` shows only additions under
  `gates/` (two files) and `knowledge/seasoned/` (four), no edit to any other `ai_player/` path; `run_units.py` all suites exit 0
  on the new HEAD; `provenance.py` prints clean-at-HEAD.
- **M6 the adversarial pass** (step 5 above), its prompt and its findings saved beside the evidence file.

**Risks.** (1) CRLF/pin mistakes produce a false "differs" or a false "identical" (M3). (2) The verifier shares the decomp
reading with the extractor, so a systematic misreading passes both (the adversarial pass and the known-answer items exist for
this). (3) A merge mid-sweep fails G1 (do it between rounds). (4) 2 MB of JSON in history is acceptable and never rewritten.
**Size:** small: about 60 lines of selftest, one attribute line, one clone, about 2 hours including the adversarial agent.

---

## S3-2. N2 + P5: a rulings index, a verified-facts ledger, and one lookup tool

**Why (measured, fact 6):** 06 is 722 KB with no index; the ruling number is NOT a key (five numbers repeat, two of them for different rulings); do-not-reopen
phrases are 13 lines in prose, one of them only a quotation. About 10 `08` entries re-asked a ruled question (backlog N2);
91 % of decomp fetches repeat another agent's path (backlog, UNVERIFIED here).

**Files.**
- `tools/story-dev/build_rulings_index.py` (stdlib): parses `06-DECISIONS-LOG.md`, writes
  `PROJECT KNOWLEDGE/RULINGS.generated.json` and the human table `PROJECT KNOWLEDGE/RULINGS.md`, and has `--check`.
- `PROJECT KNOWLEDGE/rulings-overlay.json` (HAND-curated, small): the judgments a parser cannot make (below).
- `PROJECT KNOWLEDGE/facts-ledger.jsonl` (append-only; P5) and `tools/story-dev/check_facts_ledger.py` (lint, `--against-head`).
- `tools/decomp_lookup.py` (the lookup; stdlib) and `tools/decomp.pin` (one line, the SHA; S3-1 step 2 shares it).
- `tools/story-dev/selftest_rulings_index.py` and `selftest_facts_ledger.py`, registered in `run_gates.py`.
- Doc edits (outside the managed block): a one-line "first run `py -3.12 tools/decomp_lookup.py ask "<topic>"`" in `CLAUDE.md`
  rule 11, `16-ORCHESTRATION-PLAYBOOK.md`, and the P11 stage templates when they exist. Advisory, measured by P3.

**Behaviour: the index.**
- A section id is `<date>-<sha1(heading text)[:6]>`. NOT an ordinal (the file is `merge=union`, so two machines appending the same
  day can reorder) and NOT the ruling number (fact 6). Line numbers are stored as a hint only.
- Per section the generator records: id, date, line range, title, ruling numbers named in the heading (`USER RULINGS? n`,
  lists like `23, 24 and 25`), punch-list slugs (`#\d+-[a-z0-9-]+`), `KI-\d+` ids, do-not CANDIDATE lines (phrases:
  `do not re-?raise`, `do not re-?open`, `do-?not-?reopen`), supersession CUES in the heading (`CORRECT`, `SUPERSED`,
  `WITHDRAWN`, `REPLACED`, `RE-AFFIRMED`).
- **The overlay carries the judgment, the generator carries the facts.** Overlay key = section id. Fields: `status`
  (`ACTIVE`, `SUPERSEDED`, `WITHDRAWN`), `superseded_by` (an id), `ruling_key` (names which decision a heading
  defines, e.g. `12@2026-09-23` vs `12@2026-09-25`) OR `application_of` / `amends` (an id: a later heading that only applies or
  clarifies an earlier ruling, like 12 on 09-26, 23/25 on 09-29, 39 on 10-16), `do_not_reopen` (one line: what exactly must not be re-asked, and its scope), and per candidate line
  `marker` or `mention` (3126 is a mention). **Sections absent from the overlay default to ACTIVE with no flag**, so an
  ordinary append never forces an overlay edit.
- `--check` fails when: the committed generated files differ from a fresh build (stale; every `06` append triggers this, so the
  message prints the one regeneration command, critic fix); an overlay id resolves to no section
  (a renamed heading); any do-not candidate line is unclassified; two sections name the same ruling number on different dates and the later one carries
  neither `ruling_key`, `application_of` nor `amends` in the overlay (today: 12, 13, 23, 25, 39 -> the first run lists
  every heading that needs a classification); a `superseded_by` points nowhere.
- **One-time curation, the only judgment step:** classify the 13 candidate lines, classify the headings of the 5 repeated
  numbers (about 11 headings), and read the supersession-cue headings (count not measured). Open only those sections (about 20-30 KB of reading), never the whole file. The index header
  says in its first line: **"06 wins. This file is a finding aid; quote the section, never this table."**

**Behaviour: the lookup (`decomp_lookup.py`).**
- `decomp_root()` resolves `--decomp`, else env `POKEBOT_DECOMP`, else the sibling `_decomp/pokeemerald`. It verifies
  `git rev-parse HEAD` equals `tools/decomp.pin` and **refuses with exit 2 and the exact clone commands when it does not** (a
  silent answer from the wrong commit is the failure; the existing June clone must be refused). Paths are derived from the file
  location, never hardcoded (the `audit_flag_names.py` lesson).
- `grep <regex> [--in <glob>]`, `symbol <NAME>` (`#define`, `[NAME] =`, function), `trainer <TRAINER_X>` (id from
  `opponents.h` + the `trainers.h` block + its party), `map <MapName>` (map.json summary), all tolerant of `\r\n`.
- `ruling <text|n>` prints matching sections with the do-not line FIRST and quotes it from 06 (not from the index).
  `fact <text>` searches the ledger. `ask "<words>"` runs all three and prints: matching rulings (do-not first), matching ledger
  rows, decomp hits, then "NO PRIOR RULING OR FACT FOUND" with exit 3 when all are empty. Ranking is token overlap over
  title, first 400 characters, slugs, ruling keys and overlay topics (UNVERIFIED precision; the golden queries below measure it).
- Reading the decomp locally removes the `gh api` fetches that `verify_knowledge.py` and `extract_milestones.py --verify` repeat;
  moving those two onto `--decomp` is a follow-up, not in scope.

**Behaviour: the ledger (P5).** One JSON object per line: `id`, `claim`, `status` (`CONFIRMED`, `REFUTED`, `UNVERIFIED`),
`source` (`{kind: decomp|probe|code|user|evidence, ref}`, e.g. `pret/pokeemerald@731ad5bf:src/pokemon.c:SetWildMonHeldItem`),
`tool` (the command that re-checks it), `dependents` (paths), `first_seen`, `last_checked`, `checked_by`, `correction` (REFUTED
only). Lint rules: CONFIRMED needs `source.ref` and `tool`; `dependents` must exist; a decomp ref must pass the `symbol` lookup
on the pinned clone when the clone is present, and when it is absent the lint prints `SKIPPED <n> decomp refs (no pinned clone)`
and `run_gates` shows a WARN, never a pass (critic fix: a check that silently skips on another machine is vacuous); **a REFUTED row may never be removed or edited** (`--against-head` compares
with `git show HEAD:<file>`). Seeds are limited to facts I have a source for today: the refuted "no healing house on the Route
112/113 corridor" (`ROUTE111_OLD_LADYS_REST_STOP` in `map_data.py`, from `00-READ-THIS-FIRST.md`); opponent id 265 =
`TRAINER_ROXANNE_1` (`opponents.h:269`); the badge to field-move table (`party_menu.c:120-127`); "ruling numbers 12, 13, 23, 25, 39
name more than one decision" (`build_rulings_index.py`).

**Acceptance tests.**
- **N1 control, real file:** the index lists exactly the number of `^## ` headings in the real 06 (314 today); the do-not
  candidate count equals the grep count (13 today, so a drop is visible); every id is unique. (Critic: the generator and the grep
  share ONE regex, so this is a determinism check, not a recall control; N6 is the control.)
- **N2 FAULT:** a synthetic 06 with two sections both headed `USER RULING 7` on different dates and no overlay entry: `--check`
  fails naming both. CONTROL: the same file with `ruling_key` (or `application_of`) overlay entries passes.
- **N3 FAULT:** a synthetic section containing "DO NOT RE-RAISE X" and no overlay entry: fails "unclassified do-not". CONTROL:
  classified `marker` passes; classified `mention` passes AND the lookup does not surface it as a flag.
- **N4 FAULT (drift):** the overlay points at a deleted section id: fails. **N5 FAULT (stale):** append a section to a copy of 06
  without regenerating: fails; regenerate: passes; the append added no overlay obligation.
- **N6 golden re-asks (retrieval is measured, not assumed).** Six known questions, each with the section it must return in the top
  3, taken from sections located by grep today: "tracked commercial ROM" -> the 2026-08-23 RE-AFFIRMED section (06:3119);
  "stash drop" -> 2026-08-13 stash kept permanently (06:2007); "Shoal Cave hunting ground" -> 06:1749; "train the laggard to the
  boss's level" -> 06:5133; "the value question 32x310" -> 06:5173; "B1F" -> the do-not-reopen at 06:6225. Pass: 6 of 6.
  The test stores each expected SECTION ID, not the line number, which moves with every append (critic fix).
  **FAULT:** run the same queries against an index with the overlay emptied (flags gone): the do-not line must no longer be
  printed first, proving the flag is what surfaces it. **CONTROL:** a query about a topic never ruled ("quantum fishing
  tournaments") returns exit 3, "no prior ruling".
- **L1 pin refusal FAULT:** point `--decomp` at the June clone: exit 2 with the clone commands, no answer. CONTROL: the pinned
  clone answers `trainer TRAINER_ROXANNE_1` with id 265 and a first party member of level 12 (the June clone shows level 12
  Geodude; the pinned clone is expected to agree: UNVERIFIED until run). **L2 CRLF:** a copy of one decomp file with CRLF
  endings returns the same hit. **F1 FAULT:** a CONFIRMED row with no `source` fails; deleting a REFUTED row fails
  `--against-head`; appending one passes. **F2 FAULT (critic addition):** a CONFIRMED row whose decomp ref names a symbol absent
  from the pinned clone fails. CONTROL: with the clone path unset, the same file prints SKIPPED with the count and exits as WARN.

**Risks.** (1) The overlay rots: the `--check` failures above are the defence, and unflagged sections still work. (2) The index
becomes trusted over 06: the header, plus `ruling` quoting 06 itself. (3) The ledger is only as good as its `tool` field; a row
whose tool does not re-check the claim is a lie with a format, so lint requires the tool path to exist and appear in `run_gates`
or `tools/`. (4) Adoption is advisory (agents may skip `ask`); P3 measures it as the share of decomp reads that still hit `gh api`.
**Size:** medium-small: about 220 lines (index + lookup) + 90 (ledger lint) + 150 of tests; one hour of overlay curation.

---

## S3-3. A6: EXPERIENCE RECORDS from the bot's games (a script, not agents)

**Inputs (read-only; nothing is written in the clone).**
- `<clone>/ai-agent/data/runs.jsonl` rows. Fields: `log, starter, badges[], e4[], champion, wins{}, losses{}, derails, last_derail,
  end_map, end_pos, end_party (repr string), frames, mode_at_end, progress, score, wall, complete, usable, source, batch,
  code_commit, lane, lane_starter, arm, genome{}, genome_id`, and on 2,392 rows `boss_log{}`, `milestones[[boss, frame]]`,
  `derail_walls[]`, `money_last, species_caught, catches, maps_visited, dex_owned, catch_skips, human_score, batch_dir`.
- Raw logs: `runs/<source>/batch/L<lane:02d>/debug-logs/<log>` (592 rows today), or `runs/<source>/raw.zip` once O3 ships (read
  one member with `ZipFile.open`, S1-1's design). Row to log: `source` + `lane` + `log`.
- The decomp's `include/constants/opponents.h` (via S3-2's pinned clone) to turn `opp=<id>` into a boss name (verified today: `opp=265`
  in a log is `TRAINER_ROXANNE_1`, `opponents.h:269`). Without it the extractor falls back to `runs.jsonl` boss keys.

**Exact log line formats found (one real log, `ai0034/L01/...20261018-231500.log`, 50,409 lines; critic grep CONFIRMED the
TRAINER, BADGE, UseItem, `ended` and `[hb]` lines and the 161/54 counts).** A line is `f<frame> [TAG] ...`.
Tag counts in that log: BATTLE 11,484; DMGAUDIT 11,195; PARTY 3,445; MAP 3,319; hb 1,809; BALLS 1,802; STEP 1,764; MONEY 1,508;
TRAINER 431; PC 219; LEARN 202; STORY 82; GYM_TM 26; BADGE 7.
```
f174824 [TRAINER] start opp=265 class=0x20(LEADER) value=25 lvl_last=15 first=True base=1500 double=False two=False money=7368 heal_stock=- map=11,3 enemy_alive=3
f182534 [TRAINER] end opp=265 class=0x20(LEADER) value=25 lvl_last=15 first=True base=1500 res=Won money=7368->8868 delta=1500 mult=1 heal_stock=- map=11,3
f183601 [hb] mode=Story (ENDLESS RESET) state=7 controllable=False map=RUSTBORO CITY(11,3) pos=(5, 3) party=['Combusken:L17', 'Poochyena:L7', 'Shroomish:L5', 'Nincada:L6'] ids=['Combusken#3E751CAF:L17:exp3637', ...] owned=5 balls=0 money=8868 box=0 badges=1 msg='Story: entering Rustboro Gym to challenge Roxanne...'
f183421 [BADGE] n=1 party=4/6 box=0 owned=5 spare=0
f175478 [BATTLE] [TURN 0] Combusken L16 48/48 -> UseMove:Double Kick(pp26)  vs Geodude L12 33/33
f59981 [BATTLE] [TURN 0] Torchic L9 14/28 -> UseItem  vs Poochyena L3 15/15
f15036 [BATTLE] ended (outcome=BattleOutcome.Won) party=['Torchic:L5']
f2544631 [STORY] WHITEOUT recovery #1 at (0, 2)
f6515466 [STORY] DERAIL #5: Juan: 12 losses with no super-effective answer to Water/Dragon. Need one of: Dragon. Grinding levels will not fix this. ...
f6515466 [GYM_TM] boss=Juan losses=12 faints=[{'Luvdisc': 1, 'Kingdra': 5}, ...] wall=Kingdra outcome='no plan' plan=None error=None why=[...]
f6140356 [TRAINER] start opp=272 class=0x20(LEADER) ... lvl_last=46 ... heal_stock=Revive:3,Full_Heal:8,Hyper_Potion:15 map=15,0 enemy_alive=5
f6133245 [EARLY_BASKET] outcome='bought' plan=[('Revive', 3), ('Full Heal', 8), ('Hyper Potion', 15)] bought={...} money=29320->2020 ...
```
Measured in that log: 161 `res=Won` and 54 `res=Lost` on `[TRAINER] end`; classes seen in `[TRAINER] start` across lanes 1-3:
`0x20(LEADER)` 392, `0x03(TEAM_AQUA)` 147, `0x05(COOLTRAINER)` 122, `0x09(TEAM_MAGMA)` 103, `0x35(MAGMA_LEADER)` 43. Heartbeats are
3,600 frames apart (f3601, f7201), so the party read for a fight is up to a minute old: record `party_age_frames`.
**Limits found, to state in the output's header:** `UseItem` turns do NOT name the item (32 lines, none named), so "items used"
means a count of `UseItem` turns per fight plus the before/after `heal_stock` difference between consecutive bosses; no log line
carries a move list or a held item, so moves are "moves actually used" (a lower bound).

**Files.** `tools/experience/extract_experience.py` (NOT in `ai-agent/`, so the learner never restarts), `tools/experience/test_extract_experience.py`
(+ a golden mini-log fixture), output `tools/experience/store/runs_experience.jsonl` (git-ignored; included in O4's nightly zip)
and `store/cursor.json`, aggregate `ai_player/knowledge/experience/chapter_priors.json` (committed, small, regenerated when the
sample grows 10 %), and a one-line call from O1's 30-minute task: "new cycle folder since the cursor -> run `--incremental`".
**Critic fix:** the priors file is inside the digest scope (fact 3), so only an INTERACTIVE session regenerates it, between graded
rounds, committed with explicit paths; O1's task only appends to the git-ignored store (E10). O1 is unbuilt and needs the user's OK
for scheduled tasks, so until it exists a session runs `--incremental`, at the latest before ai0024 is pruned (about 2026-10-24).

**Behaviour.**
- **Incremental and append-only:** records are keyed `source/lane/log`; a run already in the store is never rewritten; the cursor
  lists extracted keys. Extraction happens BEFORE a cycle can be pruned (the cursor is the safety net; fact 9). Streaming,
  line by line, one log at a time (the largest seen is 19 MB; a cycle is about 1.3 GB).
- **Tier A (all 2,392 rows with `boss_log`):** per boss `won`, `losses`, `party_first_loss`, `party_win` parsed with
  `ast.literal_eval` into `[{species, level}]`; `frame` of the win from `milestones`; `wall` and `derail_walls` as the failure
  label (top labels today: "unreachable target" 500, "boss wall: Tate & Liza" 303, "E4 refused: League basket short" 288,
  "CHAMPION" 286, "boss wall: Norman" 194, "boss wall: Juan" 186); `money_last`, `catches`, `dex_owned`.
  The 32 rows without `boss_log` are counted and listed, never silently dropped.
- **Tier B (rows whose log exists):** per `[TRAINER] start/end` pair of a boss class: fight number, `lvl_last` (the foe's top
  level as the bot logged it), `res`, `money` before/after, `heal_stock` before, `UseItem` turn count and the set of moves used
  between start and end, the party from the newest `[hb]` (`party=`; the PID part of `ids=` is DROPPED), `party_age_frames`;
  `[BADGE] n=` frame; `[STORY] WHITEOUT` count and positions; `[STORY] DERAIL #n` texts (first 200 characters, top 3 distinct);
  `[GYM_TM]` `wall=` species (names the foe mon that beats the party).
- **Censoring (the statistics rule):** a game cut by the 12-hour limit (`usable: false`; 572 rows) is a valid prefix for the
  bosses it resolved, but its unresolved boss is NOT a failure. Boss stats use every row where the boss was resolved (won, or
  >=1 loss with `usable`); failure and wall counts use `usable` rows only, and each aggregate prints both `n` and `n_censored`.
- **`chapter_priors.json` per boss** (numbers only, labelled `source: "bot corpus"` on every block; bot data is a prior on
  NEEDS, never a style): n fought, first-try win rate, losses distribution, party size, level quantiles (min, mean, max of the
  team) at first loss and at win, win rate by 3-level band of team mean level with `n` per band, money quantiles at the fight,
  whiteouts per boss, failure labels with counts. **Species shares are excluded** from the AI-facing file (that is the bot's style);
  they stay in the git-ignored per-run store.

**Acceptance tests.**
- **E1 golden:** a hand-built 40-line log using exactly the formats above (one boss won first try, one lost twice then won, one
  truncated mid-fight) produces the exact expected record, including `incomplete: true, res: null` for the truncated fight.
- **E2 REAL-data cross-check (the control, with an independent second source):** for all 592 raw-available rows, the tier-B
  `won` and `losses` per boss equal that row's `boss_log` (made by `scoring.py`'s separate parse). Expect agreement on every boss;
  every disagreement is listed and adjudicated, never averaged away. UNVERIFIED: that `scoring.py` counts `losses` as `res=Lost`
  ends; the builder reads `scoring.py:84-100` first and writes down the definition.
- **E3 FAULT (a lie is caught):** in a scratch copy of one real log, flip one gym's `res=Won` to `res=Lost`; the record must carry
  `agrees_with_runs_jsonl: false` for that boss and the run exits 1. CONTROL: the untouched log agrees. **E3b FAULT:** truncate a real
  log in the middle of a gym fight: that fight is `incomplete`, never `Won`.
- **E4 FAULT (censoring):** mark one Tate & Liza-stuck row `usable: false` in a scratch copy; the failure count drops by exactly
  one while the boss-resolution count is unchanged. CONTROL: `usable: true` counts it. Without this a cut game inflates "wall" statistics.
- **E5 determinism, said as such:** two runs on the same input are byte-identical (a determinism check, NOT a replication,
  session rule 8); `--incremental` after adding one log appends one record and leaves the earlier bytes untouched (hash the prefix).
- **E6 archive parity:** build a zip of one real log inside the test (stdlib, no dependence on O3 being built) and read it: the
  record equals the raw-folder record.
- **E7 fairness/privacy gate on the AI-facing file:** no match for a PID (`#[0-9A-F]{8}`), no `(x, y)` position, no flag or var
  name. FAULT: plant a PID in a scratch priors file; the gate fails. CONTROL: the real file passes.
- **E8 format-drift canary:** a log of more than 1,000 lines with zero `[TRAINER] start` lines is recorded `parse_suspect: true`,
  not as an empty game; unknown tags are counted, not fatal.
- **E9 measured, not assumed:** record the wall time and the share of rows by tier in the `07` entry (UNVERIFIED: a full pass over
  592 logs is minutes, not hours).
- **E10 FAULT (critic addition, the priors file never changes mid-sweep):** `--incremental` writes only under `tools/experience/store/`;
  a test runs it on a scratch copy and asserts the `ai_player/` tree digest (`provenance.py`) is unchanged. FAULT: point the priors
  output into the scratch `ai_player/` from the incremental path; the digest assertion must fail. CONTROL: the real flags pass.

**Risks.** (1) Log format drift between `code_commit`s: E8 plus recording `code_commit` per record. (2) The corpus is the bot's:
grinding to 65, spin-hunts; every block is labelled and species are withheld. (3) Party read up to a minute stale: stored. (4) The
raw tier is perishable until O3: the nightly incremental run is the safeguard. (5) The records say what happened, not why it was
right; they feed a prior (L4, L5, L10), not a policy. **Size:** medium: about 260 lines + 200 lines of tests.

---

## S3-4. A5 CHAPTER PACKS with L1 (campaign manifest) and L2 (boss book): ONE generator, "KB2"

**One generator, two verified layers.** KB1 covers species, moves, learnsets and encounters. KB2 adds what A5 needs: trainers and
bosses, maps and links, items and gifts, scripted events. L1 and L2 are views of KB2 plus a hand skeleton and A6's priors, so
the pack generator and the AI's knowledge come from the same files (round 3's "two generators would be rework").

**Files.**
- `ai_player/gates/extract_world.py` (imports `Decomp` from `extract_seasoned.py`; stdlib) and `ai_player/gates/verify_world.py`
  (independent: regex over the raw text, does NOT import the extractor; `--seed`, `--selftest`, `--plant`).
- Outputs under `ai_player/knowledge/world/`: `trainers.json`, `bosses.json` (L2), `maps.json`, `items_gifts.json`, `events.json`;
  and `ai_player/knowledge/campaign.json` (L1). Input skeleton: `ai_player/gates/campaign_skeleton.json` (hand-authored).
- `tools/make_chapter_pack.py <N>` -> `PROJECT KNOWLEDGE/chapter-packs/ch<N>.json` + `.md` (the .md at most ~12 KB, with a
  generated "LOAD-BEARING CLAIMS" list for the adversarial agent).
- Same `.gitattributes` rule for `knowledge/world/*.json` and `campaign.json`; none of it is read by AI code until a loader and a
  `KNOWLEDGE_FIELDS` classification exist (the folders are not globbed by `check_fairness`, fact 2).

**Inputs and what each file holds (decomp-derived; the pinned clone, never `gh api`).**
- `trainers.json`: every id in `opponents.h` (855) joined to its `trainers.h` block and party, parsing ALL FOUR party shapes
  (fact 10): `id, symbol, name, class, double (doubleBattle), party[{species, level, moves?}]`, plus `rematch_of` for `_2.._5`.
  **Withheld by an explicit allowlist: `iv`, `aiFlags`** (USER RULING 44, 2026-10-21: `heldItem` is ALLOWED, a seasoned player
  knows what a boss holds; exact stats and AI flags stay withheld). Before that ruling: the backlog said boss held items and stats stay out until the
  user rules them static knowledge (RULING 40 boundary). The constant `WITHHELD_FIELDS` is tested (W1).
- `maps.json`: per map folder: `id, name, region_map_section, map_type, requires_flash, allow_cycling/escaping/running,
  connections[{dir, map, offset}], warps[{dest_map, dest_warp_id}]` (coordinates kept, a seasoned player knows where doors are),
  trainer objects `{script, trainer_type, sight, x, y}` joined to `trainers.json` through the `trainerbattle_*` line in
  `scripts.inc`, item balls and hidden items (`bg_events` of type `hidden_item`).
- ⛔ **NEEDS DESIGN (critic), slice 2, not build-ready:** `items_gifts.json` and `events.json` below have a control (W2's 20 item
  records) but NO fault arm, and their input shapes are unmeasured. Before any parser: (1) a census of every distinct `scripts.inc`
  command with its count on the pinned clone, written down; (2) a fault arm per file, at least W2 plants (e) one field item moved
  to another map and (f) one `setflag` dropped from a script, each reported by the independent verifier; (3) for `events.json`, the
  rule that flag NAMES are static knowledge only: the AI may never READ a flag live (RULING 40 hidden state), and the
  `KNOWLEDGE_FIELDS` step must classify them so.
- `items_gifts.json`: field items (object script -> `finditem`), hidden items, gifts (`giveitem`, `givemon` with the script
  label), TM gifts, and marts. UNVERIFIED how many shapes `scripts.inc` has beyond `giveitem`/`finditem`; Route104 alone has 3
  such lines. The builder greps every distinct command before writing the parser, and the verifier counts them independently.
- `events.json`: per map, the `setflag`/`setvar`/`goto_if_set`/`trainerbattle`/`special` lines, limited to flags that exist in
  `sandbox-pokebot/modules/data/event_flags/emerald.txt` (a phantom flag name reads False forever: `audit_flag_names.py` runs on
  the output, same rule as for any story code).
- `bosses.json` (L2): per gym leader, Elite Four member, Champion, rival fight, Magma/Aqua leader and admin: `id, role, order,
  double, party[{species, level, moves, types}]` (`types` derived from KB1 species, marked `derived_from`), the rematch ids, and a
  separate `measured` block copied from A6's `chapter_priors.json`, **labelled `source: "bot corpus"`**; plus short `notes` that
  change play only where a decomp or recon source is cited (for example Juan's Rest/Double Team stall, cited to the party's moves).
- `campaign.json` (L1): the skeleton fixes the ORDER and ids (story order is design, not decomp-derivable); the generator fills
  each entry's `needs` from data:
  ```
  { "id": "...", "chapter": N, "order": K, "area": [map names], "boss": "ROXANNE"|null,
    "needs": { "field_moves": [{"move":"SURF","badge":"BADGE05","ref":"src/field_control_avatar.c:450"}],
               "badges": [..], "key_items": [..], "party_min": 1|2|3, "double_battle": bool,
               "types_ahead": [..] (derived from bosses.json), "level_band": {"low":..,"high":..,"basis":"decomp boss top level"},
               "money_checkpoint": null },
    "measured": {"first_loss_level":..,"win_level":..,"source":"bot corpus"} }
  ```
  **Never routes, coordinates or step lists** (L1's rule: a manifest must not become the bot's script). `party_min: 2` comes from
  `double` of the boss's trainer block (decomp-verified: Tate and Liza); the Space Center multi battle's 3-mon party comes from
  `20-POST-FORTREE-RECON.md` 4.6 and is marked `basis: recon, decomp UNVERIFIED` until the adversarial pass checks it.
  The badge to field-move rows are read from `party_menu.c:120-127` and `field_control_avatar.c:450-475` by the extractor, not typed.
- **Chapter pack (A5)** for chapter N = the skeleton entries with `chapter == N` -> their `area` maps + one ring of neighbours
  (by `connections`/`warps`) -> from KB1/KB2: map links; trainers on those maps (single/double, sight, party levels min..max,
  species); items, hidden items, gifts, marts; scripted events with flags; the chapter's bosses; wild encounters for the area
  (species, levels, rates, from KB1); who learns each needed HM (KB1 learnsets); and from A6 the chapter's measured traps (top
  wall label, level at first loss and at win, whiteouts), each tagged `bot corpus`. Header: every source SHA, the generator's
  hash, the pin. Only the LOAD-BEARING CLAIMS list (progress-gating flags, HM gates, double battles, one-way warps, boss teams)
  goes to an agent, as an adversarial prompt. **Critic fix:** the first packs ship WITHOUT the items, gifts, marts and scripted
  events sections (slice 2 NEEDS DESIGN); their header says so, so a reader never takes an absent item list for "no items here".

**Acceptance tests.**
- **W1 withheld fields FAULT:** add `heldItem` to one trainer in a scratch output; the gate that scans every file under
  `knowledge/` for `WITHHELD_FIELDS` fails. CONTROL: the real output passes. (Same gate for `aiFlags` and `iv`.)
- **W2 plant verifier (the L1/L2 `--plant`):** `verify_world.py --plant` changes in memory (a) a boss's level, (b) Surf's badge
  from BADGE05 to BADGE04, (c) a `doubleBattle`, (d) one connection's map; it must report exactly those four. CONTROL: no plant,
  zero mismatches over a fixed-seed sample of at least 60 trainers, 20 maps, 20 item records, and the full 8 gym leaders + E4 +
  Champion.
- **W3 recall against an independently authored artefact (the real control for A5):** `ai_player/knowledge/milestones.json`
  already holds a hand-recon'd `trainers` table (ids, flags, levels for the chapter 1-4 trainers, built through `gh api` by
  `extract_milestones.py`). The generated packs for chapters 1-4 must contain EVERY trainer, flag and level that table lists for
  those chapters (recall 100 %); extras are listed and adjudicated, not hidden. **FAULT:** delete one trainer's object event from a
  scratch `map.json`; recall must fall and the test must fail (so it cannot pass vacuously). If milestones' chapter numbers do not
  map one-to-one to the pack's (its 20 milestones span chapters 1-4: ch1_intro ... ch4_roxanne), the builder records the mapping.
- **W4 consistency:** `campaign.json` ids equal `milestones.json` ids for the 20 existing milestones (control) and every later
  entry's `area` maps resolve in `maps.json`; every FLAG/VAR passes `audit_flag_names.py`. FAULT: rename one map in a scratch skeleton;
  the generator exits non-zero naming it.
- **W4b order consistency (critic addition; the hand-authored order had no test past the 20 milestones):** every badge in an entry's
  `needs.badges` and `needs.field_moves[].badge` is awarded by the boss of an EARLIER entry. FAULT: swap two gym entries in a
  scratch skeleton; the check fails naming both. CONTROL: the real skeleton passes.
- **W5 shape coverage:** all four party shapes parse: the count of parsed parties equals the count of `static const struct
  TrainerMon*` arrays in `trainer_parties.h` (854 in the local clone) and every trainer's party length is >= 1. FAULT: drop one
  shape's regex; the count test fails.
- **W6 no-routes rule:** a gate fails if `campaign.json` contains any key named `x`, `y`, `route`, `path`, `steps`, `coords`.
  FAULT: plant one; control: real file passes.
- **W7 the adversarial pass:** one fresh Claude subagent per chapter pack, handed the pack's load-bearing claims and the pinned
  clone, told to REFUTE; findings need both quotes. Record the tokens each used; the expected saving is the 8 of the 9 agents
  of the chapter 3-4 recon (about 16M tokens; UNVERIFIED until P3 measures one).
- **W8 L1 consumer check (data only, no graded code):** a pure test reads `campaign.json` and, for a fixture party with no Surf
  learner (KB1 learnsets) and the milestone that needs Surf, prints "no Surf learner" (the 2026-08-05 case, 52.0 % to 15.8 % finish
  rate). The goal-manager lookahead that USES this belongs to the R1/L4 step; this item only supplies and tests the data.

**Risks.** (1) `scripts.inc` has more command shapes than the parser knows: the independent verifier counts each command class
separately and W3 catches omissions on chapters 1-4. (2) A manifest that turns into a chapter script: W6 and the rule in L1.
(3) Ruling 40 boundary on boss moves and held items: held items, IVs and AI flags are withheld by default; moves are kept as the
backlog specifies (flagged in "Needs the user"). (4) The pack becomes a source of truth: its header says it is generated, and
the decomp wins. (5) KB2 is larger than KB1 (855 trainers, 519 maps): build in two slices, bosses and campaign first (L1+L2 are the
"decide early" items), then maps, items and events, then the pack tool.
**Size:** large overall: about 700 lines of extractor + verifier + 250 lines of tests; the first slice (trainers and bosses and
campaign) is medium and can ship alone.

---

## Summary

| spec | files (new) | proof of correctness | fault arm / control | size |
|---|---|---|---|---|
| S3-1 KB1 merge | 8 merged, 1 attribute line, 1 selftest, 1 evidence file | reproduce (`--check`), independent verifier, 3 extra seeds, 4 cross-source checks, 1 adversarial agent | M2-M4 / real data | small |
| S3-2 N2 + P5 | index + overlay, ledger + lint, lookup, pin | golden re-asks (6), `--check` of index vs 06 | N2-N5, L1, F1 / never-ruled query | medium-small |
| S3-3 A6 | extractor, store, priors, tests | tier-B vs `runs.jsonl` `boss_log` on 592 rows, golden log | E3, E4, E7 / untouched log | medium |
| S3-4 A5 + L1 + L2 | extractor, verifier, 6 data files, pack tool | plant verifier, recall vs `milestones.json`, adversarial per chapter | W1, W2, W3 FAULT, W4b, W5, W6 / real output | large (first slice medium); slice 2 (items, events) NEEDS DESIGN |

## Needs the user (plain-English calls only)

1. ✅ **ANSWERED: USER RULING 44 (2026-10-21): held items ALLOWED, exact stats (IVs) and AI flags WITHHELD, moves and levels kept.**
   The question as it was: **Boss moves and held items.** The backlog already says held items and stats stay out until you rule them "knowledge a seasoned
   player has". This spec withholds held items, hidden stats and the trainers' AI flags by default and keeps each boss's moves and
   levels. Say so if you want moves withheld too, or held items allowed.
2. **Bot statistics shown to the AI.** The AI-facing numbers (levels at first loss and at win, losses, money) are labelled "bot
   corpus". Which species the bot chose are kept out as the bot's style. Say so if you want those shares included.
3. **Trainer positions and sight ranges (critic addition).** `maps.json` keeps each trainer's tile and sight range and each door's
   position, as static map knowledge (RULING 40 "maps"). Say so if a seasoned player should not know exact sight ranges.

## What I did not verify

- The CRLF prediction in fact 4 (code and `core.autocrlf` read; `--check` not run). M3 is built to settle it.
- That `scoring.py` counts `losses` as `res=Lost` ends (E2 needs it; read `scoring.py:84-100` first).
- That the pinned commit's `trainers.h` and `trainer_parties.h` have the same four shapes as the June clone (counts quoted are the June clone's).
- How many distinct `scripts.inc` command shapes exist (only `giveitem`/`finditem`/`trainerbattle` were seen).
- Runtime of A6 over 592 logs and of the full KB2 extraction.
- The 10-species gap between `emerald_rarity.json` (153) and KB1 `where_to_find` (143) is a lead, not a finding; its cause is unread.
- The "91 % of decomp fetches repeat" figure and the "~16M tokens for chapters 3-4" figure come from the backlog and were not re-measured here.
- Whether `git merge --no-ff -F` is accepted by the project's git hooks (the destructive-git hook was not exercised; the revert path uses only a new commit).
