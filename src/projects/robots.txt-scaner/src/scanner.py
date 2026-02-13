import asyncio
import logging
import sqlite3
import urllib.parse
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, AsyncGenerator
import aiohttp
import json

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 10
DEFAULT_USER_AGENT = "RobotsTxtScanner/1.0"
CACHE_EXPIRY_HOURS = 24

class CacheManager:
    """Manages SQLite cache for scanned robots.txt results."""
    
    def __init__(self, db_path: str = "scan_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_cache (
                    domain TEXT PRIMARY KEY,
                    status_code INTEGER,
                    last_checked TEXT,
                    json_result TEXT
                )
            ''')
            conn.commit()

    def get(self, domain: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result if valid and not expired."""
        expiry_time = datetime.now() - timedelta(hours=CACHE_EXPIRY_HOURS)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT json_result, last_checked FROM scan_cache WHERE domain = ?",
                (domain,)
            )
            row = cursor.fetchone()
            if row:
                last_checked = datetime.fromisoformat(row['last_checked'])
                if last_checked > expiry_time:
                    logger.debug(f"Cache hit for {domain}")
                    return json.loads(row['json_result'])
        return None

    def set(self, domain: str, status_code: int, result: Dict[str, Any]):
        """Store scan result in cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO scan_cache (domain, status_code, last_checked, json_result) VALUES (?, ?, ?, ?)",
                (domain, status_code, datetime.now().isoformat(), json.dumps(result))
            )
            conn.commit()

class RobotsParser:
    """Custom parser to extract structured data from robots.txt content."""
    
    @staticmethod
    def parse(content: str) -> Dict[str, Any]:
        """
        Parses robots.txt content to extract rules and sitemaps.
        """
        sitemaps = []
        rules = []
        current_ua = None
        
        # Normalize line endings and split
        lines = content.replace('\r\n', '\n').split('\n')
        
        # Regex for directives
        pattern = re.compile(r'^(?P<key>user-agent|allow|disallow|sitemap|crawl-delay):\s*(?P<value>.*)$', re.IGNORECASE)
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            match = pattern.match(line)
            if match:
                key = match.group('key').lower()
                value = match.group('value').strip()
                
                if key == 'user-agent':
                    current_ua = value
                    # Check if UA group exists, if not add
                    if not any(r['user_agent'] == current_ua for r in rules):
                        rules.append({'user_agent': current_ua, 'allow': [], 'disallow': []})
                        
                elif key == 'allow':
                    if current_ua is not None:
                        for r in reversed(rules): # Update last added UA
                            if r['user_agent'] == current_ua:
                                r['allow'].append(value)
                                break
                                
                elif key == 'disallow':
                    if current_ua is not None:
                        for r in reversed(rules):
                            if r['user_agent'] == current_ua:
                                r['disallow'].append(value)
                                break
                                
                elif key == 'sitemap':
                    sitemaps.append(value)

        return {
            "sitemap_urls": sitemaps,
            "rules": rules
        }

class RobotsScanner:
    def __init__(self, concurrency: int = 50, timeout: int = DEFAULT_TIMEOUT, user_agent: str = DEFAULT_USER_AGENT):
        self.concurrency = concurrency
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.user_agent = user_agent
        self.cache = CacheManager()
        self.session: Optional[aiohttp.ClientSession] = None

    async def _init_session(self):
        if self.session is None or self.session.closed:
            headers = {"User-Agent": self.user_agent}
            self.session = aiohttp.ClientSession(headers=headers, timeout=self.timeout)

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def scan_single_url(self, target_url: str) -> Dict[str, Any]:
        """Scan a single URL for robots.txt."""
        # Input Validation and Normalization
        try:
            parsed = urllib.parse.urlparse(target_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
            
            # Construct robots.txt URL
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            domain = parsed.netloc
            
            # Check Cache
            cached = self.cache.get(domain)
            if cached:
                return cached

        except Exception as e:
            logger.error(f"URL parsing error for {target_url}: {e}")
            return {
                "target_url": target_url,
                "robots_url": None,
                "status_code": 0,
                "error": f"Invalid URL: {str(e)}",
                "rules": [],
                "sitemap_urls": []
            }

        # Fetch
        result = {
            "target_url": target_url,
            "robots_url": robots_url,
            "status_code": None,
            "content_length": 0,
            "crawl_delay": None,
            "sitemap_urls": [],
            "rules": [],
            "raw_content": None,
            "error": None
        }

        await self._init_session()
        
        try:
            async with self.session.get(robots_url) as response:
                result['status_code'] = response.status
                result['content_length'] = response.headers.get('Content-Length', 0)
                
                if response.status == 200:
                    content = await response.text()
                    result['raw_content'] = content
                    parsed_data = RobotsParser.parse(content)
                    result['rules'] = parsed_data['rules']
                    result['sitemap_urls'] = parsed_data['sitemap_urls']
                else:
                    result['error'] = response.reason or "HTTP Error"
                    
        except asyncio.TimeoutError:
            result['status_code'] = 504
            result['error'] = "Timeout"
            logger.warning(f"Timeout fetching {robots_url}")
        except aiohttp.ClientError as e:
            result['status_code'] = 500
            result['error'] = str(e)
            logger.warning(f"Client error fetching {robots_url}: {e}")
        except Exception as e:
            result['status_code'] = 500
            result['error'] = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error for {robots_url}: {e}")

        # Update Cache
        if result['status_code'] is not None:
            self.cache.set(domain, result['status_code'], result)

        return result

    async def run(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Run scan with concurrency control."""
        semaphore = asyncio.Semaphore(self.concurrency)
        
        async def bound_scan(url):
            async with semaphore:
                return await self.scan_single_url(url)
        
        tasks = [bound_scan(url) for url in urls]
        return await asyncio.gather(*tasks)
