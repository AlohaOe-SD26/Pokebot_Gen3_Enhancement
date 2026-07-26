"""Prove the ENDLESS LOOP x4 frame bridge works ACROSS PROCESSES.

Run:  python test_tile_bridge.py            (parent; spawns children itself)
      python test_tile_bridge.py child N S  (internal)
"""
import os
import subprocess
import sys
import time
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

from modules.tile_bridge import FRAME_BYTES, FRAME_HEIGHT, FRAME_WIDTH, SLOT_BYTES, TileBridge  # noqa: E402

LANES = 4


def pattern(slot: int, tick: int) -> bytes:
    """A per-slot solid colour, so a mixed-up slot is instantly visible."""
    colours = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    r, g, b = colours[slot]
    return bytes([r, g, (b + tick) % 256]) * (FRAME_WIDTH * FRAME_HEIGHT)


def run_child(shm_name: str, slot: int) -> None:
    bridge = TileBridge(shm_name, LANES, create=False)
    for tick in range(60):
        bridge.publish(
            slot, pattern(slot, tick), tick + 1, os.getpid(), tick // 10,
            {"lane": f"P{slot + 1}", "message": f"child {slot} tick {tick}", "party": "Torchic L5  18/21"},
        )
        time.sleep(0.02)
    bridge.close()


def main() -> int:
    shm_name = f"pkbtiletest{os.getpid()}"
    bridge = TileBridge(shm_name, LANES, create=True)
    print(f"[parent] created {shm_name}, {SLOT_BYTES * LANES:,} bytes ({SLOT_BYTES:,}/slot)")

    # Slot never written must read as None (blank-block sanity).
    assert bridge.read(0) is None, "an unwritten slot must not present as a valid frame"
    print("[parent] OK: unwritten slot reads None")

    children = [
        subprocess.Popen([sys.executable, __file__, "child", shm_name, str(slot)])
        for slot in range(LANES)
    ]

    seen = {slot: 0 for slot in range(LANES)}
    deadline = time.time() + 30
    while time.time() < deadline and any(c.poll() is None for c in children):
        for slot in range(LANES):
            frame = bridge.read(slot)
            if frame is None:
                continue
            seen[slot] = max(seen[slot], frame.sequence)
            expected_rgb = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)][slot][:2]
            got_rgb = tuple(frame.pixels[0:2])
            assert got_rgb == expected_rgb, f"slot {slot}: wrong pixels {got_rgb} != {expected_rgb}"
            assert len(frame.pixels) == FRAME_BYTES, f"slot {slot}: short frame {len(frame.pixels)}"
            assert frame.status.get("lane") == f"P{slot + 1}", f"slot {slot}: status crosstalk {frame.status}"
        time.sleep(0.03)

    for c in children:
        c.wait(timeout=10)

    print(f"[parent] highest sequence seen per slot: {seen}")
    for slot, seq in seen.items():
        assert seq > 5, f"slot {slot} never published (seq={seq}) — the bridge did NOT cross the process boundary"

    # Final state check: each slot holds its own last frame, no crosstalk.
    for slot in range(LANES):
        frame = bridge.read(slot)
        assert frame is not None and frame.runs_completed == 5, f"slot {slot}: runs={frame and frame.runs_completed}"
        assert f"child {slot}" in frame.status["message"], f"slot {slot}: {frame.status}"
    print("[parent] OK: all 4 slots isolated, statuses intact, runs counter carried")

    bridge.close()
    print("PASS")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "child":
        run_child(sys.argv[2], int(sys.argv[3]))
    else:
        sys.exit(main())
