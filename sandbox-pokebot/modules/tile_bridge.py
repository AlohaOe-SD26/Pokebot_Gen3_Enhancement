"""Shared-memory frame bridge for ENDLESS LOOP x4 (punch-list #24-x4).

WHY THIS EXISTS
---------------
`modules/context.py` exposes ONE process-wide `context` singleton, imported by 116
files, and `context.emulator` is a single `LibmgbaEmulator`. Running four emulators
inside one Python process would mean threading a context object through the whole
codebase — a fork-wide refactor that would also make future upstream subtree pulls
painful. So an x4 batch is FOUR CHILD PROCESSES, one emulator each, and this module
is the only thing they share with the dashboard.

WHAT IT CARRIES
---------------
Per lane ("slot"): a fixed-size 240x160 RGB framebuffer plus a small JSON status blob
(current message, runs completed, party one-liner, map). One `SharedMemory` block
holds every slot back to back, so there is exactly one OS handle for the batch.

TEARING
-------
There is no lock — a lock shared across processes on the emulator's hot path is not
worth the risk of a child wedging the dashboard. Instead the writer publishes in a
fixed ORDER (pixels, then status, then the header with `sequence` LAST) and the reader
re-checks `sequence` after copying. A reader that sees a stable sequence is guaranteed
the pixels behind it are whole; a torn read is simply retried on the next tick, which
at ~20 Hz is invisible.

LIFETIME
--------
The DASHBOARD creates the block and holds it open for the life of the batch; children
only attach. On Windows a shared-memory block dies with its last handle and `unlink()`
is a no-op, so parent-owned lifetime is what keeps a crashed child from leaking it.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from multiprocessing import shared_memory

#: Bumped if the layout below ever changes, so a stale child can never be misread as
#: a valid frame (children are separate processes and may lag a code change).
MAGIC = 0x504B5432

FRAME_WIDTH = 240
FRAME_HEIGHT = 160
FRAME_BYTES = FRAME_WIDTH * FRAME_HEIGHT * 3  # RGB888

#: JSON status blob. 1 KiB is ample for a message, a party one-liner and counters;
#: `publish()` truncates rather than raising if a message is pathologically long.
STATUS_BYTES = 1024

# magic, sequence, pid, runs_completed, flags, width, height
_HEADER_FORMAT = "<IIIIIHH"
HEADER_BYTES = struct.calcsize(_HEADER_FORMAT)
SLOT_BYTES = HEADER_BYTES + STATUS_BYTES + FRAME_BYTES

FLAG_FRAME_VALID = 1 << 0

_BLANK_FRAME = b"\x00" * FRAME_BYTES


@dataclass(frozen=True)
class TileFrame:
    """One lane's most recently published state, as read by the dashboard."""

    sequence: int
    pid: int
    runs_completed: int
    status: dict
    width: int
    height: int
    pixels: bytes


class TileBridge:
    """Shared-memory block holding `lanes` slots. Create in the parent, attach in a child."""

    def __init__(self, name: str, lanes: int, create: bool = False):
        self.name = name
        self.lanes = lanes
        self._owner = create
        if create:
            self._shm = shared_memory.SharedMemory(name=name, create=True, size=SLOT_BYTES * lanes)
            # A recycled block could otherwise present a stale MAGIC as a live frame.
            self._shm.buf[: SLOT_BYTES * lanes] = b"\x00" * (SLOT_BYTES * lanes)
        else:
            self._shm = shared_memory.SharedMemory(name=name, create=False)
        self._buf = self._shm.buf

    # -- writer side (child) ------------------------------------------------
    def publish(self, slot: int, pixels: bytes, sequence: int, pid: int, runs_completed: int, status: dict) -> None:
        """Publish one lane's frame. `pixels` MUST be exactly FRAME_BYTES of RGB888.

        Order matters: pixels, then status, then the header. `sequence` lands last so a
        reader that sees a new sequence is looking at a complete frame (see module docstring).
        """
        if len(pixels) != FRAME_BYTES:
            raise ValueError(f"expected {FRAME_BYTES} bytes of RGB888, got {len(pixels)}")
        base = slot * SLOT_BYTES
        self._buf[base + HEADER_BYTES + STATUS_BYTES : base + SLOT_BYTES] = pixels

        blob = json.dumps(status, separators=(",", ":")).encode("utf-8", "replace")
        if len(blob) > STATUS_BYTES - 1:
            # Never let an oversized message abort a publish — drop to the essentials.
            blob = json.dumps({"message": str(status.get("message", ""))[:200]},
                              separators=(",", ":")).encode("utf-8", "replace")[: STATUS_BYTES - 1]
        self._buf[base + HEADER_BYTES : base + HEADER_BYTES + STATUS_BYTES] = blob.ljust(STATUS_BYTES, b"\x00")

        struct.pack_into(
            _HEADER_FORMAT, self._buf, base,
            MAGIC, sequence & 0xFFFFFFFF, pid, runs_completed, FLAG_FRAME_VALID, FRAME_WIDTH, FRAME_HEIGHT,
        )

    # -- reader side (dashboard) --------------------------------------------
    def read(self, slot: int) -> TileFrame | None:
        """Read one lane, or None if it has never published / the read tore twice."""
        base = slot * SLOT_BYTES
        for _ in range(2):
            magic, sequence, pid, runs, flags, width, height = struct.unpack_from(_HEADER_FORMAT, self._buf, base)
            if magic != MAGIC or not (flags & FLAG_FRAME_VALID):
                return None
            raw_status = bytes(self._buf[base + HEADER_BYTES : base + HEADER_BYTES + STATUS_BYTES])
            pixels = bytes(self._buf[base + HEADER_BYTES + STATUS_BYTES : base + SLOT_BYTES])
            # Re-read the sequence: unchanged means nothing was written underneath us.
            if struct.unpack_from(_HEADER_FORMAT, self._buf, base)[1] == sequence:
                try:
                    status = json.loads(raw_status.split(b"\x00", 1)[0].decode("utf-8", "replace") or "{}")
                except Exception:
                    status = {}
                if not isinstance(status, dict):
                    status = {}
                return TileFrame(sequence, pid, runs, status, width, height, pixels)
        return None

    def close(self) -> None:
        try:
            self._buf = None
            self._shm.close()
        except Exception:
            pass
        if self._owner:
            try:
                self._shm.unlink()  # no-op on Windows; matters if this ever runs on POSIX
            except Exception:
                pass


def blank_frame() -> bytes:
    """A black 240x160 RGB frame, for lanes that have not published yet."""
    return _BLANK_FRAME
