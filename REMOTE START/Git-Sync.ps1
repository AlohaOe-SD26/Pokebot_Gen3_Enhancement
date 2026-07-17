# ============================================================
#  Git-Sync.ps1 — pre-launch sync (Claude Code Project Kit)
#  Chained by Remote-Start.bat BEFORE Remote-Start.ps1 runs.
#  Rules: BEHIND the remote -> pull (the remote is the truth,
#  because a completed wrap-up always ends with a confirmed
#  push). AHEAD or DIVERGED -> report and DO NOTHING: that
#  means a previous session ended without completing wrap-up,
#  and reconciling unpushed work is the USER's call.
#  NEVER blocks the launch and NEVER discards or pushes work.
# ============================================================
$LevelsUp = 1
$ErrorActionPreference = "Continue"

$ProjectPath = $PSScriptRoot
for ($i = 0; $i -lt $LevelsUp; $i++) { $ProjectPath = Split-Path $ProjectPath -Parent }

$LogDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
try { Start-Transcript -Path (Join-Path $LogDir ("sync-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")) | Out-Null } catch {}

Write-Host ""
Write-Host "  -- Project Kit pre-launch sync ----------------------" -ForegroundColor DarkYellow
$pause = 1
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "   [!] git not found - sync skipped." -ForegroundColor Yellow; $pause = 4
} elseif (-not (Test-Path (Join-Path $ProjectPath ".git"))) {
  Write-Host "   [i] No git repo yet - run PROJECT KIT\Bootstrap-Project.bat first." -ForegroundColor Yellow; $pause = 4
} else {
  Set-Location $ProjectPath
  $dirty = (& git status --porcelain 2>&1 | Out-String).Trim()
  & git remote get-url origin *> $null
  $hasRemote = ($LASTEXITCODE -eq 0)

  if ($dirty) {
    Write-Host "   [!] UNCOMMITTED changes left by a previous session:" -ForegroundColor Yellow
    ($dirty -split "`n") | Select-Object -First 10 | ForEach-Object { Write-Host "       $_" -ForegroundColor DarkGray }
    Write-Host "   [!] Pull SKIPPED to protect them. Make your first message to the" -ForegroundColor Yellow
    Write-Host "       agent: reconcile the leftover changes per the sync directive." -ForegroundColor Yellow
    $pause = 6
  } elseif (-not $hasRemote) {
    Write-Host "   [i] No remote configured - local-only project, sync skipped." -ForegroundColor Yellow
  } else {
    & git fetch --quiet 2>&1 | Out-Null
    & git rev-parse --abbrev-ref '@{u}' *> $null
    if ($LASTEXITCODE -ne 0) {
      Write-Host "   [i] Branch has no upstream yet - first push still pending." -ForegroundColor Yellow
    } else {
      $aheadN = 0; $behindN = 0
      [void][int]::TryParse(((& git rev-list --count '@{u}..HEAD' 2>$null | Out-String).Trim()), [ref]$aheadN)
      [void][int]::TryParse(((& git rev-list --count 'HEAD..@{u}' 2>$null | Out-String).Trim()), [ref]$behindN)
      if ($aheadN -gt 0) {
        $state = if ($behindN -gt 0) { "DIVERGED from" } else { "AHEAD of" }
        Write-Host "   [!] This machine is $state GitHub: $aheadN unpushed commit(s)." -ForegroundColor Yellow
        Write-Host "       A previous session ended WITHOUT completing wrap-up." -ForegroundColor Yellow
        Write-Host "       Nothing was pushed or discarded - reconciling is YOUR call:" -ForegroundColor Yellow
        Write-Host "       tell the agent to review the unpushed commits with you." -ForegroundColor Yellow
        $pause = 7
      } elseif ($behindN -gt 0) {
        & git pull --ff-only 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Host "   [ok] Pulled $behindN commit(s) - you are on the latest code." -ForegroundColor Green }
        else { Write-Host "   [!] Pull failed unexpectedly - ask the agent to sync per the directive." -ForegroundColor Yellow; $pause = 6 }
      } else {
        Write-Host "   [ok] Already up to date with GitHub." -ForegroundColor Green
      }
    }
  }
}
try { Stop-Transcript | Out-Null } catch {}
Start-Sleep -Seconds $pause
