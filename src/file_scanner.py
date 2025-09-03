# -*- coding: utf-8 -*-
"""
文件扫描模块
负责扫描网络盘路径，获取文件信息，集成PDF OCR和向量化功能
"""
import os
import time
from datetime import datetime, date
from pathlib import Path
import pandas as pd
from config import NETWORK_PATH, SUPPORTED_EXTENSIONS

# 导入PDF OCR模块
try:
    # 首先尝试导入完整的PDF OCR模块
    from pdf_ocr_module import PDFProcessor, VectorStore
    PDF_OCR_AVAILABLE = True
    print("✓ 使用完整版PDF OCR模块")
except ImportError:
    try:
        # 如果完整版不可用，尝试导入简化版
        from pdf_ocr_module_simple import PDFProcessor, VectorStore
        PDF_OCR_AVAILABLE = True
        print("⚠ 使用简化版PDF OCR模块")
    except ImportError:
        PDF_OCR_AVAILABLE = False
        print("✗ 警告: PDF OCR模块未安装，相关功能将不可用")


class FileScanner:
    def __init__(self, enable_pdf_ocr=True, use_gpu=False, use_milvus=False):
        self.current_year = date.today().year
        self.scanned_files = []
        
        # 初始化PDF OCR功能
        self.enable_pdf_ocr = enable_pdf_ocr and PDF_OCR_AVAILABLE
        if self.enable_pdf_ocr:
            try:
                self.pdf_processor = PDFProcessor(use_gpu=use_gpu)
                self.vector_store = VectorStore(use_milvus=use_milvus)
                print("PDF OCR模块初始化成功")
            except Exception as e:
                print(f"PDF OCR模块初始化失败: {e}")
                self.enable_pdf_ocr = False
        else:
            self.pdf_processor = None
            self.vector_store = None

    def scan_files(self, path=None, process_pdfs=True):
        """
        扫描指定路径下的所有文件
        
        Args:
            path: 扫描路径
            process_pdfs: 是否处理PDF文件（OCR和向量化）
        """
        if path is None:
            path = NETWORK_PATH
            
        print(f"开始扫描路径: {path}")
        
        try:
            # 检查路径是否存在
            if not os.path.exists(path):
                raise FileNotFoundError(f"网络路径不存在: {path}")
            
            file_count = 0
            pdf_count = 0
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    if self._is_supported_file(file):
                        file_path = os.path.join(root, file)
                        try:
                            file_info = self._get_file_info(file_path)
                            if self._is_current_year_file(file_info):
                                # 如果是PDF文件且启用了PDF处理，则进行OCR和向量化
                                if (process_pdfs and self.enable_pdf_ocr and 
                                    file_info['extension'] == '.pdf'):
                                    pdf_count += 1
                                    print(f"发现PDF文件: {file}")
                                    file_info = self._process_pdf_file(file_info)
                                
                                self.scanned_files.append(file_info)
                                file_count += 1
                                print(f"已扫描文件: {file_count}", end='\r')
                        except Exception as e:
                            print(f"处理文件 {file_path} 时出错: {e}")
                            continue
            
            print(f"\n扫描完成，共找到 {len(self.scanned_files)} 个今年内的文件")
            if self.enable_pdf_ocr and pdf_count > 0:
                print(f"其中包含 {pdf_count} 个PDF文件已进行OCR处理和向量化")
            return self.scanned_files
            
        except Exception as e:
            print(f"扫描路径时出错: {e}")
            return []

    def _process_pdf_file(self, file_info):
        """
        处理PDF文件：OCR识别和向量化存储
        
        Args:
            file_info: 文件信息字典
            
        Returns:
            更新后的文件信息字典
        """
        try:
            pdf_path = file_info['file_path']
            file_name = file_info['file_name']
            
            print(f"开始处理PDF: {file_name}")
            
            # 使用PDF处理器进行OCR和内容提取
            result = self.pdf_processor.process_pdf(pdf_path, file_name)
            
            if result['status'] == 'success':
                # 提取文本内容
                texts = result.get('texts', [])
                all_text_content = []
                
                for text_item in texts:
                    if isinstance(text_item, dict) and 'text' in text_item:
                        all_text_content.append(text_item['text'])
                    elif isinstance(text_item, str):
                        all_text_content.append(text_item)
                
                # 合并所有文本内容
                full_text = '\n'.join(all_text_content)
                
                # 生成向量并存储
                if self.vector_store and full_text.strip():
                    try:
                        # 创建向量集合（使用文件名作为集合名）
                        collection_name = f"pdf_{file_name.replace('.', '_')}"
                        self.vector_store.create_collection(collection_name, f"PDF文档: {file_name}")
                        
                        # 生成向量并存储
                        vectors = self.vector_store.generate_vectors([full_text])
                        if vectors:
                            # 保存到本地
                            self.vector_store.save_vectors_locally(
                                vectors, 
                                [full_text], 
                                collection_name
                            )
                            
                            # 更新文件信息
                            file_info['ocr_processed'] = True
                            file_info['text_content'] = full_text[:500] + "..." if len(full_text) > 500 else full_text
                            file_info['text_length'] = len(full_text)
                            file_info['vector_collection'] = collection_name
                            file_info['processing_status'] = 'success'
                            
                            print(f"PDF处理完成: {file_name}")
                        else:
                            file_info['processing_status'] = 'vector_failed'
                            print(f"PDF向量化失败: {file_name}")
                    except Exception as e:
                        print(f"PDF向量化存储失败: {file_name}, 错误: {e}")
                        file_info['processing_status'] = 'vector_failed'
                else:
                    file_info['processing_status'] = 'no_text'
                    print(f"PDF无文本内容: {file_name}")
                
                # 添加其他处理结果
                file_info['total_pages'] = result.get('total_pages', 0)
                file_info['figures_count'] = len(result.get('figures', []))
                file_info['tables_count'] = len(result.get('tables', []))
                file_info['summary'] = result.get('summary', {})
                
            else:
                file_info['processing_status'] = 'failed'
                file_info['error_message'] = result.get('message', '未知错误')
                print(f"PDF处理失败: {file_name}, 错误: {result.get('message', '未知错误')}")
                
        except Exception as e:
            file_info['processing_status'] = 'error'
            file_info['error_message'] = str(e)
            print(f"PDF处理异常: {file_info['file_name']}, 错误: {e}")
        
        return file_info

    def _is_supported_file(self, filename):
        """
        检查文件是否为支持的格式
        """
        _, ext = os.path.splitext(filename.lower())
        return ext in SUPPORTED_EXTENSIONS

    def _get_file_info(self, file_path):
        """
        获取文件的详细信息
        """
        stat_info = os.stat(file_path)
        
        # 获取文件时间信息
        creation_time = datetime.fromtimestamp(stat_info.st_ctime)
        modification_time = datetime.fromtimestamp(stat_info.st_mtime)
        access_time = datetime.fromtimestamp(stat_info.st_atime)
        
        # 获取文件大小（转换为MB）
        file_size = round(stat_info.st_size / (1024 * 1024), 2)
        
        return {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'file_size_mb': file_size,
            'creation_date': creation_time,
            'modification_date': modification_time,
            'access_date': access_time,
            'extension': os.path.splitext(file_path)[1].lower(),
            'category': '',  # 待分类
            'importance': '',  # 待标记重要性
            'tags': '',  # 待添加标签
            'notes': '',  # 备注
            # PDF处理相关字段
            'ocr_processed': False,
            'processing_status': 'pending',
            'text_content': '',
            'text_length': 0,
            'total_pages': 0,
            'figures_count': 0,
            'tables_count': 0,
            'vector_collection': '',
            'summary': {},
            'error_message': ''
        }

    def _is_current_year_file(self, file_info):
        """
        检查文件的任一日期是否在今年内
        """
        current_year = self.current_year
        
        dates_to_check = [
            file_info['creation_date'],
            file_info['modification_date'],
            file_info['access_date']
        ]
        
        for date_obj in dates_to_check:
            if date_obj.year == current_year:
                return True
        
        return False

    def export_to_excel(self, filename="scanned_files.xlsx"):
        """
        导出扫描结果到Excel文件
        """
        if not self.scanned_files:
            print("没有可导出的文件数据")
            return False
        
        try:
            df = pd.DataFrame(self.scanned_files)
            
            # 处理日期列，转换为字符串格式
            date_columns = ['creation_date', 'modification_date', 'access_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"文件信息已导出到: {filename}")
            return True
        except Exception as e:
            print(f"导出Excel文件时出错: {e}")
            return False

    def get_statistics(self):
        """
        获取扫描结果统计信息
        """
        if not self.scanned_files:
            return {}
        
        total_files = len(self.scanned_files)
        total_size = sum(file['file_size_mb'] for file in self.scanned_files)
        
        # 按扩展名统计
        ext_stats = {}
        for file in self.scanned_files:
            ext = file['extension']
            ext_stats[ext] = ext_stats.get(ext, 0) + 1
        
        # 按月份统计（以修改日期为准）
        month_stats = {}
        for file in self.scanned_files:
            month = file['modification_date'].strftime('%Y-%m')
            month_stats[month] = month_stats.get(month, 0) + 1
        
        # PDF处理统计
        pdf_stats = {}
        if self.enable_pdf_ocr:
            pdf_files = [f for f in self.scanned_files if f['extension'] == '.pdf']
            pdf_stats = {
                'total_pdfs': len(pdf_files),
                'processed_successfully': len([f for f in pdf_files if f.get('processing_status') == 'success']),
                'processing_failed': len([f for f in pdf_files if f.get('processing_status') == 'failed']),
                'vector_failed': len([f for f in pdf_files if f.get('processing_status') == 'vector_failed']),
                'no_text': len([f for f in pdf_files if f.get('processing_status') == 'no_text'])
            }
        
        return {
            'total_files': total_files,
            'total_size_mb': round(total_size, 2),
            'extension_stats': ext_stats,
            'month_stats': month_stats,
            'pdf_processing_stats': pdf_stats
        }

    def search_pdf_content(self, query, top_k=5):
        """
        搜索PDF内容（基于向量相似度）
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if not self.enable_pdf_ocr or not self.vector_store:
            print("PDF搜索功能未启用")
            return []
        
        try:
            # 搜索所有PDF文件的向量集合
            results = []
            pdf_files = [f for f in self.scanned_files if f['extension'] == '.pdf' and f.get('vector_collection')]
            
            for pdf_file in pdf_files:
                collection_name = pdf_file['vector_collection']
                try:
                    # 在向量集合中搜索
                    search_result = self.vector_store.search_vectors(
                        collection_name, query, top_k
                    )
                    
                    if search_result and search_result.get('status') == 'success':
                        for item in search_result.get('results', []):
                            results.append({
                                'file_name': pdf_file['file_name'],
                                'file_path': pdf_file['file_path'],
                                'similarity_score': item.get('score', 0),
                                'matched_content': item.get('content', ''),
                                'collection': collection_name
                            })
                except Exception as e:
                    print(f"搜索集合 {collection_name} 时出错: {e}")
                    continue
            
            # 按相似度排序
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            print(f"PDF内容搜索失败: {e}")
            return []


# 测试函数
def test_scanner():
    """
    测试文件扫描功能
    """
    # 初始化扫描器，启用PDF OCR功能
    scanner = FileScanner(enable_pdf_ocr=True, use_gpu=False, use_milvus=False)
    
    # 如果网络路径不可用，使用本地测试路径
    test_path = NETWORK_PATH
    if not os.path.exists(test_path):
        test_path = os.getcwd()  # 使用当前目录作为测试
        print(f"网络路径不可用，使用测试路径: {test_path}")
    
    # 扫描文件，启用PDF处理
    files = scanner.scan_files(test_path, process_pdfs=True)
    
    if files:
        stats = scanner.get_statistics()
        print("\n扫描统计:")
        print(f"总文件数: {stats['total_files']}")
        print(f"总大小: {stats['total_size_mb']} MB")
        print("\n文件类型分布:")
        for ext, count in stats['extension_stats'].items():
            print(f"  {ext}: {count} 个")
        
        # PDF处理统计
        if 'pdf_processing_stats' in stats and stats['pdf_processing_stats']:
            pdf_stats = stats['pdf_processing_stats']
            print(f"\nPDF处理统计:")
            print(f"  总PDF文件: {pdf_stats['total_pdfs']}")
            print(f"  处理成功: {pdf_stats['processed_successfully']}")
            print(f"  处理失败: {pdf_stats['processing_failed']}")
            print(f"  向量化失败: {pdf_stats['vector_failed']}")
            print(f"  无文本内容: {pdf_stats['no_text']}")
        
        # 导出前5个文件作为示例
        if len(files) > 5:
            files_sample = files[:5]
        else:
            files_sample = files
        
        print("\n文件示例:")
        for i, file in enumerate(files_sample, 1):
            print(f"{i}. {file['file_name']}")
            print(f"   路径: {file['file_path']}")
            print(f"   大小: {file['file_size_mb']} MB")
            print(f"   修改时间: {file['modification_date']}")
            
            # 如果是PDF文件，显示处理状态
            if file['extension'] == '.pdf':
                status = file.get('processing_status', 'unknown')
                print(f"   PDF状态: {status}")
                if file.get('ocr_processed'):
                    print(f"   文本长度: {file.get('text_length', 0)} 字符")
                    print(f"   向量集合: {file.get('vector_collection', 'N/A')}")
            print()
    
    return files


if __name__ == "__main__":
    test_scanner()