"""parser 모듈 단위 테스트"""
import pytest
from src.parser import Directive
from src.parser import RobotsParser


class TestDirective:
    """Directive 데이터 클래스 테스트"""
    
    def test_directive_creation_allow(self):
        """Allow directive 생성 테스트"""
        directive = Directive(type="Allow", value="/public/")
        assert directive.type == "Allow"
        assert directive.value == "/public/"
    
    def test_directive_creation_disallow(self):
        """Disallow directive 생성 테스트"""
        directive = Directive(type="Disallow", value="/admin/")
        assert directive.type == "Disallow"
        assert directive.value == "/admin/"
    
    def test_directive_creation_crawl_delay(self):
        """Crawl-delay directive 생성 테스트"""
        directive = Directive(type="Crawl-delay", value="10")
        assert directive.type == "Crawl-delay"
        assert directive.value == "10"
    
    def test_directive_to_dict(self):
        """Directive to_dict 메서드 테스트"""
        directive = Directive(type="Disallow", value="/private/")
        result = directive.to_dict()
        assert isinstance(result, dict)
        assert result["type"] == "Disallow"
        assert result["value"] == "/private/"
    
    def test_directive_with_empty_value(self):
        """빈 값으로 Directive 생성 테스트"""
        directive = Directive(type="Disallow", value="")
        assert directive.value == ""
    
    def test_directive_case_sensitivity(self):
        """Directive 타입 대소문자 테스트"""
        directive = Directive(type="allow", value="/path/")
        assert directive.type == "allow"


class TestRobotsParser:
    """RobotsParser 클래스 테스트"""
    
    def test_parser_initialization(self):
        """RobotsParser 초기화 테스트"""
        parser = RobotsParser()
        assert parser is not None
    
    def test_parse_simple_disallow(self):
        """간단한 Disallow 파싱 테스트"""
        parser = RobotsParser()
        content = "User-agent: *\nDisallow: /admin/"
        result = parser.parse(content)
        
        assert "directives" in result
        assert "*" in result["directives"]
        assert len(result["directives"]["*"]) == 1
        assert result["directives"]["*"][0]["type"] == "Disallow"
        assert result["directives"]["*"][0]["value"] == "/admin/"
    
    def test_parse_multiple_user_agents(self, sample_robots_content):
        """여러 User-agent 파싱 테스트"""
        parser = RobotsParser()
        result = parser.parse(sample_robots_content)
        
        assert "*" in result["directives"]
        assert "Googlebot" in result["directives"]
    
    def test_parse_allow_directive(self):
        """Allow directive 파싱 테스트"""
        parser = RobotsParser()
        content = "User-agent: *\nAllow: /public/"
        result = parser.parse(content)
        
        assert result["directives"]["*"][0]["type"] == "Allow"
        assert result["directives"]["*"][0]["value"] == "/public/"
    
    def test_parse_crawl_delay(self, sample_robots_content):
        """Crawl-delay directive 파싱 테스트"""
        parser = RobotsParser()
        result = parser.parse(sample_robots_content)
        
        crawl_delays = [d for d in result["directives"]["*"] if d["type"] == "Crawl-delay"]
        assert len(crawl_delays) == 1
        assert crawl_delays[0]["value"] == "10"
    
    def test_parse_sitemap(self, sample_robots_content):
        """Sitemap directive 파싱 테스트"""
        parser = RobotsParser()
        result = parser.parse(sample_robots_content)
        
        assert "sitemaps" in result
        assert "https://example.com/sitemap.xml" in result["sitemaps"]
    
    def test_parse_empty_content(self):
        """빈 콘텐츠 파싱 테스트"""
        parser = RobotsParser()
        result = parser.parse("")
        
        assert "directives" in result
        assert result["directives"] == {} or "*" not in result["directives"]
    
    def test_parse_content_with_comments(self):
        """주석이 포함된 콘텐츠 파싱 테스트"""
        parser = RobotsParser()
        content = "# This is a comment\nUser-agent: *\nDisallow: /admin/ # inline comment"
        result = parser.parse(content)
        
        assert result["directives"]["*"][0]["value"] == "/admin/"
    
    def test_parse_line_valid(self):
        """_parse_line 메서드 테스트"""
        parser = RobotsParser()
        key, value = parser._parse_line("Disallow: /admin/")
        
        assert key == "Disallow"
        assert value == "/admin/"
    
    def test_parse_line_with_spaces(self):
        """공백이 포함된 라인 파싱 테스트"""
        parser = RobotsParser()
        key, value = parser._parse_line("Disallow:   /admin/   ")
        
        assert key == "Disallow"
        assert value == "/admin/"
    
    def test_parse_line_empty(self):
        """빈 라인 파싱 테스트"""
        parser = RobotsParser()
        result = parser._parse_line("")
        assert result is None or result == ("", "")
    
    def test_find_comment_index(self):
        """_find_comment_index 메서드 테스트"""
        parser = RobotsParser()
        line = "Disallow: /admin/ # comment"
        index = parser._find_comment_index(line)
        
        assert index == line.index("#")
    
    def test_find_comment_index_no_comment(self):
        """주석이 없는 경우 테스트"""
        parser = RobotsParser()
        line = "Disallow: /admin/"
        index = parser._find_comment_index(line)
        
        assert index == -1 or index is None
    
    def test_get_disallowed_paths(self, sample_robots_content):
        """get_disallowed_paths 메서드 테스트"""
        parser = RobotsParser()
        result = parser.parse(sample_robots_content)
        paths = parser.get_disallowed_paths(result["directives"], "*")
        
        assert "/admin/" in paths
        assert "/private/" in paths
    
    def test_get_disallowed_paths_specific_user_agent(self, sample_robots_content):
        """특정 User-agent의 Disallow 경로 테스트"""
        parser = RobotsParser()
        result = parser.parse(sample_robots_content)
        paths = parser.get_disallowed_paths(result["directives"], "Googlebot")
        
        assert "/secret/" in paths
    
    def test_get_disallowed_paths_nonexistent_user_agent(self, sample_robots_content):
        """존재하지 않는 User-agent 테스트"""
        parser = RobotsParser()
        result = parser.parse(sample_robots_content)
        paths = parser.get_disallowed_paths(result["directives"], "NonExistentBot")
        
        # 기본적으로 와일드카드(*) 규칙이 적용되거나 빈 리스트 반환
        assert isinstance(paths, list)
    
    def test_get_crawl_delay(self, sample_robots_content):
        """get_crawl_delay 메서드 테스트"""
        parser = RobotsParser()
        result = parser.parse(sample_robots_content)
        delay = parser.get_crawl_delay(result["directives"], "*")
        
        assert delay == 10
    
    def test_get_crawl_delay_no_delay(self):
        """Crawl-delay가 없는 경우 테스트"""
        parser = RobotsParser()
        content = "User-agent: *\nDisallow: /admin/"
        result = parser.parse(content)
        delay = parser.get_crawl_delay(result["directives"], "*")
        
        assert delay is None or delay == 0
    
    def test_parse_with_windows_line_endings(self):
        """Windows 라인 엔딩(CRLF) 파싱 테스트"""
        parser = RobotsParser()
        content = "User-agent: *\r\nDisallow: /admin/\r\n"
        result = parser.parse(content)
        
        assert result["directives"]["*"][0]["value"] == "/admin/"
    
    def test_parse_mixed_case_directives(self):
        """대소문자 혼합 directive 파싱 테스트"""
        parser = RobotsParser()
        content = "USER-AGENT: *\nDISALLOW: /admin/"
        result = parser.parse(content)
        
        assert len(result["directives"]) > 0
    
    def test_parse_invalid_line(self):
        """잘못된 형식의 라인 파싱 테스트"""
        parser = RobotsParser()
        content = "This is not a valid robots.txt line\nUser-agent: *\nDisallow: /admin/"
        result = parser.parse(content)
        
        # 유효한 라인만 파싱되어야 함
        assert "*" in result["directives"]
    
    def test_parse_trailing_slash_paths(self):
        """경로 trailing slash 테스트"""
        parser = RobotsParser()
        content = "User-agent: *\nDisallow: /admin"
        result = parser.parse(content)
        
        assert result["directives"]["*"][0]["value"] == "/admin"
