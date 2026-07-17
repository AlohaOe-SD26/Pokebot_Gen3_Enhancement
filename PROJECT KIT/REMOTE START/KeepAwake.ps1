# ============================================================
#  KeepAwake.ps1 — keeps the PC awake while Claude Code runs
#  (Claude Code Project Kit). Started minimized by
#  Remote-Start.bat. Uses SetThreadExecutionState — NO system
#  settings are changed; normal sleep behavior returns the
#  moment Claude Code exits (or if this window is closed).
#  Only system sleep is held — the display may still turn off.
# ============================================================
$ErrorActionPreference = "Continue"
Add-Type -Namespace Kit -Name Power -MemberDefinition @'
[DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern uint SetThreadExecutionState(uint esFlags);
'@
$ES_CONTINUOUS      = [uint32]"0x80000000"
$ES_SYSTEM_REQUIRED = [uint32]"0x00000001"

$LogDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$Log = Join-Path $LogDir ("awake-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
function Note($m) { ("{0}  {1}" -f (Get-Date -Format "HH:mm:ss"), $m) | Add-Content -Path $Log }

# --- session heartbeat (read by the Remote Programs hub) ------------
# While a real Claude session is up we write a small lock file and
# refresh it every poll; the hub shows the project as "running" while
# that heartbeat stays fresh. Removed on exit; the hub's staleness
# window covers hard kills (closed window / crash). This lives in
# KeepAwake - which runs for exactly the session's lifetime - so the
# user's Remote-Start launcher stays untouched.
$ProjectName = Split-Path (Split-Path $PSScriptRoot -Parent) -Leaf
$LockPath    = Join-Path $LogDir "session.lock"
$LockStarted = (Get-Date).ToString("s")
function Update-Lock {
  try {
    $obj = [ordered]@{ schema = 1; keepawake_pid = $PID; started = $LockStarted; heartbeat = (Get-Date).ToString("s"); project = $ProjectName }
    [System.IO.File]::WriteAllText($LockPath, ($obj | ConvertTo-Json -Compress), (New-Object System.Text.UTF8Encoding($false)))
  } catch { Note ("heartbeat write failed: " + $_.Exception.Message) }
}
function Remove-Lock {
  try { if (Test-Path $LockPath) { Remove-Item $LockPath -Force -ErrorAction SilentlyContinue } } catch {}
}

function Test-ClaudeRunning {
  try {
    if (Get-Process -Name "claude*" -ErrorAction SilentlyContinue) { return $true }
    $byCmd = Get-CimInstance Win32_Process -Filter "Name = 'node.exe'" -ErrorAction SilentlyContinue |
             Where-Object { $_.CommandLine -match 'claude' }
    return [bool]$byCmd
  } catch { return $false }
}

$host.UI.RawUI.WindowTitle = "Project Kit - KeepAwake (close me to release the hold)"
Note "KeepAwake started - waiting up to 120s for Claude Code to appear."
Remove-Lock   # clear any stale lock a crashed prior run may have left
$found = $false
for ($i = 0; $i -lt 24; $i++) {
  if (Test-ClaudeRunning) { $found = $true; break }
  Start-Sleep -Seconds 5
}
try {
  if ($found) {
    Note "Claude Code detected - holding system awake (display may still sleep)."
    Update-Lock
    $miss = 0
    while ($miss -lt 2) {   # tolerate one missed poll (~60s) before releasing
      [Kit.Power]::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED) | Out-Null
      Update-Lock           # refresh the heartbeat the hub reads
      Start-Sleep -Seconds 30
      if (Test-ClaudeRunning) { $miss = 0 } else { $miss++ }
    }
    Note "Claude Code no longer running."
  } else {
    Note "Claude Code never appeared within the grace period - nothing to hold."
  }
} finally {
  Remove-Lock
  [Kit.Power]::SetThreadExecutionState($ES_CONTINUOUS) | Out-Null
  Note "Awake hold released - normal sleep behavior restored."
}
