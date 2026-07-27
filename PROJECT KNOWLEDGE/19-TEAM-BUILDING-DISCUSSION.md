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

## Sequencing note

If all three are built, the order that de-risks best is:

1. **Trainer-first training** — smallest, most contained, and directly attacks the observed
   #1 failure (attrition).
2. **Favourite roll** — small, self-contained variance knob; measurable immediately.
3. **PC swapping / party management** — largest, and depends on decisions from both above.

Nothing here should start before the current x4 batch's logs have been reviewed, since they
may change what the priority ought to be.
