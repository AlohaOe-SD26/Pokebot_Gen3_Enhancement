"""Command line for the AI player.

    py -3.12 -m ai_player run --profile NAME [--frames N] [--wall-seconds S]
                              [--fresh | --state PATH] [--build-root DIR] [--template-profile NAME]
                              [--run-dir DIR] [--allow-ungated]

Run it from the folder that CONTAINS `ai_player/` (the repo root). It runs the purity gate on this very
package (and refuses to launch on a FAIL, exit 7), creates the profile if needed, seeds its game state,
starts the framework headless in "AI Player" mode in a child process, echoes the child's output, and
exits with the child's exit code, EXCEPT that a child exiting 0 without a CLEAN verdict file from its
instrument makes it exit 8.

Two wall clocks: the mode ends ITSELF at a soft deadline a few seconds early (`reason=wall-clock`,
code 124, verdict written); if it is stuck and cannot, the launcher kills the whole process tree at
the hard deadline (code 124, and a line saying the run has NO purity verdict). Fault and control
switches are environment variables; see `ai_player/options.py` and the README.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from ai_player import MODE_NAME
from ai_player.options import ALL_SWITCHES, VERDICT_FILE_NAME
from ai_player.platform.launcher import (
    GATE_REFUSED_EXIT,
    NO_VERDICT_EXIT,
    UNTRUSTED_ENV,
    ChildResult,
    LaunchError,
    bot_command,
    child_env,
    ensure_profile,
    package_root,
    read_verdict,
    resolve_build_root,
    run_child,
    run_gate,
    seed_profile,
    soft_deadline_margin,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ai_player", description="The Emerald AI player.")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help=f"play in the framework's '{MODE_NAME}' mode, headless")
    run.add_argument("--profile", required=True, help="profile name under <build root>/profiles/")
    run.add_argument("--frames", type=int, default=3000, help="the brain's frame budget (default 3000)")
    run.add_argument("--wall-seconds", type=float, default=600.0, help="hard wall clock for the child (default 600)")
    seed = run.add_mutually_exclusive_group()
    seed.add_argument("--fresh", action="store_true", help="wipe the profile's game state: boot to New Game")
    seed.add_argument("--state", type=Path, help="seed the profile from this save state (.ss1)")
    run.add_argument("--build-root", help="the framework folder holding pokebot.py (default: ../sandbox-pokebot)")
    run.add_argument("--template-profile", help="profile to copy metadata.yml from when creating one")
    run.add_argument("--run-dir", type=Path, help="where this run's ai_player.log and purity.json go (default: inside the profile)")
    run.add_argument(
        "--allow-ungated",
        action="store_true",
        help="launch even if the purity gate FAILS on the package (fault arms only: they test the live "
        "audit on code the static gate refuses)",
    )
    return parser


def _gate(build_root: Path, allow_ungated: bool) -> bool:
    """Gate the package the child will load. Returns False when the launch must be refused."""
    gate = run_gate(build_root)
    package = package_root() / "ai_player"
    print(f"[AI-GATE] exit={gate.exit_code} verdict={'PASS' if gate.passed else 'FAIL'} package={package}", flush=True)
    if gate.passed:
        return True
    for line in gate.findings()[:25]:
        print(f"[AI-GATE] {line}", flush=True)
    if not allow_ungated:
        print(
            "[AI-GATE] refusing to launch: the purity gate failed on the package the framework would load "
            f"(exit {GATE_REFUSED_EXIT}); fix the findings, or pass --allow-ungated for a fault arm",
            flush=True,
        )
        return False
    print("[AI-GATE] launching ANYWAY (--allow-ungated): this run is a fault arm, not an AI run", flush=True)
    return True


def _report_verdict(run_dir: Path, result: ChildResult) -> int:
    """Read the instrument's verdict file and decide the launcher's exit code from it."""
    verdict = read_verdict(run_dir)
    if verdict is None:
        print(f"[AI-RUN] NO VERDICT FILE: {run_dir / VERDICT_FILE_NAME} was not written by the instrument", flush=True)
    else:
        facts = verdict.get("facts") or {}
        print(
            f"[AI-RUN] verdict file: verdict={verdict.get('verdict')} exit_reason={facts.get('exit_reason')} "
            f"exit_code={facts.get('exit_code')} pid={verdict.get('pid')} "
            f"package_is_the_gated_one={facts.get('package_root') == str(package_root())}",
            flush=True,
        )
    if result.killed or result.exit_code != 0:
        return result.exit_code
    facts = (verdict or {}).get("facts") or {}
    certified = (
        verdict is not None
        and verdict.get("verdict") == "CLEAN"
        and facts.get("exit_code") == 0
        and facts.get("package_root") == str(package_root())
    )
    if certified:
        return 0
    print(
        f"[AI-RUN] the child exited 0, but its instrument did not certify a CLEAN finish of the gated package; "
        f"exit {NO_VERDICT_EXIT}",
        flush=True,
    )
    return NO_VERDICT_EXIT


def cmd_run(args: argparse.Namespace) -> int:
    if args.frames <= 0:
        print("[AI-RUN] --frames must be positive", flush=True)
        return 2
    if args.wall_seconds <= 0:
        print("[AI-RUN] --wall-seconds must be positive", flush=True)
        return 2
    try:
        build_root = resolve_build_root(args.build_root)
    except LaunchError as error:
        print(f"[AI-RUN] cannot start: {error}", flush=True)
        return 2
    if not _gate(build_root, args.allow_ungated):
        return GATE_REFUSED_EXIT
    try:
        profile_dir, profile_note = ensure_profile(build_root, args.profile, args.template_profile)
        state_note = seed_profile(profile_dir, args.state.resolve() if args.state else None, args.fresh)
    except LaunchError as error:
        print(f"[AI-RUN] cannot start: {error}", flush=True)
        return 2

    run_dir = (args.run_dir or profile_dir / "ai_player_runs" / time.strftime("%Y%m%d-%H%M%S")).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    stale = run_dir / VERDICT_FILE_NAME
    if stale.exists():
        stale.unlink()  # a verdict file must come from THIS run
    cmd = bot_command(build_root, args.profile)
    env = child_env(args.frames, run_dir, args.wall_seconds)
    switches = [f"{name}={env[name]}" for name in ALL_SWITCHES if env.get(name)]
    dropped = [name for name in UNTRUSTED_ENV if name in os.environ]

    print(profile_note, flush=True)
    print(state_note, flush=True)
    print(
        f"[AI-RUN] build_root={build_root} frames={args.frames} wall_seconds={args.wall_seconds:g} "
        f"soft_deadline_margin={soft_deadline_margin(args.wall_seconds):g}s switches={','.join(switches) or 'none'} "
        f"dropped_env={','.join(dropped) or 'none'}",
        flush=True,
    )
    print(f"[AI-RUN] run_dir={run_dir}", flush=True)
    print(f"[AI-RUN] command={' '.join(cmd)}", flush=True)

    result = run_child(cmd, build_root, env, args.wall_seconds, run_dir / "stdout.txt")
    if result.killed:
        print(
            f"[AI-RUN] WALL CLOCK: {args.wall_seconds:g}s reached; killed process tree pids={result.killed_pids} "
            f"survivors={result.survivors}",
            flush=True,
        )
        print(
            "[AI-RUN] NO PURITY VERDICT: the child was killed before it could report one "
            "(it did not reach its soft deadline, so it was stuck); treat this run as UNVERIFIED",
            flush=True,
        )
    print(
        f"[AI-RUN] child exit code={result.exit_code} elapsed={result.elapsed:.1f}s killed={result.killed}",
        flush=True,
    )
    return _report_verdict(run_dir, result)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = _parser().parse_args(argv)
    if args.command == "run":
        return cmd_run(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
