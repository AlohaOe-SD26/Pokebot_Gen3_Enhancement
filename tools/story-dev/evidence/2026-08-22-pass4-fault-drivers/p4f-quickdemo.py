import sys, pathlib
SD = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement/tools/story-dev")
sys.path.insert(0, str(SD))
import run_gates
run_gates.HERE = pathlib.Path(__file__).resolve().parent / "fakegates"
run_gates.GATES = [("fast_ok.py", False), ("slow_red.py", True)]
for argv in (["run_gates.py"], ["run_gates.py", "--quick"]):
    sys.argv = argv
    print(f"\n##### argv={argv}")
    rc = run_gates.main()
    print(f"##### run_gates.main() RETURNED {rc}")
