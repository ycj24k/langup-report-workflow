# -*- coding: utf-8 -*-
"""
文件扫描模块
负责扫描网络盘路径，获取文件信息，集成PDF、PPT和Office OCR功能
"""
import os
import time
from datetime import datetime, date
from pathlib import Path
import pandas as pd
from config import NETWORK_PATH, SUPPORTED_EXTENSIONS, COMPLIANCE_STATUS, PARSING_STATUS, OCR_CONFIG
from ocr_task_manager import get_task_manager, OCRTask, TaskStatus
from typing import List, Dict

# 导入PDF、PPT和Office OCR模块
try:
    # 首先尝试导入完整的PDF OCR模块
    from pdf_ocr_module import PDFProcessor, PPTProcessor, OfficeProcessor
    PDF_OCR_AVAILABLE = True
    PPT_OCR_AVAILABLE = True
    OFFICE_OCR_AVAILABLE = True
    print("✓ 使用完整版PDF、PPT和Office OCR模块")
except ImportError:
    try:
        # 如果完整版不可用，尝试导入简化版
        from pdf_ocr_module_simple import PDFProcessor, PPTProcessor
        PDF_OCR_AVAILABLE = True
        PPT_OCR_AVAILABLE = True
        OFFICE_OCR_AVAILABLE = False
        print("⚠ 使用简化版PDF和PPT OCR模块，Office功能不可用")
    except ImportError:
        PDF_OCR_AVAILABLE = False
        PPT_OCR_AVAILABLE = False
        OFFICE_OCR_AVAILABLE = False
        print("✗ 警告: PDF、PPT和Office OCR模块未安装，相关功能将不可用")


class FileScanner:
    def __init__(self, enable_pdf_ocr=True, enable_ppt_ocr=True, enable_office_ocr=True, use_gpu=False):
        self.current_year = date.today().year
        self.scanned_files = []
        
        # 初始化任务管理器
        self.task_manager = get_task_manager()
        self.task_manager.start()
        
        # 初始化PDF OCR功能
        self.enable_pdf_ocr = enable_pdf_ocr and PDF_OCR_AVAILABLE
        self.pdf_processor = None
        if self.enable_pdf_ocr:
            try:
                self.pdf_processor = PDFProcessor(use_gpu=use_gpu)
                print("PDF OCR模块初始化成功")
            except Exception as e:
                print(f"PDF OCR模块初始化失败: {e}")
                self.enable_pdf_ocr = False
        
        # 初始化PPT OCR功能
        self.enable_ppt_ocr = enable_ppt_ocr and PPT_OCR_AVAILABLE
        self.ppt_processor = None
        if self.enable_ppt_ocr:
            try:
                self.ppt_processor = PPTProcessor()
                print("PPT OCR模块初始化成功")
            except Exception as e:
                print(f"PPT OCR模块初始化失败: {e}")
                self.enable_ppt_ocr = False
        
        # 初始化Office OCR功能
        self.enable_office_ocr = enable_office_ocr and OFFICE_OCR_AVAILABLE
        self.office_processor = None
        if self.enable_office_ocr:
            try:
                self.office_processor = OfficeProcessor(use_gpu=use_gpu)
                print("Office OCR模块初始化成功")
            except Exception as e:
                print(f"Office OCR模块初始化失败: {e}")
                self.enable_office_ocr = False
        
        self.parse_mode = "快速"
    
    def _ensure_processors_available(self):
        """确保处理器可用，如果未初始化则动态创建"""
        # 确保PDF处理器可用
        if self.enable_pdf_ocr and not self.pdf_processor:
            try:
                self.pdf_processor = PDFProcessor()
                print("动态创建PDF处理器成功")
            except Exception as e:
                print(f"动态创建PDF处理器失败: {e}")
                self.enable_pdf_ocr = False
        
        # 确保PPT处理器可用
        if self.enable_ppt_ocr and not self.ppt_processor:
            try:
                self.ppt_processor = PPTProcessor()
                print("动态创建PPT处理器成功")
            except Exception as e:
                print(f"动态创建PPT处理器失败: {e}")
                self.enable_ppt_ocr = False
        
        # 确保Office处理器可用
        if self.enable_office_ocr and not self.office_processor:
            try:
                self.office_processor = OfficeProcessor()
                print("动态创建Office处理器成功")
            except Exception as e:
                print(f"动态创建Office处理器失败: {e}")
                self.enable_office_ocr = False

    def scan_files(self, path=None, recursive=True):
        """扫描指定路径下的文件"""
        if path is None:
            path = NETWORK_PATH
        
        print(f"开始扫描路径: {path}")
        print(f"递归扫描: {recursive}")
        print(f"支持的文件格式: {SUPPORTED_EXTENSIONS}")
        
        scanned_files = []
        
        if not os.path.exists(path):
            print(f"路径不存在: {path}")
            return scanned_files
        
        try:
            if recursive:
                # 递归扫描所有子目录
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_info = self._get_file_info(file_path)
                        if file_info:
                            scanned_files.append(file_info)
            else:
                # 只扫描当前目录
                for file in os.listdir(path):
                    file_path = os.path.join(path, file)
                    if os.path.isfile(file_path):
                        file_info = self._get_file_info(file_path)
                        if file_info:
                            scanned_files.append(file_info)
            
            print(f"扫描完成，共找到 {len(scanned_files)} 个文件")
            self.scanned_files = scanned_files
            return scanned_files
            
        except Exception as e:
            print(f"扫描文件时出错: {e}")
            return []

    def _get_file_info(self, file_path):
        """获取文件基本信息"""
        try:
            if not os.path.isfile(file_path):
                return None
            
            # 检查文件扩展名
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in SUPPORTED_EXTENSIONS:
                return None
            
            # 获取文件统计信息
            stat = os.stat(file_path)
            file_size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            created_time = datetime.fromtimestamp(stat.st_ctime)
            
            # 获取相对路径
            try:
                relative_path = os.path.relpath(file_path, NETWORK_PATH)
            except ValueError:
                relative_path = file_path
            
            file_info = {
                'file_path': file_path,
                'relative_path': relative_path,
                'file_name': os.path.basename(file_path),
                'file_extension': file_ext,
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'modified_time': modified_time,
                'created_time': created_time,
                'year': modified_time.year,
                'month': modified_time.month,
                'day': modified_time.day,
                'compliance_status': '待定',
                'parsing_status': '未解析',
                'processing_status': 'pending',
                'text_content': '',
                'summary': '',
                'keywords': '',
                'categories': [],
                'category_descriptions': [],
                'category_confidence': 0.0,
                'tags': [],
                'scan_time': datetime.now()
            }
            
            return file_info
            
        except Exception as e:
            print(f"获取文件信息失败 {file_path}: {e}")
            return None

    def _process_pdf_file(self, file_path, file_info):
        """处理PDF文件"""
        if not self.enable_pdf_ocr or not self.pdf_processor:
            print(f"PDF OCR功能未启用，跳过: {file_path}")
            return file_info
        
        try:
            print(f"开始处理PDF文件: {file_path}")
            result = self.pdf_processor.process_pdf(file_path)
            
            if result and result.get('success'):
                file_info['processing_status'] = 'success'
                file_info['text_content'] = result.get('text_content', '')
                file_info['summary'] = result.get('summary', '')
                file_info['keywords'] = result.get('keywords', '')
                file_info['categories'] = result.get('categories', [])
                file_info['category_descriptions'] = result.get('category_descriptions', [])
                file_info['category_confidence'] = result.get('category_confidence', 0.0)
                file_info['tags'] = result.get('tags', [])
                print(f"PDF处理成功: {file_path}")
            else:
                file_info['processing_status'] = 'failed'
                print(f"PDF处理失败: {file_path}")
                
        except Exception as e:
            file_info['processing_status'] = 'error'
            print(f"PDF处理出错: {file_path}, 错误: {e}")
        
        return file_info

    def _process_ppt_file(self, file_path, file_info):
        """处理PPT文件"""
        if not self.enable_ppt_ocr or not self.ppt_processor:
            print(f"PPT OCR功能未启用，跳过: {file_path}")
            return file_info
        
        try:
            print(f"开始处理PPT文件: {file_path}")
            result = self.ppt_processor.process_ppt(file_path)
            
            if result and result.get('success'):
                file_info['processing_status'] = 'success'
                file_info['text_content'] = result.get('text_content', '')
                file_info['summary'] = result.get('summary', '')
                file_info['keywords'] = result.get('keywords', '')
                print(f"PPT处理成功: {file_path}")
            else:
                file_info['processing_status'] = 'failed'
                print(f"PPT处理失败: {file_path}")
                
        except Exception as e:
            file_info['processing_status'] = 'error'
            print(f"PPT处理出错: {file_path}, 错误: {e}")
        
        return file_info

    def _process_office_file(self, file_path, file_info):
        """处理Office文件（Word、Excel）"""
        if not self.enable_office_ocr or not self.office_processor:
            print(f"Office OCR功能未启用，跳过: {file_path}")
            return file_info
        
        try:
            print(f"开始处理Office文件: {file_path}")
            result = self.office_processor.process_office(file_path)
            
            if result and result.get('success'):
                file_info['processing_status'] = 'success'
                file_info['text_content'] = result.get('text_content', '')
                file_info['summary'] = result.get('summary', '')
                file_info['keywords'] = result.get('keywords', '')
                print(f"Office处理成功: {file_path}")
            else:
                file_info['processing_status'] = 'failed'
                print(f"Office处理失败: {file_path}")
                
        except Exception as e:
            file_info['processing_status'] = 'error'
            print(f"Office处理出错: {file_path}, 错误: {e}")
        
        return file_info

    def parse_selected_files(self, file_paths, progress_callback=None):
        """解析选中的文件"""
        if not file_paths:
            print("没有选择要解析的文件")
            return []
        
        print(f"开始解析 {len(file_paths)} 个文件")
        
        # 确保处理器可用
        self._ensure_processors_available()
        
        results = []
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            try:
                # 检查文件是否正在处理中
                if self.is_file_processing(file_path):
                    print(f"文件正在处理中，跳过: {file_path}")
                    continue
                
                # 获取文件信息
                file_info = self._get_file_info(file_path)
                if not file_info:
                    continue
                
                # 根据文件类型选择处理器
                file_ext = file_info['file_extension'].lower()
                
                if file_ext == '.pdf':
                    file_info = self._process_pdf_file(file_path, file_info)
                elif file_ext in ['.ppt', '.pptx']:
                    file_info = self._process_ppt_file(file_path, file_info)
                elif file_ext in ['.doc', '.docx', '.xls', '.xlsx']:
                    file_info = self._process_office_file(file_path, file_info)
                else:
                    print(f"不支持的文件类型: {file_ext}")
                    continue
                
                results.append(file_info)
                
                # 更新进度
                if progress_callback:
                    progress = (i + 1) / total_files * 100
                    progress_callback(progress, f"已处理 {i + 1}/{total_files} 个文件")
                
                print(f"文件处理完成: {file_path}")
                
            except Exception as e:
                print(f"处理文件时出错 {file_path}: {e}")
                continue
        
        print(f"解析完成，共处理 {len(results)} 个文件")
        return results

    def submit_ocr_tasks(self, file_paths, progress_callback=None):
        """提交OCR任务到任务管理器"""
        if not file_paths:
            print("没有选择要处理的文件")
            return []
        
        print(f"提交 {len(file_paths)} 个OCR任务")
        
        task_ids = []
        for file_path in file_paths:
            try:
                # 检查文件是否正在处理中
                if self.is_file_processing(file_path):
                    print(f"文件正在处理中，跳过: {file_path}")
                    continue
                
                # 创建OCR任务
                task = OCRTask(
                    file_path=file_path,
                    task_type="ocr_analysis",
                    callback=progress_callback
                )
                
                # 提交任务
                task_id = self.task_manager.submit_task(task)
                task_ids.append(task_id)
                
                print(f"OCR任务已提交: {file_path} (ID: {task_id})")
                
            except Exception as e:
                print(f"提交OCR任务失败 {file_path}: {e}")
                continue
        
        print(f"共提交 {len(task_ids)} 个OCR任务")
        return task_ids

    def get_ocr_progress(self):
        """获取OCR任务进度统计"""
        return self.task_manager.get_statistics()

    def get_running_tasks(self):
        """获取正在运行的任务"""
        return self.task_manager.get_running_tasks()

    def cancel_ocr_task(self, task_id):
        """取消OCR任务"""
        return self.task_manager.cancel_task(task_id)

    def is_file_processing(self, file_path):
        """检查文件是否正在处理中"""
        return self.task_manager.is_file_locked(file_path)

    def search_document_content(self, query, file_paths=None, top_k=10):
        """搜索文档内容（简化版，不使用向量库）"""
        if not query.strip():
            return []
        
        print(f"搜索内容: {query}")
        
        # 如果没有指定文件路径，使用扫描的文件
        if file_paths is None:
            file_paths = [f['file_path'] for f in self.scanned_files]
        
        results = []
        
        for file_path in file_paths:
            try:
                # 获取文件信息
                file_info = self._get_file_info(file_path)
                if not file_info:
                    continue
                
                # 简单的文本搜索
                text_content = file_info.get('text_content', '')
                if query.lower() in text_content.lower():
                    # 计算相关性分数（简单的关键词匹配）
                    score = text_content.lower().count(query.lower()) / len(text_content) if text_content else 0
                    
                    results.append({
                        'file_path': file_path,
                        'file_name': file_info['file_name'],
                        'score': score,
                        'text_content': text_content[:500] + '...' if len(text_content) > 500 else text_content
                    })
                    
            except Exception as e:
                print(f"搜索文件时出错 {file_path}: {e}")
                continue
        
        # 按相关性分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"搜索完成，找到 {len(results)} 个相关文件")
        return results[:top_k]

    def get_statistics(self):
        """获取扫描统计信息"""
        if not self.scanned_files:
            return {
                'total_files': 0,
                'pdf_files': 0,
                'ppt_files': 0,
                'office_files': 0,
                'other_files': 0,
                'total_size_mb': 0,
                'processed_files': 0,
                'failed_files': 0
            }
        
        stats = {
            'total_files': len(self.scanned_files),
            'pdf_files': 0,
            'ppt_files': 0,
            'office_files': 0,
            'other_files': 0,
            'total_size_mb': 0,
            'processed_files': 0,
            'failed_files': 0
        }
        
        for file_info in self.scanned_files:
            file_ext = file_info['file_extension'].lower()
            stats['total_size_mb'] += file_info['file_size_mb']
            
            if file_ext == '.pdf':
                stats['pdf_files'] += 1
            elif file_ext in ['.ppt', '.pptx']:
                stats['ppt_files'] += 1
            elif file_ext in ['.doc', '.docx', '.xls', '.xlsx']:
                stats['office_files'] += 1
            else:
                stats['other_files'] += 1
            
            if file_info.get('processing_status') == 'success':
                stats['processed_files'] += 1
            elif file_info.get('processing_status') in ['failed', 'error']:
                stats['failed_files'] += 1
        
        return stats

    def export_to_excel(self, output_path=None):
        """导出扫描结果到Excel文件"""
        if not self.scanned_files:
            print("没有扫描结果可导出")
            return None
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"scanned_files_{timestamp}.xlsx"
        
        try:
            # 准备导出数据
            export_data = []
            for file_info in self.scanned_files:
                export_data.append({
                    '文件路径': file_info['file_path'],
                    '相对路径': file_info['relative_path'],
                    '文件名': file_info['file_name'],
                    '文件扩展名': file_info['file_extension'],
                    '文件大小(MB)': file_info['file_size_mb'],
                    '修改时间': file_info['modified_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    '创建时间': file_info['created_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    '年份': file_info['year'],
                    '月份': file_info['month'],
                    '日期': file_info['day'],
                    '合规状态': file_info['compliance_status'],
                    '解析状态': file_info['parsing_status'],
                    '处理状态': file_info['processing_status'],
                    '文本内容': file_info['text_content'][:1000] + '...' if len(file_info['text_content']) > 1000 else file_info['text_content'],
                    '摘要': file_info['summary'],
                    '关键词': file_info['keywords'],
                    '分类': ', '.join([cat.get('name', '') if isinstance(cat, dict) else str(cat) for cat in file_info['categories']]),
                    '分类描述': ', '.join(file_info['category_descriptions']),
                    '分类置信度': file_info['category_confidence'],
                    '标签': ', '.join(file_info['tags']),
                    '扫描时间': file_info['scan_time'].strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # 创建DataFrame并导出
            df = pd.DataFrame(export_data)
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            print(f"扫描结果已导出到: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"导出Excel文件失败: {e}")
            return None
