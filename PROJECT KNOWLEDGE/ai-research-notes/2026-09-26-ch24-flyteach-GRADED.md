# 2026-09-26 — `#26-ch24organic` GAP 3 (TEACH FLY IN PRODUCTION) + THE HAND-OFF CHAIN — GRADED: ALL THREE ARMS AS PREDICTED (re-run on the post-review picker)

> Grades `2026-09-26-ch24-flyteach-PREDICTIONS.md` (committed `e491d8c0` on branch `wt/ch24organic` BEFORE any
> drive). Evidence, committed: `tools/story-dev/evidence/2026-09-26-ch24handoff-{H1-TEACH,H0-NOTEACH,K-KNOWN}.txt`
> (+ `.stdout.txt`) — ⚠ these files are RUN 3 (after the code review's picker fix; addendum `adcae1fb`) — and the VOID
> first run `…-RUN1-VOID-NOBATTLEHOOK-{H1-TEACH,K-KNOWN}.txt`. Fixtures verified:
> `post_league_shop` `1564948368f6`, `post_ch24ready` `cf383b5b2567`. All drives `HARNESS_EXIT_ON_MANUAL=1`.

## ⚠ RUN 1 OF H1 AND K WAS VOID — A DRIVER DEFECT, NOT A PRODUCTION RESULT

The new `--driver ch24handoff` had no `on_battle_started`, so the harness FLED every wild battle
(`BattleListener.run_away_from_battle` ×753 in K's stdout): ~500k frames on ROUTE117, Zigzagoon still L19, 0 EXP.
Production was not involved — the teach itself had already succeeded in H1 (`Swellow learned Fly (lost Peck)`).
Fixed in `8eab44b9` (the hook returns `SwapTrainBattleStrategy`/`StoryItemBattleStrategy` exactly as the proven
`Ch24TrainMode` does), and gated: `probe_ch24_flyteach.py` **F2b** (this driver) and **F5** (EVERY training driver in
the harness must define the hook — 7 today; fault-tested). H0 of run 1 was valid (it never battled) and repeated
identically in run 2.

## CODE REVIEW (adversarial `reviewer`) — KICK-BACK, then fixed

⛔ **The learner/slot rule could strip a flyer's LAST USABLE attack.** `teach_hm_move`'s own rule (0-power first, else
weakest) ignores the battle ban list, and `battle.yml` bans Dig, Solar Beam, Sky Attack, Fake Out, Wrap, Counter …
⇒ [Peck, Dig, Solar Beam, Sky Attack] would lose Peck and keep three moves the bot never clicks. (The review's own
example, Skarmory with three status moves, was actually safe — status goes first — but the hole it pointed at is
real.) Fixed: `_fly_teach_plan` chooses the slot (empty → status → banned → weakest usable only if another usable
remains; a candidate that would end with none is skipped) and hands it to `teach_hm_move` explicitly. Gate F3 now
carries that shape, and the pre-review rule is a fault arm that fails it (3 cases). Risks it named, not fixed:
F5 only sees a DIRECT `train_*` call in a driver class (a private wrapper method would evade it — none exists
today); a derail in the middle of the teach menu is undriven (re-entry short-circuits on `first_pokemon_with_move`).

## RUN 3 (final code) — GRADED — identical verdicts to run 2, plus `fly_replace_slot=0` (Peck) from the new plan

## RUN 2 — GRADED

| arm | prediction | reading | verdict |
|---|---|---|---|
| **H1** HAND-OFF (teach), floor 21 | Swellow learns Fly losing **Peck**; Zigzagoon 19 → ≥21 on a Fly-reached ground; bridge FLIES back; R1 passes; door open | `FLY {'fly_learner': 'Swellow#0B30A747', 'fly_lost': ['Peck'], 'fly_teach': 'taught'}`; `rungs=[{Zigzagoon, ROUTE117, 19→21, finished=True}]`, ended ROUTE117 (31,16); `BRIDGE mode='fly'`; `E1-READY`, `E1-AT-DOOR`; all conjuncts True — `ACCEPTANCE: PASS` | ✅ |
| **H0** CONTROL (`NOFLYTEACH`) | no teach; `no_ground`; never leaves (18,6); R1 refuses `1 mōn below the L21 floor: Zigzagoon#33CB74C3 L19` | `fly_teach='fault_skipped'`; `rungs=[] no_ground=[('Zigzagoon', 19)]`, end `((0, 8), (18, 6))`; the exact refusal; door shut — `ACCEPTANCE: PASS` (expect=refuse) | ✅ **the teach is load-bearing** |
| **K** ALREADY-KNOWN | `fly_teach='already'`; the rest as H1 | `FLY {'fly_teach': 'already', 'fly_knower': 'Swellow#0B30A747'}`; same rung, bridge `fly`, door open — `ACCEPTANCE: PASS` | ✅ |

## WHAT THIS SETTLES
* ✅ **The first organic-shaped §Ch24 hand-off, end to end:** a party that does not know Fly is taught it,
  a below-floor member climbs on a Fly-reached ground, the bot flies back to the League door, R1 passes and the
  door opens — every step production code, in `_play`'s order (pinned by F1/F2).
* ✅ Without the teach (H0) the same party cannot train at all from the plateau and R1 refuses by name.

## WHAT IT DOES NOT SETTLE
* ⚠ Floor 21, one rung, one party (rule 8). The production floor is 65 (a multi-hour, multi-rung climb — the
  ladder itself is proven separately by `--driver ch24train`).
* ⚠ Parties with NO Fly-compatible member (13 of 30 organic parties): `ensure_fly_learner` reports `no_learner`
  and continues — gaps 4 (the no-Fly plateau walk-off) and 5 (flyer acquisition) remain open.
