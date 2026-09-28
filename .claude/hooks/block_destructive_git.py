r"""PreToolUse(Bash|PowerShell) hook - REFUSE git commands that can silently DISCARD work.

WHY (2026-09-27, `08-MISTAKES.md`): a reviewer agent "reverted" a test mutation with `git checkout -- <file>` while the
fix under review was UNCOMMITTED, and deleted the fix. CLAUDE.md already said: never discard local work, ask before any
destructive git operation or branch deletion, never force-push. The user approved enforcing it (2026-09-28).

WHY PYTHON, NOT POWERSHELL (the 2026-09-28 review of the first, PowerShell draft): hand-parsing shell text in PowerShell
missed comments (`# don't` opened a "quote" and hid every later line), escapes, here-strings, `$(...)`, `for ... do`,
attached redirections and more: 49 of 79 adversarial probes got through. And its deny output was NOT VALID JSON (a
BOM-less .ps1 is read as Windows-1252 by PowerShell 5.1, which mangled the reason's non-ASCII characters), so it could
never have blocked anything. Here `shlex` does the lexing (quotes, escapes, comments, ; && || | ( ) < >), a small
pre-pass removes heredoc bodies (bash) and here-strings / block comments (PowerShell), and `json.dumps` writes ASCII.
This file is ASCII-only on purpose.

WHAT IT BLOCKS - any git command that can discard uncommitted work, published history or a branch:
  checkout: `--` paths | a path operand | a path after a tree-ish | -f/--force/--ours/--theirs/-p | -B (resets a branch)
  restore (unless --staged without --worktree) | reset --hard/--merge | stash (not list/show/apply/create/store/-h)
  clean with force (not with -n/--dry-run) | switch --discard-changes/-f/-C | branch -d/-D/-f/-M/-C/--delete
  push --force/-f/--force-with-lease/--force-if-includes/--mirror/--delete/-d/--prune, a `+refspec`, a `:ref` delete
  worktree remove | rm -f (not with --cached) | update-ref -d | read-tree --reset -u | checkout-index -f
  filter-branch | filter-repo | reflog expire/delete | prune | gc --prune=now
  `-c alias.*`, `-c clean.requireForce`, `-c remote.*.mirror/push` (a config override can change what a command does)
Long options match by unique prefix (`--har` is `--hard`), as git itself accepts. Git aliases are expanded.
It finds git after command prefixes (env, command, xargs, sudo, nohup, time, timeout, `&`, then/do/else, `!`, `$(`,
backticks, `( )`, `{ }`) and inside `bash -c` / `sh -c` / `cmd /c` / `powershell -Command` strings.

WHAT IT ALLOWS: branch switching (`git checkout <existing ref>` is resolved against the repo, so `wt/phase2.step0` is a
branch, not a file), `checkout -b`, `restore --staged`, `reset <path>`/`--soft`/`--mixed`, `stash list/show/apply`,
`clean -n`, `rm --cached`, ordinary push, and every MENTION (quoted text, heredoc bodies, comments, commit messages).

ESCAPE HATCH, ONLY for an operation the USER approved: a live `POKEBOT_ALLOW_DESTRUCTIVE_GIT=1` assignment in front of
the git command itself (`POKEBOT_ALLOW_DESTRUCTIVE_GIT=1 git branch -D x`), or the variable set in Claude Code's own
environment. A mention in a comment, a string, or another statement does not count.

KNOWN LIMITS (not parsed; an agent on autopilot does not write these): PowerShell splatting (`git @a`), variables used
as the subcommand (`git $cmd`), `eval`, and git aliases defined in a different repo than the hook's cwd.

Contract: tool call JSON on stdin; exit 0 always (fails OPEN on any internal error: a hook that blocks everything is
worse than the bug); print a JSON "deny" to block. `--selftest` runs the case table and exits 1 on any failure.
Gate: `tools/story-dev/selftest_destructive_git_hook.py`.
"""
from __future__ import annotations

import base64
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

HATCH = "POKEBOT_ALLOW_DESTRUCTIVE_GIT"
SEPS = {";", "&", "&&", "|", "||", "|&", ";;", "(", ")", "\n", "{", "}"}
REDIRECT = re.compile(r"^\d*[<>]")
ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
PREFIX_WORDS = {"then", "do", "else", "elif", "if", "while", "until", "!", "time", "exec", "nohup", "command",
                "builtin", "sudo", "&", ".", "call", "nice", "stdbuf", "$", "eval"}
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


# ------------------------------------------------------------------------------------------------ context (injectable)
class Ctx:
    """How the hook asks the repo whether a token is a ref, a path, or an alias. The self-test swaps in tables."""

    def __init__(self, cwd: str | None):
        self.cwd = Path(cwd) if cwd else Path.cwd()

    def _git(self, base: Path, *args: str) -> "subprocess.CompletedProcess | None":
        try:
            return subprocess.run(["git", "-C", str(base), *args], capture_output=True, text=True, timeout=3)
        except (OSError, subprocess.SubprocessError):
            return None

    def base(self, c_dir: str | None) -> Path:
        if not c_dir:
            return self.cwd
        p = Path(c_dir)
        return p if p.is_absolute() else self.cwd / p

    def is_ref(self, tok: str, c_dir: str | None) -> bool:
        b = self.base(c_dir)
        r = self._git(b, "rev-parse", "--verify", "--quiet", f"{tok}^{{commit}}")
        if r is not None and r.returncode == 0:
            return True
        r = self._git(b, "for-each-ref", "--count=1", "--format=%(refname)", f"refs/heads/{tok}", f"refs/tags/{tok}",
                      f"refs/remotes/*/{tok}")
        return bool(r is not None and r.returncode == 0 and r.stdout.strip())

    def is_path(self, tok: str, c_dir: str | None) -> bool:
        try:
            return (self.base(c_dir) / tok).exists()
        except (OSError, ValueError):
            return False

    def alias(self, name: str, c_dir: str | None) -> str | None:
        r = self._git(self.base(c_dir), "config", "--get", f"alias.{name}")
        return r.stdout.strip() if r is not None and r.returncode == 0 and r.stdout.strip() else None


# ------------------------------------------------------------------------------------------------ pre-pass + lexing
_HEREDOC = re.compile(r"(?<!<)<<(-?)[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")


def strip_heredocs(text: str) -> str:
    """Blank every heredoc BODY (bash). `<<<` is a here-string, not a heredoc."""
    out, pending = [], []
    for line in text.split("\n"):
        if pending:
            tag, dash = pending[0]
            if (line.lstrip("\t") if dash else line).rstrip("\r") == tag:
                pending.pop(0)
            out.append("")
            continue
        out.append(line)
        for m in _HEREDOC.finditer(line):
            if m.end() < len(line) and line[m.end() - 1 + 1:m.end() + 1] == "<":
                continue
            pending.append((m.group(3), m.group(1) == "-"))
    return "\n".join(out)


def ps_prepass(text: str) -> str:
    """PowerShell: here-strings -> a token, block comments -> space, backtick escapes -> their character, CR -> newline."""
    text = re.sub(r"@(['\"])[ \t]*\r?\n.*?\r?\n\1@", " 'HERESTRING' ", text, flags=re.S)
    text = re.sub(r"<#.*?#>", " ", text, flags=re.S)
    text = re.sub(r"`\r?\n", " ", text)
    text = text.replace('`"', '\\"').replace("`'", "\\'")
    text = re.sub(r"`(.)", r"\1", text)
    return text.replace("\r", "\n")


def lex(text: str) -> list[str]:
    lx = shlex.shlex(text, posix=True, punctuation_chars=";&|()<>\n")
    lx.whitespace = " \t\r"
    lx.whitespace_split = True
    lx.commenters = "#"
    return list(lx)


def commands(text: str, shell: str) -> list[list[str]]:
    """Split a tool command into simple commands (token lists)."""
    text = ps_prepass(text) if shell == "ps" else strip_heredocs(text).replace("`", " ; ")
    for attempt in (text, text + '"', text + "'"):
        try:
            toks = lex(attempt)
            break
        except ValueError:
            continue
    else:
        return []          # unbalanced beyond repair: the shell will refuse to run it too
    out, cur = [], []
    for t in toks:
        # shlex GROUPS adjacent punctuation (three newlines are ONE token '\n\n\n'; `;` + newline is ';\n'), so a
        # separator is any token made only of these characters. `<`/`>` are excluded: `>&` is a redirection.
        if t in {"{", "}"} or (t and set(t) <= set(";&|()\n")):
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        out.append(cur)
    return out


# ------------------------------------------------------------------------------------------------ option helpers
def lopt(a: str, name: str, minlen: int = 3) -> bool:
    """`a` is the long option `--name` or a unique-enough prefix of it (git accepts prefixes)."""
    if not a.startswith("--") or a == "--":
        return False
    k = a[2:].split("=", 1)[0]
    return len(k) >= min(minlen, len(name)) and name.startswith(k)


def sopt(a: str, letters: str) -> bool:
    """`a` is a short-option bundle (`-fd`) containing any of `letters` (case-sensitive)."""
    return a.startswith("-") and not a.startswith("--") and len(a) > 1 and any(c in a[1:] for c in letters)


def looks_like_path(t: str) -> bool:
    if t in {".", "./", ".\\", "..", "*", "**", ":/"} or t.startswith(":(") or t.endswith(("/", "\\")):
        return True
    return bool(re.match(r"^\.[A-Za-z]", t) or re.search(r"\.[A-Za-z][A-Za-z0-9_-]{0,9}$", t))


# ------------------------------------------------------------------------------------------------ the decision
def git_reason(args: list[str], ctx: Ctx, depth: int) -> str | None:
    i, c_dir = 0, None
    while i < len(args) and args[i].startswith("-") and args[i] != "--":
        a = args[i]
        if a == "-c" and i + 1 < len(args):
            key = args[i + 1].split("=", 1)[0].lower()
            if key.startswith("alias.") or key == "clean.requireforce" or re.match(r"remote\..*\.(mirror|push)$", key):
                return f"a -c {key} override can change what a git command does"
        if a == "-C" and i + 1 < len(args):
            c_dir = args[i + 1]
        i += 2 if a in GIT_GLOBAL_WITH_VALUE else 1
    if i >= len(args):
        return None
    sub, rest = args[i].lower(), []
    for t in args[i + 1:]:
        if REDIRECT.match(t):
            break
        rest.append(t)
    opts = [a for a in rest if a.startswith("-") and a != "--"]
    operands = [a for a in rest if not a.startswith("-")]

    if sub not in GIT_BUILTINS and depth < 3:
        exp = ctx.alias(sub, c_dir)
        if exp:
            if exp.startswith("!"):
                return evaluate(exp[1:] + " " + " ".join(rest), "bash", ctx, depth + 1)
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
        if ctx.is_ref(ops[0], c_dir):
            return "checkout of paths after a tree-ish discards their uncommitted changes" if ops[1:] else None
        if ctx.is_path(ops[0], c_dir) or looks_like_path(ops[0]):
            return f"checkout of a path ('{ops[0]}') discards its uncommitted changes"
        return None
    if sub == "restore":
        staged = any(lopt(a, "staged") or sopt(a, "S") for a in opts)
        worktree = any(lopt(a, "worktree") or sopt(a, "W") for a in opts)
        paths = operands or any(lopt(a, "pathspec-from-file") for a in opts)
        if paths and (not staged or worktree):
            return "restore of working-tree files discards their uncommitted changes (use --staged to only unstage)"
        return None
    if sub == "reset":
        return "reset --hard/--merge discards uncommitted changes" if any(
            lopt(a, "hard") or lopt(a, "merge") for a in opts) else None
    if sub == "stash":
        if any(a in {"-h", "--help"} for a in opts):
            return None
        verb = operands[0].lower() if operands else "push"
        return None if verb in {"list", "show", "apply", "create", "store"} else f"stash {verb} hides or drops work"
    if sub == "clean":
        force = any(lopt(a, "force") or sopt(a, "f") for a in opts)
        dry = any(lopt(a, "dry-run") or sopt(a, "n") for a in opts)
        return "clean -f deletes untracked files (use -n for a dry run)" if force and not dry else None
    if sub == "switch":
        if any(lopt(a, "discard-changes") or lopt(a, "force") or sopt(a, "fC") or lopt(a, "force-create") for a in opts):
            return "switch --discard-changes/--force/-C discards changes or resets a branch"
        return None
    if sub == "branch":
        if any(lopt(a, "delete") or lopt(a, "force") or sopt(a, "dDfMC") for a in opts):
            return "branch deletion or forced move/rename/copy (CLAUDE.md: ask the user first)"
        return None
    if sub == "push":
        for a in rest:
            if any(lopt(a, n) for n in ("force", "force-with-lease", "force-if-includes", "mirror", "delete", "prune")) \
                    or sopt(a, "fd"):
                return f"push {a} (CLAUDE.md: never force-push, never rewrite published history)"
            if not a.startswith("-") and (a.startswith("+") or (a.startswith(":") and len(a) > 1)):
                return f"push refspec '{a}' forces or deletes a remote ref"
        return None
    if sub == "worktree":
        return "worktree remove deletes a checkout that may hold uncommitted work" if operands[:1] in (
            ["remove"], ["rm"]) else None
    if sub == "rm":
        if any(lopt(a, "cached") for a in opts):
            return None
        return "rm -f deletes files even with uncommitted changes" if any(
            lopt(a, "force") or sopt(a, "f") for a in opts) else None
    if sub == "update-ref":
        return "update-ref -d deletes a ref" if any(a == "-d" or lopt(a, "delete") for a in opts) else None
    if sub == "read-tree":
        return "read-tree --reset -u overwrites the working tree" if (
            "-u" in rest and any(lopt(a, "reset") for a in opts)) else None
    if sub == "checkout-index":
        return "checkout-index -f overwrites working files" if any(
            lopt(a, "force") or sopt(a, "f") for a in opts) else None
    if sub in {"filter-branch", "filter-repo"}:
        return f"{sub} rewrites history"
    if sub == "reflog" and operands[:1] in (["expire"], ["delete"]):
        return "reflog expire/delete removes the record needed to recover lost commits"
    if sub == "prune":
        return "prune deletes unreachable objects (the last copy of dropped work)"
    if sub == "gc" and any(a.startswith("--prune=now") or a == "--prune=all" for a in opts):
        return "gc --prune=now deletes unreachable objects immediately"
    return None


def _strip_prefix(cmd: list[str]) -> tuple[list[str], bool, bool]:
    """Drop assignments, keywords and wrapper commands in front of the real command.
    Returns (rest, hatch_seen, via_xargs): xargs APPENDS operands from stdin, so `xargs git checkout --` has paths."""
    hatch, i, via_xargs = False, 0, False
    while i < len(cmd):
        t = cmd[i]
        if ASSIGN.match(t):
            hatch = hatch or t == f"{HATCH}=1"
            i += 1
        elif t in PREFIX_WORDS:
            i += 1
        elif t in {"env", "xargs", "timeout"}:
            via_xargs = via_xargs or t == "xargs"
            i += 1
            while i < len(cmd) and (cmd[i].startswith("-") or ASSIGN.match(cmd[i])
                                    or (t == "timeout" and re.match(r"^\d", cmd[i]))):
                if ASSIGN.match(cmd[i]):
                    hatch = hatch or cmd[i] == f"{HATCH}=1"
                if cmd[i] in {"-I", "-L", "-n", "-P", "-d", "-E", "-s", "-a", "-u", "-k", "-s"} and i + 1 < len(cmd):
                    i += 1
                i += 1
        else:
            break
    return cmd[i:], hatch, via_xargs


def evaluate(text: str, shell: str, ctx: Ctx, depth: int = 0) -> str | None:
    """The reason to block `text`, or None to allow it."""
    if depth > 3 or not text or not text.strip():
        return None
    for cmd in commands(text, shell):
        cmd, hatch, via_xargs = _strip_prefix(cmd)
        if not cmd:
            continue
        if via_xargs:
            cmd = cmd + ["XARGS_OPERAND"]   # stands for what xargs appends from stdin
        head = re.split(r"[\\/]", cmd[0])[-1].lower()
        head = head[:-4] if head.endswith(".exe") else head
        if head in SHELLS:
            flags = {"-c", "-command", "/c", "/k", "-encodedcommand", "-ec"}
            for j, t in enumerate(cmd[1:], start=1):
                if t.lower() in flags and j + 1 < len(cmd):
                    inner = cmd[j + 1]
                    if t.lower() in {"-encodedcommand", "-ec"}:
                        try:
                            inner = base64.b64decode(inner).decode("utf-16-le")
                        except (ValueError, UnicodeDecodeError):
                            inner = ""
                    if t.lower() in {"/c", "/k"}:
                        inner = " ".join(cmd[j + 1:])
                    r = evaluate(inner, "ps" if head in {"pwsh", "powershell"} else "bash", ctx, depth + 1)
                    if r and not hatch:
                        return r
                    break
            continue
        if head != "git":
            continue
        r = git_reason(cmd[1:], ctx, depth)
        if r and not hatch:
            return r
    return None


# ------------------------------------------------------------------------------------------------ the self-test table
class FakeCtx(Ctx):
    REFS = {"main", "master", "HEAD", "HEAD~1", "HEAD~5", "wt/restock", "wt/x", "wt/new", "wt/phase2.step0", "v1.0.rc1",
            "v0.1.5", "origin/main", "origin/wt/x.y", "wt/r20.1", "release/v1.2", "restore/pre-promote-2026-09-24"}
    PATHS = {"a.py", "x.py", "pokemon_league.py", "sandbox-pokebot", "sandbox-pokebot/", ".gitignore", "Makefile",
             "conflicted", "dir", "old.py", "list.txt", "..", "."}
    ALIASES = {"co": "checkout", "nuke": "!git reset --hard", "st": "status"}

    def is_ref(self, tok, c_dir):
        return tok in self.REFS

    def is_path(self, tok, c_dir):
        return tok in self.PATHS

    def alias(self, name, c_dir):
        return self.ALIASES.get(name)


G, H = "g" + "it", HATCH + "=1"
B, A = True, False
CASES: list[tuple[str, bool, str]] = [
    # --- BLOCK: the 2026-09-27 incident and its siblings ------------------------------------------------------------
    ("bash", B, f"{G} checkout -- sandbox-pokebot/modules/story/pokemon_league.py"),
    ("bash", B, f"cd /repo && {G} checkout -- a.py"),
    ("bash", B, f'{G} -C "C:/Remote Projects/pokebot-wt-ch24" checkout -- x.py'),
    ("bash", B, f"{G} checkout HEAD -- a.py"), ("bash", B, f"{G} checkout ."), ("bash", B, f"{G} checkout pokemon_league.py"),
    ("bash", B, f"{G} checkout -f main"), ("bash", B, f"{G} checkout --force main"), ("bash", B, f"{G} checkout --theirs a.py"),
    ("bash", B, f"{G} checkout --ours conflicted"), ("bash", B, f"{G} checkout sandbox-pokebot"),
    ("bash", B, f"{G} checkout sandbox-pokebot/"), ("bash", B, f"{G} checkout .."), ("bash", B, f"{G} checkout .gitignore"),
    ("bash", B, f"{G} checkout HEAD Makefile"), ("bash", B, f"{G} checkout --pathspec-from-file=list.txt"),
    ("bash", B, f"{G} checkout -B main"),
    ("bash", B, f"{G} restore a.py"), ("bash", B, f"{G} restore --worktree --staged a.py"), ("bash", B, f"{G} restore -W a.py"),
    ("bash", B, f"{G} restore --source=HEAD~1 a.py"), ("bash", B, f"{G} restore --pathspec-from-file=list.txt"),
    ("bash", B, f"{G} restore --staged --wor a.py"),
    ("bash", B, f"{G} reset --hard"), ("bash", B, f"{G} reset --hard origin/main"), ("bash", B, f"{G} reset --merge"),
    ("bash", B, f"{G} reset --har"),
    ("bash", B, f"{G} stash"), ("bash", B, f"{G} stash -u"), ("bash", B, f"{G} stash push -m wip"), ("bash", B, f"{G} stash save x"),
    ("bash", B, f"{G} stash drop"), ("bash", B, f"{G} stash clear"), ("bash", B, f"{G} stash pop"), ("bash", B, f"{G} stash branch x"),
    ("bash", B, f"{G} clean -fd"), ("bash", B, f"{G} clean -xdf"), ("bash", B, f"{G} clean --force"), ("bash", B, f"{G} clean --forc -d"),
    ("bash", B, f"{G} switch --discard-changes main"), ("bash", B, f"{G} switch --discard main"), ("bash", B, f"{G} switch -f main"),
    ("bash", B, f"{G} switch -C main"),
    ("bash", B, f"{G} branch -D wt/restock"), ("bash", B, f"{G} branch -d wt/restock"), ("bash", B, f"{G} branch --delete wt/x"),
    ("bash", B, f"{G} branch --del wt/x"), ("bash", B, f"{G} branch -M wt/a main"), ("bash", B, f"{G} branch -f main HEAD~5"),
    ("bash", B, f"{G} push --force origin main"), ("bash", B, f"{G} push -f"), ("bash", B, f"{G} push --force-with-lease origin main"),
    ("bash", B, f"{G} push --force-w origin main"), ("bash", B, f"{G} push origin +main"), ("bash", B, f"{G} push origin :wt/restock"),
    ("bash", B, f"{G} push origin --delete wt/restock"), ("bash", B, f"{G} push --del origin wt/x"),
    ("bash", B, f"{G} push origin HEAD:main --force"), ("bash", B, f"{G} push --mirror"),
    ("bash", B, f"{G} worktree remove ../pokebot-wt-ch24"), ("bash", B, f"{G} worktree remove --force ../x"),
    ("bash", B, f"{G} rm -f a.py"), ("bash", B, f"{G} rm -rf dir"),
    ("bash", B, f"{G} update-ref -d refs/heads/wt/x"), ("bash", B, f"{G} read-tree --reset -u HEAD"),
    ("bash", B, f"{G} checkout-index -a -f"), ("bash", B, f"{G} filter-branch --tree-filter x HEAD"),
    ("bash", B, f"{G} reflog expire --expire=now --all"), ("bash", B, f"{G} prune"), ("bash", B, f"{G} gc --prune=now"),
    # --- BLOCK: git not the first word (the review's class B) --------------------------------------------------------
    ("bash", B, f"{G} status; {G} checkout -- a.py"), ("bash", B, f"echo ok && {G} reset --hard"),
    ("bash", B, f"false && {G} -C /x stash drop"), ("bash", B, f"OTHER=1 {G} reset --hard"),
    ("bash", B, f"echo $({G} reset --hard)"), ("bash", B, f"$({G} stash)"), ("bash", B, f"`{G} reset --hard`"),
    ("bash", B, f"({G} reset --hard)"), ("bash", B, f"{{ {G} reset --hard; }}"), ("bash", B, f"! {G} stash"),
    ("bash", B, f"env {G} reset --hard"), ("bash", B, f"command {G} reset --hard"), ("bash", B, f"bash -c '{G} reset --hard'"),
    ("bash", B, f"if true; then {G} reset --hard; fi"), ("bash", B, f"for f in a.py; do {G} checkout -- $f; done"),
    ("bash", B, f"echo a.py | xargs {G} checkout --"), ("bash", B, f"ls | xargs {G} rm -f"), ("bash", B, f"'{G}' reset --hard"),
    ("bash", B, f"{G} status;\n{G} reset --hard"), ("bash", B, f"{G} status\n\n\n{G} stash drop"),
    ("bash", B, f'"C:/Program Files/Git/cmd/{G}.exe" reset --hard'), ("bash", B, f"nohup {G} stash &"),
    ("bash", B, f"timeout 30 {G} reset --hard"),
    # --- BLOCK: the mask/lexer traps (class C) and attached redirections (class D) -----------------------------------
    ("bash", B, f"# don't touch\n{G} reset --hard"), ("bash", B, f'grep x <<< "$v"; {G} reset --hard'),
    ("bash", B, f"cat <<< EOF; {G} stash"), ("bash", B, f'MSG="a b" {G} reset --hard'),
    ("bash", B, f"{G} reset --hard>/dev/null"), ("bash", B, f"{G} stash>/dev/null"), ("bash", B, f"{G} push --force>/dev/null"),
    ("bash", B, f"cat > m.txt <<'EOF'\nharmless\nEOF\n{G} reset --hard"),
    # --- BLOCK: config overrides and aliases (class A) ---------------------------------------------------------------
    ("bash", B, f"{G} -c alias.x=reset x --hard"), ("bash", B, f"{G} -c 'alias.x=!{G} stash' x"),
    ("bash", B, f"{G} --no-advice reset --hard"), ("bash", B, f"{G} --no-lazy-fetch stash"),
    ("bash", B, f"{G} --attr-source=HEAD reset --hard"), ("bash", B, f"{G} -c clean.requireForce=false clean -dx"),
    ("bash", B, f"{G} -c remote.origin.mirror=true push origin"), ("bash", B, f"{G} co -- a.py"), ("bash", B, f"{G} nuke"),
    # --- BLOCK: PowerShell ------------------------------------------------------------------------------------------
    ("ps", B, f"{G} reset --hard"), ("ps", B, f'& "C:/Program Files/Git/cmd/{G}.exe" reset --hard'),
    ("ps", B, f"& {{ {G} reset --hard }}"), ("ps", B, f"if ($true) {{ {G} reset --hard }}"), ("ps", B, f"cmd /c {G} reset --hard"),
    ("ps", B, f"{G} --% reset --hard"), ("ps", B, f"$m = @'\nit's fine\n'@\n{G} reset --hard"),
    ("ps", B, f'Write-Output "a`"b"; {G} reset --hard'), ("ps", B, f"{G} status\r{G} reset --hard"),
    ("ps", B, f"powershell -Command \"{G} stash drop\""),
    # --- BLOCK: the hatch cannot be spoofed ----------------------------------------------------------------------------
    ("bash", B, f'echo "{H}" && {G} reset --hard'), ("bash", B, f"# {H}\n{G} reset --hard"),
    ("ps", B, f'<#\n$env:{HATCH} = "1"\n#>\n{G} reset --hard'), ("ps", B, f'if ($false) {{\n$env:{HATCH} = "1"\n}}\n{G} reset --hard'),
    ("bash", B, f"{H} echo x; {G} reset --hard"),
    # --- ALLOW: ordinary work -----------------------------------------------------------------------------------------
    ("bash", A, f"{G} checkout main"), ("bash", A, f"{G} checkout wt/restock"), ("bash", A, f"{G} checkout -b wt/new-item"),
    ("bash", A, f"{G} checkout -b feature.md"), ("bash", A, f"{G} checkout v0.1.5"), ("bash", A, f"{G} checkout -b wt/x.y origin/wt/x.y"),
    ("bash", A, f"{G} checkout wt/phase2.step0"), ("bash", A, f"{G} checkout v1.0.rc1"), ("bash", A, f"{G} checkout wt/r20.1"),
    ("bash", A, f"{G} checkout restore/pre-promote-2026-09-24"), ("bash", A, f"{G} checkout -- "), ("bash", A, f"{G} checkout -"),
    ("bash", A, f"{G} switch main"), ("bash", A, f"{G} switch -c wt/new-item"), ("bash", A, f"{G} switch -c x.y"),
    ("bash", A, f"{G} restore --staged a.py"), ("bash", A, f"{G} restore -S a.py"), ("bash", A, f"{G} restore -s HEAD~1 --staged a.py"),
    ("bash", A, f"{G} reset a.py"), ("bash", A, f"{G} reset --soft HEAD~1"), ("bash", A, f"{G} reset HEAD a.py"), ("bash", A, f"{G} reset --mixed"),
    ("bash", A, f"{G} stash list"), ("bash", A, f"{G} stash show -p stash@{{0}}"), ("bash", A, f"{G} stash apply"), ("bash", A, f"{G} stash -h"),
    ("bash", A, f"{G} clean -n"), ("bash", A, f"{G} clean --dry-run -d"), ("bash", A, f"{G} clean -nfd"),
    ("bash", A, f"{G} branch wt/new"), ("bash", A, f"{G} branch -a"), ("bash", A, f"{G} branch --show-current"),
    ("bash", A, f"{G} branch -m old new"), ("bash", A, f"{G} branch --list"), ("bash", A, f"{G} branch -vv"),
    ("bash", A, f"{G} push -u origin wt/new"), ("bash", A, f"{G} push origin main"), ("bash", A, f"{G} push -q origin main 2>&1 | tail -1"),
    ("bash", A, f"{G} push --tags"), ("bash", A, f"{G} push --dry-run origin main"), ("bash", A, f"{G} push origin HEAD:wt/x"),
    ("bash", A, f"{G} worktree add ../wt -b wt/x"), ("bash", A, f"{G} worktree list"), ("bash", A, f"{G} worktree prune"),
    ("bash", A, f"{G} rm --cached a.py"), ("bash", A, f"{G} rm old.py"), ("bash", A, f"{G} rm -rf --cached sandbox-pokebot/logs"),
    ("bash", A, f"{G} rm -r --cached dir"),
    ("bash", A, f"{G} diff -- a.py"), ("bash", A, f"{G} diff HEAD -- a.py"), ("bash", A, f"{G} log --oneline -- a.py"),
    ("bash", A, f"{G} show HEAD:a.py"), ("bash", A, f"{G} merge --ff-only origin/wt/swapevo"), ("bash", A, f"{G} status --short"),
    ("bash", A, f'{G} -C "C:/Remote Projects/pokebot-wt-ch24" status --short'), ("bash", A, f"{G} gc"), ("bash", A, f"{G} reflog"),
    ("bash", A, f"{G} st"), ("bash", A, f"{G} fetch -q origin"), ("bash", A, f"ls | xargs {G} add"),
    ("bash", A, f"ls | xargs {G} restore --staged"), ("bash", A, f"{G} log --oneline -3 2>&1 | tail -1"), ("bash", A, f"{G} subtree pull --prefix=x upstream main --squash"),
    # --- ALLOW: MENTIONS ------------------------------------------------------------------------------------------------
    ("bash", A, f'echo "{G} checkout -- a.py"'), ("bash", A, f'grep -n "{G} reset --hard" CLAUDE.md'),
    ("bash", A, f'{G} commit -m "never run {G} checkout -- on uncommitted work"'),
    ("bash", A, f"cat > m.txt <<'EOF'\nrule: never {G} reset --hard\nEOF"),
    ("bash", A, f"{G} commit -F - <<'EOF'\nfix: x\n\n{G} stash drop was never run\nEOF"),
    ("bash", A, f'echo "12\\" record; {G} stash drop \\" ok"'), ("bash", A, f"# {G} reset --hard\necho hi"),
    ("ps", A, f"{G} commit -m @'\nfix: block destructive git\n\nThe reviewer's revert used the wrong command.\n{G} checkout -- a.py deleted the fix.\n'@"),
    ("ps", A, f'{G} commit -m @"\nfix: the 12" rule\n{G} stash drop is refused\n"@'),
    ("ps", A, f'{G} commit -m "the 12`" rule; {G} stash drop is refused"'),
    ("ps", A, f"<# {G} reset --hard #>\n{G} status"),
    # --- ALLOW: the deliberate, user-approved hatch -----------------------------------------------------------------------
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
    print(f"  OK  block_destructive_git.py: {len(CASES)}/{len(CASES)} cases (incident, review bypasses A-H, "
          f"false positives, mentions, the live hatch)")
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
