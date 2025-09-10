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

# 布局检测配置（优先使用专业模型）
LAYOUT_CONFIG = {
    "model_path": str(MODELS_DIR / "doclayout_yolo_ft.pt"),  # 优先使用专业模型
    "fallback_model": str(MODELS_DIR / "yolov10l_ft.pt"),    # 备用专业模型
    "conf_threshold": 0.25,
    "iou_threshold": 0.45,
    "max_det": 50,
    "use_gpu": True,  # 优先使用GPU
    "device": "cuda"  # 指定GPU设备
}

# 图像处理配置
IMAGE_CONFIG = {
    "target_resolution": 1024,      # 标准分辨率
    "high_resolution": 2560,        # 高分辨率
    "similarity_threshold": 0.8,    # 图片相似度阈值
    "overlap_threshold": 0.3        # 重叠区域阈值
}

# 向量化配置已禁用

# LLM配置（使用 LangUp API）
LLM_CONFIG = {
    "provider": "langup",
    "login_url": "https://langupapi.langup.cn/api/sysAuth/NoLogin",
    "chat_url": "https://langupapi.langup.cn/api/chat/completeChat",
    "account": "pythonuser",
    "password": "BMSarX",
    # 取消加密与预处理，使用明文直传
    # 登录额外参数（验证码等）
    "login_extra": {
        "code": "",
        "codeId": 0
    },
    # Header签名所需
    "access_key": "pythonuser",
    "access_secret": "BMSarX",
    "timeout": 60
}

# Milvus配置已禁用

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
    "summary": "你是资深研报分析师。请生成中文摘要，保留要点与数据。\n内容：\n{context}",
    "keyword": "请提取5-10个关键词，用顿号分隔，只输出关键词本身：\n{context}",
    "hybrid": "请以分点形式输出要点总结（不少于5点），必要时给出数据与结论：\n{context}",
    "markdown": "将以下内容转为结构化Markdown，小标题使用二级标题：\n{context}",
    "part_summary": "对下述段落进行简洁总结：\n{context}",
    "charts": "判断该图像是否包含有用的图表/数据可视化。仅返回 true 或 false。",
    "classify": (
        "你是行业研报分类助手。请基于全文内容判断所属行业/主题分类，"
        "从以下候选中多选返回：['宏观','消费','TMT','能源与化工','医药与医疗',"
        "'机械制造','汽车','电子','军工','建材','地产','商贸零售','计算机/AI',"
        "'金融','农业','海外市场','其他']。"
        "只输出JSON，字段要求：{\"categories\":[{\"name\":str,\"description\":str}],\"confidence\":0-1的小数}。"
        "注意：\n- description 用1-2句话概括为何归入该类，突出依据（数据/主题/结论）。\n"
        "- 仅输出严格JSON，无解释。\n内容：\n{context}"
    ),
    "tags": (
        "请为以下内容打10-20个标签，覆盖核心主题、公司、指标、结论与风险，"
        "使用中文，按重要性降序，避免过长短语；只输出JSON：{\"tags\":[...]}。\n内容：\n{context}"
    )
}

# 文件类型支持
SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.xlsx', '.xls']

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
    "enabled": True,  # 是否启用远程OCR
    "server_url": "http://192.168.3.133:8888",  # 远程OCR服务器地址
    "timeout": 300,  # 请求超时时间（秒）
    "retry_times": 3,  # 重试次数
    "fallback_to_local": False  # 远程失败时不回退到本地，避免加载本地模型
}
