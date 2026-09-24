# Punch List — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. The agreed work queue. ⛔ **THIS FILE IS AT ITS LINE BUDGET — run `lint_docs.py` for the live number. The next edit that GROWS it turns Tier 0 RED; retire a completed item first (SUMMARISE + POINT at `07-CHANGELOG.md`, never delete).**
> Item format: `- [ ] #N — description` (N never gets reused; check items
> off with `[x]` and move them to Done with the completion date).
> Full future-idea catalog: `09-FEATURE-BRAINSTORM.md`.
>
> ⛔ **A SANDBOX↔CUSTOM DRIFT FIGURE QUOTED INSIDE AN ITEM IS A DATED CLAIM ABOUT THAT ITEM'S
> FILES, NEVER THE REPO'S CURRENT NUMBER.** Several items quote one, each true on its own
> promotion date. **The only authority is `promote.py --check`**, and `04-HANDOFF.md`'s STATE row
> names the currently expected set. Added 2026-08-14 after a `#24-roster` line claimed the KI-63
> wiring was "NOT promoted" for hours after it was — the same failure in the other direction.
> ‼ Note the phrasing here is deliberate: `audit_doc_consistency.py` matches the literal figure
> and **cannot tell a quotation from a claim**, so naming it even as a warning turns this line red.

## ‼ TRIAGE INDEX (2026-08-10) — read this before scanning 100+ entries

**The problem this solves:** the list carried **117 open/partial entries**, and a scan could not
distinguish "being worked on today" from a roadmap line written three weeks ago. Two entries were
found stale-open for **8 days** while their code had shipped, and one contradicts the handoff.
Nothing below was deleted — items are closed only with evidence, and conflicts are flagged for the
user rather than resolved unilaterally.

### 1. 📦 **RETIRED 2026-09-10 — the old front-of-file index table is in `28-HANDOFF-ARCHIVE.md`.** ⛔ It was self-described as *“NOT AN ACTIVE LIST”* and had gone stale TWICE by naming whatever was live when last edited. ⇒ **`04-HANDOFF.md`’s `➡➡➡` NEXT ACTION marker is the one thing to act from** — never a table in this file.

### 2. BLOCKED ON A USER DECISION — no work should start on these
| item | the decision |
|---|---|
| ~~PROMOTE Ch15 + `#24-strength`~~ | ✅ **DONE 2026-08-10 night — user-approved.** Promoted and **verified DRIVEN in `custom-pokebot`** (`--build custom` → `groudon=True`, 0 whiteouts). **Source drift: ZERO**, so the sandbox re-base is a no-op. See `custom-pokebot/DIVERGENCE-LOG.md`. |
| ~~`#24-magmahideout` status conflict~~ | ✅ **RESOLVED 2026-08-10.** The conflict was "this list says DEFERRED, the handoff calls it the next lever". The handoff was right, the deferral's *reason* was wrong three separate times (see the entry below), and the chapter is now **DONE**. |
| the boss-healing response | items / burst damage / stop promising an answer — see `04-HANDOFF.md`. ‼ **2026-08-11 sharpened it**: the Magma Hideout loss is **Crobat CONFUSING the two best attackers into killing themselves** + Maxie healing Camerupt 22→67. So the menu of answers now includes **status response** (switch out / Persim Berry), not just burst damage and items. |
| **KI-52 — `lead_cannot_battle_action`** | ‼ **NEW 2026-08-11.** A WILD battle ends the run when the lead drops below `hp_threshold`, **with five healthy party members unused** (measured, Magma Hideout 4F). `rotate` is obviously right there — but **`flee` is CORRECT for shiny hunting**, so a global flip trades a story derail for a hunting regression. Needs a scope decision: mode-scoped override, a story battle strategy, or leave it. |
| `#doc-policy-05` | should `05-KNOWN-ISSUES` drop an entry at sandbox-fix or at promotion? |
| `#24-organicteam` | ✅ **APPROVED — GATE LIFTED (user 2026-08-06, re-confirmed 2026-08-14).** ⛔ This cell read *"deferred by the user on purpose 2026-08-05. Do not start early"* until 2026-08-14 and was stale by eight days; it is the line the session-start catch-up summary quotes, so it misdirected every cold start. Build order: the three PC defects first, then this. |

### 3. THE MEASUREMENT PROBLEM — affects every outcome item above
Finish rate has been unresolvable in **every** batch: 25.0 → 33.3 → 16.1% at n≈30 runs each. To
resolve a 10-point change needs ~300 runs ≈ **30 hours of batching per question**. Battle-level
metrics have ~800 samples per batch instead. **Grade mechanism work on battle-level metrics**
(boss win rate, item landings, heal events); treat finish rate as a lagging indicator only.

### 4. DORMANT BACKLOG — real ideas, nobody is working on them
GUI/dashboard (`#30`, `#31`, `#32`, `#33`, `#36b`, `#25`, `#26`, `#28`), dex/analytics tooling
(`#9`, `#11`, `#22`, `#23`, `#34`, `#35`, `#41`, `#42`, `#45`), and story sub-features not yet
scheduled (`#24-ui`, `#24-shops`, `#24-autosave`, `#24-defeat`, `#24-personality`, `#24-favourite`,
`#24-badges*`, `#24-gymtrainers`, `#24-partyvariety`). ‼ Several are marked "BUILT IN SANDBOX
2026-07-19" and were never verified or closed.

### 5. ✅ DUPLICATE / OVERLAPPING IDS — CONSOLIDATED 2026-08-10 (user-approved) — 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-08, R3 budget).
- [x] ⛔ CLOSED bookkeeping — which duplicate IDs were merged, and why. Not a live item.

### 6. CLOSED BY THIS TRIAGE (evidence in each entry)
* `#24-leadcounter` — shipped; `is_hunted_counter` is in `team_policy.lead_rank_key`.
* `#24-counters` phase 2 — shipped and batch-validated repeatedly (z = +3.24 on Machop).
* the "READY TO APPLY THE MOMENT BATCH `20260802-160603` LANDS" heading — that batch landed
  2026-08-02.

### Marker states (documented 2026-07-27 — the file uses THREE, not two)
| marker | meaning |
|---|---|
| `- [ ]` | open — not started, or started and not landed |
| `- [~]` | **partial** — built but not fully verified/promoted, or v1 done with follow-ups |
| `- [x]` | done |

⛔ **NO COUNTS ARE QUOTED HERE ON PURPOSE — `lint_docs.py` prints them and IS the authority.**
This table carried `80 / 17 / 37` from 2026-07-27 until a 2026-08-17 audit recounted the boxes and
measured **98 / 22 / 95** — stale by +18 / +5 / +58, and it had survived every doc pass since.
‼ A hand-typed tally in a file whose items change daily is stale the moment it is written; this is
the same rule the handoff's LINE BUDGETS block already applies to its own limits. **Count the
boxes** (`grep -c '^- \[x\]'`), never re-type a tally.

‼ `- [~]` is load-bearing and was previously undocumented: several `[~]` items read as
"DONE" in their text (e.g. `#24-move`, `#24-resume`) while still carrying open follow-ups.
Do not treat `[~]` as either finished or unstarted without reading the entry.

**Status audit 2026-07-27** (`#doc-audit-1`, partial — see `#doc-audit-2`): 98 distinct
`#`-ids carry a checkbox; exactly **one** id had a genuinely conflicting status
(`#24-pokenav-faithful`, now cross-linked — it is a legitimate RECURRENCE, not a
bookkeeping error). No item marked `[x]` was found whose code is missing. A full
open-vs-built sweep of all 80 open items has **not** been done.

## Now (active focus)

### ‼ MIXED — items filed 2026-09-12 AND 2026-09-13; **read each bullet's own marker, the heading does not grade them.** Evidence: `07-CHANGELOG.md` 2026-09-12 (midday) and 2026-09-13
- [x] ✅✅ `#24-wallydecline` — **CLOSED 2026-09-13. Fixed, promoted, VERIFIED AT SCALE: Wally 12% → 100% (35/35), `DeclineWallyBattle` 85 → 0.** B is NO at a Gen-3 yes/no; the decline flag is never cleared by anything in the decomp and Wally blocks the only tile the gym door opens from. `20260913-092254` vs `20260912-104105`, both single-build: **Mauville watchdog deaths 62 → 0**, runs ENDED 70 → 10 (they survive longer), depth **9-12×** at gyms 3-6 while UPSTREAM milestones are FLAT (Roxanne 1.0×, Route110 1.0×) — that shape is the control. ‼ Deaths RELOCATED as predicted: whiteouts 409 → 753, new end reasons Victory Road / Juan / Winona / Tate & Liza ⇒ it bought DEPTH, not survival. ⛔ Grade this site on the `POKEBOT_WALLY_FAULT=decline` arm, NEVER a single green run — the pre-fix masher passes here by phase luck. Gate #58. Evidence: `07-CHANGELOG.md` 2026-09-13.
- [ ] ⬇⬇ `#24-rival110` — ⛔ **DOWNGRADED 2026-09-13 THE SAME DAY IT WAS FILED: I RANKED IT ON DATA FROM A BUILD I HAD JUST SUPERSEDED.** It was filed as *“the largest measured defect, 52.3% of every whiteout”* from batches `20260912-*` — both **PRE-`#24-wallydecline`**. Re-derived on the CURRENT build (`20260913-092254`, commit `f039bffc`): **ROUTE110 = 47 losses = 6.3%, the 6th site**, loss rate 42.7%/attempt (47 losses of 110 rival attempts, `20260913-092254`). It was 44.1% / 57.9% in the two old batches. ‼ **AND POOLING THOSE TWO WAS ALSO WRONG** — they are the ARM-ON and ARM-OFF halves of the `POKEBOT_MAINTAIN` A/B, i.e. treatment and control, and they disagree (44.1% vs 57.9%). ⭐ **STILL TRUE AND WORTH KEEPING:** the fight has **no `grass` key**, `:2813-2816` prints *“no training grass here — re-attempting is the training”* and trains nothing, and band prep is **NOT vacuous** — mirrored over **530 real loss parties**, `need` is non-empty in **95.8% / 98.7% / 99.2%** of draws at target 18/19/20 (2-3 mons). ⛔ **BUT ITS NAMED FIX IS UNSAFE.** ⚠ *(I first wrote “there is no legal ground” here; a `calculate_path` recon corrected me — **ROUTE117 (31,16) sweeps two-way clean** from the Cycling Road north gate door (106wp) and Mauville PC (62wp), and is already a promoted `TRAINING_GRASS` entry.)* The real objections are: (1) the grass SOUTH of the rival (x26-37,y63-71) looks ideal from the staging tile but **its only door is the trigger row — it is BEHIND the fight**; (2) `ROUTE110 (31,44)` is a **measured ONE-WAY ledge** (gate→tile FAIL, tile→gate OK 66wp), corroborating `early_game.py:3906`; (3) **KI-48 is about the DRIVEN navigator**, and a `calculate_path` OK is not proof the bot can walk it; and (4) adding the key flips `grass_is_fodder` → silently disables `boss_mode` (a KI-80-guarded path). ⇒ park it; do not add a `grass` key on this evidence. ⭐ **AND A DECOMP NOTE SUGGESTS THE DIAGNOSIS IS TYPE-COVERAGE, NOT DEPTH — but it is a NOTE: `ai-research-notes/2026-09-13-route110-rival-decomp.md`.** ⚠ Its key claims are the note author's own **CALCULATIONS, not emulator measurements**, and it says so: that Grovyle's 4× Absorb may HEAL more than Marshtomp can deal (an attrition loss with no HP threshold), that the per-starter level thresholds are ~L29/L30/L23, that *“the fix is one Pokémon, not nine levels”*, and that the ace is sent out **second, not third**. ⛔ **NONE of that is verified here** — read the note, then confirm anything load-bearing in our own harness before code depends on it (`ai-research-notes/00-READ-THIS-FIRST.md`).
- [x] ♻ `#24-norman-lead` — **RETIRED THE HOUR IT WAS FILED: IT IS A DUPLICATE OF THE OPEN `#24-leadpolicy`, WHICH THE USER ALREADY RULED ON.** I filed it as a fresh *“Hypothesis (UNVERIFIED)”* that `_lead_best_matchup` fronts a weak mon at Norman. That is **KI-25** (opened **2026-07-27**, HIGH) and `#24-leadpolicy`, which name the same function, the same cause and **the same boss** — *“P4 led Shedinja L20 vs Norman … lost to Slaking's Faint Attack”*. ⛔ **AND MY INSTINCT WAS THE OPTION THE USER REJECTED:** I reasoned from *“the lead is six levels below our best”*, i.e. level-gap weighting = **OPTION B, explicitly NOT ADOPTED** (`06-DECISIONS-LOG.md` 2026-07-29). ⇒ the measurement lives on in `#24-leadpolicy`; this slug exists only so the mistake is findable. See `08-MISTAKES.md` 2026-09-13.
- [ ] ⬇ `#26-healmap-lavaridge` — **DOWNGRADED 2026-09-12: a frame-cost, NOT a run-killer, and its “obvious” fix is a NO-OP.** ⛔ (1) `_training_area_heal_map()`'s ROUTE112/FIERY_PATH rows are **DEAD KEYS** — all 3 callers key off `TRAINING_GRASS`, which contains neither map (verified: 0 entries each). The real caller is a LITERAL, `story_mode.py:4271` `heal_in_pokemon_center(PokemonCenter.LavaridgeTown)` in the Flannery segment. ⇒ the previously recommended “make it CONSULT `NO_RETURN_GROUNDS`” would change NOTHING. ⛔ (2) IT RECOVERS: the derail re-plans via Jagged Pass and reaches Lavaridge anyway, ~3,000 frames + 1 derail slot — a careless fix could BREAK a working recovery. ⛔ (3) THE REPLACEMENT IS **DISPUTED**: my `calculate_path` probe says Fallarbor OK / Mauville FAIL; a decomp-level BFS says Mauville 145 steps (Rock Smash) and Fallarbor needs **Go-Goggles**, which are awarded WITH Flannery's badge — i.e. probably unavailable in the pre-Flannery window when this fires. Both instruments reproduce the one control we have. ⇒ **UNRESOLVED; change nothing yet.** **DECISIVE TEST (named, not run):** drive `_navigate_riding_out` — the instrument the bot ACTUALLY uses, which crosses warps — from `ROUTE112 (11,36)` to each candidate door on a PRE-FLANNERY save. ⚠ Also measured: 33 of 269 landing tiles may have NO reachable centre, and the heal map is keyed by MAP not TILE, so it cannot express that. Full evidence: `07-CHANGELOG.md` 2026-09-12 (night).
- [x] ⭐ `#24-pass2triage` — **CLOSED 2026-09-16: all eleven findings are resolved** (ten fixed, one — (a) — already done by an earlier commit). It SPAWNED `#26-victoryroadgap` and sharpened `#24-e4postbattlestall`; those are separate OPEN items, not remnants of this one. ⛔ **EVERYTHING FROM “REMAINING, each verified by the auditor” ONWARD IS SUPERSEDED HISTORY, KEPT VERBATIM — do NOT action it.** *(A Tier 1 reviewer flagged that a skimmer 2,000 characters into this bullet would hit that list and read it as live orders.)* Ready to archive. — **NEW 2026-09-16. AN ADVERSARIAL COLD-START AUDIT RETURNED 17 FINDINGS; THE THREE THAT WOULD MISLEAD A FRESH SESSION ARE FIXED, THESE ARE NOT.** Fixed already: the post-victory stall is a HANG not a frame cost (4/4 runs), §G''s `calculate_path` rebuttal is RETRACTED as unsupported, and the post-victory saves that §D'' said did not exist are now PINNED (`post_sidney_door_open.ss1`, `_b.ss1`). ✅✅ **TEN OF THE ELEVEN ARE DONE (2026-09-16, second session). ONLY (h) REMAINS, AND IT IS NOW A *MEASUREMENT* RATHER THAN AN EDIT.** ⛔ (a) WAS ALREADY DONE BEFORE I STARTED — commit `6fc6b1bf` added the `07-CHANGELOG` entry the item says is missing, so this very list was commanding work that had shipped; I verified reality before acting, which is the only reason it was not redone (P5). DONE: (b) the `KI-101` STATE cell's unmarked “NOT PROMOTED” is now a dated retraction; (c) the 3,600 budget → the block now quotes NO limit at all, because `lint_docs.py:102` says 4,400 and a LIMIT drifts exactly like a COUNT; (d) the second “(LATEST)” drift figure and the “FORK IS FROZEN” directive are retired (`promote.py --check` re-measured: **drift 0**); (e) the retracted `KI-96` repro no longer issues orders; (f) all three wrong `story_mode.py` citations replaced by the SYMBOL (`probe_stale_citations.py`'s own lesson: a bare `file.py:NNN` is unverifiable by construction — `:5003` was a `seafloor_cavern` import, `:4865` a Tate&Liza dict); (g) **the instrument is fixed and IT FOUND SOMETHING** — see `#26-victoryroadgap`; (i) 02-ARCHITECTURE said 19 story modules (there are 24) and documented neither `victory_road.py` nor `pokemon_league.py` — both now written up; (j) HOW TO RUN has a §Ch24 block; (k) `battle_frames` was the WAIT loop's counter and read 0 beside a 24,576-frame fight — the wait is now `frames_waited_for_battle_end` and `battle_frames` is stamped from `on_battle_started`. ⛔ **(h) IS NOT AN EDIT — IT IS UNRESOLVED.** *(The item below claimed the harness value was right and the note wrong.)* The note says the entry auto-walk ends at **(6,7)**; the drive reads **(6,11)**; **all three sources over-claimed**, because the drive samples the tile the instant `wait_until_truly_controllable` returns — and that function also returns on TIMEOUT — so (6,11) is equally consistent with the walk being IN FLIGHT. ‼ A one-frame sample of a moving player is not a landing. ✅✅ **RESOLVED THE SAME DAY BY THE 6-ANGLE RECON — AND IT IS OUR WARNING THAT WAS WRONG, NOT THE NOTE.** Both numbers are correct readings at different instants of ONE six-step scripted walk: the entry warp is **(6,13)**, the entry script runs `Common_Movement_WalkUp6`, 13−6 = **7** ⇒ the auto-walk END tile really is **(6,7)**, and **(6,11)** is 13−2 = exactly TWO steps in. ⭐ **THE DISCRIMINATOR WAS ALREADY IN OUR OWN LOG:** the same drive recorded `elite4_state_in_room = 0`, and `setvar VAR_ELITE_4_STATE, 1` runs only AFTER `WalkInCloseDoor` returns ⇒ at the instant (6,11) was sampled the auto-walk had **provably** not finished. ⇒ **retire the claim “(6,7) is WRONG”; KEEP the operational rule** (read the position back, never hardcode), which is right for a different reason — rule 4, and the probe already obeys it by reading `get_map_objects()`. —— the original list of eleven, kept verbatim: **REMAINING, each verified by the auditor against the tools/code and NOT yet actioned:** (a) the KI-101 **promotion has no `07-CHANGELOG` entry** and the changelog's last words still say NOT PROMOTED — DoD step 3 skipped, and the file is append-only so the fix is a NEW entry; (b) `04-HANDOFF:385`'s STATE cell still carries an UNMARKED “NOT PROMOTED” under its own “IS PROMOTED” headline — the sixth instance, and `#24-promotedpairgate`'s own live test case; (c) `04-HANDOFF:164` quotes a **3,600** line budget for 03 when `lint_docs.py` says **4,400** — a cold reader concludes the file is 600 lines over a commit-blocking cap and starts archiving; (d) `:855` carries a SECOND “(LATEST)” drift figure — a stale one; ⛔ the digit is deliberately not reprinted here, run `promote.py --check` — plus a standing “THE FORK IS FROZEN” directive from a batch that ended days ago; (e) `:837` still commands the `KI-96` repro the banner explicitly retracted at `:42`; (f) three wrong `story_mode.py` citations INSIDE the live `➡➡➡` line (`:5003`, `:5003-5058`, `:4865` — the real insertion point is after `:5130`); (g) the “30% reach the League” headline counts the OUTDOOR Ever Grande map, which the instrument's own comment says must NOT count, and its cumulative row is an assumed-order roll-up rather than a `seen_maps` test; (h) `§G'` lists `(6,7)` as a “measured fact” while `story_harness.py:15835` records the landing as **(6,11)** and says DO NOT TRUST THE RESEARCHED COORDINATE; (i) `02-ARCHITECTURE.md` says 19 story modules (there are 24) and **never mentions `pokemon_league.py` or §Ch24 at all**; (j) HOW TO RUN has no command for ANY of this session's §Ch24 work; (k) `R battle_frames = 0` is printed under `ACCEPTANCE: PASS` while the same log shows ~24,576 frames of battle. ⛔ **DO NOT BULK-FIX THESE BLIND** — each is a doc claim with a pair somewhere else; fix one, re-run Tier 0, move on. Full audit reasoning with both-halves quotes is in `07-CHANGELOG.md` 2026-09-16 (second pass).
- [x] ⭐ `#24-promotedpairgate` — ✅✅ **DONE 2026-09-16: `probe_promoted_pair.py` SHIPS AS GATE #63 *(⚠ **STALE LABEL, corrected 2026-09-17**: it carries NO `# --- #N` header in `run_gates.py` and sits at list position **48**. The `# --- #63` header belongs to `probe_retraction_coverage.py`, added 2026-09-17 after `#62`. The gate itself is unaffected — only this number is wrong.)*, ENFORCING, 19 FAULT ARMS — AND IT FOUND AN 8TH INSTANCE ON ITS FIRST LIVE RUN** (`04-HANDOFF.md:314` read *“`KI-95`: … sandbox-only, unpromoted”* against that KI's own **PROMOTED 2026-09-07** header, nine days stale; fixed, gate now 0). ⭐ **THE ITEM'S OWN CONSTRAINT WAS HONOURED:** the line-scoped design this entry refutes was NOT built — the fix is the BOUNDED-RADIUS primitive `probe_drift_restatement.py` already owns, so the KI mention and the contradicting phrase must be within ±300 chars of EACH OTHER. An arm proves it: at line scope (10,000) the mega-line fires, at clause scope it does not ⇒ the window, not luck, is the discriminator. The retraction exemption is kept and armed. ‼ **TWO FALSE POSITIVES WERE REMOVED BY PRINCIPLED SCOPING, NOT WORD-LIST TUNING** (self-declared MIXED headers are out of scope; a status phrase belongs to its NEAREST KI) — and ⛔ **the first such fix introduced a FALSE NEGATIVE that killed the true positive** (`PARTIAL` swallowed “PARTIALLY ARCHIVED”, dropping KI-95 from scope), caught in the same run and now pinned by its own arm. ⚠ **SCOPE, PLAINLY:** a WORD-LEVEL check between two files; it cannot tell you a KI is really fixed, only that the two documents do not contradict each other. —— the original brief: **WRITE THE GATE; PROSE HAS FAILED FIVE TIMES IN ONE SESSION.** Every break is the same shape: a fact lives in THREE places (a KI header, the handoff STATE row, and the handoff BANNER), an increment updates the two it is already editing, and the BANNER — the half a cold reader meets FIRST, and the half it ACTS on — keeps the superseded claim. Caught each time by the diff advisory or a Tier 2 audit, i.e. by cost, never by a check. ⭐ **PROPOSED CHECK (narrow on purpose):** for every `KI-\d+` whose `05-KNOWN-ISSUES.md` header contains PROMOTED/FIXED/CLOSED, no line in `04-HANDOFF.md` mentioning that same KI may contain NOT PROMOTED / STILL OPEN / AWAITING unless it is inside a dated retraction marker. ⛔ **FAULT-TEST IT BOTH WAYS** — it must fire on today's real defect (KI-101 header PROMOTED vs banner NOT PROMOTED) and must NOT fire on the dated `*(This clause read ...)*` retractions this file is full of, or it becomes the noisy gate CLAUDE.md rates worse than none. `CLAUDE.md` rule 6: a rule already broken twice is evidence that prose failed. ⛔⛔ **BUT THE PROPOSED SHAPE ABOVE IS ALREADY REFUTED — DRY-RUN IT BEFORE BUILDING IT, AND DO NOT BUILD IT LINE-GRANULAR.** I ran the check as a one-off on 2026-09-16: it produced **6 findings, all FALSE POSITIVES**. Every one came from `04-HANDOFF.md:386`, where the phrase “the two drifting FILES are NOT promoted” sits on the same line as six unrelated `KI-` numbers — this file's lines run to thousands of characters and carry dozens of independent facts, so *“a line mentioning KI-X that also contains NOT PROMOTED” is a meaningless conjunction here.* ⇒ the check must be **CLAUSE-scoped** (sentence or marker-delimited span), never line-scoped. ✅ **TWO PARTS OF THE DESIGN SURVIVED AND ARE WORTH KEEPING:** the retraction exemption did real work — it correctly suppressed **35** would-be false positives on this project's dated `*(This clause read …)*` style, so it is REQUIRED rather than decorative; and the dry run DID surface a genuine stale claim (line 386's “nothing parked MID-TASK / two files unpromoted / a batch is running”, all three false) — which the line-granular version then BURIED among its own noise. ‼ That is the lesson to carry: **a gate that finds a real defect and six false ones has not found the defect.** ⭐⭐ **AND THE SECOND DRY RUN SETTLED IT QUANTITATIVELY:** after I FIXED the real defect at line 386 — i.e. after the document got strictly MORE accurate — the check's findings went **6 → 23**, with **20 of the 23 coming from ONE line** (`:145`, the mega-line YOU-ARE-HERE history block). ⇒ **the metric tracks LINE LENGTH, not correctness.** A measure that gets WORSE when the thing it measures gets BETTER is measuring the wrong quantity, and no amount of tuning the word list fixes that. Whoever builds this must scope to a CLAUSE (sentence, or a `*(…)*` / `——` delimited span) and re-run this dry run as the acceptance test: it must find line 386's defect class with ZERO hits on `:145`.
- [~] ⭐ `#24-e4postbattlestall` — ⚠ **AUDIT STATUS, STATED HONESTLY: TWO full Tier 2 cold-start rounds were run on 2026-09-16; a THIRD was NOT.** Round 2 found three defects that round 1 missed (a citation ~1,335 lines off, a stale “60-SECOND VERSION” ladder, and a HOW-TO-RUN block a session behind its own banner), so **do not assume these docs are audit-clean** — CLAUDE.md's own rule is that two clean audits in a row would not retire the tier either, because agreement is not a confidence signal. Round 3's fixes were verified MECHANICALLY (8 checks: the symbol citation landed, no live `:3779-3795` claim survives, the ladder says only §Ch24 remains, both new driver commands are in HOW TO RUN beside the leg-vs-probe fixture warning, and exactly one `➡➡➡` marker remains) but NOT by a fresh cold-start agent. ⇒ the cheap next check is one more Tier 2 round. ‼ **WHAT REMAINS: THE WIRING, NOT A MEASUREMENT** — put the proven sequence into `modules/story/pokemon_league.py` as a real leg (it lives in a PROBE today) and add a Segment 24 dispatch. ⛔⛔⛔ **AND START THE LEG FROM `post_ch24_atdoor.ss1` — GRADING IT FROM `post_sidney_door_open.ss1` IS VACUOUS, MEASURED:** a Tier 2 cold-start auditor read the flag out of both fixtures offline (positive control `LANDMARK_POKEMON_LEAGUE` True on both, so the reader was not blind) — `post_ch24_atdoor.ss1` has `DEFEATED_ELITE_4_SIDNEY=**False**`, `post_sidney_door_open.ss1` has it **`True` BEFORE A FRAME RUNS**. A leg graded on that flag from the post-victory save PASSES WITHOUT DOING ANYTHING. ‼ **The cheap fixture is the trap** — it is ~4,000 frames against `ch24probe`'s ~29,000, so cycle-time pressure points straight at it. It is correct for the DISMISS and DOOR probes (they grade on control and position, never the flag) and wrong for the leg. and note **only SIDNEY's room is measured** — Phoebe/Glacia/Drake are an INFERENCE from byte-identical ROM layouts plus a shared victory script. ✅ **EVERYTHING ELSE IS DONE AND DRIVEN:** ✅✅✅ **ANSWERED BY MEASUREMENT, 2026-09-16 — `B` CLEARS THE BOX AND CONTROL COMES BACK, AND THE CONTROL ARM PROVES THE BOX DOES NOT SELF-CLEAR.** New probe `--driver e4dismiss` from the PINNED `post_sidney_door_open.ss1` (md5 `6231369647f8`), which IS the stall state, so the whole experiment costs SECONDS instead of the ~29,000 frames `ch24probe` needs to reach the same moment. Predictions were filed and committed BEFORE the run (`ai-research-notes/2026-09-16-e4dismiss-PREDICTIONS.md`, graded in the same file). **TREATMENT** `controllable_after=True` after **297** frames, `prompts_cleared=2`, `script_active_after=False`. **CONTROL (`POKEBOT_E4DISMISS_FAULT_NOPRESS=1`, presses nothing)** `controllable_after=False`, `prompts_cleared=0`, printer still `(True,'WaitForButton')`, script still active, **having burned its FULL 2,600-frame budget — 1.4× the 1,802 frames the real stall lasted.** Both arms `ACCEPTANCE: PASS`, because they are graded by OPPOSITE expectations on the same reading. Evidence committed: `tools/story-dev/evidence/2026-09-16-e4dismiss-{TREATMENT,CONTROL-NOPRESS,TREATMENT-fixtureB}.stdout.txt`. ⭐ The probe also carries a PREMISE conjunct that FAILS on a clean overworld save, so a pass cannot be vacuous. ❌ **ONE PREDICTION WAS WRONG AND IT WAS MY INSTRUMENT:** I predicted 1-12 presses and measured 50, because `presses_issued` counts duty-cycle ticks where the GATE was true, not prompts the game consumed — rule 7 in my own probe, while writing about rule 7. Fixed by adding `prompts_cleared` (WaitForButton→else transitions): **2**, consistent with the decomp's 3 for Sidney given the fixture is captured mid-sequence. ⚠ **HONEST SCOPE (rule 8):** the `_b` fixture returns IDENTICAL numbers, but it is a second capture of the SAME parked moment replayed deterministically — a byte-level sanity check, **not a replication**. The phenomenon is measured in ONE room against ONE trainer. ⛔ **STILL NOT ESTABLISHED:** that stepping on `(6,2)` warps; that Phoebe/Glacia/Drake behave the same (inferred from byte-identical ROM layouts, not measured); and that the EXISTING helpers clear it — this probe pressed B on its own gate, which proves the GAME accepts B here (the load-bearing half), but the one-line insertion still has to be driven.  ✅✅✅ **AND `calculate_path` ROUTES TO THE DOOR AFTER ALL — MEASURED 2026-09-16, WITH A POSITIVE CONTROL, A NEGATIVE CONTROL AND A DISCRIMINATOR.** From the post-dismiss state, `calculate_path(SIDNEYS_ROOM (6,6) → (6,2))` returns **6 waypoints**: `SIDNEYS_ROOM (5,6)→(5,5)→(5,4)→(5,3)→(6,3)` then **`HALL1 (5,12)`**. ⇒ it routes **AROUND the standing defeated trainer at (6,5)** via the x=5 column, and then **FOLLOWS THE WARP into Hall1**, landing on exactly the tile the warp backbone predicts. **CONTROLS:** `(5,6)` (a plainly walkable neighbour) → OK 1 waypoint, so the planner works; `(0,0)` (a wall) → **REFUSED** `PathFindingError`, so it is not saying yes to everything. ⭐⭐ **AND THE DISCRIMINATOR NAILS THE MECHANISM:** `(6,1)` — the door's OTHER tile, adjacent to (6,2), identical in both grids, but **not a warp** — is **REFUSED**. The only difference between them is `warps_to`, so `map_path.py:841`'s destination-warp exemption (`tile == destination_tile and tile.warps_to`) is demonstrably what is operating, not general leniency about that corner of the room. ⛔⛔ **THIS REFUTES §G''S BFS PREMISE.** The leg-1 spec says leg 1 needs *“a short BFS over `_live_collision_grid` plus `get_map_objects()`, because the planner cannot see the door”*. It can — `KI-74` blinds the COLLISION GRID, but `warps_to` comes from the static warp-event table, which `KI-74` does not touch. ⇒ **do not build the BFS.** ⚠ **BUT THIS IS NECESSARY, NOT SUFFICIENT:** a `calculate_path` OK is not proof the DRIVEN navigator can walk it — that is `KI-48`, and it still owes a drive. Evidence: `tools/story-dev/evidence/2026-09-16-e4dismiss-TREATMENT.stdout.txt`. ✅✅✅ **AND THE FULL REPEATING UNIT IS DRIVEN — `room → hall → NEXT ROOM` (2026-09-16).** ‼ **A USER NOTE CAUGHT A SCOPING ERROR IN MY OWN SPEC:** the gauntlet's unit is not “leave the room” — between every pair of E4 rooms there is a CORRIDOR the bot must walk, with a second door at its far end. Every measurement before this stopped half-way, at the hall landing. ✅ **THE GEOMETRY IS NOW MEASURED FROM OUR OWN MAP DATA** (`probe_e4_halls.py`, NEW; controls hold — every forward door reads collision 0, every corner reads 1): HALL5/1/2/3 are **10 steps** each, `(5,12)→(5,2)`; ⛔ **HALL4, DRAKE→CHAMPION, IS 31 STEPS**, `(5,33)→(5,2)` — the user's “longer path to the champions room”, CONFIRMED against our data and agreeing with the live 10-waypoint reading out of HALL1. ‼‼ **AND THE HALL NUMBERING IS *NOT* THE WALKING ORDER: HALL5 IS THE FIRST HALL** (lobby→Sidney), then 1→2→3→4 — a leg that iterates `HALL1..HALL5` walks the gauntlet in the wrong order. ⭐⭐ **DRIVEN** (`POKEBOT_E4EXIT_CONTINUE=1`): `SIDNEY (6,6)` —dismiss **297f**→ exit door —**164f**→ `HALL1 (5,12)` —walk—**219f**→ **`PHOEBE (6,7)`**, `ELITE_4_STATE 1→2`, `battles=0`, `whiteouts=0`, and `can_continue_to_phoebe_6_6 = OK 1 waypoint` with the negative control still REFUSING. **~680 frames for a complete inter-room transition.** ⭐ `final_tile=(6,7)` is the THIRD independent confirmation of the auto-walk end tile and the first DIRECT one (sampled after a deliberate 240-frame settle) ⇒ the `(6,7)` vs `(6,11)` question is CLOSED, in the note's favour. ⭐ `ELITE_4_STATE==2` is load-bearing, not decoration: it is Phoebe's ENTRY script having run, which is what fires the auto-walk AND the entry seal; a `1` would mean an UNSEALED room. ⛔ **NOT SHOWN: Phoebe is never fought** (the run ends beside her), only the SIDNEY→PHOEBE instance is driven, and ⛔⛔ **the LAST transition is not this shape** — HALL4 is 31 steps and the Champion's room has NO pre-battle window, it `goto`s straight into Wallace's fight. —— ✅✅✅ **AND THE WALK IS DRIVEN — `KI-48` DOES NOT BITE AT THIS DOOR.** `--driver e4exit` (new) dismisses and then exits via the SHIPPED `early_game._pass_through_door((6,2), …)`: **TREATMENT** ends `EVER_GRANDE_CITY_HALL1 (5,12)` — **the exact tile the warp backbone predicted from `map.json`, derived independently before any of this ran** — in `walk_frames=164`, `battles=0`, `whiteouts=0`, and a REAL `calculate_path` off the landing tile to the hall's north door returns **OK 10 waypoints**. **CONTROL (`POKEBOT_E4EXIT_FAULT_NOWALK=1`)** dismisses identically and skips the walk: ends `SIDNEYS_ROOM (6,6)`, `arrived_in_hall1=False`, and its continuation path is **REFUSED** — so the continuation check is not a formality that passes wherever you stand (the §Ch15/§Ch18/§Ch19 “passed while stranded” shape, actively excluded). Evidence `evidence/2026-09-16-e4exit-{TREATMENT,CONTROL-NOWALK}.stdout.txt`; predictions filed first in `ai-research-notes/2026-09-16-e4exit-PREDICTIONS.md`. ⭐⭐ **⇒ LEG 1'S MECHANICS ARE A COMPOSITION OF HELPERS THAT ALREADY SHIP. NO NEW MACHINERY, AND NO BFS.** ⛔ **WHAT REMAINS FOR THE ITEM:** this was proven in a PROBE, not wired into `pokemon_league.py` as a leg, and only SIDNEY's room is measured — Phoebe/Glacia/Drake are an INFERENCE from byte-identical ROM layouts plus a shared victory script. —— the history that led here:  — **NEW 2026-09-16, OBSERVED LIVE.** After Sidney is beaten the bot stalls in the post-battle return: `STUCK-OW cb=ReturnFromBattleToOverworld instr=BattleScript_PayDayMoneyAndPickUpItems textprinter=active=True state=TextPrinterState.WaitForButton`, then `NO-PROGRESS x1200` with the signature naming `Ch24ProbeMode.run` — i.e. DURING the driver, not after it. ⛔⛔ **CORRECTED 2026-09-16 (second-pass audit) — IT IS A HANG, AND IT IS LEG 1's FIRST BLOCKER.** *(This clause read “It RECOVERED … so this is a FRAME COST and not yet a hang”.)* **ALL FOUR** drives from this fixture end `HANG CONFIRMED (20000 frames no progress)` with `final mode=Manual` — P24DOOR-KI74-LIVE, KI101-ARM-ON, KI101-CONSUMPTION-VERDICT and KI101-CUSTOMBUILD-VERIFY. **4 for 4; none recovered.** The readings ARE taken and `ACCEPTANCE: PASS` is honest — that acceptance only asserts REACHING and MEASURING, never that the bot can continue — so the PASS line hid a total loss of control. ‼ **AND “~1,200 frames” WAS NEVER A DURATION:** `NO-PROGRESS x1200` is the first rung of an escalating counter ladder (x1200, x3000, x8000, x15000). I read a THRESHOLD as a MEASUREMENT. The real shape: `wait_until_truly_controllable` (`early_game.py:1257`) is bounded at `timeout_frames=1800` and **returns silently on timeout with no success signal**; control was retaken at f27174 and dropped at f28976 = 27174 + 1800 EXACTLY. It did not recover — it hit its bound, with `textprinter=active=True state=WaitForButton` still on screen. ⇒ **§G' IS WRONG THAT “ONLY THE WALK IS UNBUILT”: regaining control after a victory is also unbuilt, and it is what actually stops every run today.** — ⛔ but §Ch24 has FIVE such victories in a ONE-WAY gauntlet, and the note's trap D2 predicted exactly this: the victory script sets the flag, then runs a 32-frame movement, THEN a `msgbox`, so the flag is true while a message is still pending. ⭐ A sequencer must dismiss on `get_text_printer(0).state == WaitForButton`, never on a frame count. Evidence: `tools/story-dev/evidence/2026-09-16-ch24probe-P24DOOR-KI74-LIVE.stdout.txt`. ⛔⛔ **THIRD CORRECTION, 2026-09-16 (second session) — THE “4 FOR 4 HANG CONFIRMED” EVIDENCE IS WITHDRAWN; THE CONCLUSION IT SUPPORTED SURVIVES ON BETTER EVIDENCE.** *(The clause above reads “ALL FOUR drives … end `HANG CONFIRMED` … 4 for 4; none recovered” and treats that as the finding.)* ‼ **`HANG CONFIRMED` AFTER `ACCEPTANCE:` IS WHAT *EVERY* PROBE DRIVER DOES — MEASURED ACROSS THE TREE: 51 of 53 evidence files containing `HANG CONFIRMED` also carry an `ACCEPTANCE:` line (43 PASS + 8 FAIL), and the drop→HANG interval is exactly 20,000 frames in every sampled case, including drivers with nothing to do with §Ch24.** ‼ **AND “4 FOR 4” WAS AT MOST *TWO* TRAJECTORIES**: three of the four logs are frame-identical (drop f26821, hang f46821, byte-identical party strings) — session-discipline rule 8, a determinism check replayed is not a replication. `story_harness.py:19727-19741` fires it on 20,000 idle frames unless `context.message` contains “end of built content” — which only the STORY bot sets — so a driver that finishes and drops to Manual ALWAYS ends this way. `04-HANDOFF`'s own HOW TO RUN block has said so for weeks: *“A driver keeps running after it prints ACCEPTANCE … logging ‘HANG CONFIRMED’ on a run that SUCCEEDED. Read the `ACCEPTANCE:` line, not the last line.”* ⇒ counting it 4 times counted the instrument, not the bot — the SAME shape as reading `NO-PROGRESS x1200` as a duration, which this item already records. ⭐⭐ **THE DEFECT IS REAL AND HERE IS THE EVIDENCE THAT ACTUALLY SHOWS IT** — the generator stack, printed by the harness's own wedge dump INSIDE the driver (`evidence/2026-09-16-ch24probe-P24DOOR-KI74-LIVE.stdout.txt`): `f28374: gen -> Ch24ProbeMode.run @ story_harness.py:16009` / `f28374: gen -> wait_until_truly_controllable @ early_game.py:1232`. Control was retaken f27174 and the wait returned f28976 — a delta of **1802**: its 1800-frame bound plus two frames of Manual teardown (one for the driver to reach its trailing `yield` after `set_manual_mode()`, one for the harness to clear the stack). *(This read “= 27174 + 1800 EXACTLY”; corrected 2026-09-16 by a recon angle that checked the subtraction. The conclusion is unaffected and in fact TIGHTER — but the wrong figure had been copied verbatim from the changelog into here.)* With `textprinter=active=True state=WaitForButton` on screen throughout. ⇒ **the bot sat in a wait that presses NOTHING BY DESIGN while a msgbox waited for a button, and the wait then returned SILENTLY as though it had succeeded** (`early_game.py:1257`, no success signal on timeout). That is leg 1's first blocker, and it is a CLASS defect: ⛔ **262 call sites** share that function — *(this read “~40”; **40 is the count of call sites lexically inside a LOOP**, which is where that figure came from. 303 grep lines = 262 `yield from` calls + 36 imports + 4 comments + 1 def)*. ⛔ **DO NOT “FIX” IT BY MAKING `wait_until_truly_controllable` PRESS A** without reading its docstring first — *“probing showed that mashing inputs at it only prolongs the flicker”* — and `early_game.py:3287` has a call site whose comment says it relies on the function pressing nothing. ⭐⭐ **AND THE FIX IS NOT NEW CODE — THREE HELPERS THAT ALREADY PRESS ON EXACTLY THIS GATE SHIP TODAY**, and two of them are ALREADY inserted before this very wait elsewhere (`early_game.py:3290`, `story_mode.py:3683`): `_wait_until_cutscene_over` (`early_game.py:639`, gate `script_running or is_waiting_for_input()` — **both conjuncts MEASURED true in the stall dump**), `_ride_out_scripted_scene("B")`, and `normalize_to_overworld()`. `modules/tasks.py:199 is_waiting_for_input()` is **the same predicate** as the log's `WaitForButton`, not merely similar (both read `sTextPrinters` 0x1B/0x1C, raw states 2/3). ⇒ the defect is better stated as *the probe called the press-NOTHING wait where a press-SOMETHING helper was required*; the fix is one line at one call site. ⛔⛔ **AND IT MUST PRESS `B`, NOT `A`** — the bot stands at (6,6) facing Sidney at (6,5) and his script is RE-TRIGGERABLE after defeat into another `MSGBOX_DEFAULT`, so an A-mash re-opens the box it just closed. `KI-93`'s own dismiss presses **B** (one frame in 12, `_KI93_DISMISS_PERIOD`); anything that copies it and presses A is copying it backwards. ⛔ **DO NOT BUILD ON ANY OF THIS YET** — no evidence file in the tree shows this msgbox EVER being dismissed by the bot; that is a decomp READ, not a drive. Full recon + the 3 refuters per claim: `ai-research-notes/2026-09-16-ch24-leg1-RECON-6-ANGLES.md` §0.
- [ ] ⬇ `#24-e4fixtureparty` — ⛔ **DOWNGRADED 2026-09-16, THE SAME DAY IT WAS FILED: THE PARTY WAS NOT THE CAUSE.** The five faints happened while the bot had **no working healing at all** — `KI-101`: both Full Restore attempts aimed at FAINTED Pokémon because the in-battle bag permutes the party and our target was computed before the menu opened. ⇒ re-measure survivability only AFTER `KI-101` is fixed; judging the fixture on a no-healing trajectory would retire a party that may be perfectly adequate. *(Original filing follows, and its DATA stands.)* **NEW 2026-09-16, MEASURED.** The pinned §Ch24 fixture `post_ch24_atdoor.ss1` carries **Sceptile L53 / Zigzagoon L19 / Swellow L48 / Wailord L47 / Mightyena L48 / Castform L36** — **NOT the L60 grind party** (`post_grind_L60.ss1` is a separate fixture). On this party, beating **Sidney alone left FIVE OF SIX FAINTED** (`Swellow 139/139` the only survivor). ⇒ with the gauntlet ONE-WAY and healing restricted to the BAG, four more fights on that party is not obviously survivable. ⛔ **DO NOT read this as “§Ch24 is impossible”** — it is one trajectory, and `#24-e4healing` step 2 (heal BETWEEN rooms) is precisely the untested mitigation. **THE DECISION IT FORCES:** which fixture §Ch24 is built against. Re-capturing the door-apron state from the L60 party is the obvious candidate and has not been costed.
- [x] ✅ `#24-hallwarpdisputed` — **SETTLED THE SAME DAY BY MEASUREMENT: A SIDESTEP DOES **NOT** WARP, AND THE PUNCH-LIST HALF WAS THE WRONG ONE.** Live arm (`POKEBOT_E4EXIT_SIDESTEP=1`): `SIDESTEP from ((16,5),(5,12)) -> (16,5)(4,12) warped=False` — the bot stood on the exact tile this file said would warp it back into the cleared room, and stayed in HALL1. ⭐ **TWO INDEPENDENT METHODS AGREE:** `probe_e4_halls.py` reads behaviour `'Normal'` (= `MB_NORMAL`, which `IsWarpMetatileBehavior` rejects) on **all 15 backward tiles across all five halls**, and the live step confirms the refusal. ‼ **THE PROVENANCE EXPLAINS THE ERROR:** the refuted half came from `get_map_data(...).warps`, a warp-**EVENT TABLE** — a tile can be a warp's DESTINATION without being able to TRIGGER one. Same class as reading a candidate list as an attempt. ⇒ **leg 1 may walk the hall normally; the “column-constrained, never sidestep” caution is RETIRED.** ⚠ Live step measured on HALL1 only; the other four share the behaviour reading. —— the original: **TWO OF OUR OWN DOCS CONTRADICT EACH OTHER ABOUT THE EXACT HALL §Ch24 LEG 1 WALKS.** `ai-research-notes/2026-09-04-ch24-LEAGUE-INTERIOR-ROUTING.md:139` says the halls' backward warps at (4,12)/(6,12) are **destination-only** — they sit on `MB_NORMAL`, which `IsWarpMetatileBehavior` rejects, so stepping on them never fires. `2026-09-07-ch24-elite-four-BUILD-SPEC.md:157` and this file say **a single sidestep in that hall warps you back into the cleared room**. ‼ **THE SECOND WAS DERIVED FROM `get_map_data(...).warps` — A WARP-*EVENT* TABLE, WHICH SAYS NOTHING ABOUT WHETHER A WARP FIRES.** A warp entry exists as an arrival destination whether or not its tile can trigger one. ⭐ **DECISIVE TEST:** from `HALL1 (5,12)` resolve the BEHAVIOUR byte for (4,12)/(6,12) via `_live_metatile_grid`, then step one tile west and log the map. ⛔ It matters because leg 1 walks that hall: “a lateral nudge silently undoes a cleared room” would force a much more defensive walk than a straight `_pass_through_door`. ⇒ until settled, treat the hall walk as COLUMN-CONSTRAINED and do not sidestep.
- [x] ✅✅ `#24-grindppstall` — **FIXED AND A/B-PROVEN 2026-09-17, AND THE SEVERITY WAS LOWER THAN I FILED IT: THE DEFECT WAS **HARNESS-ONLY**, NOT PRODUCTION.** ⛔ *(I filed this as “must be fixed before any long grind is trusted”, which implied production risk. It does not exist in production.)* `StoryMode.on_battle_started` (`story_mode.py:3477`) already installs **`SwapTrainBattleStrategy`** when `swap_train_active()`, and that class exists for exactly this case — its docstring says a lead that *“ran out of usable moves”* ROTATES *“rather than FLEE for zero XP (old behaviour)”* and *“the training loop then heals normally”*. **`Ch24GrindMode` is a HARNESS driver, not a `StoryMode`**, so it returned `StoryItemBattleStrategy()` unconditionally and silently inherited the parent's FLEE. ‼‼ **AND IT IS A RECURRENCE THE TREE HAD ALREADY WRITTEN UP:** `victory_road.py:3404` documents the IDENTICAL defect in `Ch23TrainMode` — *“the DRIVER NEVER INSTALLED SWAP-TRAINING”*. A second driver repeated it because the finding was recorded as PROSE IN A COMMENT rather than as shared code. ✅ **THE FIX:** `Ch24GrindMode.on_battle_started` now mirrors production's gate verbatim, including its `try/except`. **A/B, same fixture, same 90,000-frame budget:**
      BEFORE   15 Won / 50 RanAway   — 20 turn decisions: 5x Surf, 15x Waterfall, then 457 RunAway
      AFTER    38 Won /  0 RanAway   — 52 turn decisions, and the BENCH fights: Strength x4,
                                        Wing Attack x3, Take Down x3 alongside Wailord's water moves
  Wailord L60 → **L62** (STEP 1 completed, which never happened before); Mightyena +2,467 exp, Sceptile +1,097, Swellow +662 — the bench gains XP now. ⭐ **AND A HEAL DEMONSTRABLY FIRED:** Wailord used **Water Spout 6 times** having started that arm at **0/5 PP**, so PP was restored — the *“training loop then heals normally”* half of the docstring, observed. ⚠ Same fixture replayed, so a determinism check on the BEFORE arm; the AFTER arm is a genuine behaviour change. ✅ The failing arm is preserved as `grind_stall_ppzero.ss1` + `probe_grind_stall_predicate.py`, so the regression is re-checkable without re-deriving it. ⇒ **the L60→L75 grind is now viable**, subject to `#24-fixturelineage` (that save still has no Ice Beam and no Fly).
- [x] ⭐ `#24-grindppstall` — —— the original filing:  — **NEW 2026-09-17. THE `ch24grind` STALL IS DIAGNOSED END TO END, AND IT IS THE *THIRD* ROUTE INTO ONE PREDICATE.** The stall state is now PINNED (`grind_stall_ppzero.ss1`, md5 `9ca6c133e297`) and slot 0 tells the whole story:
      Wailord L61 225/309   Dive:10/10   Surf:0/15   Water Spout:0/5   Waterfall:0/15
  **Every ATTACKING move is at ZERO PP and the only move left is `Dive`, which is BANNED** (`context.config.battle.banned_moves`, 38 entries — Dive/Fly/Dig are banned as two-turn/field moves). ⇒ `_util.py:255-266` scores a 0-PP move `-1` **and** a banned move `-1`, so `max_strength <= 0` and `get_strongest_move_against` **returns None** ⇒ the strategy cannot pick a move and **FLEES** — and the flee path never triggers `train_team`'s *“heal on HP **or PP** dip”*, so PP is never restored. **Encounter → flee → encounter → flee, for ever, zero EXP.** ⭐ **THE “15 WINS” IS THE PP BUDGET, NOT A MAGIC NUMBER:** Surf 15 + Waterfall 15 + Water Spout 5 = **35 PP** ≈ 15 battles × ~2 moves per battle. ‼‼ **AND THIS IS THE SAME SINGLE POINT OF FAILURE AS `#24-ghostzerodamage`.** One predicate, `max_strength <= 0 → None`, is reachable three ways: **(1) TYPE IMMUNITY** (Normal/Fighting into a Ghost — Phoebe), **(2) PP EXHAUSTION** (this), **(3) A BANNED MOVE** being the only one left. The two consumers then diverge: `_fight_on` falls through to move SLOT 0 (a 0-damage loop), and the LevelUp/training path FLEES (this infinite loop). ⇒ **the fix belongs at the predicate's CONSUMERS: `max_strength <= 0` must mean “I cannot fight — heal / rotate / recover”, never “flee and retry the same situation for ever”.** ⛔ **DO NOT FIX IT BY UNBANNING DIVE** — the ban is deliberate (two-turn moves) and unbanning it would only move the wall to the next empty-PP state. ✅✅ **THE PREDICATE IS NOW *MEASURED*, NOT INFERRED, AND THE FAILING ARM IS AN INSTRUMENT:** `probe_grind_stall_predicate.py` (NEW) loads the pinned stall save and reproduces `_util.py`'s scoring on the real party — **all four of the trainee's moves score `-1`, for TWO different reasons** (`Dive 10/10 BANNED`, `Surf 0/15`, `Water Spout 0/5`, `Waterfall 0/15`) ⇒ `max = -1` ⇒ returns **None**. ⭐ **ITS CONTROL FIRES:** the same computation on a healthy mon from the SAME party returns `max=1` ⇒ not None, so the probe is not reporting None for any input. Exit 0. ‼ **A PP-BUDGET NOTE, WITH ITS MECHANISM CORRECTED (2026-09-17):** this lineage carries **Water Spout (5 PP)** where the §Ch24 fixture carries **Ice Beam (10 PP)**, so it has less PP to grind on. ⛔ *(This read “the grind made itself worse: its own level-up learning replaced Ice Beam with Water Spout” — **FALSE**. The ancestor `post_training.ss1` already had Water Spout and no Ice Beam, so the lineages diverged before it; Water Spout is Wailord's natural L44 move. The bot in fact DECLINES level-up moves — Wailord crossed L52 Amnesia and L59 Hydro Pump in the L47→L60 grind and kept all four.)* ✅ **A/B TARGET EXISTS:** `grind_stall_ppzero.ss1`. A working fix must make the bot RECOVER from that save (heal, restoring PP) rather than flee; the failing arm is the save as it stands. ⚠ Reproduced deterministically (15 Won / 50 RanAway in a bounded 90,000-frame run) — same fixture replayed, so a determinism check, not an independent replication.
- [x] ✅✅✅ `#24-learnhmcoverage` — **NEW AND FIXED 2026-09-17, PROVEN BY A *LIVE* A/B. THE MOVE-LEARNING POLICY SPENT THE TEAM'S ONLY ICE MOVE ON A FOURTH WATER MOVE, BECAUSE ITS TYPE CENSUS COULD NOT SEE HMs.**
  ⭐ **THE DEFECT.** `which_move_should_be_replaced` (`story_mode.py`) states a good rule — *“if the new move's type is ALREADY covered, only overwrite a WEAKER same-type move … otherwise DECLINE”* — but built its census from `damaging_slots`, **which EXCLUDES HM moves**. Wailord's three Water moves are all HMs (Dive/HM08, Surf/HM03, Waterfall/HM07), so the census read `[Ice]`, **Hydro Pump (Water) looked like a type the party LACKED**, and the policy “freed the weakest slot to gain coverage” — discarding **Ice Beam**, the move a **~700,000-frame Abandoned Ship round trip** was taken to get, and the one the change analysis says the party LOSES to Drake without. Ice is **4x** on Salamence, Altaria and Flygon.
  ‼‼ **ONE MECHANISM EXPLAINS THE OPPOSITE OBSERVATION TOO, WHICH IS WHY IT IS THE RIGHT ONE.** On the `post_grind_L60` lineage that slot held **Water Spout** — a TM, so non-HM. The census read `[Water]`, Hydro Pump was REDUNDANT and weaker (150 vs 120), and the policy correctly **DECLINED**, keeping all four moves across the very same level. Same code, same level, opposite outcome, decided entirely by which slot happened to be replaceable. ⇒ that is the observation I generalised into *“the bot DECLINES level-up moves”* — now RETRACTED; see `#24-fixturelineage`.
  ✅ **THE FIX:** coverage is counted over **every damaging move, HMs included**; the REPLACEABLE set is unchanged. *Replaceability and coverage are different questions — you cannot overwrite an HM, but the Pokémon still KNOWS it, and coverage is about what it can DO.*
  ⭐⭐ **PROVEN BY A LIVE A/B, NOT AN OFFLINE ONE — same level, same lineage, only the fix differs:**
      BEFORE  post_e4grind_L59.ss1  L59  Dive, Surf, Hydro Pump, Waterfall   ⛔ Ice Beam LOST
      AFTER   post_e4ice_L59.ss1    L59  Dive, Surf, Ice Beam,   Waterfall   ✅ Ice Beam INTACT
  ✅ Plus gate **#63** `probe_learn_hm_coverage.py`, which runs the policy against the **REAL** pinned Wailord and the **REAL** Hydro Pump (not fakes — twice today a hand-built probe fixture was wrong while its subject was right). Three arms: the redundant Water move is DECLINED; a genuine new type (Thunderbolt) is still ACCEPTED; a same-type upgrade (Hyper Beam over Take Down) still lands — so the widened census did not turn the policy into “always decline”.
  ⛔ **THE LOSS IS PERMANENT ON THE OLD LINEAGE** — USER RULING 2026-09-17: TM13 is a one-time pickup, is sold nowhere, and the Move Reminder only teaches level-up moves. ⇒ re-grinding from **`post_e4grind_L57.ss1`** (the last checkpoint whose Wailord still has Ice Beam) was the remedy, 18 levels rather than 28 with no ship trip — ✅✅ **AND IT IS DONE: `post_e4ice_FINAL.ss1` (md5 `ebfafa71fa99`), all four battlers L75, 1,353 battles, 0 whiteouts, Wailord verified BY RELOAD as `Dive, Surf, ICE BEAM, Waterfall`.** ⛔ DO NOT RE-RUN THE GRIND. See `06-DECISIONS-LOG.md` 2026-09-17 (second).
- [x] ✅✅ `#24-flymaptype` — **NEW AND FIXED 2026-09-17. `fly_to_destination` HAD NO GUARD FOR “DOES THIS MAP ALLOW FLY AT ALL”, AND THE §Ch24 PARTY IS PARKED IN A CAVE.**
  ⭐ **HOW IT SURFACED:** the finished gauntlet party `post_e4ice_FINAL.ss1` sits at **VICTORY_ROAD_1F (15,39)** — the grind tile — and the plan for reaching the League door was *“it is ONE Fly away”*. It is not, **from there**: that map is `map_type=Underground`, and Gen 3 refuses Fly on it. ⇒ **the chapter's FIRST MOVE is not a Fly — it is a WALK OUT of Victory Road to EVER_GRANDE_CITY**, and only then a Fly to `PokemonLeague`.
  ‼‼ **AND THE FUNCTION WOULD NOT HAVE SAID SO.** Its three guards (`pokemon_league.py:1226-1236`) are *knows Fly* / *`BADGE06_GET`* / *destination flag set*. **All three pass inside a cave**, so the failure happened in the field-move menu — far from the cause, with nothing naming it.
  ⭐ **THE ALLOW-LIST IS NOT “outdoors”, AND GUESSING THAT IS HOW I GOT IT WRONG FIRST.** VERIFIED at `src/overworld.c:1366-1375` `Overworld_MapTypeAllowsTeleportAndFly`: **ROUTE, TOWN, OCEAN_ROUTE, CITY — exactly four.** `Underground` (caves), `Indoor` and `Underwater` are all refused. My first check tested `map_type == "Indoor"` and therefore printed a cheerful **“✅ yes” for a cave** — a FALSE GREEN on the one fixture the question was asked about. The list is now encoded verbatim rather than paraphrased. *(Third time in one day a predicate of mine tested something narrower than the claim — see `08-MISTAKES.md`.)*
  ✅ **THE FIX:** a fourth guard that reads the current map type and REFUSES with a message naming the type, the tile, the decomp function and the remedy. ⛔ An UNREADABLE map type also refuses — an unknown is treated as NO, never as yes.
  ✅✅ **DRIVEN BOTH WAYS, on real fixtures:**
      ARM      post_e4ice_FINAL.ss1  (VICTORY_ROAD_1F, Underground)  → REFUSED in <3,000 frames,
               `missing=['R-FLYABLE','R-FLOWN','R-CONTINUE']`, `ACCEPTANCE: FAIL` — it refuses
               BEFORE taking R-FLYABLE, and does not hang in a menu
      CONTROL  post_ch24ready.ss1    (EVER_GRANDE_CITY, City)        → NOT refused; flies and
               `R arrived = ((0,8),(18,6))`, `moved=True`, `missing=[]`, `ACCEPTANCE: PASS`
  ⇒ the guard separates: it blocks the illegal case and is invisible to the legal one. ✅ `probe_fly_allowed_here.py` answers “can I Fly from here?” per fixture, for any future save.
- [x] ✅✅✅ `#24-leg0toleague` — **NEW AND DONE 2026-09-17. THE **L75** PARTY IS AT THE LEAGUE DOOR, AND LEG 2 NOW HAS A START STATE.** Fixture `post_ch24_atdoor_L75.ss1` (md5 `8b8cd907db09`), EVER_GRANDE_CITY **(18,6)**.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full entry, its evidence and any ⛔ warnings are there.
- [x] ✅✅✅ `#24-sidneyL75` — **NEW AND DONE 2026-09-17. THE FIRST ELITE FOUR FIGHT AT L75 IS WON, AND IT COST **15 HP**.** `--driver ch24probe` from the new `post_ch24_atdoor_L75.ss1`, `ACCEPTANCE: PASS`, all 6 readings, `missing=[]`, `battles=1`, `whiteouts=0`, `ELITE_4_STATE 0 → 1`.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full entry, its evidence and any ⛔ warnings are there.
- [x] ✅✅✅ `#24-phoebeL75` — **NEW AND DONE 2026-09-17. PHOEBE IS BEATEN AT L75, ROOMS 1→2 ARE DRIVEN AS ONE UNIT, AND ⭐ THE MEASUREMENT `#24-ghostreplacement` WAS BLOCKED ON IS IN HAND.**
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full entry, its evidence and any ⛔ warnings it carried are there.
- [x] ✅✅ `#24-doccontrolchars` — **NEW AND DONE 2026-09-17 (late). AN INVISIBLE BACKSPACE BYTE WAS SITTING IN A TRACKED DOCUMENT, AND A SWEEP FOUND A SECOND ONE THAT HAD BEEN THERE FOR WEEKS. GATE #64, SIX FAULT ARMS, ENFORCING.**
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full entry, its evidence and any ⛔ warnings it carried are there.
- [~] ⛔⛔ `#24-retractioncoverage` — **BUILT, SHIPPED ENFORCING, AND DOWNGRADED TO ADVISORY THE SAME DAY (2026-09-17). ⇒ WHAT REMAINS: it produces a FALSE POSITIVE on live text, and it is BLIND to the in-place-marker idiom used by its own motivating defect #3. Both must be fixed before it may be ENFORCING again.**
  **WHY:** in ONE session I retracted three claims and each time left another copy of the same sentence
  live elsewhere — a closed item still reading *"all three prerequisites still stand"*; my own
  decisions-log entry still reading *"not a re-plumbing job"*; and *"Grind past L62 toward ~L75 BEFORE
  building more legs"* marked in ONE of its TWO verbatim occurrences in `04-HANDOFF.md`. **Two were
  caught by Tier 1 reviewers, i.e. by cost.** `08-MISTAKES.md` already carried the rule and I broke it
  anyway ⇒ CLAUDE.md §6: prose failed, write the gate.
  ⭐ **THE CATEGORY ERROR IT REMOVES:** *"is this copy historical?"* is a JUDGEMENT about surrounding
  prose; *"does a marker sit next to THIS copy?"* is a FACT about bytes. The gate only asks the second.
  ⛔⛔ **IT FAILED ITS OWN FAULT TEST TWICE, WHICH IS THE ONLY REASON IT IS TRUSTED.** v1's regex matched
  the prose *between* two quotations — 1,004 bogus claims and **199 false positives** on the real tree.
  v2 let a claim CONTAINING a keyword excuse itself, so the injected-defect arm reported **ZERO**
  violations: blind to exactly the defect it exists to catch. v3 requires the past-reference idiom
  (*"THIS clause READ …"*) **and** an adjacent retraction keyword, and excludes the claim's own text
  from the marker window. Four arms now pass: real tree clean (0) · unmarked copy injected FIRES (1) ·
  same copy with a marker does NOT fire (0) · no sub-threshold fragments harvested (0).
  ⛔ **THIS SAID "34 real retracted claims are under coverage"; A REVIEWER MEASURED 35 THE SAME HOUR**
  — the downgrade text added above is itself retraction-shaped, so writing the number changed it.
  ⇒ **do not quote the count here; run `probe_retraction_coverage.py --self-test` for the live one.**
  *(Third time today a number written into the file it describes went stale before the commit landed.)*
  ⛔⛔ **THIS BULLET ORIGINALLY READ "SAFE TO ENFORCE BECAUSE IT FAILS SAFE: an unrecognised retraction
  idiom is simply not harvested, so the failure mode is a MISS, never a false alarm." THAT CLAIM IS
  WITHDRAWN — A TIER 1 REVIEWER REFUTED IT FROM BOTH DIRECTIONS AND I REPRODUCED BOTH MYSELF:**
  1. **FALSE POSITIVE (kills the "fails safe" argument).** A retraction keyword and an *unrelated*
     past-reference quotation can share a window, so a still-LIVE sentence is harvested as dead and
     every honest copy of it is then reported. **Keyword-adjacency is not claim-relatedness.**
     Reproduced on the reviewer's two-document repro: 1 claim harvested, 1 violation on live text.
  2. **FALSE NEGATIVE ON ITS OWN MOTIVATING DEFECT #3.** *"Grind past L62 toward ~L75 BEFORE building
     more legs"* is retracted with an **IN-PLACE marker** (the marker follows the live sentence), not
     re-quoted via *"THIS clause READ …"*. `harvest_claims` only recognises the re-quotation idiom.
     **Measured: that sentence occurs 2× in `04-HANDOFF.md` and is harvested 0×** — the gate is
     structurally blind to the exact bug it was written to prevent.
  ⇒ **NOW ADVISORY** (`run_gates.py` ADVISORY set); the suite is **77 entries = 73 ENFORCING + 4
  ADVISORY**. ⛔ Do not re-promote until both defects are fixed AND fault-tested against those repros.
  ⭐ **THE DURABLE LESSON, worth more than the gate: A FAULT TEST PROVES THE ARMS YOU THOUGHT OF; IT
  DOES NOT PROVE THE PROPERTY YOU CLAIMED.** Four arms passed and the property they were meant to
  establish was false in two ways no arm looked for. ⇒ when a gate's ENFORCING status rests on a
  PROPERTY, write an arm that attacks the PROPERTY.
  ✅ Also fixed in passing: `_report()` died with `UnicodeEncodeError` on a cp1252 console while
  printing its own FIX guidance (the reviewer hit it). `sys.stdout.reconfigure(encoding="utf-8")`
  added, matching the three gates that carried this bug before.
  ⚠ **THEREFORE THE PROSE RULE IN `08-MISTAKES.md` STAYS.** The gate covers the house idiom, not every
  phrasing; it is a floor, not a replacement. Run: `py -3.12 probe_retraction_coverage.py --self-test`.
- [x] ✅✅ `#24-league2f` — **NEW AND DONE 2026-09-18. THE LOBBY WINDOW'S SECOND MAP IS READ, THE REPO'S FIRST 2F FIXTURE IS MINTED, AND THE ESCALATOR ROUND TRIP IS MEASURED IN BOTH DIRECTIONS.**
  **WHY:** `#24-lobbyfixture` closed with *“the window is TWO maps and this measures ONE”*. This is
  the other one. `--driver ch24lobby2f`, predictions committed first (`265b7d40`), four arms.
  ⭐ **THE ARTIFACT:** `saves/post_league_2f.ss1`, pinned `d3c09e7af34922d28dacbf927fb7b6bc` — the
  repo's FIRST fixture on `EVER_GRANDE_CITY_POKEMON_LEAGUE_2F`. **Rests on (2,6)**, L75 party,
  **0 battles**, `ENTERED_ELITE_FOUR` **still False**; re-verified by RELOAD in
  `probe_ch23_leg_guards.py`, which now reads FIVE positions.
  ‼‼ **(1,6) IS THE DELIVERED TILE; (2,6) IS THE RESTING TILE — DO NOT CONFUSE THEM.** The escalator
  delivers to **(1,6)** (✅ the decomp's reciprocal warp, measured here for the first time) and the
  avatar then AUTO-COMPLETES A STEP to (2,6).
  ⭐⭐ **THE ROUND TRIP IS CLOSED AND THAT SENTENCE IS NOW EXECUTED.** `victory_road.py:410-411` has
  called the escalator *“benign (2F warps straight back)”* since it was written and **nothing in this
  repo had ever run it.** Measured: `(3,4)→(1,7)` warps up; stepping from (2,6) back onto (1,6)
  returns to `LEAGUE_1F (1,7)`; the leg walks home to (3,4). ⇒ a stray step on the escalator is
  **recoverable**. ⚠ 2F is still `"allow_escaping": false` — no Dig/Teleport/Escape Rope; the
  escalator is the ONLY way out, it simply works.
  ⭐ **AND §Ch23 RAISES ON 2F TOO** — all ten call sites False, `ch23_chapter_done()` False, and a
  guarded call gives `BotModeError … failed after 3 attempts`, `frames=0`, `moved=False`.
  ⇒ `#24-ch23lobbyresume`'s **LEAGUE-WIDE** scope is confirmed on a THIRD map.
  ✅ **ARMS:** TREATMENT `missing=[]` · VACUITY refused at the premise with zero readings ·
  `NORETURN` → `missing=['L2-RETURN']` alone · `BLINDGUARD2F` → the guard's self-test fires and the
  leg walks NOTHING, going blind to exactly the sealed-room and second-warp synthetics while still
  catching the same-map one.
  ⛔ **TWO DRIVER BUGS, BOTH OF WHICH WOULD HAVE BLAMED THE GAME — see the graded note.** (1) a
  CROSS-MAP `calculate_path` request returned *“not on connected maps (warps don't count)”*, which my
  own predictions file said would mean *“2F is a one-way pocket”*; it meant the request was malformed.
  (2) after a settle was added, the return aimed at the SETTLED tile instead of the DELIVERED one and
  raised a message accusing `victory_road.py` of being wrong.
  ⚠ **A DESIGN DEVIATION IS DECLARED IN THE GRADED NOTE, NOT BURIED:** prediction P3 was pre-registered as *“vet a route to a SEALED map (or unreachable)”*; the implementation injects **SYNTHETIC** waypoints instead, because a sealed route IS unreachable from the lobby and that arm would have passed **for the wrong reason** on every run — the exact shape `#24-pathguardblind` was about. ⇒ P3 is graded ✅ against the SYNTHETIC test, and the change is stated rather than scored around.
  ⚠ **STILL OWED:** a **post-talk** sibling fixture. The metatile behaviour of (1,6) is NOT measured
  (only that the return works), and the FREQUENCY of a stray escalator step is untouched.
  Graded predictions + the two reusable facts: `ai-research-notes/2026-09-18-ch24-league2f-PREDICTIONS.md`
- [x] ✅ `#24-pathguardblind` — **CLOSED. Full entry ARCHIVED 2026-09-23 to `28-HANDOFF-ARCHIVE.md`** (the punch list is a CURRENT-STATE file and had grown past its line budget again). ⇒ search that file for `#24-pathguardblind` — nothing was deleted.
- [x] ✅ `#24-lobbyfixture` — **CLOSED. Full entry ARCHIVED 2026-09-23 to `28-HANDOFF-ARCHIVE.md`** (the punch list is a CURRENT-STATE file and had grown past its line budget; this was its longest closed item at 65 lines). ⇒ search that file for `#24-lobbyfixture` — nothing was deleted.
- [~] ⛔ `#24-ch23lobbyresume` — **NEW 2026-09-18, AND THE RAISE IS NOW *MEASURED*, NOT TRACED. ⛔⛔ RE-SCOPED THE SAME DAY: THE SYMPTOM IS **LEAGUE-WIDE**, NOT LOBBY-ONLY. ⇒ WHAT REMAINS: DESIGN THE FIX — and FIRST establish whether this ever happens in a real run (a BATCH question, untouched).**
  ✅✅ **MEASURED 2026-09-18** by `probe_ch23_lobby_resume.py` — the chapter is **CALLED**, not traced.
  On `post_league_lobby.ss1` (LEAGUE_1F (3,4)): `ch23_chapter_done() BEFORE = False` →
  `CALL -> BotModeError` (*“Ch23 (Victory Road) failed after 3 attempts”*, three clauses each
  *“every leg ran but the chapter does not grade done (wally=True, at=((16, 10), (3, 4)))”*),
  `moved = False`, **`frames consumed = 0`**. ✅ CONTROL SEPARATES: on `post_league_shop.ss1`
  `ch23_chapter_done()` is True and the same call `RETURNED` cleanly, running no leg.
  ⭐ **WHY IT WAS SAFE TO RUN, AND THE REASON GENERALISES:** with every guard False the chapter
  **yields nothing**, so one `next()` executes the whole body for **zero emulator frames** — the
  bot cannot move, so it cannot wander into the un-fleeable gauntlet. `frames consumed` is
  REPORTED rather than assumed, so the safety argument is checked on every run.
  ⭐⭐ **THE CHARACTERISATION: PHYSICALLY FREE, LOGICALLY STUCK.** `calculate_path` off (3,4) to the
  lobby's own exit landing **SUCCEEDS — 14 waypoints**. ⇒ ⛔ this is **NOT** the §Ch15/§Ch18/§Ch19
  “stranded” shape and must not be described with that word: the bot's legs work, its BOOKKEEPING
  has no move. Every pass re-derives the same ten False guards and burns the retry budget again.
  ⛔⛔ **RE-SCOPED BY ITS OWN PRE-REGISTERED FALSIFIER (P9).** `post_hall4_door` — a SEALED map —
  raises **identically** (same clauses, zero frames). ⇒ §Ch23 cannot resume from **ANY** map inside
  the League, because `ch23_chapter_done()` conjuncts `_on_map(EG)` and every interior is a
  separate map. The prediction row had said in advance that a match would mean the name was too
  narrow; it matched.
  ⭐ **THE SLUG SURVIVES BECAUSE THE *RESIDUAL* IS LOBBY-ONLY.** The §Ch24 marker is *on a
  `CH24_SEALED_MAP` OR `IS_CHAMPION`*, and `06-DECISIONS-LOG.md` DECISION 2 **deliberately excludes
  `POKEMON_LEAGUE_1F (16,10)`** (§Ch23's legs 10/11 work there). ⇒ the marker covers the HALL4 half
  and leaves the lobby half exactly as measured. ⚠ **NOT VERIFIED BY ME:** *how* the marker is meant
  to feed `ch23_chapter_done()` or the `story_mode.py:5172` gate — that is prerequisite (1)'s
  implementation and I have read no code for it. The claim above is about the marker's MAP SET,
  which is decided; not about a mechanism that exists.
  ⚠⚠ **BEFORE THIS IS PRIORITISED: THE FREQUENCY IS UNMEASURED.** Nothing shows a real run ever
  re-enters §Ch23 from inside the League. `CLAUDE.md` §9: that is a BATCH question, not a driver
  question. ‼ **A measured raise is not a measured incident rate.**
  ⚠ **FIX NOT DESIGNED.** Two visible candidates, neither evaluated: widen the completion
  predicate, or stop `story_mode` re-entering a chapter that raised from an unchanged position.
  Graded predictions + the instrument defect found mid-run:
  `ai-research-notes/2026-09-18-ch23-lobby-resume-PREDICTIONS.md`
  ⛔ *(Superseded headline, kept so the change is visible: “§Ch23 CANNOT RESUME FROM THE LEAGUE
  LOBBY — THE TILE ITS OWN LEG 10 STANDS ON. ⇒ WHAT REMAINS: PROVE THE RAISE BY RUNNING IT.”
  The leg-10 fact is still true and still the reason the lobby is REACHED; it is simply not the
  boundary of the defect.)*
  **THE SHAPE.** ✅ MEASURED 2026-09-18 on `post_league_lobby.ss1`: on `POKEMON_LEAGUE_1F (3,4)` **all
  ten §Ch23 call sites read False** and **`ch23_chapter_done()` reads False** — the latter because it
  conjuncts `_on_map(EG)`, the OUTDOOR map (`ch23_chapter_done`, `victory_road.py` — ‼ cite the
  SYMBOL, the line has drifted: `06-DECISIONS-LOG.md` cites `:3312`, it is `:3278` today).
  ⇒ nothing runs, nothing changes, the chapter never grades done, three attempts are consumed, and
  `do_victory_road_chapter` **raises** `BotModeError("Ch23 (Victory Road) failed after 3 attempts…")`.
  `story_mode.py:5172-5173` re-enters the chapter whenever `ch23_chapter_done()` is False — in the
  lobby, **always**.
  ⭐⭐ **WHY THIS IS REACHABLE IN ORDINARY PLAY, AND NOT A §Ch24 PROBLEM.** ✅ `heal_at_league` (leg 10)
  holds Up through the League door and then runs `_navigate_riding_out(LEAGUE_1F, LEAGUE_NURSE_STAND)`
  — **`(3,4)`, the exact tile of the repro fixture.** Leg 11 (the mart) works on that map too. ⇒ §Ch23
  **puts itself** on a tile it cannot resume from; any derail or whiteout-recovery that re-enters the
  chapter while standing there lands in the raise.
  ⛔ **THE §Ch24 MARKER WILL NOT FIX THIS, AND MUST NOT BE STRETCHED TO.** `06-DECISIONS-LOG.md`
  DECISION 2 excludes `POKEMON_LEAGUE_1F (16,10)` from `CH24_SEALED_MAPS` **on purpose**, because
  §Ch23's legs 10/11 work there — including it would grade §Ch23 done mid-heal, before the basket is
  bought. That exclusion is correct for the marker's purpose. ⇒ **two different problems; do not
  collapse them.**
  ⚠ **AND CHECK THE PREMISE BEFORE BUILDING A FIX — I HAVE NOT:** is the lobby actually re-entered
  with §Ch23 incomplete in a real run, or do legs 10/11 always complete within one attempt? The raise
  is measured; **the FREQUENCY is not**, and `CLAUDE.md` §9 says frequency questions are batch
  questions, not driver questions.
  ⭐ **THE NEXT STEP IS CHEAP, SAFE AND DECISIVE:** load `post_league_lobby.ss1` and call
  `do_victory_road_chapter()`. Every guard is False, so **nothing moves** — the run cannot wander into
  the gauntlet — and it either raises (confirming the trace) or it does not (refuting it). ⇒ turns a
  DERIVED consequence into a READ one for the cost of ~3 attempts of no-ops.
- [ ] ⚠ `#24-harnessphantomnames` — **NEW 2026-09-18, FILED NOT FIXED. FOUR PHANTOM FLAG/VAR NAMES IN THE HARNESS READ FALSE/0 FOREVER. ⇒ WHAT REMAINS: rename one, and DECIDE about the other three.**
  ✅ **MEASURED:** 302 harness files · 86 `get_event_flag` + 68 `get_event_var` literal calls · **4
  phantom names**, all in `story_harness.py`:
  * `:592` `get_event_flag('FLAG_ADDED_MATCH_CALL_TO_POKENAV')` — **fixable by rename**: the bare name
    exists (`event_flags/emerald.txt:252`, `304 ADDED_MATCH_CALL_TO_POKENAV`).
  * `:396`, `:508`, `:551` `get_event_var('VAR_RESULT')` — ⚠ **not a prefix bug**: our var table has
    **no RESULT entry at all** (256 entries, zero matches). Needs a decision, not a rename.
  ✅ **SEVERITY IS LOW AND I CHECKED RATHER THAN ASSUMED:** all four are **DIAGNOSTICS** — `_var()` feeds
  a log f-string at `:408`, `_dump` is a dump, `:551` is a log line. **Zero feed an acceptance, assert
  or raise.** ⇒ misleading log output, not a false PASS.
  ⚠ **THE GATE'S SCOPE IS DELIBERATE, NOT A DEFECT** — checked before claiming one.
  `audit_flag_names.py` says *“every flag/var name string used by **story code**”* and globs
  `modules/story/*.py` + `story_mode.py`; the harness is out of scope **by design**. ⇒ the argument for
  widening it is **“the harness is where drivers produce EVIDENCE, and a phantom name corrupts a reading
  silently”**, not “the gate is broken”. ‼ Note its own history: it *“ran for weeks against exactly two
  hand-written paths”* while chapters moved out from under it, and the fix was a glob. **Same shape, one
  directory over.**
- [ ] ⛔⛔ `#24-markerwinstate` — **NEW 2026-09-17 (late). THE §Ch24 PROGRESS MARKER CHOSEN ON 2026-09-16 DOES NOT COVER *WINNING*, AND MY OWN TAIL PROBE HOLDS THE COUNTEREXAMPLE. ⇒ WHAT REMAINS (updated 2026-09-18 — the DESIGN is now complete): **(a)** mint a LOBBY fixture and re-measure caveat (2), which is currently TRACED by an agent probe and not READ; **(b)** implement the explicit `CH24_SEALED_MAPS` tuple + `IS_CHAMPION` disjunct. *(The header previously read “the marker must become a DISJUNCT before prerequisite (1) can be called done” — that design decision is made; see the body.)*
  **THE RULING** (`06-DECISIONS-LOG.md:5496`): *"the marker is 'the bot is standing on a SEALED League
  map'"*, safe **by exhaustion** because no whiteout can respawn on one. ✅ **That exhaustion argument
  is TRUE and I re-measured it** — the decomp's heal table has **22 locations over 20 maps and not one
  is a League interior**; the only INDOOR heal points in the game are the two Littleroot bedrooms.
  ⛔⛔ **BUT A *WINNING* RUN ENDS AT `LITTLEROOT_TOWN_BRENDANS_HOUSE_2F (4,2)`** — MEASURED by
  `--driver ch24tailprobe` (`ai-research-notes/2026-09-17-ch24-legB-TAIL-MEASURED.md` Q8) — **which is
  not a League map.** So after a win the marker reads FALSE. Verified line by line, in our own code:
  1. `ch23_chapter_done()` requires `_on_map(EG)`; Littleroot is not Ever Grande ⇒ **False** ⇒ §Ch23
     runs again (`victory_road.py:3318`).
  2. Legs 1-3 self-skip — `_PRE_DEPARTURE_MAPS = (CITY, PC_1F, PC_2F, UWS, UW126)` (`:3275`).
  3. **Leg 4 FIRES:** `if not inside_vr and not at_ever_grande_top()` (`:3384-3385`), and
     `at_ever_grande_top()` is `inside_league() or (_on_map(EG) and y <= EG_LANDING[1])` (`:1426`) —
     **both terms False from Littleroot.**
  ⇒ ⭐ **THE BOT WOULD ATTEMPT AN OCEAN CROSSING FROM A BEDROOM**, burn the chapter's three attempts
  and raise — turning a **completed game** into a hard §Ch23 failure.
  ✅ **THE FIX IS ONE WORD — A DISJUNCT:** *"on a sealed League map **OR** the game is cleared"*.
  ✅✅ **CORROBORATED 2026-09-18 AT THE DECOMP, BY ME:** `data/event_scripts.s:585-586` shows
  `EventScript_WhiteOut::` calls `ResetEliteFour` **unconditionally** ⇒ the wipe is not confined to
  the gauntlet: **a white-out ANYWHERE in Hoenn clears them.** ⇒ the choice below is not merely
  defensible, it is forced.
  `IS_CHAMPION` (flag **2175**) is the right second term because it is **MONOTONE**: set in exactly one
  decomp file (`data/scripts/hall_of_fame.inc`) and **cleared nowhere** — unlike `VAR_ELITE_4_STATE`
  and the four `DEFEATED_ELITE_4_*` flags, which `ResetEliteFour` wipes on the WINNING path as well as
  the losing one. ⚠ `IS_CHAMPION` alone is reported ~13,000 frames early (agent claim, unverified), so
  it is a COMPLETION term, not a "the run is usable" term — do not collapse the two roles
  (`#24-gameclearflag`).
  ‼ **THIS IS THE THIRD CAVEAT ON THAT RULING, AND THE FIRST TWO ARE STILL OPEN:** (1) `inside_league()`
  is the wrong helper — it includes the lobby and 2F, where §Ch23's own heal and mart legs stand; (2)
  the lobby window between the guard-talk and Hall5 is still untraced.
  ✅✅ **THE DESIGN IS NOW COMPLETE — ALL THREE CAVEATS ANSWERED 2026-09-18.** Full write-up, separating
  what I measured from what an agent did: `ai-research-notes/2026-09-18-ch24-marker-DESIGN-COMPLETE.md`
  ⭐⭐ **THE DECISIVE CONSTRAINT, FOUND BY A REFUTER ATTACKING MY OWN SHORTHAND: THE MARKER MUST BE AN
  EXPLICIT TUPLE, NEVER A GROUP OR RANGE TEST.** ✅ I verified `map_data.py:1037-1051` myself — map group
  16 ALSO contains `EVER_GRANDE_CITY_POKEMON_CENTER_1F (16,12)`, `_2F (16,13)`, `POKEMON_LEAGUE_1F (16,10)` and
  `POKEMON_LEAGUE_2F (16,14)`. ⛔⛔ **CITATION CORRECTED 2026-09-18 AFTER A TIER 1 BLOCK — I NAMED THE WRONG MAP AND MARKED IT “✅ verified by me”.** *(This said the Poké Center maps are “which §Ch23's leg 10 walks into to heal”.)* ✅ **LEG 10 HEALS ON `LEAGUE_1F` — `EVER_GRANDE_CITY_POKEMON_LEAGUE_1F (16,10)`**: `heal_at_league` asserts `_on_map(LEAGUE_1F)` (`victory_road.py:2962`) and walks to `LEAGUE_NURSE_STAND = (3,4)` on that same map (`:2982`). ⛔⛔ **AND MY OWN CORRECTION OVER-REACHED — CAUGHT BY ME ON THE NEXT PASS.** *(It said the Poké Center maps are “never visited by our code (2 refs repo-wide)”.)* **That was a SYMBOL COUNT, not an occupancy test.** ✅ `PokemonCenter.EvergrandeCity = (MapRSE.EVER_GRANDE_CITY, (27, 48))` (`map_data.py:1537`) is a **DOOR** tile on the OUTDOOR map, and `heal_in_pokemon_center` walks through it ⇒ the avatar stands INSIDE `EVER_GRANDE_CITY_POKEMON_CENTER_1F (16,12)` during any Poké-Centre heal. The code simply never names that enum member — it detects such maps by SUBSTRING (`early_game.py:385`: `if cur is None or “POKEMON_CENTER” not in enum_name`), which is why my grep found 2 files for the symbol and 7 for the substring **within `modules/`** (8 across the whole sandbox — a reviewer counted the wider scope; both are right, which is why the scope is now stated). ⇒ ⭐ **BOTH `(16,10)` AND `(16,12)` ARE GENUINELY OCCUPIED, so the range-test hazard is STRONGER than either earlier version of this paragraph: two independent maps in group 16 that §Ch23 stands on while its work is unfinished.** ✅ **UPGRADED FROM INFERRED TO READ** — a Tier 1 reviewer found the direct evidence and I confirmed it at source: §Ch23 walks into that Poké Center **twice, both before the basket**. **Leg 4** (`victory_road.py:1556-1566`): *“⛔⛔ THIS IS LOAD-BEARING, NOT HOUSEKEEPING. Until the bot walks into the Ever Grande Poké Center, `lastHealLocation` is still SOOTOPOLIS”* — then `heal_in_pokemon_center(PokemonCenter.EvergrandeCity)`. **Leg 6** (`:2328-2333`) calls it again, *“heal before the B1F descent”*. ⇒ the occupancy of `(16,12)` is now a READ fact, not an inference. *(The docs previously UNDER-claimed this; the reviewer said so and was right.)* ⭐ **THE HAZARD IS UNCHANGED AND ACTUALLY MORE DIRECT:** the bot stands on **(16,10), a group-16 map**, while the heal prompt runs, so a range test grades §Ch23 done mid-heal. The Poké Center pair is a second, independent reason a range test is wrong — it would sweep in maps we never occupy. ⇒ the 11-member explicit tuple is unaffected; only the citation was wrong. ‼ I had verified the MAP TABLE and then attached an agent's sentence about leg 10 to it. ⇒ a range test
  would grade §Ch23 **done mid-heal, before the basket is bought** — the KI-90 class of hole re-opened by
  a convenience. *(Also: `ROUTE4_POKEMON_CENTER_1F` shares the raw tuple `(16,0)` in another enum —
  compare enum MEMBERS, never bare tuples.)*
  **THE MARKER:** an explicit 11-member `CH24_SEALED_MAPS` (five rooms + Hall1-5 + Hall of Fame),
  **OR `IS_CHAMPION`** for the winning end state. ⚠ `IS_CHAMPION` is a COMPLETION term, not a
  “run is usable” term — do not collapse the roles (`#24-gameclearflag`).
  ✅ **MEASURED BY ME THAT THE MARKER IS NECESSARY:** loading pinned fixtures and evaluating the real
  predicates — on `post_hall4_door` (**HALL4, sealed, one tile from the Champion's door**)
  `ch23_chapter_done()` returns **False**, so §Ch23 *is* re-entered mid-gauntlet without a marker.
  Controls separate (sealed marker=True / outdoor marker=False), and `post_league_heal` False →
  `post_league_shop` True shows the basket conjunct working as designed.
  **CAVEAT (2), the lobby window: SAFE POST-WALLY.** Zero of the eleven legs fire there; the chapter
  raises after three no-op attempts. ⭐ And the two caveats INTERACT: leg 4 skips because
  `at_ever_grande_top()` is True in the lobby **via `inside_league()`, which includes 1F** ⇒ the lobby is
  protected by the very wideness that makes that helper wrong for the marker. ✅ Keep it as it is — it
  has exactly ONE caller. ⚠ **The window is TWO maps**: 1F and League 2F, reachable by
  `LEAGUE_ESCALATOR = (1,7)`, *“`MB_UP_ESCALATOR`, collision 0 — an accidental step-on warp”*
  (`victory_road.py:410-412`). ⚠ And “zero legs fire” holds **post-Wally only**; pre-Wally the training
  leg fires there (its guard at `:3393` carries no position test).
  ✅✅ **AND THE DESIGN'S CENTRAL CLAIM IS NOW *READ*, NOT TRACED (2026-09-18).** Evaluating every
  §Ch23 leg guard live at each fixture we hold — guards only, no leg ever run — **on the SEALED map
  `post_hall4_door` (HALL4) NOT ONE of the TEN CALL SITES is True**, and the same holds at the new
  `post_league_lobby` fixture.
  ⛔⛔ **CORRECTED 2026-09-18, SAME DAY: THIS FIRST READ “NINE GUARDS” AND THE DISPATCH HAS TEN.**
  An adversarial reviewer found (a) the **TRAINING leg** (`victory_road.py:3430-3431`) is a guarded
  `yield from` carrying no `LEG N` banner, so an enumeration built from the numbered banners walks
  past it — ‼ **and this file ALREADY SAID SO four lines above**, which is the sharp part of the
  lesson; and (b) **leg 11 is a NESTED call site** (`:3462-3467`) whose transcription read only the
  outer half. Both instruments were corrected and re-run.
  ‼ **THE CORRECTION CHANGED TWO CONTROL READINGS**, so the old numbers below are RETRACTED:
  EVER_GRANDE degraded was published as **5/10/11** and is actually **5/10**; basket-bought was
  published as **5/11** and is actually **5**. Controls separate and are informative:
  at EVER_GRANDE legs **5/10** fire on the degraded-party fixture and **5** on the healthy one, ✅ **RE-RUNNABLE AND COMMITTED** (a reviewer noted the first version had no artifact): `tools/story-dev/probe_ch23_leg_guards.py`, output at `tools/story-dev/evidence/2026-09-18-ch23-leg-guards-TEN-CALL-SITES.stdout.txt` ‼ **CITE THIS ONE.** ⛔ The older `…-BY-POSITION.stdout.txt` is the NINE-site output and is SUPERSEDED — it is kept as the record of what the first instrument printed, and its two EVER_GRANDE control rows are WRONG (see the retraction above).
  i.e. leg 10's heal guard behaving exactly as written. ⇒ inside the sealed zone the legs are not
  merely inert, they are **never invoked** — stronger than the design claimed.
  ⛔⛔ **RETRACTED 2026-09-18 (same day it was written) — THIS “NUANCE” WAS FALSE.** It read:
  *“leg 11's guard is bare `_on_map(EG)` with no basket conjunct, so it fires at Ever Grande even
  AFTER the basket is bought — its self-skip lives in the leg body.”* The dispatch is **nested**:
  `if _on_map(EG): stock = bag_healing_stock(); if any(stock < qty): yield from ...`
  (`victory_road.py:3462-3467`). The self-skip **IS the inner `if`, at the call site**, one line below
  the outer one — not in the leg body at all, and leg 11 does **not** fire once the basket is stocked
  (measured: it fires at NEITHER Ever Grande fixture). ‼ The transcription had instrumented the outer
  `if`, which merely CONTAINS the call — **an input to the action, not the action** — and I reported
  its value as if it described when the leg runs.
  ⇒ “legs do not re-fire” is true for two DIFFERENT reasons in two places; only the sealed-zone case is
  guaranteed by the dispatch. Full table: `ai-research-notes/2026-09-18-ch24-lobby-fixture-SPEC.md`
  ⚠⚠ **WHAT IS STILL OWED, AND IT IS SMALL:** the lobby result is an AGENT probe reproduced by a
  refuter — **not measured by me**, because **no fixture in this repo stands in the lobby**
  (`grep -c POKEMON_LEAGUE_1F saves/FIXTURES.md5` → 0). ⇒ **mint a lobby fixture and re-measure**; the
  §Ch24 entry driver already walks that route. Until then caveat (2) is TRACED, not READ.
  ⛔ **DO NOT WIRE SEGMENT 24** — the DESIGN of prerequisite (1) is done; the IMPLEMENTATION is not, and
  prerequisites (2), (3) and (4) are untouched.
- [~] ✅⚠ `#24-cavehealblind` — **THE RULED GROUND'S HEAL IS MEASURED AND WORKS (2026-09-18). ⛔⛔ BUT THE QUESTION THIS ITEM ORIGINALLY ASKED — CAN A TILE *DEEPER* THAN THE EXIT APRON HEAL — IS **NOT ANSWERED**; IT IS **MOOT** BY USER RULING 2. ⇒ WHAT REMAINS: nothing, unless B1F is ever re-opened.**
  ⭐⭐ **WHAT WAS MEASURED** (`--driver ch24caveheal`, predictions committed first at `32b9fcf3`; graded in `ai-research-notes/2026-09-18-cavehealblind-PREDICTIONS.md`): from `TRAIN_SPOT_1F (15,39)` the route is **`VICTORY_ROAD_1F → EVER_GRANDE_CITY → EVER_GRANDE_CITY_POKEMON_CENTER_1F → EVER_GRANDE_CITY`**, then a navigate back in. **2,002 yields · 1 wild battle · 0 whiteouts · `missing=[]` · PASS**, with **HP 72.8% → 100% and PP 437/480 → 480/480**.
  ⛔⛔ **AND HERE IS THE HONEST PART, CAUGHT BY A TIER 1 REVIEW BEFORE IT SHIPPED: THIS CONFIRMED WHAT THIS ITEM ALREADY PREDICTED, AND DID NOT TEST WHAT IT ASKED.** The original text (kept below) says *“HEALING FROM VICTORY ROAD WORKS TODAY ONLY BECAUSE `TRAIN_SPOT_1F (15,39)` **IS** `VR_EXIT_APRON`”* and then asks for a drive **“park at a B1F chamber tile”**. ⇒ my drive parked on the APRON. It upgrades *“works by coincidence”* to *“works, measured, including PP”* — which is worth having — but it is **not** the deeper-tile experiment, and I first filed it as a separate `[x] ANSWERED` item, which left TWO contradictory entries for one slug.
  ✅ **WHY THE UNANSWERED HALF NO LONGER BLOCKS ANYTHING:** USER RULING 2 (2026-09-18) put the grind at the Victory Road **exit side** for round-trip speed and states **“B1F IS OFF THE TABLE … do not reopen B1F without a new ruling”**. ⇒ the deeper-tile heal is a prerequisite for a **B1F** grind only, and there is no B1F grind. **Moot, not solved.** ⛔ If B1F is ever re-opened, **this experiment comes back with it** — park at a B1F chamber tile, force a heal, observe.
  ⭐ **A REAL SUB-FINDING THAT DOES GENERALISE:** the `_CAVE_EXITS` gap turned out not to matter even here — `heal_in_pokemon_center` uses the multi-hop warp-aware `navigate_to_anywhere` and walked out AND back with **no table entry**. ⛔ Do NOT “fix” this by adding a Victory Road row; `early_game.py:1988-1997` already records the tables as *“REDUNDANT, not load-bearing”*. ⚠ That said, this is evidence from the APRON, one step from the warp — it does **not** settle the cross-warp-level case the `:2154-2157` comment warns about.
  ⭐ **IT ALSO REMEDIES THE STALL THE FIXTURE WAS CAPTURED FOR:** `grind_stall_ppzero.ss1` had every slot-0 move at 0 PP, and the heal restored **PP as well as HP** ⇒ a complete remedy for the dry-PP stall, not a partial one.
  ⚠ **WHAT IT DOES NOT SHOW:** it is **ONE heal, not a grind** — a 623-battle run interleaves heals with training, and the ≈1-heal-per-8.3-battles frequency is measured elsewhere and NOT re-measured here.
  ⚠ **AND ONE ARM DID NOT DO ITS JOB.** The intended VACUITY arm never fired — **no fixture in this repo is at full HP AND full PP** — so what that run produced is a **SECOND INDEPENDENT REPLICATION** on a different L75 party, and its evidence file is named `REPLICATION-L75` so it cannot be cited as vacuity. The guard is instead **self-tested in-process, in both directions**.
  ‼ **ONE INSTRUMENT DEFECT, FIXED MID-DRIVE:** `C-ATPC` was read from the position AFTER the heal generator finished and logged a MISS — because `heal_in_pokemon_center` **enters, heals and walks back out**, so the reading was true and then stopped being true before I looked. Taken from the ROUTE now. **Record a reading AT ITS TAKE POINT.**
  ⭐ **RUN IT:** `PYTHONUTF8=1 py -3.12 story_harness.py grind_stall_ppzero.ss1 --driver ch24caveheal --frames 120000 --log caveheal.log`
  ─── *(the item's ORIGINAL text, kept verbatim — it is the statement of the question that is still unanswered, and it predicted the apron result correctly:)*
  ✅ **MEASURED BY ME:** `grep -c VICTORY_ROAD sandbox-pokebot/modules/story/early_game.py` → **0**.
  `_CAVE_EXITS` (`early_game.py:2003`) holds exactly two entries — `GRANITE_CAVE_1F` and Fiery Path —
  and its docstring says *“A cheap no-op anywhere that is not in `_CAVE_EXITS`.”*
  ⛔ **THE COMMENT DIRECTLY ABOVE THE CALL RECORDS A MEASURED FAILURE** (`:2154-2157`): *“CAVE-AWARE HEAL
  (2× real-HW Manual drops 2026-07-22): healing from INSIDE Granite Cave targeted the Dewford PC
  **across warp levels** — the global navigator can't do that (‘not on connected maps’). Exit the cave
  first.”*
  ⇒ ⭐ **HEALING FROM VICTORY ROAD WORKS TODAY ONLY BECAUSE `TRAIN_SPOT_1F (15,39)` *IS* `VR_EXIT_APRON`**
  — the spin tile already sits one step from the arrow warp, so the no-op costs nothing. **Move the spin
  tile one warp deeper (i.e. B1F) and the heal depends on the very navigation the comment says fails.**
  ⚠ **UNRESOLVED, AND I COULD NOT SETTLE IT STATICALLY.** `heal_in_pokemon_center` uses
  `navigate_to_anywhere` (`higher_level_actions.py:465`), a warp-chaining graph navigator needing live
  state — **not** `calculate_path`. ⇒ **THE CHEAP DECISIVE EXPERIMENT IS A DRIVE:** park at a B1F
  chamber tile, force a heal, observe. That same run also buys B1F's unmeasured frames/battle.
  ‼ **THIS IS A PREREQUISITE FOR *ANY* B1F GRIND** and is why the ground choice is deferred — see
  `#24-levelgap`. It costs nothing today because production never trains anywhere but 1F.
- [ ] ⏸ `#24-overworlditems` — **NEW 2026-09-18. ⛔⛔ DEFERRED BY USER RULING — DO NOT START. GATED BEHIND “THE BOT BEATS THE ELITE FOUR TO THE USER'S STANDARD”, WHICH IS A JUDGEMENT ONLY THE USER CAN MAKE.**
  **THE RULING (2026-09-18), verbatim:** *“Out for now but worth investigating in the future once we
  get the bot to complete the elite 4 successfully **to my liking**, only then can we investigate the
  ground items/thief items/reward items/gifted items (like quick claw for example) but note **I may
  call for this earlier and that is ok** but for now it should be gated to be worked on AFTER the bot
  beats the elite 4 **to my liking/standards**.”*
  ✅✅ **THE GATE IS NOW CONCRETE — USER RULING 11 (2026-09-18) REPLACED “TO MY LIKING” WITH A
  CHECKABLE BAR:** *“it beats the Elite 4/enters the hall of fame … **Wins organically — no fixture
  scaffolding, no harness driver, running as the real story mode at ×1**”*.
  ⇒ **FOUR CONJUNCTS, ALL REQUIRED:** (1) the Hall of Fame is entered; (2) from the REAL story mode,
  not a `--driver`; (3) with NO pinned-fixture scaffolding — the bot got itself there; (4) at **×1**.
  ⛔⛔ **CORRECTION TO THIS ITEM'S OWN EARLIER WORDING (made hours earlier, same day):** it said
  *“DO NOT unlock this by checking `SYS_GAME_CLEAR` / `IS_CHAMPION`”*. ‼ **That is now too strong.**
  The flag IS conjunct (1) — it is simply **NOT SUFFICIENT ALONE**. The other three are about
  PROVENANCE: *how* the flag came to be set. ⇒ check the flag **and** how it was reached.
  ‼ **AND THE ORIGINAL WARNING STILL BITES:** the Elite Four HAS already been beaten — 2026-09-17,
  `--driver ch24tailprobe`, from a pinned L75 fixture. That satisfies conjunct (1) and **fails (2),
  (3) and (4)**, which is exactly why the gate is still shut.
  ✅ **THE GATE IS SOFT IN ONE DIRECTION ONLY:** the user may call for it EARLIER (*“that is ok”*).
  ⇒ an explicit user instruction opens it; nothing else does.
  **SCOPE WHEN IT OPENS** (the user's own list): **ground items** (overworld balls), **thief items**
  (stolen via Thief/Covet), **reward items** (given for events), and **gifted items** — the example
  given is **Quick Claw**.
  ⚠ **ONE EXCEPTION ALREADY IN FLIGHT, AND IT IS NOT THIS ITEM:** `#24-amuletcoin` is a single
  targeted errand justified by USER RULING 6 (money is a high priority) and is tracked separately.
  ⇒ ⛔ do not fold it in here, and do not use it as a wedge to start general item work.
- [ ] ⭐⭐ `#24-mapknowledge` — **NEW 2026-09-18 (USER DIRECTIVE). A PER-CHAPTER TRAVERSABILITY KNOWLEDGE BASE: WHERE CAN THE BOT GO, GIVEN WHERE IT IS IN THE STORY. ⇒ WHAT REMAINS: research is RUNNING; then a scope decision; then build.**
  ⭐ **THE DIRECTIVE:** *“we should ensure we have a better picture of the entire gameplay map such as
  moveable tiles, obstacles (requiring hms or certain tasks to be completed) as well as **maps for each
  chapter of the story** so the bot can understand WHERE its able to go depending on what part of the
  story its at … to also help us figure out mapping between locations as well as training
  routes/routes to gym leaders and trainers to re battle (maybe also items to pick up to
  use/sell/give to pokemon?)”*
  ⭐⭐ **IT IS PRODUCT, NOT TOOLING** — the user ties it explicitly to the v2 AI pilot
  (`01-VISION-AND-DESIGN.md` §2, extended 2026-09-18): the data is handed forward so that agent does
  not rediscover Hoenn by trial and error.
  **WHY IT PAYS OFF FOR *THIS* BOT TOO:** routing, level-appropriate training grounds
  (`#24-trainingbrackets`), and rematch routes (`#24-pokenavrematch`) are all the same question —
  *what is reachable from here, right now* — which nothing currently answers.
  ⚠⚠ **SCOPE DISCIPLINE, AND IT MATTERS:** the bot **cannot yet beat the Elite Four**. A full map KB
  is a large detour from that. ⇒ ⛔ **do NOT let this block §Ch24**; the research brief explicitly asks
  the agents to say what should WAIT.
  ⛔ **KNOWN TRAPS THE DESIGN MUST SURVIVE:** KI-74 — a layout-swapped map **lies to static ROM
  readers**, so any generated collision/behaviour data is untrustworthy exactly where it matters most;
  script-moved NPCs block tiles; one-way warps; and tiles walkable only while a flag is set.
  ‼ **AND A MEASURED CONSTRAINT ON ANY ROUTING LAYER BUILT ON THIS:** `calculate_path` REFUSES
  cross-map requests (*“not on connected maps … warps don't count”*) — cross-map travel must be
  expressed as per-map segments that STEP ONTO the warp tile.
  ‼ STATUS: an 11-agent research workflow is RUNNING (5 angles, each adversarially verified). ⛔ No
  code until it lands and its load-bearing claims are re-verified here.
- [ ] ⭐⭐ `#24-amuletcoin` — **NEW 2026-09-18. A FREE ITEM THAT DOUBLES EVERY TRAINER PAYOUT, AND OUR CODE HAS NEVER HEARD OF IT. ⇒ WHAT REMAINS: VERIFY THE CLAIM MYSELF, then decide whether to fetch it.**
  ⭐ **WHY THIS MATTERS NOW:** USER RULING 6 makes money *“a high priority … money is relatively
  limited”*, and §Ch23 leg 11 spends ₽54,300 on the Elite Four basket against a MEASURED ₽56,041 —
  **₽1,741 of slack**. A payout multiplier attacks that constraint at its root rather than at the margin.
  ⚠ **AGENT-SOURCED, NOT YET VERIFIED BY ME** (``ai-research-notes/2026-09-18-ch24-training-economy-WORKFLOW.md``): the **AMULET COIN** doubles trainer payouts
  and Pay Day; it is FREE from Mom in Littleroot; the Elite Four gauntlet alone is claimed to go
  **₽32,400 → ₽64,800**; and `moneyMultiplier` is set once per battle and never reset, so **any** mon
  sent out locks the ×2 — it need not be the lead or the holder for the whole fight.
  ⛔ **“NOT REFERENCED ANYWHERE IN OUR CODE” is itself a claim I have not checked** — grep first.
  ⚠ **THE GATE CHAIN IS LONGER THAN “ONE NPC”** (agent-sourced): a `VAR_LITTLEROOT_HOUSES_STATE`
  short-circuit plus `FLAG_HAS_MATCH_CALL` and `FLAG_ENABLE_MOM_MATCH_CALL` ⇒ possibly TWO
  conversations, and it is gated behind `FLAG_BADGE05_GET`. ⇒ this is a STORY ERRAND, not a pickup.
  ‼ **SEQUENCING PROBLEM TO SETTLE BEFORE BUILDING:** the bot is far past Badge 5 by §Ch23/§Ch24, so
  a fetch would be a BACKTRACK to Littleroot. Fly makes that cheap — but USER RULING 3 says Fly only
  reaches unlocked destinations. ⇒ price the round trip before committing, and weigh it against the
  ₽ it would actually recover on the REMAINING trainers (most one-time trainers are already spent by
  then — the multiplier applies to future battles only).
- [ ] ⚠ `#24-pokenavrematch` — **NEW 2026-09-18 (USER RULING 7, RESEARCH RETURNED). VERDICT: A REPEATABLE *MONEY* SOURCE, A WEAK *TRAINING* ONE. ⇒ WHAT REMAINS: a decision, not a build.**
  ⚠ **ALL AGENT-SOURCED** (``ai-research-notes/2026-09-18-ch24-training-economy-WORKFLOW.md`` §3), decomp-cited but **not verified by me**:
  * 78 rematch rows; each trainer is a ladder of **5 STATIC parties with NO level scaling, ever**.
  * ⭐ Once all four are beaten **the top team repeats FOREVER** ⇒ genuinely repeatable income.
  * ⭐ **A LOSS DOES NOT BURN THE ARMING** (`CB2_WhiteOut` branches before the rematch bookkeeping).
  * Arming needs ≥5 badges + 255 steps + a map load + a **31% roll** per registered trainer on that
    map; a FAILED roll leaves the counter at 255 ⇒ leave and re-enter for a free re-roll; ⚠ but
    entering a map where someone is ALREADY armed returns TRUE and **burns** the counter.
  ⇒ ⛔ **NOT A TRAINING ANSWER FOR §Ch24.** Static parties do not scale, so they cannot be
  level-appropriate for a L47-75 party — which is exactly what USER RULING 4 requires. It does not
  compete with Victory Road grass.
  ⇒ ⭐ **IT IS A MONEY ANSWER**, and it pairs with `#24-amuletcoin` (the multiplier applies to rematch
  payouts too). ⚠ Cost: it needs **PokeNav menu-driving**, a capability we do not have.
  ⭐⭐ **USER DIRECTIVE 2026-09-18 EXPANDS THIS INTO A LEDGER, AND SUPPLIES TWO LEADS TO VERIFY:**
  * *“you can fight other trainers you fought before again using pokenav **only after beating the
    5th gym (Norman)**”* — ✅ CONSISTENT with the agent finding of a **≥5 badges** gate on the
    arming roll, but the two are not the same statement; verify which it actually is.
  * *“re-battle **gym leaders after beating the elite 4** (entering hall of fame)”* — rows 65-72
    of the rematch table are the gym leaders, consistent with a separate, later gate. VERIFY.
  * ⭐ *“how a trainer/gym leader is determined to be battle[able] again (**does the user call
    them, or does the trainer/gym leader call the user?**)”* — the initiation direction decides
    how much PokéNav UI-driving we would need, so it is the cost question, not a detail.
  * ⭐ **THE DELIVERABLE IS A LEDGER:** *“mapping all the eligible trainers/gym leaders … where we
    can also log their pokemon, stats, rewards etc… to help us gauge **who is actually worth
    fighting again for money/xp**”* ⇒ a ranked table, not a yes/no answer.
  ⭐⭐ **RULING 9 (2026-09-18): THE LEDGER IS *TWO* ARTIFACTS, NOT ONE.** *“A bit of both, having the
  ledger from the getgo is helpful but having a sort of **‘call ledger’ to know who has actually
  called and is available to fight** would be the second piece to this.”*
  1. **THE STATIC LEDGER** — generated from the ROM/decomp: every rematchable trainer, their five
     party tiers, levels, payouts, EXP, and where they are. Complete from day one; it describes
     what the GAME CONTAINS.
  2. **THE CALL LEDGER** — written at RUNTIME: who has actually rung, and who is armed and
     fightable right now. It describes what has ACTUALLY HAPPENED in this save.
  ‼ **THEY ANSWER DIFFERENT QUESTIONS AND NEITHER SUBSTITUTES FOR THE OTHER** — the static one
  cannot know who is armed; the runtime one cannot know who is worth fighting until they call.
  ⇒ ⭐ the static table is also the **CONTROL** for the runtime log: a call for a trainer absent
  from the static table means our extraction is wrong, which is a bug we would otherwise never see.
  ⭐⭐ **RESEARCH LANDED 2026-09-18 (11 agents, 0 errors) AND THE COST ANSWER IS THE GOOD ONE:**
  **FIGHTING A REMATCH NEEDS *ZERO* POKÉNAV WORK.** The game ARMS; the player always STARTS.
  Accepting an armed rematch is *walk to the NPC, face, A, advance dialogue* — primitives we
  already have — and the armed state is readable from SaveBlock1 rather than by opening the app.
  ‼ **THAT RETIRES MY OWN EARLIER COST ESTIMATE**, which said this needed PokéNav menu-driving.
  ✅✅ **BOTH USER RECOLLECTIONS CONFIRMED:** (a) ordinary rematches gate on **FIVE BADGES** —
  confirmed in substance, with a precision correction: it is a badge COUNT, not Norman by name, and
  it is spelled **two different ways** (the walking path counts ANY five; the phone path counts a
  SEQUENTIAL PREFIX that stops at the first missing badge). They coincide in vanilla order ⇒ ‼ the
  bot's condition must be the CODE's, not the story's. (b) gym-leader rematches gate on
  **`FLAG_SYS_GAME_CLEAR`** — confirmed exactly.
  ⚠ **AND GYM LEADERS ARE FAR RARER THAN THE FIRST PASS SUGGESTED:** armed by a BATTLE counter with
  a modulo (`% 20` trainer, `% 60` wild) ⇒ ~1 arming per 65 trainer battles, not 31% per battle.
  ⛔ **A TRAP IN THE PROJECT'S OWN FAVOURITE SHAPE:** `ShouldTryRematchBattle` returns TRUE FOREVER
  once the 2nd ladder step is beaten, so talking ALWAYS takes the rematch branch and the un-armed
  case falls silently through to post-battle text. ⇒ **assert the BATTLE, or the cleared
  `trainerRematches[i]` — never the dialogue branch.** That is `CLAUDE.md` §7 arriving from the decomp.
  ⚠ **NOT VERIFIED BY ME:** the SaveBlock1 offsets (`+0x9C8`, `+0x9CA`), which the note itself marks
  INFERRED for our BPEE0 and never probed. ⛔ Probe before any code reads them.
  ⚠ **STILL AWAITING** a user decision on APPETITE — but the decision is now much cheaper than I
  described it, because only the ARMING-BY-CALL half would need PokéNav UI at all.
- [~] ✅⭐ `#24-trainingbrackets` — **PIECE 1 SHIPPED 2026-09-19 (the data foundation). ⇒ WHAT REMAINS: Piece 2 (a PER-TRAINEE ground choice + Fly traversal) and Piece 3 (the §Ch24 leg, which MUST carry a frame cap before any live selector routes a bare `train_team` at Victory Road).**
  ✅✅ **WHAT LANDED:** `TRAINING_GRASS` gains `(VICTORY_ROAD_1F, (15,39), (36,40))`; the duplicate `PENDING_GRASS` row removed; `AREA_PREREQ[VICTORY_ROAD_1F] = "region"`; `_training_area_heal_map()` gains `VICTORY_ROAD_1F → EvergrandeCity`; **new gate #66** `probe_picker_allow_required.py`. Predictions pre-registered at `3c044a0d`. ⇒ **closure-reasons (i) “a third guard is needed” and (ii) “no heal-map row” are RESOLVED by this commit** — they are struck from the list below.
  ⛔⛔ **AND A TIER 1 REVIEW FOUND A THIRD CONSUMER I HAD MISSED, WHICH REFUTES PREDICTION P7.** `_hm_hunting_grounds` (`early_game.py:4813-4866`) iterates `TRAINING_GRASS` with **no** `AREA_PREREQ` check, and `ensure_hm_learner` orders candidates `reversed(grounds)` — *furthest-progressed first* — so the new row became an EARLY candidate for Cut/Surf/Strength/Rock Smash hunts, every one a PRE-Badge-8 errand. ‼ The concrete hazard was closed only by ACCIDENT (`calculate_path` refuses Victory Road as warp-only reachable), which is not a guard. ✅ FIXED here with a named `_HM_HUNT_EXCLUDED` set + the reasoning for why a prereq filter or a live reachability check would each be wrong.
  ⛔⛔ **I CLOSED THIS ON 2026-09-18 AND ONE OF MY FIVE REASONS DID NOT SURVIVE THE RULING.** Reason (2) was *“the remedy already ships — §Ch23 already grinds on that exact tile”*. ✅ True of §Ch23's HARDCODED call; ⛔ **false of the per-trainee selector the ruling requires**, which does not exist and cannot work without the promotion. ‼ **“No current caller needs it” is not “no requirement exists”** — see `08-MISTAKES.md` 2026-09-19.
  ✅ **MEASURED, AND IT IS THE WHOLE ARGUMENT:** from Ever Grande the 4-hop budget (`_MAX_TRAINING_TRAVEL_LEGS`) refuses **every** route ground — ROUTE121 **6** hops, ROUTE118/119 **9**, ROUTE111/117 **11**, ROUTE115 **15**. `VICTORY_ROAD_1F` is **1 hop** and is the only candidate in budget. ⇒ **without the promotion a per-trainee selector returns `None` for every trainee.**
  ⭐ **AND THE PROMOTION NOW EARNS ITS KEEP FOR A REASON IT DID NOT HAVE BEFORE:** it supplies the **L34-46 bracket**, which is exactly where the battlers sit. Measured today: with a permissive predicate the current table answers **ROUTE121 (25-28) for every trainee from L36 to L65** — a **+37** gap at L65, the same defect the original ruling named.
  ⛔ **TWO CONSTRAINTS REMAIN FOR PIECES 2-3; TWO ARE NOW RESOLVED.** ~~(i) a third guard is needed~~ ✅ **DONE — gate #66**, structural rather than behavioural because the obvious assertion is self-refuting (✅ reproduced: it returns VICTORY_ROAD_1F from L35 up) and narrowing the default is refuted (✅ measured: 83 of 99 levels change, all worse). ~~(ii) no heal-map row~~ ✅ **DONE** — `VICTORY_ROAD_1F → EvergrandeCity` added, which was NOT optional (two consumers fall back to the boss's own centre on a miss). **STILL OPEN:** (iii) `_exit_training_cave_if_inside()` no-ops for it (absent from `_CAVE_EXITS`); (iv) a bare `train_team` has **no frame cap**, only a 500-round guard — KI-28's 19.9M-frame shape. Full working: `ai-research-notes/2026-09-18-trainingbrackets-CLOSED.md` (its reason 2 is now superseded; the rest stands). Full write-up, all five reasons: `ai-research-notes/2026-09-18-trainingbrackets-CLOSED.md`.
  ✅ **(1) MEASURED BY ME — THE DEFECT IS A CALL SHAPE PRODUCTION NEVER MAKES.** `best_training_area(53) → ROUTE117 (13,14)` is real **only at `allow=None`**, because every higher-band row carries an `AREA_PREREQ` (`ROUTE111:"region"`, `ROUTE115/118/119/121:"surf"`) and the conservative default skips exactly those. With a real predicate the SAME table answers `ROUTE121 (25,28)` for L30+. ✅ And all four production callers pass one: `counter_hunt.py:647`, `story_mode.py:2659`, `:3168`, `:3199`.
  ✅ **(2) VERIFIED AT SOURCE — §Ch23 ALREADY GRINDS ON THE PROPOSED TILE.** `victory_road.py:2087-2090` calls `train_team(target, slots={0}, grass=TRAIN_SPOT_1F, heal_center=PokemonCenter.EvergrandeCity)`, and `TRAIN_SPOT_1F = (VR1F, (15,39))` (`:477`) is the identical tile. ⇒ promotion unlocks nothing; it re-routes a working hardcoded path through a generic picker that lacks its supports.
  ⛔ **(3) THE PROPOSED REGRESSION GATE WAS SELF-REFUTING — ✅ REPRODUCED BY MY OWN EXECUTION, not taken on an agent's word.** Adding the row in memory (with the `AREA_PREREQ` row too): `best_training_grass(allow=None)` returns **VICTORY_ROAD_1F(15,39) for L35, L40, L53 and L75** — so the assertion is false from **L35 up**, not merely at the L40 the gate named. Meanwhile `best_training_area(allow=None)` stays ROUTE117 throughout, which is the asymmetry exactly: the prereq row protects ONE picker and not the other (`training_areas.py:213-219`, deliberate).
  ‼ **AND A NUANCE THE ITEM NEVER NOTICED: the two pickers ALREADY DISAGREE TODAY.** With no change at all, `best_training_grass(allow=None)` answers **ROUTE121** while `best_training_area(allow=None)` answers **ROUTE117** — because only the latter honours `AREA_PREREQ`. ⇒ the “conservative default” is a property of ONE function, never of the table.
  ⛔ **(4) THE GENERIC PATH LACKS THE SUPPORTS:** no `VICTORY_ROAD_*` row in `_training_area_heal_map()`; `_exit_training_cave_if_inside()` no-ops (absent from `_CAVE_EXITS`); and a bare `train_team` has **no frame cap**, only a 500-round guard (`early_game.py:2322`) — KI-28's 19.9M-frame shape. See `#24-healmapfallback`.
  ⛔ **(5) THE CODE ALREADY WARNED AGAINST IT** — `victory_road.py:3425-3429` names “training elsewhere” as one of five MEASURED-WRONG entries and demands an adversarial pass first. It got one; it was refuted.
  ⭐⭐ **AND THE RULING IS ALREADY SATISFIED:** §Ch23 trains a ~L47 party on L36-40 wilds (~1.2× gap). The bracket map the ruling asks for EXISTS at `training_areas.py:27-61`, and was **independently re-corroborated dual-source today** (pret decomp + our own live-ROM `cache/encounter_index_BPEE0.json`; 38 rows diffed, **zero mismatches**). ⛔ **L55+ is NOTHING; the highest level on any table by any method anywhere is 50, and both tables reaching it are unusable.** ⇒ no wild grind reaches L62-75 at a sane rate.
  ⇒ **WHAT ACTUALLY REMAINS IS `#24-levelgap`** — a purpose-built §Ch24 stepped leg driving `train_team(..., grass=TRAIN_SPOT_1F)` with its own MEASURED budget. Already the ruling; this item was the wrong road to it.
- [ ] ⚠ `#24-p7reachincave` — **NEW 2026-09-18. P7 — *“nothing consults reachability while the bot is inside Victory Road”* — IS STILL **UNTESTED BY MEASUREMENT** AFTER TWO ATTEMPTS. ⇒ WHAT REMAINS: answer it with a HARNESS DRIVER, not a bare generator loop.**
  ⭐ **WHY IT MATTERS:** the `#24-waterfallcap` fix measurably changed one thing — standing INSIDE Victory Road, `best_training_area(allow=_counter_area_allowed)` goes `None → ROUTE121`. P7 claims no production path can ask from in there. ✅ A caller census supports it structurally (every boss segment is gated `if not _done("BADGEnn_GET")` and runs pre-Badge-8, when the Waterfall gate is False anyway; §Ch23's own dispatcher never calls back into `_prepare_for_fight` / `best_training_area` / `decide_maintenance`). ⚠ **That is a census, not a measurement, and it is an ABSENCE claim.**
  ⛔ **TWO MEASUREMENT ATTEMPTS, BOTH CORRECTLY REFUSED BY THE PROBE'S OWN VACUITY GATE** (`probe_p7_reach_calls_in_cave.py`, evidence `evidence/2026-09-18-p7-reach-calls-in-cave.stdout.txt`): **(1)** wrong fixture — `grind_stall_ppzero.ss1` is saved MID-BATTLE (`game_state=BATTLE`, `controllable=False`, stable 1200+ frames), so `train_team`, an OVERWORLD entry point, raised *“Cutscene did not end after 8000 frames”*. **(2)** right fixture (`post_grind_L60.ss1`, overworld at `(15,39)`), wrong DRIVER — a bare `next(gen)` loop advances the generator but provides **no battle handling**, so the spin found an encounter in **~425 frames** and the run then sat in that unfought battle for the remaining ~89,000.
  ⭐⭐ **WHAT THE FAILURES DID PROVE, AND IT IS WORTH MORE THAN THE PROBE:** both runs would have printed *“no reachability calls inside Victory Road — P7 CONFIRMED”* had the vacuity gate not refused, because **an arm that never runs produces exactly the silence the hypothesis predicts.** The probe now also self-diagnoses the stuck-in-battle case by name.
  ✅ **AND ONE INCIDENTAL DATUM WORTH KEEPING:** the spin at `TRAIN_SPOT_1F (15,39)` produced a wild encounter within **~425 frames**, corroborating that tile as productive grind ground independently of `has_encounters`.
  ⇒ **HOW TO ACTUALLY ANSWER IT:** add a `story_harness.py` driver that grinds at `TRAIN_SPOT_1F` with the harness's real battle handling, wrapping the four `region_reach` entry points to log caller + player map per call. ⚠ A clean result would be evidence about **the grind loop only** — `_prepare_for_fight`, a counter hunt and whiteout recovery have their own entry conditions and stay the census's job.
- [~] ✅⛔ `#24-ladderleak` — **THE MECHANISM NOW EXISTS AND IS UNWIRED (2026-09-19). ✅ `best_training_area` gained an optional `max_wild_max` — pass `mon.level + 1` and the trainee always out-levels its wilds. MEASURED: that closes **all 9** leaking rungs and leaves no level without a ground. ⛔ **NOTHING CALLS IT YET** — the leg that will is Piece 2/3, and a Fly-aware predicate must NOT ship before the traversal (it would admit ROUTE115, 15 walking hops, with no frame cap). ⇒ WHAT REMAINS: wire it in the leg.** *(original filing follows)* **MEASURED. THE LEVEL-APPROPRIATE LADDER HAS **9 LEAKING RUNGS**, AND AT EACH ONE THE L65-75 RULING'S MECHANISM SILENTLY STOPS WORKING. ⇒ WHAT REMAINS: Piece 2's selector must require the trainee OUT-LEVELS its band, not merely sit closest to it.**
  ⭐ **WHY THE RULING WORKS AT ALL, AND WHY THAT IS FRAGILE.** `SwapTrainBattleStrategy.UNDERLEVEL_MARGIN = 2`: the swap fires when `trainee + 2 <= foe`, putting TWO participants in the battle so the FINISHER banks an equal share — the mechanism that drove Wailord to a computed **L89**. A trainee that OUT-levels its wilds solos for full xp as the only participant, and the ceiling survives. ⇒ the ruling is a mechanical fix, and it holds **only on rungs where the trainee is above the band**.
  ⛔ **MEASURED** (`probe_training_ladder.py`, evidence `evidence/2026-09-19-training-ladder.stdout.txt`; pure table arithmetic, no ROM). Walking L10→L75 and asking `best_training_area` at each level, **9 rungs leak: L12, L18-L20, L24, L35-L38.** The selector minimises `abs(hi - team_level)` — it finds the CLOSEST band, which is not the same as one the trainee beats.
  ‼ **APPORTIONING THIS HONESTLY:** L12 / L18-20 / L24 are **PRE-EXISTING** — that is how the ladder has always behaved and nobody had measured it. **L35-L38 is the window the 2026-09-19 Victory Road promotion opened**, because the next band up jumped from ROUTE121's `(25,28)` to `(36,40)`. ⇒ the promotion did not create the defect class; it added one instance of it.
  ⭐⭐ **THE FIX BELONGS IN PIECE 2 AND IS NAMED:** the selector must be asked for a band the trainee out-levels (`trainee >= hi - 1`), accepting a LOWER band when none qualifies. ⛔ The alternative — take the closest band and check the ceiling afterwards — **is exactly the shape that produced the L89 finisher**, so it is refused in advance.
  ⚠ **WHAT THE MEASUREMENT DOES NOT COVER:** slot weights (which wild is actually drawn), the trainee's HP, and the SECOND swap trigger (*can't continue* — low HP after a close fight). It answers the UNDER-LEVELLED trigger only, which is the one the ruling is about. ⇒ a clean ladder is not a promise of zero swaps.
- [ ] ⭐⭐ `#25-partyroster` — **NEW 2026-09-23 (USER DIRECTIVE). FISHING AS AN HM-CARRIER SOURCE, A FULL SIX-MŌN TEAM, AND WORKING PC SWAPS — FILED AS **ONE** ITEM BECAUSE THEY ARE ONE PROBLEM. ⛔ GATED: EXPLICITLY AFTER §Ch24, BY THE USER'S OWN FRAMING (*“slated as something we focus on later”*). ⇒ WHAT REMAINS: everything — nothing here is started.**
  ⭐ **THE DIRECTIVE, VERBATIM:** *“when looking for a surf/dive/waterfall hm user or even a water type pokemon, we need to make the bot have more options because if we get the fishing rods we can use the best fishing rod we have at the moment to get a better/higher level water pokemon from different parts of the world… along with unlocking the team from 4 pokemon to 6 and validate/wire/improve the pokemon pc mechanics so the bot can catch pokemon and swap them around between the team and pc like a normal human would do organically.”*
  ⭐⭐ **THE SYNTHESIS, AND IT IS WHY THIS IS ONE ITEM: THE TEAM IS NOT CAPPED AT 4 BY A CONSTANT — IT IS HELD BELOW SIX ON PURPOSE, BECAUSE THE PC DOES NOT WORK.** ✅ Verified: `PARTY_CAPACITY = 6` already (`story_mode.py:1500`). The effective limit is a **RUNWAY RESERVATION** — post-Badge-1 a dex catch is REFUSED whenever `party_slots_used < PARTY_CAPACITY` (`story_mode.py:1664`), because *“the empty slots are the runway HM and counter catches land on”*. ⇒ **fix the PC and the reservation stops being necessary; leave the PC broken and raising the team to six re-creates the failure the reservation prevents.**
  ⛔ **THE MEASUREMENT THAT PUT THE RESERVATION THERE — DO NOT REMOVE IT BLIND.** `#24-partycap` measured a finish rate of **52.0% → 15.8%** when the early party is disturbed, *“the ENTIRE loss on one badge rung”*, with **10 of 16 non-finishes** being literally *“No party mōn can learn Surf and the party is full”*. ⇒ that failure string is the directive's own motivation, arriving from the opposite direction.
  ✅ **AND THE PC IS ALREADY KNOWN-BROKEN IN TWO INDEPENDENT WAYS** (`#24-pcoverflow`, recorded at `pc_trip.py:370`): a `getattr(..., lambda: [])` fallback made `box_views()` raise on every call so `find_in_box` could never find anything (*“withdrawing LOGGED 0 IN EVERY BATCH”*), and both catch-on-sight branches still required `party < 6` so a full-party catch never happened. ‼ The defensive fallback **disguised** the first bug by looking like safety.
  ⭐ **WHAT ALREADY EXISTS AND SHOULD NOT BE REBUILT:** a `fish()` primitive (`modules/modes/util/higher_level_actions.py:325`); rod identities in `modules/safari_strategy.py`; and a standalone one-slot deposit, `deposit_one_dead_weight` (`pc_trip.py:219`), which is NOT behind the pinned-0 `POKEBOT_PC_ROTATION` and HAS fired in real batch runs.
  ⚠ **TWO GOTCHAS ALREADY MEASURED IN THAT DEPOSIT PATH** — whoever builds this inherits them: it returns **True having deposited nothing** when the party is already under six (`pc_trip.py:274`), and victim choice sorts **ascending by level** (`team_policy.py:173`, `find_dead_weight`'s `found.sort(...)`), so a caller **cannot name** which mōn to box.
  ⭐⭐ **AND THE DIRECTIVE SOLVES A SINGLE POINT OF FAILURE I MEASURED ON 2026-09-18:** on the pinned §Ch24 party, **Waterfall AND Dive are held by exactly one mōn (Wailord)** and Fly by one (Swellow) — `evidence/2026-09-18-party-l65-audit.stdout.txt`. Losing Wailord strands the run. ⇒ a fishing-sourced water mōn is not a convenience; it is **redundancy for the two moves §Ch24's geography depends on.**
  ⇒ **SUGGESTED ORDER WHEN IT IS TAKEN UP (not decided):** (1) prove the PC round trip — deposit AND withdraw a NAMED PID — with a drive, since `#24-pcoverflow` shows the withdraw half has never worked; (2) only then relax the runway reservation, and re-measure the `#24-partycap` finish rate to confirm the 52%→15.8% collapse does not return; (3) add fishing as an HM-carrier source, best-rod-first. ⛔ Doing (2) before (1) is the documented failure.
- [~] ⚠⭐ `#24-flyladder` — **NEW 2026-09-23. ⛔⛔ ITS FIRST WRITE-UP WAS CORRECTED THE SAME DAY: I PUBLISHED “5 OF 6 LAST MILES WALKABLE” AND THE MEASURED ANSWER IS **3 OF 6**. ✅✅ **PIECES 2b AND 2c ARE SHIPPED, TOGETHER, AND THE DISJUNCT IS PROVEN LOAD-BEARING (5 of 6 rungs are admitted by Fly ALONE). ⇒ WHAT REMAINS: PIECE 3 — the §Ch24 leg, which MUST carry a frame purse (`_yield_bounded_by_frames`); a bare `train_team` has no frame cap, only a 500-round guard (`early_game.py:2322`), which is KI-28's 19.9M-frame shape.**
  ✅⭐ **PIECE 2b — THE FLY DISJUNCT** (`story_mode.py`, in `_training_area_allowed`): the predicate now returns yes if `is_map_reachable(area, max_hops=4)` **OR** `can_fly_to_anchor(heal_centre)`. ⛔ **The walking oracle is UNTOUCHED and `calculate_path` is deliberately NOT used** — see the decision in `06-DECISIONS-LOG.md` 2026-09-23.
  ✅⭐ **PIECE 2c — THE FLY TRAVERSAL** (`early_game.py`): `_goto_training_area` gained an optional `heal_center` and now calls `_fly_to_training_anchor` first. Four ordered guards (no anchor / already on the map / already in the anchor town / cannot fly) and it **never raises** — a missing HM degrades to walking, it does not kill the run. ✅ **REGRESSION GUARD MEASURED:** with `heal_center=None` the generator yields **0** steps, so every pre-existing caller is behaviourally identical.
  ⭐⭐ **THE PROOF, AND IT IS AN A/B WITH A NEGATIVE CONTROL** (`probe_fly_disjunct.py`, **now gate #68**, evidence `evidence/2026-09-23-fly-disjunct.stdout.txt`): on `post_ch24_atdoor_L75.ss1` the walking oracle refuses **ROUTE117, ROUTE111, ROUTE115, ROUTE118 and ROUTE121** at the 4-hop budget and admits only VICTORY_ROAD_1F ⇒ **5 rungs flip NO→YES on Fly alone.** On `post_grind_L60.ss1` (no Fly knower) **nothing extra is admitted** — the control holds. ‼ The gate FAILS if zero rungs flip, so it cannot go green by the feature being unnecessary.
  ⛔⛔ **THE FOURTH GUARD — CAUGHT BY AN ADVERSARIAL REVIEW BEFORE IT SHIPPED, AND IT WAS THE SEVERE ONE.** `fly_to_destination` has **FOUR** guards, not three: **the map you are STANDING ON must allow Fly** (`Route/Town/City/Ocean Route` only — `Underground`, `Indoor` and `Underwater` are refused, `src/overworld.c` `Overworld_MapTypeAllowsTeleportAndFly`). My `can_fly_to_anchor` claimed to mirror “three guards EXACTLY” and omitted it. ‼ **`pokemon_league.py:1237` literally calls that omission out in its own source** — *“THE FOURTH GUARD, AND THE ONE THIS FUNCTION SHIPPED WITHOUT”* — and names the measured case: the §Ch24 party sits at **VICTORY_ROAD_1F, `map_type=Underground`**, which is this ladder's own grind tile. ⇒ the predicate would have admitted a far area on a Fly that cannot happen, the fly would raise, the traversal would degrade to WALKING, and the bot would walk 11-15 hops on a frame-capless `train_team` — **KI-28's 19.9M-frame shape, the exact outcome this feature's own comments forbid.** ✅ FIXED: the allow-list is **hoisted to module scope and shared** (`_FLY_ALLOWED_MAP_TYPES` + `fly_is_legal_from_current_map()`), never copied.
  ✅⭐ **AND A BACKSTOP, BECAUSE A GUARD THAT ONLY REFUSES IS NOT ENOUGH:** when `_fly_to_training_anchor` cannot fly, it now asks the SAME 4-hop walking oracle the predicate used. Walkable ⇒ walk (the ordinary heal-return case — a Poké Center is `Indoor`, so Fly is illegal there, but the grind tile is two hops away). **NOT walkable ⇒ raise `UnreachableDestinationError`**, which the caller already handles by blocklisting the area and running normal derail recovery. ⇒ a loud, recoverable refusal instead of a silent multi-million-frame trek.
  ⛔⛔ **AND A SECOND DEFECT IN MY OWN BACKSTOP, CAUGHT BY A PROMOTION-SAFETY REVIEW: THE REFUSAL WAS CATCHING ITSELF.** `_fly_to_training_anchor`'s `raise UnreachableDestinationError(...)` sat **INSIDE** the `try` whose own `except Exception as error:` caught it, and `reraise_if_aborting` re-raises **only** when the story-abort latch is set (`early_game.py:161`) — i.e. only after a whiteout. ⇒ on every ordinary run the refusal was **swallowed**, the generator returned, and `_goto_training_area` fell straight through to the walk. **The backstop I had just added to prevent the KI-28 trek was INERT.** ✅ FIXED: an `except UnreachableDestinationError: raise` clause ahead of the broad handler. ✅ PROVEN: the error now reaches the caller, and a walkable target still degrades silently.
  ✅⭐ **GATE #69 (`probe_flyanchor_refusal.py`) NOW GUARDS IT, BECAUSE NOTHING DID.** #68 exercises the PREDICATE; the TRAVERSAL was unexercised, which is exactly how this shipped. Two arms: **A** refusal propagates when it must, **B** a walkable target still degrades quietly. ‼ Arm B is not decoration — a “fix” that re-raised unconditionally would pass A and break every heal-return (a Poké Center is `map_type=Indoor`, so Fly is *always* illegal there while the grind tile is two hops away). Fault-tested: with `POKEBOT_FLYREFUSAL_FAULT=1` it fails **arm A only**, arm B staying green — a discriminating result. No emulator; pure control flow.
  ⛔⛔ **AND A THIRD DEFECT IN THE SAME HELPER, FROM THE SAME REVIEW: GUARD 3 COMPARED THE MAP, AND EVER GRANDE IS SPLIT BY TERRAIN.** §Ch23's last leg (`heal_at_league`) deliberately leaves the bot at **`EVER_GRANDE_CITY (18,6)`**, the League plateau (`victory_road.py:374` `LEAGUE_DOOR_APRON`). That is the **same map** as the Poké Center landing (27,49) — and `calculate_path` between them is **NO PATH IN BOTH DIRECTIONS**, measured (`evidence/2026-09-18-vr-heal-roundtrip.stdout.txt`, control at (18,42) = 23 wp, so the refusal is a real reachability answer). ⇒ a map-level guard says *“already in the anchor town”* and **skips the Fly — at the exact tile the previous chapter hands over, where Fly is the only way off the plateau.** ✅ FIXED: guard 3 now compares the **TILE**. Flying to a town you already stand in is legal and is exactly what we want — it NORMALISES position onto the landing tile every measured last mile starts from. ✅ Pinned by gate #69 **arm C**, with **arm C'** proving the tile guard still short-circuits when we ARE on the landing (without C', *“fix it by always flying”* would pass every other arm and make guard 3 dead code).
  ‼ **THE RULE THIS EARNS: A GUARD PLACED INSIDE THE HANDLER THAT CATCHES IT HAS BEEN WRITTEN BUT NOT INSTALLED** — and no check in this tree could see the difference until #69 existed.
  ✅ **GATE #68 IS FAULT-TESTED** (`POKEBOT_FLYDISJUNCT_FAULT=1` stubs the Fly oracle to always say NO): happy path **exit 0**, fault arm **exit 1** reporting *“VACUOUS: NOT ONE rung was admitted by Fly alone”*. Evidence `evidence/2026-09-23-fly-disjunct-FAULT.stdout.txt`. ‼ Without this arm a green #68 proved nothing — the gate guards a **silent** failure.
  ⚠ **A LATENT TRAP THE REVIEW FOUND, INERT TODAY, WORTH KNOWING:** the “LEVEL-APPROPRIATE RELOCATION” branch (`story_mode.py:3167-3275`) calls `train_team` through this same predicate with **no frame budget**, unlike its sibling top-up branch which gates on `MAX_PREP_TRAINING_FRAMES`. It is dead code today — all five boss configs carrying a `"grass"` key are pre-Badge-6, and `can_fly_to_anchor` fails closed on BADGE06 — but **a future post-Badge-6 config with a `"grass"` key would inherit the KI-28 shape.** Not fixed; named.
  ⚠ **WHAT PIECE 2 DOES NOT DO, STATED SO PIECE 3 DOES NOT ASSUME IT:** it does not bound the grind in frames, does not measure trainer sight cones on the approach, and does not prove the traversal in a DRIVE — the predicate and its oracle are flag/graph questions and that is all that is measured here.**
  ⭐ **THE LADDER IT SERVES** (measured under the out-level cap, `probe_training_ladder.py`): ROUTE117 L15-20 → ROUTE111 L21-24 → ROUTE115 L25-26 → ROUTE118 L27 → ROUTE121 L28-38 → VICTORY_ROAD_1F L39-75. ‼ Each ground is anchored at its **heal centre**, not its nearest town.
  ✅ **(1) EVERY ANCHOR TOWN IS UNLOCKED — AND THE FIXTURES DISAGREE ABOUT FLY, SO NAME THE FIXTURE** (`probe_fly_unlocked.py`, evidence `evidence/2026-09-23-fly-unlocked-v2.stdout.txt`). All six region-map flags are set on **all four** pinned fixtures. Fly itself: ✅ `post_ch24_atdoor_L75.ss1`, ✅ `post_ch24_atdoor.ss1`, ⛔ `post_grind_L60.ss1` (no Fly knower **and** `map_type=Underground`), ⛔ `post_league_lobby.ss1` (**`map_type=Indoor`** — the party CAN fly, it just cannot fly *from there*). ⇒ **2 of 4, not 3** — an earlier draft of this entry said 3, because the probe graded only three of `fly_to_destination`'s FOUR guards. That is not a hole in the ladder (a mid-grind save predates the Fly carrier); it **is** a hole in any sentence that says “on the pinned fixtures”.
  ⛔⛔ **(2) ONLY THREE OF SIX LAST MILES ARE WALKABLE ON FOOT** (`probe_lastmile_paths.py`, evidence `evidence/2026-09-23-lastmile-paths-v2.stdout.txt`), measured from the **real Fly landing tiles** and with swimming explicitly disabled:
    ✅ **WALKABLE:** ROUTE117 **47 wp** (clean), ROUTE111 **220 wp** via `FALLARBOR_TOWN → ROUTE113 → ROUTE111`, ROUTE121 **81 wp** (clean).
    ⛔ **SURF-ONLY — ROUTE115 and ROUTE118.** Both return **NO PATH** with `no_surfing=True`. Their v1 “passes” were the planner swimming: ROUTE115 crosses **9 water tiles / 1 Surf step**, ROUTE118 **15 water tiles / 1 Surf step**. ⇒ the bot lands on foot; these are **not** walkable last miles. ✅⭐ **BUT THEY ARE STILL TRAVERSABLE, AND THAT IS NOW CHECKED RATHER THAN HOPED:** the production walker executes a Surf mount (`walking.py:221` and `:304` handle `WaypointAction.Surf`), and **no caller anywhere passes `no_surfing`**, so production pathing already permits swimming. `can_surf()` requires `BADGE05_GET` plus a party Surf knower (`map_path.py:787`) — both hold on the §Ch24 party. ⇒ the two rungs are reachable; what changes is the **cost**, not the feasibility.
    ⚠ **THE TWO COSTS THAT COME WITH THAT, NEITHER MEASURED:** (1) a surfing leg draws **water encounters**, whose levels are unrelated to the land table the rung was chosen for — a L25 trainee crossing water is not in a L25 fight; (2) it makes the ladder **depend on Wailord**, the sole Surf/Dive/Waterfall carrier already logged as a single point of failure in `#25-partyroster`. ⇒ prefer a land rung where one exists; do not treat these two as equivalent to the walkable three.
    ✅⭐ **AND THIS CONFIRMS THE TABLE RATHER THAN CONTRADICTING IT — THE CODEBASE ALREADY KNEW.** `AREA_PREREQ[ROUTE115] = "surf"` and `AREA_PREREQ[ROUTE118] = "surf"` (`training_areas.py:320-321`), and `_training_area_allowed` already refuses both unless `_party_can_surf()`. ‼ **The spin tiles themselves are WATER**: the final waypoint of each path IS (29,15) / (6,53). These are surf spots, not land patches with a wet approach — which is why arm B returns NO PATH, and that is CORRECT behaviour, not a ladder defect. ⇒ two independent instruments agree, so treat this as **corroboration**, and do not file it as an open problem.
    ⚠ **VICTORY_ROAD_1F — NO PATH in either arm**, the expected warp case: its entrance is a **door warp** (`victory_road.py:132`) and `calculate_path` cannot use warps while `navigate_to_anywhere` can — proven by the `ch24caveheal` drive, both directions.
  ⭐ **THE REAL LANDING TILES ARE NOW KNOWN, AND THE REPO ALREADY HELD THE RULE.** Every anchor's Fly landing is exactly its Poké Center door **+ (0,+1)** — verified 6/6 against `pret/pokeemerald:src/data/heal_locations.json`. `victory_road.py:147-148` derives `EG_PC_APRON` that way already. ⛔ **Do NOT path from the door itself**: it is a WARP, and `calculate_path` follows a warp used as an endpoint, so a leg computed from it can resolve *inside* the Poké Center.
  ⚠ **ROUTE111's WALK FIRES EXACTLY ONE REAL SCRIPT — AND THE FIRST COUNT HERE WAS WRONG.** Its 220-wp path crosses **1 of the 10 genuinely-armed coord-event triggers**: **(13,43), `VAR_TEMP_3`** — the decomp's `Route111_EventScript_ViciousSandstormTriggerLeft` (`data/maps/Route111/scripts.inc:176`), which checks `ITEM_GO_GOGGLES` and lets a holder pass. `avoid_scripted_events` is a `cost += 10000` **penalty, not a wall** (`map_path.py:1034-1037`), so the planner returns such a path and a walker fires it. ⛔ An earlier draft of this entry said *“3 of 34”*; 24 of that 34 are **phantoms** and 2 of the 3 crossings were phantom hits — see `#24-phantomtrigger`.
  ⭐ **ROUTE111 IS STILL THE RIGHT ANCHOR, ON A CORRECTED NUMBER.** It is the most-failed training walk in the corpus — **183 of 289** logged *“not reachable — dropping it”* events (63.3%, 3× the next map; re-derived from `PROJECT KNOWLEDGE/batch-evidence/*/`). ⛔ An earlier draft of this entry said **1,041**; that figure is **not reproducible** from this corpus and is withdrawn. Its nearest town is Mauville, the wrong side of the Go-Goggles desert; its heal centre is Fallarbor, and from Fallarbor the path exists. ⇒ anchoring on `_training_area_heal_map()` rather than proximity is correct by measurement.
  ⛔⛔ **THE BLIND SPOT NO ARM ABOVE CAN SEE — TRAINER SIGHT CONES.** `avoid_scripted_events` consults ONLY `on_enter_event_triggers`; spotting is a per-frame scan in the decomp's `trainer_see.c`. The planner is **structurally blind** to it and `victory_road.py:2765-2770` hardcodes a bypass waypoint to work around it. ⇒ a clean walk above is **not** a battle-free walk, and these are trainer routes.
  ⛔ **AND THE BUILD ORDER IS NOT OPTIONAL:** the Fly-aware `allow` predicate and the traversal helper **must land in the same commit**. A Fly-aware predicate shipped alone admits ROUTE115 — **15 walking hops** from Ever Grande — and the bot would try to WALK it, on a bare `train_team` with no frame cap.
- [ ] ⛔⭐ `#24-phantomtrigger` — **NEW 2026-09-23, MEASURED, NOT YET FIXED. `calculate_path` PENALISES 24 ROUTE111 TILES BY +10000 EACH ON THE STRENGTH OF A READ FROM A **NEGATIVE** SAVE-BLOCK OFFSET. ⇒ WHAT REMAINS: decide the guard, then measure whether any route actually changes.**
  ⭐ **THE CHAIN, EVERY LINK VERIFIED AT SOURCE.** (1) `MapCoordEvent.trigger_var_number` is `unpack_uint16(...) - 0x4000` (`map.py:605-607`). (2) A `TRIGGER_RUN_IMMEDIATELY` coord event stores **0**, so its var number comes out as **-16384**. (3) `get_event_var_by_number` computes `vars_offset + (var_number * 2)` with **no guard** (`memory.py:400-408`) — for Emerald that is `0x139C - 32768`. (4) ‼ **MEASURED 2026-09-23: that call raises nothing and returns `0`**, which equals the event's `trigger_value` of 0. ⇒ the tile reads **ARMED**.
  ⛔ **AND THE PRODUCTION PLANNER MAKES EXACTLY THIS COMPARISON** (`map_path.py:1034-1037`), so this is not a probe artefact. **MEASURED on ROUTE111: 34 coord events — 24 with a negative var number, all 24 comparing EQUAL and therefore penalised +10000; only 10 are genuinely armed.** The 24 are the ambient `SandstormTrigger`/`SunTrigger` weather tiles, which are harmless to walk over.
  ⭐ **WHY IT PLAUSIBLY MATTERS HERE, STATED AS A HYPOTHESIS AND NOT A FINDING.** ROUTE111 is the most-failed training walk in the corpus (**183 of 289** drop events, 63.3%). A spurious +10000 on 24 of its tiles distorts routing across exactly that map. ⛔ **NOT MEASURED: whether any route actually differs with the guard in place.** Do not write the causal sentence until an A/B says so — a +10000 penalty is survivable when no cheaper route exists, which is precisely why `victory_road.py:162-168` documents the planner walking through a penalised tile anyway.
  ⚠ **THE FIX IS ONE LINE AND STILL NEEDS A DECISION:** skip the comparison when `trigger_var_number < 0` (in `map_path.py`, where the penalty is applied) **or** guard `get_event_var_by_number` itself. The latter is broader — it protects every caller — but changes a shared primitive, so it needs its own A/B. ‼ `map_path.py:113` already excludes `type == "weather"` from the trigger table; these 24 slip through because our reader does not type them as weather.
  ✅ **HOW IT WAS FOUND:** a trainer-sight-cone recon agent flagged the negative offset as an INFERRED latent defect; it was then confirmed live here. ⇒ the agent's note was a lead, and the measurement is the evidence — the standing rule working as intended.
- [x] ✅✅ `#24-swaptrigger2` — **MEASURED AND CLOSED 2026-09-23. ALL SIX PRE-REGISTERED PREDICTIONS CONFIRMED; THE LADDER WORKS AND USER RULING 12 IS ACHIEVABLE. ⇒ PIECE 3 IS UNBLOCKED.** `--driver ch24swaptrigger`, `ACCEPTANCE: PASS`, all 7 readings, `missing=[]`, **29 battles, 0 whiteouts**. Evidence `evidence/2026-09-23-ch24swaptrigger.stdout.txt`; predictions pre-registered in commit `0218e7e6` BEFORE the run.
  ⭐⭐ **THE HEADLINE (P3): trigger 2's HP half fired ONCE IN 29 BATTLES — 3.4 %**, against a prediction of <10 % and a falsifier of ≥25 %. The trainee **soloed 28 of 29 battles**.
  ⭐ **AND THE EXP LEAK IS NOW A MEASURED NUMBER, NOT A MODEL:** trainee banked **4,716** exp; **one** other mōn banked **108** ⇒ the leak is **2.2 %**. The ladder's thesis — a level-matched trainee keeps its own exp — is confirmed by direct observation.
  ✅ **P1** trigger 1 (`underleveled`) fired **0** times — the out-level cap is structural, as designed. **P4** the one finisher chosen was **slot 4, Wailord L75** — `_capable_finisher` takes the strongest, as read. **P5** **162.6 xp/battle** measured vs 143.4 modelled (+13 %), so `_CALIBRATED_AVG_WILD_BASE_EXP_YIELD` is sound at this band.
  ⭐⭐ **P6 — AND THIS IS THE SEPARATE PRIZE: THE FLY LEG WORKS IN A DRIVE, FROM THE PLATEAU.** The run started at `EVER_GRANDE_CITY (18,6)` — the League plateau — flew to `VERDANTURF_TOWN (16,4)`, and walked to `ROUTE117 (31,16)`. ‼ That is the exact case the guard-3 TILE fix exists for: a map-level guard would have called (18,6) *“already in the anchor town”* and skipped the Fly, stranding the leg where §Ch23 hands over. ⇒ **this is the DRIVE verification `promote.py` asked for after the promotion**, and it also validates `fly_landing_tile` end to end — the bot landed on exactly the door+(0,+1) tile the decomp predicted.
  ⚠⚠ **WHAT THIS DOES NOT ESTABLISH — READ BEFORE QUOTING 3.4 %:**
    • **ONE trajectory, 29 battles.** A single firing gives a wide interval (Wilson 95 % ≈ 0.6-17 %). It REFUTES the ≥25 % falsifier decisively; it supports “<10 %” only weakly.
    • **ROUTE117 only.** The real climb spends **822 of ~1,055 battles on ROUTE121** against L38 foes. HP pressure there is a different question and this result does **not** transfer.
    • ⛔⛔ **AND P2 IS NARROWER STILL: 29 BATTLES IS BELOW THE ~44-BATTLE PP BUDGET.** The run measured the **pre-dry regime only**, so `pp=0` means *29 < 44*, not *the PP half stays quiet*. See `#24-ppscope` — once the trainee goes dry the PP half fires on EVERY battle and nothing heals it, because `_team_is_out_of_pp()` is all-quantified.
    • ⛔ **P2 IS CONFOUNDED, AND HONESTLY SO.** The PP half fired 0 times — but `heal_in_pokemon_center` ran **twice** mid-grind (f30201, f67225), which resets PP. So the reading is *“the existing heal cadence keeps PP up”*, **not** *“PP lasts 29 battles”*. ✅ That is still the answer Piece 3 needs — `train_team` already bounds the PP half by itself, so the leg does not need new heal logic — but the two claims are not the same and the weaker one is what was measured.
  ✅⭐ **THE GRADE NOW CARRIES “AND THE BOT CAN CONTINUE” — IT SHIPPED WITHOUT IT, AND A DIFF ADVISORY CAUGHT THAT.** `R-ACCEPTGRADE` exists because §Ch15 ended four floors underground, §Ch18 on an eleven-tile island and §Ch19 in a living room, and **all three passed their own tests**. `S-CONTINUE` is now a REQUIRED reading with two conjuncts, both derived from the tile the run actually reached: **(a)** a real `calculate_path` back to the anchor landing, and **(b)** Fly must be LEGAL there, because the ladder's next move is another Fly. Final grade: **PASS, 8 readings, `missing=[]`.**
  ⛔⛔ **AND THE CHECK'S FIRST RUN FAILED ON A BUG IN THE CHECK, NOT IN THE BOT.** It reported `path_home=0` at `VERDANTURF_TOWN (16,4)` and graded FAIL — but **0 waypoints means “already standing on the landing”**, which is the BEST outcome: `train_team` ends with a heal and leaves the bot in town, on that very tile. `calculate_path(x, x)` returns an EMPTY list and I tested TRUTHINESS. ⇒ fixed to `is not None`. ‼ This is this tree's own recurring trap, hit again: *“when a probe FAILS, read the failing line before touching the thing under test.”*
  ‼ **THE THREE RUNS ARE A DETERMINISM CHECK, NOT A REPLICATION.** All three produced IDENTICAL numbers (`calls=53`, `hp=1`, `swaps=1`, exp `4716`/`108`) — as they must, from a fixed save state in a deterministic emulator. ⇒ say **“one trajectory, replayed”**. It confirms the readings are stable; it adds **no** statistical weight to the 3.4 %, and the Wilson interval above is unchanged.
  ✅ **A CONSTANT WAS CORRECTED BY THIS RUN:** turns/battle is **1.83** (53 `decide_turn` calls / 29 battles), not the 3 assumed by `probe_ladder_economics.py`. ⇒ the real PP budget is ~44 battles, not 27 — the assumption erred SAFE, though its comment reasoned the direction backwards and has been corrected.
  ⭐ **THE GAP, EXACTLY.** The ladder's escape from the L89-L94 overshoot is that a level-matched trainee never triggers the swap and so solos for full xp. **`max_wild_max` kills only TRIGGER 1** (`underleveled`). `SwapTrainBattleStrategy.decide_turn` fires on `(underleveled or cant_continue)`, and **`cant_continue` = HP below `battle.hp_threshold` OR no usable move** — the out-level rule touches neither. When it fires, `_capable_finisher` takes the **strongest** healthy mōn that out-levels the foe, and at a level-matched ground the foe is low-level, so **almost any L75 qualifies** ⇒ the equal share leaks exactly as before.
  ✅ **THE HP HALF LOOKS SURVIVABLE — BY READING, NOT MEASUREMENT.** `hp_threshold` defaults to **20 %** (`modules/config/schemas_v1.py`), and a trainee that out-levels its wilds should rarely fall that far in a short wild battle. ⛔ Do not build on this sentence; it is exactly the kind of reasoned-not-measured claim `06-DECISIONS-LOG.md` flags as reopenable.
  ⚠⚠ **THE PP HALF IS THE REAL EXPOSURE, AND IT IS CERTAIN RATHER THAN LIKELY.** `not any(util.move_is_usable(move))` fires on PP exhaustion, which happens eventually in every long grind and then fires on **every** battle until healed. ‼ This tree already carries a fixture called `grind_stall_ppzero.ss1` — the state is known to occur. ⇒ **the leg's heal cadence is what BOUNDS trigger 2**, not a comfort feature.
  ⇒ **WHAT TO MEASURE:** the trigger-2 firing RATE at a level-matched ground, **split HP-driven vs PP-driven**, and the exp actually banked by the trainee vs the finisher. ‼ Instrument the value the code ACTS on (which branch fired, and the chosen finisher index), never a candidate list — a candidate is not an attempt.
  ✅⭐ **THE PP HALF IS NOW SETTLED BY ARITHMETIC, AND IT IS A DESIGN NUMBER, NOT A WORRY** (`probe_ladder_economics.py`, evidence `evidence/2026-09-23-ladder-economics.stdout.txt`). Read from the real party: **Zigzagoon has 80 PP** across its moveset, **Castform 50**. At a conservative 3 turns/battle that is a heal cadence of **every ~27 battles (Zigzagoon)** and **every ~17 (Castform)** — miss it and trigger 2 fires on EVERY battle thereafter. ⇒ **~40 and ~49 heal trips** across the grind. The leg's heal frequency is therefore a CORRECTNESS requirement, not a comfort feature.
  ✅⭐ **AND THE LADDER'S BENEFIT IS NOW A NUMBER: it roughly HALVES the grind.** Priced rung-by-rung against each mōn's real growth curve and `total_exp`, carrying the measured ×1.65 frames-per-WIN correction in BOTH columns: **SOLO (ladder) 22.3 h** (Zigzagoon 12.3 + Castform 10.0) vs **2-WAY 43.0 h** if trigger 2 fires every battle. The difference is exactly the ×2.00 participant divisor the ladder is designed to remove.
  ⛔⛔ **THE FINDING THAT RESHAPES PIECE 3: THE GRIND IS 96 % OF AN ENTIRE RUN BUDGET.** `MAX_FRAMES_PER_RUN = 5_000_000` (`story_mode.py:5517`) is **23.3 h**; the grind alone is **22.3 h ≈ 4,794,924 frames**. ⇒ a leg that tries to FINISH training in one run is structurally impossible — it would exhaust the run with nothing left for the Elite Four, and everything BEFORE §Ch24 costs frames too. ⛔⛔ **BOTH HALVES OF THAT SENTENCE ARE FALSE, AND I PUBLISHED IT ANYWAY. CORRECTED 2026-09-23 (late).**
    ⛔ **(a) `MAX_FRAMES_PER_RUN` IS NOT `StoryMode`'s.** The constant `MAX_FRAMES_PER_RUN` is declared inside the class `StoryEndlessResetMode` (`story_mode.py:5542`) — ‼ deliberately NO bare line number for the constant itself: an earlier version carried one in PROSE (to dodge the citation-pairing heuristic) and it went stale the very next time that file was edited, where no gate could see it. The class citation is gated and carries the location. ‼ Class `StoryMode` (`story_mode.py:1730`) has **no frame cap at all**. ⇒ the “96 % of a run budget” figure applies ONLY to the endless-reset BATCH mode. ‼ I grepped the constant, read the number, and never checked which class owned it.
    ⛔ **(b) THE STORY BOT NEVER SAVES.** `save_the_game()` has **ZERO** call sites in `modules/story/` or `plugins/custom_modes/` — the only two in the tree are `modules/modes/_listeners.py:279` and `:286`, both inside `BattleListener.catch`. Levels live in **emulator RAM**. ⇒ *“exp lives in the save”* was an assumption stated as a fact.
    ⛔ **(c) AND THE ENDLESS MODE RESETS DELIBERATELY:** `reset_per_run_state()` then a hard reset + NEW GAME (`:5690`), *“a clean slate by construction”* (`:5484-5485`).
    ⇒ **IN THE MODE THAT HAS THE BUDGET, NOTHING PERSISTS. IN THE MODE WHERE THINGS PERSIST, THERE IS NO BUDGET AND NO “NEXT RUN”.** The design sentence was incoherent.
  ✅⭐ **THE REFRAME THAT IS ACTUALLY BUILDABLE:** Piece 3 is **“train to target in ONE uncapped run, with the frame purse demoted from a SCHEDULER to a KI-28 BACKSTOP”**. `_yield_bounded_by_frames` is still the right helper — its job changes from *“spend a slice”* to *“never let a wedged grind run forever”*, which is what it was built for.
  ⚠ **A REAL SCOPE CONSEQUENCE, FOR THE USER NOT FOR THE CODE:** under `Story (ENDLESS RESET)` — the BATCH mode used for measurement — the grind **cannot fit**. Cap 5,000,000; deepest COMPLETED real run **3,058,007** frames (`story_mode.py:5500`); grind **4,794,924**. ⇒ §Ch24-with-training is reachable in `Story` and `Story (DEBUG - RESET)` (both uncapped) and **not** in the endless batch. That is a measurement-coverage question to put to the user, not a defect to fix.
  ⛔⛔ **THAT “AWKWARD SIDE-FINDING” WAS BACKWARDS, AND SO WERE ITS NUMBERS — RETRACTED 2026-09-23 (late).** It said `VICTORY_ROAD_1F` (top wild L75) is admissible only at L74+ and so is *not* the ladder's workhorse, with `ROUTE121` (top wild L38) carrying L37→L65 alone over 822 battles. **Every number in that sentence was wrong**, because `probe_ladder_economics.py` TRANSCRIBED a ladder table instead of reading the production one. Real bands (`training_areas.py`): ROUTE117 **(13,14)** not 20 · ROUTE111 **(19,22)** not 24 · ROUTE121 **(25,28)** not 38 · VICTORY_ROAD_1F **(36,40)** not 75 — **four of six rungs wrong.** ‼ The cause: I copied the TRAINEE-LEVEL ranges out of `probe_training_ladder.py` (*“ROUTE117 L15-20”*) and used them as **WILD-LEVEL TOPS**. Those are different quantities, and `xp_per_battle()` is linear in the wild level.
  ✅⭐ **CORRECTED, AND THE TRUTH IS THE OPPOSITE: `VICTORY_ROAD_1F` OPENS AT L39 AND IS THE WORKHOLDER OF THE WHOLE CLIMB.** With `hi=40` and the rule `hi <= level+1`, it becomes admissible at **L39** and carries **751 of Zigzagoon's 1,026 battles (73 %)** and **751 of Castform's 796 (94 %)**. `ROUTE121` does **L28→L39, 186 battles** — not the climb.
  ✅ **THE FIX IS STRUCTURAL, NOT ARITHMETIC:** the probe now **calls `best_training_area(level, max_wild_max=level+1)`** — the picker the bot itself uses — and finds each rung's end by stepping the level until the picker answers with a different ground. ⇒ its rung boundaries are the bot's by construction. **A transcribed table cannot disagree with production loudly; it disagrees silently.**
  ‼ **AND THE HEADLINE TOTAL BARELY MOVED — FOR ENTIRELY DIFFERENT REASONS, WHICH IS WHY THE OLD NUMBER WAS NOT EVIDENCE THAT THE OLD MODEL WAS RIGHT.** 21.7 h → **21.0 h** solo (41.1 h 2-way). The two errors partly cancelled: the fake-high ROUTE121 (38 vs 28) made it look strong, while the fake-high VICTORY_ROAD_1F (75 vs 40) locked the real workhorse out entirely. ⇒ a stable bottom line across a model change is **not** corroboration.
  ⭐ **A CONSEQUENCE FOR THE §Ch23 RE-ENTRY PROBLEM, AND IT IS GOOD NEWS:** because the dominant phase is **inside Victory Road**, `inside_vr` is True there (`victory_road.py:3378`, `VICTORY_ROAD_MAPS` at `:3270`) and **leg 4's ocean crossing does NOT fire**. The re-entry tax applies only to the EARLY rungs — **276 of 1,026 battles for Zigzagoon, 46 of 796 for Castform**. ⛔ It does NOT remove the marker prerequisite: `ch23_chapter_done()` returns False *inside* Victory Road too (`:3318`), so `_guard` still stops the run. The Victory Road promotion was justified as *“the only candidate in budget”* under a 4-hop WALKING budget; with Fly and the out-level cap, the rung that actually does the work is ROUTE121. The promotion is still correct — it is the L74+ rung and the §Ch24 top-up ground — but it is not the ladder's workhorse.
  ⛔ **STILL UNMEASURED: THE HP HALF.** `hp_threshold` is 20 % and the trainee out-levels its wilds, so it SHOULD be rare — but that is a reading. Only a drive at a level-matched ground, counting WHICH BRANCH fires, settles it. ‼ Instrument the branch and the chosen finisher INDEX; a candidate list is not an attempt.
  ⛔ **IF IT FIRES OFTEN:** training all six cannot meet the L65-75 ceiling, and the question returns to the user with real numbers. USER RULING 12 says what is WANTED; it cannot make an impossible outcome possible.
- [~] ✅⭐ `#24-ppscope` — **MEASURED IN MOTION 2026-09-24 (264 battles, past the ~44-battle dry point). The trainee-scoped PP term FIRED: `pp_predicate_true=2` of `3365` calls ⇒ the predicate promoted *"proven as a predicate, unproven in motion"* is now proven in motion. ⇒ WHAT REMAINS: the **trigger-2 HP-vs-PP mechanism split** asked for below is still uninstrumented.**
  ⛔ **THE PREDICTED PP-DRY REGIME DID NOT MATERIALISE** — 2 firings in 264 battles, because the existing heal cadence keeps PP topped up (already on record at the `29 battles` note above). ⇒ the honest claim is *"a live backstop that fires rarely"*, NOT *"the dry regime is characterised"*. ‼ And the predicate is evaluated up to twice per heal decision (`early_game.py:2364`, `:2371`), so `true=2` is an UPPER BOUND meaning **one or two** PP-driven heals — not a heal count.
  ✅ **THE OUTCOME THE SPLIT WAS WANTED FOR IS MEASURED, AND THE LEAK IS CONFIGURATION-DEPENDENT.** **sandbox 8.94 %** over 264 battles; **custom 11.38 %** over 253. ⛔ **AN EARLIER VERSION OF THIS LINE CALLED THAT A "SPLIT" — THAT LABEL IS WITHDRAWN.** A pre-registered same-fork repeat reproduced the sandbox run **bit-for-bit** (`battles=264`, `exp_leak_pct=8.94`, every PID's exp identical), so the harness is **deterministic within a fork** and the two figures are **two deterministic outcomes of two different configurations, not two samples**. ⇒ **P4 is NOT ESTABLISHED**; *"the leak is bounded below 10 %"* is not supported. Neither run nears the 25 % refutation bar, so the ladder's premise stands. `Wailord#FA51ECF3` dominates both: 5,700 of 6,910, then 8,016. ⚠ Both climbs stop at **L40** while the real floor is **L65** ⇒ re-measure. ‼ And **never quote a sandbox number as the custom number** — a cross-fork comparison is CONFOUNDED.
  ✅ **BUILT:** `lead_has_no_damaging_pp(party)` — a **pure** predicate beside the all-quantified `_team_is_out_of_pp`, and a new `train_team(..., heal_on_lead_pp=False)` parameter that ORs it into the heal condition.
  ⭐⭐ **OFF BY DEFAULT, AND THAT IS THE ENTIRE SAFETY ARGUMENT.** `train_team` is a SHARED path — early-game grind, gym prep, counter hunts. With the default `False` the condition short-circuits before the new predicate is even CALLED, so the expression is byte-for-byte the old one and **no existing caller can move**. Only a caller training ONE mōn on a strong bench opts in.
  ⛔ **AND IT DOES NOT NARROW `_team_is_out_of_pp`:** that predicate is all-quantified and **correct** for the whole-team grind it serves, where the whole team fights. This is a second, narrower term — not a replacement.
  ✅ **GATE #70 (`probe_lead_pp_scope.py`), FOUR ARMS, NO EMULATOR** (the predicate is pure, so it runs in milliseconds): **A** a dry lead on a full bench reads DRY — the case the old predicate is structurally blind to, printed beside the contrast that proves the gap; **B** a lead with a damaging move does NOT; **C** ⭐ a lead holding only **status** moves (base power 0 — Castform's real `Sunny Day`/`Hail` shape) reads DRY, which a naive “any move with PP” test gets wrong; **D1-D3** an egg / absent / empty lead is **not** dry, because reporting it so would send the bot on a heal trip that fixes nothing forever.
  ✅ **FAULT-TESTED:** with `POKEBOT_PPSCOPE_FAULT=1` the gate exits 1 with **both** True-expecting arms red and every False-expecting arm green. ‼ An earlier grading demanded that ONLY arm A go red and **failed its own fault test** — the blanket-False stub was blunt, the predicate was fine. Corrected: the signal is that a False expectation CANNOT be broken by a stub returning False.
  ⚠⚠ **WHAT IS STILL NOT MEASURED, AND IT IS THE POINT OF THE ITEM:** no run has observed the dry regime at all. `--driver ch24swaptrigger` stopped at **29 battles** against a **~44-battle** PP budget. ⇒ the fix is proven CORRECT as a predicate and **unproven in motion**. Do not record `#24-ppscope` as closed on gate #70 alone.
  ⭐ **THE CHAIN, EVERY LINK VERIFIED AT SOURCE.** `train_team`'s heal condition is `_lead_level() >= target OR _min_battler_hp_pct() <= heal_at OR _team_is_out_of_pp()` (`early_game.py:2304-2307`). **`_team_is_out_of_pp()` returns `False` as soon as ANY non-egg party member has a damaging move with PP left** (`early_game.py:1152`, body at `:1170-1181`). ⇒ with five L75s on the bench it is **permanently False** while one trainee grinds.
  ⛔⛔ **WHAT THEN HAPPENS, AND IT UNDOES THE LADDER'S ENTIRE BENEFIT.** (1) The trainee's PP runs dry — measured budget **~44 battles** for Zigzagoon's 80 PP at 1.83 turns/battle. (2) No PP heal fires. (3) A dry trainee trips `cant_continue`, so **trigger 2's PP half fires on every battle** and `_capable_finisher` sends in a L75 ⇒ **exp splits 50/50**. (4) The finisher now takes the hits, so the TRAINEE stops taking damage and the only remaining trigger is `_min_battler_hp_pct()` (`:1128`, lowest HP% across the team) — and a **L75 Wailord with 396 HP against L40 wilds sheds HP very slowly.** ⇒ the split regime persists for a long, unbounded stretch, decaying the measured **21.0 h** toward the **41.1 h** 2-way figure.
  ‼ **IT IS NOT A LIVELOCK, AND SAYING SO MATTERS.** `_team_is_out_of_pp`'s own docstring records the livelock it was written for — *3,011 consecutive flees, ~2.9 MILLION frames* — but that was the STOCK strategy fleeing. Under `SwapTrainBattleStrategy` a dry lead SWAPS instead of fleeing, so the bot keeps winning and keeps levelling. ⇒ the damage is **silent inefficiency, not a stall**, which is strictly harder to notice.
  ⚠⚠ **AND MY OWN DRIVE COULD NOT HAVE SEEN IT — THIS QUALIFIES THE 3.4 % RESULT.** `--driver ch24swaptrigger` ran **29 battles**, which is BELOW the ~44-battle PP budget. It measured the **pre-dry regime only**. The `pp=0` reading in that run is therefore not evidence that the PP half stays quiet — it is evidence that 29 < 44. ⇒ **a drive that stops before the failure mode's onset cannot report on it**, and the honest reading of `#24-swaptrigger2` is narrower than it first appeared.
  ✅ **THE FIX SHAPE (not yet built):** a trainee-scoped predicate — *“does the mon we are LEVELLING still have a damaging move with PP?”* — OR'd into the heal condition. ⛔ Do **not** narrow `_team_is_out_of_pp` itself: it is shared with the early-game whole-team grind where all-quantified is CORRECT (the whole team is fighting). Add a second, narrower term.
  ‼ **AND IT NEEDS ITS OWN MEASUREMENT, NOT A RE-READ:** drive past **60+ battles** on one trainee and count trigger-2 PP firings and the exp split before and after the dry point. The existing evidence stops too early to grade the fix.
- [~] ✅⚠ `#24-ch24owns` — **NEW 2026-09-23 (late), BUILT AND GATED (#71). THE SECOND OF PIECE 3'S TWO PREREQUISITES. ⇒ WHAT REMAINS: **nothing sets the latch yet** — Piece 3's leg calls `mark_ch24_owns_run()` as its first act. It ships INERT, deliberately.**
  ⭐⭐ **THE PROBLEM IT SOLVES, VERIFIED AT SOURCE.** `ch23_chapter_done()` is **FLAG ∧ POSITION ∧ BAG** (`victory_road.py:3315-3322`): it needs `_on_map(EVER_GRANDE)` **and** that we are on no Victory Road floor. ⛔ **§Ch24 breaks the POSITION conjunct by design** — training flies to ROUTE117 within seconds, and the dominant phase grinds INSIDE Victory Road, tripping the other half of the same line. ⇒ every later run would find §Ch23 “unfinished”, re-run `do_victory_road_chapter()`, and `_guard` would **stop the bot**. ‼ `victory_road.py:3308-3313` predicted this and called it a forward dependency.
  ✅ **BUILT:** `StoryMode.mark_ch24_owns_run()` sets a run-scoped latch; `_play()` gains a `_ch23_settled()` helper = `latch OR ch23_chapter_done()`, used on **BOTH** the skip **and** the `_guard`. ⛔ Both halves or neither: `_guard` is **assert-not-skip**, so gating only the skip moves the failure one line down instead of fixing it.
  ⛔⛔ **THE LATCH CLEARS IN `reset_per_run_state()`, NEVER `__init__`, AND THAT CHOICE HAS A BODY COUNT.** `StoryEndlessResetMode.run()` loops on the **same mode object**, so `__init__` runs once per BATCH — a latch set there would make run 2 of an overnight batch believe §Ch24 had started and **skip §Ch23 entirely**. That is the `_rival_attempts` shape (`story_mode.py:1849-1872`) which killed **16 of 20 P1 runs, 6 of 9 P2, 5 of 8 P3**. ✅ Verified: `__init__` only calls `reset_per_run_state()`; the derail path (`continue` → re-`_play()`) and the whiteout path both keep the SAME instance, so the latch correctly survives both and dies only at a real run boundary.
  ✅ **GATE #71 — FOUR ARMS, NO EMULATOR:** **A** latch set ⇒ §Ch23 settled though its predicate says no; **B** ⭐ it CLEARS between runs (the arm with the body count); **C** inert when unset — `_ch23_settled()` is exactly `ch23_chapter_done()`, so nothing moves for runs that never reach §Ch24; **D1-D4** read the **shipping source** to confirm both dispatch halves are gated, the reset exists, and `__init__` does not set it. ‼ D exists because A-C model a closure that cannot be imported — it stops the model drifting into a comforting fiction.
  ⚠ **A RESIDUAL HOLE, STATED RATHER THAN HIDDEN:** a **process restart** mid-§Ch24 clears the latch, so §Ch23 re-runs once. Recoverable and wasteful, not fatal — and the alternative (an event flag) would mean inventing a meaning for an unrelated Gen-3 flag, which is how `KI-90` was filed.
- [~] ✅✅⭐ `#24-ch24trainleg` — **THE MULTI-RUNG CLIMB NOW DRIVES END TO END (2026-09-24). `ACCEPTANCE: PASS`, 7 readings, `missing=[]`, **264 battles, 0 whiteouts**, BOTH trainees at the floor (Zigzagoon L19→L40 over six grounds, Castform L36→L40 over two), `leg_still_below=[]`. ⇒ WHAT REMAINS: the floor driven was **40, not the real 65**. The L39→L65 stretch (~751 battles, 73-94 % of the real work) is still UNDRIVEN.**
  ⛔⛔ **THE `floor=21` PASSES HID A DEFECT THAT MADE THE LEG USELESS FOR ITS SECOND TRAINEE, AND ONE OF THEM AUTHORISED A PROMOTION.** Finishing a rung inside `VICTORY_ROAD_1F` (`map_type=Underground`) makes `fly_is_legal_from_current_map()` False ⇒ `can_fly_to_anchor` False ⇒ `_training_area_allowed`'s **entire Fly disjunct fails for every ground**, and a ≤ 4-hop walk from a cave reaches nothing. The leg then reported *"no reachable ground Castform out-levels at L36"* with ~2 M frames of purse unspent. Needs a trainee to FINISH on a Fly-illegal ground, which first happens at **L39** — 18 levels past the default. ✅ FIXED by `_ch24_step_out_if_fly_illegal()` before each trainee's first ground pick.
  ⛔ **AND A SECOND DEFECT APPEARED ONLY ONCE THE FIRST WAS FIXED:** both mōn trained and the run STILL failed `T-CONTINUE`, ending on `VICTORY_ROAD_1F (15,39)` with no computable path out (door warp). ⇒ the step-out is now a **postcondition** of `train_for_league`. The fix went in the LEG, not the CHECK. After it: `end_tile='EVER_GRANDE_CITY(27,49)'`, `fly_legal_at_end=True`, `path_to_league_anchor=0`.
  ✅ **WHAT RAN, ON THE REAL LEG** (`--driver ch24train`, evidence `evidence/2026-09-23-ch24train.stdout.txt`): from `EVER_GRANDE_CITY (18,6)` — the League plateau — it selected **Zigzagoon#33CB74C3 L19 by PID**, called `mark_ch24_owns_run()` (**1** latch call, recorded), picked **ROUTE117** via the production picker, flew there, rotated the trainee to slot 0 **verified by PID**, ran `train_team(..., heal_on_lead_pp=True)`, and took it **L19 → L21** in **14 battles**. `floor_reached=True`, `still_below=[]`, and it ended able to continue (Fly legal at ROUTE117).
  ✅ **FAULT-ARMED:** `POKEBOT_CH24_FAULT_NOLATCH=1` shadows the latch method ⇒ `latched=False` with **0** calls, while the leg still trains — a missing latch is a DEGRADATION, not a refusal, and the arm proves the reading is live rather than a foregone tick.
  ⛔⛔ **THE REVIEW THAT FORCED THE DRIVE WAS RIGHT, AND ITS FIRST BLOCKER WAS “NO PROOF THIS EVER RAN”.** Every *MEASURED* citation in the leg was evidence for a PRIOR bug or estimate; none was a recorded execution of `train_for_league`. ⇒ **correct on paper is not correct**, and the drive immediately found two real defects in my own test apparatus (below).
  ✅ **THREE BLOCKERS FIXED BEFORE THE DRIVE:** (1) the rung-cap exit was the ONLY one that said nothing — it now records `rung_cap_hit`; (2) `report["purse_finished"]` read True when every trainee had merely been *visited*, even with one left below the floor — the classic *“a candidate is not an attempt”* shape — renamed `all_trainees_visited` with a separate `floor_reached` computed from the PARTY; (3) three helpers caught bare `Exception` and could launder a whiteout abort into *“nobody needs training”* — all now call `reraise_if_aborting`.
  ⚠⚠ **SCOPE, STATED SO THE PASS IS NOT OVER-READ:** floor=21 proves **one rung of the machinery**, not the climb. Undriven: the multi-rung ladder, Castform's climb, the VICTORY_ROAD_1F rung that carries 73-94 % of the real work, and the PP-dry regime beyond ~44 battles (`#24-ppscope`). The ACCEPTANCE line carries this caveat itself.
- [ ] ⚠ `#24-healmapfallback` — **NEW 2026-09-18, FILED NOT FIXED. TWO OF THE THREE CONSUMERS OF `_training_area_heal_map()` FALL BACK TO THE **BOSS'S OWN** HEAL CENTRE WHEN A TRAINING MAP IS MISSING, INSTEAD OF REFUSING. ⇒ WHAT REMAINS: decide whether both should fail safe like the third, then fix.**
  ✅ **VERIFIED AT SOURCE.** `story_mode.py:3210` — `heal_at_center = _training_area_heal_map().get(b_map, cfg["heal"])`; `counter_hunt.py:651` — `_training_area_heal_map().get(map_enum, cfg.get("heal"))`. **Neither guards against a miss.** ⭐ Contrast the one that DOES: `decide_maintenance` at `story_mode.py:1560-1561` — `if heal_for(grass_map) is None: return None, “… refusing”`.
  ⚠ **WHY IT MATTERS:** a miss does not raise — it silently aims the heal at whatever centre the BOSS segment carries, which can be across Hoenn from the training ground. That is the quiet failure shape this project keeps paying for. ⛔ **NOT CURRENTLY BITING** — every map those paths can reach today has a row; it is the un-guarded `.get` default that is the latent defect.
  ⇒ **SUGGESTED SHAPE (not decided):** make both mirror `decide_maintenance` and refuse, since a wrong heal centre burns a cross-Hoenn round trip and a refusal costs one skipped relocation.
- [x] ✅✅✅ `#24-waterfallcap` — **FIXED AND PROVEN 2026-09-18.** `_resolve_caps` (`region_reach.py:228-236`) now iterates `_GATE_MOVE_NAMES` instead of a hardcoded four-key literal, so the move-name table is the single source of truth and a sixth gate cannot repeat this silently; `can_waterfall` is threaded through the public signatures for parity. ⭐ **MEASURED AFTER:** `is_map_reachable(VICTORY_ROAD_1F)` is **True** on all 4 fixtures, `why_unreachable` reads `reachable`, and from the grind tile the world went **3 → 309 maps**. **All 65 enforcing gates pass**, and **gate #65 (`probe_caps_resolve_every_gate.py`) now holds this line** — it was written BEFORE the fix and shown to FAIL on the unfixed code. Predictions were pre-registered at `65f29520` and graded **6 confirmed / 1 ungradeable / 0 refuted** (`ai-research-notes/2026-09-18-waterfallcap-PREDICTIONS.md`). ⚠ **THE ONE UNGRADED PREDICTION IS P7** — *“no §Ch23/§Ch24 drive behaviour changes”* — an absence claim that only a drive can test. ⇒ **watch the next drive for it.** ⛔ **AND THE FIX IS SANDBOX-ONLY:** `custom-pokebot/` is untouched, so it is one of the differing files — **run `promote.py --check` for the live count, never trust a digit written here** — and promotion needs explicit user approval. *(Original filing follows, and its measurements stand.)* **MEASURED ON THREE PINNED FIXTURES IN BOTH DIRECTIONS. `is_map_reachable(VICTORY_ROAD_1F)` RETURNS FALSE FOR **EVERY PARTY AT EVERY BADGE COUNT**, BECAUSE THE REACHABILITY GRAPH NEVER RESOLVES THE `"waterfall"` CAPABILITY IT GATES ON. ⇒ WHAT REMAINS: teach `_resolve_caps` the `"waterfall"` key (ONE dictionary entry — the other three pieces are already wired), then prove it with a drive. ✅⚠ **THIS ITEM MAY STILL LAND FIRST AND ALONE — BUT NOT FOR THE REASON FIRST GIVEN.** ⛔ “exposes nothing” is **REFUTED by my own A/B**: it changes counter-candidate RANKING and takes `best_training_area(allow=_counter_area_allowed)` from `None` to `ROUTE121`, **though only from a position INSIDE Victory Road**. ✅ At the EXECUTOR level nothing changes — `best_huntable` is identical in both arms everywhere and `huntable` stays False. ⇒ the honest claim is *“ranking-only, inside-the-cave-only, executor guard intact”*. It does NOT have to wait for, or ship with, `#24-trainingbrackets`. ⛔ The pair that IS inseparable is the other one: that item's `TRAINING_GRASS` row must never land without its `AREA_PREREQ` row.**
  ✅ **THE MECHANISM, VERIFIED AT SOURCE BEFORE AND AFTER:** `KNOWN_GATES` (`region_reach.py:81-98`) gates the sole EVER_GRANDE_CITY ↔ VICTORY_ROAD_1F edge on `"waterfall"`; `:342` drops any edge whose gate is missing from `caps`; and `_resolve_caps` (`:228-236`) used to iterate a hardcoded four-key literal, so `caps.get("waterfall", False)` was **always False** and `_gate_key` (`:158-159`) sealed it BOTH ways. ‼ `_GATE_MOVE_NAMES` (`:100-106`) and `_RSE_BADGE_BY_MOVE` already carried Waterfall — **three of the four pieces were wired** by commit `0c1d6686`, which never touched the resolver and has no revert.
  ⭐ **MEASURED, BOTH DIRECTIONS, 4 FIXTURES:** before — parties HELD Waterfall (Wailord, `BADGE08_GET`, `_live_capability('Waterfall')=True`) and the graph still refused, naming its own gate; the world from the grind tile was **3 maps**. After — `reachable`, and **309 maps**. Evidence: `evidence/2026-09-18-waterfall-capability{,-AFTERFIX}.stdout.txt`.
  ⭐ **AND THE CHANGE WAS MEASURED BEFORE IT WAS WRITTEN** (`probe_waterfall_fix_ab.py`, `evidence/2026-09-18-waterfall-fix-AB.stdout.txt`): at the EXECUTOR level nothing moves — `best_huntable` is identical in both arms and `huntable` stays False for every Victory Road candidate. The only actionable delta is `best_training_area(allow=_counter_area_allowed)` → `ROUTE121`, **and only from INSIDE the cave**. ⚠ P7 (*“no drive behaviour changes”*) is an ABSENCE claim and remains **UNTESTED** — the next §Ch23/§Ch24 drive is its test.
  ‼ **FULL DETAIL LIVES IN THE APPEND-ONLY FILES, NOT HERE** (this is a CURRENT-STATE file): `ai-research-notes/2026-09-18-waterfallcap-PREDICTIONS.md` (pre-registered at `65f29520`, graded 6/1/0), `07-CHANGELOG.md` 2026-09-18, and `06-DECISIONS-LOG.md` 2026-09-18 for why an abort condition fired and the change proceeded anyway.
- [ ] ⚠ `#24-gategranularity` — **NEW 2026-09-18. THE WATERFALL GATE IS ON AN EDGE THAT NEEDS NO FIELD MOVE, AND THAT IS A DELIBERATE MAP-GRANULAR APPROXIMATION — NOT A BUG, BUT IT SHOULD BE WRITTEN DOWN BEFORE SOMEONE “FIXES” IT. ⇒ WHAT REMAINS: decide whether to model it honestly, and add the missing ROUTE128 ocean edge.**
  ✅ **THE GEOGRAPHY, CORROBORATED TWO WAYS.** A decomp pass decoded `data/layouts/EverGrandeCity/map.bin` and found a block of `MB_WATERFALL` metatiles at x≈15-26, y≈60-67 — **inside Ever Grande City**, between the Route 128 arrival seam and the rest of the town. ⭐ **OUR OWN LIVE-MEASURED CONSTANTS AGREE TILE-FOR-TILE:** `victory_road.py:128-130` — `WATERFALL_BASE = (18, 68)`, `WATERFALL_TOP = (18, 59)`, `EG_LANDING = (18, 55)`. And `VR_DOOR = (18, 41)` (`:138`) sits on dry land north of that, with `ch23route` R11b measuring `(18,55) -> (18,41)` as a **plain 16-waypoint walk**.
  ⇒ **SO `KNOWN_GATES`' `((0,8),(24,43)): "waterfall"` GATES A DOOR THAT NEEDS NOTHING.** The real requirement is on `ROUTE128 <-> EVER_GRANDE_CITY`, which has **no entry at all**.
  ✅✅ **BUT IT IS NOT A DEFECT, AND THIS IS THE PART TO READ BEFORE TOUCHING IT.** The graph is **MAP-granular** and the falls split **one map** in half — there is no way to express “the northern half of Ever Grande” in a map graph. Gating the Victory Road edge is a correct-by-construction proxy, and `0c1d6686`'s own comment says exactly that: *“that entrance sits at the TOP OF A WATERFALL, so HM07 is mandatory to stand on it.”* ⇒ since **no party can be north of the falls without Waterfall**, the predicate is **observationally correct in both directions for every reachable game state**.
  ⚠ **WHAT IS GENUINELY IMPRECISE:** `is_map_reachable(EVER_GRANDE_CITY)` is True for a Surf-only party — true at MAP granularity (you can float on the arrival strip) and misleading at TILE granularity (the Poké Center and both Victory Road doors are north of the falls). `story_mode.py:1213` already warns about exactly this map-vs-tile gap.
  ⇒ **WHAT REMAINS, AND THE ORDER MATTERS:** (a) add the missing `ROUTE128 <-> EVER_GRANDE_CITY` ocean edge gated on `"surf"` — same shape as the two Dewford rows, and today that edge is **ungated**, so a no-Surf party is told Ever Grande is reachable; (b) only THEN consider moving the waterfall gate, because doing (b) first would open Victory Road to any party that can reach the town's southern shore. ⛔ **Do not do (b) alone.**
  ⚠ **NOT VERIFIED BY ME:** the decomp's raw tile decode, and its open question of whether a 1F-only HM-free walk-through from `(15,40)` to the north arrow-warp `(39,5)` exists (it flagged that as needing a live `calculate_path`, not as a fact).
- [ ] ⛔⛔⛔ `#24-levelgap` — **⭐⭐ RE-SCOPED 2026-09-18 BY USER RULING (every member L65-75) — AND THE OBVIOUS READING OF THAT RULING IS **VERIFIED IMPOSSIBLE**. ⇒ WHAT REMAINS: a USER CHOICE on party composition, then build the leg.**
  ⛔⛔ **TRAINING THE MULES TO THE FLOOR BREAKS THE CEILING — I COMPUTED THIS MYSELF** against each mōn's real growth curve and real `total_exp` (`ai-research-notes/2026-09-18-ch24-levelgap-SPEC.md`). `SwapTrainBattleStrategy` (`story_mode.py:1038-1096`) switches the trainee out turn 1 when it is ≥`UNDERLEVEL_MARGIN` below the foe, and its own docstring says *“the team-mate finishes and the trainee keeps its XP share”* ⇒ **two participants, so the finisher gains too**, and `_capable_finisher` always picks the STRONGEST. ⇒ the mules need **491,450 exp**; Wailord L75 absorbing an equal share reaches **L89** (**L94** with the ×1.5 trade boost). **14-19 levels over the ruling's own cap.**
  ⛔ **AND THE SPEC'S PROPOSED ESCAPE IS REFUTED BY THE SAME ARITHMETIC.** It argued the overshoot is order-dependent and that running the mules first from `post_ch24ready` keeps the finisher in band (*“~L71”*). ✅ Both mules, real values: **Sceptile L53 → L85.** No escape.
  ⭐⭐ **AND THE ALTERNATIVE IS FREE, NOT MERELY CHEAPER:** on `post_ch24_atdoor_L75.ss1`, boxing Zigzagoon + Castform leaves Mightyena/Sceptile/Swellow/Wailord **all at L75** ⇒ the ruling is satisfied with **zero further grinding**. ⇒ **the choice is not “expensive vs cheap”, it is “impossible vs free”.**
  ✅ **THE BOT CAN DEPOSIT, AND IT IS SAFE TO:** `deposit_one_dead_weight()` (`pc_trip.py:219`) is standalone and NOT behind the pinned-0 `POKEBOT_PC_ROTATION`; and both mules are navigationally free to remove (measured — their field moves are duplicated; `team_policy.py:147-148`'s own `_only_hm_carrier` exemption independently protects Wailord and Swellow but not them).
  ⚠ **TWO GOTCHAS FOR WHOEVER BUILDS IT:** `pc_trip.py:274-276` returns **True having deposited nothing** when the party is already under six (so two calls will not box two), and `find_dead_weight` sorts **ascending by level** (`team_policy.py:170-173`) so the caller **cannot name a victim**. Boxing two NAMED mōn needs a PID-addressed deposit on the same `interact_with_pc` primitive.
  ⛔ **BLOCKED ON A USER DECISION** — removing two Pokémon changes what the art piece shows, and no ruling permits it. Put both readings to the user with these numbers; do not pick.
  *(original filing follows)* — **NEW 2026-09-17 (late). THE FOURTH PREREQUISITE FOR WIRING SEGMENT 24, AND IT WAS NOT ON THE LIST OF THREE. PRODUCTION REACHES THE LEAGUE DOOR AT L47 AND THE GAUNTLET IS 0% AT L53.**
  ‼ **EVERY §Ch24 PROBE THIS PROJECT HAS RUN USED A HAND-GROWN L75 PARTY.** That party came from `--driver ch24grind` (`Ch24GrindMode`), which lives **ONLY in `tools/story-dev/story_harness.py:15393`** — it is NOT production code. ⇒ a wired Segment 24 today would walk into a ONE-WAY SEALED ZONE at L47 and lose, repeatedly.
  **THE NUMBERS, ALL FROM OUR OWN TREE:** production's only story training target is **`TRAIN_TARGET = 47`** (`modules/story/victory_road.py:492`) — ⭐ **verified to be the ONLY one in the entire story tree** (`grep` over `modules/story/*.py` + `story_mode.py` returns exactly that one plus `ENDLESS_RESET_TARGET`, which is unrelated). And the win-rate curve (`07-CHANGELOG.md:23310-23313`) is: **`L53 → 0% Glacia · L57 → 87% Glacia, dies at Drake · L60 → 99.7% Glacia · L75 → 88% CLEAR`**, with *“Break-even is L62”* against Wallace’s Milotic Recover race (`:23307`).
  ⚠ **THAT CURVE IS SIMULATED, NOT MEASURED — and I wrote “the measured curve” here first and corrected it the same day.** `07-CHANGELOG.md:23285` says *“Simulated over 400 runs per configuration”*, and `04-HANDOFF.md` carries the standing caveat *“SIMULATION results, not drives — the model approximates the enemy AI and ignores crits/status; treat L62/L75 as ESTIMATES”*. ⭐ **Its TOP END is now corroborated by a real drive** — the 2026-09-17 tail probe beat Wallace at L75+ and cleared the game (one trajectory). ⇒ **“L75 clears” is simulated AND driven; “L47/L53 is hopeless” is simulated ONLY.** The conclusion survives either way: L47 against a break-even of L62 is a **15-level** gap, far outside any plausible error bar on a 400-run model.
  ⛔⛔ **THIS CORRECTS THE LAST SENTENCE OF A STANDING RULING, AND THAT IS WHERE A FUTURE AGENT WILL LOOK.** `06-DECISIONS-LOG.md` (2026-09-16, *“CORRECTION TO MY OWN WINNABILITY VERDICT”*) ends: *“the cheapest path to a winnable gauntlet is not more legs — it is **grinding past L62, toward ~L75** — and it is a capability we already shipped.”* ⇒ **That capability is shipped in the HARNESS, NOT in production.** `--driver ch24grind` is `Ch24GrindMode` in `tools/story-dev/story_harness.py`; nothing in `sandbox-pokebot/modules/story/` can climb above `TRAIN_TARGET = 47`. The ruling’s *conclusion* (grind to L62–75) is right; its *“already shipped”* is true only of the harness. ⚠ `06` is append-only, so that entry stands as written — **this item is the correction of record**, and a dated decisions-log entry is appended alongside it pointing here.
  ⭐⭐ **THE FIX IS ALREADY DESIGNED IN OUR OWN CODE — IT WAS JUST NEVER BUILT.** `TRAIN_TARGET`'s own docstring (`victory_road.py:488-492`) says 47 *"does NOT clear Wallace's 58 — **the remaining gap is meant to be closed on B1F after Wally** (950.8 EXP/battle vs 1F's 775.6), which is the only better ground and is gated behind exactly the fight this training is for."* And `:2025` names the same escape hatch (*"or train on B1F AFTER Wally"*). ⛔ **But §Ch23's eleven legs contain NO post-Wally training leg** — legs 6-9 are the B1F/B2F traverse, 10-11 are heal and shop (`victory_road.py:3374-3460`).
  ⭐ **AND THE GROUND QUESTION IS ALREADY SETTLED AGAINST THE DECOMP** (`modules/story/training_areas.py:30-49`): every `MAP_ROUTE*` land table maxes at **28** (ROUTE130's 50 is the Mirage Island WYNAUT trap), **no land table anywhere in Hoenn has a max of 34/35/37/41/43/46/47/48/49**, and ⇒ *"EVERY L30+ WILD GROUND IN EMERALD IS A CAVE, A DUNGEON, THE SAFARI ZONE, OR VICTORY ROAD … the surviving lever is **train IN the dungeon you are already clearing**, never relocation."* ⇒ **B1F is not a preference, it is the only option.**
  **THE WORK — ⛔⛔ BIGGER THAN “ADD A LEG”. I MEASURED THE GUARD AND IT REFUSES EVERY CONFIGURATION.**
   A post-Wally training leg on `VICTORY_ROAD_B1F` to **L62 minimum** (L75 for the modelled 88%) is the
   right SHAPE, and `train_for_victory_road`’s own refusal message already recommends it verbatim
   (`victory_road.py:2025-2026`). But three things block it, and the first two were not in this item’s
   first draft:
   1. ⛔ **THE GROUND IS NOT A PARAMETER.** `target` is (fixed 2026-09-04), but the call site hardcodes
      `grass=TRAIN_SPOT_1F` (`:2088`) and `WILD_MAX = 40` is a hardcoded local (`:1988`). **There is no
      `TRAIN_SPOT_B1F` — `TRAIN_SPOT_1F` (`:477`) is the only such constant in the module.** ⇒ this IS
      partly a re-plumbing job, and it is the *same shape* as the 2026-09-04 defect one level out:
      **a parameter that reaches half the function is not a parameter.** ‼ My first draft said “a new
      LEG, not a re-plumbing job” — **that was wrong, and I found it by reading the call site.**
   2. ⛔⛔ **THE PER-CALL CEILING REFUSES IT — MEASURED, ALL 16 CELLS.** `MAX_TRAINING_FRAMES = 250_000`
      (`:508`) refuses any SINGLE mon whose estimate exceeds it (`:2021`). Running the project’s own
      `estimate_frames_to_level` (CAL 50.2, 1433 frames/battle) for a L47 mon, against land maxima I
      measured from the decomp (`src/data/wild_encounters.json`: **1F max 40, B1F max 42, B2F max 44**):

      | ground | →L62 cheapest curve | →L62 worst | →L75 cheapest | →L75 worst |
      |---|---|---|---|---|
      | 1F (wild 40) | 538,808 | 841,171 | 1,271,071 | 1,986,138 |
      | B1F (wild 42) | **513,014** | 801,047 | 1,210,885 | 1,891,560 |

      ⇒ **every cell REFUSES**; the cheapest is **2.05×** over and the worst **7.6×** (double all of it
      again if swap-training’s 2-way split applies, which the estimator ignores). ⛔ And per the refusal
      message’s own instruction, **do NOT raise the ceiling to make the run start.**
   3. ⚠ **B1F BUYS ONLY +5% UNDER THE GUARD’S MODEL, NOT +22.6%.** My first draft took “950.8 vs 775.6
      EXP/battle” (+22.6%) and sized the leg at *“~500 battles / ~25 min”*. **Those two figures come from
      DIFFERENT MODELS and the sizing is not comparable to the ceiling.** The guard sees only
      `CAL × wild_level / 7` ⇒ 1F **286.9** vs B1F **301.2** xp/battle, a **+5.0%** difference. 500 battles
      would be 716,500 frames — **2.9× the ceiling** — so the sizing never established feasibility at all.
   ⛔⛔ **WHAT WOULD UNBLOCK IT IS *NOT* THE ESTIMATOR — I FILED THAT AND WITHDREW IT THE SAME DAY
   (`#24-trainestimatorcal` above). CORRECTED ARITHMETIC BELOW.** The estimator is only ~18%
   pessimistic on the quantity that matters (exp per FRAME), because `FRAMES_PER_WILD_BATTLE = 1433`
   is wrong for Victory Road in the *same* direction as the xp term and the errors cancel
   (`07-CHANGELOG.md:24637-24641`, settled 2026-09-08). ⇒ **the refusals are REAL, not an artifact.**
   ⭐ **TRUE COST OF L47→L62 ON B1F**, at the real rate (950.8 xp/battle) and the real frame cost
   (~3,192 f/battle measured at Victory Road — ⚠ **that frame rate was measured alongside 1F’s 775.6 and is TRANSFERRED to B1F here; frames/battle has never been measured per Victory Road FLOOR, as this item’s own withdrawal states. The refusal margins are 46%+ so it does not flip the conclusion, but the precise digits carry that assumption** ⚠⚠ **AND THE 3,192 FIGURE ITSELF IS NOW IN DOUBT (2026-09-18):** two independent angles measured it from real logs as **2,138** and **2,384–2,648**. NOT adjudicated — see `ai-research-notes/2026-09-18-ch24-grind-economics-MEASURED.md`. *(Direction matters: a LOWER frames/battle makes every grind CHEAPER than the figures below assume.)*): **Fast 363,888** · **Medium-Fast 453,264** · **Medium-Slow 466,032** · **Slow 564,984** frames.
   ⇒ **EVERY curve REFUSES the 250,000 ceiling — by 1.46× (Fast) to 2.26× (Slow)** — and L75 costs
   **855k–1.34M** frames, 3.4×–5.3× over. Double all of it again if swap-training's 2-way split
   applies (`set_swap_train(True)` is unconditional at `early_game.py:2097`).
   ⇒ **THE REAL BLOCKER IS THE BUDGET SHAPE, NOT THE COST MODEL:** a 15-level climb does not fit in
   one `train_team` call, and ⛔ the refusal message forbids the obvious dodge — *"do NOT raise the
   ceiling to make the run start."*    ⛔⛔ **THE ORDER ABOVE IS SUPERSEDED — IT READ “(1) `#24-trainestimatorcal`, (2) decide how a
   multi-call or split-aware grind is budgeted, (3) build the leg.” STEP (1) WAS WITHDRAWN THE SAME DAY,
   AND STEP (2) IS NOW ANSWERED (2026-09-18).**
   ⭐⭐ **THE ANSWER: NOTHING NEEDS DESIGNING OR RELAXING. A STEPPED GRIND IS ALREADY PERMITTED, AND THE
   SHAPE ALREADY EXISTS AND HAS RUN.**
   * ✅ **The ceiling is PER-CALL by explicit design** — `victory_road.py:2012-2019`, verbatim:
     *“⛔⛔ THE CEILING IS PER-CALL, NOT PER-TOTAL, AND THE DISTINCTION IS THE WHOLE POINT … summing them
     and refusing would be measuring the wrong quantity … ⇒ refuse any SINGLE mon whose grind is
     unaffordable”* — and the test is `worst = max(estimates.items(), …)`, one mon, one call.
     ⇒ **each step under the ceiling is legal; the guard was never the obstacle it looked like.**
   * ⭐ **The shape exists:** `Ch24GrindMode` (`story_harness.py:15393-15689`) is a stepped loop of
     `train_for_victory_road(target=low+STEP)`, `STEP=2`, `MAX_STEPS=24`, `MAX_RETRIES=2`, a save-state
     checkpoint after EVERY step, and a refuse-to-spin break. Its checkpoint ladder
     `post_e4grind_L49 … L73 + FINAL` is **on disk** from 2026-09-17.
   ⇒ **THE WORK IS TO PROMOTE THAT SHAPE INTO A PRODUCTION LEG** — not to invent a design, not to fix
   the estimator, and (see below) not to choose a ground first.
   ⛔⛔ **BUT NOT INTO §Ch23 — REVERSED 2026-09-18 (later) AFTER A 10-AGENT BUILD RECON.** *(This item
   previously implied the leg would be inserted into §Ch23, and `04-HANDOFF.md` said so outright.)*
   **Both §Ch23 placements have a distinct, serious failure mode, and I verified the decisive one at
   source:**
   * **BEFORE leg 11 (the only mechanically viable slot, between legs 5 and 6): ONE WHITEOUT
     BANKRUPTS THE CHAPTER.** ✅ Decomp `src/overworld.c:358-366` — `DoWhiteOut()` calls
     `SetMoney(..., GetMoney(...) / 2)`. ✅ `victory_road.py:444` — *“₽54,300 total against a MEASURED
     ₽56,041”*, i.e. **₽1,741 of slack (3.1%)**. Halving gives ₽28,020 against a ₽54,300 basket ⇒ leg 11
     raises and the Elite Four's healing is never bought. A hundreds-of-battles grind is exactly where
     a whiteout becomes likely, and the derail budget RESETS on every whiteout so nothing bounds it.
   * **AFTER leg 11 — a SUSPECTED bag interaction.** ⚠⚠ **HAZARD (b) IS UNVERIFIED AND OUR OWN CODE CONTRADICTS IT — DOWNGRADED 2026-09-18 AFTER A TIER 1 BLOCK.** *(All three docs stated, as settled fact: “AFTER leg 11 the grind and the basket SHARE ONE BAG — consuming healing items makes `ch23_chapter_done()`'s basket conjunct False.”)* ✅ **MEASURED BY ME:** `train_team`'s 118-line body contains **ZERO** bag/item references in code, and its only healing call is `heal_in_pokemon_center(heal_center)` — a free Poké Center visit. The wild-battle handler `SwapTrainBattleStrategy` is pure switch logic; the item-using `StoryItemBattleStrategy` is scoped to TRAINER battles only. And `Ch24GrindMode._basket()`'s own comment says the opposite of my claim: *“THIS IS A READING, NOT A GUARD … the expectation is FLAT: `train_team` heals at a Poké Center (which also restores PP), not from the bag.”* No evidence file anywhere contains a `basket=` reading showing a drain. ⇒ **treat (b) as THEORETICAL, pending a drive with `_basket()` logging.** ⛔ **THE REVERSAL DOES NOT DEPEND ON IT** — hazard (a), the money halving, is fully verified at the decomp and sufficient on its own.
   ⇒ ⭐ **THE FIX BELONGS ON THE §Ch24 SIDE OF THE BOUNDARY** — i.e. it is part of what Segment 24 must
   CONTAIN, not a patch to a shipped chapter. ‼ **This does NOT downgrade the blocker:** production
   still tops out at ~L47 and a §Ch24 wired today still loses every run. What changed is WHERE the fix
   lives, which dissolves an apparent circularity — `#24-levelgap` is not a prerequisite to be cleared
   *before* wiring, it is a mandatory CONTENT REQUIREMENT *of* the §Ch24 chapter.
   ⛔⛔ **AND THE SHAPE MUST NOT BE COPIED VERBATIM — IT SWALLOWS WHITEOUTS.** ✅ Verified at source:
   `story_harness.py:15646-15655` does `set_story_abort(False)` then `except Exception`, and
   `class StoryAbort(BotModeError)` (`early_game.py:112`) means that `except` **catches the whiteout
   unwind**. §Ch23's own dispatch docstring forbids exactly this (`victory_road.py:3342-3345`):
   *“⛔ A WHITEOUT IS NOT RETRIED HERE … The 3-attempt loop is for `BotModeError` and nothing else”*
   — it is **KI-67's shape**, and gate #27 `probe_abort_swallowing.py` scans `modules/story` for it.
   ⇒ **promote the 33-line stepping loop; leave the retry wrapper, the save-state checkpoints, the
   `set_manual_mode()` and the ACCEPTANCE printing behind.**
   ⭐ **WHAT SURVIVES AND IS READY TO BUILD ON:** every 2-level step fits the ceiling — measured on the
   REAL battlers of `post_wally.ss1` (Sceptile L52, Swellow/Wailord/Mightyena L47; Zigzagoon L19 and
   Castform L36 are excluded by `BENCH_SPECIES`), worst step **136,135 f against 250,000, 1.8×
   headroom**. *(DERIVATION, so it is reproducible rather than asserted — a Tier 1 reviewer noted it had none: the GUARD's OWN model, `xp_per_battle = CAL 50.2 × WILD_MAX 40 / 7 = 286.9`, `× FRAMES_PER_WILD_BATTLE 1433`, applied to **Wailord** — the binding mon because it is the SLOW growth curve — climbing its last two levels to L61. The recon's independent simulation put its own worst step at 154,764 under different assumptions; both are far under the ceiling.)* And **resumability is FREE**: `team_is_ready(target)` and both loops in
   `train_for_victory_road` re-read the LIVE party and skip battlers already at target, so the grind's
   progress IS the party's levels. ⚠ `BENCH_SPECIES` is three hardcoded names, so the leg must CHECK
   at runtime that no battler sits far below target rather than relying on that list.
   ⭐⭐ **USER RULINGS 2026-09-18 — THE GOAL IS RATIFIED AND THE GROUND IS DECIDED (`06-DECISIONS-LOG.md`).**
   ✅ **L62-75 IS THE RIGHT TARGET** (*“yes that level range is worthwhile”*) ⇒ this item STANDS; the
   grind is required §Ch24 content. ⚠ Mid-50s clears exist but need *“serious strategy that we have
   not implemented”* ⇒ ⛔ do NOT propose “just play better” as a way to skip the grind.
   ⭐⭐ **GRIND AT THE VICTORY ROAD EXIT SIDE — ⛔ B1F IS OFF THE TABLE.** The user named *“the room
   right before we leave the victory road onto the other side of the ever grande island”* as the
   grind spot, for round-trip SPEED ⇒ that is `TRAIN_SPOT_1F`, *“1 step from the entrance warp”*,
   the ground the only proven driver already uses. **Do not reopen B1F without a new ruling.**
   ✅ **HEAL AT A POKÉ CENTER, NOT ITEMS** (items cost money, and leg 11's basket leaves ₽1,741 of
   slack). ✅ And the League building has **a nurse AND a merchant** before the guard — corroborating
   `heal_at_league`'s `LEAGUE_NURSE_STAND (3,4)`.
   ⭐ **THIS DISSOLVES THE APPARENT HEAL CONTRADICTION:** my own probe measured the Poké Center as
   **23 wp from `(18,42)` (the VR exit side) but NO PATH from `(18,6)` (the League door side)** — the
   ruling points the grind at the side where it IS reachable. ⇒ `#24-cavehealblind` shrinks to *“does
   `train_team`'s heal actually execute the SHORT round trip from `TRAIN_SPOT_1F`?”* — still a drive.
   ⛔⛔⛔ **BUT THE PLAN IS STILL REFUTED — THE RULING RATIFIES THE GOAL, NOT THE SCHEDULE.**
   ⛔⛔⛔ **THE “EVERY 2-LEVEL STEP FITS” CLAIM IS REFUTED (2026-09-18), AND I RE-DERIVED IT MYSELF.**
   ✅ Wailord is `Fluctuating` (`species.json`), curve `((level//2)+32)*level**3//50` past L36
   (`modules/pokemon.py:615-621`) ⇒ **cost RISES with level, so the worst step is the LAST one.**
   Computed from those formulas and the estimator's own constants: **73→75 = 266,538 f @wild40 and
   253,641 @wild42 — BOTH OVER the 250,000 ceiling.** The item's quoted **136,135 is the 57→59
   step**, an INTERIOR one, presented as the worst. ⇒ the “1.8× headroom” does not exist.
   ‼ **ATTRIBUTION CORRECTED: NEITHER HALF OF THE ~3.3× IS A NEW DISCOVERY.** The ×2 EXP-split
   half was **ALREADY FILED 2026-09-08** — see the closed item *“THE ESTIMATOR IGNORES THE EXP
   SPLIT”* further down this file, which already carries a worked SOLO-vs-2-WAY table and already
   concluded **REFUSE** at L35 and L40. The ×1.65 frames-per-WIN half is documented at
   `story_harness.py:15416-15420`. ⇒ **what the 2026-09-18 adversarial pass ADDED was APPLYING
   them to the 2-level-step claim, which nobody had done** — exactly the shape that older item
   names in its own headline: *“WHAT IS NEW IS THE CONSEQUENCE NOBODY APPLIED.”* ‼ This is the
   THIRD time this session a re-discovery was nearly published as new; the standing rule is to
   grep the tree before claiming novelty.
   ⛔⛔ **AND THE MODEL IS KNOWN-WRONG BY ~3.3× IN A FILE DATED ONE DAY EARLIER.** ✅
   `story_harness.py:15416-15420`: figures *“already doubled for the measured **0.501 participant
   divisor the estimator does not model**”* and *“~1.65× on top — ~2,368 frames per WIN against the
   estimator's 1,433 per BATTLE”*. Combined **3.30×** ⇒ **EVERY step exceeds the ceiling, including
   the first (47→49 = 293,046).**
   ⇒ ⛔ **2-LEVEL STEPPING IS NOT VIABLE AS SPECIFIED.** Step size must SHRINK with level and the
   budget must come from MEASURED cost, not `estimate_frames_to_level`. ‼ And because a leg calling
   `train_team` directly inherits NO ceiling, it would not be refused — it would simply run for
   ~879,138 frames without complaining, which is **KI-28's shape exactly**.
   ⛔ **THE ITEM ALSO NAMES A GROUND WITH NO VERIFIED TILE:** it says “B1F”, but the driver it
   proposes promoting trains on **1F** (`story_harness.py` `GRIND_TILE = VR.TRAIN_SPOT_1F[1]` (‼ cite the SYMBOL — the line drifted 15603→15610 within a day))
   and B1F's `PENDING_GRASS` row has `None` for its spin tile ⇒ building to the literal wording
   means inventing and two-way sweeping a new B1F tile, which is unscoped work.
   ✅ **NOT overturned by the adversarial pass:** resumability is free; the ceiling really is
   per-call; the fainted-mon risk is inherited from existing code, not introduced here.
   ⛔⛔ **RECON 2026-09-18 ALSO INVERTED THIS ITEM'S FRAMING — READ `ai-research-notes/2026-09-18-ch24-levelgap-RECON.md` BEFORE BUILDING.**
   ✅ **`MAX_TRAINING_FRAMES` IS NOT ENFORCED INSIDE `train_team`.** Defined `victory_road.py:508`,
   enforced at **exactly one site**, `:2021`, inside `train_for_victory_road`; the symbol is absent
   from `early_game.py` entirely. ⇒ a §Ch24 leg calling `train_team` directly inherits **NO frame
   ceiling at all** — only its 500-ROUND guard (`early_game.py:2102`). ⛔ **That is a HAZARD, not a
   licence** (`:505-507`: *“KI-28 burned 19.9M frames”*): the new leg must impose its own budget.
   ⇒ **the 16-cell refusal table above describes `train_for_victory_road`, not the leg we would build.**
   ⭐⭐ **AND THE REAL BLOCKER IS THE HEAL, WHICH IS ALREADY FILED AS `#24-cavehealblind`.**
   ✅ MEASURED by me (`probe_vr_heal_roundtrip.py`, planning only): from `post_wally.ss1` the grind
   tile is **44 wp same-map OK**; but from the League-door apron `EVER_GRANDE (18,6)` the Poké
   Center `(27,48)` is **NO PATH — a SAME-MAP ask**, while from `(18,42)` it is 23 wp. ⇒ Ever Grande
   is SPLIT, which is very likely why §Ch23 leg 10 heals at the **League NURSE** and not the Poké
   Center — and `train_team`'s `heal_center` takes a `PokemonCenter`, which the nurse is not.
   ⚠ `calculate_path` only PLANS; `navigate_to_anywhere` is multi-hop warp-aware
   (`early_game.py:1988-1997`), so a refusal does NOT bound the navigator. **Only a drive settles it.**
   ⛔ **A FALSE “VERIFIED” CLAIM WAS RETRACTED:** `train_team` **does** travel — it calls
   `_goto_training_area` (`early_game.py:2257-2274`) on every round of `train_team` (`early_game.py:2288-2403`). The registry's `POKEBOT_CH24_FAULT_NOWALK`
   rationale and the matching harness comment are corrected; that arm measures something else.
   ✅ **AND `train_team` ALREADY TAKES THE GROUND AS A PARAMETER** — production proves the shape at
   `story_mode.py:4183-4184`: `train_team(level_floor, scope="whole", grass=…, heal_center=…)`.
   ⇒ the “ground is not a parameter” blocker is about `train_for_victory_road`'s hardcoded
   `grass=TRAIN_SPOT_1F` (`:2088`) and local `WILD_MAX = 40` (`:1988`), NOT about `train_team`.
   ✅ **B1F GROUND EXISTS AND ITS “ISOLATION” IS A GUARANTEE, NOT A PENALTY:** 8 walkable `Cave`
   tiles with encounters, 2-3 wp from the `(8,3)` ladder (best `(9,4) (7,4) (9,5) (10,4) (6,4)`;
   ⛔ not `(9,3)/(7,3)`, adjacent to the ladder WARP), band L38-42 with **Hariyama at 35%**; and
   **0/5 trainers and the B2F warp are unreachable from the pocket** ⇒ nothing can ambush a parked
   spin. ⚠ The tile table is a **STATIC ROM read** and KI-74 is exactly where that lies — a LIVE
   grid read is owed before code depends on it.
   ⛔ **CORRECTED: `team_is_ready` DOES NOT RAISE.** ✅ I read `victory_road.py:1847-1912` — it has
   **no `raise` at all**; it returns `(bool, list)`, and the raise is in the CALLER (`:2138`).
   ⇒ design consequence: a §Ch24 leg calling it directly gets `(False, reasons)` back and can DECIDE,
   rather than inheriting a terminal raise. *(Original text, kept as the record:)*
   ⚠ **ONE RECORDED OBSTACLE, CHECK IT BEFORE BUILDING:** `team_is_ready(target)` (`:2135-2141`) raises
   terminally and its Crunch clause (`:1903`) hardcodes `CRUNCH_LEVEL = 47` instead of `target` — the
   surviving reason §Ch23's **sub-47** stepping was refuted on 2026-09-08. ✅ **VERIFIED 2026-09-18 — and the inference was right for a STRONGER reason than I gave.** *(This read “INFERRED, unverified: it does not bite stepping UPWARD from 47.”)* The gate is **`if "Crunch" not in moves`**; `CRUNCH_LEVEL` only picks the WORDING of the failure reason, and **the clause never consults `target` at all** (`victory_road.py:1902-1912`) — *“⛔⛔ ASSERT THE MOVE, NEVER THE LEVEL THAT USUALLY GRANTS IT … The level is a PROXY; the move is the requirement.”* ⇒ a Mightyena that KNOWS Crunch passes at any target; stepping upward is unaffected.
   ⚠⚠ **BUT A PRECONDITION NOBODY HAD STATED, AND IT IS PERMANENT:** if Mightyena does NOT know Crunch, `team_is_ready` fails at **every** level (*“there is NO Dark TM in Emerald to recover with”*) ⇒ **every step would raise, forever.** ⇒ **the leg must check Crunch ONCE up front and fail fast**, not discover it per step. The normal §Ch23 lineage satisfies it by construction.
   ⛔⛔ **AND MY OWN FRAMING OF THIS ITEM WAS REFUTED BY AN ADVERSARIAL PASS, WHICH I THEN VERIFIED.**
   I wrote that the next step was to *price a heal round-trip and settle the ground question*.
   **`estimate_frames_to_level` contains NO heal term and NO travel term** — its whole body is
   `ceil(needed_exp / xp_per_battle) * FRAMES_PER_WILD_BATTLE` — so **pricing the heal cannot move the
   refusal by one frame**, and under that guard's model the ground choice is worth **~5%** against a
   required **2.05×** cut. *(The recon said 4.79% and this item says +5.0% forty lines above: same ratio, different denominators — 301.2/286.9 is +5.0% of 1F, 4.76% of B1F. Reconciled here rather than left reading as a contradiction.)* ⇒ **ground selection is two orders of magnitude from the decision.**
   Full measured economics, the landmine below, and what is still unproven: `ai-research-notes/2026-09-18-ch24-grind-economics-MEASURED.md`.
  ‼ **UNTIL THIS SHIPS, DO NOT WIRE SEGMENT 24.** The handoff's standing list of three prerequisites (position-independent marker · leg 2 · a `ch24_chapter_done()` that is not `SYS_GAME_CLEAR` alone) is INCOMPLETE without it, and all three could be satisfied while the bot still loses every run.
- [x] ⛔⛔ `#24-trainestimatorcal` — **FILED AND WITHDRAWN THE SAME DAY (2026-09-17). CLOSED.** I re-discovered a SETTLED question and filed it as a defect; correcting the numerator while leaving the denominator was the error, and both are Route-102-calibrated so the errors cancel.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)**. ‼ The rule it left behind lives in `08-MISTAKES.md`: **when two analyses of the same quantity disagree by a factor, check the DENOMINATOR before believing either.**
- [x] ⭐⭐⭐ `#24-tailprobe` — **NEW AND DONE 2026-09-17 (late). WALLACE IS BEATEN AND THE GAME IS CLEARED. THE ENDGAME TAIL IS MEASURED END TO END.**
  `--driver ch24tailprobe` (NEW `Ch24TailProbeMode`, OBSERVE-ONLY) from the pinned `post_hall4_door.ss1`: stepped onto `(5,2)`, won the Champion fight (`on_battle_ended` latched **`outcome=<BattleOutcome.Won: 1>`**, `whiteouts=0`), rode the post-battle cutscene, the Hall of Fame MAP, the Hall of Fame SCREEN, **10,353 frames of un-skippable credits** and a `SoftReset(RESET_ALL)`, and came back **controllable in `LITTLEROOT_TOWN_BRENDANS_HOUSE_2F (4,2)` with `IS_CHAMPION=True` and `SYS_GAME_CLEAR=True` in BOTH RAM AND FLASH.** Full frame table + answers: `ai-research-notes/2026-09-17-ch24-legB-TAIL-MEASURED.md`; evidence `evidence/2026-09-17-ch24tailprobe-*`.
  ⭐⭐ **Q7 ANSWERED — THE SINGLE UNMEASURED LOAD-BEARING FACT IN THE WHOLE LEG-B SPEC: flash written BY THE GAME survives `_core.reset()`.** The profile started at **`<no save data>`**, the Hall of Fame wrote the save slot mid-run, and the reboot went **`CB2_MAINMENU` → `CB2_CONTINUESAVEDGAME`** — not `NAMING_SCREEN`. ⇒ trap T17 does not bite on this path, because the game itself populates flash before the reboot.
  ⭐ **Q2 ANSWERED — a leg-B driver does NOT need to defeat the 20,000-frame no-progress detector.** The longest in-tail constant-signature stretch reached only the **x8000** rung. ‼ The `HANG CONFIRMED` in the log is at **f69937, AFTER the ACCEPTANCE line, with `ctrl='<none>'`** — the post-acceptance artifact every probe produces. ⇒ **the spec's suggested sub-generator-cycling trick is unnecessary machinery**, and the probe deliberately did not implement it so the question could be measured rather than hidden.
  ‼ **THE TAIL IS ~54% LONGER THAN THE SPEC ESTIMATED** — 19,914 frames excluding the fight, vs ~12,950 predicted (the credits alone are 10,353). ⇒ **budget a leg-B driver at `--frames ≥ 120000`**, not 30,000. The fight itself was **29,959 frames**; total door-step → controllable = **49,873**.
  ⛔⛔ **MY OWN FIRST RUN WAS WRONG, AND BOTH RUNS ARE COMMITTED.** v1's stop condition was `OVERWORLD ∧ controllable ∧ battle_ended`; it fired on the FIRST post-battle overworld frame — still in the Champion's room, `IS_CHAMPION=False` — so it measured NONE of the tail. **`player_avatar_is_controllable()` READS TRUE UNDER `lockall`**, which the `story-drive` skill states in as many words. v2 adds two conjuncts, the load-bearing one being **"has LEFT the Champion's room"**. `...-v1-STOPPED-EARLY.stdout.txt` is kept because the mistake instructs better than the fix.
  ⛔ **WHAT THIS DOES NOT ESTABLISH:** it is a PROBE, not a chapter — **Segment 24 is still NOT wired**. Wallace was beaten **once**, from a fully-healed party with 1 Revive; that is one trajectory, not a win rate. `presses=19056` is duty-cycle ticks issued, **not prompts consumed**. And the gauntlet is driven as a **CHAIN OF PINNED FIXTURES** (`atdoor → sidney → phoebe → glacia → drake → hall4_door → cleared`), every link individually driven — **no single run has gone door-to-credits.**
  ⚠ The profile's `current_save.sav` now holds a CLEARED game (the Hall of Fame force-saves). Harmless — every fixture is a `.ss1` — but `get_save_data()` on this profile reads a champion save from now on.
- [x] ✅✅✅ `#24-hall4stopshort` — **NEW AND DONE 2026-09-17 (late). THE BOT WALKED TO THE CHAMPION'S DOOR AND DELIBERATELY DID NOT ARRIVE — the first STOP-SHORT leg this project has built.** `--driver ch24hall4` (NEW `Ch24Hall4Mode`) from pinned `post_drake_L75.ss1`: `ACCEPTANCE: PASS`, all 5 readings, `missing=[]`, **`battles=0`**, `whiteouts=0`, `H-STOPSHORT ... tile=(5,3) on_hall4=True right_tile=True`. Minted + pinned **`post_hall4_door.ss1`** (`1f15cc400218`) — *the cleanest state in the gauntlet*: fully healed (`gauntlet_ready=True`, `HEAL PLAN=[]`), Ice Beam intact, one tile from the Champion, nothing fought. Predictions filed + GRADED (`ai-research-notes/2026-09-17-ch24hall4-PREDICTIONS.md`); evidence `evidence/2026-09-17-ch24hall4-*`.
  ⛔⛔ **WHY IT MUST STOP SHORT, VERIFIED AT SOURCE:** `HALL4 (5,2)` → `CHAMPIONS_ROOM (6,12)`; on arrival `LoadMapFromWarp` → `ClearTempFieldEventData` zeroes `VAR_TEMP_1`, the room's `OnFrame` (`map_script_2 VAR_TEMP_1, 0, ..._EventScript_EnterRoom`) matches on the FIRST controllable frame (`TryRunOnFrameMapScript` is polled at `field_control_avatar.c:150`, ABOVE the `tookStep` check at `:157`), and its first command is `lockall`. `"allow_escaping": false`; NO defeated-flag guard anywhere in that room's script, and `trainerbattle_no_intro` skips the `GetTrainerFlag` path entirely ⇒ **a re-entry re-fights Wallace at full strength.** There is no frame in which a driver can enter and stop; win or whiteout are the only exits.
  ‼ **THE ONE THING THAT WOULD HAVE BUILT IT WRONG:** rooms 1-4 all crossed doors with `_pass_through_door`, which makes the warp the navigation DESTINATION by construction. Pointed at (5,2) it does not stop at a door — it starts the championship battle. This leg uses **`navigate_to(HALL4,(5,3))`**, MAP-LOCAL, whose docstring states warps are not used automatically unless the door IS the destination. ⭐ A **TRIPWIRE** in the class refuses to run at all if `STOP_SHORT_TILE` is ever edited to equal `CHAMPION_DOOR_TILE`.
  ⛔ **THERE IS DELIBERATELY NO "OVERSHOOT" FAULT ARM** — it would start the fight and spend the fixture. That is a leg-B measurement, never a fault injection.
  ‼ **A CONFOUND I CAUGHT IN MY OWN ARM AND FIXED:** the first `NOROOMHEAL` run omitted `CH24_HALL4_CAPTURE` and so failed on **two** independent reasons (`H-HEAL` *and* `H-CAPTURE`) — exactly the flaw `#24-healgradearm` had just been closed over. Re-run isolated it: **`missing=['H-HEAL']` ALONE**. Only the isolated run is committed as the arm.
  ⭐ **THE DISMISS MODEL NOW HOLDS ACROSS THREE ROOMS** (roughly linear in the PREVIOUS room's speech length): Glacia 2 pages → 35 presses, Phoebe 4 → 77, **Drake 6 → 128**.
  ⛔⛔ **FOR WHOEVER GRADES ROOM 5: DO NOT USE THE `DEFEATED_ELITE_4_*` FLAGS.** The Hall of Fame script CLEARS all four and resets `VAR_ELITE_4_STATE` to 0 (`event_scripts.s`) BEFORE `special GameClear` ⇒ **they read FALSE ON SUCCESS.** Grade on `IS_CHAMPION` (flag **2175**, verified in `emerald.txt:1061`) — and per `#24-gameclearflag` `SYS_GAME_CLEAR` alone is not sufficient either. ‼ **ONE REVIVE REMAINS and there is NO heal after this fixture.**
- [x] ✅✅✅ `#24-drakeL75` — **NEW AND DONE 2026-09-17 (late). DRAKE IS BEATEN AT L75 — FOUR OF FIVE ELITE FOUR ROOMS — AND THE UNIT COMPOSED A FOURTH TIME ON A *DAMAGED* PARTY.**
  `--driver ch24drake` (NEW `Ch24DrakeMode`) from the pinned `post_glacia_L75.ss1`: `ACCEPTANCE: PASS`, all 7 readings, `missing=[]`, `battles=1`, `whiteouts=0`, **`DEFEATED_ELITE_4_DRAKE=True`**, exit door OPEN in the live grid. Minted and pinned `post_drake_L75.ss1` (`51cd43a8e427`, `VAR_ELITE_4_STATE=4`). Evidence: `evidence/2026-09-17-ch24drake-{TREATMENT,VACUITY-WRONG-ROOM,VACUITY-OWN-OUTPUT,FAULT-NOROOMHEAL}.stdout.txt`; predictions filed and GRADED in `ai-research-notes/2026-09-17-ch24drake-PREDICTIONS.md`.
  ⭐⭐ **THE FIRST ROOM ENTERED ON A PARTY THE PREVIOUS ROOM BROKE.** The start fixture carried a **FAINTED Mightyena (0/230)** and Wailord at 188/396. The between-rooms heal repaired it live — `heal_actions=3`, `Mightyena 0/230 → 230/230`, `Wailord → 396/396`, bag `Revive 3→2` — and ⭐ **the offline `plan_healing` projection matched the live run ACTION FOR ACTION**, which is the first time this project has predicted a heal plan before driving it.
  ⭐⭐ **A RECON'S ADVERSARIAL ARM FOUND THAT THE GRADE COULD NOT FAIL ON A BROKEN HEAL, AND IT WAS FIXED BEFORE THE DRIVE.** `taken.add("D-HEAL")` is unconditional (it must be — an empty plan is the common case) and a raising heal is deliberately swallowed into `R["heal_error"]` (the zone is sealed; refusing strands the bot). ⇒ `ok` now also requires **`heal_ready is True`**. ✅ Non-vacuous and non-retroactive — ‼ **but the evidence is rooms 2-3, NOT 1-3, and the first draft of this line overclaimed it (Tier 1 caught it):** rooms 2 and 3 MEASURED `ready=True` (`P-HEAL actions=1 ready=True`, `G-HEAL actions=0 ready=True`), while **room 1 (Sidney) never computed the reading at all** — it was driven by `Ch24ProbeMode`, which has no heal step (its readings are `P24-*`). The conjunct is still non-retroactive for Sidney, but because his grade does not USE it, not because he measured it.
  ‼‼ **HONEST SCOPE — THE ARM DOES NOT PROVE THE CONJUNCT.** `NOROOMHEAL` failed on `missing=['D-HEAL']`, which it would have done **with or without** the conjunct. The case the conjunct actually covers — *the heal RAN and left the party unready* — is **still untested**; see `#24-healgradearm`.
  ⭐ **BUT THE ARM EARNED ITS KEEP ANYWAY — IT IS THE FIRST ROOM WHERE IT IS NOT VACUOUS** (room 3's plan was `[]`, so arm ≡ treatment). Skipping the heal still BEAT Drake, but: **Zigzagoon `48/48 → 0/48`** (the mule was sent in and KO'd; untouched in the treatment) and **Full Restore `3 → 0` — the ENTIRE stock burned IN battle** while **35 Hyper Potions went untouched**. ⇒ the heal is load-bearing in a measurable way.
  ⛔ **"ROOM 4 IS A RENAME OF ROOM 3" IS 80% RIGHT AND ITS STATED FORM IS WRONG.** (1) The rename names TWO map constants and there are **THREE** — the START map must become `GLACIAS_ROOM` or the premise refuses its own input. (2) Drake's `EventScript_Defeated` runs **two extra opcodes no other room has** (`setvar VAR_0x8004, FANCOUNTER_DEFEATED_DRAKE` + `special Script_TryGainNewFanFromCounter`) before `setflag`; verified INERT at `src/field_specials.c`, but the rooms are NOT byte-identical. (3) Drake's room reuses **Sidney's** `OnWarp` (the decomp comments on it). (4) `VAR_ELITE_4_STATE` gate is `==3`, sets 4.
  ⭐ **TEXT COUNTS, READ AT SOURCE — Drake inverts Glacia.** In-battle `Text_Defeat`: Drake **0 `\p` (1 page)** vs Glacia's 3 — Glacia was the outlier and Drake reverts to the Sidney/Phoebe shape. `Text_PostBattleSpeech`: Drake **5 `\p` (6 pages)**, the LONGEST of the four (Sidney 2, Phoebe 4, Glacia 2, Drake 6) — and that parks for **room 5's** dismiss, ~110 presses against a 500-press budget.
  ⛔⛔ **ROOM 5 IS *NOT* THE FIFTH INSTANCE — AND THE PROOF IS NOW STRONGER THAN "no flag guard".** Wallace's `object_event` carries **`"script": "0x0"` and `"flag": "0"`** ⇒ **he is not interactable at all**, so the unit's "navigate beside the trainer and press A" step has nothing to press. ⚠ And **HALL4 is 31 steps, not 10** — every budget copied from a 10-step hall must be re-derived.
  ‼ **THE REVIVE CLIFF IS HERE: 2 REVIVES REMAIN**, and the bot does not use them in battle — ⛔ **NOT because the game forbids it**: `KI-100` says OUR call site sets `allow_revive=False` (`battle_items.py:165`) pending a PID-grounded index probe, so the Wallace fight can absorb at most 2 faints and only at the single remaining between-rooms heal.

- [ ] ⭐⭐ `#24-healfullrestorewaste` — **NEW 2026-09-17 (late). `plan_healing` BURNS A FULL RESTORE ON A SCRATCH WHENEVER THE TARGET'S MAX HP IS BELOW 200, AND GATE #36 CANNOT SEE IT. ✅✅ **REPRODUCED HERE 2026-09-17 (late) — it began as an agent's note and is now OUR measurement.**
  **THE CLAIM:** `plan_healing` picks the "cheapest sufficient" item by `effective_heal`, which returns **`total_hp`** for a Full Restore — so on any mon with `total_hp < 200` (Castform **103**, Zigzagoon **48**) a Full Restore outranks a Hyper Potion (flat 200) and is spent on minor damage. Reported measured: `Castform 90/103 → ['Full Restore']`. Gate #36 is blind because its hand-made bag holds Potion/Super Potion that **the real gauntlet basket does not contain**; run the same check against the gate's own realistic `BASKET` and it picks Full Restore.
  ✅✅ **THE MECHANISM, READ AT SOURCE AND THEN RUN.** `overworld_items.py:222-227`: `healers = [(effective_heal(p, mon.total_hp), n) ...]`, then `sufficient = sorted((h for h in healers if h[0] >= missing), key=lambda h: (h[0], h[1]))` and `pick = sufficient[0][1]`. `effective_heal` returns **`total_hp`** for a Full Restore (`:108-109`) but a flat **200** for a Hyper Potion ⇒ for any mon under 200 max HP the Full Restore sorts LOWER and wins “cheapest sufficient”. **MEASURED by calling the pure function against the REAL basket** (32 Hyper Potion / 2 Full Restore), only the HP value constructed: `Castform 90/103 -> ['Full Restore']` · `Zigzagoon 40/48 -> ['Full Restore']` · **CONTROL** `Sceptile 73/205 -> ['Hyper Potion']`. ⇒ the boundary is exactly `total_hp < 200`, and it is TOTAL HP, not damage.
  ⭐ **AND ONE ROW CORRECTED MY OWN EXPECTATION:** `Wailord 188/396 -> ['Full Restore']` is **CORRECT**, not the bug — `missing = 208 > 200`, so the Hyper Potion is not sufficient at all and only the Full Restore qualifies. That is the item's genuine use case, and it is exactly what the live `ch24drake` treatment spent. ⇒ **do not “fix” this by making Full Restore always lose.**
  ⭐ **CORROBORATING (but NOT the same code path, do not conflate):** the `ch24drake` `NOROOMHEAL` arm measured the **in-battle** policy spending **all 3 Full Restores while using 0 of 35 Hyper Potions**. That is `battle_items.py`, not `plan_healing`. Two paths, one smell — a measurement that separates them is the first job.
  ✅ **WHY IT DID NOT BITE ROOMS 1-4:** every mon it would have hit is a bench mule that never took damage, and the battlers' max HP are all **above** 200 (Sceptile 205, Mightyena 230, Swellow 232, Wailord 396) — `post_drake_L75`'s plan correctly chose a **Hyper Potion** for Sceptile at 73/205. ⇒ the boundary is real and the gauntlet has been sitting just on the safe side of it.
  ‼ **WHY IT MATTERS NOW:** only **2 Full Restores** remain for Wallace, and one careless stop that tops up Castform (103) and Zigzagoon (48) would zero the stock.
  **FIRST STEP:** reproduce it HERE against the real `LEAGUE_BASKET` before touching `overworld_items`/`effective_heal`, then rebuild gate #36's case from the REAL basket rather than a hand-made bag. *(A fixture invented to demonstrate a defect will demonstrate it — and a bag invented to test a chooser will exonerate it.)*

- [x] ✅✅ `#24-healgradearm` — **FILED AND CLOSED 2026-09-17 (late). THE `heal_ready` GRADE CONJUNCT IS NOW **PROVEN LOAD-BEARING** BY AN ARM IN WHICH IT IS THE ONLY THING THAT CAN FAIL THE RUN.** *(Filed as UNPROVEN in the same session and shut with a measurement rather than an argument — the honest declaration is kept below because it is what produced the arm.)*
  `Ch24DrakeMode`'s grade now requires `heal_ready is True`. The `NOROOMHEAL` arm FAILED — but on **`missing=['D-HEAL']`**, which it would have done **with or without** the conjunct, because the reading lives inside the `else` branch the arm skips. ⇒ **the arm does not exercise the conjunct.**
  **THE CASE THE CONJUNCT ACTUALLY COVERS** is *the heal RAN and left the party unready*: `D-HEAL` is added unconditionally, `missing` is empty, and only `heal_ready` can fail the run. **Untested.**
  ✅✅ **THE ARM WAS BUILT AND RUN: `POKEBOT_CH24_FAULT_HEALNOOP`** (registered in `29-DISABLED-FEATURES-REGISTRY.md`). ⭐ **IT FAKES NOTHING** — no synthetic party, no invented bag, no monkeypatch: it calls the REAL production `heal_party_from_bag` with the REAL bag and `max_actions=0`. `plan_healing` breaks at `len(plan) >= max_actions` (`overworld_items.py:169`) so the plan is EMPTY, and `heal_party_from_bag` then reports `heal_actions=0` with `heal_ready = party_is_gauntlet_ready(before)` = **False** (Mightyena is fainted). Same code path as the treatment, bounded to do nothing.
  ✅ **MEASURED:** `D-HEAL actions=0 ready=False` · **`missing=[]`** (all 7 readings TAKEN, D-HEAL included) · `failure=None` · `⛔ GRADE: heal_ready=False` · `ACCEPTANCE: FAIL`. ⇒ **with `missing=[]` and `failure=None` the OLD grade (`ok = not missing and failure is None`) would have returned PASS** — the conjunct is the only thing failing it. That is the discriminator `NOROOMHEAL` could not provide. Evidence: `evidence/2026-09-17-ch24drake-FAULT-HEALNOOP.stdout.txt`. *(Rule 8 satisfied: the claim “without X the bug survives” was paid for with an arm, not asserted.)*

- [ ] ⭐⭐ `#24-harnessflagaudit` — **NEW 2026-09-17 (late), MEASURED. `audit_flag_names.py` HAS NEVER SCANNED `story_harness.py`, AND THERE ARE LIVE PHANTOM NAMES IN IT.**
  **THE GAP:** `tools/story-dev/audit_flag_names.py:30` globs `sandbox-pokebot/modules/story/*.py` plus one `story_mode.py`. **`tools/story-dev/story_harness.py` is not in the list**, so **144 resolvable flag/var names there are UNAUDITED** — measured by replicating the audit's own method over that file. ‼ This is the SAME shape the audit's own docstring describes for 2026-08-12 (*"the audit ran for weeks against exactly two hand-written paths while the chapters moved OUT"*) — the harness is now where a lot of grading logic lives.
  ⛔⛔ **AND IT IS NOT HYPOTHETICAL — TWO PHANTOM NAMES ARE LIVE CALL SITES TODAY** (not comments; I checked each line): **`get_event_flag('FLAG_ADDED_MATCH_CALL_TO_POKENAV')`** at `story_harness.py:592`, and **`get_event_var("VAR_RESULT")`** at `:396`, `:508`, `:551`.
  **ROOT CAUSE, VERIFIED AT SOURCE:** our tables store names **UNPREFIXED** — `modules/data/event_flags/emerald.txt:252` is `304 ADDED_MATCH_CALL_TO_POKENAV`, and **0 of 1,164 flag rows and 0 of 256 var rows carry a `FLAG_`/`VAR_` prefix**. `modules/memory.py:336` is `if flag_name not in _event_flags: return False` and `:393` is `if var_name not in _event_vars: return -1` — **there is NO prefix stripping.** ⇒ the decomp-style spellings resolve to nothing.
  ‼‼ **NOTE THE ASYMMETRY, IT DECIDES HOW DETECTABLE EACH ONE IS.** An unknown **FLAG returns `False`** — indistinguishable from "the flag is genuinely false", so it is silent forever. An unknown **VAR returns `-1`**, which is outside the legal 0..65535 range and therefore *detectable* if anything checks. ⇒ **a predicate that cannot distinguish "false" from "I could not find that name" is not a predicate.** *(Measured directly this session: `get_event_flag('DEFEATED_ELITE_4_NOBODY')` returns **False** and does NOT raise.)*
  ⚠ **SCOPE — these are OLD PokéNav probe drivers (`story_harness.py:363-592`), NOT §Ch24**, and they are PRE-EXISTING. Nothing in the §Ch24 work depends on them. `Ch24GlaciaMode.VICTORY_FLAG` and `Ch24PhoebeMode.VICTORY_FLAG` were both proven real against `emerald.txt` before use.
  **THE FIX HAS THREE PARTS AND THE ORDER MATTERS:** (1) ⛔ **Do NOT just add the file to the glob** — the audit would still see almost nothing, because it matches `get_event_flag("LIT")` while the harness idiom is **`VR._flag("NAME")`**, and its constant resolver `const_def` is **`^`-anchored** so it misses **indented CLASS attributes** like `VICTORY_FLAG`. Both patterns need widening (verified: with them widened, `VICTORY_FLAG` resolves correctly — that is the positive control). (2) Decide what `VAR_RESULT` was *meant* to read — **there is no `RESULT` var under any spelling**, so this is not a rename, it is an unanswered question about what those probes were measuring. (3) Only then extend the gate, and **FAULT-TEST it**: prove it fires on a planted phantom and prove it does NOT fire on the many decomp-style `FLAG_*`/`VAR_*` names that appear in COMMENTS and DOCSTRINGS throughout that file (there are many — a gate with false positives teaches the reader to bypass it).
  ⛔ **DO NOT MARK THIS DONE BY EXTENDING THE GLOB AND SEEING GREEN** — green would mean the patterns still match nothing, which is the failure this item is about.

- [x] ✅✅✅ `#24-glaciaL75` — **DONE 2026-09-17. GLACIA IS BEATEN AT L75 — THREE OF FIVE ELITE FOUR ROOMS. CLOSED.** Fixture `post_glacia_L75.ss1` is PINNED.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the drive, its readings and its evidence are there.
- [ ] ⭐⭐⭐ `#24-leg2spec` — ‼‼ **STUB MARKER (2026-09-17 evening): FOUR DESIGNS FOR THIS LEG WERE WRITTEN AND THEN ADVERSARIALLY REFUTED — **44 FATAL/SERIOUS FLAWS** — AND THE FULL REFUTATION IS IN `ai-research-notes/2026-09-17-ch24-leg2-DESIGN-REFUTATION.md`. READ IT BEFORE BUILDING.** It is a NOTE, not truth: THIS file wins on any contradiction, and every load-bearing claim needs verifying in our own harness first. ⚠ Several refuters caught the designs citing DRIFTED line numbers, so re-read any line a flaw cites. ⭐ **THE FOUR HIGHEST-VALUE RESULTS:** (a) the completion predicate must be `IS_CHAMPION` + `SYS_GAME_CLEAR` + a live-overworld machine-state conjunct — **never** the four victory flags, because the Hall of Fame itself clears them (`hall_of_fame.inc:7` → `event_scripts.s:628-634`, verified here at source), so a predicate built on them is false FOREVER after a perfect clear and loops the gauntlet; (b) **room 5 must NOT be the fifth instance of the room unit** — a refuter showed the Drake instance would fight Wallace *inside* the unit and the 3-attempt retry would re-fight him, which is exactly what O7 forbids; (c) the endgame tail's button presses must WAIT FOR THEIR TASK TO EXIST or a clean run hangs for ever at the Hall-of-Fame screen; (d) `ko_turns` breaks gate #39's C2. —— *the original spec:* **NEW 2026-09-17. THE §Ch24 GAUNTLET SPEC, FROM A 4-ANGLE RECON WHOSE ADVERSARIAL ARM DID ITS JOB. ⛔ THE “REPEATING UNIT × 5” MODEL IS REFUTED — DO NOT BUILD IT.**
  ‼ **WHAT THE ONE MEASURED TRAVERSAL ACTUALLY PROVED** (`SIDNEY (6,6) → door → HALL1 → PHOEBE (6,7)`, ~680 frames): **one post-victory NAVIGATION transition, from a fixture, with `battles=0` in it.** ⛔ It contains **no fight** — step (a) of the claimed unit was never exercised. ⛔ `ELITE_4_STATE 1→2` is **not a victory signal**: it is set by Phoebe's ENTRY script, so it grades the warp, not the fight — grade on `DEFEATED_ELITE_4_<NAME>` flags instead. ⛔ `(6,7)` is the CUTSCENE's destination (`WalkUp6` from the entry warp), not the bot's; the run ended beside Phoebe on a *reachability query* (`OK 1 wp`) — **a candidate is not an attempt**.
  **THE MAP CHAIN, CONFIRMED FROM THE `map.json` WARP TABLES:** `LEAGUE_1F → HALL5 → SIDNEY → HALL1 → PHOEBE → HALL2 → GLACIA → HALL3 → DRAKE → HALL4 → CHAMPION`. **HALL5 is the ENTRANCE hall.** Rooms 1-4 share one shape: entry warp **(6,13)**, exit door **(6,2)**, trainer at **(6,5)** (`MOVEMENT_TYPE_FACE_DOWN`, never despawns) permanently blocking the straight column — which is why the measured route is 6 waypoints and not 5.
  ⭐⭐ **THE RANKED OBJECTIONS — EACH ONE IS A BUILD REQUIREMENT:**
    **O1 ⛔ ROOM 5 IS NOT AN INSTANCE OF THE UNIT.** Entry warp is **(6,12)**, not (6,13). Its `OnFrame` gate is **`VAR_TEMP_1`** (a TEMP var, so it re-arms on every map load) and it `lockall`s, walks the player to (6,6) and starts Wallace **itself** ⇒ **no A-press trigger and no walk-to-trainer step**; a leg that navigates and presses A is racing a `lockall`. Its exit is a **scripted `warp` to HALL_OF_FAME**, not a door — the door it `setmetatile`s open is never used. Its post-battle chain is **~11 `MSGBOX_DEFAULT` stops**, not one.
    **O2 ⛔⛔ THE CHAPTER ENDS IN A CONSOLE REBOOT** — see `#24-gameclearflag`, filed separately because it is already wired into `chapters.py` and is a FALSE PASS waiting to happen.
    **O3 ⛔ PP IS NOT IN THE READINESS PREDICATE, AND CANNOT BE RESTORED IN THE SEALED ZONE.** `overworld_items.py:240-249` `party_is_gauntlet_ready()` tests fainted / status / HP fraction — **PP is not a term**. The healing allowlist (`:150-154`) has no Ether, Elixir or Leppa Berry, and `heal_party_from_bag` filters on `ItemFieldUse.Healing`, which excludes PP items by construction. ‼ **The League mart does not sell one either** — Ultra Ball, Hyper/Max Potion, Full Restore, Full Heal, Revive, Max Repel. **25 opposing Pokémon on one PP bar.** ⇒ this is `#24-grindppstall`'s exact predicate with the Poké Center removed, and it is the objection most likely to hit first.
    **O4 ✅ THE WHITEOUT QUESTION IS SETTLED — AND OUR DOC'S STATED REASON WAS WRONG.** `DoWhiteOut` halves money, heals, and warps to `lastHealLocation`; `PokemonLeague_1F`'s `OnTransition` sets that to `HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE` = **`MAP_EVER_GRANDE_CITY` (18,6), OUTDOORS** — not the lobby beside the nurse. ⛔⛔ **AND `EventScript_WhiteOut` CALLS `ResetEliteFour`, WHICH CLEARS ALL FOUR `DEFEATED_ELITE_4_*` FLAGS AND ZEROES `ELITE_4_STATE`** ⇒ **a whiteout anywhere costs the WHOLE gauntlet**, not one room. Recoverable, but five fights behind and at half money. *(The (18,6) figure was already right; the reason attached to it was not.)*
    **O5 ✅✅ CONFIRMED LIVE 2026-09-17 — THE ZONE SEALS BEHIND YOU, VIA TILES OUR MAP MODEL CANNOT SEE.** ⭐ `probe_e4_entry_seal.py` on the pinned `post_sidney_door_open.ss1`, measuring the ROM layout and `gBackupMapLayout` **on one map at one instant**:
        ENTRY (5,12) (6,12) (7,12) (5,13) (6,13) (7,13)   ROM=0 (open)     LIVE=3 (SEALED)
        EXIT  (6,1) (6,2)                                  ROM=1 (blocked)  LIVE=0 (OPEN)
        CONTROL floor (6,6) 0/0 · CONTROL wall (0,0) 1/1   — both AGREE, so a door divergence
                                                              is about the DOOR, not the reader
      ‼‼ **TWO DIVERGENCES IN OPPOSITE DIRECTIONS, FROM ONE MECHANISM.** A single-direction result could be waved away as *“our ROM reader is just wrong about this map”*; two cannot — they prove the two grids describe genuinely different state and pin which one the game walks on. ⇒ **`KI-74` IS ONLY HALF THE HAZARD:** it is the case where the planner REFUSES a route that exists; this is the case where it CONFIDENTLY PLANS a retreat the game refuses. ⚠ *“Sealed” is `collision != 0`, and the observed value is **3**, not 1 — our planner blocks on `!= 0` (`map_path.py:137`) and so does the live-grid consumer (`sootopolis.py:997`). The probe's first predicate asserted `== 1` and printed “THE DECOMP CLAIM IS NOT CONFIRMED” over a confirmation; the PREDICATE was wrong, not the claim.* —— *the original decomp finding:* `elite_four.inc` `WalkInCloseDoor` sets (5..7,12) and (5..7,13) **impassable at runtime**, re-applied `ON_LOAD` so it survives save/load and re-entry; the backward hall warps are `MB_NORMAL`, which `IsWarpMetatileBehavior` rejects, so they are **provably inert**; and every League map has **`allow_escaping: false`** ⇒ no Escape Rope, no Dig, no Teleport. ⇒ **the nurse and the mart are unreachable from HALL5 onward** — any between-rooms heal that is not BAG-ONLY is fiction. ‼‼ **AND THIS IS A MIRROR-IMAGE OF `KI-74`:** the ROM grid says those tiles are PASSABLE, so a ROM-cached planner will confidently route a retreat the game refuses. Use the live `gBackupMapLayout` grid (`sootopolis.py:871 _live_collision_grid`), never the static layout.
    **O6 ⚠ HALL4 ALONE COSTS THE ENTIRE MEASURED UNIT.** It is `11×34` (warps (5,33)→(5,2) = **31 tiles**) where halls 1/2/3/5 are `11×13` (10 tiles). At the measured ~21.9 frames/tile — and **`allow_running: false` on every League map**, so the 8-frame running step does not exist — that is **~680 frames for one corridor**, i.e. what the whole measured unit cost. A per-room frame budget derived from 680 aborts inside HALL4 having done nothing wrong.
    **O7 ⛔ RE-ENTRY IS IDEMPOTENT FOR ROOMS 1-4 AND RE-FIGHTS UNCONDITIONALLY IN ROOM 5.** Rooms 1-4 guard the trainer on `goto_if_set FLAG_DEFEATED_ELITE_4_<NAME>`. The Champion's room has **no flag guard anywhere**, and `trainerbattle_no_intro` carries no `HasTrainerBeenFought` check ⇒ **every entry is another full Wallace battle**. ⛔ There is also **no value of `ELITE_4_STATE` that means “in the Champion's room” or “Wallace beaten”** — it sits at 4 from Drake's entry until game clear. ⇒ a retry policy of “re-enter and check whether the trainer is done” is correct for four rooms and starts an unwanted championship battle in the fifth.
    **O8 ⚠ THE ITEM ARITHMETIC DOES NOT CLOSE.** `battle_items.py:46` `MAX_ITEM_USES_PER_BATTLE = 4` ⇒ the per-battle cap binds long before the 30 Hyper Potions do (≤ 20 in-battle uses across five fights). `:165` **`allow_revive=False` by default** (`KI-100` — revive targets a different index space, and `handle_fainted_pokemon` has a three-deep index-space bug history), so in-battle revival is OFF; overworld revival is capped at **3 Revives for 5 one-way rooms**. The only Sidney win on record finished with **five of six fainted**.
    **O9 ⚠ THE DISMISS IS A COVERAGE GAP, NOT AN INPUT BUG.** `libmgba.py:471-476` genuinely produces a `JOY_NEW` edge every other frame, so the press cadence is sound — stated plainly because it would be easy to blame the wrong layer. The gap is that room 5 + Hall of Fame carry **~13-15 button-gated stops**, and `ProfBirch_EventScript_ShowRatingMessage` uses a raw `waitbuttonpress` that is **NOT an overworld text printer** ⇒ the `KI-93` dismisser, gated on `get_text_printer(0).state == WaitForButton`, **cannot see it**.
    **O10 ⚠ THE HARNESS WATCHDOG CANNOT GRADE THE TAIL.** Its no-progress signature reads controller / game state / battle instruction / coords; after `SetMainCallback2` those are stale or throwing, and after `SoftReset` they are garbage. Constant ⇒ a false HANG on a chapter that actually succeeded; flickering ⇒ the lane burns to `MAX_FRAMES_PER_RUN`. **Neither branch is a correct verdict, and there is no third.**
  ✅ **WHERE THE MODEL SURVIVES, STATED PLAINLY:** rooms **2, 3 and 4 really are** room 1's shape — same object at (6,5), same warps, same scripts; Drake's only extra is a fan-counter `special` that prints nothing. The exit-door step and the hall walk are sound, and the sidestep hazard is dead (measured twice: all 15 backward tiles `'Normal'`, and a live `warped=False`). **Hall geometry may be read STATICALLY** — no hall has an `ON_LOAD`, `ON_FRAME`, object or coord event, so nothing rewrites those tiles and `KI-74` does not apply there. ⇒ **BUILD ROOMS 1-4 AS THE UNIT, AND BUILD ROOM 5 PLUS ITS TAIL AS A SEPARATE LEG WITH ITS OWN GRADE.**
  ⭐ League 1F carries a **Nurse at (3,2)** and a **Mart at (16,2)** *inside* the gate (the gate itself checks only `FLAG_BADGE06_GET`) — the natural pre-gauntlet heal/stock point, and per O5 the last one that exists.
- [ ] ⛔⛔⛔ `#24-gameclearflag` — **NEW 2026-09-17, VERIFIED AT SOURCE IN BOTH HALVES. THE §Ch24 COMPLETION FLAG FIRES ~20,000 FRAMES AND ONE CONSOLE REBOOT BEFORE THE GAME IS USABLE.** ‼‼ **READ THIS DISTINCTION BEFORE TOUCHING ANYTHING — I BLURRED IT ON THE FIRST WRITE-UP AND IT WOULD HAVE SENT SOMEONE TO ‘FIX’ THE WRONG FILE.** `chapters.py:288` grades Chapter 24 on **`flag("SYS_GAME_CLEAR")`**, and `chapters.py` is the **READOUT** — it answers *“which chapter is this run in?”* and dispatches no work (consumed by `progress.py` `detect_progress` / `detect_live`). ✅ **For a readout that is DEFENSIBLE** and should probably stay: once `SYS_GAME_CLEAR` is set the game genuinely IS cleared. `story_mode.py`'s Segment 23 block already states the rule — *“the readout answers which chapter this run is in; the gate answers whether the next segment may start. Both are correct. Do not collapse them.”* ⛔ **THE HAZARD IS THE DISPATCH GATE THAT DOES NOT EXIST YET.** `ch24_chapter_done()` has to be written, and the obvious implementation — reuse the milestone — is the trap, because in the decomp `src/post_battle_event_funcs.c` `GameClear()` sets `FLAG_SYS_GAME_CLEAR` at **line 30** and does `SetMainCallback2(CB2_DoHallOfFameScreen)` at **line 84** — a full main-callback swap OUT of the overworld, 54 lines later. ⇒ **the flag is true while the Hall of Fame screen, the credits and a `SoftReset(RESET_ALL)` are all still ahead.** From that instruction on, every reading the bot takes — map, coords, controllable, script context — is meaningless. ‼‼ **THE TAIL, READ FROM THE DECOMP:** HoF force-SAVES (`hall_of_fame.c` `Task_Hof_TrySaveData`), shows each mon for 120 frames, then **blocks for ever on `JOY_NEW(A_BUTTON)`** (`Task_Hof_ExitOnKeyPressed`); credits are **57 pages** *(corrected 2026-09-17 — this said 58; MEASURED two independent ways by a recon round and reproduced by its refuter)* and ⛔ **CANNOT BE FAST-FORWARDED ON A FIRST CLEAR** — the B-hold speed-up is gated on `gHasHallOfFameRecords`, which `GameClear` sets FALSE exactly when this is the first clear; THE END waits up to **7,200 frames** unless a key is pressed; then `SoftReset(RESET_ALL)`. **The player does not end up on a map — the GBA reboots to the title screen**, and CONTINUE resumes in **Littleroot, the bedroom**. ⚠ **LATENT, NOT LIVE — AND THAT IS EXACTLY WHY IT MUST BE FIXED BEFORE SEGMENT 24 IS WIRED.** `_play()` stops after Segment 23 today, so nothing reads this yet. The moment the gauntlet is wired, the chapter reports COMPLETE and hands a **rebooting emulator** to whatever runs next — a FALSE PASS, which is worse than a hang. ⇒ **§Ch24's `ch24_chapter_done()` must NOT be `SYS_GAME_CLEAR` alone** — it needs a conjunct that is only true once the machine is back in the overworld and CONTROLLABLE (the player ends up in **Littleroot, the bedroom**, after CONTINUE). ‼ And the shape to copy is §Ch21's, not §Ch23's: a conjunction of **flags and vars only, with NO `_on_map` term**, because the gauntlet is one-way and a position conjunct would go false for ever the moment the League door is crossed — which is the very defect that blocked wiring Segment 24 in the first place. ⚠ And the leg that fights Wallace owns ~13-15 button-gated stops plus a soft reset, none of which any code in this tree handles today (`soft reset` appears **0 times** across `05-KNOWN-ISSUES`/`07-CHANGELOG`/this file). ⭐ Found by the ADVERSARIAL recon angle; both halves re-verified here by reading `chapters.py` and the decomp directly.
- [ ] ⛔⛔⛔ `#24-ghostreplacement` — **REOPENED 2026-09-17 (evening). I MARKED THIS FIXED AND “A/B-PROVEN” THIS MORNING AND IT IS A MEASURED **NO-OP ON THE REAL PARTY**.**
  ⭐⭐ **THE MEASUREMENT** (`probe_ghost_replacement_real.py`, the SHIPPED `rank_replacement` run against the PINNED party `post_e4ice_FINAL.ss1` and a pure Ghost):
        slot 0  Mightyena  L75  incoming=0.5  best_outgoing=240   Crunch 240 / Bite 180
        slot 1  Zigzagoon  L19  incoming=0.0  best_outgoing= 95   Surf 95            <- CHOSEN
        slot 2  Sceptile   L75  incoming=1.0  best_outgoing=105
        slot 3  Swellow    L75  incoming=0.0  best_outgoing= 90   Aerial Ace 90
        slot 4  Wailord    L75  incoming=1.0  best_outgoing=142
        >>> PICKS slot 1 = **Zigzagoon L19**   key=(0, 0.0, -95.0, -1.0, -19)
  ⛔⛔ **IT SENDS AN L19 MULE INTO PHOEBE.** Worse than the L48 Swellow the item was filed for, because among the three `incoming=0.00` Normal-types the tie-break is `-outgoing`, and Zigzagoon's Surf (95) beats Swellow's Aerial Ace (90). ‼ The mules ARE eligible: benching means *do not TRAIN*, not *do not FIELD* (`story_mode.py:273-274`; `_excluded` is ally-only).
  ‼‼ **WHY THE FIX MISSED, AND IT IS A LESSON ABOUT THE ARM, NOT ABOUT THE RANKER.** `cannot_damage` separates only candidates whose best outgoing is **LITERALLY ZERO**. Swellow's **Aerial Ace is FLYING (1x on a Ghost)** and Zigzagoon carries **Surf** — neither is zero ⇒ the new term is `0` for every candidate, the tuple falls through to `incoming` exactly as before, and Ghost→Normal is 0x so the Normal-types score a PERFECT 0.00. ⛔ **GATE #39's C8 PASSES BECAUSE I BUILT ITS ARM OUT OF A SYNTHETIC MON** holding ONLY a Normal move — a mon that does not exist in this party. *A fixture invented to demonstrate a defect will demonstrate it.* The gate is green, the fix is real, and it does not reach the case it was filed for. ⇒ **C8 MUST BE REBUILT FROM THE PINNED PARTY**, and `probe_ghost_replacement_real.py` is the instrument that asks the question the right way.
  ⭐ **WHAT THE REAL FIX HAS TO EXPRESS:** the leading term must capture *how long this mon takes to win*, not *can it do anything at all*. A candidate that is IMMUNE but needs 12 turns is worse, in an unfleeable five-fight gauntlet with no PP restoration, than one that takes 0.5x and wins in 3. ⚠ A proposed shape is `ko_turns = ceil(foe_hp / outgoing)` as the leading (bucketed) term — ⛔ **UNVERIFIED**: it needs the foe's HP at the moment `choose_new_lead_after_faint` runs, and that is called both inside and outside the party menu (`battle_handler.py:515-522`); confirm `current_hp` is populated there before building on it, and fall back to a party-relative offensive bucket if it is not.
  ⭐⭐ **AND THE OBVIOUS REPLACEMENT TERM IS NOT SAFE TO GUESS — MEASURE FIRST.** The proposed `ko_turns = ceil(foe_hp / outgoing)` is computable: ✅ **VERIFIED 2026-09-17 that a foe's `current_hp` IS populated in battle** (`grind_stall_ppzero.ss1`, an in-battle save: `opponent.left_battler Zubat current_hp=77 total_hp=77`), which resolves the design's own UNVERIFIED flag. ⛔ **BUT IT MAY NOT SEPARATE THE CANDIDATES THAT MATTER.** At **L75 against her L48-51 team**, several of our battlers plausibly one-shot a Dusclops — and if Mightyena and Swellow both land in the `ko_turns = 1` bucket, the key falls through to `incoming` and picks **Swellow again**. That is the SAME failure as `cannot_damage`, one bucket further along: *a term that saturates stops discriminating exactly where the real party lives.* ‼ The offline probe above uses `base_power × effectiveness × STAB`, which is fine for “zero vs non-zero” but is **NOT** a damage prediction — it cannot answer the bucketing question. ⇒ **THE NEXT STEP IS A MEASUREMENT, NOT A PATCH:** drive into Phoebe, capture an IN-BATTLE fixture, and read `calculate_move_damage_range(...).max` for every battler against a real Ghost. Only then choose the leading term and its cap. ⛔ Do not ship a second key without those numbers — the first one was shipped on a synthetic arm and that is exactly why this item is open again.
  ✅✅ **DOES *NOT* BLOCK LEG 2 — CORRECTED 2026-09-17 (evening) BY AN ADVERSARIAL REVIEW THAT CAUGHT ME CONTRADICTING A SETTLED USER RULING.** *(This read “⇒ BLOCKS LEG 2.”)* **USER RULING 2** (`06-DECISIONS-LOG.md` 2026-09-17) is that **3 Revives is enough at L75 because faints should be RARE** — and the faint chooser only runs ON A FAINT. ⇒ a code path the user has ruled will seldom execute is a risk to **INSTRUMENT**, not a gate to stop behind; blocking on it would also invert this project's own instrument rule (*drivers answer CORRECTNESS questions*) by making a rare-path defect stop the build that produces the very measurement needed to fix it. ⭐ **AND THE FIX GENUINELY CANNOT BE MADE WITHOUT LEG 2**, which settles the sequencing: the leading term has to be chosen from **real in-battle damage numbers against a real Ghost**, and the only way to obtain those is to drive into Phoebe — which IS leg 2. ⇒ **BUILD LEG 2, AND MAKE THE CHOOSER'S DECISION A REQUIRED READING:** log EVERY candidate row `(index, pid, species, incoming, outgoing, hp_fraction, level, key)` plus `estimates_ok` / `estimates_failed` / `metric` at every faint — not just the winner, which is all `story_mode.py` logs today and is why “why did it pick that mon” is currently unanswerable. ‼ **AND DO NOT SHIP `ko_turns`:** a refuter DRY-RAN the proposed key against gate #39's own C2 and C9 rows and **C2 GOES RED** — so the obvious replacement breaks a case the function exists for. That is now a measured objection rather than my earlier instinct. See `ai-research-notes/2026-09-17-ch24-leg2-DESIGN-REFUTATION.md`. —— *the retracted claim, kept because its MECHANISM half is still correct:* - [~] ⚠ `#24-ghostreplacement` — **NEW 2026-09-17, A/B-PROVEN OFFLINE **ON A SYNTHETIC ARM ONLY** (see the reopening above). THE FAINT CHOOSER SENT OUR WORST ATTACKER INTO PHOEBE, AND A DEFENSIVE IMMUNITY IS WHY.** ⭐ **MEASURED on the real §Ch24 fixture party, running the SHIPPED pure `rank_replacement` against Phoebe's lead Dusclops (pure Ghost):**
      slot 2  Swellow    L48  incoming=0.00  best_outgoing=31.0   <- CHOSEN
      slot 4  Mightyena  L48  incoming=0.50  best_outgoing=68.0   <- never considered
  The key was `(incoming, -outgoing, -hp_fraction, -level)` and **`incoming` decides first**. Ghost→Normal is **0×**, so our three Normal-types score a PERFECT defensive 0.00 and win at term one, while Mightyena — which resists Ghost at 0.5 **and** is the only mon that hits it for double — loses there and is never considered. ⇒ after every faint against Phoebe's four pure Ghosts the bot sent in the battler with **one usable move and the only PP budget that does not cover the fight**; when Swellow is gone the same rule hands over Castform, then Zigzagoon. ‼‼ **“TAKES 0” AND “DEALS 0” ARE THE SAME TYPE RELATION READ FROM OPPOSITE ENDS**, so ranking on `incoming` alone does not merely tolerate the useless mon — it **actively seeks it**. ✅ **THE FIX:** `cannot_damage = 0 if outgoing > 0 else 1` leads the key. ⭐ It is a **NO-OP unless some candidate deals literally zero**: when all can damage the foe the term is 0 for everyone and the tuple falls through to exactly the old key; when none can, it is 1 for everyone and the ordering is likewise unchanged. ⇒ safe on a shared path by construction, not by hope. ✅✅ **A/B, gate #39 (`probe_faint_chooser_rank.py`), and the fault test is the proof:**
      WITH the fix      9/9 PASS  (C8 picks the Dark biter; C9 control still picks the RESISTANT mon)
      fix REVERTED      8/9 — and EXACTLY C8 goes red, picking `NormalOnly`
  ⇒ C8 detects the defect, the fix is what makes it pass, and **no other case moves**, which is the ordinary-case evidence this project requires for a change on a shared path. ⛔ **C9 IS NOT OPTIONAL AND IT CAUGHT MY OWN DATA BUG.** It proves the new term did not simply make the ranker prefer whoever hits hardest — among mons that CAN fight, defence must still decide first. It went RED on first run against a CORRECT subject, because my fake type chart never gave Water a resistance to Water, so both candidates tied at `incoming 1.0` and the harder hitter correctly won. *The probe's DATA was wrong, not the ranker.* ‼ **IT ALSO REFUTES A COMMENT IN OUR OWN TREE:** `victory_road.py:498-501` justifies benching Zigzagoon/Castform on the grounds that a full-HP party makes the ranking *“fall through `hp_fraction` … to `-level`, which then picks the STRONGEST”*. Against a pure Ghost the ranking **never reaches those terms** — it is decided at `incoming`, and it measurably picked L48 Swellow over L53 Sceptile. The stated safety mechanism did not hold for the one fight that file exists to prepare for. ⚠ NOT YET DRIVEN — no drive has fought Phoebe; this is the shipped pure function on real party data, with controls that fire (Sableye→Mightyena, Sealeo→Wailord).
- [x] ✅✅ `#24-planorder` — **NEW AND FIXED 2026-09-17. `TRAVEL_PLAN` SILENTLY SACRIFICED THE WRONG SWELLOW SLOT IF THE §Ch24 PREP PLANS RAN OUT OF ORDER — AND EVERY EXISTING CHECK PASSED IT.** ⭐ **THE DEFECT.** `TRAVEL_PLAN` teaches **Fly** over **Wing Attack**, and its written reason is that Wing Attack is *“strictly dominated by the Aerial Ace Swellow already knows”* — which is true **only after** `MOVESET_PLAN` has replaced **Peck** with **Facade**. Run them the other way round and Swellow still holds **Peck (35 BP, the worst move on the team)**: the teach destroys **Wing Attack (60 BP)** and KEEPS Peck. ‼‼ **AND `apply_moveset_plan` WOULD HAVE REPORTED SUCCESS** — species present ✓, doomed move known ✓, item in bag ✓, post-teach verification confirms Fly learned and Wing Attack lost ✓. ⇒ a **silent wrong-slot teach**, which is precisely the failure that function exists to refuse (`KI-88` burned single-use TMs over the wrong move on two separate drives), reached through the one door it had no check on. ✅ **THE FIX — STATED GENERALLY, NOT AS A SPECIAL CASE FOR SWELLOW** (`pokemon_league.py`, in the plan-building loop): refuse when the Pokémon still has an **outstanding `MOVESET_PLAN` change that the plan being applied does not itself carry**. `MOVESET_PLAN` therefore never trips on its own entries, and any future plan gets the guard for free. ✅✅ **A/B ON TWO REAL PINNED FIXTURES — `probe_plan_order_guard.py`, exit 0:**
      FAILING ARM  post_training.ss1  Swellow [Peck, Wing Attack, Aerial Ace, Quick Attack]
                   -> REFUSED, naming the outstanding [('Peck','Facade')]; teaches fired: []
      CONTROL      post_moveset.ss1   Swellow [Facade, Wing Attack, Aerial Ace, Quick Attack]
                   -> order guard did NOT fire; plan_todo [('Swellow',2,'HM02','Fly','Wing Attack')]
  ⛔ **THE CONTROL IS NOT THE OBVIOUS ONE, ON PURPOSE.** `post_ch24ready.ss1` looks like the natural control but its Swellow **already knows Fly**, so the plan is skipped for an unrelated reason and the guard is never evaluated — a green light measuring nothing. `post_moveset.ss1` is the only fixture where the guard must actively decide *“this order is fine”*. ‼ **THE PROBE'S FIRST CONTROL ASSERTION WAS WRONG, AND THE SUBJECT WAS RIGHT.** It asserted `refusal is None`; with the actuator stubbed, Swellow never actually learns Fly, so `apply_moveset_plan`'s OWN post-teach check correctly raised *“taught Fly … and it does NOT know it”*. ⇒ the arm incidentally proved a SECOND guard works, and the fix was to assert **“the ORDER guard did not fire”** instead of “nothing raised”. *Read the failing line before touching the thing under test.* ⚠ **LATENT, NOT LIVE:** the §Ch24 lineage happens to have been built in the right order (`post_ch24ready.ss1`'s Swellow reads `Facade, Fly, Aerial Ace, Quick Attack`), so nothing shipped is broken — which is the argument FOR a guard rather than a comment: the next lineage to run prep from scratch is the one that pays, and by then the reasoning will be a year old. ⭐ Surfaced by the 4-angle recon commissioned for the now-abandoned L60 repair — the plan died, the finding did not.
- [x] ✅✅ `#24-fixturelineage` — **RESOLVED 2026-09-17 BY MEASURING THE LINEAGE INSTEAD OF REPAIRING IT — ⛔ DO NOT GRIND `post_grind_L60.ss1`, AND DO NOT “REPAIR” IT.** ⭐⭐ **THE FINDING:** `post_grind_L60.ss1` is not a §Ch24 save that lost its moves. It **branched straight off `post_training.ss1`**, the §Ch23 training fixture, and skipped the ENTIRE prep chain (`post_league_shop` → `post_moveset` → `post_fly` → `post_slateport` → `post_icebeam` → `post_teachice` → `post_ch24ready` → `post_ch24_atdoor`). ⇒ it never had Ice Beam or Fly, and “repairing” it means re-running that whole chain — including the **~700,000-frame Abandoned Ship trip** for TM13 — to arrive at a party the other branch ALREADY IS. Its 13 levels are the only thing it owns, and levels are cheap here: MEASURED, **L75 costs ~3.7 h** from the prepped party. ✅ **MEASURED BY `probe_grind_lineage_route.py`** (two-sided control passed — PC door OK, League door FAIL reproducing `FIXTURES.md5`): `post_ch24ready.ss1` stands at EVER_GRANDE_CITY **(27,49)** carrying **Ice Beam, Fly, Aerial Ace, Facade, Strength**, and **(27,49) → VR apron (18,42) = OK, 22 waypoints** ⇒ it can WALK to the proven grind tile. Returning to the League door afterwards is **ONE Fly** (`CB_ExitFlyMap` special-cases Ever Grande — that is exactly how `post_ch24_atdoor.ss1` was made). ⇒ ruling in `06-DECISIONS-LOG.md` 2026-09-17. ⛔⛔ **THIS CLAUSE IS RETRACTED — THE OBJECTION WAS ALIVE AND IT CAME TRUE.** *(It read: “AND THE OBJECTION THAT MADE THIS LOOK HARD IS DEAD: ‘teach the moves, then the grind overwrites them again’ — the bot DECLINES level-up moves.”)* The grind overwrote **Ice Beam** at **L59**. See the retraction above and `#24-learnhmcoverage`. ✅ The LINEAGE ruling itself is unaffected: `post_grind_L60.ss1` is still a dead branch and `post_ch24ready.ss1` is still the right start — what changed is that the grind needed a CODE FIX first, not merely a better fixture. —— *the retracted text:* ‼ **AND THE OBJECTION THAT MADE THIS LOOK HARD IS DEAD:** *“teach the moves, then the grind overwrites them again”* — ⛔ **RETRACTED — see the retraction under `#24-fixturelineage`: Wailord LOST Ice Beam to Hydro Pump at L59 on the §Ch24 lineage, and the objection this sentence dismissed was correct. The cause was `#24-learnhmcoverage` (the coverage census ignored HM moves) and it is now fixed.** *(This read: “the bot DECLINES level-up moves (measured; Wailord crossed L52 and L59 keeping all four), and no battler learns anything between L61 and L75 anyway.” ‼ The L61-75 half is still true and is not the point — the loss happens at **L59**, below that window.)* —— *the original filing, kept for its measurements:* ✅✅✅ **UNBLOCKED THE SAME DAY — THE L60 PARTY IS FULLY REPAIRABLE, AND BOTH REPAIRS USE CAPABILITIES WE ALREADY SHIP.** MEASURED on both saves, with a +control (`BADGE08_GET` True on both) and a −control (an invented flag name → False, because `get_event_flag` returns False for an unknown name):
  * **FLY — re-teachable.** `HM02` is IN `post_grind_L60.ss1`'s TM/HM pocket (15 entries: TM03, TM04, TM08, TM34, TM39, TM40, TM42, TM47, TM50, **HM02**, HM03, HM04, HM06, HM07, HM08). HMs are infinite-use ⇒ just teach it.
  * **ICE BEAM — still in the world on THAT lineage.** `ITEM_ABANDONED_SHIP_ROOMS_B1F_TM_ICE_BEAM` reads **False** on `post_grind_L60.ss1` and **True** on `post_ch24_atdoor.ss1` ⇒ the L60 lineage never collected TM13, so `#24-icebeamtrip` (a BUILT leg, `--driver ch24icebeam`) can fetch it and `teach_move_from_bag` can teach it.
  ⇒ **REPAIR ORDER: teach Fly → run the Ice Beam trip → teach Ice Beam → THEN grind.** ⚠ `LANDMARK_POKEMON_LEAGUE` is **False** on the L60 save, so the `PokemonLeague` fly destination is not armed yet — that flag is set on FIRST League entry, and the save is standing mid-Victory-Road, so §Ch23 (built and wired) carries it there. ⛔ **STILL UNCOSTED:** the grind stall above is a separate, unexplained defect and repairing the moveset does not address it. —— **NEW 2026-09-16. THE TWO §Ch24 FIXTURES ARE DIFFERENT LINEAGES, AND THE STRONG ONE HAS LOST THE TWO MOVES §Ch24 EXISTS TO USE.** MEASURED by loading both saves and printing movesets:
  * `post_grind_L60.ss1` — all four battlers **L60**, but Wailord `Dive, Surf, **Water Spout**, Waterfall` and Swellow `Peck, Wing Attack, Aerial Ace, Quick Attack`. **NO Ice Beam. NO Fly.**
  * `post_ch24_atdoor.ss1` — L47-53, Wailord `Dive, Surf, **Ice Beam**, Waterfall`, Swellow `Facade, **Fly**, Aerial Ace, Quick Attack`.
  (Also: Sceptile has Slam vs Aerial Ace; Mightyena has Tackle vs Strength.) ⛔⛔ **MECHANISM CORRECTED 2026-09-17 — THE GRIND OVERWROTE NOTHING; THE LINEAGES DIVERGED EARLIER.** *(This said “the grind learned level-up moves OVER the curated set”.)* **MEASURED:** the ancestor `post_training.ss1` (L47-51, the save `post_grind_L60.ss1` was produced FROM) already carries the identical move NAMES — Wailord `Dive, Surf, Water Spout, Waterfall`, Swellow `Peck, Wing Attack, Aerial Ace, Quick Attack`, Sceptile `Rock Smash, Strength, Leaf Blade, Slam`, Mightyena `Tackle, Crunch, Take Down, Bite`. ⇒ **this lineage NEVER HAD Ice Beam or Fly to lose**; it diverged from the Ice-Beam lineage BEFORE that ancestor, and `Water Spout` is simply Wailord's natural **L44** level-up move. ⛔⛔ **RETRACTED 2026-09-17 — REFUTED BY MEASUREMENT ON THE §Ch24 LINEAGE.** *(This said the bot “DECLINES level-up moves” and that “a taught move will NOT be undone by grinding”.)* **IT IS NOT A RULE, AND THE OBJECTION I USED IT TO DISMISS WAS CORRECT.** Wailord **LOST ICE BEAM TO HYDRO PUMP AT EXACTLY L59** — the very level I cited as proof it would not:
      post_e4grind_L57.ss1  L57  Dive, Surf, Ice Beam,   Waterfall
      post_e4grind_L59.ss1  L59  Dive, Surf, Hydro Pump, Waterfall   <<< -Ice Beam +Hydro Pump
  ⭐ **THE REAL MECHANISM** (`#24-learnhmcoverage`, now fixed): `which_move_should_be_replaced` decides per case, and its type-coverage census was built from the **replaceable** slots, which **EXCLUDE HMs**. Wailord's three Water moves are all HMs (Dive/Surf/Waterfall), so the census read `[Ice]`, Hydro Pump looked like **a type we LACK**, and the policy “freed the weakest slot to gain coverage” — spending the team's only Ice move on a FOURTH Water move. ‼ **THE SAME CODE EXPLAINS THE OBSERVATION THAT MISLED ME:** on the `post_grind_L60` lineage that slot held **Water Spout** — a TM, so non-HM — the census read `[Water]`, Hydro Pump was REDUNDANT and weaker (150 vs 120), and it correctly DECLINED. Same code, same level, opposite outcome, decided purely by which slot happened to be replaceable. ⇒ I watched the policy work correctly on one party and wrote down a universal law. —— *the retracted text:* ⭐⭐ **AND THE OPPOSITE OF MY CLAIM IS TRUE, WHICH IS THE USEFUL PART: THE BOT DECLINES LEVEL-UP MOVES.** Wailord crossed **L52 (Amnesia)** and **L59 (Hydro Pump)** during that L47→L60 grind and kept all four of its moves. ⇒ **a taught move will NOT be undone by grinding** — which is the strongest objection to the repair plan, refuted by measurement rather than argument. ‼ Corroborated from the learnsets: **no battler learns ANYTHING between L61 and L75** (last level-up moves: Wailord/Sceptile L59, Mightyena L52, Swellow L49, Zigzagoon L41, Castform L30 — read from `modules/data/species.json`, with a control that printed Wailord's full learnset and found `Water Spout` at L44 as expected). ⛔ **DO NOT “FIX” THE GRIND TO STOP OVERWRITING MOVES — there is no such defect.**  ⛔ **WHY IT MATTERS:** Ice Beam is the designated **Drake** counter (Flygon has LEVITATE ⇒ Ice is the only super-effective type reachable on it) and cost TWO work items to teach; **Fly is how §Ch24 reaches the League**. ‼ **THIS BREAKS THE “GRIND FIRST” BUILD ORDER** ruled earlier today: grinding `post_grind_L60.ss1` to L75 produces a strong party that cannot fly to the League and has no answer to Flygon; and `post_ch24_atdoor.ss1` **cannot be ground** — `ch24grind`'s own docstring says *“The League fixtures cannot be used: from the League door `calculate_path` reaches neither grass nor a Poké Center.”* ⭐ **THE REAL NEXT QUESTION IS THEREFORE A FIXTURE QUESTION, NOT A GRIND QUESTION:** produce ONE save that is simultaneously high-level, Ice-Beam-carrying and Fly-carrying. Candidates: re-teach Ice Beam + Fly onto the L60 party (TM13 is single-use — check the bag), or grind `post_ch24ready.ss1` (pre-Fly, on the mainland) and only then fly in. ⚠ Neither is costed yet. ✅ **AND THE VERIFICATION GAP IS THE LESSON:** `FIXTURES.md5` said this save was *“Verified by RELOADING the file (`probe_anchor_inventory.py`)”* — a probe that **does not print movesets**, a caveat the docs already record for the other fixture. The manifest row now carries the warning.
- [ ] ⛔ `#24-ghostzerodamage` — **NEW 2026-09-16. LEG 2 (PHOEBE) HAS A ZERO-DAMAGE LOOP, AND THE MECHANISM IS VERIFIED AT SOURCE.** Phoebe's team is ALL GHOST, and **10 of our party's 24 damaging move slots deal literally ZERO to it** (every Normal and Fighting move). ⛔ **THE CHAIN, each link READ in our own code:** `_util.py:264-266` — `max_strength = max(move_strengths); if max_strength <= 0: return None` ⇒ when EVERY move of the active mon deals 0, the ranker returns **None**; then `battle_strategies/default.py:358-360` — `if move is None: move = 0` ⇒ it uses **move SLOT 0**. ‼ **AND SLOT 0 STILL HAS PP, SO THE GAME DOES *NOT* SUBSTITUTE STRUGGLE** — Struggle only appears when NOTHING is usable. ⇒ the bot repeats a 0-damage move until that slot's PP is exhausted. ⭐ **WHERE PRESSURE COMES IN:** both Phoebe's Dusclops carry **Pressure**, which doubles PP drain on the moves that DO work (Crunch/Bite, Aerial Ace, Surf, Ice Beam) — so the working moves empty first and the party is left holding only the 0-damage ones, which is exactly the `max_strength <= 0` precondition. ⚠ **CORRECTION TO THE RECON THAT FOUND THIS:** it described the outcome as *“a permanent zero”*. It is not permanent — `_fight_on`'s own docstring is right that Struggle eventually ends the battle. The real cost is a long self-damaging loss in a ONE-WAY gauntlet with finite items, which is effectively fatal but not a hang. ✅ **MITIGATING FACT, CHECKED PER MON:** every battler DOES have at least one move that hits Ghost — Mightyena Crunch/Bite (super-effective), Sceptile Leaf Blade/Aerial Ace, Swellow Fly/Aerial Ace, Wailord all four, Castform Powder Snow. So the loop needs PP exhaustion FIRST; it is not reachable on turn one. ⭐ **WHAT LEG 2 SHOULD DO:** lead **Mightyena** into Phoebe (the only super-effective answer), and treat `max_strength <= 0` as a ROTATE signal rather than letting it fall through to slot 0. ⛔ **NOT YET MEASURED** — no drive has fought Phoebe; this is a code reading plus a decomp roster, and the PP arithmetic is unsimulated.
- [ ] ⛔ `#24-itemcontextplural` — **NEW 2026-09-16. THE HEALING PATH WAITS ON ONE CONTEXT-MENU TASK WHERE THE FILE KNOWS FOUR — AND THE OBVIOUS FIX IS MEASURED AS A REGRESSION.** `pokemon_league.py` `use_item_on_party_member` calls `wait_for_task_to_start_and_finish(ITEM_CONTEXT_TASK, "A")` — the SINGULAR name — while the same file defines `ITEM_CONTEXT_TASKS` (all four) with the comment *“Naming only one of these cost four drives — the bot sat on the bag list and the failure blamed the party cursor.”* That fix landed on the TEACH path 2026-09-05 and **never on the HEALING path**, which is the gauntlet's only survival mechanism. ⛔⛔ **DO NOT TRANSPLANT THE TEACH LOOP — IT WAS TRIED AND IT BROKE EVERYTHING.** MEASURED A/B, `--driver ch24heal` on `post_league_shop.ss1`, same staged damage: BASELINE `ready=True failure=None ACCEPTANCE: PASS` (7 actions) → with the transplant `ready=False failure=…Task_HandleChooseMonInput never became active… ACCEPTANCE: FAIL` (**0 actions, nothing healed**) → after revert PASS again. Evidence `evidence/2026-09-16-ch24heal-{BASELINE,AFTER-fixes,AFTER-revert}.stdout.txt`. ‼ **WHY:** `wait_for_task_to_start_and_finish` presses A **through** the menu — start AND finish — which is what SELECTS “Use”; the teach loop is **start-only** and stops pressing once the menu opens, because on that path the NEXT block does the selecting. ⭐ **THE CORRECT FIX generalises START-AND-FINISH across all four names** (wait for ANY to become active while pressing A, then keep pressing until NONE is active), and must be graded by re-running that same A/B. ✅ The `_check_abort` import it will need is already at module level. ⚠ Severity is LATENT, not live: the singular name has never been observed to fail on medicine — `item_menu.c:1683` picks the task by ACTION COUNT, and medicine has four actions, so `MultipleRows` is correct for every item this function is currently handed.
- [ ] ⭐⭐ `#26-victoryroadgap` — **NEW 2026-09-16. MEASURED OVER THE SAME 99-RUN CORPUS, WITH CONTROLS THAT FIRE: *NOT ONE RUN HAS EVER ENTERED VICTORY ROAD.*** ⛔⛔ **AND IT REFUTES THE STATED REASON FOR PRIORITISING §Ch24.** `ai-research-notes/2026-09-16-endless-batch-REVIEW.md` §1 is headed *“30% OF RUNS REACH THE LEAGUE'S DOORSTEP”* and its §Next-steps says *“Build the §Ch24 sequencer. 30% of runs already reach the door”*. That 30% is the **EVER GRANDE CITY** milestone — the OUTDOOR map, which the bot reaches by surfing in from ROUTE 128, on the Poké Center side. The League door apron is on the far side of VICTORY ROAD, and **0 of 99 runs entered it**. ⭐ **HOW IT WAS FOUND, AND WHY IT HAD BEEN INVISIBLE:** the analyser's CUMULATIVE row was an **ASSUMED-ORDER ROLL-UP** — `cum += furthest[key]` walked backwards through `MILESTONES` and INFERRED that reaching Ever Grande implied having reached every earlier milestone, Victory Road included. `seen_maps` was already computed per run and thrown away, so the real number was one line away. Fixed in `analyze_endless_batch.py` (`#24-pass2triage` g): it now prints MEASURED beside assumed and flags disagreements, with a `--self-test` arm that builds a skipping run and PROVES the two can differ (a side-by-side that cannot disagree is decoration). On re-run, exactly one row disagrees: `victory_road  MEASURED 0 (0.0%)  assumed-roll-up 30 (30.3%)  ← DISAGREES by -30`. ✅ **CONTROLS FIRE, UNDER *TWO* PATTERNS, AND THE STRICT ONE REPRODUCES THE ANALYSER EXACTLY.** Per-run, over all 99: **STRICT** (a real `[MAP]`/`[hb]` map LOAD named it, i.e. the analyser's own regexes) — `VICTORY` **0**, `EVER GRANDE` **30**, `SOOTOPOLIS` **50**; **LOOSE** (any `-> X` / `map=X`, which also catches DESTINATION-INTENT lines) — `VICTORY` **0**, `EVER GRANDE` **51**, `SOOTOPOLIS` **54**. ‼ **I CHECKED THIS BECAUSE MY FIRST CONTROL DISAGREED WITH THE ANALYSER** (a loose grep said 51 where the tool said 30) — the gap is 21 runs that *aimed* at Ever Grande and never loaded it, i.e. exactly the candidate-vs-attempt distinction (rule 7). Strict matches the tool 30/30 and 50/50, so the instrument and the control agree. ⭐⭐ **AND VICTORY ROAD IS 0 UNDER *BOTH*** ⇒ stronger than “never arrived”: across 338.5M frames no run ever even NAMED a Victory Road map as a destination. The only “Victory Road” strings in the entire corpus are dex-hunt lines — *“Hariyama (Fighting) (type match) on Victory Road (B1F) (tile unmapped, NOT HUNTABLE)”* — i.e. a CANDIDATE, and CLAUDE.md rule 7 says a candidate is not an attempt. Sampled trail: `ROUTE 128 -> EVER GRANDE CITY`, then the run bounces between warps (0,8) and (16,12) and never climbs. ⛔⛔ **WHAT THIS DOES *NOT* SAY.** It does NOT say §Ch24 is the wrong thing to build — the user's standing directive is to get back to the story, and §Ch24 is the last chapter. It says the *argument* “one run in three is already at the door” is false, so §Ch24 must be justified as **finishing the story**, not as **converting traffic that exists**. ‼ It also does not yet say WHY: §Ch23 IS built and wired as Segment 23, so the candidates are (a) runs die/time out before Victory Road, (b) the §Ch23 entry is never triggered from the endless-reset path, or (c) `#26-destreachability` derails consume the budget first. ⭐ **NEXT STEP (cheap, offline, no drive):** for the 30 Ever-Grande runs, print the last 200 log lines and the final `[STORY]` guard each one was inside. That separates (a) from (b) without touching the emulator. ⛔ Do not re-run the batch to answer this — the corpus is already on disk and CLAUDE.md rule 9 says batches answer frequency questions, which this no longer is.
- [ ] ⭐ `#26-destreachability` — **NEW 2026-09-16, MEASURED over 99 runs / 338.5M frames. THE THREE ITEMS AROUND IT ARE ONE DEFECT: a destination is COMMITTED TO before its reachability is proven.** `ROUTE111` (84/99 runs — relocation picks it from ROUTE116; the path needs RUSTURF_TUNNEL, a **warp**, and `calculate_path` cannot use warps ⇒ the pathfinder is right to refuse, the CHOOSER was wrong to ask); `PETALBURG_WOODS` (78/99 runs, the only INTRA-map member, (14,5)->(26,5)); `heal_in_pokemon_center ... BLOCKED` **229x** over PetalburgCity 94 / LavaridgeTown 94 / FortreeCity 29 / FallarborTown 12. ‼ **PetalburgCity (94) was absent from this file entirely** until now — `#26-healmap-*` named only Lavaridge and the Route-111 split. ⛔⛔ **DO NOT PRIORITISE THIS OFF THOSE COUNTS YET — THEY ARE EVENT COUNTS, NOT COSTS.** A derail can RECOVER (proven for ROUTE111: 77 attempts, 1 failure — `07-CHANGELOG.md:27655`), and a 2026-09-16 claim that read frequency as cost was RETRACTED the same day. **PREREQUISITE: a per-derail RECOVERED/FATAL classifier.** ⚠ And a `calculate_path` OK is NOT proof the driven navigator can walk it (`KI-48`) — any reachability pre-check must use the instrument the bot actually uses. Evidence: `ai-research-notes/2026-09-16-endless-batch-REVIEW.md`.
- [ ] `#26-healmap-route111split` — SAME SHAPE, found in passing: `story_mode.py:1120` maps `ROUTE111 -> FallarborTown`, correct for Route 111's NORTH side; its SOUTH side answers **Mauville**. One map, two correct answers, split by the desert. Filed, not fixed.
- [x] ✅ `#24-ratchet-scope-gap` — **CLOSED 2026-09-13. Both ratchets now scan `plugins/custom_modes`, and both admissions are FAULT-PROVEN.** ⛔ My filed estimate (“93 broad handlers, ~90 unguarded”) was from a HAND-ROLLED count and was **off by 20× for the gate that matters**: measured with each gate's OWN rule, `probe_abort_swallowing` cost **+4** (23→27) and `repro_no_silent_except` **+79** (per-root pinned). ‼ *Measure an admission with the GATE'S OWN LOGIC, never an equivalent.* All 4 abort sites were TRIAGED and carry an `ABORT-SWALLOW TRIAGE` comment — **three would BREAK if guarded** (a derail-recovery settle loop that already cleared the latch; an ordered `except BotModeError: raise` that an abort can never get past; and the ENDLESS-RESET batch loop where catching IS the point). FAULT ARMS: an 80th silent handler → RED (`80 / 79 <- OVER`, *“even if the total did not”*); a 28th abort site → RED. Evidence: `07-CHANGELOG.md` 2026-09-13.
- [ ] ⬇ `#24-ratchet-paydown` — NEW, follow-on: the 79 admitted silent handlers (72 `story_mode.py`, 7 `living_dex_mode.py`) are now VISIBLE and RATCHETED. Pay down in small reviewable batches and LOWER the per-root budget each time (that is the ratchet turning). ⛔ Do NOT attempt a sweep — `repro_no_silent_except`'s own text says ~69% of handlers in this code are silent and a gate demanding zero would be red on arrival and switched off.
- [ ] ⬇ `#24-maintain-staletarget` — **DOWNGRADED 2026-09-12: REAL in structure, ZERO measured cost.** `_prepare_for_fight` runs the errand at `:2613` with the pre-escalation target; `:2763`/`:2780` then raise it and `:2803` recomputes the exclusion floor. **Measured over 1,298 runs and BOTH escalation paths** (boss-mode `:2763` = 3,132 events / 83% of lanes; heavy `:2786` = 67 / 12%): of the 23 approvals adjacent to an escalation, **0 spent frames** — 22 preempted by the ROTATION guard, 1 by a nav failure. ⛔ **DO NOT REORDER:** `_prepare_for_fight` has early-return paths (counter-ladder / second-wind) that bypass READY-THE-BATTLERS; maintenance runs BEFORE them today, so moving it would remove the errand entirely from the hardest bosses — a CERTAIN regression traded for a zero-occurrence defect. ‼ **WATCH CONDITION (why this stays open):** re-run `tools/story-dev/probe_staletarget_cost.py` after any change to `MAINTAIN_MAX_FRAMES`, the rotation guard, or `decide_maintenance`'s refusal ORDER — three unrelated gates screen this and none was designed to. Ruling: `06-DECISIONS-LOG.md` 2026-09-12. Evidence: `07-CHANGELOG.md` 2026-09-12 (night).

### 📦 SESSION END 2026-08-05 — **ARCHIVED 2026-09-04 to `28-HANDOFF-ARCHIVE.md` (387 lines, VERBATIM, nothing deleted).**

- [x] **Moved because this file sat at its 3,600-line cap for three commits and R3's own wording names the cause: "an archive is forming inside a current-state file". This block declared itself HISTORICAL in its own heading.** ‼ Its opening line records that the heading read "THE CURRENT TOP OF THE LIST" for a month over a stale suite figure — the exact failure mode that keeping spent content in a current-state file causes. Slugs it contains, preserved and findable in the archive: `#24-cavethread`, `#24-ch21climb-whiteoutarm`, `#24-driftassertions`, `#24-driftreduction`, `#24-gymwhiteoutgatehang`, `#24-handoffbudget`, `#24-hmteachloop`, `#24-ki59archiveheader`, `#24-livegridreader`, `#24-logcollision-siblings`, `#24-organicteam`, `#24-orphans`, `#24-partycap`, `#24-pcoverflow`, `#24-pcoverflow-proof`, `#24-probecountgate`, `#24-roster`, `#24-skypillarprobewrites`, `#24-stdoututf8gate`, `#24-zerokocounter`, `#26-gatestartupcontention`.

### ✅ `#24-abortrecoveryresiduals` — ALL THREE RESOLVED 2026-08-23 (RETIRED to a summary; full detail in `07-CHANGELOG.md`)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted).
- [x] ⛔ DO NOT REDO. Full detail in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.

### ✅ `#24-brokenrepros` — DONE 2026-08-23 (RETIRED to a summary; full detail in `07-CHANGELOG.md`)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ DO NOT REDO. Full detail is in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.

### ✅ `#24-p2headergate` — DONE 2026-08-23 (RETIRED to a summary; full detail in `07-CHANGELOG.md`)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ DO NOT REDO. Full detail is in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.

### ‼ `#24-pluginwhiteoutnoyield` — an UPSTREAM bug: the plugin whiteout hook has NEVER run (filed 2026-08-23)

- [ ] **VERIFIED, not reported second-hand.** `modules/modes/_listeners.py:567` calls
      `plugin_whiteout()` **bare** — no `yield from`. `plugin_whiteout` IS a generator function
      (`modules/plugins.py`, `-> Generator`, contains `yield from`), so the generator object is
      created and immediately discarded and **no plugin's `on_whiteout()` hook has ever executed**.
      ⛔ **UPSTREAM, NOT OURS:** identical at `40cakes repo/pokebot-gen3/modules/modes/_listeners.py:536`,
      so it must NOT be fixed in the mirror. Fixing it in our forks is a DIVERGENCE and needs a
      DIVERGENCE-LOG entry.
      ⚠ **Currently a NO-OP for us** — no plugin in our tree implements `on_whiteout`; StoryMode's
      handling goes through `bot_mode.on_whiteout()` at `:566`, which does run. So this is latent,
      not live. ‼ It becomes live the moment anyone writes a plugin whiteout hook and quietly gets
      nothing. Scoped: exactly 1 bare call out of 10 generator functions in `plugins.py` — an
      isolated slip, not a pattern.

### ‼ `#24-harnesswhiteoutdrop` — 36 harness runs dropped to Manual on a whiteout (filed 2026-08-23)

- [ ] **Found while assessing `#24-abortrecoveryresiduals` (a).** 36 genuine
      `[MODE] Story -> Manual (message='Player whited out...')` transitions, ALL in story-dev harness
      profiles (`repro-*`, `nc-*`, `nat-*`, `mt1/2`, `ki66single`, `hpstart`, `item-old`, `jp-post`)
      and **never in the batch runs**. Diagnosis: `on_whiteout()` reached something that was not a
      `StoryMode`, i.e. a harness pushing `run()` without setting `context.bot_mode_instance`, so the
      custom handling never engaged and the listener fell through to `set_manual_mode()`.
      ⇒ **This is a TEST-FIDELITY defect, not a bot defect:** any harness driver that whites out
      silently stops behaving like the real mode from that point on, so whatever it was measuring
      afterwards is suspect. ➡ **RECON 2026-08-26 (static sweep, spot-verified): the filed
      mechanism is REFUTED AS STATED** — all 67 driver branches (+ an else fallback,
      `story_harness.py:10551`) DO set `context.bot_mode_instance`, and the frame loop passes that
      instance to listeners (`:10620`). Two candidate mechanisms survive: (a) the mode those old
      profiles ran was a NON-Story mode whose inherited `BotMode.on_whiteout()` returns False
      (`_interface.py:191` — verified) → Manual by design; (b) assignment runs ONLY on
      stack-empty frames (`:10286`), so a stale instance can persist. ✅ **THE LOG MINING RAN the
      same day** — corrected analysis in `ai-research-notes/2026-08-26-whiteoutdrop-log-tally.md`:
      **26/36 ran named NON-story drivers (expected drops, not defects); the other 10 are
      UNRESOLVABLE from the logs because the run header never records `--driver`.** ⇒ NEXT: add
      `driver:` to the harness run header (2 lines + one proving boot); the mixin-adoption
      question for recon drivers is the USER's call.

### ‼‼ `#26-manualderails` — PRODUCTION derails to MANUAL around Fortree and Mossdeep (USER REPORT 2026-08-26)

**USER-OBSERVED, single live instance, Mudkip starter:** the bot *"works really well but has some
derails where it reverts to MANUAL"*, clustered **around Fortree and Mossdeep** — and ‼ **when the
user flips it back to Story mode it continues normally.** That recoverability is the diagnostic gold:
whatever gives up is a GUARD or RETRY-EXHAUSTION handing off via `set_manual_mode()`, not a wedge —
the underlying navigation still works on re-entry.
**Plan (the user's own suggestion):** an `--lanes 8` batch, then read the debug logs for the derail
signatures — WHICH `_guard()`/abort path fired, on which map, at what point. ⛔ Batches answer
FREQUENCY; once a signature is in hand, the fix is proven by a targeted driver, not more batches.

➡ **FORTREE HALF DIAGNOSED 2026-08-26 (31 finished bundles mined; MECHANISM read from code):**
* Dominant signature: the **Winona hopeless-gate** — `story_mode.py:1919` raises *"N losses with no
  super-effective answer … Grinding levels will not fix this"*. **530 lines corpus-wide, ALL 31
  bundles incl. the newest; 111 runs burned their budget on it.**
* ⛔ **ITS PREMISE IS MEASURABLY WRONG SOMETIMES:** `20260811-130454/L01` lost twice to Winona then —
  same team shape, NO super-effective answer, lead SWELLOW — **won the Feather Badge on retry.**
* **WHY THE USER'S FLIP WORKS, precisely:** losses live in `self._loss_ko_history` (PER MODE
  INSTANCE, `story_mode.py:1153`) and the counter ladder gets ONE attempt per boss per run — once it
  fails, **every later derail in the same instance deterministically re-raises with zero new
  information**, burning the 5-derail budget → `main.py:151` → `set_manual_mode()`. Flipping back
  builds a FRESH instance: losses reset, ladder re-armed, the bot re-fights — and often wins.
  **The budget was exhausted, not the situation.**
* ⛔ **THE HONEST-STOP RULING STANDS** (`06-DECISIONS-LOG.md` 2026-07-30 — do NOT delete the raise).
  ✅ **THE SECOND WIND IS SHIPPED 2026-08-26, BY THE BOOK:** the `--driver secondwind` arm was
  built FIRST and measured on unmodified code (`era=TODAY`: RAISE x5 + re-arm RAISE, matching the
  hand-computed discriminator exactly), THEN the fix landed (`era=AFTER`: SECOND_WIND +
  PLAIN_ESCALATION x4, ZERO raises, and ⛔ the re-arm control still RAISES — the 2026-07-30
  honest-stop ruling is COMPLIED WITH, not reopened). Once per boss per run; both natural resets
  (manual flip, per-run reset) re-arm it; the per-run-state gate enforces the reset.
  Evidence: `evidence/2026-08-26-secondwind-AB.txt`. ⚠ The arm proves the DECISION layer (it
  drives `_prepare_for_fight` directly, the ki80ladder pattern); the end-to-end pass through the
  real derail loop is measured by the next post-fix batch, discriminator: no five-fold
  hopeless-gate repeats before Manual. ‼ The arm's predicted casualty (ki80ladder)
  was confirmed then fixed — and that run exposed a PRE-EXISTING stale-era rot in ki80ladder
  (proven at pristine HEAD), fixed the same hour.
* Secondary: KI-36 battle wedges at the gym (last seen 20260810); cutscene-wedge family (absent from
  the newest 7 bundles — already fixed).
➡ **MOSSDEEP HALF — FIRST DATA EVER, mined MID-BATCH 2026-08-26 (⚠ interim; final counts when the
  batch lands):**
  * ✅ **THE GYM ITSELF IS CLEAN: 5 of 5 lanes that reached it passed badge 7, ZERO derails inside.**
    The user's "around Mossdeep" is the era, not the gym.
  * ⛔ **NEW SIGNATURE 1 — the unfleeable-battle freeze (3 lanes):** became `#26-fleefreeze`,
    ✅ FIXED + LIVE-VALIDATED (zero freezes in both post-fix batches) — see its entry.
  * ⛔ **NEW SIGNATURE 2 — the degraded-party spiral (L08):** party fell to ONE viable mon; the
    Tate & Liza DOUBLE-battle preflight correctly REFUSED ("need 2 Pokemon able to fight; the party
    has 1") — and then recovery could not path out (`(23,8) -> (6,35) @ MOSSDEEP_CITY_GYM` refused;
    a MAUVILLE heal target refused too), burning 5 derails. The refusal was right; the RECOVERY
    (heal-then-return, or exit the gym at all) is what is missing.
  * *(interim Winona/type-loss tallies superseded by the final numbers below.)*
➡ **BATCH COMPLETE 2026-08-26 — FINAL NUMBERS (baseline: `ad37949b` pre-fix production code):**
  * **50 boundary-marked runs: 6 finished / 44 derailed** (measured from the run-boundary lines
    myself — ‼ the mining agent reported "0 finishes" and was WRONG; the harness's lane table and
    my own grep agree on 6. Verify-the-agent, again). Treecko lanes: **0 finished of 9** — the
    user's starter concern is now a measured fact.
  * ⛔ **§Ch20 RAN IN A BATCH FOR THE FIRST TIME — and the TEACH BUG killed it.** L01 debug-log
    081321: reached the Seafloor Cavern, SOLVED ROOM 8, exited to ROUTE128 — then died to
    *"Teach flow finished but Linoone does not know Surf"*. On PRE-fix code: this is the exact path
    `#26-surfteachchain`'s D1/D2 gates fix, now measured as a run-killer (~9% of endings, 5 runs).
  * **The freeze signature is settled:** both frozen contexts are **MAGMA_HIDEOUT (24,86)/(24,91)
    during the "to Fortree" stage** (the interim "To Lilycove" label was wrong), one frozen INSIDE
    `EventScript_DoNoIntroTrainerBattle` — a NO-INTRO TRAINER battle, which can never be fled.
  * **Treecko's Surf-chain corner measured:** L03 085044: *"Cannot hunt a Surf learner: no Poké
    Balls and no money to buy any"* — the resource-depleted end of the hunt, filed with D3-D6.
  * Winona: **15 run-ending derails this batch** (treecko/torchic lanes), no loss-then-win observed
    IN THIS BATCH (the premise-refutation win is from 20260811/L01). Agent-mined ranking (⚠ its
    finish count was wrong, so treat ranks as indicative): boss type-loss 21, watchdog 9, nav 6,
    Surf-teach 5, handler wedge 4.
➡➡ **POST-FIX VALIDATION BATCH MINED 2026-08-26 (`20260826-130441`, code `dce95b4a`, 300 min,
  VERDICT OK, headers 39/39 clean). The four PRE-REGISTERED discriminators, graded:**
  * **(1) FINISH RATE: PASS — 8/31 completed (25.8%) vs baseline 6/50 (12.0%).** Same wall-clock,
    fewer + LONGER runs (runs die deeper). Mudkip lanes 5/10 finished (L02 **4/4**); ⛔ Treecko
    **0/6** — the design-gap half is untouched, as expected (D3-D6 + `#24-roster`).
  * **(2) SURF-TEACH: PASS, instrument-honest.** At DOUBLE the exposure (10 involved runs vs 5),
    **7/10 finished through the failure** (baseline 4/5 by the SAME stdout instrument);
    surf-as-last-derail 2 vs 1. ⚠ The old "~9% of endings" figure came from the mining agent whose
    totals this entry already flags as wrong — by symmetric instruments the teach failure is now
    overwhelmingly non-fatal at higher exposure. D1b (failure-phase exit fault arm) is STILL unproven.
  * **(3) FLEE-FREEZE LIVE ARM: PASS, decisive** — `[KI-52] … escape impossible (a partial-trapping
    move …) -> FIGHTING ON` fired repeatedly on the exact Torkoal signature; **ZERO
    `BattleScript_PrintCantEscapeFromBattle` freezes corpus-wide** (baseline: 3 lanes frozen); zero
    KI-47 nets on that signature. The 3 KI-47 nets present are ALL the `#26-battleitemwedge` /
    action-selection family — which is NOT in this batch's code and rides the NEXT one, as filed.
  * **(4) HOPELESS REPEATS: ⛔ FAIL AS PRE-REGISTERED — WORKING AS DESIGNED.** 27 live SECOND-WIND
    firings end-to-end (the proof the arm could not give); 17 resolved with NO repeat cluster. But
    10 runs still burned **five same-count raises + boundary echo AFTER their one wind was spent**
    (counts frozen: 12/12/12…, 25×5, etc. — deterministic, zero new information). That residue IS
    the ruled once-per-boss design. ➡ **OPEN QUESTION FOR THE USER (do not build unilaterally):
    once the wind is spent and a raise repeats with an UNCHANGED loss count, should the run go
    straight to Manual instead of burning ~4 more derail cycles?** (Saves dead time on genuinely
    hopeless runs; the honest stop itself stays.)
➡➡ **SECOND POST-FIX BATCH MINED 2026-08-27 (`20260826-185918`, code `86eaf8f3`; the manifest's
  `-dirty` was DOCS-ONLY, verified; 300 min, VERDICT OK):**
  * **Finish rate 12/32 = 37.5%** (12.0% → 25.8% → 37.5% in one day); Mudkip lanes 8/10.
    **11 of 12 Surf-teach-involved runs FINISHED.** D4 shape unchanged (20 winds, 7 burns).
  * ‼ **FIRST TREECKO FINISH EVER** (L07 run 2 — the real Ch20-done line; ⚠ frame count zeroed
    by a mid-run emulator reset).
  * ‼ **THE TREECKO WALL, NAMED by a clean run-ender:** *"No party mon can learn Surf and the
    party is full — needs PC box management (`#24-pc`) or a manual swap"* (L07 run 3, stage 14)
    — the `#24-roster` WITHDRAW half measured as a run-ender in production's own words.
  * **`#26-battleitemwedge` live arm: VALIDATED** — its KI-47 family **2 → 0** over 572 item
    flows, 577 `bag-not-open-yet` re-presses recovering eaten As. The 2 remaining nets are the
    `handle_fainted_pokemon`/FaintedMonTry family (KI-66 residual area) — the NEXT wedge target.
    CantEscape freezes still ZERO.

### ‼ `#26-surfteachchain` — D1/D2 GATES SHIPPED 2026-08-26 (ordinary case A/B-clean); D3-D6 residuals remain

**SHIPPED:** the ride loop's blind `_f % 3 → A` and the post-select loop's blind A are GATED (A only
in a menu / text / waiting-for-input; else B) + a FAILURE-PHASE EXIT (30 stable overworld frames
without the move learned → break; the honest raise fires ~8,000 frames sooner and never touches the
NPC). The museum-greeter shape verbatim, armed only in the Surf seam (indoors next to Wally's dad,
Norman battle tail resident) — which is why Rock Smash with IDENTICAL code stayed clean (outdoors,
quiet map). Ordinary-case arm: `--driver teachfull` replace-path → `learned=True, ride_exit=learned,
ride_frames=479`. ⚠ HONEST LIMIT: the failure-phase exit is NOT yet exercised (needs a teach-failure
fault hook). **Also shipped:** the hunt fallback flip `grounds[-1]` → `grounds[0]` (measured
incident: the SURF hunt sent to Surf-gated ROUTE119).
✅ **LIVE VALIDATION 2026-08-26 (batch `20260826-130441`):** at double the exposure, 7 of 10
teach-failure runs FINISHED anyway — the gates convert the run-killer into a recovered stumble.
Full discriminator-2 grading (and the ~9%-figure correction): `#26-manualderails`' batch section.
⛔ Treecko lanes 0/6 — the design-gap half is measurably still the cost.
**HALF 2 ANSWERED BY AUDIT:** the guarantee EXISTS — Segment 12c wires
`ensure_hm_learner_making_room(HM03)` post-Norman; a slot is freed BEFORE the catch (never lands in
the PC); sole-carrier protection holds; catch cap 4 keeps runway. Per-starter: Mudkip line
self-learns; Treecko/Torchic hunt Zigzagoon/Lotad on R102, Petalburg's doorstep.
**RESIDUALS:** D1b fault arm (above); D3 `_select_forget_slot` blind relative scroll assumes cursor
slot 0 on RE-entry — ‼ DECOMP RECON DONE 2026-08-26 (`ai-research-notes/2026-08-26-d3-forgetmenu-
cursor-decomp.md`, NOTE not truth): cursor RESETS on re-entry (screen freed + AllocZeroed), but
re-entry inserts an EXTRA "replace move?" YES/NO before the selector — the D3 hazard is FLOW
desync, not cursor drift; needs a live probe before code changes; D4 the A-cadence can race
`Task_HandleChooseMonInput`; D5 per-frame press cadences; D6 cheap hardening — step OUTSIDE Wally's
house before teaching (mirrors Rock Smash's clean seam); the KI-63 making-room deposit path has ZERO
recorded live firings; Wingull HM03 decomp cross-check. *(original filing:)*

📦 *(original A-spam observation: fixed by the D1/D2 gates above; full quotes in
`07-CHANGELOG.md` 2026-08-26 + git history of this entry.)*
⛔ **HALF 2, THE DESIGN GAP:** the user's test bot was MUDKIP, which learns Surf itself. **A
Treecko/Torchic run may hold NO Surf-capable pokémon at this point.** Required: an organic
surf-learner path — capture a suitable pokémon, and if the party is full, ensure it ends up IN the
party (PC trip), before the story needs Surf. ‼ The Dive equivalent already exists and is DONE
(`ensure_hm_learner_making_room`; its driver is likewise complete — cited here as the PROVEN PATTERN
to copy, ⛔ not as work to run) — establish whether Surf has an equivalent, and if not, build one
shaped like the Dive one. Anchors: `norman_done.ss1`, `prenorman_fodder_grind.ss1`.

### ✅ `#26-mossdeeppuzzlespeed` — CLOSED. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-11, R3 budget; zero open boxes).
- [x] ⛔ DO NOT REDO. Detail in the archive and `07-CHANGELOG.md`.

### ✅ `#26-fleefreeze` — CLOSED. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-11, R3 budget; nothing deleted, zero open boxes).
- [x] ⛔ DO NOT REDO. Full detail in the archive under its 2026-09-11 banner and in `07-CHANGELOG.md`.

### ✅ `#26-battleitemwedge` — CLOSED. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-11, R3 budget; zero open boxes).
- [x] ⛔ DO NOT REDO. Detail in the archive and `07-CHANGELOG.md`.

### ✅ `#26-gatestartupcontention` — **CLOSED 2026-09-11: never contention, never a hang — the gate was PACED to 60fps.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (R3 budget).
- [x] ⛔ DO NOT REOPEN. Root cause + the A/B (900s kill → 107s) in `07-CHANGELOG.md` 2026-09-11; gate #54 `probe_gate_unthrottled.py` enforces it.

### ✅ `#24-driftheadlineshape` — **DONE 2026-08-26: `check_drift` PASS 3 reads the drift-row HEADLINE, fault-tested both ways plus a live incident replay.** ⛔ DO NOT REBUILD. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-10, R3 budget). Narrative: `07-CHANGELOG.md` 2026-08-26.

### ✅ `#24-ch22juan` — §Ch22, GYM 8 (JUAN): **DONE AND CLOSED 2026-09-03.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (R3 line budget; nothing deleted). ⛔ Nothing here is outstanding — the badge is won, the chapter is assembled and wired as Segment 22, and `#24-ch22chapter` carries the live detail. ⚠ **Drift: run `promote.py --check` (the authority; never restated here)** — `modules/story/victory_road.py` (⚠ **NO LONGER COMMENT-ONLY as of 2026-09-08** — it now also carries the `team_is_ready` EMPTY-BATTLER GUARD, a real behaviour change: an empty battler set used to return `(True, [])` and certify a broken run READY. Gate #48 `probe_empty_battler_guard.py` locks it, fault-tested) and `modules/story/counter_hunt.py` (the `KI-84` workaround, ⚠ **UNDRIVEN** — its A/B is `--driver ki84counter`). SANDBOX-ONLY; ⛔ do NOT promote `counter_hunt.py` before that A/B. *(was 1 as of 2026-09-08 — `modules/story/victory_road.py`, and it is COMMENT-ONLY** (9 insertions, 0 deletions: the note recording that the stepping fix was DRIVEN AND REFUTED, so it is not rebuilt). ⛔ Not a behaviour difference; promoting it is optional and cosmetic. *(was 0 as of 2026-09-08 — ALL FIVE PROMOTED (`KI-96`, `#24-truckleak`, `#24-pcpingpong`, `#24-hm07teach`, `#24-hm07funnel` + the whiteout budget), **PROMOTED 2026-09-08, user-authorised, verified by driving `--build custom` (`ACCEPTANCE: PASS`, `done=True`, `battles=12`, `whiteouts=0`); rollback tag `pre-promote-2026-09-08`**. *(was: drift 5, sandbox-only — ⛔ **the batch that blocked promotion FINISHED 2026-09-08 (`x4-runs/20260907-203713`), so nothing is waiting on it; PROMOTING IS THE USER'S CALL**. *(was: `battle_action_selection.py` for `KI-96`, `mossdeep_gym.py` for `#24-mossdeepstrand`, `counter_plan.py` for `#24-countermsg`, plus `story_mode.py`, the `KI-95` fix, sandbox-only and awaiting the user's promotion call); it was 0 — PROMOTED 2026-09-06.** *(pre-promotion count now lives in `DIVERGENCE-LOG.md`; the file detail is kept:)* (`modules/story/pokemon_league.py` joined 2026-09-04 — the §Ch24 out-of-battle party heal; `modules/story/overworld_items.py` joined 2026-09-04 — the NEW pure out-of-battle healing policy for `#24-e4healing`, gate #36; `modules/modes/util/walking.py` joined on 2026-09-04 — the `#24-waterfalltimeout` fix; 2026-09-03: `chapters.py` for a §Ch23 correctness fix, plus the new sandbox-only chapter modules `sootopolis_gym.py` and `victory_road.py`) — ✅✅ **PROMOTED 2026-09-06 with USER APPROVAL, which took drift to 0** *(it went to 2 on 2026-09-06 — `story_mode.py` for `KI-95` and `battle_action_selection.py` for `KI-93` — and back to **0 on 2026-09-07** when both were PROMOTED and driven-verified)*, driven-verified against `--build custom`; see `custom-pokebot/DIVERGENCE-LOG.md`. *(this read "PROMOTION IS THE USER'S CALL and is not implied", true until that date.)* ‼ The one rule worth carrying out of it: *a pre-step check that REFUSES is worth more than a post-hoc assertion that explains* — the guards caught five faults here, including a `+1`-per-step counter that is really `+2` on a threshold crossing, and a fall direction reversed because y increases SOUTHWARD.

### ✅ `#24-ch23wally` — **CLOSED 2026-09-04: WALLY IS BEATEN.** ✅ Option (b) (the faint-replacement ranking) is **DONE 2026-09-06** — `KI-95`, gate #39, sandbox-only and unpromoted. It had been OBSERVED firing inside the winning run — see the open bullet. (filed, ruled, trained and closed 2026-09-04)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ DO NOT REDO. Full detail is in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.

### ✅ `#24-waterfalltimeout` — **FIXED 2026-09-04 (sandbox).** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted).
- [x] ⛔ DO NOT REDO. `[0][1]` → `[1][1]`, direction MEASURED before the edit; detail in the archive and `07-CHANGELOG.md` for 2026-09-04.

### ✅ `#24-ch23healdescent` — **CLOSED 2026-09-04: leg 6 now heals before descending, and an A/B proves it (un-healed 32% / 3 fainted vs healed 87% / 0).** (filed and closed 2026-09-04)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ DO NOT REDO. Full detail is in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.

### ✅ `#24-ch23attrition` — **CLOSED 2026-09-04.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 line budget; nothing deleted, nothing edited).
- [x] ⛔ **DO NOT RE-RUN THE §Ch23 ATTRITION WORK.** The party is back to 807/807 with zero fainted; the fix and its A/B are in the archive under the 2026-09-07 banner and in `07-CHANGELOG.md` for 2026-09-04.

### 🔜 `#24-ch23leg3arms` — **§Ch23 leg 3's OWED FAULT ARMS + the B1F/B2F §F live checks.** (opened 2026-09-05)

⛔ **OPENED BECAUSE A HEADER TRIED TO CLOSE OVER THEM.** These two residuals were stated plainly
inside `#24-ch23victoryroad`'s body and had no slug of their own, so when that header was promoted to
✅ they briefly became invisible — the `#24-orphans` / `#24-codeorphans` shape, which this file has
already paid for twice. A Tier 1 reviewer caught it; the fix is a slug, not a caveat.

**OWED (quoted from `#24-ch23victoryroad`'s own body, unchanged):**
* *"LEG 3's OWED ARMS (still open): `STALERESPAWN`, a real `BADSTEP` (the current one is **hollow** —
  its branch never runs), and a `_play()` run to demonstrate the layout pin (a **NO-OP** in a fresh
  process)."* ✅ `NOHEAL` is already fault-proven by A/B — do not redo that one.
* *"Adjudicated OFFLINE only — the three live checks in the B1F/B2F note §F are still owed."*

‼ **A HOLLOW FAULT ARM IS WORSE THAN A MISSING ONE** — it reports PASS while proving nothing, which
is this project's most expensive documented failure shape. `BADSTEP`'s branch never runs, so its
green result is not evidence. ⇒ when this is worked, FAULT-TEST THE ARM ITSELF: prove it FAILS when
the thing it guards is broken, before trusting any run that includes it.

⚠ Priority: BELOW `#24-ch23chain`. The chain hang blocks the chapter; these harden a leg that already
drives green. ⛔ But do not silently drop them — that is why this slug exists.

---

### ✅ `#24-ch23chain` — **CLOSED 2026-09-05: §Ch23 COMPLETES END TO END.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 line budget; nothing deleted, nothing edited).
- [x] ⛔ **DO NOT REBUILD ANY PART OF §Ch23.** `ACCEPTANCE: PASS`, `done=True`. The full item — every leg, fixture, A/B and gotcha — is in the archive under its 2026-09-07 banner, and the shipping detail is in `07-CHANGELOG.md` for 2026-09-04/05.

### ✅ `#24-icebeamtrip` — **CLOSED 2026-09-05: TM13 ICE BEAM IS IN THE BAG.** ⛔ DO NOT REDO THE TRIP. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-10, R3 budget).
### ✅ `#24-icebeamteach` — **CLOSED 2026-09-05: WAILORD KNOWS ICE BEAM.** ⛔ DO NOT REOPEN. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-05, to keep 03 under its R3 line budget).
### ✅ `#24-flyunlock` — **CLOSED 2026-09-05: FLY IS TAUGHT AND FLOWN; the Ever Grande plateau is solved.** ⛔ DO NOT REDO. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-10, R3 budget).
### ✅ `#24-e4moveset` — **CLOSED 2026-09-05: the four FREE move changes are applied and driven.** ⛔ DO NOT REDO THEM. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-10, R3 budget).
‼ **ITS LIVE RESIDUAL IS HERE, NOT IN THE ARCHIVE — the block was the only place tracking it:** the free
pickup **Dragon Claw (TM02) for Sceptile** is STILL UN-FETCHED (availability confirmed by
`probe_ch24_readiness.py`), and **Wallace is still a loss**. ⛔ A CLOSED ITEM CAN BE THE SOLE OWNER OF
AN OPEN FACT — sweep for residuals before retiring one.

---

### 🔜 `#24-e4healing` — **§Ch24 HEALING. MIXED — read each step's own marker.** ✅ step 1 DONE 2026-09-04 (revive/cure/top-up OUT of battle). ✅ **step 3 DONE + DRIVEN 2026-09-13** — in-battle status cures are wired (`story_mode.py::_maybe_use_item` → `choose_status_or_revive_item`), gated (#59 = 72 checks, #60 = 11), and PROVEN LIVE on a staged-FROZEN lead: decision #1 chose **Full Heal** (`parameter==0`) and Sidney fell (`elite4_state=1`), while the `POKEBOT_E4_FAULT_NOCURE` control fired **no cure** and lost. Evidence: `tools/story-dev/evidence/2026-09-13-ch24probe-STEP3-{LIVE,NOCURE,BASELINE-UNSTAGED}.stdout.txt`. ✅ **step 4 ANSWERED 2026-09-14 — MEASURED: *do not raise the threshold*; the prerequisite is reliable item EXECUTION, not a better number.** ⛔ **✅ **RULED 2026-09-16 BY THE USER — the POST-WHITEOUT MONEY POLICY is SPEND DOWN BEFORE ENTERING**, and ⛔ **DO NOT RE-RAISE IT.** Convert spare cash into items at the door; items survive a whiteout, money is halved (`DoWhiteOut` → `SetMoney(money/2)`), so idle cash is the only thing a whiteout can take. ⛔ **THREE OPTIONS WERE OFFERED AND DECLINED** — adaptive re-stock, an attempt cap, and fly-out-and-re-earn. ⚠ **ACCEPTED CONSEQUENCE:** with no cap a whiteout loop has NO FLOOR (`EventScript_WhiteOut` → `ResetEliteFour` clears all four flags and zeroes the state — `data/event_scripts.s:585-586,628-634`), so a run seen looping in the League is BY DESIGN and needs a NEW user ruling, not a unilateral cap. Build notes + rejected alternatives: `06-DECISIONS-LOG.md` 2026-09-16. *(This item was DEFERRED on 2026-09-15 and open since 2026-09-10.)* ⭐ **ITS SHAPE CHANGED 2026-09-15 AND IT IS NARROWER THAN FILED** — verified at the decomp: **League 1F has a REAL Pokémon Center nurse at (3,2)** (`Common_EventScript_PkmnCenterNurse`) **and a mart at (16,2)** selling Full Restore / Full Heal / Revive, and every transition into that map does `setrespawn HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE`, so a mid-gauntlet whiteout lands back in that lobby. ⇒ the HEAL is free; only CONSUMABLES must be re-bought, so the question is *what basket to re-buy on halved money*, not *how to get healed*. The standing “no nurse here” ruling remains correct — it is about the GAUNTLET, and the rooms and halls have zero objects. ⚠ Whether the bot can walk BACK to the lobby mid-gauntlet is UNMEASURED and load-bearing. See `ai-research-notes/2026-09-15-ch24-ROUTING-AND-GRADING-CORRECTION.md` §D'. —— REMAINING: step 2 ONLY** (call it BETWEEN rooms — blocked on the §Ch24 chapter, which does not exist). ⛔ The REVIVE half stays OFF pending `KI-100`. (opened 2026-09-04)

⛔⛔⛔ **AND IT IS WORSE THAN A RE-BUY — VERIFIED IN CODE 2026-09-06.** The §Ch23 dispatch is:
`story_mode.py:3791` `if not ch23_chapter_done():` → `:3792` runs the chapter, `:3793` else-skips —
and `:3795` `_guard("Victory Road (Ch23)", ch23_chapter_done)` sits **OUTSIDE the if/else**.
`_guard` (defined in `story_mode.py`; ⛔ no line cited ON PURPOSE — this names a DEFINITION, and a line number here has drifted four times in one session) **RAISES `BotModeError`** when its check fails. ⇒ the moment
§Ch24 spends the basket, the next pass through `_play()` does all three of these:
(1) re-enters the WHOLE Victory Road chapter, because `:3791` is now True;
(2) reaches leg 11 and tries to re-buy a **₽54,300** basket holding **₽1,741** — leg 11 refuses
loudly, exactly as designed; and
(3) `_guard` raises anyway, because the predicate is still False.
⇒ ⭐ **BOTH HALVES MUST BE RELAXED IN THE SAME COMMIT — a fix aimed only at the `if` leaves the
unconditional `_guard` and turns a wasteful re-buy into a HARD FAILURE.**
⛔⛔ **CORRECTED 2026-09-10 BY AN ADVERSARIAL ROUND — THE SENTENCE ABOVE IS RIGHT BUT ITS DETAIL AND
ITS PROPOSED FIX ARE BOTH WRONG. Read `06-DECISIONS-LOG.md` 2026-09-10 before touching this.**
1. **`SYS_GAME_CLEAR` IS DEAD AS THE GATE.** Decomp-verified: set once (`post_battle_event_funcs.c:30`)
   and never cleared — but only reachable via `special GameClear` AFTER Wallace and the Hall of Fame,
   so it is False for the whole gauntlet. ‼ And it is **already the READOUT milestone**
   (`chapters.py:288`), so gating on it collapses the readout≠gate rule this tree already has.
2. **`FLAG_ENTERED_ELITE_FOUR` — the "obvious" replacement — IS ALSO DEAD**, and it is the more
   valuable kill: decomp-clean (never cleared anywhere), but set when the door guards step aside,
   i.e. **BEFORE the first fight**, and still SET after a mid-gauntlet whiteout ⇒ **REACHED BY
   FAILING.** It re-creates the 2026-09-05 defect inside the no-nurse gauntlet.
3. ✅ **FIXED AND GATED 2026-09-10 (gate #52, 8 cases, TWO fault arms) — ⛔ DO NOT REBUILD.** Leg 4
   fired on re-entry and attempted an ocean crossing *from inside the League*; the raise came from the
   chapter's **own 3-attempt loop** (`victory_road.py:3400-3403`), never reaching `_guard`.
   ⛔⛔ **THE MECHANISM I FIRST RECORDED HERE WAS WRONG — copied from the agent report unchecked.** It
   said *"False at the League door"*; `EG_LANDING=(18,55)`, the apron is `(18,6)`, **`6<=55` was
   already True**. The hole was one map further in (each League room is its own map ⇒ `_on_map(EG)`
   False, and the League is not in `VICTORY_ROAD_MAPS`). Fixed in the PREDICATE (its two call sites
   mirror); `=nofix` proves it: **C1+C2 red, C3-C7 green.**
   ‼ `ch23_chapter_done` has **FIVE call sites, not two** — a two-site fix is incomplete.
4. ⭐⭐ **THE QUESTION WAS WRONG.** A whiteout leaves the run genuinely NEEDING legs 10-11 again (party
   healed, money HALVED, E4 flags cleared, respawn outside the League) ⇒ **re-entry is CORRECT**; what
   is broken is that it cannot SUCCEED. ⇒ next §Ch24 work is (a) leg 4's precondition at the League
   door and (b) the money policy for a post-whiteout re-stock — **not a marker**, which hides both.

⛔⛔ **READ THIS BEFORE BUILDING ANY §Ch24 STEP — A HARD DEPENDENCY §Ch23 NOW PLACES ON YOU.** `ch23_chapter_done()` requires the **Elite Four basket in the bag** (it was position-only until 2026-09-05, and a WHITEOUT respawn at Ever Grande satisfied it — the predicate called a WIPED party "chapter complete"; see `06-DECISIONS-LOG.md` 2026-09-05). ⇒ **THE MOMENT §Ch24 SPENDS THE BASKET, `ch23_chapter_done()` FLIPS FALSE and the dispatch will RE-ENTER §Ch23** and re-buy it. ‼ **§Ch24 MUST THEREFORE SET ITS OWN PROGRESS MARKER** (a flag/var its own predicate reads) so Segment 23 is not re-entered mid-gauntlet. ⭐ This line exists here, and not only in the decisions log, because this project has repeatedly lost facts that lived in exactly one place a builder does not open.

**STATUS: OPEN — steps 1, 3 AND 4 DONE; ONLY step 2 remains, and it is BLOCKED on the §Ch24 chapter.** *(This read "steps 1 AND 3 DONE; steps 2 and 4 remain" until 2026-09-14 — stale for the second day running, because the CHECKLIST below was updated and this header was not.)* ✅ **STEP 3 IS WIRED *AND DRIVEN LIVE* (2026-09-13)** — `--driver ch24probe` + `POKEBOT_CH24_STAGE_FREEZE=1` cured a staged-FROZEN lead on decision #1 with a **Full Heal** (`parameter==0`) and beat Sidney (`elite4_state=1`); the `POKEBOT_E4_FAULT_NOCURE` control fired **no cure** and lost. ⛔ The REVIVE half is still OFF (`allow_revive=False`, `KI-100`). *(This line read "step 3's POLICY BUILT + GATED but DELIBERATELY NOT WIRED" until 2026-09-13 — it was already stale when written, since its own next sentence said "AND NOW WIRED".)* ✅ **STEP 3:** `choose_status_or_revive_item()` in `battle_items.py` — a SIBLING of `choose_healing_item` (a status cure restores no HP; folding it in would make `effective_heal` lie). Narrow by design: **cure only Sleep/Freeze** (they cost the turn anyway ⇒ the trade is free; Gen-3 freeze NEVER self-thaws), **revive only when `non_fainted_count <= 1`** (a Revive costs a turn and returns the mon at half HP on the BENCH), cheapest-first, and the per-battle cap is SHARED so a revive loop terminates. Selection is BY NAME, never by `parameter` — a Repel's parameter is 100 *steps*. **Gate #59** (`repro_battle_items.py`, 72 checks; **plus gate #60 `repro_item_noop_detector.py`, 11 checks, which drives the REAL `_maybe_use_item` state machine** — a Tier 1 reviewer found that a SUCCESSFUL cure read as a failed item to the HP-delta no-op detector, so TWO cures in one battle would have set `_items_ineffective` and **disabled HP-emergency healing for the rest of an Elite Four fight**. Fixed (the detector is kind-aware; the HP path untouched) and fault-proven: reverting it reds 5 of 11 including *“the HP path still works after two cures”*. ‼ #59 could not see it — it is pure-function and static-source; this is a turn-over-turn state machine) — ‼ **that file existed and was NOT in `run_gates.py`; the HP policy had been ungated all along.** Fault-proven: widening the status set reds exactly 3, exit 1. ✅ **AND NOW WIRED (2026-09-13):** `_maybe_use_item` asks the status policy after the HP policy declines, with `allow_revive=False`. ⛔⛔ **VERIFYING THE WIRING CAUGHT A PERMANENTLY DEAD PATH:** the first draft read `getattr(mon, "status_condition", None)` — **`BattlePokemon` has no `status_condition`** (that is `Pokemon`; the battle object has **`status_permanent`**), so behind a safe getattr the cure would have returned None EVERY TURN FOREVER with all 66 policy checks green. The same draft used `get_party` out of scope, which `decide_turn`'s `try/except` would also have swallowed into a silent None. ⇒ **six static checks now gate the CALL SITE** (calls the policy · passes `status_permanent` · never `status_condition` · revives off · HP asked first · gets the UNFILTERED medicine list); fault-tested — reintroducing `status_condition` reds exactly 2 of 72, exit 1. ⚠ **WORTH, MEASURED BEFORE BUILDING:** 1,308 of 97,567 our-side turns (**1.34%**) are lost to Sleep/Freeze, ~31 per run, and the cure only fires when a cure item is HELD ⇒ expect an Elite-Four-shaped benefit, not a whole-game one. ⛔⛔ **AND THE TWO ANSWERS ARE NOT ALIKE — see `KI-100`:** a cure aims at the ACTIVE battler (proven 19/19 at slot 0); a REVIVE aims at a FAINTED NON-ACTIVE member, the index space behind **KI-18/KI-34/KI-66**. The policy already takes **`allow_revive=False`** for exactly this — wire the CURE first; flip revives on only after an observe-only index probe (rule 10).
      ⭐⭐ **STEP 2 PLACEMENT IS ROM-VERIFIED (2026-09-13):** `HALL1/2/3/5` warps = `[(5,12),(5,2),(4,12),(6,12)]`, `HALL4` = only `[(5,33),(5,2)]`. The bot ARRIVES at (5,12) and **both neighbours are ALSO warps BACK** ⇒ one sidestep while healing silently undoes a cleared room. ⛔ **Heal INSIDE the arenas for bosses 1-4** (all `TRAINER_TYPE_NONE`, sight 0 ⇒ unlimited window) **and use HALL4 for the Wallace heal** — Champion's Room has NO window (Wallace's object script is `0x0`; an `OnFrame` script starts it, hence leg 10's *do NOT press A*). ⭐ **JUSTIFYING MEASUREMENT, ALREADY IN OUR DOCS** (`04-HANDOFF.md:19-26` / `KI-93`): `--driver ch24probe` **BEAT SIDNEY** and ended with **only `Wailord L47 226/226` standing** (5 of 6 fainted, 20 faint-chooser events) ⇒ it wins room 1 and enters room 2 with ONE mon. ⛔ **DO NOT COMMISSION FRESH RECON** — `ai-research-notes/` holds EIGHT Ch24 notes incl. `2026-09-07-ch24-elite-four-BUILD-SPEC.md` (12-leg shape; legs 5b-8b ARE step 2); a 9-agent workflow re-derived them and its own adversary said so (`08-MISTAKES.md` 2026-09-13). **Read the index first.**

**MEASURED BY ME against our own code, 2026-09-04 — not an agent's claim.** (A research agent
reported the in-battle cap was "1+ per battle"; the real constant is
`MAX_ITEM_USES_PER_BATTLE = 4` at `modules/story/battle_items.py:46`. The agent's number was wrong,
which is exactly why this was re-read rather than believed.)

**WHAT THE IN-BATTLE POLICY ACTUALLY DOES** (`battle_items.py`, a pure module):
- heals only below **`HEAL_AT_FRACTION = 0.35`** (line 40) — above 35% HP it attacks instead;
- picks the **cheapest SUFFICIENT** item, else the largest (rules 2, lines 94-104);
- **refuses to heal into a losing race** — if the best heal we hold is smaller than the biggest hit
  taken this battle, it attacks instead (rule 3, lines 89-92);
- is **bounded at 4 uses per battle** (line 46), and `on_battle_started` returns a FRESH strategy
  instance per fight, so the bound RESETS each fight ⇒ **up to 20 in-battle heals across the
  gauntlet**, against 33 usable HP items. The bound is not the problem.

⛔ **THE PROBLEM IS THE FILTER AT `battle_items.py:85`** — `if qty > 0 and param > 0`. Checked
against `modules/data/items.json`:

| item | bought | `battle_use` | `parameter` | in-battle usable? |
|---|---|---|---|---|
| Hyper Potion | 30 | healing | 200 | ✅ |
| Full Restore | 3 | healing | 255 | ✅ |
| **Full Heal** | **8** | healing | **0** | ✅ **YES since 2026-09-13** — reached by the STATUS policy (step 3), for **Sleep/Freeze only**. *(This cell read ⛔ NO.)* |
| **Revive** | **3** | healing | **0** | ⛔ **NO — still true 2026-09-13**: `allow_revive=False` at the call site, pending `KI-100`. |
| Antidote | 4 | healing | 0 | ⛔ NO — **still true and DELIBERATE**: poison is outside `TURN_COSTING_STATUSES` (Sleep/Freeze), so curing it trades a turn for nothing. ⛔ Do not "fix" this cell. |

⇒ **11 purchased items — ₽9,300 of the ₽54,300 — are invisible to the in-battle policy.** ⚠ **UPDATED 2026-09-13 — THE FULL HEAL HALF OF THIS IS NOW FALSE.** Step 3 wired a SECOND policy (`choose_status_or_revive_item`) that the `param > 0` filter does NOT gate, so the **8 Full Heals ARE used in battle** (Sleep/Freeze only; DRIVEN LIVE vs Sidney — decision #1 chose Full Heal). ⇒ **41 of the 44 are usable, not 33**; the **3 Revives** are the only unusable ones (`allow_revive=False`, pending `KI-100`). ⛔ "No out-of-battle party-heal helper" is ALSO false — step 1 shipped one on 2026-09-04. The module
says so on purpose (docstring lines 16-18: *"`Full Heal` is `parameter == 0` — a STATUS cure, not an
HP item, and is excluded here on purpose"*). It is a deliberate, documented scope boundary, **not a
bug** — but it is a boundary the Elite Four sits directly on top of. ⚠ **(2026-09-13: step 3 MOVED that boundary rather than crossing it — the HP policy still refuses `parameter == 0`; a SEPARATE policy handles those. The docstring quoted above remains accurate.)**

⛔⛔ **AND THE SECOND HALF IS WORSE: THERE IS NO OUT-OF-BATTLE PARTY-HEAL AT ALL.**
`modules/modes/util/items.py:43` `use_item_from_bag()` opens the bag, scrolls, presses A and waits
for the start menu — the shape for a **no-target** item like a Repel. A Potion or Revive then asks
*"Use on which POKéMON?"*, and **nothing in the tree answers that prompt.** ‼ Corrected while
writing this: `menuing.py:680/723/728` DO contain the strings "Revive"/"Max Revive", but they are
entries in `get_items_available_for_pickup()` — a list of what the Pickup ability can yield. **That
is not revive logic**, and reading it as such would have been a false reassurance.

⇒ **WHAT THIS MEANS FOR THE GAUNTLET, CONCRETELY:**
1. **HP carries over between all five fights** with no way to top up between rooms.
2. **A fainted Pokémon stays fainted for the entire gauntlet** — attrition is strictly one-way. The
   3 Revives cannot be used by any code path we currently have.
3. **Status is completely unhandled.** ⚠ **RETRACTED 2026-09-13 — steps 1 and 3 fixed exactly this: status IS handled, OUT of battle (step 1 — revive, cure and top up, **all statuses**) and IN battle (step 3, wired and DRIVEN LIVE). ⛔ **THE IN-BATTLE HALF IS SLEEP AND FREEZE ONLY** — they are the only statuses in `TURN_COSTING_STATUSES`; Poison / Burn / **Paralysis** are deliberately NOT cured, because they do not cost a turn and curing them trades a guaranteed attack for nothing.** *(Read "Gen-3 freeze does not thaw on its own" until 2026-09-13 — FALSE: Emerald self-thaws 20%/attempted move, `battle_util.c` `CANCELER_FROZEN`.)* Glacia's ice moves and
   a sleep/paralysis from any of the five would simply persist. The 8 Full Heals cannot be used. ⚠ **(As of 2026-09-13 they ARE used — in battle, proven on a staged-FROZEN lead against Sidney: decision #1 chose Full Heal. ⛔ **SLEEP AND FREEZE ONLY** — they are the only statuses in `TURN_COSTING_STATUSES`; Poison / Burn / **Paralysis** are deliberately NOT cured, because they do not cost a turn and curing them trades a guaranteed attack for nothing. ⇒ the **PARALYSIS named in the sentence immediately above is STILL not cured**, and that is deliberate, not a gap.)**

⛔⛔ **AND A THIRD THING, READ OFF THE FIXTURE FILE ITSELF (`probe_anchor_inventory.py
post_league_shop.ss1`) RATHER THAN RECALLED — THE PARTY IS NOT WHAT I HAD BEEN WRITING.**
I had been describing it as "L47 across the board". It is actually:

| slot | mon | level | verdict for the gauntlet |
|---|---|---|---|
| 1 | Sceptile | **L53** | real fighter |
| 2 | **Zigzagoon** | **L19** | ⛔ **DEAD WEIGHT** — HM mule |
| 3 | Swellow | **L48** | real fighter |
| 4 | Wailord | **L47** | real fighter |
| 5 | Mightyena | **L48** | real fighter (has Crunch) |
| 6 | **Castform** | **L36** | ⛔ **DEAD WEIGHT** |

⇒ ‼ **THIS IS A FOUR-POKÉMON PARTY, NOT A SIX**, against five trainers fielding ~25 Pokémon at
L46-58. Two slots are carrying an HM mule and a L36 passenger. **That reframes the level-gap question
entirely:** the cheapest intervention may not be grinding the four — it may be *replacing the two
dead slots*, which costs no grinding at all.
⚠ **AND IT ARMS A KNOWN BUG:** `#24-ch23wally` records that the faint-replacement ranking can feed
**Zigzagoon L19** into a fight. In Victory Road that cost a leg; in the Elite Four, where a fainted
mon cannot be revived (see above), sending the L19 in is **a wasted Pokémon we cannot get back.**
⇒ this is now a §Ch24 blocker too, not just a §Ch23 annoyance.

**THE WORK (in order):**
- [x] ✅✅ **`heal_party_from_bag()` IS BUILT AND DRIVEN (2026-09-04). ⛔ DO NOT REBUILD IT.** ‼ That warning is the reason this line survives: it is the §Ch24 between-rooms healing path, and the Elite Four has NO nurse between rooms, so a rebuild would re-litigate a solved and gated behaviour.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the build, its drive and its evidence are there.
- [ ] **2. Call it between rooms**, in the corridor after each Elite Four win, before the next door.
- [x] **3. DONE + DRIVEN LIVE (2026-09-13) — the in-battle policy GOT STATUS awareness; the REVIVE half stays OFF (`KI-100`).** *(This item read: "Decide whether the in-battle policy should get status/revive awareness", or whether
      between-room healing is enough. ⭐ Prefer step 2 first — it is the cheaper, more testable half,
      and it may make step 3 unnecessary." ⛔ That framing is SUPERSEDED: step 3 shipped FIRST, and step 2 is now the BLOCKED half — there are no rooms to heal between until §Ch24 exists.)*
- [x] **4. ANSWERED 2026-09-14 — MEASURED, AND THE ANSWER IS: DO NOT RAISE IT (yet).** The line below said this was *"a NUMBER TO MEASURE, not to argue about"*; it was measured. 35% against an E4 mon
      IS inside two-shot range — **VERIFIED by executing the real policy: at `53/147` (36.1%) it returns `None` and the next 59-damage hit leaves −6 ☠; at `51/147` (34.7%) it heals and the mon lives. Generalised: a hit worth 50-64% of max HP leaves the mon ABOVE the gate, so it never heals, and the next identical hit faints it.** ⛔⛔ **BUT RAISING THE THRESHOLD IS MEASURED HARMFUL TODAY, AND THE A/B IS DETERMINISTIC:** same fixture, same fight, only the threshold differs — `heal_frac=0.35` → **WON** (f35237, `ineffective=True` on **0** of 51 decisions); `heal_frac=0.50` → **LOST** (f46267, `ineffective=True` from decision 38, **31** of 68). ⭐ MECHANISM — ⚠ **both arms made exactly 2 item requests, so this is NOT "more requests"**: healing earlier changed WHICH request and WHEN (raised arm: decision 36, Mightyena 68/144; default: decision 47, Castform 13/103), and in the raised arm the request **did not execute** (HP 68 → 68); `battle_action_use_item` **does not reliably execute** (`battle_action_selection.py:985-988`, measured 2026-08-09: *5 requests → 1 potion consumed*), a failed bag-open `return`s and the strategy RE-DECIDES the same turn (`:1023-1024`), and the no-op detector counts those as misses and sets `_items_ineffective` — disabling ALL item use for the rest of the battle. ⛔ **THAT GUARD IS NOT A NEW DEFECT**: `06-DECISIONS-LOG.md` 2026-08-10 accepted it explicitly (*"the no-op guard costs at most one turn per battle and then disables items for that battle"*). What is NEW is that raising the threshold converts that accepted, bounded cost into a LOST Elite Four fight. ⇒ **the prerequisite for tuning this number is reliable item EXECUTION, not a better number.** Knob `POKEBOT_HEAL_AT_FRACTION` ships (default unset = 0.35) so the A/B can be re-run the day execution is fixed. ⚠ n=1 per arm, deterministic on replay; the MECHANISM is what carries the claim, not the win/loss. Evidence: `tools/story-dev/evidence/2026-09-14-ch24probe-STEP4-AB-heal0{35-WON,50-LOST}.stdout.txt`.

‼ **DO NOT "FIX" THIS BY EDITING `battle_items.py`'s filter.** That module is pure and exhaustively
tested by `repro_battle_items.py`; widening `param > 0` would silently make `effective_heal()` return
0 for a Revive and the policy would pick it as the "cheapest sufficient" heal for everything. The
right place is a NEW out-of-battle path.

---

### 🔶 `#24-ch23victoryroad` — **MIXED. READ EACH BULLET'S OWN MARKER; THIS HEADING DOES NOT CLOSE THE ITEM.**

✅ **DONE, ⛔ DO NOT REBUILD:** §Ch23 Victory Road is TRAVERSED and EXITED, party whole and bag stocked — ELEVEN LEGS BUILT AND DRIVEN, **and the chapter orchestrator + Segment 23 wiring SHIPPED 2026-09-05** (`ch23_chapter_done()` + `do_victory_road_chapter()`, dispatch at `story_mode.py`'s `# --- Segment 23: VICTORY ROAD ---` block, ending in `_guard("Victory Road (Ch23)", ch23_chapter_done)` — ⛔ **cite the SYMBOL: this read `:3779-3795`, which is a whiteout-exit settle loop ~1,335 lines away; corrected 2026-09-16**, `--driver ch23chapter`).
🔜 **STILL OPEN, and tracked so it cannot go invisible:**
* the chapter's CHAIN hangs on `KI-90` ⇒ **`#24-ch23chain`**;
* **`#24-ch23leg3arms`** — leg 3's owed fault arms and the B1F/B2F §F live checks, both stated in this item's own body below (`"LEG 3's OWED ARMS (still open)"`, `"the three live checks … are still owed"`).

⛔⛔ **WHY THIS HEADING IS 🔶 AND NOT ✅ OR 🔜 — BOTH WERE WRONG, IN OPPOSITE DIRECTIONS.** 📦 *(SUPERSEDED WORDING, quoted as history — the phrases below are what this heading FORMERLY said; neither is a live claim.)* It formerly read *"ONLY THE CHAPTER ORCHESTRATOR + SEGMENT 23 WIRING REMAIN"* (an UNDERclaim commanding the rebuild of shipped work, caught by Tier 1), and was then promoted to *"✅ … DO NOT REBUILD ANY OF IT"* (an OVERclaim over a body that still says "still open", caught by Tier 1 the very next round). ⇒ ⭐ **the project's own pair-P2 rule is the answer: a heading is a claim about every bullet beneath it, and when their statuses differ the heading must say MIXED.** ⚠ The party ends at 35% with three fainted — `#24-ch23attrition` — ✅ **CLOSED 2026-09-04** (the party is back to 807/807 with zero fainted; the fix was a 36-step walk to the League's Poké Center, not the ~5 hours of training I had priced). *(This clause read "now ACTIONABLE because the bot can finally leave" until a Tier 1 reviewer quoted it against that item's own CLOSED header — P2: a heading is a claim about everything it points at.)* (filed 2026-09-03, updated 2026-09-04)

> ⛔⛔ **THAT HEADER DROPPED THE UN-DRIVEN EXIT FOR ONE COMMIT — THE FOURTH TIME THIS ITEM'S HEADLINE HAS BEEN CAUGHT CLAIMING MORE THAN ITS OWN BULLETS.** The bullet one line below it listed the arrow warp; the header said "ONLY the wiring remains". `04-HANDOFF.md` had it right in BOTH halves, so this was the punch list alone regressing. ⇒ **when a header enumerates what remains, diff it against the bullet directly beneath it before committing** — and note that gate #35 cannot catch this shape, because no CLOSED slug is being mis-described.

> ⛔⛔ **P5 CAUGHT THIS ITEM FOR THE THIRD TIME (2026-09-04).** Twice before, a CHILD item was closed while this PARENT kept commanding the finished work; this time its header still read *"Leg 6 ships WITHOUT a heal step"* and its bullet still said *"Add the heal before building leg 7"* AFTER `#24-ch23healdescent` closed. ⇒ **closing a child is not updating the parent, and this item is where that keeps failing.** A research note calls this item *"the authoritative live status"*, so a cold agent reading it would rebuild shipped work and start leg 7 from the superseded 32%/3-fainted fixture. **Whoever closes the next §Ch23 child item: grep this slug and re-read this block FIRST.**

> ⛔ **HEADER/BODY PAIR NOTE (2026-09-04).** This header read "LEGS 1-4 SHIP AND PASS; LEGS 5-8 REMAIN" for one commit *after* its own body bullet had been corrected to "legs 6-8" — a Tier 1 reviewer caught it. **P2: a header is a claim about every bullet beneath it**, and updating the body alone is the more dangerous state, because the body looks current.

- [x] ✅✅ `#24-ch23chain` — **§Ch23 IS A CHAPTER: DONE 2026-09-05.** The orchestrator (`ch23_chapter_done()` + `do_victory_road_chapter()`) and the Segment 23 dispatch shipped.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — all eleven legs' readings, fault arms and acceptance lines are there in full.
      **THE FACTS A LATER SESSION ACTUALLY NEEDS — the leg→fixture chain, kept here:** `post_training` → `post_wally` → `post_b1f_healed` → `post_b2f` → `post_return` → `post_vr_exit` → `post_league_heal` → `post_league_shop`.
      ⚠ Two inherited caveats that are NOT closed: the league basket is stocked but **only 33 of 44 items were usable when filed** (`#24-e4healing`; half since corrected — Full Heal *is* usable **both out of battle AND in battle** (step 3, driven)), and §Ch23 leaves the party **degraded** — `post_wally.ss1` is 67% HP with TWO fainted, so **heal before using it as a start point**.
      ⇒ the live successor is `#24-levelgap`: §Ch23 ends at ~L47 and the gauntlet needs ~L62.
### 🔧 `#24-linebudgetchars` — **THE LINE-COUNT DOC BUDGET REWARDS CRAMMING, AND IT HAS NOW PRODUCED THE ROT IT EXISTS TO PREVENT.** (filed 2026-09-03)

- [ ] **`lint_docs.py` R3 counts LINES and nothing else** (`lint_docs.py:156`, `if lines > budget`).
      There is no character or word check, so the cheapest way to stay under budget is to append to
      an existing line rather than add one. That is exactly what happened: `04-HANDOFF.md`'s §Ch23
      queue head reached **~14,000 characters on ONE line**, and by the time it was read it carried
      **four statements that later text on the SAME line falsified** — *"§Ch23 has none"* (a
      fixture), *"STILL OWED: dump the bag's HMs"*, *"genuinely UNMEASURED"* (Flash), and
      *"B1F/B2F STILL HAVE NO TRAINER OR BOULDER AUDIT"*.
      ‼ **This is the second time in two days the same rot hit the same queue item, and a warning
      about it was already ON the line** — the §Ch22 retirement note, which says in so many words
      that a chronological append-log inside a current-state file rots from the middle.
      ⇒ **The lesson is not "be careful". A gate that measures the wrong quantity does not merely
      fail to help — it actively teaches the workaround that defeats it.** The budget was meant to
      force retirement; it produced an unreadable line instead.
      **Proposed fix (cheap, and it must be FAULT-TESTED before it is trusted):** add an R-rule
      capping any single line in a current-state file at ~2,000 characters, and prove it (a) fires
      on the pre-retirement queue head, and (b) does NOT fire on legitimately long table rows —
      ⚠ `03-PUNCH-LIST.md`'s `#24-remainingarc` row is a single cell of many thousands of
      characters, so a naive rule turns Tier 0 red immediately and the next agent bypasses it.
      ⇒ **scope it to non-table lines first, or grandfather the known offenders explicitly.**
      ⚠ Do NOT raise the line budgets as the fix — that removes the pressure to retire without
      addressing why retirement was avoided.

### ✅✅ `#24-ch22chapter` — §Ch22 IS A CHAPTER: **DONE AND CLOSED 2026-09-03.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (R3 line budget; nothing deleted). ⛔ Nothing outstanding: built, wired as **Segment 22**, driven to `ACCEPTANCE: PASS` (`frames=64563`, `ice_steps=64`, `b1f_steps=19`, `battles_on_B1F=0` with `b1f_entered=True`, `CONTINUE=23`, `RECOVERIES 1`), both fault arms exercised — **and it passed by LOSING the gym fight and recovering.** The chapter ladder is **23 of 24**. ⚠ The two facts §Ch23 inherits: the Juan fight is **stochastic (5 wins, 1 loss over six distinct RNG draws)** so a story run may spend ~35k extra frames there; and ⛔ **KI-47 can freeze the shared battle path inside it** — `#24-ki47rotatelead`, deliberately NOT fixed. ⇒ the live successor is `#24-ch23victoryroad`.

### ‼‼ `#24-ki47rotatelead` — the RotateLead switch can wedge EVERY battle in the game (2026-09-03)

- [ ] ⭐⭐ **MECHANISM PROVEN, REPRO DETERMINISTIC, FIX DELIBERATELY NOT ATTEMPTED YET.**
      `battle_action_selection.py:269-291` drove the in-battle party menu onto **the mon already on
      the field**; the game refused (`gStringVar4 = "SCEPTILE is already in battle!"`, which ends in
      `PAUSE_UNTIL_PRESS` and returns to the chooser) and the branch's last statement is an
      **unbounded** `while get_game_state() == PARTY_MENU: press A; yield` — no counter, no break,
      no raise. ‼ The KI-46 bound cannot fire: `unrecognised` only increments in the
      "no branch matched" paths, so it is frozen at 0 once a branch matched. Only
      `handle_battle._watch`'s 3,000-frame net caught it. Full evidence in **KI-47**.
      ⛔ Repro: `POKEBOT_CH22JUAN_JITTER=181 … --driver ch22chapter` (~22,000 frames).
- [ ] ⛔ **THE NEXT STEP IS AN OBSERVE-ONLY PROBE, NOT A FIX.** Why the cursor sat on slot 0 is
      UNEXPLAINED — three index spaces are conflated here (battle-party id vs menu slot vs live
      `gPlayerParty` index, all MEASURED divergent in the stall state), and a reconstruction of
      `select_rotation_target` predicts slot 4, not 0. **This is the `handle_fainted_pokemon` shape
      a FOURTH time** (KI-18/34/66 + `#24-faintchooser-fourthspace`), and the standing rule is that
      an index conversion has its DIRECTION MEASURED before it is applied. Log `index`,
      `in_battle_index`, `gBattlePartyCurrentOrder`, `gBattlerPartyIndexes` and the live cursor
      immediately BEFORE the A-spam and again after `scroll_to_party_menu_index` — the party order
      is observed to change 35 frames after the decision, so a stale conversion is a live candidate.
- [ ] ⚠ **AND THE STALL SIGNATURE IS BLIND TO MENU CHURN.** `_progress_sig`
      (`battle_handler.py:257-269`) is script instruction + main callback + learn-move state + total
      exp — none of which a party-menu ping-pong changes. ⇒ "KI-47 fired" means *this signature
      stopped moving*, NOT *the game stopped moving*. Worth widening once the above is settled.
- [ ] ⛔ **ANY FIX TOUCHES EVERY BATTLE IN THE GAME**, so it needs an A/B on the ORDINARY case, not
      just on this repro (SESSION DISCIPLINE #9).

### ‼ `#24-pressbuttoncause` — a prevention rule's stated MECHANISM contradicts the code (2026-09-03)

- [ ] ⚠ `08-MISTAKES.md` (2026-09-02, §Ch21 leg 5) says `press_button` on every frame **HOLDS** the
      button, denying `waitbuttonpress` its `JOY_NEW` edge. ✅ But `modules/libmgba.py:476` is
      `self._pressed_inputs |= (self._prev_pressed_inputs & mask) ^ mask` with `_pressed_inputs`
      cleared every frame — **so it AUTO-RELEASES: every-frame calls give a clean edge every two
      frames.** The `frames % 4` fix worked; its recorded CAUSE cannot be right as written.
- [ ] **THE DISCRIMINATOR:** one arm with the duty cycle removed and the `not ...is_active`
      predicate KEPT, on the §Ch21 leg-5 fixture — the two landed together, so neither was isolated.
      ⛔ Until it runs, the fix stands and the cause is marked UNVERIFIED, **not deleted**: a wrong
      recorded cause that is flagged is far safer than a silent one, and a rule pointed at the wrong
      mechanism is what makes the next person apply the wrong remedy.

### ‼ `#24-retiredclaimgate` — a RETRACTED claim survives a literal grep, four times in one round (filed 2026-09-03)

- [ ] **THE MEASUREMENT THAT MOTIVATES IT.** Retracting one claim ("the party cannot win Juan" →
      it won; *believed* 4/4 at the time, later measured 5W/1L) took **four sweeps**: my literal grep (12 hits fixed), then Tier 1 pass 1
      (3 more), then a Tier 1 pass aimed at *where the fixes landed* (4 more — including
      `04-HANDOFF.md`'s own YOU-ARE-HERE banner, the first thing a cold agent reads), then my own
      sweep again (1 more). **Every survivor was a PARAPHRASE**: *"THE LIVE WORK IS NOW §Ch22 (GYM 8
      — JUAN)"* contains none of the search terms and says the same wrong thing.
      ⇒ full narrative + three prevention rules: `08-MISTAKES.md` 2026-09-03.
- [ ] **THE GATE, to be written** (proposed name: an `audit_retired_claims` script alongside the
      other doc gates in `tools/story-dev/` — ⛔ it does NOT exist yet, so this is a SPEC, not a
      citation). A small registry of
      `(retired phrase or regex, retired-on date, the marker that legitimises a quotation)` — and
      the gate fails if a retired phrase appears anywhere in `PROJECT KNOWLEDGE/` or
      `sandbox-pokebot/modules/story/` **outside** an adjacent supersede marker.
      ⛔ **FAULT-TEST IT BOTH WAYS** (the standing rule): prove it FAILS on a re-introduced phrase,
      and prove it does NOT fire on the retraction's own quotation of that phrase — this gate's
      whole failure mode is flagging the sentence that says *"this used to read X"*.
      ‼ Seed the registry from the retractions already in `08-MISTAKES.md`; each one is a phrase
      that has already cost a sweep.
- [ ] ⚠ **SCOPE HONESTLY.** This catches re-introduction and literal survivors. It CANNOT catch a
      paraphrase nobody registered — which is the majority of what the reviewers found. ⇒ it is a
      RATCHET, not a replacement for the independent sweep; say so in its own docstring so the next
      reader does not retire Tier 1 on the strength of a green gate.

### ‼ `#24-crackedfloorpathfinder` — the planner cannot see a hole in the floor (filed 2026-08-24; §Ch21 half RETIRED 2026-09-02, POST-GAME half still OPEN)

- [ ] **WHAT SURVIVES, AND IT IS ONLY THE POST-GAME HALF.** `map_path.py` does not model
      `"Cracked Floor"` at all — decoded in `map.py:391`, then never consulted
      (`grep -n "Cracked" map_path.py` = ZERO hits). The real blocker is the **Rayquaza CAPTURE**
      (post-game), which needs 10 cracked tiles crossed on Sky Pillar 2F at `PLAYER_SPEED_FASTEST`
      = **Mach Bike at `bikeFrameCounter == 2` ONLY**; the Acro Bike returns `PLAYER_SPEED_FASTER`
      and **always falls**. Also gates **Mirage Tower** and **Granite Cave B1F**. The bot is
      BIKELESS (`RECEIVED_BIKE=False`, measured).
      ‼ Whoever fixes it must decide whether a cracked tile is *a hazard to avoid* or *a traversal
      edge with a destination* — for the Sky Pillar it is BOTH, tile by tile. A hazard-avoiding
      planner would report the summit UNREACHABLE, which reads as "our pathfinder is broken", and
      this project has burned days on exactly that shape.

⛔⛔ **THE ENTIRE §Ch21 HALF OF THIS ITEM IS RETIRED — IT IS RESOLVED, AND IT WAS DANGEROUS.**
Its headline claim ("no crack-free route exists on 2F/4F") was **REFUTED 2026-09-01**: it measured
the DEFAULT/post-game crack set, while the story runs on the `*_Clean` layouts where 33 of 38 (2F)
and 29 of 34 (4F) are SOLID GROUND. Every leg had a crack-free story route, and banning 4F's five
real cracks cost nothing (29 wp either way, measured). `SKY_PILLAR_TOP` was validated the same day.
**And all of it has since SHIPPED: legs 3, 4 and 5 are built and driven, and §Ch21 IS A CHAPTER as
of 2026-09-02** (`--driver ch21chapter`, PASS, `frames=95823`) — including the deliberate falls the
planner cannot propose, and the ROUTE131 live-pin the swim turned out to be impossible without.
Full narrative: `07-CHANGELOG.md` 2026-09-01 and 2026-09-02.
‼ **WHY IT IS RETIRED RATHER THAN LEFT TO ACCRETE:** a Tier 2 cold-start audit found this item
**commanding the opposite of the live first action**, under four layers of inline SUPERSEDED /
REFUTED markers stacked on one another — a reader who stopped at any one of them got a different
answer. ⇒ *when an item's claim is refuted AND its work has shipped, COMPRESS it to what survives;
stacking another correction on top is how it became unreadable.*
### ✅ `#24-ch21anchor` — CLOSED. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-11, R3 budget; nothing deleted, zero open boxes).
- [x] ⛔ DO NOT REDO. Full detail in the archive under its 2026-09-11 banner and in `07-CHANGELOG.md`.

### ‼ `#24-divegroundroute120` — a MEASURABLY better Dive-learner ground nobody had evaluated (filed 2026-08-24)

- [ ] **Route 120 Marill beats Route 117 Marill on every axis, and the 2026-08-13 plan never
      enumerated it** — it framed the choice as Route 117 vs Shoal Cave only.
      | | Route 117 (wired today) | **Route 120 (proposed)** |
      |---|---|---|
      | slot rate | Marill 10% | **Marill 15%** |
      | levels | L13 | **L25-27** |
      | trip from Mossdeep | **1,055** waypoints | **379** out / 395 back |
      ⇒ 2.8× shorter, ~13 levels more useful, outdoors (no tide, no KI-73, no cave-warp threading).
      ✅ **AND IT IS INERT FOR TRAINING — MEASURED:** adding it to `TRAINING_GRASS` **with**
      `AREA_PREREQ[ROUTE120] = "surf"` changes **0 of 66** levels L5-70. ⛔ That prereq entry is
      LOAD-BEARING, not cosmetic: WITHOUT it, 47 of 66 levels change.
      ⚠ **NEEDS ONE LIVE SWEEP BEFORE ADOPTION** — this project demotes statically-derived grounds
      (the Route 114 lesson), and all 436 of Route 120's encounter tiles are **Long Grass** while
      every ground swept to date is plain **Tall Grass**. ⛔ Whether `spin()` behaves on Long Grass
      is NOT DETERMINED; the sweep must assert it.
      ‼ Prefer a SEPARATE HM-ground table over appending to `TRAINING_GRASS` — `_hm_hunting_grounds`
      has exactly one production caller, so the blast radius is provably nil, and
      `06-DECISIONS-LOG.md` already names that shape. ⛔ Do NOT reuse `HUNTING_GROUNDS`; that dict
      feeds the counter planner and would widen a second consumer.
      ⛔ **DO NOT RE-PROPOSE SHOAL CAVE.** Ruled out 2026-08-13 (user-delegated): at HIGH TIDE its
      reachable on-foot encounter tiles are **0**, so the hunt silently burns its whole budget.
- [ ] ⛔⛔ **2026-09-10 — THIS ITEM IS *NOT* A FIX FOR THE §Ch23 REFUSAL, AND THAT WAS TESTED BEFORE
      IT WAS PROPOSED.** `Marill` is the named offender in 11 of 23 refusal events and is the Dive
      carrier acquired at ROUTE117 **L13**, so re-prioritising this from "quality" to "capability"
      looked obvious. **[MEASURED — `tools/story-dev/probe_dive_carrier_level.py`]** it is not:
      L13 → **406,972** frames · L25 → **352,518** · L27 → **336,755**, against a **250,000** ceiling.
      ⇒ **every reachable acquisition level REFUSES**, so this stays a QUALITY upgrade and the
      2026-08-13 ruling is **VINDICATED**, not undermined.
      ⭐ The validation also found the carrier is **inert in the exp-bearing batch** (521/521 at
      `L13:exp1757`) — ⚠ but see `#24-lowlevelmules`: corpus-wide it DOES level (1,492 readings
      above L13), so "never gains" was a one-batch scope error of mine plus observation censoring.
      **Full record: `07-CHANGELOG.md`, "A better Dive ground would NOT clear the gate".**

### ‼ `#24-hmgroundwatertiles` — two HM hunting grounds are WATER tiles priced off the LAND table (filed 2026-08-24)

- [ ] **A silent 40,000-frame stall, tried FIRST.** `ROUTE118 (29,15)` and `ROUTE119 (21,109)` are
      **Ocean Water, elevation 1**, where only the SURF table fires — but `_hm_hunting_grounds`
      reads `enc.land_encounters` only, so it promises Linoone/Zigzagoon while the tile can only
      produce Tentacool/Wingull/Pelipper. They are the LAST two entries and `ensure_hm_learner`
      tries `reversed(grounds)`, so they are the **first** thing a post-Norman **HM03 Surf** hunt
      attempts — spinning its full budget meeting nothing that can learn Surf, then reading as bad
      luck. Same shape as the failure the Shoal ruling refused.
      ⚠ **STATIC ROM READING, NOT A DRIVEN OBSERVATION.** Confirm cheaply first: spin on
      `ROUTE118 (29,15)` and log the species actually encountered.
      ‼ Related: `ROUTE115/118/119`'s recorded training BANDS are land bands on water tiles, so
      `best_training_area` mis-describes those grounds too.

### ‼ `#24-gatescopeharness` — the undefined-name gate is blind to `tools/story-dev/` (filed 2026-08-24)

- [ ] ⛔ **RE-SCOPED 2026-08-24 — THE ORIGINAL FILING RESTED ON A FALSE PREMISE.** It claimed
      `repro_undefined_names.py` was "structurally blind" to `story_harness.py`. It is NOT: that file
      has been in `EXTRA_FILES` since 2026-08-12, added for the very same missing-`os` bug. The two
      `NameError`s that killed a 25-minute drive were caught by nothing because **the gate was not
      RUN before the drive**, not because it could not see the file.
      ⇒ **What IS genuinely uncovered: the REST of `tools/story-dev/*.py`** — ~100 probe/repro
      scripts outside `EXTRA_FILES`. Widening to them is still worth doing.
      ⚠ **NOT a blind switch-on**: those scripts have never been linted, so the baseline is unknown —
      give it its own RATCHET the way `probe_abort_swallowing` has one, rather than demanding zero.
      ‼ And the cheaper half needs no code at all: **run the gate suite BEFORE a long drive**, not
      only before a commit.

### 🔧 `#24-advisorydocstring` — **`advise_on_diff.py` FIRES ON HAZARDS DESCRIBED IN DOCSTRINGS, SO DOCUMENTING A TRAP ACCUSES YOU OF HAVING IT.** (filed 2026-09-03, MEASURED)

- [ ] **R-LOOP false-fired on `victory_road.py` for a `while True:` THAT DOES NOT EXIST** — the only
      occurrence is `:149`, inside the **module docstring**, describing KI-83. AST-verified: the file
      has **six `For` loops and ZERO `While` loops.** **Cause:** the tool strips `#` comments, but a
      **docstring is a string expression, not a comment**, so documented hazard names reach the
      matcher as code.
      ⛔⛔ **THE PERVERSE INCENTIVE IS THE POINT: the more carefully you DOCUMENT a hazard, the more
      the tool accuses you of COMMITTING it** — and this project asks every module to explain its
      traps in its docstring, so the two rules fight. ‼ *A gate with false positives teaches the
      reader to bypass it* — advisory-only makes that cheaper, not harmless.
      **Fix, FAULT-TESTED BOTH WAYS:** blank every `ast.Expr` string before matching. ⭐ The two arms
      are the point: (a) a real `while True:` still FIRES; (b) the same text in a docstring is
      SILENT. Without (a) the "fix" could just disable the rule.
      ⚠ Likely affects the other text-matching rules too — check them in the same pass.
      ✅ The rest of that advisory run was correct: R-EXCEPT prompted a real check, and
      `probe_abort_swallowing.py` reports **23 sites, exactly at baseline** — zero new debt.

### ✅ `#24-difftriggeredrules` — **DONE 2026-08-26, CLOSED.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (R3 budget; nothing deleted). ⛔ DO NOT REBUILD. `tools/story-dev/advise_on_diff.py` — 9 diff-keyed rule families, ADVISORY and never blocking (exit 0 either way), delivered by `.claude/hooks/advise-on-commit.ps1` as `additionalContext` only; ⛔ deliberately NO `permissionDecision`, because an "allow" would auto-approve the commit past the user's own prompt. Proof: a 32-check `--self-test` (every rule both ways) plus a mutation test. ⭐ **IT IS LIVE AND EARNING ITS KEEP:** on 2026-09-03 its **R-SCANBOUND** rule caught a coordinate scan in a new probe bounded by the WRONG shaft's floor — the output had been right only by luck. ‼ Adding a rule = one table entry + its two self-test arms (T25 enforces the pairing).

### ‼ `#24-sanitycheck2` — the deep sanity check is 2 passes of 5 (filed 2026-08-27)

- [ ] **PASSES 1-2 RAN (20 fault-injecting agents) and paid for themselves** — 5 gate defects fixed,
      13 stale-prose contradictions corrected (`07-CHANGELOG.md` 2026-08-27). ⛔ **PASSES 3-5 DID
      NOT RUN** (account limit twice; the user ruled the 40-agent fan-out too expensive — do NOT
      re-run it that way). **What is therefore UNAUDITED since 2026-08-22:** (3) story-code
      re-verification (loop bounds + `_check_abort` placement since `dce95b4a`, A-press gating,
      PID-identity, era-keyed Expect rot); (4) infrastructure (runner controls, fixture-coverage
      delta, evidence orphans, shared-state growth, the contention gate's live status); (5)
      cold-start startability. ⇒ **DO IT CHEAPLY — greppable/AST checks INLINE, or 2-3 agents per
      pass; ⛔ never a 40-agent fan-out.** Angle list: the workflow script `deep-sanity-5x8-*.js`.
### ‼ `#24-reprosweepratchet` — WHAT THE STANDING SUITE DOES NOT RUN, ROTS (filed 2026-08-23)

- [ ] **⛔ MEASURED, not theorised: the SAME script was written off as "environmental" TWICE.**
      `#24-brokenrepros` fixed six `repro_*.py` scripts. **None of the 104 repros is in
      `run_gates.py`** — the suite covers 28 enforcing gates, and the rest are run only when somebody
      remembers to. Consequences already paid, twice on one script:
      * 2026-07-30 — `repro_double_faint`'s stub lost `level` when the KI-18 tiebreaker landed; its
        own comment records it was *"recorded as environmental, needs a real mgba, for days. It needs
        no emulator at all."*
      * 2026-08-23 — the SAME script, the SAME misfiling, a different missing stub attribute
        (`is_double_battle_with_partner`). It was not in the item's own table of five, and only a
        full 150s sweep of all 104 surfaced it.
      ⇒ **A doc line saying "environmental" is a CLAIM, and it is self-sealing: it tells the next
      reader not to run the thing that would refute it.**
      ‼ **DESIGN (do NOT just bolt 104 scripts onto `run_gates.py` — the suite is 158s and must stay
      fast enough to run every commit):** a `repro_sweep_ratchet.py` that runs every `repro_*.py`
      with the 150s cap and asserts the set of failing scripts is a SUBSET of a documented allowlist,
      each entry carrying a REASON. Ratchet semantics, like every other gate here: the set may shrink
      freely, may never grow. ⛔ Run it as an ADVISORY/slow tier or on a schedule, NOT in the hot
      suite; and ⛔ `repro_x4_lanes` must stay excluded — it spawns real lane processes.
      ⚠ **Fault-test both directions:** break a passing repro (must fire); add a listed one (must
      stay silent); and prove the allowlist cannot silently absorb a NEW failure.

### ‼ `#24-codeorphans` — SIX SLUGS THAT CODE CITES AND THIS FILE NEVER DEFINED (filed 2026-08-22, PASS 5)

- [ ] **⛔ THE `#24-orphans` SHAPE AGAIN, and this time the dangling pointers are IN THE CODE.**
      Measured: each slug below has **0 mentions in this file** and is referenced from a script or
      a KI. `repro_fortree_gate_solver.py:1` literally opens *"ACCEPTANCE CHECK for punch-list
      #24-fortreegates"* — a gate declaring itself the acceptance check for an item that does not
      exist. ⇒ **These are STUBS to make the pointers resolve, not a claim about their status;**
      each needs triage against the code before anyone works it (this file's own history has THREE
      items marked "ready to build" that had already shipped).
      | slug | cited from | what the citation says it is |
      |---|---|---|
      | `#24-fortreegates` | `repro_fortree_gate_solver.py:1` | Fortree Gym rotating-gate solver; the script is its acceptance check |
      | `#24-harness-finish` | `story_harness.py:10181`, `compare_runs.py:158` | distinguish a run that FINISHED from one that HUNG — a live grading question |
      | `#24-boxmessage` | `story_harness.py:1653` | capability test: does a FULL-PARTY catch complete and exit cleanly |
      | `#24-endlessruns-gui` | `endless_runs.py:9` | lands in the currently UNPROMOTED GUI bundle |
      | `#24-bosstelemetry` | `probe_boss_healing.py:16,118` + 3 KI cites | per-turn opponent logging; `probe_boss_healing` reads what it writes |
      | `#24-areaitemgate` | `05-KNOWN-ISSUES.md:1302` | touches the heal/item path alongside `#24-pc` |
      ⚠ **SEPARATE, related defect:** five more slugs exist ONLY as rows of the (now re-titled)
      MIXED index at the top of this file and have no `- [ ]` item anywhere — `#24-pathsourcecheck`,
      `#24-npcgifts`, `#24-grounditems`, `#24-remainingarc`, `#24-shoalcave`. ‼ **`#24-pathsourcecheck`
      was RE-DERIVED AS REAL AND OPEN:** `map_path.py:968` still passes only the
      NEIGHBOUR tile to the accessibility predicate and never the SOURCE tile (the predicate is
      `is_tile_accessible`, `map_path.py:829`), and KI-60 is still open in `05-KNOWN-ISSUES.md`.

- [ ] `#24-fixturecoverage` — **NEW 2026-08-22 (deep sanity check PASS 4). ‼ REFERENCED FROM CODE
      (`verify_fixtures.py`) — this item may not be deleted without editing that file.**
      **`verify_fixtures.py` walks the MANIFEST, never the DIRECTORY**, so a save with no
      `saves/FIXTURES.md5` row is not merely unprotected, it is INVISIBLE. **MEASURED: 11 rows
      against 77 `.ss1` on disk ⇒ 66 fixtures neither PINNED nor declared VOLATILE.** Among them
      **`at_steven_2f.ss1`** (the KI-66 driver's anchor) and **`ch13_fortree_door.ss1`** (KI-80's
      condition table) — both cited in the docs as things evidence rests on.
      ✅ The gate now PRINTS the gap at every run (advisory, 2026-08-22). ⛔ It deliberately does NOT
      fail: 66 red files would block every commit, and a gate that cries wolf is worse than none.
      **THE WORK:** decide PINNED vs VOLATILE per file and add rows. ⚠ **Pin nothing you have not
      first measured as stable** — pinning a save a driver rewrites turns the suite permanently red,
      and `verify_fixtures.py`'s own docstring records that "copy the file now" is NOT pinning.
      ⚠ 1 of the 77 (`midstuck.ss1`) is deliberately gitignored — a demoted shared scratch path, not
      a hole. Do not "fix" it.

- [ ] `#24-gateselftests` — **NEW 2026-08-22 (PASS 4). Make PASS 4's fault-injections PERMANENT.**
      **MEASURED, and worse than the lead said: 21 of 28 suite gates had NO `--self-test`** (⚠ re-derive: the suite is **29** now and 7 carry one, so **22** lack it — `selftest_git_add_hook.py` is the 29th and is the precedent to copy) (the
      earlier note said "9 of 11 sampled"). ‼ **"No self-test" is NOT "cannot fail"** — pass 4's
      agents demonstrated by injection that most of the 21 DO fail correctly (all four static
      scanners, all four behavioural repros, lint R1-R6, preflight's four sections,
      `verify_fixtures`, `audit_flag_names`, `repro_party_accounting`, `repro_impassable_dirs`).
      ⛔ **But those demonstrations lived in ephemeral scratch and are now GONE.** That is the whole
      item: a gate proven to fail once, with no standing proof, decays to a gate nobody can trust.
      ⇒ Port the injections into `--self-test` blocks, cheapest first. Precedent to copy exactly:
      `selftest_git_add_hook.py` (2026-08-22) and `repro_whiteout_abort.py --self-test`.

- [ ] `#24-testrunsweep` — **NEW 2026-08-22 (PASS 4). 98 more `LibmgbaEmulator(...)` sites still
      lack `is_test_run=True`.** Without it the emulator registers an atexit that OVERWRITES shared
      `profiles/<name>/current_state.ss1` and drops a `states/` snapshot — so an "observe-only"
      probe mutates state the next run reads. **MEASURED: `profiles/repro-ml/states/` had reached
      2,820 files / 160 MB.** ‼ **RE-DERIVE BOTH, do not trust these digits** (a Tier 1 reviewer
      correctly flagged them as bare numbers): sites =
      `grep -rn "LibmgbaEmulator(" tools/story-dev/*.py | wc -l` minus `... | grep -c is_test_run`
      (⛔ the `grep -c ... | grep -v` form I first wrote here is BROKEN — it emits per-file counts, so
      the filter matches nothing; caught by a PASS 5 agent running it verbatim); accumulation =
      `ls sandbox-pokebot/profiles/repro-ml/states/ | wc -l` and `du -sh` on the same path. Both
      GROW with every run on every machine, so they are readings, not properties. ✅ Pass 2 fixed 2 (the KI-76 probes); **PASS 4 fixed the 7 that are in
      the STANDING SUITE** and PROVED it (states count and `current_state.ss1` mtime byte-identical
      across four probe runs). ⛔ **The remaining 98 were deliberately NOT swept**: `is_test_run`
      also suppresses LOADING `current_state.ss1` (`libmgba.py:144`), so it is a BEHAVIOUR change,
      and a blind mass-edit of 98 files could silently change what a probe boots from.
      ⚠ `story_harness.py:122` is the real driver and probably SHOULD keep profile state — decide it
      explicitly rather than sweeping it. ⇒ Do them in batches, running each after.

- [~] `#24-p4residuals` — **SIX OF SEVEN DONE 2026-08-23; only (f) remains.**
      ✅ **(a) `--strict`, (b) fence-blanking, (c) `splitlines()`, (d) the DENYLIST, (e) `--build`
      on three gates, (g) proximity-scoped supersede — all shipped, each fault-tested BOTH ways.**
      ⛔⛔ **TWO OF THEM PROVE THE ITEM'S OWN PROPOSED FIX WAS WRONG, and both were refuted by
      MEASUREMENT before any code changed:** (d)'s relevance-keyword allowlist would have newly
      failed **43 genuine handlers** (all 60 comment justifications are real; this codebase justifies
      in DOMAIN PROSE, not keywords) and broken the ratchet on all four roots; (g)'s span-port
      inverts the corpus's direction (the drift check needs the marker BEFORE the claim; gate-count
      retractions here come AFTER the figure) — 1 false positive over 143 commits. See
      `06-DECISIONS-LOG.md` and `07-CHANGELOG.md`, both 2026-08-23.
      ⚠ **NO PRODUCTION CODE WAS TOUCHED — drift is unchanged at 1.**
      *(This header said "Six" while listing seven, then "SEVEN" — both caught by audits the same day.)*
      ✅ **(a) DONE 2026-08-23 — `--strict` added, proven on all four arms (drift 1 → check 0 /
      strict 1; forced drift 0 → both 0).** Original: `promote.py --check` — the drift "authority" — **ALWAYS exits 0**
      (`promote.py:117-120` returns 0 before any refusal), so it cannot be chained or gated.
      VERIFIED FROM SOURCE, not from a passing run. ⇒ add `--strict`; ⛔ do NOT make plain `--check`
      exit 1 on drift — drift is a normal state, not an error.
      ✅ **(b) DONE 2026-08-23 — fences are blanked before R1/R2 scan, LINE COUNT PRESERVED so R3
      and `--show` are unaffected; fault-tested 5 ways.** Original: lint R1/R2 fire on `# HISTORY` and banner text INSIDE fenced code blocks (latent
      today). ⇒ strip ``` fences before scanning.
      ✅ **(c) DONE 2026-08-23 — `len(text.splitlines())`; all five files drop by exactly 1, none
      changes pass/fail, boundary still discriminates (900 quiet / 901 RED).** Original: lint R3 counts `text.count("
")+1`, one MORE than `wc -l` for any file ending in a trailing newline.
      ⛔ **NO EXAMPLE FIGURE IS QUOTED HERE — the first draft cited two line counts and both were
      stale within a day.** Re-derive: `wc -l <file>` beside `lint_docs.py`'s budget table.
      Harmless DIRECTION (it over-counts, so the effective limit is one stricter) but the budget
      is off by one. ⇒ `len(text.splitlines())`.
      ✅ **(d) DONE 2026-08-23 — a DENYLIST, not the proposed allowlist (see the header). Gate still
      reports exactly 148, per-root 133/4/3/8 unchanged; new `--self-test`, 10 reject + 8 keep
      cases, fault-tested three ways.** Original: `repro_no_silent_except.py:107` justifies a silent handler on comment LENGTH
      (`>= 12` chars), not relevance — any filler comment launders it.
      ✅ **(e) DONE 2026-08-23 — `--build sandbox|custom` on all three, PROVEN not a no-op (153
      offender paths under the selected fork, 0 under the other); two now REFUSE loudly instead
      of tracebacking on a missing fork.** Original: `repro_undefined_names.py`, `repro_no_silent_except.py`, `repro_roster_reorder.py`
      hardcode `sandbox-pokebot` with no `--build` (only `repro_pid_identity_key.py` has one) ⇒ a
      defect landing in the PROMOTED fork is invisible to all three.
      ⛔ **(f) IS THE ONLY ONE LEFT — and it is deferred DELIBERATELY.** That gate is 573 lines,
      boots a ROM and orchestrates its arms as SUBPROCESSES, so ARM C is a real emulator drive
      with its own verification, not a quick addition. ‼ A gate change that cannot be proven in
      the same sitting should not ship in that sitting. Evidence intact below.
      **(f)** `repro_ki65_unbound_party_index.py` tests only the UNBOUND read; the documented KI-65
      residual (a legitimately-bound `party_index = -1`, i.e. the LAST party member) is untested and
      REPRODUCES THE LIE when injected (`lie_msg=1`, Loudred consulted instead of Marshtomp).
      ⇒ add ARM C.
      ✅ **(g) DONE 2026-08-23 — unit scope KEPT, direction-agnostic PROXIMITY of 120 chars added.
      Measured over 143 historical commits: 4 TRUE-STALE, 0 FALSE POSITIVES, 0 findings lost, 0 on
      the live tree; the reinjected `28 gates` defect is now CAUGHT.** Original: `audit_doc_consistency`'s supersede exemption is NEIGHBOURHOOD-BOUND, not
      CLAIM-BOUND — the SAME bug shape already fixed in `check_promotion_prose` on 2026-08-17.**
      ⚠ **ITS EXAMPLE IS NOW UNREPRODUCIBLE — a starter must build a fresh one** (the stale line was
      fixed the same day). The GATE DEFECT is still real: `audit_doc_consistency.py:513` still scopes
      the exemption to the whole unit. As it was MEASURED: `04-HANDOFF.md:51` carried a stale GATE-COUNT claim (a suite size two behind
      reality) six lines above a correct one, and the gate stayed SILENT. ⛔ The stale sentence is
      DESCRIBED here, not reproduced — quoting it verbatim re-created a live-looking false claim
      that `audit_doc_consistency` then flagged, correctly, in this very file — because the claim falls inside a **3,975-character unit**
      that contains the words *"older framing"* somewhere, and one supersede marker exempts the
      WHOLE unit, live orientation instructions included. A **Tier 1 human-shaped reviewer** caught
      it; the gate structurally could not. ⇒ scope the exemption to the SENTENCE/clause, as
      `check_promotion_prose` now does. ⛔ **MEASURE THE BLAST RADIUS FIRST** — narrowing it will
      un-exempt every number in every large annotated block, and a flood of false positives is worse
      than the miss. *(A seventh phrasing was added to the claim regex the same day; it is correct
      and matches this line in isolation — it simply never gets consulted here.)*

- [ ] `#24-flagnamedocscan` — **NEW 2026-08-22 (PASS 4). ⛔ THE OBVIOUS FIX IS REFUTED BY
      MEASUREMENT — do not build it.** `audit_flag_names.py` scans only story `*.py`; docs are never
      checked, and CLAUDE.md names docs as exactly where hallucinated flag names land.
      **But gating doc flag names WOULD BE NOISE** — and ⚠ **TWO INDEPENDENT MEASUREMENTS OF THIS
      POPULATION DISAGREE** (293 unresolvable / 438 mentions / 49 files vs a later 281 / 500 / 59),
      because the population is REGEX-DEFINED and therefore definition-sensitive. ⛔ **Do not pick a
      side — re-derive with your own scan and state your regex.** Both agree on the SHAPE, which is
      what decides the ruling: the overwhelming majority of hits are in `ai-research-notes/` — explicitly "RECALL ONLY, never
      authoritative", where unverified names are the POINT — and of the **15 in 7 authoritative
      docs**, most are prose PLACEHOLDERS (`FLAG_NAME`, `FLAG_BADGE`, `VAR_TEMP`,
      `FLAG_MOSSDEEP_GYM_SWITCH_X`). A gate firing on those trains the reader to bypass it.
      ‼ **ALSO MEASURED AND NON-OBVIOUS:** the ground truth (`modules/data/event_flags/emerald.txt`)
      stores **BARE** names (`BADGE07_GET`), while docs use the **decomp** prefix
      (`FLAG_BADGE07_GET`) — a naive comparison reports 100% failure. *(My first probe did exactly
      that and I nearly filed 652 phantom findings; the CHECK was wrong, not the docs.)*
      ⇒ **THE REAL WORK IS SMALL:** adjudicate the ~8 non-placeholder names against the decomp via
      `gh api repos/pret/pokeemerald/contents/...` — `FLAG_RECEIVED_HM03`,
      `FLAG_DEFEATED_RIVAL_ROUTE119`, `FLAG_RECEIVED_ITEMFINDER`,
      `FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_1`, `FLAG_RECEIVED_MAGMA_EMBLEM`, `FLAG_DEFEATED_CHAMPION`,
      `FLAG_RECEIVED_TM27`, `FLAG_GET_CAUGHT`. Fix any that are wrong; gate nothing.

- [ ] `#24-driftreduction` — **NEW 2026-08-17, split out of `#24-driftassertions` (which shipped the
      GATE half). Assert the drift number in ONE place; every other site points at the command.**
      Keep the STATE table row (it is where a cold start looks) and the HOW TO RUN `Expect:` line
      (it is a grading claim); everywhere else should say *"run `promote.py --check`"* with no digit.
      ✅ **THE MEASUREMENT THAT SIZES THIS JOB ALREADY EXISTS:** the corpus carries **67** windows
      mentioning a drift figure across the 7 current-state docs, classified as ~16 claims about now,
      ~24 historical measurements, ~29 prose-about-the-problem. **Only the claims-about-now are in
      scope** — ⛔ do NOT strip the historical ones, they are the evidence trail, and the gate is
      built to leave them alone.
      ⚠ **DO THIS AT A QUIET MOMENT, NOT MID-ARC:** it touches the same lines every in-flight change
      touches, and a merge conflict here is a stale drift figure by another route.
      ‼ **AND IT IS NOW MUCH LESS URGENT THAN WHEN IT WAS FILED** — the gate half closed the failure
      mode this was meant to prevent (a stale figure surviving a hand sweep). Treat it as tidying,
      and re-run `audit_doc_consistency.py --self-test` after, because deleting figures changes the
      very corpus the false-positive controls were tuned against. ⭐ **2026-09-15 — FRESH EVIDENCE + A PARTIAL PAYDOWN AT THE SOURCE:** a phantom `drift: 1` (line endings; git stores ONE blob) forced its ENCODING-ONLY caveat to be hand-copied into THREE places in `04-HANDOFF.md`, and correcting the digit cost 4 edits across 2 files. Fixed in the METER rather than the docs — `promote.py` normalises newlines and reports line-ending-only files separately (gate #62). ⇒ that is 4 assert-sites fewer to tidy here. See `07-CHANGELOG.md` / `06-DECISIONS-LOG.md` 2026-09-15.

- [x] `#24-abortswallow` — **KI-81. ✅ CLOSED AND GATED. ⛔ DO NOT REOPEN.** Story/recovery paths must not swallow aborts; the swallow class was paid down 36 → 23 and is RATCHETED by gate #27 `probe_abort_swallowing.py`, so a new swallowing handler re-opens paid-for debt.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full write-up, the listed exemptions and the reasoning are there.
      ‼ **Two rules survive here, and a Tier 1 reviewer caught that my first summary named only the second:** the archived body's own *“ONE ENGINEERING RULE”* is **re-raise only the `BotModeError` family** (`higher_level_actions.py:842`); the companion mechanism, recorded at `07-CHANGELOG.md:15359`, is **`reraise_if_aborting(error)` as the FIRST statement** of any handler. Both are real; the archived text is the authority for the first.
- [ ] `#24-zerokocounter` — **NEW 2026-08-16, from the KI-80 decoupling. Should `boss_teaches` ALSO
      come off the counter-ladder's gate?** `story_mode.py:1901` is now `if boss_teaches:`. KI-80's
      wording ("gated on *is this fight hopeless*, which `_boss_plan_is_hopeless` answers alone")
      can be read as removing BOTH conjuncts. ‼ **The case FOR is strong:** a party that KOs
      **nothing** and has no type answer is the MOST hopeless case, yet today it gets the `:1932`
      "the boss can't teach us" message and plain grass escalation instead of a counter hunt.
      ⛔ **NOT SHIPPED BECAUSE NO TEST CAN SEE IT** — all four `ki80ladder` arms seed `kos = 1`.
      ✅ **DISCRIMINATOR COMPUTED** (arm 5: flat `kos = 0` on `batch2_run04_wedge.ss1`, NOGRASS):
      today → `PLAIN_ESCALATION`; after → `LADDER`. Non-vacuous.
      ⛔⛔ **BUT ARM 5 IS NOT ENOUGH — TWO HAZARDS, derived by a Tier 2 audit:** (a) removing
      `boss_teaches` makes `:1901` unconditional, so the `elif` at `:1932` is **structurally DEAD in
      every case**; (b) the not-hopeless path becomes reachable by a zero-KO party, so a boss with a
      **fodder patch AND a credible answer** would set `boss_mode = True`, print *"re-attempting the
      boss is the real training (KO'd [0, 0] of theirs)"* and **SUPPRESS `:1937`'s grass
      escalation** — KI-23's mirror regression again. **⇒ an ARM 6 is required too** (HAS_ANSWER +
      `kos = 0` + fodder patch). Same lesson as arms 1-3 vs arm 4.
      ⚠ **AND MEASURE FIRST:** nobody has checked how often a flat zero-KO loss series occurs in
      production. `analyse_defeat_loops.py` measured *"53 sequences with >=3 defeats — flat in 37"*
      but never broke out zero-KO series. ⛔ Do not change behaviour of unknown frequency.
      ‼ **PROMOTED TO A TOP-LEVEL ITEM 2026-08-16** because a Tier 2 audit pointed out the irony: it
      was filed as a nested bullet inside `#24-roster`'s body — reachable only from inside another
      item — which is precisely the defect `#24-orphans` exists to stop. `#24-orphans` says SIX;
      this was the seventh. *(The full derivation stays in that nested bullet; this is the tracked
      entry point.)*

- [ ] `#24-rarepredicate` — ‼ **NOT READY TO BUILD. 2026-08-07: the dataset does not reproduce,
      and as computed it FAILS the user's own named example.**
      `tools/story-dev/rare_species_dataset.py` (new) is the **first script in this repo that
      computes this dataset** — the figures below were prose only, with nothing to regenerate or
      audit them, and `#24-roster` is approved to build ON them.
      | | recorded 2026-08-06 | computed 2026-08-07 |
      |---|---|---|
      | histogram | `d0=59 d1=21 d2=39 d3=7 d4+=3 d99=3` | `d0=62 d1=36 d2=22 d3=11 d99=1` |
      | depth>=3 | 13 species | 12 |
      | RARE (either rule) | 26 of 132 | 23 of 132 |
      | **Skitty** | rare via rate (2%) | ✅ **rate 2%, depth 0 — reproduces exactly** |
      | **Bagon** | pseudo-rare via warp depth, **d3** | ❌ **depth 2 — NOT selected** |
      ‼ **The `>=3` threshold exists FOR BAGON**, and under this derivation Bagon is d2, so the
      rule as written does not select the example that motivated it.
      ‼ **DO NOT tune the BFS until Bagon comes out at 3** — that is fitting the method to the
      desired answer. The punch list already predicted this exact fragility ("Meteor Falls' d2
      rooms are ALSO Surf-gated in reality, so `>=3` earns some of its precision by luck of
      Bagon's room being one warp deeper"); that luck does not hold here.
      **WHAT UNBLOCKS IT:** pin ONE definition of warp depth deliberately — the seed set, whether
      the connection closure is transitive, and warp directionality (making warps bidirectional
      moved d99 from 34 to 1, so that choice alone dominates the answer) — write the reasoning
      down, and make that script authoritative. Then re-decide the threshold with Bagon's real
      depth known. Skitty's rate rule is unaffected and is already reproduced.
      ✅ ‼ **USER INPUT 2026-08-14 — THIS MAY RETIRE WARP DEPTH ENTIRELY, WHICH WOULD UNBLOCK
      THE ITEM.** Asked what makes Bagon pseudo-rare, the user did NOT describe warp distance —
      they described **HM GATING plus LOCATION SCARCITY**, verbatim:
      > "For the Bagon instance, it is locked behind a Surf AND Waterfall requirement, and it is
      > only available in that one location which to me would be considered 'pseudo-rare' simply
      > based on the gating and limited location, encounter rate may not be low enough to
      > constitute a legit 'rare' tag but those other factors contribute to it being somewhat
      > rare/hard to find."

      > "For Feebas, that one should be considered rare due to the limited (potentially random)
      > tiles it is available on (also gated by fishing rod and surf requirement) as well as low
      > spawn rate"

      ⇒ **The candidate replacement rule is `HM/field-move gate count` + `distinct location
      count`, not BFS warp depth.** Bagon = 2 field-move gates (Surf, Waterfall) × 1 location ⇒
      pseudo-rare; that is a DIRECT read of the user's reasoning rather than a proxy that has to
      be tuned until it agrees. ‼ **This is exactly what "pin ONE definition deliberately" asked
      for — and warp depth was never the user's mental model, it was ours.**
      ⚠ **Feebas needs a special case regardless of the rule chosen:** it is one of the known
      false negatives that are **absent from `encounter_index` altogether** (with Beldum, gift
      and static species), so no rate-based or location-count rule can see it; and its real
      mechanic (a handful of seed-chosen tiles on ROUTE119) is not expressible in the encounter
      tables at all. Treat it as an explicit entry, not as something the predicate derives.
      ⚠ Field-move gates are partly modelled already (`training_areas.AREA_PREREQ` uses
      `"surf"`/`"rocksmash"`; `region_reach.KNOWN_GATES`) but **Waterfall and rod requirements
      are not**, and `KNOWN_GATES` is admittedly incomplete — pricing that gap is step 1.

- [x] HISTORY — `#24-rarepredicate` (original spec, 2026-08-06) — **the duplicate-catch exemption (`#24-roster` ruling 3). SOLVED — the  — 📦 **ARCHIVED 2026-08-23 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).

- [x] `#24-hmteachloop` — **ROOT-CAUSED AND FIXED 2026-08-07.** The HM-teaching loop defect, closed; the user's description of the symptom turned out to be literally accurate.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full root-cause narrative and its fix are there.
- [x] HISTORY — `#24-hmteachloop` (original report) — **USER-REPORTED 2026-08-06. Real bug, wastes frames and looks buggy.**
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full entry, its evidence and any ⛔ warnings are there.
- [x] `#24-movepoolcounters` — **SHIPPED 2026-08-07. It is the fix for `#24-winonaground`.**
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full entry, its evidence and any ⛔ warnings are there.
- [x] HISTORY — `#24-movepoolcounters` (original measurement) — **USER DIRECTIVE 2026-08-07.**  — 📦 **ARCHIVED 2026-08-23 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).

- [x] `#24-counterdesertgate` — **FIXED 2026-08-07, the same day it was found. CLOSED.** The desert-gate counter defect.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full root cause and fix are there.
- [x] HISTORY — `#24-counterdesertgate` (original diagnosis) — ✅ FIXED 2026-08-07, the same day it was found. **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05** (no loss, no orphan — both invariants asserted before writing).
- [x] `#24-huntreachproof` — **PART 1 SHIPPED AND BATCH-CONFIRMED 2026-08-08.**
      **CONVERSION 15% → 50% (5/33 → 10/20), z = +2.73 — RESOLVABLE ✅.** Hunts fell 33 → 20 and
      catches DOUBLED. `could not reach` 72 → 53; `global watchdog` 9 → 0.
      ‼‼ **PART 2 AS PLANNED IS CANCELLED — the batch REFUTED my (anchor → ground) hypothesis.**
      `Numel @ FIERY_PATH` went 5 hunts/0 caught → **7 hunts/3 caught**, so FIERY_PATH *is*
      reachable from Mauville. The old 0/5 was **destination ORDERING**: the ladder spent the
      boss's single hunt on ROUTE111/ROUTE116 first and the bound was consumed before the good
      ground was tried. The per-anchor sweep campaign would have fixed a problem that does not
      exist. **Do not run it.**

- [x] `#24-slugmaspin` — **‼ BATCH-CONFIRMED 2026-08-09 AND CLOSED.** The Slugma-spin defect, confirmed against a real batch (`x4-runs/20260809-081643`) rather than argued from code.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the batch evidence, the counts and the reasoning are there.
- [x] `#24-slugmaspin` (original finding) — **Winona's rung FIRES but does not convert.**
      `Slugma @ FIERY_PATH`: **5 hunts, 0 caught** — on the same ground that converts 6/8 for
      Machop and 3/7 for Numel in the same batch, so **it is not travel**. This is the movepool
      work reaching production for the first time; the catch is the last missing step.
      Likeliest causes, in order: the **10% encounter rate** (vs Machop 15% / Numel 30%) against
      the spin budget; or the catch-on-sight branch not targeting the species.
      **NEXT PROBE: instrument the Slugma spin — arrivals, encounters seen, species matched —
      BEFORE changing anything.** Winona is 6 of 20 non-finishes.

- [x] `#24-huntreachproof` (part 1 detail) — **narrowing: `hunt_ground_tile(require_driven=...)`,
      strict by default.** ✅ DONE. Retired to a summary 2026-09-03; detail in `07-CHANGELOG.md`.

- [x] `#24-huntreachproof` (original finding) — ✅ CLOSED. **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05.** The ORIGINAL 2026-08-08 framing — *"only ONE counter rung has ever worked"* — kept for its reasoning; the shipped answer is the `- [x]` entry above.
- [x] `#24-r116sweep` — ✅ **ANSWERED 2026-08-09, CLOSED: DO NOT ADD ROUTE116 to `HUNTING_GROUNDS`. Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-08-17** (the R3 relief valve: this file hit its 3,600-line limit). ⛔ Nothing here is outstanding; read the archive for the reachability method behind the ruling.

- [x] `#24-battleitems` — ✅ **DONE, PROMOTED 2026-08-10 (user-approved), zero source drift.**  — 📦 **ARCHIVED 2026-08-23 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).

- [ ] `#24-r110mauville` — **NEW 2026-08-09, MEASURED (KI-48).** `_navigate_riding_out` cannot
      walk ROUTE110 → MAUVILLE_CITY: **3/3 identical deterministic failures** at (16, 89), with
      the planner enumerating only Mauville's **six building doors** and never the map
      connection. Story mode makes the same trip every run, so it is a gap in the direct
      navigation entry point, not a map fact. Repro is ~1,400 frames (see KI-48).
      ‼ A door-warp transition race is **RULED OUT** by a retry-after-settle A/B — do not
      re-test it. ‼ Do NOT assume it explains the batch's 72 `could not reach` events without a
      measurement that could discriminate.

- [x] `#24-r116sweep` (original framing) — **NEW 2026-08-08.** His only LEGAL pre-badge answer is **Nincada @ ROUTE116** (verified
      Bug/**Ground**; ROUTE116 carries no prereq), and `#24-huntreachproof` part 1 removed it
      because ROUTE116 is in `TRAINING_GRASS`, not `HUNTING_GROUNDS`.
      ‼ **Do NOT relax the narrowing to get it back** — permissiveness measured 28 wasted treks
      and 15% conversion; the narrowing took conversion to 50% (z = +2.73). **EARN the entry:**
      sweep ROUTE116 from Wattson's real anchor (**MAUVILLE**) with
      `probe_counter_reachability.py`, both directions, and add it to `HUNTING_GROUNDS` only if
      it passes.
      ‼ Do not assume it will: Nincada @ ROUTE116 was **5 hunts, 0 caught** in batch
      `20260808-095721`. The sweep exists to answer that, not to confirm a hope.

- [x] `#24-progressiongate` (original finding) — ‼‼ **USER-IDENTIFIED 2026-08-08, VERIFIED. The counter planner has  — 📦 **ARCHIVED 2026-08-23 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).

- [x] `#24-teachmsgstall` — ✅ **FIX SHIPPED 2026-08-11 AND KEPT; ⚠ REOPENED THE SAME DAY** because
      batch `20260811-130454` showed it had **no measurable production effect** (success 38/47 vs
      38/42 pre-fix, **z = -1.28 NOT resolvable**; the new `already-advanced` exit fired **ZERO**
      times in 85 teaches). The one-frame `Task_ReplaceMoveYesNo` window was real and
      decomp-confirmed, and the fix closes it and costs nothing — but **it was not the dominant
      production cause, and another path to `exhausted` remains unfound.** Promoted 2026-08-11,
      user-approved, verified DRIVEN in `custom-pokebot` as the same A/B, frame-for-frame identical.
      📚 **The full 344-line investigation — the decomp trace, the A/B, the batch statistics and the
      reopening analysis — is ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md` (moved 2026-08-16 on the
      3600-line budget). Nothing was deleted.** ‼ The live summary of its status is the table row
      for `#24-teachmsgstall` near the top of this file; this entry is its history.
- [x] HISTORY — `#24-teachmsgstall` (original characterisation) — ✅ superseded; the live status is the `- [x]` entry above (shipped 2026-08-11, reopened the same day). **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05**, including its task signature, its "post_select DOES NOT MATTER" analysis and its NEXT STEP plan.
- [x] HISTORY — `#24-winonaground` (wrong-cause history) — ✅ CLOSED. **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05** (no loss, no orphan — both invariants asserted before writing). It records a diagnosis that was WRONG and how it was corrected.
- [x] HISTORY — `#24-winonaground` — **the original text was WRONG and is superseded.** Retired to
      a summary 2026-09-03; the wrong claim, its refutation and the measurement that settled it are
      in `07-CHANGELOG.md` and `08-MISTAKES.md`. ⛔ Kept as a slug so citations resolve.

- [ ] `#24-ballstarve` — **NEW 2026-08-07.** `Cannot hunt a Surf learner: no Poké Balls and no
      money to buy any` — 4 occurrences + 1 whole run derailed, batch `20260807-102552`. Consistent
      with KI-43's note that catches rose while each restock still buys 10 balls. Pairs with the
      end reason `No party mon can learn Surf and the party is full — needs PC box management`,
      which the now-proven `#24-pcoverflow` withdraw path should be able to serve.
      ⚠ **MEASURED 2026-08-13 — the premise DOES NOT HOLD at `post_dive.ss1`, which does NOT
      close this item.** `probe_dive_learner_plan.py` reads **19 balls** (Poké 16 / Premier 1 /
      Great 1 / Master 1) and **$54,334** there — `affordable_poke_balls()` = 269, and the Mossdeep
      mart door is 27 waypoints away. So a hunt at the CURRENT era is not ball-starved.
      ‼ **This is a late-game anchor and the item was filed from a mid-game BATCH** (4 occurrences,
      Surf-era, party still small and poor). Ball starvation is plausibly a real EARLY/MID-game
      condition that simply does not reproduce this late. ⇒ **Do not close on this evidence** —
      it needs a measurement at the era the batch actually failed in. Recorded so the next reader
      does not re-derive "we have no balls" from a stale headline.

- [x] `#24-teachpathrace` — **FIXED 2026-08-07, the same day it was found. CLOSED.** The HM-teaching path race, caught by a gate rather than by a run.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full root cause and fix are there.
- [x] HISTORY — `#24-teachpathrace` (original report) — ✅ CLOSED (fixed 2026-08-07, same day). **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05**, including its root-cause and FIX SHAPE paragraphs.
- [x] `#24-whiteoutloop` — **BOTH PARTS SHIPPED 2026-08-07. CLOSED.** The whiteout-loop defect, fixed in both halves.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — both parts, their reasoning and their evidence are there.
- [x] HISTORY — `#24-whiteoutloop` (part 2, "the hard plateau") — ✅ CLOSED; BOTH PARTS SHIPPED 2026-08-07. **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05** (no loss, no orphan — both invariants asserted before writing).
- [x] HISTORY — `#24-whiteoutloop` (diagnosis) — ✅ CLOSED; both parts shipped 2026-08-07. **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05** (no loss, no orphan — both invariants asserted before writing).
- [x] ~~`#24-mtpyre-batch`~~ (superseded) — **NEXT ACTION. Batch Segment 14 before trusting any finish rate.**
      Every run that beats Winona now continues into Mt. Pyre, so run length and finish rate
      both change by construction. Read against the **52.0%** baseline (`20260805-075638`).
      Watch: does the Route 121 gate fire reliably from a real run's approach (the live proof
      started from a save already ON Route 121's north band)? Do the four summit-corridor Aqua
      grunts' sight-lines derail the ascent?

- [x] ~~`#24-mtpyre`~~ (superseded) — **‼ NOW UNBLOCKED (2026-08-05) AND THE TOP ITEM. First chapter past
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full entry, its evidence and any ⛔ warnings are there.
- [x] `#24-r121gate` — ✅ **CLOSED 2026-08-10: IT WAS ALREADY BUILT** — the THIRD stale "ready to build" header found that week, caught only because the spec was verified before coding. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted). ‼ **Its TWO REUSABLE RULES WERE PROMOTED to `14-AGENT-PLAYBOOK.md` §4 (items 2 and 6) on 2026-08-24** — *accessors take the BARE var name* and *`calculate_path` spans only DIRECTLY CONNECTED maps* — because a chapter author never looks inside a CLOSED punch-list item, and both had been costing real time.
- [x] ~~`#24-r121topology`~~ (superseded) — **DO THIS BEFORE ANY MORE NAVIGATION WORK ON MT. PYRE.**
      From ROUTE121 (21,5) — where the ROUTE120 connection lands — `calculate_path` reaches
      neither Route 121's own south edge nor ANY Route 122 tile, **with surf allowed**
      (`BADGE05_GET=True`, `party_has_surf=True`, both measured). So the blocker is topological,
      not a missing capability and not a tile-choice heuristic.
      **(1)** Dump ROUTE121 at FULL WIDTH — every dump so far covers only x=0-46 of **80**.
      **(2)** Reachability-sweep from (21,5) (`calculate_path` per sampled tile, the KI-39
      method). **(3)** Then decide if the Mt. Pyre route goes via LILYCOVE instead.
      ‼ Two `_connection_step` heuristics have already failed inside the untested assumption
      that Route 121 is traversable from the entry point. Measure first.

- [ ] `#24-connstep` — **WRITTEN, BOTH VARIANTS FAIL, GATED OFF (`POKEBOT_CONNECTION_STEP=0`).**
      It crosses the ROUTE120→ROUTE121 border the old code could not, then strands the bot in
      Route 121's north band (its own south edge is unreachable from the tile chosen). Cause:
      the candidate lattice scans `y` from the TOP, biasing north when the target is south.
      **Fix before enabling:** (1) aim the choice with `map_path`'s global `offset`/`level`;
      (2) remember rejected targets (`used_warps` pattern). **Then batch it.**

- [ ] `#24-connstep-batch` — **RUN A BATCH BEFORE ENABLING `#24-connstep`.**
      The connection step (shipped 2026-08-05, live A/B: old dies on ROUTE120, new reaches
      ROUTE121) has **no outcome measurement**. `navigate_to_anywhere` is used by every chapter,
      so a regression here is broad. Read the finish rate against the **52.0%** baseline
      (`20260805-075638`) and watch for journeys that now wander instead of failing fast.
      ‼ Known weakness to watch: the step target is a coarse-lattice tile, not aimed at the
      onward route, so it can land somewhere with less onward reachability than ideal.

- [x] `#24-magmahideout` — ✅ **DONE, CLOSED. Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-08-17** (`#24-handoffbudget`'s relief valve: this file hit its 3,600-line R3 limit). ⛔ Nothing here is outstanding; read the archive only if you need the history.

- [x] `#24-strength` — ✅ **DONE, CLOSED. Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-08-17** (`#24-handoffbudget`'s relief valve: this file hit its 3,600-line R3 limit). ⛔ Nothing here is outstanding; read the archive only if you need the history.

### ‼ THREE FLAGS THAT MUST STAY `0` (each hides a MEASURED regression)
`POKEBOT_LEAD_DEMOTE_WONDER_GUARD` (~20 pts) · `POKEBOT_AREA_ITEM_GATE` (~7 pts) ·
`POKEBOT_PC_ROTATION` (~19 pts of the last rung). All three REMOVED something and were
justified by counting failures without counting successes. Do not re-enable without a batch.


### ~~READY TO APPLY THE MOMENT BATCH `20260802-160603` LANDS~~ — ✅ APPLIED; header stale  — 📦 **ARCHIVED 2026-08-22 (PASS 5, R3 budget) → `28-HANDOFF-ARCHIVE.md`. CLOSED; moved verbatim, nothing deleted.**

### ‼ BATCH 5 LANDED — the blocker moved a THIRD time, to the LEAD  — 📦 **ARCHIVED 2026-08-22 (PASS 5, R3 budget) → `28-HANDOFF-ARCHIVE.md`. CLOSED; moved verbatim, nothing deleted.**

### ‼ APPLIED 2026-08-01 AFTER BATCH `20260801-075805` LANDED

- [x] `#24-counters-travel` (**KI-44**) — **FIXED 2026-08-01 and CLOSED.** The counter-travel defect; the fix landed and the outcome batch confirmed it.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full write-up and its batch numbers are there.
- [x] `#24-navready-budget` (**KI-43**) — ✅ **DONE 2026-07-31** — fixed via a dedicated nav-ready budget. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [ ] `#24-wdcanary-dedupe` — `summarize_lane` counts `global watchdog` in stdout AND the
      debug log, so every reported figure is ~2× (`9 → 143` is really `5 → 72`). Dedupe the
      source, then `--resummarise` **all four** batches so they are read by one instrument.
      ‼ Specific to this canary — `GAVE UP` is debug-only, `BADGE:`/`losses` stdout-only.

### ‼ BATCH REVIEW 2026-07-26 (bundle `20260726-231412`) — two catastrophic bugs found & FIXED  — 📦 **ARCHIVED 2026-08-22 (PASS 5, R3 budget) → `28-HANDOFF-ARCHIVE.md`. CLOSED; moved verbatim, nothing deleted.**

### ‼ BATCH REVIEW 2026-07-27 (bundle `20260727-063751`) — PRE-FIX DATA + a new failsafe hole
That batch launched before the fixes above existed, from a working copy that had not been
pulled, so it re-confirms them rather than testing them. It did expose one NEW bug:

- [x] `#24-x4-framebudget` — ✅ **DONE** — the per-run frame cap could not stop a runaway run; now it can. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [ ] `#24-weatherinstitute-hang` — the specific hang P3 hit: `do_weather_institute` →
      `_ride_out_all_scenes` (`early_game.py:455`), then `state=3 controllable=False` for
      27M frames. The frame budget now BOUNDS it (the run derails and the batch continues),
      but the underlying scene wait is still wrong. Needs the first post-fix batch to see
      whether it recurs and how often before spending time on it.
- [ ] ⭐ `#24-grindconverge` — **RE-SCOPED 2026-09-09 AFTER AN ADVERSARIAL PASS KILLED THE OBVIOUS
  READING.** P1/P2 ground for 13-20M frames without reaching a level floor.
  ⛔⛔ **DO NOT BUILD IT AS "REPLACE THE FRAME CEILING WITH A CONVERGENCE TEST" — THAT IS KILLED.**
  At §Ch23 the test is **VACUOUS**: `estimate_frames_to_level` returns `None` only when
  `wild_level is None or wild_level <= 0`, and §Ch23 hardcodes `WILD_MAX = 40`, so the estimate is
  ALWAYS finite and positive. A predicate *"will this grind reach the target?"* returns TRUE for
  every one of the 16 refusals. ⇒ it does not RAISE the ceiling, it **DELETES** it and substitutes a
  tautology — strictly worse than *"raise the ceiling"*, which is already measured wrong.
  ‼ **AND THIS ITEM'S OWN TEXT IS A COST TEST:** *"a training target that the local grass cannot
  deliver **in reasonable time**"*. *In reasonable time* IS cost. The item cannot be cited as
  authority for replacing cost with convergence.
  ⭐⭐ **ITS REAL SHAPE IS ALREADY DESCRIBED IN CODE AND IS NARROW AND BUILDABLE** —
  `victory_road.py:474-476`: a spin parked on an `MB_NORMAL` tile **generates ZERO battles while
  looking perfectly healthy**. ⇒ the failure is *no encounters*, not *slow encounters*. The DETECTOR
  already exists (`_story_spin`'s xp watchdog, `_STORY_SPIN_NO_PROGRESS_FRAMES = 2400`,
  `early_game.py:168/217`); **its defect is DISPOSITION, not detection** — it bails into the
  500-round retry loop instead of abandoning the target. ⇒ **build the disposition, and make it
  SUPPLEMENT the ceiling, never replace it.**
- [ ] ⛔⛔ **STRUCTURAL FACT THAT CHANGES EVERY "BUDGET HEADROOM" ARGUMENT — VERIFIED 2026-09-09.**
  `MAX_FRAMES_PER_RUN = 5_000_000` sits in `story_mode.py`, **inside `StoryEndlessResetMode`
  (`:4283`) — the BATCH HARNESS.** Production `StoryMode` (`:1123`) has **no total-frame budget at
  all**; `train_team` has only a 500-*round* guard. ⇒ **in a real run the per-call
  `MAX_TRAINING_FRAMES` ceiling is the ONLY pre-emptive bound in existence**, and removing or
  loosening it re-opens the `KI-28` shape with nothing behind it.
- [ ] ⛔ **AND THE HEADROOM ITSELF IS NOT THERE.** Measured at the 16 Ch23 refusals from debug-log
  `f`-stamps: median run had burned **85.8%** of the harness budget (median spare **710,600**, range
  78,800-1,932,800). The FULL bill — every battler under L47, not just the worst — exceeds the
  run's own remaining budget in **10 of 16** runs on the solo model and **14 of 16** with the
  2-way split, before the seven §Ch23 legs after training (declared caps ≥720,000).
  ⭐ **RE-RUNNABLE:** `py -3.12 tools/story-dev/probe_ch23_headroom.py` prints the 16-row table.
  ‼ These numbers were first published from an agent's report with no command behind them and a
  reviewer refused them; re-measured, two reproduced and **three did not** (median battlers 3.5
  → **3.0**, 9/16 → 10/16, 13/16 → 14/16). ⚠ Erratic/Fluctuating growth curves are approximated
  as Medium Fast in that tool, so species on those curves may be mis-costed.
- [ ] ⛔⛔ **"ONE UNDER-LEVELLED MULE" IS FALSE — IT IS 2-5 BATTLERS, MEDIAN 3.5.** Excluding
  `BENCH_SPECIES`, the count of battlers under L47 at the refusal is **2 to 5 (median 3.0)** (e.g. one run:
  `Swampert:L57 / Mightyena:L33 / Ninjask:L23 / Dustox:L29 / Machoke:L30 / Shedinja:L29` — **five**).
  The error message prints only `max(estimates)`, **which is why this tree believes it is one mon**.
  ⇒ every plan scoped to "the mule" is scoped to roughly a third of the real debt.
- [x] ⛔⛔ **WIRING THE PICKER IS KILLED 2026-09-09 — AND THE PREMISE OF THE 2026-07-21 DIRECTIVE IS
  📦 **THE FULL ITEM (221 lines: the 6-agent adversarial round, the measured overlap figures, and the reasoning that killed it) IS ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md`** under “WIRING THE PICKER IS KILLED — the full item, ARCHIVED 2026-09-17”. ⛔ It stays CLOSED; the summary above is the ruling, and the archive holds the evidence.
- [x] ✅ **SETTLED 2026-09-09 BY A CHECKED-IN TOOL — AND THREE EARLIER ANSWERS WERE ALL WRONG. CLOSED.**
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — ‼ the three wrong answers and why the tool settled it are there, and that trail is the point: it is why the answer is a TOOL and not a note.
- [x] ✅ **FIXED 2026-09-09 — TWO FALSE STATEMENTS IN THE FUNCTION THAT DECIDES RELOCATION.**
  **[MEASURED BY ME]** `training_areas.py:432` is
  `FODDER_RULE = _os.environ.get("POKEBOT_FODDER_RULE", "xp_rate")` — the default is **xp_rate** —
  while `_local_grass_is_fodder`'s docstring claimed *"behaviour under the default rule is
  byte-for-byte the legacy expression"* and its branch comment read `# "legacy" (default)`. **Both
  false, and not equivalent:** `xp_rate` returns NOT-fodder whenever `best_available_max` is falsy,
  so a caller that has not looked for an alternative gets NO relocation, where `legacy` would compare
  levels. ⇒ anyone reasoning about when this bot relocates got it backwards — **including my own
  agent brief, which three reviewers had to correct.** Comment-only fix; it adds one file to the sandbox drift (run `promote.py --check` — the authority, never restated here).
- [ ] ⚠ **`best_training_grass(mon_level)` — the per-mon, trainee-keyed picker requested 2026-07-21 —
  HAS NO **PRODUCTION** CALL SITE** (`training_areas.py:102`) — ⚠ it DOES have one TEST caller, `tools/story-dev/repro_no_return_grounds.py` (import :49, call :75), which exercises its no-return-ground refusal. *(This bullet read "ZERO CALL SITES" until 2026-09-09; my grep had been scoped to `sandbox-pokebot/` and `PROJECT KNOWLEDGE/`, so `tools/` was invisible to it. ⇒ a MEASURED claim must carry its SCOPE.)*. And
  `grep -c VICTORY_ROAD modules/story/training_areas.py` = **0**, so the picker cannot even compare
  against the ground §Ch23 uses. That is a `#24-trainmap+` gap, not a new concept.
- [ ] ⚠ **NEW, PREVIOUSLY UNFILED:** the post-hoc frame REPORT at `story_mode.py:4535`
  (`raw_frames = get_frame_count() - start_frame`) does **not** re-base across the reset performed
  inside `super().run()` at `:4506`, so **printed per-run frame totals are wrong**. The live
  enforcement path DOES re-base (`:4386-4388`), so the budget itself is correct — it is the REPORT
  that lies. ⇒ derive frames from debug-log `f`-stamps, never from the printed summary.
      (Route 103 wilds are L2-3; Route 116 L6-7). A training target that the local grass
      cannot deliver in reasonable time should be detected and abandoned, not pursued
      forever. Related to `#24-route110cap`: both are "the bot will not give up" bugs.
- [ ] `#24-canary11` — P4 broke the 1:1 losses:whiteouts ratio twice (run 1: 39 W vs 38 L;
      run 8 opens with a whiteout before any loss). Two events in 52. Most consistent with a
      whiteout crossing a run boundary rather than poison damage; the new per-run reset may
      already cover it. RE-CHECK on the first post-fix batch before investigating.

### ✅ ALL FOUR HARNESS FIXES VALIDATED LIVE — CLOSED. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-11, R3 budget; zero open boxes).
- [x] ⛔ DO NOT REDO. Detail in the archive and `07-CHANGELOG.md`.

### ✅ USER RULINGS 2026-07-29 — CLOSED. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-11, R3 budget; zero open boxes).
- [x] ⛔ DO NOT REDO. Detail in the archive and `07-CHANGELOG.md`.

### 🔶 `#24-dexhunt` — catch EVERY new species, and hunt for unseen ones — **MIXED as of 2026-09-10: the CATCHING FENCE is BUILT, PURE AND GATED (#50) — ⛔ DO NOT REBUILD IT — but its A/B is UNRUN, so EFFICACY is unproven, and the fence is deliberately NARROWER than the ruling. READ EACH BULLET'S OWN MARKER; THIS HEADING DOES NOT CLOSE THE ITEM.** (user proposal 2026-07-29, ruled 2026-07-31; re-affirmed and widened by a new user directive 2026-09-04)

⛔⛔ **THIS IS THE ITEM THAT SERVES THE 2026-09-04 CATCHING DIRECTIVE. DO NOT OPEN A SECOND ONE.**
*(I opened `#24-dexcatch` on 2026-09-05 with a fresh guard list before an adversarial reviewer found
this entry and the 2026-07-31 ruling. That ruling PINS the predicate — "the codebase already has the
right predicate: `counter_hunt.resource_blocker()`. **Reuse it rather than writing a second one that
can drift**" — so my guard list WAS the forbidden second predicate. `#24-dexcatch` is retired before
it ever shipped. See `08-MISTAKES.md` 2026-09-05.)*

**THE NEW DIRECTIVE (2026-09-04, verbatim):** *"I am fine with the bot catching and training
pokemon, it should be doing this as well as collecting pokemon (new, rare, considered rare) to fill
out the pokedex"*. ⇒ it does not overturn the 2026-07-31 ruling; it **widens** it — Pokédex
completion becomes a first-class goal, and **rarity becomes a selection criterion** rather than an
accident of what the bot happened to meet.

**✅ WHAT IS NOW MEASURED AND UNBLOCKED (2026-09-05):**
* **Dex: seen 116 / owned 11** — **105 species seen but never caught**, incl. Pikachu, Gyarados,
  Skarmory, Kingdra, Tentacruel, Crobat, Azumarill, Magneton, Xatu.
* **23 Poké Balls** held ⇒ `resource_blocker()`'s only remaining gate (`_ball_count() <= 1`) is clear.
* **A full party no longer refuses a catch** — ruled `#24-pcoverflow` 2026-08-05; it lands in the box
  and `pc_trip.withdraw_from_box` retrieves it. The PC is empty (all 14 boxes).
* **`#24-flyunlock` is CLOSED**, so the bot can finally REACH wild encounters at all.

**⛔ THE FIVE CONSTRAINTS AN ADVERSARIAL REVIEW FOUND — build against these, they are measured:**
1. **`_should_catch` already implements the right dex test** (`story_mode.py:2070`, comparing
   `owned_species` by national dex number). It is gated off by conditions written for the NARROWER
   pre-Gym-1 team-building purpose: `if get_event_flag("BADGE01_GET"): return False` and a
   party-full check. ⇒ **relax those two; do not rewrite the predicate.**
2. ⛔ **THE SPIN'S WATCHDOG IS EXP-BASED AND A CATCH EARNS ZERO EXP.** `_story_spin` stops after
   `_STORY_SPIN_NO_PROGRESS_FRAMES = 2400` of unchanged party EXP (`early_game.py:168,183-219`). A
   catch-and-skip phase moves that number by nothing ⇒ the watchdog fires every ~40 s and the caller
   re-navigates: **an invisible retry loop, not a hang you would see.** `counter_hunt.hunt` survives
   only because it FIGHTS nearly every encounter.
3. ⛔ **THE FRAME BUDGET IS BLIND HERE — KI-36.** `_run_with_frame_budget` cannot check itself while
   a battle handler sits above the mode, and a catch phase is ~100% battle handler. KI-36 measured
   25,632,106 frames against a 5,000,000 cap reporting `frame-cap=0`.
4. ⛔ **NEVER RETURN `BattleAction.Catch`.** It routes through `_listeners.py:277` to the STOCK
   `CatchStrategy`, whose `decide_turn` returns `switch_to_manual()` the moment no ball can be
   thrown (`catch.py:45-48`) — and ball exhaustion is this feature's DESIGNED terminus. Return a
   STRATEGY OBJECT (`StoryCatchStrategy`), which `_listeners.py:124` routes through `fight()`.
5. ⛔ **"PARTY UNCHANGED BY PID" IS A VACUOUS GRADE HERE** — with a 6/6 party every catch goes to the
   box by construction, so the PID SET cannot change and the check passes whether or not the feature
   ran. Keep it as a SAFETY INVARIANT; grade on **`owned_species` COUNT STRICTLY INCREASED** and name
   the new dex numbers. ⚠ And do NOT grade party ORDER: `choose_new_lead_after_battle` legitimately
   rotates the lead after a faint, which catch battles cause often.

- [x] ✅ **THE "88.8% ARE BORN BEHIND" FIGURE — WHICH IS THIS ITEM'S PRIORITY ARGUMENT — IS
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full entry, its evidence and any ⛔ warnings it carried are there.
- [x] ⭐⭐ **DESIGNED 2026-09-09 (6-agent adversarial pass) — VERDICT: BUILD A NARROWER VERSION.** The design pass and its verdict, CLOSED.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the six agents' findings and the narrowing are there.
- [x] ✅✅ **THE FENCE IS BUILT AND GATED 2026-09-10 (gate #50, 20 cases, fault-armed). CLOSED.**
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the fence's design, its 20 cases and its fault arms are there. The GATE itself is live in `run_gates.py` and is what actually enforces this; the prose was the record, not the mechanism.
- [x] ✅ **THE VACUITY QUESTION IS ANSWERED — MEASURED, NOT ARGUED. CLOSED.**
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the measurement and its reasoning are there.
### ✅ `#26-healnavbare` — FIXED 2026-09-11, **VERIFIED EFFECTIVE BY BATCH 2026-09-12**: 323 ride-outs fired, the targeted Slateport derail went **22/26/22 per batch → 0** beside 1,642 Slateport mentions (non-vacuous). ⚠ RESIDUE: 13 cases exhausted all 8 ride-outs (Fortree ×6, Petalburg ×6, Lavaridge ×2) — the mechanism works and is not universal. (filed 2026-09-11)

⛔ **DO NOT SIMPLY RAISE THE 8-ROUND BOUND.** A ceiling that is too high turns a fast visible failure into a slow one. The open question is *why Fortree/Petalburg/Lavaridge differ from Slateport*, not *how many more tries*. — **Everything below this line is the ORIGINAL 2026-09-11 filing, kept for the diagnosis; the bare-navigate it describes is FIXED.**

**`higher_level_actions.py:377`** — the helper ends in a bare
`navigate_to_anywhere(door_map, door_tile)`: no `avoid_scripted_events=False`, no retry, no
ride-out. If ANY coord event is armed on the way to a Poké Center door, `walking.py:499-505` raises
*"We unexpectedly triggered a scripted event … Switching to manual mode"* and the run derails.

⭐ **THIS IS THE GENERAL CASE OF A DEFECT ALREADY MEASURED AT 22-26x PER BATCH.** Its Slateport
instance (`#26-slateportpcderail`) was fixed 2026-09-11 by wrapping THAT call site. The helper itself
was deliberately left alone: it is the shared path for every heal in the project, and changing it
hours before a measurement batch is exactly the shape rule 9 warns about — *when a change touches a
shared path, the cheap decisive test is an A/B on the ORDINARY case, not more samples of the exotic one.*

- [ ] A/B the helper on an ORDINARY heal (one with no armed events anywhere near the door) BEFORE
      changing it — prove the wrapper costs nothing on the common path.
- [ ] Then move the ride-out INTO the helper and delete the per-site wrapper added at
      `sail_to_slateport` Leg 4, so the protection is not something each new caller must remember.
- [ ] ⛔ Do NOT use `expecting_script=True`: it suppresses the error WITHOUT riding the scene out,
      converting a visible derail into a silent wedge.
⚠ Until then, any NEW `heal_in_pokemon_center` call on a map with armed coord events inherits this.

---

### ✅ `#26-slateportpcderail` — **FIXED 2026-09-11**: the Slateport Poké-Center walk derailed to MANUAL 22-26x per batch. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (R3 budget).
- [x] ⛔ DO NOT REDO. `sail_to_slateport` Leg 4 now rides out the scene like Leg 3 already did. ↪ The shared-helper half is `#26-healnavbare`.

### ‼ `#24-prechecksentence` — `precheck_prior_art.py` answers a SENTENCE with a confident `0 hit(s)` (filed 2026-09-11)

⛔⛔ **ITS FAILURE MODE IS A REASSURING SILENCE, WHICH IS WORSE THAN NO TOOL** — and the handoff's
`➡➡➡` marker instructs every future session to run it.

**MEASURED 2026-09-11.** `main()` does `terms = [t for t in sys.argv[1:] if t.strip()]` and matches
`t.lower() in line.lower()` — so **each argv element is ONE WHOLE-PHRASE term** tested as a substring
of a SINGLE LINE. A natural-language query in quotes therefore cannot match anything:
```
precheck_prior_art.py "call best_training_grass per-mon during the early game"   -> 0 hit(s)
precheck_prior_art.py TRAIN_CATCHUP_GAP best_training_grass                      -> 30 hit(s)
```
⭐ **The second form surfaces a 2026-09-10 DECISIONS-LOG ruling that explicitly rejects the work the
marker was sending the reader to do.** Three sentence-shaped queries had returned clean first; the
ruling appeared only after a CONTROL query for something already known to be documented
(`widen TRAIN_CATCHUP_GAP`) ALSO returned 0 — proving the INSTRUMENT was quiet, not the tree.
‼ Nothing in the output hints at this: `0 hit(s) shown, 0 sitting near a VERDICT word` plus a
coverage footer reads like a thorough search that found nothing.

- [ ] **Warn on sentence-shaped terms.** If a term contains a space AND is longer than ~24 chars,
      print a loud banner: *"this looks like a sentence; each argument is matched as one whole phrase
      against a single line — pass SPACE-SEPARATED SYMBOLS instead"*, and show what the symbol-split
      form would have found. ⚠ Warn, do not silently re-split: a caller who MEANT an exact phrase
      must still be able to ask for one.
- [ ] **Make `0 hits` across ALL files say so loudly**, since that is the outcome that gets
      misread as clearance.
- [ ] ⛔ Fault-test it: a query that SHOULD hit (`TRAIN_CATCHUP_GAP`) must hit, and a query that
      should not must stay quiet — the same two-sided bar every gate here meets.
⚠ The docstring's own USAGE text should show the symbol form FIRST; the marker's phrasing
("run `precheck_prior_art.py` anyway") invites the sentence form.

---

### 🔜 `#24-countermsg2` — "Nearest **reachable** counters:" is printed over a list containing UNREACHABLE entries (filed 2026-09-11)

⛔⛔ **READ THIS BEFORE RE-FILING THE BIGGER BUG. I FILED IT AND IT DOES NOT EXIST.**
On 2026-09-11 I read this line out of batch `20260910-234959`:
> *"Juan: 12 losses … Need one of: Dragon. Nearest reachable counters: **Bagon (Dragon)** on Meteor
> Falls (B1F) 2R (tile unmapped, NOT HUNTABLE, L25-35, 25% rate) — UNREACHABLE…"*

— and filed it as *"`counter_plan` recommends HM-gated grounds it cannot reach, and the Juan
suggestion is CIRCULAR because badge 8 IS Juan."* **The circularity is real** (Waterfall is gated on
`FLAG_BADGE08_GET`, decomp `src/field_control_avatar.c:455`, which I read myself; Bagon is in
`B1F_2R` only). ‼ **But the bot never ACTED on it, so there is no behavioural defect:**
- `counter_plan.py:435` — `best_huntable`, *"the ONLY function an executor should use to pick where
  to go. Reading `cands[0]` instead is the bug this exists to prevent"* — returns a candidate only
  when `huntable AND hunt_tile is not None`.
- `counter_plan.py:345` — `huntable = bool(reachable and hunt_tile is not None)`.
- Meteor Falls is `PENDING_GRASS` with **`tile=None`**, so it is unhuntable by construction, and the
  log printed **both** markers (`NOT HUNTABLE`, `UNREACHABLE`) exactly as designed.
⇒ the candidate list is a **DIAGNOSIS**, not a plan. `AREA_PREREQ` already handles this class
(`training_areas.py:246`; its own comment records the identical Numel/FIERY_PATH circularity for
Wattson). **Nothing is broken. Do not "fix" the ranking.**

**WHAT IS ACTUALLY WRONG — one sentence, one file:**
- [ ] `plugins/custom_modes/story_mode.py:1094` builds
      `base_msg += " Nearest reachable counters: " + summary` — but `summarise_candidates`
      (`counter_plan.py:457`) emits `— UNREACHABLE` per entry. **The prefix contradicts its own
      list.** Say *"Nearest counters (reachability marked per entry):"*, or filter to reachable ones
      before printing. ⚠ Keep printing the unreachable ones somewhere — they are the diagnosis that
      explains an honest stop; the fix is the LABEL, not the content.
⭐ **MEASURED COST OF THIS LABEL: one phantom punch-list item (this one), filed and retracted the
same hour.** `counter_plan.py:477` already records a 2026-09-07 incident of the same shape — *"I read
‘Need Rock/Ice/Dragon … Slugma (Fire)’ off a live log and reported the recommender as broken. It was
correct… The line, not the logic, was the defect."* ⇒ **that is TWICE. The log line is the defect
surface; fix the label.**

---

### 🔜 `#24-egpc-leg4gap` — the LAST instance of the leg-4 guard class: the Ever Grande Poké Center (filed 2026-09-10)

**FOUND BY THE TIER 1 REVIEW OF THE FIX FOR THE SAME CLASS — not by the fix.** Gate #52 closed the
League interior; `EVER_GRANDE_CITY_POKEMON_CENTER_1F`/`_2F` still have **both** leg-4 guards False for
the identical reason (own map ⇒ `_on_map(EG)` fails ⇒ the `y <= 55` arm never runs). Standing there the
crossing is unambiguously DONE, so the honest answer is True. ⚠ **PRE-EXISTING, not worsened** — left
because widening the predicate *after* the review that cleared it ships an unreviewed change.
⛔ Gate #52's **C6 asserts the current `False` WITHOUT endorsing it** (it pins the
`startswith("EVER_GRANDE_CITY_")` trap). Read the probe's C6 note first, or closing this reintroduces
the prefix bug.
- [ ] Decide if `at_ever_grande_top()` means *"past the crossing"* (⇒ both PC maps) or *"plateau or
      League"*; then re-point C6 and add a PC case.

---

### 🔜 `#24-barecitationblindspot` — `audit_doc_citations.py` cannot see a BARE `:LINE` citation (filed 2026-09-10)

**FOUND BY A TIER 1 RE-REVIEW, not by the gate.** It matches `identifier` + `file.py:LINE`, so the FULL
citation form resolves and drift is caught. Elide the filename — natural when the file was named a
clause earlier — and the token carries no `file.py`, so the gate never looks. It reported **"all
definition-citations resolve"** over a `_should_catch` line number that was wrong. ⇒ **a stale line
hides in the SHORTER citation form, which is the form a careful writer prefers.**
‼ **AND THIS ITEM CANNOT SPELL ITS OWN EXAMPLE** — writing the bad citation literally made the gate
flag THIS FILE. The fix must tell a citation from a QUOTATION of one.
- [ ] Resolve a bare line token against the symbol named beside it. ⚠ **FAULT-TEST BOTH WAYS** — never
      on ranges, dates, or `07`/`08` history preserving an old figure as evidence. ⛔ A gate with false
      positives teaches the reader to bypass it.

---

### 🔜 `#24-dexcatch-battlebail` — a catch battle NEVER fights back, and the fence just exported it to L30-45 routes (filed 2026-09-10)

**FOUND WHILE BUILDING `#24-dexhunt`'s FENCE, verified in code, NOT shipped with it.**
`CatchStrategy.decide_turn` (`catch.py:41-62`) only ever throws a ball or applies a status move —
**never a damaging move** — and `should_flee_after_faint` returns **False unconditionally**
(`catch.py:38-39`), which removes the base strategy's *"party can't battle → flee"* escape. So the
wild attacks for free and the bot does not leave until the balls run out.

⚠ **WHY THIS IS NEW RATHER THAN PRE-EXISTING:** pre-gym-1 it was bounded by L3-6 wilds and a party
of ≤4. The fence runs at party 6 on post-badge routes, where the corpus puts the bot on ROUTE 119
and MOSSDEEP against **L30-45** wilds.

✅ **WHAT THE FENCE ALREADY DOES:** it bounds ENTRY — `party_healthy` in `decide_dex_catch` refuses
unless every battler is at full HP. A pure predicate can do that much.
⛔ **WHAT IT CANNOT DO:** bound MID-BATTLE degradation. Six mons can still faint one at a time.

⛔⛔ **DO NOT FIX IT BY EDITING `StoryCatchStrategy`.** `StoryShinyCatchStrategy` **INHERITS** from
it, and the shiny rule is an explicit user directive (2026-07-22): *attempt until success, whiteout,
or out of balls*. A bail-out there would silently overrule a user directive.
⇒ **The shape that survives: a dex-ONLY subclass** (`StoryDexCatchStrategy`) returned by the fence's
call site, which abandons the catch on a faint threshold. Pre-gym-1 and shiny paths stay
byte-identical.
‼ It is **battle-strategy internals**, which is where this project's index-space bugs live
(`KI-18`/`KI-34`/`KI-66`/`KI-95`) — build it with a probe first, not a drive.

---

### `#24-dexhunt` (original 2026-07-29 proposal) — 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-08, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ NOT A LIVE ITEM — it is the ORIGINAL proposal, kept for its rationale, which now
  lives in the archive under its 2026-09-08 banner. **The LIVE `#24-dexhunt` is the re-affirmed and widened section ABOVE this one** — act from that, not from this pointer.

### 🔶 `#25-organicplay` — **USER DIRECTION 2026-09-24: THE BOT SHOULD PLAY LIKE A PERSON.** NOT SCHEDULED; the user asked for a DISCUSSION first and explicitly asked not to derail §Ch24. Recorded so it survives the session.
  **The ask:** catch organically (battle / HM slave / training / **dex completion**) with **no 4-mon cap**; **use the PC** to swap mōn in and out; and **two dex modes** — opportunistic during the story, **completion-focused post-Elite-Four** while still training. **Observed:** story runs well, but catching stops at 4 party members (~Rustboro) and the PC is never used.
  ✅ **THE USER'S DIAGNOSIS IS CORRECT AND THE CAUSE IS ALREADY ON FILE — see `#24-catchcap` below:** `_catch_team_target = 4` (`story_mode.py:845`) is a **PARTY-SIZE** target, not a catch count, and `:960` gates on `len(party) >= target` where **party includes the starter** ⇒ starter + 3 catches. Fix already specified in `21-TEAM-POLICY-DESIGN.md` §1.
  ✅ **THE DEX MACHINERY EXISTS:** `#24-dexhunt`'s catching fence is **built, pure and gated (#50)** — ⛔ do not rebuild — **but its A/B is UNRUN, so efficacy is unproven.** ⇒ that explains the whole observation: real machinery, behind an unraised cap, never demonstrated in a run.
  ⚠ **THE PC IS NOT REJECTED — IT IS GATED ON EVIDENCE BY THE USER'S OWN RULING:** *"PC deposit — prove it first"*, i.e. a **named-PID round trip** (deposit AND withdraw, identity by PID never slot) in a real drive. ⇒ "never seen it use the PC" is the expected consequence of an unproven capability, not a missing one.
  ⛔⛔ **AND IT COLLIDES WITH A STANDING RULING — RESOLVE BEFORE BUILDING:** `06-DECISIONS-LOG.md` (USER RULING 2026-09-18, reaffirmed 09-23) says **every team member L65-75, none benched**. Free catching grows a roster; a six-slot party pinned to a narrow band is in direct tension with *"swap in and out as needed"*. **That is a decision, not code.**
  ⇒ **WHAT IS ACTUALLY MISSING**, once the above is subtracted: (1) raise the cap — *design already written*; (2) prove the fence in motion — *A/B unrun*; (3) PC round-trip drive — *gated on the ruling above*; (4) ⛔ **the two dex MODES — no sign this exists, the genuinely new ask**; (5) ⛔ **reconcile with L65-75/no-bench — unresolved, and it blocks the rest.** ⭐ The §Ch24 Fly ladder already built is the enabler for the training half.

### `#24-catchcap` — the bot catches only THREE Pokémon (user-observed 2026-07-30, cause CONFIRMED)
**NOT SCHEDULED — bundle with `#24-dexhunt`.** The user noticed the party never fills.
**Cause, verified in code:** `self._catch_team_target = 4` (`story_mode.py:845`) is a
**PARTY-SIZE** target, not a catch count, and the gate is
`if len(party) >= self._catch_team_target: return False` (`:960`) where `party` **includes the
starter**. So the bot stops at starter + 3 catches. Exactly the 3 observed.
**Fix already specified** in `21-TEAM-POLICY-DESIGN.md` §1: *"Drop the `BADGE01_GET` gate. Raise
`_catch_team_target` 4 → 6, allow overflow to the box."* One constant plus one gate — but see
`#24-dexhunt`'s HARD DEPENDENCIES (ball economy, PC/party management, menu-wedge exposure)
before shipping it, or the bot will starve on Poké Balls and clog its party with dead weight.

### `#24-menutext` — text-detection fallback for a refused party-menu selection (user proposal 2026-07-30)
**NOT SCHEDULED — deliberately deferred so KI-34 can be validated alone.**
Read `gDisplayedStringBattle` for the game's "already in battle" refusal and pick a different
mon. Sound, and there is precedent: `handle_battle._move_learn_text_showing()` already does
text-driven detection *because the internal task state is flaky*. It is also **strictly more
general** than the KI-34 index fix — it would catch ANY refusal reason (already-active, fainted,
egg), not just the on-field one.
‼ **The exact string MUST be read from the pokeemerald decomp, never recalled** — this project
does not write game facts from memory.
‼ **Why NOT now:** shipping it alongside the KI-34 index fix would make it impossible to tell
which one fixed double battles. Run the index fix alone; if `[FAINT-CHOOSER] … GAVE UP` lines
persist, this earns its place with evidence.

### ‼ A USER ASSUMPTION THE DATA REFUTES — do not build on it
The user proposed: *"in a double battle, the first 2 pokemon slots in the party are Battle slot
1 and Battle slot 2, slots 3-4 are benched."* True at the START of a double battle, **false by
the time the after-faint chooser runs** — which is the only time it matters.
Measured across **4,116 double-battle samples** in bundle `20260730-062818`:

| on-field pair (party-order) | count |
|---|---|
| `[2, 4]` | **3,975** |
| `[0, 1]` | 76 (**1.8%**) |
| `[1, 2]` / `[0, 2]` / `[1, 3]` / `[0, 3]` / `[1, 4]` / `[2, 3]` / `[1, 5]` / `[2, 5]` | 65 combined |

A replacement **keeps its own party slot** — the game tracks which party index occupies each
battler position rather than reordering the party. Hardcoding "slots 0-1 are active" would
recreate the KI-34 bug in a new place: inferring an index relationship instead of reading it.
Always read it via `BattleState.map_battle_party_index()` / `gBattlerPartyIndexes`.

### 🔶 `#24-maintain` — MAINTAIN, not cram — **⚖ TWO A/Bs DONE 2026-09-12. The first measured it NET-HARMFUL (406 run deaths); the cause was fixed (gate #57) and the second VINDICATED the fix — death family **406 → 0**, run duration **5.35 → 38.02 min** (control 34.34), badges/run **0.72 → 2.055** (control 2.030), with the fail-soft path SEEN abandoning 77 errands in production. ⚖ The feature measures **NEUTRAL** — indistinguishable from the control on every outcome metric — while ELEVATING two residual failure modes (heal-nav 15 vs 3; ROUTE111 74 vs 36). ‼‼ **I RECOMMENDED OFF AND WAS OVERRULED: the USER RULED 2026-09-12 to ENABLE it.** ✅ **PROMOTED TO `custom-pokebot` 2026-09-12** (user-authorised; all 4 files TOGETHER; rollback `pre-promote-2026-09-12`) and VERIFIED BY DRIVING — `--driver maintain --build custom` → `ACCEPTANCE: PASS`, `arm=ON` with no env var set, `dormant=False`, L13→L14, lead restored, crash scan 0. ✅ **SLOT-0 GUARD DRIVEN 2026-09-12** (`--driver rotzero`: `unguarded` reproduced the PID swap A735D162↔550A9BE6; `guarded` read the guard from the PRODUCTION source and suppressed it; fault-tested — removing the guard makes the arm FAIL). ✅ **HEAL FAIL-SOFT ALSO DRIVEN 2026-09-12** (`POKEBOT_HEALWALK_FAULT`: `blocked` → abandon + `failure=None`; `nohandler` → `failure=BotModeError`, run DIES — both PASS). It needed `POKEBOT_STAGE_HP` first: the driver reaches ZERO heals unaided. ⛔ STILL UNPROVEN: that `decide_maintenance` ever SELECTS slot 0 in a real run. ⛔ AND THE RESIDUAL 19-vs-9 HEAL DERAILS ARE UNEXPLAINED BY THIS — 18 of 19 fire OUTSIDE the errand. Both prerequisites landed FIRST (heal-nav fixed; ROUTE111 bounded at max 1/run, non-fatal). ⛔ DO-NOT-REOPEN the value question — `06-DECISIONS-LOG.md` 2026-09-12 (user ruling). The late-game half stays DEAD.** (user proposal 2026-07-29)
✅ **A/B RAN 2026-09-11** (same fixture/frames/pinned target, separate profiles). ARM-ON:
`start Marill pid=6A767BDA L13->L14 on ROUTE117(31,16) est=7165`, `rotation=landed`. ARM-OFF:
`dormant`. **P1, P2 (the vacuity conjunct) and P6 PASS; P3/P4/P5 UNTESTED — ⛔ UNTESTED IS NOT PASS.**
P3 is ungradeable HERE: Wattson's `cfg["grass"]` and `best_training_grass(13)` are the SAME pair, so
the log line fits a boss-keyed implementation too. Evidence: `evidence/2026-09-11-maintain-ARM-*.log`.
- [x] **SAFETY BATCH PASSED 2026-09-12 14:45** (ARM-ON `x4-runs/20260912-104105`, ARM-OFF `x4-runs/20260912-124117`; both SINGLE BUILD `bda41d45`). Bar was **ON ≤ OFF on run-enders**: **68.6% vs 69.5% — MET**. Run duration 37.71 vs 34.55 min; pointless 8-ride-out retries 15/3 → **0/0**; ROUTE111 failures **74 → 1** (the errand’s blocklist is SHARED with the prep path and now PROTECTS it). ⚠ badges/run 1.922 vs 2.067 (still no benefit); heal-nav derails 19 vs 9. ⛔⛔ **THE HEAL FAIL-SOFT PATH FIRED ZERO TIMES** — 18 of 19 heal derails are OUTSIDE the errand; gate #57 proves its SHAPE, production has never executed it. ⚠ Prediction MISS recorded: pre-registered “15 → ~3”, got 19. Details: `07-CHANGELOG.md` 2026-09-12 (14:45).
- [x] **THE VALUE QUESTION — ASKED TWICE, ANSWERED “NO” BOTH TIMES (2026-09-12).** The SECOND batch (32×120/arm, ARM-ON `x4-runs/20260912-050244`, ARM-OFF `x4-runs/20260912-070254`) confirmed the FIX completely — all three pre-registered predictions pass — and then found the feature NEUTRAL: badges/run **2.055 vs 2.030**, derail rate **64.8% vs 68.0%** ⚠ *(ARM-ON's `MANIFEST.txt` flags a **MIXED BUILD** — docs were committed mid-run. The numbers survive: 0 `.py` differ between those commits, ARM-OFF was a single build, and a build-matched subset gives 0.800 vs 0.826/run against 0.813 for the whole arm — but never quote them bare. See `08-MISTAKES.md` 2026-09-12.)* ⛔ At n≈91 runs/arm that cannot separate it from neutral, which is NOT “useless”. ⇒ **Settle “how much better must it be to be worth ON?” BEFORE another machine-night** — if the answer is a few percent, no sample size justifies it. Details: `07-CHANGELOG.md` / `06-DECISIONS-LOG.md` 2026-09-12 09:03.
- [x] **(superseded, kept for the record) THE FIRST BATCH, 2026-09-12, ANSWERED “NO”.** 32 lanes × 310 min per
      arm (`x4-runs/20260911-175201` ARM-ON vs `x4-runs/20260911-230219` ARM-OFF; arms verified
      separated — 901 starts/0 dormant vs 0 starts/2,644 dormant; commit delta docs-only).
      **Median run duration 5.35 min ON vs 35.18 min OFF (wall-clock, n=520/211); badges won per run 0.72 vs 2.25** — ARM-OFF won **547 badges from 243 runs**, ARM-ON only **398 from 552**. ⭐ Every tier is lower in ARM-ON in ABSOLUTE terms despite 2.3× the runs (Stone 171 vs 239 … Rain 3 vs 8).
      ⚠ An earlier draft quoted “badge 7: 0.9% vs 3.7%” — a Ch18-only STEP line with **n=14**. Superseded by badges/run (**n=945**); same direction, far better powered. ARM-ON-only
      run-enders: ROUTE102 ×319, ROUTE117 ×40, ROUTE103 ×27, ROUTE101 ×20.
      ⛔⛔ **AND THE METRIC THIS ITEM NAMED IS CONFOUNDED — DO NOT REUSE IT.** “badge-moment level
      GAPS” made the HARMFUL arm look better (380 episodes vs 402, median first gap 7 vs 8) purely
      because ARM-ON runs died before they could accumulate gap (0.69 episodes/run vs 1.65).
      ⇒ the next A/B compares **median run length and badge rate**, not per-batch episode counts.
      Cause + fix + gate #57: `07-CHANGELOG.md` 2026-09-12. Ruling: `06-DECISIONS-LOG.md` 2026-09-12.
- [ ] P3 needs the `bossground` falsifier BUILT (it never was) **and** a boss whose `cfg["grass"]`
      differs from `best_training_grass(laggard_level)`; on Wattson they coincide.
- [ ] P4/P5 need an over-budget laggard staged (`POKEBOT_MULE_LEVEL` far below `catchup`).
✅ **BUILT 2026-09-11 (sandbox only, UNPROMOTED):** `decide_maintenance` (a PURE predicate beside
`decide_dex_catch`) + `_maintain_lagging_battler`, called from ONE seam — the top of
`_prepare_for_fight`, before the sufficiency gate that can `return` early. It lifts any battler
the exclusion is about to abandon up to `catchup` (= `target - TRAIN_CATCHUP_GAP`), on a ground
keyed to **its own** level. Gate **#55 `probe_maintenance_decision.py`**: 13 cases, 3 fault arms.
⛔⛔ **WHAT IS *NOT* PROVEN, AND THE HEADLINE SAYS SO ON PURPOSE: the GENERATOR HAS NEVER RUN.**
Gate #55 proves the DECISION. The ACTION — `_rotate_lead_safely` → `train_team(scope="lead")` →
`_lead_strongest_battler` on BOTH the success and failure paths, with `train_team` under a HARD frame cap (`_yield_bounded`) — has not executed a single frame. *(This read "in a `finally`" until 2026-09-11; that shape was a latent `RuntimeError` and gate #56 now forbids it.)* ‼ This project's own
rule 7: **a candidate is not an attempt**, and a decision is not an action.
- [ ] **NEXT: drive it.** `--inject-hmmule` already stages exactly the laggard this needs
      (Marill L13 ADDED to a ready party; `POKEBOT_MULE_LEVEL` tunes it). The A/B is
      **ARM-ON `POKEBOT_MAINTAIN=1`** vs **ARM-OFF: `POKEBOT_MAINTAIN` unset** ⚠ *(this read “the shipped default” until 2026-09-12; unset now means **ON** — a future arm must pass `POKEBOT_MAINTAIN=0` explicitly)* (was the shipped
      default), graded on the mule's level BY PID — resolved from `nickname == "MULE"`, which
      `--inject-hmmule` already sets, and compared WITHIN one arm (the PID is drawn from an
      unseeded RNG per run, so it must never be compared ACROSS arms).
      ⛔ **`POKEBOT_MAINTAIN_FAULT=off` NO LONGER EXISTS** — the fault flag knows only
      `nobudget`. Running this item as it read until 2026-09-11 gives **dormant-vs-dormant**,
      i.e. a vacuous A/B that would read as a REFUTATION of a true finding.
      ⛔ Compute the discriminator on the fixture FIRST and show the arms differ — a handed-off
      spec in this project once named a fixture that made its own A/B vacuous.
- [ ] Grade prediction **P6** (the boss is handed a STRONG lead, not the laggard) — it is a
      generator property and gate #55 explicitly does NOT cover it.
✅ **PROMOTED 2026-09-11 (user-authorised), BUT SHIPPED DORMANT.** ⚠ **STILL TRUE OF `custom-pokebot` ONLY — SANDBOX FLIPPED TO **ON** 2026-09-12 (user ruling); custom is UNPROMOTED and still defaults OFF.** `POKEBOT_MAINTAIN` defaults
OFF, so custom carries this as LATENT CODE, not behaviour — which is how the urgent gate-#56
crash fix in the same file could ship without waiting for this drive. Verified by driving
220,000 frames `--build custom` (exit 0, crash scan 0); the promoted `[MAINTAIN] dormant` log
line proves the code was REACHED, not merely loaded. Rollback `pre-promote-2026-09-11b`.
⛔ *(SUPERSEDED 2026-09-12 — the drive AND two A/Bs passed, and the USER RULED to enable it; sandbox now defaults ON. This sentence read “Do NOT flip `POKEBOT_MAINTAIN` on until the drive below passes” and is kept as the record of the bar that was set.)* The flip was made in its own
reviewable change — never as a side effect of another edit.
⛔⛔ **CORRECTED 2026-09-11 — THE “PREMISE IS DEAD” HEADLINE I PUT HERE ON 2026-09-10 WAS TOO BROAD.** Dead: using a level-matched ground to CLOSE a 30-level gap late — no such ground exists above L28, and the L33-40 ones cannot be WON at (**69 battles, 0/43 HP, still L13**). **ALIVE, and now the `➡➡➡` NEXT ACTION:** maintaining so the gap never opens. That happens while the mon is **L8-28**, which the CURRENT table already covers (L13→ROUTE117, L20→ROUTE111, L25→ROUTE115). ⇒ buildable today with NO new map data.
**NOT SCHEDULED.** ⛔⛔ **AND THE RELOCATE-TO-A-MATCHED-GROUND SHAPE CANNOT WORK — not for want of searching, but by the GAME's design.** Measured against the decomp: every `MAP_ROUTE*` land table tops out at **L28** (ROUTE121/ROUTE123 joint-highest; ROUTE121 is already in `TRAINING_GRASS`), and **no land table anywhere in Hoenn has a max level of 34, 35, 37, 41, 43, 46, 47, 48 or 49** — so §Ch23's `TRAIN_TARGET = 47` has no ground at its level in the entire game. Every L30+ ground is a cave, a dungeon, the Safari Zone (ZERO EXP — `BATTLE_TYPE_SAFARI`) or Victory Road.
⇒ ⭐ **THE SURVIVING SHAPE IS “TRAIN IN THE DUNGEON YOU ARE ALREADY CLEARING”**, which §Ch23's own note already prefers (Victory Road B1F, *950.8 EXP/battle vs 1F's 775.6*) — never a `best_training_grass` pick from across Hoenn. Candidates + blockers are staged in `PENDING_GRASS`; the full proof is a header block in `training_areas.py` and `07-CHANGELOG.md` 2026-09-10.

**The proposal.** The bot should level its Pokémon "logically and organically" — keep the team
growing together, rather than only grinding to a floor immediately before a boss.

**‼ This is not a new idea — it is the unbuilt half of the 2026-07-21 directive.**
`modules/story/training_areas.py`'s own module docstring records it verbatim:
> *"USER DIRECTIVE (2026-07-21, Option 1): to train an under-levelled team member EFFICIENTLY,
> send it to a grass area whose wild Pokémon are around its own level, so it wins WINNABLE
> fights for FULL XP — rather than swap-training (half XP) everywhere."*
> *"STATUS: data + query helper only. NOT yet wired into `train_team` — punch-list #24-trainmap."*
`best_training_grass(mon_level)` is already **per-mon** — exactly the maintenance primitive —
and it has never been called.

**The measured symptom it would cure** (all from real logs):
- **35% of badge moments** carry ≥1 mon **15+ levels** below the team max; up to five at once.
- A **Makuhita went L8 → L9 across FIVE badges** while the team went L22 → L42 — and Makuhita
  is a Fighting type, i.e. Norman's counter, sitting in the party unusable.
- A completed run finished carrying **Shedinja L21 beside Blaziken L44**.
The starter takes nearly all the XP; the bench rots. Current training is target-driven and
reactive ("cram to a floor before this boss"), which is the opposite of maintenance.

**Why level-matched maintenance is efficient, not just tidy.** The calibrated model is
`xp/battle = 50.2 × wild_level / 7` — XP depends ONLY on the defeated wild's level, never on
the trainee's. So a low mon in a high-level area earns full XP per KO **but cannot win**, while
swap-training pays **half**. Sending each under-levelled mon to *its own* level-matched area to
win fights outright is strictly better than both. That is precisely what the 2026-07-21
directive asked for.

**‼ IT CONFLICTS WITH `team_policy`, AND THAT TENSION IS THE INTERESTING PART.**
`team_policy.dead_weight()` (built 2026-07-29) says *box* anything >8 levels behind, on the
grounds that `_prepare_for_fight` stops catching a mon up at `TRAIN_CATCHUP_GAP = 6` so it is
"unrecoverable by construction". **Maintenance would make that premise false** — a mon is only
unrecoverable because nothing ever levels it. Likely resolution: maintenance is the CURE,
boxing is for the genuinely hopeless (a L3 Zigzagoon caught at the wrong moment). If
maintenance works, the 35% dead-weight rate should fall — which is a **measurable success
criterion**, and the honest way to test the pair against each other.

**Interacts with `#24-dexhunt` above:** hunting for new species generates exactly the
level-matched encounters maintenance needs. Done together they are one activity, not two.

### 🔶 `#24-orphans` — **MIXED — NOT CLOSED: 4 of 6 done, 2 LIVE HALVES HOISTED BELOW.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-11, R3 budget; nothing deleted, nothing edited).
⛔ **THE TWO LIVE HALVES ARE RESTATED HERE ON PURPOSE, NOT POINTED AT.** This block was the SOLE
OWNER of both, and an archived block takes its open facts with it — that is exactly how
`#24-e4moveset` went missing earlier today. The closed four ((2) KI-65, (4) log collision,
(5) `compare_runs` A/B axis, (6) the KI-76 shelving) are in the archive; ⛔ do not redo them.
- [~] **(1) `withdraw_from_box`'s VERDICT — the REACTION POLICY is still open.** Production can now
      READ the verdict (instrumentation shipped 2026-08-17: returned, BOUND, reported, gated,
      two-armed A/B); **it still does not ACT on it.** ⚠ Blocked on an UNMEASURED heap offset, and
      the choice of reaction **needs the USER**. ⚠ The measurement itself is ESTABLISHED, not
      novel — `pc_interaction.py:135-182` already reads that same struct at
      `+0xC74`/`+0x6FA`/`+0x20A0`, and `menu_parsers.py:357` is the pattern for comparing **ROM
      bytes against the live buffer** (⛔ never hardcode English text).
      ‼‼ **TWO PREREQUISITE BUGS ARE OPEN ON THEIR OWN MERITS — restored here 2026-09-11 because they
      existed ONLY inside the archived block and a Tier 1 reviewer caught the loss. They do NOT wait
      on the heap offset or on the user:**
      - [ ] **P1 ⛔ `withdraw_from_box` (`pc_trip.py:481-482`, gate at `:489`) counts `alive`
            EXCLUDING EGGS — a live latent bug.** On **5 mons + 1 egg** the make-room block is
            SKIPPED and `pc_interaction.py:418` then raises. ‼ **A retry over this ping-pongs
            forever.**
      - [ ] **P3 ⛔ the capacity guard uses the WRONG QUANTITY** — `pc_interaction.py:418` tests
            `get_party_size()` (**B**) while the game uses **A**; `pokemon_party.py:184-193` is the
            authority saying capacity questions must use A. With a **HOLE** (A=6, B=5 — already
            OBSERVED 30x in `boxcounter2`) the bot proceeds and the GAME refuses.
      - [ ] **P2 ⛔ `interact_with_pc` has UNBOUNDED `while … press A` loops — FOUR sites, not one**:
            `pc_interaction.py:424-433` plus **`:466-492`, `:332-344`, `:363-376`**. Per decomp,
            `Task_WithdrawMon` on a full party sets `state = 1` and **never reaches the state 4 that
            loop waits for**; wrapping a retry around an unbounded wait MULTIPLIES a hang.
            *(Loop behaviour under repeated A is decomp INFERENCE, not observed — but "no bound + a
            state that may never arrive" is enough to bound it first.)*
      ⛔⛔ **AND ONE POLICY QUESTION THAT IS THE USER'S, NOT AN AGENT'S — restored live 2026-09-11;
      `06-DECISIONS-LOG.md` was grepped first (rule 11) and carries NO ruling on it, so it is
      genuinely open:** when only ALLY mons are alive, ARM B's correct behaviour is *"ride out the
      loss"* — but that contradicts `ally_party_indices`'s own documented fail-closed rationale
      (`default.py:31-34`, which fails closed to an empty set precisely to avoid pushing the caller
      into the full-party fallback). **Deliberately losing a battle is a behaviour choice**, so it
      needs a ruling before anything is built on it.
      ‼ The `IndexError`-on-turn-1 sub-claim is **REFUTED (2026-08-12), not pending** — do not
      re-check it. *(P4 is ✅ FIXED AND PROMOTED 2026-08-16, KI-81 — do not redo.)*
- [~] **(3) `KI-66` — the OWNER-FILTER half is still open.** The `_on_field` half is FIXED AND
      PROMOTED; the owner-filter half is not built.
      ‼‼ **AND THE HAZARD IS BROADER THAN THE FAINT CHOOSER — restored here 2026-09-11, it existed
      ONLY in the archived block:** **FOUR more full-party scans are unguarded, one feeding an
      UNBOUNDED `while … press A`** — `battle_handler.py:541-545`, `:588-598`, `:630-636`, and
      `_util.py:522-587`. OPEN and code-verified, never live-run. ⚠ The choke point
      `ally_party_indices()` already EXISTS (`battle_strategies/default.py:12`) and is called
      from `default.py:189` / `level_up.py:53` / `story_mode.py:171` — and from **NONE** of the
      four sites above. ⇒ they have a single natural fix site, already written.
      - [ ] Guard the four scans; bound the `press A` loop (this project never ships an unbounded one).
      ⚠ **Whoever builds it: `handle_fainted_pokemon` has shipped THREE index-space bugs
      (KI-18/34/66), so measure the direction of any coordinate conversion BEFORE applying it**
      (SESSION DISCIPLINE rule 10) — an OBSERVE-ONLY probe printing both coordinate spaces beside an
      independently-derived ground truth, then the edit.
      ⛔ And heed KI-66's own refuted headline: **a CANDIDATE IS NOT AN ATTEMPT.** An A/B that fixes
      only the owner filter showed NO DIFFERENCE on the one fixture and could make things WORSE (it
      empties `alive_slots` and trips a FALSE "no eligible replacement"). It needs its OWN
      discriminator.
      - 📦 *History, not live work: a fourth bug in that same function was filed as
        `#24-faintchooser-fourthspace` and CLOSED 2026-08-17 (archived 2026-08-22). ⛔ Do not reopen
        it. It is named here only so the count "three shipped" above is not read as the whole story.*
⭐ The reusable lesson, kept out of the archive because it is still true: *for every "still open /
still owed / not built" sentence you write, ask whether a future session would ever FIND it.* Four
of these six were live residuals recorded inside a document half marked DONE or ARCHIVED.


### ✅✅ `#24-sanitycheck` — the 5-PASS DEEP AUDIT — **COMPLETE (5/5). ⛔ DO NOT RE-RUN ANY PASS.** 📦 Full record in `28-HANDOFF-ARCHIVE.md`; ⭐ **its reusable METHOD was hoisted 2026-09-10 to `14-AGENT-PLAYBOOK.md` §0a** — a closed item is not where a technique should live.

### ‼ `#24-ki76correctness` — KI-76's CORRECTNESS half: the slide model's ENDPOINT is wrong (filed 2026-08-17 from `#24-orphans` (6), which existed because this had NO item of its own)

- [ ] **TWO OPEN DEFECTS IN `map_path.py`, and they have OPPOSITE arming profiles — ⛔ do not treat
      them as one issue, which is exactly what KI-76's own header did until this measurement.**
      **(A) THE DISMOUNT DEFECT** — `map_path.py:340-344` ends a slide on the LAST WATER TILE; the
      game moves the player ONTO the walkable land tile ahead and DISMOUNTS
      (`COLLISION_STOP_SURFING`). ⇒ wrong tile AND wrong movement mode; every planned step after it
      is wrong.
      **(B) THE ENDS-ON-A-WARP DEFECT** — `map_path.py:972` charges the 1,000,000 warp penalty
      against the NEIGHBOUR, and `:1013` only afterwards substitutes the slide DESTINATION. So a
      slide that ends on a warp is never penalised and never marked `is_warp`. ‼ And A* is *biased
      toward* long slides (~9x cheaper than walking under `avoid_encounters`), i.e. toward exactly
      the moves that spring it.
      ⛔⛔ **STOP — THE ONLY FIXTURE THIS ITEM HAS CANNOT TEST ITS ONLY LIVE DEFECT (found 2026-08-22,
      PASS 5). READ THIS BEFORE PLANNING AN A/B.** The pinned save is `post_dive_ki76.ss1` and
      `--driver ki76warp` stages in **SEAFLOOR_CAVERN_ROOM6** — and this item's OWN table below says
      ROOM6 has **ZERO** armed DISMOUNT chains. ⇒ a dismount A/B on that fixture runs **both arms
      over 0 armed chains**, prints *"no difference"*, and would read as a **REFUTATION of a
      1,852-chain defect that is real.** ‼ This is precisely the `team_max 39` vacuous-arm trap the
      standing directives were written about, sitting on the queue head, and no consistency check
      can see it — the item is perfectly self-consistent and perfectly unusable.
      ➡ **BEFORE ANY DISMOUNT WORK: capture an anchor standing on ROUTE132/133/134 or
      SEAFLOOR_CAVERN_ROOM7 with Surf** (those are where the 1,852 live), pin it, and name it here.
      ✅ **ONE THING IS STARTABLE TODAY WITH ZERO INPUT:** the single `get_map_data` check of the
      Sealed Chamber DIVE entry at ROUTE134 `(60,31)` — it decides whether this item is urgent or
      merely real, and needs no fixture at all.
      ✅✅ **MEASURED 2026-08-17 — `tools/story-dev/probe_slide_endpoints.py`, evidence
      `evidence/2026-08-17-ki76-slide-endpoints-MEASURED.stdout.txt`. ⛔ DO NOT RE-DERIVE THESE.**
      ‼ **PRODUCTION IS THE ORACLE**: every count is classified on `PathTile.forced_movement_to` —
      the endpoint `map_path.py:260-350` ITSELF computes — not on a replica. (A replica was written
      first, was kicked back by an adversarial review for being blind past a map boundary, and now
      survives only to supply the break REASON and as a cross-check: it agreed with production on
      **3,763 of 4,384** chains, and all 621 disagreements are the cross-map case.)
      | | armed chains | where |
      |---|---|---|
      | **(A) dismount** | **1,852** *(lower bound, understated by ≤24)* | ROUTE133 765, ROUTE132 542, ROUTE134 501, ROOM7 44, **ROOM6 0** |
      | **(B) ends-on-warp** | **9** | **ROOM6 only — ZERO on ROUTE132/133/134** |
      ✅ **The dismount PREMISE holds with no exceptions:** all 1,852 tiles the game would dismount
      onto are elevation 3 (`ELEVATION_DEFAULT`) — checked, not assumed, because that premise is
      what the whole defect rests on.
      ✅ **AND THE SAFETY HALF'S CAP IS NOW PROVEN, not assumed:** production followed every
      cross-map chain on ONE shared 512-step budget and the cap **never fired**; nothing cycles; the
      longest chain in the ROM is **77** steps ⇒ margin **6.6x**. ⛔ `map_path.py`'s comment claimed
      "32 tiles / ~16x / ROUTE132-134 unmeasured" — all three were stale and are corrected in the
      code (comment-only, AST-proven, net-zero on line count so no `map_path.py:NNN` citation moved).
      ✅ **PROMOTED 2026-08-17, USER-APPROVED** (`modules/map_path.py`, comment-only) in the five-file
      round — bytes now identical, AST still equal, and the three refuted claims are gone from custom.
      Restore point `restore/2026-08-17-pre-promotion-all5`. *(Superseded: this cell carried a drift figure; the STATE row and `promote.py --check` are the authority.)* **(`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven).**
      ⛔ **PRIORITY, and it is NOT what the docs said.** ‼ But §Ch23/Ever Grande is a **Fly
      destination** — VERIFIED IN OUR OWN FORK, `sandbox-pokebot/modules/region_map.py:54` — so the
      currents are BYPASSABLE there, and the handoff's "the route to … Ever Grande" OVERSTATES it.
      ⚠ **The Regi arc looks like the real forcing function, but that half is NOT verified and must
      not be treated as measured:** the Sealed Chamber's DIVE entry at ROUTE134 `(60,31)` comes from
      `ai-research-notes/2026-08-13-regi-arc-decomp-ground-truth.md:67`, whose own header says
      *"Everything else is UNVERIFIED IN OUR HARNESS"*. ⇒ **Before this item's 501 ROUTE134 chains
      are called unavoidable, confirm that entry with `get_map_data`** — one call, and it decides
      whether this item is urgent or merely real. ⛔ Do not repeat the coordinate as fact until then.
      ✅✅ **STEP 1 IS DONE 2026-08-17 — THE ENDS-ON-A-WARP DEFECT IS CONFIRMED LIVE.
      ⛔ DO NOT REBUILD `--driver ki76warp`.** It staged on `(8,12)`, pressed EAST onto `(9,12)`, and
      recorded the whole slide: **exactly the nine steps production predicted, ending exactly on its predicted `(14,8)`** (⚠ the COUNT and ENDPOINT were predicted; the intermediate tiles are what the recorded tile TYPES imply, and they match), then
      `SEAFLOOR_CAVERN_ENTRANCE` — warp-arrival tile `(10,1)` at f+142, then the game's own auto-step to `(10,2)`, which is the FINAL settled tile the driver graded on — a different MAP — with **`surfing` True throughout the
      slide and False on arrival**. ⇒ a planner resting on `(14,8)` in ROOM6 is wrong on map, tile
      AND movement mode. `ACCEPTANCE: PASS`, anchor hash unchanged.
      ‼ **The acceptance grades the INSTRUMENT, not the answer** (staged AND stepped AND anchor
      intact AND landed on one of the two predicted arms) — a driver that only passes when it likes
      the result is not an experiment.
      ⚠ **Two honest limits, both recorded:** the run does NOT confirm the DISMOUNT defect in its own
      right (that one is about a slide ending beside walkable LAND; this dismount came from a WARP
      transition), and n is small — a second run is a DETERMINISM check, never a replication.
      📁 `evidence/2026-08-17-ki76warp-RUN3-CONFIRMED.stdout.txt`.
      ⛔⛔ **AND THE PLANNER-SIDE ASSERTION IS *VACUOUS* — MEASURED 2026-08-17, NOT ARGUED.**
      The obvious next step ("assert `calculate_path` PENALISES or MARKS a slide destination that is
      a warp") **cannot fail on the only map where the defect is armed.** Two observe-only queries,
      re-run by hand after a Tier 2 agent reported them (⛔ an agent's word is not enough on a
      load-bearing point): asking for a path TO `(14,8)` returns ONE waypoint,
      `coords=(10,1) is_warp=True` — the planner already resolves it THROUGH the warp and MARKS it
      (`map_path.py:869` sets `is_warp` on the final node); and the real Room 6 crossing emits 13
      waypoints, **none of them `(14,8)`**, because A* cannot expand past that tile — continuing
      needs SEAFLOOR_CAVERN_ENTRANCE, which is not on ROOM6's connected set.
      ⇒ **Both arms identical. Shipping that assertion would have printed "no difference", which
      reads as a REFUTATION of a defect that is LIVE-CONFIRMED** — the worst available outcome.
      📁 `evidence/2026-08-17-ki76-plannerside-VACUOUS.stdout.txt`.
      ‼ **A subtler finding, worth more than the assertion would have been:** on that map the
      planner is **ACCIDENTALLY SAFE — safe by INABILITY, not by design.** It avoids the warp only
      because it cannot route past it, and that protection evaporates on any map where the far side
      IS in the connected set.
      ✅✅ **VACUITY RE-CONFIRMED EXHAUSTIVELY 2026-08-17 (pass 3), and it now covers the COST
      half too.** An adversarial agent swept **all 235 legal ROOM6 tiles x 235 destinations =
      54,990 `calculate_path` calls**: `(14,8)` appears as a non-final waypoint in **0** of them.
      The structural cause is topology, not tuning — `(14,8)`'s north/east/west neighbours are
      collision walls and its south neighbour is the current that feeds it, so it is a DEAD END
      A* can only reach as an explicitly requested destination. ⛔ **Therefore a COST-based test
      is vacuous for the SAME structural reason**: there is no competing route to compare costs
      against on this ROM. ⇒ **the planner-side half is vacuous IN ITS ENTIRETY here**, not just
      its `is_warp` piece.
      ‼ It also re-scanned every map with currents through the production oracle and reproduced
      **9 D2-armed chains ROM-wide, all `(14,8)` in ROOM6, 0 elsewhere**, and found **0** D2
      endpoints anywhere in the ROM with an escape route — so the dead-end is universal for this
      data, not a ROOM6 quirk.
      ➡ **WHAT IS ACTUALLY LEFT, restated after that sweep:** nothing on this ROM discriminates.
      A real test needs a map where a slide destination is a warp AND the far side is on the
      connected set — and **no such map exists here**. ⇒ this half is BLOCKED ON REALITY, not on
      effort; treat it as such rather than hunting for a cleverer assertion. Formerly:** the COST at `map_path.py:972` is charged against the NEIGHBOUR and never against
      the substituted destination, so the planner may still PREFER a route it should avoid. That is
      a route-CHOICE comparison (does the emitted route change when the penalty is applied to the
      destination?), **not** an `is_warp` check. ⛔ Do not start it by re-deriving the vacuous one.
      ⛔ **NOT READY TO PATCH, and the reason is KI-76's own:** both fixes are changes to SHARED
      pathfinding every mode depends on (the KI-59 shape), each needs its own A/B, and KI-76
      requires **LIVE confirmation before code depends on either**. This measurement is static; it
      does NOT discharge that.
      ⛔⛔ **SUPERSEDED 2026-08-17 — THE BUILD SPEC BELOW IS HISTORY. THE DRIVER EXISTS AND HAS RUN.**
      Everything from here to the NAMING HAZARD note was the recipe for `--driver ki76warp`; it is
      kept because its measurements (the staging tile, the nine entry tiles, the unreachability of
      `(14,9)`) are still the reference. ⛔ **It is NOT a work instruction any more** — a Tier 2
      cold-start audit found this `➡ NEXT ACTION` marker commanding a driver the same item declares
      built, seventeen lines above.
      ⚠ **NAMING HAZARD:** the two defects are numbered inconsistently across three files —
      `probe_ch20_currents.py:174` calls the WARP one "KI-76 / D1", `probe_current_edges.py:1` calls
      the `None`-unpack "KI-76 / D5", and KI-76 itself calls the warp one "Defect 2". ⛔ Say
      "dismount" and "ends-on-warp"; do not mint a fourth numbering.

### ‼‼ THE BIG ONE — `#24-trainmap+` : area-aware training, party>4, PC rotation

> ⛔⛔ **BEFORE YOU TOUCH ANY BOSS `cfg["grass"]` OR `TRAINING_GRASS`, READ KI-80 (2026-08-15).**
> The handoff's (P6) framing of this — *"Norman's patch is L3-5 against a band of L27-31, and
> Winona has no patch at all"* — is **WRONG ON BOTH EXAMPLES**, and acting on it regresses the
> bot. ✅ **UPDATED 2026-08-16 — THE COUPLING IS GONE FROM BOTH FORKS (promoted).** `grass_is_fodder`
> (`story_mode.py:1899`) USED TO CO-GATE KI-23's `_boss_plan_is_hopeless`/`_counter_ladder`
> (with `boss_teaches`, inside `losses >= 2`), so giving Winona a `grass` key SKIPPED her counter
> machinery silently for any team at L30-35. **KI-80 decoupled it:** `:1901` is now
> `if boss_teaches:` and `boss_mode` sits behind its own `if grass_is_fodder:`.
> ⚠ **The warning below still stands for the OTHER two reasons**, which the decoupling does NOT
> address. ✅ The decoupling was PROMOTED 2026-08-16, so BOTH forks now have it. Norman's L3-5 patch is the DELIBERATE fodder trigger for the only relocation
> this bot has ever performed (70-83% measured). And a new `TRAINING_GRASS` row re-ranks ONE
> GLOBAL table for every caller, including the counter picker for every other boss.
> ✅ **ENFORCED, not requested:** `repro_boss_grass_gate.py` (suite #24) fails the build if an
> at-risk fight gains a `grass` key while the coupling stands. It is AST-based (a comment cannot
> trip it) and SELF-RETIRING (it stops enforcing once the ladder is decoupled).
> ✅✅ **DONE — KI-80's decoupling is BUILT, DRIVEN, REVIEWED AND PROMOTED TO BOTH FORKS
> (2026-08-16). ⛔ DO NOT REBUILD IT.** *(This line commanded it as live work after it shipped.)*
> It did NOT ship on reading alone: the KI-23 repro was driven before AND after. ⛔ **READ KI-80's CONDITION TABLE FIRST.** This line used to say
> *"at `losses >= 2` with `kos >= 1` and no type answer"* — that is **REFUTED and would build a
> VACUOUS test**: below `losses >= 6` the ladder cannot fire at all, at 12+ `hard_plateau`
> passes it for the WRONG reason, and the fixture must ALSO satisfy `team_max <= wild_max + 8`
> or `grass_is_fodder` never flips and BOTH arms take the same branch.

**User directive 2026-07-29.** The bot trains in whatever grass is next to the objective,
often below L5, so XP is near worthless — and Norman is the 5th gym but sits in the STARTING
region, where "train near the gym" is actively wrong.

‼ **The data layer ALREADY EXISTS — this is wiring + policy, not a new map.** Verified
2026-07-29 before proposing any build:
- `modules/encounter_index.py` — whole-game reverse index from the ROM's `gWildMonHeaders`:
  species → [{map, method, rate%, level range}], cached per ROM. Built for Hunt Planner (#9).
- `modules/story/training_areas.py` — verified spin tiles + wild bands,
  `best_training_area()`, `best_training_grass()`, `estimate_frames_to_level()`.
- `modules/story/counter_plan.py` — already ranks reachable, cost-priced counter encounters.

**The three concrete gaps:**
- [ ] **(1) `train_team` never picks an area.** `early_game.py:2288` —
      `grass: tuple = RUSTBORO_TRAINING_GRASS` is a caller-supplied constant; it never calls
      `best_training_area`. Its own docstring admits this. **Wire it.**
- [~] **(2) `FODDER_LEVEL_GAP = 12` compares the WRONG QUANTITIES — ANALYSED 2026-07-29,
      DELIBERATELY NOT CHANGED.** See **KI-31** for the full write-up and the measured table.
      Short version: the gate tests wild-level vs TEAM-level, but the project's own calibrated
      model says `xp/battle = 50.2 × wild_level / 7` — XP depends only on the WILD level. The
      failure window is teams **below ~L17** (because `5+12=17`); a L15 team on Route 102
      forgoes a **2.8×** speedup and never moves.
      **Blocked on two things, both real:**
      1. The conservatism is DELIBERATE — `repro_fodder_grass.py` says *"the whole point of the
         conservative gap: proven-good prep must not move"*, and L10-17 is exactly
         Roxanne/Brawly/Wattson.
      2. **That repro needs a real `mgba`** (it loads a ROM + `saves/norman_done.ss1`) and is
         one of the 5 environmental failures on the dev box. **Validate on the batch machine.**
      Proposed replacement (no new constant, no travel measurement needed): relocate when
      `estimate_frames_to_level(...local_max) − estimate_frames_to_level(...better_hi)` is a
      large win — e.g. the better area at least HALVES the grind, i.e. `better_hi ≥ 2×local_max`.
- [ ] **(3) party cap 4 → 6 + PC rotation — ALREADY DESIGNED, BUILD IT.**
      ‼ The user flagged this as "needs further discussion". **That discussion already
      happened on 2026-07-26 and is written up build-ready in `21-TEAM-POLICY-DESIGN.md`**,
      which specifies exactly what was asked for: raise `_catch_team_target` 4 → 6 with
      overflow to the box (§1), a scored catch roll behind hard floors (§1), a dead-weight
      predicate in a new pure `modules/story/team_policy.py` (§2), **rotation that piggybacks
      on heal trips and never detours for its own sake** (§4), a counter ladder that checks
      the BOX first (§5), a never-randomise safety list (§6) — including *"boxing the only
      Surf carrier soft-locks the run"*, which is the same wall P1 hit on 2026-07-29 — and a
      no-emulator test plan (§7).
      **The machinery also exists:** `modules/modes/util/pc_interaction.py` provides
      `interact_with_pc(actions)` with deposit/withdraw/move-box primitives.
      **And the game fact is already settled in our own code:** `story_mode.py:84` —
      *"even with a full party (the catch goes to the PC box, vanilla behavior)"* — a path
      the shiny-catch strategy already exercises in real runs. No probe needed.
      So this is ASSEMBLY against an existing spec, not a new design. Re-read `21` first;
      only bring the user a question `21` does not already answer.

- [x] **`#24-reprorot` — DONE 2026-07-30.** The 4 "environmental / needs mgba" repro failures were real bugs. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted). ‼ **This exact misfiling recurred on 2026-08-23** (`#24-brokenrepros`) — see `#24-reprosweepratchet` for the structural cause.
- [x] **`#24-menuorder` — DONE 2026-07-30.** Story block + ×4 controls hoisted to the TOP of the menu. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [x] **`#24-x4headless` — DONE 2026-07-31.** Headless ENDLESS-RESET batch runner. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [x] **`#24-journey` — DONE 2026-07-31. Warp planning at MAP granularity. CLOSED.**
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the design and its measurements are there.
- [x] **`#24-smashroute` — DONE 2026-07-31.** The bot clears a field-move obstacle that seals a route. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [x] ~~**‼ `#24-smashroute` — clear a ROCK SMASH obstacle that seals a journey**~~ — **SUPERSEDED / CLOSED.**
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full statement and its reasoning are there.
- [x] ~~**‼ `#24-journey` — CROSS-MAP OVERWORLD ROUTE PLANNING**~~ — **SUPERSEDED / CLOSED.** The original journey-planning item; its successor entry (also `#24-journey`, DONE 2026-07-31, warp planning at MAP granularity) remains in place above.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full original statement and KI-39 context are there.
- [~] **‼‼ `#24-menutext` — THE REAL FIX for KI-38/KI-40. NOW THE #1 ITEM (2026-07-30).**
      Runs stopped finishing entirely (48% → 0%) because the after-faint chooser cannot select
      a living replacement: measured `NO ELIGIBLE REPLACEMENT` = **0** while `GAVE UP` runs at
      **~22/hour**, i.e. a valid target always existed and was never chosen. KI-38's own
      evidence says the CURSOR MODEL is wrong (`presses={'Down': 3, 'A': 273}`,
      `cursors_seen=[0,2,3,7]` in a 4-mon party, 7 probably CANCEL) — and no number of retries
      fixes a wrong model.
      **Build:** read the party-menu TEXT so the bot knows what the cursor is actually on,
      instead of inferring it from indices. ‼ **The strings MUST come from the decomp**
      (`gh api repos/pret/pokeemerald/contents/...`), never from memory — that rule has already
      been broken once today (08-MISTAKES, the Hoenn route claim).
      ✅ **STRINGS ALREADY FETCHED AND VERIFIED 2026-07-30** from `src/strings.c` — use these,
      do not re-derive or guess:
      | symbol | text |
      |---|---|
      | `gText_SendOut` | `SEND OUT` |
      | `gText_Shift` | `SHIFT` |
      | `gText_Switch2` / `gText_Switch` | `SWITCH` |
      | `gText_Summary5` | `SUMMARY` |
      | `gText_Cancel` / `gText_Cancel2` | `CANCEL` |
      | `gText_Enter` | `ENTER` |
      | `gText_DoWhatWithPokemon` | `Do what with this {PKMN}?` — shown when the ACTION menu is open over a chosen mon |
      ✅ **INSTRUMENTATION ALREADY SHIPPED:** the `GAVE UP` log line now also records the live
      `gDisplayedStringBattle` and `gStringVar4` (tagged `[#24-menutext]`), diagnostic-only.
      **The next batch's logs should therefore SHOW what the screen said at each failure** —
      read those before writing the chooser, rather than reasoning from indices again.
      **MITIGATION (A) SHIPPED 2026-07-30:** `FAINT_CHOOSER_GIVEUP_LIMIT` 3 → 20, clamped to
      200, tunable via `POKEBOT_FAINT_GIVEUP_LIMIT` (`repro_faint_giveup_limit.py`).
      ‼ **If the finish rate recovers, that is the MITIGATION working, not this item done.**
- [x] **`#24-giveuplimit` — DONE 2026-07-30 (mitigation A for KI-38/KI-40).** See above.
      Test caught a real hole pre-ship: the env override was validated but not CLAMPED, so a
      fat-fingered value gave an effectively unbounded chooser and silently reintroduced the
      KI-36 hazard the finite limit exists to prevent.

### ‼ #1 EXECUTION PRIORITY — the counter chain is now 72% of all derails
- [x] **`#24-counters` phase 2 — ✅ BUILT 2026-07-30, and LIVE-VALIDATED many times since;  — 📦 **ARCHIVED 2026-08-23 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).

- [ ] **`#24-starter-gym3` — Gym 3 viability is decided by the starter (new, 2026-07-29).**
      P3/Treecko stalls at 2 badges in **11 of 14 runs**, and **10 of its 11 derails are
      Wattson**. P2/Mudkip never hits this: Marshtomp is Water/**Ground** — immune to Electric
      and super-effective back. Torchic/random sit between. Only Mudkip is self-sufficient at
      Wattson. This is a *consequence* of `#24-counters` phase 2, not a separate fix — but it
      is the sharpest measurement of why that item matters, and it is exactly the
      starter-specific failure the ×4 instrument was built to expose.
- [ ] **`#24-pc` / Surf resource walls (new derail classes, 2026-07-29).** Seen for the first
      time in P1: *"No party mon can learn Surf and the party is full — needs PC box
      management (#24-pc)"* ×2, and *"Cannot hunt a Surf learner: no Poké Balls and no money
      to buy any"* ×1. Resource exhaustion, not combat failure — related to
      `#24-provisions` (money/items) and `#24-partyvariety` (a full party of dead weight).

### ‼ DOCUMENTATION CORRECTNESS AUDIT — 2026-07-27
- [x] `#doc-audit-1` — **docs 00/01/02/05/14 re-verified against code.** DONE 2026-07-27.
      Biggest find: `02-ARCHITECTURE.md`'s folder map omitted **`sandbox-pokebot/`, where all work
      happens**, while its own prose cited sandbox-only modules — the doc contradicted itself.
      Retired to a summary 2026-09-03; fixes/method/calibration: `06-DECISIONS-LOG.md` 2026-07-27.
- [~] `#doc-audit-2` — **`03-PUNCH-LIST.md` status audit (THIS FILE) — PARTIAL.** The agent
      running it was killed by a weekly usage limit on 2026-07-27; redone by hand 2026-07-29
      for the CONSISTENCY half only.
      **Done:** 134 items across 98 distinct `#`-ids; the undocumented third marker `- [~]`
      (17 items) is now defined at the top of this file; exactly one id had a conflicting
      status (`#24-pokenav-faithful`) and it proved to be a legitimate recurrence, now
      cross-linked in both directions; no `- [x]` item was found whose code is missing.
      **Still open:** the expensive half — walking all **80** open items and checking each
      against `sandbox-pokebot/` for "already built". Calibration case if resumed:
      `#24-regionreach` is `[~]` and its oracle IS wired (`story_mode.py:553`/`:606`), so
      only the KI-24b hop-count nuance remains — i.e. `[~]` is correct there, and a naive
      "it's wired, mark it done" sweep would be wrong. Expect more items like that.
- [ ] `#doc-audit-3` — **`12-STORYMODE-DESIGN.md` (2,886 lines) never audited.** Check Area
      Atlas coords/flags against `modules/map_data.py` + the decomp, and promote any
      `⚠ VALIDATE LIVE` item that live runs have since validated.
- [~] `#doc-audit-4` — **`ai-research-notes/` integrity — SPOT-CHECKED 2026-07-29, not
      exhaustive.** The directory is 84 files / ~9,400 lines; a full claim-by-claim sweep was
      NOT done.
      **Checked and PASSING:** (a) `00-READ-THIS-FIRST.md` states the rule, the per-claim
      verification gates, and its own track record; (b) stub markers exist in the authoritative
      docs that matter — `12-STORYMODE-DESIGN.md:4-10` carries a proper header stub, and
      `03`/`04`/`05`/`22`/`23` all reference the directory; (c) **the one documented Gemini
      error was correctly contained** — the note claimed no healing house exists on the
      Route 112/113 corridor, `sandbox-pokebot/modules/map_data.py:1059` has
      `ROUTE111_OLD_LADYS_REST_STOP = (18, 1)`, and
      `18-RESEARCH-HEALPOINTS-AND-LEGENDARIES.md:27-31` records the claim tagged
      `(INFERENCE)` and rebuts it with our own map data. `05-KNOWN-ISSUES.md:368` holds the
      verified detail. The marker-and-rebut discipline held.
      **Still open:** no systematic check that every *other* note's claims are either
      stub-marked or verified. Highest-risk class per the 2026-07-25 measurement is Gemini's
      **architecture advice** (all three of its "your bot must hardcode an interrupt here"
      constraints rested on permanence that does not exist) — sweep the design docs
      (`19`–`23`) for actionable advice traceable to a note rather than to code.
- [ ] `#doc-policy-05` — **user ruling wanted:** should `05-KNOWN-ISSUES.md` delete an entry
      when it is fixed in `sandbox-pokebot/`, or keep it until promotion to `custom-pokebot/`?
      Currently retained-and-marked. See `06-DECISIONS-LOG.md` 2026-07-27 (provisional).

**STILL OPEN from the same review — design calls, NOT yet built (need the user's ruling):**
- [ ] `#24-leadpolicy` — **the matchup lead is purely defensive and benches the winner.**
      ⭐⭐ **RE-MEASURED 2026-09-13 ON THE CURRENT BUILD — THIS IS NOW THE #1 COST IN THE BOT.** Batch `20260913-092254` (commit `f039bffc`, single build, 42 runs): **PETALBURG CITY / Norman = 180 of 749 losses = 24.0%**, 119 W / 180 L = **60.2% loss rate**; FORTREE / Winona = **141 of 749 = 18.8%** is #2 and likely the same mechanism. ⛔ **NOT underlevelling** — median TOP mon at a loss is **L35** against a **L31 Slaking**, party 5-6 strong; but the median **LEAD is L29**. ‼ **THE FIX IS ALREADY RULED:** `06-DECISIONS-LOG.md` 2026-07-29 → **OPTIONS A + C** (the lead must ALSO have a ≥neutral attacking option; 1-HP Wonder Guard mons get a special case). ⛔ **OPTION B (level-gap weighting) WAS EXPLICITLY NOT ADOPTED — do not re-propose it, and note that “the lead is 6 levels below our best” is exactly B.** ⚠ **STATUS OF THAT RULING IS UNRESOLVED AND MUST BE ESTABLISHED FIRST:** `28-HANDOFF-ARCHIVE.md` claims *“A+C BUILT 2026-08-01”*, but `_lead_best_matchup` (`early_game.py:1822`) is still documented and implemented as *“minimizing the foe's WORST-CASE STAB multiplier … breaking ties by higher level”*, and its `min_incoming_only` parameter is **DEAD CODE — declared once, never referenced, never passed by any caller** (verified by grep across `early_game.py` and `story_mode.py`). ⇒ decide which of *(i) never shipped*, *(ii) shipped but does not cover multi-battler bosses*, *(iii) shipped and regressed* is true BEFORE writing code.
      `_lead_best_matchup` (`early_game.py:1822`) picks `min(incoming_multiplier, -level)` —
      it models only the foe ace's STAB types, and ignores whether the chosen lead can deal
      damage or survive a level gap. Verified to reproduce every observed lead exactly:
      P2 led **Whismur L15** into the Route 110 rival **13 times** while **Marshtomp L24**
      sat in slot 2 (Marshtomp is 4× weak to the Grovyle, so it is correctly excluded — but
      Whismur cannot win either). P4 led **Shedinja L20** vs Norman (Normal→Ghost = 0×, a
      genuinely clever Wonder Guard read) and lost to Slaking's **Faint Attack (Dark)**,
      which the model cannot see because it does not read movepools.
      ‼ This is NOT the old `train_team` lead-restore bug — that fix is intact and its repro
      still passes; the matchup call simply runs afterwards and overrides it.
      OPTIONS (user's call): (a) require the lead to also have a ≥neutral attacking option;
      (b) weight the level gap so a resistant chaff mon can't bench a much stronger one;
      (c) special-case 1-HP Wonder Guard mons; (d) leave as-is and fix via provisions.
- [ ] `#24-route110cap` — **the Route 110 rival gets no prep and no cap.** Unlike every other
      boss it calls neither `_prepare_for_fight` (no proactive band training, no reactive
      escalation) nor an attempt cap, so P2 burned **13 whiteouts** there in one run.
      ‼ DELIBERATELY NOT FIXED BLIND: a naive cap would have KILLED that run, which went on
      to reach Fortree after those 13 losses. Adding prep needs a Route 110 training-grass
      tile, which is a game fact that must be verified (live probe / decomp), not recalled.

- [ ] **#24 — STORY AUTO-PLAYER.** The only active work.
      ⛔⛔ **THIS BODY HAS NOW GONE STALE TWICE — it said "20 of 24" and "Seafloor Cavern driven
      through Room 3" on 2026-09-03, when §Ch20 AND §Ch21 had both shipped as wired chapters.**
      ⇒ **DO NOT RESTATE THE LADDER HERE.** The ladder count and the live head belong in
      `04-HANDOFF.md` (the 60-SECOND VERSION and NEXT ACTIONS); this entry now POINTS there,
      because a second copy of a moving number is how it goes stale a third time.
      Current order: `#24-ch22chapter` → the `04-HANDOFF.md` NEXT ACTIONS queue.
      Sub-items live in `## Story bot (#24) — open backlog` below.
- [ ] #V — Post-promotion verification sweep (PARKED behind #24): independent adversarial pass
      on the promoted features that only had builder self-verification (not
      an independent pass) — #8 global pathfinding, #12 shiny alerts, #18
      update notice, #20 cloud-sync, and the 2026-07-19 GUI polish (tabs /
      full-dex picker / XP bars / topmost dialogs). Interrupted twice by
      credit limits; run it against custom-pokebot before relying on the
      save-touching bits (cloud-sync ships off-by-default, so inert).

- [ ] #24-x4 — **ENDLESS LOOP ×4** (user request 2026-07-26): four independent
      `Story (ENDLESS RESET)` bots at once, one process + profile + starter each
      (P1 torchic / P2 mudkip / P3 treecko / P4 random), tiled 2×2 in the
      dashboard's video area, looping forever and restarting independently.
      A TEST INSTRUMENT — it exists to raise the rate of reviewable failure data
      and guarantee starter coverage.
      **Phase 1 BUILT in sandbox (2026-07-26), tests green, LIVE RUN NOT YET DONE**
      — this dev box has no `mgba`, so nothing involving a real emulator has been
      exercised. See 04-HANDOFF for the exact live confirms the user must run.
      **Phase 2a DONE 2026-07-26** — the party strip / party tab / hover tooltip
      follow the focused lane (`modules/remote_party.py` rebuilds stand-ins from the
      lane's status blob; the renderer is unchanged). Live confirm still owed.
      **#24-x4-logs DONE 2026-07-26** — `Emulator > Park x4 & Collect Logs...`
      (batch-only menu item): parks every lane, bundles all four lanes' logs into
      one verified zip under `profiles/x4 LOGS/`, archives the originals to each
      profile's `debug-logs/Old/` only AFTER the zip verifies. Added the
      parent->child command channel that phase 2b will reuse. Live confirm owed.
      Phase 2b (agreed with the user, NOT built): the watch/CONTROL toggle — click a
      tile then drive it, forwarding `press_button`/`hold_button`/`release_button`
      over a per-lane input pipe (`modules/libmgba.py` already exposes exactly that
      surface, so the channel is strings, not input-model surgery).
- [ ] #24-badges — **TRAINER-CARD / BADGE CASE overlay** (user request 2026-07-26):
      a Bag-icon button under the 6th party slot opens an overlay to the right laid
      out like the in-game badge case — 8 badges, black silhouette until earned —
      and hovering/clicking one shows that gym leader's details plus THE TEAM THAT
      BEAT THEM. User said it may be tabled; the UI is tabled, the capture is NOT.
      **DONE:** `modules/badge_log.py` records the party at the instant each
      `BADGE0N_GET` flag flips, to `<profile>/badge-log.json`, re-arming on emulator
      reset so every run of an x4 batch is captured. Shipped first because it can
      only record badges earned AFTER it is on — waiting would have thrown away
      every x4 run's badge data (06-DECISIONS-LOG).
      **UI DONE 2026-07-26** — Bag button under the 6th ball + the 2x4 badge-case
      overlay (silhouette until earned, hover/click for leader detail + the team
      that won). Leader table decomp-verified in `modules/badge_case.py`; the 8th
      leader is JUAN, not Wallace (that error shipped first — 08-MISTAKES).
      Live confirm owed. **REMAINING:** real Bag artwork (the icon is PIL-drawn;
      the repo ships none); and choosing WHICH run's team to show when a badge has
      many recorded wins — currently the latest, with a count of the rest.
- [ ] #24-badges-live — **Make the badge case LIVE, like the party strip**
      (user request 2026-07-26). Today `_badge_case_source()` already reads the
      FOCUSED x4 lane, so opening the Bag after clicking P3's tile shows P3 — but
      the contents are a SNAPSHOT taken in `open_badge_case()` and cached in
      `_badge_case_entries_cache`. Two consequences to fix:
        (a) clicking a different tile while the case is OPEN does not switch it —
            `_x4_click` refreshes the party (`_refresh_party` + `_refresh_party_strip`)
            but not the case;
        (b) it does not tick over as badges are earned during a run.
      Wanted: the case tracks focus changes and refreshes on a cadence, the way the
      party strip does off `_refresh_sidebar`.
      ‼ Design constraint that produced the snapshot in the first place: the entries
      come from `badge_log.read_log()`, i.e. a DISK READ of `badge-log.json`, and
      `_show_badge_detail` runs on every hover — a naive "just read it live" turns
      mouse movement into file I/O. Refresh on focus-change and on the KPI/sidebar
      cadence (or when the lane's published badge set changes), NOT per hover.
      Cheap seam available: lanes already publish `badges` in their status blob, so
      "has anything changed?" is answerable without touching the disk.
      Assets are NOT a blocker: all 8 Hoenn badge sprites already exist at
      `modules/web/static/sprites/badges/` (Stone, Knuckle, Dynamo, Heat, Balance,
      Feather, Mind, Rain). The only missing art is a Bag icon.

## Under discussion (user 2026-07-26, NOT agreed scope — see `19-TEAM-BUILDING-DISCUSSION.md`)
> ‼ Do NOT start these. Each has open questions that must be answered with the user first;
> the design note records them. Promote to the active list once resolved.
- [ ] #24-gymtrainers — **Battle gym/town trainers BEFORE grinding wild, at every gym.**
      Raised for Dewford (bot trains in the cave; user says it should be on "the second
      floor" AND should clear the island + gym trainers first for XP and money). Directly
      attacks the #1 failure in batch `20260726-181825`: attrition, not gym leaders (P2
      whited out 41× on Route 110 and derailed). ‼ Open: WHICH floor (Granite Cave 1F/B1F/
      B2F); always vs only-when-underlevelled; town-wide vs arc-wide trainer scope.
      **ANSWERED 2026-07-26: train on Granite Cave B1F AND B2F; fight trainers ALWAYS.**
      ‼ **ALL FACTS NOW DECOMP-VERIFIED** (see `19-TEAM-BUILDING-DISCUSSION.md` §8) and the
      spin tiles are recorded in `training_areas.py` PENDING_GRASS: **B1F (3,18) L9-11**,
      **B2F (28,17) L10-12**, neither gated by any HM/item/flag. B1F's 62 cracked-floor
      tiles are all UNREACHABLE ON FOOT (north of an unclimbable muddy slope).
      ⛔ **UNBLOCKED 2026-08-13 — the blocker below was CLOSED 2026-08-05** (`#24-cavethread`: multi-hop cave threading ALREADY WORKS, both directions, no chain table — see its [x] entry). This item is now limited by priority, not by a dependency. Superseded text: ‼ **BLOCKED ON ONE THING:** `_CAVE_EXITS` / `_CAVE_ENTRANCES` are SINGLE-HOP tables,
      and B1F/B2F are 2-3 hops deep from Route 106. Promoting them without making that
      threading chain-aware breaks the post-training HEAL — the global navigator cannot
      cross warp levels, and that exact failure already dropped two real-hardware runs to
      Manual (2026-07-22). **Next step: make cave entry/exit chain-aware, then promote,
      then validate live.** Deliberately NOT done blind — this is navigation code.
      ‼ **PRIORITY NOTE:** this spot only fires after ≥2 Brawly losses, and batch
      `20260726-201838` had 2-3 Dewford losses in the whole batch. Runs are dying at
      MAUVILLE (Wattson) and PETALBURG (Norman), not Dewford. Worth doing because the user
      asked and the data is now free, but it is not where the failures are.
- [ ] #24-partyvariety — **Fill the party and vary what is caught; PC deposit/withdraw.**
      ‼ **ROOT CAUSE FOUND (recon 2026-07-26) — it is not emergent, it is two conditions.**
      `_should_catch` (`story_mode.py:2070-2169`) requires `not BADGE01_GET` AND
      `len(party) < _catch_team_target` where **`_catch_team_target = 4`** (`:811`). So the
      bot catches FOUR mons before the Stone Badge and then never catches again for the
      rest of the run. Part 1 is nearly a one-line change.
      ‼ **PC automation ALREADY EXISTS and is unused:** `modules/pokemon_storage.py` (full
      box READ) + `modules/modes/util/pc_interaction.py` (804 lines: withdraw / deposit /
      release), whose only consumer is `daycare.py`. `#24-pc`'s "map the PC UI" is already
      done — what is missing is navigation to a PC and a keep/box POLICY. The shiny path
      already proves party-full→box works (`story_mode.py:1456-1482`).
      ‼ **CONFIRMED ONE ITEM WITH `#24-counters` PHASE 2** — the counter chain currently
      diagnoses and then RAISES `BotModeError` (`story_mode.py:1309-1313`); that raise is
      the seam where fetching would hook in, and `HM_CATCH_TARGET_DEX` (`:1485-1511`) is a
      working "catch species X on sight" primitive to reuse. Blocked on counter tiles being
      mapped (every candidate has `tile: None`).
      Also: **dead weight is invisible by construction** — `_battler_slots()` only asks
      "not an egg, has a move with base_power > 0", so a L5 CASCOON in a L24 party passes,
      and `_prepare_for_fight` then excludes it from training. Cheap first win: bench or
      deposit anything more than N levels below the lead.
- [ ] #24-personality — **A two-axis bot "personality" (user answer 2026-07-26).** The
      user wants BOTH testing-diversity and competence, selected by a personality that
      swings and drifts during play so it looks organic. Recommendation in the design
      note: TWO axes (`curiosity` = what it collects/fields, `caution` = how much risk it
      takes), because one axis forces "more varied" to also mean "more reckless".
      Drift should be EVENT-DRIVEN (whiteout -> caution up; clean streak -> caution down),
      not a random walk. ‼ TRAP: "cautious" must NOT mean "grind longer" — P2 whited out
      41x on Route 110 while training, so that loop would worsen the dominant failure.
      Must be a pure function of (seed, events) so it is testable without an emulator, and
      the rolled values must reach the logs so personality can be correlated with outcome.
- [ ] #24-favourite — **Roll a "favourite" species per run.** Prefer to catch/keep it,
      unless it is a disadvantage for the fight about to be entered. Cheap run-to-run
      variance that is independent of the RNG decorrelation already in place.
      **ANSWERED 2026-07-26:** "disadvantage" = a TYPE CHECK, applied to gym leaders /
      rival / Wally / Elite Four, PLUS reactively when a trainer keeps beating the bot
      (hang that off the existing `_defeat_counts`, `story_mode.py:813`). TWO favourites
      per run: one regular, one LEGENDARY. Pool = anything obtainable in Emerald —
      ‼ derive it from `modules/obtainability.py` + `emerald_obtainability.json`, never a
      hand-written list, and check whether that model counts event-only species (Mew,
      Deoxys, Jirachi, Ho-Oh, Lugia) as obtainable. Honest note: every Hoenn legendary is a
      late-game static, and the frontier is ~Badge 3, so the legendary favourite will do
      NOTHING for run diversity yet — build it, log it, expect nothing from it for now.
      ‼ The rival / Wally / E4 rosters are NOT yet decomp-verified (gym leaders are, in
      `modules/badge_case.py`); they need that before the type check can use them.
      Still open: preference strength; per-run vs per-lane (recommend per run).

## Next (user-set order 2026-07-19: #30 → #31 → #32, THEN the first wave below)
> #30/#31/#32 are BUILT + ADVERSARIALLY VERIFIED in sandbox (clean pass:
> money cheat byte-safe 56/56, GUI nav 28/28, no code bugs). AWAITING USER
> OK to promote to custom. In-game confirms still pending (filled-slot
> composites, hover with real stats, money effect, controller feel on Ally).
- [ ] #30 — Handheld & GUI refinements (user-specified 2026-07-19):
      (a) Persistent "Handheld Mode" button — move it out of the Play/
      Controls tab into an always-visible header (in the drawer: right of
      the "TOOLS" text; desktop: a header row above the tabs) so it shows on
      every tab.
      (b) Handheld menu relocation — in handheld mode the Tk top menu
      (Emulator/Profile/View/Help) must NOT appear at all (even with the
      drawer open; reverses the earlier "menu shows with drawer" behavior
      for handheld). Surface those commands as buttons/sections inside the
      PLAY tab instead. Desktop keeps the normal menu bar.
      (c) Left Party Section — a vertical party strip to the LEFT of the
      emulator video, in BOTH desktop and handheld: 6 slots, 1 mon/row.
      Empty slot = Poké Ball sprite; filled slot = the mon's sprite
      composited over its caught-ball sprite (ball BEHIND, from
      `pokemon.poke_ball`; ball art at sprites/items/<Ball>.png).
      (d) Hover stats — hovering (mouse) over a Left Party slot shows ALL
      that mon's stats (level/IVs/nature/ability/moves/…) in a tooltip;
      SAME hover-stats on the Party tab rows; must also be reachable via the
      gamepad-GUI navigation (#32).
- [ ] #31 — Adjustable money cheat: in the CHEATS card, a money entry
      pre-filled with the character's CURRENT money (read live), editable to
      any value, + a "Lock" toggle that freezes money at the typed value
      (on = keep re-applying that exact value; off = stop). Refines the
      existing Max/Infinite money.
- [ ] #32 — ★ Gamepad-driven GUI navigation (roadmap F2, PRIORITIZED by
      user to come right after #30/#31): drive the dashboard with the ROG/
      Xbox controller (D-pad/stick move focus across tabs/cards/buttons/
      party, A activates, incl. triggering the party hover-stats). Distinct
      from the existing in-GAME gamepad input (Manual mode).

## Adjustments (user-requested 2026-07-19)
- [x] #36 — Left Party balls enlarged 52→104px (ball visible behind mon)
      (ce66eb78).
- [x] #37 — Party hover tooltip restyled Pokémon-themed (type badges, IV
      grid, moves, sprite) (ce66eb78).
- [x] #38 — Gamepad GUI-nav gated to drawer-open only (no more gameplay
      interruption) (ce66eb78).
- [x] #39 — Auto-DECLINE new move learning (default `new_move: cancel`;
      seam for future move-intelligence at
      DefaultBattleStrategy.which_move_should_be_replaced) (25fac025).
      User's placed battle.yml also set to cancel.
- [x] #40 — Catch-ball allowlist (d5573234): "CATCH BALLS" card (checkbox+
      icon per ball) filters catch.py::_get_best_poke_ball; catch_balls.yml
      global+per-profile; default protects Master Ball. Live-verified on the
      real save. (Live catch in a real battle still pending.)
- [~] #36b — Party balls enlarged further to 140px (~2.7×); reads clearly
      behind smaller mons, big sprites (Celebi/Sceptile) still partly cover.
      Capped by column height — could go scrollable for a true 5× if the
      user wants. (d5573234)
- [x] #S — User's real save placed: "Nick - Emerald" (progressed) +
      "-restored" + global configs into custom/sandbox profiles/
      (gitignored). LIVE TEST on real party running.

## User rulings + new round (2026-07-19)
- [x] RULINGS: Latias+Latios BOTH obtainable (218/386); Surskit unobtainable
      (c2707bad).
- [x] #46 — Hover tooltip ball ~3× (fixed thumbnail no-op bug) (c2707bad).
- [x] #47 — Opportunistic catch: any SHINY (even owned) caught (c2707bad).
- [x] PROMOTE-2 — whole batch promoted to custom w/ extensive intent docs
      (DIVERGENCE-LOG a–i + DOCUMENTATION/05-hunting-and-livingdex.md);
      live-verified on the real save; 29b9aae5.
- [x] ~~`#24` (roadmap restatement)~~ — ‼ **SUPERSEDED by the canonical `#24`. CLOSED.**
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full restatement is there; the canonical `#24` remains in place.
- [~] #24-move — SMART MOVE-LEARNING (user 2026-07-20): DONE — Story strategy
      `which_move_should_be_replaced` override keeps every Pokémon combat-capable
      (never trades a damaging move for a status move), preserves type coverage,
      and skips no-gain moves; overrides the stock `new_move: cancel` decline.
      In both builds, unit-verified. REMAINING (folds into #24-team): status-move
      UTILITY ranking (value Sleep Powder/heal over Growl) rather than treating
      all status moves as equal.
- [~] #24-resume — RESUME-FROM-ANYWHERE (user 2026-07-20): v1 DONE — segmented
      flag-gated run() resumes from a fresh game / resumed save / hand-played
      state, skipping finished segments (fixed the "thinks I need Wally"
      mis-detection via the HIDE_PETALBURG_CITY_WALLYS_MOM flag). REMAINING:
      finer per-STEP resume with each step self-locating from any tile; FAST
      travel (Fly/Teleport/Escape Rope when available, gated by HMs/badges/items
      per #42); title-screen-with-save auto-Continue; reliable completion flags
      for chapters past Gym 1. Design §RS.
- [ ] #24-autosave — AUTO CHAPTER SAVE-STATE (sandbox testing aid; user
      2026-07-20). After each scripted chapter/segment completes in StoryMode
      (SANDBOX ONLY), auto-save a save state named by chapter into `states/` so
      chapters can be tested/resumed fast. TOGGLE in the Play tab, DEFAULT ON,
      safely toggleable on/off even while the bot runs (the story generator reads
      the flag at SEGMENT BOUNDARIES, so flipping it never interrupts). Implement
      by hooking the segment boundaries already in `StoryMode.run()` (§RS).
      **APPLY ONLY AFTER the user green-lights the current story build** (it
      touches run()); until then this is a note. Save quickly at a boundary
      (get_save_state + write) — negligible one-frame pause.
- [x] #24-loadpage — LOAD-STATE POPUP PAGINATION (user 2026-07-20): DONE both
      builds. `load_state_window.py` now shows 5 states/page and lazily renders
      only the current page's thumbnails (Prev/Next + arrow/PageUp-Down + page
      label; nav auto-hidden for one page). Fixes the slow-open with a full
      `states/` folder (was decoding up to 128 PNGs at once).
- [ ] #24-defeat — DEFEAT RESPONSE (user 2026-07-20; design §DR). What the bot
      does when it LOSES a battle, as a settings-popup choice:
      (A) "Reload save state" = today's watchdog behaviour, made a toggle; verify
      the resume-after-reload rough edges (the segmented resume §RS already fixes
      most — the old run() stranded the bot on any restart; also ensure watchdog
      snapshots are CLEAN OVERWORLD states, never mid-battle/scene).
      (B) "Play through & retry" = ride out the whiteout → respawn (Poké Center /
      early houses) → recalc position + story segment (§RS) → MATCHUP ASSESS (avg
      enemy vs own level, team size, type/move coverage) → train/adjust team
      (#24-team) if outmatched → escalate on repeated loss → retry. Mode B = §RS +
      matchup gate + #24-team, one engine. Sub-parts: a small matchup scorer;
      whiteout ride-out; failure/attempt tracking per objective.
- [~] #24-evo — EVOLUTION policy (user 2026-07-20): CURRENT (sandbox+custom) =
      ALLOW ALL evolutions (`should_allow_evolution → True`, overriding the stock
      `stop_evolution`) — fixes the Lv16 evolve+move-learn hang and strengthens
      the team. POPUP options to add (#24-ui): **allow all (default on) / random
      evolution / no evolution**. Robustness the bot must have (verify): RECOGNIZE
      when an evolution happens, navigate the evolution CUTSCENE, and handle the
      accept/deny of a new move + deleting an old one to replace it (uses the
      stock evolve→learn path + `which_move_should_be_replaced`). "Random" mode =
      per-Pokémon coin-flip whether to evolve (organic team variety, ties #24-team).
- [x] ~~`#24-team`~~ — ‼ **SUPERSEDED by `#24-organicteam`, which is ✅ APPROVED — GATE LIFTED** (user 2026-08-06, re-confirmed 2026-08-14). ⛔ Read `#24-organicteam`, not this. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [ ] #24-shops — MAP SHOPS AS REACHED (user 2026-07-21; planning doc §4). Each mart
      has its own layout AND stock/order; the buy code is already shop-agnostic
      (universal task-driven flow + `_mart_item_row` reads stock live). So map each
      shop's ENTRY facts (mart map, clerk-approach tile, facing) when first reached,
      verify live, add an Atlas row. SPECIAL: **Lilycove Department Store** is
      MULTI-FLOOR (per-floor shop + stock, elevator nav); the **Elite Four Poké
      Center** has a shop + mart; Slateport stalls / TM sellers use non-standard
      menus. Do NOT map all shops up front (unreachable → can't verify).
- [x] ~~`#24-pc` (design entry)~~ — ‼ **SUPERSEDED by `#24-roster`**, which the
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full entry, its evidence and any ⛔ warnings are there.
- [x] #24-resume — SEGMENT 1 RESUME BUG FIXED (2026-07-21). Pre-Pokédex
      recovery/resume re-ran the scripted intro from the truck → derail loop
      ("stuck after respawn"). Split Segment 1: scripted intro gated on
      `_has_starter()`; train→rival→Pokédex resumable + flag-gated. Derail budget
      hardened (monotonic party `_progress_sig`; patient recovery). Verified in
      harness. Sandbox (early_game.py, story_mode.py). See CHANGELOG/MISTAKES 07-21.
- [x] `#24-freeze` — **OLDALE PC FREEZE, FIXED (user 2026-07-21). CLOSED.**
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the root cause and the fix are there.
- [x] #24-debuglog — DEBUG LOGGING TOGGLE (user 2026-07-21). Opt-in "Debug Logging"
      in the Run (bot-mode) menu (both GUIs), default off → `modules/debug_logger.py`
      writes an extensive structured log to `<profile>/debug-logs/` (event stream +
      stuck dumps with the generator call stack). For diagnosing Bug #2 (#24-freeze)
      from a shared real-bot log. Built + validated in sandbox. See CHANGELOG 07-21.
- [x] #24-swaptrain — SWAP-TRAINING **DONE** (user 2026-07-21). Fixes the
      under-levelled-mon training loop: `SwapTrainBattleStrategy` switches a trainee
      that's ≥2 levels below the wild foe to the strongest team-mate turn 1 (shares
      XP, no fainting/heal-churn). Gated around `train_team`. Validated Poochyena
      L4→L7, 0 heals/faints. Commit ef812c0e.
- [~] #24-trainmap — AREA-APPROPRIATE TRAINING (user 2026-07-21, Option 1).
      **ROUTING HALF DONE (2026-07-24):** `modules/story/training_areas.py` carries
      `TRAINING_GRASS` (10 areas with VERIFIED spin tiles + level bands), `AREA_PREREQ`
      (surf/region gates), `best_training_area(team_level, min_wild_max=, allow=)` and
      `estimate_frames_to_level()`. `_prepare_for_fight` calls it with the
      `_training_area_allowed` reachability predicate and RELOCATES via
      `_goto_training_area` (warp-aware), healing at the PC nearest THAT area — this is
      what stopped the Norman fodder grind. Swap-train (#24-swaptrain) remains the
      anywhere fallback.
      **REMAINING: the `PENDING_GRASS` spin tiles** — Route 104, Petalburg Woods,
      Rusturf Tunnel and Granite Cave 1F still have `None` tiles, so they can never be
      proposed. Fill each as the map is reached (two-way sweep from a real story anchor,
      per the Route 111/114 lesson: same-map connectivity does NOT imply the story can
      get there), then move the entry into `TRAINING_GRASS`.
      Related: `#24-regionreach` (the reachability predicate itself), `#24-watertrain`,
      `#24-healverify`.
      ‼ **NOW ENFORCED IN CODE — see `training_areas.NO_RETURN_GROUNDS`** (2026-07-26).
      This paragraph is history; the table is the authority, and both training pickers
      refuse those maps before any reachability check. It was moved into code because
      this prose was re-derived from scratch by a probe cycle on 2026-07-26 (08-MISTAKES).
      ‼ LAVARIDGE HAS NO REACHABLE TRAINING GRASS (two-way sweep 2026-07-23,
      `tools/story-dev/jaggedgrass_probe.py`): Jagged Pass cannot be re-entered from
      the town (one-way ledges) and Route 112's lower grass has no return path. So
      Segment 11d (Flannery) preps with a Water lead + heal and NO grind; a L29-31
      team wins but is marginal (one whiteout in validation run 11). First concrete
      customer for this item.
- [ ] #24-ui — STORY-BOT PRE-RUN SETTINGS POPUP (user 2026-07-20). A popup/menu
      shown BEFORE the Story bot runs to set: player name; starter nickname mode
      (none / defined / random); starter choice (specific / random); + other
      settings TBD. Front-end for the existing `<profile>/story.yml`
      (character_name/gender/starter/starter_nickname already read by
      modules/story/config.py). WORK ON THIS ONLY AFTER the bot is finished and
      tested 100% (user directive). Popup also hosts the #24-autosave toggle
      (auto chapter save-state, default on) and the #24-defeat "Defeat response"
      section (Reload-save-state vs Play-through-and-retry + sub-toggles).

## Living-Dex deepening (user-requested 2026-07-19; DESIGN-FIRST, no cutting corners)
- [ ] #41 — Obtainability model: classify every species — wild / evolution
      (method+from) / in-game trade / gift / static / roamer / event — so the
      Living Dex knows trade-evolutions and evolve-only / trade-only mons
      (must obtain pre-evo + evolve, or manual trade), not just "no wild →
      skip". (design: 11-LIVINGDEX-DESIGN.md)
- [ ] #42 — Reachability/requirement gating: hunt + living-dex must skip a
      target when the area/encounter needs a capability the player lacks
      (Surf/Cut/Rock Smash/Dive/Waterfall HMs, the right fishing rod, badges
      for HM use, story-flag area access). Read owned HMs/rods/badges/flags
      from the save.
- [x] #43 — Living Dex OPPORTUNISTIC catching: catch ANY wanted-uncaught
      species en route (target only drives travel); live-dex-driven
      advancement; 22/22 units (a8840769).
- [x] #44 — Party ball rework: strip now clean mon sprites (no ball
      backdrop); caught ball moved to the hover tooltip as an icon+name row.
      Live-verified on the real save (9c2b1f94).
- [x] #41-evo/#42-easy — obtainability (evolution) + capability gating
      built (ceb7343e; 30/30 units; live save read Old/Good/Super Rod;
      panel shows 128 wild/147 evolve/102 special-trade). obtainability.py
      + capabilities.py.
- [x] #41-research — compiled + fact-checked Emerald obtainability lists
      (gift 7/static 8/roamer 1/event 6/breeding 3/special 1/unobtainable 79;
      in-game trades rescue nothing). Census sums to 386; "show both"
      denominators exposed (217/386 obtainable without trading). 16/16 units.
      modules/data/emerald_obtainability.json + obtainability.py. Fact-check
      report + citations: 11-LIVINGDEX-DESIGN.md (Phase #41-research). REMAINING
      for full #41: wire living_dex_mode target selection to plan_for's gate +
      route gift/static/roamer to reset modes; auto-evolve helper.
- [ ] #42-hard — HM-gated cross-map reachability in the nav graph (v2).
- [ ] #45 — (FUTURE, with story-mode bot #24) enumerate story instances the
      bot can automate, and let hunt/living-dex progress the story to unlock
      areas/capabilities needed for dex completion.

## Now-ish (user-added 2026-07-19, ahead of first wave)
- [ ] #33 — GUI fixes (in sandbox): Left Party Section ALWAYS visible in
      both modes regardless of drawer state; unified open/close — Pokéball
      opens the side tool menu + a Close/Hide collapses it in BOTH handheld
      AND desktop (desktop can hide tools to see more emulator).
- [ ] #34 — Living POKÉDEX tab: search all Emerald species; caught mark +
      shinies-caught count (from stats.db) + full dex info (types/abilities/
      base stats/dex#/category/flavor) + learnable moves (level-up/TM/HM/
      tutor/egg) — offline Bulbapedia. Needs battle sprite + dex artwork.
      RESEARCH-FIRST (see 10-DEX-RESEARCH.md): inventory bot data → gap-fill
      → fact-check → THEN build.
- [ ] #35 — ITEM-DEX tab: search all items; total-collected-historically +
      currently-held counters + item info + map locations + used/held/
      dropped-by Pokémon. Needs item sprite + inventory image. Same
      research-first flow as #34 (10-DEX-RESEARCH.md).

## First wave (after #30-#32 + #33-#35 — agreed direction 2026-07-19)
- [ ] #22 — ★ Watchdog / auto-recovery: BUILT IN SANDBOX 2026-07-19
      (c7d25305; encounter-stall + drop-to-Manual + frame-freeze detection,
      bounded recovery ladder [re-assert → savestate-reload w/ safety backup
      → give up to Manual], overworld-gated, alerts, GUI status line; 17/17
      self-tests + recovery-path safety confirmed). Remaining: live-hunt
      softlock recovery needs a progressed save; independent adversarial
      pass to bundle with the batch verification before promotion.
- [ ] #9 — Hunt planner: v1 + v2 BUILT IN SANDBOX 2026-07-19 (6141d96f,
      4df17747). Encounter index from ROM (132 species/805 locations,
      19/19 fact-check); Hunt tab shows ranked locations + mode; v2 adds an
      encounter-tile finder + "Hunt (Custom)" mode = one-click travel (via
      global nav) + hunt. KI-6 tab overcrowding FIXED (two-row tab bar).
      REMAINING: live navigate+hunt on a progressed save; Rock Smash has no
      auto-tile finder (degrades to manual). Independent adversarial pass at
      promotion time.
- [ ] #23 — Living-Dex orchestrator: v1 BUILT IN SANDBOX 2026-07-19
      (34c5f461; living_dex.py target derivation + "Living Dex (Custom)"
      mode: travel→hunt→catch-first-uncaught→advance; catch-intent verified;
      16/16 units + real-ROM fact-check 132 targets). REMAINING: live
      autonomous run needs a progressed save; screenshot harness needs a fix
      after #33 layout change; independent adversarial pass at promotion.
- [ ] #25 — Pokémon detail + PC box viewer: click a party/box mon → full
      stats (IVs/nature/ability/moves); browse PC boxes with sprites. (M)
- [ ] #11 — Analytics suite: v1 BUILT IN SANDBOX 2026-07-19 (8094bb05;
      analytics.py + ANALYTICS card in Stats tab: encounter-rate sparkline,
      luck meter [actual vs binomial 1/8192, Ïƒ/z/verdict], sortable+
      filterable stats browser w/ sprites; 26/26 units). REMAINING:
      meaningful values need a populated stats.db (real hunt); independent
      pass at promotion.
- [ ] #27 — Battery-aware mode (ROG Ally): throttle speed/fps on low
      battery, pause on critical, resume on charge. (S-M)
- [ ] #28 — Polished mobile remote: phone-optimized web dashboard view to
      monitor 24/7 hunts (builds on the existing HTTP API). (M)

## Later / icebox (catalog in 09-FEATURE-BRAINSTORM.md; user re-orders/culls)
- [x] ~~`#24` (roadmap restatement)~~ — ‼ **SUPERSEDED by the canonical `#24`
      entry (“STORY AUTO-PLAYER”, the one carrying current state). Consolidated 2026-08-10.**
      HISTORY, kept for the reasoning trail — #24 — Story auto-player (trainer/gym battler) — most ambitious, most
      transformative: progress the game to bootstrap a save to any hunt. (L)
- [ ] #26 — Theme system (selectable color themes; palette is centralized). (S-M)
- [ ] #29 — Box manager / auto-release by IV/nature/shiny filter (prevents
      full-box stalls in long hunts). (M)
- [ ] #13 — Macro composer v2: chain macros + repeat counts + conditions. (M-L)
- [ ] #14 — Profile manager UI (create/duplicate/rename/delete). (S-M)
- [ ] #15 — Config editor GUI (catch_block/battle/cheats + CCF builder). (M)
- [ ] #16 — PKHeX quick-export (.pk3 of any party/box mon). (S)
- [ ] #17 — Multi-instance manager (several profiles, aggregating board). (L)
- [ ] #19 — Stream overlay theme refresh (OBS overlay → dashboard style). (S-M)
- [ ] #6 — Idea backlog: everything else in 09-FEATURE-BRAINSTORM.md
      (egg-hatch optimizer, catch profiles, Nuzlocke, goals panel, log
      viewer, setup wizard, keybinding editor, shiny gallery, hunt-summary
      cards, cross-session history, stream chat, webhooks, crash-safe
      savestate ring, health monitor, scheduled hunts, gamepad-driven GUI,
      RNG manip, cheat presets, plugin loader UI).

## Promoted to custom 2026-07-19 (built; awaiting user in-game confirmation)
- [~] #3 — Custom automations + Patrol (v3 multi-map/global-nav). Awaiting
      user's in-game play-test.
- [~] #7 — Sandbox enhancement round (backup/restore + cloud, macros,
      multi-map Patrol, GUI pack) — built, adversarially verified (16-bug
      round), promoted.
- [~] #8 — Warp-aware global pathfinding — promoted; user cross-warp walk pending.
- [~] #10 — Gamepad + handheld menu-hide — promoted; user real-pad test pending.
- [~] #12 — Shiny alerts — promoted; user sees a live shiny fire it pending.
- [~] #18 — Auto-update notice — promoted; observe on a stale checkout pending.
- [~] #20 — Cloud save-sync v2 (off by default) — promoted; desktop↔Ally run pending.
- [~] #21 — Game cheat menu (+ tabbed GUI, full-dex sprite picker, XP bars,
      topmost dialogs) — promoted; user in-game effect test pending.

## Story bot (#24) — open backlog
> Two groups: the PRIORITY block was added 2026-07-25 by the doc audit (these IDs were
> referenced all over the changelog/handoff but had no punch-list entry at all). The rest
> were sitting under `## Done` while still open (`- [ ]`) and were moved here the same
> day — not reworded, only relocated.

### Priority block (added 2026-07-25 — previously referenced but unlisted)
- [~] **#24-whiteout — MEASURED 2026-07-25; half fixed, half is now `#24-counters` phase 2.**
      ‼ It is **not** attrition in the general sense. Census of all 5 night5 runs (~128
      losses; losses:whiteouts are 1:1 — no potion/revive layer exists, so a loss always
      whites out): **~83% of losses are GYM LEADERS** — `PETALBURG_CITY_GYM` 38 (Norman),
      `MAUVILLE_CITY_GYM` 24 (Wattson), `FORTREE_CITY_GYM` 20 (Winona),
      `LAVARIDGE_TOWN_GYM_1F` 18 (Flannery), ROUTE110 10, Dewford+Rustboro 6. Travel and
      wild encounters are noise by comparison.
      **What boss-as-training-vehicle actually delivers** (run3, Norman, traced): 27
      attempts / **508,000 frames** (~19k each) / **+2-4 levels total** / **KOs flat at
      1-2 of 4 for all 27** / a L15 Shroomish carried untrained the whole way.
      **DONE:** the plateau detector was **power-blind** and could never have fired on
      Norman — its "we have an answer" veto accepted **Rock Smash (20 power)**, the HM
      the bot must carry, because Fighting is 2.0x vs Normal. Now requires
      `base_power x effectiveness x STAB >= CREDIBLE_ANSWER_POWER` (60). A/B on the real
      party: `(False, []) -> (True, ['Fighting'])`. Its silent `except` now warns.
      (Note the night5 logs PRE-DATE the whole counter chain — 07:36 vs 09:47-13:27 — so
      those 27 attempts had no guard at all, and would still have had none without this.)
      **LIVE-CONFIRMED 2026-07-25** (batch `20260725-194810`, 5 fresh lanes): the guard
      fired on Norman at **exactly 6 losses** in 2 runs (was 27), Petalburg-gym losses
      38 -> 14 batch-wide, and **1/5 reached the frontier** (baseline 0/5).
      **✅ TRAVEL ATTRITION FIXED 2026-07-26 — SURVIVAL MODE.** run01 lost **25 times on
      ROUTE110** (largest single cluster, 31 of 66 batch-wide). Root cause was NOT training:
      with no `train_team` session, `on_battle_started` falls through to
      `LevelUpTravelBattleStrategy`, which fights every wild to level the lead and "flees only
      at low HP, which the training loop covers by healing" — but a TRAVEL leg has no training
      loop and so never heals. After `SURVIVAL_WHITEOUT_THRESHOLD` (3) defeats on a map, wild
      battles there are FLED. Narrow by design and asserted in `repro_survival_mode.py` (7
      cases): wild only (trainers are un-fleeable, boss path untouched), never during
      `train_team`, per-map. On the real run01 state it flees — 22 of those 25 whiteouts
      would not have happened.
      **REMAINING:** the bot now STOPS with a named counter instead of grinding forever.
      Actually travelling/catching/training it is `#24-counters` phase 2 — the two items
      are the same problem from opposite ends. Also still unbuilt: a potions/healing
      layer (`#24-provisions`) so a loss is not automatically a whiteout, and benching
      dead-weight party members (a L15 in a L30+ team is a free loss).
- [ ] **#24-pokenav-faithful — the FAITHFUL PokéNav tutorial is being skipped 8 runs out of 9.**
      ‼ **This is a RECURRENCE of the `[x]` entry in `## Done` (2026-07-22), not a duplicate.**
      That entry closed the first sighting as "user ran VIDEO OFF — the renderer-gated fallback
      fired as designed" and explicitly said *"check why the faithful path didn't engage next
      time it recurs"*. It recurred; this is that check. The same id intentionally appears twice.
      Measured across the user's real-hardware logs (2026-07-26): ONE run played it faithfully
      ("PokéNav Match-Call tutorial (calling Mr. Stone)... done (called Mr. Stone)"), the other
      EIGHT fell back to "clearing the forced PokéNav Match-Call tutorial (state-write to vanilla
      end-state)". Not a breakage — the fallback reproduces vanilla's exact end-state and never
      hangs, so runs continue — but the standing faithfulness directive makes the state-write a
      LAST RESORT, and it has quietly become the norm on real hardware where the renderer IS on
      (which is the condition the faithful path needs). The 1 success proves the faithful path
      still works, so this is a trigger/stall-detection question, not a dead feature.
      Start by logging WHY the fallback fired (renderer state, which stall bound tripped) —
      today nothing records the reason, so the choice is invisible.
- [ ] **#24-npcheal — heal at an NPC, not only at a Poké Center.** Re-pair the Route 111
      training band to `ROUTE111_OLD_LADYS_REST_STOP` (decomp-cited: a full, ungated,
      repeatable heal — **96 steps vs 213** to Fallarbor). Blocked on a heal-at-NPC
      helper: every current heal path assumes a Poké Center layout (KI-19).
- [~] **#24-counters — CATCH A TYPE COUNTER when the boss plan cannot converge (KI-23).**
      **Phase 1 DONE (2026-07-25):** `_boss_plan_is_hopeless` detects non-convergence
      (6 losses + flat KOs + nothing hitting the boss's `ace_types` for ≥2.0), computes
      the needed types from the real type chart, and `counter_plan.find_counter_candidates`
      ranks catch targets over the whole-game encounter index, gated by
      `_counter_area_allowed` → `region_reach`. Proven from the Winona-era save: it names
      **Electrike on ROUTE118 (29,15), L24-26, 30% — REACHABLE**, where the old predicate
      returned zero. Fail-safe in all three planner outcomes (`repro_counter_wiring.py`).
      **Phase 2 NOT STARTED:** actually travelling to the target, catching it, and training
      it. Today the bot converts an unbounded loop into a bounded stop that NAMES the fix;
      acting on it is the next step and needs a live run to validate, not a repro.
      **SPEC + ECONOMICS: `12-STORYMODE-DESIGN.md` §CC2 (+ its 2026-07-26 update).**
      Blocker #2 (ranking) is CLOSED — candidates now sort by ESTIMATED COST (frames to
      find + frames to train to the team's level) instead of encounter rate; measured
      effect on the real save: Machop/Jagged Pass 75,949 vs Makuhita/Granite Cave 315,260,
      i.e. the old order preferred the 4.2x more expensive option.
      ‼ **BLOCKERS (1), (3) and (4) ARE CLOSED — 2026-07-30.** All three were the same
      bug wearing three hats, and the fix is one fail-closed predicate:
      `training_areas.hunt_ground_tile()` (whitelist: `TRAINING_GRASS` + the new
      `HUNTING_GROUNDS`) → `counter_plan` candidates carry `huntable` →
      `counter_plan.best_huntable()` is the ONLY selector an executor may call.
      Proof `repro_counter_huntable.py` (offline, real ROM tables, ALL PASS).
      (1) **Tiles — the premise was WRONG.** "Every candidate has `tile: None`" is false:
          Wattson's ROUTE111 (25,55) and Winona's ROUTE118 (29,15) answers both carry
          swept tiles. Only the *Fighting* answers lacked one, and FIERY_PATH **(18,19)**
          is now recorded in `HUNTING_GROUNDS` — the tile `story_harness --driver
          fierycave` actually walked; legs 1+2 PASS, only the heal leg fails, and a
          catch-and-leave hunt never walks it. **All three derail classes now resolve to
          a swept, walkable destination.**
      (3)+(4) **Victory Road / story interiors — solved by the whitelist, not by
          `KNOWN_GATES`.** The blacklist route would be an ever-growing list of game facts
          written from memory (forbidden). And reachability could never have gated it:
          run live from the Winona-era save, `_counter_area_allowed` reports **Magma
          Hideout, Shoal Cave and the Safari Zone as `reachable`**, 10/10 candidates.
          Confirmed hazard, not a theoretical one: rank 1 for Norman is **Hariyama @
          VICTORY_ROAD_B1F L38-42**, because the cost model prices "train it to the team's
          level" at ~0 for a wild already above the team — so it PREFERS endgame maps.
          Jagged Pass proves the gate has teeth: it ranks ABOVE Fiery Path (134,702 vs
          250,297 frames) and is refused via `NO_RETURN_GROUNDS`.
      ‼ **REMAINING BLOCKER: (2) the executor itself** — travel to `best_huntable()`'s
          tile, catch (a `COUNTER_CATCH_TARGET_DEX` catch-on-sight branch mirroring
          `HM_CATCH_TARGET_DEX`), and TRAIN the catch. See `21-TEAM-POLICY-DESIGN.md` §5.
          ‼ The train step is NOT optional garnish: catching a L15 Machop for a L30 team
          and not training it converts today's bounded, honest stop into an unbounded
          loop, because `_boss_plan_is_hopeless` then answers "not hopeless" for ever
          after. Bound the OUTCOME (playbook rule 3).
      ‼ **Value check before building:** priced against the measured cost of the current
      behaviour (run05 lost to Norman 21x ~ 399,000 frames; run3 27x = 508,000), a Machop
      costs 98,877 and a Makuhita 363,982 — but the only counter the LIVE predicate
      accepted was the Makuhita, i.e. ~9% better than doing nothing. **Phase 2's value is
      gated by reachability, not ranking** — widen reachability first or it buys little.
- [~] **#24-regionreach — region-scale reachability oracle.** ‼ **A WRONG *YES* COST 2 OF 5
      LIVE RUNS (2026-07-25) — now bounded.** `_training_area_allowed`'s cost model said a
      wrong yes "costs ONE wasted walk, fails RECOVERABLY and loudly"; in batch
      `20260725-194810` it cost the RUN, twice, because the picker is DETERMINISTIC and every
      derail re-picked the same unreachable ROUTE111 (25,55) from Mauville (that tile is
      FALLARBOR-SIDE ONLY — north of the Go-Goggles desert — while `is_map_reachable` is
      correctly True for the map). FIXED generally, not per-tile: new
      `UnreachableDestinationError(BotModeError)` + `StoryMode._training_unreachable`, keyed
      `(standing map, target map, tile)` so a directional ground survives elsewhere
      (`repro_training_unreachable.py`, 5 cases). This bounds EVERY future `KNOWN_GATES` gap
      to one wasted walk — which is the point of (a) below.
      **BUILT + PROVEN**
      (`modules/story/region_reach.py`, `repro_region_reach.py`): a graph from the ROM's own
      `MapConnections` + warps, capability gates, and `why_unreachable()` reasons that keep
      "no connection path" / "needs Surf at A↔B" / "reachable but N hops away" as three
      distinct facts. **STILL OPEN:**
      (a) **`KNOWN_GATES` must GROW** — it holds ONE hand-verified entry (Dewford's two sea
      edges), so any gate not derivable from ROM data reads as UNGATED. This oracle fails
      OPEN where the old one failed CLOSED; that is the right direction for a planner but
      must be grown before it gates anything irreversible.
      (b) ~~Only one caller is wired~~ **DONE 2026-07-25 — BOTH callers now use it.**
      `_training_area_allowed` was switched off `calculate_path`; the Winona candidate list
      went from `[False × 10]` to `[True × 5, False × 5]` (Route 118 Electrike reachable).
      Landing it exposed a partial-mock bug in `repro_fodder_grass._stand_at()` that had been
      giving false confidence to every training-logic change for two days (see 08-MISTAKES).
      (c) ~~`repro_counter_plan.py:200` red~~ **RESOLVED 2026-07-25 (user ruling):** the
      non-vacuity check moved off the wide type set (where it required an unreachable entry to
      exist, and so inverted when the predicate was fixed) onto the WINONA set, asserted to
      span both branches — the property the sort proof actually needs. Full repro suite 5/5.
- [ ] #24-edgecost — finer travel cost than a flat 1-hop edge (**DEFERRED**). Uniform
      weighting compresses "same landmass cluster" (1-4 hops) — measured from ROUTE120,
      Lilycove (2) reads as CLOSER than Route 118 (3), the actual answer — because one ROM
      connection can span a whole sea route. If finer granularity is ever needed: weight
      each edge by the source map's traversal length, or price travel in FRAMES so it
      composes with `training_areas.estimate_frames_to_level`. **Not needed until hop count
      demonstrably mis-ranks something** — today `max_hops` is only ever a filter (KI-24b).
- [ ] #24-fortreelive — close the Fortree Kecleon-chokepoint proof properly. The current
      evidence is a strong FAULT-INJECTION proof (flag 969 injected → (25,8) walkable), not
      a live post-flush save. Capture a checkpoint keyed on flag 969 and re-run §6/7
      WITHOUT injection to close it. Residual verification debt only — the live playthrough
      already sets the flag first via `get_devon_scope`.

### Moved out of `## Done` (still open)
- [ ] #24-sanity — SELF-CORRECTION / SANITY-CHECK (user 2026-07-20; design §SC).
      Story mode must never get permanently derailed: re-validate at every segment
      boundary (did the completion flag actually set? else retry/skip-ahead),
      handle out-of-place execution (self-locate), handle non-monotonic progress
      (reload/blackout moving backward), detect mid-run derailment (expected vs
      actual segment) and re-sync, bounded retries + escalation (ties §DR/#24-team),
      stall watch as last resort (Watchdog #22). Unifies §RS + §DR + #24-team into
      one state-machine engine. Also bounds the Treecko-Lv16 "stuck but not stopped"
      loop class.
- [ ] #24-interrupt — INTERRUPTION INTELLIGENCE (user 2026-07-22): the bot should
      KNOW when its current task was interrupted and by WHAT (training spin →
      trainer sight-line battle; navigation → PokéNav call ring; heal walk →
      scripted scene; etc.) and resume the task accordingly instead of relying on
      the generic derail/retry loop. Today large parts are handled implicitly
      (battle listeners resume travel; _ride_out_scripted_scene; the derail
      recovery re-runs _play) — this item is the DELIBERATE design pass: a small
      "current intent" state (what am I doing + resume point) + an interruption
      classifier, so recovery is targeted rather than re-derived. Design first
      (fits the decision-brain seam in doc 13 §future).
- [ ] #24-movelock — BATTLE ENGINE: move-blocking/locking effects (user
      2026-07-22): Disable (last move unusable), Encore (locked INTO a move for
      N turns), and kin (Taunt — status moves blocked; Torment — can't repeat;
      Imprison; Choice-item lock later). The turn chooser (get_strongest_move_
      against / move_is_usable) currently ignores these volatile statuses, so a
      blocked move can be selected → wasted turns (the game refuses the input).
      Fix: read the battler's volatile status/disable struct and filter the
      usable-move set; if EVERYTHING is blocked, Struggle happens naturally.
      Validate vs a Roxanne/Brawly-era Disable user (e.g. wild Whismur has none —
      find a story trainer with Disable/Encore, or fault-inject the volatile
      struct in the harness).
- [x] **✅ `#24-ch8b-museum` — DONE 2026-07-22; the marker was 31 DAYS STALE** (found by a PASS 5 audit). — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [ ] #24-freshbatch-rustboro — batch run03 (fresh game) 2026-07-22 played
      extensively but HUNG in Rustboro (11,3)=(5,3) area after ~450k frames
      (Torchic start, 4-mon team). Under-investigated; capture a repro from the
      run03 log if it recurs in a future batch.
- [ ] #24-train-efficiency — the same run spent ~240k frames on the pre-rival
      level-floor (L10) and ~200k on the Brawly band (L15) with swap-training.
      Bounded + productive, but slow. Related: an ABRA catch (Teleport-only, can''t
      attack) rode along the whole run at L7 — confirm battler-slot exclusion is
      airtight and consider skipping Abra-class catches for team slots, or routing
      lows to level-matched grass (#24-trainmap).
- [ ] #24-npc-talk-speed — Briney talk-dance polish (user log review 2026-07-22):
      BOTH user-observed oddities are the same subsystem, `_talk_to_wandering_npc`
      (observe a patrol lap -> park beside the route -> face-tap on transit):
      (a) cottage Briney (~3,600 frames of visible maneuvering before the talk at
      (6,2) in Route104_MrBrineysHouse), and (b) post-Brawly "erratic movement
      right of the gym" = the DOCK Briney ambush near (12,9) (~5-7k frames across
      four transient stucks at sail_to_slateport's dock-talk step; it completed
      and sailed — slow, not broken). FIX DESIGN: add a `known_spot` fast-path —
      navigate STRAIGHT to the recorded successful parking tile per NPC (extract
      the exact tiles from validated-run debug logs), wait bounded (~1 lap) for
      the NPC to transit adjacent, face-tap+A; on one failure fall back to the
      full observe-then-park. Keeps the proven adaptive path as the safety net.
- [ ] #24-hm-slaves — HM CARRIER ARCHITECTURE (user directive 2026-07-22 night):
      HMs are infinite-use but unremovable without the Lilycove MOVE DELETER
      (free; the Heart Scale is for Fallarbor''s Move RELEARNER — different NPC).
      Near-term policy: Marshtomp carries Rock Smash + later Strength (learns
      both; physical-type moves suit its Attack — a working mule, not a dead
      slot). Longer-term: dedicated HM slave(s) (Zigzagoon: Cut/Rock Smash/
      Strength/Surf) parked in the POKEMON PC — which requires PC deposit/
      withdraw MACHINERY (party-slot management UI flow) built BEFORE the
      Surf-era chapters (~Ch13+, Route 118 gate). Also: some moves are
      overworld-usable from the party menu (Dig, Teleport, Flash, Sweet Scent)
      — useful shortcuts (Teleport-to-PC, Dig-out-of-caves) worth wiring into
      travel logic once carriers exist.
- [ ] #24-knowledge-base — DEEP GAME KNOWLEDGE BASE (user directive 2026-07-22
      night): per-chapter, during mapping: route items (visible + HIDDEN, both
      in decomp map.jsons), puzzles, secrets, legendary unlock chains + catch
      strategies (Regis braille gates, Sky Pillar/Rayquaza, Groudon/Kyogre story
      beats), gym rosters. Machine layer: the bot''s modules/data already holds
      full species/moves/learnsets/TM-compat — the MOVE-PRIORITY SYSTEM v2
      (#24-movelock: STAB + type coverage + Gen3 physical/special-BY-TYPE
      stat-matching + utility ranking) should QUERY it, not hand-author lists.
- [ ] #24-event-pokemon — EVENT LEGENDARIES, endgame (user directive 2026-07-22
      night): Deoxys (Birth Island via AURORATICKET), Mew (Faraway Island via
      OLD SEA MAP), Jirachi (external event), Latios/Latias roamer choice + the
      EON TICKET (Southern Island second Lati). These need event-only items that
      vanilla distributed via Mystery Gift / e-Reader — the bot must obtain them
      in a way that LOOKS earned and stays quasi-canon (user framing): candidate
      mechanisms to discuss LATER — Mystery Gift spoofing (emulating the
      distribution the game natively supports — most authentic), a scripted
      "delivery man" trigger, or a direct bag write (last resort). Same
      plan/map/test loop as story chapters + a design discussion with the user
      on the acquisition theater BEFORE building. Endgame content — schedule
      after the main story skeleton reaches the Elite Four.
- [ ] #24-provisions — HEALING-ITEM PROVISIONING + STRATEGIC HEALING (user
      directive 2026-07-23): alongside Poké Balls, buy POTIONS (the best tier
      available at the local mart — Potion→Super→Hyper→Full Restore as the
      frontier advances) and keep a sensible stock; then use them with intent:
      in-battle healing when a sweep is worth saving, between-battle healing in
      places with no PC (Victory Road, THE ELITE FOUR — vanilla players stock up
      at the League mart precisely for this). Extends the buy-at-mart machinery
      (shop-agnostic `_mart_item_row` already reads stock live). Design note:
      gate on money reserve like balls; a heal-item strategy layer slots into
      the battle strategies where flee/switch decisions already live.
      !!! PRIORITY RAISED 2026-07-26 (user directive) - AND THE DATA AGREES EMPHATICALLY.
      The old note said "NOT urgent (the fight/train/retry loop carries the mid-game)".
      Batch 20260726-201838 refutes it: LOSSES AND WHITEOUTS ARE 1:1 IN EVERY LANE --
      P1 27 losses / 27 whiteouts, P2 43/44, P3 10/10, P4 12/12. With no potion or revive
      layer, EVERY battle loss becomes a full whiteout: respawn at the last Center, walk
      all the way back, re-fight. A heal-item layer is the single change that breaks that
      1:1, converting the most expensive failure in the game (whiteout + travel) into the
      cheapest (one turn spent on a Potion).
      Build order: (1) BUY -- extend the existing mart machinery, gate on a money reserve
      as Poke Balls already do; (2) USE IN BATTLE -- a heal threshold in the battle-strategy
      layer where flee/switch already decide; (3) USE BETWEEN BATTLES where there is no PC.
      Steps 1+2 alone should measurably cut whiteouts, and that is a DIRECTLY MEASURABLE
      hypothesis: compare whiteouts-per-loss before and after.
      Money is not the blocker -- the Dewford arc alone has 4,924 PokeDollars on foot that
      the bot currently walks past (19-TEAM-BUILDING-DISCUSSION.md 8.2), and the Lilycove
      Dept Store 2F sells up to MAX POTION + Revive (Aqua-hideout recon 2026-07-26). NOT urgent
      (the fight→train→retry loop carries the mid-game) — required before the E4.
- [ ] #24-grasswander - ORGANIC MOVEMENT WHILE TRAINING (user request 2026-07-26).
      Today the bot trains by SPINNING IN PLACE - `spin()`
      (`modules/modes/util/higher_level_actions.py:158`) turns on the spot, wrapped by
      `_story_spin` (`early_game.py:172`) for the whiteout-abort and no-progress watchdog.
      The user wants it to WANDER the grass with human-like movement, mixing in occasional
      spins, so training looks organic instead of robotic.
      !! THIS IS THE SAFE PLACE TO PUT RANDOM MOVEMENT, and the risk profile is INVERTED
      versus travel meandering (#24-meander):
        * On a TRAVEL leg, extra steps mean more wild encounters, which means more battles,
          more damage and more whiteouts. Our dominant failure is travel attrition, so
          meandering there is actively dangerous.
        * While TRAINING, extra steps mean more encounters - which is the entire POINT.
          Wandering costs nothing we did not already want.
      SEAM ALREADY PROVEN: `run_in_circle` (`modules/modes/util/walking.py:726`) shows
      `follow_waypoints` accepts an ARBITRARY waypoint generator. A bounded random-walk
      generator drops straight into that seam - no pathfinder change at all.
      MUST PRESERVE (all three already exist and all three have scar tissue behind them):
        * the whiteout abort in `_story_spin`, or a mid-training whiteout spins forever;
        * the no-EXP-progress watchdog, which is what un-sticks a bot that wandered out of
          the grass - it already handles exactly this failure and must keep working;
        * the leftover-script clear, since an active script SUPPRESSES wild encounters.
      REAL RISKS to bound:
        * wandering OUT of the encounter region (watchdog catches it, but wasted frames);
        * wandering into a TRAINER SIGHT CONE next to the training patch - an unwanted,
          unfleeable battle;
        * hazard tiles - ledges (one-way, drops you out of the area) and Granite Cave B1F
          cracked floors. Confine the walk to a verified safe tile set, not "anywhere
          walkable".
      !! VERIFY FIRST, DO NOT ASSUME: does turning in place generate encounters at the same
      rate as stepping? If spinning is already step-equivalent, wandering is neutral on
      training speed and purely cosmetic; if stepping is faster, wandering is a genuine
      throughput WIN as well. Check `CheckForWildBattle` / the field state machine in the
      decomp before designing around either answer - this decides whether the feature pays
      for itself or merely looks nicer.
      Design sketch: a seeded bounded random walk over the region's MB_CAVE / tall-grass
      tiles, biased to stay near the centre, with occasional in-place spins and short
      pauses; region supplied by the caller (we already derive safe tile sets - see the
      Granite Cave work in `19-TEAM-BUILDING-DISCUSSION.md` 8.1).
- [ ] #24-items - GROUND + HIDDEN ITEM PICKUP (user request 2026-07-26). The bot walks
      past every item ball and every hidden item in the game. Two mechanisms, handled
      differently:
        (a) VISIBLE ITEM BALLS - real object events at a known tile; pickup is "navigate
            there, press A". The Ch14 recon alone found Carbos (Route121 55,10), Revive
            (60,10), Zinc (38,13), Max Potion (MtPyre Exterior 27,15), TM48 (19,40), Sea
            Incense, Lax Incense, TM30 - all on routes the bot already walks. The Aqua
            hideout holds a MASTER BALL (B1F 15,9) + Nugget, behind a solved warp path.
        (b) HIDDEN ITEMS - no object event; need the ITEMFINDER and a press on the exact
            tile. Requires the Itemfinder in the bag plus a per-map coordinate table from
            the decomp (`hiddenitem` script commands in data/maps/*/scripts.inc).
      !! SYNERGY, and the reason to build this alongside #24-provisions: many ground items
      ARE Potions and Revives, so pickup directly feeds the layer that breaks the
      loss->whiteout 1:1. Do (a) first: navigation + a press, reuses everything that exists.
      !! CORRECTED by later recon (22-CAPABILITY-RECON.md C1): PICKUPS ARE SAFE. Item balls
      (finditem/Std_FindItem) and hidden items both call checkitemspace FIRST; on a full bag
      the ball STAYS with its flag unset, so the pickup is simply retryable. No bag guard is
      needed for pickup logic.
      The strand vector is GIFT scenes only - giveitem/Std_ObtainItem calls additem with NO
      pre-check, sets VAR_RESULT=FALSE and prints nothing, and 38 sites never test it.
      Those are concentrated in KEY ITEMS (cap 30) and TM/HM (cap 64) - including EVERY HM
      (Cut, Flash, Strength, Rock Smash, Surf, Fly, Dive, Waterfall) and the Magma Emblem.
      The general Items pocket has NO unchecked story grant on the path, so stockpiling
      Potions cannot strand a run. Rule: keep KEY ITEMS and TM/HM headroom before gift scenes.
      !! The ITEMFINDER IS NOT REQUIRED to COLLECT a hidden item - only to detect one
      (field_control_avatar.c:346-353 checks the flag alone). The bot can harvest hidden
      items straight from a coordinate table without ever obtaining it.
      On-path healing already mapped: REVIVE at Route117 (9,1) and Route109 (16,23, hidden),
      MAX REVIVE at Petalburg (19,2), Hyper Potions on Route118/119, plus Rare Candies on
      Granite Cave B2F (29,4) and Route110 (26,47).
      Open: detour for items, or only collect what is on the existing path? Recommend
      on-path only first, then let the `curiosity` personality axis price the detour
      (19-TEAM-BUILDING-DISCUSSION.md 5).
- [ ] #24-tms — TM ACQUISITION + USAGE (user directive 2026-07-23): TMs arrive as
      gym rewards (TM39 Roxanne, TM08 Brawly...), ground items, and mart stock;
      the bot should track what's in the bag, know single-use vs HM reuse, and
      teach them via the SAME validated teach flow (teach_hm_move already takes
      any TM item + hm_learner_slot generalizes — the missing piece is the
      DECISION layer: which TM to which mon, driven by the move-priority system
      (#24-movelock v2) and later the per-Pokémon profiles (#24-pokeprofiles)).
- [ ] #24-pokeprofiles — PER-POKÉMON BATTLE PROFILES, deep-research program (user
      directive 2026-07-23): build a detailed profile for EVERY Emerald-obtainable
      species (217 + evolution lines; census in emerald_obtainability.json):
      goal moveset(s) with priority order, how each move is obtained (level-up /
      TM+where / HM / tutor), training plan (when to evolve, what to delay),
      battle role (sweeper/wall/HM mule), and priority tiers so the bot knows
      WHICH mon to invest in. Execution model per the user: OVERNIGHT AUTONOMOUS
      RESEARCH in batches (10-20 species — tune for accuracy over speed), with
      self-generated Gemini assistant prompts BOTH when stuck AND routinely for
      cross-referencing/verification of my own conclusions; results verified
      against modules/data (learnsets/TM-compat are already in the bot) before
      being written. Output doubles as the reference layer for the sibling
      Pokémon Emerald AI project (Pokemon_Emerald_AI_Notes.md). Prereq for the
      full #24-tms decision layer and the "proper battling" endgame; schedule
      after the story skeleton is deeper.
- [ ] #24-economy — CASHFLOW MAINTENANCE (user directive 2026-07-23, extends the
      planning doc's money-reality note): keep a healthy balance for balls +
      potions + TMs across the whole run — trainer payouts (the main income; no
      Vs Seeker in Emerald), Amulet Coin when obtainable, selling vendor trash
      (Nuggets/Pearls/Stardust from Pickup — Zigzagoon/Linoone party slot is a
      passive income engine), and mart budgeting against the reserve. Design
      with #24-provisions; both consult one Resource Ledger (doc 13 spec).
- [ ] #24-trainersweep — EXHAUST UNFOUGHT ROUTE TRAINERS BEFORE GRINDING (from the
      2026-07-23 boss-training discussion + Gemini consult): before any wild-grass
      escalation, sweep the one-time optional trainers reachable at the current
      frontier (Wattson stage: Route 111 south Winstrate family, Route 110 cycling
      road + surface leftovers, Route 117, Trick House puzzle 1-2) — big one-time
      XP+money a faithful player takes first. Needs: per-route trainer tables
      (decomp object events, sight-lines), a "fought yet?" check (trainer flags —
      readable), and routing. Later: PokéNav Match Call REMATCHES (255-step trigger,
      call answering, scaled teams) as the true repeatable mid-game XP engine.
- [ ] #24-gemini-org — "COMPANY-STYLE" GEMINI ORCHESTRATION (user 2026-07-23, timing
      left to the agent → deferred to a quiet/overnight slot): formalize the ad-hoc
      multi-agent consult pattern (design-critique agent + adversarial agent worked
      well for the sufficiency gate) into reusable roles (researcher / critic /
      verifier / synthesizer) with standard prompts, cross-checking rules, and when
      to escalate models (3.1-pro vs flash). Candidate first use: the #24-pokeprofiles
      overnight batches. Refine WITH Gemini agents when picked up.
- [ ] #24-rare-catch — RARITY-TIERED OPPORTUNISTIC CATCHING (user 2026-07-23, future):
      extend the catch branch beyond team-building phases: RARE species (low
      encounter-slot %, version exclusives, one-shot statics) should be caught on
      sight when NOT yet owned, in ANY phase (training, traveling) — party room +
      spare balls permitting, same gating style as the HM-learner hunt. An ULTRA-RARE
      tier (the user's example: a MALE Skitty — a 2%-slot species × 25% male gender
      roll) is attempted on EVERY encounter, shiny-style, even if the species is
      already owned. Needs: a rarity classifier (encounter-table slot % from the ROM
      data × gender-ratio math — all derivable, no hand lists), tier thresholds to
      agree with the user, and integration ordering vs the shiny branch (shiny stays
      first). Pairs with #43 opportunistic catching + the Living-Dex orchestrator.
- [ ] #24-hm-multi — TEACH AN HM TO ADDITIONAL APPLICABLE MONS (user 2026-07-23,
      future): after the primary teach, consider teaching the HM to OTHER party mons
      when it is a genuine upgrade over one of their current moves ("if they are
      present and if it is a higher priority over their current moves" — the user's
      framing). NOTE the research nuance before building: per the graded pokeprofiles
      registry, Rock Smash-class HMs are an HM TAX (weak move, undeletable without
      the Lilycove Move Deleter) — "applicable" must mean "the decision layer says
      it beats a current move" (#24-tms/#24-movelock), not merely "compatible", or
      we poison battlers' movesets. Strength (80BP) is the counter-example where
      multi-teach genuinely pays. Build after the TM decision layer exists.
- [ ] #24-flannery-grind (OBSERVATION, not a bug — 2026-07-23 milestone run): from the
      Lavaridge milestone (weak fixed team L29), Flannery took 3 boss-training whiteouts
      (L29→L32) before the win — grass-less gym + tanky Torkoal + optimistic sufficiency
      gate + team re-solves the trapdoor maze each retry (~22k frames/solve). Working as
      designed (reactive net ground out the win, 0 derails), but slow FROM A WEAK
      milestone team; a real fresh run arrives stronger. If it proves annoying later:
      a stronger prep floor for grass-less tanky-ace gyms, or full-team survivability
      in the sufficiency gate (consult flagged Torkoal's bulk+Sunny Day). Low priority.
- [ ] #24-rivalcap — `_rival_attempts` (story_mode.py §5c) increments on every _play
  re-entry, not on actual lost rival battles — a derail-y stretch near the rival can
  burn the 3-attempt budget without fighting once (seen on the goods_recovered thin-team
  save 2026-07-24). Key the counter on a genuine battle loss.
- [ ] #24-watertrain — WATER training tiles (user 2026-07-24): once Surf is obtained AND
      taught, surf encounters become a viable training band (level + typing permitting).
      Extend training_areas with water tiles + a "needs surf" prereq (the AREA_PREREQ
      mechanism already exists) and teach the picker to consider them.
- [ ] #24-healverify — re-verify the Surf-gated heal-centre pairings (Routes 115/118/119/121)
      from a POST-Surf checkpoint; repro_fodder_grass.py currently marks them PENDING because
      no pre-Surf save can path a water route. Route 119 (21,109) reached NO Poké Center.

## Done — ⚠ MIXED, and that is a defect being tracked, not a convention
> ⛔ **THREE STILL-OPEN `[ ]` ITEMS ARE FILED UNDER THIS HEADING** and are therefore invisible to
> anyone scanning for work: **`#24-partyindex-minus-one`**, **`#24-errorpath-frequency`**,
> **`#24-stalestatusclaims`** (that last one is named in `04-HANDOFF.md` as a startable
> alternative, so the handoff points INTO a section marked Done). Found by a PASS 5 audit
> 2026-08-22. ⇒ Move the three blocks above this heading; until then, this warning is the pointer.
> ⛔ **THE 8 OLDEST CLOSED ITEMS OF THIS SECTION MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-17)**
> on the R3 3,600-line budget. All were `[x]` and long closed; nothing was deleted. The relief
> valve is deliberate — `lint_docs` has been reporting ~105 completed items sitting in a
> CURRENT-STATE file, and this is the first draw on it.

- [x] `#24-ch20rename` (original text) — **NEW 2026-08-13, SMALL AND SAFE, do it at the START of a session not the end.**
      The Seafloor Cavern beat is **Chapter 20** (`chapters.py:233`), but 2026-08-13's work called it
      "§Ch21" throughout and the misnomer is baked into artefact names:
      `--driver ch20dive` (and its `Ch21DiveMode` class), `tools/story-dev/probe_ch20_topology.py`,
      and `ai-research-notes/2026-08-13-ch20-dive-leg-predictions.md`.
      ‼ Nothing is broken — they are correct code with wrong names. The risk is a future agent
      building "Chapter 21" (which is really **Sootopolis / Rayquaza**) against cavern tooling.
      **Do:** rename driver + class + probe + note, update `04-HANDOFF.md`'s naming-correction
      block and every reference, then run `run_gates.py`. **Do NOT** rewrite git history or the
      append-only logs — correct forward and leave the old names in the changelog where they are.

### `#24-faintchooser-fourthspace` — ✅ CLOSED 2026-08-17, ARCHIVED 2026-08-22 → `28-HANDOFF-ARCHIVE.md`

- [x] **ANSWERED: no fourth index space is demonstrated; the anomaly is INERT. ⛔ DO NOT "FIX" IT.**
      ‼ **The rule that survives:** `handle_fainted_pokemon` has had THREE index-space bugs
      (KI-18, KI-34, KI-66) — ⛔ when a fix is a coordinate/index conversion, MEASURE ITS
      DIRECTION with an observe-only probe FIRST; never reason it out from the docstring,
      which has now produced three bugs. Full 70-line record in `28-HANDOFF-ARCHIVE.md`.

### `#24-partyindex-minus-one` — a BOUND-BUT-WRONG `party_index` of `-1` slips past KI-65's guards (filed 2026-08-17)

- [ ] **Found by an orphan audit, not by a bug report.** KI-65's fix guards
      `battle_move_replacing.py:285` and `:425` with `if party_index is None:`, which covers
      **unbound**. It does NOT cover *bound but wrong*: `get_party_menu_cursor_pos` does not raise on
      a bad cursor — it calls `set_manual_mode()` and returns **`slot_id = -1`**
      (`battle_move_replacing.py:138` assigns it straight through), and `get_party()[-1]` is the
      **LAST party member**. That is a WRONG MON, not an exception, so both guards pass it.
      ‼ **Why it was nearly orphaned:** it was written only inside KI-65's body — under a header that
      reads **CLOSED** — which is exactly the shape `#24-orphans` exists to stop. Now tracked here.
      ⚠ **NOT observed live and unquantified.** ⛔ Do not "fix" it blind: first measure whether
      `slot_id = -1` ever reaches that line (an observe-only probe, per the rule that settled KI-66),
      because `set_manual_mode()` has already fired by then and the run may be derailing anyway.

### `#24-errorpath-frequency` — the fixes are proven CORRECT but their real-world FREQUENCY is unmeasured (filed 2026-08-17)

- [ ] **Both 2026-08-17 fixes are error-path fixes whose rate in real play is unknown**, and this was
      stated honestly in the changelog and then tracked nowhere:
      * **KI-65** reproduces what happens WHEN `_read_offered_move` fails — never how OFTEN it does.
      * **KI-66** was driven on one fixture; the pathological faint cost 1263 frames vs 59, but how
        often a real run hits it is unmeasured.
      ‼ **This is the one question a BATCH is actually the right instrument for** — §0c: battle-level
      metrics get ~800 samples per 3-hour batch and CAN resolve, whereas finish rate cannot.
      ⛔ **Pre-register the questions BEFORE running**, or the result gets rationalised afterwards:
      (a) how many times does KI-65's "cannot verify" message fire? (b) how many faints occur inside
      a partner double battle, and what is the menu-open→send-out frame cost distribution?
      (c) any NEW derail class that did not exist before these two fixes?
      ⚠ Blocks nothing today. It is worth doing once several changes have accumulated, so the three
      hours buy more than one answer.

### `#24-stalestatusclaims` — an ADVERSARIAL AUDIT FOUND 14 TRACKING CLAIMS THAT ARE FALSE OF THE CODE (2 fixed on sight, 12 filed) (filed 2026-08-17)

**2026-09-08 — ONE SUB-CLASS OF THIS ITEM IS NOW GATED, NOT CLOSED. ⛔ THE ITEM REMAINS OPEN.**
The *drift-figure* sub-class is done and enforced: `probe_drift_restatement.py` (gate #46) forbids a
live restatement outside the STATE row. Fourteen instances were found and remediated — an audit
listed 3, a Tier 1 reviewer found a 4th, a grep a 5th, the gate six more, and a SECOND reviewer pass
a 14th that the gate itself had been blind to (line-global quote parity on a 30,045-character line).
⭐ The transferable finding for the REST of this item: **when one instance on a line is found and
another on the same line is not, suspect the INSTRUMENT, not the list.**
⛔ The other 12 filed claims are untouched by that work and still need auditing.

- [ ] ⛔ **These are DOC defects, not code defects — the code is fine. Each was verified against the
      repo by an agent that ran greps and tools rather than reading prose.** ‼ **Two were fixed on
      sight because they would MISDIRECT the next session** (see below); the rest are filed here so
      they are not re-discovered one painful item at a time.
      ✅ **FIXED 2026-08-17, on sight:**
      * an `➡ NEXT: decouple _counter_ladder from grass_is_fodder` arrow commanding work that had
        **shipped to BOTH forks** on 2026-08-16 (`story_mode.py:1901` is `if boss_teaches:`);
      * this file's own `#24-driftassertions` deliverable claimed the gate "walks past `zero`" and
        made WORD FORMS the job — **`_WORD_NUMBERS` already includes `zero`** and `_NUM` interpolates
        it into all seven drift patterns (`re.I`). Only CLAIM-SHAPE detection was open —
        ✅ **and THAT SHIPPED 2026-08-17; `#24-driftassertions` is CLOSED. ⛔ Nothing here is
        outstanding work.** *(This clause read "Only CLAIM-SHAPE detection is open" until the item
        closed; a Tier 1 reviewer caught it still commissioning finished work from ~3,000 lines
        away — the very defect the bullet above it describes, committed by the pass that describes
        it.)*
      🔜 **STILL TO SWEEP (each has both halves quoted in the audit; re-verify before editing):**
      1. `#24-leadpolicy` tracked TWICE with conflicting states (`[x] A+C BUILT` vs an `[ ]` bullet)
         and **no supersede marker**, unlike this file's other duplicate IDs. Code: `early_game.py:1755`.
      2. **KI-25** still says *"needs a user ruling"*; the ruling shipped.
      3. **KI-43** header says *"FIX NOT YET APPLIED"*; `_TRANSIENT_WAIT_FRAMES = 600` is live in BOTH forks.
      4. **KI-26** says *"exactly SIX sites"* → there are **eight**; its "biggest lever" already exists.
      5. `#24-counters` *"Phase 2 NOT STARTED / the executor itself"* → `counter_hunt.py` IS the
         executor (`def hunt` `:426`, wired `story_mode.py:1702`), and `:2267` already says BUILT.
      6. `#24-items` *"walks past every item ball"* → `collect_item_ball()` is live (`early_game.py:8059`).
      7. `#24-postwinona-save` body says *"No save exists past Winona"* → `saves/post_winona.ss1` exists.
      8. `#24-slugmaspin` *"production runs this regression WITHOUT its fix"* → forks are identical.
      9. `CREDIBLE_ANSWER_POWER` written as `(60)` in the present tense → it is **75** in both forks
         (and this file says 75 elsewhere).
      10. Marker/count drift: the marker table says `80/17/37` → measured **96/21/105**; *"all 8
          handlers"* → **9**; *"24 checks"* → **21**; *"KNOWN_GATES holds ONE entry"* → **3**.
      11. `05-KNOWN-ISSUES.md`'s own header says *"23 distinct IDs … KI-15 appears twice"* → **64**
          distinct IDs, and `KI-15` appears exactly once — inside that sentence.
      12. `cache/warp_graph_BPEE0.json` is called *"committed"* but is **git-ignored and untracked**,
          while `rare_species_dataset.py:61` reads it ⇒ that dataset cannot be rebuilt from a clean
          clone. ‼ This one is arguably a REAL defect, not just a doc defect — triage it first.
      ⛔⛔ **THE GATES CANNOT SEE ANY OF THIS.** `lint_docs` and `audit_doc_consistency` exit 0 over all
      ‼ **And `probe_stale_citations.py` EXISTS but is NOT REGISTERED in `run_gates.py`** — a gate
      that might catch this class is sitting unused. **Registering it (after fault-testing) is
      probably the cheapest first move on this item.**
      ⚠ The audit also relayed ~9 further suspected items it did NOT personally re-verify. Treat
      those as UNCONFIRMED and re-check before acting.

### ✅ `#24-mossdeepstrand` — **CLOSED 2026-09-07 (sandbox): winning BADGE07 no longer locks the bot on the (23,8) collision island — `leave_the_gym()` now runs before BOTH badge early-returns.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-10, R3 budget).
‼ **ITS LIVE RESIDUAL IS HERE, NOT IN THE ARCHIVE:** the fix is **UNDRIVEN** — acceptance is still owed, and it is a drive from a save standing on **(23,8) with BADGE07 set**. Every checkbox in the retired block is `[x]`; the owed drive lived in prose, which is why a checkbox scan cannot be the archiving test. ⛔ Do not read the ✅ as "driven".

### `#24-ballrestock-ordering` — the counter hunt's ball restock is DEAD CODE from its only caller (filed 2026-09-07)
- [ ] ✅ `hunt()` holds the contingency (`counter_hunt.py:471-475`) but the ladder calls
  `resource_blocker()` first (`story_mode.py:1778-1782`) and returns; that blocker is now **only** a
  ball gate (`counter_hunt.py:405-407`) and `:1809` is `hunt()`'s sole production caller ⇒ **those
  five lines can never run.** Lane L03 lost a run to *"no spare Poké Balls"*, then bought 30 one run
  later. ⚠ **NOT a one-liner:** `provision_poke_balls` defaults to `RUSTBORO_MART`
  (`early_game.py:2299`), the tree's only mart constant, so from Fortree a restock is a cross-Hoenn
  trek spending the boss's one ruled hunt attempt shopping ⇒ minimum = ordering fix **+** nearest-mart
  lookup. ⛔ `06-DECISIONS-LOG.md:958/998/3423` checked — whitelist, one-hunt-per-run and second wind
  are SETTLED; **this ordering is covered by none.** Detail: `ai-research-notes/2026-09-07-batch-blockers-RECON.md`.

### `#24-punchlist-archive` — 03 is AT its 3600-line budget; the next item needs an archive pass first (filed 2026-09-07)
- [ ] ⛔ Move CLOSED items VERBATIM to an append-only archive; never splice. A 2026-09-07
  anchor-to-anchor compression swallowed a root-cause block and no gate noticed.

### `#24-tateliza-attrition` — the DEEPEST runs die losing to Tate & Liza, and NO guard catches it (filed 2026-09-07)
- [ ] ✅ MEASURED on the live batch: both `too many whiteout recoveries in a row` runs — the two
  deepest of the batch at **3,877,438** and **4,198,775 frames** — died in the Mossdeep Gym
  (`MOSSDEEP_CITY_GYM = (14, 0)`, `map_data.py:1005`) against **Tate & Liza**. Lane L04 reached
  **`defeat #24 here`**, L05 `defeat #11`. Each loss whites out, and each recovery **re-solves the
  117-step statue puzzle** (`Story: Ch18 plan #1 from (6, 35) — 117 steps`) before losing again.
- [ ] ⛔ **THE GUARD THAT SHOULD HAVE STOPPED IT NEVER FIRED, AND THAT IS THE REAL FINDING.** The
  non-convergence guard stops a boss it judges HOPELESS — but it grades on TYPE coverage, and against
  Psychic the party genuinely has Dark/Ghost/Bug answers, so `_boss_plan_is_hopeless` returns False
  and the bot simply keeps losing. ⇒ **it catches "wrong types" and is blind to "right types, too
  weak".** The 3 runs that died with a clean *"no super-effective answer"* diagnosis are the case it
  DOES handle; this is the case it does not, and it is the one that burns the most frames.
- [ ] ⚠ **TWO HYPOTHESES, NOT YET DISCRIMINATED — do not pick one without measuring.**
  (a) TEAM: the party is simply under-levelled/under-powered for a double boss.
  (b) BATTLE LOGIC: Tate & Liza is the story's one DOUBLE battle, and `KI-96`'s freshness invariant
  is **incomplete in doubles** — battle slot 0 encodes only the LEFT battler (decomp-verified
  2026-09-07), so a rotation aimed from a partly-stale order is unvalidated exactly here.
  ⭐ **The discriminator is cheap and already built:** run the `[KI96-REREAD]` drive against this
  fight and count rotations that hit the 240-press bound or log `DIFFER`. If rotations are clean, it
  is (a) and the answer is levels; if they wedge, (b) is contributing. ⛔ Do NOT grind levels first —
  that is the expensive arm, and it would mask (b) rather than rule it out.
- [ ] ⚠ Also worth pricing: a whiteout here costs the 117-step puzzle re-solve, so attrition at this
  boss is far more expensive per attempt than at any other. Detail: `ai-research-notes/2026-09-07-batch-blockers-RECON.md`.

### ✅ `#24-countermsg` — **CLOSED 2026-09-07: the counter guard now names WHICH rule admitted a species (`via move:Rock Throw@L15`); display-only.** ⛔ DO NOT REDO. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-10, R3 budget).

### `#24-counterprobe-rotted` — an offline counter-planner probe fails its OWN positive control (filed 2026-09-07)
- [ ] `probe_counter_candidates_offline.py` exits 1 with *"POSITIVE CONTROL — Norman finds Machop @
  FIERY_PATH: FAIL - the harness is broken... Ignore every other number this script printed."*
  ✅ RULED OUT as caused by `#24-countermsg`: the probe never calls `summarise_candidates`, and that
  diff is confined to that one function (hunks at `:474` and `:487`). ⛔ It is **not registered in
  `run_gates.py`** — nothing runs it, exactly the rot `#24-reprosweepratchet` names. Either repair its
  ROM stand-ins and register it, or delete it; **an ungated probe that lies is worse than none.**

### `#24-countermsg-repro` — the display fix has no committed regression guard (filed 2026-09-07)
- [ ] `#24-countermsg` was verified by calling `summarise_candidates` directly, and a Tier 1 reviewer
  independently reproduced the output byte-for-byte — but **nothing was committed that re-runs it**,
  so a future edit can silently drop `answer_via` again or break the by-species dedupe and no gate
  would notice. ‼ A DISPLAY regression is invisible by definition: the program keeps working and only
  the reader is misled, which is precisely how this defect survived since `#24-movepoolcounters`.
  **Build:** a small `repro_countermsg_display.py` asserting (a) a `move:` answer renders its
  `via move:<Name>@L<n>` clause, (b) a `type` answer renders `(type match)`, (c) a missing
  `answer_via` renders neither and does not raise, (d) the displayed list keeps at most one row per
  species. Fault-test each arm, then register as a gate and bump the suite count.

### `#24-harness-faultgap` — no harness driver can exercise `request_mode_recovery` (filed 2026-09-07)
- [ ] ✅ VERIFIED: `handles_battle_faults` appears **ZERO times** in `tools/story-dev/story_harness.py`,
  so `request_mode_recovery` (`modules/battle_fault.py`) returns False for every driver and the caller
  raises — dropping to Manual **by design**. ⇒ every fix that routes through that channel (`KI-47`'s
  watchdog, the `KI-34` faint-chooser give-up, `KI-96`'s new bound) is **UNPROVEN BY DRIVING**, and a
  Manual drop in a harness log proves nothing about recovery — it is easily misread as proving it
  BROKEN. ⭐ `--driver storyresume` (added 2026-09-07) inherits `handles_battle_faults = True` from
  `StoryMode` and is the first driver that CAN test it. **Next:** drive a fault through it and show
  the mode consumes it (`take_pending_fault`) and derails recoverably instead of stopping.

### `#24-mossdeep-strandfixture` — the strand fix's RESCUE half has no fixture (filed 2026-09-07)
- [ ] `#24-mossdeepstrand`'s SAFE half is driven (Segment 18's `else` ran and `leave_the_gym()`
  no-oped off the gym map). Its RESCUE half needs a save standing on **MOSSDEEP_CITY_GYM (23,8) with
  BADGE07 SET**, and `at_mossdeep_leaders.ss1` was captured BEFORE the fight, so the badge is unset.
  **Build:** win the fight from `at_mossdeep_leaders.ss1` and capture immediately after the badge
  flag sets, before leaving the platform — that is precisely the state production reaches and the one
  no fixture covers. ⚠ The batch shows this fight is lost often (`#24-tateliza-attrition`), so the
  capture may need several attempts.

### `#24-rotatelead-precondition` — the RotateLead arm presses blind; the move path does not (filed 2026-09-07)
- [ ] ✅ VERIFIED contrast. `battle_action_use_move` presses **only** while
  `get_battle_controller_callback(battler)` is an input-accepting callback and stops the instant it
  is not (`battle_action_selection.py:976, 987-1000`) — so a refusal ENDS the loop. The
  `TurnAction.RotateLead` arm computes its aim pre-menu, scrolls blind, presses A blind, then mashes
  on `while get_game_state() == GameState.PARTY_MENU` — **which is true both while the menu waits for
  input AND while it prints a refusal at you.** `scroll_to_battle_action` likewise only compares
  `gActionSelectionCursor`; it never checks the action menu is live.
  ⇒ the loop cannot tell "not yet accepted" from "actively refused", which is why `KI-96` could spin.
  **Fix shape (independent of KI-96's cause):** gate the presses on the controller callback the way
  the move path does, and treat `gPartyMenuUseExitCallback` — set TRUE only on success
  (`party_menu.c:5852`) and read by `WaitForMonSelection` — as the accept signal, rather than "did
  the menu close". ⚠ MEASURE FIRST: `[KI96-WHY]` will say whether the refusal is per-slot or a
  trapped-mode refusal that no aim can satisfy.

### 🔶 `#24-truckleak` — MIXED: the FIX is in (sandbox), its ACCEPTANCE is not — a HELD BUTTON leaked across the reset boundary (filed + fixed 2026-09-07)
- [x] ✅ **ROOT-CAUSED AND FIXED.** `_held_inputs` is Python-side wrapper state (`libmgba.py:157`);
  `reset()` (`:198-199`) never clears it and it is re-OR'd every frame (`:581`). A run killed
  mid-walk by the frame budget leaked `Up`, which then beat the truck loop's `Right` forever.
  **Separation is total:** 867 dumps `held_buttons=[]` → truck exit in ~67 frames; 719 dumps
  `['B','Up']` → 858 failures, ZERO escapes. Cost: lane L03 lost **146 runs**.
  **Fix:** `reset_held_buttons()` before `context.emulator.reset()` in `StoryDebugResetMode.run`,
  printing the released mask. ⛔ Do NOT clear holds per-frame — navigation depends on them; the
  inverse failure is the batch filling with `Could not reach …` derails.
- [ ] ⚠ **`#24-truckleak-accept` — THE RESIDUAL, TRACKED ON ITS OWN SLUG.** The fix above is
  UNDRIVEN, and its acceptance MUST be **fault-armed**: a normal run holds nothing, so an
  unarmed run proves nothing at all. Hold `Up`+`B` deliberately at a run boundary, then require
  BOTH the `DEBUG-RESET: released leaked held inputs (0x00c0)` line (proving the arm was real
  AND the fix acted) and a truck exit (`INSIDE OF TRUCK(25,40) -> LITTLEROOT TOWN`) within 300
  frames. ⛔ Do not close `#24-truckleak` until this runs.

### ✅ `#24-lane-respawn-build` — **CLOSED 2026-09-07: a respawned lane records its ON-DISK build commit; fixed, gated, fault-tested.** ⛔ DO NOT REDO. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-10, R3 budget). ‼ Its live rule survives in `04-HANDOFF.md`: never promote or edit `sandbox-pokebot/` while a batch runs.

### 🔶 `#24-pcpingpong` — MIXED: the FIX is in (sandbox), its DRIVE is not — the heal deposited a mon then withdrew the SAME mon (filed + fixed 2026-09-07)
- [x] ✅ **FIXED + GATED + FAULT-TESTED.** `withdraw_precedence()` (pure, testable) defers the
  counter-withdraw when the visit was entered to FREE a seat. MEASURED 135/135 failures had a
  withdraw, 9/9 successes did not, and the withdrawn mon was **the same mon just deposited 135/135**.
  ⛔ Adds NO deposit — it removes an UNDO — so it stays inside the 2026-08-05/08-06 rulings
  (`POKEBOT_PC_ROTATION` still 0; catch policy and party cap untouched).
  Gate: `repro_heal_piggyback_reporting.py` (25 checks, all four branches incl. **the ordinary heal
  that must not move**); removing the fix turns it red.
- [ ] ⚠ **`#24-pcpingpong-accept` — THE DRIVE IS OWED.** 144 samples of perfect separation is a
  natural CONTRAST, not an executed A/B. Run both arms on a fixture that reaches HM03 with a full,
  Surf-incapable party carrying a spent counter. POSITIVE CONTROLS (all must APPEAR or the run never
  reached the code): `freeing ONE slot`, `depositing ONE mon to free a slot: <name>`, and
  `catching <sp> — it can learn the HM we need!`. PASS = `freed a slot (6 -> 5)` + the `DEFERRED`
  line, and NO `withdrawing <same name>` between them — **that identity is the discriminator**.
  FAULT ARM (`POKEBOT_PCPINGPONG_FAULT=1`) must reproduce the ping-pong.

### `#24-counterpids-never-retired` — a hunted counter is re-collected FOREVER (filed 2026-09-07)
- [ ] ✅ VERIFIED: `_hunted_counter_pids` has exactly two mutations — `story_mode.py:1327` (init) and
  `:1876` (`.add`). No `.clear`/`.discard`/`.remove` anywhere in either tree. ⇒ once a counter is
  registered it is withdrawn at EVERY subsequent heal, long after its boss is dead (L03 prints
  `BADGE: Balance Badge (Norman…)` on the line before the ping-pong). `#24-pcpingpong` stops it
  refilling a seat that was just emptied, but does NOT answer *when does an element leave this set?*
  ⚠ Likely retirement point: the boss it was hunted for is beaten. ⛔ MEASURE FIRST — a counter kept
  deliberately for a LATER boss would be lost by a naive retirement.

### ✅ `#24-hm07teach` — CLOSED. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-11, R3 budget; zero open boxes).
- [x] ⛔ DO NOT REDO. Detail in the archive and `07-CHANGELOG.md`.

### ✅ `#24-hm07funnel` — **CLOSED 2026-09-08, DRIVEN AT SCALE: Surf+Dive party-full went 7 of 53 → 0 of 49.** ⛔ DO NOT REDO. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-10, R3 budget). Detail: `07-CHANGELOG.md`.

### `#24-ch23preflight-gap` — the §Ch23 preflight omits Strength and Rock Smash (filed 2026-09-07)
- [ ] `assert_ch23_preflight` checks only `("Surf", "Dive", "Waterfall")`, but `chapters.py:265-274`
  records that Victory Road B1F needs **Strength AND Rock Smash**: a 2x2 boulder/rock interlock that
  opens only with BOTH (23 tiles reachable with neither, 66 with Strength alone, 23 with Rock Smash
  alone, 298 + the B2F warp with both). ⇒ a party missing either reaches the chapter and fails
  mid-cave instead of at a named preflight. ⚠ Deliberately NOT bundled with `#24-hm07funnel`: adding
  requirements makes the preflight STRICTER and could turn currently-passing driven fixtures red.
  Check the §Ch23 fixtures first, then add both to `field_move_carriers()` and the preflight.

### 🔶 `#24-whiteoutloop` — MIXED: the COUNTER is fixed and gated; the bot still cannot WIN the fights (filed + half-fixed 2026-09-07)
- [x] ✅ **THE COUNTER — ROOT-CAUSED, FIXED, GATED (sandbox).** `recoveries` had **no reset
  site anywhere** while its message said *"in a row"*: a LIFETIME loss quota. All 14 killed
  runs reached exactly #41 after whiteouts spread over a **median of 13 different towns**,
  while winning **86-96%** of their battles (one won 866 of 907 with an L51 lead). ⇒ a fuse
  on run LENGTH — kill rate 0% under 1.5M frames, 62% above 3.5M, and `MAX_FRAMES_PER_RUN`
  (5,000,000) was never reached by ANY of the 61 runs. ⛔⛔ **FALSE AS OF 2026-09-09 — MEASURED 6 FIRINGS.** `grep -rho "per-run frame budget exhausted" x4-runs/*/L0*/stdout.txt | wc -l` = **6** (overshoot ≤10,149 frames, 0.2%). ‼ AND THE BIGGER POINT: `MAX_FRAMES_PER_RUN` lives at `story_mode.py:4914`, inside **`StoryEndlessResetMode` — the BATCH HARNESS**. Production `StoryMode` has **no total-frame budget at all**, so in a real run the per-call `MAX_TRAINING_FRAMES` ceiling is the ONLY pre-emptive bound in existence. ⛔ Do not argue from run-budget headroom: at the 16 Ch23 refusals the median run had already burned 86% of it (median spare **707,123** frames against a mean training bill of **1,083,258** solo / **2,164,009** with the 2-way split). FIX: `whiteout_budget()` (PURE) keys
  it to CONSECUTIVE whiteouts at ONE location. GATE #44 `probe_whiteout_budget.py` replays
  the 14 real sequences: **0 of 14 still killed**, a stuck run and a blind run both STILL
  stopped at #41, and three fault arms fire. ⛔ DO NOT rewrite it to use `_progress_sig()` —
  that contains `total_exp`, which grows on the walk back, so it would reset every time and
  DELETE the guard (FAULT ARM 3 fails exactly that).
- [ ] ⛔ **THE OTHER HALF IS OPEN — see `#24-regimeb-noescalation`.** The counter fix stops
  runs being killed for playing long; it does NOT make the bot win. ⚠ EXPECT the failure to
  MOVE, not vanish: runs that used to die at #41 will now run on to some later blocker.
- [x] ⭐ ORIGINAL QUESTIONS, ANSWERED (kept as history): `Story: too many whiteout recoveries in a row —
  stopping so I don't loop forever. Check the team/route.` — 14 of 53 ended runs in the full 8-hour
  batch `20260907-113851` (26%), up from 2 of 17 before, because runs now survive long enough to
  reach it. **Never investigated.**
- [ ] ⭐ FIRST QUESTIONS (do not guess): WHERE do the whiteouts happen — one boss, or scattered? Is
  the cap itself reasonable, or does it fire on a run that would have recovered? Is this the same
  "right types, too weak" shape as `#24-tateliza-attrition`, which the counter-guard cannot see
  because it grades on TYPE coverage only? ⚠ Two of the deepest runs in the PREVIOUS batch died at
  Tate & Liza with 24 and 11 losses, so start by checking whether these 14 share a location.

### `#24-regimeb-noescalation` — the back half of the game has NO loss-adaptation at all (filed 2026-09-07)
- [ ] ⛔ **VERIFIED IN OUR OWN TREE, not taken from an agent.** There are **8** `*_fight` configs and
  **8** `_prepare_for_fight` call sites; the last is `winona_fight` (badge 6, `story_mode.py:3729`).
  Every chapter after it is dispatched as a bare `if not _done(...): yield from chapter()`. All six
  late chapter modules — `mossdeep_gym`, `sootopolis_gym`, `victory_road`, `pokemon_league`,
  `seafloor_cavern`, `space_center` — contain **ZERO** uses of `_prepare_for_fight`, `_defeat_counts`
  or `_boss_plan_is_hopeless`.
- [ ] ⇒ **From badge 7 on, N whiteouts is N IDENTICAL losses.** No level escalation, no plateau
  detector, no counter-hunt, no second wind, no honest stop — the machinery that badges 1-6 get.
  Survival mode cannot help: it is gated on `encounter is not None`, i.e. WILD battles only, and a
  gym leader is a trainer battle by construction.
- [ ] ⚠ **DO NOT SCOPE FROM THE TERMINAL-LOCATION STATISTIC** — it is a sample of size one per run
  (`08-MISTAKES.md` 2026-09-07). Plot the whole distribution of loss sites first.
- [x] ⛔⛔ **THE ‘CHEAPEST FIRST SLICE’ IS REFUTED (2026-09-08) — ⛔ DO NOT BUILD IT. CLOSED.** Arming it was measured to be the wrong first move; the refutation stands.
      📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` (2026-09-18, R3 line budget; nothing deleted)** — the full refutation and its measurements are there.
- [x] ✅ **THE MONEY CONTRADICTION THIS ITEM RECORDED AS OPEN IS NOW SETTLED, FROM THE DECOMP.**
  `src/overworld.c:358` — `DoWhiteOut()` does `SetMoney(&money, GetMoney(&money) / 2)`. `MoneyLoss`
  has **zero** hits in `pret/pokeemerald`; the `sWhiteOutMoneyLossMultipliers` table is FireRed's
  (`pokefirered/src/overworld.c:227`). ⇒ **`victory_road.py:446` was RIGHT; `story_mode.py`'s
  boss-training comment was WRONG** and has been corrected in sandbox. ⚠ The CONSEQUENCE is filed
  separately as `#24-bosstrainingeconomics` — the fact is settled, the decision is not.
- [ ] ⭐ CHEAPEST FIRST SLICE, and it is not the escalation: **90% of Mossdeep Gym whiteouts respawn
  in LILYCOVE** (148 vs 16) because the Mossdeep Poké Center is never registered before the gym —
  the only two `heal_in_pokemon_center(PokemonCenter.MossdeepCity)` calls are in `seafloor_cavern.py`
  and `space_center.py`, both chapters that run AFTER it. Cost: a median ~8 min per retry.
  ✅ **VERIFIED MYSELF 2026-09-07** (was agent-reported): `heal_in_pokemon_center(PokemonCenter.MossdeepCity)` has EXACTLY TWO call sites — `seafloor_cavern.py:884` and
  `space_center.py:185` — and both chapters run AFTER the gym. And of **139** whiteouts that
  STARTED on a Mossdeep map, only **13** respawn at Mossdeep: ~91% land elsewhere (my split
  is ROUTE 124 81 / LILYCOVE 45, because ROUTE 124 is the Lilycove→Mossdeep surf corridor and
  a 'first map after recovery' proxy catches transit; the agent read 148/16. ⇒ **the exact
  split is proxy-dependent, the ~90% direction is not.**)
- [ ] ⚠ ALSO REPORTED, UNVERIFIED: `story_mode.py:1995` justifies boss-training mode with *"whiteout
  money loss is level x badge-payout — cheap"*, which is the FRLG model; our own
  `victory_road.py:446` records that Emerald's `DoWhiteOut` does `SetMoney(money / 2)`.
  ✅ **THE INTERNAL CONTRADICTION IS VERIFIED 2026-09-07** — both lines exist as quoted, and
  they cannot both be right. ⛔ **WHAT IS *NOT* VERIFIED IS WHICH ONE THE GAME AGREES WITH**:
  that needs the decomp, not our own two comments. Settle it there BEFORE re-deriving the
  economics of deliberately farming whiteouts (`story_mode.py:1996` engages boss-training
  ~98% of the time on that premise, and each attempt spends a unit of the whiteout budget).


### `#24-bosstrainingeconomics` — boss-training re-loses on purpose, and EVERY loss halves all money (filed 2026-09-08)
- [ ] ⛔ **THE PREMISE WAS FALSE AND IS NOW CORRECTED IN CODE.** `story_mode.py`'s boss-training
  comment justified deliberately re-attempting a boss as a training vehicle with *"whiteout money
  loss is level x badge-payout — cheap"*. That is **FireRed's** model. Emerald halves ALL money on
  every whiteout (`src/overworld.c:358`, decomp-read 2026-09-08). The comment is fixed; the STRATEGY
  is untouched.
- [ ] ⭐ **MEASURED EXPOSURE:** the *"boss-training mode — local wilds …"* line fires **1,477 times**
  across `20260907-203713` + `20260907-113851` (16 lane files, total occurrences). Each engagement is
  a deliberate loss, i.e. a halving.
- [ ] ⛔⛔ **DO NOT ACT ON THIS YET — THE COST IS UNMEASURED AND THE INSTRUMENT DOES NOT EXIST.**
  Money is not written to any log, and the natural proxy is unusable: `provision_poke_balls`'s
  *"too low on money to restock"* goes to `context.message` (a UI field), **not** `console.print`, so
  it never reaches `stdout.txt`. A zero count there means NOT LOGGED, not NEVER HAPPENED.
  ⇒ **FIRST DELIVERABLE IS AN INSTRUMENT, NOT A FIX**: log money at run start, at each whiteout, and
  at each mart visit. Only then is "boss-training is too expensive" a claim rather than an inference.
- [ ] ⚠ **THE ONE HARD DATA POINT SO FAR:** 5 runs derailed on *"Cannot hunt a Surf learner: no Poké
  Balls and no money to buy any."* Real, but 5 — nowhere near enough to indict a strategy that fires
  1,477 times. ⛔ Do not scope this from that number.
- [ ] ⭐ **AND THE COUNTER-ARGUMENT, so it is not re-derived:** boss-training exists because a lost
  attempt that KOs two of the boss's mons pays ~1,200 XP against ~145 XP for a local wild, and Gen 3
  **does** keep mid-battle XP through a whiteout (that half of the comment is true). The strategy may
  well still be correct at half-money. **Price it; do not assume either way.**

### `#24-ch23training` — TOP BLOCKER, ROOT-CAUSED 2026-09-08 (16 of 49, 32.7%) — ⛔ the guard is the MESSENGER
- [x] ✅ **ROOT CAUSE VERIFIED.** `victory_road.py:1937` refuses when ANY single under-target battler
  costs more than `MAX_TRAINING_FRAMES = 250_000` to reach `TRAIN_TARGET = 47` on `WILD_MAX = 40`.
  ⚠ **"alone" does NOT mean the mon is alone in the party** (all 16 failures have 2+ members) — it
  means *that one mon by itself*. Inverted levels: **Marill ≈L13, Slugma L17, Mightyena ≈L20,
  Shedinja ≈L23**, against a leg calibrated on a curated party with an **L40 floor**.
- [x] ⭐ **THE BOT CREATES THEM AND THEN PINS THEM.** `ensure_hm_learner` CATCHES a wild mon at wild
  level to carry an HM; HMs cannot be forgotten in Gen 3; `team_policy.py:147-149` exempts a **sole
  HM carrier** from deposit BEFORE any level test. `battler_identities` (`victory_road.py`'s `battler_identities` *(cited `:1824` until 2026-09-16, when an unrelated 6-line comment edit above it shifted the symbol to :1830-1846 and `audit_doc_citations.py` caught it — ⛔ cite the SYMBOL, the line is a sighting aid)*)
  then admits it — `BENCH_SPECIES` is only `("Zigzagoon","Linoone","Castform")`, 3 hardcoded names
  against 6 observed species. ‼ Already measured in `team_policy.py:8-16`: *"35% of badge moments
  carried at least one mon 15+ levels below the team max"*. My recount: **86.9%/78.9% of runs.**
- [x] ⛔⛔ **SIX NOW — "ROUTE THE MULE TO A LEVEL-MATCHED AREA" IS KILLED ON ARITHMETIC (2026-09-09).**
  Adversarial pass, five angles. **No ground in Emerald can clear the ceiling from L13.** The per-call
  budget is `250,000 / FRAMES_PER_WILD_BATTLE(1433)` = **174 battles**; L13→L47 needs 81,301 exp, i.e.
  **467 xp/battle, i.e. a wild level of ≥65**. The highest wild level the project's own encounter cache holds is **50**
  (⚠ *this said 44 — an undercount; corrected 2026-09-09 by a reviewer*). **Either way it is far short of 65**, so the conclusion is untouched.
  ‼ **AND A SEPARATE DEFECT SURFACED WHILE CHECKING IT — FILED, NOT FIXED:** those high entries carry **FRLG-only map names** (*"Artisan Cave"*, *"Desert Underpass"*) inside a **BPEE0 Emerald** cache, which points at a map-name lookup mismatch for high bank/map indices (`modules/pokemon.py`'s shared gen3 name list). ⇒ any analysis that trusts `map_name` from `cache/encounter_index_BPEE0.json` may be reading a wrong label. Not this item's bug; do not fix it here. Relocating moves the number the WRONG way — VR1F 406,972 → ROUTE121 580,365 →
  ROUTE117 **1,160,730**, all against an unchanged 250,000.
  ‼ **AND THE PREMISE WAS WRONG:** `best_training_area(13)` returns **ROUTE117 (L13-14)**, never a
  L25-28 area — `if team_level < lo - 1: continue` rejects every higher band. The picker is
  level-matched by construction, so it can only ever pick something POORER than Victory Road.
- [x] ⛔⛔ **THE ESTIMATOR IGNORES THE EXP SPLIT — ‼ ALREADY FILED 2026-09-08 (see the "UNDERSTATES TRAINEE COST ~2x" bullet above); WHAT IS NEW IS THE CONSEQUENCE NOBODY APPLIED.** That bullet ends *"any future costing of a catch-time top-up must double the estimate"* — and this item's own FIX DIRECTION below never did. ⇒ do not re-file this fact; the value here is the arithmetic it implies:
  `training_areas.estimate_frames_to_level` computes `xp_per_battle = CAL * wild_level / 7` with **no
  division by participants** (verified in source), i.e. it models a SOLO fight — while its own caller
  `train_team` sets `set_swap_train(True)` (`early_game.py:2026`), putting TWO mons in the battle and
  halving the share. ⇒ **every training cost estimate is up to 2x optimistic about the path that
  calls it.**
  ⭐⭐ **CONSEQUENCE FOR THIS ITEM: THE "BAR IS L35" MAY BE WRONG.** Recomputed with a model that
  reproduces all five published figures EXACTLY (L13=406,972 / L20=384,044 / L26=345,353 /
  L30=308,095 / L35=243,610), then halved for two participants:
  ```
  arrival   SOLO (modelled)   2-WAY SPLIT      ceiling 250,000
    L35           243,610         487,220      REFUSE
    L40           160,496         319,559      REFUSE
    L42           118,939         237,878      PASS
  ```
  ⇒ L35 is the SOLO bar; the real bar looks like **L42**, and this item's planned *"catch at L26 AND
  train the remainder to ~L39"* would **still refuse**.
  ⚠ **NOT PROVEN, AND THE LIMIT IS HONEST:** the split is 2 only when swap-training actually fires; it
  does not fire when no capable finisher exists, and then the solo model is right. The true cost lies
  BETWEEN the two columns.
- [ ] ⛔ **THE DECIDING MEASUREMENT IS NOT AVAILABLE FROM EXISTING LOGS — IT NEEDS INSTRUMENTATION.**
  I looked: **0** logs in `sandbox-pokebot/profiles` + `tools/story-dev/x4-runs` contain BOTH
  `-> RotateLead` telemetry AND an exp readout. Production rotation logs carry `party=None` and no exp
  field at all. ⇒ **NEXT DELIVERABLE IS ONE LOG LINE, NOT AN ANALYSIS**: record the trainee's
  `total_exp` BY PID before and after each wild battle in a run where swap-training fires, and divide.
  That single number decides whether this item targets **L35 or L42** — i.e. whether its next build
  works or repeats this failure one level up.
- [ ] ⚠ **CARRY-FORWARD HAZARD FOR WHOEVER TOUCHES §Ch23's TRAINING:** `WILD_MAX = 40`
  (`victory_road.py`) and `grass=TRAIN_SPOT_1F` are **independent hardcodes**. A relocation that edits
  one and not the other prices the grind at L40 while grinding at L14 — that is `KI-28`'s 19.9M-frame
  livelock with its only guard blinded. Also `_MAX_TRAINING_TRAVEL_LEGS` (4) is never referenced by
  `victory_road.py` or `early_game.py`, so a relocation bypasses the travel cap silently.
- [ ] ⛔ **FIVE FIXES ARE MEASURED WRONG — DO NOT PROPOSE ANY OF THEM:** benching low mons,
  stepping the target, raising the ceiling, training elsewhere, relaxing the estimator. Each was
  killed by evidence, not opinion; the reasons are in `07-CHANGELOG.md` 2026-09-07/08.
- [x] ⛔⛔ **SECOND, INDEPENDENT REASON STEPPING COULD NEVER WORK (review, not drive):**
  `team_is_ready(target)`'s LEVEL loop uses `target` but its **CRUNCH loop does not** — it tests
  `mon.level < CRUNCH_LEVEL`(=47) unconditionally, and it is the terminal gate. ⇒ any sub-target < 47
  RAISES whenever a sub-47 Mightyena lacks Crunch, which the fixture has ⇒ **it would have broken the
  CONTROL.** ⭐ **STANDING TRAP: `team_is_ready` IS NOT SAFELY CALLABLE WITH A SUB-TARGET.**
- [x] ⛔⛔ **THE BENCH FIX IS REFUTED — DO NOT RE-PROPOSE IT.** An adversarial review returned
  UNSAFE: on the chapter's OWN fixture (`Sceptile L51 / Swellow L42 / Wailmer L40 / Mightyena L44`)
  a `party_max - 8` line benches **Wailmer and Swellow — two of the four mons the shipped run
  trained to L47** — and Wailmer is the sole carrier of Dive AND Waterfall (`victory_road.py:760`).
  It also turns a LOUD refusal SILENT (a benched Poochyena never evolves, so the Crunch guard keyed
  on `species.name == "Mightyena"` never fires ⇒ Phoebe's all-Ghost team with no Dark move, and
  there is no Dark TM in Emerald), and an empty battler set returns `(True, [])` ⇒ a broken run ✅✅ **CLOSED 2026-09-08 — FIXED AND GATED BEFORE THE PREDICATE IS TOUCHED.** `team_is_ready` now refuses loudly on an empty battler set (`victory_road.py`, +24/−1), locked by **gate #48 `probe_empty_battler_guard.py`** (4 arms; fault-tested — disable the guard and it exits 1, restore byte-identical and it exits 0). ⛔ This does NOT advance the item: the ROLE predicate is still unbuilt. It removes the trap that would have made a bad predicate look like a SUCCESS. Rationale + raw evidence: `06-DECISIONS-LOG.md` 2026-09-08.
  grades PASS. `team_policy.py:42-59` had ALREADY measured this predicate over 363 parties: *"59%
  would be left with FEWER THAN 3 mons"* — which is why that module CAPS it and my proposal did not.
  Full detail: `07-CHANGELOG.md` 2026-09-08.
- [x] ⛔⛔ **STEPPING IS ALSO REFUTED — BUILT, DRIVEN, REVERTED 2026-09-08.** MEASURED: **69 battles,
  Marill lead at 0/43 HP, STILL L13.** A L13 mon cannot survive VICTORY_ROAD_1F's L36-40 wilds and a
  fainted mon earns nothing ⇒ it can never level there **at any step size**.
- [x] ⭐⭐ **⇒ THE GUARD IS CORRECT, FOR A REASON ITS MESSAGE DOES NOT STATE.** It says "too
  expensive"; the truth is "not survivable here", and the two coincide BY CONSTRUCTION — a mon over
  the 250k ceiling is ~20+ levels under the wild band. **The ceiling is a PROXY for survivability.** ⛔⛔ **WITHDRAWN 2026-09-09 — THIS RESTED ON A FABRICATED MEASUREMENT.** The mule was NOT one-shot: measured, it started **66 of 72** battles at full 43/43 and fought 2.3 turns each. It gained nothing because the DRIVER never installed swap-training (`Ch23TrainMode` returns `StoryItemBattleStrategy`; 232 turn decisions, 0 RotateLead), not because it could not survive. ⇒ **the ceiling is a COST test, not a survivability proxy.** See `07-CHANGELOG.md` 2026-09-09.
- [ ] ⇒ **BOTH LEG-LOCAL FIXES ARE DEAD; THE DEFECT IS UPSTREAM — see `#24-lowlevelmules`.** The bot
  catches HM mules and counters at wild level and never trains them; by Victory Road no local remedy
  exists.
- [ ] ⭐ **AND THE PREMISE IS SMALLER THAN IT LOOKS:** at the measured **1032 frames/sec**, Marill's
  406,972 frames is **~6.6 minutes**; all six mules ≈ **44 minutes**. The refusal is rejecting a
  sub-hour grind — a per-call-ceiling artefact, not an economics fact.
- [x] ✅ **THE DISCRIMINATOR EXISTS — ⛔ DO NOT REBUILD IT.** `--inject-hmmule` adds an L13 Marill
  to an otherwise-ready party; with `POKEBOT_CH23_ESTIMATE_ONLY=1 --driver ch23train` the arms differ
  in seconds (CONTROL worst 217,816 passes · ARM A worst 406,972 refuses, shared mons identical).
  406,972 is the EXACT production figure. Evidence: `acceptance-2026-09-07/EVIDENCE.md`.
- [x] ⭐ **ACCEPTANCE CRITERIA (kept — they are what KILLED the step fix):** ARM A must PASS · the
  CONTROL must be UNCHANGED · a genuinely impossible case must STILL refuse. Stepping failed the
  first two; ⚠ `ESTIMATE_ONLY` returns BEFORE the raise, so it cannot grade a real run.
- [ ] ⛔⛔ **THE TRAP IN THE CODE YOU WILL MIRROR.** `Ch24Grind`'s step loop
  (`story_harness.py:15236-15246`) is the reference implementation — `sub = min(target, low + STEP)`,
  `MAX_STEPS/MAX_RETRIES = 24/2`, and a **"refuse to spin"** break when a step moves nobody. **Copy
  those.** ⛔ **DO NOT copy its `except Exception as error:`** — that is legitimate in a HARNESS
  driver (a refusal IS the reading) but in the CHAPTER RUNNER it would swallow `StoryAbort` and
  re-open the abort-swallow debt that gate #27 ratchets at baseline 23. Production must
  `reraise_if_aborting(error)` first, or not catch at all.
- [ ] ⚠ **AND THE CALL SITE IS THE CHANGE, NOT THE FUNCTION.** `train_for_victory_road` ALREADY takes
  `target=` (`victory_road.py:1872`), so stepping is a CALLER concern. The site is the chapter runner
  at `victory_road.py:3290`. ⛔ Nothing about `battler_identities`, `team_is_ready` or
  `MAX_TRAINING_FRAMES` needs to change — and Decision 3 explicitly rejected touching the constant.
- [ ] ⚠ **NOT BUILT DELIBERATELY — THERE IS NO DISCRIMINATOR YET.** No fixture reproduces a low-level
  mule party, `--inject-*` is preset-only, and `battler_identities` feeds BOTH `team_is_ready` and
  the estimator (a shared path). ⇒ ⭐ **STEP 1 IS THE FIXTURE, NOT THE FIX:** capture a save whose
  party holds a sole-HM-carrier 15+ levels below the max (or add a harness inject for one), and show
  the two arms DIFFER on it before changing `battler_identities`.

### `#24-marillskew` — ⚠ my own `#24-hm07funnel` fix appears to cost 2.7x more Marill (filed 2026-09-08)
- [ ] **MEASURED over distinct RUNS (not log-line mentions):** Marill 4 of 61 (6.6%) → **10 of 57
  (17.5%)**; every other species flat. Marill is the refused mon in **9 of 16** `#24-ch23training`
  failures. ⭐ The innocent explanation is REFUTED: at the SAME depth band (party max L50+, 18 runs
  each) it is still **3 → 8**. ⚠ n=18/cell — SUGGESTIVE, not proven (p ~ 0.1).
- [ ] ⛔ The DIRECT mechanism is also refuted: `pick_land_hm_slot` excludes Waterfall-capable species
  and Marill learns Waterfall, so it can never SELECT one. ⇒ the path is INDIRECT. Leading
  hypothesis, UNVERIFIED: spreading land HMs across more mons creates more **sole-HM-carrier
  exemptions**, and each such mon becomes permanently undepositable.
- [ ] ⇒ **NET: the funnel fix STAYS** (preflight 11→0, Surf/Dive 7→0). This is a cost to track, not a
  reason to revert. Settle it by correlating `teaching Rock Smash/Strength to <X>` against the
  refused PID in `x4-runs/20260907-203713/L0*/debug-logs/`.

### `#24-cutscenestall` — NEW in the post-fix batch: 4 of 49 runs (8.2%) (filed 2026-09-08)
- [ ] `Cutscene did not end after N frames (controllable=False, script_active=True).` **Zero
  occurrences in the BEFORE batch**, so this is genuinely new rather than a share-of-a-different-mix
  artefact. ⚠ Also new: `per-run frame budget exhausted` (2 of 49). ⛔ Both are UNINVESTIGATED —
  check whether either traces to this session's changes before assuming they are pre-existing.
### `#24-tier2audit-residue` — 10 doc defects a cold-start audit found and I did NOT fix (filed 2026-09-08)
- [ ] ⭐ **THE SYSTEMIC CAUSE, worth more than the list:** *a status change gets written where the
  WRITER is looking and not where the READER will look.* Four instances were fixed 2026-09-08 (the
  `➡➡➡` headline, `KI-81`'s header, "live frontier is `KI-96`", `KI-97`'s header). These remain:
- [ ] **(a) THREE "ARCHIVED VERBATIM … nothing deleted" claims where ~399 lines NEVER MOVED** — `05`
  `KI-76` (~165), `KI-66` (~163), `KI-50` (~80). The archive holds copies (`28`), so this is
  DUPLICATION, not archival, and the stated R3 budget relief never happened. ⭐ This is exactly
  `archive_doc_block.py`'s **INVARIANT D** class, in history predating it. Either move them or
  retract the claim.
- [ ] **(b) `05:430-431` a KI-26 header wrapped across two `##` lines** ⇒ a PHANTOM section that
  structurally owns KI-26's body; any tool walking `##` boundaries mis-attributes it.
- [ ] **(c) `05:28-29` the file's own navigation grep is wrong for the 3rd time** — it prescribes
  `^## KI-[0-9]+` (66) and misses 10 backticked headings (`^## \`KI-`); true total ~75.
- [ ] **(d) promotion-paste residue in `KI-93` / `KI-95` / `KI-79`** — headers say PROMOTED while
  bodies still say "unpromoted / still open"; `KI-95` has a runaway parenthetical whose last rendered
  words are the opposite of its Status line. **(e)** `KI-47:890` + `KI-8:136-137` still commission a
  probe `KI-96` ANSWERED; `05:2738-2740` is a 4th live copy of the KI-96 census instruction.
  **(f)** `05:16/:22` claims everything from KI-6 on is our own code — refuted by KI-83/88/89
  ("upstream helper"). **(g)** `05:1509` MIXED heading has an unmarked bullet (`KI-60`).
  **(h)** `KI-35` header carries no status in a file whose preamble says "open problems only".
  **(i)** `KI-73`'s sub-heading asserts what the line beneath it corrects. **(j)** the preamble says
  fixed issues are removed, but the 2026-07-29 ruling retains sandbox-only fixes — ≥16 promoted
  entries are retained; the file asserts both.

### `#24-lowlevelmules` — the REAL defect behind `#24-ch23training`: caught mons are never trained (filed 2026-09-08)

- [x] ⭐⭐⭐ **ROOT CAUSE FOUND AND VERIFIED IN CODE 2026-09-08 — IT IS AN ABSORBING STATE, AND THIS
  ITEM'S TITLE UNDERSTATES IT.** `story_mode.py:2135-2137 (SANDBOX; the same logic sits at ~:2119 in custom-pokebot — a fork mixup, corrected 2026-09-10)` (`TRAIN_CATCHUP_GAP = 6`, `:1136`):
  `to_train = {i for i in battlers if party[i].level >= target - 6}`, with `target` drawn from the
  fight's own band (`:1945`). ⇒ a battler more than 6 below the band is excluded from training, so it
  gains nothing, so it is further below the NEXT band, so it is excluded again — **permanently, with
  nothing in the tree pulling it back**. `team_policy.py:11-14` had already recorded the symptom
  (*Makuhita L8 → L9 across FIVE badges*) without naming the mechanism.
  ⇒ **the HM mule is not special — it is the most FREQUENT victim of a general trap.**
- [x] ⭐⭐⭐ **AND THE BIGGER STRUCTURAL FINDING: THERE IS NO TEAM TRAINING AFTER WINONA.** Verified by
  exhaustive grep: **8** `"band"` configs and **8** `_prepare_for_fight` call sites, the last being
  `winona_fight` (`story_mode.py:3753`, `:3758`). **No band, no prep, and no `train_team` call exists
  for Tate & Liza, Juan, the E4, or §Ch16-§Ch22.** The only `train_team` callers in the tree are
  `counter_hunt.py:782` (the hunted counter only), `victory_road.py:2004` (§Ch23 itself),
  `story_mode.py:1988` (single-mon top-up), `:2240` (band prep) and `:3145` (§Ch6 rival).
  ⇒ **the party crosses ~9 chapters from Winona's L29-33 band to §Ch23's L47 requirement with NO
  training mechanism at all** — the max climbs organically to L49-59 while any laggard receives
  nothing. §Ch23 is simply the first place that requires the WHOLE team.
- [x] ⭐ **MEASURED — what §Ch23 sees** (18 runs of `20260907-203713` that reached it, using the code's
  own bench predicate): lowest battler **median L13 (L12-23)** against party max **L49-59**;
  **0 of 18** clear L35 on every battler. Lowest-battler species: **Marill 9**, Slugma 2, Abra 2,
  Shedinja 1, Ninjask 1, Mightyena 1, Kadabra 1, Poochyena 1. ⇒ Marill is exactly HALF; the rest are
  **late catches, not HM mules**, so an HM-scoped fix can address at most half the population.
- [x] ⛔⛔ **REFUTED — "acquire a Marill on Route 104 at §Ch3 so it is never a mule".** Killed by
  adversarial review on six counts, each verified in code. The two that are fatal on their own:
  (a) `pick_land_hm_slot` (`early_game.py:4744-4793`) **skips any species that can learn Waterfall**
  — Marill does, so it is **structurally ineligible for Strength/Rock Smash forever**; and
  (b) Route 104 is in **`PENDING_GRASS` with spin tile `None`** (`training_areas.py:57-58`), never
  swept, and `_hm_hunting_grounds` skips `tile is None`. Also: no ball supply at §Ch3
  (`provision_poke_balls` → `RUSTBORO_MART`, §Ch4); until it holds an HM it has **no deposit
  exemption** (`team_policy.py:147-149`) and is sorted FIRST for boxing; and on Mudkip runs the
  starter wins Surf (`hm_learner_slot` ranks by LEVEL) so the slot is a passenger.
- [x] ⛔⛔ **REFUTED — "the earlier catch-time refutation used the wrong bar".** The reasoning was that
  a fresh catch need not reach L35, only `target - 6` of the NEXT fight, after which `to_train`
  carries it. **The next fight is WINONA AND THERE IS NOTHING AFTER IT** (finding above), so the
  ceiling this mechanism can deliver is `randint(29,33)` = **L33**. Reproducing the project's own
  measured sweep from `estimate_frames_to_level` (5 of 5 exact matches at L13/L26/L30/L35) and filling
  the gap: **L33 needs 272,270 frames against the 250,000 ceiling — it STILL REFUSES, by 22,270.**
  ‼ My "rides to ~L47" was a misreading: **L47 is `TRAIN_TARGET`** (`victory_road.py:492`), the level
  §Ch23 trains *to*, not one the band curve delivers.
- [x] ⛔⛔ **THE B1F 'LEAD' IS ALSO REFUTED — I RECORDED IT AS LIVE WITHOUT CHECKING THE HISTORY FIRST.** `07-CHANGELOG.md` (2026-09-08, earlier the same day) already killed it under *"move the training somewhere better"*: **B1F is richer (959.2 vs 768.0) but its ladder is 44 wp PAST WALLY'S TRIGGER — the better ground is gated behind the fight the training is for**, and readiness must pass BEFORE Wally. ⇒ **seven refuted fixes; no cheap lead remains.**
  `victory_road.py:1942-1943`'s refusal message already says: *"train on B1F AFTER Wally (950.8
  EXP/battle vs 1F's 775.6)"* — a **1.226x** economy. At B1F rates L33 costs ~222k, which **passes**.
  ⛔ It is NOT free: it depends on (1) KI-84 being fixed for the gym-prep path, (2) the carrier being
  a Fast-curve species (Marill yes; a **Lotad** carrier is Medium-Slow and raises the bar L35 → L38),
  and (3) drawing L33 rather than the L31 expectation. ⚠ Check first whether this is the already-
  refuted *"training elsewhere"* before proposing it.
- [x] ⛔ **KI-84 FIRES ON THE GYM-PREP PATH, and this corrects an attribution.** At Winona the
  established battlers are all >= target, so `need` (`story_mode.py:2126`) collapses to the single
  mule slot, i != 0 — literally the documented-broken `train_team(slots={i})` case
  (`victory_road.py:1970-1982`). ⇒ the *Makuhita L8 → L9* evidence is the **KI-84 +1-level
  signature**, not purely the catchup gap. ⭐ The multi-slot case DOES converge while slot 0 is also
  below target (the swap keeps the member set closed) — that is the early game, not Winona.
- [x] ⛔ **THE ESTIMATOR UNDERSTATES TRAINEE COST ~2x.** `estimate_frames_to_level`
  (`training_areas.py:571-580`) models FULL XP, but `train_team` enables swap-train
  (`early_game.py:2009`) which this project's own comment calls *"half-XP swap-training"*
  (`story_mode.py:2106-2107`). Any future costing of a catch-time top-up must double the estimate.
  ‼ And `story_mode.py:2240` (band prep) has **no estimate gate at all**.
- [ ] ⛔ **UPSTREAM, AND ALREADY MEASURED — `team_policy.py:8-16`:** *"35% of badge moments carried a
  mon 15+ levels below the team max… the answer was in the party the whole time and never became
  usable."* My recount over two batches: **86.9% / 78.9% of runs** ever carried such a mon.
- [ ] ⭐ **WHY FATAL ONLY AT §Ch23:** `ensure_hm_learner` CATCHES a wild mon for an HM;
  `team_policy.py:147-149` then EXEMPTS a sole carrier from deposit (correctly — boxing the only Surf
  carrier soft-locks). Created, pinned, never trained; §Ch23 is where its level is first REQUIRED.
- [x] ⭐⭐ **THE BAR IS MEASURED: L35.** Sweep (`POKEBOT_MULE_LEVEL` 13/20/26/30/35, ESTIMATE_ONLY,
  seconds per arm): Marill needs 406,972 / 384,044 / 345,353 / 308,095 / **243,610** frames — the
  §Ch23 refusal clears only at **L35**. (Pre-registered prediction "L34-L35" HELD.)
- [x] ⛔⛔ **NEITHER LEVER ALONE REACHES IT.** Catch-time training buys ~+15 (L13→L28). The whole-game
  GRASS ceiling for a water-HM carrier is Shoal Cave L26-32 / Route 120 L25-27 — **both under L34**;
  Route 120 maps to the L26 arm at 345,353, **still refuses**. ⇒ `#24-divegroundroute120` alone does
  NOT clear §Ch23 (it is still a real win: 236 battles vs 588, 379 wp vs 1,055).
- [ ] ⇒ ⛔⛔ **FIX DIRECTION — ITS ARITHMETIC IS STALE AND IT FAILS ONCE CORRECTED (2026-09-09).**
  It reads *"L26 catch + 250k budget at wild-28 → ~L39, clearing L35"* — computed at FULL xp,
  ignoring the *"must double the estimate"* instruction in this item's OWN bullet above.
  ‼ Redone with the split applied (model reproduces all five published figures exactly): the
  first arrival level clearing the 250,000 ceiling is **L42, not L35**, and 250k at wild-28
  from L26 buys far less than the ~L39 claimed. ⇒ **CATCH-HIGHER + TRAIN-THE-REMAINDER, AS
  SPEC'D, WOULD STILL REFUSE.**   ✅✅ **DECOMP-VERIFIED AND MEASURED 2026-09-09 — THE PAYOUT IS DIVIDED AMONG PARTICIPANTS.**
  ⭐ **THE MECHANISM, from the decomp (settles it independently of any log):** `Cmd_getexp`,
  `pret/pokeemerald` `src/battle_script_commands.c:3292-3324` —
  ```c
  for (viaSentIn = 0, i = 0; i < PARTY_SIZE; i++)   ...   viaSentIn++;   // mon that were SENT IN
  calculatedExp = gSpeciesInfo[...].expYield * gBattleMons[gBattlerFainted].level / 7;
  *exp = SAFE_DIV(calculatedExp, viaSentIn);            // no EXP Share
  *exp = SAFE_DIV(calculatedExp / 2, viaSentIn);        // with EXP Share  ⇒ a SECOND regime
  ```
    ‼ **`viaSentIn` counts "was sent in AND IS STILL ALIVE", not "why".** Verified by reading the loop:
  ```c
  if (GetMonData(&gPlayerParty[i], MON_DATA_SPECIES) == SPECIES_NONE
      || GetMonData(&gPlayerParty[i], MON_DATA_HP) == 0)   continue;   // ⇐ a FAINTED participant
  if (gBitTable[i] & sentIn)  viaSentIn++;                             //    does NOT dilute
  ```
  ⇒ two consequences: (1) the divisor is **mechanism-independent** — a deliberate swap-training
  rotation and an emergency survival rotation increment the same counter, which is what licenses a
  general-population measurement standing in for swap-training; (2) **a participant that FAINTED is
  excluded**, so a trainee that goes down does not cost the survivor half its payout.
  *(This passage read "counts 'was sent in', NOT 'why'" until a verification pass caught the missing
  ALIVE condition — correct about the part that mattered, incomplete about the mechanic.)*
  ⭐ **MEASURED, and it agrees to three decimal places** (batch `20260909-160339`, 8 lanes, 3h,
  `--build sandbox`; `tools/story-dev/probe_exp_participant_divisor.py`, matched on (foe species,
  foe level) so the divisor is not confounded with which foes get fought):
  ```
    min n2   groups   median ratio      pooled sanity check (confounded by foe mix):
         1       88          0.829        1 participant  median 205 exp  (n=3,290)
         5       27          0.592        2 participants median 123 exp  (n=  401)
        10       11          0.504        ratio 0.60
        20        2          0.501      ⇐ decomp predicts exactly 0.500
  ```
  ⇒ **`estimate_frames_to_level` HAS NO PARTICIPANT DIVISOR, so every estimate where a second mon
  participates is up to 2x OPTIMISTIC — and this item's corrected arithmetic (L42, not L35) STANDS.**
  ⚠ **SCOPE, STATED:** the 401 two-participant observations are **mostly NOT deliberate
  swap-training** — this batch holds only **14** turn-0 full-HP rotation windows (11 of which showed
  two mon gaining). The decomp is what licenses generalising from one to the other; the log evidence
  alone would not.
  ⚠ **HETEROGENEITY IS REAL:** `Poochyena L6` (0.83, n2=13) and `Nincada L6` (0.81, n2=13) sit far
  from 0.5 — the `calculatedExp / 2 / viaExpShare` branch above is a plausible second regime and is
  **not** separated by this tool.
  ⚠ Previously (superseded by the measurement above): the split is 2 only when swap-training FIRES,
  so the true cost is between the solo and 2-way columns — which is exactly why the measurement
  below (log `total_exp` by PID either side of a battle) was the next deliverable.
  ✅✅ **THAT BLOCKER IS CLEARED 2026-09-09 — THE TELEMETRY NOW EXISTS.**
  **[MEASURED BY ME — scope: `x4-runs` 298 `stdout.txt` + its `debug-logs/*.log`,
  `sandbox-pokebot/profiles` 500 `*.log`, `tools/story-dev` 500 `*.log`]** there was **no continuous
  PID-bearing party telemetry anywhere**: `Species#PID` occurred in **96** stdout lines, **AT THE TIME OF MEASUREMENT all of
  them §Ch23 refusal messages**, plus ~15 from one-off probes. Party snapshots carried
  `Species:L<level>` and nothing stable ⇒ **a mon could not be followed across readings**, which is
  why this measurement was blocked and why the *"88.8% born behind"* figure on `#24-dexhunt` is
  still unverifiable.
  ✅ **`modules/debug_logger.py` now emits `ids=[Species#PID:L<lv>:exp<n>, …]` in the heartbeat.**
  ⛔ It is a **SEPARATE field**: `_party_key` is untouched because it drives `_detect_events` (size
  change ⇒ CATCH, slot change ⇒ LEVEL-UP/EVOLUTION), and folding identity into it would change which
  frames count as party events — a behaviour change wearing telemetry clothes. Nothing reads the new
  field. Per-mon safety: `None` slots skipped, an unreadable PID degrades to `#????????`, each mon
  wrapped in its own `except`, and the whole call wrapped again by the file's `_safe()`.
  ‼ **NOT GATE-CERTIFIED, and say so honestly:** `repro_no_silent_except.py` and
  `repro_undefined_names.py` **do not scan `modules/debug_logger.py`**, so their green exits are NOT
  evidence for that handler; the safety case is the code, read directly.
  ⇒ **NEXT: one ORDINARY batch answers it — `PYTHONUTF8=1 py -3.12 x4_headless.py --build sandbox`.**
  ⛔ **`--build sandbox` IS MANDATORY** (`x4_headless.py` defaults to `custom`, and BOTH fields are sandbox-only — `custom-pokebot/modules/debug_logger.py` has `party_ids` 0x, `_owned_dex` 0x, measured 2026-09-09) ⇒ a default batch emits NOTHING and reads as a refutation.
  Pair `total_exp` by PID either side of a wild battle
  where swap-training fires, and the L35-vs-L42 question is settled. No new driver, no fixture.
- [ ] ⚠ **SURF IS STILL UNSOLVED BY BOTH.** Best pre-Surf ground is Route 117 **L13** (every
  higher-band Surf-learner ground is gated behind Surf itself), and L13+250k → ~L28 < L35. ⇒ the only
  candidate is acquiring a carrier at **§Ch3 (Route 104 Marill L4-5, at team level)** so it is never
  a mule. ✅ **VERIFIED 2026-09-08** from our own ROM-derived cache `sandbox-pokebot/cache/encounter_index_BPEE0.json`: **Route 104 Grass, Marill, 20% of encounters, L4-5.** ⛔⛔ BUT THE §Ch3 ACQUISITION IS **REFUTED** — see the block below; the encounter data was never the weak link.
  ⭐ [VERIFIED] Marill learns ALL FIVE HMs (Dive/Rock Smash/Strength/Surf/Waterfall); Zigzagoon only
  Cut/Rock Smash/Surf. Full detail: `ai-research-notes/2026-09-08-hm-mule-catch-sites-MEASURED.md`.
