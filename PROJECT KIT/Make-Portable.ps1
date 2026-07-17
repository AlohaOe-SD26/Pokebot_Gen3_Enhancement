# ============================================================
#  Make-Portable.ps1 — offline snapshot (Claude Code Project Kit)
#
#  Packs THIS project into a dated portable folder (e.g. on a
#  USB stick) containing:
#    1. <project>.bundle — the ENTIRE git repository (all
#       branches, tags, full history, docs, the kit inside it)
#       in one file that git can clone with zero network
#    2. A copy of the current PROJECT KIT (so you can also
#       bootstrap NEW projects offline)
#    3. PORTABLE-README.txt — repo URL + exact restore steps
#
#  A bundle is a SNAPSHOT, not a sync channel: it is frozen the
#  moment it is made. GitHub remains the single source of truth;
#  the kit's AHEAD/DIVERGED guard will flag work resumed from a
#  stale bundle before it can cause confusion.
# ============================================================

# ---- optional knobs ----------------------------------------
$LevelsUp = 1
# Set a path here to skip the destination prompt (e.g. "E:\"):
$DefaultDestination = ""
# ------------------------------------------------------------

$ErrorActionPreference = "Stop"

$LogDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
try { Start-Transcript -Path (Join-Path $LogDir ("portable-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")) | Out-Null } catch {}

function Fail($msg) {
  Write-Host ""
  Write-Host "  ERROR: $msg" -ForegroundColor Red
  Write-Host ""
  try { Stop-Transcript | Out-Null } catch {}
  Read-Host "Press Enter to close"
  exit 1
}
function Done($msg) { Write-Host "   [ok]   $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "   [!]    $msg" -ForegroundColor Yellow }

function Run-Native {
  param([string]$Exe, [string[]]$ArgList)
  $old = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $out = & $Exe @ArgList 2>&1
  $script:NativeExit = $LASTEXITCODE
  $ErrorActionPreference = $old
  return (($out | ForEach-Object { "$_" }) -join "`n").Trim()
}

# --- resolve project root --------------------------------------------
$ProjectPath = $PSScriptRoot
for ($i = 0; $i -lt $LevelsUp; $i++) { $ProjectPath = Split-Path $ProjectPath -Parent }
$ProjectName = Split-Path $ProjectPath -Leaf

Write-Host ""
Write-Host "  =====================================================" -ForegroundColor DarkYellow
Write-Host "   PROJECT KIT - Make Portable (offline snapshot)" -ForegroundColor Yellow
Write-Host "  =====================================================" -ForegroundColor DarkYellow
Write-Host "   Project : $ProjectPath"
Write-Host ""

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail "git not found on PATH." }
if (-not (Test-Path (Join-Path $ProjectPath ".git"))) { Fail "No git repository here - run Bootstrap-Project.bat first." }
Set-Location $ProjectPath

# --- honest state report before snapshotting -------------------------
$dirty = Run-Native "git" @("status", "--porcelain")
if ($dirty) {
  Warn "Uncommitted changes exist - a bundle only contains COMMITTED history,"
  Warn "so these changes will NOT be in the snapshot:"
  ($dirty -split "`n") | Select-Object -First 10 | ForEach-Object { Write-Host "       $_" -ForegroundColor DarkGray }
  $ans = Read-Host "   Continue anyway (or commit/checkpoint first)? [y/N]"
  if ($ans -notmatch '^[Yy]') { Fail "Stopped so you can commit first (tip: /checkpoint in a session)." }
}
$branch = Run-Native "git" @("rev-parse", "--abbrev-ref", "HEAD")
$hash   = Run-Native "git" @("log", "-1", "--format=%h  %s  (%ci)")
$url    = Run-Native "git" @("remote", "get-url", "origin")
if ($script:NativeExit -ne 0 -or -not $url) { $url = "(no remote configured)" }
$aheadN = 0
Run-Native "git" @("rev-parse", "--abbrev-ref", "@{u}") | Out-Null
if ($script:NativeExit -eq 0) {
  [void][int]::TryParse((Run-Native "git" @("rev-list", "--count", "@{u}..HEAD")), [ref]$aheadN)
}

# --- destination ------------------------------------------------------
$dest = $DefaultDestination
if ([string]::IsNullOrWhiteSpace($dest)) {
  $dest = Read-Host "   Destination folder for the portable copy (e.g. E:\ for a USB stick)"
}
if ([string]::IsNullOrWhiteSpace($dest)) { Fail "No destination given." }
if (-not (Test-Path $dest)) { Fail "Destination not found: $dest" }
$stamp  = Get-Date -Format "yyyyMMdd-HHmm"
$folder = Join-Path $dest "$ProjectName-portable-$stamp"
New-Item -ItemType Directory -Path $folder | Out-Null

# --- 1) the bundle: entire repo in one file ---------------------------
$bundlePath = Join-Path $folder "$ProjectName.bundle"
Write-Host ""
Write-Host "   Creating bundle (full history, all branches + tags)..."
$out = Run-Native "git" @("bundle", "create", $bundlePath, "--all")
if ($script:NativeExit -ne 0) { Write-Host "      $out" -ForegroundColor DarkGray; Fail "git bundle create failed." }
$out = Run-Native "git" @("bundle", "verify", $bundlePath)
if ($script:NativeExit -ne 0) { Write-Host "      $out" -ForegroundColor DarkGray; Fail "Bundle failed verification - do not trust this snapshot." }
$sizeMB = "{0:N1}" -f ((Get-Item $bundlePath).Length / 1MB)
Done "Bundle created and VERIFIED ($sizeMB MB): $ProjectName.bundle"

# --- 2) a copy of the current kit (minus local logs) ------------------
$kitCopy = Join-Path $folder "PROJECT KIT"
Copy-Item $PSScriptRoot $kitCopy -Recurse
$copiedLogs = Join-Path $kitCopy "logs"
if (Test-Path $copiedLogs) { Remove-Item $copiedLogs -Recurse -Force }
Done "PROJECT KIT copied (for bootstrapping new projects offline)"

# --- 3) PORTABLE-README.txt -------------------------------------------
$aheadNote = ""
if ($aheadN -gt 0) {
  $aheadNote = "NOTE: this bundle contains $aheadN commit(s) NOT yet pushed to GitHub.`r`nIt is currently the ONLY copy of that work besides the source PC - push from`r`nthe source PC (or from a restore of this bundle) as soon as possible.`r`n`r`n"
}
$dirtyNote = ""
if ($dirty) { $dirtyNote = "NOTE: uncommitted changes existed when this snapshot was made and are NOT included.`r`n`r`n" }
$readme = @"
PORTABLE PROJECT SNAPSHOT - $ProjectName
=========================================
Created      : $(Get-Date -Format "yyyy-MM-dd HH:mm") on $env:COMPUTERNAME
Branch       : $branch
Last commit  : $hash
GitHub repo  : $url

$aheadNote$dirtyNote
WHAT THIS IS
------------
$ProjectName.bundle is the ENTIRE git repository (all branches, tags, full
history, all docs, and the Project Kit inside it) in a single file that git
can clone with no network at all. The PROJECT KIT folder beside it is the
standalone kit, for bootstrapping brand-new projects offline.

RESTORE (on any machine with git installed)
-------------------------------------------
1. Open PowerShell in the folder where you want the project, then:
       git clone "$ProjectName.bundle" "$ProjectName"
       cd "$ProjectName"
2. Work normally - the kit, docs, and launcher are all inside. Commit
   locally as usual (REMOTE START works; sync steps just report offline).
3. When GitHub access returns, reconnect and reconcile:
       git remote set-url origin $url     (or: git remote add origin <url>)
       git fetch
   Then follow the kit's sync rules: if GitHub moved on while you worked
   from this snapshot, the AHEAD/DIVERGED guard will flag it - review with
   the agent and merge deliberately. Push when green.

IMPORTANT
---------
This is a SNAPSHOT, frozen at the moment of creation - never a sync
channel. GitHub remains the single source of truth. Prefer cloning from
GitHub whenever it is reachable; use this bundle only when it is not.
"@
[System.IO.File]::WriteAllText((Join-Path $folder "PORTABLE-README.txt"), $readme, (New-Object System.Text.UTF8Encoding($false)))
Done "PORTABLE-README.txt written (repo URL + restore steps)"

Write-Host ""
Write-Host "  =====================================================" -ForegroundColor DarkYellow
Write-Host "   Portable snapshot complete:" -ForegroundColor Yellow
Write-Host "   $folder"
Write-Host "  =====================================================" -ForegroundColor DarkYellow
Write-Host ""
try { Stop-Transcript | Out-Null } catch {}
Read-Host "Press Enter to close"
