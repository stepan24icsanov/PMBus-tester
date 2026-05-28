@echo off
setlocal

set "PORT=%~1"
set "SCRIPT_DIR=%~dp0"
set "SOURCE_DIR=%SCRIPT_DIR%Source"

if "%PORT%"=="" (
    echo Usage: upload_to_pico.bat COM_PORT
    echo Example: upload_to_pico.bat COM3
    exit /b 1
)

where mpremote >nul 2>nul
if errorlevel 1 (
    echo [ERROR] mpremote not found.
    echo Install it with: py -m pip install mpremote
    exit /b 1
)

if not exist "%SOURCE_DIR%\*.py" (
    echo [ERROR] Python files not found in "%SOURCE_DIR%".
    exit /b 1
)

echo Uploading files from "%SOURCE_DIR%" to Raspberry Pi Pico on %PORT%...

for %%F in ("%SOURCE_DIR%\*.py") do (
    echo   %%~nxF
    mpremote connect "%PORT%" fs cp "%%~fF" ":%%~nxF"
    if errorlevel 1 (
        echo [ERROR] Failed to upload %%~nxF.
        exit /b 1
    )
)

echo Resetting Pico...
mpremote connect "%PORT%" reset
if errorlevel 1 (
    echo [WARN] Files uploaded, but reset failed.
    exit /b 0
)

echo Done.
exit /b 0
