# Linux服务器部署指南

## 服务器信息
- **地址**: 192.168.3.133:22
- **账号**: spoce
- **系统**: Linux (无桌面，仅命令行)

## 部署步骤

### 1. 连接服务器
```bash
# 使用XTerminal或其他SSH客户端连接
ssh spoce@192.168.3.133 -p 22
```

### 2. 上传代码文件
将以下文件上传到服务器：
- `server/` 目录下的所有文件
- 或者使用git克隆（如果代码在git仓库中）

### 3. 环境与依赖（使用已配置的 paddleocr 环境）
在服务器已激活的 paddleocr 环境中（你本机已就绪），仅当缺少以下依赖时再按需安装：
```bash
# 布局检测（必需）
pip install --no-cache-dir ultralytics==8.2.103

# 上传接口所需（若未安装）
pip install --no-cache-dir python-multipart

# 可选：PPTX 支持（解析文本 + 对图片做OCR）
pip install --no-cache-dir python-pptx

# 可选：OpenCV 纯CPU版本（如出现 libGL 报错再装）
pip install --no-cache-dir opencv-python-headless==4.10.0.84
```

### 4. 布局模型与权重
将布局检测权重统一放在目录：`/home/spoce/ocr_service/src/models/`

要求文件名与配置一致：
```
doclayout_yolo_ft.pt
yolov10l_ft.pt
```
配置文件：`server/src/config.py` → `LAYOUT_CONFIG`。
若未放置，将回退到 `yolov8n.pt`（效果较差）。

### 5. 启动服务
```bash
cd /home/spoce/ocr_service
python remote_ocr_server.py
```
启动成功后日志应包含：`🚀 GPU OCR服务启动成功！`。

### 5. 验证服务
```bash
# 检查服务状态
sudo systemctl status ocr-service

# 查看服务日志
sudo journalctl -u ocr-service -f

# 测试API
curl http://localhost:8888/
```

## 服务管理命令

### 启动/停止/重启服务
```bash
sudo systemctl start ocr-service    # 启动
sudo systemctl stop ocr-service     # 停止
sudo systemctl restart ocr-service  # 重启
sudo systemctl status ocr-service   # 查看状态
```

### 查看日志（如以 systemd 部署）
```bash
# 实时查看日志
sudo journalctl -u ocr-service -f

# 查看最近100行日志
sudo journalctl -u ocr-service -n 100

# 查看今天的日志
sudo journalctl -u ocr-service --since today
```

### 开机自启动
```bash
# 启用开机自启动
sudo systemctl enable ocr-service

# 禁用开机自启动
sudo systemctl disable ocr-service
```

## API 接口

服务启动后，常用接口：

- 健康检查: `GET http://192.168.3.133:8888/health`
- GPU 信息: `GET http://192.168.3.133:8888/gpu`
- PDF OCR: `POST http://192.168.3.133:8888/ocr/pdf` (form-data: file)
- 图片 OCR: `POST http://192.168.3.133:8888/ocr/image` (form-data: file)
- PPTX OCR: `POST http://192.168.3.133:8888/ocr/ppt` (form-data: file，需安装 python-pptx)

## API接口

服务启动后，可通过以下接口访问：

- **健康检查**: `GET http://192.168.3.133:8888/`
- **PDF OCR**: `POST http://192.168.3.133:8888/ocr/pdf`
- **PPT OCR**: `POST http://192.168.3.133:8888/ocr/ppt`
- **图片OCR**: `POST http://192.168.3.133:8888/ocr/image`

## 故障排除

### 1. 服务启动失败
```bash
# 查看详细错误信息
sudo journalctl -u ocr-service -n 50

# 直接前台启动看堆栈
cd /home/spoce/ocr_service && python remote_ocr_server.py
```

### 2. GPU不可用
```bash
# 检查CUDA
nvidia-smi

# 检查PyTorch CUDA支持
python -c "import torch; print(torch.cuda.is_available())"
```

### 3. 端口被占用
```bash
# 查看端口占用
sudo netstat -tlnp | grep 8888

# 如需改端口（编辑 remote_ocr_server.py）
# uvicorn.run(app, host="0.0.0.0", port=8889)
```

### 4. 权限问题
```bash
# 检查文件权限
ls -la /home/spoce/ocr_service/

# 修复权限
sudo chown -R spoce:spoce /home/spoce/ocr_service/
chmod +x /home/spoce/ocr_service/remote_ocr_server.py
```

## 更新代码

当需要更新代码时：
```bash
# 方式A：前台运行
cd /home/spoce/ocr_service
# 同步/替换文件后直接重启进程（Ctrl+C 结束，再运行）
python remote_ocr_server.py

# 方式B：如使用 systemd
sudo systemctl stop ocr-service
# 同步文件后
sudo systemctl start ocr-service
```

## 注意事项

1. **防火墙**: 确保8888端口对外开放
2. **GPU内存**: 确保GPU有足够内存运行模型
3. **磁盘空间**: 确保有足够空间存储模型和临时文件
4. **网络**: 确保服务器可以访问外网下载依赖

## PPT 文件处理说明

- PPTX（.pptx）：安装 `python-pptx` 后可直接上传识别；文本直接解析，图片会额外走 OCR 补充。
- PPT（.ppt）：Linux 环境不建议启用 COM 接口，推荐先转换为 PDF 再走 PDF OCR。
  ```bash
  sudo apt-get update && sudo apt-get install -y libreoffice
  libreoffice --headless --convert-to pdf your.ppt --outdir /tmp
  # 将 /tmp/your.pdf 上传至 /ocr/pdf
  ```
