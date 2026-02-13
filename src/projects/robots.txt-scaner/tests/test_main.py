import pytest
import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from io import StringIO

# Adjust path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import read_urls, write_results
from src.scanner import RobotsScanner, RobotsParser, CacheManager

@pytest.fixture
def sample_urls_file(tmp_path):
    """Fixture to create a temporary file with URLs."""
    file_path = tmp_path / "urls.txt"
    content = "https://example.com\nhttps://google.com\n# Comment\nhttps://github.com"
    file_path.write_text(content)
    return file_path

class TestInputOutput:
    def test_read_urls_from_file(self, sample_urls_file):
        urls = read_urls(str(sample_urls_file))
        assert len(urls) == 3
        assert "https://example.com" in urls
        assert "# Comment" not in urls

    def test_read_urls_from_stdin(self):
        dummy_input = StringIO("https://test.com\nhttps://dev.com\n")
        urls = read_urls(dummy_input)
        assert len(urls) == 2
        assert urls[0] == "https://test.com"

    def test_write_results(self, tmp_path):
        results = [{"url": "https://example.com", "status": 200}]
        output_path = tmp_path / "output.json"
        write_results(results, str(output_path))
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data == results

class TestRobotsParser:
    def test_parse_basic_rules(self):
        content = """
        User-agent: *
        Disallow: /admin
        Allow: /
        
        User-agent: Googlebot
        Disallow: /private
        Sitemap: https://example.com/sitemap.xml
        """
        parsed = RobotsParser.parse(content)
        
        assert "https://example.com/sitemap.xml" in parsed['sitemap_urls']
        assert len(parsed['rules']) == 2
        
        rule_star = next(r for r in parsed['rules'] if r['user_agent'] == '*')
        assert '/admin' in rule_star['disallow']
        assert '/' in rule_star['allow']
        
        rule_google = next(r for r in parsed['rules'] if r['user_agent'] == 'Googlebot')
        assert '/private' in rule_google['disallow']

class TestScannerLogic:
    @pytest.mark.asyncio
    async def test_scan_single_url_success(self):
        # Mocking aiohttp session response
        with patch('src.scanner.aiohttp.ClientSession') as MockSession:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {'Content-Length': '100'}
            mock_response.text = AsyncMock(return_value="User-agent: *\nDisallow: /")
            mock_response.reason = "OK"
            
            mock_session = AsyncMock()
            mock_session.get = MagicMock(return_value=mock_response.__aenter__.return_value)
            mock_session.closed = False
            
            MockSession.return_value = mock_session

            # Mock Cache to avoid DB ops during unit test
            with patch.object(RobotsScanner, '__init__', lambda self, concurrency, timeout, user_agent: None):
                scanner = RobotsScanner(concurrency=10, timeout=5, user_agent="Test")
                scanner.cache = MagicMock()
                scanner.cache.get = MagicMock(return_value=None)
                scanner.session = mock_session
                
                result = await scanner.scan_single_url("https://example.com")
                
                assert result['status_code'] == 200
                assert len(result['rules']) == 1
                assert result['rules'][0]['user_agent'] == '*'
                assert result['target_url'] == "https://example.com"

    @pytest.mark.asyncio
    async def test_scan_single_url_invalid(self):
        with patch('src.scanner.aiohttp.ClientSession'):
            with patch.object(RobotsScanner, '__init__', lambda self, concurrency, timeout, user_agent: None):
                scanner = RobotsScanner(concurrency=10, timeout=5, user_agent="Test")
                scanner.cache = MagicMock()
                scanner.session = MagicMock()
                
                result = await scanner.scan_single_url("not-a-valid-url")
                
                assert result['status_code'] == 0
                assert "Invalid URL" in result['error']