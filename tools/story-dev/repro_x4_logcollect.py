"""Prove the x4 log collector: park -> copy -> VERIFY -> archive, and the failure paths.

The property that matters most is the NEGATIVE one: if the zip does not verify, nothing
must be moved. A "tidy up" step that runs on a bad archive is how you lose the only copy
of the run data the whole feature exists to gather.
"""
import json
import shutil
import sys
import tempfile
import types
import zipfile
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

from modules import x4_logs  # noqa: E402
from modules.tile_bridge import CMD_NONE, CMD_PARK, TileBridge  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


class Lane:
    def __init__(self, slot, tag, starter):
        self.slot, self.tag, self.starter = slot, tag, starter
        self.profile_name = f"endless-{tag}-{starter}"


LANES = [Lane(i, f"P{i + 1}", s) for i, s in enumerate(("torchic", "mudkip", "treecko", "random"))]


def build_profiles(root: Path, with_badges=True):
    for lane in LANES:
        debug = root / lane.profile_name / "debug-logs"
        debug.mkdir(parents=True, exist_ok=True)
        (debug / f"{lane.tag}-Story-debug-20260726-100000.log").write_text(
            f"{lane.tag} debug log\n" * 50, encoding="utf-8")
        (debug / f"{lane.tag}-stdout-20260726-100000.txt").write_text(
            f"{lane.tag} stdout\n" * 20, encoding="utf-8")
        if with_badges:
            (root / lane.profile_name / "badge-log.json").write_text(
                json.dumps([{"badge": "Stone", "leader": "Roxanne",
                             "team": [{"name": "TORCHIC", "level": 14}]}]), encoding="utf-8")


print("== a clean collection ==")
root = Path(tempfile.mkdtemp(prefix="x4logs-"))
build_profiles(root)
result = x4_logs.collect(root, LANES)
check(result.ok, f"collect() succeeded ({result.error})")
check(result.zip_path is not None and result.zip_path.exists(), "the zip exists")
check(result.zip_path.parent.name == x4_logs.FOLDER_NAME, f"it is in '{x4_logs.FOLDER_NAME}/'")
check(result.zip_path.name.startswith("P1 - P4 x4 LOGs "), f"name: {result.zip_path.name}")
check(result.zip_path.name.endswith(".zip"), "it is a .zip")
check(":" not in result.zip_path.name, "the timestamp uses no ':' (illegal on Windows)")
check(result.files_bundled == 12, f"12 files bundled — 2 logs + 1 badge log x 4 lanes (got {result.files_bundled})")

with zipfile.ZipFile(result.zip_path) as z:
    names = set(z.namelist())
check("MANIFEST.txt" in names, "the manifest is present")
for lane in LANES:
    check(any(n.startswith(f"{lane.tag}/") for n in names), f"{lane.tag}/ has entries")
check(f"P1/badge-log.json" in names, "badge-log.json is bundled")

print("\n== per-run logs archived, cumulative history NOT ==")
for lane in LANES:
    debug = root / lane.profile_name / "debug-logs"
    live = [p.name for p in debug.glob("*") if p.is_file()]
    old = [p.name for p in (debug / "Old").glob("*")] if (debug / "Old").is_dir() else []
    check(live == [], f"{lane.tag}: no per-run logs left loose (found {live})")
    check(len(old) == 2, f"{lane.tag}: both logs moved to Old/ (found {len(old)})")
    check((root / lane.profile_name / "badge-log.json").is_file(),
          f"{lane.tag}: badge-log.json STAYED (it is cumulative history)")
check(result.archived == 8, f"8 files archived, not 12 (got {result.archived})")

print("\n== the manifest is informative ==")
with zipfile.ZipFile(result.zip_path) as z:
    manifest = z.read("MANIFEST.txt").decode("utf-8")
check("starter=torchic" in manifest, "the manifest records each lane's starter")
check("Stone x1" in manifest, "the manifest summarises badges earned")
check("(kept, cumulative)" in manifest, "the manifest marks files that were not archived")

print("\n== a second collection does not re-bundle what is already in Old/ ==")
second = x4_logs.collect(root, LANES)
check(not second.ok, "a collection with nothing new fails cleanly rather than shipping a "
                     "badge-only bundle that looks like it holds run data")
check("no new per-run logs" in (second.error or ""), f"and says why: {second.error}")

print("\n== new logs after archiving are collected, old ones are not ==")
for lane in LANES:
    (root / lane.profile_name / "debug-logs" / f"{lane.tag}-Story-debug-20260726-120000.log").write_text(
        "second batch\n", encoding="utf-8")
third = x4_logs.collect(root, LANES)
check(third.ok, "the second batch collected")
check(third.files_bundled == 8, f"4 new logs + 4 badge logs, NOT the archived ones (got {third.files_bundled})")

print("\n== an archive name collision does not overwrite ==")
for lane in LANES:
    (root / lane.profile_name / "debug-logs" / f"{lane.tag}-Story-debug-20260726-120000.log").write_text(
        "third batch, same filename\n", encoding="utf-8")
fourth = x4_logs.collect(root, LANES)
check(fourth.ok, "the third batch collected")
old_p1 = sorted(p.name for p in (root / "endless-P1-torchic" / "debug-logs" / "Old").glob("*.log"))
check(any("(1)" in n for n in old_p1), f"the colliding file was renamed, not clobbered: {old_p1}")
check(len(old_p1) == 3, f"all three P1 logs survive in Old/ (got {len(old_p1)}: {old_p1})")

print("\n== !! IF THE ZIP DOES NOT VERIFY, NOTHING IS ARCHIVED ==")
root2 = Path(tempfile.mkdtemp(prefix="x4logs-bad-"))
build_profiles(root2)
real_verify = x4_logs._verify
x4_logs._verify = lambda zip_path, plan: "simulated corruption"
try:
    bad = x4_logs.collect(root2, LANES)
finally:
    x4_logs._verify = real_verify
check(not bad.ok, "collect() reported failure")
check("did not verify" in (bad.error or ""), f"and said why: {bad.error}")
check(bad.archived == 0, "nothing was archived")
for lane in LANES:
    debug = root2 / lane.profile_name / "debug-logs"
    check(len(list(debug.glob("*.log"))) == 1, f"{lane.tag}: the original log is still in place")
    check(not (debug / "Old").exists(), f"{lane.tag}: no Old/ folder was even created")

print("\n== _verify actually catches a damaged archive ==")
root3 = Path(tempfile.mkdtemp(prefix="x4logs-tamper-"))
build_profiles(root3, with_badges=False)
good = x4_logs.collect(root3, LANES, archive=False)
check(good.ok, "bundled without archiving")
plan = [(root3 / l.profile_name / "debug-logs" / f"{l.tag}-Story-debug-20260726-100000.log",
         f"{l.tag}/{l.tag}-Story-debug-20260726-100000.log", True) for l in LANES]
check(x4_logs._verify(good.zip_path, plan) is None, "a good zip verifies")
missing_plan = plan + [(plan[0][0], "P1/not-in-the-zip.log", True)]
check(x4_logs._verify(good.zip_path, missing_plan) is not None, "a missing member is caught")
truncated = root3 / "truncated.zip"
truncated.write_bytes(good.zip_path.read_bytes()[: len(good.zip_path.read_bytes()) // 2])
check(x4_logs._verify(truncated, plan) is not None, "a truncated zip is caught")

print("\n== archive=False leaves everything in place ==")
for lane in LANES:
    debug = root3 / lane.profile_name / "debug-logs"
    check(len(list(debug.glob("*.log"))) == 1, f"{lane.tag}: log untouched with archive=False")

print("\n== the command channel carries PARK across the bridge ==")
bridge = TileBridge("pkbtilecmdtest", 4, create=True)
child_view = TileBridge("pkbtilecmdtest", 4, create=False)
check(child_view.read_command(0) == (CMD_NONE, 0), "no command initially")
bridge.send_command(2, CMD_PARK, 7)
check(child_view.read_command(2) == (CMD_PARK, 7), "PARK reached slot 2")
check(child_view.read_command(0) == (CMD_NONE, 0), "other slots are untouched")

print("\n== a command survives the child publishing frames over its own regions ==")
import PIL.Image  # noqa: E402

pixels = PIL.Image.new("RGB", (240, 160), (5, 5, 5)).tobytes()
child_view.publish(2, pixels, 1, 123, 0, {"lane": "P3", "parked": False})
check(child_view.read_command(2) == (CMD_PARK, 7),
      "publishing did NOT clobber the parent's command (separate regions)")
frame = bridge.read(2)
check(frame is not None and frame.status.get("lane") == "P3", "and the frame still reads back correctly")
bridge.close()
child_view.close()

for path in (root, root2, root3):
    shutil.rmtree(path, ignore_errors=True)

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
