@echo off
chcp 65001 >nul
echo 安装研报文件分类管理系统依赖...
echo.

cd /d "%~dp0\.."

echo 正在安装Python依赖包...
pip install -r requirements.txt

echo.
echo 正在安装PDF OCR模块依赖...
pip install -r src/pdf_ocr_module/requirements.txt

echo.
echo 安装完成！
echo 现在可以运行 run.bat 启动程序
pause