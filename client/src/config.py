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

# 文件分类标签 - 更新为完整的行业分类（带描述）
FILE_CATEGORIES = [
    # 传统金融研究分类
    {'name': '宏观经济', 'description': '宏观经济政策、GDP、通胀、利率等宏观指标分析'},
    {'name': '行业研究', 'description': '特定行业的发展趋势、竞争格局、投资机会分析'},
    {'name': '公司研究', 'description': '上市公司财务分析、业务模式、估值研究'},
    {'name': '投资策略', 'description': '投资组合配置、市场策略、风险控制建议'},
    {'name': '固定收益', 'description': '债券市场、信用分析、利率走势研究'},
    {'name': '量化研究', 'description': '量化模型、算法交易、风险管理策略'},
    {'name': '市场动态', 'description': '市场热点、交易数据、投资者情绪分析'},
    
    # 快消品行业
    {'name': '快消品', 'description': '快速消费品行业趋势、品牌分析、消费行为研究'},
    {'name': '美妆护肤', 'description': '化妆品、护肤品行业分析、品牌竞争、消费趋势'},
    {'name': '电商', 'description': '电子商务平台、在线零售、数字化营销分析'},
    
    # 制造业
    {'name': '汽车', 'description': '汽车行业、新能源汽车、智能驾驶技术分析'},
    {'name': '家电', 'description': '家用电器行业、智能家居、消费升级趋势'},
    {'name': '手机', 'description': '智能手机市场、移动通信、消费电子分析'},
    {'name': '数码3C', 'description': '数码产品、3C消费、科技创新趋势'},
    {'name': '服装', 'description': '服装行业、时尚趋势、品牌营销分析'},
    {'name': '家居', 'description': '家居建材、装修装饰、生活方式研究'},
    
    # 服务业
    {'name': '互联网', 'description': '互联网行业、平台经济、数字化转型分析'},
    {'name': '餐饮', 'description': '餐饮行业、连锁经营、消费升级趋势'},
    {'name': '游戏', 'description': '游戏行业、电竞产业、娱乐消费分析'},
    {'name': '影视娱乐', 'description': '影视制作、娱乐产业、内容消费趋势'},
    {'name': '时尚', 'description': '时尚产业、潮流趋势、品牌营销分析'},
    {'name': '宠物', 'description': '宠物行业、宠物经济、消费行为研究'},
    {'name': '酒类', 'description': '酒类行业、品牌竞争、消费升级分析'},
    {'name': '教育', 'description': '教育培训、在线教育、教育科技趋势'},
    {'name': '体育', 'description': '体育产业、运动消费、健康生活趋势'},
    {'name': '文旅', 'description': '文化旅游、休闲娱乐、体验经济分析'},
    {'name': '零售', 'description': '零售行业、新零售、消费渠道变革'},
    {'name': '医疗', 'description': '医疗健康、生物医药、健康消费趋势'},
    {'name': '招商', 'description': '招商引资、产业政策、投资环境分析'},
    
    # 其他行业
    {'name': '金融', 'description': '金融服务、银行业、保险业、资本市场分析'},
    {'name': '食品', 'description': '食品行业、食品安全、消费升级趋势'},
    {'name': '地产', 'description': '房地产行业、土地市场、住房政策分析'},
    
    # 内容类型
    {'name': '必读书单', 'description': '推荐阅读、知识管理、学习资源整理'},
    {'name': '手册', 'description': '操作指南、技术文档、实用工具说明'},
    {'name': '思维导图', 'description': '知识梳理、逻辑框架、思维工具'},
    
    # 其他
    {'name': '其他', 'description': '其他类型文档、未分类内容'}
]

# 为了兼容性，保留原有的简单列表格式
FILE_CATEGORIES_SIMPLE = [cat['name'] if isinstance(cat, dict) else cat for cat in FILE_CATEGORIES]

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
    'enable_gpu': False         # 是否启用GPU加速
}