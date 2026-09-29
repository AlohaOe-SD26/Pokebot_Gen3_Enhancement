# 2026-09-28 — `#27-enroutejoin` GRADED: a catch can no longer join the party while a hunt WALKS to its ground — reproduced live, then fixed

> Predictions: `2026-09-28-enroutejoin-PREDICTIONS.md` (`780e151a`, before the fix), with the addendum for the live
> walk-battle arms (`3a3728df`, before they ran). Fix: `409b5dda`. Driver instrument fix: `3b8962e5`. Every arm used
> `random.seed(1)`. Evidence: `tools/story-dev/evidence/2026-09-28-enroutejoin-*.txt`.

## RESULTS

| Arm | Code, env | Reading | Verdict |
|---|---|---|---|
| **H-FAULT-ON** (skip-the-fix) | `OPENFENCE=1` + `FAULT_NOWALK=1`, `healed101` | the walk's first battle, **Wurmple at f2977204: `phase=walk strategy=StoryDexCatchStrategy fence='dex catch #265 (joins the party)'`**; `walk_joins ['Wurmple#6E8805CD']`, party 5 → **6**; **`spin_battles 0`**; exit **`BotModeError: Hunted for a Surf learner but never caught one (timeout/balls).`** | ✅ **THE BUG, LIVE** (the audit's site A) |
| **H-FIX-ON** | `OPENFENCE=1`, `healed101` | the same battle, same frame: **`fence='a hunt is walking to its ground — …'`**, no catch; a Zigzagoon walk battle (f2978683) is refused the same way; `walk_joins []`; the hunt spins 8 battles and catches its Zigzagoon: `exit slot 5` | ✅ |
| **H-OFF** | nothing set, `healed101` | both walk battles refused as "runway"; the same battle frames and the same hunt outcome as H-FIX-ON | ✅ |
| H-*r (replays) | the `(PID, species)` instrument | 0 differing battle rows against the first runs; `party_after_walk` 5 / 6 / 5 | ✅ determinism check, true counts |
| **G-FIX-ON / G-FAULT-ON / G-FIX-OFF** | `healedindoor` | verdicts identical to their M2 twins (0 walk battles, 1 spin battle, `exit slot 5`); **`walk_marker [True] / [False] / [True]`** | ✅ the ordinary hunt is unchanged; the marker is live on the real walk |
| **G-LONG-ON** | `storyresume`, `OPENFENCE=1`, 480,000 frames | **623 of 624 event lines frame-identical to M3-ON-s1**, through `[MODE] Story -> Manual` at f539264 | ⚠ MISS on the literal prediction (below) |

Reading H-FAULT-ON against H-FIX-ON: the two arms are identical up to the one battle whose verdict the marker decides.
There the skip-the-fix arm catches, the party fills, and the hunt derails exactly as the audit traced (`early_game.py`:
the entry-time `party_count`, then `len(party) > before` stops the spin on its first frame). The fix refuses that battle
and the hunt succeeds.

## THE MISSES (disclosed)

1. **"Walk battles are rare"** was my inference from `_navigate_riding_out(..., avoid_encounters=True)`, and it shaped
   the first predictions ("no live arm here can show a walk battle being refused"). The batch-log count refuted it:
   81–90% of 84 real hunts met one (`2026-09-28-enroutejoin-FREQUENCY.md`, a NOTE). The pre-registered `healed101` arms
   then showed one live.
2. **"The heal deposits one member (5 → 4)"**, stated in the predictions' measurement section, is FALSE. The driver
   keyed its party snapshot by PID, and this fixture's Shedinja carries its Ninjask's PID (KI-78), so a party of 5 read
   as 4. The fence's own reading ("party is 5/6") was right. The instrument was fixed (`3b8962e5`), the H arms were
   replayed identically with true counts, and the M/G evidence files carry a warning line.
3. **G-LONG-ON:** the prediction said every `[STEP]` line frame for frame. All lines match through the story's hand-off
   to Manual at f539264. The harness's next line, `'Bot stopped: …'`, came 13 frames later (f539278 against f539265),
   and so did every stuck-dump after it. That line is emitted after `StoryMode` has left the controller stack, so it is
   outside the code under test. The cause was not isolated: M3 ran from the main checkout's harness and G-LONG-ON from
   the worktree's.

## WHAT THIS PROVES

- **The mechanism, end to end, live:**
  - with the marker off, a walk catch fills the party and the HM hunt derails;
  - with it on, the same battle is refused and the hunt succeeds.
- **Flag OFF is untouched.** Its walk refusals stay "runway", and the gate's O12o case covers it.
- **The ordinary HM hunt and the ordinary long story replay unchanged** (the G arms).

## WHAT THIS DOES NOT SHOW

- **The counter hunt's walk, live** (the audit's site B). Its two walk calls are wrapped (gate A1, AST) and share the
  marker the HM hunt proves live, but no drive walked a counter hunt through an admissible battle.
- **How often this would have cost a run.** That is the Phase 3 batch. The count says ~21–26% of hunts meet the
  triggering case.
- **The withdraw re-picks** (audit site C) are unchanged. Their walks cross no land encounters.
