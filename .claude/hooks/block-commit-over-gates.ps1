# PreToolUse(Bash|PowerShell) hook — REFUSE a `git commit` chained to a gate run in ONE command.
#
# WHY THIS EXISTS. On 2026-09-25 this command ran:
#
#     grep -aE "ALL [0-9]+ ENFORCING|FAIL" /tmp/gatesD.out | tail -2 && git add ... && git commit ...
#
# The suite had FAILED (`FAILED: 1 of 85`). The commit went through anyway — because the exit
# status that gated it was **grep's**, and grep had SUCCEEDED at finding the word "FAIL".
# The gate's own exit code was never consulted by anything.
#
# ‼ THIS WAS THE SECOND OCCURRENCE. `08-MISTAKES.md` already records the first: a `for` loop with
# `&& echo PASS || echo FAIL` that swallowed a red Tier 0 and let a docs commit through. The fix
# recorded then was prose — "read the gate result as its own step" — and prose did not hold.
# CLAUDE.md is explicit that committing over a red doc gate is the same offence as `git add -A`,
# and that a rule broken twice must become enforcement. So here it is.
#
# WHAT IT BLOCKS — A WHITELIST, AND THE FIRST DESIGN WAS A BLACKLIST THAT MISSED THE REAL CASE.
# My first version blocked "a gate .py runs in the same command". Its own self-test refuted it
# immediately: the REAL 2026-09-25 command ran NO gate — it grepped a SAVED log — so the hook would
# have allowed the exact command it was written to prevent. A blacklist must enumerate every way to
# read a result (grep, tail, head, cat, sed, awk, a .out file, whatever is invented next) and is
# wrong the moment one is missed.
# ⇒ THE PROPERTY IS: a `git commit` may share its command ONLY with things that cannot stand in for
#   a verification result. The whitelist is short and stable:
#       git  (add / commit / push / status — the commit workflow itself)
#       cat, echo, printf, tee  (writing the commit MESSAGE file, usually via heredoc)
#       cd, true, :
#   ANY other head — grep, tail, py, a for-loop — blocks, because the commit's precondition must
#   never be some other command's exit status.
# ‼ THE UNDERLYING RULE, stated once: a verification READ and a mutating ACTION must not share a
#   tool call, because then the output cannot be READ before the action happens.
#
# ⛔ WHAT IT MUST NOT BLOCK, AND WHY THAT IS THE HARD HALF. Commit messages in this repo mention
# gate names constantly — "registers the gate (85 entries...)", "run_gates.py --quick 75". Those
# mentions live inside heredoc bodies and quoted strings. A naive grep would block exactly the
# well-documented commits this project demands, which is the false-positive failure its sibling
# hook already learned the hard way: "a check with false positives teaches the reader to bypass
# it, which is strictly worse than no check."
# ⇒ every character inside single quotes, double quotes or a heredoc body is masked as DATA before
#   any matching happens. `Get-DataMask` is copied VERBATIM from block-blind-git-add.ps1, which is
#   deliberate: that file cannot be dot-sourced without executing its hook body.
#
# ESCAPE HATCH: prefix with POKEBOT_ALLOW_COMMIT_CHAIN=1 so the choice is deliberate and visible.
#
# FAULT-TESTED BOTH WAYS: `-SelfTest` runs 12 cases — the real 2026-09-25 command, a saved-log tail,
# a gate run, order reversal, the `git -C` form, a for-loop — and the ALLOW side: a bare commit, the
# ordinary add/commit/push, a heredoc message naming gates, `git commit -m` quoting a gate name, a
# gate run with no commit, and `cd &&`. It exits non-zero if any regresses.
# ⭐ THE SELF-TEST ALREADY EARNED ITS KEEP: it refuted the first design on its first run.
#
# Contract: read the tool call as JSON on stdin; exit 0 to allow; print JSON with
# permissionDecision "deny" to block. On the HOOK path it ALWAYS exits 0 — it fails OPEN, because
# a hook that wedges the session is worse than the bug it guards.

param([switch]$SelfTest)

$ErrorActionPreference = "SilentlyContinue"

# ---------------------------------------------------------------------------------------------
# DATA MASK — which characters are inside quotes or a heredoc body, and therefore NOT shell syntax.
# Returns a char array parallel to $Text: 'D' = data, '.' = live shell text.
# ‼ COPIED VERBATIM from block-blind-git-add.ps1 (which cannot be dot-sourced without running its
#   hook body). If that one is ever corrected, correct this too — both self-tests would catch drift.
# ---------------------------------------------------------------------------------------------
function Get-DataMask {
    param([string]$Text)

    $n = $Text.Length
    $mask = New-Object char[] $n
    for ($i = 0; $i -lt $n; $i++) { $mask[$i] = '.' }

    $inSingle = $false
    $inDouble = $false
    $heredocTag = $null
    $lineStart = 0

    for ($i = 0; $i -lt $n; $i++) {
        $c = $Text[$i]

        if ($c -eq "`n") {
            if ($heredocTag) {
                $line = $Text.Substring($lineStart, $i - $lineStart).Trim()
                if ($line -eq $heredocTag) { $heredocTag = $null }
            }
            $lineStart = $i + 1
            continue
        }

        if ($heredocTag) { $mask[$i] = 'D'; continue }

        if (-not $inDouble -and $c -eq "'") { $inSingle = -not $inSingle; $mask[$i] = 'D'; continue }
        if (-not $inSingle -and $c -eq '"') { $inDouble = -not $inDouble; $mask[$i] = 'D'; continue }
        if ($inSingle -or $inDouble) { $mask[$i] = 'D'; continue }

        if ($c -eq '<' -and $i + 1 -lt $n -and $Text[$i + 1] -eq '<') {
            $rest = $Text.Substring($i)
            $m = [regex]::Match($rest, "^<<-?\s*(?:'([^']+)'|`"([^`"]+)`"|([A-Za-z_][A-Za-z0-9_]*))")
            if ($m.Success) {
                $heredocTag = if ($m.Groups[1].Success) { $m.Groups[1].Value }
                              elseif ($m.Groups[2].Success) { $m.Groups[2].Value }
                              else { $m.Groups[3].Value }
                $i += $m.Length - 1
                continue
            }
        }
    }
    return $mask
}

# Blank out every DATA character so matching only ever sees live shell text.
function Get-LiveText {
    param([string]$Text)
    $mask = Get-DataMask $Text
    $sb = New-Object System.Text.StringBuilder
    for ($i = 0; $i -lt $Text.Length; $i++) {
        if ($mask[$i] -eq 'D') { [void]$sb.Append(' ') } else { [void]$sb.Append($Text[$i]) }
    }
    return $sb.ToString()
}

# ---------------------------------------------------------------------------------------------
# The decision.
# ---------------------------------------------------------------------------------------------
function Test-CommitChainedToGates {
    param([string]$Command)

    $live = Get-LiveText $Command
    if (-not $live) { return $false }

    # Is there a `git commit` at all? (allows global options: `git -C <path> commit`)
    if ($live -notmatch '(?i)\bgit\b(?:\s+-[^\s]+(?:\s+[^\s-][^\s]*)?)*\s+commit\b') { return $false }

    # Split into STATEMENTS on `&&`, `||`, `;` and newlines — and deliberately NOT on a single `|`.
    # ⛔⛔ THIS DISTINCTION IS THE WHOLE CORRECTNESS OF THE HOOK, and the first version got it
    # wrong: it split on `|` too, so `git commit -F m | tail -3 && git push` was BLOCKED because a
    # `tail` segment appeared. That is a FALSE POSITIVE on the single most ordinary shape in this
    # repo — and it fired on the very commit that introduced this hook.
    # ⇒ what matters is a statement's PIPELINE HEAD, because that is whose exit status the next
    #   `&&` actually consults. Trailing filters cannot gate anything:
    #       grep X log | tail -2 && git commit   -> head `grep`  -> BLOCK (this is the real bug)
    #       git commit -F m | tail -3 && git push -> head `git`  -> ALLOW (output trimming only)
    $statements = [regex]::Split($live, '(&&|\|\||;|`n)') |
                  Where-Object { $_ -and ($_ -notmatch '^(&&|\|\||;|`n)$') }

    foreach ($seg in $statements) {
        # Only the PIPELINE HEAD is judged — everything after a `|` is an output filter.
        $t = ($seg -split '\|')[0].Trim()
        if (-not $t) { continue }

        # Strip leading VAR=value assignments (`PYTHONUTF8=1 py ...`) to reach the real head.
        while ($t -match '^[A-Za-z_][A-Za-z0-9_]*=\S*\s+(.*)$') { $t = $Matches[1].Trim() }
        if (-not $t) { continue }

        $head = ($t -split '\s+')[0]
        $head = $head -replace '^.*[\\/]', ''      # /usr/bin/grep -> grep

        # ⭐ THE WHITELIST — what may legitimately share a call with a commit.
        #   git      : add / commit / push / status ... the commit workflow itself
        #   cat,echo,printf,tee : writing the commit MESSAGE file (usually via heredoc)
        #   cd, true, :        : navigation and no-ops
        # EVERYTHING ELSE is treated as a possible RESULT-READ or side effect, and the commit's
        # precondition must not be its exit status.
        if ($head -match '^(?i)(git|cat|echo|printf|tee|cd|true|:)$') { continue }

        return $true    # something else shares this call with a commit -> block
    }

    return $false
}

# ---------------------------------------------------------------------------------------------
# SELF-TEST — the case table. Every entry is a real shape, not a hypothetical.
# ---------------------------------------------------------------------------------------------
if ($SelfTest) {
    $cases = @(
        # --- MUST BLOCK ---------------------------------------------------------------------------
        @{ Block = $true;  Why = "THE REAL 2026-09-25 COMMAND: grep of a SAVED gate log, then commit";
           Cmd = 'grep -aE "ALL ENFORCING|FAIL" /tmp/gatesD.out | tail -2 && git add x && git commit -F /tmp/m.txt' },
        @{ Block = $true;  Why = "tail of a saved gate log, then commit";
           Cmd = 'tail -2 /tmp/gatesD.out && git commit -F /tmp/m.txt' },
        @{ Block = $true;  Why = "gate RUN then commit";
           Cmd = 'PYTHONUTF8=1 py -3.12 run_gates.py && git commit -m x' },
        @{ Block = $true;  Why = "ORDER REVERSED - commit first, verification after";
           Cmd = 'git commit -m x && py -3.12 run_gates.py' },
        @{ Block = $true;  Why = "git -C form with a gate run";
           Cmd = 'py -3.12 audit_doc_consistency.py && git -C /repo commit -F /tmp/m.txt' },
        @{ Block = $true;  Why = "a for-loop / arbitrary shell sharing the call with a commit";
           Cmd = 'for g in a b; do py $g; done; git commit -F /tmp/m.txt' },

        # --- MUST ALLOW (a false positive is worse than no hook) ------------------------------------
        @{ Block = $false; Why = "a commit on its own";
           Cmd = 'git commit -F /tmp/msg.txt' },
        @{ Block = $false; Why = "the ordinary workflow: add && commit && push";
           Cmd = 'git add a b && git commit -F /tmp/m.txt && git push' },
        @{ Block = $false; Why = "writing the message with a heredoc, then committing";
           Cmd = "cat > /tmp/m.txt <<'EOF'`nfeat: x`n`nregisters the gate in run_gates.py`nEOF`ngit add a && git commit -F /tmp/m.txt" },
        @{ Block = $false; Why = "commit -m whose quoted message names a gate";
           Cmd = 'git commit -m "wire repro_roamer_outcome.py into run_gates.py"' },
        @{ Block = $false; Why = "a gate run with NO commit anywhere";
           Cmd = 'PYTHONUTF8=1 py -3.12 run_gates.py > /tmp/g.out 2>&1' },
        @{ Block = $false; Why = "cd then commit";
           Cmd = 'cd /repo && git add x && git commit -F /tmp/m.txt' },
        @{ Block = $false; Why = "THE FALSE POSITIVE THAT FIRED ON THIS HOOK'S OWN COMMIT - output filters";
           Cmd = 'git add a && git commit -F /tmp/m.txt | tail -3 && git push 2>&1 | tail -2' },
        @{ Block = $false; Why = "heredoc message + add + commit + push, all with tail filters";
           Cmd = "cat > /tmp/m.txt <<'EOF'`nfeat: x`nEOF`ngit add a && git commit -F /tmp/m.txt | tail -3 && git push 2>&1 | tail -2" },
        @{ Block = $true;  Why = "STILL BLOCKS: a grep PIPELINE head, even with a tail filter after it";
           Cmd = 'grep -aE "FAIL" /tmp/g.out | tail -2 && git commit -F /tmp/m.txt | tail -3' }
    )

    $failed = 0
    foreach ($c in $cases) {
        $got = Test-CommitChainedToGates $c.Cmd
        $ok = ($got -eq $c.Block)
        if (-not $ok) { $failed++ }
        $verdict = if ($ok) { "PASS" } else { "FAIL" }
        $want = if ($c.Block) { "BLOCK" } else { "ALLOW" }
        Write-Host ("  {0}  want={1,-5} got={2,-5}  {3}" -f $verdict, $want, $(if ($got) { "BLOCK" } else { "ALLOW" }), $c.Why)
    }
    Write-Host ""
    if ($failed -gt 0) {
        Write-Host "RESULT: FAIL - $failed case(s) regressed."
        exit 1
    }
    Write-Host "RESULT: ALL PASS - blocks the real failure, allows every documented-commit shape."
    exit 0
}

# ---------------------------------------------------------------------------------------------
# HOOK PATH — always exits 0.
# ---------------------------------------------------------------------------------------------
try {
    $raw = [Console]::In.ReadToEnd()
    if (-not $raw) { exit 0 }
    $payload = $raw | ConvertFrom-Json
    $cmd = [string]$payload.tool_input.command
    if (-not $cmd) { exit 0 }

    if ($env:POKEBOT_ALLOW_COMMIT_CHAIN -eq "1") { exit 0 }

    if (-not (Test-CommitChainedToGates $cmd)) { exit 0 }

    $reason = @"
BLOCKED: a 'git commit' chained to a gate run in ONE command.

In a single chain the commit is gated by the WRONG exit status. On 2026-09-25 this exact shape
committed over a RED suite:

    grep -aE "ALL ... ENFORCING|FAIL" /tmp/gatesD.out | tail -2 && git add ... && git commit ...

The suite had printed 'FAILED: 1 of 85'. The commit proceeded anyway, because the status that
gated it was GREP's - and grep had SUCCEEDED at finding the word 'FAIL'.
This was the SECOND occurrence; the first is already in 08-MISTAKES.md, and prose did not hold.

Do this instead - three separate tool calls, so each result is READ before the next step:
  1. run the suite            (its own call; note the exit code and the ALL ... PASS line)
  2. confirm it is green      (if red: fix the cause, never the baseline, then re-run)
  3. git add <paths> && git commit -F <file>

A commit MESSAGE that merely mentions gate names is fine - quoted text and heredoc bodies are
not treated as shell syntax. This only blocks a gate actually being RUN in the same command.

If you truly need it, prefix with POKEBOT_ALLOW_COMMIT_CHAIN=1 so the choice is deliberate.
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
