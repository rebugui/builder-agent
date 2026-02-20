"""
Builder Agent v2.0 - 주제 발굴 시스템

GitHub Trending, CVE, 보안 뉴스 등에서 프로젝트 아이디어를 발굴합니다.
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import random


@dataclass
class ProjectIdea:
    """프로젝트 아이디어"""
    name: str
    description: str
    source: str  # github, cve, news, user
    category: str
    difficulty: str  # easy, medium, hard
    keywords: List[str]


class TopicDiscoverer:
    """주제 발굴기"""
    
    def __init__(self):
        self.github_trending_url = "https://api.gitterapp.com/repositories"
        self.cve_url = "https://cve.circl.lu/api/browse/"
        self.cache_duration = timedelta(hours=6)
        self._cache = {}
        self._cache_time = {}
    
    def discover_topics(self, limit: int = 10) -> List[ProjectIdea]:
        """
        다양한 소스에서 주제 발굴
        
        Args:
            limit: 최대 주제 수
            
        Returns:
            프로젝트 아이디어 리스트
        """
        ideas = []
        
        # GitHub Trending
        try:
            github_ideas = self._get_github_trending()
            ideas.extend(github_ideas)
        except Exception as e:
            print(f"GitHub Trending 조회 실패: {e}")
        
        # 보안 도구 아이디어
        security_ideas = self._get_security_tool_ideas()
        ideas.extend(security_ideas)
        
        # DevOps 도구 아이디어
        devops_ideas = self._get_devops_tool_ideas()
        ideas.extend(devops_ideas)
        
        # 중복 제거 및 셔플
        ideas = self._deduplicate(ideas)
        random.shuffle(ideas)
        
        return ideas[:limit]
    
    def _get_github_trending(self, language: str = "python") -> List[ProjectIdea]:
        """GitHub Trending에서 아이디어 발굴"""
        ideas = []
        
        try:
            # GitHub Trending API (비공식)
            url = f"https://api.gitterapp.com/repositories?language={language}&since=weekly"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                repos = resp.json()[:10]
                for repo in repos:
                    # 보안/DevOps 관련만 필터링
                    if self._is_security_or_devops(repo.get('description', '')):
                        ideas.append(ProjectIdea(
                            name=self._generate_tool_name(repo['name']),
                            description=f"{repo.get('description', '보안 도구')} - Python으로 재구현",
                            source="github",
                            category="security",
                            difficulty="medium",
                            keywords=["security", "tool", repo.get('name', '').lower()]
                        ))
        except Exception as e:
            print(f"GitHub API 에러: {e}")
        
        # API 실패 시 하드코딩된 아이디어 사용
        if not ideas:
            ideas = self._get_fallback_github_ideas()
        
        return ideas
    
    def _get_fallback_github_ideas(self) -> List[ProjectIdea]:
        """GitHub API 실패 시 대체 아이디어"""
        return [
            ProjectIdea(
                name="subdomain-scanner",
                description="서브도메인 스캐너 - DNS 레코드 기반 서브도메인 탐지",
                source="fallback",
                category="security",
                difficulty="medium",
                keywords=["subdomain", "dns", "reconnaissance"]
            ),
            ProjectIdea(
                name="jwt-cracker",
                description="JWT 토큰 취약점 스캐너 - none algorithm, weak secret 탐지",
                source="fallback",
                category="security",
                difficulty="medium",
                keywords=["jwt", "authentication", "vulnerability"]
            ),
            ProjectIdea(
                name="api-fuzzer",
                description="REST API 퍼저 - 입력 검증 취약점 탐지",
                source="fallback",
                category="security",
                difficulty="hard",
                keywords=["api", "fuzzer", "testing"]
            ),
            ProjectIdea(
                name="log-analyzer",
                description="보안 로그 분석기 - 의심스러운 활동 탐지",
                source="fallback",
                category="security",
                difficulty="medium",
                keywords=["log", "analysis", "siem"]
            ),
            ProjectIdea(
                name="port-knocker",
                description="포트 노커 - 스텔스 포트 스캐닝 도구",
                source="fallback",
                category="security",
                difficulty="easy",
                keywords=["port", "network", "scanning"]
            ),
        ]
    
    def _get_security_tool_ideas(self) -> List[ProjectIdea]:
        """보안 도구 아이디어"""
        ideas = [
            ProjectIdea(
                name="sql-injection-detector",
                description="SQL Injection 자동 탐지 도구",
                source="generated",
                category="security",
                difficulty="medium",
                keywords=["sqli", "injection", "web"]
            ),
            ProjectIdea(
                name="xss-scanner",
                description="XSS 취약점 스캐너",
                source="generated",
                category="security",
                difficulty="medium",
                keywords=["xss", "injection", "web"]
            ),
            ProjectIdea(
                name="ssl-checker",
                description="SSL/TLS 인증서 검사 도구",
                source="generated",
                category="security",
                difficulty="easy",
                keywords=["ssl", "tls", "certificate"]
            ),
            ProjectIdea(
                name="secrets-scanner",
                description="코드 내 하드코딩된 시크릿 탐지",
                source="generated",
                category="security",
                difficulty="medium",
                keywords=["secrets", "credentials", "git"]
            ),
            ProjectIdea(
                name="header-analyzer",
                description="HTTP 보안 헤더 분석기",
                source="generated",
                category="security",
                difficulty="easy",
                keywords=["http", "headers", "security"]
            ),
        ]
        return ideas
    
    def _get_devops_tool_ideas(self) -> List[ProjectIdea]:
        """DevOps 도구 아이디어"""
        ideas = [
            ProjectIdea(
                name="docker-linter",
                description="Dockerfile 린터 - 보안 및 최적화 검사",
                source="generated",
                category="devops",
                difficulty="medium",
                keywords=["docker", "lint", "security"]
            ),
            ProjectIdea(
                name="k8s-auditor",
                description="Kubernetes 보안 감사 도구",
                source="generated",
                category="devops",
                difficulty="hard",
                keywords=["kubernetes", "audit", "security"]
            ),
            ProjectIdea(
                name="ci-monitor",
                description="CI/CD 파이프라인 모니터링 도구",
                source="generated",
                category="devops",
                difficulty="medium",
                keywords=["ci", "cd", "monitoring"]
            ),
            ProjectIdea(
                name="env-validator",
                description="환경변수 검증 및 문서화 도구",
                source="generated",
                category="devops",
                difficulty="easy",
                keywords=["env", "validation", "config"]
            ),
            ProjectIdea(
                name="backup-manager",
                description="자동화된 백업 관리 도구",
                source="generated",
                category="devops",
                difficulty="medium",
                keywords=["backup", "automation", "recovery"]
            ),
        ]
        return ideas
    
    def _is_security_or_devops(self, description: str) -> bool:
        """보안/DevOps 관련 여부 확인"""
        keywords = [
            'security', 'vulnerability', 'scan', 'exploit', 'pentest',
            'docker', 'kubernetes', 'k8s', 'ci', 'cd', 'deploy',
            'monitoring', 'log', 'audit', 'compliance',
            '보안', '취약점', '스캔', '로그', '모니터링'
        ]
        desc_lower = description.lower()
        return any(kw in desc_lower for kw in keywords)
    
    def _generate_tool_name(self, repo_name: str) -> str:
        """저장소명을 도구명으로 변환"""
        # 특수문자 제거, 소문자화
        name = repo_name.lower().replace('-', '_').replace('.', '_')
        # 길이 제한
        if len(name) > 30:
            name = name[:30]
        return name
    
    def _deduplicate(self, ideas: List[ProjectIdea]) -> List[ProjectIdea]:
        """중복 제거"""
        seen = set()
        unique = []
        for idea in ideas:
            if idea.name not in seen:
                seen.add(idea.name)
                unique.append(idea)
        return unique
    
    def get_random_topic(self) -> ProjectIdea:
        """랜덤 주제 반환"""
        ideas = self.discover_topics(limit=20)
        if ideas:
            return random.choice(ideas)
        
        # 기본값
        return ProjectIdea(
            name="security-tool",
            description="보안 도구",
            source="default",
            category="security",
            difficulty="medium",
            keywords=["security"]
        )


# 사용 예시
if __name__ == "__main__":
    discoverer = TopicDiscoverer()
    ideas = discoverer.discover_topics(limit=10)
    
    print("=== 발굴된 프로젝트 아이디어 ===\n")
    for i, idea in enumerate(ideas, 1):
        print(f"{i}. {idea.name}")
        print(f"   설명: {idea.description}")
        print(f"   카테고리: {idea.category}")
        print(f"   난이도: {idea.difficulty}")
        print(f"   키워드: {', '.join(idea.keywords)}")
        print()
