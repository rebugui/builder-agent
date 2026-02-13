"""Pydantic models for data validation and serialization."""
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, HttpUrl, field_validator, ConfigDict


class DirectiveModel(BaseModel):
    """Represents a single Allow or Disallow directive."""
    type: str
    path: str
    
    @field_validator('type')
    def validate_type(cls, v):
        if v not in ['Allow', 'Disallow']:
            raise ValueError("Directive type must be 'Allow' or 'Disallow'")
        return v


class UserAgentGroupModel(BaseModel):
    """Represents a group of rules for a specific User-agent."""
    user_agent: str
    directives: List[DirectiveModel] = []
    crawl_delay: Optional[int] = None


class ScanResultModel(BaseModel):
    """Represents the final scan result for a single URL."""
    model_config = ConfigDict(use_enum_values=True)
    
    input_url: str
    robots_url: str
    status: str  # 'success', 'error', 'timeout'
    status_code: Optional[int] = None
    rules: List[UserAgentGroupModel] = []
    sitemaps: List[str] = []
    error: Optional[str] = None
    scanned_at: datetime = datetime.utcnow()
    
    @field_validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['success', 'error', 'timeout', 'not_found']
        if v not in allowed_statuses:
            raise ValueError(f"Invalid status: {v}")
        return v