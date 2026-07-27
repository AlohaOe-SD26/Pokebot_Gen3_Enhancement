# 2026-07-26 research sweep — index

Five topics, each covered TWICE: a Gemini note (recall, broad) and a Claude agent
(verification against the decomp + our codebase). Gemini notes are `*.gemini.md` here;
the Claude findings are folded into the PROJECT KNOWLEDGE docs directly.

| topic | gemini note | verified by |
|-------|-------------|-------------|
| Pokémon PC / boxes | `T1-pc-boxes.gemini.md` | Claude agent — `pc_interaction.py` audit + decomp box rules |
| Ground + hidden items | `T2-items.gemini.md` | Claude agent — per-map item-ball table + full-pocket hazard |
| Healing items | `T3-healing.gemini.md` | Claude agent — `src/data/items.h` prices/amounts + our mart machinery |
| Shops / heal points | `T4-stores.gemini.md` | Claude agent — settlement table + League 1F + exposure analysis |
| Team development | `T5-teams.gemini.md` | Claude agent — design against `19-TEAM-BUILDING-DISCUSSION.md` |

## ‼ First contradiction already spotted, before any verification

`T5-teams.gemini.md` closes by recommending a **"concentrated, over-levelled core of 4
rather than a weak, spread-out team of 6"**. That is the opposite of what this project is
trying to build — the user's explicit goal is MORE varied and diverse teams across runs
(`19-TEAM-BUILDING-DISCUSSION.md` §2, §5). It is also a textbook example of the documented
failure mode: Gemini's *architecture advice* is the part that hallucinates, while its
*names and numbers* are usually good.

Take the item names, level bands and mechanics from these notes. Do not take their strategy.
