r"""PreToolUse(Bash|PowerShell) hook - REFUSE git commands that can silently DISCARD work.

WHY (2026-09-27, `08-MISTAKES.md`): a reviewer agent "reverted" a test mutation with `git checkout -- <file>` while the
fix under review was UNCOMMITTED, and deleted the fix. CLAUDE.md already said: never discard local work, ask before any
destructive git operation or branch deletion, never force-push. The user approved enforcing it (2026-09-28).

HOW IT PARSES (version 3; each version was broken by an adversarial review, and its cases are in the table below):
  1. `prescan` - a character-level state machine per shell (bash / PowerShell) that knows quotes and escapes. It strips
     comments ONLY where a word starts (the newline is kept, so `cmd  # note` + newline + `git reset --hard` stays TWO
     commands), joins line continuations, blanks heredoc / here-string BODIES only when the opener is in live text (any
     delimiter word, `<<-`, quoted or `\EOF`), and turns backticks into `$( )`. A heredoc fed to a shell
     (`bash <<EOF`) is returned as a script to evaluate.
  2. `shlex` (posix, no comment handling, PowerShell without backslash escapes) splits the clean text into words and
     `; && || | ( ) < >` punctuation; a newline is a separator.
  3. Every `$( ... )` inside any word (double-quoted strings included) is evaluated as a command.
  4. Per command: assignments, keywords and wrappers are stripped (env, xargs, sudo, nice, timeout, `$x =`, `&`, then /
     do, ...); `cd` changes the directory later checkout operands resolve against; shells (`bash -c`, `bash -lc`,
     `cmd /c`, `cmd //c`, `powershell [-Command] ...`), `find -exec`, `git submodule foreach` are evaluated inside.
  5. git: global options skipped (`-c alias.*` / `clean.requireForce` / `remote.*.mirror` blocked), aliases expanded,
     redirections (and their fd number: `2>&1`) removed, then the subcommand rules below.
  Output is `json.dumps` (ASCII); this file is ASCII-only (a BOM-less PowerShell draft emitted invalid JSON).

WHAT IT BLOCKS - any git command that can discard uncommitted work, published history or a branch:
  checkout: `--` paths | a path operand (resolved against the repo; `$var`, xargs and `{}` operands count as paths) |
    a path after a tree-ish | -f/--force/--ours/--theirs/-p | -B;   restore (unless only --staged);   reset --hard/--merge;
  stash (not list/show/apply/create/store/-h);   clean with force (not with -n);   switch --discard-changes/-f/-C;
  branch -d/-D/-f/-M/-C/--delete;   push --force/-f/--force-with-lease/--force-if-includes/--mirror/--delete/-d/--prune,
  a `+refspec`, a `:ref` delete;   fetch `+refspec`;   worktree remove;   rm -f (not --cached);
  update-ref -d/--stdin/refs/heads/...;   read-tree --reset -u;   checkout-index -f;   apply -R (not --check/--cached);
  filter-branch;  filter-repo;  reflog expire/delete;  prune;  gc --prune=now.
  Long options match by unique prefix of 2+ characters, as git accepts.

ALLOWS: branch switching (checkout operands are asked of the repo: a real branch/tag/commit is not a file), checkout -b,
restore --staged, reset <path>/--soft/--mixed, stash list/show/apply, clean -n, rm --cached, ordinary push, and every
MENTION (quoted text, heredoc bodies, comments, commit messages).

ESCAPE HATCH, ONLY for an operation the USER approved: a live `POKEBOT_ALLOW_DESTRUCTIVE_GIT=1` assignment in front of
the git command itself, or the variable set in Claude Code's own environment. Mentions elsewhere never count.

KNOWN LIMITS (deliberate evasion, not autopilot): PowerShell splatting (`git @a`), a variable as the subcommand
(`git $cmd`), `eval`, interpreters that shell out (`py -c "os.system(...)"`), GIT_* environment redirection, unicode
look-alike whitespace. The hook is a seat belt against habit, not a sandbox against an adversary.

Contract: tool call JSON on stdin; exit 0 always (fails OPEN on any internal error); print a JSON "deny" to block.
`--selftest` runs the case table and exits 1 on any failure. Gate: `tools/story-dev/selftest_destructive_git_hook.py`.
"""
from __future__ import annotations

import base64
import copy
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

HATCH = "POKEBOT_ALLOW_DESTRUCTIVE_GIT"
PUNCT = ";&|()<>\n"
ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
REDIR = re.compile(r"^(\d*|&|\*)?(>>?|<<?|>&|<&|&>>?)$")
PREFIX_WORDS = {"then", "do", "else", "elif", "if", "while", "until", "!", "time", "exec", "nohup", "builtin", "&", ".",
                "call", "coproc", "winpty", "$", "eval", "{", "}"}
OPT_WRAPPERS = {"env": {"-u", "-C", "-S"}, "xargs": {"-I", "-L", "-n", "-P", "-d", "-E", "-s", "-a", "--max-args",
                "--max-procs", "--delimiter", "--arg-file", "--max-lines"}, "sudo": {"-u", "-g", "-C"},
                "nice": {"-n"}, "stdbuf": {"-o", "-e", "-i"}, "command": set(), "timeout": {"-s", "-k"}}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "pwsh", "powershell", "cmd"}
GIT_BUILTINS = {
    "add", "am", "apply", "archive", "bisect", "blame", "branch", "bundle", "cat-file", "check-ignore", "checkout",
    "checkout-index", "cherry", "cherry-pick", "clean", "clone", "commit", "config", "count-objects", "describe", "diff",
    "diff-files", "diff-index", "diff-tree", "fetch", "filter-branch", "filter-repo", "for-each-ref", "format-patch",
    "fsck", "gc", "grep", "hash-object", "help", "init", "log", "ls-files", "ls-remote", "ls-tree", "merge", "merge-base",
    "mv", "notes", "prune", "pull", "push", "range-diff", "read-tree", "rebase", "reflog", "remote", "replace", "reset",
    "restore", "rev-list", "rev-parse", "revert", "rm", "shortlog", "show", "show-ref", "sparse-checkout", "stash",
    "status", "submodule", "subtree", "switch", "symbolic-ref", "tag", "update-index", "update-ref", "var", "version",
    "whatchanged", "worktree", "write-tree", "maintenance", "lfs", "credential", "request-pull", "verify-commit",
}
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env",
                         "--exec-path", "--list-cmds", "--attr-source"}
UNRESOLVED = "XARGS_OPERAND"


# ------------------------------------------------------------------------------------------------ context (injectable)
class Ctx:
    """How the hook asks the repo whether a token is a ref, a path, or an alias. The self-test swaps in tables."""

    def __init__(self, cwd: "str | None"):
        self.cwd = Path(cwd) if cwd else Path.cwd()

    def with_cwd(self, d: str) -> "Ctx":
        c = copy.copy(self)
        p = Path(d)
        c.cwd = p if p.is_absolute() else self.cwd / p
        return c

    def _git(self, base: Path, *args: str) -> "subprocess.CompletedProcess | None":
        try:
            return subprocess.run(["git", "-C", str(base), *args], capture_output=True, text=True, timeout=3)
        except (OSError, subprocess.SubprocessError):
            return None

    def base(self, c_dir: "str | None") -> Path:
        if not c_dir:
            return self.cwd
        p = Path(c_dir)
        return p if p.is_absolute() else self.cwd / p

    def is_ref(self, tok: str, c_dir: "str | None") -> bool:
        b = self.base(c_dir)
        r = self._git(b, "rev-parse", "--verify", "--quiet", f"{tok}^{{commit}}")
        if r is not None and r.returncode == 0:
            return True
        r = self._git(b, "for-each-ref", "--count=1", "--format=%(refname)", f"refs/heads/{tok}", f"refs/tags/{tok}",
                      f"refs/remotes/*/{tok}")
        return bool(r is not None and r.returncode == 0 and r.stdout.strip())

    def is_path(self, tok: str, c_dir: "str | None") -> bool:
        try:
            return (self.base(c_dir) / tok).exists()
        except (OSError, ValueError):
            return False

    def alias(self, name: str, c_dir: "str | None") -> "str | None":
        r = self._git(self.base(c_dir), "config", "--get", f"alias.{name}")
        return r.stdout.strip() if r is not None and r.returncode == 0 and r.stdout.strip() else None


# ------------------------------------------------------------------------------------------------ 1. the pre-scan
_TAG_END = set(" \t\r\n;&|<>()")


def _word_start(out: list) -> bool:
    return not out or out[-1] in " \t\r\n;&|()<>"


def _prescan_bash(text: str) -> "tuple[str, list]":
    out, scripts, pending, i, n = [], [], [], 0, len(text)
    state = "N"
    while i < n:
        c = text[i]
        if state == "S":                                   # single quotes: nothing escapes
            out.append(c)
            state = "N" if c == "'" else "S"
            i += 1
            continue
        if state == "D":                                   # double quotes: \ escapes, ` is a substitution
            if c == "\\" and i + 1 < n:
                out.append(c + text[i + 1]); i += 2; continue
            if c == "`":
                j = text.find("`", i + 1)
                j = n if j < 0 else j
                out.append("$(" + text[i + 1:j] + ")"); i = j + 1; continue
            if c == '"':
                state = "N"
            out.append(c); i += 1
            continue
        # --- normal (live) text ---------------------------------------------------------------------------------------
        if c == "\\" and i + 1 < n:
            if text[i + 1] == "\n":                        # line continuation
                out.append(" "); i += 2; continue
            out.append(c + text[i + 1]); i += 2; continue
        if c == "'":
            state = "S"; out.append(c); i += 1; continue
        if c == '"':
            state = "D"; out.append(c); i += 1; continue
        if c == "`":
            j = text.find("`", i + 1)
            j = n if j < 0 else j
            out.append(" $( " + text[i + 1:j] + " ) "); i = j + 1; continue
        if c == "#" and _word_start(out):                  # a comment: drop to end of line, KEEP the newline
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "<" and text.startswith("<<", i) and not text.startswith("<<<", i) and (i == 0 or text[i - 1] != "<"):
            j = i + 2
            dash = j < n and text[j] == "-"
            j += 1 if dash else 0
            while j < n and text[j] in " \t":
                j += 1
            if j < n and text[j] in "'\"":
                q = text[j]; k = text.find(q, j + 1); k = n if k < 0 else k
                tag = text[j + 1:k]; j = k + 1
            else:
                if j < n and text[j] == "\\":
                    j += 1
                k = j
                while k < n and text[k] not in _TAG_END:
                    k += 1
                tag = text[j:k].replace("'", "").replace('"', ""); j = k
            if tag:
                line = "".join(out).rsplit("\n", 1)[-1]
                head = re.split(r"[\s;&|()]+", line.strip() or "x")[0]
                head = re.split(r"[\\/]", head)[-1].lower().removesuffix(".exe")
                pending.append((tag, dash, head in SHELLS))
                out.append(" << '" + tag + "' "); i = j
                continue
        if c == "\n" and pending:                          # heredoc bodies start after this newline
            out.append("\n"); i += 1
            for tag, dash, is_shell in pending:
                body = []
                while i < n:
                    e = text.find("\n", i)
                    e = n if e < 0 else e
                    ln = text[i:e]
                    i = e + 1
                    if (ln.lstrip("\t") if dash else ln).rstrip("\r") == tag:
                        break
                    body.append(ln)
                if is_shell:
                    scripts.append("\n".join(body))
            pending = []
            continue
        out.append(c); i += 1
    return "".join(out), scripts


def _prescan_ps(text: str) -> "tuple[str, list]":
    out, i, n, state = [], 0, len(text), "N"
    while i < n:
        c = text[i]
        if state == "S":                                   # '...': '' is an escaped quote
            out.append(c)
            if c == "'" and text.startswith("''", i):
                out.append("'"); i += 2; continue
            state = "N" if c == "'" else "S"
            i += 1
            continue
        if state == "D":                                   # "...": `x escapes, "" is an escaped quote
            if c == "`" and i + 1 < n:
                out.append('""' if text[i + 1] == '"' else text[i + 1]); i += 2; continue
            if c == '"' and text.startswith('""', i):
                out.append('""'); i += 2; continue
            if c == '"':
                state = "N"
            out.append(c); i += 1
            continue
        if c == "`" and i + 1 < n:
            if text[i + 1] in "\r\n":                      # line continuation
                i += 3 if text.startswith("\r\n", i + 1) else 2
                out.append(" "); continue
            out.append(text[i + 1]); i += 2; continue
        if c == "@" and i + 1 < n and text[i + 1] in "'\"":
            m = re.match(r"@(['\"])[ \t]*\r?\n", text[i:])
            if m:                                          # a here-string: body until a line starting with q@
                q = m.group(1)
                e = re.search(r"\r?\n" + re.escape(q) + "@", text[i + m.end() - 1:])
                i = (i + m.end() - 1 + e.end()) if e else n
                out.append(" 'HERESTRING' ")
                continue
        if c == "<" and text.startswith("<#", i):          # a block comment
            e = text.find("#>", i + 2)
            i = n if e < 0 else e + 2
            out.append(" ")
            continue
        if c == "#" and _word_start(out):
            while i < n and text[i] not in "\r\n":
                i += 1
            continue
        if c == "'":
            state = "S"
        elif c == '"':
            state = "D"
        out.append("\n" if c == "\r" else c)
        i += 1
    return "".join(out), []


def lex(text: str, shell: str) -> "list[str]":
    lx = shlex.shlex(text, posix=True, punctuation_chars=PUNCT)
    lx.whitespace = " \t\r"
    lx.whitespace_split = True
    lx.commenters = ""
    if shell == "ps":
        lx.escape = ""
    return list(lx)


def _is_sep(t: str) -> bool:
    return bool(t) and set(t) <= set(PUNCT) and (bool(set(t) & set(";|()\n")) or t in {"&", "&&"})


def commands(text: str, shell: str) -> "tuple[list, list]":
    """Split a tool command into simple commands (token lists), plus scripts found inside it (heredocs fed to shells)."""
    clean, scripts = _prescan_ps(text) if shell == "ps" else _prescan_bash(text)
    toks = None
    for attempt in (clean, clean + '"', clean + "'"):
        try:
            toks = lex(attempt, shell)
            break
        except ValueError:
            continue
    if toks is None:
        return [], scripts          # unbalanced beyond repair: the shell will refuse to run it too
    out, cur = [], []
    for t in toks:
        # A script block `{ ... }` (PowerShell: ForEach-Object { }, try { } catch { }; bash: a group) is a command
        # boundary. A token that merely CONTAINS braces (`stash@{0}`, `@{-1}`, find's `{}`) is not.
        if t.startswith("{") and t not in {"{", "{}"}:
            if cur:
                out.append(cur)
            cur = [t[1:]]
            continue
        if t.endswith("}") and t != "}" and "{" not in t:
            cur.append(t[:-1])
            out.append(cur)
            cur = []
            continue
        if _is_sep(t) or t in {"{", "}"}:
            if cur:
                # `git checkout -- (git diff --name-only)`: a parenthesised expression is an OPERAND.
                if "(" in t and re.split(r"[\\/]", cur[0])[-1].lower().removesuffix(".exe") == "git":
                    cur.append(UNRESOLVED)
                out.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        out.append(cur)
    return out, scripts


def substitutions(tok: str) -> "list[str]":
    """Every `$( ... )` body inside a word (quoted text included: bash and PowerShell both run it)."""
    found, i = [], 0
    while i < len(tok):                                  # bounded: `i` strictly increases
        i = tok.find("$(", i)
        if i < 0:
            return found
        depth, j = 1, i + 2
        while j < len(tok) and depth:
            depth += {"(": 1, ")": -1}.get(tok[j], 0)
            j += 1
        found.append(tok[i + 2:j - 1])
        i = j
    return found


# ------------------------------------------------------------------------------------------------ option helpers
def lopt(a: str, name: str, minlen: int = 2) -> bool:
    """`a` is the long option `--name` or a prefix of it of `minlen`+ characters (git accepts unique prefixes)."""
    if not a.startswith("--") or a == "--":
        return False
    k = a[2:].split("=", 1)[0]
    return len(k) >= min(minlen, len(name)) and name.startswith(k)


def sopt(a: str, letters: str) -> bool:
    """`a` is a short-option bundle (`-fd`) containing any of `letters` (case-sensitive)."""
    return a.startswith("-") and not a.startswith("--") and len(a) > 1 and any(c in a[1:] for c in letters)


def last_flag(opts: "list[str]", on: str, off: str, short: str = "") -> bool:
    """git's last-one-wins for `--x` / `--no-x` (and a short letter for `--x`)."""
    val = False
    for a in opts:
        if lopt(a, off, len(off)):
            val = False
        elif lopt(a, on) or (short and sopt(a, short)):
            val = True
    return val


def looks_like_path(t: str) -> bool:
    if t in {".", "./", ".\\", "..", "*", "**", ":/", "{}", UNRESOLVED} or t.startswith((":(", "$")) or t.endswith(("/", "\\")):
        return True
    return bool(re.match(r"^\.[A-Za-z]", t) or re.search(r"\.[A-Za-z][A-Za-z0-9_-]{0,9}$", t))


def strip_redirections(args: "list[str]") -> "list[str]":
    """Drop redirection operators, their targets, and an fd number / `&` / `*` token in front of them (`2>&1`)."""
    out, i = [], 0
    while i < len(args):
        t = args[i]
        if REDIR.match(t):
            if out and re.match(r"^(\d+|&|\*)$", out[-1]):
                out.pop()
            i += 2 if not t.endswith("&") or (i + 1 < len(args) and re.match(r"^\d+$", args[i + 1])) else 1
            continue
        out.append(t)
        i += 1
    return out


# ------------------------------------------------------------------------------------------------ 5. git rules
def git_reason(args: "list[str]", ctx: Ctx, depth: int, env_alias: bool = False) -> "str | None":
    if env_alias:
        return "a GIT_CONFIG_KEY_n=alias.* override can change what a git command does"
    args = strip_redirections(args)
    i, c_dir = 0, None
    while i < len(args) and args[i].startswith("-") and args[i] != "--":
        a = args[i]
        cfg = args[i + 1] if a in {"-c", "--config-env"} and i + 1 < len(args) else (
            a.split("=", 1)[1] if a.startswith("--config-env=") else None)
        if cfg is not None:
            key = cfg.split("=", 1)[0].lower()
            if key.startswith("alias.") or key == "clean.requireforce" or re.match(r"remote\..*\.(mirror|push)$", key):
                return f"a config override of {key} can change what a git command does"
        if a == "-C" and i + 1 < len(args):
            c_dir = args[i + 1]
        i += 2 if a in GIT_GLOBAL_WITH_VALUE else 1
    if i >= len(args):
        return None
    sub, rest = args[i].lower(), args[i + 1:]
    opts = [a for a in rest if a.startswith("-") and a != "--"]
    operands = [a for a in rest if not a.startswith("-")]

    if sub not in GIT_BUILTINS and depth < 3:
        exp = ctx.alias(sub, c_dir)
        if exp:
            if exp.startswith("!"):
                return evaluate(exp[1:] + " " + shlex.join(rest), "bash", ctx, depth + 1)
            return git_reason(shlex.split(exp) + rest, ctx, depth + 1)

    if sub == "checkout":
        if any(lopt(a, "force") or lopt(a, "ours") or lopt(a, "theirs") or lopt(a, "patch") or sopt(a, "fp")
               for a in opts):
            return "checkout with --force/--ours/--theirs/-p overwrites uncommitted changes"
        if "-B" in rest:
            return "checkout -B resets an existing branch"
        if any(lopt(a, "pathspec-from-file") for a in opts):
            return "checkout of paths from a file discards their uncommitted changes"
        if "--" in rest and rest.index("--") < len(rest) - 1:
            return "checkout of paths after '--' discards their uncommitted changes"
        if "-b" in rest or any(lopt(a, "orphan") for a in opts):
            return None            # creating a branch: operands are the name and a start point, never paths
        ops = [a for a in rest if a != "--" and not a.startswith("-")]
        if not ops:
            return None
        if ops[0] not in {UNRESOLVED, "{}"} and not ops[0].startswith("$") and ctx.is_ref(ops[0], c_dir):
            return "checkout of paths after a tree-ish discards their uncommitted changes" if ops[1:] else None
        if ctx.is_path(ops[0], c_dir) or looks_like_path(ops[0]):
            return f"checkout of a path ('{ops[0]}') discards its uncommitted changes"
        return None
    if sub == "restore":
        staged = last_flag(opts, "staged", "no-staged", "S")
        worktree = last_flag(opts, "worktree", "no-worktree", "W")
        paths = operands or any(lopt(a, "pathspec-from-file") for a in opts)
        if paths and (not staged or worktree):
            return "restore of working-tree files discards their uncommitted changes (use --staged to only unstage)"
        return None
    if sub == "reset":
        return "reset --hard/--merge discards uncommitted changes" if any(
            lopt(a, "hard") or lopt(a, "merge", 3) for a in opts) else None
    if sub == "stash":
        if any(a in {"-h", "--help"} for a in opts):
            return None
        verb = operands[0].lower() if operands else "push"
        return None if verb in {"list", "show", "apply", "create", "store"} else f"stash {verb} hides or drops work"
    if sub == "clean":
        force = any(lopt(a, "force") or sopt(a, "f") for a in opts)
        dry = last_flag(opts, "dry-run", "no-dry-run", "n")
        return "clean -f deletes untracked files (use -n for a dry run)" if force and not dry else None
    if sub == "switch":
        if any(lopt(a, "discard-changes") or lopt(a, "force") or sopt(a, "fC") or lopt(a, "force-create", 7)
               for a in opts):
            return "switch --discard-changes/--force/-C discards changes or resets a branch"
        return None
    if sub == "branch":
        if any(lopt(a, "delete") or lopt(a, "force") or sopt(a, "dDfMC") for a in opts):
            return "branch deletion or forced move/rename/copy (CLAUDE.md: ask the user first)"
        return None
    if sub == "push":
        for a in rest:
            if any(lopt(a, n, 3) for n in ("force", "force-with-lease", "force-if-includes", "mirror", "delete", "prune")) \
                    or sopt(a, "fd"):
                return f"push {a} (CLAUDE.md: never force-push, never rewrite published history)"
            if not a.startswith("-") and (a.startswith("+") or (a.startswith(":") and len(a) > 1)):
                return f"push refspec '{a}' forces or deletes a remote ref"
        return None
    if sub == "fetch":
        forced = any(o.startswith("+") for o in operands) or (
            any(lopt(a, "force") or sopt(a, "f") for a in opts) and any(":" in o for o in operands))
        return "fetch with a forced refspec overwrites a local branch" if forced else None
    if sub == "worktree":
        if operands[:1] in (["remove"], ["rm"]):
            return "worktree remove deletes a checkout that may hold uncommitted work"
        return "worktree add -B resets an existing branch" if operands[:1] == ["add"] and "-B" in rest else None
    if sub == "tag":
        return "tag deletion (restore/* tags are this project's rollback points)" if any(
            lopt(a, "delete") or sopt(a, "d") for a in opts) else None
    if sub == "rm":
        if any(lopt(a, "cached") for a in opts):
            return None
        return "rm -f deletes files even with uncommitted changes" if any(
            lopt(a, "force") or sopt(a, "f") for a in opts) else None
    if sub == "update-ref":
        if any(a == "-d" or lopt(a, "delete") or lopt(a, "stdin") for a in opts) or any(
                o.startswith("refs/heads/") for o in operands):
            return "update-ref deletes or moves a branch ref"
        return None
    if sub == "read-tree":
        return "read-tree --reset -u overwrites the working tree" if (
            "-u" in rest and any(lopt(a, "reset") for a in opts)) else None
    if sub == "checkout-index":
        return "checkout-index -f overwrites working files" if any(
            lopt(a, "force") or sopt(a, "f") for a in opts) else None
    if sub == "apply":
        rev = any(lopt(a, "reverse") or sopt(a, "R") for a in opts)
        safe = any(lopt(a, n) for a in opts for n in ("check", "stat", "numstat", "summary", "cached"))
        return "apply -R reverts changes in the working tree" if rev and not safe else None
    if sub in {"filter-branch", "filter-repo"}:
        return f"{sub} rewrites history"
    if sub == "reflog" and operands[:1] in (["expire"], ["delete"]):
        return "reflog expire/delete removes the record needed to recover lost commits"
    if sub == "prune":
        return "prune deletes unreachable objects (the last copy of dropped work)"
    if sub == "gc" and any(a.startswith("--prune=now") or a == "--prune=all" for a in opts):
        return "gc --prune=now deletes unreachable objects immediately"
    if sub == "submodule" and operands[:1] == ["foreach"]:
        inner = rest[rest.index("foreach") + 1:]
        inner = [a for a in inner if a not in {"--recursive", "-q", "--quiet"}]
        return evaluate(inner[0] if len(inner) == 1 else shlex.join(inner), "bash", ctx, depth + 1)
    return None


# ------------------------------------------------------------------------------------------------ 4. per command
def _strip_prefix(cmd: "list[str]") -> "tuple[list[str], bool, bool, bool]":
    """Drop assignments, keywords and wrappers in front of the real command.
    Returns (rest, hatch_seen, via_xargs, env_alias_override)."""
    hatch = via_xargs = env_alias = False
    i = 0
    while i < len(cmd):
        t = cmd[i]
        if ASSIGN.match(t):
            hatch = hatch or t == f"{HATCH}=1"
            env_alias = env_alias or bool(re.match(r"^GIT_CONFIG_(KEY_\d+=alias\.|PARAMETERS=.*alias\.)", t, re.I))
            i += 1
        elif re.match(r"^\$[\w:.]+$", t) and i + 1 < len(cmd) and cmd[i + 1] == "=":       # PowerShell `$x = cmd`
            i += 2
        elif re.match(r"^\$[\w:.]+=$", t):                                                  # `$x= cmd`
            i += 1
        elif re.match(r"^\$[\w:.]+=.+$", t):                                                # `$x=cmd`
            cmd = cmd[:i] + [t.split("=", 1)[1]] + cmd[i + 1:]
        elif t in PREFIX_WORDS:
            i += 1
        elif t in OPT_WRAPPERS:
            via_xargs = via_xargs or t == "xargs"
            takes = OPT_WRAPPERS[t]
            i += 1
            while i < len(cmd) and (cmd[i].startswith("-") or ASSIGN.match(cmd[i])
                                    or (t == "timeout" and re.match(r"^\d", cmd[i]))):
                if ASSIGN.match(cmd[i]):
                    hatch = hatch or cmd[i] == f"{HATCH}=1"
                if cmd[i] in takes and i + 1 < len(cmd):
                    i += 1
                i += 1
            if t == "timeout" and i < len(cmd) and re.match(r"^\d", cmd[i]):
                i += 1
        else:
            break
    return cmd[i:], hatch, via_xargs, env_alias


def _shell_inner(head: str, cmd: "list[str]") -> "str | None":
    """The command text a shell wrapper will run, or None."""
    rest = cmd[1:]
    if head == "cmd":
        for j, t in enumerate(rest):
            if t.lower() in {"/c", "/k", "//c", "//k"}:
                return " ".join(rest[j + 1:])
        return None
    if head in {"pwsh", "powershell"}:
        value_opts = {"-executionpolicy", "-ep", "-version", "-windowstyle", "-outputformat", "-inputformat",
                      "-configurationname", "-workingdirectory", "-wd", "-settingsfile"}
        j = 0
        while j < len(rest):
            t = rest[j].lower()
            if t in {"-encodedcommand", "-ec", "-e"} and j + 1 < len(rest):
                try:
                    return base64.b64decode(rest[j + 1]).decode("utf-16-le")
                except (ValueError, UnicodeDecodeError):
                    return None
            if t.startswith("-comm") or t == "-c":
                return " ".join(rest[j + 1:])
            if t in {"-file", "-f"}:
                return None
            if t in value_opts:
                j += 2
                continue
            if t.startswith("-"):
                j += 1
                continue
            return " ".join(rest[j:])                      # positional: Windows PowerShell's -Command
        return None
    for j, t in enumerate(rest):                           # bash/sh/zsh: -c, or a bundle containing c (-lc, -ec)
        if t.startswith("-") and not t.startswith("--") and "c" in t[1:] and j + 1 < len(rest):
            return rest[j + 1]
    return None


def evaluate(text: str, shell: str, ctx: Ctx, depth: int = 0) -> "str | None":
    """The reason to block `text`, or None to allow it."""
    if depth > 4 or not text or not text.strip():
        return None
    cmds, scripts = commands(text, shell)
    for s in scripts:
        r = evaluate(s, "bash", ctx, depth + 1)
        if r:
            return r
    for cmd in cmds:
        for tok in cmd:
            for inner in substitutions(tok):
                r = evaluate(inner, shell, ctx, depth + 1)
                if r:
                    return r
        cmd, hatch, via_xargs, env_alias = _strip_prefix(cmd)
        if not cmd:
            continue
        head = re.split(r"[\\/]", cmd[0])[-1].lower()
        for ext in (".exe", ".cmd", ".bat"):
            head = head.removesuffix(ext)
        if head in {"cd", "pushd", "set-location", "sl", "chdir", "push-location"}:
            dest = next((a for a in cmd[1:] if not a.startswith("-")), None)
            if dest and dest not in {"~", "-"} and not dest.startswith("$"):
                ctx = ctx.with_cwd(dest)
            continue
        if via_xargs:
            cmd = cmd + [UNRESOLVED]      # xargs APPENDS operands from stdin
        if head in SHELLS:
            inner = _shell_inner(head, cmd)
            if inner is None and "<<<" in cmd and cmd.index("<<<") + 1 < len(cmd):     # `bash <<< 'git ...'`
                inner = cmd[cmd.index("<<<") + 1]
            if inner:
                r = evaluate(inner, "ps" if head in {"pwsh", "powershell"} else "bash", ctx, depth + 1)
                if r and not hatch:
                    return r
            continue
        if head == "find":
            for j, t in enumerate(cmd):
                if t in {"-exec", "-execdir", "-ok", "-okdir"}:
                    inner = [a for a in cmd[j + 1:] if a not in {"+", ";"}]
                    r = evaluate(shlex.join(inner), "bash", ctx, depth + 1)
                    if r:
                        return r
            continue
        if head != "git":
            continue
        r = git_reason(cmd[1:], ctx, depth, env_alias)
        if r and not hatch:
            return r
    return None


# ------------------------------------------------------------------------------------------------ the self-test table
class FakeCtx(Ctx):
    REFS = {"main", "master", "HEAD", "HEAD~1", "HEAD~5", "wt/restock", "wt/x", "wt/new", "wt/phase2.step0", "v1.0.rc1",
            "v0.1.5", "origin/main", "origin/wt/x.y", "wt/r20.1", "release/v1.2", "restore/pre-promote-2026-09-24"}
    PATHS = {"a.py", "x.py", "pokemon_league.py", "sandbox-pokebot", ".gitignore", "Makefile", "conflicted", "dir",
             "old.py", "list.txt", "..", ".", "sandbox-pokebot/modules", "sandbox-pokebot/modules/story",
             "sandbox-pokebot\\modules"}
    ALIASES = {"co": "checkout", "nuke": "!git reset --hard", "st": "status"}

    def __init__(self, cwd=None):
        super().__init__(None)
        self.rel = ""

    def with_cwd(self, d):
        c = copy.copy(self)
        c.rel = (self.rel + "/" + d).strip("/") if self.rel else d.strip("/")
        return c

    def is_ref(self, tok, c_dir):
        return tok in self.REFS

    def is_path(self, tok, c_dir):
        full = (self.rel + "/" + tok) if self.rel else tok
        return tok in self.PATHS or full.rstrip("/") in self.PATHS

    def alias(self, name, c_dir):
        return self.ALIASES.get(name)


G, H = "g" + "it", HATCH + "=1"
B, A = True, False
CASES: "list[tuple[str, bool, str]]" = [
    # --- BLOCK: the 2026-09-27 incident and its siblings ------------------------------------------------------------
    ("bash", B, f"{G} checkout -- sandbox-pokebot/modules/story/pokemon_league.py"),
    ("bash", B, f"cd /repo && {G} checkout -- a.py"),
    ("bash", B, f'{G} -C "C:/Remote Projects/pokebot-wt-ch24" checkout -- x.py'),
    ("bash", B, f"{G} checkout HEAD -- a.py"), ("bash", B, f"{G} checkout ."), ("bash", B, f"{G} checkout pokemon_league.py"),
    ("bash", B, f"{G} checkout -f main"), ("bash", B, f"{G} checkout --force main"), ("bash", B, f"{G} checkout --theirs a.py"),
    ("bash", B, f"{G} checkout --ours conflicted"), ("bash", B, f"{G} checkout sandbox-pokebot"),
    ("bash", B, f"{G} checkout sandbox-pokebot/"), ("bash", B, f"{G} checkout .."), ("bash", B, f"{G} checkout .gitignore"),
    ("bash", B, f"{G} checkout HEAD Makefile"), ("bash", B, f"{G} checkout --pathspec-from-file=list.txt"),
    ("bash", B, f"{G} checkout -B main"), ("bash", B, f"{G} checkout --fo main"),
    ("bash", B, f"{G} restore a.py"), ("bash", B, f"{G} restore --worktree --staged a.py"), ("bash", B, f"{G} restore -W a.py"),
    ("bash", B, f"{G} restore --source=HEAD~1 a.py"), ("bash", B, f"{G} restore --pathspec-from-file=list.txt"),
    ("bash", B, f"{G} restore --staged --wor a.py"), ("bash", B, f"{G} restore --staged --wo a.py"),
    ("bash", B, f"{G} restore --staged --no-staged a.py"),
    ("bash", B, f"{G} reset --hard"), ("bash", B, f"{G} reset --hard origin/main"), ("bash", B, f"{G} reset --merge"),
    ("bash", B, f"{G} reset --har"), ("bash", B, f"{G} reset --ha"), ("bash", B, f"{G} reset >/dev/null --hard"),
    ("bash", B, f"{G} stash"), ("bash", B, f"{G} stash -u"), ("bash", B, f"{G} stash push -m wip"), ("bash", B, f"{G} stash save x"),
    ("bash", B, f"{G} stash drop"), ("bash", B, f"{G} stash clear"), ("bash", B, f"{G} stash pop"), ("bash", B, f"{G} stash branch x"),
    ("bash", B, f"{G} clean -fd"), ("bash", B, f"{G} clean -xdf"), ("bash", B, f"{G} clean --force"), ("bash", B, f"{G} clean --forc -d"),
    ("bash", B, f"{G} clean --fo -d"), ("bash", B, f"{G} clean -n --no-dry-run -f"),
    ("bash", B, f"{G} switch --discard-changes main"), ("bash", B, f"{G} switch --discard main"), ("bash", B, f"{G} switch -f main"),
    ("bash", B, f"{G} switch -C main"), ("bash", B, f"{G} switch --di main"),
    ("bash", B, f"{G} branch -D wt/restock"), ("bash", B, f"{G} branch -d wt/restock"), ("bash", B, f"{G} branch --delete wt/x"),
    ("bash", B, f"{G} branch --del wt/x"), ("bash", B, f"{G} branch --de wt/x"), ("bash", B, f"{G} branch -M wt/a main"),
    ("bash", B, f"{G} branch -f main HEAD~5"),
    ("bash", B, f"{G} push --force origin main"), ("bash", B, f"{G} push -f"), ("bash", B, f"{G} push --force-with-lease origin main"),
    ("bash", B, f"{G} push --force-w origin main"), ("bash", B, f"{G} push origin +main"), ("bash", B, f"{G} push origin :wt/restock"),
    ("bash", B, f"{G} push origin --delete wt/restock"), ("bash", B, f"{G} push --del origin wt/x"),
    ("bash", B, f"{G} push origin HEAD:main --force"), ("bash", B, f"{G} push --mirror"),
    ("bash", B, f"{G} push --force-with-lease=main:abc origin main"), ("bash", B, f"{G} fetch origin +main:main"),
    ("bash", B, f"{G} worktree remove ../pokebot-wt-ch24"), ("bash", B, f"{G} worktree remove --force ../x"),
    ("bash", B, f"{G} rm -f a.py"), ("bash", B, f"{G} rm -rf dir"),
    ("bash", B, f"{G} update-ref -d refs/heads/wt/x"), ("bash", B, f"{G} update-ref --stdin"),
    ("bash", B, f"{G} update-ref refs/heads/main HEAD~3"), ("bash", B, f"{G} read-tree --reset -u HEAD"),
    ("bash", B, f"{G} checkout-index -a -f"), ("bash", B, f"{G} filter-branch --tree-filter x HEAD"),
    ("bash", B, f"{G} reflog expire --expire=now --all"), ("bash", B, f"{G} prune"), ("bash", B, f"{G} gc --prune=now"),
    ("bash", B, f"{G} diff -- a.py | {G} apply -R"), ("bash", B, f"{G} apply --reverse fix.patch"),
    ("bash", B, f"{G} submodule foreach {G} reset --hard"), ("bash", B, f"{G} submodule foreach '{G} stash'"),
    # --- BLOCK: git not the first word ----------------------------------------------------------------------------------
    ("bash", B, f"{G} status; {G} checkout -- a.py"), ("bash", B, f"echo ok && {G} reset --hard"),
    ("bash", B, f"false && {G} -C /x stash drop"), ("bash", B, f"OTHER=1 {G} reset --hard"),
    ("bash", B, f"echo $({G} reset --hard)"), ("bash", B, f"$({G} stash)"), ("bash", B, f"`{G} reset --hard`"),
    ("bash", B, f"({G} reset --hard)"), ("bash", B, f"{{ {G} reset --hard; }}"), ("bash", B, f"! {G} stash"),
    ("bash", B, f"env {G} reset --hard"), ("bash", B, f"command {G} reset --hard"), ("bash", B, f"command -p {G} reset --hard"),
    ("bash", B, f"bash -c '{G} reset --hard'"), ("bash", B, f"bash -lc '{G} reset --hard'"), ("bash", B, f"sh -ec '{G} stash drop'"),
    ("bash", B, f"if true; then {G} reset --hard; fi"), ("bash", B, f"for f in a.py; do {G} checkout -- $f; done"),
    ("bash", B, f'for f in a.py b.py; do {G} checkout "$f"; done'),
    ("bash", B, f"echo a.py | xargs {G} checkout --"), ("bash", B, f"{G} diff --name-only | xargs {G} checkout"),
    ("bash", B, f"ls | xargs {G} rm -f"), ("bash", B, f"ls | xargs --max-args 1 {G} checkout"), ("bash", B, f"'{G}' reset --hard"),
    ("bash", B, f'"C:/Program Files/Git/cmd/{G}.exe" reset --hard'), ("bash", B, f"{G}.cmd reset --hard"),
    ("bash", B, f"nohup {G} stash &"), ("bash", B, f"timeout 30 {G} reset --hard"), ("bash", B, f"nice -n 5 {G} reset --hard"),
    ("bash", B, f"stdbuf -oL {G} reset --hard"), ("bash", B, f"winpty {G} reset --hard"),
    ("bash", B, f"{G} status;\n{G} reset --hard"), ("bash", B, f"{G} status\n\n\n{G} stash drop"),
    ("bash", B, f'echo "$({G} reset --hard)"'), ("bash", B, f'r="$({G} stash pop)"'), ("bash", B, f'echo "`{G} reset --hard`"'),
    ("bash", B, f"cat <({G} reset --hard)"), ("bash", B, f"cmd //c {G} reset --hard"),
    ("bash", B, f"find . -name '*.py' -exec {G} checkout -- {{}} +"), ("bash", B, f"cd sandbox-pokebot && {G} checkout modules"),
    ("bash", B, f"cd sandbox-pokebot && {G} checkout modules/story"),
    # --- BLOCK: comments, continuations, heredocs --------------------------------------------------------------------------
    ("bash", B, f"# don't touch\n{G} reset --hard"), ("bash", B, f"{G} status  # check first\n{G} reset --hard"),
    ("bash", B, f"cd /x  # go to repo\n{G} reset --hard"), ("bash", B, f"echo ok#1 && {G} reset --hard"),
    ("bash", B, f"[ $# -eq 0 ] && {G} reset --hard"), ("bash", B, f"{G} reset \\\n  --hard"),
    ("bash", B, f"{G} -C /x \\\n  reset --hard"), ("bash", B, f"{G} push \\\n  --force-with-lease origin main"),
    ("bash", B, f'grep x <<< "$v"; {G} reset --hard'), ("bash", B, f"cat <<< EOF; {G} stash"), ("bash", B, f'MSG="a b" {G} reset --hard'),
    ("bash", B, f"{G} reset --hard>/dev/null"), ("bash", B, f"{G} stash>/dev/null"), ("bash", B, f"{G} push --force>/dev/null"),
    ("bash", B, f"cat > m.txt <<'EOF'\nharmless\nEOF\n{G} reset --hard"),
    ("bash", B, f"# write the message with a heredoc (<<EOF)\n{G} reset --hard"),
    ("bash", B, f'{G} commit -m "fix <<EOF parsing"\n{G} push --force'), ("bash", B, f'py -c "print(1 << bits)"\n{G} reset --hard'),
    ("bash", B, f"cat <<END-MSG\nhi\nEND-MSG\n{G} reset --hard"), ("bash", B, f"bash <<'EOF'\n{G} reset --hard\nEOF"),
    # --- BLOCK: config overrides and aliases -------------------------------------------------------------------------------
    ("bash", B, f"{G} -c alias.x=reset x --hard"), ("bash", B, f"{G} -c 'alias.x=!{G} stash' x"),
    ("bash", B, f"{G} --no-advice reset --hard"), ("bash", B, f"{G} --no-lazy-fetch stash"),
    ("bash", B, f"{G} --attr-source=HEAD reset --hard"), ("bash", B, f"{G} -c clean.requireForce=false clean -dx"),
    ("bash", B, f"{G} -c remote.origin.mirror=true push origin"), ("bash", B, f"{G} co -- a.py"), ("bash", B, f"{G} nuke"),
    ("bash", B, f"{G} --config-env=alias.x=V x --hard"), ("bash", B, f"GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=alias.x GIT_CONFIG_VALUE_0=reset {G} x --hard"),
    # --- BLOCK: PowerShell ------------------------------------------------------------------------------------------------
    ("ps", B, f"{G} reset --hard"), ("ps", B, f'& "C:/Program Files/Git/cmd/{G}.exe" reset --hard'),
    ("ps", B, f"& {{ {G} reset --hard }}"), ("ps", B, f"if ($true) {{ {G} reset --hard }}"), ("ps", B, f"cmd /c {G} reset --hard"),
    ("ps", B, f"{G} --% reset --hard"), ("ps", B, f"$m = @'\nit's fine\n'@\n{G} reset --hard"),
    ("ps", B, f'Write-Output "a`"b"; {G} reset --hard'), ("ps", B, f"{G} status\r{G} reset --hard"),
    ("ps", B, f'powershell -Command "{G} stash drop"'), ("ps", B, f"powershell -Command {G} reset --hard"),
    ("ps", B, f'powershell -NoProfile "{G} reset --hard"'), ("bash", B, f"powershell -Comm '{G} reset --hard'"),
    ("ps", B, f"{G} status # x\n{G} reset --hard"), ("ps", B, f"{G} checkout sandbox-pokebot\\modules"),
    ("ps", B, f"$null = {G} reset --hard"), ("ps", B, f"$out = {G} stash pop"), ("ps", B, f"$o={G} reset --hard"),
    ("ps", B, f'Write-Output "$({G} reset --hard)"'), ("ps", B, f"# @'\n{G} reset --hard\n'@ | Out-Null"),
    ("ps", B, f'Write-Output "<#"; {G} reset --hard; Write-Output "#>"'),
    ("ps", B, f'{G} -C "C:\\Remote Projects\\Pokebot_Gen3_Enhancement\\" reset --hard'),
    # the v3 confirmation review: PowerShell script blocks, Push-Location, a parenthesised operand
    ("ps", B, f"{G} diff --name-only | ForEach-Object {{ {G} checkout -- $_ }}"), ("ps", B, f"$fs | % {{ {G} restore $_ }}"),
    ("ps", B, f"$files | foreach {{ {G} checkout $_ }}"), ("ps", B, f"ForEach-Object -Process {{ {G} reset --hard }}"),
    ("ps", B, f"try {{ {G} reset --hard }} catch {{ }}"), ("ps", B, f"try {{ {G} status }} catch {{ {G} stash }}"),
    ("ps", B, f"foreach ($f in $files) {{{G} checkout -- $f}}"), ("ps", B, f"if ({G} status --porcelain) {{{G} stash}}"),
    ("ps", B, f"Invoke-Command {{ {G} reset --hard }}"), ("ps", B, f"Start-Job {{ {G} stash drop }}"),
    ("ps", B, f"Push-Location sandbox-pokebot; {G} checkout modules"), ("ps", B, f"{G} checkout -- ({G} diff --name-only)"),
    ("ps", B, f"{G} restore ({G} diff --name-only)"), ("bash", B, f"bash <<< '{G} reset --hard'"),
    ("bash", B, f"{G} tag -d restore/pre-promote-2026-09-24"), ("bash", B, f"{G} fetch -f origin main:main"),
    ("bash", B, f"{G} worktree add -B wt/x ../wt"),
    # --- BLOCK: the hatch cannot be spoofed ----------------------------------------------------------------------------------
    ("bash", B, f'echo "{H}" && {G} reset --hard'), ("bash", B, f"# {H}\n{G} reset --hard"),
    ("ps", B, f'<#\n$env:{HATCH} = "1"\n#>\n{G} reset --hard'), ("ps", B, f'if ($false) {{\n$env:{HATCH} = "1"\n}}\n{G} reset --hard'),
    ("bash", B, f"{H} echo x; {G} reset --hard"), ("bash", B, f"export {H}; {G} reset --hard"),
    ("bash", B, f"{H}  # user approved\n{G} reset --hard"), ("bash", B, f"{H} true && {G} reset --hard"),
    # --- ALLOW: ordinary work -----------------------------------------------------------------------------------------------
    ("bash", A, f"{G} checkout main"), ("bash", A, f"{G} checkout wt/restock"), ("bash", A, f"{G} checkout -b wt/new-item"),
    ("bash", A, f"{G} checkout -b feature.md"), ("bash", A, f"{G} checkout v0.1.5"), ("bash", A, f"{G} checkout -b wt/x.y origin/wt/x.y"),
    ("bash", A, f"{G} checkout wt/phase2.step0"), ("bash", A, f"{G} checkout v1.0.rc1"), ("bash", A, f"{G} checkout wt/r20.1"),
    ("bash", A, f"{G} checkout restore/pre-promote-2026-09-24"), ("bash", A, f"{G} checkout -- "), ("bash", A, f"{G} checkout -"),
    ("bash", A, f"{G} checkout main 2>&1"), ("bash", A, f"{G} checkout main 2>/dev/null"), ("bash", A, f"{G} checkout main 2> err.txt"),
    ("bash", A, f"{G} checkout main &>/dev/null"), ("bash", A, f"{G} checkout wt/restock 2>&1 && {G} log --oneline -1"),
    ("bash", A, f"{G} checkout main 2>&1 | tail -2"), ("ps", A, f"{G} checkout main 2>$null"), ("ps", A, f"{G} checkout main *>$null"),
    ("bash", A, f"{G} checkout main   # go back to main\n{G} pull --ff-only"),
    ("bash", A, f"{G} checkout wt/restock  # the restock branch\n{G} log --oneline -3"),
    ("bash", A, f"{G} switch main"), ("bash", A, f"{G} switch -c wt/new-item"), ("bash", A, f"{G} switch -c x.y"),
    ("bash", A, f"{G} restore --staged a.py"), ("bash", A, f"{G} restore -S a.py"), ("bash", A, f"{G} restore -s HEAD~1 --staged a.py"),
    ("bash", A, f"{G} reset a.py"), ("bash", A, f"{G} reset --soft HEAD~1"), ("bash", A, f"{G} reset HEAD a.py"), ("bash", A, f"{G} reset --mixed"),
    ("bash", A, f"{G} stash list"), ("bash", A, f"{G} stash show -p stash@{{0}}"), ("bash", A, f"{G} stash apply"), ("bash", A, f"{G} stash -h"),
    ("bash", A, f"{G} clean -n"), ("bash", A, f"{G} clean --dry-run -d"), ("bash", A, f"{G} clean -nfd"),
    ("bash", A, f"{G} branch wt/new"), ("bash", A, f"{G} branch -a"), ("bash", A, f"{G} branch --show-current"),
    ("bash", A, f"{G} branch -m old new"), ("bash", A, f"{G} branch --list"), ("bash", A, f"{G} branch -vv"),
    ("bash", A, f"{G} push -u origin wt/new"), ("bash", A, f"{G} push origin main"), ("bash", A, f"{G} push -q origin main 2>&1 | tail -1"),
    ("bash", A, f"{G} push --tags"), ("bash", A, f"{G} push --dry-run origin main"), ("bash", A, f"{G} push origin HEAD:wt/x"),
    ("bash", A, f"{G} push --follow-tags origin main"), ("bash", A, f"{G} fetch -q origin"), ("bash", A, f"{G} fetch upstream-pokebot"),
    ("bash", A, f"{G} worktree add ../wt -b wt/x"), ("bash", A, f"{G} worktree list"), ("bash", A, f"{G} worktree prune"),
    ("bash", A, f"{G} rm --cached a.py"), ("bash", A, f"{G} rm old.py"), ("bash", A, f"{G} rm -rf --cached sandbox-pokebot/logs"),
    ("bash", A, f"{G} rm -r --cached dir"), ("bash", A, f"{G} apply fix.patch"), ("bash", A, f"{G} apply -R --check fix.patch"),
    ("bash", A, f"{G} diff -- a.py"), ("bash", A, f"{G} diff HEAD -- a.py"), ("bash", A, f"{G} log --oneline -- a.py"),
    ("bash", A, f"{G} show HEAD:a.py"), ("bash", A, f"{G} merge --ff-only origin/wt/swapevo"), ("bash", A, f"{G} status --short"),
    ("bash", A, f'{G} -C "C:/Remote Projects/pokebot-wt-ch24" status --short'), ("bash", A, f"{G} gc"), ("bash", A, f"{G} reflog"),
    ("bash", A, f"{G} st"), ("bash", A, f"ls | xargs {G} add"), ("bash", A, f"ls | xargs {G} restore --staged"),
    ("bash", A, f"{G} log --oneline -3 2>&1 | tail -1"), ("bash", A, f"{G} subtree pull --prefix=x upstream main --squash"),
    ("bash", A, f"for f in a.py b.py; do {G} log --oneline -- $f; done"), ("bash", A, f"for f in *.py; do {G} diff -- \"$f\"; done"),
    ("bash", A, f"find . -name '*.py' -exec {G} log -1 -- {{}} \\;"), ("bash", A, f"cd sandbox-pokebot && {G} status --short"),
    ("bash", A, f"bash -c '{G} status'"), ("ps", A, f"$s = {G} status --short"), ("ps", A, f"cd sandbox-pokebot; {G} log -1"),
    ("bash", A, f"issue#27 && {G} status"), ("ps", A, f"{G} stash show -p stash@{{0}}"), ("ps", A, f"{G} checkout @{{-1}}"),
    ("ps", A, f"try {{ {G} status }} catch {{ Write-Output $_ }}"), ("ps", A, f"$fs | ForEach-Object {{ {G} log -1 -- $_ }}"),
    ("ps", A, f"{G} diff --name-only | ForEach-Object {{ {G} add $_ }}"), ("bash", A, f"{G} tag -a v1 -m x"),
    ("bash", A, f"{G} tag --list"), ("bash", A, f"{G} fetch origin main"), ("bash", A, f"bash <<< '{G} status'"),
    ("bash", A, f"{G} worktree add ../wt -b wt/x"), ("bash", A, f"cat <<\\EOF > n.md\n{G} stash drop is refused\nEOF"),
    ("bash", A, f"cat > notes.md << 'END-OF-NOTES'\n...{G} stash drop is refused.\nEND-OF-NOTES"),
    # --- ALLOW: MENTIONS ---------------------------------------------------------------------------------------------------
    ("bash", A, f'echo "{G} checkout -- a.py"'), ("bash", A, f'grep -n "{G} reset --hard" CLAUDE.md'),
    ("bash", A, f'{G} commit -m "never run {G} checkout -- on uncommitted work"'),
    ("bash", A, f"cat > m.txt <<'EOF'\nrule: never {G} reset --hard\nEOF"),
    ("bash", A, f"{G} commit -F - <<'EOF'\nfix: x\n\n{G} stash drop was never run\nEOF"),
    ("bash", A, f'echo "12\\" record; {G} stash drop \\" ok"'), ("bash", A, f"# {G} reset --hard\necho hi"),
    ("bash", A, f"python - <<'EOF'\nimport subprocess\nsubprocess.run(['{G}', 'status'])\nprint('{G} reset --hard')\nEOF"),
    ("ps", A, f"{G} commit -m @'\nfix: block destructive git\n\nThe reviewer's revert used the wrong command.\n{G} checkout -- a.py deleted the fix.\n'@"),
    ("ps", A, f'{G} commit -m @"\nfix: the 12" rule\n{G} stash drop is refused\n"@'),
    ("ps", A, f'{G} commit -m "the 12`" rule; {G} stash drop is refused"'),
    ("ps", A, f"<# {G} reset --hard #>\n{G} status"),
    # --- ALLOW: the deliberate, user-approved hatch ------------------------------------------------------------------------
    ("bash", A, f"{H} {G} branch -D wt/restock"), ("bash", A, f"cd /repo && {H} {G} worktree remove ../x"),
    ("bash", A, f"env {H} {G} reset --hard"),
]


def run_selftest(decide=None) -> int:
    decide = decide or (lambda text, shell: evaluate(text, shell, FakeCtx(None)))
    fails = 0
    for shell, want, cmd in CASES:
        got = bool(decide(cmd, shell))
        if got != want:
            fails += 1
            print(f"  FAIL  want={'BLOCK' if want else 'ALLOW'} got={'BLOCK' if got else 'ALLOW'}  [{shell}] {cmd!r}")
    if fails:
        print(f"  {fails} of {len(CASES)} cases FAILED")
        return 1
    print(f"  OK  block_destructive_git.py: {len(CASES)}/{len(CASES)} cases (incident, both reviews' realistic and "
          f"exotic bypasses, false positives, mentions, the live hatch)")
    return 0


# ------------------------------------------------------------------------------------------------ hook entry point
REASON = """BLOCKED: a git command that can silently discard work - {why}.

On 2026-09-27 a reviewer agent "reverted" a test mutation with 'git checkout -- <file>' while the fix under review
was UNCOMMITTED, and deleted the fix. CLAUDE.md: ask before any destructive git operation; never force-push; never
discard local work.

Do this instead:
  * to undo a test mutation: mutate a COPY (a temp file or an exec'd string), never the file itself;
  * to protect work before a review: COMMIT it (a WIP commit on the branch) first;
  * to change branch: 'git switch <branch>' (it refuses to overwrite local changes);
  * to unstage: 'git restore --staged <path>'.

If the USER approved this exact operation, put POKEBOT_ALLOW_DESTRUCTIVE_GIT=1 in front of the git command
itself, so the choice is deliberate and visible."""


def main() -> int:
    if "--selftest" in sys.argv:
        return run_selftest()
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        cmd = str((payload.get("tool_input") or {}).get("command") or "")
        if not cmd or os.environ.get(HATCH) == "1":
            return 0
        shell = "ps" if str(payload.get("tool_name", "")).lower() == "powershell" else "bash"
        why = evaluate(cmd, shell, Ctx(payload.get("cwd")))
        if why:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                     "permissionDecisionReason": REASON.format(why=why)}}))
    except Exception:  # noqa: BLE001 - fail OPEN: a hook that errors must never block the session
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
