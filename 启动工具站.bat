@echo off
chcp 65001 >nul
title AI-Mask 智能文件脱敏站
cd /d "%~dp0"

echo =======================================================
echo          🛡️ AI-Mask 智能文件脱敏站 启动中...
echo =======================================================
echo.
echo 正在启动后端引擎与 Web 控制台 (http://127.0.0.1:8000)...
echo.

:: 延时 2 秒后自动打开默认浏览器
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"

:: 启动 uvicorn 服务
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

pause
