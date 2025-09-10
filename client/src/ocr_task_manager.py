# -*- coding: utf-8 -*-
"""
OCR任务管理器
负责管理多进程OCR任务，文件锁定，进度跟踪
"""
import os
import time
import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import queue
from loguru import logger

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class OCRTask:
    task_id: str
    file_path: str
    file_type: str
    status: TaskStatus
    progress: float  # 0.0 - 1.0
    message: str
    result: Optional[Dict] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    worker_id: Optional[int] = None

class OCRTaskManager:
    def __init__(self, max_workers: int = None, progress_callback: Callable = None):
        self.max_workers = max_workers or min(4, multiprocessing.cpu_count())
        self.progress_callback = progress_callback
        
        # 任务管理
        self.tasks: Dict[str, OCRTask] = {}
        self.locked_files: set = set()  # 正在处理的文件路径
        
        # 线程安全
        self.lock = threading.RLock()
        self.task_queue = queue.Queue()
        
        # 进程池
        self.executor = None
        self._shutdown = False
        
        logger.info(f"OCR任务管理器初始化完成，最大工作进程数: {self.max_workers}")
    
    def start(self):
        """启动任务管理器"""
        if self.executor is None:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
            logger.info("OCR任务管理器已启动")
    
    def stop(self):
        """停止任务管理器"""
        self._shutdown = True
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
        logger.info("OCR任务管理器已停止")
    
    def is_file_locked(self, file_path: str) -> bool:
        """检查文件是否被锁定"""
        with self.lock:
            return file_path in self.locked_files
    
    def lock_file(self, file_path: str) -> bool:
        """锁定文件"""
        with self.lock:
            if file_path in self.locked_files:
                return False
            self.locked_files.add(file_path)
            return True
    
    def unlock_file(self, file_path: str):
        """解锁文件"""
        with self.lock:
            self.locked_files.discard(file_path)
    
    def submit_task(self, file_path: str, file_type: str, processor_func: Callable, 
                   *args, **kwargs) -> str:
        """提交OCR任务"""
        if self._shutdown:
            raise RuntimeError("任务管理器已关闭")
        
        if self.is_file_locked(file_path):
            raise ValueError(f"文件 {file_path} 正在处理中")
        
        task_id = f"{int(time.time() * 1000)}_{hash(file_path) % 10000}"
        
        with self.lock:
            task = OCRTask(
                task_id=task_id,
                file_path=file_path,
                file_type=file_type,
                status=TaskStatus.PENDING,
                progress=0.0,
                message="等待处理..."
            )
            self.tasks[task_id] = task
            self.lock_file(file_path)
        
        # 启动任务
        self._start_task(task, processor_func, *args, **kwargs)
        
        logger.info(f"OCR任务已提交: {task_id} - {file_path}")
        return task_id
    
    def _start_task(self, task: OCRTask, processor_func: Callable, *args, **kwargs):
        """启动任务"""
        if not self.executor:
            self.start()
        
        # 更新任务状态
        with self.lock:
            task.status = TaskStatus.RUNNING
            task.start_time = time.time()
            task.message = "正在处理..."
        
        # 提交到进程池
        future = self.executor.submit(self._run_task, task, processor_func, *args, **kwargs)
        
        # 启动监控线程
        monitor_thread = threading.Thread(
            target=self._monitor_task,
            args=(task.task_id, future),
            daemon=True
        )
        monitor_thread.start()
    
    def _run_task(self, task: OCRTask, processor_func: Callable, *args, **kwargs) -> Dict:
        """在子进程中运行任务"""
        try:
            # 更新进度
            self._update_task_progress(task.task_id, 0.1, "开始处理...")
            
            # 调用处理器函数
            result = processor_func(task.file_path, *args, **kwargs)
            
            # 更新进度
            self._update_task_progress(task.task_id, 1.0, "处理完成")
            
            return result
            
        except Exception as e:
            logger.error(f"OCR任务执行失败: {task.task_id} - {e}")
            self._update_task_progress(task.task_id, 0.0, f"处理失败: {str(e)}")
            raise
    
    def _monitor_task(self, task_id: str, future):
        """监控任务执行"""
        try:
            result = future.result(timeout=3600)  # 1小时超时
            
            with self.lock:
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    task.status = TaskStatus.COMPLETED
                    task.progress = 1.0
                    task.message = "处理完成"
                    task.result = result
                    task.end_time = time.time()
                    
                    # 解锁文件
                    self.unlock_file(task.file_path)
                    
                    logger.info(f"OCR任务完成: {task_id}")
                    
        except Exception as e:
            with self.lock:
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    task.status = TaskStatus.FAILED
                    task.message = f"处理失败: {str(e)}"
                    task.error = str(e)
                    task.end_time = time.time()
                    
                    # 解锁文件
                    self.unlock_file(task.file_path)
                    
                    logger.error(f"OCR任务失败: {task_id} - {e}")
        
        # 通知进度回调
        if self.progress_callback:
            self.progress_callback(task_id)
    
    def _update_task_progress(self, task_id: str, progress: float, message: str):
        """更新任务进度"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.progress = progress
                task.message = message
    
    def get_task_status(self, task_id: str) -> Optional[OCRTask]:
        """获取任务状态"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[OCRTask]:
        """获取所有任务"""
        with self.lock:
            return list(self.tasks.values())
    
    def get_running_tasks(self) -> List[OCRTask]:
        """获取正在运行的任务"""
        with self.lock:
            return [task for task in self.tasks.values() 
                   if task.status == TaskStatus.RUNNING]
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                    task.status = TaskStatus.CANCELLED
                    task.message = "已取消"
                    self.unlock_file(task.file_path)
                    logger.info(f"OCR任务已取消: {task_id}")
                    return True
        return False
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """清理已完成的任务"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self.lock:
            to_remove = []
            for task_id, task in self.tasks.items():
                if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] 
                    and task.end_time 
                    and (current_time - task.end_time) > max_age_seconds):
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.tasks[task_id]
            
            if to_remove:
                logger.info(f"清理了 {len(to_remove)} 个已完成的任务")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self.lock:
            stats = {
                'total_tasks': len(self.tasks),
                'pending': 0,
                'running': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0,
                'locked_files': len(self.locked_files)
            }
            
            for task in self.tasks.values():
                stats[task.status.value] += 1
            
            return stats


# 全局任务管理器实例
_global_task_manager: Optional[OCRTaskManager] = None

def get_task_manager() -> OCRTaskManager:
    """获取全局任务管理器"""
    global _global_task_manager
    if _global_task_manager is None:
        _global_task_manager = OCRTaskManager()
    return _global_task_manager

def shutdown_task_manager():
    """关闭全局任务管理器"""
    global _global_task_manager
    if _global_task_manager:
        _global_task_manager.stop()
        _global_task_manager = None
