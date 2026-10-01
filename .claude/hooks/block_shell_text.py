r"""PreToolUse(Bash|PowerShell) hook - REFUSE documentation or code text written THROUGH THE SHELL.

WHY (USER RULING 29, 2026-10-01; `08-MISTAKES.md` 2026-09-30 and 2026-10-01): the written rule "documentation and code
text never pass through a shell-quoted string; use Write/Edit, or a script file written with Write and then run" was
broken FIVE times in two sessions. Every slip happened to be harmless, but shell quoting silently rewrites backslashes,
`$` and backticks, and the next one lands in a doc or a gate. CLAUDE.md rule 6: a rule broken repeatedly is evidence
that prose failed; write the gate.

HOW IT PARSES: it REUSES `block_destructive_git.py`'s parser (imported, never copied - one parser, one place to fix):
quotes, escapes, comments at a word start, line continuations; a heredoc opener is reported ONLY in live text (it
becomes the standalone token `<<`), and a PowerShell here-string becomes the token `HERESTRING`. Every `$( ... )`,
every `bash -c` / `cmd /c` / `powershell -Command` body and every `find -exec` command is evaluated too. The LINE rules
(H7-H11) must know whether a word was QUOTED (a PowerShell literal, a double-quoted commit message), which the posix
lexer forgets, so `_words` re-splits the parser's OWN pre-scanned text keeping that: the pre-scan stays in one place.
(It also keeps `awk '{...}' x.md` whole: the shared lexer opens a new command at a word starting with `{`.)

WHAT IT BLOCKS (the reason names the rule), per simple command:
  H1  a LIVE heredoc (`<<TAG`, `<<-TAG`, `<<'TAG'`), whatever the command: its body is text written through the shell.
      BASH only (PowerShell has no heredocs), and only an UNQUOTED `<<`: a quoted '<<' argument is a mention;
  H2  a here-string `<<<` given as the PROGRAM of an interpreter or shell that has no script (`bash <<< '...'`,
      `py - <<< "..."`); `py x.py <<< "y"` is stdin DATA for a script and passes;
  H3  a PowerShell here-string in a command line that writes a file (a writer cmdlet, or a `>`/`>>` ANYWHERE on the
      line, ignoring $null, /dev/null, nul and an fd-numbered `2>`) or runs an interpreter;
  H4  `python -c` code that WRITES a file (`.write_text(`, `.write_bytes(`, `.writelines(`, `json.dump(`, `open(...)`
      with a write mode ANYWHERE in the call (w a x r+, `Path(...).open('w')` too), `os.open` with write flags,
      `inplace=True`; `-c` bundles such as `-Bc` included), or whose OUTPUT is redirected into a doc or code file;
  H5  `echo`/`printf`/`Write-Output` redirected into a DOC or CODE file (DOC_CODE_RE: under `PROJECT KNOWLEDGE`, or
      .md .py .pyw .ps1 .psm1 .json .jsonl .yml .yaml .toml .ini .cfg .sh .bash .bat .cmd .html .js .ts .css - NOT .txt),
      or into ANY file when the text is over 120 characters; text with no visible content (`printf '\n'`) passes;
  H6  PROSE as arguments to a SCRIPT: arguments with 8+ spaces totalling over 150 characters, given to a python .py file
      or -m module, a bash/sh .sh file, a .ps1, or powershell -File (never to `python -c` code: its .py arguments are
      data, and its code is H4's business);
per command LINE (pipelines, with quoting known):
  H7  an in-place regex edit of a DOC or CODE file: sed/gsed -i, perl -i (bundles), awk -i inplace, inside find -exec
      too (`{}` stands for the -name pattern) - the FILE operand decides, never the edit script; and a PowerShell line
      with -replace/.Replace( and a writer whose target is doc or code;
  H8  a PowerShell writer fed a LITERAL (Set-Content/sc, Add-Content/ac, Out-File, Tee-Object/tee, New-Item -Value, a
      bare "string" `>`/`>>`, [IO.File]::WriteAll*/AppendAll*) when the target is doc or code or the literal is over
      120 characters; a literal is a quoted value, a here-string (or a variable assigned one on this line), @(...),
      or a pipeline that starts with a quoted string or echo/Write-Output;
  H9  a git commit/tag/notes/merge/revert MESSAGE through the shell: an -m/--message value with a newline, over 120
      characters, a here-string, a live substitution in bash (a backtick included; only exactly `$(cat FILE)` passes),
      or a double-quoted PowerShell value with `$` or a backtick; or a literal piped into `git commit -F -`;
  H10 a pipeline that starts with echo/printf/Write-Output or a bare literal, into tee/Tee-Object, cat/type `>`, or
      `dd of=` (doc/code target or over 120 characters), or into python reading its PROGRAM from stdin; and `<<<` given
      to cat/tee that writes a doc/code file or over 120 characters;
  H11 echo/printf with a live, unescaped backtick written to any file (bash); a file written by echo/printf/a literal
      that the SAME command line then gives to `git -F`/`--file`.

ALLOWS every MENTION (quoted text, comments, a heredoc BODY is never scanned as commands), `git commit -F <file>`,
`git commit -m "short message"`, short echoes into logs (`echo "exit=$?" >> run.txt`), read-only `py -c`, short script
arguments, ordinary pipes, writers fed by a command or a file (`Get-Content a | Set-Content b`).

ESCAPE HATCH, ONLY for an operation the USER approved: a live `POKEBOT_ALLOW_SHELL_TEXT=1` assignment in front of the
command itself (read from the COMMAND, so it works - unlike the two older hooks, `#27-hookhatch`; for a line rule, in
front of any command of that pipeline), or the variable set in Claude Code's own environment.

KNOWN LIMITS (deliberate evasion or vanishingly rare here; the hook is a seat belt against habit, not a sandbox):
  * text built in a variable first (`$c = "<sentence>"; Set-Content x.md $c`), `eval`, `exec('...')` of a string,
    base64;
  * interpreters other than python (`node -e "...writeFileSync..."`, `perl -e 'open(F,">a.md")...'`), and gh
    (`gh pr create --body "<text>"`), which this push-to-main workflow does not use;
  * unusual redirects: a redirect before the command (`>a.md echo x`), `>|` (lexed as a pipe), ANSI-C `$'...'` quoting
    (it can hide a later heredoc from the pre-scan), a here-string inside a nested `powershell -Command`;
  * short multi-line printf/echo into a .txt (`printf 'feat: x\n\nbody\n' > msg.txt` with no git on the same line),
    or several short `echo >> m.txt` lines: an aggregate rule would block ordinary multi-line log writes;
  * prose PRINTED by read-only `python -c` code into `| tee` or `>` a non-doc file (BL-1);
  * a bash arithmetic shift by a NAMED amount (`(( x << n ))`) reads as a heredoc (a false positive); a numeric amount
    (`$(( 1 << 2 ))`) is allowed.
ACCEPTED COST: H4 also blocks extractor, downloader and EOL-fixer `-c` one-liners that write a file (64 of 18,484
replayed commands): the -c program is itself code in a shell string; Write it as a script.

Contract: tool call JSON on stdin; exit 0 always (fails OPEN on any internal error, a missing parser included); print
an ASCII JSON "deny" to block. `--selftest` runs the case table. Gate: `tools/story-dev/selftest_shell_text_hook.py`.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import NamedTuple

HATCH = "POKEBOT_ALLOW_SHELL_TEXT"
HERE = Path(__file__).resolve().parent
PYTHONS = {"python", "python3", "py", "pythonw", "python3.12"}
SH_SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
SHELL_HEADS = SH_SHELLS | {"pwsh", "powershell", "cmd"}
INTERPRETERS = PYTHONS | SHELL_HEADS | {"node", "ruby", "perl", "php"}
H3_WRITERS = {"set-content", "add-content", "out-file", "tee-object", "sc", "ac", "tee"}
PS_WRITERS = H3_WRITERS | {"new-item", "ni"}
ECHOES = {"echo", "printf", "write-output", "write-host", "write"}
OUT_REDIR = {">", ">>", "1>", "1>>", "&>", "&>>"}
NULLS = {"$null", "/dev/null", "nul", "nul:"}
GIT_MSG_SUBS = {"commit", "tag", "notes", "merge", "revert"}
WRITE_RE = re.compile(
    r"\.write_(?:text|bytes)\s*\(|\.writelines\s*\(|\bjson\.dump\s*\("
    r"|\bopen\s*\((?:[^()]|\([^()]*\))*?['\"](?:[wax]|r[bt]?\+)[bt+]*['\"]"
    r"|\bos\.open\s*\([^)]*O_(?:WRONLY|RDWR|APPEND|CREAT)|\binplace\s*=\s*True")
DOC_CODE_RE = re.compile(r"(PROJECT KNOWLEDGE|\.(md|py|pyw|ps1|psm1|json|jsonl|yml|yaml|toml|ini|cfg|sh|bash|bat|cmd|"
                         r"html|js|ts|css)['\"]?$)", re.I)
C_OPT = re.compile(r"-[A-Za-z]*c")                       # python -c, bundles included (`-Bc`)
CAT_FILE = re.compile(r"\$\(cat\s+[^();&|<>`\n]+\)")     # the one substitution a -m may hold: a file's content
IOFILE_RE = re.compile(r"(?i)\[(?:system\.)?io\.file\]::(?:write|append)all(?:text|lines|bytes)\s*\(\s*"
                       r"(?:(['\"])(?P<tgt>.*?)\1|\$[\w:.]+)\s*,\s*"
                       r"(?:(['\"])(?P<lit>.*?)\3|(?P<var>\$[\w:.]+)|(?P<arr>@\())")
REPLACE_RE = re.compile(r"(?i)(?:^|[\s)])-[ci]?replace\b|\.replace\s*\(")
ECHO_MAX = 120          # characters of literal text a short log line may carry
PROSE_SPACES = 8        # an argument with this many spaces is prose
PROSE_MAX = 150         # prose arguments to one script may total this much
BIG = 10 ** 6           # a here-string's body is blanked by the pre-scan: its length is unknown, so it counts as long


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


def _is_doc(t: str) -> bool:
    return bool(DOC_CODE_RE.search(t))


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


def _heredoc_live(clean: str, shell: str) -> bool:
    """H1's precondition (BH-08): an UNQUOTED `<<` (not `<<<`) in the pre-scanned text. PowerShell has no heredocs. In
    bash the pre-scan rewrote every live opener to a bare ` << 'TAG' `, while a quoted '<<' argument (a grep pattern)
    stays inside its quotes - where the posix lexer would otherwise turn it into the very same token."""
    if shell == "ps":
        return False
    st, i, n = "N", 0, len(clean)
    while i < n:
        c = clean[i]
        if st == "S":
            st = "N" if c == "'" else "S"
        elif c == "\\":
            i += 1
        elif st == "D":
            st = "N" if c == '"' else "D"
        elif c == "'":
            st = "S"
        elif c == '"':
            st = "D"
        elif clean.startswith("<<", i) and not clean.startswith("<<<", i) and (i == 0 or clean[i - 1] != "<"):
            return True
        i += 1
    return False


def _out_targets(toks: "list[str]") -> "list[str]":
    """Files a command's `>`/`>>` redirections write: not $null, /dev/null or nul, and not an fd-numbered `2>`."""
    out = []
    for j, t in enumerate(toks[:-1]):
        if t in OUT_REDIR and toks[j + 1].lower() not in NULLS and not (j > 0 and re.fullmatch(r"[2-9]", toks[j - 1])):
            out.append(toks[j + 1])
    return out


def _c_index(rest: "list[str]") -> "int | None":
    """Where python's `-c` is, when python RUNS -c code: the `-c` (or a bundle ending in c) comes before any script,
    module or `-`. In `py -c CODE x.py` the .py is sys.argv[1], DATA (FP-1)."""
    i = 1
    while i < len(rest):
        t = rest[i]
        if C_OPT.fullmatch(t):
            return i
        if t in {"-X", "-W"}:
            i += 2
            continue
        if t == "-" or not t.startswith("-") or re.match(r"-[A-Za-z]*m", t):
            return None
        i += 1
    return None


def _is_script(head: str, rest: "list[str]") -> bool:
    """A SCRIPT run with arguments (BH-05): python with a .py/.pyw file or -m module first, bash/sh with a .sh/.bash
    file first, a .ps1, or powershell -File. Never python running -c code (FP-1)."""
    if head.endswith(".ps1"):
        return True
    if head in {"powershell", "pwsh"}:
        return any(t.lower() in {"-file", "-f"} for t in rest[1:])
    if head in PYTHONS:
        i = 1
        while i < len(rest):
            t = rest[i]
            if C_OPT.fullmatch(t) or t == "-":
                return False
            if re.match(r"-[A-Za-z]*m", t):
                return True
            if t in {"-X", "-W"}:
                i += 2
                continue
            if not t.startswith("-"):
                return t.lower().endswith((".py", ".pyw"))
            i += 1
        return False
    if head in SH_SHELLS:
        for t in rest[1:]:
            if t.startswith("-") and not t.startswith("--") and "c" in t[1:]:
                return False
            if not t.startswith("-"):
                return t.lower().endswith((".sh", ".bash"))
    return False


def _prose_total(args: "list[str]") -> int:
    """Characters of PROSE among the arguments (BH-05, FP-2): an argument with 8+ spaces. An unquoted shell word holds
    no space at all, so a long comma list of data never counts."""
    return sum(len(t) for t in args if t.count(" ") >= PROSE_SPACES)


def _visible(text: str) -> bool:
    """Whether echo/printf text carries anything visible (FP-3): `printf '\\n'` (a blank separator line) does not."""
    return bool(re.sub(r"(?:^|(?<=\s))-[neE]+(?=\s|$)|\\[nrt0]|%[sbc]|\s", "", text))


def _program_from_stdin(head: str, rest: "list[str]") -> bool:
    """The interpreter takes its PROGRAM from stdin (BH-12): no script, no -c/-m/-e/-Command, or an explicit `-`."""
    i = 1
    while i < len(rest):
        t = rest[i]
        if t == "<<<" or re.fullmatch(r"\d*(?:>>?|<|>&|<&|&>>?)", t):            # a redirection and its operand
            i += 2
            continue
        if t.isdigit() and i + 1 < len(rest) and re.fullmatch(r"[<>&]+", rest[i + 1]):  # its fd number
            i += 1
            continue
        if t == "-":
            return True
        if head in PYTHONS:
            if re.fullmatch(r"-[A-Za-z]*[cm]", t):
                return False
            if t in {"-X", "-W"}:
                i += 2
                continue
        elif head in SH_SHELLS:
            if t.startswith("-") and not t.startswith("--") and "c" in t[1:]:
                return False
            if t.startswith("-") and not t.startswith("--") and "s" in t[1:]:
                return True
        elif head in {"pwsh", "powershell"}:
            tl = t.lower()
            if tl.startswith("-comm") or tl in {"-c", "-file", "-f", "-encodedcommand", "-ec", "-e"}:
                return False
        elif head == "cmd":
            if t.lower() in {"/c", "/k", "//c", "//k"}:
                return False
        elif t in {"-e", "-E", "-r"}:
            return False
        if not t.startswith(("-", "/")) or (head not in {"cmd"} and not t.startswith("-")):
            return False                                                      # a script file
        i += 1
    return True


def _edit_operands(head: str, args: "list[str]") -> "tuple[bool, list[str]]":
    """(in place?, FILE operands) of a sed / perl / awk command. The edit SCRIPT is never a file operand: sed's first
    positional unless -e/-f gave it, perl's -e code, awk's program unless -f gave it (a script that MENTIONS
    `PROJECT KNOWLEDGE` must not make a .txt target look like a doc). In a short bundle, sed/perl `-i` takes the REST
    as a backup suffix (`perl -pie` is -p -i with suffix "e"); `e`/`f` (sed), `e`/`E` (perl) take the next word."""
    inplace, script_given, pos, k = False, False, [], 0
    takes = {"sed": "efl", "gsed": "efl", "perl": "eE", "awk": "fvFi", "gawk": "fvFi"}[head]
    while k < len(args):
        a = args[k]
        if a == "--":
            pos.extend(args[k + 1:])
            break
        if a.startswith("--"):
            name, _, val = a[2:].partition("=")
            if name in {"in-place"}:
                inplace = True
            elif name in {"expression", "file"}:
                script_given = True
                k += 0 if val else 1
            elif name == "include" and (val or (args[k + 1] if k + 1 < len(args) else "")) == "inplace":
                inplace = True
                k += 0 if val else 1
            k += 1
            continue
        if a.startswith("-") and len(a) > 1:
            for j, ch in enumerate(a[1:], start=1):
                if ch == "i" and head in {"sed", "gsed", "perl"}:
                    inplace = True
                    break                                   # the rest of the bundle is a backup suffix
                if ch in takes:
                    val = a[j + 1:] or (args[k + 1] if k + 1 < len(args) else "")
                    if not a[j + 1:]:
                        k += 1
                    if head in {"awk", "gawk"} and ch == "i" and val == "inplace":
                        inplace = True
                    script_given = script_given or ch in "efE"
                    break
                if head == "perl" and ch in "MmIxCdDlF0":
                    break                                   # a glued value
            k += 1
            continue
        pos.append(a)
        k += 1
    files = pos if script_given else pos[1:]
    return inplace, [f for f in files if not re.fullmatch(r"[A-Za-z_]\w*=.*", f)]   # awk `var=value` operands


def _inplace_reason(head: str, rest: "list[str]") -> "str | None":
    """H7 (BH-03): sed/gsed -i, perl -i, awk -i inplace whose FILE operand is DOC or CODE. A LINE rule: the shared
    lexer starts a new command at a word beginning with `{` (a PowerShell script block), which cuts `awk '{...}' x.md`
    before its file."""
    if head not in {"sed", "gsed", "perl", "awk", "gawk"}:
        return None
    inplace, files = _edit_operands(head, rest[1:])
    if inplace and any(_is_doc(f) for f in files):
        return (f"an in-place `{head}` edit of a doc or code file: its pattern and replacement are text passed through "
                f"the shell (H7)")
    return None


def command_reason(cmd: "list[str]", p, all_heads: "set[str]", herestring_line: bool, live_ltlt: bool = True,
                   line_targets: "list[str] | None" = None) -> "str | None":
    """Why this simple command writes text through the shell, or None."""
    if _hatch(cmd):
        return None
    rest = p._strip_prefix(cmd)[0]
    if not rest:
        return None
    head = _head(rest[0])
    if live_ltlt and "<<" in cmd and not _arithmetic_shift(cmd):
        return "a heredoc (`<<`): its body is text passed through the shell (H1)"
    if "<<<" in cmd and head in INTERPRETERS and _program_from_stdin(head, rest):
        return "a here-string (`<<<`) fed to an interpreter as its program: code text passed through the shell (H2)"
    targets = _out_targets(rest)
    if herestring_line and "HERESTRING" in rest and (all_heads & (H3_WRITERS | INTERPRETERS) or targets
                                                     or line_targets):
        return "a PowerShell here-string written to a file or fed to an interpreter (H3)"
    if head in PYTHONS:
        c = _c_index(rest)
        if c is not None and c + 1 < len(rest):
            if WRITE_RE.search(rest[c + 1]):
                return "`python -c` code that writes a file: code text passed through the shell (H4)"
            if any(_is_doc(t) for t in targets):
                return "`python -c` output redirected into a doc or code file: code text passed through the shell (H4)"
    if _is_script(head, rest) and _prose_total(rest[1:]) > PROSE_MAX:
        return "prose passed as arguments to a script: text passed through the shell (H6)"
    if head in ECHOES and targets:
        text = " ".join(t for t in rest[1:] if t not in OUT_REDIR and t not in targets)
        if _visible(text) and (any(_is_doc(t) for t in targets) or len(text) > ECHO_MAX):
            return "`echo`/`printf` writing documentation or code text into a file (H5)"
    return None


def _find_exec_reason(rest: "list[str]", p, depth: int) -> "str | None":
    """`find ... -exec CMD {} +`: CMD is evaluated, with `{}` standing for the -name pattern (BH-03)."""
    name = next((rest[k + 1] for k, t in enumerate(rest[:-1]) if t in {"-name", "-iname", "-path", "-ipath"}), None)
    for j, t in enumerate(rest):
        if t in {"-exec", "-execdir", "-ok", "-okdir"}:
            inner = []
            for a in rest[j + 1:]:
                if a in {";", "+", "\\;"}:
                    break
                inner.append(name if a == "{}" and name else a)
            r = evaluate(shlex.join(inner), "bash", p, depth + 1) if inner else None
            if r:
                return r
    return None


# ------------------------------------------------------------------------------------------------ the LINE rules
class _W(NamedTuple):
    v: str          # the word's value, quotes removed
    q: str          # the quote the word STARTS with ("'" or '"'), or "" when it starts unquoted
    op: bool        # punctuation: a separator or a redirection operator
    glued: bool     # no whitespace between this word and the one before it


def _words(clean: str, shell: str, punct: str) -> "list[_W]":
    """Split the parser's pre-scanned text as its posix lexer does (same whitespace, same punctuation), but keep for
    each word whether it was QUOTED. PowerShell has no backslash escapes (the pre-scan already resolved backticks)."""
    out: "list[_W]" = []
    i, n, esc, glued = 0, len(clean), shell != "ps", False
    while i < n:
        c = clean[i]
        if c in " \t\r":
            i += 1
            glued = False
            continue
        start = i
        if c in punct:
            while i < n and clean[i] in punct:
                i += 1
            out.append(_W(clean[start:i], "", True, glued))
            glued = True
            continue
        val = []
        while i < n and clean[i] not in " \t\r" and clean[i] not in punct:
            c = clean[i]
            if c == "'":
                k = clean.find("'", i + 1)
                k = n if k < 0 else k
                val.append(clean[i + 1:k])
                i = k + 1
            elif c == '"':
                j = i + 1
                while j < n and clean[j] != '"':
                    if esc and clean[j] == "\\" and j + 1 < n:
                        val.append(clean[j + 1] if clean[j + 1] in '"\\$`' else clean[j:j + 2])
                        j += 2
                        continue
                    val.append(clean[j])
                    j += 1
                i = j + 1
            elif esc and c == "\\" and i + 1 < n:
                val.append(clean[i + 1])
                i += 2
            else:
                val.append(c)
                i += 1
        out.append(_W("".join(val), clean[start] if clean[start] in "'\"" else "", False, glued))
        glued = True
    return out


def _pipelines(words: "list[_W]", p) -> "list[list[list[_W]]]":
    """Pipelines of stages (word lists); `{` / `}` and every separator but `|` end a pipeline."""
    out, pipe, cur = [], [], []
    for w in words:
        if w.op and w.v in {"|", "|&"}:
            pipe.append(cur)
            cur = []
        elif (w.op and p._is_sep(w.v)) or (not w.op and not w.q and w.v in {"{", "}"}):
            pipe.append(cur)
            if any(pipe):
                out.append([s for s in pipe if s])
            pipe, cur = [], []
        else:
            cur.append(w)
    pipe.append(cur)
    if any(pipe):
        out.append([s for s in pipe if s])
    return out


def _strip(stage: "list[_W]", p) -> "tuple[list[_W], list[str]]":
    """The stage with assignments / wrappers / keywords in front removed: (its words, their values)."""
    rest = p._strip_prefix([w.v for w in stage])[0]
    return (stage[len(stage) - len(rest):], rest) if rest else ([], [])


def _operand_positions(ws: "list[_W]") -> "set[int]":
    """Indexes of redirection operators, their operands and a glued fd number (`2>&1`, `2> err.txt`)."""
    skip = set()
    for k, w in enumerate(ws):
        if w.op:
            skip.update({k, k + 1})
            if k > 0 and w.glued and ws[k - 1].v.isdigit():
                skip.add(k - 1)
    return skip


def _targets(ws: "list[_W]") -> "list[str]":
    """Files a stage's `>`/`>>` write: not $null, /dev/null or nul, and not an fd-numbered `2>` (BH-10)."""
    out = []
    for j, w in enumerate(ws[:-1]):
        nxt = ws[j + 1]
        if w.op and w.v in {">", ">>", "&>", "&>>"} and not nxt.op and nxt.v.lower() not in NULLS:
            if j > 0 and w.glued and re.fullmatch(r"[2-9]", ws[j - 1].v):
                continue
            out.append(nxt.v)
    return out


def _literal_head(ws: "list[_W]", vals: "list[str]", shell: str) -> "tuple[str | None, str, int]":
    """('echo' | 'literal', text, length) when a pipeline's first stage produces LITERAL text, else (None, '', 0)."""
    skip = _operand_positions(ws)
    if _head(vals[0]) in ECHOES:
        text = " ".join(w.v for k, w in enumerate(ws) if k > 0 and k not in skip)
        return "echo", text, len(text)
    if shell == "ps" and ws[0].q:
        if ws[0].q == "'" and ws[0].v == "HERESTRING":
            return "literal", "", BIG
        text = " ".join(w.v for k, w in enumerate(ws) if k not in skip and w.q)
        return "literal", text, len(text)
    return None, "", 0


def _here_vars(words: "list[_W]") -> "set[str]":
    """PowerShell variables assigned a here-string on this line (`$t = @'...'@`)."""
    out = set()
    for k, w in enumerate(words):
        if re.fullmatch(r"\$[\w:.]+=?", w.v) and not w.q:
            nxt = words[k + 1:k + 3] if not w.v.endswith("=") else [_W("=", "", False, True)] + words[k + 1:k + 2]
            if len(nxt) == 2 and nxt[0].v == "=" and nxt[1].q == "'" and nxt[1].v == "HERESTRING":
                out.add(w.v.rstrip("=").lower())
    return out


def _live_backtick(text: str) -> bool:
    """A live, unescaped backtick in raw bash text (outside single quotes and comments): a command substitution."""
    st, i, n = "N", 0, len(text)
    while i < n:
        c = text[i]
        if st == "S":
            st = "N" if c == "'" else "S"
        elif c == "\\":
            i += 1
        elif c == "`":
            return True
        elif st == "D":
            st = "N" if c == '"' else "D"
        elif c == "'":
            st = "S"
        elif c == '"':
            st = "D"
        elif c == "#" and (i == 0 or text[i - 1] in " \t\n;&|()"):
            e = text.find("\n", i)
            i = n if e < 0 else e
            continue
        i += 1
    return False


def _ps_dq_backtick(text: str) -> bool:
    """A backtick inside a double-quoted PowerShell string (an escape: `b is a BACKSPACE, `" swallows the quote)."""
    st, i, n = "N", 0, len(text)
    while i < n:
        c = text[i]
        if st == "S":
            if c == "'" and text.startswith("''", i):
                i += 2
                continue
            st = "N" if c == "'" else "S"
        elif st == "D":
            if c == "`":
                return True
            if c == '"' and text.startswith('""', i):
                i += 2
                continue
            st = "N" if c == '"' else "D"
        elif c == "`":
            i += 2
            continue
        elif c == "'":
            st = "S"
        elif c == '"':
            st = "D"
        elif c == "#" and (i == 0 or text[i - 1] in " \t\r\n;|"):
            while i < n and text[i] not in "\r\n":
                i += 1
            continue
        i += 1
    return False


_PS_PATH = ("-path", "-literalpath", "-filepath", "-pspath")
_PS_VALUE = ("-value", "-inputobject")
_PS_VALUED = ("-encoding", "-itemtype", "-type", "-width", "-variable", "-delimiter", "-stream", "-credential",
              "-filter", "-include", "-exclude")


def _ps_param(t: str, names: "tuple[str, ...]") -> bool:
    """PowerShell accepts an unambiguous prefix of a parameter name; 4+ characters (`-val`) is unambiguous here."""
    return any(t == n or (len(t) >= 4 and n.startswith(t)) for n in names)


def _ps_writer(ws: "list[_W]", h: str) -> "tuple[list[str], _W | None]":
    """A PowerShell writer cmdlet's (target files, value word) from its own arguments."""
    tgts, val, pos, k = [], None, [], 1
    while k < len(ws):
        w, t = ws[k], ws[k].v.lower()
        nxt = ws[k + 1] if k + 1 < len(ws) and not ws[k + 1].op else None
        if w.op:
            k += 2 if nxt is not None else 1
            continue
        if not w.q and t.startswith("-") and len(t) > 1:
            if nxt is not None and (_ps_param(t, _PS_PATH) or t in {"-lp", "-fp"}
                                    or (h in {"new-item", "ni"} and _ps_param(t, ("-name",)))):
                tgts.append(nxt.v)
                k += 2
            elif nxt is not None and _ps_param(t, _PS_VALUE):
                val = nxt
                k += 2
            elif nxt is not None and _ps_param(t, _PS_VALUED):
                k += 2
            else:
                k += 1
            continue
        pos.append(w)
        k += 1
    if not tgts and pos:
        tgts.append(pos.pop(0).v)
    if val is None and pos and h in {"set-content", "sc", "add-content", "ac"}:
        val = pos[0]
    return [t for t in tgts if t.lower() not in NULLS], val


def _iofile_reason(clean: str, here_vars: "set[str]") -> "str | None":
    """H8: [IO.File]::WriteAll*/AppendAll* fed a literal (the shared lexer splits at `(`, hence a line regex)."""
    for m in IOFILE_RE.finditer(clean):
        here = bool(m["var"]) and m["var"].lower() in here_vars
        if m["lit"] is None and not here and not m["arr"]:
            continue
        n = BIG if here else len(m["lit"] or "")
        if (m["tgt"] and _is_doc(m["tgt"])) or n > ECHO_MAX:
            return "[IO.File]::WriteAll*/AppendAll* fed a literal string: text passed through the shell (H8)"
    return None


def _git_message_reason(ws, vals, h, shell, piped, here_vars, dq_bt, written, p) -> "str | None":
    """H9 (BH-01, BH-04) and H11's git half (BH-09): a commit/tag/notes/merge/revert message through the shell."""
    if h != "git":
        return None
    i = 1
    while i < len(vals) and vals[i].startswith("-"):
        i += 2 if vals[i] in p.GIT_GLOBAL_WITH_VALUE else 1
    if i >= len(vals) or vals[i].lower() not in GIT_MSG_SUBS:
        return None
    k = i + 1
    while k < len(ws):
        w, a = ws[k], ws[k].v
        if w.op:
            k += 2
            continue
        if w.q:
            k += 1
            continue
        val = None
        if a in {"-m", "--message"} or re.fullmatch(r"-[A-Za-z]*m", a):
            val = ws[k + 1] if k + 1 < len(ws) and not ws[k + 1].op else None
            k += 2
        elif a.startswith("--message="):
            val = _W(a.split("=", 1)[1], "", False, True)
            k += 1
        elif re.fullmatch(r"-[A-Za-z]*m.+", a) and not a.startswith("--"):
            val = _W(a[a.index("m") + 1:], "", False, True)
            k += 1
        elif a in {"-F", "--file"} or a.startswith("--file=") or (a.startswith("-F") and len(a) > 2):
            if a.startswith("--file="):
                f, k = a.split("=", 1)[1], k + 1
            elif len(a) > 2 and a.startswith("-F"):
                f, k = a[2:], k + 1
            else:
                f, k = (ws[k + 1].v if k + 1 < len(ws) else ""), k + 2
            if f == "-" and (piped or "<<<" in vals):
                return "a commit message piped or fed from a literal into `git -F -` (H9)"
            if f != "-" and f in written:
                return "a commit-message file built by echo/printf/a literal on the same command line (H11)"
            continue
        else:
            k += 1
            continue
        if val is None:
            continue
        v = val.v
        if (val.q == "'" and v == "HERESTRING") or v.lower() in here_vars:
            return "a commit message from a here-string: text passed through the shell (H9)"
        if "\n" in v or len(v) > ECHO_MAX:
            return f"a multi-line or over-{ECHO_MAX}-character commit message in -m: text passed through the shell (H9)"
        if shell == "bash" and val.q != "'" and "$(" in v and not CAT_FILE.fullmatch(v.strip()):
            return "a live command substitution (a backtick?) in a commit message: the shell rewrites it (H9)"
        if shell == "ps" and val.q == '"' and ("$" in v or dq_bt):
            return "a double-quoted PowerShell commit message with `$` or a backtick: the shell rewrites it (H9)"
    return None


def _pipe_into_reason(ws, vals, h, tg, kind, text, n, live_bt) -> "tuple[str | None, list[str]]":
    """H10 (BH-06): literal text piped into a writer or an interpreter. Returns (reason, files written)."""
    def doc_or_long(files):
        return any(_is_doc(f) for f in files) or n > ECHO_MAX
    if h in {"tee", "tee-object"}:
        skip = _operand_positions(ws)
        files = [w.v for k, w in enumerate(ws) if k > 0 and k not in skip and (w.q or not w.v.startswith("-"))
                 and w.v.lower() not in NULLS] + tg
        if files and doc_or_long(files):
            return "literal text piped into `tee` writing a doc or code file, or over 120 characters (H10)", files
        if files and live_bt and kind == "echo" and "$(" in text:
            return "an echo/printf with a live backtick written to a file through `tee` (H11)", files
        return None, files
    if h in {"cat", "type"} and tg:
        if doc_or_long(tg):
            return "literal text piped into `cat >` a doc or code file, or over 120 characters (H10)", tg
        return None, tg
    if h == "dd":
        of = [w.v[3:] for w in ws if w.v.startswith("of=")]
        if of and doc_or_long(of):
            return "literal text piped into `dd of=` a doc or code file (H10)", of
        return None, of
    if h in PYTHONS and _program_from_stdin(h, vals):
        return "code piped from a literal into python's stdin: code text passed through the shell (H10)", []
    return None, []


def line_reason(text: str, shell: str, p, clean: "str | None" = None) -> "str | None":
    """The LINE rules (H7's PowerShell half, H8-H11): pipelines with quoting known."""
    if clean is None:
        clean = (p._prescan_ps if shell == "ps" else p._prescan_bash)(text)[0]
    words = _words(clean, shell, p.PUNCT)
    pipes = []
    for pipe in _pipelines(words, p):
        if any(_hatch([w.v for w in st]) for st in pipe):
            continue
        stages = [s for s in (_strip(st, p) for st in pipe) if s[1]]
        if stages:
            pipes.append(stages)
    here_vars = _here_vars(words) if shell == "ps" else set()
    if shell == "ps":
        r = _iofile_reason(clean, here_vars)
        if r:
            return r
        if REPLACE_RE.search(clean):
            for stages in pipes:
                for ws, vals in stages:
                    h = _head(vals[0])
                    tg = _targets(ws) + (_ps_writer(ws, h)[0] if h in PS_WRITERS else [])
                    if any(_is_doc(t) for t in tg):
                        return "a PowerShell `-replace`/`.Replace(` written back into a doc or code file (H7)"
    live_bt = shell == "bash" and _live_backtick(text)
    dq_bt = shell == "ps" and _ps_dq_backtick(text)
    written: "set[str]" = set()
    for stages in pipes:
        kind, lit_text, lit_len = _literal_head(*stages[0], shell)
        for j, (ws, vals) in enumerate(stages):
            h = _head(vals[0])
            tg = _targets(ws)
            piped = j > 0 and kind is not None
            r = _git_message_reason(ws, vals, h, shell, piped, here_vars, dq_bt, written, p) or _inplace_reason(h, vals)
            if r:
                return r
            if shell == "ps" and h in PS_WRITERS:
                files, val = _ps_writer(ws, h)
                if val is not None:
                    here = (val.q == "'" and val.v == "HERESTRING") or val.v.lower() in here_vars
                    lit, n = bool(val.q) or here or (val.v == "@" and not val.q), (BIG if here else len(val.v))
                else:
                    lit, n = piped, lit_len
                if lit and files:
                    if any(_is_doc(f) for f in files) or n > ECHO_MAX:
                        return "a PowerShell writer fed a literal string: text passed through the shell (H8)"
                    written.update(files)
            if j == 0 and kind and tg:
                if kind == "literal" and (any(_is_doc(t) for t in tg) or lit_len > ECHO_MAX):
                    return "a PowerShell literal string redirected into a doc or code file (H8)"
                if live_bt and kind == "echo" and "$(" in lit_text:
                    return "an echo/printf with a live backtick written to a file: the shell runs it (H11)"
                written.update(tg)
            if piped:
                r, files = _pipe_into_reason(ws, vals, h, tg, kind, lit_text, lit_len, live_bt)
                if r:
                    return r
                written.update(files)
            if "<<<" in vals and h in {"cat", "tee"}:
                k = vals.index("<<<")
                operand = ws[k + 1].v if k + 1 < len(ws) else ""
                skip = _operand_positions(ws)
                files = tg + ([w.v for m, w in enumerate(ws) if m > 0 and m not in skip and not w.v.startswith("-")]
                              if h == "tee" else [])
                if files and (any(_is_doc(f) for f in files) or len(operand) > ECHO_MAX):
                    return "a here-string (`<<<`) written to a doc or code file by cat/tee (H10)"
    return None


def evaluate(text: str, shell: str, p, depth: int = 0) -> "str | None":
    """The reason to block `text`, or None to allow it."""
    if depth > 4 or not text or not text.strip():
        return None
    cmds, _scripts = p.commands(text, shell)
    clean = (p._prescan_ps if shell == "ps" else p._prescan_bash)(text)[0]
    heads = {_head(p._strip_prefix(c)[0][0]) for c in cmds if p._strip_prefix(c)[0]}
    herestring_line = shell == "ps" and any("HERESTRING" in c for c in cmds)
    live_ltlt = _heredoc_live(clean, shell)
    line_targets = [t for c in cmds for t in _out_targets(p._strip_prefix(c)[0])] if herestring_line else []
    for cmd in cmds:
        for tok in cmd:
            for inner in p.substitutions(tok):
                r = evaluate(inner, shell, p, depth + 1)
                if r:
                    return r
        r = command_reason(cmd, p, heads, herestring_line, live_ltlt, line_targets)
        if r:
            return r
        rest = p._strip_prefix(cmd)[0]
        if rest and not _hatch(cmd):
            head = _head(rest[0])
            if head in SHELL_HEADS:
                inner = p._shell_inner(head, rest)
                if inner:
                    r = evaluate(inner, "ps" if head in {"pwsh", "powershell"} else "bash", p, depth + 1)
                    if r:
                        return r
            elif head == "find":
                r = _find_exec_reason(rest, p, depth)
                if r:
                    return r
    return line_reason(text, shell, p, clean)


# ------------------------------------------------------------------------------------------------ the self-test table
B, A = True, False
LONG = "word " * 62              # a PROSE stand-in, 310 characters (FP-2: H6 keys on prose, no longer on raw length)
S250 = ("T1-3 aborted the batch in 0.8 min as predicted; the live leak monitor fired on lane 4 and the "
        "freeze watch stayed silent, which is the expected outcome for a clean arm header on every lane. ok")
S400 = S250 + " " + S250[:150]
PROMPT600 = "In Pokemon Emerald, list every script label and flag set during the Mossdeep Gym puzzle. " * 7
LONGRO = ("import ast, sys\n" + "".join(f"a{k} = open(sys.argv[1], encoding='utf-8').read().count('def ')\n"
                                      for k in range(6)) + "print(a0)")   # read-only, spaced like real code (FP-1)
SPECIES = ",".join(["TREECKO", "GROVYLE", "SCEPTILE", "TORCHIC", "COMBUSKEN", "BLAZIKEN", "MUDKIP", "MARSHTOMP"] * 6)
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
    # --- H6 prose arguments to a script (the stand-in is prose since FP-2) ------------------------------------------------
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
    # =================== the adversarial pass (2026-10-01), every finding in both directions ===================
    # --- FP-1: python running -c code: its .py argument is DATA, never a script for H6 -----------------------------------
    ("bash", A, f'py -3.12 -c "{LONGRO}" "$SP/sm_head.py"'),
    ("bash", B, f'py -3.12 x.py -c "{LONG}"'),                                 # a SCRIPT's own -c option: still H6
    ("bash", B, f'py -3.12 -c "{LONGRO}"; py -3.12 a.py "{LONG}"'),            # -c in one command, prose in the next
    # --- FP-2: an unquoted data list is not prose ------------------------------------------------------------------------
    ("bash", A, f"python ../learn.py {SPECIES} 40 FIRE,ELECTRIC 2>&1"),
    # --- FP-3: echo/printf with no visible content -----------------------------------------------------------------------
    ("bash", A, "cat \"$S/m.md\" >> \"PROJECT KNOWLEDGE/08-MISTAKES.md\"; printf '\\n' >> \"PROJECT KNOWLEDGE/08-MISTAKES.md\""),
    ("bash", B, "printf '\\n%s\\n' 'x = 1' >> tools/story-dev/x.py"),
    ("bash", B, "echo -e \"\\nimport os\" >> a.py"),
    # --- BH-08: a QUOTED '<<' is a mention; PowerShell has no heredocs; bash bodies stay bash -----------------------------
    ("bash", A, "grep -n '<<' a.sh"),
    ("bash", A, "git log --grep '<<' --oneline"),
    ("bash", A, "grep -c \"<<\" \"PROJECT KNOWLEDGE/08-MISTAKES.md\""),
    ("bash", A, "echo '<<'"),
    ("ps", A, "Select-String -Path a.md -Pattern '<<'"),
    ("bash", B, "echo it\\'s && cat > a.md <<EOF\nx\nEOF"),
    ("ps", B, "bash -c \"cat > a.md <<'EOF'\nx\nEOF\""),
    ("bash", B, "git commit -m \"$(cat <<'EOF'\nfeat: x\nEOF\n)\""),
    # --- BH-12: a here-string as stdin DATA for a script ---------------------------------------------------------------
    ("bash", A, "py -3.12 x.py <<< \"y\""),
    ("bash", B, "python3 <<< \"print(1)\""),
    # --- BH-01: a git message through the shell -------------------------------------------------------------------------
    ("bash", B, "git commit -m \"docs: measure offline with `probe_live_mapgrid.py`, which is an existing tool\""),
    ("bash", B, f"git commit -m \"feat: subject (punch-list #26)\" -m \"{S250}\""),
    ("bash", B, "git commit -m \"feat: x\n\nbody line\""),
    ("ps", B, "git commit -m \"feat: a long multi-line message`n`nwith $x and more words here\""),
    ("ps", B, "git commit -m \"docs: the `\"x`\" flag\""),                     # a backtick alone (no `$`)
    ("bash", A, "git commit -am \"wip\""),
    ("bash", A, "git commit -m \"$(cat C:/x/msg.txt)\""),
    ("bash", A, "git merge --no-ff -m \"merge wt/batch14\" wt/batch14"),
    ("bash", A, "git commit -m 'docs: the `x` flag, single-quoted, never expands'"),
    ("bash", A, "git tag -a v1 -m \"release v1\""),
    # --- BH-04: a here-string commit message -----------------------------------------------------------------------------
    ("ps", B, "git commit -m @'\nfeat: x\n\nbody with `code`\n'@"),
    ("ps", B, "@'\nfeat: x\n'@ | git commit -F -"),
    ("ps", B, "$msg = @'\nfeat: x\n'@; git commit -m $msg"),
    # --- BH-02: PowerShell writers fed a literal (doc/code target, or over 120 characters) --------------------------------
    ("ps", B, "Add-Content -Path \"PROJECT KNOWLEDGE\\07-CHANGELOG.md\" -Value \"" + S250 + "\""),
    ("ps", B, "\"text\" > x.md"),
    ("ps", B, "[IO.File]::WriteAllText(\"x.md\", \"text\")"),
    ("ps", B, "Set-Content x.md \"text\" -Encoding utf8"),
    ("ps", B, "Write-Output 'text' | Set-Content x.md"),
    ("ps", B, "New-Item -Path x.md -ItemType File -Value \"text\" -Force"),
    ("ps", B, "Set-Content x.md -Value @('line1','line2')"),
    ("ps", B, "powershell -Command \"Set-Content x.md 'text'\""),
    ("ps", B, "Add-Content -Path C:\\x\\scratchpad\\notes.txt -Value \"" + S250 + "\""),
    ("ps", A, "Set-Content -Path flag.txt -Value 1"),
    ("ps", A, "Get-Content a.md | Set-Content b.md"),
    ("ps", A, "$r | ConvertTo-Json -Depth 5 | Set-Content out.json"),
    ("ps", A, "\"started $(Get-Date)\" >> C:\\x\\scratchpad\\run.txt"),
    ("ps", A, "py -3.12 x.py | Out-File -Encoding utf8 C:\\x\\scratchpad\\out.md"),
    ("ps", A, "[IO.File]::WriteAllText(\"C:\\x\\scratchpad\\out.txt\", $json)"),
    ("ps", A, "Add-Content -Path \"C:\\x\\scratchpad\\run.txt\" -Value \"exit=$LASTEXITCODE\""),
    # --- BH-03: an in-place regex edit of a doc or code file -------------------------------------------------------------
    ("bash", B, "sed -i 's/old phrase/new phrase/' \"PROJECT KNOWLEDGE/04-HANDOFF.md\""),
    ("bash", B, "perl -pi -e 's/old/new/g' x.md"),
    ("bash", B, "awk -i inplace '{gsub(/a/,\"b\")}1' x.md"),
    ("bash", B, "find . -name '*.md' -exec sed -i 's/a/b/' {} +"),
    ("ps", B, "(Get-Content x.md) -replace 'old','new' | Set-Content x.md"),
    ("ps", B, "(Get-Content x.md -Raw).Replace('old','new') | Set-Content x.md -Encoding utf8"),
    ("bash", A, "sed -n '1,20p' a.md"),
    ("bash", A, "sed -E 's/a/b/' a.md | head"),
    ("bash", A, "perl -Mstrict -ne 'print if /x/' a.md"),
    ("bash", A, "sed -i 's/a/b/' C:/x/scratchpad/notes.txt"),            # not a doc/code target
    ("bash", A, "sed -i 's|  PROJECT KNOWLEDGE/07-CHANGELOG.md$|x|' C:/x/scratchpad/msg4.txt"),  # the SCRIPT names a doc
    ("bash", B, "perl -pie 's/a/b/' x.py"),                                # -pie: -i with suffix "e", file x.py
    ("bash", B, "sed -ne 's/a/b/p' -i notes.md"),
    ("ps", A, "(Get-Content a.md) -replace 'a','b' | Select-String x"),
    ("ps", A, "(Get-Content a.log) -replace '\\s+$','' | Out-File C:\\x\\scratchpad\\clean.txt"),
    # --- BH-05 / BH-13: prose as script arguments ------------------------------------------------------------------------
    ("bash", B, "py -3.12 append.py \"" + S250 + "\""),
    ("bash", B, "py -3.12 append.py \"" + S250[:150] + "\" \"" + S250[100:] + "\""),
    ("ps", B, "& .\\append.ps1 -Text \"" + S400 + "\""),
    ("bash", B, "py -3.12 -m tools.append \"" + S400 + "\""),
    ("bash", B, "bash append.sh \"" + S400 + "\""),
    ("bash", B, "PYTHONUTF8=1 py -3.12 tools/story-dev/gemini_relay.py \"" + PROMPT600 + "\""),
    ("bash", A, "py -3.12 x.py \"C:/Remote Projects/pokebot-wt-ch24/tools/story-dev/evidence/2026-10-01-batch14-T1-ADVERSARIAL.txt\""),
    ("bash", A, "py -3.12 x.py --label \"a short label with nine spaces in it for the run\""),
    ("bash", A, "py -3.12 tools/story-dev/gemini_relay.py --file C:/x/q.md --out C:/x/a.md"),
    ("bash", A, "py -3.12 tools/story-dev/gemini_relay.py \"What script sets FLAG_X in Mossdeep?\""),
    # --- BH-06: literal text piped into a writer or an interpreter -------------------------------------------------------
    ("bash", B, "echo \"- entry about `x`\" | tee -a \"PROJECT KNOWLEDGE/07-CHANGELOG.md\""),
    ("bash", B, "echo \"x\" | py -3.12 -"),
    ("bash", B, "echo \"text\" | cat >> \"PROJECT KNOWLEDGE/07-CHANGELOG.md\""),
    ("bash", B, "echo \"x\" | dd of=a.md"),
    ("bash", B, "printf 'feat: x\\n\\nbody\\n' | git commit -F -"),
    ("ps", B, "\"text\" | Tee-Object -FilePath x.md"),
    ("ps", B, "\"open('x.md','w').write('x')\" | py -3.12 -"),
    ("bash", B, "tee a.md <<< \"text\""),
    ("bash", B, "cat <<< \"long text\" > a.md"),
    ("bash", A, "PYTHONUTF8=1 py -3.12 x.py 2>&1 | tee run.log"),
    ("bash", A, "git log --oneline -5 | tee out.txt"),
    ("bash", A, "echo hi | py -3.12 x.py"),
    ("bash", A, "cat <<< \"$v\" | grep x"),
    ("bash", A, "echo \"exit=$?\" | tee -a C:/x/scratchpad/run.log"),
    # --- BH-07: python -c write variants, and -c output redirected into a doc ---------------------------------------------
    ("bash", B, "py -c \"f=open('x.md', encoding='utf-8', mode='w'); f.write('x')\""),
    ("bash", B, "py -c \"from pathlib import Path; Path('x.md').open('w').write('x')\""),
    ("bash", B, "py -c \"from pathlib import Path; open(Path('d')/'x.md', 'w').write('x')\""),
    ("bash", B, "py -3.12 -c \"print('# heading')\" > \"PROJECT KNOWLEDGE/x.md\""),
    ("bash", B, "py -c \"f=open('x.md', 'r+'); f.write('x')\""),
    ("bash", B, "py -c \"import os; fd=os.open('x.md', os.O_WRONLY|os.O_CREAT); os.write(fd, b'x')\""),
    ("bash", B, "py -c \"import fileinput,sys\nfor l in fileinput.input('x.md', inplace=True): sys.stdout.write(l)\""),
    ("bash", B, "py -Bc \"open('x.md','w').write('x')\""),
    ("bash", A, "py -c \"print(open('x.md').read().count('a'))\""),
    ("bash", A, "py -3.12 -c \"import pathlib; print(pathlib.Path('a.md').open(encoding='utf-8').read()[:100])\""),
    ("bash", A, "py -3.12 -c \"import x4_headless\" > out.txt"),
    # --- BH-09: an echo-built commit file; a live backtick into a file ----------------------------------------------------
    ("bash", B, "echo \"feat: add `x` flag (punch-list #26)\" > \"C:/x/scratchpad/msg.txt\" && git commit -F \"C:/x/scratchpad/msg.txt\""),
    ("bash", B, "printf 'feat: x' > msg.txt && git commit -F msg.txt"),
    ("bash", B, "echo \"a `code` note\" >> C:/x/scratchpad/notes.txt"),
    ("bash", A, "echo \"started $(date)\" >> run.txt"),
    ("bash", A, "echo 'a `code` note, single-quoted' >> C:/x/scratchpad/notes.txt"),
    # --- BH-10: a here-string variable redirected by a LATER command ------------------------------------------------------
    ("ps", B, "$t = @'\nbody\n'@; $t > x.md"),
    ("ps", B, "$t = @'\nbody\n'@; $t >> \"PROJECT KNOWLEDGE\\07-CHANGELOG.md\""),
    ("ps", A, "$m = @'\nfeat: x\n'@; git status 2>$null; git log -1 2> err.txt"),
    # --- BH-11: the wider doc/code extensions (.txt deliberately NOT one) ------------------------------------------------
    ("bash", B, "echo '#!/bin/bash' > run.sh"),
    ("bash", B, "echo 'timeout = 30' > config.toml"),
    ("bash", B, "echo 'print(1)' > x.pyw"),
    ("bash", B, "echo '<p>x</p>' > page.html"),
    ("bash", A, "echo '- [ ] item' >> TODO.txt"),
    # --- the hatch reaches the line rules --------------------------------------------------------------------------------
    ("bash", A, f"{HATCH}=1 git commit -m \"feat: subject\" -m \"{S250}\""),
    ("bash", A, f"{HATCH}=1 sed -i 's/a/b/' x.md"),
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
    print(f"  OK  block_shell_text.py: {len(CASES)}/{len(CASES)} cases (the five incidents, H1-H11, every adversarial "
          f"finding both ways, mentions, ordinary work, the hatch)")
    return 0


# ------------------------------------------------------------------------------------------------ hook entry point
REASON = """BLOCKED: {why}.

USER RULING 29 (2026-10-01): documentation and code text never pass through a shell-quoted string. Shell quoting
silently rewrites backslashes, `$` and backticks; this rule broke five times in two sessions before it became a hook.

Do this instead:
  * a file's content, or an in-place edit (sed -i, perl -i, -replace): use the Write or Edit tool;
  * a script: Write it to a file (the scratchpad), then run that file;
  * an extractor, downloader or EOL fixer that writes a file: Write it as a script;
  * a commit message: Write it to a file with the Write tool, then 'git commit -F <file>';
  * text for a script: Write it to a file and pass the PATH, never the text
    (a long Gemini prompt: 'gemini_relay.py --file <prompt file>').
Add-Content is encoding-safe, but literal doc text still goes through the Write tool.

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
