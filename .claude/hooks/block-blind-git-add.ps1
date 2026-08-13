# PreToolUse(Bash|PowerShell) hook — REFUSE a blind `git add -A` / `git add .`.
#
# WHY THIS EXISTS. On 2026-08-13 the same session ran `git add -A` while subagents were
# concurrently writing files into the working tree, and swept an unreviewed 406-line script into
# an unrelated "docs:" commit. It was caught, backed out, and the cause was written down — and
# then the SAME mistake happened four commits later, and that one was PUSHED, so it could not be
# amended away (this project never rewrites published history).
#
# ‼ THE LESSON THAT MADE THIS A HOOK RATHER THAN A RULE. The first occurrence was corrected
# perfectly and taught nothing, because fixing the COMMIT is not fixing the HABIT. This project's
# own log records that >=12 of 164 mistakes are self-admitted repeats, several committed while the
# author knew the rule. A rule that is merely written down has already been shown not to work here.
# Anything that can be enforced by a gate should BE a gate, not a line of prose.
#
# WHAT IT DOES. Blocks the wildcard forms and tells the caller to stage explicit paths. It does NOT
# block `git add <path>`, `git add -p`, or `git add -u` (which only touches already-tracked files
# and so cannot sweep in an agent's new file — the actual failure mode).
#
# ESCAPE HATCH: set POKEBOT_ALLOW_BLIND_ADD=1 for one command if you genuinely mean it. Deliberate
# and visible, which is the point — the failure was never a decision, it was an autopilot.
#
# Contract: read the tool call as JSON on stdin; exit 0 to allow; print JSON with
# permissionDecision "deny" to block. NEVER hangs. Always exits 0 (a broken hook must not wedge
# the session — it fails OPEN, because a hook that blocks everything is worse than the bug).

$ErrorActionPreference = "SilentlyContinue"

try {
    $raw = [Console]::In.ReadToEnd()
    if (-not $raw) { exit 0 }
    $payload = $raw | ConvertFrom-Json
    $cmd = [string]$payload.tool_input.command
    if (-not $cmd) { exit 0 }

    if ($env:POKEBOT_ALLOW_BLIND_ADD -eq "1") { exit 0 }

    # Match `git add -A|--all|.` ONLY IN COMMAND POSITION — at the start of the string, or right
    # after a shell separator (&& || ; | newline). Anything else is a mention, not an invocation.
    #
    # ‼ THE FIRST DRAFT MATCHED THE BARE SUBSTRING ANYWHERE, and it immediately blocked the very
    # script written to TEST it, because that script contained "git add -A" inside a quoted test
    # case. It would equally have blocked editing this comment, grepping for the phrase, or writing
    # the mistakes-log entry that explains it. That is the same defect as a doc-gate that fires on
    # prose: a check with false positives trains the reader to bypass it, which is strictly worse
    # than having no check. Narrow first, then verify with BOTH block-cases and allow-cases.
    $blind = $cmd -match '(?im)(^|[;&|]\s*|`n\s*)git\s+add\s+(-A\b|--all\b|\.(\s|$))'
    if (-not $blind) { exit 0 }

    $reason = @"
BLOCKED: blind 'git add -A' / 'git add .'.

This repo runs subagents that write files into the working tree while you work, so a wildcard
stage can sweep in an unreviewed file. That happened TWICE on 2026-08-13; the second one was
pushed and could not be amended away.

Do this instead:
  1. git status --short          # look at EVERY untracked file and account for it by name
  2. git add <path> [<path>...]  # stage explicit paths only
  3. name every added file in the commit message

'git add -u' is allowed (tracked files only). If you truly need the wildcard, prefix the command
with POKEBOT_ALLOW_BLIND_ADD=1 so the choice is deliberate and visible.
"@

    $out = @{
        hookSpecificOutput = @{
            hookEventName            = "PreToolUse"
            permissionDecision       = "deny"
            permissionDecisionReason = $reason
        }
    }
    $out | ConvertTo-Json -Depth 6 -Compress
} catch {
    # Fail OPEN. A hook that errors must never block the session.
}
exit 0
