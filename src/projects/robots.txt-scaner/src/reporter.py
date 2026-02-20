"""
보고서 생성
"""
import json
from typing import List
from .models import ScanResult


class Reporter:
    """보고서 생성기"""
    
    def format(self, results: List[ScanResult], format_type: str = "text") -> str:
        """
        결과 포맷팅
        
        Args:
            results: 스캔 결과
            format_type: 포맷 타입 (json, text)
            
        Returns:
            포맷팅된 결과
        """
        if format_type == "json":
            return self._to_json(results)
        return self._to_text(results)
    
    def _to_json(self, results: List[ScanResult]) -> str:
        data = [
            {{
                "target": r.target,
                "vulnerability": r.vulnerability,
                "severity": r.severity.value,
                "description": r.description,
                "recommendation": r.recommendation
            }}
            for r in results
        ]
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _to_text(self, results: List[ScanResult]) -> str:
        lines = []
        for r in results:
            lines.append(f"[{{r.severity.value.upper()}}] {{r.target}}")
            lines.append(f"  취약점: {{r.vulnerability}}")
            lines.append(f"  설명: {{r.description}}")
            if r.recommendation:
                lines.append(f"  권장사항: {{r.recommendation}}")
            lines.append("")
        return "\n".join(lines)
