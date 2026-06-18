@echo off
setlocal

set "PORT=%~1"
set "SCRIPT_DIR=%~dp0"
set "SOURCE_DIR=%SCRIPT_DIR%Source"
set "UPLOAD_RETRIES=5"

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
echo Sending exit command to Pico console...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s = [System.IO.Ports.SerialPort]::new('%PORT%', 115200); $s.ReadTimeout = 500; $s.WriteTimeout = 500; try { $s.Open(); Start-Sleep -Milliseconds 200; $s.WriteLine('exit'); Start-Sleep -Milliseconds 500; $s.Close(); exit 0 } catch { if ($s.IsOpen) { $s.Close() }; Write-Host $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo [WARN] Could not send exit to %PORT%. The port may be busy.
)
timeout /t 1 /nobreak >nul

echo Resetting Pico before upload...
mpremote connect "%PORT%" reset
if errorlevel 1 (
    echo [ERROR] Could not stop the program already running on Pico.
    echo [ERROR] The Pico is probably running an old main.py that restarts after Ctrl+C.
    echo.
    echo Recovery:
    echo   1. Unplug Pico.
    echo   2. Hold BOOTSEL and plug it back in.
    echo   3. Copy flash_nuke.uf2 to the RPI-RP2 drive.
    echo   4. Hold BOOTSEL again and copy the MicroPython UF2 to RPI-RP2.
    echo   5. Run this script again with the new COM port.
    echo.
    echo After this upload succeeds, the new main.py will stop on Ctrl+C and also supports
    echo safe boot by holding GP22 to GND during reset.
    exit /b 1
)
echo Waiting for %PORT% to become available...
timeout /t 2 /nobreak >nul

for %%F in ("%SOURCE_DIR%\*.py") do (
    echo   %%~nxF
    call :upload_file "%%~fF" "%%~nxF"
    if errorlevel 1 (
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

:upload_file
set "LOCAL_FILE=%~1"
set "REMOTE_FILE=%~2"
set /a ATTEMPT=1

:upload_retry
mpremote connect "%PORT%" fs cp "%LOCAL_FILE%" ":%REMOTE_FILE%"
if not errorlevel 1 exit /b 0

if %ATTEMPT% GEQ %UPLOAD_RETRIES% (
    echo [ERROR] Failed to upload %REMOTE_FILE%.
    echo [HINT] Close Thonny or any serial monitor that may be using %PORT%.
    echo [HINT] If the Pico is running an older main.py, it may block mpremote raw REPL.
    echo [HINT] Stop the program or erase/reinstall MicroPython once, then run this script again.
    exit /b 1
)

echo [WARN] Upload failed, retrying in 1 second... [%ATTEMPT%/%UPLOAD_RETRIES%]
set /a ATTEMPT+=1
timeout /t 1 /nobreak >nul
goto upload_retry
