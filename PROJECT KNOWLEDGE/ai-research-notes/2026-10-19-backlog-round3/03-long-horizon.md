# Backlog round 3, angle 3: LONG-HORIZON risks for the AI player (chapters 5-8, Victory Road, Elite Four, Champion) (2026-10-19)

A NOTE, not truth. Candidates, not decisions. Written read-only from grep and targeted line ranges; nothing was run.
IDs are `L1`..`L12` (round 3, angle 3). Items marked UNVERIFIED have a one-line cheap check named.

Sources read: `05-KNOWN-ISSUES.md` (KI-58/63/72/74/84/88/89/99/102-107/116/118), `08-MISTAKES.md` (entries dated
2026-07-23, 07-26, 07-30, 08-03, 08-05, 09-04, 09-07, 09-26), `06-DECISIONS-LOG.md` (RULINGS 14, 15, 33, 33-addendum),
`20-POST-FORTREE-RECON.md`, `21-TEAM-POLICY-DESIGN.md` section 6, `ai-research-notes/2026-10-03-decision-points-MAP.md`,
the learner's `findings/LATEST.md` and `DEVELOPER-NOTES.md` (read in the clone, not edited), `ai_player/README.md`
(knowledge section, step-4 limits), and round 2 `03-ai-player.md` (R10-R12). KI-122 has no `05` entry: it lives in
`03-PUNCH-LIST.md`, the decision-points MAP and the learner's notes ("diagnosed only").

## The one finding behind most of these

Where the bot's 1,852 scored runs ended (learner `LATEST.md`, 2026-10-19):

| ended at | runs | share |
|---|---|---|
| a boss wall mid-game (Tate & Liza 303, Norman 194, Juan 186, Winona 75, other 61) | 819 | 44 % |
| the Elite Four DOOR refused (basket short 288, team below the level floor 163) | 451 | 24 % |
| the Champion | 286 | 15 % |
| Victory Road failed | 109 | 6 % |
| navigation (unreachable 100, watchdog 33, heal walk 16) | 149 | 8 % |

Navigation and puzzles, which cost the bot most of its engineering time (Mossdeep, Sootopolis, Seafloor, Magma Hideout),
end 8 % of runs. **Planning ends 68 %**: how strong the team is when it meets a boss, whether it has the money and items
for the League, and whether the right mon is in the party. The AI player will meet the same walls, and a person's answer
is the same too: a plan for the whole game made early, adjusted by what happens. Today the AI's goal manager knows 20
milestones, all in chapters 1-4, and `knowledge/` deliberately omits learnsets, encounters and trainer parties ("a person
meets those by playing", README step 4). USER RULING 40 (a SEASONED player) reversed that stance for static knowledge, so the
data below is allowed and is the cheapest large win.

Two more measured facts shape the list:

- **Tate & Liza**: the bot arrives at team level 33.1 (first loss) against trainers at 41-42, loses 11.8 times per run, and
  wins at 34.1. It wins by fighting through losses, not by preparing. Each loss is a whiteout (money halved, respawn).
  A human reference of 37-43 exists but is a Gemini estimate, UNVERIFIED (`2026-10-03-human-reference-NOTE.md`).
- **The Elite Four is won at team level ~64 (floor 65, RULING 15), and still Wallace is beaten by only 286 of 531
  (54 %)** at an average team level of 64.3-65.0, while Sidney, Phoebe and Glacia are ~100 % and Drake 94 %. Levels did not
  fix the last fight, so the cause is coverage, moves or item use, not level. (Inference from the table; the cause was
  NOT read. Cheap check: grep Wallace losses in 20 stored logs for the lead, its moves and the turn it fell.) The bot's
  L65 floor is a safety ceiling bought with a long grind; the AI should learn its own lower figure, not copy it.

## Which bot lessons are DATA, which are SKILL, which are bot-like (the sorting rule)

- **Knowledge (data, allowed by RULING 40, generated and decomp-verified like `extract_knowledge.py`/`verify_knowledge.py`
  already do):** facts about the game that a seasoned player carries. Boss parties, HM and badge gates, learnsets, shop
  stock and prices, encounter tables WITH their story-stage gate, prize-money and whiteout rules, puzzle TYPES.
- **Skills (code, general, each with a game-read proof):** things the AI's hands do from the screen: PC deposit/withdraw by
  identity, teach an HM, buy N and verify the bag, mount Surf, solve a statue or ice puzzle from what it sees, recover after
  a whiteout.
- **Bot-like behaviour to AVOID (RULING 35):** per-chapter legs with coordinates (the Victory Road leg 11 shape), a
  precomputed ice path replayed blind, `calculate_path` across a whole region, state-writes as a "faithful fallback", the
  bot's once-per-boss counter ladder and `HUNT_SPIN_BUDGET_FRAMES = 120,000` spin hunts, whiteout used as a free
  heal-and-teleport (KI-29's canary expects losses and whiteouts to stay 1:1, i.e. a loss is expected to end in a whiteout), hard "REFUSING to enter" stops as the
  ONLY readiness logic, and reading hidden vars such as `ICE_STEP_COUNT` (a person counts cracked tiles by looking). A
  bot HELPER the AI cannot use also carries the bot's bugs: `train_team(slots={i})` (KI-84), `scroll_to_item_in_bag`
  (KI-89), `teach_hm_or_tm` (KI-88) are all upstream helpers the bot ROUTED AROUND. The AI's own skills must not inherit them.

## The items

### A. Design early (data and interfaces, small code; chapters 3-4)

**L1. A CAMPAIGN MANIFEST: what the whole game will demand, by milestone (data).** Priority A. Cost: small-medium.
- **Evidence:** Tate & Liza needs 2 usable mons or no battle starts (`NeedTwoMons`, `20-POST-FORTREE-RECON.md`); the Space Center
  multi battle cuts the party to 3 and opens a party select (same file, 4.6); Sootopolis is an island entered by Dive;
  Waterfall (HM07) is given before the gym but unusable until Badge 8; Surf = Badge 5, Dive = Badge 7 (recon gating chain).
  The 2026-08-05 mistake (party filled 4 to 6 before gym 1 cut the finish rate 52.0 % to 15.8 %, ten non-finishes
  "No party mon can learn Surf and the party is full") is a failure to look ahead.
- **What:** `knowledge/campaign.json`: for each milestone through the Champion, the needs: HM and badge for field use, the
  items, the party size (2 for a double, 3 for the multi battle), the types the next bosses demand, a money checkpoint, and
  the level band. Generated from the bot's data and the decomp, with a verifier that plants wrong facts, the way
  `extract_milestones.py --verify --plant` does. The goal manager reads it to LOOK AHEAD ("what will the next three
  milestones need that I do not have?"), which is what a seasoned player does.
- **Benefit:** the HM carrier, the coverage mon, the money and the second mon are acquired on the way, not discovered at the
  wall. **Risk:** a manifest that becomes the bot's chapter script. Rule: it lists NEEDS and gates, never routes or coordinates.

**L2. A BOSS BOOK: `bosses.json` (data).** Priority A. Cost: small (the design draft already names it).
- **Evidence:** the README step-4 limits: "any knowledge of a leader's party (the design's `bosses.json`, from pret's trainer
  parties)" is not built. The learner table gives per-boss first-loss versus win levels for all 13 fights.
- **What:** per gym leader, the Elite Four, the Champion, the rivals and Magma/Aqua leaders: party, levels, types, moves, held
  items, single or double, and notes that change play (Juan's Kingdra Rest/Double Team stalls; Wallace's team is
  Water-themed; the E4 themes are Dark, Ghost, Ice, Dragon, Water). A separate field `measured` carries the bot-corpus priors
  (first-loss level, win level, losses per run), clearly labelled as bot data.
- **Benefit:** feeds L4, L5, L7 and the type-coverage plan; verified against pret's `trainer_parties.h` through `gh api`.
- **Note:** this is also the cheapest way to get the 13 per-boss numbers into the AI's hands with no emulator run.

**L3. PARTY AND PC BY IDENTITY, WITH ROLES (code + data).** Priority A. Cost: medium. Needs R2 (persisted memory).
- **Evidence:** the same position-versus-identity bug appeared at least six times in shared helpers (KI-18, KI-34, KI-66, KI-84,
  KI-96, KI-101, KI-100) and the rule "assert identity, never position" was written in response. Two PC failures are the
  late-game pattern: the PC rotation deposited the counter the chain had just crossed Hoenn to fetch because a freshly caught
  counter is ~25 levels behind the best BY CONSTRUCTION (08 2026-08-03); the HM mule was picked by level and not by
  compatibility (08 2026-07-23). The recon says a boxed Dive carrier strands the run on the Sootopolis island (4.10), and
  `21-TEAM-POLICY-DESIGN.md` section 6 lists HM carriers as "never randomise".
- **What:** (a) every mon is tracked by PID and species and carries ROLES (lead, HM carrier for X, counter for boss Y, catch
  helper per RULING 33, spare); (b) a box/party decision reads the roles, never level alone; (c) a PREFERENCE (a counter that
  leads) is scoped to the boss it was made for and expires when that boss falls. KI-122 is exactly an unscoped preference:
  `_hunted_counter_pids` persists the whole run, so a Norman counter still leads into Tate & Liza; (d) the PC is the default
  destination for a surplus catch. The learner's notes count 14-20 skipped catches per run for "party is #/#, a catch would
  consume the HM/counter runway" and 19 for "below the dex reserve", with the Pokedex at 17-23 owned against a human
  estimate of 65-95 (UNVERIFIED reference). A reliable PC skill removes the runway workaround, and the 2026-08-05 failure
  becomes "deposit the weakest SPARE, withdraw the Surf learner".
- **Benefit:** removes three wall causes (KI-118, KI-122, the stranded carrier) by construction, and lifts the Pokedex goal
  of the user's personalities. **Risk:** a role system that over-protects and fills the party with undepositable mons: cap the
  protected roles (HM carriers share a mon where the learnsets allow; a Water mon can carry Surf, Dive and Waterfall).
- **Variety (RULING 33 addendum):** random choice only AMONG options that pass the coverage test (L4). The bot never audited
  whether `team_policy.lead_rank_key` breaks ties at random ("UNAUDITED"); the AI should do it from the start.

**L4. A READINESS ESTIMATOR in place of hard thresholds (pure function + data priors).** Priority A. Cost: medium.
- **Evidence:** the three League refusals are thresholds: level floor 65 for 4 of 6 (RULING 15), `LEAGUE_MIN_MONEY` 54,300,
  `CREDIBLE_ANSWER_POWER = 75` (raised from 60 after a Combusken+Rock Smash false negative). Each was a claim about a MOMENT
  and was wrong once: the money check read the pre-Victory-Road wallet (38,893) against a basket that is bought after payouts
  (08 2026-09-26 item 2). KI-118's box-first accepted a Fighting mon on TYPE alone; the credible-move repair would break
  Wattson's counters because Magnitude and Low Kick are stored with base power 1 (variable-power moves: the DATA is wrong, not
  the rule). The counter-candidate ranker preferred Victory Road Hariyama because "cost" fell as wilds got stronger (08
  2026-07-30).
- **What:** `readiness(party, boss, bag) -> expected margin and the reason`: the best effective-power move per party mon
  against each boss mon (power x type x STAB, with variable-power moves given real values), level margin against the boss ace,
  lead HP, healing items per expected fight length, and the number of usable mons (2 for a double). The margin that counts as
  "ready" is LEARNED: the prior comes from the bot's corpus (L10), and the AI's own fight ledger (R11) moves it. A hard floor
  remains only as a SAFETY gate in graded runs.
- **Benefit:** one function serves every boss, including Tate & Liza (trains toward a margin, not +1 level per loss), the
  League door, and L3's "does this mon answer boss X". **Risk:** a learned margin that rewards loafing (R13): the margin
  is graded by the game's own level and badge counters, and held-out seeds judge it.

**L5. AN ECONOMY LEDGER (data + small code).** Priority A. Cost: small.
- **Evidence:** "E4 refused: League basket short" ends 288 runs (16 %). The basket is Hyper Potion x30, Full Restore x3, Full Heal
  x8, Revive x3 = 54,300; the pre-Victory-Road wallet measured ~38,893; the floor is 1,000 and rises to ~109,600 in the
  basket era (decision-points MAP section 7). A whiteout HALVES money (the MAP cites decomp `src/overworld.c:358`, not
  re-verified here), and Tate & Liza averages 11.8 losses, so the wall that comes first may be draining the money that the
  League needs. **UNVERIFIED hypothesis; cheap check:** among stored runs that ended "basket short", compare the whiteout
  count at Tate & Liza against runs that passed the League door.
- **What:** a persisted ledger of balance, expected income (trainer payouts by level and class, sellable items) and the next
  BUDGETED spends from L1's manifest (balls for the dex, heals for the next boss, the TMs worth buying, the League kit). A
  budget check is made WHERE THE MONEY IS SPENT, never earlier. Selling uses an ALLOW-list (the bot sells Nuggets only; never
  a deny-list). The Amulet Coin holder and the Game Corner (RULING 33, "future note") are later knobs.
- **Benefit:** the AI is never surprised at the door; it also lets a PERSONALITY choose to spend on balls. **Risk:** low.

### B. Skills (code), built when their chapter comes, designed now

**L6. THE HM PLAN as a dependency graph plus one teach skill.** Priority A. Cost: medium.
- **Evidence:** `20-POST-FORTREE-RECON.md` 4.9: "no section anywhere on teaching one to a party member, or on HM-slave party
  planning"; later KI-88 (replaces the wrong move), KI-89 (the game SORTS the TM/HM pocket when the bag opens; the bot's
  helper counted the stored order), KI-104 (the slot rule deleted a mon's ONLY attack of a type), KI-105 (the wrong HM
  taught), KI-99 (the HM06 gift may have no bag-full guard and the success signal would lie, UNVERIFIED).
- **What:** (a) the graph in L1 (HM, who gives it, badge to use, first map that needs it, learner candidates from the
  learnsets, party or PC); (b) one teach skill that READS the cursor's item name and the move list before every confirm and
  READS the result after (move list contains the HM). This is the screen-reading form of the identity rule, and it makes the
  KI-88/89/104/105 class impossible without a special case; (c) invariants: an HM carrier is not boxed while a pending gate
  needs it; never overwrite the only attack of a type; keep one party slot reachable for a learner; the Move Deleter is where
  an HM move is forgotten (location from the data, not memory).
- **Benefit:** four closed KIs never recur in the AI. **Risk:** low once the skill is read-before-confirm.

**L7. LOSS AND WHITEOUT POLICY: every loss must CHANGE something (skill + policy).** Priority B. Cost: medium. Extends R11.
- **Evidence:** boss mode after 2 losses tops up only +1 level because "the boss battle is the trainer" (decision-points
  MAP, `story_mode.py:3865`), and the learner shows 11.8 losses per run at Tate & Liza with the team at 33-34. The whiteout
  loop was quantified in 2026-08 (`#24-whiteoutloop`); a Draw is a whiteout but is counted only on `Lost` (KI-116); a held
  Up leaked across a whiteout and walked the Ever Grande respawn into the Poke Center (KI-106); a stale whiteout flag made a
  run idle 6.27M frames (KI-107); a swap-training grind left the WEAKEST mon leading and cost one lane 44 whiteouts (08
  2026-07-26); a test passed because the whiteout was healing the run (08 2026-08-11).
- **What:** (a) a whiteout RECOVERY skill: read where the player woke (the respawn map), release all input, read money and
  party, re-plan; (b) the ledger rule: after a loss the NEXT attempt must differ in at least one of lead, moves, level
  margin, items, or the answer-type mon; the same attempt twice is forbidden; (c) before EVERY trainer or boss, a lead check by
  identity ("my best answer leads"), because any rotation or training leaves the weakest in front; (d) an explicit "I need two
  usable mons" precheck for doubles. (e) The cost of a loss is stated in the ledger: halved money, lost position.
- **Bot-like to avoid:** treating a whiteout as the heal. For the AI, a whiteout is a MISTAKE that costs money.

**L8. PUZZLE SKILLS as general solvers over the VISIBLE state, with knowledge of the puzzle TYPE only.** Priority B (build when the
chapter comes; design the interface now). Cost: large per puzzle family, one-time.
- **Evidence:** every late gym and hideout is a graph search (recon): Mossdeep (six teleport-pad pairs, a trap at (21,6), eight
  colour switches rotating statues in 2x2 cycles of period 4, BFS over player tile x phase, up to 1024 states; statue state
  persists in the save, so a re-entered gym is not the map layout); Sootopolis (cracked ice, 64 tiles stepped once, in ONE
  unbroken visit because a fall resets everything, recon 4.1; the first claim of an "unsolvable" state was corrected); Magma
  Hideout and Seafloor (boulders reset on re-entry, 4.4); the Fortree gym (named in the user's brief; not read here, UNVERIFIED). The bot built each as a chapter leg.
- **What:** (a) a solver family that reads the live tiles and objects from the screen and the memory the eyes already expose
  (state is partly hidden from view, e.g. an unseen pad pair, so the solver must EXPLORE a pad before planning through it,
  as a person does); (b) knowledge supplies "this is a statue room, switches advance one colour" so the AI knows what to
  look for, never the solution; (c) every solver's proof is a game-read result (the gym badge flag) on a bot-made fixture with
  a CONTROL tile, as the project's own rule says (reachability proof from a real position plus a tile that should not path).
- **Bot-like to avoid:** replaying a precomputed path (the ice path "can be precomputed and replayed" is the bot's idea).

**L9. HM-GATED EDGES in the region-aware world graph (extends R10).** Priority B. Cost: medium (inside R10's cost).
- **Evidence:** the bot's reachability layer could not see Dive (4.8), could not see the two tile types you cannot surface
  from and routed a dive to a dead end (KI-72), could not see `setmetatile` changes and was wrong at the Elite Four door
  (KI-74, "ROM says BLOCKED, the live grid says OPEN"), and treated a permanently moved NPC's ROM tile as a wall (KI-103,
  Sootopolis's only bridge west). The AI reads the LIVE map, which avoids the template-versus-live class, but the missing
  piece is the same: an EDGE needs a precondition (Surf, Dive, Waterfall, Strength boulder, a one-way ledge, a story flag).
- **What:** R10's graph nodes carry edges annotated with the ability they need (from L1's gates) and with what the AI
  actually observed crossing them, so "I cannot cross this yet, I need X" is a normal planner answer and feeds L1/L6.
- **Rule:** knowledge says what a gate needs; the screen says whether it is open now. When they differ, the screen wins and
  the difference is logged (a candidate fact, not a fix).

### C. Proof and process

**L10. MINE THE BOT'S FINISHED GAMES AS PRIORS AND AS AN OFFLINE TEST BED (no emulator).** Priority A. Cost: medium. This is
`#28-trainer-improvements` item 7 aimed at the long horizon.
- **Evidence:** the learner holds ~1,850 scored runs with per-boss team levels at first loss and win, and the walls above.
  A game-read proof of a planner would otherwise need an emulator run per boss.
- **What:** (a) extract per run: party (species, level, moves), money, items at each boss, outcome and losses; (b) fit the L4
  margin priors and the L5 income curve; (c) TEST L4 offline as a HELD-OUT check: fit on cycles A, ask on cycles B whether
  `readiness` would have flagged the Tate & Liza and League-door failures BEFORE they happened, and with what false-alarm
  rate (a planner that flags everything is useless); include a control (boss fights the bot won). Same-seed replays are one
  trajectory, not two measurements.
- **Benefit:** the long-horizon planner gets a measured start with zero live play. **Risk:** the corpus is the BOT's, so it
  encodes bot habits (grinding to 65, spin-hunts): use it as a PRIOR on what a team needs, not as a style. Label it so.

**L11. USE BOT-MADE FIXTURES FOR SKILL PROOFS ONLY, AND CHAIN THE AI'S OWN SAVES FOR THE WHOLE-GAME CLAIM.** Priority B. Cost: small.
- **Evidence:** steps 2-5 already prove skills from bot-made states (`rival_r103.ss1`); R9 proposes chain checkpoints made only by
  the AI's own presses. Late-game fixtures (Tate & Liza, the League door, the Mossdeep gym) exist only as bot saves, and some
  are not pinned (`prenorman_fodder_grind.ss1` is not in `saves/FIXTURES.md5`).
- **What:** a one-line rule in the AI's README: a late-game skill may be proven on a pinned bot fixture (with a control arm and
  the fixture's hash), but "the AI beat Tate & Liza" counts only from the AI's own chain (R9). Pin each late-game fixture the
  skills use.

**L12. SEQUENCING: what to build when (so the late game is not a rebuild).**
- **Now, with chapters 3-4 (cheap, mostly data):** L1, L2 (generated and verified), L10 (extraction), the PID/role fields in
  the AI's party model (L3 part a-b), and the ledger skeleton (R11) with L7 (b)/(c). These are data and interfaces; they change no
  game code.
- **Before chapter 5 (Fortree/Lilycove era):** L3 (c)/(d) with the PC skill, L5, L6 (the teach skill is needed by the first
  Rock Smash/Cut/Surf), L4 as a function (offline proof first).
- **With their chapters:** L8 (one solver family at a time: boulders, then pads, then statues, then ice), L9, the Space Center
  multi battle handler, the League door logic.
- **Do NOT build early:** a Victory Road leg, the League basket purchase script, any ice-path or statue-path table.

## Cross-links and conflicts

- Extends round 2: R10 (L9), R11 (L7), R12 (every L4/L5 constant becomes a knob entry with its trade written down), R13 (L4's
  margin is judged by held-out seeds, never the AI's own grader), R2 (L3, L5 need persisted state).
- Folds into `#28-trainer-improvements`: item 7 (experience records) = L10.
- Backlog ordering: L1/L2/L10 can ride with the backlog's step 6 ("Step 5.3, then chapters 3-4, on D1-D3") since they are data;
  L3-L6 are the "general skills over chapter patches" (D1) for chapters 5-8 and should be named there.
- Do not reopen: KI-118 and KI-122 remain the user's/bot-side decisions (KI-118's fix choice is the user's, `05` says so); this
  note only says the AI should not inherit either shape.

## Unverified or open (so nobody builds on them)

1. Whiteout losses at Tate & Liza drain the League money (L5): hypothesis, check named.
2. Wallace's 54 % cause (L4): not read.
3. Juan's 10 % wall cause: no KI found; the "stall" description is from the recon (Rest/Double Team), not from a loss log.
4. The human reference levels and species counts are a Gemini estimate (`2026-10-03-human-reference-NOTE.md`).
5. The whiteout-halves-money rule and the `LEAGUE_MIN_MONEY` composition are quoted from the decision-points MAP; neither was
   re-checked against pret in this pass.
6. The "pre-Victory-Road wallet 38,893" is the 2026-09-26 measurement; money has moved with later changes (08 2026-09-04
   "quoting a money figure that four weeks of gameplay had moved"): re-measure before using it as a prior.
