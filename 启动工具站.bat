@echo off
chcp 65001 >nul
title AI-Mask 智能文件脱敏站
cd /d "%~dp0"

echo =======================================================
echo          🛡️ AI-Mask 智能文件脱敏站 启动中...
echo =======================================================
echo.
echo 将自动检测端口占用；若 8000 被其他服务抢走，
echo 会改用空闲端口，并在下方打印真实访问地址。
echo.
echo 说明：若浏览器出现 {"detail":"Not Found"}，
echo 多半是 127.0.0.1:8000 被别的进程/幽灵端口占用，
echo 请看控制台打印的实际端口，或运行 python run.py。
echo.

:: 推荐走 run.py（含端口冲突检测与自动换端口）
python run.py
if errorlevel 1 (
  echo.
  echo 启动失败。也可手动指定端口，例如：
  echo   set AIMASK_PORT=8001
  echo   python run.py
  echo.
)

pause
