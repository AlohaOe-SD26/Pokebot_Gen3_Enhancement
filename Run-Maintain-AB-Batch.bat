@echo off
REM ============================================================================
REM  Run-Maintain-AB-Batch.bat
REM  ---------------------------------------------------------------------------
REM  Runs the #24-maintain A/B as TWO batches, back to back, unattended.
REM
REM  JUST DOUBLE-CLICK IT. It figures out where it is, so it works on any PC and
REM  from any folder - you only have to keep it in the repo ROOT (next to
REM  CLAUDE.md and README.md).
REM
REM  WHAT IT DOES, and why each part matters:
REM    ARM ON   POKEBOT_MAINTAIN=1   maintenance is LIVE
REM    ARM OFF  POKEBOT_MAINTAIN     removed entirely - the shipped default
REM
REM  !! THE WHOLE POINT OF THIS SCRIPT IS THE ENVIRONMENT VARIABLE. In PowerShell
REM  or a normal command window, "set POKEBOT_MAINTAIN=1" STAYS SET for the rest
REM  of that window's life. If ARM OFF inherits it, BOTH arms are really ARM ON,
REM  the two results look identical, and that reads as "the feature does nothing"
REM  - a FALSE result, which is worse than no result at all. This script uses
REM  SETLOCAL so the variable cannot leak, and clears it explicitly before ARM
REM  OFF instead of trusting that it was never set.
REM
REM  It also:
REM    * forces --build sandbox (the custom build has no telemetry, so a batch
REM      run against it cannot answer the question)
REM    * gives both arms the SAME lanes and minutes, so nobody can attribute a
REM      difference to one arm getting more time
REM    * writes ARM-ON.txt / ARM-OFF.txt into each result folder, so which batch
REM      is which can never be guessed wrong afterwards
REM    * prints both folder names at the end - send those to Claude
REM
REM  OPTIONAL: you can pass lanes and minutes, e.g.
REM      Run-Maintain-AB-Batch.bat 4 60
REM  Defaults are 8 lanes and 180 minutes PER ARM (so about 6 hours total).
REM ============================================================================

setlocal EnableExtensions EnableDelayedExpansion

REM --- work out where we are, no matter where the repo lives -------------------
set "REPO=%~dp0"
if "%REPO:~-1%"=="\" set "REPO=%REPO:~0,-1%"
set "TOOLS=%REPO%\tools\story-dev"
set "RUNNER=%TOOLS%\x4_headless.py"

echo(
echo ============================================================================
echo   #24-maintain A/B  -  two batches, run back to back
echo ============================================================================
echo   repo   : %REPO%
echo   runner : %RUNNER%

REM --- settings ---------------------------------------------------------------
set "LANES=%~1"
set "MINUTES=%~2"
if "%LANES%"==""   set "LANES=8"
if "%MINUTES%"=="" set "MINUTES=180"

REM --- sanity checks BEFORE committing hours to this ---------------------------
if not exist "%RUNNER%" (
  echo(
  echo   [X] Could not find the batch runner:
  echo       %RUNNER%
  echo(
  echo   This script must sit in the REPO ROOT - the folder that also contains
  echo   CLAUDE.md, README.md and the tools\ folder. Move it there and re-run.
  goto :fail
)

where py >nul 2>&1
if errorlevel 1 (
  echo(
  echo   [X] The Python launcher "py" is not on PATH, so nothing can run.
  echo       Install Python 3.12, or run PROJECT KIT\Install-Environment.bat first.
  goto :fail
)

REM --- warn (do NOT block) if the working tree has uncommitted changes ---------
REM  A batch is only comparable against the code it ran on, and the runner records
REM  the commit. Uncommitted edits make that record say "<commit>-dirty", which is
REM  still usable - you just need to know it.
where git >nul 2>&1
if not errorlevel 1 (
  pushd "%REPO%" >nul 2>&1
  for /f "delims=" %%c in ('git rev-parse --short HEAD 2^>nul') do set "COMMIT=%%c"
  set "DIRTY="
  for /f "delims=" %%d in ('git status --porcelain 2^>nul') do set "DIRTY=1"
  popd >nul 2>&1
  if defined COMMIT echo   commit : !COMMIT!
  if defined DIRTY (
    echo(
    echo   [!] The working tree has UNCOMMITTED CHANGES. The batch will record the
    echo       commit as "-dirty". That is fine, just mention it to Claude.
  )
)

echo(
echo   lanes         : %LANES%   ^(same for both arms^)
echo   minutes/arm   : %MINUTES%
echo   build         : sandbox   ^(forced - custom has no telemetry^)
echo(
echo   ARM 1 = ON    POKEBOT_MAINTAIN=1
echo   ARM 2 = OFF   POKEBOT_MAINTAIN removed
echo(
echo   Nothing else should use the emulator while this runs.
echo   You can leave it alone - it will not ask you anything again.
echo(
set /p "GO=Start now?  (Y = yes, anything else = cancel): "
if /i not "%GO%"=="Y" (
  echo   Cancelled. Nothing was run.
  goto :done
)

set "PYTHONUTF8=1"
set "ARMON_DIR=(not recorded)"
set "ARMOFF_DIR=(not recorded)"

REM ============================ ARM 1 - ON =====================================
echo(
echo ----------------------------------------------------------------------------
echo  ARM 1 of 2 - MAINTENANCE ON        (started %TIME%)
echo ----------------------------------------------------------------------------
set "POKEBOT_MAINTAIN=1"
pushd "%TOOLS%"
py -3.12 x4_headless.py --build sandbox --lanes %LANES% --minutes %MINUTES%
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" echo   [!] ARM 1 exited with code %RC% - keep the folder anyway, Claude can read it.

call :stamp_newest "ARM-ON" "POKEBOT_MAINTAIN=1"
set "ARMON_DIR=%NEWEST%"

REM ============================ ARM 2 - OFF ====================================
REM  Cleared EXPLICITLY. Do not rely on "I never set it" - that is exactly the
REM  mistake this script exists to make impossible.
set "POKEBOT_MAINTAIN="

echo(
echo ----------------------------------------------------------------------------
echo  ARM 2 of 2 - MAINTENANCE OFF       (started %TIME%)
echo ----------------------------------------------------------------------------
pushd "%TOOLS%"
py -3.12 x4_headless.py --build sandbox --lanes %LANES% --minutes %MINUTES%
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" echo   [!] ARM 2 exited with code %RC% - keep the folder anyway, Claude can read it.

call :stamp_newest "ARM-OFF" "POKEBOT_MAINTAIN not set"
set "ARMOFF_DIR=%NEWEST%"

REM ================================ DONE =======================================
echo(
echo ============================================================================
echo   BOTH ARMS FINISHED
echo ============================================================================
echo(
echo   Send Claude these two folder names:
echo(
echo      ARM ON   : !ARMON_DIR!
echo      ARM OFF  : !ARMOFF_DIR!
echo(
echo   They are under:
echo      %TOOLS%\x4-runs\
echo(
echo   Each folder now contains an ARM-ON.txt or ARM-OFF.txt saying which it is,
echo   so the pairing cannot be lost or guessed wrong later.
echo(
goto :done

REM --------------------------------------------------------------------------
REM  :stamp_newest  <label>  <description>
REM  Finds the newest x4-runs folder and drops a marker file in it naming the arm.
REM  Done AFTER each arm rather than before, because the runner picks its own
REM  timestamped folder name and only creates it when it starts.
REM --------------------------------------------------------------------------
:stamp_newest
set "NEWEST="
for /f "delims=" %%i in ('dir /b /ad /o-d "%TOOLS%\x4-runs" 2^>nul') do (
  set "NEWEST=%%i"
  goto :stamp_got
)
:stamp_got
if not defined NEWEST (
  set "NEWEST=(no batch folder found)"
  echo   [!] Could not find a result folder to label for %~1.
  goto :eof
)
> "%TOOLS%\x4-runs\!NEWEST!\%~1.txt" echo %~1
>> "%TOOLS%\x4-runs\!NEWEST!\%~1.txt" echo environment: %~2
>> "%TOOLS%\x4-runs\!NEWEST!\%~1.txt" echo lanes: %LANES%   minutes: %MINUTES%   build: sandbox
>> "%TOOLS%\x4-runs\!NEWEST!\%~1.txt" echo written by Run-Maintain-AB-Batch.bat
echo   labelled: x4-runs\!NEWEST!  =  %~1
goto :eof

:fail
echo(
echo   Nothing was run.
:done
echo(
pause
endlocal
