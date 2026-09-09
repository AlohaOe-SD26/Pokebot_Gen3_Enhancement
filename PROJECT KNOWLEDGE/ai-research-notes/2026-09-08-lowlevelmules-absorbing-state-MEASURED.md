# `#24-lowlevelmules` — the mechanism is an ABSORBING STATE in gym prep, not "mules are caught late"

**2026-09-08.** Recon round for the measured #1 blocker (16 of 49 runs; 16 of the 18 that reach §Ch23).
Every claim below carries its own verification status. ⛔ Per `00-READ-THIS-FIRST.md` a note never
outranks an authoritative doc — but the ✅ VERIFIED items here were checked **against our own code and
our own ROM-derived data**, not recalled, and each names the exact command or file:line that settles it.

---

## ✅ VERIFIED — the root cause, and it is not what the item's title says

`plugins/custom_modes/story_mode.py:2119-2121`, inside `_prepare_for_fight`:

```python
catchup  = target - self.TRAIN_CATCHUP_GAP     # TRAIN_CATCHUP_GAP = 6   (story_mode.py:1136)
to_train = {i for i in battlers if party[i].level >= catchup}
to_train.add(strongest)
```
with `target = random.randint(lo, hi)` drawn from that fight's `cfg["band"]` (`story_mode.py:1945`).
Its own comment states the intent: *"Fresh far-below catches are left to level organically (#24-team)."*

⭐⭐ **THIS IS AN ABSORBING STATE.** A battler more than 6 levels below the fight band is excluded from
training, therefore gains nothing, therefore is *further* below the next (higher) band, therefore is
excluded again — permanently. Nothing in the codebase pulls it back.

**Already measured in-repo, before this round** — `modules/story/team_policy.py:11-14`: a Makuhita was
carried **from L8 to L9 across FIVE badges** while the rest of the team went L22 → L42. That is the
absorbing state, observed, with the mechanism unattributed at the time.

⇒ **The HM mule is not a special case. It is the most FREQUENT victim of a general trap**, because
`ensure_hm_learner` introduces a fresh low-level mon mid-game by design.

## ✅ MEASURED — what §Ch23 actually sees

Parsed party snapshots from `x4-runs/20260907-203713`, restricted to the 18 runs that reached §Ch23,
using the code's OWN battler predicate (`BENCH_SPECIES = ("Zigzagoon","Linoone","Castform")`,
`victory_road.py:503`) rather than an invented one:

```
lowest battler — median L13, min L12, max L23        party max — L49 to L59
runs clearing L35 on EVERY battler: 0 / 18
species that ARE the lowest battler:
    Marill 9,  Slugma 2,  Abra 2,  Shedinja 1,  Ninjask 1,  Mightyena 1, Kadabra 1, Poochyena 1
```
⇒ a **35-45 level gap** inside a single party, and **Marill is the lowest battler in exactly half the
runs** — matching the independent refusal count (Marill is the refused mon in 9 of 16).
⇒ The other half are Abra/Kadabra/Slugma/Ninjask/Shedinja — **late catches, not HM mules.** Any fix
scoped only to HM carriers addresses at most half the population.

## ✅ VERIFIED — Route 104 Marill (this retires the item's own ⚠ HYPOTHESIS marker)

`03-PUNCH-LIST.md` carried *"⚠ HYPOTHESIS — its encounter data is UNVERIFIED; check before building."*
**Checked, from our own ROM-derived cache** `sandbox-pokebot/cache/encounter_index_BPEE0.json`:

> **Route 104, Grass, Marill — 20% of encounters, levels 4-5.**

⛔⛔ **AND A TRAP THAT NEARLY CORRUPTED THIS WHOLE ROUND — READ THIS BEFORE USING THAT CACHE.**
Its keys are **INTERNAL species indices, NOT National Dex numbers**, and `modules/data/species.json`
is a **LIST indexed by exactly those**. Mapping them as national dex produces confident nonsense —
"Sealeo and Aggron in Petalburg Woods at L5-6", "Breloom on Route 101 at 45%". Evolved forms on
starter routes is how the bug announces itself.
⭐ Correct usage: `species.json[internal_index]["name"]`. Proof it is right: `rows[286]=Poochyena`,
`rows[290]=Wurmple`, `rows[304]=Taillow`, `rows[309]=Wingull` — precisely Emerald's real Route 104.
‼ **Indices ≤ 251 are IDENTICAL under both schemes**, so Marill (183) looked correct under the WRONG
mapping too. **A spot-check that lands on a Gen-1/2 species proves nothing about the mapping.**
⛔ Second trap in the same data: learnsets store **MOVE IDs**, not names (`tm_hm: [264, 352, ...]`).
A string search for `"Surf"` returns **zero** hits, which is indistinguishable from a real absence.
Resolve names → ids via `moves.json` first.

**Corrected result** — early-game grass species vs the HMs the bot catches mules for:
```
Marill      Route 104   20%  L4-5   learns Dive, Rock Smash, Strength, Surf, Waterfall
Zigzagoon   Rt 101/2/3  10-20%      learns Cut, Rock Smash, Surf
Poochyena   many        28-60%      learns Rock Smash
```
Marill is the ONLY early-grass species covering all three mule HMs — which also explains why
`BENCH_SPECIES` contains Zigzagoon: it covers two of them and is today's most common stand-in.

## ⛔ REFUTED — "acquire a Marill at §Ch3 so it is never a mule" (my proposal; killed by review)

The acquisition half is sound; the half that does the work is not. Ranked, each verified in code:

1. **It walks into the same absorbing state.** A L4-5 Marill is already below Gym 1's catchup line
   (band 13-17 ⇒ catchup 7-11 — marginal at best, and below it after one gym). "Caught at team level
   ⇒ grows with the team" is the premise `catch_starter_team` ALREADY operates under, and 78.9-86.9%
   of runs still end up carrying a mon 15+ levels down.
2. **Route 104 is not a usable ground.** `modules/story/training_areas.py:57-58` lists it in
   **`PENDING_GRASS`** with spin tile `None` — *"Level ranges known, spin tile still to be MAPPED."*
   `_hm_hunting_grounds` iterates `TRAINING_GRASS` and skips `tile is None` (`early_game.py:4449-4454`).
   A live two-way sweep has never been done, and the Route 114 precedent (`training_areas.py:36-40`)
   demoted a tile that passed a same-map check but failed reachability from a real story anchor.
3. ⛔ **Marill can NEVER carry the land HMs anyway.** `pick_land_hm_slot` (`early_game.py:4416-4417`)
   skips any species that can learn Waterfall — *"leave its slots alone"*. Marill learns Waterfall, so
   it is structurally ineligible for Strength/Rock Smash. **My "covers all three" reasoning was wrong
   at the code level**, and the file says so.
4. **No ball supply at §Ch3.** `provision_poke_balls` defaults to `RUSTBORO_MART`, reachable only in
   §Ch4; the catch gate bails at `balls <= 1`. `#24-ballstarve` is still open.
5. **It would be the first mon boxed.** Until it holds an HM, `_only_hm_carrier` returns empty ⇒ no
   deposit exemption (`team_policy.py:147-149`), and `find_dead_weight` sorts worst-first by lowest
   level. ⇒ the mon acquired to prevent a mule is the one boxed to make room for one.
6. **On Mudkip runs it carries nothing.** `hm_learner_slot` ranks by LEVEL (`early_game.py:4329`) and
   the Mudkip line learns all five HMs, so the starter wins Surf and the slot is a passenger.

⭐ Keeping this refutation is the point: it is a *documented dead end*, not a gap.

## ⚠ OPEN, UNREFUTED, PRE-REGISTERED — "the earlier refutation used the wrong bar"

`08-MISTAKES.md` records catch-time training as landing **7-10 levels short**, priced as
`L13 + ~15 = L28` against the **§Ch23 bar of L35**. ⭐ But §Ch23 is ~11 chapters later. The mon does
not need L35 *at catch time* — it needs only to clear the **NEXT fight's catchup line**, after which
`to_train` includes it and every subsequent prep carries it.

Surf is caught around §Ch12c (after Norman, band 27-31); the next fight is **Winona, band (29,33)**
(`story_mode.py:3753`):
```
caught L13                 ⇒ catchup = target-6 = 23..27  ⇒ 13 < 23   ⛔ excluded  (today)
catch-time trained to L28  ⇒                                28 >= 27  ✅ included  (every draw)
```
⇒ **PRE-REGISTERED PREDICTION:** training the freshly caught HM carrier to `(next band lo) - 6 + 2`
at catch time re-enters it into `to_train` permanently, and it reaches §Ch23 at team level.

⛔ **NOT YET BUILT, AND EXPLICITLY NOT YET BELIEVED.** It is under adversarial review. Known hazards
that must be answered first:
* `train_team(slots={i})` with `i != 0` is **KI-84-broken** (one spin-batch, then returns as if
  finished — `victory_road.py:1970-1979`). Any catch-time training MUST use the proven
  rotate-to-slot-0-then-`slots={0}` workaround and assert by PID.
* The sufficiency gate (`story_mode.py:1949-1961`) can skip prep training entirely.
* `MAX_PREP_TRAINING_FRAMES` / `estimate_frames_to_level` may reject the top-up.
* Band-to-band deltas must be ≤ 6 for the mon to STAY inside the gate after re-entering.

## Method notes — two instruments failed in this round and both are recorded

* **A trajectory measurement returned "Swellow gained −19 levels".** Physically impossible ⇒ the
  instrument, not the data. Cause: one lane log holds MULTIPLE SEQUENTIAL RUNS, so the "last snapshot"
  came from a later restarted run. The table was discarded, not reported.
  ⇒ **when parsing lane logs, segment by RUN boundary; a log file is not a run.**
* The two `species.json` / encounter-index traps above.

⭐ Both were caught by *the result being impossible*, not by review. Keep asking "could this number
exist?" before "what does this number mean?"
