<#
.SYNOPSIS
  Register (or remove) the learner's ops scheduled tasks. DEFAULT IS A DRY RUN: it only PRINTS what it would do.

.DESCRIPTION
  WHY: the nightly backup (backlog O4, spec S1-2) and the 30-minute watchdog (S1-4) must run with no Claude session and
  no human. Registering a scheduled task is a SYSTEM change, so this script never makes it unless -Apply is given,
  and -Apply is used only after the user says yes.

  - The tasks run the DEPLOYMENT CLONE's copy of tools/ops (C:\Remote Projects\pokebot-learner\tools\ops), never this
    checkout's, so work in progress here cannot break the nightly. The clone gets tools/ by its own fast-forward.
  - They run "pyw.exe -3.12 -B": -B so no __pycache__ is written into the clone (a stray file there is harmless, but
    the clone stays exactly as git left it), and pyw.exe (the windowless launcher) so no console window flashes on
    the desktop at 1 AM (review finding 8). backup_learner.py's record is its status file, so it needs no console;
    tools/status.py prints that file as its one BACKUP line (ok / NEEDS-YOU / REFUSED and why).
    If pyw.exe is missing, the script falls back to py.exe and SAYS so (a window will then open each night).
    The watchdog task is the exception: it runs powershell.exe on tools\ops\watchdog.ps1 (hidden window), because
    that wrapper reports a python that cannot run and shows the toast; see its entry in the task table.
  - Idempotent: -Apply replaces an existing task of the same name with the same definition (Register -Force).

  Modes (every mode previews unless -Apply is given):
    .\install_ops_tasks.ps1                    preview the install (WhatIf)
    .\install_ops_tasks.ps1 -Apply             register / update the tasks
    .\install_ops_tasks.ps1 -Uninstall         preview the removal
    .\install_ops_tasks.ps1 -Uninstall -Apply  remove the tasks

  ASCII only on purpose: Windows PowerShell 5.1 reads a BOM-less .ps1 as Windows-1252.
#>
param(
    [switch]$Apply,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$cfgPath = Join-Path $PSScriptRoot 'ops_config.json'
$cfg = Get-Content -Raw -Path $cfgPath | ConvertFrom-Json
$agentDir = $cfg.clone -replace '/', '\'
$cloneRoot = Split-Path -Parent $agentDir
$opsDir = Join-Path $cloneRoot 'tools\ops'
# The WINDOWLESS launcher first (no console flashes at 1 AM); py.exe only as a fallback that is printed, never silent.
$launcherNote = 'pyw.exe (windowless: no console window opens when the task runs)'
$pyw = Get-Command 'C:\Windows\pyw.exe' -ErrorAction SilentlyContinue
if ($null -eq $pyw) { $pyw = Get-Command pyw.exe -ErrorAction SilentlyContinue }
if ($null -ne $pyw) {
    $pyPath = $pyw.Source
} else {
    $py = (Get-Command py.exe -ErrorAction SilentlyContinue)
    $pyPath = if ($null -ne $py) { $py.Source } else { 'C:\Windows\py.exe' }
    $launcherNote = 'NOTE pyw.exe was not found: falling back to py.exe, so a console window WILL open each time the task runs'
}

# ---------------------------------------------------------------------------------------------- the task table
# Each task: Name, Description, Script (in the clone's tools\ops), Arguments, Trigger, Settings.
$Tasks = @()

# O4 / S1-2: nightly backup of the learner's data off C:. 1:00 AM is a quiet hour, NOT a guaranteed gap between the
# learner's writes: its cycle boundaries drift and reset on every restart (02:23 AM on 10-14, 04:07 AM on 10-21), so
# the backup's millisecond reads can still collide with a state.json replace (see backup_learner.py _open_read).
# StartWhenAvailable runs a missed night (PC off at 1 AM) as soon as the PC is back.
$Tasks += @{
    Name        = 'Pokebot-Ops-Backup'
    Description = 'Nightly zip of the 24/7 learner data (data, findings, inbox, config) to a disk other than C:. tools/ops/backup_learner.py; status in %LOCALAPPDATA%\pokebot-ops\backup_status.json, shown by tools/status.py.'
    Script      = Join-Path $opsDir 'backup_learner.py'
    Arguments   = ''
    Trigger     = { New-ScheduledTaskTrigger -Daily -At '1:00 AM' }
    Settings    = { New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
                        -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries }
    TriggerText = 'daily at 1:00 AM'
    SettingsText = 'StartWhenAvailable; MultipleInstances IgnoreNew; 30-minute limit; runs on battery'
}

# ===== S1-4 WATCHDOG TASK ===============================================================================
# O1 / S1-4: every 30 minutes, the session-free watchdog writes LEARNER-STATUS.txt on the Desktop and toasts ONLY on a
# change of state. It runs watchdog.ps1, not the python: the wrapper is what reports "watchdog could not run" when
# python itself is missing or crashes, and what shows the toast (Windows PowerShell 5.1, WinRT). So this task carries
# its own Execute (powershell.exe) and full Arguments instead of the python launcher line the loop builds by default.
# -WindowStyle Hidden still FLASHES a console for a moment every 30 minutes: whether that is acceptable is a human
# check recorded with the first real toast (watchdog.ps1 -TestToast). The interactive principal the loop uses is the
# spec's "user session only": a toast needs the user's desktop, and nothing runs while the user is logged off.
# The trigger starts at midnight today and repeats every 30 minutes with no end (Windows 10+: an omitted
# RepetitionDuration is indefinite); StartWhenAvailable runs a missed check as soon as the PC is back.
$watchdogPs1 = Join-Path $opsDir 'watchdog.ps1'
$Tasks += @{
    Name        = 'Pokebot-Ops-Watchdog'
    Description = 'Every 30 minutes: checks the 24/7 learner (process, ATTENTION.md, stuck log, disk, restart, backup, held cycles), writes LEARNER-STATUS.txt on the Desktop and toasts only on a change. tools/ops/watchdog.ps1 + watchdog.py; read-only on the clone.'
    Script      = $watchdogPs1
    Execute     = (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe')
    Arguments   = ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $watchdogPs1)
    Trigger     = { New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes 30) }
    Settings    = { New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
                        -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries }
    TriggerText = 'every 30 minutes, from midnight today, with no end'
    SettingsText = 'StartWhenAvailable; MultipleInstances IgnoreNew; 5-minute limit; runs on battery; hidden window (-WindowStyle Hidden)'
}
# ========================================================================================================

$mode = if ($Uninstall) { 'UNINSTALL' } else { 'INSTALL' }
$tag = if ($Apply) { 'APPLY' } else { 'WHATIF (dry run; nothing is changed; pass -Apply to do it)' }
Write-Output "install_ops_tasks.ps1: $mode, $tag"
Write-Output "  deployment clone: $cloneRoot"
Write-Output "  python launcher:  $pyPath"
Write-Output "                    $launcherNote"

$failed = $false
foreach ($t in $Tasks) {
    $existing = Get-ScheduledTask -TaskName $t.Name -ErrorAction SilentlyContinue
    # A task with its own Execute (the watchdog's powershell.exe) runs that with its Arguments verbatim; every other
    # task runs the python launcher on its Script.
    if ($t.ContainsKey('Execute')) {
        $exe = $t.Execute
        $argLine = $t.Arguments
    } else {
        $exe = $pyPath
        $argLine = ('-3.12 -B "{0}" {1}' -f $t.Script, $t.Arguments).Trim()
    }
    if ($Uninstall) {
        if ($null -eq $existing) {
            Write-Output "  [$($t.Name)] not registered: nothing to remove"
        } elseif ($Apply) {
            Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false
            Write-Output "  [$($t.Name)] REMOVED"
        } else {
            Write-Output "  [$($t.Name)] would REMOVE the registered task"
        }
        continue
    }
    $verb = if ($null -eq $existing) { 'CREATE' } else { 'REPLACE (same name; idempotent)' }
    Write-Output "  [$($t.Name)] would $verb"
    Write-Output "      run:      `"$exe`" $argLine"
    Write-Output "      in:       $opsDir"
    Write-Output "      when:     $($t.TriggerText)"
    Write-Output "      settings: $($t.SettingsText)"
    Write-Output "      as:       $env:USERNAME (interactive session: it does not run while the user is logged off)"
    if (-not (Test-Path -LiteralPath $t.Script)) {
        Write-Output "      WARN the clone has no $($t.Script) yet: it arrives on the clone's next fast-forward after this is pushed."
        if ($Apply) {
            Write-Output "      REFUSED: a task pointing at a missing script would fail every night."
            $failed = $true
            continue
        }
    }
    if ($Apply) {
        $action = New-ScheduledTaskAction -Execute $exe -Argument $argLine -WorkingDirectory $opsDir
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
        Register-ScheduledTask -TaskName $t.Name -Description $t.Description -Action $action `
            -Trigger (& $t.Trigger) -Settings (& $t.Settings) -Principal $principal -Force | Out-Null
        Write-Output "      REGISTERED"
    }
}
if (-not $Apply) { Write-Output "WHATIF: no scheduled task was created, changed or removed." }
if ($failed) { exit 1 }
exit 0
