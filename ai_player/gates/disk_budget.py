"""TEST SIDE (build step 5.2, G5): THE DISK BUDGET of the sweeps and the live drivers.

    py -3.12 ai_player/gates/disk_budget.py                      the free space, and how many %TEMP%/ai_* folders there are
    py -3.12 ai_player/gates/disk_budget.py --temp [--older-than 24] [--apply]
                                    the %TEMP%/ai_* folders older than that many hours (a DRY RUN: counts and sizes by
                                    prefix); --apply deletes them (a running sweep's folders are younger: never touched)
    py -3.12 ai_player/gates/disk_budget.py --profiles [--keep-newest 12] [--apply]
                                    the launcher run folders `sandbox-pokebot/profiles/ai-*/ai_player_runs/*` the PRUNE
                                    POLICY would delete (dry run); --apply deletes them

WHY (the lessons draft, EN-2, measured 2026-10-15): `%TEMP%` held 24,355 `ai_*` folders, about 18 GB (`ai_step5_*` 11.8 GiB,
about 8 MB a run; `ai_rate3_*` 5.5 GiB), because `rate_step5.run_one` made a `mkdtemp` per run and never removed it, while
the disk was 96 % full and the learner wrote beside the sweeps. Three rules, each enforced here:
  1. A SWEEP REFUSES TO START with under `MIN_FREE_GB` (30) GB free on the drive of %TEMP% or of the repository
     (`preflight`): a clear message, exit 2, nothing played.
  2. A SWEEP'S RUN FOLDERS LIVE UNDER ONE ROOT (`SweepFolders`: `%TEMP%/ai_sweep_<tag>_<random>/`) and are DELETED after
     grading (`tidy`), except the FAILING runs and the newest `keep_newest`; `--keep-runs` keeps them all (a verifier who
     will recount from the raw logs needs them: say so when you pass it). The kept and deleted counts go into the evidence.
  3. A LIVE DRIVER PRUNES ITS PROFILE'S RUN FOLDERS after grading (`prune_runs`): it keeps every run folder that FAILED (no
     `purity.json`, a verdict that is not CLEAN, or a non-zero exit code), every one CITED by name (in the evidence or the
     documents), and the newest `keep_newest`; the rest is deleted.
Deleting what has already leaked is the coordinator's or the user's call: `--temp` and `--profiles` are dry runs unless
`--apply` is given.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import time
from collections.abc import Iterable
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROFILES = REPO / "sandbox-pokebot" / "profiles"
EVIDENCE = REPO / "ai_player" / "evidence"
#: rule 1: the free space a sweep needs before it starts
MIN_FREE_GB = 30.0
#: rules 2 and 3: how many of the newest run folders are kept besides the failing and the cited ones
KEEP_NEWEST = 5
KEEP_NEWEST_PROFILE = 12
GB = 1024 ** 3


def free_gb(path: Path) -> float:
    return shutil.disk_usage(Path(path).anchor or path).free / GB


def preflight(min_free_gb: float = MIN_FREE_GB, paths: Iterable[Path] | None = None,
              measure=free_gb) -> tuple[bool, str]:
    """(Rule 1) (ok, the line for the evidence or the refusal). `paths` default: %TEMP% and the repository."""
    drives: dict[str, float] = {}
    for path in (paths if paths is not None else (Path(tempfile.gettempdir()), REPO)):
        drives.setdefault(Path(path).anchor or str(path), measure(Path(path)))
    low = {drive: free for drive, free in drives.items() if free < min_free_gb}
    shown = ", ".join(f"{drive} {free:.1f} GB free" for drive, free in sorted(drives.items()))
    if low:
        return False, (f"DISK BUDGET: REFUSED - {', '.join(f'the {d} drive has {f:.1f} GB free' for d, f in sorted(low.items()))}"
                       f", under the {min_free_gb:.0f} GB a sweep needs before it starts (a run writes about 8 MB, and the "
                       f"learner and other sweeps write beside it). Nothing was played. Free space first: `py -3.12 "
                       f"ai_player/gates/disk_budget.py --temp` lists the %TEMP%/ai_* folders earlier sweeps leaked and "
                       f"`--profiles` the old launcher run folders (dry runs; `--apply` deletes)")
    return True, f"DISK BUDGET: {shown} (a sweep needs {min_free_gb:.0f} GB to start)"


def _size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            pass
    return total


class SweepFolders:
    """(Rule 2) Every run folder of one sweep under ONE root, deleted after grading but for the failing and the newest."""

    def __init__(self, tag: str, base: Path | None = None) -> None:
        self.root = Path(tempfile.mkdtemp(prefix=f"ai_sweep_{tag}_", dir=str(base) if base else None))
        self.runs: list[Path] = []

    def new(self, prefix: str) -> Path:
        folder = Path(tempfile.mkdtemp(prefix=prefix, dir=str(self.root)))
        self.runs.append(folder)
        return folder

    def tidy(self, failing: Iterable[Path], keep_all: bool = False, keep_newest: int = KEEP_NEWEST) -> str:
        """Delete every run folder that is not failing and not among the newest `keep_newest`; the line for the evidence."""
        if keep_all:
            return (f"RUN FOLDERS: all {len(self.runs)} KEPT (--keep-runs) under {self.root}, "
                    f"{_size(self.root) / 1024 ** 2:.0f} MB")
        failing_set = {Path(f).resolve() for f in failing}
        existing = [f for f in self.runs if f.is_dir()]
        newest = set(sorted(existing, key=lambda f: f.stat().st_mtime, reverse=True)[:max(0, keep_newest)])
        kept = [f for f in existing if f.resolve() in failing_set or f in newest]
        gone = [f for f in existing if f not in kept]
        freed = 0
        for folder in gone:
            freed += _size(folder)
            shutil.rmtree(folder, ignore_errors=True)
        still = [f for f in gone if f.exists()]
        if not kept and not any(self.root.iterdir()):
            self.root.rmdir()
        return (f"RUN FOLDERS: {len(gone) - len(still)} of {len(existing)} deleted after grading ({freed / 1024 ** 2:.0f} MB "
                f"freed); KEPT {len(kept)}: the failing {len([f for f in kept if f.resolve() in failing_set])} and the "
                f"newest {keep_newest}, under {self.root}{f'; NOT deleted (in use?): {still}' if still else ''} "
                f"(--keep-runs keeps them all)")


def run_failed(folder: Path) -> bool:
    """(Rule 3) A launcher run folder FAILED: no readable `purity.json`, a verdict that is not CLEAN, or a non-zero exit."""
    import json

    try:
        verdict = json.loads((folder / "purity.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True
    facts = verdict.get("facts") or {}
    return verdict.get("verdict") != "CLEAN" or facts.get("exit_code") not in (0, None)


def citing_text(extra: Iterable[Path] = ()) -> str:
    """Every text that may CITE a run folder by name: the evidence (top level and archive), the AI player's README and
    gates, and the project's documents."""
    parts = []
    # (spec S2-1, P9) `ai_player/readme/**/*.md`: the README's sections moved out by `split_readme.py` still cite
    patterns = ("ai_player/evidence/**/*.txt", "ai_player/README.md", "ai_player/readme/**/*.md", "ai_player/LESSONS.md",
                "PROJECT KNOWLEDGE/**/*.md")
    for pattern in patterns:
        for path in REPO.glob(pattern):
            try:
                parts.append(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    for path in extra:
        parts.append(Path(path).read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


_NAME = r"[\w-]+"


def cited_names(text: str) -> set[str]:
    """Every WHOLE name a text cites: each maximal run of word characters and hyphens (a path's folder names among them).
    Built once (a search of the whole corpus per folder took over 10 minutes for 3,000 folders, measured 2026-10-15)."""
    import re

    return set(re.findall(_NAME, text))


def prune_runs(runs: Path, keep: Iterable[Path] = (), keep_newest: int = KEEP_NEWEST_PROFILE, apply: bool = False,
               cited: str | set[str] | None = None) -> tuple[list[Path], list[Path], str]:
    """(Rule 3) The run folders of ONE `ai_player_runs` folder: (deleted or to delete, kept, the line). Kept: `keep` (this
    driver's own runs), the failing, the cited by name, the newest `keep_newest`. `cited`: the citing text, or its
    `cited_names` (default: `citing_text()`)."""
    import re

    folders = sorted((f for f in runs.iterdir() if f.is_dir()), key=lambda f: f.name) if runs.is_dir() else []
    source = citing_text() if cited is None else cited
    names = source if isinstance(source, set) else cited_names(source)
    mine = {Path(f).resolve() for f in keep}
    newest = set(sorted(folders, key=lambda f: f.stat().st_mtime, reverse=True)[:max(0, keep_newest)])
    why: dict[Path, str] = {}
    for folder in folders:
        if folder.resolve() in mine:
            why[folder] = "this run's"
        elif run_failed(folder):
            why[folder] = "failed"
        elif (folder.name in names if re.fullmatch(_NAME, folder.name) else
              isinstance(source, str) and re.search(rf"(?<![\w-]){re.escape(folder.name)}(?![\w-])", source)):
            # cited by its WHOLE name: "20261015-061450-CH2" is not cited by a text naming "20261015-061450-CH2M"
            why[folder] = "cited"
        elif folder in newest:
            why[folder] = "newest"
    kept = [f for f in folders if f in why]
    gone = [f for f in folders if f not in why]
    freed = sum(_size(f) for f in gone)
    if apply:
        for folder in gone:
            shutil.rmtree(folder, ignore_errors=True)
    counts = {reason: sum(1 for r in why.values() if r == reason) for reason in ("this run's", "failed", "cited", "newest")}
    return gone, kept, (f"RUN FOLDERS of {runs.parent.name}: {len(gone)} of {len(folders)} "
                        f"{'deleted' if apply else 'WOULD be deleted (dry run)'} ({freed / 1024 ** 2:.0f} MB); kept {counts}")


def temp_folders(older_than_hours: float = 24.0, base: Path | None = None) -> list[Path]:
    base = Path(base or tempfile.gettempdir())
    cutoff = time.time() - older_than_hours * 3600
    out = []
    for folder in base.glob("ai_*"):
        try:
            if folder.is_dir() and folder.stat().st_mtime < cutoff:
                out.append(folder)
        except OSError:
            pass
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--temp", action="store_true")
    parser.add_argument("--profiles", action="store_true")
    parser.add_argument("--older-than", type=float, default=24.0)
    parser.add_argument("--keep-newest", type=int, default=KEEP_NEWEST_PROFILE)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    ok, line = preflight()
    print(line if ok else line.split(". Nothing was played")[0])
    if args.temp:
        folders = temp_folders(args.older_than)
        by: dict[str, list[int]] = {}
        for folder in folders:
            prefix = "_".join(folder.name.split("_")[:2])
            entry = by.setdefault(prefix, [0, 0])
            entry[0] += 1
            entry[1] += _size(folder)
        for prefix, (count, size) in sorted(by.items(), key=lambda kv: -kv[1][1]):
            print(f"  {prefix}_*: {count} folders, {size / GB:.2f} GB")
        print(f"%TEMP%/ai_* older than {args.older_than:g} h: {len(folders)} folders, "
              f"{sum(s for _, s in by.values()) / GB:.2f} GB: {'DELETING' if args.apply else 'DRY RUN (--apply deletes)'}")
        if args.apply:
            for folder in folders:
                shutil.rmtree(folder, ignore_errors=True)
            print(f"deleted; left: {sum(1 for f in folders if f.exists())}")
        return 0
    if args.profiles:
        names = cited_names(citing_text())
        for runs in sorted(PROFILES.glob("ai-*/ai_player_runs")):
            print("  " + prune_runs(runs, keep_newest=args.keep_newest, apply=args.apply, cited=names)[2], flush=True)
        return 0
    count = sum(1 for _ in Path(tempfile.gettempdir()).glob("ai_*"))
    print(f"%TEMP%/ai_* folders: {count} (`--temp` for their sizes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
