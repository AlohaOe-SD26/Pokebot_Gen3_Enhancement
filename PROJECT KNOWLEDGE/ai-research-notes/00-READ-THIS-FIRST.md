# ⚠ AI-RESEARCH NOTES — UNVERIFIED. NOT A SOURCE OF TRUTH.

**READ THIS BEFORE USING ANYTHING IN THIS DIRECTORY.**

Every file here was produced by an **AI research agent** (Gemini, via
`tools/story-dev/gemini_relay.py`), commissioned to front-load information for future work.
These notes are **LEADS: possible, plausible, and explicitly NOT authoritative.**

## The rule (user directive, 2026-07-24)

> Note it with a stub/marker in the documentation so future AI agents can understand that
> there are notes from other AI agent runs that should be considered as **possible but not
> taken for a source of truth**.

So:

* **Never write code from a note in here.** Verify first, against the ROM or the decomp.
* **Never overwrite a current-state doc with a note from here.** The `PROJECT KNOWLEDGE/01`–`05`
  files and `12-STORYMODE-DESIGN.md` remain the authority on what is actually true and built.
  These notes are an *appendix* reached by a marker, never a replacement.
* **A note that contradicts a verified doc loses**, unless and until it is itself verified.

## Verification gates that apply to everything here

| claim type | must pass |
|---|---|
| `FLAG_*` / `VAR_*` names | `tools/story-dev/audit_flag_names.py` — a phantom name silently reads False forever and gates a segment into an eternal derail loop (the Ch9a `DEFEATED_RIVAL_ROUTE_110` incident) |
| coordinates / warps / tiles | a live probe on a real save; collision + elevation + tile type dumped |
| learnsets / TMs / base exp / encounter tables | `sandbox-pokebot/modules/data/*` |
| "you can/can't reach X" | `calculate_path` from a REAL captured position, plus a control tile that DOES path |
| anything about a legendary that can be defeated | confirm before building a hunt — a KO'd one-time static is unrecoverable |

## Proof this caution is warranted

In the very first round of these notes, an agent concluded **(INFERENCE)** that the user had
misremembered a healing house on the Route 112/113 corridor and that no such NPC house exists.
Our own `modules/map_data.py` contains **`ROUTE111_OLD_LADYS_REST_STOP = (18, 1)`**, on the route
that runs between 112 and 113 — the user was right and the note was wrong, confidently and in a
well-formatted table. See `PROJECT KNOWLEDGE/18-RESEARCH-HEALPOINTS-AND-LEGENDARIES.md`.

Track record so far: **1 confident error in the first 10 answers, on the single most
load-bearing question asked.** Treat accordingly.

## Index

| file | topic | status |
|---|---|---|
| `../18-RESEARCH-HEALPOINTS-AND-LEGENDARIES.md` | healing points + legendaries dossier (10 angles) | LEADS; angle a1's conclusion REFUTED |
| `story-notes-*.md` | remaining story chapters (Mt. Pyre → Champion) | LEADS, unverified |

### Story notes (10 angles, 2026-07-24) — ALL UNVERIFIED

| file | topic |
|---|---|
| `story-notes-s1.md` | Mt. Pyre, all floors — Magma events, Red/Blue Orb, warps, encounters |
| `story-notes-s2.md` | Team Magma hideout (Jagged Pass) + Aqua hideout (Lilycove), incl. the teleporter puzzle order |
| `story-notes-s3.md` | Routes 120-123 + Lilycove — Kecleon, Safari gate, Move Deleter, HM gating east |
| `story-notes-s4.md` | Seafloor Cavern + Cave of Origin, Dive, the awakening sequence, Sootopolis |
| `story-notes-s5.md` | Gym 7 Tate & Liza (DOUBLE battle, spin tiles) + Gym 8 Juan (ice-floor path) |
| `story-notes-s6.md` | Victory Road + Elite Four + Champion **Wallace** (Emerald differs from RS) |
| `story-notes-s7.md` | All 8 HMs — where obtained, badge needed to use, every hard block without one |
| `story-notes-s8.md` | Missable / irreversible one-time events and gifts |
| `story-notes-s9.md` | Overworld obstacle mechanics at tile level (boulders, spin tiles, cracked ice, Sky Pillar) |
| `story-notes-s10.md` | Main-plot FLAG_/VAR_ reference — ‼ every name here must pass `audit_flag_names.py` |

**Highest-value angles for the next build phase:** `s7` (HM gating — a bot that walks into a
state it cannot leave is the worst failure mode), `s9` (obstacle mechanics — the Fortree gate
work proved this class is solvable when the mechanic is understood exactly), and `s8`
(irreversible events — the only ones a bot can permanently ruin).

**Highest-risk angle:** `s10`. A phantom flag name reads False forever and gates a segment into
an eternal derail loop. Verify every single name before use.

---

# ‼ RESULT OF THE THREE-PASS EXPERIMENT (2026-07-24) — READ BEFORE TRUSTING ANY PASS

The user asked for research → verify → verify again on the ITEM topics (15 research angles,
then 10 verifiers, then 10 adjudicators). Here is what actually happened, because the outcome
changes how every note in this directory should be read.

## Pass 1 — 15 research notes
~150 KB of confident, well-formatted, table-heavy output. Files `item-notes-i01..i15.md`.

## Pass 2 — 10 ADVERSARIAL critiques (`VERIFY1-*.md`)
Not "answer it again" — each was handed the actual note and told to find the errors, with a
fixed output shape (WRONG / WRONG GAME / MISSING / UNVERIFIABLE / VERDICT).

**Result: 8 × SIGNIFICANT ERRORS, 1 × UNRELIABLE, ZERO × MOSTLY SOUND.**

Findings were specific and checkable, not nitpicks — e.g. an invented Revive in Steven's house
("not just wrong, it is a complete hallucination — it invents an item, coordinates, a flag, and
a false narrative"), HM07 Waterfall placed in the Cave of Origin, the bike gated on "defeat
Wattson", a Meowth swarm on Route 116 (Meowth is not in Emerald's wild tables), and categorical
ABSENCE claims — the most dangerous shape, since absence cannot be disproven by looking.

## Pass 3 — 10 ADJUDICATORS (`ADJUDICATED-*.md`)
Each received the note AND its critique and had to rule per disputed claim, with a citation.

**Result: nine of ten declared ~100% confidence**, typically phrased as "all claims were
verifiable against the pokeemerald decompilation project".

## ‼ THE ACTUAL LESSON

That 100% is **not credible**, and it is the finding that matters most:

1. The adjudicator did NOT inspect the decomp. It has no file access. It **recalled** and then
   described recall as verification. The phrase "verifiable against the decomp" is doing work it
   has not done.
2. It is the SAME MODEL that produced the hallucinations in pass 1 and the critiques in pass 2.
   Stacking same-model passes converges on **confident-sounding** output, not on truth.
3. So pass 3's rulings are a THIRD OPINION dressed as a verdict. Its "CONFIRMED-GOOD CORE"
   sections are the most useful part — but they are still leads.

**Verification requires an EXTERNAL ground truth.** Two are available in this repo and both are
cheap:
* `gh api repos/pret/pokeemerald/contents/<path>` — fetch the real decomp file and read it. This
  is how the Fortree gate mechanics were settled, and that port then matched the live emulator
  4/4.
* A live probe on a real save (`tools/story-dev/probe_*.py`), plus `modules/data/*` for
  learnsets/encounters/base-exp, and `audit_flag_names.py` for every FLAG_/VAR_ name.

**Therefore: treat these notes as a CROSS-REFERENCE — a list of things to go check — never as
data.** Where a note and a critique disagree and the adjudicator ruled, the ruling narrows what
to check; it does not settle it.

## Practical reading order for a future agent
1. `ADJUDICATED-*.md` → §2 "CONFIRMED-GOOD CORE" and §3 "DO NOT USE". Start here.
2. `VERIFY1-*.md` → the "most dangerous claim" line, so you know what would hurt most if wrong.
3. `item-notes-*.md` → only for coverage/ideas, never for values.
4. Then VERIFY against the decomp or the ROM before a single line of code depends on it.

---

# ‼ PROCESS CORRECTION (user directive, 2026-07-25): CLAUDE VALIDATES GEMINI

The three-pass Gemini experiment above showed that stacking same-model passes converges on
confident-sounding output, not on truth — pass 3 claimed ~100% confidence while describing
RECALL as "verifiable against the decomp".

**The corrected pipeline:**

| stage | who | why |
|---|---|---|
| research fan-out | **Gemini**, many angles | cheap breadth; good at enumerating what to look for |
| adversarial critique | **Gemini**, given the note | cheap; genuinely surfaces suspect claims |
| **VALIDATION (final word)** | **a CLAUDE subagent** | it is the only one with REAL TOOL ACCESS |

A Claude validator can actually ground a claim:
* `gh api repos/pret/pokeemerald/contents/<path>` — read the REAL decomp file (this is how the
  Fortree rotating-gate rules were settled, and that port then matched the live emulator 4/4);
* read `sandbox-pokebot/modules/data/*` for learnsets, encounters, base exp, items;
* run `tools/story-dev/audit_flag_names.py` on every `FLAG_`/`VAR_` name;
* drive a live emulator probe on a real save.

Gemini can do none of these. So **a Gemini pass may never be the final word on a fact that code
will depend on.** The user has explicitly accepted the extra token cost of Claude validation.

Files named `CLAUDE-VALIDATED-*.md` in this directory are the ONLY ones whose claims were checked
against an external ground truth. Everything else remains a lead.

---

# ✅ FIRST CLAUDE-VALIDATED ROUND (2026-07-25) — the directive is vindicated

`CLAUDE-VALIDATED-items-round1.md` is the first file here grounded in EXTERNAL truth. A Claude
subagent with real tool access reached `gh api repos/pret/pokeemerald/contents/<path>` for the
whole session and **grounded all 9 priority claims, zero unresolved** — every ruling cites a
decomp file it actually fetched and read (`map.json`, `scripts.inc`, `species_info.h`, `tv.c`,
`berry.c`).

## ‼ The meta-finding: the CRITIQUE pass was also wrong

Not just the research notes — the adversarial Gemini critiques contained their own errors:
* **HM07 Waterfall** — the note said Cave of Origin, the critique "corrected" it to Marine Cave.
  **Both wrong.** Wallace gives it in Sootopolis City, gated by
  `FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE`.
* **Route 134** — the note said no hidden items; the critique "corrected" that. **The note was
  right** and the critique fabricated the correction.
* **Relicanth's held item** — note said Deep Sea Scale, critique said Deep Sea Tooth. **Both
  wrong**: `ITEM_GREEN_SHARD`. (Deep Sea Tooth/Scale come only from trading the Scanner to
  Captain Stern.)

So a same-model critique can invent a wrongness exactly as readily as a note invents a fact.
**Only a tool-using validator can be the final word.** That is now the standing rule in
`CLAUDE.md`.

## Corrected facts from round 1 (safe to use — each cites a read file)

| claim | truth |
|---|---|
| Revive in Steven's House | **does not exist** — hallucinated; that script gives HM Dive |
| HM07 Waterfall | Wallace, **Sootopolis City**, gated `FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` |
| Bike prerequisite | **none at all** in Rydel's script |
| Route 116 post-E4 outbreak | mechanic is REAL (5 fixed entries); species is **Skitty**, not Meowth |
| Relicanth wild held item | `ITEM_GREEN_SHARD` |
| Mirage Tower fossils | item balls (not wild battles), on **4F**, mutually exclusive |
| Pacifidlog "TM27 for a Green Shard" | no such trade — a **free friendship-gated** TM gift (Return/Frustration), renewable weekly |
| Berry "tree death" | resets to blank; plus an undocumented 10-cycle regrowth cap |
| Route 134 hidden items | **genuinely none** — the original note was correct |

---

# CONCEPT ROUND (2026-07-25) — the non-code punch-list items

12 angles on the SYSTEM-DESIGN topics, run on the relay's correct top-tier default
(`gemini-3.1-pro-preview` — see 08-MISTAKES for the day I overrode it with a two-generation-old
model on ~35 calls and then blamed the tool).

**Framed deliberately as mechanics, not design.** Each prompt demanded four sections:
**A** the constraints the ROM actually enforces (with VERIFIED/RECALL/UNSURE per claim),
**B** what the bot can OBSERVE in memory (which decides whether a strategy is implementable at
all), **C** an option space of 2-4 strategies with their failure modes and how the bot would
DETECT failure — explicitly *not* a recommendation, and **D** TRAPS: ways an automated player
permanently loses value or wedges itself. D is the section that matters most, because a bot
repeats a mistake thousands of times.

Architectural choices stay with us. Gemini is good at enumerating what the ROM allows; it is
weakest exactly where a design decision has to be defended.

| file | topic |
|---|---|
| `concept-notes-c01.md` | PC / box storage — incl. what to check BEFORE a ball so a catch is never wasted |
| `concept-notes-c02.md` | catch-rate formula, every ball multiplier, the optimal observable throw policy |
| `concept-notes-c03.md` | building a type-diverse roster; obedience caps; cheap bench levelling |
| `concept-notes-c04.md` | switching & counter-play; what is READABLE about the opponent mid-battle |
| `concept-notes-c05.md` | healing items & money economy; heal-walk vs carry-potions break-even |
| `concept-notes-c06.md` | water traversal — Dive layers, currents, whirlpools, safe water pathing |
| `concept-notes-c07.md` | wild-encounter mechanics, Repel slot quirk, encounters-per-frame |
| `concept-notes-c08.md` | Mystery Gift — and what is flatly IMPOSSIBLE without event data |
| `concept-notes-c09.md` | legendary hunting; which can be PERMANENTLY LOST; which to never automate |
| `concept-notes-c10.md` | failure recovery & learning; what persists vs resets on map re-entry |
| `concept-notes-c11.md` | move learning, single-use TMs, how to score a move from memory values |
| `concept-notes-c12.md` | EXP formula; does mid-battle EXP survive a whiteout; XP-per-frame |

**Highest-stakes claims to validate first** (a wrong answer here costs something irreversible):
`c09` (permanently-losable legendaries), `c01` (can a caught Pokémon be lost with full boxes),
`c11` (single-use TMs), `c12` (does mid-battle EXP survive a whiteout — the whole boss-training
strategy rests on this).

---

# ✅ CLAUDE-VALIDATED: concepts round 1 (2026-07-25)

`CLAUDE-VALIDATED-concepts-round1.md` — **51 claims ruled: 30 CONFIRMED, 15 REFUTED, 6
UNRESOLVED**, every ruling citing a decomp file fetched and read via `gh api` in that session,
cross-checked against our own `species.json` and `event_flags/emerald.txt`. Nine findings are
marked NEW (absent from the Gemini notes and behaviour-changing).

## The four high-stakes rulings

**1. Mid-battle EXP DOES survive a whiteout → boss-training mode is VALID.** `DoWhiteOut()`
(`src/overworld.c:358-366`) only runs the script, halves money, heals, resets field flags and
warps. No save reload, no party rollback. ‼ But two corrections to how we reason about it:
EXP goes only to mons **alive at the instant the opponent faints**
(`battle_script_commands.c:3367,3431`) — a mon that trades a KO for its own life banks nothing;
and the trainer ×1.5 applies **per recipient after the split**, not to the total, so any
XP-per-frame figure derived from the notes' formula is wrong.

**2. A caught Pokémon CANNOT be lost with a full party and full boxes.** Both throw paths are
guarded before the ball leaves your hand (`item_use.c:938-956`, `battle_main.c:4268-4277`) and the
ball is **not consumed** — so no pre-throw space check is needed. The real risk is the inverse: an
infinite bag→"The BOX is full."→bag loop; detect it by the ball count failing to decrement.
Storage-full requires **all 420 slots**, and boxes **do** auto-wrap — which refutes the notes'
"current box full blocks the throw" trap outright.

**3. Legendaries — two safety checks that would each have been USELESS if written from the notes:**
* The **roamer sets no flag at all**; it clears `roamer.active` (`roamer.c:237-239`).
  `FLAG_DEFEATED_LATIAS_OR_LATIOS` is written only by the Southern Island script, so gating on it
  reads False forever. Use `modules/roamer.get_roamer() is not None`.
* The **roamer dies on every ODD battle outcome** — `battle_main.c:5238` tests
  `(gBattleOutcome & B_OUTCOME_WON)` with `B_OUTCOME_WON == 1`, so WON, **DREW (mutual KO)**,
  **PLAYER_TELEPORTED**, CAUGHT and FORFEITED all destroy it. The decomp itself labels this a bug.
  Safe exits: Run, whiteout, MON_FLED.
* `FLAG_DEFEATED_{RAYQUAZA,GROUDON,KYOGRE,REGI*}` is **also set on a successful catch** — it means
  "encounter resolved", not "destroyed".
* **Whiteout is the safe abort for every scripted static** (the script never resumes, so no flag
  is written).
* ‼ Our own flag table stores names **without** the `FLAG_` prefix (`"DEFEATED_RAYQUAZA"`).

**4. TMs are single-use — but EVALUATING one is FREE.** Cancelling the "which move to forget"
prompt does **not** consume the TM (`party_menu.c:4824-4839`). HMs cannot be selected as the
forgotten move (`pokemon_summary_screen.c:2246-2254`). ‼ **`IsMonValidForMoveDeleter` does not
exist** — the real guard is `IsLastMonThatKnowsSurf` (`party_menu.c:6407-6430`), **SURF ONLY**.
Dive, Waterfall, Fly, Strength, Rock Smash, Cut and Flash are **unguarded by the game**, so the
bot must own the HM-coverage invariant itself or it can strand a run permanently.

**Bonus — three throw-policy numbers in the notes are wrong:** Dive Ball is 3.5× **underwater
only**; Nest Ball is `max(40−L,10)/10`; Timer Ball is `(turns+10)/10`. Master Ball does not skip
the formula, and sleep + poison **stack** to ×3.0.

## Still LEADS (not examined)
`c03`–`c08`, `c10`. And parked UNRESOLVED with reasons: whether Kyogre/Rayquaza know
Double-Edge/Outrage at Lv70 (**this decides whether a False-Swipe legendary hunt is safe at all**),
the Bad-Egg-contagion claim, `gExperienceTables` values, Match Call rematch odds.

---

# STORY ROUND, TWO GENERATIONS (2026-07-25)

Each `story-notes-sN.md` (Gemini **2.5-pro**) now has a `story-notes-sN-v2.md` — the SAME prompt
re-run on Gemini **3.1-pro**. Where the two generations DISAGREE is a high-signal pointer to a claim
worth grounding; **agreement between them is NOT evidence** (measured below: they agree and are both
wrong ~35% of the time on this material).

# ✅ CLAUDE-VALIDATED: story round 1 (2026-07-25)

`CLAUDE-VALIDATED-story-round1.md` — **~65 claims ruled** across `s7` (HM acquisition & gating),
`s8` (missable/irreversible events), `s9` (obstacle mechanics) and `s10` (main-plot flag/var
reference), every ruling citing a decomp file fetched and read via `gh api`, cross-checked against
our own `event_flags/emerald.txt` and `event_vars/emerald.txt`. Nine sections are marked NEW —
absent from both generations and behaviour-changing.

**Verdict on the two generations: 3.1-pro is clearly better and re-running the tainted rounds on it
is worth the tokens** — s10 phantom flag names fell from **18/51 (35%)** to **4/38 (11%)**, and on
head-to-head disagreements 3.1 won **21–1**. On the designated calibration question (HM07 Waterfall,
already validated in round 1) 2.5-pro invented a map AND a script label and tagged it VERIFIED;
3.1-pro got both exactly right.

‼ **But 3.1-pro's failure mode is more dangerous.** 2.5-pro mostly hallucinates in *citations*;
3.1-pro hallucinates in the *actionable* section — all three of its "your bot must hardcode an
interrupt here" constraints (TM Earthquake, Magma Hideout, TM Thief) rest on permanence that does not
exist. **Grade its NAMES highly and its ARCHITECTURAL ADVICE not at all**, and budget a Claude
validation pass on top of every re-run: the cost curve improved, the requirement did not.

**And the meta-rule that generalises:** where the two generations AGREE they are still wrong ~35% of
the time here (15 BOTH-WRONG rulings). Disagreement is a good *search strategy* for finding
fabrications fast; agreement is **not** a confidence signal.

## The findings most likely to save a build phase

* **Four of eight HMs are given by a MAP-ENTRY (`ON_FRAME_TABLE`) trigger, not by talking.** Surf
  (`VAR_PETALBURG_CITY_STATE==4`), Strength (`VAR_RUSTURF_TUNNEL_STATE==4/5`, after Rock Smash),
  Dive (`VAR_STEVENS_HOUSE_STATE==1`) — walk in, don't press A. Fly is a **coord trigger** at
  Route 119 **(25,31)/(26,31)** that starts a `trainerbattle_no_intro` immediately.
* ‼ **On three of the four mandatory `multichoice` menus a blind A-press picks the WRONG option, and
  one of them LOOPS FOREVER.** `CaveOfOrigin_B1F_EventScript_WheresRayquaza` defaults to index 0 and
  only **index 2 ("Sky Pillar")** advances the story — cases 0/1/3, the switch default AND B-press
  all `goto` back to the same prompt, with no counter and no timeout. Mr. Briney's two boat menus
  default to **decline** (Route 104, correct = 0) and **cancel** (Dewford, correct = 1 for Slateport).
  All 49 `multichoice` sites were swept; the critical-path table with indices is §3i.
* ‼ **Both generations invented permanence that does not exist — 2.5-pro five times, 3.1-pro three
  times.** The Master Ball, TM Thief, TM Earthquake, every Magma Hideout item, the unchosen fossil
  and the S.S. Tidal content are all **NOT missable**. What genuinely vanishes: Aqua Hideout *grunts*
  at Badge 7, Magma Hideout *grunts* at the Groudon cutscene, and each *Trick House puzzle* the
  moment you clear it. Genuinely irreversible one-shots: the fossil pick, **Latias vs Latios**
  (`VAR_ROAMER_POKEMON`, 0=Latias), the Johto starter, and **Scanner → Deep Sea Tooth *or* Scale**.
* Gift **Pokémon** fall through to the PC when the party is full (`MON_GIVEN_TO_PC`); gift **eggs**
  hard-require a free party slot. And `JaggedPass_OnResume` `checkitem ITEM_MAGMA_EMBLEM` on **every**
  visit — sell the emblem and the Magma Hideout can never open.
* ‼ **`FLAG_DEFEATED_MAGMA_SPACE_CENTER` is NOT monotonic** — the rival's Rayquaza PokéNav call
  `clearflag`s it. §3f of the validated file is an **exhaustive census of every non-monotonic
  `FLAG_DEFEATED_*`/`FLAG_RECEIVED_*` in the game** (the E4 member flags are wiped at the Hall of
  Fame; the event legendaries are re-enabled there). **New prevention rule: passing
  `audit_flag_names.py` proves a name is readable, NOT that it is monotonic — grep for a
  `clearflag` of the exact name before gating a segment on it.**
* **HM07 Waterfall requires talking to BOTH Maxie AND Archie** in Sootopolis at
  `VAR_SOOTOPOLIS_CITY_STATE == 5` to set `FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` — which also unlocks
  the Gym door and every house door. Neither note mentions it; miss one NPC and the run is dead.
* **The mandatory Sky Pillar climb has NO cracked floors and needs NO Mach Bike** — it runs on
  `LAYOUT_SKY_PILLAR_*_CLEAN` while `VAR_SKY_PILLAR_STATE < 2`. Cracked floors exist only on the
  optional post-crisis return trip, and only on **2F and 4F** (Mirage Tower: **2F and 3F**).

> CORRECTED 2026-08-24 -- "NO cracked floors" IS FALSE. `_Clean` is a PER-FLOOR fact: `2F_Clean` has 0 cracked
> tiles but **`4F_Clean` has 5** (decoded from the shipped `SkyPillar_4F_Clean/map.bin`). The ascent
> REQUIRES stepping on one: `4F (3,1)` and `3F (7,1)` are SEALED POCKETS, unreachable from the
> `4F (11,1)` arrival even if every cracked tile is treated as passable. The only way in is a
> deliberate fall through `4F (6,4)`/`(7,4)` -- NOT `(9,4)`, which lands in 3F's MAIN region and
> wastes the climb. The "no Mach Bike" half of this claim SURVIVES. See the Ch21 ATLAS in
> `12-STORYMODE-DESIGN.md`.

* **Cut, Fly and Flash are never hard blocks.** `requires_flash` only drives a scanline effect;
  there are zero cuttable trees on any critical-path map. v1's "Cut trees block the Aqua Hideout" is
  a fabrication — the entrance is a **Surf** warp at (70,5) elevation 1.
* **`src/field_move.c` does not exist**, and 10 C function names cited across the two notes have
  **zero** hits in the repo (`CheckUseCut`, `TryCutTree`, `PushObject`, `CheckForForcedMovement`, …).
  The real badge gate is `src/party_menu.c:3725`, `FlagGet(FLAG_BADGE01_GET + fieldMove)`.
* **`VAR_SOOTOPOLIS_CITY_STATE` has SEVEN states (0-6)**, not the five both notes published — the
  complete machine with every setter is in §3f of the validated file. State 5 (Rayquaza awakened,
  set at `SkyPillar_Top/scripts.inc:126`) is the only window in which Maxie and Archie can be
  talked to; state 6 comes from **beating Juan**.
* **Exact tile-level mechanics** for the Sootopolis ice puzzle (thresholds **8/28/67** on
  `VAR_ICE_STEP_COUNT`; 0 = you fell; visited bits in `VAR_TEMP_1..VAR_TEMP_A`), currents
  (`MB_EASTWARD_CURRENT` &c. — **not** `MB_CURRENT_*`; **no whirlpools exist in Emerald**), and a
  full boulder/rock/tree census with coordinates for Victory Road, Seafloor Cavern, Magma Hideout,
  Granite Cave and the mainland routes.


---

# ✅ CLAUDE-VALIDATED index (keep this current)

| file | scope | headline |
|---|---|---|
| `CLAUDE-VALIDATED-items-round1.md` | 9 contested item claims | the critique pass was ALSO wrong in places |
| `CLAUDE-VALIDATED-concepts-round1.md` | c01, c09, c11, c12 (+c02 spot) | mid-battle EXP survives a whiteout ⇒ boss-training is valid |
| `CLAUDE-VALIDATED-story-round1.md` | s7, s8, s9, s10 (~65 claims) | flags are not all monotonic; a mandatory menu loops forever |
| `CLAUDE-VALIDATED-concepts-round2.md` | c03, c07, c10 (+c04, c06) | Fortree re-entry recovery VERIFIED correct; daycare silently eats HMs |
| `CLAUDE-VALIDATED-concepts-round3.md` | c05, c08 (+c02, c06) (~50 claims) | the impossible-without-event-data list; whiteout wipes E4 flags |

# ‼ BEST GROUNDING METHOD FOUND (adopt this by default)

Round 3 hit a GitHub 403 after ~8 `gh api search/code` calls, and switched to a **local partial
clone of the decomp**:

```
git clone --depth 1 --filter=blob:none --sparse https://github.com/pret/pokeemerald
git -C pokeemerald sparse-checkout set src data include     # ~44 MB
```

Why this is strictly better than per-file `gh api` fetches:
* whole-tree `grep` becomes free, so you stop rationing lookups;
* **ABSENCE claims become checkable** — "there is no warp to Birth Island outside
  `LilycoveCity_Harbor`" is provable by grep and unprovable by fetching files one at a time. This
  project has been burned repeatedly by categorical absence claims, and this is the fix;
* no rate limit.

Round 3 used it to prove several claims false that earlier rounds could only mark UNRESOLVED —
including that `src/pokeball.c` **does not exist** (ball logic lives in
`battle_script_commands.c`) and that `Jirachi` has zero scripts and zero encounter entries in
Emerald.
