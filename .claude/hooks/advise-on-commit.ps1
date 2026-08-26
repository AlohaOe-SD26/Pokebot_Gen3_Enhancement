# ADVISORY hook — punch-list `#24-difftriggeredrules`. Surfaces the prevention rules that
# match the working diff at the moment a `git commit` is attempted, by injecting
# `additionalContext` into the PreToolUse result.
#
# ⛔ NEVER BLOCKS, BY CONSTRUCTION: every exit path in this file is `exit 0`, and it emits
# NO permissionDecision — the normal permission flow is untouched (an "allow" here would
# auto-approve the commit past the user's prompt, which an advisory has no business doing).
# Any internal failure — bad stdin, missing python, missing tool, advisor crash — is
# swallowed and the hook stays silent: a broken advisory must cost nothing.
#
# Fault-tested standalone (see `#24-difftriggeredrules` in 03-PUNCH-LIST.md): commit
# command + findings -> JSON with additionalContext; non-commit command / clean tree /
# garbage stdin / empty stdin -> silence; ALL paths exit 0.

try {
    $raw = [Console]::In.ReadToEnd()
    if (-not $raw) { exit 0 }

    $payload = $null
    try { $payload = $raw | ConvertFrom-Json } catch { exit 0 }
    $cmd = $null
    try { $cmd = $payload.tool_input.command } catch { exit 0 }
    if (-not $cmd) { exit 0 }

    # Fire only on commit attempts. A false positive (the words inside a string) merely
    # prints an advisory — the cheap direction.
    if ($cmd -notmatch 'git(\.exe)?\s+commit') { exit 0 }

    $repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $tool = Join-Path $repo 'tools\story-dev\advise_on_diff.py'
    if (-not (Test-Path $tool)) { exit 0 }

    $env:PYTHONUTF8 = '1'
    $advice = & py -3.12 $tool 2>$null | Out-String
    if ($LASTEXITCODE -ne 0) { exit 0 }
    if (-not $advice -or -not $advice.Trim()) { exit 0 }

    $out = @{
        hookSpecificOutput = @{
            hookEventName     = 'PreToolUse'
            additionalContext = $advice.Trim()
        }
    }
    # ⚠ Measured (adversarial review): PS 5.1 ConvertTo-Json does NOT \uXXXX-escape
    # non-ASCII here — the advisory's ‼/⛔/em-dash pass through as raw UTF-8 bytes. Valid
    # JSON on this machine; if another machine's console codepage mangles them, the
    # advisory TEXT degrades cosmetically but the hook stays valid and non-blocking.
    $out | ConvertTo-Json -Depth 4 -Compress
    exit 0
} catch {
    exit 0
}
