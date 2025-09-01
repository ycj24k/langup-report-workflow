# -*- coding: utf-8 -*-
"""
文件扫描模块
负责扫描网络盘路径，获取文件信息
"""
import os
import time
from datetime import datetime, date
from pathlib import Path
import pandas as pd
from config import NETWORK_PATH, SUPPORTED_EXTENSIONS


class FileScanner:
    def __init__(self):
        self.current_year = date.today().year
        self.scanned_files = []

    def scan_files(self, path=None):
        """
        扫描指定路径下的所有文件
        """
        if path is None:
            path = NETWORK_PATH
            
        print(f"开始扫描路径: {path}")
        
        try:
            # 检查路径是否存在
            if not os.path.exists(path):
                raise FileNotFoundError(f"网络路径不存在: {path}")
            
            file_count = 0
            for root, dirs, files in os.walk(path):
                for file in files:
                    if self._is_supported_file(file):
                        file_path = os.path.join(root, file)
                        try:
                            file_info = self._get_file_info(file_path)
                            if self._is_current_year_file(file_info):
                                self.scanned_files.append(file_info)
                                file_count += 1
                                print(f"已扫描文件: {file_count}", end='\r')
                        except Exception as e:
                            print(f"处理文件 {file_path} 时出错: {e}")
                            continue
            
            print(f"\n扫描完成，共找到 {len(self.scanned_files)} 个今年内的文件")
            return self.scanned_files
            
        except Exception as e:
            print(f"扫描路径时出错: {e}")
            return []

    def _is_supported_file(self, filename):
        """
        检查文件是否为支持的格式
        """
        _, ext = os.path.splitext(filename.lower())
        return ext in SUPPORTED_EXTENSIONS

    def _get_file_info(self, file_path):
        """
        获取文件的详细信息
        """
        stat_info = os.stat(file_path)
        
        # 获取文件时间信息
        creation_time = datetime.fromtimestamp(stat_info.st_ctime)
        modification_time = datetime.fromtimestamp(stat_info.st_mtime)
        access_time = datetime.fromtimestamp(stat_info.st_atime)
        
        # 获取文件大小（转换为MB）
        file_size = round(stat_info.st_size / (1024 * 1024), 2)
        
        return {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'file_size_mb': file_size,
            'creation_date': creation_time,
            'modification_date': modification_time,
            'access_date': access_time,
            'extension': os.path.splitext(file_path)[1].lower(),
            'category': '',  # 待分类
            'importance': '',  # 待标记重要性
            'tags': '',  # 待添加标签
            'notes': ''  # 备注
        }

    def _is_current_year_file(self, file_info):
        """
        检查文件的任一日期是否在今年内
        """
        current_year = self.current_year
        
        dates_to_check = [
            file_info['creation_date'],
            file_info['modification_date'],
            # file_info['access_date']
        ]
        
        for date_obj in dates_to_check:
            if date_obj.year == current_year:
                return True
        
        return False

    def export_to_excel(self, filename="scanned_files.xlsx"):
        """
        导出扫描结果到Excel文件
        """
        if not self.scanned_files:
            print("没有可导出的文件数据")
            return False
        
        try:
            df = pd.DataFrame(self.scanned_files)
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"文件信息已导出到: {filename}")
            return True
        except Exception as e:
            print(f"导出Excel文件时出错: {e}")
            return False

    def get_statistics(self):
        """
        获取扫描结果统计信息
        """
        if not self.scanned_files:
            return {}
        
        total_files = len(self.scanned_files)
        total_size = sum(file['file_size_mb'] for file in self.scanned_files)
        
        # 按扩展名统计
        ext_stats = {}
        for file in self.scanned_files:
            ext = file['extension']
            ext_stats[ext] = ext_stats.get(ext, 0) + 1
        
        # 按月份统计（以修改日期为准）
        month_stats = {}
        for file in self.scanned_files:
            month = file['modification_date'].strftime('%Y-%m')
            month_stats[month] = month_stats.get(month, 0) + 1
        
        return {
            'total_files': total_files,
            'total_size_mb': round(total_size, 2),
            'extension_stats': ext_stats,
            'month_stats': month_stats
        }


# 测试函数
def test_scanner():
    """
    测试文件扫描功能
    """
    scanner = FileScanner()
    
    # 如果网络路径不可用，使用本地测试路径
    test_path = NETWORK_PATH
    if not os.path.exists(test_path):
        test_path = os.getcwd()  # 使用当前目录作为测试
        print(f"网络路径不可用，使用测试路径: {test_path}")
    
    files = scanner.scan_files(test_path)
    
    if files:
        stats = scanner.get_statistics()
        print("\n扫描统计:")
        print(f"总文件数: {stats['total_files']}")
        print(f"总大小: {stats['total_size_mb']} MB")
        print("\n文件类型分布:")
        for ext, count in stats['extension_stats'].items():
            print(f"  {ext}: {count} 个")
        
        # 导出前5个文件作为示例
        if len(files) > 5:
            files_sample = files[:5]
        else:
            files_sample = files
        
        print("\n文件示例:")
        for i, file in enumerate(files_sample, 1):
            print(f"{i}. {file['file_name']}")
            print(f"   路径: {file['file_path']}")
            print(f"   大小: {file['file_size_mb']} MB")
            print(f"   修改时间: {file['modification_date']}")
            print()
    
    return files


if __name__ == "__main__":
    test_scanner()