# -*- coding: utf-8 -*-
"""WHERE do runs actually lose battles? The full distribution, offline, from the recorded corpus.

⛔⛔ WHY THIS EXISTS, AND WHY IT IS A MEASUREMENT RATHER THAN A GATE.
`03-PUNCH-LIST.md`'s `#24-regimeb-noescalation` — the item that owns "the back half of the game has
NO loss-adaptation at all" — carries one explicit instruction before any fix may be designed:

    "⚠ DO NOT SCOPE FROM THE TERMINAL-LOCATION STATISTIC — it is a sample of size one per run
     (`08-MISTAKES.md` 2026-09-07). Plot the whole distribution of loss sites first."

A run's ENDING location is one observation per run. A run that loses 30 battles at Mossdeep and then
derails on Route 124 contributes "Route 124" to a terminal-location count and hides all 30. That is
how this item previously produced a 58% bucket for ROUTE 124 — a map that `heal_locations.json`
does not even contain. ⇒ **this reads EVERY loss, not the last one.**

‼ IT IS DELIBERATELY NOT IN `run_gates.py`. A 2026-09-10 health audit found the suite had grown
16 → 52 gates in 28 days while four chapters were wired, and recommended holding at 52. This answers
a ONE-TIME scoping question; a gate would re-answer it forever for nobody. ⇒ re-runnable tool, not a
standing gate — the project's rule is "a re-runnable tool instead of a scratchpad number", and that
is satisfied without spending a gate slot.

WHAT IT READS. Every `stdout.txt` under `x4-runs/`, for the production line:
    Story: lost a battle at map (G, N) (defeat #K here; KO'd M of theirs first).
`(G, N)` is the live `map_group_and_number`, resolved against `MapRSE` so the output names maps
rather than numbers. ⛔ Unresolvable pairs are reported as UNKNOWN and counted, never dropped —
a silently-discarded bucket is how the previous scoping went wrong.

⚠ HONEST LIMITS, stated so this cannot be over-quoted:
  * A LOSS IS NOT A WHITEOUT. `defeat #K here` counts battles lost; a whiteout is the party-wipe
    that follows some of them. Both are printed, separately, and they must not be conflated.
  * Batches span different builds and different ladder lengths. Per-batch output is therefore
    reported separately; the aggregate is for shape, not for a rate.
  * It says WHERE, never WHY. A map with many losses may be hard, or merely visited often.

USAGE
    PYTHONUTF8=1 py -3.12 probe_loss_site_distribution.py [<batch-dir> ...]
"""
from __future__ import annotations

import collections
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "sandbox-pokebot"))

from modules.map_data import MapRSE  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
RUNS = HERE / "x4-runs"

_LOSS = re.compile(r"lost a battle at map \((\d+), *(\d+)\).*?defeat #(\d+) here")
_WHITEOUT = re.compile(r"Story: whited out")

#: (group, number) -> enum name, built once from the real enum so no map name is ever invented.
_BY_ID = {}
for _m in MapRSE:
    try:
        _BY_ID[tuple(_m.value)] = _m.name
    except Exception:  # noqa: BLE001 - a non-tuple member is simply not a map id
        pass

#: Maps that only exist AFTER badge 6 (Winona). The gap under investigation is "no team training or
#: loss-adaptation after Winona", so losses here are the ones the machinery cannot currently answer.
_POST_WINONA = (
    "MOSSDEEP", "SOOTOPOLIS", "EVER_GRANDE", "VICTORY_ROAD", "SEAFLOOR", "SKY_PILLAR",
    "SPACE_CENTER", "ROUTE124", "ROUTE125", "ROUTE126", "ROUTE127", "ROUTE128",
    "ROUTE129", "ROUTE130", "ROUTE131", "ROUTE132", "ROUTE133", "ROUTE134",
)


def _era(name: str) -> str:
    return "post-Winona" if any(k in name for k in _POST_WINONA) else "pre-Winona"


def scan(batch: pathlib.Path) -> dict:
    losses: collections.Counter[str] = collections.Counter()
    whiteouts = 0
    runs = 0
    unknown: collections.Counter[tuple] = collections.Counter()
    for out in sorted(batch.rglob("stdout.txt")):
        runs += 1
        try:
            text = out.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        whiteouts += len(_WHITEOUT.findall(text))
        for g, n, _k in _LOSS.findall(text):
            key = (int(g), int(n))
            name = _BY_ID.get(key)
            if name is None:
                unknown[key] += 1
                losses[f"UNKNOWN{key}"] += 1
            else:
                losses[name] += 1
    return {"batch": batch.name, "runs": runs, "losses": losses,
            "whiteouts": whiteouts, "unknown": unknown}


def main(argv: list[str]) -> int:
    batches = [pathlib.Path(a) for a in argv] if argv else [p for p in sorted(RUNS.glob("*")) if p.is_dir()]

    print("=" * 100)
    print("LOSS-SITE DISTRIBUTION — every battle lost, not the terminal location")
    print("=" * 100)

    grand: collections.Counter[str] = collections.Counter()
    grand_wo = grand_runs = 0
    grand_unknown: collections.Counter[tuple] = collections.Counter()

    for b in batches:
        r = scan(b)
        if not r["losses"] and not r["whiteouts"]:
            continue
        grand.update(r["losses"])
        grand_wo += r["whiteouts"]
        grand_runs += r["runs"]
        grand_unknown.update(r["unknown"])
        tot = sum(r["losses"].values())
        print(f"\n--- {r['batch']}  ({r['runs']} stdout files, {tot} battle losses, "
              f"{r['whiteouts']} whiteouts) ---")
        for name, c in r["losses"].most_common(6):
            print(f"    {c:5}  ({100.0*c/max(tot,1):4.1f}%)  {name}   [{_era(name)}]")

    total = sum(grand.values())
    print("\n" + "=" * 100)
    print(f"AGGREGATE — {grand_runs} run files, {total} battle losses, {grand_wo} whiteouts")
    if not total:
        print("  ⛔ NO LOSS LINES FOUND. Either the corpus is empty or the production message changed;")
        print("     check `story_mode.py` for 'lost a battle at map'. A zero here is NOT 'no losses'.")
        return 1

    print("\n  TOP LOSS SITES (all batches pooled — SHAPE only, not a rate):")
    for name, c in grand.most_common(12):
        print(f"    {c:5}  ({100.0*c/total:4.1f}%)  {name}   [{_era(name)}]")

    era = collections.Counter()
    for name, c in grand.items():
        era[_era(name)] += c
    print("\n  ⭐ BY ERA — this is the number `#24-regimeb-noescalation` needs:")
    for k, c in era.most_common():
        print(f"    {c:5}  ({100.0*c/total:4.1f}%)  {k}")
    print("\n  ‼ post-Winona losses are the ones NO machinery answers: `_prepare_for_fight` is last")
    print("    called at Winona, and the six late chapter modules contain zero uses of it.")
    if grand_unknown:
        print(f"\n  ⚠ {sum(grand_unknown.values())} loss(es) on {len(grand_unknown)} UNRESOLVED map id(s) "
              f"— reported, never dropped: {list(grand_unknown)[:6]}")
    print("\n  ⛔ WHERE, never WHY. A busy map may be hard or merely often-visited.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
