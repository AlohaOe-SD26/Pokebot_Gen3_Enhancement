"""Collect every ENDLESS LOOP x4 lane's logs into one verified zip (#24-x4-logs).

WHAT IT IS FOR
--------------
A batch scatters its output across four profile directories. Handing those over one at a
time is friction, and friction is why runs go unreviewed. This bundles the lot into
`profiles/x4 LOGS/P1 - P4 x4 LOGs <date> <time>.zip` — one file to attach — and then
archives the originals so the NEXT batch starts from a clean slate and nothing is ever
sent twice.

THE SAFETY ORDER, WHICH IS THE WHOLE POINT
------------------------------------------
    park -> copy -> VERIFY -> archive

1. PARK. Lanes are separate processes; a log still open for append can be copied
   mid-line and cannot be moved on Windows. The dashboard posts `CMD_PARK` and WAITS for
   every lane to acknowledge (`status["parked"]`) before a single byte is read.
2. COPY into the zip.
3. VERIFY by REOPENING the finished zip: `testzip()` for CRC integrity, plus a
   member-by-member check that every source file is present with a matching size.
4. ARCHIVE only then. If verification fails for any reason the originals are left exactly
   where they are and the zip is left for inspection — losing logs to a "tidy up" step
   that ran on a bad archive is the one outcome worth engineering against.

WHAT IS ARCHIVED, AND WHAT DELIBERATELY IS NOT
----------------------------------------------
Archived (moved to `<profile>/debug-logs/Old/`): the per-run artefacts — `*.log` debug
logs and `*-stdout-*.txt` captures. Those belong to one batch.

COPIED BUT NEVER MOVED: `<profile>/badge-log.json`. It is CUMULATIVE history across every
run a lane has ever done (`modules/badge_log.py`), so archiving it would silently reset
the badge record on every collection — exactly the data the trainer-card overlay is being
built to read.
"""

from __future__ import annotations

import datetime
import json
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

#: Where bundles land. Inside `profiles/` because that is where the user asked for it; it
#: has no `metadata.yml`, so `list_available_profiles()` skips it rather than listing a
#: broken profile.
FOLDER_NAME = "x4 LOGS"

#: Per-run artefacts: bundled AND archived.
LOG_PATTERNS = ("*.log", "*.txt")

#: Cumulative state: bundled, never archived.
KEEP_FILES = ("badge-log.json",)

ARCHIVE_DIR = "Old"


@dataclass
class CollectResult:
    ok: bool = False
    zip_path: Path | None = None
    files_bundled: int = 0
    bytes_bundled: int = 0
    archived: int = 0
    lanes: list[str] = field(default_factory=list)
    error: str | None = None
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        if not self.ok:
            return f"Log collection FAILED: {self.error}"
        return (
            f"{self.files_bundled} file(s), {self.bytes_bundled / 1024:.0f} KB from "
            f"{len(self.lanes)} lane(s) -> {self.zip_path.name}; {self.archived} archived."
        )


def _timestamp() -> str:
    # ':' is illegal in Windows filenames, so the time uses dashes.
    return datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")


def _lane_files(profile_dir: Path) -> tuple[list[Path], list[Path]]:
    """(archivable per-run artefacts, cumulative files to copy but keep)."""
    debug_dir = profile_dir / "debug-logs"
    archivable: list[Path] = []
    if debug_dir.is_dir():
        for pattern in LOG_PATTERNS:
            for path in sorted(debug_dir.glob(pattern)):
                # Never re-bundle what a previous collection already archived.
                if path.is_file() and path.parent.name != ARCHIVE_DIR:
                    archivable.append(path)
    keep = [profile_dir / name for name in KEEP_FILES if (profile_dir / name).is_file()]
    return archivable, keep


def collect(profiles_root: Path, lanes: list, archive: bool = True) -> CollectResult:
    """Bundle every lane's logs into one verified zip, then archive the originals.

    `lanes` is the batch's lane list (anything with `.tag`, `.starter`, `.profile_name`).
    Set `archive=False` to bundle without moving anything.
    """
    result = CollectResult()
    try:
        out_dir = profiles_root / FOLDER_NAME
        out_dir.mkdir(parents=True, exist_ok=True)
        zip_path = out_dir / f"P1 - P4 x4 LOGs {_timestamp()}.zip"

        # (source, name inside the zip, is_archivable)
        plan: list[tuple[Path, str, bool]] = []
        for lane in lanes:
            profile_dir = profiles_root / lane.profile_name
            archivable, keep = _lane_files(profile_dir)
            for path in archivable:
                plan.append((path, f"{lane.tag}/{path.name}", True))
            for path in keep:
                plan.append((path, f"{lane.tag}/{path.name}", False))
            result.lanes.append(lane.tag)
            if not archivable:
                result.notes.append(f"{lane.tag}: no per-run logs found")

        # ‼ Require at least one PER-RUN log, not merely "something to zip". `badge-log.json`
        # is never archived, so it is present on every collection — without this check, a
        # second collection with no new runs would happily emit a bundle containing four
        # badge files and no logs at all, which is exactly the bundle you would send off
        # believing it held run data.
        if not any(archivable for _, _, archivable in plan):
            result.error = (
                "no new per-run logs were found — every lane's logs are already archived "
                "in its debug-logs/Old/ folder. Run a batch before collecting again."
            )
            return result

        manifest = _manifest(lanes, plan)

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive_file:
            archive_file.writestr("MANIFEST.txt", manifest)
            for source, arcname, _ in plan:
                archive_file.write(source, arcname)

        # ---- VERIFY before anything is moved --------------------------------
        problem = _verify(zip_path, plan)
        if problem is not None:
            result.error = f"the zip did not verify ({problem}); nothing was archived"
            result.zip_path = zip_path
            return result

        result.zip_path = zip_path
        result.files_bundled = len(plan)
        result.bytes_bundled = sum(source.stat().st_size for source, _, _ in plan)

        # ---- only now is it safe to move the originals ----------------------
        if archive:
            for source, _, archivable in plan:
                if not archivable:
                    continue  # cumulative files stay put — see the module docstring
                try:
                    destination_dir = source.parent / ARCHIVE_DIR
                    destination_dir.mkdir(parents=True, exist_ok=True)
                    destination = destination_dir / source.name
                    counter = 1
                    while destination.exists():
                        destination = destination_dir / f"{source.stem} ({counter}){source.suffix}"
                        counter += 1
                    shutil.move(str(source), str(destination))
                    result.archived += 1
                except Exception as exc:  # noqa: BLE001
                    # The bundle is already verified, so a stuck file is a tidiness
                    # problem, not a data-loss one. Report it and keep going.
                    result.notes.append(f"could not archive {source.name}: {exc}")

        result.ok = True
        return result
    except Exception as exc:  # noqa: BLE001
        result.error = f"{type(exc).__name__}: {exc}"
        return result


def _verify(zip_path: Path, plan: list[tuple[Path, str, bool]]) -> str | None:
    """Reopen the finished zip and prove it holds every file. None == good."""
    try:
        with zipfile.ZipFile(zip_path, "r") as archive_file:
            broken = archive_file.testzip()
            if broken is not None:
                return f"CRC failure in {broken}"
            members = {info.filename: info.file_size for info in archive_file.infolist()}
            if "MANIFEST.txt" not in members:
                return "the manifest is missing"
            for source, arcname, _ in plan:
                if arcname not in members:
                    return f"{arcname} is missing from the archive"
                expected = source.stat().st_size
                if members[arcname] != expected:
                    return f"{arcname} is {members[arcname]} bytes, expected {expected}"
        return None
    except Exception as exc:  # noqa: BLE001
        return f"{type(exc).__name__}: {exc}"


def _manifest(lanes: list, plan: list[tuple[Path, str, bool]]) -> str:
    lines = [
        "ENDLESS LOOP x4 — log bundle",
        f"created: {datetime.datetime.now().isoformat(timespec='seconds')}",
        "",
        "lanes:",
    ]
    for lane in lanes:
        files = [arcname for _, arcname, _ in plan if arcname.startswith(f"{lane.tag}/")]
        lines.append(f"  {lane.tag}  starter={lane.starter}  profile={lane.profile_name}  "
                     f"files={len(files)}")
        badges = _badge_summary(plan, lane.tag)
        if badges:
            lines.append(f"        badges recorded: {badges}")
    lines += ["", "files:"]
    for source, arcname, archivable in plan:
        try:
            size = source.stat().st_size
        except Exception:
            size = -1
        lines.append(f"  {arcname:<60} {size:>12,} bytes{'' if archivable else '   (kept, cumulative)'}")
    return "\n".join(lines) + "\n"


def _badge_summary(plan: list[tuple[Path, str, bool]], tag: str) -> str:
    """A one-line badge tally per lane, so the bundle says at a glance how far it got."""
    for source, arcname, _ in plan:
        if arcname == f"{tag}/badge-log.json":
            try:
                records = json.loads(source.read_text(encoding="utf-8"))
                if not isinstance(records, list) or not records:
                    return ""
                counts: dict[str, int] = {}
                for record in records:
                    name = str(record.get("badge", "?"))
                    counts[name] = counts.get(name, 0) + 1
                return ", ".join(f"{name} x{count}" for name, count in counts.items())
            except Exception:
                return ""
    return ""
