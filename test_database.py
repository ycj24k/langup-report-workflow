# -*- coding: utf-8 -*-
"""
数据库连接测试脚本
用于验证数据库配置是否正确
"""
import sys
from database_manager import DatabaseManager
from config import DATABASE_CONFIG


def test_database_connection():
    """
    测试数据库连接
    """
    print("=" * 50)
    print("数据库连接测试")
    print("=" * 50)
    
    print("配置信息:")
    print(f"主机: {DATABASE_CONFIG['host']}")
    print(f"端口: {DATABASE_CONFIG['port']}")
    print(f"用户: {DATABASE_CONFIG['user']}")
    print(f"数据库: {DATABASE_CONFIG['database']}")
    print("-" * 50)
    
    db = DatabaseManager()
    
    print("正在测试数据库连接...")
    
    try:
        if db.connect():
            print("✓ 数据库连接成功")
            
            print("正在创建数据库表...")
            if db.create_tables():
                print("✓ 数据库表创建成功")
                
                print("正在获取统计信息...")
                stats = db.get_file_statistics()
                print(f"✓ 当前数据库中共有 {stats.get('total_files', 0)} 个文件记录")
                
                print("✓ 数据库测试完成，系统可以正常使用")
                result = True
            else:
                print("✗ 数据库表创建失败")
                result = False
        else:
            print("✗ 数据库连接失败")
            result = False
            
    except Exception as e:
        print(f"✗ 数据库测试出错: {e}")
        result = False
    finally:
        db.close()
    
    print("=" * 50)
    return result


def main():
    """
    主函数
    """
    print("研报文件分类管理系统 - 数据库测试工具")
    print()
    
    success = test_database_connection()
    
    if success:
        print("数据库配置正确，可以正常使用系统")
    else:
        print()
        print("数据库配置有问题，请检查以下事项:")
        print("1. 数据库服务器是否正在运行")
        print("2. config.py 中的连接信息是否正确")
        print("3. 网络是否能访问数据库服务器")
        print("4. 数据库用户是否有足够权限")
        print("5. 是否安装了必要的Python包 (pymysql, sqlalchemy)")
        
        print()
        print("修改 config.py 文件中的数据库配置:")
        print("DATABASE_CONFIG = {")
        print("    'host': '你的数据库主机地址',")
        print("    'port': 3306,")
        print("    'user': '你的数据库用户名',")
        print("    'password': '你的数据库密码',")
        print("    'database': 'research_reports',")
        print("    'charset': 'utf8mb4'")
        print("}")
    
    print()
    input("按 Enter 键退出...")


if __name__ == "__main__":
    main()