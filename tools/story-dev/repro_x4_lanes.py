"""Prove the ENDLESS LOOP x4 lane setup: profiles, starter mapping, spawn plumbing.

This box has no `mgba`, so the lanes cannot actually emulate. Everything up to that
point IS tested here, including how far a spawned lane gets before it dies.
"""
import shutil
import sys
import time
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

from modules import endless_x4  # noqa: E402
from modules.roms import list_available_roms  # noqa: E402

EXPECTED = {
    0: ("P1", "torchic", "endless-P1-torchic"),
    1: ("P2", "mudkip", "endless-P2-mudkip"),
    2: ("P3", "treecko", "endless-P3-treecko"),
    3: ("P4", "random", "endless-P4-random"),
}

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


print("== lane naming ==")
for slot, (tag, starter, profile) in EXPECTED.items():
    check(endless_x4.lane_tag(slot) == tag, f"slot {slot} tag == {tag}")
    check(endless_x4.lane_starter(slot) == starter, f"slot {slot} starter == {starter}")
    check(endless_x4.lane_profile_name(slot) == profile, f"slot {slot} profile == {profile}")

roms = list_available_roms()
check(bool(roms), "a ROM is available")
if not roms:
    sys.exit(1)
rom = roms[0]
print(f"  rom: {rom.file.name}")

# Clean any leftovers from a previous run of this test so creation is exercised.
for slot in EXPECTED:
    d = SANDBOX / "profiles" / endless_x4.lane_profile_name(slot)
    if d.exists():
        shutil.rmtree(d)

print("\n== profile creation + story.yml ==")
for slot, (tag, starter, profile_name) in EXPECTED.items():
    profile = endless_x4.ensure_lane_profile(slot, rom)
    path = Path(profile.path)
    check(path.name == profile_name, f"{tag}: profile dir {profile_name}")
    check((path / "metadata.yml").is_file(), f"{tag}: metadata.yml written")
    story = (path / "story.yml").read_text(encoding="utf-8")
    check(f"starter: {starter}" in story, f"{tag}: story.yml pins starter={starter}")
    check(f"character_name: {tag}" in story, f"{tag}: story.yml names the character {tag}")

print("\n== story.yml is REWRITTEN (a stale hand-edit must not survive) ==")
p = SANDBOX / "profiles" / "endless-P2-mudkip" / "story.yml"
p.write_text("character_name: HACK\ngender: girl\nstarter: torchic\nstarter_nickname: none\n", encoding="utf-8")
endless_x4.ensure_lane_profile(1, rom)
check("starter: mudkip" in p.read_text(encoding="utf-8"), "P2: hand-edited starter reverted to mudkip")

print("\n== the config the story bot will actually read ==")
from modules.story.config import get_story_config  # noqa: E402

for slot, (tag, starter, profile_name) in EXPECTED.items():
    cfg = get_story_config(SANDBOX / "profiles" / profile_name)
    check(cfg.starter == starter, f"{tag}: get_story_config().starter == {starter}")
    check(cfg.character_name == tag, f"{tag}: get_story_config().character_name == {tag}")

print("\n== spawn plumbing (lanes will die: no mgba on this box) ==")
batch = endless_x4.EndlessX4Batch()
batch.max_restarts = 0  # do not thrash while the dependency is missing
try:
    batch.start(rom, 4)
    check(len(batch.lanes) == 4, "4 lanes created")
    check(batch.bridge is not None, "shared-memory block created")
    check(all(l.process is not None for l in batch.lanes), "all 4 lanes spawned a process")
    for lane in batch.lanes:
        check(lane.stdout_path is not None and lane.stdout_path.name.startswith(f"{lane.tag}-stdout-"),
              f"{lane.tag}: stdout log is prefixed {lane.tag}-")

    deadline = time.time() + 60
    while time.time() < deadline and any(l.is_alive for l in batch.lanes):
        time.sleep(1)
    batch.poll()

    print("\n-- how far each lane got --")
    for lane in batch.lanes:
        text = ""
        try:
            text = lane.stdout_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            text = f"<unreadable: {e}>"
        last = [ln for ln in text.strip().splitlines() if ln.strip()][-1:] or ["<empty>"]
        print(f"  {lane.tag}: exit={lane.process.returncode if lane.process else 'n/a'}  {last[0][:150]}")
        # ‼ POSITIVE evidence only (08-MISTAKES 2026-07-26). An earlier version asserted
        # `"unrecognized arguments" not in text`, which also passes for a process that
        # crashed during import, never started, or wrote nothing — and it DID pass while
        # every lane was dying at `load_plugins()`, long before argparse ran. Assert that
        # the child produced output and say honestly where it stopped.
        check(bool(text.strip()), f"{lane.tag}: the spawned process produced output")
        if "No module named 'mgba'" in text:
            print(f"       {lane.tag}: stopped at the emulator import — this box has no mgba, so "
                  f"NOTHING past `load_plugins()` is exercised by this test (see repro_x4_tile_child.py)")
        elif "unrecognized arguments" in text:
            check(False, f"{lane.tag}: argparse REJECTED the tile flags")
        else:
            check("--tile-shm" not in text, f"{lane.tag}: no argparse complaint about the tile flags")
finally:
    batch.stop()
    check(batch.bridge is None, "stop() released the shared-memory block")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
