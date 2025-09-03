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

from .config import OUTPUT_DIR, PICKLES_DIR, IMAGE_CONFIG, PROMPTS
from .ocr_engine import OCREngine
from .llm_processor import LLMProcessor


class PDFProcessor:
    """PDF处理器，负责PDF解析、图像处理和内容提取"""
    
    def __init__(self, use_gpu: bool = True):
        """
        初始化PDF处理器
        
        Args:
            use_gpu: 是否使用GPU
        """
        self.ocr_engine = OCREngine(use_gpu=use_gpu)
        self.llm_processor = LLMProcessor()
        
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
                    
                    if page_result['status'] == 'success':
                        all_texts.extend(page_result['texts'])
                        all_figures.extend(page_result['figures'])
                        all_tables.extend(page_result['tables'])
                    
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
                    'summary': summary_result
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
                page, page_num, output_path, IMAGE_CONFIG["target_resolution"]
            )
            high_image_path = self._generate_page_image(
                page, page_num, output_path, IMAGE_CONFIG["high_resolution"]
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
                    high_image_path, fig_region['bbox'], output_path, f"fig_{page_num + 1}"
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
                    high_image_path, table_region['bbox'], output_path, f"table_{page_num + 1}"
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
                    'hybrid_summary': '无内容可分析'
                }
            
            # 使用LLM生成摘要
            summary = self.llm_processor.generate_summary(all_text)
            keywords = self.llm_processor.extract_keywords(all_text)
            hybrid_summary = self.llm_processor.generate_hybrid_summary(all_text)
            
            return {
                'summary': summary,
                'keywords': keywords,
                'hybrid_summary': hybrid_summary
            }
            
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            return {
                'summary': '摘要生成失败',
                'keywords': [],
                'hybrid_summary': '分析失败'
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
