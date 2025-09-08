"""
OCR引擎 - 集成PaddleOCR和布局检测功能
"""

import cv2
import numpy as np
from PIL import Image
from loguru import logger
# 延迟导入 PaddleOCR，避免启动阶段卡顿
PaddleOCR = None
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
        self.ocr = None
        self._init_ocr()
        self._init_layout_detector()
        self.mode = "快速"

    def set_mode(self, mode: str):
        """设置解析模式影响提速与召回"""
        if mode not in ("快速", "精细"):
            return
        self.mode = mode
        # 基于模式调整参数
        try:
            if mode == "快速":
                LAYOUT_CONFIG["conf_threshold"] = max(0.35, LAYOUT_CONFIG["conf_threshold"])  # 略提阈值
                self.fast_imgsz = 768
                self.use_angle_cls = False
                self.direct_conf = 0.25
            else:
                LAYOUT_CONFIG["conf_threshold"] = 0.22
                self.fast_imgsz = 1024
                self.use_angle_cls = True
                self.direct_conf = 0.12
        except Exception:
            pass
        
    def _init_ocr(self):
        """初始化PaddleOCR"""
        try:
            global PaddleOCR
            if PaddleOCR is None:
                logger.info("正在加载PaddleOCR(首次加载可能较慢，请耐心等待)...")
                from paddleocr import PaddleOCR as _PaddleOCR
                PaddleOCR = _PaddleOCR
            self.ocr = PaddleOCR(
                use_gpu=self.use_gpu,
                lang=OCR_CONFIG.get("lang", "ch"),
                det_limit_side_len=OCR_CONFIG["det_limit_side_len"],
                layout=OCR_CONFIG["layout"],
                table=OCR_CONFIG["table"],
                det_db_unclip_ratio=OCR_CONFIG["det_db_unclip_ratio"],
                show_log=OCR_CONFIG["show_log"],
                use_angle_cls=True
            )
            logger.info("PaddleOCR初始化成功")
        except Exception as e:
            logger.error(f"PaddleOCR初始化失败: {e}")
            self.ocr = None
    
    def _init_layout_detector(self):
        """初始化布局检测器"""
        try:
            model_path = Path(LAYOUT_CONFIG["model_path"])
            # 优先加载已训练的.pt 权重，其次避免直接加载yaml导致的backbone错误
            if model_path.exists():
                if model_path.suffix.lower() == ".pt":
                    self.layout_model = YOLO(str(model_path))
                    logger.info(f"布局检测模型(.pt)加载成功: {model_path}")
                elif model_path.suffix.lower() in {".yaml", ".yml"}:
                    logger.warning("检测到的是模型配置(yaml)，非已训练权重，将回退到通用检测权重models/yolov8n.pt")
                    local_fallback = Path(__file__).parent / "models" / "yolov8n.pt"
                    self.layout_model = YOLO(str(local_fallback)) if local_fallback.exists() else YOLO("yolov8n.pt")
                    logger.info(f"已回退并加载yolov8n.pt 作为布局检测模型: {local_fallback if local_fallback.exists() else 'ultralytics内置'}")
            else:
                # 尝试加载专业备用模型
                fb = Path(LAYOUT_CONFIG.get("fallback_model", ""))
                if fb and fb.exists():
                    self.layout_model = YOLO(str(fb))
                    logger.info(f"已回退并加载备用布局模型: {fb}")
                else:
                    logger.warning("布局检测模型不存在，回退到yolov8n.pt")
                    local_fallback = Path(__file__).parent / "models" / "yolov8n.pt"
                    self.layout_model = YOLO(str(local_fallback)) if local_fallback.exists() else YOLO("yolov8n.pt")
                    logger.info(f"已回退并加载yolov8n.pt 作为布局检测模型: {local_fallback if local_fallback.exists() else 'ultralytics内置'}")
        except Exception as e:
            logger.warning(f"布局检测模型加载失败: {e}，将回退到通用检测模型")
            try:
                self.layout_model = YOLO("yolov8n.pt")
                logger.info("已回退并加载yolov8n.pt 作为布局检测模型")
            except Exception as _:
                logger.warning("通用检测模型加载失败，将使用默认规则检测")
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
            # 使用更适合专用模型的参数
            results = self.layout_model.predict(
                image_path,
                conf=LAYOUT_CONFIG["conf_threshold"],
                iou=LAYOUT_CONFIG["iou_threshold"],
                imgsz=getattr(self, 'fast_imgsz', 1024),
                verbose=False
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
            
            logger.info(f"布局检测完成，检测到 {len(layout_results)} 个区域")
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
            
            result = self.ocr.ocr(image_path, cls=getattr(self, 'use_angle_cls', True))
            
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
                    min_conf = 0.5 if self.mode == "快速" else 0.3
                    if confidence > min_conf:
                        texts.append(text)
            
            return "\n".join(texts)
            
        except Exception as e:
            logger.error(f"文字提取失败: {e}")
            return ""
    
    def extract_text_direct(self, image_path: str, confidence_threshold: float = 0.1) -> List[Dict]:
        """
        直接对整张图像进行OCR识别，不依赖布局检测
        
        Args:
            image_path: 图像路径
            confidence_threshold: 置信度阈值，默认0.1（较低阈值以获取更多文本）
            
        Returns:
            OCR识别结果列表
        """
        try:
            # 使用PaddleOCR直接识别整张图像
            result = self.ocr.ocr(image_path, cls=getattr(self, 'use_angle_cls', True))
            
            if not result or not result[0]:
                logger.warning(f"直接OCR未识别到任何文本: {image_path}")
                return []
            
            texts = []
            for line in result[0]:
                if len(line) >= 2:
                    bbox = line[0]  # 边界框坐标
                    text_info = line[1]  # 文本内容和置信度
                    
                    if len(text_info) >= 2:
                        text = text_info[0]  # 识别的文本
                        confidence = text_info[1]  # 置信度
                        
                        # 过滤置信度过低的文本（模式可覆盖）
                        min_conf = getattr(self, 'direct_conf', confidence_threshold)
                        if confidence >= min_conf:
                            # 转换边界框格式
                            x1, y1 = bbox[0]
                            x2, y2 = bbox[2]
                            
                            texts.append({
                                'text': text,
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'confidence': float(confidence),
                                'category': 'text',
                                'category_id': 0
                            })
            
            logger.info(f"直接OCR识别完成，提取到 {len(texts)} 个文本区域")
            return texts
            
        except Exception as e:
            logger.error(f"直接OCR识别失败: {e}")
            return []
    
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
            
            # 如果布局检测没有找到足够的文本区域，使用直接OCR
            if len(text_regions) < (1 if self.mode == "快速" else 1):
                logger.info("布局检测文本区域不足，使用直接OCR...")
                direct_text = self.extract_text_direct(image_path)
                if direct_text:
                    # 将直接OCR的结果作为一个整体文本区域
                    text_regions.append({
                        'bbox': None,  # 整个页面
                        'text': "\n".join([t['text'] for t in direct_text]),
                        'category': 'text',
                        'confidence': 0.8
                    })
                    logger.info(f"直接OCR提取到 {len(direct_text)} 个文本区域")
                else:
                    logger.warning("直接OCR也没有提取到文本内容")
            elif len(text_regions) < (2 if self.mode == "精细" else 1):
                logger.info("布局检测文本区域较少，尝试直接OCR补充...")
                direct_text = self.extract_text_direct(image_path)
                if direct_text:
                    # 检查直接OCR是否提供了更多内容
                    existing_text = "\n".join([tr['text'] for tr in text_regions])
                    if len(direct_text) > len(existing_text) * 1.5:  # 如果直接OCR提供的内容明显更多
                        text_regions.append({
                            'bbox': None,
                            'text': "\n".join([t['text'] for t in direct_text]),
                            'category': 'text',
                            'confidence': 0.7
                        })
                        logger.info(f"直接OCR补充提取到 {len(direct_text)} 个文本区域")
            
            return {
                'text_regions': text_regions,
                'figure_regions': figure_regions,
                'table_regions': table_regions,
                'layout_results': layout_results
            }
            
        except Exception as e:
            logger.error(f"页面处理失败: {e}")
            # 出错时尝试直接OCR
            try:
                direct_text = self.extract_text_direct(image_path)
                if direct_text:
                    return {
                        'text_regions': [{
                            'bbox': None,
                            'text': "\n".join([t['text'] for t in direct_text]),
                            'category': 'text',
                            'confidence': 0.7
                        }],
                        'figure_regions': [],
                        'table_regions': [],
                        'layout_results': []
                    }
            except Exception as direct_e:
                logger.error(f"直接OCR也失败: {direct_e}")
            
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
