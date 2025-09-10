#!/bin/bash
# Linux服务器部署脚本
# 用于在192.168.3.133上部署GPU OCR服务

set -e

echo "🚀 开始部署GPU OCR服务到Linux服务器..."

# 脚本所在目录（用于拷贝代码与查找requirements）
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

# 检查Python版本
echo "检查Python版本..."
python3 --version

# 创建项目目录
PROJECT_DIR="/home/spoce/ocr_service"
echo "创建项目目录: $PROJECT_DIR"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 创建虚拟环境
echo "创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装系统依赖（Ubuntu/Debian，兼容新旧包名；可通过 SKIP_APT=1 跳过）
if [ "${SKIP_APT}" != "1" ]; then
  echo "安装系统依赖... (设置 SKIP_APT=1 可跳过此步骤)"
  export DEBIAN_FRONTEND=noninteractive
  sudo apt-get update -y || true

  # 优先安装更通用的包名，失败不终止（避免因/boot空间不足触发initramfs失败而中断）
  sudo apt-get install -y --no-install-recommends \
      libgl1 \
      libglib2.0-0 \
      libsm6 \
      libxext6 \
      libxrender1 \
      libgomp1 \
      libgcc-s1 \
      wget \
      curl || true

  # 尝试兼容变体
  sudo apt-get install -y --no-install-recommends libglib2.0-0t64 || true
  sudo apt-get install -y --no-install-recommends libxrender-dev || true
  # 已切换为opencv-headless，通常不再需要mesa；如存在则安装，否则忽略
  sudo apt-get install -y --no-install-recommends libgl1-mesa-glx || true
else
  echo "已跳过系统依赖安装 (SKIP_APT=1)"
fi

# 同步代码到部署目录（排除venv与日志）
echo "同步代码到部署目录..."
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude "venv" \
    --exclude "logs" \
    --exclude ".git" \
    --exclude ".gitignore" \
    "$SCRIPT_DIR/" "$PROJECT_DIR/"
else
  # rsync 不可用则使用cp（不删除旧文件）
  cp -r "$SCRIPT_DIR"/* "$PROJECT_DIR"/ || true
fi

# 安装Python依赖（优先使用 requirements_linux.txt）
echo "安装Python依赖..."
if [ -f "requirements_linux.txt" ]; then
  REQ_FILE="requirements_linux.txt"
elif [ -f "requirements.txt" ]; then
  REQ_FILE="requirements.txt"
elif [ -f "$SCRIPT_DIR/requirements_linux.txt" ]; then
  REQ_FILE="$SCRIPT_DIR/requirements_linux.txt"
elif [ -f "$SCRIPT_DIR/requirements.txt" ]; then
  REQ_FILE="$SCRIPT_DIR/requirements.txt"
elif [ -f "server/requirements_linux.txt" ]; then
  REQ_FILE="server/requirements_linux.txt"
elif [ -f "server/requirements.txt" ]; then
  REQ_FILE="server/requirements.txt"
else
  echo "未找到 requirements 文件，请确认已上传 server/ 目录" && exit 1
fi

# 先安装主依赖（不含paddleocr）
pip install -r "$REQ_FILE"

# 单独安装 paddleocr，避免其强制旧版PyMuPDF依赖
# 注：2.7.0.3 与 Paddle 2.6.1 兼容；--no-deps 以我们的版本为准
pip install --no-deps paddleocr==2.7.0.3

# 显式安装 doclayout-yolo 与 huggingface_hub，避免Ultralytics运行时自动安装
pip install --no-cache-dir doclayout-yolo || pip install --no-cache-dir doclayout_yolo || true
pip install --no-cache-dir "huggingface_hub>=0.20.0" || true

# 创建必要的目录
echo "创建必要目录..."
mkdir -p logs
mkdir -p models
mkdir -p src/pickles
mkdir -p src/output

# 下载模型文件（如果需要）
echo "检查模型文件..."
if [ ! -f "models/yolov8n.pt" ]; then
    echo "下载YOLO模型..."
    wget -O models/yolov8n.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
fi

# 设置权限
echo "设置文件权限..."
chmod +x remote_ocr_server.py
chmod 755 logs
chmod 755 models

# 创建systemd服务文件
echo "创建systemd服务..."
sudo tee /etc/systemd/system/ocr-service.service > /dev/null <<EOF
[Unit]
Description=GPU OCR Service
After=network.target

[Service]
Type=simple
User=spoce
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=ULTRALYTICS_AUTO_INSTALL=0
ExecStart=$PROJECT_DIR/venv/bin/python remote_ocr_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable ocr-service

echo "✅ 部署完成！"
echo ""
echo "启动服务:"
echo "  sudo systemctl start ocr-service"
echo ""
echo "查看状态:"
echo "  sudo systemctl status ocr-service"
echo ""
echo "查看日志:"
echo "  sudo journalctl -u ocr-service -f"
echo ""
echo "停止服务:"
echo "  sudo systemctl stop ocr-service"
echo ""
echo "服务将在 http://0.0.0.0:8888 启动"
