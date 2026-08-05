"""Badge funnel for the cap-6 batch vs the 52.0% baseline, segmented by TIME WINDOW.

The badge logs accumulate across batches in each profile dir, so a window filter on
`earned_at` is what separates them. Windows are the MANIFEST's started/ended stamps.
"""
import glob
import json
import pathlib
from collections import defaultdict

WINDOWS = {
    "baseline 054fa8c6 (cap 4)": ("2026-08-05T07:56:00", "2026-08-05T11:00:00"),
    "cap-6    be104e9c":         ("2026-08-05T12:20:57", "2026-08-05T15:21:03"),
}
ORDER = ["Stone", "Knuckle", "Dynamo", "Heat", "Balance", "Feather"]

for label, (lo, hi) in WINDOWS.items():
    # (profile, run_index) identifies a run; collect the set of badges it earned.
    runs = defaultdict(set)
    teamsize = defaultdict(dict)
    for path in glob.glob("sandbox-pokebot/profiles/endless-*/badge-log.json"):
        prof = pathlib.Path(path).parent.name
        for e in json.load(open(path, encoding="utf-8")):
            if lo <= e["earned_at"] <= hi:
                key = (prof, e["run_index"])
                runs[key].add(e["badge"])
                team = [m for m in e.get("team", []) if not m.get("egg")]
                teamsize[key][e["badge"]] = len(team)

    print(f"\n{'=' * 72}\n{label}   runs seen: {len(runs)}\n{'=' * 72}")
    print(f"{'rung':<26}{'held':>8}{'of':>6}   rate")
    for i in range(len(ORDER) - 1):
        a, b = ORDER[i], ORDER[i + 1]
        have_a = [k for k, v in runs.items() if a in v]
        both = [k for k in have_a if b in runs[k]]
        rate = f"{100*len(both)/len(have_a):.0f}%" if have_a else "n/a"
        print(f"{a + '->' + b:<26}{len(both):>8}{len(have_a):>6}   {rate}")
    # whole funnel
    s = [k for k, v in runs.items() if "Stone" in v]
    f6 = [k for k in s if "Feather" in runs[k]]
    print(f"{'Stone->Feather (whole)':<26}{len(f6):>8}{len(s):>6}   "
          f"{100*len(f6)/len(s):.0f}%" if s else "n/a")

    # team size at each badge moment
    print("\n  mean team size at badge moment:")
    for b in ORDER:
        vals = [d[b] for d in teamsize.values() if b in d]
        if vals:
            print(f"    {b:<10} n={len(vals):<4} mean={sum(vals)/len(vals):.2f}")
