# 2026-10-01 — `#27-shellhook`: the heredoc / shell-text hook (USER RULING 29): BUILD SPEC + PREDICTIONS (filed BEFORE any code)

⛔ **THE CAVEAT IS THE HEADLINE.** A hook is a seat belt against HABIT, not a sandbox against an adversary. This one
enforces a written rule that failed FIVE times in two sessions: documentation and code text never pass through a
shell-quoted string; use Write/Edit, or a script file written with Write and then run. Each slip was verified
harmless. The next one may not be: a backslash, `$` or backtick silently rewritten in a doc or a gate.

**Approval:** USER RULING 29 (`06`, 2026-10-01): "I agree with approving the pending heredoc hook if you think it would
be helpful."
**Evidence of need:** `08` 2026-09-30 (the first four, two with a backslash in the body) and 2026-10-01 (the fourth and
fifth: a heredoc-written probe, and a changelog sentence passed as a shell-quoted argument).

## The build: `.claude/hooks/block_shell_text.py` (PreToolUse, Bash|PowerShell)

It REUSES `block_destructive_git.py`'s parser (imported, not copied: one parser, one place to fix). That parser
already:
- knows quotes, escapes and comments at a word start;
- reports a heredoc opener only in LIVE text, so a mention never counts;
- turns a PowerShell here-string into the token `HERESTRING`;
- strips assignments and wrappers.

**It BLOCKS, per simple command:**

| # | What | Example |
|---|---|---|
| H1 | a LIVE heredoc (`<<TAG`, `<<-TAG`, `<<'TAG'`), whatever the command: its body is text written through the shell, whether it becomes a file, a script, a commit message or a JSON body | `cat > x.py <<'EOF'`, `py - <<'EOF'`, `git commit -F - <<EOF` |
| H2 | a here-string `<<<` given to an interpreter or a shell | `bash <<< '…'`, `py - <<< "…"` |
| H3 | a PowerShell here-string (`@'…'@` / `@"…"@`) in a command that writes a file or runs an interpreter | `@'…'@ \| Set-Content x.md`, `@'…'@ \| py -` |
| H4 | `python`/`py` `-c` code that WRITES a file | `.write_text(`, `.write_bytes(`, `open(…, 'w'/'a'/'x')`, `.writelines(`, `json.dump(` |
| H5 | `echo` / `printf` / `Write-Output` redirected (`>`, `>>`) into a DOC or CODE file: under `PROJECT KNOWLEDGE/`, or `.md .py .ps1 .json .yml .yaml .jsonl`, or ANY target when the echoed text is over 120 characters | |
| H6 | a quoted argument over 300 characters passed to a `python`/`py` SCRIPT, which is text smuggled in as an argument (today's fifth slip) | |

It is evaluated inside `bash -c` / `cmd /c` / `powershell -Command` and `$( … )`, as the destructive hook does.

**It ALLOWS:** every mention (quoted text, comments, heredoc bodies of a live heredoc are never scanned as commands);
`git commit -F <file>`; `echo "exit=$?" >> run.txt` (short, not a doc or code file); read-only `py -c`; short script
arguments; `grep "<<EOF" …`; ordinary pipes.

**The hatch, ONLY for an operation the USER approved:** a live `POKEBOT_ALLOW_SHELL_TEXT=1` assignment in front of the
command itself, read from the COMMAND (this works, unlike the two older hooks' hatches, `#27-hookhatch`), or the
variable set in Claude Code's own environment.

**Contract:** tool JSON on stdin; exit 0 always; it fails OPEN on any internal error (a broken hook must never block a
session); a deny is ASCII JSON; `--selftest` runs the case table.

## The gate: `tools/story-dev/selftest_shell_text_hook.py` (appended to `run_gates.py`)

- **S1** the case table passes. It holds the five real incidents in their real shapes, every H row, the ALLOW list
  above, and the hatch.
- **S2** FAULT: the decision forced to always-allow fails the table.
- **S3** FAULT: the decision forced to always-block fails the table.
- **S4** the hook is registered in `.claude/settings.json` (PreToolUse, Bash|PowerShell) with
  `"$CLAUDE_PROJECT_DIR/.claude/hooks/…"` and `|| true` (the existing S7 rule covers the shape).
- **S5** the REAL hook process:
  - a blocked Bash command and a blocked PowerShell command each print ASCII JSON with `permissionDecision` "deny";
  - an allowed command prints nothing;
  - garbage stdin prints nothing and exits 0;
  - with the parser module missing, the hook fails OPEN.

## PREDICTIONS

| # | Run | Prediction | Falsified by |
|---|---|---|---|
| SH-1 | `selftest_shell_text_hook.py`; `run_gates.py` | S1-S5 pass; the full suite passes | any FAIL |
| SH-2 | an adversarial pass (a BYPASS hunter and a FALSE-POSITIVE hunter; the latter replays every Bash and PowerShell command this session actually ran, taken from the transcript) | every realistic bypass of H1-H6 is blocked or recorded as a known limit; 0 of this session's commands that obeyed the rule is blocked | a realistic bypass that is neither blocked nor recorded; one false positive |
| SH-3 | LIVE, after the merge to `main` (before 9:00 PM: no merge after, the batch's freeze) | a harmless heredoc command (`cat <<'EOF'` + one line, no file) is DENIED with the hook's reason; `git status` still runs | the heredoc runs; an ordinary command is denied |
