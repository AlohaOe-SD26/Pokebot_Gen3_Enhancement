#!/usr/bin/env python3
"""
SANDBOX installer — sets up, updates, heals, and launches the SANDBOX copy
of the bot (sandbox-pokebot/), where experimental enhancements live until
the user approves them for promotion into custom-pokebot.

Run:  python install_sandbox.py            (same flags as install.py:
      python install_sandbox.py --check-only / --yes)

This is a thin wrapper around install.py — same 7 robust steps, same
logging and self-healing — just pointed at the sandbox directory with its
own log file (install_sandbox.log).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import install

install.BOT_DIR_NAME = "sandbox-pokebot"
# Launch the sandbox test build with audio OFF by default (quiet for testing at
# work); audio stays toggleable in the GUI. Custom is unaffected.
install.LAUNCH_EXTRA_ARGS = ["--no-audio"]
install.LOG_FILE = install.HERE / "install_sandbox.log"
install.SCRIPT_VERSION = install.SCRIPT_VERSION + "-SANDBOX"
install.CRITICAL_FILES = install.CRITICAL_FILES + [
    "modules/backup_manager.py",
]

if __name__ == "__main__":
    try:
        install.main()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\n  Interrupted by user.")
        sys.exit(130)
    except Exception as unhandled:
        import traceback

        install.log.critical("UNHANDLED:\n%s", traceback.format_exc())
        print(f"\n\033[31m  ✗ Unexpected error: {unhandled}\033[0m")
        print(f"  Full details were written to {install.LOG_FILE}")
        sys.exit(1)
