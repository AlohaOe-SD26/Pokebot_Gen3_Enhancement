> **Committed 2026-10-29** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/r1r2recon/04-record.md` (sha256 `453f969ee8ab7a47`). Backlog R1 + R2's recon (save, CONTINUE, a memory that survives a kill), angle 4, THE RECORD (rulings, decisions, the backlog, the proof): a read-only Claude subagent's NOTE, never truth (the authoritative docs and the code win). Nothing in it was measured live. R1 + R2's build waits for the user's two save answers (`04` item 4).
> ⚠ **The adversary found WRONG here** (`2026-10-29-R1R2-recon-refute.md` section 0.1): W1, section 0 item 17 and trap 5 (a torn FIRST save leaves no save at all, and every proof run starts from an empty cartridge); W3, item 12 (only the START-menu save and `special SaveGame` raise GAME_STAT_SAVED_GAME; the Hall of Fame save does not); W4, item 13 (no game loss counter rolls back with a save); W6, item 5 (the "own PIDs" words are a code comment, not `06`:9434); W7, item 6 ("Development may use saves" is in the design draft, not `06`); W8, item 4 (the state-write fallback is the story bot's rule; the AI has none); and D-2, which is true of today's call sites only (W9).

# R1 + R2 recon, ANGLE 4: THE RECORD (rulings, decisions, the backlog's text, the pending questions, the proof rules)

A NOTE, never truth (`ai-research-notes/00-READ-THIS-FIRST.md`). Written 2026-10-29 by a read-only recon agent. Nothing in the
repo, the learner clone or `sandbox-pokebot/` was edited; nothing that starts an emulator, a gate, a driver or a test was run.
The only program run was `tools/decomp_lookup.py ask` (read-only, with `-B` so no bytecode was written), plus `git log`, `grep`
and file reads. The game was read in the PINNED clone `C:/Remote Projects/_decomp/pokeemerald` (HEAD `731ad5bf` = `tools/decomp.pin`).

NAME CLASH: "R1" and "R2" here are BACKLOG items (save/CONTINUE; persisted memory), never the step-5 grader checks `R5.*` / `R1.*`.

Tags: **VERIFIED-code** (read in this checkout; path:line), **VERIFIED-decomp** (read in the pinned clone; path:line),
**DOC** (quoted from a project doc; source:line), **UNVERIFIED** (an inference or a claim nobody measured; what would prove it
is named). Agreement between this note and any other agent's note is not proof.

Source abbreviations (all under `PROJECT KNOWLEDGE/` unless a root is named):
- **BL** `ai-research-notes/2026-10-18-improvement-backlog.md`
- **R2N** `ai-research-notes/2026-10-19-backlog-round2/03-ai-player.md` (R1-R15 are defined here)
- **R3D** `ai-research-notes/2026-10-19-backlog-round3/02-deployment.md` (its D1-D13 are the backlog's DP1-DP13)
- **R3L** `ai-research-notes/2026-10-19-backlog-round3/03-long-horizon.md` (L1-L12)
- **R4N** `ai-research-notes/2026-10-19-backlog-round4/02-backlog-review.md`
- **DD** `ai-research-notes/2026-10-07-ai-player-v1-DESIGN-DRAFT.md` (§11 wins over §1-§10; §10 wins over §2-§9)
- **RRR** `ai-research-notes/2026-10-28-R5-recon-record.md` (a NOTE; used only as a pointer, every claim taken from it was re-read)
- **06 / 07 / 08 / 01 / 04** the numbered docs; **AP** = `ai_player/`; **SB** = `sandbox-pokebot/`; **PD** = the pinned decomp.

---

## 0. The answers in brief

**(a) What binds saving, continuing, resuming and memory**
1. **No user ruling exists on the AI's in-game saving, CONTINUE or save-scumming.** `decomp_lookup.py ask "save scum"` and
   `ask "reload a save to undo a loss"` both print "NO PRIOR RULING OR FACT FOUND" (exit 3); `ask "save"`, `"save state"`,
   `"continue"`, `"profile fresh"`, `"resume after a crash"` return only bot-side or unrelated entries, none with a do-not line;
   `RULINGS.md` lists no save ruling. [VERIFIED-code: tool output 2026-10-29; DOC RULINGS.md]
2. **The backlog's R1 + R2 text, "No save-scum" included, is a CANDIDATE:** "What these are: candidates, not decisions. Each
   becomes a decision (`06`) and a punch-list status when built." [DOC BL:28] The two save questions were asked 2026-10-28
   5:27 PM and are unanswered; the handoff says to record the answers as USER RULINGS in `06`. [DOC 04:61; 07:39032]
3. **Who decides what (USER RULING 39):** "TECHNICAL decisions are Claude's" and "Decisions about what the AI IS and how it
   should BEHAVE go to the user" [DOC 06:9392-9393]. So WHEN it saves and WHETHER it may reload are the user's; paths, schema,
   the memory stamp, retention and the proof are Claude's, each logged in `06`. [UNVERIFIED: the split is my reading of 9392-9393]
4. **HOW it may save or resume is already bound:** the AI plays by its own presses, no bot code (RULINGS 35, 36, 41)
   [DOC 06:9222, 9233, 9503]; its code may not call `load_save_state`, `load_save`, `reset`, `create_save_state` and the
   like [VERIFIED-code AP/gates/check_purity.py:536-550], and the instrument counts any emulator or core load while it runs
   [VERIFIED-code AP/host/attribution.py:25, 179-180; DOC DD:400-408]. So a save is START > SAVE pressed, a resume is the
   title's CONTINUE pressed, never a state load; a state-write is "a documented last-resort fallback" [DOC CLAUDE.md:256-258].
5. **WHAT it may read stays person-fair (RULING 40, live hidden state):** its own party PIDs are allowed ("a person knows which
   of their own Pokemon they sent out") [DOC 06:9434; VERIFIED-code AP/eyes/observation.py:275-276]; the play time a memory
   stamp would use is SHOWN on the save window and on the CONTINUE window, to the minute [VERIFIED-decomp PD
   src/start_menu.c:1385-1390; src/main_menu.c:2142-2152]. The eyes do not read play time today [VERIFIED-code: grep of
   AP/eyes, AP/brain, AP/mode.py finds none].
6. **Deployment:** one standalone program that loads the ROM itself, "easy to run as an art piece" (RULING 37 Q1), at x1,
   which "creates a profile/uses an existing profile and plays the game from beginning to end" (RULING 41)
   [DOC 06:9251, 9499; 01:20-29; DD:378]. OFFICIAL acceptance starts from a real New Game, and "Development may use saves"
   [DOC DD:381; 06:9254]. "Give-up and crashes end the process; they never silently restart or park." [DOC DD:409]
7. **Prior intent on resuming, bot era (RULING B, 2026-08-14):** "continue where it left off in the event that the bot gets
   turned off during sudden power loss OR I turn it off for a period of time and turn it back on to have it continue"; Claude
   recorded it as a "RESUME/DURABILITY capability", separate from play [DOC 06:2238-2249]. It is not a ruling on the AI
   (RULING 35 makes the bot a teacher) [UNVERIFIED: inference, as RRR also says].
8. **Already decided (technical):** R5 is built as R1's free-screen precondition; "D8 kept: no save here; the save is R1's"
   [DOC 06:9858, 9864; VERIFIED-code AP/mode.py:676-707]. The whole-game goal needs CONTINUE anyway: the game autosaves in the
   Hall of Fame, soft-resets after the credits and comes back through the title's CONTINUE [DOC 06:5679-5692; VERIFIED-decomp
   PD src/hall_of_fame.c:518-526; src/post_battle_event_funcs.c:36-41].

**(b) The backlog's text and what DECIDE EARLY fixes**
9. R1 + R2 [DOC BL:290-294]: "save_game and CONTINUE read by their words, saving only on a free screen (R5); one memory.jsonl
   (full lines plus deltas) stamped with play time, so a resume loads memory NOT NEWER than its save. UNVERIFIED first: does
   mGBA flush the save before a kill? No save-scum." Folded in, DP4 [DOC BL:378-379]: ".sav is the durable copy (.ss1 is tied
   to the emulator build); keep the newest 10; deploy "new game" makes a NEW profile and "retire" archives, never a silent
   `--fresh` wipe." "DP1 + DP2 and L3 (a)-(b) land WITH R1 + R2, before its first memory file" [DOC BL:193-194].
10. DECIDE EARLY = "the first file the item writes fixes its shape; a later change migrates every saved run" [DOC BL:367].
   Before the first memory file the record wants six things decided: (i) one `AppPaths`, four data classes (program,
   knowledge, user data, the key), `AI_PLAYER_HOME`, a gate on path literals [DOC R3D:44-50; BL:390-393]; (ii) a
   `schema_version` on every user-data file, a NEWER file refused byte-identical, an older one migrated after a backup copy
   [DOC R3D:52-56; BL:393]; (iii) `memory.jsonl` through the existing `RecordFile`: full lines plus deltas, BOTH memories (world
   and goal manager), a version field, a loader that restores both [DOC R2N:52-55]; (iv) a stamp so a resume loads memory NOT
   NEWER than its save [DOC BL:293-294]; (v) every mon by PID and species, with ROLES, from the first line [DOC BL:395-399;
   R3L:95-98]; (vi) profile = one playthrough = one save, with DP4's retention and no silent wipe [DOC R3D:66-71].
11. **Left OPEN by the record:** the stamp key (BL says "play time"; R2N says "play-time or save counter") [DOC BL:293;
   R2N:54]; where `memory.jsonl` lives (`RecordFile` writes only into a run's folder today; DP1 lists a `memory/` user-data
   folder) [VERIFIED-code AP/runlog.py:55-58; DOC R3D:46]; which fields roll back on CONTINUE (R2's per-playthrough memory vs
   RULING 40's experience across games) [DOC 06:9430; UNVERIFIED design]; DP4's "newest 10" against the framework's
   unbounded `saves/` copy of every in-game save, in a framework that may not be edited [VERIFIED-code
   SB/modules/libmgba.py:160-161, 243-256; DOC 06:9261]. Play-time stamps alone are ambiguous after two resumes on different
   branches [UNVERIFIED: inference; a two-resume unit test would prove or refute it].

**(c) The two pending user questions**
12. **"When does the AI save?"** changes: whether saving is a goal with personality triggers (R2N's proposal: "after a Center
   heal, after a badge, before a gym, before a long route; a careful archetype saves more") or a safety timer, or both
   [DOC R2N:32-33]; what a crash or power cut costs at x1 (216,000 frames an hour) [DOC BL:292]; how often a full memory line
   is written; how fast DP4's backups rotate; whether a planned stop saves first (RULING B's "turn it off ... and turn it back
   on"); and what graders count (a told save can be checked against the game's own `GAME_STAT_SAVED_GAME`, which every
   in-game save increments) [VERIFIED-decomp PD src/start_menu.c:1090; include/constants/game_stat.h:4].
13. **"May it reload a save to undo a loss?"** NO (the backlog default; "a resume is for crashes only") needs a new gate,
   because purity covers API loads but not a button soft reset or a quit to the title [VERIFIED-code check_purity.py:536-550;
   UNVERIFIED that the instrument misses the game's own SoftReset]; it collides with R7's ladder rung "quit and CONTINUE from
   its own save" and R15's relaunch "for the benign codes" [DOC R2N:141, 201]; and a crash after a loss still undoes the loss.
   YES needs R11's defeat ledger to survive the rollback (so R2's NOT-NEWER rule splits by field), graders that count across
   reloads (the game's counters roll back), a retry bound (PL-4), and it weakens the vision's "losing and recovering".
   A NARROW yes (for example a fled legendary) keeps defeats on NO. [UNVERIFIED: design consequences; DOC 01:14]
14. **Prior statements that answer IN PART (none answers either question for the AI):** bot "User #1", 2026-07-21: "on
   defeat the bot must navigate the whiteout and continue from the respawn point, never reload a save state" [DOC 07:1083-1085];
   vision: "healing at Centres, losing and recovering" [DOC 01:13-14]; RULING 40: "makes human-like choices and mistakes"
   [DOC 06:9431]; the bot's whiteout loop at the League is "BY DESIGN" (reload was not among the options offered)
   [DOC 06:5353-5359]; RULING B (resume after a power loss or a deliberate stop) [DOC 06:2238-2243]; RULING 41 "uses an
   existing profile" [DOC 06:9499]; the user's standing offer to answer gameplay questions names "checkpoints"
   [DOC 06:5640-5645].

**(d) The proof**
15. Asked: "(A; proof: kill, CONTINUE, same PIDs and tile)" [DOC BL:290]. R2N's arms: "play to a Center, save, KILL the
   process, relaunch with only the `.sav`, CONTINUE, assert the same party PIDs, map and tile (identity, not counts); a fault
   arm that kills before the save must resume EARLIER", the flush measured first; R2's test "fuzz the kill frame, resume,
   compare the two memories field by field"; DP2's "hand-edit a future version in, expect a refusal and a byte-identical file"
   [DOC R2N:37-39, 56-57; R3D:55-56].
16. Rules that apply: held-out seeds registered before play, played once, a crash still spends them [VERIFIED-code
   AP/gates/ledger.py:1-36]; FAULT + CONTROL per guard, a mutant that deletes the CALL, a control that can fail, a reach
   floor [DOC AP/LESSONS.md PF-2, PF-3, PF-4]; identity, never slots or counts [CLAUDE.md rule 3; PL-10]; targets read from
   the state reached [rule 4; PF-5]; "without X" claims need an arm with X removed [rule 8]; launcher arms read the host clock,
   so each is one trajectory [DOC LESSONS EN-1, PF-9]; graders read the game, never the AI's own record [DOC BL:106-107;
   PF-6]; the R5 precedent (measure first, OLD/NEW by revert mutant, held-out A/B plus a PF-17 control, the full lane after
   the commit) [DOC 07 2026-10-29].
17. Traps the record exposes for that proof: the emulator auto-loads `current_state.ss1` at startup, so a relaunch must prove
   it came through the title's CONTINUE [VERIFIED-code SB/modules/libmgba.py:141-146; DOC 08:8437]; today's intro picks NEW
   GAME by its words even when CONTINUE is listed [VERIFIED-code AP/skills/intro.py:113-115; AP/eyes/screens.py:260-265], and
   a New Game over a save meets the game's "different game file ... entirely lost" warning (default NO) at its first save
   [VERIFIED-decomp PD src/new_game.c:154; src/start_menu.c:1035-1051; data/text/save.inc:15-23]; the game sets a special
   continue warp after the Hall of Fame and in link, contest, frontier, trade and some save/start-menu paths [VERIFIED-decomp:
   the call sites in 5.3], and after the Hall of Fame a CONTINUE goes to the bedroom, not the saved tile [DOC 06:5685-5691]
   (the dynamic cases: UNVERIFIED), so the proof saves on a plain overworld tile;
   the save tile and party must differ from the kill point or "same PIDs and tile" passes by construction [UNVERIFIED:
   CLAUDE.md Tier 2 (4) applied]. The flush question stays UNVERIFIED: the bytes go through mgba.dll's VFile, and the game
   writes the other of two slots each save, so a torn write should leave the older save [VERIFIED-code SB/mgba/vfs.py:90-108;
   VERIFIED-decomp PD include/save.h:12; src/save.c:187, 587-604; UNVERIFIED: the timing of the disk write before a kill].

---

## 1. How this note was made (so its gaps are visible)

- Read in full: BL's R1+R2, DP1+DP2, DP4, L3 entries and its order, summary, folded and rejected lists; R2N whole; R3D whole;
  R3L's L3, L11, L12 and cross-links; R4N sections 1-3; DD §9-§11; the 06 entries for RULINGS 32-42, 48, 50, RULING B/C
  (2026-08-14), the 2026-07-26 profile entries, the 2026-09-16 spend-down ruling, the 2026-09-17 §Ch24 rulings, R5's
  2026-10-29 entry; 01's north star, components and non-goals; `ai-agent/HUMAN-PLAY-DESIGN.md` (nothing on saving);
  `ai_player/LESSONS.md` whole; the README's run options and world-memory passages; `RULINGS.md` by grep.
- `06` was grepped for: save-scum, reload, CONTINUE, `current_save`, `.sav`, `--fresh`, `seed_profile`, the marker, whiteout,
  rewind, watchdog, RULING B, resumable, P13, "bot save", "own presses". `decomp_lookup.py ask` was run for nine topics (2.10).
- Code was read only to verify the record's own citations and the traps in 5.3. The code angle and the game angle own the
  deeper reads (the mGBA flush, the CONTINUE warp path, the eyes on the title screen).

---

## 2. (a) Every ruling or decision that binds R1 + R2, quoted

### 2.1 The goal: play like a person, the whole game, a seasoned player (RULINGS 32, 40, 41)

- **RULING 32 (2026-10-03):** "play it faithfully as well as organically like a human, including completing the story ...
  the goal is to make it play exactly as a human would and make sure it doesnt robotically speed run to the end ... the
  ultimate goal of this is to look and act as human as possible in the end" [DOC 06:9114-9118].
- **RULING 40 (2026-10-15):** KNOWLEDGE all allowed; "**EXPERIENCE: allowed.** It remembers across playthroughs what worked
  (the levels a boss needed, the moves that won, places it got stuck). It starts each New Game knowing more than the last
  time." [DOC 06:9430]. "**BEHAVIOUR: must stay human.** Each new game is still PLAYED like a person: it explores, detours,
  takes opportunities, and makes human-like choices and mistakes." [DOC 06:9431]. "**STILL NOT ALLOWED: LIVE HIDDEN STATE**
  a player cannot see. That is the RNG, a wild Pokemon's PID, IVs, nature or held item before the game shows them, the foe's
  exact stats, upcoming encounters, and anything the screen does not show NOW." [DOC 06:9434].
  ⇒ Two memories with different scopes: R2's memory lives within ONE playthrough; RULING 40's experience crosses playthroughs.
  A CONTINUE rolls back the first and must never roll back the second. [UNVERIFIED: inference, also drawn in RRR:358-362]
- **RULING 41 (2026-10-16):** "it launches the emulator, loads the rom, creates a profile/uses an existing profile and plays
  the game from beginning to end (maybe some setup settings/steps before the ai takes over) so the ai is taking the drivers
  seat in place of the human, without any bot usage" and "so long as we are training an ai agent to deploy that can play the
  game entirely on its own the way I described without using bots, that is my goal ... I am fine with it taking time to
  complete" [DOC 06:9499-9500]. "The end state is the standalone program of RULING 37." [DOC 06:9506]
  ⇒ "uses an existing profile" is the user's own words for continuing a playthrough; it does not say how. [DOC; inference]
- **RULING 33 (post-game):** "post champion/elite 4 main personality should change to focusing on completing the pokedex"
  [DOC 06:9142-9143]. The post-game starts after the game's own autosave and a CONTINUE (2.7). [VERIFIED-decomp; inference]
- **The north star (bot, 2026-08-11), the vision's statement of "faithful":** "walking the routes, talking to the NPCs,
  fighting the trainers, teaching the HMs, healing at Centres, losing and recovering." [DOC 01:12-14]
- **The art piece at x1 (2026-09-18):** "the goal is to make this bot play as human as possible (at regular speed, not sped
  up) as it will be an art piece I can look at from time to time to see its progress" and "regular speed is 'x1' or normal
  speed for the actual production gameplay, speed up is for dev testing" [DOC 01:20-27]. At x1 an hour is 216,000 frames
  [DOC BL:292], so what a crash costs is real time.
- **Non-goal (upstream's philosophy):** "upstream deliberately plays 'as if human' (no RNG manipulation, no memory writes for
  outcomes). Deviations from this are per-feature decisions." [DOC 01:130-132]

### 2.2 Deployment: a single standalone program, an art piece (RULING 37 Q1)

- **The user (2026-10-07):** "1: Whatever you think is best for organization, I do plan to eventually split things up to the
  point where it would be a single program that would run as the ai and load the rom automatically and all that so keep that
  in mind so it would be easy to run as an art piece like I mentioned." [DOC 06:9251]
- **Applied:** "`ai_player/` package at the repo root, with its own entry point ... **Built from day one to become a single
  standalone program** that loads the ROM itself and runs as an art piece (the user's stated plan): no hard-coded paths to
  the bot, and everything else behind the adapters." [DOC DD:378; 06:9260]
- **The launcher is the swap point today:** "it is the seam that a standalone build will replace with its own ROM loader
  (RULING 37 Q1)"; "Nothing here is on a hard-coded absolute path" [VERIFIED-code AP/host/launcher.py:3-6, 12-14].
- **Round 3's deployment decisions (CANDIDATES, renamed DP1-DP13 in BL):** "Most of the choices below cost a few dozen lines
  TODAY and are expensive to retrofit once saves, memory and settings exist in the wild ... make the data-shape decisions
  (D1-D8) NOW." [DOC R3D:12-14]. DP1, DP2, DP4 are quoted in 3.3; DP5 (personality `cycle`, "a counter in `data/`") is also a
  persisted user-data file [DOC R3D:73-75].
- **Scheduled tasks are approved only for two ops tasks:** "This approval covers these two ops tasks, not scheduled tasks in
  general." [DOC 06:9526] ⇒ an autostart that relaunches the AI after a reboot (RULING B's power-loss wish, R15) would need a
  new user approval. [UNVERIFIED: inference from the quote]

### 2.3 What the AI's code may touch (RULINGS 35, 36; the purity gate; the instrument)

- **RULING 35:** "The AI should be doing the navigation of the map, battles, interfaces, decisions, etc... as I would like to
  not have any bot like movements or usage of the bot in the AI version" [DOC 06:9222].
- **RULING 36:** "EYES = memory reading through the emulator ...; CONTROLLER = the AI presses buttons itself; BRAIN =
  entirely the AI's own (no bot pathfinding, battle strategies or menu scripts while playing, RULING 35)." [DOC 06:9233]
- **Design §10.2, adopted:** "the watchdog loads save states or switches to manual ... The purity metric counts foreign
  presses, foreign memory writes and save-state loads, and all three must be 0 ... An AST gate bans calls in the AI's code to
  `write_symbol`, `write_to_save_block`, `set_event_flag`, `set_event_var`, `write_bytes`, `load_save_state` and `reset`."
  [DOC DD:400-408]
- **The gate as built:** `STATE_CHANGING_NAMES` includes `"load_save_state", "load_save_game", "load_state",
  "load_state_slot", "load_save", ... "reset", "loadState", "loadSave", "create_save_state", "advance_time"`
  [VERIFIED-code AP/gates/check_purity.py:536-550].
- **The instrument as built:** "loads emulator.load_save_state / load_save_game / reset; the mGBA core's load_state,
  load_state_slot, load_save, load_temporary_save, load_raw_state, load_patch, reset" are counted by origin while the AI runs
  [VERIFIED-code AP/host/attribution.py:25-26, 179-180].
- **The 2026-10-07 stop of purity hardening:** "The static gate (framework doors only; no write/load/reset) and the live
  attribution of foreign presses, writes and loads cover that, and both are fault-tested." [DOC 06:9269]
- **CLAUDE.md (Story-bot craft):** "Faithful to natural gameplay — a state-write is a documented last-resort fallback that
  must reproduce vanilla's exact end-state." [DOC CLAUDE.md:256-258]
- ⇒ R1's save must be the in-game START > SAVE and its resume the title's CONTINUE, both by button presses; R8's state ring
  is host-side ("the HOST side (the instrument writes files, not the AI)") [DOC R2N:104]. [inference, consistent with RRR:383-387]
- ⚠ What the gate does NOT cover: a person-style reload by buttons. The framework's own `soft_reset` calls
  `context.emulator.reset()` (banned for the AI) and then presses through TITLE and MAIN_MENU [VERIFIED-code
  SB/modules/modes/util/soft_reset.py:13-45]; a reset the GAME performs (the A+B+START+SELECT combination) is game code, not an
  emulator API call. [UNVERIFIED: that the instrument does not count it; the code angle should read where the game's
  `SoftReset` is reached and whether `attribution.py` sees it]

### 2.4 Save STATES as fixtures and start points

- **RULING 37 Q4:** "4: Yes, for the official acceptance runs (including naming and clock setting)" [DOC 06:9254];
  applied as "A real New Game for OFFICIAL acceptance runs (naming and clock included). Development may use saves."
  [DOC DD:381]. The intro skill cites it [VERIFIED-code AP/skills/intro.py:1-2].
- **Bot saves as AI start states, REJECTED (a backlog rejection, not a 06 ruling):** "P13's bot saves as AI start states:
  REJECTED (USER RULING 35, recon Gap 9); its index lives on in R8 + R9." [DOC BL:355]. R9: "A chapter never starts from a bot
  save again." [DOC R2N:117-118]. L11: "a late-game SKILL may be proven on a pinned bot fixture with a control arm; 'the AI beat
  X' counts only from the AI's own chain." [DOC BL:380-381] (No `06` entry records P13's rejection: grep of 06 for "P13",
  "Gap 9", "bot save" finds none.) [VERIFIED-code: grep]
- **Today's development resume:** chapter 2 runs from `--state <that run's end state>` plus `AI_PLAYER_WORLD=<that run's
  dir>/world.jsonl` [VERIFIED-code AP/README.md:416-419].
- **The two kinds of save, a recorded mistake:** "`.sav` and `.ss1` are not the same kind of save. A `.sav` holds what the
  game persists; a `.ss1` holds the whole machine — RAM, callbacks, task list, mid-script state." [DOC 08:4072-4074]

### 2.5 Resuming, profiles, `--fresh`

- **RULING B (bot, 2026-08-14), verbatim:** "currently we are using the reset feature for testing from fresh saves… the goal
  would be every run (Option A) but since the goal is to have the bot have the option through my intervention to pick up
  where it left off… the idea would be to get it to also be able to continue where it left off in the event that the bot gets
  turned off during sudden power loss OR I turn it off for a period of time and turn it back on to have it continue (So
  option A and B maybe?)" [DOC 06:2238-2243]. Claude's reading, recorded: "(2) 'Pick up where it left off' is a
  RESUME/DURABILITY capability (a named profile's save resumed after power loss or a deliberate shutdown, at the user's
  intervention), which is orthogonal to the dex and applies to the whole bot." [DOC 06:2245-2249]
- **Profiles are per process (bot, 2026-07-26):** "Two bot processes sharing a profile directory clash on
  `current_save.sav`" [DOC 06:617]; headless lanes use their own profiles for the same reason [DOC 06:1089-1091]. ⇒ a resume
  must not start while the killed process still holds the profile. [UNVERIFIED: inference]
- **The AI launcher's marker rule:** "Only a profile carrying it may have its game state wiped (`--fresh`) or replaced
  (`--state`), so a person's own profile is never touched." [VERIFIED-code AP/host/launcher.py:84-86, 191-195]
- **What `--fresh` deletes today:** `current_state.ss1`, `current_save.sav` and every `states/*.ss1`, silently, then "->
  title screen / New Game" [VERIFIED-code AP/host/launcher.py:196-205]. It does NOT delete `saves/` (the framework's copy of
  every in-game save) [VERIFIED-code: the loop names only those files]. DP4 asks for the opposite in deploy mode: "never a
  silent `--fresh` wipe" [DOC BL:379].
- **With neither flag:** "resuming whatever the profile already holds" [VERIFIED-code AP/host/launcher.py:187-188]: the
  emulator loads `current_state.ss1` if it exists ("to continue exactly where we left off"), else the game boots to the title
  with the `.sav` behind it [VERIFIED-code SB/modules/libmgba.py:141-146]. The state is written only by a CLEAN close
  (`atexit` -> `shutdown` -> `create_save_state`) [VERIFIED-code SB/modules/libmgba.py:160, 231-241, 201-229]; the launcher's
  hard kill is `psutil...kill()` / `taskkill /T /F` [VERIFIED-code AP/host/launcher.py:351-372], which runs no `atexit`.
- **The framework keeps every in-game save, unbounded:** `backup_current_save_game` "is called every time the emulator writes
  out the save game ... we keep a copy of every save ever created and put it inside the profile's `saves/` directory"
  [VERIFIED-code SB/modules/libmgba.py:160-161, 243-256]. The framework may not be edited: "the framework is not edited"
  [DOC 06:9261; DD:379]. ⇒ DP4's "keep the newest 10" must be host-side or reconciled. [UNVERIFIED: inference, as RRR:351-353]
- **A recorded trap with this exact file:** "Gitignored is not the same as harmless: the next run of that profile loads it."
  and "Before a tool may claim 'nothing was changed', diff the working tree AND the profile directory across a run"
  [DOC 08:8427-8441]. "a cleanup in a generator's `finally` is only as reliable as the caller's promise to resume it. Treat a
  frame-capped smoke run as a run with NO cleanup." [DOC 08:21145-21146] ⇒ a save made at teardown is not a save; R1 must save
  during play. [UNVERIFIED: inference]

### 2.6 Losses, whiteouts and reloads (bot-side precedents; none rules the AI)

- **"User #1" (bot, 2026-07-21), as the changelog records it:** "on defeat the bot must navigate the whiteout and continue
  from the respawn point, never reload a save state (the watchdog was rewinding to older and older states)." Built: "the
  watchdog never reloads a save state or auto-restarts for Story" [DOC 07:1082-1089; 28-HANDOFF-ARCHIVE.md:2673-2681]. The
  user's verbatim words are not in the repo (grep); the directive is about the BOT and emulator save STATES. [VERIFIED-code: grep]
- **The bot's League whiteout loop is by design (2026-09-16, DO-NOT-REOPEN):** "Without an attempt cap, a whiteout loop has
  no floor ... If an unattended run is ever seen looping in the League, this is the known cause and it is BY DESIGN — the fix
  is a new ruling from the user, not a unilateral cap." [DOC 06:5353-5359]. The options offered were re-stock, attempt cap and
  re-earn; reloading was not offered [DOC 06:5345-5351], so this says nothing direct about reloading. [inference]
- **A bot design note:** "§Ch24 is a one-way gauntlet with no save-scumming and no nurse." [DOC
  ai-research-notes/2026-09-04-ch24-LEAGUE-INTERIOR-ROUTING.md:11] (Claude's framing, not a user ruling.)
- **A development reload, not a gameplay one (bot, 2026-09-17 RULING 1):** after a lost Ice Beam, "the only remedy is to
  re-grind from a save that still holds it" and the re-grind resumed from a fixture [DOC 06:5656-5660]. That is a developer
  choosing a fixture (RULING 37 Q4's "Development may use saves"), not the bot reloading in play. [inference]
- **The game itself never reloads on a whiteout:** "There is no save reload and no party rollback." [DOC
  ai-research-notes/CLAUDE-VALIDATED-concepts-round1.md:43, citing PD src/overworld.c:358-366]
- **A research note listed save-and-reset and state save-scumming as OPTIONS for the bot's boss walls** [DOC
  ai-research-notes/concept-notes-c10.md:31-47]; nothing adopted them. [VERIFIED-code: grep of 06 finds no adoption]
- **RULING C shows the user CAN sanction a non-faithful exception explicitly** ("we can bend the rules ... which breaks
  organic/faithful gameplay"), recorded as flagged, OFF by default and logged [DOC 06:2253-2269]. ⇒ if reloads were wanted,
  the record's shape for it would be an explicit, flagged deviation. [UNVERIFIED: inference]

### 2.7 The endgame save and CONTINUE (bot rulings, game facts the AI inherits)

- **The user (2026-09-17, RULING 3 on §Ch24):** "yes drive through the post game save, but verify that the game auto saves
  once going through the hall of fame (I believe it does)" [DOC 06:5679-5680]. Verified: "the game DOES auto-save inside the
  Hall of Fame, BEFORE the credits and before the reboot" and "Hall of Fame → autosave → credits → soft reset → title →
  CONTINUE → Littleroot bedroom" [DOC 06:5684, 5692].
- Re-read here: "SAVING... DON'T TURN OFF THE POWER" then `TrySavingData(SAVE_HALL_OF_FAME)` [VERIFIED-decomp PD
  src/hall_of_fame.c:518-526]; `SetContinueGameWarpStatus(); SetContinueGameWarpToHealLocation(...HOUSE_2F)`
  [VERIFIED-decomp PD src/post_battle_event_funcs.c:36-41].
- ⇒ RULING 41's whole game plus RULING 33's post-game need a CONTINUE skill even if no crash ever happens. [UNVERIFIED: inference]

### 2.8 Who decides, and how to ask

- **RULING 39:** "TECHNICAL decisions are Claude's: architecture, process, tooling, learner settings. Each is explained in
  plain English with its evidence and recorded here." / "Decisions about what the AI IS and how it should BEHAVE go to the
  user." [DOC 06:9392-9393]. Its open question "should the AI play every game as a first-time player, or as one who remembers
  past playthroughs" [DOC 06:9418] was answered by RULING 40 (remembers) [DOC 06:9422].
- **The gameplay oracle (2026-09-17):** "if you have any questions about how the game is played from a gamer perspective …
  you can ask me" ... "Named areas: gameplay mechanics, mapping from a visual standpoint, checkpoints, story logic. Ask in
  plain English with gameplay verbiage, not in code or decomp terms." [DOC 06:5640-5645]
- **Rule 11 (CLAUDE.md):** grep `06` before escalating; `decomp_lookup.py ask` first; "a no-hit is not proof".
- **A user statement on crash-cut games, tuner side (RULING 48):** games that finish before a crash COUNT; lost games are not
  backfilled; "Do not re-ask" [DOC 06:9807-9812]. Context only: it rules the tuner's ranking, not the AI's saves.

### 2.9 Technical decisions already taken that touch R1 + R2

- **R5, 2026-10-29:** "D1 kept: R5 alone, before R6's screen ladder. **Why:** R6 is not built, and R1's save needs a free
  screen now." and "D8 kept: no save here; the save is R1's." [DOC 06:9858, 9864]. The settle's docstring: "A person finishes
  what is on screen before putting the game down, and a save (backlog R1) is possible only on a free screen." [VERIFIED-code
  AP/mode.py:682-683]. The vision records the same [DOC 01:447-449]. LESSONS PL-18: "One free look is not a free screen"
  [DOC AP/LESSONS.md:357-361].
- **The play loop treats the title as a New Game:** "the title screen: a New Game (nothing is saved yet)" [VERIFIED-code
  AP/mode.py:460-461]; a second intro in one run ends it "stuck" [VERIFIED-code AP/mode.py:488-495].
- **Order:** "6. Step 5.3, then chapters 3-4, on D1, D2 and R6, R5, R1 + R2, R8 + R9, R12 ... DP1 + DP2 and L3 (a)-(b) land
  WITH R1 + R2, before its first memory file (round 3: that file fixes paths and schema)." [DOC BL:192-194]. Top-15 item 15:
  "R1 waits for the user's two save answers (`04` item 4)." [DOC BL:18]

### 2.10 What the prior-ruling lookup found (`py -3.12 -B tools/decomp_lookup.py ask "<topic>"`, 2026-10-29)

| topic | result |
|---|---|
| "save" | 3 bot-side rulings (06:612-622 profiles per lane; 06:645-658 badge recorder; 06:6125-6153 lobby fixture); no do-not line |
| "save scum" | exit 3: NO PRIOR RULING OR FACT FOUND |
| "continue" | 5 unrelated rulings (batched validation, party accounting, §Ch21/§Ch23 "can continue" checks, catching) |
| "save state" | the same three as "save" |
| "resume after a crash" | E2 + O8 (tuner journal, 06:9821-9830); 2026-10-15 usage-safe operation (06:9333-9365) |
| "reload a save to undo a loss" | exit 3: NO PRIOR RULING OR FACT FOUND |
| "whiteout loss" | 5 bot rulings (Winona/Tate & Liza prep, reserve slots, Archie loss branch, second wind, a superseded League floor) |
| "profile fresh" | 06:612-622, 06:598-610 (lane profiles), RULING 41 (06:9496-9510) |
| "memory file" / "standalone program art piece" | KI-93 refusal memory, tile bridge, RULING 36 / RULING 37 |

[VERIFIED-code: tool output; the `06:<n>` lines it prints are quoted from 06 itself]

---

## 3. (b) The backlog's text and its review rounds

### 3.1 R1 + R2 in the backlog, verbatim [DOC BL:290-294]

> - **R1 + R2. The AI SAVES and CONTINUES, and its memory survives a kill.** (A; proof: kill, CONTINUE, same PIDs and tile)
>   **Evidence:** no skill saves (`skills/intro.py:9`); the resume file is written on a CLEAN close only (`libmgba.py:141`);
>   `_Memory` is not carried (`brain/goals.py:62`); at x1 an hour is 216,000 frames. **What:** `save_game` and CONTINUE read
>   by their words, saving only on a free screen (R5); one `memory.jsonl` (full lines plus deltas) stamped with play time, so
>   a resume loads memory NOT NEWER than its save. UNVERIFIED first: does mGBA flush the save before a kill? No save-scum.

Citation check: `skills/intro.py:9` still reads "NEW GAME, chosen by reading the cursor (on a fresh save it is the first of
two)" [VERIFIED-code]; `libmgba.py:141` still reads "Whenever the emulator closes, it stores the current state in
`current_state.ss1`." [VERIFIED-code]; `brain/goals.py:62` is STALE: the words are now at :447-450, "(the memory is carried
between sessions, `AI_PLAYER_WORLD`; this goal manager's own memory is not)", and `class _Memory` is at :407-496
[VERIFIED-code]. `mode.py:104-105` `STORY_PATIENCE = 120_000`, `MAX_LOSSES = 3` still hold [VERIFIED-code].

### 3.2 R2N's full R1 and R2 (the details the backlog compressed) [DOC R2N:22-57]

- R1 What: "(1) a `save_game` skill that opens START, reads the cursor on SAVE, answers the overwrite question by its words,
  and waits for the "saved" text; (2) an intro branch that reads the main menu and picks CONTINUE when it is there, then
  settles on the overworld; (3) a "when to save" rule by personality (after a Center heal, after a badge, before a gym, before
  a long route; a careful archetype saves more); (4) a rule that saving is allowed only on a free overworld screen (see R5)."
  [R2N:31-34]
- R1 Benefit: "a crash, a Windows update or a power cut costs minutes of play instead of the run. It is also what a person
  does, so it is faithful ... It is the base of R2, R7, R8 and R15." [R2N:35-36]
- R1 Risk: "Risk of save-scumming: forbid reloading to undo a loss (a resume is for crashes only), and say so in
  `LESSONS.md`." [R2N:39-40]
- R2 What: "one `memory.jsonl` through the existing `RecordFile` (no new file writer for the purity gate, `runlog.py`
  docstring): a full line now and then, deltas between, both memories in it, a version field, and a loader that restores both.
  Stamp each line with the game's own play-time or save counter, so a resume picks the newest memory NOT NEWER than the save it
  loaded (a memory that "remembers" a gift the save lost is the one inconsistent state this design creates)." [R2N:52-55]
- R2 evidence for size: `world.jsonl` appends a FULL snapshot at every map change, "17,389 / 42,503 / 42,503 bytes at 889
  tiles learned"; a whole game "plausibly gigabytes" (an ESTIMATE). [R2N:48-51; VERIFIED-code AP/mode.py:949, 960-961]
- "R1 + R2 together (a save is only half a resume)" and "R1 + R2 (one step, one live kill-and-resume proof)". [R2N:17, 215]

### 3.3 DP1, DP2 and DP4 (round 3, folded and placed WITH R1 + R2)

- **BL:390-394, verbatim:** "**DP1 + DP2. One `AppPaths` and a `schema_version` on every user-data file.** (A, ⏰ DECIDE
  EARLY) **Evidence:** the dev default is `<repo>/sandbox-pokebot` and a profile needs a donor (`launcher.py:89,145-165`); R2's
  memory, R11's ledger and R8's `INDEX.json` will be the first persisted AI files. **What:** four data classes (program,
  knowledge, user data, the key), `AI_PLAYER_HOME`, a gate on path literals outside the dev resolver; a NEWER file is refused
  byte-identical, an older one migrated after a backup copy. **Cost:** about 60 lines and a fault arm per rule."
- **R3D D1 (the source):** USER DATA = "`settings.json`, `roms/`, `profiles/`, `memory/`, `runs/`, `consult_ledger.jsonl`,
  `crash-reports/`"; default layout "a portable folder `EmeraldAI/` with `program/` and `data/` side by side (delete the
  folder = uninstall; back up = copy `data/`)"; "Gate: no `sandbox-pokebot`, `C:/`, `Remote Projects` or `endless-P1` outside
  the dev resolver." [DOC R3D:44-50]
- **R3D D2:** "Each of `settings.json`, the memory files, the ledger and the profile marker carries `schema_version`. An older
  program that meets a newer version stops with a plain message instead of 'fixing' it; a newer program migrates forward only,
  after copying the old file to `data/backup/<date>-<version>/`. This single rule is what makes rollback safe, and it cannot be
  added after the first friend's memory file exists. Fault arm: hand-edit a future version in, expect a refusal and a
  byte-identical file." [DOC R3D:52-56]
- **R3D D4 = DP4:** "**Profile = one playthrough = one save.** The cartridge save (`current_save.sav`) is the durable truth;
  `.ss1` states are tied to the exact emulator build and ROM, so they are a convenience, never the only copy. Keep a rotating
  `.sav` backup (say the newest 10, every in-game save and before every update). `--fresh` on an existing profile must not
  silently wipe it: in deploy mode "new game" makes a NEW profile name, and "retire" archives rather than deletes. Keep the
  existing `.ai_player_profile` marker rule ... Resume after a crash comes from the `.sav`/state, via the supervisor already
  listed as round-2 R15." [DOC R3D:66-71]; folded as BL:378-379.
- Today's state against them: no `schema_version` anywhere in AP, ai-agent or tools code (grep finds one unrelated story-dev
  file) [VERIFIED-code: grep]; the world snapshot has no version field and old snapshots load through `.get()` defaults
  [VERIFIED-code AP/world/memory.py:801-817, 823-862]; `read_world` takes the LAST line, with no stamp [VERIFIED-code
  AP/world/memory.py:864-872]; the profile still needs a donor `metadata.yml` [VERIFIED-code AP/host/launcher.py:145-176].

### 3.4 L3 (a)-(b) [DOC BL:395-399; R3L:88-107, 215-218]

- BL: "**L3 (a)-(b). Every mon by PID and species, with ROLES.** (A, ⏰ DECIDE EARLY: fields in R2's memory schema from its
  first line) ... **What:** roles (lead, HM carrier, counter for boss Y, catch helper, spare) decide boxing, never level; a
  preference expires with its boss; protected roles capped. (c)-(d), the PC skill, before chapter 5."
- R3L: "(a) every mon is tracked by PID and species and carries ROLES (lead, HM carrier for X, counter for boss Y, catch helper
  per RULING 33, spare); (b) a box/party decision reads the roles, never level alone" [R3L:95-96]; risk "cap the protected
  roles" [R3L:104-105]; sequencing "Now, with chapters 3-4 ... the PID/role fields in the AI's party model (L3 part a-b)"
  [R3L:216-217]; "R2 (L3, L5 need persisted state)" [R3L:228].
- Person-fairness of PIDs: own party only [VERIFIED-code AP/eyes/observation.py:220, 275-276; DOC 06:9434].

### 3.5 The review rounds on R1 + R2

- **Round 2** placed R1 + R2 AFTER R6 and BEFORE R5 [DOC R2N:215]. **Round 4** reversed it: "**R5 vs the order.** Step 6 reads
  "R6, R1 + R2, R5", but R1 + R2 "save only on a free screen (R5)". R5 must come first." [DOC R4N:83, 202]
- **Round 4's top-15 row:** "| 15 | R5 -> R1 + R2 (+DP1, DP2, L3 a-b) | Free-screen precondition, then save/CONTINUE and a
  memory that survives a kill | DECIDE-EARLY: the first memory file fixes paths and schema | est. 300 + 200 |" [DOC R4N:44]
- **Round 4's merge cluster:** "| Free screen | R5, R6, R1's "saving only on a free screen" | R5 inside R6 as one "screen
  state" ladder | R1 and R6 both depend on R5 |" [DOC R4N:65]; overruled for R5 by 06 2026-10-29 D1 (R5 alone).
- **Round 4's contradiction 12:** L12 put "L3 a-b" in "now, with chapters 3-4" while the backlog had other placements
  [DOC R4N:97]; resolved by BL:193-194 (L3 a-b WITH R1 + R2).
- **Round 4's settings cluster:** "| AI settings as data | D2, DP5, R12, R13 | R12's registry first, D2's weight files and
  DP5's `personality`/`seed` on the same schema | else the files hold unregistered constants |" [DOC R4N:61]. ⇒ a personality
  "when to save" weight would be a knob of the same schema. [UNVERIFIED: inference]

### 3.6 What DECIDE EARLY fixes, as a checklist for the spec (each is Claude's technical call unless marked USER)

| # | decision the first memory file fixes | the record's position | status |
|---|---|---|---|
| D-1 | root and layout of user data | DP1: `AppPaths`, four classes, `AI_PLAYER_HOME`, portable `EmeraldAI/{program,data}` | proposed, not decided [DOC R3D:44-50] |
| D-2 | where `memory.jsonl` lives | DP1 lists `memory/` under user data; R2N says "through the existing `RecordFile`", which writes only `<run_dir>/<name>` | OPEN [DOC R3D:46; R2N:52; VERIFIED-code AP/runlog.py:55-58] |
| D-3 | version and migration | DP2: `schema_version`, newer refused byte-identical, older migrated after a backup | proposed [DOC R3D:52-56] |
| D-4 | file shape | one file, full lines plus deltas, both memories, a loader for both | proposed [DOC R2N:52-55] |
| D-5 | the stamp that matches a memory line to a save | BL "play time"; R2N "play-time or save counter" | OPEN [DOC BL:293; R2N:54] |
| D-6 | which fields roll back on CONTINUE | "NOT NEWER than its save" for R2; RULING 40 experience never rolls back | OPEN by field [DOC BL:293-294; 06:9430] |
| D-7 | party identity fields | every mon by PID and species, ROLES, from the first line | proposed [DOC BL:395-399] |
| D-8 | what else shares the schema | R11's `fight_ledger` ("persisted by R2"), R8's `INDEX.json`, DP5's personality/seed/`cycle` counter | proposed [DOC BL:331, 391-392; R3D:73-75] |
| D-9 | profile semantics and retention | DP4: one playthrough per profile, newest 10 `.sav`, new game = new profile, retire archives | proposed; collides with the framework's unbounded `saves/` [DOC R3D:66-71; VERIFIED-code SB/modules/libmgba.py:243-256] |
| D-10 | when a save happens | R2N's personality rule | **USER** (pending question 1) |
| D-11 | whether a reload may undo a loss | "No save-scum" | **USER** (pending question 2) |

Notes on D-5 (game facts for the spec writer):
- Play time counts frames to seconds to minutes to hours and FREEZES at 999:59:59:59 [VERIFIED-decomp PD
  src/play_time.c:36-73]; the screen shows hours and minutes [VERIFIED-decomp PD src/main_menu.c:2142-2152;
  src/start_menu.c:1385-1390].
- The game's save counter: each save writes slot `gSaveCounter % NUM_SAVE_SLOTS` (2 slots), and a load takes the slot with
  the larger counter and sets `gSaveCounter` from it [VERIFIED-decomp PD include/save.h:12; src/save.c:187, 587-604].
  It is not shown on screen. [VERIFIED-decomp: no menu prints it, by the reads above; UNVERIFIED that nothing else does]
- The game also counts saves in `GAME_STAT_SAVED_GAME`, incremented before every in-game save is written
  [VERIFIED-decomp PD src/start_menu.c:1086-1100; include/constants/game_stat.h:4].
- ⚠ A play-time stamp alone is ambiguous across branches: after "save at 1:00, play to 1:09:59, crash; CONTINUE at 1:00, save
  at 1:10", the newest line not newer than 1:10 can come from the ABANDONED branch. A branch id (or the save counter plus a
  session id) would remove that. [UNVERIFIED: inference; prove with a two-resume unit test of the loader]

### 3.7 Items that wait on R1 + R2 (so its shape serves them)

- R7 (deploy-mode get-unstuck ladder; "needs R1, R3, R6"), whose rungs include "heal and save (R1) -> quit and CONTINUE from
  its own save -> only then give up" [DOC BL:334; R2N:139-142].
- R8 + R9 (AI-made states, chapter-chain checkpoints with "R2 memory" beside each) [DOC BL:295-299; R2N:104-118].
- R11 (defeat ledger, "persisted by R2") [DOC BL:330-331; R2N:159-161]; L7 ("a loss must change something") [DOC BL:382-384].
- R15 (supervisor: "relaunch from the save and memory for the benign codes, stop and alert when the same code recurs at the
  same frame twice") [DOC R2N:198-204]. Exit codes today: 0 "the brain gave up normally" (done AND stuck), 2 crash, 3 parked,
  4 starved, 124 wall clock, 130 interrupted [VERIFIED-code AP/host/lifecycle.py:48-59].
- L3 (c)-(d) and L5 (economy) need persisted state [DOC R3L:219, 228].

---

## 4. (c) The two pending user questions

### 4.1 Status

- Asked 2026-10-28 5:27 PM, unanswered: "when the AI saves, and may it reload to undo a loss (record them as USER RULINGS in
  `06`)" [DOC 04:61]; "whether it may reload a save to undo a lost battle" [DOC 07:39032]. The exact wording and options shown
  to the user are not in the repo (grep for "5:27"). [VERIFIED-code: grep]
- Both are behaviour questions, so they are the user's under RULING 39 [DOC 06:9393]; the record's defaults are candidates
  [DOC BL:28]. This note decides neither.

### 4.2 Question 1, "when does the AI save?": what each answer would change

| possible answer | what it changes in R1 + R2 and around it |
|---|---|
| **Like a person, by personality** (R2N's proposal: "after a Center heal, after a badge, before a gym, before a long route; a careful archetype saves more") | a SAVE goal kind in the goal manager, with per-personality weights (an R12 knob, DP5's schema); R5's free screen before each save; one full memory line per save; crash loss bounded only by how rarely a personality saves; the human-likeness graders must not read a save's menu and text as loafing or a stall (PL-1 `AWAIT_MAX`, PL-12 pushing) [UNVERIFIED: how the graders classify a save today: nobody has saved yet] |
| **A safety floor by time** (at least every N minutes of play, when on a free screen) | a bounded crash loss at x1 (216,000 frames an hour) [DOC BL:292]; a clock that is the AI's own (frames, never the host clock: EN-1); jitter so it does not read as a metronome (RULING 32); memory lines at a fixed cadence |
| **Before a planned stop** ("put the game down") | `_play_end` (or the soft wall-clock exit) saves after R5's settle; serves RULING B's "turn it off for a period of time and turn it back on" [DOC 06:2242-2243]; useless for a kill or a power cut, which run no teardown [DOC 08:21145-21146; VERIFIED-code AP/host/launcher.py:351-372] |
| **Mixed** (person triggers plus a floor) | both rows above; the floor's firings REPORTED like R6's defaults, so a grader can tell a person-like save from a safety save [UNVERIFIED: design] |
| **In graded runs?** (a sub-question the record does not settle) | official acceptance starts from a New Game (RULING 37 Q4); saves inside it change frames and counters slightly; the grader would count told saves against `GAME_STAT_SAVED_GAME` by the game's second path, as L5.SHOPPED counts purchases [DOC 06:9799-9805; VERIFIED-decomp PD src/start_menu.c:1090] |

Common to every answer: the save skill must answer the overwrite question by its words, and must say NO to the game's
"WARNING! There is a different game file ... will be entirely lost" (its default is NO), which appears when a NEW GAME was
started over an existing save [VERIFIED-decomp PD src/new_game.c:149-154; src/start_menu.c:1003-1051;
data/text/save.inc:5-23]. DP4's "new game makes a NEW profile" avoids reaching it [DOC BL:378-379].

### 4.3 Question 2, "may it reload a save to undo a loss?": what each answer would change

| possible answer | what it changes |
|---|---|
| **NO, never** (the backlog default: "No save-scum"; R2N: "a resume is for crashes only") | a LESSONS entry WITH a gate (prose fails, CLAUDE.md rule 6): the purity gate bans API loads and resets [VERIFIED-code check_purity.py:536-550] but not a button soft reset or a quit to the title, so a live check is needed (for example: the title or main menu seen mid-run after a loss, or a game-side reboot reading), with a planted-reload FAULT arm and a CONTROL [UNVERIFIED: which reading discriminates]; R7's rung "quit and CONTINUE from its own save" [DOC R2N:141] and R15's relaunch "for the benign codes" [DOC R2N:201] must be narrowed to crashes, or ruled as a separate case (a reload to escape a stuck state is not "undo a loss"); a crash between a loss and the next save still restores the pre-loss game, an involuntary undo the design must accept or counter [UNVERIFIED: inference]; R11's per-fight losses: if the defeat is in R2's rolled-back memory, the AI forgets a loss it suffered before a crash, so the ledger may belong to the never-roll-back class [UNVERIFIED: design] |
| **YES** | a reload DECISION by buttons (a person's soft reset and CONTINUE; API loads stay banned); its triggers by personality; a bound on retries (PL-4) and a cap, since saving before every gym plus a reload on every loss is the save-scum loop; R11's ledger must survive the reload (a lesson), so R2's "NOT NEWER than its save" splits by field; every grader that reads the GAME's loss counters undercounts after a reload, so the harness needs its own durable record across reloads (B1: graders read the game, never the AI's report) [DOC BL:106-107]; the vision line "losing and recovering" [DOC 01:14] and RULING 40's "mistakes" [DOC 06:9431] are weakened; a reload that re-rolls a fight's dice sits close to the non-goal "no RNG manipulation" [DOC 01:130-132] |
| **NARROW YES** (for example a legendary knocked out or fled; RULINGS 33 and 40 name legendaries and a shiny hunt) | defeats stay NO; a whitelist of triggers, each with a FAULT arm; the memory split as under YES, for those cases only. (RULING 33's shiny hunt is by roaming wild areas, not by resets: "not spinning in place but running through areas that spawn pokemon like grass" [DOC 06:9154-9158].) |

How the two questions interact: Q1's "save before a gym" is harmless under NO and is the scum point under YES; Q1's save
frequency also sets how much an involuntary crash-undo can erase under NO. [UNVERIFIED: inference]

### 4.4 Prior user statements that answer IN PART (quoted; none is a ruling on the AI)

1. **Bot, 2026-07-21 ("User #1"):** "on defeat the bot must navigate the whiteout and continue from the respawn point, never
   reload a save state" [DOC 07:1083-1085]. Closest to question 2 (a NO, for the bot, about emulator states).
2. **Vision, 2026-08-11:** "healing at Centres, losing and recovering" [DOC 01:13-14]. Leans NO on question 2.
3. **RULING 40:** "makes human-like choices and mistakes" [DOC 06:9431]. Leans NO on undoing mistakes (inference).
4. **Bot, 2026-09-16:** the League whiteout loop is "BY DESIGN" [DOC 06:5358-5359]; reloading was not among the options, so it
   is NOT evidence either way (inference).
5. **RULING B, 2026-08-14:** resume "in the event that the bot gets turned off during sudden power loss OR I turn it off for a
   period of time and turn it back on" [DOC 06:2241-2243]. Speaks to question 1's WHY (survive a power cut and a planned stop),
   not its WHEN; also "through my intervention", so the user may want to choose when a resume happens.
6. **RULING 41:** "creates a profile/uses an existing profile" [DOC 06:9499]. Continuing a playthrough is wanted; when to
   save is not said.
7. **RULING 37 Q6:** "should not really stand still at any point (for now anyways)" [DOC 06:9256]. A save's menu must be
   pressed through, never idled on (PL-1).
8. **2026-09-17 offer as gameplay oracle, "checkpoints" named** [DOC 06:5640-5645]: the questions fit that channel, in plain
   English (the user's memory file says the same).

---

## 5. (d) The proof

### 5.1 What the record asks for, verbatim

- BL:290: "(A; proof: kill, CONTINUE, same PIDs and tile)".
- R2N:37-39: "Proof: live arm = play to a Center, save, KILL the process, relaunch with only the `.sav`, CONTINUE, assert the
  same party PIDs, map and tile (identity, not counts); a fault arm that kills before the save must resume EARLIER.
  UNVERIFIED: whether mGBA flushes the cartridge save to `current_save.sav` before a kill; measure that first."
- R2N:56-57: "Cost: medium (a serialiser for `_Memory`, a kill-and-resume unit test). Risk: a field missed in the serialiser.
  The test: fuzz the kill frame, resume, compare the two memories field by field."
- R3D:55-56 (DP2): "Fault arm: hand-edit a future version in, expect a refusal and a byte-identical file."
- BL:394 (DP1 + DP2): "a fault arm per rule"; R3D:49-50: the path-literal gate.
- R2N:215: "one live kill-and-resume proof".

### 5.2 The project's proof rules that apply (sources)

- **Held-out seeds and the ledger:** "a GRADED run must have been REGISTERED first, for exactly its seed range, with the sha256
  of the numbers it is graded by ... a held-out seed is played once"; "a REPLAY is allowed only on seeds already played, and
  is written and reported as a replay, never a second measurement"; "the entry is written when the run STARTS (status
  "started": a crash still spends the seeds)"; PURPOSES are development, graded, replay [VERIFIED-code
  AP/gates/ledger.py:10-36, 46, 147-193]. Overlap is checked within a family [VERIFIED-code ledger.py:127, 173]. ⇒ a
  kill-and-CONTINUE arm is two processes on ONE seed: it needs one entry covering both legs (or its own family), decided before
  registration. [UNVERIFIED: design]
- **PF-7 / PF-8:** held-out seeds; bounds pre-registered, never loosened [DOC AP/LESSONS.md:161-171].
- **FAULT + CONTROL per guard:** PF-2 "the mutant DELETES ITS CALL, not just its body"; PF-3 "A metric is a claim only once it
  FAILS its control, and the control must be able to fail"; PF-4 "A fault arm must REACH the state it tests ... with a reach
  floor"; PF-10 "A premise or after-state check must be able to FAIL" [DOC AP/LESSONS.md:127-185]; CLAUDE.md rule 6
  ("FAULT-TEST every gate ... prove it does NOT fire on mere mentions").
- **Identity:** CLAUDE.md rule 3 "Assert IDENTITY, never position or count. PIDs — never slot indices, never party counts";
  PL-10 [DOC AP/LESSONS.md:306-310].
- **The state reached:** rule 4 "derive its target from the state the run ACTUALLY reached, and must assert something the run
  does not already satisfy"; PF-5 [DOC AP/LESSONS.md:149-153].
- **A/B for causal claims:** rule 8 "a claim of the form 'without X the bug survives' is a CLAIM, and the only currency this
  project accepts for it is an arm with X removed". R2N's "kill before the save must resume EARLIER" is that arm.
- **One trajectory:** rule 8 and PF-9 ("Identical output across runs is a DETERMINISM check, never a replication"); EN-1 "A
  launcher run's cartridge clock is the HOST's: live arms differ by time of day and cannot be replayed" [DOC
  AP/LESSONS.md:173-178, 371-376]. A real process kill needs the launcher (`kill_tree`) [VERIFIED-code
  AP/host/launcher.py:351-372], so its arms read the host clock. [UNVERIFIED: whether the in-process harness can stand in]
- **Instrument the action:** rule 7 and PF-15: log the save the AI PERFORMED (the game's "saved the game." text and its
  counter), not the decision to save [DOC AP/LESSONS.md:213-217].
- **The game is the judge:** B1 "Every graded human-likeness yield must be READ FROM THE GAME by the harness, never the AI's
  own report" [DOC BL:106-107]; PF-6 [DOC AP/LESSONS.md:155-159]. ⇒ "same PIDs and tile" is read by the harness from the game
  after CONTINUE, never from `memory.jsonl`. [inference]
- **Measure first:** rule 10's shape (an OBSERVE-ONLY probe before the change) and R5's precedent: "The bug, measured first
  (ledger #43, development seeds 5301-5303, the tree before R5)" [DOC 07 2026-10-29 R5 entry].
- **The R5 build precedent:** spec, build, independent mutant sweep, adversarial review, fix round, the live A/B RE-RUN on the
  final tree on held-out seeds registered before play (OLD = a revert mutant), a PF-17 control, "PASS: 4 of 4 seeds counted
  (floor 3)", then the full regression lane after the commit [DOC 07 2026-10-29; ai-research-notes/2026-10-28-R5-BUILD-REPORT.md:3-10].
- **Process rules:** "re-run the lane (`py -3.12 ai_player/gates/run_regression.py --full --evidence`, 72-100 min, detached)
  after any change to the AI player's code ... While it runs: no commit, and no edit to any file in ... `covers` or `reads`"
  [DOC 04:52]; `regression_due.py` and every DUE revert driver before each commit under `ai_player/` [DOC 04:59-60, citing 08
  2026-10-23]; Tier 1 per item, Tier 2 at session end (CLAUDE.md DOC CONSISTENCY LAYER).
- **Official runs:** a real New Game (RULING 37 Q4). The kill-and-CONTINUE proof is a capability proof; whether a chapter's
  official acceptance may include a resume is not ruled. [DOC DD:381; UNVERIFIED: no ruling found]

### 5.3 Traps in the record that the proof must not fall into

1. **The auto-loaded state.** The emulator loads `current_state.ss1` at startup when it exists [VERIFIED-code
   SB/modules/libmgba.py:141-146]; a clean close writes it, a hard kill does not [VERIFIED-code :160, 231-241; launcher.py:351-372].
   After a kill, an OLD `current_state.ss1` (the last clean close, or a `--state` fixture copied in at launch, launcher.py:208)
   would load instead of the title. The relaunch must prove it went through the title's CONTINUE (the title and main menu SEEN
   on the relaunch, no state file present at launch), with a CONTROL arm that leaves the state file in place and shows the other
   path. [UNVERIFIED: design; DOC 08:8437 "the next run of that profile loads it"]
2. **The intro picks NEW GAME.** It chooses "NEW GAME" by its words [VERIFIED-code AP/skills/intro.py:113-115] from a main
   menu whose options are ("CONTINUE", "NEW GAME", "OPTION") when a save exists [VERIFIED-code AP/eyes/screens.py:260-265],
   and the play loop reads the title as "a New Game (nothing is saved yet)" [VERIFIED-code AP/mode.py:461]. A New Game sets
   `gDifferentSaveFile = TRUE` [VERIFIED-decomp PD src/new_game.c:154], and the first in-game save then shows the "different
   game file" WARNING with NO as default [VERIFIED-decomp PD src/start_menu.c:1035-1051; data/text/save.inc:15-23].
3. **Vacuity.** If the save tile equals the run's start tile or the kill tile, or the party did not change between the save and
   the kill, "same PIDs and tile" and "resume EARLIER" pass by construction. Compute the discriminator before running: a
   different tile AND a party change (a catch, a box) between the save and the kill. [UNVERIFIED: CLAUDE.md Tier 2 (4) and rule 4
   applied]
4. **Special continue warps.** The game sets a continue warp in some places: the Hall of Fame (`SetContinueGameWarpStatus`,
   PD src/post_battle_event_funcs.c:36) and dynamic warps in contest, frontier, record mixing, save, start menu, trade and union
   room code [VERIFIED-decomp: grep call sites, e.g. src/start_menu.c:1297, src/save.c:1003]. That the CONTINUE then lands on
   the warp, not the saved tile, is recorded for the Hall of Fame [DOC 06:5685-5691] and UNVERIFIED for the dynamic ones. A proof save on a normal
   overworld tile (the Center R2N names) avoids them. [UNVERIFIED: that a normal save resumes on the exact tile; the game angle
   should read the CONTINUE warp path]
5. **The flush.** UNVERIFIED by the record and still unmeasured. The framework opens the `.sav` read-write so mGBA will write it
   ("libmgba needs a save file to be loaded, or otherwise it will not save anything to disk") [VERIFIED-code
   SB/modules/libmgba.py:124-133] through `lib.VFileOpen(path, flags)` [VERIFIED-code SB/mgba/vfs.py:90-108], and backs it up
   on mGBA's `savedata_updated` callback [VERIFIED-code SB/mgba/core.py:95-99, 145-147; SB/modules/libmgba.py:161]. When the
   bytes reach the disk relative to a TerminateProcess is inside mgba.dll: UNVERIFIED. Two slots mean a torn write should leave
   the previous save loadable [VERIFIED-decomp PD include/save.h:12; src/save.c:187, 587-604]. What would prove it: a probe that
   saves in-game, hard-kills at a swept delay after "saved the game." (0, 1, 15, 60, 300 frames), relaunches with only the
   `.sav`, and reports which save CONTINUE shows (play time, badges) against the save's own on-screen values.
6. **Purity on both legs.** Each leg's verdict must be CLEAN; a CONTINUE pressed by the AI is not a load, while any API load
   would be counted [VERIFIED-code AP/host/attribution.py:25-26]. [inference]
7. **One profile, one process.** The relaunch must not start while the killed tree still holds the profile [DOC 06:617;
   VERIFIED-code launcher.py:371-372 returns the pids still alive]. [UNVERIFIED: design]
8. **Two memories in the field-by-field test.** The world memory is carried today by `AI_PLAYER_WORLD` from a run's last
   snapshot [VERIFIED-code AP/mode.py:940-945; AP/world/memory.py:864-872]; `_Memory` is not [VERIFIED-code AP/brain/goals.py:447-450].
   The R2 test must compare BOTH and must include a kill between a save and the next map change (when no new world line exists).
   [UNVERIFIED: design]

### 5.4 What would prove the open claims of this note

| claim | tag | what would prove or refute it |
|---|---|---|
| mGBA's save bytes reach disk before a hard kill | UNVERIFIED | the swept-delay kill probe in 5.3 item 5 |
| the instrument does not count a game-performed soft reset | UNVERIFIED | read where `SoftReset` runs (BIOS SWI) against `attribution.py`'s wrapped doors; a planted button reset in a dev arm, then read `purity.json` |
| a normal overworld save resumes on the exact tile | UNVERIFIED | the decomp's CONTINUE path (`CB2_ContinueSavedGame`) plus one dev arm |
| play-time stamps are ambiguous across two resumes | UNVERIFIED | a unit test: two branches with interleaved play times, the loader picks the abandoned one |
| R7 and R15 conflict with "a resume is for crashes only" | DOC + inference | the user's answer to question 2, scoped to "a reload to get unstuck" |
| an autostart for the AI needs a new approval | inference from DOC 06:9526 | ask the user if R15 is ever built as a scheduled task |

---

## 6. Not checked, and limits

- The exact text and options the user was shown at 5:27 PM 2026-10-28 (not in the repo).
- `ai-research-notes/concept-notes-c10.md` was skimmed only for its options list; its provenance (Gemini or Claude) was not
  checked, so it is cited as an option list, never as a fact.
- The game's CONTINUE path, the eyes on the title and main menu, and the mGBA write path were not read beyond the lines cited:
  they belong to the game and code angles.
- `08` was searched for save and state entries by keyword; an entry phrased differently could be missed.
- The whole of `06` was not read: it was grepped (rule 11) and the lookup tool was run; RULINGS 32-50 were read in full.
