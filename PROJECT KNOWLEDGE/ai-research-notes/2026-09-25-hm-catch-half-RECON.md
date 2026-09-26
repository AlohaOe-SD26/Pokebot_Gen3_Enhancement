# The CATCH half of the HM directive — what already exists. RECON NOTE, 2026-09-25

> ⚠ **A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`). Produced by a Claude recon subagent over our
> own `sandbox-pokebot/`. ✅ The claims I **re-opened and verified myself** are marked VERIFIED
> BY ME. Everything else is a search index — check it before building on it.

**Scope.** `#24-hm-slaves`'s WITHDRAW half shipped 2026-09-25 (`--driver hmpcfirst`). This note
covers the next bullet: **catch a new carrier when neither the party nor the PC has one**, per the
user's 2026-09-25 directive — *"as well as catch new pokemon (not duplicates unless shiny) that it
can use to teach it the hm move it needs."*

---

## ⭐ THE HUNT ALREADY EXISTS — `ensure_hm_learner`

Reported at `modules/story/early_game.py:4941`. It checks the party, picks hunting grounds,
provisions balls, navigates, and spins with `HM_CATCH_TARGET_DEX` armed, on a **40,000-frame
deadline** (`:5020`). ⇒ the *catching* is built. What broke for the user was everything BEFORE it.

**Its four give-up messages** (reported; quote them before relying on them, they are what a user
sees):
* `:4959` — *"No party mon can learn {move} and the party is full — needs PC box management..."*
* `:4966` — *"No party mon can learn {move} and no swept training grass hosts a learner species —
  extend training_areas.TRAINING_GRASS first."*  ← **the message the user reported**
* `:5011` — *"Cannot hunt a {move} learner: no Poké Balls and no money to buy any."*
* `:5039` — *"Hunted for a {move} learner but never caught one (timeout/balls)."*

## ⛔ THE HUNTING GROUNDS ARE THE NARROW PART — AND THE FIX IS **NOT** THE INDEX

Reported: `modules/story/training_areas.py:77-120`, `TRAINING_GRASS` = **11 entries**
`(map_enum, spin_tile, level_band)`, ordered earliest→latest, and
`early_game.py:4979` does `ordered = list(reversed(grounds))` — **furthest-progressed first**.

‼ **CARRIED FORWARD FROM EARLIER WORK, AND IT IS THE LOAD-BEARING DESIGN CONSTRAINT HERE:** widen
the **TABLE** (curated, each row carrying a TILE), never the INDEX. `modules/encounter_index.py`
rows carry `map`, `map_name`, `method`, `rate`, `min_level`, `max_level` and **NO TILE**
(`:102-111`) — so an index row cannot tell the bot *where to stand*. And `reversed()` means a
naively widened table would prefer the most dangerous late-game ground first.

## ⚠ THE DUPLICATE / SHINY QUESTION — THE AGENT'S FRAMING WAS WRONG, THE LINE IS REAL

✅ **VERIFIED BY ME**, `plugins/custom_modes/story_mode.py:3368`:

```python
if _eg.HM_CATCH_TARGET_DEX and encounter is not None and not getattr(encounter, "is_shiny", False):
```

⛔ **DO NOT READ THIS AS "SHINIES ARE REJECTED FOR HM LEARNERS"**, which is how the recon reported
it, nor as contradicting the user's directive. `not is_shiny` makes the HM branch **DEFER** on a
shiny — it declines to consume a shiny as a disposable HM mule and leaves it to whatever handles
shiny encounters. ✅ And the paragraph below settles WHERE — it is the desired behaviour, verified, not merely probable.

✅✅ **RESOLVED THE SAME DAY — AND THE ANSWER IS THAT THERE IS NOTHING TO FIX.** VERIFIED BY ME:

* `:3322-3332` states the intent outright — *"a wild shiny is a rare collectible and is ALWAYS worth
  a catch attempt — **even an already-caught species, even with a full party (→ PC box)**, at any
  story stage. **This check runs FIRST** so it pre-empts swap-training and ordinary team-catching."*
* `:3334` `if encounter is not None and encounter.is_shiny:` … `:3352` **`return
  StoryShinyCatchStrategy()`** — it **RETURNS**, so `:3368` is never reached for a shiny.
* `:3356-3359` — with no usable ball, or in the scripted Tutorial battle, it fights through. It
  never stops the bot.
* `:1662-1665` — *"Pre-empted upstream by `StoryShinyCatchStrategy` … Returning False here is not a
  refusal to catch shinies — it is **refusing to catch them TWICE**."*

⇒ the user's *"not duplicates unless shiny"* is **ALREADY SATISFIED**: a shiny is caught regardless
of duplication, and the HM branch correctly declines to burn one as a disposable mule.
⚠ Because the shiny branch RETURNS, `:3368`'s `not is_shiny` is redundant-but-harmless — defensive
depth, not a second policy. Do not "simplify" it away; two independent statements of the same rule
is what makes the rule survive a refactor of either branch.

⭐⭐ **AND THE RECON WAS WRONG ABOUT THIS, CONFIDENTLY** — it filed the absence of a duplicate
filter as a GAP that *"appears to contradict the user's requirement"*. It had the line number right
and the meaning inverted. **That is the whole reason an agent's output is a NOTE and never truth**,
and it is the second time today a recon's *names* were excellent while its *interpretation* was
not.

**Duplicates (the NON-shiny case — still genuinely open):** the HM branch is reported to gate only
on *species ∈ target dex*, *party < 6*, *spare balls > 1* (`:3373-3377`) — **no duplicate filter** —
while the general predicate is `should_catch_for_story` (`:1672`). ⚠ UNVERIFIED and NOT closed by the
shiny finding above, which is a different question. Whether it matters turns on whether the HM
branch can fire for a species we already own — precisely the case the WITHDRAW half now intercepts
first, so it may be moot in practice. **Check before building; do not assume either way.**

---

## ⛔ WHAT THIS NOTE DOES NOT SAY

No design, no recommendation — the standing rule is that agent **architecture advice** is graded
not at all and its **names** graded highly. Established here: the hunt EXISTS; the grounds table is
the narrow part; the index cannot supply tiles.

✅ **CLOSED:** *where does a shiny go during an armed HM hunt?* — the shiny branch runs first and
returns, catching duplicates and overflowing to the PC box. Nothing to build.
⚠ **STILL OPEN:** the NON-shiny duplicate gate, and which ground(s) to add to `TRAINING_GRASS`.

⛔ **THIS SECTION ONCE SAID THE SHINY QUESTION *"must be answered by measurement before anything is
built"* — three paragraphs after the body had answered it.** Appending a resolution is HALF the
edit: when you resolve something, grep the document for every sentence that called it open.
