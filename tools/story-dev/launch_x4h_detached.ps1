# Launch x4_headless.py DETACHED from this Claude session (design v2 step 14, T1): through WMI, so the runner is in no
# job object and its parent is WmiPrvSE — this session's processes sit in a kill-on-close job (measured 2026-10-01).
# The runner's own console is hidden; its output is teed to <batch dir>\x4h.txt. Stop it by ending its python.exe
# (its kill-on-close job then ends every lane) or let --minutes end it.
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][double]$Minutes,
    [int]$Lanes = 16
)
$py = "C:\Users\Ripto\AppData\Local\Programs\Python\Python312\python.exe"
$dir = "C:\Remote Projects\Pokebot_Gen3_Enhancement\tools\story-dev"
if (-not (Test-Path $py)) { throw "python not found: $py" }
if (-not (Test-Path "$dir\x4_headless.py")) { throw "runner not found under $dir" }
$cmd = "`"$py`" -X utf8 `"$dir\x4_headless.py`" --build sandbox --lanes $Lanes --minutes $Minutes " +
       "--arms `"$dir\arms\batch14.json`" --profile-tag $Tag"
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $dir }
"ReturnValue=$($r.ReturnValue) pid=$($r.ProcessId)"
"command: $cmd"
