"""핵심 기능 구현 - AsyncIO 오케스트레이션"""
import asyncio
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from tqdm import tqdm

from .scanner.fetcher import Fetcher
from .scanner.parser import RobotsParser
from .scanner.models import ScanResult
from .utils.file_reader import FileReader


@dataclass
class ScanConfig:
    """스캔 설정 데이터클래스"""
    input_file: str
    output_file: str = "output.json"
    workers: int = 50
    timeout: int = 10
    delay: float = 0.0
    user_agent: str = "RobotsScanner/1.0"
    filter_agent: Optional[str] = None
    verbose: bool = False


class URLValidator:
    """URL 검증 유틸리티"""
    
    # URL 패턴 (보안적으로 검증된 정규식)
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// 또는 https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 도메인
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP 주소
        r'(?::\d+)?'  # 선택적 포트
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    @classmethod
    def validate(cls, url: str) -> bool:
        """
        URL 형식 검증.
        
        Args:
            url: 검증할 URL 문자열
        
        Returns:
            유효성 여부
        """
        if not url or not isinstance(url, str):
            return False
        
        url = url.strip()
        
        # 길이 제한 (보안: 매우 긴 URL 차단)
        if len(url) > 2048:
            return False
        
        # 패턴 매칭
        if not cls.URL_PATTERN.match(url):
            return False
        
        # 프로토콜 확인 (http/https만 허용)
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        
        return True
    
    @classmethod
    def normalize(cls, url: str) -> str:
        """
        URL 정규화 (후행 슬래시 처리).
        
        Args:
            url: 정규화할 URL
        
        Returns:
            정규화된 URL
        """
        url = url.strip()
        if not url.endswith('/'):
            url += '/'
        return url


class RobotsScanner:
    """Robots.txt 스캐너 메인 클래스"""
    
    def __init__(self, config: ScanConfig, logger: Any):
        """
        스캐너 초기화.
        
        Args:
            config: 스캔 설정
            logger: 로거 인스턴스
        """
        self.config = config
        self.logger = logger
        self.fetcher = Fetcher(
            timeout=config.timeout,
            user_agent=config.user_agent
        )
        self.parser = RobotsParser(filter_agent=config.filter_agent)
        self.results: List[ScanResult] = []
        self._stop_event = asyncio.Event()
    
    def _read_urls(self) -> List[str]:
        """
        입력 파일에서 URL 목록 읽기.
        
        Returns:
            URL 리스트
        
        Raises:
            FileNotFoundError: 입력 파일이 존재하지 않음
            ValueError: 유효한 URL이 없음
        """
        file_reader = FileReader(self.config.input_file)
        raw_urls = file_reader.read_lines()
        
        # URL 검증 및 정규화
        valid_urls = []
        invalid_count = 0
        
        for url in raw_urls:
            url = url.strip()
            if not url or url.startswith('#'):
                continue
            
            if URLValidator.validate(url):
                valid_urls.append(URLValidator.normalize(url))
            else:
                invalid_count += 1
                if self.config.verbose:
                    self.logger.warning(f"Invalid URL skipped: {url}")
        
        if invalid_count > 0:
            self.logger.warning(f"Skipped {invalid_count} invalid URLs")
        
        if not valid_urls:
            raise ValueError("No valid URLs found in input file")
        
        self.logger.info(f"Loaded {len(valid_urls)} valid URLs")
        return valid_urls
    
    async def _scan_single(self, url: str, pbar: tqdm) -> ScanResult:
        """
        단일 URL 스캔.
        
        Args:
            url: 스캔할 기본 URL
            pbar: 진행률 표시줄
        
        Returns:
            스캔 결과
        """
        robots_url = urljoin(url, '/robots.txt')
        
        try:
            # 요청 지연 적용
            if self.config.delay > 0:
                await asyncio.sleep(self.config.delay)
            
            # robots.txt 가져오기
            response = await self.fetcher.fetch(robots_url)
            
            if response.status == 200 and response.body:
                # 파싱 수행
                parsed_rules = self.parser.parse(response.body)
                
                return ScanResult(
                    url=url.rstrip('/'),
                    robots_url=robots_url,
                    status=response.status,
                    content_length=len(response.body),
                    rules=parsed_rules,
                    raw_content=response.body,
                    error=None
                )
            else:
                return ScanResult(
                    url=url.rstrip('/'),
                    robots_url=robots_url,
                    status=response.status,
                    content_length=0,
                    rules=None,
                    raw_content=None,
                    error=self._get_error_message(response.status)
                )
        
        except asyncio.TimeoutError:
            return ScanResult(
                url=url.rstrip('/'),
                robots_url=robots_url,
                status=None,
                content_length=0,
                rules=None,
                raw_content=None,
                error="Connection Timeout"
            )
        except Exception as e:
            error_msg = str(e)
            # 보안: 민감한 정보 노출 방지
            if "certificate" in error_msg.lower():
                error_msg = "SSL Certificate Error"
            elif "connection" in error_msg.lower():
                error_msg = "Connection Error"
            
            return ScanResult(
                url=url.rstrip('/'),
                robots_url=robots_url,
                status=None,
                content_length=0,
                rules=None,
                raw_content=None,
                error=error_msg
            )
        finally:
            pbar.update(1)
    
    def _get_error_message(self, status: Optional[int]) -> str:
        """
        HTTP 상태 코드에 대한 에러 메시지 반환.
        
        Args:
            status: HTTP 상태 코드
        
        Returns:
            에러 메시지
        """
        error_messages = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "No robots.txt found",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        return error_messages.get(status, f"HTTP Error {status}")
    
    async def _worker(
        self,
        queue: asyncio.Queue,
        pbar: tqdm
    ) -> None:
        """
        워커 코루틴.
        
        Args:
            queue: URL 큐
            pbar: 진행률 표시줄
        """
        while not self._stop_event.is_set():
            try:
                url = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            
            try:
                result = await self._scan_single(url, pbar)
                self.results.append(result)
            except Exception as e:
                self.logger.error(f"Worker error for {url}: {e}")
            finally:
                queue.task_done()
    
    async def _run_async(self, urls: List[str]) -> List[ScanResult]:
        """
        비동기 스캔 실행.
        
        Args:
            urls: 스캔할 URL 리스트
        
        Returns:
            스캔 결과 리스트
        """
        queue: asyncio.Queue = asyncio.Queue()
        
        # 큐에 URL 추가
        for url in urls:
            await queue.put(url)
        
        total = len(urls)
        
        # 진행률 표시줄과 함께 워커 실행
        with tqdm(
            total=total,
            desc="Scanning",
            unit="url",
            disable=self.config.verbose
        ) as pbar:
            workers = [
                asyncio.create_task(self._worker(queue, pbar))
                for _ in range(min(self.config.workers, total))
            ]
            
            await asyncio.gather(*workers)
        
        return self.results
    
    def _save_results(self, results: List[ScanResult]) -> None:
        """
        결과를 JSON 파일로 저장.
        
        Args:
            results: 스캔 결과 리스트
        """
        output_path = Path(self.config.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 결과를 딕셔너리 리스트로 변환
        output_data = [r.to_dict() for r in results]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Results saved to {output_path}")
    
    def run(self) -> List[ScanResult]:
        """
        스캔 실행 (동기 진입점).
        
        Returns:
            스캔 결과 리스트
        
        Raises:
            FileNotFoundError: 입력 파일 없음
            ValueError: 유효한 URL 없음
        """
        self.logger.info(f"Starting robots.txt scan with {self.config.workers} workers")
        
        # URL 읽기
        urls = self._read_urls()
        
        # 비동기 스캔 실행
        results = asyncio.run(self._run_async(urls))
        
        # 결과 저장
        self._save_results(results)
        
        # 통계 출력
        success_count = sum(1 for r in results if r.status == 200)
        error_count = sum(1 for r in results if r.error)
        
        self.logger.info(
            f"Scan completed: {success_count} success, "
            f"{len(results) - success_count - error_count} other, "
            f"{error_count} errors"
        )
        
        return results
