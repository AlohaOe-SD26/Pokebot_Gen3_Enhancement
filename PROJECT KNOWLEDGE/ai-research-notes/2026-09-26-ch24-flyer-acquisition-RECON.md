# §Ch24 flyer acquisition (gap 5): design synthesis (a NOTE, not truth)

> ⚠ **AI RESEARCH NOTE — NOT A SOURCE OF TRUTH.** A 5-agent Claude workflow (`ch24-flyer-acquisition-recon`,
> 2026-09-26): machinery, when/where, encounter data, adversarial, and a synthesizer. Nothing was driven. The
> authoritative doc is `03-PUNCH-LIST.md` `#26-ch24organic` (gap 5). ⚠ Written BEFORE USER RULING 15 (R1 now needs
> only 4 of 6 at the floor), which changes its item 4 (a withdrawn low-level carrier no longer blocks R1 by itself
> if four fighters are at the floor) and softens user decision U1.

*2026-09-26. Synthesized from 4 recon notes (machinery, when/where, data, adversarial) plus synthesizer re-reads. [CODE] = `C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot/` (wt/ch24organic). Nothing driven.*

**Headline:** most no-flyer parties already OWN a boxed flyer, so the first build is a lobby-PC withdraw, not a hunt. Every option needs the lobby-PC swap, which has never been driven. The existing HM hunt must not be reused as-is: 3 of its 6 grounds spin on water with a land target list, and R119 cannot succeed.

## 1. The net

1. **`ensure_fly_learner` never looks in the box.** It reads the party and reports `no_learner` ("gap 5") [CODE modules/story/pokemon_league.py:2186-2250, re-read]. `boxed_hm_learner_pids` exists as a pure save read [CODE early_game.py:4706-4774].
2. **From the plateau only a withdraw is possible.** Nothing walkable from (18,6) has encounters or water [DECOMP EverGrandeCity layout; INFERENCE offline walk]. Both PC paths go through `heal_in_pokemon_center`, which needs a `PokemonCenter` member the League lacks and stand tile (10,2) [CODE early_game.py:5068-5083; pc_trip.py:35-37,555; map_data.py:1524-1544]. The lobby PC is (6,1) `MB_PC`; (6,2) is standable [DECOMP EverGrandeCity_PokemonLeague_1F/map.bin, two independent decodes]. ⇒ a **new lobby-PC primitive**.
3. **The final swap-back also needs that PC** [INFERENCE]: the carrier must be in the party to fly home, and the displaced fighter must return before R1. Mid-game acquisition does not avoid it.
4. **R1 checks levels, not identity.** `ch24_trainees_below_floor` counts every non-egg member [CODE pokemon_league.py:1622-1647, re-read], so a withdrawn L2 carrier becomes a trainee. If the carrier is re-boxed without withdrawing the fighter, a 5-mon party passes R1 [CODE `ch24_readiness_shortfall`, adversarial]. ⇒ record six fighter PIDs at entry, exclude all other PIDs from trainees, assert party PIDs == fighters before R1.
5. **The hunt targets the wrong table.** Spin tiles R115 (6,53), R118 (29,15), R119 (21,109) are `MB_OCEAN_WATER`, but targets come from `land_encounters` [CODE early_game.py:4911-4937,5017; DECOMP map.bin + metatile_attributes.bin, decoded twice; LOG (29,15): Tentacool 214 / Wingull 96 / Pelipper 16, no land species]. R119's target {Tropius} never appears there. The recon's "R115 ≈10 steps" is the Surf-gated north grass only. Order is furthest-first: R121, R119, … [CODE early_game.py:4979-5005].
6. **`hm_learner_slot` ignores saturation**; `_fly_teach_plan` is the right rule and accepts a carrier with an empty slot or no attack [CODE pokemon_league.py:2126-2183, re-read].
7. **A full party breaks the hunt.** It raises, or deposits `find_dead_weight` (lowest level) — at §Ch24 a RULING-12 trainee, permanently [CODE early_game.py:4956-4962,5180-5209; team_policy.py:170-173]. The catch branch needs party < 6 [CODE story_mode.py:3399]; 61/64 parties are full at BADGE06 [LOG badge-log.json]. A full-party catch goes to the PC [DECOMP src/pokemon.c:4439-4440].
8. **Teach late is safe; keeping the flyer in the party is not.** Fly gates use `knows_move` [CODE training_areas.py:851; pokemon_party.py:79-83]. A party flyer becomes a §Ch23 L47 requirement [CODE victory_road.py:493,504] and a make-room victim (P1 run 5 lost Swellow L34 at §Ch19b [LOG P1-stdout-20260915-072605.txt:343220-343225]). ⇒ **box it**.
9. **Cite rulings by date.** 09-25 RULING 13 ("the roster is free") sanctions a carrier "swapped in as needed" and calls withdrawing "the PREFERRED fix" [LOG 06-DECISIONS-LOG.md:7101-7125, re-read]. 09-23 RULING 12 still binds: "Do not box Zigzagoon or Castform to make the level floor easier" [LOG :6816-6834]. A PC round-trip regression on the current build is owed [LOG :7133-7140].

**Disagreements:** (a) machinery says R118 sea "beats" R121; data puts them level (sea 113-129 steps/target, R121 100). (b) When/where's "R118, 47 steps" is the east grass, which has no spin tile; our tile is sea, ~129. (c) RULING 2's "room": adversarial reads the VR exit half; 06:6241 reads (18,42). Unresolved.

## 2. The true size

Same logs, three denominators [LOG endless-P*/badge-log.json + debug-logs; DATA species.json]:

| Denominator | No party flyer | Owns none (party ∪ box) |
|---|---|---|
| Refused runs 09-15/16 (recon) | 13/30 | — |
| Badge-8 parties 09-15/16 | 18/39 | 6–7/39 |
| + 09-26 batch (3) | **19/42 = 45%** | **7–8/42 ≈ 17–19%** |

When/where (23/42 have a flyer) and adversarial (21/39 + P1-1, P2-1) reconcile exactly [synthesizer arithmetic]. Owners hold Wingull ×10 (+Pelipper), Tropius ×1, mostly low-level dex-fence catches [LOG `[DEXCATCH] … -> box`]. Caveats: the census counts dex-fence catches, not make-room deposits, so "owns none" is an upper bound; badge 8 proxies §Ch24 entry; nothing read from saves. ⇒ a withdraw serves ~11 of 19; a new catch is needed for ~7–8 of 42.

## 3. Options (ranked)

### O1 — PC-first at the lobby; carrier is a PID-excluded mule (build first; all options need it)
At (18,6) record FIGHTERS. If `_fly_teach_plan` finds nobody and a carrier is boxed: enter the lobby; at (6,2) facing Up, in ONE visit deposit fighter X (the one trained LAST, not `find_dead_weight`) and withdraw carrier C by PID. Teach (unchanged). The ladder trains below-floor ∩ FIGHTERS. At X's turn, swap at an anchor PC (X in, finished Y out). Fly back; lobby swap C→Y; assert PIDs == FIGHTERS; R1.
Risks: lobby PC undriven; lead rotation could send C into battle; whether a fainted C can Fly out of battle; "every anchor has a PC" is INFERENCE; ≥3 PC visits.
**Drive:** fixture = organic §Ch24-entry save from a "no party flyer, boxed Wingull" run (NOT P4-1 — owns none), md5 pinned. Premise conjunct at take point: `_fly_teach_plan(party)` is None ∧ `boxed_hm_learner_pids(HM02)` non-empty, else VACUOUS. Ordered readings: L-ENTRY, L-WD (C in party, X in box, by PID), F-TAUGHT, L-FLYOUT, L-BACK, L-SWAP (party PIDs == FIGHTERS). Continue: `calculate_path` to the League door. Budget: one rung. Fault arms: `…_FAULT_NOBOXWITHDRAW` (expect `no_learner`, then R1 names trainees); `…_FAULT_NOSWAPBACK` (identity assert MUST fail while the level check passes); `…_FAULT_CARRIERTRAINEE` (R1 names C).

### O2 — Segment 13e acquisition into the box (after `_guard("Gym 6 (Winona)")`, before Seg 14)
[CODE story_mode.py:4900→4902]: BADGE06 held, Fortree PC adjacent. Re-entry gate "owns a Fly learner in party ∪ box, or BADGE07"; never raises; no teach. Needs: `_fly_teach_plan`-based predicate; method-aware targets (surf table on water [CODE map.py:881,1857]); density ranking; a catch-to-box lift of the <6 gate, confirmed by PID; a local mart (restock defaults to Rustboro [CODE early_game.py:2457]).
Risks: single spin + 2,400-frame XP drought at surf rate 4 [CODE early_game.py:169-219,5033]; reachability; frames against the 7M cap.
**Drive:** fixture at 13e from an own-none run, full party. Premise: no compatible member in party ∪ box. Readings: ground/tile/method; target set ⊆ that tile's table; caught PID in box; party PIDs unchanged; no Fly knower; path to Seg 14's start. Fault arms: GROUND=R119 sea (expect "never caught one"); LANDTABLE (expect timeout). Shared-path A/B: a flyer-owning fixture must spend ≈0 frames at 13e.

### O3 — Dex-fence exemption: box-catch a Fly species when none is owned
Cheapest code; every own-none run met Wingull/Taillow repeatedly [LOG]. Risk: touches the fence measured at 52.0% → 15.8% [LOG 06:7120-7124]. Frequency question ⇒ batch A/B (finish rate AND flyer-owned at §Ch24), plus one correctness driver at a full-party Wingull encounter asserting a box catch by PID.

## 4. User decisions
- **U1:** is the mule swap (a fighter, possibly Zigzagoon/Castform, briefly boxed during training; the same six at R1) compatible with 09-23 RULING 12?
- **U2:** for the ~7–8/42 that own none — O2, O3, or accept R1's named refusal? O3 is catch policy (09-24: E4 → Pokédex → organic).
- **U3:** RULING 2's "room": would a League-side VR-exit-half tile be acceptable? It rescues only L39+ parties; 2 of 7–8 non-owners lack bench mons.
- **U4 (deferred):** bias Segment 4 toward Taillow.

## 5. Unverified, load-bearing
1. Box contents on real saves at §Ch24 entry.
2. The lobby PC works from (6,2) facing Up (DECOMP only).
3. PC round-trip regression on the current build.
4. Whether a fainted carrier can Fly, and whether lead rotation can put it in.
5. Every ladder anchor has a reachable PC.
6. 13e `calculate_path` reachability of R118 (29,15), R121 (44,14), R118 east grass (bridges read as walls [CODE story_mode.py:1188,1329]).
7. Encounter/drought rates while spinning on a surf tile.