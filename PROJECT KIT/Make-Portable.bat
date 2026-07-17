@echo off
:: Make-Portable.bat — double-click me.
:: Creates a dated offline snapshot of THIS project (full git bundle
:: + a copy of the kit + restore instructions) at a destination you
:: choose, e.g. a USB stick. See PORTABLE-README.txt it generates.
:: PowerShell's execution policy is bypassed for this launch only.
powershell -NoLogo -ExecutionPolicy Bypass -File "%~dp0Make-Portable.ps1"
