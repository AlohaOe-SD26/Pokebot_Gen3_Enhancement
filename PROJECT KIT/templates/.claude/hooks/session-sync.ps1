# SessionStart hook (Claude Code Project Kit) - safe sync + cheap catch-up.
# Runs from the project root on every session start / resume / clear /
# compact. It (1) syncs git per the kit's rules and (2) emits a SMALL
# catch-up brief as hookSpecificOutput.additionalContext so a fresh session
# gets oriented for very few tokens instead of re-reading everything.
# Rules: BEHIND remote -> pull (remote is truth after a clean wrap-up);
# AHEAD/DIVERGED -> report only, never auto-push/merge/discard. Never hangs,
# blocks, pushes, or discards. Always exits 0.
$ErrorActionPreference = "SilentlyContinue"
$env:GIT_TERMINAL_PROMPT = "0"
# Force UTF-8 for stdout and native-command decode so the brief is not mangled
# by Windows PowerShell 5.1's OEM/ANSI defaults. Guarded: setting the console
# encoding can throw when stdout is redirected (no real console); if it does,
# we swallow it and carry on so the never-hang / always-exit-0 invariant holds.
try { $utf8NoBom = New-Object System.Text.UTF8Encoding $false } catch { $utf8NoBom = $null }
if ($utf8NoBom) {
  try { [Console]::OutputEncoding = $utf8NoBom } catch {}
  try { $OutputEncoding = $utf8NoBom } catch {}
}
$lines = @()           # human-readable status lines for the brief
$syncNote = $null

function Tail($file, $n) {
  if (-not (Test-Path $file)) { return @() }
  $c = Get-Content $file -Encoding UTF8 -ErrorAction SilentlyContinue
  if (-not $c) { return @() }
  if ($c.Count -le $n) { return $c }
  return $c[($c.Count - $n)..($c.Count - 1)]
}

try {
  $haveGit = [bool](Get-Command git -ErrorAction SilentlyContinue)
  $inRepo  = (Test-Path ".git")

  if ($haveGit -and $inRepo) {
    $dirty = (& git status --porcelain 2>$null | Out-String).Trim()
    & git remote get-url origin *> $null
    $hasRemote = ($LASTEXITCODE -eq 0)
    if ($dirty) {
      $syncNote = "Uncommitted changes exist from a previous session. Pull was SKIPPED to protect them. Reconcile per the sync directive (review with the user; checkpoint or commit) BEFORE new work."
    } elseif ($hasRemote) {
      & git fetch --quiet 2>$null | Out-Null
      & git rev-parse --abbrev-ref '@{u}' *> $null
      if ($LASTEXITCODE -eq 0) {
        $ahead = 0; $behind = 0
        [void][int]::TryParse(((& git rev-list --count '@{u}..HEAD' 2>$null | Out-String).Trim()), [ref]$ahead)
        [void][int]::TryParse(((& git rev-list --count 'HEAD..@{u}' 2>$null | Out-String).Trim()), [ref]$behind)
        if ($ahead -gt 0) {
          $state = "AHEAD of"; if ($behind -gt 0) { $state = "DIVERGED from" }
          $syncNote = "This machine is $state the remote ($ahead unpushed commit(s)) - a previous session ended WITHOUT completing wrap-up. Do NOT push, build on, or discard them automatically; review with the user first."
        } elseif ($behind -gt 0) {
          & git pull --ff-only 2>$null | Out-Null
          if ($LASTEXITCODE -eq 0) { $syncNote = "Pulled $behind commit(s) from origin - working on the latest code." }
          else { $syncNote = "Behind origin but pull could not fast-forward; sync per the directive before new work." }
        } else { $syncNote = "Repo is up to date with origin." }
      }
    }
    $branch = (& git rev-parse --abbrev-ref HEAD 2>$null | Out-String).Trim()
    if ($branch) { $lines += "Branch: $branch" }
    $short = (& git status --short 2>$null | Out-String).Trim()
    if ($short) { $lines += "Working tree (uncommitted):"; $lines += (($short -split "`n") | Select-Object -First 8) }
  }

  # Compact catch-up pulled from the knowledge base (kept tiny on purpose).
  $pk = "PROJECT KNOWLEDGE"
  $midtask = $null
  $handoff = Join-Path $pk "04-HANDOFF.md"
  if (Test-Path $handoff) {
    $h = Get-Content $handoff -Raw -Encoding UTF8
    $m = [regex]::Match($h, '(?ms)^##\s*If stopped mid-task\s*(.+?)(?:^##\s|\Z)')
    if ($m.Success) {
      $body = $m.Groups[1].Value.Trim()
      if ($body -and $body -notmatch 'Nothing pending' -and $body -notmatch 'last stop was clean') {
        $midtask = ($body -split "`n" | Where-Object { $_.Trim() } | Select-Object -First 6) -join " "
      }
    }
  }

  $openPunch = @()
  $punch = Join-Path $pk "03-PUNCH-LIST.md"
  if (Test-Path $punch) {
    $openPunch = Get-Content $punch -Encoding UTF8 | Where-Object { $_ -match '^\s*-\s*\[ \]' } | Select-Object -First 5
  }

  $recentMistakes = @()
  $mistakes = Join-Path $pk "08-MISTAKES.md"
  if (Test-Path $mistakes) {
    $recentMistakes = Get-Content $mistakes -Encoding UTF8 | Where-Object { $_ -match '^##\s' } | Select-Object -Last 3
  }

  # Assemble the brief text.
  $brief = @()
  $brief += "[kit catch-up] Orient from this before acting; full detail is in PROJECT KNOWLEDGE/."
  if ($syncNote) { $brief += "Sync: $syncNote" }
  if ($lines.Count) { $brief += $lines }
  if ($midtask) { $brief += "RESUME POINT (mid-task): $midtask" }
  if ($openPunch.Count) { $brief += "Open punch-list:"; $brief += $openPunch }
  if ($recentMistakes.Count) {
    $brief += "Recent logged mistakes to NOT repeat (see 08-MISTAKES.md):"
    $brief += $recentMistakes
  }
  $brief += "Read 04-HANDOFF.md for the authoritative current state if anything here is unclear."
  $briefText = ($brief -join "`n")

  # Emit as official SessionStart additionalContext. Keep it small.
  $payload = @{
    hookSpecificOutput = @{
      hookEventName   = "SessionStart"
      additionalContext = $briefText
    }
  }
  $payload | ConvertTo-Json -Depth 6 -Compress
} catch {}
exit 0
