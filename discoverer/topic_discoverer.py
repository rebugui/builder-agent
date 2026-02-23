"""
Topic Discoverer - 프로젝트 아이디어 발굴
"""
import os
import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import feedparser

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.idea import (
    ProjectIdea, 
    IdeaSource, 
    ProjectType, 
    Priority
)


class TopicDiscoverer:
    """프로젝트 아이디어 발굴기"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.cache_file = "logs/discovered_ideas.json"
        self._load_cache()
    
    def _load_cache(self):
        """캐시 로드"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
        else:
            self.cache = {"ideas": [], "last_update": None}
    
    def _save_cache(self):
        """캐시 저장"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def discover(self, limit: int = 5) -> List[ProjectIdea]:
        """
        여러 소스에서 프로젝트 아이디어 발굴
        
        Args:
            limit: 반환할 아이디어 최대 개수
            
        Returns:
            발굴된 아이디어 리스트
        """
        all_ideas = []
        
        # 1. GitHub Trending
        try:
            github_ideas = self._github_trending()
            all_ideas.extend(github_ideas)
        except Exception as e:
            print(f"[WARN] GitHub Trending failed: {e}")
        
        # 2. Security News
        try:
            security_ideas = self._security_news()
            all_ideas.extend(security_ideas)
        except Exception as e:
            print(f"[WARN] Security News failed: {e}")
        
        # 3. Hacker News
        try:
            hn_ideas = self._hacker_news()
            all_ideas.extend(hn_ideas)
        except Exception as e:
            print(f"[WARN] Hacker News failed: {e}")
        
        # 4. 사전 정의된 아이디어 풀 (fallback)
        predefined_ideas = self._predefined_ideas()
        all_ideas.extend(predefined_ideas)
        
        # 중복 제거
        unique_ideas = self._deduplicate(all_ideas)
        
        # 우선순위별 정렬
        sorted_ideas = sorted(
            unique_ideas, 
            key=lambda x: x.priority.value, 
            reverse=True
        )
        
        # 상위 N개 반환
        return sorted_ideas[:limit]
    
    def _github_trending(self) -> List[ProjectIdea]:
        """GitHub Trending에서 아이디어 발굴"""
        ideas = []
        
        url = "https://github.com/trending"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        repos = soup.find_all('article', class_='Box-row')[:5]
        
        for repo in repos:
            try:
                name = repo.find('h2', class_='h3').text.strip().replace(' ', '')
                description = repo.find('p', class_='col-9').text.strip()
                
                # 인기 있는 프로젝트를 기반으로 새로운 도구 아이디어 생성
                idea = ProjectIdea(
                    name=self._generate_tool_name(name),
                    description=f"Tool inspired by {name}: {description}",
                    source=IdeaSource.GITHUB_TRENDING,
                    project_type=ProjectType.DEVELOPMENT_TOOL,
                    priority=Priority.HIGH,
                    tags=["github-trending", "development"],
                    reference_url=f"https://github.com{name}"
                )
                ideas.append(idea)
            except Exception as e:
                continue
        
        return ideas
    
    def _security_news(self) -> List[ProjectIdea]:
        """보안 뉴스에서 아이디어 발굴"""
        ideas = []
        
        # 미리 정의된 보안 도구 아이디어 (RSS 피드 실패 시 fallback)
        security_tools = [
            {
                "name": "secrets-leak-scanner",
                "description": "Scan code repositories for accidentally committed secrets and API keys",
                "tags": ["security", "secrets", "scanner"],
                "requirements": [
                    "Scan multiple file types",
                    "Support regex patterns for common secrets",
                    "Generate JSON reports",
                    "Exclude patterns for false positives"
                ]
            },
            {
                "name": "sbom-generator",
                "description": "Generate Software Bill of Materials from project dependencies",
                "tags": ["security", "sbom", "dependencies"],
                "requirements": [
                    "Parse multiple package managers",
                    "Output SPDX format",
                    "Detect transitive dependencies",
                    "Include license information"
                ]
            },
            {
                "name": "container-vulnerability-scanner",
                "description": "Scan Docker images for known vulnerabilities",
                "tags": ["security", "docker", "vulnerability"],
                "requirements": [
                    "Pull Docker images",
                    "Scan layers for CVEs",
                    "Generate severity reports",
                    "Suggest remediation"
                ]
            },
            {
                "name": "api-security-tester",
                "description": "Automated API security testing tool",
                "tags": ["security", "api", "testing"],
                "requirements": [
                    "Parse OpenAPI/Swagger specs",
                    "Test common vulnerabilities",
                    "Generate test reports",
                    "Support authentication"
                ]
            },
            {
                "name": "log-anomaly-detector",
                "description": "Detect anomalies in application logs using ML",
                "tags": ["security", "logs", "ml"],
                "requirements": [
                    "Parse multiple log formats",
                    "Detect unusual patterns",
                    "Alert on suspicious activity",
                    "Visualize anomalies"
                ]
            }
        ]
        
        for tool in security_tools:
            idea = ProjectIdea(
                name=tool["name"],
                description=tool["description"],
                source=IdeaSource.SECURITY_NEWS,
                project_type=ProjectType.SECURITY_TOOL,
                priority=Priority.HIGH,
                tags=tool["tags"],
                requirements=tool["requirements"],
                technical_stack=["Python", "Click", "Rich"],
                difficulty="medium"
            )
            ideas.append(idea)
        
        return ideas
    
    def _hacker_news(self) -> List[ProjectIdea]:
        """Hacker News에서 아이디어 발굴"""
        ideas = []
        
        try:
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(url, timeout=10)
            story_ids = response.json()[:10]
            
            for story_id in story_ids[:3]:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                story = requests.get(story_url, timeout=10).json()
                
                if story.get('title'):
                    idea = ProjectIdea(
                        name=self._generate_tool_name(story['title']),
                        description=f"Tool inspired by: {story['title']}",
                        source=IdeaSource.HACKER_NEWS,
                        project_type=ProjectType.DEVELOPMENT_TOOL,
                        priority=Priority.MEDIUM,
                        tags=["hacker-news", "trending"],
                        reference_url=story.get('url'),
                        metadata={"hn_score": story.get('score', 0)}
                    )
                    ideas.append(idea)
        except Exception as e:
            print(f"[WARN] Hacker News API failed: {e}")
        
        return ideas
    
    def _predefined_ideas(self) -> List[ProjectIdea]:
        """사전 정의된 아이디어 풀"""
        ideas = [
            {
                "name": "code-complexity-analyzer",
                "description": "Analyze code complexity metrics (cyclomatic, cognitive)",
                "type": ProjectType.DEVELOPMENT_TOOL,
                "tags": ["code-quality", "metrics"],
                "stack": ["Python", "ast", "radon"]
            },
            {
                "name": "git-commit-analyzer",
                "description": "Analyze git commit patterns and generate insights",
                "type": ProjectType.DEVELOPMENT_TOOL,
                "tags": ["git", "analytics"],
                "stack": ["Python", "GitPython"]
            },
            {
                "name": "api-mock-server",
                "description": "Generate mock API servers from OpenAPI specs",
                "type": ProjectType.DEVELOPMENT_TOOL,
                "tags": ["api", "mock", "testing"],
                "stack": ["Python", "FastAPI"]
            },
            {
                "name": "env-config-validator",
                "description": "Validate environment configuration files",
                "type": ProjectType.DEVELOPMENT_TOOL,
                "tags": ["config", "validation"],
                "stack": ["Python", "pydantic"]
            },
            {
                "name": "docker-image-optimizer",
                "description": "Analyze and optimize Docker image sizes",
                "type": ProjectType.DEVELOPMENT_TOOL,
                "tags": ["docker", "optimization"],
                "stack": ["Python", "docker"]
            },
            {
                "name": "sql-query-formatter",
                "description": "Format and beautify SQL queries",
                "type": ProjectType.DEVELOPMENT_TOOL,
                "tags": ["sql", "formatting"],
                "stack": ["Python", "sqlparse"]
            },
            {
                "name": "json-schema-generator",
                "description": "Generate JSON schemas from JSON data",
                "type": ProjectType.DEVELOPMENT_TOOL,
                "tags": ["json", "schema"],
                "stack": ["Python"]
            },
            {
                "name": "csv-data-cleaner",
                "description": "Clean and normalize CSV data files",
                "type": ProjectType.DATA_ANALYSIS,
                "tags": ["csv", "data-cleaning"],
                "stack": ["Python", "pandas"]
            },
            {
                "name": "markdown-link-checker",
                "description": "Check and validate links in markdown files",
                "type": ProjectType.DEVELOPMENT_TOOL,
                "tags": ["markdown", "links"],
                "stack": ["Python", "requests"]
            },
            {
                "name": "ssl-certificate-monitor",
                "description": "Monitor SSL certificate expiration dates",
                "type": ProjectType.SECURITY_TOOL,
                "tags": ["ssl", "monitoring"],
                "stack": ["Python", "cryptography"]
            }
        ]
        
        predefined = []
        for item in ideas:
            idea = ProjectIdea(
                name=item["name"],
                description=item["description"],
                source=IdeaSource.MANUAL,
                project_type=item["type"],
                priority=Priority.MEDIUM,
                tags=item["tags"],
                technical_stack=item["stack"],
                difficulty="easy"
            )
            predefined.append(idea)
        
        return predefined
    
    def _generate_tool_name(self, source: str) -> str:
        """소스 이름에서 도구 이름 생성"""
        # 간단한 이름 정리
        name = source.lower()
        name = name.replace(' ', '-').replace('_', '-')
        name = ''.join(c for c in name if c.isalnum() or c == '-')
        
        # 너무 길면 자르기
        if len(name) > 30:
            name = name[:30]
        
        # 접미사 추가 (중복 방지)
        if not name.endswith('-tool'):
            name = f"{name}-tool"
        
        return name
    
    def _deduplicate(self, ideas: List[ProjectIdea]) -> List[ProjectIdea]:
        """중복 아이디어 제거"""
        seen = set()
        unique = []
        
        for idea in ideas:
            if idea.name not in seen:
                seen.add(idea.name)
                unique.append(idea)
        
        return unique


if __name__ == "__main__":
    # 테스트
    discoverer = TopicDiscoverer()
    ideas = discoverer.discover(limit=5)
    
    for i, idea in enumerate(ideas, 1):
        print(f"\n{i}. {idea.name}")
        print(f"   Source: {idea.source.value}")
        print(f"   Type: {idea.project_type.value}")
        print(f"   Description: {idea.description}")
        print(f"   Priority: {idea.priority.name}")
