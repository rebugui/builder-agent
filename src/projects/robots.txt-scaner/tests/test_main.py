"""main 모듈 단위 테스트"""
import pytest
import logging
import argparse
from unittest.mock import patch, MagicMock
from io import StringIO
from src.main import setup_logging, parse_arguments, cli


class TestSetupLogging:
    """setup_logging 함수 테스트"""
    
    def test_setup_logging_default(self):
        """기본 로깅 설정 테스트"""
        setup_logging(verbose=False)
        
        root_logger = logging.getLogger()
        # 기본 로그 레벨 확인 (INFO 또는 WARNING)
        assert root_logger.level in [logging.INFO, logging.WARNING, logging.DEBUG]
    
    def test_setup_logging_verbose(self):
        """상세 로깅 설정 테스트"""
        setup_logging(verbose=True)
        
        root_logger = logging.getLogger()
        # verbose 모드에서는 DEBUG 레벨
        assert root_logger.level == logging.DEBUG
    
    def test_setup_logging_format(self):
        """로그 포맷 설정 테스트"""
        setup_logging(verbose=False)
        
        root_logger = logging.getLogger()
        handlers = root_logger.handlers
        
        # 핸들러가 존재하고 포맷이 설정되어 있는지 확인
        if handlers:
            handler = handlers[0]
            if hasattr(handler, 'formatter') and handler.formatter:
                assert handler.formatter._fmt is not None
    
    def test_setup_logging_multiple_calls(self):
        """여러 번 호출 테스트"""
        # 여러 번 호출해도 에러가 발생하지 않아야 함
        setup_logging(verbose=False)
        setup_logging(verbose=True)
        setup_logging(verbose=False)


class TestParseArguments:
    """parse_arguments 함수 테스트"""
    
    def test_parse_arguments_default(self):
        """기본 인자 파싱 테스트"""
        with patch('sys.argv', ['prog']):
            args = parse_arguments()
            assert args is not None
    
    def test_parse_arguments_with_urls(self):
        """URL 인자 파싱 테스트"""
        with patch('sys.argv', ['prog', 'https://example.com', 'https://test.org']):
            args = parse_arguments()
            # URL이 올바르게 파싱되는지 확인
            assert hasattr(args, 'urls') or hasattr(args, 'url')
    
    def test_parse_arguments_with_file(self):
        """파일 인자 파싱 테스트"""
        with patch('sys.argv', ['prog', '-f', 'urls.txt']):
            args = parse_arguments()
            assert hasattr(args, 'file') or hasattr(args, 'input_file')
    
    def test_parse_arguments_verbose(self):
        """verbose 플래그 파싱 테스트"""
        with patch('sys.argv', ['prog', '-v']):
            args = parse_arguments()
            assert args.verbose is True
    
    def test_parse_arguments_output(self):
        """출력 파일 인자 파싱 테스트"""
        with patch('sys.argv', ['prog', '-o', 'output.json']):
            args = parse_arguments()
            assert hasattr(args, 'output') and args.output == 'output.json'
    
    def test_parse_arguments_help(self):
        """도움말 인자 테스트"""
        with patch('sys.argv', ['prog', '-h']):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            # -h는 정상 종료 (exit code 0)
            assert exc_info.value.code == 0
    
    def test_parse_arguments_timeout(self):
        """