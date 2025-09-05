#!/usr/bin/env python3
"""
远程GPU OCR服务器 - 主程序
部署在192.168.3.133上，提供OCR识别API服务
"""

import os
import sys
import json
import base64
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger

# 添加src路径
sys.path.append('src')

from src.ocr_engine import OCREngine
from src.pdf_processor import PDFProcessor
from src.ppt_processor import PPTProcessor

app = FastAPI(title="远程GPU OCR服务", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
pdf_processor = None
ppt_processor = None
ocr_engine = None

@app.on_event("startup")
async def startup_event():
    """启动时初始化OCR组件"""
    global pdf_processor, ppt_processor, ocr_engine
    
    try:
        logger.info("正在初始化GPU OCR服务...")
        
        # 初始化OCR引擎（使用GPU）
        ocr_engine = OCREngine(use_gpu=True)
        logger.info("OCR引擎初始化成功")
        
        # 初始化PDF处理器
        pdf_processor = PDFProcessor(ocr_engine=ocr_engine)
        logger.info("PDF处理器初始化成功")
        
        # 初始化PPT处理器
        ppt_processor = PPTProcessor()
        logger.info("PPT处理器初始化成功")
        
        logger.info("🚀 GPU OCR服务启动成功！")
        
    except Exception as e:
        logger.error(f"OCR服务初始化失败: {e}")
        raise

@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "running",
        "service": "GPU OCR Service",
        "gpu_enabled": True,
        "components": {
            "pdf_processor": pdf_processor is not None,
            "ppt_processor": ppt_processor is not None,
            "ocr_engine": ocr_engine is not None
        }
    }

@app.post("/ocr/pdf")
async def process_pdf(file: UploadFile = File(...)):
    """处理PDF文件OCR"""
    try:
        if not pdf_processor:
            raise HTTPException(status_code=500, detail="PDF处理器未初始化")
        
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 处理PDF
            logger.info(f"开始处理PDF: {file.filename}")
            result = pdf_processor.process_pdf(tmp_file_path, file.filename)
            
            # 清理临时文件
            os.unlink(tmp_file_path)
            
            if result.get('status') == 'success':
                logger.info(f"PDF处理成功: {file.filename}")
                return {
                    "status": "success",
                    "filename": file.filename,
                    "result": result
                }
            else:
                logger.error(f"PDF处理失败: {file.filename}")
                return {
                    "status": "error",
                    "filename": file.filename,
                    "message": result.get('message', '处理失败')
                }
                
        except Exception as e:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            raise e
            
    except Exception as e:
        logger.error(f"PDF处理异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ocr/ppt")
async def process_ppt(file: UploadFile = File(...)):
    """处理PPT文件OCR"""
    try:
        if not ppt_processor:
            raise HTTPException(status_code=500, detail="PPT处理器未初始化")
        
        # 保存上传的文件到临时目录
        suffix = '.pptx' if file.filename.endswith('.pptx') else '.ppt'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 处理PPT
            logger.info(f"开始处理PPT: {file.filename}")
            result = ppt_processor.process_ppt(tmp_file_path, file.filename)
            
            # 清理临时文件
            os.unlink(tmp_file_path)
            
            if result.get('status') == 'success':
                logger.info(f"PPT处理成功: {file.filename}")
                return {
                    "status": "success",
                    "filename": file.filename,
                    "result": result
                }
            else:
                logger.error(f"PPT处理失败: {file.filename}")
                return {
                    "status": "error",
                    "filename": file.filename,
                    "message": result.get('message', '处理失败')
                }
                
        except Exception as e:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            raise e
            
    except Exception as e:
        logger.error(f"PPT处理异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ocr/image")
async def process_image(file: UploadFile = File(...)):
    """处理图片OCR"""
    try:
        if not ocr_engine:
            raise HTTPException(status_code=500, detail="OCR引擎未初始化")
        
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 处理图片
            logger.info(f"开始处理图片: {file.filename}")
            result = ocr_engine.extract_text_direct(tmp_file_path)
            
            # 清理临时文件
            os.unlink(tmp_file_path)
            
            logger.info(f"图片处理成功: {file.filename}")
            return {
                "status": "success",
                "filename": file.filename,
                "text": result
            }
                
        except Exception as e:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            raise e
            
    except Exception as e:
        logger.error(f"图片处理异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "gpu_available": True,
        "components": {
            "pdf_processor": pdf_processor is not None,
            "ppt_processor": ppt_processor is not None,
            "ocr_engine": ocr_engine is not None
        }
    }

if __name__ == "__main__":
    # 配置日志
    logger.add("logs/remote_ocr_server.log", rotation="10 MB", retention="7 days")
    
    # 启动服务
    uvicorn.run(
        app,
        host="0.0.0.0",  # 允许外部访问
        port=8888,
        reload=False,
        log_level="info"
    )
