"""Asynchronous HTTP client for fetching robots.txt."""
import asyncio
import aiohttp
from typing import Tuple, Optional
from urllib.parse import urljoin, urlparse
from .parser import RobotsParser
from .models import ScanResultModel


class Fetcher:
    """Handles HTTP requests with security and error handling."""
    
    def __init__(self, timeout: int = 10, user_agent: str = "RobotsScanner/1.0"):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.headers = {"User-Agent": user_agent}

    def _validate_url(self, url: str) -> bool:
        """Basic input validation for URL structure."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    async def fetch(self, session: aiohttp.ClientSession, target_url: str) -> ScanResultModel:
        """
        Fetches and parses a single robots.txt.
        Returns a ScanResultModel.
        """
        # Security: Input Validation
        if not self._validate_url(target_url):
            return ScanResultModel(
                input_url=target_url,
                robots_url="",
                status="error",
                error="Invalid URL format"
            )

        robots_url = urljoin(target_url, '/robots.txt')
        
        try:
            async with session.get(robots_url, headers=self.headers, timeout=self.timeout) as response:
                # Read content only if status is OK or redirect was handled
                content = await response.text()
                
                status_code = response.status
                if status_code == 200:
                    parser = RobotsParser(content)
                    rules, sitemaps = parser.parse()
                    
                    return ScanResultModel(
                        input_url=target_url,
                        robots_url=str(response.url), # Use final URL after redirects
                        status="success",
                        status_code=status_code,
                        rules=rules,
                        sitemaps=sitemaps
                    )
                else:
                    # Handle 404, 500, etc.
                    status_str = "not_found" if status_code == 404 else "error"
                    return ScanResultModel(
                        input_url=target_url,
                        robots_url=str(response.url),
                        status=status_str,
                        status_code=status_code,
                        rules=[],
                        error=f"HTTP {status_code}"
                    )

        except asyncio.TimeoutError:
            return ScanResultModel(
                input_url=target_url,
                robots_url=robots_url,
                status="timeout",
                error="Connection timed out"
            )
        except aiohttp.ClientError as e:
            # Handle connection errors, DNS issues, etc.
            return ScanResultModel(
                input_url=target_url,
                robots_url=robots_url,
                status="error",
                error=str(e)
            )
        except Exception as e:
            # Catch-all for unexpected errors (Security: prevent crashing)
            return ScanResultModel(
                input_url=target_url,
                robots_url=robots_url,
                status="error",
                error=f"Unexpected error: {str(e)}"
            )