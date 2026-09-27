# 2026-09-27 — RULING 20 Phase 0: the pre-gym-1 per-species catch-attempt cap — RECON (a NOTE, not truth)

> ⚠ **AI RESEARCH NOTE — NOT A SOURCE OF TRUTH.** Four read-only Claude agents took four angles: our code, batch data,
> Gen 3 mechanics from the decomp, and an adversarial agent. Nothing was driven. The load-bearing numbers are log counts
> an agent made with scratch scripts; they were not re-derived by a second instrument unless stated. The decision this
> fed is in `06-DECISIONS-LOG.md` (2026-09-27).

## THE QUESTION

The RULING 20 plan (`2026-09-26-rulings19-20-PLAN.md`) lists for Phase 0: "the per-species attempt cap and health
check before gym 1 too". It gives no value. What should it be?

## THE ANSWER — at today's pre-gym-1 target of 4, no cap value changes anything worth changing

| Cap (attempts per species per run, pre-gym-1) | 38-run batch (140 attempts) | 872-run H corpus (3,196 attempts) | early P batch (352) |
|---|---|---|---|
| 1 | cuts 4 attempts; **2 catches lost** | cuts 146; **126 catches lost**; 2 whiteouts avoided | cuts 16; 15 catches lost |
| 2 | **nothing** | 3 attempts (all Abra #3); 2 catches lost | nothing |
| 3 | nothing | nothing | nothing |

- **Retries are rare by construction.** The team target of 4 ends pre-gym-1 catching (`story_mode.py`, the pre-gym-1
  branch of `decide_dex_catch`); 932 of 933 badge-1 runs had exactly 4 battlers.
- **Almost every second attempt followed our own ball supply running out, not the species.** The run starts with 5
  Poké Balls plus 1 Great Ball, and restocks only at Rustboro.
- ⇒ A cap is near-inert until Phase 2 raises or removes the target of 4. **An A/B of it now would show "no difference"
  by construction**, and would read as a result.

## THE HEALTH CHECK — the full-HP form is harmful; the risk lives inside one battle

- **A full-HP entry check** (the post-gym-1 `party_healthy`) would refuse 79% of pre-gym-1 catches: 111 of 140 in the
  batch, and about 4,144 of 5,230 across the corpus. It shows no measured benefit either: whiteouts ran at 0.55% whether
  or not the party entered at full HP.
- **What actually kills is the catch battle itself.** In the H corpus, 19 catch battles ended `Lost` (15 distinct after
  removing replays). 16 of those 19 were Whismur using Uproar while the plain catch strategy kept throwing and sending
  the next mon (`catch.py`: `should_flee_after_faint` is False).
- **The effective form is an in-battle bail on the first faint.** It would have turned 13 of the 19 H losses into
  flees, at a cost of about 1.6% of catches.
  - It cannot help a one-mon party, where the first faint IS the whiteout.
  - The existing post-gym-1 bail class cannot be reused before gym 1: its 10-ball reserve rule would flee on turn 0,
    since 89 of 140 attempts started with 10 balls or fewer.
- **The current batch had 0 losses in 140 attempts.** At the H rate that outcome has a probability of about 0.43, so
  the risk is not shown to be gone.

## OTHER FINDINGS

- ✅ **FIXED 2026-09-27: a defect in the POST-gym-1 catch-rate skip.** `_expected_throws_for` scored the BEST ball held,
  whatever its quantity, so one Great Ball made a rate-60 catch read 8.1 throws (admitted). The thrower spends that ball
  and continues with Poké Balls; the whole sequence averages about 11.8, above the cap.
  - Now `dex_catch_expected_throws_seq` walks the bag best-first.
  - Gate `probe_dexcatch_rate.py` R7 checks it, with the shipped adapter as a fault arm.
- **The attempt counter is shared across the badge boundary.** `_dex_catch_attempts` increments before gym 1 too, so a
  pre-gym-1 failure already spends one of the two post-gym-1 attempts. Two measured cases: Silcoon and Poochyena. Any
  Phase 2 cap must decide this on purpose, and must never add a second counter at the same increment site.
- **Ball supply before gym 1:**
  - 6 balls before Rustboro: 5 from the rival, 1 Great Ball in Petalburg Woods.
  - Earlier marts (Oldale, Petalburg) sell balls, but the bot buys only at Rustboro, at 1 ball or fewer during the Route
    116 spin (`early_game.py`).
  - 18 of 38 runs ran out of balls once pre-gym-1.
- **Pre-gym-1 saves, verified by loading them 2026-09-27 (unpinned):**
  - `oldale.ss1`: ROUTE101, Mudkip L8.
  - `route103.ss1`: ROUTE103, Mudkip L6.
  - `rustboro.ss1`: RUSTBORO_CITY, Mudkip L13, a party of one.

## CONSTRAINTS A PHASE-2 CAP MUST SATISFY (the adversarial angle)

1. **Place it correctly.** It belongs inside the pure `decide_dex_catch`, after the wild, shiny, Pokédex, owned and
   in-party checks. It must never go in `StoryCatchStrategy`, which shinies, the HM and counter hunts and the tutorial
   share.
2. **Keep it ≥ 2.** A cap of 1 refuses the "out of balls, then caught on retry" path (134 cases).
3. **Never strand the Route 116 team-catch loop.** It needs a logged "nothing admissible left" exit, or a rule never to
   refuse the last available species.
4. **Never count what shouldn't count.** Exclude the Wally tutorial, which fakes `Caught`, a party swap and ball changes,
   and attempts that ended because our own balls ran out.
5. **Log it in `06` as a NARROWING** of the 2026-07-31 ruling ("catch every unseen species except when doing so would
   block progress").
6. **Keep per-run state in `reset_per_run_state`.**
