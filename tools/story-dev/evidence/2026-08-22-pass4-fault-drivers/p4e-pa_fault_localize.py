"""P4e AUDIT: fault-inject repro_party_accounting.py's gate to prove (a) blinding ONE
divergence class turns exactly that class's checks red (localisation, not aggregation),
and does NOT turn the OTHER classes' checks red.

Mechanism: import the shipped repro_party_accounting.py as a module (guard prevents
auto-run), then monkeypatch modules.pokemon_party._account_slot_anomaly to SILENTLY DROP
only kind=="HOLE" before calling repro.main(). Nothing in tools/story-dev is written to.
"""
import importlib.util
import io
import sys
import contextlib
import pathlib

REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
GATE = REPO / "tools" / "story-dev" / "repro_party_accounting.py"

sys.argv = ["repro_party_accounting.py", "--build", "sandbox"]
spec = importlib.util.spec_from_file_location("repro_party_accounting_underaudit", GATE)
repro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repro)   # runs argparse + sys.path.insert only (module-level code)

import modules.pokemon_party as party_mod  # noqa: E402  (sandbox-pokebot now on sys.path)

orig_slot_anomaly = party_mod._account_slot_anomaly


def blind_hole(kind, index, game_count, detail):
    if kind == "HOLE":
        return  # BLINDED -- the observer is never told about this class
    return orig_slot_anomaly(kind, index, game_count, detail)


party_mod._account_slot_anomaly = blind_hole

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = repro.main()
out = buf.getvalue()

print("=== exit code:", rc, "===")
lines = [l for l in out.splitlines() if "PASS" in l or "FAIL" in l]
fails = [l for l in lines if l.strip().startswith("FAIL")]
print(f"total checks printed: {len(lines)}, FAIL count: {len(fails)}")
print("\n--- FAILED checks (should be ONLY HOLE-related) ---")
for l in fails:
    print(l)
print("\n--- spot-check specific PASS/FAIL lines ---")
for needle in ["HOLE is observed from inside the real get_party()",
               "OVERFLOW is observed",
               "STALE is observed by the six-slot scan",
               "INVALID is observed",
               "NO false positive: a healthy party records no divergence at all"]:
    hit = [l for l in out.splitlines() if needle in l]
    print(f"[{needle}] -> {hit}")
