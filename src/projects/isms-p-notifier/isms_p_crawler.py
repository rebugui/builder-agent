"""
ISMS-P 자료실 크롤러
클라우드보안인증제 자료실의 첫 번째 게시글 번호를 확인합니다.
"""

from bs4 import BeautifulSoup
from typing import Optional, Dict
import logging
import asyncio
import re

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class ISMPCrawler:
    """ISMS-P 자료실 크롤러 (Playwright 사용)"""

    def __init__(self, base_url: str, headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def _init_browser(self):
        """Playwright 브라우저 초기화"""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            self.page = await self.context.new_page()
            logger.info("Playwright 브라우저 초기화 완료")

    async def close(self):
        """브라우저 종료"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("브라우저 종료 완료")

    async def fetch_html(self) -> Optional[str]:
        """페이지 HTML 가져오기"""
        try:
            await self._init_browser()
            logger.debug(f"페이지 로드: {self.base_url}")
            await self.page.goto(self.base_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)  # JavaScript 실행 대기
            return await self.page.content()
        except Exception as e:
            logger.error(f"페이지 가져오기 실패: {e}")
            return None

    async def get_first_post_info(self) -> Optional[Dict[str, str]]:
        """
        첫 번째 게시글 정보 가져오기

        Returns:
            {'number': '63', 'title': '...', 'date': '...', 'link': '...'}
        """
        html = await self.fetch_html()
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # certi_status_02_tb 영역 찾기
        tb_div = soup.find('div', class_='certi_status_02_tb')
        if not tb_div:
            logger.warning("certi_status_02_tb 영역을 찾을 수 없음")
            return None

        text = tb_div.get_text()

        # 번호 추출
        number_match = re.search(r'번호\s*(\d+)', text)
        number = number_match.group(1) if number_match else ""

        # 날짜 추출
        date_match = re.search(r'게시일(\d{4}-\d{2}-\d{2})', text)
        date = date_match.group(1) if date_match else ""

        # 제목과 링크 (첫 번째 링크)
        link = tb_div.find('a')
        title = ""
        detail_url = ""

        if link:
            title = link.get_text(strip=True)
            href = link.get('href', '')
            # JavaScript 함수에서 URL 추출
            url_match = re.search(r"['\"]([^'\"]*selectGnrlVrtlRcsrmDetail[^'\"]*?)['\"]", href)
            if url_match:
                detail_url = url_match.group(1)
            else:
                detail_url = href

        result = {
            'number': number,
            'title': title,
            'date': date,
            'detail_url': detail_url,
            'link': f"https://isms-p.or.kr{detail_url}" if detail_url and not detail_url.startswith('http') else ""
        }

        logger.info(f"첫 번째 게시글: [{number}] {title[:50]}...")
        return result


class SyncISMPCrawler:
    """동기식 인터페이스 래퍼"""

    def __init__(self, base_url: str, headless: bool = True):
        self.crawler = ISMPCrawler(base_url, headless)

    def _run_async(self, coro):
        """비동기 함수 실행"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    def get_first_post_info(self) -> Optional[Dict[str, str]]:
        """첫 번째 게시글 정보 가져오기 (동기)"""
        try:
            return self._run_async(self.crawler.get_first_post_info())
        finally:
            self._run_async(self.crawler.close())
