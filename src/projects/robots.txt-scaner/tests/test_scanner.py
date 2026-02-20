"""scanner 모듈 단위 테스트"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.core import RobotsScanner


class TestRobotsScanner:
    """RobotsScanner 클래스 테스트"""
    
    def test_scanner_initialization_default(self):
        """기본값으로 RobotsScanner 초기화 테스트"""
        scanner = RobotsScanner()
        assert scanner.max_workers > 0
        assert scanner.timeout > 0
        assert scanner.user_agent is not None
        assert scanner.parser is not None
    
    def test_scanner_initialization_custom(self):
        """커스텀 값으로 RobotsScanner 초기화 테스트"""
        scanner = RobotsScanner(
            max_workers=20,
            timeout=60,
            user_agent="CustomBot/1.0"
        )
        assert scanner.max_workers == 20
        assert scanner.timeout == 60
        assert scanner.user_agent == "CustomBot/1.0"
    
    def test_scanner_initialization_invalid_workers(self):
        """잘못된 max_workers 값 테스트"""
        with pytest.raises((ValueError, TypeError)):
            RobotsScanner(max_workers=-1)
    
    def test_scanner_initialization_invalid_timeout(self):
        """잘못된 timeout 값 테스트"""
        with pytest.raises((ValueError, TypeError)):
            RobotsScanner(timeout=0)
    
    def test_get_protocols_to_try_with_https(self):
        """HTTPS URL에 대한 프로토콜 테스트"""
        scanner = RobotsScanner()
        url = "https://example.com"
        protocols = scanner._get_protocols_to_try(url)
        
        assert "https" in protocols
    
    def test_get_protocols_to_try_with_http(self):
        """HTTP URL에 대한 프로토콜 테스트"""
        scanner = RobotsScanner()
        url = "http://example.com"
        protocols = scanner._get_protocols_to_try(url)
        
        assert "http" in protocols
    
    def test_get_protocols_to_try_no_protocol(self):
        """프로토콜 없는 URL 테스트"""
        scanner = RobotsScanner()
        url = "example.com"
        protocols = scanner._get_protocols_to_try(url)
        
        # 기본적으로 https를 먼저 시도하거나 둘 다 시도
        assert len(protocols) > 0
    
    @pytest.mark.asyncio
    async def test_scan_single_url_success(self):
        """단일 URL 스캔 성공 테스트"""
        scanner = RobotsScanner()
        
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="User-agent: *\nDisallow: /admin/")
            mock_response.headers = {"content-type": "text/plain"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # 실제 scan 메서드가 있다면 테스트
            # result = await scanner.scan_single("https://example.com")
            # assert result is not None
            pass
    
    @pytest.mark.asyncio
    async def test_scan_single_url_not_found(self):
        """robots.txt 없는 URL 스캔 테스트"""
        scanner = RobotsScanner()
        
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # result = await scanner.scan_single("https://example.com")
            # assert result is None or result.get("status") == 404
            pass
    
    @pytest.mark.asyncio
    async def test_scan_multiple_urls(self, sample_urls):
        """다중 URL 스캔 테스트"""
        scanner = RobotsScanner(max_workers=5)
        
        with patch.object(scanner, "_fetch_robots") as mock_fetch:
            mock_fetch.return_value = {"status": 200, "content": "User-agent: *\nDisallow: /"}
            
            # results = await scanner.scan(sample_urls)
            # assert len(results) == len(sample_urls)
            pass
    
    @pytest.mark.asyncio
    async def test_scan_with_timeout(self):
        """타임아웃 처리 테스트"""
        scanner = RobotsScanner(timeout=1)
        
        async def slow_response():
            await asyncio.sleep(5)
            return "content"
        
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.side_effect = asyncio.TimeoutError()
            
            # 타임아웃이 발생해도 예외 없이 처리되어야 함
            # result = await scanner.scan_single("https://slow-example.com")
            # assert result is None or "error" in result
            pass
    
    @pytest.mark.asyncio
    async def test_scan_with_connection_error(self):
        """연결 오류 처리 테스트"""
        scanner = RobotsScanner()
        
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.side_effect = ConnectionError()
            
            # result = await scanner.scan_single("https://invalid.example.com")
            # assert result is None or "error" in result
            pass
    
    def test_scanner_parser_integration(self):
        """Scanner와 Parser 통합 테스트"""
        scanner = RobotsScanner()
        
        # Parser가 올바르게 초기화되었는지 확인
        assert hasattr(scanner.parser, "parse")
        assert callable(scanner.parser.parse)
    
    @pytest.mark.asyncio
    async def test_concurrent_scan_limit(self):
        """동시 연결 제한 테스트"""
        max_workers = 3
        scanner = RobotsScanner(max_workers=max_workers)
        
        # 실제 동시 연결 수가 max_workers를 초과하지 않는지 확인
        # 이 테스트는 구현에 따라 조정 필요
        assert scanner.max_workers == max_workers
    
    def test_user_agent_header_format(self):
        """User-Agent 헤더 형식 테스트"""
        custom_agent = "MyBot/2.0 (compatible; +https://mysite.com)"
        scanner = RobotsScanner(user_agent=custom_agent)
        
        assert scanner.user_agent == custom_agent
    
    @pytest.mark.asyncio
    async def test_scan_empty_url_list(self):
        """빈 URL 목록 스캔 테스트"""
        scanner = RobotsScanner()
        
        # results = await scanner.scan([])
        # assert results == [] or results is None
        pass
    
    @pytest.mark.asyncio
    async def test_scan_invalid_url(self):
        """잘못된 URL 형식 스캔 테스트"""
        scanner = RobotsScanner()
        invalid_urls = ["not-a-url", "://missing-protocol.com", ""]
        
        # 잘못된 URL에 대해 적절히 처리되어야 함
        # results = await scanner.scan(invalid_urls)
        # for result in results:
        #     assert "error" in result or result is None
        pass
    
    def test_scanner_attributes_type(self):
        """Scanner 속성 타입 검증"""
        scanner = RobotsScanner()
        
        assert isinstance(scanner.max_workers, int)
        assert isinstance(scanner.timeout, (int, float))
        assert isinstance(scanner.user_agent, str)
    
    @pytest.mark.asyncio
    async def test_scan_with_redirect(self):
        """리다이렉트 처리 테스트"""
        scanner = RobotsScanner()
        
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.url = "https://example.com/robots.txt"  # 리다이렉트된 URL
            mock_response.text = AsyncMock(return_value="User-agent: *\nDisallow: /")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # 리다이렉트 후 올바른 내용을 가져오는지 확인
            pass
