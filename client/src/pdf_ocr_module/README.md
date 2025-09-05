# PDF OCR 向量化模块

一个集成了PDF解析、OCR识别、布局检测、AI内容分析和向量化存储的完整模块。

## 🚀 功能特性

### 核心功能
- **PDF解析**: 支持多页PDF文件解析和图像生成
- **OCR识别**: 基于PaddleOCR的高精度文字识别
- **布局检测**: 智能识别文本、图片、表格等布局元素
- **AI分析**: 使用LLM生成摘要、关键词、结构化内容
- **向量化**: 支持多种向量模型，生成文本向量
- **向量存储**: 集成Milvus向量数据库，支持本地存储

### 高级特性
- **异步处理**: 支持多任务并发处理
- **批量处理**: 一键处理整个目录的PDF文件
- **智能去重**: 自动识别和清理相似图像
- **灵活配置**: 丰富的配置选项，支持GPU/CPU切换
- **API服务**: 提供完整的HTTP API接口

## 📦 安装说明

### 环境要求
- Python 3.8+
- Windows/Linux/macOS
- 可选：GPU支持（CUDA 11.0+）

### 快速安装

1. **克隆模块**
```bash
# 将整个 pdf_ocr_module 文件夹复制到你的项目中
cp -r pdf_ocr_module /path/to/your/project/
```

2. **安装依赖**
```bash
cd pdf_ocr_module
pip install -r requirements.txt
```

3. **验证安装**
```bash
python -c "from pdf_ocr_module import PDFProcessor; print('安装成功!')"
```

### 可选依赖

如果需要使用Milvus向量数据库：
```bash
# 安装Milvus相关依赖
pip install pymilvus

# 启动Milvus服务（使用Docker）
docker-compose up -d
```

## 🎯 快速开始

### 1. 基础使用

```python
from pdf_ocr_module import PDFProcessor

# 初始化处理器
processor = PDFProcessor(use_gpu=False)

# 处理PDF文件
result = processor.process_pdf("document.pdf", "output_name")

# 查看结果
print(f"处理状态: {result['status']}")
print(f"总页数: {result['total_pages']}")
print(f"提取文本数: {len(result['texts'])}")
print(f"识别图片数: {len(result['figures'])}")
print(f"识别表格数: {len(result['tables'])}")
```

### 2. OCR引擎使用

```python
from pdf_ocr_module import OCREngine

# 初始化OCR引擎
ocr_engine = OCREngine(use_gpu=True)

# 处理图像
result = ocr_engine.process_page("page.jpg")
print(f"文本区域: {len(result['text_regions'])}")
print(f"图片区域: {len(result['figure_regions'])}")
print(f"表格区域: {len(result['table_regions'])}")
```

### 3. 向量存储使用

```python
from pdf_ocr_module import VectorStore

# 初始化向量存储
vector_store = VectorStore(use_milvus=False)

# 生成向量
texts = ["文本1", "文本2", "文本3"]
vectors = vector_store.generate_vectors(texts)

# 保存到本地
vector_store.save_vectors_locally(vectors, texts, "my_vectors")
```

### 4. API服务器

```python
from pdf_ocr_module import PDFOCRServer

# 初始化服务器
server = PDFOCRServer(use_milvus=False)

# 启动服务
server.run(host="127.0.0.1", port=8888)
```

## 🔧 配置说明

### 配置文件结构

```python
# config.py 中的主要配置项

# OCR配置
OCR_CONFIG = {
    "use_gpu": True,                    # 是否使用GPU
    "det_limit_side_len": 1440,        # 检测图像最大边长
    "det_db_unclip_ratio": 1.6         # 文本检测参数
}

# 图像处理配置
IMAGE_CONFIG = {
    "target_resolution": 1024,          # 标准分辨率
    "high_resolution": 2560,            # 高分辨率
    "similarity_threshold": 0.8         # 图片相似度阈值
}

# 向量化配置
VECTOR_CONFIG = {
    "model_name": "quentinz/bge-large-zh-v1.5",  # 向量模型
    "num_gpu": 0,                      # GPU数量
    "batch_size": 32                   # 批处理大小
}

# LLM配置
LLM_CONFIG = {
    "base_url": "http://your-llm-server/v1",  # LLM服务地址
    "api_key": "your-api-key",                # API密钥
    "model_name": "gpt-4o-mini"              # 模型名称
}
```

### 自定义配置

```python
from pdf_ocr_module.config import IMAGE_CONFIG, VECTOR_CONFIG

# 修改配置
IMAGE_CONFIG["target_resolution"] = 800
VECTOR_CONFIG["model_name"] = "bge-base-zh"
```

## 📚 API接口

### 主要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/upload` | POST | 上传PDF文件 |
| `/embedding` | POST | 处理PDF嵌入 |
| `/task_status/{task_id}` | GET | 获取任务状态 |
| `/vector_store/create` | POST | 创建向量集合 |
| `/vector_store/search` | POST | 搜索向量 |
| `/batch_process` | POST | 批量处理PDF |

### 使用示例

```bash
# 上传PDF文件
curl -X POST "http://localhost:8888/upload" \
  -F "file=@document.pdf" \
  -F "vector_store_name=my_collection"

# 查询任务状态
curl "http://localhost:8888/task_status/{task_id}"

# 搜索向量
curl -X POST "http://localhost:8888/vector_store/search" \
  -F "collection_name=my_collection" \
  -F "query=搜索关键词" \
  -F "top_k=5"
```

## 🎨 使用场景

### 1. 文档管理
- 批量PDF文档OCR识别
- 自动提取文档结构
- 智能分类和标签

### 2. 知识库构建
- 文档向量化存储
- 语义搜索和检索
- 知识图谱构建

### 3. 内容分析
- 自动生成文档摘要
- 关键词提取和分析
- 内容相似度计算

### 4. 企业应用
- 合同文档处理
- 报告自动分析
- 合规性检查

## 🔍 高级用法

### 批量处理

```python
# 批量处理整个目录
results = processor.batch_process("pdf_directory", "batch_output")

for result in results:
    if result['status'] == 'success':
        print(f"文件 {result['output_path']} 处理成功")
    else:
        print(f"处理失败: {result['message']}")
```

### 异步处理

```python
import asyncio

async def process_multiple_pdfs():
    tasks = []
    for pdf_file in pdf_files:
        task = asyncio.create_task(
            processor.process_pdf(pdf_file)
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

# 运行异步任务
results = asyncio.run(process_multiple_pdfs())
```

### 自定义布局检测

```python
# 使用自定义YOLO模型
from ultralytics import YOLO

custom_model = YOLO("path/to/custom/model.pt")
ocr_engine.layout_model = custom_model
```

## 🐛 故障排除

### 常见问题

1. **PaddleOCR初始化失败**
   - 检查CUDA版本兼容性
   - 尝试使用CPU模式：`use_gpu=False`

2. **内存不足**
   - 降低图像分辨率：修改`IMAGE_CONFIG`
   - 使用批处理模式

3. **LLM连接失败**
   - 检查网络连接
   - 验证API密钥和地址

4. **Milvus连接失败**
   - 检查Docker服务状态
   - 验证端口配置

### 性能优化

1. **GPU加速**
   - 确保CUDA环境正确安装
   - 使用支持GPU的模型

2. **批处理优化**
   - 调整批处理大小
   - 使用异步处理

3. **内存优化**
   - 及时清理临时文件
   - 使用流式处理大文件

## 📝 开发说明

### 项目结构

```
pdf_ocr_module/
├── __init__.py          # 模块初始化
├── config.py            # 配置文件
├── ocr_engine.py        # OCR引擎
├── pdf_processor.py     # PDF处理器
├── llm_processor.py     # LLM处理器
├── vector_store.py      # 向量存储
├── api_server.py        # API服务器
├── example.py           # 使用示例
├── requirements.txt     # 依赖列表
└── README.md           # 说明文档
```

### 扩展开发

1. **添加新的OCR引擎**
   - 继承`OCREngine`类
   - 实现`process_page`方法

2. **支持新的文档格式**
   - 修改`PDFProcessor`类
   - 添加格式检测逻辑

3. **集成新的向量模型**
   - 修改`VectorStore`类
   - 更新配置参数

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请：
1. 查看本文档
2. 运行示例代码
3. 提交Issue
4. 联系维护者

---

**注意**: 首次使用前请确保已正确安装所有依赖，并检查配置文件中的参数设置。
