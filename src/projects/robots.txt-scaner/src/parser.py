"""robots.txt 파싱 로직 - 텍스트를 구조화된 데이터로 변환"""
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging


@dataclass
class Directive:
    """
    개별 directive를 나타내는 데이터 클래스.
    
    Attributes:
        type: Directive 타입 (Allow, Disallow, Crawl-delay 등)
        value: Directive 값
    """
    type: str
    value: str
    
    def to_dict(self) -> Dict[str, str]:
        """딕셔너리로 변환합니다."""
        return {"type": self.type, "value": self.value}


class RobotsParser:
    """
    robots.txt 콘텐츠 파서 클래스.
    
    raw 텍스트를 구조화된 딕셔너리 형태로 변환합니다.
    
    Example:
        >>> parser = RobotsParser()
        >>> result = parser.parse("User-agent: *\\nDisallow: /admin/")
        >>> print(result["directives"])
        {"*": [{"type": "Disallow", "value": "/admin/"}]}
    """
    
    # 지원하는 directive 타입
    DIRECTIVE_TYPES = {
        'user-agent': 'User-agent',
        'allow': 'Allow',
        'disallow': 'Disallow',
        'sitemap': 'Sitemap',
        'crawl-delay': 'Crawl-delay',
        'request-rate': 'Request-rate',
        'visit-time': 'Visit-time',
        'robot-version': 'Robot-version',
        'comment': 'Comment'
    }
    
    def __init__(self):
        """RobotsParser 초기화."""
        self.logger = logging.getLogger(__name__)
    
    def parse(self, content: str) -> Dict[str, Any]:
        """
        robots.txt 콘텐츠를 파싱합니다.
        
        Args:
            content: robots.txt 원본 텍스트
            
        Returns:
            파싱된 결과 딕셔너리:
            {
                "directives": {user_agent: [Directive, ...]},
                "sitemaps": [url, ...]
            }
        """
        result = {
            "directives": {},
            "sitemaps": []
        }
        
        if not content or not isinstance(content, str):
            return result
        
        lines = content.split('\n')
        current_user_agent: Optional[str] = None
        user_agents_for_current_group: List[str] = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 빈 줄 무시
            if not line:
                i += 1
                continue
            
            # 주석 무시 (전체 줄이 주석인 경우)
            if line.startswith('#'):
                i += 1
                continue
            
            # 주석 제거 (인라인 주석)
            if '#' in line:
                comment_idx = self._find_comment_index(line)
                if comment_idx > 0:
                    line = line[:comment_idx].strip()
            
            # key: value 파싱
            parsed = self._parse_line(line)
            if not parsed:
                i += 1
                continue
            
            key, value = parsed
            key_lower = key.lower()
            
            if key_lower == 'user-agent':
                # 새 user-agent 그룹 시작
                if user_agents_for_current_group and current_user_agent:
                    # 이전 그룹 처리
                    pass
                current_user_agent = value
                user_agents_for_current_group.append(value)
                
                if value not in result["directives"]:
                    result["directives"][value] = []
                    
            elif key_lower == 'sitemap':
                # Sitemap은 전역 directive
                if value and value not in result["sitemaps"]:
                    result["sitemaps"].append(value)
                    
            elif key_lower in ('allow', 'disallow', 'crawl-delay', 'request-rate', 'visit-time'):
                # User-agent별 directive
                if current_user_agent:
                    directive_type = self.DIRECTIVE_TYPES.get(key_lower, key)
                    directive = Directive(type=directive_type, value=value)
                    
                    # 모든 현재 user-agent에 추가
                    for ua in user_agents_for_current_group:
                        if ua not in result["directives"]:
                            result["directives"][ua] = []
                        result["directives"][ua].append(directive.to_dict())
                        
                    # 그룹 초기화 (하나의 그룹 완료)
                    user_agents_for_current_group = []
            
            i += 1
        
        return result
    
    def _parse_line(self, line: str) -> Optional[tuple]:
        """
        단일 라인을 key: value 쌍으로 파싱합니다.
        
        Args:
            line: 파싱할 라인
            
        Returns:
            (key, value) 튜플 또는 None
        """
        if ':' not in line:
            return None
        
        # 첫 번째 콜론으로 분리
        colon_idx = line.index(':')
        key = line[:colon_idx].strip()
        value = line[colon_idx + 1:].strip()
        
        if not key:
            return None
        
        return (key, value)
    
    def _find_comment_index(self, line: str) -> int:
        """
        라인 내 주석 시작 인덱스를 찾습니다.
        
        URL 내의 #과 주석 #을 구분합니다.
        
        Args:
            line: 검사할 라인
            
        Returns:
            주석 시작 인덱스 (없으면 -1)
        """
        in_value = False
        for i, char in enumerate(line):
            if char == ':' and not in_value:
                in_value = True
            elif char == '#' and in_value:
                # 값 내부의 #은 주석이 아닐 수 있음
                # 간단히 처리: 공백 뒤의 #은 주석
                if i > 0 and line[i-1] == ' ':
                    return i
        
        # 값 부분 다음의 # 찾기
        if '#' in line:
            return line.index('#')
        
        return -1
    
    def get_disallowed_paths(self, directives: Dict[str, List], user_agent: str = "*") -> List[str]:
        """
        특정 user-agent에 대해 차단된 경로 목록을 반환합니다.
        
        Args:
            directives: 파싱된 directives 딕셔너리
            user_agent: 대상 user-agent (기본값: "*")
            
        Returns:
            차단된 경로 목록
        """
        disallowed = []
        
        # 와일드카드 매칭을 위해 * 먼저 확인
        if "*" in directives:
            for directive in directives["*"]:
                if directive.get("type") == "Disallow":
                    value = directive.get("value", "")
                    if value and value not in disallowed:
                        disallowed.append(value)
        
        # 특정 user-agent 확인
        if user_agent != "*" and user_agent in directives:
            for directive in directives[user_agent]:
                if directive.get("type") == "Disallow":
                    value = directive.get("value", "")
                    if value and value not in disallowed:
                        disallowed.append(value)
        
        return disallowed
    
    def get_crawl_delay(self, directives: Dict[str, List], user_agent: str = "*") -> Optional[int]:
        """
        특정 user-agent에 대한 crawl delay를 반환합니다.
        
        Args:
            directives: 파싱된 directives 딕셔너리
            user_agent: 대상 user-agent
            
        Returns:
            Crawl-delay 값 (초) 또는 None
        """
        def find_delay(ua: str) -> Optional[int]:
            if ua not in directives:
                return None
            for directive in directives[ua]:
                if directive.get("type") == "Crawl-delay":
                    try:
                        return int(directive.get("value", 0))
                    except (ValueError, TypeError):
                        return None
            return None
        
        # 특정 user-agent 우선
        if user_agent != "*":
            delay = find_delay(user_agent)
            if delay is not None:
                return delay
        
        # 와일드카드 폴백
        return find_delay("*")
