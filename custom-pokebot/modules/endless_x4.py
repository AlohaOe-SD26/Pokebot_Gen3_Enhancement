"""ENDLESS LOOP x4 — batch manager (punch-list #24-x4, user request 2026-07-26).

WHAT IT IS
----------
Four independent `Story (ENDLESS RESET)` bots running at once, each in its OWN
profile with its OWN starter, each looping forever and restarting independently, all
four painted as a 2x2 grid inside the dashboard's video area. The point is data: four
cold-start story runs per wall-clock run instead of one, with each starter guaranteed
coverage so starter-specific bugs cannot hide behind a lucky draw.

WHY THE STARTER SPLIT MATTERS
-----------------------------
It is not cosmetic. `modules/story/early_game.py` already documents that Torchic has
no super-effective move against Roxanne and "may need extra training", and the
3,011-consecutive-flee livelock (2026-07-26) was a Treecko run. Runs stratified by
starter surface different failures; a `random` lane on top keeps the sampling honest.

WHY SEPARATE PROCESSES AND SEPARATE PROFILES
--------------------------------------------
Processes: `context` is a process-wide singleton with one `context.emulator`.
Profiles: two bots sharing a profile directory would clash on `current_save.sav`,
`current_state.ss1` and the stats DB — `tools/story-dev/livetest.py` learned this the
hard way ("two harness processes must never share a profile directory"). Lane
profiles also give the P1..P4 log separation the user asked for for free, since debug
logs are already written per profile.

‼ HISTORY WORTH KNOWING
-----------------------
The FIRST endless-runs feature shelled out to `tools/story-dev/endless_runs.py` and
was abandoned because "the dialogs appeared and nothing appeared to happen" — a
headless subprocess gives the user nothing to watch. That is exactly why this feature
spends the effort on the tile view: the visual channel is what makes a subprocess
batch usable at all. Do not "simplify" this back into invisible subprocesses.
"""

from __future__ import annotations

import datetime
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from modules.console import console
from modules.profiles import PROFILES_DIRECTORY, Profile, create_profile, load_profile_by_name, profile_directory_exists
from modules.roms import ROM
from modules.runtime import get_base_path, is_bundled_app
from modules.tile_bridge import TileBridge

#: Lane 1..3 pin one starter each; lane 4 rolls. Order is fixed so P1 always means
#: Torchic in every log the user ever hands over.
LANE_STARTERS: tuple[str, ...] = ("torchic", "mudkip", "treecko", "random")

BOT_MODE = "Story (ENDLESS RESET)"


def lane_tag(slot: int) -> str:
    return f"P{slot + 1}"


def lane_starter(slot: int) -> str:
    return LANE_STARTERS[slot % len(LANE_STARTERS)]


def lane_profile_name(slot: int) -> str:
    return f"endless-{lane_tag(slot)}-{lane_starter(slot)}"


def ensure_lane_profile(slot: int, rom: ROM) -> Profile:
    """Create the lane's profile if missing and (re)write its `story.yml`.

    ‼ The story.yml is REWRITTEN on every batch launch, deliberately. These are
    bot-managed profiles whose entire purpose is "P2 is always the Mudkip lane"; a
    stale hand-edit silently turning P2 into a second Torchic would corrupt the
    starter coverage the batch exists to provide, and nothing would report it.
    """
    name = lane_profile_name(slot)
    if profile_directory_exists(name):
        profile = load_profile_by_name(name)
    else:
        profile = create_profile(name, rom)
        console.print(f"[green]Endless x4: created lane profile `{name}`.[/]")

    story_yml = Path(profile.path) / "story.yml"
    story_yml.write_text(
        "# Managed by ENDLESS LOOP x4 — REWRITTEN on every batch launch.\n"
        "# Edit the lane table in modules/endless_x4.py, not this file.\n"
        f"character_name: {lane_tag(slot)}\n"
        "gender: boy\n"
        f"starter: {lane_starter(slot)}\n"
        "starter_nickname: none\n",
        encoding="utf-8",
    )
    return profile


@dataclass
class Lane:
    slot: int
    tag: str
    starter: str
    profile_name: str
    process: subprocess.Popen | None = None
    stdout_handle: object = None
    stdout_path: Path | None = None
    restarts: int = 0

    @property
    def is_alive(self) -> bool:
        return self.process is not None and self.process.poll() is None


@dataclass
class EndlessX4Batch:
    """Owns the shared-memory block and the lane processes for one x4 batch."""

    lanes: list[Lane] = field(default_factory=list)
    bridge: TileBridge | None = None
    shm_name: str = ""
    lane_count: int = 4
    #: Auto-restart a lane whose process dies, so an overnight batch does not quietly
    #: decay from 4 lanes to 1. Bounded, so a lane that cannot even boot (bad ROM,
    #: missing save) stops thrashing the disk instead of respawning forever.
    max_restarts: int = 20
    #: Monotonic counter for the parent->child command channel. A lane acts on a CHANGE of
    #: sequence, so this must never repeat within a batch.
    _command_sequence: int = 0
    #: Set once the lanes have been parked for a log collection. `poll()` stops respawning
    #: after this — an auto-restarted lane would start a NEW log and un-park the batch
    #: underneath the collector.
    parked: bool = False

    def start(self, rom: ROM, lane_count: int = 4) -> None:
        self.lane_count = lane_count
        self.shm_name = f"pkbtile{os.getpid()}"
        self.bridge = TileBridge(self.shm_name, lane_count, create=True)
        self.lanes = []
        for slot in range(lane_count):
            profile = ensure_lane_profile(slot, rom)
            lane = Lane(
                slot=slot,
                tag=lane_tag(slot),
                starter=lane_starter(slot),
                profile_name=profile.path.name,
            )
            self.lanes.append(lane)
            self._spawn(lane)

    # ------------------------------------------------------------------
    def _spawn(self, lane: Lane) -> None:
        log_dir = PROFILES_DIRECTORY / lane.profile_name / "debug-logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        lane.stdout_path = log_dir / f"{lane.tag}-stdout-{stamp}.txt"

        args = [
            lane.profile_name,
            "-m", BOT_MODE,
            "-s", "0",          # unthrottled, as requested
            "-na",              # muted at the source
            "--tile-shm", self.shm_name,
            "--tile-slot", str(lane.slot),
            "--tile-lanes", str(self.lane_count),
            "--tile-tag", lane.tag,
            "--endless-target", "0",   # 0 == forever; lanes restart independently
        ]
        if is_bundled_app():
            command = [sys.executable, *args]
        else:
            command = [sys.executable, str(get_base_path() / "pokebot.py"), *args]

        env = dict(os.environ)
        # Encoding round-trips have corrupted em-dashes in this project's logs before.
        env["PYTHONUTF8"] = "1"
        # ‼ WITHOUT THIS THE STDOUT LOG LOOKS EMPTY. A child's stdout is a FILE here, not a
        # console, so CPython block-buffers it at 8 KiB — a lane can run for many minutes
        # with nothing whatsoever on disk, which reads exactly like "the batch produced no
        # logs" (user report, 2026-07-26). Unbuffered costs nothing at these volumes.
        env["PYTHONUNBUFFERED"] = "1"

        creation_flags = 0
        if os.name == "nt":
            # Without this the user gets four console windows thrown in their face.
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        lane.stdout_handle = open(lane.stdout_path, "w", encoding="utf-8", errors="replace")
        lane.process = subprocess.Popen(
            command,
            cwd=str(get_base_path()),
            env=env,
            stdout=lane.stdout_handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        console.print(
            f"[cyan]Endless x4: {lane.tag} ({lane.starter}) started — "
            f"pid {lane.process.pid}, profile `{lane.profile_name}`.[/]"
        )

    # ------------------------------------------------------------------
    def poll(self) -> None:
        """Restart any lane whose process has died. Cheap; safe to call every tick."""
        # ‼ A parked batch must STAY parked. Respawning here would start a fresh lane with
        # a fresh log file, un-parking the batch underneath a log collection that is
        # mid-copy — and the new log would then be archived half-written.
        if self.parked:
            return
        for lane in self.lanes:
            if lane.is_alive or lane.process is None:
                continue
            code = lane.process.returncode
            self._close_stdout(lane)
            if lane.restarts >= self.max_restarts:
                lane.process = None
                continue
            lane.restarts += 1
            console.print(
                f"[yellow]Endless x4: {lane.tag} exited (code {code}); "
                f"restarting ({lane.restarts}/{self.max_restarts}).[/]"
            )
            try:
                self._spawn(lane)
            except Exception as exc:  # noqa: BLE001
                console.print(f"[red]Endless x4: could not restart {lane.tag}: {exc}[/]")
                lane.process = None

    def stop(self) -> None:
        for lane in self.lanes:
            process = lane.process
            lane.process = None
            if process is None or process.poll() is not None:
                self._close_stdout(lane)
                continue
            try:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
            except Exception:
                pass
            self._close_stdout(lane)
        if self.bridge is not None:
            self.bridge.close()
            self.bridge = None
        console.print("[cyan]Endless x4: batch stopped.[/]")

    @staticmethod
    def _close_stdout(lane: Lane) -> None:
        try:
            if lane.stdout_handle is not None:
                lane.stdout_handle.close()
        except Exception:
            pass
        lane.stdout_handle = None

    @property
    def alive_count(self) -> int:
        return sum(1 for lane in self.lanes if lane.is_alive)

    # ------------------------------------------------------------------
    # Parking — the precondition for collecting logs safely
    # ------------------------------------------------------------------
    def park_all(self, timeout_seconds: float = 15.0) -> tuple[bool, list[str]]:
        """Ask every lane to stop, reset to the title screen and CLOSE ITS LOG, then wait
        for each to acknowledge.

        Returns (everyone_parked, notes). A lane that has already died counts as parked —
        its log file is closed by definition.

        ‼ This BLOCKS, briefly. The dashboard has no Tk mainloop (its event queue is pumped
        from the emulator frame callback), so pumping Tk from inside this wait would mean
        re-entering the frame callback. A short, bounded, honest freeze on an explicit user
        action is the safer trade; lanes normally acknowledge in ~100 ms because they poll
        commands at the 20 Hz publish rate.
        """
        import time

        from modules.tile_bridge import CMD_PARK

        notes: list[str] = []
        if self.bridge is None:
            return False, ["the batch has no shared-memory bridge"]

        self.parked = True  # set BEFORE the wait, so poll() cannot respawn mid-park
        self._command_sequence += 1
        for lane in self.lanes:
            if lane.is_alive:
                try:
                    self.bridge.send_command(lane.slot, CMD_PARK, self._command_sequence)
                except Exception as exc:  # noqa: BLE001
                    notes.append(f"{lane.tag}: could not post PARK ({exc})")

        deadline = time.time() + timeout_seconds
        pending = {lane.slot for lane in self.lanes if lane.is_alive}
        while pending and time.time() < deadline:
            time.sleep(0.05)
            for slot in list(pending):
                lane = self.lanes[slot]
                if not lane.is_alive:
                    pending.discard(slot)  # a dead lane holds no open file
                    notes.append(f"{lane.tag}: exited before parking (its log is closed)")
                    continue
                try:
                    frame = self.bridge.read(slot)
                except Exception:
                    frame = None
                if frame is not None and frame.status.get("parked") is True:
                    pending.discard(slot)

        for slot in pending:
            notes.append(f"{self.lanes[slot].tag}: did NOT acknowledge parking within "
                         f"{timeout_seconds:.0f}s — its log may still be open")
        return (not pending), notes
