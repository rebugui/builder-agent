"""robots.txt 파싱 로직"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class RobotRule:
    """개별 규칙"""
    path: str
    line_number: int


@dataclass
class UserAgentRules:
    """User-agent별 규칙 집합"""
    disallow: List[str] = field(default_factory=list)
    allow: List[str] = field(default_factory=list)
    crawl_delay: Optional[float] = None
    request_rate: Optional[str] = None
    cache_delay: Optional[float] = None


@dataclass
class ParsedRules:
    """파싱된 robots.txt 규칙"""
    user_agents: Dict[str, UserAgentRules] = field(default_factory=dict)
    sitemaps: List[str] = field(default_factory=list)
    host: Optional[str] = None
    comments: List[str] = field(default_factory=list)


class RobotsParser:
    """robots.txt 파서"""
    
    # 정규식 패턴 (보안: ReDoS 방지를 위한 단순 패턴)
    USER_AGENT_PATTERN = re.compile(r'^user-agent\s*:\s*(.+)$', re.IGNORECASE)
    DISALLOW_PATTERN = re.compile(r'^disallow\s*:\s*(.*)$', re.IGNORECASE)
    ALLOW_PATTERN = re.compile(r'^allow\s*:\s*(.*)$', re.IGNORECASE)
    SITEMAP_PATTERN = re.compile(r'^sitemap\s*:\s*(.+)$', re.IGNORECASE)
    CRAWL_DELAY_PATTERN = re.compile(r'^crawl-delay\s*:\s*(\d+(?:\.\d+)?)$', re.IGNORECASE)
    REQUEST_RATE_PATTERN = re.compile(r'^request-rate\s*:\s*(.+)$', re.IGNORECASE)
    CACHE_DELAY_PATTERN = re.compile(r'^cache-delay\s*:\s*(\d+(?:\.\d+)?)$', re.IGNORECASE)
    HOST_PATTERN = re.compile(r'^host\s*:\s*(.+)$', re.IGNORECASE)
    COMMENT_PATTERN = re.compile(r'^#(.*)$')
    
    # 경로 검증 패턴
    PATH_PATTERN = re.compile(r'^/[^\s]*$|^\*$|^/$')
    
    def __init__(self, filter_agent: Optional[str] = None):
        """
        파서 초기화.
        
        Args:
            filter_agent: 필터링할 특정 User-agent (None이면 전체)
        """
        self.filter_agent = filter_agent.lower() if filter_agent else None
    
    def _sanitize_path(self, path: str) -> Optional[str]:
        """
        경로 문자열 정제.
        
        Args:
            path: 원본 경로 문자열
        
        Returns:
            정제된 경로 또는 None (무효한 경우)
        """
        if not path:
            return None
        
        path = path.strip()
        
        # 빈 경로 허용 (Disallow: 만 있는 경우)
        if not path:
            return ""
        
        # 경로 길이 제한 (보안)
        if len(path) > 2048:
            return None
        
        # 기본 형식 검증
        if path == '*' or path.startswith('/'):
            return path
        
        # 상대 경로나 기타 형식
        if not path.startswith(('/')):
            return None
        
        return path
    
    def _sanitize_url(self, url: str) -> Optional[str]:
        """
        URL 정제 (Sitemap 등).
        
        Args:
            url: 원본 URL 문자열
        
        Returns:
            정제된 URL 또는 None
        """
        if not url:
            return None
        
        url = url.strip()
        
        # 길이 제한
        if len(url) > 2048:
            return None
        
        # 기본 URL 형식 확인
        if not url.startswith(('http://', 'https://', '/')):
            return None
        
        return url
    
    def _should_include_user_agent(self, user_agent: str) -> bool:
        """
        User-agent가 필터 조건에 맞는지 확인.
        
        Args:
            user_agent: User-agent 문자값
        
        Returns:
            포함 여부
        """
        if not self.filter_agent:
            return True
        
        return user_agent.lower() == self.filter_agent or self.filter_agent in user_agent.lower()
    
    def parse(self, content: str) -> Dict[str, Any]:
        """
        robots.txt 내용 파싱.
        
        Args:
            content: robots.txt 원본 텍스트
        
        Returns:
            파싱된 규칙 딕셔너리
        """
        if not content or not isinstance(content, str):
            return self._empty_result()
        
        # 결과 구조 초기화
        user_agents: Dict[str, UserAgentRules] = {}
        sitemaps: List[str] = []
        host: Optional[str] = None
        comments: List[str] = []
        
        current_user_agents: Set[str] = set()
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 줄 길이 제한 (보안)
            if len(line) > 4096:
                line = line[:4096]
            
            stripped = line.strip()
            
            # 빈 줄 무시
            if not stripped:
                current_user_agents.clear()
                continue
            
            # 주석 처리
            comment_match = self.COMMENT_PATTERN.match(stripped)
            if comment_match:
                comments.append(comment_match.group(1).strip())
                continue
            
            # User-agent 파싱
            ua_match = self.USER_AGENT_PATTERN.match(stripped)
            if ua_match:
                ua = ua_match.group(1).strip()
                # User-agent 길이 제한
                if len(ua) <= 256:
                    current_user_agents.add(ua)
                    if ua not in user_agents:
                        user_agents[ua] = UserAgentRules()
                continue
            
            # 현재 User-agent가 없으면 다음 줄로
            if not current_user_agents:
                continue
            
            # Sitemap 파싱 (User-agent와 무관)
            sitemap_match = self.SITEMAP_PATTERN.match(stripped)
            if sitemap_match:
                sitemap_url = self._sanitize_url(sitemap_match.group(1).strip())
                if sitemap_url and sitemap_url not in sitemaps:
                    sitemaps.append(sitemap_url)
                continue
            
            # Host 파싱
            host_match = self.HOST_PATTERN.match(stripped)
            if host_match:
                host = host_match.group(1).strip()[:256]
                continue
            
            # 나머지 규칙은 현재 User-agent에 적용
            for ua in current_user_agents:
                if ua not in user_agents:
                    user_agents[ua] = UserAgentRules()
                
                rules = user_agents[ua]
                
                # Disallow 파싱
                disallow_match = self.DISALLOW_PATTERN.match(stripped)
                if disallow_match:
                    path = self._sanitize_path(disallow_match.group(1))
                    if path is not None and path not in rules.disallow:
                        rules.disallow.append(path)
                    continue
                
                # Allow 파싱
                allow_match = self.ALLOW_PATTERN.match(stripped)
                if allow_match:
                    path = self._sanitize_path(allow_match.group(1))
                    if path is not None and path not in rules.allow:
                        rules.allow.append(path)
                    continue
                
                # Crawl-delay 파싱
                crawl_match = self.CRAWL_DELAY_PATTERN.match(stripped)
                if crawl_match:
                    try:
                        rules.crawl_delay = float(crawl_match.group(1))
                    except ValueError:
                        pass
                    continue
                
                # Request-rate 파싱
                rate_match = self.REQUEST_RATE_PATTERN.match(stripped)
                if rate_match:
                    rules.request_rate = rate_match.group(1).strip()[:128]
                    continue
                
                # Cache-delay 파싱
                cache_match = self.CACHE_DELAY_PATTERN.match(stripped)
                if cache_match:
                    try:
                        rules.cache_delay = float(cache_match.group(1))
                    except ValueError:
                        pass
        
        # 필터링 적용
        if self.filter_agent:
            filtered_agents = {
                ua: rules for ua, rules in user_agents.items()
                if self._should_include_user_agent(ua)
            }
            user_agents = filtered_agents
        
        return self._build_output(user_agents, sitemaps, host)
    
    def _empty_result(self) -> Dict[str, Any]:
        """빈 결과 반환."""
        return {
            'user_agents': {},
            'sitemaps': [],
            'crawl_delay': None
        }
    
    def _build_output(
        self,
        user_agents: Dict[str, UserAgentRules],
        sitemaps: List[str],
        host: Optional[str]
    ) -> Dict[str, Any]:
        """
        출력 형식으로 변환.
        
        Args:
            user_agents: User-agent별 규칙
            sitemaps: Sitemap URL 리스트
            host: Host 값
        
        Returns:
            출력 딕셔너리
        """
        agents_output = {}
        
        for ua, rules in user_agents.items():
            agents_output[ua] = {
                'disallow': rules.disallow,
                'allow': rules.allow
            }
            
            if rules.crawl_delay is not None:
                agents_output[ua]['crawl_delay'] = rules.crawl_delay
        
        return {
            'user_agents': agents_output,
            'sitemaps': sitemaps,
            'crawl_delay': None,  # 전체 crawl_delay (deprecated)
            'host': host
        }
    
    def is_allowed(self, path: str, user_agent: str, rules: Dict[str, Any]) -> bool:
        """
        특정 경로가 허용되는지 확인.
        
        Args:
            path: 확인할 경로
            user_agent: User-agent 문자열
            rules: 파싱된 규칙
        
        Returns:
            허용 여부
        """
        if not path:
            return True
        
        # 가장 구체적인 User-agent 찾기
        applicable_rules = None
        
        for ua, ua_rules in rules.get('user_agents', {}).items():
            if ua == '*':
                applicable_rules = ua_rules
            elif ua.lower() in user_agent.lower():
                applicable_rules = ua_rules
                break
        
        if not applicable_rules:
            return True
        
        # Allow 규칙 먼저 확인
        for allow_path in applicable_rules.get('allow', []):
            if self._path_matches(path, allow_path):
                return True
        
        # Disallow 규칙 확인
        for disallow_path in applicable_rules.get('disallow', []):
            if disallow_path and self._path_matches(path, disallow_path):
                return False
        
        return True
    
    def _path_matches(self, path: str, pattern: str) -> bool:
        """
        경로가 패턴과 매치되는지 확인.
        
        Args:
            path: 요청 경로
            pattern: robots.txt 패턴
        
        Returns:
            매치 여부
        """
        if not pattern:
            return False
        
        if pattern == '/':
            return path.startswith('/')
        
        if pattern == '*':
            return True
        
        # 와일드카드 처리
        if '*' in pattern:
            # *를 .*로 변환 (단, 보안을 위해 길이 제한)
            regex_pattern = ''
            i = 0
            while i < len(pattern):
                if pattern[i] == '*':
                    regex_pattern += '.*'
                elif pattern[i] == '$':
                    # $는 끝을 의미
                    pass
                else:
                    regex_pattern += re.escape(pattern[i])
                i += 1
            
            try:
                return bool(re.match(f'^{regex_pattern}', path))
            except re.error:
                return path.startswith(pattern.rstrip('*'))
        
        # 단순 접두사 매칭
        return path.startswith(pattern)
