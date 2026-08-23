"""P4e AUDIT: fault-inject `repro_impassable_dirs.py` by loading a SCRATCH COPY of
modules/map_path.py (with the pre-2026-08-13 Impassable-direction inversion restored) in
place of the real module, then running the shipped gate UNCHANGED. Proves claim (a):
re-inverting the production predicate makes the gate go RED.

No file inside the repo working tree is written or imported-in-place; the real
sandbox-pokebot/modules/map_path.py is never touched. Only sys.modules (this process's own
import cache) is redirected.
"""
import importlib.util
import pathlib
import sys

REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
BUILD = REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

FAULT_FILE = pathlib.Path(__file__).parent / "map_path_REINVERTED.py"

spec = importlib.util.spec_from_file_location("modules.map_path", FAULT_FILE)
faulted_map_path = importlib.util.module_from_spec(spec)
sys.modules["modules.map_path"] = faulted_map_path   # pre-register BEFORE anyone imports it
spec.loader.exec_module(faulted_map_path)
print(f"[fault] modules.map_path redirected to {FAULT_FILE.name} "
      f"(loaded from {faulted_map_path.__file__})")

GATE = REPO / "tools" / "story-dev" / "repro_impassable_dirs.py"
gate_spec = importlib.util.spec_from_file_location("repro_impassable_dirs_underaudit", GATE)
gate = importlib.util.module_from_spec(gate_spec)
try:
    gate_spec.loader.exec_module(gate)
    exit_code = 0
except SystemExit as e:
    exit_code = e.code

print(f"\n[driver] gate exit code = {exit_code}")
