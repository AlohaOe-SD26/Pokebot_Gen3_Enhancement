> **Committed 2026-10-29** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/r5recon/02-record.md` (sha256 `3a75aeb1ee0754b5`). R5's recon, angle 2, THE RECORD: a read-only Claude subagent's NOTE, never truth (its own status line says so; the authoritative docs and the code win).
> **What the R5 build then MEASURED** (`2026-10-28-R5-BUILD-REPORT.md`; seed ledger #43, #45 and #49): the play loop ended a run "done" on the pass's look, whatever was on screen (this recon's reading of `mode.py:457-458`, confirmed); `ch1_clock` ends on a FREE screen (its `use` goal plays MOM's text out before the loop reads the mark); `ch2_dad` ends on a ONE-frame free read: DAD's warp to PETALBURG CITY frees the player for one frame and WALLY's tutorial (the city's ON_FRAME script) locks the controls on the next, which the game-facts note's section 4.3 (d) predicted. The AI's own `nav_free` reads that frame FREE, so a settle gated on it alone would not have run there.

# R5 recon, angle 2: THE RECORD (what the project already decided and found about R5 and its neighbours)

**A NOTE, not truth.** Written 2026-10-28 by a read-only Claude recon subagent. Nothing was run except read-only `git`,
`py -3.12 tools/decomp_lookup.py ask ...` and two read-only Python reads of `ai_player/knowledge/milestones.json`. No repo
file and nothing in the learner clone was touched.

**Tags.** `DOC` = quoted from a project document. `CODE` = read in today's tree, HEAD `f9474661` (clean). `DECOMP` = read in
the pinned clone `C:/Remote Projects/_decomp/pokeemerald` at `731ad5b` (the pin `decomp_lookup` reports). `INFERENCE` =
my reasoning. `UNVERIFIED` = not measured or not read.

**Short paths.** `BL` = `PROJECT KNOWLEDGE/ai-research-notes/2026-10-18-improvement-backlog.md`; `RC/00`, `RC/03`, `RC/07`,
`RC/08` = `.../2026-10-15-ch34-recon/{00-RECON-NOTE,03-our-code-gaps,07-verify-facts,08-verify-gaps}.md`; `R2N` =
`.../2026-10-19-backlog-round2/03-ai-player.md`; `R3D`, `R3L` = `.../2026-10-19-backlog-round3/{02-deployment,03-long-horizon}.md`;
`R4N` = `.../2026-10-19-backlog-round4/02-backlog-review.md`; `DD` = `.../2026-10-07-ai-player-v1-DESIGN-DRAFT.md`;
`06`, `04`, `03`, `05` = `PROJECT KNOWLEDGE/0N-*.md`; `AP/` = `ai_player/`; `LIB` = `sandbox-pokebot/modules/libmgba.py`.

---

## 0. Bottom line (ten points)

1. **R5 is a PRECONDITION, not a saver.** Its origin defines it as one helper with THREE CALL SITES: "one
   `settle_to_free(hands)` helper (no text box, controls unlocked, the overworld), called before a run ends "done", before a
   goal switch after a milestone flips, and before R1's save; the chapter-end check asserts it" (R2N:129-130). The backlog's
   one-liner "One `settle_to_free` before "done", a post-milestone goal switch and a save" (BL:326) compresses that list. Read
   it as three call sites: the save and the "when to save" rule belong to R1 (R2N:31-34; BL:292-293).
2. **The record disagrees with itself about R5's evidence.** The synthesis rates Gap 4 MEDIUM (RC/00:375-383) and round 2
   builds R5 on it (R2N:127-128). The LATER adversarial verifier ruled Gap 4 "**NOT REAL for chapter 4** | The badge comes
   inside a `talk` goal, which plays to a free screen before the loop checks the target" (RC/08:24), and left only a low
   residual (RC/08:148-149). R2N never mentions RC/08's verdict. Today's code still matches RC/08's reading (CODE, section 9).
   ⇒ The record names no observed run that ended mid-box. I searched the recon notes, the backlog notes and the KI list
   (05), not every evidence file. R5 guards a residual path and is the precondition R1 needs.
3. **R5's motivating state is unreachable for today's AI.** "AI frontier: chapter 2 (WALLY's tutorial)"
   (`PROJECT KNOWLEDGE/ai-frontier.txt:1`); "*Chapters 3 and 4 have never been played.*" (AP/README.md:1716). Its proof
   therefore needs a constructed reach: "Gap 4 needs its own fault arm (end the run inside the talk)" (RC/08:263), and "its
   fault arm is a fixture where the flag flips with a box up" (R2N:131-132).
4. **Among v1's four chapter ends, only `ch4_roxanne`'s mark flips with text still to come** (DECOMP, section 3.3). So the
   CH1→CH2 chain used today never exercises the gap. One INTERMEDIATE chapter-1 mark does flip mid-scene:
   `FLAG_SET_WALL_CLOCK` comes before MOM's upstairs text. It is a candidate development fixture (UNVERIFIED as usable).
5. **The order on record is: PARK TOOL, then R5, then R1 + R2.** 04:61 reads "next is the PARK TOOL (...), then R5, then
   R1 + R2 (its item 15)", and 06:9838 reads "the park and resume become one committed, tested tool before R5". Round 4 moved
   R5 AHEAD of R1 + R2 (R4N:83, :202); round 2 had placed it after them (R2N:215).
6. **The record leaves R5 versus R6 unresolved.** BL:198 says "free screen = R5 inside R6's screen ladder", and BL:192 lists
   R6 before R5. But the top 15 (BL:18) and the handoff queue (04:61) name R5 alone, and R6 is in neither. This is a
   technical call to log in `06` before building (section 5).
7. **No user ruling names R5 or a "free screen".** `decomp_lookup ask "free screen"` (exit 0) prints one do-not line, and it
   is USER RULING 43's (the watchdog toast, unrelated). `ask "save the game"` (exit 0) prints none. `ask "save scum"` exits
   3 with "NO PRIOR RULING OR FACT FOUND", so the backlog's "No save-scum" (BL:294) is a candidate rule, not a ruling. The
   rules that DO bind are RULINGS 35, 36, 37, 40, 41 and 50, the purity gate's load ban, and the framework-not-edited rule
   (section 7).
8. **DECIDE EARLY is R1 + R2's tag, not R5's.** R4N:44 gives the reason: "the first memory file fixes paths and schema".
   As recorded, R5 writes no persisted file ("**Cost:** small", R2N:131), so it fixes no DECIDE-EARLY shape in place. It
   would if it shipped R6's wishlist file or an in-game save (section 8).
9. **Reuse before building (CODE, for the code angle to confirm).** `player_free` (AP/hands/dialogue.py:131-137) is R2N's
   predicate almost word for word. `play_out` (AP/skills/story.py:148-159) is a bounded settle loop. The play loop already
   plays out a non-free screen before it picks a goal (AP/mode.py:475-481). The record's gap is the ORDER: the "done" check
   at AP/mode.py:457-458 runs before the free check at :475.
10. **Name clashes** (section 1): the `R5.<NAME>` grader checks, "recon Gap 4" (00's numbering; in 03, gap 4 is the
    trader), and the punch list's "the coach (step 6)", which is not the backlog's step 6.

---

## 1. Name clashes (so the build does not cross wires)

- **The backlog's R5 is this item** (BL:325). It is NOT step 5's grader checks named `R5.<NAME>`: "R5.NO_LOAFING (KI-125:
  ...), R5.PUSH_PATHS_AGREE (KI-126: ...) and R5.NOTRAIN_TRAINED_CHECK" (04:59), and "a step-5 grader CHECK by its id
  (`R5.*`, `L5.*`, the table in `gates/grader_checks.py`)" (AP/LESSONS.md:7).
- **Other unrelated R5s:** O3's test "R5 FAULT, in-process: make the stream copy raise `OSError`..."
  (`.../2026-10-19-BUILD-SPECS-steps-1-2.md:98`; R3's uncritiqued copy `.../backlog-round3/01-build-specs.md:89`);
  `lint_docs`' rule R5 (`.../2026-10-22-S2-1b-part2-recon-tools.md:53`); and "R5 — RETIRED (scoped)" (08-MISTAKES.md:4554).
- **"recon Gap 4" uses the SYNTHESIS's numbering:** "### Gap 4 — MEDIUM: "done" while a box is still up" (RC/00:375). In the
  angle note RC/03, gap 4 is the trader's party menu (RC/03:28), which is RC/00's Gap 5 (RC/00:385). R2N's R6 uses 00's
  numbering: "The recon's Gap 5 (the Rustboro trader's YES opens a party menu)" (R2N:87-88).
- **"Step 6" means two things.** In the backlog it is "6. **Step 5.3, then chapters 3-4,** on **D1, D2** and **R6, R5, R1 +
  R2, R8 + R9, R12**" (BL:192). The punch list's "then chapters 3-4 to ROXANNE, self-tuning, and the coach (step 6)" (03:83)
  uses the AI player's own step numbers. **"Step 5.3" also moved:** `06` once planned "**Step 5.3:** chapter 3" (06:9324),
  but step 5.3 became B1 + N8's graded round ("step 5.3, B1 + N8's grader half (backlog items 12-13)", 04:58).

---

## 2. What R5 must do (the record's own words)

- **The backlog entry** (BL:325-326): "- **R5. A FREE-SCREEN precondition.** (B) `FLAG_BADGE01_GET` flips before TM39's
  text and the run ends "done" mid-box (`mode.py:457-458`, recon Gap 4). One `settle_to_free` before "done", a
  post-milestone goal switch and a save."
- **The top-15 line** (BL:18): "15. **R5, then R1 + R2 (+DP1, DP2, L3 a-b)** free screen, then save/CONTINUE and a memory
  that survives a kill; DECIDE EARLY. Step 6; est. 300 + 200." The 300 + 200 lines cover the whole cluster.
- **The origin** (R2N:126-132):
  - "**R5. A FREE-SCREEN precondition at every boundary: "done" never means "mid-scene".** Priority B."
  - "**What:** one `settle_to_free(hands)` helper (no text box, controls unlocked, the overworld), called before a run ends
    "done", before a goal switch after a milestone flips, and before R1's save; the chapter-end check asserts it."
  - "**Benefit:** a chained chapter does not start inside a text box, and saving is safe. **Cost:** small. **Risk:** low;
    its fault arm is a fixture where the flag flips with a box up."
- **The recon's fix** (RC/00:382-383): "Act on a milestone's completion, and end a run, only when the screen is free: no
  text box, controls unlocked. Assert that in the chapter-4 end check."
- **Its consumer is R1:** "(4) a rule that saving is allowed only on a free overworld screen (see R5)" (R2N:34), and
  "saving only on a free screen (R5)" (BL:293).
- **⇒ The deliverables on record:**
  - (a) one helper;
  - (b) three call sites: before "done", before a post-milestone goal switch, before R1's save;
  - (c) the chapter-end check asserts a free screen;
  - (d) a fault arm whose fixture flips the flag with a box up.
- **NOT R5:**
  - the "when to save" rule, which is R1's (3): "after a Center heal, after a badge, before a gym, before a long route; a
    careful archetype saves more" (R2N:32-33);
  - the save itself, which is R1's `save_game` (R2N:31).
- **Priority B** (Correctness section; R1 + R2 are A). The backlog calls all of these "candidates, not decisions. Each
  becomes a decision (`06`) and a punch-list status when built" (BL:28), and adds "A NOTE; the order below wins" (BL:20).

---

## 3. R5's stated evidence, and what the record says about each piece

### 3.1 The decomp fact: VERIFIED (re-read by me)
- `data/maps/RustboroCity_Gym/scripts.inc` (DECOMP):
  - :17 `msgbox RustboroCity_Gym_Text_StoneBadgeInfoTakeThis, MSGBOX_DEFAULT`;
  - :18 `setflag FLAG_DEFEATED_RUSTBORO_GYM`; :19 `setflag FLAG_BADGE01_GET`;
  - :25 `goto RustboroCity_Gym_EventScript_GiveRockTomb`;
  - :29 `giveitem ITEM_TM_ROCK_TOMB`; :30 `goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull`;
  - :32 `msgbox RustboroCity_Gym_Text_ExplainRockTomb, MSGBOX_DEFAULT`; :33 `release`.
- ⇒ The flags are set with two text boxes still ahead: the giveitem message and ExplainRockTomb. With a full bag, the
  bag-full message follows instead.
- The record agrees:
  - "`FLAG_BADGE01_GET` turns on before TM39 and its text (`RustboroCity_Gym/scripts.inc:18-19` vs `:28-34`)" (RC/07:389);
  - RC/07:149 marks the order CONFIRMED.
- **The milestone's proof is exactly those two flags.** `ch4_roxanne` done = `{"DEFEATED_RUSTBORO_GYM": 1264,
  "BADGE01_GET": 2151}` (CODE, `AP/knowledge/milestones.json`, read by script). A milestone is done when "Every proof holds
  on the eyes' marks" (AP/knowledge/story.py:82-87, an `all(...)` conjunction).

### 3.2 "The same shape holds for every gym" (R2N:128): consistent, line order only
- In all 8 gym scripts, the first `setflag FLAG_BADGE0N_GET` comes before the first `giveitem ITEM_TM` (DECOMP):

  | Gym | badge flag line | first TM give line |
  |---|---|---|
  | RustboroCity_Gym | 19 | 29 |
  | DewfordTown_Gym | 151 | 171 |
  | MauvilleCity_Gym | 94 | 115 |
  | LavaridgeTown_Gym_1F | 62 | 82 |
  | PetalburgCity_Gym | 369 | 394 |
  | FortreeCity_Gym | 34 | 52 |
  | MossdeepCity_Gym | 66 | 93 |
  | SootopolisCity_Gym_1F | 97 | 118 |

- ⚠ I traced the full flow for Rustboro only. For the other seven this is a line-order check, not a control-flow read.

### 3.3 The other chapter ends do NOT share the shape (DECOMP + CODE; not in the record)
- **`ch1_pokedex`** = `RECEIVED_POKEDEX_FROM_BIRCH`, `SYS_POKEDEX_GET` and `ADVENTURE_STARTED` (milestones.json, a
  conjunction).
  - In `LittlerootTown_ProfessorBirchsLab/scripts.inc`, the first two are set inside `ReceivePokedex` (:537, :539). That
    subroutine is called at :501, so they flip before the ExplainPokedex msgbox at :502.
  - `setflag FLAG_ADVENTURE_STARTED` (:510) comes after the rival's Poké Ball scene, then `releaseall` at :514.
  - ⇒ The chapter-1 end completes at :510, with no text left.
- **`ch2_wally`** = `VAR_PETALBURG_GYM_STATE` >= 2.
  - `PetalburgCity_Gym/scripts.inc`: :89 `msgbox PetalburgCity_Gym_Text_DadGoCollectBadges, MSGBOX_DEFAULT`, :90
    `setvar VAR_PETALBURG_GYM_STATE, 2`, :91 `releaseall`.
  - `ScrCmd_releaseall` calls `HideFieldMessageBox()` (`src/scrcmd.c:1240-1244`).
  - INFERENCE (not measured): `setvar` and `releaseall` run in the same script tick, so no look can see the mark with the
    box still up.
- **`ch3_rustboro`** = `VISITED_RUSTBORO_CITY`, set on the map transition. The record calls it "A quiet arrival" (RC/00, §1
  row 5).
- **An intermediate chapter-1 mark DOES flip mid-scene.** `setflag FLAG_SET_WALL_CLOCK` at `data/scripts/players_house.inc:58`
  is followed by MOM coming upstairs (:61-62), with `msgbox PlayersHouse_2F_Text_HowDoYouLikeYourRoom` at :74 / :84.
  `ch1_clock` done = `SET_WALL_CLOCK` (milestones.json).
- **Not candidates:** `ch1_rival_route103`'s `FLAG_DEFEATED_RIVAL_ROUTE103` is set at `Route103/scripts.inc:133`, just
  before `releaseall` (:138).

### 3.4 SCOTT is not a candidate (record + CODE)
- RC/08:146-147: "`VAR_SCOTT_STATE` is not a milestone mark (no hit in `milestones.json`), so its "set before the
  dialogue" order cannot end anything."
- Re-checked: 0 hits for `SCOTT` in `AP/knowledge/milestones.json` (CODE).

### 3.5 The code claim: TRUE as to ORDER (CODE)
- R2N:127-128 says: "the run ends at `mode.py:457-458` (`_play_end(... "done" ...)`) with no check that the box is gone".
- Today, AP/mode.py:457-458 reads `if milestone is None or index > target:` / `return self._play_end(hands, story, manager,
  runner, report, "done", f"{options.target} reached")`.
- The free check comes later: `if not nav_free(look):` (AP/mode.py:475).
- `_play_end` (AP/mode.py:647-682) neither settles nor saves.
- The cited lines have not moved since round 2 wrote them (`git log -L` shows the R5 line unchanged since `5a3694ab`).
  RC/00 and RC/03 cite the older `mode.py:437-438`, from the 2026-10-15 working copy.

### 3.6 The adversarial verdict, and why it still holds (record + CODE)
- RC/08:142-145: "The badge is set by ROXANNE's post-battle script, which runs inside the `talk` goal. `talk_to` →
  `play_out` loops `nav.handle` until `nav_free` ... So the TM39 text has been read before the run ends. VERIFIED-code."
- RC/08:148-149: "**Residual (low):** a `talk` that returns "talked; then stuck: …" with a screen still up. The next pass
  would end "done" with that screen up."
- RC/08:150: "⇒ 9c PASS #2 ("the screen is free at the end") passes BY CONSTRUCTION on the current code (§11)."
- **Today's code still has the same shape (CODE).**
  - `play_out` returns None only when `nav_free(look)` (AP/skills/story.py:152-155).
  - `talk_to` ends `stop = yield from play_out(hands, nav, why)` / `return "talked" if stop is None else f"talked; then
    {stop}"` (AP/skills/story.py:185-186).
  - The play loop has a second residual: after a `play_out` stop with the screen still up, it does `hands.pad.busy(...)`
    and `continue` (AP/mode.py:477-481). The next pass then reaches the done check at :457 before any new play-out.
    INFERENCE; for the code angle to confirm.
- **The question the record left open:** "**Q6. Does PL-2 ("scenes first") already stop the AI acting mid-TM39 text** (gap
  4)? Read `mode.py` and the story skills, or run it." (RC/00:728-729).
  - RC/08 §4 answered it by READING only; nobody ran it.
  - No AI-player KI concerns a run end, a save or text left up: KI-123 to KI-127 are at 05:3333-3375.

### 3.7 Why the record wants R5 anyway
- Chains: "**A chained chapter 5 starts mid-TM39 text (gap 4) and then meets this scene (P6)**" (RC/00:714).
- Saving: "saving is safe" (R2N:131).
- The theft scene after the badge: RC/03:181-183 says "The run ends at the badge (`mode.py:437-438`, index > target), so the
  STOLEN-GOODS coord scene outside the gym ... falls after the run's end. VERIFIED."

---

## 4. The proof method on record (and what binds it)

- **R5's own arm:**
  - "its fault arm is a fixture where the flag flips with a box up" (R2N:131-132);
  - "the chapter-end check asserts it" (R2N:130).
- **The chapter-4 draft:** "2. The screen is free at the end (gap 4). The TM39 text must not be left half-read." (RC/00:661).
- **Its critique** (RC/08:263): "| 9b.5 / 9c.2 "screen free at the end" | A no-op passes it (nothing on screen). On the
  current code 9c.2 passes by construction (§4) | Keep it as a guard, never as evidence. Gap 4 needs its own fault arm (end
  the run inside the talk) |".
- **The grading trap when play continues after the badge** (RC/07:56, D3):
  - "**It turns FALSE if the run keeps walking after the badge.** ... If chapter 4 is allowed to continue until "the screen
    is free" (PASS 2) and the AI then walks out, PASS 1 fails on a correct run."
  - "**Fix:** grade `>= 1`, or sample the var at the moment `FLAG_BADGE01_GET` turns on."
  - Its basis: `setvar VAR_RUSTBORO_CITY_STATE, 2` at `RustboroCity/scripts.inc:288`.
- **R1's proof, which R5 feeds:**
  - "(A; proof: kill, CONTINUE, same PIDs and tile)" (BL:290);
  - "a fault arm that kills before the save must resume EARLIER" (R2N:38).
- **The lessons that bind any R5 proof** (AP/LESSONS.md):
  - PF-4 (:135): "A fault arm must REACH the state it tests; grade only the runs that reached it, with a reach floor."
  - PF-10 (:174): "A premise or after-state check must be able to FAIL."
  - PF-17 (:219): "A rule that ENDS a run (or a goal) is a claim about every state: develop it on the game's opening, not
    only on the stuck state it was built for."
  - PL-1 (:243): "Never idle: no `AWAIT_MAX` frames while a screen waits for a press, whatever the reason." A settle
    presses; it does not wait.
  - PL-2 (:249): "Scenes come first: settle after a map change; story skills give way to a waiting screen." It is
    enforced by `ai_player/mode.py::SETTLE_FREE`.
  - PL-4 (:261): "Bound every loop: each errand has a frame budget, each `while True` a budget and a no-frame-passed cap."
- **The recon's common rules** (RC/00:593-606):
  - ground truth is read "by the HARNESS from `gSaveBlock1` flags and vars";
  - "Identity, never counts";
  - "Every fault arm declares the state it must REACH";
  - "The tree is frozen";
  - the start fixture is "the AI's OWN previous-chapter end state, chained ... COPIES only. Never write into
    `tools/story-dev/saves/`".
- **Fixtures, as the record states them:**
  - No AI-made gym state exists (section 0.3).
  - The bot's gym saves are AFTER the badge: "`gym1_done.ss1` and `r20_badge1_party1_gym.ss1` are end states" (RC/03:270).
  - Bot saves may prove a SKILL: "a late-game skill may be proven on a pinned bot fixture (with a control arm and the
    fixture's hash)" (R3L:211-212).
  - They may not start a chapter: "A chapter never starts from a bot save again" (R2N:117-118), and a run from a bot save
    "has never 'heard' DAD" (recon Gap 9, R2N:112).
- **Replays and clocks:** "Identical output across runs is a DETERMINISM check, never a replication" (PF-9,
  AP/LESSONS.md:167), and "⚠ The game reads the HOST CLOCK: pin it in any arm that must replay." (04:51).

---

## 5. Merged with R6, and the order

**The merge:**
- "free screen = R5 inside R6's screen ladder" (BL:198).
- Its source (R4N:65): "| Free screen | R5, R6, R1's "saving only on a free screen" | R5 inside R6 as one "screen state"
  ladder | R1 and R6 both depend on R5 |".

**The order, as each document gives it:**
- **Step 6:** "**R6, R5, R1 + R2, R8 + R9, R12**" (BL:192).
- **Round 4's correction:**
  - the contradiction: "4. **R5 vs the order.** Step 6 reads "R6, R1 + R2, R5", but R1 + R2 "save only on a free screen
    (R5)". R5 must come first." (R4N:83);
  - the edit: "OLD: `... **R6, R1 + R2, R5, ...**` -> NEW: `... **R6, R5, R1 + R2, ...**`" (R4N:202).
- **Superseded:** round 2's own order was "R3 and R4 (small, additive) -> R6 -> R1 + R2 (one step, one live kill-and-resume
  proof) -> R5 -> R9 ..." (R2N:215). Its rationale line still stands: "R1 + R2 together (a save is only half a resume)"
  (R2N:17).
- **The top 15** names R5 and R1 + R2 only (BL:18). R6 is not in the top 15.
- **The handoff:**
  - "next is the PARK TOOL (USER RULING 50: `park` and `resume` for the tuner as one committed, tested tool; ...), then R5,
    then R1 + R2 (its item 15)" (04:61);
  - "so the PARK TOOL, then R5." (04:21);
  - "Chapters 3-4 (the woods as a passage, double battles, ROXANNE) come with item 4's R5 and R1 + R2 (the backlog's step
    6)" (04:60).
- **The punch list:** "(10) THE PARK TOOL (USER RULING 50, 2026-10-28):** ... NOT STARTED, NEXT." (03:85). It is not built
  as of `f9474661`.

**R6's content, which "inside R6's ladder" would pull in:**
- BL:286-289: "a person-fair ladder (read, decline an unplanned yes/no, B out unless allow-listed, never A on a buy or a
  trade), each firing logged to a wishlist file. ⚠ Graded runs REPORT every firing; a default never counts as a skill."
- R2N:92-94 adds "a small ALLOW-LIST of screens where B is harmful (evolution: A only)" and "append the screen's fingerprint
  ... to `screen_wishlist.jsonl`".

**R6's evidence still holds (CODE):**
- "stuck: an unexpected {outcome[5:]} on screen" (AP/brain/navigator.py:1097).
- `_story_menu` handles only `choose_starter`, `clock` and the mart menus (AP/mode.py:611-622).
- The default YES: "YES, a person goes along with what the game asks" (AP/skills/story.py:91).

**Dependencies:** "**R7. A GET-UNSTUCK LADDER, deploy mode only.** (B; needs R1, R3, R6)" (BL:331).

**My reading (INFERENCE):** the two shapes are compatible. A free screen is the ladder's END condition, and R6 is what the
loop does on a screen it does not know. Building R5 first does not block R6 if the settle loop hands unknown screens to one
hook. But the record does not say which comes first, so log the choice in `06`.

---

## 6. What must land WITH R1 + R2 (and what R5 hands them)

**The rule:** "**DP1 + DP2 and L3 (a)-(b) land WITH R1 + R2**, before its first memory file (round 3: that file fixes paths
and schema)." (BL:193-194)

**R1 + R2** (BL:290-294):
- "(A; proof: kill, CONTINUE, same PIDs and tile)".
- Evidence: "no skill saves (`skills/intro.py:9`); the resume file is written on a CLEAN close only (`libmgba.py:141`);
  `_Memory` is not carried (`brain/goals.py:62`)".
- What: "`save_game` and CONTINUE read by their words, saving only on a free screen (R5); one `memory.jsonl` (full lines
  plus deltas) stamped with play time, so a resume loads memory NOT NEWER than its save."
- "UNVERIFIED first: does mGBA flush the save before a kill? No save-scum."

**R2N's details:**
- R1 (R2N:31-40):
  - a `save_game` skill "that opens START, reads the cursor on SAVE, answers the overwrite question by its words, and waits
    for the "saved" text";
  - a CONTINUE branch on the main menu;
  - "forbid reloading to undo a loss (a resume is for crashes only), and say so in `LESSONS.md`".
- R2 (R2N:52-55): "one `memory.jsonl` through the existing `RecordFile` ... a version field, and a loader that restores
  both."

**DP4, folded in** (BL:375-376): "the `.sav` is the durable copy (`.ss1` is tied to the emulator build); keep the newest 10;
deploy "new game" makes a NEW profile and "retire" archives, never a silent `--fresh` wipe."

**DP1 + DP2** (BL:387-391, from R3D:44-56):
- "One `AppPaths` and a `schema_version` on every user-data file. (A, ⏰ DECIDE EARLY)".
- "R2's memory, R11's ledger and R8's `INDEX.json` will be the first persisted AI files".
- R3D:52-55: "it cannot be added after the first friend's memory file exists".
- Cost: "about 60 lines and a fault arm per rule" (BL:390-391).

**L3 (a)-(b)** (BL:392-396; R3L:88-98): "Every mon by PID and species, with ROLES. (A, ⏰ DECIDE EARLY: fields in R2's
memory schema from its first line)".
- PIDs do not cross RULING 40's line. The eyes carry the AI's OWN party PIDs and withhold a foe's: "a person knows which of
  their own Pokemon they sent out. None for a FOE (nothing on screen shows a PID)" (AP/eyes/observation.py:275-277).
  RULING 40 bars "a wild Pokemon's PID, IVs, nature or held item before the game shows them" (06:9434).

**The R1 + R2 citations, re-checked today (CODE):**
- `skills/intro.py:9`: current, "NEW GAME, chosen by reading the cursor (on a fresh save it is the first of two)". No save
  skill exists; a grep of `ai_player/` for `save_game` finds only the purity bans in section 7.
- `libmgba.py:141`: current, "Whenever the emulator closes, it stores the current state in `current_state.ss1`." (LIB:140-141).
- `brain/goals.py:62`: **STALE.** The words are now at AP/brain/goals.py:449: "(the memory is carried between sessions,
  `AI_PLAYER_WORLD`; this goal manager's own memory is not)". `class _Memory` is at :407.
- The launcher already knows the cartridge save: "#: The cartridge save. A "fresh" boot with one present CONTINUES it" /
  `SAVE_FILE = "current_save.sav"` (AP/host/launcher.py:92-93).

**Framework facts for R1 and DP4 (CODE):**
- The cartridge save is opened read-write: "libmgba needs a save file to be loaded, or otherwise it will not save anything
  to disk if the player saves the game" (LIB:124-132).
- Every in-game save is COPIED, unbounded, by the `savedata_updated` hook (LIB:161) into
  `saves/<timestamp>.sav` by `backup_current_save_game`, "called every time the emulator writes out the save game"
  (LIB:243-255). That conflicts with DP4's "keep the newest 10".
- The framework may not be edited ("the framework is not edited", 06:9261), so any retention must live on the AI's host
  side. INFERENCE.
- Whether the bytes reach the disk before a HARD kill is UNVERIFIED: R1's "measure that first" (R2N:39).
- "`--fresh` deletes the profile's `current_state.ss1` and `current_save.sav`" (AP/README.md:305), against DP4's "never a
  silent `--fresh` wipe".

**Two memories, not one (INFERENCE from the record):**
- R2's `memory.jsonl` is state WITHIN one playthrough, rolled back to the save point ("loads memory NOT NEWER than its
  save", BL:293-294).
- RULING 40's EXPERIENCE spans playthroughs ("It remembers across playthroughs what worked", 06:9430).
- A CONTINUE must roll back the first and must never roll back the second.

---

## 7. Binding rulings, with their do-not lines

**Rulings that bind R5 and its neighbours:**
- **USER RULING 35** (06:9220, verbatim at :9222). The words: "the ai interacting with the game itself without any bot
  usage or bot like behaviors". So `settle_to_free` must be the AI's own presses through its pad, and the story bot's
  scene code is teaching material only.
- **USER RULING 36** (06:9233). The words: "BRAIN = entirely the AI's own (no bot pathfinding, battle strategies or menu
  scripts while playing, RULING 35)".
- **USER RULING 37 Q4** (06:9254; DD:381). The words: "4: Yes, for the official acceptance runs (including naming and clock
  setting)", and "A real New Game for OFFICIAL acceptance runs ... Development may use saves." So R1's CONTINUE is for
  crash resume and deploy, never the start of an official acceptance run.
- **USER RULING 37 Q2** (06:9261). The words: "the framework is not edited". So the save backup in `libmgba.py` stays as it
  is.
- **The design draft §10.3, adopted** (DD:409, :412). The words: "**Give-up and crashes end the process; they never
  silently restart or park.**" and "Giving up = a log line plus `sys.exit(code)`". So a settle that cannot reach a free
  screen must END the run with a reason, never loop. The record does not say whether that ending is "stuck" or "done"
  (section 11).
- **The purity gate** (06:9269; CODE). The words: "The static gate (framework doors only; no write/load/reset)". The code
  bans `"load_save_state", "load_save_game", "load_state", ...` and `"reset", "loadState", "loadSave", "create_save_state"`
  (AP/gates/check_purity.py:544-546), and counts `EMULATOR_LOAD_METHODS = ("load_save_state", "load_save_game", "reset")`
  (AP/host/attribution.py:179). So CONTINUE is pressed on the title screen, R5 and R1 write no state, and R8's ring is
  host-side (R2N:104: "the HOST side (the instrument writes files, not the AI)").
- **USER RULING 40** (06:9430, :9434). The words: "**EXPERIENCE: allowed.**" and "**STILL NOT ALLOWED: LIVE HIDDEN
  STATE**". So R2's memory holds only what the AI saw; experience crosses New Games.
- **USER RULING 41** (06:9499, :9503). The words: "it launches the emulator, loads the rom, creates a profile/uses an
  existing profile and plays the game from beginning to end", and "It uses NO bot code, enforced by `check_purity`". This
  is the user intent behind R1's save and CONTINUE ("uses an existing profile").
- **USER RULING 50** (06:9838-9839). The words: "the park and resume become one committed, tested tool before R5", and
  "⛔ **Do not park or pause the tuner or the project (no STOP file, no disabled task) unless the user asks; do not re-ask
  whether to pause.**" This sets the order and forbids a park during the build.
- **CLAUDE.md** (project rules, Story-bot craft). The words: "a state-write is a documented last-resort fallback that must
  reproduce vanilla's exact end-state". So R1's save is an in-game save, never a state write.

**A bot-side precedent: intent, not a ruling on the AI** (06:2237-2252, 2026-08-14 RULING B).
- "continue where it left off in the event that the bot gets turned off during sudden power loss OR I turn it off for a
  period of time and turn it back on to have it continue" (06:2241-2242).
- "⇒ ‼ **These are TWO SEPARATE FEATURES and must not be conflated.**" (06:2245).
- RULING 35 makes the bot a teacher. This shows the user's wish for R1; it is not a ruling on the AI (INFERENCE).

**Teaching precedent, the same class of defect** (06:4123-4131): "§Ch23's completion gate is FLAG **AND** POSITION, not the
chapter table's milestone". The flag "is set at **LEG 5 OF 11**", so "A gate on the flag alone would hand §Ch24 a run
buried two floors underground", and "three chapters that PASSED THEIR OWN TESTS while stranded". R5 applies the same rule:
FLAG AND a free screen.

**The `decomp_lookup.py ask` results** (read-only; the pin is `731ad5bf`):
- `"free screen"`, exit 0. Four rulings: 06:695-727, 06:9079-9110, 06:9277-9291 and 06:9575-9580. Its only do-not line is
  RULING 43's: "⛔ DO-NOT-REOPEN: Whether the watchdog's toast reaches the user and whether its 30-minute window flash is
  acceptable (both yes, 2026-10-21; the monitor stays off)." It does not touch R5. The step-5 entry (06:9280) mentions "a
  check on any stretch where a screen waits for a button" (pacing, PL-1).
- `"save the game"`, exit 0. Three rulings (06:6125-6153, 06:612-622, 06:645-658), all bot-side, with NO do-not line.
  Decomp hits: Battle Frontier save strings and `gText_RegisteredTextChangedOKToSave`.
- `"save scum"`, **exit 3: "NO PRIOR RULING OR FACT FOUND".**
- Extra lookups, both unrelated or teaching only: `"continue from its own save"` (06:2345-2388, party accounting) and
  `"milestone done screen"` (06:4123-4149, the precedent above).

---

## 8. DECIDE EARLY: does R5 fix any of it in place?

- **The definition:** "**⏰ DECIDE EARLY** = the first file the item writes fixes its shape; a later change migrates every
  saved run." (BL:364)
- **The items tagged ⏰:**
  - DP1 + DP2 (BL:387);
  - L3 (a)-(b) (BL:392);
  - L1 + L2 (BL:397). That one is already BUILT as A5 + L1 + L2 / S3-4 (BL:14).
- **Top-15 item 15's tag belongs to the R1 + R2 half:** "DECIDE-EARLY: the first memory file fixes paths and schema" (R4N:44).
- **R5 alone fixes nothing in place.** As recorded, it writes no persisted file (R2N:129-131).
- **Two ways a build could pre-empt a DECIDE-EARLY shape, and both need a decision first:**
  1. **R5 built "inside R6's screen ladder" with R6's `screen_wishlist.jsonl`** (R2N:94). That is a new persisted
     user-data file: "Version every user-data file" (R3D:52), and USER DATA includes `runs/` (R3D:46). The backlog lands
     DP1 + DP2 "WITH R1 + R2", after R5 (BL:193), so the wishlist would be the first file to escape them.
  2. **"and a save" (BL:326) read as R5 doing the saving.** R5 would then ship the first in-game save, DP4 would bind it
     (newest 10, a NEW profile for "new game", BL:375-376), and the framework already keeps every save (section 6).
- **Adjacent, not DECIDE EARLY:**
  - **R3's typed outcomes are NOT built** (`ai_player/outcomes.py` does not exist; CODE). Any new end reason R5 adds is
    another prose string of the kind R3's evidence names: "Control flow reads message prefixes" (R2N:61-64).
  - **R4's run card is NOT built.** "Ended on a free screen: yes or no" would be a natural run-card field (INFERENCE).

---

## 9. Code cross-checks (for the code angle to confirm; not the record)

- **The predicate exists.**
  - `player_free` (AP/hands/dialogue.py:131-137): "The player stands in the overworld with nothing running: no script,
    controls free, no menu, no text, nothing waiting, the position settled."
  - `nav_free` (AP/brain/navigator.py:245-247): `player_free` plus no fade and a view.
- **The settle loop exists.** `play_out` (AP/skills/story.py:148-159) is bounded by `SCENE_ROUNDS`. It returns None when
  free, else "stuck: {SCENE_ROUNDS} scenes and battles in a row after {why}" (:159) or `nav.handle`'s stop.
- **The play loop's order** (AP/mode.py):
  - :457-458 the done check;
  - :459-467 the intro;
  - :471-474 patience;
  - :475-481 `if not nav_free(look):` play out, then `continue`;
  - :482-487 `SETTLE_FREE` after a map change;
  - :494 `goal = manager.next_goal(...)`.
- **⇒ R5's three call sites, one by one:**
  - **Call site 2** (a goal switch after a milestone flips) already holds on every pass that does not end the run, because
    play-out comes before `next_goal`. Inside a goal, `moved_on` ends a walk when the milestone changes
    (AP/brain/goals.py:1882).
  - **Call site 1** is the order gap: :457 comes before :475.
  - **Call site 3** has no code yet (R1).

---

## 10. The doc pairs a finished R5 must update (CLAUDE.md P5: grep its slug, re-read every hit)

- **The backlog:**
  - BL:18, the top-15 status line. The handoff calls BL "whose lines 3-19 and ✅ marks are the status" (04:54).
  - BL:325-326, R5's entry.
  - BL:192, step 6, if the R6 choice changes the order.
- **The handoff:**
  - 04:21, the resume point ("so the PARK TOOL, then R5.");
  - 04:60 ("come with item 4's R5 and R1 + R2");
  - 04:61, queue item 4.
- **The punch list** defers to the handoff: "NEXT: the ORDER is `04` NEXT ACTIONS" (03:83). No punch-list line names R5 by
  ID (grep).
- **Other files:**
  - `06`, for the R5-alone or inside-R6 choice and any save-scum ruling;
  - `07`;
  - AP/LESSONS.md, if a lesson is added. Each needs its gate (AP/LESSONS.md:13-15).
- **RC/00 Q6** (RC/00:728-729) gets its answer.

---

## 11. Open questions (only the user, a live probe or a logged technical call can settle these)

1. **(Technical; Claude's call under RULING 39):** build R5 alone, as the top 15 (BL:18) and 04:61 say, or "inside R6's
   screen ladder" (BL:198)? Log the choice in `06` before building. If R6's wishlist ships, pull DP1 + DP2 forward (section 8).
2. **(Harness or live):** can a development arm REACH "a milestone mark flipped while a box is up, at the top of a
   play-loop pass"? RC/08 says the natural ROXANNE path is free by construction. The candidates:
   - a planted early return inside the talk (RC/08:263);
   - the play loop's own residual (AP/mode.py:477-481);
   - an intermediate target such as `ch1_clock` (`FLAG_SET_WALL_CLOCK` before MOM's text). It is UNVERIFIED that
     `AI_PLAYER_TARGET` accepts it, and that the clock path does not already play out to free.
   The arm needs a reach floor (PF-4) and a check that can FAIL (PF-10).
3. **(USER, a gameplay and human-likeness question):** may the AI reload its own save to undo a loss? It has never been
   ruled (`ask "save scum"` exit 3). R1 (BL:294; R2N:39-40) assumes "No save-scum", and R1 lands right after R5.
4. **(Live probe, R1's "measure that first"):** does `current_save.sav` reach the disk before a hard kill? The framework
   copies each save on `savedata_updated` (LIB:161, :243-255). That is a code reading, not a kill measurement.
5. **(Technical):** if R5 lets the run continue past the badge, the chapter-4 end check must read `VAR_RUSTBORO_CITY_STATE`
   as `>= 1` or sample it at the flip (RC/07:56, D3). Which one?
6. **(Technical):** when a settle cannot reach a free screen within its bound (an unknown menu: R6's case), does the run
   end "stuck" or "done"? DD:409 forbids a silent restart; the record names neither ending.
