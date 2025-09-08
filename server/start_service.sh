#!/bin/bash
# 启动OCR服务的简单脚本

cd /home/spoce/ocr_service
source venv/bin/activate

echo "🚀 启动GPU OCR服务..."
echo "服务地址: http://0.0.0.0:8888"
echo "按 Ctrl+C 停止服务"
echo ""

python remote_ocr_server.py
