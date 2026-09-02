---
name: staleness-sweep
description: Run after ANY status change (a leg/chapter/item ships, a gate turns green, a blocker clears) and before the commit that announces it. Finds sentences the change just made false, across the whole PROJECT KNOWLEDGE tree, by MEANING rather than by exact wording. Use whenever you are about to write "X is done".
---

# staleness-sweep — find what your status change just made false

⛔ **The premise: you cannot recall every sentence that asserts the old status, because you did not
write them all, and the ones you did write you paraphrased.** One status change in this repo left
**eight** stale claims across **three** files. Two independent reviewers and three literal greps were
needed to clear them.

## THE TWO FAILURES THIS SKILL EXISTS TO PREVENT

1. ⛔ **A LITERAL-STRING GREP PROVES THE ABSENCE OF A SPELLING, NOT OF A CLAIM.** A sweep for
   `"NOT wired into"`, `"does NOT exist yet"`, `"no orchestrator"` returned **0 survivors** while the
   handoff's **first sentence** read *"what is LEFT is the `_play()` WIRING"*. Same claim, different
   words.
2. ⛔ **THE PAIR CHECKS ARE SCOPED TO TWO FILES.** P1–P5 name `04-HANDOFF.md` and
   `03-PUNCH-LIST.md`, so a reviewer doing exactly what was asked never opens
   `12-STORYMODE-DESIGN.md` — where an eighth stale claim sat. **The enumeration is the reviewer's
   scope; the sweep is yours.**

## THE PROCEDURE

**Step 1 — name the TOPIC words and the STALENESS cues.**
Topic = what changed (`wiring|orchestrator|_play\(\)`, or `leg 5`, or the item slug).
Cues = how a doc says "not yet":
`is LEFT | what remains | remains | still not | not yet | does not exist | missing | outstanding |
to build | NOT built | NOT wired | TO WIRE | pending | blocked on`

**Step 2 — proximity search, not exact match, over EVERY `PROJECT KNOWLEDGE/*.md`.**

```python
import pathlib, re
NEAR = re.compile(r"(<TOPIC ALTERNATION>)", re.I)
CUE  = re.compile(r"\b(is LEFT|what remains|still not|not yet|does not exist|NOT wired|NOT built|TO WIRE|outstanding|pending)\b", re.I)
MARKED = ("superseded", "formerly", "historical", "this clause read", "used to read",
          "this sentence read", "when this cell was written", "gone stale")
for f in sorted(pathlib.Path("PROJECT KNOWLEDGE").glob("*.md")):
    t = f.read_text(encoding="utf-8")
    for m in NEAR.finditer(t):
        w = t[max(0, m.start()-240): m.end()+160].replace("\n", " ")
        if CUE.search(w) and not any(k in w.lower() for k in MARKED):
            print(f"!! {f.name}: …{w[-240:]}…")
```

**Step 3 — judge every hit by hand.** A hit is OK only if it is explicitly marked historical.
⛔ Do NOT auto-fix; several hits will be legitimate (other subsystems, or your own new negated
sentence like "nothing about X remains").

**Step 4 — fix by MARKING, never by deleting.** Replace the claim and keep the old wording in a
`*(This sentence read "…" until <date>.)*` parenthetical. Deleting loses the audit trail, and this
project's rule is summarise-and-point, never delete.

**Step 5 — re-run the sweep to zero, then Tier 0.**

## ⛔ HARD RULES

- **NEVER length-filter or truncate a grep you use to conclude "none remain."** `awk 'length<N'`,
  `cut -c1-N`, `head` per line — all are for READING, never for PROVING. This repo stores state in
  single ~20KB lines (the handoff banner, the `#24-remainingarc` cell), and a width filter is blind
  to exactly those. *A stale count shipped this way once.*
- **Check the FIRST SENTENCE of the banner and of the "60-SECOND VERSION" block explicitly.** They
  are what a cold reader acts on, and they have gone stale three times each.
- **Check the item's own punch-list cell OPENING**, not just somewhere in the cell. A live status
  buried 3,000 words into a mega-cell is invisible.
- **A note that predicts its own staleness does not prevent it.** One clause here carried the
  warning "when the next thing ships, THIS SENTENCE is the one to grep for first" — written one
  commit earlier by the same person who then missed it. Only the sweep works.
