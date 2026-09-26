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
shiny encounters. That is very probably the *desired* behaviour.

⚠ **BUT THE CONSEQUENCE IS UNVERIFIED AND IT MATTERS:** I have **not** checked that any other
branch actually catches that shiny. If none does, a shiny encountered mid-HM-hunt is silently
skipped — which WOULD violate the user's *"not duplicates unless shiny"*. ⇒ **first task of the
catch half: prove where a shiny goes during an armed HM hunt.** Do not assume either answer.

**Duplicates:** the HM branch is reported to gate only on *species ∈ target dex*, *party < 6*, and
*spare balls > 1* (`:3373-3377`) — **no duplicate filter**. The reported general predicate is
`should_catch_for_story` (`:1672`). ⚠ Whether the absence matters depends on whether the HM branch
can fire on a species we already own, which is exactly the case the WITHDRAW half now intercepts —
so this may already be moot. **Check, do not assume.**

---

## ⛔ WHAT THIS NOTE DOES NOT SAY

No design, no recommendation — the standing rule is that agent **architecture advice** is graded
not at all and its **names** graded highly. Established here: the hunt exists, the grounds table is
the narrow part, the index cannot supply tiles, and there is one genuinely open question (where a
shiny goes during an armed hunt) that must be answered by measurement before anything is built.
