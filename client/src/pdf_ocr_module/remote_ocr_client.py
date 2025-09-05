"""
远程OCR客户端
用于调用远程GPU OCR服务
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

class RemoteOCRClient:
    """远程OCR客户端"""
    
    def __init__(self, server_url: str = "http://192.168.3.133:8888"):
        """
        初始化远程OCR客户端
        
        Args:
            server_url: 远程OCR服务器地址
        """
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 300  # 5分钟超时
        
    def check_server_health(self) -> bool:
        """检查服务器健康状态"""
        try:
            response = self.session.get(f"{self.server_url}/health")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"远程OCR服务器健康检查通过: {data}")
                return True
            else:
                logger.error(f"远程OCR服务器健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"无法连接到远程OCR服务器: {e}")
            return False
    
    def process_pdf(self, pdf_path: str, filename: str) -> Dict:
        """
        处理PDF文件
        
        Args:
            pdf_path: PDF文件路径
            filename: 文件名
            
        Returns:
            处理结果
        """
        try:
            if not os.path.exists(pdf_path):
                return {'status': 'error', 'message': f'文件不存在: {pdf_path}'}
            
            logger.info(f"发送PDF到远程GPU服务器: {filename}")
            
            with open(pdf_path, 'rb') as f:
                files = {'file': (filename, f, 'application/pdf')}
                response = self.session.post(
                    f"{self.server_url}/ocr/pdf",
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    logger.info(f"远程PDF处理成功: {filename}")
                    return result['result']
                else:
                    logger.error(f"远程PDF处理失败: {result.get('message', '未知错误')}")
                    return {'status': 'error', 'message': result.get('message', '处理失败')}
            else:
                logger.error(f"远程PDF处理请求失败: {response.status_code}")
                return {'status': 'error', 'message': f'服务器错误: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"远程PDF处理异常: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def process_ppt(self, ppt_path: str, filename: str) -> Dict:
        """
        处理PPT文件
        
        Args:
            ppt_path: PPT文件路径
            filename: 文件名
            
        Returns:
            处理结果
        """
        try:
            if not os.path.exists(ppt_path):
                return {'status': 'error', 'message': f'文件不存在: {ppt_path}'}
            
            logger.info(f"发送PPT到远程GPU服务器: {filename}")
            
            with open(ppt_path, 'rb') as f:
                files = {'file': (filename, f, 'application/vnd.ms-powerpoint')}
                response = self.session.post(
                    f"{self.server_url}/ocr/ppt",
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    logger.info(f"远程PPT处理成功: {filename}")
                    return result['result']
                else:
                    logger.error(f"远程PPT处理失败: {result.get('message', '未知错误')}")
                    return {'status': 'error', 'message': result.get('message', '处理失败')}
            else:
                logger.error(f"远程PPT处理请求失败: {response.status_code}")
                return {'status': 'error', 'message': f'服务器错误: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"远程PPT处理异常: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def process_image(self, image_path: str, filename: str) -> str:
        """
        处理图片OCR
        
        Args:
            image_path: 图片文件路径
            filename: 文件名
            
        Returns:
            识别的文本
        """
        try:
            if not os.path.exists(image_path):
                return ""
            
            logger.info(f"发送图片到远程GPU服务器: {filename}")
            
            with open(image_path, 'rb') as f:
                files = {'file': (filename, f, 'image/jpeg')}
                response = self.session.post(
                    f"{self.server_url}/ocr/image",
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    logger.info(f"远程图片处理成功: {filename}")
                    return result.get('text', '')
                else:
                    logger.error(f"远程图片处理失败: {result.get('message', '未知错误')}")
                    return ""
            else:
                logger.error(f"远程图片处理请求失败: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"远程图片处理异常: {e}")
            return ""
