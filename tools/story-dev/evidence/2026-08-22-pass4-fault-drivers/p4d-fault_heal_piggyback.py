"""P4d fault-injection driver for repro_heal_piggyback_reporting.py.

Builds a SCRATCH COPY of the real production file with the counter-withdraw `except` handler
reverted to a silent swallow (the exact 2026-08-14 regression this gate exists to catch: a
piggyback handler that no longer calls `_piggyback_report`), then overrides the gate's TARGET
path constant (rule 2b: "override the gate's path constants to a scratch copy of just the ONE
module file it exercises") and re-runs its `main()`.
"""
import pathlib
import sys

REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
REAL = REPO / "sandbox-pokebot" / "modules" / "modes" / "util" / "higher_level_actions.py"
SCRATCH = pathlib.Path(__file__).parent / "scratch_higher_level_actions.py"

src = REAL.read_text(encoding="utf-8")

NEEDLE = (
    '            reraise_if_aborting(error)\n'
    '            _piggyback_report("counter withdraw", f"FAILED ({error!r}) — the counter is STILL "\n'
    '                                                  f"BOXED and the run will fight without it")\n'
)
REPLACEMENT = (
    '            reraise_if_aborting(error)\n'
    '            pass  # FAULT-INJECTED (P4d): reverted to the silent 2026-08-14 regression\n'
)
assert NEEDLE in src, "needle not found — production file text has moved, update the driver"
faulted = src.replace(NEEDLE, REPLACEMENT, 1)
assert faulted != src
SCRATCH.write_text(faulted, encoding="utf-8")
print(f"wrote fault-injected scratch copy: {SCRATCH}")

sys.path.insert(0, str(REPO / "tools" / "story-dev"))
import repro_heal_piggyback_reporting as gate  # noqa: E402

gate.TARGET = SCRATCH  # point the gate at our faulted scratch copy instead of the real tree
gate.REPO = SCRATCH.parent  # so TARGET.relative_to(REPO) in the gate's own print doesn't crash

rc = gate.main()
print(f"\nFAULT-INJECTED EXIT CODE: {rc}")
sys.exit(rc)
