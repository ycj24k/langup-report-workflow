# -*- coding: utf-8 -*-
"""
文件扫描测试脚本
用于验证网络盘路径访问是否正常
"""
import os
from file_scanner import FileScanner
from config import NETWORK_PATH


def test_network_path():
    """
    测试网络路径访问
    """
    print("=" * 50)
    print("网络路径访问测试")
    print("=" * 50)
    
    print(f"目标路径: {NETWORK_PATH}")
    print("-" * 50)
    
    print("正在检查路径访问权限...")
    
    try:
        if os.path.exists(NETWORK_PATH):
            print("✓ 网络路径可以访问")
            
            # 尝试列出目录内容
            try:
                items = os.listdir(NETWORK_PATH)
                print(f"✓ 路径下共有 {len(items)} 个项目")
                
                # 显示前几个项目
                if items:
                    print("前几个项目:")
                    for i, item in enumerate(items[:5]):
                        item_path = os.path.join(NETWORK_PATH, item)
                        if os.path.isfile(item_path):
                            print(f"  {i+1}. [文件] {item}")
                        else:
                            print(f"  {i+1}. [目录] {item}")
                    
                    if len(items) > 5:
                        print(f"  ... 还有 {len(items)-5} 个项目")
                
                return True
                
            except PermissionError:
                print("✗ 没有权限访问路径内容")
                return False
            except Exception as e:
                print(f"✗ 列出路径内容时出错: {e}")
                return False
        else:
            print("✗ 网络路径不存在或无法访问")
            return False
            
    except Exception as e:
        print(f"✗ 检查路径时出错: {e}")
        return False


def test_file_scanning():
    """
    测试文件扫描功能
    """
    print("\n" + "=" * 50)
    print("文件扫描功能测试")
    print("=" * 50)
    
    scanner = FileScanner()
    
    # 如果网络路径不可用，使用当前目录测试
    test_path = NETWORK_PATH
    if not os.path.exists(test_path):
        test_path = os.getcwd()
        print(f"网络路径不可用，使用当前目录进行测试: {test_path}")
    
    print(f"扫描路径: {test_path}")
    print("-" * 50)
    
    try:
        print("正在扫描文件...")
        files = scanner.scan_files(test_path)
        
        if files:
            print(f"✓ 扫描完成，找到 {len(files)} 个今年内的文件")
            
            # 获取统计信息
            stats = scanner.get_statistics()
            print("\n扫描统计:")
            print(f"总文件数: {stats['total_files']}")
            print(f"总大小: {stats['total_size_mb']} MB")
            
            if stats['extension_stats']:
                print("\n文件类型分布:")
                for ext, count in stats['extension_stats'].items():
                    print(f"  {ext}: {count} 个")
            
            # 显示前几个文件
            print("\n文件示例:")
            for i, file_data in enumerate(files[:3]):
                print(f"{i+1}. {file_data['file_name']}")
                print(f"   大小: {file_data['file_size_mb']} MB")
                print(f"   修改时间: {file_data['modification_date']}")
                print()
            
            if len(files) > 3:
                print(f"... 还有 {len(files)-3} 个文件")
            
            return True
        else:
            print("✓ 扫描完成，但未找到今年内的文件")
            return True
            
    except Exception as e:
        print(f"✗ 文件扫描出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    主函数
    """
    print("研报文件分类管理系统 - 文件扫描测试工具")
    print()
    
    # 测试网络路径
    path_ok = test_network_path()
    
    # 测试文件扫描
    scan_ok = test_file_scanning()
    
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    
    if path_ok:
        print("✓ 网络路径访问正常")
    else:
        print("✗ 网络路径访问有问题")
    
    if scan_ok:
        print("✓ 文件扫描功能正常")
    else:
        print("✗ 文件扫描功能有问题")
    
    if path_ok and scan_ok:
        print("\n✓ 所有测试通过，系统可以正常使用")
    else:
        print("\n✗ 部分测试失败，请检查配置")
        print("\n问题排查建议:")
        if not path_ok:
            print("1. 检查网络连接")
            print("2. 确认网络盘路径是否正确")
            print("3. 确认是否有访问权限")
            print("4. 尝试在文件管理器中手动访问该路径")
        if not scan_ok:
            print("5. 检查Python环境是否完整")
            print("6. 确认所有依赖包是否正确安装")
    
    print()
    input("按 Enter 键退出...")


if __name__ == "__main__":
    main()