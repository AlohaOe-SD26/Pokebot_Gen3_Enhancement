import pathlib, sys, inspect
REPO = pathlib.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
from modules.pokemon_party import Party
print(inspect.getsource(Party.get_index_for_pokemon))
