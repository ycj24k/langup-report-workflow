# -*- coding: utf-8 -*-
"""
研报文件分类管理系统 - 主程序
整合文件扫描、GUI界面和数据库功能
"""
import sys
import os
import traceback
import time
import threading
from tkinter import messagebox
import pandas as pd
from datetime import datetime
from file_scanner import FileScanner
from database_manager import DatabaseManager
from gui_interface import ResearchFileGUI
from cache_manager import FileCache, DatabaseVersionManager, IncrementalScanner
from config import DATABASE_CONFIG
from pathlib import Path


class ResearchFileManager:
    def __init__(self):
        # 初始化时禁用自动OCR，在手动解析时会动态启用
        self.file_scanner = FileScanner(enable_pdf_ocr=False, enable_ppt_ocr=False, enable_office_ocr=False, use_gpu=False)
        self.database_manager = DatabaseManager()
        self.gui = None
        
        # 初始化缓存和版本管理
        self.cache_manager = FileCache()
        self.version_manager = None  # 将在数据库连接成功后初始化
        self.incremental_scanner = None  # 将在版本管理器初始化后创建
        
    def initialize(self):
        """
        初始化系统
        """
        print("正在初始化研报文件分类管理系统...")
        
        # 测试数据库连接
        print("正在测试数据库连接...")
        try:
            if self.database_manager.connect():
                print("数据库连接成功")
                
                # 创建数据库表
                if self.database_manager.create_tables():
                    print("数据库表初始化成功")
                    
                    # 初始化版本管理器
                    self.version_manager = DatabaseVersionManager(self.database_manager)
                    self.incremental_scanner = IncrementalScanner(self.cache_manager, self.version_manager)
                    print("版本管理器和增量扫描器初始化成功")
                else:
                    print("警告: 数据库表初始化失败")
            else:
                print("警告: 数据库连接失败，部分功能可能不可用")
        except Exception as e:
            print(f"警告: 数据库连接失败 ({e})，部分功能可能不可用")
            print("您可以继续使用文件扫描和分类功能，但无法上传到数据库")
        
        # 初始化GUI
        self.gui = ResearchFileGUI()
        
        # 设置回调函数和文件扫描器
        self.gui.set_callbacks(
            scan_callback=self.scan_files,
            upload_callback=self.upload_to_database,
            clear_cache_callback=self.clear_cache,
            parse_callback=self.parse_files
        )
        
        # 传递file_scanner和cache_manager给GUI
        self.gui.file_scanner = self.file_scanner
        self.gui.cache_manager = self.cache_manager
        
        # 启动时尝试加载缓存中的上次扫描结果
        try:
            self._load_cached_into_gui()
        except Exception as e:
            print(f"加载缓存到GUI失败: {e}")
        
        print("系统初始化完成")
        
    def scan_files(self):
        """
        扫描文件回调函数
        """
        try:
            print("开始扫描文件...")
            
            # 使用增量扫描，但不进行自动OCR处理
            if self.incremental_scanner:
                print("使用增量扫描模式（不进行自动OCR）...")
                scan_result = self.incremental_scanner.scan_incremental()
                
                # 合并所有文件
                all_files = (scan_result['new_files'] + 
                           scan_result['updated_files'] + 
                           scan_result['unchanged_files'])
                
                if all_files:
                    print(f"增量扫描完成，共找到 {len(all_files)} 个文件")
                    print(f"  新增: {len(scan_result['new_files'])} 个")
                    print(f"  更新: {len(scan_result['updated_files'])} 个")
                    print(f"  未变化: {len(scan_result['unchanged_files'])} 个")
                    
                    # 对新增/更新的PDF和PPT触发OCR/解析
                    try:
                        changed_paths = {f.get('file_path') for f in (scan_result['new_files'] + scan_result['updated_files'])}
                        processed_files = []
                        for file_info in all_files:
                            ext = str(file_info.get('extension', '')).lower()
                            path = file_info.get('file_path')
                            # 仅对新增/更新的文件做处理，节省时间
                            if path in changed_paths:
                                if ext == '.pdf' and getattr(self.file_scanner, 'enable_pdf_ocr', False):
                                    file_info = self.file_scanner._process_pdf_file(file_info)
                                elif ext in ['.ppt', '.pptx'] and getattr(self.file_scanner, 'enable_ppt_ocr', False):
                                    # 仅当启用了PPT处理时才处理
                                    if hasattr(self.file_scanner, '_process_ppt_file'):
                                        file_info = self.file_scanner._process_ppt_file(file_info)
                            processed_files.append(file_info)
                        all_files = processed_files
                        print("新增/更新文件的OCR与解析已完成")
                    except Exception as e:
                        print(f"自动OCR触发失败: {e}")
                    
                    # 自动导出到Excel文件
                    try:
                        filename = f"scanned_files_{datetime.now().year}.xlsx"
                        # 确保Excel文件保存在data目录中
                        data_dir = Path("data")
                        data_dir.mkdir(exist_ok=True)
                        excel_path = data_dir / filename
                        
                        df = pd.DataFrame(all_files)
                        df.to_excel(excel_path, index=False, engine='openpyxl')
                        print(f"扫描结果已自动导出到: {excel_path}")
                    except Exception as e:
                        print(f"自动导出Excel失败: {e}")
                    
                    return all_files
                else:
                    print("未找到符合条件的文件")
                    return []
            else:
                # 回退到传统扫描（无数据库连接也能缓存）
                print("使用传统扫描模式...")
                files = self.file_scanner.scan_files()
                
                if files:
                    print(f"扫描完成，共找到 {len(files)} 个文件")
                    
                    # 将结果写入本地缓存，便于下次直接加载
                    try:
                        for f in files:
                            # 默认状态
                            if not f.get('status'):
                                f['status'] = 'unchanged'
                            self.cache_manager.update_file_cache(f.get('file_path', ''), f)
                        self.cache_manager.save_cache()
                        print("扫描结果已写入本地缓存")
                    except Exception as e:
                        print(f"写入缓存失败: {e}")
                    
                    # 显示统计信息
                    stats = self.file_scanner.get_statistics()
                    print("\n扫描统计:")
                    print(f"总文件数: {stats['total_files']}")
                    print(f"总大小: {stats['total_size_mb']} MB")
                    
                    # 自动导出到Excel文件
                    try:
                        filename = f"scanned_files_{self.file_scanner.current_year}.xlsx"
                        if self.file_scanner.export_to_excel(filename):
                            print(f"扫描结果已自动导出到: {filename}")
                    except Exception as e:
                        print(f"自动导出Excel失败: {e}")
                    
                    return files
                else:
                    print("未找到符合条件的文件")
                    return []
                
        except Exception as e:
            print(f"扫描文件时出错: {e}")
            traceback.print_exc()
            raise e
    
    def _on_reload_detected(self):
        """
        热重载通知（在GUI线程中更新状态栏）
        """
        try:
            if self.gui and hasattr(self.gui, 'status_label'):
                # 通过 after 确保在GUI主线程执行
                self.gui.root.after(0, lambda: self.gui.status_label.config(text="检测到代码变更，正在重启..."))
        except Exception:
            pass

    def _start_hot_reloader(self):
        """
        启动轻量热重载：监控关键源码文件变化，自动重启进程。
        """
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            watch_names = [
                'main.py',
                'gui_interface.py',
                'file_scanner.py',
                'database_manager.py',
                'cache_manager.py',
                'config.py',
            ]
            watch_files = []
            for name in watch_names:
                p = os.path.join(base_dir, name)
                if os.path.exists(p):
                    watch_files.append(p)
            if not watch_files:
                return

            # 记录初始修改时间
            mtimes = {}
            for p in watch_files:
                try:
                    mtimes[p] = os.path.getmtime(p)
                except OSError:
                    mtimes[p] = 0.0

            def watcher():
                while True:
                    time.sleep(1.0)
                    for p in watch_files:
                        try:
                            m = os.path.getmtime(p)
                        except OSError:
                            m = 0.0
                        old = mtimes.get(p, 0.0)
                        if m != old:
                            # 发现变更，通知并重启
                            self._on_reload_detected()
                            time.sleep(0.3)
                            try:
                                os.execv(sys.executable, [sys.executable] + sys.argv)
                            except Exception:
                                # 兜底退出
                                os._exit(0)
                            return

            t = threading.Thread(target=watcher, daemon=True)
            t.start()
        except Exception:
            # 热重载不可用不影响主流程
            pass

    def parse_files(self, file_indices):
        """
        GUI触发的解析：对选中的文件执行OCR/解析与向量化
        传入的 file_indices 为要解析的文件索引列表
        """
        try:
            if not file_indices:
                print("没有选择要解析的文件")
                return False
            
            print(f"开始解析 {len(file_indices)} 个选中的文件...")
            
            # 获取GUI中的文件数据
            if not self.gui or not hasattr(self.gui, 'files_data') or not self.gui.files_data:
                print("错误: GUI中没有文件数据")
                return False
            
            # 将GUI中的文件数据传递给文件扫描器
            self.file_scanner.scanned_files = self.gui.files_data.copy()
            print(f"已将 {len(self.file_scanner.scanned_files)} 个文件数据传递给文件扫描器")
            
            # 动态启用OCR模块进行手动解析
            print("启用OCR模块进行手动解析...")
            self.file_scanner.enable_pdf_ocr = True
            self.file_scanner.enable_ppt_ocr = True
            self.file_scanner.enable_office_ocr = True
            
            # 读取解析模式（快速/精细）并应用
            if hasattr(self.gui, 'get_parse_mode'):
                mode = self.gui.get_parse_mode()
                print(f"应用解析模式: {mode}")
                if hasattr(self.file_scanner, 'set_parse_mode'):
                    self.file_scanner.set_parse_mode(mode)
            
            # 使用文件扫描器的解析方法
            results = self.file_scanner.parse_selected_files(file_indices)
            
            # 解析完成后重新禁用OCR模块（避免扫描时自动OCR）
            print("解析完成，重新禁用OCR模块...")
            self.file_scanner.enable_pdf_ocr = False
            self.file_scanner.enable_ppt_ocr = False
            self.file_scanner.enable_office_ocr = False
            
            # 检查是否有错误（OCR模块未启用等）
            if results.get('status') == 'error':
                print(f"解析失败: {results['message']}")
                return False
            
            print(f"解析完成: 成功 {results['success']} 个，失败 {results['failed']} 个")
            
            # 显示详细结果
            for detail in results['details']:
                if detail['status'] == 'success':
                    print(f"✓ {detail['file_name']}: {detail['message']}")
                elif detail['status'] == 'failed':
                    print(f"✗ {detail['file_name']}: {detail['message']}")
                elif detail['status'] == 'skipped':
                    print(f"- {detail['file_name']}: {detail['message']}")
            
            # 将更新后的文件数据同步回GUI
            if results['success'] > 0 or results['failed'] > 0:
                self.gui.files_data = self.file_scanner.scanned_files.copy()
                print("已将更新后的文件数据同步回GUI")
            
            return results['success'] > 0
            
        except Exception as e:
            print(f"解析过程中出错: {e}")
            traceback.print_exc()
            return False

    def upload_to_database(self, files_data):
        """
        上传到数据库回调函数
        """
        try:
            if not files_data:
                print("没有数据需要上传")
                return False
            
            # 上传限制：仅允许已解析且符合要求的文件
            filtered = []
            for f in files_data:
                if (f.get('parsing_status') == '已解析' and 
                    f.get('compliance_status') == '符合'):
                    filtered.append(f)
            
            if not filtered:
                print("未找到符合条件的文件，已阻止上传")
                messagebox.showwarning("限制", "只有已解析且状态为'符合'的文件才可上传，请先执行解析")
                return False
            
            # 检查数据库连接
            if not self.database_manager.connection:
                print("数据库未连接，正在重新连接...")
                if not self.database_manager.connect():
                    print("数据库连接失败")
                    return False
            
            print(f"开始上传 {len(filtered)} 个文件到数据库...")
            
            # 生成批次名称
            from datetime import datetime
            batch_name = f"手动上传_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 执行批量上传
            success = self.database_manager.upload_files_batch(filtered, batch_name)
            
            if success:
                print("数据上传成功")
                
                # 显示数据库统计信息
                try:
                    stats = self.database_manager.get_file_statistics()
                    print(f"数据库中现有文件总数: {stats.get('total_files', 0)}")
                except Exception as e:
                    print(f"获取数据库统计信息失败: {e}")
                
                return True
            else:
                print("数据上传失败")
                return False
                
        except Exception as e:
            print(f"上传数据时出错: {e}")
            traceback.print_exc()
            return False
    
    def run(self):
        """
        运行系统
        """
        try:
            self.initialize()
            
            if self.gui:
                print("启动GUI界面...")
                # 启动热重载监控
                self._start_hot_reloader()
                self.gui.run()
            else:
                print("GUI初始化失败")
                
        except KeyboardInterrupt:
            print("\n用户中断程序")
        except Exception as e:
            print(f"程序运行出错: {e}")
            traceback.print_exc()
        finally:
            # 清理资源
            self.cleanup()
    
    def cleanup(self):
        """
        清理资源
        """
        print("正在清理资源...")
        
        if self.database_manager:
            self.database_manager.close()
        
        print("程序已退出")

    def clear_cache(self):
        """
        清空本地缓存
        """
        try:
            if self.cache_manager:
                self.cache_manager.clear_cache()
                print("本地缓存已清空")
                return True
            return False
        except Exception as e:
            print(f"清空缓存失败: {e}")
            return False

    def _load_cached_into_gui(self):
        """
        将缓存中的上次扫描结果（当年数据）加载到GUI，避免首次必须重新扫描。
        """
        if not self.gui:
            return
        cache_files_map = self.cache_manager.get_cached_files() if self.cache_manager else {}
        if not cache_files_map:
            print("缓存中没有历史记录")
            return
        current_year = datetime.now().year
        files = []
        for file_info in cache_files_map.values():
            try:
                c = file_info.get('creation_date')
                m = file_info.get('modification_date')
                a = file_info.get('access_date')
                in_year = False
                for dt in (c, m, a):
                    if dt and hasattr(dt, 'year') and dt.year == current_year:
                        in_year = True
                        break
                if not in_year:
                    continue
                # 默认状态
                if not file_info.get('status'):
                    file_info['status'] = 'unchanged'
                files.append(file_info)
            except Exception:
                continue
        if files:
            print(f"从缓存加载 {len(files)} 条记录到GUI")
            # 直接将数据交给GUI显示
            self.gui.on_scan_complete(files)
        else:
            print("缓存中没有当年数据")


def check_requirements():
    """
    检查系统要求
    """
    print("检查系统要求...")
    
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("错误: 需要Python 3.6或更高版本")
        return False
    
    # 检查必要的模块
    required_modules = [
        'tkinter', 'pandas', 'openpyxl', 'pymysql', 
        'sqlalchemy', 'ttkbootstrap'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("错误: 缺少以下必需的模块:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    print("系统要求检查通过")
    return True


def show_startup_info():
    """
    显示启动信息
    """
    print("=" * 60)
    print("研报文件分类管理系统")
    print("=" * 60)
    print("功能说明:")
    print("1. 扫描网络盘中的研报文件")
    print("2. 获取文件详细信息（创建、修改、访问时间等）")
    print("3. 筛选今年内有更新的文件")
    print("4. 提供图形界面进行手动分类和打标签")
    print("5. 支持批量上传到MySQL数据库")
    print("6. 支持Excel导入/导出功能")
    print("=" * 60)
    print("配置信息:")
    network_path = os.path.join('\\\\', 'NAS', 'study', 'study')
    print(f"网络盘路径: {network_path}")
    print(f"数据库地址: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
    print(f"数据库名称: {DATABASE_CONFIG['database']}")
    print("=" * 60)
    print()


def main():
    """
    主函数
    """
    try:
        # 显示启动信息
        show_startup_info()
        
        # 检查系统要求
        if not check_requirements():
            input("按Enter键退出...")
            return
        
        # 创建并运行管理器
        manager = ResearchFileManager()
        manager.run()
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        traceback.print_exc()
        input("按Enter键退出...")


if __name__ == "__main__":
    main()