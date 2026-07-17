@echo off
:: Install-Environment.bat - DOUBLE-CLICK ME FIRST (one time per computer).
:: Sets up everything Claude Code needs: Git, GitHub CLI, and Claude Code.
:: This wrapper asks Windows for administrator rights (needed to install
:: software), then runs the guided installer. No settings are changed
:: permanently; PowerShell's execution policy is bypassed for this run only.
powershell -NoLogo -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoLogo','-ExecutionPolicy','Bypass','-File','\"%~dp0Install-Environment.ps1\"'"
