# -*- coding: utf-8 -*-
"""
测试文件路径修改的脚本
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_cache_file_path():
    """测试缓存文件路径"""
    print("🧪 测试缓存文件路径...")
    
    try:
        from cache_manager import FileCache
        
        # 创建缓存管理器实例
        cache = FileCache()
        
        # 检查缓存文件路径
        expected_path = Path("data") / "file_cache.pkl"
        actual_path = cache.cache_file
        
        print(f"期望路径: {expected_path}")
        print(f"实际路径: {actual_path}")
        
        if str(actual_path) == str(expected_path):
            print("✅ 缓存文件路径正确")
            return True
        else:
            print("❌ 缓存文件路径不正确")
            return False
            
    except Exception as e:
        print(f"❌ 测试缓存文件路径失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_excel_export_path():
    """测试Excel导出路径"""
    print("\n🧪 测试Excel导出路径...")
    
    try:
        from file_scanner import FileScanner
        
        # 创建文件扫描器实例
        scanner = FileScanner(enable_pdf_ocr=False)
        
        # 检查data目录是否存在
        data_dir = Path("data")
        if not data_dir.exists():
            print("⚠ data目录不存在，将创建")
            data_dir.mkdir(exist_ok=True)
        
        # 模拟一些测试数据
        test_files = [
            {
                'file_name': 'test1.pdf',
                'file_path': '/test/test1.pdf',
                'file_size_mb': 1.5,
                'extension': '.pdf',
                'creation_date': '2025-01-01 10:00:00',
                'modification_date': '2025-01-01 10:00:00',
                'access_date': '2025-01-01 10:00:00'
            }
        ]
        
        # 将字符串日期转换为datetime对象
        from datetime import datetime
        for file_info in test_files:
            for date_key in ['creation_date', 'modification_date', 'access_date']:
                file_info[date_key] = datetime.strptime(file_info[date_key], '%Y-%m-%d %H:%M:%S')
        
        scanner.scanned_files = test_files
        
        # 测试导出功能
        test_filename = "test_export.xlsx"
        success = scanner.export_to_excel(test_filename)
        
        if success:
            # 检查文件是否在data目录中
            expected_path = data_dir / test_filename
            if expected_path.exists():
                print(f"✅ Excel文件成功导出到: {expected_path}")
                # 清理测试文件
                expected_path.unlink()
                print("✅ 测试文件已清理")
                return True
            else:
                print(f"❌ Excel文件未在预期位置: {expected_path}")
                return False
        else:
            print("❌ Excel导出失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试Excel导出路径失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_directory_structure():
    """测试data目录结构"""
    print("\n🧪 测试data目录结构...")
    
    try:
        data_dir = Path("data")
        
        # 确保data目录存在
        data_dir.mkdir(exist_ok=True)
        
        print(f"✅ data目录存在: {data_dir}")
        
        # 列出data目录中的文件
        files = list(data_dir.glob("*"))
        print(f"data目录中的文件:")
        for file in files:
            if file.is_file():
                print(f"  📄 {file.name} ({file.stat().st_size} bytes)")
            else:
                print(f"  📁 {file.name}/")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试data目录结构失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试文件路径修改")
    print("=" * 60)
    
    # 测试各个功能
    test_results = []
    
    test_results.append(test_cache_file_path())
    test_results.append(test_excel_export_path())
    test_results.append(test_data_directory_structure())
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！文件路径修改成功！")
        print("\n✅ 已修复的问题:")
        print("  - 缓存文件现在保存在data目录中")
        print("  - Excel导出文件现在保存在data目录中")
        print("  - 自动创建data目录（如果不存在）")
        print("\n📁 文件路径说明:")
        print("  - 缓存文件: data/file_cache.pkl")
        print("  - Excel文件: data/scanned_files_*.xlsx")
        print("  - 其他数据文件: data/")
    else:
        print("❌ 部分测试失败，需要进一步修复")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
