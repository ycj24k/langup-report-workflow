@echo off
chcp 65001
echo ========================================
echo 研报文件分类管理系统 - 安装脚本
echo ========================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到python命令，请确保已安装Python 3.6或更高版本
    echo 并且python命令可用
    pause
    exit /b 1
)

echo Python环境检查通过
echo.

echo 正在安装依赖包...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo 错误: 依赖包安装失败
    echo 请检查网络连接或尝试手动安装
    pause
    exit /b 1
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 使用说明:
echo 1. 运行 run.bat 启动程序
echo 2. 或直接运行: python main.py
echo.
echo 注意事项:
echo 1. 请确保网络盘 \\NAS\study\study 可访问
echo 2. 请配置数据库连接信息 (config.py)
echo 3. 首次运行会自动创建数据库和表
echo.
pause