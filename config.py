# -*- coding: utf-8 -*-
"""
配置文件
"""
import os

# 网络盘路径配置
NETWORK_PATH = r"\\NAS\study\research_reports"

# 数据库配置
DATABASE_CONFIG = {
    'host': '192.168.3.104',
    'port': 3306,
    'user': 'Knowledgeflow',  # 请根据实际情况修改
    'password': 'P@ssw0rd1234!',  # 请根据实际情况修改
    'database': 'research_reports',  # 修改为我们的数据库名
    'charset': 'utf8mb4'
}

# 支持的文件格式
SUPPORTED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']

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

# 预设标签选项
PRESET_TAGS = [
    '重要',
    '紧急',
    '参考',
    '存档',
    '待处理',
    '已完成',
    '需要关注',
    '投资机会',
    '风险提示',
    '政策解读',
    '行业分析',
    '公司研究',
    '市场动态',
    '技术分析',
    '基本面分析'
]