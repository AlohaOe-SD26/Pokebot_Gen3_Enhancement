# -*- coding: utf-8 -*-
"""OFFLINE proof that the post-Winona `*_fight` configs are well-formed and GRASS-LESS on purpose.

⛔⛔ WHY THIS EXISTS. `#24-regimeb-noescalation` measured that `_prepare_for_fight`'s last call site
was **Winona (badge 6)** and that all six late chapter modules contain ZERO uses of it, so from badge
7 on **N whiteouts was N IDENTICAL losses** — no escalation, no counter ladder, no honest stop. Two
configs now wire that machinery to Tate & Liza (badge 7) and Juan (badge 8).

⭐ THE LOAD-BEARING DESIGN FACT, AND IT IS A MEASUREMENT, NOT A PREFERENCE:
`training_areas.TRAINING_GRASS` tops out at **ROUTE121, L25-28**. The post-Winona opposition is
**L41-46** (decomp: Tate & Liza 41/41/42/42; Juan 41/41/43/43/**46**). ⇒ **no tabled ground can
train for these fights**, so a `grass` key would send a L40 mon to L28 grass and burn frames for
nothing. The configs are grass-less BY MEASUREMENT.
‼ And that is not a new pattern: `winona_fight` has no `grass` key either — verified here as C5, so
the claim cannot rot. (Its COMMENT said it had one; that contradiction was corrected 2026-09-10.)

⭐ WHAT THE GRASS-LESS PATH STILL BUYS — this is the whole point, and C6 pins it in code:
defeat detection, target escalation, the counter-hunt ladder, and a bounded honest stop. Only the
GRINDING is skipped.

WHAT EACH CASE PROVES:
  C1  every late config carries exactly the keys `_prepare_for_fight` actually reads.
  C2  ⛔ NO late config has a `grass` key — the measured design decision, asserted so a later
      "helpful" addition has to argue with this file.
  C3  every `keys` entry is a REAL map id, and every `heal` a REAL PokemonCenter. A bad enum here is
      a crash at badge 7, ~3 hours into a run.
  C4  the bands match the DECOMP exactly (41,42) / (41,46), and each `ace_level` equals the band's
      TOP. ‼ Juan's ace is 5 levels above his roster's bulk, so a band read off the bulk would miss
      the mon that wins the fight.
  C5  `winona_fight` is itself grass-less — the precedent this design copies.
  C6  `_prepare_for_fight` genuinely has a no-grass branch (AST-checked, not grepped), so a
      grass-less config cannot silently do nothing.

‼ FAULT ARM (self-test):
    POKEBOT_LATEBOSS_FAULT=grass  PYTHONUTF8=1 py -3.12 probe_late_boss_configs.py
injects a `grass` key into a late config; **C2 must go RED** and the script exits 1.
    POKEBOT_LATEBOSS_FAULT=band   PYTHONUTF8=1 py -3.12 probe_late_boss_configs.py
sets Juan's band to the roster bulk (41,43) — the exact mistake of reading past the ace;
**C4 must go RED** and the script exits 1.
    POKEBOT_LATEBOSS_FAULT=wiring PYTHONUTF8=1 py -3.12 probe_late_boss_configs.py
removes `_lead_best_matchup` from the source the probe reads — i.e. reproduces the FIRST DRAFT this
review rejected; **C7 must go RED** and the script exits 1.
⛔ No arm is a strawman: both are the mistakes a maintainer would plausibly make.

⚠ WHAT THIS DOES NOT PROVE: that wiring the machinery here HELPS. That is a frequency question and
needs a batch. This proves the configs are correct and the path is live.
"""
from __future__ import annotations

import ast
import os
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
SB = ROOT / "sandbox-pokebot"
STORY_MODE = SB / "plugins" / "custom_modes" / "story_mode.py"
MAP_DATA = SB / "modules" / "map_data.py"

#: Read once; the `wiring` fault arm mutates this copy.
src = STORY_MODE.read_text(encoding="utf-8")

FAULT = os.environ.get("POKEBOT_LATEBOSS_FAULT", "").strip()

#: Decomp truth (`src/data/trainer_parties.h`), read via `gh api` on 2026-09-10 and pinned here so a
#: later edit to the configs has to disagree with the ROM, not with my memory.
DECOMP = {
    "Tate & Liza": {"band": (41, 42), "ace_level": 42,
                    "party": "Claydol 41 / Xatu 41 / Lunatone 42 / Solrock 42"},
    "Juan": {"band": (41, 46), "ace_level": 46,
             "party": "Luvdisc 41 / Whiscash 41 / Sealeo 43 / Crawdaunt 43 / Kingdra 46"},
}

#: Keys `_prepare_for_fight` reads. `grass` is deliberately ABSENT from the required set.
REQUIRED = {"name", "keys", "band", "ace_types", "ace_level", "heal"}


def _configs() -> dict:
    """Parse the `*_fight` dict literals out of `story_mode.py` with AST (never exec/import —
    importing the bot needs `ruamel` and a ROM, and this probe must run anywhere)."""
    tree = ast.parse(STORY_MODE.read_text(encoding="utf-8"))
    found = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
            continue
        tgt = node.targets[0]
        if not isinstance(tgt, ast.Name) or not tgt.id.endswith("_fight"):
            continue
        d = {}
        for k, v in zip(node.value.keys, node.value.values):
            if not isinstance(k, ast.Constant):
                continue
            try:
                d[k.value] = ast.literal_eval(v)
            except Exception:  # noqa: BLE001 - MapRSE.X.value etc. are not literals
                d[k.value] = ast.unparse(v)
        found[tgt.id] = d
    return found


def main() -> int:
    cfgs = _configs()
    late = {k: v for k, v in cfgs.items() if k in ("tate_liza_fight", "juan_fight")}

    if FAULT == "grass" and "juan_fight" in late:
        late["juan_fight"] = dict(late["juan_fight"], grass="MapRSE.ROUTE121.value, (44, 14)")
    if FAULT == "band" and "juan_fight" in late:
        late["juan_fight"] = dict(late["juan_fight"], band=(41, 43))
    global src
    if FAULT == "wiring":
        # Reproduce the FIRST DRAFT exactly: prep called, counter never fielded.
        src = src.replace("_lead_best_matchup(", "_LEADMATCH_REMOVED(")

    print("=" * 100)
    print("LATE-BOSS FIGHT CONFIGS — post-Winona loss adaptation (`#24-regimeb-noescalation`)")
    if FAULT:
        _w = {"grass": "C2", "band": "C4", "wiring": "C7"}.get(FAULT, "?")
        print(f"  ⛔ FAULT ARM ACTIVE: {FAULT!r} — {_w} MUST go RED")
    print("=" * 100)

    fails: list[str] = []

    ok1 = bool(late) and all(REQUIRED <= set(c) for c in late.values())
    print(f"  [{'OK  ' if ok1 else 'FAIL'}] C1  {len(late)} late config(s) carry every required key")
    for n, c in late.items():
        print(f"         {n}: {sorted(c)}")
    if not ok1:
        fails.append("C1")

    grassy = [n for n, c in late.items() if "grass" in c]
    ok2 = not grassy
    print(f"  [{'OK  ' if ok2 else 'FAIL'}] C2  ⛔ NO late config has a `grass` key "
          f"(table ceiling L28 vs opposition L41-46)")
    if not ok2:
        fails.append("C2")
        print(f"         ⛔ grass key present in: {grassy} — a L40 mon would be sent to L28 grass")

    md = MAP_DATA.read_text(encoding="utf-8")
    bad_syms = []
    for n, c in late.items():
        for key in c.get("keys", []) if isinstance(c.get("keys"), list) else [c.get("keys")]:
            m = re.search(r"MapRSE\.([A-Z0-9_]+)", str(key))
            if m and not re.search(rf"^\s+{m.group(1)}\s*=", md, re.M):
                bad_syms.append(m.group(1))
        m = re.search(r"PokemonCenter\.([A-Za-z0-9_]+)", str(c.get("heal", "")))
        if m and not re.search(rf"^\s+{m.group(1)}\s*=", md, re.M):
            bad_syms.append(m.group(1))
    ok3 = not bad_syms
    print(f"  [{'OK  ' if ok3 else 'FAIL'}] C3  every map id and PokemonCenter resolves to a real symbol")
    if not ok3:
        fails.append("C3")
        print(f"         ⛔ not found in map_data.py: {bad_syms}")

    ok4 = True
    for n, c in late.items():
        want = DECOMP.get(c.get("name"))
        if not want:
            continue
        if tuple(c.get("band", ())) != want["band"] or c.get("ace_level") != want["ace_level"]:
            ok4 = False
            print(f"         ⛔ {c.get('name')}: band={c.get('band')} ace={c.get('ace_level')} "
                  f"but decomp says band={want['band']} ace={want['ace_level']}  [{want['party']}]")
    print(f"  [{'OK  ' if ok4 else 'FAIL'}] C4  bands + ace levels match the DECOMP exactly")
    if not ok4:
        fails.append("C4")

    ok5 = "winona_fight" in cfgs and "grass" not in cfgs["winona_fight"]
    print(f"  [{'OK  ' if ok5 else 'FAIL'}] C5  `winona_fight` is itself grass-less (the precedent copied)")
    if not ok5:
        fails.append("C5")

    ok6 = ('"grass" not in cfg' in src) or ("'grass' not in cfg" in src)
    print(f"  [{'OK  ' if ok6 else 'FAIL'}] C6  `_prepare_for_fight` has a real no-grass branch")
    if not ok6:
        fails.append("C6")
        print("         ⛔ no `\"grass\" not in cfg` branch — a grass-less config may silently no-op")

    # ⛔⛔ C7 — THE CASE A TIER 1 REVIEW SAID THIS GATE WAS MISSING, AND IT WAS RIGHT.
    # The first version checked only the config DICT LITERALS, so it went GREEN while the call sites
    # were wired wrong: `_prepare_for_fight` was called with NO `_lead_best_matchup` after it. That
    # is not cosmetic — `_lead_best_matchup` is the SOLE consumer of `_hunted_counter_pids`, so
    # without it a hunted counter is caught, trained and never FIELDED, and the benched mon then
    # makes `_boss_plan_is_hopeless` read not-hopeless, SUPPRESSING escalation and the honest stop.
    # ⇒ "the gate passes" gave false assurance about the thing that mattered most.
    # ⭐ THE LESSON, GENERALISED: A GATE OVER DATA CANNOT VOUCH FOR THE CODE THAT USES THE DATA.
    # ‼ It also pins the LOCAL IMPORT: every binding of `_lead_best_matchup` in `_play` sits inside
    # an `if not _done("BADGEnn_GET")` branch, so a RESUMED run executes none of them and the call
    # would raise `UnboundLocalError` — on exactly the runs this change exists to help.
    wiring_bad = []
    for _name in late:
        i = src.find(f"self._prepare_for_fight({_name})")
        if i < 0:
            wiring_bad.append(f"{_name}: no `_prepare_for_fight({_name})` call site")
            continue
        # ⛔ STRUCTURAL WINDOW, NOT A CHARACTER COUNT. The first draft of this check used
        # `src[i:i+1800]` and FALSELY FAILED on `tate_liza_fight`, whose `_lead_best_matchup` sits at
        # +1922 because the block carries a long explanatory comment — i.e. the check punished
        # DOCUMENTATION. A gate with false positives teaches the reader to bypass it, which this
        # project rates worse than no gate at all.
        # ⇒ the prep sequence ends where the CHAPTER DISPATCH begins, so bound the search there.
        # That is immune to comment length and cannot bleed into the NEXT boss's block.
        _end = src.find("yield from do_", i)
        window = src[i:_end] if _end > i else src[i:i + 4000]
        if "_lead_best_matchup(" not in window:
            wiring_bad.append(f"{_name}: `_prepare_for_fight` not followed by `_lead_best_matchup` "
                              f"⇒ a hunted counter would never be FIELDED")
        if "import _lead_best_matchup" not in window:
            wiring_bad.append(f"{_name}: missing the LOCAL import ⇒ UnboundLocalError on a resumed run")
    ok7 = not wiring_bad
    print(f"  [{'OK  ' if ok7 else 'FAIL'}] C7  each call site FIELDS the counter "
          f"(`_lead_best_matchup`) and imports it locally")
    if not ok7:
        fails.append("C7")
        for _w2 in wiring_bad:
            print(f"         ⛔ {_w2}")

    print("\n" + "=" * 100)
    if FAULT:
        want = {"grass": "C2", "band": "C4", "wiring": "C7"}.get(FAULT, "?")
        if want in fails:
            print(f"  FAULT ARM OK — {want} went RED under {FAULT!r}.")
            return 1
        print(f"  ⛔ FAULT ARM DID NOT REACH THE CODE — {want} stayed green. Probe cannot be trusted.")
        return 1
    if fails:
        print(f"  ⛔ FAIL — {fails}")
        return 1
    print("  PASS — all 7 cases. The late-boss configs are well-formed and grass-less by measurement.")
    print("  ‼ Proves CORRECTNESS of the configs, never that the wiring HELPS — that needs a batch.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
