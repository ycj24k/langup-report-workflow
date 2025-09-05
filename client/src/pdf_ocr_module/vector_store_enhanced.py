"""
增强版向量存储 - 基于research-report-rag的完整功能实现
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from loguru import logger

try:
    from pymilvus import MilvusClient
    from langchain_community.embeddings import OllamaEmbeddings, OpenAIEmbeddings
    from langchain_core.documents import Document
    from langchain_community.vectorstores import Milvus
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logger.warning("Milvus相关库未安装，向量存储功能将不可用")

# 条件导入，避免NameError
if not MILVUS_AVAILABLE:
    class Document:
        def __init__(self, page_content: str, metadata: Dict = None):
            self.page_content = page_content
            self.metadata = metadata or {}

try:
    from .config import OUTPUT_DIR, PICKLES_DIR
except ImportError:
    # 如果配置文件不可用，使用默认配置
    OUTPUT_DIR = Path("output")
    PICKLES_DIR = Path("pickles")
    OUTPUT_DIR.mkdir(exist_ok=True)
    PICKLES_DIR.mkdir(exist_ok=True)


class EnhancedVectorStore:
    """增强版向量存储管理器 - 集成完整的向量化和存储功能"""
    
    def __init__(self, use_milvus: bool = True, embedding_type: str = "ollama", 
                 milvus_host: str = "localhost", milvus_port: str = "19530"):
        """
        初始化向量存储
        
        Args:
            use_milvus: 是否使用Milvus数据库
            embedding_type: 向量化模型类型 ("ollama" 或 "openai")
            milvus_host: Milvus主机地址
            milvus_port: Milvus端口
        """
        self.use_milvus = use_milvus and MILVUS_AVAILABLE
        self.embedding_type = embedding_type
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.embedding_model = None
        self.milvus_client = None
        self.vector_dim = 1024  # 默认向量维度
        
        self._init_embeddings()
        
        if self.use_milvus:
            self._init_milvus()
        
    def _init_embeddings(self):
        """初始化向量化模型"""
        try:
            if not MILVUS_AVAILABLE:
                logger.warning("缺少必要的库，将使用简化向量化方法")
                self.embedding_model = None
                return
            
            if self.embedding_type == "openai":
                # 使用OpenAI Embeddings
                try:
                    self.embedding_model = OpenAIEmbeddings(
                        model='text-embedding-ada-002',
                        openai_api_base='https://open.bigmodel.cn/api/paas/v4',
                        openai_api_key='76c0d463408b4d4480c6ea9833aaca89.hdH93QfY9p17AUKD'
                    )
                    self.vector_dim = 1536  # OpenAI嵌入维度
                    logger.info("OpenAI Embeddings初始化成功")
                except Exception as e:
                    logger.error(f"OpenAI Embeddings初始化失败: {e}")
                    self.embedding_model = None
            else:
                # 使用Ollama Embeddings
                try:
                    self.embedding_model = OllamaEmbeddings(
                        model="quentinz/bge-large-zh-v1.5",
                        num_gpu=0
                    )
                    self.vector_dim = 1024  # BGE模型维度
                    logger.info("Ollama Embeddings初始化成功")
                except Exception as e:
                    logger.error(f"Ollama Embeddings初始化失败: {e}")
                    self.embedding_model = None
                    
        except Exception as e:
            logger.error(f"向量化模型初始化失败: {e}")
            self.embedding_model = None
    
    def _init_milvus(self):
        """初始化Milvus连接"""
        try:
            self.milvus_client = MilvusClient(
                uri=f"http://{self.milvus_host}:{self.milvus_port}"
            )
            logger.info("Milvus连接初始化成功")
        except Exception as e:
            logger.error(f"Milvus连接初始化失败: {e}")
            self.milvus_client = None
            self.use_milvus = False
    
    def create_collection(self, collection_name: str, description: str = "") -> Dict:
        """
        创建向量集合
        
        Args:
            collection_name: 集合名称
            description: 集合描述
            
        Returns:
            创建结果
        """
        if not self.use_milvus or not self.embedding_model:
            logger.warning("Milvus或嵌入模型未启用，创建本地集合")
            return self._create_local_collection(collection_name, description)
        
        try:
            # 检查集合是否已存在
            if self.milvus_client.has_collection(collection_name):
                logger.info(f"集合 {collection_name} 已存在")
                return {'status': 'success', 'message': f'集合 {collection_name} 已存在'}
            
            # 创建向量存储
            vector_store = Milvus(
                embedding_function=self.embedding_model,
                connection_args={
                    "host": self.milvus_host,
                    "port": self.milvus_port
                }
            )
            
            # 创建测试文档
            test_docs = [Document(
                page_content="test document", 
                metadata={"page": 0, "file": "test", "image": "", "table": ""}
            )]
            
            vector_store.from_documents(test_docs, self.embedding_model, collection_name=collection_name)
            
            logger.info(f"集合 {collection_name} 创建成功")
            return {'status': 'success', 'message': f'集合 {collection_name} 创建成功'}
            
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _create_local_collection(self, collection_name: str, description: str = "") -> Dict:
        """创建本地集合"""
        try:
            collection_path = PICKLES_DIR / collection_name
            collection_path.mkdir(exist_ok=True)
            
            # 创建集合元数据
            metadata = {
                'name': collection_name,
                'description': description,
                'created_at': str(datetime.now()),
                'vector_dim': self.vector_dim
            }
            
            with open(collection_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"本地集合 {collection_name} 创建成功")
            return {'status': 'success', 'message': f'本地集合 {collection_name} 创建成功'}
            
        except Exception as e:
            logger.error(f"创建本地集合失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def delete_collection(self, collection_name: str) -> Dict:
        """
        删除向量集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            删除结果
        """
        if not self.use_milvus:
            return self._delete_local_collection(collection_name)
        
        try:
            if not self.milvus_client.has_collection(collection_name):
                return {'status': 'error', 'message': f'集合 {collection_name} 不存在'}
            
            self.milvus_client.drop_collection(collection_name)
            logger.info(f"集合 {collection_name} 删除成功")
            return {'status': 'success', 'message': f'集合 {collection_name} 删除成功'}
            
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _delete_local_collection(self, collection_name: str) -> Dict:
        """删除本地集合"""
        try:
            import shutil
            collection_path = PICKLES_DIR / collection_name
            
            if collection_path.exists():
                shutil.rmtree(collection_path)
                logger.info(f"本地集合 {collection_name} 删除成功")
                return {'status': 'success', 'message': f'本地集合 {collection_name} 删除成功'}
            else:
                return {'status': 'error', 'message': f'本地集合 {collection_name} 不存在'}
                
        except Exception as e:
            logger.error(f"删除本地集合失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def generate_vectors(self, text: str, collection_name: str = None) -> List[float]:
        """
        生成文本向量
        
        Args:
            text: 输入文本
            collection_name: 集合名称（可选）
            
        Returns:
            向量列表
        """
        if self.embedding_model is None:
            # 使用简化的向量化方法
            return self._simple_vectorization(text)
        
        try:
            # 使用配置的嵌入模型生成向量
            if hasattr(self.embedding_model, 'embed_query'):
                vector = self.embedding_model.embed_query(text)
                return vector
            else:
                vectors = self.embedding_model.embed_documents([text])
                return vectors[0] if vectors else []
        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            return self._simple_vectorization(text)
    
    def _simple_vectorization(self, text: str) -> List[float]:
        """
        简化的向量化方法（字符频率统计）
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表
        """
        # 基于字符频率的简单向量化
        char_freq = {}
        for char in text:
            char_freq[char] = char_freq.get(char, 0) + 1
        
        # 生成固定长度的向量
        vector = [0.0] * self.vector_dim
        for i, (char, freq) in enumerate(char_freq.items()):
            if i < self.vector_dim:
                vector[i] = float(freq) / len(text)
        
        return vector
    
    def add_documents(self, collection_name: str, documents: List[Document]) -> Dict:
        """
        添加文档到向量集合
        
        Args:
            collection_name: 集合名称
            documents: 文档列表
            
        Returns:
            添加结果
        """
        if not self.use_milvus or not self.embedding_model:
            return self._add_documents_local(collection_name, documents)
        
        try:
            if not self.milvus_client.has_collection(collection_name):
                # 自动创建集合
                create_result = self.create_collection(collection_name)
                if create_result['status'] != 'success':
                    return create_result
            
            # 创建向量存储实例
            vector_store = Milvus(
                embedding_function=self.embedding_model,
                connection_args={
                    "host": self.milvus_host,
                    "port": self.milvus_port
                },
                collection_name=collection_name
            )
            
            # 添加文档
            vector_store.add_documents(documents)
            
            logger.info(f"成功添加 {len(documents)} 个文档到集合 {collection_name}")
            return {'status': 'success', 'message': f'成功添加 {len(documents)} 个文档'}
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _add_documents_local(self, collection_name: str, documents: List[Document]) -> Dict:
        """添加文档到本地集合"""
        try:
            collection_path = PICKLES_DIR / collection_name
            collection_path.mkdir(exist_ok=True)
            
            # 生成向量
            texts = [doc.page_content for doc in documents]
            vectors = []
            
            for text in texts:
                vector = self.generate_vectors(text)
                vectors.append(vector)
            
            # 加载现有数据
            data_file = collection_path / "vectors.pkl"
            if data_file.exists():
                with open(data_file, 'rb') as f:
                    existing_data = pickle.load(f)
                    
                existing_data['texts'].extend(texts)
                existing_data['vectors'].extend(vectors)
                existing_data['metadata'].extend([doc.metadata for doc in documents])
            else:
                existing_data = {
                    'texts': texts,
                    'vectors': vectors,
                    'metadata': [doc.metadata for doc in documents],
                    'collection_name': collection_name
                }
            
            # 保存数据
            with open(data_file, 'wb') as f:
                pickle.dump(existing_data, f)
            
            logger.info(f"成功添加 {len(documents)} 个文档到本地集合 {collection_name}")
            return {'status': 'success', 'message': f'成功添加 {len(documents)} 个文档到本地集合'}
            
        except Exception as e:
            logger.error(f"添加文档到本地集合失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def search_similar(self, query: str, collection_name: str, top_k: int = 5, 
                       filters: Optional[Dict] = None) -> List[Dict]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            collection_name: 集合名称
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        if not self.use_milvus or not self.embedding_model:
            return self._search_local(query, collection_name, top_k)
        
        try:
            if not self.milvus_client.has_collection(collection_name):
                logger.warning(f"集合 {collection_name} 不存在")
                return []
            
            # 生成查询向量
            query_vector = self.generate_vectors(query)
            
            # 构建过滤条件
            filter_expr = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    filter_conditions.append(f'{key} == "{value}"')
                filter_expr = ' and '.join(filter_conditions)
            
            # 执行搜索
            results = self.milvus_client.search(
                collection_name=collection_name,
                data=[query_vector],
                limit=top_k,
                output_fields=['text', 'page', 'file', 'image', 'table'],
                filter=filter_expr
            )
            
            # 格式化结果
            formatted_results = []
            if len(results) > 0:
                for hit in results[0]:
                    formatted_results.append({
                        'text': hit['entity']['text'],
                        'metadata': {
                            'page': hit['entity']['page'],
                            'file': hit['entity']['file'],
                            'image': hit['entity']['image'],
                            'table': hit['entity']['table']
                        },
                        'similarity': hit['score']
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return self._search_local(query, collection_name, top_k)
    
    def _search_local(self, query: str, collection_name: str, top_k: int = 5) -> List[Dict]:
        """
        在本地文件中搜索
        
        Args:
            query: 查询文本
            collection_name: 集合名称
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        try:
            data_file = PICKLES_DIR / collection_name / "vectors.pkl"
            
            if not data_file.exists():
                logger.warning(f"本地向量文件不存在: {data_file}")
                return []
            
            # 加载数据
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
            
            texts = data.get('texts', [])
            vectors = data.get('vectors', [])
            metadata_list = data.get('metadata', [])
            
            if not texts:
                return []
            
            # 生成查询向量
            query_vector = self.generate_vectors(query)
            
            # 计算相似度
            similarities = []
            for i, vector in enumerate(vectors):
                similarity = self._cosine_similarity(query_vector, vector)
                similarities.append((i, similarity))
            
            # 排序并返回top_k结果
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for i, similarity in similarities[:top_k]:
                if i < len(texts):
                    results.append({
                        'text': texts[i],
                        'metadata': metadata_list[i] if i < len(metadata_list) else {},
                        'similarity': similarity
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"本地搜索失败: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            相似度分数
        """
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"计算相似度失败: {e}")
            return 0.0
    
    def backup_collection(self, collection_name: str, output_name: str) -> Dict:
        """
        备份向量集合到本地
        
        Args:
            collection_name: 集合名称
            output_name: 输出名称
            
        Returns:
            备份结果
        """
        if not self.use_milvus:
            return {'status': 'error', 'message': 'Milvus未启用'}
        
        try:
            if not self.milvus_client.has_collection(collection_name):
                return {'status': 'error', 'message': f'集合 {collection_name} 不存在'}
            
            # 查询所有数据
            results = self.milvus_client.query(
                collection_name=collection_name,
                output_fields=['text', 'page', 'file', 'image', 'table'],
                limit=10000
            )
            
            if not results:
                return {'status': 'error', 'message': '集合为空'}
            
            # 提取数据
            texts = [item['text'] for item in results]
            metadata_list = [{
                'page': item.get('page', 0),
                'file': item.get('file', ''),
                'image': item.get('image', ''),
                'table': item.get('table', '')
            } for item in results]
            
            # 生成向量
            vectors = []
            for text in texts:
                vector = self.generate_vectors(text)
                vectors.append(vector)
            
            # 保存到本地
            backup_path = PICKLES_DIR / output_name
            backup_path.mkdir(exist_ok=True)
            
            backup_data = {
                'texts': texts,
                'vectors': vectors,
                'metadata': metadata_list,
                'collection_name': collection_name,
                'backup_time': str(datetime.now())
            }
            
            with open(backup_path / "backup.pkl", 'wb') as f:
                pickle.dump(backup_data, f)
            
            logger.info(f"集合 {collection_name} 备份成功到 {backup_path}")
            return {'status': 'success', 'message': f'集合 {collection_name} 备份成功'}
            
        except Exception as e:
            logger.error(f"备份集合失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def restore_collection(self, collection_name: str, backup_name: str) -> Dict:
        """
        从备份恢复向量集合
        
        Args:
            collection_name: 集合名称
            backup_name: 备份名称
            
        Returns:
            恢复结果
        """
        try:
            backup_path = PICKLES_DIR / backup_name / "backup.pkl"
            
            if not backup_path.exists():
                return {'status': 'error', 'message': f'备份文件不存在: {backup_path}'}
            
            # 加载备份数据
            with open(backup_path, 'rb') as f:
                backup_data = pickle.load(f)
            
            texts = backup_data['texts']
            metadata_list = backup_data['metadata']
            
            # 创建文档对象
            documents = []
            for i, text in enumerate(texts):
                metadata = metadata_list[i] if i < len(metadata_list) else {}
                doc = Document(page_content=text, metadata=metadata)
                documents.append(doc)
            
            # 添加到集合
            add_result = self.add_documents(collection_name, documents)
            
            if add_result['status'] == 'success':
                logger.info(f"集合 {collection_name} 从备份 {backup_name} 恢复成功")
                return {'status': 'success', 'message': f'集合 {collection_name} 恢复成功'}
            else:
                return add_result
                
        except Exception as e:
            logger.error(f"恢复集合失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """
        获取集合信息
        
        Args:
            collection_name: 集合名称
            
        Returns:
            集合信息
        """
        if not self.use_milvus:
            return self._get_local_collection_info(collection_name)
        
        try:
            if not self.milvus_client.has_collection(collection_name):
                return {'status': 'error', 'message': f'集合 {collection_name} 不存在'}
            
            # 获取集合统计信息
            stats = self.milvus_client.get_collection_stats(collection_name)
            
            return {
                'status': 'success',
                'collection_name': collection_name,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_local_collection_info(self, collection_name: str) -> Dict:
        """获取本地集合信息"""
        try:
            collection_path = PICKLES_DIR / collection_name
            
            if not collection_path.exists():
                return {'status': 'error', 'message': f'本地集合 {collection_name} 不存在'}
            
            # 读取元数据
            metadata_file = collection_path / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {'name': collection_name}
            
            # 读取向量数据
            data_file = collection_path / "vectors.pkl"
            if data_file.exists():
                with open(data_file, 'rb') as f:
                    data = pickle.load(f)
                    doc_count = len(data.get('texts', []))
            else:
                doc_count = 0
            
            return {
                'status': 'success',
                'collection_name': collection_name,
                'metadata': metadata,
                'document_count': doc_count,
                'type': 'local'
            }
            
        except Exception as e:
            logger.error(f"获取本地集合信息失败: {e}")
            return {'status': 'error', 'message': str(e)}

    # 向后兼容方法
    def search_vectors(self, query: str, collection_name: str, top_k: int = 5) -> List[Dict]:
        """搜索向量（向后兼容）"""
        return self.search_similar(query, collection_name, top_k)
