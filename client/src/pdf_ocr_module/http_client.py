"""
LangUp API 客户端封装：
- 登录获取 token（明文密码直传）
- 统一签名与公共请求头（application/json;charset=UTF-8）
- 提供 complete_chat(prompt) 能力
"""

import base64
import hashlib
import hmac
import json
import random
import string
import time
from typing import Any, Dict, Optional

import httpx
from loguru import logger


class LangUpAPIClient:
    def __init__(self, 
                 login_url: str,
                 chat_url: str,
                 account: str,
                 password: str,
                 access_key: Optional[str] = None,
                 access_secret: Optional[str] = None,
                 timeout: int = 60):
        self.login_url = login_url
        self.chat_url = chat_url
        self.account = account
        self.password = password
        # 允许通过专用 access_key/secret 配置；若未提供，则回退为账号/密码
        self.access_key = access_key or account
        self.access_secret = (access_secret or password).encode("utf-8")
        self.timeout = timeout

        self._token: Optional[str] = None
        self._client = httpx.Client(timeout=self.timeout)
        self._last_login_response: Optional[Dict[str, Any]] = None

    def _nonce(self, length: int = 6) -> str:
        return ''.join(random.choices(string.digits, k=length))

    def _build_sign(self, method: str, url_path: str, access_key: str, timestamp: str, nonce: str) -> str:
        method_upper = method.upper()
        sign_str = f"{method_upper}&{url_path}&{access_key}&{timestamp}&{nonce}"
        digest = hmac.new(self.access_secret, sign_str.encode("utf-8"), hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    def _headers(self, method: str, url_path: str, with_auth: bool = True) -> Dict[str, str]:
        timestamp = str(int(time.time()))
        nonce = self._nonce()
        sign = self._build_sign(method, url_path, self.access_key, timestamp, nonce)

        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "accessKey": self.access_key,
            "timestamp": timestamp,
            "nonce": nonce,
            "sign": sign,
        }
        if with_auth and self._token:
            headers["authorization"] = f"Bearer {self._token}"
        return headers

    # 已移除密码加密与预处理相关方法（SM2/SM3 等），登录使用明文直传

    def login(self) -> bool:
        try:
            url_path = "/api/sysAuth/login" if "/api/sysAuth/login" in self.login_url else "/api/sysAuth/NoLogin"
            headers = self._headers("POST", url_path, with_auth=False)
            # 登录接口要求特殊的 Content-Type
            headers["Content-Type"] = "application/json-patch+json"

            def post_with() -> Dict[str, Any]:
                payload = {"account": self.account, "password": self.password}
                # 合并额外登录参数
                try:
                    from .config import LLM_CONFIG
                    extra = LLM_CONFIG.get("login_extra") or {}
                except Exception:
                    extra = {}
                if isinstance(extra, dict):
                    payload.update(extra)
                # 调试输出
                try:
                    logger.debug(f"login method: POST, url_path: {url_path}, full_url: {self.login_url}")
                    logger.debug(f"login headers: {headers}")
                    logger.debug(f"login payload: {payload}")
                except Exception:
                    pass
                r = self._client.post(self.login_url, headers=headers, json=payload)
                r.raise_for_status()
                return r.json()

            data = post_with()
            self._last_login_response = data if isinstance(data, dict) else {"raw": data}

            # 兼容多种返回格式
            token = None
            if isinstance(data, dict):
                token = data.get("token") or data.get("accessToken")
                if not token and isinstance(data.get("data"), dict):
                    token = data["data"].get("token") or data["data"].get("accessToken")
                if not token and isinstance(data.get("result"), dict):
                    token = data["result"].get("token") or data["result"].get("accessToken")
            if not token:
                logger.error(f"登录响应中未找到token字段: {data}")
                return False

            self._token = token
            logger.info("LangUp 登录成功")
            return True
        except Exception as e:
            logger.error(f"LangUp 登录失败: {e}")
            return False

    def get_last_login_response(self) -> Optional[Dict[str, Any]]:
        return self._last_login_response

    def post_json(self, full_url: str, url_path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
        if not self._token:
            if not self.login():
                return {"status": "error", "message": "登录失败，无法获取token"}
        try:
            headers = self._headers("POST", url_path, with_auth=True)
            resp = self._client.post(full_url, headers=headers, json=json_body)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"POST {url_path} 调用失败: {e}")
            return {"status": "error", "message": str(e)}

    def complete_chat(self, prompt: str) -> str:
        url_path = "/api/chat/completeChat"
        result = self.post_json(self.chat_url, url_path, {"prompt": prompt})
        # 兼容多种返回结构，尝试提取文本
        if isinstance(result, dict):
            # 优先解析新LLM结构: { code, result: { choices: [ { message: { content } } ] } }
            try:
                inner = result.get("result") or {}
                if isinstance(inner, dict):
                    choices = inner.get("choices")
                    if isinstance(choices, list) and choices:
                        msg = choices[0].get("message") if isinstance(choices[0], dict) else None
                        content = (msg or {}).get("content") if isinstance(msg, dict) else None
                        if isinstance(content, str) and content.strip():
                            return content.strip()
                    # 其他常见字段
                    for key in ("content", "text", "message", "result"):
                        val = inner.get(key)
                        if isinstance(val, str) and val.strip():
                            return val.strip()
            except Exception:
                pass

            # 兼容旧结构: { data: { content: "..." } } 或顶层直接 content/text
            data = result.get("data") if isinstance(result.get("data"), (dict, str)) else result
            if isinstance(data, dict):
                content = data.get("content") or data.get("text")
                if isinstance(content, str) and content.strip():
                    return content.strip()
            for key in ("content", "text", "message"):
                val = result.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()
        # 最后回退为原始JSON字符串
        try:
            return json.dumps(result, ensure_ascii=False)
        except Exception:
            return str(result)


