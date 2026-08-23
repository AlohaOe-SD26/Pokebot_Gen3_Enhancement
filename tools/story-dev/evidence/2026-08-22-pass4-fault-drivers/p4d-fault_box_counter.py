"""P4d fault-injection driver for repro_box_counter_move_test.py.

Monkeypatches the REAL production function `modules.story.counter_hunt.box_counter_pid`
(the value the gate is supposed to be proving behaviour about) to always return None,
i.e. simulate total breakage of the box-side counter test, and shows the gate goes non-zero.
"""
import pathlib
import sys

REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
sys.path.insert(0, str(REPO / "tools" / "story-dev"))
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

import modules.story.counter_hunt as ch  # noqa: E402

_orig = ch.box_counter_pid
ch.box_counter_pid = lambda *a, **k: None  # FAULT: box-side test always finds nothing

import repro_box_counter_move_test as gate  # noqa: E402  (import AFTER the patch)

rc = gate.main()
print(f"\nFAULT-INJECTED EXIT CODE: {rc}")
sys.exit(rc)
