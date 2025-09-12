#!/usr/bin/env python3
"""
远程GPU OCR服务器
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

from src import PDFProcessor, PPTProcessor, OfficeProcessor, OCREngine

# GPU 信息探测
def _probe_gpu_info():
    info = {
        "torch": {"available": False, "device_count": 0, "devices": []},
        "paddle": {"compiled_with_cuda": False, "device": "unknown"},
        "opencv": {"cuda_device_count": 0}
    }
    try:
        import torch
        info["torch"]["available"] = bool(torch.cuda.is_available())
        if info["torch"]["available"]:
            count = torch.cuda.device_count()
            info["torch"]["device_count"] = count
            info["torch"]["devices"] = [torch.cuda.get_device_name(i) for i in range(count)]
    except Exception as e:
        info["torch"]["error"] = str(e)
    try:
        import paddle
        info["paddle"]["compiled_with_cuda"] = bool(paddle.device.is_compiled_with_cuda())
        try:
            info["paddle"]["device"] = paddle.device.get_device()
        except Exception:
            pass
    except Exception as e:
        info["paddle"]["error"] = str(e)
    try:
        import cv2
        cnt = 0
        try:
            cnt = int(cv2.cuda.getCudaEnabledDeviceCount())
        except Exception:
            cnt = 0
        info["opencv"]["cuda_device_count"] = cnt
    except Exception as e:
        info["opencv"]["error"] = str(e)
    return info

app = FastAPI(title="远程GPU OCR服务", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量（兼容旧逻辑），同时使用 app.state 保存，确保在各 worker/路由共享
pdf_processor = None
ppt_processor = None
ocr_engine = None
office_processor = None

_warmed_up = False

def _warmup_once():
    global _warmed_up, ocr_engine
    if _warmed_up or ocr_engine is None:
        return
    try:
        # 进行一次轻量推理以触发 CUDA/Paddle/Torch 的内核与显存缓存
        # 这里使用一个极小的空白图片进行直扫，避免真实 I/O
        import numpy as np
        import cv2
        tmp = np.full((32, 32, 3), 255, dtype=np.uint8)
        tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg').name
        cv2.imwrite(tmp_path, tmp)
        try:
            _ = ocr_engine.extract_text_direct(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        _warmed_up = True
        logger.info("OCR 引擎 warmup 完成")
    except Exception as e:
        logger.warning(f"warmup 失败（不影响服务可用）: {e}")

@app.on_event("startup")
async def startup_event():
    """启动时初始化OCR组件（只执行一次）"""
    global pdf_processor, ppt_processor, ocr_engine, office_processor
    
    try:
        logger.info("正在初始化GPU OCR服务...")
        gpu_info = _probe_gpu_info()
        logger.info(f"GPU 探测: {gpu_info}")
        
        # 初始化OCR引擎（使用GPU加速）
        ocr_engine = OCREngine(use_gpu=True)
        logger.info("OCR引擎初始化成功")
        
        # 初始化PDF处理器
        pdf_processor = PDFProcessor(ocr_engine=ocr_engine)
        logger.info("PDF处理器初始化成功")
        
        # 初始化PPT处理器（传入已初始化的OCR引擎以便图片直扫补救）
        ppt_processor = PPTProcessor(ocr_engine=ocr_engine)
        logger.info("PPT处理器初始化成功")
        
        # 初始化Office处理器（只做文本解析，无需 OCR 引擎）
        office_processor = OfficeProcessor(use_gpu=False)
        logger.info("Office处理器初始化成功")
        
        # 保存到 app.state，确保路由读取的一致性
        app.state.ocr_engine = ocr_engine
        app.state.pdf_processor = pdf_processor
        app.state.ppt_processor = ppt_processor
        app.state.office_processor = office_processor
        app.state.initialized = True

        # 预热，减少首个请求的冷启动延迟
        _warmup_once()

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
        "llm_enabled": False,
        "initialized": bool(getattr(app.state, "initialized", False)),
        "gpu_info": _probe_gpu_info(),
        "components": {
            "pdf_processor": bool(getattr(app.state, "pdf_processor", None)),
            "ppt_processor": bool(getattr(app.state, "ppt_processor", None)),
            "ocr_engine": bool(getattr(app.state, "ocr_engine", None))
        }
    }

@app.post("/ocr/pdf")
async def process_pdf(file: UploadFile = File(...)):
    """处理PDF文件OCR"""
    try:
        proc = getattr(app.state, "pdf_processor", None) or pdf_processor
        if not proc:
            raise HTTPException(status_code=500, detail="PDF处理器未初始化")
        
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 处理PDF
            logger.info(f"开始处理PDF: {file.filename}")
            result = proc.process_pdf(tmp_file_path, file.filename)
            
            # 清理临时文件
            os.unlink(tmp_file_path)
            
            if result.get('status') == 'success':
                return {
                    "status": "success",
                    "filename": file.filename,
                    "result": result
                }
            else:
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
        proc = getattr(app.state, "ppt_processor", None) or ppt_processor
        if not proc:
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
            result = proc.process_ppt(tmp_file_path, file.filename)
            
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

@app.post("/ocr/office")
async def process_office(file: UploadFile = File(...)):
    """处理Office文档（Word/Excel）"""
    try:
        logger.info(f"开始处理Office文档: {file.filename}")
        
        # 检查文件类型
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.docx', '.doc', '.xlsx', '.xls']:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")
        
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 使用Office处理器处理文档
            proc = getattr(app.state, "office_processor", None) or office_processor
            if not proc:
                raise HTTPException(status_code=500, detail="Office处理器未初始化")
            result = proc.process_office_document(tmp_file_path, file.filename)
            
            if result.get('status') == 'success':
                logger.info(f"Office文档处理成功: {file.filename}")
                return result
            else:
                logger.error(f"Office文档处理失败: {result.get('message', '未知错误')}")
                raise HTTPException(status_code=500, detail=result.get('message', '处理失败'))
                
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_file_path)
            except Exception:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Office文档处理异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ocr/image")
async def process_image(file: UploadFile = File(...)):
    """处理图片OCR"""
    try:
        engine = getattr(app.state, "ocr_engine", None) or ocr_engine
        if not engine:
            raise HTTPException(status_code=500, detail="OCR引擎未初始化")
        
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 处理图片
            logger.info(f"开始处理图片: {file.filename}")
            result = engine.extract_text_direct(tmp_file_path)
            
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
        "llm_enabled": False,
        "initialized": bool(getattr(app.state, "initialized", False)),
        "gpu_info": _probe_gpu_info(),
        "components": {
            "pdf_processor": bool(getattr(app.state, "pdf_processor", None)),
            "ppt_processor": bool(getattr(app.state, "ppt_processor", None)),
            "ocr_engine": bool(getattr(app.state, "ocr_engine", None))
        }
    }

@app.get("/gpu")
async def gpu_info():
    """返回详细GPU信息"""
    return _probe_gpu_info()

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
