# -*- coding: utf-8 -*-
"""
配置文件模板
请复制此文件为 config.py 并修改相应配置
"""
import os

# 网络盘路径配置
# 请根据实际情况修改网络盘路径
NETWORK_PATH = r"\\NAS\study\study"

# 数据库配置
# 请修改以下配置为实际的数据库连接信息
DATABASE_CONFIG = {
    'host': '192.168.3.104',        # 数据库服务器IP地址
    'port': 3306,                   # 数据库端口，MySQL默认3306
    'user': 'root',                 # 数据库用户名，请修改为实际用户名
    'password': '',                 # 数据库密码，请修改为实际密码
    'database': 'research_reports', # 数据库名称，会自动创建
    'charset': 'utf8mb4'           # 字符集，建议使用utf8mb4
}

# 支持的文件格式
# 可以根据需要添加或删除文件格式
SUPPORTED_EXTENSIONS = [
    '.pdf',   # PDF文档
    '.doc',   # Word文档
    '.docx',  # Word文档（新格式）
    '.txt',   # 文本文件
    '.xls',   # Excel文档
    '.xlsx',  # Excel文档（新格式）
    '.ppt',   # PowerPoint文档
    '.pptx'   # PowerPoint文档（新格式）
]

# 批次上传大小
# 每次向数据库上传的文件数量，可以根据性能调整
BATCH_SIZE = 100

# 文件分类标签
# 可以根据实际需要修改分类
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
# 可以根据实际需要修改重要性级别
IMPORTANCE_LEVELS = [
    '高',
    '中',
    '低'
]

# 配置验证
def validate_config():
    """
    验证配置是否正确
    """
    errors = []
    
    # 检查网络路径
    if not NETWORK_PATH:
        errors.append("网络路径未配置")
    
    # 检查数据库配置
    required_db_keys = ['host', 'port', 'user', 'password', 'database']
    for key in required_db_keys:
        if key not in DATABASE_CONFIG or not DATABASE_CONFIG[key]:
            if key == 'password':
                # 密码可以为空
                continue
            errors.append(f"数据库配置缺少: {key}")
    
    # 检查文件格式
    if not SUPPORTED_EXTENSIONS:
        errors.append("支持的文件格式列表为空")
    
    # 检查分类
    if not FILE_CATEGORIES:
        errors.append("文件分类列表为空")
    
    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("配置验证通过")
        return True


if __name__ == "__main__":
    print("配置文件验证")
    print("=" * 30)
    validate_config()