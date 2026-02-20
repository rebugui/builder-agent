"""pytest 설정 및 공통 픽스처"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock


@pytest.fixture
def sample_robots_content():
    """테스트용 robots.txt 샘플 콘텐츠"""
    return """User-agent: *
Disallow: /admin/
Disallow: /private/
Allow: /public/
Crawl-delay: 10

User-agent: Googlebot
Disallow: /secret/
Allow: /

Sitemap: https://example.com/sitemap.xml
"""


@pytest.fixture
def sample_urls():
    """테스트용 URL 목록"""
    return [
        "https://example.com",
        "https://test.org",
        "http://sample.net"
    ]


@pytest.fixture
def event_loop():
    """비동기 테스트용 이벤트 루프"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
