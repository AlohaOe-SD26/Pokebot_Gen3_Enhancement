# ⛔ NO-GO — THE `#24-trainingbrackets` PRODUCTION DATA CHANGE (2026-09-18)

> ⛔⛔ **AGENT OUTPUT IS A NOTE, NEVER TRUTH.** A 7-agent audit (3 angles, each adversarially
> verified, then synthesised) reviewed a proposed change to PRODUCTION data before it was written.
> **The change was NOT made.** ✅ marks what **I** re-verified at FILE:LINE.

---

# ⭐⭐ THE VERDICT, AND THE MECHANISM I VERIFIED MYSELF

**NO-GO on the two edits as specified.** The proposal was:
1. add `(MapRSE.VICTORY_ROAD_1F, (15, 39), (36, 40))` to `TRAINING_GRASS`;
2. add `AREA_PREREQ[VICTORY_ROAD_1F] = "region"` so the conservative `allow=None` path refuses it.

⛔ **IT WOULD BE INERT DATA, AND I CONFIRMED THE REASON AT SOURCE.**
* ✅ `region_reach.py:97` — the only edge into the cave is
  `((0, 8), (24, 43)): "waterfall",  # EVER_GRANDE_CITY <-> VICTORY_ROAD_1F`.
* ✅ `region_reach.py:342` — `if edge.gate is not None and not caps.get(edge.gate, False): continue`.
* ✅ `region_reach.py:228-236` — `_resolve_caps` builds `explicit` from **exactly four** keys:
  `{"surf", "rock_smash", "cut", "strength"}`. **There is no `"waterfall"` key.**
⇒ `caps.get("waterfall", False)` is **False for every party at every badge count**, and
`_gate_key` (`:158-159`) is **symmetric**, so the edge is sealed in BOTH directions.
⇒ **`is_map_reachable(VICTORY_ROAD_1F)` is always False**, so every production predicate would
refuse the new row and it would buy nothing.

✅ **THE DATA ITSELF IS CORRECT — that was never the problem.** `(15,39)` is a real `Cave` encounter
tile and `(36,40)` is exact against our own ROM cache (8 Grass rows, min 36 / max 40).

⭐⭐ **AND THE AUDIT UNCOVERED A LATENT PRODUCTION BUG THAT IS BIGGER THAN THE CHANGE IT BLOCKED** —
filed as `#24-waterfallcap`. ✅ It is an OMISSION beyond reasonable doubt: `_GATE_MOVE_NAMES:100-106`
already holds `"waterfall": "Waterfall"` and `_RSE_BADGE_BY_MOVE` already holds `"Waterfall":
"BADGE08_GET"` with the comment *“Added with the Victory Road gate below”* ⇒ three of the four
pieces were wired and only `explicit` in `_resolve_caps` was missed.

⛔⛔ **AND HERE THE AUDIT WAS WRONG, AND I CAUGHT IT ONLY AFTER PROPAGATING IT — READ THIS BEFORE
READING §ANYTHING BELOW.** The synthesis argues the bug is an *“accidental safety net”*, so fixing
it alone would expose Victory Road to `_training_area_allowed` / `_counter_area_allowed` *“for any
L35+ party at any story point”*, and therefore that all three parts must land together. ✅ I
verified that at source and it is **refuted twice over**:
1. With **no Victory Road row in `TRAINING_GRASS`**, `best_training_area` (`training_areas.py:473-512`)
   cannot return Victory Road at all ⇒ a cap fix alone exposes **nothing**.
2. The cap would **not** resolve True. `reachable_maps` defaults every cap to `None`, so
   `_resolve_caps` calls `_live_capability("Waterfall", badges)` — which requires a party mōn that
   knows Waterfall **and** `BADGE08_GET`. A party without a Waterfall user still resolves False.
✅ **THE REAL COUPLING RUNS THE OTHER WAY, AND THE AUDIT DID NOT NAME IT.** At `:504-505`,
`allow=None` — the production default — performs **no reachability check whatsoever**; it only
skips areas that HAVE an `AREA_PREREQ`. ⇒ it is the **`TRAINING_GRASS` row that must never land
without its `AREA_PREREQ` row**. **`#24-waterfallcap` is safe to fix on its own and may go first.**
⇒ the ordering advice in the synthesis below is WRONG; the NO-GO verdict itself still stands.

⚠ **AND A CORRECTION TO SOMETHING I WROTE WHILE SETTING THIS UP.** I stated that the only evidence
`(15,39)` rolls encounters was *"a COMMENT … with no committed artifact"*. ⛔ **False.**
✅ `tools/story-dev/ch23route_R15.log:110` exists and reads
`[ch23route]     (15, 39) tile_type='Cave' elev=3 collision=0`. I had grepped only
`tools/story-dev/evidence/*.txt`; the log lives at the `tools/story-dev/` root. **Concluding absence
from a partial search is a rule this project already has, and I broke it.** My own
`probe_grind_tile_encounters.py` still earns its keep — it is re-runnable and adds a CONTROL the
original log lacks — but its premise sentence was wrong and is corrected.

⚠ **NOT VERIFIED BY ME:** the caller census, the blast-radius table, and the five-part
GO-MODIFIED plan below. Those are the audit's, not mine.

---

# ─── THE AUDIT'S OWN SYNTHESIS, VERBATIM AND COMPLETE ───

> ‼ Everything below is the 7-agent output as written. It is a **NOTE, never truth**, and its
> ORDERING ADVICE IS REFUTED — see the correction above. Preserved in full so that “what the
> audit actually said” is a checkable artifact and not my paraphrase.
> *(An earlier version of this file carried a parse failure and 6,000 truncated characters
> instead: the extractor looked for `spec` at the top level when it is nested under `result`.
> Caught by a Tier 1 reviewer.)*

# SYNTHESIS — VICTORY_ROAD_1F row + `AREA_PREREQ["region"]` (variant B)

*A NOTE, never truth. READ-ONLY attestation: I edited/created/deleted nothing, ran no git write, started no emulator. My only executions were `diff -q`, `grep`, `sed`, and one `python -c` that read `cache/encounter_index_BPEE0.json` (no repo module imported, nothing mutated). All paths relative to `C:\Remote Projects\Pokebot_Gen3_Enhancement\`. Everything below is re-checked by me at the line cited unless marked INFERRED.*

---

## 1. VERDICT

**NO-GO on the two edits as specified; GO-MODIFIED as a five-part change** — because the single mechanism that makes variant B *safe* is the same one that makes it *incapable of its purpose*: `_resolve_caps` (`region_reach.py:228-236`) emits only `{"surf","rock_smash","cut","strength"}`, so `caps.get("waterfall", False)` at `:342` is **False at every badge count for every party**, and the one boundary edge into the cluster (`region_reach.py:97`) is keyed through the **symmetric** `_gate_key` (`:158-159`) — ⇒ every production predicate answers `is_map_reachable(VICTORY_ROAD_1F) == False` from everywhere outside the cave, so the row is unreachable data that falsifies ~8 in-tree statements, duplicates an existing `PENDING_GRASS` row, and flips the Tier-0 drift count to buy nothing.

---

## 2. IS (15,39) A REAL ENCOUNTER TILE, AND IS (36,40) THE RIGHT BAND?

| question | answer | evidence |
|---|---|---|
| Is (15,39) a real encounter tile? | **YES — a live tile-behaviour reading, not a comment.** | VERIFIED `tools/story-dev/ch23route_R15.log:110` `[ch23route]     (15, 39) tile_type='Cave' elev=3 collision=0`, with 8 probed neighbours all `'Cave'` on `:111-117`. Procedure VERIFIED `tools/story-dev/story_harness.py:12792-12811` (`get_map_data(MapRSE.VICTORY_ROAD_1F, _cand)` per candidate, under "⛔ Only `MB_CAVE` tiles roll encounters on 1F"). |
| Has a wild battle been *counted* from it? | **NOT FOUND IN REPO** — tile type is a proxy for encounter rolls, not a count. | Honest limit, carried forward from the adversary angle; I did not find a contradicting log either. |
| Is it the ruled ground? | **YES, exactly.** | VERIFIED `sandbox-pokebot/modules/story/victory_road.py:477` `TRAIN_SPOT_1F = (VR1F, (15, 39))     # 1 step from the entrance warp, elevation 3`; `06-DECISIONS-LOG.md:6214` RULING 2 names it. |
| Is (36,40) the right band? | **YES — exact against our own ROM-derived cache. I re-derived it myself.** | VERIFIED `sandbox-pokebot/cache/encounter_index_BPEE0.json` (`rom BPEE0`), all `map == [24,43]` `Grass` rows: 8 rows, **min 36 / max 40**. Decoded (internal→national, offset 25): Golbat 25 % L38-40, Hariyama 25 % L38-40, Zubat 10 % L36, Makuhita 10 % L36, Lairon 10 % L40, Loudred 10 % L40, Whismur 5 % L36, Aron 5 % L36. |
| Does slot weighting distort it? | Mildly — **weighted mean 38.30 vs `hi = 40`, ≈4 % overstatement**, well inside the 1.7× the table rejects water for. I computed this independently and it matches the adversary-verifier's figure to two decimals. | `(39·25 + 39·25 + 36·10 + 36·10 + 40·10 + 40·10 + 36·5 + 36·5)/100 = 38.30`; contrast VERIFIED `training_areas.py:56-60` (water weighting → ROUTE126 "1.7x"). |
| Independent corroboration | Two further places carry the same numbers. | VERIFIED `victory_road.py:1988` `WILD_MAX = 40  # MEASURED: VICTORY_ROAD_1F's strongest land encounter is L40`; VERIFIED `training_areas.py:149` `(MapRSE.VICTORY_ROAD_1F, None, (36, 40)),      # Aron/Golbat/Hariyama/Lairon/Loudred/…, rate 10.` |

**⇒ Both proposed data values are correct. The data is not the problem.**

---

## 3. WOULD ANY EXISTING CALLER BE HARMED?

Census re-run by me (`grep -rn "best_training_area\|best_training_grass" --include=*.py sandbox-pokebot/`): **4 picker call sites, all passing an `allow`.**

| # | call site (VERIFIED) | predicate | mid-game VR? | in-VR VR? | harmed? |
|---|---|---|---|---|---|
| 1 | `story_mode.py:3168` fodder probe | `_allow` (`:3156-3158`) | **NO** | n/a — see below | **NO** |
| 2 | `story_mode.py:3199-3203` relocation | same `_allow` | **NO** | n/a | **NO** |
| 3 | `story_mode.py:2659` `_maint_ground = lambda lv: best_training_grass(lv, allow=_maint_allow)` (default-ON, `:2636`) | `_maint_allow` (`:2656-2658`) | **NO** | n/a | **NO** |
| 4 | `counter_hunt.py:647` counter ground, `max_hops=8` | `_counter_area_allowed` (`:1297`, verdict at `:1322`) | **NO** | n/a | **NO** |

**Why "n/a" and not "yes"** — this is the finding that kills the loudest remaining blocker, and I verified it myself rather than inheriting it:

- VERIFIED `grep -rn "_maintain_lagging_battler" modules/ plugins/` → **exactly one non-definition call site**: `plugins/custom_modes/story_mode.py:2926`, inside `def _prepare_for_fight(self, cfg)` at `:2908`.
- VERIFIED `grep -n "_prepare_for_fight("` → **ten** call sites: `:4095` roxanne, `:4186` rival, `:4252` brawly, `:4363` rival110, `:4398` wattson, `:4594` flannery, `:4645` norman, `:4803` winona, `:4926` tate_liza, `:5115` juan — **and nothing after**.
- ⇒ Sites 1–3 **only ever run during a pre-badge-8 gym prep**. They never execute while the bot stands in Victory Road, which VERIFIED `story_mode.py:1261-1266` (`here = …` / `target = …` / `if here == target:` → `return True`) is the *only* state that admits VR1F.

Deciding lines for the "NO"s: VERIFIED `region_reach.py:97` `((0, 8), (24, 43)): "waterfall",  # EVER_GRANDE_CITY <-> VICTORY_ROAD_1F` · `:262` `gate = KNOWN_GATES.get(_gate_key(a, b))` · `:158-159` `def _gate_key(a, b): return tuple(sorted((a, b)))` (symmetric — seals **outbound** too) · `:342` `if edge.gate is not None and not caps.get(edge.gate, False): continue` · `:228-236` `_resolve_caps` with four keys only. Map ids VERIFIED `map_data.py:802` / `:1123`.

**⇒ No existing picker caller is harmed. Not one.**

---

## 4. BLAST RADIUS — every reader of `TRAINING_GRASS` / `AREA_PREREQ`

| # | reader | file:line | changes? | production consequence |
|---|---|---|---|---|
| 1 | `best_training_area` | `training_areas.py:473`, guard `:501`, prereq `:503-507`, score `:509` | **YES at team_level ≥ 35** under a permissive allow; **unchanged at `allow=None`** (prereq works here) | none — all 4 production sites route through region_reach |
| 2 | `best_training_grass` | `:205`, `:248`, `:250`, `:252` | **YES at mon_level ≥ 35 EVEN AT `allow=None`** — no `allow is None` branch exists | **zero production reach**: sole production caller is `story_mode.py:2659`, which passes `_maint_allow`. Every `allow=None` caller is a `tools/story-dev` probe |
| 3 | ⛔ `early_game._hm_hunting_grounds` / `ensure_hm_learner` | `:4577` def, `:4587` loop, `:4631`, `:4646` `ordered = list(reversed(grounds))  # furthest-progressed first`, `:4672` fallback `grounds[0]` | **YES — an appended row is tried FIRST**; NO `allow`, NO `AREA_PREREQ`, NO region_reach. Only gate is `calculate_path` | **BOUNDED — see below. This is the one consumer that matters and I resolved its open question.** |
| 4 | `counter_plan.find_counter_candidates` | `:146` `tile_by_map`, `:248-253` (honours `allow=None` prereq), `:261`, `:297`, `:319` 1e8, `:321` +100 000.0, `:337`, `:345` | **YES** — VR candidates gain `"tile": (15,39)` and +100 000.0 tier | diagnostic ORDER/TEXT only; cannot flip `huntable` (`hunt_tile` is None under the strict default) |
| 5 | `hunt_ground_tile` | `:402` def, `:451` `POKEBOT_HUNT_ANYGROUND` default `"0"`, `:457-461` early return, `:464-466` fallback loop | **only under `POKEBOT_HUNT_ANYGROUND=1`** → returns `(15,39)` | flag pinned at 0 in `29-DISABLED-FEATURES-REGISTRY.md:51`; default unchanged |
| 6 | `_training_area_heal_map` | `story_mode.py:1420-1450` — 15 keys, **no VICTORY_ROAD** (I read the whole dict) | not a reader of the table, but the **pair** of it | latent: `decide_maintenance` rule 6 refuses (`:1561`); relocation defaults to the boss's centre (`:3210`). **Unreachable today** per §3 |
| 7 | scalar helpers `xp_per_battle` / `relocation_floor` / `local_patch_is_fodder` / `estimate_frames_to_level` | `training_areas.py:589-718` | **NO** — they take scalars | nothing below team_max 35 moves |
| 8 | `PENDING_GRASS` readers | `probe_training_economics.py:108` (filters `t is not None`) | **NO** | — |
| 9 | serialisation / cache | none | **NO** | I re-ran the grep: zero `json|dump|pickle|write|cache|save` hits on `TRAINING_GRASS` |
| 10 | Tier-0 drift gate | `run_gates.py:110` `("audit_doc_consistency.py", False)` | **YES** | VERIFIED by me: `diff -q sandbox-pokebot/modules/story/training_areas.py custom-pokebot/…` → **IDENTICAL**. Editing sandbox moves measured drift 0 → 1; every doc claiming 0 must move in the same commit |

### ⭐ Reader #3, resolved — the question all three angles left open

The angle-1 verifier called this "the decisive refutation" and ended: *"The only thing standing between the bot and a Victory Road HM-learner hunt is whether `calculate_path` raises."* **It raises.**

- VERIFIED `modules/map_path.py:798-803` `def can_waterfall(): … context.rom.is_rse and get_event_flag("BADGE08_GET") and get_party().has_pokemon_with_move("Waterfall")`, consumed at `:830` `if tile.waterfall_to is not None and from_direction is Direction.North and can_waterfall():`.
- VERIFIED `:784-788` `def can_surf(): … get_event_flag("BADGE05_GET") and get_party().has_pokemon_with_move("Surf")`, consumed at `:855`.
- ⇒ `calculate_path` **models both gates**. A pre-badge-8 party cannot statically path to Victory Road; VR is silently demoted and the next candidate is tried. Cost: **one extra static path computation per hunt**, no behaviour change.

And the exposure is narrower still — only **three** production hunts exist, and I identified each:

| hunt | call site | HM | does VR1F's land table host a learner? |
|---|---|---|---|
| Rock Smash | `story_mode.py:4465` (`_hm06`, centres Mauville/Slateport ⇒ post-Wattson, pre-Surf) | HM06 | **YES (INFERRED)** — Makuhita/Hariyama/Whismur/Loudred/Aron/Lairon are Gen-3 Rock Smash learners. `can_learn_tm_hm` needs a live ROM, so this is INFERRED, not VERIFIED |
| Surf | `story_mode.py:4677` (`_hm03`) | HM03 | **NO (INFERRED)** — none of the 8 VR1F land species learns Surf in Gen 3 |
| Dive | `story_mode.py:5035` (`_hm08`) | HM08 | **NO (INFERRED)** — no water species in the land table |

⇒ the single exposed path is **HM06 at an era with neither Surf nor Waterfall**, where `calculate_path` correctly refuses. And the documented error direction is favourable: VERIFIED `story_mode.py:1183-1198` — *"A wrong **NO** from `calculate_path` is INVISIBLE… A wrong **YES** from `region_reach` costs ONE wasted walk"*; `calculate_path`'s known bias is wrong-NO (it reads dual-elevation bridges as walls).

### Prose the row would falsify (all VERIFIED at their own lines)

`training_areas.py:27-30` ("⛔⛔ THE L28 CEILING IS THE GAME"), `:99-113` ("⛔ NONE of these is promotable today" — the header directly above `:149`, which variant B does **not** remove), `:108-111` ("never a `best_training_grass` pick from across Hoenn" — the proposal does exactly this), `story_mode.py:4888`, `:4919-4922`, `run_gates.py:531-533`, `probe_late_boss_configs.py:10`/`:151`, `story_harness.py:15594-15598`, `:21759-21761`. **And one is already false before any edit:** `03-PUNCH-LIST.md:2094` asserts `grep -c VICTORY_ROAD modules/story/training_areas.py` = **0**; measured **3** (`:149`, `:150`, `:151`).

---

## 5. THE EXACT DIFF

**Not the two lines as specified.** The two-line version is safe and inert. The five-part version is the smallest set that is *both* safe and *does something*.

```
# --- sandbox-pokebot/modules/story/training_areas.py -------------------------
# (1) TRAINING_GRASS, appended after :89 (the ROUTE121 row)
+    # ‼ THE ONLY ROW ABOVE L28. Band VERIFIED against cache/encounter_index_BPEE0.json
+    # (map [24,43] Grass: 8 rows, 36-40, slot-weighted mean 38.3). Tile is TRAIN_SPOT_1F
+    # (victory_road.py:477), tile_type='Cave' at ch23route_R15.log:110, and the heal
+    # round trip from it is DRIVEN (`#24-cavehealblind`, 2,002 yields, 0 whiteouts).
+    # ⛔ Gated by AREA_PREREQ below; see the reachability note there before touching.
+    (MapRSE.VICTORY_ROAD_1F, (15, 39), (36, 40)),

# (2) PENDING_GRASS :149 — REMOVE, do not leave the map in both lists
-    (MapRSE.VICTORY_ROAD_1F, None, (36, 40)),      # Aron/Golbat/Hariyama/Lairon/Loudred/…, rate 10.
+    # (VICTORY_ROAD_1F PROMOTED to TRAINING_GRASS <date> — tile (15,39) verified.)

# (3) AREA_PREREQ, after :280
+    # ⚠ "region" here means "only while ALREADY INSIDE Victory Road". The cluster's one
+    # boundary edge is gated "waterfall" (region_reach.py:97) and _resolve_caps (:228)
+    # never emits that key, so is_map_reachable() is False from outside at EVERY badge
+    # count; the sole admitting path is story_mode.py:1261-1266's `here == target`.
+    MapRSE.VICTORY_ROAD_1F: "region",

# --- sandbox-pokebot/plugins/custom_modes/story_mode.py ---------------------
# (4) _training_area_heal_map(), after :1449 — defence in depth, latent today
+        # 23 waypoints from EVER_GRANDE_CITY (18,42); the round trip is DRIVEN.
+        MapRSE.VICTORY_ROAD_1F: PokemonCenter.EvergrandeCity,

# (5) training_areas.py header :27-30 and :108-111, story_mode.py:4888 / :4919-4922,
#     run_gates.py:531-533, story_harness.py:15594-15598 / :21759-21761,
#     03-PUNCH-LIST.md:2094 — retire the "L28 ceiling / early-game-only" prose in the
#     SAME commit, plus the sandbox<->custom drift count 0 -> 1 (run_gates.py:110 is Tier 0).
```

`PokemonCenter.EvergrandeCity` is well-formed: VERIFIED `modules/map_data.py:1537` `(MapRSE.EVER_GRANDE_CITY, (27, 48))` — the exact door the 23-waypoint trip was measured to (`06-DECISIONS-LOG.md` ~:6240).

**⛔ What the diff must NOT contain**, and this is a prohibition, not a preference: a `_CAVE_EXITS`/`_CAVE_ENTRANCES` row for Victory Road. VERIFIED `03-PUNCH-LIST.md:477` — *"⛔ Do NOT "fix" this by adding a Victory Road row; `early_game.py:1988-1997` already records the tables as "REDUNDANT, not load-bearing""*, and VERIFIED `early_game.py:1988` *"‼‼ THE PARAGRAPH ABOVE IS HISTORY — IT STOPPED BEING TRUE ON 2026-07-31"*.

**And the diff does not yet make the row usable.** Two separate defects stand between it and RULING 5's goal, both of which are code, not data:

| blocker | line | why it blocks |
|---|---|---|
| `_resolve_caps` omits `"waterfall"` | `region_reach.py:228-236` | A **one-line omission, not a design.** `_GATE_MOVE_NAMES:105` tables `"waterfall": "Waterfall"`; `_RSE_BADGE_BY_MOVE:121` tables `"Waterfall": "BADGE08_GET"` with a comment explaining the RSE choice; `why_unreachable:504` builds `open_caps` from `_GATE_MOVE_NAMES` and will print *"needs Waterfall at EVER_GRANDE_CITY<->VICTORY_ROAD_1F"*. Every component **except** `_resolve_caps` believes waterfall is resolvable. The resolver that would serve it already exists at `:219-231`. |
| `_MAX_TRAINING_TRAVEL_LEGS = 4` | `story_mode.py:1101` | INFERRED-STRONG: at the League lobby **no `TRAINING_GRASS` row is within 4 hops**. Every edge (connection **or** warp) costs exactly 1 — VERIFIED `region_reach.py:264-273`, BFS `:328-346`. From EGC: `→R128(1)→R127(2)→R126(3)→R124(4)→LILYCOVE(5)→ROUTE121(6)`, +1 from the lobby = **7**. Derived from decomp connection/warp data + `_build_graph`'s rules (`:275-299`), **not from a live BFS**. |

---

## 6. WHAT COULD STILL GO WRONG — and the cheapest detector

| # | risk | likelihood | cheapest detection (all read-only unless noted) |
|---|---|---|---|
| R1 | A **second, ungated boundary edge** into `VICTORY_ROAD_*` exists ⇒ every "NO" in §3 flips | low but **load-bearing for everything** | ⭐ THE ONE TO RUN FIRST. On a live ROM: dump `region_reach._build_graph()` edges incident on `(24,43)/(24,44)/(24,45)` and assert exactly one boundary pair. *Partial offline corroboration (INFERRED, decomp read): EverGrandeCity's only inbound links are two warps, both to `MAP_VICTORY_ROAD_1F` — so both collapse onto the same gated pair under the symmetric `_gate_key` — and VictoryRoad_1F/B1F declare `"connections": null`.* The comment at `region_reach.py:88-97` remains the only in-repo source. |
| R2 | `calculate_path` returns a wrong **YES** to VR1F mid-game ⇒ the HM06 hunt walks toward Victory Road at ~badge 3 | low (documented bias is wrong-**NO**, `story_mode.py:1183-1198`; and `can_waterfall()` is a hard `BADGE08_GET` test) | With the row added, print `_hm_hunting_grounds(HM06)` from a post-Wattson fixture and assert `VICTORY_ROAD_1F` is either absent or demoted by `calculate_path`. **This is the only gate on reader #3.** |
| R3 | The `allow=None` flip in `best_training_grass` reaches production later | zero today, non-zero after any refactor | Add a one-line gate asserting `best_training_grass(40) is not VICTORY_ROAD_1F` **or** teach it the `allow is None` skip. Note the third picker already conforms: VERIFIED `counter_plan.py:248-253` implements the same conservative skip, in code that names the sibling it mirrors — so `best_training_grass` is the **lone outlier of three**, not one of two. |
| R4 | The heal-map gap becomes live if `_prepare_for_fight` is ever called after Victory Road | latent | Keep edit (4). Note the skip is **logged, not silent** — VERIFIED `story_mode.py:2678-2681` (`_log_story_event(f"SKIPPED - {reason}", "MAINTAIN")` + a console line). |
| R5 | Tier-0 goes red on the drift count | **certain** if docs aren't moved in the same commit | `py -3.12 tools/story-dev/run_gates.py` before committing. Measured today by me: `diff -q` → IDENTICAL, drift **0**. |
| R6 | `probe_maintain_discriminator.py` is cited as proof maintenance still works | — | ⛔ Don't. VERIFIED `:86` `heal = {m: f"PC_{getattr(m, 'name', m)}" for m, _t, _b in ta.TRAINING_GRASS}` — it **fabricates a heal centre for every table row** and would mask exactly the `_training_area_heal_map` gap. |
| R7 | `repro_no_return_grounds.py` / `repro_relocation_floor_wrong_mon.py` regress | low (assertions read as level-independent) | **Neither of the three angles, nor I, executed them.** They remain INFERRED-green. Run them. |
| R8 | `probe_maintain_unreachable.py` (#57, `run_gates.py:588`) turns red | very low | Green for a *structural* reason, not the level tuple: its case-A arms compare `allow=None` against `ACCEPT_ALL`, and since `best_training_grass` does no `allow=None` filtering, **both arms include the row identically at any level**. Raise its `(4, 8, 13, 20, 27)` to 40 and it still passes. |

---

## 7. REFUTED / WITHDRAWN

**Killed by the adversarial passes, and re-confirmed dead by me:**

| # | claim | status | killer |
|---|---|---|---|
| 1 | *blast* B1: "`_CAVE_EXITS` gap is a BLOCKER; add a Victory Road row" | ⛔ **DEAD, and the proposed fix is PROHIBITED** | `early_game.py:1988` "THE PARAGRAPH ABOVE IS HISTORY"; `03-PUNCH-LIST.md:477` "⛔ Do NOT 'fix' this by adding a Victory Road row". The heal round trip from `(15,39)` was DRIVEN: 2 002 yields, 0 whiteouts, HP 72.8 %→100 %, PP 437/480→480/480. The finding quoted a 2026-07-22 docstring history while skipping the correction printed 15 lines above the table it cited. |
| 2 | *blast* B1's support: "`probe_vr_heal_roundtrip.py` suggests the heal leg does not work" | ⛔ **CITED FOR THE OPPOSITE OF WHAT IT MEASURED** | Its recorded result is 44 wp same-map **OK**; the NO-PATH half is the **League-door** apron `(18,6)`, not the exit side RULING 2 chose. From `(18,42)` the Poké Center is 23 wp. |
| 3 | *blast* B2 / *adversary* R3: "the row SILENTLY DISABLES the maintenance errand … previously it picked ROUTE121 and ran" | ⛔ **CONSEQUENCE REFUTED** (mechanism survives) | Three ways: (a) not silent — logged twice at `story_mode.py:2678-2681`; (b) **unreachable** — one caller at `:2926`, ten prep sites `:4095`–`:5115`, all pre-badge-8 (**I verified this census myself**); (c) the counterfactual is false even then — `_gate_key` is symmetric, so from VR1F **every** `TRAINING_GRASS` row is unreachable, ROUTE121 included. The row changes the skip *reason*, not the behaviour. |
| 4 | *adversary* R4: the relocation path "fails OPEN" as a **live** defect | ⛔ **"LIVE" REFUTED** | Same ten pre-badge-8 call sites. Latent shape, not a shipping defect. Keep the heal-map entry; discard the justification. |
| 5 | *adversary*'s closing prediction: "from POKEMON_LEAGUE_1F the picker still answers **ROUTE121**" | ⛔ **REFUTED — the honest answer is `None`** | `_MAX_TRAINING_TRAVEL_LEGS = 4` (`story_mode.py:1101`) vs ROUTE121 at 6 hops from EGC / 7 from the lobby, uniform 1-hop weighting VERIFIED `region_reach.py:264-273`. **This is the most consequential correction in the whole file**: it means RULING 5's *"free to pick the best ground in the game"* is unattainable through this predicate **at any table content**. |
| 6 | *predicates*' headline: variant B is "inert everywhere except when the bot is already standing inside Victory Road" ⇒ ship as documentation | ⚠ **HALF-REFUTED, THEN RE-CONFIRMED FOR A DIFFERENT REASON** | Its verifier was right that the exception looked like it swallowed the rule — but wrong that it did, because sites 1–3 never execute in Victory Road (§3). Net: **inert everywhere in production**, which is a *stronger* claim than the original and makes the "documentation only" framing accurate after all. |
| 7 | *predicates*' safety story: "`AREA_PREREQ` is what makes it safe" | ⛔ **MECHANISM ERROR, CONFIRMED** | `_counter_area_allowed` (`story_mode.py:1297`) **never reads its `prereq` argument** — sole verdict is `:1322`. `_training_area_allowed` explicitly no-ops `"region"` (`:1255-1256`). The prereq's only live effects are `best_training_area`'s `allow=None` branch and `counter_plan.py:248-253`. |
| 8 | *predicates*' gate justification: "#57 stays green because 27 < 35" | ⚠ **VERDICT SURVIVES ON A WRONG REASON** | The real reason is structural (both arms include the row identically). The level tuple is incidental. |
| 9 | *blast* B11 / *adversary*: "the Shoal Cave rejection is DIRECT precedent for **exactly** this blast radius" | ⚠ **OVERSTATED — cite and DISTINGUISH** | `06-DECISIONS-LOG.md:1791`'s two named grounds are both answered: "no per-consumer filter" → `AREA_PREREQ` is that filter and it demonstrably works for `best_training_area`; "no `NO_RETURN_GROUNDS` entry" → the return leg is driven. Shoal's decisive reasons (KI-73 geometry, the RTC tide gate) have no Victory Road analogue. The **obligation to cite it stands** (CLAUDE.md rule 11). |
| 10 | *blast* B18's support: `story_harness.py:15597` "(10 entries, ceiling L19-22 at ROUTE111)" | ⛔ **THE CITED SOURCE IS ITSELF FALSE** | 10 entries ✓ (`training_areas.py:64-91`); ceiling is `ROUTE121 (25,28)` at `:89`, or `ROUTE117 (13,14)` at `:68` under `allow=None`. Neither reading gives "L19-22 at ROUTE111". The clause actually relied on (`:15598`) is correct. |
| 11 | *blast* B16's support sentence: "the only non-`.py` file containing `TRAINING_GRASS` is `probe_dive_learner.txt`" | ⛔ **FALSE, and structurally unprovable by its own command** (a `--include=*.py` grep cannot return a non-`.py` file). 20+ `.md` files contain it. | The conclusion ("nothing serialises the table") survives — I re-ran the serialisation grep: zero hits. |
| 12 | Citation drift: 6 `region_reach`/`training_areas`/`story_mode` cites off by 1-8 lines; `modules/story/debug_logger.py` does not exist (it is `modules/debug_logger.py`) | ⚠ substance holds, precision does not | Flagged, not fatal — `audit_doc_citations.py:64` `TOLERANCE = 2`. |

**Withdrawn from the task brief itself (the requester's own premises):**

| brief says | measured | source |
|---|---|---|
| "variant A: `allow=None` returns VICTORY_ROAD_1F for **L40+**" | **L35+** | `training_areas.py:501` `if team_level < lo - 1` admits L35 for `lo=36`; `:509` `score = (abs(hi - team_level), -hi)` gives \|40−35\|=5 < \|28−35\|=7. Independently replicated by **two** of the three verification passes, **and the requester's own punch list says so**: `03-PUNCH-LIST.md` *"it returns VICTORY_ROAD_1F for **L35 through L90**"*. |
| "variant B … a permissive allow returns VICTORY_ROAD_1F for L40+. Safe, but **only helps callers that pass an allow**" | The caveat is **vacuous** (all 4 production sites pass one) and the real limitation is the opposite: **every** production `allow` routes through a gate that can never open | §3 |
| "`AREA_PREREQ` … the conservative `allow=None` default refuses to propose it on a guess" | True for `best_training_area` and `counter_plan`; **false for `best_training_grass`** (`:248` — no `allow is None` branch, by documented design at `:213-219`) | §4 row 2 |
| "two DATA edits, no logic change" | **10 readers**, two of them whitelists deciding where the bot may *walk*; one of them (`_hm_hunting_grounds`) has no reachability gate at all | §4 |

**Nothing else was killed.** Findings that survived every pass and my own re-check: the waterfall-gate mechanism, `_gate_key` symmetry, `_resolve_caps`' four keys, `_counter_area_allowed` ignoring `prereq`, the `best_training_grass` asymmetry, the HM-learner ordering, the `POKEBOT_HUNT_ANYGROUND` widening, the `counter_plan` tier delta, drift = 0, the gate survey, the scalar helpers, the stale prose list, and both honest failed attacks (§2).

---

## 8. IS THERE A SIMPLER FIX? — could the Ch24 leg just pass `grass=` explicitly?

**Directly: yes — technically it is strictly cheaper, it is the shape that already ships, and it is the *only* option that works at the location RULING 5 names. But it is the workaround the ruling explicitly rejected, and it does not close the item.**

| | pass `grass=` in the Ch24 leg | the data change (variant B, 2 edits) | the data change + reachability (5 edits + 2 code fixes) |
|---|---|---|---|
| Works at the ruled location (League lobby, post-`heal_at_league`) | **YES** | **NO** — picker returns `None` (waterfall gate + 4-hop budget) | **YES**, if both blockers are fixed |
| Blast radius | **ZERO** — no table consumer touched | 10 readers, 1 ungated | same, plus `region_reach` semantics change globally |
| Precedent in-tree | VERIFIED `victory_road.py:2087-2090` `train_team(target, slots={0}, grass=TRAIN_SPOT_1F, heal_center=PokemonCenter.EvergrandeCity,)` | `training_areas.py:108-111` explicitly forbids *"a `best_training_grass` pick from across Hoenn"* for these rows | — |
| Does Ch24 consult the picker today? | **NO** — VERIFIED `grep -n "TRAIN_SPOT\|best_training\|train_team(" modules/story/pokemon_league.py` → **nothing** | | |
| Against the ruling? | **YES** — VERIFIED `06-DECISIONS-LOG.md:6294` *"the leg should be free to pick the best ground in the game at that point, not just Victory Road's"*; `03-PUNCH-LIST.md:634` *"Our recorded response was a harness comment '⛔ never "improve" this by asking the table for the grind tile' — i.e. we routed AROUND the defect. **The ruling says fix the TABLE.**"* | satisfies the letter, not the effect | satisfies both |

**Recommended sequencing** (a note, not a ruling):

1. **UNBLOCK now** — the Ch24 leg passes `grass=TRAIN_SPOT_1F, heal_center=PokemonCenter.EvergrandeCity`, cloning `victory_road.py:2088`. Zero blast radius, works today, honestly labelled a workaround in `06-DECISIONS-LOG` so the next agent does not mistake it for the answer.
2. **THE ITEM** (`#24-trainingbrackets`) is *not* the two data edits. It is: fix `_resolve_caps` to emit `"waterfall"` (one line, fail-safe — `_live_capability` requires badge **and** a party mon with the move), then decide what `_MAX_TRAINING_TRAVEL_LEGS = 4` should be for an endgame grind, **then** ship the five-part diff in §5. Measure R1 first — the whole predicate axis rests on one 2026-07-26 probe comment that nobody in four passes could re-derive from repo alone.
3. ⛔ **Do not ship the two edits as "two data edits, no logic change, safe."** The sentence is defensible on the evidence; the *implication* — that it fixes the L13-14-wilds-for-a-L53-party defect — is not. It fixes nothing until `_resolve_caps` and the hop budget move.
