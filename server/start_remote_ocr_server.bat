@echo off
echo 启动远程GPU OCR服务器...
echo 服务器地址: 192.168.3.133:8888
echo.

REM 检查Python环境
python --version
if %errorlevel% neq 0 (
    echo 错误: Python未安装或未添加到PATH
    pause
    exit /b 1
)

REM 安装依赖
echo 安装依赖包...
pip install fastapi uvicorn requests

REM 启动服务器
echo 启动OCR服务器...
python remote_ocr_server.py

pause
