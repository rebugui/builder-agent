"""
Unit tests for robots.txt Scanner.
Focuses on URL normalization and parsing logic.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure src is in path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scanner import normalize_url, RobotsParser


class TestUrlNormalization:
    """Tests for URL normalization logic."""

    def test_normalize_valid_url(self):
        """Test normalization of a valid HTTPS URL."""
        url = "https://example.com/page1"
        assert normalize_url(url) == "example.com"

    def test_normalize_valid_http_url(self):
        """Test normalization of a valid HTTP URL."""
        url = "http://test-site.com"
        assert normalize_url(url) == "test-site.com"

    def test_normalize_url_without_scheme(self):
        """Test normalization when scheme is missing."""
        url = "sub.domain.com/path"
        assert normalize_url(url) == "sub.domain.com"

    def test_normalize_invalid_url(self):
        """Test normalization of a malformed URL."""
        assert normalize_url("") is None
        # urlparse might parse "ftp://" differently, but for http/https context:
        # We rely on urlparse inside normalize_url
        assert normalize_url("ht tp://bad") is None


class TestRobotsParser:
    """Tests for the RobotsParser logic."""

    def test_parse_basic_rules(self):
        """Test parsing basic Allow/Disallow rules."""
        content = """
        User-agent: *
        Disallow: /admin
        Allow: /public
        """
        parser = RobotsParser(content)
        result = parser.parse()
        
        assert "*" in result["user_agents"]
        assert "/admin" in result["disallows"]
        assert "/public" in result["allows"]

    def test_parse_crawl_delay(self):
        """Test parsing Crawl-delay directive."""
        content = "Crawl-delay: 5.5"
        parser = RobotsParser(content)
        result = parser.parse()
        
        assert result["crawl_delay"] == 5.5

    def test_parse_sitemap(self):
        """Test parsing Sitemap directive."""
        content = "Sitemap: https://example.com/sitemap.xml"
        parser = RobotsParser(content)
        result = parser.parse()
        
        assert result["sitemap"] == "https://example.com/sitemap.xml"

    def test_parse_comments_and_empty_lines(self):
        """Test that comments and empty lines are ignored."""
        content = """
        # This is a comment
        
        User-agent: bot
        
        """
        parser = RobotsParser(content)
        result = parser.parse()
        
        assert "bot" in result["user_agents"]
        assert "#" not in result["user_agents"]


class TestRobotsFetcher:
    """Tests for RobotsFetcher (Async)."""

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Test successful fetch and parsing."""
        # Mocking aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="User-agent: *\nDisallow: /")
        mock_response.reason = "OK"

        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        fetcher = RobotsFetcher(mock_session, timeout=10)
        result = await fetcher.fetch("example.com")

        assert result["status"] == 200
        assert result["content_found"] is True
        assert result["parsed_rules"] is not None
        assert "/" in result["parsed_rules"]["disallows"]
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_fetch_404(self):
        """Test handling of 404 errors."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.reason = "Not Found"

        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        fetcher = RobotsFetcher(mock_session, timeout=10)
        result = await fetcher.fetch("example.com")

        assert result["status"] == 404
        assert result["content_found"] is False
        assert "404" in result["error"]


if __name__ == "__main__":
    pytest.main()