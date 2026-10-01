"""GATE — prove `.claude/hooks/block_shell_text.py` can still BLOCK, still ALLOW, still SPEAKS VALID JSON, and fails OPEN.

WHY THIS EXISTS (USER RULING 29, 2026-10-01; `08-MISTAKES.md` 2026-09-30 and 2026-10-01). The written rule
"documentation and code text never pass through a shell-quoted string" was broken FIVE times in two sessions; CLAUDE.md
rule 6 turns a rule broken repeatedly into a gate. The hook reuses `block_destructive_git.py`'s parser, so a change
there can break this hook too: this gate is what notices.

WHAT IT CHECKS (the destructive-git gate's shape; its first version's failure, output Claude Code could not parse, is
why S5/S6 read the REAL process output):
  S1  the hook's case table passes (the five real incidents, H1-H11, every finding of the 2026-10-01 adversarial pass in
      both directions, mentions, ordinary work, the hatch);
  S2  FAULT ARM: the decision forced to ALWAYS-ALLOW must FAIL the table;
  S3  FAULT ARM: the decision forced to ALWAYS-BLOCK must FAIL the table;
  S4  registered in `.claude/settings.json` (PreToolUse, Bash|PowerShell) through "$CLAUDE_PROJECT_DIR/.claude/hooks/"
      and ending in `|| true` (the destructive gate's S7 covers every hook's shape; this pins THIS hook's entry);
  S5  THE REAL HOOK PROCESS: a Bash heredoc and a PowerShell here-string written to a file each print ASCII JSON with
      permissionDecision "deny"; a non-ASCII body still yields ASCII JSON; an ordinary command prints NOTHING; garbage
      stdin prints nothing and exits 0; the hook copied WITHOUT its parser module, and the hook beside a parser whose
      functions RAISE, both fail OPEN (nothing, exit 0);
  S6  FAULT ARM: a mutant hook printing plain text is REJECTED by the S5 JSON check;
  S7  EVERY RULE IS LOAD-BEARING: each rule (and each false-positive fix) reverted IN MEMORY - one exact source snippet
      replaced, the mutated source exec'd as a fresh module, nothing on disk touched - must FAIL the case table. A
      rule whose rows still pass without it has rows that test nothing. A snippet not found exactly once is a FAIL
      (update this table with the hook).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 selftest_shell_text_hook.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import types
from contextlib import redirect_stdout
from pathlib import Path

BAR = "=" * 92
ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = ROOT / ".claude" / "hooks" / "block_shell_text.py"
SETTINGS = ROOT / ".claude" / "settings.json"
failures: list = []

# S7: (finding, exact snippet in the hook, its in-memory replacement). Each reverts ONE rule or fix.
MUTANTS = [
    ("FP-1 python -c never feeds H6", "    if head in PYTHONS:\n        i = 1\n        while i < len(rest):\n            t = rest[i]\n            if C_OPT.fullmatch(t) or t == \"-\":",
     "    if head in PYTHONS and any(t.lower().endswith('.py') for t in rest[1:]):\n        return True\n    if head in PYTHONS:\n        i = 1\n        while i < len(rest):\n            t = rest[i]\n            if C_OPT.fullmatch(t) or t == \"-\":"),
    ("FP-2 prose needs spaces", "return sum(len(t) for t in args if t.count(\" \") >= PROSE_SPACES)", "return sum(len(t) for t in args)"),
    ("FP-3 no visible text", "    return bool(re.sub(r\"(?:^|(?<=\\s))-[neE]+", "    return True or bool(re.sub(r\"(?:^|(?<=\\s))-[neE]+"),
    ("BH-08 quoted '<<'", "        return False\n    st, i, n = \"N\", 0, len(clean)", "        return False\n    return True\n    st, i, n = \"N\", 0, len(clean)"),
    ("BH-08 no PowerShell H1", "    if shell == \"ps\":\n        return False\n    st, i, n", "    if shell == \"ps\":\n        return True\n    st, i, n"),
    ("BH-12 H2 needs no script", "if \"<<<\" in cmd and head in INTERPRETERS and _program_from_stdin(head, rest):", "if \"<<<\" in cmd and head in INTERPRETERS:"),
    ("BH-01 git -m newline", "if \"\\n\" in v or len(v) > ECHO_MAX:", "if len(v) > ECHO_MAX:"),
    ("BH-01 git -m length", "if \"\\n\" in v or len(v) > ECHO_MAX:", "if \"\\n\" in v:"),
    ("BH-01 git -m bash substitution", "if shell == \"bash\" and val.q != \"'\" and \"$(\" in v and not CAT_FILE.fullmatch(v.strip()):", "if False:"),
    ("BH-01 git -m PowerShell backtick", "(\"$\" in v or dq_bt)", "(\"$\" in v)"),
    ("BH-04 here-string -m", "if (val.q == \"'\" and v == \"HERESTRING\") or v.lower() in here_vars:", "if False:"),
    ("BH-04 literal into git -F -", "if f == \"-\" and (piped or \"<<<\" in vals):", "if False:"),
    ("BH-09 echo-built -F file", "if f != \"-\" and f in written:", "if False:"),
    ("BH-09 live backtick into a file", "if live_bt and kind == \"echo\" and \"$(\" in lit_text:", "if False:"),
    ("BH-02 PowerShell writer literal", "if lit and files:", "if False:"),
    ("BH-02 PowerShell bare literal", "if kind == \"literal\" and (any(_is_doc(t) for t in tg) or lit_len > ECHO_MAX):", "if False:"),
    ("BH-02 [IO.File]::WriteAll*", "r = _iofile_reason(clean, here_vars)", "r = None"),
    ("BH-03 sed/perl/awk -i", "if inplace and any(_is_doc(f) for f in files):", "if False:"),
    ("BH-03 the edit script is not a file", "files = pos if script_given else pos[1:]", "files = pos"),
    ("BH-03 PowerShell -replace", "if REPLACE_RE.search(clean):", "if False:"),
    ("BH-03 find -exec", "r = _find_exec_reason(rest, p, depth)", "r = None"),
    ("BH-05 prose threshold", "return sum(len(t) for t in args if t.count(\" \") >= PROSE_SPACES)",
     "return max([len(t) for t in args] or [0]) if max([len(t) for t in args] or [0]) > 300 else 0"),
    ("BH-05 -m module", "            if re.match(r\"-[A-Za-z]*m\", t):\n                return True", "            if False:\n                return True"),
    ("BH-05 .sh script", "return t.lower().endswith((\".sh\", \".bash\"))", "return False"),
    ("BH-05 .ps1 script", "    if head.endswith(\".ps1\"):\n        return True", "    if False:\n        return True"),
    ("BH-06 literal pipelines", "r, files = _pipe_into_reason(ws, vals, h, tg, kind, lit_text, lit_len, live_bt)", "r, files = None, []"),
    ("BH-06 <<< by cat/tee", "if \"<<<\" in vals and h in {\"cat\", \"tee\"}:", "if False:"),
    ("BH-07 write regex", "    r\"|\\bopen\\s*\\((?:[^()]|\\([^()]*\\))*?['\\\"](?:[wax]|r[bt]?\\+)[bt+]*['\\\"]\"\n    r\"|\\bos\\.open\\s*\\([^)]*O_(?:WRONLY|RDWR|APPEND|CREAT)|\\binplace\\s*=\\s*True\")",
     "    r\"|\\bopen\\s*\\([^,)]*,\\s*(mode\\s*=\\s*)?['\\\"][wax]\")"),
    ("BH-07 -c bundles", "C_OPT = re.compile(r\"-[A-Za-z]*c\")", "C_OPT = re.compile(r\"-c\")"),
    ("BH-07 -c output into a doc", "            if any(_is_doc(t) for t in targets):\n                return \"`python -c` output",
     "            if False:\n                return \"`python -c` output"),
    ("BH-10 line-wide H3 targets", "line_targets = [t for c in cmds for t in _out_targets(p._strip_prefix(c)[0])] if herestring_line else []", "line_targets = []"),
    ("BH-10 nulls and 2> ignored", "if t in OUT_REDIR and toks[j + 1].lower() not in NULLS and not (j > 0 and re.fullmatch(r\"[2-9]\", toks[j - 1])):", "if t in OUT_REDIR:"),
    ("BH-11 wider extensions", "|py|pyw|ps1|psm1|json|jsonl|yml|yaml|toml|ini|cfg|sh|bash|bat|cmd|\"\n                         r\"html|js|ts|css)",
     "|py|ps1|json|jsonl|yml|yaml)\"\n                         r\"()"),
]


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        failures.append(msg)


def load_hook():
    spec = importlib.util.spec_from_file_location("block_shell_text", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_hook(payload, hook_path: Path = HOOK) -> "tuple[int, str]":
    data = payload if isinstance(payload, str) else json.dumps(payload)
    r = subprocess.run([sys.executable, str(hook_path)], input=data, capture_output=True, text=True, encoding="utf-8",
                       timeout=30, cwd=str(ROOT))
    return r.returncode, (r.stdout or "").strip()


def deny_is_valid(out: str) -> bool:
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny" and out.isascii()
    except (ValueError, KeyError, TypeError):
        return False


def mutant_table_fails(src: str, old: str, new: str) -> "tuple[bool, str]":
    """Exec `src` with `old` replaced by `new` as a fresh in-memory module; True when its case table FAILS."""
    if src.count(old) != 1:
        return False, f"snippet found {src.count(old)} times"
    mod = types.ModuleType("block_shell_text_mutant")
    mod.__dict__["__file__"] = str(HOOK)
    sys.modules["block_shell_text_mutant"] = mod
    exec(compile(src.replace(old, new, 1), str(HOOK), "exec"), mod.__dict__)  # noqa: S102 - our own file, mutated
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.run_selftest()
    red = sum(1 for ln in buf.getvalue().splitlines() if ln.strip().startswith("FAIL"))
    return rc != 0, f"{red} row(s) red"


def main() -> int:
    print(BAR)
    print("GATE — the shell-text hook blocks text written through the shell, allows ordinary work, emits valid JSON")
    print(BAR)
    if not HOOK.exists():
        print(f"  ⛔ MISSING: {HOOK} — the hook USER RULING 29 approved is not on disk. A failure, not a skip.")
        return 1
    hook = load_hook()

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = hook.run_selftest()
    for line in buf.getvalue().splitlines():
        print(f"    {line.strip()}")
    check(rc == 0, "S1 the hook's case table passes")

    for tag, label, forced in (("S2", "ALWAYS-ALLOW", None), ("S3", "ALWAYS-BLOCK", "forced")):
        with redirect_stdout(io.StringIO()):
            mrc = hook.run_selftest(decide=lambda text, shell, f=forced: f)
        check(mrc != 0, f"{tag} FAULT ARM — decision forced to {label} — makes the case table FAIL")

    try:
        cfg = json.loads(SETTINGS.read_text(encoding="utf-8"))
        cmds = [h.get("command", "") for e in cfg.get("hooks", {}).get("PreToolUse", [])
                if "Bash" in e.get("matcher", "") and "PowerShell" in e.get("matcher", "")
                for h in e.get("hooks", [])]
        mine = [c for c in cmds if "block_shell_text.py" in c]
    except (OSError, ValueError) as err:
        print(f"  ‼ could not read {SETTINGS}: {err}")
        mine = []
    check(len(mine) == 1 and "$CLAUDE_PROJECT_DIR/.claude/hooks/block_shell_text.py" in mine[0]
          and mine[0].rstrip().endswith("|| true"),
          f"S4 registered ONCE in .claude/settings.json (PreToolUse, Bash|PowerShell), via $CLAUDE_PROJECT_DIR, "
          f"ending '|| true' (got {mine})")

    cases = (("Bash", "cat > a.md <<'EOF'\nsome text\nEOF"),
             ("PowerShell", "@'\nsome text\n'@ | Set-Content a.md"),
             ("Bash", "cat > a.md <<'EOF'\nrésumé — café\nEOF"))
    for tool, cmd in cases:
        rc, out = run_hook({"tool_name": tool, "tool_input": {"command": cmd}, "cwd": str(ROOT)})
        try:
            dec = json.loads(out)["hookSpecificOutput"]["permissionDecision"]
        except (ValueError, KeyError, TypeError):
            dec = f"UNPARSEABLE: {out[:120]!r}"
        check(rc == 0 and dec == "deny" and out.isascii(),
              f"S5 [{tool}] {cmd[:36]!r} -> valid ASCII JSON deny (got {dec!r}, rc={rc})")
    rc, out = run_hook({"tool_name": "Bash", "tool_input": {"command": "git status --short && grep -n '<<EOF' a.md"},
                        "cwd": str(ROOT)})
    check(rc == 0 and out == "", f"S5 an ordinary command (with a QUOTED '<<EOF' mention) prints NOTHING (got {out[:80]!r})")
    rc, out = run_hook("this is not json")
    check(rc == 0 and out == "", f"S5 garbage stdin fails OPEN: nothing printed, exit 0 (rc={rc}, out={out[:60]!r})")
    with tempfile.TemporaryDirectory() as tmp:
        lone = Path(tmp) / "block_shell_text.py"
        shutil.copy2(HOOK, lone)
        rc, out = run_hook({"tool_name": "Bash", "tool_input": {"command": cases[0][1]}, "cwd": str(ROOT)}, lone)
        check(rc == 0 and out == "",
              f"S5 WITHOUT its parser module the hook fails OPEN: nothing printed, exit 0 (rc={rc}, out={out[:60]!r})")
    with tempfile.TemporaryDirectory() as tmp:
        beside = Path(tmp) / "block_shell_text.py"
        shutil.copy2(HOOK, beside)
        (Path(tmp) / "block_destructive_git.py").write_text(
            "def _boom(*a, **k):\n    raise RuntimeError('parser fault arm')\n\n"
            "commands = _prescan_bash = _prescan_ps = _strip_prefix = substitutions = _shell_inner = _is_sep = _boom\n"
            "PUNCT = ';&|()<>\\n'\nGIT_GLOBAL_WITH_VALUE = set()\n", encoding="utf-8")
        rc, out = run_hook({"tool_name": "Bash", "tool_input": {"command": cases[0][1]}, "cwd": str(ROOT)}, beside)
        check(rc == 0 and out == "",
              f"S5 beside a parser whose functions RAISE the hook fails OPEN: nothing printed, exit 0 (rc={rc}, "
              f"out={out[:60]!r})")

    src = HOOK.read_text(encoding="utf-8")
    anchor = "            print(json.dumps({"
    if src.count(anchor) == 1:
        with tempfile.TemporaryDirectory() as tmp:
            mut = Path(tmp) / "block_shell_text.py"
            shutil.copy2(HOOK.parent / "block_destructive_git.py", Path(tmp) / "block_destructive_git.py")
            mut.write_text(src.replace(anchor, "            print('BLOCKED \\u2014 not json'); (json.dumps({", 1),
                           encoding="utf-8")
            _rc, mout = run_hook({"tool_name": "Bash", "tool_input": {"command": cases[0][1]}, "cwd": str(ROOT)}, mut)
            check(bool(mout) and not deny_is_valid(mout),
                  f"S6 FAULT ARM — a hook printing non-JSON is REJECTED by the S5 check (got {mout[:50]!r})")
    else:
        check(False, "S6 (mutation anchor not found exactly once — update the gate)")

    weak = []
    for name, old, new in MUTANTS:
        red, how = mutant_table_fails(src, old, new)
        if not red:
            weak.append(f"{name} ({how})")
    check(not weak, f"S7 every rule is LOAD-BEARING: {len(MUTANTS)} in-memory mutants, each reverting one rule or fix, "
                    f"each FAILS the case table (not load-bearing: {weak or 'none'})")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print(f"  {f}")
        return 1
    print("PASS — text written through the shell gets a VALID deny, ordinary work passes, every mutant fails the table.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
