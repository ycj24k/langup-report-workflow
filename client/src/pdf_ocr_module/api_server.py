"""
API服务器 - 提供HTTP接口服务
"""

import threading
import time
from uuid import uuid4
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from loguru import logger

from .pdf_processor import PDFProcessor
from .vector_store import VectorStore
from .config import SERVER_CONFIG, SUPPORTED_FORMATS


class PDFOCRServer:
    """PDF OCR API服务器"""
    
    def __init__(self, use_milvus: bool = True):
        """
        初始化API服务器
        
        Args:
            use_milvus: 是否使用Milvus数据库
        """
        self.pdf_processor = PDFProcessor()
        self.vector_store = VectorStore(use_milvus=use_milvus)
        self.task_status = {}
        self.app = self._create_app()
        
    def _create_app(self) -> FastAPI:
        """创建FastAPI应用"""
        app = FastAPI(
            title="PDF OCR 向量化服务",
            description="提供PDF上传、OCR识别、向量化存储等功能的API服务",
            version="1.0.0"
        )
        
        # 注册路由
        self._register_routes(app)
        
        return app
    
    def _register_routes(self, app: FastAPI):
        """注册API路由"""
        
        @app.get("/health")
        async def health_check():
            """健康检查"""
            return {"status": "healthy", "timestamp": time.time()}
        
        @app.post("/upload")
        async def upload_pdf(
            file: UploadFile = File(...),
            vector_store_name: str = Form(...),
            output_name: Optional[str] = Form(None)
        ):
            """上传PDF文件"""
            try:
                # 检查文件格式
                if not file.filename.lower().endswith('.pdf'):
                    raise HTTPException(status_code=400, detail="只支持PDF文件")
                
                # 保存上传的文件
                upload_dir = Path("uploads")
                upload_dir.mkdir(exist_ok=True)
                
                file_path = upload_dir / file.filename
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                # 异步处理PDF
                task_id = f'{int(time.time())}-{str(uuid4())[:8]}'
                self.task_status[task_id] = {
                    "status": "queued",
                    "message": f"文件 {file.filename} 已上传，等待处理",
                    "file_path": str(file_path),
                    "vector_store_name": vector_store_name
                }
                
                # 启动处理线程
                threading.Thread(
                    target=self._process_pdf_task,
                    args=(task_id, str(file_path), vector_store_name, output_name)
                ).start()
                
                return {
                    "status": "success",
                    "message": "文件上传成功，开始处理",
                    "task_id": task_id
                }
                
            except Exception as e:
                logger.error(f"文件上传失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/embedding")
        async def process_pdf_embedding(
            file_path: str = Form(...),
            vector_store_name: str = Form(...),
            output_name: Optional[str] = Form(None)
        ):
            """处理PDF嵌入（指定文件路径）"""
            try:
                task_id = f'{int(time.time())}-{str(uuid4())[:8]}'
                self.task_status[task_id] = {
                    "status": "queued",
                    "message": f"开始处理文件: {file_path}",
                    "file_path": file_path,
                    "vector_store_name": vector_store_name
                }
                
                # 启动处理线程
                threading.Thread(
                    target=self._process_pdf_task,
                    args=(task_id, file_path, vector_store_name, output_name)
                ).start()
                
                return {
                    "status": "success",
                    "message": "任务已启动",
                    "task_id": task_id
                }
                
            except Exception as e:
                logger.error(f"启动PDF处理失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/task_status/{task_id}")
        async def get_task_status(task_id: str):
            """获取任务状态"""
            if task_id not in self.task_status:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            return self.task_status[task_id]
        
        @app.get("/tasks")
        async def list_tasks():
            """列出所有任务"""
            return {
                "total": len(self.task_status),
                "tasks": self.task_status
            }
        
        @app.post("/vector_store/create")
        async def create_vector_store(
            collection_name: str = Form(...),
            description: str = Form("")
        ):
            """创建向量集合"""
            try:
                result = self.vector_store.create_collection(collection_name, description)
                if result['status'] == 'success':
                    return JSONResponse(content=result, status_code=200)
                else:
                    return JSONResponse(content=result, status_code=400)
                    
            except Exception as e:
                logger.error(f"创建向量集合失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.delete("/vector_store/{collection_name}")
        async def delete_vector_store(collection_name: str):
            """删除向量集合"""
            try:
                result = self.vector_store.delete_collection(collection_name)
                if result['status'] == 'success':
                    return JSONResponse(content=result, status_code=200)
                else:
                    return JSONResponse(content=result, status_code=400)
                    
            except Exception as e:
                logger.error(f"删除向量集合失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/vector_store/search")
        async def search_vectors(
            collection_name: str = Form(...),
            query: str = Form(...),
            top_k: int = Form(5)
        ):
            """搜索向量"""
            try:
                result = self.vector_store.search_similar(collection_name, query, top_k)
                if result['status'] == 'success':
                    return JSONResponse(content=result, status_code=200)
                else:
                    return JSONResponse(content=result, status_code=400)
                    
            except Exception as e:
                logger.error(f"搜索向量失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/vector_store/backup")
        async def backup_vector_store(
            collection_name: str = Form(...),
            output_name: str = Form(...)
        ):
            """备份向量集合"""
            try:
                result = self.vector_store.backup_collection(collection_name, output_name)
                if result['status'] == 'success':
                    return JSONResponse(content=result, status_code=200)
                else:
                    return JSONResponse(content=result, status_code=400)
                    
            except Exception as e:
                logger.error(f"备份向量集合失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/vector_store/restore")
        async def restore_vector_store(
            collection_name: str = Form(...),
            output_name: str = Form(...)
        ):
            """恢复向量集合"""
            try:
                result = self.vector_store.restore_collection(collection_name, output_name)
                if result['status'] == 'success':
                    return JSONResponse(content=result, status_code=200)
                else:
                    return JSONResponse(content=result, status_code=400)
                    
            except Exception as e:
                logger.error(f"恢复向量集合失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/vector_store/{collection_name}/info")
        async def get_vector_store_info(collection_name: str):
            """获取向量集合信息"""
            try:
                result = self.vector_store.get_collection_info(collection_name)
                if result['status'] == 'success':
                    return JSONResponse(content=result, status_code=200)
                else:
                    return JSONResponse(content=result, status_code=400)
                    
            except Exception as e:
                logger.error(f"获取向量集合信息失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/batch_process")
        async def batch_process_pdfs(
            pdf_dir: str = Form(...),
            vector_store_name: str = Form(...),
            output_base_name: Optional[str] = Form(None)
        ):
            """批量处理PDF文件"""
            try:
                task_id = f'{int(time.time())}-{str(uuid4())[:8]}'
                self.task_status[task_id] = {
                    "status": "queued",
                    "message": f"开始批量处理目录: {pdf_dir}",
                    "pdf_dir": pdf_dir,
                    "vector_store_name": vector_store_name
                }
                
                # 启动批量处理线程
                threading.Thread(
                    target=self._batch_process_task,
                    args=(task_id, pdf_dir, vector_store_name, output_base_name)
                ).start()
                
                return {
                    "status": "success",
                    "message": "批量处理任务已启动",
                    "task_id": task_id
                }
                
            except Exception as e:
                logger.error(f"启动批量处理失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def _process_pdf_task(self, task_id: str, file_path: str, 
                          vector_store_name: str, output_name: Optional[str]):
        """处理PDF任务"""
        try:
            # 更新任务状态
            self.task_status[task_id]["status"] = "processing"
            self.task_status[task_id]["message"] = "正在处理PDF文件..."
            
            # 处理PDF
            result = self.pdf_processor.process_pdf(file_path, output_name)
            
            if result['status'] == 'success':
                # 生成向量
                texts = [text['text'] for text in result['texts']]
                vectors = self.vector_store.generate_vectors(texts)
                
                # 保存向量到本地
                if output_name is None:
                    output_name = Path(file_path).stem
                
                self.vector_store.save_vectors_locally(vectors, texts, output_name)
                
                # 如果启用了Milvus，添加到向量数据库
                if self.vector_store.use_milvus:
                    from langchain_core.documents import Document
                    documents = []
                    for i, text in enumerate(texts):
                        doc = Document(
                            page_content=text,
                            metadata={
                                "source": file_path,
                                "page": result['texts'][i]['page'],
                                "category": result['texts'][i]['category']
                            }
                        )
                        documents.append(doc)
                    
                    self.vector_store.add_documents(vector_store_name, documents)
                
                # 更新任务状态
                self.task_status[task_id]["status"] = "completed"
                self.task_status[task_id]["message"] = "PDF处理完成"
                self.task_status[task_id]["result"] = result
                
            else:
                # 处理失败
                self.task_status[task_id]["status"] = "failed"
                self.task_status[task_id]["message"] = result['message']
                
        except Exception as e:
            logger.error(f"PDF处理任务失败: {e}")
            self.task_status[task_id]["status"] = "failed"
            self.task_status[task_id]["message"] = str(e)
    
    def _batch_process_task(self, task_id: str, pdf_dir: str, 
                           vector_store_name: str, output_base_name: Optional[str]):
        """批量处理任务"""
        try:
            # 更新任务状态
            self.task_status[task_id]["status"] = "processing"
            self.task_status[task_id]["message"] = "正在批量处理PDF文件..."
            
            # 批量处理
            results = self.pdf_processor.batch_process(pdf_dir, output_base_name)
            
            # 更新任务状态
            self.task_status[task_id]["status"] = "completed"
            self.task_status[task_id]["message"] = f"批量处理完成，共处理 {len(results)} 个文件"
            self.task_status[task_id]["results"] = results
            
        except Exception as e:
            logger.error(f"批量处理任务失败: {e}")
            self.task_status[task_id]["status"] = "failed"
            self.task_status[task_id]["message"] = str(e)
    
    def run(self, host: str = None, port: int = None, **kwargs):
        """
        运行服务器
        
        Args:
            host: 主机地址
            port: 端口号
            **kwargs: 其他参数
        """
        import uvicorn
        
        host = host or SERVER_CONFIG["host"]
        port = port or SERVER_CONFIG["port"]
        
        logger.info(f"启动PDF OCR API服务器: {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=SERVER_CONFIG["reload"],
            log_level=SERVER_CONFIG["log_level"],
            **kwargs
        )
