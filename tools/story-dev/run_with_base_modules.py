"""Run the story harness with chosen PRODUCTION MODULES taken from an older commit, in THIS worktree.

WHY (playbook §3e; design v2 step 11). A live run that leaves a predicted trajectory must be attributed: the build, or
KI-112's run-to-run nondeterminism? The only admissible answer is a run of the BASE code under everything else held
equal. A checkout or a second worktree changes the untracked profile and caches too; this changes only the code. It
loads the base source of each named module (`git show <base>:<path>`) into `sys.modules` under its real name and file
path BEFORE the harness imports it, seeds `random` exactly as the seeded wrapper does, and runs `story_harness.py`.

⛔ Name EVERY production module the build changed. The run then asserts that no module the build ADDED under
`sandbox-pokebot/modules` or `sandbox-pokebot/plugins` was imported, which is how a forgotten module shows itself: the
build's copy of a changed module imports the build's new code. (Design v2 step 12, D14: `plugins.custom_modes.*` is
accepted too, since `story_mode.py` is imported as `plugins.custom_modes.story_mode`.)

Run from tools/story-dev:
  PYTHONUTF8=1 py -3.12 -u run_with_base_modules.py <base-commit> <path>[,<path>...] <harness args...>
  e.g.  ... run_with_base_modules.py 241929d7 \
            sandbox-pokebot/modules/battle_action_selection.py,sandbox-pokebot/modules/battle_handler.py \
            saves/post_mtpyre.ss1 --driver storyresume --frames 90000 --log out.log
"""
import importlib.util
import os
import random
import runpy
import subprocess
import sys
from pathlib import Path


def _module_name(rel: str) -> str:
    parts = Path(rel).with_suffix("").parts
    assert parts[0] == "sandbox-pokebot" and parts[1] in ("modules", "plugins"), f"not a sandbox-pokebot module: {rel}"
    return ".".join(parts[1:])


def _added_modules(repo: Path, base: str) -> list[str]:
    out = subprocess.run(["git", "-C", str(repo), "diff", "--name-only", "--diff-filter=A", base, "HEAD", "--",
                          "sandbox-pokebot/modules", "sandbox-pokebot/plugins"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return [_module_name(p) for p in out.split() if p.endswith(".py")]


def main() -> None:
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    base, paths, harness_args = sys.argv[1], sys.argv[2].split(","), sys.argv[3:]
    repo = Path(os.getcwd()).resolve().parents[1]
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, str(repo / "sandbox-pokebot"))
    import modules  # noqa: F401  (the package, so each submodule can be registered on its parent)

    injected = {}
    for rel in paths:
        name = _module_name(rel)
        src = subprocess.run(["git", "-C", str(repo), "show", f"{base}:{rel}"], capture_output=True, text=True,
                             encoding="utf-8", check=True).stdout
        path = str(repo / rel)
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        parent, _, leaf = name.rpartition(".")
        setattr(sys.modules[parent] if parent in sys.modules else importlib.import_module(parent), leaf, mod)
        exec(compile(src, path, "exec"), mod.__dict__)
        injected[name] = mod
        print(f"# run_with_base_modules: {name} loaded from {base} ({len(src)} chars)", flush=True)
    added = _added_modules(repo, base)
    early = [m for m in added if m in sys.modules]
    assert not early, f"build-only module(s) imported while loading the base: {early}"
    random.seed(1)
    sys.argv = ["story_harness.py"] + harness_args
    try:
        runpy.run_path("story_harness.py", run_name="__main__")
    finally:
        late = [m for m in added if m in sys.modules]
        print(f"# run_with_base_modules: build-only modules imported during the run: {late or 'none'}", flush=True)
        # every injected module must still be THE module under its name: a loader that re-imported it (by path, or a
        # reload) would have run the build's copy silently
        swapped = [n for n, m in injected.items() if sys.modules.get(n) is not m]
        print(f"# run_with_base_modules: injected modules replaced during the run: {swapped or 'none'}", flush=True)
        assert not late, f"a changed module was NOT named, so the build's copy ran: it imported {late}"
        assert not swapped, f"an injected base module was replaced during the run: {swapped}"


if __name__ == "__main__":
    main()
