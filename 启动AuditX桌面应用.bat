@echo off
setlocal
cd /d "%~dp0"
echo [AuditX] Starting desktop app...
echo [AuditX] This window will stay open so you can see logs.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_desktop.ps1"
set EXIT_CODE=%ERRORLEVEL%

echo.
if not "%EXIT_CODE%"=="0" (
  echo [AuditX] Startup failed with exit code %EXIT_CODE%.
  echo [AuditX] Please check the logs above.
) else (
  echo [AuditX] Desktop app process exited.
)
echo.
pause
exit /b %EXIT_CODE%
