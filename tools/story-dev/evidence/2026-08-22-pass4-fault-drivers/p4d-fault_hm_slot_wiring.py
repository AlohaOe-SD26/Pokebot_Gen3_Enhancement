"""P4d fault-injection driver for repro_hm_slot_wiring.py.

Reproduces the EXACT historical KI-63 regression this gate exists to catch: both real HM
call sites in story_mode.py reverted from the wrapper `ensure_hm_learner_making_room` back to
a bare `ensure_hm_learner` call (the "individually-correct parts, one link missing" bug the
gate's own docstring names). early_game.py / higher_level_actions.py / pc_trip.py are left as
the REAL files — only the ONE module this fault targets (story_mode.py) is a scratch copy, per
rule 2b.

Because the gate is a plain top-level script (no importable main(), it runs and sys.exit()s at
import time), we write a MODIFIED COPY of the gate itself with only its STORY_MODE path constant
repointed at our faulted scratch copy, and run that copy via subprocess so the real gate script
(and everyone else's concurrent runs of it) is never touched.
"""
import pathlib
import subprocess
import sys

REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
REAL_STORY_MODE = REPO / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REAL_GATE = REPO / "tools" / "story-dev" / "repro_hm_slot_wiring.py"
SCRATCH_DIR = pathlib.Path(__file__).parent
SCRATCH_STORY_MODE = SCRATCH_DIR / "scratch_story_mode.py"
SCRATCH_GATE = SCRATCH_DIR / "scratch_repro_hm_slot_wiring.py"

src = REAL_STORY_MODE.read_text(encoding="utf-8")
NEEDLE = "_slot = yield from ensure_hm_learner_making_room(\n"
count = src.count(NEEDLE)
assert count == 2, f"expected 2 wired call sites (Rock Smash + Surf), found {count} — file text moved"
faulted = src.replace(NEEDLE, "_slot = yield from ensure_hm_learner(\n")
assert faulted.count("ensure_hm_learner_making_room(") == 0
SCRATCH_STORY_MODE.write_text(faulted, encoding="utf-8")
print(f"wrote fault-injected scratch copy: {SCRATCH_STORY_MODE}  (2 call sites reverted to bare ensure_hm_learner)")

gate_src = REAL_GATE.read_text(encoding="utf-8")
NEEDLE1 = 'SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"'
NEEDLE2 = 'STORY_MODE = SANDBOX / "plugins" / "custom_modes" / "story_mode.py"'
assert NEEDLE1 in gate_src and NEEDLE2 in gate_src
gate_faulted = gate_src.replace(
    NEEDLE1,
    f'SANDBOX = Path(r"{REPO}") / "sandbox-pokebot"  # P4d: real repo, not scratch-relative',
).replace(
    NEEDLE2,
    f'STORY_MODE = Path(r"{SCRATCH_STORY_MODE}")  # P4d: repointed at fault-injected scratch copy',
)
SCRATCH_GATE.write_text(gate_faulted, encoding="utf-8")

result = subprocess.run(
    [sys.executable, str(SCRATCH_GATE)],
    capture_output=True, text=True, cwd=str(REPO / "tools" / "story-dev"),
    env={**__import__("os").environ, "PYTHONUTF8": "1"},
)
print(result.stdout)
print(result.stderr, file=sys.stderr)
print(f"\nFAULT-INJECTED EXIT CODE: {result.returncode}")
sys.exit(result.returncode)
