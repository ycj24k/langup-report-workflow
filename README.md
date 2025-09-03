# 🚀 研报文件分类管理系统

## 📋 项目简介

研报文件分类管理系统是一个基于Python的智能文件管理工具，专门用于处理和研究报告PDF文件。系统具备以下核心功能：

- 🔍 **智能文件扫描**: 自动扫描网络盘中的研报文件
- 📊 **OCR识别**: 使用PaddleOCR进行PDF文本识别
- 🧠 **AI分析**: 基于LLM的内容摘要和关键词提取
- 🔢 **向量化存储**: 支持本地存储和Milvus数据库
- 🖥️ **图形界面**: 直观的GUI操作界面
- 💾 **数据库管理**: MySQL数据库存储和查询

## 🏗️ 项目结构

```
langup-report-workflow/
├── 📁 src/                          # 源代码目录
│   ├── 📄 main.py                   # 主程序入口
│   ├── 📄 config.py                 # 配置文件
│   ├── 📄 file_scanner.py           # 文件扫描器
│   ├── 📄 gui_interface.py          # GUI界面
│   ├── 📄 cache_manager.py          # 缓存管理器
│   ├── 📄 database_manager.py       # 数据库管理器
│   └── 📁 pdf_ocr_module/          # PDF OCR模块
├── 📁 docs/                         # 文档目录
├── 📁 tests/                        # 测试目录
├── 📁 scripts/                      # 脚本目录
└── 📁 data/                         # 数据目录
```

详细结构说明请查看 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+
- Windows 10/11

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd langup-report-workflow
   ```

2. **安装依赖**
   ```bash
   # 使用安装脚本
   scripts/install.bat
   
   # 或手动安装
   pip install -r requirements.txt
   pip install -r src/pdf_ocr_module/requirements.txt
   ```

3. **配置数据库**
   - 编辑 `src/config.py` 文件
   - 设置数据库连接信息
   - 确保MySQL服务运行

4. **运行程序**
   ```bash
   # 使用运行脚本
   scripts/run.bat
   
   # 或直接运行
   python src/main.py
   ```

## 🎯 核心功能

### 文件扫描
- 自动扫描指定网络路径
- 智能识别文件类型和更新时间
- 支持增量扫描和缓存管理

### PDF OCR处理
- 基于PaddleOCR的文本识别
- 智能布局检测（文本、图片、表格）
- 多语言支持

### AI内容分析
- 文本摘要生成
- 关键词提取
- 内容分类和标签

### 向量化存储
- 支持多种向量化模型
- 本地存储和Milvus数据库
- 智能搜索和相似度匹配

### 用户界面
- 直观的图形操作界面
- 文件列表和预览功能
- 批量操作和进度显示

## 📖 使用说明

详细使用说明请查看 [docs/使用说明.md](docs/使用说明.md)

## 🔧 配置说明

### 基础配置
- 网络盘路径配置
- 数据库连接设置
- OCR模型参数调整

### 高级配置
- 向量化模型选择
- 缓存策略设置
- 日志级别配置

## 🧪 测试

```bash
# 运行测试
cd tests
python -m pytest

# 或运行特定测试
python test_file_scanner.py
```

## 📝 开发说明

### 代码规范
- 遵循PEP 8编码规范
- 使用类型注解
- 完整的文档字符串

### 模块结构
- 清晰的模块划分
- 统一的接口设计
- 完善的错误处理

### 扩展开发
- 支持插件式架构
- 易于添加新功能
- 模块化设计

## 🐛 问题反馈

如果您遇到问题或有改进建议，请：

1. 查看 [docs/OCR向量库修复总结.md](docs/OCR向量库修复总结.md)
2. 检查日志文件
3. 提交Issue或Pull Request

## 📄 许可证

本项目采用 MIT 许可证

## 🤝 贡献

欢迎贡献代码和文档！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📞 联系方式

- 项目维护者: [您的姓名]
- 邮箱: [您的邮箱]
- 项目地址: [项目URL]

---

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**
