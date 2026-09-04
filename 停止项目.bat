@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo 正在停止业务服务和 Docker 基础服务...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_full_service.ps1" -StopInfrastructure
if errorlevel 1 (
  echo 停止过程中出现错误，请检查终端信息。
  pause
  exit /b 1
)

echo 项目已经停止。
pause
