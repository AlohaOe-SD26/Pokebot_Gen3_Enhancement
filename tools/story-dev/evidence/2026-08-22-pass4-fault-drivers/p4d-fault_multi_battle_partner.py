"""P4d fault-injection driver for repro_multi_battle_partner.py.

Monkeypatches the REAL production function `modules.battle_strategies.default.ally_party_indices`
(the guard KI-64 added) to always return an EMPTY set -- i.e. simulate the pre-KI-64 regression at
the real call site inside `DefaultBattleStrategy.choose_new_lead_after_faint`, which calls
`ally_party_indices` via its own module globals (so patching the module attribute is enough; no
source edit needed) -- then runs the gate's actual body via runpy so it exercises the REAL,
now-faulted `choose_new_lead_after_faint`.
"""
import pathlib
import runpy
import sys

REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

import modules.battle_strategies.default as default_mod  # noqa: E402

_orig = default_mod.ally_party_indices
default_mod.ally_party_indices = lambda *a, **k: set()  # FAULT: guard disabled, excludes nobody

GATE = REPO / "tools" / "story-dev" / "repro_multi_battle_partner.py"
try:
    runpy.run_path(str(GATE), run_name="__main__")
    rc = 0
except SystemExit as exc:
    rc = exc.code if isinstance(exc.code, int) else (1 if exc.code else 0)

print(f"\nFAULT-INJECTED EXIT CODE: {rc}")
sys.exit(rc)
