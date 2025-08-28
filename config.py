# -*- coding: utf-8 -*-
"""
配置文件
"""
import os

# 网络盘路径配置
NETWORK_PATH = r"\\NAS\study\study"

# 数据库配置
DATABASE_CONFIG = {
    'host': '192.168.3.104',
    'port': 3306,
    'user': 'root',  # 请根据实际情况修改
    'password': '',  # 请根据实际情况修改
    'database': 'research_reports',
    'charset': 'utf8mb4'
}

# 支持的文件格式
SUPPORTED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx']

# 批次上传大小
BATCH_SIZE = 100

# 文件分类标签
FILE_CATEGORIES = [
    '宏观经济',
    '行业研究',
    '公司研究',
    '投资策略',
    '固定收益',
    '量化研究',
    '其他'
]

# 文件重要性标签
IMPORTANCE_LEVELS = [
    '高',
    '中',
    '低'
]