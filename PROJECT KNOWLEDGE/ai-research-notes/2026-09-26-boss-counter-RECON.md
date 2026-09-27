# 2026-09-26 — Why organic runs die at WINONA (and Flannery): a 4-angle recon — a NOTE, not truth

> ⚠ **AI RESEARCH NOTE — NOT A SOURCE OF TRUTH.** Four read-only Claude agents (an audit of our counter pipeline and the
> rulings; log forensics of the live batch `#26-batch0926`; decomp + encounter data; an adversarial pass on the obvious
> fixes). Nothing was driven. Damage numbers are hand-calculated (IV assumptions), NOT measured. Line refs are the
> agents'; the load-bearing code claim (§3) was re-read by me.

## 1. The measured shape (4 Winona deaths + 1 Flannery death, interim batch)
* **The wall is SKARMORY** (Steel/Flying): on the field for ~66% of our faints (309 of 467). Decomp: only **Fire and
  Electric** are super-effective on it; Rock and Ice are 1×, Dragon 0.5×; Fire/Electric are special and hit its low
  SpDef (70) instead of its 140 Def. ⇒ the bot's needed types for Winona — **Rock/Ice/Dragon, derived from the ace
  Altaria alone** (`story_mode.py` `winona_fight["ace_types"]`) — do not answer the mon that beats us.
* **The hunted counter never did the winning work.** Untrained counters (Slugma L15) led **21 fights and won 0**; each
  fainted to the first foe. Withdrawing it deposited a working mon (Castform, whose Powder Snow had hurt Skarmory, in one
  run; Shedinja in another). A counter with a "credible" move also delays the honest stop to the 12-loss hard plateau —
  ~6 extra losses, each halving the wallet.
* **What the WINNERS had:** a strong special or Fire move on a TRAINED battler — Blaziken's Blaze Kick (one-shots
  Skarmory), Combusken's Ember, or **Surf on a trained team Linoone/Swampert** (111-142 damage to Skarmory). **All four
  deaths taught Surf to a freshly caught L3/L11 Zigzagoon HM carrier** (one dealt ~6 HP to Skarmory in 18 turns).
* **Not a level problem:** the dying teams were L37-43 vs Winona's L29-33; free levels from 24 fights did not move the KO
  count (3 every time). Nothing trains the party during the loop anyway (Winona's config has no grass: "no training grass
  here"; maintenance fixated on the L3 HM carrier).
* **Supply:** 2 of 4 deaths could not hunt at all (0-3 Poké Balls).
* By starter line this batch: Mudkip 5/5, Torchic 3/4, Treecko 1/4 beat Winona.

## 2. The bot ALREADY OWNS an answer it never uses
By Fortree the bot always holds **TM50 Overheat** (Flannery, badge 4) and **TM34 Shock Wave** (Wattson, badge 3).
Overheat learners: Combusken/Blaziken, Loudred/Exploud, Numel, Slugma, Torkoal (computed 66-134% of Skarmory at L30).
Shock Wave learners include Zigzagoon/Linoone, Loudred, Castform, Wingull/Pelipper (weaker: 20-35%). The counter
planner considers LEVEL-UP moves only — never TMs.

## 3. A real defect, but NOT the fix (verified by me)
`counter_hunt.train_counter` returns early for any boss config without `"grass"` (`counter_hunt.py:689-694`) — Flannery,
Winona, Tate & Liza, Juan — although `counter_training_ground` (KI-44) no longer needs the boss's grass; and `:705`
reads `cfg["grass"]`, so deleting the gate alone would raise. ⚠ The adversarial pass argues fixing it would NOT save
Winona runs (a trained L27 Slugma still loses to Skarmory/Altaria on the numbers) and could HURT Flannery (the untrained
Numel already converts 2 of 3; training there means leaving Lavaridge by a measured-FAIL route). ⇒ record, do not build
blind.

## 4. Candidate levers (ranked by the evidence; each needs a USER decision unless marked)
1. **Teach an owned Fire/Electric TM (Overheat / Shock Wave) to a battler that can learn it** before a gym it keeps
   losing — the cheapest reliable Skarmory answer; no hunt, no balls, no deposit. (No ruling covers TM teaching for gyms;
   the §Ch24 teach machinery exists.)
2. **Put Surf on a trained battler that can learn it, not only on a fresh HM carrier** — the Treecko wins had exactly
   this. (Touches HM-carrier policy; the 2026-09-25 HM directive is about the SEARCH, not who carries.)
3. **Never deposit a mon that already answers the boss** in the counter withdraw (`pc_trip` make-room picks the lowest
   level). No ruling found; small.
4. **Look in the box for an existing answer before hunting** (`box_counter_pid` excludes boxed PIDs).
5. The Juan honest stop — 7 of 9 runs that reached Juan beat him with no Dragon ⇒ the "grinding will not fix this" premise
   is refuted in this batch (touches the 2026-07-30 honest-stop ruling — the user's call).

## 5. Side findings (small, recorded)
* Log text contradicts events: "counter hunt failed" after a successful catch; "found nothing in 120000 frames" after 28
  Slugma encounters (it threw all 3 balls at the first); "goes in untrained" while maintenance trained it.
* `probe_counter_candidates_offline.py`'s positive control fails as shipped (FIERY_PATH gained an `AREA_PREREQ`).
* `early_game.py` says Castform is "politely declined" with a full party; the decomp's `givemon` sends it to the PC.
* Every first leader attempt started with 1-3 members at 0 HP (no heal between the gym trainers and the leader) — in
  winners too.
