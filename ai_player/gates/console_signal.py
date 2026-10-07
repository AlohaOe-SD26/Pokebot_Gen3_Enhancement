"""TEST SIDE: run a command in THIS process's console and send it Ctrl+C or Ctrl+Break (Windows).

    py -3.12 ai_player/gates/console_signal.py --kind break|c --wait "<text>" [--delay S] [--timeout S] -- CMD...

WHY IT EXISTS (step 0.1, the adversarial review's finding 7): a Ctrl+C that landed outside the AI's
generator ended the framework process with no verdict. The fix is a handler that only sets a flag,
which the guard turns into `reason=interrupted` with a verdict; the live arms IB / IC must deliver a
REAL console control event to a real framework process to prove it. Windows delivers those only to
processes attached to the sender's console, and the live driver may have none (and the launcher runs
the framework with CREATE_NO_WINDOW), so the driver starts THIS helper in a new, hidden console; the
helper starts the framework in that same console and sends the event:

  break  the child gets its own process group and `CTRL_BREAK_EVENT` is sent to that group only
         (Python sees SIGBREAK; with no handler Windows simply terminates the process);
  c      `CTRL_C_EVENT` goes to every process on the console (Windows cannot target one group with
         it). The helper re-enables Ctrl+C for itself first (a process started without it would pass
         "ignore Ctrl+C" on to the child) and catches its own copy with a no-op handler.

It echoes the child's output, prints `[SIGNAL] ...` lines saying what it sent and when, waits for the
child (bounded), kills its tree if it did not exit, and exits with the child's exit code.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import threading
import time


def kill_tree(pid: int) -> list[int]:
    try:
        import psutil
    except ImportError:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)
        return [pid]
    try:
        root = psutil.Process(pid)
        procs = [root] + root.children(recursive=True)
    except psutil.Error:
        return []
    for proc in reversed(procs):
        try:
            proc.kill()
        except psutil.Error:
            pass
    return [proc.pid for proc in procs]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--kind", choices=("break", "c"), required=True)
    parser.add_argument("--wait", required=True, help="send the event this many seconds after a line containing this text")
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=120.0, help="hard bound on the whole run")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if os.name != "nt":
        print("[SIGNAL] Windows only", flush=True)
        return 2
    if args.kind == "c":
        import ctypes

        ctypes.windll.kernel32.SetConsoleCtrlHandler(None, False)  # inherited by the child: Ctrl+C enabled
        signal.signal(signal.SIGINT, lambda number, frame: None)  # this helper ignores its own copy
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if args.kind == "break" else 0
    start = time.monotonic()
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             creationflags=flags, env=os.environ.copy())
    seen = threading.Event()

    def pump() -> None:
        assert child.stdout is not None
        for raw in iter(child.stdout.readline, b""):
            text = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            print(text, flush=True)
            if args.wait in text:
                seen.set()

    reader = threading.Thread(target=pump, daemon=True)
    reader.start()
    sent = False
    if seen.wait(timeout=max(1.0, args.timeout - 30)):
        time.sleep(args.delay)
        if child.poll() is None:
            event = signal.CTRL_BREAK_EVENT if args.kind == "break" else signal.CTRL_C_EVENT
            os.kill(child.pid if args.kind == "break" else 0, event)
            sent = True
            print(f"[SIGNAL] sent {'CTRL_BREAK_EVENT to the child process group' if args.kind == 'break' else 'CTRL_C_EVENT to the console'} "
                  f"(child pid {child.pid}) {time.monotonic() - start:.1f}s after start", flush=True)
    else:
        print(f"[SIGNAL] never saw {args.wait!r}; no event sent", flush=True)
    remaining = max(5.0, args.timeout - (time.monotonic() - start))
    try:
        code = child.wait(timeout=remaining)
        print(f"[SIGNAL] child exited by itself: code={code} sent={sent} elapsed={time.monotonic() - start:.1f}s", flush=True)
    except subprocess.TimeoutExpired:
        pids = kill_tree(child.pid)
        child.wait(timeout=30)
        code = child.returncode
        print(f"[SIGNAL] child did NOT exit within the bound; killed tree {pids} (code {code})", flush=True)
    reader.join(timeout=10)
    return int(code if code is not None else 1)


if __name__ == "__main__":
    sys.exit(main())
