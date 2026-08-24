"""INDEPENDENT verification of the claim that closes #24-abortrecoveryresiduals (a):
the whiteout-recovery window is spent on maps where no wild land encounter can fire.
Uses the PROJECT'S OWN `get_wild_encounters_for_map`, not a hand-rolled ROM parse."""
from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

p = load_profile_by_name("repro-fresh")
context.profile = p
context.config.load(p.path, strict=False)
set_rom(p.rom)
from modules.libmgba import LibmgbaEmulator
context.emulator = LibmgbaEmulator(p, lambda: None)
context.audio = False
context.video = False

from modules.map import get_wild_encounters_for_map
from modules.map_data import MapRSE

def land(name):
    g = MapRSE[name].value
    enc = get_wild_encounters_for_map(g[0], g[1])
    return len(enc.land_encounters) if enc and enc.land_encounters else 0

# EVERY town/city and EVERY Poke Center interior - not a sample. A Tier 1 reviewer pointed out
# the first version tested 11 of 18 towns and 8 of 32 centers while the prose claimed "every".
# The reviewer ran the full set independently and got the same answer, but the COMMITTED evidence
# must prove the sentence it is cited for.
TOWNS = sorted(n for n in MapRSE.__members__
               if (n.endswith("_TOWN") or n.endswith("_CITY")) and "POKEMON_CENTER" not in n)
CENTERS = sorted(n for n in MapRSE.__members__ if "POKEMON_CENTER" in n)
CONTROLS = ["ROUTE101","ROUTE102","PETALBURG_WOODS"]

print("  RESPAWN TOWNS (claim: land == 0)")
bad = 0
for t in TOWNS:
    try:
        v = land(t); bad += (v != 0)
        print(f"     {'OK ' if v==0 else 'BAD'}  {t:22} land={v}")
    except Exception as e:
        print(f"     ??   {t:22} {type(e).__name__}: {str(e)[:40]}")
print("\n  POKE CENTER INTERIORS (claim: land == 0)")
for c in CENTERS:
    try:
        v = land(c); bad += (v != 0)
        print(f"     {'OK ' if v==0 else 'BAD'}  {c[:34]:34} land={v}")
    except Exception as e:
        print(f"     ??   {c[:34]:34} {type(e).__name__}")
print("\n  POSITIVE CONTROLS (claim: land > 0 -- proves the reader WORKS)")
for c in CONTROLS:
    try:
        v = land(c); bad += (v == 0)
        print(f"     {'OK ' if v>0 else 'BAD'}  {c:22} land={v}")
    except Exception as e:
        print(f"     ??   {c:22} {type(e).__name__}")
print(f"\n  => {bad} BAD")
context.emulator.shutdown()
