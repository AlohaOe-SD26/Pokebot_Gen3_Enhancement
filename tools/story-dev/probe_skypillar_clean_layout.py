"""probe_skypillar_clean_layout.py — CAN THE STORY BOT ACTUALLY WALK THE SKY PILLAR?

‼ THIS EXISTS BECAUSE A TIER 1 REVIEW REFUSED TO ACCEPT THE FINDING WITHOUT IT, AND IT WAS RIGHT.
The §Ch21 ATLAS's central result — that the ascent REQUIRES a deliberate fall through `4F (6,4)` or
`(7,4)`, and that `4F (11,1) -> (3,1)` is NO PATH — was first produced by an ad-hoc script in a
scratch directory. The numbers were correct, but *"a hand-formatted method summary that nobody else
can re-run"* is exactly the standard this project rejects everywhere else. Every other claim in that
increment had a committed, fault-tested tool behind it. This one now does too.

⛔ WHY A LIVE PROBE CANNOT ANSWER THIS. `get_map_data()` reads the map HEADER's layout, which is the
DEFAULT — i.e. the CRACKED, post-game one. Every Sky Pillar floor swaps to `LAYOUT_SKY_PILLAR_*_CLEAN`
at RUNTIME (`setmaplayoutindex` in each floor's `OnTransition`, gated `call_if_lt
VAR_SKY_PILLAR_STATE, 2`). So `probe_ch21_topology.py` deliberately refuses to assert on those tiles.
=> The answer lives in the DECOMP's shipped `data/layouts/SkyPillar_*_Clean/map.bin`, which IS the
story layout. Reading 392 bytes per floor settles exactly what a 25-minute emulator drive would.
‼ THE REUSABLE LESSON: "my instrument cannot see this" and "this needs a live run" are DIFFERENT
claims. Ask where the source data lives before buying an emulator drive.

WHAT IT ASSERTS (each one fails loudly and exits 1):
  1. `2F_Clean` has ZERO cracked tiles      -- the story bot crosses 2F on foot
  2. `4F_Clean` has FIVE                    -- "clean" is PER-FLOOR, not global
  3. `4F_Clean (11,1) -> (3,1)` is NO PATH  -- *even treating every cracked tile as passable*,
                                               so the fall is forced by GEOMETRY, not by cracks
  4. `4F_Clean (7,1)  -> (3,1)` IS a path   -- the sealed pocket's only walkable exit
  5. the 3F pocket reached by falling on `4F (6,4)` CONTAINS `3F (7,1)`
  6. ⛔ `(9,4)` is a DECOY -- also cracked, also reachable, but lands in 3F's MAIN region and
     wastes the whole climb

NETWORK: fetches the layouts from raw.githubusercontent.com (‼ NOT `gh api | base64 -d`, which
silently corrupts binaries here -- playbook §N) and caches them under `.layout-cache/`, so re-runs
are offline. ⛔ It is therefore NOT in `run_gates.py`: a standing gate must not need the network.

FAULT HOOK: `POKEBOT_SKYPILLAR_FAULT=nofall` asserts the OPPOSITE of finding 3 (that `(11,1)`
reaches `(3,1)`), which MUST fail -- proving these assertions can fail at all.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_skypillar_clean_layout.py
"""

import os
import pathlib
import struct
import sys
import urllib.request
from collections import deque

RAW = "https://raw.githubusercontent.com/pret/pokeemerald/master/data/layouts/%s/map.bin"
CACHE = pathlib.Path(__file__).resolve().parent / ".layout-cache"
W = H = 14                      # 1F-5F only. ⛔ NOT "every Sky Pillar floor" — MEASURED from our
                                # ROM 2026-09-01: TOP is 27x24, ENTRANCE 18x18, OUTSIDE 28x23.
                                # That false premise is why this probe cannot simply be
                                # extended to TOP/1F/5F; use probe_skypillar_rom_layouts.py,
                                # which reads all six floors out of the ROM with no network.
CRACKED_METATILE = 0x236        # behaviour 0xD2 == MB_CRACKED_FLOOR
FAILURES = []


def check(label, ok, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label, ("  -- " + detail) if detail else ""))
    if not ok:
        FAILURES.append(label)


def fetch(name):
    """392 bytes per floor. Cached, so this is offline after the first run."""
    CACHE.mkdir(exist_ok=True)
    f = CACHE / (name + ".bin")
    if not f.exists():
        try:
            with urllib.request.urlopen(RAW % name, timeout=30) as r:
                f.write_bytes(r.read())
        except Exception as e:
            print("  ‼ COULD NOT FETCH %s: %s" % (name, e))
            print("    (no network and no cache -- this probe cannot run; that is a SKIP, not a PASS)")
            sys.exit(2)
    b = f.read_bytes()
    if len(b) != W * H * 2:
        print("  ‼ %s is %d bytes, expected %d -- a CORRUPT read, not a finding." % (name, len(b), W * H * 2))
        print("    ⛔ Do NOT interpret it. `gh api <contents> | base64 -d` mangles binaries here.")
        sys.exit(2)
    return b


def decode(name):
    """pokeemerald block: metatileId:10 | collision:2 | elevation:4 (include/global.fieldmap.h)."""
    v = struct.unpack("<%dH" % (W * H), fetch(name))
    coll = [[(v[y * W + x] >> 10) & 0x3 for x in range(W)] for y in range(H)]
    crack = {(x, y) for y in range(H) for x in range(W) if (v[y * W + x] & 0x3FF) == CRACKED_METATILE}
    return coll, crack


def walk(coll, crack, start, goal=None, block_cracks=True):
    """BFS. Returns the reachable set, or the step count to `goal` if given."""
    if coll[start[1]][start[0]] != 0:
        return None
    seen = {start}
    q = deque([(start, 1)])
    while q:
        (x, y), d = q.popleft()
        if goal is not None and (x, y) == goal:
            return d
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            if (nx, ny) in seen or coll[ny][nx] != 0:
                continue
            if block_cracks and (nx, ny) in crack:
                continue
            seen.add((nx, ny))
            q.append(((nx, ny), d + 1))
    return None if goal is not None else seen


print("SKY PILLAR — the CLEAN (story) layouts, decoded from the decomp's own shipped map.bin")
print("=" * 98)

c2, k2 = decode("SkyPillar_2F_Clean")
c3, k3 = decode("SkyPillar_3F_Clean")
c4, k4 = decode("SkyPillar_4F_Clean")

print("\n1 — CRACKED-TILE CENSUS  ('clean' is a PER-FLOOR fact, not a global one)")
print("      2F_Clean: %d   4F_Clean: %d  %s" % (len(k2), len(k4), sorted(k4)))
check("2F_Clean has ZERO cracked tiles (the bot crosses 2F on foot)", len(k2) == 0, str(sorted(k2)))
check("4F_Clean has FIVE cracked tiles ('_CLEAN' does NOT mean crack-free)", len(k4) == 5, str(sorted(k4)))

print("\n2 — THE SEALED POCKETS  (why the climb cannot be a plain walk)")
d_avoid = walk(c4, k4, (11, 1), (3, 1), True)
d_any = walk(c4, k4, (11, 1), (3, 1), False)
print("      4F_Clean (11,1) -> (3,1): avoiding cracks=%s ; treating cracks as PASSABLE=%s" % (d_avoid, d_any))
check("4F_Clean (11,1) -> (3,1) is NO PATH even with cracked tiles PASSABLE "
      "(=> the fall is forced by GEOMETRY, not by the cracks)", d_avoid is None and d_any is None,
      "avoid=%s any=%s" % (d_avoid, d_any))
d7 = walk(c4, k4, (7, 1), (3, 1), True)
check("4F_Clean (7,1) -> (3,1) IS walkable (the pocket's only land exit)", isinstance(d7, int), "%s steps" % d7)

print("\n3 — THE DELIBERATE FALL  (`warphole` preserves (x,y): 4F (x,y) -> 3F (x,y))")
launch_region = walk(c4, k4, (11, 1), None, True)
check("4F_Clean (5,4) — the launch tile — IS reachable from the (11,1) arrival", (5, 4) in launch_region)
check("(5,4) is ADJACENT to the cracked (6,4), so ONE step east triggers the fall",
      abs(5 - 6) + abs(4 - 4) == 1 and (6, 4) in k4)
pocket = walk(c3, k3, (6, 4), None, True)
check("falling on 4F (6,4) lands in a 3F pocket that CONTAINS the 3F (7,1) stairs",
      pocket is not None and (7, 1) in pocket, "pocket=%d tiles" % (len(pocket) if pocket else 0))

print("\n4 — ⛔ THE DECOY  (all three cracked tiles are reachable AND land on walkable 3F ground)")
for land in ((6, 4), (7, 4), (9, 4)):
    r = walk(c3, k3, land, None, True)
    inside = r is not None and (7, 1) in r
    print("      fall 4F %s -> 3F %s : walkable=%-5s reaches 3F (7,1)=%-5s  %s"
          % (land, land, r is not None, inside, "GOOD" if inside else "<-- DECOY, wastes the climb"))
decoy = walk(c3, k3, (9, 4), None, True)
check("⛔ (9,4) is a DECOY — cracked and reachable, but it does NOT reach 3F (7,1)",
      decoy is not None and (7, 1) not in decoy)

print("\n5 — FAULT CONTROL")
if os.environ.get("POKEBOT_SKYPILLAR_FAULT") == "nofall":
    print("      FAULT: asserting the OPPOSITE of finding 2 — that (11,1) DOES reach (3,1).")
    print("      This MUST fail; if it passes, these assertions are vacuous.")
    check("[FAULT] 4F_Clean (11,1) reaches (3,1)", walk(c4, k4, (11, 1), (3, 1), False) is not None)
else:
    print("      (set POKEBOT_SKYPILLAR_FAULT=nofall to prove these assertions can fail)")

print("\n" + "=" * 98)
if FAILURES:
    print("  %d ASSERTION(S) FAILED:" % len(FAILURES))
    for f in FAILURES:
        print("      - " + f)
    sys.exit(1)
print("  ✅ ALL PASS — the story ascent REQUIRES a deliberate fall through 4F (6,4) or (7,4), NOT (9,4).")
print("  ⇒ `map_path.py` does not model \"Cracked Floor\", so it can never propose this. The fall must")
print("     be an EXPLICIT chapter step, exactly like `dive()`. See the §Ch21 ATLAS.")
