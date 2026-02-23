"""
Project Idea Models for Builder Agent v3
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class IdeaSource(Enum):
    """아이디어 발굴 소스"""
    GITHUB_TRENDING = "github_trending"
    CVE_DATABASE = "cve_database"
    SECURITY_NEWS = "security_news"
    ARXIV_PAPER = "arxiv_paper"
    HACKER_NEWS = "hacker_news"
    PRODUCT_HUNT = "product_hunt"
    MANUAL = "manual"


class ProjectType(Enum):
    """프로젝트 타입"""
    SECURITY_TOOL = "security_tool"
    DEVELOPMENT_TOOL = "development_tool"
    DATA_ANALYSIS = "data_analysis"
    AUTOMATION = "automation"
    CLI_APP = "cli_app"
    WEB_APP = "web_app"
    API_SERVICE = "api_service"
    LIBRARY = "library"


class Priority(Enum):
    """우선순위"""
    HIGH = 3
    MEDIUM = 2
    LOW = 1


@dataclass
class ProjectIdea:
    """프로젝트 아이디어"""
    name: str
    description: str
    source: IdeaSource
    project_type: ProjectType
    priority: Priority = Priority.MEDIUM
    tags: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    technical_stack: List[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard
    estimated_time: str = "2-4 hours"
    reference_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source.value,
            "project_type": self.project_type.value,
            "priority": self.priority.value,
            "tags": self.tags,
            "requirements": self.requirements,
            "technical_stack": self.technical_stack,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
            "reference_url": self.reference_url,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectIdea':
        """딕셔너리에서 생성"""
        data['source'] = IdeaSource(data['source'])
        data['project_type'] = ProjectType(data['project_type'])
        data['priority'] = Priority(data['priority'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class DevelopmentResult:
    """개발 결과"""
    idea: ProjectIdea
    success: bool
    files: Dict[str, str] = field(default_factory=dict)  # filename -> content
    test_results: Optional[Dict[str, Any]] = None
    review_comments: Optional[List[str]] = None
    documentation: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "idea": self.idea.to_dict(),
            "success": self.success,
            "files": self.files,
            "test_results": self.test_results,
            "review_comments": self.review_comments,
            "documentation": self.documentation,
            "error": self.error,
            "execution_time": self.execution_time,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class PublishedProject:
    """게시된 프로젝트"""
    idea: ProjectIdea
    github_url: str
    repository_name: str
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "idea": self.idea.to_dict(),
            "github_url": self.github_url,
            "repository_name": self.repository_name,
            "stars": self.stars,
            "forks": self.forks,
            "watchers": self.watchers,
            "open_issues": self.open_issues,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }
