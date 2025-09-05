"""
向量存储 - 集成向量化和Milvus数据库操作
"""

import json
import pickle
import warnings
from pathlib import Path
from typing import List, Dict, Optional, Union
from loguru import logger

# 抑制pkg_resources弃用警告
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)

try:
    # 优先使用新包
    from langchain_ollama import OllamaEmbeddings as _OllamaEmbeddings
    OLLAMA_AVAILABLE = True
except Exception:
    try:
        # 兼容旧包
        from langchain_community.embeddings import OllamaEmbeddings as _OllamaEmbeddings
        OLLAMA_AVAILABLE = True
    except Exception:
        OLLAMA_AVAILABLE = False

try:
    from pymilvus import MilvusClient
    from langchain_core.documents import Document
    from langchain_community.vectorstores import Milvus
    MILVUS_AVAILABLE = True
except Exception:
    MILVUS_AVAILABLE = False
    logger.warning("Milvus相关库未安装，向量存储功能将不可用")

# 定义Document类作为备用
if not MILVUS_AVAILABLE:
    class Document:
        def __init__(self, page_content: str, metadata: dict = None):
            self.page_content = page_content
            self.metadata = metadata or {}

from .config import VECTOR_CONFIG, MILVUS_CONFIG, PICKLES_DIR


class VectorStore:
    """向量存储管理器"""
    
    def __init__(self, use_milvus: bool = True):
        """
        初始化向量存储
        
        Args:
            use_milvus: 是否使用Milvus数据库
        """
        self.use_milvus = use_milvus and MILVUS_AVAILABLE
        self._init_embeddings()
        self._init_milvus()
        
    def _init_embeddings(self):
        """初始化向量化模型"""
        try:
            if OLLAMA_AVAILABLE:
                self.embedding_model = _OllamaEmbeddings(
                    model=VECTOR_CONFIG["model_name"],
                    num_gpu=VECTOR_CONFIG["num_gpu"]
                )
                logger.info("Ollama Embeddings初始化成功")
            else:
                logger.warning("OllamaEmbeddings不可用，将使用备用向量化方法")
                self.embedding_model = None
        except Exception as e:
            logger.error(f"向量化模型初始化失败: {e}")
            self.embedding_model = None
    
    def _init_milvus(self):
        """初始化Milvus连接"""
        if not self.use_milvus:
            self.milvus_client = None
            return
            
        try:
            self.milvus_client = MilvusClient(
                uri=f"http://{MILVUS_CONFIG['host']}:{MILVUS_CONFIG['port']}"
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
        if not self.use_milvus:
            return {'status': 'error', 'message': 'Milvus未启用'}
        
        try:
            # 检查集合是否已存在
            if self.milvus_client.has_collection(collection_name):
                return {'status': 'success', 'message': f'集合 {collection_name} 已存在'}
            
            # 创建向量存储
            vector_store = Milvus(
                embedding_function=self.embedding_model,
                connection_args={
                    "host": MILVUS_CONFIG["host"],
                    "port": MILVUS_CONFIG["port"]
                }
            )
            
            # 创建测试文档
            test_docs = [Document(page_content="test", metadata={"source": "test"})]
            vector_store.from_documents(test_docs, self.embedding_model, collection_name=collection_name)
            
            logger.info(f"集合 {collection_name} 创建成功")
            return {'status': 'success', 'message': f'集合 {collection_name} 创建成功'}
            
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
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
            return {'status': 'error', 'message': 'Milvus未启用'}
        
        try:
            if not self.milvus_client.has_collection(collection_name):
                return {'status': 'error', 'message': f'集合 {collection_name} 不存在'}
            
            self.milvus_client.drop_collection(collection_name)
            logger.info(f"集合 {collection_name} 删除成功")
            return {'status': 'success', 'message': f'集合 {collection_name} 删除成功'}
            
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def add_documents(self, collection_name: str, documents: List[Document]) -> Dict:
        """
        添加文档到向量集合
        
        Args:
            collection_name: 集合名称
            documents: 文档列表
            
        Returns:
            添加结果
        """
        if not self.use_milvus:
            return {'status': 'error', 'message': 'Milvus未启用'}
        
        try:
            if not self.milvus_client.has_collection(collection_name):
                return {'status': 'error', 'message': f'集合 {collection_name} 不存在'}
            
            # 创建向量存储
            vector_store = Milvus(
                embedding_function=self.embedding_model,
                connection_args={
                    "host": MILVUS_CONFIG["host"],
                    "port": MILVUS_CONFIG["port"]
                }
            )
            
            # 添加文档
            vector_store.add_documents(documents)
            
            logger.info(f"成功添加 {len(documents)} 个文档到集合 {collection_name}")
            return {'status': 'success', 'message': f'成功添加 {len(documents)} 个文档'}
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def search_similar(self, collection_name: str, query: str, top_k: int = 5, 
                        filters: Optional[Dict] = None) -> Dict:
        """
        搜索相似文档
        
        Args:
            collection_name: 集合名称
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            搜索结果
        """
        if not self.use_milvus:
            return {'status': 'error', 'message': 'Milvus未启用'}
        
        try:
            if not self.milvus_client.has_collection(collection_name):
                return {'status': 'error', 'message': f'集合 {collection_name} 不存在'}
            
            # 生成查询向量
            if self.embedding_model:
                query_vector = self.embedding_model.embed_query(query)
            else:
                # 使用简化向量化
                query_vectors = self._simple_vectorization([query])
                query_vector = query_vectors[0] if query_vectors else []
            
            if not query_vector:
                return {'status': 'error', 'message': '无法生成查询向量'}
            
            # 执行搜索
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            results = self.milvus_client.search(
                collection_name=collection_name,
                data=[query_vector],
                limit=top_k,
                output_fields=['text', 'metadata'],
                filter=filters,
                search_params=search_params
            )
            
            # 格式化结果
            formatted_results = []
            for hit in results[0]:
                formatted_results.append({
                    'score': hit['score'],
                    'text': hit['entity']['text'],
                    'metadata': hit['entity']['metadata']
                })
            
            return {
                'status': 'success',
                'results': formatted_results,
                'total': len(formatted_results)
            }
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def search_vectors(self, collection_name: str, query: str, top_k: int = 5) -> Dict:
        """
        搜索向量（本地搜索，不依赖Milvus）
        
        Args:
            collection_name: 集合名称
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果
        """
        try:
            # 尝试从本地加载向量
            load_result = self.load_vectors_from_local(collection_name)
            if load_result['status'] != 'success':
                return {'status': 'error', 'message': '无法加载本地向量数据'}
            
            vectors = load_result['vectors']
            texts = load_result['texts']
            
            # 生成查询向量
            if self.embedding_model:
                query_vectors = self.embedding_model.embed_documents([query])
                query_vector = query_vectors[0] if query_vectors else []
            else:
                query_vectors = self._simple_vectorization([query])
                query_vector = query_vectors[0] if query_vectors else []
            
            if not query_vector:
                return {'status': 'error', 'message': '无法生成查询向量'}
            
            # 计算相似度
            import numpy as np
            similarities = []
            for i, vector in enumerate(vectors):
                if len(vector) == len(query_vector):
                    # 计算余弦相似度
                    dot_product = np.dot(vector, query_vector)
                    norm_a = np.linalg.norm(vector)
                    norm_b = np.linalg.norm(query_vector)
                    
                    if norm_a > 0 and norm_b > 0:
                        similarity = dot_product / (norm_a * norm_b)
                        similarities.append((similarity, i))
            
            # 排序并返回top_k结果
            similarities.sort(key=lambda x: x[0], reverse=True)
            top_results = similarities[:top_k]
            
            results = []
            for similarity, idx in top_results:
                results.append({
                    'score': float(similarity),
                    'text': texts[idx],
                    'metadata': {'index': idx}
                })
            
            return {
                'status': 'success',
                'results': results,
                'total': len(results)
            }
            
        except Exception as e:
            logger.error(f"本地向量搜索失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def generate_vectors(self, texts: List[str]) -> List[List[float]]:
        """
        生成文本向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        # 限制最大块数
        try:
            from .config import VECTOR_CONFIG
            max_chunks = int(VECTOR_CONFIG.get("max_chunks", 0))
        except Exception:
            max_chunks = 0
        if max_chunks and len(texts) > max_chunks:
            logger.info(f"向量化文本过多({len(texts)}>={max_chunks})，仅取前{max_chunks}项以提速")
            texts = texts[:max_chunks]

        if not self.embedding_model:
            return self._simple_vectorization(texts)
        
        try:
            vectors = self.embedding_model.embed_documents(texts)
            return vectors
        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            return self._simple_vectorization(texts)
    
    def _simple_vectorization(self, texts: List[str]) -> List[List[float]]:
        """
        简化的向量化方法（基于字符频率）
        
        Args:
            texts: 文本列表
            
        Returns:
            简化的向量列表
        """
        try:
            import numpy as np
            
            vectors = []
            for text in texts:
                # 简单的字符频率向量化
                char_freq = {}
                for char in text.lower():
                    if char.isalnum():
                        char_freq[char] = char_freq.get(char, 0) + 1
                
                # 转换为固定长度向量
                vector = [char_freq.get(chr(i), 0) for i in range(97, 123)]  # a-z
                vector.extend([char_freq.get(chr(i), 0) for i in range(48, 58)])  # 0-9
                
                # 归一化
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = [v / norm for v in vector]
                
                vectors.append(vector)
            
            logger.info(f"使用简化向量化方法生成了 {len(vectors)} 个向量")
            return vectors
            
        except Exception as e:
            logger.error(f"简化向量化失败: {e}")
            # 返回空向量
            return [[0.0] * 36 for _ in texts]
    
    def save_vectors_locally(self, vectors: List[List[float]], 
                            texts: List[str], output_name: str) -> bool:
        """
        保存向量到本地文件
        
        Args:
            vectors: 向量列表
            texts: 文本列表
            output_name: 输出名称
            
        Returns:
            是否保存成功
        """
        try:
            output_path = PICKLES_DIR / output_name
            output_path.mkdir(exist_ok=True)
            
            # 保存向量
            with open(output_path / "vectors.pkl", 'wb') as f:
                pickle.dump(vectors, f)
            
            # 保存文本
            with open(output_path / "texts.pkl", 'wb') as f:
                pickle.dump(texts, f)
            
            logger.info(f"向量已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存向量失败: {e}")
            return False
    
    def load_vectors_from_local(self, output_name: str) -> Dict:
        """
        从本地文件加载向量
        
        Args:
            output_name: 输出名称
            
        Returns:
            加载的数据字典
        """
        try:
            output_path = PICKLES_DIR / output_name
            
            if not output_path.exists():
                return {'status': 'error', 'message': f'目录不存在: {output_path}'}
            
            # 加载向量
            vectors_path = output_path / "vectors.pkl"
            texts_path = output_path / "texts.pkl"
            
            if not vectors_path.exists() or not texts_path.exists():
                return {'status': 'error', 'message': '向量或文本文件不存在'}
            
            with open(vectors_path, 'rb') as f:
                vectors = pickle.load(f)
            
            with open(texts_path, 'rb') as f:
                texts = pickle.load(f)
            
            return {
                'status': 'success',
                'vectors': vectors,
                'texts': texts
            }
            
        except Exception as e:
            logger.error(f"加载向量失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
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
            
            # 获取集合中的所有数据
            results = self.milvus_client.query(
                collection_name=collection_name,
                output_fields=['text', 'metadata'],
                limit=10000  # 最大限制
            )
            
            if not results:
                return {'status': 'error', 'message': '集合为空'}
            
            # 提取文本
            texts = [item['text'] for item in results]
            
            # 生成向量
            vectors = self.generate_vectors(texts)
            
            # 保存到本地
            success = self.save_vectors_locally(vectors, texts, output_name)
            
            if success:
                return {'status': 'success', 'message': f'集合 {collection_name} 备份成功'}
            else:
                return {'status': 'error', 'message': '本地保存失败'}
                
        except Exception as e:
            logger.error(f"备份集合失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def restore_collection(self, collection_name: str, output_name: str) -> Dict:
        """
        从本地恢复向量集合
        
        Args:
            collection_name: 集合名称
            output_name: 输出名称
            
        Returns:
            恢复结果
        """
        if not self.use_milvus:
            return {'status': 'error', 'message': 'Milvus未启用'}
        
        try:
            # 加载本地数据
            load_result = self.load_vectors_from_local(output_name)
            if load_result['status'] != 'success':
                return load_result
            
            vectors = load_result['vectors']
            texts = load_result['texts']
            
            # 创建文档对象
            documents = []
            for i, text in enumerate(texts):
                doc = Document(
                    page_content=text,
                    metadata={"source": f"restored_{i}", "restored": True}
                )
                documents.append(doc)
            
            # 添加到集合
            add_result = self.add_documents(collection_name, documents)
            
            if add_result['status'] == 'success':
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
            return {'status': 'error', 'message': 'Milvus未启用'}
        
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
