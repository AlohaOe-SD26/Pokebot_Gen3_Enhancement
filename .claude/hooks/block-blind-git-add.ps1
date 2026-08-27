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
# ‼‼ REWRITTEN 2026-08-22, DEEP SANITY CHECK PASS 4 (INFRASTRUCTURE). The previous version was a
# single regex and was MEASURED — 22 executed cases — to have EIGHT BYPASSES and ONE FALSE
# POSITIVE. `CLAUDE.md` calls this hook "ENFORCED, not requested", so those gaps were load-bearing:
#
#   BYPASSES (all allowed by the old regex, all verified against real git semantics):
#     git add -Av        short-option BUNDLING — `-A\b` cannot match, `\b` fails before `v`
#     git add --al       git accepts any UNAMBIGUOUS long-option prefix
#     git add ./         `\.(\s|$)` requires the dot to END the token
#     git add "."        quoting defeats a literal-dot match
#     git add -- .       the `--` end-of-options separator shifts the pathspec
#     git add *          shell glob — same sweep, different spelling
#     git -C <path> add -A   GLOBAL OPTIONS between `git` and the subcommand. ‼ THE WORST ONE:
#                        this harness's own Bash tool tells agents to "prefer absolute paths"
#                        because `cd` can trigger a permission prompt — so `git -C` is the idiom
#                        an agent is actively steered toward.
#     git add :/         pathspec magic for "the whole repo, from the top"
#
#   FALSE POSITIVE: the old pattern treated `|` `;` `&` as shell separators even INSIDE QUOTED
#   TEXT or a HEREDOC BODY. Writing a test table, a doc line, or a mistakes-log entry that merely
#   CONTAINS the phrase was blocked. That is not hypothetical: it blocked the very command written
#   to test this hook, which is the same thing that happened to this file's FIRST draft (see the
#   comment the old version carried about it). This project's own rule is that a check with false
#   positives trains the reader to bypass it, which is strictly worse than no check — so the fix
#   had to close the bypasses AND remove the false positive, not trade one for the other.
#
# HOW IT WORKS NOW — a parser, not a regex:
#   1. Build a DATA MASK: every character inside single quotes, double quotes, or a heredoc body is
#      marked as DATA. Separators are then only real where the mask is clear.
#   2. Split into command segments on unmasked `;` `|` `&` and newlines.
#   3. For each segment starting (unmasked) with `git`, skip git's GLOBAL options, require the
#      subcommand to be `add`, and then look at the arguments for a whole-tree pathspec.
#   Matching runs on the ORIGINAL text — the mask only decides where a COMMAND can begin, so
#   `git add "."` is still caught while `echo "git add -A"` is still allowed.
#
# ESCAPE HATCH: set POKEBOT_ALLOW_BLIND_ADD=1 for one command if you genuinely mean it. Deliberate
# and visible, which is the point — the failure was never a decision, it was an autopilot.
#
# FAULT-TESTED BOTH WAYS, PERMANENTLY: `-SelfTest` runs its case table (blocks, allows, every bypass
# above, and the false positive) and exits non-zero if any regresses. It is gate #29 in
# `tools/story-dev/run_gates.py` via `selftest_git_add_hook.py`, because this project's rule is
# that anything enforceable belongs in a gate, and a gate nobody can prove will fire is theatre.
#
# Contract: read the tool call as JSON on stdin; exit 0 to allow; print JSON with
# permissionDecision "deny" to block. NEVER hangs. On the HOOK path it always exits 0 (a broken
# hook must not wedge the session — it fails OPEN, because a hook that blocks everything is worse
# than the bug). `-SelfTest` is not the hook path and DOES exit 1 on failure, which is the point.

param([switch]$SelfTest)

$ErrorActionPreference = "SilentlyContinue"

# ---------------------------------------------------------------------------------------------
# DATA MASK — which characters are inside quotes or a heredoc body, and therefore NOT shell syntax.
# Returns a char array parallel to $Text: 'D' = data, '.' = live shell text.
# ---------------------------------------------------------------------------------------------
function Get-DataMask {
    param([string]$Text)

    $n = $Text.Length
    $mask = New-Object char[] $n
    for ($i = 0; $i -lt $n; $i++) { $mask[$i] = '.' }

    $inSingle = $false
    $inDouble = $false
    $heredocTag = $null          # non-null while inside a heredoc body
    $lineStart = 0

    for ($i = 0; $i -lt $n; $i++) {
        $c = $Text[$i]

        if ($c -eq "`n") {
            if ($heredocTag) {
                # Does the line just ended consist solely of the terminator?
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

        # Heredoc opener:  << TAG | <<-TAG | <<'TAG' | <<"TAG"
        if ($c -eq '<' -and $i + 1 -lt $n -and $Text[$i + 1] -eq '<') {
            $rest = $Text.Substring($i)
            $m = [regex]::Match($rest, "^<<-?\s*(?:'([^']+)'|`"([^`"]+)`"|([A-Za-z_][A-Za-z0-9_]*))")
            if ($m.Success) {
                $heredocTag = if ($m.Groups[1].Success) { $m.Groups[1].Value }
                              elseif ($m.Groups[2].Success) { $m.Groups[2].Value }
                              else { $m.Groups[3].Value }
                # The opener itself is live text; the BODY starts after the next newline.
                $i += $m.Length - 1
                continue
            }
        }
    }
    return $mask
}

# ---------------------------------------------------------------------------------------------
# Is ONE command segment a blind `git add`?
# ---------------------------------------------------------------------------------------------
function Test-Segment {
    param([string]$Segment)

    $s = $Segment.Trim()
    if ($s -notmatch '^(?i)git(\s|$)') { return $false }

    $tok = @([regex]::Split($s, '\s+') | Where-Object { $_ -ne '' })
    $i = 1

    # Skip git GLOBAL options that may sit between `git` and the subcommand. This is the gap that
    # let `git -C <path> add -A` through, and `git -C` is the form this harness steers agents to.
    while ($i -lt $tok.Count) {
        $t = $tok[$i]
        if ($t -match '^(?i)-(C|c)$')                                        { $i += 2; continue }
        if ($t -match '^(?i)--(git-dir|work-tree|namespace|exec-path|config-env)$') { $i += 2; continue }
        if ($t -match '^(?i)--(git-dir|work-tree|namespace|exec-path|config-env)=') { $i += 1; continue }
        if ($t -match '^(?i)(-P|--no-pager|--paginate|--bare|--literal-pathspecs|--glob-pathspecs|--noglob-pathspecs|--icase-pathspecs|--no-replace-objects)$') { $i += 1; continue }
        break
    }

    if ($i -ge $tok.Count) { return $false }
    if ($tok[$i] -notmatch '^(?i)add$') { return $false }
    $i++

    for (; $i -lt $tok.Count; $i++) {
        $arg = $tok[$i]
        if ($arg -eq '--') { continue }                      # end-of-options; keep inspecting
        if ($arg -match '^[<>]') { break }                   # a redirection ends the argument list
        $bare = $arg.Trim('"').Trim("'")

        # -A / --all, including git's unambiguous long-option ABBREVIATIONS (--a, --al, --all)
        if ($bare -match '^(?i)--a(l(l)?)?$')      { return $true }
        # short-option BUNDLING: -A, -Av, -vA, -nAv ...
        if ($bare -cmatch '^-[A-Za-z]*A[A-Za-z]*$') { return $true }
        # whole-tree pathspecs, in every spelling git and the shell accept
        if ($bare -eq '.' -or $bare -eq './' -or $bare -eq '.\') { return $true }
        if ($bare -eq '*' -or $bare -eq '**' -or $bare -eq '*/') { return $true }
        if ($bare -eq ':/' -or $bare -match '^(?i):\(top\)') { return $true }
    }
    return $false
}

# ---------------------------------------------------------------------------------------------
function Test-BlindGitAdd {
    param([string]$Command)

    if ([string]::IsNullOrWhiteSpace($Command)) { return $false }
    $mask = Get-DataMask $Command
    $n = $Command.Length

    $start = 0
    for ($i = 0; $i -le $n; $i++) {
        $isSep = $false
        if ($i -eq $n) {
            $isSep = $true
        } elseif ($mask[$i] -eq '.') {
            $c = $Command[$i]
            if ($c -eq ';' -or $c -eq '|' -or $c -eq '&' -or $c -eq "`n") { $isSep = $true }
        }
        if (-not $isSep) { continue }

        $len = $i - $start
        if ($len -gt 0) {
            $seg = $Command.Substring($start, $len)
            # A segment that BEGINS inside quoted/heredoc data is not a command — it is text.
            $firstLive = -1
            for ($k = $start; $k -lt $i; $k++) {
                if ([char]::IsWhiteSpace($Command[$k])) { continue }
                $firstLive = $k; break
            }
            if ($firstLive -ge 0 -and $mask[$firstLive] -eq '.') {
                if (Test-Segment $seg) { return $true }
            }
        }
        $start = $i + 1
    }
    return $false
}

# ---------------------------------------------------------------------------------------------
# PERMANENT FAULT TEST — both directions. Run via `-SelfTest`; wired as a standing gate.
# ‼ The strings are ASSEMBLED at runtime ($G) so that this file's own source does not contain the
#   literal command in a position the hook would flag. The first draft of the ORIGINAL hook blocked
#   the script written to test it; the same trap is easy to walk into twice.
# ---------------------------------------------------------------------------------------------
if ($SelfTest) {
    $G = 'g' + 'it'
    $cases = @(
        # --- MUST BLOCK: the habitual forms the 2026-08-13 incidents actually used -------------
        @{ block = $true;  cmd = "$G add -A" },
        @{ block = $true;  cmd = "$G add ." },
        @{ block = $true;  cmd = "$G add --all" },
        @{ block = $true;  cmd = "cd foo && $G add -A" },
        @{ block = $true;  cmd = "$G status; $G add ." },
        @{ block = $true;  cmd = "$G  add   -A" },
        @{ block = $true;  cmd = "GIT ADD -A" },
        @{ block = $true;  cmd = "$G add -A -- ." },
        # --- MUST BLOCK: the eight bypasses MEASURED against the old regex on 2026-08-22 --------
        @{ block = $true;  cmd = "$G add -Av" },
        @{ block = $true;  cmd = "$G add -vA" },
        @{ block = $true;  cmd = "$G add --al" },
        @{ block = $true;  cmd = "$G add ./" },
        @{ block = $true;  cmd = "$G add `".`"" },
        @{ block = $true;  cmd = "$G add '.'" },
        @{ block = $true;  cmd = "$G add -- ." },
        @{ block = $true;  cmd = "$G add *" },
        @{ block = $true;  cmd = "$G -C . add -A" },
        @{ block = $true;  cmd = "$G -C /some/path add ." },
        @{ block = $true;  cmd = "$G --work-tree=/x --git-dir=/x/.git add -A" },
        @{ block = $true;  cmd = "$G add :/" },
        # --- MUST ALLOW: every legitimate staging form ------------------------------------------
        @{ block = $false; cmd = "$G add tools/story-dev/run_gates.py" },
        @{ block = $false; cmd = "$G add -u" },
        @{ block = $false; cmd = "$G add -p" },
        @{ block = $false; cmd = "$G add -N newfile.py" },
        @{ block = $false; cmd = "$G add -- PROJECT KNOWLEDGE/04-HANDOFF.md" },
        @{ block = $false; cmd = "$G add --chmod=+x tools/x.sh" },
        @{ block = $false; cmd = "$G commit -m 'staged everything'" },
        # --- MUST ALLOW: MENTIONS. A check that fires on prose teaches the reader to bypass it. --
        @{ block = $false; cmd = "echo `"$G add -A`"" },
        @{ block = $false; cmd = "grep -n `"$G add -A`" CLAUDE.md" },
        @{ block = $false; cmd = "printf '%s' 'X|$G add -A' > note.txt" },
        @{ block = $false; cmd = "cat > t.md <<'EOF'`nBLOCK|$G add -A`nrule: never do that`nEOF" }
    )

    $fails = 0
    foreach ($case in $cases) {
        $got = Test-BlindGitAdd $case.cmd
        if ($got -ne $case.block) {
            $fails++
            $want = if ($case.block) { "BLOCK" } else { "ALLOW" }
            $g = if ($got) { "BLOCK" } else { "ALLOW" }
            $show = $case.cmd -replace "`n", "\n"
            Write-Output ("  FAIL  want={0} got={1}  {2}" -f $want, $g, $show)
        }
    }
    if ($fails -eq 0) {
        Write-Output ("  OK  block-blind-git-add.ps1: {0}/{0} cases (blocks, allows, 8 measured bypasses, 3 mention forms)" -f $cases.Count)
        exit 0
    }
    Write-Output ("  {0} of {1} cases FAILED" -f $fails, $cases.Count)
    exit 1
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

    if ($env:POKEBOT_ALLOW_BLIND_ADD -eq "1") { exit 0 }

    if (-not (Test-BlindGitAdd $cmd)) { exit 0 }

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
