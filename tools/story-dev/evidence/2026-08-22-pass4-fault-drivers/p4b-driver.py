import importlib.util
import pathlib
import sys

REAL_GATE = pathlib.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement\tools\story-dev\verify_fixtures.py")
SCRATCH_SAVES = pathlib.Path(__file__).resolve().parent / "saves"

spec = importlib.util.spec_from_file_location("verify_fixtures", REAL_GATE)
vf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vf)

# Point the gate's globals at our scratch copy instead of the real saves/ dir.
vf.SAVES = SCRATCH_SAVES
vf.MANIFEST = SCRATCH_SAVES / "FIXTURES.md5"

scenario = sys.argv[1]

if scenario == "baseline":
    rc = vf.main()
    print("EXIT", rc)

elif scenario == "pinned-drift":
    # mutate the PINNED fixture's bytes
    p = SCRATCH_SAVES / "pinned_a.ss1"
    p.write_bytes(b"MUTATED-BYTES-DO-NOT-MATCH-ANYMORE")
    rc = vf.main()
    print("EXIT", rc)

elif scenario == "pinned-missing":
    p = SCRATCH_SAVES / "pinned_a.ss1"
    p.unlink()
    rc = vf.main()
    print("EXIT", rc)

elif scenario == "volatile-drift":
    p = SCRATCH_SAVES / "volatile_a.ss1"
    p.write_bytes(b"MUTATED-VOLATILE-BYTES-EXPECTED-TO-DRIFT")
    rc = vf.main()
    print("EXIT", rc)

elif scenario == "unlisted-report":
    # unlisted.ss1 already exists on disk but is not a row in the manifest
    rc = vf.main()
    print("EXIT", rc)
    print("UNLISTED MENTIONED IN OUTPUT:", "unlisted" in pathlib.Path.read_text(vf.MANIFEST))

elif scenario == "downgrade-check":
    # Can a PINNED entry be silently downgraded to VOLATILE without alarm?
    # Simulate: change kind column from PINNED to VOLATILE for pinned_a.ss1, keep bytes drifted.
    text = vf.MANIFEST.read_text(encoding="utf-8")
    text = text.replace("PINNED  synthetic pinned fixture", "VOLATILE  synthetic pinned fixture (DOWNGRADED)")
    vf.MANIFEST.write_text(text, encoding="utf-8")
    p = SCRATCH_SAVES / "pinned_a.ss1"
    p.write_bytes(b"MUTATED-AFTER-DOWNGRADE")
    rc = vf.main()
    print("EXIT", rc)

else:
    print("unknown scenario", scenario)
    sys.exit(2)
