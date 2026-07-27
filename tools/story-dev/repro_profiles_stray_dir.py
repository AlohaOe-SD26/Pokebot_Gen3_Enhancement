"""Regression: a non-profile directory inside `profiles/` must not kill startup.

LIVE HIT 2026-07-26. ENDLESS LOOP x4 writes its log bundles to `profiles/x4 LOGS/`. On the
next launch the bot died before the profile screen:

    Starting PokeBot Gen3 dev!
    Could not load ...\\sandbox-pokebot\\profiles\\x4 LOGS\\metadata.yml, file does not exist.
    Please re-download the program or restore the missing file.

`list_available_profiles()` guards with `except RuntimeError`, but `load_profile()` ->
`load_config_file(..., strict=True)` raises `exceptions.CriticalFileMissing`, a
PrettyException — so the guard never fired. Nothing about this was specific to the x4
folder: any stray directory would have done it.
"""
import sys
import tempfile
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

from modules import profiles as profiles_mod  # noqa: E402
from modules.config.schemas_v1 import ProfileMetadata  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


root = Path(tempfile.mkdtemp(prefix="profiles-stray-"))
profiles_mod.PROFILES_DIRECTORY = root

# A REAL profile, copied from the repo's own template so the metadata is genuine.
real = root / "real-profile"
real.mkdir()
template = None
for candidate in (SANDBOX / "profiles").glob("*/metadata.yml"):
    template = candidate
    break
if template is None:
    print("  (no existing profile to copy metadata from — writing a minimal one)")
    (real / ProfileMetadata.filename).write_text(
        "rom:\n  file_name: Pokemon - Emerald Version (USA, Europe).gba\n"
        "  game_code: BPE\n  revision: 0\n  language: E\n", encoding="utf-8")
else:
    (real / ProfileMetadata.filename).write_text(template.read_text(encoding="utf-8"), encoding="utf-8")

# The stray directories that used to be fatal.
(root / "x4 LOGS").mkdir()
(root / "x4 LOGS" / "P1 - P4 x4 LOGs 2026-07-26 18-18-25.zip").write_bytes(b"not a profile")
(root / "New folder").mkdir()
(root / "_ignored").mkdir()
(root / "loose-file.txt").write_text("stray", encoding="utf-8")

print("== enumeration survives stray directories ==")
try:
    found = profiles_mod.list_available_profiles()
    check(True, "list_available_profiles() did not raise")
except BaseException as exc:  # noqa: BLE001
    check(False, f"list_available_profiles() raised {type(exc).__name__}: {exc}")
    found = []

names = sorted(p.path.name for p in found)
check("x4 LOGS" not in names, f"the x4 LOGS bundle folder is not listed as a profile ({names})")
check("New folder" not in names, "a stray 'New folder' is not listed as a profile")
check("_ignored" not in names, "an underscore-prefixed directory is still skipped")

print("\n== a directory with NO metadata.yml is skipped, whatever it is called ==")
(root / "half-copied-profile").mkdir()
(root / "half-copied-profile" / "current_save.sav").write_bytes(b"x")
try:
    profiles_mod.list_available_profiles()
    check(True, "a half-copied profile directory is skipped rather than fatal")
except BaseException as exc:  # noqa: BLE001
    check(False, f"raised {type(exc).__name__}: {exc}")

print("\n== loading a profile BY NAME still reports the missing file helpfully ==")
# Enumeration is tolerant; naming a broken profile explicitly should still tell the user
# exactly what is wrong rather than silently pretending it is not there.
try:
    profiles_mod.load_profile(root / "x4 LOGS")
    check(False, "load_profile() on a non-profile should have raised")
except BaseException as exc:  # noqa: BLE001
    check("metadata" in str(exc).lower() or "CriticalFileMissing" in type(exc).__name__,
          f"it raised something explanatory: {type(exc).__name__}: {str(exc)[:80]}")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
