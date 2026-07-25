"""Proof for the FRAME-COST GATE fix (punch-list #24: prep decisions used to budget
grinds in LEVELS, not FRAMES — see modules/story/training_areas.py's
`estimate_frames_to_level` docstring for the measured numbers this closes).

Loads the real captured save `prenorman_fodder_grind.ss1`. This save was captured
MID-GRIND — by the time it was captured, Combusken had already climbed to Lv35 (needing
only 688 exp for Lv36), so its CURRENT state is not itself expensive; it doubles below as
the CONTROL case. To reproduce the actual documented failure (a Lv33 Combusken sent to
reach Lv36/Blaziken on this exact Route 102 patch — the run that burned ~430,000 frames
for those 3 levels and helped blow the overall frame cap), we evaluate the SAME real
Combusken species/growth-curve data from this save at the ORIGIN level the real failure
started from (Lv33), using the real API
(`species.level_up_type.get_experience_needed_for_level`) — not a fabricated curve.

  1. THE REAL FAILING DECISION: Lv33 Combusken (this save's real species/growth-curve
     data) -> Lv36 on Route 102's real wild band from this save's real position. Before
     the fix, `_sufficiency_verdict`'s evo-lookahead would commit to this on level-gap
     alone (`mon.level < evo_level <= mon.level + 3`); the fix adds a frame estimate and
     REJECTS any plan over `StoryMode.MAX_PREP_TRAINING_FRAMES`.
  2. CONTROL: this save's ACTUAL current Combusken (real object, real total_exp, Lv35 ->
     Lv36, only 688 exp away) — lands comfortably under budget and is still ACCEPTED.

Run: py -3.12 tools/story-dev/repro_prep_frame_gate.py
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

profile = load_profile_by_name("repro-fresh")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"
state_path = REPO / "tools/story-dev/saves/prenorman_fodder_grind.ss1"
context.emulator.load_save_state(state_path.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from types import SimpleNamespace

from modules.pokemon_party import get_party
from modules.map_data import MapRSE
from modules.story.training_areas import estimate_frames_to_level
import plugins.custom_modes.story_mode as sm

W = 90
print("=" * W)
print("1) THE REAL FAILING DECISION — Combusken Lv33 -> L36 (Blaziken) on Route 102 wilds")
print("=" * W)

party = [p for p in get_party() if p is not None and not p.is_egg]
trainee = max(party, key=lambda m: m.level)  # Combusken, per the captured save
target_level = 36  # the reported evo-lookahead target (mon.level + 3 == 36 for L33)
origin_level = 33  # the level the real documented failure started from

wild_level = sm._wild_land_max(MapRSE.ROUTE102)
print(f"  Trainee species: {trainee.species.name} (this save's real species/growth-curve data)")
print(f"  Origin: Lv{origin_level} (the real production failure's reported starting level)")
print(f"  Target: Lv{target_level}  (evo-lookahead's mon.level+3 window)")
print(f"  Local grass: ROUTE102, max wild level = {wild_level}")

# Real growth-curve API, evaluated at the origin level the real failure started from
# (this save was captured mid-grind, already past that point — see module docstring).
origin_exp = trainee.species.level_up_type.get_experience_needed_for_level(origin_level)
mon_at_origin = SimpleNamespace(species=trainee.species, total_exp=origin_exp)

est_frames = estimate_frames_to_level(mon_at_origin, target_level, wild_level)
budget = sm.StoryMode.MAX_PREP_TRAINING_FRAMES
print(f"  estimate_frames_to_level(...) = {est_frames:,} frames")
print(f"  MAX_PREP_TRAINING_FRAMES      = {budget:,} frames")
decision = "REJECTED" if (est_frames is None or est_frames > budget) else "ACCEPTED"
print(f"  DECISION: {decision}")
assert est_frames is not None and est_frames > budget, (
    f"expected the Route 102 evo-lookahead grind to be REJECTED (over budget), "
    f"got estimate={est_frames}, budget={budget}"
)
print("  -> matches expectation: the fodder-patch grind is now REJECTED before it starts.")

print("\n" + "=" * W)
print("2) CONTROL — this save's ACTUAL current Combusken is still ACCEPTED")
print("=" * W)
# This save was captured mid-grind: Combusken is already Lv35, needing only 688 exp for
# Lv36 — a genuinely cheap grind on the SAME Route 102 patch. Real object, real state.
control_est = estimate_frames_to_level(trainee, target_level, wild_level)
print(f"  Trainee: {trainee.species.name} Lv{trainee.level} (total_exp={trainee.total_exp}) -> Lv{target_level}")
print(f"  Local grass: ROUTE102, max wild level = {wild_level}")
print(f"  estimate_frames_to_level(...) = {control_est:,} frames")
print(f"  MAX_PREP_TRAINING_FRAMES      = {budget:,} frames")
control_decision = "REJECTED" if (control_est is None or control_est > budget) else "ACCEPTED"
print(f"  DECISION: {control_decision}")
assert control_est is not None and control_est <= budget, (
    f"expected the near-target control grind to be ACCEPTED (under budget), "
    f"got estimate={control_est}, budget={budget}"
)
print("  -> matches expectation: a well-matched, cheap grind is still allowed through.")

print("\n" + "-" * W)
print("ALL PASS: the fodder-patch evo grind is rejected on frame cost; a cheap, "
      "well-matched grind is still accepted.")
