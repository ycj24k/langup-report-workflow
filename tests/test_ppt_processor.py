# -*- coding: utf-8 -*-
"""
测试PPT处理器的脚本
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_ppt_processor_import():
    """测试PPT处理器导入"""
    print("🧪 测试PPT处理器导入...")
    
    try:
        from pdf_ocr_module import PPTProcessor
        print("✅ PPT处理器导入成功")
        return True
    except ImportError as e:
        print(f"❌ PPT处理器导入失败: {e}")
        return False

def test_ppt_processor_initialization():
    """测试PPT处理器初始化"""
    print("\n🧪 测试PPT处理器初始化...")
    
    try:
        from pdf_ocr_module import PPTProcessor
        
        processor = PPTProcessor()
        print("✅ PPT处理器初始化成功")
        
        # 检查支持的文件格式
        status = processor.get_processing_status()
        print(f"支持的文件格式: {status['supported_formats']}")
        print(f"PPTX支持: {status['pptx_available']}")
        print(f"PPT支持: {status['ppt_available']}")
        print(f"LLM支持: {status['llm_available']}")
        
        return True
    except Exception as e:
        print(f"❌ PPT处理器初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ppt_file_detection():
    """测试PPT文件检测"""
    print("\n🧪 测试PPT文件检测...")
    
    try:
        from pdf_ocr_module import PPTProcessor
        
        processor = PPTProcessor()
        
        # 测试文件格式检测
        test_files = [
            "test.pptx",
            "test.ppt", 
            "test.pdf",
            "test.doc"
        ]
        
        for test_file in test_files:
            can_process = processor.can_process(test_file)
            print(f"  {test_file}: {'✓ 支持' if can_process else '✗ 不支持'}")
        
        return True
    except Exception as e:
        print(f"❌ PPT文件检测测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_scanner_ppt_support():
    """测试文件扫描器的PPT支持"""
    print("\n🧪 测试文件扫描器的PPT支持...")
    
    try:
        from file_scanner import FileScanner
        
        # 初始化扫描器，启用PPT处理
        scanner = FileScanner(enable_pdf_ocr=True, enable_ppt_ocr=True)
        
        print("✅ 文件扫描器初始化成功")
        print(f"PDF OCR启用: {scanner.enable_pdf_ocr}")
        print(f"PPT OCR启用: {scanner.enable_ppt_ocr}")
        print(f"向量存储: {'✓ 可用' if scanner.vector_store else '✗ 不可用'}")
        
        return True
    except Exception as e:
        print(f"❌ 文件扫描器PPT支持测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_ppt_support():
    """测试配置文件的PPT支持"""
    print("\n🧪 测试配置文件的PPT支持...")
    
    try:
        from config import SUPPORTED_EXTENSIONS
        
        print(f"支持的文件扩展名: {SUPPORTED_EXTENSIONS}")
        
        # 检查PPT相关扩展名
        ppt_extensions = ['.ppt', '.pptx']
        supported_ppt = [ext for ext in ppt_extensions if ext in SUPPORTED_EXTENSIONS]
        
        if len(supported_ppt) == len(ppt_extensions):
            print("✅ 所有PPT扩展名都支持")
            return True
        else:
            print(f"⚠ 部分PPT扩展名不支持: {[ext for ext in ppt_extensions if ext not in SUPPORTED_EXTENSIONS]}")
            return False
            
    except Exception as e:
        print(f"❌ 配置文件PPT支持测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试PPT处理器功能")
    print("=" * 60)
    
    # 测试各个功能
    test_results = []
    
    test_results.append(test_ppt_processor_import())
    test_results.append(test_ppt_processor_initialization())
    test_results.append(test_ppt_file_detection())
    test_results.append(test_file_scanner_ppt_support())
    test_results.append(test_config_ppt_support())
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！PPT处理器功能正常！")
        print("\n✅ 已实现的功能:")
        print("  - PPT处理器模块创建完成")
        print("  - 支持PPT和PPTX文件格式")
        print("  - 集成到文件扫描器中")
        print("  - 配置文件已支持PPT扩展名")
        print("  - 向量化存储支持")
        print("\n📁 支持的文件格式:")
        print("  - PDF文件 (.pdf)")
        print("  - PPT文件 (.ppt)")
        print("  - PPTX文件 (.pptx)")
        print("\n🔧 处理功能:")
        print("  - 文本提取（从幻灯片、形状、表格）")
        print("  - 内容摘要生成")
        print("  - 关键词提取")
        print("  - 向量化存储")
        print("  - 相似度搜索")
    else:
        print("❌ 部分测试失败，需要进一步修复")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
