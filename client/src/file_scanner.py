# -*- coding: utf-8 -*-
"""
文件扫描模块
负责扫描网络盘路径，获取文件信息，集成PDF和PPT OCR和向量化功能
"""
import os
import time
from datetime import datetime, date
from pathlib import Path
import pandas as pd
from config import NETWORK_PATH, SUPPORTED_EXTENSIONS, COMPLIANCE_STATUS, PARSING_STATUS, OCR_CONFIG

# 导入PDF和PPT OCR模块
try:
    # 首先尝试导入完整的PDF OCR模块
    from pdf_ocr_module import PDFProcessor, PPTProcessor, VectorStore
    PDF_OCR_AVAILABLE = True
    PPT_OCR_AVAILABLE = True
    print("✓ 使用完整版PDF和PPT OCR模块")
except ImportError:
    try:
        # 如果完整版不可用，尝试导入简化版
        from pdf_ocr_module_simple import PDFProcessor, PPTProcessor, VectorStore
        PDF_OCR_AVAILABLE = True
        PPT_OCR_AVAILABLE = True
        print("⚠ 使用简化版PDF和PPT OCR模块")
    except ImportError:
        PDF_OCR_AVAILABLE = False
        PPT_OCR_AVAILABLE = False
        print("✗ 警告: PDF和PPT OCR模块未安装，相关功能将不可用")


class FileScanner:
    def __init__(self, enable_pdf_ocr=True, enable_ppt_ocr=True, use_gpu=False, use_milvus=False):
        self.current_year = date.today().year
        self.scanned_files = []
        
        # 初始化PDF OCR功能
        self.enable_pdf_ocr = enable_pdf_ocr and PDF_OCR_AVAILABLE
        if self.enable_pdf_ocr:
            try:
                self.pdf_processor = PDFProcessor(use_gpu=use_gpu)
                print("PDF OCR模块初始化成功")
            except Exception as e:
                print(f"PDF OCR模块初始化失败: {e}")
                self.enable_pdf_ocr = False
        
        # 初始化PPT OCR功能
        self.enable_ppt_ocr = enable_ppt_ocr and PPT_OCR_AVAILABLE
        if self.enable_ppt_ocr:
            try:
                self.ppt_processor = PPTProcessor()
                print("PPT OCR模块初始化成功")
            except Exception as e:
                print(f"PPT OCR模块初始化失败: {e}")
                self.enable_ppt_ocr = False
        
        # 初始化向量存储
        if self.enable_pdf_ocr or self.enable_ppt_ocr:
            try:
                self.vector_store = VectorStore(use_milvus=use_milvus)
                print("向量存储模块初始化成功")
            except Exception as e:
                print(f"向量存储_module初始化失败: {e}")
                self.vector_store = None
        else:
            self.vector_store = None

        self.parse_mode = "快速"

    def set_parse_mode(self, mode: str):
        if mode in ("快速", "精细"):
            self.parse_mode = mode
            print(f"FileScanner解析模式已设置为: {self.parse_mode}")
            # 将模式传递给底层处理器（若支持）
            try:
                if hasattr(self, 'pdf_processor') and hasattr(self.pdf_processor, 'set_mode'):
                    self.pdf_processor.set_mode(self.parse_mode)
            except Exception:
                pass
            try:
                if hasattr(self, 'ppt_processor') and hasattr(self.ppt_processor, 'set_mode'):
                    self.ppt_processor.set_mode(self.parse_mode)
            except Exception:
                pass

    def scan_files(self, path=None, process_documents=None):
        """
        扫描指定路径下的所有文件
        
        Args:
            path: 扫描路径
            process_documents: 是否处理文档文件（OCR和向量化），None时使用配置文件设置
        """
        if path is None:
            path = NETWORK_PATH
        
        # 使用配置文件设置，除非明确指定
        if process_documents is None:
            process_documents = OCR_CONFIG['auto_ocr_on_scan']
            
        print(f"开始扫描路径: {path}")
        print(f"自动OCR识别: {'启用' if process_documents else '禁用'}")
        
        try:
            # 检查路径是否存在
            if not os.path.exists(path):
                raise FileNotFoundError(f"网络路径不存在: {path}")
            
            file_count = 0
            pdf_count = 0
            ppt_count = 0
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    if self._is_supported_file(file):
                        file_path = os.path.join(root, file)
                        try:
                            file_info = self._get_file_info(file_path)
                            if self._is_current_year_file(file_info):
                                # 只有在启用自动OCR时才处理文档
                                if (process_documents and self.enable_pdf_ocr and 
                                    file_info['extension'] == '.pdf'):
                                    pdf_count += 1
                                    print(f"发现PDF文件: {file}")
                                    file_info = self._process_pdf_file(file_info)
                                
                                # 只有在启用自动OCR时才处理PPT
                                elif (process_documents and self.enable_ppt_ocr and 
                                      file_info['extension'] in ['.ppt', '.pptx']):
                                    ppt_count += 1
                                    print(f"发现PPT文件: {file}")
                                    file_info = self._process_ppt_file(file_info)
                                
                                self.scanned_files.append(file_info)
                                file_count += 1
                                print(f"已扫描文件: {file_count}", end='\r')
                        except Exception as e:
                            print(f"处理文件 {file_path} 时出错: {e}")
                            continue
            
            print(f"\n扫描完成，共找到 {len(self.scanned_files)} 个今年内的文件")
            if process_documents and self.enable_pdf_ocr and pdf_count > 0:
                print(f"其中包含 {pdf_count} 个PDF文件已进行OCR处理和向量化")
            if process_documents and self.enable_ppt_ocr and ppt_count > 0:
                print(f"其中包含 {ppt_count} 个PPT文件已进行文本提取和向量化")
            return self.scanned_files
            
        except Exception as e:
            print(f"扫描路径时出错: {e}")
            return []

    def parse_selected_files(self, file_indices):
        """
        手动解析选中的文件（OCR识别和向量化）
        
        Args:
            file_indices: 要解析的文件索引列表
            
        Returns:
            解析结果字典
        """
        if not self.enable_pdf_ocr and not self.enable_ppt_ocr:
            return {'status': 'error', 'message': 'OCR模块未启用'}
        
        results = {
            'total': len(file_indices),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for idx in file_indices:
            print(f"处理文件索引: {idx}")
            print(f"scanned_files长度: {len(self.scanned_files)}")
            
            if 0 <= idx < len(self.scanned_files):
                file_info = self.scanned_files[idx]
                file_name = file_info['file_name']
                
                print(f"检查文件: {file_name}")
                print(f"  文件索引: {idx}")
                print(f"  文件路径: {file_info.get('file_path', '未知')}")
                print(f"  符合状态: {file_info.get('compliance_status', '未设置')}")
                print(f"  解析状态: {file_info.get('parsing_status', '未设置')}")
                print(f"  文件类型: {file_info.get('extension', '未知')}")
                print(f"  文件大小: {file_info.get('file_size_mb', '未知')} MB")
            else:
                print(f"错误: 文件索引 {idx} 超出范围 (0-{len(self.scanned_files)-1})")
                results['failed'] += 1
                results['details'].append({
                    'file_name': f'索引{idx}',
                    'status': 'failed',
                    'message': f'文件索引超出范围: {idx}'
                })
                continue
            
            # 暂时跳过符合状态检查，直接进行OCR解析
            print(f"  跳过符合状态检查，直接进行OCR解析")
            # if file_info.get('compliance_status') != '符合':
            #     print(f"  跳过原因: 符合状态不是'符合'")
            #     results['details'].append({
            #         'file_name': file_name,
            #         'status': 'skipped',
            #         'message': f'文件状态为"{file_info.get("compliance_status", "未设置")}"，不符合解析条件'
            #     })
            #     continue
            
            # 暂时跳过"已经解析过"的检查
            print(f"  跳过已解析状态检查，直接进行OCR解析")
            # if file_info.get('parsing_status') == '已解析':
            #     print(f"  跳过原因: 已经解析过")
            #     results['details'].append({
            #         'file_name': file_name,
            #         'status': 'skipped',
            #         'message': '文件已经解析过'
            #     })
            #     continue
            
            print(f"开始解析文件: {file_name}")
            
            # 更新解析状态为"解析中"
            file_info['parsing_status'] = '解析中'
            
            try:
                # 根据文件类型进行相应处理
                print(f"  文件类型检查: {file_info['extension']}")
                print(f"  文件类型比较: '{file_info['extension']}' == '.pdf' -> {file_info['extension'] == '.pdf'}")
                
                if file_info['extension'] == '.pdf':
                    print(f"  调用PDF处理器...")
                    updated_info = self._process_pdf_file(file_info)
                    print(f"  PDF处理器返回: {updated_info.get('processing_status', '未知状态')}")
                elif file_info['extension'] in ['.ppt', '.pptx']:
                    print(f"  调用PPT处理器...")
                    updated_info = self._process_ppt_file(file_info)
                    print(f"  PPT处理器返回: {updated_info.get('processing_status', '未知状态')}")
                else:
                    print(f"  不支持的文件类型: {file_info['extension']}")
                    updated_info = file_info
                    updated_info['parsing_status'] = '解析失败'
                    updated_info['error_message'] = '不支持的文件类型'
                
                # 更新文件信息
                self.scanned_files[idx] = updated_info
                
                if updated_info.get('processing_status') == 'success':
                    updated_info['parsing_status'] = '已解析'
                    results['success'] += 1
                    results['details'].append({
                        'file_name': file_name,
                        'status': 'success',
                        'message': '解析成功'
                    })
                else:
                    updated_info['parsing_status'] = '解析失败'
                    results['failed'] += 1
                    results['details'].append({
                        'file_name': file_name,
                        'status': 'failed',
                        'message': updated_info.get('error_message', '解析失败')
                    })
                    
            except Exception as e:
                file_info['parsing_status'] = '解析失败'
                file_info['error_message'] = str(e)
                results['failed'] += 1
                results['details'].append({
                    'file_name': file_name,
                    'status': 'failed',
                    'message': str(e)
                })
        
        # 确保返回结果包含所有必要字段
        if not results.get('details'):
            results['details'] = []
        
        print(f"解析完成: 总计 {results['total']} 个文件，成功 {results['success']} 个，失败 {results['failed']} 个")
        return results

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
            print(f"PDF文件路径: {pdf_path}")
            print(f"PDF文件大小: {file_info.get('file_size_mb', '未知')} MB")
            
            # 检查文件是否存在
            if not os.path.exists(pdf_path):
                print(f"错误: PDF文件不存在: {pdf_path}")
                file_info['processing_status'] = 'failed'
                file_info['error_message'] = f'文件不存在: {pdf_path}'
                return file_info
            
            # 使用PDF处理器进行OCR和内容提取
            print(f"调用PDF处理器...")
            result = self.pdf_processor.process_pdf(pdf_path, file_name)
            
            print(f"PDF处理器返回结果类型: {type(result)}")
            print(f"PDF处理器返回结果: {result}")
            print(f"结果状态: {result.get('status', '未知')}")
            
            # 检查结果结构
            if not isinstance(result, dict):
                print(f"错误: PDF处理器返回结果不是字典类型: {type(result)}")
                file_info['processing_status'] = 'failed'
                file_info['error_message'] = f'PDF处理器返回结果类型错误: {type(result)}'
                return file_info
            
            if result.get('status') == 'success':
                # 提取文本内容
                texts = result.get('texts', [])
                print(f"提取到的文本内容数量: {len(texts)}")
                print(f"文本内容类型: {type(texts)}")
                
                all_text_content = []
                
                for i, text_item in enumerate(texts):
                    print(f"  文本项 {i}: 类型={type(text_item)}, 内容={str(text_item)[:100]}...")
                    if isinstance(text_item, dict) and 'text' in text_item:
                        all_text_content.append(text_item['text'])
                        print(f"    提取文本: {text_item['text'][:100]}...")
                    elif isinstance(text_item, str):
                        all_text_content.append(text_item)
                        print(f"    提取文本: {text_item[:100]}...")
                    else:
                        print(f"    跳过未知类型: {type(text_item)}")
                
                # 合并所有文本内容
                full_text = '\n'.join(all_text_content)
                print(f"合并后文本长度: {len(full_text)} 字符")
                print(f"文本预览: {full_text[:200]}...")
                
                # 生成向量并存储
                print(f"开始向量化处理...")
                print(f"向量存储可用: {self.vector_store is not None}")
                print(f"文本内容非空: {bool(full_text.strip())}")
                
                if self.vector_store and full_text.strip():
                    try:
                        # 创建向量集合（使用文件名作为集合名）
                        collection_name = f"pdf_{file_name.replace('.', '_')}"
                        print(f"创建向量集合: {collection_name}")
                        self.vector_store.create_collection(collection_name, f"PDF文档: {file_name}")
                        
                        # 生成向量
                        print(f"生成向量...")
                        # 将文本分割成段落进行向量化
                        text_chunks = [chunk.strip() for chunk in full_text.split('\n') if chunk.strip()]
                        if not text_chunks:
                            text_chunks = [full_text[:1000]]  # 如果分割后为空，使用前1000字符
                        vectors = self.vector_store.generate_vectors(text_chunks)
                        print(f"向量生成结果: {len(vectors) if vectors else 0} 个向量")
                        
                        if vectors:
                            # 更新文件信息
                            file_info['processing_status'] = 'success'
                            file_info['text_content'] = full_text
                            file_info['vector_collection'] = collection_name
                            file_info['total_pages'] = result.get('total_pages', 0)
                            file_info['summary'] = result.get('summary', '')
                            file_info['keywords'] = result.get('keywords', [])
                            file_info['hybrid_summary'] = result.get('hybrid_summary', '')
                            file_info['markdown_content'] = result.get('markdown_content', '')
                            file_info['part_summaries'] = result.get('part_summaries', [])
                            print(f"✓ PDF文件处理成功: {file_name}, 共{result.get('total_pages', 0)}页")
                        else:
                            file_info['processing_status'] = 'vector_failed'
                            file_info['error_message'] = '向量生成失败'
                            print(f"✗ PDF文件向量化失败: {file_name}")
                    except Exception as e:
                        print(f"✗ PDF文件向量化出错: {file_name}, 错误: {e}")
                        print(f"错误类型: {type(e)}")
                        import traceback
                        traceback.print_exc()
                        file_info['processing_status'] = 'vector_failed'
                        file_info['error_message'] = f'向量化错误: {str(e)}'
                else:
                    if not full_text.strip():
                        file_info['processing_status'] = 'no_text'
                        file_info['error_message'] = '无文本内容'
                        print(f"✗ PDF文件无文本内容: {file_name}")
                    else:
                        file_info['processing_status'] = 'success'
                        file_info['text_content'] = full_text
                        file_info['total_pages'] = result.get('total_pages', 0)
                        file_info['summary'] = result.get('summary', '')
                        file_info['keywords'] = result.get('keywords', [])
                        file_info['hybrid_summary'] = result.get('hybrid_summary', '')
                        file_info['markdown_content'] = result.get('markdown_content', '')
                        file_info['part_summaries'] = result.get('part_summaries', [])
                        print(f"✓ PDF文件处理成功（无向量化）: {file_name}")

                # 将OCR结果保存为独立JSON，便于文件详情查看
                try:
                    from pathlib import Path as _Path
                    import json as _json
                    ocr_dir = _Path('data') / 'ocr'
                    ocr_dir.mkdir(parents=True, exist_ok=True)
                    ocr_path = ocr_dir / f"{_Path(file_name).stem}.json"
                    preview = full_text[:1000] if isinstance(full_text, str) else ''
                    ocr_payload = {
                        'file_name': file_name,
                        'file_path': file_info.get('file_path'),
                        'extension': file_info.get('extension'),
                        'total_pages': file_info.get('total_pages'),
                        'summary': file_info.get('summary', ''),
                        'keywords': file_info.get('keywords', []),
                        'hybrid_summary': file_info.get('hybrid_summary', ''),
                        'markdown_content': file_info.get('markdown_content', ''),
                        'part_summaries': file_info.get('part_summaries', []),
                        'text_preview': preview,
                        'vector_collection': file_info.get('vector_collection')
                    }
                    with open(ocr_path, 'w', encoding='utf-8') as f:
                        _json.dump(ocr_payload, f, ensure_ascii=False, indent=2)
                    file_info['ocr_data_path'] = str(ocr_path)
                except Exception as _e:
                    print(f"写入PDF OCR详情JSON失败: {file_name}, 错误: {_e}")

                return file_info

        except Exception as e:
            print(f"✗ 处理PDF文件出错: {file_info.get('file_name', '')}, 错误: {e}")
            print(f"错误类型: {type(e)}")
            import traceback
            traceback.print_exc()
            file_info['processing_status'] = 'failed'
            file_info['error_message'] = str(e)
            return file_info

    def _process_ppt_file(self, file_info):
        """
        处理PPT文件：文本提取和向量化存储
        
        Args:
            file_info: 文件信息字典
            
        Returns:
            更新后的文件信息字典
        """
        try:
            ppt_path = file_info['file_path']
            file_name = file_info['file_name']
            
            print(f"开始处理PPT: {file_name}")
            print(f"PPT文件路径: {ppt_path}")
            print(f"PPT文件大小: {file_info.get('file_size_mb', '未知')} MB")
            
            # 检查文件是否存在
            if not os.path.exists(ppt_path):
                print(f"错误: PPT文件不存在: {ppt_path}")
                file_info['processing_status'] = 'failed'
                file_info['error_message'] = f'文件不存在: {ppt_path}'
                return file_info
            
            # 使用PPT处理器进行文本提取
            print(f"调用PPT处理器...")
            result = self.ppt_processor.process_ppt(ppt_path, file_name)
            
            print(f"PPT处理器返回结果类型: {type(result)}")
            print(f"PPT处理器返回结果: {result}")
            print(f"结果状态: {result.get('status', '未知')}")
            
            # 检查结果结构
            if not isinstance(result, dict):
                print(f"错误: PPT处理器返回结果不是字典类型: {type(result)}")
                file_info['processing_status'] = 'failed'
                file_info['error_message'] = f'PPT处理器返回结果类型错误: {type(result)}'
                return file_info
            
            if result.get('status') == 'success':
                # 提取文本内容
                slide_texts = result.get('slide_texts', [])
                print(f"提取到的幻灯片文本数量: {len(slide_texts)}")
                print(f"幻灯片文本类型: {type(slide_texts)}")
                print(f"幻灯片文本详情: {slide_texts}")
                
                all_text_content = []
                
                for i, slide_text_list in enumerate(slide_texts):
                    print(f"  幻灯片 {i}: 类型={type(slide_text_list)}, 内容={str(slide_text_list)[:100]}...")
                    if isinstance(slide_text_list, list):
                        for j, text_item in enumerate(slide_text_list):
                            if text_item and text_item.strip():
                                all_text_content.append(text_item)
                                print(f"    列表项 {j}: {text_item[:100]}...")
                            else:
                                print(f"    跳过空列表项 {j}")
                        print(f"    列表内容: {len(slide_text_list)} 项")
                    elif isinstance(slide_text_list, str):
                        if slide_text_list and slide_text_list.strip():
                            all_text_content.append(slide_text_list)
                            print(f"    文本内容: {slide_text_list[:100]}...")
                        else:
                            print(f"    跳过空文本")
                    else:
                        print(f"    跳过未知类型: {type(slide_text_list)}")
                
                # 合并所有文本内容
                full_text = '\n'.join(all_text_content)
                print(f"合并后文本长度: {len(full_text)} 字符")
                print(f"文本预览: {full_text[:200]}...")
                
                # 如果没有提取到文本，尝试直接提取
                if not full_text.strip():
                    print(f"  警告: 没有提取到文本内容，尝试直接提取...")
                    try:
                        # 这里可以添加直接提取的逻辑
                        print(f"  需要实现直接提取逻辑")
                    except Exception as extract_e:
                        print(f"  直接提取失败: {extract_e}")
                
                # 生成向量并存储
                print(f"开始向量化处理...")
                print(f"向量存储可用: {self.vector_store is not None}")
                print(f"文本内容非空: {bool(full_text.strip())}")
                
                if self.vector_store and full_text.strip():
                    try:
                        # 创建向量集合（使用文件名作为集合名）
                        collection_name = f"ppt_{file_name.replace('.', '_')}"
                        print(f"创建向量集合: {collection_name}")
                        self.vector_store.create_collection(collection_name, f"PPT文档: {file_name}")
                        
                        # 生成向量
                        print(f"生成向量...")
                        # 将文本分割成段落进行向量化
                        text_chunks = [chunk.strip() for chunk in full_text.split('\n') if chunk.strip()]
                        if not text_chunks:
                            text_chunks = [full_text[:1000]]  # 如果分割后为空，使用前1000字符
                        vectors = self.vector_store.generate_vectors(text_chunks)
                        print(f"向量生成结果: {len(vectors) if vectors else 0} 个向量")
                        
                        if vectors:
                            # 更新文件信息
                            file_info['processing_status'] = 'success'
                            file_info['text_content'] = full_text
                            file_info['vector_collection'] = collection_name
                            file_info['total_slides'] = result.get('total_slides', 0)
                            file_info['summary'] = result.get('summary', '')
                            file_info['keywords'] = result.get('keywords', [])
                            file_info['file_format'] = result.get('file_format', 'unknown')
                            print(f"✓ PPT文件处理成功: {file_name}, 共{result.get('total_slides', 0)}页")
                        else:
                            file_info['processing_status'] = 'vector_failed'
                            file_info['error_message'] = '向量生成失败'
                            print(f"✗ PPT文件向量化失败: {file_name}")
                    except Exception as e:
                        print(f"✗ PPT文件向量化出错: {file_name}, 错误: {e}")
                        print(f"错误类型: {type(e)}")
                        import traceback
                        traceback.print_exc()
                        file_info['processing_status'] = 'vector_failed'
                        file_info['error_message'] = f'向量化错误: {str(e)}'
                else:
                    if not full_text.strip():
                        file_info['processing_status'] = 'no_text'
                        file_info['error_message'] = '无文本内容'
                        print(f"✗ PPT文件无文本内容: {file_name}")
                    else:
                        file_info['processing_status'] = 'success'
                        file_info['text_content'] = full_text
                        file_info['total_slides'] = result.get('total_slides', 0)
                        file_info['summary'] = result.get('summary', '')
                        file_info['keywords'] = result.get('keywords', [])
                        file_info['file_format'] = result.get('file_format', 'unknown')
                        print(f"✓ PPT文件处理成功（无向量化）: {file_name}")
            else:
                file_info['processing_status'] = 'failed'
                file_info['error_message'] = result.get('message', '未知错误')
                print(f"✗ PPT文件处理失败: {file_name}, 错误: {result.get('message', '未知错误')}")
                return file_info
                
        except Exception as e:
            print(f"✗ PPT文件处理出错: {file_info.get('file_name', 'unknown')}, 错误: {e}")
            print(f"错误类型: {type(e)}")
            import traceback
            traceback.print_exc()
            file_info['processing_status'] = 'failed'
            file_info['error_message'] = str(e)
            return file_info
        
        # 将OCR结果保存为独立JSON，便于文件详情查看（PPT）
        try:
            from pathlib import Path as _Path
            import json as _json
            ocr_dir = _Path('data') / 'ocr'
            ocr_dir.mkdir(parents=True, exist_ok=True)
            ocr_path = ocr_dir / f"{_Path(file_name).stem}.json"
            
            # 确保full_text已定义
            if 'full_text' not in locals():
                full_text = ''
                
            preview = full_text[:1000] if isinstance(full_text, str) else ''
            ocr_payload = {
                'file_name': file_name,
                'file_path': file_info.get('file_path'),
                'extension': file_info.get('extension'),
                'total_slides': file_info.get('total_slides'),
                'summary': file_info.get('summary', ''),
                'keywords': file_info.get('keywords', []),
                'text_preview': preview,
                'vector_collection': file_info.get('vector_collection')
            }
            with open(ocr_path, 'w', encoding='utf-8') as f:
                _json.dump(ocr_payload, f, ensure_ascii=False, indent=2)
            file_info['ocr_data_path'] = str(ocr_path)
        except Exception as _e:
            print(f"写入PPT OCR详情JSON失败: {file_name}, 错误: {_e}")
        
        return file_info

    def _is_supported_file(self, filename):
        """
        检查文件是否为支持的类型
        
        Args:
            filename: 文件名
            
        Returns:
            是否为支持的文件类型
        """
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in SUPPORTED_EXTENSIONS

    def _get_file_info(self, file_path):
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            stat = os.stat(file_path)
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # 获取文件时间
            creation_time = datetime.fromtimestamp(stat.st_ctime)
            modification_time = datetime.fromtimestamp(stat.st_mtime)
            access_time = datetime.fromtimestamp(stat.st_atime)
            
            # 计算文件大小（MB）
            file_size_mb = round(stat.st_size / (1024 * 1024), 2)
            
            return {
                'file_name': file_name,
                'file_path': file_path,
                'file_size_mb': file_size_mb,
                'extension': file_ext,
                'creation_date': creation_time,
                'modification_date': modification_time,
                'access_date': access_time,
                'status': 'unchanged',  # 默认状态
                'compliance_status': '待定',  # 符合状态：符合、不符合、待定
                'compliance_reason': '',  # 不符合原因
                'parsing_status': '未解析',  # 解析状态：未解析、解析中、已解析、解析失败
                'ocr_processed': False,  # 是否已进行OCR处理
                'processing_status': '',  # 处理状态
                'text_content': '',  # 提取的文本内容
                'total_pages': 0,  # 总页数
                'summary': '',  # 摘要
                'keywords': [],  # 关键词
                'ocr_data_path': '',  # OCR数据文件路径
                'vector_collection': '',  # 向量集合名称
                'error_message': ''  # 错误信息
            }
        except Exception as e:
            print(f"获取文件信息失败: {file_path}, 错误: {e}")
            return {
                'file_name': os.path.basename(file_path),
                'file_path': file_path,
                'file_size_mb': 0,
                'extension': os.path.splitext(file_path)[1].lower(),
                'creation_date': datetime.now(),
                'modification_date': datetime.now(),
                'access_date': datetime.now(),
                'status': 'error',
                'compliance_status': '待定',
                'compliance_reason': '',
                'parsing_status': '未解析',
                'ocr_processed': False,
                'processing_status': '',
                'text_content': '',
                'total_pages': 0,
                'summary': '',
                'keywords': [],
                'ocr_data_path': '',
                'vector_collection': '',
                'error_message': str(e)
            }

    def _is_current_year_file(self, file_info):
        """
        检查文件是否为今年的文件
        
        Args:
            file_info: 文件信息字典
            
        Returns:
            是否为今年的文件
        """
        current_year = date.today().year
        
        # 检查创建时间、修改时间和访问时间
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
            # 确保Excel文件保存在data目录中
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            excel_path = data_dir / filename
            
            df = pd.DataFrame(self.scanned_files)
            
            # 处理日期列，转换为字符串格式
            date_columns = ['creation_date', 'modification_date', 'access_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            df.to_excel(excel_path, index=False, engine='openpyxl')
            print(f"文件信息已导出到: {excel_path}")
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
        
        # PDF和PPT处理统计
        document_stats = {}
        if self.enable_pdf_ocr or self.enable_ppt_ocr:
            pdf_files = [f for f in self.scanned_files if f['extension'] == '.pdf']
            ppt_files = [f for f in self.scanned_files if f['extension'] in ['.ppt', '.pptx']]
            
            document_stats = {
                'total_pdfs': len(pdf_files),
                'total_ppts': len(ppt_files),
                'pdf_processed': len([f for f in pdf_files if f.get('processing_status') == 'success']),
                'ppt_processed': len([f for f in ppt_files if f.get('processing_status') == 'success']),
                'pdf_failed': len([f for f in pdf_files if f.get('processing_status') == 'failed']),
                'ppt_failed': len([f for f in ppt_files if f.get('processing_status') == 'failed']),
                'vector_failed': len([f for f in self.scanned_files if f.get('processing_status') == 'vector_failed']),
                'no_text': len([f for f in self.scanned_files if f.get('processing_status') == 'no_text'])
            }
        
        return {
            'total_files': total_files,
            'total_size_mb': round(total_size, 2),
            'extension_stats': ext_stats,
            'month_stats': month_stats,
            'document_processing_stats': document_stats
        }

    def search_document_content(self, query, top_k=5):
        """
        搜索文档内容（基于向量相似度）
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if not self.vector_store:
            print("向量搜索功能未启用")
            return []
        
        try:
            # 搜索所有文档的向量集合
            results = []
            document_files = [f for f in self.scanned_files 
                            if f['extension'] in ['.pdf', '.ppt', '.pptx'] 
                            and f.get('vector_collection')]
            
            for doc_file in document_files:
                collection_name = doc_file['vector_collection']
                try:
                    # 在向量集合中搜索
                    search_results = self.vector_store.search_similar(query, collection_name, top_k)
                    
                    for result in search_results:
                        result['source_file'] = doc_file['file_name']
                        result['file_path'] = doc_file['file_path']
                        result['file_type'] = doc_file['extension']
                        results.append(result)
                        
                except Exception as e:
                    print(f"搜索集合 {collection_name} 失败: {e}")
                    continue
            
            # 按相似度排序
            results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            print(f"搜索文档内容失败: {e}")
            return []


# 测试代码
if __name__ == "__main__":
    print("测试文件扫描器...")
    
    # 初始化扫描器，启用PDF和PPT OCR功能
    scanner = FileScanner(enable_pdf_ocr=True, enable_ppt_ocr=True, use_gpu=False, use_milvus=False)
    
    # 如果网络路径不可用，使用本地测试路径
    test_path = "test_documents" if not os.path.exists(NETWORK_PATH) else NETWORK_PATH
    
    if not os.path.exists(test_path):
        print(f"测试路径不存在: {test_path}")
        exit(1)
    
    # 扫描文件，启用文档处理
    files = scanner.scan_files(test_path, process_documents=True)
    
    if files:
        print(f"\n扫描完成，共找到 {len(files)} 个文件")
        
        # 显示统计信息
        stats = scanner.get_statistics()
        print("\n扫描统计:")
        print(f"总文件数: {stats['total_files']}")
        print(f"总大小: {stats['total_size_mb']} MB")
        
        # 显示扩展名统计
        print("\n文件类型统计:")
        for ext, count in stats['extension_stats'].items():
            print(f"  {ext}: {count} 个")
        
        # 显示文档处理统计
        if 'document_processing_stats' in stats:
            doc_stats = stats['document_processing_stats']
            print("\n文档处理统计:")
            print(f"  PDF文件: {doc_stats['total_pdfs']} 个")
            print(f"  PPT文件: {doc_stats['total_ppts']} 个")
            print(f"  PDF处理成功: {doc_stats['pdf_processed']} 个")
            print(f"  PPT处理成功: {doc_stats['ppt_processed']} 个")
        
        # 导出到Excel
        if scanner.export_to_excel():
            print("\n扫描结果已导出到Excel文件")
    else:
        print("未找到符合条件的文件")
