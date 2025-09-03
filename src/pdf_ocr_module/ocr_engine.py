"""
OCR引擎 - 集成PaddleOCR和布局检测功能
"""

import cv2
import numpy as np
from PIL import Image
from loguru import logger
from paddleocr import PaddleOCR
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from .config import OCR_CONFIG, LAYOUT_CONFIG, IMAGE_CONFIG


class OCREngine:
    """OCR引擎，集成文字识别和布局检测"""
    
    def __init__(self, use_gpu: bool = True):
        """
        初始化OCR引擎
        
        Args:
            use_gpu: 是否使用GPU
        """
        self.use_gpu = use_gpu
        self._init_ocr()
        self._init_layout_detector()
        
    def _init_ocr(self):
        """初始化PaddleOCR"""
        try:
            self.ocr = PaddleOCR(
                use_gpu=self.use_gpu,
                det_limit_side_len=OCR_CONFIG["det_limit_side_len"],
                layout=OCR_CONFIG["layout"],
                table=OCR_CONFIG["table"],
                det_db_unclip_ratio=OCR_CONFIG["det_db_unclip_ratio"],
                show_log=OCR_CONFIG["show_log"]
            )
            logger.info("PaddleOCR初始化成功")
        except Exception as e:
            logger.error(f"PaddleOCR初始化失败: {e}")
            raise
    
    def _init_layout_detector(self):
        """初始化布局检测器"""
        try:
            model_path = Path(LAYOUT_CONFIG["model_path"])
            if model_path.exists():
                self.layout_model = YOLO(str(model_path))
                logger.info("布局检测模型加载成功")
            else:
                logger.warning("布局检测模型文件不存在，将使用默认检测")
                self.layout_model = None
        except Exception as e:
            logger.warning(f"布局检测模型加载失败: {e}")
            self.layout_model = None
    
    def detect_layout(self, image_path: str) -> List[Dict]:
        """
        检测图像布局
        
        Args:
            image_path: 图像路径
            
        Returns:
            布局检测结果列表
        """
        if not self.layout_model:
            return self._default_layout_detection(image_path)
        
        try:
            results = self.layout_model.predict(
                image_path,
                conf=LAYOUT_CONFIG["conf_threshold"],
                iou=LAYOUT_CONFIG["iou_threshold"]
            )
            
            layout_results = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].cpu().numpy()
                        cls = int(box.cls[0].cpu().numpy())
                        
                        layout_results.append({
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'confidence': float(conf),
                            'category': self._get_category_name(cls),
                            'category_id': cls
                        })
            
            return layout_results
            
        except Exception as e:
            logger.error(f"布局检测失败: {e}")
            return self._default_layout_detection(image_path)
    
    def _default_layout_detection(self, image_path: str) -> List[Dict]:
        """默认布局检测（基于图像分析）"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # 简单的文本区域检测
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect_ratio = w / h if h > 0 else 0
                
                # 过滤太小的区域和太宽的区域
                if area > 100 and aspect_ratio < 10:
                    text_regions.append({
                        'bbox': [x, y, x + w, y + h],
                        'confidence': 0.8,
                        'category': 'text',
                        'category_id': 0
                    })
            
            return text_regions
            
        except Exception as e:
            logger.error(f"默认布局检测失败: {e}")
            return []
    
    def _get_category_name(self, category_id: int) -> str:
        """获取类别名称"""
        categories = {
            0: 'text',
            1: 'title',
            2: 'figure',
            3: 'table',
            4: 'header',
            5: 'footer'
        }
        return categories.get(category_id, 'unknown')
    
    def extract_text(self, image_path: str, bbox: Optional[List[int]] = None) -> str:
        """
        从图像中提取文字
        
        Args:
            image_path: 图像路径
            bbox: 边界框 [x1, y1, x2, y2]，如果为None则处理整个图像
            
        Returns:
            提取的文字
        """
        try:
            if bbox:
                # 裁剪指定区域
                image = Image.open(image_path)
                cropped = image.crop(bbox)
                temp_path = f"{image_path}_temp.jpg"
                cropped.save(temp_path)
                image_path = temp_path
            
            result = self.ocr.ocr(image_path, cls=True)
            
            if bbox and Path(temp_path).exists():
                Path(temp_path).unlink()  # 删除临时文件
            
            if not result or not result[0]:
                return ""
            
            # 提取文字内容
            texts = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0]  # 文字内容
                    confidence = line[1][1]  # 置信度
                    if confidence > 0.5:  # 过滤低置信度结果
                        texts.append(text)
            
            return "\n".join(texts)
            
        except Exception as e:
            logger.error(f"文字提取失败: {e}")
            return ""
    
    def process_page(self, image_path: str) -> Dict:
        """
        处理单页图像，返回布局和文字信息
        
        Args:
            image_path: 图像路径
            
        Returns:
            处理结果字典
        """
        try:
            # 布局检测
            layout_results = self.detect_layout(image_path)
            
            # 分类处理
            text_regions = []
            figure_regions = []
            table_regions = []
            
            for region in layout_results:
                category = region['category']
                bbox = region['bbox']
                
                if category in ['text', 'title']:
                    text = self.extract_text(image_path, bbox)
                    if text.strip():
                        text_regions.append({
                            'bbox': bbox,
                            'text': text,
                            'category': category,
                            'confidence': region['confidence']
                        })
                elif category == 'figure':
                    figure_regions.append(region)
                elif category == 'table':
                    table_regions.append(region)
            
            return {
                'text_regions': text_regions,
                'figure_regions': figure_regions,
                'table_regions': table_regions,
                'layout_results': layout_results
            }
            
        except Exception as e:
            logger.error(f"页面处理失败: {e}")
            return {
                'text_regions': [],
                'figure_regions': [],
                'table_regions': [],
                'layout_results': []
            }
    
    def clean_similar_images(self, image_dir: str, similarity_threshold: float = None) -> bool:
        """
        清理相似图像
        
        Args:
            image_dir: 图像目录
            similarity_threshold: 相似度阈值
            
        Returns:
            是否清理成功
        """
        if similarity_threshold is None:
            similarity_threshold = IMAGE_CONFIG["similarity_threshold"]
        
        try:
            image_files = list(Path(image_dir).glob("*.jpg")) + list(Path(image_dir).glob("*.png"))
            
            if len(image_files) < 2:
                return True
            
            # 计算图像相似度
            for i in range(len(image_files)):
                for j in range(i + 1, len(image_files)):
                    similarity = self._calculate_image_similarity(
                        str(image_files[i]), str(image_files[j])
                    )
                    
                    if similarity > similarity_threshold:
                        # 删除相似度高的图像
                        image_files[j].unlink()
                        logger.info(f"删除相似图像: {image_files[j]}")
            
            return True
            
        except Exception as e:
            logger.error(f"清理相似图像失败: {e}")
            return False
    
    def _calculate_image_similarity(self, img1_path: str, img2_path: str) -> float:
        """计算两张图像的相似度"""
        try:
            img1 = cv2.imread(img1_path)
            img2 = cv2.imread(img2_path)
            
            if img1 is None or img2 is None:
                return 0.0
            
            # 统一尺寸
            img1_resized = cv2.resize(img1, (224, 224))
            img2_resized = cv2.resize(img2, (224, 224))
            
            # 转换为灰度图
            gray1 = cv2.cvtColor(img1_resized, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2_resized, cv2.COLOR_BGR2GRAY)
            
            # 计算结构相似性
            similarity = cv2.matchTemplate(gray1, gray2, cv2.TM_CCOEFF_NORMED)[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"计算图像相似度失败: {e}")
            return 0.0
