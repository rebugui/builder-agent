"""
Async HTTP fetcher module for robots.txt retrieval.
Handles concurrent HTTP requests with proper error handling.
"""
import asyncio
import aiohttp
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse

from .models import RobotsResult, ScanConfig


class Fetcher:
    """Async HTTP client for fetching robots.txt files."""

    def __init__(self, config: ScanConfig):
        """
        Initialize fetcher with configuration.

        Args:
            config: ScanConfig instance with timeout and worker settings.
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "Fetcher":
        """Create aiohttp session on context entry."""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(
            limit=self.config.workers,
            limit_per_host=5,
            enable_cleanup_closed=True
        )
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                "User-Agent": "RobotsTxtScanner/1.0",
                "Accept": "text/plain,*/*"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close aiohttp session on context exit."""
        if self._session:
            await self._session.close()

    def _normalize_url(self, raw_url: str) -> str:
        """
        Normalize URL to ensure it has a valid scheme.

        Args:
            raw_url: Input URL string.

        Returns:
            Normalized URL with scheme.
        """
        raw_url = raw_url.strip()
        if not raw_url:
            raise ValueError("Empty URL provided")

        parsed = urlparse(raw_url)

        # Handle protocol-agnostic URLs
        if not parsed.scheme:
            # Default to HTTPS
            raw_url = f"https://{raw_url}"
            parsed = urlparse(raw_url)

        # Validate URL has a valid scheme
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid scheme: {parsed.scheme}")

        # Validate URL has a netloc (domain)
        if not parsed.netloc:
            raise ValueError(f"Invalid URL: missing domain")

        # Build base URL (scheme + netloc only)
        return urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))

    async def fetch_robots(self, url: str) -> RobotsResult:
        """
        Fetch robots.txt from a single URL.

        Args:
            url: Target URL to fetch robots.txt from.

        Returns:
            RobotsResult containing the fetch result.
        """
        result = RobotsResult(url=url)

        try:
            base_url = self._normalize_url(url)
            result.url = base_url
            robots_url = f"{base_url}/robots.txt"

            if not self._session:
                raise RuntimeError("Session not initialized. Use async context manager.")

            async with self._session.get(robots_url) as response:
                result.status_code = response.status
                result.content_length = response.content_length

                if response.status == 200:
                    raw_content = await response.text()
                    result.raw_content = raw_content
                    if result.content_length is None:
                        result.content_length = len(raw_content.encode('utf-8'))
                elif response.status in (404, 403, 410):
                    result.error = f"HTTP {response.status}"
                else:
                    result.error = f"HTTP {response.status}"

        except aiohttp.ClientConnectorError as e:
            result.error = f"Connection Error: {str(e)}"
        except aiohttp.ClientTimeout:
            result.error = "Connection Timeout"
        except asyncio.TimeoutError:
            result.error = "Connection Timeout"
        except aiohttp.TooManyRedirects:
            result.error = "Too Many Redirects"
        except aiohttp.ClientError as e:
            result.error = f"Client Error: {str(e)}"
        except ValueError as e:
            result.error = f"Invalid URL: {str(e)}"
        except Exception as e:
            result.error = f"Unexpected Error: {str(e)}"

        return result
