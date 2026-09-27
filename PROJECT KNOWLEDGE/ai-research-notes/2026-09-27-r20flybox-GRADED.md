# 2026-09-27 — RULING 20 Phase 1, increment B (Fly box-first) + USER RULING 21 (the swap-back): GRADED

> Predictions: `2026-09-27-r20flybox-PREDICTIONS.md` (`30de3936`, committed BEFORE the drives).
> Evidence: `tools/story-dev/evidence/2026-09-27-flybox-{B1-swap,B2-nofly,B3-wrongtile,B4-noswap,B5-ordinary,B6-hmpcfirst-regression}.txt`
> + `.stdout.txt`. Fixtures `post_moveset.ss1` (PINNED, `36e4510e…`) and `fortree_gym_wedge.ss1` (PINNED, `87d390d7…`),
> both asserted. Branch `wt/r20fly`.

## RESULT — all six as predicted

The subjects are production `ensure_fly_learner` and `restore_ch24_fighters`, called in that order from
EVER_GRANDE_CITY (18,6). The PC actions were recorded by (PID, species) when each visit BUILT them. Whether they
EXECUTED is shown by the party and box identity reads, so a built-but-not-run action (B3) cannot pass as a move. The
Machop filler gets a random PID per run.

| Arm | `ensure_fly_learner` PC actions | Fly | After Fly | `restore_ch24_fighters` | Verdict |
|---|---|---|---|---|---|
| **B1** swap | **[deposit Zigzagoon 33CB74C3, withdraw Swellow 0B30A747]** (in the lobby) | taught | back on (18,6); swap recorded: carrier Swellow, boxed Zigzagoon, fighters = the injected six | **[deposit Swellow, withdraw Zigzagoon]**; `F-RESTORED`; the party = the six fighters; Swellow boxed; standing on LEAGUE_1F (6,2) | **PASS** |
| **B2** nofly (`NOFLYBOX`) | none | `no_learner` | (18,6); Swellow still boxed; nothing recorded | — | **PASS** |
| **B3** wrongtile (`LOBBYSTAND`) | built, NOT executed: the walk to (10,2) failed (`Could not find a path … to (10/2 @ …LEAGUE_1F)`, verdict `error`) | `no_learner` | back on (18,6); Swellow still boxed; nothing recorded | — | **PASS** |
| **B4** noswap (`NOSWAPBACK` on the restore) | as B1 | taught | as B1 | none; **refused by name**: "§Ch24 RULING 21: the party is not the six recorded fighters…" | **PASS** |
| **B5** ordinary | none | taught from the party | (18,6); nothing recorded | `none_needed` | **PASS** |
| **B6** regression `hmpcfirst` (default) | its own | — | — | — | **PASS**, all six readings |

## What this proves, and what it does not

- ⭐ **Box-first is what collects the Fly learner.** B1 and B2 start from the same injected state; only the production arm
  differs.
- ⭐ **The per-map stand tile is what makes the lobby withdraw work.** B3 walks into the same lobby with the table ignored:
  (10,2) has no path (a guard stands there), and nothing moves.
- ⭐ **RULING 21's identity check is live.** B4 skips the swap and the check refuses. B1 swaps and the party is the six
  recorded fighters by (PID, species).
- The ordinary path is unchanged (B5: no lobby, nothing recorded). The generic PC-first path still works with every PC
  walk going through `pc_stand_for` (B6).
- **Not shown:**
  - §Ch24 end to end: the carrier's exclusion from training and R1's head-count are gated (pure / AST) but not driven,
    and the swap-back runs inside the real `prepare_and_open_the_league` only by wiring (AST-gated);
  - a boxed Fly KNOWER live (gated with stubs only);
  - the walk OUT of the lobby failing after a landed withdraw. The swap is recorded (gated), the teach still runs
    (the bag works indoors) and the report keeps `fly_box.ok=False`, but training would then start indoors;
  - frequency. One trajectory per arm.

## After the review (2026-09-27): two fixes, two arms re-run

The adversarial review kicked the item back:
- a silent `except` broke the silent-except ratchet;
- the swap record was written after the walk out of the lobby, so a raise there would lose it.

Both were fixed. The record is now written inside the lobby errand, and gate F5 plus a new fault arm cover it. The two arms that run the changed code were re-run on the fixed code, and both PASS:
- B1 swap: [deposit Zigzagoon, withdraw Swellow], then [deposit Swellow, withdraw Zigzagoon];
- B3 wrongtile: `no_learner`.

Evidence: `…-flybox-B1-swap-rerun.txt`, `…-flybox-B3-wrongtile-rerun.txt` (+ `.stdout.txt`).
