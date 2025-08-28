# -*- coding: utf-8 -*-
"""
研报文件分类管理系统 - 主程序
整合文件扫描、GUI界面和数据库功能
"""
import sys
import os
import traceback
from tkinter import messagebox
from file_scanner import FileScanner
from database_manager import DatabaseManager
from gui_interface import ResearchFileGUI
from config import DATABASE_CONFIG


class ResearchFileManager:
    def __init__(self):
        self.file_scanner = FileScanner()
        self.database_manager = DatabaseManager()
        self.gui = None
        
    def initialize(self):
        """
        初始化系统
        """
        print("正在初始化研报文件分类管理系统...")
        
        # 测试数据库连接
        print("正在测试数据库连接...")
        if self.database_manager.connect():
            print("数据库连接成功")
            
            # 创建数据库表
            if self.database_manager.create_tables():
                print("数据库表初始化成功")
            else:
                print("警告: 数据库表初始化失败")
        else:
            print("警告: 数据库连接失败，部分功能可能不可用")
        
        # 初始化GUI
        self.gui = ResearchFileGUI()
        
        # 设置回调函数
        self.gui.set_callbacks(
            scan_callback=self.scan_files,
            upload_callback=self.upload_to_database
        )
        
        print("系统初始化完成")
        
    def scan_files(self):
        """
        扫描文件回调函数
        """
        try:
            print("开始扫描文件...")
            files = self.file_scanner.scan_files()
            
            if files:
                print(f"扫描完成，共找到 {len(files)} 个文件")
                
                # 显示统计信息
                stats = self.file_scanner.get_statistics()
                print("\n扫描统计:")
                print(f"总文件数: {stats['total_files']}")
                print(f"总大小: {stats['total_size_mb']} MB")
                
                # 自动导出到Excel文件
                try:
                    filename = f"scanned_files_{self.file_scanner.current_year}.xlsx"
                    if self.file_scanner.export_to_excel(filename):
                        print(f"扫描结果已自动导出到: {filename}")
                except Exception as e:
                    print(f"自动导出Excel失败: {e}")
                
                return files
            else:
                print("未找到符合条件的文件")
                return []
                
        except Exception as e:
            print(f"扫描文件时出错: {e}")
            traceback.print_exc()
            raise e
    
    def upload_to_database(self, files_data):
        """
        上传到数据库回调函数
        """
        try:
            if not files_data:
                print("没有数据需要上传")
                return False
            
            # 检查数据库连接
            if not self.database_manager.connection:
                print("数据库未连接，正在重新连接...")
                if not self.database_manager.connect():
                    print("数据库连接失败")
                    return False
            
            print(f"开始上传 {len(files_data)} 个文件到数据库...")
            
            # 生成批次名称
            from datetime import datetime
            batch_name = f"手动上传_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 执行批量上传
            success = self.database_manager.upload_files_batch(files_data, batch_name)
            
            if success:
                print("数据上传成功")
                
                # 显示数据库统计信息
                try:
                    stats = self.database_manager.get_file_statistics()
                    print(f"数据库中现有文件总数: {stats.get('total_files', 0)}")
                except Exception as e:
                    print(f"获取数据库统计信息失败: {e}")
                
                return True
            else:
                print("数据上传失败")
                return False
                
        except Exception as e:
            print(f"上传数据时出错: {e}")
            traceback.print_exc()
            return False
    
    def run(self):
        """
        运行系统
        """
        try:
            self.initialize()
            
            if self.gui:
                print("启动GUI界面...")
                self.gui.run()
            else:
                print("GUI初始化失败")
                
        except KeyboardInterrupt:
            print("\n用户中断程序")
        except Exception as e:
            print(f"程序运行出错: {e}")
            traceback.print_exc()
        finally:
            # 清理资源
            self.cleanup()
    
    def cleanup(self):
        """
        清理资源
        """
        print("正在清理资源...")
        
        if self.database_manager:
            self.database_manager.close()
        
        print("程序已退出")


def check_requirements():
    """
    检查系统要求
    """
    print("检查系统要求...")
    
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("错误: 需要Python 3.6或更高版本")
        return False
    
    # 检查必要的模块
    required_modules = [
        'tkinter', 'pandas', 'openpyxl', 'pymysql', 
        'sqlalchemy', 'ttkbootstrap'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("错误: 缺少以下必需的模块:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    print("系统要求检查通过")
    return True


def show_startup_info():
    """
    显示启动信息
    """
    print("=" * 60)
    print("研报文件分类管理系统")
    print("=" * 60)
    print("功能说明:")
    print("1. 扫描网络盘中的研报文件")
    print("2. 获取文件详细信息（创建、修改、访问时间等）")
    print("3. 筛选今年内有更新的文件")
    print("4. 提供图形界面进行手动分类和打标签")
    print("5. 支持批量上传到MySQL数据库")
    print("6. 支持Excel导入/导出功能")
    print("=" * 60)
    print("配置信息:")
    print(f"网络盘路径: {os.path.join('\\\\', 'NAS', 'study', 'study')}")
    print(f"数据库地址: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
    print(f"数据库名称: {DATABASE_CONFIG['database']}")
    print("=" * 60)
    print()


def main():
    """
    主函数
    """
    try:
        # 显示启动信息
        show_startup_info()
        
        # 检查系统要求
        if not check_requirements():
            input("按Enter键退出...")
            return
        
        # 创建并运行管理器
        manager = ResearchFileManager()
        manager.run()
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        traceback.print_exc()
        input("按Enter键退出...")


if __name__ == "__main__":
    main()