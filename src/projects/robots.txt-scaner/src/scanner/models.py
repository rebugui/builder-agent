"""데이터 모델 정의"""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import json


@dataclass
class ScanResult:
    """스캔 결과 데이터 클래스"""
    url: str
    robots_url: str
    status: Optional[int]
    content_length: int = 0
    rules: Optional[Dict[str, Any]] = None
    raw_content: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        딕셔너리로 변환 (JSON 직렬화용).
        
        Returns:
            딕셔너리 표현
        """
        result = {
            'url': self.url,
            'robots_url': self.robots_url,
            'status': self.status,
            'content_length': self.content_length,
            'rules': self.rules,
            'error': self.error
        }
        
        # raw_content는 필요한 경우에만 포함
        # (파일 크기 줄이기 위해 기본적으로 제외)
        
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """
        JSON 문자열로 변환.
        
        Args:
            indent: 들여쓰기 수준
        
        Returns:
            JSON 문자열
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @property
    def is_success(self) -> bool:
        """성공 여부 확인."""
        return self.status == 200
    
    @property
    def has_robots_txt(self) -> bool:
        """robots.txt 존재 여부."""
        return self.status == 200 and self.rules is not None
    
    @property
    def has_error(self) -> bool:
        """에러 발생 여부."""
        return self.error is not None


@dataclass
class ScanStatistics:
    """스캔 통계"""
    total_urls: int = 0
    success_count: int = 0
    not_found_count: int = 0
    forbidden_count: int = 0
    error_count: int = 0
    total_sitemaps: int = 0
    total_rules: int = 0
    
    def add_result(self, result: ScanResult) -> None:
        """
        결과 추가 및 통계 업데이트.
        
        Args:
            result: 스캔 결과
        """
        self.total_urls += 1
        
        if result.is_success:
            self.success_count += 1
            if result.rules:
                self.total_sitemaps += len(result.rules.get('sitemaps', []))
                for ua_rules in result.rules.get('user_agents', {}).values():
                    self.total_rules += len(ua_rules.get('disallow', []))
                    self.total_rules += len(ua_rules.get('allow', []))
        elif result.status == 404:
            self.not_found_count += 1
        elif result.status == 403:
            self.forbidden_count += 1
       