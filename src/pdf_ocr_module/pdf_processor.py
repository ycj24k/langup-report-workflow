"""
PDF处理器 - 集成PDF解析、图像处理和内容提取功能
"""

import os
import json
import time
import pickle
import fitz
from PIL import Image
from loguru import logger
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from .config import OUTPUT_DIR, PICKLES_DIR, IMAGE_CONFIG, PROMPTS, REMOTE_OCR_CONFIG
from .ocr_engine import OCREngine
from .llm_processor import LLMProcessor


class PDFProcessor:
    """PDF处理器，负责PDF解析、图像处理和内容提取"""
    
    def __init__(self, use_gpu: bool = True, ocr_engine=None):
        """
        初始化PDF处理器
        
        Args:
            use_gpu: 是否使用GPU
            ocr_engine: 外部OCR引擎实例（可选）
        """
        if ocr_engine:
            self.ocr_engine = ocr_engine
        else:
            self.ocr_engine = OCREngine(use_gpu=use_gpu)
        
        self.llm_processor = LLMProcessor()
        self.mode = "快速"
        # 基础分辨率（可根据模式覆盖）
        self.target_resolution = IMAGE_CONFIG["target_resolution"]
        self.high_resolution = IMAGE_CONFIG["high_resolution"]
        
        # 远程OCR客户端
        self.remote_client = None
        if REMOTE_OCR_CONFIG.get("enabled", False):
            try:
                from .remote_ocr_client import RemoteOCRClient
                self.remote_client = RemoteOCRClient(REMOTE_OCR_CONFIG["server_url"])
                if self.remote_client.check_server_health():
                    logger.info("远程GPU OCR服务连接成功")
                else:
                    logger.warning("远程GPU OCR服务连接失败，将使用本地OCR")
                    self.remote_client = None
            except Exception as e:
                logger.warning(f"远程OCR客户端初始化失败: {e}")
                self.remote_client = None

    def set_mode(self, mode: str):
        """设置解析模式：快速/精细"""
        if mode not in ("快速", "精细"):
            return
        self.mode = mode
        # 调整页面渲染分辨率
        if mode == "快速":
            self.target_resolution = max(960, int(IMAGE_CONFIG["target_resolution"] * 0.75))
            self.high_resolution = max(1400, int(IMAGE_CONFIG["high_resolution"] * 0.8))
        else:  # 精细
            self.target_resolution = max(IMAGE_CONFIG["target_resolution"], 1536)
            self.high_resolution = max(IMAGE_CONFIG["high_resolution"], 2200)
        # 传递给OCR引擎
        try:
            if hasattr(self, 'ocr_engine') and hasattr(self.ocr_engine, 'set_mode'):
                self.ocr_engine.set_mode(mode)
        except Exception:
            pass
        
    def process_pdf(self, pdf_path: str, output_name: str = None) -> Dict:
        """
        处理PDF文件
        
        Args:
            pdf_path: PDF文件路径
            output_name: 输出名称，如果为None则使用文件名
            
        Returns:
            处理结果字典
        """
        if not Path(pdf_path).exists():
            return {'status': 'error', 'message': f'PDF文件不存在: {pdf_path}'}
        
        if output_name is None:
            output_name = Path(pdf_path).stem
        
        # 优先使用远程OCR
        if self.remote_client:
            try:
                logger.info(f"使用远程GPU OCR处理PDF: {output_name}")
                result = self.remote_client.process_pdf(pdf_path, f"{output_name}.pdf")
                if result.get('status') == 'success':
                    return result
                else:
                    logger.warning(f"远程OCR处理失败，回退到本地OCR: {result.get('message', '未知错误')}")
                    if not REMOTE_OCR_CONFIG.get("fallback_to_local", True):
                        return result
            except Exception as e:
                logger.warning(f"远程OCR处理异常，回退到本地OCR: {e}")
                if not REMOTE_OCR_CONFIG.get("fallback_to_local", True):
                    return {'status': 'error', 'message': str(e)}
        
        # 本地OCR处理
        try:
            # 创建输出目录
            output_path = OUTPUT_DIR / output_name
            output_path.mkdir(exist_ok=True)
            
            # 处理PDF
            result = self._process_pdf_pages(pdf_path, output_path, output_name)
            
            # 清理临时文件
            self._cleanup_temp_files(output_path)
            
            return result
            
        except Exception as e:
            logger.error(f"PDF处理失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _process_pdf_pages(self, pdf_path: str, output_path: Path, output_name: str) -> Dict:
        """处理PDF的每一页"""
        try:
            with fitz.open(pdf_path) as pdf:
                total_pages = pdf.page_count
                all_texts = []
                all_figures = []
                all_tables = []
                
                logger.info(f"开始处理PDF: {pdf_path}, 共{total_pages}页")
                
                for page_num in range(total_pages):
                    page = pdf[page_num]
                    logger.info(f"处理第{page_num + 1}页")
                    
                    # 处理单页
                    page_result = self._process_single_page(page, page_num, output_path)
                    
                    # 无论状态如何，都尝试提取文本
                    if page_result['status'] == 'success':
                        all_texts.extend(page_result['texts'])
                        all_figures.extend(page_result['figures'])
                        all_tables.extend(page_result['tables'])
                        logger.info(f"第{page_num + 1}页处理成功，提取到{len(page_result['texts'])}个文本区域")
                    else:
                        logger.warning(f"第{page_num + 1}页处理失败，尝试强制提取文本")
                        # 强制提取文本，即使处理失败
                        try:
                            # 生成标准分辨率图像
                            standard_image_path = self._generate_page_image(
                                page, page_num, output_path, IMAGE_CONFIG["target_resolution"]
                            )
                            # 直接OCR整个页面
                            direct_text = self.ocr_engine.extract_text_direct(standard_image_path)
                            if direct_text.strip():
                                all_texts.append({
                                    'page': page_num + 1,
                                    'text': direct_text,
                                    'bbox': None,
                                    'category': 'text',
                                    'confidence': 0.6
                                })
                                logger.info(f"第{page_num + 1}页强制提取到{len(direct_text)}字符文本")
                            else:
                                logger.warning(f"第{page_num + 1}页强制提取失败，无文本内容")
                        except Exception as e:
                            logger.error(f"第{page_num + 1}页强制提取出错: {e}")
                    
                    # 进度更新
                    progress = (page_num + 1) / total_pages * 100
                    logger.info(f"处理进度: {progress:.1f}%")
                
                # 生成摘要和关键词
                summary_result = self._generate_summary(all_texts)
                
                # 保存结果
                result = {
                    'status': 'success',
                    'output_path': str(output_path),
                    'total_pages': total_pages,
                    'texts': all_texts,
                    'figures': all_figures,
                    'tables': all_tables,
                    'summary': summary_result.get('summary', ''),
                    'keywords': summary_result.get('keywords', []),
                    'hybrid_summary': summary_result.get('hybrid_summary', ''),
                    'markdown_content': summary_result.get('markdown_content', ''),
                    'part_summaries': summary_result.get('part_summaries', [])
                }
                
                # 保存到pickle文件
                self._save_to_pickle(result, output_name)
                
                return result
                
        except Exception as e:
            logger.error(f"PDF页面处理失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _process_single_page(self, page, page_num: int, output_path: Path) -> Dict:
        """处理单页PDF"""
        try:
            # 获取页面信息
            page_type = 'H' if page.rect.width > page.rect.height else 'S'
            
            # 生成不同分辨率的图像
            standard_image_path = self._generate_page_image(
                page, page_num, output_path, self.target_resolution
            )
            high_image_path = ""
            if getattr(self, 'mode', '快速') == '精细':
                high_image_path = self._generate_page_image(
                    page, page_num, output_path, self.high_resolution
                )
            
            # OCR处理
            ocr_result = self.ocr_engine.process_page(standard_image_path)
            
            # 处理文本区域
            texts = []
            for text_region in ocr_result['text_regions']:
                texts.append({
                    'page': page_num + 1,
                    'text': text_region['text'],
                    'bbox': text_region['bbox'],
                    'category': text_region['category'],
                    'confidence': text_region['confidence']
                })
            
            # 处理图片区域
            figures = []
            for fig_region in ocr_result['figure_regions']:
                figure_path = self._extract_figure(
                    high_image_path or standard_image_path, fig_region['bbox'], output_path, f"fig_{page_num + 1}"
                )
                if figure_path:
                    figures.append({
                        'page': page_num + 1,
                        'path': str(figure_path),
                        'bbox': fig_region['bbox'],
                        'category': 'figure'
                    })
            
            # 处理表格区域
            tables = []
            for table_region in ocr_result['table_regions']:
                table_path = self._extract_table(
                    high_image_path or standard_image_path, table_region['bbox'], output_path, f"table_{page_num + 1}"
                )
                if table_path:
                    tables.append({
                        'page': page_num + 1,
                        'path': str(table_path),
                        'bbox': table_region['bbox'],
                        'category': 'table'
                    })
            
            return {
                'status': 'success',
                'texts': texts,
                'figures': figures,
                'tables': tables
            }
            
        except Exception as e:
            logger.error(f"单页处理失败: {e}")
            return {
                'status': 'error',
                'texts': [],
                'figures': [],
                'tables': []
            }
    
    def _generate_page_image(self, page, page_num: int, output_path: Path, target_size: int) -> str:
        """生成页面图像"""
        try:
            # 计算缩放比例
            if page.rect.width > page.rect.height:
                scale = target_size / page.rect.width
            else:
                scale = target_size / page.rect.height
            
            # 生成图像
            matrix = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            
            # 保存图像
            image_path = output_path / f"page_{page_num + 1}_{target_size}.jpg"
            pix.save(str(image_path))
            
            return str(image_path)
            
        except Exception as e:
            logger.error(f"生成页面图像失败: {e}")
            return ""
    
    def _extract_figure(self, image_path: str, bbox: List[int], output_path: Path, name: str) -> Optional[Path]:
        """提取图片区域"""
        try:
            image = Image.open(image_path)
            cropped = image.crop(bbox)
            
            figure_path = output_path / f"{name}.png"
            cropped.save(figure_path)
            
            return figure_path
            
        except Exception as e:
            logger.error(f"提取图片失败: {e}")
            return None
    
    def _extract_table(self, image_path: str, bbox: List[int], output_path: Path, name: str) -> Optional[Path]:
        """提取表格区域"""
        try:
            image = Image.open(image_path)
            cropped = image.crop(bbox)
            
            table_path = output_path / f"{name}.png"
            cropped.save(table_path)
            
            return table_path
            
        except Exception as e:
            logger.error(f"提取表格失败: {e}")
            return None
    
    def _generate_summary(self, texts: List[Dict]) -> Dict:
        """生成内容摘要"""
        try:
            # 合并所有文本
            all_text = "\n".join([text['text'] for text in texts])
            
            if not all_text.strip():
                return {
                    'summary': '文档内容为空',
                    'keywords': [],
                    'hybrid_summary': '无内容可分析',
                    'markdown_content': '无内容可转换',
                    'part_summaries': []
                }
            
            # 使用LLM生成各种类型的内容
            summary = self.llm_processor.generate_summary(all_text)
            keywords = self.llm_processor.extract_keywords(all_text)
            hybrid_summary = self.llm_processor.generate_hybrid_summary(all_text)
            markdown_content = self.llm_processor.convert_to_markdown(all_text)
            
            # 生成段落摘要
            part_summaries = []
            try:
                # 将文本分段处理
                paragraphs = [p.strip() for p in all_text.split('\n\n') if p.strip()]
                for i, paragraph in enumerate(paragraphs[:5]):  # 只处理前5段
                    if len(paragraph) > 100:  # 只对较长的段落生成摘要
                        part_summary = self.llm_processor.generate_summary(paragraph)
                        part_summaries.append({
                            'paragraph_index': i + 1,
                            'original_length': len(paragraph),
                            'summary': part_summary
                        })
            except Exception as e:
                logger.warning(f"生成段落摘要失败: {e}")
            
            return {
                'summary': summary,
                'keywords': keywords,
                'hybrid_summary': hybrid_summary,
                'markdown_content': markdown_content,
                'part_summaries': part_summaries
            }
            
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            return {
                'summary': '摘要生成失败',
                'keywords': [],
                'hybrid_summary': '分析失败',
                'markdown_content': '转换失败',
                'part_summaries': []
            }
    
    def _save_to_pickle(self, result: Dict, output_name: str):
        """保存结果到pickle文件"""
        try:
            pickle_path = PICKLES_DIR / output_name
            pickle_path.mkdir(exist_ok=True)
            
            # 保存主要结果
            with open(pickle_path / "result.pkl", 'wb') as f:
                pickle.dump(result, f)
            
            # 保存文本向量（如果需要）
            if result['texts']:
                texts = [text['text'] for text in result['texts']]
                # 这里可以添加向量化逻辑
                with open(pickle_path / "texts.pkl", 'wb') as f:
                    pickle.dump(texts, f)
            
            logger.info(f"结果已保存到: {pickle_path}")
            
        except Exception as e:
            logger.error(f"保存pickle文件失败: {e}")
    
    def _cleanup_temp_files(self, output_path: Path):
        """清理临时文件"""
        try:
            # 删除临时图像文件
            for temp_file in output_path.glob("*.jpg"):
                if "temp" in temp_file.name:
                    temp_file.unlink()
            
            logger.info("临时文件清理完成")
            
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
    
    def batch_process(self, pdf_dir: str, output_base_name: str = None) -> List[Dict]:
        """
        批量处理PDF文件
        
        Args:
            pdf_dir: PDF文件目录
            output_base_name: 输出基础名称
            
        Returns:
            处理结果列表
        """
        pdf_dir_path = Path(pdf_dir)
        if not pdf_dir_path.exists():
            return [{'status': 'error', 'message': f'目录不存在: {pdf_dir}'}]
        
        pdf_files = list(pdf_dir_path.glob("*.pdf"))
        if not pdf_files:
            return [{'status': 'error', 'message': '目录中没有PDF文件'}]
        
        results = []
        for i, pdf_file in enumerate(pdf_files):
            logger.info(f"批量处理进度: {i+1}/{len(pdf_files)} - {pdf_file.name}")
            
            if output_base_name:
                output_name = f"{output_base_name}_{i+1}"
            else:
                output_name = f"{pdf_file.stem}_{i+1}"
            
            result = self.process_pdf(str(pdf_file), output_name)
            results.append(result)
        
        return results
