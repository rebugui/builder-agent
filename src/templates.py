"""
Builder Agent v2.0 - 프로젝트 템플릿 시스템

템플릿 기반으로 일관된 구조의 프로젝트를 생성합니다.
"""

from typing import Dict, List
from enum import Enum


class ProjectType(Enum):
    """프로젝트 타입"""
    CLI = "cli"           # 커맨드라인 도구
    LIBRARY = "library"   # Python 라이브러리
    SCANNER = "scanner"   # 보안 스캐너
    ANALYZER = "analyzer" # 데이터 분석 도구
    SCRIPT = "script"     # 간단한 스크립트


class ProjectTemplates:
    """프로젝트 템플릿 관리"""
    
    @staticmethod
    def get_template(project_type: ProjectType) -> Dict:
        """프로젝트 타입에 맞는 템플릿 반환"""
        templates = {
            ProjectType.CLI: ProjectTemplates._cli_template(),
            ProjectType.LIBRARY: ProjectTemplates._library_template(),
            ProjectType.SCANNER: ProjectTemplates._scanner_template(),
            ProjectType.ANALYZER: ProjectTemplates._analyzer_template(),
            ProjectType.SCRIPT: ProjectTemplates._script_template(),
        }
        return templates.get(project_type, templates[ProjectType.CLI])
    
    @staticmethod
    def _cli_template() -> Dict:
        """CLI 도구 템플릿"""
        return {
            "structure": [
                "src/__init__.py",
                "src/main.py",
                "src/core.py",
                "src/utils.py",
                "tests/__init__.py",
                "tests/test_core.py",
                "docs/README.md",
                "requirements.txt",
                ".gitignore",
            ],
            "files": {
                "src/main.py": '''"""
{project_name} - CLI 진입점
"""
import argparse
import sys
from .core import {core_class_name}


def main():
    """메인 진입점"""
    parser = argparse.ArgumentParser(
        description="{description}",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "target",
        help="대상 (파일, URL 등)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="상세 출력"
    )
    parser.add_argument(
        "-o", "--output",
        help="결과 저장 파일"
    )
    
    args = parser.parse_args()
    
    try:
        runner = {core_class_name}(verbose=args.verbose)
        result = runner.run(args.target)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
            print(f"결과가 {args.output}에 저장되었습니다.")
        else:
            print(result)
            
    except Exception as e:
        print(f"오류: {{e}}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
''',
                "src/core.py": '''"""
{project_name} - 핵심 기능
"""
from typing import Optional
from .utils import validate_input


class {core_class_name}:
    """핵심 기능 클래스"""
    
    def __init__(self, verbose: bool = False):
        """
        초기화
        
        Args:
            verbose: 상세 출력 여부
        """
        self.verbose = verbose
    
    def run(self, target: str) -> str:
        """
        메인 실행 메서드
        
        Args:
            target: 처리할 대상
            
        Returns:
            실행 결과
        """
        # 입력 검증
        if not validate_input(target):
            raise ValueError("유효하지 않은 입력입니다.")
        
        if self.verbose:
            print(f"처리 중: {{target}}")
        
        # TODO: 실제 기능 구현
        result = self._process(target)
        
        return result
    
    def _process(self, target: str) -> str:
        """
        실제 처리 로직
        
        Args:
            target: 처리할 대상
            
        Returns:
            처리 결과
        """
        # TODO: 구현 필요
        return f"처리 완료: {{target}}"
''',
                "src/utils.py": '''"""
유틸리티 함수
"""
import re
from typing import Optional


def validate_input(target: str) -> bool:
    """
    입력 검증
    
    Args:
        target: 검증할 입력
        
    Returns:
        유효성 여부
    """
    if not target or not isinstance(target, str):
        return False
    
    # 빈 문자열 제거
    target = target.strip()
    if not target:
        return False
    
    # 위험 문자 패턴 검사
    dangerous_patterns = [
        r'<[^>]*>',      # HTML 태그
        r'javascript:',  # JavaScript
        r'data:',        # Data URI
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, target, re.IGNORECASE):
            return False
    
    return True


def format_output(data: dict) -> str:
    """
    출력 포맷팅
    
    Args:
        data: 출력할 데이터
        
    Returns:
        포맷팅된 문자열
    """
    lines = []
    for key, value in data.items():
        lines.append(f"{{key}}: {{value}}")
    return "\\n".join(lines)
''',
            },
            "test_imports": {
                "src.core": ["{core_class_name}"],
                "src.utils": ["validate_input", "format_output"],
            }
        }
    
    @staticmethod
    def _scanner_template() -> Dict:
        """보안 스캐너 템플릿"""
        return {
            "structure": [
                "src/__init__.py",
                "src/main.py",
                "src/scanner.py",
                "src/reporter.py",
                "src/models.py",
                "tests/__init__.py",
                "tests/test_scanner.py",
                "docs/README.md",
                "requirements.txt",
                ".gitignore",
            ],
            "files": {
                "src/main.py": '''"""
{project_name} - 보안 스캐너 CLI
"""
import argparse
import json
import sys
from .scanner import Scanner
from .reporter import Reporter


def main():
    parser = argparse.ArgumentParser(description="{description}")
    parser.add_argument("target", help="스캔 대상 (URL, IP, 도메인)")
    parser.add_argument("-f", "--format", choices=["json", "text"], default="text")
    parser.add_argument("-o", "--output", help="결과 파일")
    parser.add_argument("-v", "--verbose", action="store_true")
    
    args = parser.parse_args()
    
    scanner = Scanner(verbose=args.verbose)
    results = scanner.scan(args.target)
    
    reporter = Reporter()
    output = reporter.format(results, args.format)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
''',
                "src/scanner.py": '''"""
보안 스캐너
"""
from typing import List, Dict
from .models import ScanResult


class Scanner:
    """보안 스캐너"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def scan(self, target: str) -> List[ScanResult]:
        """
        대상 스캔
        
        Args:
            target: 스캔 대상
            
        Returns:
            스캔 결과 리스트
        """
        results = []
        
        # TODO: 실제 스캔 로직 구현
        if self.verbose:
            print(f"스캔 중: {{target}}")
        
        return results
''',
                "src/models.py": '''"""
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
''',
                "src/reporter.py": '''"""
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
        return "\\n".join(lines)
''',
            },
            "test_imports": {
                "src.scanner": ["Scanner"],
                "src.reporter": ["Reporter"],
                "src.models": ["ScanResult", "Severity"],
            }
        }
    
    @staticmethod
    def _library_template() -> Dict:
        """Python 라이브러리 템플릿"""
        return {
            "structure": [
                "src/__init__.py",
                "src/{module_name}.py",
                "src/exceptions.py",
                "tests/__init__.py",
                "tests/test_{module_name}.py",
                "docs/README.md",
                "requirements.txt",
                "setup.py",
                ".gitignore",
            ],
            "files": {
                "src/{module_name}.py": '''"""
{project_name} - Python 라이브러리
"""
from typing import Optional


class {core_class_name}:
    """메인 클래스"""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {{}}
    
    def process(self, data: str) -> str:
        """
        데이터 처리
        
        Args:
            data: 입력 데이터
            
        Returns:
            처리된 데이터
        """
        # TODO: 구현
        return data
''',
                "src/exceptions.py": '''"""
커스텀 예외
"""


class {project_name}Error(Exception):
    """기본 예외"""
    pass


class ValidationError({project_name}Error):
    """검증 오류"""
    pass


class ProcessingError({project_name}Error):
    """처리 오류"""
    pass
''',
            },
            "test_imports": {
                "src.{module_name}": ["{core_class_name}"],
                "src.exceptions": ["{project_name}Error", "ValidationError"],
            }
        }
    
    @staticmethod
    def _analyzer_template() -> Dict:
        """데이터 분석 도구 템플릿"""
        return ProjectTemplates._cli_template()  # CLI와 유사
    
    @staticmethod
    def _script_template() -> Dict:
        """간단한 스크립트 템플릿"""
        return {
            "structure": [
                "src/__init__.py",
                "src/main.py",
                "tests/__init__.py",
                "tests/test_main.py",
                "requirements.txt",
                ".gitignore",
            ],
            "files": {
                "src/main.py": '''#!/usr/bin/env python3
\"\"\"
{project_name} - {description}
\"\"\"
import sys


def main():
    \"\"\"메인 함수\"\"\"
    # TODO: 구현
    print("{project_name} 실행 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
            },
            "test_imports": {
                "src.main": ["main"],
            }
        }
    
    @staticmethod
    def detect_project_type(description: str) -> ProjectType:
        """
        설명 기반 프로젝트 타입 자동 감지
        
        Args:
            description: 프로젝트 설명
            
        Returns:
            감지된 프로젝트 타입
        """
        desc_lower = description.lower()
        
        # 키워드 기반 감지
        scanner_keywords = ['scan', 'vulnerability', 'security', '취약점', '보안', '스캔', '탐지']
        cli_keywords = ['cli', 'command', 'tool', '커맨드', '도구']
        analyzer_keywords = ['analyze', 'analysis', 'parse', '분석', '파싱']
        library_keywords = ['library', 'sdk', 'api', '라이브러리']
        
        for kw in scanner_keywords:
            if kw in desc_lower:
                return ProjectType.SCANNER
        
        for kw in analyzer_keywords:
            if kw in desc_lower:
                return ProjectType.ANALYZER
        
        for kw in cli_keywords:
            if kw in desc_lower:
                return ProjectType.CLI
        
        for kw in library_keywords:
            if kw in desc_lower:
                return ProjectType.LIBRARY
        
        # 기본값
        return ProjectType.CLI
    
    @staticmethod
    def fill_template(template: Dict, project_name: str, description: str) -> Dict[str, str]:
        """
        템플릿 변수 채우기
        
        Args:
            template: 템플릿 딕셔너리
            project_name: 프로젝트 이름
            description: 프로젝트 설명
            
        Returns:
            채워진 파일 딕셔너리
        """
        # 변수 생성
        core_class_name = "".join(word.capitalize() for word in project_name.replace("-", " ").replace("_", " ").split())
        module_name = project_name.lower().replace("-", "_").replace(" ", "_")
        
        # 설명에서 문법 에러 유발 문자 제거 (따옴표, 백슬래시 등)
        safe_description = description.replace('"', "'").replace("\\", "").replace("\n", " ").strip()
        if len(safe_description) > 200:
            safe_description = safe_description[:200]
        
        files = {}
        for filepath, content in template.get("files", {}).items():
            # 파일 경로 변수 치환
            filled_path = filepath.replace("{module_name}", module_name).replace("{project_name}", project_name.replace(" ", "-").lower())
            
            # 내용 변수 치환 (format 대신 replace 사용 - 중괄호 에러 방지)
            filled_content = content
            filled_content = filled_content.replace("{project_name}", project_name)
            filled_content = filled_content.replace("{description}", safe_description)
            filled_content = filled_content.replace("{core_class_name}", core_class_name)
            filled_content = filled_content.replace("{module_name}", module_name)
            
            files[filled_path] = filled_content
        
        # 기본 파일 추가
        if "src/__init__.py" not in files:
            files["src/__init__.py"] = ""
        if "tests/__init__.py" not in files:
            files["tests/__init__.py"] = ""
        if "requirements.txt" not in files:
            files["requirements.txt"] = "pytest>=7.4.0\n"
        if ".gitignore" not in files:
            files[".gitignore"] = "__pycache__/\n*.py[cod]\n.env\nvenv/\n.DS_Store\n"
        if "docs/README.md" not in files:
            files["docs/README.md"] = f"""# {project_name}

{description}

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

```bash
python -m src.main --help
```

## 라이선스

AGPL-3.0
"""
        
        return files
