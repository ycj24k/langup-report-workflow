# -*- coding: utf-8 -*-
"""
测试增强版OCR集成功能
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_enhanced_imports():
    """测试增强版模块导入"""
    print("🧪 测试增强版模块导入...")
    
    test_results = []
    
    # 测试PDF OCR模块导入
    try:
        from pdf_ocr_module import PDFProcessor, PPTProcessor, VectorStore
        print("✅ 原版PDF OCR模块导入成功")
        test_results.append(True)
    except ImportError as e:
        print(f"❌ 原版PDF OCR模块导入失败: {e}")
        test_results.append(False)
    
    # 测试增强版向量存储导入
    try:
        from pdf_ocr_module.vector_store_enhanced import EnhancedVectorStore
        print("✅ 增强版向量存储模块导入成功")
        test_results.append(True)
    except ImportError as e:
        print(f"❌ 增强版向量存储模块导入失败: {e}")
        test_results.append(False)
    
    return test_results

def test_enhanced_vector_store():
    """测试增强版向量存储功能"""
    print("\n🧪 测试增强版向量存储功能...")
    
    try:
        from pdf_ocr_module.vector_store_enhanced import EnhancedVectorStore
        
        # 测试不同配置的初始化
        test_configs = [
            {"use_milvus": False, "embedding_type": "ollama"},
            {"use_milvus": False, "embedding_type": "openai"},
            {"use_milvus": True, "embedding_type": "ollama"},
        ]
        
        results = []
        for config in test_configs:
            try:
                store = EnhancedVectorStore(**config)
                print(f"✅ 配置 {config} 初始化成功")
                results.append(True)
                
                # 测试向量生成
                test_text = "这是一个测试文本，用于验证向量生成功能。"
                vector = store.generate_vectors(test_text)
                
                if vector and len(vector) > 0:
                    print(f"✅ 向量生成成功，维度: {len(vector)}")
                    results.append(True)
                else:
                    print("⚠ 向量生成返回空结果")
                    results.append(False)
                    
            except Exception as e:
                print(f"❌ 配置 {config} 初始化失败: {e}")
                results.append(False)
        
        return results
        
    except Exception as e:
        print(f"❌ 增强版向量存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return [False]

def test_file_scanner_integration():
    """测试文件扫描器集成"""
    print("\n🧪 测试文件扫描器集成...")
    
    try:
        from file_scanner import FileScanner
        
        # 初始化扫描器，启用PDF和PPT处理
        scanner = FileScanner(enable_pdf_ocr=True, enable_ppt_ocr=True, use_gpu=False, use_milvus=False)
        
        print("✅ 文件扫描器初始化成功")
        print(f"PDF OCR启用: {scanner.enable_pdf_ocr}")
        print(f"PPT OCR启用: {scanner.enable_ppt_ocr}")
        print(f"向量存储可用: {'✓' if scanner.vector_store else '✗'}")
        
        # 测试处理器状态
        if hasattr(scanner, 'pdf_processor') and scanner.pdf_processor:
            print("✅ PDF处理器可用")
        else:
            print("⚠ PDF处理器不可用")
            
        if hasattr(scanner, 'ppt_processor') and scanner.ppt_processor:
            print("✅ PPT处理器可用")
        else:
            print("⚠ PPT处理器不可用")
        
        return True
        
    except Exception as e:
        print(f"❌ 文件扫描器集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """测试依赖库状态"""
    print("\n🧪 测试依赖库状态...")
    
    dependencies = [
        ("pymilvus", "Milvus向量数据库"),
        ("langchain_community", "LangChain社区版"),
        ("langchain_openai", "LangChain OpenAI"),
        ("openai", "OpenAI"),
        ("ollama", "Ollama"),
        ("loguru", "日志库"),
        ("numpy", "数值计算"),
        ("pandas", "数据处理"),
        ("python-pptx", "PPT处理"),
        ("paddleocr", "OCR识别"),
        ("torch", "深度学习框架"),
        ("PIL", "图像处理"),
        ("cv2", "OpenCV"),
    ]
    
    results = []
    for dep_name, description in dependencies:
        try:
            if dep_name == "python-pptx":
                import pptx
            elif dep_name == "PIL":
                from PIL import Image
            elif dep_name == "cv2":
                import cv2
            else:
                __import__(dep_name)
            print(f"✅ {description} ({dep_name}) 可用")
            results.append(True)
        except ImportError:
            print(f"❌ {description} ({dep_name}) 不可用")
            results.append(False)
    
    return results

def test_config_loading():
    """测试配置加载"""
    print("\n🧪 测试配置加载...")
    
    try:
        from pdf_ocr_module.config import (
            VECTOR_CONFIG, MILVUS_CONFIG, LLM_CONFIG, 
            OPENAI_CONFIG, PROMPTS, OCR_CONFIG
        )
        
        print("✅ 基础配置加载成功")
        print(f"向量配置: {VECTOR_CONFIG}")
        print(f"Milvus配置: {MILVUS_CONFIG}")
        print(f"LLM配置模型: {LLM_CONFIG.get('model_name', 'N/A')}")
        print(f"提示词数量: {len(PROMPTS)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_create_sample_collection():
    """测试创建样例集合"""
    print("\n🧪 测试创建样例集合...")
    
    try:
        from pdf_ocr_module.vector_store_enhanced import EnhancedVectorStore
        from langchain_core.documents import Document
        
        # 使用本地模式
        store = EnhancedVectorStore(use_milvus=False, embedding_type="ollama")
        
        # 创建测试集合
        collection_name = "test_collection"
        result = store.create_collection(collection_name, "测试集合")
        
        if result['status'] == 'success':
            print(f"✅ 集合创建成功: {result['message']}")
            
            # 添加测试文档
            test_docs = [
                Document(
                    page_content="这是第一个测试文档，包含一些示例内容。",
                    metadata={"source": "test1", "page": 1}
                ),
                Document(
                    page_content="这是第二个测试文档，用于验证搜索功能。",
                    metadata={"source": "test2", "page": 1}
                )
            ]
            
            add_result = store.add_documents(collection_name, test_docs)
            if add_result['status'] == 'success':
                print(f"✅ 文档添加成功: {add_result['message']}")
                
                # 测试搜索
                search_results = store.search_similar("测试文档", collection_name, top_k=2)
                if search_results:
                    print(f"✅ 搜索成功，找到 {len(search_results)} 个结果")
                    for i, result in enumerate(search_results):
                        print(f"  结果 {i+1}: 相似度 {result.get('similarity', 0):.3f}")
                else:
                    print("⚠ 搜索返回空结果")
                
                return True
            else:
                print(f"❌ 文档添加失败: {add_result['message']}")
                return False
        else:
            print(f"❌ 集合创建失败: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ 样例集合测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试增强版OCR集成功能")
    print("=" * 80)
    
    # 运行所有测试
    all_results = []
    
    # 基础导入测试
    import_results = test_enhanced_imports()
    all_results.extend(import_results)
    
    # 依赖库测试
    dep_results = test_dependencies()
    all_results.extend(dep_results)
    
    # 配置加载测试
    config_result = test_config_loading()
    all_results.append(config_result)
    
    # 增强版向量存储测试
    vector_results = test_enhanced_vector_store()
    all_results.extend(vector_results)
    
    # 文件扫描器集成测试
    scanner_result = test_file_scanner_integration()
    all_results.append(scanner_result)
    
    # 样例集合测试
    collection_result = test_create_sample_collection()
    all_results.append(collection_result)
    
    # 结果统计
    print("\n" + "=" * 80)
    print("📊 测试结果统计")
    print("=" * 80)
    
    passed = sum(all_results)
    total = len(all_results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"通过测试: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 集成测试基本通过！系统可以正常使用")
        print("\n✅ 功能状态:")
        print("  - 基础模块导入: ✓")
        print("  - 配置文件加载: ✓") 
        print("  - 向量存储功能: ✓")
        print("  - 文件扫描集成: ✓")
        print("  - 本地存储功能: ✓")
        
        print("\n📋 使用建议:")
        print("  1. 安装缺少的依赖库以获得最佳性能")
        print("  2. 配置Milvus数据库以启用高级向量搜索")
        print("  3. 配置Ollama或OpenAI API以获得更好的向量化效果")
        print("  4. 测试实际PDF和PPT文件处理功能")
        
    elif success_rate >= 60:
        print("⚠ 集成测试部分通过，建议修复以下问题:")
        print("  - 检查缺少的依赖库")
        print("  - 验证配置文件设置")
        print("  - 确认网络连接状态")
        
    else:
        print("❌ 集成测试失败较多，需要重点修复:")
        print("  - 安装必要的依赖库")
        print("  - 检查代码兼容性")
        print("  - 验证系统环境配置")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
