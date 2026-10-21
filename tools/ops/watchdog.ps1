<#
.SYNOPSIS
  Run the learner's watchdog (tools/ops/watchdog.py) once, and show the Windows notifications it asks for.

.DESCRIPTION
  WHY A POWERSHELL WRAPPER (backlog O1, build spec S1-4): the scheduled task Pokebot-Ops-Watchdog runs THIS file every
  30 minutes, not the python, for two reasons.
  - A watchdog that cannot run must not look like a quiet one. If python cannot be started, or watchdog.py exits with
    anything but 0, this script writes "NEEDS YOU: watchdog could not run" (and why) into the same status file and its
    fallback copy, and toasts it. A python-only watchdog could never report its own missing interpreter.
  - The toast. Windows 11 Home has no msg.exe; Windows PowerShell 5.1 can reach the WinRT ToastNotificationManager.
    watchdog.py prints one "NOTIFY<TAB>title<TAB>body" line per toast it owes (it decides WHEN: only when a NEW
    problem appears, one reminder a day, one "recovered" when none is left; a problem that merely resolves while
    others remain is written to the file, not toasted); this script shows them. A toast that fails falls back to the
    file.

  This script's OWN failure toast follows the same rule: the first failure toasts, a repeat within 24 h does not
  (marker: watchdog_ps1_failed.txt in the ops folder), and the first good run after a failure removes the marker and
  toasts once that the watchdog runs again.

  Paths: the status file is LEARNER-STATUS.txt on the Desktop, resolved with [Environment]::GetFolderPath('Desktop')
  (OneDrive-redirected on this PC); the ops folder is %LOCALAPPDATA%\pokebot-ops. It writes NOTHING in the learner's
  clone (watchdog.py refuses to, and this script writes only the status file, its fallback and the marker).

  Parameters (the scheduled task passes none):
    -Python PATH    the py launcher to run (default py.exe; it is called with -3.12 -B)
    -Out FILE       the status file (default <Desktop>\LEARNER-STATUS.txt)
    -OpsDir DIR     the ops folder (default %LOCALAPPDATA%\pokebot-ops)
    -NoToast        print "WOULD TOAST: title | body" instead of showing a toast (the selftest uses it)
    -TestToast      show ONE test toast and exit: the human check that a toast reaches the user on this PC
  Anything else on the command line is passed to watchdog.py unchanged (e.g. --config FILE --recheck-seconds 0).

  ASCII only on purpose: Windows PowerShell 5.1 reads a BOM-less .ps1 as Windows-1252.
#>
param(
    [string]$Python = 'py.exe',
    [string]$Out = '',
    [string]$OpsDir = '',
    [switch]$NoToast,
    [switch]$TestToast
)

$ErrorActionPreference = 'Continue'
$pyScript = Join-Path $PSScriptRoot 'watchdog.py'
if (-not $OpsDir) { $OpsDir = Join-Path $env:LOCALAPPDATA 'pokebot-ops' }
if (-not $Out) {
    $desk = [Environment]::GetFolderPath('Desktop')
    if ($desk) { $Out = Join-Path $desk 'LEARNER-STATUS.txt' }
}
$fallback = Join-Path $OpsDir 'LEARNER-STATUS.txt'
$failMarker = Join-Path $OpsDir 'watchdog_ps1_failed.txt'

function Show-Toast([string]$Title, [string]$Body) {
    if ($NoToast) { Write-Output "WOULD TOAST: $Title | $Body"; return }
    try {
        [void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
        [void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]
        $t = [Security.SecurityElement]::Escape($Title)
        $b = [Security.SecurityElement]::Escape($Body)
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml("<toast><visual><binding template=`"ToastGeneric`"><text>$t</text><text>$b</text></binding></visual></toast>")
        $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
        # Windows PowerShell's own registered app id: an unregistered id shows nothing on Windows 10/11.
        $appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
        Write-Output "TOASTED: $Title"
    } catch {
        Write-Output "TOAST FAILED (the status file is the record): $($_.Exception.Message)"
    }
}

function Write-StatusFile([string]$Path, [string]$Text) {
    if (-not $Path) { return }
    try {
        $dir = Split-Path -Parent $Path
        if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
        $tmp = "$Path.tmp"
        [IO.File]::WriteAllText($tmp, $Text, (New-Object Text.UTF8Encoding $false))
        Move-Item -LiteralPath $tmp -Destination $Path -Force
    } catch {
        Write-Output "WARN could not write ${Path}: $($_.Exception.Message)"
    }
}

if ($TestToast) {
    Show-Toast 'Pokebot watchdog: test' 'If you can read this, the learner watchdog can reach you with a notification.'
    exit 0
}

$pyArgs = @('-3.12', '-B', $pyScript, '--ops-dir', $OpsDir)
if ($Out) { $pyArgs += @('--out', $Out) }
$pyArgs += $args

$failed = $null
$lines = @()
if ($null -eq (Get-Command $Python -ErrorAction SilentlyContinue)) {
    $failed = "the python launcher '$Python' was not found"
} else {
    try {
        $env:PYTHONIOENCODING = 'utf-8'
        [Console]::OutputEncoding = New-Object Text.UTF8Encoding $false
    } catch { }
    try {
        $lines = @(& $Python @pyArgs 2>&1 | ForEach-Object { "$_" })
        $code = $LASTEXITCODE
        if ($code -ne 0) {
            $tail = ($lines | Select-Object -Last 3) -join ' / '
            $failed = "watchdog.py exited with code ${code}: $tail"
        }
    } catch {
        $failed = "could not start ${Python}: $($_.Exception.Message)"
    }
}

if ($failed) {
    $when = (Get-Date).ToString('h:mm tt')
    $text = "NEEDS YOU: watchdog could not run`r`n" +
            "checked $when (this PC's time), next in 30 min`r`n" +
            "why: $failed`r`n" +
            "The learner itself may be fine. To see the error, run: py -3.12 -B `"$pyScript`"`r`n"
    Write-StatusFile $Out $text
    Write-StatusFile $fallback $text
    Write-Output $text
    $owe = $true
    if (Test-Path -LiteralPath $failMarker) {
        $age = (Get-Date) - (Get-Item -LiteralPath $failMarker).LastWriteTime
        if ($age.TotalHours -lt 24) { $owe = $false }
    }
    if ($owe) {
        Show-Toast 'Pokebot learner: NEEDS YOU' "watchdog could not run: $failed"
        try {
            if (-not (Test-Path -LiteralPath $OpsDir)) { New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null }
            Set-Content -LiteralPath $failMarker -Value "first toasted $(Get-Date -Format o): $failed" -Encoding ASCII
        } catch {
            Write-Output "WARN could not write $failMarker"
        }
    }
    exit 1
}

foreach ($l in $lines) {
    if ($l.StartsWith("NOTIFY`t")) {
        $parts = $l.Split("`t", 3)
        $body = if ($parts.Count -ge 3) { $parts[2] } else { '' }
        Show-Toast $parts[1] $body
    } else {
        Write-Output $l
    }
}
if (Test-Path -LiteralPath $failMarker) {
    Remove-Item -LiteralPath $failMarker -Force -ErrorAction SilentlyContinue
    Show-Toast 'Pokebot learner: watchdog runs again' 'The watchdog could not run before; it runs again now. See LEARNER-STATUS.txt on the Desktop.'
}
exit 0
