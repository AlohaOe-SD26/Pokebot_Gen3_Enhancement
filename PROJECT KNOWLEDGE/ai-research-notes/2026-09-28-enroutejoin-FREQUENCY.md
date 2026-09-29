# 2026-09-28 — NOTE (a Claude subagent's batch-log count, not verified truth): how often a hunt's WALK meets a wild battle

> For `#27-enroutejoin`. Read-only analysis of the endless-batch debug logs in
> `sandbox-pokebot/profiles/endless-P{1..4}-*/debug-logs/Old/` (main checkout). Scripts and per-walk detail are in the
> agent's scratch directory (`C:/Users/Ripto/AppData/Local/Temp/p2b-freq/`: `walkfreq.py`, `perhunt.py`,
> `detail_all.txt`, `compact_b09*.txt`). None of it is committed.

## HEADLINE: walk battles are COMMON, not rare

⛔ This refutes my own inference, made before the count, that `_navigate_riding_out(..., avoid_encounters=True)` makes
walk battles rare. That routing cannot avoid Petalburg Woods, Rusturf Tunnel, the Fiery Path floor, the Route
101/103 grass, or the water routes.

| Group (batches b0926 + b0927) | ≥ 1 walk battle | …at party < 6 and full HP | …and a new species, > 10 balls |
|---|---|---|---|
| HM, 47 hunts | 40–45 (85–96%) | 12–15 (26–32%) | 4–6 (9–13%) |
| Counter, 37 hunts | 28–31 (76–84%) | 19–22 (51–59%) | 14–16 (38–43%) |
| **All, 84 hunts** | **68–76 (81–90%)** | **31–37 (37–44%)** | **18–22 (21–26%)** |

Across all three batches (235 hunts, adding b0915), the three columns read 85–91%, 40–43% and 14–17%.

**The last column is the case where `POKEBOT_R20_OPENFENCE` would have caught a new species INTO THE PARTY during the
walk.** It leans high: the count does not model the expected-throws gate, the attempt cap, the training flag, or
whether the catch would succeed.

## DETAILS THE AGENT REPORTED

- **Where the walk battles were:**
  - Machop counter walks: Petalburg Woods 23, Route 116 18, Rusturf Tunnel 28, Fiery Path 6;
  - Dive walks: Routes 118–124;
  - the Surf Route 103 walks: Route 101 grass 19, Route 103 grass 19.
- **The hunt target itself was met on the walk before arming.** For example, Machop at Fiery Path at party 4 and full
  HP (`P2-…-20260927-181845.log:12849`). The flag would have caught it into the party, and the counter hunt's
  after-walk PID snapshot would then exclude it.
- **What protects the Surf hunt is HP, not routing.** It starts right after Norman without a heal (Mightyena at
  0/108), so only 1–4 of 31 walks had a full-HP battle.
- **Hidden hunt starts.** When balls are ≤ 1, the ball-buying message overwrites the hunt message in the same frame. The
  agent recovered 24 such hunts.

## METHOD LIMITS (the agent's own)

- **The walk window** runs from the hunt message to the first exact sighting of the player on the spin tile.
- **Ambiguity:** the first battle ON the tile could be the last walk step or the first spin turn, and battles on the
  hunt map with no logged position are ambiguous too. Hence the ranges.
- **Trainer battles are excluded.**
- **"New species"** is rebuilt from `[DEX]` lines. It agrees with all 860 fence verdicts.
- **The ball count includes the Master Ball.**
- **The Surf spin tile moved** to ROUTE101 (12, 10) on 2026-09-28 (`#27-r101standstill`), and no batch has run it yet.
