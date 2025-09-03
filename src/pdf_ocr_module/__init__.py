"""
PDF OCR 向量化模块
集成PDF上传、OCR识别、布局检测、向量化存储等功能
"""

from .pdf_processor import PDFProcessor
from .ocr_engine import OCREngine
from .vector_store import VectorStore
from .api_server import PDFOCRServer

__version__ = "1.0.0"
__all__ = ["PDFProcessor", "OCREngine", "VectorStore", "PDFOCRServer"]
