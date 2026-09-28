"""Acceptance: a debug log must be SELF-DESCRIBING (user directive 2026-07-29).

USER, verbatim: *"all of this should be native to the debug logging... I should not have to
make arbitrary cmd commands to do this, why is this not native to the debug logs? including
version numbers and extensive details?"*

They were right. The header used to be TWO LINES — a timestamp and the log path:

    === DEBUG LOG START 2026-07-29T12:02:35 ===
        log: C:\\...\\Story_(ENDLESS_RESET)-debug-20260729-120235.log

So a shared log could not answer, on its own:
  * which BUILD produced it (needed `git log` on the machine that made it);
  * which experiment ARM it belonged to (unanswerable after the fact);
  * what Python / ROM / profile / emulation settings were in play.
Three separate times a log had to be sent back to the user with "please run this command".

A forensic artefact must identify itself. This repro pins that.

No emulator needed.
"""
import sys
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

import os  # noqa: E402

os.environ["POKEBOT_FODDER_RULE"] = "xp_rate"

from modules import debug_logger as dl  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


def capture_header():
    out = []
    real = dl._raw
    dl._raw = lambda s: out.append(s)
    try:
        dl._write_run_header()
    finally:
        dl._raw = real
    return "\n".join(out)


header = capture_header()
print("--- captured header ---")
print(header)
print("-----------------------\n")

print("== the header identifies the BUILD ==")
check("RUN HEADER" in header, "a RUN HEADER block is emitted")
check("build:" in header, "it states the build")
g = dl._git_facts()
check("commit" in g and len(g["commit"]) >= 7,
      f"the commit is read from .git (got {g.get('commit')!r})")
check("branch" in g, f"and the branch (got {g.get('branch')!r})")
check(g["commit"] in header, "the commit appears in the header text")

print("\n== it is read WITHOUT shelling out to git ==")
# `git` is frequently absent from PATH on a machine that only runs the installer, and a
# subprocess costs ~50-150ms on Windows. Reading .git/HEAD is two file reads and always works.
src = (SANDBOX / "modules" / "debug_logger.py").read_text(encoding="utf-8")
start = src.index("def _git_facts")
end = src.index("\ndef ", start + 10)
body = src[start:end]
# Strip the docstring first: it MENTIONS subprocess to explain why it is avoided, and a
# naive substring test matches that prose instead of the code (caught by this repro).
code_only = body.split('"""')[-1] if '"""' in body else body
check("subprocess" not in code_only,
      "_git_facts contains no subprocess call in its CODE (its docstring may mention one)")
check(".git" in body and "HEAD" in body, "it reads .git/HEAD directly")
check("packed-refs" in body,
      "and falls back to packed-refs (a freshly-cloned repo has no loose ref file)")

print("\n== it records the EXPERIMENT ARM ==")
check("fodder-rule:" in header, "the active training-relocation rule is stated")
check("xp_rate" in header, "the value is the one actually in effect")
check("(env)" in header, "and HOW it was set (env vs default) — so a default is not mistaken for a choice")
check("POKEBOT_FODDER_RULE" in header, "the raw env var is echoed too")
check("POKEBOT_FODDER_RULE" in dl._BEHAVIOUR_ENV_VARS,
      "the behaviour-env-var list covers it (new flags must be added here)")
# USER RULING 20 Phase 2 step T (M5, 2026-09-28): EVERY `POKEBOT_*` is echoed on its own `env-all:` line, by prefix,
# beside the curated `env:` line above — so an A/B arm's flag or fault arm is visible in the run's own log even when
# nobody added it to `_BEHAVIOUR_ENV_VARS`. (The registered gate `probe_r20_telemetry.py` holds the fault arm.)
_envall = [ln for ln in header.splitlines() if "env-all:" in ln]
check(len(_envall) == 1 and "POKEBOT_FODDER_RULE" in _envall[0],
      "an `env-all:` line echoes every POKEBOT_* variable by prefix (RULING 20 step T, M5)")

print("\n== it records the ENVIRONMENT ==")
check("python:" in header, "the Python version and OS")
check("bot:" in header, "the bot name/version")

print("\n== a default (no env var) is reported honestly, not omitted ==")
del os.environ["POKEBOT_FODDER_RULE"]
import importlib  # noqa: E402

from modules.story import training_areas as ta  # noqa: E402

importlib.reload(ta)
h2 = capture_header()
# ‼ Assert the SHAPE, not the value. The default flipped legacy -> xp_rate on 2026-07-29
# and this assertion hard-coded "legacy", so it failed on a deliberate change. What a log
# reader needs is that the header NAMES the active rule and says it came from the default
# rather than a choice — not which value happens to be default this week.
check("(default)" in h2,
      "with no env var the header marks the rule as coming from the DEFAULT")
check(ta.FODDER_RULE in h2,
      f"and names the actual default value, whatever it is (got {ta.FODDER_RULE!r})")
check("no behaviour env vars set" in h2,
      "and explicitly says none were set — silence is not evidence")

print("\n== NOTHING here can break logging ==")
# Every fact is optional; a failure to read one must degrade that line, never raise.
broken = dl._git_facts.__wrapped__ if hasattr(dl._git_facts, "__wrapped__") else None
saved = dl._git_facts
dl._git_facts = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
try:
    h3 = capture_header()
    check("RUN HEADER" in h3, "a failing git read still produces a header")
    check("unknown" in h3, "and the build line degrades to 'unknown'")
except Exception as exc:  # noqa: BLE001
    check(False, f"_write_run_header raised: {type(exc).__name__}: {exc}")
finally:
    dl._git_facts = saved

print("\n== the header is written on enable(), before the first dump ==")
i_start = src.index("=== DEBUG LOG START")
# ‼ Search AFTER the START line for the CALL — a bare .index() finds the `def
# _write_run_header()` line instead, which sits earlier in the file (caught by this repro;
# same class of error as anchoring on text that also appears in a docstring).
i_hdr = src.index("_write_run_header()", i_start)
i_dump = src.index('_dump("enable — initial state")', i_start)
check(i_start < i_hdr < i_dump,
      "enable() emits: START line -> RUN HEADER -> initial state dump")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
