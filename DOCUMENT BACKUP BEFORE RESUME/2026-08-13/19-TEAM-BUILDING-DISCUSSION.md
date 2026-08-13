# Team building & training scope — UNDER DISCUSSION (user, 2026-07-26)

> ‼ **NOTHING HERE IS AGREED SCOPE YET.** This is a faithful record of what the user asked
> for, what it interacts with, and the questions that must be answered before any of it is
> built. Nothing may be implemented from this file until the open questions below are
> resolved with the user. When an item is agreed, promote it to `03-PUNCH-LIST.md`.

Three related requests, all aimed at the same underlying goal: **runs that are stronger and
more varied**, so a batch explores more of the game instead of replaying one narrow line.

---

## 1. Train against TRAINERS before grinding wild (all gyms, not just Dewford)

**What the user said.** At Dewford the bot works "flawlessly" but trains in the cave, when
it should be training on "the second floor", and should first battle **all the trainers on
the island and in the gym** for experience and money. This should apply to **every gym that
has other trainers**.

**Why this is well-aimed, from our own data** (batch `20260726-181825`): the dominant
failure is not gym leaders, it is attrition — P2 whited out **41 times on Route 110** and
derailed; P4 whited out 20 times. The two healthiest lanes died at **Mauville Gym**. Under-
levelling is the most plausible common cause, and gym/route trainers are a large block of
XP and money the bot is currently walking past. Trainer battles also cannot be fled from,
so they are "safe" XP in a way wild encounters are not.

**Open questions — MUST be answered before building:**
- **Q1.1 — WHICH "second floor"?** Ambiguous. Granite Cave has 1F / B1F / B2F (plus
  Steven's room); Dewford Gym is a single dark floor with switch puzzles. "Training on the
  second floor" most likely means a specific Granite Cave sub-floor, but this must not be
  guessed — a wrong floor sends the bot somewhere with the wrong encounter table and level
  band. **Ask the user, then verify the floor's encounter table against `modules/data`.**
- **Q1.2 — Always, or only when under-levelled?** Trainer battles are a ONE-SHOT resource
  per playthrough (no rebattles without Match Call rematches). Spending them always is
  simplest and probably right, but it removes a reserve the bot could have used later when
  it is behind. Which does the user want?
- **Q1.3 — Before or after the wild-training step?** "First" suggests trainers → then top
  up on wild if still short. Confirm.
- **Q1.4 — Scope of "all the trainers on the island".** Dewford has trainers outside the
  gym (on the beach / in the hall). Does this mean every trainer in the TOWN, or every
  trainer on the ROUTE(S) associated with that gym's arc? For later gyms this could mean a
  lot of walking.

**Verification owed before implementation** (project rule — game facts come from the
decomp, never from memory): the actual trainer rosters and their positions per gym town,
and which are already defeated by the bot's existing route. Same for the Granite Cave floor
question.

**Known interaction:** more trainer battles = more chances to whiteout mid-arc. The
whiteout-recovery path (`#24-whiteout`) is already the weakest link; this item should be
built with that in mind, not on top of it.

---

## 2. Fill the party, and make catching VARIED

**What the user said.** The bot only ever catches 6 Pokémon; runs come out with similar
party layouts. It should catch more, and **swap Pokémon in and out of the PC** so it can
train what it needs (typing, moves) — the goal being more variable and diverse parties
across runs.

**Confirmed by the logs.** P1's party across its single run was
`NINCADA → NINJASK + SHEDINJA, COMBUSKEN, DUSTOX, CASCOON L5`. **CASCOON stayed at level 5
for the entire run** — a permanently dead party slot the bot never reconsidered. That is the
"similar layouts" problem in one line: the party is whatever was caught first, forever.

**Open questions:**
- **Q2.1 — Diversity for TESTING, or diversity for COMPETENCE?** These pull in opposite
  directions. A deliberately varied team explores more of the game's content (good for
  finding bugs); a deliberately optimal team wins more (good for reaching the frontier).
  The user said "more variable and diverse", which reads as the former — confirm, because
  it decides whether the picker optimises or randomises.
- **Q2.2 — Does PC access exist?** Swapping via the PC is a substantial new capability
  (walk to a Poké Center, open the PC UI, navigate boxes, deposit/withdraw). Needs a survey
  of what already exists before it can be estimated. This is likely the largest single
  piece of work in this document.
- **Q2.3 — What triggers a swap?** "If the bot needs them (typing/moves)" implies the bot
  evaluates an upcoming fight and fetches a counter. That is close to `#24-counters`
  phase 2, which is already on the punch list — these should probably be ONE item, not two.
- **Q2.4 — A dead slot like CASCOON L5: evolve it, train it, box it, or release it?**
  Cheapest immediate win may simply be "never keep a party member that is more than N
  levels below the lead", independent of everything else here.

---

## 3. A rolled "FAVOURITE" Pokémon per run

**What the user said.** Roll a favourite species per run; if the bot sees one in the wild or
already has one, prefer to keep it in the party — "unless it's deemed a disadvantage to the
team for the fight they are about to enter".

**Why this is a good idea.** It is a cheap, single-knob source of run-to-run variance that
is independent of the RNG decorrelation already in place. Two lanes on the same starter with
different favourites will build different teams and hit different content. It is also easy
to log and therefore easy to correlate with outcomes.

**Open questions:**
- **Q3.1 — Rolled from what pool?** Any species in the game (mostly unobtainable early),
  everything catchable in Hoenn, or only what is catchable at the bot's current point?
- **Q3.2 — How strong is the preference?** Always catch on sight, always keep in party, or
  a weighting that other logic can override?
- **Q3.3 — What does "a disadvantage for the fight about to be entered" mean concretely?**
  A type check against the upcoming leader? A level floor? This needs a definite rule, or
  it becomes an unfalsifiable judgement call in code.
- **Q3.4 — One favourite per run, or per lane?** Per RUN gives more variety per batch; per
  lane makes a lane's behaviour easier to reason about across runs. (Recommend per run, for
  the same reason the RNG decorrelation is per run.)

---

---

## 4. ‼ ANSWERS FROM THE USER (2026-07-26) — the four blockers are resolved

- **Q1.1 — which floor:** **Granite Cave B1F and B2F** (both).
- **Q2.1 — testing vs competence:** **BOTH**, via a bot "personality" that can swing one way
  or the other, ideally drifting DURING gameplay so it looks organic rather than robotic.
- **Q1.2 — trainers:** **always** fight them.
- **Q3.3 — "disadvantage":** a **type check**.

---

## 5. Design thinking: the PERSONALITY mechanic

This is the subtlest request in the document and the easiest to build badly, so the thinking
is recorded before any code exists.

### 5.1 One axis or two?

**Recommendation: TWO axes, not one.**

A single "exploration ↔ optimisation" slider conflates two things that are genuinely
independent in a human player:

| axis | low | high | governs |
|------|-----|------|---------|
| **curiosity** | keep the proven team, catch only what is useful | catch novel species, try new team members, honour the favourite | WHAT the bot collects and fields |
| **caution** | push on at low HP, skip healing, accept risky fights | heal early, train to a bigger level margin, avoid marginal fights | HOW MUCH RISK it takes |

With ONE axis, "make the team more varied" is forced to also mean "play more dangerously",
which is not what was asked for and would simply make runs fail more without buying better
coverage. Two axes allow the most valuable configuration for our purposes:
**curious but careful** — a run that fields odd teams AND survives long enough to reach deep
content. A single slider cannot express that.

Cost: two knobs to tune instead of one. Worth it.

### 5.2 How the drift should work — event-driven, not a random walk

A random walk would look organic and mean nothing. **Event-driven drift is both organic and
useful**, because it mirrors how a person actually plays:

- whiteout, or a loss to a boss → **caution rises**
- a clean stretch (N battles, no faints) → **caution falls** (confidence)
- a new species caught / a badge earned → **curiosity rises** briefly
- repeated failure at the same objective → **curiosity falls** (focus up, stop experimenting)

This also gives the bot a crude but real self-correction: the run that is dying repeatedly
stops experimenting and starts playing safe.

### 5.3 ‼ The trap: "cautious" must NOT simply mean "train more"

Our own data says training is where runs die. In batch `20260726-181825` **P2 whited out 41
times on Route 110** — travel and training attrition, not boss fights. A naive feedback loop
of "died → be cautious → train more → train in the same place → die again" would make the
dominant failure WORSE, and would look like the personality system working.

So "caution" must be defined as a set of concrete behaviours that genuinely reduce risk:
heal sooner and more often, prefer a safer training location, accept a smaller level target
rather than grinding in a dangerous spot, flee marginal fights. **Never as "grind longer".**
Any implementation must be checked against this specific failure before it is believed.

### 5.4 What the personality must feed (one value, many decisions)

The point of a personality is that ONE state drives MANY decisions coherently — otherwise it
is just several unrelated random knobs wearing a costume:

- **catch decision** — curiosity gates "is this worth a ball?"
- **party composition** — curiosity gates keeping a novel/favourite mon over a stronger one;
  caution gates benching anything badly under-levelled (the CASCOON L5 problem)
- **level target before a gym** — caution sets the margin
- **healing threshold** — caution sets the HP fraction that triggers a Center trip
- **flee/fight on a marginal wild encounter** — caution
- **optional detours** (extra trainers, side areas) — curiosity

### 5.5 Testability requirements (non-negotiable, given this session's history)

Twice today a feature shipped believing something it had never checked. A drifting
personality is exactly the kind of system that hides that, so:

1. The personality state must be a **pure, deterministic function of (seed, event log)** —
   no emulator reads — so it can be unit-tested by feeding it synthetic events.
2. Every decision it feeds must be a **pure function of (personality, candidates)**, testable
   without an emulator.
3. Every drift must be **logged with its cause** (`caution 0.35 -> 0.55 (whiteout #3)`), or
   nobody will ever be able to explain a run's behaviour afterwards.
4. The rolled starting values must be **published in the lane status blob and written into
   the run's log header**, so personality can be CORRELATED WITH OUTCOME across a batch.
   Without that, this is decoration; with it, it is an experiment.

### 5.6 What "type check" means for the favourite (Q3.3, answered)

The favourite is kept in the party UNLESS a type check says it is a liability for the fight
about to be entered. Concretely, the rule needs: the upcoming opponent's types (known for
gym leaders from the decomp-verified table in `modules/badge_case.py`), the favourite's
types, and a threshold — e.g. bench it if the opponent's STAB is super-effective against it
AND it has no super-effective answer. That is checkable offline and therefore testable.
Open sub-question: does this apply only to GYM LEADERS (where we know the roster) or to any
trainer battle (where we would need the party at runtime)?

---

---

## 6. ‼ WHAT ACTUALLY EXISTS (codebase recon, 2026-07-26) — this rewrites the estimates

Three findings overturn assumptions made earlier in this document.

### 6.1 The bot catches **FOUR**, not six — and stops entirely after Badge 1

`StoryMode._should_catch` (`plugins/custom_modes/story_mode.py:899-937`) requires ALL of:

- `not get_event_flag("BADGE01_GET")` — **catching stops dead once the Stone Badge is won**
- `len(party) < self._catch_team_target`, and `_catch_team_target = 4` (`:811`)
- species not already in `pokedex.owned_species` and not already in the party
- `poke_balls > 1`

So the team is assembled in the first ~20 minutes and is **frozen for the remaining hours of
the run**. That is the whole of the "runs have similar party layouts" complaint, and it is
not a subtle emergent problem — it is two explicit conditions. The user's premise ("they
only catch 6") was generous; the real number is four.

**This makes the diversity work far cheaper than estimated.** Raising the target and
relaxing the badge gate is close to a one-line change; the interesting work is then the
POLICY for what to keep.

### 6.2 PC / box automation is **already fully built** — it is simply unused

- `modules/pokemon_storage.py` — full READ access to box contents (`get_pokemon_storage()`,
  `.boxes`, `.contains_species()`, `.get_slot_for_pokemon()`, `first_empty_slot_index`).
- `modules/modes/util/pc_interaction.py` (804 lines) — full UI automation:
  `PCAction.withdraw_pokemon_from_box`, `deposit_pokemon_to_box`,
  `release_pokemon_from_party`, plus item actions, driven by `interact_with_pc(actions)`.
- **Its only consumer in the entire repo is `modules/modes/daycare.py`.**

I estimated PC swapping as "likely the largest single piece of work in this document". That
was wrong: the hard part exists and is proven. What is missing is (a) navigating the story
bot to a PC, and (b) a policy for what to deposit and withdraw. `#24-pc`'s note says "map PC
access points and the PC UI" — the UI half is already done.

Note the story bot currently REFUSES the situation outright
(`early_game.py:4079-4084`): a full party during the HM-learner hunt raises
`BotModeError("… needs PC box management (#24-pc) or a manual swap.")`. Meanwhile the SHINY
path already handles a full party correctly by letting the catch go to the box
(`story_mode.py:1456-1482`) — so the party-full→box path is proven too, just not generalised.

### 6.3 There is NO trainer-seeking capability — but the mechanism is proven

No trainer table, no line-of-sight seeking, no "defeat trainer N" step. Trainers are fought
**incidentally** when their sight-line scripts fire during navigation, and the code's job is
to survive them (`_navigate_riding_out`, `TrainerApproachListener`).

The one precedent is real and directly reusable: the Petalburg Gym door chain
(`early_game.py:5288-5315`) **deliberately initiates a trainer battle** — navigate to the
tile below the trainer, face Up, press A, let the listener fight. That is exactly the
primitive `#24-gymtrainers` needs. What is missing is the DATA (a per-town trainer table
with positions) and a route that visits them, not the mechanism.

### 6.4 Other findings that matter

- **Dead weight is invisible by construction.** The only "is this mon useful" test is
  `_battler_slots()` (`early_game.py:1651`): not an egg, and has ≥1 move with
  `base_power > 0`. **A level-5 Cascoon with Tackle passes.** `_prepare_for_fight` then
  trains only the strongest battler plus those within `TRAIN_CATCHUP_GAP = 6` levels of
  target, explicitly leaving far-below catches "to level organically" — so the L5 Cascoon
  is carried forever, never trained, never benched. A cheap first win: bench or deposit
  anything more than N levels below the lead.
- **`#24-counters` currently ENDS THE RUN.** `_boss_plan_is_hopeless` diagnoses, then
  `story_mode.py:1309-1313` raises `BotModeError` carrying the counter's name. The seam for
  ACTING is that exact `raise`, inside a generator, so `yield from <travel/catch/train>`
  can replace it. And a working "catch species X on sight" primitive already exists —
  `HM_CATCH_TARGET_DEX` + the branch at `story_mode.py:1485-1511`. **This confirms
  `#24-partyvariety`'s "fetch a counter" half and `#24-counters` phase 2 are ONE item.**
  Blocker recorded: every counter candidate currently has `tile: None`, so there is nothing
  to path to yet.
- **Humanising randomness has precedent.** `random.choice(["plus5_max","plus5_avg",
  "escalate_band"])` (`story_mode.py:1330`) already randomises the level-escalation style
  after repeated losses specifically to look less robotic. The personality axes should
  subsume this rather than sit beside it.
- **Training already has a real cost model** — `training_areas.py`: verified grass tiles
  with level bands, `FRAMES_PER_WILD_BATTLE = 1433` (measured), `estimate_frames_to_level`,
  `best_training_area` ranking, fodder detection, `NO_RETURN_GROUNDS`, and a reachability
  oracle (`modules/story/region_reach.py`). Caution should feed THESE, not reinvent them.
  ‼ Note `PENDING_GRASS` already lists `GRANITE_CAVE_1F (35,11)` with a known level band but
  an unmapped tile — relevant to the Granite Cave request.

### 6.5 Revised sequencing (supersedes the note below)

1. **Catch target + badge gate** (`#24-partyvariety`, part 1) — two conditions in
   `_should_catch`. Smallest possible change, and it is the actual cause of the complaint.
2. **Dead-weight benching** — one rule, uses only what exists.
3. **Personality axes** — pure logic, testable offline, subsumes the existing
   `plus5_*` randomisation.
4. **Favourite roll** — small, feeds the personality's curiosity axis.
5. **PC deposit/withdraw policy** — much cheaper than estimated; UI is built, needs
   navigation + policy.
6. **Trainer-first training** (`#24-gymtrainers`) — needs a decomp-verified trainer table
   per town; mechanism already proven at Petalburg.
7. **Counter execution** — merge with `#24-partyvariety`'s fetch half; blocked on counter
   tiles being mapped.

---

## 7. Remaining answers from the user (2026-07-26)

### 7.1 Favourite pool — TWO favourites, one regular and one legendary

> "any pokemon obtainable in pokemon emerald including pokedex and legendaries, matter of
> fact let them have a favorite regular pokemon and a favorite legendary."

**Consequence — do NOT hand-write the pool.** "Obtainable in Emerald" is exactly the kind of
fact this project has twice got wrong from memory, and several Gen-3 legendaries
(Mew, Deoxys, Jirachi, Ho-Oh, Lugia) are **event-only** and not obtainable in normal play.
The repo already has the answer as DATA: `modules/obtainability.py`, `modules/capabilities.py`
and `modules/data/emerald_obtainability.json` (punch list `#41-research` is done). The
favourite roll must be derived from that model, not from a list anyone types out.
‼ Verify before use whether that model marks event-only species as obtainable — if it does,
the legendary pool needs an additional filter, and that is a fact to check, not assume.

**Honest expectation-setting on the legendary favourite:** every Hoenn legendary is a
late-game static encounter, and the bot's current frontier is roughly Badge 3 (Mauville
Gym). A favourite legendary will therefore have **no practical effect on runs for a long
time**. It is worth building — it costs almost nothing once the regular favourite exists,
and it is a real behaviour once the bot gets deep — but it should not be counted as
contributing to run diversity now. Build it, log it, expect nothing from it yet.

### 7.2 Type-check scope — named opponents, plus a reactive trigger

> "mostly gym leaders, rival, wally, elite four but can be used if constantly being defeated
> by a trainer outside or in a gym or dungeon"

Two distinct paths, and pleasingly both map onto machinery that already exists:

**(a) Known-roster path** — gym leaders, the rival, Wally, the Elite Four. For GYM LEADERS
the roster is already decomp-verified in `modules/badge_case.py` (leader, type, ace + level).
‼ The rival, Wally and the E4 have **no verified table yet** — they need the same treatment
before the type check can reason about them. Do not infer them from the gym data.

**(b) Reactive path** — "constantly being defeated by a trainer". This is already measured:
`StoryMode.on_battle_ended` (`story_mode.py:813`) counts `BattleOutcome.Lost` per location
key into `self._defeat_counts`, which already drives survival mode
(`SURVIVAL_WHITEOUT_THRESHOLD = 3`) and the loss escalation. The reactive type check should
hang off that existing counter rather than introducing a second notion of "keeps losing".

This also means the type check is not favourite-specific: it is a general
"is this party member a liability for the fight in front of us" predicate, which the
favourite logic then consults. Building it that way makes it testable in isolation and
reusable by the dead-weight rule and the counter chain.

---

## 8. DECOMP-VERIFIED FACTS — Granite Cave and the Dewford arc (2026-07-26)

All read from `pret/pokeemerald` master. Items marked **[derived]** were computed by
decoding `map.bin` collision/elevation and flood-filling with the game's own rules.

### 8.1 Granite Cave — nothing is gated, but two things bite

| map | group/num | size | `requires_flash` |
|-----|-----------|------|------------------|
| `GRANITE_CAVE_1F` | 24/7 | 42×15 | false |
| `GRANITE_CAVE_B1F` | 24/8 | 32×26 | **true** |
| `GRANITE_CAVE_B2F` | 24/9 | 32×26 | **true** |
| `GRANITE_CAVE_STEVENS_ROOM` | 24/10 | 15×14 | false |

**No HM, item or story flag gates B1F or B2F.** `GraniteCave_B2F/scripts.inc` is three lines
(`.byte 0` — no script at all); B1F's is 11 and contains only the hole machinery. No
boulders on any floor. Verified, not assumed.

**Encounters (rate 10 = 5.56 %/step on both floors):**
- **B1F land** — Zubat 30 %, **Aron 40 %**, Abra 10 %, Makuhita 10 %, Sableye 10 %, **L9-11**
- **B2F land** — Zubat 30 %, **Aron 40 %**, Abra 10 %, Sableye 20 %, **L10-12** (no Makuhita)
- B2F also has a `rock_smash_mons` table (Geodude/Nosepass L10-20) — **unreachable during
  this arc**, Rock Smash needs Badge 3. It gates only 7 of 353 tiles, so it is not a blocker.

**‼ TWO REAL HAZARDS FOR A GRINDING LOOP:**

1. **B1F has 62 cracked-floor tiles that drop the bot to B2F.** `GraniteCave_B1F/scripts.inc:2-10`
   sets `STEP_CB_CRACKED_FLOOR` + `setholewarp MAP_GRANITE_CAVE_B2F`. Stepping on
   `MB_CRACKED_FLOOR` arms a **3-step delay**, then the tile becomes a hole and the next step
   onto it warps the player down to the SAME (x,y) on B2F. A back-and-forth grind lane that
   wanders onto those tiles will silently relocate the bot mid-grind. **[derived]** they sit
   in x2-7 & x15-24, y1-6 (plus x3-5 y5-6, x18-24 y4-6); the southern/central corridors have
   none.
2. **Flash is locked behind Badge 2** (`src/party_menu.c:120-127`, gate at `:3725`) — which is
   Dewford's own badge. So any PRE-gym cave trip is unavoidably at flash level 7. ‼ This is
   **cosmetic only**: collision and pathing are unaffected, so the bot can navigate blind.
   It does mean "grind first, then gym" cannot be improved by fetching Flash.

**[derived] Best grind lane: the B2F SOUTH POCKET.** B2F is four disconnected pockets
(hub-and-spoke via B1F). The south pocket has **~205 encounter tiles, zero cracked floors**,
and the highest levels in the cave (L10-12). Route: `Route106 (48,16)` → `1F (37,12)` →
`1F (17,11)` ladder → `B1F (4,21)` → cross B1F → `B1F (28,21)` ladder → B2F south.
B1F's own main region has 195 encounter tiles but carries the cracked-floor hazard.

‼ Note `modules/story/training_areas.py` already lists `GRANITE_CAVE_1F (35,11)` in
`PENDING_GRASS` — 1F is the WEAKEST floor (L6-10) and is the one currently known to the bot.

### 8.2 Dewford trainers — the user's premise needs one correction

**‼ DEWFORD TOWN HAS ZERO TRAINERS.** All five object events on `DewfordTown/map.json` are
`TRAINER_TYPE_NONE` (a woman, Mr. Briney, a fisherman, the boat, the Trendy Phrase boy), and
the Hall and both houses contain none. There is nothing on the island itself to farm. The
"trainers on the island" are really **the gym's six, plus two on Route 106**.

**Dewford Gym — six trainers, all L13, ₽2,184 total:**

| trainer | class | party | position | facing |
|---------|-------|-------|----------|--------|
| TAKAO | Black Belt | Machop L13 | (2,18) | Up |
| JOCELYN | Battle Girl | Meditite L13 | (15,3) | Down |
| LAURA | Battle Girl | Meditite L13 | (12,25) | Up |
| BRENDEN | Sailor | Machop L13 | (14,12) | Right |
| CRISTIAN | Black Belt | Makuhita L13 | (7,8) | Right |
| LILITH | Battle Girl | Meditite L13 | (16,9) | Down |
| *(Brawly)* | Leader | Machop L16, Meditite L16, **Makuhita L19 @ Sitrus** | (4,3) | Down |

**‼ ALL SIX CAN BE — AND ARE — SKIPPED.** **[derived]** every sight cone is a dead-end spur
off the main corridor: 142 tiles are reachable ignoring cones, **114 while avoiding all six**,
and Brawly's approach tile is in that set. So the gym trainers **never fire on the way to
Brawly**. That is precisely why the bot is not banking this XP and money today — it is not a
bug, the bot simply walks past them. To collect them the bot must **deliberately step into
each cone** (or walk adjacent and press A, the primitive Petalburg's door chain already uses).

The dark-gym "puzzle" is **not** a switch puzzle — there are no coord_events and no trigger
tiles. Defeating trainers only widens the flash radius (`7 - count`). **The maze is fully
navigable at flash level 7**, so darkness can be ignored entirely.

**Route 106 — two foot-reachable trainers** (Elliot ₽400, Ned ₽440); Douglas and Kyla are on
water and need Surf. Routes 107 and 108 are entirely Surf-only and out of scope for this arc.

**Money available on foot in the whole Dewford arc: ₽4,924** — Elliot 400 + Ned 440 + six gym
trainers 2,184 + Brawly 1,900. (Doubles with an Amulet Coin.) Formula
(`src/battle_script_commands.c:5618-5631`) is `4 × lastMonLevel × multiplier × classValue`;
‼ it uses the **LAST party slot's level, not the highest** — irrelevant for every Dewford
trainer, but it will matter elsewhere.

## Sequencing note (SUPERSEDED by §6.5 — kept for the reasoning)

If all three are built, the order that de-risks best is:

1. **Trainer-first training** — smallest, most contained, and directly attacks the observed
   #1 failure (attrition).
2. **Favourite roll** — small, self-contained variance knob; measurable immediately.
3. **PC swapping / party management** — largest, and depends on decisions from both above.

Nothing here should start before the current x4 batch's logs have been reviewed, since they
may change what the priority ought to be.
