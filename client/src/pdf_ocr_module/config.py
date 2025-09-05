"""
配置文件 - 包含所有可配置的参数
"""

import os
from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
PICKLES_DIR = BASE_DIR / "pickles"
MODELS_DIR = BASE_DIR / "models"

# 确保目录存在
OUTPUT_DIR.mkdir(exist_ok=True)
PICKLES_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# OCR配置
OCR_CONFIG = {
    "use_gpu": True,
    "det_limit_side_len": 2048,  # 增加分辨率限制，提高识别精度
    "layout": True,               # 启用内置布局检测
    "table": True,                # 启用表格检测
    "det_db_unclip_ratio": 1.8,  # 调整文本检测参数
    "show_log": False,
    "lang": "ch",                 # 指定中文语言
    "use_angle_cls": True,        # 启用角度分类器
    "cls_threshold": 0.9,         # 分类器置信度阈值
    "det_db_thresh": 0.3,         # 文本检测阈值
    "det_db_box_thresh": 0.5      # 文本框检测阈值
}

# 布局检测配置（优先从本地 models 目录加载）
LAYOUT_CONFIG = {
    "model_path": str(MODELS_DIR / "yolov8n.pt"),
    "conf_threshold": 0.25,
    "iou_threshold": 0.45,
    "max_det": 50
}

# 图像处理配置
IMAGE_CONFIG = {
    "target_resolution": 1024,      # 标准分辨率
    "high_resolution": 2560,        # 高分辨率
    "similarity_threshold": 0.8,    # 图片相似度阈值
    "overlap_threshold": 0.3        # 重叠区域阈值
}

# 向量化配置
VECTOR_CONFIG = {
    "model_name": "quentinz/bge-large-zh-v1.5",
    "num_gpu": 0,
    "batch_size": 32,
    "embedding_type": "ollama",  # 可选: "ollama", "openai"
    "max_chunks": 1200            # 生成向量的最大文本块数量上限（防止过慢）
}

# LLM配置
LLM_CONFIG = {
    "base_url": "http://47.76.75.25:9000/v1",
    "api_key": "sk-wMGxvunANdPMxw7Y64F759Fc0b7b4623B34aA80f3f3fA88f",
    "model_name": "gpt-4o-mini",
    "max_tokens": 4000,
    "temperature": 0.1
}

# Milvus配置
MILVUS_CONFIG = {
    "host": "localhost",
    "port": "19530",
    "collection_prefix": "pdf_docs_"
}

# 服务器配置
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8888,
    "reload": True,
    "log_level": "info"
}

# OpenAI配置（备用）
OPENAI_CONFIG = {
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "api_key": "76c0d463408b4d4480c6ea9833aaca89.hdH93QfY9p17AUKD",
    "model_name": "text-embedding-ada-002"
}

# 提示词模板
PROMPTS = {
    "summary": "请总结以下文本的主要内容，提取关键信息：\n{context}",
    "keyword": "请从以下文本中提取5-10个关键词：\n{context}",
    "hybrid": "请分析以下文本，提供结构化的要点总结：\n{context}",
    "markdown": "请将以下文本转换为Markdown格式：\n{context}",
    "part_summary": "请对以下段落进行简洁总结：\n{context}",
    "charts": "请判断这个图像是否包含有用的图表或数据可视化内容。如果是，请返回true；如果不是，请返回false。"
}

# 文件类型支持
SUPPORTED_FORMATS = ['.pdf']

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    "file": str(BASE_DIR / "logs" / "pdf_ocr.log")
}

# 确保日志目录存在
(BASE_DIR / "logs").mkdir(exist_ok=True)

# 远程OCR配置
REMOTE_OCR_CONFIG = {
    "enabled": False,  # 是否启用远程OCR
    "server_url": "http://192.168.3.133:8888",  # 远程OCR服务器地址
    "timeout": 300,  # 请求超时时间（秒）
    "retry_times": 3,  # 重试次数
    "fallback_to_local": True  # 远程失败时是否回退到本地
}
