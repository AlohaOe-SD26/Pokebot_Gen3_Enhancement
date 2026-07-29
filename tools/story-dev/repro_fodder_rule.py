"""Acceptance: the fodder-grass decision is PURE, and the new rule is behind a flag (KI-31).

WHY THIS EXISTS. `_prepare_for_fight` decided "is the local grass fodder?" with an inline
`local_max + FODDER_LEVEL_GAP < team_max`. That compares the WILD level to the TEAM level —
but `training_areas`' own calibrated model says `xp/battle = 50.2 * wild_level / 7`, i.e. xp
is proportional to the WILD level and does not depend on the team at all.

Measured against the real `TRAINING_GRASS` bands, a team standing on Route 102 (L3-5):

    team L10  -> no relocation, 1.6x speedup forgone
    team L15  -> no relocation, 2.8x speedup forgone     <- the hole
    team L20  -> relocates, works
    team L25+ -> relocates, works

The hole is teams below ~L17, because 5 + 12 = 17.

‼ BUT THE CONSERVATISM IS DELIBERATE. `repro_fodder_grass.py` records the contract:
"WATTSON / ROXANNE / an early team -> UNCHANGED 'train locally' (the whole point of the
conservative gap: proven-good prep must not move)". L10-17 is exactly those bosses. And that
repro loads a real ROM + save state, so it CANNOT run on the dev box — flipping the rule
blind would gamble the user's overnight batches on a test nobody can run here.

So the rule is behind `training_areas.FODDER_RULE`, defaulting to "legacy", and the decision
itself is a pure function this file exercises exhaustively with no emulator.

TO VALIDATE THE NEW RULE (on the machine that HAS mgba):
    1. run `py -3.12 tools/story-dev/repro_fodder_grass.py`   -> record the decision table
    2. set `FODDER_RULE = "xp_rate"` in modules/story/training_areas.py
    3. run it again. The NORMAN row must still relocate/skip as before; the
       WATTSON/ROXANNE rows are the ones to inspect — they are what the flag changes.
    4. only then consider making "xp_rate" the default.
"""
import sys
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

from modules.story import training_areas as ta  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


GAP = 12  # StoryMode.FODDER_LEVEL_GAP


def legacy(local_max, team_max):
    """The EXACT expression that used to be inline in _prepare_for_fight."""
    return local_max is not None and local_max + GAP < team_max


print("== ‼ THE DEFAULT IS THE PROVEN BEHAVIOUR ==")
check(ta.FODDER_RULE == "legacy",
      f"FODDER_RULE defaults to 'legacy' (got {ta.FODDER_RULE!r})")
print("     -> the user's overnight batches keep the behaviour that has been running.")

print("\n== the extracted function reproduces the old expression EXACTLY ==")
mismatches = []
for local_max in range(1, 31):
    for team_max in range(1, 61):
        got = ta.local_patch_is_fodder(local_max, team_max, GAP)
        want = legacy(local_max, team_max)
        if got != want:
            mismatches.append((local_max, team_max, got, want))
check(not mismatches,
      f"all 1,800 (local_max, team_max) combinations match the legacy expression "
      f"({len(mismatches)} mismatches)")
check(ta.local_patch_is_fodder(None, 40, GAP) is False,
      "an unknown local_max is never 'fodder' (fail safe — do not relocate on ignorance)")

print("\n== the model: xp/battle is proportional to the WILD level, not the team's ==")
check(abs(ta.xp_per_battle(5) - 50.2 * 5 / 7) < 1e-9, "xp_per_battle(5) matches the model")
check(ta.xp_per_battle(20) > 3.9 * ta.xp_per_battle(5),
      "L20 wilds pay ~4x what L5 wilds pay")
check(ta.xp_per_battle(0) == 0.0 and ta.xp_per_battle(None) == 0.0,
      "a missing/zero wild level yields 0, not a crash")

print("\n== ‼ THE HOLE the legacy rule leaves (documented, not yet fixed) ==")
for team, expect_legacy in ((10, False), (15, False), (20, True), (25, True)):
    got = ta.local_patch_is_fodder(5, team, GAP)
    check(got is expect_legacy,
          f"legacy: L{team} team on L5 grass -> relocate={got} (hole below ~L17)")

print("\n== the 'xp_rate' rule closes it, and only fires on large wins ==")
# Route 102 (L3-5) with Route 117 (L13-14) reachable: 14/5 = 2.8x -> relocate.
check(ta.local_patch_is_fodder(5, 15, GAP, best_available_max=14, rule="xp_rate") is True,
      "xp_rate: L15 team, L5 local, L14 available -> RELOCATE (2.8x, legacy said no)")
# Route 101 (L2-3) with Route 116 (L6-8) reachable: 8/3 = 2.7x -> relocate.
check(ta.local_patch_is_fodder(3, 10, GAP, best_available_max=8, rule="xp_rate") is True,
      "xp_rate: L10 team, L3 local, L8 available -> RELOCATE (2.7x)")
# A marginal gain must NOT trigger a walk.
check(ta.local_patch_is_fodder(6, 20, GAP, best_available_max=8, rule="xp_rate") is False,
      "xp_rate: only a 1.3x gain -> DO NOT relocate (travel cost is unmeasured)")
check(ta.local_patch_is_fodder(5, 40, GAP, best_available_max=None, rule="xp_rate") is False,
      "xp_rate: nothing better known -> DO NOT relocate (never walk on ignorance)")
check(ta.XP_RATE_RELOCATE_RATIO == 2.0,
      f"the ratio is 2.0 = 'at least halves the grind' (got {ta.XP_RATE_RELOCATE_RATIO})")

print("\n== the two rules DISAGREE exactly where the hole is, and nowhere else ==")
# Boundary, stated exactly: legacy needs `local_max + GAP < team_max`, so with local_max=5
# it is False for team <= 17 and True from team 18. The hole is therefore teams AT OR BELOW
# 17 — an off-by-one this repro caught in the first draft of this very assertion.
FIRST_RELOCATING_TEAM_LEVEL = 5 + GAP + 1  # == 18
check(ta.local_patch_is_fodder(5, 17, GAP) is False, "legacy is still False AT L17")
check(ta.local_patch_is_fodder(5, 18, GAP) is True, "legacy first relocates at L18")

disagree_low, disagree_high = [], []
for team in range(5, 45):
    lg = ta.local_patch_is_fodder(5, team, GAP)
    xr = ta.local_patch_is_fodder(5, team, GAP, best_available_max=14, rule="xp_rate")
    if lg != xr:
        (disagree_low if team < FIRST_RELOCATING_TEAM_LEVEL else disagree_high).append(team)
check(disagree_low == list(range(5, FIRST_RELOCATING_TEAM_LEVEL)),
      f"they disagree on exactly L5-L17 — the hole (got {disagree_low})")
check(disagree_high == [],
      f"they AGREE from L18 up ({disagree_high}) — proven-good late prep is untouched")

print("\n== ‼ THE A/B IS RUNNABLE WITHOUT EDITING CODE ==")
# The first version of this flag was a bare constant, so running the experiment meant
# hand-editing a source file on the batch machine — and install.py's self-healing does
# `git checkout -- <drifted>`, so that edit could be reverted by the very installer the
# operator was told to run. An env var is immune to both problems.
import importlib  # noqa: E402
import os  # noqa: E402

check(ta.FODDER_RULE == "legacy", "default (no env var) is still legacy")

os.environ["POKEBOT_FODDER_RULE"] = "xp_rate"
importlib.reload(ta)
check(ta.FODDER_RULE == "xp_rate", f"POKEBOT_FODDER_RULE=xp_rate switches the rule (got {ta.FODDER_RULE!r})")
check("xp_rate" in ta.active_fodder_rule_banner() and "env" in ta.active_fodder_rule_banner(),
      f"and the banner names it + how it was set: {ta.active_fodder_rule_banner()!r}")

os.environ["POKEBOT_FODDER_RULE"] = "  XP_Rate "
importlib.reload(ta)
check(ta.FODDER_RULE == "xp_rate", "whitespace/case are normalised (a shell quirk must not silently mean 'legacy')")

os.environ["POKEBOT_FODDER_RULE"] = "xprate"
raised = False
try:
    importlib.reload(ta)
except ValueError:
    raised = True
check(raised,
      "‼ a TYPO is REFUSED LOUDLY — a silent fallback would run legacy while the operator "
      "believed they were testing xp_rate, invalidating the whole A/B")

del os.environ["POKEBOT_FODDER_RULE"]
importlib.reload(ta)
check(ta.FODDER_RULE == "legacy", "clearing the env var restores the default")

print("\n== the active rule is NAMED IN THE RUN LOG, so a bundle is attributable ==")
sm_src = (SANDBOX / "plugins" / "custom_modes" / "story_mode.py").read_text(encoding="utf-8")
check("active_fodder_rule_banner" in sm_src,
      "the endless loop prints the active rule each run")
i_banner = sm_src.index("active_fodder_rule_banner")
i_start = sm_src.index("=== ENDLESS RESET: starting run")
check(i_start < i_banner < i_start + 900,
      "and it sits in the per-run header, where a log reader will find it")
# ‼ console.print and the debug log are SEPARATE streams — debug_logger never sees console
# output. The first version banner-ed to the console only, so the DEBUG LOG (the artefact
# actually shared for review) had no record of which rule produced it.
tail = sm_src[i_banner:i_banner + 900]
check("debug_logger.event(" in tail,
      "the banner ALSO goes to the debug log, so a shared log is self-describing")

print("\n== the call site really routes through the pure function ==")
src = (SANDBOX / "plugins" / "custom_modes" / "story_mode.py").read_text(encoding="utf-8")
check("local_patch_is_fodder(" in src, "_prepare_for_fight calls local_patch_is_fodder")
check("local_max + self.FODDER_LEVEL_GAP < team_max_now" not in src,
      "the old inline expression is gone (no second, drifting copy of the rule)")
check('FODDER_RULE == "xp_rate"' in src,
      "the extra area probe is gated on the flag, so the legacy path does no extra lookup")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
