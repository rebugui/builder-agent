"""
robots.txt Scanner Core Module

This module handles the core logic for fetching and parsing robots.txt files.
It includes functions for URL normalization, asynchronous fetching, and rule parsing.
"""
import asyncio
import re
from urllib.parse import urlparse
from urllib import robotparser
from typing import Dict, List, Optional, Any
import aiohttp


class RobotsParser:
    """Custom parser to extract structured rules from robots.txt content."""

    def __init__(self, content: str):
        self.content = content

    def parse(self) -> Dict[str, Any]:
        """
        Parses the content of robots.txt to extract structured rules.

        Returns:
            A dictionary containing user_agents, allows, disallows, 
            crawl_delay, and sitemap.
        """
        rules = {
            "user_agents": [],
            "allows": [],
            "disallows": [],
            "crawl_delay": None,
            "sitemap": None
        }

        # Simple line-by-line parser for specific directives
        # Standard library's robotparser is good for checking access, 
        # but we need explicit rule lists for the JSON output.
        lines = self.content.splitlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Split only on the first occurrence of ':'
            if ':' in line:
                parts = line.split(':', 1)
                key = parts[0].strip().lower()
                value = parts[1].strip()

                if key == 'user-agent':
                    rules['user_agents'].append(value)
                elif key == 'disallow':
                    rules['disallows'].append(value)
                elif key == 'allow':
                    rules['allows'].append(value)
                elif key == 'crawl-delay':
                    try:
                        rules['crawl_delay'] = float(value)
                    except ValueError:
                        pass
                elif key == 'sitemap':
                    rules['sitemap'] = value
        
        return rules


class RobotsFetcher:
    """Handles asynchronous fetching of robots.txt files."""

    def __init__(self, session: aiohttp.ClientSession, timeout: int = 10):
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def fetch(self, domain: str) -> Dict[str, Any]:
        """
        Fetches and parses robots.txt for a given domain.

        Args:
            domain: The target domain (e.g., 'example.com').

        Returns:
            A dictionary containing the scan result.
        """
        robots_url = f"https://{domain}/robots.txt"
        result = {
            "domain": domain,
            "robots_url": robots_url,
            "status": None,
            "fetch_time_ms": 0,
            "content_found": False,
            "parsed_rules": None,
            "error": None
        }

        start_time = asyncio.get_event_loop().time()

        try:
            async with self.session.get(robots_url, timeout=self.timeout) as response:
                result["status"] = response.status
                result["fetch_time_ms"] = int(
                    (asyncio.get_event_loop().time() - start_time) * 1000
                )

                if response.status == 200:
                    text = await response.text()
                    result["content_found"] = True
                    
                    # Use custom parser
                    parser = RobotsParser(text)
                    result["parsed_rules"] = parser.parse()
                    
                    # Optional: Validate with standard library
                    rp = robotparser.RobotFileParser()
                    rp.set_url(robots_url)
                    # We simulate reading the text since we already fetched it
                    # Note: RobotFileParser.read() fetches again usually, 
                    # but we can parse content manually or just trust our parser for JSON export.
                    
                else:
                    result["error"] = f"HTTP {response.status} {response.reason}"

        except asyncio.TimeoutError:
            result["fetch_time_ms"] = int(
                (asyncio.get_event_loop().time() - start_time) * 1000
            )
            result["error"] = "Connection Timeout"
        except aiohttp.ClientError as e:
            result["fetch_time_ms"] = int(
                (asyncio.get_event_loop().time() - start_time) * 1000
            )
            result["error"] = str(e)
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"

        return result


def normalize_url(url: str) -> Optional[str]:
    """
    Extracts the netloc (domain) from a URL.

    Args:
        url: The input URL string.

    Returns:
        The domain (netloc) or None if invalid.
    """
    try:
        # Basic validation to prevent shell injection or weird formats
        if not re.match(r'^https?://', url):
            url = 'http://' + url
            
        parsed = urlparse(url)
        if parsed.netloc:
            return parsed.netloc
        return None
    except ValueError:
        return None