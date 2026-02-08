"""
Async LLM Client Module
aiohttp를 사용하여 비동기로 LLM API를 호출합니다.
"""

import aiohttp
import asyncio
from typing import Dict, Optional, Any
from modules.intelligence.config import GLM_API_KEY, GLM_BASE_URL, GLM_MODEL
from modules.intelligence.utils import setup_logger

logger = setup_logger(__name__, "llm_client_async.log")

class AsyncLLMClient:
    """비동기 GLM API 클라이언트"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or GLM_API_KEY
        self.base_url = base_url or GLM_BASE_URL
        self.model = model or GLM_MODEL
        self.timeout = 300  # 5분

        if not self.api_key:
            logger.warning("GLM_API_KEY is not set.")

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """GLM API 비동기 호출"""
        if not self.api_key:
            raise ValueError("API Key가 설정되지 않았습니다.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 8000
        }

        url = self.base_url.rstrip('/') + "/chat/completions"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=payload, timeout=self.timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"GLM API Error {response.status}: {error_text}")
                        response.raise_for_status()
                    
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]

            except asyncio.TimeoutError:
                logger.error(f"GLM API Timeout ({self.timeout}s)")
                raise Exception(f"GLM API 요청 타임아웃 ({self.timeout}초 초과)")
            except Exception as e:
                logger.error(f"GLM API Request Failed: {e}")
                raise

# 동기 호환성을 위한 래퍼 (필요 시 사용)
# client = AsyncLLMClient()
# result = asyncio.run(client.chat(...))
