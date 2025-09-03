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
    "det_limit_side_len": 1440,
    "layout": False,
    "table": False,
    "det_db_unclip_ratio": 1.6,
    "show_log": False
}

# 布局检测配置
LAYOUT_CONFIG = {
    "model_path": str(MODELS_DIR / "layout_detection.yaml"),
    "conf_threshold": 0.5,
    "iou_threshold": 0.45
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
    "batch_size": 32
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

# 提示词模板
PROMPTS = {
    "summary": "请总结以下文本的主要内容，提取关键信息：\n{context}",
    "keyword": "请从以下文本中提取5-10个关键词：\n{context}",
    "hybrid": "请分析以下文本，提供结构化的要点总结：\n{context}",
    "markdown": "请将以下文本转换为Markdown格式：\n{context}"
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
