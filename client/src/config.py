# -*- coding: utf-8 -*-
"""
配置文件
"""
import os

# 网络盘路径配置
# NETWORK_PATH = r"\\NAS\study\research_reports"
NETWORK_PATH = r"E:\project\sideline\changshashuziyoumin\research-report-list"

# 数据库配置
DATABASE_CONFIG = {
    'host': '192.168.3.104',
    'port': 3306,
    'user': 'root',  # 请根据实际情况修改
    'password': '123456789',  # 请根据实际情况修改
    'database': 'reportflow',  # 使用用户有权限的数据库
    'charset': 'utf8mb4'
}

# 支持的文件格式
SUPPORTED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']

# 批次上传大小
BATCH_SIZE = 100

# 文件分类标签 - 更新为完整的行业分类
FILE_CATEGORIES = [
    # 传统金融研究分类
    '宏观经济',
    '行业研究',
    '公司研究',
    '投资策略',
    '固定收益',
    '量化研究',
    '市场动态',
    
    # 快消品行业
    '快消品',
    '美妆护肤',
    '电商',
    
    # 制造业
    '汽车',
    '家电',
    '手机',
    '数码3C',
    '服装',
    '家居',
    
    # 服务业
    '互联网',
    '餐饮',
    '游戏',
    '影视娱乐',
    '时尚',
    '宠物',
    '酒类',
    '教育',
    '体育',
    '文旅',
    '零售',
    '医疗',
    '招商',
    
    # 其他行业
    '金融',
    '食品',
    '地产',
    
    # 内容类型
    '必读书单',
    '手册',
    '思维导图',
    
    # 其他
    '其他'
]

# 文件重要性标签
IMPORTANCE_LEVELS = [
    '高',
    '中',
    '低'
]

# 预设标签选项 - 扩展更多标签
PRESET_TAGS = [
    # 基础标签
    '重要',
    '紧急',
    '参考',
    '存档',
    '待处理',
    '已完成',
    
    # 分析标签
    '需要关注',
    '投资机会',
    '风险提示',
    '政策解读',
    '行业分析',
    '公司研究',
    '市场动态',
    '技术分析',
    '基本面分析',
    
    # 新增标签
    '热点话题',
    '深度研究',
    '数据报告',
    '专家观点',
    '市场预测',
    '竞争分析',
    '趋势分析',
    '创新技术',
    '政策影响',
    '风险评估',
    '投资建议',
    '行业趋势',
    '市场机会',
    '战略规划'
]

# 文件符合状态选项
COMPLIANCE_STATUS = [
    '符合',
    '不符合',
    '待定'
]

# 解析状态选项
PARSING_STATUS = [
    '未解析',
    '解析中',
    '已解析',
    '解析失败'
]

# OCR配置
OCR_CONFIG = {
    'auto_ocr_on_scan': False,  # 扫描时是否自动进行OCR识别
    'enable_gpu': False,        # 是否启用GPU加速
    'enable_milvus': False      # 是否启用Milvus向量数据库
}