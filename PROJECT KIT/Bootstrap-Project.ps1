# ============================================================
#  Bootstrap-Project.ps1 - Claude Code Project Kit installer
#
#  HOW TO USE: copy the whole "PROJECT KIT" folder into your
#  project's ROOT folder, then double-click Bootstrap-Project.bat.
#  No editing required - the project root is auto-detected as the
#  PARENT of the folder this script lives in.
#
#  What it installs / configures (all steps are SAFE TO RE-RUN -
#  existing files are never overwritten, only missing pieces are
#  added, and the CLAUDE.md managed block is updated in place):
#    1. PROJECT KNOWLEDGE\ doc skeleton (only missing files created)
#    2. CLAUDE.md standing directives (managed BEGIN/END block)
#    3. REMOTE START\ phone-access launcher
#    4. git init + starter .gitignore (if missing)
#    5. Initial commit of the bootstrap files
#    6. GitHub remote: via gh CLI (creates a private repo, name
#       prompted) or a manually pasted repo URL
#    7. Repo URL recorded in PROJECT KNOWLEDGE\04-HANDOFF.md
#    8. Push
#
#  Works on stock Windows PowerShell 5.1. One-time GitHub CLI
#  setup ("gh auth login"): see README.md in this folder.
# ============================================================

# ---- automation parameters (all optional; double-click behavior is
#      unchanged when none are given). Added for the Remote Programs hub,
#      which drives this script without prompts:
#        -RepoName <name>   create a private GitHub repo with this name
#        -RepoUrl <url>     use this existing repo as origin (no creation)
#        -NoRemote          skip the GitHub remote + push steps entirely
#        -NonInteractive    never prompt; take safe defaults everywhere
param(
  [string]$RepoName = "",
  [string]$RepoUrl  = "",
  [switch]$NoRemote,
  [switch]$NonInteractive
)

# ---- optional knobs (defaults work for the setup above) ----
# How many folders UP from this script is the project root?
#   1 = kit lives in a subfolder of the project root (recommended)
#   0 = kit files sit directly in the project root itself
$LevelsUp = 1
# Hard override: set a full path here to ignore auto-detection entirely:
$ManualProjectPath = ""
# Default branch name for new repos:
$DefaultBranch = "main"
# ------------------------------------------------------------

$ErrorActionPreference = "Stop"
$KitVersion = "1.10"

# --- run log: a full transcript of every bootstrap run ------
$LogDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
try { Start-Transcript -Path (Join-Path $LogDir ("bootstrap-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")) | Out-Null } catch {}

function Fail($msg) {
  Write-Host ""
  Write-Host "  ERROR: $msg" -ForegroundColor Red
  Write-Host ""
  try { Stop-Transcript | Out-Null } catch {}
  if (-not $NonInteractive) { Read-Host "Press Enter to close" }
  exit 1
}
function Done($msg) { Write-Host "   [ok]   $msg" -ForegroundColor Green }
function Skip($msg) { Write-Host "   [skip] $msg" -ForegroundColor DarkGray }
function Warn($msg) { Write-Host "   [!]    $msg" -ForegroundColor Yellow }

# Run a native command (git/gh) without $ErrorActionPreference="Stop"
# turning its stderr chatter into a script-killing exception.
function Run-Native {
  param([string]$Exe, [string[]]$ArgList)
  $old = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $out = & $Exe @ArgList 2>&1
  $script:NativeExit = $LASTEXITCODE
  $ErrorActionPreference = $old
  return (($out | ForEach-Object { "$_" }) -join "`n").Trim()
}

# --- resolve the project root (same pattern as Remote-Start) --------
if ($ManualProjectPath -ne "") {
  $ProjectPath = $ManualProjectPath
} else {
  $ProjectPath = $PSScriptRoot
  for ($i = 0; $i -lt $LevelsUp; $i++) {
    $parent = Split-Path $ProjectPath -Parent
    if ([string]::IsNullOrEmpty($parent)) { Fail "Auto-detect walked above the drive root. Check LevelsUp." }
    $ProjectPath = $parent
  }
}
if (-not (Test-Path $ProjectPath)) { Fail "Project folder not found: $ProjectPath" }
$driveRoot = [System.IO.Path]::GetPathRoot($ProjectPath)
if ($ProjectPath.TrimEnd('\') -eq $driveRoot.TrimEnd('\')) {
  Fail "Auto-detected path is a drive root ($ProjectPath). Put the PROJECT KIT folder INSIDE your project's root folder (or set LevelsUp = 0 if its files sit directly in the root)."
}

$ProjectName = Split-Path $ProjectPath -Leaf
$KitDir      = $PSScriptRoot
$TemplateDir = Join-Path $KitDir "templates"
$Stamp       = Get-Date -Format "yyyy-MM-dd"
if (-not (Test-Path $TemplateDir)) { Fail "templates\ folder not found next to this script. Keep the PROJECT KIT folder intact." }

function Expand-Template([string]$text) {
  return $text.Replace('{{PROJECT_NAME}}', $ProjectName).Replace('{{DATE}}', $Stamp)
}
function Write-Text([string]$path, [string]$text) {
  [System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))
}

Write-Host ""
Write-Host "  =====================================================" -ForegroundColor DarkYellow
Write-Host "   CLAUDE CODE PROJECT KIT v$KitVersion - Bootstrap" -ForegroundColor Yellow
Write-Host "  =====================================================" -ForegroundColor DarkYellow
Write-Host "   Project : $ProjectPath"
Write-Host "   Name    : $ProjectName"
Write-Host ""

# ====================================================================
# 0) First-run preflight - detect & offer to set up prerequisites
#    Interactive but never blocking: anything the user declines is just
#    reported; the bootstrap continues and degrades gracefully.
# ====================================================================
Write-Host "  -- Preflight ----------------------------------------"
$ghReady = $false
# Git presence
if (Get-Command git -ErrorAction SilentlyContinue) {
  Done "Git is installed"
  # Git identity
  $gname = Run-Native "git" @("config", "--global", "user.name")
  $gmail = Run-Native "git" @("config", "--global", "user.email")
  if ([string]::IsNullOrWhiteSpace($gname) -or [string]::IsNullOrWhiteSpace($gmail)) {
    Warn "Git identity is not fully set (needed so commits are attributed)."
    $ans = ""
    if (-not $NonInteractive) { $ans = Read-Host "   Set it now? Enter your name (or blank to skip)" }
    if (-not [string]::IsNullOrWhiteSpace($ans)) {
      $email = Read-Host "   And your email"
      if (-not [string]::IsNullOrWhiteSpace($email)) {
        Run-Native "git" @("config", "--global", "user.name", $ans) | Out-Null
        Run-Native "git" @("config", "--global", "user.email", $email) | Out-Null
        Done "Git identity set ($ans <$email>)"
      } else { Warn "No email given - skipped; set it later with git config --global." }
    } else { Skip "Git identity left unset - the commit step will remind you if needed." }
  } else {
    Skip "Git identity already set ($gname <$gmail>)"
  }
} else {
  Warn "Git is NOT installed - it's required for everything that follows."
  Warn "Install it with:  winget install Git.Git"
  Warn "Then reopen PowerShell and re-run this bootstrap."
}

# GitHub CLI presence + auth (only meaningful if git exists)
if (Get-Command git -ErrorAction SilentlyContinue) {
  if (Get-Command gh -ErrorAction SilentlyContinue) {
    Done "GitHub CLI is installed"
    Run-Native "gh" @("auth", "status") | Out-Null
    if ($script:NativeExit -eq 0) {
      $ghReady = $true
      Done "GitHub CLI is logged in"
    } else {
      Warn "GitHub CLI is installed but not logged in - needed to auto-create"
      Warn "your private repo (otherwise you'll paste a repo URL by hand)."
      $ans = "n"
      if (-not $NonInteractive) { $ans = Read-Host "   Run 'gh auth login' now? [Y/n]" }
      if ([string]::IsNullOrWhiteSpace($ans) -or $ans -match '^[Yy]') {
        Write-Host "   Launching gh auth login - follow its prompts" -ForegroundColor Yellow
        Write-Host "   (GitHub.com -> HTTPS -> authenticate Git: Yes -> web browser)." -ForegroundColor Yellow
        & gh auth login
        Run-Native "gh" @("auth", "status") | Out-Null
        if ($script:NativeExit -eq 0) { $ghReady = $true; Done "GitHub CLI is now logged in" }
        else { Warn "Still not logged in - you can paste a repo URL later, or re-run." }
      } else {
        Skip "Skipped - you'll be asked for a repo URL at the GitHub step."
      }
    }
  } else {
    Warn "GitHub CLI (gh) is NOT installed - without it the bootstrap can't"
    Warn "auto-create your private repo; you'd paste a repo URL by hand."
    Warn "Install it with:  winget install GitHub.cli  (then reopen PowerShell)."
    $ans = "y"
    if (-not $NonInteractive) { $ans = Read-Host "   Continue without gh for now? [Y/n]" }
    if (-not ([string]::IsNullOrWhiteSpace($ans) -or $ans -match '^[Yy]')) {
      Fail "Stopped so you can install gh first. Re-run after installing."
    }
  }
}
Write-Host ""

# ====================================================================
# 1) PROJECT KNOWLEDGE skeleton - create only what's missing
# ====================================================================
Write-Host "  -- PROJECT KNOWLEDGE --------------------------------"
$pkSrc = Join-Path $TemplateDir "PROJECT KNOWLEDGE"
$pkDst = Join-Path $ProjectPath "PROJECT KNOWLEDGE"
if (-not (Test-Path $pkDst)) {
  New-Item -ItemType Directory -Path $pkDst | Out-Null
  Done "Created PROJECT KNOWLEDGE\"
} else {
  Skip "PROJECT KNOWLEDGE\ already exists"
}
Get-ChildItem $pkSrc -File | Sort-Object Name | ForEach-Object {
  $dst = Join-Path $pkDst $_.Name
  if (Test-Path $dst) {
    Skip "$($_.Name) exists - left untouched"
  } else {
    Write-Text $dst (Expand-Template (Get-Content $_.FullName -Raw -Encoding UTF8))
    Done "Created $($_.Name)"
  }
}

# ====================================================================
# 2) CLAUDE.md - create, or update/append the managed block
# ====================================================================
Write-Host "  -- CLAUDE.md ----------------------------------------"
$tplPath   = Join-Path $TemplateDir "CLAUDE.md"
if (-not (Test-Path $tplPath)) { Fail "templates\CLAUDE.md is missing from the kit." }
$tpl       = Expand-Template (Get-Content $tplPath -Raw -Encoding UTF8)
$beginMark = '<!-- BEGIN PROJECT-KIT DIRECTIVES'
$endMark   = '<!-- END PROJECT-KIT DIRECTIVES -->'
$bi = $tpl.IndexOf($beginMark); $ei = $tpl.IndexOf($endMark)
if ($bi -lt 0 -or $ei -lt 0) { Fail "templates\CLAUDE.md is missing its BEGIN/END markers." }
$block = $tpl.Substring($bi, ($ei - $bi) + $endMark.Length)

$claudePath = Join-Path $ProjectPath "CLAUDE.md"
if (-not (Test-Path $claudePath)) {
  Write-Text $claudePath $tpl
  Done "Created CLAUDE.md with standing directives"
} else {
  $cur = Get-Content $claudePath -Raw -Encoding UTF8
  $cbi = $cur.IndexOf($beginMark); $cei = $cur.IndexOf($endMark)
  if ($cbi -ge 0 -and $cei -gt $cbi) {
    $new = $cur.Substring(0, $cbi) + $block + $cur.Substring($cei + $endMark.Length)
    if ($new -ne $cur) {
      Copy-Item $claudePath "$claudePath.bak" -Force
      Write-Text $claudePath $new
      Done "Updated managed directives block (backup: CLAUDE.md.bak)"
    } else {
      Skip "Managed directives block already up to date"
    }
  } else {
    Copy-Item $claudePath "$claudePath.bak" -Force
    Write-Text $claudePath ($cur.TrimEnd() + "`r`n`r`n" + $block + "`r`n")
    Done "Appended managed directives block to your existing CLAUDE.md (backup: CLAUDE.md.bak)"
    Warn "This project already had its own CLAUDE.md. In your FIRST session,"
    Warn "run /reconcile - the agent will merge any pre-existing session"
    Warn "protocol with the kit directives: ask-first, nothing deleted"
    Warn "without your approval, contradictions surfaced for you to decide."
  }
}

# ====================================================================
# 2b) Claude Code slash commands (.claude\commands)
# ====================================================================
Write-Host "  -- Slash commands -----------------------------------"
$cmdSrc = Join-Path $TemplateDir ".claude\commands"
if (Test-Path $cmdSrc) {
  $cmdDst = Join-Path $ProjectPath ".claude\commands"
  if (-not (Test-Path $cmdDst)) { New-Item -ItemType Directory -Path $cmdDst -Force | Out-Null }
  Get-ChildItem $cmdSrc -File | ForEach-Object {
    $dst = Join-Path $cmdDst $_.Name
    $newC = Expand-Template (Get-Content $_.FullName -Raw -Encoding UTF8)
    if (-not (Test-Path $dst)) {
      Write-Text $dst $newC
      Done "Installed /$($_.BaseName) command"
    } elseif ($newC -ne (Get-Content $dst -Raw -Encoding UTF8)) {
      Copy-Item $dst "$dst.bak" -Force
      Write-Text $dst $newC
      Done "Updated /$($_.BaseName) command (backup: $($_.Name).bak)"
    } else { Skip "/$($_.BaseName) up to date" }
  }
} else {
  Warn "templates\.claude\commands not found - slash commands skipped"
}

# ====================================================================
# 2c) Session-start sync hook (.claude\settings.json + hooks\)
#     Defensive: settings.json is only CREATED if absent - if you already
#     have one, the hook must be merged manually (template shows the snippet).
# ====================================================================
Write-Host "  -- Session hook -------------------------------------"
$hkSrc = Join-Path $TemplateDir ".claude\hooks"
if (Test-Path $hkSrc) {
  $hkDst = Join-Path $ProjectPath ".claude\hooks"
  if (-not (Test-Path $hkDst)) { New-Item -ItemType Directory -Path $hkDst -Force | Out-Null }
  Get-ChildItem $hkSrc -File | ForEach-Object {
    $dst = Join-Path $hkDst $_.Name
    if (Test-Path $dst) { Skip "hooks\$($_.Name) exists - left untouched" }
    else { Copy-Item $_.FullName $dst; Done "Installed hooks\$($_.Name)" }
  }
  $setSrc = Join-Path $TemplateDir ".claude\settings.json"
  $setDst = Join-Path $ProjectPath ".claude\settings.json"
  if (Test-Path $setSrc) {
    if (-not (Test-Path $setDst)) {
      Copy-Item $setSrc $setDst
      Done "Installed .claude\settings.json (SessionStart sync hook)"
    } elseif ((Get-Content $setDst -Raw) -notmatch 'session-sync') {
      Warn ".claude\settings.json already exists - merge the SessionStart hook"
      Warn "manually using the snippet in PROJECT KIT\templates\.claude\settings.json"
    } else { Skip "SessionStart hook already configured" }
  }
} else {
  Warn "templates\.claude\hooks not found - session hook skipped"
}

# ====================================================================
# 3) REMOTE START launcher - install / upgrade
#    Remote-Start.ps1 is YOUR launcher: copied only if missing, never
#    overwritten. Git-Sync.ps1, KeepAwake.ps1 + the .bat are kit-owned:
#    kept current on every re-run.
# ====================================================================
Write-Host "  -- REMOTE START launcher ----------------------------"
$rsSrc = Join-Path $KitDir "REMOTE START"
$rsDst = Join-Path $ProjectPath "REMOTE START"
if (Test-Path $rsSrc) {
  if (-not (Test-Path $rsDst)) { New-Item -ItemType Directory -Path $rsDst | Out-Null }
  Get-ChildItem $rsSrc -File | ForEach-Object {
    $dst = Join-Path $rsDst $_.Name
    if (-not (Test-Path $dst)) {
      Copy-Item $_.FullName $dst; Done "Installed REMOTE START\$($_.Name)"
    } elseif ($_.Name -eq "Remote-Start.ps1") {
      Skip "Remote-Start.ps1 exists - left untouched (your launcher)"
    } else {
      # kit-owned (Remote-Start.bat, Git-Sync.ps1, KeepAwake.ps1): keep current
      if ((Get-Content $_.FullName -Raw) -ne (Get-Content $dst -Raw)) {
        Copy-Item $dst "$dst.bak" -Force
        Copy-Item $_.FullName $dst -Force
        Done "Updated REMOTE START\$($_.Name) (backup: .bak)"
      } else { Skip "$($_.Name) up to date" }
    }
  }
} else {
  Warn "Kit's REMOTE START\ folder not found - launcher skipped"
}

# ====================================================================
# 4) Git init + .gitignore
# ====================================================================
Write-Host "  -- Git ----------------------------------------------"
$haveGit = [bool](Get-Command git -ErrorAction SilentlyContinue)
$originUrl = $null
if (-not $haveGit) {
  Warn "git not found on PATH - all Git/GitHub steps skipped."
  Warn "Install Git for Windows (winget install Git.Git), then re-run this bootstrap."
} else {
  Set-Location $ProjectPath
  if (-not (Test-Path (Join-Path $ProjectPath ".git"))) {
    Run-Native "git" @("init") | Out-Null
    # Set default branch name without requiring git >= 2.28's init -b:
    Run-Native "git" @("symbolic-ref", "HEAD", "refs/heads/$DefaultBranch") | Out-Null
    Done "Initialized git repository (branch: $DefaultBranch)"
  } else {
    Skip "Git repository already initialized"
  }

  $gi = Join-Path $ProjectPath ".gitignore"
  if (-not (Test-Path $gi)) {
    $giBody = @"
# --- Claude Code Project Kit starter .gitignore (extend per stack) ---
# Secrets - never commit these
.env
.env.*
*.pem
*.key

# OS noise
Thumbs.db
desktop.ini
.DS_Store

# Editor / tool noise
.vscode/
.idea/
*.bak
*.tmp

# Common build/dependency output (delete lines that don't apply)
node_modules/
dist/
build/
__pycache__/
*.pyc
bin/
obj/

# Project Kit run logs (local diagnostics)
PROJECT KIT/logs/
REMOTE START/logs/
"@
    Write-Text $gi $giBody
    Done "Created starter .gitignore"
  } else {
    Skip ".gitignore already exists"
    $giRaw = Get-Content $gi -Raw
    if ($giRaw -notmatch [regex]::Escape('PROJECT KIT/logs/')) {
      Add-Content -Path $gi -Value "`r`n# Project Kit run logs (local diagnostics)`r`nPROJECT KIT/logs/`r`nREMOTE START/logs/"
      Done "Added kit log folders to existing .gitignore"
    }
  }

  # ------------------------------------------------------------------
  # .gitattributes:
  #   - launcher stays byte-verbatim: Remote-Start.ps1 ships with its
  #     ORIGINAL line endings and must never be CRLF/LF-normalized by git
  #     across machines (marking it -text disables all text conversion).
  #   - append-only logs merge cleanly across machines (merge=union keeps
  #     BOTH sides when two machines appended entries).
  # ------------------------------------------------------------------
  $ga = Join-Path $ProjectPath ".gitattributes"
  $launcherLines = "# Project Kit: keep the phone launcher byte-verbatim (its line endings are original)`r`n`"REMOTE START/Remote-Start.ps1`" -text`r`n`"REMOTE START/Remote-Start.bat`" -text"
  $unionLines = "# Project Kit: append-only logs - on conflicting appends, keep BOTH sides`r`n`"PROJECT KNOWLEDGE/06-DECISIONS-LOG.md`" merge=union`r`n`"PROJECT KNOWLEDGE/07-CHANGELOG.md`" merge=union`r`n`"PROJECT KNOWLEDGE/08-MISTAKES.md`" merge=union"
  if (-not (Test-Path $ga)) {
    Write-Text $ga ($launcherLines + "`r`n" + $unionLines + "`r`n")
    Done "Created .gitattributes (launcher byte-verbatim + append-only logs auto-merge)"
  } else {
    $gaRaw = Get-Content $ga -Raw -Encoding UTF8
    $added = @()
    if ($gaRaw -notmatch 'Remote-Start\.ps1') {
      Add-Content -Path $ga -Value ("`r`n" + $launcherLines); $added += "launcher -text"
    }
    if ($gaRaw -notmatch 'merge=union') {
      Add-Content -Path $ga -Value ("`r`n" + $unionLines); $added += "append-only merge"
    }
    if ($added.Count -gt 0) { Done ("Added " + ($added -join " + ") + " rule(s) to existing .gitattributes") }
    else { Skip ".gitattributes launcher + merge rules already present" }
  }

  # ------------------------------------------------------------------
  # Large-file guard (GitHub rejects pushes containing files > 100MB)
  # ------------------------------------------------------------------
  $big = Get-ChildItem $ProjectPath -Recurse -File -ErrorAction SilentlyContinue |
         Where-Object { $_.Length -gt 95MB -and $_.FullName -notmatch '\\\.git(\\|$)' }
  if ($big) {
    Warn "Files over 95MB found - GitHub rejects pushes with files over 100MB:"
    $big | ForEach-Object { Write-Host ("      {0:N0} MB  {1}" -f ($_.Length / 1MB), $_.FullName.Substring($ProjectPath.Length + 1)) -ForegroundColor DarkGray }
    $ans = "y"
    if (-not $NonInteractive) { $ans = Read-Host "   Add these to .gitignore so they stay local-only? [Y/n]" }
    if ([string]::IsNullOrWhiteSpace($ans) -or $ans -match '^[Yy]') {
      $rel = $big | ForEach-Object { ($_.FullName.Substring($ProjectPath.Length + 1)) -replace '\\', '/' }
      Add-Content -Path $gi -Value ("`r`n# Auto-added by Project Kit: files too large for GitHub`r`n" + ($rel -join "`r`n"))
      Done "Added $($big.Count) large file(s) to .gitignore"
    } else {
      Warn "Left as-is - the push may fail; consider Git LFS for large assets."
    }
  }

  # ==================================================================
  # 5) Initial commit (before remote creation - works on every gh version)
  # ==================================================================
  Write-Host "  -- Initial commit -----------------------------------"
  $dirty = Run-Native "git" @("status", "--porcelain")
  if ($dirty) {
    Run-Native "git" @("add", "-A") | Out-Null
    $out = Run-Native "git" @("commit", "-m", "chore: bootstrap with Claude Code Project Kit")
    if ($script:NativeExit -eq 0) { Done "Committed bootstrap files" }
    else {
      Warn "Commit failed:"
      Write-Host "      $out" -ForegroundColor DarkGray
      if ($out -match "user.name|user.email|identity") {
        Warn "Set your git identity once, then re-run this bootstrap:"
        Write-Host '      git config --global user.name  "Your Name"' -ForegroundColor DarkGray
        Write-Host '      git config --global user.email "you@example.com"' -ForegroundColor DarkGray
      }
    }
  } else {
    Skip "Nothing new to commit"
  }

  # ==================================================================
  # 6) GitHub remote - gh CLI (preferred) or manual URL
  # ==================================================================
  Write-Host "  -- GitHub remote ------------------------------------"
  $existing = Run-Native "git" @("remote", "get-url", "origin")
  if ($script:NativeExit -eq 0 -and $existing) {
    $originUrl = $existing
    Skip "Remote 'origin' already set: $originUrl"
  } elseif ($NoRemote) {
    Skip "Remote skipped (-NoRemote) - commits stay local until one is added."
  } elseif ($RepoUrl -ne "") {
    Run-Native "git" @("remote", "add", "origin", $RepoUrl) | Out-Null
    if ($script:NativeExit -eq 0) { $originUrl = $RepoUrl; Done "Set origin: $RepoUrl" }
    else { Warn "Could not add remote '$RepoUrl' - add one manually and push." }
  } else {
    $ghAuthed = $false
    if (Get-Command gh -ErrorAction SilentlyContinue) {
      Run-Native "gh" @("auth", "status") | Out-Null
      if ($script:NativeExit -eq 0) { $ghAuthed = $true }
    }

    if ($ghAuthed) {
      # Suggest a sanitized repo name from the folder; prompt unless supplied.
      $suggest = ($ProjectName.ToLower() -replace '[^a-z0-9._-]', '-') -replace '-{2,}', '-'
      $suggest = $suggest.Trim('-')
      if ([string]::IsNullOrWhiteSpace($suggest)) { $suggest = "my-project" }

      for ($try = 1; $try -le 3; $try++) {
        if ($RepoName -ne "") {
          $name = $RepoName
        } elseif ($NonInteractive) {
          Warn "No -RepoName given (non-interactive) - skipping remote creation."
          break
        } else {
          $name = Read-Host "   New PRIVATE repo name on your GitHub profile [Enter = $suggest, type 'skip' to skip]"
          if ([string]::IsNullOrWhiteSpace($name)) { $name = $suggest }
        }
        if ($name -eq "skip") { Warn "Skipped creating a remote - commits will stay local."; break }

        $out = Run-Native "gh" @("repo", "create", $name, "--private", "--source", ".", "--remote", "origin")
        if ($script:NativeExit -eq 0) {
          $originUrl = Run-Native "git" @("remote", "get-url", "origin")
          Done "Created private GitHub repo and set origin: $originUrl"
          break
        } else {
          Warn "gh repo create failed (attempt $try of 3):"
          Write-Host "      $out" -ForegroundColor DarkGray
          if ($RepoName -ne "") { break }   # supplied name failed - do not loop on it
          if ($try -eq 3) { Warn "Giving up on gh - re-run this bootstrap later or add a remote manually." }
        }
      }
    } else {
      Warn "GitHub CLI not installed or not logged in."
      Warn "(One-time fix: see 'gh auth login' steps in PROJECT KIT\README.md)"
      $url = ""
      if (-not $NonInteractive) { $url = Read-Host "   Paste an existing GitHub repo URL to use as origin [Enter = skip]" }
      if (-not [string]::IsNullOrWhiteSpace($url)) {
        Run-Native "git" @("remote", "add", "origin", $url) | Out-Null
        if ($script:NativeExit -eq 0) { $originUrl = $url; Done "Set origin: $url" }
        else { Warn "Could not add remote - check the URL and re-run." }
      } else {
        Skip "No remote configured - commits will stay local until one is added."
      }
    }
  }

  # ==================================================================
  # 7) Record the repo URL in the handoff doc (+ tiny docs commit)
  # ==================================================================
  $handoff = Join-Path $pkDst "04-HANDOFF.md"
  if ($originUrl -and (Test-Path $handoff)) {
    $h = Get-Content $handoff -Raw -Encoding UTF8
    if ($h -match '\*\*Repository:\*\*') {
      $h2 = $h -replace '\*\*Repository:\*\*[^\r\n]*', "**Repository:** $originUrl"
    } else {
      $h2 = "**Repository:** $originUrl`r`n`r`n" + $h
    }
    if ($h2 -ne $h) {
      Write-Text $handoff $h2
      Done "Recorded repo URL in 04-HANDOFF.md"
      Run-Native "git" @("add", "-A") | Out-Null
      Run-Native "git" @("commit", "-m", "docs: record repository URL in handoff") | Out-Null
    } else {
      Skip "Repo URL already recorded in 04-HANDOFF.md"
    }
  }

  # ==================================================================
  # 8) Push
  # ==================================================================
  if ($originUrl) {
    Write-Host "  -- Push ---------------------------------------------"
    $out = Run-Native "git" @("push", "-u", "origin", "HEAD")
    if ($script:NativeExit -eq 0) { Done "Pushed to origin" }
    else {
      Warn "Push failed - run 'git push -u origin $DefaultBranch' manually once connectivity/auth is sorted:"
      Write-Host "      $out" -ForegroundColor DarkGray
    }
  }
}

# ====================================================================
# Summary
# ====================================================================
Write-Host ""
Write-Host "  =====================================================" -ForegroundColor DarkYellow
Write-Host "   Bootstrap complete." -ForegroundColor Yellow
Write-Host "  =====================================================" -ForegroundColor DarkYellow
Write-Host "   Next:"
Write-Host "    1. Open PROJECT KNOWLEDGE\01-VISION-AND-DESIGN.md and fill in"
Write-Host "       the one-liner + goals (or have Claude interview you for it)."
Write-Host "    2. Seed PROJECT KNOWLEDGE\03-PUNCH-LIST.md with first work items."
Write-Host "    3. Start working: double-click REMOTE START\Remote-Start.bat"
Write-Host "       (or run 'claude' in the project folder)."
Write-Host "    4. In-session commands now available: /checkpoint (leaving"
Write-Host "       mid-task), /wrapup (finish an item), /health (audit+repair)."
Write-Host ""
Write-Host "   Re-running this bootstrap any time is safe: it only adds"
Write-Host "   missing pieces and refreshes the CLAUDE.md managed block."
Write-Host "   (Full log of this run: PROJECT KIT\logs\)"
Write-Host ""
try { Stop-Transcript | Out-Null } catch {}
if (-not $NonInteractive) { Read-Host "Press Enter to close" }
