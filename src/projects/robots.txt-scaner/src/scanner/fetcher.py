"""HTTP 요청 로직 - aiohttp 래퍼"""
import asyncio
from dataclasses import dataclass
from typing import Optional

import aiohttp


@dataclass
class FetchResponse:
    """HTTP 응답 데이터"""
    status: int
    body: Optional[str]
    headers: dict
    url: str


class Fetcher:
    """비동기 HTTP 요청 처리기"""
    
    def __init__(
        self,
        timeout: int = 10,
        user_agent: str = "RobotsScanner/1.0",
        max_redirects: int = 5
    ):
        """
        Fetcher 초기화.
        
        Args:
            timeout: 요청 타임아웃 (초)
            user_agent: User-Agent 헤더
            max_redirects: 최대 리다이렉트 횟수
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.user_agent = user_agent
        self.max_redirects = max_redirects
        
        # 보안 헤더 설정
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'text/plain,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
    
    async def fetch(self, url: str) -> FetchResponse:
        """
        URL에서 데이터 가져오기.
        
        Args:
            url: 요청할 URL
        
        Returns:
            FetchResponse 객체
        
        Raises:
            asyncio.TimeoutError: 요청 타임아웃
            aiohttp.ClientError: HTTP 클라이언트 오류
        """
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            ttl_dns_cache=300,
            ssl=False  # SSL 검증 비활성화 (필요시 활성화)
        )
        
        async with aiohttp.ClientSession(
            connector=connector,
            headers=self.headers,
            timeout=self.timeout,
            auto_decompress=True
        ) as session:
            try:
                async with session.get(
                    url,
                    allow_redirects=True,
                    max_redirects=self.max_redirects
                ) as response:
                    body = None
                    if response.status == 200:
                        # 응답 본문 크기 제한 (보안: 메모리 보호)
                        max_size = 1024 * 1024  # 1MB
                        body = await response.text()
                        
                        if len(body) > max_size:
                            body = body[:max_size]
                    
                    return FetchResponse(
                        status=response.status,
                        body=body,
                        headers=dict(response.headers),
                        url=str(response.url)
                    )
            
            except asyncio.TimeoutError:
                raise
            except aiohttp.ClientError as e:
                raise aiohttp.ClientError(f"HTTP request failed: {str(e)}")
    
    async def fetch_batch(
        self,
        urls: list,
        concurrency: int = 50
    ) -> list:
        """
        여러 URL 동시 요청.
        
        Args:
            urls: URL 리스트
            concurrency: 동시 요청 수
        
        Returns:
            FetchResponse 리스트
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def _fetch_with_semaphore(url: str) -> FetchResponse:
            async with semaphore:
                return await self.fetch(url)
        
        tasks = [_fetch_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
