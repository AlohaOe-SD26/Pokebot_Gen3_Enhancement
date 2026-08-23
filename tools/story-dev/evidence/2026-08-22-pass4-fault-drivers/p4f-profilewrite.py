"""Prove the six probes' construction WRITES profile state, without touching the real profile:
redirect Profile.path to a scratch dir and construct exactly as the probes do."""
import sys, pathlib, dataclasses, atexit
REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
BUILD = REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))
from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

real = load_profile_by_name("repro-ml")
scratch = pathlib.Path(__file__).resolve().parent / "fakeprofile"
scratch.mkdir(exist_ok=True)
try:
    fake = dataclasses.replace(real, path=scratch)
except Exception:
    class F: pass
    fake = F(); fake.rom = real.rom; fake.path = scratch
context.profile = fake
context.config.load(real.path, strict=False)
set_rom(real.rom)
from modules.libmgba import LibmgbaEmulator
before = sorted(p.name for p in scratch.iterdir())
emu = LibmgbaEmulator(fake, lambda: None)   # EXACTLY the probes' call - no is_test_run
context.emulator = emu
context.audio = False; context.video = False
for _ in range(10):
    emu.run_single_frame()
mid = sorted(p.name for p in scratch.iterdir())
print(f"[probe-shape ctor] files before={before}  after ctor+10 frames={mid}")
n = len([f for f in atexit._ncallbacks.__self__ if False]) if False else None
emu.shutdown()      # what atexit.register(self.shutdown) does at interpreter exit
after = sorted(p.name for p in scratch.iterdir())
print(f"[after shutdown()] files={after}")
print("WROTE current_state.ss1:", "current_state.ss1" in after)
