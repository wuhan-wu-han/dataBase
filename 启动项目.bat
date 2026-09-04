@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ========================================
echo   安塞区城市安全生命线平台 - 一键启动
echo ========================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_full_service.ps1" -Rebuild
if errorlevel 1 (
  echo.
  echo 启动失败，请查看 logs 目录中的错误日志。
  pause
  exit /b 1
)

echo.
echo 系统启动成功：http://localhost:5173/login
start "" "http://localhost:5173/login"
pause
