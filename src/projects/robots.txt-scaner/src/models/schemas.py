"""Data models for robots.txt scanner using dataclasses."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class PermissionType(Enum):
    """Permission type enum for robots.txt directives."""
    ALLOW = "allow"
    DISALLOW = "disallow"


class ScanStatus(Enum):
    """Scan status enum."""
    SUCCESS = "success"
    ERROR = "error"
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"


@dataclass
class Permission:
    """Represents a single allow/disallow permission."""
    path: str
    permission: str  # "allow" or "disallow"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "permission": self.permission
        }


@dataclass
class UserAgentRule:
    """Represents rules for a specific user-agent."""
    user_agent: str
    permissions: list = field(default_factory=list)
    crawl_delay: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "user_agent": self.user_agent,
            "permissions": [p.to_dict() for p in self.permissions],
            "crawl_delay": self.crawl_delay
        }


@dataclass
class RobotsTxtResult:
    """Result of scanning a single URL's robots.txt."""
    source_url: str
    robots_url: str
    status: str
    http_code: Optional[int] = None
    content_length: Optional[int] = None
    error_message: Optional[str] = None
    rules: list = field(default_factory=list)
    sitemaps: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "source_url": self.source_url,
            "robots_url": self.robots_url,
            "status": self.status,
            "rules": [r.to_dict() for r in self.rules],
            "sitemaps": self.sitemaps
        }
        if self.http_code is not None:
            result["http_code"] = self.http_code
        if self.content_length is not None:
            result["content_length"] = self.content_length
        if self.error_message is not None:
            result["error_message"] = self.error_message
        return result