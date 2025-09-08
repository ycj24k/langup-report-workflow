"""
LLM处理器 - 用于生成摘要、关键词等AI分析功能
"""

import json
import httpx
from loguru import logger
from typing import List, Dict, Optional
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
# 延迟导入，避免启动时的导入错误
ChatOpenAI = None

from .config import LLM_CONFIG, PROMPTS
from .http_client import LangUpAPIClient


class LLMProcessor:
    """LLM处理器，负责AI内容分析"""
    
    def __init__(self):
        """初始化LLM处理器"""
        self._init_llm()
        
    def _init_llm(self):
        """初始化LLM模型"""
        global ChatOpenAI
        try:
            if LLM_CONFIG.get("provider") == "langup":
                self.client = LangUpAPIClient(
                    login_url=LLM_CONFIG["login_url"],
                    chat_url=LLM_CONFIG["chat_url"],
                    account=LLM_CONFIG["account"],
                    password=LLM_CONFIG["password"],
                    access_key=LLM_CONFIG.get("access_key"),
                    access_secret=LLM_CONFIG.get("access_secret"),
                    timeout=LLM_CONFIG.get("timeout", 60),
                )
                self.llm = None
                logger.info("LLM切换为LangUp API客户端模式")
                return

            # 兼容旧OpenAI配置
            if ChatOpenAI is None:
                try:
                    from langchain_openai import ChatOpenAI
                except ImportError:
                    from langchain_community.chat_models import ChatOpenAI
            self.llm = ChatOpenAI(
                model_name=LLM_CONFIG["model_name"],
                base_url=LLM_CONFIG["base_url"],
                api_key=LLM_CONFIG["api_key"],
                max_tokens=LLM_CONFIG["max_tokens"],
                temperature=LLM_CONFIG["temperature"]
            )
            logger.info("LLM模型初始化成功")
        except Exception as e:
            logger.error(f"LLM模型初始化失败: {e}")
            self.llm = None
    
    def _truncate(self, text: str, max_chars: int = 6000) -> str:
        """安全截断，避免超长上下文导致阻塞或超时"""
        if not isinstance(text, str):
            return ""
        if len(text) <= max_chars:
            return text
        return text[:max_chars]
    
    def generate_summary(self, text: str) -> str:
        """
        生成文本摘要
        
        Args:
            text: 输入文本
            
        Returns:
            生成的摘要
        """
        # LangUp 模式
        if hasattr(self, 'client') and self.client:
            try:
                logger.info("开始生成摘要（LangUp）")
                prompt = PROMPTS["summary"].format(context=self._truncate(text))
                result = self.client.complete_chat(prompt)
                logger.info("摘要生成完成")
                return result.strip() if isinstance(result, str) else str(result)
            except Exception as e:
                logger.error(f"生成摘要失败: {e}")
                return self._fallback_summary(text)
        
        # 旧OpenAI模式
        if not self.llm:
            return self._fallback_summary(text)
        try:
            prompt = PromptTemplate(template=PROMPTS["summary"], input_variables=["context"])
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"context": text})
            return result.strip()
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            return self._fallback_summary(text)
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 输入文本
            
        Returns:
            关键词列表
        """
        # LangUp 模式
        if hasattr(self, 'client') and self.client:
            try:
                logger.info("开始提取关键词（LangUp）")
                prompt = PROMPTS["keyword"].format(context=self._truncate(text))
                result = self.client.complete_chat(prompt)
                logger.info("关键词提取完成")
                return self._parse_keywords(str(result))
            except Exception as e:
                logger.error(f"提取关键词失败: {e}")
                return self._fallback_keywords(text)
        
        # 旧OpenAI模式
        if not self.llm:
            return self._fallback_keywords(text)
        try:
            prompt = PromptTemplate(template=PROMPTS["keyword"], input_variables=["context"])
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"context": text})
            return self._parse_keywords(result)
        except Exception as e:
            logger.error(f"提取关键词失败: {e}")
            return self._fallback_keywords(text)
    
    def generate_hybrid_summary(self, text: str) -> str:
        """
        生成混合摘要
        
        Args:
            text: 输入文本
            
        Returns:
            生成的混合摘要
        """
        # LangUp 模式
        if hasattr(self, 'client') and self.client:
            try:
                logger.info("开始生成混合摘要（LangUp）")
                prompt = PROMPTS["hybrid"].format(context=self._truncate(text))
                result = self.client.complete_chat(prompt)
                logger.info("混合摘要生成完成")
                return str(result).strip()
            except Exception as e:
                logger.error(f"生成混合摘要失败: {e}")
                return self._fallback_hybrid_summary(text)
        
        # 旧OpenAI模式
        if not self.llm:
            return self._fallback_hybrid_summary(text)
        try:
            prompt = PromptTemplate(template=PROMPTS["hybrid"], input_variables=["context"])
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"context": text})
            return result.strip()
        except Exception as e:
            logger.error(f"生成混合摘要失败: {e}")
            return self._fallback_hybrid_summary(text)
    
    def convert_to_markdown(self, text: str) -> str:
        """
        转换为Markdown格式
        
        Args:
            text: 输入文本
            
        Returns:
            Markdown格式文本
        """
        # LangUp 模式
        if hasattr(self, 'client') and self.client:
            try:
                logger.info("开始Markdown转换（LangUp）")
                prompt = PROMPTS["markdown"].format(context=self._truncate(text, max_chars=8000))
                result = self.client.complete_chat(prompt)
                logger.info("Markdown转换完成")
                return str(result).strip()
            except Exception as e:
                logger.error(f"转换为Markdown失败: {e}")
                return self._fallback_markdown(text)
        
        # 旧OpenAI模式
        if not self.llm:
            return self._fallback_markdown(text)

    def classify(self, text: str) -> Dict:
        """基于LLM的多标签分类，返回 { categories: [{name, description}], confidence }"""
        try:
            if hasattr(self, 'client') and self.client:
                logger.info("开始分类（LangUp）")
                prompt = PROMPTS["classify"].format(context=self._truncate(text))
                raw = self.client.complete_chat(prompt)
                try:
                    data = json.loads(raw) if isinstance(raw, str) else raw
                except Exception:
                    data = {"categories": [], "confidence": 0.0, "raw": raw}
                # 规整化：支持对象数组 {name, description}，并兼容字符串/列表
                cats_raw = data.get("categories") or []
                cats: List[Dict[str, str]] = []
                if isinstance(cats_raw, list):
                    for item in cats_raw:
                        if isinstance(item, dict):
                            name = str(item.get("name", "")).strip()
                            desc = str(item.get("description", "")).strip()
                            if name:
                                cats.append({"name": name, "description": desc})
                        elif isinstance(item, str):
                            name = item.strip()
                            if name:
                                cats.append({"name": name, "description": ""})
                elif isinstance(cats_raw, str):
                    for name in [c.strip() for c in cats_raw.replace('，', ',').split(',') if c.strip()]:
                        cats.append({"name": name, "description": ""})
                conf = data.get("confidence")
                try:
                    conf = float(conf)
                except Exception:
                    conf = 0.0
                result = {"categories": cats[:6], "confidence": max(0.0, min(1.0, conf))}
                logger.info("分类完成")
                return result
            return {"categories": [], "confidence": 0.0}
        except Exception as e:
            logger.error(f"分类失败: {e}")
            return {"categories": [], "confidence": 0.0}

    def generate_tags(self, text: str) -> List[str]:
        """基于LLM打标签，返回有序标签列表"""
        try:
            if hasattr(self, 'client') and self.client:
                logger.info("开始打标签（LangUp）")
                prompt = PROMPTS["tags"].format(context=self._truncate(text))
                raw = self.client.complete_chat(prompt)
                try:
                    data = json.loads(raw) if isinstance(raw, str) else raw
                    tags = data.get("tags") or []
                    if isinstance(tags, str):
                        tags = [t.strip() for t in tags.replace('，', ',').split(',') if t.strip()]
                    if not isinstance(tags, list):
                        tags = []
                except Exception:
                    # 回退解析：按分隔符切分
                    s = str(raw)
                    tags = [t.strip() for t in s.replace('，', ',').split(',') if t.strip()]
                tags = [t for t in tags if 1 < len(t) <= 24][:20]
                logger.info("打标签完成")
                return tags
            return []
        except Exception as e:
            logger.error(f"打标签失败: {e}")
            return []
        try:
            prompt = PromptTemplate(template=PROMPTS["markdown"], input_variables=["context"])
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"context": text})
            return result.strip()
        except Exception as e:
            logger.error(f"转换为Markdown失败: {e}")
            return self._fallback_markdown(text)
    
    def analyze_content(self, text: str) -> Dict:
        """
        综合分析内容
        
        Args:
            text: 输入文本
            
        Returns:
            分析结果字典
        """
        try:
            result = {
                'summary': self.generate_summary(text),
                'keywords': self.extract_keywords(text),
                'hybrid_summary': self.generate_hybrid_summary(text),
                'markdown': self.convert_to_markdown(text)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"内容分析失败: {e}")
            return {
                'summary': '分析失败',
                'keywords': [],
                'hybrid_summary': '分析失败',
                'markdown': text
            }
    
    def _parse_keywords(self, text: str) -> List[str]:
        """解析关键词文本"""
        try:
            # 尝试从文本中提取关键词
            lines = text.strip().split('\n')
            keywords = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 移除序号和特殊字符
                    clean_line = line.replace('1.', '').replace('2.', '').replace('3.', '')
                    clean_line = clean_line.replace('-', '').replace('•', '').replace('*', '')
                    clean_line = clean_line.strip()
                    
                    if clean_line and len(clean_line) > 1:
                        keywords.append(clean_line)
            
            # 如果没有提取到关键词，返回空列表
            if not keywords:
                return []
            
            # 限制关键词数量
            return keywords[:10]
            
        except Exception as e:
            logger.error(f"解析关键词失败: {e}")
            return []
    
    def _fallback_summary(self, text: str) -> str:
        """摘要生成失败时的备用方案"""
        try:
            # 简单的文本截取
            if len(text) <= 200:
                return text
            
            # 取前200个字符作为摘要
            summary = text[:200].strip()
            if not summary.endswith('。') and not summary.endswith('.'):
                summary += '...'
            
            return summary
            
        except Exception:
            return "摘要生成失败"
    
    def _fallback_keywords(self, text: str) -> List[str]:
        """关键词提取失败时的备用方案"""
        try:
            # 简单的关键词提取（基于词频）
            import re
            from collections import Counter
            
            # 移除标点符号
            clean_text = re.sub(r'[^\w\s]', '', text)
            
            # 分词（简单按空格分割）
            words = clean_text.split()
            
            # 过滤短词
            words = [word for word in words if len(word) > 1]
            
            # 统计词频
            word_count = Counter(words)
            
            # 返回最常见的5个词
            return [word for word, _ in word_count.most_common(5)]
            
        except Exception:
            return []
    
    def _fallback_hybrid_summary(self, text: str) -> str:
        """混合摘要失败时的备用方案"""
        try:
            # 分段处理
            paragraphs = text.split('\n\n')
            if len(paragraphs) <= 3:
                return text
            
            # 取前3段
            summary = '\n\n'.join(paragraphs[:3])
            return summary
            
        except Exception:
            return "混合摘要生成失败"
    
    def _fallback_markdown(self, text: str) -> str:
        """Markdown转换失败时的备用方案"""
        try:
            # 简单的Markdown转换
            lines = text.split('\n')
            markdown_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 判断是否为标题（简单启发式）
                if len(line) < 50 and (line.endswith('：') or line.endswith(':') or line.isupper()):
                    markdown_lines.append(f"## {line}")
                else:
                    markdown_lines.append(line)
            
            return '\n\n'.join(markdown_lines)
            
        except Exception:
            return text
