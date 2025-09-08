@echo off
echo 上传服务端代码到Linux服务器...
echo.

REM 使用scp上传文件（需要安装OpenSSH或使用Git Bash）
echo 方法1: 使用scp命令（推荐）
echo scp -r -P 22 server/* spoce@192.168.3.133:/home/spoce/ocr_service/
echo.

echo 方法2: 使用WinSCP等图形化工具
echo 1. 下载并安装WinSCP
echo 2. 连接到 192.168.3.133:22
echo 3. 上传server目录下的所有文件到 /home/spoce/ocr_service/
echo.

echo 方法3: 使用XTerminal的文件传输功能
echo 1. 在XTerminal中连接服务器
echo 2. 使用文件传输功能上传server目录
echo.

echo 上传完成后，在服务器上运行：
echo cd /home/spoce/ocr_service
echo chmod +x deploy_linux.sh
echo ./deploy_linux.sh
echo.

pause
