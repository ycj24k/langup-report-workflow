"""
使用示例 - 展示如何使用PDF OCR模块
"""

import asyncio
from pathlib import Path
from pdf_ocr_module import PDFProcessor, OCREngine, VectorStore, PDFOCRServer


def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    # 1. 初始化PDF处理器
    processor = PDFProcessor(use_gpu=False)  # 不使用GPU
    
    # 2. 处理单个PDF文件
    pdf_path = "example.pdf"  # 替换为你的PDF文件路径
    if Path(pdf_path).exists():
        result = processor.process_pdf(pdf_path, "example_output")
        print(f"处理结果: {result}")
    else:
        print(f"PDF文件不存在: {pdf_path}")
    
    print()


def example_ocr_engine():
    """OCR引擎使用示例"""
    print("=== OCR引擎使用示例 ===")
    
    # 1. 初始化OCR引擎
    ocr_engine = OCREngine(use_gpu=False)
    
    # 2. 处理图像
    image_path = "example.jpg"  # 替换为你的图像文件路径
    if Path(image_path).exists():
        result = ocr_engine.process_page(image_path)
        print(f"OCR结果: {result}")
    else:
        print(f"图像文件不存在: {image_path}")
    
    print()


def example_vector_store():
    """向量存储使用示例"""
    print("=== 向量存储使用示例 ===")
    
    # 1. 初始化向量存储（不使用Milvus）
    vector_store = VectorStore(use_milvus=False)
    
    # 2. 生成文本向量
    texts = ["这是第一段文本", "这是第二段文本", "这是第三段文本"]
    vectors = vector_store.generate_vectors(texts)
    print(f"生成了 {len(vectors)} 个向量")
    
    # 3. 保存到本地
    success = vector_store.save_vectors_locally(vectors, texts, "example_vectors")
    if success:
        print("向量已保存到本地")
    
    # 4. 从本地加载
    load_result = vector_store.load_vectors_from_local("example_vectors")
    if load_result['status'] == 'success':
        print("向量加载成功")
    
    print()


def example_api_server():
    """API服务器使用示例"""
    print("=== API服务器使用示例 ===")
    
    # 1. 初始化API服务器
    server = PDFOCRServer(use_milvus=False)
    
    # 2. 运行服务器
    print("启动API服务器...")
    print("访问 http://localhost:8888/docs 查看API文档")
    
    # 注意：这里只是示例，实际运行时需要取消注释
    # server.run(host="127.0.0.1", port=8888)
    
    print("API服务器示例完成")
    print()


def example_batch_processing():
    """批量处理示例"""
    print("=== 批量处理示例 ===")
    
    # 1. 初始化PDF处理器
    processor = PDFProcessor(use_gpu=False)
    
    # 2. 批量处理PDF文件
    pdf_dir = "pdf_files"  # 替换为你的PDF文件目录
    if Path(pdf_dir).exists():
        results = processor.batch_process(pdf_dir, "batch_output")
        print(f"批量处理完成，共处理 {len(results)} 个文件")
        
        for i, result in enumerate(results):
            print(f"文件 {i+1}: {result['status']}")
    else:
        print(f"PDF目录不存在: {pdf_dir}")
    
    print()


def example_custom_config():
    """自定义配置示例"""
    print("=== 自定义配置示例 ===")
    
    # 你可以修改 config.py 中的配置参数
    # 或者创建自定义配置
    
    from pdf_ocr_module.config import IMAGE_CONFIG, VECTOR_CONFIG
    
    # 修改图像处理配置
    IMAGE_CONFIG["target_resolution"] = 800
    IMAGE_CONFIG["high_resolution"] = 1600
    
    # 修改向量化配置
    VECTOR_CONFIG["model_name"] = "bge-base-zh"
    
    print("配置已修改")
    print()


async def example_async_usage():
    """异步使用示例"""
    print("=== 异步使用示例 ===")
    
    # 1. 初始化组件
    processor = PDFProcessor(use_gpu=False)
    vector_store = VectorStore(use_milvus=False)
    
    # 2. 异步处理多个PDF文件
    pdf_files = ["file1.pdf", "file2.pdf", "file3.pdf"]  # 替换为实际文件路径
    
    async def process_single_pdf(pdf_file):
        """处理单个PDF文件"""
        if Path(pdf_file).exists():
            result = processor.process_pdf(pdf_file)
            if result['status'] == 'success':
                # 生成向量
                texts = [text['text'] for text in result['texts']]
                vectors = vector_store.generate_vectors(texts)
                return {'file': pdf_file, 'vectors': vectors, 'status': 'success'}
            else:
                return {'file': pdf_file, 'status': 'failed', 'error': result['message']}
        else:
            return {'file': pdf_file, 'status': 'not_found'}
    
    # 3. 并发处理
    tasks = [process_single_pdf(pdf_file) for pdf_file in pdf_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 4. 处理结果
    for result in results:
        if isinstance(result, Exception):
            print(f"处理异常: {result}")
        else:
            print(f"文件 {result['file']}: {result['status']}")
    
    print()


def main():
    """主函数"""
    print("PDF OCR 模块使用示例")
    print("=" * 50)
    
    try:
        # 基础使用示例
        example_basic_usage()
        
        # OCR引擎示例
        example_ocr_engine()
        
        # 向量存储示例
        example_vector_store()
        
        # API服务器示例
        example_api_server()
        
        # 批量处理示例
        example_batch_processing()
        
        # 自定义配置示例
        example_custom_config()
        
        # 异步使用示例
        print("运行异步示例...")
        asyncio.run(example_async_usage())
        
    except Exception as e:
        print(f"示例运行出错: {e}")
    
    print("\n所有示例完成！")
    print("\n使用说明:")
    print("1. 确保已安装所有依赖: pip install -r requirements.txt")
    print("2. 修改示例中的文件路径为实际路径")
    print("3. 根据需要调整配置参数")
    print("4. 查看 config.py 了解所有可配置选项")


if __name__ == "__main__":
    main()
