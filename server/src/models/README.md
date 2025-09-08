模型权重放置说明

将以下布局检测权重文件放入本目录：

- doclayout_yolo_ft.pt
- yolov10l_ft.pt

说明：
- 服务端代码已在 `server/src/config.py` 中将模型目录配置为 `server/src/models`。
- 若文件名不同，请同步修改 `LAYOUT_CONFIG` 中的 `model_path` 与 `fallback_model`。
- 若未放置这些文件，服务端将回退到通用YOLO权重，识别效果会变差。


