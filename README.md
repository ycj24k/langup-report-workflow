# 研报文件分类管理系统

一个用于扫描、分类和管理研报文件的Python应用程序，支持从网络盘读取文件信息，手动分类打标签，并批量上传到MySQL数据库。

## 功能特性

- 📂 **文件扫描**: 扫描网络盘中的研报文件，获取详细信息
- 📅 **日期筛选**: 自动筛选今年内有更新的文件
- 🏷️ **手动分类**: 图形化界面支持手动分类和打标签
- 💾 **数据库存储**: 批量上传文件信息到MySQL数据库
- 📊 **Excel支持**: 支持Excel文件导入/导出
- 📈 **统计信息**: 提供详细的文件统计信息

## 快速开始

### 1. 环境要求
- Windows 10/11
- Python 3.6+（建议使用Python 3.13）
- MySQL 5.7+
- 网络盘访问权限

### 2. 安装依赖
```bash
# 运行安装脚本
install.bat

# 或手动安装
python -m pip install -r requirements.txt
```

### 3. 配置数据库
编辑 `config.py` 文件，修改数据库连接信息：
```python
DATABASE_CONFIG = {
    'host': '192.168.3.104',
    'port': 3306,
    'user': 'your_username',
    'password': 'your_password',
    'database': 'research_reports',
    'charset': 'utf8mb4'
}
```

### 4. 运行程序
```bash
# 方式1: 双击运行
run.bat

# 方式2: 命令行运行
python main.py
```

## 项目结构

```
langup-report-workflow/
├── main.py                 # 主程序入口
├── file_scanner.py         # 文件扫描模块
├── database_manager.py     # 数据库管理模块
├── gui_interface.py        # GUI界面模块
├── config.py              # 配置文件
├── requirements.txt       # Python依赖
├── install.bat           # 安装脚本
├── run.bat              # 运行脚本
├── test_database.py     # 数据库测试工具
├── test_scan.py         # 文件扫描测试工具
├── config_template.py   # 配置文件模板
├── 使用说明.md          # 详细使用说明
└── README.md           # 项目说明
```

## 使用方法

### 基本流程
1. **扫描文件**: 点击"扫描文件"按钮，扫描网络盘中的研报文件
2. **分类标记**: 在界面中对文件进行分类和标签设置
3. **保存数据**: 将分类结果导出为Excel或上传到数据库

### 主要功能
- **文件扫描**: 自动扫描 `\\NAS\study\study` 路径
- **智能筛选**: 只显示今年内有更新的文件
- **多维分类**: 支持分类、重要性、标签、备注等多维度标记
- **批量处理**: 支持批量上传和导出操作

## 测试工具

### 数据库连接测试
```bash
python test_database.py
```

### 文件扫描测试
```bash
python test_scan.py
```

## 配置说明

### 网络路径配置
默认扫描路径为 `\\NAS\study\study`，可在 `config.py` 中修改。

### 文件格式支持
默认支持：PDF, DOC, DOCX, TXT, XLS, XLSX, PPT, PPTX

### 分类体系
- 宏观经济
- 行业研究
- 公司研究
- 投资策略
- 固定收益
- 量化研究
- 其他

## 数据库表结构

### research_files (主表)
- 文件基本信息（名称、路径、大小等）
- 时间信息（创建、修改、访问时间）
- 分类信息（分类、重要性、标签、备注）

### upload_batches (批次记录)
- 批次上传记录和统计信息

### file_categories (分类管理)
- 文件分类定义和颜色配置

## 常见问题

### Q: 网络盘路径无法访问？
A: 请确保网络连接正常，并且有权限访问指定路径。

### Q: 数据库连接失败？
A: 请检查数据库服务器状态和配置信息，运行 `test_database.py` 进行诊断。

### Q: 扫描速度慢？
A: 网络盘访问速度影响扫描效率，建议分批次处理大量文件。

## 技术栈

- **语言**: Python 3.6+
- **GUI**: tkinter + ttkbootstrap
- **数据库**: MySQL + SQLAlchemy + PyMySQL
- **数据处理**: pandas + openpyxl
- **文件操作**: pathlib + os

## 许可证

本项目采用 MIT 许可证。

## 更新记录

- **v1.0.0** (2024-12-28)
  - 初始版本发布
  - 实现文件扫描、分类、数据库存储等核心功能
