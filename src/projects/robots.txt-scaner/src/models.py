"""
데이터 모델
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class Severity(str, Enum):
    """심각도"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ScanResult:
    """스캔 결과"""
    target: str
    vulnerability: str
    severity: Severity
    description: str
    recommendation: Optional[str] = None
