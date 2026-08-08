"""`#24-huntreachproof`: a counter hunt may only target DRIVEN reach-and-leave evidence.

MEASURED, batch `20260808-095721` — conversion by destination:

    Machop @ FIERY_PATH   (HUNTING_GROUNDS)    5 hunts,  5 caught = 100%
    every other ground    (TRAINING_GRASS)    28 hunts,  0 caught =   0%
    `could not reach` 72 / `Could not find a path` 45 / `hunt found nothing` 0

They are TRAVEL failures. `TRAINING_GRASS` tiles were two-way swept **for training, from training
anchors**; a counter hunt fires from wherever a BOSS is fought — a different journey the sweep
never measured. `HUNTING_GROUNDS` encodes *driven* reach-and-leave evidence, has one entry, and
that entry is the only rung that converts. Reusing one whitelist for two different questions is
how a fails-closed gate quietly became fails-open.

‼ WHY NARROWING IS CORRECT HERE: the hunt is bounded to ONE attempt per boss per run, so an
unreachable destination does not cost a trek — it costs the boss. An honest immediate "no
huntable candidate" beats a cross-Hoenn journey that ends in the same stop.

‼ THIS IS A REDUCTION, NOT A CURE, AND THE FILE SAYS SO: `Numel @ FIERY_PATH` was **5 hunts, 0
caught** in the same batch, on the SAME ground Machop converts 5/5 from. Reachability is a
property of the (boss anchor → ground) PAIR, not of the ground. Full coverage needs per-pair
sweeps; this only stops the 28 known-bad ones.
"""
from __future__ import annotations
import ast, os, pathlib, re, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
TA = REPO / "sandbox-pokebot" / "modules" / "story" / "training_areas.py"
FAIL: list[str] = []

def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok: FAIL.append(label)

src = TA.read_text(encoding="utf-8")
ast.parse(src)

print("1. the gate exists and is strict BY DEFAULT")
check("hunt_ground_tile takes require_driven", "require_driven" in src)
check("it defaults to STRICT (opt-OUT, not opt-in)",
      'POKEBOT_HUNT_ANYGROUND", "0"' in src,
      "the permissive path must be the one you have to ask for")
check("the TRAINING_GRASS fallback is skipped when strict",
      re.search(r"if require_driven:.*?return None", src, re.S) is not None)
# ‼ Order matters: the HUNTING_GROUNDS lookup must come BEFORE the strict bail-out, or the one
# ground that actually works would be refused too.
i_hg = src.find("entry = HUNTING_GROUNDS.get(map_enum)")
i_strict = src.find("if require_driven:")
check("HUNTING_GROUNDS is consulted BEFORE the strict bail-out", -1 < i_hg < i_strict,
      "otherwise FIERY_PATH — the only converting ground — would be refused as well")

print()
print("2. live behaviour: strict keeps FIERY_PATH and drops the rest")
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
from modules.map_data import MapRSE
from modules.story.training_areas import hunt_ground_tile

os.environ["POKEBOT_HUNT_ANYGROUND"] = "0"
check("FIERY_PATH still qualifies (driven evidence)", hunt_ground_tile(MapRSE.FIERY_PATH) == (18, 19))
for m in ("ROUTE111", "ROUTE116", "ROUTE117", "ROUTE118"):
    check(f"{m} is refused under strict", hunt_ground_tile(MapRSE[m]) is None)

os.environ["POKEBOT_HUNT_ANYGROUND"] = "1"
check("the OLD permissive arm is still reproducible on demand",
      hunt_ground_tile(MapRSE.ROUTE116) is not None,
      "so the 28/28 regression can be re-measured without reverting code")
os.environ["POKEBOT_HUNT_ANYGROUND"] = "0"

print()
if FAIL:
    print(f"FAILED {len(FAIL)}:")
    for f in FAIL: print("  -", f)
    sys.exit(1)
print("ALL PASS")
