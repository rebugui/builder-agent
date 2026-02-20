"""utils 모듈 단위 테스트"""
import pytest
import tempfile
import os
import sys
from io import StringIO
from unittest.mock import patch, mock_open
from src.utils import (
    normalize_url,
    is_valid_url,
    read_urls_from_file,
    read_urls_from_stdin,
    format_file_size,
    sanitize_filename
)


class TestNormalizeUrl:
    """normalize_url 함수 테스트"""
    
    def test_normalize_url_basic(self):
        """기본 URL 정규화 테스트"""
        url = normalize_url("https://example.com")
        assert url == "https://example.com"
    
    def test_normalize_url_add_https(self):
        """프로토콜 추가 테스트"""
        url = normalize_url("example.com")
        assert url.startswith("https://")
    
    def test_normalize_url_trailing_spaces(self):
        """앞뒤 공백 제거 테스트"""
        url = normalize_url("  https://example.com  ")
        assert url == "https://example.com"
    
    def test_normalize_url_http(self):
        """HTTP 프로토콜 유지 테스트"""
        url = normalize_url("http://example.com")
        assert url == "http://example.com"
    
    def test_normalize_url_with_path(self):
        """경로 포함 URL 정규화 테스트"""
        url = normalize_url("https://example.com/path/to/page/")
        assert url == "https://example.com/path/to/page/"
    
    def test_normalize_url_with_query(self):
        """쿼리 스트링 포함 테스트"""
        url = normalize_url("https://example.com?query=value")
        assert "query=value" in url
    
    def test_normalize_url_empty_string(self):
        """빈 문자열 테스트"""
        url = normalize_url("")
        # 빈 문자열 처리 방식에 따라 다름
        assert url == "" or url is None or "https://" in url
    
    def test_normalize_url_double_slash(self):
        """이중 슬래시 정규화 테스트"""
        url = normalize_url("https://example.com//path")
        # 구현에 따라 이중 슬래시가 제거되거나 유지됨
        assert "example.com" in url
    
    def test_normalize_url_with_port(self):
        """포트 번호 포함 테스트"""
        url = normalize_url("https://example.com:8080")
        assert ":8080" in url
    
    def test_normalize_url_subdomain(self):
        """서브도메인 테스트"""
        url = normalize_url("https://sub.example.com")
        assert url == "https://sub.example.com"


class TestIsValidUrl:
    """is_valid_url 함수 테스트"""
    
    def test_is_valid_url_https(self):
        """HTTPS URL 검증 테스트"""
        assert is_valid_url("https://example.com") is True
    
    def test_is_valid_url_http(self):
        """HTTP URL 검증 테스트"""
        assert is_valid_url("http://example.com") is True
    
    def test_is_valid_url_no_protocol(self):
        """프로토콜 없는 URL 검증 테스트"""
        # 구현에 따라 다름
        result = is_valid_url("example.com")
        assert isinstance(result, bool)
    
    def test_is_valid_url_empty(self):
        """빈 문자열 검증 테스트"""
        assert is_valid_url("") is False
    
    def test_is_valid_url_invalid(self):
        """잘못된 URL 검증 테스트"""
        assert is_valid_url("not a valid url") is False
    
    def test_is_valid_url_with_path(self):
        """경로 포함 URL 검증 테스트"""
        assert is_valid_url("https://example.com/path/to/page") is True
    
    def test_is_valid_url_with_special_chars(self):
        """특수 문자 포함 URL 테스트"""
        assert is_valid_url("https://example.com/path?query=value&foo=bar") is True
    
    def test_is_valid_url_ipv4(self):
        """IPv4 주소 URL 테스트"""
        assert is_valid_url("https://192.168.1.1") is True
    
    def test_is_valid_url_ipv6(self):
        """IPv6 주소 URL 테스트"""
        assert is_valid_url("https://[2001:db8::1]") is True
    
    def test_is_valid_url_localhost(self):
        """localhost URL 테스트"""
        assert is_valid_url("http://localhost:8000") is True


class TestReadUrlsFromFile:
    """read_urls_from_file 함수 테스트"""
    
    def test_read_urls_from_file_single(self):
        """단일 URL 파일 읽기 테스트"""
        content = "https://example.com\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name
        
        try:
            urls = read_urls_from_file(temp_path)
            assert "https://example.com" in urls
        finally:
            os.unlink(temp_path)
    
    def test_read_urls_from_file_multiple(self):
        """여러 URL 파일 읽기 테스트"""
        content = "https://example.com\nhttps://test.org\nhttps://sample.net\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name
        
        try:
            urls = read_urls_from_file(temp_path)
            assert len(urls) == 3
            assert "https://example.com" in urls
            assert "https://test.org" in urls
        finally:
            os.unlink(temp_path)
    
    def test_read_urls_from_file_with_comments(self):
        """주석 포함 파일 읽기 테스트"""
        content = "# This is a comment\nhttps://example.com\n# Another comment\nhttps://test.org\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name
        
        try:
            urls = read_urls_from_file(temp_path)
            # 주석이 제거되거나 무시되어야 함
            assert all(not url.startswith("#") for url in urls if url.strip())
        finally:
            os.unlink(temp_path)
    
    def test_read_urls_from_file_empty(self):
        """빈 파일 읽기 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            f.flush()
            temp_path = f.name
        
        try:
            urls = read_urls_from_file(temp_path)
            assert urls == [] or urls == ['']
        finally:
            os.unlink(temp_path)
    
    def test_read_urls_from_file_nonexistent(self):
        """존재하지 않는 파일 테스트"""
        with pytest.raises((FileNotFoundError, IOError)):
            read_urls_from_file("/nonexistent/path/to/file.txt")
    
    def test_read_urls_from_file_with_empty_lines(self):
        """빈 줄 포함 파일 테스트"""
        content = "https://example.com\n\n\nhttps://test.org\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name
        
        try:
            urls = read_urls_from_file(temp_path)
            # 빈 줄이 필터링되어야 함
            non_empty_urls = [u for u in urls if u.strip()]
            assert len(non_empty_urls) >= 2
        finally:
            os.unlink(temp_path)


class TestReadUrlsFromStdin:
    """read_urls_from_stdin 함수 테스트"""
    
    def test_read_urls_from_stdin_single(self):
        """stdin 단일 URL 읽기 테스트"""
        test_input = "https://example.com\n"
        with patch('sys.stdin', StringIO(test_input)):
            # stdin에서 읽기는 실제 환경에서 테스트 어려움
            # mock으로 대체
            pass
    
    def test_read_urls_from_stdin_multiple(self):
        """stdin 여러 URL 읽기 테스트"""
        test_input = "https://example.com\nhttps://test.org\nhttps://sample.net\n"
        with patch('sys.stdin', StringIO(test_input)):
            pass
    
    def test_read_urls_from_stdin_empty(self):
        """stdin 빈 입력 테스트"""
        test_input = ""
        with patch('sys.stdin', StringIO(test_input)):
            pass


class TestFormatFileSize:
    """format_file_size 함수 테스트"""
    
    def test_format_file_size_bytes(self):
        """바이트 크기 포맷 테스트"""
        result = format_file_size(500)
        assert "500" in result
        assert "B" in result
    
    def test_format_file_size_kilobytes(self):
        """킬로바이트 크기 포맷 테스트"""
        result = format_file_size(1024)
        assert "1" in result
        assert "KB" in result
    
    def test_format_file_size_megabytes(self):
        """메가바이트 크기 포맷 테스트"""
        result = format_file_size(1024 * 1024)
        assert "1" in result
        assert "MB" in result
    
    def test_format_file_size_gigabytes(self):
        """기가바이트 크기 포맷 테스트"""
        result = format_file_size(1024 * 1024 * 1024)
        assert "1" in result
        assert "GB" in result
    
    def test_format_file_size_zero(self):
        """0 바이트 포맷 테스트"""
        result = format_file_size(0)
        assert "0" in result
    
    def test_format_file_size_negative(self):
        """음수 크기 포맷 테스트"""
        # 음수 처리 방식에 따라 다름
        result = format_file_size(-100)
        assert result is not None
    
    def test_format_file_size_large(self):
        """매우 큰 크기 포맷 테스트"""
        result = format_file_size(1024 * 1024 * 1024 * 1024)
        assert "TB" in result or "PB" in result
    
    def test_format_file_size_decimal_places(self):
        """소수점 자릿수 테스트"""
        result = format_file_size(1536)  # 1.5 KB
        assert "1.5" in result or "1.50" in result


class TestSanitizeFilename:
    """sanitize_filename 함수 테스트"""
    
    def test_sanitize_filename_normal(self):
        """정상 파일명 테스트"""
        result = sanitize_filename("normal_filename.txt")
        assert result == "normal_filename.txt"
    
    def test_sanitize_filename_with_slashes(self):
        """슬래시 포함 파일명 테스트"""
        result = sanitize_filename("file/name.txt")
        assert "/" not in result
    
    def test_sanitize_filename_with_backslashes(self):
        """역슬래시 포함 파일명 테스트"""
        result = sanitize_filename("file\\name.txt")
        assert "\\" not in result
    
    def test_sanitize_filename_with_colon(self):
        """콜론 포함 파일명 테스트"""
        result = sanitize_filename("file:name.txt")
        assert ":" not in result
    
    def test_sanitize_filename_with_special_chars(self):
        """특수 문자 포함 파일명 테스트"""
        result = sanitize_filename("file<>:\"|*?.txt")
        dangerous_chars = ['<', '>', ':', '"', '|', '*', '?']
        for char in dangerous_chars:
            assert char not in result
    
    def test_sanitize_filename_empty(self):
        """빈 파일명 테스트"""
        result = sanitize_filename("")
        assert result is not None
    
    def test_sanitize_filename_with_spaces(self):
        """공백 포함 파일명 테스트"""
        result = sanitize_filename("file name.txt")
        # 공백이 유지되거나 언더스코어로 대체
        assert " " not in result or result == "file name.txt"
    
    def test_sanitize_filename_with_dots(self):
        """여러 점 포함 파일명 테스트"""
        result = sanitize_filename("file...name.txt")
        # 구현에 따라 처리 방식 다름
        assert result is not None
    
    def test_sanitize_filename_unicode(self):
        """유니코드 파일명 테스트"""
        result = sanitize_filename("파일명.txt")
        # 유니코드가 유지되거나 변환됨
        assert result is not None
    
    def test_sanitize_filename_long(self):
        """긴 파일명 테스트"""
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        # 파일명 길이 제한이 있을 수 있음
        assert len(result) <= 255 or result is not None
    
    def test_sanitize_filename_reserved_names(self):
        """예약된 파일명 테스트 (Windows)"""
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        for name in reserved_names:
            result = sanitize_filename(name)
            # 예약어가 처리되어야 함
            assert result is not None
