# P11-1, the slow dark GRANITE CAVE crossing: a diagnosis, 2026-11-09 (read-only; nothing built)

> A NOTE, not a source of truth (`00-READ-THIS-FIRST.md`). One analyst, read-only, against branch `wip/ch6-ch7`
> (`58fd4778`) and the records of development probes #107 and #111 (each one trajectory per start, never a rate).
> Headline, with its caveat: most of the extra frames are WILD BATTLES met on 3-4x the steps; the steps come from an
> explorer with no dark mode (an unseen tile one step away outscores a ladder it can see) and from static ladder
> knowledge the AI already may use (`knowledge/world/maps.json`, classified `ai`) but no loader reads. The step counts of
> the options are an OFFLINE MODEL (`dark_sim.py`) fitted to the two probes, not measurements. Recommendation: a static
> "way through" fact plus "a lit ladder beats the frontier on a dark map" (options B + A), proven by the driver A/B in
> section (4). The analysis scripts are appended as they ran; their `s53/` paths are the session's scratch folder.


## P11-1 diagnosis: why the dark GRANITE CAVE B1F/B2F crossing is 2.6x to 11x slower (read only, 2026-11-09)

Scope: probe 11 (ledger #111, worktree wf_e7452923-f06-3 at b7c11490) against probe #107 (round 4, the eyes saw the whole
window). Nothing was changed or built. Tools written here (all read only, in this folder): `cave_frames.py` (frames by mode,
frontier distances, steps, revisits), `ladder_seen.py` (per stay on a floor: when each ladder was first in the 3x3 lit window,
and which ladder it left by), `dark_sim.py` (an OFFLINE MODEL of the explorer on the pinned decomp's layouts. It is a model,
not the AI's code).

### (1) Where the extra frames go (measured from each run's actions.jsonl, the AI's own records)

Frames inside the B1F/B2F windows, by the mode in each record's digest (`cave_frames.py`):

| run | total | battle | overworld (walking) | menu | wild battles | cave steps | distinct tiles | revisits |
|---|---|---|---|---|---|---|---|---|
| #111 C1 | 57,624 | 41,425 (72%) | 15,165 | 519 | 29 | 564 | 311 | 253 |
| #107 C1 | 21,945 | 16,979 | 4,283 | 350 | 11 | 156 | 135 | 21 |
| #111 C2 (4 passes) | 93,947 | 70,737 (75%) | 21,227 | 1,311 | 45 | 844 | 344 | 500 |
| #107 C2 | 12,811 | 8,396 | 4,040 | 78 | 6 | 160 | 136 | 24 |
| #111 C3 | 77,029 | 62,338 (81%) | 13,820 | 518 | 34 | 478 | 290 | 188 |
| #107 C3 | 6,832 | 4,316 | 2,461 | 0 | 2 | 118 | 114 | 4 |

(C2's window sum is 117,499. The extra 23,595 is the gaps between its 4 passes, which the script attributed to the last
record before each gap. It is left out above.)

- **The extra frames are mostly wild battles, and the battles follow from extra STEPS.** Of the extra frames, battle accounts
  for C1 +24.4k of +35.7k (68%), C2 +62.3k of +81.1k (77%) and C3 +58.0k of +70.2k (83%). Walking accounts for the rest
  (+10.9k, +17.2k, +11.4k). The encounter rate per step is NOT higher: 5.1, 5.3 and 7.1 battles per 100 steps against
  7.1, 3.8 and 1.7 in #107. A battle costs about 1,400 to 1,800 frames. The AI simply walks 3.6x, 5.3x and 4.1x as many
  steps, so it meets 3x to 17x as many wild Pokemon.
- **The frontier walks are 1 to 3 tiles long.** C1 had 221 of its 255 frontier decides at 1 to 3 tiles from the player
  (C2 190 of 234, C3 206 of 235). In #107 there were 0 of 15, 13 and 14: every target there was 4 or more tiles away and
  most were 7 or more. The median gap from one frontier decide to the next decide is 16 frames, which is ONE step (#107:
  84, 155 and 89). The AI re-decides on every step.
- **Back-tracking:** 253, 500 and 188 tile revisits against 21, 24 and 4. It covers 2.1x to 2.5x as many distinct tiles
  (311/344/290 vs 135/136/114), because it searches side pockets and dead ends.
- **The budgets are a SYMPTOM, not a cost.** The go goal (`deliver MR. STONE's LETTER ... to GRANITE_CAVE_STEVENS_ROOM (by
  looking around: not told yet)`) counts battle frames against its 9,000-frame budget, so it runs out after 11 to 36
  battles. The same goal is then re-issued (C1 L2741 then L2744), or "put aside" for a 2,400-frame look_around (C1 L4515)
  that runs the SAME explorer. No frames are lost to the budgets themselves.
- **Per floor** (`ladder_seen.py`; "lit" means the player first stood within 1 tile of the ladder):

| stay | #111 C1 | #111 C2 | #111 C3 | #107 C1/C2/C3 |
|---|---|---|---|---|
| B1F (4,21)->(28,21) | 170 steps, 18,076 fr; ladder lit at +4,360 | 100 steps, 16,537 fr; lit at +2,979 | 100 steps, 17,039 fr; lit at +14,934 | 88/90/50 steps, 14.7k/9.2k/5.5k fr |
| **B2F (28,21)->(29,13)** | **349 steps, 36,093 fr**; lit at +34,618 | 274 steps then went BACK by (28,21) (29,275 fr); 2nd try 207 steps, 25,904 fr | **333 steps, 53,087 fr**; lit at +50,850 | **61/63/61 steps, 7.0k/3.4k/1.1k fr** |
| B1F (29,13)->(25,13) | 42 steps, 3,372 fr; lit at +152 | 42/46 steps | 42 steps, 6,820 fr; lit at +148 | 4/4/4 steps, 154/163/140 fr |

  **B2F is most of the slowdown:** C1 +29.0k of +35.7k (81%), C2 about +51.8k of +81k (64%; its B1F stays are most of the
  rest), C3 +52.0k of +70.2k (74%). On B2F the exit ladder (29,13) lies 8 tiles north of the arrival ladder (28,21), but the
  AI lights it only at the END of the stay. That is a blind search. On the last B1F stay the ladder (25,13) is lit within
  150 frames, yet the AI walks 42 steps before it takes it, and on the first B1F stay C1 and C2 left a lit ladder for about
  13.5k frames. In both cases the AI has seen the way on and still chooses to explore.
  C2's first B2F pass returned to B1F the way it came (it ended with the "go | stuck" at L6346 and the "lost" decides toward
  PETALBURG), which belongs to P11-2 and P11-3.

### (2) The mechanism

- **The eyes:** on a dark map only a 24 px circle round the screen's middle is drawn (`eyes/view.py:122-137`,
  `FLASH_RADIUS[7] = 24`; `host/eyes.py:104-113`). The 8 neighbouring tile centres lie at 16 and 22.6 px and the next ring at
  32 px, so the AI sees a **3x3 window**. Tiles outside it stay unknown (`View.rows` None) and the world memory never learns
  them.
- **The explorer has no dark mode.** `brain/` contains no `lit`, `dark` or `requires_flash` logic; the only mention is a
  comment at goals.py:1328. It scores the dark exactly as it scores daylight:
  - The frontier is every seen walkable tile with unseen neighbours (`world/memory.py:302-305`).
  - A frontier tile's value is `weights.frontier * (1 + unknown/3)` (`brain/explore.py:589-595`), 13.3 to 20 after
    `VALUE_TILES = 10` (:123).
  - The score is `10*value - walk + away` (:513), and `away` (Story 0.3 per tile, capped at 20 tiles: :159, :163) applies
    to frontier, road and grass only (:511-512).
  - An unused exit (a ladder) is worth `weights.door` = 0.8, which is 8 (:557-558). Its walk includes +3 to stand beside
    it (:470).
  - In daylight one look reveals about 15x10 tiles, so the nearby frontier runs out at once and the ladder wins. In the dark
    an unseen tile one step away always scores more than a seen ladder.
  - Logged proof, C1's last B1F stay: the frontier decides score 14.3 to 25.0 (L5286-L5512), and the AI walks
    (28,12)->(24,12), past the ladder at (25,13). The door is chosen only at L5517 (`door ... sc=5.0`), once every pocket
    nearby has been seen.
- **It uses NO static knowledge of the cave's layout. It walks only on what it has lit.**
  - `knowledge/world/maps.json` has no layout. Its keys per map are id, name, map_type, region_map_section, allow_*,
    requires_flash, connections, warps, trainers, item_balls and hidden_items.
  - It DOES hold every ladder's coordinates and destination, `warps[].x/.y/.dest_map`. Those are classified `ai`, "a guide's
    map; RULING 45: coordinates kept" (`gates/check_fairness.py:231-237`). `requires_flash` is classified too (:222).
  - But the only loader, `knowledge/atlas.py`, reads just `id` and `map_type`, plus bosses.json (atlas.py:12-16, 37). So the
    ladder coordinates are allowed and on disk, yet unused.
  - No file holds the collision layout. There is no memory across games: a grep for any cross-game store found none.
  - The one precedent for steering by static knowledge is `gym_back` (goals.py:867).
- **An offline model reproduces both probes** (`dark_sim.py`: the explorer's scoring, a 3x3 window, passability from the
  pinned `data/layouts/GraniteCave_B{1,2}F/map.bin`).
  - Today's policy (P0) takes 114, 217 and 40 steps for the three stays. Measured: 100 to 170, 207 to 349, and 42 to 46.
  - The shortest walk on the static layout (P3) takes 42, 61 and 4 steps. #107 measured 50 to 90, **61/63/61** and **4/4/4**.

### (3) Options (each: what a person does, RULING 40 fit, modelled steps B1F + B2F + B1F; today P0 = 114 + 217 + 40 = 371)

- **A. A lit ladder outranks the frontier on a dark map** (only `explore.py` scoring; no knowledge).
  - What a person does: in a dark cave they take the ladder they find.
  - RULING 40: fits, because it uses only what is seen.
  - Model P1: 108 + 211 + 4 = 323 (-13%). It fixes the last B1F stay (40 -> 4) and the cases where C1 and C2 left a lit
    ladder on the first B1F stay (about 13.5k frames each).
  - It does nothing for B2F, the largest share.
  - Risk: B1F has 7 ladders, so it could take a wrong, unused one. The model never did.
- **B. The way through, from static knowledge** (a seasoned player's "the ladder down is east on B1F, the one up is north on
  B2F, then west").
  - The ladder coordinates are already AI-classified in maps.json. WHICH ladder leads on needs connectivity: an extractor
    on the test side computes it from the pinned layout and ships only the result, as a new classified fact per dark map.
  - On a dark map the explorer adds a route target at that ladder's known coordinates. The navigator plans through unseen
    tiles at `UNKNOWN_COST` 3 (`brain/navigator.py:186, :322`, which already exist) and re-plans as walls are lit.
  - RULING 40: fits, because it is static and is "the way through a cave". It mirrors `gym_back`.
  - Model P2: 70 + 99 + 4 = 173 (-53%).
- **C. The static layout for dark maps** (a guide's full map).
  - The navigator plans over the known passability, as #107 effectively did. Objects, people and items stay visible only
    in the lit circle.
  - RULING 40: fits; the task statement lists layouts as allowed.
  - Model P3: 42 + 61 + 4 = 107 (-71%), about #107's speed.
  - Cost: a new world file (32x26 per dark map), RULE B classification, a loader, and a rule that static tiles are
    planning knowledge, not sight. Static tiles also empty the frontier, so the change must be confined to
    `requires_flash` maps.
- **D. A frontier rule for the dark** (keep heading, prefer long corridors, discount a dark unseen tile's value).
  - RULING 40: fully fair.
  - Not modelled. It is the least certain option: today's B2F already hits mostly 3-unseen-tile frontiers, and the issue is
    direction, not tie-breaks.
- **E. FLASH first.**
  - The HM comes from the hiker on lit 1F (`data/maps/GraniteCave_1F/scripts.inc:9`, `giveitem ITEM_HM_FLASH`).
  - Using it in the field needs **BADGE02** (`src/party_menu.c:121` `FIELD_MOVE_FLASH // FLAG_BADGE02_GET`, enforced at
    :3725), so only after BRAWLY, whose gym is itself dark.
  - It works only on a `cave` map (`src/fldeff_flash.c:83` checks `gMapHeader.cave`), and it sets flash level 1, a 72 px
    radius that covers nearly the whole screen (`eyes/view.py` comment and `FLASH_RADIUS[1]`).
  - C1 and C3 crossed the cave BEFORE the gym (steven f850542 < gym f863623; f939329 < f947850). So FLASH cannot help their
    crossing unless the story order changes.
  - It also needs a FLASH-compatible party member (not checked) and HM teaching plus field-move menus, which do not exist
    yet. That is a large build, though one needed later for CUT, ROCK SMASH and the others.
  - RULING 40: fits.
- **F. Accept it.**
  - Cost: +36k to +81k frames per crossing, 3% to 7% of a 1.2M-frame run. All 3 runs crossed, and 2 of 3 earned BADGE02.
    C1's 3 losses to BRAWLY are a separate problem.
  - A first-timer in the dark also wanders, and the extra battles give EXP.
  - The same pattern will cost more on VICTORY ROAD B1F/B2F (also `requires_flash`).

### (4) Recommendation and the smallest test

**Recommend B, with A folded in.** B removes most of the B2F blind search, the largest share. It uses knowledge RULING 40
names, the way through a cave, at a guide's level of detail rather than a tile map, and it keeps the round-7 rule: the AI
still SEES only the lit circle. A covers the "lit ladder ignored" cases for free. If B's live arm leaves B2F above about
150 steps, escalate to C.

The smallest test, a DRIVER (correctness) rather than a batch:

0. **Offline (done, seconds):** `dark_sim.py`. The CONTROL P0 reproduces today's measured steps, P3 reproduces #107's, and
   P2 gives the prediction to beat: 99 B2F steps.
1. **Live A/B on one start and seed** (C3 had the fastest crossing in #107 and the slowest in #111). Run from the #111 stage's
   start save to the first frame on 1F (35,3), capped at 250k frames.
   - FIX arm: B plus A.
   - FAULT arm: the same code with the way-through fact removed, so the loader returns None, which is today's behaviour.
   - **Discriminator, computed first on the FAULT arm:** the B2F ladder (29,13) must be lit only late in the stay (today:
     +25k to +51k frames). If it is lit early, the arms cannot differ and the A/B is vacuous.
   - Pass:
     - FIX B2F steps at most about 120 (model 99; FAULT expected 200+).
     - FIX last-B1F steps at most 6 (FAULT about 42).
     - Count steps from the AI's own position digests, not frames, because battle noise is large.
2. **CONTROL on a lit map:** on GRANITE CAVE 1F and ROUTE 106, the FIX arm's decide records equal the FAULT arm's (the fact
   applies only on `requires_flash` maps).
3. **Fairness gate:** `check_fairness.py` RULE B passes with the new keys classified. A developer key planted under the new
   fact must FAIL the gate (mutant).

## Appendix: `cave_frames.py` (as it ran)

```python
"""Read only: where the frames go inside each GRANITE CAVE B1F/B2F pass (judge json cave_passes windows).
Frames are attributed to the mode in each record's digest (battle/menu/text/overworld/...) by the gap to the next record.
Frontier decides: count, Manhattan distance player->target, frames until the next decide (overworld walk per target).
Tiles: steps (position changes) vs distinct tiles on the cave maps (back-tracking = revisits).
usage: cave_frames.py JUDGE.json OUT_BATCH_DIR"""
import collections
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2])
HEAD = re.compile(r"^f(\d+) (\S+) .*?GRANITE CAVE\((\d+),(\d+)\) xy=\((-?\d+),(-?\d+)\)")
CAVE = {(24, 8): "B1F", (24, 9): "B2F"}

for run in report["runs"]:
    windows = [(c["entered"], c["left"] or 10 ** 9) for c in run["cave_passes"]]
    recs = []
    with (out / run["name"] / "actions.jsonl").open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            rec = json.loads(line)
            f = rec.get("frame")
            if not isinstance(f, int):
                continue
            if any(lo <= f <= hi for lo, hi in windows):
                recs.append((line_no, rec))
            elif recs and f > max(hi for _, hi in windows):
                recs.append((line_no, rec))  # one record past the end closes the last gap
                break
    mode_frames = collections.Counter()
    map_mode = collections.Counter()
    dist_hist = collections.Counter()
    kinds = collections.Counter()
    walk_per_target = []
    steps, tiles, last_pos = 0, collections.Counter(), None
    last_decide = None
    for i, (ln, rec) in enumerate(recs[:-1]):
        f = rec["frame"]
        gap = recs[i + 1][1]["frame"] - f
        m = HEAD.match(str(rec.get("digest") or ""))
        mode = str(rec.get("digest") or "").split(" ")[1] if rec.get("digest") else "?"
        mp = CAVE.get((int(m.group(3)), int(m.group(4)))) if m else None
        mode_frames[mode] += gap
        map_mode[(mp or "other-map", mode)] += gap
        if m and mp and mode == "overworld":
            pos = (mp, int(m.group(5)), int(m.group(6)))
            if pos != last_pos:
                steps += 1
                tiles[pos] += 1
                last_pos = pos
        if rec.get("decision") == "decide":
            ex = rec.get("extra") or {}
            kind = ex.get("kind")
            kinds[kind] += 1
            if last_decide is not None:
                walk_per_target.append((last_decide[1], f - last_decide[0]))
            last_decide = (f, kind)
            if kind == "frontier" and ex.get("player") and ex.get("target"):
                d = abs(ex["player"][0] - ex["target"][0]) + abs(ex["player"][1] - ex["target"][1])
                dist_hist["1-3" if d <= 3 else "4-6" if d <= 6 else "7-10" if d <= 10 else "11+"] += 1
    total = sum(mode_frames.values())
    fr_gaps = sorted(g for k, g in walk_per_target if k == "frontier")
    med = fr_gaps[len(fr_gaps) // 2] if fr_gaps else 0
    revisit = sum(c - 1 for c in tiles.values())
    print(f"== {run['name']} passes={len(windows)} judge_frames={run.get('cave_frames_total')} window_frames={total}")
    print("   frames by mode:", dict(mode_frames.most_common()))
    print("   by (map, mode):", {f"{a}/{b}": v for (a, b), v in sorted(map_mode.items()) if v > 500})
    print("   decide kinds:", dict(kinds.most_common()))
    print("   frontier distance player->target:", dict(sorted(dist_hist.items())))
    print(f"   frames between a frontier decide and the next decide: n={len(fr_gaps)} median={med} "
          f"sum={sum(fr_gaps)} p90={fr_gaps[int(len(fr_gaps) * 0.9)] if fr_gaps else 0}")
    print(f"   cave overworld steps={steps} distinct tiles={len(tiles)} revisits={revisit} "
          f"(B1F {sum(1 for t in tiles if t[0]=='B1F')}, B2F {sum(1 for t in tiles if t[0]=='B2F')} tiles)")
    print("   wild battles (judge):", [c.get("wild_battles") for c in run["cave_passes"]],
          "maps:", [c.get("maps") for c in run["cave_passes"]])
```

## Appendix: `ladder_seen.py` (as it ran)

```python
"""Read only: per stay on GRANITE CAVE B1F/B2F, when the player first stood within 1 tile (Chebyshev) of each ladder (the
lit circle shows it then) and which ladder it left by, with steps and frames of the stay. Ladders: knowledge/world/maps.json
warps (static). usage: ladder_seen.py JUDGE.json OUT_BATCH_DIR MAPS_JSON"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2])
maps = {m["id"]: m for m in json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))["maps"]}
WARPS = {k: [(w["x"], w["y"], w["dest_map"].replace("MAP_GRANITE_CAVE_", "")) for w in maps[v]["warps"]]
         for k, v in (("B1F", "MAP_GRANITE_CAVE_B1F"), ("B2F", "MAP_GRANITE_CAVE_B2F"))}
HEAD = re.compile(r"^f(\d+) (\S+) .*?\((\d+),(\d+)\) xy=\((-?\d+),(-?\d+)\)")
CAVE = {(24, 8): "B1F", (24, 9): "B2F"}

for run in report["runs"]:
    lo = min(c["entered"] for c in run["cave_passes"])
    hi = max((c["left"] or 10 ** 9) for c in run["cave_passes"])
    print(f"== {run['name']}")
    stay = None

    def close(s):
        if s is None:
            return
        last = s["last"]
        left_by = [w for w in WARPS[s["map"]] if (w[0], w[1]) == last]
        seen = " ".join(f"{w[0]},{w[1]}->{w[2]}@+{f - s['f0']}" for w, f in s["seen"].items())
        print(f"  {s['map']} f{s['f0']}..f{s['f1']} ({s['f1'] - s['f0']} fr, {s['steps']} steps) in at {s['first']} "
              f"left by {left_by[0][:2] if left_by else last} -> {left_by[0][2] if left_by else '?'}; ladders lit (frames after "
              f"entering): {seen}")

    with (out / run["name"] / "actions.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            f = rec.get("frame")
            if not isinstance(f, int) or f < lo:
                continue
            if f > hi:
                break
            m = HEAD.match(str(rec.get("digest") or ""))
            if not m:
                continue
            mp = CAVE.get((int(m.group(3)), int(m.group(4))))
            pos = (int(m.group(5)), int(m.group(6)))
            if stay is not None and mp != stay["map"]:
                close(stay)
                stay = None
            if mp is None:
                continue
            if stay is None:
                stay = {"map": mp, "f0": f, "first": pos, "last": pos, "steps": 0, "seen": {}, "f1": f}
            if pos != stay["last"]:
                stay["steps"] += 1
            stay["last"], stay["f1"] = pos, f
            for w in WARPS[mp]:
                if max(abs(w[0] - pos[0]), abs(w[1] - pos[1])) <= 1 and w not in stay["seen"]:
                    stay["seen"][w] = f
    close(stay)
```

## Appendix: `dark_sim.py` (as it ran)

```python
"""Read only, OFFLINE MODEL (not the AI's code): the three dark legs of GRANITE CAVE on the pinned decomp's layouts, walked by
policies that copy `brain/explore.py` candidates' scoring (VALUE_TILES 10, frontier 1+u/3, door 0.8 (Story), stand cost +3,
away 0.3 per tile from the entry capped 20) with a 3x3 lit window (24 px round the screen's middle: the 8 neighbours lie at
16 and 22.6 px, the next ring at 32 px). Passable = collision bits 0 (elevation, cracked floors, boulders ignored).
Policies: P0 CONTROL (today's greedy frontier), P1 (a lit unused ladder outranks the frontier on a dark map), P2 (a pull to
the KNOWN coordinates of the right ladder, planned through unseen tiles at cost 3, as navigator.UNKNOWN_COST), P3 (the static
layout known: the shortest walk). usage: dark_sim.py DECOMP_DIR"""
import heapq
import sys
from collections import deque
from pathlib import Path

D = Path(sys.argv[1])
W, H = 32, 26
LEGS = [("B1F", (4, 21), (28, 21)), ("B2F", (28, 21), (29, 13)), ("B1F", (29, 13), (25, 13))]
WARPS = {"B1F": [(25, 13), (4, 21), (29, 13), (28, 21), (8, 5), (12, 3), (29, 2)],
         "B2F": [(29, 13), (28, 21), (8, 5), (12, 3), (29, 2)]}


def load(name):
    raw = (D / "data/layouts" / f"GraniteCave_{name}" / "map.bin").read_bytes()
    vals = [raw[i] | raw[i + 1] << 8 for i in range(0, len(raw), 2)]
    return {(x, y): ((vals[y * W + x] >> 10) & 3) == 0 for y in range(H) for x in range(W)}


N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def bfs(pas, start, ok):
    dist = {start: 0}
    q = deque([start])
    while q:
        c = q.popleft()
        for dx, dy in N4:
            n = (c[0] + dx, c[1] + dy)
            if n not in dist and ok(n):
                dist[n] = dist[c] + 1
                q.append(n)
    return dist


def run(name, start, goal, policy, cap=3000):
    pas = load(name)
    known = {}

    def reveal(p):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                t = (p[0] + dx, p[1] + dy)
                if t in pas:
                    known[t] = pas[t]

    pos, steps, entry, used = start, 0, start, {start}
    reveal(pos)
    while steps < cap:
        if pos == goal:
            return steps, "right ladder"
        if pos in WARPS[name] and pos not in used:
            return steps, f"WRONG ladder {pos}"
        other = set(WARPS[name]) - {goal} - {pos}
        reach = bfs(pas, pos, lambda t: known.get(t, False) and t not in WARPS[name])
        for wp in WARPS[name]:
            if wp in known and wp not in reach:
                near = [reach[(wp[0] + dx, wp[1] + dy)] for dx, dy in N4 if (wp[0] + dx, wp[1] + dy) in reach]
                if near:
                    reach[wp] = min(near) + 1
        if policy == "P3":
            path = bfs(pas, goal, lambda t: pas.get(t, False) and t not in other)
            nxt = min((n for n in ((pos[0] + dx, pos[1] + dy) for dx, dy in N4) if n in path), key=lambda n: path[n])
        elif policy == "P2":
            # A* from goal back over known-passable (1) and unknown (3) tiles; step to the neighbour with the least cost-to-go
            cost = {goal: 0.0}
            hq = [(0.0, goal)]
            while hq:
                c0, c = heapq.heappop(hq)
                if c0 > cost.get(c, 1e9):
                    continue
                for dx, dy in N4:
                    n = (c[0] + dx, c[1] + dy)
                    if n not in pas or known.get(n) is False or n in other:
                        continue
                    nc = c0 + (1.0 if n in known else 3.0)
                    if nc < cost.get(n, 1e9):
                        cost[n] = nc
                        heapq.heappush(hq, (nc, n))
            opts = [n for n in ((pos[0] + dx, pos[1] + dy) for dx, dy in N4) if known.get(n) and n in cost]
            if not opts:
                return steps, "boxed in"
            nxt = min(opts, key=lambda n: (cost[n], n))
        else:
            best = None
            for t, w in reach.items():
                if t == pos:
                    continue
                u = sum(1 for dx, dy in N4 if (t[0] + dx, t[1] + dy) not in known)
                if u:
                    s = 10 * (1 + u / 3) - w + 0.3 * min(abs(t[0] - entry[0]) + abs(t[1] - entry[1]), 20)
                    best = max(best or (s, t), (s, t))
            for wp in WARPS[name]:
                if wp in reach and wp not in used:
                    s = (30.0 if policy == "P1" else 8.0) - (reach[wp] + 3)
                    best = max(best or (s, wp), (s, wp))
            if best is None:
                return steps, "nothing left"
            tgt = best[1]
            back = bfs(pas, tgt, lambda t: known.get(t, False) and t not in WARPS[name])
            nxt = min((n for n in ((pos[0] + dx, pos[1] + dy) for dx, dy in N4) if n in back), key=lambda n: (back[n], n))
        pos = nxt
        steps += 1
        reveal(pos)
    return steps, "cap"


for name, a, b in LEGS:
    row = [f"{name} {a}->{b}:"]
    for pol in ("P0", "P1", "P2", "P3"):
        s, how = run(name, a, b, pol)
        row.append(f"{pol} {s} steps ({how})")
    print("  ".join(row))
```
