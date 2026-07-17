# ============================================================
#  Install-Environment.ps1 - one-click setup for non-coders
#  (Claude Code Project Kit). Installs Git, GitHub CLI, and
#  Claude Code, then GUIDES you through the two one-time
#  sign-ins that must be done by hand (GitHub + Claude). Safe
#  to run more than once - it skips anything already installed.
# ============================================================
$ErrorActionPreference = "Continue"

$LogDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
try { Start-Transcript -Path (Join-Path $LogDir ("install-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")) | Out-Null } catch {}

function Say($m)   { Write-Host "   $m" }
function OK($m)    { Write-Host "   [done] $m" -ForegroundColor Green }
function Info($m)  { Write-Host "   [info] $m" -ForegroundColor Cyan }
function Warn($m)  { Write-Host "   [!]    $m" -ForegroundColor Yellow }
function Step($n,$m){ Write-Host ""; Write-Host "  === Step $n of 5: $m ===" -ForegroundColor Yellow }

function Have($exe) { return [bool](Get-Command $exe -ErrorAction SilentlyContinue) }
function Refresh-Path {
  $machine = [System.Environment]::GetEnvironmentVariable("Path","Machine")
  $user    = [System.Environment]::GetEnvironmentVariable("Path","User")
  $env:Path = "$machine;$user"
}

Clear-Host
Write-Host ""
Write-Host "  ===================================================" -ForegroundColor DarkYellow
Write-Host "   CLAUDE CODE PROJECT KIT - Environment Installer" -ForegroundColor Yellow
Write-Host "  ===================================================" -ForegroundColor DarkYellow
Write-Host ""
Say "This sets up the 3 tools you need, one time on this PC:"
Say "  1. Git          - tracks your project's history"
Say "  2. GitHub CLI   - saves your work online (your account)"
Say "  3. Claude Code  - the AI assistant you'll work with"
Write-Host ""
Say "You can re-run this any time; it skips what's already done."
Write-Host ""

# --- winget availability (the installer engine) ---------------------
Step 1 "Checking the Windows app installer (winget)"
if (-not (Have "winget")) {
  Warn "winget (the Windows package installer) isn't available."
  Warn "Open the Microsoft Store, search 'App Installer', install/update it,"
  Warn "then run this again. (On Windows 10/11 it's usually already there.)"
  Write-Host ""
  Read-Host "Press Enter to close"
  try { Stop-Transcript | Out-Null } catch {}
  exit 1
}
OK "winget is available"

function Install-WithWinget($id, $friendly) {
  Info "Installing $friendly ..."
  winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements | Out-Null
  Refresh-Path
}

# --- Git -------------------------------------------------------------
Step 2 "Git"
if (Have "git") { OK "Git is already installed" }
else {
  Install-WithWinget "Git.Git" "Git"
  if (Have "git") { OK "Git installed" }
  else { Warn "Git may need a new window to appear on PATH - re-run this installer if the next steps can't find it." }
}

# --- GitHub CLI ------------------------------------------------------
Step 3 "GitHub CLI"
if (Have "gh") { OK "GitHub CLI is already installed" }
else {
  Install-WithWinget "GitHub.cli" "GitHub CLI"
  if (Have "gh") { OK "GitHub CLI installed" }
  else { Warn "GitHub CLI may need a new window to appear on PATH - re-run if needed." }
}

# --- Claude Code: native installer first, winget fallback ------------
Step 4 "Claude Code"
if (Have "claude") { OK "Claude Code is already installed" }
else {
  Info "Installing Claude Code (native installer - keeps itself updated)..."
  $nativeOk = $false
  try {
    Invoke-Expression (Invoke-RestMethod -Uri "https://claude.ai/install.ps1")
    Refresh-Path
    if (Have "claude") { $nativeOk = $true }
  } catch { }
  if ($nativeOk) {
    OK "Claude Code installed (native)"
  } else {
    Warn "Native installer didn't complete - trying winget instead..."
    Install-WithWinget "Anthropic.ClaudeCode" "Claude Code"
    if (Have "claude") { OK "Claude Code installed (winget)" }
    else { Warn "Claude Code isn't on PATH yet. Close this window, open a NEW PowerShell, and run this installer once more." }
  }
}

# --- Guided one-time sign-ins ---------------------------------------
Step 5 "Sign in (two quick logins done by hand)"
Write-Host ""
Say "These two sign-ins open in your web browser. They can't be"
Say "automated safely, so I'll walk you through them."
Write-Host ""

# GitHub login
if (Have "gh") {
  & gh auth status *> $null
  if ($LASTEXITCODE -eq 0) {
    OK "You're already signed in to GitHub"
  } else {
    Info "GitHub sign-in:"
    Say "  - A short code will appear (looks like ABCD-1234). Copy it."
    Say "  - Press Enter; your browser opens github.com/login/device."
    Say "  - Paste the code and approve. When asked, pick:"
    Say "      GitHub.com  ->  HTTPS  ->  authenticate Git: Yes  ->  browser."
    Write-Host ""
    $go = Read-Host "   Ready to sign in to GitHub now? [Y/n]"
    if ([string]::IsNullOrWhiteSpace($go) -or $go -match '^[Yy]') {
      & gh auth login --web --git-protocol https
      & gh auth status *> $null
      if ($LASTEXITCODE -eq 0) { OK "Signed in to GitHub" }
      else { Warn "Not signed in yet - you can re-run this installer to try again." }
    } else { Info "Skipped - re-run later to finish GitHub sign-in." }
  }
} else { Warn "GitHub CLI not found yet - re-run this installer after opening a new window." }

# Git identity (needed so commits are attributed)
if (Have "git") {
  $gname = (& git config --global user.name)  2>$null
  $gmail = (& git config --global user.email) 2>$null
  if ([string]::IsNullOrWhiteSpace($gname) -or [string]::IsNullOrWhiteSpace($gmail)) {
    Write-Host ""
    Info "One detail Git needs: a name and email to label your saves."
    $n = Read-Host "   Your name (e.g. Nick)"
    if (-not [string]::IsNullOrWhiteSpace($n)) {
      $e = Read-Host "   Your email"
      if (-not [string]::IsNullOrWhiteSpace($e)) {
        & git config --global user.name  "$n" | Out-Null
        & git config --global user.email "$e" | Out-Null
        OK "Git will label your saves as $n <$e>"
      }
    }
  } else { OK "Git already knows who you are ($gname)" }
}

# Claude login
if (Have "claude") {
  Write-Host ""
  Info "Claude Code sign-in:"
  Say "  - A window will open 'claude'. Follow its prompt to sign in"
  Say "    through claude.ai (use your Claude Pro or Max account)."
  Say "  - Once it says you're signed in, type  /status  to confirm,"
  Say "    then type  exit  to close it."
  Write-Host ""
  $go = Read-Host "   Open Claude Code to sign in now? [Y/n]"
  if ([string]::IsNullOrWhiteSpace($go) -or $go -match '^[Yy]') {
    & claude
    OK "Returned from Claude Code"
  } else { Info "Skipped - just run 'claude' later to sign in." }
}

# --- Final verification gate ----------------------------------------
Write-Host ""
Write-Host "  === Checking everything is ready ===" -ForegroundColor Yellow
$allGood = $true
if (Have "git") { OK "Git ready" } else { Warn "Git missing"; $allGood = $false }
if (Have "gh") {
  & gh auth status *> $null
  if ($LASTEXITCODE -eq 0) { OK "GitHub ready (signed in)" } else { Warn "GitHub installed but not signed in"; $allGood = $false }
} else { Warn "GitHub CLI missing"; $allGood = $false }
if (Have "claude") { OK "Claude Code ready" } else { Warn "Claude Code missing"; $allGood = $false }

Write-Host ""
if ($allGood) {
  Write-Host "  All set! This PC is ready." -ForegroundColor Green
  Write-Host ""
  Say "Next: open your project folder and double-click"
  Say "  PROJECT KIT\Bootstrap-Project.bat   (to set up a project), or"
  Say "  CONTINUE FROM GITHUB\Continue-From-GitHub.bat  (to pull one down)."
} else {
  Warn "A few things still need attention (see above)."
  Warn "The usual fix: close this window, open a NEW PowerShell or just"
  Warn "double-click this installer again - PATH updates need a fresh window."
}
Write-Host ""
try { Stop-Transcript | Out-Null } catch {}
Read-Host "Press Enter to close"
