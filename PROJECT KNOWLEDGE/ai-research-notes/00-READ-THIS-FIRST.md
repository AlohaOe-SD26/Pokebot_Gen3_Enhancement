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
