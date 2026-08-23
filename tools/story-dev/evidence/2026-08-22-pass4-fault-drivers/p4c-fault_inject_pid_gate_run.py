"""Fault-inject gate 4 IN-MEMORY (no repo writes): monkeypatch Party.get_index_for_pokemon
to the OLD PID-only rule on the live class, then call the gate's own main() and report exit code."""
import importlib.util
import pathlib
import sys

REPO = pathlib.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
BUILD_ARG = sys.argv[1] if len(sys.argv) > 1 else "sandbox"
sys.path.insert(0, str(REPO / f"{BUILD_ARG}-pokebot"))
sys.argv = ["repro_pid_identity_key.py", "--build", BUILD_ARG]

spec = importlib.util.spec_from_file_location(
    "repro_pid_identity_key_g4",
    REPO / "tools" / "story-dev" / "repro_pid_identity_key.py",
)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

from modules.pokemon_party import Party

def old_rule_get_index(self, pokemon):
    """The OLD PID-only rule, as it shipped before Stage 1 (KI-78) -- reintroduced in-memory only."""
    for party_pokemon in self._pokemon:
        if party_pokemon.data[:4] == pokemon.data[:4]:
            return party_pokemon.index
    raise RuntimeError("This Pokemon is not in the player's party.")

print("\n" + "#" * 90)
print(f"# FAULT INJECTION: Party.get_index_for_pokemon reverted to OLD PID-only rule ({BUILD_ARG}-pokebot)")
print("#" * 90 + "\n")
Party.get_index_for_pokemon = old_rule_get_index

rc = gate.main()
print(f"\n>>> gate.main() returned {rc}")
sys.exit(rc)
