# THE 2026-09-15/16 ENDLESS-RESET BATCH — 99 RUNS REVIEWED

> ⛔⛔ **RETRACTION STUB — ADDED 2026-09-16 (later). §1'S HEADLINE AND §NEXT-STEPS ITEM 2 ARE REFUTED BY THIS SAME CORPUS.** “30% OF RUNS REACH THE LEAGUE'S DOORSTEP” and “30% of runs already reach the door” both read the **EVER GRANDE CITY** milestone as the League apron. It is not: that is the OUTDOOR map, reached by surfing in from ROUTE 128 on the Poké Center side. The apron lies beyond **VICTORY ROAD**, and **0 of 99 runs ever entered Victory Road** — the cumulative row that implied otherwise was an ASSUMED-ORDER ROLL-UP, not a measurement. See `03-PUNCH-LIST.md` `#26-victoryroadgap` and `07-CHANGELOG.md` 2026-09-16 (eighth). ‼ The rest of this note — the derail families, the frame/level statistics, §3's self-correction — is unaffected.
>
> *(Nothing below is edited: this file is a dated NOTE, and the project's rule is that the authoritative doc gets a stub pointing forward, never a silent rewrite.)*

> ⚠ **NOTE, not truth** — `ai-research-notes/00-READ-THIS-FIRST.md` governs. ‼ **BUT THIS ONE IS
> UNUSUAL: every number below is a MEASUREMENT I made myself with a committed, fault-tested
> instrument** (`tools/story-dev/analyze_endless_batch.py`, `--self-test` = 5 arms, exit 0), not an
> agent's recall. Re-derive any figure with the commands quoted beside it.

**Corpus:** 99 runs, 4 lanes, **338,516,331 frames (~1,567 emulated hours)**, 07:26 on 2026-09-15 →
06:16 on 2026-09-16, `--build sandbox` by construction (the lanes invoke `sandbox-pokebot/pokebot.py`).
Logs: `sandbox-pokebot/profiles/endless-P*/debug-logs/Old/*2026091[56]*.log`.
⛔ **NOT an `x4_headless` batch** — no `x4-runs/<stamp>/`, no MANIFEST, `--resummarise` does not apply.

    PYTHONUTF8=1 py -3.12 tools/story-dev/analyze_endless_batch.py

---

## 1. THE HEADLINE: 30% OF RUNS REACH THE LEAGUE'S DOORSTEP ⛔⛔ **— REFUTED, SEE THE STUB AT THE TOP.** It is the EVER GRANDE CITY **outdoor** map, not the apron; **0 of 99 runs entered VICTORY ROAD**.

| furthest map **reached** | runs | share |
|---|---|---|
| Ever Grande City | **30** | **30.3%** |
| Sootopolis | 20 | 20.2% |
| Mossdeep | 10 | 10.1% |
| Fortree | 8 | 8.1% |
| Lavaridge | 17 | 17.2% |
| Mauville | 10 | 10.1% |
| Slateport / Rustboro | 4 | 4.0% |

Cumulative: **100%** reach Rustboro, **96%** Mauville, **86%** Lavaridge, **69%** Fortree,
**61%** Mossdeep, **51%** Sootopolis, **30%** Victory Road *and* Ever Grande.

⛔ **"REACHED" IS NOT "CLEARED".** There is no badge or chapter marker in these logs — I grepped for
one and there is none — so this is map arrival, a strictly weaker claim than beating the gym there.
The instrument names every milestone `reached_*` for exactly that reason. **Do not let this table be
quoted as a badge distribution.**

Median party max level **49**; max 58. Median dex **14 owned**; max 22.
Whiteouts: **2,537 total**, median **28 per run**, max 58.

⭐ **WHAT THIS MEANS FOR §Ch24.** The approach to the League is *not* the bottleneck — roughly one run
in three gets to Ever Grande unaided, with a party around L49. A working Segment 24 would convert
those into actual Elite Four attempts. The chapter is the highest-leverage thing to build.

### ⛔ The falsification arm, and it held
The instrument explicitly looks for any run entering a League **interior** map (Pokémon League 1F,
Sidney/Phoebe/Glacia/Drake/Champion's rooms, Hall of Fame). **Zero.** That is *consistent with*
§Ch24 being unwired in `story_mode.py` — ‼ consistent with, not proof of: it shows the interior was
never entered, not why.

---

## 2. THE DERAILS — 977 TOTAL, AND THE TOP THREE FAMILIES SHARE ONE ROOT CAUSE

| runs hit | occurrences | derail |
|---|---|---|
| **78 / 99 (79%)** | 179 | `Could not reach (26,5) on PETALBURG_WOODS … no path from (14,5)` |
| **84 / 99 (85%)** | 84 | `Could not reach (25,55) on ROUTE111 … Source (47/9 @ ROUTE116) and destination (4/10 @ RUSTURF_TUNNEL) are not on connected maps` |
| 37 / 30 / 28 / 3 | 94 / 94 / 29 / 12 | `heal_in_pokemon_center: the walk to {PetalburgCity, LavaridgeTown, FortreeCity, FallarborTown} is BLOCKED` |
| 54 | 62 | `global watchdog — nothing progressed for N frames` |
| 9 | 45 | `Ch23 (Victory Road) failed after N attempts` |
| 8 / 6 / 5 | 40 / 30 / 25 | `{Winona, Juan, Tate & Liza}: N losses with no super-effective answer` |

### ⭐⭐ THE SYNTHESIS: THE BOT COMMITS TO A DESTINATION BEFORE PROVING IT CAN WALK THERE

The top three families are **the same defect wearing three coats**, and each subsystem rediscovers it
independently:

* **ROUTE111 (85% of runs)** — the training relocation picks ROUTE111 while standing on ROUTE116.
  The path needs RUSTURF_TUNNEL, i.e. a **warp**, and `calculate_path` *cannot use warps* — a known,
  documented limitation. The pathfinder is right to refuse; the **chooser** was wrong to ask.
* **`heal_in_pokemon_center` (229 occurrences across 4 destinations)** — the heal map names a town
  the walker cannot reach from where the bot is standing.
* **PETALBURG_WOODS (79% of runs)** — the only *intra*-map member: source and destination are both
  on PETALBURG_WOODS at y=5, x 14 → 26, and no path exists between them.

⇒ **The common shape: a destination is selected by a table or a rule, and its reachability is only
discovered by failing to walk there.** ‼ This is the same shape as `#26-healmap-lavaridge` and
`#26-healmap-route111split`, which are filed as separate small items — **the measurement says they
are instances of one systemic issue, and it is the largest single source of derails in the corpus.**

⚠ **PetalburgCity at 94 occurrences / 37 runs is NOT in the punch list at all** — `#26-healmap-*`
names Lavaridge and the Route-111 split. Petalburg is the joint-largest heal-nav destination failure
and is undocumented.

---

## 3. ⛔⛔ RETRACTED — I COMPARED *ATTEMPTS* TO *FAILURES*. THE DOCUMENTED ROW IS FINE.

**This section originally claimed** that `04-HANDOFF.md`'s SAFETY BATCH row (`Could not reach …
ROUTE111` = 1 ARM-ON vs 5 ARM-OFF) *"does not reproduce and INVERTS when normalised per run
(0.755 vs 0.257)"*, and the claim was repeated as fact in the handoff banner and the changelog
headline. **It is withdrawn in full.** A Tier 1 reviewer refuted it and the refutation checks out.

**What I did wrong.** I counted `DERAIL #N: Could not reach … ROUTE111` lines and treated each as a
*failure*. It is not. `07-CHANGELOG.md:27655` defines the metric, and my own numbers are literally
the ones already published there:

> *"The relocations still happen — **77 in ARM-ON vs 27 in ARM-OFF**, in line with the 74/37
> measured before. What changed is that they now **succeed**: 1 failure per 77 attempts (**1.3%**)"*

⇒ 77 and 27 are **ATTEMPTS** — exactly what my grep reproduced. 1 and 5 are the **FAILURES** among
them. A relocation that logs this derail and then *recovers* is a successful attempt, and a sampled
log confirms the shape: derail → stuck-detector dump → resume → run continues.
**Attempts-per-run and failures-per-attempt are different, non-contradictory quantities.** The
documented row is consistent with its own evidence; there was never an inversion.

‼ **THE LESSON, AND IT IS ONE THIS PROJECT HAD ALREADY WRITTEN DOWN.** `CLAUDE.md` rule 5 says *"a
count can be exactly right and its conclusion still wrong — ask what question it ANSWERED."* My
count was exactly right. It answered "how many relocation attempts hit the warp-blind pathfinder",
and I read it as "how many runs were harmed". ⛔ **And note where the damage was**: my own note
hedged honestly (*"I could not reproduce how 1 and 5 were obtained"*) while the HANDOFF BANNER and
the CHANGELOG HEADLINE asserted `INVERTS` flatly. That is SESSION DISCIPLINE rule 2 — **the headline
carries the caveat** — violated in the same document that quotes it.

### ⛔ CONSEQUENCE FOR §2 ABOVE — READ IT AS *EVENTS*, NOT AS DAMAGE
The same error threatens the derail table in §2. Those are **derail EVENTS**, and the ROUTE111
evidence proves that a derail can be followed by a clean recovery. **This corpus does not yet
distinguish a derail that recovered from one that ended a run**, so:
* *"84 of 99 runs hit the ROUTE111 derail"* is TRUE and is a statement about **events**.
* *"the ROUTE111 derail costs 85% of runs"* would be FALSE, and is not claimed anywhere.
⇒ **The ranking in §2 ranks FREQUENCY, not COST.** Ranking by cost needs a per-derail outcome
classifier that does not exist yet — that is the honest next measurement, and it is now the first
item in §4.

## 4. WHAT I RECOMMEND, IN ORDER

1. ⛔ **FIRST, MAKE THE DERAIL TABLE MEAN SOMETHING: classify each derail as RECOVERED or FATAL.** §2 ranks frequency; nobody has measured cost. The §3 retraction exists precisely because a frequency count was read as a cost. Until that classifier exists, do NOT prioritise navigation work off the §2 ordering.
2. **Build the §Ch24 sequencer.** ⛔⛔ **THE REASON GIVEN HERE IS REFUTED — the recommendation is not.** §Ch24 is still the right build, as FINISHING the story; it is NOT converting traffic that exists, because **0 of 99 runs reached the door** (`#26-victoryroadgap`). *(The superseded reason, kept verbatim:)* 30% of runs already reach the door; nothing else converts so much
   latent progress into the user's stated goal. Routing and traps are already established in
   `2026-09-15-ch24-ROUTING-AND-GRADING-CORRECTION.md`.
3. **File the destination-reachability defect as ONE item**, not three. The fix shape is the same in
   all three: *ask the pathfinder before committing to the destination, and pick a reachable
   alternative when it says no.* ⚠ A `calculate_path` OK is **not** proof the driven navigator can
   walk it (`KI-48`) — so the check must use the instrument the bot actually uses.
4. ✅ **NOTHING TO DO ABOUT THE SAFETY-BATCH ROW** — §3 is a RETRACTION; the row was correct.
5. Leave the gym-loss derails (Winona 40, Juan 30, Tate & Liza 25) alone for now — they are
   type-coverage problems with an existing decision trail, and they are an order of magnitude
   smaller than the navigation family.
