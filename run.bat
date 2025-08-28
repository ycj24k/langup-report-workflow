@echo off
chcp 65001
title 研报文件分类管理系统

echo ========================================
echo 研报文件分类管理系统
echo ========================================
echo.

echo 正在启动程序...
python3 main.py

if errorlevel 1 (
    echo.
    echo 程序异常退出
    echo 如果遇到依赖问题，请先运行 install.bat
)

echo.
pause