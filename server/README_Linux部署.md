# Linux服务器部署指南

## 服务器信息
- **地址**: 192.168.3.133:22
- **账号**: spoce
- **密码**: langup.cn
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

### 3. 运行部署脚本
```bash
# 进入server目录
cd server

# 给脚本执行权限
chmod +x deploy_linux.sh

# 运行部署脚本
./deploy_linux.sh
```

### 4. 启动服务
```bash
# 方式1：使用systemd服务（推荐）
sudo systemctl start ocr-service

# 方式2：直接运行（用于测试）
chmod +x start_service.sh
./start_service.sh
```

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

### 查看日志
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

## 模型与权重

服务端布局检测模型统一放在目录：`server/src/models/`

请将以下文件放入该目录（文件名需与配置一致）：

- `doclayout_yolo_ft.pt`
- `yolov10l_ft.pt`

相关配置在 `server/src/config.py` 的 `LAYOUT_CONFIG` 中：

```
LAYOUT_CONFIG = {
    "model_path": str(MODELS_DIR / "doclayout_yolo_ft.pt"),
    "fallback_model": str(MODELS_DIR / "yolov10l_ft.pt"),
    ...
}
```

注意：
- 若未放置这些权重，服务端将尝试回退到通用YOLO权重，识别效果可能下降。
- 如更改权重文件名/路径，请同步修改 `LAYOUT_CONFIG`。

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

# 检查Python环境
cd /home/spoce/ocr_service
source venv/bin/activate
python --version
pip list
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

# 修改端口（编辑remote_ocr_server.py）
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
# 停止服务
sudo systemctl stop ocr-service

# 更新代码文件
# （上传新文件或git pull）

# 重启服务
sudo systemctl start ocr-service
```

## 注意事项

1. **防火墙**: 确保8888端口对外开放
2. **GPU内存**: 确保GPU有足够内存运行模型
3. **磁盘空间**: 确保有足够空间存储模型和临时文件
4. **网络**: 确保服务器可以访问外网下载依赖
