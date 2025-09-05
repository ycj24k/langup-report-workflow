# 📁 项目结构说明

## 🏗️ 重构后的项目结构

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
│       ├── 📄 __init__.py
│       ├── 📄 api_server.py
│       ├── 📄 config.py
│       ├── 📄 example.py
│       ├── 📄 llm_processor.py
│       ├── 📄 ocr_engine.py
│       ├── 📄 pdf_processor.py
│       ├── 📄 README.md
│       ├── 📄 requirements.txt
│       └── 📄 vector_store.py
│
├── 📁 docs/                         # 文档目录
│   ├── 📄 README.md                 # 项目说明
│   ├── 📄 使用说明.md               # 使用说明
│   ├── 📄 OCR向量库修复总结.md      # 修复总结
│   ├── 📄 升级完成总结.md           # 升级总结
│   └── 📄 分类体系说明.md           # 分类体系说明
│
├── 📁 tests/                        # 测试目录
│   └── 📄 (测试文件将放在这里)
│
├── 📁 scripts/                      # 脚本目录
│   ├── 📄 install.bat               # 安装脚本
│   └── 📄 run.bat                   # 运行脚本
│
├── 📁 data/                         # 数据目录
│   ├── 📄 scanned_files_2025.xlsx   # 扫描文件记录
│   ├── 📄 scanned_files_full_20250903_101631.xlsx
│   └── 📄 file_cache.pkl            # 文件缓存
│
├── 📄 requirements.txt               # Python依赖
├── 📄 PROJECT_STRUCTURE.md          # 项目结构说明
└── 📄 .git/                         # Git版本控制
```

## 🔄 重构说明

### 清理的文件
- ❌ `test_*.py` - 测试文件（已清理）
- ❌ `demo_*.py` - 演示文件（已清理）
- ❌ `pdf_ocr_module_simple.py` - 简化模块（已清理）
- ❌ `__pycache__/` - Python缓存（已清理）
- ❌ 重复的Excel文件（已清理）
- ❌ 临时测试文档（已清理）

### 保留的核心文件
- ✅ `main.py` - 主程序
- ✅ `config.py` - 配置管理
- ✅ `file_scanner.py` - 文件扫描
- ✅ `gui_interface.py` - 用户界面
- ✅ `cache_manager.py` - 缓存管理
- ✅ `database_manager.py` - 数据库管理
- ✅ `pdf_ocr_module/` - PDF OCR模块

### 新增的目录结构
- 📁 `src/` - 源代码集中管理
- 📁 `docs/` - 文档集中管理
- 📁 `tests/` - 测试文件管理
- 📁 `scripts/` - 脚本文件管理
- 📁 `data/` - 数据文件管理

## 🚀 使用方法

### 运行程序
```bash
# 从项目根目录运行
python src/main.py

# 或使用脚本
scripts/run.bat
```

### 安装依赖
```bash
# 安装Python依赖
pip install -r requirements.txt

# 或使用脚本
scripts/install.bat
```

### 开发调试
```bash
# 进入源代码目录
cd src

# 运行特定模块
python file_scanner.py
python gui_interface.py
```

## 📋 目录职责

### `src/` - 源代码
- 包含所有核心业务逻辑
- 模块化组织，便于维护
- 统一的导入路径管理

### `docs/` - 文档
- 项目说明和使用指南
- 技术文档和修复记录
- 版本更新说明

### `tests/` - 测试
- 单元测试和集成测试
- 测试数据和测试脚本
- 质量保证相关文件

### `scripts/` - 脚本
- 安装和部署脚本
- 运行和调试脚本
- 自动化工具脚本

### `data/` - 数据
- 程序运行时生成的数据
- 缓存文件和临时文件
- 用户上传和处理的文件
- **导出的扫描文件和生成的数据**

## 🔧 维护建议

1. **代码开发**: 在 `src/` 目录下进行
2. **文档更新**: 在 `docs/` 目录下管理
3. **测试编写**: 在 `tests/` 目录下组织
4. **脚本管理**: 在 `scripts/` 目录下维护
5. **数据管理**: 
   - 定期清理 `data/` 目录中的临时文件
   - 保留重要的导出数据文件
   - 备份重要的扫描记录

## 📝 注意事项

- 所有Python模块的导入路径需要更新
- 运行脚本时需要从正确的目录执行
- 配置文件中的路径可能需要调整
- 建议使用相对路径避免硬编码
- **所有导出和生成的数据文件都存放在data目录中**

## 📊 文件分类说明

### docs目录包含
- 📄 项目文档和说明
- 📄 技术文档和修复记录
- 📄 版本更新说明

### data目录包含
- 📄 程序运行时缓存
- 📄 临时生成的数据
- 📄 用户上传和处理的文件
- 📄 **导出的扫描文件记录**
- 📄 **生成的数据文件**

这样的结构更加清晰，所有数据文件集中在data目录，便于管理和备份！🎉
