"""Every losing fight must have a `_prepare_for_fight` cfg. NO EMULATOR — pure source parsing.

WHY THIS EXISTS (`#24-whiteoutloop`, 2026-08-07). All the boss machinery — the sufficiency
gate, `_boss_plan_is_hopeless`'s plateau detection, the counter/training escalation, the
hard-plateau backstop — hangs off a cfg dict passed to `_prepare_for_fight`. **A fight with no
cfg gets none of it, silently.** For weeks, two of the eight losable fights had no cfg at all:

    ROUTE110 (the rival)          #1 or #2 defeat map in 4 of 4 measured batches, 91-120 each
    LAVARIDGE_TOWN_GYM_1F         top-4 in 4 of 4 (87/57/53/73), and the worst runaway seen
                                  anywhere: 17 consecutive losses, kos=[3]*17, perfectly flat

Together those two were **48% of all defeats** (1,079 of 2,236 across four batches), and
"too many whiteout recoveries in a row" was the **#1 end reason** of batch `20260807-102552`
(4 of 14 non-finishes). None of it was visible as a bug — the fights simply lost, quietly,
for ever, because the code that would have noticed was never wired to them.

‼ THE RULE THIS FILE PINS: **a feature that is opt-in per call site will be missing from some
call site.** Assert the COVERAGE, not just the behaviour. `repro_boss_plateau.py` proves the
detector works; nothing proved it was connected, and the detector being perfect is worth
nothing at a fight that never calls it.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
STORY = REPO / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


if not STORY.exists():
    raise SystemExit(f"repro cannot run: missing {STORY}")
src = STORY.read_text(encoding="utf-8")
tree = ast.parse(src)

print("1. collect every cfg that is actually PASSED to _prepare_for_fight")

# The call sites name a local variable; find those names, then the dict literals bound to them.
passed_names = set(re.findall(r"_prepare_for_fight\((\w+)\)", src))
check("at least one call site found", bool(passed_names), f"{len(passed_names)} distinct cfg vars")

cfgs: dict[str, dict] = {}
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
        name = getattr(node.targets[0], "id", None)
        if name not in passed_names:
            continue
        fields = {}
        for k, v in zip(node.value.keys, node.value.values):
            if isinstance(k, ast.Constant):
                try:
                    fields[k.value] = ast.literal_eval(v)
                except Exception:
                    fields[k.value] = "<dynamic>"
        # `keys` is a list of MapRSE .value attributes — recover the MAP NAMES textually.
        raw = ast.get_source_segment(src, node.value) or ""
        fields["_maps"] = re.findall(r"MapRSE\.(\w+)\.value", raw)
        cfgs[name] = fields

check("every passed cfg var resolves to a dict literal", len(cfgs) == len(passed_names),
      f"resolved {sorted(cfgs)} of {sorted(passed_names)}")

print()
print("2. every cfg carries the fields the boss machinery reads")

# `grass` is deliberately OPTIONAL — `_prepare_for_fight` supports a grass-less cfg
# ("No training grass exists for this boss (e.g. Lavaridge)"), and Lavaridge genuinely has
# none (two-way sweep, jaggedgrass_probe.py). Requiring it here would force someone to invent
# a training tile, which is how KI-44 happened.
BASE_REQUIRED = ("keys", "band")
# ‼ `ace_types`/`ace_level` are required only for fights the bot MEASURABLY LOSES — see §3.
# `rival_fight` (the Rustboro rival) has neither and that is FINE: it recorded **0 defeats in
# all four measured batches**, so the plateau detector has nothing to detect there. The first
# draft of this test demanded them everywhere, which would have pushed someone to invent ace
# data for a fight that never loses — churn with a real chance of being wrong.
for name, f in sorted(cfgs.items()):
    missing = [k for k in BASE_REQUIRED if k not in f]
    check(f"{name} has {', '.join(BASE_REQUIRED)}", not missing,
          f"maps={f.get('_maps')} missing={missing}" if missing else f"maps={f.get('_maps')}")
    if f.get("band") not in (None, "<dynamic>"):
        lo, hi = f["band"]
        ace = f.get("ace_level")
        # ‼ THE BAND DOES NOT CONTAIN THE ACE, and asserting that it does is wrong.
        # `band` is the TRAINING TARGET range; the ace is often above it — decomp-verified:
        # Brawly is Machop 16 / Meditite 16 / **Makuhita 19**, cfg band (14, 16), ace_level 19.
        # The first draft asserted `lo <= ace <= hi` and failed correct, decomp-accurate data.
        # The real invariant is only that the ace is not BELOW the band's floor.
        check(f"{name}: band ordered, ace_level not below the band floor",
              lo <= hi and (ace is None or ace == "<dynamic>" or ace >= lo),
              f"band={f['band']} ace_level={ace}")

print()
print("3. ‼ COVERAGE: every fight the bot MEASURABLY loses at has a cfg")

# Measured from four stored batches via `analyse_defeat_loops.py` — these are the maps that
# actually accumulate defeats, ordered by volume. ROUTE110 and LAVARIDGE_TOWN_GYM_1F are the
# two that were missing and are the entire reason this file exists.
MUST_COVER = {
    "ROUTE110": "the rival — #1/#2 defeat map in 4 of 4 batches",
    "LAVARIDGE_TOWN_GYM_1F": "Flannery — top-4 in 4 of 4; worst runaway seen (17x, kos flat at 3)",
    "PETALBURG_CITY_GYM": "Norman — worst single sequence, 32 consecutive losses",
    "MAUVILLE_CITY_GYM": "Wattson",
    "FORTREE_CITY_GYM": "Winona",
    "DEWFORD_TOWN_GYM": "Brawly",
    "RUSTBORO_CITY_GYM": "Roxanne",
}
cfg_for_map = {m: n for n, f in cfgs.items() for m in f.get("_maps", [])}
for m, why in MUST_COVER.items():
    owner = cfg_for_map.get(m)
    check(f"{m} is covered by a _prepare_for_fight cfg", owner is not None, why)
    # ...and the cfg covering a LOSING map must carry the ace data, or the plateau detector
    # returns early (`"ace_types" not in cfg`) and the coverage is nominal only.
    if owner:
        f = cfgs[owner]
        check(f"{m}'s cfg ({owner}) carries ace_types + ace_level",
              "ace_types" in f and "ace_level" in f,
              "without these `_boss_plan_is_hopeless` returns early and nothing detects a plateau")

print()
print("4. the new cfgs actually DRIVE the detector (not just well-formed)")

# A cfg can be perfectly shaped and still be inert if `ace_types` is empty or unusable:
# `_boss_plan_is_hopeless` returns early on `"ace_types" not in cfg`. Assert the two new ones
# carry real, non-empty type tuples.
for name in ("flannery_fight", "rival110_fight"):
    f = cfgs.get(name)
    check(f"{name} exists", f is not None)
    if f:
        at = f.get("ace_types")
        check(f"{name}.ace_types is a non-empty tuple of type names",
              isinstance(at, tuple) and len(at) >= 1 and all(isinstance(x, str) for x in at)
              or at == "<dynamic>",
              f"ace_types={at}")

# ‼ The Route 110 rival's ace DEPENDS ON THE PLAYER'S STARTER (decomp: sParty_MayRoute110*),
# so its `ace_types` is necessarily computed, not literal. Assert the derivation still names
# all three cases and uses TYPE PAIRS — effectiveness against a dual-type is the PRODUCT, so
# naming only the primary type ("Water" for Marshtomp) understates the matchup.
seg = re.search(r"ace_types = \(\"Grass\",\).*?travel_route110_and_fight_rival", src, re.S)
check("the Route 110 starter-dependent derivation is present", seg is not None)
if seg:
    body = seg.group(0)
    check("Torchic branch -> Marshtomp's PAIR (Ground, Water)",
          '("Ground", "Water")' in body)
    check("Treecko branch -> Combusken's PAIR (Fighting, Fire)",
          '("Fighting", "Fire")' in body)
    check("Mudkip default -> Grovyle (Grass)", 'ace_types = ("Grass",)' in body)

print()
if FAILURES:
    print(f"FAILED {len(FAILURES)} check(s):")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print(f"ALL PASS — {len(cfgs)} boss cfgs, {len(MUST_COVER)} measured defeat maps all covered.")
