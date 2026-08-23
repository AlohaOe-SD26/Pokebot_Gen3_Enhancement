"""Fault-inject repro_pid_identity_key.py IN-MEMORY ONLY (no repo file writes).
Imports the real gate module (guarded by if __name__=='__main__'), then monkeypatches
Party.get_index_for_pokemon on the live class object to the OLD PID-only rule, and calls
the gate's own main() to see if it now reports FAIL."""
import importlib.util
import pathlib
import sys

REPO = pathlib.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
sys.argv = ["repro_pid_identity_key.py", "--build", "sandbox"]

spec = importlib.util.spec_from_file_location(
    "repro_pid_identity_key_g4",
    REPO / "tools" / "story-dev" / "repro_pid_identity_key.py",
)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)  # runs module top level (arg parsing etc), guarded main() not yet called

from modules.pokemon_party import Party

def old_rule_get_index(self, pokemon):
    """The OLD PID-only rule, applied as an in-memory monkeypatch of the real class."""
    for index, mon in enumerate(self._get_pokemon_list_with_indices()) if hasattr(self, "_get_pokemon_list_with_indices") else enumerate([]):
        pass
    # Simplify: just scan self's underlying party the same way old code did, PID-only.
    for phys_index, mon in self._iter_physical():
        if mon is not None and mon.data[:4] == pokemon.data[:4]:
            return phys_index
    raise RuntimeError("old-rule stub: no PID match")

print("=" * 90)
print("Inspecting Party.get_index_for_pokemon before patch:")
import inspect
print(inspect.getsource(Party.get_index_for_pokemon)[:400])
