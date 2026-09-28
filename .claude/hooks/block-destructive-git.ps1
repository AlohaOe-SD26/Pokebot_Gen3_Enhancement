# PreToolUse(Bash|PowerShell) hook — REFUSE git commands that can silently DISCARD work.
#
# WHY THIS EXISTS (2026-09-27, `08-MISTAKES.md`). An adversarial REVIEWER agent tested a mutation of a
# file under review and then "reverted" it with `git checkout -- <file>`. The fix under review was
# UNCOMMITTED, so the revert silently restored the PRE-FIX file: the fix itself was deleted. A gate
# caught it only because its wiring check happened to read that function. The user approved turning the
# rule into a hook (2026-09-28): CLAUDE.md already says "ask before any destructive git operation",
# "never force-push", and "never discard local work"; prose did not stop an agent, so this does.
#
# WHAT IT BLOCKS (each is a way to lose uncommitted work, published history, or a branch):
#   git checkout -- <paths> | git checkout <tree-ish> -- <paths> | git checkout . | git checkout <file>
#       | git checkout -f/--force/--ours/--theirs/-p           (branch switching is ALLOWED; prefer `git switch`)
#   git restore <paths>                  (ALLOWED: `git restore --staged <paths>` — it only unstages)
#   git reset --hard | --merge           (ALLOWED: `git reset <path>`, `--soft`, `--mixed`)
#   git stash | stash push/save/drop/clear/pop/branch   (ALLOWED: stash list/show/apply)
#   git clean -f... (any force)          (ALLOWED: `git clean -n`, the dry run)
#   git switch --discard-changes | -f/--force
#   git branch -d/-D/--delete            (CLAUDE.md: ask before branch deletion)
#   git push --force/-f/--force-with-lease/--mirror/--delete, a `+refspec` or a `:branch` delete
#   git worktree remove                  (deletes a checkout that may hold uncommitted work)
#   git rm -f/--force                    (ALLOWED: plain `git rm`, which refuses on local changes; `--cached`)
#
# HOW IT PARSES: the same DATA MASK as `block-blind-git-add.ps1` (quoted text and heredoc bodies are
# DATA, never commands), segments split on live `;` `|` `&` and newlines, leading `VAR=value`
# assignments stripped, git GLOBAL options skipped (`git -C <path> checkout ...` is caught).
#
# ESCAPE HATCH — ONLY after the USER approved that specific operation: put
#   POKEBOT_ALLOW_DESTRUCTIVE_GIT=1
# in front of the git command (`POKEBOT_ALLOW_DESTRUCTIVE_GIT=1 git branch -D x`), or set
# `$env:POKEBOT_ALLOW_DESTRUCTIVE_GIT=1` earlier in the same PowerShell command. ‼ It is read from the
# COMMAND TEXT (live, unquoted). The two older hooks read their hatch from the HOOK PROCESS's
# environment, which a command prefix never reaches, so their documented prefix cannot work
# (found 2026-09-28 while writing this one; recorded, not silently "fixed").
#
# FAULT-TESTED BOTH WAYS: `-SelfTest` runs the case table and exits non-zero if any case regresses.
# Wired as a standing gate via `tools/story-dev/selftest_destructive_git_hook.py`, which also
# mutates this file (decision forced to always-allow, then always-block) and requires the table to FAIL.
#
# Contract: tool call JSON on stdin; exit 0 to allow; print JSON with permissionDecision "deny" to
# block. On the HOOK path it ALWAYS exits 0 and fails OPEN on any internal error (a hook that blocks
# everything is worse than the bug). `-SelfTest` exits 1 on failure.

param([switch]$SelfTest)

$ErrorActionPreference = "SilentlyContinue"

# ---------------------------------------------------------------------------------------------
# DATA MASK — copied verbatim from block-blind-git-add.ps1 (it cannot be dot-sourced without running
# its hook body). 'D' = data (quoted / heredoc body), '.' = live shell text.
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

# A token that names a FILE (not a branch). Branch names here contain '/' (`wt/restock`) and tags
# carry dotted numbers (`v0.1.5`), so the test is a LETTER-led extension, or the whole-tree specs.
function Test-LooksLikePath {
    param([string]$Tok)
    if ($Tok -in @('.', './', '.\', '*', '**', ':/')) { return $true }
    if ($Tok -match '^:\(') { return $true }
    if ($Tok -match '\.[A-Za-z][A-Za-z0-9]{0,5}$') { return $true }
    return $false
}

# ---------------------------------------------------------------------------------------------
# Is ONE command segment a destructive git call? Returns a reason string, or $null.
# ---------------------------------------------------------------------------------------------
function Get-SegmentVerdict {
    param([string]$Segment, [bool]$HatchSeen)

    $s = $Segment.Trim()
    $hatch = $HatchSeen
    # Leading VAR=value assignments (bash env prefix). The hatch may be one of them.
    while ($s -match '^([A-Za-z_][A-Za-z0-9_]*)=(\S*)\s+(.*)$') {
        if ($Matches[1] -eq 'POKEBOT_ALLOW_DESTRUCTIVE_GIT' -and $Matches[2].Trim('"').Trim("'") -eq '1') { $hatch = $true }
        $s = $Matches[3].Trim()
    }
    if ($s -notmatch '^(?i)(\S*[\\/])?git(\.exe)?(\s|$)') { return $null }

    # QUOTE-AWARE tokens: split on whitespace only where the segment's own mask is live, so
    # `git -C "C:/Remote Projects/x" checkout -- f` keeps the quoted path as ONE token (this repo's
    # own paths contain a space; a plain whitespace split let exactly that form through — self-test).
    $segMask = Get-DataMask $s
    $tok = @()
    $cur = New-Object System.Text.StringBuilder
    for ($q = 0; $q -lt $s.Length; $q++) {
        if ($segMask[$q] -eq '.' -and [char]::IsWhiteSpace($s[$q])) {
            if ($cur.Length -gt 0) { $tok += $cur.ToString(); [void]$cur.Clear() }
        } else { [void]$cur.Append($s[$q]) }
    }
    if ($cur.Length -gt 0) { $tok += $cur.ToString() }
    $tok = @($tok | ForEach-Object { $_.Replace('"', '').Replace("'", '') })
    $i = 1
    while ($i -lt $tok.Count) {
        $t = $tok[$i]
        if ($t -match '^(?i)-(C|c)$')                                                   { $i += 2; continue }
        if ($t -match '^(?i)--(git-dir|work-tree|namespace|exec-path|config-env)$')     { $i += 2; continue }
        if ($t -match '^(?i)--(git-dir|work-tree|namespace|exec-path|config-env)=')     { $i += 1; continue }
        if ($t -match '^(?i)(-P|--no-pager|--paginate|--bare|--literal-pathspecs|--glob-pathspecs|--noglob-pathspecs|--icase-pathspecs|--no-replace-objects|--no-optional-locks)$') { $i += 1; continue }
        break
    }
    if ($i -ge $tok.Count) { return $null }
    $sub = $tok[$i].ToLower()
    $args_ = @()
    for ($k = $i + 1; $k -lt $tok.Count; $k++) {
        if ($tok[$k] -match '^[<>]|^\d?>') { break }     # a redirection ends the argument list
        $args_ += $tok[$k]
    }
    $reason = $null

    switch ($sub) {
        'checkout' {
            $skipNext = $false
            $afterDashDash = $false
            foreach ($a in $args_) {
                if ($skipNext) { $skipNext = $false; continue }
                if ($afterDashDash) { $reason = "checkout of paths after '--' discards their uncommitted changes"; break }
                if ($a -eq '--') { $afterDashDash = $true; continue }
                if ($a -cmatch '^-(b|B)$' -or $a -eq '--orphan') { $skipNext = $true; continue }
                # ‼ PowerShell's -and/-or have EQUAL precedence (left to right): parenthesise, or
                # `A -or B -and C` becomes `(A -or B) -and C` and `--force` slips through (self-test).
                if (($a -match '^(?i)(--force|--ours|--theirs|--patch)$') -or (($a -cmatch '^-[A-Za-z]*[fp][A-Za-z]*$') -and ($a -notmatch '^--'))) {
                    $reason = "checkout $a overwrites uncommitted changes"; break
                }
                if ($a -notmatch '^-' -and (Test-LooksLikePath $a)) { $reason = "checkout of a path ('$a') discards its uncommitted changes"; break }
            }
        }
        'restore' {
            $staged = @($args_ | Where-Object { ($_ -match '^(?i)(--staged|-S)$') -or (($_ -cmatch '^-[A-Za-z]*S[A-Za-z]*$') -and ($_ -notmatch '^--')) }).Count -gt 0
            $worktree = @($args_ | Where-Object { ($_ -match '^(?i)(--worktree|-W)$') -or (($_ -cmatch '^-[A-Za-z]*W[A-Za-z]*$') -and ($_ -notmatch '^--')) }).Count -gt 0
            $anyPath = @($args_ | Where-Object { $_ -notmatch '^-' }).Count -gt 0
            if ($anyPath -and (-not $staged -or $worktree)) { $reason = "restore of working-tree files discards their uncommitted changes (use --staged to only unstage)" }
        }
        'reset' {
            if (@($args_ | Where-Object { $_ -match '^(?i)--(hard|merge)$' }).Count -gt 0) { $reason = "reset --hard/--merge discards uncommitted changes" }
        }
        'stash' {
            $first = @($args_ | Where-Object { $_ -notmatch '^-' } | Select-Object -First 1)
            $subcmd = if ($first.Count -gt 0) { $first[0].ToLower() } else { 'push' }
            if ($subcmd -notin @('list', 'show', 'apply', 'create')) { $reason = "stash $subcmd hides or drops work (a kept stash is a user ruling: never drop stash@{0})" }
        }
        'clean' {
            if (@($args_ | Where-Object { $_ -match '^(?i)--force$' -or ($_ -cmatch '^-[A-Za-z]*f[A-Za-z]*$' -and $_ -notmatch '^--') }).Count -gt 0) {
                $reason = "clean -f deletes untracked files (use -n for a dry run)"
            }
        }
        'switch' {
            if (@($args_ | Where-Object { $_ -match '^(?i)(--discard-changes|--force|-f)$' }).Count -gt 0) { $reason = "switch --discard-changes/--force discards uncommitted changes" }
        }
        'branch' {
            if (@($args_ | Where-Object { $_ -match '^(?i)--delete$' -or ($_ -cmatch '^-[A-Za-z]*[dD][A-Za-z]*$' -and $_ -notmatch '^--') }).Count -gt 0) {
                $reason = "branch deletion (CLAUDE.md: ask the user before deleting a branch)"
            }
        }
        'push' {
            foreach ($a in $args_) {
                if ($a -match '^(?i)--(force|force-with-lease|force-if-includes|mirror|delete|prune)(=.*)?$' -or ($a -cmatch '^-[A-Za-z]*[fd][A-Za-z]*$' -and $a -notmatch '^--')) {
                    $reason = "push $a (CLAUDE.md: never force-push, never rewrite published history)"; break
                }
                if ($a -match '^\+' -or $a -match '^:[^/]') { $reason = "push refspec '$a' forces or deletes a remote ref"; break }
            }
        }
        'worktree' {
            $first = @($args_ | Where-Object { $_ -notmatch '^-' } | Select-Object -First 1)
            if ($first.Count -gt 0 -and $first[0].ToLower() -eq 'remove') { $reason = "worktree remove deletes a checkout that may hold uncommitted work" }
        }
        'rm' {
            if (@($args_ | Where-Object { $_ -match '^(?i)--force$' -or ($_ -cmatch '^-[A-Za-z]*f[A-Za-z]*$' -and $_ -notmatch '^--') }).Count -gt 0) {
                $reason = "rm -f deletes files even with uncommitted changes"
            }
        }
    }

    if ($reason -and $hatch) { return $null }
    return $reason
}

# ---------------------------------------------------------------------------------------------
function Get-DestructiveReason {
    param([string]$Command)

    if ([string]::IsNullOrWhiteSpace($Command)) { return $null }
    $mask = Get-DataMask $Command
    $n = $Command.Length
    $hatchSeen = $false

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
            $firstLive = -1
            for ($k = $start; $k -lt $i; $k++) {
                if ([char]::IsWhiteSpace($Command[$k])) { continue }
                $firstLive = $k; break
            }
            if ($firstLive -ge 0 -and $mask[$firstLive] -eq '.') {
                # A PowerShell `$env:POKEBOT_ALLOW_DESTRUCTIVE_GIT = "1"` statement earlier in the command.
                if ($seg -match '^\s*\$env:POKEBOT_ALLOW_DESTRUCTIVE_GIT\s*=\s*["'']?1["'']?\s*$') { $hatchSeen = $true }
                $r = Get-SegmentVerdict $seg $hatchSeen
                if ($r) { return $r }
            }
        }
        $start = $i + 1
    }
    return $null
}

# ---------------------------------------------------------------------------------------------
# PERMANENT FAULT TEST — both directions. Strings are assembled ($G) so this file's own source never
# contains a live destructive command in a position a hook could flag.
# ---------------------------------------------------------------------------------------------
if ($SelfTest) {
    $G = 'g' + 'it'
    $H = 'POKEBOT_ALLOW_DESTRUCTIVE_GIT=1'
    $cases = @(
        # --- MUST BLOCK: THE 2026-09-27 INCIDENT, and its siblings -----------------------------------
        @{ block = $true;  cmd = "$G checkout -- sandbox-pokebot/modules/story/pokemon_league.py" },
        @{ block = $true;  cmd = "cd /repo && $G checkout -- a.py" },
        @{ block = $true;  cmd = "$G -C `"C:/Remote Projects/pokebot-wt-ch24`" checkout -- x.py" },
        @{ block = $true;  cmd = "$G checkout HEAD -- a.py" },
        @{ block = $true;  cmd = "$G checkout ." },
        @{ block = $true;  cmd = "$G checkout pokemon_league.py" },
        @{ block = $true;  cmd = "$G checkout -f main" },
        @{ block = $true;  cmd = "$G checkout --theirs a.py" },
        # the two bypasses the first draft's own self-test exposed (precedence; a quoted path with a space)
        @{ block = $true;  cmd = "$G checkout --force main" },
        @{ block = $true;  cmd = "$G checkout --ours conflicted" },
        @{ block = $true;  cmd = "$G -C `"C:/Path With Space/repo`" reset --hard" },
        @{ block = $true;  cmd = "$G -C 'C:/Remote Projects/x' stash" },
        @{ block = $true;  cmd = "$G restore a.py" },
        @{ block = $true;  cmd = "$G restore --worktree --staged a.py" },
        @{ block = $true;  cmd = "$G restore --source=HEAD~1 a.py" },
        @{ block = $true;  cmd = "$G reset --hard" },
        @{ block = $true;  cmd = "$G reset --hard origin/main" },
        @{ block = $true;  cmd = "$G stash" },
        @{ block = $true;  cmd = "$G stash -u" },
        @{ block = $true;  cmd = "$G stash push -m wip" },
        @{ block = $true;  cmd = "$G stash drop" },
        @{ block = $true;  cmd = "$G stash clear" },
        @{ block = $true;  cmd = "$G stash pop" },
        @{ block = $true;  cmd = "$G clean -fd" },
        @{ block = $true;  cmd = "$G clean -xdf" },
        @{ block = $true;  cmd = "$G clean --force" },
        @{ block = $true;  cmd = "$G switch --discard-changes main" },
        @{ block = $true;  cmd = "$G branch -D wt/restock" },
        @{ block = $true;  cmd = "$G branch -d wt/restock" },
        @{ block = $true;  cmd = "$G branch --delete wt/restock" },
        @{ block = $true;  cmd = "$G push --force origin main" },
        @{ block = $true;  cmd = "$G push -f" },
        @{ block = $true;  cmd = "$G push --force-with-lease origin main" },
        @{ block = $true;  cmd = "$G push origin +main" },
        @{ block = $true;  cmd = "$G push origin :wt/restock" },
        @{ block = $true;  cmd = "$G push origin --delete wt/restock" },
        @{ block = $true;  cmd = "$G worktree remove ../pokebot-wt-ch24" },
        @{ block = $true;  cmd = "$G worktree remove --force ../x" },
        @{ block = $true;  cmd = "$G rm -f a.py" },
        @{ block = $true;  cmd = "$G rm -rf dir" },
        @{ block = $true;  cmd = "$G status; $G checkout -- a.py" },
        @{ block = $true;  cmd = "echo ok && $G reset --hard" },
        @{ block = $true;  cmd = "OTHER=1 $G reset --hard" },
        # the hatch must be LIVE: quoted or in a heredoc it is only a mention
        @{ block = $true;  cmd = "echo `"$H`" && $G reset --hard" },
        # --- MUST ALLOW: ordinary work ------------------------------------------------------------
        @{ block = $false; cmd = "$G checkout main" },
        @{ block = $false; cmd = "$G checkout wt/restock" },
        @{ block = $false; cmd = "$G checkout -b wt/new-item" },
        @{ block = $false; cmd = "$G checkout -b feature.md" },
        @{ block = $false; cmd = "$G checkout v0.1.5" },
        @{ block = $false; cmd = "$G switch main" },
        @{ block = $false; cmd = "$G switch -c wt/new-item" },
        @{ block = $false; cmd = "$G restore --staged a.py" },
        @{ block = $false; cmd = "$G restore -S a.py" },
        @{ block = $false; cmd = "$G reset a.py" },
        @{ block = $false; cmd = "$G reset --soft HEAD~1" },
        @{ block = $false; cmd = "$G stash list" },
        @{ block = $false; cmd = "$G stash show -p stash@{0}" },
        @{ block = $false; cmd = "$G clean -n" },
        @{ block = $false; cmd = "$G clean --dry-run -d" },
        @{ block = $false; cmd = "$G branch wt/new" },
        @{ block = $false; cmd = "$G branch -a" },
        @{ block = $false; cmd = "$G branch --show-current" },
        @{ block = $false; cmd = "$G push -u origin wt/new" },
        @{ block = $false; cmd = "$G push origin main" },
        @{ block = $false; cmd = "$G push -q origin main 2>&1 | tail -1" },
        @{ block = $false; cmd = "$G worktree add ../wt -b wt/x" },
        @{ block = $false; cmd = "$G worktree list" },
        @{ block = $false; cmd = "$G rm --cached a.py" },
        @{ block = $false; cmd = "$G rm old.py" },
        @{ block = $false; cmd = "$G diff -- a.py" },
        @{ block = $false; cmd = "$G log --oneline -- a.py" },
        @{ block = $false; cmd = "$G merge --ff-only origin/wt/swapevo" },
        @{ block = $false; cmd = "$G status --short" },
        @{ block = $false; cmd = "$G -C `"C:/Remote Projects/pokebot-wt-ch24`" status --short" },
        @{ block = $false; cmd = "$G -C `"C:/Remote Projects/pokebot-wt-ch24`" log --oneline -3" },
        # --- MUST ALLOW: MENTIONS (quoted, heredoc, grep, commit message) ---------------------------
        @{ block = $false; cmd = "echo `"$G checkout -- a.py`"" },
        @{ block = $false; cmd = "grep -n `"$G reset --hard`" CLAUDE.md" },
        @{ block = $false; cmd = "$G commit -m `"never run $G checkout -- on uncommitted work`"" },
        @{ block = $false; cmd = "cat > m.txt <<'EOF'`nrule: never $G reset --hard`nEOF" },
        # --- MUST ALLOW: the deliberate, user-approved hatch -----------------------------------------
        @{ block = $false; cmd = "$H $G branch -D wt/restock" },
        @{ block = $false; cmd = "cd /repo && $H $G worktree remove ../x" },
        @{ block = $false; cmd = "`$env:POKEBOT_ALLOW_DESTRUCTIVE_GIT = `"1`"; $G branch -D wt/x" }
    )

    $fails = 0
    foreach ($case in $cases) {
        $got = [bool](Get-DestructiveReason $case.cmd)
        if ($got -ne $case.block) {
            $fails++
            $want = if ($case.block) { "BLOCK" } else { "ALLOW" }
            $g = if ($got) { "BLOCK" } else { "ALLOW" }
            Write-Output ("  FAIL  want={0} got={1}  {2}" -f $want, $g, ($case.cmd -replace "`n", "\n"))
        }
    }
    if ($fails -eq 0) {
        Write-Output ("  OK  block-destructive-git.ps1: {0}/{0} cases (blocks incl. the 2026-09-27 incident, ordinary work, mentions, the live hatch)" -f $cases.Count)
        exit 0
    }
    Write-Output ("  {0} of {1} cases FAILED" -f $fails, $cases.Count)
    exit 1
}

# ---------------------------------------------------------------------------------------------
# HOOK PATH — always exits 0; fails OPEN.
# ---------------------------------------------------------------------------------------------
try {
    $raw = [Console]::In.ReadToEnd()
    if (-not $raw) { exit 0 }
    $payload = $raw | ConvertFrom-Json
    $cmd = [string]$payload.tool_input.command
    if (-not $cmd) { exit 0 }
    if ($env:POKEBOT_ALLOW_DESTRUCTIVE_GIT -eq "1") { exit 0 }

    $why = Get-DestructiveReason $cmd
    if (-not $why) { exit 0 }

    $reason = @"
BLOCKED: a git command that can silently discard work — $why.

On 2026-09-27 a reviewer agent "reverted" a test mutation with 'git checkout -- <file>' while the
fix under review was UNCOMMITTED, and deleted the fix. CLAUDE.md: ask before any destructive git
operation; never force-push; never discard local work.

Do this instead:
  * to undo a test mutation: mutate a COPY (a temp file or an exec'd string), never the file itself;
  * to protect work before a review: COMMIT it (a WIP commit on the branch) first;
  * to change branch: 'git switch <branch>' (it refuses to overwrite local changes);
  * to unstage: 'git restore --staged <path>'.

If the USER approved this exact operation, prefix the git command with
POKEBOT_ALLOW_DESTRUCTIVE_GIT=1 so the choice is deliberate and visible.
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
