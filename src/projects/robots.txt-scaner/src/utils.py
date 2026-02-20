"""유틸리티 함수 - URL 정규화, 파일 처리 등"""
import sys
import re
from typing import List, Optional
from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> Optional[str]:
    """
    URL을 정규화합니다.
    
    - 앞뒤 공백 제거
    - 프로토콜 기본값: https
    - 경로 정규화
    
    Args:
        url: 입력 URL 문자열
        
    Returns:
        정규화된 URL 또는 None (유효하지 않은 경우)
    """
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    if not url:
        return None
    
    # 프로토콜이 없는 경우 추가
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    try:
        parsed = urlparse(url)
        
        # 유효한 도메인 확인
        if not parsed.netloc:
            return None
        
        # 기본 경로 처리
        path = parsed.path or '/'
        
        # 정규화된 URL 재구성 (robots.txt 경로 제외)
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            path,
            parsed.params,
            parsed.query,
            ''  # fragment 제거
        ))
        
        return normalized.rstrip('/')
        
    except Exception:
        return None


def is_valid_url(url: str) -> bool:
    """
    URL이 유효한지 검증합니다.
    
    Args:
        url: 검증할 URL 문자열
        
    Returns:
        유효 여부
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    if not url:
        return False
    
    # 프로토콜이 없는 경우 추가 후 검증
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    try:
        parsed = urlparse(url)
        
        # 필수 구성 요소 확인
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # 스킴 확인
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # 도메인 형식 기본 검증
        domain = parsed.netloc
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$', domain.split(':')[0]):
            return False
        
        return True
        
    except Exception:
        return False


def read_urls_from_file(file_path: str) -> List[str]:
    """
    파일에서 URL 목록을 읽어옵니다.
    
    Args:
        file_path: 입력 파일 경로
        
    Returns:
        URL 목록
        
    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        IOError: 파일 읽기 오류
    """
    urls = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith('#'):
                urls.append(url)
    
    return urls


def read_urls_from_stdin() -> List[str]:
    """
    표준 입력에서 URL 목록을 읽어옵니다.
    
    Returns:
        URL 목록
    """
    urls = []
    
    for line in sys.stdin:
        url = line.strip()
        if url and not url.startswith('#'):
            urls.append(url)
    
    return urls


def format_file_size(size_bytes: int) -> str:
    """
    바이트 크기를 사람이 읽기 쉬운 형식으로 변환합니다.
    
    Args:
        size_bytes: 바이트 단위 크기
        
    Returns:
        포맷된 크기 문자열
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def sanitize_filename(filename: str) -> str:
    """
    파일명에서 위험한 문자를 제거합니다.
    
    Args:
        filename: 원본 파일명
        
    Returns:
        안전한 파일명
    """
    # 위험한 문자 제거
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # 연속된 밑줄 정리
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # 앞뒤 밑줄/공백 제거
    sanitized = sanitized.strip('_ ')
    
    # 빈 파일명 방지
    if not sanitized:
        sanitized = "output"
    
    return sanitized
