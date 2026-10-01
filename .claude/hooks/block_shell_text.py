r"""PreToolUse(Bash|PowerShell) hook - REFUSE documentation or code text written THROUGH THE SHELL.

WHY (USER RULING 29, 2026-10-01; `08-MISTAKES.md` 2026-09-30 and 2026-10-01): the written rule "documentation and code
text never pass through a shell-quoted string; use Write/Edit, or a script file written with Write and then run" was
broken FIVE times in two sessions. Every slip happened to be harmless, but shell quoting silently rewrites backslashes,
`$` and backticks, and the next one lands in a doc or a gate. CLAUDE.md rule 6: a rule broken repeatedly is evidence
that prose failed; write the gate.

HOW IT PARSES: it REUSES `block_destructive_git.py`'s parser (imported, never copied - one parser, one place to fix):
quotes, escapes, comments at a word start, line continuations; a heredoc opener is reported ONLY in live text (it
becomes the standalone token `<<`), and a PowerShell here-string becomes the token `HERESTRING`. Every `$( ... )` and
every `bash -c` / `cmd /c` / `powershell -Command` body is evaluated too.

WHAT IT BLOCKS, per simple command:
  H1  a LIVE heredoc (`<<TAG`, `<<-TAG`, `<<'TAG'`), whatever the command: its body is text written through the shell
      (a file, a script, a commit message, a JSON body);
  H2  a here-string `<<<` given to an interpreter or a shell (`bash <<< '...'`, `py - <<< "..."`);
  H3  a PowerShell here-string in a command line that writes a file (Set-Content, Add-Content, Out-File, Tee-Object,
      `>`/`>>`) or runs an interpreter;
  H4  `python`/`py` `-c` code that WRITES a file (`.write_text(`, `.write_bytes(`, `open(x, 'w'|'a'|'x')`, `.writelines(`,
      `json.dump(`);
  H5  `echo`/`printf`/`Write-Output` redirected (`>`, `>>`) into a DOC or CODE file (under `PROJECT KNOWLEDGE`, or
      .md .py .ps1 .json .jsonl .yml .yaml), or into ANY file when the text is over 120 characters;
  H6  a quoted argument over 300 characters given to a `python`/`py` SCRIPT (text smuggled in as an argument).

ALLOWS every MENTION (quoted text, comments, a heredoc BODY is never scanned as commands), `git commit -F <file>`,
short echoes into logs (`echo "exit=$?" >> run.txt`), read-only `py -c`, short script arguments, ordinary pipes.

ESCAPE HATCH, ONLY for an operation the USER approved: a live `POKEBOT_ALLOW_SHELL_TEXT=1` assignment in front of the
command itself (read from the COMMAND, so it works - unlike the two older hooks, `#27-hookhatch`), or the variable set
in Claude Code's own environment.

KNOWN LIMITS (deliberate evasion, not habit): text built in a variable first (`$t='...'; $t > x.md`), interpreters
other than python fed by a file, `eval`, base64. The hook is a seat belt against habit, not a sandbox. One false
positive is accepted: a bash arithmetic shift by a NAMED amount (`(( x << n ))`) reads as a heredoc; a numeric amount
(`$(( 1 << 2 ))`) is allowed.

Contract: tool call JSON on stdin; exit 0 always (fails OPEN on any internal error, a missing parser included); print
an ASCII JSON "deny" to block. `--selftest` runs the case table. Gate: `tools/story-dev/selftest_shell_text_hook.py`.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HATCH = "POKEBOT_ALLOW_SHELL_TEXT"
HERE = Path(__file__).resolve().parent
PYTHONS = {"python", "python3", "py", "pythonw", "python3.12"}
INTERPRETERS = PYTHONS | {"node", "ruby", "perl", "php", "bash", "sh", "zsh", "dash", "ksh", "pwsh", "powershell",
                          "cmd"}
PS_WRITERS = {"set-content", "add-content", "out-file", "tee-object", "sc", "ac", "tee"}
ECHOES = {"echo", "printf", "write-output", "write-host"}
OUT_REDIR = {">", ">>", "1>", "1>>", "&>", "&>>"}
WRITE_RE = re.compile(r"\.write_(text|bytes)\s*\(|\bopen\s*\([^,)]*,\s*(mode\s*=\s*)?['\"][wax]|\.writelines\s*\(|"
                      r"\bjson\.dump\s*\(")
DOC_CODE_RE = re.compile(r"(PROJECT KNOWLEDGE|\.(md|py|ps1|json|jsonl|yml|yaml)['\"]?$)", re.I)
ECHO_MAX = 120
ARG_MAX = 300


def _load_parser():
    spec = importlib.util.spec_from_file_location("block_destructive_git", HERE / "block_destructive_git.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _head(tok: str) -> str:
    h = re.split(r"[\\/]", tok)[-1].lower()
    for ext in (".exe", ".cmd", ".bat"):
        h = h.removesuffix(ext)
    return h


def _hatch(cmd: "list[str]") -> bool:
    """A live `POKEBOT_ALLOW_SHELL_TEXT=1` among the assignments in front of the command (`env` included)."""
    for t in cmd:
        if t == f"{HATCH}=1":
            return True
        if not (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t) or t in {"env", "&", "!"}):
            return False
    return False


def _arithmetic_shift(cmd: "list[str]") -> bool:
    """`$(( 1 << 2 ))`: a bit shift, which the shared pre-scan reads as a heredoc opener, and whose `((` the lexer has
    already split off as separators (measured: the command arrives as `['1', '<<', '2']`). A heredoc delimiter made of
    DIGITS only is legal bash but never written in practice, so a numeric "tag" means a shift. (`(( x << n ))` with a
    NAMED shift amount stays blocked: a recorded limit, rare in this project.)"""
    i = cmd.index("<<")
    return i + 1 < len(cmd) and cmd[i + 1].isdigit()


def _redirect_targets(cmd: "list[str]") -> "list[str]":
    return [cmd[j + 1] for j, t in enumerate(cmd[:-1]) if t in OUT_REDIR]


def command_reason(cmd: "list[str]", p, all_heads: "set[str]", herestring_line: bool) -> "str | None":
    """Why this simple command writes text through the shell, or None."""
    if _hatch(cmd):
        return None
    rest = p._strip_prefix(cmd)[0]
    if not rest:
        return None
    head = _head(rest[0])
    if "<<" in cmd and not _arithmetic_shift(cmd):
        return "a heredoc (`<<`): its body is text passed through the shell"
    if "<<<" in cmd and head in INTERPRETERS:
        return "a here-string (`<<<`) fed to an interpreter: code text passed through the shell"
    if herestring_line and "HERESTRING" in rest and (all_heads & (PS_WRITERS | INTERPRETERS) or _redirect_targets(rest)):
        return "a PowerShell here-string written to a file or fed to an interpreter"
    if head in PYTHONS:
        for j, t in enumerate(rest[1:], start=1):
            if t == "-c" and j + 1 < len(rest):
                if WRITE_RE.search(rest[j + 1]):
                    return "`python -c` code that writes a file: code text passed through the shell"
                break
        if any(t.lower().endswith(".py") for t in rest[1:]) and any(len(t) > ARG_MAX for t in rest[1:]):
            return f"a quoted argument over {ARG_MAX} characters given to a Python script: text passed through the shell"
    if head in ECHOES:
        targets = _redirect_targets(rest)
        if targets:
            text = " ".join(t for t in rest[1:] if t not in OUT_REDIR and t not in targets)
            if any(DOC_CODE_RE.search(tg) for tg in targets) or len(text) > ECHO_MAX:
                return "`echo`/`printf` writing documentation or code text into a file"
    return None


def evaluate(text: str, shell: str, p, depth: int = 0) -> "str | None":
    """The reason to block `text`, or None to allow it."""
    if depth > 4 or not text or not text.strip():
        return None
    cmds, _scripts = p.commands(text, shell)
    heads = {_head(p._strip_prefix(c)[0][0]) for c in cmds if p._strip_prefix(c)[0]}
    herestring_line = shell == "ps" and any("HERESTRING" in c for c in cmds)
    for cmd in cmds:
        for tok in cmd:
            for inner in p.substitutions(tok):
                r = evaluate(inner, shell, p, depth + 1)
                if r:
                    return r
        r = command_reason(cmd, p, heads, herestring_line)
        if r:
            return r
        rest = p._strip_prefix(cmd)[0]
        if rest and not _hatch(cmd):
            head = _head(rest[0])
            if head in {"bash", "sh", "zsh", "dash", "ksh", "pwsh", "powershell", "cmd"}:
                inner = p._shell_inner(head, rest)
                if inner:
                    r = evaluate(inner, "ps" if head in {"pwsh", "powershell"} else "bash", p, depth + 1)
                    if r:
                        return r
    return None


# ------------------------------------------------------------------------------------------------ the self-test table
B, A = True, False
LONG = "x" * 310
CASES = [
    # --- the five real incidents (2026-09-30 / 2026-10-01), in their real shapes ------------------------------------
    ("bash", B, "cat > \"C:/Users/x/scratchpad/injob.py\" <<'EOF'\nimport ctypes, os\nprint(1)\nEOF\nPYTHONUTF8=1 py -3.12 x.py"),
    ("bash", B, "cd \"/c/R/PROJECT KNOWLEDGE/ai\" && PYTHONUTF8=1 py -3.12 - <<'EOF'\nimport pathlib\np = pathlib.Path('d.md')\nEOF"),
    ("bash", B, "PYTHONUTF8=1 py -3.12 \"C:/x/t1_append_logs.py\" \"" + "T1-3 aborted the batch in 0.8 min " * 12 + "\""),
    ("bash", B, "py -3.12 -c \"import pathlib; p=pathlib.Path('04-HANDOFF.md'); p.write_text(p.read_text().replace('a','b'))\""),
    ("bash", B, "python -c \"s=open('x.md').read(); open('x.md','w').write(s.replace('\\\\`','`'))\""),
    # --- H1 heredocs, any command ----------------------------------------------------------------------------------------
    ("bash", B, "git commit -F - <<'EOF'\nfeat: x\nEOF"),
    ("bash", B, "tee \"PROJECT KNOWLEDGE/x.md\" <<EOF\nhello\nEOF"),
    ("bash", B, "cat <<-EOF > out.json\n\t{}\n\tEOF"),
    ("bash", B, "python3 <<\\EOF\nprint(1)\nEOF"),
    ("bash", B, "ls && cat <<'EOF'\none line\nEOF"),
    ("bash", B, "bash -c \"cat > a.md <<EOF\nx\nEOF\""),
    ("bash", B, "echo $(cat <<EOF\nx\nEOF\n)"),
    # --- H2 here-strings to interpreters -------------------------------------------------------------------------------
    ("bash", B, "bash <<< 'echo hi'"),
    ("bash", B, "py - <<< \"print(1)\""),
    # --- H3 PowerShell here-strings to writers / interpreters ------------------------------------------------------------
    ("ps", B, "@'\nline one\n'@ | Set-Content \"PROJECT KNOWLEDGE\\x.md\""),
    ("ps", B, "@\"\nimport os\n\"@ | py -3.12 -"),
    ("ps", B, "@'\nx\n'@ > notes.md"),
    # --- H4 python -c that writes -----------------------------------------------------------------------------------------
    ("ps", B, "py -3.12 -c \"import pathlib;pathlib.Path('a.py').write_text('x')\""),
    ("bash", B, "python -c \"import json; json.dump({}, open('a.json', mode='w'))\""),
    ("bash", B, "py -c \"open('log.txt', 'a').writelines(['x'])\""),
    # --- H5 echo / printf into doc or code files, or long text anywhere --------------------------------------------------
    ("bash", B, "echo \"some text\" > \"PROJECT KNOWLEDGE/04-HANDOFF.md\""),
    ("bash", B, "printf '%s\\n' 'x = 1' >> tools/story-dev/x.py"),
    ("bash", B, "echo \"" + "a long sentence of documentation " * 5 + "\" > notes.txt"),
    ("ps", B, "Write-Output 'x' > a.json"),
    # --- H6 a long quoted argument to a Python script --------------------------------------------------------------------
    ("ps", B, f"py -3.12 C:\\x\\append.py \"{LONG}\""),
    # --- ALLOW: mentions, ordinary work ----------------------------------------------------------------------------------
    ("bash", A, "git commit -q -F \"C:/x/commit.txt\""),
    ("bash", A, "grep -n \"<<EOF\" \"PROJECT KNOWLEDGE/08-MISTAKES.md\""),
    ("bash", A, "# never write a heredoc (<<EOF) here\nls -la"),
    ("bash", A, "echo \"exit=$?\" >> \"C:/x/scratchpad/t1_rungates.txt\""),
    ("bash", A, "py -3.12 -c \"import pathlib;s=pathlib.Path('07.md').read_text(encoding='utf-8');print(s.count('x'))\""),
    ("bash", A, "py -3.12 -c \"import ast; ast.parse(open('x4_headless.py',encoding='utf-8').read()); print('ok')\""),
    ("bash", A, "PYTHONUTF8=1 py -3.12 \"C:/x/t1_smoke_grade.py\" \"C:/R/x4-runs/20261001-090649\" smoke"),
    ("bash", A, "cat file.txt | head -5 && sed -n 1,80p a.py"),
    ("bash", A, "py -3.12 -c \"print('<<EOF')\""),
    ("bash", A, "echo \"<<EOF\" > notes.txt"),
    ("bash", A, "git log --oneline -3 && git status --short"),
    ("bash", A, "x=$(( 1 << 2 )); echo $x"),
    ("ps", A, "git commit -m \"short message\""),
    ("ps", A, "$msg = @'\nfeat: x\n'@; Write-Host 'ok'"),
    ("ps", A, "Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = 'py x.py' }"),
    ("ps", A, "Get-Content a.md | Select-String 'Set-Content'"),
    ("ps", A, "& \"C:\\R\\tools\\story-dev\\launch_x4h_detached.ps1\" -Tag s14smoke -Minutes 15"),
    # --- the hatch -------------------------------------------------------------------------------------------------------
    ("bash", A, f"{HATCH}=1 cat > a.md <<'EOF'\nx\nEOF"),
    ("bash", A, f"env {HATCH}=1 py -3.12 -c \"open('a.py','w').write('x')\""),
    ("bash", B, f"echo {HATCH}=1; cat > a.md <<'EOF'\nx\nEOF"),          # a MENTION of the hatch is not the hatch
]


def run_selftest(decide=None) -> int:
    p = _load_parser()
    decide = decide or (lambda text, shell: evaluate(text, shell, p))
    fails = 0
    for shell, want, cmd in CASES:
        got = bool(decide(cmd, shell))
        if got != want:
            fails += 1
            print(f"  FAIL  want={'BLOCK' if want else 'ALLOW'} got={'BLOCK' if got else 'ALLOW'}  [{shell}] {cmd!r}")
    if fails:
        print(f"  {fails} of {len(CASES)} cases FAILED")
        return 1
    print(f"  OK  block_shell_text.py: {len(CASES)}/{len(CASES)} cases (the five incidents, H1-H6, mentions, ordinary "
          f"work, the hatch)")
    return 0


# ------------------------------------------------------------------------------------------------ hook entry point
REASON = """BLOCKED: {why}.

USER RULING 29 (2026-10-01): documentation and code text never pass through a shell-quoted string. Shell quoting
silently rewrites backslashes, `$` and backticks; this rule broke five times in two sessions before it became a hook.

Do this instead:
  * a file's content: use the Write or Edit tool;
  * a script: Write it to a file (the scratchpad), then run that file;
  * a commit message: Write it to a file, then 'git commit -F <file>';
  * text for a script: Write it to a file and pass the PATH, never the text.

If the USER approved this exact operation, put POKEBOT_ALLOW_SHELL_TEXT=1 in front of the command itself."""


def main() -> int:
    if "--selftest" in sys.argv:
        return run_selftest()
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        cmd = str((payload.get("tool_input") or {}).get("command") or "")
        if not cmd or os.environ.get(HATCH) == "1":
            return 0
        shell = "ps" if str(payload.get("tool_name", "")).lower() == "powershell" else "bash"
        why = evaluate(cmd, shell, _load_parser())
        if why:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                     "permissionDecisionReason": REASON.format(why=why)}}))
    except Exception:  # noqa: BLE001 - fail OPEN: a hook that errors must never block the session
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
