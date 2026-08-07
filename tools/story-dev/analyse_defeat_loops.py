import re, sys, pathlib
from collections import defaultdict, Counter
LOSS = re.compile(r"lost a battle at map \((\d+), (\d+)\) \(defeat #(\d+) here; KO'd (\d+) of theirs first\)")
NAMES = {(0,25):"ROUTE110",(8,1):"PETALBURG_GYM",(4,1):"LAVARIDGE_GYM",(12,1):"FORTREE_GYM",
         (10,0):"MAUVILLE_GYM",(24,12):"MT_CHIMNEY",(3,3):"DEWFORD_GYM",(0,26):"ROUTE111",
         (1,1):"RUSTBORO_GYM",(0,15):"RUSTBORO_CITY"}
# maps reached by a _prepare_for_fight cfg (its "keys" lists)
HAS_CFG = {(1,1),(0,15),(3,3),(2,0),(10,0),(0,9),(8,1),(0,13),(12,1),(0,17)}
tot = Counter(); cfgless = Counter()
for batch in sys.argv[1:]:
    root = pathlib.Path(batch)
    per = Counter()
    for f in root.glob("L0*/stdout.txt"):
        for line in f.open(encoding="utf-8", errors="replace"):
            m = LOSS.search(line)
            if m:
                g,n,d,k = (int(x) for x in m.groups())
                per[(g,n)] += 1
    s = sum(per.values())
    no = sum(v for kk,v in per.items() if kk not in HAS_CFG)
    print(f"{root.name}: defeats={s:4}  at maps with NO _prepare_for_fight cfg = {no:4} ({100*no/max(1,s):.0f}%)")
    top = ", ".join(f"{NAMES.get(k,k)}={v}{'' if k in HAS_CFG else '*'}" for k,v in per.most_common(5))
    print(f"    top5: {top}")
    tot.update(per)
print()
s = sum(tot.values()); no = sum(v for k,v in tot.items() if k not in HAS_CFG)
print(f"ALL BATCHES: defeats={s}  no-cfg={no} ({100*no/s:.0f}%)   (* = no boss cfg)")
