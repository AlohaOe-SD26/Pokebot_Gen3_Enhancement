"""P4e AUDIT: fault-inject a MUTATING observer to prove the "NO BEHAVIOUR CHANGE" control
actually catches an observer that writes to state, not just one that no-ops correctly.

Mechanism: monkeypatch modules.pokemon_party._account_slot_anomaly so that on a HOLE
sighting it also corrupts the memory backing the NEXT slot's checksum bytes (via the bound
FakeMemory instance reachable through party_accounting.read_symbol.__self__), THEN calls
through to the real observer. The "WITH observer" arm of the shipped control should then
diverge from the "WITHOUT observer" (stubbed) arm on the SAME fixture -- if the control
only compares values the observer never touches, it will not notice.
"""
import importlib.util
import io
import sys
import contextlib
import pathlib

REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
GATE = REPO / "tools" / "story-dev" / "repro_party_accounting.py"

sys.argv = ["repro_party_accounting.py", "--build", "sandbox"]
spec = importlib.util.spec_from_file_location("repro_party_accounting_underaudit2", GATE)
repro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repro)

import modules.pokemon_party as party_mod  # noqa: E402
from modules import party_accounting  # noqa: E402

orig_slot_anomaly = party_mod._account_slot_anomaly


def mutant_slot_anomaly(kind, index, game_count, detail):
    if kind == "HOLE":
        try:
            # party_accounting.read_symbol is monkeypatched, inside run_scenario(), to the
            # BOUND METHOD memory.read_symbol -- reach the FakeMemory instance through it.
            memory_obj = party_accounting.read_symbol.__self__
            block = bytearray(memory_obj.symbols["gPlayerParty"])
            off = (index + 1) * 100 + 28  # corrupt the NEXT slot's checksum bytes
            block[off:off + 2] = b"\xDE\xAD"
            memory_obj.symbols["gPlayerParty"] = bytes(block)
            print(f"[MUTATION] observer corrupted checksum of slot {index + 1}")
        except Exception as e:
            print(f"[MUTATION] failed to corrupt: {e!r}")
    return orig_slot_anomaly(kind, index, game_count, detail)


party_mod._account_slot_anomaly = mutant_slot_anomaly

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = repro.main()
out = buf.getvalue()

print("=== exit code:", rc, "===")
lines = [l for l in out.splitlines() if "PASS" in l or "FAIL" in l]
fails = [l for l in lines if l.strip().startswith("FAIL")]
print(f"total checks printed: {len(lines)}, FAIL count: {len(fails)}")
print("\n--- ALL FAILED checks ---")
for l in fails:
    print(l)
print("\n--- the specific NO-BEHAVIOUR-CHANGE checks ---")
for l in out.splitlines():
    if "byte-identical with and without the observer" in l:
        print(l)
