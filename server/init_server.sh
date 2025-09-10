#!/bin/bash

# 服务端初始化脚本
echo "=== 服务端初始化开始 ==="

# 设置工作目录
cd /home/spoce/ocr_service

# 激活虚拟环境
source ./venv/bin/activate

# 检查GPU状态
echo "检查GPU状态..."
nvidia-smi

# 检查Python环境
echo "检查Python环境..."
python --version
pip list | grep -E "(paddle|torch|opencv)"

# 测试PaddleOCR导入
echo "测试PaddleOCR导入..."
python -c "
import paddle
print(f'PaddlePaddle版本: {paddle.__version__}')
print(f'GPU可用: {paddle.is_compiled_with_cuda()}')
print(f'GPU设备数: {paddle.device.get_device_count()}')

try:
    from paddleocr import PaddleOCR
    print('PaddleOCR导入成功')
except Exception as e:
    print(f'PaddleOCR导入失败: {e}')
"

# 测试YOLO导入
echo "测试YOLO导入..."
python -c "
try:
    from ultralytics import YOLO
    print('YOLO导入成功')
except Exception as e:
    print(f'YOLO导入失败: {e}')
"

# 检查模型文件
echo "检查模型文件..."
ls -la src/models/

# 测试OCR引擎初始化
echo "测试OCR引擎初始化..."
python -c "
import sys
sys.path.append('src')
try:
    from src.ocr_engine import OCREngine
    print('OCR引擎导入成功')
    # 不实际初始化，避免启动时间过长
    print('OCR引擎类定义正常')
except Exception as e:
    print(f'OCR引擎导入失败: {e}')
"

echo "=== 服务端初始化完成 ==="
