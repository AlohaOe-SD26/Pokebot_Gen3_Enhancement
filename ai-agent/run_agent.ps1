# Keeps the Emerald AI learner running 24/7. Start it from a PowerShell window:
#     cd "C:\Remote Projects\Pokebot_Gen3_Enhancement\ai-agent"; .\run_agent.ps1
# To stop cleanly: create a file named STOP in this folder. The running cycle finishes its batch (up to
# cycle_minutes), then the learner exits. Closing this window instead stops the loop, and the batch's
# game lanes may keep running until their time limit.
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = '1'
while ($true) {
    if (Test-Path "$PSScriptRoot\STOP") { Write-Host "STOP file found; exiting."; break }
    py -3.12 learner.py run
    $code = $LASTEXITCODE
    if ($code -eq 0) { Write-Host "Learner exited normally (STOP, a pause, or ATTENTION.md). Not restarting."; break }
    if ($code -eq 2) { Write-Host "Another learner is already running. Not starting a second one."; break }
    Write-Host "Learner exited with code $code; restarting in 10 minutes."
    Start-Sleep -Seconds 600
}
