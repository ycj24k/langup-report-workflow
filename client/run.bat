@echo off
chcp 65001 >nul
echo 启动研报文件分类管理系统...
echo.

cd /d "%~dp0\.."
python src/main.py

pause