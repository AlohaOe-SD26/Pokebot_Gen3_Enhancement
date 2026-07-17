@echo off
:: Remote-Start.bat — double-click me.  (Project Kit v1.10 enhanced)
:: Step 1: KeepAwake.ps1 (minimized) holds the PC awake while Claude
::         Code runs, so remote sessions don't die to sleep. Released
::         automatically when Claude exits. No settings are changed.
:: Step 2: Git-Sync.ps1 pulls the latest pushed work from your other
::         computers and flags anything a previous session left behind.
:: Step 3: your original Remote-Start.ps1 launches Claude Code with
::         remote control, exactly as before (that file is untouched).
:: Portable: keep this folder inside your project's root folder.
:: PowerShell's execution policy is bypassed for these launches only.
start "" /min powershell -NoLogo -ExecutionPolicy Bypass -File "%~dp0KeepAwake.ps1"
powershell -NoLogo -ExecutionPolicy Bypass -File "%~dp0Git-Sync.ps1"
powershell -NoLogo -ExecutionPolicy Bypass -File "%~dp0Remote-Start.ps1"
