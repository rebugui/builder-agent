"""
Result Models Module

Data structures for scan results.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any, Dict


@dataclass
class Rule:
    """Represents a single Allow/Disallow rule."""
    type: str
    path: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {"type": self.type, "path": self.path}


@dataclass
class Directive:
    """Represents a User-agent group with its rules."""
    user_agent: str
    rules: List[Rule] = field(default_factory=list)
    crawl_delay: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_agent": self.user_agent,
            "rules": [r.to_dict() for r in self.rules],
            "crawl_delay": self.crawl_delay
        }


@dataclass
class ScanResult:
    """
    Result of a single robots.txt scan.
    
    Attributes:
        url: The base URL that was scanned.
        robots_url: The full robots.txt URL.
        status: HTTP status code (or None on error).
        directives: List of parsed directives.
        sitemaps: List of sitemap URLs.
        error: Error message if scan failed.
    """
    url: str
    robots_url: str
    status: Optional[int]
    directives: List[Directive] = field(default_factory=list)
    sitemaps: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the result.
        """
        return {
            "url": self.url,
            "robots_url": self.robots_url,
            "status": self.status,
            "directives": [d.to_dict() for d in self.directives],
            "sitemaps": self.sitemaps,
            "error": self.error
        }
    
    def is_success(self) -> bool:
        """Check if the scan was successful."""
        return self.error is None and self.status is not None and self.status < 400
    
    def has_robots_txt(self) -> bool:
        """Check if robots.txt was found (status 200)."""
        return self.status == 200
